<!-- AUTO-GENERATED from UC-1.2.91.json — DO NOT EDIT -->

---
id: "1.2.91"
title: "USB / Removable Device Auditing"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.91 · USB / Removable Device Auditing

## Description

Removable storage devices are a data exfiltration vector. Auditing device connections enables DLP and compliance enforcement.

## Value

USB and removable events prove policy enforcement and give evidence after data moves. They matter most on jump boxes and regulated workstations touched by this UC.

## Implementation

Enable Audit PnP Activity (EventCode 6416) via Advanced Audit Policy. Track USB mass storage, MTP devices, and portable drives. Correlate with file access events for full data movement picture. Alert on USB connections to servers or high-security workstations. Consider blocking USB storage via Group Policy on sensitive systems.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 6416), `sourcetype=WinEventLog:Microsoft-Windows-DriverFrameworks-UserMode/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Audit PnP Activity (EventCode 6416) via Advanced Audit Policy. Track USB mass storage, MTP devices, and portable drives. Correlate with file access events for full data movement picture. Alert on USB connections to servers or high-security workstations. Consider blocking USB storage via Group Policy on sensitive systems.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=6416
| eval DeviceClass=coalesce(ClassName, "Unknown")
| where DeviceClass="DiskDrive" OR DeviceClass="WPD" OR DeviceClass="USB"
| stats count by host, DeviceId, DeviceDescription, DeviceClass, SubjectUserName, _time
| sort -_time
```

Understanding this SPL

**USB / Removable Device Auditing** — Removable storage devices are a data exfiltration vector. Auditing device connections enables DLP and compliance enforcement.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 6416), `sourcetype=WinEventLog:Microsoft-Windows-DriverFrameworks-UserMode/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **DeviceClass** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where DeviceClass="DiskDrive" OR DeviceClass="WPD" OR DeviceClass="USB"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, DeviceId, DeviceDescription, DeviceClass, SubjectUserName, _time** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (device connections over time), Table (device details), Alert on server USB connections.

## SPL

```spl
index=wineventlog EventCode=6416
| eval DeviceClass=coalesce(ClassName, "Unknown")
| where DeviceClass="DiskDrive" OR DeviceClass="WPD" OR DeviceClass="USB"
| stats count by host, DeviceId, DeviceDescription, DeviceClass, SubjectUserName, _time
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.dest span=1h
| where count > 0
```

## Visualization

Timeline (device connections over time), Table (device details), Alert on server USB connections.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
