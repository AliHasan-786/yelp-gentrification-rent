import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "transportability_protocol",
    ROOT / "scripts" / "transportability_protocol.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def synthetic_rows(zips_per_metro=25):
    rows = []
    metros = ["Indianapolis", "Nashville", "New Orleans", "Philly MSA", "Tampa Bay"]
    for metro_index, metro in enumerate(metros):
        for zip_index in range(zips_per_metro):
            zip_code = f"{metro_index + 1}{zip_index:04d}"
            for year in range(2015, 2023):
                rows.append(
                    {
                        "row_id": f"{metro}-{zip_code}-{year}",
                        "zip": zip_code,
                        "metro": metro,
                        "year": year,
                    }
                )
    return rows


def pair(baseline=10.0, language=9.5, **extra):
    return {"baseline_mae": baseline, "language_mae": language, **extra}


OUTER_FOLD = {"fold_id": "time-2022", "test_year": 2022}
INNER_A = "time-2022-inner-2020"
INNER_B = "time-2022-inner-2021"


def inner_fold_records(eligible=True):
    return [
        {"fold_id": INNER_A, "validation_year": 2020, "eligible": eligible},
        {"fold_id": INNER_B, "validation_year": 2021, "eligible": eligible},
    ]


def score_grid(config, default=5.0):
    return {
        penalty: {INNER_A: default, INNER_B: default}
        for penalty in config["selection"]["ridgePenalties"]
    }


def decision_inputs():
    years = []
    for year, language in zip((2020, 2021, 2022), (9.7, 9.6, 9.8)):
        years.append(
            pair(
                10.0,
                language,
                cell_id=f"time-{year}",
                year=year,
                eligible=True,
            )
        )
    metros = []
    values = {
        "Indianapolis": 9.5,
        "Nashville": 9.7,
        "New Orleans": 9.6,
        "Philly MSA": 10.0,
        "Tampa Bay": 9.8,
    }
    for metro, language in values.items():
        metros.append(
            pair(
                10.0,
                language,
                aggregate_id=f"metro-{metro}",
                metro=metro,
                eligible=True,
            )
        )
    pooled = pair(
        10.0,
        9.5,
        scope="pooled_out_of_time",
        cell_ids=["time-2020", "time-2021", "time-2022"],
        eligible=True,
        delta_mae_ci=[-1.0, -0.1],
        ci_status="ready",
    )
    return pooled, years, metros


def coverage_results(*passing):
    passing = set(passing)
    return [
        {
            "threshold_id": threshold,
            "out_of_time_passes": threshold in passing,
            "metro_time_passes": threshold in passing,
        }
        for threshold in ("reviews>=20", "reviews>=50", "reviews>=100")
    ]


class FoldConstructionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = MODULE.load_config()
        cls.rows = synthetic_rows()
        cls.row_by_id = {row["row_id"]: row for row in cls.rows}

    def test_outer_folds_are_deterministic_and_never_use_future_or_held_metro(self):
        first = MODULE.make_outer_folds(self.rows, self.config)
        second = MODULE.make_outer_folds(list(reversed(self.rows)), self.config)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 18)
        self.assertTrue(all(fold["eligible"] for fold in first))
        for fold in first:
            train = [self.row_by_id[row_id] for row_id in fold["train_ids"]]
            test = [self.row_by_id[row_id] for row_id in fold["test_ids"]]
            self.assertTrue(all(row["year"] < fold["test_year"] for row in train))
            self.assertTrue(all(row["year"] == fold["test_year"] for row in test))
            if fold["held_out_metro"] is not None:
                self.assertTrue(
                    all(row["metro"] != fold["held_out_metro"] for row in train)
                )
                self.assertTrue(
                    all(row["metro"] == fold["held_out_metro"] for row in test)
                )

    def test_inner_folds_are_exact_two_year_rolling_origin_inside_outer_train(self):
        outer = next(
            fold for fold in MODULE.make_outer_folds(self.rows, self.config)
            if fold["fold_id"] == "metro-New Orleans-2022"
        )
        inner = MODULE.make_inner_folds(self.rows, outer, self.config)
        self.assertEqual([fold["validation_year"] for fold in inner], [2020, 2021])
        outer_ids = set(outer["train_ids"])
        for fold in inner:
            self.assertTrue(fold["eligible"])
            self.assertLessEqual(
                set(fold["train_ids"]) | set(fold["validation_ids"]), outer_ids
            )
            train = [self.row_by_id[row_id] for row_id in fold["train_ids"]]
            validation = [
                self.row_by_id[row_id] for row_id in fold["validation_ids"]
            ]
            self.assertTrue(
                all(row["year"] < fold["validation_year"] for row in train)
            )
            self.assertTrue(
                all(row["year"] == fold["validation_year"] for row in validation)
            )
            self.assertTrue(all(row["metro"] != "New Orleans" for row in train))
            self.assertTrue(
                all(row["metro"] != "New Orleans" for row in validation)
            )

    def test_ineligible_fold_is_retained_with_reasons(self):
        folds = MODULE.make_outer_folds(synthetic_rows(zips_per_metro=1), self.config)
        new_orleans_2020 = next(
            fold for fold in folds if fold["fold_id"] == "metro-New Orleans-2020"
        )
        self.assertFalse(new_orleans_2020["eligible"])
        self.assertIn("insufficient_test_rows", new_orleans_2020["failures"])
        self.assertIn("insufficient_test_zip_clusters", new_orleans_2020["failures"])

    def test_metro_aggregate_requires_all_cells_and_ten_zip_clusters(self):
        full_folds = MODULE.make_outer_folds(self.rows, self.config)
        full_records = MODULE.make_metro_aggregate_records(
            self.rows, full_folds, self.config
        )
        self.assertEqual(len(full_records), 5)
        self.assertTrue(all(record["eligible"] for record in full_records))
        self.assertTrue(all(len(record["cell_ids"]) == 3 for record in full_records))

        small_rows = synthetic_rows(zips_per_metro=5)
        small_folds = MODULE.make_outer_folds(small_rows, self.config)
        small_records = MODULE.make_metro_aggregate_records(
            small_rows, small_folds, self.config
        )
        self.assertTrue(all(not record["eligible"] for record in small_records))
        self.assertTrue(
            all(
                "insufficient_aggregate_test_zip_clusters" in record["failures"]
                for record in small_records
            )
        )

    def test_configured_metros_are_fixed_and_missing_metro_cells_are_retained(self):
        without_tampa = [row for row in self.rows if row["metro"] != "Tampa Bay"]
        folds = MODULE.make_outer_folds(without_tampa, self.config)
        tampa = [fold for fold in folds if fold["held_out_metro"] == "Tampa Bay"]
        self.assertEqual(len(tampa), 3)
        self.assertTrue(all(not fold["eligible"] for fold in tampa))

        with self.assertRaises(MODULE.ProtocolError):
            MODULE.make_outer_folds(
                self.rows + [
                    {"row_id": "extra", "zip": "00000", "metro": "Extra", "year": 2020}
                ],
                self.config,
            )


class SelectionAndFailureRuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = MODULE.load_config()

    def test_penalty_uses_macro_fold_mean_and_larger_penalty_tie_break(self):
        scores = score_grid(self.config)
        scores[0.1] = {INNER_A: 2.0, INNER_B: 4.0}
        scores[1.0] = {INNER_A: 3.0, INNER_B: 3.0}
        scores[10.0] = {INNER_A: 1.0, INNER_B: float("nan")}
        result = MODULE.select_penalty(
            scores, inner_fold_records(), OUTER_FOLD, self.config
        )
        self.assertEqual(result["penalty"], 1.0)
        self.assertEqual(result["macro_mae"], 3.0)
        self.assertIn("10.0", result["invalid_candidates"])

    def test_penalty_rejects_unknown_missing_and_malformed_candidates(self):
        scores = score_grid(self.config)
        scores.pop(100.0)
        scores[999] = {INNER_A: 1.0, INNER_B: 1.0}
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty(
                scores, inner_fold_records(), OUTER_FOLD, self.config
            )

        scores = score_grid(self.config)
        scores.pop(100.0)
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty(
                scores, inner_fold_records(), OUTER_FOLD, self.config
            )

        scores = score_grid(self.config)
        scores.pop(1.0)
        scores[True] = {INNER_A: 1.0, INNER_B: 1.0}
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty(
                scores, inner_fold_records(), OUTER_FOLD, self.config
            )

    def test_penalty_rejects_missing_duplicate_or_ineligible_inner_folds(self):
        scores = score_grid(self.config)
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty(
                scores, inner_fold_records()[:1], OUTER_FOLD, self.config
            )
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty(
                scores,
                [
                    {"fold_id": INNER_A, "validation_year": 2020, "eligible": True},
                    {"fold_id": INNER_A, "validation_year": 2020, "eligible": True},
                ],
                OUTER_FOLD,
                self.config,
            )
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty(
                scores, inner_fold_records(False), OUTER_FOLD, self.config
            )

        wrong_identity = inner_fold_records()
        wrong_identity[-1] = dict(
            wrong_identity[-1], fold_id="time-2022-inner-2099", validation_year=2099
        )
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty(scores, wrong_identity, OUTER_FOLD, self.config)

    def test_penalty_invalid_values_fail_closed(self):
        scores = score_grid(self.config, default=float("nan"))
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty(
                scores, inner_fold_records(), OUTER_FOLD, self.config
            )
        scores = score_grid(self.config)
        scores[0.01][INNER_A] = True
        result = MODULE.select_penalty(
            scores, inner_fold_records(), OUTER_FOLD, self.config
        )
        self.assertIn("0.01", result["invalid_candidates"])

    def test_relative_gain_defines_zero_and_invalid_denominators(self):
        self.assertEqual(
            MODULE.relative_mae_gain(0.0, 0.0)["status"], "both_zero"
        )
        adverse = MODULE.relative_mae_gain(0.0, 0.1)
        self.assertEqual(adverse["status"], "baseline_zero_language_positive")
        self.assertTrue(adverse["adverse"])
        self.assertEqual(
            MODULE.relative_mae_gain(-1.0, 0.0)["status"], "invalid_metric"
        )
        self.assertEqual(
            MODULE.relative_mae_gain(None, 0.0)["status"], "invalid_metric"
        )

    def test_bootstrap_fails_closed_without_clusters_or_all_replicates(self):
        self.assertFalse(MODULE.validate_bootstrap(9, 2000, self.config)["ci_available"])
        self.assertFalse(
            MODULE.validate_bootstrap(20, 1999, self.config)["ci_available"]
        )
        self.assertTrue(MODULE.validate_bootstrap(20, 2000, self.config)["ci_available"])

    def test_transportable_requires_all_frozen_success_conditions(self):
        pooled, years, metros = decision_inputs()
        result = MODULE.classify_primary_decision(
            pooled, list(reversed(years)), list(reversed(metros)), self.config
        )
        self.assertEqual(result["decision"], "transportable")

    def test_duplicate_missing_unknown_or_ineligible_cells_cannot_pass(self):
        pooled, years, metros = decision_inputs()
        duplicate_years = [years[0], years[0], years[2]]
        result = MODULE.classify_primary_decision(
            pooled, duplicate_years, metros, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("invalid_year_cell_identities", result["reasons"])

        missing_metro = metros[:-1]
        result = MODULE.classify_primary_decision(
            pooled, years, missing_metro, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("invalid_metro_cell_identities", result["reasons"])

        unknown = pair(
            10.0,
            9.0,
            aggregate_id="metro-Unknown",
            metro="Unknown",
            eligible=True,
        )
        result = MODULE.classify_primary_decision(
            pooled, years, metros[:-1] + [unknown], self.config
        )
        self.assertEqual(result["decision"], "inconclusive")

        ineligible = [dict(years[0], eligible=False)] + years[1:]
        result = MODULE.classify_primary_decision(
            pooled, ineligible, metros, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("ineligible_year_cell", result["reasons"])

    def test_arbitrary_pooled_scope_or_cells_cannot_pass(self):
        pooled, years, metros = decision_inputs()
        pooled["scope"] = "arbitrary_summary"
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("invalid_pooled_scope_or_cells", result["reasons"])

        pooled, years, metros = decision_inputs()
        pooled["cell_ids"] = ["time-2020", "time-2021", "time-2099"]
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "inconclusive")

        pooled, years, metros = decision_inputs()
        pooled["cell_ids"] = [["malformed"], "time-2021", "time-2022"]
        years[0]["cell_id"] = ["malformed"]
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "inconclusive")

    def test_null_zero_denominator_and_missing_ci_cannot_pass(self):
        null_pooled, null_years, null_metros = decision_inputs()
        null_pooled.update(baseline_mae=0.0, language_mae=0.0, delta_mae_ci=[0.0, 0.0])
        for cell in null_years + null_metros:
            cell.update(baseline_mae=0.0, language_mae=0.0)
        result = MODULE.classify_primary_decision(
            null_pooled, null_years, null_metros, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")

        pooled_without_ci, good_years, good_metros = decision_inputs()
        pooled_without_ci.update(language_mae=9.0, delta_mae_ci=None, ci_status="failed")
        result = MODULE.classify_primary_decision(
            pooled_without_ci, good_years, good_metros, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("required_pooled_ci_unavailable", result["reasons"])

        pooled_with_bad_ci, good_years, good_metros = decision_inputs()
        pooled_with_bad_ci.update(language_mae=9.0, delta_mae_ci=[-1.0, float("nan")])
        result = MODULE.classify_primary_decision(
            pooled_with_bad_ci, good_years, good_metros, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("required_pooled_ci_unavailable", result["reasons"])

    def test_language_failure_or_two_adverse_metros_is_non_transportable(self):
        pooled, years, metros = decision_inputs()
        metros[-1] = dict(metros[-1], language_failure=True)
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "non-transportable")

        pooled, years, metros = decision_inputs()
        metros[0].update(language_mae=10.1)
        metros[1].update(language_mae=10.1)
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "non-transportable")
        self.assertIn("two_or_more_worse_metros", result["reasons"])

    def test_shared_failure_is_retained_as_inconclusive(self):
        pooled, years, metros = decision_inputs()
        years[-1] = dict(years[-1], shared_failure=True)
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("undefined_or_shared_execution_failure", result["reasons"])

    def test_adverse_required_cell_survives_an_incomplete_metric_set(self):
        pooled, years, metros = decision_inputs()
        metros[0] = dict(metros[0], language_failure=True)
        result = MODULE.classify_primary_decision(
            pooled, years[:-1], metros, self.config
        )
        self.assertEqual(result["decision"], "non-transportable")
        self.assertIn("invalid_year_cell_identities", result["reasons"])
        self.assertIn("language_only_execution_failure", result["reasons"])

    def test_coverage_conditional_uses_frozen_order_and_reports_all_passing(self):
        result = MODULE.apply_coverage_gate(
            "inconclusive",
            list(reversed(coverage_results("reviews>=20", "reviews>=100"))),
            self.config,
        )
        self.assertEqual(result["decision"], "coverage-conditional")
        self.assertEqual(result["threshold"], "reviews>=20")
        self.assertEqual(
            result["passing_thresholds"], ["reviews>=20", "reviews>=100"]
        )

    def test_unknown_duplicate_or_missing_coverage_thresholds_cannot_qualify(self):
        unknown = coverage_results("reviews>=20")
        unknown[-1]["threshold_id"] = "reviews>=999"
        duplicate = coverage_results("reviews>=20")
        duplicate[-1]["threshold_id"] = "reviews>=20"
        missing = coverage_results("reviews>=20")[:-1]
        for results in (unknown, duplicate, missing):
            decision = MODULE.apply_coverage_gate(
                "inconclusive", results, self.config
            )
            self.assertEqual(decision["decision"], "inconclusive")
            self.assertIn(
                "invalid_coverage_sensitivity_identities", decision["reasons"]
            )

        malformed = coverage_results("reviews>=20")
        malformed[-1] = None
        decision = MODULE.apply_coverage_gate(
            "inconclusive", malformed, self.config
        )
        self.assertEqual(decision["decision"], "inconclusive")

    def test_coverage_sensitivity_cannot_upgrade_adverse_primary(self):
        result = MODULE.apply_coverage_gate(
            "non-transportable",
            coverage_results("reviews>=20", "reviews>=50", "reviews>=100"),
            self.config,
        )
        self.assertEqual(result["decision"], "non-transportable")
        self.assertIsNone(result["threshold"])


if __name__ == "__main__":
    unittest.main()
