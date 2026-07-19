import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_site_data.py"

spec = importlib.util.spec_from_file_location("build_site_data", SCRIPT_PATH)
build_site_data = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(build_site_data)


class SiteDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel = json.loads(
            (ROOT / "site" / "data" / "panel.json").read_text(encoding="utf-8")
        )
        cls.geometry = json.loads(
            (ROOT / "site" / "data" / "zcta.geojson").read_text(encoding="utf-8")
        )

    def test_expected_scope(self):
        self.assertEqual(self.panel["meta"]["sourceRows"], 1113)
        self.assertEqual(self.panel["meta"]["mappedRows"], 1105)
        self.assertEqual(self.panel["meta"]["removedDuplicateRows"], 8)
        self.assertEqual(self.panel["meta"]["zipCount"], 238)
        self.assertEqual(self.panel["meta"]["years"], list(range(2015, 2023)))
        self.assertEqual(self.panel["meta"]["pc1VariancePct"], 13.5)
        self.assertEqual(self.panel["meta"]["h2JointP"], 0.0293)
        self.assertEqual(
            self.panel["meta"]["metroCorrections"],
            {"37076": "Nashville", "70122": "New Orleans"},
        )
        self.assertEqual(
            [metro["label"] for metro in self.panel["metros"]],
            [
                "Indianapolis",
                "Nashville",
                "New Orleans",
                "Philadelphia",
                "Tampa Bay",
            ],
        )

    def test_panel_and_geometry_zip_sets_match(self):
        panel_zips = set(self.panel["zips"])
        geometry_zips = {
            feature["properties"]["zip"]
            for feature in self.geometry["features"]
        }
        self.assertEqual(len(panel_zips), 238)
        self.assertEqual(panel_zips, geometry_zips)

    def test_all_mapped_rows_are_exported_once(self):
        exported_rows = sum(
            len(payload["series"]) for payload in self.panel["zips"].values()
        )
        self.assertEqual(exported_rows, self.panel["meta"]["mappedRows"])
        for payload in self.panel["zips"].values():
            years = [row["year"] for row in payload["series"]]
            self.assertEqual(len(years), len(set(years)))

    def test_cross_metro_duplicates_use_canonical_geography(self):
        self.assertEqual(self.panel["zips"]["37076"]["metro"], "Nashville")
        self.assertEqual(self.panel["zips"]["70122"]["metro"], "New Orleans")
        geometry_metros = {
            feature["properties"]["zip"]: feature["properties"]["metro"]
            for feature in self.geometry["features"]
        }
        self.assertEqual(geometry_metros["37076"], "Nashville")
        self.assertEqual(geometry_metros["70122"], "New Orleans")

    def test_generated_values_match_recomputed_pipeline(self):
        frame = build_site_data.load_panel()
        for row in frame.itertuples(index=False):
            exported = next(
                item
                for item in self.panel["zips"][row.postal_code]["series"]
                if item["year"] == row.year
            )
            self.assertEqual(
                exported["score"],
                build_site_data.json_number(row.gentrify_pca_score, 4),
            )
            self.assertEqual(
                exported["rent"],
                build_site_data.json_number(row.avg_rent, 2),
            )
            self.assertEqual(
                exported["rentGrowth"],
                build_site_data.json_number(
                    row.next_year_rent_yoy_change, 3
                ),
            )

    def test_public_copy_avoids_causal_claims_and_stale_metros(self):
        public_copy = "\n".join(
            [
                (ROOT / "README.md").read_text(encoding="utf-8"),
                (ROOT / "site" / "index.html").read_text(encoding="utf-8"),
            ]
        ).lower()
        for phrase in (
            "los angeles",
            "new york",
            "chicago",
            "san francisco",
            "washington d.c.",
            "causes rent",
            "caused rent",
            "causing rent",
        ):
            self.assertNotIn(phrase, public_copy)

    def test_editorial_css_has_no_gradients(self):
        css = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        self.assertNotIn("gradient(", css.lower())


if __name__ == "__main__":
    unittest.main()
