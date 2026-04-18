#!/usr/bin/env python3
"""Generate AppInspect-shaped Splunk app trees from the compliance catalogue.

Phase 1.8 seeded the POC; Phase 5.1 scales it out to the 12 per-regulation
apps the plan targets (11 tier-1 frameworks + UK GDPR, a tier-2 derivative
that is material enough to ship standalone evidence for).  Each regulation
gets a self-contained app under ``splunk-apps/splunk-uc-<regulation-id>/``
containing every use case (sidecar JSON in ``use-cases/cat-*/uc-*.json``)
that tags that regulation.

Phase 5.1 additions
-------------------

* Every app ships a generated Simple XML compliance-posture dashboard
  (``default/data/ui/views/<reg-id>_compliance_posture.xml``) that reads
  from the per-app ``uc_compliance_mappings`` lookup.
* ``default/data/ui/nav/default.xml`` links the dashboard alongside the
  catch-all eventtype search so operators can jump straight into posture
  visualisations after install.
* ``metadata/default.meta`` exports the dashboard at ``app`` scope while
  keeping saved searches private (AppInspect-friendly).
* The default selection list now explicitly includes ``uk-gdpr`` so the
  generator produces the plan's 12 apps (Phase 5.1 exit criterion).

The generator is:

* **Deterministic** — same inputs always produce byte-identical output.  CI
  runs ``--check`` to diff the committed tree against the regenerated tree
  and fails on drift.
* **Offline** — no network calls; everything reads from the repository.
* **Additive** — files are written with a stable ordering and a generator
  banner so maintainers never hand-edit them.
* **AppInspect-shaped** — every app has the minimum files Splunkbase vetting
  expects: ``app.manifest`` v2, ``default/app.conf``, ``metadata/default.meta``,
  ``README.md``, ``LICENSE``, a navigation stub, and a ``savedsearches.conf``
  where every stanza ships ``disabled = 1`` / ``is_scheduled = 0`` by default.

Inputs
------

* ``schemas/uc.schema.json``              — authoring schema (for field names)
* ``data/regulations.json``               — framework index, aliases, clauses
* ``use-cases/cat-*/uc-*.json``           — UC sidecars (compliance + SPL)
* ``VERSION``                             — catalogue version
* ``LICENSE``                             — upstream MIT licence (copied)
* ``reports/compliance-coverage.json``    — used only for the README pre-amble

Outputs
-------

``splunk-apps/splunk-uc-<reg-id>/``
    ├── app.manifest                              Splunkbase v2.0.0 manifest
    ├── README.md                                 Regulation-specific overview
    ├── LICENSE                                   MIT (copied from repo root)
    ├── default/
    │   ├── app.conf
    │   ├── savedsearches.conf                    1 stanza per UC, disabled by default
    │   ├── eventtypes.conf                       1 stanza per controlFamily
    │   ├── macros.conf                           shared helpers used by the searches
    │   ├── tags.conf                             "uc_compliance" + per-regulation tag
    │   └── data/ui/
    │       ├── nav/default.xml                   links dashboard + catch-all search
    │       └── views/
    │           └── <reg>_compliance_posture.xml  Simple XML posture dashboard
    ├── lookups/
    │   └── uc_compliance_mappings.csv            per-UC clause/assurance table
    ├── metadata/
    │   └── default.meta                          export=system for knowledge objects;
    │                                             export=app for the dashboard
    └── static/                                   empty; placeholder for future icons

CLI
---

    # Default: 11 tier-1 frameworks + UK GDPR (the 12 per-regulation apps)
    python3 scripts/generate_splunk_app.py

    # Single regulation
    python3 scripts/generate_splunk_app.py --regulation gdpr

    # Determinism guard (CI)
    python3 scripts/generate_splunk_app.py --check

    # Custom output directory
    python3 scripts/generate_splunk_app.py --output dist/splunk-apps
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
USE_CASES_DIR = REPO_ROOT / "use-cases"
DATA_DIR = REPO_ROOT / "data"
REGULATIONS_FILE = DATA_DIR / "regulations.json"
DEFAULT_OUTPUT = REPO_ROOT / "splunk-apps"
VERSION_FILE = REPO_ROOT / "VERSION"
LICENSE_FILE = REPO_ROOT / "LICENSE"

# Sibling generators (notably ``scripts/generate_recommender_app.py``) also
# write ``splunk-uc-*`` trees into ``splunk-apps/``.  They own those trees
# end-to-end, so this generator must neither prune them during cleanup nor
# flag them as drift during ``--check``.
_EXTERNAL_APP_IDS = frozenset({
    "splunk-uc-recommender",
    "splunk-uc-recommender-ta",
})


# Derivative (tier-2+) regulations that the plan wants shipped as their own
# standalone Splunk app in addition to every tier-1 framework.  Keep this
# list conservative and documented — adding a framework here commits the
# project to maintaining a packaged evidence pack, Splunk app, and SME
# review flow for it (Phase 5.1 / Phase 5.2 scope).
#
# UK GDPR is the first derivative promoted because Regulation (EU)
# 2016/679 was onshored into UK law under the European Union (Withdrawal)
# Act 2018 with identity clause numbering; UK auditors consistently ask
# for UK-GDPR-branded evidence rather than a generic GDPR export, so
# shipping a dedicated app satisfies the most common request.  See the
# ``derivesFrom`` entry in ``data/regulations.json`` for the identity
# propagation rules the Phase 3.3 generator already applies.
_DEFAULT_DERIVATIVE_APP_IDS = frozenset({
    "uk-gdpr",
})


def _is_external_app(relative_path: pathlib.Path) -> bool:
    """Return True if ``relative_path`` belongs to a sibling-owned app tree."""
    parts = relative_path.parts
    return bool(parts) and parts[0] in _EXTERNAL_APP_IDS

GENERATED_BANNER = (
    "# -----------------------------------------------------------------\n"
    "# GENERATED by scripts/generate_splunk_app.py — DO NOT EDIT BY HAND.\n"
    "# Source of truth: use-cases/cat-*/uc-*.json + data/regulations.json.\n"
    "# Re-run `python3 scripts/generate_splunk_app.py` after content edits.\n"
    "# -----------------------------------------------------------------\n"
)


# ---------------------------------------------------------------------------
# Small I/O helpers (deterministic writers)
# ---------------------------------------------------------------------------


def _deterministic_timestamp() -> str:
    """Return a reproducible UTC timestamp for every generated artifact.

    Uses the same strategy as ``scripts/generate_api_surface.py`` and
    ``scripts/audit_compliance_mappings.py``:

    1. ``SOURCE_DATE_EPOCH`` if the caller set it (CI uses this for
       reproducible builds).
    2. Otherwise the HEAD commit timestamp (``git log -1 --format=%ct``).
    3. Fallback: the current UTC time, rounded to the second.
    """
    env = os.environ.get("SOURCE_DATE_EPOCH")
    if env:
        try:
            return (
                datetime.fromtimestamp(int(env), tz=timezone.utc)
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
            datetime.fromtimestamp(ts, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return (
            datetime.now(tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )


def _load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_text(path: pathlib.Path, body: str) -> None:
    """Write ``body`` to ``path``.  Ends with exactly one newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not body.endswith("\n"):
        body += "\n"
    path.write_text(body, encoding="utf-8", newline="\n")


