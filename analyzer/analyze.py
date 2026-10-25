#!/usr/bin/env python3
"""Static analysis, comparison report and human-rating sheet for agent runs.

A run is a folder named <condition>__<rep> (for example with-setup__1) that holds a JS/TS
project, possibly nested. The report groups runs by condition.

  python analyzer/analyze.py run    runs/with-setup__1 --out results/with-setup__1.json
  python analyzer/analyze.py sheet  results/*.json --out human.csv
  python analyzer/analyze.py report results/*.json --md report.md [--human human.csv]

Tools that only read text (Biome, jscpd, lizard) run on a copy of the run. Anything that
executes code of the run (install, type check, project lint config, tests) goes through
sandbox.py. A missing tool or sandbox is recorded as "skipped", never as a pass.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checklist as cl  # noqa: E402
import sandbox  # noqa: E402

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "config"
TOOLS_BIN = Path(os.environ.get("QA_TOOLS_BIN", HERE / "tools" / "node_modules" / ".bin"))
TIMEOUT = int(os.environ.get("QA_TOOL_TIMEOUT", "600"))
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", ".turbo",
             ".idea", ".vscode", ".svelte-kit", ".output"}
SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
GENERATED = re.compile(r"\.d\.ts$|\.min\.js$")
MIN_REPS = 3
COPY_THRESHOLD = 0.25
SATURATION_RATING = 9
# Escape hatches that make linters and type checkers go quiet.
SUPPRESSIONS = [r"@ts-ignore", r"@ts-expect-error", r"@ts-nocheck", r"eslint-disable",
                r"biome-ignore", r":\s*any\b", r"\bas\s+any\b"]


# ---------------------------------------------------------------- helpers

def skipped(reason: str) -> dict:
    return {"status": "skipped", "reason": reason}


def failed(res: dict, what: str) -> dict:
    reason = "timeout" if res.get("timeout") else (res["err"] or res["out"])[-500:]
    return {"status": "error", "reason": f"{what}: {reason}"}


def host_run(cmd: list[str], cwd: Path) -> dict:
    """Run a trusted tool (one that only reads text) on the host; never raises."""
    start = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT, errors="replace")
        return {"code": p.returncode, "out": p.stdout, "err": p.stderr, "secs": round(time.time() - start, 1)}
    except OSError:  # not found, or not executable
        return {"code": None, "out": "", "err": "not found", "secs": 0, "missing": True}
    except subprocess.TimeoutExpired:
        return {"code": None, "out": "", "err": "timeout", "secs": TIMEOUT, "timeout": True}


def tool(name: str) -> str | None:
    local = TOOLS_BIN / name
    return str(local) if local.exists() else shutil.which(name)


def safe_copy(src: Path, dst: Path) -> None:
    """Copy a run without symlinks (they could point outside it) and without skipped folders."""
    dst.mkdir(parents=True)
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not (Path(dirpath) / d).is_symlink()]
        target = dst / Path(dirpath).relative_to(src)
        target.mkdir(parents=True, exist_ok=True)
        for name in filenames:
            f = Path(dirpath) / name
            if not f.is_symlink():
                shutil.copy2(f, target / name)


def find_project(run_dir: Path) -> tuple[Path, str]:
    """Shallowest package.json within 3 levels; Dart/Flutter runs are reported as unsupported."""
    for depth in range(4):
        pattern = "/".join(["*"] * depth)
        for marker, kind in (("package.json", "node"), ("pubspec.yaml", "dart")):
            for hit in sorted(run_dir.glob(f"{pattern}/{marker}" if pattern else marker)):
                rel = hit.relative_to(run_dir).parts
                if not any(part in SKIP_DIRS for part in rel) and not hit.is_symlink():
                    if kind == "dart":
                        sys.exit("Dart/Flutter runs are not supported yet (JS/TS only)")
                    return hit.parent, kind
    sys.exit(f"No package.json found under {run_dir}")


def source_files(root: Path) -> list[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix in SOURCE_EXT and not GENERATED.search(name) and not p.is_symlink():
                files.append(p)
    return sorted(files)


def count_loc(files: list[Path]) -> int:
    total = 0
    for f in files:
        for line in f.read_text(errors="ignore").splitlines():
            s = line.strip()
            if s and not s.startswith(("//", "/*", "*")):
                total += 1
    return total


def tool_versions() -> dict:
    out = {"python": sys.version.split()[0]}
    for name in ("biome", "jscpd", "tsc"):
        path = tool(name)
        if path:
            res = host_run([path, "--version"], HERE)
            out[name] = (res["out"] or res["err"]).strip().splitlines()[-1].split()[-1] if res["code"] == 0 else "unknown"
    try:
        import lizard
        out["lizard"] = lizard.version
    except ImportError:
        pass
    out["sandbox_image"] = sandbox.image()
    return out


# ---------------------------------------------------------------- checks

def install(work: Path, mode: str) -> dict:
    # Lifecycle scripts stay off: install only fetches packages. Network is open only here.
    lock = (work / "package-lock.json").exists()
    cmd = ["npm", "ci" if lock else "install", "--ignore-scripts", "--no-audit", "--no-fund"]
    res = sandbox.run(cmd, work, timeout=TIMEOUT, network="bridge", mode=mode)
    if res["code"] == 0:
        return {"status": "ok", "secs": res["secs"]}
    return failed(res, "install")


def biome(work: Path) -> dict:
    exe = tool("biome")
    if not exe:
        return skipped("biome not installed")
    res = host_run([exe, "check", "--reporter=json", "--colors=off", "--max-diagnostics=none", "."], work)
    m = re.search(r"\{.*\}", res["out"], re.S)
    if not m:
        return failed(res, "biome")
    data = json.loads(m.group(0))
    counts = {"errors": 0, "warnings": 0, "infos": 0}
    unformatted: set[str] = set()
    by_rule: dict[str, int] = {}
    for d in data.get("diagnostics", []):
        cat = d.get("category", "")
        if cat == "deserialize":  # problems of the config file, not of the run
            continue
        if cat.startswith(("format", "assist")):
            unformatted.add(str((d.get("location") or {}).get("path", cat)))
            continue
        sev = d.get("severity", "information")
        counts["errors" if sev == "error" else "warnings" if sev == "warning" else "infos"] += 1
        by_rule[cat] = by_rule.get(cat, 0) + 1
    top = dict(sorted(by_rule.items(), key=lambda kv: -kv[1])[:10])
    return {"status": "ok", **counts, "unformatted_files": len(unformatted), "top_rules": top, "secs": res["secs"]}


def tsc(work: Path, mode: str) -> dict:
    if not (work / "tsconfig.json").exists():
        return skipped("no tsconfig.json")
    if not (work / "node_modules" / ".bin" / "tsc").exists():
        return skipped("typescript is not installed in the run")
    res = sandbox.run(["node_modules/.bin/tsc", "--noEmit", "--pretty", "false"], work, timeout=TIMEOUT, mode=mode)
    if res["code"] is None:
        return failed(res, "tsc")
    return {"status": "ok", "errors": len(re.findall(r"error TS\d+", res["out"])), "secs": res["secs"]}


def eslint(work: Path, mode: str) -> dict:
    # The project's own config is code, so it only ever runs in the sandbox.
    has_cfg = any(work.glob("eslint.config.*")) or any(work.glob(".eslintrc*"))
    if not has_cfg or not (work / "node_modules" / ".bin" / "eslint").exists():
        return skipped("no ESLint config or ESLint not installed in the run")
    res = sandbox.run(["node_modules/.bin/eslint", ".", "--format", "json"], work, timeout=TIMEOUT, mode=mode)
    try:
        files = json.loads(res["out"])
    except json.JSONDecodeError:
        return failed(res, "eslint")
    return {"status": "ok", "errors": sum(f["errorCount"] for f in files),
            "warnings": sum(f["warningCount"] for f in files), "secs": res["secs"]}


def complexity(files: list[Path]) -> dict:
    try:
        import lizard
    except ImportError:
        return skipped("lizard not installed")
    ccns = [fn.cyclomatic_complexity for info in lizard.analyze_files([str(f) for f in files])
            for fn in info.function_list]
    if not ccns:
        return {"status": "ok", "functions": 0, "avg_ccn": 0.0, "functions_ccn_over_15": 0}
    return {"status": "ok", "functions": len(ccns), "avg_ccn": round(sum(ccns) / len(ccns), 2),
            "functions_ccn_over_15": sum(c > 15 for c in ccns)}


def duplication(work: Path) -> dict:
    exe = tool("jscpd")
    if not exe:
        return skipped("jscpd not installed")
    with tempfile.TemporaryDirectory() as out:
        res = host_run([exe, "--silent", "--reporters", "json", "--output", out, "--min-lines", "6",
                        "--ignore", "**/node_modules/**,**/dist/**,**/build/**", "."], work)
        report = Path(out) / "jscpd-report.json"
        if not report.exists():
            return failed(res, "jscpd")
        total = json.loads(report.read_text())["statistics"]["total"]
    return {"status": "ok", "duplicated_pct": total.get("percentage", 0), "clones": total.get("clones", 0)}


def suppressions(files: list[Path]) -> dict:
    pats = [re.compile(p) for p in SUPPRESSIONS]
    total = sum(1 for f in files for line in f.read_text(errors="ignore").splitlines()
                if len(line) <= cl.MAX_LINE and any(p.search(line) for p in pats))
    return {"status": "ok", "total": total}


def tests(work: Path, mode: str, argv: list[str] | None = None) -> dict:
    res = sandbox.run(argv or ["npm", "test", "--silent"], work, timeout=TIMEOUT, mode=mode)
    if res["code"] is None:
        return failed(res, "tests")
    return {"status": "ok", "passed_run": res["code"] == 0, "secs": res["secs"]}


def semgrep(work: Path) -> dict:
    exe = tool("semgrep")
    if not exe:
        return skipped("semgrep not installed")
    res = host_run([exe, "scan", "--config", "p/default", "--json", "--quiet", "."], work)
    try:
        return {"status": "ok", "findings": len(json.loads(res["out"])["results"])}
    except (json.JSONDecodeError, KeyError):
        return failed(res, "semgrep")


# ---------------------------------------------------------------- run metadata

def run_meta(run_dir: Path) -> dict:
    """Optional run.json from whoever ran the agent, e.g.
    {"cost_usd": 4.2, "tokens": 3100000, "duration_min": 95, "agent_tool": "...", "model": "...",
     "refusals": 0, "hit_limit": false}"""
    p = run_dir / "run.json"
    if not p.is_file() or p.is_symlink():
        return {}
    try:
        meta = json.loads(p.read_text())
    except json.JSONDecodeError:
        return {"error": "run.json is not valid JSON"}
    if isinstance(meta.get("tokens"), (int, float)):
        meta["tokens_m"] = round(meta["tokens"] / 1e6, 3)
    return meta


def prompt_hash(run_dir: Path) -> str | None:
    p = run_dir / "prompt.txt"
    if p.is_file() and not p.is_symlink():
        return hashlib.sha256(" ".join(p.read_text(errors="ignore").split()).encode()).hexdigest()[:12]
    return None


def fingerprint(files: list[Path]) -> list[str]:
    """Hashes of long, distinctive source lines, to detect runs that copied each other."""
    out = set()
    for f in files:
        for line in f.read_text(errors="ignore").splitlines():
            t = line.strip()
            if len(t) > 40 and not t.startswith(("import ", "//", "*", "export ")):
                out.add(hashlib.sha256(t.encode()).hexdigest()[:10])
    return sorted(out)


def copy_pairs(results: list[dict], threshold: float = COPY_THRESHOLD) -> list[tuple[str, str, float]]:
    """Run pairs whose shared fingerprints reach the threshold of the smaller run."""
    out = []
    for i, a in enumerate(results):
        for b in results[i + 1:]:
            fa, fb = set(a.get("fingerprint", [])), set(b.get("fingerprint", []))
            if fa and fb:
                share = len(fa & fb) / min(len(fa), len(fb))
                if share >= threshold:
                    out.append((a["run"], b["run"], round(share, 2)))
    return out


# ---------------------------------------------------------------- run

def sandbox_mode(choice: str) -> str | None:
    if choice == "process":
        return "process"
    if sandbox.runtime():
        return "container"
    if choice == "container":
        sys.exit("--sandbox container needs docker or podman on PATH")
    return None


def run(args) -> None:
    run_dir = Path(args.run_dir).resolve()
    project, kind = find_project(run_dir)
    mode = sandbox_mode(args.sandbox)
    no_exec = skipped("no container runtime: code of the run is not executed")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "project"
        safe_copy(project, work)
        overridden = []
        if not args.use_project_config:
            # Same rules for every run, so a run cannot win by loosening its own lint config.
            for old in list(work.glob("biome.json*")):
                old.unlink()
            shutil.copy(Path(args.config_dir) / "biome.json", work / "biome.json")
            overridden.append("biome.json")
        files = source_files(work)
        loc = count_loc(files)
        pristine = Path(args.pristine_spec) if args.pristine_spec else None
        spec_file = cl.find_spec_file(run_dir)
        spec_text = (spec_file.read_text(errors="ignore") if spec_file else "") or (
            pristine.read_text(errors="ignore") if pristine else "")
        items = cl.applicable(cl.load(args.checklist)["items"], kind, spec_text)

        c: dict = {}
        c["install"] = install(work, mode) if mode else no_exec
        installed = c["install"].get("status") == "ok"
        c["analyzer"] = biome(work)
        c["typecheck"] = tsc(work, mode) if mode and installed else no_exec if not mode else skipped("install failed")
        c["eslint"] = eslint(work, mode) if mode and installed else no_exec if not mode else skipped("install failed")
        c["complexity"] = complexity(files)
        c["duplication"] = duplication(work)
        c["suppressions"] = suppressions(files)
        c["hygiene"] = {"status": "ok", **cl.structural(run_dir, project, pristine)}
        c["mistake_patterns"] = {"status": "ok", "items": cl.count_patterns(files, work, items, loc)}
        if args.semgrep:
            c["security"] = semgrep(work)
        if args.self_tests:
            c["self_tests"] = tests(work, mode) if mode else no_exec
        if args.acceptance_dir:
            if mode:
                shutil.copytree(args.acceptance_dir, work / "_acceptance", symlinks=False)
                c["acceptance"] = tests(work, mode, shlex.split(args.acceptance_cmd) if args.acceptance_cmd else None)
            else:
                c["acceptance"] = no_exec
        result = {
            "run": run_dir.name,
            "condition": run_dir.name.split("__")[0],
            "kind": kind,
            "project_path": str(project.relative_to(run_dir)),
            "config_overridden": overridden,
            "source_files": len(files),
            "loc": loc,
            "sandbox": mode or "none",
            "tools": tool_versions(),
            "meta": run_meta(run_dir),
            "prompt_hash": prompt_hash(run_dir),
            "fingerprint": fingerprint(files),
            "checklist_items": [it["id"] for it in items],
            "structural_items": {it["id"]: it["structural"] for it in items if it.get("structural")},
            "calibration": {it["id"]: it["calibration"] for it in items if it.get("calibration")},
            "checks": c,
        }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(f"{run_dir.name}: {loc} LOC -> {args.out}")


# ---------------------------------------------------------------- human rating

def blind_id(run: str, salt: str) -> str:
    return "R" + hashlib.sha256(f"{salt}:{run}".encode()).hexdigest()[:6]


def sheet(args) -> None:
    """Blank rating sheet in an order unrelated to condition, with no model scores."""
    results = load_results(args.results)[0]
    salt = args.seed or secrets.token_hex(8)
    rows = sorted(({"id": blind_id(r["run"], salt), "run": r["run"]} for r in results), key=lambda x: x["id"])
    out = Path(args.out)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "rating_1_to_10", "notes"])
        w.writerows([[r["id"], "", ""] for r in rows])
    key = out.with_suffix(".key.json")
    key.write_text(json.dumps({r["id"]: r["run"] for r in rows}, indent=2) + "\n")
    print(f"wrote {out} (key: {key})")


def read_human(path: Path) -> dict[str, float]:
    key = json.loads(path.with_suffix(".key.json").read_text())
    out = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                out[key[row["id"]]] = float(row["rating_1_to_10"])
            except (KeyError, ValueError):
                continue
    return out


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def spearman(xs: list[float], ys: list[float]) -> float | None:
    """Rank correlation (ties share the average rank); None below 2 points or without variance."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    sx = sum((a - mx) ** 2 for a in rx)
    sy = sum((b - my) ** 2 for b in ry)
    if sx == 0 or sy == 0:
        return None
    return round(sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / (sx * sy) ** 0.5, 2)


