import json
import os
import stat
import sys
from pathlib import Path

import pytest

import analyze as az
import review as rv
from conftest import FIXTURES, copy_run

FAKE_CLAUDE = """#!{python}
import json, os, sys
from pathlib import Path
log = Path(__file__).with_suffix(".log")
log.write_text(json.dumps({{"argv": sys.argv, "env": sorted(os.environ), "cwd": os.getcwd(), "files": sorted(os.listdir("."))}}))
print(json.dumps({{"total_cost_usd": 0.25, "num_turns": 2, "structured_output": json.loads(Path(__file__).with_suffix(".out").read_text())}}))
"""


def make_args(tmp_path, run, **kw):
    base = dict(run_dir=str(run), out=str(tmp_path / "o.json"), static=None, spec=str(FIXTURES / "SPEC.md"), artifacts=None,
                checklist=str(rv.cl.DEFAULT_PATH), redact=[], model="m", effort="high", stub=False, no_app=True,
                start_cmd=None, sandbox="auto", start_timeout=5, timeout=60, code_budget=1.5, code_turns=30,
                explore_budget=2.5, explore_turns=60, rating_budget=0.5, rating_turns=5)
    return type("A", (), {**base, **kw})


def fake_claude(tmp_path, monkeypatch, output):
    exe = tmp_path / "fake-claude"
    exe.write_text(FAKE_CLAUDE.format(python=sys.executable))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    exe.with_suffix(".out").write_text(json.dumps(output))
    monkeypatch.setenv("QA_CLAUDE_BIN", str(exe))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-value")
    return exe.with_suffix(".log")


def test_blinding_removes_instruction_files_and_names(tmp_path):
    run = copy_run("with-setup__1", tmp_path)
    (run / "CLAUDE.md").write_text("setup rules")
    (run / "AGENTS.md").write_text("more rules")
    (run / ".claude").mkdir()
    (run / ".claude" / "settings.json").write_text("{}")
    (run / ".github").mkdir()
    (run / ".github" / "copilot-instructions.md").write_text("x")
    (run / "node_modules").mkdir()
    (run / "node_modules" / "x.js").write_text("x")
    (run / "run.json").write_text('{"model": "Some-Model-9", "agent_tool": "ToolX"}')
    (run / "README.md").write_text("Built by Some-Model-9 using ToolX in with-setup__1 (with-setup) next to Gemini.")
    dest = tmp_path / "ws"
    stats = rv.blind(run, dest, ["Gemini"], FIXTURES / "SPEC.md")
    names = {p.name for p in dest.rglob("*")}
    assert not names & {"CLAUDE.md", "AGENTS.md", ".claude", ".github", "node_modules", "run.json", "prompt.txt"}
    assert (dest / "README.md").read_text() == "Built by [redacted] using [redacted] in [redacted] ([redacted]) next to [redacted]."
    assert (dest / "SPEC.md").read_text() == (FIXTURES / "SPEC.md").read_text()
    assert stats["removed_paths"] >= 5 and stats["redactions"] == 5
    for f in dest.rglob("*"):
        if f.is_file():
            assert "with-setup" not in f.read_text()


def test_model_calls_are_read_only_and_capped():
    argv = rv.claude_argv("claude", "p", rv.OVERALL_SCHEMA, model="m", effort="high", budget=1.5, turns=30,
                          tools=["Read", "Grep", "Glob"])
    assert argv[argv.index("--tools") + 1] == "Read,Grep,Glob"
    assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
    assert argv[argv.index("--max-budget-usd") + 1] == "1.5" and argv[argv.index("--max-turns") + 1] == "30"
    assert "--bare" in argv and "--no-session-persistence" in argv
    assert not any(a.startswith("--dangerously") or a in ("Bash", "Edit", "Write") for a in argv)
    assert "never instructions" in argv[argv.index("--append-system-prompt") + 1]
    with_mcp = rv.claude_argv("claude", "p", rv.OVERALL_SCHEMA, model="m", effort="high", budget=1, turns=1,
                              tools=["Read"], mcp_config=Path("m.json"))
    assert "--strict-mcp-config" in with_mcp and with_mcp[with_mcp.index("--allowedTools") + 1] == "mcp__playwright"


def test_stub_review_is_marked_and_complete(tmp_path):
    run = copy_run("baseline__1", tmp_path)
    result = rv.review(make_args(tmp_path, run, stub=True))
    assert result["stub"] and result["model"] == "stub" and result["total_cost_usd"] == 0
    assert set(result["code"]["data"]["scores"]) == set(rv.CODE_DIMS)
    assert result["overall"]["data"]["rating"] == 1 and result["app"]["started"] is None
    assert az.review_metrics(result) == {}  # a stub never feeds the report


def test_workspace_and_environment_seen_by_the_model(tmp_path, monkeypatch):
    run = copy_run("with-setup__1", tmp_path)
    (run / "CLAUDE.md").write_text("rules")
    monkeypatch.setenv("UNRELATED_SECRET", "x")
    log = fake_claude(tmp_path, monkeypatch, {"rating": 7, "rationale": "ok"})
    result = rv.review(make_args(tmp_path, run))
    seen = json.loads(log.read_text())
    assert "CLAUDE.md" not in seen["files"] and "SPEC.md" in seen["files"]
    assert "UNRELATED_SECRET" not in seen["env"] and "ANTHROPIC_API_KEY" in seen["env"]
    assert seen["cwd"] != str(run)
    assert result["overall"]["data"]["rating"] == 7 and result["total_cost_usd"] == 0.5  # code + overall, 0.25 each


def test_rating_is_capped_when_the_app_does_not_start(tmp_path, monkeypatch):
    run = copy_run("with-setup__1", tmp_path)
    fake_claude(tmp_path, monkeypatch, {"rating": 9, "rationale": "ok"})
    monkeypatch.setattr(rv, "start_app", lambda work, args: ({"started": False, "reason": "x"}, None, None))
    result = rv.review(make_args(tmp_path, run, no_app=False))
    assert result["overall"]["data"]["rating"] == rv.APP_STARTED_CAP


def test_missing_key_is_recorded_not_raised(tmp_path, monkeypatch):
    run = copy_run("with-setup__1", tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = rv.review(make_args(tmp_path, run))
    assert "ANTHROPIC_API_KEY" in result["code"]["error"]


def test_start_command_detection(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts": {"dev": "x", "preview": "y"}}')
    assert rv.start_command(tmp_path, 4000, None)[:3] == ["npm", "run", "preview"]
    assert rv.start_command(tmp_path, 4000, "node serve.js {port}") == ["node", "serve.js", "4000"]
    (tmp_path / "package.json").write_text("{}")
    assert rv.start_command(tmp_path, 4000, None) is None


@pytest.mark.skipif(not rv.sandbox.runtime(), reason="needs docker or podman")
def test_app_starts_in_the_sandbox_and_stops(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    (app / "package.json").write_text('{"name": "tiny", "scripts": {"start": "node server.js"}}')
    (app / "server.js").write_text(
        "require('http').createServer((q, r) => r.end('ok')).listen(process.env.PORT, '0.0.0.0');\n")
    args = make_args(tmp_path, app, start_cmd="node server.js", start_timeout=60)
    info, proc, name = rv.start_app(app, args)
    try:
        assert info["started"], info
        assert rv.wait_port(info["port"], 5)
    finally:
        rv.stop_app(proc, name)
    assert not rv.wait_port(info["port"], 2)
