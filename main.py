#!/usr/bin/env python3
"""
main.py – Primary Execution Script
====================================

A Parametric Analysis of the Kham Restoration and Its Replicability
Across Indian Waterways.

This script orchestrates the complete analysis pipeline:
    1. Load and validate data
    2. Build the six-parameter matrix
    3. Compute similarity metrics (Euclidean, Cosine, Manhattan)
    4. Compute the Composite Replicability Index
    5. Generate publication-quality visualisations
    6. Export results to CSV

Usage:
    python main.py                    # Full analysis + visualisations
    python main.py --no-plots         # Analysis only, no plots
    python main.py --export-csv       # Export results to CSV

Author: River Revival Research Group
Version: 1.0.0
"""

import os
import sys
import io
import argparse
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import pandas as pd
from tabulate import tabulate

# Ensure the project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from src.parameters import (
    build_parameter_matrix,
    PARAMETER_WEIGHTS,
    CPCB_THRESHOLDS,
    compute_wqi,
    load_kham_data,
    load_candidate_data,
)
from src.similarity import (
    normalise_matrix,
    run_full_analysis,
    ALPHA, BETA, GAMMA,
)
from src.visualise import generate_all_figures


def print_header():
    """Print the analysis header."""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 10 + "A PARAMETRIC ANALYSIS OF THE KHAM RESTORATION" + " " * 22 + "║")
    print("║" + " " * 5 + "AND ITS REPLICABILITY ACROSS INDIAN WATERWAYS" + " " * 27 + "║")
    print("╠" + "═" * 78 + "╣")
    print(f"║  Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " " * 43 + "║")
    print(f"║  Version:  1.0.0" + " " * 60 + "║")
    print("╚" + "═" * 78 + "╝\n")


def print_section(title: str):
    """Print a section divider."""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")


def display_parameter_matrix(raw_df: pd.DataFrame):
    """Display the raw parameter matrix in a formatted table."""
    print_section("OBJECTIVE 1: KEY RESTORATION PARAMETERS")
    print("\nThe six parametric dimensions extracted from the Kham case study:\n")

    for param, weight in PARAMETER_WEIGHTS.items():
        label = param.replace("_", " ").title()
        print(f"  • {label:<30s}  Weight: {weight:.2f}  ({weight*100:.0f}%)")

    print(f"\n{'─' * 60}")
    print("\nParameter Matrix (raw scores):\n")

    display_df = raw_df.copy()
    display_df = display_df.drop(columns=["state"], errors="ignore")

    # Rename columns for display
    col_rename = {
        "water_quality_index": "WQI",
        "physical_ecological": "Phys/Eco",
        "waste_load_intensity": "Waste Load",
        "governance_access": "Governance",
        "community_engagement": "Community",
        "seasonality_factor": "Seasonality",
    }
    display_df = display_df.rename(columns=col_rename)

    print(tabulate(display_df, headers="keys", tablefmt="grid",
                   floatfmt=".3f", showindex=True))


def display_similarity_results(results: dict):
    """Display the similarity analysis results."""
    print_section("OBJECTIVE 2: REPLICABILITY ANALYSIS")

    print("\nComposite Replicability Index (RI) Formula:")
    print(f"  RI = {ALPHA}×CS + {BETA}×(1 - ED_norm) + {GAMMA}×(1 - MD_norm)")
    print("  Where CS = Cosine Similarity, ED = Euclidean Distance, MD = Manhattan Distance\n")

    ranking = results["replicability_ranking"]

    # Display ranking table
    display_cols = ["rank", "river", "state", "replicability_index",
                    "cosine_similarity", "euclidean_distance", "category"]
    display_df = ranking[display_cols].copy()
    display_df.columns = ["Rank", "River", "State", "RI Score",
                          "Cosine Sim.", "Euclid. Dist.", "Category"]

    print(tabulate(display_df, headers="keys", tablefmt="grid",
                   floatfmt=".4f", showindex=False))

    # Best match
    best = ranking.iloc[0]
    print(f"\n  ★ STRONGEST COMPARATOR: {best['river']} ({best['state']})")
    print(f"    Replicability Index: {best['replicability_index']:.4f}")
    print(f"    Category: {best['category']}")
    print(f"    Cosine Similarity to Kham: {best['cosine_similarity']:.4f}")


def display_kham_summary():
    """Display key facts about the Kham restoration."""
    print_section("KHAM RIVER RESTORATION – KEY FACTS")

    kham = load_kham_data()
    pre = kham["pre_restoration"]
    post = kham["post_restoration"]
    outcomes = post["restoration_outcomes"]

    print(f"""
  Location:     {kham['location']['city']}, {kham['location']['state']}
  River Length:  {kham['physical_characteristics']['length_km']} km (total),
                 {kham['physical_characteristics']['urban_stretch_km']} km (urban),
                 {kham['physical_characteristics']['restored_stretch_km']} km (restored)
  Type:          Seasonal/Intermittent tributary of Godavari River
  Population:    {kham['physical_characteristics']['city_population']:,} (city),
                 {kham['physical_characteristics']['catchment_population']:,} (catchment)

  Pre-Restoration Water Quality:
    DO:  {pre['water_quality']['DO']['value']} mg/L  (threshold: ≥{CPCB_THRESHOLDS['DO']})
    BOD: {pre['water_quality']['BOD']['value']} mg/L  (threshold: ≤{CPCB_THRESHOLDS['BOD']})
    COD: {pre['water_quality']['COD']['value']} mg/L (threshold: ≤{CPCB_THRESHOLDS['COD']})
    TDS: {pre['water_quality']['TDS']['value']} mg/L (threshold: ≤{CPCB_THRESHOLDS['TDS']})

  Key Outcomes:
    • {outcomes['riparian_restored_acres']} acres of riparian zone restored
    • {outcomes['households_waste_collection']:,} households connected to waste collection
    • {outcomes['community_participants']:,} people participated in waterfront events
    • {outcomes['native_saplings_planted']:,} native saplings planted
    • {outcomes['garbage_points_eliminated']} Garbage Vulnerable Points eliminated
    • {outcomes['flood_free_years']} consecutive flood-free years
    • {outcomes['material_recovery_facilities']} material recovery facilities established
    • {outcomes['sanitation_staff_integrated']} sanitation staff formalised
    """)


def export_results_csv(results: dict):
    """Export all results to CSV files in the output directory."""
    output = Path("output")
    output.mkdir(parents=True, exist_ok=True)

    # Parameter matrix
    results["parameter_matrix"].to_csv(output / "parameter_matrix.csv")
    print(f"  ✓ Exported: output/parameter_matrix.csv")

    # Normalised matrix
    results["normalised_matrix"].to_csv(output / "normalised_matrix.csv")
    print(f"  ✓ Exported: output/normalised_matrix.csv")

    # RI ranking
    results["replicability_ranking"].to_csv(output / "replicability_ranking.csv",
                                            index=False)
    print(f"  ✓ Exported: output/replicability_ranking.csv")

    # Cosine similarity
    results["cosine_similarities"].to_csv(output / "cosine_similarities.csv")
    print(f"  ✓ Exported: output/cosine_similarities.csv")

    # Euclidean distances
    results["euclidean_distances"].to_csv(output / "euclidean_distances.csv")
    print(f"  ✓ Exported: output/euclidean_distances.csv")

    # Manhattan distances
    results["manhattan_distances"].to_csv(output / "manhattan_distances.csv")
    print(f"  ✓ Exported: output/manhattan_distances.csv")


def main():
    """Run the complete parametric analysis pipeline."""
    parser = argparse.ArgumentParser(
        description="Kham River Restoration Parametric Analysis"
    )
    parser.add_argument("--no-plots", action="store_true",
                        help="Skip visualisation generation")
    parser.add_argument("--export-csv", action="store_true",
                        help="Export results to CSV")
    args = parser.parse_args()

    print_header()

    # Step 1: Display Kham summary
    display_kham_summary()

    # Step 2: Build parameter matrix
    raw_df = build_parameter_matrix()
    display_parameter_matrix(raw_df)

    # Step 3: Run full analysis
    results = run_full_analysis()
    display_similarity_results(results)

    # Step 4: Export CSV if requested
    if args.export_csv:
        print_section("EXPORTING RESULTS TO CSV")
        export_results_csv(results)

    # Step 5: Generate plots
    if not args.no_plots:
        print_section("GENERATING VISUALISATIONS")
        generate_all_figures()

    print_section("ANALYSIS COMPLETE")
    print("\n  All outputs saved to: output/")
    print("  To view results without plots: python main.py --no-plots")
    print("  To export CSV data:            python main.py --export-csv")
    print()


if __name__ == "__main__":
    main()
