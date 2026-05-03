<!-- AUTO-GENERATED from UC-5.8.30.json — DO NOT EDIT -->

---
id: "5.8.30"
title: "Infoblox Grid Member DNS Service Restarts and Critical Audit Events"
status: "draft"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.8.30 · Infoblox Grid Member DNS Service Restarts and Critical Audit Events

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Audit &middot; **Status:** Draft

*We help you know when a DNS service on the grid restarts or throws serious audit events, so core name resolution is not left blind.*

---

## Description

Unexpected DNS service restarts or member-level failures on the Infoblox Grid often precede partial outages or indicate administrative mistakes and potential unauthorised changes. The audit sourcetype is the authoritative record for who changed what on the platform.

## Value

Infrastructure operations teams monitor Infoblox grid member DNS service restarts, HA failover events, and critical audit actions (zone deletions, permission changes, login failures) to ensure DNS infrastructure stability and security compliance.

## Implementation

Enable comprehensive audit logging on Grid Manager and forward to Splunk. Refine the keyword search to match your NIOS audit message vocabulary. Require change tickets for matched events during business hours; after hours, route to on-call DNS and security.

## Detailed Implementation

### Prerequisites
- Splunk Add-on for Infoblox (Splunk_TA_infoblox, Splunkbase 2934) installed. Infoblox NIOS audit logs forwarded to Splunk via syslog. Data in `index=infoblox` (or `index=dns`) with `sourcetype=infoblox:audit`. Key fields: `admin_name`, `action`, `object_type`, `object_name`, `result` (success/failure), `source_ip`.
- Infoblox Grid audit logs capture: (1) grid member service restarts (DNS, DHCP, NTP), (2) configuration changes (zone additions, record modifications), (3) admin logins and logouts, (4) grid upgrade events, (5) HA failover events.
- A DNS service restart on an Infoblox grid member causes a brief service interruption (typically 5-30 seconds). During this time, queries to that member fail or are delayed. Frequent restarts indicate instability — configuration issues, memory problems, or software bugs.
- Build `infoblox_grid_members.csv` lookup: `member_hostname,member_ip,role,datacenter,ha_pair` (e.g., `ns1.corp.com,10.1.1.1,primary,DC-East,ns2.corp.com`).

### Step 1 — Configure data collection
Verify audit log data:
```spl
index=infoblox sourcetype="infoblox:audit" earliest=-7d
| stats count by action, object_type
| sort -count
```

### Step 2 — Create the search and alert

**Primary search — DNS service restart events:**
```spl
index=infoblox sourcetype="infoblox:audit" earliest=-7d
| where match(action, "(?i)(restart|start|stop)") AND match(object_type, "(?i)(dns|named|service)")
| lookup infoblox_grid_members.csv member_hostname as host OUTPUT role datacenter ha_pair
| eval restart_type=case(match(action, "(?i)restart"), "RESTART", match(action, "(?i)stop"), "STOP", match(action, "(?i)start"), "START", 1==1, action)
| stats count as events earliest(_time) as first_event latest(_time) as last_event values(restart_type) as types by host, role, datacenter
| eval duration_hours=round((last_event - first_event)/3600, 1)
| eval frequency=if(duration_hours > 0, round(events/duration_hours, 1), events)
| eval severity=case(events > 10, "CRITICAL", events > 5, "HIGH", events > 2, "MEDIUM", 1==1, "INFO")
| sort severity, -events
```

#### Understanding this SPL: A single planned DNS restart is normal (after config changes). Multiple unplanned restarts indicate a problem: Infoblox Out-of-Memory (OOM) kills the named process and restarts it, a configuration error causes named to crash on startup, or a runaway query load triggers a watchdog restart. The `frequency` metric (restarts per hour) helps distinguish a single maintenance event from ongoing instability.

