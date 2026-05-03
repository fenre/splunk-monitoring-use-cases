<!-- AUTO-GENERATED from UC-5.3.1.json — DO NOT EDIT -->

---
id: "5.3.1"
title: "Pool Member Health Status (F5 BIG-IP)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.1 · Pool Member Health Status (F5 BIG-IP)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We read pool member up and down messages from the load balancer so a drained server or a real failure is obvious before customers complain.*

---

## Description

Offline pool members reduce capacity. All members down = complete service outage.

## Value

Application delivery teams monitor F5 BIG-IP pool member availability with capacity impact analysis, detecting degraded pools, complete outages, and flapping members before user-facing service impact.

## Implementation

Forward F5 syslog (LTM log level). Install TA. Alert when pool members go down. Critical alert when all members in a pool offline.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680) installed. F5 BIG-IP LTM syslog forwarded to Splunk with `sourcetype=f5:bigip:syslog`. Key syslog messages: `MCPD` subsystem for pool member state transitions ("Pool member ... monitor status down/up"), `bigd` for health monitor results.
* F5 syslog configuration: System > Logs > Configuration > Remote Logging > add Splunk syslog IP, set severity to Informational.
* Create `f5_pool_inventory.csv` lookup: `pool`, `member`, `application`, `owner`, `tier` (prod/staging), `expected_members` (count of members that should be up).

### Step 1 — - Configure data collection
On the F5 BIG-IP, configure remote syslog:
```
tmsh modify sys syslog remote-servers add { splunk { host <SPLUNK_SYSLOG_IP> remote-port 514 } }
```
Verify data flows:
```spl
index=network sourcetype="f5:bigip:syslog" earliest=-4h
| where match(_raw, "(?i)(pool member|monitor status)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Pool member state with capacity impact:**
```spl
index=network sourcetype="f5:bigip:syslog" ("pool member" AND ("down" OR "up" OR "offline" OR "available")) earliest=-4h
| rex "Pool (?<pool>\S+) member (?<member>\S+) monitor status (?<status>\w+)"
| where isnotnull(pool)
| stats latest(status) as current_status latest(_time) as last_change by host, pool, member
| lookup f5_pool_inventory.csv pool OUTPUT application, owner, tier, expected_members
| eval is_down=if(match(lower(current_status), "down|offline"), 1, 0)
| stats sum(is_down) as down_count count as total_members values(application) as app values(tier) as tier by host, pool, expected_members
| eval up_count=total_members - down_count
| eval capacity_pct=round(100*up_count/total_members, 1)
| eval severity=case(down_count=total_members, "CRITICAL -- ALL MEMBERS DOWN", capacity_pct < 50, "HIGH -- below 50%", down_count > 0, "WARNING -- degraded", 1==1, "OK")
| where down_count > 0
| sort severity, -down_count
```

**Pool member flapping detection:**
```spl
index=network sourcetype="f5:bigip:syslog" ("pool member" AND ("down" OR "up")) earliest=-4h
| rex "Pool (?<pool>\S+) member (?<member>\S+) monitor status (?<status>\w+)"
| stats count as transitions dc(status) as states by pool, member
| where transitions > 4
| eval issue="FLAPPING -- member toggling up/down (".transitions." transitions in 4h)"
| sort -transitions
```

### Step 3 — - Validate
(a) In tmsh: `show ltm pool <pool_name> members` -- compare member states with Splunk.
(b) Force a pool member offline: `tmsh modify ltm node <node> state user-down` -- verify the event appears in Splunk within 60 seconds.
(c) Re-enable: `tmsh modify ltm node <node> state user-up` -- verify the "up" event.

### Step 4 — - Operationalize
Dashboard ("F5 -- Pool Health"):
* Row 1 -- Single-value tiles: "Pools with down members", "Total down members", "Critical pools (all down)", "Flapping members".
* Row 2 -- Pool capacity table: pool, app, tier, up/total, capacity %, severity.
* Row 3 -- Flapping member detail.

Alerting:
* Critical (all members down in any prod pool): immediate -- complete service outage.
* High (pool capacity < 50%): degraded -- remaining members may be overloaded.
* Warning (member flapping > 4 transitions in 1h): unstable backend -- investigate health monitor or server.

### Step 5 — - Troubleshooting

* **All members down but application works** -- Check if the pool has a "fallback host" or "action on service down" configured (tmsh: `list ltm pool <pool> all-properties`). Traffic may be going to a sorry page or alternate pool.

* **Member shows down but server is healthy** -- The F5 health monitor is failing. Check: (1) monitor type (HTTP, TCP, ICMP), (2) send/receive strings, (3) network path between F5 and backend. Test: `tmsh run ltm monitor <monitor> destination <member_ip:port>`.

* **Flapping member** -- The backend is intermittently failing the health check. Common causes: (1) backend at capacity (slow responses exceed monitor timeout), (2) GC pauses (JVM), (3) health endpoint returning errors under load.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=network sourcetype="f5:bigip:syslog" ("pool member" AND ("down" OR "up" OR "offline"))
| rex "Pool (?<pool>\S+) member (?<member>\S+) monitor status (?<status>\w+)"
| table _time host pool member status | sort -_time
```

## Visualization

Status grid (green/red per member), Table, Timeline.

## Known False Positives

Backend servers are often drained on purpose for deploys, capacity tests, or standby; down members are not always broken.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
