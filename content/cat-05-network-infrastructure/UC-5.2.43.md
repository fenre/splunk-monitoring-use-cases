---
id: "5.2.43"
title: "Juniper SRX Cluster Failover Events (Juniper SRX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.43 · Juniper SRX Cluster Failover Events (Juniper SRX)

## Description

Chassis-clustered SRX devices use redundancy groups (RGs) so services fail over when a node, link, or priority changes. JSRPD and cluster-related messages record RG ownership changes, interface monitoring triggers, and manual switchovers. Frequent or flapping failovers point to unstable fabric links, NIC or RE problems, or split-brain risk. Tracking RG state, reason strings, and duration helps you distinguish planned maintenance from emerging hardware or path faults.

## Value

Chassis-clustered SRX devices use redundancy groups (RGs) so services fail over when a node, link, or priority changes. JSRPD and cluster-related messages record RG ownership changes, interface monitoring triggers, and manual switchovers. Frequent or flapping failovers point to unstable fabric links, NIC or RE problems, or split-brain risk. Tracking RG state, reason strings, and duration helps you distinguish planned maintenance from emerging hardware or path faults.

## Implementation

Forward cluster member syslogs with millisecond timestamps and synchronized NTP. Alert on any RG primary change, interface monitoring-driven failover, or unexpected preempt. Dashboard current RG primary per cluster ID and correlate with interface `up`/`down` events on fabric/control links. For active/active designs, track both RGs independently. Keep runbooks for manual `request chassis cluster failover` versus automatic events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_juniper` (Splunkbase 2847), syslog.
• Ensure the following data sources are available: `sourcetype=juniper:junos:structured`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward cluster member syslogs with millisecond timestamps and synchronized NTP. Alert on any RG primary change, interface monitoring-driven failover, or unexpected preempt. Dashboard current RG primary per cluster ID and correlate with interface `up`/`down` events on fabric/control links. For active/active designs, track both RGs independently. Keep runbooks for manual `request chassis cluster failover` versus automatic events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="juniper:junos:structured"
  (lower(process)="jsrpd" OR match(_raw, "(?i)chassis cluster|redundancy group|RG-\d+|failover|switchover"))
| rex "(?i)redundancy group (?<rg_id>\d+)"
| rex "(?i)Reason:\s*(?<failover_reason>[^\|]+)"
| rex "(?i)interface (?<ifname>\S+) (?<if_state>up|down)"
| table _time host rg_id failover_reason ifname if_state process _raw
| sort -_time
```

Understanding this SPL

**Juniper SRX Cluster Failover Events (Juniper SRX)** — Chassis-clustered SRX devices use redundancy groups (RGs) so services fail over when a node, link, or priority changes. JSRPD and cluster-related messages record RG ownership changes, interface monitoring triggers, and manual switchovers. Frequent or flapping failovers point to unstable fabric links, NIC or RE problems, or split-brain risk. Tracking RG state, reason strings, and duration helps you distinguish planned maintenance from emerging hardware or path faults.

Documented **Data sources**: `sourcetype=juniper:junos:structured`. **App/TA** (typical add-on context): `Splunk_TA_juniper` (Splunkbase 2847), syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: juniper:junos:structured. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="juniper:junos:structured". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Juniper SRX Cluster Failover Events (Juniper SRX)**): table _time host rg_id failover_reason ifname if_state process _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failover markers), Table (RG, reason, node), Status panel (current primary per cluster).

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
  (lower(process)="jsrpd" OR match(_raw, "(?i)chassis cluster|redundancy group|RG-\d+|failover|switchover"))
| rex "(?i)redundancy group (?<rg_id>\d+)"
| rex "(?i)Reason:\s*(?<failover_reason>[^\|]+)"
| rex "(?i)interface (?<ifname>\S+) (?<if_state>up|down)"
| table _time host rg_id failover_reason ifname if_state process _raw
| sort -_time
```

## Visualization

Timeline (failover markers), Table (RG, reason, node), Status panel (current primary per cluster).

## References

- [Splunkbase app 2847](https://splunkbase.splunk.com/app/2847)
