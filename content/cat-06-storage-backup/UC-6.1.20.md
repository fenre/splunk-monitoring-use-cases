<!-- AUTO-GENERATED from UC-6.1.20.json — DO NOT EDIT -->

---
id: "6.1.20"
title: "iSCSI Session Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.20 · iSCSI Session Monitoring

## Description

Dropped or flapping iSCSI sessions cause path loss and I/O errors. Session count and login state trending validates host-to-array connectivity after network or firmware changes.

## Value

Dropped or flapping iSCSI sessions cause path loss and I/O errors. Session count and login state trending validates host-to-array connectivity after network or firmware changes.

## Implementation

Scripted input on hosts or array API export of active sessions every 5m. Alert on session count drop to zero or vs baseline. Correlate with NIC/link events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, Linux `iscsiadm` scripted input, array iSCSI session API.
• Ensure the following data sources are available: Host `iscsiadm -m session`, array iSCSI session list.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input on hosts or array API export of active sessions every 5m. Alert on session count drop to zero or vs baseline. Correlate with NIC/link events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="iscsi:session"
| bin _time span=5m
| stats dc(session_id) as sessions by host, target_iqn, _time
| eventstats avg(sessions) as baseline by host, target_iqn
| where sessions < baseline OR sessions=0
```

Understanding this SPL

**iSCSI Session Monitoring** — Dropped or flapping iSCSI sessions cause path loss and I/O errors. Session count and login state trending validates host-to-array connectivity after network or firmware changes.

Documented **Data sources**: Host `iscsiadm -m session`, array iSCSI session list. **App/TA** (typical add-on context): Vendor TA, Linux `iscsiadm` scripted input, array iSCSI session API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: iscsi:session. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="iscsi:session". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, target_iqn, _time** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by host, target_iqn** so each row reflects one combination of those dimensions.
• Filters the current rows with `where sessions < baseline OR sessions=0` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Line chart (sessions per host/target), Table (hosts with zero sessions), Single value (total active sessions).

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
index=storage sourcetype="iscsi:session"
| bin _time span=5m
| stats dc(session_id) as sessions by host, target_iqn, _time
| eventstats avg(sessions) as baseline by host, target_iqn
| where sessions < baseline OR sessions=0
```

## Visualization

Line chart (sessions per host/target), Table (hosts with zero sessions), Single value (total active sessions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
