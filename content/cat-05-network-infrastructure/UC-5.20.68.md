<!-- AUTO-GENERATED from UC-5.20.68.json — DO NOT EDIT -->

---
id: "5.20.68"
title: "IPv6 Flow Label Anomaly Detection and ECMP Manipulation"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.68 · IPv6 Flow Label Anomaly Detection and ECMP Manipulation

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*Each IPv6 letter has a small stamp number (the flow label) that helps the post office decide which truck to put it on. If someone is putting wildly different stamp numbers on thousands of letters per minute, they might be trying to overwhelm certain truck routes or hide secret messages in the stamp numbers. We watch the stamp number patterns to spot this manipulation.*

---

## Description

Detects anomalous IPv6 flow label usage from IPFIX/NetFlow flow records. The IPv6 flow label is a 20-bit field that routers use for ECMP path hashing. Manipulation of this field allows attackers to influence traffic routing paths, conduct denial-of-service attacks, or establish covert data channels. Extremely high unique flow label counts from a single source indicate either an ECMP manipulation attempt or a DoS flooding technique.

## Value

Flow label manipulation is an IPv6-specific attack vector with no IPv4 equivalent. An attacker who controls the flow label can force all their traffic down a single ECMP path (overloading one link while others are idle), distribute attack traffic evenly across all paths (maximising total throughput), or create a steganographic covert channel in the 20-bit field. Flow label anomaly detection catches these attack patterns before they impact network availability or enable data exfiltration.

## Implementation

Export IPv6 flow label in IPFIX/NetFlow v9 templates. Analyse flow label distributions per source. Baseline normal flow label entropy. Alert on statistical anomalies.

## Detailed Implementation

