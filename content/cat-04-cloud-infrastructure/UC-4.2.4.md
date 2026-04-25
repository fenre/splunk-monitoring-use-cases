<!-- AUTO-GENERATED from UC-4.2.4.json — DO NOT EDIT -->

---
id: "4.2.4"
title: "NSG Flow Log Analysis"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.4 · NSG Flow Log Analysis

## Description

NSG Flow Logs provide Azure network-level visibility. Detects blocked traffic, anomalous patterns, and lateral movement within VNets.

## Value

NSG Flow Logs provide Azure network-level visibility. Detects blocked traffic, anomalous patterns, and lateral movement within VNets.

## Implementation

Enable NSG Flow Logs (Version 2) on all NSGs. Send to a storage account. Ingest via Splunk_TA_microsoft-cloudservices. Create dashboards for denied traffic and top talkers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:nsgflowlog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable NSG Flow Logs (Version 2) on all NSGs. Send to a storage account. Ingest via Splunk_TA_microsoft-cloudservices. Create dashboards for denied traffic and top talkers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:nsgflowlog" flowState="D"
| stats count by src, dest, dest_port, protocol
| sort -count | head 20
```

Understanding this SPL

**NSG Flow Log Analysis** — NSG Flow Logs provide Azure network-level visibility. Detects blocked traffic, anomalous patterns, and lateral movement within VNets.

Documented **Data sources**: `sourcetype=mscs:azure:nsgflowlog`. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:nsgflowlog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:nsgflowlog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, dest, dest_port, protocol** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top denied flows), Sankey diagram, Timechart, Map.

## SPL

```spl
index=azure sourcetype="mscs:azure:nsgflowlog" flowState="D"
| stats count by src, dest, dest_port, protocol
| sort -count | head 20
```

## Visualization

Table (top denied flows), Sankey diagram, Timechart, Map.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
