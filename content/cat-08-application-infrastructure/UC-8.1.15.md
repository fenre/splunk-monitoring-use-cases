---
id: "8.1.15"
title: "HAProxy Backend Health State"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.15 · HAProxy Backend Health State

## Description

CSV stats `status` (UP/DOWN/MAINT) per server line with weight. Distinct from UC-8.1.6 NGINX-only upstream errors for HAProxy-native shops.

## Value

CSV stats `status` (UP/DOWN/MAINT) per server line with weight. Distinct from UC-8.1.6 NGINX-only upstream errors for HAProxy-native shops.

## Implementation

Poll stats every 30s. Alert on any backend DOWN not in maintenance window. Track flapping (status changes >3 in 10m).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: HAProxy stats socket scripted input.
• Ensure the following data sources are available: `haproxy:stats` `svname`, `status`, `chkfail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll stats every 30s. Alert on any backend DOWN not in maintenance window. Track flapping (status changes >3 in 10m).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=haproxy sourcetype="haproxy:stats" type=server
| where status!="UP" OR chkfail > 0
| stats latest(status) as status, sum(chkfail) as fails by pxname, svname
| sort fails
```

Understanding this SPL

**HAProxy Backend Health State** — CSV stats `status` (UP/DOWN/MAINT) per server line with weight. Distinct from UC-8.1.6 NGINX-only upstream errors for HAProxy-native shops.

Documented **Data sources**: `haproxy:stats` `svname`, `status`, `chkfail`. **App/TA** (typical add-on context): HAProxy stats socket scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: haproxy; **sourcetype**: haproxy:stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=haproxy, sourcetype="haproxy:stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status!="UP" OR chkfail > 0` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by pxname, svname** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t sum(Web.status) as agg_value from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - agg_value
```

Understanding this CIM / accelerated SPL

**HAProxy Backend Health State** — CSV stats `status` (UP/DOWN/MAINT) per server line with weight. Distinct from UC-8.1.6 NGINX-only upstream errors for HAProxy-native shops.

Documented **Data sources**: `haproxy:stats` `svname`, `status`, `chkfail`. **App/TA** (typical add-on context): HAProxy stats socket scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (backend × UP/DOWN), Table (DOWN servers), Timeline (state changes).

## SPL

```spl
index=haproxy sourcetype="haproxy:stats" type=server
| where status!="UP" OR chkfail > 0
| stats latest(status) as status, sum(chkfail) as fails by pxname, svname
| sort fails
```

## CIM SPL

```spl
| tstats summariesonly=t sum(Web.status) as agg_value from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - agg_value
```

## Visualization

Status grid (backend × UP/DOWN), Table (DOWN servers), Timeline (state changes).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
