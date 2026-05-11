<!-- AUTO-GENERATED from UC-5.18.7.json — DO NOT EDIT -->

---
id: "5.18.7"
title: "MPLS OAM / LSP Ping and Traceroute Failures"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.18.7 · MPLS OAM / LSP Ping and Traceroute Failures

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Fault, Availability, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We send tiny test postcards along the same hidden tracks big traffic uses. When postcards bounce or vanish, we know the track is cracked even if the loudspeaker still says everything is fine.*

---

## Description

Splunk aggregates MPLS Operations-and-Management probe failures—from CLI-driven LSP pings to SBFD session drops—so passive syslog silence breaks when proactive validation proves unreachable or mis-forwarded FECs despite seemingly stable RSVP adjacencies.

## Value

Advanced assurance teams shorten stubborn ticket investigations because Splunk timestamps synthetic proof of broken dataplane labels alongside correlated RSVP/LDP neighbor logs instead of relying on subjective CLI screenshots.

## Implementation

Schedule scripted probes every five minutes per critical wholesale pseudowire/FEC list, wrap stderr/stdout as JSON to Splunk, dedupe by FEC hash, alert after three consecutive probe failures.

## Detailed Implementation

### Prerequisites
- Secure credential vault accessible to universal forwarder service account.
- FEC inventory prioritized by revenue tier.

### Step 1 — Probe command baseline
Cisco IOS-XR: `ping mpls ipv4 <fec> repeat 5`; Junos: `ping mpls rsvp <lsp-name> count 5`; Nokia: equivalent `oam` test commands per TIMOS release docs.

### Step 2 — Wrapper script
Python wrapper captures return codes, latency stats, and timestamps; ships via HEC with sourcetype `mpls:oam_probe`.

### Step 3 — Splunk transforms
Set `TIMESTAMP_FIELDS` for JSON `probe_ts`; map `fec`, `lsp_name`, `forwarding equivalence class` identifiers consistently.

### Step 4 — Validation
Induce failure by shutting passive interface in lab—ensure three consecutive failures trigger alert while single jitter drop does not.

### Step 5 — Documentation
Publish operator playbook linking Splunk alert to recommended `traceroute mpls` depth parameters and PE isolation tests.

## SPL

```spl
index=network earliest=-24h@h latest=now
| eval msg=lower(_raw)
| eval oam=match(msg,"(?:lsp.?ping|mpls.?ping|mpls.?trace|traceroute.?mpls|oam|bfd.*(?:mpls|lsp)|sbfd.*(?:discriminator|mpls)|mpls.?tp|y\.1731|eth.?cfm|cv.?cc)")
| eval fail=match(msg,"(?:fail|timeout|no.?reply|rtt.*(?:exceed|miss)|loss.*(?:100|[89][0-9])|malformed|misconnected|(?:down|alarm).*mpls)")
| where oam=1 AND fail=1
| rex field=_raw max_match=0 "(?i)(?:fec|prefix)\s*[:=]?\s*(?<fec>[0-9./:]+)"
| rex field=_raw max_match=0 "(?i)(?:tunnel|lsp)\s*[:=]?\s*(?<lsp_name>[^\s,]+)"
| rex field=_raw max_match=0 "(?i)(?:router.?id|ingress)\s*[:=]?\s*(?<ingress>[0-9.]+|[0-9a-f:]+)"
| stats count earliest(_time) as first_seen latest(_time) as last_seen values(fec) as fecs values(lsp_name) as lsps by host sourcetype
| sort - count
```

## Visualization

Dashboard Studio: KPI for failing FECs; timeline colored by severity; map panel keyed by site lookup showing impacted POP pairs.

## Known False Positives

**ICMP suppression:** some hops drop TTL-expired replies yet dataplane fine—pair with LFIB checks.**CPU-driven delay:** slow RE spikes RTT—threshold adaptive.**Multi-segment pseudowires:** misconfigured FEC strings cause repetitive noise until inventory corrected.**Scheduler overlap:** cron collisions duplicate failures—dedupe `fec+minute`.**IPv6 vs IPv4 FEC:** mismatched family yields false failure.

## References

- [Cisco IOS XR MPLS OAM Configuration Guide](https://www.cisco.com/c/en/us/)
- [Juniper MPLS Applications User Guide — MPLS Ping and Traceroute](https://www.juniper.net/documentation/us/en/software/junos/mpls/)
- [IETF RFC 6428 — MPLS On-Demand Connectivity Verification](https://www.rfc-editor.org/rfc/rfc6428)
