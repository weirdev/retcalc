from prompt import takefloat, takeint
import random

def inflated_val(val, r, t):
    return val * ((1 + r)**t)

def inflated_payments(payment, r, t):
    total = 0
    for i in range(t):
        total += inflated_val(payment, r, i)
    return total
    

def retirement_value(expendature, emergency, fixed, equity, inflation, eret, t):
    inflation_s = random.gauss(*inflation)
    eret_s = random.gauss(*eret)
    equity = (equity - expendature) * (1  + eret_s)
    expendature = expendature * (1 + inflation_s)
    fixed = fixed * (1 + inflation[0])

    if t > 0:
        return retirement_value(expendature, emergency, fixed, equity, inflation, eret, t - 1)
    else:
        return (expendature, emergency, fixed, equity, inflation, eret, t)
    

def simulate(rconfig, n):
    results = []
    for _ in range(n):
        results.append(retirement_value(*rconfig))
    return results

"""
pmin = tail probablility, ie. 1/100 worst case
"""
def worst_case(runs, pmin):
    runs = sorted(runs, key=lambda x: x[1] + x[2] + x[3])
    return runs[int(len(runs) * pmin)]


def max_expendature(rconfig, pmin):
    rconfig = list(rconfig)
    low = 0
    high = 1000

    rconfig[0] = high
    while worst_case(simulate(rconfig, 10_000), pmin)[3] > 0:
        high = high * 2
        rconfig[0] = high

    diff = high
    while diff > 100:
        mid = low + (diff / 2)
        rconfig[0] = mid
        if worst_case(simulate(rconfig, 10_000), pmin)[3] < 0:
            high = mid
        else:
            low = mid
        diff = high - low

    return high
    

def r_val_print(expendature, emergency, fixed, equity, inflation, eret, t):
    print(f"Expendature: ${expendature:,.2f}")
    print(f"Emergency: ${emergency:,.2f}")
    print(f"Fixed Income: ${fixed:,.2f}")
    print(f"Equity: ${equity:,.2f}")
    print(f"Inflation mean: {inflation[0]*100:.2f}%")
    print(f"Inflation stdev: {inflation[1]*100:.2f}%")
    print(f"Equity return mean: {eret[0]*100:.2f}%")
    print(f"Equity return stdev: {eret[1]*100:.2f}%")
    print(f"Years left: {t}")
        
    
        
if __name__ == '__main__':
    t = takeint("Whole number of remaining earning years from today", lbound=1)
    fixed = takefloat("Enter current amount invested in fixed income assets ($)", lbound=0)
    equity = takefloat("Enter current amount invested in equities ($)", lbound=0)
    expendature = -takefloat("Enter expected annual equity contributions over this period (your yearly savings) ($)")
    inflation = (takefloat("Enter estimated mean inflation over this period", -1, 1), 
                 takefloat("Enter estimated inflation standard deviation over this period", 0, 1))
    eret = (takefloat("Enter estimated mean equity return over this period", -1, 1),
            takefloat("Enter estimated equity return standard deviation over this period", 0, 1))

    print()
    wcp = takefloat("Enter tail probability for Monte Carlo simulation (<0.5=worse than average result)", 0, 1)
    print("Simulating 10,000 possible scenarios...")
    runs = simulate((expendature, 0, fixed, equity, inflation, eret, t), 10_000)
    retwealth = sum(worst_case(runs, wcp)[1:4])
    print(f"Estimated new worth at end of earning years: ${retwealth:,.2f}")

    print()
    t = takeint("Enter estimated whole number of years of retirement", lbound=1)
    emergency = takefloat("Enter retirement emergency fund size", 0, int(retwealth))

    print()
    print("Binary searching possible retirement scenarios 10,000 times each...")
    maxexp = max_expendature((None, emergency, fixed, retwealth - emergency - fixed, inflation, eret, t), wcp)
    print(f"Maximum safe yearly expendature in retirement: ${maxexp:,.2f}")