<!-- AUTO-GENERATED from UC-5.13.14.json — DO NOT EDIT -->

---
id: "5.13.14"
title: "Client Onboarding Failure Rate"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.14 · Client Onboarding Failure Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for people who cannot connect to the network at all — not slow, but completely blocked. When the system that checks passwords goes down, or when the address pool runs dry, this alarm catches it within minutes so your team can fix it before the entire office is stuck without network access.*

---

## Description

Tracks client onboarding failures detected by Catalyst Center Assurance — DHCP timeouts, RADIUS/AAA rejections, association failures, and excessive onboarding latency — so operations can identify whether users are being blocked from connecting and why, before the help desk is overwhelmed with 'I can't connect' calls.

## Value

An onboarding failure is the worst possible user experience — the person isn't just slow, they literally cannot access the network. High onboarding failure rates during business hours mean RADIUS is down, DHCP is exhausted, or APs are at capacity. This UC separates onboarding issues from general client health issues (UC-5.13.11) so you route the problem to the right team: identity/RADIUS team for AAA failures, infrastructure team for DHCP, wireless team for association failures. The issue name from Catalyst Center's AI tells you the root cause category without manual investigation.

## Implementation

Uses the `issue` input filtered to `category="Onboarding"`. No additional input needed if UC-5.13.21 (Issue Summary) is operational. Schedule as alert: cron `*/15 * * * *`, trigger when onboarding issues > 5 in the last 30 minutes. Route to the wireless/identity team.

## Detailed Implementation

### Prerequisites
- UC-5.13.21 (Issue Summary) must be operational — this UC filters the same `cisco:dnac:issue` data to `category="Onboarding"`. No additional input needed.
- Alternatively, for per-client onboarding metrics, enable the `client` detail input (same as UC-5.13.12). The `cisco:dnac:client` events include `onboardingTime` (seconds) and `connectionStatus` fields that provide client-level granularity.
- Understand Catalyst Center's onboarding issue taxonomy: Assurance detects several types of onboarding failures, each with a specific `name`:
  - "DHCP_TIMEOUT" / "Client DHCP Timeout" — client didn't get an IP address
  - "AAA_AUTH_FAILURE" / "Client AAA Failure" — RADIUS rejected the authentication
  - "ASSOCIATION_FAILURE" — client couldn't associate with the AP
  - "EXCESSIVE_ONBOARDING_TIME" — onboarding took longer than the SLA threshold
