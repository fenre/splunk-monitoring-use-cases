---
id: "1.1.51"
title: "TCP Retransmission Rate Elevation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.51 · TCP Retransmission Rate Elevation

## Description

High retransmission rates indicate network congestion, packet loss, or application issues affecting throughput.

## Value

High retransmission rates indicate network congestion, packet loss, or application issues affecting throughput.

## Implementation

Create a scripted input that parses /proc/net/snmp for TCP retransmission metrics. Track TcpRetransSegs and TcpOutSegs to calculate retransmission percentage. Alert when above 2% or 3x baseline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:tcp_stats, /proc/net/tcp`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that parses /proc/net/snmp for TCP retransmission metrics. Track TcpRetransSegs and TcpOutSegs to calculate retransmission percentage. Alert when above 2% or 3x baseline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=netstat host=*
| bin _time span=5m
| stats sum(retransSegs) as retrans by host, _time
| streamstats window=100 avg(retrans) as baseline stdev(retrans) as stddev by host
| eval upper=baseline+(2*stddev)
| where retrans > upper
```

Understanding this SPL

**TCP Retransmission Rate Elevation** — High retransmission rates indicate network congestion, packet loss, or application issues affecting throughput.

Documented **Data sources**: `sourcetype=custom:tcp_stats, /proc/net/tcp`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: netstat. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=netstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `streamstats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **upper** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where retrans > upper` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Anomaly Chart

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
index=os sourcetype=netstat host=*
| bin _time span=5m
| stats sum(retransSegs) as retrans by host, _time
| streamstats window=100 avg(retrans) as baseline stdev(retrans) as stddev by host
| eval upper=baseline+(2*stddev)
| where retrans > upper
```

## Visualization

Timechart, Anomaly Chart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
