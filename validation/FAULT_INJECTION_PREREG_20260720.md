# Five-layer audit fault-injection preregistration

Freeze date: 2026-07-20

## Purpose

This validation tests whether the generic audit detects known identity, budget, execution-path, and observer defects without flagging a clean implementation. It is not an optimizer performance experiment.

## Frozen clean harness

- Algorithm: minimal DE/rand/1/bin with greedy selection.
- Objective: five-dimensional sphere, bounds `[-5,5]`.
- Population: 10.
- True target: 100 objective evaluations.
- Seed: 20260724 using MATLAB `twister`.
- Logging is append-only and must not consume random numbers in the clean mode.

## Frozen injected defects

| ID | Defect | Expected failed gate |
|---|---|---|
| F1 | Declared/source identity mismatch | algorithm identity |
| F2 | Result marked as inherited rather than generated | algorithm identity |
| F3 | Declared candidate overwritten before evaluation | evaluated path |
| F4 | Auxiliary objective call omitted from reported FE | budget identity |
| F5 | Pre-reduction batch counted using post-reduction population | budget identity |
| F6 | Iteration stop used instead of fixed true FE | budget identity |
| F7 | Logger consumes one random number | observer identity |
| F8 | Declared operator label differs from generated source | evaluated path |

No defect, threshold, expected gate, seed, dimension, population, or target may be changed after execution.

## Passing criteria

- The clean implementation triggers zero failed identity gates.
- Every injected defect fails its preregistered gate.
- Complete detection rate is `8/8` and false-positive rate on the clean control is zero.
- Logging-on/off equality is evaluated on final objective, solution, reported FE, true FE, and final RNG state.
- Category totals equal the independent true FE count for every mode.

## Overhead

Measure clean logging-on and logging-off wall time over 100 paired repetitions after one warm-up. Report the median time ratio and serialized trace size. Timing is implementation-specific and is not used as an optimizer-quality claim.

