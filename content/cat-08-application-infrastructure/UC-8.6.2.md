<!-- AUTO-GENERATED from UC-8.6.2.json — DO NOT EDIT -->

---
id: "8.6.2"
title: "FTP / SFTP Service Availability Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.6.2 · FTP / SFTP Service Availability Monitoring

## Description

FTP and SFTP services support automated file transfer workflows between systems, partners, and legacy integrations. Silent service failures cause missed file deliveries that may not surface until business processes fail downstream. Nagios `check_ftp` provides port-level verification; Splunk replicates this through daemon log monitoring and scripted probes.

## Value

FTP and SFTP services support automated file transfer workflows between systems, partners, and legacy integrations. Silent service failures cause missed file deliveries that may not surface until business processes fail downstream. Nagios `check_ftp` provides port-level verification; Splunk replicates this through daemon log monitoring and scripted probes.

## Implementation

Monitor vsftpd, proftpd, or OpenSSH SFTP subsystem logs via Universal Forwarder. For SFTP (port 22 subsystem), filter syslog for `sftp-server` process events. Alert when no daemon activity is seen for more than 15 minutes on a host expected to serve FTP/SFTP. Supplement with a scripted input using `nc -z -w5 host 21` (FTP) or `nc -z -w5 host 22` (SFTP) logged as synthetic check results. Correlate FTP availability with file-transfer success/failure logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_syslog`, custom scripted input.
• Ensure the following data sources are available: `vsftpd`, `proftpd`, or `openssh-sftp-server` logs; scripted TCP port probe output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor vsftpd, proftpd, or OpenSSH SFTP subsystem logs via Universal Forwarder. For SFTP (port 22 subsystem), filter syslog for `sftp-server` process events. Alert when no daemon activity is seen for more than 15 minutes on a host expected to serve FTP/SFTP. Supplement with a scripted input using `nc -z -w5 host 21` (FTP) or `nc -z -w5 host 22` (SFTP) logged as synthetic check results. Correlate FTP availability with file-transfer success/failure logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| inputlookup ftp_hosts.csv
| fields host, service_name
| join type=left max=1 host [search index=os (sourcetype=vsftpd OR sourcetype=syslog process=sftp-server) earliest=-15m | stats count as ftp_events by host]
| where isnull(ftp_events) OR ftp_events=0
| eval status="FTP_DOWN"
| table host, service_name, status
```

Understanding this SPL

**FTP / SFTP Service Availability Monitoring** — FTP and SFTP services support automated file transfer workflows between systems, partners, and legacy integrations. Silent service failures cause missed file deliveries that may not surface until business processes fail downstream. Nagios `check_ftp` provides port-level verification; Splunk replicates this through daemon log monitoring and scripted probes.

Documented **Data sources**: `vsftpd`, `proftpd`, or `openssh-sftp-server` logs; scripted TCP port probe output. **App/TA** (typical add-on context): `Splunk_TA_syslog`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting.
• Keeps or drops fields with `fields` to shape columns and size.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where isnull(ftp_events) OR ftp_events=0` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **FTP / SFTP Service Availability Monitoring**): table host, service_name, status


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, port, status, last event), Single value (unavailable FTP hosts), Line chart (event rate over time per host), Alert timeline.

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
| inputlookup ftp_hosts.csv
| fields host, service_name
| join type=left max=1 host [search index=os (sourcetype=vsftpd OR sourcetype=syslog process=sftp-server) earliest=-15m | stats count as ftp_events by host]
| where isnull(ftp_events) OR ftp_events=0
| eval status="FTP_DOWN"
| table host, service_name, status
```

## Visualization

Table (host, port, status, last event), Single value (unavailable FTP hosts), Line chart (event rate over time per host), Alert timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
