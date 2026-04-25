<!-- AUTO-GENERATED from UC-1.1.35.json — DO NOT EDIT -->

---
id: "1.1.35"
title: "LVM Thin Pool Capacity Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.35 · LVM Thin Pool Capacity Monitoring

## Description

Thin pool exhaustion causes I/O errors on all logical volumes in the pool, causing application failures.

## Value

Thin pool exhaustion causes I/O errors on all logical volumes in the pool, causing application failures.

## Implementation

Create a scripted input running 'lvs' to extract thin pool metrics. Monitor Data% and Metadata% separately. Alert at 80% capacity and again at 95%, with escalation at 99%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:lvm_thin, lvs output`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input running 'lvs' to extract thin pool metrics. Monitor Data% and Metadata% separately. Alert at 80% capacity and again at 95%, with escalation at 99%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:lvm_thin host=*
| stats latest(data_percent) as pool_usage by host, pool_name
| where pool_usage > 80
```

Understanding this SPL

**LVM Thin Pool Capacity Monitoring** — Thin pool exhaustion causes I/O errors on all logical volumes in the pool, causing application failures.

Documented **Data sources**: `sourcetype=custom:lvm_thin, lvs output`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:lvm_thin. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:lvm_thin. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, pool_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where pool_usage > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Single Value

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
index=os sourcetype=custom:lvm_thin host=*
| stats latest(data_percent) as pool_usage by host, pool_name
| where pool_usage > 80
```

## Visualization

Gauge, Single Value

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
