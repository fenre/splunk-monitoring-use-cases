"""Tests for the typed :class:`UseCase` dataclass + :class:`UseCaseDict`.

Coverage focuses on the three invariants called out in the model's
docstring:

1. **Schema-aligned construction** — ``id`` / ``title`` are required;
   malformed ``id`` is rejected with a useful message.
2. **Lossless round-trip** — JSON → :class:`UseCase` → ``to_dict`` →
   JSON yields the canonical key order from
   :data:`splunk_uc._uc_sidecar.SIDECAR_FIELD_ORDER` with every
   original key preserved.
3. **Typed access** — modelled fields surface as proper attributes;
   unmodelled fields flow through ``extras`` so the round-trip is
   stable as the schema gains optional properties.

The fixtures intentionally use real cat-1 sidecar shapes (minimal +
representative) rather than schema-derived synthetic data so the test
suite stays meaningful if the schema gains a field that is real-world
common but not yet modelled.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# The repo follows the "every test sets up its own sys.path" convention
# documented in pyproject.toml's [tool.pytest.ini_options]. Keep this
# block tight so import order stays explicit.
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from splunk_uc._uc_sidecar import SIDECAR_FIELD_ORDER  # noqa: E402
from splunk_uc.models import UseCase, UseCaseDict, load_use_case  # noqa: E402

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


def _minimal_sidecar() -> dict[str, object]:
    """A two-field sidecar — the schema's strict minimum."""
    return {
        "id": "1.1.1",
        "title": "CPU Utilization Trending (Linux)",
    }


def _full_sidecar() -> dict[str, object]:
    """A representative cat-1 sidecar exercising every modelled field.

    Field order intentionally scrambled so the round-trip test can
    prove the canonical ordering is actually applied, not just
    accidentally preserved.

    Empty arrays are deliberately *omitted* (rather than included as
    ``[]``) because:

    * The schema's minItems/required constraints already disallow
      empty arrays on every catalogue-relevant array field.
    * :class:`UseCase` treats "absent" and "explicitly empty array"
      as semantically equivalent and collapses both to ``()`` on
      the model + omits the key on :meth:`to_dict` output. That
      collapse is the documented contract; representing absent
      fields here as missing rather than ``[]`` keeps the
      round-trip test honest about that contract.
    """
    return {
        "title": "CPU Utilization Trending (Linux)",
        "spl": "index=os sourcetype=cpu | stats avg(cpu) by host",
        "id": "1.1.1",
        "criticality": "high",
        "value": "Spot host-level CPU saturation before user-visible impact.",
        "difficulty": "beginner",
        "monitoringType": ["Performance"],
        "splunkPillar": "IT Operations",
        "wave": "crawl",
        "app": "Splunk Add-on for Linux",
        "dataSources": "index=os sourcetype=cpu",
        "cimModels": ["Performance"],
        "grandmaExplanation": "We watch how busy each computer's brain is.",
        "description": "Trend CPU usage across the Linux fleet.",
        "implementation": {"steps": ["onboard nix:cpu", "build base search"]},
        "visualization": "line chart, 7-day window, split by host",
        "references": ["https://docs.splunk.com/Documentation/AddOns/latest/Nix"],
        "knownFalsePositives": "Batch jobs may legitimately drive sustained 100%.",
        "detectionType": "trend",
        "securityDomain": "endpoint",
        "requiredFields": ["host", "cpu"],
        "equipment": ["linux-server"],
        "status": "production",
        "lastReviewed": "2026-05-01",
        "splunkVersions": ["9.x", "10.x"],
        "reviewer": "fenre",
    }


# ----------------------------------------------------------------------
# Construction
# ----------------------------------------------------------------------


def test_from_dict_minimal_sidecar() -> None:
    """The two required fields are enough to build a :class:`UseCase`."""
    uc = UseCase.from_dict(_minimal_sidecar())
    assert uc.id == "1.1.1"
    assert uc.title == "CPU Utilization Trending (Linux)"
    # Optional fields default to None / ().
    assert uc.criticality is None
    assert uc.difficulty is None
    assert uc.monitoring_type == ()
    assert uc.prerequisite_use_cases == ()
    assert uc.cim_models == ()
    assert uc.extras == {}


