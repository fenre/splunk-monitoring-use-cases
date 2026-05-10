<!-- AUTO-GENERATED from UC-5.20.26.json — DO NOT EDIT -->

---
id: "5.20.26"
title: "DAD Proxy Event Tracking"
status: "verified"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-5.20.26 · DAD Proxy Event Tracking

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Configuration, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*When a new device joins the network, it calls out 'Is anyone using address 42?' to make sure the address is free. If two devices are on different floors and cannot hear each other, the building's switchboard relays the call for them. We track when the switchboard has to step in to prevent two devices from accidentally using the same address.*

---

## Description

Tracks DAD Proxy activity on switches with SISF (Switch Integrated Security Features) to monitor duplicate address detection across isolated Layer 2 segments. In environments with private VLANs, wired/wireless isolation, or proxy ARP/NDP, DAD Proxy is essential for preventing address conflicts between hosts that cannot directly communicate at Layer 2. Each DAD Proxy response indicates that the switch intervened to prevent a duplicate address — this is expected in small quantities but can indicate a systematic problem if the rate is high. Excessive DAD Proxy events may indicate: (1) multiple hosts independently choosing the same SLAAC address due to identical IID generation (unlikely with RFC 8981 privacy extensions but possible with stable IIDs), (2) a DAD denial-of-service attack where an attacker responds to all DAD probes to prevent legitimate hosts from obtaining addresses (UC-5.20.87), or (3) a configuration issue where PVLAN or wireless isolation is breaking normal DAD without DAD Proxy enabled.

## Value

DAD Proxy is a 'silent hero' feature that prevents address conflicts in segmented VLANs. Without monitoring, you have no visibility into how often it intervenes. A sudden increase in DAD Proxy events may indicate a change in the network (new segment isolation, new PVLAN configuration) that is causing more address conflicts. A DAD Proxy event for a critical server's address means another device is trying to claim that address — this needs immediate investigation. Tracking DAD Proxy also validates that the feature is working correctly on switches where it is deployed.

## Implementation

Monitor SISF DAD Proxy syslog events. Track event rate per switch and per address. Alert on excessive DAD Proxy activity (>10 events per address per hour) or DAD Proxy events involving critical infrastructure addresses (routers, DNS servers, domain controllers).

## Detailed Implementation

### Prerequisites
- Cisco IOS-XE switches with SISF (device-tracking) enabled.
- DAD Proxy feature enabled on relevant interfaces/VLANs. This is automatically part of SISF when `device-tracking policy` is applied.
- Syslog forwarding from switches to Splunk at informational level (severity 6) to capture SISF events.

### Step 1 — Configure data collection

**Enable SISF with DAD Proxy on Cisco IOS-XE:**
```
device-tracking policy DT_POLICY
 security-level guard
 tracking enable
 logging
!
interface range GigabitEthernet1/0/1 - 48
 device-tracking attach-policy DT_POLICY
```
SISF automatically enables DAD Proxy when `security-level guard` is set. DAD Proxy responses are logged as `%SISF-6-DAD_PROXY_RESPONSE` or related SISF DAD events.

**Verify DAD Proxy is active:**
```
show device-tracking policy DT_POLICY
  Security Level: GUARD
  Device Role: NODE
  DAD: ENABLED
  Tracking: ENABLED
```

**Verification in Splunk:**
```spl
index=network sourcetype="cisco:ios" "%SISF" "DAD" earliest=-7d
| stats count by host
```
Expected: switches with SISF enabled should show DAD events. If zero events, DAD Proxy may not be triggering (no conflicts detected) or syslog level may be too restrictive.

### Step 2 — Create the search and alert

**Primary search — DAD Proxy activity summary:**
```spl
index=network sourcetype="cisco:ios" "%SISF" "DAD" earliest=-24h
| rex field=_raw "(?:address|for)\s+(?<dad_address>[0-9a-fA-F:]+)"
| rex field=_raw "(?:port|interface)\s+(?<port>\S+)"
| rex field=_raw "(?:vlan|VLAN)\s*(?<vlan>\d+)"
| stats count as events dc(dad_address) as unique_addrs values(port) as ports latest(_time) as last_event by host, vlan
| eval last_event=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| sort -events
```

**Alert — excessive DAD Proxy for a single address:**
```spl
index=network sourcetype="cisco:ios" "%SISF" "DAD" earliest=-1h
| rex field=_raw "(?:address|for)\s+(?<dad_address>[0-9a-fA-F:]+)"
| stats count as events by host, dad_address
| where events > 10
```
Trigger: >10 DAD Proxy events for the same address in 1 hour. This indicates persistent address conflict or DAD DoS. Priority: HIGH.

