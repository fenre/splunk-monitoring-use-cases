<!-- AUTO-GENERATED from UC-4.2.55.json — DO NOT EDIT -->

---
id: "4.2.55"
title: "Azure Network Watcher Connection Troubleshooting"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.2.55 · Azure Network Watcher Connection Troubleshooting

## Description

Network Watcher captures flow logs, connection monitors, and packet captures for Azure networks. Proactive monitoring of connectivity test results detects network issues before they impact applications.

## Value

Network Watcher captures flow logs, connection monitors, and packet captures for Azure networks. Proactive monitoring of connectivity test results detects network issues before they impact applications.

## Implementation

Configure Connection Monitor tests for critical network paths (VM-to-VM, VM-to-PaaS, on-prem-to-Azure). Collect `ChecksFailedPercent`, `RoundTripTimeMs`, and `TestResult` metrics. Alert when failed check percentage exceeds threshold or round-trip time degrades significantly. Use NSG flow logs enriched with Traffic Analytics for deeper investigation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:diagnostics` (NetworkSecurityGroupFlowEvent), `sourcetype=azure:monitor:metric` (Connection Monitor).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Connection Monitor tests for critical network paths (VM-to-VM, VM-to-PaaS, on-prem-to-Azure). Collect `ChecksFailedPercent`, `RoundTripTimeMs`, and `TestResult` metrics. Alert when failed check percentage exceeds threshold or round-trip time degrades significantly. Use NSG flow logs enriched with Traffic Analytics for deeper investigation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/networkwatchers/connectionmonitors"
| where metric_name="ChecksFailedPercent"
| timechart span=5m avg(average) as failed_pct by resource_name
| where failed_pct > 10
```

Understanding this SPL

**Azure Network Watcher Connection Troubleshooting** — Network Watcher captures flow logs, connection monitors, and packet captures for Azure networks. Proactive monitoring of connectivity test results detects network issues before they impact applications.

Documented **Data sources**: `sourcetype=azure:diagnostics` (NetworkSecurityGroupFlowEvent), `sourcetype=azure:monitor:metric` (Connection Monitor). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where metric_name="ChecksFailedPercent"` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resource_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where failed_pct > 10` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Network Watcher Connection Troubleshooting** — Network Watcher captures flow logs, connection monitors, and packet captures for Azure networks.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (check failure % by monitor), Table (failing paths), Single value (overall connectivity health).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/networkwatchers/connectionmonitors"
| where metric_name="ChecksFailedPercent"
| timechart span=5m avg(average) as failed_pct by resource_name
| where failed_pct > 10
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (check failure % by monitor), Table (failing paths), Single value (overall connectivity health).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
