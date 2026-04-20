---
id: "3.1.14"
title: "Docker Network Overlay Issues"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.14 · Docker Network Overlay Issues

## Description

Overlay plugins (VXLAN, weave, custom bridges) failures cause intermittent connectivity between containers on different hosts.

## Value

Overlay plugins (VXLAN, weave, custom bridges) failures cause intermittent connectivity between containers on different hosts.

## Implementation

Forward daemon logs with network driver context. Pattern-match overlay create/delete errors, IPAM failures, and iptables sync issues. Correlate multi-host with timestamps.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Docker daemon logs, syslog.
• Ensure the following data sources are available: `sourcetype=docker:daemon`, `sourcetype=syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward daemon logs with network driver context. Pattern-match overlay create/delete errors, IPAM failures, and iptables sync issues. Correlate multi-host with timestamps.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog (docker OR "br-" OR "vxlan")
| search fail OR error OR unreachable
| stats count by host, _raw
```

Understanding this SPL

**Docker Network Overlay Issues** — Overlay plugins (VXLAN, weave, custom bridges) failures cause intermittent connectivity between containers on different hosts.

Documented **Data sources**: `sourcetype=docker:daemon`, `sourcetype=syslog`. **App/TA** (typical add-on context): Docker daemon logs, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by host, _raw** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, error signature, count), Timeline, Bar chart by error type.

## SPL

```spl
index=os sourcetype=syslog (docker OR "br-" OR "vxlan")
| search fail OR error OR unreachable
| stats count by host, _raw
```

## Visualization

Table (host, error signature, count), Timeline, Bar chart by error type.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
