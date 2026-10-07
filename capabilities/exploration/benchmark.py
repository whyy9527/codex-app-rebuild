"""Explicit, reproducible packing instances; validation never drives selection."""
import random
from capabilities.exploration.ledger import digest


def case_key(case):
    weights,capacity=case
    return digest({'weights':sorted(weights),'capacity':capacity})


def split_cases(*,seed,count=8):
    if isinstance(seed,bool) or not isinstance(seed,int): raise ValueError('integer seed required')
    if isinstance(count,bool) or not isinstance(count,int) or not 1<=count<=100: raise ValueError('count in [1,100] required')
    randomizer=random.Random(seed)
    seen=set()
    groups={}
    for split in ('training','validation'):
        cases=[]
        while len(cases)<count:
            size=randomizer.randint(10,16)
            case=([randomizer.randint(18,79) for i in range(size)],100)
            identifier=case_key(case)
            if identifier in seen: continue
            seen.add(identifier)
            cases.append(case)
        groups[split]=cases
    return groups
