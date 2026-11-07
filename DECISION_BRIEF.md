# Decision brief — P2 release candidate

**Project:** The Brunch Index

**Date:** 2026-11-07

**Assignment:** `yelp-release-candidate-1`

**Governing spec:** `/Users/alihasan/Documents/Codex/project-specs/SPEC_YELP_INTERACTIVE.md`

**Repo:** `/Users/alihasan/Documents/Codex/2026-07-18/read-strategy-handoff-md-and-readme/yelp-gentrification-rent`

## Decision requested

The portfolio coordinator should inspect and accept or return this release
candidate. On acceptance, the next milestone is to push the local P2 commits,
deploy `site/` to Vercel, verify production performance and links, and replace
the existing `yelp-rent` hub placeholder with the reviewed metadata and live
URL.

Ali's 2026-11-07 standing authorization covers routine pushes and portfolio
deployments after checks and coordinator review. No additional conversational
publication approval is required. This assignment itself stops at the local
release candidate, so no push, deployment, or hub edit has been made here.

## Release set

- Opening ZIP story grounded in generated panel values.
- Five-metro choropleth, 2015–2022 slider, keyboard-accessible ZIP selection,
  and twin language/rent curves.
- Interactive 30-term lexicon sortable by PCA loading, raw next-year
  correlation, and review frequency.
- Effect-size panel comparing `+0.276 pp` with `6.70%` mean growth, plus the
  `13.5%` PCA, COVID-period, and fixed-effects context.
- Method appendix with H1–H3 results, limitations, provenance, and notebook
  links.
- Deterministic generator, executable pipeline notebook, regression tests,
  pinned dependencies, inert CI workflow, and Ali-facing explainer.
- Public-safe integration metadata at `portfolio.json`.
- Representative 1200 x 630 thumbnail at
  `site/assets/the-brunch-index-thumbnail.png`.
- Course-versus-corrected metric provenance at `docs/CLAIMS_LEDGER.md`.

## Evidence verified on 2026-11-07

- `python3 scripts/build_site_data.py` regenerated both extracts byte-for-byte:
  - `panel.json`: `f1f96c4aac4f62a6c6ff4ccdb140153bdc7b99ba1d7ece6ace65235b1c36bb49`
  - `zcta.geojson`: `bcd2a843b1366e48e84d74be509188de38f0633cc28c961351dad8c6a27bf68a`
- `python3 -m unittest discover -s tests -v`: 8/8 passing.
- `notebooks/site_data_pipeline.ipynb` executed successfully with `nbconvert`.
- `node --check site/app.js`, JSON parsing, and `git diff --check` passed.
- Desktop and 390 px browser QA found no horizontal overflow and no console
  warnings or errors.
- Metro selection, year-slider state, ZIP detail rendering, deep links, and all
  three lexicon sort modes were exercised successfully.
- Local 390 px navigation load was 9 ms. The static site payload remains about
  657 KiB; the spec's `<2s` requirement still needs production verification.

## Claims to preserve

- Correct metro list: Indianapolis, Nashville, New Orleans, Philadelphia, and
  Tampa Bay.
- The submitted course notebook is the original 1,113-row record: H1 beta
  `0.1366`, H2 p `0.0231`, H3 p `0.2075`.
- The public interactive removes eight exact duplicate metro assignments and
  reports corrected-panel results on 1,105 ZIP-years: H1 beta `0.1373`, H1
  one-sided p `0.0013`, H2 p `0.0293`, and H3 p `0.2308`.
- The analysis is observational. Public language may say **associated with**,
  **predicts**, or **precedes**, never that Yelp language causes rent growth.

## Final prose for review

**Title:** The Brunch Index

**One-line description:** Interactive data essay on whether Yelp language
precedes next-year ZIP-level rent growth across five metros.

**Primary metric:** +0.276 pp per +1 SD PC1 on the corrected
1,105-ZIP-year panel.

**Portfolio paragraph:** An interactive data essay testing whether
gentrification-coded language in Yelp restaurant reviews precedes next-year
ZIP-level rent growth across Indianapolis, Nashville, New Orleans,
Philadelphia, and Tampa Bay. The deterministic Python pipeline reconstructs a
30-keyword PCA score, refits fixed-effects models with HC3 robust inference,
validates Census ZIP geometry, and powers a dependency-free choropleth, ZIP
drill-down, lexicon explorer, and effect-size explainer. The corrected
1,105-row mapping panel finds a statistically reliable but modest association:
about +0.276 percentage points per score standard deviation against a 6.70%
mean, with the COVID-era shock, non-significant quartile result, and limits of
observational evidence shown directly.

## Remaining release risks

- Production `<2s` mobile performance and public links cannot be verified until
  deployment.
- The opening ZIP is illustrative, not representative or causal.
- The analysis covers five Yelp metros and PC1 explains 13.5% of keyword
  variance.
- Provider authentication or an app-enforced runtime prompt could still block
  a release command; it must be reported rather than bypassed.
- The stopped reviewer-loop automation remains out of scope and must not be
  invoked.

## Recommendation

Accept the copy and local release assets as the P2 candidate. Proceed to the
bounded release milestone under standing authorization, then update
`portfolio.json.demoUrl`, production-check the site, and hand the verified live
URL plus metadata to the hub owner.
