---
id: "3.4.8"
title: "Registry TLS and Certificate Expiration"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.4.8 · Registry TLS and Certificate Expiration

## Description

Expired or expiring registry certificates break all pulls and pushes. Proactive monitoring prevents pipeline and runtime failures.

## Value

Expired or expiring registry certificates break all pulls and pushes. Proactive monitoring prevents pipeline and runtime failures.

## Implementation

Script that connects to registry HTTPS and extracts cert expiry (e.g. `openssl s_client -connect registry:443 -servername registry`). Ingest daily. Alert when expiry is within 30 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (openssl s_client, registry health API).
• Ensure the following data sources are available: TLS certificate from registry endpoint.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Script that connects to registry HTTPS and extracts cert expiry (e.g. `openssl s_client -connect registry:443 -servername registry`). Ingest daily. Alert when expiry is within 30 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="registry:tls"
| eval days_left=round((expiry_time-now())/86400, 0)
| where days_left < 30
| table registry_host expiry_time days_left subject
| sort days_left
```

Understanding this SPL

**Registry TLS and Certificate Expiration** — Expired or expiring registry certificates break all pulls and pushes. Proactive monitoring prevents pipeline and runtime failures.

Documented **Data sources**: TLS certificate from registry endpoint. **App/TA** (typical add-on context): Custom scripted input (openssl s_client, registry health API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: registry:tls. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="registry:tls". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_left < 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Registry TLS and Certificate Expiration**): table registry_host expiry_time days_left subject
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (registry, expiry, days left), Single value (soonest expiry), Gauge (days remaining).

## SPL

```spl
index=containers sourcetype="registry:tls"
| eval days_left=round((expiry_time-now())/86400, 0)
| where days_left < 30
| table registry_host expiry_time days_left subject
| sort days_left
```

## Visualization

Table (registry, expiry, days left), Single value (soonest expiry), Gauge (days remaining).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
