<!-- AUTO-GENERATED from UC-5.9.49.json — DO NOT EDIT -->

---
id: "5.9.49"
title: "ThousandEyes Data Collection Health Monitoring"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.49 · ThousandEyes Data Collection Health Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch the watcher — making sure the system that monitors our network is actually running, because if the monitoring system breaks, nobody notices until something goes very wrong and we didn't get a warning.*

---

## Description

Monitors the health of the data pipeline from ThousandEyes to Splunk — detecting data gaps, HEC failures, OAuth token expiration, and integration outages. This is the "monitoring for the monitoring" UC that ensures all other ThousandEyes UCs (5.9.1–5.9.48) have data to work with.

## Value

Every ThousandEyes UC depends on data flowing from ThousandEyes to Splunk. If the OTel stream stops, the HEC token expires, or the OAuth authentication fails, ALL ThousandEyes UCs silently stop working — no alerts fire, no dashboards update, and the team assumes "no news is good news" when in reality the monitoring system itself is broken. This UC detects that failure mode immediately. It's the foundation that all other ThousandEyes monitoring depends on.

## Implementation

Monitor event volume in the ThousandEyes indexes and HEC health in _internal. Alert when volume drops below expected baseline.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, data inputs enabled).
- **Understand the ThousandEyes → Splunk data pipeline architecture.** The pipeline has multiple failure points, each requiring different monitoring:
  1. **ThousandEyes SaaS** generates test results. If ThousandEyes itself is down, no data is produced.
  2. **HEC push (metrics & alerts).** ThousandEyes pushes OTel metrics and alert data to Splunk's HTTP Event Collector. Failure points: HEC token expired/invalid, HEC endpoint unreachable, SSL certificate issues, Splunk indexer queue full.
  3. **API polling (events & path viz).** The `ta_cisco_thousandeyes` polls ThousandEyes APIs for event data, path visualization, and activity logs. Failure points: OAuth token expired, API rate limited, Splunk heavy forwarder down, network connectivity.
  4. **Splunk indexing.** Splunk must parse and index the incoming data. Failure points: index not created, parsing errors, license exceeded.
- **Baseline event volume documented.** Calculate expected volume:
  - Metrics: Each test produces 1 metric event per agent per test interval. Example: 20 tests × 5 agents × 12 rounds/hour = 1,200 metric events/hour.
  - Alerts: Volume depends on alert frequency. Baseline during normal operations (low alert volume).
  - Events: Activity log events are sporadic. Path viz events depend on the number of tests with path viz enabled.
  Document your expected volume so you can set appropriate thresholds.
- **This is a meta-monitoring UC.** It monitors the monitoring system itself. If this UC's alerts fail, you have NO visibility into data pipeline failures. Therefore, this alert should be as simple and robust as possible — avoid complex SPL that could itself break.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`, `thousandeyes_events`, `thousandeyes_alerts`, `thousandeyes_pathvis`, AND `_internal` (for HEC and app log monitoring).

### Step 1 — Configure data collection
No additional data input is needed. This UC monitors the existing data pipeline using data already flowing into Splunk and internal Splunk logs.

Verify that ALL four ThousandEyes indexes are receiving data:
```spl
(index=thousandeyes_metrics OR index=thousandeyes_events OR index=thousandeyes_alerts OR index=thousandeyes_pathvis) earliest=-1h
| stats count latest(_time) as last_event by index, sourcetype
| eval minutes_ago=round((now() - last_event) / 60, 0)
| table index, sourcetype, count, minutes_ago
| sort index
```
Expected: Each index/sourcetype should show recent data. If `minutes_ago > 30` for any row, that data source may be broken.

**Understanding the four data streams:**
- `thousandeyes_metrics` (`cisco:thousandeyes:metric`) — HEC-pushed. Highest volume. Continuous flow. If this stops, HEC is broken.
- `thousandeyes_alerts` (`cisco:thousandeyes:alerts`) — HEC-pushed. Variable volume (depends on alert activity). May have legitimate gaps during healthy periods.
- `thousandeyes_events` (`cisco:thousandeyes:event`) — API-polled. Lower volume. Depends on `ta_cisco_thousandeyes` Event input.
- `thousandeyes_pathvis` (`cisco:thousandeyes:path-vis`) — API-polled. Depends on path viz input being enabled.

