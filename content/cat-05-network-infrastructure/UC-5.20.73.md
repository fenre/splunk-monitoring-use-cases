<!-- AUTO-GENERATED from UC-5.20.73.json — DO NOT EDIT -->

---
id: "5.20.73"
title: "IPv6 Router Advertisement Spoofing Attack Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.73 · IPv6 Router Advertisement Spoofing Attack Detection

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*In our building, the building manager (router) sends regular announcements telling everyone which exit to use and what the building rules are. If a stranger (attacker) stands in the hallway and starts making fake announcements — 'Use this new exit!' 'The address has changed!' — everyone follows the fake instructions, and the stranger can intercept all the mail and packages. We have guards (RA Guard) who check credentials before allowing anyone to make announcements, and we get an alarm whenever someone without credentials tries.*

---

## Description

Detects IPv6 Router Advertisement (RA) spoofing attacks by monitoring RA Guard violation events and unexpected RA sources. A single spoofed RA can compromise every host on the VLAN simultaneously — redirecting default gateways, injecting rogue DNS servers, and deprecating legitimate addresses. RA Guard on switches blocks rogue RAs, and this detection monitors the RA Guard violation log to identify active attack attempts.

## Value

RA spoofing is the IPv6 equivalent of DHCP starvation combined with ARP poisoning — but more powerful because it compromises every host on the VLAN with a single packet. Tools like THC-IPv6 `fake_router6` make RA spoofing trivial. Even with RA Guard deployed, monitoring RA Guard violations provides critical intelligence: it tells you that someone on your network is actively attempting to launch an RA spoofing attack, which host they're using, and which switch port they're connected to.

## Implementation

Monitor RA Guard violation events from switches. Detect unexpected RA sources not in the authorised router list. Alert on any rogue RA attempt. Correlate with switch port for physical source identification.

## Detailed Implementation

### Prerequisites
- RA Guard enabled on all access switch ports (see UC-5.20.29).
- Authorised router list maintained per VLAN.
- Syslog from switches forwarded to Splunk.

### Step 1 — Configure data collection

**Cisco IOS-XE — RA Guard configuration (recap from UC-5.20.29):**
```
ipv6 nd raguard policy ROUTER-POLICY
 device-role router

ipv6 nd raguard policy HOST-POLICY
 device-role host

interface GigabitEthernet1/0/1
 description UPLINK-TO-ROUTER
 ipv6 nd raguard attach-policy ROUTER-POLICY

interface range GigabitEthernet1/0/2 - 48
 description ACCESS-PORTS
 ipv6 nd raguard attach-policy HOST-POLICY
```
RA Guard blocks RAs on ports configured as `device-role host` and generates syslog violations.

**SISF-based RA validation (IOS-XE 16.x+):**
With SISF `security-level guard`, RA validation is integrated into the device-tracking policy:
```
device-tracking policy DT-GUARD
 security-level guard
```
RAs from non-router ports generate `%SISF-4-PAK_DROP` with reason `RA`.

**Authorised router lookup:**
```csv
vlan,router_link_local,router_mac,router_hostname
100,fe80::1,0000.0c07.ac64,rtr-dist-01
100,fe80::2,0000.0c07.ac65,rtr-dist-02
200,fe80::1,aabb.cc00.0001,rtr-core-01
```
Upload as `authorised_routers.csv`.

**Verification:**
```spl
index=network sourcetype="cisco:ios" ("%SISF" OR "%RA_GUARD" OR "%RAGUARD") earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**RA Guard violation alert:**
```spl
index=network sourcetype="cisco:ios" ("%SISF-4-PAK_DROP" OR "%RA_GUARD" OR "%RAGUARD") "RA" earliest=-15m
| rex field=_raw "(?:source|from|src)\s*=?\s*(?<ra_source>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:MAC|mac)\s*=?\s*(?<ra_mac>[0-9a-fA-F.]+)"
| rex field=_raw "(?:port|Port|IF)\s*=?\s*(?<port>\S+)"
| rex field=_raw "VLAN\s*(?<vlan>\d+)"
| stats count as violations first(_time) as first last(_time) as last by host, port, vlan, ra_source, ra_mac
| eval alert="ROGUE RA BLOCKED: " . violations . " RAs from MAC " . coalesce(ra_mac, "unknown") . " on " . host . " port " . port . " VLAN " . vlan
| sort -violations
```
Trigger: any RA Guard violation. Even one indicates an active attack attempt or a dangerous misconfiguration.

**Unexpected RA source detection (backup for non-RA-Guard environments):**
```spl
index=network sourcetype="cisco:ios" "%ICMPv6" "router advertisement" earliest=-1h
| rex field=_raw "from\s+(?<ra_source>[0-9a-fA-F:.]+)"
| rex field=_raw "interface\s+(?<interface>\S+)"
| lookup authorised_routers.csv router_link_local as ra_source OUTPUT router_hostname
| where isnull(router_hostname)
| eval alert="UNAUTHORISED RA from " . ra_source . " on " . interface . " of " . host . " — NOT in authorised router list"
| table _time, host, interface, ra_source, alert
```

**RA content anomaly detection:**
```spl
index=network sourcetype="cisco:ios" "%ICMPv6" "router advertisement" earliest=-1h
| rex field=_raw "prefix\s+(?<advertised_prefix>[0-9a-fA-F:/]+)"
| rex field=_raw "lifetime\s*=?\s*(?<lifetime>\d+)"
| lookup authorised_prefixes.csv prefix as advertised_prefix OUTPUT authorised
| where isnull(authorised) OR lifetime="0"
| eval issue=case(
    isnull(authorised), "ROGUE PREFIX: " . advertised_prefix . " is not an authorised prefix",
    lifetime="0", "CRITICAL: RA with lifetime=0 will deprecate addresses — DoS attack",
    1=1, "UNKNOWN")
