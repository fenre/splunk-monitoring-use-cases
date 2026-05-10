<!-- AUTO-GENERATED from UC-5.20.18.json — DO NOT EDIT -->

---
id: "5.20.18"
title: "/64 per Host Prefix Assignment Tracking"
status: "verified"
criticality: "low"
splunkPillar: "IT Operations"
---

# UC-5.20.18 · /64 per Host Prefix Assignment Tracking

> **Criticality:** Low &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*Instead of giving each device one address on a shared street, we give each device its own private driveway — a whole block of addresses just for them. We keep track of who received which block, so we always know which driveway belongs to whom.*

---

## Description

Tracks DHCPv6 Prefix Delegation assignments where each host receives a /64 prefix instead of a single address, as described in RFC 8273. This model is increasingly common in shared infrastructure environments (co-working spaces, campus Wi-Fi, cloud hosting) where each device needs its own subnet for running containers, VMs, or for privacy isolation. The use case monitors prefix assignments, renewal health, and alerts on non-standard prefix lengths or excessive prefix consumption by a single client.

## Value

RFC 8273 prefix-per-host deployment changes the operational model fundamentally: instead of tracking individual addresses, you are now tracking prefix assignments. Each host becomes a mini-router with its own /64, which means traditional NDP-based device inventory (UC-5.20.4) may not capture the host's actual operational addresses within its delegated prefix. Monitoring PD assignments ensures your IPAM remains accurate, detects clients consuming more prefixes than expected (potential abuse or misconfiguration), and maintains the forensic chain from prefix to DUID to physical device.

## Implementation

Configure DHCPv6 servers to log IA_PD events. Parse delegated prefix and client DUID from DHCPv6-PD log entries. Track active delegations, renewal rates, and alert on anomalies: non-/64 prefix lengths, excessive prefix count per client, or failed renewals indicating prefix exhaustion.

## Detailed Implementation

### Prerequisites
- A DHCPv6 server configured for Prefix Delegation (IA_PD): Cisco IOS DHCPv6 server, ISC Kea, Infoblox NIOS, or similar.
- Router interfaces configured with `ipv6 dhcp server <pool>` and `ipv6 nd prefix <prefix> <valid> <preferred> no-autoconfig` (disabling SLAAC so hosts rely on PD).
- DHCPv6 pool configured with PD prefix: `prefix-delegation pool <name> lifetime <valid> <preferred>`.
- Understanding of your PD architecture: what prefix length is delegated (/64 per RFC 8273, or /48-/56 for CPE in SP environments).

### Step 1 — Configure data collection

**Cisco IOS/IOS-XE DHCPv6 server:**

DHCPv6-PD assignments are logged to syslog when configured:
```
ipv6 dhcp pool HOST_PD_POOL
 prefix-delegation pool PD_PREFIXES lifetime 86400 3600
 dns-server 2001:db8::53
 domain-name example.com
!
ipv6 local pool PD_PREFIXES 2001:db8:100::/48 64
```
The pool definition `2001:db8:100::/48 64` means: allocate /64 prefixes from the 2001:db8:100::/48 aggregate. Each client gets a unique /64.

Enable DHCPv6 event logging:
```
logging buffered 32768 informational
```
DHCPv6-PD events appear as `%DHCPv6-PD-6-PREFIX_ASSIGN` in syslog, forwarded to Splunk via the Cisco IOS TA.

Verify active delegations on the router:
```
show ipv6 dhcp binding
  Client: FE80::1 
  DUID: 000100011A2B3C4D00E0B0C0D0E0
  IA PD: IA ID 0x00030001, T1 1800, T2 2880
    Prefix: 2001:db8:100:1::/64
            preferred lifetime 3600, valid lifetime 86400
```

**ISC Kea DHCPv6 server:**

Kea logs PD events to the lease file and syslog. Configure in `kea-dhcp6.conf`:
```json
{
  "Dhcp6": {
    "subnet6": [{
      "subnet": "2001:db8:100::/48",
      "pd-pools": [{
        "prefix": "2001:db8:100::",
        "prefix-len": 48,
        "delegated-len": 64
      }]
    }]
  }
}
```
Kea lease entries include `ia-pd` in the log. Forward to Splunk with `sourcetype=isc:dhcpd`.

