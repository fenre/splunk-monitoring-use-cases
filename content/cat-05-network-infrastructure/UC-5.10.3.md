<!-- AUTO-GENERATED from UC-5.10.3.json — DO NOT EDIT -->

---
id: "5.10.3"
title: "Mobile Subscriber RADIUS Session Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.3 · Mobile Subscriber RADIUS Session Tracking

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability

*We use the carrier’s session history to see how long people stay online and where traffic piles up, so the mobile team can add capacity before sites overload.*

---

## Description

Tracks active mobile subscriber sessions via RADIUS accounting, providing visibility into session duration, data volume, and SGSN/MCC-MNC distribution — critical for mobile core capacity planning and roaming analytics.

## Value

Core network teams detect SGSN failures (sudden subscriber drops), identify roaming traffic patterns for partner SLA management, and provide capacity planning with session-level visibility across the packet core.

## Implementation

Configure Splunk App for Stream to capture RADIUS accounting traffic from the mobile packet core (GGSN/PGW). Enable RADIUS protocol extraction including the telco-specific fields `sgsn_address` and `sgsn_mcc_mnc`. Use `code="Accounting-Request"` to filter for accounting records. Correlate `start_time` and `stop_time` for session duration. The `sgsn_mcc_mnc` field identifies the serving network (home vs. roaming). Alert on sudden drops in active sessions per SGSN.

## Detailed Implementation

### Prerequisites
- Splunk App for Stream (Splunkbase 1809) v8.0+ with the Stream Forwarder deployed on a mirror/tap capturing RADIUS traffic between the GGSN/PGW and the AAA server (typically on UDP ports 1812/1813 or 1645/1646). RADIUS uses UDP — ensure the mirror captures both request and response directions.
- Understand the 3GPP RADIUS attributes relevant to mobile networks: `Acct-Status-Type` (Start=1, Stop=2, Interim-Update=3), `3GPP-SGSN-Address` (the SGSN/MME serving the subscriber), `3GPP-SGSN-MCC-MNC` (Mobile Country Code + Mobile Network Code identifying the serving PLMN — critical for roaming detection), `Calling-Station-Id` (MSISDN), `User-Name` (IMSI or NAI), `Acct-Session-Time` (session duration in seconds), `Acct-Input-Octets`/`Acct-Output-Octets` (byte counters).
- RADIUS accounting follows a session lifecycle: Accounting-Start when the PDP/PDN session is created, Interim-Update periodically during the session (interval configured on the GGSN/PGW, typically 15–60 minutes), and Accounting-Stop when the session ends. For session tracking, Start and Stop records are most important; Interim updates are useful for near-real-time visibility.
- Know your MCC-MNC codes: your home network has a specific MCC-MNC (e.g. `24201` for Norway Telenor). Any session with a different `sgsn_mcc_mnc` indicates roaming — the subscriber is attached to a visited network's SGSN/MME. Maintain a lookup `mcc_mnc_operators.csv` mapping codes to operator names for human-readable output.
- Index and license: create `index=telecom_radius` or use the existing `index=stream`. RADIUS accounting generates approximately 0.5–1 KB per record. Volume depends on session turnover and interim update interval.

### Step 1 — Configure data collection
In the Splunk Stream app, create a RADIUS stream:

| Setting | Value |
|---------|-------|
| Protocol | RADIUS |
| Name | `radius_mobile_accounting` |
| Filter | `code in ["Accounting-Request", "Accounting-Response"]` |
| Fields | `code`, `login` (User-Name/IMSI), `calling_station_id` (MSISDN), `acct_session_id`, `acct_status_type`, `sgsn_address`, `sgsn_mcc_mnc`, `start_time`, `stop_time`, `acct_session_time`, `acct_input_octets`, `acct_output_octets`, `framed_ip_address` |
| Sourcetype | `stream:radius` |
| Index | `telecom_radius` |

Verify data is arriving:
```spl
index=telecom_radius sourcetype="stream:radius" code="Accounting-Request" earliest=-15m
| stats count by sgsn_address
```
Each `sgsn_address` should correspond to an SGSN or MME in your mobile core. If you see no results, verify the mirror captures the RADIUS interface (Gi/SGi reference point).

