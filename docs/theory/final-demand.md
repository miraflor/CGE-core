# Households, Government and Investment

The standard model contains three final-demand blocks.

## Household demand

Households allocate disposable factor income across goods using calibrated Cobb-Douglas expenditure shares:

```{math}
X_i^p
=
\frac{\alpha_i}{p_i^q}
\left(
\sum_h p_h^f FF_h
-
S^p
-
T^d
\right).
```

## Government demand

Government consumption depends on tax revenue net of government saving:

```{math}
X_i^g
=
\frac{\mu_i}{p_i^q}
\left(
T^d
+
\sum_j T_j^z
+
\sum_j T_j^m
-
S^g
\right).
```

## Investment demand

Investment demand is allocated using fixed shares:

```{math}
X_i^v
=
\frac{\lambda_i}{p_i^q}
\left(
S^p
+
S^g
+
\varepsilon S^f
\right).
```

Private and government saving are themselves defined as calibrated fractions of their respective income bases:

```{math}
S^p
=
ss^p \sum_h p_h^f FF_h,
```

```{math}
S^g
=
ss^g
\left(
T^d
+
\sum_j T_j^z
+
\sum_j T_j^m
\right).
```

These equations mean that a policy shock can affect final demand indirectly through income, taxes, saving and prices even when the shock is applied somewhere else in the model.

## Follow this block

- **Economic interpretation:** this page
- **Full equation crosswalk:** {doc}`../MODEL`
- **Python model definition:** {doc}`../api/model-definitions`
- **Policy workflow:** {doc}`../getting-started/first-simulation`
