<!-- AUTO-GENERATED from UC-5.15.5.json — DO NOT EDIT -->

---
id: "5.15.5"
title: "Infoblox DHCP Lease Rate Trending and Scope Exhaustion Forecasting (Infoblox)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.15.5 · Infoblox DHCP Lease Rate Trending and Scope Exhaustion Forecasting (Infoblox)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity, Analytics &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how quickly computers grab temporary addresses and estimate how soon the pool runs dry, so building Wi‑Fi never hits a surprise busy hour with no room left.*

---

## Description

This use case tracks how fast DHCP leases are granted per scope using sliding hourly lease rates, then forecasts how many days remain until the numeric pool is consumed if the recent growth trend continues.

## Value

Operators gain a forward-looking metric—distinct from static utilization snapshots—that captures bursty onboarding, conference Wi‑Fi, or IoT bursts so expansions are funded before DHCPNAK storms flood the service desk.

## Implementation

Normalize DHCPACK events per scope, compute rolling moving averages, join authoritative pool sizes, schedule hourly summaries, and alert when projected_fill_days falls inside your risk window (for example 14 days).

## Detailed Implementation

### Prerequisites
- `Splunk_TA_infoblox` installed and DHCP syslog flowing with DHCPACK lines retaining scope or IP address.
- Lookup table `infoblox_scopes.csv` maintained whenever subnets change.
- Familiarity with lease timers—short leases amplify ACK noise; optionally divide counts by renewal probability when tuning forecasts.

### Step 1 — Configure data collection
Verify ACK volume (`index=dhcp sourcetype="infoblox:dhcp" DHCPACK earliest=-1h | stats count`). Capture scope identifiers—some appliances embed scope name only in OFFER; if missing, map IPs to scopes via the same CIDR lookup pattern used in UC‑5.15.4.

### Step 2 — Create the search and alert
Run the primary SPL hourly. Add `predict` on daily aggregates as an alternate model (`| predict lease_rate algorithm=LLP future_timespan=7`). Alert when two consecutive runs show `projected_fill_days` below threshold.

### Step 3 — Validate
Compare projected lease velocity against Grid Manager lease histogram for a pilot subnet over 48 hours; reconcile differences caused by BOOTP relays or duplicate syslog paths.

### Step 4 — Operationalize
Dashboard panels: scope leaderboard by projected_fill_days, ribbon chart of hourly_leases, annotations for change tickets. Integrate with CMDB site codes via lookup.

### Step 5 — Troubleshooting
**Missing scope_id:** fall back to IP→CIDR lookup.**Forecast spikes:** holiday traffic may distort moving averages—use `seasonality` or weekly baselines.**IPv6:** extend logic when DHCPv6 prefixes replace IPv4 pools.

## SPL

```spl
index=dhcp sourcetype="infoblox:dhcp" earliest=-14d@d latest=now
| where match(_raw,"(?i)DHCPACK")
| rex field=_raw "(?i)(?:on|for|ip[\\s:=]+)(?<lease_ip>\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})"
| rex field=_raw "(?i)scope[\\s:=]+(?<scope_id>[^,\\s]+)"
| lookup infoblox_scopes.csv scope_id OUTPUT pool_size network
| bin _time span=1d
| stats dc(lease_ip) as daily_leases by scope_id pool_size network _time
| sort scope_id _time
| streamstats window=7 global=f avg(daily_leases) as baseline7 by scope_id
| eval daily_growth=daily_leases-baseline7
| eval free_addrs=pool_size-daily_leases
| eval projected_fill_days=if(daily_growth>0 AND free_addrs>0, round(free_addrs/daily_growth,1), null())
| where _time >= relative_time(now(), "-1d@d")
| where projected_fill_days<=45 AND projected_fill_days>0 AND pool_size>0
| sort projected_fill_days
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Network_Sessions.DHCP by DHCP.network span=1h
| where count>0
```

## Visualization

Top-N scope forecast table, hourly lease-rate timechart with reference bands, single-value alert badge for scopes under 7-day runway.

## Known False Positives

**Renewal bursts:** Heavy ACK counts during mass renewals can resemble growth—blend DISCOVER/BOUND ratios before reacting.**Lab VLAN noise:** Ephemeral labs inflate forecasts; exclude scopes tagged `environment=lab` via lookup.**Incorrect pool_size:** Wrong totals instantly skew days-to-full projections.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
