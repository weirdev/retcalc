from os import path, listdir, mkdir
import random
from typing import List, Optional, MutableSet, Tuple

from prompt import choose, takebool, takefloat, takeint
from rettypes import *
from yaml_helper import load_yaml, dump_yaml


SAVED_SCENARIOS_DIRNAME = "savedscenarios"


def save_retirement_settings(scenario: 'RetirementSettings', 
                             filepath: Optional[str] = None):
    if filepath is None:
        filename = input("Filename [.yaml]: ").strip()
        if not filename.endswith(".yaml"):
            filename += ".yaml"
        filepath = path.join(SAVED_SCENARIOS_DIRNAME, filename)
    dump_yaml(scenario.to_structured(), filepath)


def select_retirement_settings_file() -> Optional[str]:
    if not path.isdir(SAVED_SCENARIOS_DIRNAME):
        mkdir(SAVED_SCENARIOS_DIRNAME)
    files = [(filename, filename)
             for filename in listdir(SAVED_SCENARIOS_DIRNAME)]
    if len(files) == 0:
        print("No saved retirement scenarios available")
        return None
    elif len(files) == 1:
        print(f"Using scenario from {files[0][1]}")
    filename = choose(files)
    filepath = path.join(SAVED_SCENARIOS_DIRNAME, filename)
    return filepath


def load_retirement_settings(filepath: str) -> Optional['RetirementSettings']:
    return RetirementSettings.from_structured(load_yaml(filepath))


def select_and_load_retirement_settings() -> Optional['RetirementSettings']:
    filepath = select_retirement_settings_file()
    if filepath is None:
        return None
    return load_retirement_settings(filepath)


def inflated_val(val: float, r: float, t: int):
    return val * ((1 + r)**t)


def inflated_payments(payment: float, r: float, t: int) -> float:
    total = 0
    for i in range(t):
        total += inflated_val(payment, r, i)
    return total


def retirement_value(retirementSettings: RetirementSettings) -> RetirementSettings:
    new_rs = retirementSettings.copy()

    while new_rs.t > 0:
        inflation_s = random.gauss(*new_rs.inflation)
        inflation_factor = 1 + inflation_s

        to_spend = new_rs.expendature
        hit_zero = False
        for ri, asset_alloc in enumerate(reversed(new_rs.asset_distribution.asset_allocations)):
            if ri == len(new_rs.asset_distribution.asset_allocations) - 1:
                if asset_alloc.asset.value < to_spend:
                    hit_zero = True
                spent = to_spend
            else:
                spent = min(asset_alloc.asset.value, to_spend)
            asset_alloc.asset.value -= spent
            to_spend -= spent
            asset_alloc.minimum_value *= inflation_factor

        if not hit_zero:
            for asset_alloc in new_rs.asset_distribution.asset_allocations:
                asset_alloc.asset.value *= 1 + random.gauss(asset_alloc.asset.mean_return,
                                                            asset_alloc.asset.return_stdev)
            rebalance_assets(new_rs.asset_distribution.asset_allocations)

        new_rs.expendature *= inflation_factor
        new_rs.t -= 1

    return new_rs


def simulate(retirementSettings: RetirementSettings, n: int) -> List[RetirementSettings]:
    return [retirement_value(retirementSettings.copy()) for _ in range(n)]


def worst_case(runs: List[RetirementSettings], pmin: float):
    """
    pmin = tail probablility, ie. 1/100 worst case
    """
    runs = sorted(runs, key=lambda rs: rs.current_value())
    return runs[int(len(runs) * pmin)]


