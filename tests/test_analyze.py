import json
import shutil
import sys

import pytest

import analyze as az
import sandbox
from conftest import FIXTURES, copy_run

pytestmark = pytest.mark.skipif(not sandbox.runtime(), reason="needs docker or podman for the sandbox")


def args(run_dir, out, **kw):
    base = dict(run_dir=str(run_dir), out=str(out), config_dir=str(az.DEFAULT_CONFIG), checklist=str(az.cl.DEFAULT_PATH),
                use_project_config=False, pristine_spec=str(FIXTURES / "SPEC.md"), semgrep=False, self_tests=False,
                acceptance_dir=None, acceptance_cmd=None, sandbox="auto")
    return type("A", (), {**base, **kw})


def test_run_on_fixture_runs(tmp_path):
    for name in ("with-setup__1", "baseline__1"):
        az.run(args(FIXTURES / "runs" / name, tmp_path / f"{name}.json"))
    good = json.loads((tmp_path / "with-setup__1.json").read_text())
    bad = json.loads((tmp_path / "baseline__1.json").read_text())
    assert good["condition"] == "with-setup" and good["loc"] > 0
    assert good["checks"]["install"]["status"] == "ok"
    assert good["checks"]["suppressions"]["total"] == 0
    assert bad["checks"]["hygiene"]["spec_modified"]["modified"] is True
    assert bad["checks"]["mistake_patterns"]["items"]["empty-catch"]["hits"] == 1
    assert good["meta"]["tokens_m"] == 1.2 and good["prompt_hash"] == bad["prompt_hash"]
    assert good["tools"]["sandbox_image"] == sandbox.image()
    az.report(type("A", (), {"results": [str(tmp_path / "with-setup__1.json"), str(tmp_path / "baseline__1.json")],
                             "md": str(tmp_path / "r.md"), "human": None}))
    assert "| Run | LOC" in (tmp_path / "r.md").read_text()


def test_fixed_config_replaces_the_run_config(tmp_path, monkeypatch):
    run = copy_run("with-setup__1", tmp_path)
    (run / "biome.json").write_text('{"linter": {"enabled": false}}')
    seen = {}

    def spy(work):
        seen["config"] = json.loads((work / "biome.json").read_text())
        return az.skipped("spy")

    monkeypatch.setattr(az, "biome", spy)
    az.run(args(run, tmp_path / "o.json"))
    assert seen["config"]["linter"]["enabled"] is True
    assert json.loads((tmp_path / "o.json").read_text())["config_overridden"] == ["biome.json"]
    seen.clear()
    az.run(args(run, tmp_path / "o2.json", use_project_config=True))
    assert seen["config"]["linter"]["enabled"] is False


def test_symlinks_are_not_copied(tmp_path):
    run = copy_run("with-setup__1", tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside")
    (run / "src" / "link.js").symlink_to(outside)
    (run / "linked").symlink_to(tmp_path)
    dst = tmp_path / "copy"
    az.safe_copy(run, dst)
    assert not (dst / "src" / "link.js").exists() and not (dst / "linked").exists()
    assert (dst / "src" / "counter.js").exists()


def test_dart_runs_are_rejected(tmp_path):
    (tmp_path / "r__1").mkdir()
    (tmp_path / "r__1" / "pubspec.yaml").write_text("name: x\n")
    with pytest.raises(SystemExit, match="Dart/Flutter"):
        az.run(args(tmp_path / "r__1", tmp_path / "o.json"))
