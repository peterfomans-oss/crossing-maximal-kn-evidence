# Reproduction guide

## Requirements

- Python 3.10 or newer.
- No network access for the release preflight, finite enumerations, or certificate checks.
- No third-party Python package for the core mathematical checks.
- Do not run Python with `-O`; several checkers use assertions.

The historical solver environment used Python 3.13.9 and `pycryptosat` 5.14.7. That environment is needed only to rerun the SAT/XOR computations, not to check the included finite proofs and drawing certificates.

## 1. Check the public release tree

From the repository root:

```text
python scripts/release_preflight.py
```

This checks required files, parses JSON and Python sources, rejects common private-path and secret patterns, rejects bundled executables and caches, and verifies that the K17 result records retain the `UNCERTIFIED_SOLVER_AUDIT` status.

Before an actual public release, run:

```text
python scripts/release_preflight.py --strict-release
```

Strict mode requires the completed root `LICENSE` and `CITATION.cff`, in
addition to all ordinary release checks.

## 2. Run all core mathematical checks

```text
python scripts/run_core_checks.py
```

The wrapper first performs the release preflight and static file checks, then calls `audits/run_math_checks.py`. It does not launch a K14–K17 SAT search.

For a fast CI-style syntax, JSON, privacy, and claim-metadata check only:

```text
python scripts/run_core_checks.py --quick
```

The full mathematical runner covers the K5 finite classification and independent audit, K8/K9 claim and planarization checks, the K8 construction, and the seven-point sharpness check. Individual commands and expected outputs are documented under `audits/` and `certificates/`.

## 3. Inspect the solver records without rerunning the solver

The sanitized run records are under:

- `computations/safe-no-prefix/k14/` through `k17/`
- `computations/historical-prefix-k17/`

Each directory includes a human-readable `RESULT.md` and preserved JSON records. The safe K17 formula hash is:

```text
9c9abf7012053fa6f064f2d43233e11ec3f274fcb1003b900d6f4910664c5490
```

The historical prefix-constrained K17 formula hash is:

```text
04a2f88f98ef3d5303574928e273073eab16dad51ebe88175a8760e38b093105
```

Both records state that the result is a solver audit for the exact hashed formula and that no independently checkable UNSAT proof is present.

## 4. Optional full solver reproduction

See `computations/README.md`, `computations/safe-no-prefix/README.md`, and `solver/README.md`. A compatible `pycryptosat` installation is required; no solver binary or private virtual environment is included.

The safe K17 run recorded about 68.4 hours of solve time on its original machine. Runtime is machine-dependent. Re-running the solver can confirm reproducibility, but another matching solver response is still not an independently checkable UNSAT proof certificate.

## Interpretation

- Passing certificate checks validates the stated concrete objects.
- Passing finite enumeration checks validates the stated finite classifications, together with their completeness arguments.
- Matching the K17 solver result validates reproducibility of a solver computation.
- None of these steps, separately or in combination, should be relabeled beyond the scopes in [CLAIMS.md](CLAIMS.md).
