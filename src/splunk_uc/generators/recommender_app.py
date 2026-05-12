#!/usr/bin/env python3
"""Generate the ``splunk-uc-recommender`` Splunk app (single-artefact).

The recommender app is a Cloud-safe search-head companion to the
use-case repository:

* scans a Splunk environment for sourcetypes, indexes, CIM acceleration
  status, and installed apps (four Cloud-safe saved searches);
* matches that inventory against the upstream API indexes under
  ``/api/v1/recommender/`` to preview UCs the operator can enable;
* never writes to ``savedsearches.conf`` on the target instance — the UI
  ships "Copy SPL" and "Open in Search app" deep-links only;
* tracks per-UC implementation status in two KV collections
  (``uc_recommender_implementations`` + ``uc_recommender_audit``);
* surfaces the Splunkbase apps required to implement each UC and gates
  the install guidance on a custom ``edit_uc_implementations`` capability.

Design rules:

* **Deterministic** — same inputs always produce byte-identical output.
  CI runs ``--check`` to diff the committed tree against the regenerated
  tree and fails on drift.
* **Offline** — no network calls; everything reads from the repository.
* **AppInspect-shaped** — ``app.manifest`` v2, ``default/app.conf``,
  ``metadata/default.meta``, ``README.md``, MIT ``LICENSE``, nav stub,
  and saved searches that honour ``disabled = 1`` / ``is_scheduled = 0``
  unless they are the low-cost inventory refreshers that the recommender
  strictly relies on.
* **Cloud-safe** — no ``commands.conf``, ``restmap.conf``,
  ``web.conf[expose:*]``, or ``[script://]`` inputs.

History: v9.0 consolidated this repo to a single Splunk artefact. The
companion ``splunk-uc-recommender-ta`` (Enterprise-only modular input
TA) and the 12 per-regulation app variants were both retired in favour
of this one app. See ``docs/migration-v8.md``.

CLI
---

    # Default: generate the recommender app
    python3 scripts/generate_recommender_app.py

    # Determinism guard (CI)
    python3 scripts/generate_recommender_app.py --check

    # Custom output directory
    python3 scripts/generate_recommender_app.py --output dist/splunk-apps
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# P6 (scripts taxonomy, 2026-05-10) relocated this generator from
# scripts/generate_recommender_app.py to
# src/splunk_uc/generators/recommender_app.py. parents[3] resolves:
# recommender_app.py -> generators/ -> splunk_uc/ -> src/ -> repo root.
# The legacy ``parent.parent`` chain assumed a one-level depth and is
# now wrong by three. The legacy shim at scripts/generate_recommender_app.py
# re-exports ``main`` so existing CI/Makefile callers still work.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VERSION_FILE = REPO_ROOT / "VERSION"
LICENSE_FILE = REPO_ROOT / "LICENSE"
DEFAULT_OUTPUT = REPO_ROOT / "splunk-apps"
CONTENT_DIR = REPO_ROOT / "content"
DATA_DIR = REPO_ROOT / "data"
REGULATIONS_FILE = DATA_DIR / "regulations.json"
SPLUNKBASE_CATALOG_FILE = DATA_DIR / "splunkbase-catalog.json"
SPLUNKBASE_OVERRIDES_FILE = DATA_DIR / "splunkbase-catalog-overrides.json"

PRIMARY_APP_ID = "splunk-uc-recommender"
API_BASE_URL = "https://fenre.github.io/splunk-monitoring-use-cases/api/v1"


# ---------------------------------------------------------------------------
# Inlined compliance/UC helpers (formerly imported from generate_splunk_app.py
# which was retired in v9.0). Kept name-stable internally so callers below
# still read as ``_gsa_*``.
# ---------------------------------------------------------------------------


def _gsa_load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _gsa_uc_sort_key(uc: Mapping[str, Any]) -> tuple[int, ...]:
    uid = uc.get("id") or ""
    try:
        return tuple(int(part) for part in str(uid).split("."))
    except ValueError:  # pragma: no cover - malformed IDs
        return (9_999,)


def _gsa_load_ucs() -> list[dict[str, Any]]:
    seen_ids: set = set()
    items: list[dict[str, Any]] = []

    def _ingest(root: pathlib.Path, glob: str) -> None:
        if not root.exists():
            return
        for path in sorted(root.rglob(glob)):
            try:
                data = _gsa_load_json(path)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
            if not isinstance(data, dict) or not data.get("id"):
                continue
            uid = data["id"]
            if uid in seen_ids:
                continue
            seen_ids.add(uid)
            data["_sourcePath"] = str(path.relative_to(REPO_ROOT))
            items.append(data)

    _ingest(CONTENT_DIR, "UC-*.json")
    items.sort(key=_gsa_uc_sort_key)
    return items


def _gsa_alias_map(regs: Mapping[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for fw in regs.get("frameworks", []):
        fid = fw.get("id")
        if not fid:
            continue
        out[fid.lower()] = fid
        short = fw.get("shortName")
        if short:
            out[short.lower()] = fid
        for alias in fw.get("aliases", []) or []:
            out[str(alias).lower()] = fid
    for alias, target in (regs.get("aliasIndex") or {}).items():
        if alias.startswith("$"):
            continue
        out[str(alias).lower()] = str(target)
    return out


def _gsa_framework_by_id(regs: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {fw["id"]: fw for fw in regs.get("frameworks", []) if fw.get("id")}


_SAFE_STANZA_RE = re.compile(r"[\[\]\n\r]")


def _gsa_safe_stanza(name: str) -> str:
    return _SAFE_STANZA_RE.sub(" ", name).strip()


# Backwards-compatible alias used by call sites below.
_GSA_REGULATIONS_FILE = REGULATIONS_FILE

GENERATED_CONF_BANNER = (
    "# -----------------------------------------------------------------\n"
    "# GENERATED by scripts/generate_recommender_app.py — DO NOT EDIT.\n"
    "# Source of truth: scripts/generate_recommender_app.py.\n"
    "# Re-run `python3 scripts/generate_recommender_app.py` after edits.\n"
    "# -----------------------------------------------------------------\n"
)
GENERATED_XML_BANNER = "<!-- GENERATED by scripts/generate_recommender_app.py — DO NOT EDIT. -->"
GENERATED_JS_BANNER = (
    "/* GENERATED by scripts/generate_recommender_app.py — DO NOT EDIT.   */\n"
    "/* Source of truth: scripts/generate_recommender_app.py.              */\n"
    "/* Re-run `python3 scripts/generate_recommender_app.py` after edits.  */\n"
)
GENERATED_CSS_BANNER = "/* GENERATED by scripts/generate_recommender_app.py — DO NOT EDIT. */\n"


# ---------------------------------------------------------------------------
# I/O helpers (deterministic writers, mirrors generate_splunk_app.py)
# ---------------------------------------------------------------------------


def _deterministic_timestamp() -> str:
    """Return a reproducible UTC timestamp for every generated artifact."""
    env = os.environ.get("SOURCE_DATE_EPOCH")
    if env:
        try:
            return (
                datetime.fromtimestamp(int(env), tz=UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
        except ValueError:  # pragma: no cover - defensive
            pass
    try:  # pragma: no cover - thin wrapper over git
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", "-1", "--format=%ct"],
            capture_output=True,
            text=True,
            check=True,
        )
        ts = int(out.stdout.strip())
        return (
            datetime.fromtimestamp(ts, tz=UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_version() -> str:
    """Return the catalogue version padded to SemVer (``6.0`` → ``6.0.0``)."""
    if not VERSION_FILE.exists():
        return "0.0.0"
    raw = VERSION_FILE.read_text().strip()
    if not raw:
        return "0.0.0"
    parts = raw.split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts[:3])


def _write_text(path: pathlib.Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not body.endswith("\n"):
        body += "\n"
    path.write_text(body, encoding="utf-8", newline="\n")


def _write_json(path: pathlib.Path, obj: Any) -> None:
    body = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)
    _write_text(path, body)


def _render_conf(
    banner: str,
    sections: Sequence[tuple[str, Sequence[tuple[str, str]]]],
) -> str:
    """Serialise ``[(stanza, [(k, v), …]), …]`` into a deterministic .conf body.

    Stanza ordering is left to the caller so we can keep the
    "install, ui, launcher, package" order in ``app.conf`` without
    accidentally re-sorting.
    """
    buf = io.StringIO()
    buf.write(banner)
    buf.write("\n")
    for i, (stanza, pairs) in enumerate(sections):
        if i:
            buf.write("\n")
        buf.write(f"[{stanza}]\n")
        for key, value in pairs:
            buf.write(f"{key} = {value}\n")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# default/app.conf
# ---------------------------------------------------------------------------


def _primary_app_conf(version: str) -> str:
    description = (
        "Scans the local Splunk environment for sourcetypes, indexes, "
        "CIM acceleration, and installed apps, then previews matching "
        "monitoring use cases from the Splunk Monitoring Use Cases "
        "catalogue (fenre/splunk-monitoring-use-cases). Preview-only: "
        "saved searches are never written to the instance."
    )
    # AppInspect's ``check_app_conf_id_matches_app_directory_name``
    # wants an explicit ``[id]`` stanza on top of ``[package]``.
    # Splunk Cloud admission has rejected manifest-only apps in the
    # past — keep both as a belt-and-braces measure.
    sections = [
        (
            "install",
            [
                ("is_configured", "0"),
                ("state", "enabled"),
                ("build", "14"),
            ],
        ),
        (
            "id",
            [
                ("name", PRIMARY_APP_ID),
                ("version", version),
                ("build", "14"),
            ],
        ),
        (
            "ui",
            [
                ("is_visible", "true"),
                ("label", "Splunk UC Recommender"),
            ],
        ),
        (
            "launcher",
            [
                ("author", "Splunk Monitoring Use Cases contributors"),
                ("description", description),
                ("version", version),
            ],
        ),
        (
            "package",
            [
                ("id", PRIMARY_APP_ID),
                ("check_for_updates", "false"),
            ],
        ),
    ]
    return _render_conf(GENERATED_CONF_BANNER, sections)


# ---------------------------------------------------------------------------
# default/savedsearches.conf
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Compliance bundle (UC saved searches + macros + tags + lookup)
#
# Every UC that cites at least one tier-1 regulation is folded into the
# unified recommender app so operators install ONE app and get every
# compliance content pack in a single place.  Each saved search ships
# ``disabled = 1`` / ``is_scheduled = 0`` so nothing schedules until an
# operator reviews the SPL and points it at the right index(es).
#
# A UC tagged against multiple regulations produces ONE saved search with
# all its regulation/clause metadata serialised into the description and
# action.* keys; the lookup CSV preserves the per-clause grain.
# ---------------------------------------------------------------------------


_SEVERITY_BY_CRITICALITY: Mapping[str, str] = {
    "critical": "5",
    "high": "4",
    "medium": "3",
    "low": "2",
    "informational": "1",
}


def _load_compliance_bundle() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return ``(ucs, frameworks_by_id)`` for tier-1 regulations.

    Each returned UC is annotated with ``_matchedCompliance``: the list of
    compliance entries that resolve to a tier-1 framework.  UCs without any
    tier-1 match are dropped so the bundle stays focused on the regulations
    operators actually deploy from this repo.
    """
    regs = _gsa_load_json(_GSA_REGULATIONS_FILE)
    alias_map = _gsa_alias_map(regs)
    by_id = _gsa_framework_by_id(regs)
    tier1 = {fid for fid, fw in by_id.items() if (fw.get("tier") or 99) == 1}

    ucs = _gsa_load_ucs()
    matched: list[dict[str, Any]] = []
    for uc in ucs:
        entries = []
        for entry in uc.get("compliance") or []:
            raw = str(entry.get("regulation") or "").strip()
            if not raw:
                continue
            canonical = alias_map.get(raw.lower())
            if canonical and canonical in tier1:
                normalised = dict(entry)
                normalised["_canonical"] = canonical
                entries.append(normalised)
        if entries:
            uc_copy = dict(uc)
            uc_copy["_matchedCompliance"] = entries
            matched.append(uc_copy)
    matched.sort(key=_gsa_uc_sort_key)
    return matched, {fid: by_id[fid] for fid in sorted(tier1) if fid in by_id}


def _uc_to_unified_savedsearch(
    uc: Mapping[str, Any],
    frameworks: Mapping[str, Mapping[str, Any]],
) -> tuple[str, list[tuple[str, str]]]:
    """Render one UC stanza tagged with every tier-1 regulation it satisfies."""
    uc_id = uc.get("id") or ""
    title = uc.get("title") or uc.get("name") or f"UC-{uc_id}"
    stanza = _gsa_safe_stanza(f"UC-{uc_id} — {title}")[:1024]

    matched = uc.get("_matchedCompliance") or []
    regulations: list[str] = sorted(
        {str(e.get("_canonical")) for e in matched if e.get("_canonical")}
    )
    clauses: list[str] = sorted(
        {str(e.get("clause") or "").strip() for e in matched if e.get("clause")}
    )
    version_tags: list[str] = sorted(
        {
            f"{e.get('_canonical')}@{e.get('version') or 'unversioned'}"
            for e in matched
            if e.get("_canonical")
        }
    )

    criticality = (uc.get("criticality") or "medium").lower()
    severity = _SEVERITY_BY_CRITICALITY.get(criticality, "3")

    reg_labels = [(frameworks.get(r, {}).get("shortName") or r.upper()) for r in regulations]
    description_lines: list[str] = [
        title,
        f"UC {uc_id} | regulations={','.join(reg_labels)} | criticality={criticality}",
    ]
    if clauses:
        description_lines.append(f"clauses={'; '.join(clauses)}")
    description_lines.append(
        "Bundled by splunk-uc-recommender. Disabled by default — review SPL "
        "and adjust index= filters before enabling."
    )
    description = " | ".join(description_lines)

    spl_text = (uc.get("spl") or uc.get("query") or "").strip()
    if not spl_text:
        spl_text = (
            "index=* earliest=-15m latest=now "
            "| eval _placeholder=1 "
            "| stats count "
            f'| eval uc_id="{uc_id}"'
        )
    spl_lines = [line.rstrip() for line in spl_text.splitlines() if line.strip()]
    if len(spl_lines) == 1:
        search_value = spl_lines[0]
    else:
        search_value = " \\\n".join(spl_lines)

    pairs: list[tuple[str, str]] = [
        ("description", description),
        ("search", search_value),
        ("cron_schedule", "*/15 * * * *"),
        ("dispatch.earliest_time", "-30m@m"),
        ("dispatch.latest_time", "now"),
        ("enableSched", "0"),
        ("is_scheduled", "0"),
        ("disabled", "1"),
        ("alert.severity", severity),
        ("alert_condition", "search count > 0"),
        ("alert.track", "1"),
        ("alert.suppress", "0"),
        ("action.email", "0"),
        ("action.logevent", "0"),
        ("action.uc_compliance.param.uc_id", uc_id),
        ("action.uc_compliance.param.regulations", ",".join(regulations)),
    ]
    if clauses:
        pairs.append(("action.uc_compliance.param.clauses", ",".join(clauses)))
    if version_tags:
        pairs.append(("action.uc_compliance.param.versions", ",".join(version_tags)))
    return stanza, pairs


def _compliance_savedsearches_sections(
    ucs: Sequence[Mapping[str, Any]],
    frameworks: Mapping[str, Mapping[str, Any]],
) -> list[tuple[str, list[tuple[str, str]]]]:
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    for uc in ucs:
        sections.append(_uc_to_unified_savedsearch(uc, frameworks))
    sections.sort(key=lambda s: s[0])
    return sections


def _compliance_eventtypes_sections(
    ucs: Sequence[Mapping[str, Any]],
    frameworks: Mapping[str, Mapping[str, Any]],
) -> list[tuple[str, list[tuple[str, str]]]]:
    """One eventtype per (regulation, controlFamily) for routing/searches.

    The eventtype is a navigation/routing marker referenced by the
    ``uc_compliance_<fw>`` macros and tagged in ``tags.conf`` — it does
    not have a live event surface of its own (the bundled compliance
    saved searches ship disabled-by-default and don't write summary
    events). The ``search`` clause is therefore intentionally a
    sourcetype-scoped placeholder that:

    * parses cleanly so Splunk does not emit a ``[mink]`` warning at
      conf-load (a previous build used ``tag::uc_compliance_regulation=
      "<fw>"`` which referenced a tag that ``tags.conf`` does not
      define on the ``uc_compliance_regulation`` field — Splunk
      validated the eventtype search and warned ``The tag '<fw>' does
      not exist or is deactivated on uc_compliance_regulation``);
    * does not accidentally match unrelated production data;
    * survives if an operator later starts logging the bundled saved
      searches to a summary index with that sourcetype.

    The human-readable description (covered UC IDs etc.) lives in the
    proper ``description`` attribute, not concatenated into ``search``
    where it was previously parsed as a ``eventtype_description="..."``
    field clause that never matches.
    """
    by_key: dict[tuple[str, str], list[str]] = {}
    for uc in ucs:
        family = (uc.get("controlFamily") or "uncategorised").strip() or "uncategorised"
        for entry in uc.get("_matchedCompliance") or []:
            fw_id = str(entry.get("_canonical") or "").strip()
            if not fw_id:
                continue
            by_key.setdefault((fw_id, family), []).append(uc.get("id") or "")
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    for fw_id, family in sorted(by_key):
        ids = sorted(set(by_key[(fw_id, family)]))
        safe_family = re.sub(r"[^A-Za-z0-9]+", "_", family).strip("_").lower() or "uncategorised"
        stanza = f"uc_compliance_{fw_id}_{safe_family}"
        description = (
            f"{fw_id} — {family} (covers UC {', '.join(ids[:5])}{'…' if len(ids) > 5 else ''})"
        )
        search = f'sourcetype="uc_compliance::{fw_id}::{safe_family}"'
        sections.append(
            (
                stanza,
                [
                    ("description", description),
                    ("search", search),
                    ("priority", "10"),
                    ("disabled", "0"),
                ],
            )
        )
    return sections


def _compliance_macros_sections(
    frameworks: Mapping[str, Mapping[str, Any]],
) -> list[tuple[str, list[tuple[str, str]]]]:
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "uc_compliance_window(1)",
            [
                ("args", "lookback"),
                ("definition", "earliest=-$lookback$@m latest=now"),
                ("iseval", "0"),
                (
                    "description",
                    (
                        "Parameterised lookback shared by every bundled compliance UC. "
                        "`uc_compliance_window(30m)` → `earliest=-30m@m latest=now`."
                    ),
                ),
            ],
        ),
    ]
    for fw_id in sorted(frameworks):
        sections.append(
            (
                f"uc_compliance_{fw_id}",
                [
                    ("definition", f'eventtype="uc_compliance_{fw_id}_uncategorised"'),
                    ("iseval", "0"),
                    (
                        "description",
                        (
                            f"Convenience macro: expands to the catch-all eventtype "
                            f"for the {fw_id.upper()} content. Override to chain with "
                            f"your own filters."
                        ),
                    ),
                ],
            )
        )
    return sections


def _compliance_tags_sections(
    frameworks: Mapping[str, Mapping[str, Any]],
) -> list[tuple[str, list[tuple[str, str]]]]:
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    for fw_id in sorted(frameworks):
        sections.append(
            (
                f"eventtype=uc_compliance_{fw_id}_uncategorised",
                [
                    ("uc_compliance_regulation", "enabled"),
                    (f"uc_compliance_framework_{fw_id}", "enabled"),
                ],
            )
        )
    return sections


