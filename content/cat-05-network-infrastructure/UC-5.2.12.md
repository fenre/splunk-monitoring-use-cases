<!-- AUTO-GENERATED from UC-5.2.12.json — DO NOT EDIT -->

---
id: "5.2.12"
title: "NAT Pool Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.12 · NAT Pool Exhaustion

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We look for public address pools running out so new sessions still get out to the internet during busy days and big projects.*

---

## Description

NAT exhaustion prevents outbound connections. Users lose internet access.

## Value

Operations teams detect NAT pool exhaustion events and allocation failures that prevent new outbound connections, enabling capacity planning for NAT IP address pools.

## Implementation

Forward firewall logs. Monitor NAT table usage. Alert on exhaustion messages or >80% utilization.

## Detailed Implementation

### Prerequisites
* Firewall NAT/system logs in `index=firewall`. Key events: NAT pool exhaustion, PAT allocation failures, NAT session creation failures. Palo Alto: `pan:system` with NAT events. Fortinet: `fgt_event` with NAT messages. Key fields: `nat_pool`, `nat_rule`, `sessions_used`, `sessions_max`.
* NAT pool exhaustion: when all available IP:port combinations in a NAT pool are used, new outbound connections fail. PAT (Port Address Translation) typically allows ~64K ports per IP. For large environments, multiple NAT IPs are needed.

### Step 1 — - Configure data collection
**Palo Alto:**
```
show running nat-rule-ippool  # shows pool utilization
show running ippool  # shows allocated IPs and port ranges
```
Forward system events that include NAT resource warnings via syslog.
Verify:
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)NAT.*(exhaust|fail|alloc|pool|limit|resource|oversubscr)")
| stats count by host, _raw
| head 20
```

### Step 2 — - Create the search and alert

**Primary search -- NAT pool exhaustion detection:**
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)NAT.*(exhaust|fail|alloc.*fail|pool.*full|limit.*reach|resource.*low|oversubscr|no.*available)")
| eval nat_event=case(match(_raw, "(?i)exhaust|pool.*full|no.*available"), "POOL_EXHAUSTED", match(_raw, "(?i)alloc.*fail"), "ALLOCATION_FAILED", match(_raw, "(?i)limit.*reach|oversubscr"), "NEAR_LIMIT", match(_raw, "(?i)resource.*low"), "LOW_RESOURCES", 1==1, "OTHER")
| rex "pool\s+(?<nat_pool>[\w.-]+)"
| rex "rule\s+(?<nat_rule>[\w.-]+)"
| stats count as events latest(_time) as last_event by host, nat_event, nat_pool
| eval severity=case(nat_event="POOL_EXHAUSTED", "CRITICAL -- NAT pool exhausted, connections failing", nat_event="ALLOCATION_FAILED" AND events > 100, "HIGH -- frequent allocation failures", nat_event="NEAR_LIMIT", "WARNING -- approaching limit", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

**Session count by NAT pool (if available from API polling):**
```spl
index=firewall sourcetype="pan:system:resource" earliest=-4h
| eval pool_pct=round(100*tonumber(sessions_used)/tonumber(sessions_max), 1)
| where pool_pct > 70
| stats latest(pool_pct) as utilization latest(sessions_used) as used latest(sessions_max) as max by nat_pool, host
| sort -utilization
```

### Step 3 — - Validate
(a) Palo Alto: `show running nat-rule-ippool` -- check allocation percentage.
(b) Fortinet: `diagnose firewall iprope list 100004` -- shows NAT pool utilization.
(c) Verify by checking if users report internet access failures that correlate with NAT exhaustion events.

### Step 4 — - Operationalize
Dashboard ("Firewall -- NAT Pool Health"):
* Row 1 -- Gauge: "NAT pool utilization %" per pool.
* Row 2 -- NAT exhaustion events timeline.

Alerting:
* Critical (pool exhausted): outbound connections failing immediately.
* High (allocation failures > 100/hr): capacity issue.
* Warning (pool > 80%): plan additional NAT IPs.

### Step 5 — - Troubleshooting

* **NAT pool exhausted** -- Immediate: add more IP addresses to the NAT pool. Long-term: (1) identify top session consumers (specific hosts using excessive outbound connections), (2) reduce session timeouts for short-lived connections, (3) investigate for infected hosts opening many sessions.

* **Single host consuming most NAT sessions** -- May indicate: (1) P2P software, (2) malware with many C2 connections, (3) aggressive web crawler. Investigate the host.

* **NAT pool size planning** -- Rule of thumb: each public IP provides ~60K concurrent PAT sessions. For 10K users with average 5 concurrent connections, you need at least 1 NAT IP. Peak loads need 2-3x.

## SPL

```spl
index=firewall ("NAT" OR "nat") ("exhausted" OR "allocation failed" OR "out of")
| stats count by host, nat_pool | sort -count
```

## Visualization

Gauge per pool, Table, Events timeline.

## Known False Positives

Traffic bursts, many new users, and VoIP or gaming patterns can use more NAT resources than a steady baseline.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
