<!-- AUTO-GENERATED from UC-5.20.114.json — DO NOT EDIT -->

---
id: "5.20.114"
title: "DHCPv6 Prefix Delegation (PD) Security and Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.114 · DHCPv6 Prefix Delegation (PD) Security and Tracking

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Security, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*When a branch office needs its own block of new addresses (IPv6), it asks the headquarters router to assign it a block, like getting a range of house numbers for a new neighbourhood. We monitor this process to make sure only authorised branches get address blocks, that we don't run out of blocks to give, and that nobody is pretending to be headquarters and handing out fake address blocks.*

---

## Description

Monitors DHCPv6 Prefix Delegation (PD) for security and operational issues: tracks prefix delegations to CPE routers, detects pool exhaustion, identifies unauthorized prefix requests, and alerts on rogue delegating routers. DHCPv6-PD is the primary mechanism for distributing IPv6 prefixes to branch routers, home gateways, and Thread Border Routers.

## Value

DHCPv6 Prefix Delegation is the mechanism that gives downstream routers their IPv6 addresses. If an attacker can request a prefix, they get a routable IPv6 block to use for attacks. If the pool is exhausted, no new branches can come online. If a rogue DHCPv6 server delegates spoofed prefixes, downstream devices use incorrect routing. Monitoring PD operations ensures the IPv6 address distribution system maintains integrity.

## Implementation

Monitor DHCPv6 PD events from delegating routers and DHCP servers. Track prefix-to-client mappings. Alert on pool exhaustion and unauthorized clients.

## Detailed Implementation

### Prerequisites
- DHCPv6 delegating router or Infoblox DHCP server configured for PD.
- DHCPv6 event logging enabled.

### Step 1 — Configure DHCPv6-PD logging

**Cisco IOS-XE delegating router:**
```
ipv6 dhcp pool BRANCH-PD-POOL
 prefix-delegation pool PD-POOL
!
ipv6 local pool PD-POOL 2001:db8::/32 48
!
interface GigabitEthernet0/0/0
 ipv6 dhcp server BRANCH-PD-POOL
```

Enable detailed DHCPv6 logging:
```
service dhcpv6
logging buffered 8192 informational
```

**Infoblox DHCP logging:**
Enable DHCPv6 lease logging via Grid → DHCP → IPv6 → Logging.

### Step 2 — Create monitoring searches

**Current prefix delegation inventory:**
```spl
index=network ("DHCPv6" OR "prefix-delegation") earliest=-7d
| where match(_raw, "(?i)PD.*allocat|prefix.*delegat")
| rex field=_raw "prefix\s*=?\s*(?<prefix>[0-9a-fA-F:/]+)"
| rex field=_raw "(?:client|DUID)\s*=?\s*(?<duid>[0-9a-fA-F:]+)"
| rex field=_raw "(?:interface|link)\s*(?<interface>\S+)"
| stats latest(_time) as last_seen latest(prefix) as current_prefix by duid, host
| eval age_hours=round((now() - last_seen) / 3600, 1)
| table duid, current_prefix, host, last_seen, age_hours
```

**PD pool utilization:**
```spl
index=network ("DHCPv6" OR "prefix-delegation") earliest=-24h
| stats dc(eval(if(match(_raw, "(?i)allocat|delegat"), delegated_prefix, null()))) as active_delegations by host
| eval pool_size=256
| eval utilization_pct=round(active_delegations / pool_size * 100, 1)
| eval status=case(
    utilization_pct > 90, "CRITICAL — PD pool near exhaustion",
    utilization_pct > 75, "WARNING — PD pool utilization high",
    1=1, "OK")
```

### Step 3 — Validate
(a) **Delegation test.** From a test CPE, request a prefix via DHCPv6-PD. Verify the delegation appears in Splunk within 60 seconds.

(b) **Unauthorized client test.** From an unauthorized device, send a DHCPv6 Solicit with IA_PD. Verify the delegating router either rejects it or logs it as an unknown client.

