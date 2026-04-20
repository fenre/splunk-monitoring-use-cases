#!/usr/bin/env python3
"""Generate the per-regulation unified story payload.

Introduced by the Regulation-to-UC Story Redesign (Phase 2c). Each framework
in ``data/regulations.json`` gets one ``api/v1/compliance/story/{regulationId}.json``
file that combines:

* Buyer block  — coverage headline, top-five highlights, top-three gaps,
                 the one-line "why this matters" per highlight. Links by
                 ``narrativeRef`` to ``non-technical-view.js#area-{slug}``
                 so the ``compliance-story.html`` page can pull the
                 existing ``whatItIs`` / ``whoItAffects`` / ``splunkValue``
                 paragraphs without duplicating prose.
* Auditor block — full ``clauseCoverageMatrix`` with UC IDs, assurance,
                  evidenceArtifact, and rationale. Copied from the
                  already-augmented regulation API file (Phase 2b) so
                  both surfaces stay in sync.
* Implementer block — ``quickStartPlaybook[]``: for each clause, the 1-3
                      UCs an implementer should turn on first, ranked by
                      assurance then by UC ``criticality``.
* Related endpoints — links to the reverse-index clause page, the
                      regulation endpoint, the evidence pack, and the
                      regulatory primer section.

Why a separate endpoint rather than a field on the regulation payload:
the regulation endpoint stays machine-contract-stable and audit-grade;
the story endpoint is allowed to evolve narrative shape (new blocks,
richer copy) without breaking existing v1 consumers.

Inputs (in-repo, zero network):

* ``data/regulations.json``
* ``api/v1/compliance/regulations/{id}.json`` (produced by
  ``scripts/generate_api_surface.py`` then augmented by
  ``scripts/augment_regulation_api.py``)
* ``content/cat-*/UC-*.json`` (for ``criticality`` lookups)

Output:

* ``api/v1/compliance/story/index.json``
* ``api/v1/compliance/story/{regulationId}.json``

Design invariants: deterministic JSON, additive within v1, offline, and
``--check`` drift-check mode, matching the contracts already used by
``scripts/generate_api_surface.py`` and ``scripts/generate_clause_index.py``.

Exit codes:
    0  Success.
    1  Drift / missing input.
    2  Uncaught exception.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
REGULATIONS_PATH = REPO_ROOT / "data" / "regulations.json"
REGS_DIR = REPO_ROOT / "api" / "v1" / "compliance" / "regulations"
CLAUSES_DIR = REPO_ROOT / "api" / "v1" / "compliance" / "clauses"
OUT_DIR = REPO_ROOT / "api" / "v1" / "compliance" / "story"
UC_GLOB = "content/cat-*/UC-*.json"
VERSION_FILE = REPO_ROOT / "VERSION"
EVIDENCE_PACK_DIR = REPO_ROOT / "docs" / "evidence-packs"
PRIMER_PATH = REPO_ROOT / "docs" / "regulatory-primer.md"


# ---------------------------------------------------------------------------
# IO / timestamp helpers (same contract as the other generators)
# ---------------------------------------------------------------------------


def _deterministic_timestamp() -> str:
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


def _load_json(path: pathlib.Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: pathlib.Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def _read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "0.0.0"


# ---------------------------------------------------------------------------
# UC sidecar lookup (for criticality / title fallback)
# ---------------------------------------------------------------------------


_UC_ID_RX = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _uc_sort_key_from_id(uc_id: str) -> Tuple[int, int, int]:
    m = _UC_ID_RX.match(uc_id)
    if not m:
        return (10**6, 10**6, 10**6)
    return tuple(int(x) for x in m.groups())  # type: ignore[return-value]


def load_uc_index() -> Dict[str, Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    for path in sorted(REPO_ROOT.glob(UC_GLOB)):
        try:
            data = _load_json(path)
        except json.JSONDecodeError:
            continue
        uc_id = data.get("id")
        if not isinstance(uc_id, str):
            continue
        by_id[uc_id] = data
    return by_id


# ---------------------------------------------------------------------------
# Narrative (non-technical-view.js) extraction
# ---------------------------------------------------------------------------


_AREA_LINE_RX = re.compile(
    r"\{\s*name:\s*\"(?P<name>[^\"]+)\","
    r".*?"
    r"(?:whatItIs:\s*\"(?P<whatItIs>[^\"]+)\",)?"
    r".*?"
    r"(?:whoItAffects:\s*\"(?P<whoItAffects>[^\"]+)\",)?"
    r".*?"
    r"(?:splunkValue:\s*\"(?P<splunkValue>[^\"]+)\",)?"
    r".*?"
    r"(?:primer:\s*\"(?P<primer>[^\"]+)\",)?"
    r".*?"
    r"(?:evidencePack:\s*\"(?P<evidencePack>[^\"]+)\",)?",
    re.DOTALL,
)


def load_cat22_areas() -> Dict[str, Dict[str, Any]]:
    """Parse the ``non-technical-view.js`` cat-22 ``areas[]`` with a
    line-scoped regex so the story payload can link each regulation to
    its existing ``whatItIs`` / ``whoItAffects`` / ``splunkValue`` copy
    without duplicating the prose. Keys are lowercase area names.

    The parser is deliberately fault-tolerant: missing optional fields
    are fine, and unrecognised areas are silently skipped. The result is
    purely advisory — the HTML surfaces do the same lookup at runtime
    and fall back gracefully when a narrative is absent.
    """
    src_path = REPO_ROOT / "non-technical-view.js"
    if not src_path.exists():
        return {}
    text = src_path.read_text(encoding="utf-8")
    # Locate the cat-22 areas block by finding the '"22":' key and the
    # next '"23":' key (or end of file). The non-technical-view.js file
    # is 900+ lines so we only regex within the cat-22 window.
    m = re.search(r'"22"\s*:\s*\{(?P<body>.*?)\}\s*,\s*\n\s*"23"', text, re.DOTALL)
    if not m:
        m = re.search(r'"22"\s*:\s*\{(?P<body>.*)', text, re.DOTALL)
        if not m:
            return {}
    body = m.group("body")
    areas: Dict[str, Dict[str, Any]] = {}
    for line in body.splitlines():
        line = line.strip()
        if "name:" not in line:
            continue
        nm = re.search(r'name:\s*"([^"]+)"', line)
        if not nm:
            continue
        name = nm.group(1)
        def _field(key: str) -> Optional[str]:
            match = re.search(rf'{key}:\s*"((?:[^"\\]|\\.)*)"', line)
            if not match:
                return None
            # Unescape only the backslash-quoted cases that non-technical-view.js uses
            return match.group(1).replace('\\"', '"')
        areas[name.lower()] = {
            "name": name,
            "whatItIs": _field("whatItIs"),
            "whoItAffects": _field("whoItAffects"),
            "splunkValue": _field("splunkValue"),
            "primer": _field("primer"),
            "evidencePack": _field("evidencePack"),
        }
    return areas


_SLUG_RX = re.compile(r"[^a-z0-9]+")


def _narrative_slug(name: str) -> str:
    return _SLUG_RX.sub("-", name.lower()).strip("-")


# Fuzzy match regulation short-name → narrative area name. The catalogue
# has ~66 frameworks and non-technical-view.js has ~12 narratives, so a
# deterministic best-match pass is sufficient.
_MANUAL_NARRATIVE_MAP = {
    "gdpr": "GDPR compliance",
    "uk-gdpr": "UK GDPR",
    "ccpa-cpra": "CCPA privacy",
    "nis2": "NIS2 compliance",
    "iso-27001": "ISO 27001:2022",
    "nist-csf": "NIST CSF 2.0",
    "dora": "DORA digital resilience",
    "mifid-ii": "MiFID II",
    "soc-2": "SOC 2",
    "hipaa-security": "HIPAA healthcare",
    "hipaa-privacy": "HIPAA healthcare",
    "hipaa-breach-notification": "HIPAA healthcare",
    "pci-dss": "PCI DSS v4.0",
    "sox-itgc": "SOX / ITGC",
    "nerc-cip": "NERC CIP",
    "nist-800-53": "NIST 800-53",
    "fedramp": "FedRAMP",
    "cmmc": "CMMC",
    "eu-ai-act": "EU AI Act",
}


def narrative_for_regulation(
    reg_id: str,
    reg_short: str,
    areas: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    """Find the narrative record for a regulation id.

    Strategy: exact manual map first (authoritative), then fuzzy match on
    short-name lowercase, then give up.
    """
    target_name = _MANUAL_NARRATIVE_MAP.get(reg_id)
    if target_name:
        rec = areas.get(target_name.lower())
        if rec:
            return dict(rec, matchedBy="manual-map")
    # Fuzzy: does the area name contain the short name?
    lc = reg_short.lower()
    for key, rec in areas.items():
        if lc and (lc in key or key in lc):
            return dict(rec, matchedBy="fuzzy-shortname")
    return None


# ---------------------------------------------------------------------------
# Blocks: buyer / auditor / implementer
# ---------------------------------------------------------------------------


_ASSURANCE_RANK = {"full": 3, "partial": 2, "contributing": 1}
_CRITICALITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _criticality_score(value: Optional[str]) -> int:
    if not isinstance(value, str):
        return 0
    return _CRITICALITY_RANK.get(value.strip().lower(), 0)


def _uc_playbook_rank(
    row: Mapping[str, Any],
    uc_index: Mapping[str, Mapping[str, Any]],
) -> Tuple[int, int, Tuple[int, int, int]]:
    """Sort key: (-assurance, -criticality, -UC order) — lower is better.

    Both ``assurance`` and ``criticality`` are normalised case-insensitively
    because sidecars use lowercase (``high``, ``critical``) while schema
    enums use titlecase; ranking both on the same scale keeps the playbook
    deterministic regardless of source casing.
    """
    uc_id = row["ucId"]
    uc = uc_index.get(uc_id) or {}
    assurance = (row.get("assurance") or uc.get("assurance") or "").lower()
    criticality = row.get("criticality") or uc.get("criticality")
    return (
        -_ASSURANCE_RANK.get(assurance, 0),
        -_criticality_score(criticality),
        _uc_sort_key_from_id(uc_id),
    )


def build_auditor_block(
    reg_payload: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    """Flatten all per-version ``clauseCoverageMatrix[]`` entries into a
    single auditor-facing list. Keeps the matrix shape (one row per
    clause) but annotates each row with its version so multi-version
    regulations render cleanly in the HTML.
    """
    out: List[Dict[str, Any]] = []
    for v in reg_payload.get("versions") or []:
        ver_str = v.get("version")
        if not isinstance(ver_str, str):
            continue
        for row in v.get("clauseCoverageMatrix") or []:
            out.append({**row, "version": ver_str})
    out.sort(key=lambda r: (r.get("version", ""), r.get("clause", "")))
    return out


def _load_detailed_clause(
    reg_id: str,
    version: str,
    clause: str,
) -> Optional[Dict[str, Any]]:
    """Pull the Phase 2a per-clause detail file (with UC controlObjective
    and evidenceArtifact) if it exists.
    """
    canonical = f"{reg_id}@{version}#{clause}"
    # We mirror ``clause_filename`` from generate_clause_index.py without
    # importing it to keep the two scripts decoupled.
    reg_part = urllib.parse.quote(reg_id, safe="-._")
    ver_part = urllib.parse.quote(version, safe="-._").replace("/", "_")
    clause_part = urllib.parse.quote(clause, safe="-._")
    path = CLAUSES_DIR / f"{reg_part}__{ver_part}__{clause_part}.json"
    if not path.exists():
        return None
    return _load_json(path)


def build_implementer_block(
    reg_payload: Mapping[str, Any],
    uc_index: Mapping[str, Mapping[str, Any]],
    max_ucs_per_clause: int = 3,
) -> List[Dict[str, Any]]:
    """Return the quick-start playbook: for each clause that already has
    at least one covering UC, list up to ``max_ucs_per_clause`` UCs
    ranked by assurance then criticality then ordinal UC id.
    """
    reg_id = reg_payload.get("id") or ""
    playbook: List[Dict[str, Any]] = []
    for v in reg_payload.get("versions") or []:
        ver_str = v.get("version")
        if not isinstance(ver_str, str):
            continue
        for row in v.get("clauseCoverageMatrix") or []:
            covering = row.get("coveringUcs") or []
            if not covering:
                continue
            detail = _load_detailed_clause(reg_id, ver_str, row.get("clause", ""))
            scored: List[Dict[str, Any]] = []
            if detail:
                for uc_row in detail.get("coveringUcs") or []:
                    scored.append(
                        {
                            "ucId": uc_row["ucId"],
                            "ucTitle": uc_row.get("ucTitle") or "",
                            "assurance": uc_row.get("assurance"),
                            "mode": uc_row.get("mode"),
                            "controlObjective": uc_row.get("controlObjective"),
                            "evidenceArtifact": uc_row.get("evidenceArtifact"),
                            "criticality": uc_row.get("criticality")
                            or (uc_index.get(uc_row["ucId"]) or {}).get("criticality"),
                        }
                    )
            else:
                for uc_id in covering:
                    uc = uc_index.get(uc_id) or {}
                    scored.append(
                        {
                            "ucId": uc_id,
                            "ucTitle": uc.get("title") or "",
                            "assurance": None,
                            "mode": None,
                            "controlObjective": None,
                            "evidenceArtifact": None,
                            "criticality": uc.get("criticality"),
                        }
                    )
            scored.sort(key=lambda r: _uc_playbook_rank(r, uc_index))
            playbook.append(
                {
                    "version": ver_str,
                    "clause": row.get("clause"),
                    "topic": row.get("topic"),
                    "priorityWeight": row.get("priorityWeight"),
                    "coverageState": row.get("coverageState"),
                    "quickStartUcs": scored[:max_ucs_per_clause],
                }
            )
    playbook.sort(
        key=lambda p: (
            -(float(p.get("priorityWeight") or 0.0)),
            p.get("version", ""),
            p.get("clause") or "",
        )
    )
    return playbook


def _headline_phrase(summary: Mapping[str, Any]) -> str:
    total = summary.get("commonClauseCount") or 0
    covered = summary.get("coveredClauseCount") or 0
    pw = summary.get("priorityWeightedCoveragePercent")
    if not total:
        return "No common clauses are enumerated for this regulation yet."
    return (
        f"{covered} of {total} common clauses are covered by the catalogue, "
        f"with a priority-weighted coverage of {pw}% when each clause is "
        "weighted by regulator priority language."
    )


def build_buyer_block(
    reg_payload: Mapping[str, Any],
    uc_index: Mapping[str, Mapping[str, Any]],
    max_highlights: int = 5,
    max_gaps: int = 3,
) -> Dict[str, Any]:
    """Build the narrative-headline block for the buyer view.

    * ``coverageHeadline`` — a one-sentence summary.
    * ``topFiveHighlights[]`` — highest-priority covered clauses, each
      with one killer UC (the first in the implementer playbook for
      that clause).
    * ``topThreeGaps[]`` — highest-priority uncovered / contributing-only
      clauses.
    """
    all_rows: List[Dict[str, Any]] = []
    for v in reg_payload.get("versions") or []:
        ver_str = v.get("version")
        if not isinstance(ver_str, str):
            continue
        for row in v.get("clauseCoverageMatrix") or []:
            all_rows.append({**row, "version": ver_str})

    covered = [r for r in all_rows if r.get("coveringUcs")]
    covered.sort(
        key=lambda r: (
            -(float(r.get("priorityWeight") or 0.0)),
            -_ASSURANCE_RANK.get(r.get("topAssurance") or "", 0),
            r.get("version", ""),
            r.get("clause") or "",
        )
    )
    uncovered = [r for r in all_rows if not r.get("coveringUcs") and r.get("onCommonList")]
    uncovered.sort(
        key=lambda r: (
            -(float(r.get("priorityWeight") or 0.0)),
            r.get("version", ""),
            r.get("clause") or "",
        )
    )

    highlights = []
    for row in covered[:max_highlights]:
        killer_uc_id = (row.get("coveringUcs") or [None])[0]
        killer_uc = uc_index.get(killer_uc_id) if killer_uc_id else None
        killer_title = (killer_uc or {}).get("title") or ""
        highlights.append(
            {
                "clause": row.get("clause"),
                "version": row.get("version"),
                "topic": row.get("topic"),
                "priorityWeight": row.get("priorityWeight"),
                "topAssurance": row.get("topAssurance"),
                "killerUcId": killer_uc_id,
                "killerUcTitle": killer_title,
                "why": (
                    f"Clause {row.get('clause')} ({row.get('topic') or 'topic not recorded'}) "
                    f"carries a regulator-assigned priority weight of "
                    f"{row.get('priorityWeight')}, and the catalogue covers it at "
                    f"assurance={row.get('topAssurance')}."
                ),
            }
        )
    gaps = []
    for row in uncovered[:max_gaps]:
        gaps.append(
            {
                "clause": row.get("clause"),
                "version": row.get("version"),
                "topic": row.get("topic"),
                "priorityWeight": row.get("priorityWeight"),
                "obligationText": row.get("obligationText"),
                "mitigationNote": (
                    f"No UC currently claims {row.get('clause')} "
                    f"({row.get('topic') or ''}). Candidates are tracked in "
                    "docs/compliance-gaps.md until a UC is authored."
                ),
            }
        )

    # Aggregate coverage summary across versions
    totals = {
        "commonClauseCount": 0,
        "coveredClauseCount": 0,
        "priorityWeightedCoveragePercent": 0.0,
        "stateCounts": {
            "covered-full": 0,
            "covered-partial": 0,
            "contributing-only": 0,
            "uncovered": 0,
        },
    }
    pw_values: List[float] = []
    for v in reg_payload.get("versions") or []:
        s = v.get("coverageSummary") or {}
        totals["commonClauseCount"] += int(s.get("commonClauseCount") or 0)
        totals["coveredClauseCount"] += int(s.get("coveredClauseCount") or 0)
        sc = s.get("stateCounts") or {}
        for k in totals["stateCounts"]:
            totals["stateCounts"][k] += int(sc.get(k) or 0)
        pw = s.get("priorityWeightedCoveragePercent")
        if isinstance(pw, (int, float)):
            pw_values.append(float(pw))
    if pw_values:
        totals["priorityWeightedCoveragePercent"] = round(
            sum(pw_values) / len(pw_values), 2
        )

    return {
        "coverageHeadline": _headline_phrase(totals),
        "summary": totals,
        "topFiveHighlights": highlights,
        "topThreeGaps": gaps,
    }


# ---------------------------------------------------------------------------
# Related endpoints discovery
# ---------------------------------------------------------------------------


def discover_evidence_pack(reg_id: str) -> Optional[str]:
    cand = EVIDENCE_PACK_DIR / f"{reg_id}.md"
    if cand.exists():
        return f"docs/evidence-packs/{reg_id}.md"
    return None


def discover_primer_anchor(reg_short: str) -> Optional[str]:
    """Find the ``docs/regulatory-primer.md`` anchor for a regulation.

    Primer headings look like ``### 4.1 GDPR — General Data Protection...``
    or ``### 4.2 UK GDPR — ...``. GitHub-style anchor slugs strip the
    leading hash marks, lowercase, and replace runs of non-alphanumeric
    characters with a single hyphen — matching what GitHub generates for
    ``[text](#anchor)`` links so the HTML surfaces can link straight in.
    """
    if not PRIMER_PATH.exists():
        return None
    text = PRIMER_PATH.read_text(encoding="utf-8")
    slug_target = _SLUG_RX.sub("-", reg_short.lower()).strip("-")
    if not slug_target:
        return None
    # Match priority: (1) heading starts with the target (strongest),
    # (2) heading contains target as a bordered token (surrounded by
    # non-alphanumerics or edges), (3) heading contains target as a
    # substring (weakest — used only when the previous two fail).
    # Within each tier, the shortest heading wins so we don't accidentally
    # land on a derivative section that merely references the primary
    # regulation name.
    starts_match: Optional[Tuple[int, str]] = None
    token_match: Optional[Tuple[int, str]] = None
    contains_match: Optional[Tuple[int, str]] = None
    # Token regex: target preceded and followed by either the start/end of
    # string or by a non-alphanumeric character. ``\b`` would also work
    # for ASCII slugs but we intentionally use the explicit form so the
    # match survives punctuation like ``(``, ``—``, or ``·``.
    token_rx = re.compile(
        rf"(?:^|[^a-z0-9]){re.escape(slug_target)}(?:$|[^a-z0-9])"
    )
    for m in re.finditer(r"^###\s*\d+\.\d+\s+(?P<heading>[^\n]+)$", text, re.MULTILINE):
        heading_slug = _SLUG_RX.sub("-", m.group("heading").lower()).strip("-")
        if not heading_slug:
            continue
        anchor = _github_heading_anchor(m.group(0))
        score = len(heading_slug)
        if heading_slug.startswith(slug_target + "-") or heading_slug == slug_target:
            if starts_match is None or score < starts_match[0]:
                starts_match = (score, anchor)
        elif token_rx.search(heading_slug):
            if token_match is None or score < token_match[0]:
                token_match = (score, anchor)
        elif slug_target in heading_slug:
            if contains_match is None or score < contains_match[0]:
                contains_match = (score, anchor)
    picked = starts_match or token_match or contains_match
    if not picked:
        return None
    return f"docs/regulatory-primer.md#{picked[1]}"


def _github_heading_anchor(heading_line: str) -> str:
    """Approximate GitHub's heading-to-anchor algorithm.

    GitHub: strip leading ``#`` marks and the trailing newline, lowercase,
    drop anything that isn't alphanumeric/hyphen/underscore/space, then
    collapse whitespace to single hyphens. The algorithm is stable
    enough for our deterministic anchor link.
    """
    s = re.sub(r"^#+\s*", "", heading_line).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s)
    return s.strip("-")


# ---------------------------------------------------------------------------
# Build one story file
# ---------------------------------------------------------------------------


def build_story(
    reg_payload: Mapping[str, Any],
    areas: Mapping[str, Any],
    uc_index: Mapping[str, Mapping[str, Any]],
    generated_at: str,
    api_version: str,
    catalogue_version: str,
) -> Dict[str, Any]:
    reg_id = reg_payload["id"]
    reg_short = reg_payload.get("shortName") or reg_payload.get("name") or reg_id
    reg_name = reg_payload.get("name") or reg_short
    narrative = narrative_for_regulation(reg_id, reg_short, areas)
    narrative_ref = None
    if narrative:
        narrative_ref = (
            f"non-technical-view.js#cat-22/area/{_narrative_slug(narrative['name'])}"
        )

    evidence_pack = discover_evidence_pack(reg_id)
    primer_anchor = discover_primer_anchor(reg_short)

    return {
        "apiVersion": api_version,
        "catalogueVersion": catalogue_version,
        "generatedAt": generated_at,
        "regulationId": reg_id,
        "regulationName": reg_name,
        "regulationShortName": reg_short,
        "tier": reg_payload.get("tier"),
        "jurisdiction": reg_payload.get("jurisdiction"),
        "narrative": narrative,
        "narrativeRef": narrative_ref,
        "buyer": build_buyer_block(reg_payload, uc_index),
        "auditor": build_auditor_block(reg_payload),
        "implementer": {
            "quickStartPlaybook": build_implementer_block(reg_payload, uc_index),
        },
        "relatedEndpoints": {
            "regulation": f"/api/v1/compliance/regulations/{reg_id}.json",
            "clauseIndex": "/api/v1/compliance/clauses/index.json",
            "storyIndex": "/api/v1/compliance/story/index.json",
            "evidencePack": evidence_pack,
            "primerAnchor": primer_anchor,
            "clauseNavigatorDeepLink": f"clause-navigator.html#{reg_id}",
            "buyerStoryPage": f"compliance-story.html?reg={reg_id}",
        },
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def generate(
    output_root: Optional[pathlib.Path] = None,
    *,
    regs_dir: Optional[pathlib.Path] = None,
) -> Dict[str, Any]:
    """Regenerate every ``compliance/story/*.json`` file under ``output_root``.

    ``regs_dir`` overrides the location of the augmented per-regulation
    endpoints.  It defaults to the canonical
    ``api/v1/compliance/regulations`` so ad-hoc callers keep the
    pre-existing behaviour; ``generate_api_surface.py`` passes a temp-
    rooted path so the unified ``--check`` drift guard can operate on
    a fully ephemeral tree.
    """
    output_root = output_root or OUT_DIR
    regs_source = regs_dir or REGS_DIR
    if not regs_source.exists():
        raise SystemExit(
            f"ERROR: {regs_source} missing. "
            "Run scripts/generate_api_surface.py and scripts/augment_regulation_api.py first."
        )
    areas = load_cat22_areas()
    uc_index = load_uc_index()
    generated_at = _deterministic_timestamp()
    api_version = "v1"
    catalogue_version = _read_version()

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    all_reg_summaries: List[Dict[str, Any]] = []
    for reg_path in sorted(regs_source.glob("*.json")):
        if reg_path.name == "index.json" or "@" in reg_path.stem:
            continue
        reg_payload = _load_json(reg_path)
        reg_id = reg_payload.get("id")
        if not isinstance(reg_id, str):
            continue
        story = build_story(
            reg_payload, areas, uc_index, generated_at, api_version, catalogue_version
        )
        _write_json(output_root / f"{reg_id}.json", story)
        all_reg_summaries.append(
            {
                "regulationId": reg_id,
                "regulationShortName": story["regulationShortName"],
                "tier": story.get("tier"),
                "endpoint": f"/api/v1/compliance/story/{reg_id}.json",
                "coverageHeadline": story["buyer"]["coverageHeadline"],
                "priorityWeightedCoveragePercent": story["buyer"]["summary"][
                    "priorityWeightedCoveragePercent"
                ],
                "commonClauseCount": story["buyer"]["summary"]["commonClauseCount"],
                "coveredClauseCount": story["buyer"]["summary"]["coveredClauseCount"],
                "narrativePresent": bool(story.get("narrative")),
                "evidencePackPresent": bool(story["relatedEndpoints"].get("evidencePack")),
            }
        )

    all_reg_summaries.sort(key=lambda r: r["regulationId"])
    index = {
        "apiVersion": api_version,
        "catalogueVersion": catalogue_version,
        "generatedAt": generated_at,
        "totalRegulations": len(all_reg_summaries),
        "regulations": all_reg_summaries,
        "methodology": {
            "buyer": "topFive highlights by priorityWeight desc then assurance desc; topThree gaps by priorityWeight desc among uncovered.",
            "auditor": "full clauseCoverageMatrix rows from api/v1/compliance/regulations/{id}.json.",
            "implementer": "quickStartPlaybook[] — per covered clause, up to 3 UCs ranked by assurance desc then criticality desc then UC-id asc.",
        },
    }
    _write_json(output_root / "index.json", index)
    return index


def _hash_tree(root: pathlib.Path) -> str:
    h = hashlib.sha256()
    if not root.exists():
        return h.hexdigest()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    return h.hexdigest()


def _check_drift() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        generate(tmp_root)
        new_hash = _hash_tree(tmp_root)
    committed_hash = _hash_tree(OUT_DIR)
    if new_hash != committed_hash:
        print(
            "ERROR: api/v1/compliance/story/ is out of date. "
            "Run scripts/generate_story_payload.py to regenerate.",
            file=sys.stderr,
        )
        return 1
    print(f"api/v1/compliance/story/ is up to date ({new_hash[:12]})", file=sys.stderr)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        return _check_drift()
    try:
        index = generate()
    except SystemExit:
        raise
    except Exception as err:
        print(f"UNEXPECTED ERROR: {err!r}", file=sys.stderr)
        return 2
    print(
        f"Wrote {index['totalRegulations']} story payloads to "
        f"{OUT_DIR.relative_to(REPO_ROOT)} (catalogue v{index['catalogueVersion']}).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
