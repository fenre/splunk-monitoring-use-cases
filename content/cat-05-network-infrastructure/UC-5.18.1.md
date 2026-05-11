<!-- AUTO-GENERATED from UC-5.18.1.json — DO NOT EDIT -->

---
id: "5.18.1"
title: "LSP (Label Switched Path) State Changes and Failures"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.18.1 · LSP (Label Switched Path) State Changes and Failures

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault, Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch the carrier backbone’s special fast lanes so when one tears down or flips to a backup, we know right away. That way crews fix breaks before customers only notice silent slowdowns or dropped priority traffic.*

---

## Description

Splunk correlates MPLS and RSVP syslog streams so operator-visible label-path transitions, teardowns, protection switchovers, and signaling errors surface within minutes instead of waiting on customer trouble tickets after silent reroutes exhaust backup capacity.

## Value

Transport leadership keeps SLA-backed wholesale and enterprise circuits trustworthy because engineering sees primary LSP loss, backup activation, and RSVP/MBB churn before throughput collapses or latency budgets breach during fiber or node incidents.

## Implementation

Land PE syslog with severity ≥informational for RSVP-TE and MPLS subsystems, normalize tunnel/LSP identifiers, schedule the search every five minutes for spikes by host, and route alerts to the carrier NOC with topology context.

## Detailed Implementation

### Prerequisites
- Inventory mapping `host` to POP, role (P/PE), software train (IOS-XE, IOS-XR, Junos, SR OS), and maintenance windows.
- Clock sync (PTP/NTP) verified so `_time` aligns with EMS correlators.

### Step 1 — Enable verbose MPLS/RSVP logging
On Cisco IOS-XR: `logging events level informational` under MPLS TE if policy allows; capture `%ROUTING-RSVP-*`, `%MPLS_*-TE-*`, and BFD session logs for TE tunnels. On Junos: commit `set protocols rsvp traceoptions file rsvp.log size 10m files 5` plus `set protocols mpls traceoptions file mpls.log` in lab first, then tune flag severity for production syslog export. On Nokia SR OS: enable `log syslog` for TIMOS MPLS/RSVP facility at `major` default, escalate `critical` for tunnel-down.

### Step 2 — Ingest and parse
Forward to Splunk via TCP syslog or HEC; in `props.conf` assign `LINE_BREAKER` for multi-line IOS-XR messages; extract `tunnel-id`, endpoint addresses, and `lsp-name` with vendor TA extractions or supplemental `REPORT-mpls_lsp` transforms.

### Step 3 — Saved search
Save SPL as `mpls_lsp_state_failures_24h`; alert when `count`≥3 distinct failures per `host` in fifteen minutes or when message matches explicit “tunnel down” without matching suppress lookup `mpls_maintenance.csv`.

### Step 4 — Validate
During a controlled ISIS metric tweak in lab, compare Splunk event timestamps to `show mpls traffic-eng tunnels brief` / `show rsvp session` / Junos `show mpls lsp extensive` / Nokia `show router rsvp session`; discrepancies >60s imply buffering or timezone skew.

### Step 5 — Operationalize
Dashboard: timeline by POP, drilldown to raw `_raw`; annotate planned fiber events via lookup-driven suppression; weekly review false-positive regex tuning with SME sign-off.

## SPL

```spl
index=network earliest=-24h@h latest=now
| eval st=lower(coalesce(sourcetype,_sourcetype,""))
| where match(st,"cisco:ios|cisco:ios_xr|cisco:ios_xe|juniper:junos|nokia:sros|nokia")
| eval msg=lower(_raw)
| eval hit=case(
    match(msg,"lsp.*down|lsp.*removed|mpls.*lsp.*(?:fail|error)|tunnel.*(?:down|tear)|rsvp.*(?:path.*(?:error|tear)|session.*down)|signalling.*interrupted|backup.*active|primary.*(?:fail|switch)|fast.?reroute|sbfd.*(?:down|fail)|bfd.*(?:mpls|tunnel).*down"),1,
    match(msg,"(?:mpls.?te|traffic.?eng).*tunnel.*(?:chang|state|down|up)") AND match(msg,"(?:chang|transition|state|down|up|fail)"),1,
    match(msg,"ldp.*(?:lsp|fec).*") AND match(msg,"(?:withdraw|delete|fail|down)"),1,
    match(msg,"junos.*(?:lsp|rsvp|mpls).*") AND match(msg,"(?:down|fail|error|tear|switchover)"),1,
    match(msg,"(?:7750|timos|sros).*?(?:lsp|tunnel|mpls).*") AND match(msg,"(?:down|fail|clear|major|critical)"),1,
    0)
| where hit=1
| rex field=_raw max_match=0 "(?i)(?:tunnel|lsp|pw)\s*[:=]?\s*(?<lsp_name>[^\s,]+)"
| rex field=_raw max_match=0 "(?i)(?:fec|prefix)\s*[:=]?\s*(?<fec>[0-9./:]+)"
| rex field=_raw max_match=0 "(?i)vrf[_:\s]+(?<vrf>[^\s,]+)"
| stats count earliest(_time) as first_seen latest(_time) as last_seen values(lsp_name) as lsps values(fec) as fecs values(vrf) as vrfs by host st
| where count>=1
| sort - count
```

## Visualization

Dashboard Studio: KPI row for PEs with LSP failures in 24h; middle `splunk.timechart` of event count by `host`; bottom table (`host`, `st`, `lsps`, `fecs`, `first_seen`, `last_seen`) with drilldown to verbose messages.

## Known False Positives

**Graceful shutdown / MBB:** RSVP PathErr messages during make-before-break look like failures.**Aggressive regex:** generic "tunnel" strings may match GRE or IPsec constructs—tighten `st` filter.**Log flooding:** informational RSVP churn during reconvergence spikes counts; throttle with `bucket` window.**Secondary paths:** intentional switch to backup may page unless correlated with circuit maintenance.**Telemetry duplication:** if both syslog and gNMI fire, dedupe on `(host,lsp_name,_time)`.

## References

- [Cisco IOS XR MPLS Configuration Guide — MPLS Traffic Engineering](https://www.cisco.com/c/en/us/)
- [Juniper MPLS Applications User Guide — RSVP Signaling](https://www.juniper.net/documentation/us/en/software/junos/mpls/)
- [Nokia InfoProducts — SR OS documentation portal](https://infoproducts.nokia.com/)
