<!-- AUTO-GENERATED from UC-9.1.11.json — DO NOT EDIT -->

---
id: "9.1.11"
title: "Entra ID Risky Sign-Ins"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.11 · Entra ID Risky Sign-Ins

## Description

Entra ID Identity Protection detects risky sign-ins using Microsoft's threat intelligence. Ingesting into Splunk enables correlation with on-prem events.

## Value

Entra ID Identity Protection detects risky sign-ins using Microsoft's threat intelligence. Ingesting into Splunk enables correlation with on-prem events.

## Implementation

Configure Splunk Add-on for Microsoft Cloud Services to ingest Entra ID sign-in logs via Graph API. Filter for medium/high risk detections. Alert on high-risk sign-ins. Correlate with on-prem AD events for hybrid investigations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Entra ID sign-in logs, risk detection events (via Graph API).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk Add-on for Microsoft Cloud Services to ingest Entra ID sign-in logs via Graph API. Filter for medium/high risk detections. Alert on high-risk sign-ins. Correlate with on-prem AD events for hybrid investigations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:aad:signin"
| where riskLevelDuringSignIn IN ("high","medium")
| table _time, userPrincipalName, ipAddress, location, riskLevelDuringSignIn, riskDetail
| sort -_time
```

Understanding this SPL

**Entra ID Risky Sign-Ins** — Entra ID Identity Protection detects risky sign-ins using Microsoft's threat intelligence. Ingesting into Splunk enables correlation with on-prem events.

Documented **Data sources**: Entra ID sign-in logs, risk detection events (via Graph API). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:aad:signin. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:aad:signin". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where riskLevelDuringSignIn IN ("high","medium")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Entra ID Risky Sign-Ins**): table _time, userPrincipalName, ipAddress, location, riskLevelDuringSignIn, riskDetail
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND match(Authentication.app, "(?i)azure|entra|aad")
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Entra ID Risky Sign-Ins** — Entra ID Identity Protection detects risky sign-ins using Microsoft's threat intelligence. Ingesting into Splunk enables correlation with on-prem events.

Documented **Data sources**: Entra ID sign-in logs, risk detection events (via Graph API). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Entra ID sign-in and audit logs in the Microsoft Entra or Azure portal for the same users, resources, and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (risky sign-ins), Geo map (sign-in locations), Line chart (risk events over time), Bar chart (risk types).

## SPL

```spl
index=azure sourcetype="azure:aad:signin"
| where riskLevelDuringSignIn IN ("high","medium")
| table _time, userPrincipalName, ipAddress, location, riskLevelDuringSignIn, riskDetail
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND match(Authentication.app, "(?i)azure|entra|aad")
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Table (risky sign-ins), Geo map (sign-in locations), Line chart (risk events over time), Bar chart (risk types).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