# ---------------------------------------------------------------- report

# (label, path into result, per-kLOC?, kind) kind: "num", "rate" (share of reps)
METRICS = [
    ("LOC", "loc", False, "num"),
    ("Lint errors /kLOC", "checks.analyzer.errors", True, "num"),
    ("Lint warnings /kLOC", "checks.analyzer.warnings", True, "num"),
    ("Unformatted files", "checks.analyzer.unformatted_files", False, "num"),
    ("Type errors", "checks.typecheck.errors", False, "num"),
    ("ESLint errors /kLOC", "checks.eslint.errors", True, "num"),
    ("Avg cyclomatic complexity", "checks.complexity.avg_ccn", False, "num"),
    ("Functions CCN > 15", "checks.complexity.functions_ccn_over_15", False, "num"),
    ("Duplication %", "checks.duplication.duplicated_pct", False, "num"),
    ("Suppressions /kLOC", "checks.suppressions.total", True, "num"),
    ("Security findings", "checks.security.findings", False, "num"),
    ("Spec modified", "checks.hygiene.spec_modified.modified", False, "rate"),
    ("Build output left in run", "checks.hygiene.build_artifacts.count", False, "num"),
    ("Open items in status files", "checks.hygiene.open_items.count", False, "num"),
    ("Agent cost $", "meta.cost_usd", False, "num"),
    ("Agent tokens (M)", "meta.tokens_m", False, "num"),
    ("Agent wall time (min)", "meta.duration_min", False, "num"),
    ("Agent refusals", "meta.refusals", False, "num"),
    ("Agent hit usage limit", "meta.hit_limit", False, "rate"),
    ("Self-tests pass", "checks.self_tests.passed_run", False, "rate"),
    ("Acceptance pass", "checks.acceptance.passed_run", False, "rate"),
]
CODE_DIMS = ["spec_fit", "architecture", "readability", "error_handling", "testing", "security"]


