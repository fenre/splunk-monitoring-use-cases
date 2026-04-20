---
id: "9.4.15"
title: "Privileged Session Duration Anomalies"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.15 · Privileged Session Duration Anomalies

## Description

Sessions far longer than peer baseline may indicate data exfiltration or abandoned hijacked sessions.

## Value

Sessions far longer than peer baseline may indicate data exfiltration or abandoned hijacked sessions.

## Implementation

Baseline duration per target system type. Exclude known maintenance windows via lookup. Pair with UC-9.4.1 audit trail.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CyberArk / BeyondTrust session logs.
• Ensure the following data sources are available: PAM session start/end with duration.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline duration per target system type. Exclude known maintenance windows via lookup. Pair with UC-9.4.1 audit trail.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:session"
| eval dur_min=duration_sec/60
| eventstats median(dur_min) as med by target_account
| where dur_min > med*3 AND dur_min > 60
| table _time, user, target_account, dur_min, med
```

Understanding this SPL

**Privileged Session Duration Anomalies** — Sessions far longer than peer baseline may indicate data exfiltration or abandoned hijacked sessions.

Documented **Data sources**: PAM session start/end with duration. **App/TA** (typical add-on context): CyberArk / BeyondTrust session logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:session. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:session". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **dur_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eventstats` rolls up events into metrics; results are split **by target_account** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where dur_min > med*3 AND dur_min > 60` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Privileged Session Duration Anomalies**): table _time, user, target_account, dur_min, med

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Privileged Session Duration Anomalies** — Sessions far longer than peer baseline may indicate data exfiltration or abandoned hijacked sessions.

Documented **Data sources**: PAM session start/end with duration. **App/TA** (typical add-on context): CyberArk / BeyondTrust session logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (long sessions), Box plot (duration by target), Line chart (max duration trend).

## SPL

```spl
index=pam sourcetype="cyberark:session"
| eval dur_min=duration_sec/60
| eventstats median(dur_min) as med by target_account
| where dur_min > med*3 AND dur_min > 60
| table _time, user, target_account, dur_min, med
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (long sessions), Box plot (duration by target), Line chart (max duration trend).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
