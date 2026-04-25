<!-- AUTO-GENERATED from UC-6.1.25.json — DO NOT EDIT -->

---
id: "6.1.25"
title: "Snapshot Schedule Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.1.25 · Snapshot Schedule Compliance

## Description

Missed snapshot schedules break backup and rollback expectations. Verifying snapshot recency per policy supports operational and audit requirements.

## Value

Missed snapshot schedules break backup and rollback expectations. Verifying snapshot recency per policy supports operational and audit requirements.

## Implementation

Maintain lookup of expected max age per policy. Compare latest snapshot timestamp to policy. Alert on volumes with no snapshot within SLA window.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, API.
• Ensure the following data sources are available: Snapshot list with create time, policy name.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain lookup of expected max age per policy. Compare latest snapshot timestamp to policy. Alert on volumes with no snapshot within SLA window.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="storage:snapshot"
| stats latest(snapshot_time) as last_snap by volume_name, policy_name
| eval hours_since=round((now()-snapshot_time)/3600,1)
| lookup snapshot_policy_expected policy_name OUTPUT expected_hours_max
| where hours_since > expected_hours_max
```

Understanding this SPL

**Snapshot Schedule Compliance** — Missed snapshot schedules break backup and rollback expectations. Verifying snapshot recency per policy supports operational and audit requirements.

Documented **Data sources**: Snapshot list with create time, policy name. **App/TA** (typical add-on context): Vendor TA, API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: storage:snapshot. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="storage:snapshot". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by volume_name, policy_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **hours_since** — often to normalize units, derive a ratio, or prepare for thresholds.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where hours_since > expected_hours_max` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Table (non-compliant volumes), Single value (policy violations count), Timeline (snapshot completions).

## SPL

```spl
index=storage sourcetype="storage:snapshot"
| stats latest(snapshot_time) as last_snap by volume_name, policy_name
| eval hours_since=round((now()-snapshot_time)/3600,1)
| lookup snapshot_policy_expected policy_name OUTPUT expected_hours_max
| where hours_since > expected_hours_max
```

## Visualization

Table (non-compliant volumes), Single value (policy violations count), Timeline (snapshot completions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
