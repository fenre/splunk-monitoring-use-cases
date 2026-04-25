<!-- AUTO-GENERATED from UC-1.2.20.json — DO NOT EDIT -->

---
id: "1.2.20"
title: "Print Spooler Issues"
criticality: "low"
splunkPillar: "Security"
---

# UC-1.2.20 · Print Spooler Issues

## Description

Print spooler crashes affect print services and have historically been attack vectors (PrintNightmare). Monitoring catches both operational and security issues.

## Value

Print outages hit real work; the same component has been abused in the past, so this is both an ops and a security view.

## Implementation

Enable PrintService operational log on print servers. Alert on spooler crash (EventCode 372) and driver installation events (security relevance). Consider disabling the print spooler on servers that don't need it (attack surface reduction).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-PrintService/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable PrintService operational log on print servers. Alert on spooler crash (EventCode 372) and driver installation events (security relevance). Consider disabling the print spooler on servers that don't need it (attack surface reduction).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-PrintService/Operational" (EventCode=372 OR EventCode=805 OR EventCode=842)
| stats count by host, EventCode
| sort -count
```

Understanding this SPL

**Print Spooler Issues** — Print spooler crashes affect print services and have historically been attack vectors (PrintNightmare). Monitoring catches both operational and security issues.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-PrintService/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, EventCode** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest All_Changes.object span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Events timeline.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-PrintService/Operational" (EventCode=372 OR EventCode=805 OR EventCode=842)
| stats count by host, EventCode
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest All_Changes.object span=1h
| where count>0
```

## Visualization

Table, Events timeline.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
