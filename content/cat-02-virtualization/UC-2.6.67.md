<!-- AUTO-GENERATED from UC-2.6.67.json — DO NOT EDIT -->

---
id: "2.6.67"
title: "Citrix Endpoint Management Device Certificate Expiry"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.67 · Citrix Endpoint Management Device Certificate Expiry

## Description

Managed devices rely on short-lived user certificates, profile-managed identities, and sometimes enterprise signing or SCEP-issued device identities. A missed renewal quietly breaks Wi-Fi, per-app data protection, and secure mail—often showing up as vague connectivity tickets. CEM and PKI can expose `not_after` and renewal attempts. This use case finds certificates inside a 30-day window, flags renewal failures, and gives compliance teams a defensible, time-bounded list of devices to retire or re-enroll before hard outages.

## Value

Managed devices rely on short-lived user certificates, profile-managed identities, and sometimes enterprise signing or SCEP-issued device identities. A missed renewal quietly breaks Wi-Fi, per-app data protection, and secure mail—often showing up as vague connectivity tickets. CEM and PKI can expose `not_after` and renewal attempts. This use case finds certificates inside a 30-day window, flags renewal failures, and gives compliance teams a defensible, time-bounded list of devices to retire or re-enroll before hard outages.

## Implementation

Ingest a daily export of all managed certificates, or event-driven renewal logs. Standardize to UTC. Build sliding windows: critical at 7 days, warning at 30 days. Alert on any renewal error with a non-empty `error_on_renew`. Join to asset ownership to email queue owners, not the whole org. Reconcile with your PKI or SCEP service logs; dual-source if possible. If `not_after` is sometimes missing, fall back to last-known `template_name` and schedule forced re-pushes. Document emergency procedures for wide-scale root rotation.

## Detailed Implementation

Prerequisites
• SCEP and profile templates documented; CEM or gateway emitting structured cert fields; NTP on all services.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
If you only have DER subjects in logs, parse with care and test one platform first. Add fallbacks for multiple timestamp formats in `strptime`.

Step 2 — Create the search and alert
Page when under 3 days; daily digest 30–7 days. Include device platform in the page body so help desk can script quick fixes.

Step 3 — Validate
In lab, set a test profile to short lifetime, confirm the sliding window. Force a failed renewal, confirm the error event.

Step 4 — Operationalize
Add this list to the monthly CAB for PKI; align with the broader enterprise cert-use case where both exist.

## SPL

```spl
index=xd sourcetype="citrix:endpoint:cert"
| eval expire_epoch=strptime(coalesce(not_after, expiry_utc, ""), "%Y-%m-%dT%H:%M:%S%Z")
| eval days_left=floor((expire_epoch-now())/86400)
| eval renew_ok=if(match(lower(coalesce(renewal_status, "")), "(ok|success|pending)"), 1, 0)
| where (days_left<=30 OR isnull(expire_epoch)) OR renew_ok=0 OR like(lower(coalesce(error_on_renew, "")), "%fail%")
| sort days_left
| table device_id, cert_type, template_name, days_left, renewal_status, error_on_renew, _time
```

## Visualization

Gantt or bar of devices by days to expiry; single value: count of certs under 7 days; table of failed renewals in the last 24 hours.

## References

- [Certificate security in Citrix Endpoint Management (modeled overview)](https://docs.citrix.com/en-us/citrix-endpoint-management/citrix-endpoint-mdm-mam.html)
