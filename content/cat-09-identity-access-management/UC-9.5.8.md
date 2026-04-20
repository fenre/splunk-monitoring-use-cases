---
id: "9.5.8"
title: "Duo Device Trust Posture"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.5.8 · Duo Device Trust Posture

## Description

Non-compliant or out-of-date devices that still attempt access signal policy gaps and endpoint risk exposure.

## Value

Non-compliant or out-of-date devices that still attempt access signal policy gaps and endpoint risk exposure.

## Implementation

Ensure device fields (OS, encryption, posture) are extracted from Duo or endpoint telemetry. Alert on repeated access from untrusted posture or when trust level changes. Pair with Duo Device Trust policies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cisco Duo TA.
• Ensure the following data sources are available: `sourcetype=duo:authentication`, `sourcetype=duo:telephony` (device trust), Duo admin logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure device fields (OS, encryption, posture) are extracted from Duo or endpoint telemetry. Alert on repeated access from untrusted posture or when trust level changes. Pair with Duo Device Trust policies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=duo sourcetype="duo:authentication"
| where device_trust_level!="trusted" OR like(lower(_raw),"%unmanaged%")
| stats count by user, device, device_trust_level, application
| where count > 0
| sort -count
```

Understanding this SPL

**Duo Device Trust Posture** — Non-compliant or out-of-date devices that still attempt access signal policy gaps and endpoint risk exposure.

Documented **Data sources**: `sourcetype=duo:authentication`, `sourcetype=duo:telephony` (device trust), Duo admin logs. **App/TA** (typical add-on context): Cisco Duo TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: duo; **sourcetype**: duo:authentication. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=duo, sourcetype="duo:authentication". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where device_trust_level!="trusted" OR like(lower(_raw),"%unmanaged%")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by user, device, device_trust_level, application** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Endpoint.Processes by Processes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Duo Device Trust Posture** — Non-compliant or out-of-date devices that still attempt access signal policy gaps and endpoint risk exposure.

Documented **Data sources**: `sourcetype=duo:authentication`, `sourcetype=duo:telephony` (device trust), Duo admin logs. **App/TA** (typical add-on context): Cisco Duo TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Processes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, device, trust level), Pie chart (trusted vs untrusted attempts), Line chart (untrusted attempts over time).

## SPL

```spl
index=duo sourcetype="duo:authentication"
| where device_trust_level!="trusted" OR like(lower(_raw),"%unmanaged%")
| stats count by user, device, device_trust_level, application
| where count > 0
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Endpoint.Processes by Processes.user | sort - count
```

## Visualization

Table (user, device, trust level), Pie chart (trusted vs untrusted attempts), Line chart (untrusted attempts over time).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
