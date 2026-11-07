# Public claims ledger

This ledger separates the submitted course analysis from the corrected panel
used by the interactive. It is the release checklist for public numbers and
language.

## Scope and correction

| Claim | Public value | Source |
|---|---:|---|
| Metro areas | Indianapolis, Nashville, New Orleans, Philadelphia, Tampa Bay | `data/analysis_ready.csv`; validated by `scripts/build_site_data.py` |
| Years | 2015–2022 | `site/data/panel.json` → `meta.years` |
| Source panel | 1,113 ZIP-years | `site/data/panel.json` → `meta.sourceRows` |
| Corrected panel | 1,105 ZIP-years | `site/data/panel.json` → `meta.mappedRows` |
| Rows removed | 8 exact cross-metro duplicates | `site/data/panel.json` → `meta.removedDuplicateRows` |
| Canonical assignments | ZIP 37076 → Nashville; ZIP 70122 → New Orleans | `site/data/panel.json` → `meta.metroCorrections` |

The submitted course notebook remains unchanged. The static-site generator
checks that the eight removed rows are exact numeric duplicates apart from the
metro label before applying the two canonical geography assignments.

## Submitted course results

These values describe the original 1,113-row course panel and must be labeled
as the course-notebook results when quoted:

| Test | Course-notebook result |
|---|---:|
| H1 | beta = 0.1366; HC3 SE = 0.0451; one-sided p = 0.0012; about +0.27 pp per +1 SD |
| H2 | Joint F = 2.8447; p = 0.0231 |
| H3 | Q4 - Q1 = +0.3741 pp; p = 0.2075 |

Primary record: `notebooks/phase3_hypothesis_testing.ipynb`. Supporting course
documentation is retained in the local course-project archive.

## Corrected interactive results

These values are regenerated from `data/analysis_ready.csv` after the mapping
correction and are the only analysis values used in the public interactive:

| Claim | Corrected value | Generated key |
|---|---:|---|
| H1 coefficient | 0.1373 | `study.h1.beta` |
| H1 HC3 SE | 0.0454 | `study.h1.hc3Se` |
| H1 one-sided p | 0.0013 | `study.h1.oneSidedP` |
| H1 effect per +1 SD PC1 | +0.276 percentage points | `study.h1.effectPerSd` |
| H1 R-squared | 0.666 | `study.h1.rSquared` |
| H1 N | 1,105 | `study.h1.n` |
| H2 joint test | F = 2.7024; p = 0.0293 | `meta.h2JointF`, `meta.h2JointP` |
| H3 Q4 - Q1 | +0.357 percentage points; p = 0.2308 | `study.h3` |
| H3 N | 1,102 | `study.h3.n` |
| Mean next-year rent growth | 6.70% | `study.context.meanRentGrowth` |
| PC1 variance explained | 13.5% | `meta.pc1VariancePct` |
| Pre-COVID mean growth | 4.31% | `study.context.preCovidMeanGrowth` |
| 2020–2021 mean growth | 11.93% | `study.context.covidPeriodMeanGrowth` |

Generated record: `site/data/panel.json`. Producer:
`scripts/build_site_data.py`.

## Copy boundary

- Allowed: **associated with**, **predicts**, **precedes**, **signal**, and
  **supported under the specified model**.
- Not allowed: claims that Yelp language, restaurant vocabulary, or business
  density **causes** rent growth or neighborhood change.
- The ZIP 46037 opening is an illustrative sequence, not a representative case
  and not causal evidence.
- The +0.276 pp estimate is compared with 6.70% mean growth so statistical
  reliability is not presented as practical dominance.
- H1 and H2 are supported under their specified models. H3 is not supported.
- The course result and corrected interactive result must never be blended into
  a single unlabeled statistic.

## Verification commands

```bash
python scripts/build_site_data.py
python -m unittest discover -s tests -v
node --check site/app.js
```

Regeneration should leave `site/data/panel.json` and
`site/data/zcta.geojson` byte-for-byte unchanged.
