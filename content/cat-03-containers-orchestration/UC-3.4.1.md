---
id: "3.4.1"
title: "Image Push/Pull Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.4.1 · Image Push/Pull Audit

## Description

Audit trail for who pushed or pulled what images. Detects unauthorized access, supply chain concerns, and usage patterns.

## Value

Audit trail for who pushed or pulled what images. Detects unauthorized access, supply chain concerns, and usage patterns.

## Implementation

Configure registry webhooks (Harbor, ACR, ECR) to send events to Splunk HEC. Alternatively, poll registry API for audit logs. Track push events (new deployments) and pull events (consumption).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Registry webhook to Splunk HEC, API polling.
• Ensure the following data sources are available: Registry audit/webhook events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure registry webhooks (Harbor, ACR, ECR) to send events to Splunk HEC. Alternatively, poll registry API for audit logs. Track push events (new deployments) and pull events (consumption).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="registry:audit"
| stats count by action, repository, tag, user
| sort -count
```

Understanding this SPL

**Image Push/Pull Audit** — Audit trail for who pushed or pulled what images. Detects unauthorized access, supply chain concerns, and usage patterns.

Documented **Data sources**: Registry audit/webhook events. **App/TA** (typical add-on context): Registry webhook to Splunk HEC, API polling. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: registry:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="registry:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by action, repository, tag, user** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, image, action, time), Bar chart by repository, Timeline.

## SPL

```spl
index=containers sourcetype="registry:audit"
| stats count by action, repository, tag, user
| sort -count
```

## Visualization

Table (user, image, action, time), Bar chart by repository, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
