# Decision brief — P2 publication gate

**Project:** The Brunch Index  
**Date:** 2026-07-19  
**Governing spec:** `/Users/alihasan/Documents/Codex/project-specs/SPEC_YELP_INTERACTIVE.md`  
**Repo:** `/Users/alihasan/Documents/Codex/2026-07-18/read-strategy-handoff-md-and-readme/yelp-gentrification-rent`

## Decision requested

Ali must make the final `publish under my name` decision. Please review the prose voice and approve or decline both public actions:

1. Deploy `site/` to Vercel as the production interactive.
2. Push the P2 repository changes and add the live/source cross-link to the public portfolio at `/Users/alihasan/Downloads/Career Directory/portfolio-site`.

No deployment, public repository push, or portfolio mutation has been made for P2.

## What is ready

- Opening ZIP story grounded in generated panel values.
- Existing five-metro choropleth, year slider, keyboard-accessible ZIP selection, and twin curves.
- Interactive 30-term lexicon sortable by PCA loading, raw next-year correlation, and review frequency.
- Effect-size panel comparing the generated `+0.276 pp` estimate with `6.70%` mean growth, plus the `13.5%` PCA, COVID-period, and fixed-effects context.
- Method appendix with H1–H3 results, limitations, provenance, and live notebook links.
- Deterministic generator for all displayed numbers, a human-readable pipeline notebook, regression tests, pinned dependencies, inert CI workflow, and an interview explainer.
- Portfolio copy is drafted at `docs/PORTFOLIO_ENTRY.md`; the live URL remains intentionally blank until deployment.

## Evidence opened and verified

- `python3 scripts/build_site_data.py` regenerated both extracts byte-for-byte:
  - `panel.json`: `f1f96c4aac4f62a6c6ff4ccdb140153bdc7b99ba1d7ece6ace65235b1c36bb49`
  - `zcta.geojson`: `bcd2a843b1366e48e84d74be509188de38f0633cc28c961351dad8c6a27bf68a`
- `python3 -m unittest discover -s tests -v`: 7/7 passing.
- `/opt/anaconda3` Python 3.8 notebook kernel executed `notebooks/site_data_pipeline.ipynb` successfully.
- `node --check site/app.js`, `jq empty`, and `git diff --check` passed.
- Browser QA at 1440 px and 390 px: no horizontal overflow, no console warnings/errors, working lexicon sorting and section deep links.
- Local mobile-sized navigation load: 72 ms; static payload is about 657 KiB.
- All four GitHub/notebook links and the Yelp dataset link returned HTTP 200.
- Public-copy scans found no stale metros, causal claims, gradients, credential strings, or common secret patterns.

## Editorial and analytical choices to review

- Hook: ZIP `46037` in Indianapolis moves from PC1 `-0.11` in 2019 to `+1.63` in 2020; its next-year rent-growth measure moves from `3.20%` to `10.66%`. It is framed as an opening observation, not a representative case or causal example.
- Headline tone: “A real signal. A modest one.” The panel presents statistical reliability without implying practical dominance.
- Corrected public panel: eight exact cross-metro duplicate assignments are removed, leaving 1,105 ZIP-years. The original 1,113-row course notebook remains linked and its original statistics remain documented.
- H1/H2 are described as supported under the specified models; H3 is visibly reported as not supported.

## Remaining risks

- The `<2s` result is verified locally, not from a real mobile network. Production performance must be checked after Vercel deployment.
- The hook is illustrative and selected for narrative clarity; the copy explicitly avoids treating it as causal proof.
- The analysis remains observational, limited to five Yelp metros, and based on a first component explaining 13.5% of keyword variance.
- The automated Claude gate reviewer was not invoked because `/Users/alihasan/Documents/Codex/project-specs/gates/STOP` is present. This personal publication gate requires Ali’s own words regardless.

## Acceptance coverage

- README/site metros and numbers agree: generated values plus regression tests.
- Under 2 seconds on mobile: local browser QA passed; production check remains after approval.
- One script regenerates every chart number: `scripts/build_site_data.py`.
- Modest effect shown without hedging or inflation: dedicated strength panel.
- No causal claim: automated public-copy test plus repository scan.
- P2 deployment and portfolio cross-link: deliberately waiting on this gate.

