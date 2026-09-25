"""Contract tests for the local inventory-first graph MVP."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
MVP = ROOT / "graph-mvp.html"
ENGINE = ROOT / "graph-recommend.js"


class GraphMvpContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = MVP.read_text(encoding="utf-8")

    def test_has_guided_and_expert_lenses(self) -> None:
        self.assertIn('data-view="guided"', self.html)
        self.assertIn('data-view="expert"', self.html)
        self.assertIn('id="guided-results"', self.html)
        self.assertIn('id="expert-results"', self.html)

    def test_starts_with_inventory_search_not_full_graph(self) -> None:
        self.assertIn('id="equipment-search"', self.html)
        self.assertIn('id="empty-state"', self.html)
        self.assertIn('id="stack-chips"', self.html)
        self.assertIn("Find use cases for your stack", self.html)

    def test_expert_lens_has_coverage_and_export(self) -> None:
        self.assertIn('id="coverage-strip"', self.html)
        self.assertIn('id="expert-table"', self.html)
        self.assertIn('id="export-selection"', self.html)

    def test_uses_catalog_and_existing_inventory_contract(self) -> None:
        self.assertIn('fetch("catalog.json")', self.html)
        self.assertIn('fetch("graph-data.json")', self.html)
        self.assertIn('"uc-inventory"', self.html)
        self.assertIn('params.get("view")', self.html)

    def test_mobile_keeps_recommendations_visible(self) -> None:
        self.assertNotIn("@media (max-width: 600px) {\n  .recommendations { display: none", self.html)
        self.assertIn("@media (max-width: 760px)", self.html)

    def test_guided_lens_shows_a_section_per_selected_product(self) -> None:
        # The merged shortlist alone can omit a product the user selected, so
        # the page must also render one block per product.
        self.assertIn('id="per-product"', self.html)
        self.assertIn("data-product-section", self.html)
        self.assertIn("renderPerProduct", self.html)

    def test_ranking_is_delegated_to_the_shared_engine(self) -> None:
        # Scoring must not be reimplemented inline; graph-mvp.html, the Node
        # tests and VISTA all consume the same module.
        self.assertTrue(ENGINE.exists(), "graph-recommend.js is missing")
        self.assertIn('<script src="graph-recommend.js">', self.html)
        self.assertIn("UCRecommend.buildIndex", self.html)
        self.assertIn('fetch("graph-recommend.json")', self.html)
        self.assertIn("UCRecommend.attachProfiles", self.html)
        self.assertIn("UCRecommend.perProduct", self.html)
        self.assertNotIn("function guidedScore", self.html)

    def test_engine_is_loadable_by_both_browser_and_node(self) -> None:
        engine = ENGINE.read_text(encoding="utf-8")
        self.assertIn("module.exports", engine)
        self.assertIn("window.UCRecommend", engine)

    def test_csp_allows_the_local_engine_script(self) -> None:
        self.assertIn("script-src 'self'", self.html)


if __name__ == "__main__":
    unittest.main()
