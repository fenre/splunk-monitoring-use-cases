---
id: "9.1.12"
title: "Conditional Access Policy Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.1.12 · Conditional Access Policy Failures

## Description

Conditional Access blocks indicate non-compliant devices or policy misconfigurations. Monitoring ensures security policies work without excessive user friction.

## Value

Conditional Access blocks indicate non-compliant devices or policy misconfigurations. Monitoring ensures security policies work without excessive user friction.

## Implementation

Ingest Entra ID sign-in logs. Filter for Conditional Access failures. Track failure rates per policy and per user. Alert on sudden spikes indicating policy misconfiguration. Report on most-blocked policies and applications.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Entra ID sign-in logs (conditionalAccessStatus field).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Entra ID sign-in logs. Filter for Conditional Access failures. Track failure rates per policy and per user. Alert on sudden spikes indicating policy misconfiguration. Report on most-blocked policies and applications.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:aad:signin" conditionalAccessStatus="failure"
| stats count by userPrincipalName, appDisplayName, conditionalAccessPolicies{}.displayName
| sort -count
```

Understanding this SPL

**Conditional Access Policy Failures** — Conditional Access blocks indicate non-compliant devices or policy misconfigurations. Monitoring ensures security policies work without excessive user friction.

Documented **Data sources**: Entra ID sign-in logs (conditionalAccessStatus field). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:aad:signin. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:aad:signin". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by userPrincipalName, appDisplayName, conditionalAccessPolicies{}.displayName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

Understanding this CIM / accelerated SPL

**Conditional Access Policy Failures** — Conditional Access blocks indicate non-compliant devices or policy misconfigurations. Monitoring ensures security policies work without excessive user friction.

Documented **Data sources**: Entra ID sign-in logs (conditionalAccessStatus field). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (failures by policy), Table (blocked users), Line chart (failure rate trend), Pie chart (failures by application).

## SPL

```spl
index=azure sourcetype="azure:aad:signin" conditionalAccessStatus="failure"
| stats count by userPrincipalName, appDisplayName, conditionalAccessPolicies{}.displayName
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

## Visualization

Bar chart (failures by policy), Table (blocked users), Line chart (failure rate trend), Pie chart (failures by application).

## Known False Positives

Planned maintenance, backups, or batch jobs can drive metrics outside normal bands — correlate with change management windows.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
