---
id: "1.1.52"
title: "Connection Tracking Table Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.52 · Connection Tracking Table Exhaustion

## Description

Conntrack table full prevents new network connections, causing application failures.

## Value

Conntrack table full prevents new network connections, causing application failures.

## Implementation

Create a scripted input that parses /proc/net/nf_conntrack_count and /proc/sys/net/netfilter/nf_conntrack_max. Alert when usage exceeds 80%, with escalation at 95%. Include recommendations to increase nf_conntrack_max.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:conntrack, /proc/net/nf_conntrack`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that parses /proc/net/nf_conntrack_count and /proc/sys/net/netfilter/nf_conntrack_max. Alert when usage exceeds 80%, with escalation at 95%. Include recommendations to increase nf_conntrack_max.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:conntrack host=*
| stats latest(current_count) as current, latest(max_size) as maximum by host
| eval usage_pct=(current/maximum)*100
| where usage_pct > 80
```

Understanding this SPL

**Connection Tracking Table Exhaustion** — Conntrack table full prevents new network connections, causing application failures.

Documented **Data sources**: `sourcetype=custom:conntrack, /proc/net/nf_conntrack`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:conntrack. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:conntrack. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **usage_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where usage_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Alert

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
index=os sourcetype=custom:conntrack host=*
| stats latest(current_count) as current, latest(max_size) as maximum by host
| eval usage_pct=(current/maximum)*100
| where usage_pct > 80
```

## Visualization

Gauge, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
