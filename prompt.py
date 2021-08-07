from typing import *

T = TypeVar('T')

def choose(opts: List[Tuple[str, T]]) -> T:
    if len(opts) == 0:
        return None
    elif len(opts) == 1:
        return opts[0][1]

    for i, o in enumerate(opts):
        print(f"{i}. {o}")

    s = input("Choose an option: ")
    while True:
        try:
            idx = int(s)
            if idx < len(opts) and idx > 0:
                return opts[idx][1]
        except:
            pass

        s = input("Invalid input, please input a number in the list")

def takeint(prompt, lbound: float = None, ubound: float = None) -> int:
    slb = lbound if lbound is not None else "-inf"
    sub = ubound if ubound is not None else "inf"

    s = input(f"{prompt} [{slb},{sub}]: ")
    while True:
        try:
            i = int(s)
            if lbound is None or i >= lbound:
                if ubound is None or i <= ubound:
                    return i

            s = input(f"Not within bounds [{slb},{sub}]\nEnter a valid integer: ")
        except:
            s = input("Not a valid integer\nEnter a valid integer: ")

def takefloat(prompt, lbound: float = None, ubound: float = None) -> float:
    slb = lbound if lbound is not None else "-inf"
    sub = ubound if ubound is not None else "inf"

    s = input(f"{prompt} [{slb},{sub}]: ")
    while True:
        try:
            f = float(s)
            if lbound is None or f >= lbound:
                if ubound is None or f <= ubound:
                    return f
            
            s = input(f"Not within bounds [{slb},{sub}]\nEnter a valid float: ")
        except:
            s = input("Not a valid float\nEnter a valid float: ")