<!-- AUTO-GENERATED from UC-5.13.23.json — DO NOT EDIT -->

---
id: "5.13.23"
title: "P1/P2 Critical Issue Alerting"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.23 · P1/P2 Critical Issue Alerting

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Crawl &middot; **Status:** Verified

*We set up an urgent alarm that goes off when Catalyst Center's AI finds a critical problem on the network — like a major switch going offline or hundreds of people unable to connect. The alarm goes directly to the team leader's phone within minutes so they can start fixing it before most people even notice something is wrong.*

---

## Description

Fires an alert when any P1 (critical) or P2 (high) Assurance issue is active and unresolved, providing the issue names, affected devices, and categories so the NOC can begin triage immediately — within the 15-minute poll cycle that Catalyst Center's AI/ML engine detected the problem.

## Value

P1 issues mean critical infrastructure is down — core switches unreachable, WLC failures, complete site outages. P2 issues mean significant degradation — widespread onboarding failures, major performance drops affecting hundreds of users. Every minute these go unnoticed is a minute of user impact. This alert is the fastest path from Catalyst Center AI detection to human action in Splunk, with enough context (issue name, device, category) to skip the 'what happened?' phase and go straight to 'let me fix it.' It's the paging alert that replaces the NOC engineer manually refreshing the Catalyst Center Assurance GUI every 15 minutes.

## Implementation

Same `issue` input as UC-5.13.21. Schedule as alert: cron `*/5 * * * *` (every 5 minutes for fastest P1 response), time range `-15m to now`, trigger on any results. Throttle by `priority` for 4 hours. Route P1 to high-urgency PagerDuty, P2 to low-urgency.

## Detailed Implementation

### Prerequisites
- UC-5.13.21 (Issue Summary) must be operational — same `issue` data feed.
- Verify that `priority` field values match the expected format: `P1`, `P2`, `P3`, `P4`. Run `| stats count by priority` to confirm. Some Catalyst Center versions may use different strings.
- Verify that `status` field differentiates active from resolved: `| stats count by status`. The `status != "RESOLVED"` filter must match the actual resolved-state string.
- Configure alert actions BEFORE enabling the alert. A P1 alert that fires but doesn't page anyone is worse than useless — it creates a false sense of coverage.
- Decide on escalation tiers: P1 → high-urgency page to network operations lead + incident channel; P2 → low-urgency page to on-call + ops channel.

### Step 1 — Configure data collection
Same `issue` input as UC-5.13.21. No additional configuration.

For fastest P1 detection, consider setting the `issue` input interval to 300s (5 minutes) instead of the default 900s. This reduces detection latency from 15 minutes to 5 minutes, at the cost of 3× more API calls. Monitor for HTTP 429 throttling if you have many other inputs running simultaneously.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED"
| stats dc(issueId) as open_issues values(name) as issue_names values(deviceName) as affected_devices by priority, category
| sort priority
```

Why `dc(issueId)` not `count`: the same issue appears in every poll while active. `dc(issueId)` gives the actual number of distinct active P1/P2 issues. `count` would show `issues × polls_in_window`, which inflates the severity.

Why `values(name)` and `values(deviceName)`: these provide the context that makes the alert actionable. An alert that says "3 P1 issues" is useless; an alert that says "3 P1 issues: 'Device Unreachable' on core-sw-01, 'Client Onboarding Failure' on wlc-hq-01, 'Link Down' on dist-sw-03" tells the responder exactly what to investigate.

Why `by priority, category`: groups issues so the responder can see whether P1s are concentrated in one category (e.g., all Connectivity = upstream failure) or spread across categories (multiple independent problems).

Why `status != "RESOLVED"`: excludes issues that Catalyst Center has already auto-resolved. Without this filter, the alert would fire for issues that are no longer active.

Schedule as Alert:
- Cron: `*/5 * * * *` (every 5 minutes for P1 response)
- Time range: `-15m to now` (covers one poll cycle at default 900s)
- Trigger: "Number of results > 0"
- Throttle: by `priority` for `4h` (separate throttle for P1 and P2)
- Severity: Critical (for P1 results), High (for P2-only results)

For differentiated P1 vs P2 routing, create TWO alerts:
```spl
-- Alert 1: P1 only (highest urgency)
index=catalyst sourcetype="cisco:dnac:issue" priority="P1" status!="RESOLVED"
| stats dc(issueId) as p1_count values(name) as issues values(deviceName) as devices
| where p1_count > 0
```
```spl
-- Alert 2: P2 only (lower urgency)
index=catalyst sourcetype="cisco:dnac:issue" priority="P2" status!="RESOLVED"
| stats dc(issueId) as p2_count values(name) as issues values(deviceName) as devices
| where p2_count > 0
```

### Step 3 — Validate
(a) If you have a lab environment, create a P1 issue (e.g., shut a core switch interface). Within the next poll cycle (5–15 minutes), the alert should fire with the device in the results.

(b) Run the search over the last 7 days to see historical P1/P2 activity. Every result should correspond to a real incident your team handled. If it shows issues that were never investigated, the alerting is providing value by catching previously-missed events.

(c) Cross-reference with **Catalyst Center > Assurance > Issues** filtered to P1/P2. The active issue count should match `dc(issueId)` from the search.

(d) Verify throttling: trigger the alert twice for the same priority within 4 hours. You should receive only one notification.

(e) Test alert action delivery: temporarily modify the search to trigger on P3 or P4 (which likely exist), verify the PagerDuty/Slack notification arrives, then revert.

### Step 4 — Operationalize
Alerting:

**P1 (Critical):**
- PagerDuty: high-urgency, network operations lead on-call
- Custom details: `priority`, `category`, `issue_names`, `affected_devices`, `open_issues` count
- Include link to **Catalyst Center > Assurance > Issues** filtered to P1
- Include link to Splunk Issue Triage dashboard (UC-5.13.21)
- Slack: `#incident-network` for immediate team visibility

