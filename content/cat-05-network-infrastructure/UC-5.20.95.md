<!-- AUTO-GENERATED from UC-5.20.95.json — DO NOT EDIT -->

---
id: "5.20.95"
title: "IPv6 IPsec/IKEv2 VPN Tunnel Health and Cipher Compliance"
status: "verified"
criticality: "high"
splunkPillar: "ITSI"
---

# UC-5.20.95 · IPv6 IPsec/IKEv2 VPN Tunnel Health and Cipher Compliance

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** ITSI &middot; **Type:** Availability, Security &middot; **Wave:** Run &middot; **Status:** Verified

*Our secret tunnels (VPN) between offices use the new address system (IPv6). We check that each tunnel is up and running, that the locks on the tunnel (encryption) are the strongest available, and that the key-changing process (rekey) works smoothly. If a tunnel goes down or uses a weak lock, we get an alert immediately.*

---

## Description

Monitors IPv6 IPsec/IKEv2 VPN tunnel health including SA establishment, rekey success, cipher suite compliance, and failure analysis. IPv6 IPsec tunnels have unique characteristics including ESP without NAT traversal, extension header interactions, and PMTUD-dependent MTU management. Cipher suite compliance is verified against current CNSA/NIST guidelines.

## Value

IPsec VPN tunnels are critical infrastructure for site-to-site connectivity and remote access. IPv6 IPsec tunnels may fail silently when ICMPv6 PTB messages are blocked (causing PMTUD failure), when cipher negotiation mismatches occur due to different IPv6 IKE policies, or when extension header processing interferes with ESP. This monitoring ensures IPv6 VPN tunnels remain operational and use approved cryptographic algorithms.

## Implementation

Monitor IKEv2 SA establishment and lifetime events. Track rekey success rate. Verify cipher suites against compliance requirements. Alert on tunnel failures and weak ciphers.

## Detailed Implementation

### Prerequisites
- IPsec VPN infrastructure with IPv6 transport or IPv6 traffic inside tunnels.
- Syslog from VPN gateways.
- Approved cipher suite list per organisational policy.

### Step 1 — Configure data collection

**Cisco IOS-XE IKEv2 IPv6 configuration example:**
```
crypto ikev2 proposal IKEV2-PROPOSAL
 encryption aes-gcm-256
 prf sha384
 group 20
!
crypto ikev2 profile IKEV2-PROFILE
 match identity remote address 2001:db8:peer::1/128
 authentication remote pre-share
 authentication local pre-share
 keyring local IKEV2-KEYRING
!
crypto ipsec transform-set ESP-AES256-GCM esp-gcm 256
 mode tunnel
!
crypto map VPN-MAP 10 ipsec-isakmp
 set peer 2001:db8:peer::1
 set transform-set ESP-AES256-GCM
 set ikev2-profile IKEV2-PROFILE
 match address VPN-ACL-IPv6
```

**Enable detailed IKEv2 logging:**
```
logging level crypto 6
logging level ikev2 6
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%CRYPTO" OR "%IKEv2" | stats count by host | head 10
```

### Step 2 — Create monitoring searches

**Tunnel status dashboard:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:asa") "%CRYPTO" earliest=-24h
| eval tunnel_event=case(
    match(_raw, "SA created"), "up",
    match(_raw, "SA deleted"), "down",
    match(_raw, "rekey.*success"), "rekey_ok",
    match(_raw, "rekey.*fail"), "rekey_fail",
    match(_raw, "proposal.*mismatch"), "negotiation_fail")
| rex field=_raw "peer\s*=?\s*(?<peer>[0-9a-fA-F:.]+)"
| stats latest(tunnel_event) as status count(eval(tunnel_event="down")) as down_count count(eval(tunnel_event="rekey_fail")) as rekey_failures by host, peer
| eval health=case(
    status="up" AND rekey_failures=0, "HEALTHY",
    status="up" AND rekey_failures > 0, "WARNING — rekey issues",
    status="down", "DOWN")
```

**Cipher compliance audit:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:asa") "%CRYPTO" "SA created" earliest=-7d
| rex field=_raw "(?:enc|cipher)\s*=?\s*(?<cipher>[A-Za-z0-9_-]+)"
| rex field=_raw "(?:hash|prf|auth)\s*=?\s*(?<hash>[A-Za-z0-9_-]+)"
| rex field=_raw "(?:group|dh)\s*=?\s*(?<dh_group>\d+)"
| eval cipher_grade=case(
    match(cipher, "(?i)aes-gcm-256|aes.*256.*gcm"), "A",
    match(cipher, "(?i)aes.*256"), "B",
    match(cipher, "(?i)aes.*128"), "C",
    1=1, "F")
| table host, peer, cipher, hash, dh_group, cipher_grade
| sort cipher_grade
```