def _compliance_lookup_csv(ucs: Sequence[Mapping[str, Any]]) -> str:
    """One CSV row per (UC, compliance entry) — preserves the per-clause grain."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "uc_id",
            "title",
            "criticality",
            "regulation",
            "regulation_version",
            "clause",
            "clause_url",
            "assurance",
            "mode",
            "source_path",
        ]
    )
    rows: list[tuple[str, ...]] = []
    for uc in ucs:
        uc_id = uc.get("id") or ""
        title = (uc.get("title") or "").replace("\n", " ")
        criticality = uc.get("criticality") or ""
        source_path = uc.get("_sourcePath") or ""
        for entry in uc.get("_matchedCompliance") or []:
            rows.append(
                (
                    uc_id,
                    title,
                    criticality,
                    str(entry.get("_canonical") or entry.get("regulation") or ""),
                    str(entry.get("version") or ""),
                    str(entry.get("clause") or ""),
                    str(entry.get("clauseUrl") or ""),
                    str(entry.get("assurance") or ""),
                    str(entry.get("mode") or ""),
                    source_path,
                )
            )
    rows.sort()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def _savedsearches_conf() -> str:
    """Four Cloud-safe scan searches populate the KV store inventory.

    Each scan reads the current inventory, filters out rows of its own
    ``type``, appends fresh rows, and writes back. This avoids the
    race-condition of plain ``outputlookup append=false`` which would
    wipe every other scan's slice on every run.

    The same conf also bundles every tier-1 compliance UC (deduped by UC
    id) so operators can enable per-regulation searches from the same app
    that recommends them.  Compliance stanzas always ship
    ``disabled = 1`` / ``is_scheduled = 0``.
    """
    # Sourcetype inventory — frequent and cheap
    sourcetype_spl = (
        "| inputlookup uc_recommender_inventory "
        '| where type!="sourcetype" '
        "| append [ "
        "| metadata type=sourcetypes index=* "
        '| eval type="sourcetype", name=sourcetype, count=totalCount, '
        'firstSeen=strftime(firstTime,"%Y-%m-%dT%H:%M:%SZ"), '
        'lastSeen=strftime(lastTime,"%Y-%m-%dT%H:%M:%SZ"), '
        'extras="", _key="sourcetype::" . sourcetype '
        "| table _key type name count firstSeen lastSeen extras "
        "] "
        "| outputlookup uc_recommender_inventory append=false"
    )
    # Index inventory — lighter than sourcetype scan
    index_spl = (
        "| inputlookup uc_recommender_inventory "
        '| where type!="index" '
        "| append [ "
        "| eventcount summarize=false index=* "
        "| stats sum(count) as count by index "
        '| eval type="index", name=index, '
        'firstSeen="", lastSeen=strftime(now(),"%Y-%m-%dT%H:%M:%SZ"), '
        'extras="", _key="index::" . index '
        "| table _key type name count firstSeen lastSeen extras "
        "] "
        "| outputlookup uc_recommender_inventory append=false"
    )
    # CIM acceleration probe — reads the public /services/data/models REST
    # endpoint and records which CIM models are currently accelerated.
    cim_spl = (
        "| inputlookup uc_recommender_inventory "
        '| where type!="cim_model" '
        "| append [ "
        "| rest splunk_server=local /services/data/models count=0 "
        '| search (eai:acl.app="Splunk_SA_CIM" OR eai:acl.app="SA-CIM") '
        '| eval type="cim_model", name=title, '
        "count=coalesce(tonumber('acceleration.size'), 0), "
        "firstSeen=coalesce('acceleration.earliest_time', \"\"), "
        "lastSeen=coalesce('acceleration.latest_time', \"\"), "
        "extras=if(tostring('acceleration.enabled')=\"1\", "
        '"accelerated", "not_accelerated"), '
        '_key="cim::" . name '
        "| table _key type name count firstSeen lastSeen extras "
        "] "
        "| outputlookup uc_recommender_inventory append=false"
    )
    # Installed apps — once per day; uses /services/apps/local.
    #
    # Build 11 changes:
    #   * ``name``   -> human-readable label (falls back to folder
    #                   title) so the Scan tab tile reads
    #                   ``Splunk Common Information Model Add-on``
    #                   rather than ``Splunk_SA_CIM``.
    #   * ``extras`` -> the folder ``title`` (e.g. ``Splunk_TA_nix``).
    #                   This is the matcher's high-confidence signal:
    #                   the upstream app-index has many keys derived
    #                   from sidecar backticks (``Splunk_TA_nix``,
    #                   ``Splunk_SA_CIM``, ...) which won't match the
    #                   user-facing label but DO exact-match the
    #                   folder. Build 9/10 stored ``version`` here
    #                   instead, which the matcher couldn't use AND
    #                   wasn't surfaced anywhere users looked.
    apps_spl = (
        "| inputlookup uc_recommender_inventory "
        '| where type!="app" '
        "| append [ "
        "| rest splunk_server=local /services/apps/local count=0 "
        "| where disabled=0 "
        '| eval type="app", name=coalesce(label, title), '
        "count=1, "
        'firstSeen="", '
        'lastSeen=strftime(now(),"%Y-%m-%dT%H:%M:%SZ"), '
        "extras=coalesce(title, label), "
        '_key="app::" . coalesce(title, label) '
        "| table _key type name count firstSeen lastSeen extras "
        "] "
        "| outputlookup uc_recommender_inventory append=false"
    )
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "Recommender — Sourcetype inventory",
            [
                (
                    "description",
                    "Inventories active sourcetypes and writes them to the uc_recommender_inventory KV store. Low-cost: uses | metadata type=sourcetypes index=*.",
                ),
                ("search", sourcetype_spl),
                ("cron_schedule", "*/30 * * * *"),
                ("dispatch.earliest_time", "-1d@d"),
                ("dispatch.latest_time", "now"),
                ("enableSched", "1"),
                ("is_scheduled", "1"),
                ("disabled", "0"),
                ("alert.track", "0"),
                ("action.email", "0"),
                ("action.logevent", "0"),
            ],
        ),
        (
            "Recommender — Index inventory",
            [
                (
                    "description",
                    "Inventories active indexes via | eventcount. Runs every 30 minutes; cheaper than metadata when many sourcetypes share indexes.",
                ),
                ("search", index_spl),
                ("cron_schedule", "*/30 * * * *"),
                ("dispatch.earliest_time", "-1d@d"),
                ("dispatch.latest_time", "now"),
                ("enableSched", "1"),
                ("is_scheduled", "1"),
                ("disabled", "0"),
                ("alert.track", "0"),
                ("action.email", "0"),
                ("action.logevent", "0"),
            ],
        ),
        (
            "Recommender — CIM acceleration probe",
            [
                (
                    "description",
                    "Records acceleration status of every CIM data model via the REST API (/services/data/models). Drives the CIM-based recommendation signal.",
                ),
                ("search", cim_spl),
                ("cron_schedule", "0 * * * *"),
                ("dispatch.earliest_time", "-15m@m"),
                ("dispatch.latest_time", "now"),
                ("enableSched", "1"),
                ("is_scheduled", "1"),
                ("disabled", "0"),
                ("alert.track", "0"),
                ("action.email", "0"),
                ("action.logevent", "0"),
            ],
        ),
        (
            "Recommender — Installed apps",
            [
                (
                    "description",
                    "Records installed/enabled apps via /services/apps/local so the recommender can match UC.app and UC.premiumApps against what's actually on the search head.",
                ),
                ("search", apps_spl),
                ("cron_schedule", "13 3 * * *"),
                ("dispatch.earliest_time", "-1d@d"),
                ("dispatch.latest_time", "now"),
                ("enableSched", "1"),
                ("is_scheduled", "1"),
                ("disabled", "0"),
                ("alert.track", "0"),
                ("action.email", "0"),
                ("action.logevent", "0"),
            ],
        ),
    ]
    sections.extend(_implementation_tracking_savedsearches())
    compliance_ucs, frameworks = _load_compliance_bundle()
    sections.extend(_compliance_savedsearches_sections(compliance_ucs, frameworks))
    return _render_conf(GENERATED_CONF_BANNER, sections)


def _implementation_tracking_savedsearches() -> list[tuple[str, list[tuple[str, str]]]]:
    """Four v9.0 saved searches — fingerprint scan, drift, audit, retention.

    All four follow the v9.0 productionisation guards:

    * ``dispatch.max_count = 50000`` and ``dispatch.max_time = 600`` to
      cap runaway searches (per § 12c).
    * Off-peak cron offsets so they don't pile up against the existing
      sourcetype/index/CIM/apps inventory scans.
    * No outbound HTTP — every dependency is an in-app lookup
      (``uc_fingerprints.csv``) or KV collection
      (``uc_recommender_implementations`` / ``uc_recommender_audit``).

    The fingerprint scan is the auto-detect side of the hybrid
    implementation-tracking pattern (§ 6a). It joins canonicalised
    SPL hashes from the local saved-search registry against
    ``lookups/uc_fingerprints.csv`` (shipped in-app — never HTTP-fetched
    at runtime, see ``tools/build/render_api.py`` and
    ``scripts/generate_recommender_app.py``).
    """
    fingerprint_spl = (
        "| rest /services/saved/searches splunk_server=local "
        "| eval fingerprint=sha256(tostring(uc_normalise(search))) "
        "| inputlookup append=t uc_fingerprints "
        "| stats values(uc_id) AS matched_uc_id "
        "values(title) AS evidence_search_name BY fingerprint "
        "| where isnotnull(matched_uc_id) AND isnotnull(evidence_search_name) "
        '| eval _key=matched_uc_id, status="implemented", '
        'detection_source="auto-fingerprint", '
        "evidence_first_seen_at=coalesce(evidence_first_seen_at, "
        'strftime(now(),"%Y-%m-%dT%H:%M:%S%z")), '
        'evidence_last_seen_at=strftime(now(),"%Y-%m-%dT%H:%M:%S%z") '
        "| outputlookup uc_recommender_implementations append=t key_field=_key"
    )
    drift_spl = (
        "| inputlookup uc_recommender_implementations "
        '| where status="implemented" '
        "| eval seconds_absent=now() - strptime(evidence_last_seen_at, "
        '"%Y-%m-%dT%H:%M:%S%z") '
        "| where seconds_absent > 86400 "
        '| eval status="needs_review", '
        'detection_source="auto-drift", '
        'marked_at=strftime(now(),"%Y-%m-%dT%H:%M:%S%z") '
        "| outputlookup uc_recommender_implementations append=t key_field=_key"
    )
    audit_append_spl = (
        "| inputlookup uc_recommender_implementations "
        "| eval kv_seen=1 "
        "| inputlookup append=t uc_recommender_implementations_prev "
        "| stats values(status) AS statuses, values(uc_id) AS uc_ids, "
        "values(marked_by) AS users BY _key "
        "| where mvcount(statuses)=2 "
        "| eval old_status=mvindex(statuses,0), "
        "new_status=mvindex(statuses,1), "
        "uc_id=mvindex(uc_ids,0), "
        'user=coalesce(mvindex(users,0), "system"), '
        'timestamp=strftime(now(),"%Y-%m-%dT%H:%M:%S%z"), '
        "request_id=md5(_key . tostring(now())) "
        "| where old_status!=new_status "
        "| table uc_id user old_status new_status timestamp request_id "
        "| outputlookup uc_recommender_audit append=t "
    )
    audit_retention_spl = (
        "| inputlookup uc_recommender_audit "
        "| eval retain=if((now() - strptime(timestamp, "
        '"%Y-%m-%dT%H:%M:%S%z")) < 13*30*86400, 1, 0) '
        "| where retain=1 "
        "| fields - retain "
        "| outputlookup uc_recommender_audit append=f"
    )
    common_caps: list[tuple[str, str]] = [
        ("dispatch.max_count", "50000"),
        ("dispatch.max_time", "600"),
        ("enableSched", "1"),
        ("is_scheduled", "1"),
        ("disabled", "0"),
        ("alert.track", "0"),
        ("action.email", "0"),
        ("action.logevent", "0"),
    ]
    return [
        (
            "Recommender — Saved-search fingerprint",
            [
                (
                    "description",
                    "Auto-detect side of v9.0 hybrid implementation tracking. Joins SHA-256 fingerprints of canonicalised local saved-search SPL against the shipped lookups/uc_fingerprints.csv. Runs every 6 hours; updates evidence_last_seen_at for matches. Cloud-safe: no HTTP egress, fingerprints ship in-app.",
                ),
                ("search", fingerprint_spl),
                ("cron_schedule", "17 */6 * * *"),
                ("dispatch.earliest_time", "-1d@d"),
                ("dispatch.latest_time", "now"),
                *common_caps,
            ],
        ),
        (
            "Recommender — Drift detection",
            [
                (
                    "description",
                    "Re-flags implementations with evidence_last_seen_at older than 24h to needs_review. Time-window check (not point-in-time disable) defeats mass-flip via search disable+re-enable.",
                ),
                ("search", drift_spl),
                ("cron_schedule", "37 4 * * *"),
                ("dispatch.earliest_time", "-2d@d"),
                ("dispatch.latest_time", "now"),
                *common_caps,
            ],
        ),
        (
            "Recommender — Audit append",
            [
                (
                    "description",
                    "Diffs uc_recommender_implementations against the previous snapshot every 5 minutes and writes one audit row per detected change for the fast-path (JS-only) writes. Destructive transitions write atomically through the saved-search-wrapper, so this 5-min cadence covers only non-destructive transitions (in_progress, implemented).",
                ),
                ("search", audit_append_spl),
                ("cron_schedule", "*/5 * * * *"),
                ("dispatch.earliest_time", "-15m@m"),
                ("dispatch.latest_time", "now"),
                *common_caps,
            ],
        ),
        (
            "Recommender — Audit retention",
            [
                (
                    "description",
                    "Default 13-month retention on uc_recommender_audit (privacy hygiene per codeguard-0-privacy-data-protection). Operators can disable this saved search if local compliance mandates longer retention.",
                ),
                ("search", audit_retention_spl),
                ("cron_schedule", "47 5 * * *"),
                ("dispatch.earliest_time", "-1d@d"),
                ("dispatch.latest_time", "now"),
                *common_caps,
            ],
        ),
        (
            "uc_implementation_decommission",
            [
                (
                    "description",
                    "Saved-search wrapper for destructive transition (anything -> decommissioned). Server-side validates uc_id, reason, user; writes the implementations row and the audit row atomically via append/outputlookup. Dispatched from recommender.js with $uc_id$/$reason$/$user$/$request_id$ tokens; only callable by users holding edit_uc_implementations.",
                ),
                (
                    "search",
                    '| makeresults | eval uc_id="$uc_id$", reason="$reason$", '
                    'user="$user$", request_id="$request_id$" '
                    '| where match(uc_id, "^\\d+\\.\\d+\\.\\d+$") '
                    "AND len(reason) > 0 AND len(reason) <= 2000 "
                    'AND match(reason, "^[^\\r\\n]*$") '
                    '| eval _key=uc_id, status="decommissioned", '
                    "marked_by=user, "
                    'marked_at=strftime(now(),"%Y-%m-%dT%H:%M:%S%z"), '
                    'detection_source="manual", notes=reason '
                    "| outputlookup uc_recommender_implementations "
                    "append=t key_field=_key "
                    "| append [ "
                    '| makeresults | eval uc_id="$uc_id$", '
                    'user="$user$", '
                    'old_status="implemented", '
                    'new_status="decommissioned", '
                    'timestamp=strftime(now(),"%Y-%m-%dT%H:%M:%S%z"), '
                    'request_id="$request_id$" '
                    "| outputlookup uc_recommender_audit append=t "
                    "]",
                ),
                ("dispatchAs", "user"),
                ("disabled", "1"),
                ("is_scheduled", "0"),
                ("alert.track", "0"),
                ("action.email", "0"),
                ("action.logevent", "0"),
                ("dispatch.max_count", "50000"),
                ("dispatch.max_time", "120"),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# default/collections.conf
# ---------------------------------------------------------------------------


def _collections_conf() -> str:
    # ``replicate = true`` is mandatory on the new v9.0 collections so SHC
    # members converge after every KV write. ``accelerated_fields`` are
    # plain JSON specs Splunk can lift into MongoDB-style indexes — they
    # turn the per-UC implementation lookup from O(7,364) full-scan into
    # O(log N) on every dashboard render. ``_key`` is implicit and never
    # declared.
    sections = [
        (
            "uc_recommender_inventory",
            [
                ("enforceTypes", "false"),
                (
                    "field.type",
                    "string",
                ),
                ("field.name", "string"),
                ("field.count", "number"),
                ("field.firstSeen", "string"),
                ("field.lastSeen", "string"),
                ("field.extras", "string"),
                ("accelerated_fields.idx_type_name", '{"type": 1, "name": 1}'),
            ],
        ),
        (
            "uc_recommender_scan_runs",
            [
                ("enforceTypes", "false"),
                ("field.scan_type", "string"),
                ("field.run_at", "string"),
                ("field.run_by", "string"),
            ],
        ),
        (
            "uc_recommender_implementations",
            [
                ("enforceTypes", "false"),
                ("replicate", "true"),
                ("field.uc_id", "string"),
                ("field.status", "string"),
                ("field.detection_source", "string"),
                ("field.marked_by", "string"),
                ("field.marked_at", "string"),
                ("field.notes", "string"),
                ("field.evidence_search_name", "string"),
                ("field.evidence_first_seen_at", "string"),
                ("field.evidence_last_seen_at", "string"),
                ("field.required_tas_missing", "string"),
                ("accelerated_fields.uc_id_idx", '{"uc_id": 1}'),
                (
                    "accelerated_fields.status_idx",
                    '{"status": 1, "uc_id": 1}',
                ),
            ],
        ),
        (
            "uc_recommender_audit",
            [
                ("enforceTypes", "false"),
                ("replicate", "true"),
                ("field.uc_id", "string"),
                ("field.user", "string"),
                ("field.old_status", "string"),
                ("field.new_status", "string"),
                ("field.timestamp", "string"),
                ("field.request_id", "string"),
                ("field.notes", "string"),
                ("accelerated_fields.uc_id_idx", '{"uc_id": 1}'),
                ("accelerated_fields.timestamp_idx", '{"timestamp": 1}'),
            ],
        ),
    ]
    return _render_conf(GENERATED_CONF_BANNER, sections)


# ---------------------------------------------------------------------------
# default/transforms.conf
# ---------------------------------------------------------------------------


def _transforms_conf() -> str:
    sections = [
        (
            "uc_recommender_inventory",
            [
                ("external_type", "kvstore"),
                ("collection", "uc_recommender_inventory"),
                (
                    "fields_list",
                    "_key, type, name, count, firstSeen, lastSeen, extras",
                ),
            ],
        ),
        (
            "uc_recommender_scan_runs",
            [
                ("external_type", "kvstore"),
                ("collection", "uc_recommender_scan_runs"),
                ("fields_list", "_key, scan_type, run_at, run_by"),
            ],
        ),
        (
            "uc_recommender_implementations",
            [
                ("external_type", "kvstore"),
                ("collection", "uc_recommender_implementations"),
                (
                    "fields_list",
                    "_key, uc_id, status, detection_source, marked_by, "
                    "marked_at, notes, evidence_search_name, "
                    "evidence_first_seen_at, evidence_last_seen_at, "
                    "required_tas_missing",
                ),
            ],
        ),
        (
            "uc_recommender_audit",
            [
                ("external_type", "kvstore"),
                ("collection", "uc_recommender_audit"),
                (
                    "fields_list",
                    "_key, uc_id, user, old_status, new_status, timestamp, request_id, notes",
                ),
            ],
        ),
        (
            "uc_fingerprints",
            [
                ("filename", "uc_fingerprints.csv"),
                ("case_sensitive_match", "true"),
            ],
        ),
        (
            "uc_recommender_static",
            [
                ("filename", "uc_recommender_static.csv"),
                ("case_sensitive_match", "false"),
            ],
        ),
        (
            "uc_compliance_mappings",
            [
                ("filename", "uc_compliance_mappings.csv"),
                ("case_sensitive_match", "false"),
            ],
        ),
    ]
    return _render_conf(GENERATED_CONF_BANNER, sections)


# ---------------------------------------------------------------------------
# default/macros.conf
# ---------------------------------------------------------------------------


def _macros_conf() -> str:
    sections = [
        (
            "uc_recommender_inventory",
            [
                ("definition", "| inputlookup uc_recommender_inventory"),
                ("iseval", "0"),
                (
                    "description",
                    "Expands to the current inventory. Usage: `uc_recommender_inventory`.",
                ),
            ],
        ),
        (
            "uc_recommender_sourcetypes",
            [
                (
                    "definition",
                    '| inputlookup uc_recommender_inventory | where type="sourcetype"',
                ),
                ("iseval", "0"),
                (
                    "description",
                    "Convenience slice of the inventory restricted to sourcetypes.",
                ),
            ],
        ),
        (
            "uc_recommender_cim",
            [
                (
                    "definition",
                    '| inputlookup uc_recommender_inventory | where type="cim_model"',
                ),
                ("iseval", "0"),
                (
                    "description",
                    "Convenience slice of the inventory restricted to CIM models.",
                ),
            ],
        ),
        (
            "uc_recommender_fresh(1)",
            [
                ("args", "minutes"),
                (
                    "definition",
                    (
                        "| inputlookup uc_recommender_inventory "
                        '| eval _seen=strptime(lastSeen,"%Y-%m-%dT%H:%M:%SZ") '
                        '| where _seen > relative_time(now(), "-$minutes$m")'
                    ),
                ),
                ("iseval", "0"),
                (
                    "description",
                    "Inventory rows whose lastSeen timestamp is within the last `minutes` minutes.",
                ),
            ],
        ),
    ]
    _, frameworks = _load_compliance_bundle()
    sections.extend(_compliance_macros_sections(frameworks))
    return _render_conf(GENERATED_CONF_BANNER, sections)


# ---------------------------------------------------------------------------
# default/eventtypes.conf + tags.conf
# ---------------------------------------------------------------------------


def _eventtypes_conf() -> str:
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "uc_recommender_scan",
            [
                ("search", 'index=_internal sourcetype=splunkd_access "/uc_recommender/"'),
                ("priority", "10"),
                ("disabled", "0"),
            ],
        ),
    ]
    compliance_ucs, frameworks = _load_compliance_bundle()
    sections.extend(_compliance_eventtypes_sections(compliance_ucs, frameworks))
    return _render_conf(GENERATED_CONF_BANNER, sections)


def _tags_conf() -> str:
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "eventtype=uc_recommender_scan",
            [
                ("uc_recommender", "enabled"),
            ],
        ),
    ]
    _, frameworks = _load_compliance_bundle()
    sections.extend(_compliance_tags_sections(frameworks))
    return _render_conf(GENERATED_CONF_BANNER, sections)


# ---------------------------------------------------------------------------
# default/data/ui/nav/default.xml
# ---------------------------------------------------------------------------


def _nav_default_xml() -> str:
    # ``implementations`` slots between ``compliance`` and ``settings``
    # per the v9.0 plan §6d so operators land on the backlog view
    # without leaving the app's primary nav. (The Studio collection
    # that originally sat after ``implementations`` was retired in
    # build 4 — see the note above ``_recommend_studio_view_xml``'s
    # former location.)
    return (
        f"{GENERATED_XML_BANNER}\n"
        '<nav search_view="search" color="#65a637">\n'
        '  <view name="recommend" default="true" />\n'
        '  <view name="scan" />\n'
        '  <view name="browse" />\n'
        '  <view name="compliance" />\n'
        '  <view name="implementations" />\n'
        '  <view name="settings" />\n'
        '  <view name="search" />\n'
        "</nav>\n"
    )


# ---------------------------------------------------------------------------
# default/data/ui/views/*.xml — Simple XML dashboards
# ---------------------------------------------------------------------------


def _recommend_view_xml(api_base: str) -> str:
    return f"""{GENERATED_XML_BANNER}
<dashboard version="1.1" theme="light" script="js/recommender.js" stylesheet="css/recommender.css">
  <label>Recommend</label>
  <description>Match locally-detected data against the upstream use-case catalogue and preview ready-to-enable UCs.</description>
  <row>
    <panel>
      <single>
        <title>Sourcetypes detected</title>
        <search>
          <query>| inputlookup uc_recommender_inventory | where type="sourcetype" | stats dc(name) as v</query>
          <earliest>-15m</earliest>
          <latest>now</latest>
          <refresh>10m</refresh>
        </search>
        <option name="colorMode">block</option>
        <option name="drilldown">all</option>
        <option name="rangeColors">["0x6db7c6","0x65a637","0xf7bc38","0xf58f39","0xd93f3c"]</option>
      </single>
    </panel>
    <panel>
      <single>
        <title>CIM models accelerated</title>
        <search>
          <query>| inputlookup uc_recommender_inventory | where type="cim_model" AND extras="accelerated" | stats dc(name) as v</query>
          <earliest>-60m</earliest>
          <latest>now</latest>
          <refresh>10m</refresh>
        </search>
        <option name="colorMode">block</option>
        <option name="drilldown">all</option>
      </single>
    </panel>
    <panel>
      <single>
        <title>Apps detected</title>
        <search>
          <query>| inputlookup uc_recommender_inventory | where type="app" | stats dc(name) as v</query>
          <earliest>-1d</earliest>
          <latest>now</latest>
          <refresh>1h</refresh>
        </search>
        <option name="colorMode">block</option>
        <option name="drilldown">all</option>
      </single>
    </panel>
  </row>

  <row>
    <panel>
      <html>
        <div id="uc-recommender-root"
             data-api-base="{api_base}"
             data-app-name="{PRIMARY_APP_ID}">
          <p><em>Loading use-case recommendations…</em></p>
          <noscript>This page requires JavaScript to fetch the remote use-case catalogue. Use the <b>Scan</b> tab for a static view of your local inventory.</noscript>
        </div>
      </html>
    </panel>
  </row>
</dashboard>
"""


def _scan_view_xml() -> str:
    return f"""{GENERATED_XML_BANNER}
<dashboard version="1.1" theme="light">
  <label>Scan</label>
  <description>Raw inventory tables populated by the Recommender saved searches.</description>
  <row>
    <panel>
      <title>Sourcetype inventory</title>
      <table>
        <search>
          <query>| inputlookup uc_recommender_inventory | where type="sourcetype" | table name count firstSeen lastSeen | sort - count</query>
          <earliest>-15m</earliest>
          <latest>now</latest>
          <refresh>5m</refresh>
        </search>
        <option name="count">25</option>
        <option name="drilldown">row</option>
      </table>
    </panel>
  </row>
  <row>
    <panel>
      <title>Index inventory</title>
      <table>
        <search>
          <query>| inputlookup uc_recommender_inventory | where type="index" | table name count lastSeen | sort - count</query>
          <earliest>-15m</earliest>
          <latest>now</latest>
          <refresh>5m</refresh>
        </search>
        <option name="count">25</option>
      </table>
    </panel>
    <panel>
      <title>CIM model acceleration</title>
      <table>
        <search>
          <query>| inputlookup uc_recommender_inventory | where type="cim_model" | table name extras firstSeen lastSeen | sort name</query>
          <earliest>-60m</earliest>
          <latest>now</latest>
          <refresh>10m</refresh>
        </search>
        <option name="count">25</option>
      </table>
    </panel>
  </row>
  <row>
    <panel>
      <title>Installed apps</title>
      <table>
        <search>
          <query>| inputlookup uc_recommender_inventory | where type="app" | table name extras lastSeen | sort name</query>
          <earliest>-1d</earliest>
          <latest>now</latest>
          <refresh>1h</refresh>
        </search>
        <option name="count">50</option>
      </table>
    </panel>
  </row>
</dashboard>
"""


def _browse_view_xml(api_base: str) -> str:
    return f"""{GENERATED_XML_BANNER}
