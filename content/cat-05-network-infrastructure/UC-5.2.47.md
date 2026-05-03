<!-- AUTO-GENERATED from UC-5.2.47.json — DO NOT EDIT -->

---
id: "5.2.47"
title: "Check Point ClusterXL Failover Events (Check Point)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.47 · Check Point ClusterXL Failover Events (Check Point)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We catch high-availability handovers on Check Point so you can tell a drill or link issue from a silent split that could leave you exposed.*

---

## Description

ClusterXL provides gateway high availability via active-standby or active-active clusters. Failover events — whether planned (manual switchover) or unplanned (process crash, NIC failure, sync timeout) — cause brief traffic interruption and may indicate underlying hardware or software instability. Monitoring failover frequency, duration, and trigger reason supports SLA reporting and proactive hardware replacement before repeated failovers degrade user experience.

## Value

NOC teams track Check Point ClusterXL failover events and recovery times, detecting member failures and cluster flapping to maintain firewall high availability.

## Implementation

Forward Check Point system/cluster logs via Log Exporter or Smart-1 Cloud. Extract ClusterXL state change messages (member down, sync lost, failover). Alert on any unplanned failover immediately. Track failover frequency per cluster — more than 2 in 7 days warrants investigation. Correlate with gateway CPU/memory UC-10.11.35 to find resource-triggered failovers. Page on-call for active-active cluster degradation to single member.

## Detailed Implementation

### Prerequisites
* Check Point ClusterXL failover event logs. Data in `index=checkpoint` or `index=firewall` with `sourcetype=cp_log`. The Check Point TA for Splunk provides field extraction. Key fields: `product` (System Monitor, ClusterXL), `action`, `origin`, `cluster_member`, `failover_reason`, `description`.
* ClusterXL: Check Point's clustering technology. Modes include High Availability (active/standby), Load Sharing Multicast, and Load Sharing Unicast. Failover triggers: member down, interface failure, CCP (Cluster Control Protocol) heartbeat loss, manual failover, fwha_delta sync failure. CLI: `cphaprob state`, `cphaprob stat`.

### Step 1 — - Configure data collection
```
# Check Point SmartConsole -- configure log forwarding to Splunk
# Manage & Settings > Logs & Masters > Log Servers
# Add Splunk as OPSEC LEA or use Log Exporter
# Log Exporter:
cp_log_export add name splunk_export target-server <splunk-ip> target-port 514 protocol udp format syslog
cp_log_export set name splunk_export read-mode semi-unified
cp_log_export restart name splunk_export
```
Verify:
```spl
index=checkpoint sourcetype="cp_log" earliest=-30d
| where match(product, "(?i)ClusterXL|System Monitor") AND match(_raw, "(?i)failover|cluster|member.*down|member.*up|switchover")
| stats count by origin, description
| sort -count
```

### Step 2 — - Create the search and alert

**Primary search -- ClusterXL failover event tracking:**
```spl
index=checkpoint sourcetype="cp_log" earliest=-30d
| where match(product, "(?i)ClusterXL|System Monitor") OR match(_raw, "(?i)failover|cluster.*state|member.*state")
| eval member=coalesce(cluster_member, origin, src)
| eval failover_action=case(
    match(description, "(?i)member.*down|state.*down|dead"), "MEMBER_DOWN",
    match(description, "(?i)member.*up|state.*active|alive"), "MEMBER_UP",
    match(description, "(?i)failover|switchover|takeover"), "FAILOVER",
    match(description, "(?i)sync|delta|full.sync"), "SYNC_EVENT",
    1==1, "STATUS_CHANGE")
| eval reason=coalesce(failover_reason, if(match(description, "(?i)interface"), "interface_failure", if(match(description, "(?i)heartbeat|ccp"), "heartbeat_loss", if(match(description, "(?i)manual"), "manual", "unknown"))))
| sort member, _time
| streamstats current=f last(_time) as prev_time last(failover_action) as prev_action by member
| eval recovery_min=if(failover_action="MEMBER_UP" AND prev_action="MEMBER_DOWN", round((_time - prev_time)/60, 1), null())
| stats count(eval(failover_action="FAILOVER")) as failovers count(eval(failover_action="MEMBER_DOWN")) as member_downs avg(recovery_min) as avg_recovery_min latest(failover_action) as current_state by member, reason
| eval avg_recovery_min=round(avg_recovery_min, 1)
| eval severity=case(
    current_state="MEMBER_DOWN", "CRITICAL -- cluster member currently down",
    failovers > 3, "WARNING -- frequent failovers (possible flapping)",
    member_downs > 0, "WARNING -- member down events detected",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) CLI (expert mode): `cphaprob state` -- show current cluster state per member.
(b) CLI: `cphaprob -a if` -- show cluster interface status.
(c) CLI: `fw ctl pstat` -- check sync status and delta counters.

### Step 4 — - Operationalize
Dashboard ("Check Point -- ClusterXL Health"):
* Row 1 -- Single-value: "Failover events (30d)", "Members DOWN", "Avg recovery (min)".
* Row 2 -- Cluster failover timeline.
* Row 3 -- Failover reason distribution.

Alert: Critical (cluster member DOWN): immediate investigation.

### Step 5 — - Troubleshooting

* **CCP heartbeat failure** -- Check cluster network connectivity (usually dedicated sync interface). Verify CCP protocol mode matches on both members: `cphaprob mcast` or `cphaconf set_ccp broadcast`.

* **Sync failure after failover** -- Run `fw ctl pstat` to check full sync status. If delta sync fails, a full sync may be needed: `cphaprob syncstat`. Large connection tables can delay sync.

* **Split-brain** -- Both members active simultaneously. Usually caused by all sync interfaces failing. Emergency: manually stop one member with `cphaprob -d -s problem -t 0` or `cphastop`.

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-30d
| where match(lower(product),"(?i)cluster|clusterxl|ha") OR match(lower(logdesc),"(?i)failover|switchover|member.*down|sync.*fail")
| eval gw=coalesce(orig, src, hostname)
| stats count earliest(_time) as first latest(_time) as last values(logdesc) as events by gw
| sort -count
```

## Visualization

Timeline (failover events), Table (clusters with recent failovers), Single value (failovers this week), Bar chart (failovers by reason).

## Known False Positives

Rehearsals, code upgrades, and link work can make cluster state logs busy without customer impact.

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
