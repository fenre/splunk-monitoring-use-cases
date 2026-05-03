<!-- AUTO-GENERATED from UC-5.3.15.json — DO NOT EDIT -->

---
id: "5.3.15"
title: "Citrix ADC SSL Certificate Expiration Monitoring (NetScaler)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.15 · Citrix ADC SSL Certificate Expiration Monitoring (NetScaler)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance, Availability

*We look at time left on listener certificates in one place on the same gear so renewals are planned, not an outage story.*

---

## Description

SSL certificates on Citrix ADC terminate HTTPS connections for all web applications behind the load balancer. An expired certificate causes browser warnings or complete connection failures for all users. The NITRO API exposes `daystoexpiration` for every bound SSL certificate, enabling automated alerting well before expiry. Certificate expiry outages are among the most preventable yet impactful failures in production environments.

## Value

Infrastructure teams track Citrix ADC SSL certificate expiration with tiered urgency and application ownership context, preventing HTTPS outages from expired certificates.

## Implementation

Create a scripted input that polls the NITRO API `sslcertkey` resource on each ADC. The API returns `certkey` name, `subject`, `issuer`, `serial`, `clientcertnotbefore`, `clientcertnotafter`, `daystoexpiration`, and `expirymonitor` status. Also enable the built-in `expirymonitor` on the ADC with a `notificationperiod` (10–100 days). Run the scripted input daily. Alert at 90 days (plan renewal), 30 days (action required), 7 days (critical), and immediately when `daystoexpiration` reaches 0. Track all certificates bound to vServers — unbound certificates can be ignored or flagged for cleanup.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC syslog or NITRO API providing certificate data. Key fields: `cert_name`, `expiry_date`, `days_to_expiry`, `issuer`, `subject`, `serial`. Citrix ADC syslog message: "Certificate <name> is going to expire in <N> days" (message code EVENT_CERT_EXP).

### Step 1 — - Configure data collection
Citrix ADC generates certificate expiry warnings at 30 days and 7 days by default. Optionally poll NITRO API: `GET /nitro/v1/config/sslcertkey` for all certificate metadata. Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("certificate" AND ("expir" OR "expire")) earliest=-30d
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Certificate expiry monitoring:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") earliest=-7d
| where match(_raw, "(?i)(certificate|cert|ssl).*(expir|expire|expired)")
| rex "(?i)(?:certificate|cert)\s+(?<cert_name>\S+).*?(?<days_left>\d+)\s*day"
| eval days_left=coalesce(days_to_expiry, days_left)
| where isnotnull(days_left)
| lookup citrix_cert_inventory.csv cert_name OUTPUT vserver, application, owner, auto_renew
| eval urgency=case(tonumber(days_left) < 0, "EXPIRED", tonumber(days_left) < 7, "CRITICAL", tonumber(days_left) < 30, "WARNING", tonumber(days_left) < 90, "PLAN", 1==1, "OK")
| where urgency != "OK"
| table host, cert_name, application, vserver, owner, days_left, urgency, auto_renew
| sort days_left
```

### Step 3 — - Validate
(a) On ADC CLI: `show ssl certkey` -- compare expiry dates with Splunk.
(b) Identify a certificate expiring within 30 days and verify it appears.
(c) Check certificate bindings: `show ssl vserver <vs>` -- verify the correct cert is bound.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- SSL Certificate Lifecycle"):
* Row 1 -- Single-value: "Expired", "< 7 days", "< 30 days", "Total certs".
* Row 2 -- Certificate expiry table with owner and auto-renewal status.

Alerting:
* Critical (cert expired or < 7 days): immediate renewal.
* Warning (cert < 30 days): schedule renewal.
* Info (weekly): certificate report.

### Step 5 — - Troubleshooting

* **Certificate renewed but ADC still shows old** -- After uploading a new cert, you must update the binding: `update ssl certkey <name> -cert <new_file> -key <new_key>`. If HA pair, sync: `force ha sync`.

* **Wildcard cert expiring** -- Wildcard certs are often shared across many vservers. Use the lookup to identify all affected applications and coordinate renewal.

* **Let's Encrypt / ACME certs** -- If using automated renewal, verify the automation is running. Citrix ADC supports ACME protocol natively in recent firmware.

## SPL

```spl
index=network sourcetype="citrix:netscaler:ssl"
| stats latest(days_to_expiry) as days_left, latest(subject) as subject, latest(issuer) as issuer, values(bound_vserver) as bound_to by certkey_name, host
| where days_left < 90
| eval urgency=case(days_left<=7, "CRITICAL", days_left<=30, "HIGH", days_left<=90, "MEDIUM", 1=1, "LOW")
| sort days_left
| table certkey_name, days_left, urgency, subject, issuer, bound_to, host
```

## Visualization

Table (certificates sorted by expiry), Single value (certificates expiring within 30 days), Gauge (soonest expiry).

## Known False Positives

New listeners, reissues, and short-lived test certs can look "almost expired" on paper while automation is in flight.

## References

- [CIM: Certificates](https://docs.splunk.com/Documentation/CIM/latest/User/Certificates)
