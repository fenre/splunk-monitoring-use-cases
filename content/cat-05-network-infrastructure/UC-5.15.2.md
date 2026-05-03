<!-- AUTO-GENERATED from UC-5.15.2.json — DO NOT EDIT -->

---
id: "5.15.2"
title: "Infoblox DHCP Scope Utilization Trending Toward Exhaustion (Infoblox)"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.15.2 · Infoblox DHCP Scope Utilization Trending Toward Exhaustion (Infoblox)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Capacity, Availability &middot; **Status:** Verified

*We show how full your DHCP address pools are over time so you can add space before people cannot get an address.*

---

## Description

Scopes that quietly fill during BYOD spikes, IoT rollouts, or VLAN migrations cause outages that look like 'random Wi-Fi failures.' Trending utilization from DHCP traffic catches exhaustion before clients fail to obtain addresses.

## Value

Network operations can expand pools, shorten lease times, or segment traffic proactively instead of reacting to ticket storms.

## Implementation

Ensure DHCP service logs include scope/network identifiers. Build a daily summary of distinct active leases per scope; join scope size from a CMDB-exported lookup. Alert when trailing-seven-day max utilization exceeds 85% or week-over-week growth exceeds 20%.

## Detailed Implementation

### Prerequisites
- Splunk Add-on for Infoblox (`Splunk_TA_infoblox`, Splunkbase 2934) v2.2+ installed on Search Heads and on the Heavy Forwarder or SC4S instance receiving syslog.
- Infoblox NIOS 8.4+ with DHCP services enabled on Grid Members. DHCP logging must be enabled: Grid > Grid Properties > Monitoring > Syslog > enable "DHCP Process" logging category. This produces `infoblox:dhcp` events for every DHCPDISCOVER, DHCPOFFER, DHCPREQUEST, DHCPACK, DHCPNAK, DHCPRELEASE, and DHCPDECLINE message.
- Syslog transport from each NIOS Grid Member running DHCP to your Splunk ingestion tier. SC4S maps these to `sourcetype=infoblox:dhcp` into `index=netipam` by default. If using direct Heavy Forwarder input, configure `inputs.conf` on UDP/TCP 514 with the TA's `props.conf` handling sourcetype assignment.
- A scope-size lookup table `infoblox_scopes.csv` must be created and maintained. Export from Grid Manager > Data Management > DHCP > Networks, or from the Infoblox WAPI: `GET /wapi/v2.12/network?_return_fields=network,comment,members&_max_results=10000`. The CSV needs columns: `scope_id` (the network CIDR, e.g. `10.20.30.0/24`), `pool_size` (usable addresses in that scope — for a /24 this is typically 253 minus any exclusions), `network` (human-friendly name or site label). Upload to Splunk as a lookup: Settings > Lookups > Lookup Table Files > Add New.
- License headroom: DHCP logging generates ~300 bytes per message × 4 messages per lease cycle (DISCOVER/OFFER/REQUEST/ACK). A campus with 20,000 active DHCP clients renewing every 8 hours ≈ 240K events/day ≈ 72 MB/day. Guest/BYOD environments with short lease times (30 minutes) generate significantly more.
- Baseline knowledge: know your largest scopes, typical utilization percentages, and lease durations. A /24 scope with 8-hour leases and 200 clients is at 79% — already close to the 85% threshold. Scopes with 30-minute leases show higher churn but lower peak utilization.

### Step 1 — Configure data collection
On the NIOS Grid Master, ensure DHCP Process logging is enabled for all members running DHCP services. Navigate to Grid > Grid Properties > Monitoring > Syslog and verify the "DHCP Process" category is checked.

For each DHCP-serving member, confirm syslog destination is configured under Members > [member] > Monitoring > Syslog pointing at your SC4S or Heavy Forwarder.

Verify data is arriving in Splunk:
```spl
index=dhcp sourcetype="infoblox:dhcp" earliest=-1h
| stats count by host, _raw
| head 20
```
Each `host` value should correspond to a NIOS member running DHCP. You should see DHCPACK, DHCPDISCOVER, DHCPOFFER, and DHCPREQUEST messages.

