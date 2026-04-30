<!-- AUTO-GENERATED from UC-5.9.51.json — DO NOT EDIT -->

---
id: "5.9.51"
title: "Splunk On-Call Incident Routing from ThousandEyes"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.51 · Splunk On-Call Incident Routing from ThousandEyes

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We hand serious tests straight into on-call, so the right people wake up for real user pain, not for every blip.*

---

## Description

Routes ThousandEyes alerts directly to Splunk On-Call (formerly VictorOps) for incident management, on-call paging, and war room coordination. Ensures network and application issues detected by ThousandEyes reach the right team within seconds.

## Value

Routes ThousandEyes alerts directly to Splunk On-Call (formerly VictorOps) for incident management, on-call paging, and war room coordination. Ensures network and application issues detected by ThousandEyes reach the right team within seconds.

## Implementation

Configure ThousandEyes to send alert notifications to Splunk On-Call via the REST API endpoint webhook integration. In ThousandEyes, create a webhook notification pointing to the Splunk On-Call REST endpoint URL with your routing key. Map ThousandEyes alert severity to Splunk On-Call incident severity (critical→critical, warning→warning, info→info). The integration supports recovery messages to automatically resolve incidents when ThousandEyes alerts clear.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: ThousandEyes webhook integration with Splunk On-Call.
- Ensure the following data sources are available: ThousandEyes alert webhooks.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Configure ThousandEyes to send alert notifications to Splunk On-Call via the REST API endpoint webhook integration. In ThousandEyes, create a webhook notification pointing to the Splunk On-Call REST endpoint URL with your routing key. Map ThousandEyes alert severity to Splunk On-Call incident severity (critical→critical, warning→warning, info→info). The integration supports recovery messages to automatically resolve incidents when ThousandEyes alerts clear.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=oncall sourcetype="oncall:incidents" monitoring_tool="ThousandEyes"
| stats count by incident_state, routing_key, entity_id
| sort -count
```

#### Understanding this SPL

**Splunk On-Call Incident Routing from ThousandEyes** — Routes ThousandEyes alerts directly to Splunk On-Call (formerly VictorOps) for incident management, on-call paging, and war room coordination. Ensures network and application issues detected by ThousandEyes reach the right team within seconds.

Documented **Data sources**: ThousandEyes alert webhooks. **App/TA** (typical add-on context): ThousandEyes webhook integration with Splunk On-Call. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: oncall; **sourcetype**: oncall:incidents. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=oncall, sourcetype="oncall:incidents". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by incident_state, routing_key, entity_id** so each row reflects one combination of those dimensions.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (incidents by state and routing key), Timeline (incident creation/resolution), Single value (active incidents from ThousandEyes).

## SPL

```spl
index=oncall sourcetype="oncall:incidents" monitoring_tool="ThousandEyes"
| stats count by incident_state, routing_key, entity_id
| sort -count
```

## Visualization

Table (incidents by state and routing key), Timeline (incident creation/resolution), Single value (active incidents from ThousandEyes).

## Known False Positives

On-call noise grows when every warning pages; map severities to human-only tiers and add suppression windows.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
