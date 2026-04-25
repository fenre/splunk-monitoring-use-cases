<!-- AUTO-GENERATED from UC-5.1.13.json — DO NOT EDIT -->

---
id: "5.1.13"
title: "ACL Deny Logging"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.13 · ACL Deny Logging

## Description

ACL deny hits show blocked traffic. High volumes may indicate attacks or misconfigured apps.

## Value

ACL deny hits show blocked traffic. High volumes may indicate attacks or misconfigured apps.

## Implementation

Enable ACL logging (`log` keyword). Forward syslog. Dashboard showing top denied sources and trends.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable ACL logging (`log` keyword). Forward syslog. Dashboard showing top denied sources and trends.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%SEC-6-IPACCESSLOGP"
| rex "list (?<acl>\S+) denied (?<proto>\w+) (?<src>\d+\.\d+\.\d+\.\d+)"
| stats count by host, acl, src, proto | sort -count
```

Understanding this SPL

**ACL Deny Logging** — ACL deny hits show blocked traffic. High volumes may indicate attacks or misconfigured apps.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, acl, src, proto** so each row reflects one combination of those dimensions.
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

**ACL Deny Logging** — ACL deny hits show blocked traffic. High volumes may indicate attacks or misconfigured apps.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
On the device, `show access-lists` (or the Junos or Arista equivalent) with hit counts and compare the denied source, destination, and ACL name in the CLI to the same fields in Splunk.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Bar chart by source IP, Timechart.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SEC-6-IPACCESSLOGP"
| rex "list (?<acl>\S+) denied (?<proto>\w+) (?<src>\d+\.\d+\.\d+\.\d+)"
| stats count by host, acl, src, proto | sort -count
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

Table, Bar chart by source IP, Timechart.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
