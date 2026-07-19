#!/usr/bin/env python3
"""Build the static P1 site extracts from the committed analysis CSV.

The script derives the PCA language score exactly as the final analysis notebook
does, refits the preregistered H2 interaction model, and joins each ZIP to a
compact 2020 Census ZCTA boundary. It is the single source for every number
shown in the P1 interactive.
"""

from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "analysis_ready.csv"
GEOMETRY_PATH = ROOT / "data" / "geography" / "zcta_boundaries_2020.geojson"
SITE_DATA_DIR = ROOT / "site" / "data"
PANEL_PATH = SITE_DATA_DIR / "panel.json"
SITE_GEOMETRY_PATH = SITE_DATA_DIR / "zcta.geojson"

CENSUS_QUERY_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/tigerWMS_Census2020/MapServer/84/query"
)

METRO_LABELS = {
    "Indianapolis": "Indianapolis",
    "Nashville": "Nashville",
    "New Orleans": "New Orleans",
    "Philly MSA": "Philadelphia",
    "Tampa Bay": "Tampa Bay",
}

EXPECTED_YEARS = list(range(2015, 2023))
EXPECTED_METROS = list(METRO_LABELS)

# The committed CSV contains two cross-metro merge duplicates. In each case the
# numeric row is byte-for-byte identical apart from `metro`, and the canonical
# assignment follows the ZIP's actual state. Keeping both would draw Tennessee
# in Indianapolis and Louisiana in Tampa Bay, as well as double-weight H2.
CANONICAL_METRO_BY_DUPLICATED_ZIP = {
    "37076": "Nashville",
    "70122": "New Orleans",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-geometry",
        action="store_true",
        help="Re-download the selected 2020 Census ZCTA boundaries.",
    )
    return parser.parse_args()


def json_number(value: Any, digits: int) -> float | int | None:
    if value is None or pd.isna(value):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    rounded = round(number, digits)
    return 0.0 if rounded == -0.0 else rounded


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, dtype={"postal_code": "string"})
    df["postal_code"] = df["postal_code"].str.zfill(5)
    df["year"] = df["year"].astype(int)
    source_row_count = len(df)

    required = {
        "postal_code",
        "year",
        "metro",
        "total_reviews",
        "avg_rent",
        "next_year_rent_yoy_change",
        "gentrify_language_score",
        "gentrify_density",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"analysis_ready.csv is missing required columns: {missing}")

    keyword_columns = sorted(
        column
        for column in df.columns
        if column.startswith("kw_") and column.endswith("_freq")
    )
    if len(keyword_columns) != 30:
        raise ValueError(
            f"Expected 30 keyword-frequency columns; found {len(keyword_columns)}"
        )

    years = sorted(df["year"].unique().tolist())
    metros = sorted(df["metro"].unique().tolist())
    if years != EXPECTED_YEARS:
        raise ValueError(f"Expected years {EXPECTED_YEARS}; found {years}")
    if metros != sorted(EXPECTED_METROS):
        raise ValueError(
            f"Expected metros {sorted(EXPECTED_METROS)}; found {metros}"
        )

    ambiguous_zips = sorted(
        df.groupby("postal_code")["metro"].nunique().loc[lambda values: values > 1].index
    )
    expected_ambiguous_zips = sorted(CANONICAL_METRO_BY_DUPLICATED_ZIP)
    if ambiguous_zips != expected_ambiguous_zips:
        raise ValueError(
            "Unexpected cross-metro ZIP assignments. "
            f"Expected {expected_ambiguous_zips}; found {ambiguous_zips}"
        )

    removed_rows = 0
    for zip_code, canonical_metro in CANONICAL_METRO_BY_DUPLICATED_ZIP.items():
        duplicate_rows = df[df["postal_code"] == zip_code]
        for year, year_rows in duplicate_rows.groupby("year"):
            without_metro = year_rows.drop(columns=["metro"])
            if len(year_rows) != 2 or without_metro.nunique(dropna=False).max() != 1:
                raise ValueError(
                    f"ZIP {zip_code} year {year} is not an exact two-metro duplicate"
                )
        wrong_metro = (
            (df["postal_code"] == zip_code)
            & (df["metro"] != canonical_metro)
        )
        removed_rows += int(wrong_metro.sum())
        df = df.loc[~wrong_metro].copy()

    matrix = df[keyword_columns].fillna(0.0).to_numpy(dtype=float)
    means = matrix.mean(axis=0)
    scales = matrix.std(axis=0, ddof=0)
    if np.any(scales == 0):
        zero_variance = [
            keyword_columns[index]
            for index, value in enumerate(scales)
            if value == 0
        ]
        raise ValueError(f"Zero-variance PCA inputs: {zero_variance}")

    standardized = (matrix - means) / scales
    u_matrix, singular_values, components = np.linalg.svd(
        standardized, full_matrices=False
    )
    pc1_scores = u_matrix[:, 0] * singular_values[0]
    pc1_loadings = components[0]
    if pc1_loadings.sum() < 0:
        pc1_scores *= -1
        pc1_loadings *= -1

    df["gentrify_pca_score"] = pc1_scores
    df["log_total_reviews"] = np.log1p(df["total_reviews"])
    df.attrs["source_row_count"] = source_row_count
    df.attrs["removed_duplicate_rows"] = removed_rows
    df.attrs["pc1_variance_pct"] = (
        singular_values[0] ** 2 / np.sum(singular_values**2) * 100
    )
    return df