def optimize_r_var(
        retirementSettings: RetirementSettings, r_var_to_opt: RValue,
        maximize: bool, pmin: float) -> float:
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
    def get_and_clear_value(asset: Asset):
        value = asset.value
        asset.value = 0
        return value
    total_assets = sum([get_and_clear_value(aa.asset)
                       for aa in asset_allocations])
    if total_assets == 0:
        return
    assert total_assets > 0
    remaining_assets = total_assets

    priority_class: MutableSet[AssetAllocation] = set()
    priority = None
    pc_total_min_value = 0.0
    pc_total_fraction = 0.0
    for i, asset_alloc in enumerate(asset_allocations):
        if priority is None:
            priority = asset_alloc.priority
        priority_class.add(asset_alloc)
        pc_total_min_value += asset_alloc.minimum_value
        pc_total_fraction += asset_alloc.desired_fraction_of_total_assets

        if (i + 1 == len(asset_allocations) or
                (priority < asset_allocations[i + 1].priority and
                    (pc_total_min_value > 0 or pc_total_fraction > 0))):
            # Reached end of priority class

            if i + 1 == len(asset_allocations):
                # At end of allocs so may have remaining assets
                outstanding_fraction = remaining_assets / total_assets
                last_pc = True
            else:
                outstanding_fraction = pc_total_fraction
                last_pc = False

            if pc_total_min_value > 0:
                # If not enough remaining funds, distribute proportionally
                # factor: (0, 1]
                factor = min(remaining_assets / pc_total_min_value, 1.0)
                for aa in priority_class:
                    aa.asset.value = aa.minimum_value * factor
                    remaining_assets -= aa.asset.value
                    if last_pc:  # At end of allocs, distribute everything
                        outstanding_fraction -= aa.asset.value / total_assets
                    else:  # Otherwise, distribute only requested fraction
                        outstanding_fraction -= min(aa.asset.value / total_assets,
                                                    aa.desired_fraction_of_total_assets)

            if outstanding_fraction > 0:
                amount_to_allocate = outstanding_fraction * total_assets
                factor = min(remaining_assets / amount_to_allocate, 1.0)
                equal_fraction_if_unallocated = 0
                if last_pc:
                    if pc_total_fraction == 0:
                        # Last priority class and no fraction requested, so distribute equally
                        equal_fraction_if_unallocated = outstanding_fraction / \
                            len(priority_class)
                    else:
                        # Last priority class and fraction requested, so distribute proportionally
                        # factor: (0, 1]
                        # Normalize pc_total_fraction by the fraction of the total assets outstanding
                        factor /= pc_total_fraction / outstanding_fraction

                for aa in priority_class:
                    new_asset_value = \
                        max(aa.asset.value,
                            max(aa.desired_fraction_of_total_assets,
                                equal_fraction_if_unallocated)
                            * factor * total_assets)
                    remaining_assets -= new_asset_value - aa.asset.value
                    aa.asset.value = new_asset_value

            # Reset priority class
            priority_class = set()
            priority = None
            pc_total_min_value = 0.0
            pc_total_fraction = 0.0

        if abs(remaining_assets) < 0.001:
            break

    # We distributed all the $$
    assert abs(remaining_assets) < 0.001
    # Total assets remains constant
    assert abs(total_assets -
               sum([a.asset.value for a in asset_allocations])) < 0.001


def rsettings_print(retirementSettings: RetirementSettings):
    print(f"Expendature: ${retirementSettings.expendature:,.2f}")
    print("Asset distribution:")
    asset_dist_print(retirementSettings.asset_distribution)
    print(f"Inflation mean: {retirementSettings.inflation[0]*100:.2f}%")
    print(f"Inflation stdev: {retirementSettings.inflation[1]*100:.2f}%")
    print(f"Years left: {retirementSettings.t}")


def asset_dist_print(asset_distribution: AssetDistribution):
    asset_allocs_print(asset_distribution.asset_allocations)


def asset_allocs_print(asset_allocations: List[AssetAllocation]):
    for alloc in asset_allocations:
        print(f"\tAsset: {alloc.asset.name}")
        print(f"\tValuation: ${alloc.asset.value:,.2f}")
        print(f"\tMean return: ${alloc.asset.mean_return*100:.2f}%")
        print(f"\tReturn stdev: ${alloc.asset.return_stdev*100:.2f}%")
        print(f"\tPriority: {alloc.priority}")
        print(f"\tMinimum value: ${alloc.minimum_value:,.2f}")
        print(f"\tPreferred fraction of priority class: \
              {alloc.desired_fraction_of_total_assets*100:.2f}%")
        print()


