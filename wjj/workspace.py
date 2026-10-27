"""A throwaway copy of one seed. The fixer only ever touches this copy; hidden tests stay outside it."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GIT = ["git", "-c", "user.name=seed", "-c", "user.email=seed@local"]


@dataclass
class TestResult:
    passed: bool
    output: str


# A skipped or xfailed test proves nothing, so the hidden suite must run every test for real.
NOT_REAL_PASS = re.compile(r"\b\d+ (skipped|xfailed|xpassed|deselected)\b|no tests ran")


def _pytest(cwd: Path, target: str, timeout: int = 60, strict: bool = False) -> TestResult:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", target],
                           cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
        output = (r.stdout + r.stderr)[-4000:]
        passed = r.returncode == 0 and not (strict and NOT_REAL_PASS.search(output))
        return TestResult(passed, output)
    except subprocess.TimeoutExpired:
        return TestResult(False, f"pytest timed out after {timeout}s")


class Workspace:
    def __init__(self, seed: str):
        self.seed = seed
        self.seed_dir = ROOT / "seeds" / seed
        self.hidden_dir = ROOT / "hidden" / seed
        if not self.seed_dir.is_dir():
            raise SystemExit(f"No such seed: {seed}")
        self._tmp = tempfile.TemporaryDirectory(prefix=f"wjj-{seed}-")
        self.path = Path(self._tmp.name) / seed
        shutil.copytree(self.seed_dir, self.path)
        subprocess.run([*GIT, "init", "-q"], cwd=self.path, check=True)
        subprocess.run([*GIT, "add", "-A"], cwd=self.path, check=True)
        subprocess.run([*GIT, "commit", "-qm", "seed"], cwd=self.path, check=True)

    def close(self) -> None:
        self._tmp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def resolve(self, rel: str) -> Path:
        """Map an agent-supplied path into the workspace, refusing anything outside it."""
        p = (self.path / rel).resolve()
        if p != self.path and self.path not in p.parents:
            raise ValueError(f"path escapes the workspace: {rel}")
        return p

    def task(self) -> str:
        return (self.path / "task.md").read_text()

    def list_files(self) -> list[str]:
        return sorted(str(p.relative_to(self.path)) for p in self.path.rglob("*")
                      if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts)

    def run_tests(self) -> TestResult:
        return _pytest(self.path, "tests")

    def run_hidden(self) -> TestResult:
        return _pytest(self.path, str(self.hidden_dir / "test_hidden.py"), strict=True)

    def diff(self) -> str:
        subprocess.run([*GIT, "add", "-A"], cwd=self.path, check=True)
        return subprocess.run([*GIT, "diff", "--cached", "HEAD"], cwd=self.path,
                              capture_output=True, text=True, check=True).stdout

    def touched_files(self) -> list[str]:
        subprocess.run([*GIT, "add", "-A"], cwd=self.path, check=True)
        out = subprocess.run([*GIT, "diff", "--cached", "--name-only", "HEAD"], cwd=self.path,
                             capture_output=True, text=True, check=True).stdout
        return [line for line in out.splitlines() if line]
