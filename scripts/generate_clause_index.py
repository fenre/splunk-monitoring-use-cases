#!/usr/bin/env python3
"""Generate the clause → UC reverse index under ``api/v1/compliance/clauses/``.

Introduced by the Regulation-to-UC Story Redesign (Phase 2a). The catalogue
already stores every UC → clause mapping inside each UC sidecar's
``compliance[]`` array, but the traversal only runs one way: given a UC you
can list its clauses. This generator inverts the relation and answers the
auditor-facing question "given a clause, show me every UC that covers it"
in a single static API call.

Inputs (all in-repo, zero network):

* ``content/cat-*/UC-*.json``           — UC sidecars (schema v1.6.0).
* ``data/regulations.json``             — framework registry (schema v1.1.0);
                                          provides authoritative clause
                                          topics, priority weights, and
                                          optional ``obligationText`` /
                                          ``obligationSource``.

Outputs (written to ``api/v1/compliance/clauses/``):

* ``index.json``                         — flat registry of every clause
                                           (every entry in every framework's
                                           ``commonClauses[]`` plus every
                                           clause that any UC tags). One
                                           row per ``(regulationId, version,
                                           clause)`` tuple.
* ``<clauseId>.json``                    — per-clause detail, including the
                                           full obligation text, each
                                           covering UC's ``controlObjective``
                                           / ``evidenceArtifact`` / ``mode``
                                           / ``assurance`` / ``assurance_rationale``,
                                           and a ``gapNote`` when no UC
                                           covers the clause.

Design invariants (mirrors ``scripts/generate_api_surface.py``):

* **Deterministic.** All dicts serialise with ``sort_keys=True`` and every
  list is sorted by a stable key. Timestamps come from ``SOURCE_DATE_EPOCH``
  or ``git log -1 HEAD``.
* **Additive-only within v1.** The script MUST NOT remove or rename any
  endpoint already under ``api/v1/compliance/clauses/``.
* **Side-effect safe.** ``--check`` regenerates into a temp dir and diffs
  against the committed tree so CI can fail on drift.
* **Offline.** Zero network calls.

File-naming contract (``<clauseId>``):

* ``clauseId = "{regulationId}@{version}#{clause}"`` per Phase 1's
  ``obligationRef`` pattern in ``schemas/uc.schema.json``.
* Filesystem representation replaces ``@`` with ``__``, ``#`` with ``__``,
  ``/`` with ``_``, and URL-encodes everything else with ``quote(..., safe='-._')``
  so the clause IDs ``§164.312(b)``, ``Art.32(1)(b)``, and ``10.2.1``
  all round-trip cleanly through ``pathlib.Path``. The in-JSON
  ``clauseId`` field keeps the canonical form; the ``endpoint`` field
  carries the URL-safe filename.

Exit codes:
    0  Success.
    1  Validation failure (missing/invalid input, determinism check failed).
    2  Uncaught exception (bug).
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
UC_GLOB = "content/cat-*/UC-*.json"
REGULATIONS_PATH = REPO_ROOT / "data" / "regulations.json"
OUT_DIR = REPO_ROOT / "api" / "v1" / "compliance" / "clauses"
VERSION_FILE = REPO_ROOT / "VERSION"


# ---------------------------------------------------------------------------
# Deterministic IO helpers (same contract as generate_api_surface.py)
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


def _read_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _write_json(path: pathlib.Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def _load_json(path: pathlib.Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Clause id normalisation
# ---------------------------------------------------------------------------


_SAFE = "-._"


def _encode_component(s: str) -> str:
    return urllib.parse.quote(s, safe=_SAFE)


def clause_id(regulation_id: str, version: str, clause: str) -> str:
    """Canonical clause id matching the schema v1.6.0 ``obligationRef`` pattern.

    Examples:
        >>> clause_id('gdpr', '2016/679', 'Art.32')
        'gdpr@2016/679#Art.32'
        >>> clause_id('hipaa-security', '2013-final', '§164.312(b)')
        'hipaa-security@2013-final#§164.312(b)'
    """
    return f"{regulation_id}@{version}#{clause}"


def clause_filename(clause_id_str: str) -> str:
    """Filesystem-safe filename for a clause id.

    Rationale: ``@`` and ``#`` are reserved URL characters and ``/`` in the
    version (e.g. GDPR ``2016/679``) breaks ``pathlib``. The mapping is
    reversible — ``reverse_clause_filename`` restores the canonical id — so
    consumers that need the human-readable clause id can round-trip it.
    """
    reg_part, _, rest = clause_id_str.partition("@")
    version_part, _, clause_part = rest.partition("#")
    return (
        _encode_component(reg_part)
        + "__"
        + _encode_component(version_part).replace("/", "_")
        + "__"
        + _encode_component(clause_part)
        + ".json"
    )


_RESTORE_SLASH = re.compile(r"(?<=[A-Za-z0-9])_(?=\d)")


def reverse_clause_filename(filename: str) -> str:
    """Best-effort inverse of ``clause_filename`` (lossless for the ids used
    in ``data/regulations.json``).

    Not a hard guarantee: consumers needing the canonical clause id should
    use the ``clauseId`` field inside the JSON payload. Used only by tests
    to prove the round-trip.
    """
    stem = filename.removesuffix(".json")
    parts = stem.split("__")
    if len(parts) != 3:
        raise ValueError(f"unexpected clause filename shape: {filename}")
    reg, version, clause = (urllib.parse.unquote(p) for p in parts)
    if "/" not in version and _RESTORE_SLASH.search(version):
        version = _RESTORE_SLASH.sub("/", version, count=1)
    return f"{reg}@{version}#{clause}"


# ---------------------------------------------------------------------------
# Input loaders
# ---------------------------------------------------------------------------


_UC_ID_RX = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _uc_sort_key(uc: Mapping[str, Any]) -> Tuple[int, int, int]:
    m = _UC_ID_RX.match(str(uc.get("id", "")))
    if not m:
        return (10**6, 10**6, 10**6)
    return tuple(int(x) for x in m.groups())  # type: ignore[return-value]


def load_ucs() -> List[Dict[str, Any]]:
    """Load every UC sidecar.

    Uses ``content/cat-*/UC-*.json`` — the current on-disk location. The
    older ``use-cases/cat-*/uc-*.json`` path is legacy and empty; it is
    intentionally not consulted here.
    """
    ucs: List[Dict[str, Any]] = []
    for path in sorted(REPO_ROOT.glob(UC_GLOB)):
        try:
            data = _load_json(path)
        except json.JSONDecodeError as err:
            raise SystemExit(f"ERROR: invalid JSON in {path}: {err}") from err
        if not isinstance(data.get("id"), str):
            continue
        data["_sourcePath"] = str(path.relative_to(REPO_ROOT))
        ucs.append(data)
    ucs.sort(key=_uc_sort_key)
    return ucs


def load_regulations() -> Dict[str, Any]:
    return _load_json(REGULATIONS_PATH)


# ---------------------------------------------------------------------------
# Core pivot: (reg, version, clause) → UCs
# ---------------------------------------------------------------------------


_ASSURANCE_RANK = {"full": 3, "partial": 2, "contributing": 1}


def _compare_assurance(a: Optional[str], b: Optional[str]) -> str:
    """Pick the better (numerically higher) of two assurance labels."""
    if not a:
        return b or ""
    if not b:
        return a or ""
    return a if _ASSURANCE_RANK.get(a, 0) >= _ASSURANCE_RANK.get(b, 0) else b


def build_clause_buckets(
    ucs: Iterable[Mapping[str, Any]],
) -> Dict[Tuple[str, str, str], List[Dict[str, Any]]]:
    """Bucket every ``compliance[]`` entry by ``(regulationId, version, clause)``.

    The regulation id is normalised to lowercase slug form so that a UC
    tagging ``"PCI-DSS"`` or ``"PCI DSS"`` or ``"pci-dss"`` all land in the
    same bucket. The display name is preserved alongside the slug so the
    final payload can render the canonical casing.
    """
    buckets: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for uc in ucs:
        compliance = uc.get("compliance") or []
        if not isinstance(compliance, list):
            continue
        for entry in compliance:
            if not isinstance(entry, Mapping):
                continue
            reg = entry.get("regulation")
            ver = entry.get("version")
            clause = entry.get("clause")
            if not all(isinstance(x, str) and x.strip() for x in (reg, ver, clause)):
                continue
            key = (_slugify_regulation(reg), str(ver), str(clause))
            buckets[key].append(
                {
                    "ucId": uc["id"],
                    "ucTitle": uc.get("title") or "",
                    "category": int(uc["id"].split(".", 1)[0]),
                    "mode": entry.get("mode"),
                    "assurance": entry.get("assurance"),
                    "assuranceRationale": entry.get("assurance_rationale"),
                    "controlObjective": entry.get("controlObjective"),
                    "evidenceArtifact": entry.get("evidenceArtifact"),
                    "provenance": entry.get("provenance"),
                    "clauseUrl": entry.get("clauseUrl"),
                    "regulationLabel": reg,
                    "criticality": uc.get("criticality"),
                    "legalCaveat": entry.get("legalCaveat"),
                    "smeCaveat": entry.get("smeCaveat"),
                }
            )
    return buckets


_SLUG_RX = re.compile(r"[^a-z0-9]+")


def _slugify_regulation(reg: str) -> str:
    """Match the slug convention used by ``data/regulations.json`` ``id`` fields.

    GDPR → ``gdpr``; ``PCI-DSS`` → ``pci-dss``; ``NIST 800-53`` → ``nist-800-53``.
    """
    return _SLUG_RX.sub("-", reg.strip().lower()).strip("-")


# ---------------------------------------------------------------------------
# Regulation / common-clause lookup
# ---------------------------------------------------------------------------


def build_regulation_lookup(
    regulations: Mapping[str, Any],
) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    """Return ``(regSlug, version, clause) → commonClause enrichment``.

    One entry per ``commonClauses[]`` row across every framework / version,
    keyed by the same tuple as ``build_clause_buckets``. Includes the
    regulator-facing metadata every surface needs (topic, priority weight,
    obligation text, authoritative URL).
    """
    lookup: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for fw in regulations.get("frameworks", []):
        fw_id = fw.get("id")
        if not isinstance(fw_id, str):
            continue
        slug = _slugify_regulation(fw_id)
        fw_name = fw.get("name") or fw.get("shortName") or fw_id
        fw_short = fw.get("shortName") or fw_name
        tier = fw.get("tier")
        for v in fw.get("versions", []):
            ver = v.get("version")
            if not isinstance(ver, str):
                continue
            template = v.get("clauseUrlTemplate")
            auth_url = v.get("authoritativeUrl")
            for cc in v.get("commonClauses") or []:
                clause = cc.get("clause")
                if not isinstance(clause, str):
                    continue
                key = (slug, ver, clause)
                lookup[key] = {
                    "regulationId": fw_id,
                    "regulationName": fw_name,
                    "regulationShortName": fw_short,
                    "tier": tier,
                    "version": ver,
                    "clause": clause,
                    "topic": cc.get("topic"),
                    "priorityWeight": cc.get("priorityWeight"),
                    "obligationText": cc.get("obligationText"),
                    "obligationSource": cc.get("obligationSource"),
                    "authoritativeUrl": auth_url,
                    "clauseUrlTemplate": template,
                }
    return lookup


def fill_clause_url(
    clause_url: Optional[str],
    lookup: Optional[Mapping[str, Any]],
) -> Optional[str]:
    """Pick the best available deep-link for a clause.

    Preference order: (1) the UC sidecar's explicit ``clauseUrl``, (2) the
    regulator-published paragraph in ``obligationSource``, (3) the
    ``clauseUrlTemplate`` with ``{clause}`` substituted, (4) the framework's
    top-level authoritative URL.
    """
    if isinstance(clause_url, str) and clause_url:
        return clause_url
    if not lookup:
        return None
    os_url = lookup.get("obligationSource")
    if isinstance(os_url, str) and os_url:
        return os_url
    template = lookup.get("clauseUrlTemplate")
    clause = lookup.get("clause")
    if isinstance(template, str) and template and isinstance(clause, str):
        return template.replace("{clause}", urllib.parse.quote(clause, safe="-._()"))
    auth = lookup.get("authoritativeUrl")
    return auth if isinstance(auth, str) else None


# ---------------------------------------------------------------------------
# Payload construction
# ---------------------------------------------------------------------------


def _assurance_breakdown(entries: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    out = {"full": 0, "partial": 0, "contributing": 0, "unknown": 0}
    for e in entries:
        a = e.get("assurance")
        if a in out:
            out[a] += 1
        else:
            out["unknown"] += 1
    return out


def _top_assurance(entries: Iterable[Mapping[str, Any]]) -> Optional[str]:
    best: Optional[str] = None
    for e in entries:
        best = _compare_assurance(best, e.get("assurance"))
    return best or None


def _mode_breakdown(entries: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = defaultdict(int)
    for e in entries:
        m = e.get("mode") or "unspecified"
        out[m] += 1
    return dict(out)


def _coverage_state(entries: List[Mapping[str, Any]]) -> str:
    """Derived label used by the Phase 2b ``clauseCoverageMatrix[]``.

    ``covered-full``      - at least one UC with ``assurance=full`` and
                            ``mode=satisfies``.
    ``covered-partial``   - at least one UC with ``assurance=partial`` and
                            ``mode=satisfies``.
    ``contributing-only`` - at least one UC covers the clause but only at
                            ``contributing`` assurance (or only via
                            ``detects-violation-of``).
    ``uncovered``         - no UC tags the clause.
    """
    if not entries:
        return "uncovered"
    if any(
        e.get("assurance") == "full" and e.get("mode") == "satisfies" for e in entries
    ):
        return "covered-full"
    if any(
        e.get("assurance") == "partial" and e.get("mode") == "satisfies" for e in entries
    ):
        return "covered-partial"
    return "contributing-only"


def build_clause_detail(
    reg_slug: str,
    version: str,
    clause: str,
    bucket_entries: List[Mapping[str, Any]],
    reg_entry: Optional[Mapping[str, Any]],
    generated_at: str,
    api_version: str,
) -> Dict[str, Any]:
    """Construct the per-clause detail payload.

    Falls back to a minimal shell when the clause is authored on a UC but
    not enumerated in ``data/regulations.json#/frameworks/versions/commonClauses``.
    """
    reg_id = reg_entry.get("regulationId") if reg_entry else reg_slug
    reg_short = reg_entry.get("regulationShortName") if reg_entry else reg_slug
    reg_name = reg_entry.get("regulationName") if reg_entry else reg_slug
    tier = reg_entry.get("tier") if reg_entry else None
    topic = reg_entry.get("topic") if reg_entry else None
    priority_weight = reg_entry.get("priorityWeight") if reg_entry else None
    obligation_text = reg_entry.get("obligationText") if reg_entry else None
    obligation_source = reg_entry.get("obligationSource") if reg_entry else None

    canonical = clause_id(reg_id, version, clause)

    covering_ucs = sorted(
        [
            {
                "ucId": e["ucId"],
                "ucTitle": e.get("ucTitle") or "",
                "category": e.get("category"),
                "mode": e.get("mode"),
                "assurance": e.get("assurance"),
                "assuranceRationale": e.get("assuranceRationale"),
                "controlObjective": e.get("controlObjective"),
                "evidenceArtifact": e.get("evidenceArtifact"),
                "provenance": e.get("provenance"),
                "clauseUrl": fill_clause_url(e.get("clauseUrl"), reg_entry),
                "criticality": e.get("criticality"),
                "legalCaveat": e.get("legalCaveat"),
                "smeCaveat": e.get("smeCaveat"),
            }
            for e in bucket_entries
        ],
        key=lambda row: (
            -(_ASSURANCE_RANK.get(row.get("assurance") or "", 0)),
            _uc_sort_key({"id": row["ucId"]}),
        ),
    )

    coverage_state = _coverage_state(bucket_entries)
    gap_note = None
    if coverage_state == "uncovered" and reg_entry is not None:
        gap_note = (
            f"{reg_short} clause {clause} ({topic or 'no topic recorded'}) "
            "is listed in data/regulations.json as a common clause but no use "
            "case currently tags it. Candidate UCs are tracked in "
            "docs/compliance-gaps.md and api/v1/compliance/gaps.json."
        )
    elif coverage_state == "contributing-only":
        gap_note = (
            f"{reg_short} clause {clause} has only contributing or "
            "detection-mode coverage. A primary (assurance=full or partial, "
            "mode=satisfies) UC is still needed to close the clause."
        )

    payload: Dict[str, Any] = {
        "apiVersion": api_version,
        "clauseId": canonical,
        "regulationId": reg_id,
        "regulationName": reg_name,
        "regulationShortName": reg_short,
        "tier": tier,
        "version": version,
        "clause": clause,
        "topic": topic,
        "priorityWeight": priority_weight,
        "obligationText": obligation_text,
        "obligationSource": obligation_source,
        "authoritativeUrl": fill_clause_url(None, reg_entry),
        "coverageState": coverage_state,
        "topAssurance": _top_assurance(bucket_entries),
        "coveringUcCount": len(covering_ucs),
        "coveringUcs": covering_ucs,
        "assuranceBreakdown": _assurance_breakdown(bucket_entries),
        "modeBreakdown": _mode_breakdown(bucket_entries),
        "gapNote": gap_note,
        "endpoint": f"/api/v1/compliance/clauses/{clause_filename(canonical)}",
        "relatedEndpoints": {
            "regulation": f"/api/v1/compliance/regulations/{reg_id}.json",
            "regulationVersion": f"/api/v1/compliance/regulations/{reg_id}@{urllib.parse.quote(version, safe='-.')}.json",
            "story": f"/api/v1/compliance/story/{reg_id}.json",
            "index": "/api/v1/compliance/clauses/index.json",
        },
        "generatedAt": generated_at,
    }
    return payload


def build_index(
    detail_payloads: Iterable[Mapping[str, Any]],
    generated_at: str,
    api_version: str,
    catalogue_version: str,
) -> Dict[str, Any]:
    rows = []
    state_counts = defaultdict(int)
    tier_counts = defaultdict(lambda: defaultdict(int))
    reg_counts: Dict[str, int] = defaultdict(int)
    for p in detail_payloads:
        state = p.get("coverageState") or "uncovered"
        state_counts[state] += 1
        tier = p.get("tier")
        if tier is not None:
            tier_counts[tier][state] += 1
        reg_counts[p["regulationId"]] += 1
        rows.append(
            {
                "clauseId": p["clauseId"],
                "regulationId": p["regulationId"],
                "regulationShortName": p["regulationShortName"],
                "tier": p.get("tier"),
                "version": p["version"],
                "clause": p["clause"],
                "topic": p.get("topic"),
                "priorityWeight": p.get("priorityWeight"),
                "obligationTextPresent": bool(p.get("obligationText")),
                "coverageState": state,
                "topAssurance": p.get("topAssurance"),
                "coveringUcCount": p.get("coveringUcCount", 0),
                "coveringUcs": [row["ucId"] for row in p.get("coveringUcs", [])],
                "assuranceBreakdown": p.get("assuranceBreakdown"),
                "endpoint": p["endpoint"],
            }
        )
    rows.sort(key=lambda r: (r["regulationId"], r["version"], r["clause"]))
    return {
        "apiVersion": api_version,
        "catalogueVersion": catalogue_version,
        "generatedAt": generated_at,
        "totalClauses": len(rows),
        "coverageStateCounts": dict(state_counts),
        "tierCoverageStateCounts": {
            str(k): dict(v) for k, v in sorted(tier_counts.items())
        },
        "clausesByRegulation": dict(sorted(reg_counts.items())),
        "clauses": rows,
        "methodology": {
            "clauseIdShape": "{regulationId}@{version}#{clause}",
            "endpointFilename": "urlencoded components joined by '__', with version '/' replaced by '_'",
            "sources": ["content/cat-*/UC-*.json", "data/regulations.json"],
        },
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def generate(
    output_root: pathlib.Path,
    *,
    ucs: Optional[List[Dict[str, Any]]] = None,
    regulations: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Regenerate every file under ``output_root``.

    Returns the index payload for callers that want to introspect without
    re-reading the file they just wrote.
    """
    ucs = ucs if ucs is not None else load_ucs()
    regulations = regulations if regulations is not None else load_regulations()
    buckets = build_clause_buckets(ucs)
    lookup = build_regulation_lookup(regulations)

    generated_at = _deterministic_timestamp()
    api_version = "v1"
    catalogue_version = _read_version()

    all_keys = set(buckets) | set(lookup)
    details: List[Dict[str, Any]] = []

    for key in sorted(all_keys):
        reg_entry = lookup.get(key)
        bucket = buckets.get(key, [])
        if reg_entry:
            reg_slug = _slugify_regulation(reg_entry["regulationId"])
            version = reg_entry["version"]
            clause = reg_entry["clause"]
        else:
            reg_slug, version, clause = key
        detail = build_clause_detail(
            reg_slug=reg_slug,
            version=version,
            clause=clause,
            bucket_entries=bucket,
            reg_entry=reg_entry,
            generated_at=generated_at,
            api_version=api_version,
        )
        details.append(detail)

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    for detail in details:
        fname = clause_filename(detail["clauseId"])
        _write_json(output_root / fname, detail)

    index = build_index(details, generated_at, api_version, catalogue_version)
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
        generate(pathlib.Path(tmp))
        new_hash = _hash_tree(pathlib.Path(tmp))
    committed_hash = _hash_tree(OUT_DIR)
    if new_hash != committed_hash:
        print(
            "ERROR: api/v1/compliance/clauses/ is out of date. "
            "Run scripts/generate_clause_index.py to regenerate.",
            file=sys.stderr,
        )
        return 1
    print(
        f"api/v1/compliance/clauses/ is up to date ({new_hash[:12]})",
        file=sys.stderr,
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate into a temp directory and diff against the "
        "committed api/v1/compliance/clauses/ tree; exit 1 on drift.",
    )
    args = parser.parse_args(argv)
    if args.check:
        return _check_drift()
    try:
        index = generate(OUT_DIR)
    except SystemExit:
        raise
    except Exception as err:
        print(f"UNEXPECTED ERROR: {err!r}", file=sys.stderr)
        return 2
    print(
        f"Wrote {index['totalClauses']} clauses to {OUT_DIR.relative_to(REPO_ROOT)} "
        f"(catalogue v{index['catalogueVersion']}, generated at {index['generatedAt']})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
