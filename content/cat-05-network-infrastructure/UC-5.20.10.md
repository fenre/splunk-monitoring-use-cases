<!-- AUTO-GENERATED from UC-5.20.10.json — DO NOT EDIT -->

---
id: "5.20.10"
title: "DHCPv6 Lease and Prefix Delegation Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.20.10 · DHCPv6 Lease and Prefix Delegation Tracking

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the system that hands out internet addresses to devices — some devices get one address each, while routers get a whole block of addresses to share with the devices connected to them. We make sure nobody runs out of addresses, and if a device reports that its assigned address is already taken by someone else, we flag it immediately.*

---

## Description

Tracks DHCPv6 lease activity across two fundamentally different assignment types that have no DHCPv4 equivalent: IA_NA (Identity Association for Non-temporary Addresses — assigning individual /128 addresses to clients, analogous to DHCPv4 leases) and IA_PD (Identity Association for Prefix Delegation — delegating /48 to /64 prefixes to downstream routers or CPE devices, which then advertise those prefixes via SLAAC to their local clients). IA_PD is unique to IPv6 and critical in ISP, large enterprise, and campus deployments where distribution-layer devices request prefixes from a central DHCPv6 server to create hierarchical addressing without manual configuration.

## Value

DHCPv6 is architecturally different from DHCPv4 in ways that catch operators by surprise. First, the DUID (DHCP Unique Identifier) is NOT a MAC address — it can be DUID-LLT (link-layer + time), DUID-EN (enterprise number), or DUID-LL (link-layer), and it persists across reboots, making it harder to correlate to physical devices (see UC-5.20.14). Second, IA_PD failure doesn't just affect one client — it affects every device downstream of the requesting router, potentially an entire building or floor. Third, DHCPv6 DECLINE messages indicate DAD (Duplicate Address Detection) failures, which are a symptom of address conflicts or active attacks (UC-5.20.11). Monitoring DHCPv6 lease activity provides early warning for all three failure modes.

## Implementation

Enable DHCPv6 lease logging on your DHCPv6 server (Infoblox, ISC DHCP, Windows Server). Forward logs to Splunk. The search classifies lease events by message type and assignment type (IA_NA vs IA_PD), providing a complete picture of DHCPv6 activity. Track IA_PD prefix delegation separately from IA_NA address assignment because they have different operational implications. Alert on: DECLINE messages (DAD failures), REBIND spikes (server reachability issues), and IA_PD prefix exhaustion.

## Detailed Implementation

### Prerequisites
- A DHCPv6 server must be deployed and logging to Splunk. Common platforms:
  - **Infoblox NIOS:** Grid Manager → DHCP → IPv6 → enable DHCP logging → syslog forward to Splunk. Infoblox logs DHCPv6 messages with detailed DUID, IA_NA/IA_PD, and lease information.
  - **ISC DHCP (dhcpd):** In dhcpd6.conf: `log-facility local7;`. Forward local7 via syslog to Splunk. ISC DHCPv6 logging is verbose and includes all message types.
  - **Windows Server DHCPv6:** Enable DHCPv6 audit logging in Server Manager → DHCP → IPv6 → Properties → Advanced → Enable DHCP audit logging. Forward with Splunk UF.
- Understanding of your DHCPv6 deployment model:
  - **IA_NA only:** DHCPv6 assigns individual addresses to clients (similar to DHCPv4). Common in enterprise networks where SLAAC is used for addresses and DHCPv6 only for DNS/NTP options (M=0, O=1 in RA).
  - **IA_PD:** DHCPv6 delegates prefixes to downstream routers. Common in ISP (CPE gets a /56 or /48), large campus (distribution switch gets a /48 for its access VLANs), and residential broadband.
  - **Stateless DHCPv6 (information-request only):** No address assignment — clients get DNS/NTP from DHCPv6 but addresses from SLAAC. This mode generates INFORMATION-REQUEST/REPLY messages only, not SOLICIT/ADVERTISE/REQUEST/REPLY.

