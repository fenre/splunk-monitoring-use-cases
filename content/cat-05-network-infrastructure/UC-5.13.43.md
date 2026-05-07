<!-- AUTO-GENERATED from UC-5.13.43.json — DO NOT EDIT -->

---
id: "5.13.43"
title: "Client Connection Failure Analysis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.43 · Client Connection Failure Analysis

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Walk &middot; **Status:** Verified

*We figure out exactly why people cannot connect to the network — whether it is a password problem, an address problem, or the Wi-Fi being too full. This saves your help desk from guessing and sends the right fix to the right team straight away.*

---

## Description

Categorises client connection failures by root cause (AAA rejection, DHCP timeout, association failure, EAP negotiation failure), connection type, and SSID — translating 'I can't connect' complaints into actionable infrastructure component failures that point directly at RADIUS, DHCP, the WLC, or a specific AP.

## Value

When 30 users call the help desk saying 'the Wi-Fi doesn't work,' the help desk doesn't know whether it's a RADIUS problem, a DHCP problem, or an AP problem — and neither does the network team until they investigate. This UC categorises failures by `failureReason` so the correct team gets engaged immediately: `AAA_FAILURE` → identity team (ISE), `DHCP_TIMEOUT` → infrastructure team (DHCP server), `ASSOCIATION_FAILURE` → wireless team (AP capacity/config). The SSID split tells you whether it's the guest network (lower urgency) or the corporate VoIP network (P1).

## Implementation

Same `client` detail input as UC-5.13.40. Filter to failed connections only. Schedule as alert: trigger when `dc(macAddress) > 10` for any single `failureReason` in a 30-minute window — this indicates a systemic failure, not individual device issues.

## Detailed Implementation

### Prerequisites
- UC-5.13.40 (Client Inventory) operational — same `client` detail input.
- Confirm `connectionStatus`, `onboardingStatus`, and `failureReason` fields are populated in the events. Run:
  ```spl
  index=catalyst sourcetype="cisco:dnac:client" earliest=-24h
  | stats count by connectionStatus
  ```
  You should see `CONNECTED` (majority) and possibly `FAILED` or other status values. If only `CONNECTED` appears, either there are no failures (ideal) or the field isn't populated for failed connections in your TA version.
- Understand the failure taxonomy: Catalyst Center classifies failures by the onboarding stage that failed:
  - **ASSOCIATION**: client couldn't associate with the AP (capacity, SSID mismatch, rate limiting)
  - **AAA** / **AUTHENTICATION**: RADIUS rejected the credentials (wrong password, expired cert, policy mismatch)
  - **DHCP**: client didn't receive an IP address within the timeout (scope exhaustion, relay misconfiguration)
  - **IP_CONNECTIVITY**: client got an IP but can't reach the gateway (VLAN issue, STP, routing)

### Step 1 — Configure data collection
Same `client` detail input as UC-5.13.40. No additional configuration needed. The failure fields are included in the per-client JSON response when a client has failed to connect.

