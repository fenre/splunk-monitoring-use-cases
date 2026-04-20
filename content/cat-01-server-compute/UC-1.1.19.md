---
id: "1.1.19"
title: "Filesystem Read-Only Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.19 · Filesystem Read-Only Detection

## Description

A filesystem remounting as read-only indicates disk failure, corruption, or mount issues. Applications will fail silently when they can't write.

## Value

A filesystem remounting as read-only indicates disk failure, corruption, or mount issues. Applications will fail silently when they can't write.

## Implementation

Forward syslog and dmesg. Create critical alert on read-only remount messages. Also add a scripted input: `mount | grep "ro,"` to periodically verify all expected read-write mounts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Syslog.
• Ensure the following data sources are available: `sourcetype=syslog`, `dmesg`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog and dmesg. Create critical alert on read-only remount messages. Also add a scripted input: `mount | grep "ro,"` to periodically verify all expected read-write mounts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog ("Remounting filesystem read-only" OR "EXT4-fs error" OR "I/O error" OR "read-only file system")
| table _time host _raw
| sort -_time
```

Understanding this SPL

**Filesystem Read-Only Detection** — A filesystem remounting as read-only indicates disk failure, corruption, or mount issues. Applications will fail silently when they can't write.

Documented **Data sources**: `sourcetype=syslog`, `dmesg`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Filesystem Read-Only Detection**): table _time host _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Alert panel (critical), Events list, Host status table.

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
index=os sourcetype=syslog ("Remounting filesystem read-only" OR "EXT4-fs error" OR "I/O error" OR "read-only file system")
| table _time host _raw
| sort -_time
```

## Visualization

Alert panel (critical), Events list, Host status table.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
