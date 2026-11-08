#!/usr/bin/env python3
"""Report schema/split feasibility without analyzing outcome values."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "analysis_ready.csv"
TARGET = "next_year_rent_yoy_change"
CANONICAL_METRO_BY_DUPLICATED_ZIP = {
    "37076": "Nashville",
    "70122": "New Orleans",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def corrected_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row for row in rows
        if not (
            row["postal_code"] in CANONICAL_METRO_BY_DUPLICATED_ZIP
            and row["metro"]
            != CANONICAL_METRO_BY_DUPLICATED_ZIP[row["postal_code"]]
        )
    ]


def build_report(path: Path = DATA_PATH) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        fields = reader.fieldnames or []

    required = {
        "postal_code", "year", "metro", "total_reviews", "rent_obs_count",
        "rent_yoy_change", "avg_rent", "total_food_businesses", TARGET,
    }
    kw_freq = sorted(
        field for field in fields
        if field.startswith("kw_") and field.endswith("_freq")
    )
    kw_count = sorted(
        field for field in fields
        if field.startswith("kw_") and field.endswith("_count")
    )
    clean = corrected_rows(rows)
    by_zip: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in clean:
        by_zip[(row["metro"], row["postal_code"])].append(int(row["year"]))

    metro_rows = Counter(row["metro"] for row in clean)
    metro_zips = {
        metro: len({r["postal_code"] for r in clean if r["metro"] == metro})
        for metro in sorted(metro_rows)
    }
    rows_by_year = Counter(int(row["year"]) for row in clean)
    panel_lengths = Counter(len(years) for years in by_zip.values())
    review_sensitivities = {}
    for threshold in (20, 50, 100):
        eligible = [r for r in clean if float(r["total_reviews"]) >= threshold]
        review_sensitivities[str(threshold)] = {
            "rows": len(eligible),
            "zips": len({(r["metro"], r["postal_code"]) for r in eligible}),
        }

    oot_folds = {}
    for year in (2020, 2021, 2022):
        train = [r for r in clean if int(r["year"]) < year]
        test = [r for r in clean if int(r["year"]) == year]
        oot_folds[str(year)] = {
            "trainRows": len(train), "testRows": len(test),
            "testZips": len({r["postal_code"] for r in test}),
        }
    lomo_folds = {
        metro: {
            "trainRows": len(clean) - count, "testRows": count,
            "testZips": metro_zips[metro],
        }
        for metro, count in sorted(metro_rows.items())
    }

    return {
        "checkType": "outcome-blind schema and split feasibility",
        "data": {
            "path": str(path.relative_to(ROOT)), "sha256": file_sha256(path),
            "bytes": path.stat().st_size, "sourceRows": len(rows),
            "correctedRows": len(clean),
            "removedDuplicateRows": len(rows) - len(clean), "columns": len(fields),
        },
        "schema": {
            "missingRequiredColumns": sorted(required - set(fields)),
            "keywordFrequencyColumns": len(kw_freq),
            "keywordCountColumns": len(kw_count),
            "missingTargetCells": sum(not r[TARGET].strip() for r in clean),
            "missingCurrentRentGrowthCells": sum(
                not r["rent_yoy_change"].strip() for r in clean
            ),
            "missingKeywordFrequencyCells": sum(
                not r[c].strip() for r in clean for c in kw_freq
            ),
            "allZeroKeywordRows": sum(
                all(float(r[c] or 0) == 0 for c in kw_count) for r in clean
            ),
        },
        "coverage": {
            "years": sorted(rows_by_year),
            "rowsByYear": dict(sorted(rows_by_year.items())),
            "metroRows": dict(sorted(metro_rows.items())), "metroZips": metro_zips,
            "uniqueZips": len(by_zip),
            "panelLengthDistribution": dict(sorted(panel_lengths.items())),
            "complete2015To2022Zips": sum(
                sorted(years) == list(range(2015, 2023))
                for years in by_zip.values()
            ),
            "reviewThresholdSensitivities": review_sensitivities,
        },
        "outerSplits": {
            "expandingOutOfTime": oot_folds,
            "leaveOneMetroOut": lomo_folds,
        },
        "guardrail": (
            "No target values were parsed or summarized; counts only verify "
            "that the frozen protocol is executable."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
