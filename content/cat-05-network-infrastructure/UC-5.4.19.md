<!-- AUTO-GENERATED from UC-5.4.19.json — DO NOT EDIT -->

---
id: "5.4.19"
title: "Band Steering Effectiveness Assessment (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.19 · Band Steering Effectiveness Assessment (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch band steering effectiveness assessment (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Measures effectiveness of steering clients from 2.4GHz to 5GHz bands to reduce congestion and improve performance.

## Value

Wireless operations teams monitor Meraki guest SSID splash page (captive portal) authentication success rates, detecting backend failures, timeouts, and configuration issues impacting guest WiFi access.

## Implementation

Query clients API to get current band distribution. Compare against expected ratio for band steering policy.

## Detailed Implementation

### Prerequisites
- Meraki events providing splash page (captive portal) authentication data. Data in `index=meraki` with `sourcetype=meraki:events`. Key fields: `type` (splash), `client_mac`, `ap_name`, `ssid`, `identity` (user/email), `status` (success/failure).
- Splash pages are Meraki's captive portal feature for guest SSIDs. Authentication methods include: click-through, sign-on (email), RADIUS, Active Directory, SMS verification, social login (Facebook/Google).

### Step 1 — Configure data collection
Verify splash events:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(type, "(?i)splash")
| stats count by type, ssid
```

### Step 2 — Create the search and alert

**Primary search — Splash page success/failure analysis:**
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(type, "(?i)splash")
| eval splash_result=case(match(type, "(?i)success") OR match(status, "(?i)success"), "SUCCESS", match(type, "(?i)fail") OR match(status, "(?i)fail"), "FAILURE", match(type, "(?i)timeout"), "TIMEOUT", 1==1, "OTHER")
| stats count(eval(splash_result="SUCCESS")) as successes count(eval(splash_result="FAILURE")) as failures count(eval(splash_result="TIMEOUT")) as timeouts dc(client_mac) as unique_guests by ssid, ap_name
| eval total=successes + failures + timeouts
| eval success_rate=if(total > 0, round(100*successes/total, 1), "N/A")
| where failures > 5 OR timeouts > 5 OR success_rate < 80
| eval issue=case(timeouts > failures, "Splash page load timeout — check DNS/firewall", failures > 10, "Authentication backend issue", success_rate < 80, "Low success rate", 1==1, "Monitor")
| sort -failures
```

**Guest usage trending:**
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(type, "(?i)splash") AND (match(type, "(?i)success") OR match(status, "(?i)success"))
| bin _time span=1d
| stats dc(client_mac) as unique_guests by _time, ssid
| timechart span=1d sum(unique_guests) by ssid
```

### Step 3 — Validate
(a) Connect to the guest SSID and complete the splash page flow. Verify the event appears in Splunk.
(b) Compare guest counts with Meraki Dashboard: Wireless > Splash page > Analytics.
(c) Test a failure scenario (enter wrong credentials on a RADIUS splash) and verify it's captured.

### Step 4 — Operationalize
Dashboard ("Meraki — Guest WiFi"):
- Row 1 — Single-value: "Guest logins today", "Success rate", "Failures", "Unique guests (7d)".
- Row 2 — Per-SSID splash page health table.
- Row 3 — Daily guest usage trending.

Alerting:
- Warning (splash success rate < 70% in 1 hour): captive portal issue.
- Info (daily): guest WiFi usage report.

### Step 5 — Troubleshooting

- **Splash page timeouts** — The splash page is hosted by Meraki cloud. Check: (1) DNS resolution to Meraki splash domain, (2) firewall rules — UDP/TCP 53 (DNS) and TCP 443 must be allowed before authentication, (3) walled garden configuration in Meraki Dashboard.

- **All failures are on one SSID** — Check the splash page configuration for that SSID: Wireless > SSIDs > Splash page. Verify RADIUS server or AD integration settings.

- **Social login not working** — Third-party OAuth endpoints must be in the walled garden. Check Meraki's documentation for required URLs.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by band
| eval band_ratio=round(client_count*100/sum(client_count), 2)
| fields band, client_count, band_ratio
```

## Visualization

Gauge showing 5GHz percentage; pie chart of band distribution; trend line showing steering progress.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
