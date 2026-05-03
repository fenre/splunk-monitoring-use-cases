<!-- AUTO-GENERATED from UC-5.2.36.json — DO NOT EDIT -->

---
id: "5.2.36"
title: "Warm Spare Failover and Appliance Redundancy (Meraki MX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.36 · Warm Spare Failover and Appliance Redundancy (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We catch warm-spare handovers so a spare box taking over is something you know about, not a mystery outage after the fact.*

---

## Description

Ensures warm spare failover mechanism is operational and redundancy is maintained.

## Value

NOC teams monitor Meraki MX warm spare failover events and redundancy status to ensure appliance-level high availability and detect loss of backup protection.

## Implementation

Monitor HA/warm spare events. Alert on status != "active/standby".

## Detailed Implementation

### Prerequisites
* Meraki MX warm spare events. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:appliance`. Key fields: `event_type` (warm_spare), `primary_serial`, `spare_serial`, `failover_state`.
* Meraki warm spare: two MX appliances in active/standby pair using VRRP. When the primary MX fails, the spare assumes gateway duties. Configured in Dashboard > Appliance > Warm spare. Requires two MX devices of the same model in the same network.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Appliance > Warm spare
# Configure primary and spare MX serial numbers
# Enable uplink configuration for the spare
# Syslog: enable Events category
```
Verify:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:appliance") earliest=-30d
| where match(_raw, "(?i)warm.?spare|vrrp|failover|redundancy|standby")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Warm spare failover event tracking:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:appliance") earliest=-30d
| where match(_raw, "(?i)warm.?spare|vrrp|failover|primary.*down|spare.*active")
| eval device=coalesce(serial, host, deviceSerial)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| eval failover_action=case(
    match(_raw, "(?i)spare.*active|failover.*spare|secondary.*active"), "SPARE_ACTIVATED",
    match(_raw, "(?i)primary.*restored|primary.*active|failback"), "PRIMARY_RESTORED",
    match(_raw, "(?i)spare.*lost|spare.*down|redundancy.*lost"), "REDUNDANCY_LOST",
    1==1, "STATUS_CHANGE")
| sort device, _time
| streamstats current=f last(_time) as prev_time last(failover_action) as prev_action by device
| eval failover_duration_min=if(failover_action="PRIMARY_RESTORED" AND prev_action="SPARE_ACTIVATED", round((_time - prev_time)/60, 1), null())
| stats count(eval(failover_action="SPARE_ACTIVATED")) as failovers count(eval(failover_action="REDUNDANCY_LOST")) as redundancy_lost avg(failover_duration_min) as avg_failover_min latest(failover_action) as current_state by network_name
| eval severity=case(
    redundancy_lost > 0, "CRITICAL -- redundancy lost, no warm spare protection",
    current_state="SPARE_ACTIVATED", "WARNING -- running on spare, primary down",
    failovers > 3, "WARNING -- frequent failovers",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) Dashboard: Appliance > Warm spare -- verify primary/spare status.
(b) Test: disable primary MX interface and verify failover occurs.
(c) Verify both MX devices are running same firmware version.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Warm Spare Redundancy"):
* Row 1 -- Single-value: "Networks on spare", "Redundancy lost", "Failover events (30d)".
* Row 2 -- Warm spare event timeline.

Alert: Critical (redundancy lost -- spare unreachable): immediate investigation.

### Step 5 — - Troubleshooting

* **Redundancy lost** -- Spare MX may be offline, powered down, or disconnected. Check physical connectivity and device status in Dashboard.

* **Frequent failovers** -- Primary MX may have intermittent issues (power, cooling, port flapping). Check device health and uplink stability.

* **Failover not occurring** -- Verify VRRP configuration. Both MX devices must be same model and firmware. Check network addressing.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*warm spare*" OR signature="*HA*" OR signature="*redundancy*")
| stats latest(ha_status) as redundancy_status, count as status_change_count by appliance_pair
| where ha_status!="active/standby"
```

## Visualization

HA status dashboard; failover timeline; redundancy health gauge.

## Known False Positives

Rehearsed failovers, firmware rollouts, and power tests create warm-standby messages you already expect.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
