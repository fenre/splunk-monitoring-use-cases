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

Network operations teams gain cross-domain visibility by correlating Catalyst Center Assurance alerts with syslog, SNMP, and other Splunk data sources, reducing mean time to detect and resolve infrastructure problems.

## Implementation

Install the Cisco Catalyst Add-on for Splunk (Splunkbase 7538) and configure a Catalyst Center account. Enable the `issue` input pointing to `index=catalyst`. The TA polls `GET /dna/intent/api/v1/issues` every 15 minutes by default. Key fields include `priority`, `category`, `name`, `status`, and `deviceName`.

## Detailed Implementation

### Prerequisites
- Install the **Cisco Catalyst Add-on for Splunk** (Splunkbase 7538) on a search head or heavy forwarder.
- Configure a Catalyst Center account in the TA with a service account that has **NETWORK-ADMIN-ROLE** or **SUPER-ADMIN-ROLE**.
- Catalyst Center **2.3.5+** recommended for consistent Assurance issue data.
- For app install paths and modular input layout, see `docs/implementation-guide.md`.

### Step 1 — Configure data collection
- **TA input name:** `issue`; **sourcetype:** `cisco:dnac:issue`; **index:** `catalyst`.
- **API polled:** `GET /dna/intent/api/v1/issues` (Intent API, paginated).
- **Default interval:** 900s (15 minutes). Shorter intervals improve detection latency but increase API load.
- **Volume:** ~1 event per active issue per poll. Busy networks with many open issues will generate more events.
- **Key fields to validate:** `priority` (P1/P2/P3/P4), `category` (e.g. Onboarding, Connected, Availability), `name` (issue title), `status`, `deviceName`.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:issue"
| stats count by priority, category, name | sort -priority -count
```

#### Understanding this SPL:
- **`stats count by priority, category, name`**: Aggregates issue events by their priority level, category, and specific issue name to produce a frequency table.
- **`sort -priority -count`**: Surfaces the highest-priority, most-frequent issues first for triage.
- **Tuning:** filter by `priority="P1" OR priority="P2"` for critical-only alerting; add `by deviceName` to identify which devices generate the most issues.

### Step 3 — Validate
- **Vendor UI parity:** open **Catalyst Center > Assurance > Issues** for the same time window and compare the issue count by priority. Minor count differences are normal due to poll timing.
- Pick two specific issues visible in the Catalyst Center UI and verify they appear in the Splunk results with matching priority and category.
- Run `| timechart count` over 24 hours to verify a steady event stream with no silent gaps.

### Step 4 — Operationalize
- **Dashboard:** Use as a top-level summary panel on a Network Management dashboard. Pair with single-value panels for open P1 and P2 counts.
- **Alert:** Schedule hourly; trigger on `priority="P1" | stats count | where count > 0` for immediate NOC notification.
- **Drilldown:** Link from issue rows to **Catalyst Center > Assurance > Issues** for the specific issue detail.

### Step 5 — Troubleshooting
- **No `cisco:dnac:issue` events:** if data is not arriving, check that the `issue` input is enabled in the TA, verify the Catalyst Center account credentials, and look for HTTP errors in `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"`.
- **Fewer issues than the Catalyst Center UI shows:** confirm the service account has the correct RBAC role and virtual domain scope. The API returns only active issues by default.
- **Stale data or timeout errors:** check NTP synchronization between the collection host and Catalyst Center; verify the poll interval has not been inadvertently set too long.


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
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
