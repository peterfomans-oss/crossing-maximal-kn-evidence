# Third-party notices

This release candidate does not vendor solver executables, Python runtimes, compiled extensions, CaDiCaL sources, or complete third-party environments.

## Runtime tools referenced by records

- CryptoMiniSat / `pycryptosat` 5.14.7 was used for the preserved native-XOR solver runs.
- `python-sat` appeared in parts of the historical research environment.
- Python is used for the public checkers and enumeration scripts.

These tools are not relicensed by this repository. Users who install them must follow their upstream licenses.

## K5 catalogue data

`solver/cm5_unlabeled.json0` was regenerated using research code associated with:

```text
https://github.com/manfredscheucher/rotsys-sat
```

The archive acquired on 2026-09-01 did not contain an explicit license file. Its source program is therefore not copied here. The regenerated data file is included for formula reproduction and provenance, but a future repository-level license must not be assumed to grant rights over that third-party-derived data unless its status has been confirmed.

Before public release, the repository owner should do one of the following:

1. confirm permission and document the applicable terms in `LICENSES/`; or
2. remove the catalogue file and adjust the reproduction instructions to regenerate or obtain it separately.

The independent K5 finite proof under `proofs/k5-completeness/` does not rely on treating the archived catalogue as an independent completeness proof.

## GitHub Actions

The workflow references `actions/checkout` and `actions/setup-python`; those actions remain under their respective upstream terms and are not vendored here.

