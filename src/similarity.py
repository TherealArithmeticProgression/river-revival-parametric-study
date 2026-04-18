"""
similarity.py – Multi-Metric Similarity Analysis Module
========================================================

This module constructs similarity matrices between the Kham River (reference)
and candidate Indian rivers using multiple distance/similarity metrics,
then produces a composite Replicability Index (RI).

Mathematical Framework
----------------------

1. **Euclidean Distance (ED)**

   For two rivers A and B with parameter vectors P_A and P_B in ℝ^6:

       ED(A, B) = √[ Σ_{i=1}^{6} w_i × (P_A_i - P_B_i)² ]

   where w_i are the parameter weights. The weighted Euclidean distance
   accounts for the relative importance of each parametric dimension.

   Reference: Deza, M.M. & Deza, E. (2009). Encyclopedia of Distances.
   Springer. DOI: 10.1007/978-3-642-00234-2

2. **Cosine Similarity (CS)**

   Measures the angular similarity between parameter vectors:

       CS(A, B) = (P_A · P_B) / (‖P_A‖ × ‖P_B‖)

   CS ∈ [-1, 1], where 1 indicates identical parameter profiles.
   For our normalised non-negative vectors, CS ∈ [0, 1].

   Reference: Singhal, A. (2001). Modern Information Retrieval:
   A Brief Overview. Bulletin of the IEEE CS TC on Data Engineering.

3. **Manhattan Distance (MD)**

   Also called L1 norm or city-block distance:

       MD(A, B) = Σ_{i=1}^{6} w_i × |P_A_i - P_B_i|

4. **Composite Replicability Index (RI)**

   Combines normalised distance and similarity measures:

       RI = α × CS + β × (1 - ED_norm) + γ × (1 - MD_norm)

   where:
       - ED_norm = ED / ED_max  (normalised to [0, 1])
       - MD_norm = MD / MD_max  (normalised to [0, 1])
       - α = 0.40 (cosine similarity weight)
       - β = 0.35 (Euclidean proximity weight)
       - γ = 0.25 (Manhattan proximity weight)

   RI ∈ [0, 1], where 1 indicates perfect replicability match.

   The triple-metric approach provides robustness against any single
   metric's sensitivity to outliers or scale effects (Aggarwal, C.C., 2015).

References
----------
- Deza, M.M. & Deza, E. (2009). Encyclopedia of Distances. Springer.
- Singhal, A. (2001). Modern Information Retrieval. IEEE Bulletin.
- Aggarwal, C.C. (2015). Data Mining: The Textbook. Springer.
  Chapter 3: Similarity and Distances.
"""

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist, cosine
from src.parameters import PARAMETER_WEIGHTS, build_parameter_matrix


# Composite RI weights
ALPHA = 0.40  # Cosine similarity contribution
BETA = 0.35   # Euclidean proximity contribution
GAMMA = 0.25  # Manhattan proximity contribution


def get_weight_vector() -> np.ndarray:
    """
    Return the parameter weight vector aligned with DataFrame columns.

    Returns
    -------
    np.ndarray
        Weight vector of shape (6,).
    """
    param_cols = [
        "water_quality_index",
        "physical_ecological",
        "waste_load_intensity",
        "governance_access",
        "community_engagement",
        "seasonality_factor",
    ]
    return np.array([PARAMETER_WEIGHTS[c] for c in param_cols])


