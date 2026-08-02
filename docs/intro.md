# CGE-Core

A Pyomo-based computable general equilibrium framework faithful to the
textbook by Hosoe, Gasawa & Hashimoto (2010), with documentation in the
style of [OG-Core](https://github.com/PSLmodels/OG-Core) (DeBacker &
Evans).

CGE-Core separates **model definition** (the algebraic structure, one
Pyomo `AbstractModel` per model, every equation documented with its
math and its GAMS Model Library equation name) from **model workflow**
(calibration, reform, counterfactual solution, comparison — the
`PyCGE` engine). Two reference models ship with the package:

| Model    | Hosoe ch. | Description                                          |
| -------- | --------- | ---------------------------------------------------- |
| `splcge` | 3–4       | Simple closed economy: 2 goods, 2 factors            |
| `stdcge` | 5–6       | Open economy: Armington, CET, government, investment |

Both are verified 1:1 ports of the GAMS Model Library files
`splcge.gms` (SEQ=275) and `stdcge.gms` (SEQ=276), guarded by a
regression suite that runs the real IPOPT solver in CI.

## Where to start

- **{doc}`workflow`** — install, quick start, the engine API, and how
  to load your own SAM.
- **{doc}`MODEL`** — the standard model equation by equation: the
  crosswalk to the GAMS source, the closure, degrees of freedom, and
  calibration.
- **{doc}`OG_CORE_CROSSWALK`** — if you know OG-Core, this maps its
  concepts, files, and workflow onto CGE-Core.

## Provenance

CGE-Core is a corrected and annotated fork of
[PyCGE](https://github.com/juanfung/pycge) by Juan Fung and Charley
Burtwistle (U.S. National Institute of Standards and Technology, 2017;
public domain under 17 U.S.C. 105). The fork is maintained by James
Matthew Miraflor, whose revisions were produced through an AI-assisted
("vibecoded") workflow he directed and reviewed; **the underlying model
port is not his original work**. Fork modifications are MIT-licensed.
See the repository `README.md` for citation entries and `CITATION.cff`
for machine-readable metadata.