**Infoblox NIOS:**

Configure DHCPv6-PD in the Infoblox Grid Manager:
Data Management → DHCP → IPv6 → Network → Add → Enable Prefix Delegation.
Syslog events contain `ia-pd` assignments. Forward to Splunk via the Infoblox TA with `sourcetype=infoblox:dhcp`.

**Verification:**
```spl
index=network ("IA_PD" OR "PREFIX_ASSIGN" OR "ia-pd" OR "prefix-delegation") earliest=-24h
| stats count by sourcetype, host
```
Expected: events from each DHCPv6-PD server.

### Step 2 — Create the search and alert

**Primary search — active prefix delegations:**
```spl
index=network (sourcetype="infoblox:dhcp" OR sourcetype="cisco:ios" OR sourcetype="isc:dhcpd")
  ("IA_PD" OR "PREFIX_ASSIGN" OR "ia-pd" OR "prefix-delegation")
  earliest=-24h
| rex field=_raw "prefix[= ]+(?<delegated_prefix>[0-9a-fA-F:]+/\d+)"
| rex field=_raw "(DUID|duid|client-id)[= ]+(?<client_duid>[0-9a-fA-F:]+)"
| eval prefix_length=tonumber(replace(delegated_prefix, ".*/(\d+)", "\1"))
| stats min(_time) as first_delegated max(_time) as last_renewed count as event_count latest(host) as dhcp_server by delegated_prefix, client_duid
| eval active=if(last_renewed > relative_time(now(), "-2h"), "ACTIVE", "EXPIRED")
| eval non_standard=if(prefix_length!=64, "YES — expected /64 per RFC 8273", "NO")
| eval first_delegated=strftime(first_delegated, "%Y-%m-%d %H:%M:%S")
| eval last_renewed=strftime(last_renewed, "%Y-%m-%d %H:%M:%S")
| sort active, client_duid
```

**Alert — excessive prefix delegation per client:**
```spl
index=network ("IA_PD" OR "PREFIX_ASSIGN" OR "ia-pd" OR "prefix-delegation")
  earliest=-24h
| rex field=_raw "prefix[= ]+(?<delegated_prefix>[0-9a-fA-F:]+/\d+)"
| rex field=_raw "(DUID|duid|client-id)[= ]+(?<client_duid>[0-9a-fA-F:]+)"
| stats dc(delegated_prefix) as prefix_count by client_duid
| where prefix_count > 3
```
Trigger: any client with > 3 active /64 delegations. This may indicate a misconfigured client requesting multiple prefixes.

**Alert — prefix pool exhaustion:**
```spl
index=network ("IA_PD" OR "PREFIX_ASSIGN" OR "ia-pd") earliest=-1h
| rex field=_raw "prefix[= ]+(?<delegated_prefix>[0-9a-fA-F:]+/\d+)"
| stats dc(delegated_prefix) as assigned_prefixes
| eval pool_total=65536
| eval utilization_pct=round(assigned_prefixes / pool_total * 100, 1)
| where utilization_pct > 80
```
Adjust `pool_total` to match your actual PD pool size (/48 containing /64s = 65536 prefixes).

### Step 3 — Validate
(a) **Trigger a PD request.** From a test client, request a prefix delegation: configure a DHCPv6-PD client (e.g., `ipv6 dhcp client pd PREFIX_FROM_ISP` on a Cisco router, or `dhclient -6 -P eth0` on Linux). Verify the delegation appears in Splunk within 2 minutes.

(b) **Cross-reference with DHCP server.** Run `show ipv6 dhcp binding` on the server and compare with Splunk results. Counts should match.

(c) **Non-standard prefix test.** If your SP environment delegates /56 prefixes, verify the `non_standard` flag fires correctly (since we expect /64 per RFC 8273 in enterprise).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Prefix Delegation Tracking"):
- Row 1 — Single-value: active delegations, pool utilization %, non-standard prefix count.
- Row 2 — Table: active prefix delegations with client DUID, prefix, server, first seen, last renewed, standard compliance.
- Row 3 — Timechart: new delegations over time — should correlate with user onboarding patterns.
- Row 4 — Alert summary: clients with excessive delegations, pool exhaustion warnings.

