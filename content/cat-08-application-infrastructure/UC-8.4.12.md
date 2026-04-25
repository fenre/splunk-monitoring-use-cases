<!-- AUTO-GENERATED from UC-8.4.12.json — DO NOT EDIT -->

---
id: "8.4.12"
title: "Apigee Policy Violations"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.4.12 · Apigee Policy Violations

## Description

Apigee analytics API or syslog with `fault` policy name (SOAPThreat, JSONThreat, Quota, SpikeArrest) for blocked requests.

## Value

Apigee analytics API or syslog with `fault` policy name (SOAPThreat, JSONThreat, Quota, SpikeArrest) for blocked requests.

## Implementation

Ingest nightly or hourly analytics. Alert on new fault_policy or high `SpikeArrest` counts. Tune policies vs false positives.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Apigee export (BigQuery/Splunk), `apigee:analytics`.
• Ensure the following data sources are available: `fault` policy, `developer_app`, `response_status_code`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest nightly or hourly analytics. Alert on new fault_policy or high `SpikeArrest` counts. Tune policies vs false positives.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="apigee:analytics"
| where isnotnull(fault_policy) OR response_status_code="429"
| stats count by fault_policy, proxy_name, developer_app
| sort -count
```

Understanding this SPL

**Apigee Policy Violations** — Apigee analytics API or syslog with `fault` policy name (SOAPThreat, JSONThreat, Quota, SpikeArrest) for blocked requests.

Documented **Data sources**: `fault` policy, `developer_app`, `response_status_code`. **App/TA** (typical add-on context): Apigee export (BigQuery/Splunk), `apigee:analytics`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: apigee:analytics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="apigee:analytics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where isnotnull(fault_policy) OR response_status_code="429"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by fault_policy, proxy_name, developer_app** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (faults by policy), Table (proxy, policy, count), Line chart (policy violations over time).

## SPL

```spl
index=api sourcetype="apigee:analytics"
| where isnotnull(fault_policy) OR response_status_code="429"
| stats count by fault_policy, proxy_name, developer_app
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - count
```

## Visualization

Bar chart (faults by policy), Table (proxy, policy, count), Line chart (policy violations over time).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
