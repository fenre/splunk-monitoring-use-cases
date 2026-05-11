<!-- AUTO-GENERATED from UC-5.1.48.json — DO NOT EDIT -->

---
id: "5.1.48"
title: "QoS Queue Drops and Priority Violations (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.48 · QoS Queue Drops and Priority Violations (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with qos queue drops and priority violations so the team can act before it grows into a bigger outage.*

---

## Description

Detects QoS queue overflow and drops that indicate traffic priority issues.

## Value

Network engineers monitor Meraki MS QoS queue drops and DSCP priority violations, ensuring voice and video traffic receives proper priority queuing and classification.

## Implementation

1. Enable Assurance Alerts input. 2. Filter to deviceType=switch with queue/drop/QoS/congest keywords. 3. For configuration-drift tracking on QoS policies use the Audit input filtered to page='Switch QoS' or page='Switch ACLs'. 4. Live per-queue drop telemetry is not available; use Meraki Dashboard -> Network-wide -> Traffic analytics for application-level visibility instead.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: Meraki MS does NOT emit per-queue drop counters to syslog or the Dashboard API. QoS visibility is limited to configuration audit (meraki:audit) and assurance alerts on congestion-related issues. For live queue depths use SNMP polling with CISCO-CLASS-BASED-QOS-MIB if the switch supports it (older MS models do not)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable Assurance Alerts input. 2. Filter to deviceType=switch with queue/drop/QoS/congest keywords. 3. For configuration-drift tracking on QoS policies use the Audit input filtered to page='Switch QoS' or page='Switch ACLs'. 4. Live per-queue drop telemetry is not available; use Meraki Dashboard -> Network-wide -> Traffic analytics for application-level visibility instead.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="MS"
    (title="*queue*" OR title="*drop*" OR title="*QoS*"
     OR title="*congest*")
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity
         by scope.devices{}.serial, scope.devices{}.name, network.name
| sort - alert_count
```

#### Understanding this SPL

**QoS Queue Drops and Priority Violations (Meraki MS)** — Network engineers monitor Meraki MS QoS queue drops and DSCP priority violations, ensuring voice and video traffic receives proper priority queuing and classification.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: Meraki MS does NOT emit per-queue drop counters to syslog or the Dashboard API. QoS visibility is limited to configuration audit (meraki:audit) and assurance alerts on congestion-related issues. For live queue depths use SNMP polling with CISCO-CLASS-BASED-QOS-MIB if the switch supports it (older MS models do not). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by scope.devices{}.serial, scope.devices{}.name, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of drops by queue; time-series of drop events; traffic distribution pie chart.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="MS"
    (title="*queue*" OR title="*drop*" OR title="*QoS*"
     OR title="*congest*")
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity
         by scope.devices{}.serial, scope.devices{}.name, network.name
| sort - alert_count
```

## Visualization

Table of drops by queue; time-series of drop events; traffic distribution pie chart.

## Known False Positives

Large file transfers and video meetings fill priority queues in ways that are normal for the business—compare to historical drops per class.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
