from dataclasses import dataclass,field


@dataclass(kw_only=True)
class Watch:
    name : str = 'abubakar'
    price : int =field(repr=False)
    brand : str

w2 = Watch(price=34433,brand=54)
print(w2)