<dashboard version="1.1" theme="light" script="js/recommender.js" stylesheet="css/recommender.css">
  <label>Browse</label>
  <description>Browse the full use-case catalogue (all categories, 6k+ entries). Click a card to load the full sidecar.</description>
  <row>
    <panel>
      <html>
        <div id="uc-recommender-browse-root"
             data-api-base="{api_base}"
             data-app-name="{PRIMARY_APP_ID}"
             data-mode="browse">
          <p><em>Loading catalogue…</em></p>
        </div>
      </html>
    </panel>
  </row>
</dashboard>
"""


def _compliance_view_xml() -> str:
    """Filterable view over the bundled compliance UC saved searches.

    Reads from the same ``uc_compliance_mappings`` lookup that the saved
    searches reference, so operators can pick a regulation, see every UC
    that satisfies it, and click through to the saved search to enable.
    """
    return f"""{GENERATED_XML_BANNER}
<form version="1.1" theme="light" stylesheet="css/recommender.css">
  <label>Compliance</label>
  <description>Filter the bundled tier-1 compliance UCs by regulation, criticality, or clause. Every saved search is shipped disabled — open one in Search to review and enable it.</description>
  <fieldset autoRun="true" submitButton="false">
    <input type="dropdown" token="reg" searchWhenChanged="true">
      <label>Regulation</label>
      <choice value="*">All regulations</choice>
      <fieldForLabel>regulation</fieldForLabel>
      <fieldForValue>regulation</fieldForValue>
      <search>
        <query>| inputlookup uc_compliance_mappings | stats count by regulation | sort regulation</query>
        <earliest>-1m</earliest>
        <latest>now</latest>
      </search>
      <default>*</default>
    </input>
    <input type="dropdown" token="crit" searchWhenChanged="true">
      <label>Criticality</label>
      <choice value="*">All</choice>
      <choice value="critical">critical</choice>
      <choice value="high">high</choice>
      <choice value="medium">medium</choice>
      <choice value="low">low</choice>
      <choice value="informational">informational</choice>
      <default>*</default>
    </input>
    <input type="text" token="q" searchWhenChanged="true">
      <label>Title contains</label>
      <default>*</default>
    </input>
  </fieldset>
  <row>
    <panel>
      <title>UC count by regulation</title>
      <chart>
        <search>
          <query>| inputlookup uc_compliance_mappings | dedup uc_id regulation | stats dc(uc_id) as ucs by regulation | sort -ucs</query>
          <earliest>-1m</earliest>
          <latest>now</latest>
        </search>
        <option name="charting.chart">bar</option>
        <option name="charting.legend.placement">none</option>
        <option name="height">220</option>
      </chart>
    </panel>
    <panel>
      <title>UC count by criticality (filtered)</title>
      <chart>
        <search>
          <query>| inputlookup uc_compliance_mappings | search regulation="$reg$" criticality="$crit$" title="*$q$*" | dedup uc_id criticality | stats dc(uc_id) as ucs by criticality | sort -ucs</query>
          <earliest>-1m</earliest>
          <latest>now</latest>
        </search>
        <option name="charting.chart">pie</option>
        <option name="height">220</option>
      </chart>
    </panel>
  </row>
  <row>
    <panel>
      <title>Compliance use cases (filtered)</title>
      <table>
        <search>
          <query>| inputlookup uc_compliance_mappings | search regulation="$reg$" criticality="$crit$" title="*$q$*" | stats values(clause) as clauses, values(regulation) as regulations, first(criticality) as criticality, first(title) as title by uc_id | sort uc_id</query>
          <earliest>-1m</earliest>
          <latest>now</latest>
        </search>
        <option name="count">100</option>
        <option name="drilldown">cell</option>
        <drilldown>
          <link target="_blank">/app/{PRIMARY_APP_ID}/search?q=%7C%20rest%20%2Fservices%2Fsaved%2Fsearches%20%7C%20search%20title%3D%22UC-$row.uc_id$*%22%20%7C%20table%20title%2C%20disabled%2C%20cron_schedule%2C%20description</link>
        </drilldown>
      </table>
    </panel>
  </row>
</form>
"""


def _implementations_view_xml() -> str:
    """v9.0 ``Implementations`` dashboard.

    Top row: counts by status (Live / In Progress / Action Needed /
    Not Started / Decommissioned) as ``<single>`` panels.

    Filter row: status, criticality, and equipment slug — bound to URL
    tokens via Splunk's ``<form>`` mechanism so reload preserves the
    operator's choices (per § 12d).

    Body: the implementations KV joined client-side against the
    upstream ``uc-thin.json`` for titles + criticality. The recommender
    JS handles the join (``recommender.js`` at boot fetches both KV via
    ``inputlookup`` and the upstream API via fetch); the dashboard
    panels just render explicit empty-state copy when both sides are
    quiet.

    CSV export panel-action surfaces via the existing ``<form>`` token
    pattern (browser save dialog on a ``| outputcsv`` URL).
    """
    return f"""{GENERATED_XML_BANNER}
<form version="1.1" theme="light" script="js/recommender.js" stylesheet="css/recommender.css">
  <label>Implementations</label>
  <description>Track which use cases are Live, In Progress, or Action Needed. Filter the backlog and mark UCs as implemented from the Recommend dashboard.</description>
  <fieldset submitButton="false" autoRun="true">
    <input type="multiselect" token="status_filter" searchWhenChanged="true">
      <label>Status</label>
      <choice value="not_started">Not Started</choice>
      <choice value="in_progress">In Progress</choice>
      <choice value="implemented">Live</choice>
      <choice value="needs_review">Action Needed</choice>
      <choice value="decommissioned">Decommissioned</choice>
      <default>not_started,in_progress,implemented,needs_review</default>
      <!-- Token expands to: (status="x" OR status="y" OR ...). Joined
           with " OR " (not ",") because Splunk's `where` command — and
           inputlookup's inline filter syntax — both require boolean
           operators between predicates. The previous "," form produced
           "(status=x,status=y)" which inputlookup's parser rejects with
           "Invalid argument: '(status=x'", crashing the table panel
           with a 400. -->
      <delimiter> OR </delimiter>
      <prefix>(</prefix>
      <suffix>)</suffix>
      <valuePrefix>status="</valuePrefix>
      <valueSuffix>"</valueSuffix>
    </input>
    <input type="dropdown" token="criticality_filter" searchWhenChanged="true">
      <label>Criticality (any tier and above)</label>
      <choice value="*">Any</choice>
      <choice value="critical">Critical</choice>
      <choice value="high">High or above</choice>
      <choice value="medium">Medium or above</choice>
      <default>*</default>
    </input>
    <input type="text" token="equipment_filter" searchWhenChanged="true">
      <label>Equipment slug contains</label>
      <default></default>
    </input>
  </fieldset>
  <row>
    <panel>
      <single>
        <title>Live</title>
        <search>
          <query>| inputlookup uc_recommender_implementations | where status="implemented" | stats count as v</query>
          <earliest>-15m</earliest><latest>now</latest>
        </search>
        <option name="rangeColors">["0xa6c84b","0x53a051"]</option>
      </single>
    </panel>
    <panel>
      <single>
        <title>In Progress</title>
        <search>
          <query>| inputlookup uc_recommender_implementations | where status="in_progress" | stats count as v</query>
          <earliest>-15m</earliest><latest>now</latest>
        </search>
      </single>
    </panel>
    <panel>
      <single>
        <title>Action Needed</title>
        <search>
          <query>| inputlookup uc_recommender_implementations | where status="needs_review" | stats count as v</query>
          <earliest>-15m</earliest><latest>now</latest>
        </search>
        <option name="rangeColors">["0xdc4e41","0xdc4e41"]</option>
      </single>
    </panel>
    <panel>
      <single>
        <title>Not Started</title>
        <search>
          <query>| inputlookup uc_recommender_implementations | where status="not_started" | stats count as v</query>
          <earliest>-15m</earliest><latest>now</latest>
        </search>
      </single>
    </panel>
    <panel>
      <single>
        <title>Decommissioned</title>
        <search>
          <query>| inputlookup uc_recommender_implementations | where status="decommissioned" | stats count as v</query>
          <earliest>-15m</earliest><latest>now</latest>
        </search>
      </single>
    </panel>
  </row>
  <row>
    <panel>
      <html>
        <h3>Implementation backlog</h3>
        <p class="ucr-implementations-empty" data-status="loading">Loading backlog &#8230;</p>
        <div id="ucr-implementations-grid" class="ucr-implementations-grid" data-source="implementations" role="region" aria-live="polite">
          <p class="ucr-implementations-empty">No implementations tracked yet &#8212; head to <a href="recommend">Recommend</a> and click &quot;Mark as implemented&quot; on a UC card to start tracking.</p>
        </div>
      </html>
    </panel>
  </row>
  <row>
    <panel>
      <table>
        <title>Raw implementations KV (current filter)</title>
        <search>
          <query>| inputlookup uc_recommender_implementations | where $status_filter$ | table uc_id status detection_source marked_by marked_at notes evidence_search_name evidence_first_seen_at evidence_last_seen_at | sort uc_id</query>
          <earliest>-15m</earliest><latest>now</latest>
        </search>
        <option name="drilldown">cell</option>
        <option name="count">25</option>
        <drilldown>
          <link target="_blank">recommend?uc_id=$row.uc_id$</link>
        </drilldown>
        <option name="csvButton">true</option>
      </table>
    </panel>
  </row>
</form>
"""


def _settings_view_xml(api_base: str) -> str:
    return f"""{GENERATED_XML_BANNER}
<dashboard version="1.1" theme="light" script="js/recommender.js" stylesheet="css/recommender.css">
  <label>Settings</label>
  <description>Override the upstream catalogue URL, trigger a manual scan, and inspect the inventory KV store.</description>
  <row>
    <panel>
      <html>
        <div id="uc-recommender-settings-root"
             data-api-base="{api_base}"
             data-app-name="{PRIMARY_APP_ID}"
             data-mode="settings">
          <p><em>Loading settings…</em></p>
        </div>
      </html>
    </panel>
    <panel>
      <title>Recent scan runs</title>
      <table>
        <search>
          <query>| inputlookup uc_recommender_scan_runs | sort - run_at | head 20</query>
          <earliest>-7d@d</earliest>
          <latest>now</latest>
        </search>
        <option name="count">20</option>
      </table>
    </panel>
  </row>
</dashboard>
"""


# ---------------------------------------------------------------------------
# Dashboard Studio note: an earlier release shipped a
# ``recommend_studio.xml`` view that mirrored the Classic Recommend
# dashboard for tenants that have switched to Dashboard Studio. It was
# removed in build 4 because Studio's ``splunk.viz.html`` strips
# ``<script>`` tags for security, so the recommender card grid (status
# badges, Splunkbase install checklist, "Mark as implemented" modal) can
# never run inside a Studio dashboard. The lite "KPIs + go-elsewhere
# callout" replacement was just visual noise — operators are better
# served by the single Classic Recommend dashboard.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# appserver/static/js/*.js + css/*.css
# ---------------------------------------------------------------------------


def _js_recommender(api_base: str) -> str:
    """Main UI bootstrapper — fetches remote indexes and renders cards.

    Loaded via the dashboard's ``script="js/recommender.js"`` attribute
    in Simple XML; paths are resolved relative to ``appserver/static/``.
    (Splunk Dashboard Studio is unsupported because ``splunk.viz.html``
    strips ``<script>`` tags — see the note where the Studio dashboard
    used to live.) All external HTML is sanitised via a small allow-
    list renderer to avoid XSS from the remote catalogue.
    """
    body = f"""{GENERATED_JS_BANNER}
