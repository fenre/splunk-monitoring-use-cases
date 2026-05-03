<!-- AUTO-GENERATED from UC-5.20.59.json — DO NOT EDIT -->

---
id: "5.20.59"
title: "MAP-E/MAP-T and DS-Lite IPv4-as-a-Service Health Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "ITSI"
---

# UC-5.20.59 · MAP-E/MAP-T and DS-Lite IPv4-as-a-Service Health Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** ITSI &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*As we switch from the old phone system (IPv4) to the new one (IPv6), we still need the old system to work for services that haven't switched yet. There's a special converter that lets new-system users call old-system numbers. We watch this converter to make sure it has enough phone lines and isn't dropping calls — because if it breaks, new-system users can't reach anyone on the old system.*

---

## Description

Monitors the health of IPv4-as-a-Service transition mechanisms (MAP-E, MAP-T, DS-Lite, Lightweight 4over6) that provide IPv4 connectivity over IPv6-only infrastructure. These mechanisms are deployed at scale in ISP and large enterprise environments where IPv4 address exhaustion drives migration to IPv6-only transport with IPv4 provided as a service. Translation/encapsulation failures directly impact IPv4 connectivity for potentially millions of subscribers.

## Value

IPv4-as-a-Service mechanisms are the lifeline for IPv4 connectivity in IPv6-primary networks. When MAP-E port-set allocation fails, subscribers lose the ability to reach IPv4-only services. When a DS-Lite AFTR's state table is exhausted, new IPv4 connections are rejected. These failures are invisible at the IPv6 layer — IPv6 works perfectly while IPv4 breaks. Monitoring these transition mechanisms is essential for maintaining IPv4 service quality during the transition period.

## Implementation

Collect MAP-E/MAP-T rule events, DS-Lite AFTR session logs, and port/address pool utilization metrics. Track session creation/deletion rates, failure rates, and resource utilization. Alert on port exhaustion, high failure rates, and AFTR health issues.

## Detailed Implementation

### Prerequisites
- MAP-E, MAP-T, DS-Lite, or Lw4o6 deployed in the network.
- Translation/encapsulation logging enabled on border relays and AFTRs.
- Port pool and session table utilization metrics available via SNMP or CLI.

### Step 1 — Configure data collection

**Cisco IOS-XE — DS-Lite AFTR logging:**
```
interface Tunnel0
 tunnel mode ipv6ip ds-lite
 tunnel source 2001:db8::1

ip nat log translations flow-create
ip nat log translations flow-delete
ip nat pool DS-LITE-POOL 198.51.100.0 198.51.100.255 prefix-length 24
```

**MAP-E border relay logging:**
```
map-e domain ENTERPRISE
 role border-relay
 default-mapping-rule 2001:db8::/32
 logging enable
```

**SNMP polling for AFTR session table:**
Poll `natAddrMapCurrentSessionCount`, `natAddrMapGlobalTotalSessions`, and `natAddrMapCurrentPortAlloc` from the NAT-MIB.

**Verification:**
```spl
index=network ("MAP-E" OR "MAP-T" OR "DS-Lite" OR "AFTR" OR "softwire") earliest=-24h
| stats count by sourcetype, host
```

### Step 2 — Create the search and alert

**AFTR/relay session table utilization:**
```spl
index=network sourcetype="sc4snmp:metric" (metric_name="nat.active_sessions" OR metric_name="nat.session_table_utilization") earliest=-24h
| stats latest(metric_value) as utilization by host
| lookup aftr_capacity.csv host OUTPUT max_sessions
| eval pct=round(utilization / max_sessions * 100, 1)
| where pct > 80
| eval severity=case(
    pct > 95, "CRITICAL — AFTR session table nearly full",
    pct > 90, "HIGH — approaching capacity",
    1=1, "WARNING")
```

**Port exhaustion detection:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos")
  ("port" AND ("exhaust" OR "allocat" AND "fail"))
  earliest=-1h
| stats count as port_failures by host
| where port_failures > 10
| eval alert="Port exhaustion: " . port_failures . " port allocation failures on " . host
```

**Translation failure rate:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos")
  ("MAP-E" OR "DS-Lite" OR "AFTR" OR "nat")
  ("create" OR "fail" OR "drop")
  earliest=-1h
| eval outcome=if(match(_raw, "(?i)fail|drop|denied"), "fail", "success")
| stats count(eval(outcome="success")) as ok count(eval(outcome="fail")) as fail
| eval failure_pct=round(fail / (ok + fail) * 100, 2)
| where failure_pct > 1
```

