---
id: "5.9.30"
title: "SASE Secure Edge Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.30 · SASE Secure Edge Performance

## Description

SASE architectures route traffic through cloud-based security edges (Zscaler, Cisco Umbrella, etc.). Monitoring latency and loss through these edges ensures the security layer does not unacceptably degrade user experience.

## Value

SASE architectures route traffic through cloud-based security edges (Zscaler, Cisco Umbrella, etc.). Monitoring latency and loss through these edges ensures the security layer does not unacceptably degrade user experience.

## Implementation

Create Agent-to-Server tests in ThousandEyes that route through your SASE secure edge. Name tests descriptively to include the SASE provider. Compare latency with and without the secure edge to quantify the security overhead. Correlate with Endpoint Agent `target.type="proxy"` data for end-to-end visibility.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create Agent-to-Server tests in ThousandEyes that route through your SASE secure edge. Name tests descriptively to include the SASE provider. Compare latency with and without the secure edge to quantify the security overhead. Correlate with Endpoint Agent `target.type="proxy"` data for end-to-end visibility.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*SASE*" OR thousandeyes.test.name="*Zscaler*" OR thousandeyes.test.name="*Umbrella*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort -avg_latency_ms
```

Understanding this SPL

**SASE Secure Edge Performance** — SASE architectures route traffic through cloud-based security edges (Zscaler, Cisco Umbrella, etc.). Monitoring latency and loss through these edges ensures the security layer does not unacceptably degrade user experience.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, thousandeyes.source.agent.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency through secure edge over time), Table (agent, SASE test, latency, loss), Comparison chart.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*SASE*" OR thousandeyes.test.name="*Zscaler*" OR thousandeyes.test.name="*Umbrella*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort -avg_latency_ms
```

## Visualization

Line chart (latency through secure edge over time), Table (agent, SASE test, latency, loss), Comparison chart.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