def normalise_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Min-max normalise the parameter matrix to [0, 1].

    For the WQI column, we first invert it (100 - WQI) so that higher
    pollution (lower WQI) maps to higher values, consistent with the
    interpretation that a river more similar to the Kham's degraded
    state has higher replicability potential.

    Parameters
    ----------
    df : pd.DataFrame
        Raw parameter matrix.

    Returns
    -------
    pd.DataFrame
        Normalised parameter matrix.
    """
    param_cols = [c for c in df.columns if c != "state"]
    norm_df = df.copy()

    # Invert WQI: higher pollution → higher score → more Kham-like
    if "water_quality_index" in norm_df.columns:
        norm_df["water_quality_index"] = 100.0 - norm_df["water_quality_index"]

    for col in param_cols:
        col_min = norm_df[col].min()
        col_max = norm_df[col].max()
        if col_max - col_min > 0:
            norm_df[col] = (norm_df[col] - col_min) / (col_max - col_min)
        else:
            norm_df[col] = 1.0

    return norm_df


def compute_euclidean_distances(norm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute weighted Euclidean distance matrix.

    ED(A, B) = √[ Σ w_i × (P_A_i - P_B_i)² ]

    Parameters
    ----------
    norm_df : pd.DataFrame
        Normalised parameter matrix.

    Returns
    -------
    pd.DataFrame
        Symmetric distance matrix.
    """
    param_cols = [c for c in norm_df.columns if c != "state"]
    values = norm_df[param_cols].values
    weights = get_weight_vector()

    n = len(values)
    dist_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            diff = values[i] - values[j]
            dist_matrix[i, j] = np.sqrt(np.sum(weights * diff ** 2))

    return pd.DataFrame(
        dist_matrix,
        index=norm_df.index,
        columns=norm_df.index,
    )