def dig(obj: dict, path: str):
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def metric_values(results: list[dict], path: str, per_kloc: bool, kind: str) -> list[float]:
    out = []
    for r in results:
        v = dig(r, path)
        if v is None or isinstance(v, str):
            continue
        v = float(v)
        out.append(round(v / r["loc"] * 1000, 2) if per_kloc and r.get("loc") else v)
    return out


def review_metrics(rv: dict | None) -> dict:
    """Numbers from a review JSON. Stubbed reviews carry no information and give nothing."""
    if not rv or rv.get("stub"):
        return {}
    out: dict = {}
    code = (rv.get("code") or {}).get("data")
    if code:
        out["Code: average (1-5)"] = round(sum(code["scores"][d]["score"] for d in CODE_DIMS) / len(CODE_DIMS), 2)
    app = rv.get("app")
    if app is not None:
        out["App started"] = 1.0 if app.get("started") else 0.0
    ex = (rv.get("explore") or {}).get("data")
    if ex:
        feats = [f for f in ex["features"] if f["status"] != "not_tested"]
        if feats:
            ok = sum(1 if f["status"] == "works" else 0.5 if f["status"] == "partial" else 0 for f in feats)
            out["Explore: features working %"] = round(ok / len(feats) * 100, 1)
        out["Explore: critical and major bugs"] = sum(b["severity"] in ("critical", "major") for b in ex["bugs"])
    ov = (rv.get("overall") or {}).get("data")
    if ov:
        out["Overall rating (1-10)"] = ov["rating"]
    out["Review cost $"] = round(sum((rv.get(k) or {}).get("cost_usd", 0) for k in ("code", "explore", "overall")), 4)
    return out


