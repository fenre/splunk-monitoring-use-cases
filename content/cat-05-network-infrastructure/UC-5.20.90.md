<!-- AUTO-GENERATED from UC-5.20.90.json — DO NOT EDIT -->

---
id: "5.20.90"
title: "IPv6 IDS/IPS Signature Coverage Audit"
status: "verified"
criticality: "high"
splunkPillar: "ES"
---

# UC-5.20.90 · IPv6 IDS/IPS Signature Coverage Audit

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** ES &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*Our security cameras (IDS/IPS) are great at recognising burglars using the old entrance (IPv4). But the new entrance (IPv6) has different types of break-in methods that the cameras might not recognise. We check how many new break-in methods the cameras can spot, and add recognition training for any they're missing.*

---

## Description

Audits IDS/IPS signature coverage for IPv6-specific attacks including NDP cache poisoning, Router Advertisement spoofing, extension header evasion, IPv6 fragmentation attacks, and tunnel encapsulation bypass. Many IDS/IPS deployments have near-zero IPv6 signature coverage, meaning IPv6-specific attacks go completely undetected while IPv4 attacks trigger alerts normally.

## Value

If IDS/IPS cannot detect IPv6 attacks, the entire security monitoring capability has a blind spot. Attackers know this and will use IPv6 attack vectors specifically because they are unlikely to be detected. This audit quantifies the IPv6 signature gap and provides a prioritised list of signatures to deploy. The goal is equivalent IPv6 and IPv4 detection coverage.

## Implementation

Analyse IDS/IPS alert data for IPv6-specific signature hits. Audit ruleset configuration for critical IPv6 signatures. Test detection capability with known IPv6 attack tools. Report coverage gaps.

## Detailed Implementation

### Prerequisites
- IDS/IPS deployment with alert data forwarded to Splunk.
- Access to the IDS/IPS ruleset configuration.
- THC-IPv6 or Scapy for detection validation testing.

### Step 1 — Configure data collection

**Critical IPv6 IDS signatures to verify (Suricata examples):**
```yaml
# RA Spoofing — non-link-local source sending Router Advertisements
alert icmpv6 !fe80::/10 any -> ff02::1 any (msg:"IPv6 RA from non-link-local source — rogue RA"; icmpv6_type:134; sid:9020001; rev:1;)

# NDP Cache Poisoning — unsolicited NA with Override flag
alert icmpv6 any any -> any any (msg:"IPv6 unsolicited NA with Override — potential NDP poisoning"; icmpv6_type:136; content:"|e0|"; offset:4; depth:1; sid:9020002; rev:1;)

# Extension Header Evasion — excessive extension headers
alert ipv6 any any -> any any (msg:"IPv6 packet with >3 extension headers — potential evasion"; ipv6.hdr_count:>3; sid:9020003; rev:1;)

# Fragment Evasion — tiny first fragment
alert ipv6 any any -> any any (msg:"IPv6 tiny first fragment — potential evasion"; fragbits:M; dsize:<100; sid:9020004; rev:1;)

# 6in4 Tunnel Detection
alert ip any any -> any any (msg:"Protocol 41 — 6in4 tunnel detected"; ip_proto:41; sid:9020005; rev:1;)

# Teredo Tunnel Detection
alert udp any any -> any 3544 (msg:"Teredo tunnel traffic — UDP 3544"; sid:9020006; rev:1;)
```

**Create signature coverage checklist lookup:**
```csv
attack_category,required_signature,suricata_sid,status,notes
RA Spoofing,"RA from non-link-local source",9020001,deployed,Custom rule
NDP Poisoning,"Unsolicited NA with Override",9020002,deployed,Custom rule
DAD DoS,"NA responses to DAD probes",TBD,missing,Needs custom rule development
Extension Header Evasion,"Excessive extension headers",9020003,deployed,Custom rule
Fragment Evasion,"Tiny first fragment",9020004,deployed,Custom rule
6in4 Tunnel,"Protocol 41 detection",9020005,deployed,Custom rule
Teredo Tunnel,"UDP 3544 detection",9020006,deployed,Custom rule
Hop-by-Hop DoS,"Hop-by-Hop Options flooding",TBD,missing,Needs custom rule
RH0 Abuse,"Routing Header Type 0",TBD,missing,Covered by ACL but no IDS rule
```
Upload as `ids_ipv6_coverage.csv`.

**Verification:**
```spl
index=network (sourcetype="suricata:alert" OR sourcetype="snort:alert") earliest=-7d
| search alert_signature="*IPv6*" OR alert_signature="*NDP*" OR alert_signature="*ICMPv6*"
| stats count by alert_signature
```

### Step 2 — Create coverage assessment

**Signature coverage matrix:**
```spl
| inputlookup ids_ipv6_coverage.csv
| stats count(eval(status="deployed")) as deployed count(eval(status="missing")) as missing count as total
| eval coverage_pct=round(deployed / total * 100, 0) . "%"
| eval assessment=case(
    deployed=total, "FULL COVERAGE — all critical IPv6 attack signatures deployed",
    missing <= 2, "NEAR FULL — " . missing . " signatures still needed",
    1=1, "SIGNIFICANT GAPS — " . missing . " attack categories undetected")
```

