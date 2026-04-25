<!-- AUTO-GENERATED from UC-5.2.5.json — DO NOT EDIT -->

---
id: "5.2.5"
title: "High-Risk Port Exposure"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.5 · High-Risk Port Exposure

## Description

Allowed traffic to RDP/SMB/Telnet from untrusted zones indicates policy gaps.

## Value

Allowed traffic to RDP/SMB/Telnet from untrusted zones indicates policy gaps.

## Implementation

Monitor allow rules for external traffic to high-risk ports. Alert on any matches. Review and tighten rules.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: Firewall traffic logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor allow rules for external traffic to high-risk ports. Alert on any matches. Review and tighten rules.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall action="allowed" (dest_port=3389 OR dest_port=445 OR dest_port=23)
| where NOT cidrmatch("10.0.0.0/8", src)
| stats count by src, dest, dest_port | sort -count
```

Understanding this SPL

**High-Risk Port Exposure** — Allowed traffic to RDP/SMB/Telnet from untrusted zones indicates policy gaps.

Documented **Data sources**: Firewall traffic logs. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT cidrmatch("10.0.0.0/8", src)` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by src, dest, dest_port** so each row reflects one combination of those dimensions.
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
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (source, dest, port), Bar chart by port, Map.

## SPL

```spl
index=firewall action="allowed" (dest_port=3389 OR dest_port=445 OR dest_port=23)
| where NOT cidrmatch("10.0.0.0/8", src)
| stats count by src, dest, dest_port | sort -count
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

Table (source, dest, port), Bar chart by port, Map.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
