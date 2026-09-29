# K14 safe/no-prefix result

- Profile: `safe-induction-no-partner-no-prefix-v1`
- Formula SHA-256: `32affac3edb48da546fc57a518fb8bca3d77b1f18adb69d10e584e7da9e4abad`
- Size: 3003 variables, 134335 CNF clauses, 30030 native-XOR clauses
- Solver: CryptoMiniSat 5.14.7 (`pycryptosat` native-XOR binding)
- Solver report: `UNSAT`
- Recorded solve time: 739.9447249000077 seconds
- Independent UNSAT certificate: **not available**
- Evidence level: `UNCERTIFIED_SOLVER_AUDIT / HASHED_ENCODED_FORMULA_ONLY`

This establishes what the solver reported for this exact encoded formula.  It
is not, by itself, an independently checkable proof certificate.

## Original record hashes (before publication redaction)

| Original relative path | SHA-256 |
|---|---|
| `outputs/k14-safe-no-prefix-v1/final-result.json` | `2eca8ced1b7ed77f89dc73a4696cdd70bad4b48618ba44fb0ca0fd93f78bf71c` |
| `outputs/k14-safe-no-prefix-v1/manifest.json` | `7c990b9e259d522d341f45913943f1785c8b3da465256f0e6fd8af9a8bdff77b` |
| `outputs/k14-safe-no-prefix-v1/cubes/cube-000.json` | `0fb9ff8e05b100a1c96f834fea6ad5ac5c5bda192be7d1fb563fd7d800899c9b` |

The public `manifest.json` and `cube-000.json` redact machine/session metadata.
The `cube_files_aggregate_sha256` retained in `final-result.json` refers to the
original unredacted cube collection.

