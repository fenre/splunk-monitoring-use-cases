<!-- AUTO-GENERATED from UC-5.5.24.json — DO NOT EDIT -->

---
id: "5.5.24"
title: "Fortinet SD-WAN Health-Check and SLA Compliance"
status: "community"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.24 · Fortinet SD-WAN Health-Check and SLA Compliance

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Crawl &middot; **Status:** Community

*We watch the Fortinet firewalls run small test pings on every WAN link to confirm it is healthy. When a probe stops getting answers, the firewall switches the traffic to a different link. We surface the failing probe so the network team can fix the underlying transport before the alternate link also fails.*

---

## Description

Surfaces Fortinet SD-WAN health-check probes that are not currently alive. Aggregates per-device, per-probe, per-interface so the failing transports surface to the top of the table even when other interfaces on the same FortiGate are healthy.

## Value

FortiGate SD-WAN is one of the most widely deployed SD-WAN footprints because it ships free with the firewall licence — every FortiGate is potentially an SD-WAN edge. The SD-WAN logic is FortiGate-internal: Fortinet does not require a separate orchestrator or controller appliance. That makes SD-WAN failures invisible to anyone watching only firewall traffic logs. This UC pulls the health-check and SLA-rule events out of the firewall event stream so the NOC can see SD-WAN outages from the same Splunk console it already uses to monitor FortiGate firewall events. For multi-vendor SD-WAN estates, the same dashboard can sit alongside the Cisco / VMware / Versa equivalents.

## Implementation

Enable SD-WAN health-check logging on FortiGate (`config log setting`, `set fwpolicy-implicit-log enable`, plus `config log syslogd setting` for the syslog forwarder). Install `TA-fortinet_fortigate` for field extraction. Alert when a health-check probe fails for more than two consecutive intervals, or when an SLA rule triggers a path switch outside an announced maintenance window.

## SPL

```spl
index=network sourcetype="fgt_event" subtype="sdwan"
| search event_type="health_check" status!="alive"
| stats count by devname, health_check_name, interface, status
| sort - count
```

## Visualization

Status grid (per-device health-check state), Table (failed probes sorted by event count), Line chart (latency / jitter / packet-loss per link, multi-link overlay).

## Known False Positives

**Probe destinations behind a maintenance window.** SD-WAN health-checks often target a 1.1.1.1 / 8.8.8.8 / internal-load-balancer probe destination. When the destination is under maintenance, every FortiGate that points at it lights up red. Filter alerts on probe-destination first.

**Cellular failover sleep mode.** Some FortiGate SKUs sleep the cellular interface when the primary is healthy; the LTE health-check will read 'dead' even though the link is fine. Suppress alerts for interfaces whose admin-state is `standby`.

**Initial probe convergence after firmware upgrade.** A FortiGate firmware upgrade resets health-check state machines; the first 1–2 minutes after reboot will show probes as `dead` until the first successful response. Tolerate a 5-minute warm-up window after announced upgrades.

## References

- [Fortinet FortiGate Add-On for Splunk (Splunkbase app 2846)](https://splunkbase.splunk.com/app/2846)
- [FortiGate SD-WAN documentation](https://docs.fortinet.com/)
