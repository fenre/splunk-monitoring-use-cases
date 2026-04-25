<!-- AUTO-GENERATED from UC-9.1.18.json — DO NOT EDIT -->

---
id: "9.1.18"
title: "Hybrid Join Device Compliance"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.1.18 · Hybrid Join Device Compliance

## Description

Hybrid Azure AD join state and Intune compliance gate access; drift from compliant blocks users and signals stale or tampered endpoints.

## Value

Hybrid Azure AD join state and Intune compliance gate access; drift from compliant blocks users and signals stale or tampered endpoints.

## Implementation

Ingest device inventory from Graph/Intune on a schedule. Join with sign-in logs for non-compliant hybrid devices. Alert on compliance flip from true to false or long-running non-compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, Microsoft Intune / Graph scripted input.
• Ensure the following data sources are available: Entra ID device objects (`trustType`, `isCompliant`, `profileType`), Intune compliance reports.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest device inventory from Graph/Intune on a schedule. Join with sign-in logs for non-compliant hybrid devices. Alert on compliance flip from true to false or long-running non-compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:intune:devices" OR sourcetype="azure:aad:devices"
| where trustType="ServerAd" AND (isCompliant="false" OR isCompliant="False")
| stats latest(_time) as last_seen by deviceId, displayName, managementType, isCompliant
| sort -last_seen
```

Understanding this SPL

**Hybrid Join Device Compliance** — Hybrid Azure AD join state and Intune compliance gate access; drift from compliant blocks users and signals stale or tampered endpoints.

Documented **Data sources**: Entra ID device objects (`trustType`, `isCompliant`, `profileType`), Intune compliance reports. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Microsoft Intune / Graph scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:intune:devices, azure:aad:devices. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:intune:devices". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where trustType="ServerAd" AND (isCompliant="false" OR isCompliant="False")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by deviceId, displayName, managementType, isCompliant** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Compare with Entra ID and Intune device inventory in the Microsoft Entra admin center (device list and compliance) for the same device IDs and time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (non-compliant hybrid devices), Pie chart (compliant vs not), Line chart (non-compliance trend).

## SPL

```spl
index=azure sourcetype="azure:intune:devices" OR sourcetype="azure:aad:devices"
| where trustType="ServerAd" AND (isCompliant="false" OR isCompliant="False")
| stats latest(_time) as last_seen by deviceId, displayName, managementType, isCompliant
| sort -last_seen
```

## Visualization

Table (non-compliant hybrid devices), Pie chart (compliant vs not), Line chart (non-compliance trend).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [Microsoft Entra device management](https://learn.microsoft.com/entra/identity/devices/)