Verify failure data is available:
```spl
index=catalyst sourcetype="cisco:dnac:client" (connectionStatus="FAILED" OR onboardingStatus="FAILED") earliest=-7d
| stats dc(macAddress) as failed_clients, values(failureReason) as failure_types
```

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:client" (connectionStatus="FAILED" OR onboardingStatus="FAILED")
| stats dc(macAddress) as affected_clients count as failure_events by failureReason, connectionType, ssid
| sort -affected_clients
```

Why `dc(macAddress)` not `count`: a single client with cached wrong credentials will generate a failure event on every poll. `dc(macAddress)` shows *how many unique clients* are affected, which is the operationally meaningful metric. `count` shows total failure events (useful for rate-of-failure analysis but misleading for impact assessment).

Why `by failureReason, connectionType, ssid`: the three-dimensional split immediately answers three questions: (1) what failed? (2) wired or wireless? (3) which network? This determines the team, the urgency, and the remediation path.

Schedule as Alert: cron `*/15 * * * *`, time range `-30m`, trigger when `affected_clients > 10` for any single `failureReason`. Throttle by `failureReason` for 4 hours.

### Step 3 — Validate
(a) If you have a test device, intentionally fail its 802.1X authentication (wrong password). Within 2 polls, the device should appear in the results with `failureReason` containing `AAA` or `AUTHENTICATION`.

(b) Cross-reference with **Catalyst Center > Assurance > Issues** filtered to "Onboarding". The failure types should match.

(c) Correlate AAA failures with ISE: `index=ise sourcetype=cisco:ise:* "FAIL" OR "REJECT"` for the same time window. ISE should show corresponding RADIUS failures.

(d) Check `failureReason` field values: `| stats values(failureReason)`. Ensure they match the expected taxonomy. If only a generic string appears (e.g., `FAILED`), the TA version may not provide granular failure reasons.

### Step 4 — Operationalize
Dashboard placement (on the Client Experience dashboard):
- Table of failure reasons with client count and SSID.
- Bar chart: Pareto of failure reasons.
- Single value: total failing clients (red ≥ 10).

Runbook (owner: NOC Tier 1):
1. Check the dominant `failureReason`:
   - **AAA/AUTHENTICATION**: contact the ISE/identity team. Verify RADIUS server health, certificate validity, and policy changes.
   - **DHCP**: check DHCP server health and scope utilisation. `show ip dhcp pool` for scope exhaustion.
   - **ASSOCIATION**: check AP capacity and channel utilisation. May need to reduce max clients per radio or add APs.
   - **IP_CONNECTIVITY**: check VLAN configuration, STP status, and gateway reachability.
2. Check the `ssid` — is it corporate (P2) or guest (P3/P4)?
3. Check the `connectionType` — wired failures are rarer and typically more severe.
4. Correlate with UC-5.13.14 (Onboarding Failure Rate) for trending.

### Step 5 — Troubleshooting

- **No FAILED events in the data** — either no failures are occurring (good) or the field names differ. Check `| stats values(connectionStatus) values(onboardingStatus)` for the actual status values.

- **`failureReason` is null or generic** — your TA/Catalyst Center version may not provide granular failure reasons. Fall back to correlating with ISE logs for authentication failures and DHCP logs for IP assignment failures.

- **Failure count seems too high** — the same client failing on every poll cycle inflates `count`. Always use `dc(macAddress)` for impact assessment.

- **Failures spike at 8 AM daily** — morning connection surge. Many clients authenticating simultaneously can overwhelm RADIUS or DHCP. Check server capacity.

- **All failures are on one SSID** — the SSID-specific configuration is the problem (RADIUS shared secret, VLAN assignment, QoS policy). Compare with a working SSID.

- **Failures correlate with AP reboots** — expected. Clients reassociate after AP restart. Check UC-5.13.8 for reboot events.

- **ISE shows success but Catalyst Center shows failure** — timing difference. The client may have succeeded on a retry after Catalyst Center recorded the initial failure.

- **Search is slow** — filter to `earliest=-30m` for the alert. Use summary indexing for daily failure trend reports.

Additional operational context for Client Connection Failure Analysis:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" (connectionStatus="FAILED" OR onboardingStatus="FAILED")
| stats dc(macAddress) as affected_clients count as failure_events by failureReason, connectionType, ssid
| sort -affected_clients
```

## Visualization

(1) Table: failureReason, connectionType, ssid, affected_clients, failure_events — sorted by affected_clients descending. (2) Bar chart: failure count by `failureReason` for Pareto triage. (3) Timechart: `| timechart span=1h dc(macAddress) as failed_clients by failureReason` to show failure patterns over 24h. (4) Single value: total clients with active failures (red ≥ 10).

## Known False Positives

**Client devices with cached credentials that are no longer valid.** Devices with saved but expired/revoked credentials attempt to authenticate on every association, generating repeated AAA failures. Distinguish by checking whether the same `macAddress` appears repeatedly with the same `failureReason`. Suppress by deduplicating on `macAddress` — count unique failing clients, not failure attempts.

**Captive portal redirects classified as connection failures.** On open/guest SSIDs with captive portals, the pre-portal state may be reported as a connection failure by some Catalyst Center versions. Distinguish by checking whether the failures are exclusively on guest SSIDs. Suppress by excluding known captive-portal SSIDs from the failure analysis.

**IoT devices that don't support 802.1X generating AAA failures.** IoT devices (printers, cameras, sensors) that connect to an 802.1X SSID without proper supplicant configuration will fail authentication. Distinguish by checking `hostType` — IoT devices should be on a MAB (MAC Authentication Bypass) SSID. Do not suppress — this is a segmentation configuration error.

**AP reboot causing brief association failure spike.** When an AP reboots, all its clients attempt to reassociate simultaneously, causing a burst of association failures until they roam to nearby APs. Distinguish by correlating with UC-5.13.8 (uptime/reboot) for AP reboots in the same timeframe. Suppress by requiring the failure spike to persist for 2+ polls.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Detail endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-client-detail)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Cisco ISE Authentication Troubleshooting Guide](https://www.cisco.com/c/en/us/support/security/identity-services-engine/products-troubleshooting-guides-list.html)
