<!-- AUTO-GENERATED from UC-5.10.4.json — DO NOT EDIT -->

---
id: "5.10.4"
title: "Carrier SIP Trunk Failure Analysis"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.10.4 · Carrier SIP Trunk Failure Analysis

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance

*We watch carrier phone calls that fail on SIP trunks so you can see a trunk or route problem before the business loses voice service.*

---

## Description

Monitors SIP response codes on carrier trunks to detect call routing failures, trunk congestion, and destination unreachable conditions — directly impacting voice service availability and revenue.

## Value

Voice operations teams identify trunk failures within minutes of onset, enabling rapid traffic rerouting to alternate carriers before call completion rates drop below SLA thresholds, directly protecting voice revenue.

## Implementation

Configure Splunk App for Stream to capture SIP signaling on trunk-facing interfaces. Enable SIP protocol extraction for fields `method`, `reply_code`, `caller`, `callee`, and `dest`. Focus on INVITE transactions as these represent call attempts. Group by `dest` to identify problematic trunks or destinations. SIP 4xx codes indicate client errors (e.g., 404 Not Found, 486 Busy Here), 5xx codes indicate server errors, and 6xx codes indicate global failures. Alert when failure rate exceeds 5% sustained over 15 minutes.

## Detailed Implementation

### Prerequisites
- Splunk App for Stream (Splunkbase 1809) v8.0+ with the Stream Forwarder deployed on a SPAN/mirror/tap that sees SIP signaling traffic on carrier trunk interfaces. SIP runs over UDP (port 5060) or TCP/TLS (ports 5060/5061) — ensure the mirror captures both directions of trunk-facing SIP traffic on the SBC (Session Border Controller).
- Understand your SIP trunk topology: identify each carrier trunk by its SBC interface, trunk group name, or destination IP/URI. The `dest` field in Stream represents the SIP Request-URI destination or the downstream SBC/proxy address. You may need to map `dest` IP addresses to carrier names using a lookup `sip_trunks.csv` with columns: dest_ip, carrier_name, trunk_group.
- Know the SIP response code classes: 1xx=Provisional (100 Trying, 180 Ringing, 183 Session Progress), 2xx=Success (200 OK), 3xx=Redirect, 4xx=Client Error (403 Forbidden, 404 Not Found, 408 Timeout, 486 Busy, 487 Request Cancelled, 488 Not Acceptable), 5xx=Server Error (500 Internal, 502 Bad Gateway, 503 Service Unavailable), 6xx=Global Failure (603 Decline, 604 Does Not Exist). For trunk health, 4xx codes are often subscriber-level issues (busy, not found) while 5xx codes indicate infrastructure problems. Distinguish between "normal" failures (486 Busy is expected) and "abnormal" failures (503 Service Unavailable indicates trunk overload).
- Index: create `index=telecom_sip` or use `index=stream`. License: SIP INVITE transactions generate approximately 0.5–1.5 KB per event. A carrier handling 100K calls/hour ≈ 2.4M events/day ≈ 1.2–3.6 GB/day.

### Step 1 — Configure data collection
In the Splunk Stream app, create a SIP stream:

| Setting | Value |
|---------|-------|
| Protocol | SIP |
| Name | `sip_trunk_signaling` |
| Filter | Optional: limit to trunk-facing interface IPs |
| Fields | `method`, `reply_code`, `caller`, `callee`, `dest`, `src`, `call_id`, `setup_delay`, `time_taken`, `user_agent` |
| Sourcetype | `stream:sip` |
| Index | `telecom_sip` |

Verify SIP data is arriving:
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" earliest=-15m
| stats count by dest
```
Each `dest` should correspond to a carrier trunk endpoint. If you see zero events, verify the mirror is capturing SIP signaling ports (5060/5061 UDP and TCP).

Verify response code extraction:
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" earliest=-1h
| stats count by reply_code
| sort reply_code
```
You should see a distribution dominated by 200 (success), 486 (busy), and 487 (cancelled). If `reply_code` is null for all events, the Stream parser may only be capturing INVITE requests without responses — verify bidirectional mirror.

### Step 2 — Create the search and alert

