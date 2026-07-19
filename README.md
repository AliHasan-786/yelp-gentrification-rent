# Predicting Rent Growth from Yelp Gentrification Signals

**Can the language of Yelp reviews predict neighborhood rent growth?**

This project investigates whether gentrification-linked language patterns in Yelp restaurant reviews — words like "artisanal," "craft," and "farm-to-table" — predict next-year rent growth across five Yelp Academic Dataset metro areas, after controlling for baseline rent levels, review volume, and metro/year fixed effects.

## Research Questions

1. Does a PCA-derived gentrification language score significantly predict next-year rent growth?
2. Does the relationship between gentrification density and rent growth vary across metros (heterogeneous effects)?
3. Do ZIP codes in the top language-score quartile have meaningfully higher rent growth than bottom-quartile ZIPs?

## Methodology

- **Data:** Yelp Academic Dataset (6.99M source reviews processed; 3.85M food-business reviews retained before the ZIP-year/Zillow merge) combined with Zillow ZORI rent indices across ZIP codes in Indianapolis, Nashville, New Orleans, Philadelphia, and Tampa Bay (2015–2022)
- **Feature engineering:** 30-keyword gentrification lexicon; keyword frequencies per ZIP-year aggregated from review text
- **Composite score:** PCA on standardized keyword frequencies — PC1 captures the shared variance across co-occurring gentrification terms, avoiding the noise of equal-weight averaging
- **Models:** OLS with heteroskedasticity-robust (HC3) standard errors and metro + year fixed effects throughout
- **Hypothesis tests:**
  - H1: one-sided test on the PCA score coefficient (α = 0.05; preregistered alternative β > 0)
  - H2: Joint F-test on density × metro interaction terms
  - H3: Q4-vs-Q1 coefficient test in an HC3-robust OLS model (α = 0.05)

## Key Findings

- The PCA-based gentrification language score is a statistically significant positive predictor of next-year rent growth (H1 supported: β = 0.1366, one-sided p = 0.0012)
- Gentrification density effects are heterogeneous across metros — the relationship is not uniform across the five-metro sample (H2 supported: joint F = 2.8447, p = 0.0231)
- The highest language-score quartile's controlled estimate is positive but not statistically significant relative to the lowest quartile (H3 not supported: +0.3741 percentage points, p = 0.2075)

## Interactive P1

`site/` contains the P1 working interactive: a static choropleth with metro controls, a 2015–2022 year slider, and a clickable ZIP drill-down comparing the PCA language score with next-year rent growth. It has no backend or runtime dependencies.

Every number and chart series in the interactive regenerates from `data/analysis_ready.csv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build_site_data.py
python -m http.server 8000 -d site
```

Then open <http://localhost:8000>. Dependency versions are pinned in `requirements.txt`.

The build produces:

| Extract | Contents |
|---|---|
| `site/data/panel.json` | PCA scores, ZIP-year chart series, metro-specific controlled slopes, and metadata |
| `site/data/zcta.geojson` | The 238 selected 2020 Census ZCTA boundaries, joined to the five analysis metros |

The compact boundary source and its Census TIGERweb provenance are documented in `data/geography/README.md`. Use `python scripts/build_site_data.py --refresh-geometry` to retrieve a fresh copy of the same 2020-vintage boundaries.

### Mapping correction

The committed CSV has 1,113 source rows, including eight exact cross-metro duplicate assignments: ZIP `37076` appears under both Nashville and Indianapolis, and ZIP `70122` under both New Orleans and Tampa Bay. The interactive pipeline validates that the duplicated numeric rows are otherwise identical, keeps the geographically correct assignments (Nashville and New Orleans), and maps 1,105 ZIP-years. On this corrected mapping panel, the H2 metro-interaction test remains significant (joint p = 0.0293, compared with p = 0.0231 in the original final-analysis notebook).

## Notebooks

| Notebook | Description |
|---|---|
| `notebooks/phase1_data_collection.ipynb` | Data collection, ZIP-level merging of Yelp + Zillow, metro filtering, cleaning |
| `notebooks/phase2_eda.ipynb` | Exploratory analysis: coverage, missingness, rent trends, keyword correlations, initial OLS |
| `notebooks/phase3_hypothesis_testing.ipynb` | PCA construction, hypothesis testing (H1/H2/H3), robustness checks |
| `notebooks/site_data_pipeline.ipynb` | Human-readable entry point for regenerating and validating the static P1 extracts |

## Data

`data/analysis_ready.csv` — ZIP-year panel dataset (post-cleaning) with:
- Rent growth metrics (from Zillow ZORI)
- 30 keyword frequency columns
- `gentrify_density` (share of food businesses in 14 gentrification-associated categories), `avg_rent`, and `total_reviews`
- Metro and year identifiers

The analysis notebooks derive `log_total_reviews` from `total_reviews` with `log1p`; it is not stored as a separate CSV column.

Raw Yelp JSON data is not included due to size (available via [Yelp Academic Dataset](https://www.yelp.com/dataset)).

## Stack

Python · pandas · scikit-learn (PCA) · statsmodels (OLS/WLS) · matplotlib · seaborn

## Course

DS 5304 — Foundations of Data Science (Spring 2026)
