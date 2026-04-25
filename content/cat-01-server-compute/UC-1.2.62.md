<!-- AUTO-GENERATED from UC-1.2.62.json — DO NOT EDIT -->

---
id: "1.2.62"
title: "TCP Connection State Monitoring (Windows)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.62 · TCP Connection State Monitoring (Windows)

## Description

Excessive TIME_WAIT, CLOSE_WAIT, or ESTABLISHED connections indicate connection leaks, exhausted ephemeral ports, or application hanging. Causes service unavailability.

## Value

Connection-state failure modes are a classic *ops-scale* class—fire drills start when a host runs out of ephemeral ports, not at 90% CPU.

## Implementation

Configure Perfmon inputs for TCPv4 object: `Connections Established`, `Connection Failures`, `Connections Reset`, `Segments Retransmitted/sec` (interval=60). Also deploy a scripted input running `netstat -an | find /c "TIME_WAIT"` for state-level counts. Alert when established connections exceed application baseline by 2x or TIME_WAIT exceeds 5000 (ephemeral port exhaustion risk). Default ephemeral port range: 49152-65535 (16K ports).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:TCPv4` (counters: Connections Established, Connection Failures).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs for TCPv4 object: `Connections Established`, `Connection Failures`, `Connections Reset`, `Segments Retransmitted/sec` (interval=60). Also deploy a scripted input running `netstat -an | find /c "TIME_WAIT"` for state-level counts. Alert when established connections exceed application baseline by 2x or TIME_WAIT exceeds 5000 (ephemeral port exhaustion risk). Default ephemeral port range: 49152-65535 (16K ports).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:TCPv4" counter IN ("Connections Established","Connection Failures","Connections Reset")
| timechart span=5m avg(Value) as value by counter, host
| where value > 10000
```

Understanding this SPL

**TCP Connection State Monitoring (Windows)** — Excessive TIME_WAIT, CLOSE_WAIT, or ESTABLISHED connections indicate connection leaks, exhausted ephemeral ports, or application hanging. Causes service unavailability.

Documented **Data sources**: `sourcetype=Perfmon:TCPv4` (counters: Connections Established, Connection Failures). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:TCPv4. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:TCPv4". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by counter, host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where value > 10000` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src span=5m
| where count>0
```

Understanding this CIM / accelerated SPL

**TCP Connection State Monitoring (Windows)** — Excessive TIME_WAIT, CLOSE_WAIT, or ESTABLISHED connections indicate connection leaks, exhausted ephemeral ports, or application hanging. Causes service unavailability.

Documented **Data sources**: `sourcetype=Perfmon:TCPv4` (counters: Connections Established, Connection Failures). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` on the CIM data model in `cimModels` (see the accelerated SPL block). Enable that model in Data Model Acceleration.
• The `where` and `by` clauses mirror the intent of the primary SPL; if tstats is empty, confirm field aliases in Splunk CIM and the Windows TA.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (connection states over time), Gauge (established connections), Single value (TIME_WAIT count).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=perfmon sourcetype="Perfmon:TCPv4" counter IN ("Connections Established","Connection Failures","Connections Reset")
| timechart span=5m avg(Value) as value by counter, host
| where value > 10000
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src span=5m
| where count>0
```

## Visualization

Line chart (connection states over time), Gauge (established connections), Single value (TIME_WAIT count).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
