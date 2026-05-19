#!/usr/bin/env python3
"""Vendor product changelog audit (Cisco-only v1).

Maintains a curated, machine-readable record of upstream vendor release
changes that affect Splunk field names, log formats, or sourcetypes.
For v1 the changelog is hand-curated under ``data/vendor-changelog/``;
this audit validates schema, freshness, and surfaces UCs whose SPL
references deprecated or renamed vendor fields.

Exit codes
----------
* ``0`` — all vendor files valid and freshness within policy.
* ``1`` — schema/freshness failure, or ``--check`` detected stale data.
* ``2`` — usage / I/O error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from splunk_uc.audits._uc_walk import REPO, get_text_field, iter_uc_sidecars

VENDOR_CHANGELOG_DIR = REPO / "data" / "vendor-changelog"
SCHEMA_PATH = REPO / "schemas" / "vendor-changelog.schema.json"
DEFAULT_OUT_DIR = REPO / "dist" / "audits"

# Vendors permitted without a schema/registry bump. Follow-up PRs add
# aws (J-5b), microsoft (J-5c), and crowdstrike (J-5d).
KNOWN_VENDORS: dict[str, frozenset[str]] = {
    "cisco": frozenset({"1.0"}),
}

CHANGE_KINDS: frozenset[str] = frozenset(
    {
        "field-added",
        "field-renamed",
        "field-removed",
        "field-deprecated",
        "format-changed",
        "log-source-renamed",
        "log-source-removed",
        "log-source-added",
        "other",
    }
)

DEFAULT_WARN_DAYS = 90
DEFAULT_FAIL_DAYS = 180

_SPL_FIELDS = ("spl", "cimSpl", "rbaSpl", "mvSpl")


class FreshnessLevel(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


class VendorChangelogError(ValueError):
    """Raised when a vendor changelog file fails validation."""


@dataclass(frozen=True)
class FieldRename:
    from_field: str
    to_field: str


@dataclass(frozen=True)
class ChangelogEntry:
    id: str
    product: str
    product_display: str
    release: str
    release_date: str
    change_kind: str
    summary: str
    details: str
    fields_added: tuple[str, ...]
    fields_removed: tuple[str, ...]
    fields_renamed: tuple[FieldRename, ...]
    fields_deprecated: tuple[str, ...]
    spl_impact: str
    affected_uc_categories: tuple[str, ...]
    source_url: str
    source_kind: str
    severity: str
    added_by: str
    added_date: str


@dataclass(frozen=True)
class VendorChangelog:
    path: Path
    version: str
    generated: date
    schema_version: str
    vendor: str
    vendor_display: str
    entries: tuple[ChangelogEntry, ...]


@dataclass(frozen=True)
class FreshnessReport:
    vendor: str
    generated: date
    days_old: int
    level: FreshnessLevel
    warn_days: int
    fail_days: int
    message: str


@dataclass(frozen=True)
class Impact:
    uc_id: str
    entry_id: str
    vendor: str
    product: str
    change_kind: str
    reasons: tuple[str, ...]
    spl_impact: str
    severity: str


@dataclass
class AuditSummary:
    vendors: dict[str, dict[str, Any]] = field(default_factory=dict)
    freshness: list[dict[str, Any]] = field(default_factory=list)
    impacted_ucs: list[dict[str, Any]] = field(default_factory=list)
    top_affected_categories: list[dict[str, Any]] = field(default_factory=list)
    recent_changes: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


def _parse_date(value: str, *, context: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise VendorChangelogError(f"{context}: invalid date {value!r}") from exc


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise VendorChangelogError(f"{SCHEMA_PATH}: schema root must be an object")
    return payload


def _entry_sort_key(entry: ChangelogEntry) -> tuple[int, str]:
    ordinal = _parse_date(entry.release_date, context="entry.release_date").toordinal()
    return (-ordinal, entry.id)


def _parse_entry(raw: dict[str, Any]) -> ChangelogEntry:
    renames = tuple(
        FieldRename(from_field=str(item["from"]), to_field=str(item["to"]))
        for item in raw.get("fields_renamed", [])
        if isinstance(item, dict)
    )
    change_kind = str(raw["change_kind"])
    if change_kind not in CHANGE_KINDS:
        raise VendorChangelogError(f"entry {raw.get('id')}: unknown change_kind {change_kind!r}")
    return ChangelogEntry(
        id=str(raw["id"]),
        product=str(raw["product"]),
        product_display=str(raw["product_display"]),
        release=str(raw["release"]),
        release_date=str(raw["release_date"]),
        change_kind=change_kind,
        summary=str(raw["summary"]),
        details=str(raw["details"]),
        fields_added=tuple(str(v) for v in raw.get("fields_added", [])),
        fields_removed=tuple(str(v) for v in raw.get("fields_removed", [])),
        fields_renamed=renames,
        fields_deprecated=tuple(str(v) for v in raw.get("fields_deprecated", [])),
        spl_impact=str(raw["spl_impact"]),
        affected_uc_categories=tuple(str(v) for v in raw.get("affected_uc_categories", [])),
        source_url=str(raw["source_url"]),
        source_kind=str(raw["source_kind"]),
        severity=str(raw["severity"]),
        added_by=str(raw["added_by"]),
        added_date=str(raw["added_date"]),
    )


def _sort_entries(entries: tuple[ChangelogEntry, ...]) -> tuple[ChangelogEntry, ...]:
    return tuple(sorted(entries, key=_entry_sort_key))


def _validate_vendor_registration(vendor: str, schema_version: str) -> None:
    allowed = KNOWN_VENDORS.get(vendor)
    if allowed is None:
        known = ", ".join(sorted(KNOWN_VENDORS))
        raise VendorChangelogError(
            f"vendor {vendor!r} is not registered in KNOWN_VENDORS "
            f"(known: {known}). Add the vendor in a dedicated PR with schema review."
        )
    if schema_version not in allowed:
        raise VendorChangelogError(
            f"vendor {vendor!r}: schema_version {schema_version!r} is not allowed "
            f"(allowed: {sorted(allowed)})"
        )


def load_vendor_changelog(path: Path) -> VendorChangelog:
    """Parse and schema-validate one vendor changelog file."""
    if not path.is_file():
        raise VendorChangelogError(f"vendor changelog not found: {path}")

    with path.open(encoding="utf-8") as fh:
        try:
            payload = json.load(fh)
        except json.JSONDecodeError as exc:
            raise VendorChangelogError(f"{path}: invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise VendorChangelogError(f"{path}: top-level value must be an object")

    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        loc = ".".join(str(part) for part in first.path) or "<root>"
        raise VendorChangelogError(f"{path}: schema violation at {loc}: {first.message}")

    vendor = str(payload["vendor"])
    schema_version = str(payload["schema_version"])
    stem = path.stem
    if vendor != stem:
        raise VendorChangelogError(
            f"{path}: vendor field {vendor!r} does not match filename stem {stem!r}"
        )
    _validate_vendor_registration(vendor, schema_version)

    raw_entries = payload.get("entries", [])
    if not isinstance(raw_entries, list):
        raise VendorChangelogError(f"{path}: entries must be an array")

    entries = _sort_entries(tuple(_parse_entry(item) for item in raw_entries if isinstance(item, dict)))

    generated = _parse_date(str(payload["generated"]), context=f"{path}: generated")

    return VendorChangelog(
        path=path,
        version=str(payload["version"]),
        generated=generated,
        schema_version=schema_version,
        vendor=vendor,
        vendor_display=str(payload["vendor_display"]),
        entries=entries,
    )


def load_all_vendor_changelogs(directory: Path = VENDOR_CHANGELOG_DIR) -> dict[str, VendorChangelog]:
    """Load every ``*.json`` file in ``data/vendor-changelog/``."""
    if not directory.is_dir():
        raise VendorChangelogError(f"vendor changelog directory not found: {directory}")

    changelogs: dict[str, VendorChangelog] = {}
    for path in sorted(directory.glob("*.json")):
        changelog = load_vendor_changelog(path)
        if changelog.vendor in changelogs:
            raise VendorChangelogError(
                f"duplicate vendor {changelog.vendor!r} from {path} and {changelogs[changelog.vendor].path}"
            )
        changelogs[changelog.vendor] = changelog
    return changelogs


def evaluate_freshness(
    changelog: VendorChangelog,
    today: date,
    *,
    warn_days: int = DEFAULT_WARN_DAYS,
    fail_days: int = DEFAULT_FAIL_DAYS,
) -> FreshnessReport:
    """Flag stale changelog files based on the ``generated`` date."""
    days_old = (today - changelog.generated).days
    if days_old > fail_days:
        level = FreshnessLevel.FAIL
        message = (
            f"{changelog.vendor}: generated {changelog.generated.isoformat()} is "
            f"{days_old} days old (fail threshold {fail_days})"
        )
    elif days_old > warn_days:
        level = FreshnessLevel.WARN
        message = (
            f"{changelog.vendor}: generated {changelog.generated.isoformat()} is "
            f"{days_old} days old (warn threshold {warn_days})"
        )
    else:
        level = FreshnessLevel.OK
        message = (
            f"{changelog.vendor}: generated {changelog.generated.isoformat()} is "
            f"{days_old} days old (fresh)"
        )
    return FreshnessReport(
        vendor=changelog.vendor,
        generated=changelog.generated,
        days_old=days_old,
        level=level,
        warn_days=warn_days,
        fail_days=fail_days,
        message=message,
    )


def _uc_category(uc: dict[str, Any]) -> str | None:
    uc_id = uc.get("id")
    if not isinstance(uc_id, str):
        return None
    parts = uc_id.split(".")
    if not parts:
        return None
    return parts[0]


def _collect_spl_text(uc: dict[str, Any]) -> str:
    chunks: list[str] = []
    for key in _SPL_FIELDS:
        text = get_text_field(uc, key)
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def _spl_references_field(spl_text: str, field_name: str) -> bool:
    if not spl_text or not field_name:
        return False
    pattern = re.compile(rf"(?<![\w.-]){re.escape(field_name)}(?![\w.-])")
    return pattern.search(spl_text) is not None


def _data_sources_text(uc: dict[str, Any]) -> str:
    ds = uc.get("dataSources")
    if isinstance(ds, str):
        return ds
    if isinstance(ds, list):
        parts: list[str] = []
        for item in ds:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("name", "sourcetype", "source", "type"):
                    val = item.get(key)
                    if isinstance(val, str):
                        parts.append(val)
        return " ".join(parts)
    return ""


def evaluate_uc_impact(
    uc: dict[str, Any],
    changelogs: dict[str, VendorChangelog],
) -> list[Impact]:
    """Return changelog entries that may affect this UC."""
    uc_id_raw = uc.get("id")
    uc_id = f"UC-{uc_id_raw}" if isinstance(uc_id_raw, str) else "UC-<unknown>"
    category = _uc_category(uc)
    spl_text = _collect_spl_text(uc)
    ds_text = _data_sources_text(uc).lower()

    impacts: list[Impact] = []

    for changelog in changelogs.values():
        for entry in changelog.entries:
            reasons: list[str] = []

            if category and category in entry.affected_uc_categories:
                reasons.append(f"category {category} listed in affected_uc_categories")

            for removed in entry.fields_removed:
                if _spl_references_field(spl_text, removed):
                    reasons.append(f"SPL references removed field {removed!r}")

            for rename in entry.fields_renamed:
                if _spl_references_field(spl_text, rename.from_field):
                    reasons.append(
                        f"SPL references renamed field {rename.from_field!r} -> {rename.to_field!r}"
                    )

            for deprecated in entry.fields_deprecated:
                if _spl_references_field(spl_text, deprecated):
                    reasons.append(f"SPL references deprecated field {deprecated!r}")

            if entry.product.lower() in ds_text:
                reasons.append(f"dataSources references product {entry.product!r}")

            if not reasons:
                continue

            impacts.append(
                Impact(
                    uc_id=uc_id,
                    entry_id=entry.id,
                    vendor=changelog.vendor,
                    product=entry.product,
                    change_kind=entry.change_kind,
                    reasons=tuple(sorted(set(reasons))),
                    spl_impact=entry.spl_impact,
                    severity=entry.severity,
                )
            )

    impacts.sort(key=lambda item: (item.uc_id, item.entry_id))
    return impacts


def _entry_to_dict(entry: ChangelogEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "product": entry.product,
        "product_display": entry.product_display,
        "release": entry.release,
        "release_date": entry.release_date,
        "change_kind": entry.change_kind,
        "summary": entry.summary,
        "severity": entry.severity,
    }


def _impact_to_dict(impact: Impact) -> dict[str, Any]:
    return asdict(impact)


def build_audit_report(
    changelogs: dict[str, VendorChangelog],
    *,
    today: date,
    warn_days: int,
    fail_days: int,
    show_impact: bool,
) -> tuple[AuditSummary, list[FreshnessReport]]:
    """Build the machine summary used for JSON/Markdown output."""
    summary = AuditSummary()
    freshness_reports: list[FreshnessReport] = []

    category_counts: dict[str, int] = {}
    all_impacts: list[Impact] = []

    for vendor in sorted(changelogs):
        changelog = changelogs[vendor]
        freshness = evaluate_freshness(
            changelog, today, warn_days=warn_days, fail_days=fail_days
        )
        freshness_reports.append(freshness)
        summary.vendors[vendor] = {
            "vendor_display": changelog.vendor_display,
            "entry_count": len(changelog.entries),
            "generated": changelog.generated.isoformat(),
            "schema_version": changelog.schema_version,
            "version": changelog.version,
        }
        summary.freshness.append(
            {
                "vendor": freshness.vendor,
                "generated": freshness.generated.isoformat(),
                "days_old": freshness.days_old,
                "level": freshness.level.value,
                "message": freshness.message,
            }
        )
        summary.recent_changes[vendor] = [
            _entry_to_dict(entry) for entry in changelog.entries[:5]
        ]
        for entry in changelog.entries:
            for cat in entry.affected_uc_categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1

    if show_impact:
        for _path, uc in iter_uc_sidecars():
            all_impacts.extend(evaluate_uc_impact(uc, changelogs))

    summary.top_affected_categories = [
        {"category": cat, "entry_hits": count}
        for cat, count in sorted(
            category_counts.items(), key=lambda item: (-item[1], item[0])
        )[:10]
    ]

    impacted_by_uc: dict[str, list[Impact]] = {}
    for impact in all_impacts:
        impacted_by_uc.setdefault(impact.uc_id, []).append(impact)

    summary.impacted_ucs = [
        {
            "uc_id": uc_id,
            "impact_count": len(items),
            "impacts": [_impact_to_dict(item) for item in items],
        }
        for uc_id, items in sorted(impacted_by_uc.items())
    ]

    return summary, freshness_reports


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(
    summary: AuditSummary,
    freshness_reports: list[FreshnessReport],
) -> str:
    """Human-readable audit rollup."""
    lines = [
        "# Vendor changelog audit",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Freshness",
        "",
        "| Vendor | Generated | Days old | Level |",
        "| --- | --- | ---: | --- |",
    ]
    for report in freshness_reports:
        lines.append(
            f"| {report.vendor} | {report.generated.isoformat()} | "
            f"{report.days_old} | {report.level.value} |"
        )

    lines.extend(["", "## Recent changes (top 5 per vendor)", ""])
    for vendor, entries in sorted(summary.recent_changes.items()):
        lines.append(f"### {vendor}")
        lines.append("")
        if not entries:
            lines.append("_No entries._")
            lines.append("")
            continue
        for entry in entries:
            lines.append(
                f"- **{entry['id']}** ({entry['release_date']}) — "
                f"{entry['summary']} (`{entry['change_kind']}`, {entry['severity']})"
            )
        lines.append("")

    lines.extend(["## Top affected UC categories", ""])
    if summary.top_affected_categories:
        lines.append("| Category | Entry hits |")
        lines.append("| --- | ---: |")
        for row in summary.top_affected_categories:
            lines.append(f"| {row['category']} | {row['entry_hits']} |")
    else:
        lines.append("_No category rollups._")

    lines.extend(["", "## Top impacted UCs", ""])
    top_ucs = summary.impacted_ucs[:10]
    if not top_ucs:
        lines.append("_No UCs flagged for review._")
    else:
        for row in top_ucs:
            lines.append(f"### {row['uc_id']} ({row['impact_count']} hits)")
            lines.append("")
            for impact in row["impacts"][:3]:
                reasons = "; ".join(impact["reasons"])
                lines.append(
                    f"- {impact['entry_id']} ({impact['vendor']}/{impact['product']}): "
                    f"{reasons}"
                )
            if row["impact_count"] > 3:
                lines.append(f"- … and {row['impact_count'] - 3} more")
            lines.append("")

    lines.append("")
    return "\n".join(lines)


def write_report(
    out_dir: Path,
    summary: AuditSummary,
    freshness_reports: list[FreshnessReport],
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "vendor-changelog.json"
    md_path = out_dir / "vendor-changelog.md"

    payload = {
        "$comment": "Generated by python -m splunk_uc audit-vendor-changelog (gitignored under dist/).",
        "generated_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "vendors": summary.vendors,
        "freshness": summary.freshness,
        "top_affected_categories": summary.top_affected_categories,
        "impacted_uc_count": len(summary.impacted_ucs),
        "impacted_ucs": summary.impacted_ucs,
        "recent_changes": summary.recent_changes,
    }
    json_path.write_text(_canonical_json(payload), encoding="utf-8")
    md_path.write_text(render_markdown(summary, freshness_reports), encoding="utf-8")
    return json_path, md_path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit hand-curated vendor product changelogs and UC impact."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when freshness exceeds --max-age-days or schema validation fails.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Write JSON/Markdown report under this directory (default: {DEFAULT_OUT_DIR}).",
    )
    parser.add_argument(
        "--vendor",
        action="append",
        dest="vendors",
        help="Limit audit to one vendor slug (repeatable). Default: all registered vendors.",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=DEFAULT_FAIL_DAYS,
        help=f"Fail freshness when generated is older than N days (default: {DEFAULT_FAIL_DAYS}).",
    )
    parser.add_argument(
        "--warn-age-days",
        type=int,
        default=DEFAULT_WARN_DAYS,
        help=f"Warn freshness when generated is older than N days (default: {DEFAULT_WARN_DAYS}).",
    )
    parser.add_argument(
        "--show-impact",
        action="store_true",
        help="Scan UC sidecars and include impacted UC rollups in the report.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    today = date.today()

    try:
        changelogs = load_all_vendor_changelogs(VENDOR_CHANGELOG_DIR)
    except VendorChangelogError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.vendors:
        missing = [v for v in args.vendors if v not in changelogs]
        if missing:
            print(
                f"ERROR: vendor file(s) not found: {', '.join(sorted(missing))}",
                file=sys.stderr,
            )
            return 2
        changelogs = {v: changelogs[v] for v in sorted(args.vendors)}

    if not changelogs:
        print("ERROR: no vendor changelog files found", file=sys.stderr)
        return 2

    summary, freshness_reports = build_audit_report(
        changelogs,
        today=today,
        warn_days=args.warn_age_days,
        fail_days=args.max_age_days,
        show_impact=args.show_impact or args.check,
    )

    json_path, md_path = write_report(args.out, summary, freshness_reports)

    exit_code = 0
    for report in freshness_reports:
        if report.level is FreshnessLevel.WARN:
            print(f"WARN: {report.message}", file=sys.stderr)
        elif report.level is FreshnessLevel.FAIL:
            print(f"FAIL: {report.message}", file=sys.stderr)
            exit_code = 1

    total_entries = sum(len(c.entries) for c in changelogs.values())
    impacted = len(summary.impacted_ucs)
    print(
        f"Vendor changelog: {len(changelogs)} vendor(s), {total_entries} entries, "
        f"{impacted} UC(s) flagged"
    )
    print(f"Wrote {_display_path(json_path)} and {_display_path(md_path)}")

    if args.check and exit_code != 0:
        return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
