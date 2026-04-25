<!-- AUTO-GENERATED from UC-5.7.7.json — DO NOT EDIT -->

---
id: "5.7.7"
title: "Protocol Distribution Analysis"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.7.7 · Protocol Distribution Analysis

## Description

Understanding protocol mix helps validate network policies and detect unauthorized protocols (e.g., unexpected SSH, RDP, or P2P traffic).

## Value

Understanding protocol mix helps validate network policies and detect unauthorized protocols (e.g., unexpected SSH, RDP, or P2P traffic).

## Implementation

Collect NetFlow/sFlow/IPFIX from routers and switches. Map port numbers to service names via lookup. Baseline protocol distribution. Alert on new protocols or significant shifts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Stream, NetFlow integrator.
• Ensure the following data sources are available: `sourcetype=netflow`, `sourcetype=stream:tcp`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect NetFlow/sFlow/IPFIX from routers and switches. Map port numbers to service names via lookup. Baseline protocol distribution. Alert on new protocols or significant shifts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="netflow"
| lookup service_lookup dest_port OUTPUT service_name
| stats sum(bytes) as total_bytes dc(src) as unique_sources by protocol, service_name
| eval GB=round(total_bytes/1073741824,2) | sort -total_bytes
| head 20
```

Understanding this SPL

**Protocol Distribution Analysis** — Understanding protocol mix helps validate network policies and detect unauthorized protocols (e.g., unexpected SSH, RDP, or P2P traffic).

Documented **Data sources**: `sourcetype=netflow`, `sourcetype=stream:tcp`. **App/TA** (typical add-on context): Splunk Stream, NetFlow integrator. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: netflow. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="netflow". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `stats` rolls up events into metrics; results are split **by protocol, service_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **GB** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out dc(All_Traffic.src) as unique_sources
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.transport All_Traffic.app span=1h
| eval total_bytes=bytes_in+bytes_out
| sort -total_bytes
| head 20
```

Understanding this CIM / accelerated SPL

**Protocol Distribution Analysis** — Understanding protocol mix helps validate network policies and detect unauthorized protocols (e.g., unexpected SSH, RDP, or P2P traffic).

Documented **Data sources**: `sourcetype=netflow`, `sourcetype=stream:tcp`. **App/TA** (typical add-on context): Splunk Stream, NetFlow integrator. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare top `protocol` or `app` shares to a router, SD-WAN, or Stealthwatch-style view; confirm `service_lookup` matches your IANA/organization port list. If `transport` is not in the data model, fall back to `app` only in the CIM search.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (by protocol), Treemap (by service + volume), Timechart.

## SPL

```spl
index=network sourcetype="netflow"
| lookup service_lookup dest_port OUTPUT service_name
| stats sum(bytes) as total_bytes dc(src) as unique_sources by protocol, service_name
| eval GB=round(total_bytes/1073741824,2) | sort -total_bytes
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out dc(All_Traffic.src) as unique_sources
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.transport All_Traffic.app span=1h
| eval total_bytes=bytes_in+bytes_out
| sort -total_bytes
| head 20
```

## Visualization

Pie chart (by protocol), Treemap (by service + volume), Timechart.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