def test_from_dict_full_sidecar_surfaces_modelled_attrs() -> None:
    """Every modelled attribute round-trips through proper typed access."""
    uc = UseCase.from_dict(_full_sidecar())
    assert uc.id == "1.1.1"
    assert uc.title == "CPU Utilization Trending (Linux)"
    assert uc.criticality == "high"
    assert uc.difficulty == "beginner"
    # Lists become tuples (immutability).
    assert uc.monitoring_type == ("Performance",)
    assert uc.splunk_pillar == "IT Operations"
    assert uc.wave == "crawl"
    assert uc.prerequisite_use_cases == ()  # explicit empty in input
    assert uc.value is not None and "saturation" in uc.value
    assert uc.app == "Splunk Add-on for Linux"
    assert uc.data_sources == "index=os sourcetype=cpu"
    assert uc.spl is not None and uc.spl.startswith("index=os")
    assert uc.cim_models == ("Performance",)
    assert uc.grandma_explanation is not None and uc.grandma_explanation.startswith(
        "We watch"
    )


def test_from_dict_unmodelled_fields_flow_through_extras() -> None:
    """Schema fields not promoted to attributes survive via ``extras``."""
    uc = UseCase.from_dict(_full_sidecar())
    # description / references / implementation are not promoted; they
    # belong to extras so a future schema change doesn't force a
    # dataclass rev.
    assert "description" in uc.extras
    assert "implementation" in uc.extras
    assert "references" in uc.extras
    # And they keep their original Python shape (no eager tuple-ification).
    assert isinstance(uc.extras["references"], list)
    assert isinstance(uc.extras["implementation"], dict)


def test_display_id_prefixes_with_UC() -> None:
    uc = UseCase.from_dict(_minimal_sidecar())
    assert uc.display_id == "UC-1.1.1"


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------


def test_from_dict_missing_id_raises() -> None:
    with pytest.raises(ValueError, match="missing required field 'id'"):
        UseCase.from_dict({"title": "no id here"})


def test_from_dict_missing_title_raises() -> None:
    with pytest.raises(ValueError, match="missing required field 'title'"):
        UseCase.from_dict({"id": "1.1.1"})


@pytest.mark.parametrize(
    "bad_id",
    [
        "UC-1.1.1",  # carries the display prefix; not allowed in the field
        "1.1",  # too few segments
        "1.1.1.1",  # too many segments
        "01.1.1",  # leading zero
        "a.b.c",  # non-numeric
        " 1.1.1 ",  # whitespace
        "",  # empty
    ],
)
def test_from_dict_bad_id_pattern_raises(bad_id: str) -> None:
    """Every input violating the X.Y.Z grammar is rejected at construction."""
    with pytest.raises(ValueError, match=r"X\.Y\.Z"):
        UseCase.from_dict({"id": bad_id, "title": "OK title here"})


def test_from_dict_non_string_id_raises() -> None:
    with pytest.raises(ValueError, match="must be a string"):
        UseCase.from_dict({"id": 111, "title": "OK"})


def test_from_dict_non_string_title_raises() -> None:
    with pytest.raises(ValueError, match="'title' must be a string"):
        UseCase.from_dict({"id": "1.1.1", "title": 42})


def test_from_dict_non_string_array_element_raises() -> None:
    """A list containing a non-string element trips ``_opt_str_tuple``."""
    with pytest.raises(ValueError, match=r"monitoringType.\[1\].*must be a string"):
        UseCase.from_dict(
            {
                "id": "1.1.1",
                "title": "OK title here",
                "monitoringType": ["Performance", 42, "Operations"],
            }
        )


def test_from_dict_non_list_array_field_raises() -> None:
    """A scalar where the schema expects an array is rejected.

    Uses ``cimModels`` since it is array-typed in the schema —
    ``dataSources`` is deliberately a free-form ``str`` (schema
    type ``"string"``), so it cannot stand in for the "must be
    array" path.
    """
    with pytest.raises(ValueError, match=r"'cimModels' must be an array"):
        UseCase.from_dict(
            {
                "id": "1.1.1",
                "title": "OK title here",
                "cimModels": "not-a-list",
            }
        )


def test_from_dict_non_string_scalar_field_raises() -> None:
    """A non-string at a string-typed field trips ``_opt_str``."""
    with pytest.raises(ValueError, match=r"'criticality' must be a string"):
        UseCase.from_dict(
            {
                "id": "1.1.1",
                "title": "OK title here",
                "criticality": 9001,
            }
        )


