# Solver source

This directory contains the exact Python source and K5 catalogue used by the
published solver records.  It intentionally contains no Python executable,
virtual environment, compiled extension, SAT-solver binary, or toolchain.

## Requirements

- Python 3.13 (the recorded runs used 3.13.9)
- `pycryptosat==5.14.7`
- `python-sat==1.9.dev15`

The original machine also recorded `six==1.17.0`; it is included in
`requirements.txt` for environment fidelity.

## Reproduce a safe/no-prefix run

From the repository root, choose a fresh output directory.  For example:

```text
python solver/crossing_parity_checkpoint_safe_no_prefix.py 14 --run-dir reproduce/k14 --induction-witness --k5-encoding nogoods --parity-encoding direct --threads 1 --cube-depth 0
```

Replace `14` and the output directory with `15`, `16`, or `17` as needed.
Before solving, the safe runner checks the variable count, CNF/XOR counts, and
formula hash against the recorded constants.  K17 required about 68 hours on
the original machine, so this is not a quick test.

The historical stronger K17 formula can be rebuilt with the base runner:

```text
python solver/crossing_parity_checkpoint.py 17 --run-dir reproduce/k17-historical --induction-witness --k5-encoding nogoods --parity-encoding direct --threads 1 --cube-depth 0
```

That historical run is for comparison only: fourteen partner/prefix clauses
remain unproved, and no independent UNSAT certificate is produced by this
native-XOR workflow.

The publication JSON files have privacy fields redacted.  Do not run the
runner's `--audit-only` mode directly against those copies: their record-level
hashes intentionally differ from the unredacted originals.  Reproduction
should use a fresh output directory and compare the formula SHA-256 and solver
result reported in the corresponding `RESULT.md`.

## Exact source hashes

These hashes match the source hashes recorded in the original manifests.

| File | SHA-256 |
|---|---|
| `crossing_model_explore.py` | `6c6e52987894f03a7e73cf092eb07643c4e7690ccaa671e01488ecba9bf5d397` |
| `crossing_parity_sat.py` | `d44372d0a7759de641d9e83c70462c0fe781b7b3adcddcf9a841ef6ab58cfb13` |
| `crossing_parity_checkpoint.py` | `c3be5b700a72453556ff6f01e0b98ec3250bb21b7cead3cc14be02369b4407cb` |
| `crossing_parity_sat_safe_no_prefix.py` | `9290e72b5d9fd4422657af9bc5113502d20e498c4db71b03f2b23bcb54bbc29d` |
| `crossing_parity_checkpoint_safe_no_prefix.py` | `9c854ae03b4b294e057ed4fd99530c1aa70ad6f640feda180e439c0067d8c34a` |
| `sparse_parity_basis.py` | `7d1c4f07e88eda309b4a84135aa081fbce89d465953064ffedc295059029b861` |
| `cm5_unlabeled.json0` | `a8f8601be31bc948bfef94e72aa5a45ceee6b722f12ef33c50534eb80fb6619c` |

