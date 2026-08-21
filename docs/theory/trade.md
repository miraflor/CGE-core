# International Trade

The standard model distinguishes imported, domestically sold and exported goods.

## Armington demand

Domestic and imported varieties are imperfect substitutes:

```{math}
Q_i
=
\gamma_i
\left[
\delta_i^m M_i^{\eta_i}
+
\delta_i^d D_i^{\eta_i}
\right]^{1/\eta_i}.
```

The relative prices of imports and domestic goods therefore influence how composite demand is divided between $M_i$ and $D_i$.

The import first-order condition is:

```{math}
M_i
=
\left[
\frac{
\gamma_i^{\eta_i}\delta_i^m p_i^q
}{
(1+\tau_i^m)p_i^m
}
\right]^{1/(1-\eta_i)}
Q_i.
```

Import tariffs therefore enter through the tariff-inclusive import-price wedge.

## CET transformation

Domestic output can be allocated between exports and domestic sales using a constant-elasticity-of-transformation relationship:

```{math}
Z_i
=
\theta_i
\left[
\xi_i^e E_i^{\phi_i}
+
\xi_i^d D_i^{\phi_i}
\right]^{1/\phi_i}.
```

The corresponding export-supply condition is:

```{math}
E_i
=
\left[
\frac{
\theta_i^{\phi_i}\xi_i^e(1+\tau_i^z)p_i^z
}{
p_i^e
}
\right]^{1/(1-\phi_i)}
Z_i.
```

Relative export and domestic prices influence the allocation of output between export and domestic markets.

## Rest of the world

World prices are converted into local-currency prices by the exchange rate:

```{math}
p_i^e
=
\varepsilon p_i^{We},
\qquad
p_i^m
=
\varepsilon p_i^{Wm}.
```

The balance-of-payments condition is:

```{math}
\sum_i p_i^{We}E_i
+
S^f
=
\sum_i p_i^{Wm}M_i.
```

Together, these equations allow a tariff, world-price or external-balance shock to propagate through domestic production and demand.

## Follow this block

- **Economic interpretation:** this page
- **Full equation crosswalk:** {doc}`../MODEL`
- **Python model definition:** {doc}`../api/model-definitions`
- **Worked tariff experiment:** {doc}`../tutorials/tariff-reform`
