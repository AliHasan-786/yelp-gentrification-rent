# The Brunch Index — explainer for Ali

This document is written for you, not as visitor-facing copy. Its job is to make the project easy to explain without opening the code.

## The 30-second version

The project asks whether gentrification-coded language in Yelp restaurant reviews contains an early signal of next-year ZIP-level rent growth. It combines Yelp review text and food-business metadata with Zillow's Observed Rent Index across five metros from 2015–2022. A PCA-based language score is a small but statistically reliable positive predictor after baseline rent, review volume, metro, and year controls. The effect is modest: one score standard deviation corresponds to about +0.276 percentage points of next-year rent growth against a 6.70% panel mean.

The public artifact turns that analysis into a static interactive essay: a hook ZIP, metro/year choropleth, ZIP drill-down, 30-word lexicon explorer, effect-size panel, and method appendix.

## Architecture

```text
data/analysis_ready.csv
        │
        ├── validate schema, five metros, 2015–2022, 30 keywords
        ├── remove 8 exact cross-metro duplicate assignments
        ├── standardize keyword frequencies → PCA PC1
        ├── refit H1, H2, H3 with HC3 robust errors
        ├── derive hook, lexicon ranks, effect-size context
        └── join committed 2020 Census ZCTA boundaries
                     │
                     ├── site/data/panel.json
                     └── site/data/zcta.geojson
                                  │
                                  └── vanilla HTML/CSS/JS + SVG
```

There is no backend. The browser downloads roughly 660 KiB of static JSON/GeoJSON, projects the selected metro's ZCTA polygons into SVG, and renders all interactions locally.

## Why the major decisions were made

### Why PCA?

The 30 terms occur at very different rates. Standardization prevents common words from dominating solely because of scale. PC1 then captures the largest shared direction of vocabulary variation. It explains 13.5% of total keyword variance: enough to be useful, not enough to call it a complete language model.

### Why fixed effects?

Rent growth varies sharply by year and metro. The 2020–21 average is 11.93%, versus 4.31% in 2015–19. Metro and year fixed effects compare ZIP-years inside the same broad place/time conditions instead of letting the COVID-era Sun Belt shock drive the result. Fixed effects alone reach R² = 0.637; the full H1 model reaches 0.666.

### Why HC3 robust standard errors?

ZIP-years do not have equal residual variance. Some have far more reviews, different rent levels, or different shock exposure. HC3 is a conservative heteroskedasticity correction suitable for the coursework sample.

### Why a static site?

The full cleaned panel is small. Static extracts make the site cheap, fast, inspectable, and reproducible, while eliminating server or database failure modes. The same script generates every displayed number.

### Why discrete map colors?

PC1 units are relative and have outliers. A fixed domain based on the 5th–95th percentile keeps color comparisons stable across metro/year changes without letting extreme values flatten the rest of the map.

### Why show the effect against mean growth?

A significant p-value says the coefficient is unlikely to be zero under the model; it does not say the coefficient is large. Showing +0.276 pp next to 6.70% prevents the interface from inflating statistical significance into practical dominance.

## The mapping correction

The committed CSV has 1,113 rows, but ZIP `37076` is duplicated under Nashville and Indianapolis and ZIP `70122` under New Orleans and Tampa Bay. Each duplicate is numerically identical apart from `metro`. The generator fails if this exact known pattern changes, keeps the geographically valid Nashville/New Orleans assignments, and analyzes 1,105 rows.

The original final notebook stays unchanged as the coursework record. The public site reports corrected-panel results:

| Test | Corrected-panel result |
|---|---|
| H1 | β = 0.1373, HC3 SE = 0.0454, one-sided p = 0.0013 |
| H2 | Joint F = 2.7024, p = 0.0293 |
| H3 | Q4 − Q1 = +0.357 pp, p = 0.2308 |

The conclusions do not change: H1 and H2 are supported; H3 is not.

## How the interactions work

- Metro buttons filter the committed geometry and choose a high-coverage default ZIP.
- The year slider changes the map fill and current detail values.
- ZIP polygons are real keyboard-focusable SVG buttons; Enter/Space select them.
- The detail view shows aligned PC1 and next-year rent-growth curves.
- The lexicon buttons re-sort the same 30 generated records by PC1 loading, raw next-year correlation, or mentions per 1,000 reviews.
- The rigor panel reads generated H1/context values and sets the effect bar to the true effect-to-mean ratio.

## Ten hard interview questions

### 1. Does this establish a causal link between Yelp language and rent increases?

No. It is an observational predictive association. A transit investment, employment shift, pandemic migration, or changing reviewer demographics could affect both Yelp language and rent. Fixed effects absorb broad metro/year shocks, not every ZIP-specific confounder.

### 2. Why call the outcome “next-year” growth?

For a Yelp observation in year *t*, the outcome is the percentage change in annual Zillow ZORI from *t* to *t + 1*. That ordering supports a prediction question, but temporal order alone is not causal identification.

### 3. Why is the effect statistically significant but small?

The panel has more than a thousand observations and the controlled coefficient is consistent enough to distinguish from zero. Its magnitude is still only +0.276 percentage points per score SD relative to 6.70% mean growth. Statistical reliability and practical size answer different questions.

### 4. PC1 explains only 13.5%. Is that too low?

No single component dominates this high-dimensional vocabulary, which is itself an important finding. PC1 is useful as the largest shared axis, but the site explicitly avoids treating it as the entire language space. Future work could compare multiple components or supervised text features out of sample.

### 5. Why not use a supervised model instead of PCA?

PCA was preregistered and keeps score construction separate from the rent outcome, reducing the risk of optimizing the feature directly to this sample. A supervised model might predict better but would require honest train/test separation and out-of-sample validation.

### 6. Why does “brunch” have a high loading but negative raw rent correlation?

Loading and outcome correlation are different. A high loading means “brunch” co-moves strongly with the shared vocabulary axis. Its raw correlation with rent growth can still be negative because metro/year composition and other confounders have not been controlled. The interactive ranking exists to make that distinction visible.

### 7. Why did H3 fail when H1 succeeded?

H1 uses the full continuous PCA axis. H3 compresses the original equal-weight score into four buckets and tests only the top-versus-bottom contrast. Binning discards information, and its controlled +0.357 pp estimate is too noisy to clear the threshold.

### 8. What did the duplicate correction change?

It removed eight exact rows whose only conflicting field was metro, stopped Tennessee/Louisiana ZCTAs from appearing in the wrong metro maps, and slightly changed the fitted values. H2 moved from p = 0.0231 to 0.0293; the inference stayed the same.

### 9. How do you know the frontend numbers match the analysis?

`scripts/build_site_data.py` is the single producer. Tests validate the exact scope, correction, model statistics, hook, 30-word lexicon, ZIP/year uniqueness, and geometry join. The generated files are deterministic, and CI checks that regeneration creates no diff.

### 10. What would make this publication-quality research?

Out-of-sample validation on later years or other metros, a preregistered external replication, reviewer-demographic controls, time-varying business opening data, spatially clustered inference, and comparisons against simpler forecasting baselines. This artifact is a rigorous data essay, not a causal paper.

## Commands to remember

```bash
python scripts/build_site_data.py
python -m unittest discover -s tests -v
python -m http.server 8000 -d site
```

Open <http://localhost:8000> for the local interactive.
