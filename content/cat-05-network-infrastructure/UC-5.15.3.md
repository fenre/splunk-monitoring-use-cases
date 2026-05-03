<!-- AUTO-GENERATED from UC-5.15.3.json — DO NOT EDIT -->

---
id: "5.15.3"
title: "Infoblox Grid Replication Lag and Member Sync Status (Infoblox)"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-5.15.3 · Infoblox Grid Replication Lag and Member Sync Status (Infoblox)

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Configuration &middot; **Status:** Verified

*We warn you when Infoblox grid members are not in step, so the same DNS and DHCP answers show up in every place that matters.*

---

## Description

When Grid replication falls behind, DNS and DHCP views diverge between members—leading to intermittent resolution failures or stale RPZ data. Audit events are often the earliest observable signal before user impact.

## Value

DNS architects detect split-brain or lagging members quickly, schedule controlled Grid restarts, and avoid prolonged inconsistency across sites.

## Implementation

Forward all Grid and member audit categories. Create correlation searches for keywords such as replication, serial mismatch, disconnected member, or database join failure. Track event rate per member pair and alert on absence of healthy heartbeat logs.

## Detailed Implementation

### Prerequisites
- Splunk Add-on for Infoblox (`Splunk_TA_infoblox`, Splunkbase 2934) v2.2+ installed on Search Heads and on the syslog receiver (SC4S or Heavy Forwarder).
- Infoblox NIOS 8.4+ Grid deployment with at least one Grid Master and one or more Grid Members. Understand your Grid topology: which members are HA pairs, which are remote sites with WAN links, and which serve as Grid Master Candidates (GMC). Replication lag is most common on members connected over high-latency or bandwidth-constrained WAN links.
- Audit logging enabled: Grid > Grid Properties > Monitoring > Syslog > enable the "Audit" logging category. This produces `infoblox:audit` events for Grid operations including member join/leave, database replication status, configuration pushes, and administrative changes. Also enable the "Grid" or "System" category if available in your NIOS version, as replication-specific events may be categorized there.
- Syslog from the Grid Master (and ideally all Grid Members) must reach Splunk. SC4S maps `infoblox_nios_audit` to `sourcetype=infoblox:audit` into `index=netops` by default. The Grid Master generates the most replication-related events since it coordinates database sync; members generate events when they detect they are out of sync.
- NTP synchronization: all Grid Members and the Grid Master must use NTP. Time skew between members causes false replication lag signals in logs — a member reporting 5 minutes behind schedule may actually be on time if its clock is 5 minutes off. Verify NTP under Grid > Grid Properties > NTP.
- Splunk role: users need access to the `netops` (or `dns`) index where audit events are stored.
- Baseline knowledge: understand the normal replication cadence for your Grid. NIOS uses a proprietary database replication mechanism — the Grid Master pushes configuration changes to members, and members pull zone data. Normal sync time is seconds to low minutes for small changes; large zone transfers (100K+ records) can take several minutes. Know your largest zones and typical push frequency.

### Step 1 — Configure data collection
On the Grid Master, ensure Audit logging is enabled and syslog destination is configured. Navigate to Grid > Grid Properties > Monitoring > Syslog. Add the Splunk receiver as a destination if not already present. Set severity to "Informational" or higher to capture replication status messages (Warning-only will miss normal sync confirmations that establish baselines).

Verify data is arriving:
```spl
index=netops sourcetype="infoblox:audit" earliest=-4h
| stats count by host
```
You should see the Grid Master hostname/IP and ideally all Grid Members. If only the Grid Master appears, check syslog configuration on individual members.

Verify replication-relevant events exist:
```spl
index=netops sourcetype="infoblox:audit" earliest=-24h
| search replication OR "database" OR "sync" OR "serial" OR "out of sync" OR "disconnected" OR "joined" OR "member" OR "grid"
| stats count by host
```
If this returns zero, your Grid may be healthy (no replication issues in 24h), or the syslog severity filter is too restrictive. Lower the severity threshold and re-check, or trigger a test by making a configuration change on the Grid Master and verifying the push propagation generates an audit event.

Expected event volume: audit logging generates approximately 1–5 events/minute under normal operations (configuration changes, admin logins). During Grid upgrades or large zone transfers, burst volume can reach hundreds of events/minute.

### Step 2 — Create the search and alert

**Primary search — Replication status by member (real-time health):**
```spl
index=netops sourcetype="infoblox:audit" earliest=-4h
| search replication OR "grid" OR "database" OR "serial" OR "out of sync" OR "disconnected" OR "member" OR "join" OR "sync"
| rex field=_raw "(?i)member[\s:=]+(?<member>[^\s,;]+)"
| rex field=_raw "(?i)(?:serial|sequence)[\s:=]+(?<serial_number>\d+)"
| eval severity=case(match(_raw, "(?i)disconnect|fail|error|out of sync|split"), "critical", match(_raw, "(?i)lag|behind|slow|warn"), "warning", 1==1, "info")
| stats count latest(_time) as last_event values(severity) as severities values(_raw) as sample_messages by member, host
| eval status=if(mvfind(severities, "critical") >= 0, "CRITICAL", if(mvfind(severities, "warning") >= 0, "WARNING", "OK"))
| sort -status, -last_event
```

