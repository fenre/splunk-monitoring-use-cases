<!-- AUTO-GENERATED from UC-1.1.15.json — DO NOT EDIT -->

---
id: "1.1.15"
title: "Network Interface Errors"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.15 · Network Interface Errors

## Description

Interface errors (CRC, drops, overruns) indicate bad cables, failing NICs, or duplex mismatches. Catching early prevents intermittent application failures.

## Value

Interface errors (CRC, drops, overruns) indicate bad cables, failing NICs, or duplex mismatches. Catching early prevents intermittent application failures.

## Implementation

Enable `interfaces` scripted input (interval=300). Use `| delta` or `| streamstats` to track error rate deltas. Alert on increasing error counts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=interfaces`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `interfaces` scripted input (interval=300). Use `| delta` or `| streamstats` to track error rate deltas. Alert on increasing error counts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=interfaces host=*
| stats latest(RXerrors) as rx_errors, latest(TXerrors) as tx_errors, latest(Collisions) as collisions by host, Name
| where rx_errors > 0 OR tx_errors > 0
| sort -rx_errors
```

Understanding this SPL

**Network Interface Errors** — Interface errors (CRC, drops, overruns) indicate bad cables, failing NICs, or duplex mismatches. Catching early prevents intermittent application failures.

Documented **Data sources**: `sourcetype=interfaces`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: interfaces. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=interfaces. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, Name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where rx_errors > 0 OR tx_errors > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (interface, error type, count), Line chart of error rate over time.

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
index=os sourcetype=interfaces host=*
| stats latest(RXerrors) as rx_errors, latest(TXerrors) as tx_errors, latest(Collisions) as collisions by host, Name
| where rx_errors > 0 OR tx_errors > 0
| sort -rx_errors
```

## Visualization

Table (interface, error type, count), Line chart of error rate over time.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
