<!-- AUTO-GENERATED from UC-4.2.9.json — DO NOT EDIT -->

---
id: "4.2.9"
title: "Defender for Cloud Alerts"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.2.9 · Defender for Cloud Alerts

## Description

Microsoft Defender provides threat detection across Azure resources. Centralizing in Splunk enables cross-platform security correlation.

## Value

Microsoft Defender provides threat detection across Azure resources. Centralizing in Splunk enables cross-platform security correlation.

## Implementation

Configure Defender for Cloud to export alerts to Event Hub. Ingest via Splunk TA. Alert on High and Critical severity findings.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Defender alerts via Event Hub.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Defender for Cloud to export alerts to Event Hub. Ingest via Splunk TA. Alert on High and Critical severity findings.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:defender" severity="High" OR severity="Critical"
| table _time alertDisplayName severity resourceIdentifiers{} description
| sort -_time
```

Understanding this SPL

**Defender for Cloud Alerts** — Microsoft Defender provides threat detection across Azure resources. Centralizing in Splunk enables cross-platform security correlation.

Documented **Data sources**: Defender alerts via Event Hub. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:defender. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:defender". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Defender for Cloud Alerts**): table _time alertDisplayName severity resourceIdentifiers{} description
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table by severity, Bar chart (alert types), Timeline, Single value (critical count).

## SPL

```spl
index=azure sourcetype="mscs:azure:defender" severity="High" OR severity="Critical"
| table _time alertDisplayName severity resourceIdentifiers{} description
| sort -_time
```

## Visualization

Table by severity, Bar chart (alert types), Timeline, Single value (critical count).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
