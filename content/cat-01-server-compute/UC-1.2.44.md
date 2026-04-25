<!-- AUTO-GENERATED from UC-1.2.44.json — DO NOT EDIT -->

---
id: "1.2.44"
title: "SMB Share Access Anomalies"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.44 · SMB Share Access Anomalies

## Description

Anomalous SMB share access patterns indicate lateral movement, data exfiltration, or ransomware file encryption across network shares.

## Value

Unusual *breadth* of share touch is a strong lateral movement hint when paired with identity context.

## Implementation

Enable "Audit File Share" and "Audit Detailed File Share" in Advanced Audit Policy. EventCode 5140=share accessed, 5145=detailed file access with access check results. Alert when a single user accesses many shares rapidly (lateral movement) or when write volume spikes (ransomware indicator). Baseline normal access patterns per user/role. Note: generates high volume — filter to sensitive shares or use summary indexing.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 5140, 5145).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Audit File Share" and "Audit Detailed File Share" in Advanced Audit Policy. EventCode 5140=share accessed, 5145=detailed file access with access check results. Alert when a single user accesses many shares rapidly (lateral movement) or when write volume spikes (ransomware indicator). Baseline normal access patterns per user/role. Note: generates high volume — filter to sensitive shares or use summary indexing.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140
| stats dc(ShareName) as unique_shares count by SubjectUserName, IpAddress
| where unique_shares > 10 OR count > 1000
| sort -unique_shares
```

Understanding this SPL

**SMB Share Access Anomalies** — Anomalous SMB share access patterns indicate lateral movement, data exfiltration, or ransomware file encryption across network shares.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 5140, 5145). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by SubjectUserName, IpAddress** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unique_shares > 10 OR count > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  by Authentication.user Authentication.src span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top share accessors), Timechart (access rate), Bar chart (shares accessed per user).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140
| stats dc(ShareName) as unique_shares count by SubjectUserName, IpAddress
| where unique_shares > 10 OR count > 1000
| sort -unique_shares
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  by Authentication.user Authentication.src span=1h
| where count>0
```

## Visualization

Table (top share accessors), Timechart (access rate), Bar chart (shares accessed per user).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
