---
id: "5.2.49"
title: "Check Point SecureXL Acceleration Status (Check Point)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.49 · Check Point SecureXL Acceleration Status (Check Point)

## Description

SecureXL offloads connection handling from the firewall kernel to an acceleration layer, increasing throughput by 2–10×. When SecureXL cannot accelerate a connection (due to complex NAT, certain blade inspections, or resource limits), traffic falls back to the slow path (Firewall kernel or even Medium path). A rising percentage of non-accelerated connections signals policy complexity growth, blade misconfiguration, or capacity limits — reducing effective throughput well before CPU saturation appears.

## Value

SecureXL offloads connection handling from the firewall kernel to an acceleration layer, increasing throughput by 2–10×. When SecureXL cannot accelerate a connection (due to complex NAT, certain blade inspections, or resource limits), traffic falls back to the slow path (Firewall kernel or even Medium path). A rising percentage of non-accelerated connections signals policy complexity growth, blade misconfiguration, or capacity limits — reducing effective throughput well before CPU saturation appears.

## Implementation

Use `fwaccel stat` and `fwaccel conns` via scripted input on the gateway (every 5 min) or parse SecureXL log messages from system events. Baseline accelerated vs slow-path ratio per gateway. Alert when slow-path percentage exceeds 30% sustained for 1 hour. Correlate with policy install events (UC-5.2.48) — new rules with unsupported features often shift traffic to slow path. Report on acceleration trends after blade enablement changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259).
• Ensure the following data sources are available: `sourcetype=cp_log` (performance/system logs), `fwaccel` CLI output via scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use `fwaccel stat` and `fwaccel conns` via scripted input on the gateway (every 5 min) or parse SecureXL log messages from system events. Baseline accelerated vs slow-path ratio per gateway. Alert when slow-path percentage exceeds 30% sustained for 1 hour. Correlate with policy install events (UC-5.2.48) — new rules with unsupported features often shift traffic to slow path. Report on acceleration trends after blade enablement changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(product),"(?i)securexl|fwaccel") OR match(lower(logdesc),"(?i)accel|template|f2f|medium.path|pxl")
| eval gw=coalesce(orig, src, hostname)
| eval path=case(
    match(lower(_raw),"(?i)accel|template"),"accelerated",
    match(lower(_raw),"(?i)medium.path|pxl"),"medium_path",
    match(lower(_raw),"(?i)f2f|slow|firewall.path"),"slow_path",
    1=1,"unknown")
| stats count by gw, path
| eventstats sum(count) as total by gw
| eval pct=round(100*count/total,1)
| where path!="accelerated" AND pct>20
```

Understanding this SPL

**Check Point SecureXL Acceleration Status (Check Point)** — SecureXL offloads connection handling from the firewall kernel to an acceleration layer, increasing throughput by 2–10×. When SecureXL cannot accelerate a connection (due to complex NAT, certain blade inspections, or resource limits), traffic falls back to the slow path (Firewall kernel or even Medium path). A rising percentage of non-accelerated connections signals policy complexity growth, blade misconfiguration, or capacity limits — reducing effective throughput well…

Documented **Data sources**: `sourcetype=cp_log` (performance/system logs), `fwaccel` CLI output via scripted input. **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: cp_log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="cp_log", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(lower(product),"(?i)securexl|fwaccel") OR match(lower(logdesc),"(?i)accel|template|f2f|medium.path|pxl")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **gw** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **path** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by gw, path** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by gw** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where path!="accelerated" AND pct>20` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Performance.All_Performance
  by All_Performance.dest span=1h
```

Understanding this CIM / accelerated SPL

**Check Point SecureXL Acceleration Status (Check Point)** — SecureXL offloads connection handling from the firewall kernel to an acceleration layer, increasing throughput by 2–10×. When SecureXL cannot accelerate a connection (due to complex NAT, certain blade inspections, or resource limits), traffic falls back to the slow path (Firewall kernel or even Medium path). A rising percentage of non-accelerated connections signals policy complexity growth, blade misconfiguration, or capacity limits — reducing effective throughput well…

Documented **Data sources**: `sourcetype=cp_log` (performance/system logs), `fwaccel` CLI output via scripted input. **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.All_Performance` — enable acceleration for that model.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (accelerated vs medium vs slow path), Line chart (acceleration ratio over time), Table (gateways with low acceleration), Bar chart (slow-path reasons).

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
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(product),"(?i)securexl|fwaccel") OR match(lower(logdesc),"(?i)accel|template|f2f|medium.path|pxl")
| eval gw=coalesce(orig, src, hostname)
| eval path=case(
    match(lower(_raw),"(?i)accel|template"),"accelerated",
    match(lower(_raw),"(?i)medium.path|pxl"),"medium_path",
    match(lower(_raw),"(?i)f2f|slow|firewall.path"),"slow_path",
    1=1,"unknown")
| stats count by gw, path
| eventstats sum(count) as total by gw
| eval pct=round(100*count/total,1)
| where path!="accelerated" AND pct>20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Performance.All_Performance
  by All_Performance.dest span=1h
```

## Visualization

Pie chart (accelerated vs medium vs slow path), Line chart (acceleration ratio over time), Table (gateways with low acceleration), Bar chart (slow-path reasons).

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