**Detection validation results:**
```spl
| inputlookup ids_ipv6_validation.csv
| eval passed=if(detected="yes", 1, 0)
| stats sum(passed) as detected count as tested
| eval detection_rate=round(detected / tested * 100, 0) . "%"
```

### Step 3 — Validate
(a) **RA spoofing test.** Use THC-IPv6 `fake_router6` on a test segment. Verify the IDS alerts on the RA from a non-link-local source.

(b) **Extension header test.** Use Scapy to craft a packet with 5 chained extension headers. Send through the IDS sensor. Verify alert fires.

(c) **Payload inspection test.** Send a known malicious payload inside a packet with a Destination Options extension header. Verify the IDS inspects THROUGH the extension header and detects the payload.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — IDS/IPS Coverage Audit"):
- Row 1 — Single-value: IPv6 signature coverage percentage.
- Row 2 — Table: signature coverage matrix (deployed vs missing by attack category).
- Row 3 — Timechart: IPv6-specific IDS alerts over 30 days.
- Row 4 — Validation results: last detection test outcomes.

**Scheduling:** Signature coverage assessment quarterly. Detection validation testing semi-annually or after major ruleset updates.

**Runbook:**
1. Missing critical signatures: Deploy custom Suricata/Snort rules from the checklist above. Test before production deployment.
2. Extension header bypass confirmed: Upgrade IDS engine to version with full extension header inspection. As interim mitigation, deploy ACLs to limit extension header chains.
3. Zero IPv6 alerts in 30 days: Verify IDS sensor is processing IPv6 traffic. Check that IPv6 rules are enabled (not just installed). Run test traffic.

### Step 5 — Troubleshooting

- **IDS engine IPv6 support.** Verify the IDS engine version supports IPv6. Older Suricata versions (< 4.0) had limited IPv6 extension header handling. Upgrade to the latest stable version.

- **SPAN/TAP placement.** Ensure the IDS sensor receives IPv6 traffic. If the SPAN session or network TAP is placed on an IPv4-only segment, IPv6 traffic won't reach the sensor.

- **Performance impact.** IPv6 packets with extension headers may require more processing than IPv4 packets. Monitor IDS engine CPU and drop statistics when deploying new IPv6 rules.

## SPL

```spl
index=network (sourcetype="suricata:alert" OR sourcetype="snort:alert" OR sourcetype="zeek:notice") earliest=-30d
| eval is_ipv6_sig=if(match(alert_signature, "(?i)ipv6|ndp|icmpv6|slaac|ra.?guard|router.?advert|neighbor|extension.?header|fragment.?header|6to4|teredo"), 1, 0)
| stats count as total_alerts count(eval(is_ipv6_sig=1)) as ipv6_alerts dc(alert_signature) as total_sigs dc(eval(if(is_ipv6_sig=1, alert_signature, null()))) as ipv6_sigs
| eval ipv6_sig_pct=round(ipv6_sigs / total_sigs * 100, 1)
| eval ipv6_alert_pct=round(ipv6_alerts / total_alerts * 100, 1)
| eval assessment=case(
    ipv6_sigs >= 20, "GOOD — " . ipv6_sigs . " IPv6-specific signatures active",
    ipv6_sigs >= 10, "PARTIAL — " . ipv6_sigs . " IPv6 signatures. Check for RA spoofing, NDP poisoning, extension header evasion.",
    ipv6_sigs >= 1, "POOR — only " . ipv6_sigs . " IPv6 signatures. Major coverage gap.",
    1=1, "CRITICAL — ZERO IPv6-specific IDS signatures. IPv6 attacks are completely undetected.")
```

## Visualization

(1) Single-value: IPv6-specific signature count and percentage of total. (2) Table: IPv6 signatures with hit counts (active vs dormant). (3) Gap analysis: required signatures vs deployed signatures. (4) Trend: IPv6 detection events over time.

## Known False Positives

**Lab/test tool traffic.** Security testing tools (THC-IPv6, Scapy, nmap --script ipv6) may trigger IPv6 IDS signatures during authorised penetration testing. Correlate with change management and pen test schedules.

**Signature category inflation.** Some IDS/IPS signatures are labelled 'IPv6' but actually detect generic protocol issues that happen to mention IPv6. Focus on signatures that detect IPv6-SPECIFIC attacks (RA spoofing, NDP poisoning, etc.).

**Protocol 41 in legitimate tunnels.** Signature for protocol 41 (6in4 tunnel) detection may fire on legitimate transition tunnels. Whitelist authorised tunnel endpoints.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6 — IDS/IPS considerations)](https://www.rfc-editor.org/rfc/rfc9099)
- [Suricata IPv6 Rules Documentation](https://docs.suricata.io/en/latest/rules/ipv6-keywords.html)
- [THC-IPv6 — Attack toolkit for testing IPv6 IDS/IPS detection](https://github.com/vanhauser-thc/thc-ipv6)
