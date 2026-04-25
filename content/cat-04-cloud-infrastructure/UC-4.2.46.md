<!-- AUTO-GENERATED from UC-4.2.46.json — DO NOT EDIT -->

---
id: "4.2.46"
title: "Azure Application Gateway and WAF Health"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.2.46 · Azure Application Gateway and WAF Health

## Description

Application Gateway is the primary L7 load balancer for most Azure web workloads. Backend health probe failures cause 502 errors for users; WAF blocks need tuning to avoid false positives.

## Value

Application Gateway is the primary L7 load balancer for most Azure web workloads. Backend health probe failures cause 502 errors for users; WAF blocks need tuning to avoid false positives.

## Implementation

Enable diagnostics on Application Gateway to send access logs and WAF logs via Event Hub or Storage Account to Splunk. Monitor backend pool health probe status from metrics (`UnhealthyHostCount`). Alert on rising 502/504 rates, unhealthy backends, and WAF blocks that correlate with user-reported issues. Track WAF rule hit distribution to tune rule exclusions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric`, `sourcetype=azure:diagnostics` (ApplicationGatewayAccessLog, ApplicationGatewayFirewallLog).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable diagnostics on Application Gateway to send access logs and WAF logs via Event Hub or Storage Account to Splunk. Monitor backend pool health probe status from metrics (`UnhealthyHostCount`). Alert on rising 502/504 rates, unhealthy backends, and WAF blocks that correlate with user-reported issues. Track WAF rule hit distribution to tune rule exclusions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:diagnostics" Category="ApplicationGatewayAccessLog"
| eval is_error=if(httpStatusCode>=500,1,0)
| timechart span=5m count as total_requests, sum(is_error) as server_errors by host
| eval error_pct=round(100*server_errors/total_requests,2)
| where error_pct > 5
```

Understanding this SPL

**Azure Application Gateway and WAF Health** — Application Gateway is the primary L7 load balancer for most Azure web workloads. Backend health probe failures cause 502 errors for users; WAF blocks need tuning to avoid false positives.

Documented **Data sources**: `sourcetype=azure:monitor:metric`, `sourcetype=azure:diagnostics` (ApplicationGatewayAccessLog, ApplicationGatewayFirewallLog). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_error** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **error_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_pct > 5` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Application Gateway and WAF Health** — Application Gateway is the primary L7 load balancer for most Azure web workloads.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (request rate and error rate), Table (unhealthy backends), Bar chart (WAF blocks by rule ID).

## SPL

```spl
index=cloud sourcetype="azure:diagnostics" Category="ApplicationGatewayAccessLog"
| eval is_error=if(httpStatusCode>=500,1,0)
| timechart span=5m count as total_requests, sum(is_error) as server_errors by host
| eval error_pct=round(100*server_errors/total_requests,2)
| where error_pct > 5
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (request rate and error rate), Table (unhealthy backends), Bar chart (WAF blocks by rule ID).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
