#!/usr/bin/env python3
"""Add Equipment Models field to all Cisco use cases."""
import re
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UC_DIR = os.path.join(REPO, "use-cases")

# Hardware model strings by Cisco product area
HW_IOS = (
    "Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, "
    "Catalyst 3650, Catalyst 3850, Catalyst 2960-X, "
    "ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, "
    "ASR 1001-X, ASR 1002-X, ASR 1006-X, "
    "IE 3200, IE 3300, IE 3400"
)

HW_FIREPOWER = (
    "Cisco Secure Firewall 3110, 3120, 3130, 3140, "
    "Firepower 1010, 1120, 1140, 1150, "
    "Firepower 2110, 2120, 2130, 2140, "
    "Firepower 4110, 4120, 4140, 4150, "
    "Firepower 9300, "
    "Firepower Management Center (FMC)"
)

HW_MERAKI_MX = (
    "Cisco Meraki MX64, MX67, MX68, MX75, MX84, MX85, MX95, MX100, MX105, MX250, MX450"
)
HW_MERAKI_MR = (
    "Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86"
)
HW_MERAKI_MS = (
    "Cisco Meraki MS120, MS125, MS130, MS210, MS225, MS250, MS350, MS390"
)
HW_MERAKI_ALL = f"{HW_MERAKI_MX}, {HW_MERAKI_MR}, {HW_MERAKI_MS}"

HW_WLC = (
    "Cisco WLC 3504, WLC 5520, WLC 8540, "
    "Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL"
)
HW_WLC_APS = (
    "Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800"
)

HW_ISE = (
    "Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance"
)

HW_ASA = (
    "Cisco ASA 5506-X, ASA 5508-X, ASA 5516-X, ASA 5525-X, ASA 5545-X, ASA 5555-X, ASAv"
)

HW_UCS = (
    "Cisco UCS B200 M5/M6/M7, UCS C220 M5/M6/M7, UCS C240 M5/M6/M7, UCS C480 M5, "
    "UCS X210c M6/M7, UCS X410c M6, "
    "UCS 6324 FI, UCS 6332 FI, UCS 6454 FI, UCS 6536 FI"
)

HW_ACI = (
    "Cisco APIC, Nexus 9332C (ACI), Nexus 93180YC-FX (ACI), Nexus 9364C (ACI), "
    "Nexus 9504 (ACI), Nexus 9508 (ACI)"
)

HW_SDWAN = (
    "Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, "
    "ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), "
    "vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, "
    "vManage, vSmart, vBond"
)

HW_UCM = (
    "Cisco Unified Communications Manager (CUCM), Unity Connection, "
    "IP Phone 7800 series, IP Phone 8800 series"
)

HW_WEBEX = (
    "Cisco Webex Calling, Webex Meetings, Webex Room Kit, Webex Board, Webex Desk"
)

# UC ID prefix -> hardware models mapping
UC_HARDWARE = {}

# 5.1.x: All IOS use cases
for n in range(1, 24):
    UC_HARDWARE[f"5.1.{n}"] = HW_IOS

# 5.2.x: All Firepower use cases
for n in range(1, 19):
    UC_HARDWARE[f"5.2.{n}"] = HW_FIREPOWER

# 5.4.x: Wireless (mixed Meraki/WLC/ISE)
UC_HARDWARE["5.4.1"] = f"{HW_MERAKI_MR}, {HW_WLC}, {HW_WLC_APS}"       # AP Offline Detection
UC_HARDWARE["5.4.2"] = f"{HW_WLC}, {HW_WLC_APS}"                        # Client Association Failures
UC_HARDWARE["5.4.3"] = f"{HW_MERAKI_MR}, {HW_WLC}, {HW_WLC_APS}"       # Channel Utilization
UC_HARDWARE["5.4.4"] = f"{HW_WLC}, {HW_WLC_APS}"                        # Rogue AP Detection
UC_HARDWARE["5.4.5"] = f"{HW_MERAKI_MR}, {HW_WLC}, {HW_WLC_APS}"       # Client Count Trending
UC_HARDWARE["5.4.6"] = f"{HW_WLC}, {HW_WLC_APS}"                        # RF Interference Events
UC_HARDWARE["5.4.7"] = HW_ISE                                             # Wireless Authentication Trends
UC_HARDWARE["5.4.8"] = f"{HW_WLC}, {HW_ISE}"                             # RADIUS Authentication Failures
UC_HARDWARE["5.4.9"] = f"{HW_WLC}, {HW_WLC_APS}"                        # Client Roaming Analysis
UC_HARDWARE["5.4.10"] = f"{HW_WLC}, {HW_WLC_APS}"                       # Wireless IDS/IPS Events
UC_HARDWARE["5.4.11"] = f"{HW_WLC}, {HW_WLC_APS}"                       # Band Steering Effectiveness

