<!-- AUTO-GENERATED from UC-4.1.9.json — DO NOT EDIT -->

---
id: "4.1.9"
title: "VPC Flow Log Analysis"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.9 · VPC Flow Log Analysis

## Description

VPC Flow Logs provide network-level visibility into all traffic. Detects rejected traffic, data exfiltration, lateral movement, and network anomalies.

## Value

VPC Flow Logs provide network-level visibility into all traffic. Detects rejected traffic, data exfiltration, lateral movement, and network anomalies.

## Implementation

Enable VPC Flow Logs on all VPCs (send to S3 or CloudWatch Logs). Ingest via Splunk_TA_aws. Create dashboards for rejected traffic, top talkers, and unusual port activity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatchlogs:vpcflow`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable VPC Flow Logs on all VPCs (send to S3 or CloudWatch Logs). Ingest via Splunk_TA_aws. Create dashboards for rejected traffic, top talkers, and unusual port activity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatchlogs:vpcflow" action="REJECT"
| stats count by src, dest, dest_port, protocol
| sort 20 -count
```

Understanding this SPL

**VPC Flow Log Analysis** — VPC Flow Logs provide network-level visibility into all traffic. Detects rejected traffic, data exfiltration, lateral movement, and network anomalies.

Documented **Data sources**: `sourcetype=aws:cloudwatchlogs:vpcflow`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatchlogs:vpcflow. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatchlogs:vpcflow". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, dest, dest_port, protocol** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top rejected flows), Sankey diagram (source to destination), Timechart, Map.

## SPL

```spl
index=aws sourcetype="aws:cloudwatchlogs:vpcflow" action="REJECT"
| stats count by src, dest, dest_port, protocol
| sort 20 -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where like(All_Traffic.action, "%eject%") OR like(lower(All_Traffic.action), "%deny%") OR like(lower(All_Traffic.action), "%block%")
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port All_Traffic.action span=1h
| sort -count
```

## Visualization

Table (top rejected flows), Sankey diagram (source to destination), Timechart, Map.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
