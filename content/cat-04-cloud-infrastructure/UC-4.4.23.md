<!-- AUTO-GENERATED from UC-4.4.23.json — DO NOT EDIT -->

---
id: "4.4.23"
title: "Multi-Cloud DNS Resolution Health"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.23 · Multi-Cloud DNS Resolution Health

## Description

DNS failures in one cloud or resolver path strand hybrid apps; proactive health checks catch resolver outages and split-horizon misconfiguration before user impact.

## Value

DNS failures in one cloud or resolver path strand hybrid apps; proactive health checks catch resolver outages and split-horizon misconfiguration before user impact.

## Implementation

Emit probe results from each cloud (success, latency_ms, NXDOMAIN rate) via HEC. Optionally join Route 53 Resolver query logs for SERVFAIL spikes. Page when any critical FQDN fails from two vantage points or latency doubles vs baseline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (synthetic probes, Route 53 Resolver / Azure DNS / Cloud DNS logs).
• Ensure the following data sources are available: `sourcetype=dns:health`, `sourcetype=aws:route53resolverquerylog`, `sourcetype=mscs:azure:diagnostics` (DNS if enabled).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Emit probe results from each cloud (success, latency_ms, NXDOMAIN rate) via HEC. Optionally join Route 53 Resolver query logs for SERVFAIL spikes. Page when any critical FQDN fails from two vantage points or latency doubles vs baseline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud (sourcetype="dns:health" OR sourcetype="synthetic:dns")
| stats latest(success) as ok, avg(latency_ms) as avg_ms by provider, resolver_vantage, tested_fqdn
| where ok=0 OR avg_ms>500
| eval avg_ms=round(avg_ms,1)
| sort provider tested_fqdn
```

Understanding this SPL

**Multi-Cloud DNS Resolution Health** — DNS failures in one cloud or resolver path strand hybrid apps; proactive health checks catch resolver outages and split-horizon misconfiguration before user impact.

Documented **Data sources**: `sourcetype=dns:health`, `sourcetype=aws:route53resolverquerylog`, `sourcetype=mscs:azure:diagnostics` (DNS if enabled). **App/TA** (typical add-on context): Custom (synthetic probes, Route 53 Resolver / Azure DNS / Cloud DNS logs). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: dns:health, synthetic:dns. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="dns:health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by provider, resolver_vantage, tested_fqdn** so each row reflects one combination of those dimensions.
• Filters the current rows with `where ok=0 OR avg_ms>500` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **avg_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (FQDN × provider), Line chart (success rate over time), Single value (failed probes).

## SPL

```spl
index=cloud (sourcetype="dns:health" OR sourcetype="synthetic:dns")
| stats latest(success) as ok, avg(latency_ms) as avg_ms by provider, resolver_vantage, tested_fqdn
| where ok=0 OR avg_ms>500
| eval avg_ms=round(avg_ms,1)
| sort provider tested_fqdn
```

## Visualization

Status grid (FQDN × provider), Line chart (success rate over time), Single value (failed probes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
