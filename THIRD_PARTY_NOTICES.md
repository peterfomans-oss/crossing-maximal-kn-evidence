# Third-party notices

This repository does not vendor solver executables, Python runtimes, compiled
extensions, CaDiCaL sources, complete third-party environments, or third-party
source code.

## Runtime tools referenced by records

- CryptoMiniSat / `pycryptosat` 5.14.7 was used for the preserved native-XOR solver runs.
- `python-sat` appeared in parts of the historical research environment.
- Python is used for the public checkers and enumeration scripts.

These tools are not relicensed by this repository. Users who install them must follow their upstream licenses.

## K5 catalogue history and independent reconstruction

During the historical research, an identical two-record K5 rotation input was
regenerated while evaluating code associated with:

```text
https://github.com/manfredscheucher/rotsys-sat
```

The archive acquired on 2026-09-01 did not contain an explicit license file,
so none of its source code is copied here. The committed two-record
`solver/cm5_unlabeled.json0` matches, byte for byte, output derived solely from
this repository's independent exhaustive K5 classification.
`audits/k5-completeness/rebuild_solver_catalogue.py` performs the comparison
without reading third-party code or catalogue data and is run by the core
verification suite. The historical project is identified only for transparent
research provenance, not as a bundled dependency.

## GitHub Actions

The workflow references `actions/checkout` and `actions/setup-python`; those actions remain under their respective upstream terms and are not vendored here.
