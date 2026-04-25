<!-- AUTO-GENERATED from UC-2.6.66.json — DO NOT EDIT -->

---
id: "2.6.66"
title: "Citrix Endpoint Management App Distribution Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.66 · Citrix Endpoint Management App Distribution Failures

## Description

Pushing in-house, store, and volume-purchase programs (VPP) apps through CEM depends on correct tokens, licenses, and platform-specific constraints. A burst of VPP or enterprise install failures is often an Apple Business Manager or Google side issue; steady enterprise failures can point to signing or package corruption. This use case breaks down failures by channel so mobile operations can open the right vendor ticket, roll back a bad build, or fix token drift without re-imaging the whole estate.

## Value

Pushing in-house, store, and volume-purchase programs (VPP) apps through CEM depends on correct tokens, licenses, and platform-specific constraints. A burst of VPP or enterprise install failures is often an Apple Business Manager or Google side issue; steady enterprise failures can point to signing or package corruption. This use case breaks down failures by channel so mobile operations can open the right vendor ticket, roll back a bad build, or fix token drift without re-imaging the whole estate.

## Implementation

Ingest CEM app deployment or command-result logs. Tag errors into coarse buckets (VPP, public store, enterprise/internal). Mask user identifiers in shared dashboards. Alert when failures for a specific `app_id` cross a threshold in two consecutive hours, or when VPP-scoped errors exceed the prior week at the same time of day. Keep a runbook for common codes (license exhausted, not compatible OS, app removed from store). Pair with app owners so version bumps are not silent. Rate-limit noisy beta cohorts in test rings.

## Detailed Implementation

Prerequisites
• CEM and store connectors healthy; at least 30 days of history to learn seasonality; owners per published app in a lookup file.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map raw messages to a stable `error_category` with regex extractions. Keep large payloads in a separate summary index if needed for volume.

Step 2 — Create the search and alert
Tie alerts to `app_id` and include recent change tickets from your change system via lookup. Suppress for rolling pilot groups in their own tag.

Step 3 — Validate
In non-production, release a test enterprise app and force a controlled failure, confirm the category field.

Step 4 — Operationalize
Add this chart to the mobile apps CAB deck and track mean time to correct per channel.

## SPL

```spl
index=xd sourcetype="citrix:endpoint:app:deploy" outcome!="success"
| eval cat=lower(coalesce(error_category, failure_bucket, app_source, "unknown"))
| eval app=coalesce(app_name, app_id, "unknown")
| eval plat=coalesce(device_platform, os_type, "unknown")
| where like(cat, "%vpp%") OR like(cat, "%app%store%") OR like(cat, "%enterprise%") OR like(cat, "%push%") OR isnotnull(vpp_code)
| timechart span=1h count by cat, plat
| fillnull value=0
```

## Visualization

Stacked area of failures by error bucket; top failing apps table; link from `vpp_code` to Apple’s code reference where applicable.

## References

- [Distribute and manage mobile apps in Citrix Endpoint Management](https://docs.citrix.com/en-us/citrix-endpoint-management/mdm-mam/endpoint-management-mdm-mam-mdx-apps.html)
