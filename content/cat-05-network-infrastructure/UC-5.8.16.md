<!-- AUTO-GENERATED from UC-5.8.16.json — DO NOT EDIT -->

---
id: "5.8.16"
title: "Alert Volume Trending and Alert Fatigue Analysis (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.16 · Alert Volume Trending and Alert Fatigue Analysis (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you see when Meraki is throwing too many of the same alerts, so the team can tune and avoid crying wolf.*

---

## Description

Analyzes alert volume trends to optimize alerting rules and reduce false positives.

## Value

Network operations teams analyze Meraki alert volume trends to detect alert storms, identify noisy alert types causing operator fatigue, and optimize alert configurations for a sustainable signal-to-noise ratio.

## Implementation

Ingest webhook alerts. Track volume and types over time.

## Detailed Implementation

### Prerequisites
- Meraki alert data from Dashboard API (`sourcetype=meraki:api:alerts`) and/or syslog (`sourcetype=meraki:events`). Key fields: `alertType`, `alertLevel` (informational/warning/critical), `network`, `deviceSerial`, `deviceName`, `alertData`.
- Meraki generates alerts for: device offline, uplink failure, VPN connectivity loss, rogue AP detection, firmware updates, port status changes, and many more. High-volume environments can generate hundreds of alerts per hour, leading to alert fatigue.

### Step 1 — Configure data collection
Verify alert data:
```spl
index=meraki (sourcetype="meraki:api:alerts" OR sourcetype="meraki:events") earliest=-24h
| stats count by alertType, alertLevel
| sort -count
```

### Step 2 — Create the search and alert

**Primary search — Alert volume trending with fatigue analysis:**
```spl
index=meraki (sourcetype="meraki:api:alerts" OR sourcetype="meraki:events") earliest=-7d
| bin _time span=1h
| stats count as alerts dc(alertType) as alert_types dc(deviceSerial) as devices by _time
| eventstats avg(alerts) as avg_hourly stdev(alerts) as std_hourly
| eval upper_threshold=avg_hourly + (3 * std_hourly)
| eval is_storm=if(alerts > upper_threshold, "YES", "NO")
| eval fatigue_risk=case(alerts > 100, "HIGH", alerts > 50, "MEDIUM", 1==1, "LOW")
```

#### Understanding this SPL: Alert fatigue is when operators stop paying attention to alerts because there are too many. This search establishes a baseline alert volume and detects spikes (alert storms) that indicate either a real incident or a noisy alert configuration. The fatigue risk assessment helps prioritize alert tuning — if most hours are "HIGH", the alert configuration needs significant reduction.

**Top noisy alert types:**
```spl
index=meraki (sourcetype="meraki:api:alerts" OR sourcetype="meraki:events") earliest=-7d
| stats count as total dc(deviceSerial) as devices first(_time) as first_seen latest(_time) as last_seen by alertType, alertLevel
| eval daily_avg=round(total/7, 1)
| eval signal_to_noise=case(alertLevel="critical" AND daily_avg > 50, "NOISY_CRITICAL", alertLevel="warning" AND daily_avg > 100, "NOISY_WARNING", alertLevel="informational" AND daily_avg > 200, "EXCESSIVE_INFO", 1==1, "ACCEPTABLE")
| where signal_to_noise!="ACCEPTABLE"
| sort -total
```

**Alert-to-incident ratio:**
```spl
index=meraki (sourcetype="meraki:api:alerts" OR sourcetype="meraki:events") alertLevel="critical" earliest=-30d
| bin _time span=1d
| stats count as critical_alerts by _time
| eventstats avg(critical_alerts) as avg_daily_critical
| eval actionable_estimate=round(avg_daily_critical * 0.1, 0)
| eval noise_estimate=round(avg_daily_critical * 0.9, 0)
```

### Step 3 — Validate
(a) Compare alert counts with Meraki Dashboard: Organization > Alert log. Numbers should match within polling intervals.
(b) Review the top 10 noisy alert types with the network team — determine which are actionable vs. noise.
(c) Verify alert storm detection: cause a known alert spike (e.g., reboot multiple devices) and confirm the anomaly detection triggers.

### Step 4 — Operationalize
Dashboard ("Meraki Alert Health"):
- Row 1 — Single-value tiles: "Alerts (24h)", "Alert storms detected", "Noisy alert types", "Fatigue risk level".
- Row 2 — Alert volume trending (7 days) with anomaly bands.
- Row 3 — Top noisy alert types with tuning recommendations.
- Row 4 — Daily critical alert count with estimated actionable %.

Alerting:
- Warning (alert volume > 3σ above baseline): alert storm — possible incident or configuration issue.
- Info (weekly): alert fatigue report — noisy types to consider disabling or suppressing.

### Step 5 — Troubleshooting

- **Alert volume consistently high** — Disable informational alerts for non-critical device types (sensors, cameras). Tune warning thresholds in Meraki Dashboard: Network > Alerts.

- **Alert storms correlate with firmware upgrades** — During firmware rollouts, devices reboot and generate offline/online alert pairs. Suppress alerts during planned upgrade windows.

- **Critical alerts with no action taken** — Review alert routing: are critical alerts reaching the right team? If they go to a shared email, they may be ignored. Route to PagerDuty or a dedicated Slack channel.

## SPL

```spl
index=cisco_network sourcetype="meraki:webhook"
| timechart count as alert_count by alert_type
| eval alert_ratio=alert_count/sum(alert_count)
```

## Visualization

Alert volume timeline; alert type pie chart; trend sparklines.

## Known False Positives

Real incidents naturally raise alert volume; trend suppression and dedup before you tune thresholds so you do not hide true problems.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
