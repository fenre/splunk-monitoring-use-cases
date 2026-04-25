<!-- AUTO-GENERATED from UC-1.2.54.json — DO NOT EDIT -->

---
id: "1.2.54"
title: "Windows Event Forwarding (WEF) Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.54 · Windows Event Forwarding (WEF) Health

## Description

WEF collects events from thousands of endpoints to central collectors. Forwarding failures create visibility gaps across the security monitoring pipeline.

## Value

If WEF is down, a chunk of the estate is dark to SIEM and SOAR even if the hosts are ‘healthy’ in CMDB terms.

## Implementation

Enable Forwarding/Operational log on WEF collectors and clients. EventCode 103=subscription-level error, 105=access denied (Kerberos/permission issue), 111=cannot reach collector. Monitor for expected forwarders going silent — compare against CMDB endpoint list. Alert when error rate exceeds 5% of clients. Use `wecutil gr <subscription>` via scripted input for precise subscription health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Forwarding/Operational` (EventCode 100, 102, 103, 105, 111).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Forwarding/Operational log on WEF collectors and clients. EventCode 103=subscription-level error, 105=access denied (Kerberos/permission issue), 111=cannot reach collector. Monitor for expected forwarders going silent — compare against CMDB endpoint list. Alert when error rate exceeds 5% of clients. Use `wecutil gr <subscription>` via scripted input for precise subscription health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Forwarding/Operational"
  EventCode IN (102, 103, 105, 111)
| eval issue=case(EventCode=102,"Subscription connected",EventCode=103,"Subscription error",EventCode=105,"Access denied",EventCode=111,"Collector unreachable")
| stats count by host, issue, SubscriptionName
| where issue!="Subscription connected"
| sort -count
```

Understanding this SPL

**Windows Event Forwarding (WEF) Health** — WEF collects events from thousands of endpoints to central collectors. Forwarding failures create visibility gaps across the security monitoring pipeline.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Forwarding/Operational` (EventCode 100, 102, 103, 105, 111). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **issue** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, issue, SubscriptionName** so each row reflects one combination of those dimensions.
• Filters the current rows with `where issue!="Subscription connected"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (subscription × host), Pie chart (healthy vs. error), Table (error details), Single value (connected clients).

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
index=wineventlog source="WinEventLog:Microsoft-Windows-Forwarding/Operational"
  EventCode IN (102, 103, 105, 111)
| eval issue=case(EventCode=102,"Subscription connected",EventCode=103,"Subscription error",EventCode=105,"Access denied",EventCode=111,"Collector unreachable")
| stats count by host, issue, SubscriptionName
| where issue!="Subscription connected"
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| where count>0
```

## Visualization

Status grid (subscription × host), Pie chart (healthy vs. error), Table (error details), Single value (connected clients).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
