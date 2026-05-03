<!-- AUTO-GENERATED from UC-5.20.15.json — DO NOT EDIT -->

---
id: "5.20.15"
title: "IPv6 Address Accountability and Forensic Mapping"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.15 · IPv6 Address Accountability and Forensic Mapping

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We connect the dots between an internet address, the physical device using it, and the person logged into that device — like a detective tracing a phone number to a handset to a subscriber. In the new internet addressing system this chain has more links, so we check that every link is intact and report any gaps where we can't identify who was behind an address.*

---

## Description

Correlates IPv6 addresses across four independent data sources — flow data, NDP cache entries, DHCPv6 leases, and RADIUS accounting — to build a complete forensic chain from an observed IPv6 address to a physical user, device, and location. This is the IPv6 equivalent of the IPv4 accountability chain (IP → ARP → DHCP → 802.1X → user), but significantly more complex because IPv6 introduces multiple addresses per device (SLAAC, privacy extensions, DHCPv6, link-local), DUIDs that may not contain MACs, and NDP caches that age out faster than ARP tables. RFC 9099 §2.6.2.1 devotes an entire section to this challenge, calling IPv6 address accountability 'one of the most significant operational challenges in IPv6 deployment.'

## Value

During a security incident, the first question is always 'who was behind this IP address at this time?' In IPv4, this is usually answerable from DHCP logs alone. In IPv6, answering this question requires correlating multiple independent data sources because: (1) SLAAC-assigned addresses don't appear in DHCP logs at all, (2) privacy extension addresses change every 24 hours so the address in the alert may already be expired, (3) DHCPv6 DUIDs may not contain the MAC address (UC-5.20.14), and (4) NDP cache entries age out in minutes. This UC measures the 'accountability coverage' — what percentage of IPv6 flows can be traced back to a user? — and identifies which correlation links are missing so they can be strengthened.

## Implementation

Build three KV store lookups from periodic scheduled searches: `ndp_cache_lookup` (IPv6→MAC from NDP polling), `dhcpv6_lease_lookup` (IPv6→DUID from DHCPv6 logs), and `radius_auth_lookup` (MAC→username from RADIUS accounting). The main search joins flow data against all three lookups and measures the accountability depth at four levels: FULL (user known), PARTIAL-MAC (MAC known but no user), PARTIAL-DUID (DUID known but no MAC), NONE (address only). The target is > 90% FULL accountability for managed network segments.

## Detailed Implementation

### Prerequisites
- All four data sources must be actively collecting data:
  - IPFIX/NetFlow v9 with IPv6 (UC-5.20.1)
  - NDP cache polling (UC-5.20.4 / UC-5.20.16)
  - DHCPv6 lease logging (UC-5.20.10)
  - RADIUS accounting from 802.1X infrastructure (Cisco ISE, FreeRADIUS, NPS)
- Three KV store lookups must be populated by scheduled searches:
  1. `ndp_cache_lookup` — IPv6 → MAC → switch → port. Updated every 5-10 minutes from NDP cache polling.
  2. `dhcpv6_lease_lookup` — IPv6 → DUID → lease timestamps. Updated from DHCPv6 lease events.
  3. `radius_auth_lookup` — MAC → username → NAS port → auth timestamp. Updated from RADIUS accounting Start/Stop events.
- KV store collections defined in collections.conf:
```
[ndp_cache_lookup]
field.ipv6_address = string
field.mac_address = string
field.switch_hostname = string
field.switch_port = string
field.last_seen = time

[dhcpv6_lease_lookup]
field.ipv6_address = string
field.duid = string
field.lease_start = time
field.lease_end = time

[radius_auth_lookup]
field.mac = string
field.username = string
field.nas_port = string
field.auth_time = time
```

### Step 1 — Configure data collection

**Populate NDP cache lookup (schedule every 5 minutes):**
```spl
index=network sourcetype="ndp:cache" earliest=-10m
| where NOT match(ipv6_address, "^fe80:") AND NOT match(ipv6_address, "^ff")
| stats latest(mac_address) as mac_address latest(host) as switch_hostname latest(interface) as switch_port latest(_time) as last_seen by ipv6_address
| outputlookup ndp_cache_lookup
```

**Populate DHCPv6 lease lookup (schedule every 15 minutes):**
```spl
index=dhcp sourcetype="infoblox:dhcp" DHCPv6 REPLY earliest=-30m
| rex "IA_NA\s+(?<ipv6_address>[0-9a-fA-F:]+)"
| rex "DUID\s+(?<duid>[0-9a-fA-F:]+)"
| rex "lease\s+(?<lease_start>\d+).*expire\s+(?<lease_end>\d+)"
| where isnotnull(ipv6_address)
| stats latest(duid) as duid latest(lease_start) as lease_start latest(lease_end) as lease_end by ipv6_address
| outputlookup dhcpv6_lease_lookup
```

