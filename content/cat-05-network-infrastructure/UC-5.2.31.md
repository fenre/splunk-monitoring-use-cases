<!-- AUTO-GENERATED from UC-5.2.31.json — DO NOT EDIT -->

---
id: "5.2.31"
title: "Application Visibility and Network Application Trending (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.31 · Application Visibility and Network Application Trending (Meraki MX)

## Description

Identifies top applications and protocols on network to understand usage patterns and detect anomalies.

## Value

Identifies top applications and protocols on network to understand usage patterns and detect anomalies.

## Implementation

Extract application field from flow logs. Aggregate by app and category.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=flow application=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Extract application field from flow logs. Aggregate by app and category.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=flow application=*
| stats sum(bytes) as app_bytes, count as flow_count by application, application_category
| eval app_bandwidth_pct=round(app_bytes*100/sum(app_bytes), 2)
| sort - app_bytes
| head 20
```

Understanding this SPL

**Application Visibility and Network Application Trending (Meraki MX)** — Identifies top applications and protocols on network to understand usage patterns and detect anomalies.

Documented **Data sources**: `sourcetype=meraki type=flow application=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by application, application_category** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **app_bandwidth_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.




Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Network_Traffic data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Network_Traffic model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm the same events, site or appliance names, and policy context you see in the dashboard line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: App bandwidth pie chart; top apps bar chart; bandwidth timeline by app.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow application=*
| stats sum(bytes) as app_bytes, count as flow_count by application, application_category
| eval app_bandwidth_pct=round(app_bytes*100/sum(app_bytes), 2)
| sort - app_bytes
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

## Visualization

App bandwidth pie chart; top apps bar chart; bandwidth timeline by app.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
