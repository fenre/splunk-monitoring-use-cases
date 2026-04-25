<!-- AUTO-GENERATED from UC-2.6.60.json — DO NOT EDIT -->

---
id: "2.6.60"
title: "Identity Provider (SAML/AAD) Integration Failures"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.6.60 · Identity Provider (SAML/AAD) Integration Failures

## Description

Workspace and StoreFront sign-ins that rely on SAML or Microsoft Entra ID can fail when federation certificates roll without coordination, when conditional access policies block legacy protocols, or when NameID/UPN mapping between directories drifts. Users experience intermittent or total login failure while infrastructure monitors still show green VDAs. Correlating Citrix-side assertion errors with Entra sign-in results isolates the owning team (identity vs Citrix) quickly and prevents prolonged outages during certificate and trust changes.

## Value

Workspace and StoreFront sign-ins that rely on SAML or Microsoft Entra ID can fail when federation certificates roll without coordination, when conditional access policies block legacy protocols, or when NameID/UPN mapping between directories drifts. Users experience intermittent or total login failure while infrastructure monitors still show green VDAs. Correlating Citrix-side assertion errors with Entra sign-in results isolates the owning team (identity vs Citrix) quickly and prevents prolonged outages during certificate and trust changes.

## Implementation

Ingest Citrix Workspace or connector SAML diagnostic logs to a dedicated sourcetype and map certificate expiry fields. Ingest Microsoft Entra sign-in logs for applications matching Citrix. Build a time-synced join on user and a five-minute window, not a naive transaction. Alert when SAML signature or certificate errors exceed a small baseline, or when Entra returns conditional access block codes for the Citrix app only. Add change tickets for cert rotations with automatic suppression. Document IdP cert fingerprints in a lookup for drift detection. Review privacy before storing full assertion bodies.

## Detailed Implementation

Prerequisites
• Entra app registrations for Citrix with sign-in logging to Splunk; Citrix identity provider configuration documented; time synchronized across data centers.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Onboard both feeds before enabling loud alerts. Normalize user keys: prefer `userPrincipalName` on both sides when possible.

Step 2 — Create the search and alert
Start with a daily top-errors report, then add correlation. Tune out pentest and known break-glass accounts with a lookup.

Step 3 — Validate
In a test tenant, run a lab certificate swap and assert both index families record related failures. Restore the trust and confirm return to normal.

Step 4 — Operationalize
Add this flow to the identity change calendar; require Citrix and identity joint ownership for cert updates.

## SPL

```spl
index=xd (sourcetype="citrix:workspace:saml:diag" OR sourcetype="citrix:cloud:connector:saml")
| eval err=lower(coalesce(error_code, error, message, "")), src="citrix_saml", user=coalesce(user_principal, saml_nameid, subject)
| where like(err, "%cert%") OR like(err, "%signature%") OR like(err, "%nameid%") OR like(err, "%audience%") OR like(err, "%mismatch%") OR match(err, "(AADSTS|MSIS)")
| eval userPrincipalName=user, errorCode=err
| append [
  search index=azure sourcetype="azure:aad:signin" result!="Success"
  (resourceDisplayName="*citrix*" OR resourceDisplayName="*Citrix*" OR appDisplayName="Citrix Workspace")
  | eval src="entra_signin"
  | fields _time, userPrincipalName, result, conditionalAccessStatus, errorCode, src
  ]
| stats count by userPrincipalName, result, errorCode, src
| sort - count
```

## Visualization

Side-by-side timeline: Citrix SAML errors versus Entra failure codes; table of UPNs with both streams; single value of unique users blocked in one hour.

## References

- [Citrix Cloud identity providers and authentication](https://docs.citrix.com/en-us/citrix-cloud/citrix-cloud-management/identity-providers-in-citrix-cloud.html)
- [Splunk add-on: Microsoft Cloud Services (Entra / Azure data)](https://splunkbase.splunk.com/app/3110)
