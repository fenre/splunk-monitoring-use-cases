<!-- AUTO-GENERATED from UC-5.20.140.json — DO NOT EDIT -->

---
id: "5.20.140"
title: "IPv6 Flow Label Misuse and Covert Channel Detection (RFC 6437)"
status: "verified"
criticality: "medium"
splunkPillar: "ES"
---

# UC-5.20.140 · IPv6 Flow Label Misuse and Covert Channel Detection (RFC 6437)

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** ES &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*Every IPv6 packet has a small label, like a shipping tag. It should be a random number for each conversation. If someone is writing secret messages on these tags instead of random numbers, they could be smuggling data out of the network. We check that these tags look properly random and flag any suspicious patterns.*

---

## Description

Detects misuse of the IPv6 Flow Label field for covert channel communication. The 20-bit Flow Label should be uniformly random per flow (RFC 6437). Non-random patterns indicate either misconfiguration or deliberate covert channel encoding. Also detects all-zero Flow Labels, which while valid, reduce QoS effectiveness.

## Value

The IPv6 Flow Label is a 20-bit field that traverses the network unchanged by routers. This makes it an attractive covert channel for data exfiltration or C2 communication. Because most security tools ignore the Flow Label, it can carry encoded data undetected. Monitoring Flow Label entropy identifies both covert channels and misconfigured stacks that don't set Flow Labels properly.

## Implementation

Analyze Flow Label diversity and entropy per source. Alert on anomalous patterns.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX exporting Flow Label field.
- Note: Not all NetFlow implementations export the Flow Label.

### Step 1 — Verify NetFlow exports include Flow Label.

### Step 2 — Baseline normal Flow Label distribution.

### Step 3 — Validate: Generate test traffic with known Flow Labels. Verify detection.

### Step 4 — Operationalize
**Dashboard:** Flow Label analysis. **Alert:** Low-entropy Flow Labels — investigate.

### Step 5 — Troubleshooting
- Zero Flow Labels: Usually harmless but indicate the source stack doesn't implement RFC 6437. Update OS/firmware.
- Encoded data in labels: Investigate the source for malware or unauthorized tools.

## SPL

```spl
index=network sourcetype="netflow" earliest=-24h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| eval flow_label=if(isnotnull(flow_label), flow_label, 0)
| stats count as flows dc(flow_label) as unique_labels avg(flow_label) as avg_label stdev(flow_label) as stdev_label by src
| eval label_ratio=round(unique_labels/flows, 4)
| eval anomaly=case(
    unique_labels=1 AND flows > 100 AND flow_label=0, "ALL_ZERO — " . flows . " flows with flow_label=0 — legacy behaviour or misconfiguration",
    label_ratio < 0.01 AND flows > 100, "LOW_DIVERSITY — only " . unique_labels . " labels across " . flows . " flows — possible encoding",
    stdev_label < 100 AND flows > 100, "LOW_ENTROPY — flow labels have suspiciously low randomness",
    1=1, null())
| where isnotnull(anomaly)
| sort -flows
```

## Visualization

(1) Histogram: Flow Label distribution. (2) Table: sources with anomalous labels. (3) Single-value: % of flows with zero labels.

## Known False Positives

**Legacy stacks.** Older IPv6 implementations set Flow Label to zero on all packets. This is valid per RFC 6437 but reduces QoS effectiveness.

**Load balancers.** Some load balancers set specific Flow Label patterns for ECMP distribution. These are legitimate.

## References

- [RFC 6437 — IPv6 Flow Label Specification](https://www.rfc-editor.org/rfc/rfc6437)
- [IPv6 Flow Labels as Covert Channel — Academic Research](https://doi.org/10.1109/ACSAC.2005.25)
