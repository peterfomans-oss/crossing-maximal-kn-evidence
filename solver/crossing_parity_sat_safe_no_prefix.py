"""Audited induction encoding without the unproved partner/prefix clauses.

This module leaves the production encoder unchanged.  It builds the common
crossing-only formula with the historical induction block disabled, then adds
only the two symmetry-breaking families justified in
K17_EVIDENCE_2026-09-04/audit/SAFE_INDUCTION_PATCH_AUDIT.md:

* edge 12 is uncrossed after deleting vertex 0; and
* vertices 3,...,n-1 are put in the transitive tournament order.

It deliberately does not add X(12,03), or any prefix clauses on X(12,0k).
"""

from __future__ import annotations

import itertools
import time

from crossing_model_explore import normalized_pair
from crossing_parity_sat import build_instance as build_base_instance


PROFILE = "safe-induction-no-partner-no-prefix-v1"


def append_safe_induction_constraints(n, cnf, crossing_vars):
    """Append exactly the two audited, lossless induction families."""
    if n < 4:
        raise ValueError("induction witness needs vertices 0,1,2,3")

    witness_edge = (1, 2)
    deletion_units = 0
    for other in itertools.combinations(range(3, n), 2):
        cnf.append([-crossing_vars[normalized_pair(witness_edge, other)]])
        deletion_units += 1

    tournament_units = 0
    for i, j in itertools.combinations(range(3, n), 2):
        cnf.append([crossing_vars[normalized_pair((1, i), (2, j))]])
        tournament_units += 1

    expected_each = (n - 3) * (n - 4) // 2
    if deletion_units != expected_each or tournament_units != expected_each:
        raise RuntimeError("safe induction clause-count invariant failed")

    return {
        "profile": PROFILE,
        "deletion_witness_units": deletion_units,
        "tournament_order_units": tournament_units,
        "fixed_crossing_partner_units": 0,
        "star_prefix_clauses": 0,
    }


def build_instance(
    n: int,
    induction_witness: bool = False,
    all_deletion_witnesses: bool = False,
    native_xor: bool = False,
    k5_encoding: str = "nogoods",
    parity_encoding: str = "basis",
    return_metadata: bool = False,
):
    """Build the base formula and optionally add the audited induction block."""
    started = time.perf_counter()
    cnf, xor_clauses, stats, metadata = build_base_instance(
        n,
        induction_witness=False,
        all_deletion_witnesses=all_deletion_witnesses,
        native_xor=native_xor,
        k5_encoding=k5_encoding,
        parity_encoding=parity_encoding,
        return_metadata=True,
    )

    constraint_record = {
        "profile": "no-induction-witness",
        "deletion_witness_units": 0,
        "tournament_order_units": 0,
        "fixed_crossing_partner_units": 0,
        "star_prefix_clauses": 0,
    }
    if induction_witness:
        constraint_record = append_safe_induction_constraints(
            n, cnf, metadata["crossing_vars"]
        )

    stats = dict(stats)
    stats["clauses"] = len(cnf.clauses)
    stats["build_seconds"] = time.perf_counter() - started
    stats["induction_profile"] = constraint_record["profile"]

    metadata = dict(metadata)
    metadata["induction_constraints"] = constraint_record

    if return_metadata:
        return cnf, xor_clauses, stats, metadata
    return cnf, xor_clauses, stats

