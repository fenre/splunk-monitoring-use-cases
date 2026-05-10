<!-- AUTO-GENERATED from UC-5.20.123.json — DO NOT EDIT -->

---
id: "5.20.123"
title: "IPv6 Flow Label Usage and Abuse Detection (RFC 6437)"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.123 · IPv6 Flow Label Usage and Abuse Detection (RFC 6437)

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Every IPv6 letter has a small coloured sticker (flow label) that helps the post office sort it quickly without opening it. We check that all letters have proper stickers and that nobody is using the stickers to secretly communicate or to trick the sorting machine into sending their letters through a preferred route.*

---

## Description

Monitors IPv6 Flow Label field usage and anomalies. The flow label is a 20-bit field used for ECMP load balancing and flow classification. Detects zero flow labels (legacy implementations), abnormal flow label distributions (possible covert channel), and flow label manipulation (ECMP steering attacks).

## Value

The IPv6 flow label is an underutilized but important field. It enables efficient ECMP without deep packet inspection, but can be abused for covert communication or load balancer manipulation. Monitoring flow label usage reveals legacy implementations that need updating and detects potential abuse patterns.

## Implementation

Collect flow label data from NetFlow/IPFIX exports. Analyse distribution patterns. Alert on anomalous usage.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX exporter configured to include IPv6 flow label (Information Element 31).

### Step 1 — Configure flow label export
Ensure NetFlow/IPFIX templates include the flow label field. Cisco: `flow record` with `match ipv6 flow-label`.

### Step 2 — Create monitoring searches
```spl
index=network sourcetype="netflow" earliest=-24h
| where isnotnull(ipv6_flow_label)
| stats count by ipv6_flow_label
| sort -count
| head 20
```

### Step 3 — Validate
Generate IPv6 traffic from a modern OS (Linux 4.4+, Windows 10+). Verify non-zero flow labels appear in NetFlow.

### Step 4 — Operationalize
**Dashboard:** Flow label distribution. **Alert:** Sudden flow label pattern change — investigate.

### Step 5 — Troubleshooting
- Zero labels: Update the source OS or network stack. Linux: flow labels are random by default since kernel 4.4.

## SPL

```spl
index=network sourcetype="netflow" earliest=-24h
| eval has_flow_label=if(isnotnull(ipv6_flow_label) AND ipv6_flow_label != "0" AND ipv6_flow_label != 0, 1, 0)
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| stats count as total sum(has_flow_label) as with_label sum(eval(if(has_flow_label=0, 1, 0))) as zero_label by src
| eval label_pct=round(with_label / total * 100, 1)
| eval status=case(
    label_pct=0, "ALL ZERO — legacy implementation or flow label stripping",
    label_pct < 50, "LOW USAGE — " . label_pct . "% of flows have labels",
    1=1, "OK — " . label_pct . "% flows labeled")
| where label_pct < 50 AND total > 100
| sort label_pct
```

## Visualization

(1) Pie chart: flow label usage (labeled vs zero). (2) Histogram: flow label value distribution. (3) Table: sources with zero labels. (4) Trend: label adoption over time.

## Known False Positives

**Legacy OS.** Older operating systems and network stacks set the flow label to zero. This is not malicious, just outdated.

**VPN tunnels.** Some VPN implementations zero the flow label on encapsulated traffic. This is an implementation limitation.

## References

- [RFC 6437 — IPv6 Flow Label Specification](https://www.rfc-editor.org/rfc/rfc6437)
- [RFC 6438 — Using the IPv6 Flow Label for Equal Cost Multipath Routing and Link Aggregation](https://www.rfc-editor.org/rfc/rfc6438)
