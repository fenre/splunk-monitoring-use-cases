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

## Visualization

Timechart (utilization % per scope), single-value (worst scope), table (scope, leases in use, free, trend).

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)

