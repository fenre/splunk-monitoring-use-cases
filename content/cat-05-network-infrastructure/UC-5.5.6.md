<!-- AUTO-GENERATED from UC-5.5.6.json — DO NOT EDIT -->

---
id: "5.5.6"
title: "Certificate Expiration"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.6 · Certificate Expiration

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

SD-WAN device certificates must be valid for overlay connectivity.

## Value

Network operations teams track SD-WAN device and CA certificate expiration dates across the entire fabric, enabling proactive renewal scheduling and preventing certificate-expiry-induced outages.

## Implementation

Poll vManage for certificate status. Alert at 60/30/7 day thresholds.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage for device certificate status. Data in `index=sdwan` with `sourcetype=cisco:sdwan:device` or `sourcetype=cisco:sdwan:certificate`. Key fields: `system_ip`, `site_id`, `certificate_status`, `expiration_date`, `serial_number`, `issuer`, `subject`.
- SD-WAN relies on certificates for control plane authentication (DTLS between controllers and edges), data plane encryption (IPsec tunnel keying), and vManage web interface (HTTPS). Certificate expiration causes: control connection loss (device goes "headless"), tunnel failures, and management access loss.
- Cisco SD-WAN uses two certificate types: (1) Enterprise root CA certificates (used for control plane authentication), (2) WAN edge certificates (device identity). Both have expiration dates that must be tracked.

### Step 1 — Configure data collection
Verify certificate data:
```spl
index=sdwan (sourcetype="cisco:sdwan:device" OR sourcetype="cisco:sdwan:certificate") earliest=-1h
| search certificate* OR expir*
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Primary search — Certificate expiration countdown:**
```spl
index=sdwan sourcetype="cisco:sdwan:certificate" earliest=-1h
| eval expiry_epoch=strptime(expiration_date, "%Y-%m-%dT%H:%M:%S")
| eval days_until_expiry=round((expiry_epoch - now()) / 86400, 0)
| eval urgency=case(days_until_expiry < 0, "EXPIRED", days_until_expiry < 7, "CRITICAL", days_until_expiry < 30, "WARNING", days_until_expiry < 90, "PLAN", 1==1, "OK")
| where urgency!="OK"
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| lookup sdwan_devices.csv system_ip OUTPUT hostname device_model
| eval device_label=if(isnotnull(hostname), hostname, system_ip)
| table device_label, site_name, tier, certificate_status, expiration_date, days_until_expiry, urgency, issuer, serial_number
| sort days_until_expiry
```

#### Understanding this SPL: Certificate expiration is one of the most common causes of SD-WAN outages because it's preventable but often overlooked. When a device certificate expires, all DTLS control connections fail, the device can't establish new IPsec tunnels, and the device effectively goes offline. The urgency tiers provide actionable lead time: 90 days for planning, 30 days for scheduling, 7 days for emergency.

**Certificate inventory summary:**
```spl
index=sdwan sourcetype="cisco:sdwan:certificate" earliest=-1h
| eval expiry_epoch=strptime(expiration_date, "%Y-%m-%dT%H:%M:%S")
| eval days_until_expiry=round((expiry_epoch - now()) / 86400, 0)
| eval bucket=case(days_until_expiry < 0, "Expired", days_until_expiry < 30, "< 30 days", days_until_expiry < 90, "30-90 days", days_until_expiry < 365, "90-365 days", 1==1, "> 1 year")
| stats count by bucket, issuer
| sort bucket
```

**Root CA expiration check:**
```spl
index=sdwan sourcetype="cisco:sdwan:certificate" issuer="*root*" OR issuer="*CA*" earliest=-1h
| eval expiry_epoch=strptime(expiration_date, "%Y-%m-%dT%H:%M:%S")
| eval days_until_expiry=round((expiry_epoch - now()) / 86400, 0)
| where days_until_expiry < 180
| table issuer, subject, expiration_date, days_until_expiry
```

### Step 3 — Validate
(a) In vManage: Administration > Certificate Management. Compare certificate expiration dates with Splunk results.
(b) On an edge device: `show certificate installed` — compare expiration date and serial number with Splunk.
(c) Set up a test alert for certificates expiring within 365 days and verify it captures known certificates.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Certificate Management"):
- Row 1 — Single-value tiles: "Expired certificates", "Expiring < 30 days", "Expiring < 90 days", "Total certificates tracked".
- Row 2 — Certificate expiration timeline (bar chart: buckets by expiry window).
- Row 3 — Urgent certificates table: device, site, expiration date, days remaining, urgency.
- Row 4 — Root CA status: issuer, expiration date.

Alerting:
- Critical (any certificate expired): immediate — device has lost or will lose connectivity.
- Critical (certificate expires within 7 days): emergency renewal needed.
- Warning (certificate expires within 30 days): schedule renewal.
- Info (certificate expires within 90 days): plan renewal during next maintenance window.

### Step 5 — Troubleshooting

- **Certificate data not in Splunk** — The TA may not poll the certificate API endpoint. Check if `/dataservice/certificate/vedge/list` is included in the TA's data collection.

- **Expiration date parsing fails** — Different vManage versions may use different date formats (ISO 8601, epoch, or custom). Check raw events and adjust the `strptime` format string.

- **Certificate shows expired but device still works** — The device may be using a cached session. Once the DTLS session times out or the device reboots, it won't be able to re-establish connections.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:certificate"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<60
| table hostname system_ip days_left | sort days_left
```

## Visualization

Table, Single value, Status indicator.

## Known False Positives

Staging upgrades, RMA replacements, and deferred maintenance windows can leave devices on non-target versions briefly; align alerts with your change calendar.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
