---
id: "5.8.7"
title: "Network Configuration Drift Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.7 · Network Configuration Drift Detection

## Description

Configuration drift from golden standards introduces vulnerabilities and operational inconsistencies. Detecting drift maintains compliance.

## Value

Configuration drift from golden standards introduces vulnerabilities and operational inconsistencies. Detecting drift maintains compliance.

## Implementation

Schedule config pulls via Oxidized/RANCID. Diff against golden templates. Ingest diff results into Splunk. Alert on unauthorized changes (outside change windows).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: RANCID/Oxidized, custom diff scripts, DNA Center.
• Ensure the following data sources are available: `sourcetype=config:diff`, `sourcetype=cisco:dnac`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Schedule config pulls via Oxidized/RANCID. Diff against golden templates. Ingest diff results into Splunk. Alert on unauthorized changes (outside change windows).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="config:diff"
| rex "device=(?<device>\S+).*?lines_changed=(?<changes>\d+)"
| where changes > 0
| stats sum(changes) as total_changes, count as change_events by device
| sort -total_changes
```

Understanding this SPL

**Network Configuration Drift Detection** — Configuration drift from golden standards introduces vulnerabilities and operational inconsistencies. Detecting drift maintains compliance.

Documented **Data sources**: `sourcetype=config:diff`, `sourcetype=cisco:dnac`. **App/TA** (typical add-on context): RANCID/Oxidized, custom diff scripts, DNA Center. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: config:diff. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="config:diff". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where changes > 0` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by device** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, changes, last modified), Timeline (change events), Single value (devices with drift).

## SPL

```spl
index=network sourcetype="config:diff"
| rex "device=(?<device>\S+).*?lines_changed=(?<changes>\d+)"
| where changes > 0
| stats sum(changes) as total_changes, count as change_events by device
| sort -total_changes
```

## Visualization

Table (device, changes, last modified), Timeline (change events), Single value (devices with drift).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
