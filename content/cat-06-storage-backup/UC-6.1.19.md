<!-- AUTO-GENERATED from UC-6.1.19.json — DO NOT EDIT -->

---
id: "6.1.19"
title: "Pure Storage Array Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.19 · Pure Storage Array Health

## Description

Pure FA/FB controller, component, and capacity health events indicate hardware or software risk. Unified visibility supports proactive replacement and support cases.

## Value

Pure FA/FB controller, component, and capacity health events indicate hardware or software risk. Unified visibility supports proactive replacement and support cases.

## Implementation

Poll array health and open alerts every 5–15 minutes. Ingest critical/warning alerts with component ID. Correlate with support bundle generation workflows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Pure REST API (scripted input), Pure TA if deployed.
• Ensure the following data sources are available: Pure REST `/api/2.x/arrays`, `/hardware`, `/alerts`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll array health and open alerts every 5–15 minutes. Ingest critical/warning alerts with component ID. Correlate with support bundle generation workflows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="pure:array"
| search status!="healthy" OR component_status!="ok" OR severity IN ("critical","warning")
| stats latest(_time) as last_event, values(message) as messages by array_name, component
| sort -last_event
```

Understanding this SPL

**Pure Storage Array Health** — Pure FA/FB controller, component, and capacity health events indicate hardware or software risk. Unified visibility supports proactive replacement and support cases.

Documented **Data sources**: Pure REST `/api/2.x/arrays`, `/hardware`, `/alerts`. **App/TA** (typical add-on context): Pure REST API (scripted input), Pure TA if deployed. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: pure:array. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="pure:array". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by array_name, component** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare health, capacity, and performance with the Pure1 or array web interface for the same object and time range as the search.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Single value (open critical alerts), Table (array, component, status), Timeline (health transitions).

## SPL

```spl
index=storage sourcetype="pure:array"
| search status!="healthy" OR component_status!="ok" OR severity IN ("critical","warning")
| stats latest(_time) as last_event, values(message) as messages by array_name, component
| sort -last_event
```

## Visualization

Single value (open critical alerts), Table (array, component, status), Timeline (health transitions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
