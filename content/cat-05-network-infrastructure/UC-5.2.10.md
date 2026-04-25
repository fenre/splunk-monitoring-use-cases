<!-- AUTO-GENERATED from UC-5.2.10.json — DO NOT EDIT -->

---
id: "5.2.10"
title: "Admin Access Audit"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.10 · Admin Access Audit

## Description

Firewall admin access is highly privileged. Audit trail is a compliance must-have.

## Value

Firewall admin access is highly privileged. Audit trail is a compliance must-have.

## Implementation

Forward system/auth logs. Alert on failed admin logins. Track all successful logins. Alert on unexpected source IPs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: Firewall system/auth logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward system/auth logs. Alert on failed admin logins. Track all successful logins. Alert on unexpected source IPs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="pan:system" ("login" OR "logout" OR "auth")
| eval status=case(match(_raw,"success"),"Success", match(_raw,"fail"),"Failed", 1=1,"Other")
| stats count by admin_user, src, status | sort -count
```

Understanding this SPL

**Admin Access Audit** — Firewall admin access is highly privileged. Audit trail is a compliance must-have.

Documented **Data sources**: Firewall system/auth logs. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: pan:system. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="pan:system". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by admin_user, src, status** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Authentication data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Authentication model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (admin, source, status), Timeline, Bar chart.

## SPL

```spl
index=firewall sourcetype="pan:system" ("login" OR "logout" OR "auth")
| eval status=case(match(_raw,"success"),"Success", match(_raw,"fail"),"Failed", 1=1,"Other")
| stats count by admin_user, src, status | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Table (admin, source, status), Timeline, Bar chart.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
