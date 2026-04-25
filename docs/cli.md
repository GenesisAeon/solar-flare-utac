# CLI Reference

The `solar-utac` command-line interface provides access to all UTAC simulation
and analysis functions.

## Installation

```bash
pip install solar-flare-utac
```

## Commands

### `solar-utac run`

Run a UTAC simulation cycle for a solar active region.

```bash
solar-utac run --duration 72 --active-region AR3000 --seed 42
```

| Option | Default | Description |
|---|---|---|
| `--duration` / `-d` | 72.0 | Cycle duration [hours] |
| `--active-region` / `-ar` | `AR_synthetic` | Active region identifier |
| `--seed` | 42 | Random seed |

### `solar-utac flare-window`

Estimate flare probability window over the next N days.

```bash
solar-utac flare-window --horizon 7
```

### `solar-utac gamma-crep-spectrum`

Print the complete GenesisAeon CREP Criticality Spectrum (Packages 17–22).

```bash
solar-utac gamma-crep-spectrum
```

### `solar-utac benchmark`

Validate the model against `SOLAR_TARGETS` (GOES catalog + Solar Orbiter data).

```bash
solar-utac benchmark
```

### `solar-utac zenodo-export`

Export a Zenodo-compatible metadata record to stdout.

```bash
solar-utac zenodo-export > record.json
```

### `solar-utac version`

Show the installed version.

```bash
solar-utac version
```
