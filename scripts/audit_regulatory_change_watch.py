#!/usr/bin/env python3
"""Phase 5.3 — regulatory change-watch audit.

Three modes:

- ``--check`` (default): hermetic. Validates ``data/regulations-watch.json`` against
  its JSON Schema, cross-references every ``sha256-vendor`` watch entry against
  ``data/provenance/ingest-manifest.json``, confirms each ``regulationId``
  exists in ``data/regulations.json``, and computes staleness warnings/errors
  using the file's ``stalenessPolicy``. Safe to run in pull-request CI.

- ``--fetch``: network-enabled. Executes each ``strategy`` against the live
  publisher/upstream, compares observed state to the recorded state, writes
  deltas back to ``data/regulations-watch.json`` and emits
  ``reports/regulatory-change-watch.json`` for downstream consumers (issue
  opener, dashboard). Intended for the scheduled
  ``.github/workflows/regulatory-watch.yml`` job.

- ``--freeze``: records the current moment as ``lastCheckedAt`` for every entry
  without touching observed state. Useful when seeding or resetting the ledger.

Exit codes: 0 = GREEN, 1 = staleness / validation failure, 2 = internal error.

The goal is auditor-grade provenance: if a tier-1 regulator publishes an
amendment, we must be able to prove the exact day we learned about it and the
exact commit that adopted the change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parent.parent
WATCH_PATH = REPO_ROOT / "data" / "regulations-watch.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "regulations-watch.schema.json"
INGEST_PATH = REPO_ROOT / "data" / "provenance" / "ingest-manifest.json"
REGULATIONS_PATH = REPO_ROOT / "data" / "regulations.json"
REPORT_PATH = REPO_ROOT / "reports" / "regulatory-change-watch.json"

HTTP_TIMEOUT_SECONDS = 30
USER_AGENT = "splunk-monitoring-use-cases/regulatory-change-watch/1.0 (+https://github.com/fsudmann/splunk-monitoring-use-cases)"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _parse_iso(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _days_since(ts: str, now: Optional[datetime] = None) -> Optional[int]:
    parsed = _parse_iso(ts)
    if parsed is None:
        return None
    delta = (now or _now_utc()) - parsed
    return delta.days


def _validate_https_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"watch URL must be https, got scheme={parsed.scheme!r}")
    if not parsed.netloc:
        raise ValueError("watch URL missing netloc")


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def _validate_schema(manifest: Dict[str, Any]) -> List[str]:
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except ImportError as exc:  # pragma: no cover - dev dependency
        raise SystemExit(
            f"[change-watch] missing dev dependency 'jsonschema': {exc}"
        ) from exc

    schema = _load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    return [
        f"schema: {'/'.join(str(p) for p in err.path)}: {err.message}".strip()
        for err in validator.iter_errors(manifest)
    ]


# ---------------------------------------------------------------------------
# Cross-reference validation
# ---------------------------------------------------------------------------


def _load_known_regulations() -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    data = _load_json(REGULATIONS_PATH)
    by_id: Dict[str, Dict[str, Any]] = {}
    extras: List[str] = []
    for entry in data.get("frameworks", []):
        by_id[entry["id"]] = entry
    # MITRE frameworks live outside regulations.json (they are in crosswalks);
    # accept a curated allow-list so we can watch ATT&CK / D3FEND alongside
    # statutory regulations.
    allow_list = ["mitre-attack-enterprise", "d3fend"]
    for extra in allow_list:
        if extra not in by_id:
            extras.append(extra)
    return by_id, extras


def _load_ingest_manifest() -> Dict[str, Dict[str, Any]]:
    data = _load_json(INGEST_PATH)
    return {entry["source_id"]: entry for entry in data.get("provenance", [])}


def _cross_reference_errors(
    manifest: Dict[str, Any],
    regulations: Dict[str, Dict[str, Any]],
    ingest_sources: Dict[str, Dict[str, Any]],
    mitre_allow_list: Iterable[str],
) -> List[str]:
    errors: List[str] = []
    warnings: List[str] = []
    mitre_allow_set = set(mitre_allow_list)
    seen_ids: Dict[str, int] = {}
    for idx, entry in enumerate(manifest["watchlist"]):
        rid = entry["regulationId"]
        if rid in seen_ids:
            errors.append(
                f"watchlist[{idx}] (regulationId={rid}): duplicate entry; "
                f"also at index {seen_ids[rid]}. Merge or remove."
            )
        else:
            seen_ids[rid] = idx

        if rid not in regulations and rid not in mitre_allow_set:
            errors.append(
                f"watchlist[{idx}] (regulationId={rid}): not found in "
                f"data/regulations.json frameworks[] and not in the MITRE allow-list. "
                f"Either add the framework to regulations.json or remove the watch entry."
            )

        strategy = entry.get("strategy", {})
        stype = strategy.get("type")

        if stype == "sha256-vendor":
            for src_id in strategy.get("ingestSourceIds", []):
                if src_id not in ingest_sources:
                    errors.append(
                        f"watchlist[{idx}] (regulationId={rid}): sha256-vendor "
                        f"strategy references unknown ingest source_id={src_id!r}. "
                        f"Add it to data/provenance/ingest-manifest.json or fix the manifest."
                    )
            observed = entry.get("lastObservedHash")
            if observed:
                src_ids = strategy.get("ingestSourceIds", [])
                if src_ids:
                    primary = ingest_sources.get(src_ids[0], {})
                    expected = primary.get("sha256")
                    if expected and observed != expected:
                        errors.append(
                            f"watchlist[{idx}] (regulationId={rid}): lastObservedHash "
                            f"does not match ingest-manifest.json for source_id={src_ids[0]!r}. "
                            f"Re-run --fetch or correct the manifest."
                        )

        elif stype in {"http-head", "rss-atom"}:
            try:
                _validate_https_url(strategy.get("url", ""))
            except ValueError as exc:
                errors.append(
                    f"watchlist[{idx}] (regulationId={rid}): invalid strategy.url — {exc}"
                )

        elif stype == "github-release":
            if not re.match(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", strategy.get("repo", "")):
                errors.append(
                    f"watchlist[{idx}] (regulationId={rid}): github-release "
                    f"strategy.repo must be 'owner/repo'."
                )

        elif stype == "manual-review":
            publisher = strategy.get("publisher", "")
            if not publisher.strip():
                errors.append(
                    f"watchlist[{idx}] (regulationId={rid}): manual-review "
                    f"strategy requires non-empty publisher."
                )

        else:
            errors.append(
                f"watchlist[{idx}] (regulationId={rid}): unknown strategy.type={stype!r}."
            )

    # warnings surfaced alongside errors but don't fail the run
    for w in warnings:
        print(f"  warning: {w}", file=sys.stderr)
    return errors


# ---------------------------------------------------------------------------
# Staleness computation
# ---------------------------------------------------------------------------


def _staleness_findings(manifest: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    policy = manifest["stalenessPolicy"]
    warn_days = {1: policy["tier1WarnDays"], 2: policy["tier2WarnDays"]}
    fail_days = {1: policy["tier1FailDays"], 2: policy["tier2FailDays"]}
    errors: List[str] = []
    warnings: List[str] = []
    for entry in manifest["watchlist"]:
        tier = entry.get("tier", 1)
        days = _days_since(entry["lastCheckedAt"])
        if days is None:
            errors.append(
                f"{entry['regulationId']}: unparseable lastCheckedAt={entry['lastCheckedAt']!r}."
            )
            continue
        if days > fail_days.get(tier, fail_days[1]):
            errors.append(
                f"{entry['regulationId']}: last checked {days} days ago; "
                f"tier-{tier} staleness limit is {fail_days[tier]} days. "
                f"Run 'python3 scripts/audit_regulatory_change_watch.py --fetch' or update the ledger."
            )
        elif days > warn_days.get(tier, warn_days[1]):
            warnings.append(
                f"{entry['regulationId']}: last checked {days} days ago; "
                f"tier-{tier} warn threshold is {warn_days[tier]} days."
            )
        if entry.get("openFinding"):
            warnings.append(
                f"{entry['regulationId']}: open finding — "
                f"{entry['openFinding']['summary']!r}. Address or clear before merging release."
            )
    return errors, warnings


# ---------------------------------------------------------------------------
# --fetch implementation
# ---------------------------------------------------------------------------


def _http_get(url: str, method: str = "GET") -> Tuple[int, Dict[str, str], bytes]:
    """Minimal stdlib fetcher so --fetch has no extra dependencies."""
    import urllib.request

    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as resp:  # noqa: S310 - https enforced elsewhere
        body = resp.read() if method != "HEAD" else b""
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.status, headers, body


def _fetch_sha256_vendor(entry: Dict[str, Any], ingest: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    src_ids = entry["strategy"]["ingestSourceIds"]
    primary_id = src_ids[0]
    primary = ingest.get(primary_id)
    if not primary:
        return {"error": f"ingest source_id {primary_id!r} not found"}
    url = primary["url"]
    _validate_https_url(url)
    status, _, body = _http_get(url, method="GET")
    if status != 200:
        return {"error": f"HTTP {status} fetching {url}"}
    sha = _sha256_bytes(body)
    changed = sha != entry.get("lastObservedHash")
    return {
        "observedHash": sha,
        "changed": changed,
        "summary": (
            f"SHA256 unchanged for {primary_id}"
            if not changed
            else f"SHA256 drift: was {entry.get('lastObservedHash','?')[:8]}, now {sha[:8]} for {primary_id}"
        ),
    }


def _fetch_github_release(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    repo = entry["strategy"]["repo"]
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    status, _, body = _http_get(url)
    if status != 200:
        return {"error": f"HTTP {status} fetching {url}"}
    payload = json.loads(body)
    tag = payload.get("tag_name") or payload.get("name") or ""
    pattern = entry["strategy"].get("versionPattern")
    if pattern and not re.search(pattern, tag):
        return {"error": f"tag {tag!r} does not match versionPattern {pattern!r}"}
    changed = tag != entry.get("lastObservedVersion")
    return {
        "observedVersion": tag,
        "changed": changed,
        "summary": (
            f"release tag unchanged: {tag}"
            if not changed
            else f"new release: {entry.get('lastObservedVersion','?')} -> {tag}"
        ),
    }


def _fetch_http_head(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = entry["strategy"]["url"]
    _validate_https_url(url)
    status, headers, _ = _http_get(url, method="HEAD")
    expected = entry["strategy"].get("expectedStatus", 200)
    if status != expected:
        return {"error": f"HTTP {status} (expected {expected}) for {url}"}
    etag = headers.get("etag") or headers.get("last-modified") or ""
    changed = bool(entry.get("lastObservedEtag")) and etag != entry.get("lastObservedEtag")
    return {
        "observedEtag": etag,
        "changed": changed,
        "summary": (
            f"ETag/Last-Modified unchanged: {etag[:40]}"
            if not changed
            else f"ETag/Last-Modified drift: {entry.get('lastObservedEtag','?')[:40]} -> {etag[:40]}"
        ),
    }


def _fetch_rss_atom(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = entry["strategy"]["url"]
    _validate_https_url(url)
    status, _, body = _http_get(url, method="GET")
    if status != 200:
        return {"error": f"HTTP {status} fetching {url}"}
    # lightweight title match without pulling in feedparser
    titles = re.findall(r"<title[^>]*>(.*?)</title>", body.decode("utf-8", "replace"), re.DOTALL | re.IGNORECASE)
    matches = []
    for term in entry["strategy"].get("matchTerms", []):
        term_lc = term.lower()
        for t in titles:
            if term_lc in t.lower():
                matches.append(t.strip())
    changed = bool(matches)
    return {
        "observedVersion": f"{len(matches)} matching entries" if matches else "no matching entries",
        "changed": changed,
        "summary": (
            "no matching feed entries"
            if not matches
            else "matching entries: " + " | ".join(matches[:3])
        ),
    }


def _fetch_one(entry: Dict[str, Any], ingest: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    stype = entry["strategy"]["type"]
    now = _now_utc().isoformat().replace("+00:00", "Z")
    result: Dict[str, Any] = {"regulationId": entry["regulationId"], "checkedAt": now, "type": stype}
    try:
        if stype == "sha256-vendor":
            result.update(_fetch_sha256_vendor(entry, ingest) or {})
        elif stype == "github-release":
            result.update(_fetch_github_release(entry) or {})
        elif stype == "http-head":
            result.update(_fetch_http_head(entry) or {})
        elif stype == "rss-atom":
            result.update(_fetch_rss_atom(entry) or {})
        elif stype == "manual-review":
            result.update({
                "observedVersion": entry.get("lastObservedVersion", ""),
                "changed": False,
                "summary": "manual-review: no automated probe; human check required",
            })
        else:
            result.update({"error": f"unknown strategy {stype!r}"})
    except Exception as exc:  # noqa: BLE001 - transport errors surfaced to CI log
        result.update({"error": f"{type(exc).__name__}: {exc}"})
    return result


def _apply_fetch_results(manifest: Dict[str, Any], results: List[Dict[str, Any]]) -> None:
    by_id = {r["regulationId"]: r for r in results}
    for entry in manifest["watchlist"]:
        result = by_id.get(entry["regulationId"])
        if not result or "error" in result:
            continue
        entry["lastCheckedAt"] = result["checkedAt"]
        if "observedHash" in result:
            if result["changed"]:
                entry["lastChangedAt"] = result["checkedAt"]
                entry["openFinding"] = {
                    "observedAt": result["checkedAt"],
                    "summary": result["summary"],
                    "newHash": result["observedHash"],
                }
            entry["lastObservedHash"] = result["observedHash"]
        elif "observedVersion" in result:
            if result["changed"]:
                entry["lastChangedAt"] = result["checkedAt"]
                entry["openFinding"] = {
                    "observedAt": result["checkedAt"],
                    "summary": result["summary"],
                    "newVersion": result["observedVersion"],
                }
            entry["lastObservedVersion"] = result["observedVersion"]
        elif "observedEtag" in result:
            if result["changed"]:
                entry["lastChangedAt"] = result["checkedAt"]
                entry["openFinding"] = {
                    "observedAt": result["checkedAt"],
                    "summary": result["summary"],
                }
            entry["lastObservedEtag"] = result["observedEtag"]
    manifest["generatedAt"] = _now_utc().isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------


def _write_report(manifest: Dict[str, Any], results: List[Dict[str, Any]]) -> None:
    summary = {
        "generatedAt": _now_utc().isoformat().replace("+00:00", "Z"),
        "baselineCommit": manifest.get("baselineCommit"),
        "totalWatched": len(manifest["watchlist"]),
        "openFindings": [
            {"regulationId": entry["regulationId"], **entry["openFinding"]}
            for entry in manifest["watchlist"]
            if entry.get("openFinding")
        ],
        "latestFetchResults": results,
    }
    _write_json(REPORT_PATH, summary)


# ---------------------------------------------------------------------------
# Command dispatch
# ---------------------------------------------------------------------------


def cmd_check(args: argparse.Namespace) -> int:
    manifest = _load_json(WATCH_PATH)
    schema_errors = _validate_schema(manifest)

    try:
        regulations, _ = _load_known_regulations()
    except FileNotFoundError as exc:
        print(f"[change-watch] {exc}", file=sys.stderr)
        return 2

    ingest = _load_ingest_manifest()
    mitre_allow = ["mitre-attack-enterprise", "d3fend"]
    xref_errors = _cross_reference_errors(manifest, regulations, ingest, mitre_allow)
    stale_errors, stale_warnings = _staleness_findings(manifest)

    total = len(manifest["watchlist"])
    print("=== Regulatory change-watch audit ===")
    print(f"Baseline commit : {manifest.get('baselineCommit','?')}")
    print(f"Watched total   : {total}")
    if stale_warnings:
        print("")
        print(f"=== WARNINGS ({len(stale_warnings)}) ===")
        for w in stale_warnings:
            print(f"  {w}")

    errors = schema_errors + xref_errors + stale_errors
    if errors:
        print("")
        print(f"=== ERRORS ({len(errors)}) ===")
        for err in errors:
            print(f"  {err}")
        print("")
        print("=== CHANGE-WATCH GATE: FAIL ===")
        return 1
    print("")
    print("=== CHANGE-WATCH GATE: GREEN ===")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    manifest = _load_json(WATCH_PATH)
    schema_errors = _validate_schema(manifest)
    if schema_errors:
        print("[change-watch] refusing to fetch: watch manifest fails schema:", file=sys.stderr)
        for err in schema_errors:
            print(f"  {err}", file=sys.stderr)
        return 2
    ingest = _load_ingest_manifest()

    results: List[Dict[str, Any]] = []
    for entry in manifest["watchlist"]:
        result = _fetch_one(entry, ingest)
        results.append(result)

    _apply_fetch_results(manifest, results)
    _write_json(WATCH_PATH, manifest)
    _write_report(manifest, results)

    changed = [r for r in results if r.get("changed")]
    errors = [r for r in results if r.get("error")]

    print("=== Regulatory change-watch fetch ===")
    print(f"Watched total   : {len(results)}")
    print(f"Changed entries : {len(changed)}")
    print(f"Fetch errors    : {len(errors)}")
    for r in results:
        status = "CHANGED" if r.get("changed") else ("ERROR" if r.get("error") else "stable")
        summary = r.get("summary") or r.get("error") or ""
        print(f"  {status:<8}  {r['regulationId']:<30}  {summary}")
    return 1 if errors and args.strict else 0


def cmd_freeze(args: argparse.Namespace) -> int:
    manifest = _load_json(WATCH_PATH)
    now = _now_utc().isoformat().replace("+00:00", "Z")
    for entry in manifest["watchlist"]:
        entry["lastCheckedAt"] = now
        entry.pop("openFinding", None)
    manifest["generatedAt"] = now
    _write_json(WATCH_PATH, manifest)
    print(f"[change-watch] froze {len(manifest['watchlist'])} entries at {now}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Regulatory change-watch audit (Phase 5.3).")
    sub = parser.add_subparsers(dest="mode")

    check_p = sub.add_parser("check", help="hermetic CI gate (default)")
    check_p.set_defaults(func=cmd_check)

    fetch_p = sub.add_parser("fetch", help="network probe; update manifest")
    fetch_p.add_argument("--strict", action="store_true", help="fail if any fetch errors occur")
    fetch_p.set_defaults(func=cmd_fetch)

    freeze_p = sub.add_parser("freeze", help="stamp lastCheckedAt=now for every entry")
    freeze_p.set_defaults(func=cmd_freeze)

    parser.add_argument("--check", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--fetch", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--freeze", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--strict", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)

    if args.fetch:
        return cmd_fetch(args)
    if args.freeze:
        return cmd_freeze(args)
    if args.check or args.mode is None:
        return cmd_check(args)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
