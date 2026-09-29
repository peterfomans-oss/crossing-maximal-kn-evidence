#!/usr/bin/env python3
"""One-command entry point for public release and mathematical checks."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    display = " ".join(command)
    print(f"\n==> {display}", flush=True)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="run release, privacy, claim-metadata, Python syntax, and JSON checks only",
    )
    args = parser.parse_args()

    run([sys.executable, str(ROOT / "scripts" / "release_preflight.py")])
    if args.quick:
        print("core checks: PASS (quick mode; mathematical certificate runners not executed)")
        return 0

    runner = ROOT / "audits" / "run_math_checks.py"
    if not runner.is_file():
        print(f"missing mathematical runner: {runner.relative_to(ROOT)}", file=sys.stderr)
        return 1
    run([sys.executable, "-B", str(runner)])
    print("core checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

