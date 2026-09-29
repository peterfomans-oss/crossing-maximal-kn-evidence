# Mathematical proofs

This directory contains arguments that do not rely on accepting an UNSAT solver
answer as a proof.

| Item | Evidence level | Scope |
|---|---|---|
| `k5-completeness/` | exhaustive finite proof, standard-library implementation, independently re-derived in `../audits/` | all crossing-maximal simple drawings of `K5` |
| `order-transitivity/` | direct nine-row check after the complete `K5` classification | the witness tournament is a unique total order; exact bad-star criterion |
| `logical-reduction/` | direct conditional logic proof | what a *good* deletion witness would justify in the historical prefix encoding |
| `rooted-obstruction/` | direct proof plus an independently checked sharpness example | every fixed bad crossed edge has a witness on at most seven vertices |

None of these files proves the open global `K17` existence-of-a-good-witness
lemma.  In particular, the logical reduction is conditional: it proves that a
good witness permits the historical symmetry breaking, not that such a witness
always exists.

Run the bundled mathematical checks from the repository root with:

```text
python -B audits/run_math_checks.py
```
