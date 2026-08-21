# International Trade

The standard model distinguishes imported, domestically sold and exported goods.

## Armington demand

Domestic and imported varieties are imperfect substitutes:

\[
Q_i
=
\gamma_i
\left[
\delta^m_i M_i^{\eta_i}
+
\delta^d_i D_i^{\eta_i}
\right]^{1/\eta_i}.
\]

The relative prices of imports and domestic goods therefore influence how composite demand is divided between \(M_i\) and \(D_i\).

Import tariffs enter the import price faced inside the Armington demand system.

## CET transformation

Domestic output can be allocated between exports and domestic sales using a constant-elasticity-of-transformation relationship:

\[
Z_i
=
\theta_i
\left[
\xi^e_iE_i^{\phi_i}
+
\xi^d_iD_i^{\phi_i}
\right]^{1/\phi_i}.
\]

Relative export and domestic prices influence that allocation.

## Rest of the world

World prices are converted by the exchange rate:

\[
p^e_i=\epsilon p^{We}_i,
\qquad
p^m_i=\epsilon p^{Wm}_i.
\]

The balance-of-payments condition is:

\[
\sum_i p^{We}_iE_i+S^f
=
\sum_i p^{Wm}_iM_i.
\]

Together, these equations allow a tariff, world-price or external-balance shock to propagate through domestic production and demand.

## Follow this block

- **Economic interpretation:** this page
- **Full equation crosswalk:** {doc}`../MODEL`
- **Python model definition:** {doc}`../api/model-definitions`
- **Worked tariff experiment:** {doc}`../tutorials/tariff-reform`
