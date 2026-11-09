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
        scores = {
            0.1: {"a": 2.0, "b": 4.0},
            1.0: {"a": 3.0, "b": 3.0},
            10.0: {"a": 1.0, "b": float("nan")},
        }
        result = MODULE.select_penalty(scores, ["a", "b"])
        self.assertEqual(result["penalty"], 1.0)
        self.assertEqual(result["macro_mae"], 3.0)
        self.assertIn("10.0", result["invalid_candidates"])

    def test_empty_or_invalid_inner_scores_fail_closed(self):
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty({1.0: {"a": float("nan")}}, ["a", "b"])
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.select_penalty({1.0: {}}, [])

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
        pooled = pair(10.0, 9.5, delta_mae_ci=[-1.0, -0.1], ci_status="ready")
        years = [pair(10.0, 9.7), pair(10.0, 9.6), pair(10.0, 9.8)]
        metros = [
            pair(10.0, 9.5), pair(10.0, 9.7), pair(10.0, 9.6),
            pair(10.0, 10.0), pair(10.0, 9.8),
        ]
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "transportable")

    def test_null_zero_denominator_and_missing_ci_cannot_pass(self):
        null_pooled = pair(0.0, 0.0, delta_mae_ci=[0.0, 0.0], ci_status="ready")
        null_cells = [pair(0.0, 0.0) for _ in range(5)]
        result = MODULE.classify_primary_decision(
            null_pooled, null_cells[:3], null_cells, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")

        pooled_without_ci = pair(10.0, 9.0, delta_mae_ci=None, ci_status="failed")
        good = [pair(10.0, 9.0) for _ in range(5)]
        result = MODULE.classify_primary_decision(
            pooled_without_ci, good[:3], good, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("required_pooled_ci_unavailable", result["reasons"])

        pooled_with_bad_ci = pair(
            10.0, 9.0, delta_mae_ci=[-1.0, float("nan")], ci_status="ready"
        )
        result = MODULE.classify_primary_decision(
            pooled_with_bad_ci, good[:3], good, self.config
        )
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("required_pooled_ci_unavailable", result["reasons"])

    def test_language_failure_or_two_adverse_metros_is_non_transportable(self):
        pooled = pair(10.0, 9.5, delta_mae_ci=[-1.0, -0.1], ci_status="ready")
        years = [pair() for _ in range(3)]
        metros = [pair() for _ in range(4)] + [{"language_failure": True}]
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "non-transportable")

        metros = [pair(10.0, 10.1), pair(10.0, 10.1)] + [pair() for _ in range(3)]
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "non-transportable")
        self.assertIn("two_or_more_worse_metros", result["reasons"])

    def test_shared_failure_is_retained_as_inconclusive(self):
        pooled = pair(10.0, 9.5, delta_mae_ci=[-1.0, -0.1], ci_status="ready")
        years = [pair(), pair(), {"shared_failure": True}]
        metros = [pair() for _ in range(5)]
        result = MODULE.classify_primary_decision(pooled, years, metros, self.config)
        self.assertEqual(result["decision"], "inconclusive")
        self.assertIn("undefined_or_shared_execution_failure", result["reasons"])

    def test_coverage_conditional_requires_same_frozen_threshold_in_both_tasks(self):
        result = MODULE.apply_coverage_gate(
            "inconclusive",
            {
                "reviews>=50": {"out_of_time_passes": True, "metro_time_passes": True},
                "reviews>=100": {"out_of_time_passes": True, "metro_time_passes": False},
            },
        )
        self.assertEqual(result["decision"], "coverage-conditional")
        self.assertEqual(result["threshold"], "reviews>=50")


if __name__ == "__main__":
    unittest.main()
