---
id: "4.2.1"
title: "Azure Activity Log Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.2.1 · Azure Activity Log Monitoring

## Description

Activity Log captures all control plane operations across Azure subscriptions. Essential audit trail for resource management and compliance.

## Value

Activity Log captures all control plane operations across Azure subscriptions. Essential audit trail for resource management and compliance.

## Implementation

Configure Azure Event Hub to receive Activity Log events. Set up Splunk_TA_microsoft-cloudservices with Event Hub input (connection string, consumer group). Alert on critical operations (resource deletions, policy changes).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:audit`, Azure Activity Log via Event Hub.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Azure Event Hub to receive Activity Log events. Set up Splunk_TA_microsoft-cloudservices with Event Hub input (connection string, consumer group). Alert on critical operations (resource deletions, policy changes).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" operationName.value="*delete*" OR operationName.value="*write*"
| stats count by caller, operationName.value, resourceGroupName, status.value
| sort -count
```

Understanding this SPL

**Azure Activity Log Monitoring** — Activity Log captures all control plane operations across Azure subscriptions. Essential audit trail for resource management and compliance.

Documented **Data sources**: `sourcetype=mscs:azure:audit`, Azure Activity Log via Event Hub. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by caller, operationName.value, resourceGroupName, status.value** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Azure Activity Log Monitoring** — Activity Log captures all control plane operations across Azure subscriptions. Essential audit trail for resource management and compliance.

Documented **Data sources**: `sourcetype=mscs:azure:audit`, Azure Activity Log via Event Hub. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (caller, operation, resource, status), Timeline, Bar chart by operation.

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" operationName.value="*delete*" OR operationName.value="*write*"
| stats count by caller, operationName.value, resourceGroupName, status.value
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Table (caller, operation, resource, status), Timeline, Bar chart by operation.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
