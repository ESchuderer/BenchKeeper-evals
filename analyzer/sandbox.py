"""Run commands that execute code of an untrusted run, inside a throwaway container.

The container gets: only the run copy mounted, no environment except what the caller passes,
no network unless asked, no capabilities, memory/CPU/process limits and a timeout.
Mode "process" is for trusted runs only: scrubbed environment and a timeout, no file or
network isolation.
"""
from __future__ import annotations

import os
import re
import secrets
import shutil
import subprocess
import time
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parent / "sandbox" / "Dockerfile"
SAFE_ENV = ("PATH", "LANG", "LC_ALL")


def image() -> str:
    m = re.search(r"^FROM\s+(\S+)", DOCKERFILE.read_text(), re.M)
    if not m:
        raise RuntimeError("no FROM line in sandbox/Dockerfile")
    return m.group(1)


def runtime() -> str | None:
    return next((b for b in ("docker", "podman") if shutil.which(b)), None)


def is_podman(binary: str) -> bool:
    if binary == "podman":
        return True
    try:
        out = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return "podman" in out.lower()


def container_argv(binary: str, cmd: list[str], workdir: Path, *, name: str, network: str = "none",
                   memory: str = "2g", cpus: str = "2", pids: int = 512,
                   env: dict[str, str] | None = None, publish: str | None = None,
                   podman: bool = False) -> list[str]:
    user = ["--userns=keep-id"] if podman else ["--user", f"{os.getuid()}:{os.getgid()}"]
    argv = [binary, "run", "--rm", "--init", "--name", name, *user,
            "--network", network, "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--memory", memory, "--cpus", cpus, "--pids-limit", str(pids),
            "--read-only", "--tmpfs", "/tmp:rw,size=512m",
            "--mount", f"type=bind,source={workdir},target=/work",
            "--workdir", "/work", "--env", "HOME=/tmp"]
    for key, value in (env or {}).items():
        argv += ["--env", f"{key}={value}"]
    if publish:
        argv += ["--publish", publish]
    return [*argv, image(), *cmd]


def run(cmd: list[str], workdir: Path, *, timeout: int = 600, network: str = "none",
        mode: str = "container", env: dict[str, str] | None = None) -> dict:
    """Run cmd (argv list); never raises. Returns code, out, err, secs and flags."""
    start = time.time()
    name = f"qa-{secrets.token_hex(6)}"
    binary = None
    if mode == "container":
        binary = runtime()
        if binary is None:
            return {"code": None, "out": "", "err": "no container runtime", "secs": 0, "missing": True}
        argv = container_argv(binary, cmd, workdir, name=name, network=network, env=env,
                              podman=is_podman(binary))
        child_env = {k: os.environ[k] for k in SAFE_ENV if k in os.environ}
        cwd = None
    else:
        argv = list(cmd)
        child_env = {k: os.environ[k] for k in SAFE_ENV if k in os.environ} | {"HOME": str(workdir)} | (env or {})
        cwd = workdir
    try:
        p = subprocess.run(argv, cwd=cwd, env=child_env, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return {"code": p.returncode, "out": p.stdout, "err": p.stderr, "secs": round(time.time() - start, 1)}
    except FileNotFoundError:
        return {"code": None, "out": "", "err": "not found", "secs": 0, "missing": True}
    except subprocess.TimeoutExpired:
        if binary:
            subprocess.run([binary, "rm", "-f", name], capture_output=True, timeout=60)
        return {"code": None, "out": "", "err": "timeout", "secs": timeout, "timeout": True}
