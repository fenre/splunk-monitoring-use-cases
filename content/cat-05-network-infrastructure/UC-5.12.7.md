<!-- AUTO-GENERATED from UC-5.12.7.json — DO NOT EDIT -->

---
id: "5.12.7"
title: "IMS Registration Failure Rate"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.12.7 · IMS Registration Failure Rate

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know when handsets or apps cannot register to the core—before users only say “I have no bars” in the office.*

---

## Description

HSS/UDM or P-CSCF failures show up as elevated 401/403/timeout on REGISTER — impacts VoLTE attach and VoWiFi.

## Value

IMS teams detect VoLTE and VoWiFi registration failures before subscribers lose voice service, with per-element and per-access-type drill-down for rapid root cause identification.

## Implementation

Break out by `visited_network` for roaming; correlate with certificate expiry on IPSec for VoWiFi.

## Detailed Implementation

### Prerequisites
- IMS SIP signaling data in `index=ims` with `sourcetype=ims:sip` from P-CSCF/I-CSCF/S-CSCF logs, or wire capture via `sourcetype=stream:sip` on the IMS signaling path. The `method=REGISTER` filter isolates registration transactions. `reply_code` must be extracted for success/failure classification.
- Understand IMS registration flow: UE sends REGISTER to P-CSCF, which forwards to I-CSCF, which queries HSS for the serving S-CSCF, then forwards to S-CSCF. The S-CSCF authenticates via Diameter Cx to HSS (SAR/SAA). Failures can occur at any hop: P-CSCF (IPSec/TLS issues for VoWiFi), I-CSCF (HSS routing failure), S-CSCF (authentication failure), or HSS (database issue).
- SIP response codes in IMS registration: 200 OK = success, 401 Unauthorized = normal authentication challenge (first leg of digest auth — NOT a failure), 403 Forbidden = permanent rejection (certificate invalid, subscription expired), 408 Timeout = network element not responding, 5xx = server errors (S-CSCF overloaded, HSS unreachable).
- Important: the 401 response in IMS is part of normal AKA (Authentication and Key Agreement) flow — the S-CSCF sends 401 with an authentication challenge, and the UE responds with credentials. Only count 401 as a failure if it is the final response (i.e., the UE fails to respond or sends invalid credentials). Some logging systems only capture the final outcome, in which case 401 IS a failure.
- Know your registration architecture: VoLTE registrations come via the mobile network (P-CSCF embedded in ePDG or PGW), VoWiFi comes via IPSec tunnel to ePDG/P-CSCF. Different access types have different failure modes.

### Step 1 — Configure data collection
Verify IMS registration data:
```spl
index=ims sourcetype="ims:sip" method="REGISTER" earliest=-1h
| stats count by reply_code
```
You should see 200 (success), 401 (auth challenge), and potentially 403, 408, 5xx. If `reply_code` is null, check field extractions.

Separate by access type if available:
```spl
index=ims sourcetype="ims:sip" method="REGISTER" earliest=-1h
| eval access_type=case(match(_raw, "(?i)vowifi|epdg|wifi"), "VoWiFi", match(_raw, "(?i)volte|lte"), "VoLTE", 1==1, "Unknown")
| stats count by reply_code, access_type
```

### Step 2 — Create the search and alert

**Primary search — Registration failure rate (5-min alert):**
```spl
index=ims sourcetype="ims:sip" method="REGISTER" earliest=-15m
| eval fail=if(match(reply_code, "^(403|408|5..)$"), 1, 0)
| stats count as attempts sum(fail) as fails by host
| eval fail_rate=round(100*fails/attempts, 2)
| eval status=case(fail_rate > 10, "CRITICAL", fail_rate > 5, "WARNING", 1==1, "OK")
| where fail_rate > 2
| sort -fail_rate
```

#### Understanding this SPL: We count 403 (Forbidden — permanent rejection), 408 (Timeout — element not responding), and 5xx (server errors) as registration failures. We explicitly exclude 401 because it's part of normal AKA authentication flow. Grouping by `host` (P-CSCF/S-CSCF) identifies which IMS element is generating failures. A failure rate above 2% warrants investigation; above 5% is a warning; above 10% means active subscriber impact.

**Failure code breakdown with visited network (roaming):**
```spl
index=ims sourcetype="ims:sip" method="REGISTER" earliest=-1h
| where match(reply_code, "^(403|408|5..)$")
| rex field=_raw "(?i)visited.network[=:\s]+(?<visited_network>[^\s,;]+)"
| stats count by reply_code, visited_network, host
| eval code_meaning=case(reply_code=="403", "Forbidden (cert/subscription)", reply_code=="408", "Timeout (element unresponsive)", match(reply_code, "^5"), "Server Error", 1==1, reply_code)
| sort -count
```

