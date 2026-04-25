<!-- AUTO-GENERATED from UC-5.2.6.json — DO NOT EDIT -->

---
id: "5.2.6"
title: "Geo-IP Anomaly Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.6 · Geo-IP Anomaly Detection

## Description

Traffic to/from sanctioned or unexpected countries flags exfiltration, C2, or compromised hosts.

## Value

Traffic to/from sanctioned or unexpected countries flags exfiltration, C2, or compromised hosts.

## Implementation

Install GeoIP lookup (MaxMind). Enrich traffic logs. Alert on sanctioned country traffic and volume anomalies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), GeoIP lookup.
• Ensure the following data sources are available: Firewall traffic logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install GeoIP lookup (MaxMind). Enrich traffic logs. Alert on sanctioned country traffic and volume anomalies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall action="allowed" direction="outbound"
| lookup geoip ip as dest OUTPUT Country
| search Country IN ("Russia","China","North Korea","Iran")
| stats count, sum(bytes_out) as data_sent by src, Country | sort -data_sent
```

Understanding this SPL

**Geo-IP Anomaly Detection** — Traffic to/from sanctioned or unexpected countries flags exfiltration, C2, or compromised hosts.

Documented **Data sources**: Firewall traffic logs. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), GeoIP lookup. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by src, Country** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Network_Traffic data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Network_Traffic model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Choropleth map, Table, Bar chart by country.

## SPL

```spl
index=firewall action="allowed" direction="outbound"
| lookup geoip ip as dest OUTPUT Country
| search Country IN ("Russia","China","North Korea","Iran")
| stats count, sum(bytes_out) as data_sent by src, Country | sort -data_sent
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

## Visualization

Choropleth map, Table, Bar chart by country.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
