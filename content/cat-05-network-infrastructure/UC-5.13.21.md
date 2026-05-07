<!-- AUTO-GENERATED from UC-5.13.21.json — DO NOT EDIT -->

---
id: "5.13.21"
title: "Assurance Issue Summary by Priority and Category"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.21 · Assurance Issue Summary by Priority and Category

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Crawl &middot; **Status:** Verified

*We collect all the problems that Catalyst Center's AI engine has found on your network and organise them by urgency, so your team knows what to fix first. The ones that keep showing up poll after poll float to the top — those are the persistent problems that need a proper fix, not just a quick restart.*

---

## Description

Aggregates all active Catalyst Center Assurance issues into a Pareto table by priority (P1–P4) and category, so NOC engineers can see at a glance which issue types are dominating the backlog and which are the most persistent — addressing the highest-count, highest-priority rows first for maximum impact.

## Value

Catalyst Center's AI/ML engine detects network issues automatically — connectivity losses, onboarding failures, performance degradation — but the native Assurance UI is a closed ecosystem. Centralising these issues in Splunk unlocks three things the GUI alone cannot provide: (1) correlation with syslog, NetFlow, ISE, and change-management data to find root causes faster; (2) historical trending beyond Catalyst Center's 7-day retention to prove that a recurring issue is getting worse, not better; (3) automated triage via SOAR playbooks that enrich, deduplicate, and route issues without a human clicking through the GUI for each one.

## Implementation

Install `TA_cisco_catalyst` (Splunkbase 7538) on the Search Head and Heavy Forwarder. Configure a Catalyst Center account and enable the `issue` input (Inputs → Create → Issues: account `catcenter-prod`, index `catalyst`, interval `900`). For P1 alerting, schedule a separate alert with `| where priority="P1" AND status="ACTIVE"` every 5 minutes, throttled by `issueId` for 4 hours.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) ≥1.0 installed on Search Heads AND the Heavy Forwarder / single-instance running inputs.
- Catalyst Center **2.3.5+** for stable `priority`, `category`, `name`, `status`, `issueId` field names. Older releases may use different category names or priority labels — validate with a sample event.
- Service account with **NETWORK-ADMIN-ROLE** (minimum for Assurance issue data). **SUPER-ADMIN-ROLE** is needed only for audit logs.
- Network: HTTPS (TCP 443) from Splunk HF to Catalyst Center management IP/FQDN.
- Splunk role: users need `srchIndexesAllowed = catalyst`.
- License headroom: scales with *active issue count*, not device count. A campus with 30 active issues at 900s interval produces ~30 events/poll × 96 polls/day × 600 bytes ≈ **1.7 MB/day**. A well-managed network has fewer issues; a network in distress can spike to 200+ active issues temporarily. Budget for peak, not average.
- Terminology alignment: map Catalyst Center's `category` values (Connectivity, Onboarding, Connected, Performance, Application, etc.) to your ITIL service taxonomy and ServiceNow category tree *before* automating ticket creation. Document the mapping in your runbook so NOC engineers don't waste time re-categorising.

### Step 1 — Configure data collection
In the TA on the Heavy Forwarder: Inputs → Create New Input → Issues.

| Setting | Value |
|---------|-------|
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `900` (15 minutes — for P1 alerting consider a separate 300s input or use webhooks via UC-5.13.64) |

The TA authenticates to `POST /dna/system/api/v1/auth/token`, then polls `GET /dna/intent/api/v1/issues`. The API is paginated — the TA follows pagination automatically. Each poll returns **all currently active issues**, not just new ones since the last poll. This means the same `issueId` appears in every poll for as long as the issue remains ACTIVE.

Sample event:
```json
{
  "issueId": "abc12345-def6-7890-ghij-klmno1234567",
  "name": "Network Device 10.1.1.1 Is Unreachable From Controller",
  "priority": "P1",
  "category": "Connectivity",
  "status": "ACTIVE",
  "deviceName": "core-sw-01.hq.example.com",
  "siteId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "lastOccurenceTime": 1714060200000,
  "deviceType": "Cisco Catalyst 9300 Switch"
}
```

Verification: wait one poll interval, then run:
```spl
index=catalyst sourcetype="cisco:dnac:issue" earliest=-30m
| stats count by priority
```
Compare the P1/P2/P3/P4 breakdown with **Catalyst Center > Assurance > Issues > Priority** filter. Counts should match within one poll's margin.

If no events arrive, check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors.

