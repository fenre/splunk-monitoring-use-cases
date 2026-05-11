<!-- AUTO-GENERATED from UC-5.4.20.json — DO NOT EDIT -->

---
id: "5.4.20"
title: "802.1X Authentication Failures and RADIUS Issues (Meraki MR)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.4.20 · 802.1X Authentication Failures and RADIUS Issues (Meraki MR)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance

*We watch 802.1x authentication failures and radius issues (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies authentication server problems, credential issues, and 802.1X configuration mismatches.

## Value

Wireless operations teams audit Meraki MR access point firmware versions across all sites and models, tracking compliance percentage and identifying outdated APs that need upgrade scheduling.

## Implementation

1. Configure SC4S for MR syslog. 2. The 802.1X identity (typically a username, service principal, or computer account) is in the identity= field. 3. Threshold >5 failures per identity per VAP indicates either a legitimate auth issue (expired password, wrong RADIUS shared secret, wrong supplicant cert) or a credential-stuffing attempt. 4. For RADIUS-side context, ingest the RADIUS server log (e.g. ISE, NPS) and correlate on the username.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR syslog. 802.1X EAP failures appear as type=events with type=8021x_eap_failure / 8021x_deauth and the user identity in the identity= field..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MR syslog. 2. The 802.1X identity (typically a username, service principal, or computer account) is in the identity= field. 3. Threshold >5 failures per identity per VAP indicates either a legitimate auth issue (expired password, wrong RADIUS shared secret, wrong supplicant cert) or a credential-stuffing attempt. 4. For RADIUS-side context, ingest the RADIUS server log (e.g. ISE, NPS) and correlate on the username.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    ("8021x_eap_failure" OR "8021x_deauth" OR "wpa_deauth")
    earliest=-24h
| rex "identity='(?<client_identity>[^\']+)'"
| rex "vap='(?<vap_id>\d+)'"
| rex "aid='(?<client_aid>\d+)'"
| stats count as auth_failures,
        values(type) as failure_types,
        values(host) as aps_involved
         by client_identity, vap_id
| where auth_failures > 5
| sort - auth_failures
```

#### Understanding this SPL

**802.1X Authentication Failures and RADIUS Issues (Meraki MR)** — Wireless operations teams audit Meraki MR access point firmware versions across all sites and models, tracking compliance percentage and identifying outdated APs that need upgrade scheduling.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving MR syslog. 802.1X EAP failures appear as type=events with type=8021x_eap_failure / 8021x_deauth and the user identity in the identity= field. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by client_identity, vap_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where auth_failures > 5` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of failing clients; time-series of auth failures; client-level detail dashboard.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    ("8021x_eap_failure" OR "8021x_deauth" OR "wpa_deauth")
    earliest=-24h
| rex "identity='(?<client_identity>[^\']+)'"
| rex "vap='(?<vap_id>\d+)'"
| rex "aid='(?<client_aid>\d+)'"
| stats count as auth_failures,
        values(type) as failure_types,
        values(host) as aps_involved
         by client_identity, vap_id
| where auth_failures > 5
| sort - auth_failures
```

## Visualization

Table of failing clients; time-series of auth failures; client-level detail dashboard.

## Known False Positives

Failed logins often come from typos, expired passwords, guest self-service, or a single misconfigured device; treat sustained rises across many users as the real signal.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
