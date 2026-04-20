---
id: "5.3.4"
title: "SSL Certificate Expiry (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.4 · SSL Certificate Expiry (F5 BIG-IP)

## Description

Expired certificates on load balancers cause browser warnings or connection failures. Most preventable outage.

## Value

Expired certificates on load balancers cause browser warnings or connection failures. Most preventable outage.

## Implementation

Scripted input querying iControl REST for certs. Run daily. Alert at 90/60/30/7 day thresholds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip`, custom scripted input.
• Ensure the following data sources are available: iControl REST API (`/mgmt/tm/sys/crypto/cert`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input querying iControl REST for certs. Run daily. Alert at 90/60/30/7 day thresholds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:certificate_inventory"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<90
| sort days_left | table host cert_name days_left expiry_date
```

Understanding this SPL

**SSL Certificate Expiry (F5 BIG-IP)** — Expired certificates on load balancers cause browser warnings or connection failures. Most preventable outage.

Documented **Data sources**: iControl REST API (`/mgmt/tm/sys/crypto/cert`). **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:certificate_inventory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:certificate_inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_left<90` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **SSL Certificate Expiry (F5 BIG-IP)**): table host cert_name days_left expiry_date


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table sorted by days to expiry, Single value (expiring <30d), Status indicator.

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
index=network sourcetype="f5:certificate_inventory"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<90
| sort days_left | table host cert_name days_left expiry_date
```

## Visualization

Table sorted by days to expiry, Single value (expiring <30d), Status indicator.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