/* eslint-disable */
(function () {{
  'use strict';

  // Allow-list of upstream catalogue origins. Any operator override via
  // the Settings page is validated against this list before use.
  var ALLOWED_ORIGINS = [
    'https://fenre.github.io',
  ];

  var DEFAULT_API_BASE = '{api_base}';

  // v9.0 — implementation tracking constants.
  var STATUS_LABELS = {{
    not_started: 'Not Started',
    in_progress: 'In Progress',
    implemented: 'Live',
    needs_review: 'Action Needed',
    decommissioned: 'Decommissioned',
  }};
  var FAST_PATH_STATUSES = ['not_started', 'in_progress', 'implemented'];
  var DESTRUCTIVE_STATUSES = ['decommissioned'];
  var REQUIRED_CAPABILITY = 'edit_uc_implementations';
  var SPLUNKBASE_URL_RX = /^https:\\/\\/splunkbase\\.splunk\\.com\\/app\\/\\d+\\/?$/;
  var DECOMMISSION_SAVED_SEARCH = 'uc_implementation_decommission';
  var RECONCILE_INTERVAL_MS = 5000;
  var RECONCILE_MAX_TRIES = 6; // 30 s window for SHC replication.

  var STATE = {{
    apiBase: DEFAULT_API_BASE,
    appName: '{PRIMARY_APP_ID}',
    inventory: null,
    indexes: null,
    thin: null,
    implementations: null,        // map uc_id -> implementation row
    splunkbaseIndex: null,        // map sb_id -> {{name, displayName, ...}}
    capability: false,            // user holds edit_uc_implementations?
    upstreamErrors: {{}},          // per-endpoint error messages
    recommendations: [],
  }};

  // Splunk Web exposes require() from an AMD loader. Run without it if we
  // find ourselves out of context (e.g. unit tests load this module in a
  // plain browser).
  var hasRequire = typeof require === 'function';

  function sanitiseText(text) {{
    if (text === null || text === undefined) return '';
    return String(text);
  }}

  function safeAppend(parent, tagName, text, attrs) {{
    var el = document.createElement(tagName);
    if (text !== undefined && text !== null && text !== '') {{
      el.appendChild(document.createTextNode(sanitiseText(text)));
    }}
    if (attrs) {{
      Object.keys(attrs).forEach(function (k) {{
        var v = attrs[k];
        if (v === null || v === undefined) return;
        el.setAttribute(k, String(v));
      }});
    }}
    parent.appendChild(el);
    return el;
  }}

  function validOrigin(url) {{
    try {{
      var u = new URL(url);
      return ALLOWED_ORIGINS.indexOf(u.origin) !== -1 && u.protocol === 'https:';
    }} catch (err) {{
      return false;
    }}
  }}

  // Only allow http(s) and mailto links in rendered reference lists.
  function safeLinkHref(url) {{
    if (typeof url !== 'string') return null;
    var trimmed = url.trim();
    if (/^(https?:|mailto:)/i.test(trimmed)) return trimmed;
    return null;
  }}

  function loadOperatorApiBase() {{
    try {{
      var ls = window.localStorage.getItem('uc_recommender_api_base');
      if (ls && validOrigin(ls)) return ls;
    }} catch (err) {{
      /* private mode / disabled storage */
    }}
    return DEFAULT_API_BASE;
  }}

  function storeOperatorApiBase(value) {{
    if (!validOrigin(value)) {{
      throw new Error('Refusing to save an API base outside the allow-list.');
    }}
    window.localStorage.setItem('uc_recommender_api_base', value);
  }}

  function fetchJson(url) {{
    if (!validOrigin(url)) {{
      return Promise.reject(new Error(
        'Refusing to fetch ' + url + ' (not in the allow-list).'
      ));
    }}
    return fetch(url, {{ credentials: 'omit', cache: 'no-cache' }}).then(function (r) {{
      if (!r.ok) throw new Error('HTTP ' + r.status + ' for ' + url);
      return r.json();
    }});
  }}

  // v9.0 uses Promise.allSettled so a single failed upstream never
  // blanks the whole dashboard. Errors are recorded per-endpoint on
  // STATE.upstreamErrors so render paths can show specific copy
  // (§ 13d / § 13f). The fifth fetch (splunkbase-index.json) is also
  // settled-tolerant: missing it just means the install checklist
  // renders "Splunkbase metadata unavailable" instead of breaking
  // every card.
  function loadRemoteIndexes(apiBase) {{
    var endpoints = [
      ['sourcetypes', apiBase + '/recommender/sourcetype-index.json'],
      ['cim',         apiBase + '/recommender/cim-index.json'],
      ['apps',        apiBase + '/recommender/app-index.json'],
      ['thin',        apiBase + '/recommender/uc-thin.json'],
      ['splunkbase',  apiBase + '/recommender/splunkbase-index.json'],
    ];
    return Promise.allSettled(endpoints.map(function (e) {{
      return fetchJson(e[1]).catch(function (err) {{
        STATE.upstreamErrors[e[0]] = err && err.message ? err.message : String(err);
        throw err;
      }});
    }})).then(function (results) {{
      var out = {{
        sourcetypes: {{}},
        cim: {{}},
        apps: {{}},
        thin: {{}},
        splunkbase: {{}},
      }};
      var s = results[0]; if (s.status === 'fulfilled') out.sourcetypes = s.value.sourcetypes || {{}};
      var c = results[1]; if (c.status === 'fulfilled') out.cim = c.value.cimModels || {{}};
      var a = results[2]; if (a.status === 'fulfilled') out.apps = a.value.apps || {{}};
      var t = results[3]; if (t.status === 'fulfilled') {{
        out.thin = (t.value.useCases || []).reduce(function (acc, r) {{
          acc[r.id] = r;
          return acc;
        }}, {{}});
      }}
      var b = results[4]; if (b.status === 'fulfilled') out.splunkbase = b.value.apps || {{}};
      return out;
    }});
  }}

  function loadImplementations() {{
    // Build 12: same race-free KV REST path as loadInventory(). The
    // SearchManager-event ordering bug that bit inventory bites this
    // load too — it just hadn't been user-visible because the
    // implementations KV starts empty.
    var primary = '/splunkd/__raw/servicesNS/nobody/'
                + (STATE.appName || 'splunk-uc-recommender')
                + '/storage/collections/data/uc_recommender_implementations'
                + '?output_mode=json&limit=5000';
    var fallbackUrl = '/en-US/splunkd/__raw/servicesNS/nobody/'
                + (STATE.appName || 'splunk-uc-recommender')
                + '/storage/collections/data/uc_recommender_implementations'
                + '?output_mode=json&limit=5000';

    function indexById(rows) {{
      var map = {{}};
      (rows || []).forEach(function (r) {{
        if (r && r.uc_id) map[r.uc_id] = r;
      }});
      return map;
    }}
    function fetchKv(url) {{
      return fetch(url, {{
        credentials: 'same-origin',
        cache: 'no-store',
        headers: {{ 'Accept': 'application/json' }},
      }}).then(function (r) {{
        if (!r.ok) throw new Error('implementations KV returned HTTP ' + r.status);
        return r.json();
      }});
    }}

    return fetchKv(primary).then(indexById).catch(function () {{
      return fetchKv(fallbackUrl).then(indexById).catch(function () {{
        return runSearchJob('| inputlookup uc_recommender_implementations')
          .then(indexById)
          .catch(function (err) {{
            STATE.upstreamErrors.implementations = err && err.message ? err.message : String(err);
            return {{}};
          }});
      }});
    }});
  }}

  function loadCapability() {{
    if (!hasRequire) return Promise.resolve(false);
    return new Promise(function (resolve) {{
      var settled = false;
      var timer;
      function done(value) {{
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(!!value);
      }}
      timer = setTimeout(function () {{ done(false); }}, 10000);

      function checkCaps(caps) {{
        if (!caps) return false;
        if (Array.isArray(caps)) return caps.indexOf(REQUIRED_CAPABILITY) !== -1;
        return caps === REQUIRED_CAPABILITY;
      }}

      function tryProxyFetch() {{
        if (settled) return;
        // Splunk Web's documented pass-through proxy for splunkd REST.
        // Bare /services/... 303s into /en-US/services/... which 404s
        // as an HTML error page; /en-US/splunkd/__raw/services/... is
        // the path Splunk Web actually serves to in-app dashboard JS.
        var url = '/en-US/splunkd/__raw/services/authentication/current-context?output_mode=json';
        fetch(url, {{
          credentials: 'same-origin',
          headers: {{ 'Accept': 'application/json' }},
        }}).then(function (r) {{
          if (!r.ok) return null;
          return r.json();
        }}).then(function (data) {{
          if (!data || !data.entry || !data.entry[0] || !data.entry[0].content) {{
            return done(false);
          }}
          done(checkCaps(data.entry[0].content.capabilities));
        }}).catch(function () {{ done(false); }});
      }}

      require(['splunkjs/mvc'], function (mvc) {{
        try {{
          // Preferred: SplunkJS SDK's createService() — uses SplunkWebHttp
          // transport which already knows how to dial through the
          // authenticated Splunk Web proxy.
          if (mvc && typeof mvc.createService === 'function') {{
            var service = mvc.createService();
            if (service && typeof service.currentUser === 'function') {{
              service.currentUser(function (err, user) {{
                if (err || !user || typeof user.properties !== 'function') {{
                  return tryProxyFetch();
                }}
                try {{
                  var props = user.properties() || {{}};
                  done(checkCaps(props.capabilities));
                }} catch (_) {{
                  tryProxyFetch();
                }}
              }});
              return;
            }}
          }}
          tryProxyFetch();
        }} catch (_) {{
          tryProxyFetch();
        }}
      }}, function () {{ tryProxyFetch(); }});
    }});
  }}

  function safeSplunkbaseUrl(url) {{
    if (typeof url !== 'string') return null;
    var trimmed = url.trim();
    return SPLUNKBASE_URL_RX.test(trimmed) ? trimmed : null;
  }}

  function statusOf(ucId) {{
    if (!STATE.implementations) return 'not_started';
    var row = STATE.implementations[ucId];
    if (!row || !row.status) return 'not_started';
    return STATUS_LABELS[row.status] ? row.status : 'not_started';
  }}

  function persistImplementation(ucId, payload) {{
    var url = '/splunkd/__raw/servicesNS/nobody/' + STATE.appName
      + '/storage/collections/data/uc_recommender_implementations/'
      + encodeURIComponent(ucId);
    var body = Object.assign({{
      _key: ucId,
      uc_id: ucId,
      detection_source: 'manual',
    }}, payload || {{}});
    return fetch(url, {{
      method: 'POST',
      credentials: 'same-origin',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(body),
    }}).then(function (r) {{
      if (!r.ok) throw new Error('KV write failed (HTTP ' + r.status + ')');
      return r.json().catch(function () {{ return body; }});
    }});
  }}

  function dispatchDecommission(ucId, reason) {{
    if (!hasRequire) return Promise.reject(new Error('Not in Splunk Web'));
    var url = '/splunkd/__raw/servicesNS/nobody/' + STATE.appName
      + '/saved/searches/' + encodeURIComponent(DECOMMISSION_SAVED_SEARCH)
      + '/dispatch';
    var requestId = String(Math.random()).slice(2) + '-' + Date.now();
    var params = new URLSearchParams();
    params.append('dispatch.search_args.uc_id', ucId);
    params.append('dispatch.search_args.reason', reason || '');
    params.append('dispatch.search_args.user', 'self');
    params.append('dispatch.search_args.request_id', requestId);
    return fetch(url, {{
      method: 'POST',
      credentials: 'same-origin',
      headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
      body: params.toString(),
    }}).then(function (r) {{
      if (!r.ok) throw new Error('Decommission dispatch failed (HTTP ' + r.status + ')');
      return r.json().catch(function () {{ return null; }});
    }});
  }}

  function reconcileStatus(ucId, expectedStatus) {{
    var attempts = 0;
    function tick() {{
      attempts += 1;
      return loadImplementations().then(function (impl) {{
        STATE.implementations = impl;
        var actual = (impl[ucId] || {{}}).status;
        if (actual === expectedStatus) return true;
        if (attempts >= RECONCILE_MAX_TRIES) return false;
        return new Promise(function (resolve) {{
          setTimeout(function () {{ resolve(tick()); }}, RECONCILE_INTERVAL_MS);
        }});
      }}).catch(function () {{ return false; }});
    }}
    return tick();
  }}

  function runSearchJob(spl) {{
    return new Promise(function (resolve, reject) {{
      if (!hasRequire) {{
        return reject(new Error('Not running inside Splunk Web'));
      }}
      var settled = false;
      var hardTimer = null;
      function safeResolve(rows) {{
        if (settled) return;
        settled = true;
        if (hardTimer) clearTimeout(hardTimer);
        resolve(rows || []);
      }}
      function safeReject(err) {{
        if (settled) return;
        settled = true;
        if (hardTimer) clearTimeout(hardTimer);
        reject(err instanceof Error ? err : new Error(String(err)));
      }}
      hardTimer = setTimeout(function () {{
        safeReject(new Error('search timed out after 30s'));
      }}, 30000);
      require(['splunkjs/mvc', 'splunkjs/mvc/searchmanager'], function (mvc, SearchManager) {{
        try {{
          var name = 'uc_recommender_job_' + Math.random().toString(36).slice(2);
          var sm = new SearchManager({{
            id: name,
            search: spl,
            earliest_time: '-15m',
            latest_time: 'now',
            autostart: true,
            preview: false,
            // cache:false forces a fresh dispatch every page load. Builds
            // 9 + 10 carried cache:true which let SearchManager hand back
            // a previously-empty result set (e.g. dispatch run before
            // any inventory saved-search had populated the lookup),
            // giving the matcher [] forever even after the lookup
            // had filled. The cost of a fresh dispatch on a tiny
            // ``inputlookup`` is negligible.
            cache: false,
          }});
          var results = sm.data('results', {{ count: 5000 }});
          var sawSearchDone = false;
          var pollsAfterDone = 0;

          // Build 11 fix — REPLACES the build-9 / build-10 listener-only
          // path. Previous builds attached ``results.on('data', ...)`` and
          // ``sm.on('search:done', ...)`` AFTER the SearchManager auto-
          // started the job; for fast searches (a tiny ``inputlookup``
          // returns in milliseconds) those events could fire BEFORE the
          // listener registration completed, the events were lost, and
          // the promise either timed out or resolved with [] depending
          // on whether the deferred 800 ms fallback had registered in
          // time. The user-visible failure mode was the dashboard tiles
          // showing 40 / 90 inventory rows but the recommender saying
          // "No matches yet".
          //
          // The new strategy keeps the listeners (so we still surface
          // 'search:error' / 'search:fail') but ALSO drives a polling
          // loop on ``results.data()`` every 500 ms. Polling tolerates
          // the listener-attach race because we will read the populated
          // ResultsModel as soon as the SDK's background fetch lands.
          // The polling loop uses recursive setTimeout (not setInterval)
          // so the stubbed test sandbox in
          // tests/recommender/run_search_job.test.mjs needs no extra
          // globals.
          function pull() {{
            if (settled) return;
            var d = (typeof results.data === 'function') ? results.data() : null;
            // ``d.results`` is populated (even as []) once the SDK's
            // GET /services/search/jobs/<sid>/results call lands. If
            // the property is missing, the fetch hasn't completed yet.
            if (d && d.results !== undefined) {{
              safeResolve(d.results || []);
              return;
            }}
            // Force a fetch — if the 'data' event fired before our
            // listener attached, the model already has the rows but
            // hasn't notified anyone. Calling fetch() either no-ops
            // (already fetched) or kicks the fetch.
            if (results && typeof results.fetch === 'function') {{
              try {{ results.fetch(); }} catch (_) {{ /* ignore */ }}
            }}
            // After the JOB itself reports done we only wait a bounded
            // number of polls for the background results fetch to
            // settle. 4 polls × 500 ms = 2 s headroom is plenty for the
            // SDK on every Splunk version we test against; if the
            // fetch is still empty after that, the search legitimately
            // returned no rows and we resolve with [].
            if (sawSearchDone) {{
              pollsAfterDone += 1;
              if (pollsAfterDone >= 4) {{
                safeResolve(d && d.results ? d.results : []);
                return;
              }}
            }}
          }}
          function pollLoop() {{
            if (settled) return;
            pull();
            if (settled) return;
            setTimeout(pollLoop, 500);
          }}

          results.on('data', pull);
          sm.on('search:done', function () {{
            sawSearchDone = true;
            pull();
          }});
          sm.on('search:error', function (err) {{ safeReject(err); }});
          sm.on('search:fail', function (err) {{ safeReject(err); }});
          sm.on('search:cancelled', function () {{
            safeReject(new Error('search cancelled'));
          }});

          // First quick attempt covers the case where the search
          // already completed before this require() callback fired
          // — i.e. both events were lost to the void.
          setTimeout(pull, 100);
          // Then settle into a steady polling cadence as the backstop.
          setTimeout(pollLoop, 500);
        }} catch (err) {{
          safeReject(err);
        }}
      }}, function (err) {{
        safeReject(err);
      }});
    }});
  }}

  function loadInventory() {{
    // Build 12: bypass the in-page SearchManager entirely. Builds 9–11
    // wrestled with a SearchManager event-ordering race where the
    // ``data`` event for fast ``inputlookup`` searches fired BEFORE
    // our listener attached, leaving the recommender with [] forever
    // even though the dashboard tiles (which use Simple XML's own
    // SearchManager) showed rows. The KV collection is reachable via
    // a plain REST GET on Splunk Web's ``/splunkd/__raw`` proxy
    // (credentials ride along on the active Splunk Web session
    // cookie — same proxy path persistImplementation() uses to
    // write back), so we query the collection directly. Same data,
    // no SearchManager, zero races.
    var primary  = '/splunkd/__raw/servicesNS/nobody/'
                 + (STATE.appName || 'splunk-uc-recommender')
                 + '/storage/collections/data/uc_recommender_inventory'
                 + '?output_mode=json&limit=5000';
    var fallbackUrl = '/en-US/splunkd/__raw/servicesNS/nobody/'
                 + (STATE.appName || 'splunk-uc-recommender')
                 + '/storage/collections/data/uc_recommender_inventory'
                 + '?output_mode=json&limit=5000';

    function normalise(data) {{
      if (!Array.isArray(data)) return [];
      return data.map(function (row) {{
        return {{
          type: row.type || '',
          name: row.name || '',
          count: row.count || 0,
          firstSeen: row.firstSeen || '',
          lastSeen:  row.lastSeen  || '',
          extras:    row.extras    || '',
        }};
      }});
    }}

    function fetchKv(url) {{
      return fetch(url, {{
        credentials: 'same-origin',
        cache: 'no-store',
        headers: {{ 'Accept': 'application/json' }},
      }}).then(function (r) {{
        if (!r.ok) throw new Error('inventory KV returned HTTP ' + r.status);
        return r.json();
      }});
    }}

    return fetchKv(primary).then(normalise).catch(function () {{
      return fetchKv(fallbackUrl).then(normalise).catch(function () {{
        // Last-resort fallback to the SearchManager path so the
        // page still shows SOMETHING if both proxy URLs are blocked
        // (e.g. constrained Splunk Cloud egress).
        return runSearchJob('| inputlookup uc_recommender_inventory');
      }});
    }});
  }}

  function score(row) {{
    var crit = {{
      critical: 1.0,
      high: 0.8,
      medium: 0.6,
      low: 0.4,
    }};
    return (row._score || 0) * (crit[row.criticality] || 0.6);
  }}

  // Drop catalog app-index keys that look like prose fragments rather
  // than real app/TA names. Upstream ``_recommender_apps()`` splits the
  // free-text ``t`` field on commas which can land mid-parenthesis (e.g.
  // "API gateway TAs (Kong, F5)" -> "API gateway TAs (Kong" + " F5)").
  // Filtering at consume-time is a defence in depth against these
  // tokens — the upstream generator filters too, but old API surfaces
  // may still be cached. Also reduces fuzzy-match noise.
  function looksLikeAppKey(key) {{
    if (typeof key !== 'string' || !key) return false;
    var first = key.charAt(0);
    // Reject parenthetical lead-ins and markdown/prose debris up
    // front — the upstream generator already filters these but old
    // cached app-index payloads may still contain them.
    if (first === '(' || first === '*' || first === '_' || first === '[' || first === '<' || first === '$' || first === '#' || first === '/') return false;
    var open = 0; var close = 0;
    for (var i = 0; i < key.length; i++) {{
      var c = key.charCodeAt(i);
      if (c === 40) open += 1;
      else if (c === 41) close += 1;
    }}
    if (open !== close) return false;
    if (key.indexOf('**') !== -1 || key.indexOf('__') !== -1) return false;
    if (key.toLowerCase().indexOf('://') !== -1) return false;
    // Reject keys that begin with a prose connective. These are
    // free-text fragments produced by mid-sentence comma splits in
    // the upstream ``t`` field, never real Splunk app labels.
    var lower = key.toLowerCase();
    var proseStarts = ['or ', 'and ', 'with ', 'via ', 'using ', 'for ', 'in ', 'if ', 'the ', 'this ', 'that ', 'these ', 'those ', 'any '];
    for (var p = 0; p < proseStarts.length; p++) {{
      if (lower.indexOf(proseStarts[p]) === 0) return false;
    }}
    return true;
  }}

  // Token-set overlap for app names — lightweight Jaccard over
  // alphanum-stripped lowercase words ≥3 chars. Avoids the false
  // positives the previous "indexOf substring" matcher produced when
  // a short app name was a substring of a longer prose key (e.g.
  // user app "API" matching catalog key "API gateway access logs").
  function appNameTokens(s) {{
    if (typeof s !== 'string') return [];
    var t = s.toLowerCase().replace(/[^a-z0-9_]+/g, ' ').split(/\\s+/);
    var out = [];
    for (var i = 0; i < t.length; i++) {{
      if (t[i] && t[i].length >= 3) out.push(t[i]);
    }}
    return out;
  }}

  // Build 14 — broader tokeniser for cross-namespace matching. App
  // tokens preserve ``_`` so ``Splunk_TA_nix`` stays one token, but
  // index names (``edge_hub_opcua``), sourcetype names
  // (``splunk:edge_hub:opcua``), and underscore-separated app folders
  // need to be reduced to comparable atomic words. ``broadTokens``
  // splits on every non-alphanumeric character so it can find the
  // ``opcua`` overlap between an index and a sourcetype.
  function broadTokens(s) {{
    if (typeof s !== 'string') return [];
    var t = s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').split(/\\s+/);
    var out = [];
    for (var i = 0; i < t.length; i++) {{
      if (t[i] && t[i].length >= 3) out.push(t[i]);
    }}
    return out;
  }}
  // Exposed for unit tests.
  window.__uc_recommender_helpers__ = {{
    looksLikeAppKey: looksLikeAppKey,
    appNameTokens: appNameTokens,
    looksLikeRealSourcetype: looksLikeRealSourcetype,
    looksLikeUserIndex: looksLikeUserIndex,
    isItsiInternalInventoryApp: isItsiInternalInventoryApp,
    equipmentOptions: equipmentOptions,
    sortRows: sortRows,
  }};

  // Build 13 — three matcher fairness fixes.
  //
  // Live-data analysis (90 inventory apps + 2,428 catalogue keys) found
  // that the Recommend tab returned 100/100 cat-22 UCs in the top-100
  // even though only ~22% of catalogue UCs and ~33% of citations are
  // cat-22. Three compounding causes:
  //
  // (a) The token-overlap matcher accepted single-token matches on
  //     generic Splunk-marketing words like "splunk", "for", "add",
  //     "addon", which appear in 28 of 90 inventory apps AND in 555 of
  //     2,428 catalogue keys. These reach 5,270 unique UCs and bias
  //     heavily toward cat-22.
  // (b) The cat-22 catalogue includes ~138 synthetic
  //     "App Name (NNNN)" / "App Name (Splunkbase NNNN)" evidence-pack
  //     keys, ~87% of whose UC citations are cat-22. One inventory row
  //     could match 5+ of those keys for the same UC, piling +5 on top
  //     of the legitimate +3 exact match.
  // (c) No diversification ceiling on the post-sort top-N let cat-22
  //     sweep the entire slice(0, 100).
  //
  // Stop-words used in (a). Tokens that appear in *both* sides at high
  // density and carry no meaningful signal.
  //
  // Build 15 expansion: the live-data simulation against a real ITSI
  // shop (90 apps, 27 CIM models) showed that "itsi", "module",
  // "monitoring", "content", "pack", "dashboard", "report", "service"
  // / "intelligence" were the dominant noise sources — every "ITSI
  // Module for X" inventory app token-matched dozens of catalogue
  // entries that simply contained "monitoring" or "module" with no
  // domain overlap. We deliberately keep "data", "cloud", "enterprise"
  // OFF the list — they're still useful disambiguators in app names.
  var APP_TOKEN_STOPWORDS = {{
    'splunk': 1, 'app': 1, 'apps': 1, 'add': 1, 'addon': 1, 'addons': 1,
    'for': 1, 'and': 1, 'the': 1, 'with': 1, 'via': 1, 'use': 1, 'using': 1,
    'from': 1, 'has': 1, 'any': 1, 'all': 1, 'this': 1, 'that': 1,
    'optional': 1, 'required': 1, 'requires': 1, 'tools': 1, 'tool': 1,
    // build 15 — ITSI / Content Pack / Monitoring family stop-words.
    'itsi': 1, 'module': 1, 'modules': 1,
    'monitoring': 1, 'monitor': 1,
    'content': 1, 'pack': 1, 'packs': 1,
    'dashboard': 1, 'dashboards': 1, 'report': 1, 'reports': 1,
    'service': 1, 'services': 1, 'intelligence': 1
  }};

  function meaningfulTokens(tokens) {{
    var out = [];
    for (var i = 0; i < tokens.length; i++) {{
      if (!APP_TOKEN_STOPWORDS[tokens[i]]) out.push(tokens[i]);
    }}
    return out;
  }}

  // Build 14 — evidence-pack synthetic-key detector. Catalogue keys of
  // the form ``Some App Name (NNNN)`` or ``Some App Name (Splunkbase
  // NNNN)`` are regulatory-evidence citations injected by the cat-22
  // pipeline. A user installing the underlying app does not imply the
  // SOX/HIPAA/etc. UC behind that key is actionable for them, so we
  // multiply any match weight that fires through such a key by
  // ``EVIDENCE_PACK_DISCOUNT``. The clean ``Some App Name`` key (no
  // trailing parens) still scores at full weight.
  var EVIDENCE_PACK_DISCOUNT = 0.4;
  // Trailing ``(NNNN)`` or ``(Splunkbase NNNN)``, optionally followed
  // by punctuation or whitespace. The trailing-punctuation tolerance
  // catches catalogue keys that picked up a stray ``.`` or ``,`` from
  // the upstream prose extractor (e.g.
  // ``Splunk Common Information Model Add-on (1621).``).
  var EVIDENCE_PACK_RE = /\\(\\s*(?:splunkbase\\s*)?\\d{{2,}}\\s*\\)\\s*[.,;:!?\\s]*$/i;
  function isEvidencePackKey(key) {{
    return typeof key === 'string' && EVIDENCE_PACK_RE.test(key);
  }}

  // Build 15 — guards on the INVENTORY side. The live-data simulation
  // against a real ITSI/OT shop showed that the dominant noise sources
  // were Splunk-auto-classified "sourcetypes" that don't represent real
  // monitored data (`_json`, `stash`, `*-too_small`, `dpkg-N`, bare
  // `cpu`/`disk`/`memory` from Linux input rules), Splunk-system /
  // ITSI-internal indexes (`main`, `summary`, `learned`, `itsi_*`), and
  // ITSI Content Pack inventory apps (`DA-ITSI-CP-*`) — none of which
  // reflect a domain the user is actually monitoring. These three
  // helpers filter inventory rows out (or down-weight them) BEFORE the
  // matcher tokenises them so they cannot pile noise onto the buckets.

  // Sourcetype names the saved-search inventory will return that
  // are Splunk-internal / auto-classified placeholders, never real
  // monitored data domains.
  var BUILD15_SYSTEM_SOURCETYPES = {{
    'stash': 1, 'config_file': 1, 'learned': 1, 'history': 1
  }};
  // Bare auto-classified short names with no namespace separator (e.g.
  // collectd's `cpu` / `memory` lines when no inputs.conf rule fires).
  // We restrict the bare-name guard to a strict allow-deny set so we
  // don't accidentally drop legitimate short sourcetypes.
  var BUILD15_BARE_AUTOCLASS = {{
    'cpu': 1, 'disk': 1, 'memory': 1, 'mem': 1, 'swap': 1,
    'process': 1, 'login': 1, 'utmp': 1, 'wtmp': 1, 'btmp': 1
  }};
  var BUILD15_SYSTEM_PKG_RE = /^(?:dpkg|alternatives|history|yum|apt|rpm)-/;
  function looksLikeRealSourcetype(name) {{
    if (typeof name !== 'string' || !name) return false;
    if (name.charAt(0) === '_') return false;            // _json, _internal_*
    if (BUILD15_SYSTEM_SOURCETYPES[name]) return false;
    if (BUILD15_BARE_AUTOCLASS[name]) return false;
    if (/-too_small$/.test(name)) return false;
    if (BUILD15_SYSTEM_PKG_RE.test(name)) return false;
    return true;
  }}

  // Splunk-system + ITSI-internal indexes whose names are not signals
  // of monitored data. Splunk auto-creates the leading ones; ITSI
  // pipelines auto-create the `itsi_*` ones for accounting.
  var BUILD15_SYSTEM_INDEXES = {{
    'main': 1, 'summary': 1, 'history': 1, 'learned': 1,
    'lastchanceindex': 1, 'splunklogger': 1, 'splunk_metrics': 1,
    'cim_modactions': 1, 'anomaly_detection': 1, 'snmptrapd': 1
  }};
  function looksLikeUserIndex(name) {{
    if (typeof name !== 'string' || !name) return false;
    if (name.charAt(0) === '_') return false;            // _internal, _audit, _telemetry, …
    if (BUILD15_SYSTEM_INDEXES[name]) return false;
    if (name.indexOf('itsi_') === 0) return false;       // 10+ ITSI internal accounting indexes
    if (name.indexOf('da_itsi_') === 0) return false;
    return true;
  }}

  // Inventory app rows whose ``extras`` (folder name) marks them as
  // ITSI internals — Content Packs (DA-ITSI-CP-*), Modules (DA-ITSI-*),
  // supporting addons (SA-ITSI-*). Same shape as the evidence-pack
  // discount: real apps installed for ITSI plumbing, not user-domain.
  var BUILD15_ITSI_INTERNAL_RE = /^(?:DA-ITSI-|SA-ITSI-)/i;
  function isItsiInternalInventoryApp(extras) {{
    return typeof extras === 'string' && BUILD15_ITSI_INTERNAL_RE.test(extras);
  }}

  function matchUseCases(inventory, indexes) {{
    var buckets = {{}};

    // ``rowSeen`` tracks ``invRowKey + '::' + ucId`` -> highest weight
    // already awarded. Implements fix (b) — a single inventory row can
    // contribute at most that highest weight to any one UC, even if it
    // matches the UC across many catalogue keys.
    var rowSeen = {{}};
    var currentRowKey = '';

    function bump(ucId, weight, reason) {{
      if (!ucId) return;
      // Tolerate floating-point weights (build 14 uses 0.4 and 0.5).
      if (!(weight > 0)) return;
      var seenKey = currentRowKey + '::' + ucId;
      var prev = rowSeen[seenKey] || 0;
      if (weight <= prev) {{
        // Already awarded ≥ this weight from this inventory row to
        // this UC; skip (the cap that kills evidence-pack pile-ups).
        return;
      }}
      var delta = weight - prev;
      rowSeen[seenKey] = weight;
      if (!buckets[ucId]) {{
        buckets[ucId] = {{
          id: ucId,
          score: 0,
          reasons: [],
          topReason: '',
          topWeight: 0,
        }};
      }}
      buckets[ucId].score += delta;
      buckets[ucId].reasons.push(reason);
      // Build 14 — track strongest match reason for the UI chip.
      // ``topReason`` answers the question "why was this UC picked?"
      // for the user at a glance. We store the un-discounted weight
      // (so the chip ranks "sourcetype: x" 10 above "app token: y" 0.5).
      if (weight > buckets[ucId].topWeight) {{
        buckets[ucId].topReason = reason;
        buckets[ucId].topWeight = weight;
      }}
    }}

    // Pre-filter the app-index once per call so the per-row loop is
    // O(real_apps) rather than O(all_keys_including_prose_fragments).
    var cleanAppKeys = Object.keys(indexes.apps || {{}}).filter(looksLikeAppKey);
    var cleanAppKeysLower = cleanAppKeys.map(function (k) {{ return k.toLowerCase(); }});
    // Pre-strip stop-words from the catalogue tokens too so the
    // overlap test below already operates on meaningful tokens only.
    var cleanAppTokenLists = cleanAppKeys.map(function (k) {{
      return meaningfulTokens(appNameTokens(k));
    }});

    inventory.forEach(function (row, rowIndex) {{
      var rawName = row.name || '';
      var name = rawName.toLowerCase();
      if (!name) return;
      // Stable per-row key for the (row, UC) cap. We use the inventory
      // index because two rows might share a (name, type) pair.
      currentRowKey = (row.type || '?') + ':' + rowIndex + ':' + name;

      if (row.type === 'sourcetype') {{
        // Build 15 — drop Splunk-auto-classified placeholder
        // sourcetypes BEFORE they reach the matcher. They carry no
        // signal about real monitored data (e.g. `_json`, `stash`,
        // `dpkg-too_small`, `config_file`).
        if (!looksLikeRealSourcetype(name)) return;
        // Build 14 — sourcetype is the strongest signal: real data
        // flowing through the user's deployment. Weights bumped from
        // 3/1 to 10/4 so a single sourcetype-exact hit dominates any
        // app-only match, and a sourcetype-fuzzy hit still beats
        // app-fuzzy (4 vs 1).
        var exact = indexes.sourcetypes[name];
        if (exact) exact.forEach(function (id) {{ bump(id, 10, 'sourcetype: ' + name); }});
        Object.keys(indexes.sourcetypes).forEach(function (key) {{
          if (key !== name && (key.indexOf(name) !== -1 || name.indexOf(key) !== -1)) {{
            // Build 15 — scale fuzzy weight by the substring/length
            // ratio. Without this, 24 Meraki sourcetypes all
            // fuzzy-matching the single short catalogue key `meraki`
            // gave +4 each to every UC cited under `meraki`, tying
            // 41 UCs at the exact same score 98.40. With ratio
            // scaling, longer / shorter pairs score lower so closer
            // matches break the tie.
            var ratio = Math.min(name.length, key.length)
                      / Math.max(name.length, key.length);
            var fuzzyWeight = 4 * ratio;
            indexes.sourcetypes[key].forEach(function (id) {{
              bump(id, fuzzyWeight, 'fuzzy sourcetype: ' + key);
            }});
          }}
        }});
      }} else if (row.type === 'cim_model') {{
        // Build 14 — award even unaccelerated CIM models. A CIM model
        // being defined at all is meaningful intent: the user has
        // mapped their data into that schema. Accelerated keeps the
        // higher weight (3) because tstats-friendly searches actually
        // run faster against it.
        //
        // Build 15 — defined-only halved from +1 → +0.5. Real-world
        // ITSI deployments ship with all 27 CIM models defined-but-
        // not-accelerated, so the +1 used to lift every CIM-touching
        // UC by a flat noise floor. Halving keeps it as a tiebreaker
        // without dominating the score.
        var cimIds = indexes.cim[row.name];
        if (cimIds) {{
          var accel = (row.extras || '').toLowerCase().indexOf('accelerated') !== -1
                   && (row.extras || '').toLowerCase().indexOf('not_accelerated') === -1;
          var cimWeight = accel ? 3 : 0.5;
          var cimReason = accel
            ? 'CIM accelerated: ' + row.name
            : 'CIM defined: '   + row.name;
          cimIds.forEach(function (id) {{ bump(id, cimWeight, cimReason); }});
        }}
      }} else if (row.type === 'index') {{
        // Build 14 — match the user's index names as a low-weight
        // signal. Indexes are weaker than sourcetypes (an index can
        // be empty) but a defined index named ``meraki`` or
        // ``edge_hub_opcua`` is still real evidence the user is
        // collecting that data domain.
        //
        // Index names use ``_`` separators while sourcetypes use ``:``
        // and apps use mixed punctuation, so we tokenise both with
        // ``broadTokens`` (splits on every non-alphanumeric char) and
        // look for at least one shared meaningful token. Caps: +1 for
        // sourcetype-side overlap (most likely to indicate flowing
        // data), +0.5 for app-side overlap (intent signal only).
        //
        // Build 15 — drop Splunk-system + ITSI-internal indexes BEFORE
        // tokenising. The user's `main` / `summary` / `itsi_*`
        // accounting indexes were generating cross-token noise (e.g.
        // `itsi_summary` token-matching every `splunk:summary` key in
        // the catalogue) without any real monitoring intent.
        if (!looksLikeUserIndex(name)) return;
        var idxLow = name;
        var idxTokens = meaningfulTokens(broadTokens(idxLow));
        if (idxTokens.length) {{
          Object.keys(indexes.sourcetypes).forEach(function (key) {{
            var keyTokens = meaningfulTokens(broadTokens(key));
            for (var ti = 0; ti < idxTokens.length; ti++) {{
              if (keyTokens.indexOf(idxTokens[ti]) !== -1) {{
                indexes.sourcetypes[key].forEach(function (id) {{
                  bump(id, 1, 'index ↔ sourcetype: ' + idxLow + ' / ' + key);
                }});
                break;
              }}
            }}
          }});
          for (var ai = 0; ai < cleanAppKeys.length; ai++) {{
            var keyTokens2 = meaningfulTokens(broadTokens(cleanAppKeys[ai]));
            for (var ti2 = 0; ti2 < idxTokens.length; ti2++) {{
              if (keyTokens2.indexOf(idxTokens[ti2]) !== -1) {{
                var w = isEvidencePackKey(cleanAppKeys[ai])
                  ? 0.5 * EVIDENCE_PACK_DISCOUNT
                  : 0.5;
                indexes.apps[cleanAppKeys[ai]].forEach(function (id) {{
                  bump(id, w, 'index ↔ app: ' + idxLow + ' / ' + cleanAppKeys[ai]);
                }});
                break;
              }}
            }}
          }}
        }}
      }} else if (row.type === 'app') {{
        // (1) Splunkbase folder/title exact match against ``extras`` —
        // the inventory saved-search records the ``title`` (folder) in
        // ``extras`` after the build-11 scanner change so we can still
        // hit ``Splunk_TA_nix`` -> 171 UCs even when ``name`` carries
        // the human-readable label.
        var inventoryTokens = [name];
        var extras = (row.extras || '').toLowerCase();
        if (extras && extras !== name) inventoryTokens.push(extras);
        // (2) Per-key matching: exact (high weight), substring (medium),
        // token overlap (low weight). Token overlap protects against
        // false positives that naive substring produced — only counts
        // when ≥1 word ≥3 chars is shared between user inventory and
        // catalog key, AFTER stop-word filtering.
        var rowTokens = meaningfulTokens(
          appNameTokens(rawName + ' ' + (row.extras || ''))
        );
        for (var i = 0; i < cleanAppKeys.length; i++) {{
          var keyLower = cleanAppKeysLower[i];
          var matched = false;
          var weight = 0;
          var reasonSuffix = '';
          for (var j = 0; j < inventoryTokens.length; j++) {{
            if (keyLower === inventoryTokens[j]) {{
              matched = true; weight = 3; reasonSuffix = 'app exact: ' + cleanAppKeys[i];
              break;
            }}
          }}
          if (!matched) {{
            // Substring match — but ONLY when the inventory token isn't
            // a generic Splunk-marketing word. Without this guard,
            // "splunk" inside an inventory app name substring-matches
            // every catalogue key containing "Splunk".
            for (var k = 0; k < inventoryTokens.length; k++) {{
              var invTok = inventoryTokens[k];
              if (!invTok) continue;
              if (APP_TOKEN_STOPWORDS[invTok]) continue;
              if (keyLower.indexOf(invTok) !== -1
                  || invTok.indexOf(keyLower) !== -1) {{
                matched = true; weight = 1; reasonSuffix = 'app substring: ' + cleanAppKeys[i];
                break;
              }}
            }}
          }}
          if (!matched && rowTokens.length) {{
            // Token-overlap fallback over MEANINGFUL tokens only.
            // ``rowTokens`` and ``cleanAppTokenLists[i]`` were both
            // already stripped of stop-words above. Build 14: weight
            // dropped to 0.5 — token-only matches are by far the
            // weakest signal and were the dominant noise source.
            var keyTokens = cleanAppTokenLists[i];
            for (var t = 0; t < rowTokens.length; t++) {{
              if (keyTokens.indexOf(rowTokens[t]) !== -1) {{
                matched = true; weight = 0.5; reasonSuffix = 'app token: ' + cleanAppKeys[i];
                break;
              }}
            }}
          }}
          if (matched) {{
            // Build 14 evidence-pack discount. Synthetic catalogue
            // keys like ``Splunk Add-on for Unix and Linux (833)``
            // are regulatory documentation, not actionable installs.
            var effectiveWeight = isEvidencePackKey(cleanAppKeys[i])
              ? weight * EVIDENCE_PACK_DISCOUNT
              : weight;
            // Build 15 — ITSI Content-Pack / Module / supporting
            // addon discount. Inventory rows whose ``extras`` matches
            // ``DA-ITSI-CP-*`` / ``DA-ITSI-*`` / ``SA-ITSI-*`` are
            // ITSI plumbing, not user-domain installs. Multiply by
            // the same 0.4× we use for evidence-pack catalogue keys
            // so we don't double-discount the intersection.
            if (isItsiInternalInventoryApp(row.extras)
                && !isEvidencePackKey(cleanAppKeys[i])) {{
              effectiveWeight *= EVIDENCE_PACK_DISCOUNT;
            }}
            indexes.apps[cleanAppKeys[i]].forEach(function (id) {{
              bump(id, effectiveWeight, reasonSuffix);
            }});
          }}
        }}
      }}
    }});

    var out = Object.keys(buckets).map(function (id) {{
      var bucket = buckets[id];
      var thin = indexes.thin[id];
      if (!thin) return null;
      return {{
        id: id,
        title: thin.title,
        value: thin.value,
        criticality: thin.criticality,
        difficulty: thin.difficulty,
        monitoringType: thin.monitoringType,
        splunkPillar: thin.splunkPillar,
        app: thin.app,
        cimModels: thin.cimModels,
        mitreAttack: thin.mitreAttack,
        // Build 15 — surface equipment / equipmentModels to the UI
        // so the toolbar can offer an equipment filter chip + sort
        // (and so renderCard can show the equipment slugs at a glance
        // without re-reading the thin index per card).
        equipment: thin.equipment || [],
        equipmentModels: thin.equipmentModels || [],
        _score: bucket.score,
        reasons: bucket.reasons,
        topReason: bucket.topReason,
        topWeight: bucket.topWeight,
      }};
    }}).filter(Boolean);
    out.sort(function (a, b) {{
      return (score(b) || 0) - (score(a) || 0);
    }});

    // Fix (c) — diversify the top-100 across categories. Without this,
    // even with stop-words and the per-row cap, the cat-22 evidence-
    // pack catalogue is dense enough that cat-22 still sweeps the
    // top of the score-sorted list. We allow at most ~30% of the slice
    // from any single category, falling back to score-sort once a
    // category hits its cap. Categories are derived from the leading
    // numeric segment of the UC id (e.g. "22.1.5" -> "22").
    var TOP_N = 100;
    var PER_CAT_CAP = Math.ceil(TOP_N * 0.30);   // 30 of 100 per category
    var perCat = {{}};
    var diversified = [];
    var overflow = [];
    for (var idx = 0; idx < out.length && diversified.length < TOP_N; idx++) {{
      var item = out[idx];
      var dot = item.id.indexOf('.');
      var cat = dot > 0 ? item.id.slice(0, dot) : item.id;
      var c = perCat[cat] || 0;
      if (c < PER_CAT_CAP) {{
        diversified.push(item);
        perCat[cat] = c + 1;
      }} else {{
        overflow.push(item);
      }}
    }}
    // If we ran out of UCs from other categories before filling 100
    // (e.g. small synthetic indexes in tests, or sparse catalogues),
    // top up the slice with the highest-scoring overflow items.
    for (var ov = 0; ov < overflow.length && diversified.length < TOP_N; ov++) {{
      diversified.push(overflow[ov]);
    }}
    return diversified;
  }}

  function renderStatusBadge(parent, ucId) {{
    var status = statusOf(ucId);
    var badge = safeAppend(parent, 'span', null, {{
      'class': 'uc-status-badge uc-status-' + status,
      'data-status': status,
      'role': 'status',
    }});
    // Always set textContent — never rely on colour alone (a11y, § 12d).
    badge.textContent = STATUS_LABELS[status] || 'Unknown';
    return badge;
  }}

  function renderRequiredSplunkbase(parent, sb) {{
    if (!Array.isArray(sb) || sb.length === 0) {{
      var none = safeAppend(parent, 'p', null, {{ 'class': 'uc-sb-none' }});
      none.textContent = (STATE.splunkbaseIndex && Object.keys(STATE.splunkbaseIndex).length)
        ? 'No Splunkbase apps required.'
        : 'Splunkbase metadata unavailable; consult catalog directly.';
      return;
    }}
    var details = safeAppend(parent, 'details', null, {{ 'class': 'uc-sb-section' }});
    var summary = safeAppend(details, 'summary');
    summary.textContent = 'Required Splunkbase apps (' + sb.length + ')';
    var ul = safeAppend(details, 'ul', null, {{ 'class': 'uc-sb-list' }});
    sb.forEach(function (entry) {{
      if (!entry || typeof entry.id === 'undefined') return;
      var meta = (STATE.splunkbaseIndex || {{}})[String(entry.id)] || {{}};
      var li = safeAppend(ul, 'li', null, {{ 'class': 'uc-sb-item' }});
      var label = (entry.name || meta.displayName || meta.name || ('App ' + entry.id));
      var role = entry.role ? (' (' + entry.role + ')') : '';
      // Try the catalog's URL first, but fall back to the canonical
      // /app/<id>/ form if it fails the allow-list — this gives us a
      // safe link even when upstream metadata is corrupt.
      var url = safeSplunkbaseUrl(meta.url || '')
        || safeSplunkbaseUrl('https://splunkbase.splunk.com/app/' + entry.id + '/');
      if (url) {{
        var a = safeAppend(li, 'a', null, {{
          'href': url,
          'target': '_blank',
          'rel': 'noopener noreferrer',
        }});
        a.textContent = label + role;
      }} else {{
        safeAppend(li, 'span', label + role);
      }}
      if (entry.minVersion) {{
        safeAppend(li, 'span', '  min ' + entry.minVersion, {{
          'class': 'uc-sb-version',
        }});
      }}
      if (entry.requiresSmeReview) {{
        safeAppend(li, 'span', '  needs review', {{
          'class': 'uc-sb-review',
        }});
      }}
      if (meta.cloudVetted === false) {{
        safeAppend(li, 'span', '  not cloud-vetted', {{
          'class': 'uc-sb-not-cloud',
        }});
      }}
    }});
  }}

  function renderCard(parent, row) {{
    var card = safeAppend(parent, 'div', null, {{
      'class': 'uc-card uc-crit-' + (row.criticality || 'medium'),
      'data-uc-id': row.id,
    }});
    var header = safeAppend(card, 'div', null, {{ 'class': 'uc-card-head' }});
    safeAppend(header, 'span', 'UC ' + row.id, {{ 'class': 'uc-id' }});
    safeAppend(header, 'span', row.criticality || '', {{ 'class': 'uc-crit' }});
    safeAppend(header, 'span', row.splunkPillar || '', {{ 'class': 'uc-pillar' }});
    renderStatusBadge(header, row.id);
    safeAppend(card, 'h4', row.title || ('UC ' + row.id));
    if (row.value) safeAppend(card, 'p', row.value, {{ 'class': 'uc-value' }});
    // Build 15 — equipment chips. Render a small row of pill-shaped
    // chips for the UC's equipment slugs (and the first equipment
    // model, if any) so users can scan equipment compatibility at a
    // glance instead of opening the detail drawer. Capped at 4 chips
    // + an "+N more" overflow chip for cards with long lists.
    var eq = (row.equipment || []);
    var em = (row.equipmentModels || []);
    if (eq.length || em.length) {{
      var chipRow = safeAppend(card, 'div', null, {{ 'class': 'uc-eq-chips' }});
      var shown = 0;
      var MAX_CHIPS = 4;
      eq.slice(0, MAX_CHIPS).forEach(function (slug) {{
        safeAppend(chipRow, 'span', slug, {{ 'class': 'uc-eq-chip uc-eq-chip-slug' }});
        shown++;
      }});
      // Show one equipment model only if we still have chip budget.
      if (shown < MAX_CHIPS && em.length) {{
        safeAppend(chipRow, 'span', em[0], {{ 'class': 'uc-eq-chip uc-eq-chip-model' }});
        shown++;
      }}
      var extra = (eq.length + em.length) - shown;
      if (extra > 0) {{
        safeAppend(chipRow, 'span', '+' + extra + ' more', {{
          'class': 'uc-eq-chip uc-eq-chip-more',
          'title': eq.concat(em).join(', '),
        }});
      }}
    }}
    // Build 14 — render strongest match reason as a colour-coded chip
    // so users can see at a glance whether a UC was picked from a
    // strong signal (data flowing through a sourcetype) or a weak one
    // (token overlap on an app name). Strength buckets:
    //   topWeight ≥ 4   → "strong"  (sourcetype exact/fuzzy)
    //   topWeight ≥ 1   → "medium"  (CIM model, app exact/substring,
    //                                 index ↔ sourcetype)
    //   topWeight  < 1  → "weak"    (token overlap, evidence-pack hit)
    if (row.topReason) {{
      var w = row.topWeight || 0;
      var strength = w >= 4 ? 'strong' : (w >= 1 ? 'medium' : 'weak');
      var chip = safeAppend(card, 'div', null, {{
        'class': 'uc-match-chip uc-match-' + strength,
        'title': 'Match strength: ' + strength
              + ' (score ' + (Math.round(w * 10) / 10) + ')',
      }});
      safeAppend(chip, 'span', '● ', {{ 'class': 'uc-match-dot' }});
      safeAppend(chip, 'span', 'Matched: ' + row.topReason);
    }}
    if (row.reasons && row.reasons.length > 1) {{
      var why = safeAppend(card, 'details', null, {{ 'class': 'uc-why' }});
      safeAppend(why, 'summary', 'Other matches (' + (row.reasons.length - 1) + ')');
      safeAppend(why, 'span', row.reasons.slice(1, 5).join('; '));
    }}
    var sbContainer = safeAppend(card, 'div', null, {{ 'class': 'uc-sb-container' }});
    renderRequiredSplunkbase(sbContainer, row.sb || []);
    var btnRow = safeAppend(card, 'div', null, {{ 'class': 'uc-btn-row' }});
    var detailBtn = safeAppend(btnRow, 'button', 'Details', {{
      'type': 'button',
      'class': 'uc-btn uc-btn-detail',
      'data-uc-id': row.id,
    }});
    detailBtn.addEventListener('click', function () {{
      openDetailDrawer(row);
    }});
    if (STATE.capability) {{
      var markBtn = safeAppend(btnRow, 'button', null, {{
        'type': 'button',
        'class': 'uc-btn uc-btn-mark',
        'data-uc-id': row.id,
      }});
      markBtn.textContent = (statusOf(row.id) === 'not_started')
        ? 'Mark as implemented'
        : 'Edit status';
      markBtn.addEventListener('click', function () {{
        openImplementationModal(row, markBtn);
      }});
    }}
    return card;
  }}

  // Modal a11y: role=dialog, aria-modal, focus trap, Escape closes,
  // focus-return on close. Per § 12d (WCAG 2.1 AA).
  function openImplementationModal(row, openerBtn) {{
    var existing = document.getElementById('uc-impl-modal');
    if (existing) existing.remove();
    var modal = document.createElement('div');
    modal.id = 'uc-impl-modal';
    modal.className = 'uc-modal-backdrop';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'uc-impl-modal-title');

    var dialog = safeAppend(modal, 'div', null, {{ 'class': 'uc-modal' }});
    safeAppend(dialog, 'h3', 'Update implementation status — UC ' + row.id, {{
      'id': 'uc-impl-modal-title',
    }});
    safeAppend(dialog, 'p', row.title || '');

    var statusLabel = safeAppend(dialog, 'label', 'Status');
    var select = safeAppend(dialog, 'select', null, {{
      'class': 'uc-modal-status',
      'aria-label': 'New status',
    }});
    FAST_PATH_STATUSES.concat(['needs_review']).forEach(function (s) {{
      var opt = safeAppend(select, 'option', STATUS_LABELS[s] || s, {{
        'value': s,
      }});
      if (statusOf(row.id) === s) opt.setAttribute('selected', 'selected');
    }});
    DESTRUCTIVE_STATUSES.forEach(function (s) {{
      safeAppend(select, 'option', STATUS_LABELS[s] || s, {{
        'value': s,
        'data-destructive': '1',
      }});
    }});

    safeAppend(dialog, 'label', 'Notes (max 2000 chars; CR/LF stripped)');
    var notes = safeAppend(dialog, 'textarea', null, {{
      'class': 'uc-modal-notes',
      'maxlength': 2000,
      'rows': 4,
    }});

    var msg = safeAppend(dialog, 'div', '', {{
      'class': 'uc-modal-msg',
      'role': 'alert',
      'aria-live': 'polite',
    }});

    var actions = safeAppend(dialog, 'div', null, {{ 'class': 'uc-modal-actions' }});
    var cancel = safeAppend(actions, 'button', 'Cancel', {{
      'type': 'button',
      'class': 'uc-btn uc-btn-cancel',
    }});
    var save = safeAppend(actions, 'button', 'Save', {{
      'type': 'button',
      'class': 'uc-btn uc-btn-save',
    }});

    function close() {{
      modal.remove();
      if (openerBtn && typeof openerBtn.focus === 'function') {{
        openerBtn.focus();
      }}
      document.removeEventListener('keydown', onKey);
    }}

    function trapFocus(forward) {{
      var focusables = dialog.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusables.length) return;
      var first = focusables[0];
      var last = focusables[focusables.length - 1];
      if (forward && document.activeElement === last) {{
        first.focus();
        return true;
      }}
      if (!forward && document.activeElement === first) {{
        last.focus();
        return true;
      }}
      return false;
    }}

    function onKey(e) {{
      if (e.key === 'Escape') {{
        e.preventDefault();
        close();
      }} else if (e.key === 'Tab') {{
        if (trapFocus(!e.shiftKey)) e.preventDefault();
      }}
    }}

    cancel.addEventListener('click', close);
    save.addEventListener('click', function () {{
      var newStatus = select.value;
      var notesVal = (notes.value || '').replace(/[\\r\\n]+/g, ' ').slice(0, 2000);
      if (!STATUS_LABELS[newStatus]) {{
        msg.textContent = 'Invalid status.';
        return;
      }}
      msg.textContent = 'Saving…';
      save.disabled = true;
      var op;
      if (DESTRUCTIVE_STATUSES.indexOf(newStatus) !== -1) {{
        op = dispatchDecommission(row.id, notesVal || 'Operator decommission');
      }} else {{
        op = persistImplementation(row.id, {{
          status: newStatus,
          notes: notesVal,
          marked_at: new Date().toISOString(),
        }});
      }}
      var optimistic = STATE.implementations || (STATE.implementations = {{}});
      var prev = optimistic[row.id];
      optimistic[row.id] = Object.assign({{}}, prev, {{
        uc_id: row.id,
        status: newStatus,
        notes: notesVal,
      }});
      // Re-render the badge in-place with the optimistic state.
      var badge = document.querySelector(
        '.uc-card[data-uc-id="' + CSS.escape(row.id) + '"] .uc-status-badge'
      );
      if (badge) {{
        badge.className = 'uc-status-badge uc-status-' + newStatus;
        badge.dataset.status = newStatus;
        badge.textContent = STATUS_LABELS[newStatus];
      }}
      op.then(function () {{
        msg.textContent = 'Saved. Reconciling with KV…';
        return reconcileStatus(row.id, newStatus);
      }}).then(function (matched) {{
        if (matched) {{
          close();
        }} else {{
          // Drift — revert optimistic change, surface message.
          if (prev) {{
            optimistic[row.id] = prev;
          }} else {{
            delete optimistic[row.id];
          }}
          if (badge) {{
            var revertedStatus = statusOf(row.id);
            badge.className = 'uc-status-badge uc-status-' + revertedStatus;
            badge.dataset.status = revertedStatus;
            badge.textContent = STATUS_LABELS[revertedStatus];
          }}
          msg.textContent = 'Status didn\\u2019t sync — try again.';
          save.disabled = false;
        }}
      }}).catch(function (err) {{
        msg.textContent = (err && err.message) ? err.message : String(err);
        save.disabled = false;
        // Revert optimistic update on failure.
        if (prev) {{
          optimistic[row.id] = prev;
        }} else {{
          delete optimistic[row.id];
        }}
        if (badge) {{
          var revertedStatus2 = statusOf(row.id);
          badge.className = 'uc-status-badge uc-status-' + revertedStatus2;
          badge.dataset.status = revertedStatus2;
          badge.textContent = STATUS_LABELS[revertedStatus2];
        }}
      }});
    }});

    document.body.appendChild(modal);
    document.addEventListener('keydown', onKey);
    select.focus();
    modal.addEventListener('click', function (ev) {{
      if (ev.target === modal) close();
    }});
  }}

  function searchDeepLink(query) {{
    // Link into the Search & Reporting app with URL-encoded SPL.
    var q = encodeURIComponent(query);
    return '../search/search?q=' + q + '&earliest=-24h&latest=now';
  }}

  function openDetailDrawer(row) {{
    var drawer = document.getElementById('uc-detail-drawer');
    if (!drawer) {{
      drawer = document.createElement('aside');
      drawer.id = 'uc-detail-drawer';
      drawer.className = 'uc-drawer';
      document.body.appendChild(drawer);
    }}
    drawer.textContent = '';
    var close = safeAppend(drawer, 'button', 'Close', {{ 'class': 'uc-close' }});
    close.addEventListener('click', function () {{
      drawer.classList.remove('open');
    }});
    var title = safeAppend(drawer, 'h3', 'UC ' + row.id);
    if (row.title) safeAppend(drawer, 'h4', row.title);
    safeAppend(drawer, 'p', row.value || '');
    safeAppend(drawer, 'p', 'Loading full sidecar…', {{ 'class': 'uc-loading' }});
    drawer.classList.add('open');

    var url = STATE.apiBase + '/compliance/ucs/' + row.id + '.json';
    fetchJson(url).then(function (sidecar) {{
      drawer.textContent = '';
      safeAppend(drawer, 'button', 'Close', {{ 'class': 'uc-close' }}).addEventListener('click', function () {{
        drawer.classList.remove('open');
      }});
      safeAppend(drawer, 'h3', 'UC ' + sidecar.id);
      safeAppend(drawer, 'h4', sidecar.title || row.title);
      safeAppend(drawer, 'p', sidecar.value || row.value || '');
      if (sidecar.spl) {{
        var codeBlock = safeAppend(drawer, 'pre', sidecar.spl, {{ 'class': 'uc-spl' }});
        var copy = safeAppend(drawer, 'button', 'Copy SPL', {{ 'class': 'uc-btn' }});
        copy.addEventListener('click', function () {{
          navigator.clipboard && navigator.clipboard.writeText(sidecar.spl);
        }});
        var open = safeAppend(drawer, 'a', 'Open in Search app', {{
          'class': 'uc-btn',
          'href': searchDeepLink(sidecar.spl),
          'target': '_blank',
          'rel': 'noopener noreferrer',
        }});
      }}
      if (sidecar.references && sidecar.references.length) {{
        var ul = safeAppend(drawer, 'ul', null, {{ 'class': 'uc-refs' }});
        sidecar.references.forEach(function (ref) {{
          var li = safeAppend(ul, 'li');
          var href = ref && ref.url ? safeLinkHref(ref.url) : null;
          if (href) {{
            safeAppend(li, 'a', ref.title || href, {{
              'href': href,
              'target': '_blank',
              'rel': 'noopener noreferrer',
            }});
          }} else {{
            safeAppend(li, 'span', ref.title || '');
          }}
        }});
      }}
    }}).catch(function (err) {{
      drawer.textContent = '';
      safeAppend(drawer, 'button', 'Close', {{ 'class': 'uc-close' }}).addEventListener('click', function () {{
        drawer.classList.remove('open');
      }});
      safeAppend(drawer, 'h3', 'UC ' + row.id);
      safeAppend(drawer, 'p', 'Could not load full sidecar: ' + (err.message || err));
    }});
  }}

  // URL-state helpers — persist filters across reloads & tabs (§ 12c).
  function readUrlState() {{
    try {{
      var params = new URLSearchParams(window.location.search || '');
      var equipParam = params.get('eq') || '';
      // Build 15 — additional facets so deep links survive reload.
      // ``eq`` carries a comma-separated list of equipment slugs.
      return {{
        text:           params.get('q')      || '',
        status:         params.get('status') || '',
        criticality:    params.get('crit')   || '',
        pillar:         params.get('pillar') || '',
        monitoringType: params.get('mtype')  || '',
        equipment:      equipParam ? equipParam.split(',').filter(Boolean) : [],
        sort:           params.get('sort')   || '',
      }};
    }} catch (err) {{
      return {{
        text: '', status: '', criticality: '',
        pillar: '', monitoringType: '', equipment: [], sort: '',
      }};
    }}
  }}

  function writeUrlState(state) {{
    if (!window.history || typeof window.history.replaceState !== 'function') return;
    try {{
      var url = new URL(window.location.href);
      var setOrDelete = function (key, value) {{
        if (value) url.searchParams.set(key, value);
        else        url.searchParams.delete(key);
      }};
      setOrDelete('q',      state.text);
      setOrDelete('status', state.status);
      setOrDelete('crit',   state.criticality);
      setOrDelete('pillar', state.pillar);
      setOrDelete('mtype',  state.monitoringType);
      setOrDelete('sort',   state.sort);
      var eq = (state.equipment || []).join(',');
      setOrDelete('eq', eq);
      window.history.replaceState(null, '', url.toString());
    }} catch (err) {{
      /* ignore — URL persistence is best-effort */
    }}
  }}

  function rowsToCsv(rows) {{
    var headers = ['uc_id', 'title', 'criticality', 'status', 'pillar', 'value', 'reasons'];
    var esc = function (v) {{
      var s = (v === null || v === undefined) ? '' : String(v);
      if (/[",\\r\\n]/.test(s)) {{
        s = '"' + s.replace(/"/g, '""') + '"';
      }}
      return s;
    }};
    var out = [headers.join(',')];
    rows.forEach(function (r) {{
      out.push([
        r.id,
        r.title || '',
        r.criticality || '',
        statusOf(r.id),
        r.splunkPillar || '',
        r.value || '',
        (r.reasons || []).join('; '),
      ].map(esc).join(','));
    }});
    return out.join('\\r\\n');
  }}

  function downloadCsv(filename, csv) {{
    var blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8' }});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () {{ URL.revokeObjectURL(url); }}, 5000);
  }}

  // Build 15 — central filter applied to BOTH the Recommend tab
  // (rows = matchUseCases output) and the Browse tab (rows = thin
  // entries). The state object carries every active toolbar control:
  //   text             freeform substring search across many fields
  //   status           implementation status (Recommend tab only)
  //   criticality      one of critical / high / medium / low / ''
  //   pillar           one of security / observability / platform / ''
  //   monitoringType   substring match against the row's mtype list
  //   equipment        array of equipment slugs; row matches if it
  //                    carries ANY of the selected slugs (OR logic)
  // Empty string / empty array / undefined ⇒ "no constraint".
  function applyFilters(rows, state) {{
    var f = (state.text || '').toLowerCase();
    var statusFilter = state.status || '';
    var critFilter = state.criticality || '';
    var pillarFilter = (state.pillar || '').toLowerCase();
    var mtypeFilter = (state.monitoringType || '').toLowerCase();
    var equipFilter = Array.isArray(state.equipment) ? state.equipment : [];
    return rows.filter(function (row) {{
      if (statusFilter && statusOf(row.id) !== statusFilter) return false;
      if (critFilter && (row.criticality || '') !== critFilter) return false;
      if (pillarFilter && (row.splunkPillar || '').toLowerCase() !== pillarFilter) return false;
      if (mtypeFilter) {{
        var mt = (row.monitoringType || []);
        var hit = false;
        for (var k = 0; k < mt.length; k++) {{
          if (String(mt[k]).toLowerCase() === mtypeFilter) {{ hit = true; break; }}
        }}
        if (!hit) return false;
      }}
      if (equipFilter.length) {{
        var eq = (row.equipment || []);
        var hitEq = false;
        for (var ei = 0; ei < eq.length; ei++) {{
          if (equipFilter.indexOf(String(eq[ei])) !== -1) {{ hitEq = true; break; }}
        }}
        if (!hitEq) return false;
      }}
      if (f) {{
        // Build 15 — extend the search hay to every metadata facet
        // the user might reasonably look up. Previously this only
        // searched id + title + value + reasons, which missed common
        // queries like "MITRE T1110" or "OPC-UA equipment" or
        // "endpoint cim".
        var hay = (
          row.id + ' ' +
          (row.title || '') + ' ' +
          (row.value || '') + ' ' +
          (row.reasons || []).join(' ') + ' ' +
          (row.equipment || []).join(' ') + ' ' +
          (row.equipmentModels || []).join(' ') + ' ' +
          (row.cimModels || []).join(' ') + ' ' +
          (row.mitreAttack || []).join(' ') + ' ' +
          (row.monitoringType || []).join(' ') + ' ' +
          (row.app || []).join(' ') + ' ' +
          (row.splunkPillar || '')
        ).toLowerCase();
        if (hay.indexOf(f) === -1) return false;
      }}
      return true;
    }});
  }}

  // Build 15 — derive a stable, sorted union of equipment slugs from
  // a row set so the toolbar dropdown can offer real options. We
  // de-dup case-insensitively but keep the original-cased label.
  function equipmentOptions(rows) {{
    var seen = {{}};
    var out = [];
    for (var i = 0; i < rows.length; i++) {{
      var eq = (rows[i].equipment || []);
      for (var j = 0; j < eq.length; j++) {{
        var slug = String(eq[j] || '').trim();
        if (!slug) continue;
        var key = slug.toLowerCase();
        if (seen[key]) continue;
        seen[key] = 1;
        out.push(slug);
      }}
    }}
    out.sort(function (a, b) {{ return a.toLowerCase().localeCompare(b.toLowerCase()); }});
    return out;
  }}

  // Build 15 — Sort comparator factory. The "relevance" mode exists
  // ONLY for the Recommend tab where rows carry ``_score``; the
  // Browse tab uses "id" (the natural lexical UC-id sort) instead.
  var CRIT_RANK = {{ 'critical': 0, 'high': 1, 'medium': 2, 'low': 3 }};
  function sortRows(rows, by) {{
    var sorted = rows.slice();
    if (by === 'criticality') {{
      sorted.sort(function (a, b) {{
        var ra = CRIT_RANK[a.criticality];
        var rb = CRIT_RANK[b.criticality];
        if (ra === undefined) ra = 4;
        if (rb === undefined) rb = 4;
        if (ra !== rb) return ra - rb;
        return String(a.id).localeCompare(String(b.id));
      }});
    }} else if (by === 'title') {{
      sorted.sort(function (a, b) {{
        return String(a.title || '').toLowerCase()
                 .localeCompare(String(b.title || '').toLowerCase());
      }});
    }} else if (by === 'equipment') {{
      sorted.sort(function (a, b) {{
        var ea = ((a.equipment || [])[0] || '~').toLowerCase();   // '~' sorts last
        var eb = ((b.equipment || [])[0] || '~').toLowerCase();
        if (ea !== eb) return ea.localeCompare(eb);
        return String(a.id).localeCompare(String(b.id));
      }});
    }} else if (by === 'category') {{
      sorted.sort(function (a, b) {{
        var ca = parseInt(String(a.id).split('.')[0], 10) || 0;
        var cb = parseInt(String(b.id).split('.')[0], 10) || 0;
        if (ca !== cb) return ca - cb;
        return String(a.id).localeCompare(String(b.id));
      }});
    }} else if (by === 'id') {{
      sorted.sort(function (a, b) {{
        return String(a.id).localeCompare(String(b.id));
      }});
    }}
    // by === 'relevance' OR unknown ⇒ leave as-is (matchUseCases
    // already returned the rows in score-then-diversification order).
    return sorted;
  }}

  // Build a structured diagnostics view shown when ``matchUseCases``
  // returns []. Replaces the build-9 / build-10 single-sentence
  // "No matches yet" empty state, which gave operators no way to tell
  // whether the inventory failed to load (SearchManager race, build 11
  // fix), the catalogue endpoints failed to load, or the inventory
  // simply didn't overlap with anything in the upstream catalogue.
  // The diagnostics renderer reads STATE.inventory + STATE.indexes and
  // surfaces:
  //   - Inventory size by type (sourcetype/index/cim/app)
  //   - Catalogue index sizes (with greens / reds for missing endpoints)
  //   - Per-type overlap counters (X of Y inventory items have a match)
  //   - Sample names from BOTH sides so operators can spot
  //     case / suffix / prefix mismatches at a glance.
  function renderDiagnostics(parent) {{
    var details = safeAppend(parent, 'details', null, {{
      'class': 'uc-diagnostics',
      'role': 'group',
      'aria-label': 'Recommender diagnostics',
    }});
    // Auto-expand the diagnostics panel when there are zero matches —
    // the operator's whole job here is to figure out why.
    details.setAttribute('open', 'open');
    var summary = safeAppend(details, 'summary');
    summary.textContent = 'Diagnostics';

    var inv = STATE.inventory || [];
    var ix = STATE.indexes || {{}};
    var sIx = ix.sourcetypes || {{}};
    var cIx = ix.cim || {{}};
    var aIx = ix.apps || {{}};
    var thinIx = ix.thin || {{}};

    function bucket(rows, predicate) {{
      var out = [];
      for (var i = 0; i < rows.length; i++) {{
        if (predicate(rows[i])) out.push(rows[i]);
      }}
      return out;
    }}

    var invST  = bucket(inv, function (r) {{ return r && r.type === 'sourcetype'; }});
    var invIDX = bucket(inv, function (r) {{ return r && r.type === 'index'; }});
    var invCIM = bucket(inv, function (r) {{ return r && r.type === 'cim_model'; }});
    var invCIMA = bucket(invCIM, function (r) {{
      return (r.extras || '').indexOf('accelerated') !== -1;
    }});
    var invAPP = bucket(inv, function (r) {{ return r && r.type === 'app'; }});

    function renderTable(parent, rows) {{
      var table = safeAppend(parent, 'table', null, {{ 'class': 'uc-diag-table' }});
      var tbody = safeAppend(table, 'tbody');
      rows.forEach(function (row) {{
        var tr = safeAppend(tbody, 'tr');
        safeAppend(tr, 'td', row[0], {{ 'class': 'uc-diag-label' }});
        var valueCell = safeAppend(tr, 'td', null, {{ 'class': 'uc-diag-value' }});
        if (row[2] === 'ok') valueCell.classList.add('uc-diag-ok');
        if (row[2] === 'warn') valueCell.classList.add('uc-diag-warn');
        if (row[2] === 'bad') valueCell.classList.add('uc-diag-bad');
        valueCell.textContent = String(row[1]);
      }});
      return table;
    }}

    // --- Section 1: Inventory loaded ---
    safeAppend(details, 'h4', 'Inventory loaded from this Splunk instance');
    var invStatus = inv.length === 0 ? 'bad' : 'ok';
    renderTable(details, [
      ['Total rows',           inv.length, invStatus],
      ['Sourcetypes',          invST.length,  invST.length  ? 'ok' : 'warn'],
      ['Indexes',              invIDX.length, invIDX.length ? 'ok' : 'warn'],
      ['CIM models (any)',     invCIM.length, invCIM.length ? 'ok' : 'warn'],
      ['CIM models (accel.)',  invCIMA.length + ' / ' + invCIM.length,
                                                            invCIMA.length ? 'ok' : 'warn'],
      ['Apps',                 invAPP.length, invAPP.length ? 'ok' : 'warn'],
    ]);

    if (inv.length === 0) {{
      var p = safeAppend(details, 'p', null, {{ 'class': 'uc-diag-explain' }});
      p.textContent = 'Inventory is empty. The dashboard tiles above use a '
        + 'separate Simple-XML search; if they show non-zero counts but '
        + 'this row is 0, the in-page SearchManager dispatch is racing '
        + 'with results delivery (the build-11 fix should prevent this — '
        + 'reload the page and re-check). If the tiles also show 0, run '
        + 'the four "Recommender — *" saved searches in '
        + 'Settings → Searches, reports, and alerts.';
      return;
    }}

    // --- Section 2: Catalogue indexes loaded ---
    safeAppend(details, 'h4', 'Catalogue indexes (upstream)');
    var sCount = Object.keys(sIx).length;
    var cCount = Object.keys(cIx).length;
    var aCount = Object.keys(aIx).length;
    var tCount = Object.keys(thinIx).length;
    var bCount = STATE.splunkbaseIndex ? Object.keys(STATE.splunkbaseIndex).length : 0;
    renderTable(details, [
      ['Sourcetype index',   sCount, sCount ? 'ok' : 'bad'],
      ['CIM index',          cCount, cCount ? 'ok' : 'bad'],
      ['App index',          aCount, aCount ? 'ok' : 'bad'],
      ['Use-case (thin)',    tCount, tCount ? 'ok' : 'bad'],
      ['Splunkbase metadata', bCount, bCount ? 'ok' : 'warn'],
    ]);

    // --- Section 3: Per-type overlap analysis ---
    safeAppend(details, 'h4', 'Overlap analysis');

    var stHits = 0; var stExact = []; var stFuzzy = []; var stNone = [];
    for (var i = 0; i < invST.length; i++) {{
      var n = (invST[i].name || '').toLowerCase();
      if (!n) continue;
      if (sIx[n]) {{ stHits += 1; stExact.push(invST[i].name); continue; }}
      var fuzzy = false;
      var keys = Object.keys(sIx);
      for (var j = 0; j < keys.length; j++) {{
        if (keys[j].indexOf(n) !== -1 || n.indexOf(keys[j]) !== -1) {{
          fuzzy = true; break;
        }}
      }}
      if (fuzzy) {{ stFuzzy.push(invST[i].name); }} else {{ stNone.push(invST[i].name); }}
    }}

    var cimHits = 0; var cimNone = [];
    for (var k = 0; k < invCIMA.length; k++) {{
      if (cIx[invCIMA[k].name]) cimHits += 1; else cimNone.push(invCIMA[k].name);
    }}

    var appHits = 0; var appExamples = [];
    var cleanAppKeys = Object.keys(aIx).filter(looksLikeAppKey);
    var cleanAppKeysLower = cleanAppKeys.map(function (k2) {{ return k2.toLowerCase(); }});
    for (var m = 0; m < invAPP.length; m++) {{
      var nameLower = (invAPP[m].name || '').toLowerCase();
      var extrasLower = (invAPP[m].extras || '').toLowerCase();
      var hit = false;
      for (var p2 = 0; p2 < cleanAppKeysLower.length; p2++) {{
        var ck = cleanAppKeysLower[p2];
        if (!ck) continue;
        if (ck === nameLower || ck === extrasLower
            || (nameLower && (ck.indexOf(nameLower) !== -1 || nameLower.indexOf(ck) !== -1))
            || (extrasLower && (ck.indexOf(extrasLower) !== -1 || extrasLower.indexOf(ck) !== -1))) {{
          hit = true; break;
        }}
      }}
      if (hit) {{
        appHits += 1;
        if (appExamples.length < 5) appExamples.push(invAPP[m].name);
      }}
    }}

    renderTable(details, [
      ['Sourcetype exact matches',  stExact.length + ' / ' + invST.length,
                                                                  stExact.length ? 'ok' : 'warn'],
      ['Sourcetype fuzzy matches',  stFuzzy.length + ' / ' + invST.length,
                                                                  stFuzzy.length ? 'ok' : 'warn'],
      ['CIM model accelerated matches', cimHits + ' / ' + invCIMA.length,
                                                                  cimHits ? 'ok' : 'warn'],
      ['App matches (any)',          appHits + ' / ' + invAPP.length,
                                                                  appHits ? 'ok' : 'warn'],
    ]);

    // --- Section 4: Examples to spot mismatches ---
    function listSample(parent, label, items) {{
      if (!items || !items.length) return;
      var h = safeAppend(parent, 'h5', label);
      var ul = safeAppend(parent, 'ul', null, {{ 'class': 'uc-diag-list' }});
      items.slice(0, 8).forEach(function (it) {{
        var li = safeAppend(ul, 'li');
        li.textContent = String(it);
      }});
      if (items.length > 8) {{
        var more = safeAppend(parent, 'p', '+' + (items.length - 8) + ' more', {{
          'class': 'uc-diag-more',
        }});
      }}
    }}

    var examples = safeAppend(details, 'div', null, {{ 'class': 'uc-diag-examples' }});
    listSample(examples, 'Inventory sourcetypes (sample)', invST.map(function (r) {{ return r.name; }}));
    listSample(examples, 'Catalogue sourcetypes (sample)', Object.keys(sIx));
    listSample(examples, 'Inventory apps (sample)', invAPP.map(function (r) {{
      return r.name + (r.extras ? ' [' + r.extras + ']' : '');
    }}));
    listSample(examples, 'Catalogue app keys (clean, sample)', cleanAppKeys);
    listSample(examples, 'Sourcetypes with NO catalogue match (first 8)', stNone);
    listSample(examples, 'Sourcetypes with EXACT catalogue match (first 8)', stExact);

    // --- Section 5: Plain-language guidance ---
    var guide = safeAppend(details, 'p', null, {{ 'class': 'uc-diag-explain' }});
    if (sCount === 0 || aCount === 0) {{
      guide.textContent = 'The catalogue endpoints did not load. Check the '
        + 'banner above (if any) and confirm this Splunk host can reach '
        + 'fenre.github.io. Workgroup proxies often need an allow-list '
        + 'entry for *.github.io.';
    }} else if (stHits === 0 && cimHits === 0 && appHits === 0) {{
      guide.textContent = 'Catalogue indexes loaded but your inventory does '
        + 'not overlap them. Common causes: case mismatch (e.g. '
        + '"WinEventLog:Security" vs lower-case keys), niche internal '
        + 'sourcetypes not yet in the catalogue, or apps whose label / '
        + 'folder differ from upstream conventions. Compare the samples '
        + 'above for hints — the matcher does case-insensitive substring '
        + 'so anything close should match.';
    }} else {{
      guide.textContent = 'Catalogue indexes loaded and overlap was '
        + 'detected. If the recommendation list above is still empty, '
        + 'the matched UCs may all be hidden by the criticality / '
        + 'status filters; clear the filters in the toolbar and retry.';
    }}
  }}

  function renderRecommendations(root, rows) {{
    if (!rows.length) {{
      var empty = safeAppend(root, 'div', null, {{ 'class': 'uc-empty', 'role': 'status' }});
      safeAppend(empty, 'p', 'No matches yet.');
      safeAppend(empty, 'p', 'Run the Scan tab once, wait for ingestion, then refresh — '
        + 'the recommender needs at least one inventory row before it can match.');
      renderDiagnostics(root);
      return;
    }}
    var state = readUrlState();
    // Toolbar: text + status + criticality + equipment + sort + CSV export.
    // Build 15 added equipment dropdown and sort dropdown.
    var toolbar = safeAppend(root, 'div', null, {{ 'class': 'uc-toolbar' }});
    var search = safeAppend(toolbar, 'input', null, {{
      'type': 'search',
      'placeholder': 'Filter by id, title, equipment, MITRE, CIM, app…',
      'class': 'uc-filter',
      'value': state.text,
      'aria-label': 'Filter recommendations',
    }});
    var statusSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-status-filter',
      'aria-label': 'Filter by implementation status',
    }});
    safeAppend(statusSel, 'option', 'All statuses', {{ 'value': '' }});
    Object.keys(STATUS_LABELS).forEach(function (s) {{
      var opt = safeAppend(statusSel, 'option', STATUS_LABELS[s], {{ 'value': s }});
      if (s === state.status) opt.setAttribute('selected', 'selected');
    }});
    var critSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-crit-filter',
      'aria-label': 'Filter by criticality',
    }});
    safeAppend(critSel, 'option', 'All criticality', {{ 'value': '' }});
    ['critical', 'high', 'medium', 'low'].forEach(function (c) {{
      var opt = safeAppend(critSel, 'option', c, {{ 'value': c }});
      if (c === state.criticality) opt.setAttribute('selected', 'selected');
    }});
    // Build 15 — equipment dropdown (single-select for layout reasons;
    // multi-select would require a custom widget). The "All equipment"
    // option clears the constraint. Options are computed once from the
    // full unfiltered ``rows`` so the menu doesn't shrink as the user
    // narrows the selection.
    var equipSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-equip-filter',
      'aria-label': 'Filter by equipment',
    }});
    safeAppend(equipSel, 'option', 'All equipment', {{ 'value': '' }});
    equipmentOptions(rows).forEach(function (slug) {{
      var opt = safeAppend(equipSel, 'option', slug, {{ 'value': slug }});
      if ((state.equipment || []).indexOf(slug) !== -1) {{
        opt.setAttribute('selected', 'selected');
      }}
    }});
    // Build 15 — sort dropdown. "Relevance" is the default and uses the
    // matchUseCases score-then-diversification order. Other modes sort
    // the already-filtered slice.
    var sortSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-sort-filter',
      'aria-label': 'Sort recommendations',
    }});
    var sortOptions = [
      ['',            'Sort: Relevance'],
      ['criticality', 'Sort: Criticality'],
      ['equipment',   'Sort: Equipment'],
      ['category',    'Sort: Category'],
      ['title',       'Sort: Title (A-Z)'],
    ];
    sortOptions.forEach(function (pair) {{
      var opt = safeAppend(sortSel, 'option', pair[1], {{ 'value': pair[0] }});
      if (pair[0] === (state.sort || '')) opt.setAttribute('selected', 'selected');
    }});
    var exportBtn = safeAppend(toolbar, 'button', 'Export CSV', {{
      'type': 'button',
      'class': 'uc-btn uc-btn-export',
    }});
    var counter = safeAppend(toolbar, 'span', '', {{ 'class': 'uc-toolbar-count' }});

    var grid = safeAppend(root, 'div', null, {{ 'class': 'uc-grid' }});

    function refresh() {{
      grid.textContent = '';
      var filtered = applyFilters(rows, state);
      filtered = sortRows(filtered, state.sort || 'relevance');
      counter.textContent = 'Showing ' + Math.min(filtered.length, 60)
        + ' of ' + filtered.length + ' (of ' + rows.length + ' total)';
      filtered.slice(0, 60).forEach(function (row) {{
        renderCard(grid, row);
      }});
      if (filtered.length === 0) {{
        var noResults = safeAppend(grid, 'p', 'No use cases match the current filters.', {{
          'class': 'uc-empty',
          'role': 'status',
        }});
      }}
    }}

    search.addEventListener('input', function (e) {{
      state.text = e.target.value;
      writeUrlState(state); refresh();
    }});
    statusSel.addEventListener('change', function (e) {{
      state.status = e.target.value;
      writeUrlState(state); refresh();
    }});
    critSel.addEventListener('change', function (e) {{
      state.criticality = e.target.value;
      writeUrlState(state); refresh();
    }});
    equipSel.addEventListener('change', function (e) {{
      state.equipment = e.target.value ? [e.target.value] : [];
      writeUrlState(state); refresh();
    }});
    sortSel.addEventListener('change', function (e) {{
      state.sort = e.target.value;
      writeUrlState(state); refresh();
    }});
    exportBtn.addEventListener('click', function () {{
      var filtered = applyFilters(rows, state);
      filtered = sortRows(filtered, state.sort || 'relevance');
      var ts = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19);
      downloadCsv('uc-recommender-' + ts + '.csv', rowsToCsv(filtered));
    }});

    refresh();
  }}

  function renderBrowse(root, thin) {{
    root.textContent = '';
    // Build 15 — Browse tab now uses the same applyFilters + sortRows
    // pipeline as the Recommend tab. Previous implementation searched
    // only id/title/value with no facet filters and no sort control,
    // which made it useless for "show me everything tagged ``meraki``"
    // or "show me Critical UCs in pillar=Security" queries.
    var rows = Object.keys(thin).sort().map(function (id) {{ return thin[id]; }});
    var state = readUrlState();
    // Default Browse sort is "id" so the page is stable on initial
    // load (matchUseCases ordering doesn't apply here — these aren't
    // recommendations).
    if (!state.sort) state.sort = 'id';

    var summary = safeAppend(root, 'p', 'Showing ' + rows.length + ' use cases.', {{
      'class': 'uc-browse-summary',
    }});

    var toolbar = safeAppend(root, 'div', null, {{ 'class': 'uc-toolbar uc-toolbar-browse' }});
    var input = safeAppend(toolbar, 'input', null, {{
      'type': 'search',
      'placeholder': 'Filter id, title, equipment, MITRE, CIM, app, pillar…',
      'class': 'uc-filter',
      'value': state.text,
      'aria-label': 'Filter use cases',
    }});
    // Criticality filter
    var critSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-crit-filter',
      'aria-label': 'Filter by criticality',
    }});
    safeAppend(critSel, 'option', 'All criticality', {{ 'value': '' }});
    ['critical', 'high', 'medium', 'low'].forEach(function (c) {{
      var opt = safeAppend(critSel, 'option', c, {{ 'value': c }});
      if (c === state.criticality) opt.setAttribute('selected', 'selected');
    }});
    // Pillar filter — derived from the row set, lower-cased to dedup.
    var pillarSet = {{}};
    rows.forEach(function (r) {{
      var p = (r.splunkPillar || '').toString().trim();
      if (p) pillarSet[p.toLowerCase()] = p;
    }});
    var pillarSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-pillar-filter',
      'aria-label': 'Filter by Splunk pillar',
    }});
    safeAppend(pillarSel, 'option', 'All pillars', {{ 'value': '' }});
    Object.keys(pillarSet).sort().forEach(function (k) {{
      var opt = safeAppend(pillarSel, 'option', pillarSet[k], {{ 'value': k }});
      if (k === (state.pillar || '').toLowerCase()) opt.setAttribute('selected', 'selected');
    }});
    // Monitoring-type filter — same pattern but on the array field.
    var mtypeSet = {{}};
    rows.forEach(function (r) {{
      (r.monitoringType || []).forEach(function (m) {{
        if (m) mtypeSet[String(m).toLowerCase()] = String(m);
      }});
    }});
    var mtypeSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-mtype-filter',
      'aria-label': 'Filter by monitoring type',
    }});
    safeAppend(mtypeSel, 'option', 'All monitoring types', {{ 'value': '' }});
    Object.keys(mtypeSet).sort().forEach(function (k) {{
      var opt = safeAppend(mtypeSel, 'option', mtypeSet[k], {{ 'value': k }});
      if (k === (state.monitoringType || '').toLowerCase()) opt.setAttribute('selected', 'selected');
    }});
    // Equipment filter — derived from union of rows.equipment.
    var equipSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-equip-filter',
      'aria-label': 'Filter by equipment',
    }});
    safeAppend(equipSel, 'option', 'All equipment', {{ 'value': '' }});
    equipmentOptions(rows).forEach(function (slug) {{
      var opt = safeAppend(equipSel, 'option', slug, {{ 'value': slug }});
      if ((state.equipment || []).indexOf(slug) !== -1) {{
        opt.setAttribute('selected', 'selected');
      }}
    }});
    // Sort dropdown — Browse defaults to "id".
    var sortSel = safeAppend(toolbar, 'select', null, {{
      'class': 'uc-sort-filter',
      'aria-label': 'Sort use cases',
    }});
    [
      ['id',          'Sort: ID'],
      ['title',       'Sort: Title (A-Z)'],
      ['criticality', 'Sort: Criticality'],
      ['equipment',   'Sort: Equipment'],
      ['category',    'Sort: Category'],
    ].forEach(function (pair) {{
      var opt = safeAppend(sortSel, 'option', pair[1], {{ 'value': pair[0] }});
      if (pair[0] === state.sort) opt.setAttribute('selected', 'selected');
    }});
    var counter = safeAppend(toolbar, 'span', '', {{ 'class': 'uc-toolbar-count' }});

    var grid = safeAppend(root, 'div', null, {{ 'class': 'uc-grid' }});

    function refresh() {{
      grid.textContent = '';
      // Browse mode never filters on implementation status — leave
      // ``state.status`` blank so applyFilters skips that branch.
      state.status = '';
      var filtered = applyFilters(rows, state);
      filtered = sortRows(filtered, state.sort || 'id');
      counter.textContent = 'Showing ' + filtered.length + ' of ' + rows.length;
      // Paginate at 200 to keep the DOM bounded; users searching
      // beyond that should narrow filters first.
      var slice = filtered.slice(0, 200);
      slice.forEach(function (row) {{ renderCard(grid, row); }});
      if (filtered.length > slice.length) {{
        safeAppend(grid, 'p',
          'Showing first ' + slice.length + ' of ' + filtered.length
          + '. Narrow the filters to see more.',
          {{ 'class': 'uc-empty', 'role': 'status' }});
      }} else if (filtered.length === 0) {{
        safeAppend(grid, 'p', 'No use cases match the current filters.', {{
          'class': 'uc-empty', 'role': 'status',
        }});
      }}
    }}

    input.addEventListener('input', function (e) {{
      state.text = e.target.value; writeUrlState(state); refresh();
    }});
    critSel.addEventListener('change', function (e) {{
      state.criticality = e.target.value; writeUrlState(state); refresh();
    }});
    pillarSel.addEventListener('change', function (e) {{
      state.pillar = e.target.value; writeUrlState(state); refresh();
    }});
    mtypeSel.addEventListener('change', function (e) {{
      state.monitoringType = e.target.value; writeUrlState(state); refresh();
    }});
    equipSel.addEventListener('change', function (e) {{
      state.equipment = e.target.value ? [e.target.value] : [];
      writeUrlState(state); refresh();
    }});
    sortSel.addEventListener('change', function (e) {{
      state.sort = e.target.value; writeUrlState(state); refresh();
    }});

    refresh();
  }}

  function renderSettings(root) {{
    root.textContent = '';
    safeAppend(root, 'h3', 'Recommender settings');
    safeAppend(root, 'p', 'Override the upstream catalogue URL (advanced — usually leave blank).');
    var form = safeAppend(root, 'form', null, {{ 'class': 'uc-settings' }});
    var lbl = safeAppend(form, 'label', 'API base URL');
    var input = safeAppend(form, 'input', null, {{
      'type': 'url',
      'pattern': 'https://.*',
      'value': STATE.apiBase,
      'class': 'uc-apibase',
      'size': 80,
    }});
    var save = safeAppend(form, 'button', 'Save', {{ 'type': 'submit', 'class': 'uc-btn' }});
    var msg = safeAppend(form, 'div', '', {{ 'class': 'uc-msg' }});
    form.addEventListener('submit', function (e) {{
      e.preventDefault();
      try {{
        storeOperatorApiBase(input.value);
        msg.textContent = 'Saved. Reload the Recommend tab to fetch.';
      }} catch (err) {{
        msg.textContent = String(err.message || err);
      }}
    }});
    var clearBtn = safeAppend(root, 'button', 'Reset to default', {{ 'class': 'uc-btn' }});
    clearBtn.addEventListener('click', function () {{
      try {{ window.localStorage.removeItem('uc_recommender_api_base'); }} catch (err) {{}}
      input.value = DEFAULT_API_BASE;
      msg.textContent = 'Reset.';
    }});
  }}

  function renderUpstreamBanner(target) {{
    var keys = Object.keys(STATE.upstreamErrors || {{}});
    if (!keys.length) return;
    var banner = safeAppend(target, 'div', null, {{
      'class': 'uc-banner uc-banner-warn',
      'role': 'alert',
    }});
    safeAppend(banner, 'strong', 'Some catalogue endpoints failed: ');
    var msgs = keys.map(function (k) {{ return k + ' (' + STATE.upstreamErrors[k] + ')'; }});
    safeAppend(banner, 'span', msgs.join('; '));
  }}

  function renderReadOnlyBanner(target) {{
    if (STATE.capability) return;
    var banner = safeAppend(target, 'div', null, {{
      'class': 'uc-banner uc-banner-info',
      'role': 'note',
    }});
    safeAppend(banner, 'strong', 'Read-only mode: ');
    safeAppend(banner, 'span',
      'You do not hold the edit_uc_implementations capability. ' +
      'Status updates are disabled; ask an admin or power user.');
  }}

  function boot() {{
    var root = document.getElementById('uc-recommender-root');
    var browseRoot = document.getElementById('uc-recommender-browse-root');
    var settingsRoot = document.getElementById('uc-recommender-settings-root');
    var studioRoot = document.getElementById('uc-recommender-studio-root');
    STATE.apiBase = loadOperatorApiBase();
    if (root) root.setAttribute('data-api-base', STATE.apiBase);

    if (settingsRoot) {{
      renderSettings(settingsRoot);
      return;
    }}

    if (browseRoot) {{
      loadRemoteIndexes(STATE.apiBase).then(function (indexes) {{
        STATE.indexes = indexes;
        renderBrowse(browseRoot, indexes.thin);
      }}).catch(function (err) {{
        browseRoot.textContent = '';
        safeAppend(browseRoot, 'p', 'Could not load catalogue: ' + (err.message || err));
      }});
      return;
    }}

    var target = root || studioRoot;
    if (!target) return;
    target.textContent = '';
    safeAppend(target, 'p', 'Scanning…', {{ 'class': 'uc-loading' }});

    Promise.all([
      loadRemoteIndexes(STATE.apiBase),
      loadInventory(),
      loadImplementations(),
      loadCapability(),
    ]).then(function (parts) {{
      STATE.indexes = parts[0];
      STATE.inventory = parts[1];
      STATE.implementations = parts[2] || {{}};
      STATE.capability = !!parts[3];
      var recs = matchUseCases(STATE.inventory, STATE.indexes);
      STATE.recommendations = recs;
      target.textContent = '';
      renderUpstreamBanner(target);
      renderReadOnlyBanner(target);
      renderRecommendations(target, recs);
    }}).catch(function (err) {{
      target.textContent = '';
      renderUpstreamBanner(target);
      safeAppend(target, 'p', 'Recommender could not load: ' + (err.message || err));
    }});
  }}

  if (document.readyState === 'complete' || document.readyState === 'interactive') {{
    setTimeout(boot, 0);
  }} else {{
    document.addEventListener('DOMContentLoaded', boot);
  }}

  // Expose helpers for unit tests.
  window.__uc_recommender__ = {{
    matchUseCases: matchUseCases,
    score: score,
    validOrigin: validOrigin,
    safeLinkHref: safeLinkHref,
    statusOf: statusOf,
    safeSplunkbaseUrl: safeSplunkbaseUrl,
    state: STATE,
    renderCard: renderCard,
    renderStatusBadge: renderStatusBadge,
    renderRequiredSplunkbase: renderRequiredSplunkbase,
    openImplementationModal: openImplementationModal,
    persistImplementation: persistImplementation,
    dispatchDecommission: dispatchDecommission,
    reconcileStatus: reconcileStatus,
    loadRemoteIndexes: loadRemoteIndexes,
    loadImplementations: loadImplementations,
    loadInventory: loadInventory,
    loadCapability: loadCapability,
    runSearchJob: runSearchJob,
    STATUS_LABELS: STATUS_LABELS,
    DESTRUCTIVE_STATUSES: DESTRUCTIVE_STATUSES,
    REQUIRED_CAPABILITY: REQUIRED_CAPABILITY,
  }};
}})();
"""
    return body


def _js_scanner() -> str:
    return f"""{GENERATED_JS_BANNER}
