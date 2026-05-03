<!-- AUTO-GENERATED from UC-5.1.31.json — DO NOT EDIT -->

---
id: "5.1.31"
title: "QoS Policy Drops per Class"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.31 · QoS Policy Drops per Class

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with qos policy drops per class so the team can act before it grows into a bigger outage.*

---

## Description

Traffic dropped per QoS class/queue on routers/switches.

## Value

Network engineers monitor QoS policy drops per traffic class, detecting drops in priority queues (voice/video) that indicate misconfiguration or severe congestion affecting critical applications.

## Implementation

Poll CISCO-CLASS-BASED-QOS-MIB (cbQosCMDropPkt, cbQosCMPrePolicyPkt) per policy/class. Map OID to policy name via lookup. Alert when drop rate exceeds 5% for critical classes.

## Detailed Implementation

### Prerequisites
* QoS policy drop data from SNMP or syslog. Data in `index=network` with SNMP `cbQosCMDropPkt` (.1.3.6.1.4.1.9.9.166.1.15.1.1.14) or interface queue statistics. CLI: `show policy-map interface`.
* QoS drops: packets dropped per traffic class when egress queues are congested. Business-critical traffic (voice, video, signaling) should never be dropped; best-effort traffic may be dropped to protect priority classes. Drops in priority queues indicate misconfiguration or severe congestion.

### Step 1 — - Configure data collection
```
# SNMP polling for QoS drop counters
[snmp_qos_drops]
interval = 300
sourcetype = snmp:qos:drops
index = network
# OID: cbQosCMDropPkt (.1.3.6.1.4.1.9.9.166.1.15.1.1.14)
```
Verify:
```spl
index=network sourcetype="snmp:qos:drops" earliest=-4h
| stats latest(cbQosCMDropPkt) by host, class_name, interface
```

### Step 2 — - Create the search and alert

**Primary search -- QoS policy drops per class:**
```spl
index=network earliest=-4h
| eval drops=tonumber(coalesce(cbQosCMDropPkt, qos_drops, tail_drops))
| eval class_name=coalesce(class_name, qos_class, traffic_class)
| eval interface=coalesce(ifName, interface, port)
| eval device=coalesce(host, device_name)
| where isnotnull(drops)
| bin _time span=5m
| stats latest(drops) as drop_count by _time, device, interface, class_name
| sort device, interface, class_name, _time
| streamstats current=f last(drop_count) as prev_drops by device, interface, class_name
| eval delta_drops=drop_count - prev_drops
| where delta_drops > 0
| eval is_priority=if(match(class_name, "(?i)voice|video|critical|ef|realtime|priority"), "YES", "NO")
| eval severity=case(
    is_priority="YES" AND delta_drops > 0, "CRITICAL -- drops in priority class ".class_name,
    delta_drops > 1000, "WARNING -- high drops in ".class_name,
    delta_drops > 100, "INFO -- drops in ".class_name,
    1==1, "INFO")
| where severity != "INFO"
| table _time, device, interface, class_name, delta_drops, is_priority, severity
| sort severity, -delta_drops
```

### Step 3 — - Validate
(a) CLI: `show policy-map interface <intf>` -- check per-class drop counts and queue depth.
(b) CLI: `show interface <intf> | include queue` -- check output queue drops.
(c) Verify QoS policy: `show policy-map` -- check bandwidth allocations per class.

### Step 4 — - Operationalize
Dashboard ("Network -- QoS Drops"):
* Row 1 -- Single-value: "Priority class drops", "Total drops (4h)".
* Row 2 -- QoS drops timechart by class.

Alert: Critical (any drops in voice/video/priority class): QoS misconfiguration or extreme congestion.

### Step 5 — - Troubleshooting

* **Drops in priority class** -- Priority queue should never drop. Check: (1) bandwidth allocation is sufficient, (2) traffic is correctly classified (DSCP marking), (3) upstream/downstream devices honor QoS markings.

* **High drops in best-effort** -- Normal during congestion. If excessive, consider: increasing link capacity, adjusting bandwidth allocation, or implementing WRED for smoother congestion management.

* **QoS not applied** -- Verify policy-map is applied to correct interface direction: `service-policy output <name>` on egress interfaces.

## SPL

```spl
index=network sourcetype=snmp:qos
| streamstats current=f last(cbQosCMDropPkt) as prev_drop, last(cbQosCMPrePolicyPkt) as prev_pre by host, cbQosConfigIndex, cbQosObjectsIndex
| eval drop_delta=cbQosCMDropPkt-coalesce(prev_drop,0), pre_delta=cbQosCMPrePolicyPkt-coalesce(prev_pre,0)
| eval drop_rate=round(drop_delta/(pre_delta+0.001)*100,2)
| where drop_delta > 0
| stats sum(drop_delta) as total_drops, sum(pre_delta) as total_pre by host, policy_class
| eval drop_pct=round(total_drops/(total_pre+0.001)*100,2)
| sort -total_drops
```

## Visualization

Table (host, class, drops, rate), Bar chart, Line chart (drops over time).

## Known False Positives

Large file transfers and video meetings fill priority queues in ways that are normal for the business—compare to historical drops per class.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
