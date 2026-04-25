<!-- AUTO-GENERATED from UC-4.4.7.json — DO NOT EDIT -->

---
id: "4.4.7"
title: "Cross-Cloud Log Ingestion Pipeline Health"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.7 · Cross-Cloud Log Ingestion Pipeline Health

## Description

Log pipelines (CloudTrail → S3 → Splunk, Event Hub → Splunk, Pub/Sub → Splunk) can break. Monitoring pipeline health ensures no audit or observability gaps.

## Value

Log pipelines (CloudTrail → S3 → Splunk, Event Hub → Splunk, Pub/Sub → Splunk) can break. Monitoring pipeline health ensures no audit or observability gaps.

## Implementation

Track last event time per cloud sourcetype (e.g. aws:cloudtrail, mscs:azure:audit, google:gcp:pubsub). Alert when no events received for >15–30 minutes. Monitor Event Hub consumer lag and Pub/Sub subscription backlog as pipeline indicators.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk _internal, ingest metrics, or custom heartbeat.
• Ensure the following data sources are available: Splunk ingest metrics (by source/sourcetype), heartbeat searches, or pipeline-specific metrics (e.g. S3 object count, Event Hub lag).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track last event time per cloud sourcetype (e.g. aws:cloudtrail, mscs:azure:audit, google:gcp:pubsub). Alert when no events received for >15–30 minutes. Monitor Event Hub consumer lag and Pub/Sub subscription backlog as pipeline indicators.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=_internal source=*metrics* group=per_sourcetype_thruput
| eval delay_minutes = (now() - _time) / 60
| where delay_minutes > 15 AND (sourcetype=*aws* OR sourcetype=*azure* OR sourcetype=*gcp*)
| table sourcetype last_time delay_minutes
```

Understanding this SPL

**Cross-Cloud Log Ingestion Pipeline Health** — Log pipelines (CloudTrail → S3 → Splunk, Event Hub → Splunk, Pub/Sub → Splunk) can break. Monitoring pipeline health ensures no audit or observability gaps.

Documented **Data sources**: Splunk ingest metrics (by source/sourcetype), heartbeat searches, or pipeline-specific metrics (e.g. S3 object count, Event Hub lag). **App/TA** (typical add-on context): Splunk _internal, ingest metrics, or custom heartbeat. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: _internal.

**Pipeline walkthrough**

• Scopes the data: index=_internal. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **delay_minutes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where delay_minutes > 15 AND (sourcetype=*aws* OR sourcetype=*azure* OR sourcetype=*gcp*)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cross-Cloud Log Ingestion Pipeline Health**): table sourcetype last_time delay_minutes


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (sourcetype, last event, delay), Single value (stale pipelines), Timeline (ingest volume by source).

## SPL

```spl
index=_internal source=*metrics* group=per_sourcetype_thruput
| eval delay_minutes = (now() - _time) / 60
| where delay_minutes > 15 AND (sourcetype=*aws* OR sourcetype=*azure* OR sourcetype=*gcp*)
| table sourcetype last_time delay_minutes
```

## Visualization

Table (sourcetype, last event, delay), Single value (stale pipelines), Timeline (ingest volume by source).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
