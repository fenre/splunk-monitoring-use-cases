<!-- AUTO-GENERATED from UC-5.1.20.json — DO NOT EDIT -->

---
id: "5.1.20"
title: "EIGRP Neighbor Flapping"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.20 · EIGRP Neighbor Flapping

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Anomaly, Availability

*We help you know early when something looks wrong with eigrp neighbor flapping so the team can act before it grows into a bigger outage.*

---

## Description

EIGRP neighbor instability causes route recalculation, increased CPU load, and traffic blackholing during convergence.

## Value

NOC teams detect EIGRP neighbor flapping on Cisco routers, identifying hold timer expirations and adjacency instability that cause routing reconvergence and traffic disruption.

## Implementation

Collect syslog from Cisco routers. Alert on >2 EIGRP neighbor down events in 15 minutes. Correlate with interface flaps and CPU utilization.

## Detailed Implementation

### Prerequisites
* EIGRP neighbor flapping syslog messages. Data in `index=network` with `sourcetype=cisco:ios`. Key mnemonics: `%DUAL-5-NBRCHANGE` (neighbor up/down), `%EIGRP-5-NBRCHANGE`.
* EIGRP neighbors: routers in the same EIGRP AS form adjacencies via Hello packets (multicast 224.0.0.10). Neighbor loss triggers DUAL recalculation and potentially route recalculation. Flapping causes constant reconvergence, increased CPU, and traffic disruption.

### Step 1 — - Configure data collection
```
# Cisco IOS -- EIGRP neighbor changes are logged by default
# Ensure syslog includes informational level
logging host <splunk-syslog-ip>
logging trap informational

# Optional: EIGRP event logging
router eigrp <asn>
 eigrp log-neighbor-changes
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)DUAL.*NBRCHANGE|EIGRP.*NBRCHANGE|eigrp.*neighbor|eigrp.*down|eigrp.*up")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- EIGRP neighbor flapping detection:**
```spl
index=network earliest=-24h
| where match(_raw, "(?i)DUAL.*NBRCHANGE|EIGRP.*NBRCHANGE|eigrp.*neighbor")
| rex field=_raw "(?i)(?:neighbor|Neighbor|Nbr)\s+(?<neighbor_ip>\d+\.\d+\.\d+\.\d+)"
| rex field=_raw "(?i)(?<eigrp_state>is\s+(?:up|down))"
| eval neighbor=coalesce(neighbor_ip, eigrp_neighbor)
| eval state=if(match(_raw, "(?i)is\s+down|went.*down|lost|dead"), "down", "up")
| eval device=coalesce(host, device_name)
| sort device, neighbor, _time
| stats count as events count(eval(state="down")) as down_events count(eval(state="up")) as up_events latest(state) as current_state by device, neighbor
| eval flapping=if(events > 4, "YES", "NO")
| eval severity=case(
    current_state="down" AND flapping="YES", "CRITICAL -- EIGRP neighbor DOWN and flapping",
    current_state="down", "WARNING -- EIGRP neighbor DOWN",
    flapping="YES", "WARNING -- EIGRP neighbor flapping",
    1==1, "OK")
| where severity != "OK"
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show eigrp neighbors` -- verify current neighbor states.
(b) CLI: `show eigrp topology` -- check route status.
(c) CLI: `show ip eigrp interfaces detail` -- check hello/hold timers.

### Step 4 — - Operationalize
Dashboard ("Network -- EIGRP Neighbors"):
* Row 1 -- Single-value: "Neighbors DOWN", "Flapping neighbors".
* Row 2 -- EIGRP neighbor event timeline.

Alert: Critical (EIGRP neighbor DOWN on WAN link): routing impact.

### Step 5 — - Troubleshooting

* **Hold timer expired** -- Hello packets not received. Check: interface status, ACLs blocking multicast 224.0.0.10, K-value mismatch between neighbors.

* **Stuck in Active (SIA)** -- DUAL query not answered in time. Check downstream neighbor CPU and convergence. Adjust: `timers active-time`.

* **K-value mismatch** -- All EIGRP neighbors must have matching K-values. Check: `show ip eigrp interfaces detail | include K-value`. Mismatch prevents adjacency formation.

## SPL

```spl
index=network sourcetype="cisco:ios" "%DUAL-5-NBRCHANGE"
| rex "EIGRP-(?<protocol>IPv4|IPv6) (?<as_number>\d+).*Neighbor (?<neighbor_ip>\S+) \((?<interface>\S+)\) is (?<state>up|down)"
| bin _time span=15m | stats count(eval(state="down")) as downs, count(eval(state="up")) as ups by _time, host, neighbor_ip, interface
| where downs > 2
```

## Visualization

Timeline (up/down events), Table (neighbor, interface, flap count), Status grid.

## Known False Positives

EIGRP neighbor churn can follow redistribution changes, serial link clocking work, or lab reruns—compare to change records before treating as a fault.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
