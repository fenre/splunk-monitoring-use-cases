<!-- AUTO-GENERATED from UC-5.1.4.json — DO NOT EDIT -->

---
id: "5.1.4"
title: "BGP Peer State Changes"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.4 · BGP Peer State Changes

## Description

BGP session drops cause routing convergence, potentially making networks unreachable.

## Value

BGP session drops cause routing convergence, potentially making networks unreachable.

## Implementation

Forward syslog from all BGP speakers. Critical alert on adjacency down. Include neighbor IP and AS number.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog from all BGP speakers. Critical alert on adjacency down. Include neighbor IP and AS number.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%BGP-5-ADJCHANGE" OR "%BGP-3-NOTIFICATION"
| rex "neighbor (?<neighbor_ip>\S+)" | table _time host neighbor_ip _raw | sort -_time
```

Understanding this SPL

**BGP Peer State Changes** — BGP session drops cause routing convergence, potentially making networks unreachable.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **BGP Peer State Changes**): table _time host neighbor_ip _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
On the device, run `show ip bgp summary` (Cisco-style) or the Junos or Arista equivalent and check neighbor state, uptime, and last reset for the peer IP in your log line.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline (critical), Status panel per BGP session, Table.

## SPL

```spl
index=network sourcetype="cisco:ios" "%BGP-5-ADJCHANGE" OR "%BGP-3-NOTIFICATION"
| rex "neighbor (?<neighbor_ip>\S+)" | table _time host neighbor_ip _raw | sort -_time
```

## Visualization

Events timeline (critical), Status panel per BGP session, Table.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
