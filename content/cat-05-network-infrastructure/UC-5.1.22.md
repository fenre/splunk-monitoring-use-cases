<!-- AUTO-GENERATED from UC-5.1.22.json — DO NOT EDIT -->

---
id: "5.1.22"
title: "Syslog Source Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.22 · Syslog Source Health

> **Criticality:** High &middot; **Difficulty:** Expert &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with syslog source health so the team can act before it grows into a bigger outage.*

---

## Description

Silence from a device means either it's healthy or its syslog forwarding broke. Detecting missing syslog sources ensures continuous visibility.

## Value

Operations teams monitor syslog source health by tracking device reporting intervals, detecting silent failures where network devices stop sending logs without explicit down notification.

## Implementation

Maintain a device inventory lookup. Schedule a search comparing active syslog sources against inventory. Alert on devices missing for >1 hour.

## Detailed Implementation

### Prerequisites
* Syslog event volume from network devices. Data in `index=network` with various sourcetypes. This UC monitors the health of syslog forwarding itself -- detecting silent device failures where a device stops sending syslog without any down notification.
* Syslog source health: if a device stops sending syslog, it may indicate device failure, network partition, or syslog misconfiguration. Absence of data is as important to detect as presence of error data.

### Step 1 — - Configure data collection
```
# No additional configuration needed -- this monitors existing syslog
# Create a baseline of expected syslog sources

# Lookup: network_devices.csv
# hostname, ip, device_type, site, expected_interval_min
```
Verify:
```spl
index=network earliest=-24h
| stats count dc(sourcetype) as sourcetypes latest(_time) as last_event by host
| eval hours_since=round((now() - last_event)/3600, 1)
| sort -hours_since
```

### Step 2 — - Create the search and alert

**Primary search -- Syslog source health monitoring:**
```spl
index=network earliest=-24h
| stats count as events latest(_time) as last_event by host
| eval hours_since_last=round((now() - last_event)/3600, 1)
| lookup network_devices.csv hostname AS host OUTPUT device_type, site, expected_interval_min
| eval expected_gap_hours=coalesce(expected_interval_min/60, 1)
| eval severity=case(
    hours_since_last > 24, "CRITICAL -- device silent for >24 hours",
    hours_since_last > 4, "WARNING -- device silent for >4 hours",
    hours_since_last > expected_gap_hours AND expected_gap_hours > 0, "INFO -- exceeds expected reporting interval",
    1==1, "OK")
| where severity != "OK"
| eval last_event_time=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| table host, device_type, site, events, last_event_time, hours_since_last, severity
| sort severity, -hours_since_last
```

**Secondary search -- New/missing device detection:**
```spl
| inputlookup network_devices.csv
| eval host=hostname
| join type=left host [search index=network earliest=-24h | stats count latest(_time) as last_seen by host]
| where isnull(count) OR count=0
| eval severity="CRITICAL -- expected device not seen in Splunk"
| table host, device_type, site, severity
```

### Step 3 — - Validate
(a) Ping the silent device to verify reachability.
(b) SSH/console to verify syslog configuration: `show logging` (Cisco).
(c) Check network path between device and Splunk syslog collector.

### Step 4 — - Operationalize
Dashboard ("Network -- Syslog Source Health"):
* Row 1 -- Single-value: "Silent devices", "Active sources", "Missing from inventory".
* Row 2 -- Device last-seen table.

Alert: Critical (device silent > 24h): verify device is operational.

### Step 5 — - Troubleshooting

* **Device reachable but not logging** -- Check syslog configuration: `show logging` (Cisco). Verify logging host IP is correct and syslog is enabled at informational level.

* **Network partition** -- Device may be up but network path to syslog collector is broken. Check routing to syslog collector IP.

* **Device rebooted** -- After reboot, verify syslog configuration persists (saved to startup-config). Some devices lose syslog config if not saved.

## SPL

```spl
| tstats count where index=network sourcetype="cisco:ios" by host
| append [| inputlookup network_device_inventory.csv | rename device as host | fields host]
| stats sum(count) as event_count by host | where event_count=0 OR isnull(event_count)
| table host | rename host as "Silent Devices"
```

## Visualization

Table (silent devices), Single value (count of silent devices), Status grid (all devices).

## Known False Positives

Index maintenance, HF restarts, and UDP drops during firewall rule pushes can look like a silent device. Check forwarder and firewall paths first.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
