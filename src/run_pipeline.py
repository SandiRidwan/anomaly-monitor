"""run_pipeline.py — ingest → analyze → tests."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent


def run(script: Path) -> bool:
    print(f"\n{'='*64}\n▶ {script.name}\n{'='*64}")
    t0 = time.time()
    r = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
    print(f"{'✓' if r.returncode == 0 else '✗'} {script.name} ({time.time()-t0:.1f}s)")
    return r.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ingest", action="store_true")
    args = ap.parse_args()
    steps = []
    if not args.no_ingest:
        steps.append(SRC / "ingest.py")
    steps += [SRC / "analyze.py", SRC / "decide_actions.py",
              ROOT / "tests" / "test_anomaly.py"]
    for s in steps:
        if not run(s):
            print(f"\n✗ PIPELINE GAGAL di {s.name}")
            return 1
    print("\n" + "=" * 64 + "\n✓ PIPELINE SELESAI\n" + "=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
