<!-- AUTO-GENERATED from UC-5.4.14.json — DO NOT EDIT -->

---
id: "5.4.14"
title: "Excessive Client Roaming Activity (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.14 · Excessive Client Roaming Activity (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch excessive client roaming activity (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Detects unstable roaming patterns and AP handoff issues that cause latency spikes and dropped connections.

## Value

Network operations teams detect excessive wireless client roaming on Meraki MR networks, identifying ping-pong patterns between AP pairs to optimize RF design, power levels, and cell boundaries.

## Implementation

1. Configure SC4S for MR syslog. 2. Group by client_aid (which is a Meraki-issued association identifier persistent for a session). 3. Filter for clients seen on >3 APs with >20 association events in 24h — these are 'sticky-client' or band-steering loop candidates. 4. Identifying the underlying physical client: the client MAC isn't in the syslog payload directly; correlate with the API-side Wireless Packet Loss by Device input (meraki:wirelessdevicespacketlossbydevice) or the Meraki Dashboard -> Wireless -> Clients page.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR access-point syslog. Roaming = a client with high association/disassociation event count across multiple APs (host field). Each event carries aid (association id), vap, channel..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MR syslog. 2. Group by client_aid (which is a Meraki-issued association identifier persistent for a session). 3. Filter for clients seen on >3 APs with >20 association events in 24h — these are 'sticky-client' or band-steering loop candidates. 4. Identifying the underlying physical client: the client MAC isn't in the syslog payload directly; correlate with the API-side Wireless Packet Loss by Device input (meraki:wirelessdevicespacketlossbydevice) or the Meraki Dashboard ->…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    (type=association OR type=disassociation)
    earliest=-24h
| rex "aid='(?<client_aid>\d+)'"
| rex "vap='(?<vap_id>\d+)'"
| rex "channel='(?<channel>\d+)'"
| stats count as event_count,
        dc(host) as ap_count,
        values(host) as ap_names
         by client_aid
| where event_count > 20 AND ap_count > 3
| sort - event_count
```

#### Understanding this SPL

**Excessive Client Roaming Activity (Meraki MR)** — Network operations teams detect excessive wireless client roaming on Meraki MR networks, identifying ping-pong patterns between AP pairs to optimize RF design, power levels, and cell boundaries.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR access-point syslog. Roaming = a client with high association/disassociation event count across multiple APs (host field). Each event carries aid (association id), vap, channel. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by client_aid** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where event_count > 20 AND ap_count > 3` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of heavy roamers; line chart of roaming frequency by client; network diagram showing roam paths.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    (type=association OR type=disassociation)
    earliest=-24h
| rex "aid='(?<client_aid>\d+)'"
| rex "vap='(?<vap_id>\d+)'"
| rex "channel='(?<channel>\d+)'"
| stats count as event_count,
        dc(host) as ap_count,
        values(host) as ap_names
         by client_aid
| where event_count > 20 AND ap_count > 3
| sort - event_count
```

## Visualization

Table of heavy roamers; line chart of roaming frequency by client; network diagram showing roam paths.

## Known False Positives

Clients may roam often when people move between floors, during large meetings, or when access points reboot; some clients also stay 'sticky' and look noisy without a real outage.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
