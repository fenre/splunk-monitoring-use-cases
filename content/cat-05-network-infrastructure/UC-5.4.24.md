<!-- AUTO-GENERATED from UC-5.4.24.json — DO NOT EDIT -->

---
id: "5.4.24"
title: "Wireless Health Score Trending (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.24 · Wireless Health Score Trending (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch wireless health score trending (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Provides a composite health metric across all APs to facilitate executive reporting and trend analysis.

## Value

Network operations teams track Meraki wireless bandwidth consumption by SSID and client, correlating usage with WAN capacity to detect bandwidth abuse and validate traffic shaping policy effectiveness.

## Implementation

1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. 2. The TA polls GET /organizations/{orgId}/assurance/alerts hourly and emits one event per open alert with deviceType, deviceSerial, categoryType, title, severity, dismissedAt. 3. Filter to deviceType=wireless for AP-specific issues. 4. Meraki does not expose a numeric health score per AP via the API; counting open alerts and grading by severity is the closest workable approximation. 5. Pair with the Wireless Packet Loss by Device input for a continuous loss-based health metric.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts, hourly). Optional: Wireless Packet Loss by Device input for a numeric loss-based score..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. 2. The TA polls GET /organizations/{orgId}/assurance/alerts hourly and emits one event per open alert with deviceType, deviceSerial, categoryType, title, severity, dismissedAt. 3. Filter to deviceType=wireless for AP-specific issues. 4. Meraki does not expose a numeric health score per AP via the API; counting open alerts and grading by severity is the closest workable approximation. 5. Pair with the Wireless Packet Loss by Device i…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="wireless"
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity,
        latest(dismissedAt) as dismissed_at
         by deviceSerial, deviceName, networkName, categoryType
| where isnull(dismissed_at)
| eval health_band = case(
    alert_count>=10 OR severity="critical", "Critical",
    alert_count>=5 OR severity="warning", "Warning",
    alert_count>0, "Informational",
    1=1, "Healthy")
| sort - alert_count
```

#### Understanding this SPL

**Wireless Health Score Trending (Meraki MR)** — Network operations teams track Meraki wireless bandwidth consumption by SSID and client, correlating usage with WAN capacity to detect bandwidth abuse and validate traffic shaping policy effectiveness.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts, hourly). Optional: Wireless Packet Loss by Device input for a numeric loss-based score. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by deviceSerial, deviceName, networkName, categoryType** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where isnull(dismissed_at)` — typically the threshold or rule expression for this monitoring goal.
- `eval` defines or adjusts **health_band** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge of overall health; bar chart of individual AP health; trend sparkline; KPI dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="wireless"
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity,
        latest(dismissedAt) as dismissed_at
         by deviceSerial, deviceName, networkName, categoryType
| where isnull(dismissed_at)
| eval health_band = case(
    alert_count>=10 OR severity="critical", "Critical",
    alert_count>=5 OR severity="warning", "Warning",
    alert_count>0, "Informational",
    1=1, "Healthy")
| sort - alert_count
```

## Visualization

Gauge of overall health; bar chart of individual AP health; trend sparkline; KPI dashboard.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
