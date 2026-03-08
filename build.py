#!/usr/bin/env python3
"""
build.py — Compile per-category markdown files into data.js for the dashboard.

Usage:
    python3 build.py

Reads:
    use-cases/cat-*.md          — use case content (all data including CIM)
    use-cases/INDEX.md          — category metadata (icons, descriptions, starters)

Writes:
    data.js                     — const DATA, CAT_META, CAT_STARTERS, CAT_GROUPS
"""

import glob
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UC_DIR = os.path.join(SCRIPT_DIR, "use-cases")
OUTPUT = os.path.join(SCRIPT_DIR, "data.js")
OUTPUT_CATALOG_JSON = os.path.join(SCRIPT_DIR, "catalog.json")

# Emoji → value mappings
CRITICALITY_MAP = {
    "🔴 critical": "critical", "critical": "critical",
    "🟠 high": "high", "high": "high",
    "🟡 medium": "medium", "medium": "medium",
    "🟢 low": "low", "low": "low",
}

DIFFICULTY_MAP = {
    "🟢 beginner": "beginner", "beginner": "beginner",
    "🔵 intermediate": "intermediate", "intermediate": "intermediate",
    "🟠 advanced": "advanced", "advanced": "advanced",
    "🔴 expert": "expert", "expert": "expert",
}

CAT_GROUPS = {
    "infra":    [1, 2, 5, 6, 15, 18, 19],
    "security": [9, 10, 17],
    "cloud":    [3, 4, 20],
    "app":      [7, 8, 11, 12, 13, 14, 16],
}

