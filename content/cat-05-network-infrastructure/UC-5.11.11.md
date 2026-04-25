<!-- AUTO-GENERATED from UC-5.11.11.json — DO NOT EDIT -->

---
id: "5.11.11"
title: "ACL Hit Counter Analysis via Streaming Telemetry"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.11.11 · ACL Hit Counter Analysis via Streaming Telemetry

## Description

ACL rules that never match traffic are dead weight that slows TCAM lookups and obscures security intent. Conversely, deny rules with climbing hit counts reveal active attack patterns. Streaming ACL counters via gNMI at 30-second intervals provides the data needed for security policy effectiveness analysis and ACL cleanup — tasks that are nearly impossible with periodic SNMP polling.

## Value

ACL rules that never match traffic are dead weight that slows TCAM lookups and obscures security intent. Conversely, deny rules with climbing hit counts reveal active attack patterns. Streaming ACL counters via gNMI at 30-second intervals provides the data needed for security policy effectiveness analysis and ACL cleanup — tasks that are nearly impossible with periodic SNMP polling.

## Implementation

Subscribe to `/acl/acl-sets/acl-set/acl-entries/acl-entry/state` at 30s intervals. Identify deny rules with increasing hit counts — these represent blocked attack traffic. Identify permit rules with zero hits over 30 days — candidates for cleanup. Cross-reference with firewall logs and IDS alerts for security correlation. Generate monthly ACL effectiveness reports for compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/acl/acl-sets/acl-set/acl-entries/acl-entry/state` (matched-packets, matched-octets); Telegraf metric: `openconfig_acl`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to `/acl/acl-sets/acl-set/acl-entries/acl-entry/state` at 30s intervals. Identify deny rules with increasing hit counts — these represent blocked attack traffic. Identify permit rules with zero hits over 30 days — candidates for cleanup. Cross-reference with firewall logs and IDS alerts for security correlation. Generate monthly ACL effectiveness reports for compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats rate_avg("openconfig_acl.matched_packets") AS hits_per_sec WHERE index=gnmi_metrics BY host, acl_name, sequence_id, description span=5m
| where hits_per_sec > 0
| eval daily_hits=round(hits_per_sec * 86400, 0)
| table host, acl_name, sequence_id, description, hits_per_sec, daily_hits
| sort -hits_per_sec
```

Understanding this SPL

**ACL Hit Counter Analysis via Streaming Telemetry** — ACL rules that never match traffic are dead weight that slows TCAM lookups and obscures security intent. Conversely, deny rules with climbing hit counts reveal active attack patterns. Streaming ACL counters via gNMI at 30-second intervals provides the data needed for security policy effectiveness analysis and ACL cleanup — tasks that are nearly impossible with periodic SNMP polling.

Documented **Data sources**: gNMI path: `/acl/acl-sets/acl-set/acl-entries/acl-entry/state` (matched-packets, matched-octets); Telegraf metric: `openconfig_acl`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• Filters the current rows with `where hits_per_sec > 0` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **daily_hits** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **ACL Hit Counter Analysis via Streaming Telemetry**): table host, acl_name, sequence_id, description, hits_per_sec, daily_hits
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare `openconfig_acl` hit rates in Splunk to the device’s `show access-list` (or platform equivalent) for the same rule at the end of a quiet hour.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (ACL rules sorted by hit rate), Bar chart (top 10 deny rules by hits), Stacked chart (permit vs deny hits over time), List (zero-hit rules for cleanup).

## SPL

```spl
| mstats rate_avg("openconfig_acl.matched_packets") AS hits_per_sec WHERE index=gnmi_metrics BY host, acl_name, sequence_id, description span=5m
| where hits_per_sec > 0
| eval daily_hits=round(hits_per_sec * 86400, 0)
| table host, acl_name, sequence_id, description, hits_per_sec, daily_hits
| sort -hits_per_sec
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -count
```

## Visualization

Table (ACL rules sorted by hit rate), Bar chart (top 10 deny rules by hits), Stacked chart (permit vs deny hits over time), List (zero-hit rules for cleanup).

## References

- [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
