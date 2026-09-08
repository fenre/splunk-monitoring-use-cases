"""Tests for ``generate-equipment-app-map`` (equipment picker Phase 5)."""

from __future__ import annotations

from splunk_uc.audits import equipment_app_map as audit
from splunk_uc.generators import equipment_app_map as generator


def test_committed_map_matches_generator() -> None:
    generated = generator.generate_map()
    assert len(generated["entries"]) >= 120
    assert generator.main(["--check"]) == 0


def test_generator_output_passes_audit() -> None:
    generated = generator.generate_map()
    errors = audit._validate_schema(generated)
    assert errors == []
    errors.extend(
        audit.audit_map(
            generated,
            catalog=audit._load_catalog(),
            equipment_kinds=audit._load_equipment_slugs(),
            dsa_ids=audit._load_dsa_source_ids(),
            corroboration=audit.build_corroboration_index(),
        )
    )
    assert errors == []
