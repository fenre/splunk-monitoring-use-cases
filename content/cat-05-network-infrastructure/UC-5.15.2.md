<!-- AUTO-GENERATED from UC-5.15.2.json — DO NOT EDIT -->

---
id: "5.15.2"
title: "Infoblox DHCP Scope Utilization Trending Toward Exhaustion (Infoblox)"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.15.2 · Infoblox DHCP Scope Utilization Trending Toward Exhaustion (Infoblox)

## Description

Scopes that quietly fill during BYOD spikes, IoT rollouts, or VLAN migrations cause outages that look like 'random Wi-Fi failures.' Trending utilization from DHCP traffic catches exhaustion before clients fail to obtain addresses.

## Value

Network operations can expand pools, shorten lease times, or segment traffic proactively instead of reacting to ticket storms.

## Implementation

Ensure DHCP service logs include scope/network identifiers. Build a daily summary of distinct active leases per scope; join scope size from a CMDB-exported lookup. Alert when trailing-seven-day max utilization exceeds 85% or week-over-week growth exceeds 20%.

## Detailed Implementation

Prerequisites
• Ingest `infoblox:dhcp` into `index=dhcp` (or your standard) and maintain `infoblox_scopes.csv` with `scope_id`, `pool_size`, and `network`.
• Confirm DHCPACK or lease events include a scope or network key your `rex` can read.

Step 1 — Configure data collection
Forward member logs; align lease timers with your reporting window. Refresh the scope size lookup when subnets change in IPAM.

Step 2 — Create the search and alert
```spl
index=dhcp sourcetype="infoblox:dhcp" earliest=-7d@d latest=now
| where match(_raw,"(?i)DHCPACK|lease.*granted")
| rex field=_raw "(?i)scope[\s:=]+(?<scope_id>[^,\s]+)"
| stats dc(mac) as active_leases by scope_id, host
| lookup infoblox_scopes.csv scope_id OUTPUT pool_size network
| eval util_pct=if(isnotnull(pool_size) AND pool_size>0, round(100*active_leases/pool_size,1), null())
| where util_pct>=85 OR active_leases>=500
| sort - util_pct
```

Understanding this SPL
We estimate distinct clients per scope and compare to your pool size from the lookup, then call out pools near exhaustion.

Step 3 — Validate
In Grid Manager, open DHCP smart folders or the lease viewer for a scope you flagged and compare active lease counts to `active_leases` in the search. Reconcile `pool_size` in your lookup with the real range size in the GUI so utilization math matches operations.

Step 4 — Operationalize
Schedule the search daily; page when utilization is above 85% or absolute lease counts exceed your design.

Step 5 — Troubleshooting
If `util_pct` is null, the lookup is missing a scope. If counts look high, confirm duplicate MACs and relay vs local DHCP are not double-counting.

## SPL

```spl
index=dhcp sourcetype="infoblox:dhcp" earliest=-7d@d latest=now
| where match(_raw,"(?i)DHCPACK|lease.*granted")
| rex field=_raw "(?i)scope[\s:=]+(?<scope_id>[^,\s]+)"
| stats dc(mac) as active_leases by scope_id, host
| lookup infoblox_scopes.csv scope_id OUTPUT pool_size network
| eval util_pct=if(isnotnull(pool_size) AND pool_size>0, round(100*active_leases/pool_size,1), null())
| where util_pct>=85 OR active_leases>=500
| sort - util_pct
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.DHCP
  by DHCP.dhcp_server DHCP.network span=1d
| where count>0
| sort -count
```

## Visualization

Timechart (utilization % per scope), single-value (worst scope), table (scope, leases in use, free, trend).

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