def fetch_geometry(zips: list[str]) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for start in range(0, len(zips), 75):
        chunk = zips[start : start + 75]
        where = "GEOID IN (" + ",".join(repr(zip_code) for zip_code in chunk) + ")"
        query = urllib.parse.urlencode(
            {
                "where": where,
                "outFields": "GEOID",
                "returnGeometry": "true",
                "outSR": "4326",
                "maxAllowableOffset": "0.0003",
                "f": "geojson",
            }
        )
        request = urllib.request.Request(
            f"{CENSUS_QUERY_URL}?{query}",
            headers={"User-Agent": "yelp-gentrification-rent/1.0"},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.load(response)
        if "error" in payload:
            raise RuntimeError(f"Census TIGERweb query failed: {payload['error']}")
        features.extend(payload.get("features", []))

    normalized: list[dict[str, Any]] = []
    for feature in features:
        zip_code = str(feature["properties"]["GEOID"]).zfill(5)
        if feature.get("geometry") is None:
            raise ValueError(f"Census returned no geometry for ZCTA {zip_code}")
        normalized.append(
            {
                "type": "Feature",
                "properties": {"zip": zip_code},
                "geometry": feature["geometry"],
            }
        )

    normalized.sort(key=lambda feature: feature["properties"]["zip"])
    found = {feature["properties"]["zip"] for feature in normalized}
    missing = sorted(set(zips) - found)
    if missing:
        raise ValueError(f"Census geometry is missing {len(missing)} ZIPs: {missing}")

    return {
        "type": "FeatureCollection",
        "provenance": {
            "source": "U.S. Census Bureau TIGERweb",
            "vintage": "2020 ZCTA",
            "layer": 84,
            "url": CENSUS_QUERY_URL,
            "simplification_degrees": 0.0003,
        },
        "features": normalized,
    }


def load_or_fetch_geometry(
    zips: list[str], refresh: bool
) -> dict[str, Any]:
    if refresh or not GEOMETRY_PATH.exists():
        geometry = fetch_geometry(zips)
        GEOMETRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        GEOMETRY_PATH.write_text(
            json.dumps(geometry, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    else:
        geometry = json.loads(GEOMETRY_PATH.read_text(encoding="utf-8"))

    found = {
        feature["properties"]["zip"]
        for feature in geometry.get("features", [])
    }
    missing = sorted(set(zips) - found)
    extra = sorted(found - set(zips))
    if missing or extra:
        raise ValueError(
            "Committed geography does not match the CSV ZIP set. "
            f"Missing: {missing}; extra: {extra}. "
            "Run with --refresh-geometry."
        )
    return geometry


def fit_metro_slopes(df: pd.DataFrame) -> tuple[dict[str, float], float]:
    model = smf.ols(
        "next_year_rent_yoy_change ~ gentrify_density * C(metro) "
        "+ avg_rent + log_total_reviews + C(year)",
        data=df,
    ).fit(cov_type="HC3")

    base = float(model.params["gentrify_density"])
    slopes = {"Indianapolis": base}
    interaction_terms: list[str] = []
    for metro in EXPECTED_METROS:
        if metro == "Indianapolis":
            continue
        term = f"gentrify_density:C(metro)[T.{metro}]"
        interaction_terms.append(term)
        slopes[metro] = base + float(model.params[term])

    restriction = np.zeros((len(interaction_terms), len(model.params)))
    for row_index, term in enumerate(interaction_terms):
        restriction[row_index, model.params.index.get_loc(term)] = 1.0
    joint_test = model.f_test(restriction)
    return slopes, float(joint_test.pvalue)


def build_extracts(
    df: pd.DataFrame, geometry: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    metro_by_zip = (
        df[["postal_code", "metro"]]
        .drop_duplicates()
        .set_index("postal_code")["metro"]
        .to_dict()
    )
    if df.groupby("postal_code")["metro"].nunique().max() != 1:
        raise ValueError("At least one ZIP is assigned to multiple metros")

    slopes, h2_joint_p = fit_metro_slopes(df)
    score_low, score_high = np.quantile(
        df["gentrify_pca_score"].to_numpy(), [0.05, 0.95]
    )

    zip_payload: dict[str, Any] = {}
    for zip_code, group in df.groupby("postal_code", sort=True):
        group = group.sort_values("year")
        series = []
        for row in group.itertuples(index=False):
            series.append(
                {
                    "year": int(row.year),
                    "score": json_number(row.gentrify_pca_score, 4),
                    "language": json_number(row.gentrify_language_score, 6),
                    "rent": json_number(row.avg_rent, 2),
                    "rentGrowth": json_number(
                        row.next_year_rent_yoy_change, 3
                    ),
                    "reviews": int(row.total_reviews),
                }
            )
        zip_payload[zip_code] = {
            "metro": metro_by_zip[zip_code],
            "series": series,
        }

    metro_payload = []
    for metro in EXPECTED_METROS:
        metro_rows = df[df["metro"] == metro]
        zip_activity = (
            metro_rows.groupby("postal_code")["total_reviews"]
            .agg(["count", "sum"])
            .sort_values(["count", "sum"], ascending=False)
        )
        metro_payload.append(
            {
                "id": metro,
                "label": METRO_LABELS[metro],
                "zipCount": int(metro_rows["postal_code"].nunique()),
                "defaultZip": str(zip_activity.index[0]),
                "slopePer10pp": json_number(slopes[metro] * 0.1, 3),
            }
        )

    site_geometry = {
        "type": "FeatureCollection",
        "provenance": geometry["provenance"],
        "features": [],
    }
    for feature in geometry["features"]:
        zip_code = feature["properties"]["zip"]
        site_geometry["features"].append(
            {
                "type": "Feature",
                "properties": {
                    "zip": zip_code,
                    "metro": metro_by_zip[zip_code],
                },
                "geometry": feature["geometry"],
            }
        )

    panel = {
        "meta": {
            "source": "data/analysis_ready.csv",
            "sourceRows": int(df.attrs["source_row_count"]),
            "mappedRows": int(len(df)),
            "removedDuplicateRows": int(df.attrs["removed_duplicate_rows"]),
            "metroCorrections": CANONICAL_METRO_BY_DUPLICATED_ZIP,
            "zipCount": int(df["postal_code"].nunique()),
            "years": EXPECTED_YEARS,
            "pc1VariancePct": json_number(df.attrs["pc1_variance_pct"], 1),
            "scoreDomain": [
                json_number(score_low, 3),
                json_number(score_high, 3),
            ],
            "h2JointP": json_number(h2_joint_p, 4),
        },
        "metros": metro_payload,
        "zips": zip_payload,
    }
    return panel, site_geometry


def main() -> None:
    args = parse_args()
    df = load_panel()
    zips = sorted(df["postal_code"].unique().tolist())
    geometry = load_or_fetch_geometry(zips, args.refresh_geometry)
    panel, site_geometry = build_extracts(df, geometry)

    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PANEL_PATH.write_text(
        json.dumps(panel, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )
    SITE_GEOMETRY_PATH.write_text(
        json.dumps(site_geometry, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print(
        "Built "
        f"{PANEL_PATH.relative_to(ROOT)} ({PANEL_PATH.stat().st_size / 1024:.1f} KiB) "
        "and "
        f"{SITE_GEOMETRY_PATH.relative_to(ROOT)} "
        f"({SITE_GEOMETRY_PATH.stat().st_size / 1024:.1f} KiB)"
    )
    print(
        f"Verified {df.attrs['source_row_count']:,} source rows; "
        f"mapped {len(df):,} after removing "
        f"{df.attrs['removed_duplicate_rows']} exact cross-metro duplicates; "
        f"{len(zips)} ZIPs, "
        f"{len(EXPECTED_METROS)} metros, "
        f"PC1 variance {df.attrs['pc1_variance_pct']:.1f}%, "
        f"H2 joint p={panel['meta']['h2JointP']:.4f}"
    )


if __name__ == "__main__":
    main()
