<!-- AUTO-GENERATED from UC-8.8.1.json — DO NOT EDIT -->

---
id: "8.8.1"
title: "RPA Bot Execution Health and Queue Depth Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.8.1 · RPA Bot Execution Health and Queue Depth Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the little tireless assistants that moving paperwork between systems. When they stumble or lines back up behind them grow, we shout early so chores do not tumble back onto people unexpectedly.*

---

## Description

Hourly aggregation of robot run counts, derived failure rates from normalized status text, average duration, and peak queue depth per bot and process so unhealthy automations stand out before business SLAs miss.

## Value

Operations managers keep invoice, claims, and onboarding robots from silently piling up exceptions that force expensive manual clearing teams, which protects customer promises and frees people for work that still needs a human touch.

## Implementation

Land Orchestrator job logs and Automation Anywhere Bot Insight JSON on `index=rpa`. Map vendor-specific success and fault codes into the coalesced `status_norm` field at index time for consistency. Start alerts on failure_rate and queue_depth, then add seasonality baselines per process_name for finance month-end peaks.

## Detailed Implementation

### Prerequisites
- **Orchestrator / Control Room OAuth app** registered with **Robot / Jobs read** scopes (least privilege—not full admin secrets on forwarder).
- **Outbound HTTPS:** heavy forwarders can reach SaaS orchestrator endpoints; proxy exceptions documented (**PAC** file exclusions).
- **Clock sync:** Splunk indexer & Orchestrator timestamps within **≤60s skew** (`ntpstat`).
- **Field normalisation workbook** aligning `RobotName`, `machine`, `Username`, `ReleaseName` synonyms between vendors (`bot_name`).
- **Licence sanity:** OData high-frequency polling counted against UiPath Automation Cloud quotas—coordinate with Automation COE monthly.

### Step 1 — Configure data collection
**UiPath modular input pseudocode workflow:** (1) POST `/identity_/connect/token` with `grant_type=client_credentials`. (2) GET `/odata/Jobs?$filter=…` paging `Prefer: odata.maxpagesize=1000`. (3) Optionally GET `/odata/QueueItems?$filter=Status eq \'Pending\'` per queue id to compute backlog. (4) Splunk Modular Input writes JSON batches with **`sourcetype=uipath:orchestrator`**, **`index=rpa`**.

`inputs.conf` example:
```ini
[uipath_modinput://Production]
orchestratorUrl = https://cloud.uipath.com/<org>/<tenant>/orchestrator_
clientSecretJson = etc/apps/secrets/oauth_uipath.json
interval = 300
startByJobServerTime = true
deduplication_field = UniqueKeyFromPayload
```

```ini
[uipath:orchestrator]
SHOULD_LINEMERGE=false
EVAL-duration_seconds = coalesce(JobDuration_secs, VendorReportedDurationSecs)
```
Tune `EVAL-duration_seconds` to your OData field names (`Job.Duration` flattened). Prefer computing duration in modular input Python for clarity.

**Automation Anywhere path:** Splunk DB Connect input `Database Input` querying **Bot Insight hourly roll-up** projection with SQL where `ExecutedTime BETWEEN ? AND ?`; write raw rows with sourcetype `automation_anywhere:bot_insight`. Ensure DB account read-only scoped to analytic views—not production bot credential vault tables.

**Verification SPL:** `index=rpa earliest=-24h sourcetype IN ("uipath:orchestrator","automation_anywhere:bot_insight") | timechart span=1h count by sourcetype` — continuous lines; spikes at maintenance should align with calendars.

### Step 2 — Create the search and alert
```spl
index=rpa sourcetype IN ("uipath:orchestrator","automation_anywhere:bot_insight")
| eval status_norm=lower(coalesce(State, bot_status, status, ""))
| eval failure=if(status_norm IN ("faulted","failed","error","stopped"),1,0)
| bin _time span=1h
| stats count as executions sum(failure) as failures avg(duration_seconds) as avg_duration max(queue_depth) as max_queue by bot_name process_name _time
| eval failure_rate=round(if(executions>0,(failures/executions)*100,0),1)
| where failure_rate > 10 OR max_queue > 50
| sort - failure_rate
```

#### Understanding this SPL
- **Sourcetype union** merges disparate vendor payloads into unified metrics fields.
- **`status_norm`** coalesces case variants avoiding double logic.
- **`failure`** boolean maps multiple terminal failure keywords—extend carefully when vendor adds synonyms.
- **`bin _time span=1h`** aligns reporting to SLA hour boundaries used by robotics COE dashboards.
- **`stats`** simultaneously yields throughput, faults, durations, backlog peaks—single pass efficiency.
- **`failure_rate`** expresses reliability as percent failed executions for leadership communication.
- **`where` thresholds** deliberately conservative starter values—tune via histogram of historical baselines (`| eventstats perc95(queue_depth)` optional overlay).

Schedule as Alert: cron **`*/15 * * * *`**; timeframe ** `-2h@m`→`now`**, trigger **results>0**, suppress **same `bot_name+process_name` 2h**. Secondary daily summary report for trends.

