<!-- AUTO-GENERATED from UC-5.10.1.json — DO NOT EDIT -->

---
id: "5.10.1"
title: "Diameter Signaling Health Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.10.1 · Diameter Signaling Health Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance

*We track whether the mobile core’s sign-in and billing handshakes succeed, so a signaling problem is caught before millions of people lose service.*

---

## Description

Tracks the success and failure rates of Diameter signaling messages (authentication, authorization, accounting) in the mobile core, essential for maintaining service availability and subscriber experience.

## Value

Operators detect Diameter signaling degradation — authentication failures, routing errors, or peer disconnects — before the volume of affected subscribers triggers a service incident, cutting mean time to detect from minutes to seconds.

## Implementation

Install Splunk App for Stream and configure it to capture Diameter protocol traffic on the core network. Enable the Diameter protocol for full field extraction. Monitor `command_code` and `result_code` to detect signaling issues. Create alerts for sustained drops in success rate or spikes in failure codes such as DIAMETER_AUTHENTICATION_REJECTED (5003) or DIAMETER_UNABLE_TO_DELIVER (3002).

## Detailed Implementation

### Prerequisites
- Splunk App for Stream (Splunkbase 1809) v8.0+ installed on the Search Head (dashboards, stream configuration UI) and the Stream Forwarder (`splunk_app_stream_forwarder`) deployed on a host connected to a SPAN port, mirror session, or network tap that sees Diameter signaling traffic in the mobile core. The forwarder performs deep packet inspection (DPI) at line rate.
- Network access to Diameter signaling links: deploy the Stream Forwarder where it can passively observe traffic between Diameter peers — typically between the MME/SGSN and HSS (S6a interface, application_id 16777251), between the PCRF and PGW (Gx interface, application_id 16777238), or between the OCS/OFCS and PGW (Gy/Rf interfaces, application_id 4). Diameter runs over SCTP (port 3868) or TCP (port 3868) — ensure the mirror captures both directions of these flows.
- Understand the Diameter protocol basics for your core: command codes identify the transaction type (257=CER/CEA Capabilities Exchange, 271=ACR/ACA Accounting, 272=CCR/CCA Credit Control, 280=DWR/DWA Device-Watchdog, 318=Authentication-Information-Request on S6a). Result codes indicate success (2001=DIAMETER_SUCCESS) or failure (3xxx=protocol errors, 4xxx=transient failures, 5xxx=permanent failures). Know which command codes are critical for your subscribers — on an LTE network, CCR/CCA on Gx controls policy enforcement, and AIR/AIA on S6a controls subscriber authentication.
- Splunk license headroom: Diameter signaling generates approximately 1–2 KB per transaction. A mobile core serving 1 million subscribers typically produces 5–50 million Diameter transactions/day ≈ 5–100 GB/day depending on subscriber activity and poll intervals. The Stream Forwarder can filter to specific command codes or application IDs to reduce volume.
- Index: create a dedicated index `index=telecom_diameter` or use a broader `index=stream`. Configure the Stream app to route `sourcetype=stream:diameter` to your chosen index.

### Step 1 — Configure data collection
In the Splunk Stream app UI, navigate to Configuration > Streams > New Stream. Create a Diameter stream:

| Setting | Value |
|---------|-------|
| Protocol | Diameter |
| Name | `diameter_core_signaling` |
| Sourcetype | `stream:diameter` (default) |
| Index | `telecom_diameter` |
| Fields | Enable all: `command_code`, `result_code`, `origin_host`, `origin_realm`, `destination_host`, `destination_realm`, `application_id`, `session_id`, `auth_application_id`, `acct_application_id`, `hop_by_hop_id`, `end_to_end_id` |
| Filters | Optional: limit to specific application_id values if you only need certain interfaces (e.g. `application_id in [16777251, 16777238, 4]` for S6a + Gx + Gy) |

Deploy the stream configuration to the Stream Forwarder. Verify the forwarder is receiving traffic:
```spl
index=telecom_diameter sourcetype="stream:diameter" earliest=-15m
| stats count by command_code, application_id
```
You should see rows for each active Diameter interface. Common command_code values: 257 (CER/CEA — peer capability exchange, fires on connection setup), 280 (DWR/DWA — keepalive watchdog, fires every 30s per peer), 272 (CCR/CCA — credit control, fires per session), 318 (AIR/AIA — authentication on S6a).

Verify field extraction quality:
```spl
index=telecom_diameter sourcetype="stream:diameter" earliest=-15m
| fieldsummary
| where field IN ("command_code", "result_code", "origin_host", "application_id", "session_id")
| table field count distinct_count
```
All key fields should have non-zero counts. If `result_code` is missing, the Stream Forwarder may not be seeing the response messages (only requests) — verify that the mirror captures both directions.

Expected volume: DWR/DWA (code 280) generates the most messages (one per peer pair every 30 seconds). For health monitoring, you may want to filter these out in the stream configuration or in SPL to focus on transactional codes (271, 272, 318).

### Step 2 — Create the search and alert

