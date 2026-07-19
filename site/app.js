const SVG_NS = "http://www.w3.org/2000/svg";
const MAP_WIDTH = 760;
const MAP_HEIGHT = 540;
const MAP_PADDING = 28;
const MAP_COLORS = [
  "#eee8dc",
  "#dfcdb9",
  "#cda98e",
  "#b9785f",
  "#9f4938",
  "#6e261b",
];

const state = {
  panel: null,
  geometry: null,
  metro: "Philly MSA",
  year: 2021,
  selectedZip: null,
  lexiconSort: "loading",
};

const elements = {
  metroControls: document.querySelector("#metro-controls"),
  yearSlider: document.querySelector("#year-slider"),
  yearOutput: document.querySelector("#year-output"),
  map: document.querySelector("#map"),
  mapTitle: document.querySelector("#map-title"),
  mapCount: document.querySelector("#map-count"),
  tooltip: document.querySelector("#tooltip"),
  zipTitle: document.querySelector("#zip-title"),
  zipMetro: document.querySelector("#zip-metro"),
  metricScore: document.querySelector("#metric-score"),
  metricRent: document.querySelector("#metric-rent"),
  metricGrowth: document.querySelector("#metric-growth"),
  metricSlope: document.querySelector("#metric-slope"),
  twinChart: document.querySelector("#twin-chart"),
  jointP: document.querySelector("#joint-p"),
  dataNote: document.querySelector("#data-note"),
  headerRows: document.querySelector("#header-rows"),
  headerZips: document.querySelector("#header-zips"),
  headerMetros: document.querySelector("#header-metros"),
  hookLocation: document.querySelector("#hook-location"),
  hookBeforeYear: document.querySelector("#hook-before-year"),
  hookSignalYear: document.querySelector("#hook-signal-year"),
  hookScoreDelta: document.querySelector("#hook-score-delta"),
  hookGrowthBefore: document.querySelector("#hook-growth-before"),
  hookGrowthAfter: document.querySelector("#hook-growth-after"),
  hookScoreBefore: document.querySelector("#hook-score-before"),
  hookScoreAfter: document.querySelector("#hook-score-after"),
  hookRentBefore: document.querySelector("#hook-rent-before"),
  hookRentAfter: document.querySelector("#hook-rent-after"),
  hookReviewNote: document.querySelector("#hook-review-note"),
  lexiconList: document.querySelector("#lexicon-list"),
  lexiconDescription: document.querySelector("#lexicon-description"),
  lexiconCount: document.querySelector("#lexicon-count"),
  lexiconButtons: document.querySelectorAll("[data-lexicon-sort]"),
  meanGrowthLabel: document.querySelector("#mean-growth-label"),
  effectLabel: document.querySelector("#effect-label"),
  effectBar: document.querySelector("#effect-bar"),
  effectCaption: document.querySelector("#effect-caption"),
  varianceStat: document.querySelector("#variance-stat"),
  fixedEffectsStat: document.querySelector("#fixed-effects-stat"),
  fixedEffectsCopy: document.querySelector("#fixed-effects-copy"),
  covidStat: document.querySelector("#covid-stat"),
  covidCopy: document.querySelector("#covid-copy"),
  h1Result: document.querySelector("#h1-result"),
  h2Result: document.querySelector("#h2-result"),
  h3Result: document.querySelector("#h3-result"),
};

function createSvgElement(name, attributes = {}) {
  const node = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => {
    node.setAttribute(key, String(value));
  });
  return node;
}

function metroRecord(id = state.metro) {
  return state.panel.metros.find((metro) => metro.id === id);
}

function rowForYear(zipCode, year = state.year) {
  const zip = state.panel.zips[zipCode];
  return zip?.series.find((row) => row.year === year) ?? null;
}

function signed(value, digits = 2) {
  if (value == null) return "—";
  return `${value >= 0 ? "+" : "−"}${Math.abs(value).toFixed(digits)}`;
}

function pValue(value) {
  if (value == null) return "p = —";
  return `p = ${value.toFixed(4).replace(/^0/, "")}`;
}

