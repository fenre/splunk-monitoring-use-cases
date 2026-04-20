---
id: "5.1.5"
title: "OSPF Neighbor Adjacency"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.5 · OSPF Neighbor Adjacency

## Description

OSPF neighbor loss triggers SPF recalculation, disrupting traffic.

## Value

OSPF neighbor loss triggers SPF recalculation, disrupting traffic.

## Implementation

Forward syslog from all OSPF routers. Alert on adjacency changes to/from FULL. Track frequency for instability.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog from all OSPF routers. Alert on adjacency changes to/from FULL. Track frequency for instability.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%OSPF-5-ADJCHG"
| rex "Nbr (?<neighbor_ip>\S+) on (?<interface>\S+) from (?<from_state>\S+) to (?<to_state>\S+)"
| table _time host neighbor_ip interface from_state to_state
```

Understanding this SPL

**OSPF Neighbor Adjacency** — OSPF neighbor loss triggers SPF recalculation, disrupting traffic.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **OSPF Neighbor Adjacency**): table _time host neighbor_ip interface from_state to_state


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table (router, neighbor, states).

## SPL

```spl
index=network sourcetype="cisco:ios" "%OSPF-5-ADJCHG"
| rex "Nbr (?<neighbor_ip>\S+) on (?<interface>\S+) from (?<from_state>\S+) to (?<to_state>\S+)"
| table _time host neighbor_ip interface from_state to_state
```

## Visualization

Events timeline, Table (router, neighbor, states).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
