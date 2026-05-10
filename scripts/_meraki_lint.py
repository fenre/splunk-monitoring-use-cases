#!/usr/bin/env python3
"""Meraki-aware SPL linter.

For every Meraki UC in content/, examine the SPL and flag bugs that would
make the query fail or return wrong/empty results on a real Splunk server
running Splunk_TA_cisco_meraki 3.3 + SC4S Meraki vendor pack.

Bug classes (each tied to a specific sourcetype's canonical field set):

  S1  meraki:assurancealerts uses lowercase product type
      e.g. deviceType="wireless"  -> should be deviceType="MR"
           deviceType="switch"    -> should be deviceType="MS"
           deviceType="appliance" -> should be deviceType="MX"
           deviceType="camera"    -> should be deviceType="MV"
           deviceType="sensor"    -> should be deviceType="MT"
           deviceType="cellular"  -> should be deviceType="MG"

  S2  meraki:assurancealerts uses short flat field names
      e.g. deviceSerial / deviceName / networkName / networkId
      -> should be scope.devices{}.serial / scope.devices{}.name /
                   network.name / network.id

  S3  any sourcetype: isnull(dismissed*) used as if dismissedAt were a
      real null; the field carries the literal STRING "null" — must use
      search dismissed_at="null" or eval ... = if(dismissed_at="null", ...)

  V1  meraki:appliancesdwanstatuses uses vpnPeers{} (wrong array name)
      -> should be merakiVpnPeers{}

  V2  meraki:appliancesdwanstatuses uses peerNetworkId / peerNetworkName
      -> should be just networkId / networkName (inside merakiVpnPeers struct)

  V3  meraki:appliancesdwanstatuses references usage.sent / usage.received
      -> those live on the SEPARATE meraki:appliancesdwanstatistics
         endpoint; on Statuses there are no per-peer byte counters.

  N1  SPL targets sourcetype="meraki" (SC4S syslog convention) but the UC
      `app` field claims only the API TA (Splunkbase 5580) without
      mentioning SC4S. Either rewrite SPL to use a meraki:<sub> sourcetype
      or add SC4S to `app`/`dataSources`.

  N2  SPL targets sourcetype="meraki" but the UC `dataSources` field
      doesn't even mention SC4S or syslog — the SPL refers to a data
      source the UC's prose never installs.

  D1  meraki:devices SPL uses scope.devices{}.serial / scope.devices{}.name
      (those are assurance-alerts paths; on meraki:devices the fields are
      flat: serial / name).

Usage:
    python3 scripts/_meraki_lint.py            # human report
    python3 scripts/_meraki_lint.py --json     # machine readable
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
MANIFEST_PATH = REPO / "scripts" / "_meraki_field_manifests.json"


# ---- helpers -------------------------------------------------------------

SOURCETYPE_RE = re.compile(r'sourcetype\s*=\s*"?(meraki[:\w-]*)"?', re.IGNORECASE)
INDEX_RE = re.compile(r'index\s*=\s*"?([\w*-]+)"?', re.IGNORECASE)


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


def referenced_sourcetypes(spl: str) -> set[str]:
    return {m.group(1) for m in SOURCETYPE_RE.finditer(spl or "")}


def is_meraki_uc(payload: dict) -> bool:
    blob = " ".join(
        str(payload.get(k, ""))
        for k in ("app", "dataSources", "spl", "implementation", "title", "description")
    ).lower()
    return ("meraki" in blob) or ("cisco_meraki" in blob)


# ---- bug detectors --------------------------------------------------------

def lint_uc(payload: dict) -> list[dict]:
    spl = payload.get("spl", "") or ""
    app = payload.get("app", "") or ""
    ds = payload.get("dataSources", "") or ""
    sts = referenced_sourcetypes(spl)
    findings: list[dict] = []

    # S1 / S2 / S3 — assurance alerts hallucinations
    if "meraki:assurancealerts" in sts:
        m = re.search(
            r'deviceType\s*=\s*"(wireless|switch|appliance|camera|sensor|cellular|cellularGateway|campusGateway)"',
            spl, re.IGNORECASE,
        )
        if m:
            real = PRODUCT_TYPE_TO_MODEL.get(m.group(1).lower(), "?")
            findings.append({
                "code": "S1",
                "msg": (f'meraki:assurancealerts uses deviceType="{m.group(1)}" '
                        f'(lowercase product type); real values are uppercase '
                        f'model codes like "MR/MS/MX/MV/MT/MG". Use deviceType="{real}".'),
            })
        for short, real in [
            ("deviceSerial", "scope.devices{}.serial"),
            ("deviceName",   "scope.devices{}.name"),
            ("networkName",  "network.name"),
        ]:
            if re.search(rf'\b{short}\b', spl):
                findings.append({
                    "code": "S2",
                    "msg": f"meraki:assurancealerts uses {short} (does not exist); use {real}.",
                })
        if re.search(r'\bnetworkId\b', spl) and "network.id" not in spl:
            findings.append({
                "code": "S2",
                "msg": "meraki:assurancealerts uses flat networkId; use network.id (the TA preserves Meraki's nested JSON).",
            })
        if re.search(r'isnull\(\s*dismissed\w*\s*\)', spl, re.IGNORECASE):
            findings.append({
                "code": "S3",
                "msg": ('isnull(dismissed*) — dismissedAt carries the literal STRING "null" '
                        'while the alert is open, not a SQL/Splunk NULL. '
                        'Use search dismissedAt="null" or compare with eval.'),
            })

    # V1 / V2 / V3 — VPN statuses field hallucinations
    if "meraki:appliancesdwanstatuses" in sts:
        if re.search(r'\bvpnPeers\b', spl) and "merakiVpnPeers" not in spl:
            findings.append({
                "code": "V1",
                "msg": ("meraki:appliancesdwanstatuses uses vpnPeers{} (wrong array name); "
                        "the real Meraki API field is merakiVpnPeers{}."),
            })
        if re.search(r'\bpeerNetworkId\b|\bpeerNetworkName\b', spl):
            findings.append({
                "code": "V2",
                "msg": ("meraki:appliancesdwanstatuses uses peerNetworkId/peerNetworkName "
                        "(those don't exist); inside the merakiVpnPeers struct it is just "
                        "networkId/networkName."),
            })
        if re.search(r'usage\.(sent|received)', spl):
            findings.append({
                "code": "V3",
                "msg": ("meraki:appliancesdwanstatuses references usage.sent/usage.received; "
                        "per-peer byte counters live on the SEPARATE meraki:appliancesdwanstatistics "
                        "endpoint, not Statuses."),
            })

    # D1 — flat-field sourcetypes shouldn't use scope.devices{}.* paths.
    # Only flag when assurancealerts is NOT also referenced (because in
    # mixed-sourcetype pipelines the nested path legitimately belongs to
    # the assurancealerts subsearch and is usually renamed for join keys).
    flat_serial_sts = {
        "meraki:devices", "meraki:devicesavailabilities",
        "meraki:summarytopdevicesbyusage", "meraki:wirelessdevicesethernetstatuses",
        "meraki:devicesuplinksaddressesbydevice",
        "meraki:summarytopappliancesbyutilization",
    }
    if any(st in sts for st in flat_serial_sts) and "meraki:assurancealerts" not in sts:
        if re.search(r'scope\.devices\{\}\.serial', spl):
            findings.append({
                "code": "D1",
                "msg": (f"sourcetype {next(iter(flat_serial_sts & sts))} uses flat 'serial' "
                        "field; scope.devices{}.serial is an assurance-alerts path and won't match here."),
            })

    # N1 / N2 — narrative inconsistency between SPL sourcetype, app, and dataSources
    sc4s_in_spl = bool(re.search(r'sourcetype\s*=\s*"?meraki"?(?!\:)', spl))
    api_ta_in_app = (
        "5580" in app or
        "Cisco Meraki Add-on" in app or
        "Splunk_TA_cisco_meraki" in app
    )
    sc4s_in_app = bool(re.search(r"\bSC4S\b|\bSplunk Connect for Syslog\b", app, re.IGNORECASE))
    sc4s_in_ds = bool(re.search(r"\bSC4S\b|\bSplunk Connect for Syslog\b", ds, re.IGNORECASE))
    if sc4s_in_spl and api_ta_in_app and not sc4s_in_app and not sc4s_in_ds:
        findings.append({
            "code": "N2",
            "msg": ('SPL targets sourcetype="meraki" (SC4S syslog), but neither `app` nor '
                    '`dataSources` mentions SC4S. The query has no installable data path.'),
        })
    elif sc4s_in_spl and api_ta_in_app and not sc4s_in_app and sc4s_in_ds:
        findings.append({
            "code": "N1",
            "msg": ('SPL targets sourcetype="meraki" (SC4S syslog) and `dataSources` '
                    'mentions SC4S, but `app` only names the API TA (Splunkbase 5580). '
                    'A user installing only the named app will never see results.'),
        })

    return findings


# ---- driver --------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of human text")
    parser.add_argument("--check", action="store_true", help="exit 1 if any findings")
    args = parser.parse_args()

    records = []
    for path in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"PARSE-FAIL {path}: {exc}", file=sys.stderr)
            continue
        if not is_meraki_uc(payload):
            continue
        findings = lint_uc(payload)
        records.append({
            "path": str(path.relative_to(REPO)),
            "id": payload.get("id"),
            "title": payload.get("title"),
            "sourcetypes": sorted(referenced_sourcetypes(payload.get("spl", "") or "")),
            "findings": findings,
        })

    flagged = [r for r in records if r["findings"]]

    if args.json:
        print(json.dumps(records, indent=2))
    else:
        by_code: dict[str, int] = defaultdict(int)
        for r in flagged:
            for f in r["findings"]:
                by_code[f["code"]] += 1
        print(f"Scanned {len(records)} Meraki UCs, "
              f"{len(flagged)} have at least one finding "
              f"({sum(by_code.values())} findings total).")
        print()
        for code in sorted(by_code):
            print(f"  {code}: {by_code[code]:3d} occurrences")
        print()
        for r in flagged:
            print(f"--- UC-{r['id']}  {r['title']}")
            print(f"    {r['path']}")
            print(f"    sourcetypes: {r['sourcetypes']}")
            for f in r["findings"]:
                print(f"    [{f['code']}] {f['msg']}")
            print()

    if args.check and flagged:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
