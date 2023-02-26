# Monte Carlo retirement simulations

    python retcalc.py

## Next Steps
1. Extensibe "waterfall" of asset classes
    - Each with different configurable returns, risks, and priority -- Done
    - Each year assets reallocated -- TODO
    - Update yearly contribution prompt to reflect new asset classes -- TODO
2. Simulation for any variable
    - Simplify code by having single input-taking function that accepts an array of RValues
    - Split current "Calculate max expenditure in retirement" option into "Calculate assets after time" and "Calculate max expenditure in retirement"