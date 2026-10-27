"""Check every seed: visible tests fail as shipped, the reference fix passes visible and hidden tests.

Usage: python scripts/verify_seeds.py
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pytest(cwd: Path, target: Path) -> bool:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(target)],
                       cwd=cwd, capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return r.returncode == 0


def main() -> int:
    bad = 0
    for seed in sorted(p for p in (ROOT / "seeds").iterdir() if p.is_dir()):
        hidden = ROOT / "hidden" / seed.name
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / seed.name
            shutil.copytree(seed, work)
            shipped_visible = pytest(work, work / "tests")
            shipped_hidden = pytest(work, hidden / "test_hidden.py")
            ref = hidden / "reference"
            if ref.exists():
                shutil.copytree(ref, work, dirs_exist_ok=True)
                ref_visible = pytest(work, work / "tests")
                ref_hidden = pytest(work, hidden / "test_hidden.py")
            else:
                ref_visible = ref_hidden = None
        ok = not shipped_visible and not shipped_hidden and ref_visible is not False and ref_hidden is not False
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {seed.name:12} shipped visible={'pass' if shipped_visible else 'fail'} "
              f"hidden={'pass' if shipped_hidden else 'fail'} | reference visible={ref_visible} hidden={ref_hidden}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
