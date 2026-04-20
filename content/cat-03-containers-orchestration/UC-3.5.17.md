---
id: "3.5.17"
title: "Kubernetes Resource Quota and LimitRange Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.5.17 · Kubernetes Resource Quota and LimitRange Compliance

## Description

Kubernetes resource quotas and LimitRanges prevent any single team from monopolizing cluster resources. When a namespace approaches its quota, new pod deployments fail silently — the deployment controller keeps retrying but pods never schedule. Monitoring quota utilization trending per namespace detects teams approaching limits before their deployments start failing, enabling proactive quota adjustment rather than reactive incident response at 2 AM when the next deployment fails.

## Value

Kubernetes resource quotas and LimitRanges prevent any single team from monopolizing cluster resources. When a namespace approaches its quota, new pod deployments fail silently — the deployment controller keeps retrying but pods never schedule. Monitoring quota utilization trending per namespace detects teams approaching limits before their deployments start failing, enabling proactive quota adjustment rather than reactive incident response at 2 AM when the next deployment fails.

## Implementation

Use the OTel Collector's `k8sobjects` receiver to collect ResourceQuota objects from the Kubernetes API. Each ResourceQuota contains `status.used` and `status.hard` for CPU, memory, pods, services, and other resources. Calculate utilization percentage for each resource type per namespace. Alert when any namespace exceeds 75% (warning) or 90% (critical) of any quota dimension. Correlate with FailedScheduling events (from UC-3.5.16) to confirm that quota exhaustion is causing pod scheduling failures. Track quota utilization trends over 30 days to forecast when namespaces will hit limits based on growth rate. Provide monthly capacity reports to platform teams with recommendations for quota adjustments. Also monitor LimitRange violations — pods that request resources outside the defined min/max range fail admission and generate events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Distribution of OpenTelemetry Collector (k8sobjects receiver), Splunk Connect for Kubernetes.
• Ensure the following data sources are available: `sourcetype=kube:objects:resourcequotas`, `sourcetype=kube:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use the OTel Collector's `k8sobjects` receiver to collect ResourceQuota objects from the Kubernetes API. Each ResourceQuota contains `status.used` and `status.hard` for CPU, memory, pods, services, and other resources. Calculate utilization percentage for each resource type per namespace. Alert when any namespace exceeds 75% (warning) or 90% (critical) of any quota dimension. Correlate with FailedScheduling events (from UC-3.5.16) to confirm that quota exhaustion is causing pod scheduling failur…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="kube:objects:resourcequotas"
| spath
| eval cpu_used_pct=round(status.used.cpu*100/status.hard.cpu, 1)
| eval mem_used_pct=round(status.used.memory*100/status.hard.memory, 1)
| eval pods_used_pct=round(status.used.pods*100/status.hard.pods, 1)
| stats latest(cpu_used_pct) as cpu_pct, latest(mem_used_pct) as mem_pct, latest(pods_used_pct) as pods_pct by metadata.namespace, metadata.name
| eval max_util=max(cpu_pct, mem_pct, pods_pct)
| eval risk=case(
    max_util >= 90, "Critical - Near Limit",
    max_util >= 75, "Warning - Approaching Limit",
    max_util >= 50, "Info - Moderate Usage",
    1==1, "OK")
| where risk!="OK"
| table metadata.namespace, metadata.name, cpu_pct, mem_pct, pods_pct, max_util, risk
| sort -max_util
```

Understanding this SPL

**Kubernetes Resource Quota and LimitRange Compliance** — Kubernetes resource quotas and LimitRanges prevent any single team from monopolizing cluster resources. When a namespace approaches its quota, new pod deployments fail silently — the deployment controller keeps retrying but pods never schedule. Monitoring quota utilization trending per namespace detects teams approaching limits before their deployments start failing, enabling proactive quota adjustment rather than reactive incident response at 2 AM when the next deployment…

Documented **Data sources**: `sourcetype=kube:objects:resourcequotas`, `sourcetype=kube:events`. **App/TA** (typical add-on context): Splunk Distribution of OpenTelemetry Collector (k8sobjects receiver), Splunk Connect for Kubernetes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: kube:objects:resourcequotas. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="kube:objects:resourcequotas". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• `eval` defines or adjusts **cpu_used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **mem_used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **pods_used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by metadata.namespace, metadata.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **max_util** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **risk** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where risk!="OK"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubernetes Resource Quota and LimitRange Compliance**): table metadata.namespace, metadata.name, cpu_pct, mem_pct, pods_pct, max_util, risk
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (quota utilization % by namespace), Table (namespaces approaching limits), Heatmap (namespace × resource type utilization), Line chart (quota utilization trend per namespace over 30 days).

## SPL

```spl
index=containers sourcetype="kube:objects:resourcequotas"
| spath
| eval cpu_used_pct=round(status.used.cpu*100/status.hard.cpu, 1)
| eval mem_used_pct=round(status.used.memory*100/status.hard.memory, 1)
| eval pods_used_pct=round(status.used.pods*100/status.hard.pods, 1)
| stats latest(cpu_used_pct) as cpu_pct, latest(mem_used_pct) as mem_pct, latest(pods_used_pct) as pods_pct by metadata.namespace, metadata.name
| eval max_util=max(cpu_pct, mem_pct, pods_pct)
| eval risk=case(
    max_util >= 90, "Critical - Near Limit",
    max_util >= 75, "Warning - Approaching Limit",
    max_util >= 50, "Info - Moderate Usage",
    1==1, "OK")
| where risk!="OK"
| table metadata.namespace, metadata.name, cpu_pct, mem_pct, pods_pct, max_util, risk
| sort -max_util
```

## Visualization

Bar chart (quota utilization % by namespace), Table (namespaces approaching limits), Heatmap (namespace × resource type utilization), Line chart (quota utilization trend per namespace over 30 days).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
