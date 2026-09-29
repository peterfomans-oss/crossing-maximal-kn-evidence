# Historical K17 prefix-constrained run

> **Research archive, not a proof of the general K17 case.**

This directory records the earlier K17 computation with a stronger induction
block.  In addition to the two audited relabelling families, the historical
formula contains fourteen extra CNF clauses:

- one unit clause fixing `X(12,03)`; and
- thirteen clauses forcing the set of `k` for which `X(12,0k)` holds to be a
  prefix of the tournament order.

No proof is currently known that every relevant K17 candidate admits the
required partner/prefix witness.  Equivalently, these fourteen clauses have
not been proved lossless for the general problem.  Their presence is exactly
why the historical formula has 412072 CNF clauses rather than the safe
formula's 412058.

CryptoMiniSat 5.14.7 reported `UNSAT` for formula SHA-256
`04a2f88f98ef3d5303574928e273073eab16dad51ebe88175a8760e38b093105`.
The run also has **no independently checkable UNSAT certificate**.  Therefore
this result says only that the solver reported UNSAT for this exact stronger,
hashed formula.  It does not establish the general K17 statement.

The record is published because it documents the historical route, makes the
gap explicit, and allows comparison with the fresh safe/no-prefix run.

