<!-- AUTO-GENERATED from UC-5.14.15.json — DO NOT EDIT -->

---
id: "5.14.15"
title: "Varnish ESI Fragment Error Rate"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.15 · Varnish ESI Fragment Error Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance &middot; **Status:** Draft

*We watch varnish esi fragment error rate and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

ESI failures create partial pages that are hard to spot in averages.

## Value

Operations teams detect Varnish ESI fragment fetch failures and XML parsing errors that cause broken page assembly for end users.

## Implementation

Limit verbose ESI debug to non-prod; aggregate counts in prod.

## Detailed Implementation

### Prerequisites
* Varnish logs with ESI (Edge Side Includes) processing events. Key counters: `MAIN.esi_errors`, `MAIN.esi_warnings`. ESI log tags: `ESI_xmlerror`, `Error`. Data in `index=proxy` with `sourcetype=varnish:log` or `sourcetype=varnish:stats`.
* ESI: Varnish parses `<esi:include src="/fragment"/>` tags in responses and fetches each fragment separately, allowing independent caching of page components. ESI errors occur when: (1) fragment fetch fails, (2) XML parsing error in ESI tags, (3) infinite include loop, (4) fragment returns non-200 status.

### Step 1 — - Configure data collection
Enable ESI in VCL:
```
sub vcl_backend_response {
    if (beresp.http.Content-Type ~ "text/html") {
        set beresp.do_esi = true;
    }
}
```
Verify:
```spl
index=proxy (sourcetype="varnish:log" OR sourcetype="varnish:stats") earliest=-4h
| where match(_raw, "(?i)esi_error|ESI_xmlerror|esi.*fail|esi.*warning")
| stats count
```

### Step 2 — - Create the search and alert

**Primary search -- ESI error analysis:**
```spl
index=proxy (sourcetype="varnish:log" OR sourcetype="varnish:stats") earliest=-4h
| eval is_stats=if(sourcetype="varnish:stats", 1, 0)
| eval esi_event=case(match(_raw, "(?i)ESI_xmlerror"), "XML_PARSE_ERROR", match(_raw, "(?i)esi.*failed.*fetch|esi.*no backend"), "FRAGMENT_FETCH_FAIL", match(_raw, "(?i)esi.*include.*loop"), "INCLUDE_LOOP", match(_raw, "(?i)esi_error"), "ESI_ERROR", match(_raw, "(?i)esi_warning"), "ESI_WARNING", 1==1, null())
| where isnotnull(esi_event)
| rex "src="(?<fragment_url>[^"]+)""
| stats count as errors dc(fragment_url) as unique_fragments values(fragment_url) as fragments by esi_event
| eval severity=case(esi_event="INCLUDE_LOOP", "CRITICAL -- recursive ESI loop", errors > 100, "HIGH -- frequent ESI errors", 1==1, "WARNING")
| sort severity, -errors
```

### Step 3 — - Validate
(a) Create a test page with `<esi:include src="/test-fragment"/>` and a failing fragment endpoint.
(b) `varnishstat -1 | grep esi` -- shows ESI error/warning counters.
(c) `varnishlog -q "ESI_xmlerror"` -- live ESI errors.

### Step 4 — - Operationalize
Dashboard ("Varnish -- ESI Health"):
* Row 1 -- Single-value: "ESI errors (4h)", "Failed fragments", "XML parse errors".
* Row 2 -- ESI error breakdown by type.

Alerting:
* Critical (include loop detected): can cause resource exhaustion.
* High (ESI errors > 100/hr): page rendering affected.

### Step 5 — - Troubleshooting

* **XML parse error** -- The parent page has malformed ESI tags. Check: properly closed tags, no nested `<esi:include>` in attributes, valid XML characters.

* **Fragment fetch failure** -- The fragment URL is unreachable. Check: (1) fragment backend is healthy, (2) URL path is correct relative to Varnish, (3) fragment backend has capacity.

* **Performance impact** -- Each ESI include is a separate internal request. Many fragments per page multiply latency. Consider reducing fragments or increasing TTLs on frequently used fragments.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(ESI.*error|include.*failed)"
| stats count by host
| where count > 10
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish ESI Fragment Error Rate» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/esi.html)
