# Certified `K8` example

Evidence level: explicit simple drawing, independently checkable without a SAT
solver or external catalogue.

Key files:

- `counterexample-k8.json`: complete 70-entry crossing table;
- `check_counterexample.py`: exhausts all nonempty deletion witnesses;
- `planar/certificate.json` and `planar/check_certificate.py`: sphere-map
  certificate and checker;
- `check_embedding_independent.py`: a second reconstruction that ignores the
  producer's port and face data;
- `twins/`: an independent geometric near-vertex-duplication construction;
- `rooted-sharpness/`: certificate that the seven-vertex rooted bound cannot in
  general be reduced to six.

From the repository root:

```text
python -B certificates/k8/check_counterexample.py
python -B certificates/k8/planar/check_certificate.py
python -B certificates/k8/check_embedding_independent.py
python -B certificates/k8/twins/construct_twins.py
python -B certificates/k8/rooted-sharpness/check_sharpness.py
```

The four globally uncrossed edges are `02, 17, 34, 56`; therefore this example
does not satisfy the all-edges-crossed premise of the open `K17` lemma.
