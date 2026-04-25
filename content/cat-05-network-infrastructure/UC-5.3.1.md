<!-- AUTO-GENERATED from UC-5.3.1.json — DO NOT EDIT -->

---
id: "5.3.1"
title: "Pool Member Health Status (F5 BIG-IP)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.1 · Pool Member Health Status (F5 BIG-IP)

## Description

Offline pool members reduce capacity. All members down = complete service outage.

## Value

Offline pool members reduce capacity. All members down = complete service outage.

## Implementation

Forward F5 syslog (LTM log level). Install TA. Alert when pool members go down. Critical alert when all members in a pool offline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip`, syslog.
• Ensure the following data sources are available: `sourcetype=f5:bigip:syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward F5 syslog (LTM log level). Install TA. Alert when pool members go down. Critical alert when all members in a pool offline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:syslog" ("pool member" AND ("down" OR "up" OR "offline"))
| rex "Pool (?<pool>\S+) member (?<member>\S+) monitor status (?<status>\w+)"
| table _time host pool member status | sort -_time
```

Understanding this SPL

**Pool Member Health Status (F5 BIG-IP)** — Offline pool members reduce capacity. All members down = complete service outage.

Documented **Data sources**: `sourcetype=f5:bigip:syslog`. **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Pool Member Health Status (F5 BIG-IP)**): table _time host pool member status
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Open the F5 Configuration utility or tmsh, select the same pools, members, and health monitors, and compare up or down state and recent events with Splunk for the same time range.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (green/red per member), Table, Timeline.

## SPL

```spl
index=network sourcetype="f5:bigip:syslog" ("pool member" AND ("down" OR "up" OR "offline"))
| rex "Pool (?<pool>\S+) member (?<member>\S+) monitor status (?<status>\w+)"
| table _time host pool member status | sort -_time
```

## Visualization

Status grid (green/red per member), Table, Timeline.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
