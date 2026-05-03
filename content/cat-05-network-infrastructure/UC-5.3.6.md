<!-- AUTO-GENERATED from UC-5.3.6.json — DO NOT EDIT -->

---
id: "5.3.6"
title: "Response Time Degradation (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.6 · Response Time Degradation (F5 BIG-IP)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We track how slow answers are from the load balancer to important URLs so a creeping delay is a signal before a full timeout storm.*

---

## Description

Increasing response times indicate backend bottlenecks before they become outages.

## Value

Application delivery teams track F5 BIG-IP response times per VIP and pool member with SLA threshold comparison, detecting backend latency degradation before it breaches service level agreements.

## Implementation

Enable request logging with server-side timing. Track P95 latency per VIP. Alert when exceeding SLA threshold.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680). F5 request logging profile capturing response time (`$RESPONSE_MSECS`). Data in `index=network` with `sourcetype=f5:bigip:ltm:http:request`. Key fields: `response_time_ms` or `response_msecs`, `virtual_server`, `pool_member`, `uri`.

### Step 1 — - Configure data collection
Ensure the F5 request logging profile includes `$RESPONSE_MSECS` in the template. Verify:
```spl
index=network sourcetype="f5:bigip:ltm:http:request" earliest=-4h
| where isnotnull(response_time_ms) OR isnotnull(response_msecs)
| stats avg(response_time_ms) as avg_ms by virtual_server
| sort -avg_ms
```

### Step 2 — - Create the search and alert

**Primary search -- Response time degradation by VIP:**
```spl
index=network sourcetype="f5:bigip:ltm:http:request" earliest=-4h
| eval rt=coalesce(response_time_ms, response_msecs)
| eval vs=coalesce(virtual_server, virtual_name)
| eval member=coalesce(pool_member, server_ip)
| stats avg(rt) as avg_ms p95(rt) as p95_ms p99(rt) as p99_ms max(rt) as max_ms count as requests by vs, member
| lookup f5_vip_inventory.csv virtual_server as vs OUTPUT application, tier, sla_ms
| eval sla_breach=if(isnotnull(sla_ms) AND p95_ms > sla_ms, "YES", "No")
| eval severity=case(p95_ms > 5000, "CRITICAL", p95_ms > 2000, "HIGH", p95_ms > 1000, "WARNING", sla_breach="YES", "SLA_BREACH", 1==1, "OK")
| where severity != "OK"
| sort severity, -p95_ms
```

**Response time trending:**
```spl
index=network sourcetype="f5:bigip:ltm:http:request" earliest=-24h
| eval rt=coalesce(response_time_ms, response_msecs)
| eval vs=coalesce(virtual_server, virtual_name)
| bin _time span=5m
| stats p95(rt) as p95_ms avg(rt) as avg_ms count as requests by _time, vs
| timechart span=5m avg(p95_ms) by vs
```

### Step 3 — - Validate
(a) Make a request to a known slow endpoint and verify the response time appears in Splunk.
(b) Compare p95 values with application APM data or backend server metrics.
(c) Add artificial delay to a test backend and verify the degradation shows in Splunk.

### Step 4 — - Operationalize
Dashboard ("F5 -- Response Times"):
* Row 1 -- Single-value: "Average response time", "P95 (all VIPs)", "SLA breaches", "Slowest VIP".
* Row 2 -- Per-VIP/member response time table with SLA comparison.
* Row 3 -- P95 response time trending timechart.

Alerting:
* Critical (p95 > 5s for prod VIP over 5 min): severe latency -- users impacted.
* Warning (p95 > SLA threshold for 15 min): SLA breach.

### Step 5 — - Troubleshooting

* **High response time on all members of one pool** -- Backend application is slow. Check: database queries, external API calls, GC pauses. This is not an F5 issue.

* **One pool member much slower than others** -- That server may be degraded. Check CPU/memory/disk on the backend. Consider marking it maintenance until resolved.

* **Response time spikes at specific times** -- Correlate with batch jobs, backups, or database maintenance on the backend.

## SPL

```spl
index=network sourcetype="f5:bigip:ltm:http"
| timechart span=5m perc95(server_latency) as p95 by virtual_server | where p95>2000
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Line chart (P50/P95/P99), Table, Single value.

## Known False Positives

Traffic bursts, long downloads, and cold caches can raise latency for short spans without a chronic problem.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
