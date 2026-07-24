"""Taxonomy row model for cat-21 industry UC expansion."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaxonomyEntry:
    subcategory: str  # e.g. "21.1"
    title: str
    industry: str
    index: str
    sourcetype: str
    spl_filter: str
    criticality: str
    difficulty: str
    monitoring_type: tuple[str, ...]
    splunk_pillar: str
    description: str
    value: str
    implementation: str
    visualization: str
    app: str
    equipment: tuple[str, ...]
    equipment_models: tuple[str, ...] = ()
    mitre_attack: tuple[str, ...] = ()
    cim_models: tuple[str, ...] = ("N/A",)
    cim_spl: str = ""
    known_false_positives: str = ""
    wave: str = "walk"
    prerequisite_uc: str | None = None
    regulation: str | None = None
    regulation_clause: str | None = None
    cost_tier: str = "medium"
    splunkbase_id: int = 5180
    splunkbase_name: str = "Splunk OT Intelligence"
    vendor_ref_title: str = "Splunk Lantern — Industry use cases"
    vendor_ref_url: str = "https://lantern.splunk.com/"
    security_domain: str = "industry"
    table_fields: str = "_time host source severity message"
    source_tag: str = ""  # manifest, matrix, fsi


def infer_index(sourcetype: str, default_index: str) -> str:
    from .subcategory_meta import SOURCETYPE_INDEX

    for prefix, idx in SOURCETYPE_INDEX.items():
        if sourcetype.startswith(prefix):
            return idx
    return default_index


def build_entry(
    *,
    subcategory: str,
    title: str,
    sourcetype: str | None = None,
    spl_filter: str = "*",
    criticality: str = "high",
    difficulty: str = "intermediate",
    monitoring_type: tuple[str, ...] = ("Operations", "Availability"),
    splunk_pillar: str = "Observability",
    description: str = "",
    value: str = "",
    mitre: tuple[str, ...] = (),
    regulation: str | None = None,
    regulation_clause: str | None = None,
    source_tag: str = "manifest",
    table_fields: str | None = None,
) -> TaxonomyEntry:
    from .subcategory_meta import SUBCATEGORY_META

    meta = SUBCATEGORY_META[subcategory]
    st = sourcetype or str(meta["default_sourcetype"])
    idx = infer_index(st, str(meta["index"]))
    industry = str(meta["industry"])
    app = str(meta["app"])
    equipment = tuple(meta["equipment"])  # type: ignore[arg-type]
    prereq = meta.get("prerequisite")

    if not description:
        description = (
            f"Monitors {title.lower()} using `{st}` telemetry in `index={idx}` "
            f"to surface operational risk before it impacts {industry.lower()} service delivery."
        )
    if not value:
        value = (
            f"Operations and risk leaders in {industry} use this signal to prioritize crews, "
            f"budget, and customer or regulator communications while conditions are still controllable."
        )

    impl = (
        f"Ingest `{st}` events via HEC or Edge Hub into `index={idx}`. "
        f"Normalize field extractions in props/transforms for the {industry} feed. "
        f"Save as a scheduled search or real-time alert; tune thresholds using a 14-day baseline."
    )

    if table_fields is None:
        from .table_fields import TABLE_FIELDS_FOR

        table_fields = TABLE_FIELDS_FOR.get(st, "_time host source severity message")

    reg_note = ""
    if regulation:
        reg_note = f" Aligns with {regulation} clause {regulation_clause or 'operational evidence'} requirements."

    return TaxonomyEntry(
        subcategory=subcategory,
        title=title,
        industry=industry,
        index=idx,
        sourcetype=st,
        spl_filter=spl_filter,
        criticality=criticality,
        difficulty=difficulty,
        monitoring_type=monitoring_type,
        splunk_pillar=splunk_pillar,
        description=description + reg_note,
        value=value,
        implementation=impl,
        visualization="Timechart by host/asset, single-value KPI, table of top offenders.",
        app=app,
        equipment=equipment,
        mitre_attack=mitre or ("T0809",) if idx in ("scada", "mfg", "oilgas", "water") else ("T1078",),
        wave=str(meta["wave"]),
        prerequisite_uc=str(prereq) if prereq else None,
        regulation=regulation,
        regulation_clause=regulation_clause,
        source_tag=source_tag,
        table_fields=table_fields,
        known_false_positives=(
            "Planned maintenance windows, vendor pack updates, DR exercises, "
            "and seasonal demand patterns excluded via asset/schedule lookup."
        ),
    )


def crawl_uc_ids() -> dict[str, str]:
    """Return subcategory -> crawl/prerequisite UC id (bare, no UC- prefix)."""
    from .subcategory_meta import SUBCATEGORY_META

    out: dict[str, str] = {}
    for sub, meta in SUBCATEGORY_META.items():
        prereq = meta.get("prerequisite")
        if prereq:
            out[sub] = str(prereq)
    return out
