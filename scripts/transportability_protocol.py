#!/usr/bin/env python3
"""Pure protocol helpers; never reads the Yelp/ZORI panel or fits a model."""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "docs" / "research" / "transportability_protocol_v1_1.json"


class ProtocolError(ValueError):
    """Raised when a frozen protocol invariant is not satisfied."""


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ids(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    return sorted(str(row["row_id"]) for row in rows)


def _zip_count(rows: Iterable[Mapping[str, Any]]) -> int:
    return len({str(row["zip"]) for row in rows})


def _eligibility(
    train: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    *,
    minimum_train_years: int,
    minimum_train_rows: int,
    minimum_train_zips: int,
    minimum_test_rows: int,
    minimum_test_zips: int,
) -> list[str]:
    failures = []
    if len({int(row["year"]) for row in train}) < minimum_train_years:
        failures.append("insufficient_training_years")
    if len(train) < minimum_train_rows:
        failures.append("insufficient_training_rows")
    if _zip_count(train) < minimum_train_zips:
        failures.append("insufficient_training_zip_clusters")
    if len(test) < minimum_test_rows:
        failures.append("insufficient_test_rows")
    if _zip_count(test) < minimum_test_zips:
        failures.append("insufficient_test_zip_clusters")
    return failures


def make_outer_folds(
    rows: Sequence[Mapping[str, Any]], config: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Create deterministic time and metro-time folds from metadata only."""
    outer = config["outer"]
    folds: list[dict[str, Any]] = []
    metros = list(config["metros"])
    observed_metros = {str(row["metro"]) for row in rows}
    unexpected_metros = sorted(observed_metros - set(metros))
    if unexpected_metros:
        raise ProtocolError(f"unexpected metros: {unexpected_metros}")

    for test_year in outer["testYears"]:
        train = [row for row in rows if int(row["year"]) < test_year]
        test = [row for row in rows if int(row["year"]) == test_year]
        failures = _eligibility(
            train,
            test,
            minimum_train_years=config["inner"]["minimumTrainingYears"],
            minimum_train_rows=config["inner"]["minimumTrainingRows"],
            minimum_train_zips=config["inner"]["minimumTrainingZipClusters"],
            minimum_test_rows=outer["time"]["minimumTestRows"],
            minimum_test_zips=outer["time"]["minimumTestZipClusters"],
        )
        folds.append(
            {
                "fold_id": f"time-{test_year}",
                "kind": "time",
                "test_year": test_year,
                "held_out_metro": None,
                "train_ids": _ids(train),
                "test_ids": _ids(test),
                "eligible": not failures,
                "failures": failures,
            }
        )

    for metro in metros:
        for test_year in outer["testYears"]:
            train = [
                row for row in rows
                if str(row["metro"]) != metro and int(row["year"]) < test_year
            ]
            test = [
                row for row in rows
                if str(row["metro"]) == metro and int(row["year"]) == test_year
            ]
            failures = _eligibility(
                train,
                test,
                minimum_train_years=config["inner"]["minimumTrainingYears"],
                minimum_train_rows=config["inner"]["minimumTrainingRows"],
                minimum_train_zips=config["inner"]["minimumTrainingZipClusters"],
                minimum_test_rows=outer["metroTime"]["minimumCellTestRows"],
                minimum_test_zips=outer["metroTime"]["minimumCellTestZipClusters"],
            )
            folds.append(
                {
                    "fold_id": f"metro-{metro}-{test_year}",
                    "kind": "metro_time",
                    "test_year": test_year,
                    "held_out_metro": metro,
                    "train_ids": _ids(train),
                    "test_ids": _ids(test),
                    "eligible": not failures,
                    "failures": failures,
                }
            )
    return folds


def make_metro_aggregate_records(
    rows: Sequence[Mapping[str, Any]],
    outer_folds: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Gate each metro aggregate without reading predictions or outcomes."""
    row_by_id = {str(row["row_id"]): row for row in rows}
    expected_years = list(config["outer"]["testYears"])
    minimum_zips = config["outer"]["metroTime"][
        "minimumAggregateMetroZipClusters"
    ]
    records = []
    for metro in config["metros"]:
        cells = sorted(
            (
                fold for fold in outer_folds
                if fold["kind"] == "metro_time"
                and fold["held_out_metro"] == metro
            ),
            key=lambda fold: int(fold["test_year"]),
        )
        failures = []
        if [int(fold["test_year"]) for fold in cells] != expected_years:
            failures.append("missing_required_metro_time_cells")
        if any(not fold["eligible"] for fold in cells):
            failures.append("ineligible_metro_time_cell")
        test_rows = [
            row_by_id[row_id]
            for fold in cells
            for row_id in fold["test_ids"]
            if row_id in row_by_id
        ]
        if _zip_count(test_rows) < minimum_zips:
            failures.append("insufficient_aggregate_test_zip_clusters")
        records.append(
            {
                "aggregate_id": f"metro-{metro}",
                "held_out_metro": metro,
                "cell_ids": [fold["fold_id"] for fold in cells],
                "test_ids": _ids(test_rows),
                "test_zip_clusters": _zip_count(test_rows),
                "eligible": not failures,
                "failures": failures,
            }
        )
    return records


def make_inner_folds(
    rows: Sequence[Mapping[str, Any]],
    outer_fold: Mapping[str, Any],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Create two rolling inner folds wholly inside an outer training set."""
    row_by_id = {str(row["row_id"]): row for row in rows}
    outer_train = [row_by_id[row_id] for row_id in outer_fold["train_ids"]]
    inner_config = config["inner"]
    folds = []
    for offset in inner_config["validationYearOffsetsFromOuterTestYear"]:
        validation_year = int(outer_fold["test_year"]) + int(offset)
        train = [row for row in outer_train if int(row["year"]) < validation_year]
        validation = [
            row for row in outer_train if int(row["year"]) == validation_year
        ]
        failures = _eligibility(
            train,
            validation,
            minimum_train_years=inner_config["minimumTrainingYears"],
            minimum_train_rows=inner_config["minimumTrainingRows"],
            minimum_train_zips=inner_config["minimumTrainingZipClusters"],
            minimum_test_rows=inner_config["minimumValidationRows"],
            minimum_test_zips=inner_config["minimumValidationZipClusters"],
        )
        held_out = outer_fold["held_out_metro"]
        if held_out is not None and any(
            str(row["metro"]) == held_out for row in train + validation
        ):
            failures.append("held_out_metro_leakage")
        if any(int(row["year"]) >= validation_year for row in train):
            failures.append("future_year_leakage")
        folds.append(
            {
                "fold_id": f"{outer_fold['fold_id']}-inner-{validation_year}",
                "validation_year": validation_year,
                "train_ids": _ids(train),
                "validation_ids": _ids(validation),
                "eligible": not failures,
                "failures": failures,
            }
        )
    return folds


def select_penalty(
    scores: Mapping[float, Mapping[str, float]],
    required_fold_ids: Sequence[str],
    *,
    tie_tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Macro-average required inner-fold MAEs and use the frozen tie-break."""
    valid: list[tuple[float, float]] = []
    invalid: dict[str, list[str]] = {}
    required = list(required_fold_ids)
    if len(required) != 2 or len(set(required)) != 2:
        raise ProtocolError("exactly two distinct inner-fold IDs are required")
    for penalty, fold_scores in scores.items():
        reasons = []
        if set(fold_scores) != set(required):
            reasons.append("missing_or_extra_inner_fold")
        values = [fold_scores.get(fold_id) for fold_id in required]
        if any(
            value is None or not math.isfinite(float(value)) or float(value) < 0
            for value in values
        ):
            reasons.append("invalid_inner_mae")
        if reasons:
            invalid[str(penalty)] = reasons
            continue
        valid.append((float(penalty), sum(float(v) for v in values) / len(values)))
    if not valid:
        raise ProtocolError("no penalty has all required finite inner-fold MAEs")
    best_score = min(score for _, score in valid)
    tied = [
        penalty for penalty, score in valid
        if abs(score - best_score) <= tie_tolerance
    ]
    return {
        "penalty": max(tied),
        "macro_mae": best_score,
        "invalid_candidates": invalid,
    }


def relative_mae_gain(
    baseline_mae: Any, language_mae: Any, *, zero_tolerance: float = 1e-12
) -> dict[str, Any]:
    """Apply frozen zero/undefined denominator behavior."""
    try:
        values = (float(baseline_mae), float(language_mae))
    except (TypeError, ValueError):
        return {"status": "invalid_metric", "gain": None, "adverse": None}
    if any(not math.isfinite(value) or value < 0 for value in values):
        return {"status": "invalid_metric", "gain": None, "adverse": None}
    baseline, language = values
    if baseline <= zero_tolerance:
        if language <= zero_tolerance:
            return {"status": "both_zero", "gain": None, "adverse": False}
        return {
            "status": "baseline_zero_language_positive",
            "gain": None,
            "adverse": True,
        }
    gain = (baseline - language) / baseline
    return {"status": "defined", "gain": gain, "adverse": language > baseline}


def validate_bootstrap(
    unique_clusters: int,
    finite_replicates: int,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    bootstrap = config["bootstrap"]
    if unique_clusters < bootstrap["minimumZipClusters"]:
        return {"status": "unavailable_low_clusters", "ci_available": False}
    if finite_replicates != bootstrap["finiteReplicatesRequired"]:
        return {
            "status": "failed_nonfinite_or_missing_replicates",
            "ci_available": False,
        }
    return {"status": "ready", "ci_available": True}


def _pair_status(pair: Mapping[str, Any], zero_tolerance: float) -> dict[str, Any]:
    if pair.get("shared_failure"):
        return {"status": "shared_failure", "gain": None, "adverse": False}
    if pair.get("language_failure"):
        return {"status": "language_failure", "gain": None, "adverse": True}
    return relative_mae_gain(
        pair.get("baseline_mae"),
        pair.get("language_mae"),
        zero_tolerance=zero_tolerance,
    )


def _valid_ci(value: Any) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return False
    try:
        lower, upper = (float(item) for item in value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(lower) and math.isfinite(upper) and lower <= upper


def classify_primary_decision(
    pooled: Mapping[str, Any],
    years: Sequence[Mapping[str, Any]],
    metros: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify without dropping invalid, null, or adverse cells."""
    rules = config["decision"]
    zero_tolerance = config["relativeImprovement"]["zeroTolerance"]
    pooled_status = _pair_status(pooled, zero_tolerance)
    year_statuses = [_pair_status(pair, zero_tolerance) for pair in years]
    metro_statuses = [_pair_status(pair, zero_tolerance) for pair in metros]
    reasons: list[str] = []

    if len(years) != 3 or len(metros) != rules["metroCount"]:
        reasons.append("missing_required_cells")
    if pooled_status["status"] == "language_failure" or any(
        status["status"] == "language_failure"
        for status in year_statuses + metro_statuses
    ):
        reasons.append("language_only_execution_failure")
    if pooled_status["status"] == "defined" and pooled_status["adverse"]:
        reasons.append("pooled_language_worse")
    if pooled_status["status"] == "baseline_zero_language_positive":
        reasons.append("pooled_language_worse_with_zero_baseline")

    year_worse = 0
    for status in year_statuses:
        if status["status"] == "baseline_zero_language_positive":
            reasons.append("year_language_worse_with_zero_baseline")
            year_worse += 1
        elif status["status"] == "defined" and status["gain"] < -rules[
            "maximumYearRelativeWorsening"
        ]:
            reasons.append("year_worsening_exceeds_limit")
            year_worse += 1

    worse_metros = 0
    for status in metro_statuses:
        if status["status"] == "baseline_zero_language_positive":
            reasons.append("metro_language_worse_with_zero_baseline")
            worse_metros += 1
        elif status["status"] == "defined":
            if status["gain"] < 0:
                worse_metros += 1
            if status["gain"] < -rules["maximumMetroRelativeWorsening"]:
                reasons.append("metro_worsening_exceeds_limit")
    if worse_metros >= 2:
        reasons.append("two_or_more_worse_metros")

    adverse_reasons = sorted(set(reasons) - {"missing_required_cells"})
    if adverse_reasons:
        return {"decision": "non-transportable", "reasons": sorted(set(reasons))}

    all_statuses = [pooled_status] + year_statuses + metro_statuses
    if any(
        status["status"] in {"invalid_metric", "shared_failure"}
        for status in all_statuses
    ):
        reasons.append("undefined_or_shared_execution_failure")
    if (
        pooled.get("ci_status") != "ready"
        or not _valid_ci(pooled.get("delta_mae_ci"))
    ):
        reasons.append("required_pooled_ci_unavailable")
    if reasons:
        return {"decision": "inconclusive", "reasons": sorted(set(reasons))}

    metro_gains = [status["gain"] for status in metro_statuses]
    defined_metro_gains = [gain for gain in metro_gains if gain is not None]
    non_worse_metros = sum(
        status["status"] in {"defined", "both_zero"}
        and (status["gain"] is None or status["gain"] >= 0)
        for status in metro_statuses
    )
    ci_upper = float(pooled["delta_mae_ci"][1])
    success = (
        pooled_status["gain"] is not None
        and pooled_status["gain"] >= rules["minimumPooledOutOfTimeRelativeGain"]
        and ci_upper < rules["pooledDeltaMaeCiUpperMustBeBelow"]
        and non_worse_metros >= rules["minimumNonWorseMetroCount"]
        and len(defined_metro_gains) == rules["metroCount"]
        and median(defined_metro_gains)
        >= rules["minimumMedianMetroRelativeGain"]
    )
    if success:
        return {"decision": "transportable", "reasons": []}
    return {"decision": "inconclusive", "reasons": ["success_threshold_not_met"]}


def apply_coverage_gate(
    primary_decision: str,
    sensitivity_results: Mapping[str, Mapping[str, bool]],
) -> dict[str, Any]:
    """Allow coverage-conditional only for a single frozen threshold in both tasks."""
    if primary_decision != "inconclusive":
        return {"decision": primary_decision, "threshold": None}
    passing = sorted(
        threshold for threshold, result in sensitivity_results.items()
        if result.get("out_of_time_passes") and result.get("metro_time_passes")
    )
    if not passing:
        return {"decision": "inconclusive", "threshold": None}
    return {"decision": "coverage-conditional", "threshold": passing[0]}
