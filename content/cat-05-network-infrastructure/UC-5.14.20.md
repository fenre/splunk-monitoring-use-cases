<!-- AUTO-GENERATED from UC-5.14.20.json — DO NOT EDIT -->

---
id: "5.14.20"
title: "Varnish Pipe Session Bypass Trending"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.20 · Varnish Pipe Session Bypass Trending

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Analytics &middot; **Status:** Draft

*We watch varnish pipe session bypass trending and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Unexpected pipe volume loads origin more than dashboards suggest.

## Value

Operations teams trend Varnish pipe (TCP tunnel) session volume and duration, identifying thread exhaustion risk from long-lived bypass connections like WebSockets.

## Implementation

Pipe mode disables caching for those requests; watch WebSocket or upload paths.

## Detailed Implementation

### Prerequisites
* Varnish access logs with pipe session indicators. Key fields: `handling` or `hitmiss` = "pipe", request duration. Data in `index=proxy` with `sourcetype=varnish:access`.
* Pipe mode: when `return(pipe)` is called in VCL `vcl_recv`, Varnish switches to TCP tunnel mode -- it forwards bytes between client and backend without HTTP parsing or caching. Used for WebSocket, non-HTTP protocols, or intentional bypass. Pipe sessions consume a thread for the entire duration. High pipe usage can exhaust threads.

### Step 1 — - Configure data collection
Verify pipe detection:
```spl
index=proxy sourcetype="varnish:access" earliest=-4h
| where match(hitmiss, "(?i)pipe") OR match(handling, "(?i)pipe")
| stats count as pipe_sessions avg(duration) as avg_duration_s
```

### Step 2 — - Create the search and alert

**Primary search -- Pipe session trending and thread impact:**
```spl
index=proxy sourcetype="varnish:access" earliest=-4h
| eval is_pipe=if(match(hitmiss, "(?i)pipe") OR match(handling, "(?i)pipe"), 1, 0)
| eval duration_s=tonumber(coalesce(duration, Tt))/1000000
| bin _time span=15m
| stats sum(is_pipe) as pipe_sessions count as total avg(eval(if(is_pipe=1, duration_s, null()))) as avg_pipe_duration max(eval(if(is_pipe=1, duration_s, null()))) as max_pipe_duration by _time
| eval pipe_pct=round(100*pipe_sessions/total, 2)
| eval severity=case(pipe_pct > 10, "HIGH -- >10% pipe sessions (thread exhaustion risk)", pipe_sessions > 100, "WARNING -- high pipe count", avg_pipe_duration > 300, "WARNING -- long pipe sessions (avg ".round(avg_pipe_duration, 0)."s)", 1==1, "OK")
| where severity != "OK"
| table _time, total, pipe_sessions, pipe_pct, avg_pipe_duration, max_pipe_duration, severity
```

### Step 3 — - Validate
(a) Check VCL for `return(pipe)` directives -- identify what triggers pipe mode.
(b) `varnishstat -1 | grep sess_pipe` -- shows pipe session count.
(c) Test a WebSocket connection through Varnish and verify it enters pipe mode.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Pipe Sessions"):
* Row 1 -- Single-value: "Pipe sessions", "Pipe %", "Avg pipe duration".
* Row 2 -- Pipe session timechart.

Alerting:
* High (pipe % > 10%): significant thread consumption risk.
* Warning (avg pipe duration > 5 min): long-lived pipes holding threads.

### Step 5 — - Troubleshooting

* **Unexpected pipe sessions** -- Review VCL `vcl_recv` for `return(pipe)` conditions. Common trigger: WebSocket `Upgrade` header or non-HTTP protocols. Ensure pipe is intentional.

* **Long-lived pipe sessions exhausting threads** -- Each pipe session holds a thread for its entire duration. For WebSocket, consider a dedicated proxy (e.g., nginx or HAProxy) instead of Varnish.

* **Pipe traffic not being logged** -- Pipe mode bypasses HTTP logging. Use `varnishlog -g session -q "VCL_call eq PIPE"` for pipe-specific logging.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)VCL_pipe|Link\s+pipe"
| bin _time span=5m
| stats count as pipe_sess by host, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Pipe Session Bypass Trending» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-pipe.html)
