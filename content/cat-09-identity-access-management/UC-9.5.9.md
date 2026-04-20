---
id: "9.5.9"
title: "Duo Enrollment Anomalies"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.5.9 · Duo Enrollment Anomalies

## Description

Sudden bulk enrollments or enrollments from unusual locations can indicate attacker-driven device registration or help-desk abuse.

## Value

Sudden bulk enrollments or enrollments from unusual locations can indicate attacker-driven device registration or help-desk abuse.

## Implementation

Ingest Duo admin enrollment events. Baseline enrollment rate per hour per location. Alert on spikes and on enrollments outside business hours. Correlate with HR onboarding feeds when available.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cisco Duo TA.
• Ensure the following data sources are available: `sourcetype=duo:admin`, `sourcetype=duo:authentication` (enrollment events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Duo admin enrollment events. Baseline enrollment rate per hour per location. Alert on spikes and on enrollments outside business hours. Correlate with HR onboarding feeds when available.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=duo sourcetype="duo:admin" event_type="enrollment"
| bin _time span=15m
| stats dc(user) as new_users by _time
| where new_users > 20
```

Understanding this SPL

**Duo Enrollment Anomalies** — Sudden bulk enrollments or enrollments from unusual locations can indicate attacker-driven device registration or help-desk abuse.

Documented **Data sources**: `sourcetype=duo:admin`, `sourcetype=duo:authentication` (enrollment events). **App/TA** (typical add-on context): Cisco Duo TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: duo; **sourcetype**: duo:admin. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=duo, sourcetype="duo:admin". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where new_users > 20` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (enrollments per hour), Table (spike windows), Bar chart (enrollments by integration).

## SPL

```spl
index=duo sourcetype="duo:admin" event_type="enrollment"
| bin _time span=15m
| stats dc(user) as new_users by _time
| where new_users > 20
```

## Visualization

Line chart (enrollments per hour), Table (spike windows), Bar chart (enrollments by integration).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
