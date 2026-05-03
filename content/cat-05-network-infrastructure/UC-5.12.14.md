<!-- AUTO-GENERATED from UC-5.12.14.json — DO NOT EDIT -->

---
id: "5.12.14"
title: "SBC (Session Border Controller) Registration Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.14 · SBC (Session Border Controller) Registration Trending

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Security &middot; **Wave:** Crawl &middot; **Status:** Verified

*We track phones checking in with the border gatekeeper so we notice if they suddenly cannot log on, whether from a bad password rush or a broken security certificate.*

---

## Description

Measures SIP REGISTER attempt volumes, success ratios, and distinct endpoint footprint per SBC to expose credential attacks, TLS migration regressions, or registrar outages before phones mass-unregister.

## Value

Security and voice ops detect brute-force REGISTER storms, certificate rollover failures, or stale expiry timers early—preserving inbound reachability for BYOD softphones and SIP trunk survivability options.

## Implementation

Extract METHOD and response reliably via transforms; whitelist maintenance subnets; alert on fail_rate >5% over fifteen minutes or sudden 401/403 bursts; retain hashed AOR identifiers if privacy policy requires minimization.

## Detailed Implementation

### Prerequisites
- SIP syslog from each SBC cluster member with consistent timestamp source (prefer hardware clock).
- Dictionary mapping `host` → `site`, `carrier_proxy`, `tls_profile_version`.
- Understanding of normal registration refresh intervals (typically 300–3600 seconds).

### Step 1 — Normalize SIP events
Ensure REGISTER rows carry `sip_response_code`, `sip_method`, `contact`, `authorization_identity` if logged.

### Step 2 — Baseline steady state
Compute hourly median attempts per site; seasonal adjustments for retail handset rollouts.

### Step 3 — Detection logic
Alert when fifteen-minute failure ratio exceeds baseline + three sigma or absolute >8%; parallel threshold on distinct_contacts drop >40% indicating partial outage.

### Step 4 — Visualization
Stacked success vs failure over time; geomap of REGISTER sources when anomalies correlate to geography.

### Step 5 — Response
Validate TLS certificate expiry on SBC; replay PCAP subset if Stream enabled; coordinate with IdP if REGISTER carries OAuth-derived credentials.

Extended troubleshooting
Carrier-backed registrations may aggregate behind single Contact leading to low dc(contact)—switch KPI to unique Call-ID. NAT rebinding events mimic churn; compare UDP vs TCP transports separately.

## SPL

```spl
index=voip (sourcetype="sip:sbc" OR sourcetype="cisco:ios")
| search REGISTER
| eval success=if(match(sip_response_code,"^(200|202)$"),1,0)
| bin _time span=15m
| stats sum(success) as ok count as attempts dc(contact) as distinct_contacts by _time, host
| eval fail_rate=if(attempts>0, round(100*(attempts-ok)/attempts,2), 0)
| where fail_rate>5 OR attempts>1000
| sort _time
```

## Visualization

Timechart REGISTER attempts vs successes; single-value current fail_rate; top user_agent table for fingerprinting rogue scanners.

## Known False Positives

Certificate renewal cutovers cause brief 401/407 spikes until endpoints retry with new trust anchors; firmware refresh overnight forces mass reregistration resembling attack volume; geo-redundant SBC tests hammer synthetic REGISTER sources; SIP ALG misconfigurations duplicate attempts doubling counts without failures.

## References

- [RFC 3261 — SIP REGISTER refreshes overview](https://www.rfc-editor.org/rfc/rfc3261)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
