---
id: "9.2.6"
title: "LDAP Query Volume Anomalies"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.2.6 · LDAP Query Volume Anomalies

## Description

Sudden spikes in LDAP searches may indicate reconnaissance, brute enumeration, or misbehaving applications hammering directory services.

## Value

Sudden spikes in LDAP searches may indicate reconnaissance, brute enumeration, or misbehaving applications hammering directory services.

## Implementation

Baseline searches per source per interval. Alert on statistical outliers. Correlate with known ETL jobs via lookup. On AD, combine with 1644 expensive search events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: LDAP access log parsing, `Splunk_TA_windows` (Directory Service 1644).
• Ensure the following data sources are available: OpenLDAP access log (SEARCH count), AD DS expensive search / query stats.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline searches per source per interval. Alert on statistical outliers. Correlate with known ETL jobs via lookup. On AD, combine with 1644 expensive search events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ldap sourcetype="openldap:access" operation="SEARCH"
| bin _time span=15m
| stats count by src, _time
| eventstats median(count) as med by src
| where count > med*10 AND count > 100
| sort -count
```

Understanding this SPL

**LDAP Query Volume Anomalies** — Sudden spikes in LDAP searches may indicate reconnaissance, brute enumeration, or misbehaving applications hammering directory services.

Documented **Data sources**: OpenLDAP access log (SEARCH count), AD DS expensive search / query stats. **App/TA** (typical add-on context): LDAP access log parsing, `Splunk_TA_windows` (Directory Service 1644). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ldap; **sourcetype**: openldap:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ldap, sourcetype="openldap:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by src, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > med*10 AND count > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src span=15m | sort - count
```

Understanding this CIM / accelerated SPL

**LDAP Query Volume Anomalies** — Sudden spikes in LDAP searches may indicate reconnaissance, brute enumeration, or misbehaving applications hammering directory services.

Documented **Data sources**: OpenLDAP access log (SEARCH count), AD DS expensive search / query stats. **App/TA** (typical add-on context): LDAP access log parsing, `Splunk_TA_windows` (Directory Service 1644). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (query volume by source), Table (spikes), Bar chart (top talkers).

## SPL

```spl
index=ldap sourcetype="openldap:access" operation="SEARCH"
| bin _time span=15m
| stats count by src, _time
| eventstats median(count) as med by src
| where count > med*10 AND count > 100
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src span=15m | sort - count
```

## Visualization

Line chart (query volume by source), Table (spikes), Bar chart (top talkers).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
