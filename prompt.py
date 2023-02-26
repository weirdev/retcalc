from typing import List, Optional, Tuple, TypeVar

T = TypeVar('T')

def choose(opts: List[Tuple[str, T]]) -> T:
    assert len(opts) != 0

    if len(opts) == 1:
        return opts[0][1]

    for i, o in enumerate(opts):
        print(f"{i}. {o[0]}")

    s = input("Choose an option: ")
    while True:
        try:
            idx = int(s)
            if idx < len(opts) and idx >= 0:
                return opts[idx][1]
        except:
            pass

        s = input("Invalid input, please input a number in the list")

def takebool(prompt: str) -> bool:
    prompt = f"{prompt} [y/n]: "
    while True:
        s = input(prompt)
        try:
            resp = s.strip().lower()
            if resp == "y" or resp == "n" or resp == "yes" or resp == "no":
                return "y" == resp[0]
        except:
            pass

def takeint(prompt: str, lbound: Optional[float] = None, ubound: Optional[float] = None) -> int:
    slb = lbound if lbound is not None else "-inf"
    sub = ubound if ubound is not None else "inf"

    s = input(f"{prompt} [{slb},{sub}]: ")
    while True:
        try:
            i = int(s.strip())
            if lbound is None or i >= lbound:
                if ubound is None or i <= ubound:
                    return i

            s = input(f"Not within bounds [{slb},{sub}]\nEnter a valid integer: ")
        except:
            s = input("Not a valid integer\nEnter a valid integer: ")

def takefloat(prompt: str, lbound: Optional[float] = None, ubound: Optional[float] = None) -> float:
    slb = lbound if lbound is not None else "-inf"
    sub = ubound if ubound is not None else "inf"

    s = input(f"{prompt} [{slb},{sub}]: ")
    while True:
        try:
            f = float(s.strip())
            if lbound is None or f >= lbound:
                if ubound is None or f <= ubound:
                    return f
            
            s = input(f"Not within bounds [{slb},{sub}]\nEnter a valid float: ")
        except:
            s = input("Not a valid float\nEnter a valid float: ")