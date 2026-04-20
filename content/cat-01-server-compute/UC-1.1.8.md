---
id: "1.1.8"
title: "SSH Brute-Force Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.8 · SSH Brute-Force Detection

## Description

Detects active password-guessing attacks against SSH services. Can be early indicator of compromised credentials or targeted intrusion attempts.

## Value

Detects active password-guessing attacks against SSH services. Can be early indicator of compromised credentials or targeted intrusion attempts.

## Implementation

Forward `/var/log/auth.log` (Debian/Ubuntu) or `/var/log/secure` (RHEL/CentOS). Create alert for >10 failed attempts from a single IP in 5 minutes. Consider integrating with a GeoIP lookup for geographic context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Syslog.
• Ensure the following data sources are available: `sourcetype=linux_secure` (`/var/log/auth.log` or `/var/log/secure`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward `/var/log/auth.log` (Debian/Ubuntu) or `/var/log/secure` (RHEL/CentOS). Create alert for >10 failed attempts from a single IP in 5 minutes. Consider integrating with a GeoIP lookup for geographic context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_secure "Failed password"
| rex "from (?<src>\d+\.\d+\.\d+\.\d+)"
| stats count as attempts, dc(user) as users_targeted, values(user) as usernames by src, host
| where attempts > 10
| sort -attempts
| iplocation src
```

Understanding this SPL

**SSH Brute-Force Detection** — Detects active password-guessing attacks against SSH services. Can be early indicator of compromised credentials or targeted intrusion attempts.

Documented **Data sources**: `sourcetype=linux_secure` (`/var/log/auth.log` or `/var/log/secure`). **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_secure. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_secure. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by src, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where attempts > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **SSH Brute-Force Detection**): iplocation src

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

Understanding this CIM / accelerated SPL

**SSH Brute-Force Detection** — Detects active password-guessing attacks against SSH services. Can be early indicator of compromised credentials or targeted intrusion attempts.

Documented **Data sources**: `sourcetype=linux_secure` (`/var/log/auth.log` or `/var/log/secure`). **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of source IPs with attempt counts, Choropleth map (GeoIP), Timechart of brute-force events.

## SPL

```spl
index=os sourcetype=linux_secure "Failed password"
| rex "from (?<src>\d+\.\d+\.\d+\.\d+)"
| stats count as attempts, dc(user) as users_targeted, values(user) as usernames by src, host
| where attempts > 10
| sort -attempts
| iplocation src
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

## Visualization

Table of source IPs with attempt counts, Choropleth map (GeoIP), Timechart of brute-force events.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
