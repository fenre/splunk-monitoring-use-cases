<!-- AUTO-GENERATED from UC-9.7.3.json — DO NOT EDIT -->

---
id: "9.7.3"
title: "Privileged Account Activity Trending"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.7.3 · Privileged Account Activity Trending

## Description

Privileged logon volume should be relatively stable; spikes can indicate credential theft, mass admin activity during an incident, or automation run amok. Trending over thirty days highlights gradual increases that point-in-time thresholds miss.

## Value

Privileged logon volume should be relatively stable; spikes can indicate credential theft, mass admin activity during an incident, or automation run amok. Trending over thirty days highlights gradual increases that point-in-time thresholds miss.

## Implementation

Build `privileged_users.csv` from Active Directory privileged groups, cloud Global Administrator roles, and break-glass accounts; refresh on a schedule. Require `Authentication.action='success'` to measure real sessions. Investigate sustained upward trends with parallel searches on source IP and workstation. Pair with change tickets to expected elevation work.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`).
• Ensure the following data sources are available: `Authentication` data model; `privileged_users.csv` lookup (user, is_privileged) aligned with `Authentication.user`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Build `privileged_users.csv` from Active Directory privileged groups, cloud Global Administrator roles, and break-glass accounts; refresh on a schedule. Require `Authentication.action='success'` to measure real sessions. Investigate sustained upward trends with parallel searches on source IP and workstation. Pair with change tickets to expected elevation work.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where earliest=-30d@d latest=@d Authentication.action='success'
  by _time span=1d Authentication.user
| lookup privileged_users user AS "Authentication.user" OUTPUT is_privileged
| where is_privileged="true"
| timechart span=1d sum(count) as privileged_logons
| trendline sma7(privileged_logons) as priv_sma7
| predict privileged_logons as priv_forecast algorithm=LLP future_timespan=7
```

Understanding this SPL

**Privileged Account Activity Trending** — Privileged logon volume should be relatively stable; spikes can indicate credential theft, mass admin activity during an incident, or automation run amok. Trending over thirty days highlights gradual increases that point-in-time thresholds miss.

Documented **Data sources**: `Authentication` data model; `privileged_users.csv` lookup (user, is_privileged) aligned with `Authentication.user`. **App/TA** (typical add-on context): Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where is_privileged="true"` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **Privileged Account Activity Trending**): trendline sma7(privileged_logons) as priv_sma7
• Pipeline stage (see **Privileged Account Activity Trending**): predict privileged_logons as priv_forecast algorithm=LLP future_timespan=7

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user span=1d | sort - count
```

Understanding this CIM / accelerated SPL

**Privileged Account Activity Trending** — Privileged logon volume should be relatively stable; spikes can indicate credential theft, mass admin activity during an incident, or automation run amok. Trending over thirty days highlights gradual increases that point-in-time thresholds miss.

Documented **Data sources**: `Authentication` data model; `privileged_users.csv` lookup (user, is_privileged) aligned with `Authentication.user`. **App/TA** (typical add-on context): Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare results with the authoritative identity source (directory, IdP, or PAM) for the same time range and with known change or maintenance tickets.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart of privileged_logons with SMA; anomaly overlay if using MLTK or `anomalydetection`.

## SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where earliest=-30d@d latest=@d Authentication.action='success'
  by _time span=1d Authentication.user
| lookup privileged_users user AS "Authentication.user" OUTPUT is_privileged
| where is_privileged="true"
| timechart span=1d sum(count) as privileged_logons
| trendline sma7(privileged_logons) as priv_sma7
| predict privileged_logons as priv_forecast algorithm=LLP future_timespan=7
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user span=1d | sort - count
```

## Visualization

Line chart of privileged_logons with SMA; anomaly overlay if using MLTK or `anomalydetection`.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
