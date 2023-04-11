from os import path, listdir
import random
from typing import List, Optional, MutableSet, Tuple

from prompt import choose, takebool, takefloat, takeint
from rettypes import *
from yaml_helper import load_yaml, dump_yaml


SAVED_SCENARIOS_DIRNAME = "savedscenarios"


def save_retirement_settings(scenario: 'RetirementSettings'):
    filename = input("Filename [.yaml]: ").strip()
    if not filename.endswith(".yaml"):
        filename += ".yaml"
    filepath = path.join(SAVED_SCENARIOS_DIRNAME, filename)
    dump_yaml(scenario.to_structured(), filepath)


def select_and_load_retirement_settings() -> Optional['RetirementSettings']:
    files = [(filename, filename)
             for filename in listdir(SAVED_SCENARIOS_DIRNAME)]
    if len(files) == 0:
        print("No saved retirement scenarios available")
        return None
    elif len(files) == 1:
        print(f"Using scenario from {files[0][1]}")
    filename = choose(files)
    filepath = path.join(SAVED_SCENARIOS_DIRNAME, filename)
    return RetirementSettings.from_structured(load_yaml(filepath))


def inflated_val(val: float, r: float, t: int):
    return val * ((1 + r)**t)


def inflated_payments(payment: float, r: float, t: int) -> float:
    total = 0
    for i in range(t):
        total += inflated_val(payment, r, i)
    return total


def retirement_value(retirementSettings: RetirementSettings) -> RetirementSettings:
    inflation_s = random.gauss(*retirementSettings.inflation)
    inflation_factor = 1 + inflation_s

    new_rs = retirementSettings.copy()

    to_spend = retirementSettings.expendature
    hit_zero = False
    for ri, asset_alloc in enumerate(reversed(new_rs.asset_allocations)):
        if ri == len(new_rs.asset_allocations) - 1:
            if asset_alloc.asset.value < to_spend:
                hit_zero = True
            spent = to_spend
        else:
            spent = min(asset_alloc.asset.value, to_spend)
        asset_alloc.asset.value -= spent
        to_spend -= spent
        asset_alloc.minimum_value *= inflation_factor

    if not hit_zero:
        for asset_alloc in new_rs.asset_allocations:
            asset_alloc.asset.value *= (1 + random.gauss(asset_alloc.asset.mean_return,
                                                     asset_alloc.asset.return_stdev))
        rebalance_assets(new_rs.asset_allocations)

    new_rs.expendature *= inflation_factor

    if retirementSettings.t > 0:
        new_rs.t -= 1
        return retirement_value(new_rs)
    return new_rs


def simulate(retirementSettings: RetirementSettings, n: int) -> List[RetirementSettings]:
    results = []
    for _ in range(n):
        results.append(retirement_value(retirementSettings.copy()))
    return results


def worst_case(runs: List[RetirementSettings], pmin: float):
    """
    pmin = tail probablility, ie. 1/100 worst case
    """
    runs = sorted(runs, key=lambda rs: rs.current_value())
    return runs[int(len(runs) * pmin)]


def optimize_r_var(retirementSettings: RetirementSettings, r_var_to_opt: RValue, maximize: bool,
                   pmin: float) -> float:
    low = 0
    high = 100

    # r_val_print(retirementSettings)
    # input()

    # Find top end of range
    retirementSettings.update_val(r_var_to_opt, lambda _: high)
    while (worst_case(simulate(retirementSettings, 10_000), pmin).current_value() -
            retirementSettings.emergency_min < 0) ^ maximize:
        # TODO: Update low to previous high
        # r_val_print(retirementSettings)
        # input()
        high = high * 2
        retirementSettings.update_val(r_var_to_opt, lambda _: high)

    diff = high
    while diff > 100:  # TODO: Make relative to mid
        # r_val_print(retirementSettings)
        # input()
        mid = low + (diff / 2)
        retirementSettings.update_val(r_var_to_opt, lambda _: mid)
        if (worst_case(simulate(retirementSettings, 10_000), pmin).current_value() -
                retirementSettings.emergency_min > 0) ^ maximize:
            high = mid
        else:
            low = mid
        diff = high - low

    return high


