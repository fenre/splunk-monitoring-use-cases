<!-- AUTO-GENERATED from UC-5.15.4.json — DO NOT EDIT -->

---
id: "5.15.4"
title: "Infoblox IPAM Subnet Utilization and Exhaustion Prediction (Infoblox)"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.15.4 · Infoblox IPAM Subnet Utilization and Exhaustion Prediction (Infoblox)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Capacity, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch how many addresses are really in use in each office subnet and guess how soon it fills up, so you can add space before phones and laptops stop connecting.*

---

## Description

This use case estimates how full each managed subnet is by correlating live DHCP lease activity with authoritative IPAM pool sizes, then projects runway until exhaustion using recent daily lease density rather than a single snapshot.

## Value

Capacity and IPAM teams receive early warning before guest VLANs, IoT segments, or campus scopes silently saturate, which protects revenue-critical Wi‑Fi and VoIP services from brownouts caused by address starvation.

## Implementation

Maintain `infoblox_ipam_networks.csv` from Grid/WAPI with CIDR and usable host counts; ingest DHCPACK events via the TA; schedule daily searches that compute utilization and runway; alert when utilization crosses 85% or projected days-to-full drops below 45.

## Detailed Implementation

### Prerequisites
- Splunk Add-on for Infoblox (`Splunk_TA_infoblox`, Splunkbase 2934) on search heads and ingestion tier receiving NIOS syslog.
- DHCP Process logging enabled so `sourcetype=infoblox:dhcp` includes DHCPACK lines with leased IPv4 addresses.
- An accurate `infoblox_ipam_networks.csv` lookup: columns must include `lease_ip` key or CIDR mapping strategy documented below, `pool_size` (usable IPs after reservations), and optional `site` label.
- Splunk roles granting `index=dhcp` (and `netops` if augmenting with audit).

### Step 1 — Configure data collection
Confirm DHCP events arrive (`index=dhcp sourcetype=infoblox:dhcp earliest=-1h | stats count`). Export networks from Grid Manager or automate WAPI pulls nightly into `$SPLUNK_HOME/etc/apps/search/lookups/`. If the TA extracts `dest_ip` reliably, replace the sample `rex` with that field.

### Step 2 — Create the search and alert
Use the primary SPL to trend distinct leased IPs per subnet per day. Layer a secondary alert that compares today’s `util_pct` to a 14-day median with `eventstats median(util_pct) as med by network_cidr` to catch sudden jumps. Throttle alerts per `network_cidr`.

### Step 3 — Validate
Pick one subnet in Grid Manager IPAM and compare active DHCP leases to Splunk’s `current_leases` for the same window; reconcile exclusions (statics, reservations) against `pool_size`. Spot-check runway math against manual growth estimates.

### Step 4 — Operationalize
Dashboard row 1: worst subnets single value and table of runway_days; row 2: 30-day utilization timechart per top-N subnets; row 3: site-level rollup. Tie tickets to IPAM change records when audit shows container edits (`infoblox:audit` "network" OR "container").

### Step 5 — Troubleshooting
**Lookup mismatch:** Ensure lease IPs map to CIDR keys—use `cidrmatch()` or expand parent containers if subnets nest.**Privacy MAC churn:** dedupe by MAC if counting leases.**IPv6:** extend with DHCPv6 IA_NA logs if present; IPv4-only math will under-report dual-stack demand.

## SPL

```spl
index=dhcp sourcetype="infoblox:dhcp" earliest=-30d@d latest=now
| where match(_raw,"(?i)DHCPACK")
| rex field=_raw "(?i)(?:on|for|ip[\\s:=]+)(?<lease_ip>\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})"
| rex field=_raw "(?i)(?:to|mac[\\s:=]+)(?<client_mac>[0-9a-fA-F]{2}(?:[:\\-][0-9a-fA-F]{2}){5})"
| eval scope_key=replace(lease_ip,"^(\\d+\\.\\d+\\.\\d+)\\.\\d+$","\\1.0/24")
| lookup infoblox_ipam_networks.csv network_cidr AS scope_key OUTPUT pool_size site network
| bin _time span=1d
| stats dc(client_mac) as distinct_leases by scope_key pool_size site network _time
| eventstats latest(distinct_leases) as current_leases latest(pool_size) as pool by scope_key site
| where _time >= relative_time(now(), "-1d@d")
| eval util_pct=if(isnotnull(pool) AND pool>0, round(100*current_leases/pool,1), null())
| eval free=pool-current_leases
| eval runway_days=if(current_leases>0 AND free>0, round(free/max(current_leases/30,0.01),0), null())
| where util_pct>=70 OR free<=20
| sort - util_pct
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Network_Sessions.DHCP where nodename=Network_Sessions.DHCP by DHCP.network span=1d
| where count>0
| sort -count
```

## Visualization

Single-value (subnets above 85%), timechart (daily util_pct by network_cidr), table (site, pool_size, current_leases, util_pct, runway_days), map or site breakdown panel.

## Known False Positives

**Short-term spikes:** Events or labs can temporarily raise DHCP counts without true structural growth—confirm with two consecutive days above threshold.**Mis-sized pools:** If reservations/statics are omitted from `pool_size`, utilization appears artificially high.**Relay duplication:** Multiple syslog paths for the same ACK can inflate counts until you dedup MAC/IP pairs.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
- [Infoblox NIOS documentation — IPAM networks](https://docs.infoblox.com/)
