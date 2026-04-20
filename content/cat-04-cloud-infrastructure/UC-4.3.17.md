---
id: "4.3.17"
title: "Cloud Logging Export Sink and Exclusion Filter"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.3.17 · Cloud Logging Export Sink and Exclusion Filter

## Description

Log sink and exclusion changes affect what is exported to Splunk or other destinations. Unauthorized changes create visibility gaps.

## Value

Log sink and exclusion changes affect what is exported to Splunk or other destinations. Unauthorized changes create visibility gaps.

## Implementation

Forward audit logs. Alert on CreateSink, UpdateSink, DeleteSink. Track sink destinations and filters. Ensure critical sinks (e.g. to Pub/Sub for Splunk) are not modified without change control.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Audit logs (logging.googleapis.com).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward audit logs. Alert on CreateSink, UpdateSink, DeleteSink. Track sink destinations and filters. Ensure critical sinks (e.g. to Pub/Sub for Splunk) are not modified without change control.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="logging.googleapis.com" (protoPayload.methodName="CreateSink" OR protoPayload.methodName="UpdateSink" OR protoPayload.methodName="DeleteSink")
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.methodName resource.labels.sink_id
| sort -_time
```

Understanding this SPL

**Cloud Logging Export Sink and Exclusion Filter** — Log sink and exclusion changes affect what is exported to Splunk or other destinations. Unauthorized changes create visibility gaps.

Documented **Data sources**: Audit logs (logging.googleapis.com). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Cloud Logging Export Sink and Exclusion Filter**): table _time protoPayload.authenticationInfo.principalEmail protoPayload.methodName resource.labels.sink_id
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Cloud Logging Export Sink and Exclusion Filter** — Log sink and exclusion changes affect what is exported to Splunk or other destinations. Unauthorized changes create visibility gaps.

Documented **Data sources**: Audit logs (logging.googleapis.com). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (who, what, sink), Timeline (sink changes), Single value (sink count).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="logging.googleapis.com" (protoPayload.methodName="CreateSink" OR protoPayload.methodName="UpdateSink" OR protoPayload.methodName="DeleteSink")
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.methodName resource.labels.sink_id
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Table (who, what, sink), Timeline (sink changes), Single value (sink count).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
