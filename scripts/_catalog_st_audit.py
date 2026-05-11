"""Audit catalog SPL for sourcetype hallucinations against documented TAs.

Hard-coded mapping of "wrong sourcetype -> documented sourcetype" based
on Splunkbase TA documentation. Each entry references the official
Splunkbase package and what the TA's documented sourcetypes actually are.

This catches the case where a UC's `app` field claims a specific TA but
the SPL uses a sourcetype that doesn't exist in that TA's real schema.

Usage:
    python3 scripts/_catalog_st_audit.py
    python3 scripts/_catalog_st_audit.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"

# wrong_sourcetype -> (canonical_sourcetype | list, documented_TA, why)
HALLUCINATIONS = {
    # --- Splunk Add-on for Palo Alto Networks (Splunkbase 2757) ---
    "paloalto:traffic":     ("pan:traffic",     "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:threat":      ("pan:threat",      "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:system":      ("pan:system",      "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:config":      ("pan:config",      "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:globalprotect": ("pan:globalprotect", "Splunk_TA_paloalto",
                                "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:hipmatch":    ("pan:hipmatch",    "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:userid":      ("pan:userid",      "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:url":         ("pan:url",         "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:correlation": ("pan:correlation", "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:wildfire":    ("pan:wildfire",    "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:gtp":         ("pan:gtp",         "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:sctp":        ("pan:sctp",        "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:auth":        ("pan:auth",        "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),
    "paloalto:decryption":  ("pan:decryption",  "Splunk_TA_paloalto",
                              "TA uses pan:* sourcetypes, not paloalto:*"),

    # --- Splunk Add-on for Microsoft Office 365 (Splunkbase 4055) ---
    # The TA emits o365:* sourcetypes; ms:o365:* never existed in any TA.
    "ms:o365:management":           ("o365:management:activity",
                                      "Splunk_TA_MS_O365",
                                      "TA emits o365:management:activity, not ms:o365:management"),
    "ms:o365:dlp":                  ("o365:management:activity",
                                      "Splunk_TA_MS_O365",
                                      "DLP events arrive on o365:management:activity (Workload=Dlp filter)"),
    "ms:o365:messagetrace":         ("o365:reporting:messagetrace",
                                      "Splunk_TA_MS_O365",
                                      "Real sourcetype is o365:reporting:messagetrace"),
    "ms:o365:message_trace":        ("o365:reporting:messagetrace",
                                      "Splunk_TA_MS_O365",
                                      "Real sourcetype is o365:reporting:messagetrace"),
    "ms:o365:service:status":       ("o365:service:status",
                                      "Splunk_TA_MS_O365",
                                      "TA emits o365:service:* without ms: prefix"),
    "ms:o365:service:incident":     ("o365:service:incident",
                                      "Splunk_TA_MS_O365",
                                      "TA emits o365:service:* without ms: prefix"),
    "ms:o365:service:message":      ("o365:service:message",
                                      "Splunk_TA_MS_O365",
                                      "TA emits o365:service:* without ms: prefix"),
    "ms:o365:graph:azure_ad":       ("o365:graph:azure_ad",
                                      "Splunk_TA_MS_O365",
                                      "TA emits o365:graph:* without ms: prefix"),
    "ms:o365:graph:tenants":        ("o365:graph:tenants",
                                      "Splunk_TA_MS_O365",
                                      "TA emits o365:graph:* without ms: prefix"),
    "ms:o365:graph:users":          ("o365:graph:users",
                                      "Splunk_TA_MS_O365",
                                      "TA emits o365:graph:* without ms: prefix"),

    # --- Splunk Add-on for Cisco Wireless LAN Controller (Splunkbase 1865) ---
    # The TA and current SC4S vendor pack both emit cisco:wlc:syslog.
    "cisco:wlc": ("cisco:wlc:syslog", "Splunk_TA_cisco-wlc",
                   "TA / SC4S emits cisco:wlc:syslog, not bare cisco:wlc"),

    # --- Splunk Add-on for Cisco NX-OS (Splunkbase 5601) ---
    # The TA and SC4S vendor pack both emit cisco:nxos:syslog for log data;
    # bare cisco:nxos isn't a documented sourcetype.
    "cisco:nxos": ("cisco:nxos:syslog", "Splunk_TA_cisco-nxos",
                    "TA / SC4S emits cisco:nxos:syslog, not bare cisco:nxos"),

    # --- Splunk Add-on for Microsoft Azure (Splunkbase 3757) ---
    # Azure AD sign-in logs: ms:aad:signin never existed in any TA.
    # The current TA emits azure:aad:signin.
    "ms:aad:signin": ("azure:aad:signin", "Splunk_TA_microsoft-azure",
                       "TA emits azure:aad:signin (current) or "
                       "mscs:azure:signinlog (legacy SA-MS-CloudServices); "
                       "ms:aad:signin never existed."),
}


def audit_uc(uc_id: str, spl: str, app: str) -> list[dict]:
    out = []
    for m in re.finditer(r'sourcetype\s*=\s*"?([\w:.\-]+)"?', spl, re.I):
        st = m.group(1).lower()
        if st in HALLUCINATIONS:
            canonical, ta, why = HALLUCINATIONS[st]
            out.append({
                "uc_id": uc_id,
                "wrong": st,
                "canonical": canonical,
                "ta": ta,
                "why": why,
                "app_field": app[:200],
            })
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    findings = []
    n = 0
    for path in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(open(path))
        except Exception:
            continue
        n += 1
        spl = d.get("spl") or ""
        if not spl:
            continue
        app = d.get("app") or ""
        for f in audit_uc(d.get("id", "?"), spl, app):
            f["path"] = str(path.relative_to(ROOT))
            f["title"] = d.get("title", "")
            findings.append(f)

    if args.json:
        print(json.dumps(findings, indent=2))
        return 0 if not findings else 1
    print(f"Scanned {n} UCs, {len(findings)} sourcetype hallucinations\n")
    from collections import Counter
    by_st = Counter(f["wrong"] for f in findings)
    by_uc = Counter(f["uc_id"] for f in findings)
    print(f"Affected UCs: {len(by_uc)}")
    print()
    print("Hallucinations by frequency:")
    for st, c in by_st.most_common():
        canonical = HALLUCINATIONS[st][0]
        print(f"  {c:>3d}x  {st!r:30s} -> {canonical!r}")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
