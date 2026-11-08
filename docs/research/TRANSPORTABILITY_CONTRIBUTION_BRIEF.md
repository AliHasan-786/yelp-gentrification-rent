# Transportability contribution brief

**Assignment:** `yelp-transportability-prereg-1`  
**Audit cutoff:** 2026-11-07  
**Evidence stage:** planned and unrun  
**Protocol:** [`TRANSPORTABILITY_PREREGISTRATION_2026-11-07.md`](./TRANSPORTABILITY_PREREGISTRATION_2026-11-07.md)

## Useful question

Does a Yelp review-language index add practically useful next-year rent-growth
prediction beyond rent history and data-coverage baselines when it is applied to
later years or a metro absent from training?

The answer could help an urban-data analyst decide whether this kind of
platform-text signal deserves a place in a monitoring workflow, should be used
only as a coverage-qualified exploratory layer, or should be rejected as a
non-transportable artifact. It does **not** decide whether a neighborhood is
gentrifying, identify displacement, or support property, lending, enforcement,
or resource-allocation decisions.

## What changes beyond the course project

The accepted course analysis estimated a full-panel conditional association.
Its PCA normalization and loadings were fit on the same corrected panel later
used for inference, and the notebooks have already inspected year-, metro-, and
residual-level outcomes. Those results remain historical coursework/development
knowledge.

The proposed extension instead evaluates incremental prediction under two
explicit transfer tasks:

1. expanding out-of-time tests for 2020, 2021, and 2022 predictor years; and
2. five leave-one-metro-out tests.

Every scaler, imputer, PCA loading, index orientation, and model choice is fit
inside training data. The language model must beat a rent-history and coverage
baseline under predeclared practical and adverse-failure rules. Coverage and an
equal-weight index are planned sensitivities, not post-result rescue analyses.

Because every outcome in the derivative was used or inspected during the class
project, this is a **retrospective, protocol-locked validation**, not a fresh
holdout and not confirmatory evidence. A genuinely fresh test would require a
new, rights-cleared later Yelp snapshot and later ZORI outcomes; that collection
is outside this assignment.

## Current and closest related work

Sources below were reviewed on 2026-11-07. Publication/revision dates are given
so the audit can be reproduced without implying that the list is timeless.

