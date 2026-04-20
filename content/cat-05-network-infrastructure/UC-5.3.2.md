---
id: "5.3.2"
title: "Virtual Server Availability (F5 BIG-IP)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.2 · Virtual Server Availability (F5 BIG-IP)

## Description

VIP down = application unreachable. Direct service impact.

## Value

VIP down = application unreachable. Direct service impact.

## Implementation

Forward syslog. Monitor VIP status via SNMP or iControl REST. Alert on any state change away from "available".

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip`, SNMP.
• Ensure the following data sources are available: `sourcetype=f5:bigip:syslog`, iControl REST.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog. Monitor VIP status via SNMP or iControl REST. Alert on any state change away from "available".

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:syslog" "virtual" ("disabled" OR "offline" OR "unavailable")
| table _time host virtual_server status | sort -_time
```

Understanding this SPL

**Virtual Server Availability (F5 BIG-IP)** — VIP down = application unreachable. Direct service impact.

Documented **Data sources**: `sourcetype=f5:bigip:syslog`, iControl REST. **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`, SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Virtual Server Availability (F5 BIG-IP)**): table _time host virtual_server status
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Virtual Server Availability (F5 BIG-IP)** — VIP down = application unreachable. Direct service impact.

Documented **Data sources**: `sourcetype=f5:bigip:syslog`, iControl REST. **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`, SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator per VIP, Events timeline (critical).

## SPL

```spl
index=network sourcetype="f5:bigip:syslog" "virtual" ("disabled" OR "offline" OR "unavailable")
| table _time host virtual_server status | sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

## Visualization

Status indicator per VIP, Events timeline (critical).

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