### Prerequisites
- IPFIX or NetFlow v9 exporters configured to include flowLabelIPv6 (IE#31) in the template.
- Splunk NetFlow collector parsing the flow label field.
- Baseline of normal flow label distributions per source type.

### Step 1 — Configure data collection

**Cisco IOS-XE — Include flow label in Flexible NetFlow record:**
```
flow record IPV6-WITH-LABEL
 match ipv6 source address
 match ipv6 destination address
 match ipv6 flow-label
 match transport source-port
 match transport destination-port
 collect counter bytes long
 collect counter packets long
```
The `match ipv6 flow-label` directive adds the 20-bit flow label to each flow record.

**IPFIX template verification:**
Verify IE#31 (flowLabelIPv6) appears in IPFIX template exports:
```spl
index=network sourcetype="netflow" earliest=-1h
| where isnotnull(flowLabelIPv6)
| stats count by exporter_ip
```
If no results, the flow label is not being exported.

**Verification:**
```spl
index=network sourcetype="netflow" flowLabelIPv6=* earliest=-1h
| stats count min(flowLabelIPv6) max(flowLabelIPv6) dc(flowLabelIPv6) as unique_labels by exporter_ip
```

### Step 2 — Create the search and alert

**High unique label count (ECMP manipulation / DoS):**
```spl
index=network sourcetype="netflow" flowLabelIPv6=* earliest=-15m
| stats dc(flowLabelIPv6) as unique_labels count as flow_count by sourceIPv6Address
| where unique_labels > 5000
| eval alert="ECMP manipulation or DoS: " . unique_labels . " unique flow labels from " . sourceIPv6Address . " in 15 minutes"
| sort -unique_labels
```

**Structured pattern detection (covert channel):**
```spl
index=network sourcetype="netflow" flowLabelIPv6=* earliest=-1h
| eval label=tonumber(flowLabelIPv6)
| streamstats current=t window=10 values(label) as recent_labels by sourceIPv6Address
| eval label_range=max(recent_labels) - min(recent_labels)
| where label_range < 100 AND label > 0
| stats count as structured_windows by sourceIPv6Address
| where structured_windows > 50
| eval alert="Structured flow labels from " . sourceIPv6Address . " — potential covert channel (" . structured_windows . " windows with low-range sequential labels)"
```
Legitimate flow labels should be pseudo-random. Sequential or structured patterns indicate intentional encoding.

**Zero-label transition detection:**
```spl
index=network sourcetype="netflow" earliest=-24h
| eval has_label=if(tonumber(flowLabelIPv6) > 0, 1, 0)
| bin _time span=1h
| stats avg(has_label) as label_rate by sourceIPv6Address, _time
| streamstats current=t window=2 values(label_rate) as rates by sourceIPv6Address
| where mvcount(rates)=2 AND mvindex(rates, 0) > 0.8 AND mvindex(rates, 1) < 0.2
| eval alert="Sudden flow label dropout from " . sourceIPv6Address . " — investigate for downgrade or stack change"
```

### Step 3 — Validate
(a) **Label export verification.** Generate known IPv6 traffic with specific flow labels. Verify the labels appear in IPFIX records.

(b) **High-label test.** Use a tool that generates many unique flow labels per second. Verify the ECMP manipulation alert fires.

(c) **Baseline establishment.** Measure normal unique-label-per-source rates for different device types (servers, workstations, network devices).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Flow Label Analysis"):
- Row 1 — Alert panel: sources with anomalous flow label counts.
- Row 2 — Timechart: unique flow labels per minute (global and per top source).
- Row 3 — Histogram: flow label value distribution.
- Row 4 — Table: sources with structured flow label patterns.

**Scheduling:** High unique labels every 15 minutes. Structured pattern hourly. Zero-label transition daily.

**Runbook:**
1. >10,000 unique labels: investigate source immediately. If internal, check for compromised host running attack tools. If external, apply rate limiting.
2. Structured labels: investigate for covert channel. Packet capture the flow and analyse label values for encoded data.
3. Zero-label transition: verify the host's network stack. OS updates can change flow label behaviour.

### Step 5 — Troubleshooting

- **Missing flow labels** — Not all IPFIX exporters include the flow label by default. If the field is missing from records, update the flow record definition to include `match ipv6 flow-label`.

- **Endianness** — The flow label is a 20-bit field. Ensure the IPFIX parser handles the 20-bit extraction correctly. Some parsers may zero-pad or truncate incorrectly.

- **ECMP hash sensitivity** — Not all routers use the flow label in their ECMP hash. Check the router's hash algorithm configuration (`show ipv6 cef exact-route` on Cisco) to understand the impact of flow label manipulation.

## SPL

```spl
index=network sourcetype="netflow" flowLabelIPv6=* earliest=-1h
| eval flow_label=tonumber(flowLabelIPv6)
| stats dc(flow_label) as unique_labels count as packets avg(flow_label) as avg_label stdev(flow_label) as stdev_label by sourceIPv6Address
| where unique_labels > 1000
| eval anomaly=case(
    unique_labels > 10000, "CRITICAL — " . unique_labels . " unique flow labels from single source — DoS or ECMP manipulation",
    stdev_label < 50000, "WARNING — low entropy in flow labels — potential structured covert channel",
    unique_labels > 1000, "MEDIUM — elevated unique flow label count — investigate source application",
    1=1, null())
| sort -unique_labels
```

## Visualization

(1) Timechart: unique flow labels per minute per top source. (2) Table: sources with anomalous flow label counts. (3) Histogram: flow label value distribution (should be approximately uniform for legitimate sources). (4) Scatter plot: flow label entropy vs volume per source.

## Known False Positives

**Load balancers and CDN edge servers.** Servers that originate many independent flows (CDN edges, load balancers, DNS resolvers) legitimately generate many unique flow labels. Identify these by role and adjust thresholds.

**Applications with per-packet labels.** Some applications or OS network stacks incorrectly generate a new flow label per packet instead of per flow. This is a compliance issue (RFC 6437) but not a security threat.

**OS default behaviour variation.** Different operating systems handle flow labels differently — Linux uses random labels, Windows may use zero, and some embedded devices use fixed values. Baseline per OS type.

## References

- [RFC 6437 — IPv6 Flow Label Specification](https://www.rfc-editor.org/rfc/rfc6437)
- [RFC 6438 — Using the IPv6 Flow Label for ECMP and LAG](https://www.rfc-editor.org/rfc/rfc6438)
