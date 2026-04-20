---
id: "4.2.31"
title: "Azure Policy Compliance Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.2.31 · Azure Policy Compliance Trending

## Description

Point-in-time compliance misses drift; trending non-compliant resource counts shows whether governance keeps pace with deployments.

## Value

Point-in-time compliance misses drift; trending non-compliant resource counts shows whether governance keeps pace with deployments.

## Implementation

Schedule daily export of compliance snapshot per subscription. Ingest as JSON with timestamp. Alert when rolling 7-day average of non-compliant % increases week over week. Tie to deployment pipelines.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Policy compliance export, `sourcetype=mscs:azure:audit` (policy events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Schedule daily export of compliance snapshot per subscription. Ingest as JSON with timestamp. Alert when rolling 7-day average of non-compliant % increases week over week. Tie to deployment pipelines.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" complianceState="NonCompliant"
| timechart span=1d count by policyDefinitionId
```

Understanding this SPL

**Azure Policy Compliance Trending** — Point-in-time compliance misses drift; trending non-compliant resource counts shows whether governance keeps pace with deployments.

Documented **Data sources**: Policy compliance export, `sourcetype=mscs:azure:audit` (policy events). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by policyDefinitionId** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (non-compliant % over time), Table (policy, delta), Bar chart (top resource types).

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" complianceState="NonCompliant"
| timechart span=1d count by policyDefinitionId
```

## Visualization

Line chart (non-compliant % over time), Table (policy, delta), Bar chart (top resource types).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
