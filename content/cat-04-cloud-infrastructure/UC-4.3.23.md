---
id: "4.3.23"
title: "VPC Service Controls Perimeter Violations"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.3.23 · VPC Service Controls Perimeter Violations

## Description

VPC Service Controls enforce network perimeter. Violations indicate data exfiltration attempts or misconfigured access. Critical for data perimeter security.

## Value

VPC Service Controls enforce network perimeter. Violations indicate data exfiltration attempts or misconfigured access. Critical for data perimeter security.

## Implementation

Enable VPC SC violation logging. Forward to Pub/Sub and Splunk. Alert on every violation. Correlate with principal, source IP, and resource. Use for perimeter tuning and incident response.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Access Context Manager / VPC SC audit logs (perimeter violation events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable VPC SC violation logging. Forward to Pub/Sub and Splunk. Alert on every violation. Correlate with principal, source IP, and resource. Use for perimeter tuning and incident response.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="accesscontextmanager.googleapis.com"
| search "violation" OR "perimeter"
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.requestMetadata.callerIp resource
| sort -_time
```

Understanding this SPL

**VPC Service Controls Perimeter Violations** — VPC Service Controls enforce network perimeter. Violations indicate data exfiltration attempts or misconfigured access. Critical for data perimeter security.

Documented **Data sources**: Access Context Manager / VPC SC audit logs (perimeter violation events). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **VPC Service Controls Perimeter Violations**): table _time protoPayload.authenticationInfo.principalEmail protoPayload.requestMetadata.callerIp resource
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (principal, resource, violation), Timeline (violations), Map (source IPs).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="accesscontextmanager.googleapis.com"
| search "violation" OR "perimeter"
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.requestMetadata.callerIp resource
| sort -_time
```

## Visualization

Table (principal, resource, violation), Timeline (violations), Map (source IPs).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