### Step 1 — Configure data collection

For **Infoblox** (most common enterprise DHCPv6):
1. Grid Manager → Grid → Grid Properties → Monitoring → enable syslog forwarding to Splunk HF.
2. Per DHCP member: Member → DHCP → Logging → enable DHCP logging.
3. Install `Splunk_TA_infoblox` on the HF and Search Heads.
4. inputs.conf on HF:
```
[udp://1514]
sourcetype = infoblox:dhcp
index = dhcp
```

For **ISC DHCP:**
1. Ensure dhcpd6.conf has `log-facility local7;` (or your chosen facility).
2. Configure rsyslog/syslog-ng to forward that facility to Splunk HF.
3. Create custom sourcetype `isc:dhcpd` with appropriate TIME_FORMAT.

Verification:
```spl
index=dhcp sourcetype=infoblox:dhcp DHCPv6 earliest=-4h
| rex "(?<dhcpv6_msg>SOLICIT|ADVERTISE|REQUEST|REPLY|RENEW|REBIND|RELEASE|DECLINE|INFORMATION-REQUEST)"
| stats count by dhcpv6_msg
```
Expected: SOLICIT and REPLY counts should be approximately equal (each SOLICIT eventually gets a REPLY). RENEW should be higher than SOLICIT (renewals happen more frequently than initial requests). DECLINE should be zero or very low.

### Step 2 — Create the search and alert

**Primary search — DHCPv6 activity overview:**
```spl
index=dhcp sourcetype="infoblox:dhcp" DHCPv6 earliest=-24h
| rex "(?<dhcpv6_msg>SOLICIT|ADVERTISE|REQUEST|REPLY|RENEW|REBIND|RELEASE|DECLINE|INFORMATION-REQUEST)"
| rex "IA_NA\s+(?<ia_na_addr>[0-9a-fA-F:]+)"
| rex "IA_PD\s+(?<ia_pd_prefix>[0-9a-fA-F:]+/\d+)"
| rex "DUID\s+(?<client_duid>[0-9a-fA-F:]+)"
| eval assignment_type=case(
    isnotnull(ia_pd_prefix), "Prefix Delegation (IA_PD)",
    isnotnull(ia_na_addr), "Address Assignment (IA_NA)",
    dhcpv6_msg="INFORMATION-REQUEST", "Stateless (info only)",
    1==1, "Other")
| stats count as events dc(client_duid) as unique_clients by dhcpv6_msg, assignment_type
| sort dhcpv6_msg
```

**Understanding this SPL:**
- DHCPv6 uses a different message flow than DHCPv4: SOLICIT → ADVERTISE → REQUEST → REPLY (4-message exchange) or SOLICIT → REPLY (2-message rapid commit). RENEW extends an existing lease. REBIND is a client seeking ANY server (its preferred server is unreachable). DECLINE means the client detected an address conflict via DAD.
- IA_NA and IA_PD are extracted separately because they represent fundamentally different operations. A single DHCPv6 transaction can contain both (a router requesting an address for its own interface AND a prefix for its downstream clients).
- DUID (DHCP Unique Identifier) replaces the DHCPv4 concept of `client-id = MAC`. DUIDs are more complex and may not contain the MAC address at all (DUID-EN type uses enterprise number + device serial).

**IA_PD prefix delegation tracking:**
```spl
index=dhcp sourcetype="infoblox:dhcp" DHCPv6 IA_PD earliest=-7d
| rex "IA_PD\s+(?<ia_pd_prefix>[0-9a-fA-F:]+/\d+)"
| rex "DUID\s+(?<client_duid>[0-9a-fA-F:]+)"
| rex "(?<dhcpv6_msg>REQUEST|REPLY|RENEW|RELEASE)"
| where isnotnull(ia_pd_prefix)
| stats count as events latest(dhcpv6_msg) as last_msg latest(_time) as last_seen values(client_duid) as requesting_device by ia_pd_prefix
| eval last_seen_time=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| eval pd_status=if(last_msg="RELEASE", "Released", "Active")
| sort -last_seen
```

