<!-- AUTO-GENERATED from UC-5.9.7.json — DO NOT EDIT -->

---
id: "5.9.7"
title: "WAN Link Quality Scoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.7 · WAN Link Quality Scoring

## Description

Composite quality score derived from latency, loss, and jitter provides a single metric for WAN link health, simplifying executive reporting and SLA tracking.

## Value

Composite quality score derived from latency, loss, and jitter provides a single metric for WAN link health, simplifying executive reporting and SLA tracking.

## Implementation

For Endpoint agents the OTel metric `network.score` provides a pre-computed composite. For Cloud and Enterprise Agent tests, calculate a weighted score from latency, loss, and jitter as shown. Adjust weights and thresholds for your SLA requirements.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
For Endpoint agents the OTel metric `network.score` provides a pre-computed composite. For Cloud and Enterprise Agent tests, calculate a weighted score from latency, loss, and jitter as shown. Adjust weights and thresholds for your SLA requirements.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-server" OR thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_lat avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval latency_score=if(avg_lat<0.05,100,if(avg_lat<0.1,80,if(avg_lat<0.2,60,if(avg_lat<0.5,40,20))))
| eval loss_score=if(avg_loss<0.1,100,if(avg_loss<0.5,80,if(avg_loss<1,60,if(avg_loss<3,40,20))))
| eval jitter_score=if(avg_jitter<5,100,if(avg_jitter<15,80,if(avg_jitter<30,60,if(avg_jitter<50,40,20))))
| eval quality_score=round((latency_score*0.4 + loss_score*0.35 + jitter_score*0.25),0)
| sort quality_score
```

Understanding this SPL

**WAN Link Quality Scoring** — Composite quality score derived from latency, loss, and jitter provides a single metric for WAN link health, simplifying executive reporting and SLA tracking.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, server.address** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **latency_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **loss_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **jitter_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **quality_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (quality score per link), Table (all links ranked), Trend line chart.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server" OR thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_lat avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval latency_score=if(avg_lat<0.05,100,if(avg_lat<0.1,80,if(avg_lat<0.2,60,if(avg_lat<0.5,40,20))))
| eval loss_score=if(avg_loss<0.1,100,if(avg_loss<0.5,80,if(avg_loss<1,60,if(avg_loss<3,40,20))))
| eval jitter_score=if(avg_jitter<5,100,if(avg_jitter<15,80,if(avg_jitter<30,60,if(avg_jitter<50,40,20))))
| eval quality_score=round((latency_score*0.4 + loss_score*0.35 + jitter_score*0.25),0)
| sort quality_score
```

## Visualization

Gauge (quality score per link), Table (all links ranked), Trend line chart.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
