"""Explicit economic metadata for CGE-Core model families.

v0.8.0 keeps economic meaning out of spelling conventions.  Public model
families carry an explicit ModelSpec describing closure, benchmark-only data,
base-protected quantities, semantic shocks, and required data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

ClosureTarget = Tuple[str, Any]


@dataclass(frozen=True)
class ModelSpec:
    """Internal metadata contract shared by public model adapters."""

    name: str
    family: str
    default_numeraire: Optional[ClosureTarget] = None
    default_redundant: Optional[ClosureTarget] = None
    benchmark_only: frozenset[str] = field(default_factory=frozenset)
    base_protected: frozenset[str] = field(default_factory=frozenset)
    required_data: frozenset[str] = field(default_factory=frozenset)
    semantic_shocks: Mapping[str, str] = field(default_factory=dict)
    validation_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "semantic_shocks", MappingProxyType(dict(self.semantic_shocks)))
        object.__setattr__(
            self, "validation_metadata", MappingProxyType(dict(self.validation_metadata))
        )

    @property
    def closure(self) -> Mapping[str, Optional[ClosureTarget]]:
        return MappingProxyType({
            "numeraire": self.default_numeraire,
            "dropped_equation": self.default_redundant,
        })


# These names are explicit economic declarations for the validated Hosoe
# implementations.  They are not derived at runtime from a trailing "0".
_STANDARD_BENCHMARK_ONLY = frozenset({
    "sam", "Td0", "Tz0", "Tm0", "F0", "Y0", "X0", "Z0", "M0",
    "Xp0", "Sp0", "Xg0", "Sg0", "Xv0", "E0", "Q0", "D0",
})

_SIMPLE_BENCHMARK_ONLY = frozenset({
    "sam", "X0", "F0", "Z0",
})

_CAM_BENCHMARK_ONLY = frozenset({
    "gr0", "cdtot0", "wa0", "mps0", "tm0", "m0", "e0", "xd0",
    "pd0", "pm0", "pe0", "pwe0", "pva0", "xxd0", "dst0", "id0",
    "ls0", "x0", "int0", "y0",
})

SIMPLE_SPEC = ModelSpec(
    name="SimpleCGE",
    family="Hosoe simple CGE",
    default_numeraire=("pf", "LAB"),
    default_redundant=("eqpf", "LAB"),
    benchmark_only=_SIMPLE_BENCHMARK_ONLY,
    base_protected=frozenset({"FF"}),
    required_data=frozenset({
        "set-i-.csv", "set-h-.csv", "set-u-.csv", "param-sam-.csv"
    }),
    semantic_shocks={"endowment": "FF"},
    validation_metadata={"reference": "Hosoe, Gasawa & Hashimoto"},
)

STANDARD_SPEC = ModelSpec(
    name="StandardCGE",
    family="Hosoe standard CGE",
    default_numeraire=("pf", "LAB"),
    default_redundant=("eqpf", "LAB"),
    benchmark_only=_STANDARD_BENCHMARK_ONLY,
    base_protected=frozenset({"FF"}),
    required_data=frozenset({
        "set-i-.csv", "set-h-.csv", "set-u-.csv", "param-sam-.csv"
    }),
    semantic_shocks={
        "tariff": "taum",
        "production_tax": "tauz",
        "endowment": "FF",
    },
    validation_metadata={
        "reference": "Hosoe, Gasawa & Hashimoto standard CGE",
        "canonical_validation": "benchmark and tariff-abolition replication",
    },
)

CAM_SPEC = ModelSpec(
    name="CamCGE",
    family="CAMCGE Cameroon 1987",
    default_numeraire=("mps", None),
    default_redundant=("caeq", None),
    benchmark_only=_CAM_BENCHMARK_ONLY,
    validation_metadata={
        "reference": "CAMCGE published 1987 base and three experiments",
        "published_objective": 191.7346,
    },
)

IFPRI_SPEC = ModelSpec(
    name="IFPRICGE",
    family="IFPRI Standard CGE",
    validation_metadata={
        "synthetic_status": "redistributable independently authored demonstration economy",
        "official_status": "official-source replication requires separately supplied licensed material",
    },
)
