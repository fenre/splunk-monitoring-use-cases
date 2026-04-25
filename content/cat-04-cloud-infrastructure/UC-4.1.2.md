<!-- AUTO-GENERATED from UC-4.1.2.json — DO NOT EDIT -->

---
id: "4.1.2"
title: "Root Account Usage"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.1.2 · Root Account Usage

## Description

The AWS root account has unrestricted access and should never be used for daily operations. Any root activity is a critical security event.

## Value

The AWS root account has unrestricted access and should never be used for daily operations. Any root activity is a critical security event.

## Implementation

CloudTrail must be enabled in all regions. Create a critical real-time alert on any event where `userIdentity.type=Root`. Exclude expected events (e.g., automated billing).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
CloudTrail must be enabled in all regions. Create a critical real-time alert on any event where `userIdentity.type=Root`. Exclude expected events (e.g., automated billing).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" userIdentity.type="Root"
| table _time eventName sourceIPAddress userAgent errorCode
| sort -_time
```

Understanding this SPL

**Root Account Usage** — The AWS root account has unrestricted access and should never be used for daily operations. Any root activity is a critical security event.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Root Account Usage**): table _time eventName sourceIPAddress userAgent errorCode
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where match(Authentication.user, "(?i)arn:aws:iam::[0-9]+:root|\\bRoot\\b")
  by Authentication.src Authentication.action Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Root Account Usage** — The AWS root account has unrestricted access and should never be used for daily operations. Any root activity is a critical security event.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events list (critical alert), Single value (root events last 30d), Timeline.

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" userIdentity.type="Root"
| table _time eventName sourceIPAddress userAgent errorCode
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where match(Authentication.user, "(?i)arn:aws:iam::[0-9]+:root|\\bRoot\\b")
  by Authentication.src Authentication.action Authentication.app span=1h
| sort -count
```

## Visualization

Events list (critical alert), Single value (root events last 30d), Timeline.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