# Equipment (IT assets) → TA patterns. Used to filter use cases by "what equipment do you have?"
# Each entry: id (slug), label (user-facing), tas (substrings; if any appears in UC's App/TA field, UC is relevant).
EQUIPMENT = [
    {"id": "linux", "label": "Linux / Unix servers", "tas": ["Splunk_TA_nix"]},
    {"id": "windows", "label": "Windows servers & workstations", "tas": ["Splunk_TA_windows"]},
    {"id": "macos", "label": "macOS", "tas": ["macOS", "Splunk UF for macOS"]},
    {
        "id": "vmware",
        "label": "VMware",
        "tas": ["Splunk_TA_vmware", "TA-vmware", "VMware", "vSphere", "ESXi", "vCenter"],
        "models": [
            {"id": "vsphere", "label": "vSphere", "tas": ["vSphere", "vsphere"]},
            {"id": "esxi", "label": "ESXi", "tas": ["ESXi", "esxi"]},
            {"id": "vcenter", "label": "vCenter", "tas": ["vCenter", "vcenter"]},
            {"id": "ta_vmware", "label": "Splunk TA for VMware", "tas": ["Splunk_TA_vmware", "TA-vmware"]},
        ],
    },
    {"id": "hyperv", "label": "Microsoft Hyper-V", "tas": ["Hyper-V", "Splunk_TA_microsoft-cloudservices", "hyperv", "HyperV", "Perfmon:HyperV", "Hyper-V"]},
    {"id": "aws", "label": "Amazon Web Services (AWS)", "tas": ["Splunk_TA_aws", "AWS", "CloudTrail", "CloudWatch"]},
    {"id": "azure", "label": "Microsoft Azure", "tas": ["Splunk_TA_microsoft-cloudservices", "Azure", "Azure Monitor", "Azure Activity"]},
    {"id": "gcp", "label": "Google Cloud Platform (GCP)", "tas": ["Splunk_TA_google-cloudplatform", "GCP", "Google Cloud"]},
    {"id": "kubernetes", "label": "Kubernetes / containers", "tas": ["Kubernetes", "Splunk Connect for Kubernetes", "SCK", "OpenTelemetry", "Splunk_TA_otel", "Docker", "containers"]},
    {
        "id": "paloalto",
        "label": "Palo Alto Networks",
        "tas": ["Splunk_TA_paloalto", "Palo Alto", "GlobalProtect", "Prisma"],
        "models": [
            {"id": "pan_firewall", "label": "Palo Alto Firewall / PAN-OS", "tas": ["Splunk_TA_paloalto", "Palo Alto", "PAN-OS", "paloalto"]},
            {"id": "globalprotect", "label": "GlobalProtect", "tas": ["GlobalProtect", "globalprotect"]},
            {"id": "prisma", "label": "Prisma Access", "tas": ["Prisma", "prisma"]},
        ],
    },
    {
        "id": "cisco",
        "label": "Cisco",
        "tas": ["Splunk_TA_cisco", "Cisco", "cisco-firepower", "cisco-asa", "cisco-ios", "cisco-ise",
                "cisco_meraki", "Meraki", "cisco:ucs", "cisco:aci", "cisco:sdwan", "cisco:ucm",
                "cisco:wlc", "Webex", "TA-cisco_ios", "Cisco Catalyst Add-on", "Cisco Meraki Add-on",
                "Cisco Secure Firewall"],
        "models": [
            {"id": "firepower", "label": "Cisco Firepower / Secure Firewall", "tas": ["Cisco Firepower", "cisco-firepower", "cisco:firepower", "Cisco Secure Firewall"]},
            {"id": "asa", "label": "Cisco ASA", "tas": ["Splunk_TA_cisco-asa", "Cisco ASA", "cisco-asa", "cisco:asa"]},
            {"id": "ios", "label": "Cisco IOS / Catalyst / ISR / ASR", "tas": ["TA-cisco_ios", "Cisco IOS", "cisco-ios", "cisco:ios"]},
            {"id": "ise", "label": "Cisco ISE", "tas": ["Splunk_TA_cisco-ise", "Cisco ISE", "cisco-ise", "cisco:ise"]},
            {"id": "meraki", "label": "Cisco Meraki", "tas": ["Cisco Meraki Add-on", "Cisco Meraki", "Meraki", "cisco_meraki", "meraki"]},
            {"id": "ucs", "label": "Cisco UCS", "tas": ["Splunk_TA_cisco-ucs", "Cisco UCS", "cisco:ucs", "UCS Manager"]},
            {"id": "aci", "label": "Cisco ACI", "tas": ["cisco:aci", "Cisco ACI", "ACI", "APIC", "TA_cisco-ACI"]},
            {"id": "sdwan", "label": "Cisco SD-WAN / Catalyst Center", "tas": ["cisco:sdwan", "Cisco SD-WAN", "vManage", "Cisco Catalyst Add-on"]},
            {"id": "wlc", "label": "Cisco WLC / Catalyst 9800", "tas": ["cisco:wlc", "Cisco WLC", "WLC"]},
            {"id": "ucm", "label": "Cisco UCM / Unified Communications", "tas": ["cisco:ucm", "Cisco UCM", "UCM CDR", "CUCM"]},
            {"id": "webex", "label": "Cisco Webex", "tas": ["Webex", "webex", "ta_cisco_webex"]},
            {"id": "spaces", "label": "Cisco Spaces", "tas": ["Cisco Spaces", "cisco:spaces", "cisco_spaces", "Spaces Add-On"]},
        ],
    },
    {
        "id": "fortinet",
        "label": "Fortinet",
        "tas": ["Fortinet", "FortiGate", "Splunk_TA_fortinet", "TA-fortinet_fortigate"],
        "models": [
            {"id": "fortigate", "label": "FortiGate", "tas": ["FortiGate", "fortigate", "Splunk_TA_fortinet", "TA-fortinet_fortigate"]},
            {"id": "fortianalyzer", "label": "FortiAnalyzer", "tas": ["FortiAnalyzer", "fortianalyzer"]},
        ],
    },
    {
        "id": "f5",
        "label": "F5",
        "tas": ["Splunk_TA_f5-bigip", "F5", "BIG-IP", "f5-bigip"],
        "models": [
            {"id": "bigip", "label": "F5 BIG-IP", "tas": ["Splunk_TA_f5-bigip", "BIG-IP", "f5-bigip", "bigip"]},
            {"id": "asm", "label": "F5 ASM", "tas": ["ASM", "f5-bigip (ASM)"]},
        ],
    },
    {"id": "syslog", "label": "Syslog (generic)", "tas": ["Splunk_TA_syslog", "Syslog", "syslog"]},
    {
        "id": "snmp",
        "label": "SNMP",
        "tas": ["SNMP", "snmp"],
        "models": [
            {"id": "generic", "label": "SNMP (generic)", "tas": ["SNMP", "snmp"]},
            {"id": "pdu", "label": "PDU / power", "tas": ["PDU", "PDU-MIB", "pdu"]},
            {"id": "ups", "label": "UPS", "tas": ["UPS", "UPS-MIB", "ups"]},
        ],
    },
    {"id": "iis", "label": "Microsoft IIS", "tas": ["IIS", "Microsoft IIS", "Splunk Add-on for Microsoft IIS"]},
    {"id": "mssql", "label": "Microsoft SQL Server", "tas": ["Splunk_TA_microsoft-sqlserver", "microsoft-sqlserver", "SQL Server"]},
    {"id": "m365", "label": "Microsoft 365 / Entra ID", "tas": ["Splunk_TA_MS_O365", "MS_O365", "Office 365", "Entra", "M365", "microsoft-cloudservices"]},
    {"id": "exchange", "label": "Microsoft Exchange", "tas": ["Splunk_TA_microsoft-exchange", "microsoft-exchange", "Exchange"]},
    {
        "id": "apache",
        "label": "Apache HTTP Server",
        "tas": ["Splunk_TA_apache", "apache"],
        "models": [
            {"id": "httpd", "label": "Apache httpd", "tas": ["Splunk_TA_apache", "apache", "httpd"]},
        ],
    },
    {
        "id": "nginx",
        "label": "NGINX",
        "tas": ["TA-nginx", "nginx", "NGINX"],
        "models": [
            {"id": "open", "label": "NGINX Open Source", "tas": ["TA-nginx", "nginx", "NGINX"]},
            {"id": "plus", "label": "NGINX Plus", "tas": ["NGINX Plus", "nginx plus"]},
        ],
    },
    {"id": "okta", "label": "Okta", "tas": ["Splunk_TA_okta", "okta"]},
    {"id": "servicenow", "label": "ServiceNow", "tas": ["Splunk_TA_snow", "snow", "ServiceNow"]},
    {"id": "jenkins", "label": "Jenkins", "tas": ["Jenkins"]},
    {"id": "kafka", "label": "Kafka", "tas": ["TA-kafka", "Kafka", "kafka"]},
    {
        "id": "db_connect",
        "label": "Databases",
        "tas": ["DB Connect", "Splunk_TA_oracle", "splunk_app_db_connect", "Oracle", "MySQL", "PostgreSQL"],
        "models": [
            {"id": "dbconnect", "label": "Splunk DB Connect", "tas": ["DB Connect", "splunk_app_db_connect"]},
            {"id": "oracle", "label": "Oracle", "tas": ["Splunk_TA_oracle", "Oracle", "oracle"]},
            {"id": "mssql_ta", "label": "Microsoft SQL (TA)", "tas": ["Splunk_TA_microsoft-sqlserver", "microsoft-sqlserver"]},
        ],
    },
    {
        "id": "hardware_bmc",
        "label": "Hardware / BMC",
        "tas": ["ipmitool", "iDRAC", "iLO", "smartctl", "storcli", "megacli", "BMC", "edac-util", "ssacli", "dmidecode"],
        "models": [
            {"id": "idrac", "label": "Dell iDRAC", "tas": ["iDRAC", "idrac"]},
            {"id": "ilo", "label": "HPE iLO", "tas": ["iLO", "ilo"]},
            {"id": "ipmi", "label": "IPMI (generic)", "tas": ["ipmitool", "IPMI", "ipmi"]},
            {"id": "smartctl", "label": "Disks (SMART / smartctl)", "tas": ["smartctl"]},
            {"id": "storcli", "label": "LSI MegaRAID (storcli)", "tas": ["storcli"]},
            {"id": "megacli", "label": "LSI MegaRAID (megacli)", "tas": ["megacli"]},
            {"id": "ssacli", "label": "HPE Smart Array (ssacli)", "tas": ["ssacli"]},
            {"id": "edac", "label": "Memory / EDAC (edac-util)", "tas": ["edac-util", "edac"]},
            {"id": "dmidecode", "label": "System info (dmidecode)", "tas": ["dmidecode"]},
        ],
    },
    {"id": "security_essentials", "label": "Splunk Security Essentials (ESCU)", "tas": ["Security Essentials", "ESCU"]},
    {
        "id": "infoblox",
        "label": "Infoblox",
        "tas": ["Splunk_TA_infoblox", "Infoblox", "infoblox"],
        "models": [
            {"id": "dns", "label": "Infoblox DNS", "tas": ["Infoblox", "infoblox", "DNS"]},
            {"id": "dhcp", "label": "Infoblox DHCP", "tas": ["Infoblox", "infoblox", "DHCP"]},
        ],
    },
    {
        "id": "netflow",
        "label": "NetFlow",
        "tas": ["NetFlow", "netflow"],
        "models": [
            {"id": "netflow", "label": "NetFlow", "tas": ["NetFlow", "netflow"]},
            {"id": "sflow", "label": "sFlow", "tas": ["sFlow", "sflow"]},
        ],
    },
    {
        "id": "citrix",
        "label": "Citrix",
        "tas": ["Splunk_TA_citrix-netscaler", "citrix", "NetScaler"],
        "models": [
            {"id": "netscaler", "label": "Citrix NetScaler / ADC", "tas": ["Splunk_TA_citrix-netscaler", "citrix", "NetScaler", "netscaler"]},
        ],
    },
    {"id": "cyberark", "label": "CyberArk", "tas": ["Splunk_TA_cyberark", "CyberArk", "cyberark"]},
    {"id": "itsi", "label": "Splunk ITSI", "tas": ["ITSI", "Splunk ITSI"]},
    {"id": "stream", "label": "Splunk Stream", "tas": ["Splunk Stream", "Splunk App for Stream"]},
]

