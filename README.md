# Crossing-Maximal Complete-Graph Evidence

[简体中文](README.zh-CN.md)

This repository collects mathematical arguments, finite enumerations, checked drawing certificates, and reproducible SAT/XOR run records concerning crossing-maximal simple drawings of complete graphs.

## Important status statement

This repository does **not** claim a proved new K17 theorem.

There are two K17 computations:

1. The historical **prefix-constrained** formula was reported UNSAT by CryptoMiniSat. It contains 14 additional clauses: one fixed first-partner clause and 13 prefix clauses. The needed general existence lemma for that normalization has not been proved. This run therefore cannot establish the unrestricted K17 claim.
2. The later **safe no-prefix** formula removes all 14 disputed clauses and was also reported UNSAT by CryptoMiniSat.

Both are **uncertified solver-reported UNSAT results** for exact hashed encoded formulas. Neither run emitted an independently checkable UNSAT proof certificate. The safe run is materially stronger evidence because it does not depend on the disputed prefix normalization, but a complete encoding-to-drawing audit and an independently checked UNSAT certificate are still required before treating it as a mathematical proof.

It is accurate to say:

> Using the crossing-only SAT/XOR encoding, CryptoMiniSat reported UNSAT for the exact hashed K17 formula, including a safe version with the disputed 14 prefix-related clauses removed. The current records are reproducible solver audits, not independently certified UNSAT proofs.

It is not accurate to say “K17 has been proved” on the basis of these records alone.

## Safe no-prefix run summary

| Instance | Variables | CNF clauses | XOR clauses | Formula SHA-256 | Recorded solver result |
|---|---:|---:|---:|---|---|
| K14 | 3,003 | 134,335 | 30,030 | `32affac3edb48da546fc57a518fb8bca3d77b1f18adb69d10e584e7da9e4abad` | solver-reported UNSAT, uncertified |
| K15 | 4,095 | 200,892 | 50,050 | `4c69c551566203434aca6297de0f0180682cfa8451d0f5ecda6f088c7f935233` | solver-reported UNSAT, uncertified |
| K16 | 5,460 | 291,476 | 80,080 | `7fbb430aaba9761372840f08de315c3d8a7fcaf1781c69c8a64f079df116c5d3` | solver-reported UNSAT, uncertified |
| K17 | 7,140 | 412,058 | 123,760 | `9c9abf7012053fa6f064f2d43233e11ec3f274fcb1003b900d6f4910664c5490` | solver-reported UNSAT, uncertified |

The archived records label their own evidence level `UNCERTIFIED_SOLVER_AUDIT` and their claim scope `HASHED_ENCODED_FORMULA_ONLY`.

## Independently checkable results included here

- A complete finite K5 classification: all 1,296 normalized rotation systems and all 650 relevant along-edge crossing orders are exhausted, producing exactly two unlabeled crossing-table types and 72 labeled tables.
- A proof that the tournament relation associated with a deletion witness is a total order, based on the completed K5 classification and a finite local table.
- A conditional logical reduction: if a good nonempty deletion witness exists, the historical prefix normalization can be introduced without loss in the stated setting.
- A rooted obstruction theorem: a crossed root edge with no good nonempty deletion center has such an obstruction on at most seven vertices; the bound seven is sharp.
- Checked realizable K8 and K9 drawings that refute stronger statements obtained by dropping the “every edge is crossed” premise. These are **not** counterexamples to the original all-edges-crossed K17 target.

See [CLAIMS.md](CLAIMS.md) for exact scopes and [EVIDENCE_LEVELS.md](EVIDENCE_LEVELS.md) for the labels used in this repository.

## Repository map

- [`proofs/`](proofs/) — K5 completeness, the conditional logical reduction, and the rooted obstruction theorem.
- [`certificates/`](certificates/) — K8/K9 crossing data, rotations, planarization certificates, constructions, and independent checkers.
- [`computations/`](computations/) — sanitized safe K14–K17 records and the historical prefix-constrained K17 record.
- [`solver/`](solver/) — source needed to inspect or reproduce the SAT/XOR encoding; solver binaries are not vendored.
- [`audits/`](audits/) — independent finite checks and the mathematical check runner.
- [`research/`](research/) — status of the unproved prefix lemma and documented failed routes.
- [`OPEN_OBLIGATIONS.md`](OPEN_OBLIGATIONS.md) — what remains before stronger claims are justified.
- [`DATA_AND_PROVENANCE.md`](DATA_AND_PROVENANCE.md) — source, transformation, and integrity notes.

## Quick verification

Python 3.10 or newer is recommended. The release preflight and the mathematical certificate checks use only the Python standard library.

```text
python scripts/release_preflight.py
python scripts/run_core_checks.py
```

Do not add `-O`: several finite checkers rely on assertions. These commands do not run the full K17 solver search. See [REPRODUCE.md](REPRODUCE.md) for details.

## Licensing and citation

Original repository content is released under the [MIT License](LICENSE) by
`peterfomans-oss`. Citation metadata is in [`CITATION.cff`](CITATION.cff).
See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for referenced tools and
historical provenance. No third-party source code or solver binary is vendored.
