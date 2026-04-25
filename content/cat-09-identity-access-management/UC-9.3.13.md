<!-- AUTO-GENERATED from UC-9.3.13.json — DO NOT EDIT -->

---
id: "9.3.13"
title: "App Registration Secret Expiry"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.3.13 · App Registration Secret Expiry

## Description

Expired client secrets break automation and encourage long-lived secrets; proactive alerting avoids outages and insecure workarounds.

## Value

Expired client secrets break automation and encourage long-lived secrets; proactive alerting avoids outages and insecure workarounds.

## Implementation

Schedule Graph export of app registrations with secrets/certificates. Alert at 30/14/7 days. Map apps to owners via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, Graph scripted input.
• Ensure the following data sources are available: Application credential inventory (`passwordCredentials.endDateTime`), audit when secret added.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Schedule Graph export of app registrations with secrets/certificates. Alert at 30/14/7 days. Map apps to owners via lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:graph:applications"
| eval days_left=round((strptime(endDateTime,"%Y-%m-%dT%H:%M:%SZ")-now())/86400)
| where days_left < 30 AND days_left > 0
| table appId, displayName, days_left, endDateTime
| sort days_left
```

Understanding this SPL

**App Registration Secret Expiry** — Expired client secrets break automation and encourage long-lived secrets; proactive alerting avoids outages and insecure workarounds.

Documented **Data sources**: Application credential inventory (`passwordCredentials.endDateTime`), audit when secret added. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Graph scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:graph:applications. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:graph:applications". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_left < 30 AND days_left > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **App Registration Secret Expiry**): table appId, displayName, days_left, endDateTime
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with Entra ID sign-in and audit logs in the Microsoft Entra or Azure portal for the same users, resources, and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (expiring secrets), Single value (next expiry), Gauge (apps past due).

## SPL

```spl
index=azure sourcetype="azure:graph:applications"
| eval days_left=round((strptime(endDateTime,"%Y-%m-%dT%H:%M:%SZ")-now())/86400)
| where days_left < 30 AND days_left > 0
| table appId, displayName, days_left, endDateTime
| sort days_left
```

## Visualization

Table (expiring secrets), Single value (next expiry), Gauge (apps past due).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
