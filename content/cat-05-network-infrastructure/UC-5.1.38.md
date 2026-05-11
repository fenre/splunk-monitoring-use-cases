<!-- AUTO-GENERATED from UC-5.1.38.json — DO NOT EDIT -->

---
id: "5.1.38"
title: "Spanning Tree Protocol (STP) Topology Changes (Meraki MS)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.38 · Spanning Tree Protocol (STP) Topology Changes (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with spanning tree protocol so the team can act before it grows into a bigger outage.*

---

## Description

Alerts on unexpected STP topology changes that indicate link failures or network configuration issues.

## Value

Network engineers monitor Meraki MS STP topology changes, root bridge stability, and BPDU guard violations to detect network loops and unauthorized switch connections.

## Implementation

1. Configure SC4S to receive Meraki MS syslog on UDP/514 (or a dedicated port per https://splunk.github.io/splunk-connect-for-syslog/main/sources/vendor/Cisco/cisco_meraki/). 2. In Meraki Dashboard go to Network-wide -> General -> Reporting and add the SC4S syslog server with role 'Switch event log'. 3. STP topology changes appear as type=events with 'STP', 'STP BPDU', 'STP role' in the body. 4. Use rex to extract port_id and role; threshold count > 3 in 24h to alert on unstable spanning-tree topologies.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. STP events are emitted as type=events with message bodies like 'Port 5 received an STP BPDU from <mac> so the port was blocked' and 'Port 5 changed STP role from designated to alternate'. Use rex to extract port_id and the role transition..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S to receive Meraki MS syslog on UDP/514 (or a dedicated port per https://splunk.github.io/splunk-connect-for-syslog/main/sources/vendor/Cisco/cisco_meraki/). 2. In Meraki Dashboard go to Network-wide -> General -> Reporting and add the SC4S syslog server with role 'Switch event log'. 3. STP topology changes appear as type=events with 'STP', 'STP BPDU', 'STP role' in the body. 4. Use rex to extract port_id and role; threshold count > 3 in 24h to alert on unstable spanning-tree to…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    ("STP" OR "spanning-tree" OR "STP role" OR "STP BPDU")
    earliest=-24h
| rex "Port (?<port_id>\d+) (?:received|changed STP role from (?<from_role>\S+) to (?<to_role>\S+))"
| stats count as change_count,
        values(from_role) as from_roles,
        values(to_role) as to_roles
         by host, port_id
| where change_count > 3
| sort - change_count
```

#### Understanding this SPL

**Spanning Tree Protocol (STP) Topology Changes (Meraki MS)** — Network engineers monitor Meraki MS STP topology changes, root bridge stability, and BPDU guard violations to detect network loops and unauthorized switch connections.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. STP events are emitted as type=events with message bodies like 'Port 5 received an STP BPDU from <mac> so the port was blocked' and 'Port 5 changed STP role from designated to alternate'. Use rex to extract port_id and the role transition. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host, port_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where change_count > 3` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline of topology changes; table of affected switches; alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    ("STP" OR "spanning-tree" OR "STP role" OR "STP BPDU")
    earliest=-24h
| rex "Port (?<port_id>\d+) (?:received|changed STP role from (?<from_role>\S+) to (?<to_role>\S+))"
| stats count as change_count,
        values(from_role) as from_roles,
        values(to_role) as to_roles
         by host, port_id
| where change_count > 3
| sort - change_count
```

## Visualization

Timeline of topology changes; table of affected switches; alert dashboard.

## Known False Positives

STP TCNs happen during access switch adds, link moves, and voice VLAN changes. Storm-control tuning can also shift TC rates.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
