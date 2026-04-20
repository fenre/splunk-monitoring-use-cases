---
id: "8.7.1"
title: "User Session Volume Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.7.1 · User Session Volume Trending

## Description

Daily or weekly active session counts show adoption, campaign effects, and capacity needs before saturation. Seasonal patterns become visible for staffing and infrastructure scale plans.

## Value

Daily or weekly active session counts show adoption, campaign effects, and capacity needs before saturation. Seasonal patterns become visible for staffing and infrastructure scale plans.

## Implementation

Prefer application-native session metrics if available (Spring session registry, .NET session state). Deduplicate proxies and bots with a known crawler user-agent lookup. For stateless APIs, substitute `dc(client_ip)` or OAuth `sub` as a proxy with documented caveats. Align time zones with business reporting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector / app instrumentation, Tomcat / IIS / NGINX TAs as applicable.
• Ensure the following data sources are available: `index=web` `sourcetype=access_combined`, `index=app` session or access logs, optional `JSESSIONID` / `session_id` fields.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Prefer application-native session metrics if available (Spring session registry, .NET session state). Deduplicate proxies and bots with a known crawler user-agent lookup. For stateless APIs, substitute `dc(client_ip)` or OAuth `sub` as a proxy with documented caveats. Align time zones with business reporting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web OR index=app (sourcetype=access_combined OR sourcetype="tomcat:access" OR sourcetype="iis:access")
| eval sid=coalesce(JSESSIONID, session_id, client_session)
| bin _time span=1d
| stats dc(sid) as approx_active_sessions by _time
| timechart span=1d sum(approx_active_sessions) as daily_sessions
```

Understanding this SPL

**User Session Volume Trending** — Daily or weekly active session counts show adoption, campaign effects, and capacity needs before saturation. Seasonal patterns become visible for staffing and infrastructure scale plans.

Documented **Data sources**: `index=web` `sourcetype=access_combined`, `index=app` session or access logs, optional `JSESSIONID` / `session_id` fields. **App/TA** (typical add-on context): Splunk OTel Collector / app instrumentation, Tomcat / IIS / NGINX TAs as applicable. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web, app; **sourcetype**: access_combined, tomcat:access, iis:access. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=web, index=app, sourcetype=access_combined. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **sid** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=1d | sort - count
```

Understanding this CIM / accelerated SPL

**User Session Volume Trending** — Daily or weekly active session counts show adoption, campaign effects, and capacity needs before saturation. Seasonal patterns become visible for staffing and infrastructure scale plans.

Documented **Data sources**: `index=web` `sourcetype=access_combined`, `index=app` session or access logs, optional `JSESSIONID` / `session_id` fields. **App/TA** (typical add-on context): Splunk OTel Collector / app instrumentation, Tomcat / IIS / NGINX TAs as applicable. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (daily sessions), column chart (week-over-week), single value (rolling 7-day average).

## SPL

```spl
index=web OR index=app (sourcetype=access_combined OR sourcetype="tomcat:access" OR sourcetype="iis:access")
| eval sid=coalesce(JSESSIONID, session_id, client_session)
| bin _time span=1d
| stats dc(sid) as approx_active_sessions by _time
| timechart span=1d sum(approx_active_sessions) as daily_sessions
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=1d | sort - count
```

## Visualization

Line chart (daily sessions), column chart (week-over-week), single value (rolling 7-day average).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
