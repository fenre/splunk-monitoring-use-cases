---
id: "4.2.2"
title: "Entra ID Sign-In Anomalies"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.2.2 · Entra ID Sign-In Anomalies

## Description

Risky sign-ins include impossible travel, unfamiliar locations, and anonymous IP usage. Primary detection layer for account compromise.

## Value

Risky sign-ins include impossible travel, unfamiliar locations, and anonymous IP usage. Primary detection layer for account compromise.

## Implementation

Forward Entra ID sign-in logs via Event Hub or direct API. Alert on riskLevelDuringSignIn = high or medium. Correlate with conditional access policy results.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:signinlog`, Entra ID sign-in logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Entra ID sign-in logs via Event Hub or direct API. Alert on riskLevelDuringSignIn = high or medium. Correlate with conditional access policy results.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:signinlog" riskLevelDuringSignIn!="none"
| table _time userPrincipalName riskLevelDuringSignIn riskState ipAddress location.city location.countryOrRegion
| sort -_time
```

Understanding this SPL

**Entra ID Sign-In Anomalies** — Risky sign-ins include impossible travel, unfamiliar locations, and anonymous IP usage. Primary detection layer for account compromise.

Documented **Data sources**: `sourcetype=mscs:azure:signinlog`, Entra ID sign-in logs. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:signinlog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:signinlog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Entra ID Sign-In Anomalies**): table _time userPrincipalName riskLevelDuringSignIn riskState ipAddress location.city location.countryOrRegion
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, risk level, location, IP), Map (sign-in locations), Timeline, Bar chart by risk type.

## SPL

```spl
index=azure sourcetype="mscs:azure:signinlog" riskLevelDuringSignIn!="none"
| table _time userPrincipalName riskLevelDuringSignIn riskState ipAddress location.city location.countryOrRegion
| sort -_time
```

## Visualization

Table (user, risk level, location, IP), Map (sign-in locations), Timeline, Bar chart by risk type.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
