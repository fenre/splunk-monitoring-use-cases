---
id: "5.10.3"
title: "Mobile Subscriber RADIUS Session Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.3 · Mobile Subscriber RADIUS Session Tracking

## Description

Tracks active mobile subscriber sessions via RADIUS accounting, providing visibility into session duration, data volume, and SGSN/MCC-MNC distribution — critical for mobile core capacity planning and roaming analytics.

## Value

Tracks active mobile subscriber sessions via RADIUS accounting, providing visibility into session duration, data volume, and SGSN/MCC-MNC distribution — critical for mobile core capacity planning and roaming analytics.

## Implementation

Configure Splunk App for Stream to capture RADIUS accounting traffic from the mobile packet core (GGSN/PGW). Enable RADIUS protocol extraction including the telco-specific fields `sgsn_address` and `sgsn_mcc_mnc`. Use `code="Accounting-Request"` to filter for accounting records. Correlate `start_time` and `stop_time` for session duration. The `sgsn_mcc_mnc` field identifies the serving network (home vs. roaming). Alert on sudden drops in active sessions per SGSN.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk App for Stream` (Splunkbase #1809).
• Ensure the following data sources are available: `sourcetype=stream:radius`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk App for Stream to capture RADIUS accounting traffic from the mobile packet core (GGSN/PGW). Enable RADIUS protocol extraction including the telco-specific fields `sgsn_address` and `sgsn_mcc_mnc`. Use `code="Accounting-Request"` to filter for accounting records. Correlate `start_time` and `stop_time` for session duration. The `sgsn_mcc_mnc` field identifies the serving network (home vs. roaming). Alert on sudden drops in active sessions per SGSN.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
sourcetype="stream:radius" code="Accounting-Request"
| eval session_secs=stop_time-start_time
| eval session_min=round(session_secs/60, 1)
| stats count as sessions, avg(session_min) as avg_duration_min, dc(login) as unique_subscribers by sgsn_address, sgsn_mcc_mnc
| sort -sessions
```

Understanding this SPL

**Mobile Subscriber RADIUS Session Tracking** — Tracks active mobile subscriber sessions via RADIUS accounting, providing visibility into session duration, data volume, and SGSN/MCC-MNC distribution — critical for mobile core capacity planning and roaming analytics.

Documented **Data sources**: `sourcetype=stream:radius`. **App/TA** (typical add-on context): `Splunk App for Stream` (Splunkbase #1809). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: stream:radius. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: sourcetype="stream:radius". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **session_secs** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **session_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by sgsn_address, sgsn_mcc_mnc** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (active sessions by SGSN address), Table (sgsn_address, sgsn_mcc_mnc, sessions, unique_subscribers, avg_duration_min — sortable), Timechart (session count over 24h), Pie chart (session distribution by MCC-MNC for roaming analysis).

## SPL

```spl
sourcetype="stream:radius" code="Accounting-Request"
| eval session_secs=stop_time-start_time
| eval session_min=round(session_secs/60, 1)
| stats count as sessions, avg(session_min) as avg_duration_min, dc(login) as unique_subscribers by sgsn_address, sgsn_mcc_mnc
| sort -sessions
```

## Visualization

Column chart (active sessions by SGSN address), Table (sgsn_address, sgsn_mcc_mnc, sessions, unique_subscribers, avg_duration_min — sortable), Timechart (session count over 24h), Pie chart (session distribution by MCC-MNC for roaming analysis).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
