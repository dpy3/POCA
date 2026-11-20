# POCA v0.2.1 release status

Updated: 2026-11-20
State: v0.2.1 patch release tree prepared for clean-clone verification. This patch changes release documentation and metadata only; the verifier, tests, data records, and scientific claims are unchanged from v0.2.0. The selected reuse licence for author-generated records is CC BY 4.0; no separate data DOI is included in this package.

This tree is based on the public v0.2.0 release. The v0.2.0 and v0.1.1 tags remain unchanged as earlier releases and baselines.

## Completed and checked

- The verifier specification, input schemas, and six hash vectors are present and parse; all six SHA-256 values were recalculated from normalized bytes.
- src/verify_evidence.py implements declared-artifact hash checks, result-row identifier association, campaign-wide run-ID coverage checks, wrapper-call reconciliation, and conversion to the existing POCA audit-record format. Its report preserves local and effective statuses.
- Missing parseable evidence is distinguished from observed mismatch: a missing results-file path and a results row with no run_id produce INDETERMINATE; a changed artifact hash and undeclared or duplicate campaign run IDs produce FAIL. A synchronized artifact-plus-manifest rewrite still passes declared consistency, as intended; the report states that this is not authentication or proof of execution provenance.
- The full local unit suite passed: 36 tests, including all 13 inherited evaluator tests.
- The pinned SciPy 1.16.2 smoke test passed on Python 3.13.7: logging-off/on outputs and RNG states matched; wrapper count and nfev were both 48. Local statuses were identity/budget/runnability PASS, path INDETERMINATE, and effective L3 BLOCKED_BY_UPSTREAM. This is one software-integration case, not a performance result or full candidate trace.
- The release manifest covers 63 files using text-lf-v1 or binary-exact-v1 hashes; byte-size values refer to the canonical bytes actually hashed. The manifest excludes itself.
- The current release checkout passed manifest validation (63 files, exact file set, hashes, and canonical sizes), all 36 unit tests, the branching example, and the pinned SciPy smoke test (48 wrapper calls matched nfev; path status remained INDETERMINATE). A fresh clone of the final public tag is the next verification gate.
- The companion manuscript draft targets v0.2.1; its exact commit citation and final PDF are maintained in the submission package. No optimizer, result, or verification rule was changed in this patch.
- Highlights.txt has five manuscript-aligned statements, each within 85 characters.
- DATA_AVAILABILITY_REVIEW.md inventories the bundled data. The user selected CC BY 4.0 for author-generated data; no separate data repository or DOI has been created, and the final coauthor rights review remains pending.

## Release artifacts

- Verifier specification: spec/verify_v1.md and the three verifier JSON contracts in spec/.
- Implementation and tests: src/verify_evidence.py, src/test_verify_evidence.py.
- SciPy smoke adapter and protocol: src/run_scipy_smoke.py and validation/SCIPY_SMOKE_PROTOCOL_20261119.md.
- Canonical smoke output: validation/scipy_smoke_20261119/.
- Release manifest: RELEASE_MANIFEST.txt; earlier manifests are preserved for provenance.
- Clean-extraction verification is retained outside the package in the parent QA folder.

## Remaining gates

1. The authors must review the final code, manuscript claims, AI-assistance disclosure, author order, affiliations, funding, conflict statement, and CRediT roles.
2. Complete DATA_AVAILABILITY_REVIEW.md: confirm all coauthors approve CC BY 4.0 for the included author-generated records, check whether additional raw logs/configurations exist, and verify whether the selected journal requires a separate DOI-backed data record. Third-party source archives remain excluded.
3. Before submission, authors must confirm C1-C3, author metadata, data rights, and declarations against the public v0.2.1 tag; do not imply that a separate data DOI exists.
4. After publication, keep the GitHub release tag, manifest, README, software citation, and manuscript C1-C3 synchronized. Data records should be linked using the persistent identifier selected by the authors.

## Claim boundary

The verifier checks consistency among declared files, row identifiers, and calls visible at the objective wrapper. It does not authenticate the manifest, show that a declared source generated a result, prevent unlogged calls, verify optimizer correctness, or reconstruct candidate acceptance. For the tested SciPy interface, candidate path remains INDETERMINATE.
