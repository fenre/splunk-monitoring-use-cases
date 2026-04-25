<!-- AUTO-GENERATED from UC-6.1.31.json — DO NOT EDIT -->

---
id: "6.1.31"
title: "MDS VSAN Health and Isolation Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.31 · MDS VSAN Health and Isolation Events

## Description

VSANs provide logical SAN segmentation. VSAN isolation events (caused by ISL failures, misconfigured trunking, or merge failures) split the fabric and break host-to-storage paths. Detecting isolation within seconds is essential for maintaining storage availability.

## Value

VSANs provide logical SAN segmentation. VSAN isolation events (caused by ISL failures, misconfigured trunking, or merge failures) split the fabric and break host-to-storage paths. Detecting isolation within seconds is essential for maintaining storage availability.

## Implementation

Forward MDS syslog with facility-level logging. Alert immediately on VSAN isolation or segmentation events. Correlate with ISL link status (UC-6.1.27) and zone changes (UC-6.1.29) to identify root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `cisco:mds` syslog, SNMP TA.
• Ensure the following data sources are available: MDS syslog (VSAN state change, merge failure, isolation events), SNMP.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward MDS syslog with facility-level logging. Alert immediately on VSAN isolation or segmentation events. Correlate with ISL link status (UC-6.1.27) and zone changes (UC-6.1.29) to identify root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:mds" "VSAN" ("isolated" OR "merge" OR "segmented" OR "down")
| stats count latest(_time) as last_event by switch, vsan_id, event_type
| where event_type IN ("isolated","segmented","merge_failure")
| table switch, vsan_id, event_type, count, last_event
| sort -last_event
```

Understanding this SPL

**MDS VSAN Health and Isolation Events** — VSANs provide logical SAN segmentation. VSAN isolation events (caused by ISL failures, misconfigured trunking, or merge failures) split the fabric and break host-to-storage paths. Detecting isolation within seconds is essential for maintaining storage availability.

Documented **Data sources**: MDS syslog (VSAN state change, merge failure, isolation events), SNMP. **App/TA** (typical add-on context): `cisco:mds` syslog, SNMP TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:mds. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:mds". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch, vsan_id, event_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where event_type IN ("isolated","segmented","merge_failure")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **MDS VSAN Health and Isolation Events**): table switch, vsan_id, event_type, count, last_event
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare port and error counters with the switch CLI (`show interface`, `porterrshow`) or DCNM for the same switch, port, and interval.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Status grid (VSAN health), Table (isolation events), Topology map (VSAN segmentation).

## SPL

```spl
index=network sourcetype="cisco:mds" "VSAN" ("isolated" OR "merge" OR "segmented" OR "down")
| stats count latest(_time) as last_event by switch, vsan_id, event_type
| where event_type IN ("isolated","segmented","merge_failure")
| table switch, vsan_id, event_type, count, last_event
| sort -last_event
```

## Visualization

Status grid (VSAN health), Table (isolation events), Topology map (VSAN segmentation).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
