# Frozen preregistration: Yelp-language transportability

**Protocol ID:** `yelp-transportability-2026-11-07-v1`  
**Assignment:** `yelp-transportability-prereg-1`  
**Frozen:** 2026-11-07, before new outcome analysis  
**Status:** planned, unrun, pending protocol and rights review  
**Input hash:** `data/analysis_ready.csv` SHA-256
`b2b81fbc2a26141fe04b61a474de488b0cb5c28c9f850b1e2235656ef2fb0568`

This document authorizes no experiment by itself. It freezes the plan to be
reviewed. The historical notebooks and full-panel coefficients are development
knowledge; every row's outcome has already been available to the course team.
Results under this protocol must be called retrospective validation, never a
fresh holdout or confirmatory evidence.

## PR-01 — Question and intended decision

**Question:** Does a fixed 30-term Yelp review-language representation add at
least a small, reliable improvement in next-year ZIP-level rent-growth
prediction over rent-history and data-coverage features when transported to
later years and to a metro absent from training?

**Decision:**

- retain language as a coverage-qualified exploratory monitoring feature only
  if it meets the joint success rule in PR-10;
- otherwise reject the transportability claim and present the failure pattern;
- never use the score as a gentrification detector, causal estimate, resident-
  level classification, or operational allocation signal.

## PR-02 — Frozen sample and unit

- Unit: ZIP × predictor year.
- Predictor year: 2015–2022.
- Outcome: `next_year_rent_yoy_change`, the percentage change in annualized ZORI
  from year *t* to *t + 1* already stored in the derivative.
- Geography: Indianapolis, Nashville, New Orleans, Philadelphia (`Philly MSA`
  in data), and Tampa Bay.
- Source rows: 1,113.
- Corrected analysis rows: 1,105 after removing eight exact duplicate metro
  assignments using the repository's existing rules: 37076 → Nashville and
  70122 → New Orleans.
- No outcome trimming or winsorization.
- No new rows, fields, data downloads, geocoding, or outcome refresh.

The main analysis uses all corrected rows. Sensitivity subsets are specified in
PR-09. Sample changes require a dated deviation before outcomes are recomputed.

## PR-03 — Outer evaluation tasks

### A. Expanding out-of-time evaluation

Generate one prediction per row in each test year:

| Test predictor year | Training predictor years | Train rows | Test rows |
| ---: | --- | ---: | ---: |
| 2020 | 2015–2019 | 549 | 153 |
| 2021 | 2015–2020 | 702 | 200 |
| 2022 | 2015–2021 | 902 | 203 |

All preprocessing and model fitting restart within each fold. Results are
reported by test year and pooled across the 556 out-of-time predictions.

### B. Leave-one-metro-out evaluation

Hold out each metro, fit on the other four across all years, and predict every
row in the held-out metro:

| Held-out metro | Train rows | Test rows | Held-out ZIPs |
| --- | ---: | ---: | ---: |
| Indianapolis | 924 | 181 | 38 |
| Nashville | 949 | 156 | 29 |
| New Orleans | 1,053 | 52 | 14 |
| Philadelphia | 820 | 285 | 68 |
| Tampa Bay | 674 | 431 | 89 |

No random row-level cross-validation is permitted. ZIP-year rows from an outer
test fold may not influence preprocessing, model selection, or imputation.

## PR-04 — Predictors available at year t

### Baseline features

The strong baseline uses only information available in predictor year *t*:

- `year` as a centered numeric trend;
- `log1p(avg_rent)`;
- `rent_yoy_change`;
- an indicator that current-year rent growth is missing;
- `log1p(total_reviews)`;
- `rent_obs_count / 12`;
- `log1p(total_food_businesses)`; and
- `gentrify_density`, labeled business-category composition rather than a
  language feature.

The baseline intentionally excludes metro fixed effects so the same model can
be applied to an unseen metro. It excludes static ZIP identifiers, future rent
fields, `next_year_*` fields, precomputed language scores, and any feature
selected after outcome inspection.

Missing `rent_yoy_change` is imputed with the training-fold median and paired
with the missing indicator. All other listed fields must be present; otherwise
the fold stops and is reported as a protocol failure.

### Language features

