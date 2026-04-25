<!-- AUTO-GENERATED from UC-8.3.22.json — DO NOT EDIT -->

---
id: "8.3.22"
title: "Squid TCP_DENIED Policy Denial Spike"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-8.3.22 · Squid TCP_DENIED Policy Denial Spike

## Description

Bursts of `TCP_DENIED` indicate ACL changes, authentication failures, or blocked malware callbacks through the proxy.

## Value

Supports DLP and acceptable-use monitoring for forward proxies.

## Implementation

Ensure usernames or groups appear in logs if available. Join with identity feeds for context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Squid access.log).
• Ensure the following data sources are available: `index=proxy` `sourcetype=squid:access`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tune threshold to enterprise size; add URI filters to ignore health checks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy sourcetype="squid:access"
| rex "TCP_(?<cache_result>DENIED)"
| where isnotnull(cache_result)
| bin _time span=15m
| stats count as denied by _time
| where denied > 100
```

Understanding this SPL

**Squid TCP_DENIED Policy Denial Spike** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=proxy` `sourcetype=squid:access`. **App/TA**: Custom (Squid access.log). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare a sample of `TCP_DENIED` lines with Squid’s `access.log` on the proxy (or a direct `grep` of the same file for that time window) to confirm counts and that parsing matches your format.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Timechart (denied/min), table (top URLs), map of source subnets..

## SPL

```spl
index=proxy sourcetype="squid:access"
| rex "TCP_(?<cache_result>DENIED)"
| where isnotnull(cache_result)
| bin _time span=15m
| stats count as denied by _time
| where denied > 100
```

## Visualization

Timechart (denied/min), table (top URLs), map of source subnets.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Squid Configuration Manual — Access Log](http://www.squid-cache.org/Doc/config/access_log/)
