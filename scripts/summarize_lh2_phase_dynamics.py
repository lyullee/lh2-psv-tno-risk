"""Summarize and plot the targeted LH2 phase-dynamics calculations."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "paper" / "data"
FIG = ROOT / "paper" / "figures" / "lh2_phase_response.png"
PAPER_FIG_DIR = ROOT / "paper" / "figures"
PAPER_FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 7.5,
        "savefig.dpi": 300,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    }
)

NAVY = "#24394C"
TEAL = "#327A75"
RUST = "#B6613C"
GRAY = "#687781"
PALE = "#E7EBED"
COLORS = {0.6: NAVY, 2.0: TEAL, 6.0: RUST}


def read_trace(case: str) -> list[dict]:
    with (DATA / f"{case}_phase_trace.csv").open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def number(row: dict, key: str) -> float:
    value = row[key]
    return float(value) if value not in ("", None) else float("nan")


def derive(case: str, ua: float, bore: float, fill: float) -> dict:
    rows = read_trace(case)
    initial = rows[0]
    active = [i for i, row in enumerate(rows) if number(row, "release_rate_kg_s") > 1e-10]
    first = active[0]
    pre = rows[first - 1]
    qualities = np.array([number(row, "liquid_quality") for row in rows])
    masses = np.array([number(row, "liquid_mass_kg") for row in rows])
    finite = np.isfinite(qualities)
    flash_equivalent = np.where(finite, qualities * masses, np.nan)
    maximum = int(np.nanargmax(flash_equivalent))
    return {
        "case": case,
        "tank_UA_W_K": ua,
        "bore_mm": bore,
        "fill_fraction": fill,
        "first_open_h": number(pre, "time_s") / 3600.0,
        "liquid_temperature_rise_at_opening_K": number(pre, "liquid_temperature_K")
        - number(initial, "liquid_temperature_K"),
        "vapor_temperature_rise_at_opening_K": number(pre, "vapor_temperature_K")
        - number(initial, "vapor_temperature_K"),
        "preopen_interfacial_evaporation_kg": number(pre, "cum_evaporation_from_liquid_kg"),
        "maximum_lower_cv_quality": qualities[maximum],
        "maximum_flash_equivalent_mass_kg": flash_equivalent[maximum],
        "maximum_flash_time_h": number(rows[maximum], "time_s") / 3600.0,
        "released_mass_kg": number(rows[-1], "cum_release_kg"),
        "flash_to_release_ratio": flash_equivalent[maximum]
        / number(rows[-1], "cum_release_kg"),
        "phase_balance_error_kg": max(
            abs(number(row, "phase_mass_balance_difference_kg")) for row in rows
        ),
    }


CASES = (
    ("UA0.6_D6_F0.6", 0.6, 6.0, 0.6),
    ("UA2_D6_F0.6", 2.0, 6.0, 0.6),
    ("UA6_D6_F0.6", 6.0, 6.0, 0.6),
    ("UA2_D6_F0.4", 2.0, 6.0, 0.4),
    ("UA2_D6_F0.8", 2.0, 6.0, 0.8),
    ("UA0.6_D18_F0.6", 0.6, 18.0, 0.6),
)


def main() -> None:
    derived = [derive(*case) for case in CASES]
    with (DATA / "lh2_phase_findings.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=derived[0].keys())
        writer.writeheader()
        writer.writerows(derived)

    base = [row for row in derived if row["bore_mm"] == 6.0 and row["fill_fraction"] == 0.6]
    base.sort(key=lambda row: row["tank_UA_W_K"])
    x = np.arange(len(base))

    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.75), layout="constrained")

    width = 0.34
    axes[0].bar(
        x - width / 2,
        [row["liquid_temperature_rise_at_opening_K"] for row in base],
        width,
        color=TEAL,
        label="Lower liquid CV",
    )
    axes[0].bar(
        x + width / 2,
        [row["vapor_temperature_rise_at_opening_K"] for row in base],
        width,
        color=RUST,
        label="Upper vapor CV",
    )
    axes[0].set_xticks(x, [f"{row['tank_UA_W_K']:g}" for row in base])
    axes[0].set_xlabel("Tank UA (W K$^{-1}$)")
    axes[0].set_ylabel("Temperature rise at lift (K)")
    axes[0].set_ylim(0, 0.50)
    axes[0].set_title(
        "(a) Thermal state at PSV lift", loc="left", fontweight="bold", pad=28
    )
    axes[0].legend(
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=2,
        borderaxespad=0.0,
        columnspacing=1.0,
        handlelength=1.5,
    )
    for i, row in enumerate(base):
        axes[0].text(
            i,
            0.47,
            f"{row['first_open_h']:.2f} h",
            ha="center",
            va="bottom",
            fontsize=7.2,
            color=GRAY,
        )

    for row in base:
        case = row["case"]
        trace = read_trace(case)
        first_time = row["first_open_h"] * 3600.0
        elapsed = np.array([number(item, "time_s") - first_time for item in trace]) / 60.0
        quality = 100.0 * np.array([number(item, "liquid_quality") for item in trace])
        mask = (elapsed >= 0.0) & (elapsed <= 60.0) & np.isfinite(quality)
        axes[1].plot(
            elapsed[mask],
            quality[mask],
            lw=1.5,
            color=COLORS[row["tank_UA_W_K"]],
            label=f"UA {row['tank_UA_W_K']:g}",
        )
    axes[1].set_xlim(0, 60)
    axes[1].set_ylim(bottom=0)
    axes[1].set_xlabel("Time after first lift (min)")
    axes[1].set_ylabel("Lower-CV vapor quality (%)")
    axes[1].set_title("(b) Flash response", loc="left", fontweight="bold")
    axes[1].legend(
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=0.90,
        loc="lower right",
        borderpad=0.35,
    )

    markers = {0.4: "s", 0.6: "o", 0.8: "^"}
    for row in derived:
        color = COLORS.get(row["tank_UA_W_K"], GRAY)
        marker = markers[row["fill_fraction"]]
        axes[2].scatter(
            row["released_mass_kg"],
            row["maximum_flash_equivalent_mass_kg"],
            s=34 if row["bore_mm"] == 6.0 else 48,
            marker=marker,
            facecolor=color if row["bore_mm"] == 6.0 else "white",
            edgecolor=color,
            linewidth=1.1,
            zorder=3,
        )
    limit = 65
    axes[2].plot([0, limit], [0, limit], color=GRAY, lw=0.9, ls="--", label="1:1")
    axes[2].set_xlim(0, limit)
    axes[2].set_ylim(0, limit)
    axes[2].set_xlabel("Released mass by 6 h (kg)")
    axes[2].set_ylabel("Maximum flash-equivalent mass (kg)")
    axes[2].set_title("(c) Flash inventory and release", loc="left", fontweight="bold")
    axes[2].legend(frameon=False, loc="upper left")

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=PALE, lw=0.55, zorder=0)

    for extension in ("png", "pdf", "svg"):
        for directory in (DATA, PAPER_FIG_DIR):
            fig.savefig(
                directory / f"lh2_phase_response.{extension}",
                bbox_inches="tight",
                pad_inches=0.06,
            )
    plt.close(fig)


if __name__ == "__main__":
    main()
