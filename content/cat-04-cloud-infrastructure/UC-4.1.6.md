<!-- AUTO-GENERATED from UC-4.1.6.json — DO NOT EDIT -->

---
id: "4.1.6"
title: "EC2 Instance State Changes"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.6 · EC2 Instance State Changes

## Description

Tracks instance lifecycle for audit and change management. Unexpected terminations indicate accidents, auto-scaling issues, or attacks.

## Value

Tracks instance lifecycle for audit and change management. Unexpected terminations indicate accidents, auto-scaling issues, or attacks.

## Implementation

Ingest CloudTrail via the Splunk Add-on for AWS (`Splunk_TA_aws`) using the S3/SQS input from the organization trail. Alert on `TerminateInstances` where `requestParameters.instancesSet.items{}.instanceId` matches production-tagged instances from a `prod_instances` lookup. Suppress alerts during Auto Scaling scale-in events by checking `userIdentity.invokedBy=autoscaling.amazonaws.com`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CloudTrail via the Splunk Add-on for AWS (`Splunk_TA_aws`) using the S3/SQS input from the organization trail. Alert on `TerminateInstances` where `requestParameters.instancesSet.items{}.instanceId` matches production-tagged instances from a `prod_instances` lookup. Suppress alerts during Auto Scaling scale-in events by checking `userIdentity.invokedBy=autoscaling.amazonaws.com`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" (eventName="RunInstances" OR eventName="TerminateInstances" OR eventName="StopInstances" OR eventName="StartInstances")
| table _time userIdentity.arn eventName requestParameters.instancesSet.items{}.instanceId responseElements.instancesSet.items{}.currentState.name
| sort -_time
```

Understanding this SPL

**EC2 Instance State Changes** — Tracks instance lifecycle for audit and change management. Unexpected terminations indicate accidents, auto-scaling issues, or attacks.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **EC2 Instance State Changes**): table _time userIdentity.arn eventName requestParameters.instancesSet.items{}.instanceId responseElements.instancesSet.items{}.currentSta…
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where All_Changes.object_category="instance" OR match(All_Changes.object, "(?i)ec2:|i-[0-9a-f]{8,17}")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**EC2 Instance State Changes** — Tracks instance lifecycle for audit and change management. Unexpected terminations indicate accidents, auto-scaling issues, or attacks.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (timeline), Bar chart (events by type per day), Line chart (instance count trending).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" (eventName="RunInstances" OR eventName="TerminateInstances" OR eventName="StopInstances" OR eventName="StartInstances")
| table _time userIdentity.arn eventName requestParameters.instancesSet.items{}.instanceId responseElements.instancesSet.items{}.currentState.name
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where All_Changes.object_category="instance" OR match(All_Changes.object, "(?i)ec2:|i-[0-9a-f]{8,17}")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table (timeline), Bar chart (events by type per day), Line chart (instance count trending).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
