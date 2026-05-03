<!-- AUTO-GENERATED from UC-5.20.71.json — DO NOT EDIT -->

---
id: "5.20.71"
title: "IPv6 Network Scanning and Address Reconnaissance Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.71 · IPv6 Network Scanning and Address Reconnaissance Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*In our old building (IPv4), there were only 254 rooms per floor, so a burglar could knock on every door quickly. In the new building (IPv6), each floor has billions of rooms, so knocking on every door is impossible. Instead, burglars use tricks — they look for rooms with numbers matching specific patterns (like all rooms ending in 1-100), or they shout in the corridor and note who opens their door. We watch for these specific burglar patterns.*

---

## Description

Detects IPv6 network scanning and address reconnaissance using flow data and connection logs. Unlike IPv4 where sequential /24 scans are trivial, IPv6 scanning requires intelligence — attackers use EUI-64 OUI targeting, low-byte address guessing, DNS harvesting, and NDP multicast reconnaissance as documented in RFC 7707. This detection identifies scanning patterns specific to IPv6 address space: probing within a /64 subnet, targeting predictable IID patterns, and using NDP for host discovery.

## Value

IPv6 scanning techniques are fundamentally different from IPv4 and require different detection logic. Traditional IDS rules that detect sequential IP scanning across a /24 will not detect an attacker scanning low-byte addresses (::1 through ::ffff) within a /64, or targeting specific MAC OUI patterns in EUI-64 addresses. Purpose-built IPv6 scanning detection catches these attack patterns that generic network IDS misses entirely.

## Implementation

Analyse connection attempts per source to identify high destination-count patterns within individual /64 prefixes. Correlate with NDP multicast activity. Classify scanning technique based on target address patterns.

## Detailed Implementation

### Prerequisites
- Flow or connection data with IPv6 source and destination addresses.
- Zeek/Corelight sensor for detailed connection-level analysis (preferred).
- Understanding of RFC 7707 scanning techniques for tuning detection thresholds.

### Step 1 — Configure data collection

**Zeek/Corelight (preferred):**
Zeek conn.log records all connection attempts including failed connections. No special IPv6 configuration needed.

**NetFlow v9/IPFIX:**
Ensure IPv6 flow records include source and destination addresses (see UC-5.20.66).

**Firewall deny logs:**
Denied connection attempts (see UC-5.20.65) are the best source for scanning detection — successful connections may be legitimate.

**Verification:**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="netflow") earliest=-1h
| eval dest_ip=coalesce(id_resp_h, dest, destinationIPv6Address)
| where match(dest_ip, ":")
| stats count
```

### Step 2 — Create the search and alert

**Low-byte address scanning detection (RFC 7707 §2.5):**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="netflow" OR sourcetype="paloalto:traffic") earliest=-1h
| eval dest_ip=coalesce(id_resp_h, dest, destinationIPv6Address)
| eval src_ip=coalesce(id_orig_h, src, sourceIPv6Address)
| where match(dest_ip, ":")
| rex field=dest_ip ":(?<iid_last>[0-9a-fA-F]{1,4})$"
| eval iid_decimal=tonumber(iid_last, 16)
| where iid_decimal < 65536
| rex field=dest_ip "(?<prefix64>[0-9a-fA-F:]+:)[0-9a-fA-F:]*:[0-9a-fA-F]{1,4}$"
| stats dc(dest_ip) as unique_low_byte_targets count as attempts by src_ip, prefix64
| where unique_low_byte_targets > 20
| eval alert="Low-byte IPv6 scanning (RFC 7707 §2.5): " . src_ip . " probed " . unique_low_byte_targets . " low-byte addresses in " . prefix64
| sort -unique_low_byte_targets
```

