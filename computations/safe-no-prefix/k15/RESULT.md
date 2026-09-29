# K15 safe/no-prefix result

- Profile: `safe-induction-no-partner-no-prefix-v1`
- Formula SHA-256: `4c69c551566203434aca6297de0f0180682cfa8451d0f5ecda6f088c7f935233`
- Size: 4095 variables, 200892 CNF clauses, 50050 native-XOR clauses
- Solver: CryptoMiniSat 5.14.7 (`pycryptosat` native-XOR binding)
- Solver report: `UNSAT`
- Recorded solve time: 3227.7990497000283 seconds
- Independent UNSAT certificate: **not available**
- Evidence level: `UNCERTIFIED_SOLVER_AUDIT / HASHED_ENCODED_FORMULA_ONLY`

This establishes what the solver reported for this exact encoded formula.  It
is not, by itself, an independently checkable proof certificate.

## Original record hashes (before publication redaction)

| Original relative path | SHA-256 |
|---|---|
| `outputs/k15-safe-no-prefix-v1/final-result.json` | `0ae769287e005db58ee9c35b8cb0ca8ab8bdd5536eb21d8c4e0da11886031f97` |
| `outputs/k15-safe-no-prefix-v1/manifest.json` | `79f8a83fb07773e6b4b730275d246ea109b6b135376f8035228ed80352a0ffd3` |
| `outputs/k15-safe-no-prefix-v1/cubes/cube-000.json` | `19a140f3b5f0422a8df5f9cb8a8d782e2ec334b283dbe0a7ed27a1b03e5d99b1` |

The public `manifest.json` and `cube-000.json` redact machine/session metadata.
The `cube_files_aggregate_sha256` retained in `final-result.json` refers to the
original unredacted cube collection.