**Scheduling:** Primary delegation tracking every 15 minutes. Pool exhaustion check every hour. Excessive-per-client alert every 6 hours.

**Runbook:**
1. Pool exhaustion warning: increase the PD pool (delegate from a larger aggregate) or reduce delegation lifetime to reclaim unused prefixes.
2. Excessive delegations per client: investigate the client DUID — is it a router requesting multiple prefixes for downstream subnets (legitimate) or a single host misbehaving?
3. Non-standard prefix length: if intentional (SP CPE), document and suppress. If in enterprise, investigate why the DHCPv6 server is delegating non-/64 prefixes.

### Step 5 — Troubleshooting

- **No IA_PD events in logs** — DHCPv6-PD requires both server-side configuration (prefix-delegation pool) and client-side configuration (dhcp client pd). Without a PD-capable client requesting IA_PD, no delegations occur. Verify: `show ipv6 dhcp pool` should show PD prefixes available.

- **Prefix not routable** — After a prefix is delegated, the server must inject a route toward the client. On Cisco: verify `show ipv6 route` contains a route to the delegated /64 via the client's link-local address. Missing route = delegated prefix is black-holed.

- **DUID format varies by vendor** — Cisco uses DUID-LL (link-layer based), Linux dhclient uses DUID-LLT (link-layer + time), Windows uses DUID-LL. The regex must accommodate all three formats. If DUID parsing fails, widen the regex or use `rex mode=sed`.

## SPL

```spl
index=network (sourcetype="infoblox:dhcp" OR sourcetype="cisco:ios" OR sourcetype="isc:dhcpd")
  ("IA_PD" OR "PREFIX_ASSIGN" OR "ia-pd" OR "prefix-delegation")
| rex field=_raw "prefix[= ]+(?<delegated_prefix>[0-9a-fA-F:]+/\d+)"
| rex field=_raw "(DUID|duid|client-id)[= ]+(?<client_duid>[0-9a-fA-F:]+)"
| eval prefix_length=tonumber(replace(delegated_prefix, ".*/(\d+)", "\1"))
| stats min(_time) as first_delegated max(_time) as last_renewed count as renewal_count latest(host) as dhcp_server by delegated_prefix, client_duid
| eval first_delegated=strftime(first_delegated, "%Y-%m-%d %H:%M:%S")
| eval last_renewed=strftime(last_renewed, "%Y-%m-%d %H:%M:%S")
| eval non_standard=if(prefix_length!=64, "YES — expected /64 per RFC 8273", "NO")
| sort client_duid, delegated_prefix
```

## Visualization

(1) Table: active prefix delegations with client DUID, prefix, delegation time, renewal count. (2) Single-value: total active /64 delegations, prefix pool utilization %. (3) Timechart: new delegations per hour — spikes indicate onboarding events or misbehaving clients. (4) Alert panel: non-standard prefix lengths and clients with more than expected delegations.

## Known False Positives

**Residential CPE prefix delegation.** In service-provider networks, each residential CPE (home router) receives a /48 or /56 via IA_PD, not a /64. The non-standard prefix length alert (expecting /64 per RFC 8273) will fire for these legitimate delegations. Filter by client type or create separate monitoring for SP vs enterprise PD.

**Lab/test environments.** Developers running multiple VMs or containers on a single host may trigger the 'excessive prefix count per client' alert if they legitimately need multiple /64 prefixes. Whitelist known development DUIDs.

**Prefix renewals during server failover.** When a DHCPv6 server cluster fails over, the backup server may re-delegate prefixes to all clients, causing a spike in delegation events. This is normal failover behaviour, not a real anomaly.

## References

- [RFC 8273 — Unique IPv6 Prefix per Host (prefix-per-host model for shared networks)](https://www.rfc-editor.org/rfc/rfc8273)
- [RFC 8415 — Dynamic Host Configuration Protocol for IPv6 (DHCPv6) — IA_PD Identity Association for Prefix Delegation](https://www.rfc-editor.org/rfc/rfc8415)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.1.3 — prefix delegation security implications)](https://www.rfc-editor.org/rfc/rfc9099)
