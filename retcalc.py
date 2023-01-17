import random
from enum import Enum
from typing import Any, Callable, List, Optional, Tuple

from prompt import choose, takefloat, takeint


class AssetSetting(Enum):
    NAME = 1
    VALUE = 2
    MEAN_RETURN = 3
    RETURN_STDEV = 4


class Asset:
    def __init__(self, name, value, mean_return, return_stdev):
        self.name = name
        self.value = value
        self.mean_return = mean_return
        self.return_stdev = return_stdev

    def copy(self) -> 'Asset':
        return Asset(self.name, self.value, self.mean_return, self.return_stdev)

    def update_val(self, asset_setting: AssetSetting, op: Callable[[Any], Any]):
        if asset_setting == AssetSetting.NAME:
            self.name = op(self.name)
        elif asset_setting == AssetSetting.VALUE:
            self.value = op(self.value)
        elif asset_setting == AssetSetting.MEAN_RETURN:
            self.mean_return = op(self.mean_return)
        elif asset_setting == AssetSetting.RETURN_STDEV:
            self.return_stdev = op(self.return_stdev)


class AllocationSetting(Enum):
    ASSET = 1
    PRIORITY = 2
    MINIMUM_VALUE = 3
    PREFERRED_FRACTION_OF_PRIORITY_CLASS = 4


class AllocationValue:
    def __init__(self, allocation_setting, asset_setting=None):
        self.allocation_setting = allocation_setting
        self.asset_setting = asset_setting


class AssetAllocation:
    def __init__(self, asset: Asset, priority, minimum_value, preferred_fraction_of_priority_class):
        self.asset = asset
        self.priority = priority
        self.minimum_value = minimum_value
        self.preferred_fraction_of_priority_class = preferred_fraction_of_priority_class

    def copy(self) -> 'AssetAllocation':
        return AssetAllocation(self.asset.copy(), self.priority, self.minimum_value,
                               self.preferred_fraction_of_priority_class)

    def update_val(self, avalue: AllocationValue, op: Callable[[Any], Any]):
        asetting = avalue.allocation_setting
        if asetting == AllocationSetting.ASSET:
            if avalue.asset_setting is None:
                self.asset = op(self.asset)
            else:
                self.asset.update_val(avalue.asset_setting, op)
        elif asetting == AllocationSetting.PRIORITY:
            self.priority = op(self.priority)
        elif asetting == AllocationSetting.MINIMUM_VALUE:
            self.minimum_value = op(self.minimum_value)
        elif asetting == AllocationSetting.PREFERRED_FRACTION_OF_PRIORITY_CLASS:
            self.preferred_fraction_of_priority_class = op(
                self.preferred_fraction_of_priority_class)


class RSetting(Enum):
    EXPENDATURE = 1
    INFLATION = 5
    T = 7
    EMERGENCY_MIN = 8
    ASSET_ALLOCATIONS = 9


class RValue:
    def __init__(self, rsetting: RSetting, allocation_value: Optional[Tuple[int, AllocationValue]] = None):
        self.rsetting = rsetting
        self.allocation_value = allocation_value


class RetirementSettings:
    def __init__(self, expendature, inflation: Tuple[float, float],
                 t: int, emergency_min, asset_allocations: List[AssetAllocation]):
        self.expendature = expendature
        self.inflation = inflation
        self.t = t
        self.emergency_min = emergency_min
        asset_allocations.sort(key=lambda a: a.priority)
        self.asset_allocations = asset_allocations

    def update_val(self, rvalue: RValue, op: Callable[[Any], Any]):
        rsetting = rvalue.rsetting
        if rsetting == RSetting.EXPENDATURE:
            self.expendature = op(self.expendature)
        elif rsetting == RSetting.INFLATION:
            self.inflation = op(self.inflation)
        elif rsetting == RSetting.T:
            self.t = op(self.t)
        elif rsetting == RSetting.EMERGENCY_MIN:
            self.emergency_min = op(self.emergency_min)
        elif rsetting == RSetting.ASSET_ALLOCATIONS:
            if rvalue.allocation_value is None:
                self.asset_allocations = op(self.asset_allocations)
            else:
                self.asset_allocations[rvalue.allocation_value[0]].update_val(
                    rvalue.allocation_value[1], op)

    def get_val(self, rsetting: RSetting):
        if rsetting == RSetting.EXPENDATURE:
            return self.expendature
        elif rsetting == RSetting.INFLATION:
            return self.inflation
        elif rsetting == RSetting.T:
            return self.t
        elif rsetting == RSetting.EMERGENCY_MIN:
            return self.emergency_min
        elif rsetting == RSetting.ASSET_ALLOCATIONS:
            return self.asset_allocations

    def current_value(self):
        return sum(map(lambda a: a.asset.value, self.asset_allocations))

    def copy(self) -> 'RetirementSettings':
        return RetirementSettings(self.expendature, self.inflation, self.t,
                                  self.emergency_min,
                                  [a.copy() for a in self.asset_allocations])


