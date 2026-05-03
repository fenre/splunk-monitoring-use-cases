<!-- AUTO-GENERATED from UC-5.1.60.json — DO NOT EDIT -->

---
id: "5.1.60"
title: "Arista MLAG Health and Consistency (Arista)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.60 · Arista MLAG Health and Consistency (Arista)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with arista mlag health and consistency so the team can act before it grows into a bigger outage.*

---

## Description

MLAG pairs depend on matching configuration and a healthy peer link; inconsistency or peer loss can lead to blackholed VLANs or asymmetric forwarding while both switches appear “up.” Catching `config-sanity` failures and peer state changes early prevents subtle application outages that load balancers and servers cannot retry away from. Splunk correlation across both peers speeds root cause when only one side logs the fault.

## Value

NOC teams monitor Arista MLAG peer status, peer-link health, and configuration consistency to ensure dual-homed device redundancy and detect MLAG pair failures.

## Implementation

Ingest syslog from both MLAG peers with synchronized clocks. Alert on peer-link down, partial connectivity, or config-sanity failure strings present in your EOS version. Use a lookup pairing `mlag_domain` or neighbor hostname to open one incident for the pair. Validate against `show mlag` snapshots if you periodically scrape CLI into Splunk.

## Detailed Implementation

### Prerequisites
* Arista MLAG (Multi-Chassis Link Aggregation) health data from syslog or eAPI. Data in `index=arista` or `index=network` with `sourcetype=arista:eos` or `sourcetype=syslog`. Key syslog: `MLAG-4-INACTIVE`, `MLAG-6-PEER_STATUS`, `MLAG-3-CONFIG_CONSISTENCY`. eAPI: `show mlag`.
* Arista MLAG: two Arista switches form a virtual pair, providing active-active link aggregation to downstream devices. MLAG requires: peer-link (trunk between switches), MLAG domain, and consistent configuration. MLAG health depends on: peer reachability, peer-link status, and configuration consistency.

### Step 1 — - Configure data collection
```
# Arista EOS -- syslog forwarding
logging host <splunk-ip>
logging trap informational
logging facility local7

# eAPI scripted input (alternative to syslog)
# Polls: show mlag, show mlag detail
```
Verify:
```spl
index=arista earliest=-24h
| where match(_raw, "(?i)MLAG|mlag|peer.link|peer.status|mlag.*config")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- MLAG health and consistency monitoring:**
```spl
index=arista earliest=-24h
| where match(_raw, "(?i)MLAG|mlag|peer.link|peer.status|config.*consistency")
| eval device=coalesce(host, device_name)
| eval mlag_event=case(
    match(_raw, "(?i)peer.*down|peer.*unreachable|peer.*fail"), "PEER_DOWN",
    match(_raw, "(?i)peer.*up|peer.*active|peer.*established"), "PEER_UP",
    match(_raw, "(?i)peer.link.*down|peer-link.*fail"), "PEER_LINK_DOWN",
    match(_raw, "(?i)config.*inconsist|consistency.*error"), "CONFIG_INCONSISTENCY",
    match(_raw, "(?i)INACTIVE|port.*inactive"), "PORT_INACTIVE",
    match(_raw, "(?i)reload.*delay|MLAG.*reload"), "RELOAD_DELAY",
    1==1, "MLAG_EVENT")
| stats count as events count(eval(mlag_event="PEER_DOWN")) as peer_downs count(eval(mlag_event="CONFIG_INCONSISTENCY")) as config_errors latest(mlag_event) as latest_event by device
| eval severity=case(
    peer_downs > 0, "CRITICAL -- MLAG peer down (no redundancy)",
    match(latest_event, "PEER_LINK_DOWN"), "CRITICAL -- MLAG peer-link down",
    config_errors > 0, "WARNING -- MLAG configuration inconsistency",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show mlag` -- overall MLAG status and peer.
(b) CLI: `show mlag detail` -- detailed peer-link and port-channel status.
(c) CLI: `show mlag config-sanity` -- configuration consistency check.

### Step 4 — - Operationalize
Dashboard ("Arista -- MLAG Health"):
* Row 1 -- Single-value: "MLAG peer status", "Config errors", "Inactive ports".
* Row 2 -- MLAG event timeline.

Alert: Critical (MLAG peer down or peer-link down): dual-homing lost.

### Step 5 — - Troubleshooting

* **MLAG peer down** -- Check: (1) peer switch reachable, (2) MLAG domain ID matches, (3) peer-link physical connectivity. CLI: `show mlag detail` for failure reason.

* **Configuration inconsistency** -- MLAG requires matching configuration on both peers (VLANs, STP, interface config). Run `show mlag config-sanity` for specific mismatches. Fix mismatches on both switches.

* **MLAG port inactive** -- Member port not participating in MLAG. Check: port-channel configuration, LACP status, and that the MLAG ID matches on both peers.

## SPL

```spl
index=network sourcetype="arista:eos"
| search Mlag OR MLAG OR mlag OR "Mlag:" OR "Dual attached" OR "peer-link" OR "inactive"
| rex field=_raw "(?i)Mlag:\s*(?<mlag_msg>[^\n]+)"
| stats count as mlag_events, latest(mlag_msg) as last_summary, values(_raw) as samples by host
| sort -mlag_events
```

## Visualization

MLAG peer pair dashboard; red/amber status per domain; timeline of state transitions.

## Known False Positives

Peer-link upgrades, ISSU, and cable moves trigger MLAG checks. Confirm whether both switches saw the same event.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
