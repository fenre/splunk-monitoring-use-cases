<!-- AUTO-GENERATED from UC-5.4.2.json — DO NOT EDIT -->

---
id: "5.4.2"
title: "Client Association Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.2 · Client Association Failures

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch client association failures so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Failed associations frustrate users and indicate RADIUS/auth issues, RF problems, or AP overload.

## Value

Network operations teams classify wireless client association failures by root cause (credentials, RADIUS, capacity, roaming) to distinguish user errors from infrastructure issues and prioritize remediation by impact scope.

## Implementation

Forward WLC/AP syslog. Correlate with RADIUS logs (ISE). Alert on spike in failures per SSID or AP.

## Detailed Implementation

### Prerequisites
- Wireless controller or cloud platform forwarding client association events to Splunk. Sources: (1) Cisco WLC syslog — `*DOT1X*`, `*ASSOC*` messages, (2) Meraki events (`sourcetype=meraki:events`) — association/disassociation events, (3) Aruba controller syslog — client authentication/association logs.
- Data in `index=wireless` with platform-specific sourcetypes. Key fields: `client_mac`, `ap_name`, `ssid`, `reason_code` (802.11 deauthentication reason), `result` (success/failure), `auth_method` (WPA2-PSK, WPA3-Enterprise, 802.1X).
- 802.11 association failures happen during: (1) initial connection (client fails to authenticate), (2) roaming (client fails to re-associate with new AP), (3) reauthentication (session timeout triggers re-auth). The reason code field identifies the specific failure cause.

### Step 1 — Configure data collection
Verify association failure events:
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(assoc.*fail|auth.*fail|deauth|disassoc|reject)")
| stats count by sourcetype, ssid
```

### Step 2 — Create the search and alert

**Primary search — Client association failures by cause:**
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(assoc.*fail|auth.*fail|deauth|reject)")
| eval failure_reason=case(match(_raw, "(?i)wrong.password|invalid.key|PSK.mismatch"), "WRONG_PASSWORD", match(_raw, "(?i)radius|eap|802.1x|dot1x"), "RADIUS_AUTH_FAILURE", match(_raw, "(?i)timeout|no.response"), "AUTH_TIMEOUT", match(_raw, "(?i)max.client|capacity|full"), "AP_CAPACITY", match(_raw, "(?i)policy|acl|denied"), "POLICY_DENIED", match(_raw, "(?i)roam|reassoc"), "ROAMING_FAILURE", 1==1, "OTHER")
| eval client_id=coalesce(client_mac, src_mac)
| eval ap_id=coalesce(ap_name, name)
| stats count as failures dc(client_id) as affected_clients dc(ap_id) as affected_aps by ssid, failure_reason
| eval severity=case(failure_reason="RADIUS_AUTH_FAILURE" AND failures > 50, "CRITICAL", failures > 100, "HIGH", failures > 20, "MEDIUM", 1==1, "LOW")
| sort severity, -failures
```

#### Understanding this SPL: The failure reason classification is key for troubleshooting. WRONG_PASSWORD affects individual users (user error or credential rotation not applied). RADIUS_AUTH_FAILURE affects all 802.1X users and indicates a RADIUS server issue (see UC-5.4.8). AP_CAPACITY means the AP has too many clients (capacity planning needed). ROAMING_FAILURE suggests RF design issues (insufficient AP overlap for seamless roaming).

**Client-level failure tracking:**
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(assoc.*fail|auth.*fail|deauth|reject)")
| eval client_id=coalesce(client_mac, src_mac)
| eval ap_id=coalesce(ap_name, name)
| stats count as failures dc(ap_id) as aps_tried values(ssid) as ssids by client_id
| where failures > 5
| sort -failures
| head 20
```

**AP-level failure concentration:**
```spl
index=wireless earliest=-4h
| where match(_raw, "(?i)(assoc.*fail|auth.*fail|deauth|reject)")
| eval ap_id=coalesce(ap_name, name)
| stats count as failures dc(client_mac) as clients by ap_id, ssid
| where failures > 10
| lookup wireless_ap_inventory.csv ap_name as ap_id OUTPUT building floor zone
| sort -failures
```

### Step 3 — Validate
(a) Attempt to connect to the wireless with an incorrect password and verify the "WRONG_PASSWORD" failure appears.
(b) Temporarily stop the RADIUS server and verify "RADIUS_AUTH_FAILURE" events are generated for 802.1X SSIDs.
(c) Compare failure counts with the wireless controller's client troubleshooting dashboard.

### Step 4 — Operationalize
Dashboard ("Wireless — Association Failures"):
- Row 1 — Single-value tiles: "Total failures (4h)", "Affected clients", "RADIUS failures", "Worst AP (failures)".
- Row 2 — Failure breakdown table: SSID, failure reason, count, affected clients/APs, severity.
- Row 3 — Top failing clients: client MAC, failure count, APs tried.
- Row 4 — Top failing APs with building/floor context.

Alerting:
- Critical (RADIUS_AUTH_FAILURE > 50 in 15 minutes): RADIUS server issue — all 802.1X users affected.
- High (> 100 association failures in 1 hour on single SSID): systemic issue on that SSID.
- Warning (single AP with > 20 failures): investigate AP health or RF environment.

### Step 5 — Troubleshooting

- **Mass failures across all SSIDs and APs** — Controller issue or configuration push failure. Check the controller health and recent configuration changes.

- **Failures only on 802.1X SSID** — RADIUS server issue (see UC-5.4.8). Check RADIUS server reachability, certificate validity, and EAP method configuration.

- **Failures concentrated on one AP** — The AP may have a hardware issue (bad radio), RF interference (see UC-5.4.6), or be overloaded (see UC-5.4.5 for client count).

## SPL

```spl
index=network sourcetype="cisco:wlc" ("association" OR "authentication") AND ("fail" OR "reject" OR "denied")
| stats count by ap_name, ssid, reason | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src Authentication.app span=1h
| where count>0
| sort -count
```

## Visualization

Table (AP, SSID, reason, count), Bar chart by reason, Timechart.

## Known False Positives

Failed logins often come from typos, expired passwords, guest self-service, or a single misconfigured device; treat sustained rises across many users as the real signal.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
