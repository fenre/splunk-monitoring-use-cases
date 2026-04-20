---
id: "1.1.11"
title: "Kernel Panic Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.11 · Kernel Panic Detection

## Description

Kernel panics cause immediate system crashes and potential data corruption. Often indicates hardware failure, driver issues, or memory corruption.

## Value

Kernel panics cause immediate system crashes and potential data corruption. Often indicates hardware failure, driver issues, or memory corruption.

## Implementation

Forward syslog and enable dmesg scripted input. Create critical alert on `kernel panic` or `Oops:` keywords. Correlate with hardware health data (IPMI) for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Syslog.
• Ensure the following data sources are available: `sourcetype=syslog`, `dmesg`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog and enable dmesg scripted input. Create critical alert on `kernel panic` or `Oops:` keywords. Correlate with hardware health data (IPMI) for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog ("kernel panic" OR "Kernel panic" OR "BUG:" OR "Oops:" OR "Call Trace:")
| table _time host _raw
| sort -_time
```

Understanding this SPL

**Kernel Panic Detection** — Kernel panics cause immediate system crashes and potential data corruption. Often indicates hardware failure, driver issues, or memory corruption.

Documented **Data sources**: `sourcetype=syslog`, `dmesg`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Kernel Panic Detection**): table _time host _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Count by host, Alert panel (critical).

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
index=os sourcetype=syslog ("kernel panic" OR "Kernel panic" OR "BUG:" OR "Oops:" OR "Call Trace:")
| table _time host _raw
| sort -_time
```

## Visualization

Events timeline, Count by host, Alert panel (critical).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
