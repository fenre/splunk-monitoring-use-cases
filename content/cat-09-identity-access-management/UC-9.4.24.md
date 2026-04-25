<!-- AUTO-GENERATED from UC-9.4.24.json — DO NOT EDIT -->

---
id: "9.4.24"
title: "BeyondTrust Privileged Sessions Started Outside Business Hours"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.24 · BeyondTrust Privileged Sessions Started Outside Business Hours

## Description

Privileged PAM sessions that begin late night or on weekends warrant review because they align with ransomware operators and rogue administrators evading oversight.

## Value

Operationalizes a simple time-based control that works even when session recordings are retained elsewhere, giving SOC analysts a prioritized review queue.

## Implementation

Adjust business-hour boundaries and weekend definition for your locale. Map `target_host` field names to your parser. Exclude maintenance accounts via lookup. Pair with on-call schedules to reduce false positives.

## Detailed Implementation

Prerequisites
• Install and configure: BeyondTrust TA / Splunk CIM Email & Authentication patterns (org deployment).
• Data sources: `sourcetype=beyondtrust:session` (or normalized PAM session events forwarded from BeyondTrust).

Step 1 — Configure data collection
Adjust business-hour boundaries and weekend definition for your locale. Map `target_host` field names to your parser. Exclude maintenance accounts via lookup. Pair with on-call schedules to reduce false positives.

Step 2 — Create the search and alert

```spl
index=pam sourcetype="beyondtrust:session" earliest=-7d
| eval user=coalesce(user, UserName, admin_user, "")
| eval hour=strftime(_time, "%H")
| eval dow=strftime(_time, "%u")
| where (hour<7 OR hour>=19) OR dow IN ("6","7")
| stats count values(target_host) as targets by user
| sort -count
```

Step 3 — Validate
Compare with BeyondTrust session history in the vendor console for the same users, targets, and timestamps.

Step 4 — Operationalize
Add to a dashboard or alert; document the owner. Table (user × targets), timeline of off-hours sessions, pie (weekday vs weekend).

## SPL

```spl
index=pam sourcetype="beyondtrust:session" earliest=-7d
| eval user=coalesce(user, UserName, admin_user, "")
| eval hour=strftime(_time, "%H")
| eval dow=strftime(_time, "%u")
| where (hour<7 OR hour>=19) OR dow IN ("6","7")
| stats count values(target_host) as targets by user
| sort -count
```

## Visualization

Table (user × targets), timeline of off-hours sessions, pie (weekday vs weekend).

## References

- [BeyondTrust Password Safe / Cloud Dashboard for Splunk](https://splunkbase.splunk.com/app/5574)
- [Splunk Lantern — privileged access monitoring patterns](https://lantern.splunk.com/)
