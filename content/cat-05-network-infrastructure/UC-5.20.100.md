<!-- AUTO-GENERATED from UC-5.20.100.json — DO NOT EDIT -->

---
id: "5.20.100"
title: "OMB M-21-07 Federal IPv6-Only Mandate Compliance Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.100 · OMB M-21-07 Federal IPv6-Only Mandate Compliance Tracking

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*The government has told all its offices that by a certain year, everyone must switch from old-format addresses (IPv4) to new-format addresses (IPv6). We built a big scoreboard that shows exactly how many of our computers and devices have switched, how many still need to switch, and how close we are to meeting the deadline. It's like tracking homework completion for a very large class.*

---

## Description

Automates compliance tracking for OMB Memorandum M-21-07, which mandates U.S. federal agencies transition to IPv6-only. Calculates IPv6 adoption percentages across all network assets, categorises assets as IPv6-only, dual-stack, or IPv4-only, and tracks progress against the FY2025 (80% IPv6-capable) and FY2028 (100% IPv6-only) milestones. While primarily applicable to federal agencies, this UC is valuable for any large organization tracking IPv6 migration progress.

## Value

OMB M-21-07 is a binding federal mandate with annual reporting requirements. Manual compliance tracking is error-prone and labour-intensive across large agencies with thousands of network assets. This automated dashboard provides real-time compliance visibility, identifies IPv4-only holdouts requiring remediation, and generates the data needed for OMB annual reporting. The same framework is applicable to enterprise IPv6 migration programs.

## Implementation

Collect network device and host data. Classify each asset as IPv6-only, dual-stack, or IPv4-only based on observed traffic and configuration. Calculate compliance percentages against OMB milestones.

## Detailed Implementation

### Prerequisites
- Network asset inventory in Splunk (device type, location, function).
- Traffic data from firewalls, flow collectors, or packet brokers.
- Configuration data from network devices.

### Step 1 — Configure data collection

**Asset inventory lookup:**
Create a CSV lookup mapping hosts to asset metadata:
```csv
host,asset_type,location,business_unit,waiver,waiver_reason
fw-dc-01,firewall,DC-East,Infrastructure,no,
legacy-mainframe,server,DC-East,Finance,yes,"COBOL application cannot be modified"
```

Upload to Splunk:
```spl
| inputlookup asset_inventory.csv | stats count by asset_type, waiver
```

**Configuration-based classification:**
For more accurate classification, parse device configs:
```spl
index=network sourcetype="cisco:*:config" earliest=-7d
| dedup host
| eval has_ipv6_interface=if(match(_raw, "(?i)ipv6 address"), 1, 0)
| eval has_ipv4_interface=if(match(_raw, "(?i)ip address \d"), 1, 0)
| eval config_status=case(
    has_ipv6_interface=1 AND has_ipv4_interface=0, "IPv6-only",
    has_ipv6_interface=1 AND has_ipv4_interface=1, "Dual-stack",
    has_ipv6_interface=0 AND has_ipv4_interface=1, "IPv4-only",
    1=1, "Unknown")
| stats count by config_status
```

### Step 2 — Create compliance dashboard

**Monthly trend for OMB annual report:**
```spl
index=network earliest=-365d
| eval month=strftime(_time, "%Y-%m")
| eval has_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}"), 1, 0)
| stats max(has_ipv6) as ipv6_capable by host, month
| stats count as total dc(eval(if(ipv6_capable=1, host, null()))) as ipv6_hosts by month
| eval ipv6_pct=round(ipv6_hosts / total * 100, 1)
| table month, total, ipv6_hosts, ipv6_pct
```

**IPv4-only remediation list:**
```spl
index=network earliest=-30d
| eval has_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}"), 1, 0)
| stats max(has_ipv6) as ipv6_capable by host
| where ipv6_capable=0
| lookup asset_inventory.csv host OUTPUT asset_type, location, business_unit, waiver
| where waiver!="yes" OR isnull(waiver)
| table host, asset_type, location, business_unit
| sort asset_type, location
```

### Step 3 — Validate
(a) **Accuracy check.** Select 10 random assets from each category. SSH/RDP to each and verify IPv6 status manually (Windows: `ipconfig`; Linux: `ip -6 addr`; IOS: `show ipv6 interface brief`).

