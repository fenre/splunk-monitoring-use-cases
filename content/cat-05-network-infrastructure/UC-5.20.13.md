<!-- AUTO-GENERATED from UC-5.20.13.json — DO NOT EDIT -->

---
id: "5.20.13"
title: "EUI-64 Address Usage Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.13 · EUI-64 Address Usage Detection

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We check for devices that accidentally broadcast their unique hardware serial number inside their internet address — like writing your Social Security number on every envelope you send. Modern devices know not to do this, but older ones still do, and we flag them so they can be updated.*

---

## Description

Detects IPv6 addresses using the EUI-64 Interface Identifier format, which embeds the device's MAC address directly into the IPv6 address. RFC 8064 deprecated EUI-64 for SLAAC in 2017, recommending opaque stable IIDs (RFC 7217) instead. EUI-64 addresses are a privacy risk (RFC 7721): they reveal the device's MAC address to any observer on the network path, enable cross-network device tracking (the IID stays the same regardless of which /64 prefix the device joins), and expose the hardware vendor via the OUI. The `ff:fe` pattern in the IID is the telltale signature — it never occurs naturally in non-EUI-64 addresses.

## Value

EUI-64 addresses reveal hardware identity to every hop between source and destination. For organisations with privacy requirements (GDPR — IPv6 addresses are personal data per the Breyer ruling), employees' devices being tracked across networks by their embedded MAC is a compliance concern. For security teams, EUI-64 also enables reconnaissance: an attacker who captures one IPv6 address can extract the MAC, determine the vendor (OUI lookup), and use the MAC to find the same device on other VLANs or at other times. RFC 8064 and RFC 7217 provide the fix (opaque IIDs), but many older devices, IoT sensors, and network equipment still default to EUI-64. This UC identifies them for remediation.

## Implementation

Search for the `ff:fe` pattern in the Interface Identifier portion of IPv6 source addresses across flow data, NDP caches, or any IPv6-bearing data source. Any match indicates an EUI-64 address. The search counts affected devices per network segment and can optionally extract the embedded MAC for vendor lookup. Schedule weekly for compliance dashboards.

## Detailed Implementation

### Prerequisites
- Any data source with IPv6 addresses indexed in Splunk. This UC analyses existing data — no new inputs needed.
- Understanding of EUI-64 address construction:
  1. Take MAC address: `aa:bb:cc:dd:ee:ff`
  2. Insert `ff:fe` between bytes 3 and 4: `aa:bb:cc:ff:fe:dd:ee:ff`
  3. Flip the Universal/Local (U/L) bit (bit 7 of byte 1): `a8:bb:cc:ff:fe:dd:ee:ff`
  4. The IID becomes `a8bb:ccff:fedd:eeff`
  5. Combined with prefix: `2001:db8:1::a8bb:ccff:fedd:eeff`
  The `ff:fe` in the middle is the signature. No other address generation mechanism produces this pattern.

### Step 1 — Configure data collection
No new data collection needed. Verify IPv6 addresses are available:
```spl
index=netflow OR index=network earliest=-1h
| where match(src_ip, ":")
| head 10
| table src_ip
```

### Step 2 — Create the search and alert

**Primary search — EUI-64 address detection:**
```spl
index=netflow sourcetype=ipfix earliest=-24h
| where match(src_ip, ":")
| where match(src_ip, "(?i)[0-9a-f]{1,4}:[0-9a-f]*ff:fe[0-9a-f]*:[0-9a-f]{1,4}$")
| rex field=src_ip "(?i)(?<iid>[0-9a-f]{1,4}:[0-9a-f]*ff:fe[0-9a-f]*:[0-9a-f]{1,4})$"
| eval mac_embedded="Embedded MAC visible in IID — privacy risk per RFC 7721"
| stats dc(src_ip) as eui64_addr_count count as total_flows by host
| sort -eui64_addr_count
```

**Understanding this SPL:**
- The regex `[0-9a-f]{1,4}:[0-9a-f]*ff:fe[0-9a-f]*:[0-9a-f]{1,4}$` matches the `ff:fe` signature in the lower 64 bits of the IPv6 address. The `$` anchor ensures we're matching the IID portion, not a coincidental `ff:fe` in the prefix.
- `(?i)` makes the match case-insensitive — some TAs store hex in uppercase.
- Grouping by `host` (the flow exporter/router) shows which network segments have EUI-64 devices.

**Variant — extract the embedded MAC address:**
```spl
index=netflow sourcetype=ipfix earliest=-24h
| where match(src_ip, "(?i)[0-9a-f]{1,4}:[0-9a-f]*ff:fe[0-9a-f]*:[0-9a-f]{1,4}$")
| rex field=src_ip "(?i)(?<b1>[0-9a-f]{2})(?<b2>[0-9a-f]{2}):(?<b3>[0-9a-f]{2})ff:fe(?<b4>[0-9a-f]{2}):(?<b5>[0-9a-f]{2})(?<b6>[0-9a-f]{2})$"
| eval mac=b1.":".b2.":".b3.":".b4.":".b5.":".b6"
| eval oui=b1.":".b2.":".b3
| lookup oui_vendor_lookup oui OUTPUT vendor
| stats count as flows latest(vendor) as device_vendor by src_ip, mac
| sort -flows
```
Note: this requires an `oui_vendor_lookup.csv` populated from the IEEE OUI database. The U/L bit flip is not reversed in this simplified version — for exact MAC recovery, XOR the first byte with 0x02.

