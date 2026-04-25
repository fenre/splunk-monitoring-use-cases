<!-- AUTO-GENERATED from UC-5.2.12.json — DO NOT EDIT -->

---
id: "5.2.12"
title: "NAT Pool Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.12 · NAT Pool Exhaustion

## Description

NAT exhaustion prevents outbound connections. Users lose internet access.

## Value

NAT exhaustion prevents outbound connections. Users lose internet access.

## Implementation

Forward firewall logs. Monitor NAT table usage. Alert on exhaustion messages or >80% utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), syslog.
• Ensure the following data sources are available: Firewall NAT/system logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward firewall logs. Monitor NAT table usage. Alert on exhaustion messages or >80% utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall ("NAT" OR "nat") ("exhausted" OR "allocation failed" OR "out of")
| stats count by host, nat_pool | sort -count
```

Understanding this SPL

**NAT Pool Exhaustion** — NAT exhaustion prevents outbound connections. Users lose internet access.

Documented **Data sources**: Firewall NAT/system logs. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, nat_pool** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per pool, Table, Events timeline.

## SPL

```spl
index=firewall ("NAT" OR "nat") ("exhausted" OR "allocation failed" OR "out of")
| stats count by host, nat_pool | sort -count
```

## Visualization

Gauge per pool, Table, Events timeline.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
