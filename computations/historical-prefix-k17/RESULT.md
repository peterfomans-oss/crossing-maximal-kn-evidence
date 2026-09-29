# K17 historical prefix-constrained result

- Formula profile: historical induction witness with partner/prefix clauses
- Formula SHA-256: `04a2f88f98ef3d5303574928e273073eab16dad51ebe88175a8760e38b093105`
- Size: 7140 variables, 412072 CNF clauses, 123760 native-XOR clauses
- Solver: CryptoMiniSat 5.14.7 (`pycryptosat` native-XOR binding)
- Solver report: `UNSAT`
- Recorded solve time: 15089.85293750005 seconds (about 4 h 11 min 30 s)
- Independent UNSAT certificate: **not available**
- Evidence level: `UNCERTIFIED_SOLVER_AUDIT / HASHED_ENCODED_FORMULA_ONLY`

## Essential limitation

The formula contains one fixed-partner unit clause and thirteen prefix clauses.
Those fourteen clauses have not been proved lossless for every relevant K17
candidate.  Consequently this result does not prove the general K17 case even
if one accepts the solver report.  A conditional reduction is available if a
good prefix witness is assumed, but existence of such a witness remains open.

## Original record hashes (before publication redaction)

| Original relative path | SHA-256 |
|---|---|
| `outputs/k17-unsplit-like-before/final-result.json` | `fc8fbfa4f130c30e4e69d5945c3ce9992d1389e123b7da5393cc082db07528ce` |
| `outputs/k17-unsplit-like-before/manifest.json` | `f96a6ec9bb8db2925e2447174637342b8980a97dfe349338fbc3f0348d35bb1d` |
| `outputs/k17-unsplit-like-before/cubes/cube-000.json` | `c2edd309e08a3597c091d8cc0d23be2469669404044673ce88115580cdc50aa6` |

The public `manifest.json` and `cube-000.json` redact machine/session metadata.
The `cube_files_aggregate_sha256` retained in `final-result.json` refers to the
original unredacted cube collection.

