---
id: "2.1.44"
title: "ESXi Host Certificate Renewal Compliance"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.1.44 · ESXi Host Certificate Renewal Compliance

## Description

ESXi hosts use SSL certificates for vCenter communication, vMotion, and HA. Expired certificates break vCenter connectivity, prevent migrations, and cause HA communication failures. Proactive monitoring prevents unexpected outages when certs expire.

## Value

ESXi hosts use SSL certificates for vCenter communication, vMotion, and HA. Expired certificates break vCenter connectivity, prevent migrations, and cause HA communication failures. Proactive monitoring prevents unexpected outages when certs expire.

## Implementation

Create scripted input: use `openssl s_client -connect <host>:443 -servername <host> 2>/dev/null | openssl x509 -noout -enddate` or PowerCLI `Get-VMHost | Get-VMHostCertificate`. Run daily. Alert at 90 days (warning), 30 days (high), 7 days (critical). Include vCenter VMCA and STS certs — their expiry affects all hosts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (openssl, ESXi API, or PowerCLI).
• Ensure the following data sources are available: Certificate expiry from ESXi hosts (scripted input querying host API or certificate store).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: use `openssl s_client -connect <host>:443 -servername <host> 2>/dev/null | openssl x509 -noout -enddate` or PowerCLI `Get-VMHost | Get-VMHostCertificate`. Run daily. Alert at 90 days (warning), 30 days (high), 7 days (critical). Include vCenter VMCA and STS certs — their expiry affects all hosts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="esxi_certificates"
| eval days_to_expiry = round((strptime(not_after, "%Y-%m-%dT%H:%M:%S") - now()) / 86400, 0)
| eval severity = case(days_to_expiry < 0, "Expired", days_to_expiry < 7, "Critical", days_to_expiry < 30, "High", days_to_expiry < 90, "Warning", 1==1, "OK")
| where days_to_expiry < 90
| sort days_to_expiry
| table host, subject, issuer, not_after, days_to_expiry, severity
```

Understanding this SPL

**ESXi Host Certificate Renewal Compliance** — ESXi hosts use SSL certificates for vCenter communication, vMotion, and HA. Expired certificates break vCenter connectivity, prevent migrations, and cause HA communication failures. Proactive monitoring prevents unexpected outages when certs expire.

Documented **Data sources**: Certificate expiry from ESXi hosts (scripted input querying host API or certificate store). **App/TA** (typical add-on context): Custom scripted input (openssl, ESXi API, or PowerCLI). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: esxi_certificates. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="esxi_certificates". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_to_expiry** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_to_expiry < 90` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **ESXi Host Certificate Renewal Compliance**): table host, subject, issuer, not_after, days_to_expiry, severity


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, cert, days to expiry), Single value (certs expiring within 30 days), Timeline (upcoming expirations).

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
| eval days_to_expiry = round((strptime(not_after, "%Y-%m-%dT%H:%M:%S") - now()) / 86400, 0)
| eval severity = case(days_to_expiry < 0, "Expired", days_to_expiry < 7, "Critical", days_to_expiry < 30, "High", days_to_expiry < 90, "Warning", 1==1, "OK")
| where days_to_expiry < 90
| sort days_to_expiry
| table host, subject, issuer, not_after, days_to_expiry, severity
```

## Visualization

Table (host, cert, days to expiry), Single value (certs expiring within 30 days), Timeline (upcoming expirations).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
