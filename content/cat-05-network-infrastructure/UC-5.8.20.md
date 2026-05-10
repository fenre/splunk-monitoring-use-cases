<!-- AUTO-GENERATED from UC-5.8.20.json — DO NOT EDIT -->

---
id: "5.8.20"
title: "Configuration Change Window Compliance (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.20 · Configuration Change Window Compliance (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We help you show when changes were made in approved windows versus odd hours, so maintenance stays under control.*

---

## Description

Ensures configuration changes only occur within approved maintenance windows.

## Value

Network operations teams enforce configuration change window compliance across Meraki networks, detecting out-of-window changes, flagging sensitive modifications, and generating governance compliance reports.

## Implementation

1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. The 'change window' is a policy decision — adjust the eval threshold to your maintenance window definition (here: 22:00–06:00 local). 3. _time on each audit event is the change timestamp. 4. Pair with adminName to identify out-of-window admins; route to your change-advisory-board ticketing system.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit). Configuration changes are NOT in Meraki syslog — they are only available via the Audit input which polls GET /organizations/{orgId}/configurationChanges..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. The 'change window' is a policy decision — adjust the eval threshold to your maintenance window definition (here: 22:00–06:00 local). 3. _time on each audit event is the change timestamp. 4. Pair with adminName to identify out-of-window admins; route to your change-advisory-board ticketing system.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:audit" earliest=-30d
| eval change_hour = strftime(_time, "%H")
| eval window_compliant = if(change_hour>=22 OR change_hour<6, "Yes", "No")
| stats count as change_count,
        values(adminName) as admins,
        values(page) as pages
         by window_compliant, change_hour
| where window_compliant="No"
| sort change_hour
```

#### Understanding this SPL

**Configuration Change Window Compliance (Meraki)** — Network operations teams enforce configuration change window compliance across Meraki networks, detecting out-of-window changes, flagging sensitive modifications, and generating governance compliance reports.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit). Configuration changes are NOT in Meraki syslog — they are only available via the Audit input which polls GET /organizations/{orgId}/configurationChanges. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:audit", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `eval` defines or adjusts **change_hour** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **window_compliant** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by window_compliant, change_hour** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where window_compliant="No"` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Change compliance timeline; out-of-window change alert table.

## SPL

```spl
index=meraki sourcetype="meraki:audit" earliest=-30d
| eval change_hour = strftime(_time, "%H")
| eval window_compliant = if(change_hour>=22 OR change_hour<6, "Yes", "No")
| stats count as change_count,
        values(adminName) as admins,
        values(page) as pages
         by window_compliant, change_hour
| where window_compliant="No"
| sort change_hour
```

## Visualization

Change compliance timeline; out-of-window change alert table.

## Known False Positives

Emergency fixes outside the window are sometimes correct; require change ticket and approver for exceptions, do not only silence the alert.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