Expected event volume: `active_issue_count × 96 polls/day × ~600 bytes`. A campus with 30 issues ≈ 1.7 MB/day; a network in crisis with 200 issues ≈ 11 MB/day.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:issue"
| stats count by priority, category, name
| sort -priority -count
```

Why `count` not `dc(issueId)`: this is a deliberate design choice. `count` reflects **persistence** — an issue that has been active for 10 poll cycles produces a count of 10, while a transient issue that appeared once and resolved produces 1. This Pareto table therefore weights long-standing issues higher, which is the correct triage signal. If you need unique issue counts instead ("how many distinct problems exist right now?"), use `| stats dc(issueId) as unique_issues` in UC-5.13.22 or a companion panel.

Why `sort -priority -count`: lexicographic sort on `P1`…`P4` strings works correctly for single-digit priorities. P1 sorts first (highest priority), and within each priority band, the most-counted issue names appear at the top. If Cisco ever adds `P10`, you'd need numeric conversion — monitor after Catalyst Center upgrades.

Why no `where status!="RESOLVED"` filter: the TA may be configured to return only active issues (check the input's Advanced settings). If it returns both active and resolved, add the filter. Validate by checking whether `| stats count by status` shows RESOLVED events. If it does and you want only the active backlog, filter them out.

Schedule as Alert (P1 detection): cron `*/5 * * * *`, time range `-15m to now`, trigger on `priority="P1" AND status="ACTIVE" | stats dc(issueId) as p1_count | where p1_count > 0`, throttle on `priority` for `4h`. This is the fastest-response alert in the Catalyst Center UC family.

Schedule as Report (daily summary): cron `0 7 * * *`, time range `-24h to now`, output to scheduled PDF delivered to `#network-ops` Slack channel.

### Step 3 — Validate
(a) In Catalyst Center, navigate to **Assurance > Issues**. Set the priority filter to P1 and P2. Count the issues. In Splunk, run `index=catalyst sourcetype="cisco:dnac:issue" earliest=-15m (priority="P1" OR priority="P2") | stats dc(issueId) as unique_issues`. The count should match.

(b) Pick a specific issue in the Catalyst Center UI — note its `name`, `priority`, `category`, and `deviceName`. Search for it in Splunk: `index=catalyst sourcetype="cisco:dnac:issue" issueId="<paste-the-id>" | table _time priority category name deviceName status`. The fields should match exactly.

(c) Check for category completeness: `index=catalyst sourcetype="cisco:dnac:issue" | stats dc(category) as categories, values(category) as category_list`. Compare the category list with the categories visible in **Catalyst Center > Assurance > Issues > Category** dropdown.

(d) Confirm ingest cadence: `index=catalyst sourcetype="cisco:dnac:issue" | timechart span=15m count`. Expect a regular pattern. Flat zero for > 1 hour indicates a stalled input (unless your network genuinely has zero active issues — validate by checking the Catalyst Center GUI).

(e) Verify deduplication behaviour: `index=catalyst sourcetype="cisco:dnac:issue" earliest=-1h | stats count, dc(issueId) as unique_issues`. If `count >> unique_issues`, the TA is returning the same issues on each poll (expected behaviour). If `count ≈ unique_issues`, the TA may be filtering to only new issues (check the input configuration).

