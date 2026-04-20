---
id: "5.5.15"
title: "DPI Application Visibility"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.5.15 · DPI Application Visibility

## Description

Deep Packet Inspection on SD-WAN edges classifies traffic by application. Visibility into top applications per site drives policy tuning, bandwidth planning, and identification of shadow IT or unauthorized SaaS usage.

## Value

Deep Packet Inspection on SD-WAN edges classifies traffic by application. Visibility into top applications per site drives policy tuning, bandwidth planning, and identification of shadow IT or unauthorized SaaS usage.

## Implementation

Enable DPI on SD-WAN edge routers (requires UTD container or native NBAR2). Collect application statistics via vManage. Identify top bandwidth consumers per site. Compare against policy expectations — flag when non-business applications (streaming, gaming, social media) consume more than 20% of WAN bandwidth.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage DPI statistics, `sourcetype=cisco:sdwan:dpi`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DPI on SD-WAN edge routers (requires UTD container or native NBAR2). Collect application statistics via vManage. Identify top bandwidth consumers per site. Compare against policy expectations — flag when non-business applications (streaming, gaming, social media) consume more than 20% of WAN bandwidth.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:dpi"
| stats sum(bytes) as total_bytes, sum(packets) as total_pkts by app_name, family, site_id
| eval GB=round(total_bytes/1073741824,2)
| sort -total_bytes
| head 50
| table app_name family site_id GB total_pkts
```

Understanding this SPL

**DPI Application Visibility** — Deep Packet Inspection on SD-WAN edges classifies traffic by application. Visibility into top applications per site drives policy tuning, bandwidth planning, and identification of shadow IT or unauthorized SaaS usage.

Documented **Data sources**: vManage DPI statistics, `sourcetype=cisco:sdwan:dpi`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:dpi. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:dpi". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by app_name, family, site_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **GB** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.
• Pipeline stage (see **DPI Application Visibility**): table app_name family site_id GB total_pkts

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.app span=1d
| sort -bytes | head 20
```

Understanding this CIM / accelerated SPL

**DPI Application Visibility** — Deep Packet Inspection on SD-WAN edges classifies traffic by application. Visibility into top applications per site drives policy tuning, bandwidth planning, and identification of shadow IT or unauthorized SaaS usage.

Documented **Data sources**: vManage DPI statistics, `sourcetype=cisco:sdwan:dpi`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top 20 apps by volume), Treemap (app families), Table (app, site, volume).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:dpi"
| stats sum(bytes) as total_bytes, sum(packets) as total_pkts by app_name, family, site_id
| eval GB=round(total_bytes/1073741824,2)
| sort -total_bytes
| head 50
| table app_name family site_id GB total_pkts
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.app span=1d
| sort -bytes | head 20
```

## Visualization

Bar chart (top 20 apps by volume), Treemap (app families), Table (app, site, volume).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
