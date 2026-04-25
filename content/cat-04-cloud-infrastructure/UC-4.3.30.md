<!-- AUTO-GENERATED from UC-4.3.30.json — DO NOT EDIT -->

---
id: "4.3.30"
title: "Security Command Center Findings"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.30 · Security Command Center Findings

## Description

SCC aggregates misconfigurations and threats; operationalizing findings closes gaps faster than periodic console reviews.

## Value

SCC aggregates misconfigurations and threats; operationalizing findings closes gaps faster than periodic console reviews.

## Implementation

Enable continuous export or finding notifications to Pub/Sub. Map categories to owners. Auto-ticket CRITICAL; weekly review HIGH. Deduplicate by finding ID across updates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform` (Pub/Sub export).
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message` (SCC findings JSON), SCC Pub/Sub notifications.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable continuous export or finding notifications to Pub/Sub. Map categories to owners. Auto-ticket CRITICAL; weekly review HIGH. Deduplicate by finding ID across updates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" sourceProperties.ResourceName=*
| spath path=finding
| search finding.state="ACTIVE" (finding.severity="HIGH" OR finding.severity="CRITICAL")
| stats latest(finding.createTime) as seen by finding.category, resource
| sort -seen
```

Understanding this SPL

**Security Command Center Findings** — SCC aggregates misconfigurations and threats; operationalizing findings closes gaps faster than periodic console reviews.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` (SCC findings JSON), SCC Pub/Sub notifications. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform` (Pub/Sub export). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by finding.category, resource** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (category, resource, severity), Bar chart (findings by category), Timeline (new findings).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" sourceProperties.ResourceName=*
| spath path=finding
| search finding.state="ACTIVE" (finding.severity="HIGH" OR finding.severity="CRITICAL")
| stats latest(finding.createTime) as seen by finding.category, resource
| sort -seen
```

## Visualization

Table (category, resource, severity), Bar chart (findings by category), Timeline (new findings).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Vulnerabilities](https://docs.splunk.com/Documentation/CIM/latest/User/Vulnerabilities)
