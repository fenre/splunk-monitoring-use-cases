<!-- AUTO-GENERATED from UC-5.8.26.json — DO NOT EDIT -->

---
id: "5.8.26"
title: "CDN Origin Hit Rate and Cache Efficiency (CloudFront / Akamai / Fastly)"
status: "community"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.26 · CDN Origin Hit Rate and Cache Efficiency (CloudFront / Akamai / Fastly)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Community

*We watch how often our content delivery network (the cache layer that serves images and videos closer to users) actually finds what users ask for in its memory versus going back to the original servers. When the cache hit rate drops or errors climb, we alert before users notice slow pages or before our origin servers get overloaded.*

---

## Description

Tracks CDN cache efficiency and origin pull rates across CloudFront, Akamai, and Fastly by classifying each edge request as HIT, MISS, or ERROR and aggregating per URI. Surfaces URIs whose hit rate sits below 80% (the typical break-even threshold where the CDN is paying its way) or whose edge error count exceeds 10 in the search window.

## Value

Cache efficiency at the CDN edge is the lever that determines origin server load and end-user latency. A 90% hit rate means the origin sees one request for every ten user requests; a 50% hit rate means it sees five — a 5x amplification that capacity planning rarely accounts for. Misconfigured cache-control headers, unintentional cache-busting query strings, and cache-poisoning regressions all show up here long before they trip a separate origin-saturation alert. This UC also catches CDN misroutes (the same URI hitting multiple PoPs with wildly different hit rates).

## Implementation

Enable CloudFront access logging to S3 and ingest via Splunk Add-on for AWS. For Akamai, configure DataStream to forward to Splunk via syslog (or to a Kinesis sink the AWS TA can read). For Fastly, configure Real-Time Log Streaming to a Splunk HEC endpoint. Alert on cache hit rate drops below 80% or elevated edge error rates.

## SPL

```spl
index=cdn sourcetype="aws:cloudfront:accesslogs"
| eval cache_result=case(x_edge_result_type="Hit","HIT", x_edge_result_type="Miss","MISS", x_edge_result_type="Error","ERROR", 1=1,"OTHER")
| stats count as total, count(eval(cache_result="HIT")) as hits, count(eval(cache_result="MISS")) as misses, count(eval(cache_result="ERROR")) as errors by cs_uri_stem
| eval hit_rate=round(hits/total*100,2)
| where hit_rate < 80 OR errors > 10
| sort - total
```

## Visualization

Line chart (cache hit rate over time, multiple PoPs overlaid), Table (low-efficiency URIs sorted by total volume), Pie chart (HIT/MISS/ERROR distribution per CDN provider).

## Known False Positives

**First-deploy / cold-cache window.** A newly deployed origin or a freshly invalidated cache region will have low hit rates for the first few hours simply because the cache is empty. Suppress alerts during planned deploys and scheduled invalidations.

**Personalised content URIs.** URIs that incorporate per-user query strings (session IDs, A/B test buckets) legitimately have hit rates near 0% because the cache key is unique per request. Pre-filter these URIs from the search or move them to a dedicated origin pass-through path so they do not depress the dashboard average.

**Long-tail static assets.** The first request for a rarely-fetched static asset is always a MISS at every edge. URIs with very low absolute volume can show 50% hit rates simply because their first-of-day MISS dominates a sample of two requests. Filter `where total > 100` to focus on URIs with statistical significance.

## References

- [Splunk Add-on for AWS (Splunkbase app 1876)](https://splunkbase.splunk.com/app/1876)
- [AWS CloudFront access log documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html)
- [Akamai DataStream](https://techdocs.akamai.com/datastream2/docs)
- [Fastly Real-Time Log Streaming](https://docs.fastly.com/en/guides/about-fastlys-realtime-log-streaming-features)
