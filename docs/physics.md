# Physics Background

## UTAC Framework

The **Universal Threshold Avalanche Criticality (UTAC)** framework models
phase-transition-like events as dynamical systems with a CREP-gated threshold.

### State Variable Mapping

| UTAC symbol | Solar quantity |
|---|---|
| H(t) | Normalised magnetic free energy ∈ [0, 1] |
| K | E_max ≈ 10³² J (active region energy ceiling) |
| H* | Quiescent fixed point ≈ 0.10 K |
| r | Flux-emergence buildup rate ≈ 0.06 hr⁻¹ |
| σ | CREP coupling = 2.2 |
| Γ(t) | CREP tensor (C, R, E, P) → Γ_solar ≈ 0.014 |

### ODE

$$\frac{dH}{dt} = r(1 - H) - \lambda(H, \Gamma) \cdot H$$

where the CREP-gated reconnection rate is:

$$\lambda(H, \Gamma) = \begin{cases}
  \lambda_{\text{quiet}} & H < H_{\text{threshold}} \text{ or } \Gamma \leq \theta_{PT} \\
  \lambda_{\text{quiet}} + (\lambda_{\text{eruptive}} - \lambda_{\text{quiet}}) \tanh(\sigma\Gamma) & \text{otherwise}
\end{cases}$$

## CREP Tensor

Four observational quantities map to the scalar CREP coupling Γ:

$$\Gamma = \frac{\text{arctanh}(\eta_{\text{CREP}})}{\sigma}, \quad
\eta_{\text{CREP}} = \frac{C + R + E + P}{4}$$

| Component | Physical quantity |
|---|---|
| C | Magnetic helicity coherence (twist uniformity) |
| R | Resonance between photospheric driver and corona |
| E | Non-potential energy fraction (free energy above potential field) |
| P | 1 − permutation entropy of GOES 1–8 Å flux |

## Central Result: Γ_solar ≈ 0.014

From the UTAC fixed-point condition H* = K · tanh(σΓ), with η = H*/K:

$$\Gamma_{\text{solar}} = \frac{\text{arctanh}(0.03)}{2.2} \approx 0.014$$

A typical X-class flare releases η ≈ 3% of the active-region magnetic energy,
fixing the solar operating point at the ultra-sensitive end of the CREP spectrum.

## Magnetic Avalanche Mechanism

The "magnetic avalanche" (Solar Orbiter A&A 2026) corresponds to the phase
transition at H > H_threshold AND Γ > θ_PT:

1. Photospheric flux emergence drives H(t) upward (slowly, r ≈ 0.06 hr⁻¹)
2. When H crosses H_threshold ≈ 0.60, the current sheet becomes unstable
3. If Γ > θ_PT at the same time, reconnection triggers
4. Energy releases rapidly: E_flare = (H − H*_quiet) × E_max
5. H relaxes back to the quiescent fixed point H* ≈ 0.10

## Geomagnetic Impact

Flare energy is coupled to the geomagnetic Dst index via:

$$\text{Dst}_{peak} = Q \cdot p_{\text{dyn}} \quad \text{(Burton et al. 1975)}$$

where $p_{\text{dyn}} \propto v_{\text{CME}}^2 \cdot \eta$ is the CME dynamic pressure proxy.
