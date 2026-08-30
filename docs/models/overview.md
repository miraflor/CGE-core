# Bundled models

CGE-Core v0.8 exposes four model families through model-specific façades.

| Model | Entry point | Primary role |
| --- | --- | --- |
| Simple CGE | `SimpleCGE` | Closed-economy teaching model |
| Standard CGE | `StandardCGE` | Open-economy policy analysis |
| IFPRI Standard CGE | `IFPRICGE` | Rich institutions and named macro-closure scenarios |
| CAMCGE | `CamCGE` | Published Cameroon replication |

They share the broad benchmark → scenario → result workflow where that is scientifically
appropriate, but retain separate equations, calibration logic, closure, and validation.
