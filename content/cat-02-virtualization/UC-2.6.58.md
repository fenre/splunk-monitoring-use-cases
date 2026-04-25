<!-- AUTO-GENERATED from UC-2.6.58.json — DO NOT EDIT -->

---
id: "2.6.58"
title: "Citrix Analytics for Performance Data Export"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.58 · Citrix Analytics for Performance Data Export

## Description

Citrix Analytics for Performance scores sessions and surfaces machine and session lifecycle events with modeled user-experience metrics. When those streams land in a dedicated index, you can trend score regressions by delivery group, catch rising ICA round trip before the help desk floods, and separate image issues from home-network problems. This use case focuses on continuous performance observability and capacity-driven tuning, not on raw security forensics (see related security export use case).

## Value

Citrix Analytics for Performance scores sessions and surfaces machine and session lifecycle events with modeled user-experience metrics. When those streams land in a dedicated index, you can trend score regressions by delivery group, catch rising ICA round trip before the help desk floods, and separate image issues from home-network problems. This use case focuses on continuous performance observability and capacity-driven tuning, not on raw security forensics (see related security export use case).

## Implementation

Complete Citrix Cloud onboarding for Analytics, enable the Performance export, and install Splunkbase 6280 on a test search head. Map exported fields to a stable schema: prefer `user_principal` and `session_id` as join keys. Build baseline weekly medians of UX score and logon time per app group. Alert on a sustained drop in median score (for example 15 points for two hours) or on percentile shifts of ICA RTT. Route reports to EUC and network teams. Mask or hash identifiers if exports leave regulated regions. Keep raw exports within retention that matches your DLP policy.

## Detailed Implementation

Prerequisites
• Citrix Cloud entitlement for Analytics; data export permissions; Splunkbase app 6280 installed with correct credentials and index routing (for example `index=citrix`).
• Field extraction verified on `citrix:analytics:performance` for scores and durations.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Validate event volume and sampling; if volume is high, sample heavy dashboards to five-minute rollups. Document field synonyms your tenant uses (some orgs customize labels).

Step 2 — Create the search and alert
Start with a weekly report before paging; tune thresholds with two weeks of data. Add suppressions for image rollout windows using a change calendar lookup.

Step 3 — Validate
Compare a handful of poor-score sessions in this index with the Citrix Cloud UI for the same `session_id` to confirm mapping.

Step 4 — Operationalize
Publish an executive one-page on median score trend; tie to golden-image releases and autoscale events.

## SPL

```spl
index=citrix sourcetype="citrix:analytics:performance"
| eval score=tonumber(coalesce(ux_score, user_experience_score, session_score, -1))
| eval rtt=tonumber(coalesce(ica_rtt, round_trip_ms, 0))
| eval logon=tonumber(coalesce(logon_duration_ms, logon_ms, 0))
| where (score>0 AND score<70) OR rtt>300 OR logon>15000
| eval reason=case(score>0 AND score<70, "low_ux_score", rtt>300, "high_ica_rtt", logon>15000, "slow_logon", true(), "other")
| timechart span=1h count by reason, user_principal
| fillnull value=0
```

## Visualization

Time chart of median UX score by delivery group; scatter of logon time versus ICA RTT; table of worst sessions in the last hour with drill to machine name and region.

## References

- [Citrix Analytics Add-on for Splunk (Splunkbase 6280)](https://splunkbase.splunk.com/app/6280)
- [Citrix Analytics for Performance (overview)](https://docs.citrix.com/en-us/citrix-analytics/performance.html)
