"""Common-mistakes checklist: loading, validation, pattern counting and structural checks.

An item is checked up to four ways: regex patterns (hits per kLOC), a structural check
(by name, see STRUCTURAL), a question for the code reviewer and a step for the tester.
"""
from __future__ import annotations

import hashlib
import json
import re
import statistics
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent / "config" / "checklist.json"
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_LINE = 2000  # longer lines (minified or generated text) are not matched
LOCKFILES = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb")
BUILD_DIRS = ("dist", "build", ".next", "out", "coverage")
SPEC_NAMES = ("SPEC.md", "spec.md", "BRIEF.md", "brief.md", "REQUIREMENTS.md")
STATUS_NAMES = ("STATUS.md", "PROGRESS.md", "TODO.md", "TASKS.md", "PLAN.md")
OPEN_ITEM = re.compile(r"^\s*[-*]\s*\[ \]|\bTODO\b|\bnot (yet )?implemented\b", re.I)
TEST_FILE = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$")


def load(path: Path | str | None = None) -> dict:
    return json.loads(Path(path or DEFAULT_PATH).read_text())


def validate(data: dict) -> list[str]:
    """Return a list of problems; empty means the checklist is usable."""
    errors: list[str] = []
    seen: set[str] = set()
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return ["items must be a non-empty list"]
    for it in items:
        iid = it.get("id", "")
        if not ID_RE.match(str(iid)):
            errors.append(f"bad id: {iid!r}")
        if iid in seen:
            errors.append(f"duplicate id: {iid}")
        seen.add(iid)
        for key in ("title", "review", "explore"):
            if not isinstance(it.get(key), str) or not it[key].strip():
                errors.append(f"{iid}: {key} must be a non-empty string")
        if it.get("structural") is not None and it["structural"] not in STRUCTURAL:
            errors.append(f"{iid}: unknown structural check {it['structural']!r}")
        for pat in it.get("patterns", []):
            try:
                re.compile(pat["regex"])
            except (re.error, KeyError, TypeError) as exc:
                errors.append(f"{iid}: bad pattern {pat!r}: {exc}")
        spec = it.get("applies_if_spec_matches")
        if spec is not None:
            try:
                re.compile(spec)
            except re.error as exc:
                errors.append(f"{iid}: bad applies_if_spec_matches: {exc}")
    return errors


def applicable(items: list[dict], kind: str, spec_text: str) -> list[dict]:
    out = []
    for it in items:
        if kind not in it.get("applies_to", [kind]):
            continue
        cond = it.get("applies_if_spec_matches")
        if cond and not re.search(cond, spec_text, re.I):
            continue
        out.append(it)
    return out


def _lines(path: Path):
    try:
        yield from path.read_text(errors="ignore").splitlines()
    except OSError:
        return


def count_patterns(files: list[Path], root: Path, items: list[dict], loc: int) -> dict:
    """Pattern hits per item over the given source files; per_kloc uses the run's LOC."""
    result = {}
    for it in items:
        pats = [re.compile(p["regex"]) for p in it.get("patterns", [])]
        if not pats:
            continue
        hits, where = 0, []
        for f in files:
            n = sum(1 for line in _lines(f) if len(line) <= MAX_LINE and any(p.search(line) for p in pats))
            if n:
                hits += n
                where.append(str(f.relative_to(root)))
        result[it["id"]] = {
            "hits": hits,
            "per_kloc": round(hits / loc * 1000, 2) if loc else 0.0,
            "files": sorted(where)[:5],
        }
    return result


# ------------------------------------------------------------ structural checks

def _norm_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()


def find_spec_file(run_dir: Path) -> Path | None:
    for name in SPEC_NAMES:
        hit = next(iter(sorted(run_dir.glob(name))), None) or next(iter(sorted(run_dir.glob(f"*/{name}"))), None)
        if hit:
            return hit
    return None


def _spec_modified(run_dir: Path, project: Path, pristine: Path | None) -> dict:
    spec = find_spec_file(run_dir)
    if pristine is None or spec is None:
        return {"flagged": False, "modified": None}
    changed = _norm_hash(spec.read_text(errors="ignore")) != _norm_hash(pristine.read_text(errors="ignore"))
    return {"flagged": changed, "modified": changed}


def _missing_lockfile(run_dir: Path, project: Path, pristine: Path | None) -> dict:
    missing = not any((project / name).exists() for name in LOCKFILES)
    return {"flagged": missing, "count": int(missing)}


def _build_artifacts(run_dir: Path, project: Path, pristine: Path | None) -> dict:
    found = sorted(d for d in BUILD_DIRS if (project / d).is_dir() and not (project / d).is_symlink())
    return {"flagged": bool(found), "count": len(found), "dirs": found}


def _open_items(run_dir: Path, project: Path, pristine: Path | None) -> dict:
    count = 0
    for name in STATUS_NAMES:
        for base in {run_dir, project}:
            f = base / name
            if f.is_file() and not f.is_symlink():
                count += sum(1 for line in _lines(f) if OPEN_ITEM.search(line))
    return {"flagged": count > 0, "count": count}


def _no_tests(run_dir: Path, project: Path, pristine: Path | None) -> dict:
    has = any(TEST_FILE.search(p.name) for p in project.rglob("*") if "node_modules" not in p.parts)
    return {"flagged": not has, "count": int(not has)}


STRUCTURAL = {
    "spec_modified": _spec_modified,
    "missing_lockfile": _missing_lockfile,
    "build_artifacts": _build_artifacts,
    "open_items": _open_items,
    "no_tests": _no_tests,
}


def structural(run_dir: Path, project: Path, pristine: Path | None = None) -> dict:
    return {name: fn(run_dir, project, pristine) for name, fn in STRUCTURAL.items()}


# ------------------------------------------------------------ review and explore prompts

def review_questions(items: list[dict]) -> list[dict]:
    return [{"id": it["id"], "question": it["review"]} for it in items]


def explore_steps(items: list[dict]) -> list[dict]:
    return [{"id": it["id"], "step": it["explore"]} for it in items]


# ------------------------------------------------------------ calibration

def p90(values: list[float]) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, int(0.9 * len(s)))] if s else 0.0


def calibrate(items: list[dict], per_impl: list[dict]) -> dict:
    """Reference distribution per pattern item from {id: per_kloc} of several implementations."""
    out = {}
    for it in items:
        if not it.get("patterns"):
            continue
        vals = [impl.get(it["id"], 0.0) for impl in per_impl]
        if not vals:
            continue
        out[it["id"]] = {
            "n": len(vals),
            "fire_rate": round(sum(v > 0 for v in vals) / len(vals), 2),
            "median": round(statistics.median(vals), 2),
            "p90": round(p90(vals), 2),
        }
    return out
