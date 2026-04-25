<!-- AUTO-GENERATED from UC-6.1.5.json — DO NOT EDIT -->

---
id: "6.1.5"
title: "Replication Lag Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.5 · Replication Lag Monitoring

## Description

Replication lag directly impacts RPO. Monitoring ensures DR readiness and compliance with data protection SLAs.

## Value

Replication lag directly impacts RPO. Monitoring ensures DR readiness and compliance with data protection SLAs.

## Implementation

Poll replication status every 15 minutes. Alert when lag exceeds RPO target (e.g., >60 min for hourly replication). Track replication state (idle, transferring, broken-off) and alert on non-healthy states.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, REST API polling.
• Ensure the following data sources are available: Array replication status (SnapMirror, RecoverPoint, etc.).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll replication status every 15 minutes. Alert when lag exceeds RPO target (e.g., >60 min for hourly replication). Track replication state (idle, transferring, broken-off) and alert on non-healthy states.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:snapmirror"
| eval lag_minutes=lag_time/60
| where lag_minutes > 60
| table _time, source_volume, destination_volume, lag_minutes, state
```

Understanding this SPL

**Replication Lag Monitoring** — Replication lag directly impacts RPO. Monitoring ensures DR readiness and compliance with data protection SLAs.

Documented **Data sources**: Array replication status (SnapMirror, RecoverPoint, etc.). **App/TA** (typical add-on context): Vendor TA, REST API polling. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:snapmirror. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:snapmirror". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **lag_minutes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where lag_minutes > 60` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Replication Lag Monitoring**): table _time, source_volume, destination_volume, lag_minutes, state


Step 3 — Validate
Compare volume, aggregate, or SnapMirror state with NetApp ONTAP System Manager, the ONTAP CLI, or NetApp Active IQ Unified Manager for the same object and interval.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Single value (max replication lag), Table (replication pairs with lag), Line chart (lag over time).

## SPL

```spl
index=storage sourcetype="netapp:ontap:snapmirror"
| eval lag_minutes=lag_time/60
| where lag_minutes > 60
| table _time, source_volume, destination_volume, lag_minutes, state
```

## Visualization

Single value (max replication lag), Table (replication pairs with lag), Line chart (lag over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
