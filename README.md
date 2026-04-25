# solar-flare-utac

**GenesisAeon Package 21** — Solar Flare Magnetic Avalanche Threshold

[![CI](https://github.com/genesisaeon/solar-flare-utac/actions/workflows/ci.yml/badge.svg)](https://github.com/genesisaeon/solar-flare-utac/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19645351.svg)](https://doi.org/10.5281/zenodo.19645351)

Models **solar flare onset as a magnetic-field UTAC phase transition**, calibrated
against Solar Orbiter (2026), GOES X-ray data (1975–2026), and
Velasco Herrera et al. (2026, JGR Space Physics).

---

## Central Result

> **Γ_solar = arctanh(0.03) / 2.2 ≈ 0.014**

Solar active regions occupy the **ultra-sensitive** (ultra-low CREP) end of the
GenesisAeon cross-domain criticality spectrum — the lowest Γ of any system in the
atlas.  Tiny CREP fluctuations produce giant energy releases, explaining why
deterministic solar flare prediction is so notoriously difficult.

### CREP Criticality Spectrum

| Domain | Package | Γ | η | Character |
|---|---|---|---|---|
| **Solar Flare** | **P21** | **0.014** | **1%** | **Ultra-sensitive** |
| Cygnus X-1 Jet | P17 | 0.046 | 5% | Hair-trigger |
| Amazon Rainforest | P19 | 0.116 | 12% | Fragile |
| AMOC Ocean | P18 | 0.251 | 50% | Homeostatic |
| Neural Criticality | P20 | 0.251 | 50% | Homeostatic (!) |
| BTW Sandpile | P22 | 0.296 | 58% | Robust SOC |
| Manna Sandpile | P22 | 0.376 | 72% | Dense SOC |
| ERA5 Arctic | P01 | 0.920 | 99% | Near-saturated |

---

## Physical Mapping to UTAC

| UTAC symbol | Solar quantity |
|---|---|
| H(t) | Normalised magnetic free energy ∈ [0, 1] |
| K | E_max ≈ 10³² J (active region energy ceiling) |
| H* | Quiescent fixed point ≈ 0.10 K |
| r | Flux-emergence buildup rate ≈ 0.06 hr⁻¹ |
| σ | CREP coupling = 2.2 |
| Γ(t) | CREP tensor (C, R, E, P) → Γ_solar ≈ 0.014 |

**Flare trigger:** when H > H_threshold = 0.60 AND Γ > θ_PT ≈ 0.014, the
magnetic current sheet becomes unstable → reconnection cascade → "magnetic
avalanche" (Solar Orbiter A&A 2026).

---

## Install

```bash
pip install solar-flare-utac
# or
uv add solar-flare-utac
```

## Quick Start

```python
from solar_flare_utac import SolarFlareUTAC

model = SolarFlareUTAC(seed=42)
state  = model.run_cycle(duration_hours=72)

print(state['crep_state'])    # {C, R, E, P, Gamma}
print(state['utac_state'])    # {H, dH_dt, H_star, K_eff}
print(state['flare_count'])   # flares in this cycle

window = model.predict_flare_window(horizon_days=3)
record = model.to_zenodo_record()
```

## CLI

```bash
# Run a 72-hour simulation cycle
solar-utac run --duration 72 --active-region AR3000

# Flare probability window forecast
solar-utac flare-window --horizon 7

# Print the full CREP Criticality Spectrum
solar-utac gamma-crep-spectrum

# Validate against benchmark targets
solar-utac benchmark

# Export Zenodo metadata record
solar-utac zenodo-export
```

## Diamond-Template Contract

All GenesisAeon packages implement the same five-method interface:

```python
model.run_cycle(duration_hours=72)  → dict
model.get_crep_state()              → {C, R, E, P, Gamma}
model.get_utac_state()              → {H, dH_dt, H_star, K_eff}
model.get_phase_events()            → list[dict]   # each flare = one event
model.to_zenodo_record()            → dict
```

## Repository Structure

```
solar-flare-utac/
├── src/solar_flare_utac/
│   ├── system.py          # SolarFlareUTAC — Diamond interface + Ethics Gate
│   ├── active_region.py   # Magnetic free energy ODE (UTAC)
│   ├── reconnection.py    # Reconnection instability threshold (Syrovatsky)
│   ├── crep_solar.py      # Solar CREP tensor (C, R, E, P → Γ)
│   ├── goes_loader.py     # GOES X-ray flux loader + synthetic generator
│   ├── superflare.py      # Power-law flare statistics (SOC)
│   ├── geomagnetic.py     # Dst storm impact model
│   ├── benchmark.py       # Validation vs. GOES catalog + Orbiter
│   ├── cli.py             # Typer CLI
│   └── constants.py       # All physical and model constants
├── data/
│   ├── goes_xray_annual_stats.yaml
│   └── flare_catalog_summary.yaml
├── notebooks/
│   ├── 01_solar_utac_overview.ipynb
│   ├── 02_goes_crep_analysis.ipynb
│   ├── 03_flare_cascade.ipynb
│   └── 04_gamma_solar_calibration.ipynb
└── tests/
    ├── test_diamond_interface.py
    ├── test_active_region.py
    ├── test_reconnection.py
    └── test_superflare.py
```

## Benchmark Targets

| Target | Value | Tolerance |
|---|---|---|
| Γ_solar | 0.014 | ±0.005 |
| X-class energy [J] | 10³² | log ±0.5 |
| Power-law index α | 1.8 | ±0.1 |
| Reconnection timescale | 10 min | ±30% |
| X-class flares/cycle | 150 | ±20% |

## Falsifiable Prediction

UTAC predicts the next X5+ flare window: **2026 Q3** (southern hemisphere active
region peak, per Velasco Herrera 2026).  Γ_solar will exceed θ_PT during this
period.  Testable against GOES real-time monitoring at [SWPC](https://swpc.noaa.gov).

## References

- Solar Orbiter / A&A 2026 — magnetic avalanche mechanism
- Velasco Herrera et al. 2026, JGR Space Physics — 47-year superflare dataset
- Thoen Faber et al. 2025 — SST/CHROMIS high-resolution flare ribbons (140–200 km)
- ESA CryoSat + Swarm 2026 — X-class geomagnetic storm measurements

---

Part of the **GenesisAeon** cross-domain CREP criticality atlas.
MIT licence · seed=42 · numpy/scipy/matplotlib