def load_results(paths: list[str]) -> tuple[list[dict], dict[str, dict]]:
    results, reviews = [], {}
    for p in map(Path, paths):
        data = json.loads(p.read_text())
        if p.name.endswith(".review.json"):
            reviews[data.get("run", p.name.removesuffix(".review.json"))] = data
        else:
            results.append(data)
    return sorted(results, key=lambda r: r["run"]), reviews


def median(vals: list[float]) -> str:
    return f"{statistics.median(vals):.4g}" if vals else "n/a"


def warnings_for(results, reviews) -> list[str]:
    warns = []
    by_cond: dict[str, list] = {}
    for r in results:
        by_cond.setdefault(r["condition"], []).append(r)
    for cond, rs in by_cond.items():
        if len(rs) < MIN_REPS:
            warns.append(f"Condition {cond} has {len(rs)} rep(s); at least {MIN_REPS} are needed before medians mean anything.")
    hashes = {r["prompt_hash"] for r in results if r.get("prompt_hash")}
    if len(hashes) > 1:
        warns.append(f"Runs were started with {len(hashes)} different prompts.")
    missing = [r["run"] for r in results if not r.get("prompt_hash")]
    if missing:
        warns.append("No prompt.txt in: " + ", ".join(missing) + ".")
    for r in results:
        if (r.get("meta") or {}).get("hit_limit"):
            warns.append(f"{r['run']} hit a usage limit and may have stopped early.")
    for a, b, share in copy_pairs(results):
        warns.append(f"{a} and {b} share {share:.0%} of their distinctive lines (possible copying).")
    if any(rv.get("stub") for rv in reviews.values()):
        warns.append("Some reviews are stubbed and are left out of every review metric.")
    models = {(rv.get("model"), rv.get("effort")) for rv in reviews.values() if not rv.get("stub")}
    if len(models) > 1:
        warns.append("Reviews used different models or effort levels; ratings are not comparable.")
    ratings = [m["Overall rating (1-10)"] for rv in reviews.values() if (m := review_metrics(rv)) and "Overall rating (1-10)" in m]
    if ratings and min(ratings) >= SATURATION_RATING:
        warns.append(f"Every run is rated {SATURATION_RATING} or higher: the spec may be too easy to separate setups.")
    return warns


