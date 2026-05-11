<!-- AUTO-GENERATED from UC-5.18.8.json — DO NOT EDIT -->

---
id: "5.18.8"
title: "Traffic Engineering Re-Optimization Events"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.18.8 · Traffic Engineering Re-Optimization Events

> **Criticality:** Medium &middot; **Difficulty:** Expert &middot; **Pillar:** Observability &middot; **Type:** Change, Performance, Operations &middot; **Wave:** Run &middot; **Status:** Verified

*We notice when the backbone suddenly redraws its detour maps over and over because roads closed or weights changed. Seeing the flurry helps crews tell normal tweaks from a messy pile-up.*

---

## Description

Splunk detects bursts of MPLS traffic-engineering reoptimization—whether from CSPF recomputation, metric churn, or bandwidth advertisement updates—so transient tunnel reroutes become measurable incidents instead of invisible controller churn.

## Value

Optical and IP operations gain shared situational awareness because Splunk correlates TE reroute storms with underlying fiber hits or metric manipulation, preventing duplicate escalations when CE complaints lag core stabilization.

## Implementation

Tune syslog to capture TE subsystem informational messages during business hours pilot, baseline normal CSPF frequency per POP, alert when five-minute bucket exceeds rolling median ×4 joined with ISIS metric events.

## Detailed Implementation

### Prerequisites
- Maintenance calendar tagging planned optical works impacting metrics.
- Baseline median TE messages per hour derived from thirty-day summary index.

### Step 1 — Vendor logging alignment
IOS-XR: enable MPLS TE logging for auto-bandwidth and reoptimization paths sparingly to avoid flooding—sample via discriminators. Junos: route `rpd` TED updates at notice level.

### Step 2 — SPL anomaly layer
Use `streamstats` over `_time` to compute Z-score on `count`; hybrid alert uses absolute threshold OR statistical spike.

### Step 3 — Correlation join
Subsearch pulling ISIS metric change events within ±120s window stitched via `transaction host maxspan=120s`.

### Step 4 — CLI validation
Validate Splunk spike against `show isis database verbose` TE TLV shifts and `show mpls traffic-eng tunnels` reroute counters.

### Step 5 — Governance
Monthly review with optical NOC calibrates thresholds; document vendor bugs where false CSPF loops occurred.

## SPL

```spl
index=network earliest=-24h@h latest=now
| eval msg=lower(_raw)
| eval te_evt=match(msg,"(?:reoptim|re.?optim|cspf|(?:ted|traffic.?engineering).*(?:spf|recalc|update)|mpls.?te.*(?:recalc|metric.?chang)|tunnel.*(?:reroute|path.?chang)|(?:igp|isis|ospf).*(?:metric|te).*(?:chang|update)|(?:bandwidth).*(?:avail|update).*tunnel)")
| where te_evt=1
| rex field=_raw max_match=0 "(?i)(?:tunnel.?id|tunnel)\s*[:=]?\s*(?<tunnel_id>[0-9]+)"
| rex field=_raw max_match=0 "(?i)(?:metric|cost)\s*[:=]?\s*(?<metric>[0-9]+)"
| bin _time span=5m
| stats count values(metric) as metrics dc(tunnel_id) as tunnels_affected by _time host
| where count>=5 OR tunnels_affected>=3
| sort _time host
```

## Visualization

Dashboard Studio: timeline of TE events overlaid with ISIS metric deltas; bubble chart sized by `tunnels_affected`; drilldown raw `_raw` panel.

## Known False Positives

**Periodic auto-bandwidth adjustments:** weekly timers mimic outage churn—whitelist schedules.**Metric micro-flaps:** sub-second changes invisible to Splunk buckets aggregate oddly.**Log verbosity toggles:** engineering debugging spikes counts—tag source IPs.**Multi-instance ISIS:** messages lacking instance ID ambiguous—extract NET.**Telemetry-only TE:** silent syslog environments require alternate signals.

## References

- [Cisco IOS XR ISIS Configuration Guide — MPLS TE Extensions](https://www.cisco.com/c/en/us/)
- [Juniper RSVP and Traffic Engineering User Guide](https://www.juniper.net/documentation/us/en/software/junos/mpls/)
- [IETF RFC 3630 — Traffic Engineering Extensions for OSPF](https://www.rfc-editor.org/rfc/rfc3630)