/* eslint-disable */
(function () {{
  'use strict';

  // Convenience wrappers around the inventory KV store. The main
  // recommender.js already calls these directly; scanner.js is kept as a
  // separate entry point so operators can load it on any Simple XML page
  // to surface the scan tables without the full recommender UI.

  function runJob(spl) {{
    if (typeof require !== 'function') {{
      return Promise.reject(new Error('Not running inside Splunk Web'));
    }}
    return new Promise(function (resolve, reject) {{
      require(['splunkjs/mvc', 'splunkjs/mvc/searchmanager'], function (mvc, SearchManager) {{
        var name = 'uc_scanner_' + Math.random().toString(36).slice(2);
        var sm = new SearchManager({{
          id: name,
          search: spl,
          earliest_time: '-15m',
          latest_time: 'now',
          autostart: true,
          preview: false,
          cache: true,
        }});
        var results = sm.data('results', {{ count: 10000 }});
        results.on('data', function () {{
          resolve((results.data() || {{}}).results || []);
        }});
        sm.on('search:error', reject);
      }});
    }});
  }}

  window.UcScanner = {{
    sourcetypes: function () {{
      return runJob('| inputlookup uc_recommender_inventory | where type="sourcetype"');
    }},
    indexes: function () {{
      return runJob('| inputlookup uc_recommender_inventory | where type="index"');
    }},
    cim: function () {{
      return runJob('| inputlookup uc_recommender_inventory | where type="cim_model"');
    }},
    apps: function () {{
      return runJob('| inputlookup uc_recommender_inventory | where type="app"');
    }},
    runs: function () {{
      return runJob('| inputlookup uc_recommender_scan_runs | sort - run_at');
    }},
  }};
}})();
"""


def _js_uc_card() -> str:
    return f"""{GENERATED_JS_BANNER}