Verify the key fields the TA extracts:
```spl
index=dhcp sourcetype="infoblox:dhcp" DHCPACK earliest=-1h
| fieldsummary
| where count > 0
| table field count distinct_count
```
Expected fields include: `dest_ip` (leased IP), `src_mac` or `mac` (client MAC), `dest_nt_host` or `hostname` (client hostname if provided), `dhcp_server` or `host` (member that granted the lease). The network/scope is typically embedded in the IP address itself — you extract it by mapping the IP to its CIDR range via the lookup.

Create and populate the scope lookup:
```
| makeresults | eval scope_id="10.20.30.0/24", pool_size=240, network="Building-A-Floor-3" | outputlookup append=t infoblox_scopes.csv
```
For production, export from Grid Manager or automate via WAPI script and schedule a daily refresh with `| outputlookup`.

Expected event volume: for scope utilization tracking, we primarily need DHCPACK events. Expect approximately 1 DHCPACK per lease grant/renewal per client.

### Step 2 — Create the search and alert

**Primary search — Scope utilization overview (daily):**
```spl
index=dhcp sourcetype="infoblox:dhcp" earliest=-7d@d latest=now
| where match(_raw, "(?i)DHCPACK|lease.*granted")
| rex field=_raw "(?i)(?:on|for|ip[\s:=]+)(?<lease_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
| rex field=_raw "(?i)(?:to|mac[\s:=]+)(?<client_mac>[0-9a-fA-F]{2}(?:[:\-][0-9a-fA-F]{2}){5})"
| eval scope_id=lease_ip
| lookup infoblox_scopes.csv scope_id OUTPUT pool_size network
| stats dc(client_mac) as active_leases by scope_id, network, pool_size, host
| eval util_pct=if(isnotnull(pool_size) AND pool_size>0, round(100*active_leases/pool_size, 1), null())
| eval status=case(util_pct>=95, "CRITICAL", util_pct>=85, "WARNING", util_pct>=70, "Monitor", 1==1, "Healthy")
| where util_pct>=70 OR active_leases>=500
| sort -util_pct
```

#### Understanding this SPL: We extract the leased IP and client MAC from DHCPACK messages using `rex` against the raw event. The `dc(client_mac)` counts distinct active clients per scope over 7 days — this approximates peak concurrent utilization. We join to `infoblox_scopes.csv` to get the pool size, then calculate utilization percentage. The status classification uses 70/85/95 thresholds: 70% = monitor (capacity planning), 85% = warning (expand soon), 95% = critical (exhaustion imminent). Note: this counts distinct MACs over 7 days, so it may overcount if clients change MACs (privacy addresses) — for more precise counts, narrow the time range to the lease duration.

**Trending — week-over-week utilization growth:**
```spl
index=dhcp sourcetype="infoblox:dhcp" earliest=-14d latest=now
| where match(_raw, "(?i)DHCPACK")
| rex field=_raw "(?i)(?:on|for|ip[\s:=]+)(?<lease_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
| rex field=_raw "(?i)(?:to|mac[\s:=]+)(?<client_mac>[0-9a-fA-F]{2}(?:[:\-][0-9a-fA-F]{2}){5})"
| eval scope_id=lease_ip
| lookup infoblox_scopes.csv scope_id OUTPUT pool_size network
| bin _time span=1d
| stats dc(client_mac) as daily_leases by scope_id, network, pool_size, _time
| eval util_pct=round(100*daily_leases/pool_size, 1)
| eventstats first(util_pct) as week_ago_pct latest(util_pct) as current_pct by scope_id
| where _time >= relative_time(now(), "-1d@d")
| eval growth_pct=round(current_pct - week_ago_pct, 1)
| where growth_pct > 10
| sort -growth_pct
```

#### Understanding this SPL: We track daily distinct client counts over 14 days, then compare the most recent day to 7 days ago. Scopes growing more than 10 percentage points week-over-week are flagged — this catches IoT rollouts, BYOD spikes, or VLAN migrations that will exhaust the scope within weeks if unchecked.