- For cross-product correlation with ISE, ensure `index=ise` has ISE syslog or API data with authentication results. The join field is `macAddress` (client) or `nas_ip_address` (AP's management IP).

### Step 1 — Configure data collection
The `issue` input (same as UC-5.13.21) already collects onboarding issues. Confirm they're present:
```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Onboarding" earliest=-7d
| stats dc(issueId) as unique_issues count as total_events
```
If `unique_issues = 0`, either your network has no onboarding problems (good!) or the `category` field name differs in your Catalyst Center version. Check with `| stats values(category)` on the full issue feed.

For per-client onboarding metrics (optional, higher volume), confirm the `client` detail input includes `onboardingTime`:
```spl
index=catalyst sourcetype="cisco:dnac:client" earliest=-1h
| where isnum(onboardingTime)
| stats avg(onboardingTime) as avg_onboard_sec, perc95(onboardingTime) as p95_onboard_sec
```
Typical healthy onboarding: avg < 5s for open SSIDs, avg < 10s for 802.1X. P95 > 30s indicates systemic delay.

### Step 2 — Create the search and alert
Issue-based approach (recommended for crawl/walk):
```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Onboarding"
| stats dc(issueId) as onboarding_issues dc(deviceName) as affected_devices by name
| sort -onboarding_issues
```

Why filter to `category="Onboarding"`: isolates onboarding-specific issues from the broader Assurance issue feed. Onboarding failures have distinct root causes (AAA, DHCP, association) and require different teams than performance or connectivity issues.

Why `dc(issueId)` not `count`: the same issue is returned on every poll while it's active. `dc(issueId)` gives unique issues, which is the operationally meaningful count. `count` reflects persistence (how many poll cycles the issue has been active), which is useful in UC-5.13.21 but not here.

Why `by name`: groups by the specific onboarding failure type ("Client DHCP Timeout", "Client AAA Failure", etc.). This immediately tells the responder whether to call the DHCP team or the identity team.

Client-metrics approach (for deeper analysis):
```spl
index=catalyst sourcetype="cisco:dnac:client"
| eval onboard_ok=if(connectionStatus="CONNECTED" AND onboardingTime < 15, 1, 0)
| eval onboard_fail=if(connectionStatus!="CONNECTED" OR onboardingTime >= 15, 1, 0)
| stats sum(onboard_ok) as successes sum(onboard_fail) as failures dc(macAddress) as total_clients by ssid
| eval failure_rate=round(failures*100/(successes+failures),1)
| where failure_rate > 5
| sort -failure_rate
```

Schedule as Alert: cron `*/15 * * * *`, time range `-30m`, trigger when `dc(issueId) > 3` for the issue-based search. Throttle by `name` for 4 hours.

### Step 3 — Validate
(a) Run the issue-based search over the last 7 days. Cross-reference the issue names with **Catalyst Center > Assurance > Issues** filtered to category "Onboarding". The issue names and counts should match.

(b) If using the client-metrics approach: pick an SSID with a high `failure_rate`. Check **Catalyst Center > Assurance > Client Health > Onboarding** for that SSID. The failure count should be comparable.

(c) Correlate with ISE: for AAA failures, run `index=ise sourcetype=cisco:ise:* "REJECT" OR "FAILED"` for the same time window. If ISE shows corresponding RADIUS rejects, the onboarding failure is confirmed as an authentication issue.

(d) Check onboarding latency: `index=catalyst sourcetype="cisco:dnac:client" | stats avg(onboardingTime) p95(onboardingTime) by ssid`. If `p95 > 30s` for an SSID, investigate RADIUS response time, DHCP server load, or AP overload.

(e) Vendor UI parity: compare the onboarding issue count in Splunk with **Catalyst Center > Assurance > Issues > Onboarding** category count.

### Step 4 — Operationalize
Dashboard placement (on the "Client Experience" dashboard or a dedicated "Onboarding Health" dashboard):
- Single value: "Active Onboarding Issues" (red ≥ 5, yellow ≥ 1, green 0).
- Table: onboarding issue names with counts and affected device counts.
- Timechart: onboarding issues over 7 days to show peak-hour patterns.

Runbook (owner: NOC Tier 1 / Wireless & Identity team):
1. Check the issue `name` to determine the failure type:
   - **"Client DHCP Timeout"** → DHCP scope may be exhausted. Check `show ip dhcp pool` on the DHCP server. Expand the scope or add a secondary DHCP server.
   - **"Client AAA Failure"** → RADIUS server may be down or certificate expired. Check `index=ise sourcetype=cisco:ise:*` for ISE health. Verify the RADIUS shared secret matches between AP/WLC and ISE.
   - **"Association Failure"** → AP may be at capacity. Check `index=catalyst sourcetype="cisco:dnac:devicehealth"` for WLC/AP health scores. Reduce max clients per radio or add APs.
   - **"Excessive Onboarding Time"** → network path to RADIUS or DHCP is congested. Check latency to the RADIUS server.
2. Check whether the issue is localised (one site, one SSID) or campus-wide:
   - Localised → physical infrastructure issue (AP, switch, DHCP relay).
   - Campus-wide → centralised service issue (RADIUS server, DHCP server, DNS).
3. After remediation, verify the onboarding issue resolves in the next 1-2 poll cycles.

### Step 5 — Troubleshooting

- **No onboarding issues in the data** — your network may genuinely have no onboarding problems, or the `category` value differs. Run `| stats values(category)` on the full issue feed to check. Common variants: `Onboarding`, `CLIENT_ONBOARDING`, `onboarding`.

- **High onboarding issue count but no user complaints** — the issues may be for IoT devices or background processes that auto-retry. Check `deviceType` on the affected devices. IoT onboarding failures are lower priority than user device failures.

- **ISE correlation shows no matching RADIUS failures** — the onboarding failure may be at the association layer (before RADIUS is even reached). Check AP capacity and channel utilisation.

- **`onboardingTime` is null in client events** — your TA version may not extract this field. Fall back to the issue-based approach.

- **Failure rate seems too high** — the `onboardingTime >= 15` threshold in the client-metrics search may be too strict. Adjust to 30s for 802.1X SSIDs (EAP handshakes take longer).

- **Same onboarding issue persists for days** — the root cause hasn't been fixed. This is a Problem Management issue, not an alerting issue. Move from UC-5.13.14 alerting to UC-5.13.25 (Recurring Issues) tracking.

- **Onboarding failures spike at 8 AM every day** — this is the morning connection surge. APs and RADIUS servers may be undersized for peak demand. Track the pattern and plan for capacity.

- **Cross-product correlation with ISE shows mismatched counts** — ISE counts individual authentication attempts; Catalyst Center counts unique onboarding failures per client. A client that retries 5 times generates 5 ISE events but 1 Catalyst Center issue. The counts are complementary, not identical.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Onboarding"
| stats dc(issueId) as onboarding_issues dc(deviceName) as affected_devices by name
| sort -onboarding_issues
```

## Visualization

(1) Table: issue name, onboarding_issues count, affected_devices count — sorted by frequency. (2) Single value: total onboarding issues active (red threshold ≥ 5). (3) Timechart: `| timechart span=1h dc(issueId) as onboarding_issues` over 7 days to show patterns (peak-hour spikes, recurring failures). (4) Drilldown: click an issue name → show affected device list from UC-5.13.26.

## Known False Positives

**Scheduled RADIUS server maintenance causing temporary authentication failures.** During ISE maintenance windows, wireless clients cannot authenticate, generating onboarding failures. Distinguish by correlating with `index=ise sourcetype=cisco:ise:*` for ISE health and with ITSM change records. Suppress by using a `catalyst_maintenance_windows` lookup and filtering maintenance periods.

**New device onboarding via PnP generating transient failures.** When many new APs or switches are provisioned through Catalyst Center PnP, their clients temporarily fail to onboard as the devices initialise. Distinguish by checking whether the affected devices have very short uptime (UC-5.13.8). Suppress by requiring the failure rate to persist for 2+ consecutive polls.

**Certificate expiry causing mass 802.1X failures.** If the RADIUS server certificate or the supplicant trust chain expires, all 802.1X clients fail to authenticate simultaneously. Distinguish by checking whether the onboarding issue name contains "certificate" or "EAP" and whether it affects all SSIDs that use 802.1X. Do not suppress — this is a critical issue requiring immediate certificate renewal.

**MAC address randomisation causing repeated 'new device' onboarding.** iOS and Android devices with MAC randomisation appear as new devices on each connection, potentially inflating onboarding failure counts if the network enforces MAC-based policies. Distinguish by checking whether the failing MAC addresses are randomised (locally-administered bit set). Suppress by updating network policies to not rely on MAC addresses for access decisions.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Issues endpoint](https://developer.cisco.com/docs/catalyst-center/#!issues)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Cisco ISE Authentication Troubleshooting](https://www.cisco.com/c/en/us/support/security/identity-services-engine/products-troubleshooting-guides-list.html)
