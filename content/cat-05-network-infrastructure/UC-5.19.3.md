<!-- AUTO-GENERATED from UC-5.19.3.json — DO NOT EDIT -->

---
id: "5.19.3"
title: "RESTCONF API Error Rate to Network Devices"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.19.3 · RESTCONF API Error Rate to Network Devices

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance, Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*We measure how often bad replies happen when tools talk to gear over the newer web-style management channel. Spikes tell us something broke in permissions, formatting, or load before hundreds of settings fail at once.*

---

## Description

Splunk aggregates RESTCONF-facing HTTP access trails so elevated 4xx/5xx ratios, payload validation faults, and latency tails across automation tenants become visible before controllers silently stall bulk intent pushes.

## Value

Operators regain confidence in model-driven workflows because misauthentication, schema mismatches, or oversubscribed TLS frontends are quantified per device cluster rather than inferred from vague "commit failed" chatter in chat rooms.

## Implementation

Land RESTCONF paths with HTTP status and timing fields; strip secrets from bodies; schedule ten-minute buckets; maintain allowlist for probe clients; correlate spikes with change calendars.

## Detailed Implementation

### Prerequisites
- Inventory which devices expose RESTCONF directly versus via centralized API gateway; document TLS offload paths.
- Standardize log format (JSON preferred) including upstream device identity.

### Step 1 — Access logging
Enable structured access logs on the terminating proxy or enable IOS-XE RESTCONF diagnostics appropriate for operations (avoid full payload capture).

### Step 2 — Field extraction
Parse `status`, `uri`, `latency`; map `device_host` from upstream DNS or X-Forwarded headers; reject events missing RESTCONF path markers to reduce noise.

### Step 3 — Saved search
Save as `restconf_error_rate_10m`; alert when `err_rate`≥5% with ≥20 requests per bucket or `p95_ms` doubles rolling median.

### Step 4 — Validate
Inject controlled 401/404 responses in lab; verify Splunk classification matches curl transcripts.

### Step 5 — Operationalize
Dashboard: timeline of error rate by device group; top URIs table; optional lookup enrichments for owning team; suppress maintenance windows via CSV.

## SPL

```spl
index IN ("network","web","proxy") earliest=-4h@m latest=now
| eval uri_l=lower(coalesce(uri,request_uri,url_path,""))
| where match(uri_l,"restconf") OR match(lower(_raw),"restconf")
| eval sc=tonumber(coalesce(status,http_status,response_code))
| eval err=if(isnull(sc),1,if(sc>=400,1,0))
| eval ms=tonumber(coalesce(latency_ms,request_time,duration_ms))
| eval dev=coalesce(device_host,upstream_host,host)
| bin _time span=10m
| stats count as reqs sum(err) as err_ct perc95(ms) as p95_ms values(client_ip) as clients by _time dev
| eval err_rate=round(100*err_ct/nullif(reqs,0),2)
| where reqs>=20 AND err_rate>=5
| sort -err_rate,-p95_ms
```

## Visualization

Dashboard Studio: single-value error-rate KPI; `splunk.timechart` by device group; drilldown table (`dev`,`reqs`,`err_ct`,`err_rate`,`p95_ms`,`clients`).

## Known False Positives

**Auth rotation:** mass 401s during certificate rollover resemble outages.**Scanner noise:** external scanners hitting `/restconf` drive 404s unless IP-restricted.**Health probes:** synthetic checks bump counts—tag `User-Agent`.**Double logging:** client plus proxy duplicates requests unless deduped.**Large payloads:** latency spikes during config dumps are benign unless sustained.

## References

- [IETF RFC 8040 — RESTCONF Protocol](https://www.rfc-editor.org/rfc/rfc8040)
- [Cisco Programmability Configuration Guide — RESTCONF](https://www.cisco.com/c/en/us/)
- [NGINX access log module reference](https://nginx.org/en/docs/http/ngx_http_log_module.html)
