<!-- AUTO-GENERATED from UC-5.10.7.json — DO NOT EDIT -->

---
id: "5.10.7"
title: "SIP Trunk Health and Call Setup Success Rate"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.10.7 · SIP Trunk Health and Call Setup Success Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We count how many calls actually get through each outside line we buy so when one supplier quietly starts dropping setups we see it on a chart instead of hearing angry stories days later.*

---

## Description

Measures SIP INVITE outcomes across trunk endpoints every fifteen minutes to surface degraded carrier interconnect—few progress responses (180/183), elevated failure replies (4xx/5xx/6xx), and collapsing computed setup-success percentages versus baseline steady-state trunk behaviour.

## Value

Voice ops quantify trunk-by-trunk regression versus negotiated interconnect KPIs so carrier escalation happens from measurable SIP metrics rather than anecdotal complaints—often shortening dispute cycles because Splunk retains correlated timelines alongside ticketing IDs.

## Implementation

Point Stream at bilateral SIP signaling toward PSTN/SBC trunk IPs; normalize INVITE events into `telecom_sip`; attach trunk/carrier labels via lookup; schedule the fifteen-minute aggregation; tune minimum invites-per-window so sparse routes do not page falsely.

## Detailed Implementation

### Prerequisites
- Splunk App for Stream (Splunkbase 1809) 8.x forwarders tapping trunk-facing VLAN or ERSPAN with symmetric bidirectional captures so responses arrive with requests.
- Inventory CSV `sip_trunks.csv` mapping signaling endpoints (`dest_ip`), carrier-facing trunk_group identifiers, commercial carrier_name, and routing class (national/international/satellite) when thresholds differ.
- Written interconnect KPI targets from acceptance testing—many carriers quote combined setup-success objectives excluding intentionally busy subscribers; align SPL exclusions accordingly.
- Enough license capacity for sustained INVITE telemetry—historically multiple TB/day on busy PSTN breakout farms.

### Step 1 — Configure Stream SIP extraction focusing on `method=INVITE`. Validate `reply_code`, `call_id`, `dest`, `_time`, and `setup_delay` fields via fifteen-minute verification searches comparing counts against session border controller logs.

### Step 2 — Land events in `index=telecom_sip` with sourcetype `stream:sip`; automate lookup synchronization whenever trunk IPs change after migrations or wholesale resale rearrangements.

### Step 3 — Implement scheduled searches computing progressing_pct (share receiving 180/183/200 first-leg responses) and cs_sr_pct (share avoiding hard 4xx/5xx/6xx failures including canceled attempts). Require `invites>=50` per bucket to suppress noise on dormant routes; optionally stratify thresholds using lookup `call_type`.

### Step 4 — Operational dashboard couples KPI tiles, fifteen-minute trend charts per trunk_group, and Rapid Investigation drilldown launching raw events constrained by `call_id`. Tie Splunk alerts to ticketing via webhook carrying trunk_label and rolling averages.

### Step 5 — Troubleshooting: asymmetric taps yield artificial failures—validate ERSPAN ACL directionality; lab trunks should be filtered with explicit dest exclusions; when audio suffers despite healthy counters, pivot to UC-5.10.6 post-dial delay analytics and RTP loss panels.

## SPL

```spl
index=telecom_sip sourcetype="stream:sip" method="INVITE"
| bin _time span=15m
| stats count as invites,
        sum(eval(if(reply_code IN (180,183,200),1,0))) as progressing_ok,
        sum(eval(if((reply_code>=400 AND reply_code<700) OR reply_code IN (403,404,408,486,487,503,603),1,0))) as invite_failures,
        sum(eval(if(reply_code==487,1,0))) as canceled_before_answer,
        dc(call_id) as unique_sessions
        by _time, dest
| eval cs_sr_pct=round(100*(invites-invite_failures)/invites,2)
| eval progressing_pct=round(100*progressing_ok/invites,2)
| where invites>=50 AND (cs_sr_pct < 97 OR progressing_pct < 92)
| lookup sip_trunks.csv dest_ip as dest OUTPUT carrier_name trunk_group
| eval trunk_label=coalesce(carrier_name,dest)
| table _time trunk_label invites progressing_pct cs_sr_pct invite_failures canceled_before_answer
| sort -invite_failures
```

## Visualization

Row 1: single-value tiles per carrier for fifteen-minute CS-SR with traffic-light thresholds; Row 2: timechart of progressing_pct and cs_sr_pct stacked per trunk; Row 3: table of failures by SIP response code with drill to Stream packet capture IDs if stored.

## Known False Positives

Flash crowds dialing unreachable premium-rate ranges spike 404/486 counts legitimately; SIP OPTIONS heartbeats mis-tagged as INVITE if filters slip; carrier lawful-intercept reroutes may briefly emit 503 during provisioning—cross-check carrier notifications.

## References

- [Splunkbase — Splunk App for Stream](https://splunkbase.splunk.com/app/1809)
- [RFC 3261 — SIP: Session Initiation Protocol](https://www.rfc-editor.org/rfc/rfc3261)