function renderHook() {
  const hook = state.panel.hook;
  elements.hookLocation.textContent = `ZIP ${hook.zip} · ${hook.metro}`;
  elements.hookBeforeYear.textContent = hook.beforeYear;
  elements.hookSignalYear.textContent = hook.signalYear;
  elements.hookScoreDelta.textContent = signed(hook.scoreDelta, 2);
  elements.hookGrowthBefore.textContent = `${hook.growthBefore.toFixed(2)}%`;
  elements.hookGrowthAfter.textContent = `${hook.growthAfter.toFixed(2)}%`;
  elements.hookScoreBefore.textContent = signed(hook.scoreBefore, 2);
  elements.hookScoreAfter.textContent = signed(hook.scoreAfter, 2);
  elements.hookRentBefore.textContent = `${hook.growthBefore.toFixed(2)}%`;
  elements.hookRentAfter.textContent = `${hook.growthAfter.toFixed(2)}%`;
  elements.hookReviewNote.textContent =
    `${hook.reviewsBefore.toLocaleString()} reviews in ${hook.beforeYear}; ` +
    `${hook.reviewsAfter.toLocaleString()} in ${hook.signalYear}.`;
}

const LEXICON_CONFIG = {
  loading: {
    field: "loading",
    description:
      "Loading shows how strongly each term contributes to the shared PC1 vocabulary axis.",
    format: (value) => value.toFixed(3),
    compare: (left, right) => right.loading - left.loading,
  },
  correlation: {
    field: "nextYearCorrelation",
    description:
      "Correlation is the raw, uncontrolled relationship between a term’s frequency and next-year rent growth.",
    format: (value) => signed(value, 3),
    compare: (left, right) =>
      right.nextYearCorrelation - left.nextYearCorrelation,
  },
  frequency: {
    field: "mentionsPer1kReviews",
    description:
      "Frequency counts keyword mentions per 1,000 retained reviews in the corrected mapping panel.",
    format: (value) => `${value.toFixed(2)} / 1k`,
    compare: (left, right) =>
      right.mentionsPer1kReviews - left.mentionsPer1kReviews,
  },
};

function renderLexicon() {
  const config = LEXICON_CONFIG[state.lexiconSort];
  const sorted = [...state.panel.lexicon].sort(config.compare);
  const maximum = Math.max(
    ...sorted.map((item) => Math.abs(item[config.field])),
  );

  elements.lexiconList.replaceChildren();
  sorted.forEach((item) => {
    const value = item[config.field];
    const listItem = document.createElement("li");
    listItem.className = "lexicon-item";

    const word = document.createElement("span");
    word.className = "lexicon-word";
    word.textContent = item.word;

    const track = document.createElement("span");
    track.className = "lexicon-bar-track";
    track.setAttribute("aria-hidden", "true");
    const bar = document.createElement("i");
    bar.className = `lexicon-bar${value < 0 ? " is-negative" : ""}`;
    bar.style.width = `${Math.max(0.6, Math.abs(value) / maximum * 100)}%`;
    track.append(bar);

    const valueLabel = document.createElement("span");
    valueLabel.className = "lexicon-value";
    valueLabel.textContent = config.format(value);

    listItem.append(word, track, valueLabel);
    elements.lexiconList.append(listItem);
  });

  elements.lexiconDescription.textContent = config.description;
  elements.lexiconCount.textContent = `${sorted.length} terms`;
  elements.lexiconButtons.forEach((button) => {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.lexiconSort === state.lexiconSort),
    );
  });
}

function renderStrengthAndMethods() {
  const { h1, h3, context } = state.panel.study;
  const effectRatio = h1.effectPerSd / context.meanRentGrowth * 100;

  elements.meanGrowthLabel.textContent =
    `${context.meanRentGrowth.toFixed(2)}%`;
  elements.effectLabel.textContent = `${signed(h1.effectPerSd, 3)} pp`;
  elements.effectBar.style.width = `${Math.max(0.4, effectRatio)}%`;
  elements.effectCaption.textContent =
    `The +1 SD language-score effect is ${effectRatio.toFixed(1)}% ` +
    "as large as the panel’s mean annual rent-growth rate.";
  elements.varianceStat.textContent =
    `${state.panel.meta.pc1VariancePct.toFixed(1)}%`;
  elements.fixedEffectsStat.textContent =
    `R² ${context.fixedEffectsRSquared.toFixed(3)}`;
  elements.fixedEffectsCopy.textContent =
    `Metro and year fixed effects alone reach R² ` +
    `${context.fixedEffectsRSquared.toFixed(3)}; the full H1 model reaches ` +
    `${h1.rSquared.toFixed(3)}. Most model fit comes from place and time.`;
  elements.covidStat.textContent =
    `${context.covidPeriodMeanGrowth.toFixed(2)}%`;
  elements.covidCopy.textContent =
    `Mean next-year growth in 2020–21, versus ` +
    `${context.preCovidMeanGrowth.toFixed(2)}% across 2015–19. Year effects ` +
    "keep that shared shock from masquerading as vocabulary signal.";

  elements.h1Result.textContent =
    `β = ${h1.beta.toFixed(4)} · HC3 SE = ${h1.hc3Se.toFixed(4)} · ` +
    `${pValue(h1.oneSidedP)} · N = ${h1.n.toLocaleString()}`;
  elements.h2Result.textContent =
    `Joint F = ${state.panel.meta.h2JointF.toFixed(4)} · ` +
    `${pValue(state.panel.meta.h2JointP)} · corrected mapping panel`;
  elements.h3Result.textContent =
    `Q4 − Q1 = ${signed(h3.q4VsQ1, 3)} pp · ` +
    `${pValue(h3.twoSidedP)} · N = ${h3.n.toLocaleString()}`;
}

