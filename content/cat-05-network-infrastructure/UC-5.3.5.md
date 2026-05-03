<!-- AUTO-GENERATED from UC-5.3.5.json — DO NOT EDIT -->

---
id: "5.3.5"
title: "HTTP Error Rate by VIP (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.5 · HTTP Error Rate by VIP (F5 BIG-IP)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We group server-side error rates by service so a bad release or a sick back end shows up on the same chart your users already feel.*

---

## Description

Backend 5xx errors indicate application issues. Per-VIP tracking isolates degraded services.

## Value

Application delivery teams monitor F5 BIG-IP HTTP error rates per virtual server, separating server-side (5xx) from client-side (4xx) errors to distinguish backend failures from invalid client requests.

## Implementation

Enable F5 request logging profile on VIPs. Alert when 5xx rate >5% over 5 minutes.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680). F5 BIG-IP request logging profile or LTM policy logging enabled, sending HTTP request/response data to Splunk. Data in `index=network` with `sourcetype=f5:bigip:ltm:http:request` or `sourcetype=f5:bigip:syslog`. Key fields: `virtual_server`, `response_code`, `client_ip`, `uri`, `method`, `pool_member`.
* F5 Request Logging: Create a request logging profile that captures response codes. Attach it to virtual servers you want to monitor.

### Step 1 — - Configure data collection
Create an HTTP analytics profile on F5:
```
tmsh create ltm profile request-log splunk_logging defaults-from request-log request-logging enabled request-log-pool <syslog_pool> request-log-template "$DATE_NCSA $VIRTUAL_NAME $CLIENT_IP $SERVER_IP:$SERVER_PORT $HTTP_METHOD $HTTP_URI $HTTP_STATCODE $RESPONSE_SIZE $RESPONSE_MSECS"
```
Attach to virtual server:
```
tmsh modify ltm virtual <vs> profiles add { splunk_logging }
```

Verify:
```spl
index=network (sourcetype="f5:bigip:ltm:http:request" OR sourcetype="f5:bigip:syslog") earliest=-4h
| where isnotnull(response_code) OR isnotnull(http_status)
| stats count by response_code
```

### Step 2 — - Create the search and alert

**Primary search -- HTTP error rate by VIP:**
```spl
index=network (sourcetype="f5:bigip:ltm:http:request" OR sourcetype="f5:bigip:syslog") earliest=-1h
| eval status=coalesce(response_code, http_status, status_code)
| eval status_class=case(status >= 500, "5xx_server", status >= 400, "4xx_client", status >= 300, "3xx_redirect", status >= 200, "2xx_success", 1==1, "other")
| eval vs=coalesce(virtual_server, virtual_name, vip_name)
| stats count as total count(eval(status_class="5xx_server")) as errors_5xx count(eval(status_class="4xx_client")) as errors_4xx by vs
| eval error_rate_5xx=round(100*errors_5xx/total, 2)
| eval error_rate_4xx=round(100*errors_4xx/total, 2)
| lookup f5_vip_inventory.csv virtual_server as vs OUTPUT application, tier
| eval severity=case(error_rate_5xx > 10, "CRITICAL", error_rate_5xx > 5, "HIGH", error_rate_5xx > 1, "WARNING", error_rate_4xx > 30, "WARNING -- high client errors", 1==1, "OK")
| where severity != "OK"
| sort severity, -error_rate_5xx
```

**Error trending by VIP:**
```spl
index=network (sourcetype="f5:bigip:ltm:http:request" OR sourcetype="f5:bigip:syslog") earliest=-24h
| eval status=coalesce(response_code, http_status)
| eval is_5xx=if(status >= 500, 1, 0)
| eval vs=coalesce(virtual_server, virtual_name)
| bin _time span=5m
| stats sum(is_5xx) as errors count as total by _time, vs
| eval error_pct=round(100*errors/total, 2)
| timechart span=5m avg(error_pct) by vs
```

### Step 3 — - Validate
(a) Generate a 503 by stopping a backend server and verify the error appears in Splunk.
(b) Compare error rates with F5 Dashboard: Statistics > Module Statistics > HTTP.
(c) Verify that 4xx errors (client-side) are separated from 5xx errors (server-side).

### Step 4 — - Operationalize
Dashboard ("F5 -- HTTP Error Rates"):
* Row 1 -- Single-value: "5xx error rate", "4xx error rate", "Total requests/hour", "Worst VIP".
* Row 2 -- Per-VIP error rate table with application context.
* Row 3 -- Error rate trending timechart.

Alerting:
* Critical (5xx > 10% for any prod VIP over 5 min): backend failures impacting users.
* Warning (5xx > 1% sustained for 15 min): elevated error rate.

### Step 5 — - Troubleshooting

* **High 5xx errors on one VIP** -- Check pool member health (UC-5.3.1). If all members are up, the backend application is returning errors. Check backend logs.

* **High 4xx errors** -- Usually client-side (bad URLs, authentication failures). Check if it's a bot or scanner generating bad requests. Look at the URI pattern.

* **No HTTP status data in Splunk** -- F5 request logging must be explicitly enabled per virtual server via the request logging profile. Without it, F5 syslog only contains connection-level events.

## SPL

```spl
index=network sourcetype="f5:bigip:ltm:http"
| eval is_error=if(response_code>=500,1,0)
| timechart span=5m sum(is_error) as errors, count as total by virtual_server
| eval error_rate=round(errors/total*100,2) | where error_rate>5
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Line chart (error rate), Table (VIP, error rate), Single value.

## Known False Positives

Bad releases, client retries, and upstream blips can raise error rates; compare to the app team before the load-balancer runbook.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
