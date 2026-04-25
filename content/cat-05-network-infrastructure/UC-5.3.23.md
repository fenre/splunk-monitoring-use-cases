<!-- AUTO-GENERATED from UC-5.3.23.json — DO NOT EDIT -->

---
id: "5.3.23"
title: "Citrix ADC AppFlow Export Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.23 · Citrix ADC AppFlow Export Health

## Description

Citrix ADC AppFlow exports flow records to external IPFIX collectors for traffic analytics. If exports are dropped, ignored, or templates do not match the collector, you lose visibility into application traffic and may miss security or capacity signals. Monitoring AppFlow health ensures flow telemetry continuously reaches Splunk and your collectors, and surfaces misconfiguration before export backlogs or silent data loss.

## Value

Citrix ADC AppFlow exports flow records to external IPFIX collectors for traffic analytics. If exports are dropped, ignored, or templates do not match the collector, you lose visibility into application traffic and may miss security or capacity signals. Monitoring AppFlow health ensures flow telemetry continuously reaches Splunk and your collectors, and surfaces misconfiguration before export backlogs or silent data loss.

## Implementation

Enable AppFlow on the ADC and point collectors at your IPFIX endpoints. Forward `citrix:netscaler:syslog` (export health and template messages) and `citrix:netscaler:appflow` (decapsulated or forwarded flow records) to `index=netscaler`. Alert on sustained drops/ignores, collector unreachable messages, or template mismatch events. Correlate with network path and collector capacity. Baseline normal flow export rates per ADC to detect drift.

## Detailed Implementation

Prerequisites
• Install Splunk Add-on for Citrix NetScaler (Splunk_TA_citrix-netscaler) and assign data to `index=netscaler`.
• Ingest `citrix:netscaler:syslog` (AppFlow export status, IPFIX errors) and `citrix:netscaler:appflow` where used for flow telemetry.
• Document collector IPs, ports, and template versions in your runbook.

Step 1 — Configure data collection
On the ADC, configure AppFlow actions and collectors; enable logging of export failures. Use syslog forwarding to Splunk for export health messages. Ensure time sync (NTP) between ADC, collectors, and Splunk. If fields are extracted (`action`, `export_status`, `collector_ip`), confirm they line up with vendor documentation in props transforms.

Step 2 — Create the search and alert
Run the provided SPL. Save as a scheduled search or real-time alert when drops, ignores, or template/collector errors exceed baseline (for example, any template mismatch, or drop rate sustained for 10 minutes). Add a lookup for known maintenance windows to suppress noise.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Network_Traffic data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Network_Traffic model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Add panels to a NetOps dashboard, route high-severity alerts to on-call, and document triage: verify collector health, network ACLs, template versions, and ADC packet engine load.

## SPL

```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:appflow")
(("appflow" AND ("drop" OR "ignore" OR "template" OR "collector" OR "IPFIX")) OR match(_raw, "(?i)flow.*(export|discard)"))
| eval flow_action=coalesce(action, export_status, "unknown")
| bin _time span=5m
| stats count as events, dc(host) as adc_count by _time, host, flow_action
| where match(flow_action, "(?i)(drop|ignore|fail|mismatch)") OR events > 100
| sort - _time
| table _time, host, flow_action, events, adc_count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

## Visualization

Time chart of AppFlow export events by action, single value for drops per hour, table of hosts with template or collector errors.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
- [Citrix ADC — AppFlow overview](https://docs.citrix.com/en-us/citrix-adc/current-release/application-firewall-analytics/appflow-analytics.html)