def human_section(results, reviews, human: dict[str, float]) -> list[str]:
    pairs = [(human[r["run"]], review_metrics(reviews.get(r["run"])).get("Overall rating (1-10)"))
             for r in results if r["run"] in human]
    pairs = [(h, m) for h, m in pairs if m is not None]
    lines = ["## Model rating against your rating", ""]
    if len(pairs) < 4:
        return lines + [f"{len(pairs)} runs have both ratings; at least 4 are needed for a rank correlation.", ""]
    rho = spearman([h for h, _ in pairs], [m for _, m in pairs])
    return lines + [f"Spearman rank correlation over {len(pairs)} runs: {rho}", ""]


def report(args) -> None:
    results, reviews = load_results(args.results)
    if not results:
        sys.exit("no result files")
    human = read_human(Path(args.human)) if args.human else {}
    conditions = sorted({r["condition"] for r in results})
    per_run_review = {r["run"]: review_metrics(reviews.get(r["run"])) for r in results}
    lines = ["# Agent run comparison", ""]
    warns = warnings_for(results, reviews)
    if warns:
        lines += ["## Warnings", ""] + [f"- {w}" for w in warns] + [""]
    lines += ["## Medians per condition", "", "| Metric | " + " | ".join(
        f"{c} (n={sum(r['condition'] == c for r in results)})" for c in conditions) + " |",
        "|---|" + "---|" * len(conditions)]
    for label, path, per_kloc, kind in METRICS:
        row = [median(metric_values([r for r in results if r["condition"] == c], path, per_kloc, kind)) for c in conditions]
        if any(v != "n/a" for v in row):
            lines.append(f"| {label} | " + " | ".join(row) + " |")
    review_labels = sorted({k for m in per_run_review.values() for k in m})
    for label in review_labels:
        row = [median([m[label] for r in results if r["condition"] == c and label in (m := per_run_review[r["run"]])]) for c in conditions]
        lines.append(f"| {label} | " + " | ".join(row) + " |")
    per_dollar = {c: [m["Overall rating (1-10)"] / r["meta"]["cost_usd"]
                      for r in results if r["condition"] == c and (m := per_run_review[r["run"]])
                      and "Overall rating (1-10)" in m and (r.get("meta") or {}).get("cost_usd")]
                  for c in conditions}
    if any(per_dollar.values()):
        lines.append("| Rating per agent dollar | " + " | ".join(median(per_dollar[c]) for c in conditions) + " |")
    lines += ["", "## Runs", "", "| Run | LOC | Lint errors | Type errors | Duplication % | Cost $ | Rating |", "|---|---|---|---|---|---|---|"]
    for r in results:
        g = lambda p: "n/a" if dig(r, p) is None else dig(r, p)  # noqa: E731
        rating = per_run_review[r["run"]].get("Overall rating (1-10)", "n/a")
        lines.append(f"| {r['run']} | {r['loc']} | {g('checks.analyzer.errors')} | {g('checks.typecheck.errors')} | "
                     f"{g('checks.duplication.duplicated_pct')} | {g('meta.cost_usd')} | {rating} |")
    lines += ["", "## Common mistakes", ""] + mistakes_table(results, conditions)
    skips = [(r["run"], k, v.get("reason", "")) for r in results for k, v in r["checks"].items() if v.get("status") == "skipped"]
    lines += ["", "## Skipped checks", ""]
    lines += ["| Run | Check | Reason |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in skips] if skips else ["None."]
    lines.append("")
    if human:
        lines += human_section(results, reviews, human)
    lines += ["## Provenance", "", "| Run | Sandbox | Tools |", "|---|---|---|"]
    lines += [f"| {r['run']} | {r.get('sandbox')} | {', '.join(f'{k} {v}' for k, v in r.get('tools', {}).items() if k != 'sandbox_image')} |" for r in results]
    text = "\n".join(lines) + "\n"
    if args.md:
        Path(args.md).write_text(text)
    print(text)


def mistakes_table(results: list[dict], conditions: list[str]) -> list[str]:
    ids = sorted({i for r in results for i in r.get("checklist_items", [])})
    rows = ["| Item | " + " | ".join(conditions) + " |", "|---|" + "---|" * len(conditions)]
    for iid in ids:
        cells = []
        for c in conditions:
            rs = [r for r in results if r["condition"] == c and iid in r.get("checklist_items", [])]
            cells.append(mistake_cell(iid, rs))
        if any(cell != "-" for cell in cells):
            rows.append(f"| {iid} | " + " | ".join(cells) + " |")
    return rows


def mistake_cell(iid: str, rs: list[dict]) -> str:
    if not rs:
        return "-"
    flagged = sum(1 for r in rs if (name := r.get("structural_items", {}).get(iid))
                  and r["checks"]["hygiene"][name].get("flagged"))
    pats = [r["checks"]["mistake_patterns"]["items"][iid]["per_kloc"] for r in rs
            if iid in r["checks"]["mistake_patterns"]["items"]]
    parts = []
    if flagged:
        parts.append(f"{flagged}/{len(rs)} runs")
    if pats and statistics.median(pats) > 0:
        cal = rs[0].get("calibration", {}).get(iid)
        over = " (above reference p90)" if cal and statistics.median(pats) > cal["p90"] else ""
        parts.append(f"{statistics.median(pats):.4g}/kLOC{over}")
    return ", ".join(parts) or "-"


# ---------------------------------------------------------------- cli

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="analyze one run folder")
    r.add_argument("run_dir")
    r.add_argument("--out", required=True)
    r.add_argument("--config-dir", default=str(DEFAULT_CONFIG))
    r.add_argument("--checklist", default=str(cl.DEFAULT_PATH))
    r.add_argument("--use-project-config", action="store_true", help="keep the run's own Biome config")
    r.add_argument("--pristine-spec", help="the original spec, to detect runs that edited theirs")
    r.add_argument("--semgrep", action="store_true")
    r.add_argument("--self-tests", action="store_true", help="run the tests the run wrote (not comparable)")
    r.add_argument("--acceptance-dir", help="owner-written tests copied into every run as _acceptance/")
    r.add_argument("--acceptance-cmd", help="command that runs them, split like a shell would (default: npm test)")
    r.add_argument("--sandbox", choices=["auto", "container", "process"], default="auto",
                   help="container: docker or podman (default when found); process: trusted runs only, no isolation")
    r.set_defaults(fn=run)
    s = sub.add_parser("sheet", help="blank human-rating sheet in blinded order")
    s.add_argument("results", nargs="+")
    s.add_argument("--out", required=True)
    s.add_argument("--seed", help="fixed salt for a reproducible order")
    s.set_defaults(fn=sheet)
    p = sub.add_parser("report", help="comparison report over result files (and *.review.json)")
    p.add_argument("results", nargs="+")
    p.add_argument("--md")
    p.add_argument("--human", help="filled sheet; its .key.json must sit next to it")
    p.set_defaults(fn=report)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