**Alert — DHCPv6 DECLINE spike (DAD failures):**
```spl
index=dhcp sourcetype="infoblox:dhcp" DHCPv6 DECLINE earliest=-1h
| stats count as decline_count by host
| where decline_count > 5
```
Trigger: > 5 DECLINE messages in 1 hour. Each DECLINE means a DHCPv6-assigned address failed DAD (another device on the network already has that address). This indicates: (a) address pool overlap with SLAAC range, (b) stale leases from a previous server, or (c) an active DAD denial-of-service attack (UC-5.20.87).

**Alert — IA_PD prefix pool exhaustion:**
```spl
index=dhcp sourcetype="infoblox:dhcp" DHCPv6 IA_PD REPLY earliest=-24h
| rex "IA_PD\s+(?<ia_pd_prefix>[0-9a-fA-F:]+/\d+)"
| stats dc(ia_pd_prefix) as delegated_prefixes
| eval max_prefixes=256
| eval utilisation_pct=round(delegated_prefixes/max_prefixes*100, 1)
| where utilisation_pct > 80
```
Adjust `max_prefixes` to your pool size. IA_PD exhaustion means no more downstream routers can be provisioned.

### Step 3 — Validate
(a) **Compare to DHCP server UI:** In Infoblox Grid Manager → DHCP → IPv6 → Leases, count active IA_NA leases. Compare to `index=dhcp ... | stats dc(ia_na_addr)`.

(b) **Spot-check a specific client:** On a known DHCPv6 client: `ip -6 addr show` (Linux) or `ipconfig /all` (Windows — look for "DHCPv6 Client DUID"). Search Splunk for that DUID: `index=dhcp DUID="<duid>"`. The lease history should match.

(c) **Verify IA_PD on a requesting router:** On a distribution switch configured with `ipv6 dhcp client pd <prefix-name>`: `show ipv6 dhcp interface`. The delegated prefix should appear in the Splunk IA_PD tracking results.

(d) **Check for missing message types:** If only REPLY appears but no SOLICIT/REQUEST, the DHCPv6 server may be logging responses but not requests. Adjust logging level on the server.

### Step 4 — Operationalize

**Dashboard** ("DHCPv6 Health"):
- Row 1 — Single-value tiles: active IA_NA leases, active IA_PD delegations, DECLINE count (24h), pool utilisation %.
- Row 2 — Stacked bar: message types over 24h (SOLICIT, REQUEST, RENEW, RELEASE, DECLINE).
- Row 3 — IA_PD table: delegated prefixes, requesting DUID, status, last seen.
- Row 4 — Timechart: lease activity over 7 days — flat-line drops indicate server outage.

**Scheduling:** Hourly for pool utilisation. Real-time for DECLINE alerts.

