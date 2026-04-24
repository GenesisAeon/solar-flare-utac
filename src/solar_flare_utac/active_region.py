"""Magnetic active-region energy model.

The active region stores magnetic free energy H(t) ∈ [0, 1] (normalised
to E_max).  Energy is supplied by photospheric flux emergence and removed
either by quiescent coronal dissipation or explosive reconnection.

ODE (UTAC form):
    dH/dt = r_build * (1 - H) - λ(H, Γ) * H

where λ(H, Γ) is the CREP-gated reconnection rate supplied by
:class:`~solar_flare_utac.reconnection.ReconnectionThreshold`.
"""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .constants import (
    E_MAX_J,
    H_STAR_QUIET,
    H_THRESHOLD,
    LAMBDA_QUIET,
    R_BUILDUP,
    RELAXATION_TAU_HOURS,
    SEED,
    SIGMA_CREP,
)


class MagneticActiveRegion:
    """Model the magnetic free energy H(t) of a solar active region.

    Parameters
    ----------
    r_buildup : float
        Flux-emergence energy buildup rate [hr⁻¹].
    h_init : float
        Initial normalised free energy H₀ ∈ [0, 1].
    seed : int
        Random seed for stochastic flux fluctuations.
    """

    def __init__(
        self,
        r_buildup: float = R_BUILDUP,
        h_init: float = H_STAR_QUIET,
        seed: int = SEED,
    ) -> None:
        self.r_buildup = r_buildup
        self.H = float(np.clip(h_init, 0.0, 1.0))
        self.rng = np.random.default_rng(seed)
        self._history: list[float] = [self.H]
        self._time_hours: float = 0.0
        self._flare_count: int = 0
        self._last_flare_energy_J: float = 0.0

    # ── ODE right-hand side ────────────────────────────────────────────────────

    def dH_dt(self, H: float, lambda_reconnect: float) -> float:
        """Time derivative dH/dt given current reconnection rate λ.

        Parameters
        ----------
        H : float
            Current normalised free energy.
        lambda_reconnect : float
            CREP-gated reconnection dissipation rate [hr⁻¹].
        """
        return self.r_buildup * (1.0 - H) - lambda_reconnect * H

    # ── single timestep integration (RK4) ─────────────────────────────────────

    def step(
        self,
        dt_hours: float,
        lambda_reconnect: float,
        noise_sigma: float = 0.002,
    ) -> dict:
        """Advance H by dt_hours using 4th-order Runge–Kutta + small noise.

        Returns
        -------
        dict with keys: H_new, dH_dt, flare_triggered, energy_released_J
        """
        H0 = self.H

        k1 = self.dH_dt(H0, lambda_reconnect)
        k2 = self.dH_dt(H0 + 0.5 * dt_hours * k1, lambda_reconnect)
        k3 = self.dH_dt(H0 + 0.5 * dt_hours * k2, lambda_reconnect)
        k4 = self.dH_dt(H0 + dt_hours * k3, lambda_reconnect)
        dH = (dt_hours / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        # Stochastic perturbation (flux-emergence fluctuations)
        dH += self.rng.normal(0.0, noise_sigma * dt_hours)

        H_new = float(np.clip(H0 + dH, 0.0, 1.0))
        flare_triggered = H_new >= H_THRESHOLD and H0 < H_THRESHOLD

        energy_released_J = 0.0
        if flare_triggered:
            energy_released_J = (H_new - H_STAR_QUIET) * E_MAX_J
            H_new = H_STAR_QUIET + self.rng.uniform(0.0, 0.02)
            self._flare_count += 1
            self._last_flare_energy_J = energy_released_J

        self.H = H_new
        self._time_hours += dt_hours
        self._history.append(H_new)

        return {
            "H_new": H_new,
            "dH_dt": float(k1),
            "flare_triggered": flare_triggered,
            "energy_released_J": energy_released_J,
        }

    # ── bulk simulation ────────────────────────────────────────────────────────

    def simulate(
        self,
        duration_hours: float,
        dt_hours: float = 0.1,
        lambda_func=None,
    ) -> dict:
        """Run the active-region ODE for duration_hours.

        Parameters
        ----------
        lambda_func : callable(H, t) -> float, optional
            Time-varying reconnection rate.  Defaults to LAMBDA_QUIET.
        """
        if lambda_func is None:
            lambda_func = lambda H, t: LAMBDA_QUIET  # noqa: E731

        n_steps = int(duration_hours / dt_hours)
        times = np.zeros(n_steps + 1)
        H_arr = np.zeros(n_steps + 1)
        H_arr[0] = self.H

        flare_events: list[dict] = []

        for i in range(n_steps):
            t = i * dt_hours
            lam = float(lambda_func(self.H, t))
            result = self.step(dt_hours=dt_hours, lambda_reconnect=lam)
            times[i + 1] = t + dt_hours
            H_arr[i + 1] = result["H_new"]
            if result["flare_triggered"]:
                flare_events.append(
                    {
                        "time_h": t,
                        "energy_J": result["energy_released_J"],
                        "H_pre": H_arr[i],
                    }
                )

        return {"times": times, "H": H_arr, "flare_events": flare_events}

    # ── derived properties ─────────────────────────────────────────────────────

    @property
    def non_potential_fraction(self) -> float:
        """Fraction of energy above the potential (current-free) field state."""
        return float(np.clip(self.H - H_STAR_QUIET, 0.0, 1.0))

    @property
    def helicity_coherence(self) -> float:
        """Proxy for magnetic helicity coherence from recent H trajectory.

        High coherence → sustained monotonic rise of H → C component of CREP.
        """
        if len(self._history) < 5:
            return 0.01
        recent = np.array(self._history[-20:])
        # Fraction of consecutive increases in recent history
        increases = float(np.sum(np.diff(recent) > 0)) / max(len(recent) - 1, 1)
        # Scale to solar nominal range [0, 0.1]
        return float(np.clip(increases * 0.1, 0.0, 1.0))

    @property
    def flare_count(self) -> int:
        return self._flare_count

    @property
    def last_flare_energy_J(self) -> float:
        return self._last_flare_energy_J

    def reset(self, h_init: float = H_STAR_QUIET) -> None:
        self.H = float(np.clip(h_init, 0.0, 1.0))
        self._history = [self.H]
        self._time_hours = 0.0
        self._flare_count = 0
        self._last_flare_energy_J = 0.0
