---
id: "2.6.5"
title: "Citrix Delivery Controller Service Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.5 · Citrix Delivery Controller Service Health

## Description

Citrix Delivery Controllers run multiple critical Windows services: Broker Service, Configuration Service, Host Service, Machine Creation Service, and others. If the Broker Service stops, no new sessions can be brokered. If both controllers in a site fail, the entire Citrix environment becomes unavailable. Monitoring service health on all controllers ensures rapid detection and failover.

## Value

Citrix Delivery Controllers run multiple critical Windows services: Broker Service, Configuration Service, Host Service, Machine Creation Service, and others. If the Broker Service stops, no new sessions can be brokered. If both controllers in a site fail, the entire Citrix environment becomes unavailable. Monitoring service health on all controllers ensures rapid detection and failover.

## Implementation

Deploy Splunk Universal Forwarder on all Delivery Controllers and monitor Windows System Event Log. Windows Event ID 7036 records service state changes ("entered the running/stopped state"). Track all Citrix-specific services. Alert immediately when any critical Citrix service enters the stopped state. Correlate across controllers — if the Broker Service stops on all controllers simultaneously, escalate as P1. Also monitor Event IDs 7031 (service crash) and 7034 (unexpected termination).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows.
• Ensure the following data sources are available: `index=xd_winevents` `sourcetype="WinEventLog:System"` fields `EventCode`, `service_name`, `service_state`, `host`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Splunk Universal Forwarder on all Delivery Controllers and monitor Windows System Event Log. Windows Event ID 7036 records service state changes ("entered the running/stopped state"). Track all Citrix-specific services. Alert immediately when any critical Citrix service enters the stopped state. Correlate across controllers — if the Broker Service stops on all controllers simultaneously, escalate as P1. Also monitor Event IDs 7031 (service crash) and 7034 (unexpected termination).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd_winevents sourcetype="WinEventLog:System" EventCode=7036
  (service_name="Citrix Broker Service" OR service_name="Citrix Configuration Service"
  OR service_name="Citrix Host Service" OR service_name="CitrixMachineCreationService"
  OR service_name="Citrix Storefront*")
| eval status=if(match(Message, "running"), "Running", "Stopped")
| stats latest(status) as current_state, latest(_time) as last_change by host, service_name
| where current_state="Stopped"
| eval last_change_fmt=strftime(last_change, "%Y-%m-%d %H:%M:%S")
| table host, service_name, current_state, last_change_fmt
```

Understanding this SPL

**Citrix Delivery Controller Service Health** — Citrix Delivery Controllers run multiple critical Windows services: Broker Service, Configuration Service, Host Service, Machine Creation Service, and others. If the Broker Service stops, no new sessions can be brokered. If both controllers in a site fail, the entire Citrix environment becomes unavailable. Monitoring service health on all controllers ensures rapid detection and failover.

Documented **Data sources**: `index=xd_winevents` `sourcetype="WinEventLog:System"` fields `EventCode`, `service_name`, `service_state`, `host`. **App/TA** (typical add-on context): Splunk Add-on for Microsoft Windows. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd_winevents; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd_winevents, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, service_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where current_state="Stopped"` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **last_change_fmt** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Citrix Delivery Controller Service Health**): table host, service_name, current_state, last_change_fmt


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (service x controller), Timeline (state change events), Table (stopped services).

## SPL

```spl
index=xd_winevents sourcetype="WinEventLog:System" EventCode=7036
  (service_name="Citrix Broker Service" OR service_name="Citrix Configuration Service"
  OR service_name="Citrix Host Service" OR service_name="CitrixMachineCreationService"
  OR service_name="Citrix Storefront*")
| eval status=if(match(Message, "running"), "Running", "Stopped")
| stats latest(status) as current_state, latest(_time) as last_change by host, service_name
| where current_state="Stopped"
| eval last_change_fmt=strftime(last_change, "%Y-%m-%d %H:%M:%S")
| table host, service_name, current_state, last_change_fmt
```

## Visualization

Status grid (service x controller), Timeline (state change events), Table (stopped services).

## References

- [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742)