### Step 2 — Create the search and alert
**Data freshness monitor (primary alert — simple and robust):**
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" earliest=-30m
| stats count as event_count latest(_time) as last_event
| eval minutes_since_last=round((now() - last_event) / 60, 0)
| where event_count < 10 OR minutes_since_last > 15
```

**Understanding this SPL**

This is intentionally simple. It checks the most critical data source (metrics) for two conditions:
- `event_count < 10` — abnormally low volume in the last 30 minutes. Even a small ThousandEyes deployment should produce > 10 metric events in 30 minutes.
- `minutes_since_last > 15` — no data received in the last 15 minutes. This catches complete pipeline failures.

Why metrics and not alerts/events? Metrics flow via HEC push (continuous) and are the highest-volume stream. If metrics stop, the core pipeline is broken. Alert and event streams have legitimate quiet periods.

**Per-index data freshness (comprehensive view):**
```spl
(index=thousandeyes_metrics OR index=thousandeyes_events OR index=thousandeyes_alerts OR index=thousandeyes_pathvis) earliest=-2h
| stats count latest(_time) as last_event earliest(_time) as first_event by index, sourcetype
| eval minutes_ago=round((now() - last_event) / 60, 0)
| eval events_per_hour=round(count / ((last_event - first_event) / 3600), 0)
| table index, sourcetype, count, events_per_hour, minutes_ago
| sort index
```
This shows data health across all four streams. Use for dashboard, not alerting (alert/event streams may have legitimate gaps).

**Data volume trending (detect gradual degradation):**
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" earliest=-7d
| timechart span=1h count as hourly_events
| eval hour_of_day=strftime(_time, "%H")
```
Look for: (a) complete gaps (count=0), (b) sudden volume drops (< 50% of normal), (c) gradual decline over days (possibly losing agents or tests).

**HEC health check (monitors the push pipeline):**
```spl
index=_internal sourcetype=splunkd component=HttpInputDataHandler earliest=-1h
| stats count by log_level
| where log_level="ERROR" OR log_level="WARN"
```
HEC errors indicate: token issues, SSL problems, queue full, parsing errors. ANY HEC errors during normal operation warrant investigation.

**HEC error detail:**
```spl
index=_internal sourcetype=splunkd component=HttpInputDataHandler log_level=ERROR earliest=-24h
| stats count by message
| sort -count
```
Common HEC error messages:
- "Token disabled" — the HEC token used by ThousandEyes has been disabled.
- "Invalid token" — token was deleted or changed.
- "Index not found" — the target index doesn't exist.
- "Queue full" — Splunk indexing pipeline is backed up.

**OAuth / app health check (monitors the polling pipeline):**
```spl
index=_internal source="*ta_cisco_thousandeyes*" earliest=-1h log_level=ERROR
| stats count by message
| sort -count
```
Common app errors:
- "Authentication failed" or "401" — OAuth token expired. Re-authenticate.
- "429 Too Many Requests" — ThousandEyes API rate limit hit. Reduce polling frequency.
- "Connection refused" or "timeout" — Network connectivity issue between Splunk and ThousandEyes API.

