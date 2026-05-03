<!-- AUTO-GENERATED from UC-5.18.3.json — DO NOT EDIT -->

---
id: "5.18.3"
title: "RSVP-TE Tunnel State and Bandwidth Reservation"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.18.3 · RSVP-TE Tunnel State and Bandwidth Reservation

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We track when reserved highway lanes on our backbone fail to open or get bumped by higher-priority trucks. That helps planners see squeezes before promised speeds to customers quietly shrink.*

---

## Description

Splunk aggregates RSVP-TE signaling failures, bandwidth shortage messages, and telemetry snapshots so constrained TE trunks and preemption storms become visible before admission control blocks new wholesale circuits.

## Value

Planning and NOC teams defend committed information rates on constrained bundles because Splunk highlights when reservations fail, priorities preempt lower classes, or tunnel bandwidth diverges from engineered DS-TE templates.

## Implementation

Combine syslog RSVP errors with periodic telemetry pulls of tunnel bandwidth; normalize Mbps; alert on INSUFFICIENT_RESOURCES strings or when telemetry shows allocated bandwidth exceeding interface policy caps minus headroom.

## Detailed Implementation

### Prerequisites
- DS-TE / TE-class policies documented with numeric priorities and interface maximum reservable bandwidth.
- Tunnel naming convention encoded in lookup `te_tunnel_inventory.csv` with endpoints and CIR.

### Step 1 — Instrument RSVP failures
Enable MPLS TE syslog at severity capturing `%ROUTING-RSVP-4-*` style insufficient bandwidth and preemption notifications on Cisco; Junos `traceoptions` only where syslog bridging exists—prefer telemetry for steady-state.

### Step 2 — Telemetry normalization
For IOS-XR OpenConfig or native sensor paths, map `tunnel-name`, `signaled-bandwidth`, `state`; land JSON with sourcetype `telemetry:mpls`. Juniper network-agent subscriptions similar.

### Step 3 — Saved correlation
Search `rsvp_te_bw_reserve_issues`: failure syslog OR `(bw_mbps > nominal_cap_mbps * 0.95)` joined via lookup on `tunnel_id`.

### Step 4 — Validation
During lab admission tests, attempt tunnel setup exceeding RSVP maximum—ensure Splunk captures RSVP PathErr reason code matching CLI `show rsvp reservation`.

### Step 5 — Visualization & governance
Executive dashboard shows top congested POP pairs; monthly review tunes thresholds against upgrade Capex triggers.

## SPL

```spl
index=network earliest=-24h@h latest=now
| eval st=lower(coalesce(sourcetype,_sourcetype,""))
| eval msg=lower(_raw)
| eval rsvp_te=match(msg,"rsvp") AND match(msg,"(?:tunnel|ero|explicit|rro|soft.?preempt|bandwidth|bw|reservation|ero.?hop|session.*(?:fail|error)|(?:path|resv).*(?:err|tear))")
| where rsvp_te=1 OR match(st,"telemetry") AND match(msg,"\"tunnel\"|mpls.?te|traffic.?eng")
| rex field=_raw max_match=0 "(?i)bandwidth[^0-9]*(?<bw_kbps>[0-9]+)\s*(kbps|kb/s)?"
| rex field=_raw max_match=0 "(?i)(?:tunnel.?id|tunnel)\s*[:=]?\s*(?<tunnel_id>[0-9]+)"
| rex field=_raw max_match=0 "(?i)(?:setup|hold).*priority[^0-9]*(?<prio>[0-7])"
| stats values(msg) as sample_messages latest(bw_kbps) as last_bw latest(prio) as last_prio count by host tunnel_id
| eval bw_mbps=round(if(isnotnull(last_bw),tonumber(last_bw)/1024,null()),2)
| sort - count
```

## Visualization

Dashboard Studio: KPI row for tunnels with reservation failures; dual-axis timechart of signaled bandwidth vs interface cap; table (`host`, `tunnel_id`, `bw_mbps`, `sample_messages`) with severity coloring.

## Known False Positives

**Soft preemption notifications:** informational churn during priority reshuffles.**Telemetry skew:** sensor lag vs syslog instantaneous failure—prefer syslog for truth on admission.**Shared tunnel IDs:** local significance only—must pair with `host` or global ID lookup.**False bandwidth peaks:** burst smoothing absent—apply five-minute average post-process.**IPv6 TE:** parsers tuned for IPv4 ERO strings may miss IPv6 formatted hops.

## References

- [Cisco IOS XR Traffic Engineering Configuration Guide](https://www.cisco.com/c/en/us/td/docs/iosxr/asr9000/ip-addresses-and-services/b-ip-addresses-and-services-configuration-guide-asr9000-xr/traffic-engineering.html)
- [Juniper RSVP User Guide — MPLS Traffic Engineering](https://www.juniper.net/documentation/us/en/software/junos/mpls/topics/example/rsvp-traffic-engineering-configuring.html)
- [IETF RFC 3209 — RSVP-TE Extensions](https://www.rfc-editor.org/rfc/rfc3209)
