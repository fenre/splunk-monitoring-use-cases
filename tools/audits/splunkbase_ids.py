#!/usr/bin/env python3
"""tools.audits.splunkbase_ids — verify every UC's splunkbaseApps[] id resolves.

Every numeric ``splunkbaseApps[].id`` referenced by a UC sidecar must exist in
``data/splunkbase-catalog.json`` (after applying ``data/splunkbase-catalog-overrides.json``).
The catalog is refreshed weekly by ``scripts/sync_splunkbase_catalog.py``; the
audit runs on every PR and exits non-zero when a UC names a Splunkbase id that
the cached catalog cannot resolve.

This is the hermetic counterpart to the Splunkbase-API liveness check. We
deliberately do NOT call splunkbase.splunk.com from CI on every PR — that
would burn the API budget and add a network dependency to every test run.
The weekly cron is the authoritative refresh; this audit only validates that
the cache is internally consistent with the corpus.

Usage
-----
    python3 tools/audits/splunkbase_ids.py
    python3 tools/audits/splunkbase_ids.py --json reports/splunkbase-ids.json

Exit codes
----------
0 — every referenced id resolves against the catalog.
1 — at least one id is missing (lists offenders on stderr).
2 — invocation error (catalog unreadable, content dir missing, etc.).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Tuple


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "content"
UC_FILE_GLOB = "cat-*/UC-*.json"
CATALOG_PATH = REPO_ROOT / "data" / "splunkbase-catalog.json"
OVERRIDES_PATH = REPO_ROOT / "data" / "splunkbase-catalog-overrides.json"


def _load_catalog() -> Dict[str, Dict[str, Any]]:
    if not CATALOG_PATH.exists():
        raise SystemExit(
            f"[splunkbase_ids] missing catalog file: {CATALOG_PATH.relative_to(REPO_ROOT)}"
        )
    base = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    overrides = (
        json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
        if OVERRIDES_PATH.exists()
        else {"apps": {}}
    )
    apps: Dict[str, Dict[str, Any]] = {}
    for key, entry in (base.get("apps") or {}).items():
        if isinstance(entry, dict):
            apps[str(key)] = dict(entry)
    for key, entry in (overrides.get("apps") or {}).items():
        if isinstance(entry, dict):
            if str(key) in apps:
                apps[str(key)].update(entry)
            else:
                apps[str(key)] = dict(entry)
    return apps


def _read_uc(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="splunkbase_ids")
    parser.add_argument(
        "--json",
        help="Optional path: write the offending-id breakdown as JSON.",
    )
    args = parser.parse_args(argv)

    if not CONTENT_DIR.is_dir():
        print(f"[splunkbase_ids] missing content dir: {CONTENT_DIR}", file=sys.stderr)
        return 2

    try:
        catalog = _load_catalog()
    except (OSError, json.JSONDecodeError) as err:
        print(f"[splunkbase_ids] catalog unreadable: {err}", file=sys.stderr)
        return 2

    catalog_ids = {int(k) for k in catalog if str(k).isdigit()}

    offenders: List[Tuple[str, List[Tuple[Any, str]]]] = []
    bad_url_examples: List[Tuple[str, str]] = []
    total_refs = 0
    total_ucs = 0

    for path in sorted(CONTENT_DIR.glob(UC_FILE_GLOB)):
        try:
            uc = _read_uc(path)
        except (OSError, json.JSONDecodeError) as err:
            print(f"[splunkbase_ids] {path}: {err}", file=sys.stderr)
            return 2

        entries = uc.get("splunkbaseApps")
        if not isinstance(entries, list) or not entries:
            continue
        total_ucs += 1
        local_offenders: List[Tuple[Any, str]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            total_refs += 1
            app_id = entry.get("id")
            if not isinstance(app_id, int) or app_id not in catalog_ids:
                local_offenders.append((app_id, "id missing from catalog"))
                continue
            url = entry.get("url")
            if isinstance(url, str) and url:
                expected_prefix = f"https://splunkbase.splunk.com/app/{app_id}"
                if not url.startswith(expected_prefix):
                    bad_url_examples.append(
                        (str(path.relative_to(REPO_ROOT)), f"id={app_id} url={url!r}")
                    )
        if local_offenders:
            offenders.append((str(path.relative_to(REPO_ROOT)), local_offenders))

    print(
        f"[splunkbase_ids] catalog_size={len(catalog_ids)} "
        f"ucs_with_apps={total_ucs} total_references={total_refs} "
        f"offending_ucs={len(offenders)}"
    )

    if args.json:
        out = {
            "catalogSize": len(catalog_ids),
            "ucsWithApps": total_ucs,
            "totalReferences": total_refs,
            "offendingUcs": [
                {
                    "uc": uc_path,
                    "offenders": [{"id": oid, "reason": reason} for oid, reason in errs],
                }
                for uc_path, errs in offenders
            ],
            "badUrlExamples": [
                {"uc": uc_path, "detail": detail} for uc_path, detail in bad_url_examples
            ],
        }
        out_path = pathlib.Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if offenders:
        for uc_path, errs in offenders[:10]:
            ids = ", ".join(f"{oid} ({reason})" for oid, reason in errs)
            print(f"[splunkbase_ids] {uc_path}: {ids}", file=sys.stderr)
        if len(offenders) > 10:
            print(
                f"[splunkbase_ids] ... and {len(offenders) - 10} more UCs reference unknown ids",
                file=sys.stderr,
            )
        return 1

    if bad_url_examples:
        for uc_path, detail in bad_url_examples[:5]:
            print(f"[splunkbase_ids] BAD URL {uc_path}: {detail}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
