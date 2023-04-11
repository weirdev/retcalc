# Monte Carlo retirement simulations

    python retcalc.py

## Run tests

    python -m unittest

## Next Steps
0. Housekeeping
    - Tests
        - Basic data types -- Done
        - simulate -- TODO
        - worst case -- TODO
        - reallocate -- TODO
    - Performance
        - Cleanup unnecessary copying
        - reallocate introduced some perf regressions, see if these can be mitigated
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
