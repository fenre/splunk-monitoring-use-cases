<!-- AUTO-GENERATED from UC-5.3.17.json — DO NOT EDIT -->

---
id: "5.3.17"
title: "Citrix ADC GSLB Site and Service Health (NetScaler)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.17 · Citrix ADC GSLB Site and Service Health (NetScaler)

## Description

Global Server Load Balancing (GSLB) distributes traffic across multiple data centers based on proximity, health, and load. GSLB relies on the Metric Exchange Protocol (MEP) between sites to share health and load metrics. If MEP connectivity fails between sites, the GSLB method falls back to Round Robin — potentially sending users to degraded or distant sites. Monitoring GSLB site health and MEP status ensures intelligent multi-site traffic distribution.

## Value

Global Server Load Balancing (GSLB) distributes traffic across multiple data centers based on proximity, health, and load. GSLB relies on the Metric Exchange Protocol (MEP) between sites to share health and load metrics. If MEP connectivity fails between sites, the GSLB method falls back to Round Robin — potentially sending users to degraded or distant sites. Monitoring GSLB site health and MEP status ensures intelligent multi-site traffic distribution.

## Implementation

The ADC logs GSLB service state changes and MEP connectivity events via syslog. MEP runs on TCP ports 3011 (standard) or 3009 (secure) between GSLB sites. Additionally, poll the NITRO API `gslbsite` and `gslbservice` resources for site status, MEP status, and GSLB service health. Alert on: any GSLB service going DOWN, MEP status changing to DOWN between any pair of sites (fallback to Round Robin), and GSLB site becoming unreachable. When MEP fails, all GSLB decisions for that site pair become unaware of the remote site's health — traffic may be sent to a degraded or offline site.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), NITRO API scripted input.
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `gslb_site`, `gslb_service`, `mep_status`, `site_ip`, `service_state`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The ADC logs GSLB service state changes and MEP connectivity events via syslog. MEP runs on TCP ports 3011 (standard) or 3009 (secure) between GSLB sites. Additionally, poll the NITRO API `gslbsite` and `gslbservice` resources for site status, MEP status, and GSLB service health. Alert on: any GSLB service going DOWN, MEP status changing to DOWN between any pair of sites (fallback to Round Robin), and GSLB site becoming unreachable. When MEP fails, all GSLB decisions for that site pair become un…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:syslog" ("GSLB" OR "MEP") ("DOWN" OR "UP" OR "disabled")
| rex "GSLB (?:site|service) (?<gslb_entity>\S+).*State (?<state>\w+)"
| where state="DOWN" OR match(_raw, "MEP.*DOWN")
| bin _time span=5m
| stats count as events, latest(state) as current_state by gslb_entity, host, _time
| table _time, gslb_entity, current_state, events, host
```

Understanding this SPL

**Citrix ADC GSLB Site and Service Health (NetScaler)** — Global Server Load Balancing (GSLB) distributes traffic across multiple data centers based on proximity, health, and load. GSLB relies on the Metric Exchange Protocol (MEP) between sites to share health and load metrics. If MEP connectivity fails between sites, the GSLB method falls back to Round Robin — potentially sending users to degraded or distant sites. Monitoring GSLB site health and MEP status ensures intelligent multi-site traffic distribution.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `gslb_site`, `gslb_service`, `mep_status`, `site_ip`, `service_state`. **App/TA** (typical add-on context): Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), NITRO API scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where state="DOWN" OR match(_raw, "MEP.*DOWN")` — typically the threshold or rule expression for this monitoring goal.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by gslb_entity, host, _time** so each row reflects one combination of those dimensions.
• Pipeline stage (see **Citrix ADC GSLB Site and Service Health (NetScaler)**): table _time, gslb_entity, current_state, events, host


Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (GSLB site x MEP status), Table (DOWN GSLB services), Timeline (GSLB state changes).

## SPL

```spl
index=network sourcetype="citrix:netscaler:syslog" ("GSLB" OR "MEP") ("DOWN" OR "UP" OR "disabled")
| rex "GSLB (?:site|service) (?<gslb_entity>\S+).*State (?<state>\w+)"
| where state="DOWN" OR match(_raw, "MEP.*DOWN")
| bin _time span=5m
| stats count as events, latest(state) as current_state by gslb_entity, host, _time
| table _time, gslb_entity, current_state, events, host
```

## Visualization

Status grid (GSLB site x MEP status), Table (DOWN GSLB services), Timeline (GSLB state changes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
