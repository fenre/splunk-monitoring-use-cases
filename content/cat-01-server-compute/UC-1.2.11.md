<!-- AUTO-GENERATED from UC-1.2.11.json — DO NOT EDIT -->

---
id: "1.2.11"
title: "Blue Screen of Death (BSOD)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.11 · Blue Screen of Death (BSOD)

## Description

BSODs indicate severe system instability — driver bugs, hardware failure, or memory corruption. Repeated BSODs on the same host demand immediate attention.

## Value

Repeat BSODs on production hosts are a stability emergency—early visibility shortens the path to a driver, firmware, or hardware fix.

## Implementation

Enable System event log collection. Alert on EventCode 1001 from BugCheck source. Correlate bugcheck codes with known issues. Track frequency per host to identify chronic instability.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System`, EventCode=1001 (BugCheck).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable System event log collection. Alert on EventCode 1001 from BugCheck source. Correlate bugcheck codes with known issues. Track frequency per host to identify chronic instability.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=1001 SourceName="BugCheck"
| rex "(?<bugcheck_code>0x[0-9a-fA-F]+)"
| table _time host bugcheck_code Message
| sort -_time
```

Understanding this SPL

**Blue Screen of Death (BSOD)** — BSODs indicate severe system instability — driver bugs, hardware failure, or memory corruption. Repeated BSODs on the same host demand immediate attention.

Documented **Data sources**: `sourcetype=WinEventLog:System`, EventCode=1001 (BugCheck). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Blue Screen of Death (BSOD)**): table _time host bugcheck_code Message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1d
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table per host, Single value (BSOD count last 30d).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=1001 SourceName="BugCheck"
| rex "(?<bugcheck_code>0x[0-9a-fA-F]+)"
| table _time host bugcheck_code Message
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1d
| where count>0
```

## Visualization

Events timeline, Table per host, Single value (BSOD count last 30d).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
