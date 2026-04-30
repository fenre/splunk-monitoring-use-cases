<!-- AUTO-GENERATED from UC-1.1.107.json — DO NOT EDIT -->

---
id: "1.1.107"
title: "Hardware Clock Drift Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.107 · Hardware Clock Drift Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Configuration

*We compare the Linux clock to real time so logins, certificates, and cross-system correlation stay trustworthy.*

---

## Description

Hardware clock drift affects system time accuracy impacting application consistency and audit trails.

## Value

Hardware clock drift affects system time accuracy impacting application consistency and audit trails.

## Implementation

Use Splunk_TA_nix time input to track system time vs. reference. Monitor offset from NTP server. Alert when offset exceeds 100ms. Recommend NTP service investigation or hardware RTC replacement.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk_TA_nix`.
- Ensure the following data sources are available: `sourcetype=time`.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Use Splunk_TA_nix time input to track system time vs. reference. Monitor offset from NTP server. Alert when offset exceeds 100ms. Recommend NTP service investigation or hardware RTC replacement.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=time host=*
| stats latest(time_offset_ms) as offset by host
| where abs(offset) > 100
```

#### Understanding this SPL

**Hardware Clock Drift Detection** — Hardware clock drift affects system time accuracy impacting application consistency and audit trails.

Documented **Data sources**: `sourcetype=time`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: time. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=os, sourcetype=time. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
- Filters the current rows with `where abs(offset) > 100` — typically the threshold or rule expression for this monitoring goal.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Timechart

## SPL

```spl
index=os sourcetype=time host=*
| stats latest(time_offset_ms) as offset by host
| where abs(offset) > 100
```

## Visualization

Gauge, Timechart

## Known False Positives

VM clock sync through the hypervisor, leap seconds, or a one-time `chronyc makestep` can move `time_offset_ms` sharply without ongoing drift. Containers sharing the host clock can duplicate the same offset—dedupe by asset if needed.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
