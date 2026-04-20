---
id: "5.1.29"
title: "ARP Table Size Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.29 · ARP Table Size Trending

## Description

ARP table approaching hardware limits; can cause connectivity failures.

## Value

ARP table approaching hardware limits; can cause connectivity failures.

## Implementation

Poll ipNetToMediaTable (count rows) or parse `show ip arp` / `show arp` output via scripted input. Create lookup with device→max_arp (from vendor specs). Alert when utilization exceeds 70%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: ipNetToMediaTable entries count, show arp count.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll ipNetToMediaTable (count rows) or parse `show ip arp` / `show arp` output via scripted input. Create lookup with device→max_arp (from vendor specs). Alert when utilization exceeds 70%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=snmp:arp OR sourcetype=cisco:ios:arp
| eval arp_count=coalesce(arp_entries, arp_count, 0)
| stats latest(arp_count) as current_arp by host
| lookup arp_limit host OUTPUT max_arp
| eval util_pct=round(current_arp/max_arp*100,1)
| where util_pct > 70
| table host current_arp max_arp util_pct
```

Understanding this SPL

**ARP Table Size Trending** — ARP table approaching hardware limits; can cause connectivity failures.

Documented **Data sources**: ipNetToMediaTable entries count, show arp count. **App/TA** (typical add-on context): SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:arp, cisco:ios:arp. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:arp. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **arp_count** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where util_pct > 70` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **ARP Table Size Trending**): table host current_arp max_arp util_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (ARP count over time), Gauge (utilization), Table.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=network sourcetype=snmp:arp OR sourcetype=cisco:ios:arp
| eval arp_count=coalesce(arp_entries, arp_count, 0)
| stats latest(arp_count) as current_arp by host
| lookup arp_limit host OUTPUT max_arp
| eval util_pct=round(current_arp/max_arp*100,1)
| where util_pct > 70
| table host current_arp max_arp util_pct
```

## Visualization

Line chart (ARP count over time), Gauge (utilization), Table.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
