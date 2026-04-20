---
id: "4.1.5"
title: "Console Login Without MFA"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.5 · Console Login Without MFA

## Description

Console access without MFA is a security risk — compromised passwords alone can grant full account access. Most compliance frameworks require MFA.

## Value

Console access without MFA is a security risk — compromised passwords alone can grant full account access. Most compliance frameworks require MFA.

## Implementation

Monitor ConsoleLogin events. Alert on successful console logins where MFA is not used. Exclude service accounts that authenticate via SSO (which has its own MFA).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor ConsoleLogin events. Alert on successful console logins where MFA is not used. Exclude service accounts that authenticate via SSO (which has its own MFA).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventName="ConsoleLogin" responseElements.ConsoleLogin="Success"
| eval mfa_used = if(additionalEventData.MFAUsed="Yes", "Yes", "No")
| where mfa_used="No"
| table _time userIdentity.arn sourceIPAddress mfa_used
| sort -_time
```

Understanding this SPL

**Console Login Without MFA** — Console access without MFA is a security risk — compromised passwords alone can grant full account access. Most compliance frameworks require MFA.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **mfa_used** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where mfa_used="No"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Console Login Without MFA**): table _time userIdentity.arn sourceIPAddress mfa_used
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND (match(Authentication.signature, "(?i)ConsoleLogin|AwsConsoleSignIn") OR match(Authentication.app, "(?i)signin\\.amazonaws"))
  AND NOT (Authentication.mfa="true" OR lower(Authentication.authentication_method)="mfa")
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Console Login Without MFA** — Console access without MFA is a security risk — compromised passwords alone can grant full account access. Most compliance frameworks require MFA.

Documented **Data sources**: `sourcetype=aws:cloudtrail`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, source IP, MFA status), Pie chart (MFA vs. no-MFA), Single value.

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventName="ConsoleLogin" responseElements.ConsoleLogin="Success"
| eval mfa_used = if(additionalEventData.MFAUsed="Yes", "Yes", "No")
| where mfa_used="No"
| table _time userIdentity.arn sourceIPAddress mfa_used
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND (match(Authentication.signature, "(?i)ConsoleLogin|AwsConsoleSignIn") OR match(Authentication.app, "(?i)signin\\.amazonaws"))
  AND NOT (Authentication.mfa="true" OR lower(Authentication.authentication_method)="mfa")
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Table (user, source IP, MFA status), Pie chart (MFA vs. no-MFA), Single value.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
