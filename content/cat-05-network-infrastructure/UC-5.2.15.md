<!-- AUTO-GENERATED from UC-5.2.15.json — DO NOT EDIT -->

---
id: "5.2.15"
title: "Botnet/C2 Traffic Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.15 · Botnet/C2 Traffic Detection

## Description

Detecting outbound connections to known C2 infrastructure identifies compromised internal hosts before data exfiltration occurs.

## Value

Detecting outbound connections to known C2 infrastructure identifies compromised internal hosts before data exfiltration occurs.

## Implementation

Enable threat prevention and URL filtering on the firewall. Ingest threat logs. Cross-reference with external threat intelligence (STIX/TAXII feeds). Alert immediately on any C2 match.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), Threat intelligence feeds.
• Ensure the following data sources are available: `sourcetype=pan:threat`, `sourcetype=pan:traffic`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable threat prevention and URL filtering on the firewall. Ingest threat logs. Cross-reference with external threat intelligence (STIX/TAXII feeds). Alert immediately on any C2 match.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="pan:threat" category="command-and-control" OR category="spyware"
| stats count values(dest) as c2_targets dc(dest) as unique_c2 by src
| sort -count
| lookup dnslookup clientip as src OUTPUT clienthost as src_hostname
```

Understanding this SPL

**Botnet/C2 Traffic Detection** — Detecting outbound connections to known C2 infrastructure identifies compromised internal hosts before data exfiltration occurs.

Documented **Data sources**: `sourcetype=pan:threat`, `sourcetype=pan:traffic`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), Threat intelligence feeds. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: pan:threat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="pan:threat". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Intrusion_Detection data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Intrusion_Detection model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (compromised hosts, C2 targets), Sankey diagram (source → C2), Single value (count).

## SPL

```spl
index=network sourcetype="pan:threat" category="command-and-control" OR category="spyware"
| stats count values(dest) as c2_targets dc(dest) as unique_c2 by src
| sort -count
| lookup dnslookup clientip as src OUTPUT clienthost as src_hostname
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

## Visualization

Table (compromised hosts, C2 targets), Sankey diagram (source → C2), Single value (count).

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
