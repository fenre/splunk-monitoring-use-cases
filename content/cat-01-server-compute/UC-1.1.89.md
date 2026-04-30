<!-- AUTO-GENERATED from UC-1.1.89.json — DO NOT EDIT -->

---
id: "1.1.89"
title: "Syslog Flood Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.89 · Syslog Flood Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Anomaly

*We help you know when one machine suddenly starts writing a truly huge diary, so a broken program or attack does not fill the log system and hide other problems.*

---

## Description

Buckets **syslog** volume per **host** in **5**-**minute** intervals and flags any interval over **10**k events—tune to your daily **p99** once you have a baseline.

## Value

Log floods burn **ingest** license, mask **security** lines in noise, and often come from **looping** apps or **debug** left on after an incident.

## Implementation

Replace the static **10**k with `| eventstats median(count) as med by host | where count>20*med` for an adaptive version; add **ignore** **host** patterns for known **noisy** appliances if policy allows.

## Detailed Implementation

### Prerequisites
- Accurate **host** field; for **K8s**, you may instead run the same SPL on **`namespace`** in a different use case.

**SPL** — Replaces the invalid `where count>10000 in 5 minute window` pattern with a proper **bin** + **stats**.


### Step 3 — Validate
`tcpdump` **not** required first—on the host, `journalctl --since` rate or **rsyslog** **impstats** if you use them; compare to the **count** in Splunk for the **bin**.

### Step 4 — Operationalize
Throttle at the **forwarder** after you identify the **facility** causing the burst.



## SPL

```spl
index=os sourcetype=syslog host=*
| bin _time span=5m
| stats count by host, _time
| where count>10000
```

## Visualization

Timechart, Alert

## Known False Positives

**SIEM** **forwarders** that batch; **k8s** **node** **syslog** during **rollouts**; too-low **10**k on a **log** **aggregator**—run this **per** **source** **type** child, not on the **agg** only, or you will never learn the true offender.

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
