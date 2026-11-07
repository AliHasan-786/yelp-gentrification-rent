# Decision brief — production release

**Project:** The Brunch Index

**Date:** 2026-11-07

**Assignment:** `yelp-release-1`

**Governing spec:** `/Users/alihasan/Documents/Codex/project-specs/SPEC_YELP_INTERACTIVE.md`

**Repo:** `/Users/alihasan/Documents/Codex/2026-07-18/read-strategy-handoff-md-and-readme/yelp-gentrification-rent`

## Release decision

The accepted interactive is released and production-verified at
[the-brunch-index.vercel.app](https://the-brunch-index.vercel.app). The Vercel
deployment is `dpl_2AcEpJbcHSk8gFcrBAmbmpBpfoU2`; its immutable URL is
`https://site-naur06n0h-ali-hasans-projects-734a68d1.vercel.app`, and the exact
deployed source revision is `dcab3385222f79d6ae28a87568cd9cc17d8d2e03`.

Anonymous production access is enabled. Vercel SSO protection was disabled for
this project after it redirected anonymous visitors to login; Git-fork
protection remains enabled. No portfolio-hub files were edited.

## Release set

- Opening ZIP story grounded in generated panel values.
- Five-metro choropleth, 2015–2022 slider, keyboard-accessible ZIP selection,
  and twin language/rent curves.
- Interactive 30-term lexicon sortable by PCA loading, raw next-year
  correlation, and review frequency.
- Effect-size panel comparing `+0.276 pp` with `6.70%` mean growth, plus the
  `13.5%` PCA, COVID-period, and fixed-effects context.
- Method appendix with H1–H3 results, limitations, provenance, and public
  notebook links.
- Deterministic generator, executable pipeline notebook, regression tests,
  pinned dependencies, inert CI workflow, and Ali-facing explainer.
- Public integration metadata at `portfolio.json` and a representative
  1200 x 630 thumbnail at `site/assets/the-brunch-index-thumbnail.png`.

## Production verification on 2026-11-07

- Anonymous desktop QA at 1440 x 1000: all five sections rendered, metro/year/
  ZIP state changed correctly, all lexicon sort modes worked, and the console
  had zero warnings or errors.
- Fresh 390 x 844 headless browser context with an empty cache and unique query:
  no horizontal overflow; `DOMContentLoaded` 250 ms; `loadEventEnd` 256 ms;
  final first-party resource 302 ms; 184,141 transferred bytes.
- The mobile timing passes the `<2s` acceptance threshold on the actual
  production URL. It was measured on the local unthrottled network and is not
  represented as simulated cellular performance.
- Document, CSS, JavaScript, panel JSON, and geography GeoJSON returned 200.
- All three public notebook links and the repository link returned 200 in a
  real browser.
- Mobile metro/year control, ZIP details, deep links, and review-frequency sort
  were exercised successfully; the console had zero warnings or errors.
- `python3 -m unittest discover -s tests -v`, `node --check site/app.js`, JSON
  parsing, and `git diff --check` passed for the release record.

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

## Portfolio copy

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

## Residual interpretation limits

- The opening ZIP is illustrative, not representative or causal.
- The analysis covers five Yelp metros and PC1 explains 13.5% of keyword
  variance.
- The stopped reviewer-loop automation remains out of scope and must not be
  invoked.

## Recommendation

The project is ready for the portfolio-hub owner to integrate using
`portfolio.json`, the verified live URL, and the supplied thumbnail. No project
release blocker remains.
