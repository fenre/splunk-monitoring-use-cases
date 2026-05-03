<!-- AUTO-GENERATED from UC-5.1.48.json — DO NOT EDIT -->

---
id: "5.1.48"
title: "QoS Queue Drops and Priority Violations (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.48 · QoS Queue Drops and Priority Violations (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with qos queue drops and priority violations so the team can act before it grows into a bigger outage.*

---

## Description

Detects QoS queue overflow and drops that indicate traffic priority issues.

## Value

Network engineers monitor Meraki MS QoS queue drops and DSCP priority violations, ensuring voice and video traffic receives proper priority queuing and classification.

## Implementation

Monitor QoS-related syslog events and drops. Alert on significant drop rates.

## Detailed Implementation

### Prerequisites
* Meraki MS QoS queue data from syslog or API. Data in `index=meraki` with `sourcetype=meraki:events` or port status data. Key: QoS policy drops and priority violations.
* Meraki MS QoS: configured per-port or per-switch via Dashboard. Supports DSCP marking and CoS mapping. Queue drops indicate congestion in specific traffic classes.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Switch > QoS
# Configure DSCP to queue mapping
# Syslog: enable Event log for QoS events
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)QoS|queue.*drop|priority|DSCP|CoS")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- QoS queue drops and priority violations:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)QoS|queue.*drop|priority.*violation|DSCP.*mismatch|CoS.*drop")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| rex field=_raw "(?i)(?:port|Port)\s+(?<port_id>\d+)"
| eval queue_event=case(
    match(_raw, "(?i)queue.*drop|tail.*drop"), "QUEUE_DROP",
    match(_raw, "(?i)priority.*violation|DSCP.*mismatch"), "PRIORITY_VIOLATION",
    1==1, "QOS_EVENT")
| stats count as events values(port_id) as ports by network_name, device, queue_event
| eval severity=case(
    queue_event="QUEUE_DROP" AND events > 100, "WARNING -- significant QoS queue drops",
    queue_event="PRIORITY_VIOLATION", "INFO -- QoS priority violation",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Dashboard: Switch > QoS -- check queue configuration and mapping.
(b) Verify DSCP marking is consistent end-to-end.
(c) Check if voice/video traffic is correctly classified.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- QoS"):
* Row 1 -- Single-value: "Queue drops (4h)", "Priority violations".
* Row 2 -- QoS event timeline.

### Step 5 — - Troubleshooting

* **Queue drops on voice/video** -- Check QoS policy. Ensure voice/video DSCP (EF/46, AF41/34) is mapped to priority queue. Verify upstream devices mark traffic correctly.

* **DSCP mismatch** -- Verify DSCP trust is enabled on the switch port. Some switches reset DSCP to 0 by default on access ports.

* **Congestion on specific queue** -- Interface may be oversubscribed. Consider upgrading link or applying traffic shaping.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*QoS*" OR signature="*queue*" OR signature="*drop*")
| stats sum(packets_dropped) as total_drops by switch_name, queue_id
| where total_drops > 1000
```

## Visualization

Table of drops by queue; time-series of drop events; traffic distribution pie chart.

## Known False Positives

Large file transfers and video meetings fill priority queues in ways that are normal for the business—compare to historical drops per class.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
