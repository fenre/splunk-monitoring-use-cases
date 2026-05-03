<!-- AUTO-GENERATED from UC-5.7.18.json — DO NOT EDIT -->

---
id: "5.7.18"
title: "DNS-over-HTTPS / DNS-over-TLS Flow Identification"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.7.18 · DNS-over-HTTPS / DNS-over-TLS Flow Identification

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance, Governance &middot; **Wave:** Walk &middot; **Status:** Verified

*We look for patterns where computers ask for names using sealed tunnels instead of the old-style phone book queries. That helps policy folks guide people toward approved helpers and spot sneaky hideouts.*

---

## Description

Segments flows likely carrying encrypted name lookups using resolver-side transport hints—standard ports for private-name-over-transport-security plus conservative World Wide Web port heuristics enriched by resolver catalogs.

## Value

Policy teams enforce approved resolver programs, incident responders differentiate covert channels from ordinary browsing volume, and privacy councils document proportionality when regulating encrypted resolution paths.

## Implementation

Curate resolver lookups quarterly; combine alerts with full packet capture teams for confirmation; tune byte-per-packet ratios per campus; educate employees on approved providers.

## Detailed Implementation

### Prerequisites
- Signed acceptable-use policy referencing encrypted resolution.
- Collaboration with desktop engineering on browser defaults.
- Splunk role separation so human-resources subnets receive aggregated counts only.

### Step 1 — Configure data collection
Ensure exporters emit Layer-four ports reliably; validate Network Address Translation does not collapse distinct internal hosts beyond acceptable cardinality targets.

### Step 2 — Create the search
Promote high-fidelity hits into a summary index with `(dest_port==853)` certainty tier before heuristic bucket results. Cross-launch Secure Gateway logs when available.

### Step 3 — Validate
Compare hourly Splunk counts to resolver aggregate dashboards from your recursive infrastructure for campuses still using corporate resolvers.

### Step 4 — Operationalize
Dashboard blends educational messaging with quantitative tiles; automated emails attach remediation links rather than raw endpoints where regulations require minimization.

### Step 5 — Troubleshooting
Video-over-port-443 gaming platforms mimic heuristic ratios—maintain entertainment subnet filters. Split-tunnel virtual private networks inflate resolver diversity benignly.

## SPL

```spl
index=netflow earliest=-24h (protocol=6 OR upper(protocol)="TCP")
| eval svc=case(dest_port==853 OR src_port==853, "PRIVATE_NAME_TLS",
              dest_port==443 AND packets>10 AND bytes>20480 AND bytes/packets<900, "LIKELY_WEB_TUNNEL_HINT",
              dest_port==443, "GENERIC_WEB",
              true(), "OTHER")
| lookup doh_providers.csv dest OUTPUT provider_label
| eval tunnel_label=case(isnotnull(provider_label), provider_label, svc=="PRIVATE_NAME_TLS", "PORT853_UNLABELED", svc=="LIKELY_WEB_TUNNEL_HINT", "SMALL_PKT_WEB_HEURISTIC", 1==1, null())
| where isnotnull(tunnel_label)
| stats sum(bytes) as bytes dc(src) as hosts dc(dest) as resolvers avg(bytes/packets) as avg_payload
  by tunnel_label svc
| eval mb=round(bytes/1048576,2)
| sort -bytes
| head 40
```

## Visualization

Stacked bar of mb by tunnel_label; table with hosts, resolvers, avg_payload; trendline of distinct hosts using port eight-five-three.

## Known False Positives

Legitimate developer containers pull artifacts over small-message HTTPS sessions. Managed Chrome updates contact multiple resolvers briefly. Shared carrier-grade Network Address Translation concentrates hosts artificially.

## References

- [RFC 8484 — DNS Queries over HTTPS](https://www.rfc-editor.org/rfc/rfc8484)
- [RFC 7858 — Specification for DNS over Transport Layer Security](https://www.rfc-editor.org/rfc/rfc7858)
