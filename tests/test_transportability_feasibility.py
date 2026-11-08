import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "transportability_feasibility",
    ROOT / "scripts" / "check_transportability_feasibility.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TransportabilityFeasibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = MODULE.build_report()

    def test_frozen_input_and_corrected_scope(self):
        self.assertEqual(
            self.report["data"]["sha256"],
            "b2b81fbc2a26141fe04b61a474de488b0cb5c28c9f850b1e2235656ef2fb0568",
        )
        self.assertEqual(self.report["data"]["correctedRows"], 1105)
        self.assertEqual(self.report["coverage"]["uniqueZips"], 238)

    def test_language_schema_and_outer_splits_are_feasible(self):
        self.assertEqual(self.report["schema"]["keywordFrequencyColumns"], 30)
        self.assertEqual(self.report["schema"]["missingKeywordFrequencyCells"], 0)
        self.assertEqual(
            set(self.report["outerSplits"]["expandingOutOfTime"]),
            {"2020", "2021", "2022"},
        )
        self.assertEqual(
            set(self.report["outerSplits"]["leaveOneMetroOut"]),
            {"Indianapolis", "Nashville", "New Orleans", "Philly MSA", "Tampa Bay"},
        )

    def test_check_remains_outcome_blind(self):
        self.assertIn("No target values were parsed", self.report["guardrail"])
        self.assertNotIn("targetMean", self.report)


if __name__ == "__main__":
    unittest.main()
