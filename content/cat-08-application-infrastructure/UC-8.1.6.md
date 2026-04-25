<!-- AUTO-GENERATED from UC-8.1.6.json — DO NOT EDIT -->

---
id: "8.1.6"
title: "Upstream Backend Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.6 · Upstream Backend Health

## Description

Backend server failures behind reverse proxies cause partial service degradation. Detection enables rapid failover response.

## Value

Backend server failures behind reverse proxies cause partial service degradation. Detection enables rapid failover response.

## Implementation

Forward NGINX error logs. Parse upstream failure messages. For HAProxy, enable stats socket and poll via scripted input. Alert on backend server failures. Track backend health state over time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-nginx` (error logs), HAProxy stats.
• Ensure the following data sources are available: NGINX error logs (upstream errors), HAProxy stats socket, F5 pool member logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward NGINX error logs. Parse upstream failure messages. For HAProxy, enable stats socket and poll via scripted input. Alert on backend server failures. Track backend health state over time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="nginx:error"
| search "upstream" ("connect() failed" OR "no live upstreams" OR "timed out")
| stats count by upstream_addr, server_name
| sort -count
```

Understanding this SPL

**Upstream Backend Health** — Backend server failures behind reverse proxies cause partial service degradation. Detection enables rapid failover response.

Documented **Data sources**: NGINX error logs (upstream errors), HAProxy stats socket, F5 pool member logs. **App/TA** (typical add-on context): `TA-nginx` (error logs), HAProxy stats. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: nginx:error. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="nginx:error". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by upstream_addr, server_name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (backend × health), Table (failed backends), Timeline (backend failure events).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=web sourcetype="nginx:error"
| search "upstream" ("connect() failed" OR "no live upstreams" OR "timed out")
| stats count by upstream_addr, server_name
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=502 AND Web.status<=504
  by Web.dest Web.uri_path span=5m
| sort -count
```

## Visualization

Status grid (backend × health), Table (failed backends), Timeline (backend failure events).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