function scoreColor(score) {
  if (score == null) return "#f7f3ea";
  const [low, high] = state.panel.meta.scoreDomain;
  const ratio = Math.max(0, Math.min(0.999, (score - low) / (high - low)));
  return MAP_COLORS[Math.floor(ratio * MAP_COLORS.length)];
}

function walkCoordinates(geometry, callback) {
  if (geometry.type === "Polygon") {
    geometry.coordinates.forEach((ring) => ring.forEach(callback));
  } else if (geometry.type === "MultiPolygon") {
    geometry.coordinates.forEach((polygon) => {
      polygon.forEach((ring) => ring.forEach(callback));
    });
  }
}

function mercator([longitude, latitude]) {
  const radians = Math.PI / 180;
  const clampedLatitude = Math.max(-85, Math.min(85, latitude));
  return [
    longitude * radians,
    -Math.log(
      Math.tan(Math.PI / 4 + (clampedLatitude * radians) / 2),
    ),
  ];
}

function projectionFor(features) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  features.forEach((feature) => {
    walkCoordinates(feature.geometry, (coordinate) => {
      const [x, y] = mercator(coordinate);
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    });
  });

  const availableWidth = MAP_WIDTH - MAP_PADDING * 2;
  const availableHeight = MAP_HEIGHT - MAP_PADDING * 2;
  const scale = Math.min(
    availableWidth / Math.max(maxX - minX, 0.000001),
    availableHeight / Math.max(maxY - minY, 0.000001),
  );
  const offsetX =
    MAP_PADDING + (availableWidth - (maxX - minX) * scale) / 2;
  const offsetY =
    MAP_PADDING + (availableHeight - (maxY - minY) * scale) / 2;

  return (coordinate) => {
    const [x, y] = mercator(coordinate);
    return [
      offsetX + (x - minX) * scale,
      offsetY + (y - minY) * scale,
    ];
  };
}

function geometryPath(geometry, project) {
  const polygons =
    geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
  const commands = [];

  polygons.forEach((polygon) => {
    polygon.forEach((ring) => {
      ring.forEach((coordinate, index) => {
        const [x, y] = project(coordinate);
        commands.push(`${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`);
      });
      commands.push("Z");
    });
  });
  return commands.join("");
}

function showTooltip(event, zipCode, row) {
  const mapBounds = elements.map.parentElement.getBoundingClientRect();
  const score = row ? signed(row.score, 2) : "No data";
  elements.tooltip.innerHTML = `<strong>ZIP ${zipCode}</strong>PC1 ${score}`;
  elements.tooltip.hidden = false;
  const x = Math.min(
    event.clientX - mapBounds.left + 12,
    mapBounds.width - 130,
  );
  const y = Math.max(event.clientY - mapBounds.top - 54, 8);
  elements.tooltip.style.left = `${x}px`;
  elements.tooltip.style.top = `${y}px`;
}

function hideTooltip() {
  elements.tooltip.hidden = true;
}

function renderMetroControls() {
  elements.metroControls.replaceChildren();
  state.panel.metros.forEach((metro) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "metro-button";
    button.setAttribute("aria-pressed", String(metro.id === state.metro));
    button.innerHTML = `
      <span>${metro.label}</span>
      <small>${signed(metro.slopePer10pp, 2)} pp model slope</small>
    `;
    button.addEventListener("click", () => {
      state.metro = metro.id;
      state.selectedZip = metro.defaultZip;
      render();
    });
    elements.metroControls.append(button);
  });
}

