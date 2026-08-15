# L-SHADE positive external-case preregistration

Protocol: `LSHADE101_POSITIVE_EXTERNAL_20260721`

## Frozen source

- Algorithm: author-corrected L-SHADE 1.0.1 MATLAB/Octave release.
- Author archive SHA-256: `a9d094018b18da674849a97415116146dae6e423c19be8ef0ada9766890f0b9b`.
- Functional reference: `LSHADE101_Reference.m`.
- Passive trace port: `LSHADE101_FrozenCore.m`.
- Both ports dispatch to the same audited L-SHADE 1.0.1 engine mathematics. The interface adaptation accepts external objectives, fixed bounds, and an exact final partial generation.

## Frozen tasks

- Sphere, Rosenbrock, and Rastrigin.
- Dimension 10, population 50, bounds `[-5,5]^10`.
- Exact target: 5,000 objective calls.
- Seeds: 20260741, 20260742, and 20260743.
- Total: 9 reference runs, 9 passive-trace runs, and 9 same-seed trace replays.

## Frozen positive gate

Every task-seed record must match exactly in final objective, final solution, full convergence curve, every evaluated point, FE count, initial population, final RNG state, and complete trace replay. The trace trial vectors must equal the evaluated points after initialization. Any mismatch terminates the positive case; partial pass rates are not promoted to admissibility.

## Claim boundary

Passing establishes a dependency-complete, end-to-end external algorithm execution case under a disclosed common-objective adapter. It does not establish L-SHADE superiority or validate every language/platform release.
