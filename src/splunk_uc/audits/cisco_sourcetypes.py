#!/usr/bin/env python3
"""Fail when a search names a Cisco sourcetype that Splunk does not list.

The allowed set is ``data/cisco-sourcetypes.json``, copied from Splunk's
Integrated Enterprise Value supported-sourcetype table. A sourcetype is
treated as Cisco when it is on that list or uses a Cisco product prefix
(``cisco:``, ``meraki:``, ``webex:``, ``duo:``, and the other prefixes
recorded in this module).

Use cases with ``splStatus`` ``example`` may keep unofficial sourcetypes
for ACI, UCS, Intersight, SD-WAN, Webex, and Spaces. Those products have
no sample events in the add-on package, so their searches are
illustrations. Every other Cisco sourcetype in ``spl``, ``cimSpl``, or
a ``splVariants`` search must be on the list or in the backlog.

``data/cisco-sourcetype-backlog.json`` lists the use-case and sourcetype
pairs that already fail. The list may only shrink: ``--check`` fails on
a hit that is not listed and on a listed pair that no longer fails.

Run::

    PYTHONPATH=src python3 -m splunk_uc audit-cisco-sourcetypes
    PYTHONPATH=src python3 -m splunk_uc audit-cisco-sourcetypes --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import iter_uc_sidecars
from splunk_uc.equipment_evidence import extract_spl_evidence

REPO_ROOT = Path(__file__).resolve().parents[3]
LIST_PATH = REPO_ROOT / "data" / "cisco-sourcetypes.json"
BACKLOG = REPO_ROOT / "data" / "cisco-sourcetype-backlog.json"

# Prefixes that identify a Cisco-product sourcetype even when the token
# is not on the supported list. ``meraki`` without a colon is the
# literal official value, matched separately.
_CISCO_PREFIXES = (
    "cisco:",
    "cisco_",
    "cisco-",
    "meraki:",
    "meraki_",
    "webex:",
    "duo:",
    "umbrella:",
    "opendns:",
    "stealthwatch:",
    "viptela",
    "talos:",
    "firesight:",
    "estreamer",
    "snort",
    "sourcefire",
    "ciscocloud",
    "ciscosecurity",
    "ciscothousandeyes",
    "switch_cisco",
    "ta_cisco",
)

# Unofficial names that splStatus=example is allowed to keep. Official
# names in these families still have to be on the list; the exemption
# only covers names the list does not contain.
_EXAMPLE_PREFIXES = (
    "cisco:aci",
    "cisco:dc:aci",
    "cisco:ucs",
    "ta_cisco_ucs",
    "cisco:intersight",
    "cisco:sdwan",
    "viptela",
    "cisco:webex",
    "webex:",
    "cisco:spaces",
)


def load_official(path: Path | None = None) -> set[str]:
    """Return the lowercased supported sourcetypes."""
    payload = json.loads((path or LIST_PATH).read_text(encoding="utf-8"))
    found: set[str] = set()
    products = payload.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError(f"{path or LIST_PATH} has no products")
    for product in products:
        if not isinstance(product, dict):
            raise ValueError("product entry is not an object")
        sourcetypes = product.get("sourcetypes")
        if not isinstance(sourcetypes, list) or not sourcetypes:
            raise ValueError(f"product {product.get('product')!r} has no sourcetypes")
        for raw in sourcetypes:
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError("sourcetype entries must be non-empty strings")
            found.add(raw.strip().lower())
    return found


def is_cisco_sourcetype(sourcetype: str, official: set[str]) -> bool:
    """True when the token is a Cisco product sourcetype."""
    token = sourcetype.lower()
    if token in official or token == "meraki":
        return True
    return token.startswith(_CISCO_PREFIXES)


def _example_family(sourcetype: str) -> bool:
    return sourcetype.lower().startswith(_EXAMPLE_PREFIXES)


def _search_texts(sidecar: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in ("spl", "cimSpl"):
        value = sidecar.get(key)
        if isinstance(value, str) and value.strip():
            texts.append(value)
    variants = sidecar.get("splVariants")
    if isinstance(variants, list):
        for item in variants:
            if not isinstance(item, dict):
                continue
            for key in ("spl", "cimSpl"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    texts.append(value)
    return texts


def unofficial_sourcetypes(sidecar: dict[str, Any], official: set[str]) -> list[str]:
    """Cisco sourcetypes named by this use case that are not on the list."""
    named = extract_spl_evidence(*_search_texts(sidecar)).sourcetypes
    example = sidecar.get("splStatus") == "example"
    bad: list[str] = []
    for token in sorted(named):
        if token in official or not is_cisco_sourcetype(token, official):
            continue
        if example and _example_family(token):
            continue
        bad.append(token)
    return bad


def collect(official: set[str] | None = None) -> list[dict[str, str]]:
    """One row per use case and unofficial Cisco sourcetype."""
    allowed = official if official is not None else load_official()
    rows: list[dict[str, str]] = []
    for _path, sidecar in iter_uc_sidecars():
        uc_id = f"UC-{sidecar.get('id')}"
        title = str(sidecar.get("title") or "")
        for token in unofficial_sourcetypes(sidecar, allowed):
            rows.append({"id": uc_id, "title": title, "sourcetype": token})
    rows.sort(key=lambda row: (row["id"], row["sourcetype"]))
    return rows


def load_backlog(path: Path | None = None) -> set[tuple[str, str]]:
    """Return ``(UC id, sourcetype)`` pairs the backlog already accepts."""
    data = json.loads((path or BACKLOG).read_text(encoding="utf-8"))
    return {(entry["id"], entry["sourcetype"]) for entry in data.get("useCases", [])}


def compare(
    current: list[dict[str, str]], backlog: set[tuple[str, str]]
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (new hits not in the backlog, backlog entries that no longer hit)."""
    keys = {(row["id"], row["sourcetype"]) for row in current}
    new = sorted(keys - backlog)
    stale = sorted(backlog - keys)
    return new, stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail on an unlisted unofficial sourcetype or a backlog entry that is gone.",
    )
    args = parser.parse_args(argv)
    try:
        rows = collect()
        backlog = load_backlog()
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"Cisco sourcetype list: {exc}", file=sys.stderr)
        return 1
    new, stale = compare(rows, backlog)
    ucs = {row["id"] for row in rows}
    print(
        f"Cisco sourcetype list: {len(rows)} unofficial uses "
        f"in {len(ucs)} use cases ({len(backlog)} in backlog)"
    )
    for uc_id, sourcetype in new[:40]:
        print(f"  NEW   {uc_id} sourcetype={sourcetype}")
    if len(new) > 40:
        print(f"  ... {len(new) - 40} more new uses")
    for uc_id, sourcetype in stale[:40]:
        print(f"  STALE {uc_id} sourcetype={sourcetype}")
    if len(stale) > 40:
        print(f"  ... {len(stale) - 40} more stale backlog entries")
    if args.check and (new or stale):
        print(
            "FAIL: a search names a Cisco sourcetype outside the official list, "
            f"or a backlog entry no longer fails. See {BACKLOG.relative_to(REPO_ROOT)}."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
