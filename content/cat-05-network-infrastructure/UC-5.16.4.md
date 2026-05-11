<!-- AUTO-GENERATED from UC-5.16.4.json — DO NOT EDIT -->

---
id: "5.16.4"
title: "SSL/TLS Interception Certificate Expiry"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.16.4 · SSL/TLS Interception Certificate Expiry

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Compliance, Availability, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*The helpers that inspect encrypted traffic carry their own ID cards that expire like passports. We track those dates so nobody wakes up to browsers refusing connections because an ID went stale.*

---

## Description

Splunk continuously inventories TLS assets anchoring WAN optimization interception—including offlineissued enterprise roots—surfacing appliances whose impersonation certificates approach expiry before browsers reject connections.

## Value

Compliance maintains uninterrupted decryption transparency while operations avoids midnight outages triggered by forgotten intermediate rotations that would otherwise force emergency bypass and plaintext WAN segments.

## Implementation

Schedule daily saved search, integrate ticketing via webhook when days_remaining<=14, store PEM fingerprints hashed when privacy policies disallow raw subjects.

## Detailed Implementation

### Prerequisites
- authoritative PKI calendar synced with Splunk lookups (`cert_inventory.csv`).
- Roles tagging `cert_role` (`intercept_ca`,`peering`,`mgmt`).
- Secrets vault granting read-only API tokens without exporting private keys.

### Step 1 — Configure data collection
Automate nightly pulls from each vendor UI/API translating PEM metadata into newline-delimited JSON lines ingested with `KV_MODE=json`.

### Step 2 — Create the search and alert
Promote SPL to correlation searches tiered 45/30/14/7 days; escalate severity when HA peers disagree on certificate inventory revision.

### Step 3 — Validate
Compare Splunk table against `openssl s_client` spot checks from branch jump hosts quarterly.

### Step 4 — Operationalize
Dashboard timeline plotting expiry ladders plus SLA donut for renewed vs pending—attach QR linking runbooks.

### Step 5 — Troubleshooting
**Timezone drift:** normalize `_time` ingestion vs notAfter UTC.**Wildcard certs:** dedupe using SAN counts.**Shadow imports:** detect duplicates across passive monitors.

## SPL

```spl
index=wanop OR index=infra OR index=certificate earliest=-60d@d latest=+120d@d
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"riverbed|steelhead"),"Riverbed SteelHead",match(v,"silverpeak|edgeconnect"),"Silver Peak EdgeConnect",match(v,"citrix"),"Citrix SD-WAN WANOP",match(v,"zdx|zscaler"),"Zscaler Digital Experience","other")
| where vendor!="other"
| eval expire_epoch=tonumber(coalesce(not_after_epoch,cert_not_after_epoch,ssl_not_after_epoch))
| eval expire=strptime(coalesce(cert_not_after,not_after,ssl_expiry_date),"%Y-%m-%d %H:%M:%S")
| eval expiry_epoch=coalesce(expire_epoch,expire)
| eval days_left=floor((expiry_epoch-_time)/86400)
| eval cn=coalesce(cert_subject,cn,ssl_cn,common_name,"unknown")
| where isnotnull(days_left) AND days_left<=45 AND days_left>=-3
| stats latest(days_left) as days_remaining latest(cn) as subject latest(issuer_cn) as issuer min(expiry_epoch) as expires by vendor host cert_role
| eval urgency=case(days_remaining<=7,"critical",days_remaining<=30,"warning","notice")
| sort days_remaining vendor host
```

## Visualization

Gantt-style table sorted by days_remaining with color tokens for urgency; supporting tile counting certs expiring per vendor.

## Known False Positives

**Short-lived ACME certs:** rotate faster than WAN cadence—exclude ACME profiles.**Lab appliances:** tagged hosts inherit prod thresholds unless filtered.**Clock-skewed logs:** negative days_left despite valid certs—monitor `_indextime` deltas.**Duplicate ingestion:** identical PEM hashed twice inflates counts—use `dedup sha256`.

## References

- [NIST SP 1800-16 — TLS Server Certificate Management (practice guide)](https://csrc.nist.gov/publications/)
- [Citrix Product Documentation — Certificates on SD-WAN](https://docs.citrix.com/en-us/citrix-sd-wan/)
