<!-- AUTO-GENERATED from UC-2.6.25.json — DO NOT EDIT -->

---
id: "2.6.25"
title: "Citrix NetScaler ADC Performance via uberAgent"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.25 · Citrix NetScaler ADC Performance via uberAgent

## Description

uberAgent can monitor Citrix NetScaler (ADC) appliances via NITRO API without requiring a separate add-on on the ADC itself. This provides gateway session counts, SSL TPS, HTTP request rates, and system resource utilisation alongside endpoint and session data in the same Splunk index, enabling end-to-end correlation from ADC to VDA to application.

## Value

uberAgent can monitor Citrix NetScaler (ADC) appliances via NITRO API without requiring a separate add-on on the ADC itself. This provides gateway session counts, SSL TPS, HTTP request rates, and system resource utilisation alongside endpoint and session data in the same Splunk index, enabling end-to-end correlation from ADC to VDA to application.

## Implementation

Configure uberAgent's NetScaler monitoring with NITRO API credentials. This provides a unified data source — VDA performance, user sessions, and ADC health all in one index. Correlate ADC gateway session counts with VDA session capacity. Alert on ADC resource utilisation exceeding thresholds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448) with NetScaler Monitoring enabled.
• Ensure the following data sources are available: `sourcetype="uberAgent:CitrixADC:AppliancePerformance"`, `sourcetype="uberAgent:CitrixADC:vServer"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure uberAgent's NetScaler monitoring with NITRO API credentials. This provides a unified data source — VDA performance, user sessions, and ADC health all in one index. Correlate ADC gateway session counts with VDA session capacity. Alert on ADC resource utilisation exceeding thresholds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:CitrixADC:AppliancePerformance"
| stats latest(CPUUsagePct) as cpu latest(MemUsagePct) as mem latest(HttpRequestsPerSec) as http_rps latest(SSLTransactionsPerSec) as ssl_tps by ADCHost
| where cpu > 70 OR mem > 80
| table ADCHost, cpu, mem, http_rps, ssl_tps
```

Understanding this SPL

**Citrix NetScaler ADC Performance via uberAgent** — uberAgent can monitor Citrix NetScaler (ADC) appliances via NITRO API without requiring a separate add-on on the ADC itself. This provides gateway session counts, SSL TPS, HTTP request rates, and system resource utilisation alongside endpoint and session data in the same Splunk index, enabling end-to-end correlation from ADC to VDA to application.

Documented **Data sources**: `sourcetype="uberAgent:CitrixADC:AppliancePerformance"`, `sourcetype="uberAgent:CitrixADC:vServer"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448) with NetScaler Monitoring enabled. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:CitrixADC:AppliancePerformance. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:CitrixADC:AppliancePerformance". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ADCHost** so each row reflects one combination of those dimensions.
• Filters the current rows with `where cpu > 70 OR mem > 80` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix NetScaler ADC Performance via uberAgent**): table ADCHost, cpu, mem, http_rps, ssl_tps

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (CPU, memory), Line chart (SSL TPS over time), Table (ADC fleet health).

## SPL

```spl
index=uberagent sourcetype="uberAgent:CitrixADC:AppliancePerformance"
| stats latest(CPUUsagePct) as cpu latest(MemUsagePct) as mem latest(HttpRequestsPerSec) as http_rps latest(SSLTransactionsPerSec) as ssl_tps by ADCHost
| where cpu > 70 OR mem > 80
| table ADCHost, cpu, mem, http_rps, ssl_tps
```

## Visualization

Single value (CPU, memory), Line chart (SSL TPS over time), Table (ADC fleet health).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
