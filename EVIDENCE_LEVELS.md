# Evidence levels

The labels below describe what can actually be checked. They are categories, not a claim that every item in one category is more important than every item in another.

## `DIRECT_PROOF`

A written mathematical argument derives the statement from explicitly listed hypotheses. Finite lemmas used by the argument must be separately identified.

## `FINITE_EXHAUSTION`

A terminating program enumerates a finite, explicitly justified search space without an UNKNOWN branch. The proof obligation includes both the mathematical argument that the enumeration is complete and review of the program. An independent implementation or audit is recorded when available.

## `CHECKED_CERTIFICATE`

A concrete object is supplied with a checker that verifies the claimed local or topological properties. Examples here include crossing tables, rotations, and planarization certificates. A certificate check proves only the properties implemented by its checker.

## `UNCERTIFIED_SOLVER_AUDIT`

A named solver returned SAT or UNSAT for an exactly fingerprinted encoded formula, and the run metadata was preserved. For the UNSAT runs in this repository, no independently checkable proof trace was emitted.

Hashes protect identity and detect accidental changes; they do not prove solver correctness, encoding fidelity, or the mathematical theorem represented by the encoding. Accordingly, this level must be described as “solver-reported UNSAT,” not “a proof of UNSAT.”

## `EXPLORATORY_ONLY`

A bounded search, heuristic observation, solver result without adequate preservation, or UNKNOWN outcome. It can guide research but is not listed as a proved claim. UNKNOWN has no truth-value implication.

## `OPEN`

The statement remains unproved and undisproved within this project. Related partial results must not be combined across incompatible hypotheses.

## Two independent axes

For computational claims, always ask two separate questions:

1. **Was the encoded formula result independently certified?** For both K17 runs here, the answer is no.
2. **Does the encoded formula faithfully represent the intended mathematical objects?** Parts of the bridge have been audited, including K5 completeness, but the full publication-grade bridge has not yet been closed.

A solver certificate would address the first question only. It would not automatically settle the second.

