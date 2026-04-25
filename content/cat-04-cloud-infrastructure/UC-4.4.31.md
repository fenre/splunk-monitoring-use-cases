<!-- AUTO-GENERATED from UC-4.4.31.json — DO NOT EDIT -->

---
id: "4.4.31"
title: "Multi-Cloud Certificate Expiry Tracking"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.4.31 · Multi-Cloud Certificate Expiry Tracking

## Description

Expired certs break TLS for APIs and VPNs across regions; a unified expiry calendar prevents outages.

## Value

Expired certs break TLS for APIs and VPNs across regions; a unified expiry calendar prevents outages.

## Implementation

Nightly inventory jobs push cert metadata via HEC. Escalate at 30, 14, and 7 days. Include private CAs and cloud-managed certs for load balancers and API gateways.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: ACM/Key Vault/Certificate Manager exports, optional certstream.
• Ensure the following data sources are available: `sourcetype=aws:acm:inventory`, `sourcetype=mscs:azure:metrics` / cert inventory, `sourcetype=google:gcp:pubsub:message` (certificatemanager).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Nightly inventory jobs push cert metadata via HEC. Escalate at 30, 14, and 7 days. Include private CAs and cloud-managed certs for load balancers and API gateways.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud (sourcetype="aws:acm:inventory" OR sourcetype="azure:keyvault:certs" OR sourcetype="google:gcp:pubsub:message")
| eval not_after_epoch=coalesce(strptime(expiry, "%Y-%m-%dT%H:%M:%SZ"), strptime(expiry, "%Y-%m-%dT%H:%M:%S%z"), strptime(notAfter, "%Y-%m-%dT%H:%M:%S"))
| eval days_left=round((not_after_epoch-now())/86400,0)
| eval provider=case(sourcetype="aws:acm:inventory","aws", sourcetype="azure:keyvault:certs","azure", sourcetype="google:gcp:pubsub:message","gcp",1=1,"unknown")
| where days_left < 30 AND days_left >= 0
| table cert_name, provider, expiry, days_left
| sort days_left
```

Understanding this SPL

**Multi-Cloud Certificate Expiry Tracking** — Expired certs break TLS for APIs and VPNs across regions; a unified expiry calendar prevents outages.

Documented **Data sources**: `sourcetype=aws:acm:inventory`, `sourcetype=mscs:azure:metrics` / cert inventory, `sourcetype=google:gcp:pubsub:message` (certificatemanager). **App/TA** (typical add-on context): ACM/Key Vault/Certificate Manager exports, optional certstream. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: aws:acm:inventory, azure:keyvault:certs, google:gcp:pubsub:message. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="aws:acm:inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **not_after_epoch** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **provider** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_left < 30 AND days_left >= 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Multi-Cloud Certificate Expiry Tracking**): table cert_name, provider, expiry, days_left
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cert, provider, days left), Timeline (expiry dates), Single value (next expiry).

## SPL

```spl
index=cloud (sourcetype="aws:acm:inventory" OR sourcetype="azure:keyvault:certs" OR sourcetype="google:gcp:pubsub:message")
| eval not_after_epoch=coalesce(strptime(expiry, "%Y-%m-%dT%H:%M:%SZ"), strptime(expiry, "%Y-%m-%dT%H:%M:%S%z"), strptime(notAfter, "%Y-%m-%dT%H:%M:%S"))
| eval days_left=round((not_after_epoch-now())/86400,0)
| eval provider=case(sourcetype="aws:acm:inventory","aws", sourcetype="azure:keyvault:certs","azure", sourcetype="google:gcp:pubsub:message","gcp",1=1,"unknown")
| where days_left < 30 AND days_left >= 0
| table cert_name, provider, expiry, days_left
| sort days_left
```

## Visualization

Table (cert, provider, days left), Timeline (expiry dates), Single value (next expiry).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
