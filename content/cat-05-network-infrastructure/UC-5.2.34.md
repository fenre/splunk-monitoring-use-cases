<!-- AUTO-GENERATED from UC-5.2.34.json — DO NOT EDIT -->

---
id: "5.2.34"
title: "Internet Uplink Failover Events and Recovery Time (Meraki MX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.34 · Internet Uplink Failover Events and Recovery Time (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We see when a site moves between primary and backup internet so the team can confirm a cutover is real, fast, and expected.*

---

## Description

Tracks failover events, recovery time, and uplink behavior to ensure high availability.

## Value

NOC teams track Meraki MX uplink failover events and measure recovery time to assess high-availability effectiveness and identify flapping circuits requiring ISP escalation.

## Implementation

1. Configure SC4S for MX syslog and enable Appliance event log. 2. Use rex to extract the failover target and cellular state. 3. The 'failover to cellular' + subsequent 'Cellular connection up' pair indicates a successful WAN-to-LTE failover. 4. For continuous uplink quality context combine with the API-side Devices Uplinks Loss and Latency input.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving MX syslog. Uplink failover events use type=events with message bodies 'failover to wan1', 'failover to cellular', 'Cellular connection up', 'Cellular connection down'..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MX syslog and enable Appliance event log. 2. Use rex to extract the failover target and cellular state. 3. The 'failover to cellular' + subsequent 'Cellular connection up' pair indicates a successful WAN-to-LTE failover. 4. For continuous uplink quality context combine with the API-side Devices Uplinks Loss and Latency input.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    ("failover" OR "uplink" OR "Cellular connection")
    earliest=-7d
| rex "failover to (?<target>wan\d|cellular)"
| rex "Cellular connection (?<cellular_state>up|down)"
| eval failover_event = if(isnotnull(target),"failover_to_"+target, null())
| eval cellular_event = if(isnotnull(cellular_state),"cellular_"+cellular_state, null())
| eval event_type = coalesce(failover_event, cellular_event)
| where isnotnull(event_type)
| stats count as event_count,
        values(event_type) as event_types,
        earliest(_time) as first_seen,
        latest(_time) as last_seen
         by host
| eval span_hours = round((last_seen - first_seen)/3600, 1)
| sort - event_count
```

#### Understanding this SPL

**Internet Uplink Failover Events and Recovery Time (Meraki MX)** — NOC teams track Meraki MX uplink failover events and measure recovery time to assess high-availability effectiveness and identify flapping circuits requiring ISP escalation.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving MX syslog. Uplink failover events use type=events with message bodies 'failover to wan1', 'failover to cellular', 'Cellular connection up', 'Cellular connection down'. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `eval` defines or adjusts **failover_event** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **cellular_event** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **event_type** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnotnull(event_type)` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **span_hours** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Failover timeline; recovery time gauge; uplink failure cause pie chart.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    ("failover" OR "uplink" OR "Cellular connection")
    earliest=-7d
| rex "failover to (?<target>wan\d|cellular)"
| rex "Cellular connection (?<cellular_state>up|down)"
| eval failover_event = if(isnotnull(target),"failover_to_"+target, null())
| eval cellular_event = if(isnotnull(cellular_state),"cellular_"+cellular_state, null())
| eval event_type = coalesce(failover_event, cellular_event)
| where isnotnull(event_type)
| stats count as event_count,
        values(event_type) as event_types,
        earliest(_time) as first_seen,
        latest(_time) as last_seen
         by host
| eval span_hours = round((last_seen - first_seen)/3600, 1)
| sort - event_count
```

## Visualization

Failover timeline; recovery time gauge; uplink failure cause pie chart.

## Known False Positives

Test failovers, cable swaps, and ISP work can make uplink change messages noisy during business hours.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
