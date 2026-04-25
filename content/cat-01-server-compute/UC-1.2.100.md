<!-- AUTO-GENERATED from UC-1.2.100.json — DO NOT EDIT -->

---
id: "1.2.100"
title: "PKI / Certificate Authority Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.100 · PKI / Certificate Authority Health

## Description

An enterprise CA issues certificates for authentication, encryption, and code signing. CA failures break SSO, VPN, Wi-Fi, and TLS across the organization.

## Value

When the issuing CA struggles, certificates for VPN, Wi-Fi, apps, and domain trust can all fail together. Watching request, deny, and config events keeps PKI issues a small incident, not a company-wide outage.

## Implementation

Enable CA-specific audit events via certsrv MMC. Monitor certificate request lifecycle: received (4886), approved (4887), denied (4888). Alert on CA configuration changes (4890/4891) and key archival (4893). Track CRL publishing failures in Application log. Monitor CA certificate expiration (alert 90/60/30 days before). Detect ESC1-ESC8 ADCS attack patterns (misconfigurations in certificate templates).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4886, 4887, 4888), `sourcetype=WinEventLog:Application`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CA-specific audit events via certsrv MMC. Monitor certificate request lifecycle: received (4886), approved (4887), denied (4888). Alert on CA configuration changes (4890/4891) and key archival (4893). Track CRL publishing failures in Application log. Monitor CA certificate expiration (alert 90/60/30 days before). Detect ESC1-ESC8 ADCS attack patterns (misconfigurations in certificate templates).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (4886, 4887, 4888, 4890, 4891, 4893)
| eval Action=case(EventCode=4886,"CertRequest_Received", EventCode=4887,"CertRequest_Approved", EventCode=4888,"CertRequest_Denied", EventCode=4890,"CA_Settings_Changed", EventCode=4891,"CA_Config_Changed", EventCode=4893,"CA_Archived_Key", 1=1,"Other")
| stats count by Action, host, SubjectUserName, RequesterName
| sort -count
```

Understanding this SPL

**PKI / Certificate Authority Health** — An enterprise CA issues certificates for authentication, encryption, and code signing. CA failures break SSO, VPN, Wi-Fi, and TLS across the organization.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4886, 4887, 4888), `sourcetype=WinEventLog:Application`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Action** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by Action, host, SubjectUserName, RequesterName** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (CA lifecycle as `Authentication` when tagged to 4886–4888/4890–4893):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.dest span=1h
| where count > 0
```

Enable **data model acceleration** on `Authentication`. Map EventCode to `action` (request/deny/config); the primary `index=wineventlog` stats in Step 2 remain clearest for CA health dashboards.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (cert requests), Table (CA changes), Alert on config changes and template modifications.

## SPL

```spl
index=wineventlog EventCode IN (4886, 4887, 4888, 4890, 4891, 4893)
| eval Action=case(EventCode=4886,"CertRequest_Received", EventCode=4887,"CertRequest_Approved", EventCode=4888,"CertRequest_Denied", EventCode=4890,"CA_Settings_Changed", EventCode=4891,"CA_Config_Changed", EventCode=4893,"CA_Archived_Key", 1=1,"Other")
| stats count by Action, host, SubjectUserName, RequesterName
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.dest span=1h
| where count > 0
```

## Visualization

Timechart (cert requests), Table (CA changes), Alert on config changes and template modifications.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
