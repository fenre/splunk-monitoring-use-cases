<!-- AUTO-GENERATED from UC-5.7.15.json — DO NOT EDIT -->

---
id: "5.7.15"
title: "Encrypted Traffic Analytics (ETA) via Flow Metadata"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.7.15 · Encrypted Traffic Analytics (ETA) via Flow Metadata

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Anomaly, Risk &middot; **Wave:** Run &middot; **Status:** Verified

*We study fingerprints around sealed letter traffic—timing and shape clues the gear shares—so we can spot sneaky tunnels without opening every envelope.*

---

## Description

Surfaces internal hosts whose encrypted-web flows carry anomaly-oriented metadata scores or handshake fingerprints associated with encrypted-traffic analytics pipelines rather than inspecting payloads.

## Value

Incident responders prioritize probable covert tunnels without bulk decryption, supports zero-trust networking assertions about encrypted channels, and documents investigative rationale using exporter-grade telemetry aligned with vendor analytics investments.

## Implementation

Enable ETA-capable templates on supported Catalyst or ISR platforms; map enterprise information elements in props; baseline departmental scores; pair alerts with endpoint and identity context.

## Detailed Implementation

### Prerequisites
- Hardware with Cisco ETA licensing and Stealthwatch or Secure Client telemetry correlation documented by your security architecture board.
- Splunk field extractions verified against a packet capture ground truth during pilot.
- Governance memo permitting metadata-driven inspection without payload decryption.

### Step 1 — Configure data collection
Mirror Flexible NetFlow records to a dedicated heavy forwarder input; segregate high-volume campus exporters into separate indexes to control license burn.

### Step 2 — Create the search
Layer allowlists for software-update CDN nets and known DevOps artifact hosts. Use `streamstats` over seven days per src for adaptive thresholds when static numbers chatter.

### Step 3 — Validate
Replay labelled malware samples in a sandbox whose flows egress through an ETA-enabled router and confirm elevated scores appear with acceptable latency.

### Step 4 — Operationalize
Dashboard integrates ETA tiles with traditional volumetric exfiltration panels from sibling use cases; notable events carry autonomous-system and domain enrichment.

### Step 5 — Troubleshooting
Null scores often mean an outdated protocol pack—upgrade IOS-XE. Duplicate telemetry occurs when both sampled NetFlow and packet-derived analytics feed Splunk; deduplicate using `dedup` on `(src, dest, dest_port, flow_start_ms)`.

## SPL

```spl
index=netflow earliest=-24h dest_port=443 OR dest_port=9443
| eval eta_score=coalesce(spl_exfiltration_score, eta_metadata_score, ssl_entropy_score)
| eval tls_ext=coalesce(tls_extensions_length, tls_extensions_len)
| eval handshake_rtt=coalesce(initial_round_trip_time_ms, tls_handshake_rtt_ms)
| where isnotnull(eta_score) OR isnotnull(tls_ext) OR isnotnull(handshake_rtt)
| stats avg(eta_score) as avg_eta max(eta_score) as peak_eta sum(bytes) as bytes dc(dest) as uniq_servers count as flows
  by src
| where avg_eta>50 OR peak_eta>85 OR (flows>500 AND avg_eta>35)
| eval mb=round(bytes/1048576,2)
| sort -peak_eta
| head 50
```

## Visualization

Scatter of avg_eta versus mb per src; table with peak_eta, uniq_servers, flows; timeline of rolling averages.

## Known False Positives

Developers compiling containers generate noisy handshake variability. Video conferencing renewal bursts inflate round-trip statistics. Misconfigured load balancers duplicate flows and exaggerate scores.

## References

- [Cisco Encrypted Traffic Analytics Overview](https://www.cisco.com/c/en/us/products/security/)
- [Splunk Docs — NetFlow Add-on](https://docs.splunk.com/Documentation/NetFlow/)