# Link to the common implementation guide (apps, inputs.conf, Splunk directory)
IMPLEMENTATION_GUIDE_LINK = "docs/implementation-guide.md"


def equipment_ids_for_ta_string(ta_str):
    """Given a use case's App/TA field (t), return (equipment_ids, model_compound_ids).
    model_compound_ids are "eqId_modelId" for equipment that has models and whose model tas matched."""
    if not (ta_str or "").strip():
        return [], []
    raw = (ta_str or "").replace("`", "").strip().lower()
    if not raw:
        return [], []
    seen = set()
    model_seen = set()
    for eq in EQUIPMENT:
        for pattern in eq["tas"]:
            if pattern.lower() in raw:
                seen.add(eq["id"])
                break
        models = eq.get("models") or []
        for mod in models:
            for pattern in mod["tas"]:
                if pattern.lower() in raw:
                    model_seen.add(eq["id"] + "_" + mod["id"])
                    break
    return sorted(seen), sorted(model_seen)


def generate_detailed_impl(uc):
    """Generate a thorough step-by-step implementation guide from UC fields (used when no explicit Detailed implementation is in markdown)."""
    t = (uc.get("t") or "").strip()
    d = (uc.get("d") or "").strip()
    m = (uc.get("m") or "").strip()
    z = (uc.get("z") or "").strip()
    q = (uc.get("q") or "").strip()
    script = (uc.get("script") or "").strip()
    # First 2–3 sentences of implementation for Step 1 (cap length)
    m_lead = m[:500] + ("…" if len(m) > 500 else "") if m else "Configure inputs and permissions as needed for your environment."
    lines = [
        "Prerequisites",
        "• Install and configure the required add-on or app: " + (t or "see App/TA above") + ".",
        "• Ensure the following data sources are available: " + (d or "see Data Sources above") + ".",
        "• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: " + IMPLEMENTATION_GUIDE_LINK,
        "",
        "Step 1 — Configure data collection",
        m_lead,
        "",
        "Step 2 — Create the search and alert",
    ]
    if q:
        lines.append("Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):")
        lines.append("")
        lines.append("```spl")
        lines.append(q)
        lines.append("```")
        lines.append("")
        lines.append("If the use case includes a tstats/CIM query, enable Data Model Acceleration for the relevant data model.")
    else:
        lines.append("Run the SPL query from the SPL Query section above in Search. Save as a report or alert. Adjust the time range and threshold as needed. If the use case includes a tstats/CIM query, enable Data Model Acceleration for the relevant data model.")
    lines.extend([
        "",
        "Step 3 — Validate",
        "Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.",
        "",
        "Step 4 — Operationalize",
        "Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. " + (("Consider visualizations: " + z) if z else "Use the Visualization section above for suggested panels."),
    ])
    # Scripted input: use explicit script if present; else add generic example when use case mentions scripted input
    d_m_lower = (d + " " + m).lower()
    if script:
        lines.extend([
            "",
            "Scripted input example",
            "Use the script below in a scripted input (see Implementation guide for inputs.conf). Ensure the script is executable and the path in inputs.conf matches your app location:",
            "",
            "```bash",
            script,
            "```",
        ])
    elif "scripted" in d_m_lower:
        lines.extend([
            "",
            "Scripted input (generic example)",
            "This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:",
            "",
            "```ini",
            "[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]",
            "interval = 300",
            "sourcetype = your_sourcetype",
            "index = main",
            "disabled = 0",
            "```",
            "",
            "The script should print one event per line (e.g. key=value). Example minimal script (bash):",
            "",
            "```bash",
            "#!/usr/bin/env bash",
            "# Output metrics or events, one per line",
            "echo \"metric=value timestamp=$(date +%s)\"",
            "```",
            "",
            "For full details (paths, scheduling, permissions), see the Implementation guide: " + IMPLEMENTATION_GUIDE_LINK,
        ])
    return "\n".join(lines)


