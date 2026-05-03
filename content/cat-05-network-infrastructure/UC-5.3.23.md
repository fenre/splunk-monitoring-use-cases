<!-- AUTO-GENERATED from UC-5.3.23.json — DO NOT EDIT -->

---
id: "5.3.23"
title: "Citrix ADC AppFlow Export Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.23 · Citrix ADC AppFlow Export Health

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We read AppFlow and export health on the same path so a gap in app visibility is a data path issue you can fix, not a blind spot forever.*

---

## Description

Citrix ADC AppFlow exports flow records to external IPFIX collectors for traffic analytics. If exports are dropped, ignored, or templates do not match the collector, you lose visibility into application traffic and may miss security or capacity signals. Monitoring AppFlow health ensures flow telemetry continuously reaches Splunk and your collectors, and surfaces misconfiguration before export backlogs or silent data loss.

## Value

Infrastructure teams monitor Citrix ADC AppFlow export health, detecting export failures and record drops that create visibility gaps in Splunk traffic analytics.

## Implementation

Enable AppFlow on the ADC and point collectors at your IPFIX endpoints. Forward `citrix:netscaler:syslog` (export health and template messages) and `citrix:netscaler:appflow` (decapsulated or forwarded flow records) to `index=netscaler`. Alert on sustained drops/ignores, collector unreachable messages, or template mismatch events. Correlate with network path and collector capacity. Baseline normal flow export rates per ADC to detect drift.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC AppFlow export sending IPFIX/AppFlow records to Splunk. Data in `index=netscaler` with `sourcetype=citrix:netscaler:appflow`. Key fields: `appflow_collector`, `export_rate`, `dropped_records`, `template_version`.
* AppFlow is Citrix ADC's telemetry export mechanism (IPFIX-based). It sends per-transaction records including URL, response code, latency, SSL cipher, client IP to external collectors (Splunk, Citrix ADM, etc.). If AppFlow export fails, Splunk loses visibility into ADC traffic.

### Step 1 — - Configure data collection
Configure AppFlow on ADC:
```
add appflow collector splunk_collector <splunk_ip> -port 4739 -transport logstream
add appflow action splunk_action -collectors splunk_collector
add appflow policy splunk_policy true splunk_action
bind lb vserver <vs> -policyName splunk_policy -priority 1 -type REQUEST
```
Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:appflow" earliest=-1h | stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- AppFlow export health:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") earliest=-4h
| where match(_raw, "(?i)(appflow|collector|export|ipfix)")
| eval collector=coalesce(appflow_collector, collector_name)
| eval dropped=coalesce(dropped_records, appflowdroppedrecords, 0)
| eval exported=coalesce(export_rate, appflowexportedrecords, 0)
| stats latest(dropped) as total_dropped latest(exported) as total_exported by host, collector
| eval drop_pct=if(total_exported > 0, round(100*total_dropped/(total_exported + total_dropped), 2), 0)
| eval status=case(total_exported=0, "NO_DATA -- collector may be unreachable", drop_pct > 5, "DROPPING -- ".drop_pct."% records lost", drop_pct > 1, "WARNING -- some drops", 1==1, "HEALTHY")
| where status != "HEALTHY"
| sort status
```

### Step 3 — - Validate
(a) On ADC CLI: `stat appflow` -- compare exported/dropped counts with Splunk.
(b) Stop the Splunk receiver briefly and verify dropped records increase.
(c) Verify template: `show appflow policy` and `show appflow action`.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- AppFlow Health"):
* Row 1 -- Single-value: "Export rate", "Dropped records", "Drop %", "Collector status".

Alerting:
* High (zero exports for > 15 min): AppFlow not reaching Splunk -- data gap.
* Warning (drop rate > 5%): collector capacity issue.

### Step 5 — - Troubleshooting

* **Zero exports** -- Check: (1) collector IP/port reachable: `ping <splunk_ip>`, (2) AppFlow policy is bound to vservers, (3) Splunk is listening on the configured port.

* **High drop rate** -- ADC buffer overflow. Increase buffer: `set appflow param -templateRefresh 600 -flowRecordInterval 60`. Alternatively, the Splunk receiver may be too slow.

* **AppFlow data incomplete** -- Ensure the AppFlow action includes all required templates (HTTP, SSL, TCP). Check: `show appflow action <action>`.

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

## Known False Positives

AppFlow drops, network blips, and exporter restarts can look like a gap in data before you know it is ingest.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
- [Citrix ADC — AppFlow overview](https://docs.citrix.com/en-us/citrix-adc/current-release/application-firewall-analytics/appflow-analytics.html)
