<!-- AUTO-GENERATED from UC-8.6.14.json — DO NOT EDIT -->

---
id: "8.6.14"
title: "Asterisk / FreePBX Call Quality and Trunk Status"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.14 · Asterisk / FreePBX Call Quality and Trunk Status

## Description

Call volume, ASR (Answer Seizure Ratio), ACD (Average Call Duration), and trunk registration indicate VoIP/PBX health. Trunk failures block inbound/outbound calls; quality metrics affect user experience.

## Value

Call volume, ASR (Answer Seizure Ratio), ACD (Average Call Duration), and trunk registration indicate VoIP/PBX health. Trunk failures block inbound/outbound calls; quality metrics affect user experience.

## Implementation

Forward Asterisk CDR (Call Detail Record) logs via Universal Forwarder. Parse caller, callee, duration, disposition, channel. For trunk status, use AMI (Asterisk Manager Interface) or `asterisk -rx "pjsip show endpoints"` via scripted input. Poll trunk registration status every 5 minutes. Calculate ASR (answered/total*100) and ACD per hour. Alert when ASR drops below 80% or trunk shows UNREACHABLE. Track call volume for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Asterisk AMI, CDR logs).
• Ensure the following data sources are available: Asterisk CDR logs, AMI events, SIP trunk status.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Asterisk CDR (Call Detail Record) logs via Universal Forwarder. Parse caller, callee, duration, disposition, channel. For trunk status, use AMI (Asterisk Manager Interface) or `asterisk -rx "pjsip show endpoints"` via scripted input. Poll trunk registration status every 5 minutes. Calculate ASR (answered/total*100) and ACD per hour. Alert when ASR drops below 80% or trunk shows UNREACHABLE. Track call volume for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=asterisk sourcetype="asterisk:cdr"
| eval duration_sec=tonumber(duration)
| bin _time span=1h
| stats count as calls, avg(duration_sec) as acd, count(eval(disposition=="ANSWERED")) as answered by, _time
| eval asr=round(answered/calls*100,2)
| where asr < 80 OR acd < 60
```

Understanding this SPL

**Asterisk / FreePBX Call Quality and Trunk Status** — Call volume, ASR (Answer Seizure Ratio), ACD (Average Call Duration), and trunk registration indicate VoIP/PBX health. Trunk failures block inbound/outbound calls; quality metrics affect user experience.

Documented **Data sources**: Asterisk CDR logs, AMI events, SIP trunk status. **App/TA** (typical add-on context): Custom (Asterisk AMI, CDR logs). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: asterisk; **sourcetype**: asterisk:cdr. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=asterisk, sourcetype="asterisk:cdr". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **duration_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **asr** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where asr < 80 OR acd < 60` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (ASR and ACD over time), Table (trunk status), Single value (calls per hour), Bar chart (call volume by trunk).

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
index=asterisk sourcetype="asterisk:cdr"
| eval duration_sec=tonumber(duration)
| bin _time span=1h
| stats count as calls, avg(duration_sec) as acd, count(eval(disposition=="ANSWERED")) as answered by, _time
| eval asr=round(answered/calls*100,2)
| where asr < 80 OR acd < 60
```

## Visualization

Line chart (ASR and ACD over time), Table (trunk status), Single value (calls per hour), Bar chart (call volume by trunk).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
