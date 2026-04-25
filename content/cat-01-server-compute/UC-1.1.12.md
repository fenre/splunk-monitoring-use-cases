<!-- AUTO-GENERATED from UC-1.1.12.json — DO NOT EDIT -->

---
id: "1.1.12"
title: "NTP Time Sync Drift (Linux)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.12 · NTP Time Sync Drift (Linux)

## Description

Clock drift causes authentication failures (Kerberos), log correlation issues, transaction ordering problems, and certificate validation failures.

## Value

Clock drift causes authentication failures (Kerberos), log correlation issues, transaction ordering problems, and certificate validation failures.

## Implementation

Enable the `ntp` scripted input in Splunk_TA_nix (interval=300). It runs `ntpq -pn` and outputs peer data. The `offset` field is in milliseconds. Alert when offset exceeds 100ms or stratum exceeds 5.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=ntp` (scripted input via `ntpq -p` or `chronyc tracking`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `ntp` scripted input in Splunk_TA_nix (interval=300). It runs `ntpq -pn` and outputs peer data. The `offset` field is in milliseconds. Alert when offset exceeds 100ms or stratum exceeds 5.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=ntp host=*
| eval offset_ms = abs(offset)
| stats latest(offset_ms) as drift_ms, latest(stratum) as stratum by host
| where drift_ms > 100 OR stratum > 5
| sort -drift_ms
```

Understanding this SPL

**NTP Time Sync Drift (Linux)** — Clock drift causes authentication failures (Kerberos), log correlation issues, transaction ordering problems, and certificate validation failures.

Documented **Data sources**: `sourcetype=ntp` (scripted input via `ntpq -p` or `chronyc tracking`). **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: ntp. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=ntp. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **offset_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where drift_ms > 100 OR stratum > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (drift over time by host), Table of hosts with excessive drift.

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
index=os sourcetype=ntp host=*
| eval offset_ms = abs(offset)
| stats latest(offset_ms) as drift_ms, latest(stratum) as stratum by host
| where drift_ms > 100 OR stratum > 5
| sort -drift_ms
```

## Visualization

Line chart (drift over time by host), Table of hosts with excessive drift.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
