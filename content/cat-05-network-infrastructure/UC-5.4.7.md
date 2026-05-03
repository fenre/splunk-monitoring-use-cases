<!-- AUTO-GENERATED from UC-5.4.7.json — DO NOT EDIT -->

---
id: "5.4.7"
title: "Wireless Authentication Trends"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.4.7 · Wireless Authentication Trends

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We watch wireless authentication trends so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

802.1X success/failure rates indicate RADIUS health, certificate issues, or expired credentials.

## Value

Network operations teams monitor wireless authentication trends across all SSIDs and methods (802.1X, PSK, MAB) to detect systemic RADIUS failures, credential rotation issues, and authentication method performance degradation.

## Implementation

Forward ISE/RADIUS authentication logs. Track success/failure ratio over time. Alert on sustained failure rate increase.

## Detailed Implementation

### Prerequisites
- Wireless authentication events from controllers, RADIUS servers, or cloud platforms. Sources: (1) RADIUS server logs (`sourcetype=radius` or vendor-specific), (2) Cisco WLC syslog — DOT1X events, (3) Meraki events — 802.1X authentication results, (4) Aruba ClearPass logs.
- Key fields: `auth_method` (WPA2-PSK, WPA2-Enterprise, WPA3-Enterprise, Open+Captive, MAC Auth), `result` (success/failure/timeout), `ssid`, `client_mac`, `username` (for 802.1X), `reason` (failure reason code).
- Authentication methods by security level: Open (no auth — guest networks), WPA2-PSK (shared password — small offices), WPA2/3-Enterprise (802.1X with RADIUS — corporate), MAC Authentication Bypass (MAB — for devices without 802.1X support like printers, IoT).

### Step 1 — Configure data collection
Verify authentication event data:
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(auth|dot1x|radius|eap|802\.1x|wpa|psk)")
| stats count by sourcetype, ssid
```

### Step 2 — Create the search and alert

**Primary search — Authentication method distribution and failure rates:**
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(auth|dot1x|radius|eap)")
| eval auth_type=case(match(_raw, "(?i)eap|802\.1x|dot1x|enterprise"), "802.1X", match(_raw, "(?i)psk|pre.shared"), "PSK", match(_raw, "(?i)mac.auth|mab"), "MAB", match(_raw, "(?i)open|captive"), "Open/Captive", 1==1, "Other")
| eval auth_result=case(match(_raw, "(?i)(success|accept|permit|authenticated)"), "SUCCESS", match(_raw, "(?i)(fail|reject|deny|timeout)"), "FAILURE", 1==1, "OTHER")
| stats count as total count(eval(auth_result="SUCCESS")) as success count(eval(auth_result="FAILURE")) as failures by ssid, auth_type
| eval failure_rate=round(100*failures/total, 1)
| eval severity=case(failure_rate > 20, "CRITICAL", failure_rate > 10, "HIGH", failure_rate > 5, "WARNING", 1==1, "OK")
| sort severity, -failure_rate
```

#### Understanding this SPL: Authentication failure rate by SSID and method reveals systemic issues. A 20% failure rate on 802.1X means 1 in 5 users can't connect — likely a RADIUS issue. A 5% failure rate on PSK might mean a few users have the wrong password after a rotation. Trending this over time shows whether wireless security is improving or degrading.

**Authentication trending by method:**
```spl
index=wireless earliest=-7d
| where match(_raw, "(?i)(auth|dot1x|radius|eap)")
| eval auth_result=case(match(_raw, "(?i)(success|accept)"), "SUCCESS", match(_raw, "(?i)(fail|reject)"), "FAILURE", 1==1, "OTHER")
| bin _time span=1h
| stats count(eval(auth_result="FAILURE")) as failures count as total by _time, ssid
| eval fail_rate=round(100*failures/total, 1)
| timechart span=1h avg(fail_rate) by ssid
```

### Step 3 — Validate
(a) Connect to each SSID and verify the authentication event appears in Splunk with the correct method and result.
(b) Compare failure rates with the RADIUS server's own statistics.
(c) Rotate a PSK password and verify the expected increase in PSK failures (users with old password).

### Step 4 — Operationalize
Dashboard ("Wireless — Authentication"):
- Row 1 — Single-value tiles: "Auth success rate", "802.1X failures", "PSK failures", "Total authentications (4h)".
- Row 2 — Auth method table: SSID, method, total, success, failures, failure rate, severity.
- Row 3 — 7-day failure rate trending by SSID.

Alerting:
- Critical (802.1X failure rate > 20%): RADIUS server issue — page NOC.
- High (PSK failure rate > 30%): possible credential rotation issue.
- Warning (authentication failure rate increasing): trend-based alert.

### Step 5 — Troubleshooting

- **High 802.1X failure rate across all APs** — RADIUS server down, certificate expired, or EAP method mismatch. Check RADIUS server health (UC-5.4.8) and server certificate validity.

- **High PSK failure rate after password change** — Expected for the first 24-48 hours as users update credentials. If it persists, communicate the new password more broadly.

- **MAB failures for IoT devices** — The device MAC may not be in the RADIUS MAB database. Add the MAC to the authorization list in ISE/ClearPass/NPS.

## SPL

```spl
index=network sourcetype="cisco:ise:syslog" ("Passed" OR "Failed") AND "Wireless"
| eval status=if(match(_raw,"Passed"),"Success","Failed")
| timechart span=1h count by status
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Stacked bar chart (success vs. failure), Line chart, Single value (failure rate %).

## Known False Positives

Failed logins often come from typos, expired passwords, guest self-service, or a single misconfigured device; treat sustained rises across many users as the real signal.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
