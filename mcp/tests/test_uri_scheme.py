"""Tests for ``splunk_uc_mcp.resources.uri_scheme``.

Covers the happy paths (every URI family round-trips correctly) and a
thorough set of adversarial inputs. Path traversal, case-sensitivity
bypass, oversize identifiers, unsupported schemes, and accidental URL
escape codes must all be rejected with :class:`ResourceUriError`.
"""

from __future__ import annotations

import pytest

from splunk_uc_mcp.resources import (
    LEDGER_URI,
    parse_resource_uri,
    make_use_case_uri,
    make_regulation_uri,
    make_equipment_uri,
    make_ledger_uri,
)
from splunk_uc_mcp.resources.uri_scheme import ResourceUriError


class TestParseUseCaseUri:
    def test_basic_usecase(self) -> None:
        p = parse_resource_uri("uc://usecase/22.1.1")
        assert p.kind == "use_case"
        assert p.identifier == "22.1.1"
        assert p.version is None

    @pytest.mark.parametrize("uc_id", ["0.0.0", "1.1.1", "22.99.42", "150.200.300"])
    def test_various_valid_ids(self, uc_id: str) -> None:
        p = parse_resource_uri(f"uc://usecase/{uc_id}")
        assert p.identifier == uc_id

    @pytest.mark.parametrize(
        "bad_uri",
        [
            "uc://usecase/22.1",  # missing third component
            "uc://usecase/22.1.1.5",  # too many components
            "uc://usecase/a.b.c",  # non-numeric
            "uc://usecase/22.01.1",  # leading zero
            "uc://usecase/",  # empty id
            "uc://usecase",  # missing trailing slash and id
            "uc://usecase/../../etc/passwd",
            "uc://usecase/22.1.1/extra",
        ],
    )
    def test_rejects_malformed_usecase(self, bad_uri: str) -> None:
        with pytest.raises(ResourceUriError):
            parse_resource_uri(bad_uri)


class TestParseCategoryUri:
    def test_basic_category(self) -> None:
        p = parse_resource_uri("uc://category/22")
        assert p.kind == "category"
        assert p.identifier == "22"

    @pytest.mark.parametrize(
        "bad_uri",
        [
            "uc://category/22.1",  # subcategory; not supported by URI (use tool)
            "uc://category/abc",
            "uc://category/",
            "uc://category/01",  # leading zero
        ],
    )
    def test_rejects_malformed_category(self, bad_uri: str) -> None:
        with pytest.raises(ResourceUriError):
            parse_resource_uri(bad_uri)


class TestParseRegulationUri:
    def test_basic_regulation(self) -> None:
        p = parse_resource_uri("reg://gdpr")
        assert p.kind == "regulation"
        assert p.identifier == "gdpr"
        assert p.version is None

    def test_regulation_with_version(self) -> None:
        p = parse_resource_uri("reg://gdpr@2016-679")
        assert p.kind == "regulation"
        assert p.identifier == "gdpr"
        assert p.version == "2016-679"

    @pytest.mark.parametrize(
        "slug",
        ["gdpr", "hipaa-security", "pci-dss", "eu-ai-act", "nis2", "cmmc", "dora"],
    )
    def test_real_slugs_round_trip(self, slug: str) -> None:
        p = parse_resource_uri(f"reg://{slug}")
        assert p.identifier == slug

    @pytest.mark.parametrize(
        "bad_uri",
        [
            "reg://",  # empty
            "reg://GDPR",  # uppercase
            "reg://gdpr@",  # empty version
            "reg://gdpr@..",  # path traversal in version
            "reg://gdpr@2016/679",  # slash — URIs cannot carry sub-segments
            "reg://gdpr/extra",  # extra path segment
            "reg://gdpr space",
            "reg://-gdpr",  # leading hyphen
        ],
    )
    def test_rejects_malformed_regulation(self, bad_uri: str) -> None:
        with pytest.raises(ResourceUriError):
            parse_resource_uri(bad_uri)


class TestParseEquipmentUri:
    def test_basic_equipment(self) -> None:
        p = parse_resource_uri("equipment://azure")
        assert p.kind == "equipment"
        assert p.identifier == "azure"
        assert p.version is None

    @pytest.mark.parametrize(
        "slug",
        ["linux", "windows", "cisco_asa", "aws", "azure", "kubernetes", "splunk"],
    )
    def test_real_slugs_round_trip(self, slug: str) -> None:
        p = parse_resource_uri(f"equipment://{slug}")
        assert p.identifier == slug

    @pytest.mark.parametrize(
        "bad_uri",
        [
            "equipment://",
            "equipment://Azure",  # uppercase
            "equipment:///double-slash",
            "equipment://azure/extra",
            "equipment://cisco-asa",  # hyphen not in equipment regex (underscores only)
        ],
    )
    def test_rejects_malformed_equipment(self, bad_uri: str) -> None:
        with pytest.raises(ResourceUriError):
            parse_resource_uri(bad_uri)


class TestParseLedgerUri:
    def test_ledger_parses(self) -> None:
        p = parse_resource_uri(LEDGER_URI)
        assert p.kind == "ledger"
        assert p.identifier == ""
        assert p.version is None

    @pytest.mark.parametrize(
        "bad_uri",
        [
            "ledger://extra",
            "ledger:///",  # triple slash rejected
            "ledger://mapping-ledger.json",
        ],
    )
    def test_rejects_non_canonical_ledger(self, bad_uri: str) -> None:
        with pytest.raises(ResourceUriError):
            parse_resource_uri(bad_uri)


class TestAdversarial:
    @pytest.mark.parametrize(
        "bad_uri",
        [
            "",
            "http://example.com/",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "uc:usecase/22.1.1",  # single slash
            "UC://USECASE/22.1.1",  # uppercase scheme
            "uc://unknown/22.1.1",  # unsupported kind
            "uc://usecase/22.1.1" + "/" + ("a" * 300),  # oversize suffix
            "a" * 300,  # oversize URI
        ],
    )
    def test_rejects_bad_input(self, bad_uri: str) -> None:
        with pytest.raises(ResourceUriError):
            parse_resource_uri(bad_uri)

    def test_rejects_non_string(self) -> None:
        with pytest.raises(ResourceUriError):
            parse_resource_uri(None)  # type: ignore[arg-type]


class TestMakeHelpers:
    def test_make_use_case_uri_roundtrip(self) -> None:
        uri = make_use_case_uri("22.1.1")
        assert uri == "uc://usecase/22.1.1"
        assert parse_resource_uri(uri).identifier == "22.1.1"

    def test_make_use_case_uri_validates(self) -> None:
        with pytest.raises(ResourceUriError):
            make_use_case_uri("22.1")

    def test_make_regulation_uri_no_version(self) -> None:
        assert make_regulation_uri("gdpr") == "reg://gdpr"

    def test_make_regulation_uri_with_version(self) -> None:
        assert make_regulation_uri("gdpr", "2016-679") == "reg://gdpr@2016-679"

    def test_make_regulation_uri_validates_id(self) -> None:
        with pytest.raises(ResourceUriError):
            make_regulation_uri("GDPR")

    def test_make_regulation_uri_validates_version(self) -> None:
        with pytest.raises(ResourceUriError):
            make_regulation_uri("gdpr", "..")

    def test_make_equipment_uri_roundtrip(self) -> None:
        uri = make_equipment_uri("cisco_asa")
        assert uri == "equipment://cisco_asa"
        assert parse_resource_uri(uri).identifier == "cisco_asa"

    def test_make_ledger_uri(self) -> None:
        assert make_ledger_uri() == LEDGER_URI
