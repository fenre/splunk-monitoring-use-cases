<!-- AUTO-GENERATED from UC-8.5.13.json — DO NOT EDIT -->

---
id: "8.5.13"
title: "Varnish Ban and Purge Request Bursts"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-8.5.13 · Varnish Ban and Purge Request Bursts

## Description

Sudden ban/purge storms may follow bad deploys, cache poisoning response, or automation bugs.

## Value

Correlates cache invalidation with content management changes.

## Implementation

Ship filtered VSL lines to reduce volume; include username if management ACL logs it.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: varnishlog forwarding (tagged VSL) or `varnishhist` pipeline.
• Ensure the following data sources are available: `index=cache` `sourcetype=varnish:vsl` or management log with `BAN` / `RP` tags.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
If VSL is unavailable, approximate via HTTP PURGE requests logged at the edge.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="varnish:vsl"
| search "BAN" OR "PURGE"
| bin _time span=5m
| stats count by _time
| where count > 50
```

Understanding this SPL

**Varnish Ban and Purge Request Bursts** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=cache` `sourcetype=varnish:vsl` or management log with `BAN` / `RP` tags. **App/TA**: varnishlog forwarding (tagged VSL) or `varnishhist` pipeline. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with `varnishstat` or `varnishlog` on the Varnish host for the same period.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Timeline (events/min), table (operators), link to CMS releases..

## SPL

```spl
index=cache sourcetype="varnish:vsl"
| search "BAN" OR "PURGE"
| bin _time span=5m
| stats count by _time
| where count > 50
```

## Visualization

Timeline (events/min), table (operators), link to CMS releases.

## References

- [varnishstat — Varnish reference](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
