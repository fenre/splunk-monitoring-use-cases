---
id: "4.2.26"
title: "Azure Service Health and Planned Maintenance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.26 · Azure Service Health and Planned Maintenance

## Description

Service Health and planned maintenance notifications prevent wasted troubleshooting and enable change planning.

## Value

Service Health and planned maintenance notifications prevent wasted troubleshooting and enable change planning.

## Implementation

Service Health events flow to Activity Log. Ingest and filter for category=ServiceHealth. Alert on incidentType=Incident or Security. Dashboard active incidents and upcoming maintenance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Service Health alerts via Activity Log (ServiceHealth).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Service Health events flow to Activity Log. Ingest and filter for category=ServiceHealth. Alert on incidentType=Incident or Security. Dashboard active incidents and upcoming maintenance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" category.value="ServiceHealth"
| table _time properties.incidentType properties.title properties.description properties.status
| sort -_time
```

Understanding this SPL

**Azure Service Health and Planned Maintenance** — Service Health and planned maintenance notifications prevent wasted troubleshooting and enable change planning.

Documented **Data sources**: Service Health alerts via Activity Log (ServiceHealth). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Azure Service Health and Planned Maintenance**): table _time properties.incidentType properties.title properties.description properties.status
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (incident, service, status), Timeline (incidents), Single value (active incidents).

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" category.value="ServiceHealth"
| table _time properties.incidentType properties.title properties.description properties.status
| sort -_time
```

## Visualization

Table (incident, service, status), Timeline (incidents), Single value (active incidents).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
