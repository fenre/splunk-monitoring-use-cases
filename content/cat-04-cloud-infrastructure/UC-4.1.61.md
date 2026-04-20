---
id: "4.1.61"
title: "Network ACL Changes"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.61 · Network ACL Changes

## Description

NACL changes can open subnets to the internet or break least-privilege segmentation; they are less common than security groups and warrant explicit audit.

## Value

NACL changes can open subnets to the internet or break least-privilege segmentation; they are less common than security groups and warrant explicit audit.

## Implementation

Require change tickets in deployment pipeline metadata where possible. Alert on any prod NACL change. Visualize before/after rule numbers and CIDR blocks from `requestParameters`. Weekly review with network team.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail` (ec2.amazonaws.com CreateNetworkAclEntry, ReplaceNetworkAclEntry, DeleteNetworkAclEntry).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Require change tickets in deployment pipeline metadata where possible. Alert on any prod NACL change. Visualize before/after rule numbers and CIDR blocks from `requestParameters`. Weekly review with network team.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="ec2.amazonaws.com" (eventName="CreateNetworkAclEntry" OR eventName="ReplaceNetworkAclEntry" OR eventName="DeleteNetworkAclEntry")
| stats count by userIdentity.arn, requestParameters.networkAclId, eventName, awsRegion
| sort -_time
```

Understanding this SPL

**Network ACL Changes** — NACL changes can open subnets to the internet or break least-privilege segmentation; they are less common than security groups and warrant explicit audit.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (ec2.amazonaws.com CreateNetworkAclEntry, ReplaceNetworkAclEntry, DeleteNetworkAclEntry). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by userIdentity.arn, requestParameters.networkAclId, eventName, awsRegion** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Network ACL Changes** — NACL changes can open subnets to the internet or break least-privilege segmentation; they are less common than security groups and warrant explicit audit.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (ec2.amazonaws.com CreateNetworkAclEntry, ReplaceNetworkAclEntry, DeleteNetworkAclEntry). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (NACL, user, action), Timeline (changes), Single value (changes 24h).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="ec2.amazonaws.com" (eventName="CreateNetworkAclEntry" OR eventName="ReplaceNetworkAclEntry" OR eventName="DeleteNetworkAclEntry")
| stats count by userIdentity.arn, requestParameters.networkAclId, eventName, awsRegion
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user | sort - count
```

## Visualization

Table (NACL, user, action), Timeline (changes), Single value (changes 24h).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