**Alert — DAD Proxy for infrastructure address:**
```spl
index=network sourcetype="cisco:ios" "%SISF" "DAD" earliest=-15m
| rex field=_raw "(?:address|for)\s+(?<dad_address>[0-9a-fA-F:]+)"
| lookup ipv6_infrastructure.csv address as dad_address OUTPUT role
| where isnotnull(role)
| table _time, host, dad_address, role
```
Trigger: any result. A device is trying to claim an infrastructure address (router, DNS, DC). Priority: CRITICAL.

### Step 3 — Validate
(a) **Controlled conflict test (lab).** On a lab VLAN with SISF DAD Proxy, configure two hosts on different switch ports with the same static IPv6 address. The second host's DAD probe should be answered by DAD Proxy, preventing the duplicate. Verify the `%SISF-6-DAD_PROXY_RESPONSE` event appears in Splunk.

(b) **Negative test.** On the same VLAN, assign a unique address to a new host. DAD should complete without a DAD Proxy response (no conflict). Verify no SISF DAD event appears.

(c) **Infrastructure address test.** Attempt to configure a host with the default gateway's IPv6 address. DAD Proxy should respond and the host should fail DAD. Verify the CRITICAL alert fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DAD Proxy Activity"):
- Row 1 — Single-value: total DAD Proxy events (24h), addresses with repeated conflicts.
- Row 2 — Table: DAD Proxy events by switch, VLAN, address, port.
- Row 3 — Timechart: DAD Proxy event rate — should be low and steady.

**Scheduling:** Summary report every 6 hours. Excessive-per-address alert every hour. Infrastructure address alert in real-time.

**Runbook:**
1. Repeated DAD Proxy for same address: identify which ports are claiming the address and whether the conflict is due to static assignment (fix: use unique addresses) or SLAAC collision (rare — investigate IID generation method).
2. Infrastructure address conflict: immediately investigate the port claiming the infrastructure address — this may be a misconfiguration or an address theft attempt.

### Step 5 — Troubleshooting

- **No DAD Proxy events despite SISF being enabled** — DAD Proxy only generates events when it detects an actual conflict (another device already owns the address in the binding table). If all addresses are unique, DAD Proxy silently passes the DAD probes through without logging.

- **DAD Proxy events but no actual conflict** — On some IOS-XE versions, SISF logs DAD activity even when no conflict is found (the log indicates 'DAD probe observed' rather than 'DAD proxy response'). Distinguish between 'observed' (informational) and 'responded' (actual conflict) events.

- **DAD Proxy not working across VLANs** — DAD Proxy operates within a single VLAN/broadcast domain. It cannot detect conflicts between different VLANs even if they use the same prefix (which is a misconfiguration).

## SPL

```spl
index=network sourcetype="cisco:ios" "%SISF" "DAD"
| rex field=_raw "DAD.*(?:for|address)\s+(?<dad_address>[0-9a-fA-F:]+).*(?:port|interface)\s+(?<port>\S+)"
| stats count as dad_events dc(dad_address) as unique_addresses values(dad_address) as addresses by host, port
| sort -dad_events
```

## Visualization

(1) Table: DAD Proxy events by switch, port, and address. (2) Timechart: DAD Proxy event rate over time — flat baseline with spikes indicating issues. (3) Single-value: total DAD Proxy interventions (24h). (4) Alert panel: DAD Proxy events for critical infrastructure addresses.

## Known False Positives

**New host onboarding.** When a new host connects and performs SLAAC, it sends a DAD probe. If DAD Proxy is enabled and no other host has that address, the probe receives no response and the host proceeds. The DAD Proxy only responds if there IS a conflict — so DAD Proxy events always indicate a genuine (though possibly expected) address overlap.

**Privacy extension address rotation.** When hosts generate new temporary addresses (RFC 8981), each new address triggers DAD. If DAD Proxy is enabled, it checks its binding table for conflicts. Most of these checks will result in 'no conflict' (no DAD Proxy response), but occasionally a collision does occur due to the birthday paradox in the IID space.

**VRRP/HSRP VIP DAD.** When a VRRP standby router performs DAD for the VIP address, the DAD Proxy on the switch may respond because the active router already has that address in the binding table. This is expected during failover events.

## References

- [RFC 6957 — Duplicate Address Detection Proxy (DAD-Proxy specification)](https://www.rfc-editor.org/rfc/rfc6957)
- [RFC 4861 — Neighbor Discovery for IP version 6 (§5.4 — Duplicate Address Detection procedure)](https://www.rfc-editor.org/rfc/rfc4861)
- [Cisco SISF Configuration Guide — DAD Proxy and Binding Table operations](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sisf/configuration/xe-17/sisf-xe-17-book.html)