#### Understanding this SPL: Breaks down failures by response code and visited network. Roaming subscribers may fail registration if the visited network's P-CSCF cannot reach the home HSS, or if the roaming agreement doesn't cover IMS services. This helps distinguish between home-network issues (all visited_network values) and roaming-specific issues (specific partner networks).

**Trending — failure rate over 24h by access type:**
```spl
index=ims sourcetype="ims:sip" method="REGISTER" earliest=-24h
| eval fail=if(match(reply_code, "^(403|408|5..)$"), 1, 0)
| eval access_type=case(match(_raw, "(?i)vowifi|epdg|wifi"), "VoWiFi", 1==1, "VoLTE")
| timechart span=5m sum(fail) as fails count as attempts by access_type
| eval volte_fail_rate=round(100*'fails: VoLTE'/'attempts: VoLTE', 2)
```

Schedule as Alert: every 5 minutes. Trigger when fail_rate > 5% on any host. Critical when fail_rate > 10%.

### Step 3 — Validate
(a) On the IMS EMS (Element Management System), check S-CSCF registration statistics for the same period. Compare success/failure counts.
(b) Register a test device (VoLTE + VoWiFi) and verify the registration appears in Splunk with reply_code=200.
(c) Force a test registration failure (expired certificate, invalid credentials) and verify it appears with the correct failure code.
(d) Confirm the 401 handling: verify that 401 responses from normal AKA flow are NOT counted as failures.

### Step 4 — Operationalize
Dashboard ("IMS - Registration Health"):
- Row 1 — Single-value tiles: "Registration failure rate" (gauge), "Total registrations (5m)", "Active failures", "VoWiFi failure rate" (separate gauge — VoWiFi is often more fragile).
- Row 2 — Timechart: failure rate by access type (VoLTE vs. VoWiFi) over 24h.
- Row 3 — Failure code breakdown table with visited network for roaming analysis.
- Row 4 — Per-CSCF health table showing failure rate by IMS element.

Alerting:
- Critical (fail_rate > 10%): page IMS core team — widespread registration failure, VoLTE/VoWiFi service impacted.
- Warning (fail_rate > 5%): ticket with 2-hour SLA.
- VoWiFi-specific (VoWiFi fail_rate > 10%): may indicate ePDG or IPSec certificate issue.

Runbook (owner: IMS Core Engineering):
1. **403 Forbidden spike**: Check for expired IPSec certificates on the ePDG (VoWiFi) or certificate store issues on the P-CSCF. Also check HSS subscription data for the affected IMSIs — subscription may have expired.
2. **408 Timeout spike**: An IMS element in the registration path is not responding. Check P-CSCF, I-CSCF, S-CSCF, and HSS health. Check Diameter Cx link between S-CSCF and HSS.
3. **5xx errors**: S-CSCF or HSS is overloaded. Check CPU, memory, and database connection pool on the IMS elements. Scale horizontally if possible.
4. **Roaming registration failures**: Check the roaming hub and IPX connectivity to the visited network. Verify the Diameter S6a/Cx link to the home HSS is operational from the visited network's perspective.

### Step 5 — Troubleshooting

- **401 responses are being counted as failures** — In IMS AKA flow, the first REGISTER gets a 401 challenge, then the UE re-registers with credentials. If your logging captures both transactions, 401 is normal. If it only captures the final outcome, 401 means the UE failed authentication. Check your CSCF logging configuration to understand which transactions are logged.

- **VoWiFi failures much higher than VoLTE** — VoWiFi traverses the public internet and IPSec tunnels, making it more susceptible to network issues. Check ePDG IPSec certificate validity, DPD (Dead Peer Detection) settings, and NAT traversal configuration.

- **Failure rate spikes during S-CSCF failover** — Active/standby S-CSCF switchover causes temporary registration failures until subscribers re-register to the new active S-CSCF. This should resolve within the registration interval (typically 3600s). Add a suppression window for planned failovers.

- **`visited_network` field is null** — This field may not be present in all IMS log formats. It is typically in the P-Access-Network-Info or P-Visited-Network-ID SIP headers. Check if these headers are logged by your P-CSCF.

## SPL

```spl
index=ims sourcetype="ims:sip" method="REGISTER"
| eval fail=if(match(reply_code,"^(401|403|408|5..)$"),1,0)
| timechart span=5m sum(fail) as fails, count as attempts
| eval fail_rate=round(100*fails/attempts,2)
| where fail_rate > 5
```

## Visualization

Line chart (fail rate), Bar chart (SIP reason by S-CSCF), Table (IMSI hash top failures).

## Known False Positives

Planned S-CSCF work, HSS cutovers, and certificate rotations create expected registration churn; use maintenance windows in your alert logic.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