### Step 3 — Validate
(a) Pick row; reconcile `executions` against Orchestrator **Jobs filtered last 2 hours** screenshot.
(b) Validate **`duration_seconds` units** comparing three random jobs timeline UI.
(c) Inspect **fault reason text** `_raw` to ensure not environmental false positive flagged as Faulted.
(d) Compare **queue depth** with live queues during alert.
(e) Replay hour where **Orchestrator API outage** suspected—dedupe ingestion gaps flagged.
(f) SLA sign-off documenting threshold adoption from pilot week PDF.

### Step 4 — Operationalize
**Dashboard:** Panels per `visualization`. Add textual **queue owner** lookup column via `lookup rpa_queue_owner process_name`.
**Alerting:** PagerDuty **RPA-Bots** service; low priority for **non-prod** via routing key filter.
**Runbook:** 1) Open Orchestrator job details. 2) Check machine connectivity + credential asset. 3) Replay failed job with safe dataset. 4) Raise vendor ticket if systemic. 5) Update threshold macro after sustained architecture change.

### Step 5 — Troubleshooting
- **`executions drop to zero`** — Modular input crashed; grep `splunkd.log` for HTTP 429/503 — implement backoff & token refresh.
- **Inflated `failure_rate`** due to preemptive **stopped** cancellations during deployments — add exclusion filter keyed on **`Release.Version` rollout window** lookup.
- **`queue_depth` null** — missing secondary ingest; optionally compute analytic field `queue_depth_jobs_pending` fallback.
- **Duplicated `_raw` events double counts** — fix dedupe key in modular input ACK.
- **Clock skew artefacts** causing hour bucket splits — align NTP urgent.
- **DB Connect lag** delaying AA insight — widen alert window temporarily or tighten JDBC poll interval SLA with DBA.

## SPL

```spl
index=rpa sourcetype IN ("uipath:orchestrator","automation_anywhere:bot_insight")
| eval status_norm=lower(coalesce(State, bot_status, status, ""))
| eval failure=if(status_norm IN ("faulted","failed","error","stopped"),1,0)
| bin _time span=1h
| stats count as executions sum(failure) as failures avg(duration_seconds) as avg_duration max(queue_depth) as max_queue by bot_name process_name _time
| eval failure_rate=round(if(executions>0,(failures/executions)*100,0),1)
| where failure_rate > 10 OR max_queue > 50
| sort - failure_rate
```

## Visualization

**Layout:**

- (1) **Panel A — “Hourly failure vs queue overlay”** — Dual-axis chart: `failure_rate` line (%) and **`max_queue` columns** by `_time`; split by **`process_name`**.
- (2) **Panel B — “Worst offender table”** — Table: `bot_name`, `process_name`, `executions`, `failures`, `failure_rate`, `avg_duration`, `max_queue`; drill-through to Splunk Investigation Workbench dashboard.
- (3) **Panel C — “Queue depth gauges”** — Radial gauges per critical queue SLA (finance, HC claims).
- (4) **Panel D — “Duration drift”** — Box plot (`avg_duration`, `perc95(duration_seconds)` per process) detecting slowdown prior to faults.

## Known False Positives

- **Platform upgrades / maintenance windows** — Jobs flip through **Stopping** states and queues pause. *Mitigation:* join `MaintenanceCalendar` KV lookup keyed on `tenant`/`FolderId`, suppress alerting when `planned_change=1`.
- **Credential rotation blips** — First run after vault rotation fails auth once; queue depth dips then recovers seconds later. *Mitigation:* throttle identical `RobotName + ProcessName` failures to one alert per hour unless consecutive ≥3 faults.
- **Staging / Regression tenants** — Dev queues intentionally fault to test exception flows. *Mitigation:* segregate **`index=rpa_stage`** OR filter hosts containing `-dev-`.
- **Large batch bursts (month-end invoices)** — `queue_depth` legitimately climbs above static threshold albeit healthy throughput. *Mitigation:* adaptive threshold `max_queue > percentile(p90_last_28d)` using `historicalscheduled` macros.
- **Vendor API pagination gaps** — Missed OData page inflates inferred failure counts. *Mitigation:* reconcile hourly counts versus Orchestrator web UI KPIs nightly; pager if ingestion delta >5%.
- **Mixed-case status strings introduced** — already mitigated via `lower()` but new vendor synonyms like **`Suspended`** erroneously flagged. *Mitigation:* maintain `trusted_status.csv` whitelist + expand `failure` eval carefully with change control.

## References

- [Splunk Lantern — Use Case Explorer: IT Modernization](https://lantern.splunk.com/Splunk_Platform/UCE)
- [UiPath Orchestrator OData API Reference (Jobs / QueueItems)](https://docs.uipath.com/automation-cloud/)
- [Automation Anywhere Documentation — Bot Insight Analytics](https://docs.automationanywhere.com/bundle/enterprise-v2019/)
- [Splunk Documentation — Modular inputs overview](https://docs.splunk.com/Documentation/Splunk/latest/Admin/)
