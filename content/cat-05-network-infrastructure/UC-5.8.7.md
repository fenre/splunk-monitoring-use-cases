<!-- AUTO-GENERATED from UC-5.8.7.json — DO NOT EDIT -->

---
id: "5.8.7"
title: "Network Configuration Drift Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.7 · Network Configuration Drift Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Configuration &middot; **Wave:** Crawl

*We spot when a device's settings drift from what we expect, so surprise changes do not sit there quietly until they cause an outage.*

---

## Description

Detects configuration drift by analysing diffs between device running-configs and golden templates, identifying devices with the most configuration changes for investigation.

## Value

Undetected configuration drift introduces security vulnerabilities, compliance violations, and operational inconsistencies. Proactively surfacing drift ensures changes are authorised and aligned with organisational standards.

## Implementation

Deploy RANCID or Oxidized to periodically pull running-configs from network devices. Configure diff output to be ingested into Splunk via file monitor or HEC. The diff results include device name and line change counts. Alert when changes occur outside approved change windows.

## Detailed Implementation

### Prerequisites
- RANCID or Oxidized installed and configured to pull running-configs from your network devices on a schedule (typically every 30–60 minutes).
- A diff mechanism that compares each pulled config against a golden template and produces structured output with at least `device` and `lines_changed` fields.
- Splunk forwarder or HEC endpoint configured to ingest the diff results as `sourcetype=config:diff` into `index=network`.

### Step 1 — Configure data collection
- **Oxidized setup:** Configure device groups and credentials in `router.db`; set the `output` plugin to write diffs to a watched directory or push via HEC.
- **RANCID setup:** Configure `router.db` entries and `rancid-run` cron jobs; monitor the RCS/Git diff output directory with a Splunk file monitor input.
- **Diff format:** Each diff event should include at minimum `device=<hostname>` and `lines_changed=<count>`. Additional fields like `section`, `timestamp`, and `change_type` enrich the analysis.
- **Volume:** Typically one event per device per config pull. Expect ~100 events/day for 100 devices polled every 30 minutes (most pulls show zero changes).

### Step 2 — Create the search and alert
```spl
index=network sourcetype="config:diff"
| rex "device=(?<device>\S+).*?lines_changed=(?<changes>\d+)"
| where changes > 0
| stats sum(changes) as total_changes, count as change_events by device
| sort -total_changes
```

#### Understanding this SPL:
- **`rex`**: Extracts the device hostname and line change count from the diff output format. Adjust the regex if your diff tool uses a different output structure.
- **`where changes > 0`**: Filters out config pulls where nothing changed, keeping only actual drift events.
- **`stats sum(changes)`**: Aggregates total line changes per device. Devices with high `total_changes` may have undergone significant unauthorised modification.
- **Tuning:** Correlate with a change management lookup (`| lookup change_windows device OUTPUT approved`) to filter out authorised changes.

### Step 3 — Validate
- **Cross-reference:** pick two devices that show config changes in Splunk and manually verify the diff against the golden template stored in your Oxidized/RANCID repository.
- Run `| timechart count by device` over 7 days to verify the diff ingestion cadence matches the expected pull schedule.
- Confirm zero-change pulls are being ingested (run without `where changes > 0`) to distinguish between "no drift" and "no data."

### Step 4 — Operationalize
- **Dashboard:** Table of top drifted devices, timeline of change events with change-window overlay, single-value tile of total devices with active drift.
- **Alert:** Trigger on any changes outside approved change windows or on devices in critical infrastructure groups.
- **Runbook:** Link to the Oxidized/RANCID diff viewer to inspect the specific configuration lines that changed.

### Step 5 — Troubleshooting
- **No `config:diff` events:** if data is not arriving, check that the Splunk file monitor input is pointed at the correct diff output directory, verify Oxidized/RANCID is running (`systemctl status oxidized`), and confirm new diff files appear in the output directory.
- **All events show zero changes:** golden template may be identical to running-configs (expected in a well-managed environment), or the diff mechanism is not correctly comparing against the template.
- **`device` field not extracted:** the `rex` pattern assumes a specific diff output format. Run `| head 5` on raw events to see the actual format and adjust the regex accordingly.
- **Connection refused or timeout from network devices:** verify device reachability from the RANCID/Oxidized host, check SSH/SNMP credentials, and confirm devices have not been access-listed to block the polling host.


## SPL

```spl
index=network sourcetype="config:diff"
| rex "device=(?<device>\S+).*?lines_changed=(?<changes>\d+)"
| where changes > 0
| stats sum(changes) as total_changes, count as change_events by device
| sort -total_changes
```

## Visualization

Table (device, total_changes, change_events), Timeline of change events over 30 days, Single value (devices with drift count).

## Known False Positives

Authorized template pushes, golden-config refreshes, and RANCID noise can all move diff counts; require change-ticket match before treating as incident.

## References

- [Oxidized — Network Device Configuration Backup](https://github.com/ytti/oxidized)
- [Splunk Lantern — Configuration Management](https://lantern.splunk.com/)
