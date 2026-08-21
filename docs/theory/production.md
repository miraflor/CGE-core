# Production and Factor Demand

In the standard model, production combines a composite of primary factors with intermediate inputs.

## Composite factor production

For good $i$,

```{math}
Y_i
=
b_i \prod_h F_{h,i}^{\beta_{h,i}}.
```

Here:

- $Y_i$ is composite factor output;
- $F_{h,i}$ is demand for factor $h$;
- $\beta_{h,i}$ is the calibrated factor share; and
- $b_i$ is a scale parameter.

Cost minimisation implies factor demand:

```{math}
F_{h,i}
=
\frac{\beta_{h,i}\,p_i^y\,Y_i}{p_h^f}.
```

## Intermediate inputs

Intermediate demand is Leontief:

```{math}
X_{i,j}
=
a^x_{i,j} Z_j,
```

and composite-factor demand is:

```{math}
Y_i
=
a_i^y Z_i.
```

The zero-profit unit-cost condition is:

```{math}
p_j^z
=
a_j^y p_j^y
+
\sum_i a^x_{i,j} p_i^q.
```

These relationships correspond to `eqpy`, `eqF`, `eqX`, `eqY`, and `eqpzs` in the standard model implementation.

## Follow this block

- **Economic interpretation:** this page
- **Full equation crosswalk:** {doc}`../MODEL`
- **Python model definition:** {doc}`../api/model-definitions`
- **Where it sits in the whole system:** {doc}`../architecture`
