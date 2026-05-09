<!-- AUTO-GENERATED from UC-5.6.19.json — DO NOT EDIT -->

---
id: "5.6.19"
title: "BlueCat DHCP Lease Utilization and Scope Health"
status: "community"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.19 · BlueCat DHCP Lease Utilization and Scope Health

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Availability &middot; **Wave:** Crawl &middot; **Status:** Community

*We track how full each pool of network addresses is. When the pool runs out, devices in that part of the building cannot get on the network at all. We alert long before the pool fills up so the team can expand it without anyone losing connectivity.*

---

## Description

Reports per-scope DHCP behaviour by counting successful ACKs vs failed NAKs and tracking the unique-client churn that drives lease-pool consumption. Flags scopes whose failure rate exceeds 5% (typically misconfigured policy or pool starvation) or whose ACK count is anomalously low (silent broadcast-domain failure).

## Value

DHCP scope exhaustion is a silent campus-wide outage waiting to happen. When a corporate VLAN runs out of leases, every device that comes online — laptops resuming from sleep, IoT sensors after a power cycle — fails to get an address and silently loses connectivity. BlueCat does not publish utilisation as a syslog event by default; it must be derived from lease churn or polled from BAM. This UC closes that visibility gap and lets capacity planning see the curve climbing weeks before the cliff.

## Implementation

Configure BlueCat BDDS to forward DHCP logs to Splunk via syslog. Poll BlueCat Address Manager API for scope utilisation data on a 15-minute schedule. Alert when any scope exceeds 85% utilisation, when the ACK count for a scope drops below the historical floor, or when the failure rate climbs above 5%.

## SPL

```spl
index=dhcp sourcetype="bluecat:dhcp"
| stats count(eval(action="DHCPACK")) as acks, count(eval(action="DHCPNAK")) as naks, dc(client_mac) as unique_clients by scope
| eval failure_rate=round(naks/(acks+naks)*100,2)
| where failure_rate > 5 OR acks < 10
| sort - failure_rate
```

## Visualization

Gauge (worst scope utilisation %), Table (scope health by network), Line chart (lease churn over time, per scope), Heatmap (utilisation across the entire scope inventory).

## Known False Positives

**Mass authentication failures masquerading as DHCP NAKs.** When 802.1X authentication fails for a VLAN, clients may DHCPDECLINE / DHCPNAK rapidly even though the DHCP scope is healthy. Correlate with ISE/RADIUS auth-fail rates before paging.

**Client-side reservation conflicts.** Devices configured with static reservations that no longer match the scope (post-renumbering) generate persistent NAK chatter from a small set of MACs. Suppress by aggregating distinct client MACs per scope before alerting.

**End-of-day rapid-churn windows.** In office environments, the 17:00 wave of laptops sleeping then re-acquiring leases temporarily inflates `unique_clients` and depresses scope utilisation calculations. Use a rolling 4-hour median, not a 15-minute snapshot, for the headline alert.

## References

- [BlueCat DNS/DHCP Server documentation](https://docs.bluecatnetworks.com/r/DNS-DHCP-Server-Administration-Guide)
- [BlueCat Address Manager API reference](https://docs.bluecatnetworks.com/r/Address-Manager-API-Guide)
