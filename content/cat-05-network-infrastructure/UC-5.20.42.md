<!-- AUTO-GENERATED from UC-5.20.42.json — DO NOT EDIT -->

---
id: "5.20.42"
title: "IPv6 Fragment Reassembly Failure and Overlap Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.42 · IPv6 Fragment Reassembly Failure and Overlap Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*Sometimes a big letter has to be torn into smaller pieces to fit through the mail slots. In IPv6, there are very strict rules about this: only the sender can tear up letters, the pieces can never overlap, and it should be very rare. We watch for someone trying to slip in letters with overlapping pieces — that trick was banned because burglars used it to sneak past the mail inspector.*

---

## Description

Detects IPv6 fragmentation abuse and reassembly failures, including overlapping fragments (banned by RFC 8200), tiny first fragments (evasion technique), fragment bombs (DoS), atomic fragments (deprecated by RFC 8021), and normal reassembly timeouts that indicate path problems. IPv6 fragmentation is architecturally different from IPv4 — only the source can fragment, overlapping fragments are explicitly banned, and fragmentation should be rare because PMTUD is mandatory. Any significant volume of fragmented IPv6 traffic is unusual and warrants investigation.

## Value

IPv6 fragmentation should be rare in a well-configured network because PMTUD adjusts packet sizes at the source. Significant fragmentation indicates either PMTUD failure (UC-5.20.38) or deliberate fragmentation for evasion. Overlapping fragments, which were a major attack vector in IPv4 (Teardrop attack, IDS evasion), are explicitly banned in IPv6 — any overlapping fragment is a definitive indicator of malicious activity. This use case provides fragmentation visibility that most security tools lack, catching both operational issues (reassembly failures) and security threats (evasion, DoS).

## Implementation

Deploy Zeek/Corelight sensors for packet-level fragment analysis. Collect reassembly failure syslog from routers and firewalls. Detect overlapping fragments (attack), tiny fragments (evasion), atomic fragments (deprecated), and excessive fragmentation (DoS or PMTUD failure).

## Detailed Implementation

### Prerequisites
- Zeek/Corelight sensors with IPv6 fragment logging (enabled by default in Zeek 5.0+).
- Router/firewall syslog with reassembly failure messages.
- Understanding that IPv6 fragmentation should be rare — high volumes are inherently suspicious.

### Step 1 — Configure data collection

**Cisco IOS-XE — fragment reassembly logging:**
```
ipv6 virtual-reassembly timeout 15
logging buffered informational
```
Reassembly failures generate syslog messages like:
```
%IPV6-3-FRAG_REASSEMBLY_TIMEOUT: IPv6 fragment reassembly timeout for ID 0x12345678 from 2001:db8::1
%IPV6-4-FRAG_OVERLAP: IPv6 overlapping fragment from 2001:db8::bad
```

**Cisco ASA — fragment policy:**
```
fragment reassembly full outside
fragment chain 24
fragment size 200
```

**Zeek** — fragment analysis is automatic. Check `weird.log` for fragment-related weird events:
```
grep -i frag weird.log
```
Common entries: `fragment_overlap`, `fragment_size_inconsistency`, `fragment_with_DF`.

**Verification:**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="cisco:ios") ("frag" OR "reassembl" OR "Fragment") earliest=-24h
| stats count by host, sourcetype
```

### Step 2 — Create the search and alert

**Fragment overlap detection (CRITICAL — zero legitimate use):**
```spl
index=network (sourcetype="zeek:weird" OR sourcetype="corelight:weird" OR sourcetype="cisco:ios" OR sourcetype="pan:threat")
  ("fragment_overlap" OR "FRAG_OVERLAP" OR "overlapping fragment" OR "frag overlap")
  earliest=-24h
| rex field=_raw "(?:src|source|from)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:dst|dest|to)\s*=?\s*(?<dst_ipv6>[0-9a-fA-F:.]+)"
| stats count as overlap_count first(_time) as first_seen last(_time) as last_seen by src_ipv6, dst_ipv6
| eval severity="CRITICAL — overlapping fragments are banned by RFC 8200. This is definitively malicious."
```
Trigger: any detection. Zero false positive rate — overlapping IPv6 fragments are banned by the protocol specification.

**Reassembly failure trending:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="pan:traffic")
  ("reassembly" AND ("fail" OR "timeout" OR "error"))
  earliest=-24h
| rex field=_raw "(?:src|source|from)\s*=?\s*(?<src_ipv6>[0-9a-fA-F:.]+)"
| timechart span=1h count by host
```

**Fragment bomb detection (excessive fragmented traffic):**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="corelight:conn") earliest=-15m
| eval has_frag=if(match(_raw, "ext_header.*44") OR match(_raw, "(?i)fragment"), 1, 0)
| stats sum(has_frag) as frag_packets count as total_packets by src_ip
| eval frag_pct=round(frag_packets / total_packets * 100, 1)
| where frag_packets > 500 AND frag_pct > 20
| eval alert="Fragment bomb: " . frag_packets . " fragmented packets (" . frag_pct . "% of traffic) from " . src_ip
```
Trigger: more than 500 fragmented packets AND more than 20% of traffic from a single source is fragmented in a 15-minute window.

**Atomic fragment detection (deprecated):**
```spl
index=network (sourcetype="zeek:weird" OR sourcetype="corelight:weird")
  ("IPv6_atomic_fragment" OR "atomic_fragment")
  earliest=-24h