#### Understanding this SPL: We search for all replication-related keywords in audit events, then extract the member hostname and any serial/sequence numbers mentioned. The `severity` eval classifies each event based on keyword analysis — disconnections and failures are critical, lag warnings are warning-level, and normal sync messages are informational. The `stats` command groups by member to show the overall status of each member's replication health. This gives operators a single table showing which members are healthy and which are lagging or disconnected.

**Member silence detection — missing heartbeat (negative alert):**
```spl
| inputlookup infoblox_grid_members.csv
| eval expected_member=member_fqdn
| join type=left expected_member
    [search index=netops sourcetype="infoblox:audit" earliest=-4h
    | rex field=_raw "(?i)member[\s:=]+(?<expected_member>[^\s,;]+)"
    | stats latest(_time) as last_seen count as event_count by expected_member]
| eval hours_silent=round((now()-last_seen)/3600, 1)
| where isnull(last_seen) OR hours_silent > 4
| table expected_member, last_seen, hours_silent, event_count
```

#### Understanding this SPL: This is a negative alert — it fires when a member *stops* appearing in audit logs. A Grid Member that generates zero audit events for 4+ hours may have lost network connectivity, crashed, or been removed from the Grid. We join a lookup of known members against recent events to find silent members. This catches scenarios the keyword-based search misses: if a member is completely offline, there are no replication error messages to find.

**Split-brain detection — divergent serial numbers:**
```spl
index=netops sourcetype="infoblox:audit" earliest=-1h
| search serial OR sequence OR "zone transfer" OR "AXFR" OR "IXFR"
| rex field=_raw "(?i)(?:serial|sequence)[\s:=]+(?<serial_number>\d+)"
| rex field=_raw "(?i)(?:zone|domain)[\s:=]+(?<zone_name>[^\s,;]+)"
| where isnotnull(serial_number)
| stats values(serial_number) as serials dc(serial_number) as serial_count by zone_name, host
| where serial_count > 1
| eval split_brain_risk="INVESTIGATE: multiple serial numbers for same zone on same member"
```

#### Understanding this SPL: In a healthy Grid, all members should converge on the same serial number for a given zone within minutes of a change. If a single member reports multiple serial numbers for the same zone in a 1-hour window, it may be oscillating or experiencing split-brain. This is a rare but serious condition that requires immediate investigation.

**Grid change push tracking — who changed what and did it propagate:**
```spl
index=netops sourcetype="infoblox:audit" earliest=-24h
| search "push" OR "configuration" OR "update" OR "modify" OR "add" OR "delete"
| rex field=_raw "(?i)user[\s:=]+(?<admin_user>[^\s,;]+)"
| rex field=_raw "(?i)(?:object|record|type)[\s:=]+(?<object_type>[^\s,;]+)"
| stats count values(object_type) as changed_objects latest(_time) as last_change by admin_user, host
| sort -last_change
```

#### Understanding this SPL: Complements the replication searches by showing *what* was changed and by whom. If replication lag coincides with a large batch of changes from a specific admin, the cause is likely a large configuration push overwhelming the replication queue.

Schedule as Alert:
- Primary replication status: every 15 minutes, trigger when any member shows `status=CRITICAL`. Throttle by `member` for 2 hours.
- Member silence detection: every 4 hours, trigger when results > 0. No throttle — a silent member is always actionable.

### Step 3 — Validate
(a) In Grid Manager, navigate to Grid > Grid Manager > Members tab. Each member shows a status indicator (green = connected, red = disconnected, yellow = issues). Compare this to the Splunk replication status table. Any member showing yellow/red in the GUI should appear with WARNING/CRITICAL status in Splunk.

(b) Trigger a test replication event: make a minor DNS record change on the Grid Master (add a test TXT record), then verify within 2–5 minutes that audit events appear in Splunk showing the change propagation. Check that the member's serial number increments.

(c) Verify member hostname extraction: the `rex` for `member` must match your NIOS log format. Run `| head 10 | table _raw` on replication events and confirm the regex captures the correct FQDN or IP. Adjust the regex if NIOS uses a different format (e.g. `Member: ib-member1.example.com` vs `member=10.0.1.5`).

(d) Build the `infoblox_grid_members.csv` lookup: export the list of all Grid Members from Grid Manager > Grid > Members. Include columns: `member_fqdn`, `site`, `role` (Master, Member, GMC). This lookup is required for the silence detection search.

