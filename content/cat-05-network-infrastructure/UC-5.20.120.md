<!-- AUTO-GENERATED from UC-5.20.120.json — DO NOT EDIT -->

---
id: "5.20.120"
title: "IPv6 Address Stability and Interface ID Tracking (RFC 7217 / RFC 8981)"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.120 · IPv6 Address Stability and Interface ID Tracking (RFC 7217 / RFC 8981)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*Old-style IPv6 addresses embedded your device's unique hardware number (like a license plate), so anyone could track where you go. Modern addresses are like changing disguises — they look different on each network. We check how many devices on our network still have the old trackable addresses and need to be updated to the new anonymous style.*

---

## Description

Tracks IPv6 interface identifier generation methods across the network: deprecated EUI-64 (privacy risk), RFC 7217 stable OPAQUE (recommended), and RFC 8981 temporary addresses (privacy-preserving but forensically challenging). Understanding the distribution helps assess privacy compliance and forensic capability.

## Value

EUI-64 addresses embed the device's MAC address, creating a persistent tracking identifier that violates GDPR privacy requirements (per the Breyer ruling). RFC 7217 provides stability without exposing the MAC. RFC 8981 temporary addresses provide maximum privacy but make forensic correlation difficult. Understanding the mix helps balance privacy and security needs.

## Implementation

Analyse IPv6 source addresses for EUI-64 patterns (::ffXX:XXXX:XXXX with ff:fe in the middle). Track the distribution of address types over time.

## Detailed Implementation

### Prerequisites
- IPv6 traffic logs in Splunk.

### Step 1 — Configure data collection
No special configuration needed — this UC analyses existing traffic data.

### Step 2 — Create monitoring searches

**EUI-64 device identification (remediation targets):**
```spl
index=network earliest=-7d
| eval is_eui64=if(match(src, "[Ff][Ff][Ff][Ee]"), 1, 0)
| where is_eui64=1
| rex field=src "(?<prefix>[0-9a-fA-F:]+):(?<iid_high>[0-9a-fA-F]{1,4}):[Ff][Ff][Ff][Ee]:(?<iid_low>[0-9a-fA-F:]+)$"
| eval mac_oui=replace(iid_high . ":ff:fe:" . iid_low, "(..)(..):ff:fe:(..)(..)", "\1:\2:XX:XX:\3:\4")
| stats dc(src) as addresses count as events by mac_oui
| sort -events
```

### Step 3 — Validate
Check a known device's IPv6 address. If it contains ff:fe, it's using EUI-64.

### Step 4 — Operationalize
**Dashboard:** Address type distribution. **Alert:** EUI-64 percentage increasing — regression.

### Step 5 — Troubleshooting
- **Disabling EUI-64 on Linux:** `sysctl -w net.ipv6.conf.all.addr_gen_mode=2` (RFC 7217 stable privacy).
- **Windows:** RFC 7217 is default since Windows 10 1703.

## SPL

```spl
index=network earliest=-24h
| eval is_ipv6=if(match(src, ":"), 1, 0)
| where is_ipv6=1
| eval iid_type=case(
    match(src, "[Ff][Ff][Ff][Ee]"), "EUI-64 (deprecated — contains MAC address)",
    match(src, "::[0-9a-fA-F]{1,4}$") AND len(replace(src, "[^:]", "")) < 5, "Likely static/manual",
    1=1, "OPAQUE or temporary (RFC 7217/8981)")
| stats dc(src) as unique_addresses count as events by iid_type
| eval pct=round(unique_addresses / sum(unique_addresses) * 100, 1)
| table iid_type, unique_addresses, pct, events
```

## Visualization

(1) Pie chart: address type distribution. (2) Table: hosts using EUI-64 (remediation targets). (3) Trend: EUI-64 usage declining over time.

## Known False Positives

**Server addresses.** Servers often use static IPv6 addresses that may look like low-byte or manual assignments. These are intentional.

**Router interfaces.** Router-facing interfaces typically use manually assigned addresses. Not a concern.

## References

- [RFC 7217 — A Method for Generating Semantically Opaque Interface Identifiers](https://www.rfc-editor.org/rfc/rfc7217)
- [RFC 8981 — Temporary Address Extensions for Stateless Address Autoconfiguration in IPv6](https://www.rfc-editor.org/rfc/rfc8981)
- [RFC 8064 — Recommendation on Stable IPv6 Interface Identifiers](https://www.rfc-editor.org/rfc/rfc8064)
