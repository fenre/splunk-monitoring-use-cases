<!-- AUTO-GENERATED from UC-5.4.8.json — DO NOT EDIT -->

---
id: "5.4.8"
title: "RADIUS Authentication Failures"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.8 · RADIUS Authentication Failures

## Description

Mass RADIUS failures prevent wireless users from connecting. Distinguishing between user errors and server issues drives faster resolution.

## Value

Mass RADIUS failures prevent wireless users from connecting. Distinguishing between user errors and server issues drives faster resolution.

## Implementation

Forward ISE/RADIUS logs to Splunk. Alert when failure rate exceeds 20% of attempts. Distinguish between bad credentials, expired certificates, and server timeouts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cisco WLC syslog, `Splunk_TA_cisco-ise`.
• Ensure the following data sources are available: `sourcetype=cisco:wlc`, `sourcetype=cisco:ise:syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward ISE/RADIUS logs to Splunk. Alert when failure rate exceeds 20% of attempts. Distinguish between bad credentials, expired certificates, and server timeouts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ise:syslog" "Authentication failed"
| rex "UserName=(?<username>\S+).*?FailureReason=(?<reason>[^;]+)"
| stats count by reason, username | sort -count
| head 20
```

Understanding this SPL

**RADIUS Authentication Failures** — Mass RADIUS failures prevent wireless users from connecting. Distinguishing between user errors and server issues drives faster resolution.

Documented **Data sources**: `sourcetype=cisco:wlc`, `sourcetype=cisco:ise:syslog`. **App/TA** (typical add-on context): Cisco WLC syslog, `Splunk_TA_cisco-ise`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ise:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ise:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by reason, username** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.



Step 3 — Validate
In Cisco ISE (Operations > RADIUS Live Log or authentication reports), compare pass/fail counts and usernames to the Splunk search for the same time range. Spot-check a few failure reasons against ISE.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (failure reasons), Table (username, reason, count), Timechart (failure rate).

## SPL

```spl
index=network sourcetype="cisco:ise:syslog" "Authentication failed"
| rex "UserName=(?<username>\S+).*?FailureReason=(?<reason>[^;]+)"
| stats count by reason, username | sort -count
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Bar chart (failure reasons), Table (username, reason, count), Timechart (failure rate).

## References

- [Splunk_TA_cisco-ise](https://splunkbase.splunk.com/app/1915)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
