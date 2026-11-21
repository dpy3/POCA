# POCA evidence verification v1.0

**Status:** release specification for the v0.2.2 patch release, 2026-11-20. This specification describes the implemented v1 verifier boundary; it is not a performance claim.

## Purpose and boundary

The verifier checks whether a declared set of run artifacts, a results row, and wrapper-level objective-call records are internally consistent with a supplied manifest. It emits local statuses and may serialize them into the existing POCA v3 audit-record format so that the existing DAG evaluator can propagate them.

The verifier does not prove that the manifest is authentic, that a listed source file produced a result, that an optimizer is correct, or that no unrecorded objective calls occurred outside the instrumented wrapper. If a file and its manifest entry are changed together, the verifier is expected to report consistency with the replacement manifest. This is a documented trust boundary, not an authentication check.

Version 1.0 supports UTF-8 JSON manifest metadata, CSV result tables, and JSONL wrapper-call records. It does not parse MAT files, verify semantic result values, reconstruct a full candidate lineage, enforce a run-time budget, or provide a complete SciPy selection trace.

## Inputs and identifiers

The manifest declares a campaign, one or more runs, artifact files, one or more results CSV files, and the wrapper-call log. Each run names its results file, source artifact, source_id, runner_id, and result_row_id. A run_id must be unique across the complete campaign, including all result files. A result_row_id must be unique within its declared results CSV. The selected row must contain the same campaign_id and run_id as the manifest and must agree with the declared source_id, runner_id, and source artifact digest.

The JSON Schema describes a complete, conforming manifest. The verifier also handles parseable manifests with omitted required fields so it can report those missing evidence items as INDETERMINATE instead of treating them as observed mismatches; malformed JSON, unsupported types, and unsafe paths remain input errors.

The manifest run list defines the campaign scope. Result rows and call records carrying this campaign_id but using a run_id absent from the manifest produce a campaign-level FAIL. A campaign row with a missing run_id produces INDETERMINATE coverage. Duplicate campaign run IDs across result files are reported as a campaign-level FAIL as well as against any affected declared run. These checks identify declaration/record mismatches; they do not prove that the supplied campaign is complete relative to an external experiment log.

All artifact paths are relative to the package root, use forward slashes, and must not resolve outside that root. Version 1.0 lists files individually; directory paths, symlinks, and implicit recursive inclusion are rejected. The manifest itself is excluded from its own artifact list to avoid self-reference.

Each artifact entry contains a relative path, role, hash_mode, and expected SHA-256. The source, runner, configuration, results CSV, and call log are separate declared artifacts. The report records each check and the exact artifact or row examined.

## Hash contract

The v0.1.1 release manifest declares line-ending normalization for text and exact-byte hashing for binary files. Version 1.0 makes that convention explicit as follows. Before describing the implementation as byte-for-byte backward-compatible with the old tag, the implementation must compare its results with the old tag's published manifest hashes. If any old digest differs under these precise rules, document the distinction and use a new hash-mode name rather than silently changing old hashes.

- hash_mode text-lf-v1 accepts UTF-8 text, converts CRLF and bare CR line endings to LF, preserves all other bytes, and then computes SHA-256. It performs no Unicode normalization and does not remove a byte-order mark.
- hash_mode binary-exact-v1 computes SHA-256 over the file's exact bytes.

The two modes are explicit per artifact; the verifier does not guess from file extensions. A missing required manifest field—including a missing results-file path—or unavailable artifact yields INDETERMINATE when the JSON remains parseable. A present artifact whose computed digest differs from its declared digest yields FAIL. Invalid JSON, unsupported schema versions, invalid paths, and malformed digest syntax are input errors and exit with the established schema-error code rather than receiving a scientific status. The report separates per-run checks from campaign-level coverage checks.

Golden vectors must show that LF and CRLF text inputs produce the same text-lf-v1 digest, while a one-byte change in a binary artifact changes its binary-exact-v1 digest. The verifier must also test a synchronized rewrite: after both an artifact and its manifest digest are changed, the artifact-consistency check is expected to PASS. That case demonstrates that the manifest is a declared reference, not a trust anchor.

## Result-row association

The results CSV column map declares campaign_id, run_id, result_row_id, source_id, source_sha256, runner_id, task_id, dimension, seed, logging_mode, run_status, target_fe, reported_fe, and, when available, solver_nfev. The verifier requires one unambiguous row matching the manifest identifiers. A completed row supports runnability=PASS; a declared failed run supports runnability=FAIL; an absent or unknown run status is INDETERMINATE.

- No matching row or a missing identifier produces INDETERMINATE.
- Duplicate campaign-scoped run_id values, duplicate result_row_id values in the same file, or a row whose identifiers contradict the manifest produce FAIL.
- Version 1.0 does not compute a semantic row-content digest and does not call row association result-row content binding.

For the existing audit-record adapter, identity means only declared artifact-to-row consistency under this manifest contract. It does not mean proof of execution provenance or causation. Manuscript wording for L1 must use that bounded meaning wherever v1 results are discussed. A source digest is checked against the declared source artifact, but a matching digest does not prove that the source was the code executed in the run.

