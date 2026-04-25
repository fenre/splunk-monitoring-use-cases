<!-- AUTO-GENERATED from UC-4.3.37.json — DO NOT EDIT -->

---
id: "4.3.37"
title: "Cloud CDN Cache Performance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.3.37 · Cloud CDN Cache Performance

## Description

Low hit ratio raises origin load and latency; optimizing cache keys and TTL improves cost and user experience.

## Value

Low hit ratio raises origin load and latency; optimizing cache keys and TTL improves cost and user experience.

## Implementation

Parse cache hit/miss from load balancer logs. Segment by content type and geography. Alert when hit ratio drops vs 14-day baseline. Review cache mode and Vary headers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: HTTP(S) LB logs with cache fill/lookup fields, `sourcetype=google:gcp:monitoring` (cdn metrics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse cache hit/miss from load balancer logs. Segment by content type and geography. Alert when hit ratio drops vs 14-day baseline. Review cache mode and Vary headers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" httpRequest.latency!=""
| eval cache_hit=if(match(_raw,"cacheHit|CACHE_HIT"),1,0)
| stats sum(cache_hit) as hits, count as total by resource.labels.url_map_name
| eval hit_ratio=round(100*hits/total,2)
| where hit_ratio < 60 AND total > 1000
| sort hit_ratio
```

Understanding this SPL

**Cloud CDN Cache Performance** — Low hit ratio raises origin load and latency; optimizing cache keys and TTL improves cost and user experience.

Documented **Data sources**: HTTP(S) LB logs with cache fill/lookup fields, `sourcetype=google:gcp:monitoring` (cdn metrics). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cache_hit** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by resource.labels.url_map_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hit_ratio < 60 AND total > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (hit ratio by URL map), Bar chart (origin egress), Table (backend, hit %).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" httpRequest.latency!=""
| eval cache_hit=if(match(_raw,"cacheHit|CACHE_HIT"),1,0)
| stats sum(cache_hit) as hits, count as total by resource.labels.url_map_name
| eval hit_ratio=round(100*hits/total,2)
| where hit_ratio < 60 AND total > 1000
| sort hit_ratio
```

## Visualization

Line chart (hit ratio by URL map), Bar chart (origin egress), Table (backend, hit %).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
