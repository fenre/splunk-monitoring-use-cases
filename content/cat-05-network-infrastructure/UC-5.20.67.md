<!-- AUTO-GENERATED from UC-5.20.67.json — DO NOT EDIT -->

---
id: "5.20.67"
title: "IPv6 East-West Lateral Movement Detection via Flow Analysis"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.20.67 · IPv6 East-West Lateral Movement Detection via Flow Analysis

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*Even if we didn't set up the new door system (IPv6) in our building, every room already has a small side door (link-local) that people can use to talk to their neighbours directly. We can't see this side-door traffic from the main security desk. So we put small cameras near each corridor to watch for someone going door-to-door through the building, which would indicate they're looking for something they shouldn't be finding.*

---

## Description

Detects IPv6 lateral movement and internal reconnaissance by analysing east-west flow data for unusual connection patterns. Because all modern operating systems have IPv6 enabled by default, attackers can use IPv6 for lateral movement even on networks that consider themselves IPv4-only. Link-local IPv6 communication between hosts on the same VLAN requires no infrastructure support — no DHCP server, no router, no DNS — and is often completely unmonitored.

## Value

IPv6 lateral movement is the most undermonitored attack vector in enterprise networks. An attacker who compromises a single host can discover all IPv6 neighbours via NDP (a built-in protocol feature, not a scan), then communicate with them over link-local addresses that are invisible to router-based flow monitoring. East-west IPv6 flow analysis from switch SPAN ports, Zeek/Corelight sensors, or host-based agents closes this critical blind spot.

## Implementation

Deploy flow sensors (Zeek, Corelight, or switch mirror sessions) to capture east-west IPv6 traffic. Analyse flow patterns for reconnaissance indicators: high destination count, port scanning, unusual protocol usage. Baseline normal east-west IPv6 patterns. Alert on deviations.

## Detailed Implementation

### Prerequisites
- East-west flow visibility via Zeek/Corelight sensor, switch SPAN/TAP, or host-based flow agents.
- Router-based NetFlow alone is insufficient — it misses link-local and intra-VLAN IPv6 traffic.
- Baseline of normal east-west IPv6 patterns (typically very low in early IPv6 deployments).

### Step 1 — Configure data collection

**Zeek/Corelight (preferred for east-west):**
Zeek automatically logs all connections including IPv6. Deploy Zeek sensor on switch SPAN ports or network TAPs:
```
# Zeek conn.log contains IPv6 connections automatically
# No special configuration needed for IPv6
# Fields: id.orig_h, id.resp_h, id.resp_p, proto, duration, orig_bytes, resp_bytes
```

Forward Zeek logs to Splunk using the Zeek TA:
```
[monitor:///opt/zeek/logs/current/conn.log]
index = network
sourcetype = zeek:conn
```

**Switch-based flow (Cisco Nexus — NX-OS):**
```
flow record IPV6-EAST-WEST
 match ipv6 source address
 match ipv6 destination address
 match transport source-port
 match transport destination-port
 collect counter bytes long
 collect counter packets long

flow monitor IPV6-EW-MON
 record IPV6-EAST-WEST
 exporter SPLUNK-COLLECTOR

interface Vlan100
 ipv6 flow monitor IPV6-EW-MON input
```

**Host-based (Windows Event Tracing for Network):**
Windows ETW can capture IPv6 connection events. Use Splunk Universal Forwarder with Windows TA:
```
[WinEventLog://Microsoft-Windows-NetworkProfile/Operational]
disabled = 0
index = endpoint
```

**Verification:**
```spl
index=network sourcetype="zeek:conn" earliest=-1h
| eval is_ipv6=if(match(src_ip, ":") OR match(id_orig_h, ":"), 1, 0)
| stats count(eval(is_ipv6=1)) as ipv6_conns count(eval(is_ipv6=0)) as ipv4_conns
```

### Step 2 — Create the search and alert

**IPv6 lateral discovery detection:**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="netflow") earliest=-1h
| eval src=coalesce(id_orig_h, src)
| eval dest=coalesce(id_resp_h, dest)
| eval is_ipv6=if(match(src, ":") AND match(dest, ":"), 1, 0)
| where is_ipv6=1
| eval src_scope=case(
    match(src, "^[Ff][Ee][89AaBb]"), "link-local",
    match(src, "^[Ff][CcDd]"), "ULA",
    1=1, "global")
| stats count as conns dc(dest) as unique_dests dc(coalesce(id_resp_p, dest_port)) as unique_ports values(coalesce(id_resp_p, dest_port)) as ports_contacted by src, src_scope
| where unique_dests > 15
| eval severity=case(
    unique_dests > 50, "CRITICAL — active IPv6 network scan",
    unique_dests > 30, "HIGH — broad IPv6 lateral contact",
    unique_dests > 15, "MEDIUM — elevated IPv6 lateral movement",
    1=1, "LOW")
