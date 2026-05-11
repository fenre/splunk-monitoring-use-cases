#!/usr/bin/env python3
"""Apply mechanical fixes for the Meraki bug classes the linter detects.

Bug classes handled:

  S1  meraki:assurancealerts deviceType="wireless|switch|appliance|camera|sensor|cellular*|campusGateway"
      -> uppercase model code (MR / MS / MX / MV / MT / MG)

  S2  short flat field names on assurancealerts
        deviceSerial  -> scope.devices{}.serial
        deviceName    -> scope.devices{}.name
        networkName   -> network.name
        networkId     -> network.id   (only when no network.id is already in the SPL)

  S3  isnull(dismissedAt) / isnull(dismissed_at) on assurancealerts
      -> search dismissedAt="null" guard, with the SPL stripping the
         where clause that referenced isnull. (Conservative: we only
         replace the exact `| where isnull(dismissed*)`. Other shapes
         are left for human review and the linter will keep flagging them.)

  N1  SPL targets sourcetype="meraki" (SC4S syslog) but `app` only
      mentions Splunk_TA_cisco_meraki / Splunkbase 5580. Append SC4S
      to the `app` field.

  N2  Same as N1, plus `dataSources` doesn't mention SC4S.
      Append SC4S to both `app` and `dataSources`.

  T1  SC4S sourcetype="meraki" SPL combines outer `type=events` with
      `type=<wireless_subtype>`. The two are mutually exclusive on the
      same single-valued field. Strip the `type=` prefix from the inner
      wireless subtypes so they become raw-text matches inside the
      surrounding parens.
        type=events (type=8021x_eap_failure OR type=wpa_deauth)
        -> type=events ("8021x_eap_failure" OR "wpa_deauth")

  T2  Wireless subtype used as outer `type=` field with no `type=events`
      anchor. Same root cause as T1. Replace `type=<sub>` with
      `type=events "<sub>"` so the outer program tag is correct AND the
      inner subtype is matched in the raw body.

  T3  `signature=...` on SC4S sourcetype="meraki". Strip the
      `signature=` prefix and quote the value as a raw text match.
      Wildcards (`*Rogue*`) are kept; bareword tokens become raw text
      matches.

Usage:
    python3 scripts/_meraki_fix.py            # apply changes in place
    python3 scripts/_meraki_fix.py --dry-run  # show diffs only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PRODUCT_TYPE_TO_MODEL = {
    "wireless": "MR",
    "switch":   "MS",
    "appliance": "MX",
    "camera":   "MV",
    "sensor":   "MT",
    "cellular": "MG",
    "cellulargateway": "MG",
    "campusgateway":   "MG",
}

# Marker fragments we append, idempotently.
SC4S_APP_NOTE = (
    " | Optional alternate path: Splunk Connect for Syslog (SC4S) "
    "with the Meraki vendor pack ingests Meraki MX/MS/MR appliance "
    "syslog as sourcetype=\"meraki\" (does not require the API TA)."
)
SC4S_DS_NOTE = (
    " | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki "
    "vendor pack — points the Meraki dashboard at an SC4S receiver "
    "and produces sourcetype=\"meraki\" syslog events (free-form text "
    "extracted with rex). Use when you don't want to deploy the polling API TA."
)

SC4S_KEYWORDS = re.compile(r"\bSC4S\b|\bSplunk Connect for Syslog\b", re.IGNORECASE)


def fix_spl_assurance(text: str) -> tuple[str, list[str]]:
    """Apply S1/S2/S3 substitutions to a single SPL/prose string."""
    notes: list[str] = []
    new = text

    # S1 — lowercase product type -> uppercase model code
    def s1_repl(m: re.Match[str]) -> str:
        kind = m.group(1).lower()
        code = PRODUCT_TYPE_TO_MODEL.get(kind, kind)
        notes.append(f'S1 deviceType="{m.group(1)}" -> "{code}"')
        return f'deviceType="{code}"'

    new = re.sub(
        r'deviceType\s*=\s*"(wireless|switch|appliance|camera|sensor|cellular|cellularGateway|campusGateway)"',
        s1_repl,
        new,
        flags=re.IGNORECASE,
    )

    # S2 — flat names -> nested paths.
    s2_pairs = [
        (r'\bdeviceSerial\b', "scope.devices{}.serial", "S2 deviceSerial"),
        (r'\bdeviceName\b',   "scope.devices{}.name",   "S2 deviceName"),
        (r'\bnetworkName\b',  "network.name",            "S2 networkName"),
    ]
    for pattern, replacement, label in s2_pairs:
        if re.search(pattern, new):
            new = re.sub(pattern, replacement, new)
            notes.append(f"{label} -> {replacement}")

    # networkId is more delicate: only replace when network.id isn't already used
    # AND the SPL block in question is targeting meraki:assurancealerts.
    if re.search(r'sourcetype\s*=\s*"?meraki:assurancealerts"?', new, re.IGNORECASE) and \
       re.search(r'\bnetworkId\b', new) and "network.id" not in new:
        new = re.sub(r'\bnetworkId\b', "network.id", new)
        notes.append("S2 networkId -> network.id")

    # S3 — replace `isnull(<field>)` with `<field>="null"` in place, leaving
    # the surrounding `| where ... AND ... | ...` structure intact. The
    # dismissedAt field carries the literal STRING "null" while open, so
    # the equality check is the correct expression.
    s3_count = 0

    def s3_inplace(m: re.Match[str]) -> str:
        nonlocal s3_count
        s3_count += 1
        return f'{m.group(1)}="null"'

    new = re.sub(
        r'isnull\(\s*(dismissed\w*)\s*\)',
        s3_inplace,
        new,
        flags=re.IGNORECASE,
    )
    if s3_count:
        notes.append(f'S3 isnull(dismissed*) -> dismissed*="null" (x{s3_count})')

    return new, notes


def add_sc4s_to_app(app: str) -> str:
    if SC4S_KEYWORDS.search(app):
        return app
    return (app.rstrip() + SC4S_APP_NOTE).strip()


def add_sc4s_to_data_sources(ds: str) -> str:
    if SC4S_KEYWORDS.search(ds):
        return ds
    return (ds.rstrip() + SC4S_DS_NOTE).strip()


SC4S_WIRELESS_SUBTYPES = (
    "8021x_eap_failure", "8021x_deauth", "8021x_eap_success",
    "wpa_deauth", "wpa_auth", "disassociation", "association",
    "splash_auth", "airmarshal_events", "vpn_connectivity_change",
)


def fix_spl_sc4s(text: str) -> tuple[str, list[str]]:
    """Apply T1/T2/T3 substitutions on SC4S sourcetype=\"meraki\" SPL."""
    notes: list[str] = []
    new = text

    # T1 / T2 — strip `type=` prefix from inner wireless subtypes.
    # Only fires when the SPL targets sourcetype="meraki" (SC4S, not API TA).
    if not re.search(r'sourcetype\s*=\s*"?meraki"?(?!\:)', new):
        return new, notes

    has_outer_events = bool(re.search(r'\btype\s*=\s*"?events"?', new))

    for sub in SC4S_WIRELESS_SUBTYPES:
        pattern = rf'\btype\s*=\s*"?{re.escape(sub)}"?'
        if not re.search(pattern, new):
            continue
        if has_outer_events:
            # T1: just convert `type=<sub>` -> `"<sub>"` (raw-text match).
            new = re.sub(pattern, f'"{sub}"', new)
            notes.append(f'T1 type={sub} -> "{sub}" (inner raw-text match)')
        else:
            # T2: replace `type=<sub>` with `type=events "<sub>"` so we get
            # both the correct outer program tag and the inner content match.
            new = re.sub(pattern, f'type=events "{sub}"', new)
            has_outer_events = True
            notes.append(f'T2 type={sub} -> type=events "{sub}"')

    # T3 — strip `signature=...` prefix and quote the value as raw text.
    def t3_repl(m: re.Match[str]) -> str:
        val = m.group(1).strip('"\'')
        return f'"{val}"'

    if re.search(r'\bsignature\s*=\s*"?\*?[\w*-]+\*?"?', new):
        new2 = re.sub(r'\bsignature\s*=\s*("?\*?[\w*-]+\*?"?)', t3_repl, new)
        if new2 != new:
            notes.append("T3 signature=<v> -> raw-text match")
            new = new2

    return new, notes