| table _time, host, advertised_prefix, lifetime, issue
```

### Step 3 — Validate
(a) **RA Guard test.** Send a test RA from an access port using `radvd` on a Linux machine. Verify RA Guard blocks it and the alert fires.

(b) **Authorised router test.** Verify legitimate RAs from authorised router ports do NOT trigger the alert.

(c) **Content analysis.** Verify a RA with lifetime=0 is detected as a potential DoS.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RA Security"):
- Row 1 — CRITICAL alert: active RA Guard violations.
- Row 2 — Table: rogue RA events with switch, port, MAC, VLAN details.
- Row 3 — Timechart: RA Guard violations per day.
- Row 4 — Table: unauthorised RA sources not in the allowed router list.

**Scheduling:** RA Guard violations real-time. Unauthorised RA source every 5 minutes.

**Runbook:**
1. RA Guard violation from access port: investigate the connected device immediately. If intentional attack (THC-IPv6 detected), shut the port. If misconfigured device (Windows ICS), remediate configuration.
2. Rogue prefix: never appeared in IPAM/prefix plan. Block at source. Check for rogue DHCPv6 server as well (combined RA+DHCPv6 attack).
3. Lifetime=0 RA: all hosts on the VLAN will lose their IPv6 addresses within seconds. This is a DoS attack. Shut the source port immediately. Verify hosts can re-acquire addresses after the rogue RA is stopped.

### Step 5 — Troubleshooting

- **RA Guard bypass via fragmentation** — RFC 6980 mandates that NDP messages MUST NOT be fragmented. RA Guard implementations that do not enforce this can be bypassed by fragmenting the RA. Ensure the switch firmware enforces RFC 6980.

- **RA Guard on trunks** — RA Guard policies apply per VLAN on trunk ports. Ensure the policy is applied correctly for each VLAN carried on the trunk.

- **SISF integration** — On IOS-XE 16.x+, RA Guard is integrated into SISF. Using both standalone RA Guard and SISF simultaneously may cause conflicts. Prefer SISF `security-level guard` which includes RA Guard functionality.

## SPL

```spl
index=network sourcetype="cisco:ios" ("%SISF-4-PAK_DROP" AND "RA" OR "%IPV6_ND-3-INVALID_RA" OR "%RA_GUARD" OR "%RAGUARD") earliest=-1h
| rex field=_raw "(?:source|from|src)\s*=?\s*(?<ra_source>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:port|Port|IF)\s*=?\s*(?<source_port>\S+)"
| rex field=_raw "(?:VLAN|vlan)\s*(?<vlan>\d+)"
| eval severity=case(
    match(_raw, "PAK_DROP.*RA"), "BLOCKED — RA Guard dropped rogue RA",
    match(_raw, "INVALID_RA"), "BLOCKED — invalid RA detected",
    match(_raw, "RAGUARD.*VIOL"), "CRITICAL — RA Guard violation",
    1=1, "WARNING")
| stats count as events first(_time) as first_seen last(_time) as last_seen by host, source_port, vlan, ra_source, severity
| eval alert="Rogue RA from " . coalesce(ra_source, "unknown") . " on port " . source_port . " VLAN " . vlan . " — " . severity
| sort -events
```

## Visualization

(1) Alert table: rogue RA events with source port, VLAN, and attacker address. (2) Timechart: RA Guard violation rate. (3) Switch port map: which ports are generating rogue RAs. (4) Historical: rogue RA activity over 30 days.

## Known False Positives

**Misconfigured client devices.** Some devices (Windows with ICS enabled, Linux with IPv6 forwarding enabled) may send RAs inadvertently. These are not attacks but are operationally harmful. RA Guard correctly blocks them.

**VMware/hypervisor networking.** Hypervisors with virtual networking that bridges VMs to the physical network may forward RAs from guest VMs. Configure RA Guard on hypervisor uplink ports.

**Wireless access points.** Some APs generate RAs on the client-facing interface. Verify AP IPv6 configuration.

**Network device misplacement.** A router connected to an access port (instead of a trunk/router port) will be blocked by RA Guard. This is an operational misconfiguration, not an attack.

## References

- [RFC 6105 — IPv6 Router Advertisement Guard](https://www.rfc-editor.org/rfc/rfc6105)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.3.2 — RA Guard)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 8106 — IPv6 Router Advertisement Options for DNS Configuration (RDNSS/DNSSL)](https://www.rfc-editor.org/rfc/rfc8106)
