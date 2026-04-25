<!-- AUTO-GENERATED from UC-8.2.30.json — DO NOT EDIT -->

---
id: "8.2.30"
title: "IIS HTTP.sys Kernel HTTP Error Log Resets"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.30 · IIS HTTP.sys Kernel HTTP Error Log Resets

## Description

HTTPERR records kernel-mode connection issues—idle timeouts, app aborts, and resets—that never appear in site W3C logs.

## Value

Explains mysterious client disconnects and TLS or ARR edge cases.

## Implementation

Assign a dedicated sourcetype; parse `Reason`, `s-ip`, and `c-ip`. Correlate with app pool recycles.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder monitors `%SystemRoot%\System32\LogFiles\HTTPERR\httperr*.log`.
• Ensure the following data sources are available: `index=web` HTTPERR log (`sourcetype=iis:httperr` or `httperr` as configured).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Reason strings vary by OS version; expand the OR list per Microsoft docs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="iis:httperr"
| search Reason="Connection_Abandoned_By_App" OR Reason="Timer_ConnectionIdle" OR Reason="Connection_Reset"
| stats count by Reason, s-ip
| sort -count
```

Understanding this SPL

**IIS HTTP.sys Kernel HTTP Error Log Resets** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` HTTPERR log (`sourcetype=iis:httperr` or `httperr` as configured). **App/TA**: Splunk Universal Forwarder monitors `%SystemRoot%\System32\LogFiles\HTTPERR\httperr*.log`. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Pie chart (reason), timechart, table (client IPs if available)..

## SPL

```spl
index=web sourcetype="iis:httperr"
| search Reason="Connection_Abandoned_By_App" OR Reason="Timer_ConnectionIdle" OR Reason="Connection_Reset"
| stats count by Reason, s-ip
| sort -count
```

## Visualization

Pie chart (reason), timechart, table (client IPs if available).

## References

- [Splunk Add-on for Microsoft IIS (Splunkbase)](https://splunkbase.splunk.com/app/3185)
- [Microsoft — Enable HTTP.sys tracing (HTTPERR)](https://learn.microsoft.com/en-us/troubleshoot/developer/webapps/iis/health-diagnostic-tools/http-sys-tracing-enable)
