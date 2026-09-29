# Data and provenance

## Release construction

This public candidate is a curated derivative of preserved local research records. The source records were not edited in place. Public copies are organized by evidence type, and raw transfer archives, local environments, compiler toolchains, caches, and unrelated experiments are excluded.

Sanitized computation JSON removes machine-specific fields such as host names, user-directory paths, process identifiers, and session identifiers. Human-readable `RESULT.md` files record the original-file fingerprints so that a private custodian can compare the public derivative with the preserved source without publishing private metadata.

## Solver records

The safe no-prefix formula fingerprints are:

| Instance | Formula SHA-256 |
|---|---|
| K14 | `32affac3edb48da546fc57a518fb8bca3d77b1f18adb69d10e584e7da9e4abad` |
| K15 | `4c69c551566203434aca6297de0f0180682cfa8451d0f5ecda6f088c7f935233` |
| K16 | `7fbb430aaba9761372840f08de315c3d8a7fcaf1781c69c8a64f079df116c5d3` |
| K17 | `9c9abf7012053fa6f064f2d43233e11ec3f274fcb1003b900d6f4910664c5490` |

The historical prefix-constrained K17 formula fingerprint is:

```text
04a2f88f98ef3d5303574928e273073eab16dad51ebe88175a8760e38b093105
```

All five preserved final results describe CryptoMiniSat 5.14.7 through its native-XOR Python binding. They explicitly state `independently_checkable_unsat_proof: false`. Solver executables and Python binaries are not included in this repository.

## Safe versus historical K17

The historical K17 formula includes one fixed first-partner clause and thirteen prefix clauses. Their universal no-loss justification is equivalent to an unresolved existence issue in the intended setting.

The safe K17 formula retains the audited deletion-witness and ordering constraints but removes those 14 disputed clauses. The historical formula's UNSAT response is not reused as the safe formula's result: the safe formula was generated and solved separately and has its own hash and run record.

## K5 data

The K5 completeness result in `proofs/k5-completeness/` is produced by a
standard-library exhaustive enumerator that does not depend on an archived
catalogue. It covers all normalized rotation systems and relevant along-edge
crossing orders, then compares the resulting labeled crossing tables with the
two-type closure.

The solver directory contains the two-line `cm5_unlabeled.json0` input used by
the recorded formulas. Its SHA-256 is
`a8f8601be31bc948bfef94e72aa5a45ceee6b722f12ef33c50534eb80fb6619c`.
The committed two-record file matches, byte for byte, the output derived
solely from this repository's standard-library exhaustive K5 classification.
`audits/k5-completeness/rebuild_solver_catalogue.py` performs this comparison
without reading any third-party program or catalogue. This establishes
independent reproducibility of the public bytes and removes any mathematical
or build dependency on an external K5 catalogue.

For historical transparency, an identical two-record input had earlier been
regenerated while evaluating research code associated with Bergold and
Scheucher's `rotsys-sat` framework (archive acquired 2026-09-01, SHA-256
`36a375bbede8c25aee763ed147297e21f47574a6a0efc3432cadcb4078486fc8`).
That upstream source is not copied into this repository and is not needed to
reconstruct the public data.

## K8 and K9 objects

The public certificate directories include the crossing data, rotations, planarization certificates, and all dependent inputs used by their checkers. The K8 and K9 planarizations have checked Euler data `(V,E,F)=(78,168,92)` and `(135,288,155)` respectively. Their checkers verify connectivity, original-edge paths, alternating branches at crossing vertices, and Euler characteristic two.

The K8/K9 objects contain uncrossed edges. This fact is part of their provenance and scope: they are counterexamples to stronger premise-weakened statements, not to the original all-edges-crossed K17 target.

## Integrity policy

- Generated and imported data must have a documented source and fingerprint.
- A changed formula or certificate receives a new fingerprint and is not silently substituted for a recorded run.
- Result labels are stored with the records and checked by `scripts/release_preflight.py`.
- The private transfer ZIP and machine environment remain outside this public tree.
