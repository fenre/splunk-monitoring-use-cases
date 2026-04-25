<!-- AUTO-GENERATED from UC-9.8.7.json — DO NOT EDIT -->

---
id: "9.8.7"
title: "BeyondTrust Remote Support Session Duration and Concurrent Analyst Trending"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-9.8.7 · BeyondTrust Remote Support Session Duration and Concurrent Analyst Trending

## Description

Support desks using BeyondTrust PRA must balance responsiveness with license consumption and supervisor oversight. Trending concurrent sessions and duration percentiles exposes understaffing, training issues, or potential session piggybacking.

## Value

Optimizes PRA licensing and staffing forecasts while surfacing unusual analyst behavior patterns for quality assurance.

## Implementation

(1) Normalize representative and customer fields across PRA editions. (2) Confirm `duration_min` or compute from start/end. (3) Use `perc95()` for session-duration percentiles (Splunk `stats`). (4) Segment internal IT vs vendor MSP accounts. (5) Review weekly with service desk management.

## SPL

```spl
index=pam sourcetype="beyondtrust:session" earliest=-24h
| eval rep=coalesce(rep_user, RepUser, analyst, technician, user, UserName, "")
| eval cust=coalesce(customer_id, Customer, end_user, "")
| eval dur_min=coalesce(duration_min, round(duration_sec/60,1), round((SessionDurationSeconds)/60,1))
| eval sess=coalesce(session_id, SessionID, "")
| bin _time span=15m
| stats dc(sess) as concurrent_sessions avg(dur_min) as avg_duration perc95(dur_min) as p95_duration by _time rep
| where concurrent_sessions>=3 OR p95_duration>90
| sort _time
```

## Visualization

Dual-axis line (concurrent sessions vs p95 duration), heatmap (rep × hour), table of peak intervals.

## References

- [BeyondTrust — Privileged Remote Access](https://www.beyondtrust.com/privileged-remote-access)
- [Splunk Docs — stats functions (percentiles)](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Commonstatsfunctions)
