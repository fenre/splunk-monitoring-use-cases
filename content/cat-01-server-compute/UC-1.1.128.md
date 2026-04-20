---
id: "1.1.128"
title: "Filesystem Inode Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.128 · Filesystem Inode Exhaustion

## Description

Inode usage approaching 100% blocks file creation even with free disk space. Applications fail with "No space left on device" despite available blocks — a common misdiagnosis.

## Value

Inode usage approaching 100% blocks file creation even with free disk space. Applications fail with "No space left on device" despite available blocks — a common misdiagnosis.

## Implementation

Create a scripted input that runs `df -i` and parses output. Extract Filesystem, Inodes, IUsed, IFree, IUse%, MountedOn. Run every 300 seconds. Set tiered alerts: 80% (warning), 90% (high), 95% (critical). Include `find` or `du --inodes` to identify directories consuming inodes for remediation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `df -i` output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that runs `df -i` and parses output. Extract Filesystem, Inodes, IUsed, IFree, IUse%, MountedOn. Run every 300 seconds. Set tiered alerts: 80% (warning), 90% (high), 95% (critical). Include `find` or `du --inodes` to identify directories consuming inodes for remediation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=df_inode host=*
| stats latest(IUsePct) as inode_pct by host, MountedOn
| where inode_pct > 80
```

Understanding this SPL

**Filesystem Inode Exhaustion** — Inode usage approaching 100% blocks file creation even with free disk space. Applications fail with "No space left on device" despite available blocks — a common misdiagnosis.

Documented **Data sources**: `df -i` output. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: df_inode. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=df_inode. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, MountedOn** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where inode_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (filesystem, host, inode %), Gauge per critical mount, Line chart (inode % over time).

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
index=os sourcetype=df_inode host=*
| stats latest(IUsePct) as inode_pct by host, MountedOn
| where inode_pct > 80
```

## Visualization

Table (filesystem, host, inode %), Gauge per critical mount, Line chart (inode % over time).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
