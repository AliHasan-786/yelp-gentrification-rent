# Predicting Rent Growth from Yelp Gentrification Signals

**Can the language of Yelp reviews predict neighborhood rent growth?**

This project investigates whether gentrification-linked language patterns in Yelp restaurant reviews — words like "artisanal," "craft," "farm-to-table" — predict next-year rent growth across 5 major U.S. metros, after controlling for baseline rent levels, review volume, and metro/year fixed effects.

## Research Questions

1. Does a PCA-derived gentrification language score significantly predict next-year rent growth?
2. Does the relationship between gentrification density and rent growth vary across metros (heterogeneous effects)?
3. Do ZIP codes in the top language-score quartile have meaningfully higher rent growth than bottom-quartile ZIPs?

## Methodology

- **Data:** Yelp Academic Dataset (~7M reviews) merged with Zillow ZORI rent indices across ZIP codes in Los Angeles, New York, Chicago, San Francisco, and Washington D.C. (2015–2022)
- **Feature engineering:** 30-keyword gentrification lexicon; keyword frequencies per ZIP-year aggregated from review text
- **Composite score:** PCA on standardized keyword frequencies — PC1 captures the shared variance across co-occurring gentrification terms, avoiding the noise of equal-weight averaging
- **Models:** OLS with heteroskedasticity-robust (HC3) standard errors and metro + year fixed effects throughout
- **Hypothesis tests:**
  - H1: t-test on PCA score coefficient (α = 0.05, two-tailed)
  - H2: Joint F-test on density × metro interaction terms
  - H3: t-test on Q4 dummy coefficient with Q1 as reference (α = 0.05, one-tailed)

## Key Findings

- The PCA-based gentrification language score is a statistically significant positive predictor of next-year rent growth (H1 supported)
- Gentrification density effects are heterogeneous across metros — the relationship is not uniform nationally (H2 supported)
- ZIP codes in the highest language-score quartile show significantly greater rent growth than the lowest quartile (H3 supported)

## Notebooks

| Notebook | Description |
|---|---|
| `notebooks/phase1_data_collection.ipynb` | Data collection, ZIP-level merging of Yelp + Zillow, metro filtering, cleaning |
| `notebooks/phase2_eda.ipynb` | Exploratory analysis: coverage, missingness, rent trends, keyword correlations, initial OLS |
| `notebooks/phase3_hypothesis_testing.ipynb` | PCA construction, hypothesis testing (H1/H2/H3), robustness checks |

## Data

`data/analysis_ready.csv` — ZIP-year panel dataset (post-cleaning) with:
- Rent growth metrics (from Zillow ZORI)
- 30 keyword frequency columns
- `gentrify_density` (reviews/km²), `avg_rent`, `log_total_reviews`
- Metro and year identifiers

Raw Yelp JSON data is not included due to size (available via [Yelp Academic Dataset](https://www.yelp.com/dataset)).

## Stack

Python · pandas · scikit-learn (PCA) · statsmodels (OLS/WLS) · matplotlib · seaborn

## Course

DS 5304 — Foundations of Data Science (Spring 2026)
