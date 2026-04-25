<!-- AUTO-GENERATED from UC-4.6.3.json — DO NOT EDIT -->

---
id: "4.6.3"
title: "Cloud Security Finding Trending"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.6.3 · Cloud Security Finding Trending

## Description

Tracking new versus resolved security findings over time shows whether your cloud security posture is improving and whether scanners or policies are flagging more issues than teams can remediate. Supports executive reporting and backlog triage.

## Value

Tracking new versus resolved security findings over time shows whether your cloud security posture is improving and whether scanners or policies are flagging more issues than teams can remediate. Supports executive reporting and backlog triage.

## Implementation

Map your findings feed so each event represents a finding state change or daily snapshot with Severity and status. For snapshot models, compare consecutive days to derive new and resolved counts via summary search. Align severities (Critical/High/Medium) across clouds for a combined view or use separate panels per provider. Refresh suppression lookups so trends reflect true risk.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: AWS Security Hub, Azure Defender, GCP Security Command Center — forwarded via HEC or add-on.
• Ensure the following data sources are available: `index=cloud sourcetype=aws:securityhub:finding` OR `sourcetype=azure:defender:alert` OR `sourcetype=gcp:scc:finding`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map your findings feed so each event represents a finding state change or daily snapshot with Severity and status. For snapshot models, compare consecutive days to derive new and resolved counts via summary search. Align severities (Critical/High/Medium) across clouds for a combined view or use separate panels per provider. Refresh suppression lookups so trends reflect true risk.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype IN ("aws:securityhub:finding", "azure:defender:alert", "gcp:scc:finding")
| eval status=case(match(WorkflowStatus,"(?i)resolved|archived|suppressed"),"resolved",1=1,"new")
| timechart span=1d count by status
| trendline sma7(new) as new_trend sma7(resolved) as resolved_trend
```

Understanding this SPL

**Cloud Security Finding Trending** — Tracking new versus resolved security findings over time shows whether your cloud security posture is improving and whether scanners or policies are flagging more issues than teams can remediate. Supports executive reporting and backlog triage.

Documented **Data sources**: `index=cloud sourcetype=aws:securityhub:finding` OR `sourcetype=azure:defender:alert` OR `sourcetype=gcp:scc:finding`. **App/TA** (typical add-on context): AWS Security Hub, Azure Defender, GCP Security Command Center — forwarded via HEC or add-on. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud.

**Pipeline walkthrough**

• Scopes the data: index=cloud. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by status** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Cloud Security Finding Trending**): trendline sma7(new) as new_trend sma7(resolved) as resolved_trend


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked column chart (new vs resolved per day), line chart (open critical count trend), area chart (cumulative open findings).

## SPL

```spl
index=cloud sourcetype IN ("aws:securityhub:finding", "azure:defender:alert", "gcp:scc:finding")
| eval status=case(match(WorkflowStatus,"(?i)resolved|archived|suppressed"),"resolved",1=1,"new")
| timechart span=1d count by status
| trendline sma7(new) as new_trend sma7(resolved) as resolved_trend
```

## Visualization

Stacked column chart (new vs resolved per day), line chart (open critical count trend), area chart (cumulative open findings).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
