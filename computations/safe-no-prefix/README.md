# Safe no-prefix runs (K14--K17)

These runs use the profile
`safe-induction-no-partner-no-prefix-v1`.  It retains only the two induction
families for which a relabelling argument was audited:

- after deleting vertex `0`, edge `12` is uncrossed; and
- vertices `3,...,n-1` are placed in the transitive tournament order.

It does **not** fix `X(12,03)` and does **not** add the star-prefix clauses.
For K17 this removes all fourteen disputed clauses from the historical
formula.  The safe formula was rebuilt and solved from scratch; the historical
UNSAT report was not reused.

## Recorded formulas

| n | Variables | CNF clauses | XOR clauses | Formula SHA-256 | Solver report |
|---:|---:|---:|---:|---|---|
| 14 | 3003 | 134335 | 30030 | `32affac3edb48da546fc57a518fb8bca3d77b1f18adb69d10e584e7da9e4abad` | UNSAT |
| 15 | 4095 | 200892 | 50050 | `4c69c551566203434aca6297de0f0180682cfa8451d0f5ecda6f088c7f935233` | UNSAT |
| 16 | 5460 | 291476 | 80080 | `7fbb430aaba9761372840f08de315c3d8a7fcaf1781c69c8a64f079df116c5d3` | UNSAT |
| 17 | 7140 | 412058 | 123760 | `9c9abf7012053fa6f064f2d43233e11ec3f274fcb1003b900d6f4910664c5490` | UNSAT |

## Evidence level

All four records are `UNCERTIFIED_SOLVER_AUDIT` with claim scope
`HASHED_ENCODED_FORMULA_ONLY`.  CryptoMiniSat 5.14.7, via its native-XOR
Python binding, reported UNSAT.  That binding did not emit an independently
checkable proof certificate.  These records may be cited as computational
results of the method, with this limitation stated explicitly; they must not
be placed in a directory or table labelled “proved theorems.”

The source used to build and run the formulas is under `../../solver/`.

