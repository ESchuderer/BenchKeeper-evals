import subprocess

import check_size


def repo_with(tmp_path, files):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, size in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * size)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_clean_tree_passes(tmp_path):
    assert check_size.problems(repo_with(tmp_path, {"results/a.json": 1000, "tests/fixtures/runs/a__1/x.js": 10}), 512) == []


def test_raw_runs_media_and_large_files_fail(tmp_path):
    root = repo_with(tmp_path, {"runs/a__1/x.js": 10, "docs/shot.png": 10, "results/big.json": 600 * 1024, "dump.jsonl": 5})
    found = "\n".join(check_size.problems(root, 512))
    for name in ("runs/a__1/x.js", "docs/shot.png", "results/big.json", "dump.jsonl"):
        assert name in found


def test_untracked_files_are_ignored(tmp_path):
    root = repo_with(tmp_path, {"a.txt": 1})
    (root / "runs").mkdir()
    (root / "runs" / "x.js").write_text("x")
    assert check_size.problems(root, 512) == []
