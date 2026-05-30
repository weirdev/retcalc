# Monte Carlo retirement simulations

    python retcalc.py

## Run tests

    python -m unittest

## Methodology

Optimizations (max safe expenditure / minimum required savings) binary-search a
variable against a tail-risk constraint. To keep that search well-posed, the
simulation shocks are sampled once per optimization and reused across every
evaluation (common random numbers), so only the optimized variable changes
between steps rather than the underlying randomness. This removes the
run-to-run jitter that came from re-sampling the objective on each step.

Each calculation also accepts an optional random seed. Leave it blank for a
fresh random run (results are still stable within that run); supply an integer
to reproduce a run exactly.

## Next Steps
0. Housekeeping
    - Tests
        - Basic data types -- Done
        - simulate -- Done
        - worst case -- Done
        - reallocate -- Done
        - retirement_value -- Done
        - inflated_val / inflated_payments -- Done
        - insert_alloc_set_priority -- Done
        - YAML save/load round-trip -- Done
    - Bugs
        - reduce_expenditure flag in retirement_value is reassigned each loop iteration instead of OR'd, so only the last asset's performance determines expenditure reduction (contradicts docstring's "any asset" intent) -- Done
        - rebalance_assets fails its own assertion when a single priority class combines both minimum values and fractional allocation -- Done
    - Performance
        - Cleanup unnecessary copying -- Done
        - reallocate introduced some perf regressions, see if these can be mitigated -- Done
        - Simulation loop can be multithreaded
1. Extensibe "waterfall" of asset classes
    - Each with different configurable returns, risks, and priority -- Done
    - Each year assets reallocated -- Done
    - Allocation by minimum value given priority -- Done
    - Proportional allocation -- TODO
    - Update yearly contribution prompt to reflect new asset classes -- TODO
        - What was this?
2. Simulation for any variable
    - Simplify code by having single input-taking function that accepts an array of RValues
    - Split current "Calculate max expenditure in retirement" option into "Calculate assets after time" and "Calculate max expenditure in retirement" (given assets at retirement)
    - Calculate best proportion of FI assets to equities