def rebalance_assets(asset_allocations: List[AssetAllocation]) -> None:
    total_assets = sum([a.asset.value for a in asset_allocations])
    if total_assets == 0:
        return
    assert total_assets > 0
    remaining_assets = total_assets

    priority_class: MutableSet[AssetAllocation] = set()
    priority = None
    requested_pc_total = 0.0
    for i, asset_alloc in enumerate(asset_allocations):
        if priority is None:
            priority = asset_alloc.priority
        priority_class.add(asset_alloc)
        requested_pc_total += asset_alloc.minimum_value

        if (i + 1 < len(asset_allocations) and 
                priority < asset_allocations[i + 1].priority and
                requested_pc_total > 0):
            # If not enough remaining funds, distribute proportionally
            # factor: (0, 1]
            factor = min(remaining_assets / requested_pc_total, 1.0)
            for aa in priority_class:
                aa.asset.value = aa.minimum_value * factor
                remaining_assets -= aa.asset.value
            priority_class = set()
            priority = None
            requested_pc_total = 0.0
        elif i + 1 == len(asset_allocations):
            # At end of allocs so may have money beyond min requested
            # Distribute proportionally
            # factor: (0,inf)
            if requested_pc_total == 0:
                equalprop = remaining_assets / len(priority_class)
                for aa in priority_class:
                    aa.asset.value = equalprop
                    remaining_assets -= aa.asset.value
            else:
                factor = remaining_assets / requested_pc_total
                for aa in priority_class:
                    aa.asset.value = aa.minimum_value * factor
                    remaining_assets -= aa.asset.value

    # We distributed all the $$
    assert abs(remaining_assets) < 0.01
    # Total assets remains constant
    assert abs(total_assets - sum([a.asset.value for a in asset_allocations])) < 0.01


def rsettings_print(retirementSettings: RetirementSettings):
    print(f"Expendature: ${retirementSettings.expendature:,.2f}")
    print("Asset allocations:")
    asset_allocs_print(retirementSettings.asset_allocations)
    print(f"Inflation mean: {retirementSettings.inflation[0]*100:.2f}%")
    print(f"Inflation stdev: {retirementSettings.inflation[1]*100:.2f}%")
    print(f"Years left: {retirementSettings.t}")


def asset_allocs_print(asset_allocations: List[AssetAllocation]):
    for alloc in asset_allocations:
        print(f"\tAsset: {alloc.asset.name}")
        print(f"\tValuation: ${alloc.asset.value:,.2f}")
        print(f"\tMean return: ${alloc.asset.mean_return*100:.2f}%")
        print(f"\tReturn stdev: ${alloc.asset.return_stdev*100:.2f}%")
        print(f"\tPriority: {alloc.priority}")
        print(f"\tMinimum value: {alloc.minimum_value}")
        print(
            f"\tPreferred fraction of priority class: {alloc.preferred_fraction_of_priority_class*100:.2f}%")
        print()


def insert_alloc_set_priority(asset_alloc: AssetAllocation, priority: float,
                              asset_allocations: List[AssetAllocation]):
    idx = 0
    intpri = 0
    bump_pri = False
    for i, aa in enumerate(asset_allocations):
        if bump_pri:
            aa.priority += 1
        elif priority < aa.priority:
            idx = i
            if priority % 1 == 0:
                intpri = int(priority)
                break
            else:
                intpri = aa.priority
                aa.priority += 1
                bump_pri = True
        elif priority == aa.priority:
            idx = i + 1

    asset_alloc.priority = intpri
    asset_allocations.insert(idx, asset_alloc)


def choose_priority(asset_allocations: List[AssetAllocation]) -> float:
    options: List[Tuple[str, float]] = []
    for i, alloc in enumerate(asset_allocations):
        if i == 0:
            options.append(
                (f"Prioritize over {alloc.asset.name}", alloc.priority - 0.5))
        options.append(
            (f"Prioritize equally with {alloc.asset.name}", alloc.priority))
        if i == len(asset_allocations) - 1:
            options.append(
                (f"Prioritize below {alloc.asset.name}", alloc.priority + 0.5))
        else:
            options.append(
                (f"Prioritize between {alloc.asset.name} and {asset_allocations[i+1].asset.name}",
                 alloc.priority + 0.5))

    if len(options) > 0:
        return choose(options)
    return 0


