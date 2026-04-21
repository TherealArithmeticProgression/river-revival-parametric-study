# Kham River Restoration – Parametric Analysis

A data-driven study that asks: **which Indian rivers can realistically replicate the Kham River restoration model?**

---

## Abstract

The Kham River in Chhatrapati Sambhajinagar (Aurangabad), Maharashtra, was restored from a heavily polluted drain into a vibrant ecological corridor through a public-private-civil society partnership. This project builds a simple parametric scoring system across six dimensions — water quality, physical/ecological degradation, waste load, governance, community engagement, and seasonality — then uses three similarity metrics (Cosine Similarity, Euclidean Distance, Manhattan Distance) to rank seven candidate rivers by their Replicability Index (RI).

**Key Finding:** The Nag River (Nagpur, Maharashtra) scores highest with an RI of ~0.72, making it the strongest candidate for directly applying Kham methodologies.

---

## Table of Contents
1. [The Six Parameters](#the-six-parameters)
2. [How the Scoring Works](#how-the-scoring-works)
3. [Results](#results)
4. [Charts Produced](#charts-produced)
5. [Running the Notebook](#running-the-notebook)
6. [References](#references)

---

## The Six Parameters

Each river is scored on six dimensions, each weighted by importance:

| # | Parameter | Weight | What It Measures |
|---|-----------|--------|-----------------|
| 1 | Water Quality Index (WQI) | **25%** | Composite of DO, BOD, COD, TDS, TSS, Fecal Coliform vs CPCB limits |
| 2 | Physical/Ecological Degradation | 15% | Encroachment, siltation, riparian loss |
| 3 | Waste Load Intensity | 15% | BOD and COD exceedance vs Kham pre-restoration baseline |
| 4 | Governance & Institutional Access | **20%** | PPP readiness, existing initiatives |
| 5 | Community Engagement Potential | 10% | Civic identity, cultural memory |
| 6 | Seasonality Factor | 15% | Flow intermittency match with Kham |

### Kham Pre-Restoration Baseline (the "problem profile" to match)

| Parameter | Kham Value | CPCB Limit | Status |
|-----------|-----------|------------|--------|
| DO | 2.1 mg/L | ≥ 5.0 mg/L | Critically low |
| BOD | 48.0 mg/L | ≤ 3.0 mg/L | 16× over limit |
| COD | 162.0 mg/L | ≤ 150.0 mg/L | Over limit |
| TDS | 1450.0 mg/L | ≤ 500.0 mg/L | 3× over limit |
| TSS | 380.0 mg/L | ≤ 100.0 mg/L | 3.8× over limit |
| Fecal Coliform | 9200 MPN/100mL | ≤ 500 | 18× over limit |

---

## How the Scoring Works

### Step 1 – Compute Raw Scores
Each river gets a score between 0 and 1 (or 0–100 for WQI) on each of the six dimensions using the data embedded directly in the notebook.

### Step 2 – Normalise (Min-Max)
$$P_i^{norm} = \frac{P_i - P_{min}}{P_{max} - P_{min}}$$

WQI is inverted first (`100 - WQI`) so that higher pollution → higher score, consistent with matching the Kham's degraded state.

### Step 3 – Three Similarity Metrics

**Euclidean Distance:**
$$ED(A, B) = \sqrt{\sum_{i=1}^{6} w_i \cdot (P_{A,i} - P_{B,i})^2}$$

**Cosine Similarity:**
$$CS(A, B) = \frac{P_A \cdot P_B}{\|P_A\| \times \|P_B\|}$$

**Manhattan Distance:**
$$MD(A, B) = \sum_{i=1}^{6} w_i \cdot |P_{A,i} - P_{B,i}|$$

### Step 4 – Composite Replicability Index
$$RI = 0.40 \times CS + 0.35 \times (1 - ED_{norm}) + 0.25 \times (1 - MD_{norm})$$

RI closer to 1.0 = stronger match with the Kham model.

---

## Results

| Rank | River | State | RI Score | Category |
|------|-------|-------|----------|----------|
| 1 | **Nag River** | Maharashtra | ~0.72 | Strong Match |
| 2 | Mula-Mutha River | Maharashtra | ~0.51 | Partial Match |
| 3 | Sukhna Choe | Punjab/Haryana | ~0.49 | Partial Match |
| 4 | Rispana-Bindal | Uttarakhand | ~0.44 | Partial Match |
| 5 | Sabarmati Tributaries | Gujarat | ~0.36 | Low Match |
| 6 | Cooum River | Tamil Nadu | ~0.35 | Low Match |
| 7 | Shivna River | Maharashtra | ~0.24 | Low Match |

The **Nag River** shares Nagpur's semi-arid tropical climate, seasonal intermittent flow, and a pollution profile dominated by untreated domestic sewage — nearly identical to the Kham's pre-restoration state.

---

## Charts Produced

All charts are saved to the `output/` folder when you run the notebook. Here is what each one shows:

### 1. `line_pre_post.png` – Pre vs Post Restoration (Line Chart)
A line chart comparing Kham's water quality parameters **before and after** restoration. Shows how DO, BOD, COD, TDS, and TSS changed after intervention. Clearly illustrates the dramatic improvement in water quality.

### 2. `hist_bod.png` – BOD Distribution (Histogram)
A histogram of BOD values across all rivers including Kham. The CPCB limit (3 mg/L) is shown as a red dashed line. Reveals that **every single river** is far above the safe limit — illustrating the scale of India's river pollution problem.

### 3. `ri_ranking.png` – Replicability Index Ranking (Horizontal Bar)
A colour-coded horizontal bar chart ranking all candidate rivers by their RI score. Bars are coloured by match category (green = Strong, orange = Moderate, red = Partial, pink = Low). Threshold lines at 0.55 and 0.70 are shown for reference.

### 4. `weights_pie.png` – Parameter Weights (Donut Pie Chart)
A donut-style pie chart showing the expert-assigned weight for each of the six parametric dimensions. Water Quality (25%) and Governance (20%) dominate the scoring.

### 5. `cosine_line.png` – Cosine Similarity Line Chart
A line chart showing each river's cosine similarity to the Kham parametric profile. Rivers with a cosine similarity close to 1.0 have the most similar "shape" of degradation, meaning the same types of problems — not just the same severity.

### 6. `hist_tds.png` – TDS Distribution (Histogram)
A histogram of Total Dissolved Solids across all rivers with the CPCB limit (500 mg/L) marked. Shows how dissolved salt/mineral loading varies and which rivers have the most extreme TDS values (Sabarmati tributaries and Cooum stand out).

### 7. `category_pie.png` – Match Category Distribution (Pie Chart)
A simple pie chart showing how many rivers fall into each replicability category. Out of seven candidates, only one achieves "Strong Match" status — showing how rare a truly Kham-like river profile is.

### 8. `metrics_line.png` – Multi-Metric Comparison (Line Chart)
Overlays three scores — RI, Cosine Similarity, and 1-Euclidean Distance — for all candidate rivers on a single line chart. Useful for seeing where the three metrics agree or diverge, validating the robustness of the composite RI.

---

## Running the Notebook

### Prerequisites
- Python 3.9+
- `numpy`, `pandas`, `matplotlib`

### Installation
```bash
git clone https://github.com/your-org/river-revival-parametric-study.git
cd river-revival-parametric-study
pip install -r requirements.txt
```

### Run
Open the notebook in Jupyter or VS Code:
```bash
jupyter notebook analysis.ipynb
```

Then run all cells (`Kernel → Restart & Run All`). Outputs are saved to `output/`.

> **Note:** All data is embedded directly in the notebook — no external JSON files are needed.

---

## References
- Brown, R. M., et al. (1970). A Water Quality Index—Do We Dare? *Water and Sewage Works*, 117(10), 339–343.
- Central Pollution Control Board (CPCB). (2017). *Guidelines for Water Quality Monitoring*. MoEFCC, Govt. of India.
- Dhagey, J. (2022). Apli Kham: Ecological River Restoration as Placemaking. *Question of Cities*.
- Joint Action for Water (JAW). (2024). By Restoring India's Kham River, a City Revives Its Cultural Legacy.
- Karhade, V. R., et al. (2020). Environmental Impact Assessment of Anthropogenic Activities and Conceptual Restoration Strategy for Kham River. *Current World Environment*, 15(3). DOI: [10.12944/CWE.15.3.31](http://dx.doi.org/10.12944/CWE.15.3.31)
- Millennium Post. (2025). *Reviving India's Rivers*.
- Shin, J., Salunkhe, M., & Kustar, A. (2024). Restoration of the Kham River Is Reviving a Cultural Legacy. *World Resources Institute (WRI)*.
- WRI Ross Center Prize for Cities. (2023–2024). *Kham River Restoration Initiative Finalist Case Study*.
