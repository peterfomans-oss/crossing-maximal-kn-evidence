# K16 safe/no-prefix result

- Profile: `safe-induction-no-partner-no-prefix-v1`
- Formula SHA-256: `7fbb430aaba9761372840f08de315c3d8a7fcaf1781c69c8a64f079df116c5d3`
- Size: 5460 variables, 291476 CNF clauses, 80080 native-XOR clauses
- Solver: CryptoMiniSat 5.14.7 (`pycryptosat` native-XOR binding)
- Solver report: `UNSAT`
- Recorded solve time: 22076.82493210002 seconds
- Independent UNSAT certificate: **not available**
- Evidence level: `UNCERTIFIED_SOLVER_AUDIT / HASHED_ENCODED_FORMULA_ONLY`

This establishes what the solver reported for this exact encoded formula.  It
is not, by itself, an independently checkable proof certificate.

## Original record hashes (before publication redaction)

| Original relative path | SHA-256 |
|---|---|
| `outputs/k16-safe-no-prefix-v1/final-result.json` | `9cf6a3ed216812bf11f7ca2c76c791381e859934d854e5cf89faa079d5e7fe40` |
| `outputs/k16-safe-no-prefix-v1/manifest.json` | `08446ff9818a343292704ac8a6c7054505925e5f83c7eebad3f9dfaac05075f9` |
| `outputs/k16-safe-no-prefix-v1/cubes/cube-000.json` | `7c2ee35c822082e51023c28bec7aa56f6ae0844312bb7bc51486b7e4fbf11c9a` |

The public `manifest.json` and `cube-000.json` redact machine/session metadata.
The `cube_files_aggregate_sha256` retained in `final-result.json` refers to the
original unredacted cube collection.