def inflated_val(val: float, r: float, t: int):
    return val * ((1 + r)**t)


def inflated_payments(payment: float, r: float, t: int) -> float:
    total = 0
    for i in range(t):
        total += inflated_val(payment, r, i)
    return total


def retirement_value(retirementSettings: RetirementSettings) -> RetirementSettings:
    inflation_s = random.gauss(*retirementSettings.inflation)

    new_rs = retirementSettings.copy()

    to_spend = retirementSettings.expendature
    for ri, asset_alloc in enumerate(reversed(new_rs.asset_allocations)):
        if ri == len(new_rs.asset_allocations) - 1:
            # If on last asset, we can go negative
            spent = to_spend
        else:
            spent = min(asset_alloc.asset.value, to_spend)
        asset_alloc.asset.value -= spent
        to_spend -= spent
        asset_alloc.asset.value *= (1 + random.gauss(asset_alloc.asset.mean_return,
                                                     asset_alloc.asset.return_stdev))

    new_rs.expendature *= (1 + inflation_s)

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


def r_val_print(retirementSettings: RetirementSettings):
    print(f"Expendature: ${retirementSettings.expendature:,.2f}")
    print("Asset allocations:")
    for alloc in retirementSettings.asset_allocations:
        print(f"\tAsset: {alloc.asset.name}")
        print(f"\tValuation: ${alloc.asset.value:,.2f}")
        print(f"\tMean return: ${alloc.asset.mean_return*100:.2f}%")
        print(f"\tReturn stdev: ${alloc.asset.return_stdev*100:.2f}%")
        print(f"\tPriority: {alloc.priority}")
        print(f"\tMinimum value: {alloc.minimum_value}")
        print(
            f"\tPreferred fraction of priority class: {alloc.preferred_fraction_of_priority_class*100:.2f}%")
        print()
    print(f"Inflation mean: {retirementSettings.inflation[0]*100:.2f}%")
    print(f"Inflation stdev: {retirementSettings.inflation[1]*100:.2f}%")
    print(f"Years left: {retirementSettings.t}")


def choose_priority(asset_allocations: List[AssetAllocation]) -> int:
    options: List[Tuple[str, int]] = []
    for i, alloc in enumerate(asset_allocations):
        alloc.priority *= 2  # Space out so we can put new priority in between
        if i == 0:
            options.append(
                (f"Prioritize over {alloc.asset.name}", alloc.priority - 1))
        options.append(
            (f"Prioritize equally with {alloc.asset.name}", alloc.priority))
        if i == len(asset_allocations) - 1:
            options.append(
                (f"Prioritize below {alloc.asset.name}", alloc.priority + 1))
        else:
            options.append(
                (f"Prioritize between {alloc.asset.name} and {asset_allocations[i+1].asset.name}",
                 alloc.priority + 1))

    priority = choose(options)
    if priority is not None:
        return priority
    return 0


def safe_ret_expenditure_prompt():
    t = takeint("Whole number of remaining earning years from today", lbound=1)

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
            f"Enter estimated {name} return standard deviation over this period", 0, 1)
        asset = Asset(name, value, mean_return, return_stdev)

        allocations.append(AssetAllocation(
            asset, choose_priority(allocations), 0, 0))
        add_asset = choose(
            [("Add another asset", True), ("Finished adding assets", False)])
    print()
    expenditure = - \
        takefloat(
            "Enter expected annual equity contributions over this period (your yearly savings) ($)")
    inflation = (takefloat("Enter estimated mean inflation over this period", -1, 1),
                 takefloat("Enter estimated inflation standard deviation over this period", 0, 1))

    print()
    wcp = takefloat(
        "Enter tail probability for Monte Carlo simulation (<0.5=worse than average result)", 0, 1)
    print("Simulating 10,000 possible scenarios...")
    runs = simulate(RetirementSettings(expenditure, inflation, t, 0, allocations),
                    10_000)
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


def savings_required_for_expenditure_prompt():
    expenditure = takefloat(
        "Enter amount to be withdrawn from equities yearly ($)", lbound=0)
    t = takeint("Enter estimated whole number of years of retirement", lbound=1)
    inflation = (takefloat("Enter estimated mean inflation over this period", -1, 1),
                 takefloat("Enter estimated inflation standard deviation over this period", 0, 1))
    eret = (takefloat("Enter estimated mean equity return over this period", -1, 1),
            takefloat("Enter estimated equity return standard deviation over this period", 0, 1))
    wcp = takefloat(
        "Enter tail probability for Monte Carlo simulation (<0.5=worse than average result)", 0, 1)

    print()
    print("Binary searching possible retirement scenarios 10,000 times each...")
    maxexp = optimize_r_var(
        RetirementSettings(expenditure, inflation, t, 0,
                           [AssetAllocation(Asset("Equities", 0, eret[0], eret[1]), 0, 0, 0)]),
        RValue(RSetting.ASSET_ALLOCATIONS,
               (0, AllocationValue(AllocationSetting.ASSET, AssetSetting.VALUE))),
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