(c) **Pool exhaustion test.** In a lab with a small PD pool (e.g., 4 prefixes), request 5 prefixes. Verify the exhaustion event is logged and alerted.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DHCPv6 Prefix Delegation"):
- Row 1 — Gauge: PD pool utilization.
- Row 2 — Table: current prefix delegations.
- Row 3 — Timeline: delegation events.
- Row 4 — Alerts: pool exhaustion, unauthorized clients.

**Alert 1:** PD pool utilization >90% — high.
**Alert 2:** Pool exhaustion — critical.
**Alert 3:** Prefix delegated to unknown client — medium.

### Step 5 — Troubleshooting

- **CPE not receiving prefix.** Check that the delegating router has available prefixes in the pool. Verify the CPE is sending DHCPv6 Solicit with IA_PD option (not just IA_NA). On Cisco CPE: `ipv6 dhcp client pd <name>`.

- **Prefix not being used downstream.** The CPE must be configured to use the delegated prefix on its LAN interfaces: `ipv6 address <pd-name> ::1/64`. Without this, the delegated prefix is wasted.

- **Frequent renumbering.** If prefixes change every time the CPE reboots, configure longer lease times or enable prefix stability features. Frequent renumbering breaks connections and complicates forensics.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe" OR sourcetype="infoblox:dhcp") earliest=-24h
  ("DHCPv6" OR "prefix-delegation" OR "IA_PD" OR "%DHCPV6")
| eval pd_event=case(
    match(_raw, "(?i)PD.*allocat|prefix.*delegat|IA_PD.*assigned"), "PREFIX_DELEGATED",
    match(_raw, "(?i)PD.*release|prefix.*release|IA_PD.*release"), "PREFIX_RELEASED",
    match(_raw, "(?i)PD.*renew|prefix.*renew|IA_PD.*renew"), "PREFIX_RENEWED",
    match(_raw, "(?i)pool.*exhaust|no.*prefix.*available|PD.*fail"), "POOL_EXHAUSTED",
    match(_raw, "(?i)PD.*decline|prefix.*decline"), "PREFIX_DECLINED",
    1=1, "OTHER")
| rex field=_raw "prefix\s*=?\s*(?<delegated_prefix>[0-9a-fA-F:/]+)"
| rex field=_raw "(?:client|DUID)\s*=?\s*(?<client_duid>[0-9a-fA-F:]+)"
| eval severity=case(
    pd_event="POOL_EXHAUSTED", "CRITICAL — DHCPv6-PD pool exhausted — new CPEs cannot get prefixes",
    pd_event="PREFIX_DECLINED", "HIGH — prefix declined — address conflict or configuration error",
    pd_event="PREFIX_DELEGATED" AND NOT match(client_duid, "^(known_duids_pattern)"), "MEDIUM — prefix delegated to unknown client",
    1=1, null())
| stats count as events latest(delegated_prefix) as current_prefix by host, pd_event, client_duid
| sort -events
```

## Visualization

(1) Table: current prefix delegations (prefix, client, router). (2) Gauge: PD pool utilization. (3) Timeline: delegation events. (4) Single-value: pool exhaustion events (should be zero).

## Known False Positives

**CPE reboots.** When a CPE router reboots, it re-requests its prefix. This appears as a release followed by a delegation. Brief re-delegation events during maintenance are normal.

**Prefix renumbering.** If the delegating pool is reconfigured, all CPEs receive new prefixes. This is a planned operation, not a security event.

**High delegation volume at ISP scale.** Service providers may see thousands of PD events per hour as customer CPEs come online. Tune thresholds to ISP scale.

## References

- [RFC 3633 — IPv6 Prefix Options for Dynamic Host Configuration Protocol (DHCP) version 6](https://www.rfc-editor.org/rfc/rfc3633)
- [RFC 8415 — Dynamic Host Configuration Protocol for IPv6 (DHCPv6)](https://www.rfc-editor.org/rfc/rfc8415)
