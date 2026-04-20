---
id: "2.3.16"
title: "Libvirt Daemon Health and Responsiveness"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.3.16 · Libvirt Daemon Health and Responsiveness

## Description

The libvirtd daemon is the management layer for all KVM operations — VM start/stop, migration, storage, networking. If libvirtd hangs or crashes, no VM management operations are possible. Existing VMs keep running but become unmanageable. Detecting libvirtd health issues enables proactive restart before they cascade.

## Value

The libvirtd daemon is the management layer for all KVM operations — VM start/stop, migration, storage, networking. If libvirtd hangs or crashes, no VM management operations are possible. Existing VMs keep running but become unmanageable. Detecting libvirtd health issues enables proactive restart before they cascade.

## Implementation

Monitor libvirtd syslog output for errors. Create a scripted input that runs `virsh list` and measures response time — if it takes >5 seconds, libvirtd is likely overloaded. Also monitor the systemd service status: `systemctl is-active libvirtd`. Alert if libvirtd is not active or response time exceeds 10 seconds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, custom scripted input.
• Ensure the following data sources are available: Syslog, systemd service status, libvirtd response time.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor libvirtd syslog output for errors. Create a scripted input that runs `virsh list` and measures response time — if it takes >5 seconds, libvirtd is likely overloaded. Also monitor the systemd service status: `systemctl is-active libvirtd`. Alert if libvirtd is not active or response time exceeds 10 seconds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "libvirtd" ("error" OR "warning" OR "failed" OR "timed out")
| bin _time span=5m
| stats count as errors by host, _time
| where errors > 5
| table _time, host, errors
```

Understanding this SPL

**Libvirt Daemon Health and Responsiveness** — The libvirtd daemon is the management layer for all KVM operations — VM start/stop, migration, storage, networking. If libvirtd hangs or crashes, no VM management operations are possible. Existing VMs keep running but become unmanageable. Detecting libvirtd health issues enables proactive restart before they cascade.

Documented **Data sources**: Syslog, systemd service status, libvirtd response time. **App/TA** (typical add-on context): `Splunk_TA_nix`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where errors > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Libvirt Daemon Health and Responsiveness**): table _time, host, errors


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator (libvirtd per host), Line chart (response time), Events table (errors).

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
index=os sourcetype=syslog "libvirtd" ("error" OR "warning" OR "failed" OR "timed out")
| bin _time span=5m
| stats count as errors by host, _time
| where errors > 5
| table _time, host, errors
```

## Visualization

Status indicator (libvirtd per host), Line chart (response time), Events table (errors).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
