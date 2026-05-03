<!-- AUTO-GENERATED from UC-5.2.4.json — DO NOT EDIT -->

---
id: "5.2.4"
title: "VPN Tunnel Status"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.4 · VPN Tunnel Status

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch whether secure tunnels to partners and sites stay up so people working remotely are not left guessing why they cannot connect.*

---

## Description

VPN failures isolate remote sites or users. Proactive monitoring prevents "the VPN is down" calls.

## Value

Operations teams monitor multi-vendor firewall VPN tunnel status transitions and IKE negotiation failures, detecting critical site-to-site connectivity loss and Phase 1/Phase 2 mismatches.

## Implementation

Forward VPN logs. Alert on tunnel down events. Track flapping. Dashboard showing all tunnels.

## Detailed Implementation

### Prerequisites
* Firewall VPN logs in `index=firewall`. Sourcetypes: Palo Alto `pan:system` (IPSec events), Fortinet `fgt_event` (VPN events), Cisco FTD `cisco:firepower:syslog` (VPN events), Juniper SRX `juniper:junos:firewall` (IKE events). Key events: tunnel up/down, IKE negotiation failure, Phase 1/Phase 2 failures.
* VPN types: site-to-site IPSec, remote access VPN (GlobalProtect/FortiClient/AnyConnect), SSL VPN.
* Create `vpn_tunnels.csv` lookup: `tunnel_name`, `peer_ip`, `peer_site`, `criticality`, `expected_status`.

### Step 1 — - Configure data collection
**Palo Alto (IPSec monitoring):**
```
# Network > IPSec Tunnels > Tunnel Monitor > enable
# Device > Log Settings > System > ensure VPN events forwarded
```
Verify:
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)ike|ipsec|vpn|tunnel.*(up|down|fail|establish|disconnect)|phase.*(1|2)")
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- VPN tunnel status monitoring:**
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)ike|ipsec|vpn|tunnel.*(up|down|fail|establish)")
| eval tunnel_event=case(match(_raw, "(?i)tunnel.*up|established|connected|phase.*succeed|SA.*established"), "UP", match(_raw, "(?i)tunnel.*down|disconnected|terminated|SA.*deleted"), "DOWN", match(_raw, "(?i)phase.1.*fail|IKE.*fail|auth.*fail|proposal.*mismatch"), "PHASE1_FAIL", match(_raw, "(?i)phase.2.*fail|ipsec.*fail|transform.*mismatch|no proposal"), "PHASE2_FAIL", match(_raw, "(?i)dpd.*timeout|dead.peer|peer.*unreachable"), "DPD_TIMEOUT", 1==1, "OTHER")
| eval peer=coalesce(peer_ip, remote_ip, vpn_peer, gateway_ip)
| eval tunnel=coalesce(tunnel_name, vpn_name, ike_gateway)
| lookup vpn_tunnels.csv tunnel_name AS tunnel OUTPUT peer_site, criticality
| stats count as events latest(_time) as last_event by tunnel, peer, tunnel_event, peer_site, criticality
| eval severity=case(tunnel_event="DOWN" AND criticality="high", "CRITICAL -- critical tunnel DOWN", tunnel_event="PHASE1_FAIL", "HIGH -- IKE Phase 1 failure", tunnel_event="DPD_TIMEOUT", "HIGH -- peer unreachable", tunnel_event="DOWN", "WARNING -- tunnel down", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Check VPN status: Palo Alto `show vpn ipsec-sa`, Fortinet `diagnose vpn tunnel list`, Cisco `show crypto ipsec sa`.
(b) Flap a test tunnel and verify UP/DOWN events appear in Splunk.
(c) Verify peer IP and tunnel name extraction across all firewall vendors.

### Step 4 — - Operationalize
Dashboard ("Firewall -- VPN Tunnel Status"):
* Row 1 -- Single-value: "Tunnels DOWN", "Phase 1 failures", "DPD timeouts", "Total tunnels".
* Row 2 -- VPN tunnel state table with color-coded status.
* Row 3 -- Tunnel flapping history (up/down events over 24h).

Alerting:
* Critical (critical tunnel DOWN for > 5 min): business-critical site connectivity lost.
* High (Phase 1 failure): IKE negotiation failing -- check pre-shared keys, proposals.
* Warning (DPD timeout): remote peer may be down or network path broken.

### Step 5 — - Troubleshooting

* **Phase 1 failure** -- IKE negotiation mismatch. Check: (1) pre-shared key matches both sides, (2) IKE version (IKEv1 vs IKEv2) matches, (3) encryption/hash/DH group proposals match, (4) peer IP is correct and reachable.

* **Phase 2 failure** -- IPSec transform set mismatch. Check: (1) encryption algorithm matches (AES-256-GCM preferred), (2) proxy IDs / traffic selectors match, (3) PFS group matches.

* **Tunnel flapping** -- Repeatedly going up and down. Common causes: (1) MTU issues (reduce to 1400), (2) unstable WAN link, (3) DPD interval too aggressive (increase to 30s). Check: `show vpn ipsec-sa` for rekey count.

## SPL

```spl
index=firewall ("tunnel" OR "IPSec" OR "IKE") ("down" OR "failed" OR "established")
| rex "(?<tunnel_peer>\d+\.\d+\.\d+\.\d+)"
| eval status=if(match(_raw,"established|up"),"Up","Down")
| stats latest(status) as state by host, tunnel_peer | where state="Down"
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

## Visualization

Status grid (green/red per tunnel), Table, Timeline.

## Known False Positives

Brief tunnel blips during ISP issues, rekeys, or remote endpoint sleep and wake are common and not always incidents.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
