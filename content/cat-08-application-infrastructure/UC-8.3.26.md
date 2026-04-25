<!-- AUTO-GENERATED from UC-8.3.26.json — DO NOT EDIT -->

---
id: "8.3.26"
title: "IIS 401 and 403 Error Rates by Site"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-8.3.26 · IIS 401 and 403 Error Rates by Site

## Description

Authentication and authorization failures often precede account lockouts, scanner activity, or misconfigured Windows Auth.

## Value

Improves SecOps visibility on IIS without relying solely on domain controller events.

## Implementation

Exclude static challenge paths; correlate with `cs-username` when populated.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft IIS (Splunkbase app 3185).
• Ensure the following data sources are available: `index=web` `sourcetype=ms:iis:auto` (`sc-status`, `cs-uri-stem`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Field names follow W3C; confirm `sc-status` extraction with `ms:iis:auto`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="ms:iis:auto"
| where sc_status=401 OR sc_status=403
| bin _time span=15m
| stats count by s_sitename, sc_status, cs-uri-stem
| eventstats sum(count) as site_total by s_sitename
| eval pct=round(100*count/site_total,2)
| where pct > 5
```

Understanding this SPL

**IIS 401 and 403 Error Rates by Site** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` `sourcetype=ms:iis:auto` (`sc-status`, `cs-uri-stem`). **App/TA**: Splunk Add-on for Microsoft IIS (Splunkbase app 3185). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Heatmap (site × status), table (URIs), timeline..

## SPL

```spl
index=web sourcetype="ms:iis:auto"
| where sc_status=401 OR sc_status=403
| bin _time span=15m
| stats count by s_sitename, sc_status, cs-uri-stem
| eventstats sum(count) as site_total by s_sitename
| eval pct=round(100*count/site_total,2)
| where pct > 5
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where (Web.status=401 OR Web.status=403)
  by Web.dest Web.uri_path Web.status span=15m
| sort -count
```

## Visualization

Heatmap (site × status), table (URIs), timeline.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Splunk Add-on for Microsoft IIS (Splunkbase)](https://splunkbase.splunk.com/app/3185)
