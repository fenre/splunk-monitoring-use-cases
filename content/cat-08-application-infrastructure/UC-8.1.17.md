<!-- AUTO-GENERATED from UC-8.1.17.json — DO NOT EDIT -->

---
id: "8.1.17"
title: "IIS Web Server Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.17 · IIS Web Server Monitoring

## Description

IIS access logs provide visibility into web application health — error rates, response times, and request volumes. Critical for web-facing services.

## Value

IIS access logs provide visibility into web application health — error rates, response times, and request volumes. Critical for web-facing services.

## Implementation

Configure IIS to use W3C Extended Log Format with time-taken field. Forward IIS logs from `%SystemDrive%\inetpub\logs\LogFiles`. Use the Microsoft IIS TA for field extraction. Create alerts on 5xx error rate >5%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Splunk Add-on for Microsoft IIS.
• Ensure the following data sources are available: `sourcetype=ms:iis:auto` or `sourcetype=iis`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure IIS to use W3C Extended Log Format with time-taken field. Forward IIS logs from `%SystemDrive%\inetpub\logs\LogFiles`. Use the Microsoft IIS TA for field extraction. Create alerts on 5xx error rate >5%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="ms:iis:auto"
| timechart span=5m count by sc_status
| eval error_rate = round((sc_status_500 + sc_status_502 + sc_status_503) / (sc_status_200 + sc_status_500 + sc_status_502 + sc_status_503) * 100, 2)
```

Understanding this SPL

**IIS Web Server Monitoring** — IIS access logs provide visibility into web application health — error rates, response times, and request volumes. Critical for web-facing services.

Documented **Data sources**: `sourcetype=ms:iis:auto` or `sourcetype=iis`. **App/TA** (typical add-on context): `Splunk_TA_windows`, Splunk Add-on for Microsoft IIS. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: ms:iis:auto. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="ms:iis:auto". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by sc_status** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.



Step 3 — Validate
Compare a sample of alert results to IIS W3C extended logs on the server (or a one-off export of the same file) and, when applicable, the IIS Manager site. Confirm `sc-status`, time-taken, and URI fields match what you expect.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (requests by status code), Single value (error rate %), Table of top error URIs.

## SPL

```spl
index=web sourcetype="ms:iis:auto"
| timechart span=5m count by sc_status
| eval error_rate = round((sc_status_500 + sc_status_502 + sc_status_503) / (sc_status_200 + sc_status_500 + sc_status_502 + sc_status_503) * 100, 2)
```

## CIM SPL

```spl
| tstats `summariesonly` count as events
  from datamodel=Web.Web
  by Web.http_method Web.dest span=5m
| sort -events
```

## Visualization

Line chart (requests by status code), Single value (error rate %), Table of top error URIs.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
