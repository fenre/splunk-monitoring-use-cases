<!-- AUTO-GENERATED from UC-9.4.2.json — DO NOT EDIT -->

---
id: "9.4.2"
title: "Password Checkout Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.2 · Password Checkout Tracking

## Description

Unusual checkout patterns may indicate misuse. Tracking ensures accountability and supports investigations.

## Value

Unusual checkout patterns may indicate misuse. Tracking ensures accountability and supports investigations.

## Implementation

Track password checkout and checkin events. Calculate checkout duration. Alert on checkouts exceeding policy limits (e.g., >4 hours). Flag accounts checked out but never checked in (hoarding). Report on checkout frequency per user.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_cyberark.
• Ensure the following data sources are available: PAM vault logs (password retrieve/checkin events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track password checkout and checkin events. Calculate checkout duration. Alert on checkouts exceeding policy limits (e.g., >4 hours). Flag accounts checked out but never checked in (hoarding). Report on checkout frequency per user.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:vault"
| search action="Retrieve" OR action="Checkin"
| transaction user, account maxspan=8h
| eval checkout_duration_hr=duration/3600
| where checkout_duration_hr > 4
| table user, account, target, checkout_duration_hr
```

Understanding this SPL

**Password Checkout Tracking** — Unusual checkout patterns may indicate misuse. Tracking ensures accountability and supports investigations.

Documented **Data sources**: PAM vault logs (password retrieve/checkin events). **App/TA** (typical add-on context): Splunk_TA_cyberark. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:vault. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:vault". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Groups related events into transactions — prefer `maxspan`/`maxpause`/`maxevents` for bounded memory.
• `eval` defines or adjusts **checkout_duration_hr** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where checkout_duration_hr > 4` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Password Checkout Tracking**): table user, account, target, checkout_duration_hr


Step 3 — Validate
Compare with CyberArk PrivateArk/Password Vault Web Access (or BeyondTrust / vendor console) for the same sessions, vault activity, and alerts.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (active checkouts), Bar chart (checkout duration by user), Line chart (checkout frequency trend).

## SPL

```spl
index=pam sourcetype="cyberark:vault"
| search action="Retrieve" OR action="Checkin"
| transaction user, account maxspan=8h
| eval checkout_duration_hr=duration/3600
| where checkout_duration_hr > 4
| table user, account, target, checkout_duration_hr
```

## Visualization

Table (active checkouts), Bar chart (checkout duration by user), Line chart (checkout frequency trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
