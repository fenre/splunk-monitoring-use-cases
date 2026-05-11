<!-- AUTO-GENERATED from UC-5.3.39.json — DO NOT EDIT -->

---
id: "5.3.39"
title: "Citrix SD-WAN Application Steering and QoS Enforcement"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.39 · Citrix SD-WAN Application Steering and QoS Enforcement

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance

*We see which apps are steered and shaped on the same fabric so a change in class or a new workload does not go unnoticed in a bill or a review.*

---

## Description

Application-aware routing and queuing are core to SD-WAN value. Monitoring which path each app uses, when drops occur in a class of service, and when steering decisions change frequently exposes misconfiguration, license limits, and congestion on steered traffic that affects voice, video, and business apps.

## Value

Network operations teams validate Citrix SD-WAN application-aware routing and QoS enforcement, detecting missteered traffic and dropped packets in real-time quality-of-service classes.

## Implementation

Import application-to-QoS mapping from the orchestrator. Track drops and deep queue signs per class. For steering churn, use `path_selected` with `streamstats` to count changes per 5m for major apps. Involve the network and app teams when a critical app rides a backup path. Pair with underlay stats from the same time window to separate LAN vs WAN causes.

## Detailed Implementation

### Prerequisites
* Citrix SD-WAN syslog or Orchestrator API data. Key fields: `application`, `steering_policy`, `actual_path`, `expected_path`, `qos_class`, `bandwidth_used`, `bandwidth_limit`, `drop_count`.
* Citrix SD-WAN application steering: routes traffic based on application type (Office 365, Zoom, SAP, web browsing) to the optimal WAN link. QoS classes: Realtime (voice/video), Interactive (business apps), Bulk (backups, updates), Best Effort (web browsing).

### Step 1 — - Configure data collection
Verify application steering data:
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:perf") earliest=-4h
| where isnotnull(application) OR isnotnull(qos_class)
| stats count by application, qos_class
```

### Step 2 — - Create the search and alert

**Primary search -- Application steering and QoS enforcement:**
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:perf") earliest=-4h
| eval app=coalesce(application, app_name)
| eval policy=coalesce(steering_policy, routing_policy)
| eval actual=coalesce(actual_path, path_used)
| eval expected=coalesce(expected_path, preferred_path)
| eval qos=coalesce(qos_class, traffic_class)
| eval bw_used=coalesce(bandwidth_used, bytes_sent)
| eval drops=coalesce(drop_count, dropped_packets, 0)
| stats sum(bw_used) as total_bandwidth sum(drops) as total_drops dc(actual) as paths_used by app, qos, policy
| eval steering_ok=if(paths_used=1, "CONSISTENT", "MULTI_PATH -- traffic split")
| eval drop_concern=if(total_drops > 0, "DROPS -- QoS enforcement dropping packets", "No drops")
| where total_drops > 0 OR steering_ok="MULTI_PATH"
| eval severity=case(qos="Realtime" AND total_drops > 0, "HIGH -- voice/video packets dropped", total_drops > 100, "WARNING -- significant drops", 1==1, "INFO")
| sort severity, -total_drops
```

### Step 3 — - Validate
(a) Start a Zoom call and verify it's classified as "Realtime" and steered to the preferred path.
(b) Compare with Citrix SD-WAN Orchestrator: Monitor > Applications.
(c) Check QoS class distribution matches expected policy.

### Step 4 — - Operationalize
Dashboard ("Citrix SD-WAN -- Application Steering"):
* Row 1 -- Single-value: "Applications tracked", "QoS drops", "Realtime drops", "Multi-path apps".
* Row 2 -- Application steering analysis.
* Row 3 -- Bandwidth by QoS class pie chart.

Alerting:
* High (Realtime class drops > 0): voice/video quality impacted by QoS enforcement.
* Warning (significant drops in any class): bandwidth contention.

### Step 5 — - Troubleshooting

* **Realtime traffic being dropped** -- Not enough bandwidth allocated to Realtime class. Check QoS bandwidth allocation in Orchestrator: Configuration > QoS.

* **Application misclassified** -- Citrix SD-WAN uses DPI for classification. If an application is in the wrong class, create a custom application rule in Orchestrator.

* **Traffic not following expected path** -- If the preferred path has poor quality, SD-WAN will steer to an alternate path. Check path health (UC-5.3.38).

## SPL

```spl
index=sdwan (sourcetype="citrix:sdwan:app_route" OR sourcetype="citrix:sdwan:qos") earliest=-4h
| eval drops=tonumber(drops), app=coalesce(app_name, application, "unknown"), psel=coalesce(path_selected, selected_path, "unknown")
| bin _time span=5m
| stats sum(drops) as total_drops, count as dec_events, values(psel) as paths_used, values(qos_class) as qos by _time, app, site_id
| where total_drops>0 OR dec_events>1000
| table _time, site_id, app, total_drops, dec_events, paths_used, qos
```

## Visualization

Stacked area: drop count by `qos_class`; Sankey or table: `app` to `path_selected` distribution; timechart: steering change rate for top apps.

## Known False Positives

Application mix changes, guest networks, and cloud moves can re-steer classes without a misconfiguration.

## References

- [Citrix — SD-WAN application quality of service](https://docs.citrix.com/en-us/citrix-sd-wan/11-4/)