def insert_alloc_set_priority(
        asset_alloc: AssetAllocation, priority: float,
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
                (f"Prioritize between {alloc.asset.name} and \
                 {asset_allocations[i+1].asset.name}",
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
                f"Enter estimated current statemated {name} return \
                    standard deviation over this period", 0, 1)
            asset = Asset(name, value, mean_return, return_stdev)

            insert_alloc_set_priority(
                AssetAllocation(asset, 0, 0, 0),
                choose_priority(allocations),
                allocations)
            add_asset = choose(
                [("Add another asset", True), ("Finished adding assets", False)])
        print()
        expenditure = - \
            takefloat("Enter expected annual equity contributions over \
                      this period (your yearly savings) ($)")
        inflation = (takefloat("Enter estimated mean inflation over this period",
                               -1, 1),
                     takefloat("Enter estimated inflation standard deviation \
                               over this period", 0, 1))

        current_state = RetirementSettings(
            expenditure, inflation, t, 0, AssetDistribution(allocations))

        if takebool("Save pre-retirement scenario to disk?"):
            save_retirement_settings(current_state)

    print()
    wcp = takefloat(
        "Enter tail probability for Monte Carlo simulation \
            (<0.5=worse than average result)", 0, 1)
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
        inflation = (takefloat("Enter estimated mean inflation over this period",
                               -1, 1),
                     takefloat("Enter estimated inflation standard deviation \
                               over this period", 0, 1))
        eret = (takefloat("Enter estimated mean equity return over this period",
                          -1, 1),
                takefloat("Enter estimated equity return standard deviation \
                          over this period", 0, 1))
        retirement_scenario = RetirementSettings(
            expenditure, inflation, t, 0,
            AssetDistribution([AssetAllocation(Asset("Equities", 0, eret[0], eret[1]),
                                               0, 0, 0)]))

    print()
    wcp = takefloat(
        "Enter tail probability for Monte Carlo simulation \
            (<0.5=worse than average result)", 0, 1)

    print()
    print("Binary searching possible retirement scenarios 10,000 times each...")
    maxexp = optimize_r_var(
        retirement_scenario,
        RValue(RSetting.ASSET_DISTRIBUTION,
               DistributionValue(
                   DistributionSetting.ASSET_ALLOCATIONS,
                   (len(retirement_scenario.asset_distribution.asset_allocations)-1,
                    AllocationValue(AllocationSetting.ASSET, AssetSetting.VALUE)))),  # type: ignore
        False, wcp)
    print(f"Minimum safe equity savings for retirement: ${maxexp:,.2f}")


def rewrite_retirement_scenario_prompt():
    scenario_file = select_retirement_settings_file()
    if scenario_file is not None:
        retirement_scenario = load_retirement_settings(scenario_file)
        if retirement_scenario is not None:
            rsettings_print(retirement_scenario)
            if takebool("Overwrite this scenario?"):
                save_retirement_settings(retirement_scenario, scenario_file)


if __name__ == '__main__':
    # rs = retirement_value(RetirementSettings(100, 0, 0, 0, (0.04, .02), (0, 0), 65, 0,
    #     [AssetAllocation(Asset("eme", 1000, 0, 0), 0, 0, 0),
    #     AssetAllocation(Asset("f", 30000, .04, .02), 2, 0, 0),
    #     AssetAllocation(Asset("eq", 615000, .1, .03), 3, 0, 0)]))
    # print(rs.current_value())

    prompt_fns = [("Calculate max expenditure in retirement", safe_ret_expenditure_prompt),
                  ("Calculate savings needed for retirement",
                   savings_required_for_expenditure_prompt),
                  ("Rewrite retirement scenario", rewrite_retirement_scenario_prompt)]
    prompt_fn = choose(prompt_fns)
    if prompt_fn:
        prompt_fn()
