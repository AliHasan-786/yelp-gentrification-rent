# Transportability protocol amendment

**Protocol:** `yelp-transportability-2026-11-07-v1`  
**Amendment:** `yelp-transportability-2026-11-09-v1.1`  
**Date:** 2026-11-09  
**Status:** retrospective validation planned and unrun; ready for execution
review only after the source-rights gate is cleared

## Scope and precedence

This is a dated amendment, not a replacement for the frozen v1
preregistration. The original file remains unchanged. This amendment closes
execution ambiguities in PR-03B and PR-06 before any outcome run. It supersedes
only the geographic outer-fold construction and the exact inner-selection
procedure described below. The predictors, estimands, sensitivities, numerical
success thresholds, adverse/null reporting, and retrospective-evidence label
remain unchanged.

No panel outcomes were read, modeled, or recomputed while preparing this
amendment. The implementation artifact constructs folds from row ID, ZIP,
metro, and year metadata only and implements decision rules from supplied
metrics.

The machine-readable authority for execution is
`docs/research/transportability_protocol_v1_1.json`. If this narrative and the
machine-readable record disagree, execution stops for protocol review; neither
record may be changed after outcome inspection.

## Exact outer folds

The primary out-of-time task has three folds, with test years 2020, 2021, and
2022. For test year `T`:

- training rows satisfy `year < T`;
- test rows satisfy `year == T`; and
- no test row may influence imputation, standardization, PCA, sign orientation,
  penalty selection, or fitting.

The geographic task is hardened from five all-years leave-one-metro-out folds
to 15 metro-time cells: each of five held-out metros crossed with test years
2020, 2021, and 2022. For held-out metro `M` and test year `T`:

- training rows satisfy `metro != M and year < T`; and
- test rows satisfy `metro == M and year == T`.

The earlier all-years geographic description could allow later-year training
rows to influence predictions for earlier held-metro years. The metro-time
definition removes that temporal leakage path. After predictions are frozen,
the three valid year cells for a held-out metro are concatenated to compute
that metro's required aggregate metrics. All 15 cells remain visible in the
execution record, including invalid, null, and adverse cells.

Outer time folds require at least 20 test rows and 10 test ZIP clusters. Each
metro-time cell requires at least five test rows and five test ZIP clusters;
the three-cell aggregate for a metro requires at least 10 distinct test ZIP
clusters. A failed minimum does not remove a cell. It marks the cell
`not_executable`, preserves its denominator and reasons, and prevents a success
declaration that requires it.

## Exact inner folds and model selection

Every executable outer fold has exactly two rolling-origin inner validation
folds. If its outer test year is `T`, validation years are `T-2` and `T-1`.
For each validation year `V`:

- inner training rows are outer-training members with `year < V`;
- inner validation rows are outer-training members with `year == V`; and
- for a metro-time outer fold, neither set can contain the held-out metro.

Thus inner validation never sees an outer test row, a future year, or a
held-out-metro row. Every inner fold independently fits the training median
imputer, continuous-feature scaler, 30-keyword scaler, one-component PCA,
deterministic sign orientation, PC1 scaler, and ridge model. No fitted object is
shared across inner folds, between baseline and language candidates, or from a
full panel.

An inner fold requires at least three distinct training years, 100 training
rows, 20 training ZIP clusters, 20 validation rows, and 10 validation ZIP
clusters. Each ridge candidate is scored by the unweighted arithmetic mean of
the two validation MAEs. A candidate is invalid if either required score is
missing, comes from an ineligible fold, is nonfinite, or is negative. Baseline
and language penalties are selected separately from
`[0.01, 0.1, 1, 10, 100]`; scores tied within `1e-12` choose the larger penalty.
If no candidate is valid, the outer cell is retained as `not_executable`.

## Pre-outcome invariant clarification

Execution review on 2026-11-09 found three helper contracts that were not
strict enough. This clarification was recorded before any outcome access. It
does not change the v1 protocol or any numerical decision threshold.

