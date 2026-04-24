"""solar-flare-utac — GenesisAeon Package 21.

Solar flare magnetic avalanche threshold modelled as a UTAC dynamical system.

Central result
--------------
Γ_solar = arctanh(0.03) / 2.2 ≈ 0.014

Solar active regions occupy the ultra-sensitive (ultra-low CREP) end of the
GenesisAeon cross-domain criticality spectrum — explaining why solar flare
prediction is notoriously difficult.

Diamond-template contract
-------------------------
    SolarFlareUTAC.run_cycle()         → dict
    SolarFlareUTAC.get_crep_state()    → {C, R, E, P, Gamma}
    SolarFlareUTAC.get_utac_state()    → {H, dH_dt, H_star, K_eff}
    SolarFlareUTAC.get_phase_events()  → list[dict]
    SolarFlareUTAC.to_zenodo_record()  → dict
"""

from .system import SolarFlareUTAC
from .constants import GAMMA_SOLAR, SIGMA_CREP, SOLAR_TARGETS, PACKAGE_REGISTRY_ENTRY

__version__ = "0.1.0"
__author__ = "Johann Römer / MOR Research Collective"
__all__ = [
    "SolarFlareUTAC",
    "GAMMA_SOLAR",
    "SIGMA_CREP",
    "SOLAR_TARGETS",
    "PACKAGE_REGISTRY_ENTRY",
]
