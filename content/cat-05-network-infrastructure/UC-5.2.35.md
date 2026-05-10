<!-- AUTO-GENERATED from UC-5.2.35.json — DO NOT EDIT -->

---
id: "5.2.35"
title: "Cellular Modem Failover Activation and Usage (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.35 · Cellular Modem Failover Activation and Usage (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We mark when a site leans on cellular backup so you know who is on expensive paths and can fix the main line with less guesswork.*

---

## Description

Tracks cellular backup activation to monitor failover effectiveness and cellular data usage.

## Value

NOC teams track Meraki MX cellular modem failover activations and usage duration to monitor backup connectivity effectiveness and manage cellular data costs.

## Implementation

1. Configure SC4S for MX/MG syslog. 2. Cellular up/down transitions appear as type=events. 3. For 30-day cellular data totals join meraki:summarytopdevicesbyusage with meraki:devices filtered to productType=cellularGateway. 4. For per-SIM monthly billing breakdown integrate with the carrier API (out of Meraki TA scope).

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) for cellular failover events plus Splunk_TA_cisco_meraki Summary Top Devices by Usage and Devices inputs for cellular-device-specific data volume. NOTE: per-SIM data plan consumption is NOT available from Meraki; pull billing data from the carrier (AT&T, Verizon) directly..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MX/MG syslog. 2. Cellular up/down transitions appear as type=events. 3. For 30-day cellular data totals join meraki:summarytopdevicesbyusage with meraki:devices filtered to productType=cellularGateway. 4. For per-SIM monthly billing breakdown integrate with the carrier API (out of Meraki TA scope).

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    ("Cellular" OR "cellular" OR "LTE" OR "5G")
    earliest=-7d
| rex "Cellular connection (?<state>up|down)"
| stats count as cellular_events,
        values(state) as states,
        earliest(_time) as first_seen,
        latest(_time) as last_seen
         by host
| eval span_hours = round((last_seen - first_seen)/3600, 1)
| append [
    search index=meraki sourcetype="meraki:summarytopdevicesbyusage" earliest=-30d
    | join type=left serial [
        search index=meraki sourcetype="meraki:devices" productType="cellularGateway"
        | stats latest(name) as cellular_device by serial
      ]
    | where isnotnull(cellular_device)
    | stats latest(usage.total) as total_kb by cellular_device
    | eval total_gb = round(total_kb/1024/1024, 2)
  ]
```

#### Understanding this SPL

**Cellular Modem Failover Activation and Usage (Meraki MX)** — NOC teams track Meraki MX cellular modem failover activations and usage duration to monitor backup connectivity effectiveness and manage cellular data costs.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) for cellular failover events plus Splunk_TA_cisco_meraki Summary Top Devices by Usage and Devices inputs for cellular-device-specific data volume. NOTE: per-SIM data plan consumption is NOT available from Meraki; pull billing data from the carrier (AT&T, Verizon) directly. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **span_hours** — often to normalize units, derive a ratio, or prepare for thresholds.
- Appends rows from a subsearch with `append`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Cellular usage timeline; failover event table; data usage gauge.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    ("Cellular" OR "cellular" OR "LTE" OR "5G")
    earliest=-7d
| rex "Cellular connection (?<state>up|down)"
| stats count as cellular_events,
        values(state) as states,
        earliest(_time) as first_seen,
        latest(_time) as last_seen
         by host
| eval span_hours = round((last_seen - first_seen)/3600, 1)
| append [
    search index=meraki sourcetype="meraki:summarytopdevicesbyusage" earliest=-30d
    | join type=left serial [
        search index=meraki sourcetype="meraki:devices" productType="cellularGateway"
        | stats latest(name) as cellular_device by serial
      ]
    | where isnotnull(cellular_device)
    | stats latest(usage.total) as total_kb by cellular_device
    | eval total_gb = round(total_kb/1024/1024, 2)
  ]
```

## Visualization

Cellular usage timeline; failover event table; data usage gauge.

## Known False Positives

Carriers, signal checks, and planned tests can make cellular backup logs busy without a site-down situation.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
