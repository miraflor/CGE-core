# Two-good exchange equilibrium

This file demonstrates the experimental CGE-Core model specification. This prose is documentation only and does not affect the executable model.

```cge
set goods = [FOOD, MFG]

param alpha[FOOD] = 0.5
param alpha[MFG] = 0.5
param endowment[FOOD] = 60
param endowment[MFG] = 40

var p[i in goods] > 0
var q[i in goods] >= 0

equation demand_food:
    q[FOOD] = alpha[FOOD] * (p[FOOD] * endowment[FOOD] + p[MFG] * endowment[MFG]) / p[FOOD]
equation demand_mfg:
    q[MFG] = alpha[MFG] * (p[FOOD] * endowment[FOOD] + p[MFG] * endowment[MFG]) / p[MFG]
equation market_food:
    q[FOOD] = endowment[FOOD]
equation market_mfg:
    q[MFG] = endowment[MFG]

fix p[FOOD] = 1
drop market_food
shockable endowment
```

At the equilibrium, the fixed FOOD price is the numeraire. Walras' law makes one market equation redundant, so `market_food` is explicitly dropped.