| Source | Date | What it establishes | Gap left for this extension |
| --- | --- | --- | --- |
| Glaeser, Kim & Luca, [“Measuring Gentrification: Using Yelp Data to Quantify Neighborhood Change”](https://doi.org/10.3386/w24952) | 2018-08 NBER working paper; AEA P&P version 2018 | Yelp business entry and category change can precede housing-price and demographic change. | It does not test this 30-term review-language index against a rent-history baseline under later-year and unseen-metro transfer. |
| Glaeser, Luca & Moszkowski, [“Gentrification and Retail Churn: Theory and Evidence”](https://www.nber.org/papers/w28271) | 2020-12; revised 2023-02 | Yelp business coverage is selected and business opening/closure dates are imperfect; results vary by city and outcome. | Reinforces the need for geography-specific failures and coverage diagnostics rather than a pooled coefficient. |
| Olson et al., [“Reading the city through its neighbourhoods”](https://doi.org/10.1016/j.cities.2020.103045) | 2021 | Deep Yelp-review representations can describe neighborhood similarity and change. | Representation utility does not establish next-year rent prediction or transfer. |
| Amos, Maio & Mittal, [“Reviews in motion”](https://arxiv.org/abs/2202.09005) | 2022-02-18 | Yelp review recommendation status changes over time and differs with income/density, creating platform-measurement risk. | Motivates coverage sensitivities and prevents treating review text as a stable population measure. |
| Quayle, [“Restaurants, Reviews, and Residential Change”](https://theses-dissertations.princeton.edu/entities/publication/133aa262-0f1a-4049-9f36-e6839c9ed549) | 2025-04-10 senior thesis | A closely related Yelp/Zillow/ACS study links review/business measures to housing-price change through 2022. | Makes a generic “Yelp predicts housing” claim non-distinct; transport failure and incremental value are the contribution here. |
| Reades et al., [“The City as Text”](https://doi.org/10.1038/s44284-025-00314-x) | 2025 Nature Cities perspective | Current urban-text work emphasizes accidental-data bias, geographic context, and the distinction between language reflecting versus shaping change. | Supports a bounded predictive audit, not a causal or automated gentrification detector. |
| Delmelle & Nilsson, [“The Evolution of Real Estate Advertisement Language in Racially Changing Neighborhoods”](https://doi.org/10.1080/24694452.2025.2582615) | online 2025-11-24; journal issue 2026 | Text indicators vary across cities and time in another housing-language setting. | Uses real-estate advertisements and demographic change, not Yelp review language and next-year ZORI. |
| Roberts et al., [structured cross-validation](https://doi.org/10.1111/ecog.02881) | 2017 | Random folds can understate error when observations have temporal, spatial, or grouped dependence. | Supplies the evaluation principle; this protocol instantiates time and metro blocking for the present panel. |

No reviewed source establishes the exact proposed claim: that this fixed
30-term review-frequency representation improves next-year ZIP-level ZORI
prediction over a strong rent-history/coverage baseline in both later-year and
unseen-metro tests. That is a gap to test, not a novelty claim or a presumed
positive finding.

## Data and rights audit

### Frozen local derivative

- `data/analysis_ready.csv`, committed 2026-05-01.
- SHA-256: `b2b81fbc2a26141fe04b61a474de488b0cb5c28c9f850b1e2235656ef2fb0568`.
- 1,113 source rows; 1,105 after the repository's documented duplicate-metro
  correction; 238 ZIPs, five metros, predictor years 2015–2022.
- The derivative contains ZIP-year aggregates, keyword counts/frequencies,
  business aggregates, and rent measures. It contains no review text, user ID,
  review ID, or business ID.
- Raw Yelp JSON and raw Zillow downloads are not committed. This assignment
  performs no collection or download.

### Yelp

The course notebooks identify the [Yelp Open Dataset](https://business.yelp.com/data/resources/open-dataset/)
as the source and quote its academic-project purpose. On 2026-11-07 the official
page was reachable by a normal browser/search index but blocked automated text
retrieval, and no copy of the accepted Dataset License Agreement is committed.
The archived Yelp examples repository is Apache-2.0, but that code license does
not license the dataset.

Therefore this audit does not infer broad redistribution rights. The planned
study may analyze the already-committed aggregate locally, but a protocol
reviewer must check the original Yelp Dataset License Agreement before any new
public derivative or data file is released. No raw text, user-level data, or
new Yelp extract may be published under this plan.

### Zillow

The [ZORI methodology](https://www.zillow.com/research/methodology-zori-repeat-rent/)
describes a quality-adjusted, weighted repeat-rent index and intentional
smoothing. The [Zillow Terms of Use](https://www.zillow.com/corporate/terms-of-use/),
updated 2025-10-28 and reviewed 2026-11-07, say that displayed/distributed
derivatives of the terms' defined “Aggregate Data” require source attribution
on every page where the data appear, including the phrase “Data Provided by
Zillow Group.” The terms define that category in relation to Local-Info pages;
this audit cannot establish whether downloaded ZORI is governed only by that
clause or by additional product terms.

The live essay names Zillow ZORI in its method and footer, but does not use that
exact attribution phrase. The applicable ZORI terms and the attribution should
therefore be confirmed with the source owner before any future extension
publication. This assignment does not alter or redeploy the accepted site.

### Census geography and repository licensing

The existing map uses the U.S. Census Bureau's 2020 TIGERweb ZCTA layer and
records its endpoint/vintage in `data/geography/README.md`. The transport study
does not require new geometry. No repository-wide `LICENSE` file is present, so
the public repository should not be described as granting downstream reuse
rights beyond the source-specific terms above.

## Feasibility findings (outcome-blind)

The check `python3 -B scripts/check_transportability_feasibility.py` parses no
target values and reports only schema, missingness, coverage, and split sizes.

- All 30 keyword-frequency fields are complete; 56 rows have zero counts for
  all 30 terms.
- All 1,105 corrected rows have a future target, but 237 lack current-year rent
  growth. The baseline therefore needs training-only imputation plus a missing
  indicator rather than complete-case deletion.
- Only 51 of 238 ZIPs have all eight years. Repeated random row folds would mix
  ZIP histories and are prohibited.
- Metro coverage is highly uneven: 14 ZIPs/52 rows in New Orleans versus 89
  ZIPs/431 rows in Tampa Bay. Metro-average claims and five-cluster asymptotics
  would be misleading.
- Review thresholds remain feasible: ≥20 reviews has 1,058 rows/220 ZIPs; ≥50
  has 962/201; ≥100 has 891/190.
- The three out-of-time folds have 153, 200, and 203 test rows. All five
  leave-one-metro-out folds have at least 14 held-out ZIP clusters.

## What a later interaction must reveal

If the protocol is approved and run, the essay extension should expose the
transfer question rather than decorate a coefficient:

- a year × metro matrix of language-versus-baseline MAE deltas, retaining
  adverse and null cells;
- a coverage control that changes the eligible sample and denominator while
  keeping the frozen model comparison visible;
- a fold selector showing training-only PCA loadings and a loading-stability
  warning;
- a plain-language decision badge: transportable, coverage-conditional,
  non-transportable, or inconclusive under the frozen rules; and
- permanent labels separating course results, this retrospective extension,
  and any future genuinely unseen evaluation.

No interaction or live-site change is approved in the present assignment.

## Limits and next gate

This protocol cannot remove platform selection, ZIP-level aggregation,
measurement error, ZORI smoothing, unobserved confounding, or prior outcome
exposure. It evaluates predictive transfer within five Yelp-heavy metros only.
The next gate is human protocol and source-rights review. Only after approval
may an implementation compute outcome metrics, and any change after outcome
inspection must be logged as a dated deviation or labeled exploratory.
