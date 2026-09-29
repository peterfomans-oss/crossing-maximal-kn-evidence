# Certified `K9` example

Evidence level: explicit simple drawing, independently checkable without a SAT
solver or external catalogue.

`check_counterexample.py` reconstructs the complete crossing relation from the
saved 126-entry table, checks every `K5`, all disjoint-triangle parity tests, and
all candidate deletion witnesses.  The two embedding checkers independently
verify the sphere planarization.

From the repository root:

```text
python -B certificates/k9/check_counterexample.py
python -B certificates/k9/planar/check_certificate.py
python -B certificates/k9/check_embedding_independent.py
```

The globally uncrossed edges are `01, 34, 56, 78`, and vertex `2` is incident
with none of them.  This is not an all-edges-crossed example and is not a `K17`
counterexample.
