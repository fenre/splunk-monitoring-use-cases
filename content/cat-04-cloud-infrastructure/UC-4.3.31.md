---
id: "4.3.31"
title: "Cloud KMS Key Rotation Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.3.31 · Cloud KMS Key Rotation Compliance

## Description

Crypto policy often mandates rotation; tracking next rotation time avoids audit findings and forced emergency rotations.

## Value

Crypto policy often mandates rotation; tracking next rotation time avoids audit findings and forced emergency rotations.

## Implementation

Nightly sync key metadata including rotation period and next rotation. Alert when rotation overdue or manual rotation gaps detected. Include CMEK keys for BigQuery and GCS.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message` (cloudkms.googleapis.com audit), Asset Inventory key metadata.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Nightly sync key metadata including rotation period and next rotation. Alert when rotation overdue or manual rotation gaps detected. Include CMEK keys for BigQuery and GCS.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="cloudkms.googleapis.com" protoPayload.methodName="*CryptoKey*"
| stats latest(protoPayload.request.nextRotationTime) as next_rot by resource.labels.key_ring_id, resource.labels.crypto_key_id
| eval days=round((strptime(next_rot,"%Y-%m-%dT%H:%M:%SZ")-now())/86400,0)
| where days < 30 OR isnull(days)
```

Understanding this SPL

**Cloud KMS Key Rotation Compliance** — Crypto policy often mandates rotation; tracking next rotation time avoids audit findings and forced emergency rotations.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` (cloudkms.googleapis.com audit), Asset Inventory key metadata. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.key_ring_id, resource.labels.crypto_key_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **days** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days < 30 OR isnull(days)` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (key, days to rotation), Timeline (rotation events), Single value (keys out of compliance).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="cloudkms.googleapis.com" protoPayload.methodName="*CryptoKey*"
| stats latest(protoPayload.request.nextRotationTime) as next_rot by resource.labels.key_ring_id, resource.labels.crypto_key_id
| eval days=round((strptime(next_rot,"%Y-%m-%dT%H:%M:%SZ")-now())/86400,0)
| where days < 30 OR isnull(days)
```

## Visualization

Table (key, days to rotation), Timeline (rotation events), Single value (keys out of compliance).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
