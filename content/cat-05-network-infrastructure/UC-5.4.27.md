<!-- AUTO-GENERATED from UC-5.4.27.json — DO NOT EDIT -->

---
id: "5.4.27"
title: "Connection Duration and Session Quality (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.27 · Connection Duration and Session Quality (Meraki MR)

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch connection duration and session quality (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Analyzes typical session lengths and stability to identify problematic SSIDs or time-based issues.

## Value

Wireless security teams audit Meraki SSID configurations across all sites against corporate security policies, detecting unauthorized SSIDs, authentication downgrades, and encryption misconfigurations.

## Implementation

Extract connection_duration from clients API. Aggregate by SSID and time of day.

## Detailed Implementation

### Prerequisites
- Meraki providing SSID availability and configuration data. Data in `index=meraki` with `sourcetype=meraki:api:wireless` or `sourcetype=meraki:events`. Key fields: `ssid`, `enabled` (true/false), `authMode` (open, psk, 8021x-radius, 8021x-meraki), `encryptionMode`, `bandSelection`, `perClientBandwidthLimitUp`, `perClientBandwidthLimitDown`, `network`.
- SSID configuration auditing ensures: (1) security policies are consistently applied across sites (e.g., WPA3 on corporate SSID), (2) unauthorized SSIDs are not enabled, (3) bandwidth limits and traffic shaping are consistent, (4) VLAN assignments are correct.

### Step 1 — Configure data collection
Verify SSID configuration data:
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:ssids") earliest=-4h
| where isnotnull(ssid) AND isnotnull(authMode)
| stats latest(authMode) as auth latest(encryptionMode) as encryption latest(enabled) as enabled by ssid, network
```

### Step 2 — Create the search and alert

**Primary search — SSID configuration compliance audit:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:ssids") earliest=-4h
| where isnotnull(ssid) AND isnotnull(authMode)
| stats latest(authMode) as authMode latest(encryptionMode) as encryption latest(enabled) as enabled latest(bandSelection) as band latest(perClientBandwidthLimitUp) as bw_up latest(perClientBandwidthLimitDown) as bw_down by ssid, network
| lookup meraki_networks.csv network OUTPUT site_name
| lookup ssid_policy.csv ssid OUTPUT required_auth required_encryption required_band
| eval auth_compliant=if(authMode=required_auth OR isnull(required_auth), "Yes", "No")
| eval encryption_compliant=if(encryption=required_encryption OR isnull(required_encryption), "Yes", "No")
| eval policy_violations=mvappend(if(auth_compliant="No", "Auth: expected ".required_auth." got ".authMode, null()), if(encryption_compliant="No", "Encryption: expected ".required_encryption." got ".encryption, null()))
| where isnotnull(policy_violations)
| table ssid, site_name, authMode, encryption, band, policy_violations
| sort ssid
```

**Unauthorized SSID detection:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:ssids") earliest=-4h
| where enabled="true" OR enabled=1
| stats values(network) as networks dc(network) as site_count by ssid, authMode
| lookup authorized_ssids.csv ssid OUTPUT authorized
| where isnull(authorized) OR authorized != "yes"
| table ssid, authMode, site_count, networks
```

### Step 3 — Validate
(a) Compare SSID configurations with Meraki Dashboard: Wireless > SSIDs.
(b) Intentionally misconfigure an SSID's auth mode in a test network and verify the compliance check catches it.
(c) Verify that the policy lookup contains the correct expected configurations for all corporate SSIDs.

### Step 4 — Operationalize
Dashboard ("Meraki — SSID Compliance"):
- Row 1 — Single-value: "SSIDs audited", "Policy violations", "Unauthorized SSIDs", "Sites non-compliant".
- Row 2 — SSID policy violation details.
- Row 3 — Unauthorized SSID alerts.

Alerting:
- High (corporate SSID with auth mode != 8021x-radius): security policy violation.
- Warning (unauthorized SSID enabled): investigate.
- Info (weekly): SSID compliance audit report.

### Step 5 — Troubleshooting

- **Policy lookup not matching** — Ensure `ssid_policy.csv` has exact SSID name matches. Meraki SSID names are case-sensitive.

- **SSID shows different auth across sites** — This indicates inconsistent configuration. Use Meraki templates (Configuration templates) to enforce consistent SSID settings across all networks.

- **Many "unauthorized" SSIDs** — These may be legitimate SSIDs not in the authorized list. Update `authorized_ssids.csv` to include all approved SSIDs.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" connection_duration=*
| stats avg(connection_duration) as avg_session_time, min(connection_duration) as min_session, max(connection_duration) as max_session by ssid
| eval session_quality=if(avg_session_time > 3600, "Stable", "Short")
```

## Visualization

Histogram of session durations; time-of-day heatmap; SSID comparison chart.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