### Step 3 — Validate
(a) **Session table metrics.** Compare Splunk values with `show nat statistics` on the AFTR/relay.

(b) **Port exhaustion simulation.** Exhaust a port pool in a lab environment. Verify the port exhaustion alert fires.

(c) **Translation success rate.** During normal operation, verify the failure rate is below 0.1%.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — IPv4-as-a-Service Health"):
- Row 1 — Single-value: active translations, session table utilization, failure rate.
- Row 2 — Gauge: per-AFTR/relay session table capacity.
- Row 3 — Timechart: session creation/deletion rates over 24 hours.
- Row 4 — Alerts: port exhaustion and high failure rates.

**Scheduling:** Session table utilization every 5 minutes. Port exhaustion continuous. Failure rate every 15 minutes.

**Runbook:**
1. Session table >90%: add capacity (additional AFTR, larger session table, or migrate to stateless MAP-E/MAP-T).
2. Port exhaustion: increase IPv4 address pool, reduce port-set size per subscriber, or implement port range reassignment.
3. High failure rate: check AFTR/relay health (CPU, memory, interface errors). Check underlying IPv6 transport to the AFTR.

### Step 5 — Troubleshooting

- **MAP-E vs DS-Lite scaling** — MAP-E is stateless at the border relay (port-sets are algorithmically determined), so it scales much better than DS-Lite (which maintains per-flow state at the AFTR). If scaling is an issue, consider migrating from DS-Lite to MAP-E.

- **Port range fragmentation** — In MAP-E, each CPE gets a fixed port range (e.g., 1024-2047). If the range is too small for the subscriber's needs, connections fail. Monitor per-subscriber port utilization.

- **Hairpin traffic** — Subscriber-to-subscriber traffic within the same MAP-E/DS-Lite domain may need to traverse the border relay/AFTR twice (hairpin). This doubles the load. Implement hairpin optimization where possible.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos")
  ("MAP-E" OR "MAP-T" OR "DS-Lite" OR "AFTR" OR "softwire" OR "lw4o6" OR "map-rule")
  earliest=-24h
| eval mechanism=case(
    match(_raw, "(?i)MAP-E|map.?encap"), "MAP-E",
    match(_raw, "(?i)MAP-T|map.?trans"), "MAP-T",
    match(_raw, "(?i)DS-Lite|AFTR|softwire"), "DS-Lite",
    match(_raw, "(?i)lw4o6|lightweight"), "Lw4o6",
    1=1, "unknown")
| eval event_type=case(
    match(_raw, "(?i)fail|error|drop|denied"), "failure",
    match(_raw, "(?i)create|start|session"), "session_create",
    match(_raw, "(?i)delete|expire|timeout"), "session_delete",
    match(_raw, "(?i)port.?exhaust|pool.?exhaust"), "port_exhaustion",
    1=1, "other")
| stats count as events count(eval(event_type="failure")) as failures count(eval(event_type="port_exhaustion")) as port_exhaustions by mechanism, host
| eval health=case(
    port_exhaustions > 0, "CRITICAL — port exhaustion",
    failures > events * 0.05, "WARNING — failure rate above 5%",
    1=1, "OK")
```

## Visualization

(1) Single-value: active translations, failure rate, port pool utilization. (2) Timechart: session creation/deletion rates by mechanism. (3) Gauge: port pool utilization per AFTR or MAP-E border relay. (4) Table: per-subscriber issues (port exhaustion, failures).

## Known False Positives

**CGN port churn.** High-use applications (gaming, streaming, peer-to-peer) consume many ports. Rapid port allocation and release is normal for these workloads and not an indication of port exhaustion.

**Session timeout cleanup.** DS-Lite AFTR and MAP-E border relays periodically clean up expired sessions. Bulk session deletion events during cleanup cycles are normal.

**Subscriber CPE reboots.** When a CPE reboots, its existing sessions may be cleaned up at the AFTR/relay, producing a spike in session deletion events.

## References

- [RFC 7597 — Mapping of Address and Port with Encapsulation (MAP-E)](https://www.rfc-editor.org/rfc/rfc7597)
- [RFC 7599 — Mapping of Address and Port using Translation (MAP-T)](https://www.rfc-editor.org/rfc/rfc7599)
- [RFC 6333 — Dual-Stack Lite Broadband Deployments Following IPv4 Exhaustion](https://www.rfc-editor.org/rfc/rfc6333)
- [RFC 7596 — Lightweight 4over6: An Extension to the Dual-Stack Lite Architecture](https://www.rfc-editor.org/rfc/rfc7596)
