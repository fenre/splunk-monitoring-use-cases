<!-- AUTO-GENERATED from UC-5.20.137.json — DO NOT EDIT -->

---
id: "5.20.137"
title: "IPv6 Address Randomization and Privacy Extensions Compliance (RFC 8981)"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.137 · IPv6 Address Randomization and Privacy Extensions Compliance (RFC 8981)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*Your IPv6 address can contain your device's hardware serial number, which is like walking around with your name tag always visible. Privacy extensions give you a random name tag that changes regularly. We check that all devices are using random name tags so nobody can track them across different networks.*

---

## Description

Verifies that endpoints use IPv6 privacy extensions (temporary addresses, RFC 8981) where required. Detects devices using SLAAC addresses with embedded EUI-64 identifiers (MAC-derived interface IDs), which enable cross-network device tracking. RFC 8064 recommends stable opaque identifiers instead of EUI-64.

## Value

EUI-64 addresses embed the device's MAC address, creating a globally unique, persistent identifier that allows tracking across networks. Privacy extensions generate temporary randomized addresses that change over time, preventing device tracking. Enterprise compliance policies and GDPR (Breyer ruling — IPv6 as personal data) may require privacy extensions on user devices.

## Implementation

Detect EUI-64 pattern (ff:fe in interface ID) in source addresses. Report devices not using privacy extensions.

## Detailed Implementation

### Prerequisites
- NetFlow or Zeek with source IPv6 addresses.

### Step 1 — Detect EUI-64 pattern: Look for `ff:fe` in the interface ID portion of IPv6 addresses.

### Step 2 — Classify addresses as EUI-64, randomized, or static.

### Step 3 — Validate: Check a known Windows/macOS host — privacy extensions should be enabled by default since Windows Vista and macOS 10.12.

### Step 4 — Operationalize
**Dashboard:** Privacy extensions adoption. **Report:** Devices with EUI-64 addresses.

### Step 5 — Troubleshooting
- Enable privacy extensions:
Linux: `sysctl -w net.ipv6.conf.all.use_tempaddr=2`
Windows: `netsh interface ipv6 set privacy state=enabled`

## SPL

```spl
index=network (sourcetype="netflow" OR sourcetype="zeek:conn") earliest=-24h
| eval is_ipv6=if(match(src, ":"), 1, 0)
| where is_ipv6=1
| rex field=src "(?<prefix>[0-9a-fA-F:]+):(?<iid>[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4})$"
| eval has_eui64=if(match(iid, "[0-9a-fA-F]{1,4}:..ff:fe.."), 1, 0)
| eval address_type=case(
    has_eui64=1, "EUI-64 (MAC-derived — trackable)",
    match(iid, "^[0-9a-fA-F]{4}:[0-9a-fA-F]{4}:[0-9a-fA-F]{4}:[0-9a-fA-F]{4}$"), "Randomized (privacy extensions active)",
    1=1, "Unknown")
| stats count as flows dc(src) as unique_addresses by host, address_type
| where address_type="EUI-64 (MAC-derived — trackable)"
| sort -unique_addresses
```

## Visualization

(1) Pie chart: EUI-64 vs randomized. (2) Table: devices with EUI-64 addresses. (3) Trend: privacy adoption over time.

## Known False Positives

**Infrastructure devices.** Routers, switches, and servers typically use stable addresses (not privacy extensions) by design. Only user endpoints should be checked.

**Manually configured addresses.** Static addresses won't match EUI-64 or privacy patterns. These are acceptable for servers.

## References

- [RFC 8981 — Temporary Address Extensions for Stateless Address Autoconfiguration in IPv6](https://www.rfc-editor.org/rfc/rfc8981)
- [RFC 8064 — Recommendation on Stable IPv6 Interface Identifiers](https://www.rfc-editor.org/rfc/rfc8064)
