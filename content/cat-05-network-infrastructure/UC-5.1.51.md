<!-- AUTO-GENERATED from UC-5.1.51.json — DO NOT EDIT -->

---
id: "5.1.51"
title: "Uplink Health and Failover Events (Meraki MS)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.51 · Uplink Health and Failover Events (Meraki MS)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with uplink health and failover events so the team can act before it grows into a bigger outage.*

---

## Description

Monitors primary/secondary uplink status to detect failover events and connection issues.

## Value

NOC teams monitor Meraki MS uplink health and failover events, detecting uplink failures that disconnect all downstream devices and trigger failover to redundant paths.

## Implementation

1. PRIMARY (SC4S path): deploy the Meraki vendor pack in SC4S so MX appliance syslog lands at sourcetype=meraki. In Meraki Dashboard go to Network-wide -> General -> Reporting and enable Appliance event log forwarding to your SC4S receiver. 2. The SPL uses `rex` to pull the event_type token and the target uplink (wan1/wan2/cellular) from the free-form syslog body. 3. SECONDARY (API TA path) — if you do NOT have SC4S, the same condition is surfaced in `meraki:assurancealerts` as `type="cellular_failover"` under `categoryType="connectivity"`. A working alternate query is: `index=meraki sourcetype="meraki:assurancealerts" categoryType="connectivity" type="cellular_failover" | rename scope.devices{}.serial as device_serial, network.name as network_name | search dismissedAt="null" | stats latest(severity) as severity, latest(title) as title by device_serial, network_name`. Pair either query with the Devices Uplinks Loss and Latency input (sourcetype=meraki:devicesuplinkslossandlatency) for uplink-quality context leading up to and following the failover.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk Connect for Syslog (SC4S)` Meraki vendor pack (PRIMARY) — alternate path: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) Assurance Alerts input..
- Ensure the following data sources are available: PRIMARY: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests MX appliance syslog under sourcetype=meraki — uplink failover messages carry `host` (appliance hostname) and a free-form body like 'failover to wan1' / 'failover to cellular' / 'Cellular connection up|down'. SECONDARY (API TA path): Splunk_TA_cisco_meraki (Splunkbase #5580) Assurance Alerts input (sourcetype=meraki:assurancealerts) surfaces the same condition as `type=cellular_failover` events under `categoryType=connectivity` — usable when you do not have SC4S. The two paths give a complementary view: syslog catches every transition with second-level granularity, the assurance alert summarises the open failover state..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. PRIMARY (SC4S path): deploy the Meraki vendor pack in SC4S so MX appliance syslog lands at sourcetype=meraki. In Meraki Dashboard go to Network-wide -> General -> Reporting and enable Appliance event log forwarding to your SC4S receiver. 2. The SPL uses `rex` to pull the event_type token and the target uplink (wan1/wan2/cellular) from the free-form syslog body. 3. SECONDARY (API TA path) — if you do NOT have SC4S, the same condition is surfaced in `meraki:assurancealerts` as `type="cellular_f…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki"
    ("uplink" OR "failover" OR "Cellular connection")
    earliest=-24h
| rex "(?<event_type>uplink|failover|recovered|failed|Cellular connection up|Cellular connection down)"
| rex "to (?<target_uplink>wan\d|cellular)"
| stats count as failover_count,
        values(event_type) as event_types,
        values(target_uplink) as targets,
        min(_time) as first_seen,
        max(_time) as last_seen
         by host
| where failover_count > 0
| convert ctime(first_seen) ctime(last_seen)
| sort - failover_count
```

#### Understanding this SPL

**Uplink Health and Failover Events (Meraki MS)** — NOC teams monitor Meraki MS uplink health and failover events, detecting uplink failures that disconnect all downstream devices and trigger failover to redundant paths.

Documented **Data sources**: PRIMARY: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests MX appliance syslog under sourcetype=meraki — uplink failover messages carry `host` (appliance hostname) and a free-form body like 'failover to wan1' / 'failover to cellular' / 'Cellular connection up|down'. SECONDARY (API TA path): Splunk_TA_cisco_meraki (Splunkbase #5580) Assurance Alerts input (sourcetype=meraki:assurancealerts) surfaces the same condition as `type=cellular_failover` events under `categoryType=connectivity` — usable when you do not have SC4S. The two paths give a complementary view: syslog catches every transition with second-level granularity, the assurance alert summarises the open failover state. **App/TA** (typical add-on context): `Splunk Connect for Syslog (SC4S)` Meraki vendor pack (PRIMARY) — alternate path: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) Assurance Alerts input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where failover_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Pipeline stage (see **Uplink Health and Failover Events (Meraki MS)**): convert ctime(first_seen) ctime(last_seen)
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Uplink status dashboard; failover event timeline; connection health gauge.

## SPL

```spl
index=meraki sourcetype="meraki"
    ("uplink" OR "failover" OR "Cellular connection")
    earliest=-24h
| rex "(?<event_type>uplink|failover|recovered|failed|Cellular connection up|Cellular connection down)"
| rex "to (?<target_uplink>wan\d|cellular)"
| stats count as failover_count,
        values(event_type) as event_types,
        values(target_uplink) as targets,
        min(_time) as first_seen,
        max(_time) as last_seen
         by host
| where failover_count > 0
| convert ctime(first_seen) ctime(last_seen)
| sort - failover_count
```

## Visualization

Uplink status dashboard; failover event timeline; connection health gauge.

## Known False Positives

Meraki cloud delays, dashboard API limits, and large site templates can look like a gap. Confirm in dashboard before opening a P1 on Splunk only.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
