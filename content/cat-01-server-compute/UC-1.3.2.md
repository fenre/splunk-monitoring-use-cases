---
id: "1.3.2"
title: "FileVault Encryption Status"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.3.2 · FileVault Encryption Status

## Description

Unencrypted endpoints are a data breach risk if lost or stolen. Compliance requirement for most security frameworks (SOC2, ISO27001, PCI).

## Value

Unencrypted endpoints are a data breach risk if lost or stolen. Compliance requirement for most security frameworks (SOC2, ISO27001, PCI).

## Implementation

Create a scripted input: `fdesetup status`. Run daily. Alert on any endpoint where FileVault is not enabled. Feed into compliance dashboard.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk UF, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (`fdesetup status`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input: `fdesetup status`. Run daily. Alert on any endpoint where FileVault is not enabled. Feed into compliance dashboard.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_filevault host=*
| stats latest(status) as fv_status by host
| where fv_status!="FileVault is On."
```

Understanding this SPL

**FileVault Encryption Status** — Unencrypted endpoints are a data breach risk if lost or stolen. Compliance requirement for most security frameworks (SOC2, ISO27001, PCI).

Documented **Data sources**: Custom scripted input (`fdesetup status`). **App/TA** (typical add-on context): Splunk UF, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: macos_filevault. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=macos_filevault. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where fv_status!="FileVault is On."` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (encrypted vs. not), Table of non-compliant hosts, Single value (compliance %).

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
index=os sourcetype=macos_filevault host=*
| stats latest(status) as fv_status by host
| where fv_status!="FileVault is On."
```

## Visualization

Pie chart (encrypted vs. not), Table of non-compliant hosts, Single value (compliance %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
