<!-- AUTO-GENERATED from UC-9.2.12.json — DO NOT EDIT -->

---
id: "9.2.12"
title: "LDAP Referral Chaining Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.2.12 · LDAP Referral Chaining Monitoring

## Description

Excessive or looping referrals degrade auth and may indicate misconfigured base DNs or cross-domain abuse.

## Value

Excessive or looping referrals degrade auth and may indicate misconfigured base DNs or cross-domain abuse.

## Implementation

Parse referral responses in access logs. Baseline per app. Alert on referral storms or new referral targets. Correlate with GSSAPI/SASL cross-realm issues in hybrid setups.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OpenLDAP / 389 DS access logs, AD debug (optional).
• Ensure the following data sources are available: LDAP access log lines containing `REFERRAL` or `v3 referral`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse referral responses in access logs. Baseline per app. Alert on referral storms or new referral targets. Correlate with GSSAPI/SASL cross-realm issues in hybrid setups.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ldap sourcetype="openldap:access" (message="REFERRAL" OR like(_raw,"%referral%"))
| stats count, values(dn) as refs by src, base
| where count > 20
| sort -count
```

Understanding this SPL

**LDAP Referral Chaining Monitoring** — Excessive or looping referrals degrade auth and may indicate misconfigured base DNs or cross-domain abuse.

Documented **Data sources**: LDAP access log lines containing `REFERRAL` or `v3 referral`. **App/TA** (typical add-on context): OpenLDAP / 389 DS access logs, AD debug (optional). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ldap; **sourcetype**: openldap:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ldap, sourcetype="openldap:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by src, base** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**LDAP Referral Chaining Monitoring** — Excessive or looping referrals degrade auth and may indicate misconfigured base DNs or cross-domain abuse.

Documented **Data sources**: LDAP access log lines containing `REFERRAL` or `v3 referral`. **App/TA** (typical add-on context): OpenLDAP / 389 DS access logs, AD debug (optional). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with the directory server’s admin or audit view (bind DNs, result codes) for the same time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (referral chains), Line chart (referral volume), Bar chart (by base DN).

## SPL

```spl
index=ldap sourcetype="openldap:access" (message="REFERRAL" OR like(_raw,"%referral%"))
| stats count, values(dn) as refs by src, base
| where count > 20
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src | sort - count
```

## Visualization

Table (referral chains), Line chart (referral volume), Bar chart (by base DN).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