**Exhaustion timeline prediction:**
```spl
index=dhcp sourcetype="infoblox:dhcp" earliest=-30d latest=now
| where match(_raw, "(?i)DHCPACK")
| rex field=_raw "(?i)(?:on|for|ip[\s:=]+)(?<lease_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
| rex field=_raw "(?i)(?:to|mac[\s:=]+)(?<client_mac>[0-9a-fA-F]{2}(?:[:\-][0-9a-fA-F]{2}){5})"
| eval scope_id=lease_ip
| lookup infoblox_scopes.csv scope_id OUTPUT pool_size network
| bin _time span=1d
| stats dc(client_mac) as daily_leases by scope_id, network, pool_size, _time
| eventstats avg(daily_leases) as avg_30d latest(daily_leases) as latest_leases by scope_id
| where _time >= relative_time(now(), "-1d@d")
| eval free_addresses=pool_size - latest_leases
| eval daily_growth=latest_leases - avg_30d
| eval days_to_exhaustion=if(daily_growth > 0, round(free_addresses / daily_growth, 0), 9999)
| where days_to_exhaustion < 90 AND days_to_exhaustion > 0
| sort days_to_exhaustion
```

#### Understanding this SPL: We project when each scope will exhaust based on the difference between the latest count and the 30-day average. `days_to_exhaustion` gives operations a concrete timeline for capacity planning. Scopes predicted to exhaust within 90 days are flagged.

Schedule as Alert: the primary utilization search runs daily at 06:00. Trigger when any scope crosses 85%. The trending search runs weekly on Monday mornings for capacity review.

### Step 3 — Validate
(a) In Grid Manager, navigate to Data Management > DHCP > Networks, click a specific network/scope, and view the "Leases" tab. Compare the number of active leases shown to the `active_leases` count in your Splunk search for that scope. Counts should align within 10% — differences arise because the Splunk count uses distinct MACs over 7 days while Grid Manager shows point-in-time active leases.

(b) Verify the `pool_size` in your lookup is accurate. For a /24 network (256 IPs), subtract the network address, broadcast address, gateway, and any DHCP exclusion ranges. A /24 with a gateway and 10 reserved IPs has pool_size = 243, not 254. Incorrect pool sizes make utilization percentages meaningless.

(c) Check for double-counting from DHCP relay agents. If your architecture uses relay agents (option 82), the same lease may be logged by both the relay member and the authoritative member. Add `| dedup client_mac, scope_id` before the stats if needed.

(d) Validate the `rex` extractions against 5 sample raw events. NIOS DHCP log format varies slightly between versions — run `| head 5 | table _raw` and confirm the IP and MAC regex captures correctly. Adjust the regex if your NIOS version uses a different format (e.g. `DHCPACK on 10.20.30.45 to 00:1a:2b:3c:4d:5e` vs `DHCPACK for 10.20.30.45 (00:1a:2b:3c:4d:5e)`).

(e) Cross-check the week-over-week trending: compare a scope that you know recently gained clients (new floor, new IoT deployment) and confirm it appears in the growth results.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Infoblox DHCP — Scope Utilization"):
- Row 1 — Single-value tiles: "Scopes above 85%" (red if ≥1), "Scopes above 70%" (yellow if ≥3), "Predicted exhaustion within 30 days" (red if ≥1), "Total active leases (fleet)".
- Row 2 — Table: scope_id, network name, active_leases, pool_size, util_pct, status (color-coded), days_to_exhaustion. Drilldown: click a scope to open a per-scope detail view showing timechart of daily lease counts over 30 days.
- Row 3 — Timechart: top 10 highest-utilization scopes over 30 days, showing daily util_pct trending. Highlight the 85% threshold as a reference line.
- Row 4 — Week-over-week growth table from the trending search, sorted by growth_pct descending.

