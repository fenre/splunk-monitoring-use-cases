<!-- AUTO-GENERATED from UC-2.6.68.json — DO NOT EDIT -->

---
id: "2.6.68"
title: "Citrix Endpoint Management Remote Wipe/Lock Action Tracking"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.6.68 · Citrix Endpoint Management Remote Wipe/Lock Action Tracking

## Description

Remote lock and wipe are the last line when a device is lost or a user leaves under duress. Stalled, failed, or abnormally slow commands can leave data exposed longer than policy allows, while repeated failures may indicate a rooted device or network blocks. CEM can emit the MDM command lifecycle. This use case reports success rate, median latency, and long-tail timeouts by action type, and it feeds security and audit teams a durable trail of who requested each destructive action and whether it completed.

## Value

Remote lock and wipe are the last line when a device is lost or a user leaves under duress. Stalled, failed, or abnormally slow commands can leave data exposed longer than policy allows, while repeated failures may indicate a rooted device or network blocks. CEM can emit the MDM command lifecycle. This use case reports success rate, median latency, and long-tail timeouts by action type, and it feeds security and audit teams a durable trail of who requested each destructive action and whether it completed.

## Implementation

Ensure both the command result stream and a tamper-resistant admin audit of `requester` and business justification (ticket id) are present. Set RTO expectations (for example lock within two minutes on cellular). Page security operations on any `wipe` or `unenroll` that fails or exceeds latency SLO, with device last-seen time for triage. Weekly review of counts versus HR-driven terminations. Retain 13 months in line with HR and privacy counsel. Suppress test-lab device IDs. Never send full device payloads to a shared room without masking sensitive fields.

## Detailed Implementation

Prerequisites
• Legal and HR sign-off on logging requesters; CEM at a build that includes detailed command results; time sync.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deduplicate command retries. Map vendor-specific status strings to the four outcomes above. Hash device identifiers in lower environments.

Step 2 — Create the search and alert
Run a scheduled search every 5 minutes for failures. Route full-text evidence only to a restricted index role.

Step 3 — Validate
In test, send lock and a selective wipe, confirm latency fields. For wipe, use a virtual lab or manufacturer reset workflow only.

Step 4 — Operationalize
Quarterly runbook drill with a paper incident; check that the audit trail is complete for auditors.

## SPL

```spl
index=xd sourcetype="citrix:endpoint:mdm:command" action IN ("wipe","lock","reset","unenroll")
| eval ok=if(match(lower(coalesce(outcome, status, "")), "(completed|acknowledged|success)"), 1, 0)
| eval late=if(tonumber(coalesce(latency_ms, 0))>120000, 1, 0)
| where ok=0 OR late=1
| eval action=upper(action)
| timechart span=1h count by action, outcome
| fillnull value=0
```

## Visualization

Gauge: success rate by action; timeline of long-running commands; table of failed devices with `requester` and `incident_id`.

## References

- [Device security actions (enterprise mobility — Apple/Android context)](https://docs.citrix.com/en-us/citrix-endpoint-management/citrix-endpoint-mdm-mam/endpoint-management-mdm-mam-cio.html)