(e) Validate NTP: run `show ntp` on 2–3 Grid Members via SSH/console. If any member is more than 5 seconds off from the Grid Master, fix NTP before relying on timestamp-based replication analysis.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Infoblox Grid — Replication Health"):
- Row 1 — Single-value tiles: "Grid Members total", "Members in sync" (green), "Members with warnings" (yellow), "Members disconnected/critical" (red), "Silent members (no events 4h+)" (red if ≥1).
- Row 2 — Table: member FQDN, status (color-coded), last event time, event count (4h), sample message. Drilldown: click a member to see all audit events for that member in the last 24h.
- Row 3 — Timeline: `| timechart span=15m count by member` showing audit event rate per member. A member whose event rate drops to zero is becoming silent. Overlay critical events as annotations.
- Row 4 — Change push log from the tracking search, showing who made changes and what was modified in the last 24h.

Alerting:
- Critical: member disconnected or split-brain detected → page DNS/DHCP infrastructure team immediately. Include member name, last sync time, and sample error messages.
- Warning: member replication lag detected → ticket to infrastructure team with 4-hour SLA.
- Informational: member silence detected → email to infrastructure team for investigation.

Runbook (owner: DNS/DHCP Infrastructure):
1. **Member disconnected**: SSH/console to the member and run `show status`. Check network connectivity to the Grid Master (`ping`, `traceroute`). If the network path is fine, check if the NIOS service is running: `show service`. Restart with `restart services` if needed. If the member cannot rejoin, it may need to be re-provisioned — this is destructive and requires a Grid backup first.
2. **Replication lag (member behind)**: Check if a large zone transfer is in progress — lag during large transfers is normal. Check WAN link utilization between the member and Grid Master. If the link is saturated, schedule large transfers for off-peak hours. In Grid Manager, check Data Management > DNS > Zones for zone sizes.
3. **Split-brain condition**: This is critical — DNS clients querying different members may get different answers. Immediately check which member has the authoritative data (compare serial numbers with the Grid Master). If a member has stale data, force a full zone transfer from the Grid Master: Grid Manager > Members > [member] > Force Zone Transfer.
4. **Grid Master failover**: If the Grid Master itself is unreachable, a Grid Master Candidate (GMC) should automatically promote. Verify promotion in audit logs. After recovery, check that the old Grid Master re-joins as a member and does not cause split-brain.

### Step 5 — Troubleshooting

- **No replication events at all in Splunk** — Audit logging may be disabled, or the severity filter is too high. NIOS categorizes replication messages at different severity levels depending on version. Set the syslog severity to "Informational" to capture all events. Also check that the Grid Master (not just members) is sending syslog to Splunk — the Grid Master generates most replication coordination messages.

- **Too many noisy events (admin logins, routine config reads)** — The primary search uses keyword filtering (replication, grid, database, etc.) to focus on relevant events. If noise persists, build an allow-list of specific message patterns from your NIOS version. Avoid filtering by `host` alone, as replication events may be generated by any member.

- **Member hostname extraction fails** — The `rex` pattern depends on your NIOS log format. Run `| rex field=_raw "(?i)member[\s:=]+(?<member>[^\s,;]+)"` against sample events and verify. If member names don't appear in the extracted field, try alternative patterns: `"(?i)from[\s]+(?<member>[^\s,;]+)"` or `"(?i)host[\s:=]+(?<member>[^\s,;]+)"`. Some NIOS versions embed the member name in the syslog header rather than the message body — check the `host` field instead.

- **False alerts during planned Grid upgrades** — Grid software upgrades (NIOS version updates) involve sequential member restarts and temporary disconnections. Maintain an `infoblox_maintenance_windows.csv` lookup with start/end times for planned upgrades and exclude those windows from alerting: `| lookup infoblox_maintenance_windows.csv | where NOT (now() >= start_time AND now() <= end_time)`.

- **Silence detection fires for members that don't generate audit events** — Some members (e.g. reporting-only or read-only members) may not produce audit events. Review and curate the `infoblox_grid_members.csv` lookup to include only members expected to generate regular audit events, or add a `monitored=true/false` column to the lookup and filter accordingly.

- **Replication events appear hours after the actual event** — Check NTP synchronization across all members and the Splunk forwarder. Also check for syslog buffering on the NIOS appliance: under Members > [member] > Monitoring > Syslog, confirm that buffering is not set to an excessive value.

## SPL

```spl
index=dns sourcetype="infoblox:audit" earliest=-4h
| search replication OR "grid" OR "database" OR "serial" OR "out of sync" OR "disconnected" OR "member"
| rex field=_raw "(?i)member[\s:]+(?<member>[^\s,]+)"
| stats count values(message) as notes latest(_time) as last by member, host
| where count>=1
| sort -last
```

## Visualization

Timeline (audit severity), table (member, last sync message, object), map (site/member status).

## Known False Positives

Planned grid upgrades, network partitions, and large zone transfers can lag replication briefly. Treat sustained or split-brain patterns as the real problem.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
- [Infoblox NIOS — Grid and replication concepts](https://docs.infoblox.com/)
