<!-- AUTO-GENERATED from UC-5.14.34.json — DO NOT EDIT -->

---
id: "5.14.34"
title: "Squid External ACL Helper Failures"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.34 · Squid External ACL Helper Failures

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Security &middot; **Status:** Draft

*We watch squid external acl helper failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

External ACLs are on the critical path for every request.

## Value

Operations teams monitor Squid external ACL helper process health, detecting broken helpers, timeouts, and queue overloads that disrupt access control decisions.

## Implementation

Scale concurrent helpers; cap slow identity providers.

## Detailed Implementation

### Prerequisites
* Squid cache logs with external ACL helper events. Data in `index=proxy` with `sourcetype=squid:cache`. Key events: helper process spawn/death, timeout, BH (broken helper) responses, slow responses.
* External ACL helpers: Squid can delegate access decisions to external programs via `external_acl_type`. These helpers check LDAP groups, databases, URL categories, etc. When helpers fail, Squid either denies all traffic (default deny) or allows everything (if configured), creating a security issue.

### Step 1 — - Configure data collection
```
# squid.conf
external_acl_type url_check ttl=300 negative_ttl=60 children-max=20 children-startup=5 %URI /usr/lib/squid/url_filter_helper
acl allowed_urls external url_check
http_access allow allowed_urls
```
Verify:
```spl
index=proxy sourcetype="squid:cache" earliest=-4h
| where match(_raw, "(?i)external.*acl|helper|ext_acl|BH|helper.*process|helper.*restarting")
| stats count by _raw | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- External ACL helper health:**
```spl
index=proxy sourcetype="squid:cache" earliest=-4h
| where match(_raw, "(?i)external.*acl|helper|ext_acl|BH|helper.*process|helper.*(crash|restart|timeout|queue|overload)")
| eval helper_event=case(match(_raw, "(?i)BH|broken.helper"), "BROKEN_HELPER", match(_raw, "(?i)timeout|timed.out"), "HELPER_TIMEOUT", match(_raw, "(?i)crash|died|restarting"), "HELPER_CRASH", match(_raw, "(?i)queue.*full|overload|too.many"), "HELPER_OVERLOADED", match(_raw, "(?i)started|spawn"), "HELPER_STARTED", 1==1, "OTHER")
| where helper_event != "OTHER" AND helper_event != "HELPER_STARTED"
| stats count as events latest(_time) as last_event by helper_event
| eval severity=case(helper_event="BROKEN_HELPER", "CRITICAL -- helper returning BH (all requests may be denied)", helper_event="HELPER_CRASH", "CRITICAL -- helper process died", helper_event="HELPER_TIMEOUT", "HIGH -- helper responses slow", helper_event="HELPER_OVERLOADED", "HIGH -- helper queue full", 1==1, "WARNING")
| sort severity, -events
```

### Step 3 — - Validate
(a) Kill a helper process and verify Squid logs the death and restarts.
(b) `squidclient mgr:ext_acl` -- shows helper statistics (requests, hits, misses, errors).
(c) Check helper concurrency: `ps aux | grep url_filter_helper | wc -l` vs `children-max`.

### Step 4 — - Operationalize
Dashboard ("Squid -- External ACL Helpers"):
* Row 1 -- Single-value: "BH events", "Timeouts", "Crashes", "Queue overloads".
* Row 2 -- Helper event timeline.

Alerting:
* Critical (BH or crash events): access control compromised.
* High (timeouts > 50/hr): helper performance degradation.

### Step 5 — - Troubleshooting

* **BH (Broken Helper)** -- Helper returned an error instead of OK/ERR. Check: (1) helper program logs, (2) dependency availability (LDAP server, database), (3) helper binary permissions.

* **Helper timeout** -- Helper is taking too long to respond. Check: (1) `external_acl_type` timeout setting, (2) backend service latency (LDAP query time), (3) increase `children-max` if helpers are overloaded.

* **Helper queue full** -- More requests than helpers can process. Increase `children-max` and `children-startup`. Also increase `ttl` to cache more decisions and reduce helper load.

## SPL

```spl
index=proxy sourcetype="squid:cache"
| regex _raw="(?i)external_acl.*(?:fail|timeout|error)"
| stats count by host
| where count > 5
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid External ACL Helper Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/external_acl_type/)
