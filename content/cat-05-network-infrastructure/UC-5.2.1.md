<!-- AUTO-GENERATED from UC-5.2.1.json — DO NOT EDIT -->

---
id: "5.2.1"
title: "Top Denied Traffic Sources"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.1 · Top Denied Traffic Sources

## Description

Identifies top blocked traffic sources — useful for rule tuning, detecting scanning, and misconfigured apps.

## Value

Identifies top blocked traffic sources — useful for rule tuning, detecting scanning, and misconfigured apps.

## Implementation

Forward firewall traffic logs via syslog. Install vendor TA for CIM-compliant fields. Create top-N dashboard.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`, `sourcetype=cisco:firepower:syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward firewall traffic logs via syslog. Install vendor TA for CIM-compliant fields. Create top-N dashboard.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall action="denied" OR action="drop"
| stats count as denials, dc(dest) as unique_dests by src
| sort -denials | head 20 | lookup geoip ip as src OUTPUT Country
```

Understanding this SPL

**Top Denied Traffic Sources** — Identifies top blocked traffic sources — useful for rule tuning, detecting scanning, and misconfigured apps.

Documented **Data sources**: `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`, `sourcetype=cisco:firepower:syslog`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action IN ("deny","denied","drop","dropped","blocked","block")
  by All_Traffic.src All_Traffic.dest span=1h
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
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (source, denials, dests), Map (GeoIP), Bar chart.

## SPL

```spl
index=firewall action="denied" OR action="drop"
| stats count as denials, dc(dest) as unique_dests by src
| sort -denials | head 20 | lookup geoip ip as src OUTPUT Country
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action IN ("deny","denied","drop","dropped","blocked","block")
  by All_Traffic.src All_Traffic.dest span=1h
| sort -count
```

## Visualization

Table (source, denials, dests), Map (GeoIP), Bar chart.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