Alerting:
- Critical (util_pct >= 95): page network operations immediately — scope will exhaust within hours/days.
- Warning (util_pct >= 85): ticket to IPAM team for scope expansion or lease time reduction.
- Capacity planning (days_to_exhaustion < 30): weekly email to network capacity planning team.

Runbook (owner: IPAM / Network Operations):
1. **Scope at 95%+ (imminent exhaustion)**: Immediately check if the scope can be expanded (add a secondary range, extend the CIDR). As a temporary measure, reduce lease time to force faster recycling — change from 8h to 2h in Grid Manager > DHCP > Networks > [scope] > Lease Time. Monitor for DHCPNAK events which indicate clients being refused.
2. **Scope at 85% (planning threshold)**: Review the scope's client population — are there stale leases from devices no longer present? In Grid Manager, check for leases with last-seen timestamps older than 2× the lease duration. Consider implementing DHCP fingerprinting to identify and segment IoT devices into a dedicated scope.
3. **Week-over-week growth > 20%**: Investigate what changed — new IoT deployment, VLAN migration, guest event. If growth is expected and sustained, proactively expand the scope before it hits 85%.
4. **Scope lookup is stale**: If the lookup hasn't been refreshed after IPAM changes, utilization percentages will be wrong. Schedule a weekly WAPI export to refresh `infoblox_scopes.csv`.

### Step 5 — Troubleshooting

- **`util_pct` is null for all scopes** — The `infoblox_scopes.csv` lookup is missing or the `scope_id` field doesn't match. The lookup key must match the format used in the search — if the search extracts `scope_id` as the leased IP (e.g. `10.20.30.45`) and the lookup has CIDR notation (e.g. `10.20.30.0/24`), they won't join. You need a `cidr()` function or a subnet lookup that maps IPs to their scope. As a workaround, use `| eval scope_id=replace(lease_ip, "\d+$", "0/24")` if all scopes are /24, or build a comprehensive CIDR-to-scope lookup.

- **Active lease counts seem too high** — If you're counting distinct MACs over 7 days but leases only last 8 hours, you'll count devices that were present any time in the week, not just concurrently. Narrow `earliest` to match your lease duration (e.g. `-8h` for 8-hour leases) for a more accurate point-in-time count.

- **No DHCPACK events in Splunk** — DHCP Process logging may not be enabled on the Grid Members, or only DHCPDISCOVER/OFFER are being logged. Verify in Grid > Grid Properties > Monitoring > Syslog that "DHCP Process" is checked. Also confirm the member's syslog destination is reachable.

- **DHCP relay agents causing duplicate counts** — If Grid Members are configured as both DHCP server and relay, the same lease transaction may be logged twice. Use `| dedup client_mac, lease_ip` before the `stats` command to eliminate duplicates.

- **Scope sizes change after IPAM modifications but lookup is stale** — Automate the lookup refresh with a scheduled Splunk search that calls the Infoblox WAPI (via a custom command or scripted input) to pull current network definitions. Alternatively, schedule a cron job on the Heavy Forwarder that exports the WAPI data to CSV and copies it to `$SPLUNK_HOME/etc/apps/search/lookups/`.

**DHCPv6 Considerations:** NIOS logs DHCPv6 with distinct message names and fields; extend `rex`, lookups, and scope keys if you track IPv6 networks or DHCPv6-PD alongside DHCPv4. DHCPv6 (RFC 8415) is a fundamentally different protocol from DHCPv4, using UDP ports 546/547. Key differences: (1) DHCPv6 does NOT provide default gateway — that comes from Router Advertisements. (2) Message types differ: Solicit/Advertise/Request/Reply instead of Discover/Offer/Request/Ack. (3) DHCPv6 Prefix Delegation (DHCPv6-PD) enables subnet allocation to downstream routers. (4) Syslog patterns differ: look for 'DHCPv6' in messages, not just 'DHCP'. For comprehensive DHCPv6 monitoring, see the IPv6 subcategory (UC-5.20.10, UC-5.20.141).

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

## Known False Positives

New sites, large guest events, and IoT surges can fill pools—pair alerts with IPAM records and real lease need before expanding blindly.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
