<!-- AUTO-GENERATED from UC-5.4.22.json — DO NOT EDIT -->

---
id: "5.4.22"
title: "Splash Page Engagement and Redirection Analytics (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.22 · Splash Page Engagement and Redirection Analytics (Meraki MR)

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch splash page engagement and redirection analytics (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Tracks guest network splash page performance and user acceptance rates for marketing and network access purposes.

## Value

Wireless operations teams monitor Meraki MR per-AP channel utilization levels to detect airtime congestion and non-WiFi interference, guiding channel planning and RF environment optimization.

## Implementation

1. Configure SC4S for MR syslog and enable the Access-point event log. 2. Each splash authentication emits one event per accepted client. 3. duration = the session timeout granted by the splash policy (in seconds); download/upload = the per-client throughput cap. 4. For redirect / dropped / abandoned splash attempts, configure a Meraki Dashboard alert profile on 'splash page redirect failure' and ingest via the Webhook Logs (HEC) input.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR syslog. Splash page authentications appear as type=events with type=splash_auth and structured ip=, duration=, vap=, download=, upload= fields..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MR syslog and enable the Access-point event log. 2. Each splash authentication emits one event per accepted client. 3. duration = the session timeout granted by the splash policy (in seconds); download/upload = the per-client throughput cap. 4. For redirect / dropped / abandoned splash attempts, configure a Meraki Dashboard alert profile on 'splash page redirect failure' and ingest via the Webhook Logs (HEC) input.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events "splash_auth"
    earliest=-7d
| rex "ip='(?<client_ip>[\d\.]+)"
| rex "duration='(?<duration>\d+)'"
| rex "vap='(?<vap_id>\d+)'"
| rex "download='(?<download_bps>\d+)bps'"
| rex "upload='(?<upload_bps>\d+)bps'"
| stats count as auth_count,
        avg(duration) as avg_session_secs,
        sum(eval(download_bps + upload_bps)) as total_bps
         by host, vap_id
| sort - auth_count
```

#### Understanding this SPL

**Splash Page Engagement and Redirection Analytics (Meraki MR)** — Wireless operations teams monitor Meraki MR per-AP channel utilization levels to detect airtime congestion and non-WiFi interference, guiding channel planning and RF environment optimization.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR syslog. Splash page authentications appear as type=events with type=splash_auth and structured ip=, duration=, vap=, download=, upload= fields. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host, vap_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart of acceptance rates; funnel chart of splash interactions; time-series trending.

## SPL

```spl
index=meraki sourcetype="meraki" type=events "splash_auth"
    earliest=-7d
| rex "ip='(?<client_ip>[\d\.]+)"
| rex "duration='(?<duration>\d+)'"
| rex "vap='(?<vap_id>\d+)'"
| rex "download='(?<download_bps>\d+)bps'"
| rex "upload='(?<upload_bps>\d+)bps'"
| stats count as auth_count,
        avg(duration) as avg_session_secs,
        sum(eval(download_bps + upload_bps)) as total_bps
         by host, vap_id
| sort - auth_count
```

## Visualization

Pie chart of acceptance rates; funnel chart of splash interactions; time-series trending.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
