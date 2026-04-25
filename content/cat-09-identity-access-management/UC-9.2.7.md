<!-- AUTO-GENERATED from UC-9.2.7.json — DO NOT EDIT -->

---
id: "9.2.7"
title: "Bind Failure Rate Spikes"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.2.7 · Bind Failure Rate Spikes

## Description

Elevated invalid credential rates often precede password spraying or application misconfiguration; complements per-event bind failure monitoring.

## Value

Elevated invalid credential rates often precede password spraying or application misconfiguration; complements per-event bind failure monitoring.

## Implementation

Tune threshold to environment. Whitelist scanners and load balancers. Correlate with account lockouts and Entra hybrid sign-in failures if applicable.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Syslog, LDAP server logs.
• Ensure the following data sources are available: OpenLDAP syslog (err=49), AD DS LDAP interface events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tune threshold to environment. Whitelist scanners and load balancers. Correlate with account lockouts and Entra hybrid sign-in failures if applicable.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ldap sourcetype="syslog" "BIND" ("err=49" OR "data 52e")
| bin _time span=15m
| stats count by src, _time
| where count > 50
| sort -count
```

Understanding this SPL

**Bind Failure Rate Spikes** — Elevated invalid credential rates often precede password spraying or application misconfiguration; complements per-event bind failure monitoring.

Documented **Data sources**: OpenLDAP syslog (err=49), AD DS LDAP interface events. **App/TA** (typical add-on context): Syslog, LDAP server logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ldap; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=ldap, sourcetype="syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by src, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 50` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src span=15m | sort - count
```

Understanding this CIM / accelerated SPL

**Bind Failure Rate Spikes** — Elevated invalid credential rates often precede password spraying or application misconfiguration; complements per-event bind failure monitoring.

Documented **Data sources**: OpenLDAP syslog (err=49), AD DS LDAP interface events. **App/TA** (typical add-on context): Syslog, LDAP server logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with the directory server’s admin or audit view (bind DNs, result codes) for the same time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (bind failure rate), Table (source IP, window count), Single value (spikes per day).

## SPL

```spl
index=ldap sourcetype="syslog" "BIND" ("err=49" OR "data 52e")
| bin _time span=15m
| stats count by src, _time
| where count > 50
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src span=15m | sort - count
```

## Visualization

Line chart (bind failure rate), Table (source IP, window count), Single value (spikes per day).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
