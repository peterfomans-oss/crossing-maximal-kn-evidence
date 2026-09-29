# Open obligations

This file separates mathematical gaps from release-administration tasks.

## A. Safe no-prefix route

The safe K17 formula removes the disputed fixed-partner and prefix clauses. It therefore does **not** require the open prefix-witness lemma. To promote its solver report to a publication-grade computer-assisted proof, at least the following remain:

1. Produce an independently checkable UNSAT proof certificate, or replace the run with a certificate-producing workflow whose complete trace can be checked by a small trusted checker.
2. Complete and publish the full audit connecting every formula layer to the intended class of realizable simple drawings. K5 completeness is now independently addressed; remaining catalogue and encoding assumptions, including the K6 layer, must be tracked explicitly.
3. Independently check the generated formula and any transformation used to obtain a proof-producing format, especially native XOR handling.
4. Write a theorem-level exposition that states all imported results and confirms that the finite K17 exclusion implies the intended mathematical statement.

## B. Historical prefix route

The historical K17 formula has two additional obligations:

1. Prove the existence of a good nonempty deletion witness for every relevant all-edges-crossed K17 candidate, or otherwise justify the 14 added clauses without loss.
2. Produce an independently checkable UNSAT certificate for the historical formula.

The current local theory proves a conditional normalization and a sharp seven-point rooted-obstruction theorem, but not the required global existence statement. The remaining gap is global compatibility: different root edges may have different seven-vertex obstruction sets.

## C. Results that are already closed at their stated scope

- The K5 finite classification and its labeled two-type closure.
- The witness-order transitivity consequence in the stated drawing model.
- The conditional prefix reduction.
- The rooted obstruction bound of seven and its sharpness.
- The stated K8 and K9 realizable counterexamples to stronger, premise-weakened claims.

These do not by themselves close either K17 route.

## D. Exploratory questions

- Can the seven-point rooted obstructions be globally incompatible when every edge is crossed?
- Can a proof-producing CNF encoding replace the native-XOR run without making verification impractical?
- Can the remaining catalogue/realizability bridge be reduced to independently checked finite certificates?

Solver UNKNOWN results and uncertified bounded UNSAT probes remain exploratory and are not promoted to claims.

## E. Publication administration

- Choose the repository license and add a root `LICENSE` file.
- Confirm the treatment or removal of third-party-derived catalogue data noted in `THIRD_PARTY_NOTICES.md`.
- Fill author and repository metadata in `AUTHORS.md` and `CITATION.cff.template`, then rename the completed template to `CITATION.cff`.
- Run `python scripts/release_preflight.py --strict-release` before publishing.