| sort -unique_dests
```

**Link-local covert channel detection:**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="netflow") earliest=-4h
| eval src=coalesce(id_orig_h, src)
| eval dest=coalesce(id_resp_h, dest)
| where match(src, "^[Ff][Ee]80:") AND match(dest, "^[Ff][Ee]80:")
| stats count as flows sum(coalesce(orig_bytes, bytes)) as total_bytes by src, dest
| where total_bytes > 10000000
| eval alert="Significant link-local IPv6 traffic: " . round(total_bytes/1048576, 1) . " MB between " . src . " and " . dest . " — potential covert channel"
```
Link-local traffic above a few KB (NDP overhead) is unusual. Large volumes indicate data exfiltration or lateral C2.

### Step 3 — Validate
(a) **Scan simulation.** From a test host, ping multiple IPv6 destinations within the subnet. Verify the lateral discovery alert fires.

(b) **Link-local baseline.** Measure normal link-local traffic volume (should be primarily NDP — a few hundred bytes per minute per host).

(c) **False positive tuning.** Identify legitimate high-destination-count hosts (monitoring systems, load balancers) and add to exclusion list.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — East-West Security"):
- Row 1 — Alert panel: hosts with lateral movement indicators.
- Row 2 — Network graph: top IPv6 internal communication relationships.
- Row 3 — Timechart: east-west IPv6 flow volume (should be stable or slowly growing).
- Row 4 — Table: link-local traffic summary (should be near-zero data volume).

**Scheduling:** Lateral movement detection every 15 minutes. Link-local covert channel every 1 hour. Weekly trending.

**Runbook:**
1. High destination count from single source: investigate host immediately. Check for compromised endpoint, running tools (nmap, THC-IPv6), or misconfigured application.
2. Significant link-local data transfer: this is almost always malicious or deeply misconfigured. Investigate both endpoints.
3. New IPv6 communication pattern: compare with approved IPv6 communication matrix. Unexpected pairs should be investigated.

### Step 5 — Troubleshooting

- **SPAN port IPv6 visibility** — Verify the SPAN port captures IPv6 traffic. Some older switch configurations only mirror IPv4 traffic. Test by generating known IPv6 traffic and verifying it appears in the sensor.

- **VLAN trunking** — If monitoring an 802.1Q trunk, ensure the Zeek sensor is configured to process VLAN tags. IPv6 link-local traffic is VLAN-specific.

- **IPv6 multicast filtering** — NDP generates significant multicast traffic (FF02::1, FF02::2, FF02::1:FF00:0/104). Filter these from lateral movement analysis to reduce noise, but do NOT filter them from the link-local covert channel detection — multicast abuse is a real attack vector.

## SPL

```spl
index=network (sourcetype="netflow" OR sourcetype="zeek:conn") earliest=-1h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| eval src_type=case(
    match(src, "^[Ff][Ee][89AaBb]"), "link-local",
    match(src, "^[Ff][CcDd]"), "ULA",
    match(src, "^2"), "global",
    1=1, "other")
| eval is_internal=if(cidrmatch("2001:db8:corporate::/48", src) AND cidrmatch("2001:db8:corporate::/48", dest), 1, 0)
| where is_internal=1 OR src_type="link-local" OR src_type="ULA"
| stats count as flows sum(bytes) as bytes dc(dest) as unique_dests dc(dest_port) as unique_ports by src
| where unique_dests > 20 OR unique_ports > 50
| eval alert=case(
    unique_dests > 50 AND unique_ports > 10, "HIGH — IPv6 host scan: " . unique_dests . " destinations, " . unique_ports . " ports",
    unique_dests > 20, "MEDIUM — IPv6 lateral discovery: " . unique_dests . " unique destinations",
    unique_ports > 50, "MEDIUM — IPv6 port scan: " . unique_ports . " ports from single source",
    1=1, "LOW")
| sort -unique_dests
```

## Visualization

(1) Network graph: IPv6 east-west communication topology. (2) Table: top IPv6 internal talkers by unique destinations. (3) Timechart: east-west IPv6 flow volume trending. (4) Alert table: hosts exhibiting lateral movement indicators.

## Known False Positives

**Network management tools.** Monitoring systems like PRTG, LibreNMS, or Nagios that poll many hosts over IPv6 will show high destination counts. Exclude known monitoring sources.

**Service discovery protocols.** mDNS (FF02::FB), LLMNR, and SSDP generate legitimate multicast traffic that can appear as lateral movement. Filter known multicast destinations.

**Cluster communication.** Kubernetes pods, Docker containers, and hypervisor clusters communicate extensively over IPv6 within the cluster. Baseline cluster traffic patterns.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.2 — monitoring considerations)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 7707 — Network Reconnaissance in IPv6 Networks (lateral discovery techniques)](https://www.rfc-editor.org/rfc/rfc7707)