def _write_json(path: pathlib.Path, obj: Any) -> None:
    body = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)
    _write_text(path, body)


def _read_version() -> str:
    if not VERSION_FILE.exists():
        return "0.0.0"
    raw = VERSION_FILE.read_text().strip()
    if not raw:
        return "0.0.0"
    # Expand "6.0" to "6.0.0" for Splunkbase-compatible SemVer.
    parts = raw.split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts[:3])


# ---------------------------------------------------------------------------
# UC + regulations loaders (mirrors scripts/generate_api_surface.py)
# ---------------------------------------------------------------------------


def _uc_sort_key(uc: Mapping[str, Any]) -> Tuple[int, ...]:
    uid = uc.get("id") or ""
    try:
        return tuple(int(part) for part in str(uid).split("."))
    except ValueError:  # pragma: no cover - malformed IDs
        return (9_999,)


def _load_ucs() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not USE_CASES_DIR.exists():
        return items
    for path in sorted(USE_CASES_DIR.rglob("uc-*.json")):
        try:
            data = _load_json(path)
        except json.JSONDecodeError as exc:  # pragma: no cover - surfaced by audit
            raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
        if not isinstance(data, dict) or not data.get("id"):
            continue
        data["_sourcePath"] = str(path.relative_to(REPO_ROOT))
        items.append(data)
    items.sort(key=_uc_sort_key)
    return items


def _regulation_alias_to_id(regs: Mapping[str, Any]) -> Dict[str, str]:
    """Case-insensitive alias -> canonical framework id.

    Kept in sync with ``scripts/generate_api_surface.py::_regulation_alias_to_id``
    and ``scripts/audit_compliance_mappings.py::RegulationsCatalogue``.  All
    three must resolve compliance[].regulation to the same framework id.
    """
    out: Dict[str, str] = {}
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


def _framework_by_id(regs: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        fw["id"]: fw
        for fw in regs.get("frameworks", [])
        if fw.get("id")
    }


def _ucs_for_regulation(
    fw_id: str,
    ucs: Sequence[Mapping[str, Any]],
    alias_map: Mapping[str, str],
) -> List[Dict[str, Any]]:
    """Return every UC with at least one compliance[] entry that resolves to ``fw_id``.

    Each returned UC is annotated with ``_matchedCompliance`` — the list of
    compliance entries on that UC that matched this regulation, so the
    saved-search stanza and README can cite the exact clauses.
    """
    out: List[Dict[str, Any]] = []
    target = fw_id.lower()
    for uc in ucs:
        matched: List[Dict[str, Any]] = []
        for entry in uc.get("compliance") or []:
            raw_reg = str(entry.get("regulation") or "").strip()
            if not raw_reg:
                continue
            canonical = alias_map.get(raw_reg.lower())
            if canonical and canonical.lower() == target:
                matched.append(entry)
        if matched:
            uc_copy = dict(uc)
            uc_copy["_matchedCompliance"] = matched
            out.append(uc_copy)
    out.sort(key=_uc_sort_key)
    return out


# ---------------------------------------------------------------------------
# .conf writers (.conf stanza ordering is ASCII sort by stanza name)
# ---------------------------------------------------------------------------


_SAFE_STANZA_RE = re.compile(r"[\[\]\n\r]")


def _safe_stanza(name: str) -> str:
    """Strip characters that break Splunk .conf stanza headers."""
    return _SAFE_STANZA_RE.sub(" ", name).strip()


