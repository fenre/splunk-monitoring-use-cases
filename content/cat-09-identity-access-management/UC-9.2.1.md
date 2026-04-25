<!-- AUTO-GENERATED from UC-9.2.1.json — DO NOT EDIT -->

---
id: "9.2.1"
title: "Bind Failure Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.2.1 · Bind Failure Monitoring

## Description

LDAP bind failures indicate authentication issues, misconfigured applications, or brute-force attempts against directory services.

## Value

LDAP bind failures indicate authentication issues, misconfigured applications, or brute-force attempts against directory services.

## Implementation

Forward LDAP server syslog to Splunk. Parse bind operations and result codes (err=49 = invalid credentials). Alert on >10 failures per source per 15 minutes. Correlate with application health monitoring.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Syslog, LDAP server logs.
• Ensure the following data sources are available: OpenLDAP syslog, 389 Directory access log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward LDAP server syslog to Splunk. Parse bind operations and result codes (err=49 = invalid credentials). Alert on >10 failures per source per 15 minutes. Correlate with application health monitoring.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ldap sourcetype="syslog" "BIND" "err=49"
| stats count by src, bind_dn
| where count > 10
| sort -count
```

Understanding this SPL

**Bind Failure Monitoring** — LDAP bind failures indicate authentication issues, misconfigured applications, or brute-force attempts against directory services.

Documented **Data sources**: OpenLDAP syslog, 389 Directory access log. **App/TA** (typical add-on context): Syslog, LDAP server logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ldap; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=ldap, sourcetype="syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, bind_dn** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action='failure'
  by Authentication.user Authentication.src span=1h
| where count > 10
```

Understanding this CIM / accelerated SPL

**Bind Failure Monitoring** — LDAP bind failures indicate authentication issues, misconfigured applications, or brute-force attempts against directory services.

Documented **Data sources**: OpenLDAP syslog, 389 Directory access log. **App/TA** (typical add-on context): Syslog, LDAP server logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with the directory server’s admin or audit view (bind DNs, result codes) for the same time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (bind failures by source/DN), Line chart (failure rate), Bar chart (top failing sources).

## SPL

```spl
index=ldap sourcetype="syslog" "BIND" "err=49"
| stats count by src, bind_dn
| where count > 10
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action='failure'
  by Authentication.user Authentication.src span=1h
| where count > 10
```

## Visualization

Table (bind failures by source/DN), Line chart (failure rate), Bar chart (top failing sources).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
