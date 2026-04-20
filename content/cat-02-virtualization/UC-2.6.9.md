---
id: "2.6.9"
title: "Citrix Profile Management Load Time"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.9 · Citrix Profile Management Load Time

## Description

Citrix User Profile Management (UPM) loads user profiles at session logon — including registry hives, application settings, and redirected folders. Large or corrupted profiles cause logon delays that can extend login times by minutes. Profile streaming can significantly reduce load times (from 54 seconds to 20 seconds in Citrix tests), but only if properly configured. Monitoring profile load times identifies users with bloated profiles and validates that profile optimization features are effective.

## Value

Citrix User Profile Management (UPM) loads user profiles at session logon — including registry hives, application settings, and redirected folders. Large or corrupted profiles cause logon delays that can extend login times by minutes. Profile streaming can significantly reduce load times (from 54 seconds to 20 seconds in Citrix tests), but only if properly configured. Monitoring profile load times identifies users with bloated profiles and validates that profile optimization features are effective.

## Implementation

Citrix Profile Management logs to `%SystemRoot%\System32\LogFiles\UserProfileManager` on each VDA. Configure centralized log storage via UPM policy (store logs on a network share). Forward these logs to Splunk via Universal Forwarder. Parse for profile load/unload timing events. Track profile size growth per user over time. Alert on: p95 profile load time exceeding 15 seconds, individual profiles exceeding 500 MB, or UPM errors indicating profile corruption ("Error while processing profile" events). Validate that profile streaming is enabled and effective by comparing load times with/without streaming.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder on VDAs, Citrix UPM log collection.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:upm:log"` fields `user`, `profile_load_time_sec`, `profile_size_mb`, `streaming_enabled`, `error_message`, `vda_host`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Citrix Profile Management logs to `%SystemRoot%\System32\LogFiles\UserProfileManager` on each VDA. Configure centralized log storage via UPM policy (store logs on a network share). Forward these logs to Splunk via Universal Forwarder. Parse for profile load/unload timing events. Track profile size growth per user over time. Alert on: p95 profile load time exceeding 15 seconds, individual profiles exceeding 500 MB, or UPM errors indicating profile corruption ("Error while processing profile" even…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:upm:log" event_type="ProfileLoad"
| bin _time span=1h
| stats avg(profile_load_time_sec) as avg_load, perc95(profile_load_time_sec) as p95_load, avg(profile_size_mb) as avg_size, count as loads by vda_host, _time
| where p95_load > 15
| table _time, vda_host, loads, avg_load, p95_load, avg_size
```

Understanding this SPL

**Citrix Profile Management Load Time** — Citrix User Profile Management (UPM) loads user profiles at session logon — including registry hives, application settings, and redirected folders. Large or corrupted profiles cause logon delays that can extend login times by minutes. Profile streaming can significantly reduce load times (from 54 seconds to 20 seconds in Citrix tests), but only if properly configured. Monitoring profile load times identifies users with bloated profiles and validates that profile…

Documented **Data sources**: `index=xd` `sourcetype="citrix:upm:log"` fields `user`, `profile_load_time_sec`, `profile_size_mb`, `streaming_enabled`, `error_message`, `vda_host`. **App/TA** (typical add-on context): Splunk Universal Forwarder on VDAs, Citrix UPM log collection. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:upm:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:upm:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by vda_host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where p95_load > 15` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Profile Management Load Time**): table _time, vda_host, loads, avg_load, p95_load, avg_size


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (profile load time trending), Bar chart (top users by profile size), Table (slow profile loads with user details).

## SPL

```spl
index=xd sourcetype="citrix:upm:log" event_type="ProfileLoad"
| bin _time span=1h
| stats avg(profile_load_time_sec) as avg_load, perc95(profile_load_time_sec) as p95_load, avg(profile_size_mb) as avg_size, count as loads by vda_host, _time
| where p95_load > 15
| table _time, vda_host, loads, avg_load, p95_load, avg_size
```

## Visualization

Line chart (profile load time trending), Bar chart (top users by profile size), Table (slow profile loads with user details).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
