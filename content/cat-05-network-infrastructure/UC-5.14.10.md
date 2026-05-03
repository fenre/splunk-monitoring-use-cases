<!-- AUTO-GENERATED from UC-5.14.10.json — DO NOT EDIT -->

---
id: "5.14.10"
title: "Varnish Backend Health Probe and Fetch Failures"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.10 · Varnish Backend Health Probe and Fetch Failures

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch varnish backend health probe and fetch failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Probe failures starve users even when edge CPUs look idle.

## Value

Operations teams monitor Varnish backend health probe results and fetch failures, detecting sick backends and connection errors before they cause widespread cache misses.

## Implementation

Enable backend polling; include `Backend` VSL tags in forwarded logs.

## Detailed Implementation

### Prerequisites
* Varnish logs including backend probe and fetch events. Key fields: `Backend_health`, `BerespStatus`, `FetchError`, `BackendOpen`, `BackendClose`. Data in `index=proxy` with `sourcetype=varnish:log` or `sourcetype=varnish:access`.
* Varnish health probes: configured per backend with `.probe { .url = "/health"; .interval = 5s; .timeout = 2s; .threshold = 3; .window = 5; }`. When a backend fails `threshold` probes out of `window`, Varnish marks it sick. Fetch failures occur when Varnish tries to connect to a backend and fails (TCP connect, timeout, HTTP error).

### Step 1 — - Configure data collection
Backend health logging:
```
# VCL backend definition
backend web1 {
    .host = "10.0.0.1";
    .port = "80";
    .probe = {
        .url = "/health";
        .interval = 5s;
        .timeout = 2s;
        .threshold = 3;
        .window = 5;
    }
}
```
Verify:
```spl
index=proxy (sourcetype="varnish:log" OR sourcetype="varnish:access") earliest=-4h
| where match(_raw, "(?i)Backend_health|FetchError|backend.*sick|backend.*healthy")
| stats count by _raw
| head 20
```

### Step 2 — - Create the search and alert

**Primary search -- Backend health transitions and fetch failures:**
```spl
index=proxy (sourcetype="varnish:log" OR sourcetype="varnish:access") earliest=-4h
| where match(_raw, "(?i)Backend_health|FetchError|backend.*(sick|healthy)|Beresp.*50[0-9]")
| eval event_type=case(match(_raw, "(?i)Backend_health.*Still sick"), "STILL_SICK", match(_raw, "(?i)Backend_health.*sick"), "WENT_SICK", match(_raw, "(?i)Backend_health.*healthy"), "WENT_HEALTHY", match(_raw, "(?i)FetchError"), "FETCH_ERROR", match(_raw, "(?i)Beresp.*(502|503|504)"), "BACKEND_ERROR", 1==1, "OTHER")
| rex "Backend_health\s+-\s+(?<backend>\S+)"
| rex "FetchError\s+(?<fetch_error>.+?)$"
| stats count as events latest(_time) as last_seen by backend, event_type, fetch_error
| eval severity=case(event_type="WENT_SICK", "CRITICAL -- backend marked sick", event_type="STILL_SICK", "CRITICAL -- backend still sick", event_type="FETCH_ERROR", "HIGH -- fetch errors", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) `varnishadm backend.list` -- shows backend health status.
(b) Stop a backend service and verify "went sick" appears in Splunk within probe interval.
(c) `varnishlog -g raw -i Backend_health` -- live stream of probe results.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Backend Health"):
* Row 1 -- Single-value: "Sick backends", "Fetch errors (4h)", "Backend transitions".
* Row 2 -- Backend state transition timeline.
* Row 3 -- Fetch error breakdown.

Alerting:
* Critical (backend went sick): capacity reduced, failover in effect.
* High (fetch error rate > 10/min): backend returning errors but still considered healthy.

### Step 5 — - Troubleshooting

* **Backend sick but service is running** -- Probe URL may be wrong or returning non-2xx. Check: `curl -v http://<backend>/health`. Verify the response code matches what Varnish expects (default: 200).

* **FetchError "no backend connection"** -- All backends are sick or maxconn reached. Check: (1) `varnishadm backend.list`, (2) backend TCP port is open, (3) firewall rules.

* **Backend flapping (sick/healthy/sick)** -- Probe thresholds may be too tight. Increase `.window` and `.threshold` to tolerate brief hiccups.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(Backend fetch failed|FetchError|no healthy backend)"
| stats count by backend
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Backend Health Probe and Fetch Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/vcl-backend-health.html)
