<!-- AUTO-GENERATED from UC-5.1.46.json — DO NOT EDIT -->

---
id: "5.1.46"
title: "Stack Unit and Redundancy Health (Meraki MS)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.46 · Stack Unit and Redundancy Health (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Availability

*We help you know early when something looks wrong with stack unit and redundancy health so the team can act before it grows into a bigger outage.*

---

## Description

Ensures switch stacking configuration remains healthy and redundancy is not compromised.

## Value

NOC teams monitor Meraki MS switch stack health including member presence, ring topology status, and role changes, detecting stack member loss and ring breaks that reduce redundancy.

## Implementation

Monitor stack member status via device API. Alert on member removal or failure.

## Detailed Implementation

### Prerequisites
* Meraki MS switch stack health data. Data in `index=meraki` with `sourcetype=meraki:events` or API data. Key events: stack member join/leave, stack role changes, stack ring status.
* Meraki MS stacking: physical stacking of MS switches via dedicated stack cables or ring topology. Stack provides unified management, single control plane, and cross-stack link aggregation. Stack member failure degrades available ports and potentially breaks ring redundancy.

### Step 1 — - Configure data collection
```
# Syslog: enable Event log
# API: GET /networks/{networkId}/switch/stacks
# Returns stack configuration and member status
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-30d
| where match(_raw, "(?i)stack|member.*join|member.*leave|ring|primary.*change")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Stack health monitoring:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:switch:stack") earliest=-30d
| where match(_raw, "(?i)stack|member.*join|member.*leave|ring.*break|ring.*restore|primary.*change|master.*change")
| eval device=coalesce(serial, host)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| eval stack_event=case(
    match(_raw, "(?i)member.*leave|member.*down|removed"), "MEMBER_LOST",
    match(_raw, "(?i)member.*join|member.*add|restored"), "MEMBER_JOINED",
    match(_raw, "(?i)ring.*break|ring.*fail"), "RING_BROKEN",
    match(_raw, "(?i)ring.*restore|ring.*heal"), "RING_RESTORED",
    match(_raw, "(?i)primary.*change|master.*change"), "ROLE_CHANGE",
    1==1, "STACK_EVENT")
| stats count as events count(eval(stack_event="MEMBER_LOST")) as members_lost count(eval(stack_event="RING_BROKEN")) as ring_breaks by network_name
| eval severity=case(
    members_lost > 0, "CRITICAL -- stack member lost",
    ring_breaks > 0, "WARNING -- stack ring broken (no redundancy)",
    events > 5, "INFO -- stack topology changes",
    1==1, "OK")
| where severity != "OK"
| sort severity
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch stacks -- check stack members and status.
(b) Verify stack cable connections and LED indicators.
(c) Check firmware version consistency across stack members.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Stack Health"):
* Row 1 -- Single-value: "Stack members lost", "Ring breaks".
* Row 2 -- Stack health event timeline.

Alert: Critical (stack member lost): reduced port capacity and potential ring break.

### Step 5 — - Troubleshooting

* **Stack member lost** -- Check: (1) power to the member switch, (2) stack cable connections, (3) member switch LED indicators. Reseat stack cables if loose.

* **Ring broken** -- Single stack cable failure. Stack continues operating in daisy-chain mode but loses redundancy. Replace failed cable immediately.

* **Firmware mismatch** -- All stack members must run same firmware. Meraki auto-updates, but verify in Dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS stack_id=*
| stats count as stack_members, count(eval(status="offline")) as offline_members by stack_id
| where offline_members > 0
```

## Visualization

Table of stack members and status; redundancy gauge; alert dashboard.

## Known False Positives

Meraki cloud delays, dashboard API limits, and large site templates can look like a gap. Confirm in dashboard before opening a P1 on Splunk only.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