def fix_uc(payload: dict, codes: set[str]) -> tuple[dict, list[str]]:
    """Return (payload, change-log)."""
    changes: list[str] = []

    # S1/S2/S3 — only meaningful when assurancealerts is in the SPL.
    if codes & {"S1", "S2", "S3"}:
        for field in ("spl", "qs", "implementation", "detailedImplementation"):
            v = payload.get(field) or ""
            if not v:
                continue
            new, notes = fix_spl_assurance(v)
            if new != v:
                payload[field] = new
                for n in notes:
                    changes.append(f"{field}: {n}")

    # T1/T2/T3 — SC4S syslog sourcetype="meraki" SPL fixes.
    if codes & {"T1", "T2", "T3"}:
        for field in ("spl", "qs", "implementation", "detailedImplementation"):
            v = payload.get(field) or ""
            if not v:
                continue
            new, notes = fix_spl_sc4s(v)
            if new != v:
                payload[field] = new
                for n in notes:
                    changes.append(f"{field}: {n}")

    # N1 — augment `app`.
    if codes & {"N1", "N2"}:
        new_app = add_sc4s_to_app(payload.get("app", "") or "")
        if new_app != (payload.get("app", "") or ""):
            payload["app"] = new_app
            changes.append("app: added SC4S alternate-path note")

    # N2 — also augment `dataSources`.
    if "N2" in codes:
        new_ds = add_sc4s_to_data_sources(payload.get("dataSources", "") or "")
        if new_ds != (payload.get("dataSources", "") or ""):
            payload["dataSources"] = new_ds
            changes.append("dataSources: added SC4S alternate-path note")

    return payload, changes


def codes_for(findings: list[dict]) -> set[str]:
    return {f["code"] for f in findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="don't write, just report what would change")
    parser.add_argument("--only", action="append",
                        help="UC id (e.g. 5.1.42) — limit fixes to these (repeatable)")
    args = parser.parse_args()

    sys.path.insert(0, str(REPO / "scripts"))
    sys.path.insert(0, str(REPO))
    from _meraki_lint import lint_uc, is_meraki_uc  # type: ignore

    only = set(args.only or [])

    modified: list[tuple[Path, list[str]]] = []
    for path in sorted((REPO / "content").glob("cat-*/UC-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not is_meraki_uc(payload):
            continue
        if only and payload.get("id") not in only:
            continue
        findings = lint_uc(payload)
        if not findings:
            continue
        codes = codes_for(findings)
        payload, changes = fix_uc(payload, codes)
        if not changes:
            continue
        modified.append((path, changes))
        if not args.dry_run:
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{'Would modify' if args.dry_run else 'Modified'} {len(modified)} files")
    for path, changes in modified:
        print(f"\n  {path.relative_to(REPO)}")
        for c in changes:
            print(f"    - {c}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
