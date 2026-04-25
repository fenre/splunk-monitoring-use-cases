<!-- AUTO-GENERATED from UC-2.6.61.json — DO NOT EDIT -->

---
id: "2.6.61"
title: "Citrix HDX Rendezvous Protocol Path Selection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.61 · Citrix HDX Rendezvous Protocol Path Selection

## Description

HDX Rendezvous lets sessions establish through direct UDP paths with STUN when possible, and fall back to relayed transport when firewalls, symmetric NAT, or port blocks get in the way. A high relay ratio or STUN failure clusters often point to home-router settings, guest Wi-Fi, or data-center egress rules rather than the VDA image. Monitoring path selection, Rendezvous v2 adoption, and UDP blockage patterns helps the right team tune Gateway, DTLS, and client policy before remote users see chronic latency, dropped multimedia, and unstable Teams inside sessions.

## Value

HDX Rendezvous lets sessions establish through direct UDP paths with STUN when possible, and fall back to relayed transport when firewalls, symmetric NAT, or port blocks get in the way. A high relay ratio or STUN failure clusters often point to home-router settings, guest Wi-Fi, or data-center egress rules rather than the VDA image. Monitoring path selection, Rendezvous v2 adoption, and UDP blockage patterns helps the right team tune Gateway, DTLS, and client policy before remote users see chronic latency, dropped multimedia, and unstable Teams inside sessions.

## Implementation

Enable the enhanced rendezvous or HDX connection diagnostics in Citrix that emit path mode. Forward those events to `index=xd` with a stable sourcetype. Parse boolean UDP-block flags when present. Create weekly baselines: percentage relay versus direct by region and by client build. Alert when relay share jumps more than 20 points versus the rolling median for a region, or when symmetric NAT count spikes after a home-router firmware wave. Work with network teams to document required UDP and DTLS allow rules. Pair with Citrix Workspace app version compliance.

## Detailed Implementation

Prerequisites
• VDA and Workspace app versions that expose rendezvous diagnostics; event volume assessed so indexes stay within license.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Confirm field names with one sample session in test; add aliases in props if the vendor renames fields between releases.

Step 2 — Create the search and alert
Start with a weekly report for capacity planning, then add threshold alerts for relay storms tied to a single office egress.

Step 3 — Validate
Use a home-lab or volunteer device behind symmetric NAT, confirm `nat_type` and relay path show as expected. Open UDP briefly in a test firewall to see path flip to direct in logs.

Step 4 — Operationalize
Publish friendly guidance for home users when the data shows a router class pattern, and track remediation by cohort.

## SPL

```spl
index=xd (sourcetype="citrix:hdx:rendezvous" OR (sourcetype="citrix:vda:events" event_type="*rendezvous*"))
| eval path=lower(coalesce(rendezvous_path, path_mode, connection_path, "unknown"))
| eval stun=lower(coalesce(stun_status, stun, "unknown"))
| eval udp_block=if(match(lower(coalesce(udp_blocked, "")), "(true|yes|1|blocked)"), 1, 0)
| eval ver=coalesce(rendezvous_version, rv2_version, "na")
| where path="relay" OR udp_block=1 OR stun!="ok" OR match(lower(coalesce(nat_type, "")), "(sym|symmetric|strict)")
| stats count by host, user, path, stun, udp_block, nat_type, ver
| sort - count
```

## Visualization

Stacked 100% bar: direct vs relay by region; map of STUN failure counts; time chart of rendezvous v2 share across clients.

## References

- [HDX direct connections (Rendezvous) — product documentation](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/hdx-direct-connections.html)
- [Citrix Gateway and rendezvous (deployment context)](https://docs.citrix.com/en-us/citrix-gateway/13-1-citrix-gateway-federation-integration.html)
