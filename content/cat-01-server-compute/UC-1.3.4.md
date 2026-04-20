---
id: "1.3.4"
title: "Software Update Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.3.4 · Software Update Compliance

## Description

Unpatched macOS endpoints are vulnerable. Tracking update levels across the fleet supports vulnerability management.

## Value

Unpatched macOS endpoints are vulnerable. Tracking update levels across the fleet supports vulnerability management.

## Implementation

Scripted input for `sw_vers` (weekly) and `softwareupdate -l` (daily). Track OS versions and pending updates. Alert when critical security updates are pending >7 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk UF, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (`softwareupdate -l`, `sw_vers`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input for `sw_vers` (weekly) and `softwareupdate -l` (daily). Track OS versions and pending updates. Alert when critical security updates are pending >7 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_sw_vers host=*
| stats latest(ProductVersion) as os_version by host
| eval is_current = if(os_version >= "14.3", "Yes", "No")
| stats count by is_current
```

Understanding this SPL

**Software Update Compliance** — Unpatched macOS endpoints are vulnerable. Tracking update levels across the fleet supports vulnerability management.

Documented **Data sources**: Custom scripted input (`softwareupdate -l`, `sw_vers`). **App/TA** (typical add-on context): Splunk UF, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: macos_sw_vers. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=macos_sw_vers. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **is_current** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by is_current** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, OS version, pending updates), Pie chart (version distribution).

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
index=os sourcetype=macos_sw_vers host=*
| stats latest(ProductVersion) as os_version by host
| eval is_current = if(os_version >= "14.3", "Yes", "No")
| stats count by is_current
```

## Visualization

Table (host, OS version, pending updates), Pie chart (version distribution).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
