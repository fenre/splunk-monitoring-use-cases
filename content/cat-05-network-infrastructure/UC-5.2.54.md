<!-- AUTO-GENERATED from UC-5.2.54.json — DO NOT EDIT -->

---
id: "5.2.54"
title: "Check Point Gateway Connection Table Utilization (Check Point)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.54 · Check Point Gateway Connection Table Utilization (Check Point)

## Description

Each Check Point gateway has a finite concurrent connection table (configurable, typically 500K–25M depending on appliance). When utilization approaches the limit, new connections are dropped — causing application failures and user complaints. Unlike CPU, connection table exhaustion can happen suddenly during attacks or application bursts with little warning.

## Value

Each Check Point gateway has a finite concurrent connection table (configurable, typically 500K–25M depending on appliance). When utilization approaches the limit, new connections are dropped — causing application failures and user complaints. Unlike CPU, connection table exhaustion can happen suddenly during attacks or application bursts with little warning.

## Implementation

Use `fw tab -t connections -s` via scripted input (every 60s) to capture current and maximum connection counts. Alternatively parse system log messages about connection limits and aggressive aging (automatic cleanup when table is near capacity). Alert at 75% utilization. Page at 90%. Correlate with NAT pool usage and DDoS indicators. Enable aggressive aging thresholds as a safety net but alert when triggered.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259).
• Ensure the following data sources are available: `sourcetype=cp_log` (system/performance logs), `fw tab -t connections -s` via scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use `fw tab -t connections -s` via scripted input (every 60s) to capture current and maximum connection counts. Alternatively parse system log messages about connection limits and aggressive aging (automatic cleanup when table is near capacity). Alert at 75% utilization. Page at 90%. Correlate with NAT pool usage and DDoS indicators. Enable aggressive aging thresholds as a safety net but alert when triggered.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="cp_log" earliest=-4h
| where match(lower(product),"(?i)firewall") AND (match(lower(logdesc),"(?i)connection.*table|conn.*limit|aggressive.aging") OR isnotnull(connections_count))
| eval gw=coalesce(orig, src, hostname)
| eval conn_count=coalesce(connections_count, concurrent_connections)
| eval conn_limit=coalesce(connections_limit, table_limit)
| eval util_pct=if(isnotnull(conn_limit) AND conn_limit>0, round(100*conn_count/conn_limit,1), null())
| stats latest(conn_count) as conns latest(util_pct) as util_pct by gw
| where util_pct > 70 OR match(lower(logdesc),"(?i)aggressive.aging")
| sort -util_pct
```

Understanding this SPL

**Check Point Gateway Connection Table Utilization (Check Point)** — Each Check Point gateway has a finite concurrent connection table (configurable, typically 500K–25M depending on appliance). When utilization approaches the limit, new connections are dropped — causing application failures and user complaints. Unlike CPU, connection table exhaustion can happen suddenly during attacks or application bursts with little warning.

Documented **Data sources**: `sourcetype=cp_log` (system/performance logs), `fw tab -t connections -s` via scripted input. **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: cp_log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="cp_log", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(lower(product),"(?i)firewall") AND (match(lower(logdesc),"(?i)connection.*table|conn.*limit|aggressive.aging") …` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **gw** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **conn_count** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **conn_limit** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by gw** so each row reflects one combination of those dimensions.
• Filters the current rows with `where util_pct > 70 OR match(lower(logdesc),"(?i)aggressive.aging")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Compare key fields and timestamps in SmartConsole, SmartView, or the gateway’s local view so Splunk and Check Point match for the same events.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (connection table utilization %), Line chart (connections over time), Single value (peak utilization today), Table (gateways approaching limit).

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
index=firewall sourcetype="cp_log" earliest=-4h
| where match(lower(product),"(?i)firewall") AND (match(lower(logdesc),"(?i)connection.*table|conn.*limit|aggressive.aging") OR isnotnull(connections_count))
| eval gw=coalesce(orig, src, hostname)
| eval conn_count=coalesce(connections_count, concurrent_connections)
| eval conn_limit=coalesce(connections_limit, table_limit)
| eval util_pct=if(isnotnull(conn_limit) AND conn_limit>0, round(100*conn_count/conn_limit,1), null())
| stats latest(conn_count) as conns latest(util_pct) as util_pct by gw
| where util_pct > 70 OR match(lower(logdesc),"(?i)aggressive.aging")
| sort -util_pct
```

## Visualization

Gauge (connection table utilization %), Line chart (connections over time), Single value (peak utilization today), Table (gateways approaching limit).

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
