"""Cross-platform task runner. `make <task>` calls this; on Windows run `python scripts/tasks.py <task>`."""

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIN = os.name == "nt"
PNPM = "pnpm.cmd" if WIN else "pnpm"
NPX = "npx.cmd" if WIN else "npx"


def run(cmd, cwd=ROOT, env=None, check=True):
    print(f"$ {' '.join(cmd)}  (in {Path(cwd).relative_to(ROOT) or '.'})")
    return subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, check=check)


def lint():
    run(["uv", "run", "ruff", "check", "."], cwd=ROOT / "api")
    run([PNPM, "lint"], cwd=ROOT / "web")
    run([PNPM, "typecheck"], cwd=ROOT / "web")


def test():
    run(["uv", "run", "pytest", "-q"], cwd=ROOT / "api")
    if (ROOT / "web" / "vitest.config.ts").exists():
        run([PNPM, "test"], cwd=ROOT / "web")


def seed():
    run(["uv", "run", "python", "-m", "app.seed"], cwd=ROOT / "api",
        env={"FIRESTORE_EMULATOR_HOST": "127.0.0.1:8080"})


def wait_for(url, seconds=90):
    end = time.time() + seconds
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def dev():
    emu_env = {"FIRESTORE_EMULATOR_HOST": "127.0.0.1:8080"}
    procs = [
        subprocess.Popen([NPX, "--yes", "firebase-tools", "emulators:start", "--only", "firestore",
                          "--project", "symbiosis-protect-demo"], cwd=ROOT),
        subprocess.Popen(["uv", "run", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
                         cwd=ROOT / "api", env={**os.environ, **emu_env}),
        subprocess.Popen([PNPM, "dev"], cwd=ROOT / "web"),
    ]
    ok = wait_for("http://127.0.0.1:8000/healthz") and wait_for("http://localhost:3100/api/healthz")
    print("\nHEALTH:", "green — web http://localhost:3100 · api http://127.0.0.1:8000/docs" if ok else "NOT READY")
    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            p.terminate()


def deploy():
    sys.exit("Deploy is gated to Phase 9 and requires the owner to say 'deploy'.")


TASKS = {"dev": dev, "seed": seed, "test": test, "lint": lint, "deploy": deploy}

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    if name not in TASKS:
        sys.exit(f"usage: tasks.py [{'|'.join(TASKS)}]")
    TASKS[name]()