The candidate adds exactly one training-derived index from the 30 existing
`kw_*_freq` columns. The vocabulary is fixed by the course project; no term is
added, removed, merged, stemmed, weighted, or screened against outcomes.

## PR-05 — Leakage-free language index

For every outer fit, and independently inside every inner model-selection fold:

1. compute each keyword's mean and population standard deviation on training
   rows only;
2. fail the fold if a training keyword has zero variance;
3. standardize training and test values with those training statistics;
4. fit one-component PCA on training rows only;
5. orient PC1 so the sum of its 30 training loadings is nonnegative;
6. transform test rows using the frozen training scaler/loadings; and
7. standardize the resulting PC1 score for the predictive model using the
   training score mean/standard deviation only.

The precomputed full-panel `gentrify_pca_score` and
`gentrify_language_score` are prohibited as candidate inputs. PCA variance
explained and loadings are descriptive representation diagnostics, not outcome
evidence.

## PR-06 — Models and inner selection

Three prediction rules are compared:

1. **Persistence diagnostic:** predict `rent_yoy_change`; where missing, use the
   training median. This is reported but is not the primary comparator.
2. **B — baseline ridge:** PR-04 baseline features.
3. **L — language ridge:** the identical baseline plus training-only PC1.

All continuous model features are standardized with training statistics. Ridge
uses an unpenalized intercept and candidate penalties
`[0.01, 0.1, 1, 10, 100]`.

- In each out-of-time outer fold, select the penalty by rolling-origin inner
  validation using the latest feasible training years, with at least two inner
  validation years. No inner fold may train on a year later than its validation
  year.
- In each leave-one-metro-out outer fold, select the penalty by inner
  leave-one-training-metro-out validation across the four available training
  metros.
- Refit the chosen model on the complete outer training fold.
- Select B and L penalties separately using mean inner-fold MAE. Ties within
  `1e-12` choose the larger penalty.

Every inner fold must refit its own imputer, scaler, PCA, and ridge. Hyperparameter
selection may not use pooled full-panel results or an outer test fold.

## PR-07 — Estimands and metrics

The primary estimand is paired incremental absolute error:

`delta_MAE = MAE(L) - MAE(B)`

Negative values favor language. Also report relative improvement:

`relative_MAE_gain = (MAE(B) - MAE(L)) / MAE(B)`

Primary reporting:

- pooled out-of-time MAE and paired delta;
- MAE and paired delta for each test year;
- MAE and paired delta for each held-out metro;
- median relative MAE gain across the five metro folds.

Secondary metrics, always reported without changing the decision:

- RMSE and paired RMSE delta;
- mean signed error;
- persistence-diagnostic MAE;
- test-row and unique-ZIP denominators; and
- training-only PCA loading stability (pairwise absolute cosine similarity
  after the frozen sign rule).

No p-value for a regression coefficient is a transportability endpoint.

## PR-08 — Clustered uncertainty

Use a paired ZIP-cluster bootstrap with 2,000 replicates and seed `5304`.

- Out-of-time pooled: within each metro, sample ZIPs with replacement and keep
  all test-year rows belonging to each sampled ZIP; compute paired metric
  differences on the combined sample.
- Per-year: sample test ZIPs with replacement, stratified by metro.
- Per-metro: sample held-out ZIPs with replacement and retain all their years.
- Report percentile 95% intervals for delta MAE and delta RMSE.

Do not use metro-cluster asymptotics: there are only five highly imbalanced
metros. The five leave-one-metro-out point estimates are themselves the main
geographic stability display. New Orleans has only 14 held-out ZIPs, so its
interval must be labeled low precision.

## PR-09 — Prespecified sensitivities and representation checks

Run each as a labeled sensitivity without altering the primary model or rule:

1. minimum `total_reviews` at 20, 50, and 100;
2. full rent coverage (`rent_obs_count == 12`) versus incomplete coverage;
3. exclude the 56 rows with zero counts for every vocabulary term;
4. alternative index: the unweighted mean of the 30 training-standardized
   keyword frequencies, with no outcome-based weighting;
5. remove `gentrify_density` from both B and L to ensure the comparison is not
   contingent on the course project's category label; and
