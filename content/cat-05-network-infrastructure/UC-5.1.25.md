<!-- AUTO-GENERATED from UC-5.1.25.json — DO NOT EDIT -->

---
id: "5.1.25"
title: "Network Configuration Drift Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.25 · Network Configuration Drift Detection

## Description

Running config differs from baseline/golden config.

## Value

Running config differs from baseline/golden config.

## Implementation

Run diff (e.g., `diff running golden`) via Oxidized hooks or custom script. Ingest diff output or Git commit metadata. Store golden configs in Git; compare after each backup. Alert on any non-whitelisted drift. Use `git diff` or `rancid -d` output as sourcetype.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (diff output from RANCID/Oxidized vs golden), `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: Config diff output, Git commit logs from network config repo.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run diff (e.g., `diff running golden`) via Oxidized hooks or custom script. Ingest diff output or Git commit metadata. Store golden configs in Git; compare after each backup. Alert on any non-whitelisted drift. Use `git diff` or `rancid -d` output as sourcetype.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=config_drift OR sourcetype=git:commit
| search "diff" OR "drift" OR "changed" OR "modified"
| rex "device[=:]\s*(?<device>\S+)" | rex "lines?\s*(?<lines_changed>\d+)"
| stats count as drift_events, values(diff_summary) as changes by device, host
| where drift_events > 0
| table device host drift_events changes
```

Understanding this SPL

**Network Configuration Drift Detection** — Running config differs from baseline/golden config.

Documented **Data sources**: Config diff output, Git commit logs from network config repo. **App/TA** (typical add-on context): Custom scripted input (diff output from RANCID/Oxidized vs golden), `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: config_drift, git:commit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=config_drift. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by device, host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where drift_events > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Network Configuration Drift Detection**): table device host drift_events changes


Step 3 — Validate
Pull the latest Oxidized, RANCID, or Git-backed export for one device in the result and run a manual `diff` against your golden. Confirm the diff hash or line count in Splunk’s event matches the file you opened.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, drift count, summary), Timeline (drift events), Single value (devices with drift).

## SPL

```spl
index=network sourcetype=config_drift OR sourcetype=git:commit
| search "diff" OR "drift" OR "changed" OR "modified"
| rex "device[=:]\s*(?<device>\S+)" | rex "lines?\s*(?<lines_changed>\d+)"
| stats count as drift_events, values(diff_summary) as changes by device, host
| where drift_events > 0
| table device host drift_events changes
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.command All_Changes.action span=1h
| sort -count
```

## Visualization

Table (device, drift count, summary), Timeline (drift events), Single value (devices with drift).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
