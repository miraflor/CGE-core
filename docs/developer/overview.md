# Developer reference

CGE-Core v0.7 has three extension levels.

1. **Use a bundled model façade** when the economics already match the question.
2. **Functional Python authoring** for a new model without requiring inheritance from a
   CGE-Core base class.
3. **Lower-level engine/model-definition work** when extending the validated PyCGE-style
   architecture.

The experimental `.cge.md` format is intentionally limited and is not the implementation
language of the validated bundled models.

Compatibility is a deliberate boundary: the v0.6 `CGE` lifecycle and lower-level engine
remain available even though practitioner documentation now starts one level higher.