(b) **Waiver verification.** Review all waivered assets to confirm documentation is current and the waiver reason is still valid.

(c) **Procurement check.** Verify recent IT acquisitions appear in the IPv6-capable category.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — OMB M-21-07 Compliance"):
- Row 1 — Gauges: FY2025 target (80% IPv6-capable) and FY2028 target (100% IPv6-only).
- Row 2 — Pie chart: asset distribution by IPv6 status.
- Row 3 — Trend: monthly IPv6 adoption progress.
- Row 4 — Table: IPv4-only assets requiring remediation (excluding waivered).
- Row 5 — Table: waivered assets with reason and review date.

**Scheduled report:** Monthly. Send to CIO/CISO office for OMB reporting.

**Alert:** IPv6-capable percentage drops below previous month — indicates regression.

### Step 5 — Troubleshooting

- **Classification accuracy.** The traffic-based classification may miss assets with low traffic volume. Supplement with configuration-based classification and active scanning.

- **Dual-stack vs IPv6-only distinction.** The FY2025 target counts both dual-stack and IPv6-only as 'capable.' The FY2028 target requires IPv6-only. Plan the dual-stack → IPv6-only transition early.

- **Asset inventory completeness.** If the asset inventory is incomplete, the compliance percentage is inaccurate. Cross-reference with CMDB and network discovery tools to ensure coverage.

## SPL

```spl
index=network earliest=-30d
| eval has_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}") OR match(_raw, "(?i)ipv6"), 1, 0)
| eval has_ipv4=if(match(_raw, "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"), 1, 0)
| stats max(has_ipv6) as ipv6_capable max(has_ipv4) as ipv4_present by host
| eval asset_status=case(
    ipv6_capable=1 AND ipv4_present=0, "IPv6-only",
    ipv6_capable=1 AND ipv4_present=1, "Dual-stack",
    ipv6_capable=0 AND ipv4_present=1, "IPv4-only",
    1=1, "Unknown")
| stats count as total_assets count(eval(asset_status="IPv6-only")) as ipv6_only count(eval(asset_status="Dual-stack")) as dual_stack count(eval(asset_status="IPv4-only")) as ipv4_only
| eval fy25_target_pct=80
| eval fy28_target_pct=100
| eval ipv6_capable_pct=round((ipv6_only + dual_stack) / total_assets * 100, 1)
| eval ipv6_only_pct=round(ipv6_only / total_assets * 100, 1)
| eval fy25_compliant=if(ipv6_capable_pct >= 80, "COMPLIANT", "NON-COMPLIANT — " . round(80 - ipv6_capable_pct, 1) . "% below target")
| eval fy28_compliant=if(ipv6_only_pct >= 100, "COMPLIANT", "IN PROGRESS — " . ipv6_only_pct . "% IPv6-only (target: 100%)")
| table total_assets, ipv6_only, dual_stack, ipv4_only, ipv6_capable_pct, ipv6_only_pct, fy25_compliant, fy28_compliant
```

## Visualization

(1) Gauge: IPv6-capable percentage vs 80% target. (2) Gauge: IPv6-only percentage vs 100% target. (3) Pie chart: asset distribution by status. (4) Table: IPv4-only assets requiring remediation. (5) Trend: monthly IPv6 adoption progress.

## Known False Positives

**Network infrastructure devices.** Routers, switches, and firewalls are inherently dual-stack (they must process both IPv4 and IPv6). These should be classified as 'dual-stack capable' rather than penalised for having IPv4.

**Legacy systems with waiver.** OMB M-21-07 allows agencies to retain IPv4 for legacy systems that cannot be migrated, with documentation. Maintain a waiver list and exclude these assets from compliance calculations.

**Monitoring-only IPv4.** Some management protocols (SNMP, legacy monitoring) may use IPv4 while the production traffic is IPv6-only. Classify based on production traffic, not management plane.

## References

- [OMB Memorandum M-21-07 — Completing the Transition to Internet Protocol Version 6 (IPv6)](https://www.whitehouse.gov/wp-content/uploads/2020/11/M-21-07.pdf)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6](https://csrc.nist.gov/publications/detail/sp/800-119/final)
- [USGv6 Program — federal IPv6 conformance and interoperability testing](https://www.nist.gov/programs-projects/usgv6-program)
