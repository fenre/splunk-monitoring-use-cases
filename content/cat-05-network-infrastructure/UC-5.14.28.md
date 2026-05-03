<!-- AUTO-GENERATED from UC-5.14.28.json — DO NOT EDIT -->

---
id: "5.14.28"
title: "Squid HTTP Access Denied by ACL"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.28 · Squid HTTP Access Denied by ACL

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Audit &middot; **Status:** Draft

*We watch squid http access denied by acl and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Policy tuning needs ranked deny reasons not anecdotes.

## Value

Operations teams analyze Squid ACL-denied HTTP requests by client and destination, detecting policy violations, unauthorized access attempts, and potential malware C2 communication.

## Implementation

Add ACL tag to `access_log format` (Squid 4+); sanitize sensitive domains in dashboards.

## Detailed Implementation

### Prerequisites
* Squid access logs with TCP_DENIED status and ACL information. Data in `index=proxy` with `sourcetype=squid:access`. Key fields: `squid_request_status=TCP_DENIED`, `http_status_code=403`, `request_url`, `src_ip` (client IP).
* ACL-based access control: Squid ACLs (`acl` + `http_access allow/deny`) control which clients can access which destinations. Denied requests return TCP_DENIED/403. High denial rates may indicate: (1) policy too restrictive, (2) unauthorized access attempts, (3) malware trying to reach C2 servers.

### Step 1 — - Configure data collection
```
# squid.conf
acl allowed_sites dstdomain .example.com .internal.corp
http_access allow allowed_sites
http_access deny all
```
Verify:
```spl
index=proxy sourcetype="squid:access" squid_request_status="TCP_DENIED" earliest=-4h
| stats count by src_ip, request_url
| sort -count | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- ACL denial analysis by client and destination:**
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| where match(squid_request_status, "(?i)DENIED")
| rex field=request_url "https?://(?<denied_domain>[^/]+)"
| bin _time span=15m
| stats count as denials dc(src_ip) as affected_clients dc(denied_domain) as unique_domains values(denied_domain) as sample_domains by _time
| eval severity=case(denials > 500, "HIGH -- heavy denial volume", affected_clients > 50, "WARNING -- many clients being denied", unique_domains > 100, "WARNING -- diverse denied destinations (possible malware)", 1==1, "OK")
| where severity != "OK"
| table _time, denials, affected_clients, unique_domains, sample_domains, severity
```

**Top denied clients:**
```spl
index=proxy sourcetype="squid:access" squid_request_status="TCP_DENIED" earliest=-4h
| rex field=request_url "https?://(?<denied_domain>[^/]+)"
| stats count as denials dc(denied_domain) as unique_domains values(denied_domain) as top_domains by src_ip
| sort -denials | head 20
```

### Step 3 — - Validate
(a) Request a blocked URL: `curl -x http://<squid>:3128 http://blocked.example.com/` -- should get 403.
(b) Verify the denial appears in the access log with TCP_DENIED.
(c) `squidclient mgr:counters | grep denied` -- shows denial counts.

### Step 4 — - Operationalize
Dashboard ("Squid -- Access Denials"):
* Row 1 -- Single-value: "Denials (4h)", "Denied clients", "Denied domains".
* Row 2 -- Denial trending timechart.
* Row 3 -- Top denied clients and domains tables.

Alerting:
* High (single client > 500 denials/hr): possible malware or misconfigured app.
* Warning (denials to > 100 unique domains from single client): suspicious C2 behavior.

### Step 5 — - Troubleshooting

* **Legitimate traffic being denied** -- Review ACL order (Squid processes ACLs top-down, first match wins). Use `squid -k parse` to validate config syntax. Check `http_access` order.

* **High denials from single client** -- Investigate: (1) malware attempting outbound connections, (2) application misconfigured with wrong proxy settings, (3) browser extensions trying to reach analytics/ad networks.

* **Denied requests to internal hosts** -- Squid is blocking internal traffic. Ensure internal ranges are in an `acl localnet` with `http_access allow localnet`.

## SPL

```spl
index=proxy sourcetype="squid:access"
| where match(code, "TCP_DENIED|ERR_ACCESS_DENIED|NONE_ABORTED")
| stats count by acl, dst_domain, src_ip
| sort - count
| head 40
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid HTTP Access Denied by ACL» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/http_access/)
