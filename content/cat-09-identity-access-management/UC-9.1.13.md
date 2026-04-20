---
id: "9.1.13"
title: "AD Certificate Services Certificate Expiration"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.1.13 · AD Certificate Services Certificate Expiration

## Description

Internal CA-issued certificates approaching expiry; missed renewals cause outages.

## Value

Internal CA-issued certificates approaching expiry; missed renewals cause outages.

## Implementation

Run `certutil -view -restrict "Disposition=20"` (issued certs) on CA servers via scripted input daily. Parse output and compute days until expiry. Alert on certificates expiring within 30 days. Include Certificate Services event logs (Event ID 100–107) for issuance/renewal events. Maintain lookup of critical certs (e.g., LDAPS, VPN) for prioritized alerts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, custom scripted input (certutil).
• Ensure the following data sources are available: ADCS issued certificates database (certutil -view), Certificate Services logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run `certutil -view -restrict "Disposition=20"` (issued certs) on CA servers via scripted input daily. Parse output and compute days until expiry. Alert on certificates expiring within 30 days. Include Certificate Services event logs (Event ID 100–107) for issuance/renewal events. Maintain lookup of critical certs (e.g., LDAPS, VPN) for prioritized alerts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=adcs sourcetype="adcs:cert_inventory"
| eval days_to_expiry=round((expiry_epoch-now())/86400)
| where days_to_expiry < 30 AND days_to_expiry > 0
| table _time, subject, issuer, days_to_expiry, serial_number
| sort days_to_expiry
```

Understanding this SPL

**AD Certificate Services Certificate Expiration** — Internal CA-issued certificates approaching expiry; missed renewals cause outages.

Documented **Data sources**: ADCS issued certificates database (certutil -view), Certificate Services logs. **App/TA** (typical add-on context): `Splunk_TA_windows`, custom scripted input (certutil). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: adcs; **sourcetype**: adcs:cert_inventory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=adcs, sourcetype="adcs:cert_inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_to_expiry** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_to_expiry < 30 AND days_to_expiry > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **AD Certificate Services Certificate Expiration**): table _time, subject, issuer, days_to_expiry, serial_number
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (expiring certificates), Single value (certs expiring in 30 days), Gauge (days until next expiry), Bar chart (expiry by issuer).

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
index=adcs sourcetype="adcs:cert_inventory"
| eval days_to_expiry=round((expiry_epoch-now())/86400)
| where days_to_expiry < 30 AND days_to_expiry > 0
| table _time, subject, issuer, days_to_expiry, serial_number
| sort days_to_expiry
```

## Visualization

Table (expiring certificates), Single value (certs expiring in 30 days), Gauge (days until next expiry), Bar chart (expiry by issuer).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
