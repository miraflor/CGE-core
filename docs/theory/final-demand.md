# Households, Government and Investment

The standard model contains three final-demand blocks.

## Household demand

Households allocate disposable factor income across goods using calibrated Cobb-Douglas expenditure shares:

\[
X^p_i
=
\alpha_i
\frac{
\sum_h p^f_h FF_h-S^p-T^d
}{
p^q_i
}.
\]

## Government demand

Government consumption depends on tax revenue net of government saving:

\[
X^g_i
=
\mu_i
\frac{
T^d+\sum_iT^z_i+\sum_iT^m_i-S^g
}{
p^q_i
}.
\]

## Investment demand

Investment demand is allocated using fixed shares:

\[
X^v_i
=
\lambda_i
\frac{
S^p+S^g+\epsilon S^f
}{
p^q_i
}.
\]

Private and government saving are themselves defined as calibrated fractions of their respective income bases.

These equations mean that a policy shock can affect final demand indirectly through income, taxes, saving and prices even when the shock is applied somewhere else in the model.

## Follow this block

- **Economic interpretation:** this page
- **Full equation crosswalk:** {doc}`../MODEL`
- **Python model definition:** {doc}`../api/model-definitions`
- **Policy workflow:** {doc}`../getting-started/first-simulation`