**Primary search — Success rate by command code and application (15-min alert):**
```spl
index=telecom_diameter sourcetype="stream:diameter" earliest=-15m
| where command_code!=280
| stats count as total sum(eval(if(result_code==2001, 1, 0))) as successful by command_code, application_id, origin_host
| eval failed=total-successful
| eval success_rate=round(successful*100/total, 2)
| where success_rate < 99 OR failed > 10
| eval app_name=case(application_id==16777251, "S6a (HSS)", application_id==16777238, "Gx (PCRF)", application_id==4, "Gy/Rf (Charging)", application_id==0, "Base", 1==1, "App-".application_id)
| eval cmd_name=case(command_code==271, "Accounting", command_code==272, "Credit-Control", command_code==318, "Auth-Info", command_code==257, "Capability-Exchange", 1==1, "Cmd-".command_code)
| table origin_host, app_name, cmd_name, total, successful, failed, success_rate
| sort success_rate
```

#### Understanding this SPL: We exclude DWR/DWA (code 280) keepalives because they are infrastructure-level and would dilute the success rate of subscriber-facing transactions. Result code 2001 is DIAMETER_SUCCESS — anything else is a failure. We group by `command_code`, `application_id`, and `origin_host` to pinpoint exactly which peer and which transaction type is failing. The `case()` eval translates numeric codes into human-readable names so operators who are not Diameter experts can triage. A success rate below 99% on subscriber-facing interfaces (S6a, Gx) likely means active subscriber impact.

**Failure breakdown — drill into specific error codes:**
```spl
index=telecom_diameter sourcetype="stream:diameter" result_code!=2001 earliest=-1h
| where command_code!=280
| eval error_class=case(result_code>=5000, "Permanent (5xxx)", result_code>=4000, "Transient (4xxx)", result_code>=3000, "Protocol (3xxx)", 1==1, "Other")
| eval error_name=case(result_code==3002, "UNABLE_TO_DELIVER", result_code==3004, "TOO_BUSY", result_code==4010, "END_USER_SERVICE_DENIED", result_code==5003, "AUTHENTICATION_REJECTED", result_code==5012, "UNABLE_TO_COMPLY", result_code==5030, "USER_UNKNOWN", 1==1, "Code-".result_code)
| stats count by result_code, error_name, error_class, command_code, origin_host
| sort -count
```

#### Understanding this SPL: This drills into failures to identify the specific error pattern. DIAMETER_UNABLE_TO_DELIVER (3002) typically means a Diameter peer is unreachable — check routing. DIAMETER_TOO_BUSY (3004) indicates overload. DIAMETER_AUTHENTICATION_REJECTED (5003) could be an HSS data issue or a mass SIM fraud event. DIAMETER_USER_UNKNOWN (5030) at scale could indicate a number portability or provisioning error. Grouping by `origin_host` identifies the specific network element generating errors.

**Trending — success rate over time per interface:**
```spl
index=telecom_diameter sourcetype="stream:diameter" earliest=-24h
| where command_code!=280
| bin _time span=15m
| stats count as total sum(eval(if(result_code==2001, 1, 0))) as successful by _time, application_id
| eval success_rate=round(successful*100/total, 2)
| eval app_name=case(application_id==16777251, "S6a", application_id==16777238, "Gx", application_id==4, "Gy", 1==1, "Other")
| timechart span=15m avg(success_rate) by app_name
```

#### Understanding this SPL: 24-hour trending with 15-minute granularity reveals patterns — dips during peak hours suggest capacity issues, sustained drops indicate persistent faults, and sudden cliffs indicate outages. The per-interface split (S6a, Gx, Gy) shows which signaling plane is affected.

Schedule as Alert: the primary success rate search runs every 15 minutes. Trigger when any row has `success_rate < 95` (subscriber impact likely). Throttle by `origin_host` for 1 hour. For critical severity: trigger when `success_rate < 90` for any S6a or Gx row.

### Step 3 — Validate
(a) Compare transaction counts: on the HSS/PCRF/OCS element management system (EMS), pull Diameter transaction statistics for the same 15-minute window. The total request count per command code should match `| stats count by command_code` in Splunk within 5%. If Splunk shows significantly fewer, the mirror may be dropping packets at high volume or missing one direction.

(b) Verify result code distribution: on the HSS console, check the error rate for AIR (Authentication-Information-Request). If the EMS shows 0.1% failure rate and Splunk shows 2%, some failure responses may be arriving from a different Diameter peer not in your mirror scope. Expand the mirror to include all Diameter links.

(c) Confirm application_id mapping: run `| stats dc(origin_host) by application_id` and verify each application_id maps to the expected set of peers. If application_id values don't match your core design, the Stream protocol parser may be misidentifying some traffic — check the Diameter AVP parsing in Stream's protocol configuration.

(d) Validate origin_host names: Diameter `origin_host` should be the FQDN of the Diameter peer (e.g. `hss01.example.com`, `pcrf01.example.com`). If you see IP addresses instead, the Diameter peer may not be setting the Origin-Host AVP correctly, or the Stream parser may not be extracting it.