Penalty selection requires exactly two distinct eligible inner-fold records.
Their fold IDs and validation years must match the declared outer fold and its
two frozen rolling-origin years.
Every model must supply scores for all and only the frozen ridge penalties.
Unknown, missing, duplicate, Boolean, nonfinite, or malformed candidate and
fold identities fail closed. A candidate with an invalid fold score remains in
the audit record but cannot be selected.

Decision inputs carry immutable identities. The pooled out-of-time metric must
declare scope `pooled_out_of_time`, the three cell IDs `time-2020`,
`time-2021`, and `time-2022`, and eligibility. Year metrics require one
eligible record for each of those three cells. Metro metrics require one
eligible aggregate for each configured metro. Shuffled input order is allowed.
Missing, duplicate, extra, unknown, inconsistent, or ineligible identities
cannot satisfy success. They produce an inconclusive decision unless a record
claiming a required identity contains evidence that meets a frozen adverse
rule. Unknown identities never count as required or adverse evidence.
Validation applies to the complete raw year and metro collections before any
record is filtered. An extra malformed record cannot disappear during identity
checking. MAEs and confidence interval endpoints must be finite integers or
floats. Boolean and other nonnumeric values are invalid. Numeric zero keeps the
existing null and adverse behavior.

The review-count sensitivities are exactly `reviews>=20`, `reviews>=50`, and
`reviews>=100`. All three results must be supplied. The helper reports every
threshold that passes both transfer tasks. If more than one passes, the primary
coverage-conditional label uses the first passing threshold in the frozen
ascending order. This picks the least restrictive passing threshold and keeps
the most rows. An unknown or incomplete threshold set cannot qualify. A
non-transportable primary result cannot be upgraded.

## Undefined values, uncertainty, and failures

Relative MAE gain uses `(MAE(B) - MAE(L)) / MAE(B)` only when baseline MAE is
greater than `1e-12`.

- If both MAEs are at most `1e-12`, relative gain is undefined. The cell is
  null: it counts as non-worse but cannot satisfy an improvement threshold.
- If baseline MAE is at most `1e-12` and language MAE is larger, relative gain
  is undefined and the language candidate is adverse.
- A negative or nonfinite MAE is invalid and retained as a failure record.

Paired uncertainty uses 2,000 ZIP-cluster bootstrap replicates with seed 5304.
At least 10 distinct ZIP clusters and all 2,000 finite replicates are required
for an interval. Otherwise the interval is unavailable, the point estimate and
failure reason remain visible, and transportability cannot be declared.

A language-only execution failure is adverse. A shared baseline/language
failure is inconclusive absent separate adverse evidence. Failures cannot be
dropped, converted to wins, or used to revise a rule. The same rule applies to
all prespecified cells.

## Frozen interpretation

PR-10's numerical rules are unchanged. A coverage-conditional label remains
available only when the primary result is inconclusive and the same
prespecified review-coverage threshold passes the analogous rules in both the
out-of-time and metro-time tasks. No sensitivity may upgrade a primary adverse
result.

Any later result must be labeled **retrospective validation with prior outcome
exposure**, not a fresh holdout or confirmatory test. This amendment makes no
claim that the language measure is transportable and does not authorize a
public release.

## Execution artifacts and gate

- Machine protocol: `docs/research/transportability_protocol_v1_1.json`
- Reusable outcome-free helpers: `scripts/transportability_protocol.py`
- Synthetic invariant tests: `tests/test_transportability_protocol.py`
- Source-rights evidence and decision:
  `docs/research/SOURCE_RIGHTS_EVIDENCE_2026-11-09.md`

Scientific execution review may now inspect a fully deterministic protocol.
Actual outcome execution and any new public derivative remain blocked until an
authorized reviewer resolves the active Yelp agreement term/entity and the
required Yelp publication review, and confirms the product-specific ZORI terms
for the intended artifact.
