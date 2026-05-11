<!-- AUTO-GENERATED from UC-5.20.53.json — DO NOT EDIT -->

---
id: "5.20.53"
title: "DNS64/NAT64 Translation Health and Dependency Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.53 · DNS64/NAT64 Translation Health and Dependency Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Some new-phone-only users need to call old-phone-only numbers. There's a special translator in the middle that converts the call between the two systems. We watch this translator to make sure it's handling all the calls properly — if it gets overloaded or breaks, people on the new phone system suddenly can't reach anyone on the old system.*

---

## Description

Monitors DNS64 synthesis rates and NAT64 translation gateway health to ensure IPv6-only hosts can reliably reach IPv4-only destinations. DNS64/NAT64 is a critical transition mechanism in IPv6-only deployments — if either component fails, IPv6-only hosts lose connectivity to any IPv4-only service. This use case tracks DNS64 synthesis volume (demand), NAT64 translation success/failure rates (supply), and state table utilization (capacity) to ensure the translation infrastructure keeps pace with demand.

## Value

DNS64/NAT64 is an invisible dependency — when it works, users don't know it exists. When it fails, a significant portion of the internet becomes unreachable from IPv6-only hosts. In mobile carrier networks, where millions of devices rely on NAT64, a failure is catastrophic. In enterprise environments, the failure is more subtle but equally impactful for users on IPv6-only VLANs. Monitoring both the DNS64 (synthesis) and NAT64 (translation) components end-to-end ensures the complete chain is healthy.

## Implementation

Collect DNS64 synthesis events from DNS resolvers and NAT64 translation logs from gateways. Track synthesis volume, translation success rate, and state table utilization. Alert on DNS64 resolver failures and NAT64 translation drops.

## Detailed Implementation

### Prerequisites
- DNS64 configured on recursive resolvers with the well-known prefix 64:ff9b::/96 (or a network-specific prefix).
- NAT64 gateway deployed with translation logging enabled.
- Understanding of which client segments are IPv6-only and depend on DNS64/NAT64.

### Step 1 — Configure data collection

**Cisco IOS-XE — NAT64 logging:**
```
nat64 v6v4 static 2001:db8::1 198.51.100.1
nat64 prefix stateful 64:ff9b::/96
nat64 logging translations flow-create
nat64 logging translations flow-delete
```

**BIND — DNS64 configuration with logging:**
```
dns64 64:ff9b::/96 {
  clients { ipv6-only-clients; };
  exclude { 64:ff9b::/96; ::ffff:0.0.0.0/96; };
};
```
BIND logs DNS64 synthesis at the `info` severity level.

**Verification:**
```spl
index=network ("64:ff9b" OR "dns64" OR "nat64") earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**DNS64 synthesis volume trending:**
```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") "64:ff9b" earliest=-7d
| timechart span=1h count as dns64_syntheses
```

**NAT64 translation health:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="pan:traffic") ("NAT64" OR "nat64") earliest=-1h
| eval outcome=case(
    match(_raw, "(?i)create|new|start"), "success",
    match(_raw, "(?i)fail|drop|error|denied"), "failure",
    match(_raw, "(?i)delete|expire|end"), "expired",
    1=1, "other")
| stats count(eval(outcome="success")) as created count(eval(outcome="failure")) as failed count(eval(outcome="expired")) as expired
| eval failure_rate=round(failed / (created + failed) * 100, 2)
| eval status=case(
    failure_rate > 5, "WARNING — high NAT64 failure rate",
    failure_rate > 1, "MONITOR — elevated NAT64 failures",
    1=1, "OK")
```

**NAT64 state table utilization:**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="nat64.active_translations" earliest=-24h
| stats latest(metric_value) as active by host
| lookup nat64_capacity.csv host OUTPUT max_translations
| eval utilization_pct=round(active / max_translations * 100, 1)
| where utilization_pct > 70
| eval alert=case(
    utilization_pct > 90, "CRITICAL — NAT64 state table nearly full",
    utilization_pct > 80, "HIGH — approaching NAT64 capacity",
    1=1, "WARNING — monitor NAT64 growth")
```

### Step 3 — Validate
(a) **DNS64 synthesis test.** From an IPv6-only host, resolve a domain with only an A record (e.g., `dig AAAA ipv4only.arpa`). This is the standard DNS64 test domain (RFC 7050). If DNS64 is working, it returns `64:ff9b::c000:aa` (192.0.0.170 embedded).

(b) **End-to-end NAT64 test.** From the same host, `curl -6 http://ipv4only.arpa`. If DNS64 and NAT64 are both working, the connection succeeds.

