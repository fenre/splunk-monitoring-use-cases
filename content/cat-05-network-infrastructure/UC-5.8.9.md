<!-- AUTO-GENERATED from UC-5.8.9.json — DO NOT EDIT -->

---
id: "5.8.9"
title: "SSL/TLS Certificate Expiration Tracking (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.9 · SSL/TLS Certificate Expiration Tracking (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We warn you before Meraki dashboard certificates age out, so the browser and API checks keep working and nobody gets stuck with scary warnings.*

---

## Description

Monitors SSL certificate expiration dates on all network devices to prevent outages.

## Value

Network operations teams track SSL/TLS certificate expiration across all network device management interfaces and Meraki appliances, preventing certificate-related management access failures and identifying weak cryptographic configurations.

## Implementation

1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. 2. Filter alert titles for certificate / TLS / SSL / expiry keywords. 3. For proactive monitoring deploy a TLS expiry scanner (e.g. the Splunk Sslscan TA or a custom curl + openssl modular input) against your branch endpoints, and trigger a Splunk alert ~30 days before expiry.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: the Meraki Dashboard API does NOT expose certificate validity dates for managed devices; the only signal available is the assurance-alert feed when a certificate-related issue is detected. For branch firewalls hosting public services, monitor your CA portal (Let's Encrypt, Sectigo, DigiCert) directly or use a TLS scanner like ssl-checker / Splunk Sslscan TA..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. 2. Filter alert titles for certificate / TLS / SSL / expiry keywords. 3. For proactive monitoring deploy a TLS expiry scanner (e.g. the Splunk Sslscan TA or a custom curl + openssl modular input) against your branch endpoints, and trigger a Splunk alert ~30 days before expiry.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    (title="*certificate*" OR title="*TLS*" OR title="*SSL*"
     OR title="*expir*")
    earliest=-7d
| stats count as alert_count,
        values(title) as cert_alerts,
        latest(severity) as severity
         by deviceSerial, deviceName, networkName
| sort - alert_count
```

#### Understanding this SPL

**SSL/TLS Certificate Expiration Tracking (Meraki)** — Network operations teams track SSL/TLS certificate expiration across all network device management interfaces and Meraki appliances, preventing certificate-related management access failures and identifying weak cryptographic configurations.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: the Meraki Dashboard API does NOT expose certificate validity dates for managed devices; the only signal available is the assurance-alert feed when a certificate-related issue is detected. For branch firewalls hosting public services, monitor your CA portal (Let's Encrypt, Sectigo, DigiCert) directly or use a TLS scanner like ssl-checker / Splunk Sslscan TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by deviceSerial, deviceName, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Expiration countdown gauge; timeline of expiring certs; alert table.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    (title="*certificate*" OR title="*TLS*" OR title="*SSL*"
     OR title="*expir*")
    earliest=-7d
| stats count as alert_count,
        values(title) as cert_alerts,
        latest(severity) as severity
         by deviceSerial, deviceName, networkName
| sort - alert_count
```

## Visualization

Expiration countdown gauge; timeline of expiring certs; alert table.

## Known False Positives

Cloud-managed certificate rotations and name mismatches in lab orgs can trigger warnings without user impact; compare cert dates in the Meraki UI.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
