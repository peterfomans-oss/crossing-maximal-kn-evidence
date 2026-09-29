# Independent audits

The audit code is deliberately separated from discovery and SAT solving.

- `k5-completeness/audit_k5_completeness.py` independently rebuilds the local
  `K4` lookup, reruns the complete `K5` enumeration, and rechecks every positive
  planarization by a separately written face traversal.
- `run_math_checks.py` copies the public proof and certificate tree to a
  temporary directory and runs all core standard-library checks there.  This
  prevents normal verification from rewriting the released inputs.

Passing these checks establishes the finite enumerations and the supplied
positive certificates.  It does not turn any solver-reported `UNSAT` result into
a certified proof and does not prove the open global prefix-witness lemma.
