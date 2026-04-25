<!-- AUTO-GENERATED from UC-5.4.7.json — DO NOT EDIT -->

---
id: "5.4.7"
title: "Wireless Authentication Trends"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.4.7 · Wireless Authentication Trends

## Description

802.1X success/failure rates indicate RADIUS health, certificate issues, or expired credentials.

## Value

802.1X success/failure rates indicate RADIUS health, certificate issues, or expired credentials.

## Implementation

Forward ISE/RADIUS authentication logs. Track success/failure ratio over time. Alert on sustained failure rate increase.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: WLC syslog, RADIUS/ISE logs.
• Ensure the following data sources are available: RADIUS logs, WLC auth events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward ISE/RADIUS authentication logs. Track success/failure ratio over time. Alert on sustained failure rate increase.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ise:syslog" ("Passed" OR "Failed") AND "Wireless"
| eval status=if(match(_raw,"Passed"),"Success","Failed")
| timechart span=1h count by status
```

Understanding this SPL

**Wireless Authentication Trends** — 802.1X success/failure rates indicate RADIUS health, certificate issues, or expired credentials.

Documented **Data sources**: RADIUS logs, WLC auth events. **App/TA** (typical add-on context): WLC syslog, RADIUS/ISE logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ise:syslog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ise:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by status** — ideal for trending and alerting on this use case.



Step 3 — Validate
In Cisco ISE (Operations > RADIUS Live Log or authentication reports), compare pass/fail counts and usernames to the Splunk search for the same time range. Spot-check a few failure reasons against ISE.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar chart (success vs. failure), Line chart, Single value (failure rate %).

## SPL

```spl
index=network sourcetype="cisco:ise:syslog" ("Passed" OR "Failed") AND "Wireless"
| eval status=if(match(_raw,"Passed"),"Success","Failed")
| timechart span=1h count by status
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Stacked bar chart (success vs. failure), Line chart, Single value (failure rate %).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
