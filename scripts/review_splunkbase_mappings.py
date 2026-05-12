#!/usr/bin/env python3
"""SME review helper for the v9.0 ``splunkbaseApps[]`` migration.

Companion to ``python3 -m splunk_uc generate-splunkbase-mappings``. The migration
generator proposes a ``splunkbaseApps[]`` array for every UC, flagging each
entry with ``requiresSmeReview: true``. This script supports the human
review pass that clears those flags. Process documented in
[``docs/splunkbase-review-guide.md``](../docs/splunkbase-review-guide.md).

Subcommands::

    review_splunkbase_mappings.py list
    review_splunkbase_mappings.py list --equipment cisco-meraki
    review_splunkbase_mappings.py signoff --equipment cisco-meraki \
        --reviewer "Pat Smith (Splunk PS)" --pr "#1234"
    review_splunkbase_mappings.py signoff --uc 1.1.1 1.1.2 \
        --reviewer "..." --pr "#1234"

The signoff command:
- Removes ``requiresSmeReview`` from every entry in the batch's UC sidecars.
- Appends a record to
  ``data/provenance/splunkbase-mappings-signoffs.json`` capturing
  reviewer + PR + commit SHA + scope.

We never auto-modify any UC outside the explicit batch, and we never write
to UCs whose ``splunkbaseApps[]`` is missing or empty.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
LEDGER_PATH = REPO_ROOT / "data" / "provenance" / "splunkbase-mappings-signoffs.json"
UC_FILE_GLOB = "cat-*/UC-*.json"

UC_ID_RE = re.compile(r"^\d+\.\d+\.\d+$")


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _read_uc(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_uc(path: pathlib.Path, body: Dict[str, Any]) -> None:
    payload = json.dumps(body, indent=2, ensure_ascii=False) + "\n"
    path.write_text(payload, encoding="utf-8")


def _read_ledger() -> Dict[str, Any]:
    if not LEDGER_PATH.exists():
        return {
            "schemaVersion": 1,
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "documentation": "docs/splunkbase-review-guide.md",
            "signoffs": [],
        }
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _write_ledger(body: Dict[str, Any]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    LEDGER_PATH.write_text(serialised, encoding="utf-8")


def _git_head_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


# ---------------------------------------------------------------------------
# UC discovery
# ---------------------------------------------------------------------------


def _all_ucs() -> List[pathlib.Path]:
    return sorted(CONTENT_DIR.glob(UC_FILE_GLOB))


def _open_review_entries(uc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the ``splunkbaseApps[]`` entries that still need SME review."""
    entries = uc.get("splunkbaseApps")
    if not isinstance(entries, list):
        return []
    return [e for e in entries if isinstance(e, dict) and e.get("requiresSmeReview")]


def _filter_ucs(
    *,
    equipment: Optional[str],
    uc_ids: Iterable[str],
) -> List[pathlib.Path]:
    wanted_ids: Set[str] = {uid.removeprefix("UC-") for uid in uc_ids}

    out: List[pathlib.Path] = []
    for path in _all_ucs():
        try:
            uc = _read_uc(path)
        except (OSError, json.JSONDecodeError):
            continue
        if wanted_ids and str(uc.get("id")) not in wanted_ids:
            continue
        if equipment:
            slugs = [s for s in (uc.get("equipment") or []) if isinstance(s, str)]
            if equipment not in slugs:
                continue
        out.append(path)
    return out


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> int:
    paths = _filter_ucs(equipment=args.equipment, uc_ids=args.uc or [])
    by_equipment: Dict[str, List[Tuple[str, int]]] = {}
    no_equipment: List[Tuple[str, int]] = []
    total_open_entries = 0
    total_open_ucs = 0

    for path in paths:
        try:
            uc = _read_uc(path)
        except (OSError, json.JSONDecodeError) as err:
            print(f"[review_splunkbase_mappings] {path}: {err}", file=sys.stderr)
            continue
        open_entries = _open_review_entries(uc)
        if not open_entries:
            continue
        total_open_ucs += 1
        total_open_entries += len(open_entries)
        slugs = [s for s in (uc.get("equipment") or []) if isinstance(s, str)]
        record = (str(uc.get("id")), len(open_entries))
        if not slugs:
            no_equipment.append(record)
            continue
        for slug in slugs:
            by_equipment.setdefault(slug, []).append(record)

    if args.equipment:
        bucket = by_equipment.get(args.equipment, [])
        print(
            f"[review_splunkbase_mappings] equipment={args.equipment} "
            f"open_ucs={len(bucket)} open_entries={sum(c for _, c in bucket)}"
        )
        for uc_id, count in sorted(bucket):
            print(f"  UC-{uc_id}\t{count} entries")
        return 0

    print(
        f"[review_splunkbase_mappings] open backlog: "
        f"{total_open_ucs} UCs, {total_open_entries} entries across "
        f"{len(by_equipment)} equipment slugs"
    )
    for slug in sorted(by_equipment):
        bucket = by_equipment[slug]
        print(f"  {slug:<28}\t{len(bucket)} UCs\t{sum(c for _, c in bucket)} entries")
    if no_equipment:
        print(
            f"  (no equipment slug)        \t{len(no_equipment)} UCs\t"
            f"{sum(c for _, c in no_equipment)} entries"
        )
    return 0


# ---------------------------------------------------------------------------
# signoff
# ---------------------------------------------------------------------------


