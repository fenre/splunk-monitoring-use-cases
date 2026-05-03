<!-- AUTO-GENERATED from UC-5.7.16.json — DO NOT EDIT -->

---
id: "5.7.16"
title: "Flow Exporter Health and Missing Exporter Detection"
status: "verified"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-5.7.16 · Flow Exporter Health and Missing Exporter Detection

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Operations, Data Quality &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep a roll call of every box that should whisper traffic summaries to us. When one goes quiet longer than we agreed, we poke someone before blind spots spread.*

---

## Description

Joins an authoritative exporter inventory lookup with recent flow observations to list devices that stopped emitting templates or fell below expected cadence within the monitoring window.

## Value

Network reliability teams restore visibility before security analytics lose coverage; change managers validate maintenance completions; auditors receive evidence that critical routers continuously contribute telemetry.

## Implementation

Maintain `flow_exporter_inventory.csv`; schedule hourly join; integrate paging for tier-one edges; archive weekly compliance snapshots.

## Detailed Implementation

### Prerequisites
- Completed discovery of every router and firewall authorized to export flows including standby contexts.
- Consistent field naming for exporter identities—normalize via transforms if vendors differ.
- Time synchronization within five hundred milliseconds across exporters.

### Step 1 — Configure data collection
Populate the lookup from your configuration management database export; include site, role, and maintenance calendar identifiers.

### Step 2 — Create the search
Add adaptive thresholds: backbone devices alert after thirty minutes, branch offices after two hours. Supplement with `metadata` searches verifying Universal Forwarder queues if syslog heartbeats exist.

### Step 3 — Validate
Disable export on a lab router and confirm alert correlation within one scheduled run. Re-enable and verify automatic clearance.

### Step 4 — Operationalize
Executive dashboard tile counts missing exporters by region; automated tickets assign to on-call network pods using lookup routing columns.

### Step 5 — Troubleshooting
False stale states occur when management addressing differs from export sourcing—store both in the lookup. Satellite links may batch flows; widen thresholds modestly after observing variance.

## SPL

```spl
| inputlookup flow_exporter_inventory.csv
| eval expected_exporter=exporter_ip
| join type=left expected_exporter [
    search index=netflow earliest=-2h
    | eval exporter_ip=coalesce(exporter_ip, agent, device_ip)
    | stats latest(_time) as last_seen sum(bytes) as bytes sum(packets) as pkts by exporter_ip
    | rename exporter_ip as expected_exporter
]
| eval minutes_since_seen=if(isnotnull(last_seen), round((now()-last_seen)/60, 1), null())
| fillnull value=0 bytes pkts
| where isnull(last_seen) OR minutes_since_seen>90
| eval status=if(isnull(last_seen), "NO_TELEMETRY", "STALE")
| sort last_seen
| table site expected_exporter status minutes_since_seen bytes pkts last_seen
```

## Visualization

Single-value tiles for missing versus stale; geographic map colored by site status; timeline of exporter counts.

## Known False Positives

Planned outages and daylight-saving skew can pause streams. Devices failing over to standby management interfaces may appear under a different exporter key until lookups catch up.

## References

- [Splunk Documentation — NetFlow Introduction](https://docs.splunk.com/Documentation/NetFlow/latest/NetFlow/Introduction)
- [Cisco — NetFlow Export FAQ](https://www.cisco.com/c/en/us/support/docs/ios-nx-os-software/ios-netflow/23921-configflowdump.html)
