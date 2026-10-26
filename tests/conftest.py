import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analyzer"))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def copy_run(name: str, dest: Path) -> Path:
    shutil.copytree(FIXTURES / "runs" / name, dest / name)
    return dest / name
