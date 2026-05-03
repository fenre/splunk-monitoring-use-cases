<!-- AUTO-GENERATED from UC-5.3.4.json — DO NOT EDIT -->

---
id: "5.3.4"
title: "SSL Certificate Expiry (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.4 · SSL Certificate Expiry (F5 BIG-IP)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We look at how many days are left on listener certificates on the big-ip so you can renew or swap in time, not the night a site breaks.*

---

## Description

Expired certificates on load balancers cause browser warnings or connection failures. Most preventable outage.

## Value

Infrastructure teams track F5 BIG-IP SSL certificate expiration dates with tiered urgency (expired, <7d, <30d, <90d), ensuring timely renewal before certificate-related outages impact HTTPS services.

## Implementation

Scripted input querying iControl REST for certs. Run daily. Alert at 90/60/30/7 day thresholds.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680). F5 iControl REST API polled for certificate data or syslog messages about certificate expiry. Data in `index=network` with `sourcetype=f5:bigip:syslog` or `sourcetype=f5:bigip:api`. Key fields: `cert_name`, `expiration_date`, `days_to_expiry`, `issuer`, `subject`, `serial`.
* Alternatively, use a scripted input to poll `/mgmt/tm/sys/file/ssl-cert` and extract certificate metadata. F5 also generates syslog messages (`01420006:4:`) when certificates approach expiry.

### Step 1 — - Configure data collection
Option A -- Poll iControl REST (recommended):
Create a scripted input that calls `/mgmt/tm/sys/file/ssl-cert` and extracts `name`, `expirationString`, `issuer`, `subject`. Push to HEC as `sourcetype=f5:bigip:certs`.

Option B -- Syslog-based:
F5 generates "Certificate ... will expire in X days" messages. Verify:
```spl
index=network sourcetype="f5:bigip:syslog" ("certificate" AND ("expir" OR "expire" OR "expired")) earliest=-7d
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Certificate expiry timeline:**
```spl
index=network (sourcetype="f5:bigip:certs" OR sourcetype="f5:bigip:syslog") earliest=-7d
| rex "(?i)certificate\s+(?<cert_name>\S+).*expir.*?(?<days_remaining>\d+)\s*day"
| eval days_remaining=coalesce(days_to_expiry, days_remaining)
| eval expiry_date=coalesce(expiration_date, strftime(relative_time(now(), "+".days_remaining."d"), "%Y-%m-%d"))
| where isnotnull(days_remaining)
| lookup f5_vip_inventory.csv cert_name OUTPUT application, owner, virtual_server
| eval urgency=case(days_remaining < 0, "EXPIRED", days_remaining < 7, "CRITICAL", days_remaining < 30, "WARNING", days_remaining < 90, "PLAN", 1==1, "OK")
| where urgency != "OK"
| table host, cert_name, application, virtual_server, owner, expiry_date, days_remaining, urgency
| sort days_remaining
```

**Certificate inventory:**
```spl
index=network sourcetype="f5:bigip:certs" earliest=-1d
| stats latest(expiration_date) as expiry latest(issuer) as issuer latest(subject) as subject by host, cert_name
| eval days_left=round((strptime(expiry, "%Y-%m-%d") - now()) / 86400, 0)
| sort days_left
```

### Step 3 — - Validate
(a) In tmsh: `show sys file ssl-cert` -- compare expiration dates with Splunk.
(b) Identify a certificate expiring within 30 days and verify it appears with "WARNING" urgency.
(c) For expired certificates, verify they show "EXPIRED" status.

### Step 4 — - Operationalize
Dashboard ("F5 -- SSL Certificate Lifecycle"):
* Row 1 -- Single-value: "Expired certs", "Expiring < 7d", "Expiring < 30d", "Total certs".
* Row 2 -- Certificate expiry timeline table with owner and application context.
* Row 3 -- Certificate inventory sorted by days remaining.

Alerting:
* Critical (certificate expired or expiring < 7 days): immediate renewal required.
* Warning (certificate expiring < 30 days): schedule renewal.
* Info (weekly): certificate status report for all F5 devices.

### Step 5 — - Troubleshooting

* **Certificate shows expired but application works** -- Check if the F5 SSL profile references a different certificate, or if SSL termination happens upstream (CDN, WAF).

* **Can't parse expiration from syslog** -- F5 syslog format varies by version. Check raw events and adjust the rex pattern. For reliability, use the iControl REST API approach.

* **Certificate renewed but Splunk still shows old expiry** -- The F5 may need a configuration sync (if HA pair) or the SSL profile needs to be updated to reference the new certificate.

## SPL

```spl
index=network sourcetype="f5:certificate_inventory"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<90
| sort days_left | table host cert_name days_left expiry_date
```

## Visualization

Table sorted by days to expiry, Single value (expiring <30d), Status indicator.

## Known False Positives

Automation renewals, name changes, and short-lived test certs can look urgent until you read who owns the name.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