### Step 3 — Validate
(a) **Tunnel status.** SSH to VPN gateway. Run `show crypto ikev2 sa` and verify IPv6 peer SAs match SPL results.

(b) **Cipher verification.** Run `show crypto ipsec sa` and verify the negotiated transform set matches the expected cipher suite.

(c) **PMTUD test.** Send a large packet (>1400 bytes) through the IPv6 IPsec tunnel. Verify PMTUD works and the tunnel MTU adjusts if needed.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — IPsec VPN Health"):
- Row 1 — Table: all IPv6 IPsec tunnels with status and cipher grade.
- Row 2 — Single-value: tunnels with weak ciphers (grade C or F).
- Row 3 — Timechart: tunnel events (up/down/rekey) over 24 hours.
- Row 4 — Rekey success rate by tunnel.

**Alert:** IPv6 IPsec tunnel down for >5 minutes. Weak cipher in use.

**Runbook:**
1. Tunnel down: Check physical connectivity. Verify IKEv2 proposal match. Check for blocked UDP 500/4500.
2. Rekey failure: Verify SA lifetimes match on both ends. Check for DH group mismatch.
3. Weak cipher: Plan cipher upgrade during maintenance window. Update IKEv2 proposal on both ends simultaneously.

### Step 5 — Troubleshooting

- **PMTUD failure through IPsec.** If ICMPv6 PTB messages are blocked upstream of the IPsec gateway, PMTUD fails and large packets are silently dropped. The symptom is TCP connections that establish but hang on data transfer. Enable `crypto ipsec fragmentation before-encryption` as a workaround.

- **NAT64 interaction.** When IPv6 IPsec traffic traverses NAT64, UDP encapsulation (NAT-T, port 4500) is required. Verify NAT-T is enabled on both peers.

- **Certificate-based authentication.** IPv6 addresses in IKEv2 certificates (in the Subject Alternative Name extension) use the format `IPAddress:2001:db8::1`. Verify certificate parsing handles IPv6 addresses correctly.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:asa" OR sourcetype="cisco:ftd") earliest=-24h
  ("%CRYPTO" OR "%ISAKMP" OR "%IKEv2" OR "ipsec")
| eval is_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}"), 1, 0)
| where is_ipv6=1
| eval event_type=case(
    match(_raw, "(?i)SA.*created|tunnel.*up|established"), "TUNNEL_UP",
    match(_raw, "(?i)SA.*deleted|tunnel.*down|delete"), "TUNNEL_DOWN",
    match(_raw, "(?i)rekey|rekeyed"), "REKEY",
    match(_raw, "(?i)fail|error|mismatch|reject"), "FAILURE",
    1=1, "OTHER")
| rex field=_raw "(?:peer|remote)\s*=?\s*(?<peer_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:cipher|enc|transform)\s*=?\s*(?<cipher_suite>[A-Za-z0-9_-]+)"
| eval cipher_status=case(
    match(cipher_suite, "(?i)AES.*256.*GCM|CHACHA20"), "STRONG",
    match(cipher_suite, "(?i)AES.*128|AES.*CBC"), "ACCEPTABLE — consider upgrading to AES-256-GCM",
    match(cipher_suite, "(?i)3DES|DES|RC4"), "WEAK — must remediate immediately",
    1=1, null())
| stats count as events latest(event_type) as current_state count(eval(event_type="FAILURE")) as failures count(eval(event_type="REKEY")) as rekeys by host, peer_ipv6, cipher_suite, cipher_status
| sort -failures
```

## Visualization

(1) Table: IPv6 VPN tunnels with status, cipher, and rekey health. (2) Timechart: tunnel up/down events. (3) Single-value: tunnels with weak ciphers (target: 0). (4) Alert panel: tunnel failures.

## Known False Positives

**Planned rekeys.** IKE SA and child SA rekeys are normal operational events. Alert on rekey FAILURES, not successful rekeys.

**DPD (Dead Peer Detection) events.** DPD keepalive messages are normal. Only alert when DPD detects a dead peer and the tunnel goes down.

**Cipher negotiation during migration.** When upgrading cipher suites, both old and new ciphers may be offered. Temporary use of the old cipher during migration is expected.

## References

- [RFC 7296 — Internet Key Exchange Protocol Version 2 (IKEv2)](https://www.rfc-editor.org/rfc/rfc7296)
- [RFC 4301 — Security Architecture for the Internet Protocol (IPsec)](https://www.rfc-editor.org/rfc/rfc4301)
- [CNSA 2.0 — Commercial National Security Algorithm Suite (cipher requirements)](https://media.defense.gov/2022/Sep/07/2003071834/-1/-1/0/CSA_CNSA_2.0_ALGORITHMS_.PDF)
