<!-- AUTO-GENERATED from UC-5.19.2.json — DO NOT EDIT -->

---
id: "5.19.2"
title: "NETCONF Session Count and Session Leak Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.19.2 · NETCONF Session Count and Session Leak Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity, Availability, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We count how many remote control connections each switch accepts and whether opened connections get closed cleanly. If connections pile up or drop oddly, we investigate before the gear locks out new work.*

---

## Description

Splunk correlates NETCONF-related syslog streams to expose abnormal concurrent sessions, asymmetric open versus close counts, and idle-timeout bursts that often precede automation client bugs, leaked ncclient pools, or brute-force reconnaissance against the management plane.

## Value

Engineering preserves stable NETCONF capacity on routers and switches because session leaks no longer exhaust vendor session limits mid-change-window, and suspicious login churn triggers investigation before credential stuffing degrades management APIs.

## Implementation

Ensure NETCONF audit/debug logging is enabled at a governed severity; normalize timestamps to UTC; sample every fifteen minutes; whitelist bastion IPs via lookup; pair with asset ownership tags on `host`.

## Detailed Implementation

### Prerequisites
- Document per-platform NETCONF session caps (IOS-XE, IOS-XR, NX-OS, Junos) and known syslog phrases for session lifecycle.
- Confirm NTP so `_time` aligns with EMS session tables.

### Step 1 — Device logging
Enable NETCONF logging appropriate to vendor guidance (avoid verbose RPC payload logs in production); capture session establish/teardown and SSH subsystem negotiation failures.

### Step 2 — Ingest
Forward management VRF syslog through SC4S or TCP inputs; assign sourcetype via IP/subnet rules; mask secrets in `_raw` transforms.

### Step 3 — Saved search
Persist SPL as `netconf_session_leak_watch`; alert when fifteen-minute `approx_sessions` doubles rolling baseline or when `timeouts`≥3 per host.

### Step 4 — Validate
Open controlled parallel NETCONF sessions from a lab runner without closing; compare Splunk-derived counts to `show netconf-yang sessions` / Junos `show system connections` within acceptable variance.

### Step 5 — Operationalize
Dashboard: heatmap of hosts by concurrent proxy; timeline of opens minus closes; drilldown listing recent `client_ip` values for SOC handoff when non-automation subnets appear.

## SPL

```spl
index=network earliest=-24h@h latest=now
| eval st=lower(coalesce(sourcetype,_sourcetype,""))
| eval msg=lower(_raw)
| where match(msg,"netconf|nc_ssh|yang|ietf-netconf")
| eval evt=case(match(msg,"session.*(?:start|creat|open|establish|login)"),"open",match(msg,"session.*(?:clos|termin|logout|disconnect|end)"),"close",match(msg,"(?:timeout|idle.*expir|kill.*session)"),"timeout",1=1,"other")
| rex field=_raw max_match=0 "(?i)(?:session\s*id|sess-id|sid)[:=\s]+(?<session_id>[^\s,]+)"
| rex field=_raw max_match=0 "(?i)(?:user|username)[:=\s]+(?<nc_user>[^\s,]+)"
| rex field=_raw max_match=0 "(?:(?:from|client)\s+(?<client_ip>[0-9a-fA-F:.]+))"
| bin _time span=15m
| stats count(eval(evt="open")) as opens count(eval(evt="close")) as closes count(eval(evt="timeout")) as timeouts dc(session_id) as approx_sessions by _time host st
| eval net_opening=opens-closes
| eventstats avg(approx_sessions) as baseline by host
| where approx_sessions > baseline*2 OR net_opening>=5 OR timeouts>=3
| sort -approx_sessions
```

## Visualization

Dashboard Studio: KPI for hosts breaching session heuristic; `splunk.timechart` of approx_sessions by host; matrix panel for timeouts; detail table with host, opens, closes, client_ip samples.

## Known False Positives

**Telemetry ambiguity:** generic SSH logs lacking subsystem markers inflate NETCONF hits.**Backup polling:** legitimate periodic collectors holding long-lived sessions mimic leaks.**Log truncation:** missing close events when devices reload skew open-close math.**Regex breadth:** "yang" matches unrelated vendor strings—tighten `host` inventory filter.**IPv6 formatting:** dual-stack duplicates session counts unless normalized.

## References

- [Cisco IOS XE NETCONF Configuration Guide — Session management](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/guide/b-programmability-cg.html)
- [IETF RFC 6241 — Network Configuration Protocol (NETCONF)](https://www.rfc-editor.org/rfc/rfc6241)
- [Juniper Junos — NETCONF XML Management Protocol Developer Guide](https://www.juniper.net/documentation/)
