<!-- AUTO-GENERATED from UC-5.2.2.json — DO NOT EDIT -->

---
id: "5.2.2"
title: "Policy Change Audit"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.2 · Policy Change Audit

## Description

Firewall rule changes can expose the network. Compliance must-have (PCI, SOX, HIPAA).

## Value

Firewall rule changes can expose the network. Compliance must-have (PCI, SOX, HIPAA).

## Implementation

Forward configuration change logs. Alert on any rule modification. Require change ticket correlation. Keep 1-year retention.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: `sourcetype=pan:config`, firewall system/config logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward configuration change logs. Alert on any rule modification. Require change ticket correlation. Keep 1-year retention.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="pan:config" cmd="set" OR cmd="edit" OR cmd="delete"
| table _time host admin cmd path | sort -_time
```

Understanding this SPL

**Policy Change Audit** — Firewall rule changes can expose the network. Compliance must-have (PCI, SOX, HIPAA).

Documented **Data sources**: `sourcetype=pan:config`, firewall system/config logs. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: pan:config. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="pan:config". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Policy Change Audit**): table _time host admin cmd path
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Change data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Change model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (who, what, when), Timeline, Single value (changes last 24h).

## SPL

```spl
index=firewall sourcetype="pan:config" cmd="set" OR cmd="edit" OR cmd="delete"
| table _time host admin cmd path | sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table (who, what, when), Timeline, Single value (changes last 24h).

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
