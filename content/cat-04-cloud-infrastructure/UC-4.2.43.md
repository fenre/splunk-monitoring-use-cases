---
id: "4.2.43"
title: "Defender for Cloud Recommendations"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.2.43 · Defender for Cloud Recommendations

## Description

Secure score and recommendations drive hardening backlog; trending open recommendations shows risk posture over time.

## Value

Secure score and recommendations drive hardening backlog; trending open recommendations shows risk posture over time.

## Implementation

Export recommendations on schedule via Logic App or Microsoft Graph security API to Splunk. Track mean time to remediate by severity. Executive dashboard of secure score trend if ingested.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, Defender export API.
• Ensure the following data sources are available: Defender for Cloud recommendations JSON, continuous export to Log Analytics/Event Hub.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export recommendations on schedule via Logic App or Microsoft Graph security API to Splunk. Track mean time to remediate by severity. Executive dashboard of secure score trend if ingested.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:defender" recommendationState="Active"
| stats count by recommendationName, severity
| sort -count
```

Understanding this SPL

**Defender for Cloud Recommendations** — Secure score and recommendations drive hardening backlog; trending open recommendations shows risk posture over time.

Documented **Data sources**: Defender for Cloud recommendations JSON, continuous export to Log Analytics/Event Hub. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Defender export API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:defender. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:defender". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by recommendationName, severity** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Vulnerabilities.Vulnerabilities by Vulnerabilities.severity | sort - count
```

Understanding this CIM / accelerated SPL

**Defender for Cloud Recommendations** — Secure score and recommendations drive hardening backlog; trending open recommendations shows risk posture over time.

Documented **Data sources**: Defender for Cloud recommendations JSON, continuous export to Log Analytics/Event Hub. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Defender export API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Vulnerabilities.Vulnerabilities` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (recommendations by type), Table (severity, count), Line chart (open recommendations over time).

## SPL

```spl
index=azure sourcetype="mscs:azure:defender" recommendationState="Active"
| stats count by recommendationName, severity
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Vulnerabilities.Vulnerabilities by Vulnerabilities.severity | sort - count
```

## Visualization

Bar chart (recommendations by type), Table (severity, count), Line chart (open recommendations over time).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Vulnerabilities](https://docs.splunk.com/Documentation/CIM/latest/User/Vulnerabilities)
