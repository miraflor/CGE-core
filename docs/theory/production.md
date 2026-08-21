# Production and Factor Demand

In the standard model, production combines a composite of primary factors with intermediate inputs.

## Composite factor production

For good \(i\),

\[
Y_i=b_i\prod_h F_{h,i}^{\beta_{h,i}},
\]

where:

- \(Y_i\) is composite factor output;
- \(F_{h,i}\) is demand for factor \(h\);
- \(\beta_{h,i}\) is the calibrated factor share; and
- \(b_i\) is a scale parameter.

Cost minimisation implies factor demand:

\[
F_{h,i}
=
\beta_{h,i}\frac{p^y_iY_i}{p^f_h}.
\]

## Intermediate inputs

Intermediate demand is Leontief:

\[
X_{i,j}=a^x_{i,j}Z_j,
\]

and composite-factor demand is:

\[
Y_i=a^y_iZ_i.
\]

The zero-profit unit-cost condition is:

\[
p^z_j
=
a^y_jp^y_j+\sum_i a^x_{i,j}p^q_i.
\]

These relationships correspond to `eqpy`, `eqF`, `eqX`, `eqY`, and `eqpzs` in the standard model implementation.