**Alert — EUI-64 on high-sensitivity VLAN:**
```spl
index=network sourcetype="ndp:cache" earliest=-24h
| where NOT match(ipv6_address, "^fe80:")
| where match(ipv6_address, "(?i)ff:fe")
| lookup sensitive_vlans interface OUTPUT vlan_sensitivity
| where vlan_sensitivity="high"
| stats dc(ipv6_address) as eui64_count by interface, host
```
Trigger: any EUI-64 address on a VLAN tagged as high-sensitivity (e.g., executive, finance, HR networks where GDPR/privacy concerns are elevated).

### Step 3 — Validate
(a) **Manual verification:** On a device with EUI-64 enabled (older Linux with `use_tempaddr=0`), check `ip -6 addr show`. The global address should contain `ff:fe` in the IID. Search Splunk for that address — it should appear in the EUI-64 results.

(b) **MAC extraction check:** For a detected EUI-64 address, manually extract the MAC (reverse the EUI-64 construction) and compare against `show mac address-table` on the access switch. They should match.

(c) **Negative test:** A device using RFC 7217 opaque IIDs (modern Windows, macOS) should NOT appear in the EUI-64 results. Verify by checking your own laptop's IPv6 address.

### Step 4 — Operationalize

**Dashboard** (panel on "IPv6 — Address Hygiene"):
- Row 1 — Single-value: EUI-64 device count (target: trending to 0). Pie chart: EUI-64 vs non-EUI-64.
- Row 2 — Table: EUI-64 addresses with extracted MAC, vendor, network segment.
- Row 3 — Timechart: EUI-64 count over 90 days (should decrease as devices are updated).

**Scheduling:** Weekly compliance report.

**Runbook:**
1. Endpoint devices (laptops, phones): push privacy extension configuration via MDM or GPO. Windows: `netsh interface ipv6 set privacy state=enabled`. Linux: `sysctl -w net.ipv6.conf.all.use_tempaddr=2`.
2. IoT devices: check if firmware supports RFC 7217. If not, document as a known limitation and mitigate by restricting IoT to dedicated VLANs.
3. Network infrastructure: EUI-64 on router interfaces is acceptable (low privacy risk for infrastructure addresses). Focus remediation on endpoint devices.

### Step 5 — Troubleshooting

- **No EUI-64 addresses found but expected** — Modern OS defaults have changed. Windows 10+, macOS 10.12+, and recent Linux distributions default to RFC 7217 opaque IIDs. EUI-64 may genuinely be absent. Check older devices, IoT, and printers.

- **Too many false matches** — If the regex matches addresses without actual EUI-64, tighten by requiring the ff:fe to be in specific byte positions of the IID. The IID is the last 64 bits (4 colon-separated groups of 4 hex digits). `ff:fe` must span bytes 4-5 of the 8-byte IID.

- **Cannot extract MAC due to address format** — Compressed IPv6 addresses (with `::`) may not have all 8 groups visible. Expand the address before regex extraction, or use NDP cache data where both MAC and IPv6 are separate fields.

## SPL

```spl
index=netflow sourcetype=ipfix earliest=-24h
| where match(src_ip, ":")
| rex field=src_ip ":(?<iid_part>[0-9a-fA-F:]+)$"
| where match(src_ip, "(?i)[0-9a-f]{1,4}:[0-9a-f]*ff:fe[0-9a-f]*:[0-9a-f]{1,4}$")
| eval mac_extracted="EUI-64 detected — MAC address embedded in IID"
| stats dc(src_ip) as eui64_addresses count as flows by host
| where eui64_addresses > 0
| sort -eui64_addresses
```

## Visualization

(1) Single-value: count of unique EUI-64 addresses detected (24h). (2) Table: EUI-64 address, extracted MAC, vendor (OUI lookup), source router/switch, flow count. (3) Pie chart: EUI-64 vs non-EUI-64 address ratio. (4) Bar chart: EUI-64 addresses by network segment — identifies which VLANs have devices still using EUI-64.

## Known False Positives

**Network infrastructure devices intentionally use EUI-64.** Router interfaces, switch SVIs, and other infrastructure devices commonly use EUI-64 for their SLAAC addresses. This is less of a privacy concern because infrastructure addresses are already documented in IPAM. Filter infrastructure devices via a lookup to focus on endpoint devices.

**IoT devices with no privacy extension support.** Many IoT sensors, cameras, and embedded systems use EUI-64 because their IPv6 stack doesn't support RFC 7217 or RFC 8981 privacy extensions. These are legitimate findings (they should be flagged) but remediation may require firmware updates from the manufacturer rather than a configuration change.

**The `ff:fe` pattern in non-EUI-64 contexts.** Extremely unlikely, but a randomly generated IID could contain `ff:fe` in the right position by chance. The probability is ~1 in 65,536 per address. If you need certainty, extract the embedded MAC and verify it matches a known OUI via an IEEE OUI lookup.

## References

- [RFC 8064 — Recommendation on Stable IPv6 Interface Identifiers (deprecates EUI-64 for SLAAC)](https://www.rfc-editor.org/rfc/rfc8064)
- [RFC 7721 — Security and Privacy Considerations for IPv6 Address Generation Mechanisms](https://www.rfc-editor.org/rfc/rfc7721)
- [RFC 7217 — A Method for Generating Semantically Opaque Interface Identifiers with IPv6 SLAAC](https://www.rfc-editor.org/rfc/rfc7217)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.5 — Address accountability)](https://www.rfc-editor.org/rfc/rfc9099)
