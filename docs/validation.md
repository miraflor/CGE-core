# Validation and provenance

CGE-Core distinguishes **software convenience** from **scientific validation**.

## Hosoe simple and standard

The v0.6 scientific baseline established benchmark replication for the Hosoe implementations. The standard model also reproduced the published tariff-abolition counterfactual and was checked with independent root-finding/multi-start evidence. v0.7 does not intentionally alter those equations.

## CAMCGE

The CAMCGE validation material checks the published 1987 objective (`omega`), 98 reported variable levels, the current-account residual on the dropped equation, and three published experiments. v0.7 makes that existing implementation reachable from an installed wheel; packaging is not a new economic validation claim.

## IFPRI

Two evidence lanes must remain separate:

1. **Redistributable synthetic economy.** Independently authored, included in the package, suitable for CI and exercising the IFPRI-format code path.
2. **Official-source replication.** Requires separately supplied licensed source material. The synthetic economy does not replace or strengthen that external-source claim.

## Release rule

Architectural refactors must not be used as an excuse to loosen tolerances or silently change validated equations. If a future release changes equations, calibration, closure, or scientific targets, that must be stated as a scientific change and validated separately.
