#!/usr/bin/env python3
"""Per-UC Splunk dashboard scaffold generator (Classic Simple XML + Dashboard Studio).

Emits operator-ready dashboard pairs under ``dist/dashboards/UC-X.Y.Z/`` —
one ``simple.xml`` (Classic Simple XML) and one ``studio.xml`` (Dashboard
Studio JSON wrapped in XML). Every panel queries real ``index=`` /
``sourcetype=`` tokens from the UC sidecar SPL; operators replace
placeholder index/sourcetype values for their environment.

Anti-patterns explicitly avoided (see ``scripts/generate_catalog_dashboard.py``
as the negative example):

- ``| makeresults`` — never used
- ``random()`` — never used
- hardcoded ``coalesce(field, 87.3)`` fallbacks — never used
- ``viz.*`` Dashboard Studio types — always ``splunk.*``

Usage::

    python3 -m splunk_uc generate-dashboards
    python3 -m splunk_uc generate-dashboards --check
    python3 -m splunk_uc generate-dashboards --only UC-1.1.1
    python3 -m splunk_uc audit-dashboards --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any
from xml.sax.saxutils import escape as xml_escape

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_ROOT = REPO_ROOT / "content"
TEMPLATE_DIR = REPO_ROOT / "templates" / "dashboards"
DEFAULT_OUT = REPO_ROOT / "dist" / "dashboards"

_TERMINATING_COMMANDS = frozenset(
    {
        "stats",
        "timechart",
        "chart",
        "tstats",
        "table",
        "top",
        "rare",
        "mstats",
    }
)

_MAKERESULTS_RE = re.compile(r"\|\s*makeresults\b", re.IGNORECASE)
_RANDOM_RE = re.compile(r"\brandom\s*\(", re.IGNORECASE)
_COALESCE_LITERAL_RE = re.compile(
    r"coalesce\s*\([^)]*,\s*(?!0\b)(?!\"0\"|'0')\d+(?:\.\d+)?\s*\)",
    re.IGNORECASE,
)
_INDEX_RE = re.compile(r"\bindex\s*=\s*([^\s|()]+)", re.IGNORECASE)
_SOURCETYPE_RE = re.compile(r"\bsourcetype\s*=\s*([^\s|()]+)", re.IGNORECASE)
_XML_TAG_INNER_RE = re.compile(r"<(label|description)>(.*?)</\1>", re.DOTALL)

@dataclass
class EmitReport:
    """Summary of a generate/audit run."""

    written: int = 0
    checked: int = 0
    drift: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    uc_ids: list[str] = field(default_factory=list)


def load_uc(path: Path) -> dict[str, Any]:
    """Load one UC sidecar JSON file."""
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return payload


def _split_stages(spl: str) -> list[str]:
    """Split SPL into pipe stages (pipe-per-line aware)."""
    stages: list[str] = []
    current: list[str] = []
    for raw_line in spl.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            if current:
                stages.append("\n".join(current))
            current = [stripped]
        else:
            current.append(stripped)
    if current:
        stages.append("\n".join(current))
    return stages


def _stage_command(stage: str) -> str:
    body = stage.strip()
    if body.startswith("|"):
        body = body[1:].strip()
    if not body:
        return ""
    return body.split()[0].lower()


def ensure_pipe_per_line(spl: str) -> str:
    """Normalise SPL so every pipe stage starts its own line."""
    text = spl.strip()
    if not text:
        return ""
    if "\n" in text:
        stages = _split_stages(text)
        if stages:
            return "\n".join(stages)
    # One-liner: split on unquoted pipes.
    parts: list[str] = []
    buf: list[str] = []
    in_quote: str | None = None
    i = 0
    while i < len(text):
        ch = text[i]
        if in_quote:
            buf.append(ch)
            if ch == in_quote and (i == 0 or text[i - 1] != "\\"):
                in_quote = None
            i += 1
            continue
        if ch in "\"'":
            in_quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == "|":
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    if not parts:
        return text
    lines = [parts[0]]
    for part in parts[1:]:
        lines.append(f"| {part.lstrip('|').strip()}")
    return "\n".join(lines)


def _base_spl(uc: dict[str, Any]) -> str:
    for key in ("spl", "cimSpl", "qs"):
        raw = uc.get(key)
        if isinstance(raw, str) and raw.strip():
            return ensure_pipe_per_line(raw.strip())
    return (
        "index=<INDEX_PLACEHOLDER> sourcetype=<SOURCETYPE_PLACEHOLDER>"
    )


def _has_terminating_aggregation(stages: list[str]) -> bool:
    for stage in reversed(stages):
        cmd = _stage_command(stage)
        if cmd in _TERMINATING_COMMANDS:
            return True
        if cmd in {"where", "sort", "fields", "rename", "head", "tail"}:
            continue
        if cmd:
            return False
    return False


def _pipeline_has_timechart(stages: list[str]) -> bool:
    return any(_stage_command(stage) == "timechart" for stage in stages)


def _extract_index_sourcetype(spl: str) -> tuple[str | None, str | None]:
    index_match = _INDEX_RE.search(spl)
    sourcetype_match = _SOURCETYPE_RE.search(spl)
    index = index_match.group(1).strip("\"'`") if index_match else None
    sourcetype = sourcetype_match.group(1).strip("\"'`") if sourcetype_match else None
    return index, sourcetype


def _has_unescaped_ampersand(xml_text: str) -> bool:
    for match in _XML_TAG_INNER_RE.finditer(xml_text):
        inner = match.group(2)
        if re.search(r"&(?!amp;|lt;|gt;|quot;|apos;)", inner):
            return True
    return False


def _is_dashboard_safe_spl(spl: str) -> bool:
    lowered = spl.lower()
    if any(token in lowered for token in ("multisearch", "join ", "[search", "| join")):
        return False
    normalised = ensure_pipe_per_line(spl)
    if not check_pipe_per_line(normalised):
        return False
    return not validate_spl_text(normalised)


def _dashboard_base_spl(uc: dict[str, Any]) -> str:
    """Return SPL suitable for dashboard panels (simple, pipe-per-line safe)."""
    full = _base_spl(uc)
    if _is_dashboard_safe_spl(full):
        return ensure_pipe_per_line(full)
    index, sourcetype = _extract_index_sourcetype(full)
    parts: list[str] = []
    if index:
        parts.append(f"index={index}")
    else:
        parts.append("index=<INDEX_PLACEHOLDER>")
    if sourcetype:
        parts.append(f"sourcetype={sourcetype}")
    else:
        parts.append("sourcetype=<SOURCETYPE_PLACEHOLDER>")
    return " ".join(parts)


def derive_panel_spl(uc: dict[str, Any]) -> tuple[str, str, str]:
    """Return ``(primary, timechart, table)`` SPL triple for dashboard panels."""
    base = _dashboard_base_spl(uc)
    stages = _split_stages(base)

    if _has_terminating_aggregation(stages):
        primary = base
        last_cmd = _stage_command(stages[-1]) if stages else ""
        if last_cmd not in _TERMINATING_COMMANDS:
            primary = f"{base}\n| stats count"
    else:
        primary = f"{base}\n| stats count"

    if _pipeline_has_timechart(stages):
        timechart = base
    else:
        timechart = f"{base}\n| timechart span=1h count"

    last_cmd = _stage_command(stages[-1]) if stages else ""
    if last_cmd == "table":
        table = base
    else:
        table = f"{base}\n| head 100\n| table *"

    return (
        ensure_pipe_per_line(primary),
        ensure_pipe_per_line(timechart),
        ensure_pipe_per_line(table),
    )


def _uc_display_id(uc: dict[str, Any], path: Path | None = None) -> str:
    raw = uc.get("id")
    if isinstance(raw, str) and raw.strip():
        return f"UC-{raw.strip()}"
    if path is not None:
        stem = path.stem
        if stem.startswith("UC-"):
            return stem
    return "UC-unknown"


def _app_id_placeholder(_uc: dict[str, Any]) -> str:
    return "<APP_ID_PLACEHOLDER>"


def _escape_spl_for_xml(spl: str) -> str:
    return xml_escape(spl, entities={"\"": "&quot;"})


def _escape_spl_for_json_string(spl: str) -> str:
    return json.dumps(spl)[1:-1]


def _dashboard_context(uc: dict[str, Any], path: Path | None = None) -> dict[str, str]:
    uc_id = _uc_display_id(uc, path)
    title = str(uc.get("title") or uc_id)
    description = str(
        uc.get("description")
        or uc.get("value")
        or f"Monitoring dashboard scaffold for {uc_id}."
    )
    criticality = str(uc.get("criticality") or "unknown")
    primary, timechart, table = derive_panel_spl(uc)
    return {
        "uc_id": uc_id,
        "title": xml_escape(title),
        "description": xml_escape(description),
        "json_title": json.dumps(title)[1:-1],
        "json_description": json.dumps(description)[1:-1],
        "criticality": xml_escape(criticality),
        "app_id_placeholder": _app_id_placeholder(uc),
        "primary_spl": _escape_spl_for_xml(primary),
        "timechart_spl": _escape_spl_for_xml(timechart),
        "table_spl": _escape_spl_for_xml(table),
        "primary_spl_json": _escape_spl_for_json_string(primary),
        "timechart_spl_json": _escape_spl_for_json_string(timechart),
        "table_spl_json": _escape_spl_for_json_string(table),
    }


def _load_template(name: str) -> Template:
    path = TEMPLATE_DIR / name
    return Template(path.read_text(encoding="utf-8"))


def render_simple_xml(
    uc: dict[str, Any],
    template: Template | None = None,
    *,
    path: Path | None = None,
) -> str:
    """Render Classic Simple XML for one UC."""
    tmpl = template or _load_template("simple-xml.xml.template")
    body = tmpl.safe_substitute(_dashboard_context(uc, path))
    if not body.endswith("\n"):
        body += "\n"
    return body


def render_studio(
    uc: dict[str, Any],
    template: Template | None = None,
    *,
    path: Path | None = None,
) -> str:
    """Render Dashboard Studio XML (JSON in CDATA) for one UC."""
    tmpl = template or _load_template("studio.xml.template")
    body = tmpl.safe_substitute(_dashboard_context(uc, path))
    if not body.endswith("\n"):
        body += "\n"
    return body


def iter_uc_paths(
    content_root: Path,
    *,
    only: str | None = None,
    criticality: str | None = None,
    limit: int | None = None,
) -> list[Path]:
    paths = sorted(content_root.glob("cat-*/UC-*.json"))
    if only:
        needle = only.removeprefix("UC-")
        paths = [p for p in paths if p.stem == f"UC-{needle}" or p.stem == only]
    if criticality:
        crit = criticality.lower()
        filtered: list[Path] = []
        for path in paths:
            try:
                uc = load_uc(path)
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            if str(uc.get("criticality", "")).lower() == crit:
                filtered.append(path)
        paths = filtered
    if limit is not None and limit >= 0:
        paths = paths[:limit]
    return paths


def validate_spl_text(spl: str, *, label: str = "SPL") -> list[str]:
    """Return validation errors for one SPL string."""
    errors: list[str] = []
    if _MAKERESULTS_RE.search(spl):
        errors.append(f"{label}: contains forbidden | makeresults")
    if _RANDOM_RE.search(spl):
        errors.append(f"{label}: contains forbidden random()")
    if _COALESCE_LITERAL_RE.search(spl):
        errors.append(f"{label}: contains hardcoded coalesce() numeric fallback")
    if not check_pipe_per_line(spl):
        errors.append(f"{label}: pipe-per-line rule violated")
    return errors


def check_pipe_per_line(text: str) -> bool:
    """True when every ``|`` starts its own physical line (base search exempt)."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return True
    first = lines[0].strip()
    if first.count("|") > 0 and not first.startswith("|"):
        return False
    for line in lines:
        stripped = line.strip()
        if stripped.count("|") > 1:
            return False
    for line in lines[1:]:
        if not line.strip().startswith("|"):
            return False
    return True


