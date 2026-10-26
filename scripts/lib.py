"""Shared helpers for data build scripts (idempotent, cached raw downloads)."""

import json
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SEED = ROOT / "data" / "seed"
DERIVED = ROOT / "data" / "derived"
UA = "SymbiosisProtectDemo/0.1 (panjacharan8@gmail.com)"


def load_locations() -> list[dict]:
    return json.loads((SEED / "locations.json").read_text(encoding="utf-8"))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def get_json(url: str, params: dict | None = None, retries: int = 5, headers: dict | None = None):
    for i in range(retries):
        r = httpx.get(url, params=params, headers={"User-Agent": UA, **(headers or {})}, timeout=60,
                      follow_redirects=True)
        if r.status_code == 200:
            return r.json()
        time.sleep(2 * (i + 1) if r.status_code != 429 else 30)
    r.raise_for_status()


def download(url: str, dest: Path) -> Path:
    """Download with resume via curl (some hosts, e.g. fema.gov, block python HTTP clients)."""
    import shutil
    import subprocess

    dest.parent.mkdir(parents=True, exist_ok=True)
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl is required for data downloads")
    head = subprocess.run([curl, "-sIL", url], capture_output=True, text=True).stdout.lower()
    sizes = [int(line.split(":")[1]) for line in head.splitlines() if line.startswith("content-length:")]
    total = sizes[-1] if sizes else 0
    for _ in range(10):
        if total and dest.exists() and dest.stat().st_size == total:
            return dest
        subprocess.run([curl, "-sSL", "-C", "-", "--retry", "3", "-o", str(dest), url], check=False)
        if dest.exists() and dest.stat().st_size < 4096 and b"Access Denied" in dest.read_bytes():
            dest.unlink()
        if not total and dest.exists():
            return dest
    raise RuntimeError(f"could not download {url}")
