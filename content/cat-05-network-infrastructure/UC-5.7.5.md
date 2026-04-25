<!-- AUTO-GENERATED from UC-5.7.5.json — DO NOT EDIT -->

---
id: "5.7.5"
title: "Data Exfiltration Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.7.5 · Data Exfiltration Detection

## Description

Unusually large outbound transfers to uncommon destinations may be data theft.

## Value

Unusually large outbound transfers to uncommon destinations may be data theft.

## Implementation

Baseline normal outbound transfer volumes per host. Alert when transfers exceed threshold to unknown destinations. Correlate with DNS and firewall logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for NetFlow.
• Ensure the following data sources are available: NetFlow.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline normal outbound transfer volumes per host. Alert when transfers exceed threshold to unknown destinations. Correlate with DNS and firewall logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=netflow direction="outbound"
| stats sum(bytes) as total_bytes by src, dest
| where total_bytes > 1073741824
| lookup known_destinations dest OUTPUT known
| where isnull(known)
| sort -total_bytes
```

Understanding this SPL

**Data Exfiltration Detection** — Unusually large outbound transfers to uncommon destinations may be data theft.

Documented **Data sources**: NetFlow. **App/TA** (typical add-on context): Splunk Add-on for NetFlow. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: netflow.

**Pipeline walkthrough**

• Scopes the data: index=netflow. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, dest** so each row reflects one combination of those dimensions.
• Filters the current rows with `where total_bytes > 1073741824` — typically the threshold or rule expression for this monitoring goal.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where isnull(known)` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_out) as total_bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| where total_bytes > 1073741824
| sort -total_bytes
```

Understanding this CIM / accelerated SPL

**Data Exfiltration Detection** — Unusually large outbound transfers to uncommon destinations may be data theft.

Documented **Data sources**: NetFlow. **App/TA** (typical add-on context): Splunk Add-on for NetFlow. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Tie one large transfer to a known upload job or a DNS name from passive DNS, then re-check the same volume on the firewall or DLP tool. If `direction` is missing, rely on CIM `bytes_out` and confirm field mapping from your NetFlow/Stream add-on.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Bar chart, Map (destination GeoIP).

## SPL

```spl
index=netflow direction="outbound"
| stats sum(bytes) as total_bytes by src, dest
| where total_bytes > 1073741824
| lookup known_destinations dest OUTPUT known
| where isnull(known)
| sort -total_bytes
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_out) as total_bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| where total_bytes > 1073741824
| sort -total_bytes
```

## Visualization

Table, Bar chart, Map (destination GeoIP).

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
