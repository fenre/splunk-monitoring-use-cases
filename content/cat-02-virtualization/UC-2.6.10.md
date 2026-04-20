---
id: "2.6.10"
title: "Citrix StoreFront Authentication and Enumeration Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.10 · Citrix StoreFront Authentication and Enumeration Health

## Description

Citrix StoreFront authenticates users and enumerates available applications and desktops before the session launch process even begins. StoreFront failures manifest as users seeing a blank application list or receiving authentication errors. Since StoreFront runs on IIS, monitoring IIS response codes, authentication success rates, and enumeration latency provides early warning of issues that block all user access.

## Value

Citrix StoreFront authenticates users and enumerates available applications and desktops before the session launch process even begins. StoreFront failures manifest as users seeing a blank application list or receiving authentication errors. Since StoreFront runs on IIS, monitoring IIS response codes, authentication success rates, and enumeration latency provides early warning of issues that block all user access.

## Implementation

Install the Splunk Add-on for Microsoft IIS on StoreFront servers. StoreFront uses a custom IIS log field order — adjust the `auto_kv_for_iis_default` transform field list per Splunk's Content Pack documentation. Monitor HTTP status codes: 401 (authentication failure), 500+ (server errors), and response times. Key URIs to track: `/Citrix/StoreWeb/` (web interface), `/Citrix/Store/resources/` (resource enumeration), `/Citrix/Authentication/` (auth endpoint). Alert on server error rate exceeding 5% or authentication failure rate exceeding 20%. Correlate StoreFront errors with Active Directory health and Delivery Controller connectivity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft IIS.
• Ensure the following data sources are available: `index=xd` `sourcetype="ms:iis:auto"` fields `cs_uri_stem`, `sc_status`, `time_taken`, `cs_username`, `s_computername`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install the Splunk Add-on for Microsoft IIS on StoreFront servers. StoreFront uses a custom IIS log field order — adjust the `auto_kv_for_iis_default` transform field list per Splunk's Content Pack documentation. Monitor HTTP status codes: 401 (authentication failure), 500+ (server errors), and response times. Key URIs to track: `/Citrix/StoreWeb/` (web interface), `/Citrix/Store/resources/` (resource enumeration), `/Citrix/Authentication/` (auth endpoint). Alert on server error rate exceeding 5…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="ms:iis:auto" s_sitename="*StoreFront*"
| bin _time span=5m
| stats sum(eval(if(sc_status>=500, 1, 0))) as server_errors,
  sum(eval(if(sc_status=401, 1, 0))) as auth_failures,
  sum(eval(if(sc_status>=200 AND sc_status<400, 1, 0))) as success,
  avg(time_taken) as avg_response_ms, count as total by s_computername, _time
| eval error_pct=round(server_errors/total*100,1)
| eval auth_fail_pct=round(auth_failures/total*100,1)
| where error_pct > 5 OR auth_fail_pct > 20 OR avg_response_ms > 5000
| table _time, s_computername, total, success, server_errors, error_pct, auth_failures, auth_fail_pct, avg_response_ms
```

Understanding this SPL

**Citrix StoreFront Authentication and Enumeration Health** — Citrix StoreFront authenticates users and enumerates available applications and desktops before the session launch process even begins. StoreFront failures manifest as users seeing a blank application list or receiving authentication errors. Since StoreFront runs on IIS, monitoring IIS response codes, authentication success rates, and enumeration latency provides early warning of issues that block all user access.

Documented **Data sources**: `index=xd` `sourcetype="ms:iis:auto"` fields `cs_uri_stem`, `sc_status`, `time_taken`, `cs_username`, `s_computername`. **App/TA** (typical add-on context): Splunk Add-on for Microsoft IIS. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: ms:iis:auto. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="ms:iis:auto". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by s_computername, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **error_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **auth_fail_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_pct > 5 OR auth_fail_pct > 20 OR avg_response_ms > 5000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix StoreFront Authentication and Enumeration Health**): table _time, s_computername, total, success, server_errors, error_pct, auth_failures, auth_fail_pct, avg_response_ms

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=5m | sort - count
```

Understanding this CIM / accelerated SPL

**Citrix StoreFront Authentication and Enumeration Health** — Citrix StoreFront authenticates users and enumerates available applications and desktops before the session launch process even begins. StoreFront failures manifest as users seeing a blank application list or receiving authentication errors. Since StoreFront runs on IIS, monitoring IIS response codes, authentication success rates, and enumeration latency provides early warning of issues that block all user access.

Documented **Data sources**: `index=xd` `sourcetype="ms:iis:auto"` fields `cs_uri_stem`, `sc_status`, `time_taken`, `cs_username`, `s_computername`. **App/TA** (typical add-on context): Splunk Add-on for Microsoft IIS. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (requests by status code), Bar chart (error rates by StoreFront server), Table (slowest requests).

## SPL

```spl
index=xd sourcetype="ms:iis:auto" s_sitename="*StoreFront*"
| bin _time span=5m
| stats sum(eval(if(sc_status>=500, 1, 0))) as server_errors,
  sum(eval(if(sc_status=401, 1, 0))) as auth_failures,
  sum(eval(if(sc_status>=200 AND sc_status<400, 1, 0))) as success,
  avg(time_taken) as avg_response_ms, count as total by s_computername, _time
| eval error_pct=round(server_errors/total*100,1)
| eval auth_fail_pct=round(auth_failures/total*100,1)
| where error_pct > 5 OR auth_fail_pct > 20 OR avg_response_ms > 5000
| table _time, s_computername, total, success, server_errors, error_pct, auth_failures, auth_fail_pct, avg_response_ms
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=5m | sort - count
```

## Visualization

Timechart (requests by status code), Bar chart (error rates by StoreFront server), Table (slowest requests).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
