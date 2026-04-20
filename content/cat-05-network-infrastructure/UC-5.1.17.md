---
id: "5.1.17"
title: "Duplex Mismatch Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.17 · Duplex Mismatch Detection

## Description

Duplex mismatches degrade link performance silently. They cause late collisions, CRC errors, and reduced throughput that are hard to diagnose.

## Value

Duplex mismatches degrade link performance silently. They cause late collisions, CRC errors, and reduced throughput that are hard to diagnose.

## Implementation

Enable CDP/LLDP on all interfaces. Monitor syslog for duplex mismatch messages. Cross-reference with SNMP interface counters showing late collisions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP Modular Input, IF-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`, `sourcetype=snmp:interface`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CDP/LLDP on all interfaces. Monitor syslog for duplex mismatch messages. Cross-reference with SNMP interface counters showing late collisions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%CDP-4-DUPLEX_MISMATCH"
| rex "duplex mismatch discovered on (?<local_intf>\S+).*with (?<remote_device>\S+) (?<remote_intf>\S+)"
| stats count latest(_time) as last_seen by host, local_intf, remote_device, remote_intf
| sort -last_seen
```

Understanding this SPL

**Duplex Mismatch Detection** — Duplex mismatches degrade link performance silently. They cause late collisions, CRC errors, and reduced throughput that are hard to diagnose.

Documented **Data sources**: `sourcetype=cisco:ios`, `sourcetype=snmp:interface`. **App/TA** (typical add-on context): SNMP Modular Input, IF-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, local_intf, remote_device, remote_intf** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (local device/interface → remote device/interface), Alert list.

## SPL

```spl
index=network sourcetype="cisco:ios" "%CDP-4-DUPLEX_MISMATCH"
| rex "duplex mismatch discovered on (?<local_intf>\S+).*with (?<remote_device>\S+) (?<remote_intf>\S+)"
| stats count latest(_time) as last_seen by host, local_intf, remote_device, remote_intf
| sort -last_seen
```

## Visualization

Table (local device/interface → remote device/interface), Alert list.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