(e) Test alert routing: temporarily lower the threshold to 99.5% (which should trigger on normal traffic) and verify the alert fires, routes to the correct NOC channel, and includes the relevant fields.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Mobile Core — Diameter Signaling Health"):
- Row 1 — Single-value tiles: "Overall success rate" (green >99%, yellow 95–99%, red <95%), "Total Diameter TPS" (transactions per second), "Active peers" (dc of origin_host), "Error count (1h)" (red if >0).
- Row 2 — Timechart: success rate trend over 24h by Diameter interface (S6a, Gx, Gy), with 15-min span. Reference line at 99% threshold.
- Row 3 — Two panels: (left) failure breakdown table by error code, name, and peer; (right) peer health table showing success rate per origin_host.
- Row 4 — Top error codes as pie chart, and DWR/DWA watchdog health (peers that stop sending watchdogs are about to disconnect).

Alerting:
- Critical (success_rate < 95% on S6a or Gx): page NOC and core network team immediately — subscriber authentication or policy enforcement is failing. Millions of subscribers may be unable to attach or use data services.
- Warning (success_rate < 99% or specific error code spike): ticket to core network team with 1-hour SLA.
- Informational (peer disconnect detected via missing DWR/DWA): alert core network team — a peer disconnect precedes transaction failures.

Runbook (owner: Mobile Core / Packet Core Engineering):
1. **S6a failure (HSS)**: AIR/AIA failures mean subscribers cannot authenticate. Check HSS process status, database connectivity, and subscriber data integrity. If `result_code=5030` (USER_UNKNOWN), check provisioning for the affected IMSI range. If `result_code=3002` (UNABLE_TO_DELIVER), check Diameter routing agent (DRA) and network path to the HSS.
2. **Gx failure (PCRF)**: CCR/CCA failures mean policy cannot be applied — subscribers may get default/restricted service. Check PCRF cluster health, SPR (Subscriber Profile Repository) connectivity, and policy rule configuration. Overload (3004) suggests the PCRF needs horizontal scaling.
3. **Gy/Rf failure (Charging)**: Accounting failures impact billing accuracy. If prepaid subscribers are affected, they may lose service. Check OCS/OFCS availability and database capacity.
4. **Peer disconnect (missing DWR/DWA)**: A Diameter peer that stops responding to watchdog requests will be marked as unavailable by the DRA. Check the peer's process status, TCP/SCTP connectivity, and certificate validity (if TLS is used on the Diameter link).

### Step 5 — Troubleshooting

- **No events in `stream:diameter`** — The Stream Forwarder may not be seeing Diameter traffic. Verify the mirror/tap is configured correctly: Diameter uses SCTP (port 3868) or TCP (port 3868). If the mirror only captures TCP, SCTP-based Diameter links will be invisible. Also confirm the Diameter stream is enabled and deployed in the Stream app UI (Configuration > Streams).

- **Only request messages, no responses (result_code is always null)** — The mirror is capturing only one direction. Diameter is a request/response protocol — you need both directions to see result codes. Reconfigure the SPAN/mirror to capture both ingress and egress on the Diameter-facing interface.

- **DWR/DWA flooding the index** — Diameter watchdog messages (code 280) fire every 30 seconds per peer pair. With 20 peers, that is 40 DWR/DWA per minute = 57,600/day. Filter them in the stream configuration (add a filter `command_code != 280`) or in SPL. They are useful for peer liveness monitoring but not for signaling health.

- **application_id shows as 0 for all events** — This can happen if the Stream parser does not extract the application-specific AVPs. Check the Splunk Stream version — older versions may not fully parse all Diameter application IDs. Upgrade to Stream 8.0+ which has improved Diameter protocol support.

- **Success rate appears low but EMS shows no issues** — Check whether the Splunk search time range includes a maintenance window or a peer restart (which generates transient failures). Also check for duplicate events caused by mirror misconfiguration (same packet captured twice).

## SPL

```spl
sourcetype="stream:diameter"
| stats count by command_code, result_code, origin_host, application_id
| eval status=if(result_code==2001, "Success", "Failure")
| stats sum(eval(if(status=="Success", 1, 0))) as successful, sum(eval(if(status=="Failure", 1, 0))) as failed by command_code, application_id
| eval success_rate=round(successful*100/(successful+failed), 2)
| where failed>0 OR success_rate<99
```

## Visualization

Single value (overall Diameter success rate with color-coded threshold: green >99%, yellow 95-99%, red <95%), Pie chart (failure breakdown by command_code), Table (origin_host, command_code, result_code, count — sortable), Line chart (success rate trend over 24h with 15-min buckets).

## Known False Positives

Planned Diameter work, HSS profile pushes, and roaming test campaigns can depress success rates in narrow windows. Compare to the PCRF and STP maintenance calendar.

## References

- [Splunkbase — Splunk App for Stream](https://splunkbase.splunk.com/app/1809)