**Runbook** (owner: Network Operations / IPAM Team):
1. DECLINE spike: check for SLAAC/DHCPv6 address range overlap on affected subnet. Ensure the DHCPv6 pool doesn't overlap with the /64 prefix advertised via SLAAC (where clients self-assign addresses in the same range).
2. Pool exhaustion (> 80%): expand the DHCPv6 address pool or investigate lease hoarding (clients with long leases that aren't releasing).
3. IA_PD failure: if a downstream router fails to get a prefix, ALL clients behind that router lose IPv6. Treat as high-severity and investigate the DHCPv6 server immediately.

### Step 5 — Troubleshooting

- **No DHCPv6 events at all** — (1) DHCPv6 may not be deployed. Check: are RAs configured with M=1 or O=1? If M=0 and O=0, clients use SLAAC only and don't contact DHCPv6. (2) DHCPv6 logging may not be enabled on the server — check server configuration.

- **SOLICIT events but no REPLY** — The DHCPv6 server is receiving requests but not responding. Causes: no available addresses in pool, server misconfiguration, relay agent not forwarding replies. Check the server's own logs for error messages.

- **DUID field is empty** — The Splunk TA field extraction may not cover the DUID format used by your server. DUIDs have variable length and format. Run `| rex field=_raw "DUID[=: ]+(?<duid>[0-9a-fA-F:]+)"` to test different patterns.

- **Very high RENEW rate** — Normal. DHCPv6 default T1 (renewal time) is 0.5 × preferred lifetime. With a 1-hour preferred lifetime, clients RENEW every 30 minutes. If the preferred lifetime is very short, RENEW traffic will be high. Lengthen preferred lifetime on the server if the rate is problematic.

- **IA_PD prefixes not appearing** — Prefix delegation requires specific server configuration (delegated prefix pool). On Infoblox: DHCP → IPv6 → create a Prefix Delegation network. On ISC DHCP: `prefix6 <start> <end> /<length>` in the subnet6 declaration.

## SPL

```spl
index=dhcp sourcetype="infoblox:dhcp" DHCPv6 earliest=-24h
| rex "(?<dhcpv6_msg>SOLICIT|ADVERTISE|REQUEST|REPLY|RENEW|REBIND|RELEASE|DECLINE)"
| rex "IA_NA\s+(?<ia_na_addr>[0-9a-fA-F:]+)"
| rex "IA_PD\s+(?<ia_pd_prefix>[0-9a-fA-F:]+/\d+)"
| rex "DUID\s+(?<client_duid>[0-9a-fA-F:]+)"
| eval assignment_type=case(
    isnotnull(ia_pd_prefix), "Prefix Delegation (IA_PD)",
    isnotnull(ia_na_addr), "Address Assignment (IA_NA)",
    1==1, "Other")
| stats count by dhcpv6_msg, assignment_type
| sort dhcpv6_msg
```

## Visualization

(1) Stacked bar chart: DHCPv6 message types over time (SOLICIT, REQUEST, RENEW, RELEASE, DECLINE — DECLINE in red). (2) Single-value tiles: active IA_NA leases, active IA_PD delegations, DECLINE count (last 24h, red if > 0). (3) Table: IA_PD delegations — prefix, requesting DUID, lease start/end, downstream scope — for prefix delegation management. (4) Timechart: lease pool utilisation (IA_NA addresses assigned / total pool size × 100%).

## Known False Positives

**RENEW storms after DHCPv6 server restart.** When a DHCPv6 server restarts, all clients whose leases are in T1 (renewal) or T2 (rebind) timers will immediately send RENEW or REBIND messages. This creates a transient spike that looks like a problem but is normal server recovery behaviour. The spike should resolve within minutes as clients receive valid replies.

**DUID changes after OS reinstall.** DUID-LLT includes a timestamp component. If a client is reimaged, its DUID changes, and it appears as a new client requesting a new lease while the old lease (under the old DUID) remains allocated until it expires. This is normal DHCPv6 behaviour — the old lease will be reclaimed automatically after expiry.

**IA_PD from virtualisation platforms.** Virtual switch platforms (vSphere, Hyper-V) that run their own DHCPv6 clients for prefix delegation on virtual network interfaces may generate IA_PD traffic that looks like a downstream router requesting prefixes. These are legitimate if the platform is designed to provide IPv6 connectivity to VMs, but unexpected if virtual networking is supposed to be IPv4-only.

## References

- [RFC 8415 — Dynamic Host Configuration Protocol for IPv6 (DHCPv6) — consolidated DHCPv6 specification](https://www.rfc-editor.org/rfc/rfc8415)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.1.3 — DHCPv6 security)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 3633 — IPv6 Prefix Options for DHCPv6 (IA_PD prefix delegation)](https://www.rfc-editor.org/rfc/rfc3633)
- [Splunk Add-on for Infoblox (Splunkbase 2934)](https://splunkbase.splunk.com/app/2934)
