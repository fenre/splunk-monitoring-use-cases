#!/usr/bin/env python3
"""tools.build.migrate_to_per_uc — split monolithic use-cases/ into per-UC content/.

This is a one-shot, idempotent migration. It is safe to re-run; the
output tree is overwritten each time. The script never deletes files
from ``use-cases/`` — that is left to a human review step (or the
``cleanup-and-docs`` follow-up todo) so the legacy build can keep
running until ``parse_content.py`` is switched to read from
``content/``.

Pipeline
--------

1. Use the legacy ``build.parse_category_file`` (already battle-tested
   for the v6 dashboard) to load each ``use-cases/cat-NN-*.md`` into
   short-key UC dicts.
2. Convert each short-key UC dict into a canonical, schema-compliant
   JSON object (see ``schemas/uc.schema.json``). The conversion
   preserves the existing sidecar JSONs at ``use-cases/cat-NN/uc-X.Y.Z.json``
   when they are richer than the markdown (the legacy parser already
   merges sidecar fields into the UC dict before this script sees it,
   but we re-merge here so sidecar wins on every overlap).
3. Render a tiny per-UC ``UC-X.Y.Z.md`` companion containing front
   matter (``id`` + ``title``) plus a readable rendering of the prose
   sections (``description``, ``value``, ``implementation``, SPL block,
   references). Authors edit this file when they want narrative that
   doesn't fit a structured field.
4. Build ``_category.json`` per category with metadata harvested from
   ``use-cases/INDEX.md`` (icon, description, quickTip, quickStart) plus
   each subcategory's "Primary App/TA" preamble line where present.

Run with no arguments from the repo root:

    python3 tools/build/migrate_to_per_uc.py

The script is intentionally pure stdlib — no external deps so it works
in stripped-down CI environments.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
USE_CASES_DIR = REPO_ROOT / "use-cases"
CONTENT_DIR = REPO_ROOT / "content"
INDEX_MD = USE_CASES_DIR / "INDEX.md"
SCHEMA_REL = "../../schemas/uc.schema.json"

# Categories the v6 build actively skips.
SKIP_FILES = {"cat-00-preamble.md", "cat-10-sse-import.md"}


# ---------------------------------------------------------------------------
# Legacy module loader (re-uses the v6 parser so behaviour stays identical)
# ---------------------------------------------------------------------------

_LEGACY = None


def _legacy_module():
    global _LEGACY
    if _LEGACY is not None:
        return _LEGACY
    legacy_path = REPO_ROOT / "build.py"
    spec = importlib.util.spec_from_file_location("_legacy_build", legacy_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load legacy build.py from {legacy_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_legacy_build"] = module
    spec.loader.exec_module(module)
    _LEGACY = module
    return module


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------


def _category_slug(filename: str) -> str:
    """``cat-01-server-compute.md`` → ``cat-01-server-compute``."""
    return filename.removesuffix(".md")


def _short_slug(filename: str) -> str:
    """``cat-01-server-compute.md`` → ``cat-01``."""
    m = re.match(r"^(cat-\d+)", filename)
    return m.group(1) if m else filename.removesuffix(".md")


# ---------------------------------------------------------------------------
# Subcategory preamble extraction (Primary App/TA + Data Sources)
# ---------------------------------------------------------------------------


_SUBCAT_HEADING_RE = re.compile(r"^#{2,3}\s+(\d+\.\d+)\s+(.+)$")
_UC_HEADING_RE = re.compile(r"^#{3,4}\s+UC-\d+\.\d+\.\d+\s*[·•]")
_PREAMBLE_FIELD_RE = re.compile(r"^\*\*([^:]+):\*\*\s*(.+)$")


def _extract_subcategory_preambles(md_text: str) -> dict[str, dict[str, str]]:
    """Pull ``**Primary App/TA:**`` / ``**Data Sources:**`` lines that sit
    *between* a subcategory heading and the first UC inside it.

    Returns ``{"22.1": {"primaryAppTa": "...", "dataSources": "..."}}``.
    """
    result: dict[str, dict[str, str]] = {}
    current: Optional[str] = None
    in_preamble = False
    for raw in md_text.splitlines():
        line = raw.strip()
        m_sub = _SUBCAT_HEADING_RE.match(line)
        if m_sub:
            current = m_sub.group(1)
            result[current] = {"name": m_sub.group(2).strip()}
            in_preamble = True
            continue
        if current and _UC_HEADING_RE.match(line):
            in_preamble = False
            continue
        if not in_preamble or not current:
            continue
        m_field = _PREAMBLE_FIELD_RE.match(line)
        if not m_field:
            continue
        key = m_field.group(1).strip().lower()
        value = m_field.group(2).strip()
        if key in ("primary app/ta", "primary app / ta", "primary app"):
            result[current]["primaryAppTa"] = value
        elif key in ("data sources", "data source"):
            result[current]["dataSources"] = value
    return result


# ---------------------------------------------------------------------------
# INDEX.md harvest (icons, descriptions, quick-start picks)
# ---------------------------------------------------------------------------


def _parse_index_metadata() -> tuple[
    dict[str, dict[str, Any]], dict[str, list[dict[str, str]]]
]:
    legacy = _legacy_module()
    legacy.UC_DIR = str(USE_CASES_DIR)  # ensure we point at the canonical dir
    return legacy.parse_index_metadata()


# ---------------------------------------------------------------------------
# Sidecar loader (per-UC JSONs already living under use-cases/cat-NN/)
# ---------------------------------------------------------------------------


def _load_sidecar(cat_id: int, uc_id: str) -> Optional[dict[str, Any]]:
    sidecar_path = USE_CASES_DIR / f"cat-{cat_id:02d}" / f"uc-{uc_id}.json"
    if not sidecar_path.exists():
        return None
    try:
        with sidecar_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  WARNING: could not parse sidecar {sidecar_path}: {exc}")
        return None
    return data if isinstance(data, dict) else None


# ---------------------------------------------------------------------------
# Short-key (legacy) → canonical schema-compliant conversion
# ---------------------------------------------------------------------------


# Map of canonical schema enum strings used as targets for normalisation.
_PILLAR_CANONICAL = {
    "security": "Security",
    "observability": "Observability",
    "platform": "Platform",
    "it operations": "IT Operations",
    "both": "Security",  # legacy tri-state — pick Security as the dominant axis
}


_REFERENCE_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")


def _split_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        return []
    parts = re.split(r"[,;\n]+", value)
    return [p.strip() for p in parts if p.strip()]


def _coerce_references(legacy_value: Any) -> list[dict[str, str]]:
    """Turn ``"[Title](https://...), [Other](https://...)"`` into ``[{title, url}]``."""
    if isinstance(legacy_value, list):
        out: list[dict[str, str]] = []
        for item in legacy_value:
            if isinstance(item, dict) and item.get("url"):
                ref = {"url": str(item["url"]).strip()}
                if item.get("title"):
                    ref["title"] = str(item["title"]).strip()
                out.append(ref)
            elif isinstance(item, str):
                m = _REFERENCE_LINK_RE.match(item.strip())
                if m:
                    out.append({"title": m.group(1), "url": m.group(2)})
                elif item.startswith("http"):
                    out.append({"url": item.strip()})
        return out
    if not isinstance(legacy_value, str):
        return []
    items: list[dict[str, str]] = []
    for match in _REFERENCE_LINK_RE.finditer(legacy_value):
        items.append({"title": match.group(1).strip(), "url": match.group(2).strip()})
    if items:
        return items
    # Fallback: split commas of bare URLs.
    for chunk in _split_string_list(legacy_value):
        if chunk.startswith("http"):
            items.append({"url": chunk})
    return items


def _coerce_premium_apps(legacy_value: Any) -> list[Any]:
    """Premium Apps in legacy is free-form text; canonical is array of strings/objects.

    Drops literal placeholders such as ``"None"``, ``"None (DSDL is free)"``,
    ``"N/A"``, and the empty string — these crept in when curators wrote
    "no premium app required" in the markdown. Preserved entries are
    normalised to either a canonical enum string or an object that keeps
    the source spelling and any trailing parenthetical qualifier.
    """
    if isinstance(legacy_value, list):
        return [item for item in legacy_value if item]
    if not isinstance(legacy_value, str):
        return []
    raw_items = _split_string_list(legacy_value)
    out: list[Any] = []
    canonical_names = {
        "splunk enterprise security": "Splunk Enterprise Security",
        "splunk es": "Splunk Enterprise Security",
        "es": "Splunk Enterprise Security",
        "splunk itsi": "Splunk ITSI",
        "splunk it service intelligence": "Splunk ITSI",
        "itsi": "Splunk ITSI",
        "splunk soar": "Splunk SOAR",
        "soar": "Splunk SOAR",
        "splunk user behavior analytics": "Splunk User Behavior Analytics",
        "uba": "Splunk User Behavior Analytics",
        "splunk app for pci compliance": "Splunk App for PCI Compliance",
        "splunk edge hub": "Splunk Edge Hub",
        "splunk ot security add-on": "Splunk OT Security Add-on",
        "splunk ot intelligence": "Splunk OT Intelligence",
        "splunk app for fraud analytics": "Splunk App for Fraud Analytics",
        "splunk airport ground operations app": "Splunk Airport Ground Operations App",
    }
    for raw in raw_items:
        if _is_premium_placeholder(raw):
            continue
        m = re.match(r"^([^()]+)(?:\(([^)]+)\))?$", raw)
        if not m:
            out.append(raw)
            continue
        head = m.group(1).strip().rstrip(",.")
        if _is_premium_placeholder(head):
            continue
        note = (m.group(2) or "").strip()
        canonical = canonical_names.get(head.lower())
        if canonical and note:
            out.append({"name": canonical, "displayName": head, "note": note})
        elif canonical:
            out.append(canonical)
        else:
            out.append(raw)
    return out


_PREMIUM_PLACEHOLDER_RE = re.compile(r"^(none|n/a|na|—|-)\b", re.IGNORECASE)


def _is_premium_placeholder(value: str) -> bool:
    if not value:
        return True
    text = value.strip().lower()
    if not text:
        return True
    return bool(_PREMIUM_PLACEHOLDER_RE.match(text))


def _legacy_uc_to_canonical(
    uc: dict[str, Any],
    cat_id: int,
    sub_id: str | None = None,
) -> dict[str, Any]:
    """Convert a parsed short-key UC into a canonical schema-compliant dict.

    The function is deliberately conservative — it only emits keys that
    have a non-empty value, so JSON diffs stay readable.

    ``sub_id`` is the subcategory bucket the legacy parser placed this UC
    under (e.g. ``"4.5"`` for UC-4.4.32). When the bucket disagrees with
    the UC id's natural prefix we record it explicitly via
    ``subcategory`` so the content-tree loader can faithfully recreate
    the legacy filing without having to re-parse markdown placement.
    """
    canonical: dict[str, Any] = {
        "$schema": SCHEMA_REL,
        "id": uc.get("i", ""),
        "title": (uc.get("n") or "").strip(),
    }

    natural_sub = ".".join(str(canonical["id"]).split(".")[:2])
    if sub_id and sub_id != natural_sub:
        canonical["subcategory"] = sub_id

    # Severity / difficulty (already lowercased + canonical by parse_category_file)
    if uc.get("c"):
        canonical["criticality"] = uc["c"]
    if uc.get("f"):
        canonical["difficulty"] = uc["f"]

    # Monitoring type (legacy short key: mtype, list of strings)
    if uc.get("mtype"):
        canonical["monitoringType"] = list(uc["mtype"])

    # Splunk pillar (legacy stores lowercase; schema requires capitalised enum)
    if uc.get("pillar"):
        canonical["splunkPillar"] = _PILLAR_CANONICAL.get(
            str(uc["pillar"]).lower(), str(uc["pillar"]).title()
        )

    if uc.get("ind"):
        canonical["industry"] = uc["ind"]

    # Compliance: legacy doesn't materialise this from markdown (only the
    # sidecar ever has it). We provide a synthetic entry per regulation
    # listed in `regs` so the schema-required field is populated when the
    # sidecar is sparse. Sidecar `compliance` always wins downstream.
    regs = uc.get("regs") or []
    if regs:
        canonical["compliance"] = [
            {
                "regulation": str(reg),
                "version": "unknown",
                "clause": "unknown",
                "mode": "satisfies",
                "assurance": "contributing",
                "assurance_rationale": (
                    "Auto-generated from legacy markdown 'Regulations' line during "
                    f"the per-UC migration. Requires SME review to fill in version, "
                    f"clause, mode, and assurance for {reg}."
                ),
                "provenance": "maintainer",
            }
            for reg in regs
        ]

    # Implementation / value / description / visualization
    if uc.get("v"):
        canonical["value"] = uc["v"]
    if uc.get("m"):
        canonical["implementation"] = uc["m"]
    if uc.get("md"):
        canonical["detailedImplementation"] = uc["md"]
    if uc.get("script"):
        canonical["scriptExample"] = uc["script"]
    if uc.get("z"):
        canonical["visualization"] = uc["z"]

    # Apps / data sources / SPL
    if uc.get("t"):
        canonical["app"] = uc["t"]
    if uc.get("d"):
        canonical["dataSources"] = uc["d"]
    if uc.get("q"):
        canonical["spl"] = uc["q"]
    if uc.get("qs"):
        canonical["cimSpl"] = uc["qs"]
    if uc.get("a"):
        canonical["cimModels"] = list(uc["a"])
    if uc.get("schema"):
        canonical["schema"] = uc["schema"]
    if uc.get("dma"):
        canonical["dataModelAcceleration"] = uc["dma"]

    # Premium apps
    premium = _coerce_premium_apps(uc.get("premium"))
    if premium:
        canonical["premiumApps"] = premium

    # References
    refs = _coerce_references(uc.get("refs"))
    if refs:
        canonical["references"] = refs

    # Misc detection metadata
    if uc.get("kfp"):
        canonical["knownFalsePositives"] = uc["kfp"]
    if uc.get("mitre"):
        canonical["mitreAttack"] = list(uc["mitre"])
    if uc.get("dtype"):
        canonical["detectionType"] = uc["dtype"]
    if uc.get("sdomain"):
        canonical["securityDomain"] = uc["sdomain"]
    if uc.get("reqf"):
        canonical["requiredFields"] = _split_string_list(uc["reqf"])

    # Equipment tagging
    if uc.get("e"):
        canonical["equipment"] = list(uc["e"])
    if uc.get("em"):
        canonical["equipmentModels"] = list(uc["em"])

    # Free-form vertical metadata (Hardware: / Telco Use Case:). These
    # were parsed from markdown by the v6 build but never made it into
    # any structured schema field; we now round-trip them so the
    # content-tree loader can re-emit them byte-identically.
    if uc.get("hw"):
        canonical["hardware"] = uc["hw"]
    if uc.get("tuc"):
        canonical["telcoUseCase"] = uc["tuc"]

    # Status / lifecycle
    if uc.get("status"):
        canonical["status"] = uc["status"]
    if uc.get("reviewed"):
        canonical["lastReviewed"] = uc["reviewed"]
    if uc.get("sver"):
        canonical["splunkVersions"] = _split_string_list(uc["sver"])
    if uc.get("rby"):
        canonical["reviewer"] = uc["rby"]

    # Description: fall back to value when the legacy file has no
    # dedicated description. Schemas require >=20 chars so we prefer to
    # leave the field absent if the value text is too short.
    if not canonical.get("description"):
        candidate = uc.get("v") or ""
        if len(candidate) >= 20:
            canonical["description"] = candidate

    return canonical


def _merge_canonical(
    base: dict[str, Any], sidecar: Optional[dict[str, Any]]
) -> dict[str, Any]:
    """Right-biased shallow merge with array de-duplication.

    The sidecar (when present) wins for any field it specifies. For
    arrays we keep the sidecar version verbatim so curators stay in
    control. ``$schema`` is always pinned to the canonical relative
    path so the file is portable inside the new tree.
    """
    if not sidecar:
        out = dict(base)
        out["$schema"] = SCHEMA_REL
        return out
    out = dict(base)
    for key, value in sidecar.items():
        if key in ("$schema",):
            continue
        if value in (None, "", []):
            continue
        out[key] = value
    out["$schema"] = SCHEMA_REL
    return out


# ---------------------------------------------------------------------------
# Stable JSON ordering (so re-runs produce byte-identical files)
# ---------------------------------------------------------------------------


_KEY_ORDER = [
    "$schema",
    "id",
    "subcategory",
    "title",
    "criticality",
    "difficulty",
    "monitoringType",
    "splunkPillar",
    "industry",
    "owner",
    "controlFamily",
    "exclusions",
    "evidence",
    "evidenceSigning",
    "compliance",
    "controlTest",
    "dataSources",
    "app",
    "premiumApps",
    "spl",
    "cimSpl",
    "cimModels",
    "schema",
    "dataModelAcceleration",
    "description",
    "value",
    "implementation",
    "detailedImplementation",
    "scriptExample",
    "visualization",
    "references",
    "knownFalsePositives",
    "mitreAttack",
    "detectionType",
    "securityDomain",
    "requiredFields",
    "equipment",
    "equipmentModels",
    "hardware",
    "telcoUseCase",
    "status",
    "lastReviewed",
    "splunkVersions",
    "reviewer",
]


def _ordered(obj: dict[str, Any]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in _KEY_ORDER:
        if key in obj:
            ordered[key] = obj[key]
    for key in sorted(obj):
        if key not in ordered:
            ordered[key] = obj[key]
    return ordered


# ---------------------------------------------------------------------------
# Markdown companion renderer
# ---------------------------------------------------------------------------


def _render_uc_markdown(canonical: dict[str, Any]) -> str:
    """Emit a small, readable .md companion next to UC-X.Y.Z.json.

    Front matter pins the canonical id + title so editors that don't
    open the JSON can still navigate the tree. Sections only render
    when their underlying field is present.
    """
    lines: list[str] = []
    fm_title = canonical.get("title", "").replace('"', '\\"')
    lines.append("---")
    lines.append(f'id: "{canonical.get("id", "")}"')
    lines.append(f'title: "{fm_title}"')
    if canonical.get("status"):
        lines.append(f'status: "{canonical["status"]}"')
    if canonical.get("criticality"):
        lines.append(f'criticality: "{canonical["criticality"]}"')
    if canonical.get("splunkPillar"):
        lines.append(f'splunkPillar: "{canonical["splunkPillar"]}"')
    lines.append("---")
    lines.append("")
    lines.append(f'# UC-{canonical.get("id", "?")} · {canonical.get("title", "")}')
    lines.append("")

    if canonical.get("description"):
        lines.append("## Description")
        lines.append("")
        lines.append(canonical["description"].rstrip())
        lines.append("")
    if canonical.get("value"):
        lines.append("## Value")
        lines.append("")
        lines.append(canonical["value"].rstrip())
        lines.append("")
    if canonical.get("implementation"):
        lines.append("## Implementation")
        lines.append("")
        lines.append(canonical["implementation"].rstrip())
        lines.append("")
    if canonical.get("detailedImplementation"):
        lines.append("## Detailed Implementation")
        lines.append("")
        lines.append(canonical["detailedImplementation"].rstrip())
        lines.append("")
    if canonical.get("spl"):
        lines.append("## SPL")
        lines.append("")
        lines.append("```spl")
        lines.append(canonical["spl"].rstrip())
        lines.append("```")
        lines.append("")
    if canonical.get("cimSpl"):
        lines.append("## CIM SPL")
        lines.append("")
        lines.append("```spl")
        lines.append(canonical["cimSpl"].rstrip())
        lines.append("```")
        lines.append("")
    if canonical.get("scriptExample"):
        lines.append("## Script Example")
        lines.append("")
        lines.append("```")
        lines.append(canonical["scriptExample"].rstrip())
        lines.append("```")
        lines.append("")
    if canonical.get("visualization"):
        lines.append("## Visualization")
        lines.append("")
        lines.append(canonical["visualization"].rstrip())
        lines.append("")
    if canonical.get("knownFalsePositives"):
        lines.append("## Known False Positives")
        lines.append("")
        lines.append(canonical["knownFalsePositives"].rstrip())
        lines.append("")
    if canonical.get("references"):
        lines.append("## References")
        lines.append("")
        for ref in canonical["references"]:
            if not isinstance(ref, dict):
                continue
            url = ref.get("url", "")
            title = ref.get("title") or url
            if url:
                lines.append(f"- [{title}]({url})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _write_text(path: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def _category_md_files() -> list[Path]:
    files = sorted(USE_CASES_DIR.glob("cat-[0-9]*.md"))
    return [f for f in files if f.name not in SKIP_FILES]


def _build_quickstart(starters: list[dict[str, str]] | None) -> list[dict[str, str]]:
    if not starters:
        return []
    out: list[dict[str, str]] = []
    for entry in starters:
        item = {
            "id": entry.get("i", ""),
            "title": entry.get("n", ""),
        }
        if entry.get("c"):
            item["criticality"] = entry["c"]
        if entry.get("sc"):
            item["subcategory"] = entry["sc"]
        out.append(item)
    return out


def _build_subcategories(
    cat_record: dict[str, Any], preambles: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    """Emit subcategories preserving the legacy duplicate-id markdown buckets.

    A few legacy category files (notably `cat-22-regulatory-compliance.md`) have
    two `### N.M` sections sharing the same numerical id (e.g. `### 22.3 DORA`
    and `### 22.3 — DORA (extended clauses)`). The legacy parser keeps both as
    distinct sub records; the content tree must do the same. We assign a stable
    `bucketKey` of the form `"<id>#<n>"` (1-indexed) to every occurrence after
    the first so the loader can file UCs into the correct bucket. The first
    occurrence intentionally has *no* `bucketKey` so the field stays absent for
    every category that doesn't need disambiguation.
    """
    subs: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for sub in cat_record.get("s", []):
        sub_id = sub.get("i")
        if not sub_id:
            continue
        occurrence = seen.get(sub_id, 0)
        seen[sub_id] = occurrence + 1
        item: dict[str, Any] = {
            "id": sub_id,
            "name": sub.get("n", ""),
            "useCaseCount": len(sub.get("u", [])),
        }
        if occurrence > 0:
            item["bucketKey"] = f"{sub_id}#{occurrence}"
        meta = preambles.get(sub_id) or {}
        if meta.get("primaryAppTa"):
            item["primaryAppTa"] = meta["primaryAppTa"]
        if meta.get("dataSources"):
            item["dataSources"] = meta["dataSources"]
        subs.append(item)
    return subs


def _category_payload(
    cat_record: dict[str, Any],
    cat_meta_entry: dict[str, Any],
    starters: list[dict[str, str]] | None,
    preambles: dict[str, dict[str, str]],
    src_filename: str,
    slug: str,
    short_slug: str,
) -> dict[str, Any]:
    cat_id = cat_record.get("i")
    payload: dict[str, Any] = {
        "$schema": "../../schemas/category.schema.json",
        "id": cat_id,
        "name": cat_record.get("n", ""),
        "slug": slug,
        "shortSlug": short_slug,
        "src": src_filename,
    }
    if cat_meta_entry.get("icon"):
        payload["icon"] = cat_meta_entry["icon"]
    if cat_meta_entry.get("desc"):
        payload["description"] = cat_meta_entry["desc"]
    if cat_meta_entry.get("quick"):
        payload["quickTip"] = cat_meta_entry["quick"]
    qs = _build_quickstart(starters)
    if qs:
        payload["quickStart"] = qs
    payload["subcategories"] = _build_subcategories(cat_record, preambles)
    payload["useCaseCount"] = sum(
        len(sub.get("u", [])) for sub in cat_record.get("s", [])
    )
    return payload


def _emit_category(
    cat_record: dict[str, Any],
    cat_meta_entry: dict[str, Any],
    starters: list[dict[str, str]] | None,
    md_text: str,
    src_filename: str,
) -> tuple[int, int]:
    """Emit content/<slug>/_category.json + every UC under it.

    Returns ``(uc_count, sidecar_hits)``.
    """
    cat_id = cat_record.get("i")
    if not cat_id:
        return (0, 0)
    slug = _category_slug(src_filename)
    short_slug = _short_slug(src_filename)
    out_dir = CONTENT_DIR / slug
    _ensure_dir(out_dir)

    preambles = _extract_subcategory_preambles(md_text)

    # _category.json
    cat_payload = _category_payload(
        cat_record,
        cat_meta_entry,
        starters,
        preambles,
        src_filename,
        slug,
        short_slug,
    )
    _write_json(out_dir / "_category.json", cat_payload)

    uc_count = 0
    sidecar_hits = 0
    sub_occurrence: dict[str, int] = {}
    for sub in cat_record.get("s", []):
        sub_id = sub.get("i") or ""
        if sub_id:
            occurrence = sub_occurrence.get(sub_id, 0)
            sub_occurrence[sub_id] = occurrence + 1
            bucket_key = sub_id if occurrence == 0 else f"{sub_id}#{occurrence}"
        else:
            bucket_key = ""
        for uc in sub.get("u", []):
            uc_id = uc.get("i")
            if not uc_id:
                continue
            base = _legacy_uc_to_canonical(uc, cat_id, sub_id=bucket_key)
            sidecar = _load_sidecar(cat_id, uc_id)
            if sidecar:
                sidecar_hits += 1
            merged = _merge_canonical(base, sidecar)
            ordered = _ordered(merged)
            _write_json(out_dir / f"UC-{uc_id}.json", ordered)
            _write_text(out_dir / f"UC-{uc_id}.md", _render_uc_markdown(ordered))
            uc_count += 1
    return (uc_count, sidecar_hits)


def _emit_index() -> None:
    """Copy use-cases/INDEX.md → content/INDEX.md verbatim."""
    if not INDEX_MD.exists():
        return
    target = CONTENT_DIR / "INDEX.md"
    target.write_text(INDEX_MD.read_text(encoding="utf-8"), encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    files = _category_md_files()
    if not files:
        print(f"No cat-NN-*.md files found under {USE_CASES_DIR}", file=sys.stderr)
        return 1
    legacy = _legacy_module()
    legacy.UC_DIR = str(USE_CASES_DIR)

    print(f"Migrating {len(files)} category files into {CONTENT_DIR.relative_to(REPO_ROOT)}/")
    cat_meta, cat_starters = _parse_index_metadata()

    total_ucs = 0
    total_sidecars = 0
    for filepath in files:
        md_text = filepath.read_text(encoding="utf-8")
        record = legacy.parse_category_file(str(filepath))
        if "i" not in record:
            print(f"  SKIP {filepath.name} (no category heading)")
            continue
        cat_id = record["i"]
        cat_meta_entry = cat_meta.get(str(cat_id), {})
        starters = cat_starters.get(str(cat_id))
        uc_count, sidecar_hits = _emit_category(
            record,
            cat_meta_entry,
            starters,
            md_text,
            filepath.name,
        )
        print(
            f"  cat-{cat_id:02d}  {uc_count:>4} UCs ({sidecar_hits:>4} sidecars merged)  → "
            f"{_category_slug(filepath.name)}/"
        )
        total_ucs += uc_count
        total_sidecars += sidecar_hits

    _emit_index()
    print(
        f"Done. {total_ucs} UCs written, {total_sidecars} sidecars merged. "
        f"Tree at {CONTENT_DIR.relative_to(REPO_ROOT)}/"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
