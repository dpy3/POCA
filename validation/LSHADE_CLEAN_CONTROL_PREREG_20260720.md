# Official L-SHADE 1.0.1 clean-control preregistration

Freeze date: 2026-07-20

## Identity

- Canonical source: author-corrected L-SHADE 1.0.1 MATLAB/Octave release.
- Author ZIP SHA-256: `a9d094018b18da674849a97415116146dae6e423c19be8ef0ada9766890f0b9b`.
- Functional reference: `LSHADE101_Reference.m`.
- Passive trace port: `LSHADE101_FrozenCore.m`, both dispatching to the same frozen `LSHADE101_Engine.m` mathematics.

## Frozen smoke

- Objective: sphere.
- Dimension: 10.
- Bounds: `[-100,100]`.
- Initial population: 50.
- Exact target: 2,000 true objective evaluations.
- Seed: 20260725 using MATLAB `twister`.

## Gate

The clean control passes only if reference and passive-trace runs have exactly identical final score, solution, complete convergence curve, every evaluated point, FE count, and final RNG state. The independent counter must equal 2,000 and the trace port must produce no change in the optimization trajectory.

This is a false-positive control for layers 1--3 and observer non-interference. It is not a performance comparison.

