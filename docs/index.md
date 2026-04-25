# solar-flare-utac

**GenesisAeon Package 21** — Solar Flare Magnetic Avalanche Threshold

[![CI](https://github.com/genesisaeon/solar-flare-utac/actions/workflows/ci.yml/badge.svg)](https://github.com/genesisaeon/solar-flare-utac/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../LICENSE)

Models **solar flare onset as a magnetic-field UTAC phase transition**.

## Central Result

> **Γ_solar = arctanh(0.03) / 2.2 ≈ 0.014**

Solar active regions occupy the **ultra-sensitive** (ultra-low CREP) end of the
GenesisAeon cross-domain criticality atlas.

## Quick Start

```bash
pip install solar-flare-utac
```

```python
from solar_flare_utac import SolarFlareUTAC

model = SolarFlareUTAC(seed=42)
state = model.run_cycle(duration_hours=72)

print(state['crep_state'])   # {C, R, E, P, Gamma ≈ 0.014}
print(state['utac_state'])   # {H, dH_dt, H_star, K_eff}
```

## CREP Criticality Spectrum

| Domain | Γ | η | Character |
|---|---|---|---|
| **Solar Flare (P21)** | **0.014** | **1%** | **Ultra-sensitive** |
| Cygnus X-1 Jet | 0.046 | 5% | Hair-trigger |
| Amazon Rainforest | 0.116 | 12% | Fragile |
| AMOC Ocean | 0.251 | 50% | Homeostatic |
| Neural Criticality | 0.251 | 50% | Homeostatic (!) |
| BTW Sandpile | 0.296 | 58% | Robust SOC |

## Diamond-Template Contract

```python
model.run_cycle(duration_hours=72)  → dict
model.get_crep_state()              → {C, R, E, P, Gamma}
model.get_utac_state()              → {H, dH_dt, H_star, K_eff}
model.get_phase_events()            → list[dict]
model.to_zenodo_record()            → dict
```
