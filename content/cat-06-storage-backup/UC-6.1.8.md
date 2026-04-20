---
id: "6.1.8"
title: "Snapshot Space Consumption"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.8 · Snapshot Space Consumption

## Description

Runaway snapshot growth can consume all available space, causing volume and application outages.

## Value

Runaway snapshot growth can consume all available space, causing volume and application outages.

## Implementation

Poll snapshot usage per volume. Alert when snapshot reserve exceeds threshold (e.g., >20% of volume). Track snapshot count and age. Create scheduled report for snapshot cleanup candidates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, REST API.
• Ensure the following data sources are available: Snapshot usage metrics per volume.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll snapshot usage per volume. Alert when snapshot reserve exceeds threshold (e.g., >20% of volume). Track snapshot count and age. Create scheduled report for snapshot cleanup candidates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:volume"
| eval snap_pct=snapshot_used_bytes/size_total*100
| where snap_pct > 20
| table volume_name, snap_pct, snapshot_used_bytes, snapshot_count
| sort -snap_pct
```

Understanding this SPL

**Snapshot Space Consumption** — Runaway snapshot growth can consume all available space, causing volume and application outages.

Documented **Data sources**: Snapshot usage metrics per volume. **App/TA** (typical add-on context): Vendor TA, REST API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:volume. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:volume". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **snap_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where snap_pct > 20` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Snapshot Space Consumption**): table volume_name, snap_pct, snapshot_used_bytes, snapshot_count
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (snapshot usage by volume), Table (volumes with high snapshot usage), Line chart (snapshot growth trend).

## SPL

```spl
index=storage sourcetype="netapp:ontap:volume"
| eval snap_pct=snapshot_used_bytes/size_total*100
| where snap_pct > 20
| table volume_name, snap_pct, snapshot_used_bytes, snapshot_count
| sort -snap_pct
```

## Visualization

Bar chart (snapshot usage by volume), Table (volumes with high snapshot usage), Line chart (snapshot growth trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
