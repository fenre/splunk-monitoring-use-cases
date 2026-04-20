---
id: "2.1.24"
title: "ESXi Host NTP Clock Drift"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.24 · ESXi Host NTP Clock Drift

## Description

Clock drift on ESXi hosts causes VM time drift, Kerberos authentication failures, log correlation issues, and vSAN timing problems. NTP misconfiguration is a common root cause of intermittent authentication failures that are difficult to diagnose.

## Value

Clock drift on ESXi hosts causes VM time drift, Kerberos authentication failures, log correlation issues, and vSAN timing problems. NTP misconfiguration is a common root cause of intermittent authentication failures that are difficult to diagnose.

## Implementation

Collect host inventory via Splunk_TA_vmware. Also monitor ESXi syslog for NTP daemon messages. Create a scripted input using `esxcli system time get` via PowerCLI to capture actual time offset. Alert when NTP is not configured or when time offset exceeds 1 second.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, ESXi syslog.
• Ensure the following data sources are available: ESXi syslog, `sourcetype=vmware:inv:hostsystem`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect host inventory via Splunk_TA_vmware. Also monitor ESXi syslog for NTP daemon messages. Create a scripted input using `esxcli system time get` via PowerCLI to capture actual time offset. Alert when NTP is not configured or when time offset exceeds 1 second.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(ntpConfig_server) as ntp_servers, latest(dateTimeInfo_timeZone) as timezone by host
| eval ntp_configured=if(isnotnull(ntp_servers) AND ntp_servers!="", "Yes", "No")
| table host, ntp_configured, ntp_servers, timezone
| sort ntp_configured
```

Understanding this SPL

**ESXi Host NTP Clock Drift** — Clock drift on ESXi hosts causes VM time drift, Kerberos authentication failures, log correlation issues, and vSAN timing problems. NTP misconfiguration is a common root cause of intermittent authentication failures that are difficult to diagnose.

Documented **Data sources**: ESXi syslog, `sourcetype=vmware:inv:hostsystem`. **App/TA** (typical add-on context): `Splunk_TA_vmware`, ESXi syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:hostsystem. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:hostsystem". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **ntp_configured** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **ESXi Host NTP Clock Drift**): table host, ntp_configured, ntp_servers, timezone
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, NTP status, servers), Status grid (NTP health), Gauge (drift in ms).

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
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(ntpConfig_server) as ntp_servers, latest(dateTimeInfo_timeZone) as timezone by host
| eval ntp_configured=if(isnotnull(ntp_servers) AND ntp_servers!="", "Yes", "No")
| table host, ntp_configured, ntp_servers, timezone
| sort ntp_configured
```

## Visualization

Table (host, NTP status, servers), Status grid (NTP health), Gauge (drift in ms).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
