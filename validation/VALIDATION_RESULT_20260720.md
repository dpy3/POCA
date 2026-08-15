# Five-layer audit controlled validation result

## Fault injection

- Clean minimal DE: all identity, budget, path, observer, and replay checks passed.
- Injected defects detected: 8/8.
- False alarms in clean minimal DE: 0.
- Median paired logging-on/off time ratio over 100 repetitions: 2.150782.
- Serialized clean trace: 19,030 bytes for 100 true evaluations.

| Mode | Expected gate | Identity | Budget | Path | Observer | Detected |
|---|---|:---:|:---:|:---:|:---:|:---:|
| clean | none | pass | pass | pass | pass | clean |
| identity-name mismatch | identity | fail | pass | pass | pass | yes |
| inherited result column | identity | fail | pass | pass | pass | yes |
| candidate overwrite | path | pass | pass | fail | pass | yes |
| uncounted auxiliary call | budget | pass | fail | pass | pass | yes |
| post-reduction counter | budget | pass | fail | pass | pass | yes |
| iteration stop | budget | pass | fail | pass | pass | yes |
| observer RNG interference | observer | pass | pass | pass | fail | yes |
| label/operator mismatch | path | pass | pass | fail | pass | yes |

## Official L-SHADE 1.0.1 clean control

- Source: author-corrected L-SHADE 1.0.1; frozen ZIP SHA-256 `a9d094018b18da674849a97415116146dae6e423c19be8ef0ada9766890f0b9b`.
- Objective: D10 sphere, population 50, exact target 2,000 FEs, seed 20260725.
- Exact equality: final score, final position, 2,000-point convergence curve, every evaluated point, FE count, final RNG state, and initial population.
- Result: clean-control gate passed; no audit defect was reported.
- Serialized full adaptive trace: 1,624,930 bytes.

These experiments validate defect localization and non-interference. They are not optimizer-performance comparisons and do not estimate field-wide defect prevalence.

