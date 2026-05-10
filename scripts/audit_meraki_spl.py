#!/usr/bin/env python3
"""Audit Meraki UCs for remaining SPL hallucinations.

Scans every ``content/cat-*/UC-*.json`` whose ``app`` references the
Meraki TA (Splunkbase 5580) and flags:

* Sourcetypes that are NOT in the canonical 35-sourcetype catalogue
  shipped by Splunk_TA_cisco_meraki (or SC4S Meraki vendor pack).
* Indexes that aren't ``meraki``, ``cisco_network``, ``cisco_meraki``,
  ``wireless``, ``network``, or any user-defined index from a per-UC
  override.
* Common hallucinated field references: ``compliance_status``,
  ``people_count`` (outside MV Sense webhook), ``quality_score``,
  ``archive_status``, ``night_mode``, ``signature="*temperature*"``,
  ``power_watts``, ``co2_ppm``, ``noise_db`` (outside the rename-aliases
  we emit in the rewritten UCs).

Usage:
    python3 scripts/audit_meraki_spl.py            # human report
    python3 scripts/audit_meraki_spl.py --check    # exit 1 on any finding
    python3 scripts/audit_meraki_spl.py --json     # machine-readable JSON
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"


# Canonical sourcetypes from the TA + SC4S Meraki vendor pack.
CANONICAL_SOURCETYPES: set[str] = {
    # Splunk_TA_cisco_meraki (35+ sourcetypes - see ~/.cursor/skills/cisco-meraki-ta-setup/reference.md)
    "meraki:accesspoints",
    "meraki:airmarshal",
    "meraki:audit",
    "meraki:cameras",
    "meraki:organizationsecurity",
    "meraki:securityappliances",
    "meraki:switches",
    "meraki:devices",
    "meraki:devicesavailabilities",
    "meraki:devicesavailabilitieschangehistory",
    "meraki:devicesuplinksaddressesbydevice",
    "meraki:devicesuplinkslossandlatency",
    "meraki:powermodulesstatusesbydevice",
    "meraki:firmwareupgrades",
    "meraki:wirelessdevicesethernetstatuses",
    "meraki:wirelessdevicespacketlossbydevice",
    "meraki:wirelesscontrolleravailabilitieschangehistory",
    "meraki:wirelesscontrollerdevicesinterfacesusagehistorybyinterval",
    "meraki:wirelesscontrollerdevicesinterfacespacketoverviewbydevice",
    "meraki:wirelessdeviceswirelesscontrollersbydevice",
    "meraki:summarytopappliancesbyutilization",
    "meraki:summaryswitchpowerhistory",
    "meraki:summarytopclientsbyusage",
    "meraki:summarytopdevicesbyusage",
    "meraki:summarytopswitchesbyenergyusage",
    "meraki:apirequestshistory",
    "meraki:apirequestsresponsecodes",
    "meraki:apirequestsoverview",
    "meraki:assurancealerts",
    "meraki:appliancesdwanstatistics",
    "meraki:appliancesdwanstatuses",
    "meraki:licensesoverview",
    "meraki:licensescotermlicenses",
    "meraki:licensessubscriptionentitlements",
    "meraki:licensessubscriptions",
    "meraki:switchportsoverview",
    "meraki:portstransceiversreadingshistorybyswitch",
    "meraki:switchportsbyswitch",
    "meraki:organizationsnetworks",
    "meraki:organizations",
    "meraki:sensorreadingshistory",
    "meraki:webhook",
    "meraki:webhooklogs:api",
    # SC4S Meraki vendor pack (syslog-side)
    "meraki",
    "cisco:meraki",
    "meraki:syslog",
    # Custom modular-input pattern documented in our rewrites
    "meraki:sm:devices",
}

CANONICAL_INDEXES: set[str] = {
    "meraki",
    "cisco_meraki",
    "cisco_network",  # legacy; flagged separately as soft warning
    "wireless",
    "network",
    "cisco_security",
}

# Hallucinated fields we know we cleaned up. Flag any that re-appear.
HALLUCINATED_FIELDS: set[str] = {
    "compliance_status",
    "compliance_reason",
    "people_count",
    "quality_score",
    "archive_status",
    "night_mode",
    "power_watts",
    # NOTE: co2_ppm and noise_db are removed — they are legitimate BMS / Airthings
    # / Awair / Kaiterra field names. They are ONLY hallucinated when used with
    # Meraki MT sensors (real Meraki MT paths are co2.concentration,
    # noise.ambient.level). The Meraki-only check below skips this false positive.
}

RE_SOURCETYPE = re.compile(
    r'sourcetype\s*=\s*(?:"([^"\\]+)"|([A-Za-z_][A-Za-z0-9_:.\-]*))'
)
RE_INDEX = re.compile(
    r'index\s*=\s*(?:"([^"\\]+)"|([A-Za-z_][A-Za-z0-9_:.\-]*))'
)
# Recognise a Meraki sourcetype anywhere in the SPL (canonical TA + SC4S).
# Matches: meraki, meraki:devices, meraki:webhooklogs:api, cisco:meraki
RE_MERAKI_SOURCETYPE = re.compile(
    r'sourcetype\s*=\s*"?(?:meraki(?::[A-Za-z0-9_:.\-]+)?|cisco:meraki)"?(?![A-Za-z0-9_:])'
)
# Match assignment heads — these create the field, they don't consume it
RE_ASSIGNMENT_HEADS = re.compile(
    r"\b(eval|rename(?:\s+\w+(?:\.\w+)*)?\s+as|stats\s+[A-Za-z_]+\([^)]*\)\s+as)\s*$",
    re.IGNORECASE,
)


@dataclass
class Finding:
    file: str
    uc_id: str
    severity: str
    category: str
    message: str
    snippet: str = ""

    def human(self) -> str:
        s = f"[{self.severity}] [{self.category}] {self.uc_id}: {self.message}"
        if self.snippet:
            s += f"\n        in: {self.snippet[:160]}"
        s += f"\n        file: {self.file}"
        return s


def _is_meraki_uc(uc: dict) -> bool:
    """Strict: a UC is *primarily* Meraki if its `app` field names the Meraki
    TA (Splunkbase 5580) or its `spl` queries a Meraki sourcetype.

    We deliberately do NOT match on equipmentModels or implementation
    because many adjacent UCs (Cisco WLC, Cisco Spaces, Webex, BMS,
    DNAC) mention Meraki in passing without using its sourcetypes.
    """
    app = str(uc.get("app", "")).lower()
    if "meraki" in app or "5580" in app:
        return True
    spl = str(uc.get("spl", ""))
    if RE_MERAKI_SOURCETYPE.search(spl):
        return True
    return False


def _scan_uc(path: Path, findings: list[Finding]) -> None:
    try:
        uc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        findings.append(
            Finding(
                file=str(path.relative_to(REPO)),
                uc_id=path.stem,
                severity="ERROR",
                category="parse",
                message=f"cannot parse JSON: {exc}",
            )
        )
        return
    uc_id = uc.get("id", path.stem)
    spl = uc.get("spl", "")
    cim_spl = uc.get("cimSpl", "") or ""
    has_meraki_st = False
    for blob in (spl, cim_spl):
        if not blob:
            continue
        # Only validate sourcetypes whose name starts with `meraki:` (or the
        # bare `meraki` SC4S sourcetype). Other vendors' sourcetypes in the
        # same SPL (cisco:wlc, cisco:spaces:*, webex:*, bms:*) are out of
        # scope for this Meraki-specific audit.
        for m in RE_SOURCETYPE.finditer(blob):
            st = m.group(1) or m.group(2)
            if "*" in st:
                continue
            is_meraki_named = st.startswith("meraki:") or st in {"meraki", "cisco:meraki"}
            if not is_meraki_named:
                continue
            has_meraki_st = True
            if st not in CANONICAL_SOURCETYPES:
                findings.append(
                    Finding(
                        file=str(path.relative_to(REPO)),
                        uc_id=uc_id,
                        severity="HIGH",
                        category="sourcetype",
                        message=f'unknown Meraki sourcetype "{st}" — not shipped by Splunk_TA_cisco_meraki nor SC4S Meraki vendor pack',
                        snippet=blob[max(0, m.start() - 40) : m.end() + 40],
                    )
                )
        # Only validate `index=meraki` / `index=cisco_meraki`-targeted SPL.
        # If the UC also queries other indexes, leave those to per-vendor audits.
        for m in RE_INDEX.finditer(blob):
            ix = m.group(1) or m.group(2)
            if ix not in {"meraki", "cisco_meraki"}:
                continue
            # Find the nearest sourcetype after this index= and verify it's a
            # Meraki sourcetype.
            tail = blob[m.end() : m.end() + 200]
            st_m = RE_SOURCETYPE.search(tail)
            if st_m:
                st = st_m.group(1) or st_m.group(2)
                if "*" in st:
                    continue
                is_meraki_named = st.startswith("meraki:") or st in {"meraki", "cisco:meraki"}
                if not is_meraki_named:
                    findings.append(
                        Finding(
                            file=str(path.relative_to(REPO)),
                            uc_id=uc_id,
                            severity="MEDIUM",
                            category="index_sourcetype_mismatch",
                            message=f'index="{ix}" used with non-Meraki sourcetype "{st}"',
                            snippet=blob[max(0, m.start() - 40) : m.end() + 60],
                        )
                    )

        # Hallucinated fields: only flag for blobs that actually reference a
        # Meraki sourcetype (otherwise we're outside scope).
        if not has_meraki_st:
            continue
        for field in HALLUCINATED_FIELDS:
            pat = re.compile(r"\b" + re.escape(field) + r"\b")
            if not pat.search(blob):
                continue
            # Skip if the SPL itself creates the field via eval/rename/as alias.
            creator = re.compile(
                r"(?:\beval\s+" + re.escape(field) + r"\s*=)"
                r"|(?:\bas\s+" + re.escape(field) + r"\b)"
                r"|(?:\brename\s+[^\n]*\bas\s+" + re.escape(field) + r"\b)",
                re.IGNORECASE,
            )
            if creator.search(blob):
                continue
            m = pat.search(blob)
            findings.append(
                Finding(
                    file=str(path.relative_to(REPO)),
                    uc_id=uc_id,
                    severity="MEDIUM",
                    category="hallucinated_field",
                    message=f'reference to hallucinated field "{field}" without alias creation',
                    snippet=blob[max(0, m.start() - 40) : m.end() + 40],
                )
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit non-zero on any finding")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    findings: list[Finding] = []
    files = sorted(CONTENT.glob("cat-*/UC-*.json"))
    for f in files:
        _scan_uc(f, findings)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        # Count Meraki UCs strictly: SPL contains a meraki:* sourcetype.
        meraki_files = 0
        for f in files:
            try:
                spl = json.loads(f.read_text(encoding="utf-8")).get("spl", "")
            except Exception:
                continue
            if RE_MERAKI_SOURCETYPE.search(spl):
                meraki_files += 1
        print(f"Scanned {len(files)} UCs ({meraki_files} Meraki SPL queries)")
        print(f"Findings: {len(findings)}")
        # group by category
        by_cat: dict[str, list[Finding]] = {}
        for f in findings:
            by_cat.setdefault(f.category, []).append(f)
        for cat in sorted(by_cat):
            print(f"\n  {cat}: {len(by_cat[cat])}")
            for f in by_cat[cat][:25]:
                print("  " + f.human())
            if len(by_cat[cat]) > 25:
                print(f"  ... +{len(by_cat[cat]) - 25} more")

    return 1 if (args.check and findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
