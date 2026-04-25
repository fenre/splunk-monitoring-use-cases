<!-- AUTO-GENERATED from UC-8.1.5.json — DO NOT EDIT -->

---
id: "8.1.5"
title: "SSL Certificate Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.5 · SSL Certificate Monitoring

## Description

Expired SSL certificates cause complete service outage and browser security warnings. Proactive monitoring prevents this entirely avoidable failure.

## Value

Expired SSL certificates cause complete service outage and browser security warnings. Proactive monitoring prevents this entirely avoidable failure.

## Implementation

Deploy scripted input that runs `openssl s_client` against all HTTPS endpoints daily. Parse certificate details (CN, SAN, expiry, issuer). Alert at 30, 14, and 7 days before expiry. Maintain endpoint inventory via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Scripted input (openssl s_client), custom certificate check.
• Ensure the following data sources are available: Certificate check scripted input, web server config parsing.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy scripted input that runs `openssl s_client` against all HTTPS endpoints daily. Parse certificate details (CN, SAN, expiry, issuer). Alert at 30, 14, and 7 days before expiry. Maintain endpoint inventory via lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=certificates sourcetype="cert_check"
| eval days_until_expiry=round((cert_expiry_epoch-now())/86400)
| where days_until_expiry < 30
| table host, port, cn, issuer, days_until_expiry
| sort days_until_expiry
```

Understanding this SPL

**SSL Certificate Monitoring** — Expired SSL certificates cause complete service outage and browser security warnings. Proactive monitoring prevents this entirely avoidable failure.

Documented **Data sources**: Certificate check scripted input, web server config parsing. **App/TA** (typical add-on context): Scripted input (openssl s_client), custom certificate check. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: certificates; **sourcetype**: cert_check. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=certificates, sourcetype="cert_check". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_until_expiry** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_until_expiry < 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **SSL Certificate Monitoring**): table host, port, cn, issuer, days_until_expiry
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (certificates with expiry dates), Single value (certs expiring within 30d), Status grid (endpoint × cert status).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=certificates sourcetype="cert_check"
| eval days_until_expiry=round((cert_expiry_epoch-now())/86400)
| where days_until_expiry < 30
| table host, port, cn, issuer, days_until_expiry
| sort days_until_expiry
```

## Visualization

Table (certificates with expiry dates), Single value (certs expiring within 30d), Status grid (endpoint × cert status).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
