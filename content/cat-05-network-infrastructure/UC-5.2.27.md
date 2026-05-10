<!-- AUTO-GENERATED from UC-5.2.27.json — DO NOT EDIT -->

---
id: "5.2.27"
title: "NAT Pool Usage and Exhaustion Alerts (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.27 · NAT Pool Usage and Exhaustion Alerts (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We check how full shared public address pools are on the small office so new guests and new sites do not run out of outbound space.*

---

## Description

Monitors NAT pool utilization to prevent address exhaustion that could block outbound traffic.

## Value

Operations teams detect Meraki MX NAT port exhaustion events, identifying when outbound connection capacity is reached and investigating top connection consumers.

## Implementation

1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki and confirm Meraki alert profiles include 'NAT translation table near capacity' and 'connection table full'. 2. Configure SC4S to receive Meraki MX syslog (UDP/514) and forward the events sourcetype to Splunk; appliance NAT/connection-table syslog messages match type=events. 3. Pair the alert query above with a 'last 1h' real-time dashboard for branch operators.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts) and SC4S Meraki vendor pack (sourcetype=meraki, type=events) for syslog-side NAT exhaustion messages. NOTE: the Meraki Dashboard API does NOT expose live NAT translation table counters; alert-driven monitoring is the only practical path..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki and confirm Meraki alert profiles include 'NAT translation table near capacity' and 'connection table full'. 2. Configure SC4S to receive Meraki MX syslog (UDP/514) and forward the events sourcetype to Splunk; appliance NAT/connection-table syslog messages match type=events. 3. Pair the alert query above with a 'last 1h' real-time dashboard for branch operators.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="appliance"
    (title="*NAT*" OR title="*port*" OR title="*translation*" OR categoryType="appliance")
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity,
        latest(dismissedAt) as dismissed_at
         by deviceSerial, networkName
| where isnull(dismissed_at) AND alert_count > 0
| sort - alert_count
```

#### Understanding this SPL

**NAT Pool Usage and Exhaustion Alerts (Meraki MX)** — Operations teams detect Meraki MX NAT port exhaustion events, identifying when outbound connection capacity is reached and investigating top connection consumers.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts) and SC4S Meraki vendor pack (sourcetype=meraki, type=events) for syslog-side NAT exhaustion messages. NOTE: the Meraki Dashboard API does NOT expose live NAT translation table counters; alert-driven monitoring is the only practical path. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by deviceSerial, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where isnull(dismissed_at) AND alert_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge of NAT pool usage; capacity timeline; pool exhaustion alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="appliance"
    (title="*NAT*" OR title="*port*" OR title="*translation*" OR categoryType="appliance")
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity,
        latest(dismissedAt) as dismissed_at
         by deviceSerial, networkName
| where isnull(dismissed_at) AND alert_count > 0
| sort - alert_count
```

## Visualization

Gauge of NAT pool usage; capacity timeline; pool exhaustion alert dashboard.

## Known False Positives

New sites, guest Wi-Fi, and more endpoints can use more public NAT than last month without an exhaustion emergency.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
