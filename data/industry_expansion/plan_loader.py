"""Load TaxonomyEntry rows from industry_manifest.md (526 named candidates)."""

from __future__ import annotations

import re
from pathlib import Path

from .taxonomy import TaxonomyEntry, build_entry

MANIFEST = Path(__file__).resolve().parent / "industry_manifest.md"

SECTION_RE = re.compile(
    r"^### (21\.\d+|Cross-vertical foundations) .+? — (\d+) net-new",
    re.MULTILINE,
)
ITEM_RE = re.compile(
    r"^(\d+)\.\s+(.+?)(?:\s+\(`([^`]+)`\))?(?:\s+\[([^\]]+)\])?\s*$",
    re.MULTILINE,
)

CROSS_VERTICAL_MAP: dict[str, str] = {
    "manufacturing oee": "21.2",
    "healthcare hl7": "21.3",
    "retail failed pos": "21.6",
    "vertical index ingest": "21.1",
    "hec token rate": "21.1",
    "edge hub store": "21.1",
    "mqtt broker": "21.14",
    "multi-vertical soar": "21.12",
    "itsi vertical service": "21.14",
    "vertical executive scorecard": "21.1",
    "cross-vertical mitre": "21.1",
    "vertical ml anomaly": "21.1",
    "multi-region vertical": "21.12",
    "vertical role-based": "21.12",
    "industry-specific app": "21.2",
}

SKIP_TAGS = {"c", "c partial"}


def _parse_subcategory(header: str) -> str | None:
    if header.startswith("21."):
        return header
    return None


def _cross_vertical_subcat(title: str) -> str:
    tl = title.lower()
    for key, sub in CROSS_VERTICAL_MAP.items():
        if key in tl:
            return sub
    return "21.1"


def _should_skip(tag: str | None) -> bool:
    if not tag:
        return False
    base = tag.lower().split()[0]
    if base in SKIP_TAGS:
        return True
    if tag.lower().startswith("c "):
        return True
    return False


def _infer_sourcetype(title: str, explicit: str | None, subcategory: str) -> str | None:
    if explicit:
        return explicit
    tl = title.lower()
    # Infer common patterns from title keywords
    hints: list[tuple[str, str]] = [
        ("scada hmi", "scada:hmi"),
        ("scada event", "scada:event"),
        ("ami ", "smartgrid:meter"),
        ("derms", "derms:event"),
        ("oms ", "oms:event"),
        ("hl7 orm", "hl7:orm"),
        ("hl7 oru", "hl7:oru"),
        ("hl7 msh", "hl7:msh"),
        ("hl7 adt", "hl7:adt"),
        ("hl7 message", "hl7:message"),
        ("fhir", "fhir:resource"),
        ("epic audit", "epic:audit"),
        ("cerner audit", "cerner:audit"),
        ("iomt", "mediot:device"),
        ("sap idoc", "sap:idoc"),
        ("sap cdr", "sap:cdr"),
        ("mes job", "mes:job"),
        ("rfid", "rfid:scan"),
        ("barcode", "barcode:scan"),
        ("tms ", "tms:event"),
        ("fleet", "fleet:telematics"),
        ("pipeline", "oil:pipeline:scada"),
        ("refinery", "oil:refinery:dcs"),
        ("wellhead", "oil:wellhead"),
        ("drilling", "oil:drilling:event"),
        ("mining", "mining:scada"),
        ("pos ", "retail:pos"),
        ("e-commerce", "retail:ecommerce"),
        ("loyalty", "retail:loyalty"),
        ("bhs", "airport:bhs"),
        ("atc ", "atc:event"),
        ("passenger flow", "airport:passenger"),
        ("5g nrf", "telco:5g:nrf"),
        ("5g smf", "telco:5g:smf"),
        ("5g upf", "telco:5g:upf"),
        ("5g amf", "telco:5g:amf"),
        ("5g ausf", "telco:5g:ausf"),
        ("cdr", "telco:cdr"),
        ("ipdr", "telco:ipdr"),
        ("edr", "telco:edr"),
        ("water meter", "water:meter"),
        ("treatment", "water:treatment"),
        ("insurance claim", "insurance:claim"),
        ("underwriting", "insurance:underwriting"),
        ("policy admin", "insurance:policy"),
    ]
    for key, st in hints:
        if key in tl:
            return st
    return None


def _spl_filter_for(title: str, sourcetype: str) -> str:
    tl = title.lower()
    if "latency" in tl or "delay" in tl:
        return "latency_ms>500 OR delay_sec>60"
    if "failure" in tl or "error" in tl:
        return "status=failure OR result=failure OR error=*"
    if "anomaly" in tl or "spike" in tl or "excursion" in tl:
        return "*"
    if "audit" in tl or "privileged" in tl:
        return "action=* OR event_type=audit"
    if "fraud" in tl:
        return "fraud_score>70 OR risk_score>80"
    if "compliance" in tl or "nerc cip" in tl:
        return "*"
    if "offline" in tl or "gap" in tl or "loss" in tl:
        return "status=offline OR gap_sec>300"
    return "*"


def load_manifest_entries(path: Path | None = None) -> list[TaxonomyEntry]:
    text = (path or MANIFEST).read_text(encoding="utf-8")
    entries: list[TaxonomyEntry] = []
    current_sub: str | None = None

    for line in text.splitlines():
        sec = SECTION_RE.match(line)
        if sec:
            current_sub = _parse_subcategory(sec.group(1))
            if sec.group(1).startswith("Cross-vertical"):
                current_sub = "cross"
            continue

        m = ITEM_RE.match(line.strip())
        if not m or current_sub is None:
            continue

        raw_title = m.group(2).strip()
        # Strip trailing source annotations like [Lantern], [guide SPL]
        title = re.sub(r"\s+\[[^\]]+\]\s*$", "", raw_title).strip()
        title = re.sub(r"\s+\[E[^\]]*\]", "", title, flags=re.I).strip()

        explicit_st = m.group(3)
        tag = m.group(4)

        if _should_skip(tag):
            continue

        # Skip FSI residual placeholder — handled by fsi_residual module
        if "fsi residual pack" in title.lower():
            continue

        if current_sub == "cross":
            subcategory = _cross_vertical_subcat(title)
        else:
            subcategory = current_sub

        sourcetype = _infer_sourcetype(title, explicit_st, subcategory)
        spl_filter = _spl_filter_for(title, sourcetype or "")

        monitoring: tuple[str, ...] = ("Operations",)
        if any(k in title.lower() for k in ("fraud", "security", "audit", "cip", "hipaa", "pci")):
            monitoring = ("Security", "Audit")
        elif any(k in title.lower() for k in ("latency", "sla", "performance", "oee")):
            monitoring = ("Performance", "Availability")

        criticality = "high"
        if any(k in title.lower() for k in ("scada", "pipeline", "nerc", "patient", "safety")):
            criticality = "critical"

        regulation = None
        clause = None
        if "nerc cip" in title.lower():
            regulation = "NERC-CIP"
            m_cip = re.search(r"cip-(\d+)", title.lower())
            clause = f"CIP-{m_cip.group(1)}" if m_cip else None
        elif "hipaa" in title.lower():
            regulation = "HIPAA"
        elif "pci" in title.lower():
            regulation = "PCI-DSS"

        entries.append(
            build_entry(
                subcategory=subcategory,
                title=title,
                sourcetype=sourcetype,
                spl_filter=spl_filter,
                criticality=criticality,
                monitoring_type=monitoring,
                regulation=regulation,
                regulation_clause=clause,
                source_tag="manifest",
            )
        )

    return entries
