# Contributing

Contributions that improve verification, documentation, portability, or
mathematical clarity are welcome under the policy below.

## Claim discipline

- Preserve the scopes and evidence labels in `CLAIMS.md`.
- Describe both K17 outcomes as **solver-reported UNSAT, without an independently checkable certificate**.
- Do not use the historical prefix-constrained run as evidence for unrestricted K17 unless the missing existence lemma is proved.
- Do not describe K8 or K9 as counterexamples to the all-edges-crossed K17 target.
- UNKNOWN solver outcomes have no positive or negative mathematical conclusion.

## Submitting changes

1. Keep generated data and its checker together.
2. Document the source, command, version, and SHA-256 of new generated artifacts.
3. Avoid user names, host names, local absolute paths, process identifiers, session identifiers, secrets, binaries, and virtual environments.
4. Run:

   ```text
   python scripts/release_preflight.py
   python scripts/run_core_checks.py
   ```

5. Explain exactly which claim is changed and why its evidence level is appropriate.

Do not run formatting tools over preserved JSON result records unless the transformation and original fingerprint are documented.

## Licensing note

Original repository content is licensed under MIT. By submitting a contribution,
contributors agree that their contribution may be distributed under that license.
A contribution must not introduce third-party content with unknown or
incompatible terms.
