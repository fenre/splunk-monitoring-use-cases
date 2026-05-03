<!-- AUTO-GENERATED from UC-5.3.17.json — DO NOT EDIT -->

---
id: "5.3.17"
title: "Citrix ADC GSLB Site and Service Health (NetScaler)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.17 · Citrix ADC GSLB Site and Service Health (NetScaler)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability

*We look at site and global load state so a shifted region or a quiet peer is on the same screen as the rest of the delivery story.*

---

## Description

Global Server Load Balancing (GSLB) distributes traffic across multiple data centers based on proximity, health, and load. GSLB relies on the Metric Exchange Protocol (MEP) between sites to share health and load metrics. If MEP connectivity fails between sites, the GSLB method falls back to Round Robin — potentially sending users to degraded or distant sites. Monitoring GSLB site health and MEP status ensures intelligent multi-site traffic distribution.

## Value

Infrastructure teams monitor Citrix ADC GSLB site reachability, service health, and inter-site RTT to detect data center outages affecting global traffic distribution before user impact.

## Implementation

The ADC logs GSLB service state changes and MEP connectivity events via syslog. MEP runs on TCP ports 3011 (standard) or 3009 (secure) between GSLB sites. Additionally, poll the NITRO API `gslbsite` and `gslbservice` resources for site status, MEP status, and GSLB service health. Alert on: any GSLB service going DOWN, MEP status changing to DOWN between any pair of sites (fallback to Round Robin), and GSLB site becoming unreachable. When MEP fails, all GSLB decisions for that site pair become unaware of the remote site's health — traffic may be sent to a degraded or offline site.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC GSLB syslog events or NITRO stats in `index=netscaler`. Key fields: `gslb_site`, `gslb_service`, `gslb_vserver`, `site_state` (UP/DOWN), `site_metric` (RTT, persistence, bandwidth).
* GSLB (Global Server Load Balancing) distributes traffic across data centers based on: (1) proximity (lowest RTT), (2) round robin, (3) static proximity (geo), (4) persistence. GSLB site DOWN means an entire data center is unreachable from the GSLB perspective.

### Step 1 — - Configure data collection
Verify GSLB data:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("GSLB" OR "gslb" OR "site" AND ("UP" OR "DOWN" OR "metric")) earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- GSLB site and service health:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("GSLB" OR "gslb") earliest=-4h
| eval site=coalesce(gslb_site, site_name, gslbsite)
| eval service=coalesce(gslb_service, gslbservice)
| eval state=coalesce(site_state, service_state, state)
| eval rtt=coalesce(site_rtt, rtt_ms)
| stats latest(state) as current_state latest(rtt) as site_rtt by host, site, service
| eval severity=case(current_state="DOWN" AND isnotnull(site), "CRITICAL -- GSLB site DOWN", current_state="DOWN" AND isnotnull(service), "HIGH -- GSLB service DOWN", tonumber(site_rtt) > 200, "WARNING -- high RTT to site (".site_rtt."ms)", 1==1, "OK")
| where severity != "OK"
| table host, site, service, current_state, site_rtt, severity
| sort severity
```

### Step 3 — - Validate
(a) On ADC CLI: `show gslb site` and `show gslb vserver` -- compare with Splunk.
(b) If possible, disable a GSLB site's MEP (metric exchange protocol) and verify it goes DOWN.
(c) Check RTT values align with expected network latency between sites.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- GSLB Health"):
* Row 1 -- Single-value: "GSLB sites", "Sites DOWN", "Services DOWN", "Max RTT (ms)".
* Row 2 -- GSLB site/service health table.

Alerting:
* Critical (GSLB site DOWN): data center unreachable -- traffic will shift to surviving sites.
* Warning (GSLB site RTT > 200ms): performance degradation for users routed to that site.

### Step 5 — - Troubleshooting

* **GSLB site DOWN** -- Check: (1) MEP (Metrics Exchange Protocol) between GSLB nodes: `show gslb site <site>`, (2) network connectivity to the remote site, (3) local lb vserver health at the remote site.

* **High RTT** -- MEP measures RTT between GSLB sites. High RTT indicates network latency. Check WAN link health, routing, or congestion.

* **No GSLB data** -- GSLB events are less frequent than LB events. Ensure GSLB syslog is enabled: `set syslogparams -logLevel ALL`.

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

## Known False Positives

GSLB shifts during drills, path changes, and ISP events can be normal if clients still land on a healthy data center.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
