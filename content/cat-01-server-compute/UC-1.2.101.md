---
id: "1.2.101"
title: "File Share Access Auditing (SMB)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.101 · File Share Access Auditing (SMB)

## Description

File share access auditing detects unauthorized data access, lateral movement via mapped drives, and ransomware encrypting network shares.

## Value

File share access auditing detects unauthorized data access, lateral movement via mapped drives, and ransomware encrypting network shares.

## Implementation

Enable Audit File Share and Audit Detailed File Share via Advanced Audit Policy. EventCode 5140 logs share-level access; 5145 logs individual file access (high volume — use targeted auditing). Alert on mass file access patterns (ransomware indicator), access from unusual IPs, and access to sensitive shares outside business hours. Use SACL on sensitive folders for granular auditing.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 5140, 5145).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Audit File Share and Audit Detailed File Share via Advanced Audit Policy. EventCode 5140 logs share-level access; 5145 logs individual file access (high volume — use targeted auditing). Alert on mass file access patterns (ransomware indicator), access from unusual IPs, and access to sensitive shares outside business hours. Use SACL on sensitive folders for granular auditing.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (5140, 5145)
| eval AccessType=case(EventCode=5140,"Share_Access", EventCode=5145,"File_Access", 1=1,"Other")
| stats count dc(RelativeTargetName) as UniqueFiles by SubjectUserName, IpAddress, ShareName, AccessType
| where count>100 OR UniqueFiles>50
| sort -count
```

Understanding this SPL

**File Share Access Auditing (SMB)** — File share access auditing detects unauthorized data access, lateral movement via mapped drives, and ransomware encrypting network shares.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 5140, 5145). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **AccessType** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by SubjectUserName, IpAddress, ShareName, AccessType** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count>100 OR UniqueFiles>50` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (access volume), Table (top users/shares), Alert on mass access patterns.

## SPL

```spl
index=wineventlog EventCode IN (5140, 5145)
| eval AccessType=case(EventCode=5140,"Share_Access", EventCode=5145,"File_Access", 1=1,"Other")
| stats count dc(RelativeTargetName) as UniqueFiles by SubjectUserName, IpAddress, ShareName, AccessType
| where count>100 OR UniqueFiles>50
| sort -count
```

## Visualization

Timechart (access volume), Table (top users/shares), Alert on mass access patterns.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
