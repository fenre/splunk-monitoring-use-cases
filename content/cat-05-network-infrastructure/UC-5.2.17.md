<!-- AUTO-GENERATED from UC-5.2.17.json — DO NOT EDIT -->

---
id: "5.2.17"
title: "Firewall Rule Hit Count Analysis"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.17 · Firewall Rule Hit Count Analysis

## Description

Unused firewall rules increase attack surface and complexity. Identifying zero-hit rules enables rule base cleanup and reduces risk.

## Value

Unused firewall rules increase attack surface and complexity. Identifying zero-hit rules enables rule base cleanup and reduces risk.

## Implementation

Collect traffic logs with rule names. Run weekly reports to identify unused rules. Review rules with zero hits over 90 days for removal. Document cleanup actions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect traffic logs with rule names. Run weekly reports to identify unused rules. Review rules with zero hits over 90 days for removal. Document cleanup actions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="pan:traffic"
| stats count as hit_count dc(src) as unique_sources dc(dest) as unique_dests by rule
| sort hit_count
| eval status=if(hit_count=0,"UNUSED",if(hit_count<10,"RARELY_USED","ACTIVE"))
```

Understanding this SPL

**Firewall Rule Hit Count Analysis** — Unused firewall rules increase attack surface and complexity. Identifying zero-hit rules enables rule base cleanup and reduces risk.

Documented **Data sources**: `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: pan:traffic. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="pan:traffic". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by rule** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.



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
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rule, hit count, status), Bar chart (hit count distribution), Single value (unused rule count).

## SPL

```spl
index=network sourcetype="pan:traffic"
| stats count as hit_count dc(src) as unique_sources dc(dest) as unique_dests by rule
| sort hit_count
| eval status=if(hit_count=0,"UNUSED",if(hit_count<10,"RARELY_USED","ACTIVE"))
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

Table (rule, hit count, status), Bar chart (hit count distribution), Single value (unused rule count).

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
