"""Tests for :mod:`splunk_uc_mcp.catalog`.

Covers:
- Local-first read behaviour with a real and a synthetic ``api/v1`` tree.
- HTTPS fallback + allow-listed base URL enforcement.
- Path-traversal / case-sensitivity / oversize rejection.
- Payload-cap enforcement for both local and remote loads.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from splunk_uc_mcp.catalog import (
    Catalog,
    CatalogError,
    CatalogNotFoundError,
    CatalogValidationError,
    DEFAULT_BASE_URL,
    MAX_PAYLOAD_BYTES,
)


class TestCatalogRootResolution:
    def test_explicit_root(self, repo_root: Path) -> None:
        cat = Catalog(catalog_root=repo_root)
        assert cat.catalog_root == repo_root.resolve()
        cat.close()

    def test_explicit_root_missing_manifest(self, tmp_path: Path) -> None:
        with pytest.raises(CatalogValidationError, match="manifest"):
            Catalog(catalog_root=tmp_path)

    def test_explicit_root_expands_user(
        self, repo_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HOME", str(repo_root))
        cat = Catalog(catalog_root=Path("~"))
        assert cat.catalog_root == repo_root.resolve()
        cat.close()

    def test_default_probes_cwd(
        self, repo_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(repo_root)
        cat = Catalog()
        assert cat.catalog_root == repo_root
        cat.close()

    def test_default_probes_package_ancestors(
        self, repo_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        cat = Catalog()
        assert cat.catalog_root == repo_root
        cat.close()


class TestBaseUrlValidation:
    def test_default_base_url(self) -> None:
        cat = Catalog()
        assert cat.base_url == DEFAULT_BASE_URL.rstrip("/")
        cat.close()

    def test_trailing_slash_stripped(self) -> None:
        cat = Catalog(base_url=DEFAULT_BASE_URL + "/")
        assert cat.base_url == DEFAULT_BASE_URL.rstrip("/")
        cat.close()

    @pytest.mark.parametrize(
        "base_url",
        [
            "http://fenre.github.io/splunk-monitoring-use-cases",  # http
            "https://evil.com/splunk",
            "https://fenre.github.io.evil.com/splunk",  # dodgy suffix
            "https://fenre.github.io/../../other",  # traversal
            "ftp://fenre.github.io/splunk",
            "https://",
        ],
    )
    def test_rejects_bad_base_url(self, base_url: str) -> None:
        with pytest.raises(CatalogValidationError):
            Catalog(base_url=base_url)

    def test_empty_string_falls_back_to_default(self) -> None:
        """Empty string is treated as "no value provided"."""

        cat = Catalog(base_url="")
        assert cat.base_url == DEFAULT_BASE_URL.rstrip("/")
        cat.close()

    def test_accepts_githubusercontent(self) -> None:
        cat = Catalog(
            base_url="https://raw.githubusercontent.com/fenre/splunk/main"
        )
        assert cat.base_url.startswith("https://raw.githubusercontent.com")
        cat.close()


class TestLocalRead:
    def test_load_manifest(self, live_catalog: Catalog) -> None:
        m = live_catalog.load_json("manifest.json")
        assert m["apiVersion"] == "v1"
        assert "endpoints" in m

    def test_load_nested(self, live_catalog: Catalog) -> None:
        index = live_catalog.load_json("compliance", "ucs", "index.json")
        assert "items" in index
        assert len(index["items"]) > 0

    def test_load_recommender_uc_thin(self, live_catalog: Catalog) -> None:
        thin = live_catalog.load_json("recommender", "uc-thin.json")
        use_cases = thin["useCases"]
        assert len(use_cases) > 1000  # real catalogue has ~6,400 UCs

    def test_load_synthetic(self, synthetic_catalog: Catalog) -> None:
        m = synthetic_catalog.load_json("manifest.json")
        assert m["apiVersion"] == "v1"
        thin = synthetic_catalog.load_json("recommender", "uc-thin.json")
        assert len(thin["useCases"]) == 2


class TestPathValidation:
    @pytest.mark.parametrize(
        "segments",
        [
            ("manifest.JSON",),  # uppercase extension
            ("manifest",),  # missing .json
            ("/etc/passwd",),  # absolute path
            (".hidden.json",),  # leading dot
            ("../manifest.json",),
            ("mani fest.json",),  # whitespace
            ("manifest;.json",),  # shell metachar
            ("manifest\n.json",),  # newline
        ],
    )
    def test_rejects_bad_filename(
        self, live_catalog: Catalog, segments: tuple[str, ...]
    ) -> None:
        with pytest.raises(CatalogValidationError):
            live_catalog.load_json(*segments)

    @pytest.mark.parametrize(
        "dir_segment",
        [
            "../compliance",
            "UPPERCASE",
            "comp liance",
            "comp.liance",  # dots disallowed in dirs
            "",
        ],
    )
    def test_rejects_bad_directory(
        self, live_catalog: Catalog, dir_segment: str
    ) -> None:
        with pytest.raises(CatalogValidationError):
            live_catalog.load_json(dir_segment, "index.json")

    def test_rejects_empty_segments(self, live_catalog: Catalog) -> None:
        with pytest.raises(CatalogValidationError, match="at least one"):
            live_catalog.load_json()

    def test_rejects_oversize_segment(self, live_catalog: Catalog) -> None:
        too_long = "a" * 200 + ".json"
        with pytest.raises(CatalogValidationError, match="1-128"):
            live_catalog.load_json(too_long)


class TestLocalFallback:
    """When the local file is missing, fall through to the HTTPS mirror."""

    @respx.mock
    def test_local_miss_falls_back_to_remote(
        self, synthetic_catalog: Catalog
    ) -> None:
        expected = {"apiVersion": "v1", "items": ["from-remote"]}
        route = respx.get(
            f"{synthetic_catalog.base_url}/api/v1/equipment/stub.json"
        ).respond(200, json=expected)

        got = synthetic_catalog.load_json("equipment", "stub.json")
        assert got == expected
        assert route.called

    @respx.mock
    def test_remote_404_raises_not_found(
        self, synthetic_catalog: Catalog
    ) -> None:
        respx.get(
            f"{synthetic_catalog.base_url}/api/v1/doesnotexist.json"
        ).respond(404)

        with pytest.raises(CatalogNotFoundError):
            synthetic_catalog.load_json("doesnotexist.json")

    @respx.mock
    def test_remote_network_error_wraps_in_catalog_error(
        self, synthetic_catalog: Catalog
    ) -> None:
        respx.get(
            f"{synthetic_catalog.base_url}/api/v1/missing.json"
        ).mock(side_effect=httpx.ConnectError("boom"))

        with pytest.raises(CatalogError, match="Remote fetch failed"):
            synthetic_catalog.load_json("missing.json")


class TestPayloadCap:
    def test_local_oversize_rejected(self, tmp_path: Path) -> None:
        v1 = tmp_path / "api" / "v1"
        v1.mkdir(parents=True)
        (v1 / "manifest.json").write_text(json.dumps({"apiVersion": "v1"}))
        huge = v1 / "huge.json"
        with huge.open("wb") as f:
            f.seek(MAX_PAYLOAD_BYTES + 10)
            f.write(b"0")
        cat = Catalog(catalog_root=tmp_path)
        with pytest.raises(CatalogError, match="MAX_PAYLOAD_BYTES"):
            cat.load_json("huge.json")
        cat.close()

    @respx.mock
    def test_remote_oversize_rejected(
        self, synthetic_catalog: Catalog
    ) -> None:
        chunks = [b"x" * (1024 * 1024)] * (MAX_PAYLOAD_BYTES // (1024 * 1024) + 2)

        def streamer(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"".join(chunks))

        respx.get(
            f"{synthetic_catalog.base_url}/api/v1/oversize.json"
        ).mock(side_effect=streamer)
        with pytest.raises(CatalogError, match="MAX_PAYLOAD_BYTES"):
            synthetic_catalog.load_json("oversize.json")


class TestDataFile:
    def test_reads_ledger(self, live_catalog: Catalog) -> None:
        ledger = live_catalog.load_data_file("provenance/mapping-ledger.json")
        assert ledger is not None
        assert "merkleRoot" in ledger
        assert "entries" in ledger

    def test_rejects_absolute_path(self, live_catalog: Catalog) -> None:
        with pytest.raises(CatalogValidationError):
            live_catalog.load_data_file("/etc/passwd")

    @pytest.mark.parametrize(
        "bad",
        [
            "provenance/../secrets.json",
            "../../etc/passwd",
            ".hidden.json",
        ],
    )
    def test_rejects_traversal(self, live_catalog: Catalog, bad: str) -> None:
        with pytest.raises(CatalogValidationError):
            live_catalog.load_data_file(bad)

    def test_missing_file_raises_not_found(
        self, live_catalog: Catalog
    ) -> None:
        with pytest.raises(CatalogNotFoundError):
            live_catalog.load_data_file("provenance/does-not-exist.json")

    def test_remote_only_returns_none(self, tmp_path: Path) -> None:
        cat = Catalog()
        cat._catalog_root = None  # type: ignore[attr-defined]
        result = cat.load_data_file("provenance/mapping-ledger.json")
        assert result is None
        cat.close()


class TestContextManager:
    def test_context_manager_closes_owned_client(self) -> None:
        with Catalog() as cat:
            client = cat._ensure_http_client()  # type: ignore[attr-defined]
            assert not client.is_closed
        assert client.is_closed

    def test_external_client_not_closed(self) -> None:
        http = httpx.Client()
        with Catalog(http_client=http) as cat:
            assert cat._http_client is http  # type: ignore[attr-defined]
        assert not http.is_closed
        http.close()
