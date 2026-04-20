---
id: "2.1.32"
title: "ESXi Host Certificate Expiration"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.32 · ESXi Host Certificate Expiration

## Description

ESXi hosts use certificates for secure communication with vCenter and other hosts. Expired certificates cause vCenter disconnection, vMotion failures, and HA communication breakdowns. The VMCA-signed certificates have a 5-year default lifetime, but custom certificates may expire sooner.

## Value

ESXi hosts use certificates for secure communication with vCenter and other hosts. Expired certificates cause vCenter disconnection, vMotion failures, and HA communication breakdowns. The VMCA-signed certificates have a 5-year default lifetime, but custom certificates may expire sooner.

## Implementation

Create a PowerCLI scripted input: `Get-VMHost | Get-VMHostCertificate | Select VMHost, NotAfter, Subject, Issuer`. Run daily. Alert at 90 days (warning), 30 days (high), 7 days (critical). Also check vCenter VMCA certificate and STS signing certificate which cause widespread failures when expired.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (PowerCLI certificate query).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a PowerCLI scripted input: `Get-VMHost | Get-VMHostCertificate | Select VMHost, NotAfter, Subject, Issuer`. Run daily. Alert at 90 days (warning), 30 days (high), 7 days (critical). Also check vCenter VMCA certificate and STS signing certificate which cause widespread failures when expired.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="esxi_certificates"
| eval days_to_expiry=round((strptime(not_after, "%Y-%m-%dT%H:%M:%S") - now()) / 86400, 0)
| where days_to_expiry < 90
| sort days_to_expiry
| table host, subject, issuer, days_to_expiry, not_after
```

Understanding this SPL

**ESXi Host Certificate Expiration** — ESXi hosts use certificates for secure communication with vCenter and other hosts. Expired certificates cause vCenter disconnection, vMotion failures, and HA communication breakdowns. The VMCA-signed certificates have a 5-year default lifetime, but custom certificates may expire sooner.

Documented **Data sources**: Custom scripted input (PowerCLI certificate query). **App/TA** (typical add-on context): `Splunk_TA_vmware`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: esxi_certificates. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="esxi_certificates". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_to_expiry** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_to_expiry < 90` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **ESXi Host Certificate Expiration**): table host, subject, issuer, days_to_expiry, not_after


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, cert, expiry), Single value (certs expiring within 30 days), Timeline (upcoming expirations).

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
index=vmware sourcetype="esxi_certificates"
| eval days_to_expiry=round((strptime(not_after, "%Y-%m-%dT%H:%M:%S") - now()) / 86400, 0)
| where days_to_expiry < 90
| sort days_to_expiry
| table host, subject, issuer, days_to_expiry, not_after
```

## Visualization

Table (host, cert, expiry), Single value (certs expiring within 30 days), Timeline (upcoming expirations).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