def _uc_to_savedsearch_stanza(uc: Mapping[str, Any], fw_id: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Return (stanza-name, ordered-key-value-pairs) for a UC saved search.

    Every stanza is ``disabled = 1`` / ``is_scheduled = 0`` / ``enableSched = 0``
    so fresh installs never schedule searches before an operator has reviewed
    them.  Clause citations ride on the ``description`` and ``action.*``
    metadata so the saved search itself documents its regulatory backing.
    """
    uc_id = uc.get("id") or ""
    title = uc.get("title") or uc.get("name") or f"UC-{uc_id}"
    stanza = _safe_stanza(f"UC-{uc_id} — {title}")[:1024]

    matched = uc.get("_matchedCompliance") or []
    clauses = sorted({str(e.get("clause") or "").strip() for e in matched if e.get("clause")})
    version_tags = sorted(
        {
            f"{e.get('regulation')}@{e.get('version') or 'unversioned'}"
            for e in matched
        }
    )

    criticality = (uc.get("criticality") or "medium").lower()
    # Splunk severity: 1=low 2=low 3=medium 4=high 5=critical.  Map string labels.
    severity = {
        "critical": "5",
        "high": "4",
        "medium": "3",
        "low": "2",
        "informational": "1",
    }.get(criticality, "3")

    description_lines = [
        f"{title}",
        f"UC {uc_id} | regulation={fw_id} | criticality={criticality}",
    ]
    if clauses:
        description_lines.append(
            "clauses=" + ", ".join(clauses[:8]) + ("…" if len(clauses) > 8 else "")
        )
    description = " | ".join(description_lines).replace("\n", " ").replace("\r", " ")

    spl = (uc.get("spl") or "").strip() or f"search index=_internal | head 0"
    # savedsearches.conf continuation: every non-final line gets a trailing "\"
    # so multi-line SPL renders as a single search.
    spl_lines = [line.rstrip() for line in spl.splitlines() if line.strip()]
    if len(spl_lines) == 1:
        search_value = spl_lines[0]
    else:
        search_value = " \\\n".join(spl_lines)

    pairs: List[Tuple[str, str]] = [
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
    ]
    if clauses:
        pairs.append(("action.uc_compliance.param.clauses", ",".join(clauses)))
    if version_tags:
        pairs.append(("action.uc_compliance.param.versions", ",".join(version_tags)))
    pairs.append(("action.uc_compliance.param.uc_id", uc_id))
    pairs.append(("action.uc_compliance.param.regulation", fw_id))
    return stanza, pairs


def _render_conf(banner: str, sections: Sequence[Tuple[str, Sequence[Tuple[str, str]]]]) -> str:
    """Turn ``[(stanza, [(k, v), …]), …]`` into a deterministic .conf body."""
    buf = io.StringIO()
    buf.write(banner)
    buf.write("\n")
    first = True
    for stanza, pairs in sections:
        if not first:
            buf.write("\n")
        first = False
        buf.write(f"[{stanza}]\n")
        for key, value in pairs:
            # Continuation lines in .conf require trailing backslashes; we
            # rely on the caller (see _uc_to_savedsearch_stanza) to have
            # already embedded \ + LF between wrapped lines.
            buf.write(f"{key} = {value}\n")
    return buf.getvalue()


def _savedsearches_conf(ucs: Sequence[Mapping[str, Any]], fw_id: str) -> str:
    sections: List[Tuple[str, List[Tuple[str, str]]]] = []
    for uc in ucs:
        stanza, pairs = _uc_to_savedsearch_stanza(uc, fw_id)
        sections.append((stanza, pairs))
    sections.sort(key=lambda s: s[0])
    return _render_conf(GENERATED_BANNER, sections)


def _eventtypes_conf(ucs: Sequence[Mapping[str, Any]], fw_id: str) -> str:
    """One eventtype per unique controlFamily seen in the UC set."""
    by_family: Dict[str, List[str]] = {}
    for uc in ucs:
        family = (uc.get("controlFamily") or "uncategorised").strip() or "uncategorised"
        by_family.setdefault(family, []).append(uc.get("id") or "")
    sections: List[Tuple[str, List[Tuple[str, str]]]] = []
    for family in sorted(by_family):
        ids = sorted(by_family[family])
        safe = re.sub(r"[^A-Za-z0-9]+", "_", family).strip("_").lower() or "uncategorised"
        stanza = f"uc_compliance_{fw_id}_{safe}"
        search = (
            f"eventtype_description=\"{fw_id} — {family} (covers "
            f"UC {', '.join(ids[:5])}{'…' if len(ids) > 5 else ''})\" "
            f"tag::uc_compliance_regulation=\"{fw_id}\""
        )
        sections.append(
            (
                stanza,
                [
                    ("search", search),
                    ("priority", "10"),
                    ("disabled", "0"),
                ],
            )
        )
    return _render_conf(GENERATED_BANNER, sections)


def _macros_conf(fw_id: str) -> str:
    sections = [
        (
            "uc_compliance_app",
            [
                ("definition", f"eventtype=\"uc_compliance_{fw_id}_uncategorised\""),
                ("iseval", "0"),
                (
                    "description",
                    (
                        f"Convenience macro: expands to the catch-all eventtype "
                        f"used by the {fw_id} compliance app.  Override to chain "
                        f"with your own filters."
                    ),
                ),
            ],
        ),
        (
            "uc_compliance_window(1)",
            [
                ("args", "lookback"),
                ("definition", "earliest=-$lookback$@m latest=now"),
                ("iseval", "0"),
                (
                    "description",
                    (
                        "Parameterised lookback.  `uc_compliance_window(30m)` "
                        "yields `earliest=-30m@m latest=now`."
                    ),
                ),
            ],
        ),
    ]
    return _render_conf(GENERATED_BANNER, sections)


def _tags_conf(fw_id: str) -> str:
    sections = [
        (
            f"eventtype=uc_compliance_{fw_id}_uncategorised",
            [
                ("uc_compliance_regulation", "enabled"),
                (f"uc_compliance_framework_{fw_id}", "enabled"),
            ],
        ),
    ]
    return _render_conf(GENERATED_BANNER, sections)


def _transforms_conf(fw_id: str) -> str:
    """``transforms.conf`` stanza that registers the compliance lookup.

    Without this stanza the CSV that we write to ``lookups/`` is just a
    file on disk — saved searches and dashboards cannot reference
    ``uc_compliance_mappings`` by name.  Exporting the transform via
    ``metadata/default.meta`` (``[transforms]`` stanza) keeps it usable
    from sibling apps too, which is what Phase 5.1 dashboards rely on.
    """
    sections = [
        (
            "uc_compliance_mappings",
            [
                ("filename", "uc_compliance_mappings.csv"),
                (
                    "description",
                    (
                        f"Per-UC clause/assurance mapping for the "
                        f"{fw_id} compliance app.  Regenerated by "
                        "scripts/generate_splunk_app.py."
                    ),
                ),
            ],
        ),
    ]
    return _render_conf(GENERATED_BANNER, sections)


def _app_conf(fw: Mapping[str, Any], version: str) -> str:
    fw_id = fw["id"]
    description = (
        f"Splunk saved searches, macros, and lookups that cover the "
        f"{fw.get('name') or fw.get('shortName') or fw_id} regulation. "
        "Generated from the Splunk Monitoring Use Cases catalogue "
        "(https://github.com/fenre/splunk-monitoring-use-cases). Every search "
        "ships disabled by default — review, override the index, and enable."
    ).replace("\n", " ")
    sections = [
        (
            "install",
            [
                ("is_configured", "0"),
                ("state", "enabled"),
                ("build", "1"),
            ],
        ),
        (
            "ui",
            [
                ("is_visible", "true"),
                (
                    "label",
                    f"Splunk Use Cases — {fw.get('shortName') or fw_id.upper()} compliance",
                ),
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
                ("id", f"splunk-uc-{fw_id}"),
                ("check_for_updates", "false"),
            ],
        ),
    ]
    return _render_conf(GENERATED_BANNER, sections)


# ---------------------------------------------------------------------------
# app.manifest + metadata + misc
# ---------------------------------------------------------------------------


def _app_manifest(fw: Mapping[str, Any], version: str) -> Dict[str, Any]:
    fw_id = fw["id"]
    return {
        "schemaVersion": "2.0.0",
        "info": {
            "title": f"Splunk Use Cases — {fw.get('shortName') or fw_id.upper()} compliance",
            "id": {
                "group": None,
                "name": f"splunk-uc-{fw_id}",
                "version": version,
            },
            "author": [
                {
                    "name": "Splunk Monitoring Use Cases contributors",
                    "email": None,
                    "company": None,
                }
            ],
            "releaseDate": None,
            "description": (
                f"Regulation-scoped Splunk compliance content for "
                f"{fw.get('name') or fw_id}. Ships saved searches, eventtypes, "
                f"macros, and a per-UC clause-mapping lookup.  All searches are "
                f"disabled by default."
            ),
            "classification": {
                "intendedAudience": "Compliance, SecOps, IT GRC",
                "categories": ["Security", "IT Operations"],
                "developmentStatus": "Production/Stable",
            },
            "commonInformationModels": {
                "Splunk_CIM": "5.3",
            },
            "license": {
                "name": "MIT",
                "text": "LICENSE",
                "uri": "https://github.com/fenre/splunk-monitoring-use-cases/blob/main/LICENSE",
            },
            "privacyPolicy": {
                "name": None,
                "text": None,
                "uri": None,
            },
            "releaseNotes": {
                "name": None,
                "text": "README.md",
                "uri": "https://github.com/fenre/splunk-monitoring-use-cases/blob/main/CHANGELOG.md",
            },
        },
        "dependencies": None,
        "tasks": [],
        "inputGroups": {},
        "incompatibleApps": {},
        "platformRequirements": {
            "splunk": {
                "Enterprise": ">=9.2",
            },
        },
        "supportedDeployments": ["_standalone", "_distributed", "_search_head_clustering"],
        "targetWorkloads": ["_search_heads"],
    }


def _default_meta() -> str:
    # Export macros, eventtypes, tags, the compliance lookup, and the
    # posture dashboard at the widest reasonable scope:
    #   - ``system`` for knowledge objects that downstream apps reuse
    #     (macros, eventtypes, tags, transforms, lookups).
    #   - ``app`` for the generated dashboard so it shows up in the app's
    #     navigation without becoming a global object.
    # Saved searches remain private (``export = none``): operators must
    # opt in per-search to avoid fan-out of disabled alerts.
    return (
        "# Default export permissions.  Regenerated by scripts/generate_splunk_app.py.\n"
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
        "[lookups]\n"
        "export = system\n"
        "\n"
        "[transforms]\n"
        "export = system\n"
        "\n"
        "[views]\n"
        "export = app\n"
    )


def _nav_default_xml(fw: Mapping[str, Any]) -> str:
    fw_id = fw["id"]
    short = fw.get("shortName") or fw_id.upper()
    dashboard = f"{fw_id.replace('-', '_')}_compliance_posture"
    return (
        "<!-- Auto-generated by scripts/generate_splunk_app.py.\n"
        "     Edits here are overwritten on the next regeneration.  -->\n"
        f"<nav search_view=\"search\" default_view=\"{dashboard}\">\n"
        f"  <view name=\"{dashboard}\" default=\"true\" />\n"
        "  <view name=\"search\" />\n"
        f"  <collection label=\"{_escape_xml(short)}\">\n"
        f"    <view name=\"{dashboard}\" />\n"
        f"    <a href=\"search?q=eventtype%3Duc_compliance_{fw_id}_uncategorised\">"
        f"All {_escape_xml(short)} alerts</a>\n"
        "  </collection>\n"
        "</nav>\n"
    )


_XML_ESCAPE_MAP = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
}


def _escape_xml(value: str) -> str:
    """Escape ``value`` for Splunk Simple XML (attributes + element text).

    Splunk's Simple XML parser is strict — an unescaped ampersand in a
    panel title is enough to break the whole dashboard.  We emit
    dashboards deterministically from catalogue data that we do not
    control end-to-end, so every interpolated field runs through this
    helper before being written.
    """
    out = []
    for ch in str(value):
        mapped = _XML_ESCAPE_MAP.get(ch)
        if mapped is not None:
            out.append(mapped)
        else:
            out.append(ch)
    return "".join(out)


def _dashboard_xml(
    fw: Mapping[str, Any],
    ucs: Sequence[Mapping[str, Any]],
    version: str,
    generated_at: str,
) -> str:
    """Return a Simple XML compliance-posture dashboard for ``fw``.

    The dashboard reads exclusively from the per-app
    ``uc_compliance_mappings`` lookup (see :func:`_transforms_conf`), so
    it works on a clean install **before** any saved search has been
    enabled.  That keeps the install story simple: install the app, open
    the dashboard, see coverage.  Operators can then schedule the saved
    searches that matter to them.

    Panels:

    * Three single-value header cells (total UCs, critical UCs, distinct
      clauses tagged) provide the one-glance answer auditors ask for.
    * A column chart summarises UC count per criticality.
    * A bar chart lists the top 15 most-referenced clauses.
    * A column chart breaks down mappings by assurance bucket (full,
      partial, contributing, unspecified) so reviewers can spot where
      evidence is thin.
    * A table enumerates every UC with its clause list, criticality, and
      source-path link — the auditor-facing evidence inventory.

    All SPL in the dashboard is idempotent, offline-friendly, and uses
    ``inputlookup`` only, which Splunk Cloud vetting accepts without
    caveats.
    """
    fw_id = fw["id"]
    short = fw.get("shortName") or fw_id.upper()
    name = fw.get("name") or short
    dashboard_id = f"{fw_id.replace('-', '_')}_compliance_posture"
    uc_count = len(ucs)

    description = (
        f"Compliance posture for {_escape_xml(name)} "
        f"({_escape_xml(short)}).  Generated from the Splunk Monitoring "
        f"Use Cases catalogue v{_escape_xml(version)} on "
        f"{_escape_xml(generated_at)}.  All panels read the per-app "
        "'uc_compliance_mappings' lookup so the dashboard works before "
        "any saved search is enabled."
    )

    # Use ASCII-only SPL strings so AppInspect's static text scans don't
    # flag exotic characters.  Ampersands inside SPL survive XML encoding
    # via _escape_xml.  Each <query> is wrapped in CDATA for readability
    # when operators open the XML in the Splunk UI.
    tile_total = (
        f"| inputlookup uc_compliance_mappings "
        f"| stats dc(uc_id) as count"
    )
    tile_critical = (
        f"| inputlookup uc_compliance_mappings "
        f"| where criticality=\"critical\" "
        f"| stats dc(uc_id) as count"
    )
    tile_clauses = (
        f"| inputlookup uc_compliance_mappings "
        f"| where clause!=\"\" "
        f"| stats dc(clause) as count"
    )
    by_criticality = (
        f"| inputlookup uc_compliance_mappings "
        f"| eval criticality=if(len(criticality)=0, \"unspecified\", criticality) "
        f"| stats dc(uc_id) as ucs by criticality "
        f"| sort -ucs"
    )
    top_clauses = (
        f"| inputlookup uc_compliance_mappings "
        f"| where clause!=\"\" "
        f"| stats dc(uc_id) as ucs by clause "
        f"| sort -ucs "
        f"| head 15"
    )
    by_assurance = (
        f"| inputlookup uc_compliance_mappings "
        f"| eval assurance=if(len(assurance)=0, \"unspecified\", assurance) "
        f"| stats count as mappings by assurance "
        f"| sort -mappings"
    )
    uc_catalog = (
        f"| inputlookup uc_compliance_mappings "
        f"| eval clause=if(len(clause)=0, \"(unspecified)\", clause) "
        f"| stats "
        f"  values(clause) as clauses "
        f"  values(criticality) as criticality "
        f"  values(assurance) as assurance "
        f"  values(source_path) as source_path "
        f"  by uc_id title "
        f"| eval clauses=mvjoin(clauses, \", \") "
        f"| sort uc_id"
    )

    lines: List[str] = [
        "<!-- Auto-generated by scripts/generate_splunk_app.py — do not edit. -->",
        f"<dashboard version=\"1.1\" theme=\"light\" script=\"\" stylesheet=\"\">",
        f"  <label>{_escape_xml(short)} compliance posture</label>",
        f"  <description>{description}</description>",
        "",
        "  <row>",
        "    <panel>",
        f"      <title>Total UCs packaged ({uc_count} sidecars)</title>",
        "      <single>",
        f"        <search>",
        f"          <query><![CDATA[{tile_total}]]></query>",
        "          <earliest>-1m</earliest>",
        "          <latest>now</latest>",
        "        </search>",
        "        <option name=\"colorBy\">value</option>",
        "        <option name=\"underLabel\">use cases with clause mappings</option>",
        "        <option name=\"rangeColors\">[\"0x118832\",\"0x118832\"]</option>",
        "      </single>",
        "    </panel>",
        "    <panel>",
        "      <title>Critical-tier UCs</title>",
        "      <single>",
        "        <search>",
        f"          <query><![CDATA[{tile_critical}]]></query>",
        "          <earliest>-1m</earliest>",
        "          <latest>now</latest>",
        "        </search>",
        "        <option name=\"colorBy\">value</option>",
        "        <option name=\"underLabel\">review these first</option>",
        "        <option name=\"rangeColors\">[\"0xb1334e\",\"0xb1334e\"]</option>",
        "      </single>",
        "    </panel>",
        "    <panel>",
        "      <title>Distinct clauses tagged</title>",
        "      <single>",
        "        <search>",
        f"          <query><![CDATA[{tile_clauses}]]></query>",
        "          <earliest>-1m</earliest>",
        "          <latest>now</latest>",
        "        </search>",
        "        <option name=\"colorBy\">value</option>",
        "        <option name=\"underLabel\">regulatory articles / sections</option>",
        "        <option name=\"rangeColors\">[\"0x0070b5\",\"0x0070b5\"]</option>",
        "      </single>",
        "    </panel>",
        "  </row>",
        "",
        "  <row>",
        "    <panel>",
        "      <title>UCs by criticality</title>",
        "      <chart>",
        "        <search>",
        f"          <query><![CDATA[{by_criticality}]]></query>",
        "          <earliest>-1m</earliest>",
        "          <latest>now</latest>",
        "        </search>",
        "        <option name=\"charting.chart\">column</option>",
        "        <option name=\"charting.axisTitleX.text\">criticality</option>",
        "        <option name=\"charting.axisTitleY.text\">distinct UCs</option>",
        "        <option name=\"charting.legend.placement\">none</option>",
        "      </chart>",
        "    </panel>",
        "    <panel>",
        "      <title>Most-referenced clauses (top 15)</title>",
        "      <chart>",
        "        <search>",
        f"          <query><![CDATA[{top_clauses}]]></query>",
        "          <earliest>-1m</earliest>",
        "          <latest>now</latest>",
        "        </search>",
        "        <option name=\"charting.chart\">bar</option>",
        "        <option name=\"charting.axisTitleX.text\">clause</option>",
        "        <option name=\"charting.axisTitleY.text\">distinct UCs</option>",
        "        <option name=\"charting.legend.placement\">none</option>",
        "      </chart>",
        "    </panel>",
        "  </row>",
        "",
        "  <row>",
        "    <panel>",
        "      <title>Mappings by assurance bucket</title>",
        "      <chart>",
        "        <search>",
        f"          <query><![CDATA[{by_assurance}]]></query>",
        "          <earliest>-1m</earliest>",
        "          <latest>now</latest>",
        "        </search>",
        "        <option name=\"charting.chart\">column</option>",
        "        <option name=\"charting.axisTitleX.text\">assurance</option>",
        "        <option name=\"charting.axisTitleY.text\">mappings</option>",
        "        <option name=\"charting.legend.placement\">none</option>",
        "      </chart>",
        "    </panel>",
        "  </row>",
        "",
        "  <row>",
        "    <panel>",
        "      <title>UC inventory (clauses, criticality, evidence path)</title>",
        "      <table>",
        "        <search>",
        f"          <query><![CDATA[{uc_catalog}]]></query>",
        "          <earliest>-1m</earliest>",
        "          <latest>now</latest>",
        "        </search>",
        "        <option name=\"count\">25</option>",
        "        <option name=\"drilldown\">none</option>",
        "        <option name=\"wrap\">true</option>",
        "        <option name=\"rowNumbers\">false</option>",
        "      </table>",
        "    </panel>",
        "  </row>",
        "</dashboard>",
    ]
    # Ensure we always end with a single trailing newline — Splunk is
    # tolerant but deterministic writers elsewhere in this file maintain
    # the same convention, so keep the whole tree consistent.
    return "\n".join(lines) + "\n"


def _lookup_csv(ucs: Sequence[Mapping[str, Any]], fw_id: str) -> str:
    """One row per (UC, compliance entry) tuple for the lookup."""
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
    rows: List[Tuple[str, ...]] = []
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
                    entry.get("regulation") or "",
                    entry.get("version") or "",
                    entry.get("clause") or "",
                    entry.get("clauseUrl") or "",
                    entry.get("assurance") or "",
                    entry.get("mode") or "",
                    source_path,
                )
            )
    rows.sort()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def _readme_body(
    fw: Mapping[str, Any],
    ucs: Sequence[Mapping[str, Any]],
    version: str,
    generated_at: str,
) -> str:
    fw_id = fw["id"]
    short = fw.get("shortName") or fw_id.upper()
    name = fw.get("name") or short

    clause_set: Dict[str, int] = {}
    for uc in ucs:
        for entry in uc.get("_matchedCompliance") or []:
            clause = str(entry.get("clause") or "").strip()
            if clause:
                clause_set[clause] = clause_set.get(clause, 0) + 1
    top_clauses = sorted(clause_set.items(), key=lambda x: (-x[1], x[0]))[:8]

    criticality_counts: Dict[str, int] = {}
    for uc in ucs:
        c = (uc.get("criticality") or "unspecified").lower()
        criticality_counts[c] = criticality_counts.get(c, 0) + 1

    uc_rows = []
    for uc in ucs:
        clauses = sorted(
            {str(e.get("clause") or "").strip() for e in (uc.get("_matchedCompliance") or []) if e.get("clause")}
        )
        clauses_display = ", ".join(clauses[:3]) + ("…" if len(clauses) > 3 else "")
        uc_rows.append(
            f"| UC-{uc.get('id')} | {(uc.get('title') or '').replace('|','\\|')} | "
            f"{(uc.get('criticality') or '').lower()} | {clauses_display} |"
        )

    header = (
        f"# Splunk Use Cases — {short} compliance\n"
        f"\n"
        f"App ID: `splunk-uc-{fw_id}`  \n"
        f"App version: **{version}**  \n"
        f"Generated: `{generated_at}`  \n"
        f"Upstream catalogue: [fenre/splunk-monitoring-use-cases]"
        f"(https://github.com/fenre/splunk-monitoring-use-cases)\n"
        f"\n"
    )
    summary = (
        f"This app packages **{len(ucs)} use cases** from the upstream "
        f"catalogue that cite {name} (`{fw_id}`), together with the macros, "
        f"eventtypes, tags, and lookup needed to operate them.  Every saved "
        f"search is shipped **disabled by default** so an operator can review "
        f"the SPL and tune indexes before enabling.\n"
        f"\n"
        f"* Regulation tier: **{fw.get('tier', 'n/a')}**\n"
        f"* Jurisdictions: {', '.join(fw.get('jurisdiction') or ['n/a'])}\n"
        f"* Versions covered: {', '.join(v.get('version') for v in (fw.get('versions') or []) if v.get('version'))}\n"
        f"* UCs by criticality: {', '.join(f'{k} = {v}' for k, v in sorted(criticality_counts.items()))}\n"
        f"\n"
    )

    clauses_section = ["## Most-referenced clauses", ""]
    if top_clauses:
        clauses_section.append("| Clause | UCs tagging this clause |")
        clauses_section.append("|--------|-------------------------|")
        for clause, n in top_clauses:
            clauses_section.append(f"| `{clause}` | {n} |")
    else:
        clauses_section.append(
            "_No UCs in this app tag a specific clause yet.  Gap analysis "
            "lives in `api/v1/compliance/gaps.json`._"
        )
    clauses_section.append("")

    install = (
        "## Installation\n"
        "\n"
        "1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` "
        "ships disabled.  Before enabling, replace placeholder `index=` patterns "
        "with your site's indexes and macros.\n"
        "2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or "
        "package it with `tar czf splunk-uc-" + fw_id + ".spl splunk-uc-" + fw_id + "/` "
        "and deploy via the Splunk app manager.\n"
        "3. **Open the compliance posture dashboard.**  The navigation lands on "
        f"`{fw_id.replace('-', '_')}_compliance_posture` — a Simple XML "
        "dashboard that reads the shipped `uc_compliance_mappings` lookup and "
        "works before any saved search is scheduled.  Use it to brief "
        "auditors, track clause coverage, and spot mappings with thin "
        "assurance.\n"
        "4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, "
        "enable and schedule the stanzas your team is ready to operate.\n"
        "5. **Audit trail.**  Every saved search carries the UC id, the "
        "regulation version, and the full clause list on its "
        "`action.uc_compliance.param.*` attributes.  These are auditor-friendly "
        "and survive Splunk's saved-search lifecycle (no lookup required).\n"
        "\n"
    )

    appinspect = (
        "## AppInspect / Splunk Cloud readiness\n"
        "\n"
        "The generator targets AppInspect's baseline checks:\n"
        "\n"
        "* `app.manifest` version 2.0.0 with the full `info` block.\n"
        "* `default/app.conf` carries `[install]`, `[ui]`, `[launcher]`, and "
        "`[package]` sections.\n"
        "* `metadata/default.meta` keeps `savedsearches` private, exports "
        "macros / eventtypes / tags / transforms / lookups at `system` "
        "scope, and the generated dashboard at `app` scope.\n"
        "* The posture dashboard uses Simple XML 1.1 with CDATA-wrapped "
        "queries that rely exclusively on `inputlookup` — no external "
        "data, no custom visualisations, no scripted inputs.\n"
        "* No custom search commands or `local/` overrides are shipped.\n"
        "* MIT licence file committed at the app root.\n"
        "\n"
        "The per-regulation app still depends on your site's CIM / "
        "Enterprise Security installation for `\\`notable\\`` and "
        "`\\`summariesonly\\`` macros when saved searches are enabled; "
        "see the upstream `scripts/audit_splunk_cloud_compat.py` report.\n"
        "\n"
    )

    dashboard_section = (
        "## Compliance posture dashboard\n"
        "\n"
        "The app ships a Simple XML dashboard at "
        f"`default/data/ui/views/{fw_id.replace('-', '_')}_compliance_posture.xml` "
        "that reads the per-app `uc_compliance_mappings` lookup.  The "
        "dashboard needs zero saved searches to render — install the app, "
        "open the dashboard, brief your auditor.\n"
        "\n"
        "Panels:\n"
        "\n"
        "1. **Total UCs packaged** — single value.\n"
        "2. **Critical-tier UCs** — single value, review-first cohort.\n"
        "3. **Distinct clauses tagged** — single value.\n"
        "4. **UCs by criticality** — column chart.\n"
        "5. **Most-referenced clauses (top 15)** — bar chart.\n"
        "6. **Mappings by assurance bucket** — column chart "
        "(full / partial / contributing / unspecified).\n"
        "7. **UC inventory** — full catalogue table with source-path "
        "references back to the upstream catalogue.\n"
        "\n"
    )

    uc_table_header = [
        "## Covered use cases",
        "",
        "| UC | Title | Criticality | Clauses |",
        "|----|-------|-------------|---------|",
    ]

    parts: List[str] = [
        header,
        summary,
        *clauses_section,
        install,
        dashboard_section,
        appinspect,
    ]
    parts.extend(uc_table_header)
    parts.extend(uc_rows)
    parts.append("")
    parts.append(
        "---\n\n"
        "_This app is generated; edits in place will be overwritten.  "
        "File bug reports and content requests at "
        "https://github.com/fenre/splunk-monitoring-use-cases/issues._\n"
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _build_app(
    fw: Mapping[str, Any],
    ucs: Sequence[Mapping[str, Any]],
    out_root: pathlib.Path,
    version: str,
    generated_at: str,
) -> pathlib.Path:
    """Write one app tree for ``fw`` under ``out_root/<reg-id>/``.

    Returns the app root path.
    """
    fw_id = fw["id"]
    app_root = out_root / f"splunk-uc-{fw_id}"
    # Files that should always exist:
    _write_text(
        app_root / "default" / "app.conf",
        _app_conf(fw, version),
    )
    _write_text(
        app_root / "default" / "savedsearches.conf",
        _savedsearches_conf(ucs, fw_id),
    )
    _write_text(
        app_root / "default" / "eventtypes.conf",
        _eventtypes_conf(ucs, fw_id),
    )
    _write_text(
        app_root / "default" / "macros.conf",
        _macros_conf(fw_id),
    )
    _write_text(
        app_root / "default" / "tags.conf",
        _tags_conf(fw_id),
    )
    _write_text(
        app_root / "default" / "transforms.conf",
        _transforms_conf(fw_id),
    )
    _write_text(
        app_root / "default" / "data" / "ui" / "nav" / "default.xml",
        _nav_default_xml(fw),
    )
    _write_text(
        app_root / "default" / "data" / "ui" / "views"
        / f"{fw_id.replace('-', '_')}_compliance_posture.xml",
        _dashboard_xml(fw, ucs, version, generated_at),
    )
    _write_text(
        app_root / "metadata" / "default.meta",
        _default_meta(),
    )
    _write_text(
        app_root / "lookups" / "uc_compliance_mappings.csv",
        _lookup_csv(ucs, fw_id),
    )
    _write_json(
        app_root / "app.manifest",
        _app_manifest(fw, version),
    )
    _write_text(
        app_root / "README.md",
        _readme_body(fw, ucs, version, generated_at),
    )
    # Copy the top-level MIT licence verbatim so every packaged app ships a
    # self-contained licence (Splunkbase requirement).
    if LICENSE_FILE.exists():
        (app_root / "LICENSE").write_text(
            LICENSE_FILE.read_text(encoding="utf-8"),
            encoding="utf-8",
            newline="\n",
        )
    return app_root


def _select_regulations(
    regs: Mapping[str, Any],
    ucs: Sequence[Mapping[str, Any]],
    alias_map: Mapping[str, str],
    requested: Optional[Sequence[str]],
) -> List[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
    """Return ``[(framework_dict, ucs_list), …]`` ordered by framework id.

    Default selection (``requested is None``) now mirrors the Phase 5.1
    exit criterion: every tier-1 regulation that has at least one tagged
    UC **plus** the derivative regulations enumerated in
    ``_DEFAULT_DERIVATIVE_APP_IDS``.  For the initial cut that adds
    UK GDPR (tier-2, identity derivative of GDPR) so the generator lands
    the 12 per-regulation apps the plan requires.

    Explicit ``--regulation`` overrides still work for one-off builds
    (tier-2/tier-3 experiments, smoke tests) without pulling in the
    default derivative set.
    """
    by_id = _framework_by_id(regs)
    selected: List[Tuple[Dict[str, Any], List[Dict[str, Any]]]] = []
    seen_ids: set[str] = set()

    def _append(fw_id: str, fw: Mapping[str, Any]) -> None:
        reg_ucs = _ucs_for_regulation(fw_id, ucs, alias_map)
        if not reg_ucs:
            return
        if fw_id in seen_ids:
            return
        selected.append((dict(fw), reg_ucs))
        seen_ids.add(fw_id)

    if requested:
        for raw in requested:
            fw_id = alias_map.get(raw.lower()) or raw
            fw = by_id.get(fw_id)
            if not fw:
                raise SystemExit(
                    f"Unknown regulation '{raw}'. Known ids: "
                    f"{', '.join(sorted(by_id))[:400]}…"
                )
            # ``--regulation`` is an explicit opt-in: we still emit the
            # app even if ``_ucs_for_regulation`` returns zero so callers
            # can test the scaffolding end-to-end.  In that case the
            # saved-search list is empty and the README makes the gap
            # visible.
            reg_ucs = _ucs_for_regulation(fw_id, ucs, alias_map)
            if fw_id in seen_ids:
                continue
            selected.append((dict(fw), reg_ucs))
            seen_ids.add(fw_id)
        return selected

    for fw_id, fw in sorted(by_id.items()):
        if (fw.get("tier") or 99) > 1:
            continue
        _append(fw_id, fw)

    # Derivative additions (sorted for determinism).  A missing framework
    # id here is a content error — fail loudly so the maintainer adds it
    # to ``data/regulations.json`` rather than silently dropping an app.
    for fw_id in sorted(_DEFAULT_DERIVATIVE_APP_IDS):
        fw = by_id.get(fw_id)
        if not fw:
            raise SystemExit(
                f"Default derivative app '{fw_id}' is listed in "
                f"_DEFAULT_DERIVATIVE_APP_IDS but no matching framework "
                f"exists in data/regulations.json.  Either add the "
                f"framework or remove the id from the allow-list."
            )
        _append(fw_id, fw)

    return selected


def _render(out_root: pathlib.Path, requested: Optional[Sequence[str]]) -> Dict[str, int]:
    regs = _load_json(REGULATIONS_FILE)
    ucs = _load_ucs()
    alias_map = _regulation_alias_to_id(regs)
    version = _read_version()
    generated_at = _deterministic_timestamp()

    out_root.mkdir(parents=True, exist_ok=True)
    # Any leftover generated trees that shouldn't be there get pruned so
    # --check stays truthful.  We leave unrelated files alone (only prune
    # subdirectories prefixed ``splunk-uc-``).
    expected_dirs: List[pathlib.Path] = []
    summary: Dict[str, int] = {}

    for fw, reg_ucs in _select_regulations(regs, ucs, alias_map, requested):
        app_dir = _build_app(fw, reg_ucs, out_root, version, generated_at)
        expected_dirs.append(app_dir)
        summary[fw["id"]] = len(reg_ucs)

    # Prune stale apps under out_root (only those matching our naming scheme).
    for child in sorted(out_root.iterdir()):
        if not child.name.startswith("splunk-uc-"):
            continue
        if child in expected_dirs:
            continue
        if child.name in _EXTERNAL_APP_IDS:
            # Owned by a sibling generator — never touch.
            continue
        shutil.rmtree(child)

    _write_json(
        out_root / "manifest.json",
        {
            "generatedAt": generated_at,
            "catalogueVersion": version,
            "apps": [
                {
                    "id": f"splunk-uc-{fw_id}",
                    "regulation": fw_id,
                    "ucCount": count,
                }
                for fw_id, count in sorted(summary.items())
            ],
        },
    )
    return summary


def _diff_trees(lhs: pathlib.Path, rhs: pathlib.Path) -> List[str]:
    """Diff two app trees, skipping sibling-owned subtrees."""
    diffs: List[str] = []
    lhs_files = {
        p.relative_to(lhs)
        for p in lhs.rglob("*")
        if p.is_file() and not _is_external_app(p.relative_to(lhs))
    }
    rhs_files = {
        p.relative_to(rhs)
        for p in rhs.rglob("*")
        if p.is_file() and not _is_external_app(p.relative_to(rhs))
    }
    for p in sorted(lhs_files - rhs_files):
        diffs.append(f"- {p}")
    for p in sorted(rhs_files - lhs_files):
        diffs.append(f"+ {p}")
    for p in sorted(lhs_files & rhs_files):
        if (lhs / p).read_bytes() != (rhs / p).read_bytes():
            diffs.append(f"  differs: {p}")
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate per-regulation Splunk app trees from the compliance catalogue.",
    )
    parser.add_argument(
        "--regulation",
        action="append",
        dest="regulations",
        metavar="ID",
        help="Limit generation to one or more regulation ids (repeat the flag). "
        "Default: every tier-1 regulation with >= 1 tagged UC.",
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
        help="Regenerate into a temp dir and diff against --output. "
        "Exits 1 if anything differs.",
    )
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = pathlib.Path(tmp) / "splunk-apps"
            _render(tmp_root, args.regulations)
            diffs = _diff_trees(args.output, tmp_root)
            if diffs:
                sys.stderr.write(
                    "Splunk app tree drift detected — regenerate with "
                    "`python3 scripts/generate_splunk_app.py` and commit:\n"
                )
                for line in diffs[:200]:
                    sys.stderr.write(line + "\n")
                if len(diffs) > 200:
                    sys.stderr.write(f"... {len(diffs) - 200} additional diffs omitted\n")
                return 1
            sys.stdout.write("Splunk apps are up to date.\n")
            return 0

    summary = _render(args.output, args.regulations)
    total_ucs = sum(summary.values())
    sys.stdout.write(
        f"Wrote {len(summary)} apps ({total_ucs} saved searches) under {args.output}\n"
    )
    for fw_id, count in sorted(summary.items()):
        sys.stdout.write(f"  splunk-uc-{fw_id}: {count} UCs\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
