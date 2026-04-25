<!-- AUTO-GENERATED from UC-8.1.14.json — DO NOT EDIT -->

---
id: "8.1.14"
title: "SSL Certificate Expiry Countdown"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.14 · SSL Certificate Expiry Countdown

## Description

Days-to-expiry dashboard for all TLS endpoints monitored by cert checks. Complements UC-8.1.5 with trend and earliest-expiry focus.

## Value

Days-to-expiry dashboard for all TLS endpoints monitored by cert checks. Complements UC-8.1.5 with trend and earliest-expiry focus.

## Implementation

Daily collection. Alert tiers at 45/30/14/7 days. Include chain validation failures as severity 1.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Scripted cert check, `openssl` input.
• Ensure the following data sources are available: `cert_check` with `cert_expiry_epoch`, `cn`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Daily collection. Alert tiers at 45/30/14/7 days. Include chain validation failures as severity 1.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=certificates sourcetype="cert_check"
| eval days_left=round((cert_expiry_epoch-now())/86400,0)
| stats min(days_left) as soonest by host, port
| where soonest < 45
| sort soonest
```

Understanding this SPL

**SSL Certificate Expiry Countdown** — Days-to-expiry dashboard for all TLS endpoints monitored by cert checks. Complements UC-8.1.5 with trend and earliest-expiry focus.

Documented **Data sources**: `cert_check` with `cert_expiry_epoch`, `cn`. **App/TA** (typical add-on context): Scripted cert check, `openssl` input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: certificates; **sourcetype**: cert_check. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=certificates, sourcetype="cert_check". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, port** so each row reflects one combination of those dimensions.
• Filters the current rows with `where soonest < 45` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, port, days_left), Single value (minimum days_left fleet-wide), Column chart (certs by expiry bucket).

## SPL

```spl
index=certificates sourcetype="cert_check"
| eval days_left=round((cert_expiry_epoch-now())/86400,0)
| stats min(days_left) as soonest by host, port
| where soonest < 45
| sort soonest
```

## Visualization

Table (host, port, days_left), Single value (minimum days_left fleet-wide), Column chart (certs by expiry bucket).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
