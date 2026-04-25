<!-- AUTO-GENERATED from UC-8.1.18.json — DO NOT EDIT -->

---
id: "8.1.18"
title: "IIS Application Pool Crashes & Recycling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.18 · IIS Application Pool Crashes & Recycling

## Description

Application pool crashes cause HTTP 503 errors and service outages. Frequent recycling indicates memory leaks or configuration issues in web applications.

## Value

Application pool crashes cause HTTP 503 errors and service outages. Frequent recycling indicates memory leaks or configuration issues in web applications.

## Implementation

WAS (Windows Activation Service) events log automatically on IIS servers. EventCode 5002=worker process crashed, 5011=pool auto-disabled due to rapid failures (5 in 5 minutes default), 5012=rapid failure protection triggered. Alert on any 5011 event (pool disabled = site down). Track recycling frequency per pool. Correlate with WER EventCode 1000 for crash details including the faulting module.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Splunk Add-on for Microsoft IIS.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (Source=WAS, EventCode 5002, 5010, 5011, 5012, 5013).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
WAS (Windows Activation Service) events log automatically on IIS servers. EventCode 5002=worker process crashed, 5011=pool auto-disabled due to rapid failures (5 in 5 minutes default), 5012=rapid failure protection triggered. Alert on any 5011 event (pool disabled = site down). Track recycling frequency per pool. Correlate with WER EventCode 1000 for crash details including the faulting module.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="WAS"
  EventCode IN (5002, 5010, 5011, 5012, 5013)
| eval event=case(EventCode=5002,"AppPool crashed",EventCode=5010,"Process termination timeout",EventCode=5011,"AppPool auto-disabled",EventCode=5012,"AppPool rapid failures",EventCode=5013,"AppPool timeout")
| table _time, host, event, AppPoolName
| sort -_time
```

Understanding this SPL

**IIS Application Pool Crashes & Recycling** — Application pool crashes cause HTTP 503 errors and service outages. Frequent recycling indicates memory leaks or configuration issues in web applications.

Documented **Data sources**: `sourcetype=WinEventLog:System` (Source=WAS, EventCode 5002, 5010, 5011, 5012, 5013). **App/TA** (typical add-on context): `Splunk_TA_windows`, Splunk Add-on for Microsoft IIS. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **event** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **IIS Application Pool Crashes & Recycling**): table _time, host, event, AppPoolName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (app pool events), Timechart (recycling frequency), Status grid (pool × health), Single value (disabled pools — target: 0).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="WAS"
  EventCode IN (5002, 5010, 5011, 5012, 5013)
| eval event=case(EventCode=5002,"AppPool crashed",EventCode=5010,"Process termination timeout",EventCode=5011,"AppPool auto-disabled",EventCode=5012,"AppPool rapid failures",EventCode=5013,"AppPool timeout")
| table _time, host, event, AppPoolName
| sort -_time
```

## Visualization

Table (app pool events), Timechart (recycling frequency), Status grid (pool × health), Single value (disabled pools — target: 0).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
