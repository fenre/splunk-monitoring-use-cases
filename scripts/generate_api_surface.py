#!/usr/bin/env python3
"""Generate the ``api/v1/*`` static JSON API surface.

Tier-1 deliverable from the Gold-Standard plan (Phase 1.7). The script is
the single source of truth for the committed API: running it must always
produce byte-identical output from the same inputs so that CI can diff the
tree and block merges that forget to regenerate it.

Inputs (all in-repo, no network):

* ``schemas/uc.schema.json``            - authoring schema (copied verbatim).
* ``data/regulations.json``             - multi-version regulation catalogue.
* ``use-cases/cat-*/uc-*.json``         - UC sidecars with compliance[].
* ``data/crosswalks/olir/*.normalised.json``
* ``data/crosswalks/oscal/*.normalised.json``
  ``data/crosswalks/oscal/component-definition-*.json``
* ``data/crosswalks/attack/*.normalised.json``
* ``data/crosswalks/d3fend/*.normalised.json``
* ``reports/compliance-coverage.json``  - 3 coverage metrics at every scope.

Outputs (written to ``api/v1/``):

* ``manifest.json``                     - endpoint catalogue + versions.
* ``context.jsonld``                    - JSON-LD context for linked data consumers.
* ``openapi.yaml``                      - OpenAPI 3.1 spec (copied verbatim).
* ``README.md``                         - developer quick start (copied verbatim).
* ``compliance/index.json``             - top-level compliance index.
* ``compliance/coverage.json``          - 3 metrics, same shape as the report.
* ``compliance/gaps.json``              - uncovered common clauses per regulation.
* ``compliance/regulations/index.json`` - flat index of all regulations.
* ``compliance/regulations/<id>.json``  - full regulation metadata (all versions).
* ``compliance/regulations/<id>@<version>.json``
                                        - single-version slice with the UCs
                                          that claim any clause from it.
* ``compliance/ucs/index.json``         - compact list of UCs touching compliance.
* ``compliance/ucs/<id>.json``          - full UC sidecar (canonical form).
* ``oscal/index.json``
* ``oscal/catalogs/<id>.json``          - normalised NIST catalogs.
* ``oscal/component-definitions/index.json``
* ``oscal/component-definitions/<uc>.json`` - OSCAL component-definition per UC.
* ``mitre/index.json``
* ``mitre/techniques.json``             - flat list of all techniques referenced.
* ``mitre/coverage.json``               - UC -> technique[] + per-tactic buckets.
* ``mitre/d3fend.json``                 - D3FEND countermeasure mapping.
* ``recommender/sourcetype-index.json`` - sourcetype -> UC ids (full 6k catalogue).
* ``recommender/cim-index.json``        - CIM model -> UC ids.
* ``recommender/app-index.json``        - Splunk app/TA -> UC ids.
* ``recommender/uc-thin.json``          - compact UC records for the recommender UI.
* ``equipment/index.json``              - equipment slug -> UC ids + regulation
                                          ids, joining the EQUIPMENT registry in
                                          ``build.py`` with the structured
                                          ``equipment[]`` / ``equipmentModels[]``
                                          fields populated by
                                          ``scripts/generate_equipment_tags.py``.
                                          Answers the auditor question "which
                                          regulations does logging equipment X
                                          help satisfy?".
* ``equipment/<id>.json``               - per-equipment detail: full UC list
                                          grouped by category and regulation,
                                          model breakdown, and a compliance
                                          summary.

Design invariants:

* **Deterministic**: every ``json.dump`` uses ``sort_keys=True``, ``indent=2``,
  ``ensure_ascii=False`` and an explicit trailing newline. Any list in the
  output is sorted by a stable key before serialisation.
* **Additive-only within v1**: the generator MUST NOT remove or rename a
  committed endpoint under ``api/v1/``. Breaking changes land under
  ``api/v2/`` per ``docs/api-versioning.md``.
* **Offline**: zero network calls.
* **Side-effect safe**: ``--check`` regenerates into a temp dir and diffs
  against the committed tree so CI can fail on drift.

Exit codes:
    0  Success.
    1  Validation failure (missing/invalid input, determinism check failed).
    2  Uncaught exception (bug).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

# Local import: the EQUIPMENT catalogue is built from build.py via
# scripts/equipment_lib.py. We use it only to look up display labels for
# the new equipment/index.json facade — the authoritative per-UC
# equipment tags come from the sidecars (compliance UCs) or catalog.json
# (full catalogue). sys.path insertion keeps this file runnable from
# anywhere the repo is checked out.
_THIS_DIR = pathlib.Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
from equipment_lib import load_equipment  # noqa: E402  (post-sys.path hack)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
API_VERSION = "v1"
API_ROOT = REPO_ROOT / "api" / API_VERSION

SCHEMA_PATH = REPO_ROOT / "schemas" / "uc.schema.json"
REGS_PATH = REPO_ROOT / "data" / "regulations.json"
OSCAL_DIR = REPO_ROOT / "data" / "crosswalks" / "oscal"
ATTACK_DIR = REPO_ROOT / "data" / "crosswalks" / "attack"
D3FEND_DIR = REPO_ROOT / "data" / "crosswalks" / "d3fend"
OLIR_DIR = REPO_ROOT / "data" / "crosswalks" / "olir"
COVERAGE_REPORT = REPO_ROOT / "reports" / "compliance-coverage.json"
UC_GLOB = "content/cat-*/UC-*.json"
CATALOG_PATH = REPO_ROOT / "catalog.json"
VERSION_FILE = REPO_ROOT / "VERSION"

NAMESPACE = "https://fenre.github.io/splunk-monitoring-use-cases"


def _deterministic_timestamp() -> str:
    """Stable UTC timestamp for committed API files.

    Uses the same resolution order as ``scripts/audit_compliance_mappings.py``
    so CI and local runs on the same commit produce byte-identical JSON.
    """
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    sde = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if sde.isdigit():
        return time.strftime(fmt, time.gmtime(int(sde)))
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", "-1", "--pretty=%ct", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        ts = out.stdout.strip()
        if ts.isdigit():
            return time.strftime(fmt, time.gmtime(int(ts)))
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return time.strftime(fmt, time.gmtime())


def _read_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _write_json(path: pathlib.Path, payload: Any) -> None:
    """Write ``payload`` to ``path`` deterministically.

    * UTF-8, no BOM.
    * ``sort_keys=True``, ``indent=2``.
    * ``ensure_ascii=False`` so human-readable clause citations (e.g. ``§``)
      stay intact.
    * Trailing newline so the file plays nicely with text tools and git.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def _write_text(path: pathlib.Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not payload.endswith("\n"):
        payload = payload + "\n"
    path.write_text(payload, encoding="utf-8")


def _load_json(path: pathlib.Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# UC sidecars
# ---------------------------------------------------------------------------


def _load_ucs() -> List[Dict[str, Any]]:
    ucs: List[Dict[str, Any]] = []
    for path in sorted(REPO_ROOT.glob(UC_GLOB)):
        try:
            data = _load_json(path)
        except json.JSONDecodeError as err:
            raise SystemExit(f"ERROR: invalid JSON in {path}: {err}") from err
        uc_id = data.get("id")
        if not isinstance(uc_id, str):
            raise SystemExit(f"ERROR: {path} is missing a string 'id'")
        data["_category"] = int(uc_id.split(".", 1)[0])
        data["_sourcePath"] = str(path.relative_to(REPO_ROOT))
        ucs.append(data)
    ucs.sort(key=_uc_sort_key)
    return ucs


_ID_RX = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _uc_sort_key(uc: Mapping[str, Any]) -> Tuple[int, int, int]:
    m = _ID_RX.match(uc.get("id", ""))
    if not m:
        return (10**6, 10**6, 10**6)
    return tuple(int(x) for x in m.groups())  # type: ignore[return-value]


def _uc_compact(
    uc: Mapping[str, Any],
    alias_to_id: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Reduce a UC to the fields indexes need (for network-friendly lists).

    The ``regulationIds`` field normalises free-text ``regulation`` strings to
    canonical framework ids so consumers can link straight to
    ``/api/v1/compliance/regulations/<id>.json`` without re-doing alias resolution.
    """
    lookup = alias_to_id or {}
    raw_pairs = sorted(
        {
            f"{c.get('regulation')}@{c.get('version')}"
            for c in uc.get("compliance") or []
            if c.get("regulation") and c.get("version")
        }
    )
    normalised_pairs = sorted(
        {
            f"{lookup.get(str(c.get('regulation')).lower(), str(c.get('regulation')).lower())}@{c.get('version')}"
            for c in uc.get("compliance") or []
            if c.get("regulation") and c.get("version")
        }
    )
    # ``wave`` + ``prerequisiteUseCases`` power the implementation-ordering
    # roadmap: ``wave`` bins the UC into crawl/walk/run, the prereq list
    # lets API consumers walk the dependency graph forward. Keys stay
    # sorted for deterministic output regardless of source-file ordering.
    pre_raw = uc.get("prerequisiteUseCases", []) or []
    return {
        "id": uc["id"],
        "title": uc.get("title", ""),
        "category": uc.get("_category"),
        "criticality": uc.get("criticality"),
        "difficulty": uc.get("difficulty"),
        "wave": uc.get("wave"),
        "prerequisiteUseCases": sorted({str(p) for p in pre_raw if p}),
        "owner": uc.get("owner"),
        "controlFamily": uc.get("controlFamily"),
        "monitoringType": sorted(uc.get("monitoringType", []) or []),
        "regulations": raw_pairs,
        "regulationIds": normalised_pairs,
        "mitreAttack": sorted(uc.get("mitreAttack", []) or []),
        "equipment": sorted(uc.get("equipment", []) or []),
        "equipmentModels": sorted(uc.get("equipmentModels", []) or []),
        "hasControlTest": bool(uc.get("controlTest")),
        "status": uc.get("status"),
    }


# ---------------------------------------------------------------------------
# Regulations facade
# ---------------------------------------------------------------------------


def _regulation_alias_to_id(regs: Mapping[str, Any]) -> Dict[str, str]:
    """Build a case-insensitive alias -> canonical framework id map.

    Mirrors the resolution strategy in
    ``scripts/audit_compliance_mappings.py::RegulationsCatalogue``: aliases
    resolve to the framework ``id`` (e.g. ``gdpr``), not the ``shortName``
    (``GDPR``). The ``shortName`` is a display property; the ``id`` is the
    stable primary key.
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
    # Explicit entries in regulations.json aliasIndex take precedence
    # because they may resolve tricky free-text UC strings to a specific
    # framework id (see data/regulations.json aliasIndex).
    for alias, target in (regs.get("aliasIndex") or {}).items():
        if alias.startswith("$"):
            continue  # skip $comment sentinels
        out[str(alias).lower()] = str(target)
    return out


def _regulations_index(regs: Mapping[str, Any]) -> Dict[str, Any]:
    frameworks = []
    for fw in regs.get("frameworks", []):
        versions = sorted(
            {v.get("version") for v in fw.get("versions", []) if v.get("version")}
        )
        frameworks.append(
            {
                "id": fw.get("id"),
                "shortName": fw.get("shortName"),
                "name": fw.get("name"),
                "tier": fw.get("tier"),
                "jurisdiction": sorted(fw.get("jurisdiction") or []),
                "tags": sorted(fw.get("tags") or []),
                "aliases": sorted(fw.get("aliases") or []),
                "versions": versions,
                "endpoint": f"/api/{API_VERSION}/compliance/regulations/{fw.get('id')}.json",
            }
        )
    frameworks.sort(key=lambda f: (f.get("id") or "").lower())
    return {
        "apiVersion": API_VERSION,
        "schemaVersion": regs.get("schemaVersion"),
        "frameworkCount": len(frameworks),
        "frameworks": frameworks,
    }


def _regulation_detail(
    fw: Mapping[str, Any],
    uc_index_by_reg: Mapping[str, List[str]],
) -> Dict[str, Any]:
    fid = fw.get("id", "")
    short = fw.get("shortName") or fid
    versions_out: List[Dict[str, Any]] = []
    for v in fw.get("versions", []) or []:
        key = f"{fid}@{v.get('version')}"
        clauses_used = sorted(set(uc_index_by_reg.get(f"{key}|clauses") or []))
        ucs_claiming = sorted(set(uc_index_by_reg.get(f"{key}|ucs") or []))
        versions_out.append(
            {
                "version": v.get("version"),
                "authoritativeUrl": v.get("authoritativeUrl"),
                "effectiveFrom": v.get("effectiveFrom"),
                "sunsetOn": v.get("sunsetOn"),
                "clauseGrammar": v.get("clauseGrammar"),
                "clauseExamples": list(v.get("clauseExamples") or []),
                "clauseUrlTemplate": v.get("clauseUrlTemplate"),
                "commonClauses": list(v.get("commonClauses") or []),
                "pendingChanges": list(v.get("pendingChanges") or []),
                "clausesReferencedByCatalogue": clauses_used,
                "useCasesTaggingThisVersion": ucs_claiming,
                "endpoint": (
                    f"/api/{API_VERSION}/compliance/regulations/"
                    f"{fw.get('id')}@{_safe_version(v.get('version'))}.json"
                ),
            }
        )
    versions_out.sort(key=lambda x: str(x.get("version") or ""))
    return {
        "apiVersion": API_VERSION,
        "id": fw.get("id"),
        "shortName": short,
        "name": fw.get("name"),
        "tier": fw.get("tier"),
        "jurisdiction": sorted(fw.get("jurisdiction") or []),
        "tags": sorted(fw.get("tags") or []),
        "aliases": sorted(fw.get("aliases") or []),
        "versions": versions_out,
    }


_SAFE_VERSION_RX = re.compile(r"[^A-Za-z0-9._+-]")


def _safe_version(version: Optional[str]) -> str:
    """Filesystem-safe version slug for ``regulations/<id>@<version>.json``."""
    if not version:
        return "unknown"
    # Replace unsafe characters with a hyphen; keep the representation
    # reasonably human-readable so dev tools can autocomplete paths.
    return _SAFE_VERSION_RX.sub("-", str(version))


# ---------------------------------------------------------------------------
# Compliance coverage + gaps
# ---------------------------------------------------------------------------


def _index_ucs_by_regulation(
    ucs: Sequence[Mapping[str, Any]],
    alias_to_id: Mapping[str, str],
) -> Dict[str, List[str]]:
    """Build ``{framework_id@version|ucs: [...], framework_id@version|clauses: [...]}``.

    The free-text ``regulation`` field on a UC compliance entry (for example
    ``"GDPR"`` or ``"CCPA/CPRA"``) is resolved to a canonical framework id
    via ``alias_to_id``. That keeps the bucket keys stable even if a UC uses
    a different display spelling than ``data/regulations.json`` stores in its
    ``shortName``.
    """
    bucket: Dict[str, List[str]] = defaultdict(list)
    for uc in ucs:
        for c in uc.get("compliance") or []:
            reg = c.get("regulation")
            ver = c.get("version")
            clause = c.get("clause")
            if not reg or not ver or not clause:
                continue
            fid = alias_to_id.get(str(reg).lower())
            if not fid:
                # Preserve the original string so downstream logic can
                # still surface unmapped regulations in gap analyses.
                fid = str(reg).strip().lower()
            key = f"{fid}@{ver}"
            bucket[f"{key}|ucs"].append(uc["id"])
            bucket[f"{key}|clauses"].append(clause)
    for k in list(bucket.keys()):
        bucket[k] = sorted(set(bucket[k]))
    return bucket


def _gaps_report(
    regs: Mapping[str, Any],
    uc_bucket: Mapping[str, List[str]],
) -> Dict[str, Any]:
    """Per-regulation list of ``commonClauses`` that no UC yet tags.

    Entries are keyed by framework id so they link back to
    ``/api/v1/compliance/regulations/<id>.json`` directly.
    """
    entries: List[Dict[str, Any]] = []
    total_common = 0
    total_covered = 0
    for fw in regs.get("frameworks", []):
        fid = fw.get("id", "")
        short = fw.get("shortName") or fid
        for v in fw.get("versions", []) or []:
            clauses = [c.get("clause") for c in v.get("commonClauses") or [] if c.get("clause")]
            covered = set(uc_bucket.get(f"{fid}@{v.get('version')}|clauses") or [])
            uncovered = sorted(set(clauses) - covered)
            total_common += len(clauses)
            total_covered += len(set(clauses) & covered)
            if not clauses:
                continue
            entries.append(
                {
                    "regulationId": fid,
                    "regulation": short,
                    "version": v.get("version"),
                    "tier": fw.get("tier"),
                    "commonClausesTotal": len(clauses),
                    "commonClausesCovered": len(set(clauses) & covered),
                    "commonClausesUncovered": uncovered,
                    "commonClausesUncoveredCount": len(uncovered),
                    "priorityWeightedUncovered": round(
                        sum(
                            float(c.get("priorityWeight") or 0)
                            for c in v.get("commonClauses") or []
                            if c.get("clause") in set(uncovered)
                        ),
                        4,
                    ),
                    "regulationEndpoint": (
                        f"/api/{API_VERSION}/compliance/regulations/{fid}.json"
                    ),
                }
            )
    entries.sort(
        key=lambda e: (
            -(e.get("commonClausesUncoveredCount") or 0),
            str(e.get("regulationId") or ""),
            str(e.get("version") or ""),
        )
    )
    return {
        "apiVersion": API_VERSION,
        "generatedAt": _deterministic_timestamp(),
        "summary": {
            "totalCommonClauses": total_common,
            "totalCommonClausesCovered": total_covered,
            "totalCommonClausesUncovered": total_common - total_covered,
        },
        "entries": entries,
    }


def _compliance_index(
    ucs: Sequence[Mapping[str, Any]],
    regs: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> Dict[str, Any]:
    compliance_uc_ids = sorted(
        [uc["id"] for uc in ucs if uc.get("compliance")], key=lambda x: _uc_sort_key({"id": x})
    )
    cat22_count = sum(1 for uc in ucs if int(uc.get("_category") or 0) == 22)
    return {
        "apiVersion": API_VERSION,
        "generatedAt": _deterministic_timestamp(),
        "docs": {
            "methodology": "/docs/coverage-methodology.md",
            "versioning": "/docs/api-versioning.md",
            "legal": "/LEGAL.md",
        },
        "counts": {
            "regulationsTotal": len(regs.get("frameworks") or []),
            "useCasesTotal": len(ucs),
            "useCasesWithCompliance": len(compliance_uc_ids),
            "cat22UseCases": cat22_count,
        },
        "endpoints": {
            "coverage": f"/api/{API_VERSION}/compliance/coverage.json",
            "gaps": f"/api/{API_VERSION}/compliance/gaps.json",
            "regulations": f"/api/{API_VERSION}/compliance/regulations/index.json",
            "ucs": f"/api/{API_VERSION}/compliance/ucs/index.json",
        },
        "relatedEndpoints": {
            "equipmentIndex": f"/api/{API_VERSION}/equipment/index.json",
            "equipmentDetail": f"/api/{API_VERSION}/equipment/{{equipmentId}}.json",
        },
        "regulationsVersion": coverage.get("regulationsVersion"),
    }


def _coverage_payload(coverage: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "apiVersion": API_VERSION,
        "generatedAt": _deterministic_timestamp(),
        "source": "reports/compliance-coverage.json",
        "schemaVersion": coverage.get("schemaVersion"),
        "regulationsVersion": coverage.get("regulationsVersion"),
        "status": coverage.get("status"),
        "counts": coverage.get("counts", {}),
        "coverage": coverage.get("coverage", {}),
        "methodology": "/docs/coverage-methodology.md",
    }


def _ucs_index_payload(
    ucs: Sequence[Mapping[str, Any]],
    alias_to_id: Mapping[str, str],
) -> Dict[str, Any]:
    items = [_uc_compact(u, alias_to_id) for u in ucs if u.get("compliance")]
    items.sort(key=lambda c: _uc_sort_key({"id": c["id"]}))
    return {
        "apiVersion": API_VERSION,
        "generatedAt": _deterministic_timestamp(),
        "count": len(items),
        "items": items,
    }


def _uc_detail_payload(uc: Mapping[str, Any]) -> Dict[str, Any]:
    payload = {k: v for k, v in uc.items() if not k.startswith("_")}
    payload["apiVersion"] = API_VERSION
    payload["_meta"] = {
        "generatedAt": _deterministic_timestamp(),
        "sourcePath": uc.get("_sourcePath"),
        "sidecarEndpoint": f"/api/{API_VERSION}/compliance/ucs/{uc['id']}.json",
        "oscalEndpoint": f"/api/{API_VERSION}/oscal/component-definitions/{uc['id']}.json",
    }
    return payload


# ---------------------------------------------------------------------------
# MITRE ATT&CK + D3FEND
# ---------------------------------------------------------------------------


def _load_attack_techniques() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not ATTACK_DIR.exists():
        return out
    for path in sorted(ATTACK_DIR.glob("*.normalised.json")):
        data = _load_json(path)
        domain = data.get("domain", path.stem)
        for tech in data.get("techniques") or []:
            aid = tech.get("attack_id")
            if not aid:
                continue
            if tech.get("deprecated") or tech.get("revoked"):
                continue
            # Retain the earliest domain we encounter so enterprise wins over
            # ICS/mobile for overlapping IDs; deterministic by sorted glob.
            out.setdefault(
                aid,
                {
                    "id": aid,
                    "name": tech.get("name"),
                    "domain": domain,
                    "isSubtechnique": bool(tech.get("is_subtechnique")),
                    "tactics": sorted(tech.get("tactics") or []),
                    "platforms": sorted(tech.get("platforms") or []),
                    "url": tech.get("url"),
                },
            )
    return out


def _load_d3fend_mappings() -> Dict[str, List[str]]:
    path = D3FEND_DIR / "d3fend-attack-mappings.normalised.json"
    if not path.exists():
        return {}
    data = _load_json(path)
    mappings = data.get("mappings")
    if isinstance(mappings, dict):
        return {k: sorted(set(v)) for k, v in mappings.items()}
    # Fall back to a list-of-pairs shape defensively.
    if isinstance(mappings, list):
        agg: Dict[str, List[str]] = defaultdict(list)
        for item in mappings:
            if not isinstance(item, dict):
                continue
            aid = item.get("attack_id")
            d3id = item.get("d3fend_id") or item.get("countermeasure")
            if aid and d3id:
                agg[str(aid)].append(str(d3id))
        return {k: sorted(set(v)) for k, v in agg.items()}
    return {}


def _mitre_payloads(
    ucs: Sequence[Mapping[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    techniques = _load_attack_techniques()
    d3fend = _load_d3fend_mappings()
    ts = _deterministic_timestamp()

    referenced: Dict[str, List[str]] = defaultdict(list)  # tech_id -> [uc_id]
    tactic_buckets: Dict[str, List[str]] = defaultdict(list)  # tactic -> [tech_id]
    for uc in ucs:
        for tech_id in uc.get("mitreAttack") or []:
            referenced[str(tech_id)].append(uc["id"])
    for tid in referenced:
        tech = techniques.get(tid)
        if not tech:
            continue
        for tac in tech.get("tactics") or []:
            tactic_buckets[tac].append(tid)
    for key in list(referenced.keys()):
        referenced[key] = sorted(set(referenced[key]), key=lambda x: _uc_sort_key({"id": x}))
    for key in list(tactic_buckets.keys()):
        tactic_buckets[key] = sorted(set(tactic_buckets[key]))

    techniques_payload = {
        "apiVersion": API_VERSION,
        "generatedAt": ts,
        "source": "data/crosswalks/attack/*.normalised.json",
        "count": len(techniques),
        "referencedByCatalogue": sorted(referenced.keys()),
        "techniques": sorted(techniques.values(), key=lambda t: str(t.get("id") or "")),
    }

    coverage_payload = {
        "apiVersion": API_VERSION,
        "generatedAt": ts,
        "ucsToTechniques": {
            uc["id"]: sorted(set(uc.get("mitreAttack") or []))
            for uc in ucs
            if uc.get("mitreAttack")
        },
        "techniquesToUcs": dict(sorted(referenced.items())),
        "tacticBuckets": dict(sorted(tactic_buckets.items())),
        "totals": {
            "ucsWithTechniques": sum(1 for uc in ucs if uc.get("mitreAttack")),
            "distinctTechniquesReferenced": len(referenced),
        },
    }

    d3fend_payload = {
        "apiVersion": API_VERSION,
        "generatedAt": ts,
        "source": "data/crosswalks/d3fend/d3fend-attack-mappings.normalised.json",
        "attackToCountermeasures": d3fend,
        "countermeasureCountsByAttackId": {k: len(v) for k, v in sorted(d3fend.items())},
    }

    index_payload = {
        "apiVersion": API_VERSION,
        "generatedAt": ts,
        "endpoints": {
            "techniques": f"/api/{API_VERSION}/mitre/techniques.json",
            "coverage": f"/api/{API_VERSION}/mitre/coverage.json",
            "d3fend": f"/api/{API_VERSION}/mitre/d3fend.json",
        },
        "counts": {
            "techniquesTotal": len(techniques),
            "ucsWithTechniques": sum(1 for uc in ucs if uc.get("mitreAttack")),
            "distinctTechniquesReferencedByCatalogue": len(referenced),
        },
    }

    return index_payload, techniques_payload, coverage_payload, d3fend_payload


# ---------------------------------------------------------------------------
# OSCAL facade
# ---------------------------------------------------------------------------


def _load_oscal_catalogs() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not OSCAL_DIR.exists():
        return out
    for path in sorted(OSCAL_DIR.glob("*.normalised.json")):
        out[path.stem] = _load_json(path)
    return out


def _load_component_definitions() -> Dict[str, Any]:
    """Discover OSCAL component-definitions produced by the ingest pipeline.

    Accepts both historical filename shapes:

    * ``component-definition-<uc-id>.json``
    * ``component-definition-uc-<uc-id>.json`` (seed file committed during Phase 1.4)
    """
    out: Dict[str, Any] = {}
    if not OSCAL_DIR.exists():
        return out
    for path in sorted(OSCAL_DIR.glob("component-definition-*.json")):
        m = re.match(
            r"component-definition-(?:uc-)?([0-9]+\.[0-9]+\.[0-9]+)\.json$",
            path.name,
        )
        if not m:
            continue
        out[m.group(1)] = _load_json(path)
    return out


def _oscal_payloads() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    ts = _deterministic_timestamp()
    catalogs = _load_oscal_catalogs()
    components = _load_component_definitions()

    catalog_index = sorted(
        [
            {
                "id": cid,
                "endpoint": f"/api/{API_VERSION}/oscal/catalogs/{cid}.json",
                "source": f"data/crosswalks/oscal/{cid}.normalised.json",
            }
            for cid in catalogs
        ],
        key=lambda x: x["id"],
    )
    # Resolve the actual source filename for each component-definition so
    # consumers can track provenance even when the filename convention changes.
    source_paths: Dict[str, str] = {}
    for path in sorted(OSCAL_DIR.glob("component-definition-*.json")) if OSCAL_DIR.exists() else []:
        m = re.match(
            r"component-definition-(?:uc-)?([0-9]+\.[0-9]+\.[0-9]+)\.json$",
            path.name,
        )
        if m:
            source_paths[m.group(1)] = str(path.relative_to(REPO_ROOT))

    component_index_items = sorted(
        [
            {
                "ucId": uc_id,
                "endpoint": f"/api/{API_VERSION}/oscal/component-definitions/{uc_id}.json",
                "source": source_paths.get(
                    uc_id, f"data/crosswalks/oscal/component-definition-{uc_id}.json"
                ),
            }
            for uc_id in components
        ],
        key=lambda x: _uc_sort_key({"id": x["ucId"]}),
    )

    index_payload = {
        "apiVersion": API_VERSION,
        "generatedAt": ts,
        "oscalVersion": "1.1.1",
        "catalogs": catalog_index,
        "componentDefinitions": component_index_items,
        "endpoints": {
            "catalogs": f"/api/{API_VERSION}/oscal/catalogs/",
            "componentDefinitions": (
                f"/api/{API_VERSION}/oscal/component-definitions/index.json"
            ),
        },
    }

    comp_index_payload = {
        "apiVersion": API_VERSION,
        "generatedAt": ts,
        "count": len(component_index_items),
        "items": component_index_items,
    }

    return index_payload, comp_index_payload, {
        "catalogs": catalogs,
        "components": components,
    }


# ---------------------------------------------------------------------------
# Recommender indexes (consumed by splunk-apps/splunk-uc-recommender)
# ---------------------------------------------------------------------------


# Canonical premium-app names, sourced from ``premiumApps`` enum in
# ``schemas/uc.schema.json`` so the app-index keys stay stable across commits.
_CANONICAL_PREMIUM_APPS: Tuple[str, ...] = (
    "Splunk Enterprise Security",
    "Splunk ITSI",
    "Splunk SOAR",
    "Splunk User Behavior Analytics",
    "Splunk App for PCI Compliance",
)

# Free-text → canonical-name aliases for the compact ``premium`` field in
# ``catalog.json``. Keys must be lowercased; values must appear in
# ``_CANONICAL_PREMIUM_APPS``.
_PREMIUM_APP_ALIASES: Dict[str, str] = {
    "splunk enterprise security": "Splunk Enterprise Security",
    "enterprise security": "Splunk Enterprise Security",
    "es": "Splunk Enterprise Security",
    "splunk it service intelligence": "Splunk ITSI",
    "splunk it service intelligence (itsi)": "Splunk ITSI",
    "splunk itsi": "Splunk ITSI",
    "itsi": "Splunk ITSI",
    "splunk soar": "Splunk SOAR",
    "soar": "Splunk SOAR",
    "splunk user behavior analytics": "Splunk User Behavior Analytics",
    "splunk user behavior analytics (uba)": "Splunk User Behavior Analytics",
    "uba": "Splunk User Behavior Analytics",
    "splunk app for pci compliance": "Splunk App for PCI Compliance",
    "splunk pci compliance": "Splunk App for PCI Compliance",
    "pci compliance app": "Splunk App for PCI Compliance",
}

# Splunk CIM root data-model names. Subobjects like ``Endpoint.Processes``
# fold to the root model (``Endpoint``) because the scanner probes root
# models with ``| tstats summariesonly=t count from datamodel=...``.
_CANONICAL_CIM_MODELS: Tuple[str, ...] = (
    "Alerts",
    "Application_State",
    "Authentication",
    "Certificates",
    "Change",
    "Databases",
    "DLP",
    "Email",
    "Endpoint",
    "Event_Signatures",
    "Interprocess_Messaging",
    "Intrusion_Detection",
    "JVM",
    "Malware",
    "Network_Resolution",
    "Network_Sessions",
    "Network_Traffic",
    "Performance",
    "Splunk_Audit",
    "Ticket_Management",
    "Updates",
    "Vulnerabilities",
    "Web",
)
_CIM_MODEL_LOOKUP: Dict[str, str] = {m.lower(): m for m in _CANONICAL_CIM_MODELS}

# ``sourcetype=<token>`` token extractor. Allows quoted, backtick-wrapped, or
# bare tokens; anchors on ``sourcetype`` so it does not catch
# ``sourcetype_name=...`` attributes. Dots and colons are legal in sourcetype
# names (e.g. ``aws:cloudtrail``, ``pan:traffic``, ``edge_hub.mqtt``).
_SOURCETYPE_RX = re.compile(
    r"sourcetype\s*=\s*[\"'`]*([A-Za-z0-9_:\-\./]+)",
    re.IGNORECASE,
)

# ``datamodel=<model>`` / ``from datamodel:<model>`` token extractor. Captures
# dotted sub-objects which the caller folds to the root model.
_CIM_DATAMODEL_RX = re.compile(
    r"\bdatamodel\s*[=:]\s*[\"'`]?([A-Za-z0-9_\.]+)",
    re.IGNORECASE,
)


def _canonicalise_cim(name: str) -> Optional[str]:
    if not name:
        return None
    root = name.split(".", 1)[0]
    return _CIM_MODEL_LOOKUP.get(root.lower())


def _load_catalog() -> List[Dict[str, Any]]:
    """Return every use-case from ``catalog.json`` as a flat list.

    ``catalog.json`` is already a committed artefact and holds the full
    6 000+ catalogue (compact schema). The recommender app needs breadth, so
    the indexes are built from this file instead of the 1 200 compliance
    sidecars under ``use-cases/cat-22/``. The compliance sidecars remain the
    authority for clause-level data and are served separately under
    ``/api/v1/compliance/ucs/``.
    """
    if not CATALOG_PATH.exists():
        return []
    data = _load_json(CATALOG_PATH)
    flat: List[Dict[str, Any]] = []
    for cat in data.get("DATA", []) or []:
        for sub in cat.get("s", []) or []:
            for uc in sub.get("u", []) or []:
                if not isinstance(uc, dict):
                    continue
                if not uc.get("i"):
                    continue
                flat.append(uc)
    flat.sort(key=lambda u: _uc_sort_key({"id": str(u.get("i", ""))}))
    return flat


def _recommender_sourcetypes(uc: Mapping[str, Any]) -> List[str]:
    """Extract lowercase sourcetypes referenced by ``uc``.

    Joins ``q`` (SPL) + ``d`` (dataSources) so both dataSource prose (e.g.
    ``sourcetype="access_combined"``) and SPL tokens are matched.
    """
    text = " ".join(
        [
            str(uc.get("q", "") or ""),
            str(uc.get("d", "") or ""),
        ]
    )
    hits: List[str] = []
    for match in _SOURCETYPE_RX.finditer(text):
        token = match.group(1).strip().lower()
        if not token or "*" in token or token.startswith("-"):
            continue
        hits.append(token)
    return sorted(set(hits))


def _recommender_cim_models(uc: Mapping[str, Any]) -> List[str]:
    text = str(uc.get("q", "") or "")
    hits: set = set()
    for match in _CIM_DATAMODEL_RX.finditer(text):
        canonical = _canonicalise_cim(match.group(1))
        if canonical:
            hits.add(canonical)
    return sorted(hits)


def _recommender_apps(uc: Mapping[str, Any]) -> List[str]:
    """Return the deduped canonical-ish app/TA labels referenced by ``uc``.

    Sources (in priority order):
    - ``uc.t`` — single TA or comma-separated TA list (free-form prose;
      ingest-method descriptions like "X export via HEC" are filtered out
      so that the app-index stays close to real Splunkbase app labels).
    - ``uc.sapp[].name`` — marketplace app display names (structured).
    - ``uc.premium`` — free-text premium-app string, normalised via the
      schema enum (``schemas/uc.schema.json``).
    """
    out: set = set()

    ta_raw = str(uc.get("t", "") or "").replace("`", "").strip()
    if ta_raw:
        for piece in re.split(r"[,;]", ta_raw):
            p = piece.strip()
            if not p or len(p) > 80 or len(p) < 3:
                continue
            lower = p.lower()
            # Drop ingest-method descriptions that land in ``t`` rather
            # than a real app/TA name.
            if " via " in lower:
                continue
            if "custom scripted" in lower or "scripted input" in lower:
                continue
            if lower.startswith("scripted"):
                continue
            out.add(p)

    for app in uc.get("sapp", []) or []:
        if isinstance(app, dict):
            nm = str(app.get("name", "") or "").strip()
        elif isinstance(app, str):
            nm = app.strip()
        else:
            nm = ""
        if nm and len(nm) <= 120:
            out.add(nm)

    premium = str(uc.get("premium", "") or "").strip()
    if premium:
        for piece in re.split(r",\s*", premium):
            base = re.sub(r"\(.+?\)", "", piece).strip()
            if not base:
                continue
            canonical = _PREMIUM_APP_ALIASES.get(base.lower(), base)
            if canonical and len(canonical) <= 120:
                out.add(canonical)

    return sorted(out)


def _recommender_uc_thin(uc: Mapping[str, Any]) -> Dict[str, Any]:
    """Compact UC record consumed by the recommender UI (~200 bytes each).

    ``equipment`` + ``equipmentModels`` come from the catalogue's compact
    ``e`` / ``em`` fields, which build.py populates from each UC's sidecar
    first (source of truth, cf. build.py::_sidecar_equipment_tags) and
    falls back to a substring match on the markdown ``App/TA`` field for
    UCs without a sidecar. This is what drives the "pick your equipment"
    filter on the landing page — exposing it here means the recommender
    UI can filter on equipment without re-reading catalog.json.
    """
    # ``wave`` + ``prerequisiteUseCases`` drive the "where do I start?"
    # planner facets in the recommender UI. ``wave`` is a short string
    # (crawl/walk/run) and the prereq list is sorted for reproducible
    # output; both are omitted via empty-string / empty-list when the
    # catalog doesn't declare them so serialization stays stable.
    pre_raw = uc.get("pre", []) or []
    pre = sorted({str(p) for p in pre_raw if isinstance(p, str) and p})
    return {
        "id": str(uc.get("i", "")),
        "title": str(uc.get("n", "") or ""),
        "value": str(uc.get("v", "") or ""),
        "criticality": str(uc.get("c", "") or ""),
        "difficulty": str(uc.get("f", "") or ""),
        "wave": str(uc.get("wv", "") or ""),
        "prerequisiteUseCases": pre,
        "monitoringType": sorted(
            [m for m in (uc.get("mtype", []) or []) if isinstance(m, str)]
        ),
        "splunkPillar": str(uc.get("pillar", "") or ""),
        "app": _recommender_apps(uc),
        "cimModels": _recommender_cim_models(uc),
        "mitreAttack": sorted(
            [m for m in (uc.get("mitre", []) or []) if isinstance(m, str)]
        ),
        "equipment": sorted(
            [e for e in (uc.get("e", []) or []) if isinstance(e, str)]
        ),
        "equipmentModels": sorted(
            [em for em in (uc.get("em", []) or []) if isinstance(em, str)]
        ),
    }


def _recommender_payloads(
    catalog_ucs: Sequence[Mapping[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Build the four recommender JSON payloads from ``catalog.json``.

    The output is deterministic (sorted keys, sorted value arrays) so the
    CI drift check produces a byte-identical diff on re-run.
    """
    sourcetype_bucket: Dict[str, List[str]] = defaultdict(list)
    cim_bucket: Dict[str, List[str]] = defaultdict(list)
    app_bucket: Dict[str, List[str]] = defaultdict(list)
    thin_records: List[Dict[str, Any]] = []
    for uc in catalog_ucs:
        uc_id = str(uc.get("i", ""))
        if not uc_id:
            continue
        for st in _recommender_sourcetypes(uc):
            sourcetype_bucket[st].append(uc_id)
        for cim in _recommender_cim_models(uc):
            cim_bucket[cim].append(uc_id)
        for app in _recommender_apps(uc):
            app_bucket[app].append(uc_id)
        thin_records.append(_recommender_uc_thin(uc))
    thin_records.sort(key=lambda r: _uc_sort_key({"id": r["id"]}))

    def _finalise(bucket: Mapping[str, List[str]]) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for key in sorted(bucket):
            out[key] = sorted(
                set(bucket[key]),
                key=lambda x: _uc_sort_key({"id": x}),
            )
        return out

    generated = _deterministic_timestamp()
    version = _read_version()
    return {
        "sourcetype-index": {
            "apiVersion": API_VERSION,
            "catalogueVersion": version,
            "generatedAt": generated,
            "description": (
                "Maps lowercased Splunk sourcetypes to use-case ids. The "
                "recommender app joins this against "
                "`| metadata type=sourcetypes index=*` to produce "
                "sourcetype-driven UC recommendations."
            ),
            "sourcetypeCount": len(sourcetype_bucket),
            "ucCount": len(
                {uid for ids in sourcetype_bucket.values() for uid in ids}
            ),
            "sourcetypes": _finalise(sourcetype_bucket),
        },
        "cim-index": {
            "apiVersion": API_VERSION,
            "catalogueVersion": version,
            "generatedAt": generated,
            "description": (
                "Maps canonical CIM data-model names (Authentication, "
                "Endpoint, Network_Traffic, …) to use-case ids. Dotted "
                "sub-objects like Endpoint.Processes fold to the root "
                "model name."
            ),
            "cimModelCount": len(cim_bucket),
            "cimModels": _finalise(cim_bucket),
        },
        "app-index": {
            "apiVersion": API_VERSION,
            "catalogueVersion": version,
            "generatedAt": generated,
            "description": (
                "Maps Splunk app/TA labels to use-case ids. Keys come "
                "from the catalogue's `t` (TA), `sapp[].name` "
                "(marketplace), and `premium` (premium apps, normalised "
                "via schemas/uc.schema.json)."
            ),
            "appCount": len(app_bucket),
            "apps": _finalise(app_bucket),
        },
        "uc-thin": {
            "apiVersion": API_VERSION,
            "catalogueVersion": version,
            "generatedAt": generated,
            "description": (
                "Compact UC records used by the recommender UI. Call "
                "/api/v1/compliance/ucs/{id}.json for the full sidecar "
                "of compliance-tagged UCs (category 22)."
            ),
            "useCaseCount": len(thin_records),
            "useCases": thin_records,
        },
    }


# ---------------------------------------------------------------------------
# Equipment facade
# ---------------------------------------------------------------------------


def _equipment_metadata() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Return ``(by_id, models_by_compound)`` from the EQUIPMENT registry.

    * ``by_id[eq_id]`` has ``{id, label, models: [{id, label}, ...]}``.
    * ``models_by_compound["{eq_id}_{model_id}"]`` has ``{id, label,
      equipmentId, equipmentLabel}``.

    Labels come from build.py's EQUIPMENT table via scripts/equipment_lib.py.
    """
    by_id: Dict[str, Dict[str, Any]] = {}
    models_by_compound: Dict[str, Dict[str, Any]] = {}
    for entry in load_equipment():
        eq_id = entry["id"]
        eq_label = entry.get("label", eq_id)
        models_out: List[Dict[str, Any]] = []
        for model in entry.get("models", []) or []:
            model_id = model.get("id")
            if not model_id:
                continue
            compound = f"{eq_id}_{model_id}"
            model_label = model.get("label", model_id)
            models_out.append({"id": model_id, "label": model_label})
            models_by_compound[compound] = {
                "id": compound,
                "modelId": model_id,
                "label": model_label,
                "equipmentId": eq_id,
                "equipmentLabel": eq_label,
            }
        models_out.sort(key=lambda m: m["id"])
        by_id[eq_id] = {"id": eq_id, "label": eq_label, "models": models_out}
    return by_id, models_by_compound


def _equipment_payloads(
    catalog_ucs: Sequence[Mapping[str, Any]],
    compliance_ucs: Sequence[Mapping[str, Any]],
    alias_to_id: Mapping[str, str],
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Build the equipment index + per-equipment detail payloads.

    Two-tier output so consumers can start with the index to enumerate
    equipment and then drill in:

    * **index.json** — compact per-equipment counts and top-level regulation
      ids (stays under a few hundred KB even at full catalogue breadth).
    * **<id>.json** — full UC list grouped by category and regulation,
      useful for auditors asking "what evidence does my Palo Alto
      GlobalProtect deployment produce for HIPAA?".

    ``catalog_ucs`` is the full compact catalogue (compact schema: ``i``,
    ``n``, ``e``, ``em``, ``i_category``) so every equipment tag across
    all 23 categories is represented, not just cat-22 sidecar-bearing
    UCs. ``compliance_ucs`` is cat-22's sidecar UCs so the per-equipment
    detail can surface clause-level regulation mappings alongside the UC
    ids.
    """
    by_id, models_by_compound = _equipment_metadata()

    compliance_by_id: Dict[str, Mapping[str, Any]] = {
        uc.get("id"): uc for uc in compliance_ucs if uc.get("id")
    }
    catalog_by_id: Dict[str, Mapping[str, Any]] = {
        str(uc.get("i")): uc for uc in catalog_ucs if uc.get("i")
    }

    equipment_ucs: Dict[str, List[str]] = defaultdict(list)
    model_ucs: Dict[str, List[str]] = defaultdict(list)
    for uc in catalog_ucs:
        uc_id = str(uc.get("i") or "")
        if not uc_id:
            continue
        for eq_id in uc.get("e", []) or []:
            if isinstance(eq_id, str) and eq_id:
                equipment_ucs[eq_id].append(uc_id)
        for compound in uc.get("em", []) or []:
            if isinstance(compound, str) and compound:
                model_ucs[compound].append(uc_id)

    def _resolve_regulation_ids(uc_id: str) -> List[str]:
        """Return canonical framework ids the UC tags (cat-22 only)."""
        sidecar = compliance_by_id.get(uc_id)
        if not sidecar:
            return []
        ids: set = set()
        for c in sidecar.get("compliance") or []:
            reg = c.get("regulation")
            if not reg:
                continue
            fid = alias_to_id.get(str(reg).lower()) or str(reg).strip().lower()
            if fid:
                ids.add(fid)
        return sorted(ids)

    def _resolve_regulation_clauses(uc_id: str) -> List[Dict[str, Any]]:
        """Return ``[{regulationId, version, clause}, ...]`` for the UC."""
        sidecar = compliance_by_id.get(uc_id)
        if not sidecar:
            return []
        out: List[Dict[str, Any]] = []
        for c in sidecar.get("compliance") or []:
            reg = c.get("regulation")
            ver = c.get("version")
            clause = c.get("clause")
            if not reg or not ver or not clause:
                continue
            fid = alias_to_id.get(str(reg).lower()) or str(reg).strip().lower()
            out.append({"regulationId": fid, "version": ver, "clause": clause})
        out.sort(key=lambda e: (e["regulationId"], str(e.get("version") or ""), e["clause"]))
        return out

    generated = _deterministic_timestamp()
    version = _read_version()

    index_entries: List[Dict[str, Any]] = []
    details: Dict[str, Dict[str, Any]] = {}
    all_referenced_ids = sorted(set(equipment_ucs.keys()) | set(by_id.keys()))
    for eq_id in all_referenced_ids:
        meta = by_id.get(eq_id, {"id": eq_id, "label": eq_id, "models": []})
        uc_ids = sorted(
            set(equipment_ucs.get(eq_id, [])),
            key=lambda x: _uc_sort_key({"id": x}),
        )
        compliance_uc_ids = [u for u in uc_ids if u in compliance_by_id]
        regulation_ids: set = set()
        for u in compliance_uc_ids:
            regulation_ids.update(_resolve_regulation_ids(u))

        model_summary: List[Dict[str, Any]] = []
        for model in meta.get("models", []):
            compound = f"{eq_id}_{model['id']}"
            m_uc_ids = sorted(
                set(model_ucs.get(compound, [])),
                key=lambda x: _uc_sort_key({"id": x}),
            )
            model_summary.append(
                {
                    "id": compound,
                    "modelId": model["id"],
                    "label": model.get("label", model["id"]),
                    "useCaseCount": len(m_uc_ids),
                    "useCaseIds": m_uc_ids,
                }
            )
        model_summary.sort(key=lambda m: m["id"])

        index_entries.append(
            {
                "id": eq_id,
                "label": meta.get("label", eq_id),
                "models": [{"id": m["id"], "label": m["label"]} for m in meta.get("models", [])],
                "useCaseCount": len(uc_ids),
                "complianceUseCaseCount": len(compliance_uc_ids),
                "regulationIds": sorted(regulation_ids),
                "endpoint": f"/api/{API_VERSION}/equipment/{eq_id}.json",
            }
        )

        by_category: Dict[int, List[str]] = defaultdict(list)
        for u in uc_ids:
            cat_uc = catalog_by_id.get(u) or {}
            try:
                cat_id = int(str(u).split(".", 1)[0])
            except ValueError:
                cat_id = 0
            by_category[cat_id].append(u)
        category_list = [
            {"category": cat, "useCaseCount": len(ids), "useCaseIds": ids}
            for cat, ids in sorted(by_category.items())
        ]

        by_regulation: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for u in compliance_uc_ids:
            for clause in _resolve_regulation_clauses(u):
                by_regulation[clause["regulationId"]].append(
                    {
                        "useCaseId": u,
                        "version": clause["version"],
                        "clause": clause["clause"],
                    }
                )
        regulation_list: List[Dict[str, Any]] = []
        for fid in sorted(by_regulation):
            entries = by_regulation[fid]
            entries.sort(
                key=lambda e: (
                    _uc_sort_key({"id": e["useCaseId"]}),
                    str(e.get("version") or ""),
                    e.get("clause") or "",
                )
            )
            uc_set = sorted(
                {e["useCaseId"] for e in entries},
                key=lambda x: _uc_sort_key({"id": x}),
            )
            regulation_list.append(
                {
                    "regulationId": fid,
                    "useCaseCount": len(uc_set),
                    "useCaseIds": uc_set,
                    "clauseMappings": entries,
                    "regulationEndpoint": f"/api/{API_VERSION}/compliance/regulations/{fid}.json",
                }
            )

        details[eq_id] = {
            "apiVersion": API_VERSION,
            "catalogueVersion": version,
            "generatedAt": generated,
            "id": eq_id,
            "label": meta.get("label", eq_id),
            "models": model_summary,
            "useCaseCount": len(uc_ids),
            "useCaseIds": uc_ids,
            "complianceUseCaseCount": len(compliance_uc_ids),
            "regulationIds": sorted(regulation_ids),
            "useCasesByCategory": category_list,
            "regulations": regulation_list,
            "indexEndpoint": f"/api/{API_VERSION}/equipment/index.json",
        }

    index_entries.sort(key=lambda e: e["id"])

    total_referenced = sum(1 for uc in catalog_ucs if uc.get("e"))
    index_payload = {
        "apiVersion": API_VERSION,
        "catalogueVersion": version,
        "generatedAt": generated,
        "description": (
            "Maps equipment slugs (from the EQUIPMENT registry in build.py) to "
            "the use-cases that tag them. Tags come from sidecar `equipment[]` "
            "/ `equipmentModels[]` fields (source of truth, generated by "
            "scripts/generate_equipment_tags.py) with a legacy substring match "
            "on the markdown App/TA field as fallback. This answers the "
            "auditor question 'if I log equipment X, which regulatory clauses "
            "does it help satisfy?' — drill into /api/v1/equipment/<id>.json "
            "for the per-regulation breakdown."
        ),
        "equipmentCount": len(index_entries),
        "useCasesWithEquipmentTotal": total_referenced,
        "equipment": index_entries,
        "modelCount": len(models_by_compound),
    }
    return index_payload, details


# ---------------------------------------------------------------------------
# Top-level manifest + context + openapi + README
# ---------------------------------------------------------------------------


def _manifest(
    ucs: Sequence[Mapping[str, Any]],
    regs: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "apiVersion": API_VERSION,
        "catalogueVersion": _read_version(),
        "generatedAt": _deterministic_timestamp(),
        "status": coverage.get("status", "unknown"),
        "methodologyDoc": "/docs/coverage-methodology.md",
        "versioningDoc": "/docs/api-versioning.md",
        "legalDoc": "/LEGAL.md",
        "contextUrl": f"/api/{API_VERSION}/context.jsonld",
        "openapiSpec": f"/api/{API_VERSION}/openapi.yaml",
        "counts": {
            "useCasesTotal": len(ucs),
            "useCasesWithCompliance": sum(1 for u in ucs if u.get("compliance")),
            "regulationsTotal": len(regs.get("frameworks") or []),
        },
        "endpoints": {
            "compliance": {
                "index": f"/api/{API_VERSION}/compliance/index.json",
                "coverage": f"/api/{API_VERSION}/compliance/coverage.json",
                "gaps": f"/api/{API_VERSION}/compliance/gaps.json",
                "regulations": f"/api/{API_VERSION}/compliance/regulations/index.json",
                "ucs": f"/api/{API_VERSION}/compliance/ucs/index.json",
            },
            "oscal": {
                "index": f"/api/{API_VERSION}/oscal/index.json",
                "catalogs": f"/api/{API_VERSION}/oscal/catalogs/",
                "componentDefinitions": (
                    f"/api/{API_VERSION}/oscal/component-definitions/index.json"
                ),
            },
            "mitre": {
                "index": f"/api/{API_VERSION}/mitre/index.json",
                "techniques": f"/api/{API_VERSION}/mitre/techniques.json",
                "coverage": f"/api/{API_VERSION}/mitre/coverage.json",
                "d3fend": f"/api/{API_VERSION}/mitre/d3fend.json",
            },
            "recommender": {
                "sourcetypeIndex": (
                    f"/api/{API_VERSION}/recommender/sourcetype-index.json"
                ),
                "cimIndex": f"/api/{API_VERSION}/recommender/cim-index.json",
                "appIndex": f"/api/{API_VERSION}/recommender/app-index.json",
                "ucThin": f"/api/{API_VERSION}/recommender/uc-thin.json",
            },
            "equipment": {
                "index": f"/api/{API_VERSION}/equipment/index.json",
                "detail": f"/api/{API_VERSION}/equipment/{{equipmentId}}.json",
            },
        },
        "deprecations": [],
        "successor": None,
    }


def _context_jsonld() -> Dict[str, Any]:
    """JSON-LD context describing catalogue terms.

    Consumers can reference this context to interpret any other document
    under ``/api/v1/`` as linked data. The vocabulary is intentionally narrow
    so that v1 can remain additive-only.
    """
    return {
        "@context": {
            "@version": 1.1,
            "@vocab": f"{NAMESPACE}/ns/",
            "smuc": f"{NAMESPACE}/ns/",
            "schema": "http://schema.org/",
            "nist": "https://pages.nist.gov/OSCAL/",
            "oscal": "urn:oscal:",
            "attck": "https://attack.mitre.org/techniques/",
            "d3fend": "https://d3fend.mitre.org/ontologies/d3fend.owl#",
            "UseCase": "smuc:UseCase",
            "Regulation": "smuc:Regulation",
            "Clause": "smuc:Clause",
            "ComplianceMapping": "smuc:ComplianceMapping",
            "ControlTest": "smuc:ControlTest",
            "id": "@id",
            "type": "@type",
            "title": "schema:name",
            "description": "schema:description",
            "regulation": {"@id": "smuc:regulation", "@type": "@id"},
            "version": "smuc:version",
            "clause": "smuc:clause",
            "clauseUrl": {"@id": "smuc:clauseUrl", "@type": "@id"},
            "mode": "smuc:assuranceMode",
            "assurance": "smuc:assuranceLevel",
            "assurance_rationale": "smuc:assuranceRationale",
            "mitreAttack": {"@id": "smuc:mitreTechnique", "@container": "@set"},
            "references": {"@id": "smuc:reference", "@container": "@set"},
            "controlFamily": "smuc:controlFamily",
            "owner": "smuc:owner",
            "criticality": "smuc:criticality",
            "evidence": "smuc:evidence",
            "exclusions": "smuc:exclusions",
            "controlTest": "smuc:controlTest",
            "positiveScenario": "smuc:positiveScenario",
            "negativeScenario": "smuc:negativeScenario",
            "fixtureRef": {"@id": "smuc:fixtureRef", "@type": "@id"},
            "attackTechnique": "smuc:attackTechnique",
            "spl": "smuc:splDetection",
            "dataSources": "smuc:dataSource",
            "detectionType": "smuc:detectionType",
            "securityDomain": "smuc:securityDomain",
            "Equipment": "smuc:Equipment",
            "EquipmentModel": "smuc:EquipmentModel",
            "equipment": {"@id": "smuc:equipment", "@container": "@set"},
            "equipmentModels": {"@id": "smuc:equipmentModel", "@container": "@set"},
            "wave": "smuc:implementationWave",
            "prerequisiteUseCases": {
                "@id": "smuc:requiresUseCase",
                "@type": "@id",
                "@container": "@set"
            }
        }
    }


OPENAPI_YAML = """openapi: 3.1.0
info:
  title: Splunk Monitoring Use Cases — Compliance API
  description: |
    Read-only static JSON API describing the Splunk Monitoring Use Cases
    compliance catalogue. Every response is a file committed under
    ``api/v1/``; consumers can `git clone` or `curl` any endpoint.

    The API is backed by the data in this repository. The authoritative
    schema for a use-case is ``schemas/uc.schema.json`` and the authoritative
    regulation metadata is ``data/regulations.json``. The API is regenerated
    by ``scripts/generate_api_surface.py`` which is exercised in CI — a drift
    between inputs and the committed API fails the build.

    See ``docs/api-versioning.md`` for the versioning + deprecation policy.
  version: "1.0.0"
  license:
    name: "Catalogue content: see LEGAL.md"
    url: https://github.com/fenre/splunk-monitoring-use-cases/blob/main/LEGAL.md
servers:
  - url: https://fenre.github.io/splunk-monitoring-use-cases/api/v1
    description: Production (GitHub Pages)
  - url: ./api/v1
    description: Local file system
paths:
  /manifest.json:
    get:
      summary: Top-level API manifest
      responses:
        "200":
          description: Endpoint catalogue and version metadata
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Manifest"
  /context.jsonld:
    get:
      summary: JSON-LD context
      responses:
        "200":
          description: Linked-data vocabulary for consumers
  /compliance/index.json:
    get:
      summary: Compliance endpoint index
  /compliance/coverage.json:
    get:
      summary: Three coverage metrics (clause %, priority-weighted %, assurance-adjusted %)
  /compliance/gaps.json:
    get:
      summary: Uncovered common clauses per regulation/version
  /compliance/regulations/index.json:
    get:
      summary: List of all regulations
  /compliance/regulations/{regulationId}.json:
    get:
      summary: Full regulation metadata (all versions)
      parameters:
        - name: regulationId
          in: path
          required: true
          schema: { type: string }
  /compliance/ucs/index.json:
    get:
      summary: Compact list of UCs touching compliance
  /compliance/ucs/{ucId}.json:
    get:
      summary: Full UC sidecar (canonical form)
      parameters:
        - name: ucId
          in: path
          required: true
          schema:
            type: string
            pattern: ^[0-9]+\\.[0-9]+\\.[0-9]+$
  /oscal/index.json:
    get:
      summary: OSCAL artifacts index
  /oscal/catalogs/{catalogId}.json:
    get:
      summary: Normalised NIST OSCAL catalog
      parameters:
        - name: catalogId
          in: path
          required: true
          schema: { type: string }
  /oscal/component-definitions/index.json:
    get:
      summary: OSCAL component-definition index
  /oscal/component-definitions/{ucId}.json:
    get:
      summary: OSCAL component-definition for a single UC
      parameters:
        - name: ucId
          in: path
          required: true
          schema: { type: string }
  /mitre/index.json:
    get:
      summary: MITRE endpoints index
  /mitre/techniques.json:
    get:
      summary: Flat list of MITRE ATT&CK techniques
  /mitre/coverage.json:
    get:
      summary: UC <-> technique cross reference
  /mitre/d3fend.json:
    get:
      summary: ATT&CK -> D3FEND countermeasure mapping
  /recommender/sourcetype-index.json:
    get:
      summary: Lowercased sourcetype → list of UC ids (drives the recommender app)
  /recommender/cim-index.json:
    get:
      summary: CIM data-model name → list of UC ids
  /recommender/app-index.json:
    get:
      summary: Splunk app / TA label → list of UC ids
  /recommender/uc-thin.json:
    get:
      summary: Compact UC records (id, title, criticality, …) consumed by the recommender UI
  /equipment/index.json:
    get:
      summary: Equipment index (equipmentId → UC count + touched regulation ids)
      description: |
        One entry per equipment slug from the EQUIPMENT registry in
        build.py. Backed by `equipment[]` / `equipmentModels[]` fields
        on UC sidecars (generated by scripts/generate_equipment_tags.py)
        joined with the full catalogue. Drill into
        /equipment/{equipmentId}.json for the per-regulation breakdown.
  /equipment/{equipmentId}.json:
    get:
      summary: Full per-equipment detail (UC list by category + regulation mappings)
      parameters:
        - name: equipmentId
          in: path
          required: true
          schema:
            type: string
            example: paloalto
components:
  schemas:
    Manifest:
      type: object
      required: [apiVersion, catalogueVersion, generatedAt, endpoints]
      properties:
        apiVersion: { type: string, example: v1 }
        catalogueVersion: { type: string }
        generatedAt: { type: string, format: date-time }
        status: { type: string }
        endpoints:
          type: object
          additionalProperties: true
"""


README_MD = """# Compliance API — v1

This directory is the **read-only HTTP/JSON surface** for the Splunk
Monitoring Use Cases compliance catalogue. Every file under this directory
is generated by [`scripts/generate_api_surface.py`](../../scripts/generate_api_surface.py)
and must never be edited by hand.

## Why static JSON?

* **Zero infra.** The project is hosted on GitHub Pages. Static JSON works
  the same in `curl`, `fetch`, `jq`, offline notebooks, and MCP servers.
* **Deterministic.** Regenerating on an unchanged repo yields byte-identical
  files, so CI can diff the tree and catch forgotten rebuilds.
* **Auditable.** The API ships in git. Every change is reviewable in a PR.

## Versioning

See [`docs/api-versioning.md`](../../docs/api-versioning.md). Inside a
major version (`v1`) we only add fields and endpoints. Anything else is
a breaking change and lands at `api/v2/`.

## Quick start

```bash
# List endpoints
curl https://fenre.github.io/splunk-monitoring-use-cases/api/v1/manifest.json | jq

# Show clause, priority-weighted, and assurance-adjusted coverage
curl https://fenre.github.io/splunk-monitoring-use-cases/api/v1/compliance/coverage.json | jq '.coverage.global'

# List common clauses that no UC yet covers
curl https://fenre.github.io/splunk-monitoring-use-cases/api/v1/compliance/gaps.json | jq '.entries[:5]'

# Fetch a single UC sidecar in canonical JSON form
curl https://fenre.github.io/splunk-monitoring-use-cases/api/v1/compliance/ucs/22.35.1.json | jq '.compliance[0]'

# Fetch its auditor-ready OSCAL component-definition
curl https://fenre.github.io/splunk-monitoring-use-cases/api/v1/oscal/component-definitions/22.35.1.json

# List equipment and the regulations each slug's UCs cover
curl https://fenre.github.io/splunk-monitoring-use-cases/api/v1/equipment/index.json | jq '.equipment[] | {id,label,useCaseCount,regulationIds}' | head -n 40

# Per-equipment detail (UC list by category + per-regulation clause map)
curl https://fenre.github.io/splunk-monitoring-use-cases/api/v1/equipment/paloalto.json | jq '.regulations[] | .regulationId'
```

## Endpoint catalogue

```
/api/v1
├── manifest.json                   Top-level index
├── context.jsonld                  JSON-LD vocabulary
├── openapi.yaml                    OpenAPI 3.1 spec
├── compliance/
│   ├── index.json                  Pointers + counts
│   ├── coverage.json               3 metrics, 4 scopes
│   ├── gaps.json                   Uncovered common clauses
│   ├── regulations/
│   │   ├── index.json              All regulations, flat list
│   │   ├── <id>.json               Full per-framework metadata
│   │   └── <id>@<version>.json     Single-version slice + UCs
│   └── ucs/
│       ├── index.json              Compact per-UC entries
│       └── <uc_id>.json            Canonical UC sidecar (incl. equipment[])
├── equipment/
│   ├── index.json                  Equipment → UCs + touched regulation ids
│   └── <equipment_id>.json         Per-equipment UC + regulation breakdown
├── oscal/
│   ├── index.json
│   ├── catalogs/
│   │   └── <catalog_id>.json       Normalised NIST OSCAL catalog
│   └── component-definitions/
│       ├── index.json
│       └── <uc_id>.json            OSCAL component-definition
├── mitre/
│   ├── index.json
│   ├── techniques.json             All referenced ATT&CK techniques
│   ├── coverage.json               UC <-> technique + tactic buckets
│   └── d3fend.json                 ATT&CK -> D3FEND countermeasures
└── recommender/
    ├── sourcetype-index.json       Sourcetype -> UC ids
    ├── cim-index.json              CIM model -> UC ids
    ├── app-index.json              Splunk app / TA -> UC ids
    └── uc-thin.json                Compact UC records (incl. equipment[])
```

## Regeneration

```bash
python3 scripts/generate_api_surface.py
```

CI runs this with `--check`, which regenerates into a temp directory and
fails if any file differs from the committed tree.

## Provenance and attestation

Every compliance mapping surfaced through this API (under
`compliance/`, `oscal/`, and the `regulation.*` fields of the UC JSON)
is hashed into the signed provenance ledger at
[`data/provenance/mapping-ledger.json`](../../data/provenance/mapping-ledger.json).
The ledger is the single authoritative source for:

- The cryptographic fingerprint (`canonicalHash`) of each
  `(UC, regulation, clause, mode, assurance)` tuple.
- The top-level `merkleRoot` spanning all 1,889 mappings.
- A snapshot of peer-, legal-, and SME-review signoff state per
  mapping at generation time.
- `firstSeenCommit` / `lastModifiedCommit` pointers into git history.

Official tagged releases ship a Sigstore-attested copy of the ledger
(`dist/mapping-ledger.json` + `dist/mapping-ledger.sigstore.bundle.json`).
Consumers can prove a downloaded API tree was produced by the official
release workflow by verifying the ledger, then matching any API-level
compliance claim back to its `canonicalHash` entry.

See [`docs/signed-provenance.md`](../../docs/signed-provenance.md) for
the full verification protocol (`gh attestation verify`,
`scripts/audit_mapping_ledger.py --require-signature --verify-signature`)
and operator runbooks.
"""


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _render(out_root: pathlib.Path) -> None:
    regs = _load_json(REGS_PATH)
    coverage = _load_json(COVERAGE_REPORT)
    ucs = _load_ucs()
    alias_to_id = _regulation_alias_to_id(regs)
    uc_bucket = _index_ucs_by_regulation(ucs, alias_to_id)

    # Manifest / meta
    _write_json(out_root / "manifest.json", _manifest(ucs, regs, coverage))
    _write_json(out_root / "context.jsonld", _context_jsonld())
    _write_text(out_root / "openapi.yaml", OPENAPI_YAML)
    _write_text(out_root / "README.md", README_MD)

    # Compliance root
    _write_json(out_root / "compliance" / "index.json", _compliance_index(ucs, regs, coverage))
    _write_json(out_root / "compliance" / "coverage.json", _coverage_payload(coverage))
    _write_json(out_root / "compliance" / "gaps.json", _gaps_report(regs, uc_bucket))

    # Regulations
    _write_json(
        out_root / "compliance" / "regulations" / "index.json",
        _regulations_index(regs),
    )
    for fw in regs.get("frameworks", []):
        detail = _regulation_detail(fw, uc_bucket)
        _write_json(
            out_root / "compliance" / "regulations" / f"{fw.get('id')}.json",
            detail,
        )
        for version in detail.get("versions", []):
            slug = _safe_version(version.get("version"))
            version_payload = {
                "apiVersion": API_VERSION,
                "id": detail["id"],
                "shortName": detail["shortName"],
                "name": detail["name"],
                "tier": detail["tier"],
                "jurisdiction": detail["jurisdiction"],
                "tags": detail["tags"],
                "version": version,
                "generatedAt": _deterministic_timestamp(),
            }
            _write_json(
                out_root
                / "compliance"
                / "regulations"
                / f"{detail['id']}@{slug}.json",
                version_payload,
            )

    # UCs
    _write_json(
        out_root / "compliance" / "ucs" / "index.json",
        _ucs_index_payload(ucs, alias_to_id),
    )
    for uc in ucs:
        _write_json(
            out_root / "compliance" / "ucs" / f"{uc['id']}.json",
            _uc_detail_payload(uc),
        )

    # OSCAL
    oscal_index, comp_index, bundles = _oscal_payloads()
    _write_json(out_root / "oscal" / "index.json", oscal_index)
    _write_json(out_root / "oscal" / "component-definitions" / "index.json", comp_index)
    for cid, body in bundles["catalogs"].items():
        _write_json(out_root / "oscal" / "catalogs" / f"{cid}.json", body)
    for uc_id, body in bundles["components"].items():
        _write_json(
            out_root / "oscal" / "component-definitions" / f"{uc_id}.json",
            body,
        )

    # MITRE
    mitre_index, tech_payload, coverage_payload, d3fend_payload = _mitre_payloads(ucs)
    _write_json(out_root / "mitre" / "index.json", mitre_index)
    _write_json(out_root / "mitre" / "techniques.json", tech_payload)
    _write_json(out_root / "mitre" / "coverage.json", coverage_payload)
    _write_json(out_root / "mitre" / "d3fend.json", d3fend_payload)

    # Recommender (drives splunk-apps/splunk-uc-recommender)
    catalog_ucs = _load_catalog()
    recommender = _recommender_payloads(catalog_ucs)
    _write_json(
        out_root / "recommender" / "sourcetype-index.json",
        recommender["sourcetype-index"],
    )
    _write_json(
        out_root / "recommender" / "cim-index.json",
        recommender["cim-index"],
    )
    _write_json(
        out_root / "recommender" / "app-index.json",
        recommender["app-index"],
    )
    _write_json(
        out_root / "recommender" / "uc-thin.json",
        recommender["uc-thin"],
    )

    # Equipment facade (equipment slug -> UCs + regulations). Uses the
    # full catalogue from catalog.json so every category contributes, not
    # just cat-22 sidecars.
    equipment_index, equipment_details = _equipment_payloads(
        catalog_ucs, ucs, alias_to_id
    )
    _write_json(out_root / "equipment" / "index.json", equipment_index)
    for eq_id, body in equipment_details.items():
        _write_json(out_root / "equipment" / f"{eq_id}.json", body)

    # Story-layer surfaces (v7.1 regulation→UC redesign). Each generator
    # is deterministic, offline, and owns its own subtree under
    # api/v1/compliance/. We invoke them here so the main --check drift
    # guard subsumes their output and the MCP drift guard can find
    # compliance/clauses/index.json locally on a fresh checkout.
    _render_story_surfaces(out_root)


def _render_story_surfaces(out_root: pathlib.Path) -> None:
    """Invoke the three story-layer generators in order.

    Order matters:

    1. ``generate_clause_index.py`` writes ``compliance/clauses/*`` (the
       clause→UC reverse index used by ``augment_regulation_api.py`` to
       build its ``clauseCoverageMatrix`` and by the new MCP tools
       ``get_clause_coverage`` / ``list_uncovered_clauses``).
    2. ``augment_regulation_api.py`` enriches every
       ``compliance/regulations/<id>.json`` (and per-version slice) with
       a ``clauseCoverageMatrix`` + ``coverageSummary``.
    3. ``generate_story_payload.py`` writes ``compliance/story/*`` with
       the per-regulation narrative shown on ``compliance-story.html``.

    All three scripts read from ``out_root`` rather than ``api/v1/`` so
    ``--check`` can safely target a temp directory.
    """
    # Lazy import so ``generate_api_surface`` stays usable even if one of
    # the story generators is absent (e.g. during bisect).
    from importlib import util as _import_util

    def _load_module(name: str):
        path = _THIS_DIR / f"{name}.py"
        spec = _import_util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load {name} from {path}")
        mod = _import_util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    clause_mod = _load_module("generate_clause_index")
    augment_mod = _load_module("augment_regulation_api")
    story_mod = _load_module("generate_story_payload")

    clauses_dir = out_root / "compliance" / "clauses"
    clauses_dir.parent.mkdir(parents=True, exist_ok=True)
    clause_mod.generate(clauses_dir)

    regs_dir = out_root / "compliance" / "regulations"
    if regs_dir.exists():
        augment_mod.augment_all(regs_dir, clauses_dir=clauses_dir)

    story_dir = out_root / "compliance" / "story"
    story_mod.generate(story_dir, regs_dir=regs_dir)


#: Sub-trees of ``api/v1/`` that are generated by OTHER scripts and
#: therefore must be ignored by this script's rmtree / diff logic.
#: Keep in sync with the corresponding generator entries in
#: .github/workflows/validate.yml.
_EXTERNAL_SUBTREES = ("evidence-packs",)


def _is_external(rel: pathlib.Path) -> bool:
    parts = rel.parts
    return bool(parts) and parts[0] in _EXTERNAL_SUBTREES


def _diff_trees(lhs: pathlib.Path, rhs: pathlib.Path) -> List[str]:
    """Return a list of paths (relative) that differ between two trees.

    Sub-trees owned by other generators (see ``_EXTERNAL_SUBTREES``) are
    excluded from the comparison so the api-surface drift check does
    not false-positive on files this script neither wrote nor is
    expected to own.
    """
    diffs: List[str] = []
    lhs_files = {
        p.relative_to(lhs) for p in lhs.rglob("*")
        if p.is_file() and not _is_external(p.relative_to(lhs))
    }
    rhs_files = {
        p.relative_to(rhs) for p in rhs.rglob("*")
        if p.is_file() and not _is_external(p.relative_to(rhs))
    }
    for rel in sorted(lhs_files | rhs_files):
        if rel not in lhs_files:
            diffs.append(f"+ {rel}  (only in freshly generated tree)")
            continue
        if rel not in rhs_files:
            diffs.append(f"- {rel}  (only on disk)")
            continue
        if (lhs / rel).read_bytes() != (rhs / rel).read_bytes():
            diffs.append(f"~ {rel}")
    return diffs


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Do not modify the tree. Regenerate into a temp directory and "
            "exit with a non-zero status if the committed ``api/v1/`` tree "
            "drifts from it."
        ),
    )
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=API_ROOT,
        help="Output directory. Defaults to api/v1/",
    )
    args = parser.parse_args(argv)

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            _render(tmp_path)
            if not args.out.exists():
                print(f"ERROR: {args.out} does not exist — run without --check first.", file=sys.stderr)
                return 1
            diffs = _diff_trees(tmp_path, args.out)
            if diffs:
                print("API surface is stale. Run scripts/generate_api_surface.py.", file=sys.stderr)
                for line in diffs:
                    print(f"  {line}", file=sys.stderr)
                return 1
            print("API surface is up to date.")
            return 0

    if args.out.exists():
        # Preserve externally-owned subtrees (see _EXTERNAL_SUBTREES) by
        # pruning only the files this generator owns. Anything else
        # (e.g. api/v1/evidence-packs/ from scripts/generate_evidence_packs.py)
        # is left intact; the corresponding generator is responsible
        # for its own drift check.
        for entry in args.out.iterdir():
            rel = entry.relative_to(args.out)
            if _is_external(rel):
                continue
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    _render(args.out)

    # Summary (counts include externally-owned files already on disk so
    # the reported total reflects the full api/v1/ tree after regen)
    file_count = sum(1 for _ in args.out.rglob("*") if _.is_file())
    print(f"Wrote {file_count} files under {args.out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - safety net only
        import traceback

        traceback.print_exc()
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