**EUI-64 OUI-targeted scanning:**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="netflow") earliest=-1h
| eval dest_ip=coalesce(id_resp_h, dest)
| where match(dest_ip, ":")
| rex field=dest_ip ":(?<iid_high>[0-9a-fA-F]{4}):[0-9a-fA-F]{2}ff:fe[0-9a-fA-F]{2}:[0-9a-fA-F]{4}$"
| where isnotnull(iid_high)
| stats dc(dest_ip) as eui64_targets by src_ip
| where eui64_targets > 10
| eval alert="EUI-64 OUI-targeted scan: " . src_ip . " targeting " . eui64_targets . " hosts with EUI-64 addresses (manufacturer fingerprinting)"
```
EUI-64 addresses contain ff:fe in the IID. Scanning specifically for EUI-64 hosts indicates the attacker is targeting a specific vendor's equipment.

**Multicast reconnaissance detection (ff02::1 abuse):**
```spl
index=network (sourcetype="zeek:conn" OR sourcetype="cisco:ios") "ff02::1" earliest=-1h
| eval src_ip=coalesce(id_orig_h, src)
| stats count as ping_count by src_ip
| where ping_count > 50
| eval alert="Excessive all-nodes multicast from " . src_ip . " (" . ping_count . " in 1 hour) — active host discovery via NDP"
```

### Step 3 — Validate
(a) **Low-byte scan test.** Use nmap with `nmap -6 --script targets-ipv6-wordlist 2001:db8:test::/64` to generate low-byte scanning traffic. Verify the detection fires.

(b) **EUI-64 detection.** Probe known EUI-64 addresses on a test network. Verify the OUI-targeted scan detection fires.

(c) **Threshold tuning.** Adjust unique_targets threshold based on network size and monitoring system exclusions.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Reconnaissance Detection"):
- Row 1 — Alert panel: active IPv6 scanning sources.
- Row 2 — Table: scanning technique classification (low-byte, EUI-64, multicast, general).
- Row 3 — Timechart: scanning attempt volume over 7 days.
- Row 4 — Network graph: top scanners and their target prefixes.

**Scheduling:** Low-byte and general scanning every 15 minutes. EUI-64 and multicast every 30 minutes.

**Runbook:**
1. External scanner: verify firewall is blocking. Rate-limit if persistent. Report to upstream provider if volumetric.
2. Internal scanner: IMMEDIATE investigation. Likely compromised host running reconnaissance tools (THC-IPv6, scan6, nmap -6).
3. EUI-64 targeting: consider deploying RFC 8064 (opaque IIDs) to eliminate EUI-64 addresses from the network.
4. Multicast reconnaissance: RA Guard and NDP security features (UC-5.20.29 through UC-5.20.36) can limit the effectiveness of multicast reconnaissance.

### Step 5 — Troubleshooting

- **IPv6 scanning is sparse.** Unlike IPv4 where a full /24 scan produces 254 connection attempts, IPv6 scanning produces far fewer attempts spread over a much larger space. Lower detection thresholds accordingly.

- **Address format parsing.** IPv6 addresses can be represented in multiple formats (compressed, expanded, mixed). Ensure the regex patterns handle all representations. Consider normalising IPv6 addresses before analysis.

- **False negative risk.** Smart attackers who spread scanning over long periods (days or weeks) may stay below per-hour thresholds. Use long-term analysis (7-day windows) for persistent low-rate scanning detection.

## SPL

```spl
index=network (sourcetype="netflow" OR sourcetype="zeek:conn" OR sourcetype="paloalto:traffic") earliest=-1h
| eval dest_ip=coalesce(destinationIPv6Address, id_resp_h, dest)
| eval src_ip=coalesce(sourceIPv6Address, id_orig_h, src)
| where match(dest_ip, ":")
| rex field=dest_ip "(?<dest_prefix>[0-9a-fA-F:]+:)[0-9a-fA-F]{1,4}$"
| stats dc(dest_ip) as unique_targets count as attempts by src_ip, dest_prefix
| where unique_targets > 30
| eval scan_type=case(
    unique_targets > 1000, "CRITICAL — broad IPv6 subnet scan (" . unique_targets . " targets in " . dest_prefix . "/64)",
    unique_targets > 100, "HIGH — IPv6 host discovery (" . unique_targets . " targets)",
    unique_targets > 30, "MEDIUM — possible IPv6 reconnaissance",
    1=1, "LOW")
| sort -unique_targets
```

## Visualization

(1) Table: scanning sources with technique classification. (2) Timechart: scanning attempt volume over 24 hours. (3) Network graph: scanner-to-target relationships. (4) Pie chart: scanning technique distribution.

## Known False Positives

**Load balancers health checks.** Load balancers probing multiple backend servers on the same subnet will show high destination counts. Exclude known LB addresses.

**Monitoring systems.** SNMP pollers, network management systems, and synthetic monitoring tools contact many destinations. Maintain an exclusion list.

**CDN prefetch.** Content delivery systems that prefetch from multiple origin servers may appear as scanners.

**IPv6 multicast.** Legitimate NDP multicast traffic (ff02::1, ff02::2) is protocol-defined, not scanning. However, excessive unicast probing within a /64 that follows NDP multicast is suspicious.

## References

- [RFC 7707 — Network Reconnaissance in IPv6 Networks (comprehensive scanning technique taxonomy)](https://www.rfc-editor.org/rfc/rfc7707)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.2.4 — scanning detection)](https://www.rfc-editor.org/rfc/rfc9099)