**Per-test data coverage (are all tests reporting?):**
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" earliest=-1h
| stats count dc(thousandeyes.source.agent.name) as reporting_agents latest(_time) as last_event by thousandeyes.test.name
| eval minutes_ago=round((now() - last_event) / 60, 0)
| where minutes_ago > 15 OR reporting_agents < 1
| sort -minutes_ago
```
This identifies individual tests that have stopped reporting, even if overall volume looks healthy. A single failed test creates a monitoring gap for that specific application/path.

**Scheduling (the most critical alert in your ThousandEyes deployment):**
- Data freshness alert: cron `*/10 * * * *`, time range `-30m to now`. This runs every 10 minutes. If data stops flowing, you'll know within 10 minutes.
- HEC health check: cron `*/30 * * * *`, time range `-35m to now`. HEC errors need attention but aren't as urgent.
- OAuth/app health: cron `0 * * * *` (hourly), time range `-65m to now`. App errors tend to be persistent once they start.

### Step 3 — Validate
(a) **Establish baseline event volume.** Run over 24 hours:
```spl
index=thousandeyes_metrics | timechart span=1h count
```
Note the minimum, average, and maximum hourly event count. Set your alert threshold below the minimum. If the minimum hourly count is 500, set the threshold at 100 (allowing for some normal variation).

(b) **Test the data freshness alert.** Temporarily disable the ThousandEyes HEC integration: in ThousandEyes → **Integrations → Streaming → Splunk** → disable the stream. Wait 15 minutes. Verify the data freshness alert fires. Re-enable the stream immediately after testing.

(c) **Verify HEC monitoring works.** Check that `index=_internal component=HttpInputDataHandler` returns results. If it returns 0, you may not have access to the `_internal` index.

(d) **Verify app log monitoring works.** Check that `index=_internal source="*ta_cisco_thousandeyes*"` returns results. If 0, the app may log to a different location. Try `source="*thousandeyes*"` instead.

(e) **Alert routing verification.** Confirm the data freshness alert routes to the correct team (Splunk admin AND ThousandEyes admin). Both teams may need to act depending on the failure point.

### Step 4 — Operationalize
**Dashboard** ("ThousandEyes Integration Health" — add to an existing admin monitoring dashboard):
- Row 1 — Pipeline status: single-value panels showing time since last event per index (green < 10 min, yellow 10–30 min, red > 30 min). Four panels: Metrics, Alerts, Events, Path Viz.
- Row 2 — Data volume timechart: hourly event count over 7 days for each index. Shows patterns and gaps.
- Row 3 — HEC and app errors: table of recent errors from `_internal`. Zero rows = healthy.
- Row 4 — Per-test coverage: table of tests that haven't reported in > 15 minutes. Zero rows = all tests reporting.

**Alerting (this is the most important alert in the ThousandEyes monitoring stack):**
- Data freshness: `minutes_since_last > 15` for `thousandeyes_metrics` → HIGH-urgency. Page on-call Splunk admin AND ThousandEyes admin. This means ALL ThousandEyes monitoring is blind.
- HEC errors detected → medium-urgency notification to Splunk admin. HEC issues will lead to data loss if not resolved.
- OAuth errors detected → medium-urgency notification to ThousandEyes admin. API polling will stop if not re-authenticated.
- Individual test stopped reporting → low-urgency notification. A monitoring gap exists but other tests continue.

**Runbook** (owner: Splunk admin AND ThousandEyes admin — both may need to act):
1. **Data gap — no metric events in > 15 minutes.** Investigate in order:
   (a) **HEC health:** Check `index=_internal component=HttpInputDataHandler log_level=ERROR`. If errors → HEC issue. Check HEC token status (**Settings → Data Inputs → HTTP Event Collector**). Verify token is enabled.
   (b) **ThousandEyes stream health:** Login to ThousandEyes → **Integrations → Streaming → Splunk**. Is the stream active? Are there delivery errors? The ThousandEyes UI shows delivery status.
   (c) **Network connectivity:** Can Splunk receive inbound HTTPS on port 8088 (HEC)? Check firewalls, load balancers, and SSL certificates.
   (d) **Splunk indexing:** Check `index=_internal source=*metrics.log group=queue name=indexqueue` for queue backup. If the indexing queue is full, data may be dropped.
2. **No event/path viz data (but metrics flowing).** The API polling pipeline is broken separately from HEC.
   (a) Check OAuth token: re-run the OAuth Device Code flow if expired.
   (b) Check Event/Path Viz inputs: **Settings → Data Inputs → ta_cisco_thousandeyes** — are all inputs enabled?
   (c) Check API rate limits: `index=_internal source="*ta_cisco_thousandeyes*" "429"`. If rate-limited, reduce polling interval.
3. **HEC errors but data still flowing.** Partial failures. Some events may be dropped. Fix the root cause (usually SSL cert or token issue) before it becomes a complete failure.
4. **OAuth re-authentication required.** The OAuth token has a limited lifetime. When it expires, API-polled data stops. Follow the re-authentication process: App Setup → Authentication → complete the Device Code flow.

### Step 5 — Troubleshooting

- **Chronic low volume (below expected baseline)** — Calculate expected: tests × agents × (60 / interval_minutes) = events/hour. If actual volume is consistently lower, some tests or agents may be disabled, failed, or producing errors that ThousandEyes doesn't send to Splunk.

- **Volume drops at specific times daily** — Some tests may have scheduling intervals that create predictable low-volume windows. Also check if ThousandEyes maintenance windows affect data production.

- **HEC token shows as enabled but no data flows** — Check that the HEC token's `indexes` setting includes `thousandeyes_metrics` and `thousandeyes_alerts`. If the token is restricted to specific indexes and the ThousandEyes stream targets a different index, data is silently dropped.

- **`_internal` queries return 0 results** — Your Splunk role may not have access to the `_internal` index. Request `srchIndexesAllowed` to include `_internal`, or ask a Splunk admin to set up the monitoring searches under an admin account.

- **Data flowing but with timestamp issues (future or past timestamps)** — Check time synchronization between ThousandEyes SaaS (UTC) and your Splunk instance. Large clock skew causes events to be indexed with incorrect timestamps, making them appear missing in time-bounded searches.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for general app troubleshooting.

## SPL

```spl
`stream_index` earliest=-2h
| timechart span=5m count as event_count
| where event_count < 10
```

## Visualization

(1) Timechart: event volume per 5 minutes (flat line = data gap). (2) Single value: events received in last hour (green > threshold, red < threshold). (3) Table: last event time per index/sourcetype. (4) HEC health from _internal logs.

## Known False Positives

**Low test volume environments.** If you have very few ThousandEyes tests (< 5), event volume may naturally be low. Adjust the threshold to match your expected data volume.

**Off-hours data reduction.** If tests are scheduled only during business hours, data volume drops at night. Account for this in your baseline.

**Splunk maintenance.** Splunk restarts or indexer maintenance may cause brief data gaps.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [Splunk HEC troubleshooting](https://docs.splunk.com/Documentation/Splunk/latest/Data/TroubleshootHTTPEventCollector)
