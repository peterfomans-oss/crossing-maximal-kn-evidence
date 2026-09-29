# K17 safe/no-prefix result

- Profile: `safe-induction-no-partner-no-prefix-v1`
- Formula SHA-256: `9c9abf7012053fa6f064f2d43233e11ec3f274fcb1003b900d6f4910664c5490`
- Size: 7140 variables, 412058 CNF clauses, 123760 native-XOR clauses
- Solver: CryptoMiniSat 5.14.7 (`pycryptosat` native-XOR binding)
- Solver report: `UNSAT`
- Recorded solve time: 246174.1711571 seconds (about 68 h 22 min 54 s)
- Independent UNSAT certificate: **not available**
- Evidence level: `UNCERTIFIED_SOLVER_AUDIT / HASHED_ENCODED_FORMULA_ONLY`

This fresh run excluded the fourteen disputed historical partner/prefix
clauses.  It is valid to report that this method produced an UNSAT result for
the exact hashed safe formula.  It is not valid to call the record an
independently certified proof: the solver emitted no proof certificate, and
the encoding-to-mathematics bridge still requires complete independent review.

## Original record hashes (before publication redaction)

| Original relative path | SHA-256 |
|---|---|
| `outputs/k17-safe-no-prefix-v1/final-result.json` | `e8953a6953311bd2de2a2f11221117a6306a19b5dd5920a9b76a17098f69bde1` |
| `outputs/k17-safe-no-prefix-v1/manifest.json` | `c1ec694722a581fb1decf0ab26770197f9ac38264849b51dba0f77e5d805aa42` |
| `outputs/k17-safe-no-prefix-v1/cubes/cube-000.json` | `cdb7bd66755339bf92bc22c83015b895533ca018aff72aa82332f50240ec5ba2` |

The public `manifest.json` and `cube-000.json` redact machine/session metadata.
The `cube_files_aggregate_sha256` retained in `final-result.json` refers to the
original unredacted cube collection.