def compute_cosine_similarities(norm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cosine similarity matrix.

    CS(A, B) = (P_A · P_B) / (‖P_A‖ × ‖P_B‖)

    Parameters
    ----------
    norm_df : pd.DataFrame
        Normalised parameter matrix.

    Returns
    -------
    pd.DataFrame
        Symmetric similarity matrix with values in [0, 1].
    """
    param_cols = [c for c in norm_df.columns if c != "state"]
    values = norm_df[param_cols].values

    n = len(values)
    sim_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            norm_i = np.linalg.norm(values[i])
            norm_j = np.linalg.norm(values[j])
            if norm_i > 0 and norm_j > 0:
                sim_matrix[i, j] = np.dot(values[i], values[j]) / (norm_i * norm_j)
            else:
                sim_matrix[i, j] = 0.0

    return pd.DataFrame(
        sim_matrix,
        index=norm_df.index,
        columns=norm_df.index,
    )


def compute_manhattan_distances(norm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute weighted Manhattan distance matrix.

    MD(A, B) = Σ w_i × |P_A_i - P_B_i|

    Parameters
    ----------
    norm_df : pd.DataFrame
        Normalised parameter matrix.

    Returns
    -------
    pd.DataFrame
        Symmetric distance matrix.
    """
    param_cols = [c for c in norm_df.columns if c != "state"]
    values = norm_df[param_cols].values
    weights = get_weight_vector()

    n = len(values)
    dist_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            dist_matrix[i, j] = np.sum(weights * np.abs(values[i] - values[j]))

    return pd.DataFrame(
        dist_matrix,
        index=norm_df.index,
        columns=norm_df.index,
    )


def compute_replicability_index(norm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the Composite Replicability Index (RI) for all rivers
    relative to the Kham River reference.

    RI = α × CS + β × (1 - ED_norm) + γ × (1 - MD_norm)

    Parameters
    ----------
    norm_df : pd.DataFrame
        Normalised parameter matrix (first row must be Kham reference).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: river, RI, rank, cosine_sim,
        euclidean_dist, manhattan_dist, and the category classification.
    """
    ed_matrix = compute_euclidean_distances(norm_df)
    cs_matrix = compute_cosine_similarities(norm_df)
    md_matrix = compute_manhattan_distances(norm_df)

    kham_label = norm_df.index[0]  # Kham River (Reference)

    # Extract distances/similarities from Kham
    ed_from_kham = ed_matrix.loc[kham_label]
    cs_from_kham = cs_matrix.loc[kham_label]
    md_from_kham = md_matrix.loc[kham_label]

    # Normalise distances to [0, 1]
    ed_max = ed_from_kham.max() if ed_from_kham.max() > 0 else 1.0
    md_max = md_from_kham.max() if md_from_kham.max() > 0 else 1.0

    ed_norm = ed_from_kham / ed_max
    md_norm = md_from_kham / md_max

    # Compute RI
    ri = ALPHA * cs_from_kham + BETA * (1 - ed_norm) + GAMMA * (1 - md_norm)

    # Build results DataFrame
    results = pd.DataFrame({
        "river": norm_df.index,
        "state": norm_df["state"].values if "state" in norm_df.columns else "N/A",
        "replicability_index": ri.values,
        "cosine_similarity": cs_from_kham.values,
        "euclidean_distance": ed_from_kham.values,
        "manhattan_distance": md_from_kham.values,
    })

    # Exclude Kham itself from ranking
    results = results[results["river"] != kham_label].copy()
    results = results.sort_values("replicability_index", ascending=False)
    results["rank"] = range(1, len(results) + 1)

    # Classification thresholds
    results["category"] = results["replicability_index"].apply(classify_ri)

    return results.reset_index(drop=True)


def classify_ri(ri: float) -> str:
    """
    Classify a Replicability Index value into a category.

    Categories:
        RI ≥ 0.85  → "Excellent Match"   (direct strategy transfer)
        RI ≥ 0.70  → "Strong Match"      (minor adaptations needed)
        RI ≥ 0.55  → "Moderate Match"    (significant adaptations needed)
        RI ≥ 0.40  → "Partial Match"     (selective strategy transfer)
        RI < 0.40  → "Low Match"         (fundamentally different context)

    Parameters
    ----------
    ri : float
        Replicability Index value.

    Returns
    -------
    str
        Category label.
    """
    if ri >= 0.85:
        return "Excellent Match"
    elif ri >= 0.70:
        return "Strong Match"
    elif ri >= 0.55:
        return "Moderate Match"
    elif ri >= 0.40:
        return "Partial Match"
    else:
        return "Low Match"


def run_full_analysis(data_dir: str = "data") -> dict:
    """
    Execute the complete similarity analysis pipeline.

    Returns a dictionary containing:
        - parameter_matrix: raw scores
        - normalised_matrix: min-max normalised scores
        - euclidean_distances: weighted ED matrix
        - cosine_similarities: CS matrix
        - manhattan_distances: weighted MD matrix
        - replicability_ranking: final RI ranking

    Parameters
    ----------
    data_dir : str
        Path to data directory.

    Returns
    -------
    dict
        Complete analysis results.
    """
    # Build parameter matrix
    raw_df = build_parameter_matrix(data_dir)

    # Normalise
    norm_df = normalise_matrix(raw_df)

    # Compute all metrics
    ed = compute_euclidean_distances(norm_df)
    cs = compute_cosine_similarities(norm_df)
    md = compute_manhattan_distances(norm_df)

    # Compute RI
    ranking = compute_replicability_index(norm_df)

    return {
        "parameter_matrix": raw_df,
        "normalised_matrix": norm_df,
        "euclidean_distances": ed,
        "cosine_similarities": cs,
        "manhattan_distances": md,
        "replicability_ranking": ranking,
    }


if __name__ == "__main__":
    import os
    from pathlib import Path
    os.chdir(Path(__file__).resolve().parent.parent)

    results = run_full_analysis()

    print("\n" + "=" * 80)
    print("REPLICABILITY INDEX RANKING")
    print("=" * 80)
    print(results["replicability_ranking"].to_string(index=False))

    print("\n" + "=" * 80)
    print("COSINE SIMILARITY MATRIX (vs Kham)")
    print("=" * 80)
    print(results["cosine_similarities"].to_string())

    print("\n" + "=" * 80)
    print("EUCLIDEAN DISTANCE MATRIX (vs Kham)")
    print("=" * 80)
    print(results["euclidean_distances"].to_string())