| stats count by src_ip, dst_ip
| eval note="Atomic fragments deprecated by RFC 8021. Source device needs update."
```

### Step 3 — Validate
(a) **Fragment overlap test (lab).** Using Scapy, generate overlapping IPv6 fragments. Verify Zeek logs `fragment_overlap` in weird.log and the alert fires.

(b) **Reassembly timeout test.** Send the first fragment of a packet but not the second. After the reassembly timeout (default 60s on most routers), verify the timeout syslog appears.

(c) **Normal fragmentation.** Send a legitimate large DNS response that requires fragmentation. Verify it appears in the fragmentation trending but does not trigger abuse alerts.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Fragmentation Security"):
- Row 1 — Single-value: overlap detections (must be 0), reassembly failures, fragmented traffic %. Expected: fragmented traffic should be <1% of total IPv6 traffic.
- Row 2 — Timechart: fragmented traffic volume over 24 hours.
- Row 3 — Alerts: all fragment abuse detections (overlaps, tiny fragments, bombs).
- Row 4 — Top fragmenting sources: hosts generating the most fragmented traffic.

**Scheduling:** Overlap detection continuous (every 5 minutes). Reassembly failure trending hourly. Fragment bomb detection every 15 minutes.

**Runbook:**
1. Fragment overlap: IMMEDIATE — block source at perimeter firewall. Alert SOC. This is definitively malicious.
2. Fragment bomb: rate-limit fragmented traffic from the source. Investigate for DoS attack.
3. Reassembly failures: check for PMTUD issues (UC-5.20.38). Check for asymmetric routing splitting fragments across paths.
4. Atomic fragments: identify the source device. Update firmware/OS to stop generating atomic fragments.
5. High fragmentation rate: investigate why sources are fragmenting instead of using PMTUD. Check for misconfigured tunnel MTUs.

### Step 5 — Troubleshooting

- **Zeek weird.log not showing fragments** — Ensure Zeek is deployed inline or on a mirror/TAP port that sees both directions of traffic. Fragment reassembly requires seeing all fragments.

- **Router not logging overlapping fragments** — Many routers silently discard overlapping fragments per RFC 8200 without generating a syslog message. Use Zeek/Corelight for definitive fragment overlap detection — routers are not reliable for this.

- **Fragmentation in ECMP environments** — ECMP can distribute fragments of the same packet across different paths. The receiving router may not see all fragments, causing reassembly failure. This is not an attack but a misconfiguration — use flow-based ECMP (which hashes on the first fragment's 5-tuple and applies the same path to all fragments with the same ID).

## SPL

```spl
index=network (sourcetype="zeek:conn" OR sourcetype="corelight:conn" OR sourcetype="cisco:ios") earliest=-24h
| eval is_fragment=case(
    match(_raw, "(?i)fragment|frag.?offset|reassembl"), 1,
    match(_raw, "ext_header.*44"), 1,
    1=1, 0)
| where is_fragment=1
| eval frag_issue=case(
    match(_raw, "(?i)overlap"), "CRITICAL — fragment overlap (banned by RFC 8200)",
    match(_raw, "(?i)reassembly.?fail|reassembly.?timeout|frag.?timeout"), "HIGH — reassembly failure",
    match(_raw, "(?i)atomic.?frag|offset.?0.*more.?0"), "MEDIUM — atomic fragment (deprecated by RFC 8021)",
    match(_raw, "(?i)tiny.?frag|first.?frag.*len.?[0-7]\d\b"), "HIGH — tiny first fragment (evasion)",
    1=1, "INFO — normal fragmentation")
| stats count by host, frag_issue
| sort -count
```

## Visualization

(1) Single-value: fragment overlap detections (should always be 0), reassembly failures, fragmented traffic as % of total. (2) Timechart: fragmented IPv6 traffic over 24 hours. (3) Table: fragment abuse detections by source and type. (4) Drilldown: fragment details for investigation.

## Known False Positives

**DNS over UDP with large responses.** DNS responses larger than the path MTU may require fragmentation. DNSSEC-signed responses are especially large. This is legitimate fragmentation but should be rare with proper PMTUD.

**IPsec with encapsulation overhead.** IPsec tunnels may fragment packets when the inner packet size plus encapsulation exceeds the outer MTU. This is legitimate but indicates incorrect tunnel MTU configuration (should use `ip mtu` to pre-adjust).

**Reassembly timeout on asymmetric paths.** If different fragments of the same packet arrive at the destination via different paths (ECMP), some fragments may arrive at a different router than others, causing reassembly failure. This is an ECMP misconfiguration issue, not an attack.

## References

- [RFC 8200 — IPv6 Specification §4.5 — Fragment Header (overlapping fragments banned)](https://www.rfc-editor.org/rfc/rfc8200#section-4.5)
- [RFC 8021 — Generation of IPv6 Atomic Fragments Considered Harmful](https://www.rfc-editor.org/rfc/rfc8021)
- [RFC 7112 — Implications of Oversized IPv6 Header Chains (tiny fragment security)](https://www.rfc-editor.org/rfc/rfc7112)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.5.1 — fragmentation security)](https://www.rfc-editor.org/rfc/rfc9099)
