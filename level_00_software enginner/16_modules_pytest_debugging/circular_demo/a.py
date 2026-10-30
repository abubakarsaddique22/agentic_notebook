# A.9 Circular import demo: a.py -> b.py -> a.py
# Chalayein (circular_demo folder ke ANDAR se):   python a.py
from b import helper_b


def helper_a():
    return "A"


print(helper_b())
