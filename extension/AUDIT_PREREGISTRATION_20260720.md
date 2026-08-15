# External audit extension preregistration

Release: AUDIT_FRAMEWORK_EXTENSION_20260720

## Scope

This extension adds two externally sourced DE cases, a machine-readable audit contract, and a multi-task/multi-seed clean-control matrix. It is an audit study, not a performance comparison.

## Frozen external cases

1. `LSHADE-SPACMA 1.0`, CEC2017 top-methods archive, SHA-256 `3bbde55b92b2e4be9bcbf957b94f5e0e9d9aa09ebad70291909c718a661d4c02`.
2. `NL-SHADE-RSP`, CEC2021 top-methods archive, SHA-256 `aaa61f80a1358142b0c790afe539d52a1df54073c074c3ede18a01c44f4afa58`.

## Frozen clean-control matrix

Tasks: sphere, Rosenbrock, and Rastrigin. Seeds: 20260731--20260735. Logging modes: off, accepted-only, and full-candidate. Population size is 10, dimension is 5, and the exact target is 120 objective calls. The same seed is replayed across all logging modes.

## Frozen gates

Each record must report source identity, true and reported FE, evaluated-path status, observer non-interference, replay equality, task, seed, logging mode, runtime, and trace bytes. `PASS` requires all applicable checks to pass. A missing dependency or source-level execution failure is `FAIL` for runnability and blocks all higher-level performance interpretation. `INDETERMINATE` is not converted to PASS.

## Stopping rule

The extension stops at the audit layer. It does not launch a 30-run benchmark, tune parameters, or convert external smoke evidence into optimizer superiority claims.
