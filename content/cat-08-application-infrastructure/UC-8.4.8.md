<!-- AUTO-GENERATED from UC-8.4.8.json — DO NOT EDIT -->

---
id: "8.4.8"
title: "mTLS Certificate Expiration"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.4.8 · mTLS Certificate Expiration

## Description

Expired mTLS certificates break service-to-service communication, causing complete mesh failures. Proactive monitoring is essential.

## Value

Expired mTLS certificates break service-to-service communication, causing complete mesh failures. Proactive monitoring is essential.

## Implementation

Monitor Istio/Linkerd certificate lifetimes. For auto-rotated certs, verify rotation is working by tracking cert age. Alert when certs approach expiry or rotation fails. Monitor CA health (Citadel, cert-manager).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Service mesh metrics, scripted input.
• Ensure the following data sources are available: Istio/Linkerd certificate metadata, `istioctl proxy-config` output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Istio/Linkerd certificate lifetimes. For auto-rotated certs, verify rotation is working by tracking cert age. Alert when certs approach expiry or rotation fails. Monitor CA health (Citadel, cert-manager).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=mesh sourcetype="istio:cert_status"
| eval days_until_expiry=round((cert_expiry_epoch-now())/86400)
| where days_until_expiry < 7
| table service, namespace, days_until_expiry, issuer
| sort days_until_expiry
```

Understanding this SPL

**mTLS Certificate Expiration** — Expired mTLS certificates break service-to-service communication, causing complete mesh failures. Proactive monitoring is essential.

Documented **Data sources**: Istio/Linkerd certificate metadata, `istioctl proxy-config` output. **App/TA** (typical add-on context): Service mesh metrics, scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: mesh; **sourcetype**: istio:cert_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=mesh, sourcetype="istio:cert_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_until_expiry** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_until_expiry < 7` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **mTLS Certificate Expiration**): table service, namespace, days_until_expiry, issuer
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.



Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (certs with expiry), Single value (certs expiring within 7d), Timeline (cert rotation events).

## SPL

```spl
index=mesh sourcetype="istio:cert_status"
| eval days_until_expiry=round((cert_expiry_epoch-now())/86400)
| where days_until_expiry < 7
| table service, namespace, days_until_expiry, issuer
| sort days_until_expiry
```

## Visualization

Table (certs with expiry), Single value (certs expiring within 7d), Timeline (cert rotation events).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
