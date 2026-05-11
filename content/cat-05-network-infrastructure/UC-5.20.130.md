<!-- AUTO-GENERATED from UC-5.20.130.json — DO NOT EDIT -->

---
id: "5.20.130"
title: "IPv6 Cloud Provider Connectivity and Peering Health"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.130 · IPv6 Cloud Provider Connectivity and Peering Health

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Our company stores important files in remote warehouses (cloud providers like AWS and Azure). We need to make sure the roads using new-format addresses (IPv6) to these warehouses are working properly and not slower than the old roads (IPv4).*

---

## Description

Monitors IPv6 connectivity to major cloud providers (AWS, Azure, GCP) including traffic flows, latency, and reachability. As organizations move workloads to cloud with dual-stack support, IPv6 connectivity to cloud endpoints becomes as critical as IPv4.

## Value

Cloud workloads increasingly require IPv6 connectivity. If IPv6 paths to cloud providers are degraded or broken, dual-stack applications fall back to IPv4, potentially causing performance issues or hitting IPv4 NAT limitations. Dedicated cloud IPv6 monitoring ensures the fastest path to cloud resources is always available.

## Implementation

Monitor traffic flows to known cloud provider IPv6 prefixes. Track latency and compare with IPv4 paths. Alert on IPv6 cloud connectivity loss.

## Detailed Implementation

### Prerequisites
- Firewall/router logging for IPv6 traffic.
- Cloud provider IPv6 prefix lists.

### Step 1 — Create cloud provider prefix lookup from published IP ranges (AWS ip-ranges.json, Azure ServiceTags, GCP cloud.json).

### Step 2 — Monitor IPv6 traffic to cloud prefixes.

### Step 3 — Compare IPv6 vs IPv4 latency to cloud endpoints.

### Step 4 — Operationalize
**Dashboard:** Cloud IPv6 connectivity. **Alert:** Zero IPv6 flows to a previously-reachable cloud — high.

### Step 5 — Troubleshooting
- No IPv6 to cloud: Check BGP peering on Direct Connect/ExpressRoute. Verify IPv6 address family is enabled.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="pan:traffic") earliest=-4h
| eval cloud_dest=case(
    match(dest, "^2600:1f") OR match(dest, "^2406:da"), "AWS",
    match(dest, "^2603:"), "Azure",
    match(dest, "^2607:f8b0:"), "Google Cloud",
    match(dest, "^2a05:d"), "AWS (EU)",
    1=1, null())
| where isnotnull(cloud_dest)
| stats count as flows sum(bytes) as total_bytes avg(duration) as avg_duration by cloud_dest
| eval status=case(
    flows > 0 AND avg_duration < 1, "OK — " . flows . " flows to " . cloud_dest,
    flows > 0 AND avg_duration >= 1, "DEGRADED — elevated latency to " . cloud_dest,
    flows=0, "NO CONNECTIVITY to " . cloud_dest . " via IPv6")
| sort cloud_dest
```

## Visualization

(1) Table: cloud provider IPv6 connectivity status. (2) Latency comparison: IPv6 vs IPv4 to each cloud. (3) Traffic volume to cloud by protocol version.

## Known False Positives

**IPv4-only cloud services.** Some cloud services are still IPv4-only. Zero IPv6 flows to those services is expected.

**Cloud prefix changes.** Cloud providers occasionally update their IP ranges. Update the lookup periodically.

## References

- [AWS — IPv6 support in VPC](https://docs.aws.amazon.com/vpc/latest/userguide/how-it-works.html#vpc-ip-addressing)
- [Azure — IPv6 for Azure Virtual Network](https://docs.microsoft.com/en-us/azure/virtual-network/ipv6-overview)
- [GCP — IPv6 support](https://cloud.google.com/vpc/docs/using-ipv6)
