<!-- AUTO-GENERATED from UC-5.3.14.json — DO NOT EDIT -->

---
id: "5.3.14"
title: "Citrix ADC Service Group Member Health (NetScaler)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.14 · Citrix ADC Service Group Member Health (NetScaler)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We read service group health on the same platform so a cold member or a flapping monitor is visible before a whole site looks "randomly" slow.*

---

## Description

Behind each Citrix ADC vServer, service group members represent individual back-end servers. When health monitors detect a service group member as DOWN, the ADC stops sending traffic to that server. A single member going down may be routine (maintenance), but multiple simultaneous failures indicate a systemic issue — network partition, shared dependency failure, or deployment problem. Monitoring service group member health identifies back-end server failures faster than application-level monitoring.

## Value

Application delivery teams monitor Citrix ADC service group member health with capacity percentages, detecting degraded backend pools and complete backend failures before vserver-level impact.

## Implementation

The ADC logs service state transitions via syslog. For richer data, poll the NITRO API `servicegroup_servicegroupmember_binding` to enumerate all members and their states. Track `svrstate` (UP, DOWN, OUT OF SERVICE) and monitor response times. Alert when: more than 2 service group members go DOWN simultaneously (systemic issue), a critical service group drops below minimum capacity threshold, or a member remains DOWN for more than 15 minutes (stale failure). Correlate member health with application error rates for impact assessment.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC syslog and/or NITRO stats. Key fields: `service_name`, `service_state` (UP/DOWN/OUT_OF_SERVICE), `service_group`, `server_ip`, `server_port`, `health_monitor`, `response_time_ms`.
* Service group members are the backend servers. When a member goes DOWN: (1) traffic redistributes to remaining members, (2) if all DOWN, the parent vserver goes DOWN.

### Step 1 — - Configure data collection
Verify service health data:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") earliest=-4h
| where isnotnull(service_name) OR match(_raw, "(?i)(service|servicegroup|member)")
| where match(_raw, "(?i)(down|up|out.of.service)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Service group member health:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("service" AND ("DOWN" OR "UP" OR "OUT OF SERVICE" OR "going down" OR "serviceMember")) earliest=-4h
| eval svc=coalesce(service_name, servicename, member_name)
| eval state=coalesce(service_state, member_state, state)
| eval sg=coalesce(service_group, servicegroup, serviceGroupName)
| eval server=coalesce(server_ip, serverip)
| stats latest(state) as current_state latest(response_time_ms) as last_rt latest(_time) as last_change by host, sg, svc, server
| eval is_down=if(match(lower(current_state), "down|out.of.service"), 1, 0)
| stats sum(is_down) as down_members count as total_members by host, sg
| eval health_pct=round(100*(total_members - down_members)/total_members, 1)
| eval severity=case(down_members=total_members, "CRITICAL -- ALL MEMBERS DOWN", health_pct < 50, "HIGH -- below 50%", down_members > 0, "WARNING -- degraded", 1==1, "OK")
| where down_members > 0
| sort severity, -down_members
```

### Step 3 — - Validate
(a) On ADC CLI: `show servicegroup <sg>` -- compare member states.
(b) Disable a member: `disable server <server>` -- verify event appears.
(c) Check monitor: `show lb monitor <monitor>` -- verify monitor parameters match expected health check.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Service Group Health"):
* Row 1 -- Single-value: "Service groups", "Down members", "Critical groups", "Fleet health %".
* Row 2 -- Per-service-group health table.

Alerting:
* Critical (all members DOWN in any service group): complete backend failure.
* Warning (service group health < 50%): degraded capacity.

### Step 5 — - Troubleshooting

* **Member DOWN but server is healthy** -- Health monitor failing. Check: `show lb monitor bindings <monitor>`. Test manually: `curl http://<server_ip>:<port>/health`. Verify the monitor send/receive strings match the backend response.

* **Members flapping** -- Backend intermittently failing health checks. Common cause: backend at capacity returns errors under load.

* **All members DOWN after config change** -- Check if the service group binding was modified: `show servicegroup <sg>`. Verify server IPs and ports.

## SPL

```spl
index=network sourcetype="citrix:netscaler:syslog" "monitor" ("DOWN" OR "UP") "servicegroup"
| rex "servicegroup member (?<sg_name>\S+)\((?<member_ip>[^)]+)\) - State (?<state>\w+)"
| where state="DOWN"
| stats count as transitions, latest(_time) as last_seen, latest(state) as current_state by sg_name, member_ip, host
| eval last_seen_fmt=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| sort -last_seen
| table sg_name, member_ip, current_state, transitions, last_seen_fmt, host
```

## Visualization

Table (service groups with DOWN members), Bar chart (DOWN members by service group), Timeline (member state changes).

## Known False Positives

Members can be in slow-start or out of rotation by design; compare with the application owner before you panic.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
