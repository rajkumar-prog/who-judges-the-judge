"""Download the three open-source libraries the real-repo seeds are built on.

They aren't kept in this repo, since they weren't written for it. This fetches the exact old
versions from PyPI, checks each download's sha256, and copies the package into its seed:

  seeds/ttlcache/cachetools   cachetools 7.2.1  (MIT)
  seeds/proxyauth/requests    requests 2.30.0   (Apache 2.0)
  seeds/xmlattr/jinja2        Jinja2 3.1.2      (BSD-3-Clause)

Each package is copied unchanged, with its license file next to it (cachetools' type stubs are
left out). Run it once after cloning:  python scripts/fetch_libs.py
"""
import hashlib
import io
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LIBS = [
    {"seed": "ttlcache", "dest": "cachetools", "license": "LICENSE",
     "url": "https://files.pythonhosted.org/packages/31/44/71476a5812da1ddf2c9a3efd31ae76d01480a1cf03ed13ac28aa8f2402e4/cachetools-7.2.1.tar.gz",
     "sha256": "b1a7537025c06abf96fcc1443e496af9a3fb95e774e70e1f0af226f73f7f2dcc",
     "top": "cachetools-7.2.1", "package": "src/cachetools", "skip": (".pyi", "py.typed")},
    {"seed": "proxyauth", "dest": "requests", "license": "LICENSE",
     "url": "https://files.pythonhosted.org/packages/e0/69/122171604bcef06825fa1c05bd9e9b1d43bc9feb8c6c0717c42c92cc6f3c/requests-2.30.0.tar.gz",
     "sha256": "239d7d4458afcb28a692cdd298d87542235f4ca8d36d03a15bfc128a6559a2f4",
     "top": "requests-2.30.0", "package": "requests", "skip": ()},
    {"seed": "xmlattr", "dest": "jinja2", "license": "LICENSE.rst",
     "url": "https://files.pythonhosted.org/packages/7a/ff/75c28576a1d900e87eb6335b063fab47a8ef3c8b4d88524c4bf78f670cce/Jinja2-3.1.2.tar.gz",
     "sha256": "31351a702a408a9e7595a8fc6150fc3f43bb6bf7e319770cbc0db9df9437e852",
     "top": "Jinja2-3.1.2", "package": "src/jinja2", "skip": ()},
]


def fetch(lib: dict) -> int:
    data = urllib.request.urlopen(lib["url"], timeout=60).read()
    got = hashlib.sha256(data).hexdigest()
    if got != lib["sha256"]:
        raise SystemExit(f"{lib['url']}: sha256 {got} doesn't match {lib['sha256']}")
    dest = ROOT / "seeds" / lib["seed"] / lib["dest"]
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    pkg = f"{lib['top']}/{lib['package']}/"
    n = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            if m.name == f"{lib['top']}/{lib['license']}":
                target = dest / lib["license"]
            elif m.name.startswith(pkg) and not m.name.endswith(lib["skip"] or ("\0",)):
                target = dest / m.name[len(pkg):]
            else:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tar.extractfile(m).read())
            n += 1
    return n


def main() -> int:
    for lib in LIBS:
        n = fetch(lib)
        print(f"seeds/{lib['seed']}/{lib['dest']}: {n} files from {lib['url'].rsplit('/', 1)[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
