<!-- AUTO-GENERATED from UC-5.1.39.json — DO NOT EDIT -->

---
id: "5.1.39"
title: "Port Security Violations and Rogue Device Detection (Meraki MS)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.1.39 · Port Security Violations and Rogue Device Detection (Meraki MS)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We help you know early when something looks wrong with port security violations and rogue device detection so the team can act before it grows into a bigger outage.*

---

## Description

Detects unauthorized MAC addresses and port security breaches that indicate potential network intrusion.

## Value

Security teams detect Meraki MS port security violations and rogue device connections, identifying unauthorized devices and 802.1X authentication failures on secure switch ports.

## Implementation

1. Configure SC4S for Meraki MS syslog and enable Switch event log in Meraki Dashboard. 2. Filter on 802.1X failure events and DHCP guard blocks — the two real syslog signals analogous to IOS port-security violations. 3. The TA-meraki (Splunkbase #3018) extracts the type=, port=, identity= fields directly from the structured key=value payload. 4. For sticky-MAC behaviour, use Meraki Dashboard -> Switch -> Access policies (port-based dot1x) instead — there is no Cisco IOS-style port-security on Meraki.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. NOTE: Meraki MS does NOT have classic IOS-style 'port-security' (sticky MAC, max-mac, violation modes); the closest Meraki signals are 802.1X authentication failures (type=8021x_eap_failure / 8021x_deauth) and 'Blocked DHCP server response from <mac> on VLAN <id>' messages emitted by the DHCP guard feature..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for Meraki MS syslog and enable Switch event log in Meraki Dashboard. 2. Filter on 802.1X failure events and DHCP guard blocks — the two real syslog signals analogous to IOS port-security violations. 3. The TA-meraki (Splunkbase #3018) extracts the type=, port=, identity= fields directly from the structured key=value payload. 4. For sticky-MAC behaviour, use Meraki Dashboard -> Switch -> Access policies (port-based dot1x) instead — there is no Cisco IOS-style port-security on M…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    ("8021x_eap_failure" OR "8021x_deauth"
     OR "Blocked DHCP server response"
     OR "MAC flooding" OR "unauthorized")
    earliest=-24h
| rex "port[=\']?(?<port_id>[\d]+)"
| rex "(?<violation_type>8021x_eap_failure|8021x_deauth|Blocked DHCP|unauthorized)"
| stats count as violation_count,
        values(violation_type) as types,
        values(identity) as identities
         by host, port_id
| where violation_count > 0
| sort - violation_count
```

#### Understanding this SPL

**Port Security Violations and Rogue Device Detection (Meraki MS)** — Security teams detect Meraki MS port security violations and rogue device connections, identifying unauthorized devices and 802.1X authentication failures on secure switch ports.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. NOTE: Meraki MS does NOT have classic IOS-style 'port-security' (sticky MAC, max-mac, violation modes); the closest Meraki signals are 802.1X authentication failures (type=8021x_eap_failure / 8021x_deauth) and 'Blocked DHCP server response from <mac> on VLAN <id>' messages emitted by the DHCP guard feature. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host, port_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where violation_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of violations; timeline of events; network detail with affected ports.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    ("8021x_eap_failure" OR "8021x_deauth"
     OR "Blocked DHCP server response"
     OR "MAC flooding" OR "unauthorized")
    earliest=-24h
| rex "port[=\']?(?<port_id>[\d]+)"
| rex "(?<violation_type>8021x_eap_failure|8021x_deauth|Blocked DHCP|unauthorized)"
| stats count as violation_count,
        values(violation_type) as types,
        values(identity) as identities
         by host, port_id
| where violation_count > 0
| sort - violation_count
```

## Visualization

Table of violations; timeline of events; network detail with affected ports.

## Known False Positives

Meraki cloud delays, dashboard API limits, and large site templates can look like a gap. Confirm in dashboard before opening a P1 on Splunk only.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
