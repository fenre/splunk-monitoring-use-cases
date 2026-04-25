<!-- AUTO-GENERATED from UC-8.7.6.json — DO NOT EDIT -->

---
id: "8.7.6"
title: "Squid Policy-Denied Requests Trending"
criticality: "low"
splunkPillar: "IT Operations"
---

# UC-8.7.6 · Squid Policy-Denied Requests Trending

## Description

Daily denied-request volume trending supports acceptable-use reviews and proves policy enforcement continuity.

## Value

Gives compliance teams a simple KPI without ad-hoc log pulls.

## Implementation

Anonymize usernames if required; document retention.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom access log analytics.
• Ensure the following data sources are available: `index=proxy` `sourcetype=squid:access` (`TCP_DENIED`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Adjust span to weekly for small offices.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="squid:access" earliest=-30d
| rex "TCP_(?<cache_result>DENIED)"
| where isnotnull(cache_result)
| timechart span=1d sum(eval(if(cache_result=="DENIED",1,0))) as denied_per_day
```

Understanding this SPL

**Squid Policy-Denied Requests Trending** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=proxy` `sourcetype=squid:access` (`TCP_DENIED`). **App/TA**: Custom access log analytics. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (30-day trend), annotate change windows..

## SPL

```spl
index=proxy sourcetype="squid:access" earliest=-30d
| rex "TCP_(?<cache_result>DENIED)"
| where isnotnull(cache_result)
| timechart span=1d sum(eval(if(cache_result=="DENIED",1,0))) as denied_per_day
```

## Visualization

Line chart (30-day trend), annotate change windows.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Squid Configuration Manual — Access Log](http://www.squid-cache.org/Doc/config/access_log/)
