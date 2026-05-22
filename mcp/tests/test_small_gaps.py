"""Targeted coverage uplift for the remaining tens-of-lines gaps in
the MCP package.

Each test maps to a single uncovered line or branch identified by
``pytest --cov`` after the earlier wave of edge-case tests landed.
The tests are deliberately small, hermetic, and pin one observable
contract apiece so a future refactor that changes the guard's shape
breaks immediately rather than silently regressing coverage.

Coverage scope:

* ``splunk_uc_mcp.catalog``
  - ``_resolve_catalog_root`` return-None fall-through (line 173)
  - ``_read_local`` corrupt-JSON branch (lines 289-290)
  - ``_fetch_remote`` invalid-UTF-8 + corrupt-remote-JSON branches
    (lines 316-317, 322-323)
* ``splunk_uc_mcp.tools.compliance``
  - ``_equipment_overlay`` endpoint-derived regulationId branch
    (lines 233-234)
  - ``get_clause_coverage`` version-too-long guard (line 511)
  - ``list_uncovered_clauses`` tier/limit type guards (lines 586, 594)
  - ``list_uncovered_clauses`` skip on missing regulationId (line 608)
  - ``list_uncovered_clauses`` include_common_only filter (line 627)
  - ``_is_common_clause`` ``onCommonList`` short-circuit (line 677)
* ``splunk_uc_mcp.tools.regulation``
  - jurisdiction non-string guard (line 161)
  - tag non-string guard (line 171)
  - ``_available_versions`` fall-through (line 249)
* ``splunk_uc_mcp.tools.search``
  - query non-string guard (line 203)
* ``splunk_uc_mcp.resources.uri_scheme``
  - ``make_equipment_uri`` invalid slug (line 229)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from splunk_uc_mcp.catalog import Catalog, CatalogError
from splunk_uc_mcp.resources.uri_scheme import (
    ResourceUriError,
    make_equipment_uri,
)
from splunk_uc_mcp.tools.compliance import (
    _equipment_overlay,
    _is_common_clause,
    get_clause_coverage,
    list_uncovered_clauses,
)
from splunk_uc_mcp.tools.regulation import (
    _available_versions,
    list_regulations,
)
from splunk_uc_mcp.tools.search import search_use_cases

# --------------------------------------------------------------------- #
# catalog.py — _resolve_catalog_root fall-through to None
# --------------------------------------------------------------------- #


def test_resolve_catalog_root_returns_none_when_all_probes_miss(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``_resolve_catalog_root(None)`` must return ``None`` when the
    env var is unset, the cwd lacks ``api/v1/manifest.json``, and
    none of the package's ancestors carry one either (covers
    catalog.py line 173 — the final ``return None``).

    We engineer all three misses by:
      1. Deleting ``SPLUNK_UC_CATALOG_ROOT`` so the env-var branch
         skips immediately.
      2. ``monkeypatch.chdir`` into an empty tmp dir so the cwd
         probe falls through.
      3. Patching ``Catalog.__module__``'s ``Path(__file__)`` to a
         file deep inside the same empty tmp dir so every ancestor
         walk also misses.
    """

    from splunk_uc_mcp import catalog as catalog_mod

    monkeypatch.delenv("SPLUNK_UC_CATALOG_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)
    # Place a fake __file__ several directories deep so every
    # ancestor walk fails. The path itself does not need to exist
    # because the resolver only consults its parents.
    fake_module = tmp_path / "a" / "b" / "c" / "fake_module.py"
    fake_module.parent.mkdir(parents=True)
    fake_module.write_text("", encoding="utf-8")
    monkeypatch.setattr(catalog_mod, "__file__", str(fake_module))

    result = Catalog._resolve_catalog_root(None)
    assert result is None


# --------------------------------------------------------------------- #
# catalog.py — _read_local corrupt-JSON branch
# --------------------------------------------------------------------- #


def test_read_local_raises_catalog_error_on_corrupt_json(
    tmp_path: Path,
) -> None:
    """A locally-stored JSON file that fails to parse must raise
    :class:`CatalogError`, not propagate the raw
    :class:`json.JSONDecodeError`. Covers catalog.py lines 289-290."""

    bad = tmp_path / "broken.json"
    bad.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(CatalogError, match="Corrupt JSON"):
        Catalog._read_local(bad)


# --------------------------------------------------------------------- #
# catalog.py — _fetch_remote error branches
# --------------------------------------------------------------------- #


def test_fetch_remote_raises_catalog_error_on_invalid_utf8(
    tmp_path: Path,
) -> None:
    """Bytes that are not valid UTF-8 must surface as
    :class:`CatalogError`, not :class:`UnicodeDecodeError`. Covers
    catalog.py lines 316-317.

    ``respx`` would coerce a ``content=`` argument through pydantic
    and lose the raw bytes, so we drive the helper directly with a
    minimal stubbed ``httpx.Client.stream`` that yields the bad
    chunk via the iter_bytes protocol.

    The base_url must satisfy ``_ALLOWED_BASE_URL`` (github.io /
    githubusercontent.com only) — we use the production default so
    the constructor doesn't reject it. The stub never actually
    talks to that URL.
    """

    with Catalog(
        catalog_root=None,
        base_url="https://fenre.github.io/splunk-monitoring-use-cases",
    ) as cat:
        # Build a fake stream context manager. The real method does:
        #   with client.stream("GET", url, ...) as resp:
        #       if resp.status_code == 404: raise NotFound
        #       resp.raise_for_status()
        #       for chunk in resp.iter_bytes(): body.extend(chunk)
        bad_bytes = b"\xff\xfe\xfd"  # lone surrogates -> UnicodeDecodeError

        class _StubResp:
            status_code = 200

            def raise_for_status(self) -> None:
                return None

            def iter_bytes(self) -> Any:
                yield bad_bytes

        class _StubStreamCtx:
            def __enter__(self) -> _StubResp:
                return _StubResp()

            def __exit__(self, *exc: Any) -> None:
                return None

        client = MagicMock()
        client.stream.return_value = _StubStreamCtx()
        # Inject the stub into Catalog so the real httpx.Client never
        # gets built; this keeps the test fully offline.
        cat._http_client = client  # type: ignore[attr-defined]

        with pytest.raises(CatalogError, match="Invalid UTF-8"):
            cat._fetch_remote(["api", "v1", "stub.json"])


def test_fetch_remote_raises_catalog_error_on_corrupt_remote_json(
    tmp_path: Path,
) -> None:
    """Valid UTF-8 that is not parseable JSON must surface as
    :class:`CatalogError` (catalog.py lines 322-323) rather than
    leaking the raw :class:`json.JSONDecodeError`."""

    with Catalog(
        catalog_root=None,
        base_url="https://fenre.github.io/splunk-monitoring-use-cases",
    ) as cat:

        class _StubResp:
            status_code = 200

            def raise_for_status(self) -> None:
                return None

            def iter_bytes(self) -> Any:
                yield b"{this is not valid json"

        class _StubStreamCtx:
            def __enter__(self) -> _StubResp:
                return _StubResp()

            def __exit__(self, *exc: Any) -> None:
                return None

        client = MagicMock()
        client.stream.return_value = _StubStreamCtx()
        cat._http_client = client  # type: ignore[attr-defined]

        with pytest.raises(CatalogError, match="Corrupt JSON"):
            cat._fetch_remote(["api", "v1", "stub.json"])


def test_load_json_falls_through_to_remote_when_catalog_root_is_none(
    tmp_path: Path,
) -> None:
    """Pin catalog.py branch 239->244: when ``_catalog_root`` is
    ``None`` (remote-only mode), ``load_json`` must skip the local
    short-circuit entirely and dispatch to ``_fetch_remote``.

    The local short-circuit covers the True arm of
    ``if self._catalog_root is not None:`` — every test that runs
    against the live or synthetic catalogues exercises that arm.
    The False arm only fires when the catalogue is initialised
    without a local root, which is the deploy shape for the
    Cloudflare-Pages-hosted MCP server. Without this test the False
    arm was uncovered and a regression that accidentally guarded
    ``_fetch_remote`` behind ``_catalog_root`` would silently break
    every remote-only deployment.

    ``Catalog._resolve_catalog_root`` probes ``Path.cwd()`` and
    ``__file__.parents`` for ``api/v1/manifest.json``; both probes
    succeed in this repo's test runner, so we forcibly overwrite
    ``_catalog_root`` after construction to simulate the deploy
    shape rather than chase a sandbox-fragile cwd patch.
    """

    payload = {"hello": "world", "n": 42}

    with Catalog(
        catalog_root=None,
        base_url="https://fenre.github.io/splunk-monitoring-use-cases",
    ) as cat:
        # Force remote-only mode regardless of the test runner's cwd.
        cat._catalog_root = None  # type: ignore[attr-defined]

        class _StubResp:
            status_code = 200

            def raise_for_status(self) -> None:
                return None

            def iter_bytes(self) -> Any:
                # Two-chunk emit to also exercise the chunk-loop's
                # extend path even though that branch is already
                # covered elsewhere — costs nothing, locks the
                # contract.
                yield b'{"hello": "world"'
                yield b', "n": 42}'

        class _StubStreamCtx:
            def __enter__(self) -> _StubResp:
                return _StubResp()

            def __exit__(self, *exc: Any) -> None:
                return None

        client = MagicMock()
        client.stream.return_value = _StubStreamCtx()
        cat._http_client = client  # type: ignore[attr-defined]

        out = cat.load_json("api", "v1", "stub.json")
        assert out == payload
        # Sanity: the stub HTTP client was actually invoked, which
        # proves we went through ``_fetch_remote`` and not some
        # cached local short-circuit.
        assert client.stream.called


# --------------------------------------------------------------------- #
# tools/compliance.py
# --------------------------------------------------------------------- #


def test_equipment_overlay_derives_reg_id_from_endpoint_when_missing() -> None:
    """If an equipment regulation entry omits ``regulationId``, the
    overlay helper must derive it from the trailing component of
    ``regulationEndpoint`` (covers tools/compliance.py lines
    233-234). Verify the derivation works for both plain
    ``/<id>.json`` and versioned ``/<id>@<ver>.json`` endpoints."""

    equipment_doc = {
        "id": "azure",
        "regulations": [
            # Plain endpoint: /gdpr.json -> reg_id "gdpr"
            {
                "regulationEndpoint": "/api/v1/compliance/regulations/gdpr.json",
                "clauseMappings": [{"clause": "Art.5"}],
            },
            # Versioned endpoint: /pci@4-0.json -> reg_id "pci"
            {
                "regulationEndpoint": "/api/v1/compliance/regulations/pci@4-0.json",
                "clauseMappings": [{"clause": "1.1"}],
            },
            # Endpoint missing entirely -> reg_id becomes "" -> never matches
            {"clauseMappings": [{"clause": "X.X"}]},
        ],
    }
    gap_entry = {"commonClausesUncovered": ["Art.5", "Art.17"]}

    # Asking for the gdpr overlay should pick up the first entry only.
    result = _equipment_overlay(equipment_doc, "gdpr", gap_entry)
    assert result["clausesCoveredByEquipment"] == ["Art.5"]
    assert result["uncoveredClausesStillUncovered"] == ["Art.17"]

    # Asking for the pci overlay should pick up only the second entry.
    pci = _equipment_overlay(
        equipment_doc,
        "pci",
        {"commonClausesUncovered": ["1.1", "1.2"]},
    )
    assert pci["clausesCoveredByEquipment"] == ["1.1"]
    assert pci["uncoveredClausesStillUncovered"] == ["1.2"]


def test_get_clause_coverage_rejects_long_version(
    synthetic_catalog: Catalog,
) -> None:
    """``version`` is capped at 64 chars to prevent absurd payloads
    from reaching the catalog lookup. Covers compliance.py line 511."""

    with pytest.raises(ValueError, match="<= 64 characters"):
        get_clause_coverage(
            catalog=synthetic_catalog,
            regulation_id="gdpr",
            clause="Art.5",
            version="x" * 65,
        )


def test_list_uncovered_clauses_rejects_non_int_tier(
    synthetic_catalog: Catalog,
) -> None:
    """Tier must be an int (not a bool, not a string, not a float).
    Covers compliance.py line 586. The bool exclusion is important
    because ``isinstance(True, int)`` is True in Python."""

    with pytest.raises(ValueError, match="tier must be an integer"):
        list_uncovered_clauses(
            catalog=synthetic_catalog,
            regulations=["gdpr"],
            tier="1",  # type: ignore[arg-type]
        )
    # bool is also rejected even though Python treats it as int.
    with pytest.raises(ValueError, match="tier must be an integer"):
        list_uncovered_clauses(
            catalog=synthetic_catalog,
            regulations=["gdpr"],
            tier=True,
        )


def test_list_uncovered_clauses_rejects_non_int_limit(
    synthetic_catalog: Catalog,
) -> None:
    """``limit`` follows the same integer-only contract as tier.
    Covers compliance.py line 594."""

    with pytest.raises(ValueError, match="limit must be an integer"):
        list_uncovered_clauses(
            catalog=synthetic_catalog,
            regulations=["gdpr"],
            limit="50",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="limit must be an integer"):
        list_uncovered_clauses(
            catalog=synthetic_catalog,
            regulations=["gdpr"],
            limit=False,
        )


def test_list_uncovered_clauses_skips_entries_without_regulation_id(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog: Catalog,
) -> None:
    """Defensive guard: any clause index entry without
    ``regulationId`` is silently skipped. Covers compliance.py
    line 608 (the ``if not rid: continue`` branch).

    We monkeypatch the index loader to return one bad entry and one
    good entry, then assert only the good one appears in matches.
    """

    def _load_json(*segments: str) -> dict[str, Any]:
        assert segments == ("compliance", "clauses", "index.json")
        return {
            "clauses": [
                # No regulationId -> hits line 608 (continue)
                {
                    "clause": "Orphan",
                    "coverageState": "uncovered",
                    "priorityWeight": 1.0,
                },
                # Good entry that we expect in the output
                {
                    "regulationId": "gdpr",
                    "clause": "Art.17",
                    "coverageState": "uncovered",
                    "priorityWeight": 2.0,
                    "tier": 1,
                    "topic": "data subject rights",
                },
            ]
        }

    monkeypatch.setattr(synthetic_catalog, "load_json", _load_json)

    result = list_uncovered_clauses(
        catalog=synthetic_catalog,
        regulations=["gdpr"],
    )
    assert result["count"] == 1
    assert result["entries"][0]["clause"] == "Art.17"
    # The orphan entry must not surface even via wildcard either.


def test_list_uncovered_clauses_drops_non_common_when_filter_enabled(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_catalog: Catalog,
) -> None:
    """``include_common_only=True`` must drop entries that
    ``_is_common_clause`` declares uncommon (covers compliance.py
    line 627). We craft two entries — one with the priorityWeight +
    topic signal that marks a common clause, and one without — and
    assert only the common one survives."""

    def _load_json(*segments: str) -> dict[str, Any]:
        return {
            "clauses": [
                # Uncommon: no priorityWeight, no topic -> _is_common_clause False
                {
                    "regulationId": "gdpr",
                    "clause": "Uncommon",
                    "coverageState": "uncovered",
                },
                # Common: priorityWeight + topic both set
                {
                    "regulationId": "gdpr",
                    "clause": "Common",
                    "coverageState": "uncovered",
                    "priorityWeight": 1.0,
                    "topic": "lawful basis",
                },
            ]
        }

    monkeypatch.setattr(synthetic_catalog, "load_json", _load_json)

    result = list_uncovered_clauses(
        catalog=synthetic_catalog,
        regulations=["gdpr"],
        include_common_only=True,
    )
    clauses = {e["clause"] for e in result["entries"]}
    assert clauses == {"Common"}


def test_is_common_clause_honours_explicit_on_common_list_flag() -> None:
    """When the entry carries an explicit ``onCommonList`` flag, the
    helper returns ``bool(entry["onCommonList"])`` and short-circuits
    before falling back to the priorityWeight/topic heuristic. Covers
    compliance.py line 677."""

    # Truthy onCommonList wins even when the heuristic would say False.
    assert _is_common_clause({"onCommonList": True}) is True
    # Falsy onCommonList wins even when the heuristic would say True.
    assert (
        _is_common_clause(
            {
                "onCommonList": False,
                "priorityWeight": 1.0,
                "topic": "audit",
            }
        )
        is False
    )
    # Non-bool truthy value is coerced via bool().
    assert _is_common_clause({"onCommonList": 1}) is True
    assert _is_common_clause({"onCommonList": 0}) is False


# --------------------------------------------------------------------- #
# tools/regulation.py
# --------------------------------------------------------------------- #


def test_list_regulations_rejects_non_string_jurisdiction(
    synthetic_catalog: Catalog,
) -> None:
    """``jurisdiction`` must be a string, not an int or list. Covers
    regulation.py line 161."""

    with pytest.raises(ValueError, match="jurisdiction must be a string"):
        list_regulations(
            catalog=synthetic_catalog,
            jurisdiction=123,  # type: ignore[arg-type]
        )


def test_list_regulations_rejects_non_string_tag(
    synthetic_catalog: Catalog,
) -> None:
    """``tag`` must be a string. Covers regulation.py line 171."""

    with pytest.raises(ValueError, match="tag must be a string"):
        list_regulations(
            catalog=synthetic_catalog,
            tag=42,  # type: ignore[arg-type]
        )


def test_available_versions_returns_empty_when_regulation_id_missing(
    synthetic_catalog: Catalog,
) -> None:
    """``_available_versions`` falls through to ``[]`` when the
    catalogue index has no framework matching the given id. Covers
    regulation.py line 249. The synthetic catalog ships only
    ``gdpr``, so an unknown slug hits the fall-through."""

    assert _available_versions(synthetic_catalog, "nonexistent_reg") == []


# --------------------------------------------------------------------- #
# tools/search.py
# --------------------------------------------------------------------- #


def test_search_use_cases_rejects_non_string_query(
    synthetic_catalog: Catalog,
) -> None:
    """``query`` must be a string when provided. Covers search.py
    line 203 — the ``not isinstance(query, str)`` ValueError path."""

    with pytest.raises(ValueError, match="query must be a string"):
        search_use_cases(
            catalog=synthetic_catalog,
            query=[1, 2, 3],  # type: ignore[arg-type]
        )


# --------------------------------------------------------------------- #
# resources/uri_scheme.py
# --------------------------------------------------------------------- #


def test_make_equipment_uri_rejects_invalid_slug() -> None:
    """``make_equipment_uri`` validates the slug against
    ``EQUIPMENT_ID_REGEX`` (lowercase alphanumeric + underscore,
    must start with [a-z0-9]). Covers uri_scheme.py line 229."""

    # Uppercase letter -> rejected.
    with pytest.raises(ResourceUriError, match="equipment_id must match"):
        make_equipment_uri("Azure")
    # Hyphen is allowed in regulation IDs but NOT equipment IDs.
    with pytest.raises(ResourceUriError):
        make_equipment_uri("azure-vm")
    # Empty string -> rejected.
    with pytest.raises(ResourceUriError):
        make_equipment_uri("")