def validate_simple_xml(text: str) -> list[str]:
    """Validate Classic Simple XML dashboard artefact."""
    import xml.etree.ElementTree as ET

    errors: list[str] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return [f"simple.xml: XML parse error: {exc}"]

    if root.tag != "dashboard":
        errors.append("simple.xml: root element must be <dashboard>")

    if _has_unescaped_ampersand(text):
        errors.append("simple.xml: unescaped & in <label> or <description>")

    for idx, query in enumerate(root.iter("query"), start=1):
        spl = (query.text or "").replace("&quot;", '"').replace("&amp;", "&")
        errors.extend(validate_spl_text(spl, label=f"simple.xml query #{idx}"))

    return errors


def validate_studio_xml(text: str) -> list[str]:
    """Validate Dashboard Studio wrapper + embedded JSON."""
    import xml.etree.ElementTree as ET

    errors: list[str] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return [f"studio.xml: XML parse error: {exc}"]

    if root.get("version") != "2":
        errors.append("studio.xml: <dashboard> must have version=\"2\"")

    if _has_unescaped_ampersand(text):
        errors.append("studio.xml: unescaped & in <label> or <description>")

    definition = root.find("definition")
    if definition is None or not definition.text:
        errors.append("studio.xml: missing <definition> CDATA block")
        return errors

    try:
        payload = json.loads(definition.text.strip())
    except json.JSONDecodeError as exc:
        errors.append(f"studio.xml: JSON parse error in CDATA: {exc}")
        return errors

    for section in ("dataSources", "visualizations", "layout", "defaults"):
        if section not in payload:
            errors.append(f"studio.xml: missing JSON section {section!r}")

    visualizations = payload.get("visualizations", {})
    if isinstance(visualizations, dict):
        for viz_id, viz in visualizations.items():
            if not isinstance(viz, dict):
                continue
            type_name = viz.get("type")
            if isinstance(type_name, str) and not type_name.startswith("splunk."):
                errors.append(
                    f"studio.xml: invalid visualization type {type_name!r} ({viz_id})"
                )

    data_sources = payload.get("dataSources", {})
    if isinstance(data_sources, dict):
        for name, ds in data_sources.items():
            if not isinstance(ds, dict):
                continue
            query = ds.get("options", {}).get("query", "")
            if isinstance(query, str):
                errors.extend(
                    validate_spl_text(query, label=f"studio.xml dataSources.{name}")
                )

    return errors


