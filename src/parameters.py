"""
parameters.py – Parameter Extraction and Normalisation Module
=============================================================

This module defines the six key parametric dimensions identified from the
Kham River restoration case study (Objective 1) and provides functions to
extract, normalise, and weight these parameters for comparative analysis.

The Six Key Parametric Dimensions
---------------------------------
1. Water Quality Index (WQI)         – composite of pH, DO, BOD, COD, TDS, TSS, FC
2. Physical/Ecological Degradation   – riparian loss, siltation, encroachment
3. Waste Load Intensity              – sewage volume, solid waste area, GVPs
4. Governance & Institutional Access – PPP readiness, stakeholder diversity
5. Community Engagement Potential    – civic identity, willingness, cultural memory
6. Seasonality Factor                – flow intermittency, monsoon dependence

Mathematical Framework
----------------------
Each parameter P_i is normalised to [0, 1] using min-max scaling:

    P_i_norm = (P_i - P_min) / (P_max - P_min)

For parameters where higher values indicate worse conditions (e.g., BOD),
the normalisation is inverted so that 1 always represents the most
Kham-like (most restorable) condition.

The Weighted Composite Score (WCS) for each river is:

    WCS = Σ (w_i × P_i_norm)   for i = 1..6

where w_i are expert-assigned weights summing to 1.0.

References
----------
- Karhade, V.R. et al. (2020). Current World Environment Journal, 15(3).
  DOI: 10.12944/CWE.15.3.31
- Padme, Y.L. & Khobragade, K.S. (2015). Int. J. Chemical & Physical Sciences, 4(4).
- Brown, R.M. et al. (1970). Water Quality Index – Do We Dare? 
  Water & Sewage Works, 117(10), 339–343.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------------------------
# Expert-assigned weights (informed by literature and Kham case study)
# ---------------------------------------------------------------------------
# These weights reflect the relative importance of each parametric dimension
# in determining replicability, derived from the Kham restoration's lessons.
#
# Rationale:
#   - Water Quality receives the highest weight (0.25) because measurable
#     pollutant levels are the primary indicator of degradation severity
#     and the most direct measure of restoration need (Karhade et al., 2020).
#   - Governance/Institutional Access (0.20) is second because the Kham
#     case demonstrated that PPP models are essential enablers (Millennium
#     Post, 2025; Shin et al., 2024).
#   - Seasonality (0.15) is critical because the Kham's intermittent flow
#     defines the restoration approach—strategies differ fundamentally
#     between perennial and seasonal rivers (WRI, 2024).
#   - Physical/Ecological, Waste Load, and Community Engagement each receive
#     moderate weights (0.15, 0.15, 0.10) reflecting their supporting roles.

PARAMETER_WEIGHTS = {
    "water_quality_index":   0.25,
    "physical_ecological":   0.15,
    "waste_load_intensity":  0.15,
    "governance_access":     0.20,
    "community_engagement":  0.10,
    "seasonality_factor":    0.15,
}


# ---------------------------------------------------------------------------
# Sub-parameter weights for Water Quality Index (WQI)
# ---------------------------------------------------------------------------
# Adapted from Brown et al. (1970) National Sanitation Foundation WQI,
# modified for Indian river conditions per CPCB standards.
#
#   WQI = Σ (w_j × q_j)
#
# where q_j is the quality rating for each sub-parameter:
#   q_j = 100 × [(V_observed - V_ideal) / (V_standard - V_ideal)]
#
# For DO: q_DO = 100 × (DO_obs / DO_standard)  [higher is better]
# For BOD, COD, TDS, TSS, FC: q_j = 100 × (V_standard / V_obs) [lower is better]

WQI_SUB_WEIGHTS = {
    "DO":  0.20,
    "BOD": 0.25,
    "COD": 0.15,
    "TDS": 0.15,
    "TSS": 0.10,
    "fecal_coliform": 0.15,
}

# CPCB thresholds for bathing-quality water (Class B)
CPCB_THRESHOLDS = {
    "DO":  5.0,       # mg/L (minimum desirable)
    "BOD": 3.0,       # mg/L (maximum permissible)
    "COD": 150.0,     # mg/L (maximum permissible)
    "TDS": 500.0,     # mg/L (maximum permissible)
    "TSS": 100.0,     # mg/L (maximum permissible)
    "fecal_coliform": 500,  # MPN/100mL (maximum permissible)
}


def load_kham_data(data_dir: str = "data") -> dict:
    """Load Kham River baseline data from JSON."""
    path = Path(data_dir) / "kham_baseline.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_candidate_data(data_dir: str = "data") -> list:
    """Load candidate river data from JSON."""
    path = Path(data_dir) / "candidate_rivers.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["candidate_rivers"]


def compute_wqi(water_quality: dict) -> float:
    """
    Compute the Water Quality Index (WQI) for a river.

    Uses a weighted arithmetic mean of sub-index scores, following the
    NSF-WQI methodology adapted for Indian conditions.

    The formula for each sub-parameter quality rating q_j:

        For DO (higher is better):
            q_DO = min(100, 100 × DO_obs / DO_threshold)

        For pollutants (lower is better):
            q_j  = min(100, 100 × Threshold_j / Value_j)

    Final WQI = Σ (w_j × q_j)

    A WQI of 100 indicates perfect compliance with CPCB Class B standards.
    Lower values indicate worse water quality.

    Parameters
    ----------
    water_quality : dict
        Dictionary with keys: DO, BOD, COD, TDS, TSS, fecal_coliform.
        Each entry has a "value" field.

    Returns
    -------
    float
        WQI score in [0, 100].

    References
    ----------
    Brown, R.M. et al. (1970). Water Quality Index – Do We Dare?
    CPCB (2017). Guidelines for Water Quality Monitoring.
    """
    wqi = 0.0
    for param, weight in WQI_SUB_WEIGHTS.items():
        if param not in water_quality:
            continue
        value = water_quality[param]["value"]
        threshold = CPCB_THRESHOLDS[param]

        if param == "DO":
            # Higher DO is better
            q = min(100.0, 100.0 * value / threshold)
        else:
            # Lower pollutant concentration is better
            if value == 0:
                q = 100.0
            else:
                q = min(100.0, 100.0 * threshold / value)

        wqi += weight * q

    return round(wqi, 2)


def compute_degradation_score(river_data: dict) -> float:
    """
    Compute the Physical/Ecological Degradation score.

    This is a qualitative-to-quantitative mapping based on the
    presence of degradation indicators identified in the Kham case.

    Scoring rubric (each indicator contributes 0-1):
        - Riparian cover depletion     : 0.3
        - Active encroachment          : 0.2
        - Unregulated sand mining      : 0.15
        - Flooding vulnerability        : 0.2
        - Biodiversity loss             : 0.15

    Parameters
    ----------
    river_data : dict
        River data dictionary with matching_parameters list.

    Returns
    -------
    float
        Score in [0, 1] where 1 = most Kham-like degradation.
    """
    indicators = {
        "encroachment": 0.20,
        "siltation_issues": 0.15,
        "urban_river": 0.30,
        "legacy_waste": 0.20,
        "heavy_metal_contamination": 0.15,
    }
    matching = river_data.get("matching_parameters", [])
    score = sum(w for k, w in indicators.items()
                if any(k in mp for mp in matching))
    return round(min(score, 1.0), 2)


def compute_waste_load_score(water_quality: dict) -> float:
    """
    Compute the Waste Load Intensity score.

    Derived from BOD and COD exceedance ratios as proxies for
    organic and chemical waste loading.

    Formula:
        WLS = 0.5 × min(1, BOD/BOD_threshold) + 
              0.3 × min(1, COD/COD_threshold) +
              0.2 × min(1, FC/FC_threshold)

    The score is normalised to [0, 1] where 1 indicates
    waste loading comparable to or exceeding the Kham's pre-restoration state.

    Parameters
    ----------
    water_quality : dict
        Water quality parameters dictionary.

    Returns
    -------
    float
        Waste load intensity score in [0, 1].
    """
    bod = water_quality.get("BOD", {}).get("value", 0)
    cod = water_quality.get("COD", {}).get("value", 0)
    fc = water_quality.get("fecal_coliform", {}).get("value", 0)

    # Normalise against Kham pre-restoration values as upper bound
    kham_bod = 48.0
    kham_cod = 162.0
    kham_fc = 9200

    score = (
        0.5 * min(1.0, bod / kham_bod) +
        0.3 * min(1.0, cod / kham_cod) +
        0.2 * min(1.0, fc / kham_fc)
    )
    return round(score, 2)


def compute_governance_score(river_data: dict) -> float:
    """
    Compute the Governance & Institutional Access score.

    Maps the qualitative governance readiness indicator to a
    quantitative score, augmented by the presence of existing
    institutional initiatives.

    Scoring:
        governance_readiness mapping:
            "high"        → 0.8
            "medium_high" → 0.65
            "medium"      → 0.5
            "low"         → 0.2

        Bonus for existing initiatives: +0.2 (capped at 1.0)

    Parameters
    ----------
    river_data : dict
        River data dictionary.

    Returns
    -------
    float
        Governance score in [0, 1].
    """
    readiness_map = {
        "high": 0.80,
        "medium_high": 0.65,
        "medium": 0.50,
        "low": 0.20,
    }
    readiness = river_data.get("governance_readiness", "low")
    score = readiness_map.get(readiness, 0.2)

    # Bonus for existing initiatives
    if river_data.get("existing_initiatives"):
        score = min(1.0, score + 0.15)

    return round(score, 2)


def compute_community_score(river_data: dict) -> float:
    """
    Compute the Community Engagement Potential score.

    Based on matching parameters related to civic identity,
    cultural memory, and community participation potential.

    Indicators and weights:
        - community_identity_potential  : 0.30
        - community_memory             : 0.25
        - strong_civic_identity        : 0.25
        - restoration_discourse_ongoing: 0.20

    Parameters
    ----------
    river_data : dict
        River data dictionary with matching_parameters list.

    Returns
    -------
    float
        Community engagement score in [0, 1].
    """
    indicators = {
        "community_identity_potential": 0.30,
        "community_memory": 0.25,
        "strong_civic_identity": 0.25,
        "restoration_discourse_ongoing": 0.20,
    }
    matching = river_data.get("matching_parameters", [])
    score = sum(w for k, w in indicators.items()
                if any(k in mp for mp in matching))
    return round(min(score, 1.0), 2)


def compute_seasonality_score(river_data: dict) -> float:
    """
    Compute the Seasonality Factor score.

    The Kham's intermittent/seasonal nature is a defining characteristic
    for replicability matching. Rivers with similar seasonal patterns
    score higher because the Kham restoration strategies were designed
    specifically for intermittent flows.

    Scoring:
        type mapping:
            "seasonal_intermittent"          → 1.0
            "seasonal_himalayan"             → 0.85
            "seasonal_rivulet"               → 0.80
            "seasonal_urban"                 → 0.75
            "seasonal_with_dam_regulation"   → 0.60
            "perennial"                      → 0.20

    Bonus for "seasonal_flow" in matching parameters: +0.1

    Parameters
    ----------
    river_data : dict
        River data dictionary.

    Returns
    -------
    float
        Seasonality score in [0, 1].
    """
    type_map = {
        "seasonal_intermittent": 1.0,
        "seasonal_himalayan": 0.85,
        "seasonal_rivulet": 0.80,
        "seasonal_urban": 0.75,
        "seasonal_with_dam_regulation": 0.60,
        "perennial": 0.20,
    }
    river_type = river_data.get("type", "perennial")
    score = type_map.get(river_type, 0.3)

    matching = river_data.get("matching_parameters", [])
    if "seasonal_flow" in matching:
        score = min(1.0, score + 0.05)

    return round(score, 2)


def build_parameter_matrix(data_dir: str = "data") -> pd.DataFrame:
    """
    Build the complete parameter matrix for all candidate rivers.

    Extracts the six parametric dimensions for each candidate river
    and returns a DataFrame suitable for similarity analysis.

    The resulting matrix has:
        - Rows: Candidate rivers + Kham River (reference)
        - Columns: Six parametric dimension scores

    Parameters
    ----------
    data_dir : str
        Path to the data directory.

    Returns
    -------
    pd.DataFrame
        Parameter matrix with normalised scores.
    """
    kham = load_kham_data(data_dir)
    candidates = load_candidate_data(data_dir)

    rows = []

    # Kham River (reference case)
    kham_wq = kham["pre_restoration"]["water_quality"]
    kham_row = {
        "river": "Kham River (Reference)",
        "state": kham["location"]["state"],
        "water_quality_index": compute_wqi(kham_wq),
        "physical_ecological": 1.0,   # Maximum degradation (baseline)
        "waste_load_intensity": 1.0,  # Maximum waste load (baseline)
        "governance_access": 1.0,     # Proven governance model
        "community_engagement": 1.0,  # Demonstrated engagement
        "seasonality_factor": 1.0,    # Seasonal intermittent (baseline)
    }
    rows.append(kham_row)

    # Candidate rivers
    for river in candidates:
        wq = river["water_quality"]
        row = {
            "river": river["name"],
            "state": river["state"],
            "water_quality_index": compute_wqi(wq),
            "physical_ecological": compute_degradation_score(river),
            "waste_load_intensity": compute_waste_load_score(wq),
            "governance_access": compute_governance_score(river),
            "community_engagement": compute_community_score(river),
            "seasonality_factor": compute_seasonality_score(river),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.set_index("river")

    return df


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).resolve().parent.parent)
    
    df = build_parameter_matrix()
    print("\n" + "=" * 80)
    print("PARAMETER MATRIX – Kham Restoration Replicability Analysis")
    print("=" * 80)
    print(df.to_string())
    print("\n" + "-" * 80)
    print("Parameter Weights:", PARAMETER_WEIGHTS)
