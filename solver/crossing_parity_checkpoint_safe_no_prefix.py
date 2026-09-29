"""Checkpoint runner for the audited no-partner/no-prefix formula profile."""

from __future__ import annotations

import crossing_parity_checkpoint as runner
from crossing_parity_sat_safe_no_prefix import PROFILE, build_instance


EXPECTED_FORMULAS = {
    14: (3003, 134335, 30030, "32affac3edb48da546fc57a518fb8bca3d77b1f18adb69d10e584e7da9e4abad"),
    15: (4095, 200892, 50050, "4c69c551566203434aca6297de0f0180682cfa8451d0f5ecda6f088c7f935233"),
    16: (5460, 291476, 80080, "7fbb430aaba9761372840f08de315c3d8a7fcaf1781c69c8a64f079df116c5d3"),
    17: (7140, 412058, 123760, "9c9abf7012053fa6f064f2d43233e11ec3f274fcb1003b900d6f4910664c5490"),
}


def checked_build_instance(
    n,
    induction_witness=False,
    all_deletion_witnesses=False,
    native_xor=False,
    k5_encoding="nogoods",
    parity_encoding="basis",
    return_metadata=False,
):
    result = build_instance(
        n,
        induction_witness,
        all_deletion_witnesses,
        native_xor,
        k5_encoding,
        parity_encoding,
        return_metadata,
    )
    if (
        n in EXPECTED_FORMULAS
        and induction_witness
        and not all_deletion_witnesses
        and native_xor
        and k5_encoding == "nogoods"
        and parity_encoding == "direct"
    ):
        cnf, xor_clauses, stats = result[:3]
        actual = (
            stats["variables"],
            len(cnf.clauses),
            len(xor_clauses),
            runner.formula_sha256(cnf, xor_clauses),
        )
        if actual != EXPECTED_FORMULAS[n]:
            raise RuntimeError(
                f"safe formula invariant failed for K{n}: "
                f"expected {EXPECTED_FORMULAS[n]}, got {actual}"
            )
    return result


_runner_config_original = runner.runner_config


def safe_runner_config(args):
    config = _runner_config_original(args)
    config["induction_profile"] = PROFILE
    return config


# The base runner resolves these globals at run time.  Patching them here lets
# us reuse its lock, heartbeat, SAT-model validation, and atomic records while
# keeping both the formula builder and every recorded source hash explicit.
runner.build_instance = checked_build_instance
runner.ENCODER_FILES = (
    "crossing_parity_sat.py",
    "crossing_parity_sat_safe_no_prefix.py",
    "crossing_model_explore.py",
    "sparse_parity_basis.py",
    "cm5_unlabeled.json0",
    "crossing_parity_checkpoint.py",
    "crossing_parity_checkpoint_safe_no_prefix.py",
)
runner.runner_config = safe_runner_config


if __name__ == "__main__":
    raise SystemExit(runner.main())
