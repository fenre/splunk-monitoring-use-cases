<!-- AUTO-GENERATED from UC-5.8.1.json — DO NOT EDIT -->

---
id: "5.8.1"
title: "DNA Center Assurance Alerts (Cisco Catalyst Center)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.1 · DNA Center Assurance Alerts (Cisco Catalyst Center)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl

*We help you see when Cisco's management system flags real problems and priorities on the network, so you can act before the trouble spreads to the apps and phones we all use.*

---

## Description

Centralises Catalyst Center Assurance issue alerts in Splunk, providing a prioritised summary of AI/ML-detected network issues by priority, category, and issue name.

## Value

Network operations teams centralize Catalyst Center Assurance AI/ML-detected issues in Splunk for cross-domain correlation, priority-based triage, and resolution time tracking across the wireless, switching, and routing infrastructure.

## Implementation

Install the Cisco Catalyst Add-on for Splunk (Splunkbase 7538) and configure a Catalyst Center account. Enable the `issue` input pointing to `index=catalyst`. The TA polls `GET /dna/intent/api/v1/issues` every 15 minutes by default. Key fields include `priority`, `category`, `name`, `status`, and `deviceName`.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk (TA_cisco_catalyst, Splunkbase 7538) installed on a search head or heavy forwarder. Configure a Catalyst Center account with a service account holding NETWORK-ADMIN-ROLE or SUPER-ADMIN-ROLE. Catalyst Center 2.3.5+ recommended for consistent Assurance issue data.
- TA `issue` modular input enabled, polling `GET /dna/intent/api/v1/issues` (Intent API, paginated). Default interval: 900s (15 minutes). Each poll returns one event per active issue. Data lands in `index=catalyst` with `sourcetype=cisco:dnac:issue`.
- Key fields: `priority` (P1/P2/P3/P4), `category` (Onboarding, Connected, Availability, Application, Device, Sensor), `name` (issue title), `status` (active/resolved), `deviceName`, `siteNameHierarchy`, `issueId`, `lastOccurredTime`.
- Build `catalyst_sites.csv` lookup: `siteNameHierarchy,site_short_name,region,tier` (e.g., `Global/US/NYC/Floor-1,NYC-F1,East,Tier1`).

### Step 1 — Configure data collection
Verify issue data arrival:
```spl
index=catalyst sourcetype="cisco:dnac:issue" earliest=-1h
| stats count dc(issueId) as unique_issues by priority
```
You should see counts across P1-P4. If empty: check TA account credentials, verify the `issue` input is enabled, and look in `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for API errors (403=RBAC, 401=auth, timeout=connectivity).

### Step 2 — Create the search and alert

**Primary search — Prioritized issue summary with site context:**
```spl
index=catalyst sourcetype="cisco:dnac:issue" earliest=-24h
| dedup issueId sortby -_time
| lookup catalyst_sites.csv siteNameHierarchy OUTPUT site_short_name region tier
| eval priority_num=case(priority="P1",1, priority="P2",2, priority="P3",3, priority="P4",4, 1==1,5)
| stats count as issue_count dc(deviceName) as affected_devices values(name) as issue_types by priority, category, site_short_name, tier
| sort priority_num, -issue_count
```

#### Understanding this SPL: Catalyst Center Assurance uses AI/ML to detect network issues across wireless, switching, and routing domains. Issues are de-duplicated by `issueId` because the same active issue is reported on every poll. The `priority` field reflects Catalyst Center's AI assessment of business impact: P1 is highest (service-affecting). Grouping by `category` separates onboarding problems (client joining failures) from connectivity issues and device health problems.

**P1/P2 issue trending:**
```spl
index=catalyst sourcetype="cisco:dnac:issue" priority IN ("P1", "P2") earliest=-7d
| dedup issueId, _time sortby -_time
| bin _time span=1h
| stats dc(issueId) as active_issues by _time, priority, category
| timechart span=1h sum(active_issues) by priority
```

**Issue resolution time analysis:**
```spl
index=catalyst sourcetype="cisco:dnac:issue" status="resolved" earliest=-30d
| stats earliest(_time) as first_seen latest(_time) as last_seen by issueId, name, priority, category, deviceName
| eval resolution_hours=round((last_seen - first_seen)/3600, 1)
| stats avg(resolution_hours) as avg_hours median(resolution_hours) as median_hours p95(resolution_hours) as p95_hours by priority, category
| sort priority
```

### Step 3 — Validate
(a) In Catalyst Center: Assurance > Issues. Compare P1/P2 count and device names for the same time window. Minor differences are expected due to poll timing.
(b) Pick two specific issues in the Catalyst Center UI and verify they appear in Splunk with matching priority, category, and device.
(c) Run `| timechart count` over 24h to verify a steady event stream with no silent polling gaps.

### Step 4 — Operationalize
Dashboard ("Catalyst Center — Assurance Issues"):
- Row 1 — Single-value tiles: "P1 active", "P2 active", "Total active issues", "Affected devices".
- Row 2 — Issue summary table: priority, category, site, issue types, device count (drilldown to device detail).
- Row 3 — P1/P2 trending over 7 days (timechart).
- Row 4 — Resolution time analysis by priority and category.

Alerting:
- Critical (any P1 issue active): page NOC immediately.
- High (P2 issue count > 5): alert for investigation.
- Warning (P1/P2 trending upward): proactive attention needed.

### Step 5 — Troubleshooting

- **Fewer issues in Splunk than Catalyst Center** — Check the service account's virtual domain scope. If the account is scoped to a subset of sites, the API returns only issues within those sites. Use SUPER-ADMIN-ROLE for full visibility.

- **Issue data stops arriving** — Catalyst Center API rate limits may throttle the TA. Check `_internal` for HTTP 429 errors. Increase the poll interval to reduce load. Also verify Catalyst Center process health: System > System 360.

- **Same issue appears multiple times** — The TA reports each active issue on every poll. Use `dedup issueId` to get unique issues. The re-reporting enables tracking of issue duration (time between first and last poll with that issueId active).

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue"
| stats count by priority, category, name | sort -priority -count
```

## Visualization

Table (issue name, priority, category, count), Bar chart (issue count by priority), Single value panels (P1/P2 open count).

## Known False Positives

Planned Assurance recalibrations, lab controllers, and polling delays after upgrades can look like new issues. Compare any spike to the Catalyst Center Assurance / Issues UI before you page someone.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](../../docs/guides/catalyst-center.md)
