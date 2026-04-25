<!-- AUTO-GENERATED from UC-3.4.7.json — DO NOT EDIT -->

---
id: "3.4.7"
title: "Registry Image Tag Retention and Orphan Cleanup"
criticality: "low"
splunkPillar: "Observability"
---

# UC-3.4.7 · Registry Image Tag Retention and Orphan Cleanup

## Description

Untagged and old tags consume storage and complicate governance. Tracking supports retention policy tuning and cleanup automation.

## Value

Untagged and old tags consume storage and complicate governance. Tracking supports retention policy tuning and cleanup automation.

## Implementation

List repositories and tags via registry API. Compute tag count and oldest tag age per repo. Report repos with excessive tags or very old tags for retention policy review.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input (registry catalog API).
• Ensure the following data sources are available: Registry catalog, image manifest API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
List repositories and tags via registry API. Compute tag count and oldest tag age per repo. Report repos with excessive tags or very old tags for retention policy review.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="registry:tags"
| eval age_days=round((now()-tag_time)/86400, 0)
| stats count as tag_count, values(tag) as tags by repository
| where tag_count > 100 OR age_days > 90
| table repository tag_count age_days
```

Understanding this SPL

**Registry Image Tag Retention and Orphan Cleanup** — Untagged and old tags consume storage and complicate governance. Tracking supports retention policy tuning and cleanup automation.

Documented **Data sources**: Registry catalog, image manifest API. **App/TA** (typical add-on context): Custom API input (registry catalog API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: registry:tags. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="registry:tags". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **age_days** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by repository** so each row reflects one combination of those dimensions.
• Filters the current rows with `where tag_count > 100 OR age_days > 90` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Registry Image Tag Retention and Orphan Cleanup**): table repository tag_count age_days


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (repository, tag count, oldest tag), Bar chart (tags per repo).

## SPL

```spl
index=containers sourcetype="registry:tags"
| eval age_days=round((now()-tag_time)/86400, 0)
| stats count as tag_count, values(tag) as tags by repository
| where tag_count > 100 OR age_days > 90
| table repository tag_count age_days
```

## Visualization

Table (repository, tag count, oldest tag), Bar chart (tags per repo).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
