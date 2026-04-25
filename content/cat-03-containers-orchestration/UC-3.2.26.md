<!-- AUTO-GENERATED from UC-3.2.26.json — DO NOT EDIT -->

---
id: "3.2.26"
title: "etcd Health and Latency"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.26 · etcd Health and Latency

## Description

etcd request latency and raft health predict API slowness and split-brain risk; early warning preserves control plane stability.

## Value

etcd request latency and raft health predict API slowness and split-brain risk; early warning preserves control plane stability.

## Implementation

Scrape etcd `/metrics` from members (managed clusters: use cloud metrics export if direct scrape is blocked). Alert on rising commit duration, peer RTT, or leader election counters.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector.
• Ensure the following data sources are available: `sourcetype=kube:etcd`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scrape etcd `/metrics` from members (managed clusters: use cloud metrics export if direct scrape is blocked). Alert on rising commit duration, peer RTT, or leader election counters.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:etcd"
| timechart span=5m avg(etcd_network_peer_round_trip_time_seconds) as rtt, avg(etcd_disk_backend_commit_duration_seconds) as commit
| where rtt>0.05 OR commit>0.1
```

Understanding this SPL

**etcd Health and Latency** — etcd request latency and raft health predict API slowness and split-brain risk; early warning preserves control plane stability.

Documented **Data sources**: `sourcetype=kube:etcd`. **App/TA** (typical add-on context): Splunk OTel Collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:etcd. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:etcd". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• Filters the current rows with `where rtt>0.05 OR commit>0.1` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency, DB size), Single value (leader changes), Table (member ID, health).

## SPL

```spl
index=k8s sourcetype="kube:etcd"
| timechart span=5m avg(etcd_network_peer_round_trip_time_seconds) as rtt, avg(etcd_disk_backend_commit_duration_seconds) as commit
| where rtt>0.05 OR commit>0.1
```

## Visualization

Line chart (latency, DB size), Single value (leader changes), Table (member ID, health).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