**Populate RADIUS accounting lookup (schedule every 15 minutes):**
```spl
index=radius sourcetype="cisco:ise:radius" Acct-Status-Type=Start earliest=-30m
| eval mac=lower(replace('Calling-Station-Id', "[-:]", ""))
| eval mac=substr(mac,1,2).":".substr(mac,3,2).":".substr(mac,5,2).":".substr(mac,7,2).":".substr(mac,9,2).":".substr(mac,11,2)
| stats latest(User-Name) as username latest(NAS-Port-Id) as nas_port latest(_time) as auth_time by mac
| outputlookup radius_auth_lookup
```

### Step 2 — Create the search and alert

**Primary search — accountability coverage measurement:**
```spl
index=netflow sourcetype=ipfix earliest=-24h
| where match(src_ip, ":")
| lookup ndp_cache_lookup ipv6_address as src_ip OUTPUT mac_address, switch_hostname, switch_port
| lookup dhcpv6_lease_lookup ipv6_address as src_ip OUTPUT duid, lease_start, lease_end
| lookup radius_auth_lookup mac as mac_address OUTPUT username, nas_port, auth_time
| eval accountability_depth=case(
    isnotnull(username), "FULL — user identified",
    isnotnull(mac_address) AND isnotnull(duid), "PARTIAL — MAC+DUID known, no user",
    isnotnull(mac_address), "PARTIAL — MAC known only",
    isnotnull(duid), "PARTIAL — DUID known only (DUID-EN, no MAC)",
    1==1, "NONE — IPv6 address only")
| stats count as flows dc(src_ip) as unique_addresses by accountability_depth
| eventstats sum(flows) as total_flows
| eval pct=round(flows/total_flows*100, 1)
| sort -pct
```

**Understanding this SPL:**
- The search chains three lookups against flow data. Each lookup adds a layer of correlation.
- `accountability_depth` classifies the result into four levels, from FULL (IPv6 → MAC → user) to NONE (just the IPv6 address, no correlation possible).
- The FULL percentage is the accountability KPI: in a well-instrumented network with 802.1X, this should be > 80% for managed VLANs.

**Forensic investigation search — trace a specific IPv6 address:**
```spl
| makeresults
| eval target_ipv6="2001:db8:1::a8bb:ccff:fedd:eeff"
| eval target_time=strptime("2026-05-03 14:30:00", "%Y-%m-%d %H:%M:%S")
| lookup ndp_cache_lookup ipv6_address as target_ipv6 OUTPUT mac_address, switch_hostname, switch_port, last_seen
| lookup dhcpv6_lease_lookup ipv6_address as target_ipv6 OUTPUT duid, lease_start, lease_end
| lookup radius_auth_lookup mac as mac_address OUTPUT username, nas_port, auth_time
| table target_ipv6, mac_address, switch_hostname, switch_port, duid, username, nas_port, auth_time, last_seen
```
Replace `target_ipv6` and `target_time` with the address and timestamp from the security incident. This single search returns the complete forensic chain.

**Alert — accountability gap exceeds threshold:**
```spl
index=netflow sourcetype=ipfix earliest=-24h
| where match(src_ip, ":")
| lookup ndp_cache_lookup ipv6_address as src_ip OUTPUT mac_address
| lookup radius_auth_lookup mac as mac_address OUTPUT username
| eval accountable=if(isnotnull(username), 1, 0)
| stats sum(accountable) as identified count as total
| eval accountability_pct=round(identified/total*100, 1)
| where accountability_pct < 70
```
Trigger: overall accountability drops below 70%. Indicates NDP polling failure, RADIUS outage, or new VLANs without 802.1X.

### Step 3 — Validate
(a) **Trace yourself:** Find your own laptop's IPv6 address (`ip -6 addr show` or `ipconfig`). Run the forensic search with your address. It should return your MAC, your 802.1X username, and the switch port you're connected to.

(b) **Cross-reference with ISE:** Pick a MAC from the NDP lookup. Search ISE RADIUS logs for that MAC. The username should match the RADIUS lookup result.

(c) **Check timing accuracy:** For a specific address, compare the NDP cache `last_seen` timestamp with the RADIUS `auth_time`. They should be within the same day. If the RADIUS timestamp is weeks old, the RADIUS lookup is stale and needs more frequent updates.

