<!-- AUTO-GENERATED from UC-8.6.1.json — DO NOT EDIT -->

---
id: "8.6.1"
title: "SSH Service Availability Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.1 · SSH Service Availability Monitoring

## Description

SSH is the primary remote administration channel for Linux and Unix servers. An unresponsive SSH daemon locks out operators and often signals broader system distress (OOM, hung kernel, storage full). Nagios `check_ssh` is one of the most universally deployed checks; Splunk replicates it through absence-of-event detection and syslog-based availability trending.

## Value

SSH is the primary remote administration channel for Linux and Unix servers. An unresponsive SSH daemon locks out operators and often signals broader system distress (OOM, hung kernel, storage full). Nagios `check_ssh` is one of the most universally deployed checks; Splunk replicates it through absence-of-event detection and syslog-based availability trending.

## Implementation

Ingest sshd syslog messages (Linux) via Universal Forwarder. Maintain a lookup (`monitored_linux_hosts.csv`) of expected hosts. Use `tstats` or a scheduled search every 5 minutes to detect hosts with no sshd events in the last 10 minutes. Optionally deploy a scripted input that performs a TCP connect to port 22 and logs result (0=up, 1=down) for direct availability data. Alert on SSH_DOWN status for more than 2 consecutive intervals to reduce false positives during restart.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, `Splunk_TA_syslog`.
• Ensure the following data sources are available: `sourcetype=syslog` (sshd messages), scripted input or Stream for TCP/22 probe.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest sshd syslog messages (Linux) via Universal Forwarder. Maintain a lookup (`monitored_linux_hosts.csv`) of expected hosts. Use `tstats` or a scheduled search every 5 minutes to detect hosts with no sshd events in the last 10 minutes. Optionally deploy a scripted input that performs a TCP connect to port 22 and logs result (0=up, 1=down) for direct availability data. Alert on SSH_DOWN status for more than 2 consecutive intervals to reduce false positives during restart.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| inputlookup monitored_linux_hosts.csv
| fields host
| join type=left max=1 host [search index=os sourcetype=syslog process=sshd earliest=-15m | stats count as ssh_events by host]
| where isnull(ssh_events) OR ssh_events=0
| eval status="SSH_DOWN"
| table host, status
```

Understanding this SPL

**SSH Service Availability Monitoring** — SSH is the primary remote administration channel for Linux and Unix servers. An unresponsive SSH daemon locks out operators and often signals broader system distress (OOM, hung kernel, storage full). Nagios `check_ssh` is one of the most universally deployed checks; Splunk replicates it through absence-of-event detection and syslog-based availability trending.

Documented **Data sources**: `sourcetype=syslog` (sshd messages), scripted input or Stream for TCP/22 probe. **App/TA** (typical add-on context): `Splunk_TA_nix`, `Splunk_TA_syslog`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting.
• Keeps or drops fields with `fields` to shape columns and size.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where isnull(ssh_events) OR ssh_events=0` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **SSH Service Availability Monitoring**): table host, status


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (hosts with SSH down), Table (host, last seen, duration down), Timeline (SSH availability per host), Heatmap (host × time availability).

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
| inputlookup monitored_linux_hosts.csv
| fields host
| join type=left max=1 host [search index=os sourcetype=syslog process=sshd earliest=-15m | stats count as ssh_events by host]
| where isnull(ssh_events) OR ssh_events=0
| eval status="SSH_DOWN"
| table host, status
```

## Visualization

Single value (hosts with SSH down), Table (host, last seen, duration down), Timeline (SSH availability per host), Heatmap (host × time availability).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
