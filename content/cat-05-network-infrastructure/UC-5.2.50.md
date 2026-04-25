<!-- AUTO-GENERATED from UC-5.2.50.json — DO NOT EDIT -->

---
id: "5.2.50"
title: "Check Point CoreXL CPU Distribution (Check Point)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.50 · Check Point CoreXL CPU Distribution (Check Point)

## Description

CoreXL distributes firewall inspection across multiple CPU cores (Firewall Worker instances). Uneven load distribution — where one core saturates while others idle — reduces effective throughput and causes packet drops on that core. This often happens when large flows or specific protocols always hash to the same core. Detecting core imbalance before it causes visible packet loss prevents elusive intermittent connectivity issues.

## Value

CoreXL distributes firewall inspection across multiple CPU cores (Firewall Worker instances). Uneven load distribution — where one core saturates while others idle — reduces effective throughput and causes packet drops on that core. This often happens when large flows or specific protocols always hash to the same core. Detecting core imbalance before it causes visible packet loss prevents elusive intermittent connectivity issues.

## Implementation

Use `fw ctl multik stat` via scripted input (interval 300s) to capture per-core connection counts and CPU. Parse core ID and utilization. Alert when any single core exceeds 85% while the gateway average is below 50% — classic imbalance. Correlate with `fwaccel` to identify non-accelerated heavy flows. Tune CoreXL instance count and affinity after analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259).
• Ensure the following data sources are available: `sourcetype=cp_log` (performance logs), `fw ctl multik stat` via scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use `fw ctl multik stat` via scripted input (interval 300s) to capture per-core connection counts and CPU. Parse core ID and utilization. Alert when any single core exceeds 85% while the gateway average is below 50% — classic imbalance. Correlate with `fwaccel` to identify non-accelerated heavy flows. Tune CoreXL instance count and affinity after analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="cp_log" earliest=-4h
| where match(lower(product),"(?i)corexl|multik|fw_worker")
| eval gw=coalesce(orig, src, hostname)
| eval core_id=coalesce(core_id, fw_instance, worker_id)
| eval cpu_pct=coalesce(cpu_usage, cpu_pct, cpu_util)
| stats avg(cpu_pct) as avg_cpu max(cpu_pct) as max_cpu by gw, core_id
| eventstats avg(avg_cpu) as gw_avg by gw
| eval imbalance=round(max_cpu - gw_avg, 1)
| where imbalance > 30 OR max_cpu > 85
| sort -imbalance
```

Understanding this SPL

**Check Point CoreXL CPU Distribution (Check Point)** — CoreXL distributes firewall inspection across multiple CPU cores (Firewall Worker instances). Uneven load distribution — where one core saturates while others idle — reduces effective throughput and causes packet drops on that core. This often happens when large flows or specific protocols always hash to the same core. Detecting core imbalance before it causes visible packet loss prevents elusive intermittent connectivity issues.

Documented **Data sources**: `sourcetype=cp_log` (performance logs), `fw ctl multik stat` via scripted input. **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: cp_log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="cp_log", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(lower(product),"(?i)corexl|multik|fw_worker")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **gw** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **core_id** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **cpu_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by gw, core_id** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by gw** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **imbalance** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where imbalance > 30 OR max_cpu > 85` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Compare key fields and timestamps in SmartConsole, SmartView, or the gateway’s local view so Splunk and Check Point match for the same events.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (CPU per core), Heatmap (core × time), Table (imbalanced gateways), Line chart (max core CPU trend).

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
| where match(lower(product),"(?i)corexl|multik|fw_worker")
| eval gw=coalesce(orig, src, hostname)
| eval core_id=coalesce(core_id, fw_instance, worker_id)
| eval cpu_pct=coalesce(cpu_usage, cpu_pct, cpu_util)
| stats avg(cpu_pct) as avg_cpu max(cpu_pct) as max_cpu by gw, core_id
| eventstats avg(avg_cpu) as gw_avg by gw
| eval imbalance=round(max_cpu - gw_avg, 1)
| where imbalance > 30 OR max_cpu > 85
| sort -imbalance
```

## Visualization

Bar chart (CPU per core), Heatmap (core × time), Table (imbalanced gateways), Line chart (max core CPU trend).

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