Verify key field extraction:
```spl
index=telecom_radius sourcetype="stream:radius" code="Accounting-Request" earliest=-15m
| stats count dc(login) as unique_imsi dc(sgsn_address) as unique_sgsn values(sgsn_mcc_mnc) as mcc_mnc_seen
```
You should see your home MCC-MNC plus any roaming partner codes. If `sgsn_mcc_mnc` is null, the GGSN/PGW may not be including the 3GPP vendor-specific attributes in RADIUS — this requires 3GPP attribute support on the GGSN/PGW and correct Stream parser configuration.

### Step 2 — Create the search and alert

**Primary search — Active sessions per SGSN with roaming breakdown:**
```spl
index=telecom_radius sourcetype="stream:radius" code="Accounting-Request" earliest=-4h
| eval session_secs=if(isnotnull(stop_time) AND isnotnull(start_time), stop_time-start_time, acct_session_time)
| eval session_min=round(session_secs/60, 1)
| eval is_roaming=if(sgsn_mcc_mnc!="24201", "Roaming", "Home")
| stats count as sessions avg(session_min) as avg_duration_min dc(login) as unique_subscribers sum(eval(round((acct_input_octets+acct_output_octets)/1048576, 2))) as total_MB by sgsn_address, sgsn_mcc_mnc, is_roaming
| lookup mcc_mnc_operators.csv sgsn_mcc_mnc OUTPUT operator_name country
| eval operator_label=if(isnotnull(operator_name), operator_name." (".country.")", sgsn_mcc_mnc)
| sort -sessions
```

#### Understanding this SPL: We compute session duration from either the Start/Stop time delta or the `acct_session_time` AVP (whichever is available). The `is_roaming` flag identifies sessions where the serving SGSN belongs to a different PLMN than the home network (replace `24201` with your own MCC-MNC). The lookup translates MCC-MNC codes into readable operator names. This gives operations a view of session distribution across serving nodes and roaming partners — useful for detecting SGSN overloads, roaming anomalies, and capacity planning.

**Session drop detection — sudden decrease in active sessions per SGSN:**
```spl
index=telecom_radius sourcetype="stream:radius" code="Accounting-Request" earliest=-24h
| bin _time span=15m
| stats dc(login) as active_subs by _time, sgsn_address
| eventstats avg(active_subs) as avg_subs stdev(active_subs) as std_subs by sgsn_address
| eval lower_bound=avg_subs - (3 * std_subs)
| where active_subs < lower_bound AND active_subs < avg_subs*0.5
| eval drop_pct=round((1 - active_subs/avg_subs)*100, 1)
```

#### Understanding this SPL: Detects sudden drops in active subscribers on a specific SGSN/MME. A >50% drop in 15 minutes with statistical significance (3 sigma) likely indicates an SGSN crash, mass detach, or network partition. This is a critical operational signal — thousands of subscribers may have lost service.

**Roaming analytics — inbound and outbound roaming summary (daily):**
```spl
index=telecom_radius sourcetype="stream:radius" code="Accounting-Request" earliest=-24h
| eval roaming_type=case(sgsn_mcc_mnc=="24201", "Home", 1==1, "Inbound Roaming")
| stats dc(login) as subscribers count as sessions sum(eval(round((acct_input_octets+acct_output_octets)/1073741824, 3))) as total_GB by sgsn_mcc_mnc, roaming_type
| lookup mcc_mnc_operators.csv sgsn_mcc_mnc OUTPUT operator_name country
| sort -subscribers
```

#### Understanding this SPL: Daily summary of roaming activity by visiting network. The `sgsn_mcc_mnc` identifies which roaming partner's network the subscriber is attached to. High subscriber counts from a specific roaming partner may indicate tourism patterns, conference events, or a bilateral roaming agreement in heavy use. This is valuable for roaming revenue forecasting and partner SLA monitoring.

Schedule as Alert: the session drop detection runs every 15 minutes. Trigger when `drop_pct > 30` for any SGSN. Throttle by `sgsn_address` for 1 hour.

### Step 3 — Validate
(a) On the GGSN/PGW console or EMS, pull the active PDP/PDN context count per SGSN/MME. Compare to `| stats dc(login) by sgsn_address` in Splunk for the same time window. Counts should match within 15% — differences arise from session state timing and Stream capture completeness.

(b) Verify roaming detection: pick a known roaming subscriber (test SIM on a visited network) and confirm their sessions appear with the correct visiting `sgsn_mcc_mnc`. If all sessions show the home MCC-MNC, the 3GPP attributes may not be included in RADIUS messages.

