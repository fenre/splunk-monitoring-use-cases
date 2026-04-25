<!-- AUTO-GENERATED from UC-8.1.11.json — DO NOT EDIT -->

---
id: "8.1.11"
title: "NGINX Upstream Response Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.11 · NGINX Upstream Response Errors

## Description

Counts upstream HTTP 5xx and connect/timeout errors from NGINX access/error logs. Isolates reverse-proxy vs origin issues faster than aggregate 5xx alone.

## Value

Counts upstream HTTP 5xx and connect/timeout errors from NGINX access/error logs. Isolates reverse-proxy vs origin issues faster than aggregate 5xx alone.

## Implementation

Enable `upstream_status` and `upstream_addr` in log_format. Alert on upstream error rate >2% for 5m. Correlate with backend pool health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-nginx`.
• Ensure the following data sources are available: `access_combined` with `upstream_status`, `nginx:error` upstream messages.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `upstream_status` and `upstream_addr` in log_format. Alert on upstream error rate >2% for 5m. Correlate with backend pool health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="nginx:access" OR sourcetype="access_combined"
| eval up_err=if(upstream_status>=500 OR status=502 OR status=504,1,0)
| stats sum(up_err) as upstream_errors, count as total by host, upstream_addr
| eval err_rate=round(upstream_errors/total*100,2)
| where err_rate > 2
```

Understanding this SPL

**NGINX Upstream Response Errors** — Counts upstream HTTP 5xx and connect/timeout errors from NGINX access/error logs. Isolates reverse-proxy vs origin issues faster than aggregate 5xx alone.

Documented **Data sources**: `access_combined` with `upstream_status`, `nginx:error` upstream messages. **App/TA** (typical add-on context): `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: nginx:access, access_combined. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="nginx:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **up_err** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, upstream_addr** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **err_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where err_rate > 2` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (upstream error rate), Table (upstream_addr, errors), Bar chart (5xx by upstream).

## SPL

```spl
index=web sourcetype="nginx:access" OR sourcetype="access_combined"
| eval up_err=if(upstream_status>=500 OR status=502 OR status=504,1,0)
| stats sum(up_err) as upstream_errors, count as total by host, upstream_addr
| eval err_rate=round(upstream_errors/total*100,2)
| where err_rate > 2
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.dest | sort - count
```

## Visualization

Line chart (upstream error rate), Table (upstream_addr, errors), Bar chart (5xx by upstream).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
