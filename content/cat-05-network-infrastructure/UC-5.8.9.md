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

Query device API for certificate expiry dates. Alert on <30 days.

## Detailed Implementation

### Prerequisites
- Meraki Dashboard API providing device certificate information via Splunk_TA_cisco_meraki. Data in `index=meraki` with `sourcetype=meraki:api:devices` or a custom script polling the Meraki certificates API. Alternatively, TLS certificate scanning tools (e.g., sslyze, nmap ssl-cert) feeding results to Splunk.
- Key fields: `hostname`/`name`, `serial`, `network`, `cert_expiry_date`, `cert_issuer`, `cert_subject`, `cert_algorithm`.
- For non-Meraki devices: a scheduled script that scans device management interfaces (HTTPS on port 443, 8443, etc.) and reports certificate details. Data in `sourcetype=cert:scan` with fields: `host`, `port`, `cn` (Common Name), `san` (Subject Alternative Names), `expiry`, `issuer`, `key_size`, `signature_algorithm`.
- Build `tls_cert_policy.csv` lookup: `host,service,min_key_size,required_algorithm,max_validity_days` to enforce organizational certificate standards.

### Step 1 — Configure data collection
Verify certificate data:
```spl
(index=meraki sourcetype="meraki:api:devices") OR (index=network sourcetype="cert:scan") earliest=-24h
| stats count by sourcetype, host
```

### Step 2 — Create the search and alert

**Primary search — Certificate expiration tracking:**
```spl
(index=meraki sourcetype="meraki:api:devices") OR (index=network sourcetype="cert:scan") earliest=-24h
| eval cert_expiry_epoch=coalesce(strptime(cert_expiry_date, "%Y-%m-%dT%H:%M:%S"), strptime(expiry, "%Y-%m-%d %H:%M:%S"), strptime(expiry, "%b %d %H:%M:%S %Y %Z"))
| eval days_until_expiry=round((cert_expiry_epoch - now()) / 86400, 0)
| eval device_name=coalesce(name, hostname, host)
| eval urgency=case(days_until_expiry < 0, "EXPIRED", days_until_expiry < 7, "CRITICAL", days_until_expiry < 30, "WARNING", days_until_expiry < 90, "PLAN", 1==1, "OK")
| where urgency!="OK"
| eval cert_info=coalesce(cert_subject, cn)
| lookup tls_cert_policy.csv host OUTPUT min_key_size required_algorithm
| eval key_compliant=if(isnotnull(min_key_size) AND key_size < min_key_size, "WEAK_KEY", "OK")
| eval algo_compliant=if(isnotnull(required_algorithm) AND signature_algorithm!=required_algorithm, "WRONG_ALGO", "OK")
| table device_name, network, cert_info, cert_issuer, days_until_expiry, urgency, key_compliant, algo_compliant
| sort days_until_expiry
```

#### Understanding this SPL: Certificate expiration on network device management interfaces causes: HTTPS management access to fail (browser warnings, automation breaks), API polling failures (TAs can't connect), and monitoring blind spots. For Meraki, the dashboard handles certificate management automatically, but on-premise devices (switches, routers, firewalls) need manual certificate renewal. The `key_compliant` check catches weak keys (RSA < 2048) and the `algo_compliant` check catches deprecated algorithms (SHA-1).

**Certificate inventory by issuer:**
```spl
(index=meraki sourcetype="meraki:api:devices") OR (index=network sourcetype="cert:scan") earliest=-24h
| eval issuer_name=coalesce(cert_issuer, issuer)
| stats count as certs dc(host) as devices by issuer_name
| eval issuer_type=case(issuer_name=cn, "Self-Signed", match(issuer_name, "(?i)let.s.encrypt"), "Let's Encrypt", match(issuer_name, "(?i)(digicert|comodo|globalsign|entrust)"), "Public CA", 1==1, "Internal CA")
| sort -certs
```

### Step 3 — Validate
(a) Open a browser to a device's HTTPS management interface and compare the certificate expiration date with Splunk results.
(b) For Meraki: check Meraki Dashboard > Organization > Inventory for device certificate status.
(c) Verify that `days_until_expiry` calculations are accurate by manually computing for 5 devices.

### Step 4 — Operationalize
Dashboard ("TLS Certificate Tracking"):
- Row 1 — Single-value tiles: "Expired certs", "Expiring < 30 days", "Weak keys", "Self-signed certs".
- Row 2 — Expiration timeline: certificates sorted by days until expiry.
- Row 3 — Certificate inventory by issuer type.
- Row 4 — Compliance issues: weak keys, wrong algorithms.

Alerting:
- Critical (certificate expired): management access broken — renew immediately.
- Critical (certificate expiring < 7 days): emergency renewal.
- Warning (certificate expiring < 30 days): schedule renewal.
- Info (weak key or deprecated algorithm detected): plan certificate re-issuance.

### Step 5 — Troubleshooting

- **Certificate scan data missing for some devices** — The scanning script may not be able to connect (firewall blocking, device using non-standard HTTPS port). Add the device's management port to the scan configuration.

- **Meraki certificate data not available** — Meraki manages certificates automatically through its cloud platform. Meraki device certificates are typically not exposed via the Dashboard API. Monitor Meraki device status instead (online/offline).

- **Expiration date parsing fails** — Different devices/CAs use different date formats. Add additional `strptime` patterns to the `coalesce` chain to handle all formats in your environment.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" certificate_expiry=*
| eval days_until_expiry=round((strptime(certificate_expiry, "%Y-%m-%d")-now())/86400, 0)
| where days_until_expiry < 30
| stats latest(days_until_expiry) as days_left by device_name, device_type
| sort days_left
```

## Visualization

Expiration countdown gauge; timeline of expiring certs; alert table.

## Known False Positives

Cloud-managed certificate rotations and name mismatches in lab orgs can trigger warnings without user impact; compare cert dates in the Meraki UI.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
