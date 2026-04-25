<!-- AUTO-GENERATED from UC-5.3.2.json — DO NOT EDIT -->

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

Step 3 — Validate
In the F5 Configuration utility or tmsh, check the same virtual servers, listeners, and status for the search window and compare to Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator per VIP, Events timeline (critical).

## SPL

```spl
index=network sourcetype="f5:bigip:syslog" "virtual" ("disabled" OR "offline" OR "unavailable")
| table _time host virtual_server status | sort -_time
```

## Visualization

Status indicator per VIP, Events timeline (critical).

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
