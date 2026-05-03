<!-- AUTO-GENERATED from UC-5.3.7.json — DO NOT EDIT -->

---
id: "5.3.7"
title: "Session Persistence Issues (F5 BIG-IP)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.7 · Session Persistence Issues (F5 BIG-IP)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Anomaly

*We look for failed or odd persistence so sticky sessions, shopping carts, and long logins do not break quietly after a deploy.*

---

## Description

Broken persistence causes lost sessions, shopping carts, or random logouts.

## Value

Application delivery teams detect F5 BIG-IP session persistence failures where clients are incorrectly routed to multiple backends, causing session state loss and user experience degradation.

## Implementation

Monitor persistence failures. Track same client hitting different backends from request logs.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680). F5 request logging with persistence fields or LTM syslog. Key fields: `virtual_server`, `persistence_profile`, `persistence_cookie`, `client_ip`, `pool_member`, `session_id`.
* Session persistence ensures a client always reaches the same backend. Persistence failures cause: (1) lost shopping carts, (2) re-authentication, (3) session state loss. Persistence methods: cookie persistence (most common), source address affinity, SSL session ID, universal persistence.

### Step 1 — - Configure data collection
Verify persistence events:
```spl
index=network sourcetype="f5:bigip:syslog" ("persist" OR "persistence" OR "session affinity") earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Persistence failures and session bouncing:**
```spl
index=network (sourcetype="f5:bigip:ltm:http:request" OR sourcetype="f5:bigip:syslog") earliest=-4h
| eval vs=coalesce(virtual_server, virtual_name)
| eval member=coalesce(pool_member, server_ip)
| eval session=coalesce(persistence_cookie, session_id, client_ip)
| where isnotnull(session) AND isnotnull(member)
| stats dc(member) as members_hit count as requests values(member) as servers by vs, session
| where members_hit > 1
| eval issue=case(members_hit > 3, "SEVERE -- session hitting ".members_hit." different backends", members_hit > 1, "BROKEN -- session split across ".members_hit." backends")
| stats count as affected_sessions sum(requests) as total_requests by vs, issue
| lookup f5_vip_inventory.csv virtual_server as vs OUTPUT application, persistence_profile
| sort -affected_sessions
```

### Step 3 — - Validate
(a) Check persistence records on F5: `tmsh show ltm persistence persist-records all` and verify active sessions.
(b) Open a browser, make several requests to the same VIP, and verify all go to the same pool member.
(c) Clear persistence records and verify the session may be redirected.

### Step 4 — - Operationalize
Dashboard ("F5 -- Session Persistence"):
* Row 1 -- Single-value: "Broken sessions", "Affected VIPs", "Total sessions tracked".
* Row 2 -- Per-VIP persistence failure table.

Alerting:
* Warning (> 10 sessions hitting multiple backends in 15 min on a VIP with persistence): persistence failing.

### Step 5 — - Troubleshooting

* **Persistence broken after F5 failover** -- In an HA pair, persistence records are mirrored. Check: `tmsh show sys ha-mirror` -- if mirroring is not enabled, failover loses persistence.

* **Cookie persistence not working** -- Check: (1) Client is accepting cookies, (2) Cookie name matches the profile, (3) Browser dev tools shows the persistence cookie. For HTTPS, ensure the cookie isn't being stripped by security headers.

* **Source address persistence failing** -- If clients come through a proxy or NAT, all clients have the same source IP. Switch to cookie persistence instead.

## SPL

```spl
index=network sourcetype="f5:bigip:syslog" "persistence" ("failed" OR "expired")
| stats count by virtual_server, persistence_type | sort -count
```

## Visualization

Table, Line chart, Bar chart.

## Known False Positives

Sessions ending, new builds, and cookie changes can make persistence look flaky even when the app is fine.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