### Step 4 — Operationalize
Dashboard (recommended layout, named "Catalyst Center — Assurance Issue Triage"):
- Row 1 — Single value tiles: "Active P1 Issues" (red threshold ≥ 1), "Active P2 Issues" (orange threshold ≥ 5), "Total Active Issues" (neutral). Each tile links to a filtered version of the table below.
- Row 2 — Sortable table (this UC's search): priority | category | name | count — sorted by -priority -count. Row colour: P1 red background, P2 orange, P3 yellow, P4 grey. Drilldown: click a row → open filtered view showing affected devices for that specific issue name.
- Row 3 — Two side-by-side panels: bar chart of count by priority (left), pie chart of share by category (right). The category pie shows whether you have a Connectivity-dominated backlog (infrastructure), an Onboarding-dominated backlog (ISE/RADIUS), or a Performance-dominated backlog (capacity).
- Row 4 — Timechart of `| timechart span=1h dc(issueId) by priority` over 7 days, from UC-5.13.22 (Issue Trending). This shows whether the backlog is growing, stable, or shrinking.
- Time-picker presets: "Last 1 hour" (incident), "Last 24 hours" (daily triage), "Last 7 days" (weekly ops review).

Alerting:
- PagerDuty/On-Call: P1 alert triggers high-urgency page to network operations lead within 5 minutes. P2 triggers low-urgency page during business hours only. Annotate the alert with `name`, `deviceName`, `category`, and a link to Catalyst Center > Assurance > Issues.
- Slack/Teams: all P1/P2 issues posted to `#network-ops` with device details.
- ServiceNow: auto-create incident for P1 issues using the SOAR playbook in UC-5.13.76. Map `category` to ServiceNow category using your ITIL mapping lookup.

Runbook (owner: NOC Tier 1 on-call):
1. Open the Assurance Issue Triage dashboard. Identify the top row — highest priority, highest count.
2. For P1 Connectivity issues: this usually means a device is unreachable. Drill to the affected `deviceName`. Check UC-5.13.1 (device health) for the device's overall score. Ping the device from the NOC jumpbox.
3. For P1/P2 Onboarding issues: this usually means client authentication is failing. Check UC-5.13.9 (client health) and correlate with `index=ise sourcetype=cisco:ise:*` for RADIUS failures. If ISE is the root cause, escalate to the identity team.
4. For Performance issues: check UC-5.13.16 (network health) for the aggregate impact. If localised to one site, drill to UC-5.13.19 (health by site).
5. For recurring issues (same `name` with high count): open Problem Management ticket. Use UC-5.13.25 (Top Recurring Issues) to identify chronic offenders.
6. Check whether the issue is already known: search `catalyst_known_issues` lookup. If it matches a known Cisco bug, note the workaround and track for firmware upgrade.

### Step 5 — Troubleshooting

- **No events at all** — `issue` input not enabled, or TA not on the Heavy Forwarder. Check: TA → Inputs → confirm Issues is present and enabled. CLI: `$SPLUNK_HOME/bin/splunk btool inputs list --debug | grep -i issue`. Check `splunkd.log` for `ExecProcessor` entries.

- **Events arrive but all show `status=RESOLVED`** — the TA is pulling the full issue history, not just active issues. Add `| where status="ACTIVE"` to the search. Or check the TA's input configuration for a "status filter" or "active only" setting.

- **Huge event count spike on first poll** — the TA pulled the entire backlog on first run. This is normal. Subsequent polls will be smaller as you narrow the time range in your searches. Set `earliest=-1h` in dashboards to filter the initial spike.

- **Priority strings changed after Catalyst Center upgrade** — P1/P2/P3/P4 is the current convention, but older versions may have used different labels. Run `| stats count by priority` after any Catalyst Center upgrade to check for new priority values. Update SPL filters and dashboard row-colouring if needed.

- **Category values you don't recognise** — Catalyst Center adds new issue categories between versions. Run `| stats count by category` periodically and update your ITIL mapping lookup. New categories are not a bug — they reflect expanded Assurance detection capabilities.

- **Count in Splunk much higher than the GUI shows** — the GUI may filter by time window ("last 1 hour") or site scope differently. Align your Splunk time range and confirm the service account's virtual domain scope matches the GUI view.

- **Issue appears in Splunk but not in the Catalyst Center GUI** — the issue may have been resolved between the last poll and when you checked the GUI. Check `status` in the Splunk event — if it's RESOLVED, the issue was closed before you looked. Or the GUI is filtered to a specific site/category.

- **API throttling (HTTP 429)** — the issues endpoint is paginated. If your Catalyst Center has hundreds of active issues, the TA makes multiple API calls per poll. Combined with other inputs polling simultaneously, this can trigger rate limits. Stagger input intervals or reduce poll frequency for non-critical inputs.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue"
| stats count by priority, category, name
| sort -priority -count
```

## Visualization

(1) Sortable table: priority, category, name, count — sorted by -priority -count to surface highest-priority, most-frequent issues at the top. (2) Bar chart: count by priority (P1 red, P2 orange, P3 yellow, P4 grey). (3) Pie or donut: share by category (Connectivity, Onboarding, Performance, etc.) to show the dominant issue type. (4) Single value: count of active P1 issues (red threshold ≥ 1, links to filtered table).

## Known False Positives

**Recurring known-bug issues that Catalyst Center auto-detects but have published workarounds.** Some Assurance issue types correspond to known Catalyst Center or IOS-XE bugs with available fixes or workarounds. These persist in the issue feed until the firmware is upgraded. Distinguish by checking whether the `name` matches a known Cisco bug ID pattern or a previously triaged issue. Suppress by maintaining a `catalyst_known_issues` lookup with `name` patterns and exclusion flags; filter known-bug issues from the priority summary while tracking them in a separate remediation dashboard.

**Same issue re-polled on every cycle inflating the count.** The issues API returns all currently active issues on each poll. If you count events rather than distinct `issueId` values, counts will inflate with each poll cycle. Distinguish by checking whether `| stats dc(issueId)` is significantly lower than `| stats count`. This is a *design choice* — see Step 2 for why event count is intentional in this UC.

**Informational P4 issues creating noise in the priority distribution.** P4 informational issues (e.g., device sync status, configuration recommendations) may dominate the issue count without indicating operational problems. Distinguish by checking whether the majority of issues are P4 with `status` that auto-resolves. Suppress by filtering `| where priority IN ("P1","P2","P3")` for operational dashboards and tracking P4 separately for trend analysis.

**Assurance issue category reclassification after Catalyst Center upgrade.** Catalyst Center may add or rename issue categories between versions, causing apparent new issue types in the summary. Distinguish by checking whether new categories appeared coincident with a Catalyst Center upgrade. Suppress by maintaining a `catalyst_issue_categories` lookup that maps old and new category names.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Issues endpoint](https://developer.cisco.com/docs/catalyst-center/#!issues)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Catalyst Center Assurance Issue Categories — Cisco Documentation](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center-assurance/assurance-overview.html)