## Wrapper-call accounting

Each JSONL call record contains campaign_id, run_id, and a positive integer call_index. For the SciPy adapter in v1, caller is the generic value objective. The public objective wrapper does not infer init-versus-trial phases. Candidate-vector digests are excluded from v1 until their byte representation is separately frozen.

For a run, observed_wrapper_calls is the number of valid, unique call records. The call indices must start at 1 and be contiguous. The verifier compares that count with reported_fe and, if supplied by the engine, solver_nfev. A duplicated call index is FAIL; a gap or incomplete call log is INDETERMINATE because omitted events cannot be distinguished from unrecorded calls.

The budget policy is explicit per run:

- upper_bound passes only when observed_wrapper_calls equals reported_fe, equals solver_nfev when that comparator is required, and does not exceed target_fe.
- exact additionally requires observed_wrapper_calls to equal target_fe.

An early-terminated run may pass under upper_bound when the counters agree and the declared policy permits early termination. The verifier does not describe reaching the target as mandatory unless the run declares exact. A counter mismatch or a count above the declared cap is FAIL.

These checks establish agreement among the records that the wrapper and engine expose. They do not establish that an external caller bypassed neither the wrapper nor the logging mechanism.

## Local-status mapping

Each check returns one of the following statuses with a reason code and evidence references:

- PASS: the requested consistency condition is supported by complete, matching inputs.
- FAIL: the available inputs contain a concrete mismatch or violated declared budget rule.
- INDETERMINATE: the check was requested, but required evidence is missing or incomplete.
- NOT_TESTED: the adapter or protocol did not request or implement that check.

For a SciPy run using only public hooks, the path status is INDETERMINATE when candidate-path verification was requested but per-candidate selection is not exposed; it must never be inferred from population differences. Replay and observer non-interference remain NOT_TESTED unless separately evaluated using a paired protocol. Control comparability and incremental value are NOT_TESTED by this verifier.

## SciPy adapter scope

The first adapter is passive and version-pinned. It uses a supplied NumPy Generator, workers=1, vectorized=False, polish=False, and no custom strategy. The wrapper records each objective call and the adapter records the engine's exposed nfev, nit, final result fields, and before/after RNG states where the pinned release exposes them.

The adapter does not claim access to internal boundary-repair details, dithering draws, parent indices, or per-candidate accept/reject events. In particular, a custom strategy may expose returned trial vectors but does not provide a public per-candidate selection hook. Full candidate-lineage verification is outside v1.0.

The documented evaluation-count formula is used only as a conditional sanity bound for the exact pinned setup. Actual wrapper counts and the engine-reported nfev are authoritative. Tolerance-based early stopping may produce fewer calls than the maximum. Tests must record the exact parameter values and compare the observed count rather than infer it from a generic formula.

## Frozen acceptance tests

The v1 prototype must cover, at minimum:

1. Clean artifact, row, and call-log agreement: expected PASS for supported checks.
2. Changed source, runner, configuration, result file, or call log without manifest update: expected FAIL for the affected hash check.
3. Synchronized artifact-plus-manifest rewrite: expected PASS for declared consistency, demonstrating the trust limitation.
4. LF/CRLF-equivalent text and byte-exact binary golden vectors.
5. Missing manifest field, missing artifact, missing row, or incomplete call log: expected INDETERMINATE where the format remains parseable.
6. Duplicate run_id across files within a campaign, an undeclared run_id in a result row or call record, duplicate result_row_id in a results file, or contradictory row identifiers: expected FAIL; missing result-row run_id: expected INDETERMINATE.
7. Duplicate call_index or FE mismatch: expected FAIL; a call-index gap: expected INDETERMINATE.
8. upper_bound and exact budget cases, including a valid early stop under upper_bound and a target overrun.
9. SciPy logging-on/off comparison for the same pinned version, seed, and inputs, with no random draws by the observer; compare supported result fields and observed counts.
10. All 13 existing unit tests remain green.

Faults count as held-out only if an independent person freezes their specifications and expected outcomes before implementation freeze and the implementation team does not inspect them during debugging. Otherwise they are regression tests.

## Release and manuscript rules

The v0.2.1 package remains unchanged as the preceding release, and the v0.1.1 package remains the earlier baseline. The v0.2.2 tag identifies the source tree, clean-clone tests, manifests, and documentation checked for this patch release. This release status does not imply optimizer performance or authenticated provenance.

The paper may describe only implemented checks and observed results. Use phrases such as manifest consistency, row-identifier association, and wrapper-call reconciliation. Do not use result-row binding, authenticated provenance, anti-tamper verification, complete candidate tracing, or causal attribution for v1.0.

For SoftwareX data availability, follow the journal's Option C: provide a repository link for data that can lawfully and ethically be shared, or a specific explanation for each dataset that cannot be shared. Do not publish third-party archives or restricted raw logs without rights review. A single DOI-backed archive for the exact code release is optional project practice, not a claim that two DOIs are required. Recheck the live journal instructions at submission.
