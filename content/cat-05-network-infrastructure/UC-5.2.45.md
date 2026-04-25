<!-- AUTO-GENERATED from UC-5.2.45.json — DO NOT EDIT -->

---
id: "5.2.45"
title: "FortiGate SD-WAN Health Check and SLA Monitoring (Fortinet)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.45 · FortiGate SD-WAN Health Check and SLA Monitoring (Fortinet)

## Description

SD-WAN health checks (ICMP, HTTP, DNS, TCP/UDP echo) continuously score each member link against SLA targets for latency, jitter, and loss. When an SLA fails, FortiOS steers traffic to better paths—so log and metric visibility is how you catch ISP brownouts before users open tickets. Trending per-interface loss and delay also validates whether performance problems are underlay-related or application-side.

## Value

SD-WAN health checks (ICMP, HTTP, DNS, TCP/UDP echo) continuously score each member link against SLA targets for latency, jitter, and loss. When an SLA fails, FortiOS steers traffic to better paths—so log and metric visibility is how you catch ISP brownouts before users open tickets. Trending per-interface loss and delay also validates whether performance problems are underlay-related or application-side.

## Implementation

Define SD-WAN SLAs and health-check servers that reflect real user paths (not only the nearest DNS). Forward `system` SD-WAN events to Splunk and confirm extracted fields with your FortiOS version—field names differ slightly across releases. Alert when SLA violations repeat for the same interface or when loss/latency step-changes correlate with carrier incidents. Cross-check with `fgt_traffic` volume shifts on the same SD-WAN zones.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-fortinet_fortigate` (Splunkbase 2846).
• Ensure the following data sources are available: `sourcetype=fgt_event` (FortiOS system events, SD-WAN subtype varies by release, e.g. `subtype=sdwan`), `sourcetype=fortinet_fortios_event`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Define SD-WAN SLAs and health-check servers that reflect real user paths (not only the nearest DNS). Forward `system` SD-WAN events to Splunk and confirm extracted fields with your FortiOS version—field names differ slightly across releases. Alert when SLA violations repeat for the same interface or when loss/latency step-changes correlate with carrier incidents. Cross-check with `fgt_traffic` volume shifts on the same SD-WAN zones.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype IN ("fgt_event","fortinet_fortios_event") type="system" (subtype="sdwan" OR subtype="sd-wan" OR match(_raw, "(?i)sd-wan|sdwan"))
| eval iface=coalesce(interface, intf, sdwan_zone, link)
| eval loss_pct=coalesce(pktloss, packet_loss, loss, sdwan_loss)
| eval lat_ms=coalesce(latency, rtt, sla_latency)
| eval jitter_ms=coalesce(jitter, sdwan_jitter)
| where loss_pct > 0 OR lat_ms > 200 OR match(lower(_raw), "violated|fail|unreachable|timeout")
| timechart span=15m avg(loss_pct) as avg_loss avg(lat_ms) as avg_latency by iface
```

Understanding this SPL

**FortiGate SD-WAN Health Check and SLA Monitoring (Fortinet)** — SD-WAN health checks (ICMP, HTTP, DNS, TCP/UDP echo) continuously score each member link against SLA targets for latency, jitter, and loss. When an SLA fails, FortiOS steers traffic to better paths—so log and metric visibility is how you catch ISP brownouts before users open tickets. Trending per-interface loss and delay also validates whether performance problems are underlay-related or application-side.

Documented **Data sources**: `sourcetype=fgt_event` (FortiOS system events, SD-WAN subtype varies by release, e.g. `subtype=sdwan`), `sourcetype=fortinet_fortios_event`. **App/TA** (typical add-on context): `TA-fortinet_fortigate` (Splunkbase 2846). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **iface** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **loss_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **lat_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **jitter_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where loss_pct > 0 OR lat_ms > 200 OR match(lower(_raw), "violated|fail|unreachable|timeout")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by iface** — ideal for trending and alerting on this use case.

Step 3 — Validate
Reconcile a sample of results with the FortiGate GUI or FortiManager for the same policies, objects, and time range.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (loss/latency per member), Table (SLA violations by interface), Single value (active violated SLAs).

## SPL

```spl
index=firewall sourcetype IN ("fgt_event","fortinet_fortios_event") type="system" (subtype="sdwan" OR subtype="sd-wan" OR match(_raw, "(?i)sd-wan|sdwan"))
| eval iface=coalesce(interface, intf, sdwan_zone, link)
| eval loss_pct=coalesce(pktloss, packet_loss, loss, sdwan_loss)
| eval lat_ms=coalesce(latency, rtt, sla_latency)
| eval jitter_ms=coalesce(jitter, sdwan_jitter)
| where loss_pct > 0 OR lat_ms > 200 OR match(lower(_raw), "violated|fail|unreachable|timeout")
| timechart span=15m avg(loss_pct) as avg_loss avg(lat_ms) as avg_latency by iface
```

## Visualization

Timechart (loss/latency per member), Table (SLA violations by interface), Single value (active violated SLAs).

## References

- [Splunkbase app 2846](https://splunkbase.splunk.com/app/2846)
