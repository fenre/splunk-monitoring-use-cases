<!-- AUTO-GENERATED from UC-5.1.39.json — DO NOT EDIT -->

---
id: "5.1.39"
title: "Port Security Violations and Rogue Device Detection (Meraki MS)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.1.39 · Port Security Violations and Rogue Device Detection (Meraki MS)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We help you know early when something looks wrong with port security violations and rogue device detection so the team can act before it grows into a bigger outage.*

---

## Description

Detects unauthorized MAC addresses and port security breaches that indicate potential network intrusion.

## Value

Security teams detect Meraki MS port security violations and rogue device connections, identifying unauthorized devices and 802.1X authentication failures on secure switch ports.

## Implementation

Monitor port security violation events from syslog. Create alert for each unique violation.

## Detailed Implementation

### Prerequisites
* Meraki MS port security events from syslog. Data in `index=meraki` with `sourcetype=meraki:events`. Key events: port security violations, sticky MAC, unknown MAC blocked.
* Meraki MS port security: configured per-port via Dashboard. Options: sticky MAC learning, MAC allow-list, and MAC limit per port. Violations generate syslog events and can auto-disable the port.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Switch > Access policies
# Configure access policies with MAC allow-lists
# Per-port: Configure access policy assignment
# Syslog: enable Event log
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(_raw, "(?i)port.*security|MAC.*violation|rogue|unauthorized|802\.1X|radius.*reject")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Port security violations and rogue device detection:**
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)port.*security|MAC.*violation|rogue|unauthorized|blocked.*mac|802\.1X.*fail|radius.*reject|access.*denied")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| rex field=_raw "(?i)(?:MAC|mac).*?(?<violating_mac>[0-9a-fA-F:]{12,17})"
| rex field=_raw "(?i)(?:port|Port)\s+(?<port_id>\d+)"
| eval violation_type=case(
    match(_raw, "(?i)rogue|unknown"), "ROGUE_DEVICE",
    match(_raw, "(?i)802\.1X.*fail|radius.*reject"), "AUTH_FAILURE",
    match(_raw, "(?i)MAC.*violation|security.*violat"), "MAC_VIOLATION",
    1==1, "PORT_SECURITY")
| stats count as violations dc(violating_mac) as unique_macs values(violating_mac) as macs values(port_id) as ports by network_name, device, violation_type
| eval severity=case(
    violation_type="ROGUE_DEVICE", "CRITICAL -- rogue device detected",
    violations > 20, "WARNING -- frequent ".violation_type." events",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -violations
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports -- check port status and connected clients.
(b) Dashboard: Network-wide > Clients -- identify the device by MAC address.
(c) Verify access policy configuration on the port.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Port Security"):
* Row 1 -- Single-value: "Security violations (24h)", "Rogue devices", "Auth failures".
* Row 2 -- Port security violation table.

Alert: Critical (rogue device on secure port): investigate immediately.

### Step 5 — - Troubleshooting

* **Rogue device detected** -- Identify MAC, check against inventory. If unauthorized, disable port. Investigate physical location.

* **Frequent auth failures** -- Check RADIUS server connectivity and credentials. Verify supplicant configuration on the client device.

* **Legitimate device blocked** -- Add MAC to allow-list or update access policy. Ensure RADIUS server has the correct user/device entry.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Port Security*" OR signature="*Unauthorized*")
| stats count as violation_count by switch_name, port_id, mac_address
| where violation_count > 0
| sort - violation_count
```

## Visualization

Table of violations; timeline of events; network detail with affected ports.

## Known False Positives

Meraki cloud delays, dashboard API limits, and large site templates can look like a gap. Confirm in dashboard before opening a P1 on Splunk only.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
