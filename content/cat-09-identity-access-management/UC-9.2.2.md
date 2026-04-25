<!-- AUTO-GENERATED from UC-9.2.2.json — DO NOT EDIT -->

---
id: "9.2.2"
title: "Search Performance Degradation"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.2.2 · Search Performance Degradation

## Description

Slow LDAP searches impact all applications relying on directory services for authentication and authorization.

## Value

Slow LDAP searches impact all applications relying on directory services for authentication and authorization.

## Implementation

Enable LDAP access logging with timing information. Parse search operations with duration. Alert on searches exceeding 1 second. Identify expensive filters (unindexed attributes, broad base DN). Recommend index creation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: LDAP access log parsing.
• Ensure the following data sources are available: OpenLDAP access log (search duration), 389 Directory access log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable LDAP access logging with timing information. Parse search operations with duration. Alert on searches exceeding 1 second. Identify expensive filters (unindexed attributes, broad base DN). Recommend index creation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ldap sourcetype="openldap:access" operation="SEARCH"
| where elapsed_ms > 1000
| stats count, avg(elapsed_ms) as avg_ms by base_dn, filter
| sort -avg_ms
```

Understanding this SPL

**Search Performance Degradation** — Slow LDAP searches impact all applications relying on directory services for authentication and authorization.

Documented **Data sources**: OpenLDAP access log (search duration), 389 Directory access log. **App/TA** (typical add-on context): LDAP access log parsing. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ldap; **sourcetype**: openldap:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ldap, sourcetype="openldap:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where elapsed_ms > 1000` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by base_dn, filter** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with the directory server’s admin or audit view (bind DNs, result codes) for the same time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (slow searches), Bar chart (avg duration by filter), Line chart (search latency trend).

## SPL

```spl
index=ldap sourcetype="openldap:access" operation="SEARCH"
| where elapsed_ms > 1000
| stats count, avg(elapsed_ms) as avg_ms by base_dn, filter
| sort -avg_ms
```

## Visualization

Table (slow searches), Bar chart (avg duration by filter), Line chart (search latency trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