(c) Validate session duration calculation: pick a specific `acct_session_id` and check that `session_min` matches the `stop_time - start_time` difference. If `stop_time` is always null, only Accounting-Start records are being captured — verify the mirror sees the full RADIUS conversation.

(d) Build and validate the `mcc_mnc_operators.csv` lookup: include at minimum your home MCC-MNC and your top 10 roaming partners. ITU maintains the official MCC-MNC registry — download and parse it into the lookup format.

(e) Cross-check data volumes: compare `total_MB` per SGSN against the PGW throughput counters. If Splunk shows significantly less, the Stream Forwarder may be dropping packets under load.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Mobile Core — RADIUS Session Analytics"):
- Row 1 — Single-value tiles: "Total active sessions", "Unique subscribers (4h)", "Roaming subscribers", "Average session duration (min)".
- Row 2 — Timechart: active subscriber count per SGSN over 24h (15-min buckets). Anomaly threshold line overlaid.
- Row 3 — Two panels: (left) Session distribution by SGSN/MME as column chart; (right) Roaming breakdown by MCC-MNC as pie chart with operator names.
- Row 4 — Table: sgsn_address, sgsn_mcc_mnc, operator_label, sessions, unique_subscribers, avg_duration_min, total_MB. Drilldown on SGSN to see per-subscriber session list.

Alerting:
- Critical (subscriber drop > 50% on any SGSN): page core network NOC immediately — potential SGSN crash or mass detach.
- Warning (subscriber count decreasing steadily over 4 hours): ticket for investigation — possible cell site issue feeding the SGSN.
- Informational (roaming subscriber count spike): notify roaming operations — may need capacity adjustment or partner notification.

Runbook (owner: Core Network / Packet Core Engineering):
1. **SGSN session drop**: Check SGSN/MME process status and connectivity. If the SGSN is unreachable, subscribers will re-attach to another SGSN — check if sessions shifted to a neighbor. If the SGSN crashed, check crash logs and escalate to vendor.
2. **Roaming anomaly**: If inbound roaming from a specific partner suddenly increases, check for a sporting event, conference, or tourism influx. If unexpected, verify with the roaming partner that the traffic is legitimate.
3. **Session duration anomaly**: If average session duration drops significantly, subscribers may be experiencing frequent disconnects and reconnects (PDP context churn). Check the RAN for cell issues and the GGSN for GTP-C errors.

### Step 5 — Troubleshooting

- **`sgsn_address` or `sgsn_mcc_mnc` fields are null** — These are 3GPP vendor-specific RADIUS attributes (VSA). Not all GGSN/PGW vendors include them by default. Check the GGSN/PGW configuration for "3GPP RADIUS attributes" or "vendor-specific attributes" and enable them. The Splunk Stream parser needs to be configured to extract VSAs — check the Stream protocol configuration.

- **Only Accounting-Start records, no Stop or Interim** — The mirror may be missing response traffic, or the GGSN/PGW may not be configured to send Interim-Update and Stop records. Check the GGSN accounting configuration and verify the AAA server is responding (no response = the GGSN may stop sending further records).

- **Session duration is zero or negative** — The `start_time` and `stop_time` fields may not be populated in RADIUS attributes. Use `acct_session_time` (Acct-Session-Time, attribute 46) as a fallback, which directly reports duration in seconds.

- **Duplicate session counts** — If the Stream Forwarder sees both RADIUS requests and responses, sessions may be double-counted. Filter to `code="Accounting-Request"` only (not Response) in the base search.

- **MCC-MNC lookup returns null for some codes** — Update the `mcc_mnc_operators.csv` lookup with the latest ITU MCC-MNC allocations. Some mobile virtual network operators (MVNOs) use non-standard codes that may not appear in the official registry.

## SPL

```spl
sourcetype="stream:radius" code="Accounting-Request"
| eval session_secs=stop_time-start_time
| eval session_min=round(session_secs/60, 1)
| stats count as sessions, avg(session_min) as avg_duration_min, dc(login) as unique_subscribers by sgsn_address, sgsn_mcc_mnc
| sort -sessions
```

## Visualization

Column chart (active sessions by SGSN address), Table (sgsn_address, sgsn_mcc_mnc, sessions, unique_subscribers, avg_duration_min — sortable), Timechart (session count over 24h), Pie chart (session distribution by MCC-MNC for roaming analysis).

## Known False Positives

Roaming tests, SGSN failovers, and mass handset reboots can swing session counts. Use carrier maintenance notices as context.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