def safe_ret_expenditure_prompt():
    current_state = None
    if choose([("Load current state from disk", True),
               ("Enter current state now", False)]):
        current_state = select_and_load_retirement_settings()

    if current_state is None:
        t = takeint(
            "Whole number of remaining earning years from today", lbound=1)

        allocations = []
        add_asset = True
        while add_asset:
            print()
            print("Adding new asset")
            name = input("Asset name: ")
            value = takefloat(f"Amount invested in {name}", lbound=0)
            mean_return = takefloat(
                f"Enter estimated mean {name} return over this period", -1, 1)
            return_stdev = takefloat(
                f"Enter estimated current statemated {name} return standard deviation over this period", 0, 1)
            asset = Asset(name, value, mean_return, return_stdev)

            insert_alloc_set_priority(
                AssetAllocation(asset, 0, 0, 0),
                choose_priority(allocations),
                allocations)
            add_asset = choose(
                [("Add another asset", True), ("Finished adding assets", False)])
        print()
        expenditure = - \
            takefloat(
                "Enter expected annual equity contributions over this period (your yearly savings) ($)")
        inflation = (takefloat("Enter estimated mean inflation over this period", -1, 1),
                     takefloat("Enter estimated inflation standard deviation over this period", 0, 1))

        current_state = RetirementSettings(
            expenditure, inflation, t, 0, allocations)

        if takebool("Save pre-retirement scenario to disk?"):
            save_retirement_settings(current_state)

    print()
    wcp = takefloat(
        "Enter tail probability for Monte Carlo simulation (<0.5=worse than average result)", 0, 1)
    print("Simulating 10,000 possible scenarios...")
    runs = simulate(current_state, 10_000)
    result_setting = worst_case(runs, wcp)

    retwealth = result_setting.current_value()
    print(f"Estimated new worth at end of earning years: ${retwealth:,.2f}")

    print()
    t = takeint("Enter estimated whole number of years of retirement", lbound=1)

    print()
    print("Binary searching possible retirement scenarios 10,000 times each...")
    retirement_start = result_setting.copy()
    retirement_start.expendature = 0
    retirement_start.t = t
    maxexp = optimize_r_var(retirement_start, RValue(
        RSetting.EXPENDATURE), True, wcp)
    print(f"Maximum safe yearly expendature in retirement: ${maxexp:,.2f}")

    print()
    if takebool("Save retirement scenario to disk?"):
        save_retirement_settings(retirement_start)


def savings_required_for_expenditure_prompt():
    retirement_scenario = None
    if choose([("Load retirement scenario from disk", True),
               ("Enter retirement scenario now", False)]):
        retirement_scenario = select_and_load_retirement_settings()
        if retirement_scenario is not None:
            rsettings_print(retirement_scenario)

    if retirement_scenario is None:
        expenditure = takefloat(
            "Enter amount to be withdrawn from equities yearly ($)", lbound=0)
        t = takeint(
            "Enter estimated whole number of years of retirement", lbound=1)
        inflation = (takefloat("Enter estimated mean inflation over this period", -1, 1),
                     takefloat("Enter estimated inflation standard deviation over this period", 0, 1))
        eret = (takefloat("Enter estimated mean equity return over this period", -1, 1),
                takefloat("Enter estimated equity return standard deviation over this period", 0, 1))
        retirement_scenario = RetirementSettings(expenditure, inflation, t, 0,
                                                 [AssetAllocation(Asset("Equities", 0, eret[0], eret[1]),
                                                                  0, 0, 0)])

    print()
    wcp = takefloat(
        "Enter tail probability for Monte Carlo simulation (<0.5=worse than average result)", 0, 1)

    print()
    print("Binary searching possible retirement scenarios 10,000 times each...")
    maxexp = optimize_r_var(
        retirement_scenario,
        RValue(RSetting.ASSET_ALLOCATIONS,
               (len(retirement_scenario.asset_allocations)-1,
                AllocationValue(AllocationSetting.ASSET, AssetSetting.VALUE))),  # type: ignore
        False, wcp)
    print(f"Minimum safe equity savings for retirement: ${maxexp:,.2f}")


if __name__ == '__main__':
    # rs = retirement_value(RetirementSettings(100, 0, 0, 0, (0.04, .02), (0, 0), 65, 0,
    #     [AssetAllocation(Asset("eme", 1000, 0, 0), 0, 0, 0),
    #     AssetAllocation(Asset("f", 30000, .04, .02), 2, 0, 0),
    #     AssetAllocation(Asset("eq", 615000, .1, .03), 3, 0, 0)]))
    # print(rs.current_value())

    prompt_fns = [("Calculate max expenditure in retirement", safe_ret_expenditure_prompt),
                  ("Calculate savings needed for retirement", savings_required_for_expenditure_prompt)]
    prompt_fn = choose(prompt_fns)
    if prompt_fn:
        prompt_fn()
