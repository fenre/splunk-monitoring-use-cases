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
a ``splVariants`` search must be on the list.

Run::

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


def findings(official: set[str] | None = None) -> list[str]:
    """One line per use case and unofficial Cisco sourcetype."""
    allowed = official if official is not None else load_official()
    lines: list[str] = []
    for _path, sidecar in iter_uc_sidecars():
        uc_id = str(sidecar.get("id") or "")
        for token in unofficial_sourcetypes(sidecar, allowed):
            lines.append(f"UC-{uc_id} sourcetype={token}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when a search names a Cisco sourcetype outside the official list.",
    )
    args = parser.parse_args(argv)
    if not args.check:
        parser.print_help()
        return 2
    try:
        rows = findings()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Cisco sourcetype list: {exc}", file=sys.stderr)
        return 1
    if rows:
        print(f"Cisco sourcetype list: {len(rows)} unofficial sourcetype uses:")
        for line in rows[:40]:
            print(f"  {line}")
        if len(rows) > 40:
            print(f"  … {len(rows) - 40} more")
        return 1
    print(f"Cisco sourcetype list check passed ({len(load_official())} official sourcetypes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
