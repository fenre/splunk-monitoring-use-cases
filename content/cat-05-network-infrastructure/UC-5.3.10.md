<!-- AUTO-GENERATED from UC-5.3.10.json — DO NOT EDIT -->

---
id: "5.3.10"
title: "Backend Server Error Code Distribution (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.10 · Backend Server Error Code Distribution (F5 BIG-IP)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We list five-hundred class errors from behind the service so a sick app, not just the load balancer, gets help before users pile on in chat.*

---

## Description

Understanding which backends return 5xx errors helps isolate faulty application instances vs. systemic issues.

## Value

Application delivery teams identify which specific F5 BIG-IP pool members generate backend errors (502/503/504/500), pinpointing unhealthy servers and providing per-error-code diagnosis for rapid triage.

## Implementation

Enable HTTP response logging on the LB. Track 5xx rates per backend member. Alert when a single member's error rate exceeds the pool average by 3x. Auto-disable unhealthy members.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680). F5 request logging profile capturing backend server response codes. Key fields: `pool_member`, `response_code`, `virtual_server`, `uri`.
* This UC focuses on backend-originated errors (the F5 passes through the backend's response code). This differs from UC-5.3.5 which measures error rate per VIP -- this UC drills into which specific backend servers are generating errors.

### Step 1 — - Configure data collection
Ensure request logging captures `$SERVER_IP:$SERVER_PORT` and `$HTTP_STATCODE`. Verify:
```spl
index=network sourcetype="f5:bigip:ltm:http:request" earliest=-4h
| where isnotnull(pool_member) AND isnotnull(response_code)
| eval status=tonumber(response_code)
| where status >= 400
| stats count by pool_member, response_code
| sort -count
```

### Step 2 — - Create the search and alert

**Primary search -- Backend error distribution:**
```spl
index=network sourcetype="f5:bigip:ltm:http:request" earliest=-4h
| eval status=tonumber(coalesce(response_code, http_status))
| eval member=coalesce(pool_member, server_ip)
| eval vs=coalesce(virtual_server, virtual_name)
| eval error_class=case(status=502, "502 Bad Gateway", status=503, "503 Service Unavailable", status=504, "504 Gateway Timeout", status=500, "500 Internal Server Error", status >= 500, "5xx Other", status >= 400, "4xx Client Error", 1==1, null())
| where isnotnull(error_class) AND status >= 500
| stats count as errors by vs, member, error_class
| eventstats sum(errors) as total_errors by vs
| eval error_share=round(100*errors/total_errors, 1)
| lookup f5_vip_inventory.csv virtual_server as vs OUTPUT application
| eval diagnosis=case(error_class="502 Bad Gateway", "Backend unreachable or returned invalid response", error_class="503 Service Unavailable", "Backend explicitly rejecting -- at capacity or maintenance", error_class="504 Gateway Timeout", "Backend too slow -- exceeded F5 timeout", error_class="500 Internal Server Error", "Application error on backend", 1==1, "Investigate backend logs")
| sort vs, -errors
```

### Step 3 — - Validate
(a) Stop a backend service and verify 502/503 errors appear attributed to that member.
(b) Add a sleep/delay to a backend and verify 504 Gateway Timeout appears.
(c) Compare error distribution with backend application logs.

### Step 4 — - Operationalize
Dashboard ("F5 -- Backend Error Analysis"):
* Row 1 -- Single-value: "Total 5xx errors", "Worst backend server", "502s", "503s", "504s".
* Row 2 -- Per-member error breakdown with diagnosis.

Alerting:
* High (single member generating > 50% of pool errors): unhealthy member -- consider marking down.
* Warning (504 Gateway Timeout spike): backend latency exceeding F5 timeout.

### Step 5 — - Troubleshooting

* **502 Bad Gateway** -- F5 cannot connect to backend or got invalid response. Check: (1) backend process is running, (2) backend port is listening, (3) firewall between F5 and backend.

* **504 Gateway Timeout** -- Backend is responding too slowly. Check F5 timeout: `tmsh list ltm profile http response-timeout`. Increase if backend needs more time (but also investigate why it's slow).

* **One member has all the errors** -- That server is unhealthy. Check: (1) Application logs on that server, (2) CPU/memory/disk, (3) Database connectivity from that server.

## SPL

```spl
index=network sourcetype="f5:bigip:ltm:http"
| where response_code >= 500
| stats count by pool_member, response_code, virtual_server
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Bar chart (errors by backend), Table (member, error code, count), Timechart.

## Known False Positives

Deploys, dependency outages, and bad releases can return five-hundred class codes from the app servers while the load balancer is healthy.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