(c) **Failure simulation.** Block NAT64 prefix (64:ff9b::/96) at the gateway. Verify translation failures appear in the logs.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DNS64/NAT64 Translation Health"):
- Row 1 — Single-value: DNS64 syntheses/hour, active NAT64 translations, failure rate.
- Row 2 — Dual timechart: DNS64 synthesis volume alongside NAT64 translations — should correlate.
- Row 3 — Gauge: NAT64 state table utilization.
- Row 4 — Alert panel: translation failures, state table warnings.

**Scheduling:** NAT64 health every 15 minutes. State table alert every 5 minutes. DNS64 trending hourly.

**Runbook:**
1. DNS64 synthesis failing: check DNS64 resolver configuration. Test with `dig AAAA ipv4only.arpa @<resolver>`.
2. NAT64 failures: check gateway health, interface status, routing for 64:ff9b::/96.
3. State table full: increase capacity, reduce translation timeouts, or add another NAT64 gateway.

### Step 5 — Troubleshooting

- **DNS64 prefix mismatch** — If the DNS64 resolver uses a different prefix than the NAT64 gateway's configured prefix, translations will fail. Both must use the same prefix (typically 64:ff9b::/96).

- **MTU issues through NAT64** — IPv6 packets (minimum 1280 bytes) are translated to IPv4 packets. If the IPv4 path has MTU constraints, fragmentation may be needed. Since the NAT64 gateway is performing stateful translation, it must handle fragment reassembly — verify this capability.

- **DNSSEC and DNS64 incompatibility** — DNS64-synthesised AAAA records break DNSSEC validation because the synthesised record does not match the authoritative zone's signature. DNS64 should be deployed on validating resolvers that strip DNSSEC from synthesised responses, or use the DNSSEC-aware DNS64 approach described in RFC 6147 §5.5.

## SPL

```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") "64:ff9b" earliest=-24h
| stats count as dns64_syntheses
| append [
    search index=network (sourcetype="cisco:ios" OR sourcetype="pan:traffic") ("NAT64" OR "nat64" OR "64:ff9b") earliest=-24h
    | eval nat64_event=case(
        match(_raw, "(?i)created|create|new"), "translation_created",
        match(_raw, "(?i)deleted|expire|timeout"), "translation_removed",
        match(_raw, "(?i)fail|error|drop"), "translation_failed",
        1=1, "other")
    | stats count as nat64_total count(eval(nat64_event="translation_created")) as translations_created count(eval(nat64_event="translation_failed")) as translations_failed
  ]
| eval health=case(
    translations_failed > translations_created * 0.05, "WARNING — NAT64 failure rate above 5%",
    dns64_syntheses > 0 AND isnull(translations_created), "WARNING — DNS64 active but no NAT64 translations seen",
    1=1, "OK")
```

## Visualization

(1) Single-value: DNS64 syntheses per hour, NAT64 translations active, failure rate. (2) Timechart: DNS64 synthesis volume and NAT64 translations over 24 hours — should correlate. (3) Gauge: NAT64 state table utilization. (4) Alert panel: translation failures.

## Known False Positives

**Dual-stack destinations.** Destinations that have both A and AAAA records do not trigger DNS64 synthesis — the real AAAA record is returned. The DNS64 synthesis rate only reflects traffic to IPv4-only destinations.

**Client DNS cache.** After a DNS64-synthesised AAAA is cached by the client, subsequent connections to the same destination use the cached record and don't generate new DNS64 synthesis events. The synthesis rate under-counts actual NAT64 usage.

**464XLAT CLAT.** In 464XLAT deployments, the customer-side CLAT performs local NAT46 for legacy IPv4 applications, then traffic traverses NAT64 at the provider. The NAT64 translation logs may not distinguish between direct NAT64 and 464XLAT-originated traffic.

## References

- [RFC 6147 — DNS64: DNS Extensions for Network Address Translation from IPv6 Clients to IPv4 Servers](https://www.rfc-editor.org/rfc/rfc6147)
- [RFC 6146 — Stateful NAT64: Network Address and Protocol Translation from IPv6 Clients to IPv4 Servers](https://www.rfc-editor.org/rfc/rfc6146)
- [RFC 8585 — Requirements for IPv6 Customer Edge Routers to Support IPv4-as-a-Service (464XLAT)](https://www.rfc-editor.org/rfc/rfc8585)
