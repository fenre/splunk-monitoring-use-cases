<!-- AUTO-GENERATED from UC-2.6.41.json — DO NOT EDIT -->

---
id: "2.6.41"
title: "FSLogix and Profile Container Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.41 · FSLogix and Profile Container Health

## Description

FSLogix profile and Office container disks live on fast SMB file shares. Slow attach, VHD reconnection failures, runaway VHDX growth, and share latency surface as long logon times or read-only profiles. Correlating FSLogix Application events with the profile phase in uberAgent logon data isolates the share path versus client-side issues faster than GPO review alone.

## Value

FSLogix profile and Office container disks live on fast SMB file shares. Slow attach, VHD reconnection failures, runaway VHDX growth, and share latency surface as long logon times or read-only profiles. Correlating FSLogix Application events with the profile phase in uberAgent logon data isolates the share path versus client-side issues faster than GPO review alone.

## Implementation

Ingest all FSLogix-related Application events and enable logical disk or SMB perf counters for share volumes. Set alerts on new error text patterns and on profile time >30s p95. Track VHD file size with a daily scripted inventory if not in events. For multi-site, tag share names with region and add synthetic SMB probes. Join carefully on `user` to avoid overmatching service accounts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows, uberAgent UXM (Splunkbase 1448) on VDAs.
• Ensure the following data sources are available: `sourcetype="WinEventLog:Application"` for FSLogix, `sourcetype="WinEventLog:System"` for VHD, optional perfmon for the profile volume.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `FSLogix` and `frx` logging in policy. Add inputs for the profile server share. Create a `ProfileLoad` or equivalent field alignment with uberAgent so joins work. If join noise appears, use `session_id` or `user_sid` as the join key instead of `user` when available.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; set subsearch window to your session length policy):

```spl
index=windows (sourcetype="WinEventLog:Application" (source="*FSLogix*" OR source="*frx*")) OR (sourcetype="WinEventLog:System" EventCode=50)
| search match(_raw, "(?i)FSLogix|frx|profile|containe|VHDX|VHD |reparse|reconnect|load.*fail|attach.*fail|size|quota|latency")
| eval severity=if(match(_raw, "(?i)fail|error|could not|denied|timeout|locked|reparse"), "error", if(match(_raw, "(?i)warn|slow|throttl|retry"), "warning", "info"))
| where severity!="info"
| join type=left user [search index=uberagent sourcetype="uberAgent:Logon:LogonDetail" earliest=-4h | stats latest(ProfileLoad) as uem_profile_s by user]
| table _time, host, user, Message, severity, uem_profile_s
```

Step 3 — Validate
Compare against a known bad profile in test. If `ProfileLoad` field name varies, `rename` in the subsearch. Confirm join cardinality (<50k) per run.

Step 4 — Operationalize
Send critical FSLogix errors to the file services team. Pair with a capacity check on the profile share to prevent sudden space exhaustion.

## SPL

```spl
index=windows (sourcetype="WinEventLog:Application" (source="*FSLogix*" OR source="*frx*")) OR (sourcetype="WinEventLog:System" EventCode=50)
| search match(_raw, "(?i)FSLogix|frx|profile|containe|VHDX|VHD |reparse|reconnect|load.*fail|attach.*fail|size|quota|latency")
| eval severity=if(match(_raw, "(?i)fail|error|could not|denied|timeout|locked|reparse"), "error", if(match(_raw, "(?i)warn|slow|throttl|retry"), "warning", "info"))
| where severity!="info"
| join type=left user [search index=uberagent sourcetype="uberAgent:Logon:LogonDetail" earliest=-4h | stats latest(ProfileLoad) as uem_profile_s by user]
| table _time, host, user, Message, severity, uem_profile_s
```

## Visualization

Timeline (FSLogix errors), Line chart (profile phase from uberAgent), Table (VHD size growth if inventoried).

## References

- [FSLogix documentation - Microsoft](https://learn.microsoft.com/en-us/fslogix/)
