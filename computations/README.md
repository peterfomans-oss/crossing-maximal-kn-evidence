# Computational records

This directory publishes two different kinds of K17 computation.  They must
not be described as independently certified proofs.

1. `safe-no-prefix/` contains fresh K14--K17 runs of the audited formula
   profile that omits the disputed partner/prefix clauses.
2. `historical-prefix-k17/` preserves the earlier, stronger K17 formula as a
   research record.  Its fourteen extra clauses have not been proved lossless.

In both cases CryptoMiniSat reported `UNSAT` for the exact hashed formula, but
the native-XOR Python binding emitted no independently checkable UNSAT proof
certificate.  The accurate public claim is therefore:

> The method produced a reproducible solver-reported UNSAT result for the
> stated exact formula hash; an independent UNSAT certificate is not yet
> available.

It is not accurate to replace that sentence with “K17 has been proved.”  The
historical run has the additional unresolved prefix-lemma gap.  The safe run
removes that gap from the formula profile, but still requires independent
certificate checking and a complete review of the encoding-to-mathematics
bridge before it can be promoted to a formal computational proof.

## Summary

| Profile | n | Variables | CNF | XOR | Solver report | Recorded solve time | Independent UNSAT certificate |
|---|---:|---:|---:|---:|---|---:|---|
| safe/no-prefix | 14 | 3003 | 134335 | 30030 | UNSAT | 739.945 s | no |
| safe/no-prefix | 15 | 4095 | 200892 | 50050 | UNSAT | 3227.799 s | no |
| safe/no-prefix | 16 | 5460 | 291476 | 80080 | UNSAT | 22076.825 s | no |
| safe/no-prefix | 17 | 7140 | 412058 | 123760 | UNSAT | 246174.171 s | no |
| historical prefix | 17 | 7140 | 412072 | 123760 | UNSAT | 15089.853 s | no |

Each result directory contains:

- `RESULT.md`: interpretation, limitations, exact formula hash, and hashes of
  the original private records;
- `manifest.json`: formula/configuration metadata;
- `final-result.json`: the solver's final report; and
- `cube-000.json`: the single depth-zero cube record.

The JSON copies in this public candidate redact hostnames, process IDs, and
session IDs.  Consequently their file hashes differ from the original records.
The original pre-redaction hashes are preserved in each `RESULT.md`.  Formula
hashes, counts, timestamps, solver versions, and solve durations are unchanged.