def test_from_dict_none_scalar_field_treated_as_absent() -> None:
    """``"field": null`` round-trips through ``None`` without erroring.

    Cat-22 backfill scripts occasionally emit ``"reviewer": null`` for
    fields they couldn't auto-populate; the model has to accept that
    rather than rejecting the entire sidecar.
    """
    uc = UseCase.from_dict(
        {
            "id": "1.1.1",
            "title": "OK title here",
            "criticality": None,
            "monitoringType": None,
        }
    )
    assert uc.criticality is None
    assert uc.monitoring_type == ()


# ----------------------------------------------------------------------
# Round-trip
# ----------------------------------------------------------------------


def test_to_dict_canonical_field_order_minimal() -> None:
    """A minimal sidecar emits ``id`` then ``title`` per ``SIDECAR_FIELD_ORDER``."""
    uc = UseCase.from_dict(_minimal_sidecar())
    out = uc.to_dict()
    assert list(out) == ["id", "title"]


def test_to_dict_canonical_field_order_full() -> None:
    """Modelled keys in ``SIDECAR_FIELD_ORDER`` are emitted in canonical order.

    The canonical sidecar order pinned by
    :data:`splunk_uc._uc_sidecar.SIDECAR_FIELD_ORDER` is the contract:
    every key in the tuple that appears in the input is emitted in
    that fixed position. Schema fields **not** in the tuple
    (currently ``wave`` and ``prerequisiteUseCases``, which are
    real schema properties but predate the tuple) flow through
    ``canonical_sidecar`` to the tail in insertion order — that is
    the documented behaviour of ``canonical_sidecar``'s second
    pass, not a leak.
    """
    uc = UseCase.from_dict(_full_sidecar())
    out = uc.to_dict()
    emitted = list(out)

    # Relative ordering of canonical keys matches the canonical pin.
    canonical_positions = {k: i for i, k in enumerate(SIDECAR_FIELD_ORDER)}
    last = -1
    for key in emitted:
        if key not in canonical_positions:
            # Schema-known but tuple-missing keys (wave / prerequisiteUseCases)
            # flow to the tail; their position is intentionally undefined
            # within the tail block but must come *after* every canonical
            # key. ``canonical_sidecar`` guarantees that.
            continue
        pos = canonical_positions[key]
        assert pos > last, (
            f"key {key!r} (pos {pos}) emitted after a later canonical key "
            f"(last seen pos {last}); order: {emitted}"
        )
        last = pos

    # Every tail key (in our fixture: only ``wave``, since
    # ``prerequisiteUseCases`` is absent) must come after the final
    # canonical key in the output.
    tail_keys = [k for k in emitted if k not in canonical_positions]
    if tail_keys:
        last_canonical_position = max(
            i for i, k in enumerate(emitted) if k in canonical_positions
        )
        first_tail_position = min(
            i for i, k in enumerate(emitted) if k not in canonical_positions
        )
        assert first_tail_position > last_canonical_position, (
            f"tail key emitted before final canonical key in {emitted}"
        )


def test_round_trip_preserves_every_key() -> None:
    """JSON → UseCase → to_dict yields the same key set."""
    sidecar = _full_sidecar()
    uc = UseCase.from_dict(sidecar)
    out = uc.to_dict()
    assert set(out) == set(sidecar)


def test_round_trip_preserves_every_value() -> None:
    """JSON → UseCase → to_dict preserves every value verbatim.

    Lists may round-trip as lists (not tuples) because the canonical
    JSON shape is lists; the test compares semantic equality, not
    identity.
    """
    sidecar = _full_sidecar()
    uc = UseCase.from_dict(sidecar)
    out = uc.to_dict()
    # Direct dict equality — lists stay lists, dicts stay dicts.
    assert out == sidecar


def test_round_trip_json_text_is_idempotent() -> None:
    """Encoding to JSON and back twice yields a stable text shape."""
    sidecar = _full_sidecar()
    once = json.dumps(UseCase.from_dict(sidecar).to_dict(), sort_keys=False, indent=2)
    twice = json.dumps(
        UseCase.from_dict(json.loads(once)).to_dict(), sort_keys=False, indent=2
    )
    assert once == twice


