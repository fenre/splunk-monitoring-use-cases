<!-- AUTO-GENERATED from UC-3.3.18.json — DO NOT EDIT -->

---
id: "3.3.18"
title: "etcd Leader Changes"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.18 · etcd Leader Changes

## Description

Frequent etcd leader elections indicate network partitions, disk I/O bottlenecks, or resource contention on control plane nodes. Excessive elections degrade API server responsiveness and can cause cluster instability.

## Value

Frequent etcd leader elections indicate network partitions, disk I/O bottlenecks, or resource contention on control plane nodes. Excessive elections degrade API server responsiveness and can cause cluster instability.

## Implementation

Scrape etcd Prometheus metrics via OpenTelemetry Collector or forward etcd logs. Track `etcd_server_leader_changes_seen_total` as a counter. Alert when more than 3 leader changes occur within 10 minutes. Correlate with disk latency metrics (`etcd_disk_wal_fsync_duration_seconds`).

## Detailed Implementation

Prerequisites
• Install and configure: OpenTelemetry Collector (Prometheus scrape), etcd log forwarding
• Have these sources flowing into Splunk: `sourcetype=openshift:etcd:metrics`, `sourcetype=openshift:etcd`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Scrape etcd Prometheus metrics via OpenTelemetry Collector or forward etcd logs. Track `etcd_server_leader_changes_seen_total` as a counter. Alert when more than 3 leader changes occur within 10 minutes. Correlate with disk latency metrics (`etcd_disk_wal_fsync_duration_seconds`).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:etcd:metrics" metric_name="etcd_server_leader_changes_seen_total"
| bin _time span=5m
| stats max(_value) as leader_changes by cluster, instance, _time
| streamstats current=f window=1 last(leader_changes) as prev by cluster, instance
| eval delta=leader_changes-prev
| where delta>0
| table _time cluster instance delta
```

Understanding this SPL

**etcd Leader Changes** — Frequent etcd leader elections indicate network partitions, disk I/O bottlenecks, or resource contention on control plane nodes.

Documented **Data sources**: `sourcetype=openshift:etcd:metrics`, `sourcetype=openshift:etcd`. **App/TA** context: OpenTelemetry Collector (Prometheus scrape), etcd log forwarding. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Timechart (leader changes over time), Table (instance, changes), Correlation panel with disk latency.

## SPL

```spl
index=openshift sourcetype="openshift:etcd:metrics" metric_name="etcd_server_leader_changes_seen_total"
| bin _time span=5m
| stats max(_value) as leader_changes by cluster, instance, _time
| streamstats current=f window=1 last(leader_changes) as prev by cluster, instance
| eval delta=leader_changes-prev
| where delta>0
| table _time cluster instance delta
```

## Visualization

Timechart (leader changes over time), Table (instance, changes), Correlation panel with disk latency.

## References

- [OpenShift etcd monitoring documentation](https://docs.openshift.com/container-platform/latest/scalability_and_performance/recommended-performance-scale-practices/recommended-etcd-practices.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
