"""Offline checks of the pinning rules: exact versions, SHA-pinned actions, digests, cooldown.

Whether each pinned version exists and is old enough is checked against the registries when
a pin changes (see the pull request that introduced it); Dependabot's cooldown does it afterwards.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
EXACT = re.compile(r"^\d+\.\d+\.\d+$")


def test_tool_package_versions_are_exact_and_locked():
    tools = ROOT / "analyzer" / "tools"
    deps = json.loads((tools / "package.json").read_text())["dependencies"]
    lock = json.loads((tools / "package-lock.json").read_text())["packages"]
    assert deps and all(EXACT.match(v) for v in deps.values())
    for name, version in deps.items():
        assert lock[f"node_modules/{name}"]["version"] == version
        assert lock[f"node_modules/{name}"]["integrity"]


def test_python_requirements_are_exact():
    for f in ("requirements.txt", "requirements-dev.txt"):
        lines = [x.strip() for x in (ROOT / f).read_text().splitlines() if x.strip() and not x.startswith(("#", "-r"))]
        assert lines and all(re.fullmatch(r"[A-Za-z0-9_.-]+==\d+(\.\d+)*", x) for x in lines), f


def test_every_action_is_pinned_to_a_commit_with_version_comment():
    assert WORKFLOWS
    for wf in WORKFLOWS:
        for line in wf.read_text().splitlines():
            m = re.search(r"uses:\s*(\S+)", line)
            if m and not m.group(1).startswith("./"):
                assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", m.group(1)), f"{wf.name}: {line.strip()}"
                assert re.search(r"#\s*v\d+\.\d+\.\d+", line), f"{wf.name}: version comment missing: {line.strip()}"


def test_images_are_pinned_by_digest():
    for text in [(ROOT / "analyzer" / "sandbox" / "Dockerfile").read_text()] + [w.read_text() for w in WORKFLOWS]:
        for ref in re.findall(r"(?:FROM\s+|docker run [^\n]*?)((?:docker\.io/)[\w./-]+(?::[\w.-]+)?(?:@sha256:[0-9a-f]{64})?)", text):
            assert "@sha256:" in ref, ref


def test_node_versions_agree():
    docker = re.search(r"node:(\d+\.\d+\.\d+)-", (ROOT / "analyzer" / "sandbox" / "Dockerfile").read_text()).group(1)
    for wf in WORKFLOWS:
        for v in re.findall(r"node-version:\s*(\S+)", wf.read_text()):
            assert v == docker, wf.name


def test_workflow_permissions_are_least_privilege():
    for wf in WORKFLOWS:
        text = wf.read_text()
        assert re.search(r"^permissions:\s*\{\}\s*$", text, re.M), f"{wf.name}: top-level permissions must be {{}}"
        assert "pull_request_target" not in text
        assert "persist-credentials: false" in text or "checkout" not in text
        assert "${{" not in run_scripts(text), f"{wf.name}: expression inside a run script"


def run_scripts(text: str) -> str:
    """All `run:` script text of a workflow (one-line and block form)."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        m = re.match(r"(\s*)(?:- )?run:\s*(.*)", lines[i])
        i += 1
        if not m:
            continue
        out.append(m.group(2))
        indent = len(m.group(1))
        while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def test_dependabot_covers_every_ecosystem_with_cooldown():
    text = (ROOT / ".github" / "dependabot.yml").read_text()
    ecosystems = re.findall(r"package-ecosystem:\s*(\S+)", text)
    assert sorted(ecosystems) == ["docker", "github-actions", "npm", "pip"]
    assert len(re.findall(r"default-days:\s*7\b", text)) == len(ecosystems)
