<!-- AUTO-GENERATED from UC-1.1.97.json — DO NOT EDIT -->

---
id: "1.1.97"
title: "CPU C-State Residency Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.97 · CPU C-State Residency Monitoring

## Description

CPU C-state residency tracking optimizes power consumption and identifies power management issues.

## Value

CPU C-state residency tracking optimizes power consumption and identifies power management issues.

## Implementation

Create a scripted input reading CPU idle state residency times. Track time spent in each C-state. Alert when C-state distribution changes unexpectedly, indicating power management changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:cpuidle, /sys/devices/system/cpu/cpu*/cpuidle/state*/`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input reading CPU idle state residency times. Track time spent in each C-state. Alert when C-state distribution changes unexpectedly, indicating power management changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:cpuidle host=*
| stats avg(c_state_time) as avg_time by host, c_state
| eval idle_pct=avg_time/total_time*100
```

Understanding this SPL

**CPU C-State Residency Monitoring** — CPU C-state residency tracking optimizes power consumption and identifies power management issues.

Documented **Data sources**: `sourcetype=custom:cpuidle, /sys/devices/system/cpu/cpu*/cpuidle/state*/`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:cpuidle. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:cpuidle. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, c_state** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **idle_pct** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie Chart, Heatmap

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
index=os sourcetype=custom:cpuidle host=*
| stats avg(c_state_time) as avg_time by host, c_state
| eval idle_pct=avg_time/total_time*100
```

## Visualization

Pie Chart, Heatmap

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
