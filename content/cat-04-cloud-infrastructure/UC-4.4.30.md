---
id: "4.4.30"
title: "Cloud Provider API Rate Limit Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.30 · Cloud Provider API Rate Limit Monitoring

## Description

Automation hitting AWS throttling, Azure 429s, or GCP RESOURCE_EXHAUSTED breaks pipelines; trending limits prevents silent job loss.

## Value

Automation hitting AWS throttling, Azure 429s, or GCP RESOURCE_EXHAUSTED breaks pipelines; trending limits prevents silent job loss.

## Implementation

Back off and jitter in automation based on Splunk alerts. Separate control-plane vs data-plane APIs. Dashboard top callers (principal or workload) causing throttles.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud TAs + application logs with HTTP status.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail` (ThrottlingException), `sourcetype=mscs:azure:audit` / app logs (429), `sourcetype=google:gcp:pubsub:message` (status 429, RESOURCE_EXHAUSTED).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Back off and jitter in automation based on Splunk alerts. Separate control-plane vs data-plane APIs. Dashboard top callers (principal or workload) causing throttles.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=aws sourcetype="aws:cloudtrail" errorCode="Throttling")
 OR (index=azure sourcetype="mscs:azure:audit" status.value="429")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "RESOURCE_EXHAUSTED" OR status="429")
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| timechart span=15m count by provider
```

Understanding this SPL

**Cloud Provider API Rate Limit Monitoring** — Automation hitting AWS throttling, Azure 429s, or GCP RESOURCE_EXHAUSTED breaks pipelines; trending limits prevents silent job loss.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (ThrottlingException), `sourcetype=mscs:azure:audit` / app logs (429), `sourcetype=google:gcp:pubsub:message` (status 429, RESOURCE_EXHAUSTED). **App/TA** (typical add-on context): Cloud TAs + application logs with HTTP status. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:cloudtrail, mscs:azure:audit, google:gcp:pubsub:message. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **provider** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by provider** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (throttle count by provider), Table (API operation, caller, count), Single value (15m throttle burst).

## SPL

```spl
(index=aws sourcetype="aws:cloudtrail" errorCode="Throttling")
 OR (index=azure sourcetype="mscs:azure:audit" status.value="429")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "RESOURCE_EXHAUSTED" OR status="429")
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| timechart span=15m count by provider
```

## Visualization

Line chart (throttle count by provider), Table (API operation, caller, count), Single value (15m throttle burst).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
