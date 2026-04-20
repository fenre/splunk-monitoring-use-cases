---
id: "5.10.2"
title: "Diameter Subscriber Data Accounting"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.2 · Diameter Subscriber Data Accounting

## Description

Aggregates Diameter accounting records to track data usage per subscriber and session, enabling detection of high-usage anomalies, billing reconciliation, and capacity planning.

## Value

Aggregates Diameter accounting records to track data usage per subscriber and session, enabling detection of high-usage anomalies, billing reconciliation, and capacity planning.

## Implementation

Configure Splunk App for Stream to capture Diameter Accounting-Request (ACR, command_code 271) and Accounting-Answer (ACA, command_code 271) messages. The fields `acct_input_octets` and `acct_output_octets` provide byte counts per session. Correlate with `calling_station_id` (subscriber MSISDN/IMSI) to build per-subscriber usage profiles. Set alerts for subscribers exceeding data thresholds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk App for Stream` (Splunkbase #1809).
• Ensure the following data sources are available: `sourcetype=stream:diameter`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk App for Stream to capture Diameter Accounting-Request (ACR, command_code 271) and Accounting-Answer (ACA, command_code 271) messages. The fields `acct_input_octets` and `acct_output_octets` provide byte counts per session. Correlate with `calling_station_id` (subscriber MSISDN/IMSI) to build per-subscriber usage profiles. Set alerts for subscribers exceeding data thresholds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
sourcetype="stream:diameter" command_code=271
| eval total_bytes=acct_input_octets+acct_output_octets
| eval total_MB=round(total_bytes/1048576, 2)
| stats sum(total_MB) as total_data_MB, count as session_count by calling_station_id, origin_host
| sort -total_data_MB
| head 100
```

Understanding this SPL

**Diameter Subscriber Data Accounting** — Aggregates Diameter accounting records to track data usage per subscriber and session, enabling detection of high-usage anomalies, billing reconciliation, and capacity planning.

Documented **Data sources**: `sourcetype=stream:diameter`. **App/TA** (typical add-on context): `Splunk App for Stream` (Splunkbase #1809). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: stream:diameter. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: sourcetype="stream:diameter". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **total_bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **total_MB** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by calling_station_id, origin_host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top 20 subscribers by data usage in MB), Table (calling_station_id, origin_host, total_data_MB, session_count — sortable), Line chart (aggregate data volume trend over 7 days), Single value (total Diameter accounting sessions).

## SPL

```spl
sourcetype="stream:diameter" command_code=271
| eval total_bytes=acct_input_octets+acct_output_octets
| eval total_MB=round(total_bytes/1048576, 2)
| stats sum(total_MB) as total_data_MB, count as session_count by calling_station_id, origin_host
| sort -total_data_MB
| head 100
```

## Visualization

Bar chart (top 20 subscribers by data usage in MB), Table (calling_station_id, origin_host, total_data_MB, session_count — sortable), Line chart (aggregate data volume trend over 7 days), Single value (total Diameter accounting sessions).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
