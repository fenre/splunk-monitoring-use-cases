<!-- AUTO-GENERATED from UC-5.13.74.json — DO NOT EDIT -->

---
id: "5.13.74"
title: "Catalyst Center Data Collection Health (Meta)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.74 · Catalyst Center Data Collection Health (Meta)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch the watchers — making sure that every data feed from the network management system into Splunk is actually working. If one of the connections breaks silently, we catch it within hours so your monitoring doesn't have blind spots that nobody notices until something goes wrong.*

---

## Description

Monitors the health of the Catalyst Center data collection pipeline by checking event volume and freshness for each sourcetype, detecting collection failures or gaps.

## Value

All other Catalyst Center use cases depend on data flowing reliably. This meta-monitoring UC ensures the pipeline is healthy and catches collection failures early.

## Implementation

This UC uses existing TA inputs — no additional configuration needed beyond the standard TA setup. It monitors all `cisco:dnac:*` sourcetypes to verify:

1. **Event volume:** Each sourcetype should have events within the last 2 hours (based on TA polling intervals)
2. **Expected sourcetypes:** devicehealth, clienthealth, networkhealth, issue, compliance, securityadvisory, client, audit:logs, site:topology
3. **Freshness:** If any sourcetype's latest event is older than 2 hours, the TA input may have failed

Schedule this search as a daily health check and alert when any sourcetype shows 'Stale' status.

## Detailed Implementation

### Prerequisites
- ALL Catalyst Center modular inputs must be configured and running — this UC monitors the health of every data collection pipeline. If a pipeline fails silently, this is the UC that detects it.
- This is a **crawl-tier meta-monitoring** UC — it monitors the monitoring system itself. Deploy it early so you know immediately if any data feed stops.
- Route alerts from this UC to the **Splunk admin team**, not the network operations team. A stalled input is a collection-infrastructure issue, not a network issue.

### Step 1 — Configure data collection
No additional inputs. This UC queries the data that all other inputs produce. It works by checking whether each expected sourcetype has received events recently.

Verify all configured sourcetypes are producing events:
```spl
index=catalyst earliest=-2h
| stats latest(_time) as last_event count by sourcetype
| eval hours_since=round((now()-last_event)/3600,1)
| eval status=case(hours_since < 1, "Active", hours_since < 4, "Delayed", 1==1, "STALE")
| sort -hours_since
```
Every configured sourcetype should show `status=Active`. `Delayed` means the input hasn't polled recently. `STALE` means no events for 4+ hours — investigate immediately.

### Step 2 — Create the search and alert
```spl
index=catalyst earliest=-4h
| stats latest(_time) as last_event count as event_count by sourcetype
| eval hours_since=round((now()-last_event)/3600,1)
| eval expected_interval=case(
    sourcetype="cisco:dnac:devicehealth", 0.25,
    sourcetype="cisco:dnac:clienthealth", 0.25,
    sourcetype="cisco:dnac:networkhealth", 0.25,
    sourcetype="cisco:dnac:issue", 0.25,
    sourcetype="cisco:dnac:compliance", 1,
    sourcetype="cisco:dnac:securityadvisory", 1,
    sourcetype="cisco:dnac:device", 1,
    sourcetype="cisco:dnac:audit:logs", 0.083,
    sourcetype="cisco:dnac:event:notification", 0,
    1==1, 1)
| eval status=case(
    expected_interval=0, if(hours_since < 24, "Active", "No events (event-driven)"),
    hours_since < expected_interval * 2, "Active",
    hours_since < expected_interval * 4, "Delayed",
    1==1, "STALE — input may be down")
| where status != "Active"
| table sourcetype, last_event, hours_since, expected_interval, status, event_count
| sort -hours_since
```

Why per-sourcetype expected intervals: each Catalyst Center input polls at a different frequency. `devicehealth` polls every 15 minutes (0.25h), `compliance` polls hourly (1h), `audit_logs` polls every 5 minutes (0.083h). The status check compares `hours_since` against `2× expected_interval` — a `devicehealth` input silent for 30 minutes is normal (one missed poll); silent for 1 hour is `Delayed`; silent for 4+ hours is `STALE`.

Why `event_count` in the output: provides context. A sourcetype with 0 events in 4 hours is definitely stalled. A sourcetype with 500 events but `hours_since=3` may have a timestamp parsing issue (events are arriving but with old timestamps).

Why `event:notification` has `expected_interval=0`: webhook events are push-based and may arrive irregularly. 24 hours without a webhook event is normal for a quiet network. The status for event-driven sources uses a different threshold.

Schedule as Alert: `0 * * * *` (hourly), trigger when any sourcetype shows `STALE`. Route to the Splunk admin team.

### Step 3 — Validate
(a) Temporarily disable one input (e.g., `devicehealth`). Within 1 hour, the search should show that sourcetype as `Delayed`. Within 2 hours, `STALE`. Re-enable the input and verify it returns to `Active`.

