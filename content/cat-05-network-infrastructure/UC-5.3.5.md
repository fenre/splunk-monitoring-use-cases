<!-- AUTO-GENERATED from UC-5.3.5.json — DO NOT EDIT -->

---
id: "5.3.5"
title: "HTTP Error Rate by VIP (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.5 · HTTP Error Rate by VIP (F5 BIG-IP)

## Description

Backend 5xx errors indicate application issues. Per-VIP tracking isolates degraded services.

## Value

Backend 5xx errors indicate application issues. Per-VIP tracking isolates degraded services.

## Implementation

Enable F5 request logging profile on VIPs. Alert when 5xx rate >5% over 5 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip`, request logging.
• Ensure the following data sources are available: F5 request logging profile.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable F5 request logging profile on VIPs. Alert when 5xx rate >5% over 5 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:ltm:http"
| eval is_error=if(response_code>=500,1,0)
| timechart span=5m sum(is_error) as errors, count as total by virtual_server
| eval error_rate=round(errors/total*100,2) | where error_rate>5
```

Understanding this SPL

**HTTP Error Rate by VIP (F5 BIG-IP)** — Backend 5xx errors indicate application issues. Per-VIP tracking isolates degraded services.

Documented **Data sources**: F5 request logging profile. **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`, request logging. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:ltm:http. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:ltm:http". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_error** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by virtual_server** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate>5` — typically the threshold or rule expression for this monitoring goal.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Web data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Web model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
In the F5 or pool member context, open the same time range in access or stream logs on the back end and confirm response codes and URLs track with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (error rate), Table (VIP, error rate), Single value.

## SPL

```spl
index=network sourcetype="f5:bigip:ltm:http"
| eval is_error=if(response_code>=500,1,0)
| timechart span=5m sum(is_error) as errors, count as total by virtual_server
| eval error_rate=round(errors/total*100,2) | where error_rate>5
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Line chart (error rate), Table (VIP, error rate), Single value.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
