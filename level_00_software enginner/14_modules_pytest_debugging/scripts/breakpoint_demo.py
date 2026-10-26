"""
C.3 breakpoint() / pdb: code ko rok kar andar dekhna (INTERACTIVE)
==================================================================
    python -m scripts.breakpoint_demo

Program breakpoint() par ruk kar (Pdb) prompt de ga. Ye try karein:
    p price                 <- variable ki value
    p discount_percent
    p price * discount_percent
    l                       <- aas paas ka code
    w                       <- abhi kahan hoon (stack)
    n                       <- agli line
    c                       <- aage chalao (continue)
    q                       <- band

Theory: NOTES_C_debugging.md (C.3)
"""


def apply_discount(price, discount_percent):
    breakpoint()                     # <- yahan ruke ga
    result = price - price * discount_percent
    return result


print("Result:", apply_discount(1000, 10))
