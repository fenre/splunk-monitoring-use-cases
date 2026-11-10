"""Tests for ``generate-equipment-app-map`` (equipment picker Phase 5)."""

from __future__ import annotations

import json
import types
from collections.abc import Iterator
from pathlib import Path

import pytest

from splunk_uc.audits import equipment_app_map as audit
from splunk_uc.generators import equipment_app_map as generator
from splunk_uc.generators import equipment_tags

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture()
def small_corpus(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Server and network sidecars stand in for the whole catalogue."""
    equipment_tags.clear_tag_cache()
    paths = sorted(REPO.glob("content/cat-01-*/UC-1.1.*.json"))[:40]
    paths += sorted(REPO.glob("content/cat-05-*/UC-5.1.*.json"))[:40]
    corpus = [(path, json.loads(path.read_text(encoding="utf-8"))) for path in paths]
    monkeypatch.setattr(generator, "iter_uc_sidecars", lambda: iter(corpus))
    monkeypatch.setattr(audit, "iter_uc_sidecars", lambda: iter(corpus))
    supported = {slug for slug, _app in generator.build_corroboration_index()}
    assert "linux" in supported
    enrichment = generator._load_enrichment_module()
    narrowed = types.SimpleNamespace(**vars(enrichment))
    narrowed.EQUIPMENT = [eq for eq in enrichment.EQUIPMENT if eq["id"] in supported]
    monkeypatch.setattr(generator, "_load_enrichment_module", lambda: narrowed)
    yield
    equipment_tags.clear_tag_cache()


@pytest.mark.usefixtures("small_corpus")
def test_generator_output_passes_audit() -> None:
    generated = generator.generate_map()
    assert generated["entries"]
    assert "linux" in generated["entries"]
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


@pytest.mark.usefixtures("small_corpus")
def test_check_detects_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "equipment-app-map.json"
    monkeypatch.setattr(generator, "MAP_PATH", out, raising=False)
    monkeypatch.setattr(generator, "OUTPUT_PATH", out, raising=False)
    assert generator.main([]) == 0
    assert generator.main(["--check"]) == 0
    out.write_text("{}\n", encoding="utf-8")
    assert generator.main(["--check"]) == 1
