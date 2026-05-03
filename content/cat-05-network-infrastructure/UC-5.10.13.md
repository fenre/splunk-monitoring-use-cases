<!-- AUTO-GENERATED from UC-5.10.13.json — DO NOT EDIT -->

---
id: "5.10.13"
title: "PSTN Gateway Health (Analog/PRI/SIP Gateway Status)"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.10.13 · PSTN Gateway Health (Analog/PRI/SIP Gateway Status)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the old-style phone boxes that still turn digital calls into analog lines so when a card overheats or a cable bundle fails the right folks wake up before banks of phones go dead.*

---

## Description

Surfaces gateway-layer DSP exhaustion, PRI/CAS controller faults, MGCP registration losses, and glare/slip anomalies aggregated per fifteen minutes—covering legacy TDM interconnects that bypass pure SIP trunk dashboards.

## Value

Contact centers and rural aggregation networks retain revenue-bearing PSTN hops through ISR gateways; early DSP/PRI alerts prevent silent hairpin failures where SIP dashboards remain green while analog/E1 segments collapse.

## Implementation

Forward gateway logs with local clock discipline; classify gateways via CSV (`pstn_gateways.csv`); tune DSP thresholds against baseline busy-hour call counts; dual-feed SIP Stream where applicable for blended diagnostics.

## Detailed Implementation

### Prerequisites
- Cisco IOS voice logging severity tuned (avoid masking DSP traps behind buffered logging).
- Hardware inventory clarifying PVDM profiles and simultaneous call capacities per chassis.
- Physical PRI numbering plans mapped to syslog controller notation.
- Optional SNMP DIM extensions polling DSP utilization when syslog insufficient.

### Step 1 — Route gateway syslog into Splunk with minimal transforms stripping ANSI noise yet preserving facility codes.

### Step 2 — Maintain regex library per IOS train—15.x differs from 17.x strings—store macros `voice_gateway_errors`.

### Step 3 — Overlay lookup describing trunk_role (`sip_primary`, `pri_backup`) for smarter paging routes.

### Step 4 — Dashboard merges PRI status tiles with SIP Stream concurrent call counters toward same gateway cluster.

### Step 5 — Troubleshooting: fax/modem modem-pass-through spikes mimic DSP faults—cross-check `fax relay` counters; clock slips on E1 need telecom-team verification before blaming Splunk parsing.

## SPL

```spl
index=voice OR index=network ((sourcetype="cisco:ios" OR sourcetype="cisco:ios:voice")
    ("VTSP" OR "DSPRM" OR "DSP" OR "MGCP" OR "PRI" OR "D-channel" OR "%CALL_VOICE" OR "DS0" OR "CAS" OR "ISDN" OR "glare"))
| eval gw_host=host
| rex field=_raw "(?i)(?<voice_evt>DSP.*FAIL|DSP.*DOWN|PRI.*DOWN|D-channel.*down|MGCP.*timeout|VTSP.*ERROR|glare|slip)"
| eval critical_evt=if(isnotnull(voice_evt) OR match(_raw,"(?i)(?:DSP.*(?:fail|down)|PRI.*(?:DOWN)|Lost.*carrier|Controller.*down)"),1,0)
| bin _time span=15m
| stats count sum(critical_evt) as critical_hits values(voice_evt) as hints by _time gw_host
| where critical_hits>0 OR count>500
| lookup pstn_gateways.csv gw_host OUTPUT site pstn_carrier trunk_role
| table _time gw_host site pstn_carrier trunk_role critical_hits count hints
| sort -critical_hits
```

## Visualization

Gateway health matrix (site × trunk_role); sparklines of critical_hits; drilldown to raw syslog lines with highlighting.

## Known False Positives

Planned PRI cable swaps generate transient `Controller down` messages; fax storms elevate DSP usage legitimately; SNMP polling gaps mimic silence—verify trap heartbeat.

## References

- [Cisco IOS Voice Troubleshooting Guide — Gateway DSP and PRI](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/voice/cube/configuration/cube-book/vcube.pdf)
- [Splunkbase — Splunk App for Stream](https://splunkbase.splunk.com/app/1809)
