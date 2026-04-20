---
id: "1.2.116"
title: "WMI Persistence Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.116 · WMI Persistence Detection

## Description

WMI event subscriptions provide fileless persistence that survives reboots. Detecting WMI persistence reveals advanced persistent threats.

## Value

WMI event subscriptions provide fileless persistence that survives reboots. Detecting WMI persistence reveals advanced persistent threats.

## Implementation

Sysmon EventCodes 19/20/21 track WMI event filter, consumer, and binding creation. Any new WMI subscription (especially CommandLineEventConsumer or ActiveScriptEventConsumer) is suspicious. Filter out known-good subscriptions (BVTFilter, TSLogonFilter). Alert on all new subscriptions and investigate the consumer action. Correlate EventCode 21 (binding) — a complete subscription requires filter + consumer + binding. MITRE ATT&CK T1546.003.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 19, 20, 21).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sysmon EventCodes 19/20/21 track WMI event filter, consumer, and binding creation. Any new WMI subscription (especially CommandLineEventConsumer or ActiveScriptEventConsumer) is suspicious. Filter out known-good subscriptions (BVTFilter, TSLogonFilter). Alert on all new subscriptions and investigate the consumer action. Correlate EventCode 21 (binding) — a complete subscription requires filter + consumer + binding. MITRE ATT&CK T1546.003.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (19, 20, 21)
| eval WMIType=case(EventCode=19,"FilterCreated", EventCode=20,"ConsumerCreated", EventCode=21,"BindingCreated", 1=1,"Other")
| table _time, host, User, WMIType, EventNamespace, Name, Query, Destination, Consumer
| where NOT match(Name, "(?i)(BVTFilter|TSLogonFilter|SCM Event)")
| sort -_time
```

Understanding this SPL

**WMI Persistence Detection** — WMI event subscriptions provide fileless persistence that survives reboots. Detecting WMI persistence reveals advanced persistent threats.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 19, 20, 21). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **WMIType** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **WMI Persistence Detection**): table _time, host, User, WMIType, EventNamespace, Name, Query, Destination, Consumer
• Filters the current rows with `where NOT match(Name, "(?i)(BVTFilter|TSLogonFilter|SCM Event)")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (WMI subscriptions), Alert on creation, Timeline (events).

## SPL

```spl
index=wineventlog EventCode IN (19, 20, 21)
| eval WMIType=case(EventCode=19,"FilterCreated", EventCode=20,"ConsumerCreated", EventCode=21,"BindingCreated", 1=1,"Other")
| table _time, host, User, WMIType, EventNamespace, Name, Query, Destination, Consumer
| where NOT match(Name, "(?i)(BVTFilter|TSLogonFilter|SCM Event)")
| sort -_time
```

## Visualization

Table (WMI subscriptions), Alert on creation, Timeline (events).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
