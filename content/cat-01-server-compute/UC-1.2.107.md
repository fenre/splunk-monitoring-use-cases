---
id: "1.2.107"
title: "DFS Replication Health Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.107 · DFS Replication Health Monitoring

## Description

DFS-R synchronizes SYSVOL and shared folders across domain controllers and file servers. Replication failures cause inconsistent GPOs and stale data.

## Value

DFS-R synchronizes SYSVOL and shared folders across domain controllers and file servers. Replication failures cause inconsistent GPOs and stale data.

## Implementation

Monitor DFS Replication event log for critical events. EventCode 4012 (DFSR stopped) and 5014 (USN journal wrap) require immediate attention — USN journal wrap can cause full resync. Track staging quota events (4302) to prevent replication stalls. Monitor SYSVOL replication specifically on domain controllers. Alert on replication backlog exceeding threshold via WMI/PowerShell scripted input collecting DFSR WMI counters.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:DFS Replication`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor DFS Replication event log for critical events. EventCode 4012 (DFSR stopped) and 5014 (USN journal wrap) require immediate attention — USN journal wrap can cause full resync. Track staging quota events (4302) to prevent replication stalls. Monitor SYSVOL replication specifically on domain controllers. Alert on replication backlog exceeding threshold via WMI/PowerShell scripted input collecting DFSR WMI counters.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:DFS Replication" EventCode IN (4012, 4302, 4304, 5002, 5008, 5014)
| eval Severity=case(EventCode=4012,"DFSR_Stopped", EventCode=4302,"Staging_Quota_Exceeded", EventCode=4304,"Staging_Cleanup_Failed", EventCode=5002,"Unexpected_Shutdown", EventCode=5008,"Auto_Recovery_Failed", EventCode=5014,"USN_Journal_Wrap", 1=1,"Warning")
| stats count by host, Severity, EventCode
| sort -count
```

Understanding this SPL

**DFS Replication Health Monitoring** — DFS-R synchronizes SYSVOL and shared folders across domain controllers and file servers. Replication failures cause inconsistent GPOs and stale data.

Documented **Data sources**: `sourcetype=WinEventLog:DFS Replication`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, Severity, EventCode** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (replication errors), Timechart (error trend), Alert on critical events.

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
index=wineventlog source="WinEventLog:DFS Replication" EventCode IN (4012, 4302, 4304, 5002, 5008, 5014)
| eval Severity=case(EventCode=4012,"DFSR_Stopped", EventCode=4302,"Staging_Quota_Exceeded", EventCode=4304,"Staging_Cleanup_Failed", EventCode=5002,"Unexpected_Shutdown", EventCode=5008,"Auto_Recovery_Failed", EventCode=5014,"USN_Journal_Wrap", 1=1,"Warning")
| stats count by host, Severity, EventCode
| sort -count
```

## Visualization

Table (replication errors), Timechart (error trend), Alert on critical events.

## References

- [USN journal wrap can cause full resync. Track staging quota events](https://splunkbase.splunk.com/app/4302)
- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
