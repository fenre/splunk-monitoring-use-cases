#!/usr/bin/env python3
"""Emit per-UC alert action templates under ``dist/alert-actions/``.

For every UC sidecar in ``content/cat-*/UC-*.json`` this generator writes:

* ``dist/alert-actions/soar/UC-X.Y.Z.yaml`` — SOAR playbook stub
* ``dist/alert-actions/email/UC-X.Y.Z.html`` — HTML email template
* ``dist/alert-actions/email/UC-X.Y.Z.txt`` — plain-text email fallback

Templates are rendered from ``templates/alert-actions/*.template`` using
stdlib :mod:`string.Template` (no Jinja2 dependency). Output is
byte-deterministic: sorted UC walk order, LF line endings, stable YAML
key order, no timestamps in generated artefacts.

``--check`` compares freshly rendered templates for every UC that has a
golden fixture under ``tests/fixtures/alert-actions/``. CI runs
``generate-alert-actions --check --limit 20`` to validate fixtures and
smoke-generate the first 20 UCs without writing ``dist/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "content"
TEMPLATE_DIR = REPO_ROOT / "templates" / "alert-actions"
DEFAULT_OUT = REPO_ROOT / "dist" / "alert-actions"
DEFAULT_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "alert-actions"
CATALOGUE_BASE_URL = "https://fenre.github.io/splunk-monitoring-use-cases"
SPL_MAX_CHARS = 4_000

# Category folder prefixes that imply OT / safety-adjacent content.
_OT_CATEGORY_PREFIXES = (
    "cat-19-compute-infrastructure-hci-converged",
    "cat-20-industrial-ot-ics",
    "cat-21-smart-buildings-facilities",
)

_OT_EQUIPMENT_TOKENS = frozenset(
    {
        "modbus",
        "opc_ua",
        "opc-ua",
        "plc",
        "dcs",
        "scada",
        "sis",
        "bacnet",
        "mqtt",
        "ot",
        "ics",
    }
)

_CRITICALITY_FILTER = frozenset({"critical", "high", "medium", "low", "all"})


@dataclass(frozen=True)
class UcRecord:
    """Minimal UC payload consumed by the template renderer."""

    uc_id: str
    title: str
    description: str
    value: str
    criticality: str
    spl: str
    mitre_tags: tuple[str, ...]
    regulatory_tags: tuple[str, ...]
    is_ot_related: bool
    cat_slug: str


@dataclass(frozen=True)
class RenderedTemplates:
    """Three template artefacts for one UC."""

    uc_id: str
    soar_yaml: str
    email_html: str
    email_txt: str


def _uc_sort_key(path: Path) -> tuple[int, ...]:
    stem = path.stem.removeprefix("UC-")
    parts: list[int] = []
    for chunk in stem.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(1_000_000)
    return tuple(parts)


def iter_uc_paths(
    *,
    content_dir: Path = CONTENT_DIR,
    only: str | None = None,
    criticality: str = "all",
) -> Iterator[Path]:
    """Yield UC sidecar paths in deterministic sorted order."""
    crit = criticality.lower()
    if crit not in _CRITICALITY_FILTER:
        raise ValueError(
            f"invalid criticality {criticality!r}; "
            f"expected one of {sorted(_CRITICALITY_FILTER)}"
        )
    if only:
        uc_id = only.removeprefix("UC-")
        matches = sorted(content_dir.glob(f"cat-*/UC-{uc_id}.json"))
        if not matches:
            raise FileNotFoundError(f"no sidecar found for UC-{uc_id}")
        yield matches[0]
        return

    for path in sorted(content_dir.glob("cat-*/UC-*.json"), key=_uc_sort_key):
        if crit == "all":
            yield path
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(payload.get("criticality", "")).lower() == crit:
            yield path


def _truncate_spl(spl: str, limit: int = SPL_MAX_CHARS) -> str:
    text = spl.strip()
    if len(text) <= limit:
        return text
    return text[: limit - len("\n... [truncated]")] + "\n... [truncated]"


def _spl_summary(spl: str, max_len: int = 240) -> str:
    first_line = spl.strip().splitlines()[0] if spl.strip() else ""
    if len(first_line) <= max_len:
        return first_line
    return first_line[: max_len - 3] + "..."


def _yaml_list(items: Iterable[str], indent: int = 0) -> str:
    prefix = " " * indent
    values = sorted({s for s in items if s})
    if not values:
        return f"{prefix}[]"
    lines = [f"{prefix}- {json.dumps(v)}" for v in values]
    return "\n".join(lines)


def _yaml_json_string(text: str) -> str:
    """Return a YAML-safe double-quoted string via JSON encoding."""
    return json.dumps(text, ensure_ascii=False)


def _extract_regulatory_tags(compliance: Any) -> tuple[str, ...]:
    if not isinstance(compliance, list):
        return ()
    tags: set[str] = set()
    for entry in compliance:
        if not isinstance(entry, dict):
            continue
        regulation = entry.get("regulation")
        clause = entry.get("clause")
        if isinstance(regulation, str) and regulation.strip():
            if isinstance(clause, str) and clause.strip():
                tags.add(f"{regulation}:{clause}")
            else:
                tags.add(regulation.strip())
    return tuple(sorted(tags))


def _is_ot_related(payload: dict[str, Any], cat_slug: str) -> bool:
    if any(cat_slug.startswith(prefix) for prefix in _OT_CATEGORY_PREFIXES):
        return True
    monitoring = payload.get("monitoringType") or []
    if isinstance(monitoring, list):
        joined = " ".join(str(x).lower() for x in monitoring)
        if any(token in joined for token in ("ot", "ics", "industrial", "sis")):
            return True
    equipment = payload.get("equipment") or []
    if isinstance(equipment, list):
        for item in equipment:
            token = str(item).lower().replace("-", "_")
            if token in _OT_EQUIPMENT_TOKENS:
                return True
    blob = " ".join(
        str(payload.get(k, ""))
        for k in ("title", "description", "value", "detailedImplementation")
    ).lower()
    return any(
        phrase in blob
        for phrase in (
            "sis ",
            " safety ",
            " plc ",
            " dcs ",
            " scada ",
            " ot/",
            "ics ",
        )
    )


def load_uc_record(path: Path) -> UcRecord:
    payload = json.loads(path.read_text(encoding="utf-8"))
    uc_id = str(payload.get("id") or path.stem.removeprefix("UC-"))
    cat_slug = path.parent.name
    mitre = payload.get("mitreAttack") or []
    mitre_tags: tuple[str, ...] = ()
    if isinstance(mitre, list):
        mitre_tags = tuple(sorted(str(t) for t in mitre if t))
    return UcRecord(
        uc_id=uc_id,
        title=str(payload.get("title") or f"UC-{uc_id}"),
        description=str(payload.get("description") or ""),
        value=str(payload.get("value") or ""),
        criticality=str(payload.get("criticality") or "medium").lower(),
        spl=str(payload.get("spl") or ""),
        mitre_tags=mitre_tags,
        regulatory_tags=_extract_regulatory_tags(payload.get("compliance")),
        is_ot_related=_is_ot_related(payload, cat_slug),
        cat_slug=cat_slug,
    )


def _email_tier(criticality: str) -> tuple[str, str, str]:
    crit = criticality.lower()
    if crit in {"critical", "high"}:
        return (
            "[CRITICAL] $title fired — immediate action required",
            "urgent",
            "Immediate action required. Review the firing search, validate impact, "
            "and escalate per your runbook.",
        )
    if crit == "medium":
        return (
            "[ALERT] $title fired",
            "investigative",
            "Investigate context and correlate with recent changes before escalation.",
        )
    return (
        "[INFO] $title aggregated digest",
        "digest",
        "This item is included in the informational digest. Review during the next "
        "scheduled triage window unless correlated with higher-severity activity.",
    )


def _do_not_section(record: UcRecord) -> str:
    if not record.is_ot_related:
        return (
            "No OT/safety-specific prohibitions apply to this use case. "
            "Follow standard change-management for any containment action."
        )
    return (
        "Do NOT disable safety instrumented functions, write to PLCs/HMIs/DCS/RTUs, "
        "or execute automated containment against Level 0/1/2 OT assets without "
        "human-in-the-loop approval from OT engineering."
    )


def _pre_conditions(record: UcRecord) -> str:
    base = (
        "Human-in-the-loop required for OT/safety-critical actions. "
        "Confirm alert is not a known maintenance window or approved test activity."
    )
    if record.is_ot_related:
        return (
            base
            + " OT engineering acknowledgement is mandatory before any action that "
            "touches process control or safety systems."
        )
    return base


def _escape_template(text: str) -> str:
    """Escape ``$`` for :class:`string.Template` substitution."""
    return text.replace("$", "$$")


def _load_template(name: str) -> Template:
    path = TEMPLATE_DIR / name
    return Template(path.read_text(encoding="utf-8"))


def render_templates(record: UcRecord) -> RenderedTemplates:
    uc_display = f"UC-{record.uc_id}"
    uc_url = f"{CATALOGUE_BASE_URL}/uc/{uc_display}/"
    spl_reference = _truncate_spl(record.spl)
    spl_summary = _spl_summary(record.spl)
    subject_tpl, tone_class, tone_body = _email_tier(record.criticality)
    email_subject = Template(subject_tpl).substitute(title=record.title)

    common = {
        "uc_id": uc_display,
        "uc_url": uc_url,
        "title": _escape_template(record.title),
        "description": _escape_template(record.description),
        "value": _escape_template(record.value),
        "criticality": record.criticality,
        "spl_reference_json": _yaml_json_string(spl_reference),
        "spl_summary": _escape_template(spl_summary),
        "mitre_tags_yaml": _yaml_list(record.mitre_tags, indent=2),
        "regulatory_tags_yaml": _yaml_list(record.regulatory_tags, indent=2),
        "pre_conditions": _escape_template(_pre_conditions(record)),
        "do_not_section": _escape_template(_do_not_section(record)),
        "human_acknowledgement_required": "true",
        "escalation_contact_placeholder": "{customer-on-call}",
        "email_subject": _escape_template(email_subject),
        "email_tone_class": tone_class,
        "email_tone_body": _escape_template(tone_body),
        "timestamp_placeholder": "{timestamp_placeholder}",
        "runtime_spl_summary": "{spl_summary}",
    }

    soar = _load_template("soar-playbook.yaml.template").substitute(**common)
    html = _load_template("email-digest.html.template").substitute(**common)
    txt = _load_template("email-digest.txt.template").substitute(**common)

    # Normalise line endings for determinism.
    soar = soar.replace("\r\n", "\n").replace("\r", "\n")
    html = html.replace("\r\n", "\n").replace("\r", "\n")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    if not soar.endswith("\n"):
        soar += "\n"
    if not html.endswith("\n"):
        html += "\n"
    if not txt.endswith("\n"):
        txt += "\n"
    return RenderedTemplates(
        uc_id=uc_display,
        soar_yaml=soar,
        email_html=html,
        email_txt=txt,
    )


def write_templates(rendered: RenderedTemplates, out_dir: Path) -> None:
    soar_dir = out_dir / "soar"
    email_dir = out_dir / "email"
    soar_dir.mkdir(parents=True, exist_ok=True)
    email_dir.mkdir(parents=True, exist_ok=True)
    (soar_dir / f"{rendered.uc_id}.yaml").write_text(
        rendered.soar_yaml, encoding="utf-8", newline="\n"
    )
    (email_dir / f"{rendered.uc_id}.html").write_text(
        rendered.email_html, encoding="utf-8", newline="\n"
    )
    (email_dir / f"{rendered.uc_id}.txt").write_text(
        rendered.email_txt, encoding="utf-8", newline="\n"
    )


def fixture_uc_ids(fixtures_root: Path) -> list[str]:
    soar_dir = fixtures_root / "soar"
    if not soar_dir.is_dir():
        return []
    ids: list[str] = []
    for path in sorted(soar_dir.glob("UC-*.yaml")):
        ids.append(path.stem)
    return ids


def _read_fixture_triplet(fixtures_root: Path, uc_id: str) -> dict[str, str]:
    return {
        "soar": (fixtures_root / "soar" / f"{uc_id}.yaml").read_text(encoding="utf-8"),
        "html": (fixtures_root / "email" / f"{uc_id}.html").read_text(encoding="utf-8"),
        "txt": (fixtures_root / "email" / f"{uc_id}.txt").read_text(encoding="utf-8"),
    }


def check_fixtures(
    *,
    content_dir: Path = CONTENT_DIR,
    fixtures_root: Path = DEFAULT_FIXTURES,
) -> list[str]:
    """Return human-readable drift messages (empty when fixtures match)."""
    errors: list[str] = []
    for uc_id in fixture_uc_ids(fixtures_root):
        sidecar_id = uc_id.removeprefix("UC-")
        paths = sorted(content_dir.glob(f"cat-*/UC-{sidecar_id}.json"))
        if not paths:
            errors.append(f"{uc_id}: sidecar missing under content/")
            continue
        rendered = render_templates(load_uc_record(paths[0]))
        expected = _read_fixture_triplet(fixtures_root, uc_id)
        actual = {
            "soar": rendered.soar_yaml,
            "html": rendered.email_html,
            "txt": rendered.email_txt,
        }
        for kind in ("soar", "html", "txt"):
            if actual[kind] != expected[kind]:
                errors.append(f"{uc_id}: {kind} drift (regenerate fixtures)")
    return errors


def generate_all(
    *,
    content_dir: Path = CONTENT_DIR,
    out_dir: Path = DEFAULT_OUT,
    only: str | None = None,
    criticality: str = "all",
    limit: int | None = None,
    dry_run: bool = False,
) -> int:
    count = 0
    for path in iter_uc_paths(
        content_dir=content_dir, only=only, criticality=criticality
    ):
        if limit is not None and count >= limit:
            break
        rendered = render_templates(load_uc_record(path))
        if not dry_run:
            write_templates(rendered, out_dir)
        count += 1
    return count


def _argv_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="generate-alert-actions",
        description="Emit per-UC SOAR + email alert action templates.",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Compare golden fixtures under tests/fixtures/alert-actions/.",
    )
    p.add_argument("--only", metavar="UC-X.Y.Z", help="Emit templates for one UC.")
    p.add_argument(
        "--criticality",
        default="all",
        choices=sorted(_CRITICALITY_FILTER),
        help="Filter UCs by criticality (default: all).",
    )
    p.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="Cap UC count (CI smoke vs full corpus).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output root (default: {DEFAULT_OUT.relative_to(REPO_ROOT)}).",
    )
    p.add_argument(
        "--fixtures-root",
        type=Path,
        default=DEFAULT_FIXTURES,
        help="Golden fixture root for --check.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Render without writing dist/ artefacts.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _argv_parser()
    args = parser.parse_args(argv)

    try:
        if args.check:
            errors = check_fixtures(
                content_dir=CONTENT_DIR, fixtures_root=args.fixtures_root
            )
            if errors:
                for msg in errors:
                    print(f"DRIFT: {msg}", file=sys.stderr)
                return 1
            # Smoke-render up to --limit UCs to catch runtime failures.
            smoke = generate_all(
                content_dir=CONTENT_DIR,
                out_dir=args.out,
                only=args.only,
                criticality=args.criticality,
                limit=args.limit,
                dry_run=True,
            )
            fixture_count = len(fixture_uc_ids(args.fixtures_root))
            print(
                f"OK: {fixture_count} golden fixture(s) match; "
                f"smoke-rendered {smoke} UC(s)."
            )
            return 0

        count = generate_all(
            content_dir=CONTENT_DIR,
            out_dir=args.out,
            only=args.only,
            criticality=args.criticality,
            limit=args.limit,
            dry_run=args.dry_run,
        )
        action = "would emit" if args.dry_run else "emitted"
        print(f"{action} alert action templates for {count} UC(s) -> {args.out}")
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
