#!/usr/bin/env python3
"""Validate top-level structure and required keys in catalog.json (stdlib only).

Abbreviated UC fields in this repo (see build.py / _schema_url):
  i = UC id, n = title, c = criticality, f = difficulty
  t = App/TA, d = data sources (not validated as required here beyond key presence
  when enforcing the full template from the parser).
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(REPO_ROOT, "catalog.json")

REQUIRED_TOP_LEVEL = (
    "_schema_url",
    "_readme",
    "DATA",
    "CAT_META",
    "CAT_GROUPS",
    "EQUIPMENT",
)

UC_ID_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
CAT_META_KEY_PATTERN = re.compile(r"^[0-9]+$")


def err(issues: List[str], msg: str) -> None:
    issues.append(msg)


def is_int(x: Any) -> bool:
    return type(x) is int


def is_str(x: Any) -> bool:
    return type(x) is str


def main() -> int:
    issues: List[str] = []

    if not os.path.isfile(CATALOG_PATH):
        print(f"ERROR: catalog not found: {CATALOG_PATH}", file=sys.stderr)
        return 1

    try:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            root = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(root, dict):
        err(issues, "Root JSON value must be an object")
        _print_issues(issues)
        return 1

    for key in REQUIRED_TOP_LEVEL:
        if key not in root:
            err(issues, f"Missing top-level key: {key!r}")

    data = root.get("DATA")
    if data is not None and not isinstance(data, list):
        err(issues, "DATA must be a list")

    cat_meta = root.get("CAT_META")
    if cat_meta is not None:
        if not isinstance(cat_meta, dict):
            err(issues, "CAT_META must be a dict")
        else:
            for mk in cat_meta:
                if not isinstance(mk, str) or not CAT_META_KEY_PATTERN.match(mk):
                    err(issues, f"CAT_META has invalid key (expected numeric string): {mk!r}")

    cat_groups = root.get("CAT_GROUPS")
    if cat_groups is not None and not isinstance(cat_groups, dict):
        err(issues, "CAT_GROUPS must be a dict")

    equipment = root.get("EQUIPMENT")
    if equipment is not None and not isinstance(equipment, list):
        err(issues, "EQUIPMENT must be a list")

    total_subcategories = 0
    total_ucs = 0
    data_category_ids: List[int] = []

    if isinstance(data, list):
        for ci, cat in enumerate(data):
            prefix = f"DATA[{ci}]"
            if not isinstance(cat, dict):
                err(issues, f"{prefix}: category entry must be an object")
                continue

            if "i" not in cat:
                err(issues, f"{prefix}: missing required key 'i' (category id, int)")
            elif not is_int(cat["i"]):
                err(issues, f"{prefix}: 'i' must be int, got {type(cat['i']).__name__}")
            else:
                data_category_ids.append(cat["i"])

            if "n" not in cat:
                err(issues, f"{prefix}: missing required key 'n' (category name, string)")
            elif not is_str(cat["n"]):
                err(issues, f"{prefix}: 'n' must be str, got {type(cat['n']).__name__}")

            subs = cat.get("s")
            if "s" not in cat:
                err(issues, f"{prefix}: missing required key 's' (subcategories list)")
            elif not isinstance(subs, list):
                err(issues, f"{prefix}: 's' must be a list")
            else:
                for si, sub in enumerate(subs):
                    sp = f"{prefix}.s[{si}]"
                    if not isinstance(sub, dict):
                        err(issues, f"{sp}: subcategory must be an object")
                        continue
                    if "i" not in sub:
                        err(issues, f"{sp}: missing required key 'i' (subcategory id)")
                    elif not is_str(sub["i"]):
                        err(issues, f"{sp}: 'i' must be str, got {type(sub['i']).__name__}")
                    if "n" not in sub:
                        err(issues, f"{sp}: missing required key 'n' (subcategory name)")
                    elif not is_str(sub["n"]):
                        err(issues, f"{sp}: 'n' must be str, got {type(sub['n']).__name__}")
                    ucs = sub.get("u")
                    if "u" not in sub:
                        err(issues, f"{sp}: missing required key 'u' (use cases list)")
                    elif not isinstance(ucs, list):
                        err(issues, f"{sp}: 'u' must be a list")
                    else:
                        total_subcategories += 1
                        for ui, uc in enumerate(ucs):
                            up = f"{sp}.u[{ui}]"
                            if not isinstance(uc, dict):
                                err(issues, f"{up}: use case must be an object")
                                continue
                            total_ucs += 1
                            for req, desc in (
                                ("i", "UC id (string, pattern X.Y.Z)"),
                                ("n", "title"),
                                ("c", "criticality"),
                                ("f", "difficulty"),
                            ):
                                if req not in uc:
                                    err(issues, f"{up}: missing required key {req!r} ({desc})")
                                elif req == "i":
                                    if not is_str(uc["i"]):
                                        err(
                                            issues,
                                            f"{up}: 'i' must be str, got {type(uc['i']).__name__}",
                                        )
                                    elif not UC_ID_PATTERN.match(uc["i"]):
                                        err(
                                            issues,
                                            f"{up}: UC id {uc['i']!r} must match pattern "
                                            r"^\d+\.\d+\.\d+$",
                                        )
                                elif not is_str(uc[req]):
                                    err(
                                        issues,
                                        f"{up}: {req!r} must be str, got {type(uc[req]).__name__}",
                                    )

            if "u" in cat:
                err(
                    issues,
                    f"{prefix}: unexpected top-level 'u' on category (UCs belong under "
                    f"each subcategory's 'u' list)",
                )

    if isinstance(cat_meta, dict) and data_category_ids:
        meta_keys = set(cat_meta.keys())
        data_keys = {str(i) for i in data_category_ids}
        missing_meta = sorted(data_keys - meta_keys, key=lambda x: int(x))
        extra_meta = sorted(meta_keys - data_keys, key=lambda x: int(x))
        if missing_meta:
            err(
                issues,
                "CAT_META missing entries for category id(s): " + ", ".join(missing_meta),
            )
        if extra_meta:
            err(
                issues,
                "CAT_META has keys not present in DATA category id(s): "
                + ", ".join(extra_meta),
            )

    if issues:
        _print_issues(issues)
        return 1

    n_cats = len(data) if isinstance(data, list) else 0
    print("catalog.json schema OK")
    print(f"  Categories:     {n_cats}")
    print(f"  Subcategories: {total_subcategories}")
    print(f"  Use cases:     {total_ucs}")
    return 0


def _print_issues(issues: List[str]) -> None:
    for line in issues:
        print(line, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