def parse_category_file(filepath):
    """Parse a single cat-*.md file into a category dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    category = {"s": []}
    current_sub = None
    current_uc = None

    # Code block state: tracks which field we're collecting for
    in_code_block = False
    code_target = None  # "q" for main SPL, "qs" for CIM SPL
    code_lines = []

    # Tracks the last field seen (for associating code blocks)
    last_field = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Code block handling ──
        if in_code_block:
            if stripped.startswith("```"):
                # End of code block — store collected lines
                if current_uc is not None and code_target:
                    current_uc[code_target] = "\n".join(code_lines)
                in_code_block = False
                code_target = None
                code_lines = []
            else:
                code_lines.append(line)
            i += 1
            continue

        # ── Category heading: # 1. Server & Compute  OR  ## 6. Storage ──
        m = re.match(r"^#{1,2}\s+(\d+)\.\s+(.+)$", stripped)
        if m:
            category["i"] = int(m.group(1))
            category["n"] = m.group(2).strip()
            i += 1
            continue

        # ── Subcategory heading: ## 1.1 Linux  OR  ### 6.1 SAN ──
        m = re.match(r"^#{2,3}\s+(\d+\.\d+)\s+(.+)$", stripped)
        if m:
            current_sub = {
                "i": m.group(1),
                "n": m.group(2).strip(),
                "u": [],
            }
            category["s"].append(current_sub)
            current_uc = None
            last_field = None
            i += 1
            continue

        # ── Use case heading: ### UC-1.1.1 · Title  OR  #### UC-6.1.1 · Title ──
        m = re.match(r"^#{3,4}\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*(.+)$", stripped)
        if m:
            current_uc = {
                "i": m.group(1),
                "n": m.group(2).strip(),
                "c": "",
                "f": "",
                "v": "",
                "t": "",
                "d": "",
                "q": "",
                "m": "",
                "z": "",
                "kfp": "",   # known false positives (SSE)
                "refs": "",  # references (URLs, comma-separated)
                "mitre": [], # MITRE ATT&CK IDs
                "dtype": "", # detection type: TTP, Anomaly, Baseline, Hunting, Correlation
                "sdomain": "", # security domain: endpoint, network, threat, identity, etc.
                "reqf": "",   # required fields for the search
                "md": "",    # detailed implementation (expandable); parsed or generated
                "script": "",  # optional script example (scripted input)
                "premium": "",  # Premium Apps (ES, ITSI, SOAR, etc.) when required
                "hw": "",       # Equipment Models — specific hardware models (searchable)
                "dma": "",    # data model acceleration note (e.g. "Enable for Performance, Network_Traffic")
                "schema": "", # schema context: CIM, OCSF, or e.g. "OCSF: authentication"
            }
            if current_sub is not None:
                current_sub["u"].append(current_uc)
            last_field = None
            i += 1
            continue

        # ── Field lines within a use case ──
        if current_uc is not None:
            # Start of code block — determine which field it belongs to
            if stripped.startswith("```spl") or stripped.startswith("```SPL"):
                in_code_block = True
                code_lines = []
                if last_field == "cim spl":
                    code_target = "qs"
                else:
                    code_target = "q"
                i += 1
                continue
            # Script example: code block after - **Script example:** (any ```)
            if stripped.startswith("```") and last_field == "script example":
                in_code_block = True
                code_lines = []
                code_target = "script"
                i += 1
                continue

            # Field: - **Criticality:** value
            m = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.*)$", stripped)
            if m:
                field_name = m.group(1).strip().lower()
                field_value = m.group(2).strip()
                last_field = field_name

                if field_name == "criticality":
                    current_uc["c"] = CRITICALITY_MAP.get(field_value.lower(), field_value.lower())
                elif field_name == "difficulty":
                    current_uc["f"] = DIFFICULTY_MAP.get(field_value.lower(), field_value.lower())
                elif field_name == "value":
                    current_uc["v"] = field_value
                elif field_name in ("app/ta", "app / ta"):
                    current_uc["t"] = field_value
                elif field_name in ("data sources", "data source"):
                    current_uc["d"] = field_value
                elif field_name == "spl":
                    # SPL might be inline or in a code block on next line
                    if field_value and not field_value.startswith("```"):
                        current_uc["q"] = field_value
                elif field_name == "implementation":
                    current_uc["m"] = field_value
                elif field_name == "script example":
                    last_field = field_name  # next code block goes to script
                elif field_name == "detailed implementation":
                    current_uc["md"] = field_value
                    i += 1
                    while i < len(lines):
                        next_stripped = lines[i].strip()
                        if (next_stripped.startswith("- **") or next_stripped.startswith("###") or
                                next_stripped == "---" or next_stripped.startswith("```")):
                            break
                        if next_stripped:
                            current_uc["md"] += "\n" + next_stripped
                        i += 1
                    i -= 1
                elif field_name == "visualization":
                    current_uc["z"] = field_value
                elif field_name == "cim models":
                    # Parse comma-separated model names
                    models = [m.strip() for m in field_value.split(",") if m.strip()]
                    if models:
                        current_uc["a"] = models
                elif field_name == "data model acceleration":
                    current_uc["dma"] = field_value
                elif field_name in ("schema", "ocsf"):
                    current_uc["schema"] = field_value
                elif field_name == "monitoring type":
                    # Network use cases: comma-separated types (e.g. Availability, Performance, Capacity)
                    mtypes = [m.strip() for m in field_value.split(",") if m.strip()]
                    if mtypes:
                        current_uc["mtype"] = mtypes
                elif field_name == "cim spl":
                    # CIM SPL: value might be inline or in next code block
                    if field_value and not field_value.startswith("```"):
                        current_uc["qs"] = field_value
                elif field_name == "known false positives":
                    current_uc["kfp"] = field_value
                elif field_name == "references":
                    current_uc["refs"] = field_value
                elif field_name in ("mitre att&ck", "mitre attack"):
                    # Comma-separated technique IDs, e.g. T1562.008, T1190
                    ids = [x.strip() for x in field_value.split(",") if x.strip()]
                    if ids:
                        current_uc["mitre"] = ids
                elif field_name == "detection type":
                    current_uc["dtype"] = field_value.strip()
                elif field_name == "security domain":
                    current_uc["sdomain"] = field_value.strip()
                elif field_name == "required fields":
                    current_uc["reqf"] = field_value
                elif field_name == "premium apps":
                    current_uc["premium"] = field_value
                elif field_name == "equipment models":
                    current_uc["hw"] = field_value

                i += 1
                continue

        i += 1

    # Fill detailed implementation and equipment tags for every UC
    for sub in category.get("s", []):
        for uc in sub.get("u", []):
            if not (uc.get("md") or "").strip():
                uc["md"] = generate_detailed_impl(uc)
            eq_ids, model_ids = equipment_ids_for_ta_string(uc.get("t"))
            uc["e"] = eq_ids
            uc["em"] = model_ids

    return category


def parse_index_metadata():
    """Parse INDEX.md for CAT_META (icons, descriptions) and CAT_STARTERS."""
    index_path = os.path.join(UC_DIR, "INDEX.md")
    if not os.path.exists(index_path):
        print("  WARNING: INDEX.md not found — no CAT_META or CAT_STARTERS")
        return {}, {}

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    cat_meta = {}   # {cat_id_str: {icon, desc}}
    cat_starters = {}  # {cat_id_str: [{i, n, c, sc}, ...]}

    current_cat = None
    in_starters = False

    for line in content.split("\n"):
        stripped = line.strip()

        # Category heading: ## 1. Server & Compute
        m = re.match(r"^##\s+(\d+)\.\s+(.+)$", stripped)
        if m:
            current_cat = m.group(1)
            cat_meta[current_cat] = {"icon": "", "desc": ""}
            in_starters = False
            continue

        if current_cat is None:
            continue

        # Icon
        m = re.match(r"^-\s+\*\*Icon:\*\*\s*(.+)$", stripped)
        if m:
            cat_meta[current_cat]["icon"] = m.group(1).strip()
            in_starters = False
            continue

        # Description
        m = re.match(r"^-\s+\*\*Description:\*\*\s*(.+)$", stripped)
        if m:
            cat_meta[current_cat]["desc"] = m.group(1).strip()
            in_starters = False
            continue

        # Quick Tip
        m = re.match(r"^-\s+\*\*Quick Tip:\*\*\s*(.+)$", stripped)
        if m:
            cat_meta[current_cat]["quick"] = m.group(1).strip()
            in_starters = False
            continue

        # Quick Start header
        if stripped == "- **Quick Start:**":
            in_starters = True
            cat_starters[current_cat] = []
            continue

        # Starter entry: - UC-1.1.23 · Name (criticality, subcategory)
        if in_starters:
            m = re.match(
                r"^-\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*(.+?)\s*\((\w+)(?:,\s*(.+?))?\)\s*$",
                stripped,
            )
            if m:
                entry = {
                    "i": m.group(1),
                    "n": m.group(2).strip(),
                    "c": m.group(3).strip(),
                }
                if m.group(4):
                    entry["sc"] = m.group(4).strip()
                cat_starters[current_cat].append(entry)
                continue
            else:
                # Non-matching line ends the starter list
                if stripped and not stripped.startswith("-"):
                    in_starters = False

    return cat_meta, cat_starters


def write_data_js(data, cat_meta, output_path):
    """Write data.js with DATA, CAT_META, CAT_GROUPS, and EQUIPMENT."""
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps(cat_meta, ensure_ascii=False, separators=(",", ":"))
    groups_json = json.dumps(CAT_GROUPS, separators=(",", ":"))
    equipment_json = json.dumps(EQUIPMENT, ensure_ascii=False, separators=(",", ":"))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by build.py — do not edit manually\n")
        f.write(f"const DATA = {data_json};\n")
        f.write(f"const CAT_META = {meta_json};\n")
        f.write(f"const CAT_GROUPS = {groups_json};\n")
        f.write(f"const EQUIPMENT = {equipment_json};\n")

    size_kb = os.path.getsize(output_path) / 1024
    return size_kb


def main():
    # Find and sort category files
    pattern = os.path.join(UC_DIR, "cat-[0-9]*.md")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"ERROR: No cat-*.md files found in {UC_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} category files")

    # Parse all categories
    data = []
    total_uc = 0
    total_cim = 0
    for filepath in files:
        fname = os.path.basename(filepath)
        cat = parse_category_file(filepath)
        if "i" not in cat:
            print(f"  SKIP {fname} — no category heading found")
            continue
        uc_count = sum(len(s.get("u", [])) for s in cat.get("s", []))
        cim_count = sum(1 for s in cat.get("s", []) for u in s["u"] if "a" in u)
        sub_count = len(cat.get("s", []))
        total_uc += uc_count
        total_cim += cim_count
        print(f"  {fname}: {cat['n']} — {sub_count} subs, {uc_count} UCs, {cim_count} with CIM")
        data.append(cat)

    # Sort by category ID
    data.sort(key=lambda c: c["i"])

    print(f"\nTotal: {len(data)} categories, {total_uc} use cases, {total_cim} with CIM data")

    # Parse INDEX.md for metadata
    cat_meta, cat_starters = parse_index_metadata()
    print(f"CAT_META: {len(cat_meta)} categories")

    # Write output (starters are derived at runtime by the dashboard)
    size_kb = write_data_js(data, cat_meta, OUTPUT)
    print(f"\nWrote {OUTPUT} ({size_kb:.0f} KB)")

    # Write catalog.json for Splunk UI Toolkit / React app (same data as data.js)
    catalog = {"DATA": data, "CAT_META": cat_meta, "CAT_GROUPS": CAT_GROUPS, "EQUIPMENT": EQUIPMENT}
    with open(OUTPUT_CATALOG_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote {OUTPUT_CATALOG_JSON} ({os.path.getsize(OUTPUT_CATALOG_JSON) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
