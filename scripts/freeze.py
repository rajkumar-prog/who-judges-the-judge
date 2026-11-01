"""Freeze the answer key before the final run, and prove afterwards that it didn't change.

  python scripts/freeze.py           writes docs/frozen-manifest.json (commit it before the run)
  python scripts/freeze.py --check   exits 1 if any frozen file differs from the manifest

Covers everything that decides a result: seeds, hidden tests, hand-written patches, case patches,
and the judge and agent prompts.
"""
import hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FROZEN = ("seeds", "hidden", "patches", "cases", "wjj/judge.py", "wjj/fixer.py")
MANIFEST = ROOT / "docs" / "frozen-manifest.json"


def hashes() -> dict:
    out = {}
    for top in FROZEN:
        p = ROOT / top
        files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.is_file() and "__pycache__" not in f.parts)
        for f in files:
            out[str(f.relative_to(ROOT))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def main() -> int:
    now = hashes()
    if "--check" in sys.argv:
        frozen = json.loads(MANIFEST.read_text())["files"]
        changed = sorted(k for k in frozen.keys() | now.keys() if frozen.get(k) != now.get(k))
        for k in changed:
            print(f"changed: {k}")
        print("frozen files unchanged" if not changed else f"{len(changed)} frozen files changed")
        return 1 if changed else 0
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    MANIFEST.write_text(json.dumps({"frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    "git_commit": commit, "files": now}, indent=1) + "\n")
    print(f"froze {len(now)} files into {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