/* eslint-disable */
(function () {{
  'use strict';

  // Standalone UC-card renderer, useful for embedding in other dashboards
  // that just want to show a single UC preview. Called as
  //   window.UcCard.render(parent, ucRecord)
  // where ucRecord is one of the rows from /api/v1/recommender/uc-thin.json.

  function safe(parent, tag, text, attrs) {{
    var el = document.createElement(tag);
    if (text) el.appendChild(document.createTextNode(String(text)));
    if (attrs) Object.keys(attrs).forEach(function (k) {{ el.setAttribute(k, attrs[k]); }});
    parent.appendChild(el);
    return el;
  }}

  window.UcCard = {{
    render: function (parent, row) {{
      if (!row || !parent) return;
      var card = safe(parent, 'div', null, {{ 'class': 'uc-card uc-crit-' + (row.criticality || 'medium') }});
      var head = safe(card, 'div', null, {{ 'class': 'uc-card-head' }});
      safe(head, 'span', 'UC ' + row.id, {{ 'class': 'uc-id' }});
      safe(head, 'span', row.criticality || '', {{ 'class': 'uc-crit' }});
      safe(card, 'h4', row.title || row.id);
      if (row.value) safe(card, 'p', row.value, {{ 'class': 'uc-value' }});
      return card;
    }},
  }};
}})();
"""


def _css_recommender() -> str:
    return f"""{GENERATED_CSS_BANNER}
