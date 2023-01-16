import random
from enum import Enum
from typing import Any, Callable, List

from prompt import choose, takefloat, takeint


class Asset:
    def __init__(self, value, mean_return, return_stdev):
        self.value = value
        self.mean_return = mean_return
        self.return_stdev = return_stdev


class RSetting(Enum):
    EXPENDATURE = 1
    EMERGENCY = 2
    FIXED = 3
    EQUITY = 4
    INFLATION = 5
    ERET = 6
    T = 7
    EMERGENCY_MIN = 8
    ASSETS = 9


class RetirementSettings:
    def __init__(self, expendature, emergency, fixed, equity, inflation, eret, t, emergency_min, assets):
        self.expendature = expendature
        self.emergency = emergency
        self.fixed = fixed
        self.equity = equity
        self.inflation = inflation
        self.eret = eret
        self.t = t
        self.emergency_min = emergency_min
        self.assets = assets

    def update_val(self, rsetting: RSetting, op: Callable[[Any], Any]):
        if rsetting == RSetting.EXPENDATURE:
            self.expendature = op(self.expendature)
        elif rsetting == RSetting.EMERGENCY:
            self.emergency = op(self.emergency)
        elif rsetting == RSetting.FIXED:
            self.fixed = op(self.fixed)
        elif rsetting == RSetting.EQUITY:
            self.equity = op(self.equity)
        elif rsetting == RSetting.INFLATION:
            self.inflation = op(self.inflation)
        elif rsetting == RSetting.ERET:
            self.eret = op(self.eret)
        elif rsetting == RSetting.T:
            self.t = op(self.t)
        elif rsetting == RSetting.EMERGENCY_MIN:
            self.emergency_min = op(self.emergency_min)
        elif rsetting == RSetting.ASSETS:
            self.assets = op(self.assets)

    def get_val(self, rsetting: RSetting):
        if rsetting == RSetting.EXPENDATURE:
            return self.expendature
        elif rsetting == RSetting.EMERGENCY:
            return self.emergency
        elif rsetting == RSetting.FIXED:
            return self.fixed
        elif rsetting == RSetting.EQUITY:
            return self.equity
        elif rsetting == RSetting.INFLATION:
            return self.inflation
        elif rsetting == RSetting.ERET:
            return self.eret
        elif rsetting == RSetting.T:
            return self.t
        elif rsetting == RSetting.EMERGENCY_MIN:
            return self.emergency_min
        elif rsetting == RSetting.ASSETS:
            return self.assets

    def current_value(self):
        return self.emergency + self.fixed + self.equity + sum(map(lambda a: a.value, self.assets))

    def copy(self) -> 'RetirementSettings':
        return RetirementSettings(self.expendature, self.emergency, self.fixed, self.equity,
                                  self.inflation, self.eret, self.t, self.emergency_min, self.assets)


def inflated_val(val: float, r: float, t: int):
    return val * ((1 + r)**t)


def inflated_payments(payment: float, r: float, t: int) -> float:
    total = 0
    for i in range(t):
        total += inflated_val(payment, r, i)
    return total


def retirement_value(retirementSettings: RetirementSettings) -> RetirementSettings:
    inflation_s = random.gauss(*retirementSettings.inflation)
    eret_s = random.gauss(*retirementSettings.eret)

    equity = (retirementSettings.equity -
              retirementSettings.expendature)
    fixed = retirementSettings.fixed
    emergency = retirementSettings.emergency
    if equity < 0:
        fixed += equity
        equity = 0
    elif retirementSettings.emergency_min is not None and emergency < retirementSettings.emergency_min:
        refill_emf = min(equity, retirementSettings.emergency_min - emergency)
        emergency += refill_emf
        equity -= refill_emf
    equity *= (1 + eret_s)
    if fixed < 0:
        emergency += fixed
        fixed = 0
    elif retirementSettings.emergency_min is not None and emergency < retirementSettings.emergency_min:
        refill_emf = min(fixed, retirementSettings.emergency_min - emergency)
        emergency += refill_emf
        fixed -= refill_emf
    # Assume fixed income assets simply keep pace with inflation
    fixed = retirementSettings.fixed * (1 + inflation_s)
    expendature = retirementSettings.expendature * (1 + inflation_s)

    new_rs = retirementSettings.copy()
    new_rs.update_val(RSetting.EXPENDATURE, lambda _: expendature)
    new_rs.update_val(RSetting.EMERGENCY, lambda _: emergency)
    new_rs.update_val(RSetting.FIXED, lambda _: fixed)
    new_rs.update_val(RSetting.EQUITY, lambda _: equity)

    if retirementSettings.t > 0:
        new_rs.update_val(RSetting.T, lambda t: t - 1)
        return retirement_value(new_rs)
    else:
        return new_rs