**Primary search — Trunk failure rate overview (15-min alert):**
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" earliest=-15m
| eval is_failure=if(reply_code>=400 AND reply_code!=486 AND reply_code!=487, 1, 0)
| eval is_server_error=if(reply_code>=500, 1, 0)
| stats count as total sum(is_failure) as abnormal_failures sum(is_server_error) as server_errors by dest
| eval failure_rate=round(abnormal_failures*100/total, 2)
| eval server_error_rate=round(server_errors*100/total, 2)
| lookup sip_trunks.csv dest_ip as dest OUTPUT carrier_name trunk_group
| eval trunk_label=if(isnotnull(carrier_name), carrier_name." (".trunk_group.")", dest)
| where failure_rate > 5 OR server_errors > 10
| sort -server_error_rate, -failure_rate
```

#### Understanding this SPL: We exclude 486 (Busy) and 487 (Request Cancelled) from the failure count because these are normal call outcomes — a busy subscriber or a caller hanging up before answer are not trunk failures. What matters for trunk health are abnormal failures: 404 (routing error), 408 (timeout — trunk not responding), 503 (overloaded), 500 (internal error). The `server_error_rate` specifically isolates 5xx codes which indicate infrastructure issues vs. subscriber-level issues. The trunk lookup translates raw IPs into carrier names for operator readability.

**Failure code breakdown — drill into specific error patterns:**
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" reply_code>=400 reply_code!=486 reply_code!=487 earliest=-1h
| eval code_meaning=case(reply_code==403, "Forbidden", reply_code==404, "Not Found", reply_code==408, "Request Timeout", reply_code==480, "Temporarily Unavailable", reply_code==488, "Not Acceptable", reply_code==500, "Internal Server Error", reply_code==502, "Bad Gateway", reply_code==503, "Service Unavailable", reply_code==504, "Server Timeout", reply_code==603, "Decline", 1==1, "Code-".reply_code)
| stats count by reply_code, code_meaning, dest
| lookup sip_trunks.csv dest_ip as dest OUTPUT carrier_name
| sort -count
```

#### Understanding this SPL: Once the primary search flags a trunk with high failure rate, this drill-down identifies the specific error pattern. A concentration of 503 (Service Unavailable) points to trunk capacity exhaustion — the downstream carrier or SBC cannot accept more calls. A pattern of 408 (Timeout) suggests the far-end is unreachable or overloaded. 404 (Not Found) at scale indicates a routing misconfiguration or number portability issue.

**Trending — failure rate per trunk over 24h:**
```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE" earliest=-24h
| eval is_abnormal_failure=if(reply_code>=400 AND reply_code!=486 AND reply_code!=487, 1, 0)
| bin _time span=15m
| stats count as total sum(is_abnormal_failure) as failures by _time, dest
| eval failure_rate=round(failures*100/total, 2)
| lookup sip_trunks.csv dest_ip as dest OUTPUT carrier_name
| eval trunk=if(isnotnull(carrier_name), carrier_name, dest)
| timechart span=15m avg(failure_rate) by trunk
```

#### Understanding this SPL: 24-hour trend showing failure rate per trunk with 15-minute granularity. Reveals time-of-day patterns (peak-hour congestion), sustained degradation (carrier issue), or sudden onset (outage). Compare trunk trends side by side — if all trunks degrade simultaneously, the issue is likely on your side (SBC, network); if only one trunk degrades, the issue is on the carrier side.

Schedule as Alert: the primary search runs every 15 minutes. Trigger when `server_error_rate > 5` (infrastructure failure) or `failure_rate > 10` (broad failure pattern). Throttle by `dest` for 1 hour.

### Step 3 — Validate
(a) On the SBC management interface, pull the call detail records (CDRs) for the same 15-minute window. Compare total INVITE count and failure count per trunk group. Splunk and SBC should match within 5%.

(b) Verify the 486/487 exclusion is appropriate for your network: on some trunks, 486 may not indicate subscriber busy but rather trunk-level rejection. Check with your carrier — if they use 486 to indicate trunk saturation, include it in the failure count.

(c) Build the `sip_trunks.csv` lookup: export trunk group definitions from the SBC configuration. Include columns: dest_ip, carrier_name, trunk_group, max_concurrent_calls, contract_sla. This lookup makes the dashboard and alerts immediately actionable.

