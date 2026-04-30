<!-- AUTO-GENERATED from UC-1.1.29.json — DO NOT EDIT -->

---
id: "1.1.29"
title: "Context Switch Rate Anomaly Detection (Linux)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.29 · Context Switch Rate Anomaly Detection (Linux)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Anomaly

*Excessive context switching reduces CPU cache effectiveness and indicates scheduler overload or contention — so you find out before users do when something is slowing down or breaking.*

---

## Description

Excessive context switching reduces CPU cache effectiveness and indicates scheduler overload or contention.

## Value

Excessive context switching reduces CPU cache effectiveness and indicates scheduler overload or contention.

## Implementation

Monitor vmstat context switch counter (cs field). Use baseline and anomaly detection to alert on sustained context switch rates that exceed 2 standard deviations above normal, indicating scheduler pressure.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk_TA_nix`.
- Ensure the following data sources are available: `sourcetype=vmstat`.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Monitor vmstat context switch counter (cs field). Use baseline and anomaly detection to alert on sustained context switch rates that exceed 2 standard deviations above normal, indicating scheduler pressure.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| bin _time span=5m
| stats avg(cs) as avg_ctx_switch by host, _time
| streamstats window=100 avg(avg_ctx_switch) as baseline stdev(avg_ctx_switch) as stddev by host
| eval upper_bound=baseline+(2*stddev)
| where avg_ctx_switch > upper_bound
```

#### Understanding this SPL

**Context Switch Rate Anomaly Detection (Linux)** — Excessive context switching reduces CPU cache effectiveness and indicates scheduler overload or contention.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Discretizes time or numeric ranges with `bin`/`bucket`.
- `stats` rolls up events into metrics; results are split **by host, _time** so each row reflects one combination of those dimensions.
- `streamstats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
- `eval` defines or adjusts **upper_bound** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where avg_ctx_switch > upper_bound` — typically the threshold or rule expression for this monitoring goal.

### Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Anomaly Detector

## SPL

```spl
index=os sourcetype=vmstat host=*
| bin _time span=5m
| stats avg(cs) as avg_ctx_switch by host, _time
| streamstats window=100 avg(avg_ctx_switch) as baseline stdev(avg_ctx_switch) as stddev by host
| eval upper_bound=baseline+(2*stddev)
| where avg_ctx_switch > upper_bound
```

## Visualization

Timechart, Anomaly Detector

## Known False Positives

Deploys, tracing, and load tests spike context switches. Require enough samples in the stats window; tune by role.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
