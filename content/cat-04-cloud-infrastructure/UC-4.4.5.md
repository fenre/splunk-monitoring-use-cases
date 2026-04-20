---
id: "4.4.5"
title: "Cloud Resource Inventory and Drift Summary"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.4.5 · Cloud Resource Inventory and Drift Summary

## Description

Unified inventory of resources across AWS/Azure/GCP supports compliance, cost, and drift detection. Drift summary highlights resources changed outside IaC.

## Value

Unified inventory of resources across AWS/Azure/GCP supports compliance, cost, and drift detection. Drift summary highlights resources changed outside IaC.

## Implementation

Export resource inventory from each provider (Config snapshot, Resource Graph query, Asset Inventory API) to S3/storage or stream to Splunk. Normalize resource type and tags. Dashboard resource count by type and cloud. Compare with IaC state for drift.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Combined cloud TAs, Config/Policy exports, or third-party CSPM.
• Ensure the following data sources are available: AWS Config, Azure Resource Graph, GCP Asset Inventory (or provider APIs).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export resource inventory from each provider (Config snapshot, Resource Graph query, Asset Inventory API) to S3/storage or stream to Splunk. Normalize resource type and tags. Dashboard resource count by type and cloud. Compare with IaC state for drift.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws OR index=azure OR index=gcp
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval resource_type=coalesce(resourceType, type, resource.type)
| stats dc(resourceId) as resource_count values(cloud) as clouds by resource_type
| sort -resource_count
```

Understanding this SPL

**Cloud Resource Inventory and Drift Summary** — Unified inventory of resources across AWS/Azure/GCP supports compliance, cost, and drift detection. Drift summary highlights resources changed outside IaC.

Documented **Data sources**: AWS Config, Azure Resource Graph, GCP Asset Inventory (or provider APIs). **App/TA** (typical add-on context): Combined cloud TAs, Config/Policy exports, or third-party CSPM. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cloud** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **resource_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by resource_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (type, cloud, count), Stacked bar (resources by cloud), Pie chart (resource distribution).

## SPL

```spl
index=aws OR index=azure OR index=gcp
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval resource_type=coalesce(resourceType, type, resource.type)
| stats dc(resourceId) as resource_count values(cloud) as clouds by resource_type
| sort -resource_count
```

## Visualization

Table (type, cloud, count), Stacked bar (resources by cloud), Pie chart (resource distribution).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