(d) **Test NONE cases:** Find an IPv6 address with NONE accountability. Investigate: is it on a guest VLAN? An IoT device? Infrastructure? Understanding the NONE cases helps calibrate the target percentage.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Address Accountability"):
- Row 1 — Single-value: FULL accountability % (target > 90% for managed VLANs). Trend arrow.
- Row 2 — Stacked bar: accountability depth distribution.
- Row 3 — Table: top 20 NONE-accountability addresses (investigation backlog).
- Row 4 — Forensic lookup panel: input field for IPv6 address → returns full accountability chain.

**Scheduling:** Daily accountability measurement at 06:00. Real-time forensic lookup available on demand.

**Runbook:**
1. Accountability < 70%: check NDP cache polling (is SC4SNMP running?), RADIUS accounting (is ISE sending accounting Start events?), DHCPv6 logging (is the server logging?). The weakest link determines overall accountability.
2. High NONE percentage on specific VLANs: either these VLANs don't have 802.1X (guest, IoT), or NDP polling doesn't cover them. Add polling or accept the gap with documentation.
3. Forensic investigation: always run the forensic search within the valid time window. IPv6 addresses rotate due to privacy extensions — an address from 3 days ago may no longer be in any lookup. Historical NDP cache data (retained in summary index) extends the forensic window.

### Step 5 — Troubleshooting

- **FULL accountability is 0% even with 802.1X** — The RADIUS lookup MAC format may not match the NDP cache MAC format. Normalise both to lowercase colon-separated: `| eval mac=lower(replace(mac, "[-\.]", ":"))`.

- **NDP lookup returns results but RADIUS lookup is empty** — RADIUS accounting may not include the `Calling-Station-Id` (MAC) attribute. Check ISE authentication policy: the authorisation profile must include the MAC attribute in RADIUS accounting.

- **Accountability fluctuates wildly between days** — Privacy extension address churn causes the NDP cache lookup to miss addresses that existed between polls. Increase NDP poll frequency (every 1-2 minutes for high-accountability requirements).

- **Forensic search returns NONE for a known corporate device** — The address may have expired from all lookups. Check historical data: `index=network sourcetype=ndp:cache ipv6_address="<target>" earliest=-30d | head 1`. If found, the lookup was overwritten by a newer poll. Retain historical NDP data in a summary index for extended forensic capability.

## SPL

```spl
index=netflow sourcetype=ipfix earliest=-24h
| where match(src_ip, ":")
| lookup ndp_cache_lookup ipv6_address as src_ip OUTPUT mac_address, switch_hostname, switch_port
| lookup dhcpv6_lease_lookup ipv6_address as src_ip OUTPUT duid, lease_start, lease_end
| lookup radius_auth_lookup mac as mac_address OUTPUT username, nas_port, auth_time
| eval accountability_depth=case(
    isnotnull(username), "FULL — user identified",
    isnotnull(mac_address), "PARTIAL — MAC known, user unknown",
    isnotnull(duid), "PARTIAL — DUID known, MAC unknown (DUID-EN)",
    1==1, "NONE — address only")
| stats count as flows dc(src_ip) as unique_addresses by accountability_depth
| eventstats sum(flows) as total_flows
| eval pct=round(flows/total_flows*100, 1)
```

## Visualization

(1) Stacked bar: accountability depth distribution (FULL/PARTIAL-MAC/PARTIAL-DUID/NONE). (2) Single-value: full accountability percentage (target > 90%). (3) Table: flows with NONE accountability — these are the investigation blind spots. (4) Sankey diagram: flow → NDP → DHCPv6 → RADIUS showing where the correlation chain breaks.

## Known False Positives

**Guest network traffic.** Guest WiFi networks typically don't use 802.1X authentication, so RADIUS accounting is absent. Guest traffic will always show PARTIAL or NONE accountability, which is expected by design — guests are isolated in a separate security zone. Filter guest VLANs from the accountability metric.

**Infrastructure device traffic.** Router-to-router traffic (OSPFv3, BGP, NDP multicast) will not have RADIUS correlations because infrastructure devices authenticate differently (SSH keys, TACACS+). Exclude infrastructure address ranges from the metric.

**Privacy extension addresses not yet in NDP cache.** If a privacy extension address was created after the last NDP cache poll but before the flow was recorded, the NDP lookup will fail. This is a timing gap, not a true accountability failure. Increasing NDP poll frequency reduces this gap.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.2.1 — Address accountability)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 6302 — Logging Recommendations for Internet-Facing Servers (BCP 162 — source port + timestamp for attribution)](https://www.rfc-editor.org/rfc/rfc6302)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§5.2 — Address forensics)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
