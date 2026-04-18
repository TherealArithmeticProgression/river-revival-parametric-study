"""
visualise.py – Publication-Quality Visualisation Module
=======================================================

Generates five key figures for the parametric study:

1. **Radar Chart**        – Overlays the six-parameter profiles of each
                            candidate river against the Kham reference.
2. **Similarity Heatmap** – Colour-coded cosine similarity matrix.
3. **RI Bar Chart**       – Ranked Replicability Index with category bands.
4. **WQI Comparison**     – Grouped bar chart of raw water-quality sub-parameters.
5. **Parameter Weights**  – Pie chart showing expert-assigned weight distribution.

All figures are saved to the ``output/`` directory in both PNG (300 dpi)
and SVG formats for publication use.

Colour Palette
--------------
Uses a colourblind-safe qualitative palette derived from
Wong, B. (2011). "Points of view: Color blindness." Nature Methods 8, 441.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import seaborn as sns
from pathlib import Path

from src.parameters import PARAMETER_WEIGHTS, build_parameter_matrix, WQI_SUB_WEIGHTS
from src.similarity import normalise_matrix, run_full_analysis


# ---------------------------------------------------------------------------
# Colour palette (colourblind-safe, Wong 2011)
# ---------------------------------------------------------------------------
COLORS = [
    "#E69F00",  # Orange
    "#56B4E9",  # Sky Blue
    "#009E73",  # Bluish Green
    "#F0E442",  # Yellow
    "#0072B2",  # Blue
    "#D55E00",  # Vermillion
    "#CC79A7",  # Reddish Purple
    "#000000",  # Black (Kham reference)
]

CATEGORY_COLORS = {
    "Excellent Match": "#009E73",
    "Strong Match":    "#56B4E9",
    "Moderate Match":  "#E69F00",
    "Partial Match":   "#D55E00",
    "Low Match":       "#CC79A7",
}

OUTPUT_DIR = Path("output")


def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def plot_radar_chart(norm_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """
    Generate a radar (spider) chart overlaying all rivers' parameter profiles.

    The radar chart provides an intuitive visual comparison of how closely
    each candidate river's parametric profile matches the Kham reference.
    Each axis represents one of the six parametric dimensions.

    Parameters
    ----------
    norm_df : pd.DataFrame
        Normalised parameter matrix.
    save : bool
        Whether to save the figure to disk.

    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    ensure_output_dir()

    param_cols = [c for c in norm_df.columns if c != "state"]
    labels = [
        "Water Quality\nDegradation",
        "Physical/\nEcological",
        "Waste Load\nIntensity",
        "Governance\nAccess",
        "Community\nEngagement",
        "Seasonality\nFactor",
    ]

    n_params = len(param_cols)
    angles = np.linspace(0, 2 * np.pi, n_params, endpoint=False).tolist()
    angles += angles[:1]  # Close the polygon

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=10, fontweight="bold")

    # Draw grid
    for i in np.arange(0.2, 1.2, 0.2):
        ax.plot(angles, [i] * (n_params + 1), "--", color="gray", alpha=0.3, linewidth=0.5)

    ax.set_ylim(0, 1.1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8, color="gray")

    # Plot each river
    legend_handles = []
    for idx, (river_name, row) in enumerate(norm_df.iterrows()):
        values = row[param_cols].values.tolist()
        values += values[:1]  # Close polygon

        color = COLORS[idx % len(COLORS)]
        linewidth = 3.0 if "Reference" in river_name else 1.8
        linestyle = "-" if "Reference" in river_name else "--"
        alpha = 0.3 if "Reference" in river_name else 0.08

        ax.plot(angles, values, color=color, linewidth=linewidth,
                linestyle=linestyle, label=river_name)
        ax.fill(angles, values, color=color, alpha=alpha)

        legend_handles.append(
            Line2D([0], [0], color=color, linewidth=linewidth,
                   linestyle=linestyle, label=river_name)
        )

    ax.legend(
        handles=legend_handles,
        loc="upper right",
        bbox_to_anchor=(1.35, 1.10),
        fontsize=9,
        frameon=True,
        framealpha=0.9,
        edgecolor="gray",
    )

    ax.set_title(
        "Parametric Profile Comparison\nCandidate Rivers vs. Kham River Reference",
        fontsize=14, fontweight="bold", pad=30,
    )

    plt.tight_layout()

    if save:
        fig.savefig(OUTPUT_DIR / "radar_chart.png", dpi=300, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        fig.savefig(OUTPUT_DIR / "radar_chart.svg", bbox_inches="tight",
                    facecolor=fig.get_facecolor())

    return fig


def plot_similarity_heatmap(results: dict, save: bool = True) -> plt.Figure:
    """
    Generate a cosine similarity heatmap.

    Visualises the pairwise cosine similarity between all rivers,
    highlighting which candidates share the most similar parametric
    profiles with the Kham reference.

    Parameters
    ----------
    results : dict
        Output from run_full_analysis().
    save : bool
        Whether to save the figure.

    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    ensure_output_dir()

    cs = results["cosine_similarities"]

    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor("#FAFAFA")

    mask = np.zeros_like(cs, dtype=bool)

    sns.heatmap(
        cs,
        annot=True,
        fmt=".3f",
        cmap="YlGnBu",
        vmin=0.7,
        vmax=1.0,
        linewidths=0.5,
        linecolor="white",
        square=True,
        ax=ax,
        cbar_kws={"label": "Cosine Similarity", "shrink": 0.8},
        annot_kws={"size": 9, "fontweight": "bold"},
    )

    ax.set_title(
        "Pairwise Cosine Similarity Matrix\nParametric Profiles of Indian Rivers",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)

    plt.tight_layout()

    if save:
        fig.savefig(OUTPUT_DIR / "similarity_heatmap.png", dpi=300,
                    bbox_inches="tight", facecolor=fig.get_facecolor())
        fig.savefig(OUTPUT_DIR / "similarity_heatmap.svg",
                    bbox_inches="tight", facecolor=fig.get_facecolor())

    return fig


def plot_replicability_ranking(results: dict, save: bool = True) -> plt.Figure:
    """
    Generate a horizontal bar chart of the Replicability Index ranking.

    Bars are colour-coded by category (Excellent, Strong, Moderate, etc.)
    with category thresholds shown as vertical reference lines.

    Parameters
    ----------
    results : dict
        Output from run_full_analysis().
    save : bool
        Whether to save the figure.

    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    ensure_output_dir()

    ranking = results["replicability_ranking"].sort_values(
        "replicability_index", ascending=True
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    bars = ax.barh(
        ranking["river"],
        ranking["replicability_index"],
        color=[CATEGORY_COLORS.get(c, "#999999") for c in ranking["category"]],
        edgecolor="white",
        linewidth=1.5,
        height=0.6,
    )

    # Add value labels
    for bar, ri_val in zip(bars, ranking["replicability_index"]):
        ax.text(
            bar.get_width() + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{ri_val:.3f}",
            va="center", ha="left", fontsize=10, fontweight="bold",
        )

    # Category threshold lines
    thresholds = [(0.85, "Excellent"), (0.70, "Strong"), (0.55, "Moderate"), (0.40, "Partial")]
    for thresh, label in thresholds:
        ax.axvline(x=thresh, color="gray", linestyle=":", alpha=0.6, linewidth=1)
        ax.text(thresh, len(ranking) - 0.3, f"  {label}", fontsize=8,
                color="gray", va="bottom")

    # Legend
    legend_patches = [
        mpatches.Patch(color=c, label=cat)
        for cat, c in CATEGORY_COLORS.items()
    ]
    ax.legend(
        handles=legend_patches, loc="lower right",
        fontsize=9, frameon=True, framealpha=0.9,
        title="Category", title_fontsize=10,
    )

    ax.set_xlabel("Replicability Index (RI)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Replicability Index Ranking\nCandidate Rivers for Kham-Model Restoration",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.set_xlim(0, 1.1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    if save:
        fig.savefig(OUTPUT_DIR / "replicability_ranking.png", dpi=300,
                    bbox_inches="tight", facecolor=fig.get_facecolor())
        fig.savefig(OUTPUT_DIR / "replicability_ranking.svg",
                    bbox_inches="tight", facecolor=fig.get_facecolor())

    return fig


def plot_wqi_comparison(data_dir: str = "data", save: bool = True) -> plt.Figure:
    """
    Generate a grouped bar chart comparing water quality sub-parameters
    across all rivers.

    Each cluster of bars represents one water quality parameter (DO, BOD,
    COD, TDS, TSS), with individual bars for each river. CPCB threshold
    lines are overlaid for reference.

    Parameters
    ----------
    data_dir : str
        Path to data directory.
    save : bool
        Whether to save the figure.

    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    ensure_output_dir()

    import json

    # Load all river data
    with open(Path(data_dir) / "kham_baseline.json", "r") as f:
        kham = json.load(f)
    with open(Path(data_dir) / "candidate_rivers.json", "r") as f:
        candidates = json.load(f)["candidate_rivers"]

    params = ["DO", "BOD", "COD", "TDS", "TSS"]
    rivers_data = {}

    # Kham
    kham_wq = kham["pre_restoration"]["water_quality"]
    rivers_data["Kham (Pre)"] = {p: kham_wq.get(p, {}).get("value", 0) for p in params}

    # Candidates
    for river in candidates:
        wq = river["water_quality"]
        rivers_data[river["name"][:12]] = {p: wq.get(p, {}).get("value", 0) for p in params}

    river_names = list(rivers_data.keys())
    n_rivers = len(river_names)
    n_params = len(params)

    fig, axes = plt.subplots(1, n_params, figsize=(20, 6), sharey=False)
    fig.patch.set_facecolor("#FAFAFA")

    thresholds = {"DO": 5.0, "BOD": 3.0, "COD": 150.0, "TDS": 500.0, "TSS": 100.0}

    for idx, param in enumerate(params):
        ax = axes[idx]
        ax.set_facecolor("#FAFAFA")
        values = [rivers_data[r][param] for r in river_names]

        bars = ax.bar(
            range(n_rivers), values,
            color=[COLORS[i % len(COLORS)] for i in range(n_rivers)],
            edgecolor="white", linewidth=1,
        )

        # CPCB threshold line
        if param in thresholds:
            ax.axhline(
                y=thresholds[param], color="red", linestyle="--",
                linewidth=1.5, alpha=0.7, label=f"CPCB: {thresholds[param]}"
            )
            ax.legend(fontsize=7, loc="upper right")

        ax.set_title(f"{param}", fontsize=12, fontweight="bold")
        ax.set_xticks(range(n_rivers))
        ax.set_xticklabels(river_names, rotation=65, ha="right", fontsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        if idx == 0:
            ax.set_ylabel("Concentration (mg/L)", fontsize=10)

    fig.suptitle(
        "Water Quality Sub-Parameter Comparison Across Rivers\n(vs. CPCB Class B Standards)",
        fontsize=14, fontweight="bold", y=1.02,
    )

    plt.tight_layout()

    if save:
        fig.savefig(OUTPUT_DIR / "wqi_comparison.png", dpi=300,
                    bbox_inches="tight", facecolor=fig.get_facecolor())
        fig.savefig(OUTPUT_DIR / "wqi_comparison.svg",
                    bbox_inches="tight", facecolor=fig.get_facecolor())

    return fig


def plot_parameter_weights(save: bool = True) -> plt.Figure:
    """
    Generate a donut chart showing the expert-assigned parameter weights.

    Parameters
    ----------
    save : bool
        Whether to save the figure.

    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    ensure_output_dir()

    labels = [
        "Water Quality (25%)",
        "Physical/Ecological (15%)",
        "Waste Load (15%)",
        "Governance (20%)",
        "Community (10%)",
        "Seasonality (15%)",
    ]
    weights = list(PARAMETER_WEIGHTS.values())

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor("#FAFAFA")

    wedges, texts, autotexts = ax.pie(
        weights,
        labels=labels,
        colors=COLORS[:6],
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.78,
        wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=10),
    )

    for at in autotexts:
        at.set_fontweight("bold")
        at.set_fontsize(11)

    ax.set_title(
        "Expert-Assigned Parameter Weights\nfor Replicability Index Computation",
        fontsize=14, fontweight="bold", pad=20,
    )

    plt.tight_layout()

    if save:
        fig.savefig(OUTPUT_DIR / "parameter_weights.png", dpi=300,
                    bbox_inches="tight", facecolor=fig.get_facecolor())
        fig.savefig(OUTPUT_DIR / "parameter_weights.svg",
                    bbox_inches="tight", facecolor=fig.get_facecolor())

    return fig


def generate_all_figures(data_dir: str = "data"):
    """
    Generate all five publication-quality figures.

    Parameters
    ----------
    data_dir : str
        Path to data directory.
    """
    print("=" * 60)
    print("  GENERATING VISUALISATIONS")
    print("=" * 60)

    results = run_full_analysis(data_dir)
    norm_df = results["normalised_matrix"]

    print("\n[1/5] Radar Chart...")
    plot_radar_chart(norm_df)
    print("      ✓ Saved: output/radar_chart.{png,svg}")

    print("[2/5] Similarity Heatmap...")
    plot_similarity_heatmap(results)
    print("      ✓ Saved: output/similarity_heatmap.{png,svg}")

    print("[3/5] Replicability Ranking...")
    plot_replicability_ranking(results)
    print("      ✓ Saved: output/replicability_ranking.{png,svg}")

    print("[4/5] WQI Comparison...")
    plot_wqi_comparison(data_dir)
    print("      ✓ Saved: output/wqi_comparison.{png,svg}")

    print("[5/5] Parameter Weights...")
    plot_parameter_weights()
    print("      ✓ Saved: output/parameter_weights.{png,svg}")

    print("\n" + "=" * 60)
    print("  ALL FIGURES GENERATED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent.parent)
    generate_all_figures()
