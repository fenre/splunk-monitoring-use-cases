---
id: "5.1.20"
title: "EIGRP Neighbor Flapping"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.20 · EIGRP Neighbor Flapping

## Description

EIGRP neighbor instability causes route recalculation, increased CPU load, and traffic blackholing during convergence.

## Value

EIGRP neighbor instability causes route recalculation, increased CPU load, and traffic blackholing during convergence.

## Implementation

Collect syslog from Cisco routers. Alert on >2 EIGRP neighbor down events in 15 minutes. Correlate with interface flaps and CPU utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect syslog from Cisco routers. Alert on >2 EIGRP neighbor down events in 15 minutes. Correlate with interface flaps and CPU utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%DUAL-5-NBRCHANGE"
| rex "EIGRP-(?<protocol>IPv4|IPv6) (?<as_number>\d+).*Neighbor (?<neighbor_ip>\S+) \((?<interface>\S+)\) is (?<state>up|down)"
| bin _time span=15m | stats count(eval(state="down")) as downs, count(eval(state="up")) as ups by _time, host, neighbor_ip, interface
| where downs > 2
```

Understanding this SPL

**EIGRP Neighbor Flapping** — EIGRP neighbor instability causes route recalculation, increased CPU load, and traffic blackholing during convergence.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, host, neighbor_ip, interface** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where downs > 2` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (up/down events), Table (neighbor, interface, flap count), Status grid.

## SPL

```spl
index=network sourcetype="cisco:ios" "%DUAL-5-NBRCHANGE"
| rex "EIGRP-(?<protocol>IPv4|IPv6) (?<as_number>\d+).*Neighbor (?<neighbor_ip>\S+) \((?<interface>\S+)\) is (?<state>up|down)"
| bin _time span=15m | stats count(eval(state="down")) as downs, count(eval(state="up")) as ups by _time, host, neighbor_ip, interface
| where downs > 2
```

## Visualization

Timeline (up/down events), Table (neighbor, interface, flap count), Status grid.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
