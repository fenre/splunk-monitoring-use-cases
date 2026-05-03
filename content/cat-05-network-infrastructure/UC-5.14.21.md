<!-- AUTO-GENERATED from UC-5.14.21.json — DO NOT EDIT -->

---
id: "5.14.21"
title: "Varnish VCL Reload and Compilation Errors"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.21 · Varnish VCL Reload and Compilation Errors

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Change, Fault &middot; **Status:** Draft

*We watch varnish vcl reload and compilation errors and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Compile errors during reloads can strand traffic on old VCL or stop updates.

## Value

Operations teams detect Varnish VCL compilation failures during reload and track configuration deployment frequency to catch failed deployments where the old VCL remains active.

## Implementation

Page immediately on compile failure in production paths.

## Detailed Implementation

### Prerequisites
* Varnish CLI or log events for VCL operations. Key events: `VCL_Log` (custom log from VCL), `CLI` (management CLI commands including `vcl.load`, `vcl.use`, `vcl.discard`). Data in `index=proxy` with `sourcetype=varnish:log` or `sourcetype=varnish:stats`.
* VCL reload: hot-reload is a key Varnish feature -- `vcl.load` compiles new VCL to C, then `vcl.use` activates it without dropping connections. Compilation errors (syntax errors, missing backends, undefined subroutines) cause the load to fail, leaving the old VCL active. Frequent reloads may indicate configuration churn or automation issues.

### Step 1 — - Configure data collection
VCL operations are logged by the varnish management interface. Forward varnishd syslog:
```
# /etc/rsyslog.d/varnish.conf
:programname, isequal, "varnishd" /var/log/varnish/varnishd.log
```
Verify:
```spl
index=proxy (sourcetype="varnish:log" OR sourcetype="syslog") earliest=-24h
| where match(_raw, "(?i)vcl\.load|vcl\.use|vcl\.discard|VCL.*compil|VCL.*error|VCL.*loaded")
| stats count by _raw | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- VCL reload and compilation error detection:**
```spl
index=proxy (sourcetype="varnish:log" OR sourcetype="syslog") earliest=-24h
| where match(_raw, "(?i)vcl\.(load|use|discard)|VCL.*compil|VCL.*error|VCL.*fail|VCL.*loaded|VCL.*active")
| eval event_type=case(match(_raw, "(?i)VCL.*error|VCL.*fail|compilation.*failed"), "COMPILE_ERROR", match(_raw, "(?i)vcl\.load|VCL.*loaded"), "VCL_LOAD", match(_raw, "(?i)vcl\.use|VCL.*active"), "VCL_ACTIVATE", match(_raw, "(?i)vcl\.discard"), "VCL_DISCARD", 1==1, "OTHER")
| rex "vcl\.load\s+(?<vcl_name>\S+)"
| stats count as events latest(_time) as last_event values(vcl_name) as vcl_names by event_type
| eval severity=case(event_type="COMPILE_ERROR", "CRITICAL -- VCL compilation failed", event_type="VCL_LOAD" AND events > 20, "WARNING -- frequent VCL reloads (".events." in 24h)", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Intentionally load VCL with a syntax error: `varnishadm vcl.load test_bad /tmp/bad.vcl` -- should fail.
(b) `varnishadm vcl.list` -- shows loaded VCL versions and which is active.
(c) Verify successful reload: `varnishadm vcl.load test1 /etc/varnish/default.vcl && varnishadm vcl.use test1`.

### Step 4 — - Operationalize
Dashboard ("Varnish -- VCL Management"):
* Row 1 -- Single-value: "VCL loads (24h)", "Compilation errors", "Active VCL version".
* Row 2 -- VCL event timeline.

Alerting:
* Critical (compilation error): VCL change failed -- old config still active.
* Warning (> 20 reloads/day): configuration churn.

### Step 5 — - Troubleshooting

* **Compilation error** -- Check the error message for line number and description. Common: (1) undefined backend referenced, (2) syntax error in regex, (3) deprecated VCL syntax (e.g., Varnish 4.x syntax in 6.x).

* **Reload fails silently** -- VCL load might succeed but `vcl.use` fails. Check with `varnishadm vcl.list` to see if new VCL is "available" but not "active".

* **Many stale VCL versions** -- Old loaded VCL versions consume memory. Clean up with `varnishadm vcl.discard <name>`. Automate cleanup in deployment scripts.

## SPL

```spl
index=proxy sourcetype="varnish:log"
| regex _raw="(?i)(VCL compilation failed|syntax error in.*vcl)"
| stats count by host, _raw
| where count >= 1
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish VCL Reload and Compilation Errors» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-separate.html)