.uc-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  margin-top: 12px;
}}
.uc-card {{
  border: 1px solid #d8d8d8;
  border-left: 6px solid #65a637;
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}}
.uc-crit-critical {{ border-left-color: #d93f3c; }}
.uc-crit-high {{ border-left-color: #f58f39; }}
.uc-crit-medium {{ border-left-color: #f7bc38; }}
.uc-crit-low {{ border-left-color: #6db7c6; }}
.uc-card-head {{
  display: flex;
  gap: 8px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #666;
  margin-bottom: 4px;
}}
.uc-id {{ font-weight: 600; color: #333; }}
.uc-crit {{ color: #d93f3c; }}
.uc-pillar {{ color: #4a4a4a; }}
.uc-card h4 {{ margin: 4px 0; color: #222; }}
.uc-value {{ font-size: 13px; color: #555; margin: 4px 0 8px; }}
.uc-why {{ font-size: 12px; color: #4a4a4a; margin-bottom: 8px; }}
.uc-why summary {{ cursor: pointer; font-weight: 600; color: #4a4a4a; padding: 2px 0; }}
.uc-why summary:hover {{ color: #255a15; }}
.uc-why span {{ display: block; padding: 4px 0 0 12px; }}
.uc-match-chip {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px 3px 6px;
  border-radius: 11px;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 8px;
  border: 1px solid;
}}
.uc-match-dot {{ font-size: 10px; line-height: 1; margin-top: -1px; }}
.uc-match-strong {{
  background: #e6f5e0; color: #1b5e20; border-color: #4ea64e;
}}
.uc-match-medium {{
  background: #fff8e1; color: #5d4708; border-color: #f0c34a;
}}
.uc-match-weak {{
  background: #fdecea; color: #8a2018; border-color: #e3897f;
}}
/* Build 15 — equipment chips on UC cards. Small pill-shaped tags
   show which equipment slugs (and one model) the UC applies to so
   users can scan compatibility without opening the drawer. */
.uc-eq-chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 4px 0 8px;
}}
.uc-eq-chip {{
  display: inline-block;
  padding: 2px 7px;
  border-radius: 9999px;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.02em;
  border: 1px solid;
  white-space: nowrap;
  line-height: 1.4;
}}
.uc-eq-chip-slug {{
  background: #eef4ff;
  color: #1f3d7a;
  border-color: #b6c8eb;
}}
.uc-eq-chip-model {{
  background: #f3eefe;
  color: #4a2a8a;
  border-color: #c8b6eb;
}}
.uc-eq-chip-more {{
  background: #f5f5f5;
  color: #555;
  border-color: #d0d0d0;
  cursor: help;
}}
.uc-btn-row {{ display: flex; gap: 8px; }}
.uc-btn {{
  border: 1px solid #65a637;
  background: #fff;
  color: #255a15;
  padding: 4px 10px;
  border-radius: 3px;
  cursor: pointer;
  text-decoration: none;
  font-size: 12px;
}}
.uc-btn:hover {{ background: #eef7e6; }}
.uc-drawer {{
  position: fixed;
  top: 0;
  right: -520px;
  width: 500px;
  height: 100vh;
  background: #fff;
  border-left: 2px solid #65a637;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
  transition: right 0.2s ease;
  overflow-y: auto;
  padding: 18px 20px;
  z-index: 9999;
}}
.uc-drawer.open {{ right: 0; }}
.uc-close {{ float: right; }}
.uc-spl {{
  background: #f6f6f6;
  padding: 8px;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  border-radius: 4px;
  max-height: 40vh;
  overflow: auto;
}}
.uc-settings label {{ display: block; font-weight: 600; margin-top: 8px; }}
.uc-apibase {{ width: 90%; padding: 6px 8px; }}
.uc-filter {{ width: 100%; padding: 6px 8px; margin: 8px 0; }}
.uc-loading {{ color: #777; font-style: italic; }}
.uc-msg {{ color: #255a15; margin-top: 6px; }}
.uc-status-badge {{
  margin-left: auto;
  font-weight: 700;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 9999px;
  border: 1px solid currentColor;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}}
.uc-status-not_started {{ color: #555; background: #f3f3f3; border-color: #bbb; }}
.uc-status-in_progress {{ color: #1f3d7a; background: #eef4ff; border-color: #2a4f9c; }}
.uc-status-implemented {{ color: #1d6f1d; background: #e7f3e3; border-color: #65a637; }}
.uc-status-needs_review {{ color: #b54708; background: #fff4e0; border-color: #f7bc38; }}
.uc-status-decommissioned {{ color: #6f1d1d; background: #f7e3e3; border-color: #d93f3c; }}

.uc-sb-container {{ margin: 6px 0 8px; }}
.uc-sb-section summary {{ cursor: pointer; font-weight: 600; color: #2a4f9c; }}
.uc-sb-list {{ margin: 4px 0 4px 18px; padding: 0; font-size: 12px; }}
.uc-sb-item {{ list-style: disc; padding: 2px 0; }}
.uc-sb-version {{ color: #777; }}
.uc-sb-review {{ color: #b54708; font-weight: 600; }}
.uc-sb-not-cloud {{ color: #d93f3c; font-weight: 600; }}
.uc-sb-none {{ color: #777; font-style: italic; font-size: 12px; margin: 4px 0; }}

.uc-banner {{
  border-radius: 4px;
  padding: 8px 12px;
  margin: 8px 0;
  font-size: 13px;
  border: 1px solid;
}}
.uc-banner-warn {{ background: #fff4e0; border-color: #f58f39; color: #6f3a08; }}
.uc-banner-info {{ background: #eef4ff; border-color: #2a4f9c; color: #1f3d7a; }}

.uc-modal-backdrop {{
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}}
.uc-modal {{
  background: #fff;
  border-radius: 6px;
  padding: 18px 22px;
  width: 480px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
}}
.uc-modal h3 {{ margin: 0 0 8px; }}
.uc-modal label {{ display: block; font-weight: 600; margin-top: 12px; font-size: 13px; }}
.uc-modal-status, .uc-modal-notes {{
  width: 100%;
  margin-top: 4px;
  padding: 6px 8px;
  border: 1px solid #bbb;
  border-radius: 3px;
  box-sizing: border-box;
  font-family: inherit;
  font-size: 13px;
}}
.uc-modal-actions {{
  margin-top: 16px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}}
.uc-btn-cancel {{
  border-color: #bbb;
  color: #444;
}}
.uc-modal-msg {{
  margin-top: 8px;
  font-size: 12px;
  color: #555;
  min-height: 1.2em;
}}

.uc-toolbar {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin: 8px 0 12px;
}}
.uc-status-filter,
.uc-crit-filter,
.uc-pillar-filter,
.uc-mtype-filter,
.uc-equip-filter,
.uc-sort-filter {{
  padding: 6px 8px;
  border: 1px solid #bbb;
  border-radius: 3px;
  font-size: 13px;
  background: #fff;
  max-width: 180px;
}}
.uc-sort-filter {{ font-weight: 600; color: #2a4f9c; }}
.uc-toolbar .uc-filter {{
  flex: 1 1 240px;
  min-width: 180px;
  margin: 0;
}}
.uc-toolbar-count {{
  font-size: 12px;
  color: #666;
  margin-left: auto;
}}
.uc-btn-export {{
  border-color: #2a4f9c;
  color: #2a4f9c;
}}
.uc-btn-export:hover {{ background: #eef4ff; }}
.uc-empty {{
  padding: 20px;
  background: #fafafa;
  border: 1px dashed #d0d0d0;
  border-radius: 4px;
  color: #555;
  text-align: center;
}}
.uc-empty p {{ margin: 4px 0; }}

/* Diagnostics panel — only rendered when matchUseCases() returns []. */
.uc-diagnostics {{
  text-align: left;
  margin: 16px auto 0;
  max-width: 860px;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid #d8d8d8;
  border-radius: 4px;
  color: #222;
  font-size: 13px;
}}
.uc-diagnostics > summary {{
  cursor: pointer;
  font-weight: 600;
  color: #2a4f9c;
  padding: 4px 0;
}}
.uc-diagnostics h4 {{
  margin: 14px 0 6px;
  font-size: 13px;
  color: #444;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
.uc-diagnostics h5 {{
  margin: 10px 0 4px;
  font-size: 12px;
  color: #555;
  font-weight: 600;
}}
.uc-diag-table {{
  width: 100%;
  border-collapse: collapse;
  margin: 4px 0 8px;
}}
.uc-diag-table tr td {{
  padding: 4px 8px;
  border-bottom: 1px solid #f0f0f0;
}}
.uc-diag-table tr:last-child td {{
  border-bottom: 0;
}}
.uc-diag-label {{ color: #444; }}
.uc-diag-value {{
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
  width: 30%;
}}
.uc-diag-ok   {{ color: #1d6f1d; }}
.uc-diag-warn {{ color: #b54708; }}
.uc-diag-bad  {{ color: #b71c1c; }}
.uc-diag-list {{
  margin: 0 0 8px 18px;
  padding: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}}
.uc-diag-list li {{
  padding: 1px 0;
  list-style: square;
  color: #333;
}}
.uc-diag-more {{
  margin: 2px 0 8px 18px;
  font-size: 12px;
  color: #777;
  font-style: italic;
}}
.uc-diag-explain {{
  margin: 12px 0 0;
  padding: 8px 12px;
  background: #f6f8fc;
  border-left: 3px solid #2a4f9c;
  font-size: 12px;
  color: #1f3d7a;
  line-height: 1.5;
}}
.uc-diag-examples {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 4px 16px;
}}
"""


# ---------------------------------------------------------------------------
# app.manifest (Splunkbase v2) + metadata/default.meta + README + lookups
# ---------------------------------------------------------------------------


def _primary_app_manifest(version: str) -> dict[str, Any]:
    return {
        "dependencies": None,
        "incompatibleApps": {},
        "info": {
            "author": [
                {
                    "company": None,
                    "email": None,
                    "name": "Splunk Monitoring Use Cases contributors",
                }
            ],
            "classification": {
                "categories": ["IT Operations", "Security"],
                "developmentStatus": "Production/Stable",
                "intendedAudience": "SecOps, IT Operations, Platform owners",
            },
            "commonInformationModels": {"Splunk_CIM": "5.3"},
            "description": (
                "Scans the local Splunk environment for sourcetypes, indexes, "
                "CIM acceleration, and installed apps, then previews matching "
                "monitoring use cases from the Splunk Monitoring Use Cases "
                "catalogue (fenre/splunk-monitoring-use-cases). Bundles every "
                "tier-1 compliance use case (CMMC, DORA, GDPR, HIPAA, ISO "
                "27001, NIS2, NIST 800-53, NIST CSF, PCI DSS, SOC 2, SOX "
                "ITGC) as disabled-by-default saved searches plus a "
                "uc_compliance_mappings lookup so operators can enable per "
                "regulation from the Compliance view. Recommendations are "
                "preview-only: nothing is auto-enabled on the instance."
            ),
            "id": {
                "group": None,
                "name": PRIMARY_APP_ID,
                "version": version,
            },
            "license": {
                "name": "MIT",
                "text": "LICENSE",
                "uri": "https://github.com/fenre/splunk-monitoring-use-cases/blob/main/LICENSE",
            },
            "privacyPolicy": {"name": None, "text": None, "uri": None},
            "releaseDate": _deterministic_timestamp()[:10],
            "releaseNotes": {
                "name": None,
                "text": "README.md",
                "uri": "https://github.com/fenre/splunk-monitoring-use-cases/blob/main/CHANGELOG.md",
            },
            "title": "Splunk UC Recommender",
        },
        "inputGroups": {},
        "platformRequirements": {"splunk": {"Enterprise": ">=9.2"}},
        "schemaVersion": "2.0.0",
        "supportedDeployments": [
            "_standalone",
            "_distributed",
            "_search_head_clustering",
        ],
        "targetWorkloads": ["_search_heads"],
        "tasks": [],
    }


def _default_meta_primary() -> str:
    # AppInspect Cloud's ``check_meta_files`` requires every shipped
    # KV collection to have an explicit ``[collections/<name>]`` stanza
    # so cloud reviewers can grant scoped access. The new v9.0
    # collections (``uc_recommender_implementations``,
    # ``uc_recommender_audit``) get write access for admin + power so
    # the JS modal can POST status changes without going through the
    # owner-only system default. The implementations dashboard and the
    # decommission saved-search wrapper get explicit stanzas too.
    return (
        "# Default export permissions. Regenerated by scripts/generate_recommender_app.py.\n"
        "[]\n"
        "access = read : [ * ], write : [ admin, power ]\n"
        "export = app\n"
        "\n"
        "[macros]\n"
        "export = system\n"
        "\n"
        "[eventtypes]\n"
        "export = system\n"
        "\n"
        "[tags]\n"
        "export = system\n"
        "\n"
        "[savedsearches]\n"
        "export = none\n"
        "\n"
        "[savedsearches/uc_implementation_decommission]\n"
        "access = read : [ admin, power ], write : [ admin, power ]\n"
        "export = none\n"
        "\n"
        "[lookups]\n"
        "export = system\n"
        "\n"
        "[collections]\n"
        "export = system\n"
        "\n"
        "[collections/uc_recommender_implementations]\n"
        "access = read : [ * ], write : [ admin, power ]\n"
        "export = system\n"
        "\n"
        "[collections/uc_recommender_audit]\n"
        "access = read : [ admin, power ], write : [ admin, power ]\n"
        "export = system\n"
        "\n"
        "[transforms]\n"
        "export = system\n"
        "\n"
        "[views]\n"
        "export = user\n"
        "\n"
        "[views/implementations]\n"
        "access = read : [ * ], write : [ admin, power ]\n"
        "export = user\n"
        "\n"
        "[nav]\n"
        "export = user\n"
        "\n"
        "[capabilities/edit_uc_implementations]\n"
        "access = read : [ * ], write : [ admin ]\n"
        "export = system\n"
    )


def _authorize_conf() -> str:
    """``default/authorize.conf`` for the v9.0 ``edit_uc_implementations`` capability.

    Splunk's REST stack enforces this capability on every write to
    ``/storage/collections/data/uc_recommender_implementations`` and on
    dispatch of ``uc_implementation_decommission``. The JS modal hides
    its buttons when the capability is absent, but that's purely
    cosmetic — the real gate is the REST stack reading this stanza.

    The capability is granted to ``admin`` and ``power`` here. Operators
    can extend the grant set in ``local/authorize.conf`` without
    touching the generator.
    """
    sections = [
        (
            "capability::edit_uc_implementations",
            [],
        ),
        (
            "role_admin",
            [
                ("edit_uc_implementations", "enabled"),
            ],
        ),
        (
            "role_power",
            [
                ("edit_uc_implementations", "enabled"),
            ],
        ),
    ]
    return _render_conf(GENERATED_CONF_BANNER, sections)


def _lookup_static_csv(version: str, generated_at: str, api_base: str) -> str:
    buf = io.StringIO()
    buf.write("key,value\n")
    buf.write(f"catalogueVersion,{version}\n")
    buf.write(f"apiBaseUrl,{api_base}\n")
    buf.write(f"generatedAt,{generated_at}\n")
    buf.write(f"primaryAppId,{PRIMARY_APP_ID}\n")
    return buf.getvalue()


def _catalog_fallback_json(version: str, generated_at: str) -> dict[str, Any]:
    """Small fallback payload bundled with the app.

    Used when the browser cannot reach the live catalogue (e.g. no
    egress). Deliberately tiny (~1 KB) — only top-level stats and the
    API base URL — so the UI can still render a descriptive error.
    """
    return {
        "catalogueVersion": version,
        "generatedAt": generated_at,
        "apiBaseUrl": API_BASE_URL,
        "fallback": True,
        "note": (
            "Bundled fallback metadata. The recommender prefers live data "
            "from the apiBaseUrl; this file is only used when the browser "
            "cannot reach it and lets the UI render a descriptive error."
        ),
    }


def _primary_readme(version: str, generated_at: str) -> str:
    return f"""# Splunk UC Recommender

App ID: `{PRIMARY_APP_ID}`  
App version: **{version}**  
Generated: `{generated_at}`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)

This app does **two** things in one Splunk install:

1. **Recommends** monitoring use cases from the upstream
   [Splunk Monitoring Use Cases catalogue]({API_BASE_URL}) based on
   what is actually deployed in your environment (sourcetypes, indexes,
   CIM acceleration, installed apps).
2. **Bundles** every tier-1 compliance use case from the same
   catalogue — CMMC, EU DORA, GDPR, HIPAA Security, ISO/IEC 27001,
   NIS2, NIST SP 800-53, NIST CSF, PCI DSS, SOC 2, SOX ITGC — as
   disabled-by-default saved searches plus one merged
   `uc_compliance_mappings` lookup, so you do not need to install one
   app per regulation.

It is **preview-only by default**: the recommender side never writes
saved searches automatically. Every recommendation ships with a
"Copy SPL" button and a deep-link into the Search & Reporting app so
operators can review, adapt, and save the search themselves. The
bundled compliance saved searches are also `disabled = 1`/
`is_scheduled = 0` until an operator opens the **Compliance** view,
filters by regulation, and explicitly enables the ones they want.

## How it works

1. Four low-cost scheduled searches under
   `default/savedsearches.conf` populate the `uc_recommender_inventory`
   KV store with your active sourcetypes, indexes, CIM acceleration
   status, and installed apps.
2. When you open the **Recommend** dashboard, a small piece of
   JavaScript under `appserver/static/js/recommender.js`:
   * reads the inventory via a search job
     (`| inputlookup uc_recommender_inventory`);
   * fetches four JSON indexes from the upstream API:
     - `/api/v1/recommender/sourcetype-index.json`
     - `/api/v1/recommender/cim-index.json`
     - `/api/v1/recommender/app-index.json`
     - `/api/v1/recommender/uc-thin.json`
   * joins them, scores each UC (exact sourcetype match = 3, fuzzy = 1,
     CIM accelerated = 2, matching app = 1, × criticality weight), and
     renders the top 60 cards.
3. Clicking **Details** loads the full compliance sidecar from
   `/api/v1/compliance/ucs/<id>.json` for the 1 200+ compliance-tagged
   UCs.
4. The **Compliance** view reads
   `lookups/uc_compliance_mappings.csv` (also written by the
   generator) so operators can pick a regulation, see every bundled
   UC that satisfies a clause, and click straight through to the
   saved-search definition to enable it.

The app only talks to the hard-coded allow-list of upstream hosts
(currently `https://fenre.github.io`). The **Settings** tab lets
operators override the API base URL; the override is validated against
the allow-list and stored in `localStorage` before it is used.

## Requirements

* Splunk Enterprise or Splunk Cloud, version 9.2+
* Outbound HTTPS from the search head to
  `https://fenre.github.io/splunk-monitoring-use-cases/api/v1/`
* KV store enabled (default on every supported deployment)

## Install

```
tar czf {PRIMARY_APP_ID}.spl {PRIMARY_APP_ID}/
# Upload via Settings → Manage Apps → Install from file
```

After install, open **Apps → Splunk UC Recommender**. The first
inventory refresh runs 30 minutes later. Hit **Settings → Manual
scan** to kick one off immediately.

## Splunk Cloud compatibility

* No `commands.conf`, `restmap.conf`, `web.conf[expose:*]`, or
  `[script://]` inputs.
* Only built-in SPL commands (`metadata`, `eventcount`, `tstats`,
  `rest`, `inputlookup`, `outputlookup`).
* All browser-side logic is bundled under `appserver/static/`.
* Outbound fetch calls are restricted to an explicit allow-list with
  `credentials: 'omit'`.

## AppInspect readiness

* `app.manifest` v2.0.0 with full `info` block.
* `metadata/default.meta` keeps saved searches private and exports
  macros, lookups, and eventtypes as `system`.
* MIT `LICENSE` at the app root.
* No local/ overrides shipped; all defaults live under `default/`.

## Files in this app

```
{PRIMARY_APP_ID}/
├── app.manifest
├── README.md
├── LICENSE
├── default/
│   ├── app.conf
│   ├── savedsearches.conf       # 4 Cloud-safe scan searches
│   │                            # + every tier-1 compliance UC, disabled
│   ├── collections.conf         # KV: uc_recommender_inventory + scan_runs
│   ├── transforms.conf          # KV + CSV lookup definitions
│   ├── macros.conf              # uc_recommender_* + uc_compliance_* macros
│   ├── eventtypes.conf          # recommender + per-(reg, family) eventtypes
│   ├── tags.conf
│   └── data/ui/
│       ├── nav/default.xml      # Recommend · Scan · Browse · Compliance ·
│       │                        # Implementations · Settings · Search
│       └── views/
│           ├── recommend.xml    # primary recommendation page
│           ├── scan.xml         # raw inventory tables
│           ├── browse.xml       # full catalogue filter
│           ├── compliance.xml   # filter bundled UCs by regulation/clause
│           ├── implementations.xml  # backlog + bulk operator workflow
│           └── settings.xml     # API base URL override, reset
├── appserver/static/
│   ├── js/
│   │   ├── recommender.js       # main UI, AMD module
│   │   ├── scanner.js           # inventory helpers
│   │   └── uc-card.js           # standalone card renderer
│   ├── css/recommender.css
│   └── data/catalog-fallback.json
├── lookups/
│   ├── uc_recommender_static.csv     # stamped catalogueVersion + apiBase
│   └── uc_compliance_mappings.csv    # one row per (UC, clause)
├── metadata/default.meta
└── static/                      # icons placeholder
```

## What the bundled compliance content covers

Every tier-1 framework defined in `data/regulations.json` ships in the
same lookup and same `savedsearches.conf`:

| Framework        | Source key   |
|------------------|--------------|
| CMMC 2.0         | `cmmc`       |
| EU DORA          | `dora`       |
| GDPR             | `gdpr`       |
| HIPAA Security   | `hipaa-security` |
| ISO/IEC 27001    | `iso-27001`  |
| NIS2             | `nis2`       |
| NIST SP 800-53   | `nist-800-53` |
| NIST CSF         | `nist-csf`   |
| PCI DSS          | `pci-dss`    |
| SOC 2            | `soc-2`      |
| SOX ITGC         | `sox-itgc`   |

UCs that satisfy multiple frameworks appear once in
`savedsearches.conf` (deduped by UC id) with every regulation listed in
their `description`/`action.uc_compliance.param.regulations` field.
The same UC fans out to one row per (regulation, clause) tuple in the
lookup so per-clause reporting still works.

## Field-coverage matching

UCs declare a `requiredFields` set in their schema. The recommender
flags every match with **field coverage unknown** by default; the
prior Enterprise-only `splunk-uc-recommender-ta` modular input that
sampled `(index, sourcetype)` pairs to populate `fields_extracted` was
retired in v9.0 to keep this repo to a single Cloud-safe artefact. A
future Cloud-safe replacement (e.g. `| metadata` + `| typelearner`)
is on the roadmap.

---

_This app is generated. Edits in place will be overwritten. File bug
reports and content requests at
<https://github.com/fenre/splunk-monitoring-use-cases/issues>._
"""


# ---------------------------------------------------------------------------
# Orchestration — build the two apps
# ---------------------------------------------------------------------------


def _build_primary_app(
    out_root: pathlib.Path,
    version: str,
    generated_at: str,
    api_base: str,
) -> pathlib.Path:
    app_root = out_root / PRIMARY_APP_ID
    _write_text(app_root / "default" / "app.conf", _primary_app_conf(version))
    _write_text(app_root / "default" / "savedsearches.conf", _savedsearches_conf())
    _write_text(app_root / "default" / "collections.conf", _collections_conf())
    _write_text(app_root / "default" / "transforms.conf", _transforms_conf())
    _write_text(app_root / "default" / "macros.conf", _macros_conf())
    _write_text(app_root / "default" / "eventtypes.conf", _eventtypes_conf())
    _write_text(app_root / "default" / "tags.conf", _tags_conf())
    _write_text(app_root / "default" / "authorize.conf", _authorize_conf())
    _write_text(
        app_root / "default" / "data" / "ui" / "nav" / "default.xml",
        _nav_default_xml(),
    )
    _write_text(
        app_root / "default" / "data" / "ui" / "views" / "recommend.xml",
        _recommend_view_xml(api_base),
    )
    _write_text(
        app_root / "default" / "data" / "ui" / "views" / "scan.xml",
        _scan_view_xml(),
    )
    _write_text(
        app_root / "default" / "data" / "ui" / "views" / "browse.xml",
        _browse_view_xml(api_base),
    )
    _write_text(
        app_root / "default" / "data" / "ui" / "views" / "settings.xml",
        _settings_view_xml(api_base),
    )
    _write_text(
        app_root / "default" / "data" / "ui" / "views" / "compliance.xml",
        _compliance_view_xml(),
    )
    _write_text(
        app_root / "default" / "data" / "ui" / "views" / "implementations.xml",
        _implementations_view_xml(),
    )
    # The Studio variant (`recommend_studio.xml` + `recommend.json`)
    # was removed in build 4. Strip any artefacts from a previous build
    # so the produced bundle is reproducible regardless of what's on disk.
    for _legacy in (
        app_root / "default" / "data" / "ui" / "views" / "recommend_studio.xml",
        app_root / "default" / "data" / "ui" / "views" / "recommend.json",
    ):
        if _legacy.exists():
            _legacy.unlink()
    _write_text(
        app_root / "appserver" / "static" / "js" / "recommender.js",
        _js_recommender(api_base),
    )
    _write_text(
        app_root / "appserver" / "static" / "js" / "scanner.js",
        _js_scanner(),
    )
    _write_text(
        app_root / "appserver" / "static" / "js" / "uc-card.js",
        _js_uc_card(),
    )
    _write_text(
        app_root / "appserver" / "static" / "css" / "recommender.css",
        _css_recommender(),
    )
    _write_json(
        app_root / "appserver" / "static" / "data" / "catalog-fallback.json",
        _catalog_fallback_json(version, generated_at),
    )
    _write_text(
        app_root / "lookups" / "uc_recommender_static.csv",
        _lookup_static_csv(version, generated_at, api_base),
    )
    compliance_ucs, _ = _load_compliance_bundle()
    _write_text(
        app_root / "lookups" / "uc_compliance_mappings.csv",
        _compliance_lookup_csv(compliance_ucs),
    )
    _write_text(
        app_root / "metadata" / "default.meta",
        _default_meta_primary(),
    )
    _write_json(
        app_root / "app.manifest",
        _primary_app_manifest(version),
    )
    _write_text(
        app_root / "README.md",
        _primary_readme(version, generated_at),
    )
    # Placeholder so the ``static/`` directory survives packaging.
    _write_text(
        app_root / "static" / ".gitkeep",
        "# Icons and branding assets land here.\n",
    )
    if LICENSE_FILE.exists():
        (app_root / "LICENSE").write_text(
            LICENSE_FILE.read_text(encoding="utf-8"),
            encoding="utf-8",
            newline="\n",
        )
    return app_root


def _render(out_root: pathlib.Path) -> dict[str, pathlib.Path]:
    version = _read_version()
    generated_at = _deterministic_timestamp()
    out_root.mkdir(parents=True, exist_ok=True)
    built: dict[str, pathlib.Path] = {
        PRIMARY_APP_ID: _build_primary_app(out_root, version, generated_at, API_BASE_URL)
    }
    return built


def _strip_timestamp_lines(content: bytes) -> bytes:
    """Remove lines that only carry generator-stamped timestamps.

    The generator derives every timestamp from
    ``_deterministic_timestamp()``, which itself reads
    ``git log -1 --format=%ct``. Because HEAD shifts the moment a
    regeneration commit lands, ``generatedAt`` / ``Generated:`` /
    ``releaseDate`` lines look stale to the next ``--check`` run. They
    are bookkeeping fields, not content; ignore them when comparing
    the freshly generated tree against the on-disk tree so a stale
    bump-then-commit cadence does not flap CI.
    """
    lines = content.split(b"\n")
    return b"\n".join(
        line
        for line in lines
        if b"generatedAt" not in line
        and b"Generated:" not in line
        and b'"releaseDate"' not in line
    )


def _diff_trees(lhs: pathlib.Path, rhs: pathlib.Path) -> list[str]:
    """Return file paths that differ between two trees (recursive)."""
    diffs: list[str] = []
    lhs_files = {p.relative_to(lhs) for p in lhs.rglob("*") if p.is_file()}
    rhs_files = {p.relative_to(rhs) for p in rhs.rglob("*") if p.is_file()}
    for p in sorted(lhs_files - rhs_files):
        diffs.append(f"+ {p}  (only in freshly generated tree)")
    for p in sorted(rhs_files - lhs_files):
        diffs.append(f"- {p}  (only on disk)")
    for p in sorted(lhs_files & rhs_files):
        lhs_content = (lhs / p).read_bytes()
        rhs_content = (rhs / p).read_bytes()
        if lhs_content != rhs_content:
            if _strip_timestamp_lines(lhs_content) != _strip_timestamp_lines(rhs_content):
                diffs.append(f"  differs: {p}")
    return diffs


def _scope_check_diff(
    expected: pathlib.Path,
    on_disk: pathlib.Path,
    apps: Iterable[str],
) -> list[str]:
    """Only diff the subdirectories the generator owns."""
    diffs: list[str] = []
    for app in apps:
        if (expected / app).exists():
            diffs.extend(_diff_trees(expected / app, on_disk / app))
    return diffs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the splunk-uc-recommender app tree (single artefact "
            "since v9.0). Deterministic; use --check in CI."
        ),
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=DEFAULT_OUTPUT,
        help="Output directory (default: splunk-apps/).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Regenerate into a temp dir and diff against --output. "
            "Exits 1 on drift so CI can gate PRs."
        ),
    )
    args = parser.parse_args(argv)

    apps = [PRIMARY_APP_ID]

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = pathlib.Path(tmp) / "splunk-apps"
            _render(tmp_root)
            diffs = _scope_check_diff(tmp_root, args.output, apps)
            if diffs:
                sys.stderr.write(
                    "splunk-uc-recommender tree drift — regenerate with "
                    "`python3 scripts/generate_recommender_app.py` and commit:\n"
                )
                for line in diffs[:200]:
                    sys.stderr.write(line + "\n")
                if len(diffs) > 200:
                    sys.stderr.write(f"... {len(diffs) - 200} additional diffs omitted\n")
                return 1
            sys.stdout.write("splunk-uc-recommender app is up to date.\n")
            return 0

    built = _render(args.output)
    total_files = 0
    for app, path in built.items():
        n = sum(1 for _ in path.rglob("*") if _.is_file())
        total_files += n
        sys.stdout.write(f"  {app}: {n} files at {path}\n")
    sys.stdout.write(f"Wrote {len(built)} app ({total_files} files) under {args.output}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
