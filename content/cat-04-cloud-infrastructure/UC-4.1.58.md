<!-- AUTO-GENERATED from UC-4.1.58.json — DO NOT EDIT -->

---
id: "4.1.58"
title: "AWS Transit Gateway Attachment Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.58 · AWS Transit Gateway Attachment Health

## Description

TGW route propagation and attachment state affect cross-VPC and hybrid connectivity. Failed attachments or stale routes cause network outages.

## Value

TGW route propagation and attachment state affect cross-VPC and hybrid connectivity. Failed attachments or stale routes cause network outages.

## Implementation

Enable AWS Config for TGW attachments to track state changes. Ingest TGW flow logs to S3 and forward to Splunk for traffic analysis. Collect CloudWatch TGW metrics (BytesIn, BytesOut) per attachment. Alert when attachment state is not available or traffic drops to zero unexpectedly. Correlate with route table propagation events. Use for hybrid connectivity and SD-WAN monitoring.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: AWS Config (TGW attachment compliance), TGW flow logs, CloudWatch TGW metrics (BytesIn, BytesOut, PacketsIn, PacketsOut).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable AWS Config for TGW attachments to track state changes. Ingest TGW flow logs to S3 and forward to Splunk for traffic analysis. Collect CloudWatch TGW metrics (BytesIn, BytesOut) per attachment. Alert when attachment state is not available or traffic drops to zero unexpectedly. Correlate with route table propagation events. Use for hybrid connectivity and SD-WAN monitoring.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws (sourcetype="aws:config:notification" resourceType="AWS::EC2::TransitGatewayAttachment" OR (sourcetype="aws:cloudwatch" namespace="AWS/TransitGateway" metric_name="BytesIn"))
| eval attachment_state=case(
  configurationItemStatus="ResourceDeleted", "deleted",
  configurationItemStatus="ResourceNotRecorded", "unknown",
  configurationItemStatus="OK", "ok",
  isnotnull(configurationItemStatus), configurationItemStatus,
  1=1, null())
| eval resourceId=coalesce(resourceId, resource_id)
| stats latest(attachment_state) as state, latest(Sum) as bytes_in by resourceId, bin(_time, 1h)
| where (isnotnull(state) AND state!="ok") OR (isnotnull(bytes_in) AND bytes_in=0)
| table _time resourceId state bytes_in
| sort -_time
```

Understanding this SPL

**AWS Transit Gateway Attachment Health** — TGW route propagation and attachment state affect cross-VPC and hybrid connectivity. Failed attachments or stale routes cause network outages.

Documented **Data sources**: AWS Config (TGW attachment compliance), TGW flow logs, CloudWatch TGW metrics (BytesIn, BytesOut, PacketsIn, PacketsOut). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:notification, AWS::EC2::TransitGatewayAttachment, aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **attachment_state** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **resourceId** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by resourceId, bin(_time, 1h)** so each row reflects one combination of those dimensions.
• Filters the current rows with `where (isnotnull(state) AND state!="ok") OR (isnotnull(bytes_in) AND bytes_in=0)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **AWS Transit Gateway Attachment Health**): table _time resourceId state bytes_in
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (attachment, state, traffic), Status grid (attachment health), Line chart (bytes in/out by attachment).

## SPL

```spl
index=aws (sourcetype="aws:config:notification" resourceType="AWS::EC2::TransitGatewayAttachment" OR (sourcetype="aws:cloudwatch" namespace="AWS/TransitGateway" metric_name="BytesIn"))
| eval attachment_state=case(
  configurationItemStatus="ResourceDeleted", "deleted",
  configurationItemStatus="ResourceNotRecorded", "unknown",
  configurationItemStatus="OK", "ok",
  isnotnull(configurationItemStatus), configurationItemStatus,
  1=1, null())
| eval resourceId=coalesce(resourceId, resource_id)
| stats latest(attachment_state) as state, latest(Sum) as bytes_in by resourceId, bin(_time, 1h)
| where (isnotnull(state) AND state!="ok") OR (isnotnull(bytes_in) AND bytes_in=0)
| table _time resourceId state bytes_in
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as peak
  from datamodel=Performance.Performance
  by Performance.object Performance.host span=1h
| where isnotnull(peak)
| sort - peak
```

## Visualization

Table (attachment, state, traffic), Status grid (attachment health), Line chart (bytes in/out by attachment).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