function renderMap() {
  const metro = metroRecord();
  const features = state.geometry.features.filter(
    (feature) => feature.properties.metro === state.metro,
  );
  const project = projectionFor(features);
  elements.map.replaceChildren();

  features.forEach((feature) => {
    const zipCode = feature.properties.zip;
    const row = rowForYear(zipCode);
    const path = createSvgElement("path", {
      d: geometryPath(feature.geometry, project),
      fill: scoreColor(row?.score),
      "fill-rule": "evenodd",
      class: `zip-shape${zipCode === state.selectedZip ? " is-selected" : ""}`,
      tabindex: "0",
      role: "button",
      "aria-label": `ZIP ${zipCode}, ${
        row ? `language score ${signed(row.score, 2)}` : "no data for this year"
      }`,
    });

    path.addEventListener("click", () => {
      state.selectedZip = zipCode;
      renderMap();
      renderDetails();
    });
    path.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        state.selectedZip = zipCode;
        renderMap();
        renderDetails();
      }
    });
    path.addEventListener("pointermove", (event) => {
      showTooltip(event, zipCode, row);
    });
    path.addEventListener("pointerleave", hideTooltip);
    elements.map.append(path);
  });

  const observed = features.filter((feature) =>
    rowForYear(feature.properties.zip),
  ).length;
  elements.mapTitle.textContent = `${metro.label} · ${state.year}`;
  elements.mapCount.textContent = `${observed} of ${features.length} ZIPs observed`;
}

function lineChartGroup({
  series,
  field,
  top,
  height,
  colorClass,
  pointClass,
  label,
  format,
}) {
  const width = 520;
  const left = 52;
  const right = 18;
  const usableWidth = width - left - right;
  const values = series.filter((row) => row[field] != null);
  const years = state.panel.meta.years;
  const minimum = Math.min(...values.map((row) => row[field]));
  const maximum = Math.max(...values.map((row) => row[field]));
  const padding = Math.max((maximum - minimum) * 0.15, 0.1);
  const low = minimum - padding;
  const high = maximum + padding;
  const x = (year) =>
    left + ((year - years[0]) / (years.at(-1) - years[0])) * usableWidth;
  const y = (value) =>
    top + height - ((value - low) / Math.max(high - low, 0.0001)) * height;
  const group = createSvgElement("g");

  [0, 0.5, 1].forEach((fraction) => {
    const lineY = top + height * fraction;
    group.append(
      createSvgElement("line", {
        x1: left,
        x2: width - right,
        y1: lineY,
        y2: lineY,
        class: "chart-grid",
      }),
    );
  });

  const title = createSvgElement("text", {
    x: left,
    y: top - 14,
    class: "chart-label",
  });
  title.textContent = label;
  group.append(title);

  const maxLabel = createSvgElement("text", {
    x: left - 8,
    y: top + 4,
    "text-anchor": "end",
    class: "chart-value",
  });
  maxLabel.textContent = format(maximum);
  group.append(maxLabel);

  const minLabel = createSvgElement("text", {
    x: left - 8,
    y: top + height + 4,
    "text-anchor": "end",
    class: "chart-value",
  });
  minLabel.textContent = format(minimum);
  group.append(minLabel);

  let pathData = "";
  let previousYear = null;
  values.forEach((row) => {
    const command =
      previousYear != null && row.year === previousYear + 1 ? "L" : "M";
    pathData += `${command}${x(row.year).toFixed(2)},${y(row[field]).toFixed(2)}`;
    previousYear = row.year;
  });
  group.append(
    createSvgElement("path", {
      d: pathData,
      class: colorClass,
    }),
  );

  values.forEach((row) => {
    group.append(
      createSvgElement("circle", {
        cx: x(row.year),
        cy: y(row[field]),
        r: row.year === state.year ? 5 : 3,
        class: pointClass,
      }),
    );
  });

  return group;
}

function renderTwinChart(series) {
  elements.twinChart.replaceChildren();
  if (!series.length) return;

  const years = state.panel.meta.years;
  const focusX =
    52 + ((state.year - years[0]) / (years.at(-1) - years[0])) * (520 - 52 - 18);
  elements.twinChart.append(
    createSvgElement("line", {
      x1: focusX,
      x2: focusX,
      y1: 28,
      y2: 320,
      class: "chart-focus",
    }),
  );

  elements.twinChart.append(
    lineChartGroup({
      series,
      field: "score",
      top: 50,
      height: 95,
      colorClass: "chart-line-language",
      pointClass: "chart-point-language",
      label: "Yelp language PC1",
      format: (value) => signed(value, 1),
    }),
  );
  elements.twinChart.append(
    lineChartGroup({
      series,
      field: "rentGrowth",
      top: 205,
      height: 95,
      colorClass: "chart-line-rent",
      pointClass: "chart-point-rent",
      label: "Next-year rent growth",
      format: (value) => `${value.toFixed(1)}%`,
    }),
  );

  [years[0], state.year, years.at(-1)].forEach((year) => {
    const x = 52 + ((year - years[0]) / (years.at(-1) - years[0])) * 450;
    const label = createSvgElement("text", {
      x,
      y: 334,
      "text-anchor": year === years[0] ? "start" : year === years.at(-1) ? "end" : "middle",
      class: "chart-year",
    });
    label.textContent = year;
    elements.twinChart.append(label);
  });
}

