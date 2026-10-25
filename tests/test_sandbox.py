import subprocess
from pathlib import Path

import pytest

import sandbox

needs_runtime = pytest.mark.skipif(not sandbox.runtime(), reason="needs docker or podman")


def test_image_is_pinned_by_digest():
    assert "@sha256:" in sandbox.image()


def test_container_argv_is_locked_down():
    argv = sandbox.container_argv("docker", ["true"], Path("/w"), name="n", env={"CI": "1"})
    joined = " ".join(argv)
    assert "--network none" in joined and "--cap-drop ALL" in joined and "no-new-privileges" in joined
    assert "--read-only" in argv and "--memory" in argv and "--pids-limit" in argv
    assert joined.count("--mount") == 1 and "source=/w,target=/work" in joined
    assert argv[-2:] == [sandbox.image(), "true"] and "--env CI=1" in joined


def test_container_argv_only_passes_env_it_is_given(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "canary")
    assert "canary" not in " ".join(sandbox.container_argv("docker", ["true"], Path("/w"), name="n"))


@needs_runtime
def test_run_cannot_read_env_secret_or_files_outside_it(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "canary-secret-value")
    work = tmp_path / "run"
    work.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("canary-outside-file")
    script = f'printenv ANTHROPIC_API_KEY; cat "{outside}"; touch /etc/x; ls /sys/class/net; echo done'
    res = sandbox.run(["sh", "-c", script], work, timeout=120)
    assert res["code"] == 0
    assert "canary" not in res["out"]  # neither the env secret nor the file content
    assert "No such file" in res["err"] and "Read-only file system" in res["err"]
    assert res["out"].split() == ["lo", "done"]  # no network interface except loopback


@needs_runtime
def test_run_can_write_only_inside_the_run_copy(tmp_path):
    res = sandbox.run(["sh", "-c", "echo hi > /work/out.txt"], tmp_path, timeout=120)
    assert res["code"] == 0 and (tmp_path / "out.txt").read_text() == "hi\n"


@needs_runtime
def test_timeout_kills_the_container(tmp_path):
    res = sandbox.run(["sleep", "60"], tmp_path, timeout=5)
    assert res.get("timeout") and res["code"] is None
    ps = subprocess.run([sandbox.runtime(), "ps", "-q", "--filter", "name=qa-"], capture_output=True, text=True)
    assert ps.stdout.strip() == ""


def test_process_mode_scrubs_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "canary-secret-value")
    res = sandbox.run(["sh", "-c", "printenv ANTHROPIC_API_KEY; echo done"], tmp_path, mode="process")
    assert res["out"] == "done\n"
