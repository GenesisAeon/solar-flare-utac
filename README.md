# solar-flare-utac

> GenesisAeon Package 22 — Solar Flare Magnetic Avalanches as UTAC System

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.19645351"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.19645351.svg" alt="DOI (GenesisAeon Whitepaper)"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="GPLv3 License"/></a>
  <a href="https://creativecommons.org/licenses/by/4.0/"><img src="https://img.shields.io/badge/docs-CC%20BY%204.0-lightblue.svg" alt="CC BY 4.0"/></a>
  <a href="https://github.com/GenesisAeon/genesis-os"><img src="https://img.shields.io/badge/part%20of-genesis--os-blueviolet" alt="Part of genesis-os"/></a>
  <img src="https://img.shields.io/badge/UTAC-package%2022-orange" alt="Package 22"/>
</p>
[![CI](https://github.com/genesisaeon/solar-flare-utac/actions/workflows/ci.yml/badge.svg)](https://github.com/genesisaeon/solar-flare-utac/actions/workflows/ci.yml)
[![Reference](https://img.shields.io/badge/Ref-A%26A%202026-red)](https://doi.org/10.1051/0004-6361/202449012)

**Solar flares modelled as magnetic UTAC avalanches** — calibrated against Solar Orbiter (2026), GOES X-ray data (1975–2026), and Velasco Herrera et al. (2026, JGR Space Physics).

**Key result**: Γ_solar ≈ 0.014 (ultra-low CREP) → most hair-trigger system in the atlas.

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

## Installation

```bash
pip install solar-flare-utac
# or
uv add solar-flare-utac
# development
pip install -e ".[dev]"
```

## Quickstart

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

## Integration in genesis-os

```python
from genesis_os import GenesisOS
os = GenesisOS()
solar = os.load_package(21)
results = solar.run_cycle(duration_hours=72)
print(f"Γ_solar = {results['crep_state']['Gamma']:.4f}")
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

## Benchmark

Validated against GOES catalog and Solar Orbiter data.

| Target | Value | Tolerance |
|---|---|---|
| Γ_solar | 0.014 | ±0.005 |
| X-class energy [J] | 10³² | log ±0.5 |
| Power-law index α | 1.8 | ±0.1 |
| Reconnection timescale | 10 min | ±30% |
| X-class flares/cycle | 150 | ±20% |

## Falsifiable Prediction

Next X5+ flare window in **2026 Q3** (southern hemisphere active region peak, per
Velasco Herrera 2026). Γ_solar will exceed θ_PT during this period. Testable
against GOES real-time monitoring at [SWPC](https://swpc.noaa.gov).

## References

- Solar Orbiter / A&A 2026 — magnetic avalanche mechanism
- Velasco Herrera et al. 2026, JGR Space Physics — 47-year superflare dataset
- Thoen Faber et al. 2025 — SST/CHROMIS high-resolution flare ribbons (140–200 km)
- ESA CryoSat + Swarm 2026 — X-class geomagnetic storm measurements

---

Part of the **GenesisAeon** cross-domain CREP criticality atlas.
Code: MIT · Docs & Data: CC BY 4.0 · seed=42 · numpy/scipy/matplotlib
