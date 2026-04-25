<!-- AUTO-GENERATED from UC-9.4.25.json — DO NOT EDIT -->

---
id: "9.4.25"
title: "BeyondTrust Privileged Session Duration Beyond Policy Threshold"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.4.25 · BeyondTrust Privileged Session Duration Beyond Policy Threshold

## Description

Sessions that remain open for hours increase the window for credential theft, lateral movement, and unrecorded activity if recording fails mid-session.

## Value

Automates a control frequently checked only during audits, surfacing outliers before they appear in quarterly PAM reports.

## Implementation

Confirm which duration field your BeyondTrust parser provides; some feeds require computing `strptime` deltas between session start and end events. Set thresholds per asset class (120 minutes default). Join with change tickets for expected long maintenance.

## Detailed Implementation

Prerequisites
• Install and configure: BeyondTrust integrations feeding Splunk PAM index.
• Data sources: `sourcetype=beyondtrust:session` with duration or start/end timestamps.

Step 1 — Configure data collection
Confirm which duration field your BeyondTrust parser provides; some feeds require computing `strptime` deltas between session start and end events. Set thresholds per asset class (120 minutes default). Join with change tickets for expected long maintenance.

Step 2 — Create the search and alert

```spl
index=pam sourcetype="beyondtrust:session" earliest=-24h
| eval dur_min=coalesce(duration_min, round(duration_sec/60,1), round((SessionDurationSeconds)/60,1))
| eval user=coalesce(user, UserName, admin_user, "")
| eval target=coalesce(target_host, TargetHost, dest, "")
| where isnotnull(dur_min) AND dur_min>120
| stats max(dur_min) as max_min avg(dur_min) as avg_min by user, target
| sort -max_min
```

Step 3 — Validate
Compare with BeyondTrust session start/end and duration fields in the vendor console for the same session IDs and time range.

Step 4 — Operationalize
Add to a dashboard or alert; document the owner. Table (user × target × max duration), histogram of session lengths, timeline.

## SPL

```spl
index=pam sourcetype="beyondtrust:session" earliest=-24h
| eval dur_min=coalesce(duration_min, round(duration_sec/60,1), round((SessionDurationSeconds)/60,1))
| eval user=coalesce(user, UserName, admin_user, "")
| eval target=coalesce(target_host, TargetHost, dest, "")
| where isnotnull(dur_min) AND dur_min>120
| stats max(dur_min) as max_min avg(dur_min) as avg_min by user, target
| sort -max_min
```

## Visualization

Table (user × target × max duration), histogram of session lengths, timeline.

## References

- [BeyondTrust Password Safe / Cloud Dashboard for Splunk](https://splunkbase.splunk.com/app/5574)
- [BeyondTrust product documentation hub](https://www.beyondtrust.com/docs)