# 5.5.x: All SD-WAN use cases
for n in range(1, 11):
    UC_HARDWARE[f"5.5.{n}"] = HW_SDWAN

# 5.8.2: Meraki Organization Monitoring
UC_HARDWARE["5.8.2"] = HW_MERAKI_ALL
# 5.8.6: ISE Endpoint Posture Compliance
UC_HARDWARE["5.8.6"] = HW_ISE

# 10.1.1: Threat Prevention (Firepower)
UC_HARDWARE["10.1.1"] = HW_FIREPOWER

# 11.3.x: UCM and Webex
UC_HARDWARE["11.3.1"] = f"{HW_UCM}, {HW_WEBEX}"   # Call Quality Monitoring
UC_HARDWARE["11.3.2"] = HW_UCM                      # Call Volume Trending
UC_HARDWARE["11.3.3"] = HW_UCM                      # VoIP Jitter/Latency/Packet Loss
UC_HARDWARE["11.3.4"] = HW_UCM                      # Trunk Utilization
UC_HARDWARE["11.3.5"] = f"{HW_UCM}, {HW_WEBEX}"   # Conference Bridge Capacity
UC_HARDWARE["11.3.6"] = HW_UCM                      # Toll Fraud Detection
UC_HARDWARE["11.3.7"] = HW_UCM                      # Mass Phone De-registration
UC_HARDWARE["11.3.8"] = HW_WEBEX                    # Webex Meeting Analytics

# Additional UCs in 11.3 if they exist
for n in range(9, 15):
    if f"11.3.{n}" not in UC_HARDWARE:
        UC_HARDWARE[f"11.3.{n}"] = HW_UCM

# 17.1.x: All NAC/ISE use cases
for n in range(1, 9):
    UC_HARDWARE[f"17.1.{n}"] = HW_ISE

# 17.2.x: All VPN/ASA use cases
for n in range(1, 9):
    UC_HARDWARE[f"17.2.{n}"] = HW_ASA

# 18.1.x: All ACI use cases
for n in range(1, 8):
    UC_HARDWARE[f"18.1.{n}"] = HW_ACI

# 19.1.x: All UCS use cases
for n in range(1, 7):
    UC_HARDWARE[f"19.1.{n}"] = HW_UCS

# 6.1.9: Fibre Channel Port Errors (Cisco MDS)
UC_HARDWARE["6.1.9"] = "Cisco MDS 9132T, MDS 9148T, MDS 9396T, MDS 9700, MDS 9706, MDS 9710"


def add_hw_to_file(filepath):
    """Add Equipment Models field after App/TA for matching UCs."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    count = 0
    current_uc_id = None

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Track current UC ID
        m = re.match(r"^#{3,4}\s+UC-(\d+\.\d+\.\d+)\s*[·•]", line)
        if m:
            current_uc_id = m.group(1)
            continue

        # After App/TA line, insert Equipment Models if this UC has hardware
        if current_uc_id and re.match(r"^-\s+\*\*App/TA:\*\*", line.strip()):
            hw = UC_HARDWARE.get(current_uc_id)
            if hw:
                # Check if Equipment Models already exists on next line
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if not next_line.startswith("- **Equipment Models:**"):
                    new_lines.append(f"- **Equipment Models:** {hw}")
                    count += 1

    if count > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))
    return count


def main():
    total = 0
    for fname in sorted(os.listdir(UC_DIR)):
        if not fname.startswith("cat-") or not fname.endswith(".md"):
            continue
        fpath = os.path.join(UC_DIR, fname)
        n = add_hw_to_file(fpath)
        if n > 0:
            print(f"  {fname}: added {n} Equipment Models fields")
            total += n
    print(f"\nTotal: {total} Equipment Models fields added")


if __name__ == "__main__":
    main()
