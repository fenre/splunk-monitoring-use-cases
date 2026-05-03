<!-- AUTO-GENERATED from UC-5.18.6.json — DO NOT EDIT -->

---
id: "5.18.6"
title: "VRF Route Leaking Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.18.6 · VRF Route Leaking Detection

> **Criticality:** Critical &middot; **Difficulty:** Expert &middot; **Pillar:** Observability &middot; **Type:** Security, Compliance, Operations &middot; **Wave:** Run &middot; **Status:** Verified

*We watch for edits that accidentally stitch two private customer closets together through the plumbing. Catching that fast keeps each renter’s mail from wandering into the wrong mailbox.*

---

## Description

Splunk correlates risky VRF import/export edits, RT mutations, and overlapping commit narratives so unintended VPN route leaking—whether mis-click or hostile insider action—triggers review workflows before prefixes traverse wrong RD boundaries.

## Value

Risk and engineering leadership preserve tenant isolation guarantees because Splunk proves who changed which leaking construct and surfaces subtle RT imports that traditional BGP flap alarms never articulate.

## Implementation

Mirror configuration changes and orchestrator plans into Splunk, baseline peer-approved patterns via lookup `approved_vrf_policies.csv`, alert on first-seen RT tuples or policy names tied to export maps touching multiple VPNs.

## Detailed Implementation

### Prerequisites
- Change-management taxonomy tagging golden configs vs emergency edits.
- Role-based actor normalization (`tacacs_username`).

### Step 1 — Source onboarding
Enable archived configs: Cisco IOS-XR commit logs to syslog; Junos `configuration archival`; Nokia SR OS admin audit stream to SIEM.

### Step 2 — Regex tuning workshop
Inventory legitimate hub-spoke leak patterns (central services VRF) and encode allow-list keys `(host,policy_name)`.

### Step 3 — Detection logic
Fire alert when commit includes `route-target import` referencing foreign ASN not on allow-list OR NETCONF `<import-route-target>` delta crosses VPN boundary.

### Step 4 — Validation tabletop
Replay sanitized configs through Splunk `_new_eval` testing index ensuring positives match SOC expectations without noisy duplicate commits.

### Step 5 — Response hook
Auto-create ticket with diff snippet and link to last-known-good RIB snapshot search ID for rollback verification.

## SPL

```spl
index=network OR index=audit earliest=-24h@h latest=now
| eval msg=lower(_raw)
| eval cfg_hit=match(msg,"(?:commit|configuration|config.?chang)") OR match(sourcetype,"audit|config|netconf|yang")
| eval leak_hint=match(msg,"(?:route.?target|rt.?import|rt.?export|vrf.?import|vrf.?export|route.?leak|vpn.?instance.*(?:import|export)|(?:unnecessary|unexpected).*vpn.*route|(?:policy).*(?:vpn|vrf).*(?:(?:accept|match).*route))")
| eval risky_cmd=match(msg,"(?:import.?route.?target|export.?route.?target|vrf.?route.?import|route.?target.?import|next-hop.?unchanged|(?:router|routing.?instance).*(?:import|export)|(?:policy.?option|prefix.?limit).*(?:leak|aggregate))")
| where (cfg_hit=1 AND leak_hint=1) OR risky_cmd=1
| rex field=_raw max_match=0 "(?i)vrf[^A-Za-z0-9_/:-]*(?<vrf>[A-Za-z0-9_.:-]+)"
| rex field=_raw max_match=0 "(?i)(?:user|acct)\s*[:=]?\s*(?<actor>[A-Za-z0-9_.@-]+)"
| stats earliest(_time) as first_seen latest(_time) as last_seen values(actor) as actors values(vrf) as vrfs count by host sourcetype
| sort - count
```

## Visualization

Dashboard Studio: KPI for risky commits per day; Sankey-style diagram from actor→host→vrfs (manual SVG asset optional); table (`host`, `vrfs`, `actors`, `count`).

## Known False Positives

**Approved shared services RT:** explicit imports flagged until allow-listed.**Automated audits:** nightly scripts rewriting harmless ordering churn.**Encrypted NETCONF:** payloads unavailable—need collector-side decryption.**Template rollout:** mass commits spike counts—tag pipeline IDs.**False actor:** shared jump-box account obscures real user—pair with session correlation.

## References

- [Cisco MPLS VPN Route Target Attributes](https://www.cisco.com/c/en/us/support/docs/multiprotocol-label-switching-mpls/mpls/581220008-vpn-route-target-import-export-vrf.htm)
- [Juniper Routing Instances Overview — VPN Import Policies](https://www.juniper.net/documentation/us/en/software/junos/routing-policy/topics/concept/routing-policy-overview.html)
- [Nokia SR OS Routing Protocols Guide — BGP/MPLS IP VPNs](https://documentation.nokia.com/)