function renderDetails() {
  const zip = state.panel.zips[state.selectedZip];
  const row = rowForYear(state.selectedZip);
  const metro = metroRecord(zip.metro);

  elements.zipTitle.textContent = `ZIP ${state.selectedZip}`;
  elements.zipMetro.textContent = `${metro.label} · review year ${state.year}`;
  elements.metricScore.textContent = row ? signed(row.score, 2) : "No data";
  elements.metricRent.textContent =
    row?.rent == null
      ? "No data"
      : new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "USD",
          maximumFractionDigits: 0,
        }).format(row.rent);
  elements.metricGrowth.textContent =
    row?.rentGrowth == null ? "No data" : `${signed(row.rentGrowth, 2)}%`;
  elements.metricSlope.textContent = `${signed(metro.slopePer10pp, 2)} pp`;
  renderTwinChart(zip.series);
}

function render() {
  const metro = metroRecord();
  if (
    !state.selectedZip ||
    state.panel.zips[state.selectedZip]?.metro !== state.metro
  ) {
    state.selectedZip = metro.defaultZip;
  }
  renderMetroControls();
  renderMap();
  renderDetails();
  elements.yearSlider.value = state.year;
  elements.yearOutput.value = state.year;
  elements.yearOutput.textContent = state.year;
}

async function initialize() {
  try {
    const [panelResponse, geometryResponse] = await Promise.all([
      fetch("data/panel.json"),
      fetch("data/zcta.geojson"),
    ]);
    if (!panelResponse.ok || !geometryResponse.ok) {
      throw new Error("The generated site extracts could not be loaded.");
    }
    [state.panel, state.geometry] = await Promise.all([
      panelResponse.json(),
      geometryResponse.json(),
    ]);

    const metro = metroRecord();
    state.selectedZip = metro.defaultZip;
    elements.yearSlider.min = state.panel.meta.years[0];
    elements.yearSlider.max = state.panel.meta.years.at(-1);
    elements.yearSlider.addEventListener("input", (event) => {
      state.year = Number(event.target.value);
      renderMap();
      renderDetails();
      elements.yearOutput.value = state.year;
      elements.yearOutput.textContent = state.year;
    });
    elements.jointP.textContent = pValue(state.panel.meta.h2JointP);
    elements.headerRows.textContent =
      `${state.panel.meta.mappedRows.toLocaleString()} mapped ZIP-years`;
    elements.headerZips.textContent =
      `${state.panel.meta.zipCount.toLocaleString()} ZIP codes`;
    elements.headerMetros.textContent =
      `${state.panel.metros.length} metro areas`;
    elements.dataNote.textContent =
      `${state.panel.meta.sourceRows.toLocaleString()} source rows regenerate ` +
      `from ${state.panel.meta.source}; ${state.panel.meta.removedDuplicateRows} ` +
      `exact cross-metro duplicates are removed before mapping, leaving ` +
      `${state.panel.meta.mappedRows.toLocaleString()} ZIP-years. PC1 explains ` +
      `${state.panel.meta.pc1VariancePct.toFixed(1)}% of keyword variance.`;
    elements.lexiconButtons.forEach((button) => {
      button.addEventListener("click", () => {
        state.lexiconSort = button.dataset.lexiconSort;
        renderLexicon();
      });
    });
    renderHook();
    renderLexicon();
    renderStrengthAndMethods();
    render();
    if (window.location.hash) {
      requestAnimationFrame(() => {
        document.querySelector(window.location.hash)?.scrollIntoView();
      });
    }
  } catch (error) {
    console.error(error);
    document.querySelector("#explorer").innerHTML = `
      <p class="error-message">
        The interactive could not load. Serve the repository over HTTP and
        regenerate the extracts with <code>python3 scripts/build_site_data.py</code>.
      </p>
    `;
  }
}

initialize();
