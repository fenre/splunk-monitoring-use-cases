<!-- AUTO-GENERATED from UC-5.6.6.json — DO NOT EDIT -->

---
id: "5.6.6"
title: "DHCP Rogue Server Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.6.6 · DHCP Rogue Server Detection

## Description

Rogue DHCP servers assign wrong IPs/gateways, causing network disruption and potential MitM attacks.

## Value

Rogue DHCP servers assign wrong IPs/gateways, causing network disruption and potential MitM attacks.

## Implementation

Enable DHCP snooping on switches. Forward syslog. Alert on any rogue DHCP server detection events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Network syslog, DHCP snooping logs.
• Ensure the following data sources are available: DHCP conflict events, switch DHCP snooping.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DHCP snooping on switches. Forward syslog. Alert on any rogue DHCP server detection events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network "DHCP" AND ("rogue" OR "conflict" OR "unauthorized" OR "snooping violation")
| table _time host src _raw | sort -_time
```

Understanding this SPL

**DHCP Rogue Server Detection** — Rogue DHCP servers assign wrong IPs/gateways, causing network disruption and potential MitM attacks.

Documented **Data sources**: DHCP conflict events, switch DHCP snooping. **App/TA** (typical add-on context): Network syslog, DHCP snooping logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network.

**Pipeline walkthrough**

• Scopes the data: index=network. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **DHCP Rogue Server Detection**): table _time host src _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
On the switches that run DHCP snooping, compare the syslog times and client MACs to the interface or violation counters in the switch CLI or NMS. In Infoblox or Windows DHCP, confirm there is only one authorized server per VLAN where you expect it.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events list (critical), Table, Map.

## SPL

```spl
index=network "DHCP" AND ("rogue" OR "conflict" OR "unauthorized" OR "snooping violation")
| table _time host src _raw | sort -_time
```

## Visualization

Events list (critical), Table, Map.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