6. report PCA loading stability; flag a pair of outer folds as unstable when
   absolute cosine similarity is below 0.80.

Sensitivity results cannot upgrade a primary failure. They may narrow a claim
to “coverage-conditional” only when the primary result is inconclusive and the
same prespecified threshold behaves consistently in both transfer tasks.

## PR-10 — Frozen decision rules

The language signal is labeled **transportable within this five-metro panel**
only if all conditions hold:

1. pooled out-of-time relative MAE gain is at least 2%;
2. the paired 95% bootstrap interval for pooled out-of-time delta MAE is wholly
   below zero;
3. language is no more than 5% worse in MAE in every individual test year;
4. at least four of five metro folds have delta MAE at or below zero;
5. median relative MAE gain across metro folds is at least 2%; and
6. no metro fold is more than 10% worse in MAE.

Outcome labels otherwise follow these rules:

- **coverage-conditional:** primary result is inconclusive, a prespecified
  coverage threshold meets the analogous rules in both tasks, and denominators
  remain disclosed;
- **non-transportable:** either pooled primary comparison favors B, any year is
  more than 5% worse, at least two metros worsen, or any metro is more than 10%
  worse;
- **inconclusive:** none of the above, including wide intervals or an executable
  fold failure.

The 2% gain is the smallest effect judged worth the added platform-data
dependency. It is a decision threshold, not a claim that 2% is economically or
policy significant.

## PR-11 — Required adverse and null reporting

The results artifact must retain:

- every year and metro cell, including null/adverse cells;
- denominator and coverage distribution for every cell;
- bootstrap intervals even when they cross zero;
- failures caused by zero variance, missing fields, singular fits, or too few
  clusters;
- loading-instability warnings;
- all prespecified sensitivity results; and
- a machine-readable record of outer predictions sufficient to recompute
  metrics, subject to the rights gate.

The write-up may not explain away a failed metro as “small sample” without
retaining it in the decision. It may not describe H3 or the old full-panel H1
as independent corroboration.

## PR-12 — Interpretation boundary

Allowed result language:

- “improved/did not improve retrospective next-year rent-growth prediction”;
- “transported/did not transport across the tested years/metros”; and
- “performance was conditional on the prespecified review-coverage threshold.”

Prohibited language:

- causal effects of Yelp language on rent;
- detecting, scoring, or forecasting “gentrification” as a social condition;
- resident demographic inference;
- national, rural, neighborhood-block, or real-time generalization;
- a fresh holdout or confirmatory claim; and
- operational deployment for housing, lending, investment, enforcement, or
  community resource allocation.

## PR-13 — Reproducibility and execution budget

- Use the existing pinned Python environment; no installation, paid inference,
  LLM call, GPU, or fresh data collection.
- Keep generated predictions/results out of the live site until review.
- Record Python/package versions, input hash, code commit, random seed, fold
  membership, selected penalties, and exact commands.
- Expected computation is CPU-only and small. Stop rather than create large
  caches or environments because the disk had roughly 219–221 MiB free during
  preregistration and temporarily refused tiny writes.
- Before execution, add automated assertions that every outer and inner
  preprocessor/model fit excludes its corresponding test indices.

## PR-14 — Visitor interaction after a successful evidence gate

A later essay change, separately reviewed, must let visitors inspect:

- the year × metro delta-MAE matrix;
- baseline, language, and persistence errors for a selected cell;
- coverage thresholds and changed denominators;
- training-fold PCA loadings and stability flags; and
- the frozen decision outcome with adverse cells visible.

It must label the accepted course association separately from the retrospective
transport study. A sortable coefficient list or animated map alone would not
satisfy the interaction requirement.

## PR-15 — Deviations and stopping

Before outcome execution, any change is appended below with date, reason, and
expected consequence. After outcome execution begins, no change may replace the
frozen analysis; modified analyses are deviations and exploratory.

Stop and return to protocol review if:

- data hash or schema differs;
- original Yelp license terms cannot be verified for the intended artifact;
- required Zillow attribution is not approved for later publication;
- an inner/outer leakage assertion fails;
- fewer than 10 held-out ZIP clusters remain in a primary metro fold; or
- disk capacity prevents a clean, reproducible run.

## Deviation log

None. Protocol is unrun.