**P2 (High):**
- PagerDuty: low-urgency, on-call engineer
- During business hours only: `| where date_hour >= 7 AND date_hour <= 19`
- Slack: `#network-ops` for awareness

Runbook (owner: NOC Tier 1):
1. Open the alert. Note `priority`, `category`, and `affected_devices`.
2. For **P1 Connectivity** ("Device Unreachable"): this is a hard down. Ping the device from the jumpbox. If unreachable, check power/physical. If reachable, the issue may be between Catalyst Center and the device — check SNMP/management reachability. See UC-5.13.6 runbook.
3. For **P1 Onboarding** (mass authentication failure): check ISE health. If ISE is down, escalate to identity team. See UC-5.13.14 runbook.
4. For **P2 Performance**: check UC-5.13.1 (device health) for the affected devices. Identify the dominant subscore (CPU, memory, link) and escalate accordingly.
5. Check whether the issue is **new** or **recurring**: run `| stats count by issueId` — a high count means it's been active across many polls (persistent). A count of 1 means it just appeared.
6. After resolution, verify the issue transitions to RESOLVED in the next poll cycle.

### Step 5 — Troubleshooting

- **Alert fires every 5 minutes for the same issue** — throttling not configured. Set throttle to 4 hours by `priority` (or by `issueId` for per-issue throttling).

- **Alert never fires but P1 issues exist in the Catalyst Center GUI** — the `priority` or `status` field values don't match the SPL filter. Run `| stats values(priority) values(status)` to see the actual strings. Common variant: `Active` vs `ACTIVE`.

- **Alert fires for issues during planned maintenance** — filter with `catalyst_maintenance_windows` lookup.

- **Too many P2 alerts during overnight batch operations** — add business-hours filter or raise the P2 threshold.

- **Alert fires for P1 AP issues that affect only one room** — Catalyst Center assigns P1 to AP failures regardless of user impact. Add a `device_criticality` lookup to differentiate core/distribution P1s (genuinely critical) from AP P1s (lower impact).

- **`values(deviceName)` shows too many devices in one alert** — a correlated event (upstream failure) can affect dozens of devices. Truncate with `| eval affected_devices=mvindex(affected_devices, 0, 9)` to show the first 10.

- **Alert action doesn't trigger** — check `index=_internal sourcetype=splunkd component=AlertManager` for the alert name. Common: PagerDuty integration key expired.

- **P1 count disagrees with Catalyst Center** — time window and `status` filter differences. The Splunk search covers `-15m`; Catalyst Center may show a longer window. Align for comparison.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED"
| stats dc(issueId) as open_issues values(name) as issue_names values(deviceName) as affected_devices by priority, category
| sort priority
```

## Visualization

(1) Alert payload table: priority, category, issue_names, affected_devices, open_issues count. (2) Single value: P1 count (red ≥ 1) + P2 count (orange ≥ 1). (3) Timeline: `| timechart span=1h dc(issueId) by priority` over 7 days showing P1/P2 frequency. (4) Drilldown links to UC-5.13.21 (full backlog) and UC-5.13.26 (by device/site).

## Known False Positives

**Catalyst Center auto-resolving transient P1 issues before investigation.** Some P1 issues (e.g., brief device unreachability during a spanning tree reconvergence) auto-resolve within 2–5 minutes. The alert fires but by the time the engineer looks, the issue is RESOLVED in the Catalyst Center UI. Distinguish by checking `status` — if it transitioned to RESOLVED within 5 minutes, it was transient. Suppress by requiring the issue to persist across 2 consecutive polls: use a lookup or summary index to track prior-poll state.

**Known P2 issues for devices in maintenance.** Devices undergoing planned firmware upgrades will generate P1/P2 issues ("Device Unreachable") during the reload window. Distinguish by correlating with ITSM change records. Suppress with `catalyst_maintenance_windows` lookup filtering.

**P1 priority assigned to non-critical device types.** Catalyst Center may assign P1 to an AP failure that affects only a storage closet. Distinguish by checking `deviceName` or `category` — AP-level P1s have lower blast radius than switch P1s. Suppress by adding a `device_criticality` lookup and downgrading AP-only P1s to P2 in the alert routing.

**Same issue oscillating between ACTIVE and RESOLVED.** An intermittent failure (flapping link, unstable PoE) may cause the same `issueId` to cycle between ACTIVE and RESOLVED, triggering the alert repeatedly. Distinguish by checking the issue history with `| stats count by issueId | where count > 5`. Suppress by throttling per `issueId` for 4 hours.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Issues endpoint](https://developer.cisco.com/docs/catalyst-center/#!issues)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Splunk Alert Actions — PagerDuty, Webhook, Email](https://docs.splunk.com/Documentation/Splunk/latest/Alert/Setupalertactions)
