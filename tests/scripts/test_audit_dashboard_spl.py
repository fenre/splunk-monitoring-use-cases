"""Unit tests for ``python3 -m splunk_uc audit-dashboard-spl``.

These tests run without any live Splunk. They cover the token-expansion
logic that turns ``$status_filter$`` into the actual SPL substring sent
to splunkd. The implementations dashboard 400-error bug shipped because
the multiselect token's ``<delimiter>`` was ``,`` (CSV) but the
inputlookup-context downstream needed `` OR ``. A unit test here means
we can catch that class of mistake even on PRs where no Splunk is
running.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import textwrap
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


# P6 (scripts taxonomy, 2026-05-09): the audit body now lives at
# src/splunk_uc/audits/dashboard_spl.py with a thin shim at the
# original scripts/ path. Importing the implementation module
# directly keeps the test surface aligned with the migrated suite.
# The legacy spec-loader path is preserved as a fallback for an
# unpacked sdist that lost the src/ tree.
def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    try:
        import splunk_uc.audits.dashboard_spl as impl

        return impl
    except ImportError:
        pass
    target = repo_root / "scripts" / "audit_dashboard_spl.py"
    spec = importlib.util.spec_from_file_location("audit_dashboard_spl", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {target}")
    module = importlib.util.module_from_spec(spec)
    # Python 3.14's @dataclass decorator introspects sys.modules to
    # resolve the class' __module__; the module must be registered
    # BEFORE exec_module runs or the decorator raises AttributeError.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit = _load_module()


# ---- token expansion -------------------------------------------------


class TokenExpansionTests(unittest.TestCase):
    """Regression-grade tests for ``_expand_tokens`` and ``TokenSpec.expand``."""

    def test_multiselect_or_delimiter(self) -> None:
        # This is exactly the implementations.xml shape (post-fix).
        spec = audit.TokenSpec(
            token="status_filter",
            type="multiselect",
            default="not_started,in_progress,implemented,needs_review",
            delimiter=" OR ",
            prefix="(",
            suffix=")",
            value_prefix='status="',
            value_suffix='"',
        )
        expanded = spec.expand()
        self.assertEqual(
            expanded,
            '(status="not_started" OR status="in_progress" '
            'OR status="implemented" OR status="needs_review")',
        )

    def test_multiselect_csv_delimiter_is_invalid_for_inputlookup(self) -> None:
        # The pre-fix shape -- generates the SPL Splunk rejected.
        # The point isn't that this expansion is "wrong" semantically;
        # the point is that THIS shape, when concatenated after
        # inputlookup, produces invalid SPL. The audit (when run live)
        # would catch it; here we lock in the expansion shape so any
        # future "fix" that silently flips the delimiter back to "," is
        # caught by code review.
        spec = audit.TokenSpec(
            token="status_filter",
            type="multiselect",
            default="not_started,in_progress",
            delimiter=",",
            prefix="(",
            suffix=")",
            value_prefix='status="',
            value_suffix='"',
        )
        self.assertEqual(spec.expand(), '(status="not_started",status="in_progress")')

    def test_dropdown_default_wildcard(self) -> None:
        spec = audit.TokenSpec(token="reg", type="dropdown", default="*")
        self.assertEqual(spec.expand(), "*")

    def test_text_default_passthrough(self) -> None:
        spec = audit.TokenSpec(token="q", type="text", default="*")
        self.assertEqual(spec.expand(), "*")

    def test_empty_default_returns_empty(self) -> None:
        spec = audit.TokenSpec(token="q", type="text", default="")
        self.assertEqual(spec.expand(), "")

    def test_drilldown_token_substitutes_to_empty(self) -> None:
        out = audit._expand_tokens("foo $row.uc_id$ bar", {})
        self.assertEqual(out, "foo  bar")

    def test_unknown_token_substitutes_to_empty(self) -> None:
        # We log unknown tokens via the warnings list elsewhere; the
        # substitution itself returns "" so the surrounding SPL still
        # has a fighting chance to parse.
        out = audit._expand_tokens("foo $not_defined_anywhere$ bar", {})
        self.assertEqual(out, "foo  bar")

    def test_full_implementations_query_expands_correctly(self) -> None:
        # End-to-end: the actual implementations.xml table query +
        # inputs, post-fix, should produce a query Splunk can parse.
        xml = textwrap.dedent(
            """\
            <form>
              <fieldset>
                <input type="multiselect" token="status_filter">
                  <default>not_started,in_progress,implemented,needs_review</default>
                  <delimiter> OR </delimiter>
                  <prefix>(</prefix>
                  <suffix>)</suffix>
                  <valuePrefix>status="</valuePrefix>
                  <valueSuffix>"</valueSuffix>
                </input>
              </fieldset>
              <row><panel><table><search>
                <query>| inputlookup uc_recommender_implementations | where $status_filter$ | table uc_id status</query>
              </search></table></panel></row>
            </form>
            """
        )
        root = ET.fromstring(xml)
        specs = audit._parse_inputs(root)
        for elem in root.iter():
            if audit._strip_ns(elem.tag) == "query":
                query = elem.text or ""
                expanded = audit._expand_tokens(query, specs)
                self.assertIn(
                    'where (status="not_started" OR status="in_progress" '
                    'OR status="implemented" OR status="needs_review")',
                    expanded,
                )
                # Critically, the broken pre-fix shape MUST NOT appear.
                self.assertNotIn('(status="not_started",', expanded)
                return
        self.fail("did not find a <query> element to expand")

    def test_compliance_token_substitution_is_inert(self) -> None:
        # Defaults of "*" inside `regulation="$reg$"` produce
        # `regulation="*"` which Splunk's `search` happily wildcards.
        xml = textwrap.dedent(
            """\
            <form>
              <fieldset>
                <input type="dropdown" token="reg"><default>*</default></input>
                <input type="dropdown" token="crit"><default>*</default></input>
                <input type="text" token="q"><default>*</default></input>
              </fieldset>
              <row><panel><table><search>
                <query>| inputlookup uc_compliance_mappings | search regulation="$reg$" criticality="$crit$" title="*$q$*"</query>
              </search></table></panel></row>
            </form>
            """
        )
        root = ET.fromstring(xml)
        specs = audit._parse_inputs(root)
        for elem in root.iter():
            if audit._strip_ns(elem.tag) == "query":
                expanded = audit._expand_tokens(elem.text or "", specs)
                self.assertIn('regulation="*"', expanded)
                self.assertIn('criticality="*"', expanded)
                # `title="*$q$*"` with $q$=* expands to title="***", which
                # Splunk's `search` command happily wildcards.
                self.assertIn('title="***"', expanded)
                return
        self.fail("did not find a <query> element to expand")


# ---- panel collection ------------------------------------------------


class PanelCollectionTests(unittest.TestCase):
    """Verify ``_collect_panels`` finds every <query> in a real dashboard."""

    def test_collects_all_panels_in_recommender_app(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        views = repo_root / "splunk-apps/splunk-uc-recommender/default/data/ui/views"
        if not views.is_dir():
            self.skipTest(
                "recommender app not generated; run python3 -m splunk_uc generate-recommender-app first"
            )

        all_panels = []
        for fp in sorted(views.glob("*.xml")):
            panels, warnings = audit._collect_panels(fp)
            self.assertEqual(warnings, [], f"{fp.name} produced warnings: {warnings}")
            all_panels.extend(panels)

        self.assertGreater(
            len(all_panels),
            0,
            "expected at least one dashboard panel; did the generator run?",
        )

        for panel in all_panels:
            # Every collected panel must have at least started with a
            # pipe or a search command -- otherwise the audit downstream
            # will dispatch garbage.
            self.assertTrue(
                panel.spl.startswith("|") or panel.spl.split()[0] in {"search", "tstats"},
                f"{panel.view}::{panel.panel} does not start with a recognized SPL command:"
                f"\n  {panel.spl[:120]}",
            )

    def test_implementations_table_query_does_not_contain_legacy_csv_join(self) -> None:
        # This is the regression-lock for the bug we just fixed. If
        # someone "simplifies" the multiselect delimiter back to ","
        # (or drops the `where` clause and goes back to inlining the
        # token directly after `inputlookup`), this test fails before
        # the smoke phase ever runs.
        repo_root = Path(__file__).resolve().parents[2]
        impl_xml = (
            repo_root
            / "splunk-apps/splunk-uc-recommender/default/data/ui/views/implementations.xml"
        )
        if not impl_xml.exists():
            self.skipTest("implementations.xml not generated yet")
        text = impl_xml.read_text()
        self.assertIn("<delimiter> OR </delimiter>", text)
        self.assertIn("| inputlookup uc_recommender_implementations | where $status_filter$", text)
        # Forbid the broken pre-fix patterns explicitly.
        self.assertNotIn(
            "| inputlookup uc_recommender_implementations $status_filter$",
            text,
            "implementations.xml regressed: token must NOT be inlined directly after inputlookup",
        )


if __name__ == "__main__":
    unittest.main()
