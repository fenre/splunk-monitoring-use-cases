<!-- AUTO-GENERATED from UC-5.14.16.json — DO NOT EDIT -->

---
id: "5.14.16"
title: "Varnish Workspace Client Overflow Detection"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.16 · Varnish Workspace Client Overflow Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance &middot; **Status:** Draft

*We watch varnish workspace client overflow detection and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Workspace overflows drop transactions abruptly.

## Value

Operations teams detect Varnish workspace memory overflows that cause 500 errors when client or backend request headers exceed the configured workspace buffer size.

## Implementation

Raise `workspace_client` and hunt oversized cookies or headers.

## Detailed Implementation

### Prerequisites
* Varnish statistics for workspace memory. Key counters: `MAIN.ws_client_overflow`, `MAIN.ws_backend_overflow`, `MAIN.ws_thread_overflow`. Data in `index=proxy` with `sourcetype=varnish:stats`.
* Workspaces: Varnish allocates fixed-size memory buffers per request (client workspace) and per backend request (backend workspace). When a request's headers or processing data exceed the workspace size, Varnish returns a 500 error. Common causes: very long URLs, many cookies, large headers.

### Step 1 — - Configure data collection
Same as UC-5.14.11. Verify:
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.ws_client_overflow.value" output=client_overflow
| stats latest(client_overflow) as overflows
```

### Step 2 — - Create the search and alert

**Primary search -- Workspace overflow detection:**
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.ws_client_overflow.value" output=client_overflow
| spath input=_raw path="MAIN.ws_backend_overflow.value" output=backend_overflow
| spath input=_raw path="MAIN.ws_thread_overflow.value" output=thread_overflow
| eval client_overflow=tonumber(client_overflow), backend_overflow=tonumber(backend_overflow), thread_overflow=tonumber(thread_overflow)
| bin _time span=5m
| stats latest(client_overflow) as client_of latest(backend_overflow) as backend_of latest(thread_overflow) as thread_of by _time
| streamstats current=f last(client_of) as prev_client last(backend_of) as prev_backend last(thread_of) as prev_thread
| eval client_rate=client_of - prev_client
| eval backend_rate=backend_of - prev_backend
| eval thread_rate=thread_of - prev_thread
| eval total_rate=client_rate + backend_rate + thread_rate
| where total_rate > 0
| eval severity=case(client_rate > 100, "CRITICAL -- heavy client workspace overflows", backend_rate > 100, "CRITICAL -- heavy backend workspace overflows", total_rate > 10, "HIGH -- workspace overflows occurring", 1==1, "WARNING")
| table _time, client_rate, backend_rate, thread_rate, severity
```

### Step 3 — - Validate
(a) `varnishstat -1 | grep ws_.*overflow`.
(b) Send a request with very large headers: `curl -H "X-Long: $(python3 -c 'print("A"*100000)')" http://<varnish>/` -- should trigger client workspace overflow.
(c) Check current workspace sizes: `varnishadm param.show workspace_client` and `workspace_backend`.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Workspace Health"):
* Row 1 -- Single-value: "Client overflows (/5m)", "Backend overflows (/5m)".
* Row 2 -- Overflow rate timechart.

Alerting:
* Critical (overflow rate > 100/5m): significant request failures.
* Warning (any overflow): investigate affected requests.

### Step 5 — - Troubleshooting

* **Client workspace overflow** -- Request headers too large. Increase: `varnishadm param.set workspace_client 128k` (default 64k). Investigate what's sending large headers (analytics cookies, JWT tokens in headers).

* **Backend workspace overflow** -- Backend response headers too large. Increase: `varnishadm param.set workspace_backend 128k`. Common cause: backends setting many `Set-Cookie` headers.

* **After increasing workspace, memory usage grows** -- Each workspace is allocated per thread. More workspace per thread = more total memory. Calculate: threads * workspace_size. Ensure server has capacity.

## SPL

```spl
index=proxy sourcetype="varnish:log"
| regex _raw="(?i)workspace.*overflow|WS.*overflow"
| stats count by host
| where count >= 1
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Workspace Client Overflow Detection» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishd.html)
