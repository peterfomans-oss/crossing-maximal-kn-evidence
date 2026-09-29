# Explicit drawing certificates

The `k8/` and `k9/` subdirectories contain complete crossing data, rotation
systems, sphere-planarization certificates, and independent Python checkers.
All checkers in this directory use only the Python standard library.

These are positive certificates for actual simple crossing-maximal drawings:

| Example | Certified conclusion | Important limitation |
|---|---|---|
| `K8` | every deleted vertex has a nonempty witness, and every such witness is bad | four edges are globally uncrossed |
| `K9` | the same, and vertex 2 is incident with no globally uncrossed edge | four edges are globally uncrossed |

Consequently these examples refute stronger statements that omit the
all-edges-crossed hypothesis.  They are **not** counterexamples to the original
all-edges-crossed `K17` target.

The checker evidence is constructive: each original edge is verified as a
simple path through the claimed crossings, crossing branches alternate, all
darts form a connected orientable map, and Euler characteristic is 2.
