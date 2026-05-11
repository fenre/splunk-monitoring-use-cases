<!-- AUTO-GENERATED from UC-5.20.34.json — DO NOT EDIT -->

---
id: "5.20.34"
title: "IPv6 Destination Guard Event Tracking"
status: "verified"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-5.20.34 · IPv6 Destination Guard Event Tracking

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Security, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*Instead of the router calling out 'Are you there?' to every address someone tries to reach — which can overwhelm it — we tell it to only call known residents. If someone tries to send a package to a non-existent address, the router simply discards it instead of wasting time looking for a resident who does not exist.*

---

## Description

Tracks IPv6 Destination Guard activity, which prevents packets destined to unknown IPv6 addresses from triggering NDP resolution. This is the primary defence against NDP exhaustion attacks (UC-5.20.23): instead of letting every unknown destination trigger a Neighbor Solicitation and create an INCOMPLETE NDP cache entry, Destination Guard silently drops packets to destinations not in the SISF binding table. Each blocked packet represents a potential NDP cache entry that was NOT created — protecting the router's NDP cache capacity.

## Value

Destination Guard is the most effective mitigation for NDP exhaustion attacks. By preventing NDP resolution for unknown destinations, it eliminates the attack surface entirely. Monitoring Destination Guard activity reveals: (1) how many NDP cache entries are being saved (capacity protection), (2) whether scanning activity is occurring (security signal), and (3) whether legitimate hosts are being blocked because their addresses are not in the binding table (operational issue).

## Implementation

Enable Destination Guard on all router SVIs. Monitor syslog events for blocked destinations. Distinguish scanning patterns (many unique destinations from single source) from binding gaps (recurring blocks for the same destination).

## Detailed Implementation

### Prerequisites
- SISF in `guard` mode on the access-layer switches (bindings must be available for Destination Guard to reference).
- Destination Guard configured on Layer 3 router SVIs.

### Step 1 — Configure data collection

**Cisco IOS-XE Destination Guard:**
```
ipv6 destination-guard policy DG_POLICY
 enforcement always
!
interface Vlan100
 ipv6 destination-guard attach-policy DG_POLICY
```

Verify:
```
show ipv6 destination-guard policy DG_POLICY
  Enforcement: always
  Target: Vlan100
```

Destination Guard blocks appear in syslog. Forward to Splunk with `sourcetype=cisco:ios`.

**Verification:**
```spl
index=network sourcetype="cisco:ios" ("DESTGUARD" OR "destination-guard") earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**Scanning detection — many unique blocked destinations:**
```spl
index=network sourcetype="cisco:ios" ("DESTGUARD" OR "destination-guard") earliest=-1h
| rex field=_raw "DST:\s*(?<dest_ipv6>[0-9a-fA-F:]+)"
| rex field=_raw "SRC:\s*(?<src_ipv6>[0-9a-fA-F:]+)"
| stats dc(dest_ipv6) as unique_dests count as total_blocks by src_ipv6, host
| where unique_dests > 50
| eval assessment="PROBABLE SCANNING: " . unique_dests . " unique destinations blocked"
```

**Binding gap detection — same destination repeatedly blocked:**
```spl
index=network sourcetype="cisco:ios" ("DESTGUARD" OR "destination-guard") earliest=-24h
| rex field=_raw "DST:\s*(?<dest_ipv6>[0-9a-fA-F:]+)"
| stats count as blocks by host, dest_ipv6
| where blocks > 10
| eval assessment="BINDING GAP: " . dest_ipv6 . " blocked " . blocks . " times — check SISF binding table"
```

### Step 3 — Validate
(a) **Scanning test (lab).** With Destination Guard enabled, ping6 100 random addresses in the /64. Verify Splunk shows blocks for each unknown destination and the scanning alert fires.

(b) **Legitimate host test.** Connect a new host, wait for SISF to learn its binding, then ping it from another host. The first ping may be blocked, but subsequent pings should succeed.

(c) **NDP cache comparison.** Compare `show ipv6 neighbors` (should be small with Destination Guard) vs without Destination Guard (fills with INCOMPLETE entries).

### Step 4 — Operationalize

Integrate into the UC-5.20.23 NDP Exhaustion Defence dashboard:
- Add a panel showing Destination Guard blocks vs NDP cache INCOMPLETE entries.
- Show that Destination Guard is preventing NDP cache exhaustion.

**Runbook:**
1. Scanning detected: identify the source and investigate. Destination Guard is blocking the attack — the NDP cache is protected.
2. Binding gap: add the missing address to the SISF binding table (static entry or configure SISF to learn from data traffic).

### Step 5 — Troubleshooting

- **Destination Guard blocking all traffic** — The SISF binding table may be empty or incomplete. Start with `enforcement stressed` (only enforce when the binding table has entries) instead of `enforcement always`.

- **Destination Guard not blocking scanning** — Verify the policy is attached to the correct SVI interface, not an access port. Destination Guard operates at the routing layer (SVI), not the switching layer.

## SPL

```spl
index=network sourcetype="cisco:ios" ("DESTGUARD" OR "destination-guard" OR ("%SISF" "Destination"))
| rex field=_raw "DST:\s*(?<dest_ipv6>[0-9a-fA-F:]+)"
| rex field=_raw "(?:interface|vlan)\s+(?<interface>\S+)"
| stats count as blocked_packets dc(dest_ipv6) as unique_destinations values(dest_ipv6) as destinations by host, interface
| sort -blocked_packets
```

## Visualization

(1) Single-value: packets blocked by Destination Guard in 24h. (2) Timechart: block rate over time — spikes indicate scanning. (3) Table: blocked destinations with frequency.

## Known False Positives

**New host connecting.** Before SISF learns the new host's binding, Destination Guard blocks packets addressed to it. The window is short (seconds) as SISF learns the binding from the host's first NDP Neighbor Advertisement or DHCPv6 exchange.

**Hosts with addresses not learned by SISF.** Statically-configured addresses or addresses from non-standard autoconfiguration may not be in the SISF binding table. These hosts will be unreachable via Destination Guard until their bindings are added.

**Multicast destinations.** Destination Guard should not block multicast (ff00::/8) destinations — these are handled by MLD, not NDP. Verify that the Destination Guard policy excludes multicast.

## References

- [Cisco IPv6 Destination Guard Configuration Guide](https://www.cisco.com/c/en/us/)
- [RFC 6583 — Operational Neighbor Discovery Problems (NDP exhaustion attack that Destination Guard mitigates)](https://www.rfc-editor.org/rfc/rfc6583)
