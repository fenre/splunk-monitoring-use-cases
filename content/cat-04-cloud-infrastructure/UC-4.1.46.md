---
id: "4.1.46"
title: "Direct Connect Virtual Interface BGP State"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.1.46 · Direct Connect Virtual Interface BGP State

## Description

BGP down on Direct Connect breaks hybrid connectivity. Monitoring BGP session state ensures quick detection and carrier escalation.

## Value

BGP down on Direct Connect breaks hybrid connectivity. Monitoring BGP session state ensures quick detection and carrier escalation.

## Implementation

ConnectionState 1 = available. Alert when state changes to down or unknown. For BGP specifically, use Direct Connect LAG/connection health or partner/carrier APIs if AWS metrics are insufficient.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Direct Connect metrics (ConnectionState, VirtualInterfaceState), or custom script polling DescribeVirtualInterfaces.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
ConnectionState 1 = available. Alert when state changes to down or unknown. For BGP specifically, use Direct Connect LAG/connection health or partner/carrier APIs if AWS metrics are insufficient.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DX" metric_name="ConnectionState"
| where Average != 1
| table _time VirtualInterfaceId ConnectionState
```

Understanding this SPL

**Direct Connect Virtual Interface BGP State** — BGP down on Direct Connect breaks hybrid connectivity. Monitoring BGP session state ensures quick detection and carrier escalation.

Documented **Data sources**: CloudWatch Direct Connect metrics (ConnectionState, VirtualInterfaceState), or custom script polling DescribeVirtualInterfaces. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Average != 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Direct Connect Virtual Interface BGP State**): table _time VirtualInterfaceId ConnectionState


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel (connection state), Table (VIF, state), Timeline (state changes).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DX" metric_name="ConnectionState"
| where Average != 1
| table _time VirtualInterfaceId ConnectionState
```

## Visualization

Status panel (connection state), Table (VIF, state), Timeline (state changes).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
