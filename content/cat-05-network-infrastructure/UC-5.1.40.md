<!-- AUTO-GENERATED from UC-5.1.40.json — DO NOT EDIT -->

---
id: "5.1.40"
title: "Switch Interface Up/Down Events and Link Flapping (Meraki MS)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.40 · Switch Interface Up/Down Events and Link Flapping (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with switch interface up/down events and link flapping so the team can act before it grows into a bigger outage.*

---

## Description

Identifies port flapping, cable issues, and unstable link states that cause intermittent connectivity.

## Value

NOC teams detect Meraki MS switch interface up/down events and link flapping, enabling rapid identification of cable failures and unstable links affecting downstream connectivity.

## Implementation

Track interface up/down state changes over 24 hours. Alert on flapping (>2 changes/hour).

## Detailed Implementation

### Prerequisites
* Meraki MS interface up/down events from syslog. Data in `index=meraki` with `sourcetype=meraki:events`. Key events: port up, port down, link flapping.
* Meraki MS logs port status changes via syslog. Link flapping (rapid up/down cycling) indicates cable issues, SFP problems, or auto-negotiation failures.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Network-wide > General > Reporting
# Syslog: enable Event log (includes port status changes)
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)port.*up|port.*down|link.*up|link.*down|connected|disconnected")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Interface up/down and link flapping:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)port.*up|port.*down|link.*up|link.*down|connected|disconnected|flap")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| rex field=_raw "(?i)(?:port|Port)\s+(?<port_id>\d+)"
| eval state=if(match(_raw, "(?i)down|disconnect"), "DOWN", "UP")
| sort device, port_id, _time
| stats count as events count(eval(state="DOWN")) as downs count(eval(state="UP")) as ups latest(state) as current by device, network_name, port_id
| eval flapping=if(events > 4, "YES", "NO")
| eval severity=case(
    current="DOWN" AND flapping="YES", "CRITICAL -- port ".port_id." DOWN and flapping",
    current="DOWN", "WARNING -- port ".port_id." DOWN",
    flapping="YES", "WARNING -- port ".port_id." flapping",
    1==1, "OK")
| where severity != "OK"
| sort severity, -events
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports -- check port status and connected device.
(b) Dashboard: Live tools > Cable test -- test cable on affected port.
(c) Check port configuration and connected device.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Port Status"):
* Row 1 -- Single-value: "Ports DOWN", "Flapping ports".
* Row 2 -- Port status event timeline.

Alert: Critical (uplink port DOWN): connectivity impact to downstream devices.

### Step 5 — - Troubleshooting

* **Port flapping** -- Run cable test from Dashboard. Replace patch cable. Check SFP module.

* **Port DOWN after change** -- Verify VLAN assignment, access policy, and PoE settings.

* **Uplink DOWN** -- Check upstream switch port status. Verify SFP compatibility.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*link*" OR signature="*Interface*" OR signature="*up*" OR signature="*down*")
| stats count as event_count by switch_name, port_id
| eval flap_rate=round(event_count/24, 2)
| where flap_rate > 2
```

## Visualization

Time-series showing flap events; table of affected ports; link state history.

## Known False Positives

Meraki cloud delays, dashboard API limits, and large site templates can look like a gap. Confirm in dashboard before opening a P1 on Splunk only.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
