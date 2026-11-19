# SciPy differential-evolution smoke protocol

**Frozen:** 2026-11-19, before running the integration case.  
**Purpose:** verify adapter accounting and logging non-interference for one pinned public implementation; this is not an optimizer-performance experiment.

## Environment

- SciPy 1.16.2, as installed in the current Python 3.13.7 environment.
- NumPy Generator created from the fixed seed below.
- One worker, non-vectorized objective, deferred updating, no polishing, and no custom strategy.

## Fixed configuration

- Objective: three-dimensional Sphere, sum of squared coordinates.
- Bounds: [-5, 5] for each of three variables.
- Seed: 20261119.
- Population multiplier: 4; maximum generations: 3.
- Tolerance and absolute tolerance: 0; initialization: SciPy default Latin hypercube.
- Budget policy: upper_bound. The expected no-early-stop maximum is checked only as a sanity bound; observed wrapper count and result.nfev are the comparison values.

## Procedure and pass criteria

1. Run the same fixed configuration once with the direct objective and once with the passive logging wrapper, each from a fresh Generator with the same seed.
2. Compare nfev, nit, best position and value, final population and energies, and the serialized post-run RNG state. All compared outputs must match exactly.
3. For the logged run, count objective-wrapper calls and compare with result.nfev, reported_fe, and the declared upper bound. The call log must have unique contiguous indices beginning at one.
4. Run the verifier on the logged run. Expected local statuses: identity=PASS, budget=PASS, runnability=PASS, path=INDETERMINATE, replay=NOT_TESTED, observer=NOT_TESTED, control=NOT_TESTED, incremental_value=NOT_TESTED.
5. The dependency evaluator may produce BLOCKED_BY_UPSTREAM for effective L3 because the existing graph requires observer evidence. The report must preserve the local path=INDETERMINATE observation.

The test supports only this pinned SciPy integration. It does not verify per-candidate accept/reject events, parent indices, internal repair details, general replay validity, or optimizer quality.