(b) Run the search and verify all expected sourcetypes appear. If a sourcetype is missing entirely, the input was never enabled — check the TA configuration.

(c) Check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for any ERROR or WARN messages from the TA. Common issues: `401 Unauthorized` (credential expired), `Connection refused` (Catalyst Center down), `429 Too Many Requests` (API throttling).

(d) Verify the `expected_interval` values match your actual input configurations. If you changed an input from 900s to 1800s, update the `case()` accordingly.

### Step 4 — Operationalize
- Admin dashboard: table of all sourcetypes with status, colour-coded (green Active, yellow Delayed, red STALE).
- Single value: count of STALE sourcetypes (red ≥ 1).
- Alert: STALE status → page the Splunk admin team. Include the sourcetype name and `hours_since` in the alert payload.

Runbook (owner: Splunk Admin team):
1. Receive STALE alert. Note the affected sourcetype.
2. Check the TA input configuration: is the input enabled? Is the account configured correctly?
3. Check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" ERROR` for the affected input's error messages.
4. Common fixes:
   - `401 Unauthorized` → credential expired. Update in TA Configuration → Account → Edit.
   - `Connection refused` → Catalyst Center is unreachable. Check network path and Catalyst Center health.
   - `429 Too Many Requests` → API throttling. Increase the input's poll interval.
   - `SSL certificate verify failed` → certificate changed. Update trust or temporarily disable verification.
5. After fix: verify events resume within one poll cycle. The status should return to `Active`.

### Step 5 — Troubleshooting

- **All sourcetypes show STALE** — the Heavy Forwarder running the TA is down, or the Catalyst Center is completely unreachable. Check HF health first, then Catalyst Center connectivity.

- **One sourcetype STALE while others are Active** — that specific input is disabled or has a configuration error. Check TA → Inputs for that input type.

- **`hours_since` is very large but events exist** — timestamp parsing issue. Events are arriving but `_time` is set to an old timestamp. Check `props.conf` for the sourcetype's `TIME_FORMAT`.

- **Event-driven sourcetype (`event:notification`) always shows "No events"** — no webhooks have fired recently. This is normal for a quiet network. If you expect webhook events, verify the HEC token and Catalyst Center webhook configuration (UC-5.13.64).

- **False STALE for low-volume sourcetypes** — some sourcetypes (audit logs on quiet days) may genuinely have no new events for hours. Adjust the `expected_interval` for those sourcetypes.

- **Want to monitor non-Catalyst-Center data feeds too** — extend the search to include other indexes and sourcetypes. This UC's pattern works for any data source: check `latest(_time)` per sourcetype against an expected interval.

- **Alert fires during Catalyst Center maintenance** — expected. The TA can't poll during maintenance. Suppress with `catalyst_maintenance_windows` lookup or acknowledge during planned windows.

- **Multiple STALE alerts from the same Heavy Forwarder** — the HF itself may be unhealthy (disk full, CPU overloaded, Splunk service stopped). Check `index=_internal host=<HF_hostname>` for HF-level health.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:*" | stats count as event_count latest(_time) as last_event earliest(_time) as first_event by sourcetype | eval hours_since_last=round((now()-last_event)/3600,1) | eval status=if(hours_since_last>2,"Stale","Active") | sort -hours_since_last
```

## Visualization

Table: sourcetype, event_count, hours_since_last, status; heatmap for Stale vs Active; optional trend of event_count per sourcetype over 7 days.

## Known False Positives

**Low-frequency inputs appearing stale when checked against a tight freshness threshold.** Some Catalyst Center API endpoints (site hierarchy, SWIM golden image, license) are polled hourly or less frequently. If the data freshness check uses a 15-minute threshold, these inputs will always appear stale. Distinguish by checking the configured poll interval for each input type in the TA configuration. Suppress by maintaining a `catalyst_input_intervals` lookup with expected poll intervals per sourcetype and comparing freshness against the per-sourcetype threshold.

**TA poll failure due to Catalyst Center API rate limiting.** If the TA exceeds Catalyst Center's API rate limits, some inputs may fail to collect data, appearing as stale. Distinguish by checking `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for rate limit errors (HTTP 429). Suppress by adjusting the TA poll intervals to stay within the rate limit.

**Catalyst Center platform maintenance causing a temporary collection gap.** During Catalyst Center upgrades or restarts, the API is unavailable and the TA cannot collect data. Distinguish by checking whether the collection gap coincides with a Catalyst Center maintenance window. Suppress by annotating data freshness gaps with maintenance window records.

**Splunk forwarder or heavy forwarder restart causing a brief collection gap.** When the Splunk instance running the TA restarts, there is a brief gap in data collection. Distinguish by checking `index=_internal sourcetype=splunkd "Splunkd starting" OR "Splunkd restarting"` for restart events coinciding with the collection gap. Suppress by allowing a 10-minute gap after a forwarder restart before flagging data freshness issues.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Intent API Reference — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!api-reference)