def test_round_trip_unknown_extras_are_appended_at_tail() -> None:
    """Schema-additional keys (lift-surface fields) survive at the tail.

    ``canonical_sidecar`` puts known keys first and unknown keys at the
    tail in insertion order. This protects against silent data loss
    when a generator stamps a debug field onto a sidecar.
    """
    sidecar = dict(_minimal_sidecar())
    sidecar["detailedImplementation"] = "lift-surface stamp"  # not in SIDECAR_FIELD_ORDER
    uc = UseCase.from_dict(sidecar)
    out = uc.to_dict()
    assert out["detailedImplementation"] == "lift-surface stamp"
    # Known keys come first.
    assert list(out)[:2] == ["id", "title"]


def test_prerequisite_use_cases_round_trip_when_present() -> None:
    """When the source sidecar specifies a non-empty ``prerequisiteUseCases``
    list, the modelled value is re-emitted intact. Pins the
    ``if self.prerequisite_use_cases`` branch on line 301."""
    sidecar = dict(_minimal_sidecar())
    sidecar["prerequisiteUseCases"] = ["1.1.1", "1.1.2"]
    uc = UseCase.from_dict(sidecar)
    out = uc.to_dict()
    assert out["prerequisiteUseCases"] == ["1.1.1", "1.1.2"]


def test_extras_do_not_overwrite_modelled_attributes_on_round_trip() -> None:
    """``UseCase.to_dict`` writes the modelled value FIRST, then merges
    extras. If an extras key collides with a modelled attribute (which
    can happen when callers manually inject conflicting keys into
    ``extras``), the modelled attribute must win. Pins the
    ``if key not in out`` defensive branch."""
    uc = UseCase.from_dict(_minimal_sidecar())
    # Force a collision: stash a value under the same key as a modelled
    # attribute. ``extras`` is bound to a dict that lives behind the
    # frozen dataclass attribute, so we use ``object.__setattr__`` to
    # rebind it without violating frozen-ness conceptually.
    object.__setattr__(uc, "extras", {**uc.extras, "id": "9.9.9-extras-injected"})
    out = uc.to_dict()
    # The modelled ``id`` value wins.
    assert out["id"] == uc.id != "9.9.9-extras-injected"


def test_to_typed_dict_returns_same_shape_as_to_dict() -> None:
    """``to_typed_dict`` is a typed view — content stays identical."""
    uc = UseCase.from_dict(_full_sidecar())
    plain = uc.to_dict()
    typed: UseCaseDict = uc.to_typed_dict()
    assert dict(typed) == plain


def test_immutability_is_enforced() -> None:
    """The dataclass is frozen — attribute assignment is a TypeError."""
    uc = UseCase.from_dict(_minimal_sidecar())
    with pytest.raises((AttributeError, TypeError)):
        uc.id = "9.9.9"  # type: ignore[misc]


# ----------------------------------------------------------------------
# load_use_case
# ----------------------------------------------------------------------


def test_load_use_case_reads_a_sidecar(tmp_path: Path) -> None:
    """The on-disk loader produces the same model as ``from_dict``."""
    path = tmp_path / "UC-1.1.1.json"
    path.write_text(json.dumps(_full_sidecar()), encoding="utf-8")
    uc = load_use_case(path)
    assert uc.id == "1.1.1"
    assert uc.cim_models == ("Performance",)


def test_load_use_case_missing_file_raises(tmp_path: Path) -> None:
    """A missing file surfaces :class:`FileNotFoundError` cleanly."""
    with pytest.raises(FileNotFoundError):
        load_use_case(tmp_path / "does-not-exist.json")


def test_load_use_case_malformed_json_raises(tmp_path: Path) -> None:
    """A non-JSON file surfaces :class:`json.JSONDecodeError`."""
    path = tmp_path / "bad.json"
    path.write_text("not json {", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_use_case(path)


def test_load_use_case_top_level_array_raises(tmp_path: Path) -> None:
    """A JSON array (rather than object) is rejected with a typed message."""
    path = tmp_path / "array.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match=r"expected a JSON object"):
        load_use_case(path)


def test_load_use_case_filename_in_error_message(tmp_path: Path) -> None:
    """Validation failures from a file include the file path in the message.

    A batch caller iterating over thousands of sidecars must be able
    to locate the offending file from the error alone — the bare
    ``from_dict`` message names the field, not the file.
    """
    path = tmp_path / "UC-bad.json"
    path.write_text(json.dumps({"title": "no id here"}), encoding="utf-8")
    with pytest.raises(ValueError, match=str(path)):
        load_use_case(path)
