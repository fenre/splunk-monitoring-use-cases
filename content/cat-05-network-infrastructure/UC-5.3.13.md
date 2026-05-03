<!-- AUTO-GENERATED from UC-5.3.13.json — DO NOT EDIT -->

---
id: "5.3.13"
title: "Citrix ADC Virtual Server Health and State (NetScaler)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.13 · Citrix ADC Virtual Server Health and State (NetScaler)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We follow virtual service state in the same logs so a down or disabled front door is something you can match to a change, not a rumor.*

---

## Description

Citrix ADC (NetScaler) virtual servers (vServers) are the front-end load-balancing endpoints that distribute traffic to back-end service groups. A vServer transitions from UP to DOWN when all bound services fail health checks, causing a complete outage for the application it serves. Monitoring vServer state changes provides immediate alerting when applications lose load-balanced availability.

## Value

Application delivery teams monitor Citrix ADC virtual server states (UP/DOWN/BUSY/OOS) across the fleet, detecting service outages and capacity issues with application context.

## Implementation

Configure Citrix ADC to send syslog to Splunk via Splunk Connect for Syslog (SC4S). The ADC generates syslog messages for vServer state transitions (SNMP trap equivalent). Alternatively, use the NITRO API via scripted input to poll `lbvserver` statistics including `state`, `curclntconnections`, `tothits`, and `health` (percentage of UP services). Alert immediately on any vServer transitioning to DOWN. Track vServer health percentage — a vServer at 50% health means half its services are down and may be approaching failure. Correlate with service group member health checks for root cause.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770) installed. Citrix ADC syslog in `index=netscaler` with `sourcetype=citrix:netscaler:syslog`. Optionally, NITRO REST API performance counters in `sourcetype=citrix:netscaler:perf`. Key fields: `vs_name` (virtual server name), `vs_state` (UP/DOWN/OUT_OF_SERVICE), `vs_type` (HTTP/SSL/TCP/UDP), `vserver_ip`, `current_connections`, `total_requests`.
* Citrix ADC virtual server states: UP (healthy, serving traffic), DOWN (no healthy services), OUT_OF_SERVICE (admin-disabled), BUSY (at connection limit).

### Step 1 — - Configure data collection
Configure Citrix ADC syslog:
```
add syslogAction splunk_syslog <splunk_ip> -logLevel ALL -transport UDP
add syslogPolicy splunk_policy "true" splunk_syslog
bind system global splunk_policy -priority 1
```
Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" earliest=-4h
| where isnotnull(vs_name) OR match(_raw, "(?i)(vserver|virtual server)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Virtual server health monitoring:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") earliest=-15m
| eval vs=coalesce(vs_name, vserver_name, vserver)
| eval state=coalesce(vs_state, vserver_state, state)
| eval vs_ip=coalesce(vserver_ip, vs_ip, ip_address)
| stats latest(state) as current_state latest(current_connections) as conns latest(total_requests) as reqs by host, vs, vs_ip
| lookup citrix_vserver_inventory.csv vs OUTPUT application, tier, owner, expected_state
| eval is_problem=case(current_state="DOWN", 1, current_state="OUT_OF_SERVICE" AND expected_state="UP", 1, current_state="BUSY", 1, 1==1, 0)
| eval severity=case(current_state="DOWN" AND tier="prod", "CRITICAL", current_state="DOWN", "HIGH", current_state="BUSY", "WARNING -- at capacity", current_state="OUT_OF_SERVICE" AND expected_state="UP", "WARNING -- unexpectedly disabled", 1==1, "OK")
| where is_problem=1
| table host, vs, vs_ip, application, tier, current_state, conns, severity
| sort severity
```

### Step 3 — - Validate
(a) On ADC CLI: `show lb vserver` -- compare states with Splunk.
(b) Disable a test vserver: `disable lb vserver <vs>` -- verify OUT_OF_SERVICE appears.
(c) Enable: `enable lb vserver <vs>` -- verify recovery.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Virtual Server Health"):
* Row 1 -- Single-value: "Total vServers", "DOWN", "BUSY", "Fleet availability %".
* Row 2 -- Problem vserver detail table.

Alerting:
* Critical (prod vserver DOWN): service outage.
* Warning (vserver BUSY): connection limit reached.

### Step 5 — - Troubleshooting

* **vServer DOWN but services are UP** -- Check: (1) vserver is admin-enabled, (2) backup vserver is not configured to take over, (3) spillover threshold not exceeded.

* **vServer BUSY** -- Max connections hit. Check: `show lb vserver <vs>` for `MaxClient` setting. Increase or investigate why connections aren't closing.

* **No vserver state events** -- Ensure syslog level is set to ALL (not just CRITICAL/ERROR).

## SPL

```spl
index=network sourcetype="citrix:netscaler:syslog" "Vserver" ("DOWN" OR "UP" OR "OUT OF SERVICE")
| rex "Vserver (?<vserver_name>\S+) - State (?<state>\w+)"
| where state="DOWN" OR state="OUTOFSERVICE"
| bin _time span=5m
| stats count as state_changes, latest(state) as current_state, values(host) as adc_node by vserver_name, _time
| table _time, vserver_name, current_state, state_changes, adc_node
```

## Visualization

Status grid (vServer name x state), Timeline (state transitions), Table (DOWN vServers with service count).

## Known False Positives

Admin disable, GSLB moves, and maintenance can mark a service down on purpose; compare to the runbook and change record.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
