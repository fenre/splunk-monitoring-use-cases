<!-- AUTO-GENERATED from UC-5.20.141.json — DO NOT EDIT -->

---
id: "5.20.141"
title: "IPv6 DHCPv6 Prefix Delegation (PD) Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.20.141 · IPv6 DHCPv6 Prefix Delegation (PD) Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Availability, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*When a branch office needs its own block of IPv6 addresses, it asks the central office to delegate a range. It's like a franchise getting permission to use part of the company's phone number block. We track which branches have their numbers, when they need to renew, and catch anyone unauthorized trying to grab a block.*

---

## Description

Monitors DHCPv6 Prefix Delegation (PD) operations where prefixes are assigned to requesting routers. Tracks the lifecycle of delegated prefixes (assignment, renewal, expiration, failure) and detects unauthorized delegation requests. Prefix delegation failures can leave entire downstream networks without IPv6 connectivity.

## Value

DHCPv6 PD is how branch offices, customer sites, and home networks obtain their IPv6 prefix. If PD fails, every host behind the requesting router loses IPv6. Monitoring PD operations ensures timely detection of pool exhaustion, unauthorized delegation requests, and prefix lifecycle issues before they cause outages.

## Implementation

Monitor DHCPv6 PD events in router syslog. Track prefix assignments and expirations. Alert on failures and unauthorized requests.

## Detailed Implementation

### Prerequisites
- DHCPv6 server with prefix delegation configured.
- Router syslog to Splunk.

### Step 1 — Verify DHCPv6 PD configuration:
```
show ipv6 dhcp pool
show ipv6 dhcp binding
```

### Step 2 — Monitor PD events in syslog.

### Step 3 — Validate: Request a prefix from a test router. Verify the event appears in Splunk.

### Step 4 — Operationalize
**Dashboard:** Prefix delegation lifecycle. **Alert:** PD failure or pool exhaustion — high.

### Step 5 — Troubleshooting
- Pool exhaustion: Expand prefix pool or reduce lease times.
- PD failure: Check DUID matching and pool configuration.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h
  ("prefix.*delegation" OR "DHCPv6" OR "PD.*assign" OR "PD.*expire" OR "PD.*renew")
| eval pd_event=case(
    match(_raw, "(?i)PD.*assign|prefix.*delegat.*assign"), "PREFIX_ASSIGNED",
    match(_raw, "(?i)PD.*renew|prefix.*delegat.*renew"), "PREFIX_RENEWED",
    match(_raw, "(?i)PD.*expire|prefix.*delegat.*expire"), "PREFIX_EXPIRED",
    match(_raw, "(?i)PD.*fail|prefix.*delegat.*fail|no.*prefix.*available"), "PREFIX_FAILED",
    match(_raw, "(?i)unauthorized.*PD|rogue.*delegat"), "UNAUTHORIZED_PD",
    1=1, null())
| where isnotnull(pd_event)
| rex field=_raw "prefix\s*(?<delegated_prefix>[0-9a-fA-F:]+/\d+)"
| stats count as events values(delegated_prefix) as prefixes by host, pd_event
| eval severity=case(
    pd_event="UNAUTHORIZED_PD", "CRITICAL — unauthorized prefix delegation request",
    pd_event="PREFIX_FAILED" AND events > 5, "HIGH — prefix delegation failures — pool exhaustion?",
    pd_event="PREFIX_EXPIRED" AND events > 10, "MEDIUM — multiple prefix expirations",
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Table: delegated prefixes with lifecycle state. (2) Timechart: PD events over time. (3) Single-value: active delegated prefixes. (4) Alert: PD failures.

## Known False Positives

**Scheduled renewals.** Regular prefix renewals are normal operational events, not alerts.

**Lab environments.** Frequent PD requests in test environments with short lease times are expected.

## References

- [RFC 8415 — Dynamic Host Configuration Protocol for IPv6 (DHCPv6) — §6.3 Prefix Delegation](https://www.rfc-editor.org/rfc/rfc8415#section-6.3)
- [RFC 3633 — IPv6 Prefix Options for DHCPv6 (historical)](https://www.rfc-editor.org/rfc/rfc3633)
