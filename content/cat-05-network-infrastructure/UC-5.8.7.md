<!-- AUTO-GENERATED from UC-5.8.7.json — DO NOT EDIT -->

---
id: "5.8.7"
title: "Network Configuration Drift Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.7 · Network Configuration Drift Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Configuration &middot; **Wave:** Crawl

*We spot when a device's settings drift from what we expect, so surprise changes do not sit there quietly until they cause an outage.*

---

## Description

Detects configuration drift by analysing diffs between device running-configs and golden templates, identifying devices with the most configuration changes for investigation.

## Value

Network operations teams detect unauthorized configuration changes by correlating actual device config modifications against the approved change calendar, identifying drift, unauthorized changes, and out-of-window modifications.

## Implementation

Deploy RANCID or Oxidized to periodically pull running-configs from network devices. Configure diff output to be ingested into Splunk via file monitor or HEC. The diff results include device name and line change counts. Alert when changes occur outside approved change windows.

## Detailed Implementation

### Prerequisites
- Configuration management tool (RANCID, Oxidized, Catalyst Center, or custom) stores device running configurations and forwards change events to Splunk. Data in `index=network_config` with `sourcetype=device:config` (full configs) and/or `sourcetype=config:change` (change events).
- Key fields: `hostname`, `config_hash`, `change_type` (add/delete/modify), `changed_section` (interface, routing, acl, snmp), `changed_by` (user who made the change, if available from AAA logs), `config_diff` (unified diff output).
- Build `approved_changes.csv` lookup: `change_id,hostname,change_window_start,change_window_end,approver,description` from your change management system (ServiceNow, Jira). This enables detection of unauthorized changes (changes outside approved windows).
- AAA logs (TACACS+/RADIUS) from `index=network sourcetype=cisco:ios` provide the `changed_by` context — who logged into the device and when.

### Step 1 — Configure data collection
Verify configuration change events:
```spl
index=network_config (sourcetype="config:change" OR sourcetype="device:config") earliest=-7d
| stats count by sourcetype, hostname
```

### Step 2 — Create the search and alert

**Primary search — Configuration drift detection (unauthorized changes):**
```spl
index=network_config sourcetype="config:change" earliest=-24h
| lookup approved_changes.csv hostname OUTPUT change_window_start change_window_end approver change_id
| eval change_epoch=_time
| eval window_start_epoch=if(isnotnull(change_window_start), strptime(change_window_start, "%Y-%m-%dT%H:%M:%S"), null())
| eval window_end_epoch=if(isnotnull(change_window_end), strptime(change_window_end, "%Y-%m-%dT%H:%M:%S"), null())
| eval in_window=if(isnotnull(window_start_epoch) AND change_epoch >= window_start_epoch AND change_epoch <= window_end_epoch, "YES", "NO")
| eval change_status=case(in_window="YES", "APPROVED", isnotnull(change_id) AND in_window="NO", "OUTSIDE_WINDOW", 1==1, "UNAUTHORIZED")
| where change_status!="APPROVED"
| table _time, hostname, changed_section, change_type, change_status, change_id
| sort change_status, -_time
```

#### Understanding this SPL: Configuration drift is one of the top causes of network outages. An engineer makes a "quick fix" at 2 AM without a change ticket, and the next morning, routing is broken. This search correlates actual configuration changes against the approved change calendar. "UNAUTHORIZED" means no change ticket exists at all; "OUTSIDE_WINDOW" means a ticket exists but the change happened outside the approved time.

**Configuration diff summary:**
```spl
index=network_config sourcetype="config:change" earliest=-24h
| stats count as changes dc(changed_section) as sections_changed values(changed_section) as sections by hostname
| sort -changes
```

**Change activity correlated with AAA logins:**
```spl
index=network_config sourcetype="config:change" earliest=-24h
| join hostname, _time type=left [search index=network sourcetype="cisco:ios" "config" OR "configure" earliest=-24h | eval changed_by=user | table hostname, _time, changed_by]
| table _time, hostname, changed_section, change_type, changed_by
| sort -_time
```

### Step 3 — Validate
(a) Make a test configuration change on a lab device (e.g., add a description to an interface) and verify the change appears in Splunk.
(b) Cross-check against the change management system: verify that approved changes show as "APPROVED" and test changes without tickets show as "UNAUTHORIZED".
(c) Verify the diff output captures the actual change accurately.

### Step 4 — Operationalize
Dashboard ("Configuration Drift Detection"):
- Row 1 — Single-value tiles: "Changes (24h)", "Unauthorized changes", "Outside-window changes", "Devices changed".
- Row 2 — Unauthorized change alert table: time, device, section, type, status.
- Row 3 — Change activity by device and section.
- Row 4 — Change timeline correlated with AAA login events.

Alerting:
- Critical (unauthorized change on Tier1 device): immediate review required.
- High (change outside approved window): validate with change owner.
- Warning (high change volume on single device > 10 changes/hour): possible configuration loop or automation issue.

### Step 5 — Troubleshooting

- **Config changes detected but no AAA login correlation** — The device may not be sending AAA logs to Splunk, or the user logged in via console (no TACACS/RADIUS). Enable AAA logging on all devices: `aaa accounting commands 15 default start-stop group tacacs+`.

- **Change detection misses some changes** — The polling interval of the config backup tool determines detection latency. If RANCID polls every 4 hours, a change made and reverted between polls is invisible. Increase polling frequency for critical devices.

- **False config drift from NTP/timestamp changes** — Normalize configurations before comparison: strip lines containing timestamps, clocks, and uptime counters.

## SPL

```spl
index=network sourcetype="config:diff"
| rex "device=(?<device>\S+).*?lines_changed=(?<changes>\d+)"
| where changes > 0
| stats sum(changes) as total_changes, count as change_events by device
| sort -total_changes
```

## Visualization

Table (device, total_changes, change_events), Timeline of change events over 30 days, Single value (devices with drift count).

## Known False Positives

Authorized template pushes, golden-config refreshes, and RANCID noise can all move diff counts; require change-ticket match before treating as incident.

## References

- [Oxidized — Network Device Configuration Backup](https://github.com/ytti/oxidized)
- [Splunk Lantern — Configuration Management](https://lantern.splunk.com/)