(d) Validate the `dest` field: depending on Stream configuration, `dest` may be the SIP Request-URI host, the downstream proxy IP, or the SBC egress interface. Run `| stats count by dest, src | head 20` to understand the address mapping and ensure `dest` correctly identifies the carrier trunk.

(e) Test alert routing: simulate a trunk failure by reducing a test trunk's capacity or blocking traffic, verify the alert fires with the correct trunk label and failure codes.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Voice — SIP Trunk Health"):
- Row 1 — Single-value tiles: "Overall trunk success rate" (green >95%, yellow 90–95%, red <90%), "Total call attempts (15m)", "Active trunks", "Trunks with 5xx errors".
- Row 2 — Timechart: failure rate by trunk over 24h. 5% threshold reference line.
- Row 3 — Two panels: (left) Trunk health table — carrier, trunk group, total calls, failure rate, worst error code; (right) Error code distribution pie chart for the worst trunk.
- Row 4 — Call volume per trunk over 24h (capacity planning), with max concurrent calls reference lines from the trunk lookup.

Alerting:
- Critical (server_error_rate > 10% on any trunk): page voice operations — trunk infrastructure failure, active call loss. Include carrier name, trunk group, and top error code.
- Warning (failure_rate > 5% sustained for 30 minutes): ticket to voice engineering with 2-hour SLA.
- Capacity (call volume > 80% of trunk max_concurrent_calls): proactive alert to capacity planning.

Runbook (owner: Voice Operations / Carrier Management):
1. **503 Service Unavailable on a trunk**: The carrier's SBC or switch is overloaded or in maintenance. Contact the carrier's NOC immediately with the trunk ID and error volume. In parallel, reroute traffic to an alternate carrier trunk on the SBC if available.
2. **408 Request Timeout spike**: The far-end is not responding. Check IP connectivity to the carrier (ping, traceroute). If the network path is fine, the carrier's SBC may be down. Escalate to carrier.
3. **404 Not Found at scale**: Routing table or number portability database is stale. Check the SBC's dial plan and LNP (Local Number Portability) dip configuration. If the issue is specific to a number range, check recent porting activity.
4. **Multiple trunks degrading simultaneously**: The issue is likely on your side — check SBC health (CPU, memory, media resource utilization), network path to all carriers, and DNS resolution for SIP domains.

### Step 5 — Troubleshooting

- **No SIP events in Splunk** — Verify the mirror captures SIP ports (5060 UDP/TCP, 5061 TLS). If SIP uses non-standard ports on your SBC, configure the Stream Forwarder to include those ports. Also check that the Stream SIP protocol is enabled and deployed.

- **`reply_code` is null for all events** — Stream may only be capturing INVITE requests without final responses. This happens when the mirror captures only one direction. Verify bidirectional capture. Also check if SIP is TLS-encrypted (port 5061) — Stream cannot parse encrypted SIP without decryption.

- **Failure rate seems too high compared to SBC CDRs** — Check if the search is counting retransmissions. SIP over UDP retransmits on timeout, generating duplicate INVITEs. Use `| dedup call_id` before the stats to count unique call attempts only.

- **`dest` shows internal SBC IP instead of carrier** — The Stream Forwarder may be capturing traffic on the wrong interface (internal-facing rather than trunk-facing). Adjust the mirror to capture only the carrier-facing SBC interfaces.

- **TLS-encrypted SIP trunks are invisible** — Splunk Stream cannot inspect TLS-encrypted traffic without the private key. For encrypted trunks, consider collecting CDR exports from the SBC instead of wire capture, or configure TLS termination/re-encryption on the SBC with a copy of the cleartext to the mirror port.

## SPL

```spl
sourcetype="stream:sip" method="INVITE"
| stats count as total, sum(eval(if(reply_code>=400, 1, 0))) as failures by dest
| eval failure_rate=round(failures*100/total, 2)
| where failure_rate>5 OR failures>50
| sort -failure_rate
```

## Visualization

Single value (overall SIP trunk success rate with thresholds: green >95%, yellow 90-95%, red <90%), Column chart (failure count by dest), Table (dest, total attempts, failures, failure_rate — sortable), Timechart (SIP 4xx/5xx/6xx responses over 24h by response code class).

## Known False Positives

SBC certificate rolls, number portability batches, and customer premise equipment reboots can spike SIP failures. Match trunk names to the carrier work queue.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
