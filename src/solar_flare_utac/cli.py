"""Command-line interface for solar-flare-utac (GenesisAeon Package 21).

Usage
-----
  solar-utac run --duration 72 --active-region AR3000
  solar-utac flare-window --horizon 7 --class X
  solar-utac gamma-crep-spectrum
  solar-utac zenodo-export
  solar-utac benchmark
"""
from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import GAMMA_SOLAR, SIGMA_CREP, __version__
from .system import SolarFlareUTAC

app = typer.Typer(
    name="solar-utac",
    help="[bold]solar-flare-utac[/bold] — GenesisAeon Package 21: Solar flare UTAC model.",
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def run(
    duration: Annotated[float, typer.Option("--duration", "-d", help="Cycle duration [hours]")] = 72.0,
    active_region: Annotated[str, typer.Option("--active-region", "-ar")] = "AR_synthetic",
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """[bold]Run[/bold] a UTAC simulation cycle."""
    console.print(
        Panel(
            f"[bold green]solar-flare-utac[/bold green] v{__version__}  |  "
            f"Γ_solar ≈ {GAMMA_SOLAR:.4f}  |  σ = {SIGMA_CREP}",
            expand=False,
        )
    )
    model = SolarFlareUTAC(seed=seed, active_region_id=active_region)
    state = model.run_cycle(duration_hours=duration)

    utac = state["utac_state"]
    crep = state["crep_state"]

    table = Table(show_header=True, box=None, padding=(0, 2))
    table.add_column("Parameter", style="cyan bold")
    table.add_column("Value", style="yellow")

    table.add_row("H (free energy)", f"{utac['H']:.4f}")
    table.add_row("dH/dt [hr⁻¹]", f"{utac['dH_dt']:.4f}")
    table.add_row("H* (quiescent)", f"{utac['H_star']:.4f}")
    table.add_row("Γ (CREP)", f"{crep['Gamma']:.5f}")
    table.add_row("C / R / E / P", f"{crep['C']:.3f} / {crep['R']:.3f} / {crep['E']:.3f} / {crep['P']:.3f}")
    table.add_row("Flares this cycle", str(state["flare_count"]))

    console.print(table)


@app.command(name="flare-window")
def flare_window(
    horizon: Annotated[float, typer.Option("--horizon", help="Forecast horizon [days]")] = 3.0,
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """[bold]Estimate[/bold] flare probability window over next N days."""
    model = SolarFlareUTAC(seed=seed)
    model.run_cycle(duration_hours=24.0)
    window = model.predict_flare_window(horizon_days=horizon)

    console.print(f"\nFlare window forecast (next {horizon:.0f} days):")
    for k, v in window.items():
        style = "red bold" if k == "warning_level" and v == "HIGH" else "white"
        console.print(f"  [cyan]{k}[/cyan]: [{style}]{v}[/{style}]")


@app.command(name="gamma-crep-spectrum")
def gamma_crep_spectrum() -> None:
    """[bold]Print[/bold] the CREP Criticality Spectrum (Packages 17–22)."""
    spectrum = [
        ("Solar Flare",           "P21", 0.014, "1%",  "Ultra-sensitive"),
        ("Cygnus X-1 Jet",        "P17", 0.046, "5%",  "Hair-trigger"),
        ("Amazon Rainforest",     "P19", 0.116, "12%", "Fragile"),
        ("AMOC Ocean Current",    "P18", 0.251, "50%", "Homeostatic"),
        ("Neural Criticality",    "P20", 0.251, "50%", "Homeostatic (!)"),
        ("BTW Sandpile",          "P22", 0.296, "58%", "Robust SOC"),
        ("Manna Sandpile",        "P22", 0.376, "72%", "Dense SOC"),
        ("ERA5 Arctic (tipping)", "P01", 0.920, "99%", "Near-saturated"),
    ]
    table = Table(title="CREP Criticality Spectrum — GenesisAeon Atlas", show_lines=True)
    table.add_column("Domain", style="cyan")
    table.add_column("Pkg", style="dim")
    table.add_column("Γ", style="yellow bold")
    table.add_column("η (efficiency)")
    table.add_column("Character")

    for domain, pkg, gamma, eta, char in spectrum:
        style = "red bold" if pkg == "P21" else ""
        table.add_row(domain, pkg, f"{gamma:.3f}", eta, char, style=style)

    console.print(table)
    console.print(
        "\n[bold]Key result:[/bold] Γ_AMOC = Γ_brain = 0.251 — "
        "cross-domain universality at η = 50%."
    )


@app.command(name="zenodo-export")
def zenodo_export(
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """[bold]Export[/bold] a Zenodo-compatible metadata record to stdout."""
    import json
    model = SolarFlareUTAC(seed=seed)
    model.run_cycle(duration_hours=24.0)
    record = model.to_zenodo_record()
    console.print_json(json.dumps(record, indent=2))


@app.command()
def benchmark(
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """[bold]Validate[/bold] model against SOLAR_TARGETS benchmark."""
    from .benchmark import SolarBenchmark
    bm = SolarBenchmark(seed=seed)
    summary = bm.summary()

    console.print(f"\nBenchmark results: {summary['passed']}/{summary['total']} passed\n")
    for line in summary["results"]:
        colour = "green" if line.startswith("[PASS]") else "red"
        console.print(f"  [{colour}]{line}[/{colour}]")


@app.command()
def version() -> None:
    """Show the solar-flare-utac version."""
    console.print(f"solar-flare-utac [bold]{__version__}[/bold]")


if __name__ == "__main__":
    app()
