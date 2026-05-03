<!-- AUTO-GENERATED from UC-5.2.34.json — DO NOT EDIT -->

---
id: "5.2.34"
title: "Internet Uplink Failover Events and Recovery Time (Meraki MX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.34 · Internet Uplink Failover Events and Recovery Time (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We see when a site moves between primary and backup internet so the team can confirm a cutover is real, fast, and expected.*

---

## Description

Tracks failover events, recovery time, and uplink behavior to ensure high availability.

## Value

NOC teams track Meraki MX uplink failover events and measure recovery time to assess high-availability effectiveness and identify flapping circuits requiring ISP escalation.

## Implementation

Monitor failover and recovery events from syslog. Calculate recovery MTTR.

## Detailed Implementation

### Prerequisites
* Meraki MX uplink status change events. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:uplinks`. Key fields: `interface` (wan1, wan2, cellular), `status` (active, failed, ready), `failedAt`, `recoveredAt`.
* Meraki Dashboard > Security & SD-WAN > SD-WAN & traffic shaping > Uplink selection controls failover behavior. Events logged when primary WAN fails and traffic shifts to secondary.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Network-wide > General > Reporting
# Enable: Syslog > Flows, Events, IDS Alerts
# Meraki syslog category: uplink change events
```
Verify:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:uplinks") earliest=-7d
| search "uplink" OR "failover" OR "wan" "down" OR "active"
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Uplink failover event tracking:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:uplinks") earliest=-7d
| where match(_raw, "(?i)failover|uplink.*change|wan.*down|wan.*up|connectivity.*change")
| eval device=coalesce(serial, host, deviceSerial)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| eval uplink=coalesce(interface, uplink)
| eval status=coalesce(status, if(match(_raw, "(?i)down|fail|lost"), "FAILED", if(match(_raw, "(?i)up|recover|active"), "RECOVERED", "CHANGE")))
| sort _time
| streamstats current=f last(_time) as prev_time last(status) as prev_status by device
| eval recovery_time_sec=if(status="RECOVERED" AND prev_status="FAILED", _time - prev_time, null())
| eval recovery_min=round(recovery_time_sec/60, 1)
| stats count as events count(eval(status="FAILED")) as failures count(eval(status="RECOVERED")) as recoveries avg(recovery_min) as avg_recovery_min max(recovery_min) as max_recovery_min by device, network_name, uplink
| eval avg_recovery_min=round(avg_recovery_min, 1)
| eval severity=case(failures > 5, "CRITICAL -- frequent failovers (flapping)", avg_recovery_min > 30, "WARNING -- slow recovery time", failures > 0, "INFO -- failover occurred", 1==1, "OK")
| where severity != "OK"
| sort severity, -failures
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Uplink status -- verify failover history.
(b) Check ISP circuit SLA against recovery times.
(c) Correlate with WAN quality degradation (UC-5.2.33) preceding failover.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Uplink Failover"):
* Row 1 -- Single-value: "Failover events (7d)", "Avg recovery (min)", "Sites affected".
* Row 2 -- Failover timeline.
* Row 3 -- Recovery time distribution.

Alert: Critical (>5 failovers in 4 hours for same device): investigate ISP/circuit flapping.

### Step 5 — - Troubleshooting

* **Rapid failover flapping** -- ISP circuit unstable. Check: physical layer (cable/optics), ISP status page, circuit monitoring. Consider increasing failover threshold timers.

* **No recovery event after failure** -- Secondary uplink may also be down. Check warm spare status (UC-5.2.36) and cellular backup (UC-5.2.35).

* **Long recovery time** -- Failover path may have DNS caching, VPN re-establishment, or BGP convergence delays. Check SD-WAN settings.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*failover*" OR signature="*recovery*")
| stats count as failover_count, latest(recovery_time) as recovery_duration by uplink_id, failure_reason
| where failover_count > 0
```

## Visualization

Failover timeline; recovery time gauge; uplink failure cause pie chart.

## Known False Positives

Test failovers, cable swaps, and ISP work can make uplink change messages noisy during business hours.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
