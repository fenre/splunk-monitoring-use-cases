<!-- AUTO-GENERATED from UC-5.9.2.json — DO NOT EDIT -->

---
id: "5.9.2"
title: "Network Packet Loss Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.2 · Network Packet Loss Monitoring

## Description

Packet loss directly degrades application performance, voice quality, and video conferencing. Even 1% loss can cause noticeable user impact.

## Value

Packet loss directly degrades application performance, voice quality, and video conferencing. Even 1% loss can cause noticeable user impact.

## Implementation

Configure Agent-to-Server tests in ThousandEyes and stream metrics to Splunk via HEC. The OTel metric `network.loss` reports packet loss as a percentage. Alert when average loss exceeds 0.5% for critical paths.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Agent-to-Server tests in ThousandEyes and stream metrics to Splunk via HEC. The OTel metric `network.loss` reports packet loss as a percentage. Alert when average loss exceeds 0.5% for critical paths.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.loss) as avg_loss max(network.loss) as max_loss by thousandeyes.source.agent.name, server.address
| where avg_loss > 0.5
| sort -avg_loss
```

Understanding this SPL

**Network Packet Loss Monitoring** — Packet loss directly degrades application performance, voice quality, and video conferencing. Even 1% loss can cause noticeable user impact.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, server.address** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_loss > 0.5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (loss % over time per agent/server), Single value (current loss), Table sorted by loss.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.loss) as avg_loss max(network.loss) as max_loss by thousandeyes.source.agent.name, server.address
| where avg_loss > 0.5
| sort -avg_loss
```

## Visualization

Line chart (loss % over time per agent/server), Single value (current loss), Table sorted by loss.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
