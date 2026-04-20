---
id: "4.2.45"
title: "Azure Container Instances Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.45 · Azure Container Instances Health

## Description

ACI containers are short-lived and opaque without platform metrics; monitoring restarts and resource exhaustion preserves burst workloads and integrations.

## Value

ACI containers are short-lived and opaque without platform metrics; monitoring restarts and resource exhaustion preserves burst workloads and integrations.

## Implementation

Route Azure Monitor metrics for Container Instances to Splunk using the Azure Add-on (Event Hub or metrics export). Enable diagnostic logs for container groups. Normalize `resource_name` to container group. Alert on CPU/memory threshold breaches, exit code non-zero patterns in logs, and restart counts from platform events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` or `sourcetype=azure:diagnostics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Route Azure Monitor metrics for Container Instances to Splunk using the Azure Add-on (Event Hub or metrics export). Enable diagnostic logs for container groups. Normalize `resource_name` to container group. Alert on CPU/memory threshold breaches, exit code non-zero patterns in logs, and restart counts from platform events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.containerinstance/containergroups"
| stats avg(average) as cpu_avg, max(maximum) as cpu_peak by resource_name, resource_group
| join type=left max=1 resource_name [
    search index=cloud sourcetype="azure:diagnostics" Category="ContainerInstanceLog"
    | where match(_raw, "(?i)error|fail|OOM")
    | stats count as log_errors by resource_name
]
| where cpu_peak>85 OR log_errors>0
| sort -cpu_peak
```

Understanding this SPL

**Azure Container Instances Health** — ACI containers are short-lived and opaque without platform metrics; monitoring restarts and resource exhaustion preserves burst workloads and integrations.

Documented **Data sources**: `sourcetype=azure:monitor:metric` or `sourcetype=azure:diagnostics`. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource_name, resource_group** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where cpu_peak>85 OR log_errors>0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU/memory over time), Table (container group, region, state), Bar chart (events by group).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.containerinstance/containergroups"
| stats avg(average) as cpu_avg, max(maximum) as cpu_peak by resource_name, resource_group
| join type=left max=1 resource_name [
    search index=cloud sourcetype="azure:diagnostics" Category="ContainerInstanceLog"
    | where match(_raw, "(?i)error|fail|OOM")
    | stats count as log_errors by resource_name
]
| where cpu_peak>85 OR log_errors>0
| sort -cpu_peak
```

## Visualization

Line chart (CPU/memory over time), Table (container group, region, state), Bar chart (events by group).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
