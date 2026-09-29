"""Run the public solver-free proof and certificate checks in a temporary copy."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent
CHECKS = [
    ("K5 exhaustive enumeration", "proofs/k5-completeness/enumerate_embeddings.py"),
    ("independent K5 audit", "audits/k5-completeness/audit_k5_completeness.py"),
    ("independent K5 solver catalogue rebuild", "audits/k5-completeness/rebuild_solver_catalogue.py"),
    ("K8 complete witness audit", "certificates/k8/check_counterexample.py"),
    ("K8 planarization certificate", "certificates/k8/planar/check_certificate.py"),
    ("K8 independent embedding reconstruction", "certificates/k8/check_embedding_independent.py"),
    ("K8 near-vertex-duplication construction", "certificates/k8/twins/construct_twins.py"),
    ("K8 planar checker mutation tests", "certificates/k8/planar/test_checker_mutations.py"),
    ("seven-vertex sharpness certificate", "certificates/k8/rooted-sharpness/check_sharpness.py"),
    ("K9 complete witness audit", "certificates/k9/check_counterexample.py"),
    ("K9 planarization certificate", "certificates/k9/planar/check_certificate.py"),
    ("K9 independent embedding reconstruction", "certificates/k9/check_embedding_independent.py"),
]


def hashes(folder: Path) -> dict[str, str]:
    return {
        p.relative_to(folder).as_posix(): sha256(p.read_bytes()).hexdigest()
        for p in folder.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write a new JSON report")
    args = parser.parse_args()
    if sys.flags.optimize:
        raise SystemExit("Do not use -O: several finite checks use assertions.")
    if args.output and args.output.exists():
        raise SystemExit("Refusing to overwrite an existing report.")

    before = hashes(RELEASE)
    rows = []
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="crossing-evidence-") as temp_name:
        temp = Path(temp_name)
        for name in ("proofs", "certificates", "audits", "solver"):
            shutil.copytree(RELEASE / name, temp / name)
        environment = dict(os.environ)
        environment.pop("PYTHONOPTIMIZE", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        for label, relative in CHECKS:
            tick = time.perf_counter()
            try:
                proc = subprocess.run(
                    [sys.executable, "-B", "-S", str(temp / relative)],
                    cwd=temp,
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=180,
                )
                status = "PASS" if proc.returncode == 0 else "FAIL"
                row = {
                    "check": label,
                    "script": relative,
                    "status": status,
                    "returncode": proc.returncode,
                    "seconds": round(time.perf_counter() - tick, 3),
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
            except subprocess.TimeoutExpired:
                row = {
                    "check": label,
                    "script": relative,
                    "status": "TIMEOUT",
                    "seconds": 180,
                }
            rows.append(row)
            print(f"{row['status']}: {label}", flush=True)

    unchanged = before == hashes(RELEASE)
    passed = unchanged and all(row["status"] == "PASS" for row in rows)
    report = {
        "status": "PASS" if passed else "FAIL",
        "python": sys.version,
        "check_count": len(rows),
        "seconds": round(time.perf_counter() - started, 3),
        "site_packages_disabled": True,
        "solver_used": False,
        "temporary_copy": True,
        "released_inputs_unchanged": unchanged,
        "scope": "Finite proofs and positive certificates; not the open K17 lemma or an UNSAT certificate.",
        "checks": rows,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
