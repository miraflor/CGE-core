# Experimental `.cge.md`

> **Experimental model specification — syntax may evolve before 1.0.**

A `.cge.md` file combines explanation and a formal model specification. The crucial rule is simple:

> **Markdown prose never controls computation.**

Only fenced blocks marked `cge` are parsed. No LLM infers an omitted equation, closure choice, or parameter from prose.

## MVP grammar

```text
set goods = [FOOD, MFG]
param alpha[FOOD] = 0.5
var p[i in goods] > 0

equation some_equation:
    left_hand_side = right_hand_side

fix p[FOOD] = 1
drop redundant_equation
shockable alpha
```

Expressions support numeric constants, Python-style identifiers (`letters`, `digits`, `_`), one- or multi-dimensional indexing, arithmetic, powers, and `sum(i in set, expression)` / `prod(i in set, expression)`. Set members also use grammar-0 identifiers in this first version; quoted/string-valued members are not yet supported. Equation declarations use exactly one standalone `=`; comparison operators such as `>=` and `==` are rejected with a source-located diagnostic. Parameter-only identities are rejected because they are data checks, not equilibrium constraints.

Strict variable bounds (`>` / `<`) are represented by the nearest floating-point value inside the open interval using `math.nextafter`, avoiding a fixed absolute epsilon that changes meaning with scale.

External data can be declared as a provenance-bearing reference:

```text
data SAM = "sam.csv"
```

Grammar version 0 does not silently interpret arbitrary CSVs as model semantics; richer data bindings can be added explicitly in later grammar versions.

## Validate

```bash
cge check examples/custom_markdown_model/two_good_exchange.cge.md
```

Errors carry file/line locations.

## Solve

```bash
cge solve examples/custom_markdown_model/two_good_exchange.cge.md
```

The first compiler target is intentionally small. StandardCGE, CAMCGE and IFPRI are **not** rewritten in this DSL merely to prove that the language exists.