def _strip_review_flag(uc: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Remove ``requiresSmeReview`` from every entry. Returns ``(new_uc, count)``."""
    cleared = 0
    new_entries: List[Dict[str, Any]] = []
    for raw in uc.get("splunkbaseApps") or []:
        if not isinstance(raw, dict):
            new_entries.append(raw)
            continue
        if raw.get("requiresSmeReview"):
            cleared += 1
            new_raw = {k: v for k, v in raw.items() if k != "requiresSmeReview"}
            new_entries.append(new_raw)
        else:
            new_entries.append(raw)
    new_uc = dict(uc)
    new_uc["splunkbaseApps"] = new_entries
    return new_uc, cleared


def _validate_signoff_inputs(args: argparse.Namespace) -> List[str]:
    errors: List[str] = []
    if not args.equipment and not args.uc:
        errors.append("must pass --equipment <slug> or --uc <id ...>")
    if not args.reviewer or len(args.reviewer.strip()) < 2:
        errors.append("--reviewer is required (use 'Name (Firm/Role)')")
    if not args.pr or not (args.pr.startswith("#") or args.pr == "direct-commit"):
        errors.append("--pr must be '#<number>' or 'direct-commit'")
    for uid in args.uc or []:
        if not UC_ID_RE.match(uid.removeprefix("UC-")):
            errors.append(f"--uc {uid!r} is not a UC-X.Y.Z id")
    return errors


def cmd_signoff(args: argparse.Namespace) -> int:
    errors = _validate_signoff_inputs(args)
    if errors:
        for err in errors:
            print(f"[review_splunkbase_mappings] {err}", file=sys.stderr)
        return 2

    paths = _filter_ucs(equipment=args.equipment, uc_ids=args.uc or [])
    if not paths:
        print(
            "[review_splunkbase_mappings] no UCs matched the filter; nothing to sign off.",
            file=sys.stderr,
        )
        return 0

    cleared_total = 0
    cleared_ucs: List[str] = []
    for path in paths:
        try:
            uc = _read_uc(path)
        except (OSError, json.JSONDecodeError) as err:
            print(f"[review_splunkbase_mappings] {path}: {err}", file=sys.stderr)
            continue
        if not _open_review_entries(uc):
            continue
        new_uc, cleared = _strip_review_flag(uc)
        if cleared == 0:
            continue
        if not args.dry_run:
            _write_uc(path, new_uc)
        cleared_total += cleared
        cleared_ucs.append(str(uc.get("id")))

    if not cleared_total:
        print(
            "[review_splunkbase_mappings] no open review flags found in the batch; "
            "ledger not updated."
        )
        return 0

    if args.dry_run:
        print(
            f"[review_splunkbase_mappings] dry-run: would clear {cleared_total} entries "
            f"across {len(cleared_ucs)} UCs."
        )
        return 0

    ledger = _read_ledger()
    signoffs = ledger.setdefault("signoffs", [])
    signoffs.append(
        {
            "pr": args.pr,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "commit": _git_head_sha(),
            "reviewer": args.reviewer.strip(),
            "scope": {
                "equipment": args.equipment,
                "ucs": sorted(cleared_ucs),
            },
            "outcome": "approved",
            "entriesCleared": cleared_total,
        }
    )
    ledger["generatedAt"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    _write_ledger(ledger)
    print(
        f"[review_splunkbase_mappings] signed off {cleared_total} entries across "
        f"{len(cleared_ucs)} UCs; ledger updated."
    )
    return 0


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------


def cmd_audit(_: argparse.Namespace) -> int:
    total = 0
    with_apps = 0
    open_entries = 0
    open_ucs = 0
    fully_signed = 0
    for path in _all_ucs():
        try:
            uc = _read_uc(path)
        except (OSError, json.JSONDecodeError):
            continue
        total += 1
        entries = uc.get("splunkbaseApps")
        if not isinstance(entries, list) or not entries:
            continue
        with_apps += 1
        review_left = _open_review_entries(uc)
        if review_left:
            open_ucs += 1
            open_entries += len(review_left)
        else:
            fully_signed += 1
    print(
        f"[review_splunkbase_mappings] total_ucs={total} "
        f"with_splunkbaseApps={with_apps} "
        f"fully_signed={fully_signed} "
        f"awaiting_review={open_ucs} "
        f"open_entries={open_entries}"
    )
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subs = parser.add_subparsers(dest="cmd", required=True)

    p_list = subs.add_parser("list", help="Show open review backlog grouped by equipment.")
    p_list.add_argument("--equipment", help="Limit to a single equipment slug.")
    p_list.add_argument("--uc", nargs="*", help="Limit to specific UC ids.")

    p_signoff = subs.add_parser("signoff", help="Clear requiresSmeReview on a batch.")
    p_signoff.add_argument("--equipment", help="Sign off all UCs that carry this slug.")
    p_signoff.add_argument("--uc", nargs="*", help="Sign off specific UC ids.")
    p_signoff.add_argument("--reviewer", required=True, help="'Name (Firm/Role)'.")
    p_signoff.add_argument("--pr", required=True, help="'#1234' or 'direct-commit'.")
    p_signoff.add_argument("--dry-run", action="store_true")

    subs.add_parser("audit", help="Print review-coverage statistics.")

    args = parser.parse_args(argv)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "signoff":
        return cmd_signoff(args)
    if args.cmd == "audit":
        return cmd_audit(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
