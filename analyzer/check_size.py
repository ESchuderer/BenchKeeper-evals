#!/usr/bin/env python3
"""Fail when git tracks raw runs, transcripts, screenshots, archives or large files.

Only result JSON and reports belong in git; raw runs live in release assets or another store.
  python analyzer/check_size.py [--max-kb 512]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

FORBIDDEN_PREFIXES = ("runs/", "artifacts/", "work/")
FORBIDDEN_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".webm", ".zip", ".tar", ".gz", ".tgz", ".har", ".jsonl")


def problems(root: Path, max_kb: int) -> list[str]:
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    out = []
    for name in filter(None, tracked.decode().split("\0")):
        path = root / name
        if name.startswith(FORBIDDEN_PREFIXES):
            out.append(f"{name}: raw runs and artifacts stay out of git")
        elif name.lower().endswith(FORBIDDEN_SUFFIXES):
            out.append(f"{name}: media, archives and transcripts stay out of git")
        elif path.is_file() and path.stat().st_size > max_kb * 1024:
            out.append(f"{name}: {path.stat().st_size // 1024} KiB is over the {max_kb} KiB limit")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-kb", type=int, default=512)
    args = ap.parse_args()
    found = problems(Path.cwd(), args.max_kb)
    print("\n".join(found) or "size check passed")
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
