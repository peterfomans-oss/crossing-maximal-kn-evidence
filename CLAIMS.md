# Claim register

This file is the authoritative short-form claim register. Evidence labels are defined in [EVIDENCE_LEVELS.md](EVIDENCE_LEVELS.md). A successful checker establishes only the statement assigned to that checker.

| ID | Claim | Evidence | Status and scope |
|---|---|---|---|
| `K5-COMPLETE` | Every realizable crossing-maximal simple K5 crossing table belongs, up to relabeling, to one of two types; their labeled closure contains 72 tables. | `FINITE_EXHAUSTION` plus an independent audit | Established for the stated drawing model. The enumeration covers 1,296 normalized rotations and 650 along-edge orders. See `proofs/k5-completeness/`. |
| `WITNESS-ORDER` | For a deletion witness, the relation used in the prefix analysis is a transitive tournament and hence a unique total order. | `DIRECT_PROOF` using `K5-COMPLETE` and a finite local table | Established in the stated crossing-maximal simple-drawing setting. |
| `PREFIX-REDUCTION-CONDITIONAL` | If a good nonempty deletion witness exists, vertices can be relabeled so the historical order, prefix clauses, and fixed first partner follow in the specified background. | `DIRECT_PROOF` | Established conditionally. It does not prove that every relevant K17 candidate has such a witness. See `proofs/logical-reduction/`. |
| `ROOTED-SEVEN` | A crossed root edge has no good nonempty deletion center iff some induced restriction on at most seven vertices containing the root edge already has that property. | `DIRECT_PROOF` | Established under the local ordering facts above. See `proofs/rooted-obstruction/`. |
| `ROOTED-SEVEN-SHARP` | The bound seven in `ROOTED-SEVEN` cannot in general be lowered to six. | `CHECKED_CERTIFICATE` | Established by an induced restriction of the certified realizable K8 drawing. See `certificates/k8/rooted-sharpness/`. |
| `K8-GENERALIZED-COUNTEREXAMPLE` | There is a realizable crossing-maximal simple K8 drawing in which every deleted vertex has a nonempty witness but no witness is good. | `CHECKED_CERTIFICATE` with independent construction and planarization checks | Established. The drawing has uncrossed edges, so it is not a counterexample to the original all-edges-crossed K17 target. |
| `K9-GENERALIZED-COUNTEREXAMPLE` | There is a realizable crossing-maximal simple K9 drawing with deletion coverage and no good witness; one vertex is incident with no uncrossed edge. | `CHECKED_CERTIFICATE` | Established. The drawing has uncrossed edges and does not refute the original all-edges-crossed K17 target. |
| `SAFE-K14` | CryptoMiniSat reported UNSAT for the exact safe no-prefix K14 encoded formula with SHA-256 `32affac3...e4abad`. | `UNCERTIFIED_SOLVER_AUDIT` | Reproducible solver result for the hashed formula only; no independently checkable UNSAT certificate. |
| `SAFE-K15` | CryptoMiniSat reported UNSAT for the exact safe no-prefix K15 encoded formula with SHA-256 `4c69c551...935233`. | `UNCERTIFIED_SOLVER_AUDIT` | Same limitation. |
| `SAFE-K16` | CryptoMiniSat reported UNSAT for the exact safe no-prefix K16 encoded formula with SHA-256 `7fbb430a...16c5d3`. | `UNCERTIFIED_SOLVER_AUDIT` | Same limitation. |
| `SAFE-K17` | CryptoMiniSat reported UNSAT for the exact safe no-prefix K17 encoded formula with SHA-256 `9c9abf70...4c5490`. The formula omits all 14 disputed prefix-related clauses. | `UNCERTIFIED_SOLVER_AUDIT` | Strong computational evidence for this encoding, but not yet an independently certified proof or a completed K17 theorem. |
| `HISTORICAL-PREFIX-K17` | CryptoMiniSat reported UNSAT for the exact historical prefix-constrained K17 encoded formula with SHA-256 `04a2f88f...93105`. | `UNCERTIFIED_SOLVER_AUDIT` | Does not imply unrestricted K17 because the general existence of a good prefix-normalizable witness is unproved; no UNSAT certificate was emitted. |
| `PREFIX-LEMMA` | Every relevant all-edges-crossed crossing-maximal K17 candidate has a good nonempty deletion witness. | `OPEN` | Neither proved nor disproved. The certified K8/K9 objects do not satisfy the all-edges-crossed premise. |
| `K17-THEOREM` | The target class of K17 drawings is empty. | `OPEN` | Not claimed by this repository. The safe computation is evidence, with remaining obligations listed in `OPEN_OBLIGATIONS.md`. |

## Wording rule

For `SAFE-K17` and `HISTORICAL-PREFIX-K17`, use “solver-reported UNSAT” or “the solver returned UNSAT for the exact hashed encoded formula.” Do not shorten this to “proved UNSAT” or “proved K17” unless an independently checkable proof certificate and the mathematical encoding audit have both been completed.

