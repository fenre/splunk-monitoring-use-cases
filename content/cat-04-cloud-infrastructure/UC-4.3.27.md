---
id: "4.3.27"
title: "Cloud Armor WAF Events"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.27 · Cloud Armor WAF Events

## Description

WAF blocks indicate attack traffic or misrules; separating noise from targeted campaigns protects edge apps behind HTTPS load balancers.

## Value

WAF blocks indicate attack traffic or misrules; separating noise from targeted campaigns protects edge apps behind HTTPS load balancers.

## Implementation

Enable logging on security policies and sink to Pub/Sub. Parse rule ID and preview vs enforce. Alert on spike vs baseline or new country/ASN concentration. Tune rules to reduce false positives.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: HTTP(S) LB request logs with Cloud Armor, `sourcetype=google:gcp:pubsub:message` (loadbalancing.googleapis.com/requests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable logging on security policies and sink to Pub/Sub. Parse rule ID and preview vs enforce. Alert on spike vs baseline or new country/ASN concentration. Tune rules to reduce false positives.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*requests" httpRequest.status=403
| search enforcedSecurityPolicy OR CLOUD_ARMOR
| stats count by jsonPayload.enforcedSecurityPolicy.name, httpRequest.remoteIp, httpRequest.requestUrl
| sort -count
```

Understanding this SPL

**Cloud Armor WAF Events** — WAF blocks indicate attack traffic or misrules; separating noise from targeted campaigns protects edge apps behind HTTPS load balancers.

Documented **Data sources**: HTTP(S) LB request logs with Cloud Armor, `sourcetype=google:gcp:pubsub:message` (loadbalancing.googleapis.com/requests). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by jsonPayload.enforcedSecurityPolicy.name, httpRequest.remoteIp, httpRequest.requestUrl** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.action, IDS_Attacks.signature, IDS_Attacks.src, IDS_Attacks.dest | sort - count
```

Understanding this CIM / accelerated SPL

**Cloud Armor WAF Events** — WAF blocks indicate attack traffic or misrules; separating noise from targeted campaigns protects edge apps behind HTTPS load balancers.

Documented **Data sources**: HTTP(S) LB request logs with Cloud Armor, `sourcetype=google:gcp:pubsub:message` (loadbalancing.googleapis.com/requests). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Intrusion_Detection.IDS_Attacks` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (rule hits), Map (client IP geo), Timeline (block rate).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*requests" httpRequest.status=403
| search enforcedSecurityPolicy OR CLOUD_ARMOR
| stats count by jsonPayload.enforcedSecurityPolicy.name, httpRequest.remoteIp, httpRequest.requestUrl
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.action, IDS_Attacks.signature, IDS_Attacks.src, IDS_Attacks.dest | sort - count
```

## Visualization

Bar chart (rule hits), Map (client IP geo), Timeline (block rate).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
