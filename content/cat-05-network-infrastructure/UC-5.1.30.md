---
id: "5.1.30"
title: "MAC Address Table Capacity"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.30 · MAC Address Table Capacity

## Description

CAM table utilization on switches approaching hardware limits.

## Value

CAM table utilization on switches approaching hardware limits.

## Implementation

Poll dot1qTpFdbTable (count) or parse `show mac address-table count`. Create lookup with switch model→max_mac. Alert when CAM utilization exceeds 75%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: dot1qTpFdbTable count, show mac address-table count.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll dot1qTpFdbTable (count) or parse `show mac address-table count`. Create lookup with switch model→max_mac. Alert when CAM utilization exceeds 75%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=snmp:bridge OR sourcetype=cisco:ios:mac
| eval mac_count=coalesce(fdb_entries, mac_count, 0)
| stats latest(mac_count) as current_mac by host
| lookup mac_limit host OUTPUT max_mac
| eval util_pct=round(current_mac/max_mac*100,1)
| where util_pct > 75
| table host current_mac max_mac util_pct
```

Understanding this SPL

**MAC Address Table Capacity** — CAM table utilization on switches approaching hardware limits.

Documented **Data sources**: dot1qTpFdbTable count, show mac address-table count. **App/TA** (typical add-on context): SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:bridge, cisco:ios:mac. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:bridge. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **mac_count** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where util_pct > 75` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **MAC Address Table Capacity**): table host current_mac max_mac util_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (MAC count over time), Gauge, Table.

## SPL

```spl
index=network sourcetype=snmp:bridge OR sourcetype=cisco:ios:mac
| eval mac_count=coalesce(fdb_entries, mac_count, 0)
| stats latest(mac_count) as current_mac by host
| lookup mac_limit host OUTPUT max_mac
| eval util_pct=round(current_mac/max_mac*100,1)
| where util_pct > 75
| table host current_mac max_mac util_pct
```

## Visualization

Line chart (MAC count over time), Gauge, Table.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