def validate_artefact_pair(simple: str, studio: str) -> list[str]:
    """Validate both dashboard artefacts for one UC."""
    errors = validate_simple_xml(simple)
    errors.extend(validate_studio_xml(studio))
    return errors


def emit_all(
    content_root: Path,
    out_root: Path,
    *,
    check: bool = False,
    only: str | None = None,
    criticality: str | None = None,
    limit: int | None = None,
) -> EmitReport:
    """Generate or drift-check dashboard pairs for all matching UCs."""
    report = EmitReport()
    simple_tmpl = _load_template("simple-xml.xml.template")
    studio_tmpl = _load_template("studio.xml.template")

    for path in iter_uc_paths(
        content_root,
        only=only,
        criticality=criticality,
        limit=limit,
    ):
        try:
            uc = load_uc(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            report.errors.append(f"{path}: {exc}")
            report.skipped += 1
            continue

        uc_id = _uc_display_id(uc, path)
        simple = render_simple_xml(uc, simple_tmpl, path=path)
        studio = render_studio(uc, studio_tmpl, path=path)
        validation_errors = validate_artefact_pair(simple, studio)
        if validation_errors:
            report.errors.extend(f"{uc_id}: {msg}" for msg in validation_errors)
            report.skipped += 1
            continue

        uc_out = out_root / uc_id
        simple_path = uc_out / "simple.xml"
        studio_path = uc_out / "studio.xml"

        if check:
            report.checked += 1
            for artefact_path, expected in (
                (simple_path, simple),
                (studio_path, studio),
            ):
                if not artefact_path.is_file():
                    report.drift += 1
                    report.errors.append(f"{uc_id}: missing {artefact_path.relative_to(out_root)}")
                    continue
                on_disk = artefact_path.read_text(encoding="utf-8")
                if on_disk != expected:
                    report.drift += 1
                    report.errors.append(f"{uc_id}: drift in {artefact_path.name}")
        else:
            uc_out.mkdir(parents=True, exist_ok=True)
            simple_path.write_text(simple, encoding="utf-8")
            studio_path.write_text(studio, encoding="utf-8")
            report.written += 1

        report.uc_ids.append(uc_id)

    return report


def audit_generated(out_root: Path) -> EmitReport:
    """Validate every dashboard pair already on disk under ``out_root``."""
    report = EmitReport()
    if not out_root.is_dir():
        report.errors.append(f"missing output directory: {out_root}")
        return report

    for uc_dir in sorted(p for p in out_root.iterdir() if p.is_dir()):
        simple_path = uc_dir / "simple.xml"
        studio_path = uc_dir / "studio.xml"
        if not simple_path.is_file() or not studio_path.is_file():
            report.errors.append(f"{uc_dir.name}: incomplete dashboard pair")
            report.skipped += 1
            continue
        simple = simple_path.read_text(encoding="utf-8")
        studio = studio_path.read_text(encoding="utf-8")
        errors = validate_artefact_pair(simple, studio)
        if errors:
            report.errors.extend(f"{uc_dir.name}: {msg}" for msg in errors)
            report.skipped += 1
            continue
        report.checked += 1
        report.uc_ids.append(uc_dir.name)

    return report


def _print_report(report: EmitReport, *, check: bool) -> None:
    if check:
        print(
            f"Dashboards: checked={report.checked} drift={report.drift} "
            f"skipped={report.skipped} errors={len(report.errors)}"
        )
    else:
        print(
            f"Dashboards: written={report.written} skipped={report.skipped} "
            f"errors={len(report.errors)}"
        )
    for msg in report.errors[:25]:
        print(f"  ERROR: {msg}", file=sys.stderr)
    if len(report.errors) > 25:
        print(f"  ... and {len(report.errors) - 25} more", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate per-UC Splunk dashboard scaffolds (Simple XML + Dashboard Studio)."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output root (default: dist/dashboards)",
    )
    parser.add_argument(
        "--content",
        type=Path,
        default=CONTENT_ROOT,
        help="UC content root (default: content/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Drift-check mode: regenerate in memory and compare to on-disk artefacts.",
    )
    parser.add_argument(
        "--only",
        metavar="UC-X.Y.Z",
        help="Emit dashboards for a single UC id.",
    )
    parser.add_argument(
        "--criticality",
        choices=("high", "medium", "low"),
        help="Filter UCs by criticality.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of UCs to process.",
    )
    args = parser.parse_args(argv)

    report = emit_all(
        args.content,
        args.out,
        check=args.check,
        only=args.only,
        criticality=args.criticality,
        limit=args.limit,
    )
    _print_report(report, check=args.check)

    if report.errors:
        return 1
    if args.check and report.drift:
        return 1
    if args.check and report.checked == 0:
        print("ERROR: no dashboard artefacts to check — run generate-dashboards first", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
