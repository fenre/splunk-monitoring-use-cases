#!/usr/bin/env python3
"""One-shot renamer for cat-22 §22.17-22.19 UCs.

The previous batch generator gave each UC a generic suffix like
"— control theme N", "— control point N", or "— indicator N".  The audit
placeholder linter rightly flags those titles as placeholder content.

Each UC has distinct SPL, so we derive a short descriptor from the SPL's
intent and rewrite:

  ### UC-22.X.Y · <old theme> — control theme N (<regulation>)

into:

  ### UC-22.X.Y · <new descriptor> (<regulation>)

The accompanying "Value" line that quotes the old suffix is rewritten too,
so no downstream search for "control theme N" / "control point N" keeps
finding templated boilerplate.

Idempotent — running twice produces no additional changes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NEW_TITLES: dict[str, str] = {
    # 22.17 · 21 CFR Part 11 — Electronic records integrity
    "22.17.1": "LIMS audit entries missing reason codes",
    "22.17.2": "LIMS excessive record modifications per batch",
    "22.17.3": "MES batch clock-skew vs generated timestamp",
    "22.17.4": "Veeva document hash mismatch",
    "22.17.5": "LIMS records past retention without disposition",
    # Electronic signatures
    "22.17.6": "ELN signatures beyond delegated authority",
    "22.17.7": "ELN signatures missing certificate or hash binding",
    "22.17.8": "ELN logins without FIDO2 or X.509 credential",
    "22.17.9": "ELN signatures missing meaning code",
    "22.17.10": "ELN release signatures bypassing multi-step flow",
    # Audit trails
    "22.17.11": "CDS injections with too few audit entries",
    "22.17.12": "LIMS sample touched by multiple actors",
    "22.17.13": "MES record UPDATE without change reason",
    "22.17.14": "HPLC NTP drift over 500 ms",
    "22.17.15": "Veeam LIMS database backup failures",
    # ALCOA+ data integrity
    "22.17.16": "MES batch entries missing ALCOA who/when/what/why fields",
    "22.17.17": "Commvault MES subclient backups not completed",
    "22.17.18": "LIMS COPY action without independent witness",
    "22.17.19": "CDS raw vs processed chromatogram file mismatch",
    "22.17.20": "Lab instrument integrity-check failures",
    # GxP computer system validation
    "22.17.21": "LIMS-PROD PQ sign-offs incomplete",
    "22.17.22": "LIMS change requests without CSV risk assessment",
    "22.17.23": "Periodic system reviews overdue",
    "22.17.24": "GxP workstation Windows account changes",
    "22.17.25": "Overdue GxP computer-systems training by course",
    # 22.18 · API RP 1164 — RTU/HMI access control
    "22.18.1": "FactoryTalk excessive operator login sessions",
    "22.18.2": "FactoryTalk compressor-area role mismatch",
    "22.18.3": "OPC-UA Write method without named approver",
    "22.18.4": "FactoryTalk rejected open/close commands",
    "22.18.5": "FactoryTalk operator sessions idle over 2 h",
    "22.18.6": "Vendor or field-tech Windows logons outside depot hours",
    "22.18.7": "Pipeline HMI app running on jailbroken mobile",
    # SCADA command authentication
    "22.18.8": "DNP3 high-volume direct-operate commands",
    "22.18.9": "PI-AF setpoint changes beyond 15 percent",
    "22.18.10": "Modbus coil writes on SIL-rated registers",
    "22.18.11": "Ignition pump actions originating from scripts",
    "22.18.12": "ESD or shutdown alarm acknowledgements",
    "22.18.13": "Rockwell controller program download or upload by vendor",
    "22.18.14": "OPC-UA unsigned program downloads",
    # Pipeline SCADA network segmentation
    "22.18.15": "FIELD zone to SCADA-DMZ unexpected bytes",
    "22.18.16": "ENTERPRISE to SCADA-DMZ flows",
    "22.18.17": "DNP3 traffic on non-standard ports",
    "22.18.18": "Pipeline-field WiFi without WPA3-Enterprise",
    "22.18.19": "Edge Modbus gateway exposing over 200 unit IDs",
    "22.18.20": "OT-PLC TLSv1.0 connections",
    "22.18.21": "Vendor GlobalProtect jump from non-standard image",
    # Field device integrity
    "22.18.22": "Field devices on firmware behind ICS-CERT required version",
    "22.18.23": "Schneider PLC logic changes by user span",
    "22.18.24": "Modbus CRC success rate below 99.5 percent",
    "22.18.25": "Wonderware flow/pressure tag jumps over 50 percent",
    "22.18.26": "RTU-ROW-12 off-role Genetec badge swipes",
    "22.18.27": "DNP3 sequence-number gaps",
    "22.18.28": "Claroty devices with unverified integrity state",
    # API 1164 incident and compliance
    "22.18.29": "Pipeline cyber incident MTTR tracking",
    "22.18.30": "API 1164 domain-score regression year-over-year",
    "22.18.31": "Critical SCADA vulnerabilities by Tenable plugin",
    "22.18.32": "SCADA tabletop exercises missing evidence",
    "22.18.33": "Pipeline SCADA risks with open treatment",
    "22.18.34": "Pipeline cyber training overdue",
    "22.18.35": "API 1164 regulatory reports past due",
    # 22.19 · FISMA / FedRAMP — Continuous monitoring
    "22.19.1": "CloudTrail high-volume mutating actions",
    "22.19.2": "Tenable FedRAMP compliance failures",
    "22.19.3": "STIG file-integrity hash mismatch",
    "22.19.4": "WSUS patch coverage below 95 percent",
    "22.19.5": "FedRAMP servers not discovered in 30 days",
    # Authorization and boundary
    "22.19.6": "GovCloud SSP sections incomplete",
    "22.19.7": "FedRAMP POA&M items past planned finish",
    "22.19.8": "Risk acceptances past review date",
    "22.19.9": "Azure VNet peerings outside approved list",
    "22.19.10": "AWS SG ingress opened to 0.0.0.0/0",
    # Federal incident handling
    "22.19.11": "FedRAMP notable events unactioned over 8 h",
    "22.19.12": "US-CERT or CISA incidents unresolved",
    "22.19.13": "Phantom high-severity containers off NIST DE.CM",
    "22.19.14": "FedRAMP hosts with cleared Windows Security log",
    "22.19.15": "Federal IR lessons-learned not published",
    # Privileged and remote access
    "22.19.16": "Fed apps accepting single-factor authentication",
    "22.19.17": "CyberArk Fed-Admin safe checkout surge",
    "22.19.18": "Dormant privileged accounts beyond 90 days",
    "22.19.19": "Fed-VDP VPN from unexpected private subnets",
    "22.19.20": "SAP users with excessive role stacking",
    # Assessment and FedRAMP evidence
    "22.19.21": "FedRAMP 2026 control assessments failed",
    "22.19.22": "Open 3PAO findings by severity",
    "22.19.23": "CDM devices without hardware root of trust",
    "22.19.24": "Risk score above 80 on CUI systems",
    "22.19.25": "FedRAMP marketplace listings not active",
}


TITLE_RE = re.compile(
    r"^### UC-(?P<id>22\.(?:17|18|19)\.\d+) · (?P<old>.+?) — (?P<suffix>control theme|control point|indicator) \d+ \((?P<reg>[^)]+)\)\s*$",
    re.MULTILINE,
)


def _title_replacer(match: re.Match[str]) -> str:
    uc_id = match.group("id")
    reg = match.group("reg")
    new_title = NEW_TITLES.get(uc_id)
    if not new_title:
        return match.group(0)
    return f"### UC-{uc_id} · {new_title} ({reg})"


def _value_line_replacer(match: re.Match[str]) -> str:
    """Drop the quoted templated-stub clause while keeping the sentence readable.

    Examples of matches (phrase → empty):
      ` by monitoring "Foo — control point 1"`  (22.18)
      ` for "Foo — control theme 2"`             (22.17)
      ` by operationalizing "Foo — indicator 3"` (22.19)
    """

    return ""


VALUE_LINE_RE = re.compile(
    r'\s+(?:by\s+[A-Za-z]+ing|for|regarding)\s+"[^"\n]+?\s+—\s+(?:control theme|control point|indicator)\s+\d+"'
)


def main(path: Path) -> int:
    text = path.read_text()

    original = text
    text, title_count = TITLE_RE.subn(_title_replacer, text)
    text, value_count = VALUE_LINE_RE.subn(_value_line_replacer, text)

    if text == original:
        print(f"No changes needed in {path}")
        return 0

    path.write_text(text)
    print(
        f"Renamed {title_count} titles and cleaned "
        f"{value_count} Value lines in {path}"
    )
    return 0


if __name__ == "__main__":
    target = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("use-cases/cat-22-regulatory-compliance.md")
    )
    sys.exit(main(target))