def simulate(retirementSettings: RetirementSettings, n: int) -> List[RetirementSettings]:
    results = []
    for _ in range(n):
        results.append(retirement_value(retirementSettings))
    return results


def worst_case(runs: List[RetirementSettings], pmin: float):
    """
    pmin = tail probablility, ie. 1/100 worst case
    """
    runs = sorted(runs, key=lambda rs: rs.emergency + rs.fixed + rs.equity)
    return runs[int(len(runs) * pmin)]


def optimize_r_var(retirementSettings: RetirementSettings, r_var_to_opt: RSetting, maximize: bool,
                   pmin: float) -> float:
    low = 0
    high = 100

    # Find top end of range
    retirementSettings.update_val(r_var_to_opt, lambda _: high)
    while (worst_case(simulate(retirementSettings, 10_000), pmin).current_value() - 
            retirementSettings.emergency_min < 0) ^ maximize:
        # TODO: Update low to previous high
        high = high * 2
        retirementSettings.update_val(r_var_to_opt, lambda _: high)

    diff = high
    while diff > 100:
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
    print(f"Emergency: ${retirementSettings.emergency:,.2f}")
    print(f"Fixed Income: ${retirementSettings.fixed:,.2f}")
    print(f"Equity: ${retirementSettings.equity:,.2f}")
    print(f"Inflation mean: {retirementSettings.inflation[0]*100:.2f}%")
    print(f"Inflation stdev: {retirementSettings.inflation[1]*100:.2f}%")
    print(f"Equity return mean: {retirementSettings.eret[0]*100:.2f}%")
    print(f"Equity return stdev: {retirementSettings.eret[1]*100:.2f}%")
    print(f"Years left: {retirementSettings.t}")


def safe_ret_expenditure_prompt():
    t = takeint("Whole number of remaining earning years from today", lbound=1)
    fixed = takefloat(
        "Enter current amount invested in fixed income assets ($)", lbound=0)
    equity = takefloat(
        "Enter current amount invested in equities ($)", lbound=0)
    expenditure = - \
        takefloat(
            "Enter expected annual equity contributions over this period (your yearly savings) ($)")
    inflation = (takefloat("Enter estimated mean inflation over this period", -1, 1),
                 takefloat("Enter estimated inflation standard deviation over this period", 0, 1))
    eret = (takefloat("Enter estimated mean equity return over this period", -1, 1),
            takefloat("Enter estimated equity return standard deviation over this period", 0, 1))

    print()
    wcp = takefloat(
        "Enter tail probability for Monte Carlo simulation (<0.5=worse than average result)", 0, 1)
    print("Simulating 10,000 possible scenarios...")
    runs = simulate(RetirementSettings(expenditure, 0, fixed, equity,
                    inflation, eret, t, 0, []), 10_000)
    retwealth = worst_case(runs, wcp).current_value()
    print(f"Estimated new worth at end of earning years: ${retwealth:,.2f}")

    print()
    t = takeint("Enter estimated whole number of years of retirement", lbound=1)
    emergency = takefloat(
        "Enter retirement emergency fund size", 0, int(retwealth))

    print()
    print("Binary searching possible retirement scenarios 10,000 times each...")
    maxexp = optimize_r_var(RetirementSettings(0, emergency, fixed, retwealth -
                            emergency - fixed, inflation, eret, t, emergency, []),
                            RSetting.EXPENDATURE, True, wcp)
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
        RetirementSettings(expenditure, 0, 0, 0, inflation, eret, t, 0, []), RSetting.EQUITY, False, wcp)
    print(f"Minimum safe equity savings for retirement: ${maxexp:,.2f}")


if __name__ == '__main__':
    prompt_fns = [("Calculate max expenditure in retirement", safe_ret_expenditure_prompt),
                  ("Calculate savings needed for retirement", savings_required_for_expenditure_prompt)]
    prompt_fn = choose(prompt_fns)
    if prompt_fn:
        prompt_fn()
