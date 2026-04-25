<!-- AUTO-GENERATED from UC-1.1.124.json — DO NOT EDIT -->

---
id: "1.1.124"
title: "Linux Entropy Pool Depletion"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.124 · Linux Entropy Pool Depletion

## Description

Low entropy blocks /dev/random and can stall crypto operations (SSL handshakes, key generation). Detecting depletion prevents application hangs and security failures.

## Value

Low entropy blocks /dev/random and can stall crypto operations (SSL handshakes, key generation). Detecting depletion prevents application hangs and security failures.

## Implementation

Create a scripted input that reads `cat /proc/sys/kernel/random/entropy_avail` and optionally `poolsize`. Run every 60 seconds. Parse entropy_avail as integer. Alert when entropy drops below 200 (warning) or 100 (critical). Consider haveged or rng-tools for entropy generation on VMs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (scripted input).
• Ensure the following data sources are available: `/proc/sys/kernel/random/entropy_avail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that reads `cat /proc/sys/kernel/random/entropy_avail` and optionally `poolsize`. Run every 60 seconds. Parse entropy_avail as integer. Alert when entropy drops below 200 (warning) or 100 (critical). Consider haveged or rng-tools for entropy generation on VMs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=entropy host=*
| bin _time span=5m
| stats avg(entropy_avail) as entropy by host, _time
| where entropy < 500
```

Understanding this SPL

**Linux Entropy Pool Depletion** — Low entropy blocks /dev/random and can stall crypto operations (SSL handshakes, key generation). Detecting depletion prevents application hangs and security failures.

Documented **Data sources**: `/proc/sys/kernel/random/entropy_avail`. **App/TA** (typical add-on context): `Splunk_TA_nix` (scripted input). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: entropy. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=entropy. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Buckets and averages `entropy_avail` per host for alerting on low-pool conditions.
• Filters the current rows with `where entropy < 500` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (entropy_avail), Line chart (entropy over time by host), Table of hosts below threshold.

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
index=os sourcetype=entropy host=*
| bin _time span=5m
| stats avg(entropy_avail) as entropy by host, _time
| where entropy < 500
```

## Visualization

Single value (entropy_avail), Line chart (entropy over time by host), Table of hosts below threshold.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
