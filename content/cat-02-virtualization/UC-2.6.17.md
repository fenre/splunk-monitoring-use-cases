<!-- AUTO-GENERATED from UC-2.6.17.json — DO NOT EDIT -->

---
id: "2.6.17"
title: "uberAgent Experience Score Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.17 · uberAgent Experience Score Monitoring

## Description

uberAgent's Experience Score is a composite 0–10 metric that summarises the end-user experience across multiple dimensions — session responsiveness, application performance, logon speed, and machine health. A single score per user per session makes it possible to answer "how is the Citrix experience right now?" without inspecting dozens of individual metrics. Score drops correlate directly with helpdesk call volume.

## Value

uberAgent's Experience Score is a composite 0–10 metric that summarises the end-user experience across multiple dimensions — session responsiveness, application performance, logon speed, and machine health. A single score per user per session makes it possible to answer "how is the Citrix experience right now?" without inspecting dozens of individual metrics. Score drops correlate directly with helpdesk call volume.

## Implementation

uberAgent UXM calculates Experience Scores via saved searches that run every 30 minutes on the search head, evaluating machine, session, and application health. Scores are stored in the `score_uberagent_uxm` index. No additional agent configuration is required beyond uberAgent deployment. Alert when the fleet-wide average drops below 4 (bad) or when p10 drops below 4. The score dashboard is the default entry point of the uberAgent UXM Splunk app. Score thresholds can be customised via lookup files (`score_machine_configuration.csv`, `score_session_configuration.csv`, `score_application_configuration.csv`).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448).
• Ensure the following data sources are available: `index=score_uberagent_uxm` — Experience Scores are calculated by saved searches on the search head and stored in a dedicated Splunk index..
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
uberAgent UXM calculates Experience Scores via saved searches that run every 30 minutes on the search head, evaluating machine, session, and application health. Scores are stored in the `score_uberagent_uxm` index. No additional agent configuration is required beyond uberAgent deployment. Alert when the fleet-wide average drops below 4 (bad) or when p10 drops below 4. The score dashboard is the default entry point of the uberAgent UXM Splunk app. Score thresholds can be customised via lookup fil…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=score_uberagent_uxm earliest=-4h
| search ScoreType="overall"
| bin _time span=30m
| stats avg(Score) as avg_score perc10(Score) as p10_score dc(Host) as hosts by _time
| eval quality=case(avg_score>=7, "Good", avg_score>=4, "Medium", 1=1, "Bad")
| table _time, avg_score, p10_score, hosts, quality
```

Understanding this SPL

**uberAgent Experience Score Monitoring** — uberAgent's Experience Score is a composite 0–10 metric that summarises the end-user experience across multiple dimensions — session responsiveness, application performance, logon speed, and machine health. A single score per user per session makes it possible to answer "how is the Citrix experience right now?" without inspecting dozens of individual metrics. Score drops correlate directly with helpdesk call volume.

Documented **Data sources**: `index=score_uberagent_uxm` — Experience Scores are calculated by saved searches on the search head and stored in a dedicated Splunk index. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: score_uberagent_uxm.

**Pipeline walkthrough**

• Scopes the data: index=score_uberagent_uxm, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **quality** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **uberAgent Experience Score Monitoring**): table _time, avg_score, p10_score, hosts, quality

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (score over time), Gauge (fleet average), Heatmap (delivery group x hour), Table (worst-scoring users).

## SPL

```spl
index=score_uberagent_uxm earliest=-4h
| search ScoreType="overall"
| bin _time span=30m
| stats avg(Score) as avg_score perc10(Score) as p10_score dc(Host) as hosts by _time
| eval quality=case(avg_score>=7, "Good", avg_score>=4, "Medium", 1=1, "Bad")
| table _time, avg_score, p10_score, hosts, quality
```

## Visualization

Line chart (score over time), Gauge (fleet average), Heatmap (delivery group x hour), Table (worst-scoring users).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