**Critical audit events (security and operational):**
```spl
index=infoblox sourcetype="infoblox:audit" earliest=-24h
| where match(action, "(?i)(delete|modify|failover|upgrade|login.fail|permission)")
| eval event_category=case(match(action, "(?i)failover"), "HA_FAILOVER", match(action, "(?i)delete"), "DELETION", match(action, "(?i)login.fail"), "AUTH_FAILURE", match(action, "(?i)upgrade"), "UPGRADE", match(action, "(?i)permission"), "PERMISSION_CHANGE", 1==1, "MODIFICATION")
| eval severity=case(event_category IN ("HA_FAILOVER", "AUTH_FAILURE"), "HIGH", event_category IN ("DELETION", "PERMISSION_CHANGE"), "MEDIUM", 1==1, "INFO")
| stats count as events by event_category, severity, admin_name, host
| sort severity, -events
```

**Admin login failure tracking:**
```spl
index=infoblox sourcetype="infoblox:audit" earliest=-24h
| where match(action, "(?i)login") AND match(result, "(?i)fail")
| stats count as failures dc(source_ip) as source_ips values(source_ip) as from_ips by admin_name
| where failures > 3
| eval risk=case(failures > 20, "BRUTE_FORCE", failures > 10, "HIGH", 1==1, "MEDIUM")
| sort -failures
```

**Grid member health audit:**
```spl
index=infoblox sourcetype="infoblox:audit" earliest=-7d
| where match(action, "(?i)(restart|failover|crash|oom|memory|disk)")
| lookup infoblox_grid_members.csv member_hostname as host OUTPUT role datacenter ha_pair
| stats count as health_events values(action) as event_types by host, role, datacenter
| sort -health_events
```

### Step 3 — Validate
(a) In Infoblox Grid Manager: Administration > Logs > Audit Log. Compare events with Splunk results.
(b) Restart the DNS service on a test member: Grid > Members > select member > Restart Services > DNS. Verify the restart event appears in Splunk.
(c) Attempt a failed login to Infoblox and verify the authentication failure appears in Splunk.

### Step 4 — Operationalize
Dashboard ("Infoblox Grid Audit"):
- Row 1 — Single-value tiles: "DNS restarts (7d)", "HA failovers", "Login failures (24h)", "Critical audit events".
- Row 2 — DNS restart frequency table: member, role, datacenter, restart count, frequency, severity.
- Row 3 — Critical audit events: category, admin, host, count.
- Row 4 — Login failure tracking: admin name, failure count, source IPs, risk level.

Alerting:
- Critical (DNS service restart > 5 times in 24 hours on same member): service instability — investigate OOM, config errors, or software bugs.
- Critical (HA failover event): primary member failed — verify secondary is handling queries.
- High (> 10 login failures for same admin): possible brute force — verify account security.
- Warning (any zone deletion): verify authorization — accidental zone deletion can cause widespread DNS resolution failures.

### Step 5 — Troubleshooting

- **Audit logs not arriving** — Check Infoblox syslog configuration: Grid > Members > select member > Syslog. Verify the Splunk syslog receiver is listed. Ensure the audit log level is set to capture the desired events.

- **Frequent DNS restarts with OOM** — The Infoblox member may need more memory for DNS cache. Check the member's resource allocation (Grid > Members > select member > Resource Allocation). Consider increasing the DNS process memory limit or reducing the cache TTL.

- **HA failover events without obvious cause** — Check the HA pair connectivity: Grid > Members > HA Status. Intermittent failovers may be caused by network issues between HA peers (latency, packet loss on the HA VLAN) or resource exhaustion on the primary (CPU, memory).

## SPL

```spl
index=dns sourcetype="infoblox:audit" earliest=-24h
| search restart OR stopped OR failed OR "Named" OR "DNS Service" OR critical
| stats count values(action) as actions latest(_time) as last by host, admin, object
| where count>=1
| sort -last
```

## Visualization

Timeline (audit spikes), Table (admin, object, actions), Notable list for unplanned restarts.

## Known False Positives

Planned restarts, upgrades, and grid join operations can restart member services; tag maintenance windows in your alert logic.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
