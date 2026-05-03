<!-- AUTO-GENERATED from UC-5.7.9.json — DO NOT EDIT -->

---
id: "5.7.9"
title: "Unauthorized VLAN Traffic Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.7.9 · Unauthorized VLAN Traffic Detection

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security

*We help you know when data is crossing virtual network lines it should not cross—like a cable plugged into the wrong room—which can be a simple mistake or someone trying to sneak in.*

---

## Description

Traffic originating from or destined to unauthorized VLANs indicates misconfigured switch ports, VLAN hopping attacks, or rogue devices.

## Value

Network security teams validate VLAN segmentation policy in real time by detecting unauthorized inter-VLAN traffic, identifying potential VLAN hopping attacks, and monitoring for microsegmentation policy drift.

## Implementation

Map flow data to VLANs via input interface. Maintain a lookup of authorized VLANs per port. Alert on traffic from unauthorized VLANs. Correlate with 802.1X status.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with VLAN information. VLAN visibility in flow records requires one of: (a) NetFlow v9/IPFIX with VLAN ID fields (input_vlan, output_vlan / ingressVRFID / vlanId), (b) Flexible NetFlow on Cisco IOS-XE with `match datalink vlan input` and `match datalink vlan output` in the flow record, (c) sFlow with VLAN extension headers.
- Build an `authorized_vlans.csv` lookup defining the expected traffic matrix: `src_vlan,dest_vlan,policy,description` (e.g., `100,200,allow,Web servers to App servers`, `100,300,deny,Web servers should never reach Database directly`). This is your microsegmentation policy baseline.
- Understand your VLAN architecture: enterprise networks typically segment by function (management, user, server, IoT/OT, guest). Unauthorized VLAN traffic — traffic crossing VLAN boundaries that policy forbids — indicates: (a) ACL misconfiguration on the inter-VLAN router/L3 switch, (b) VLAN hopping attack (802.1Q double-tagging), (c) trunk misconfiguration allowing unintended VLANs.
- For this UC to work, NetFlow must be exported from the inter-VLAN routing point (typically the core/distribution layer or a firewall doing inter-VLAN routing), not from access switches (which only see intra-VLAN traffic).

### Step 1 — Configure data collection
Verify VLAN information in flow records:
```spl
index=netflow earliest=-15m
| stats dc(input_vlan) as vlans_seen count by host
| where vlans_seen > 1
```
If `input_vlan` is null or `dc` is 1 for all hosts, VLAN fields are not being exported. On Cisco IOS-XE, add `match datalink vlan input` and `match datalink vlan output` to your Flexible NetFlow flow record. On Juniper, configure `vlan-id` in the sampling template.

Alternative if VLAN fields unavailable — derive VLAN from subnet:
```spl
index=netflow earliest=-15m
| lookup subnet_to_vlan.csv src OUTPUT src_vlan
| lookup subnet_to_vlan.csv dest OUTPUT dest_vlan
| where isnotnull(src_vlan) AND isnotnull(dest_vlan)
| stats count by src_vlan, dest_vlan
```

### Step 2 — Create the search and alert

**Primary search — Unauthorized VLAN-to-VLAN traffic detection:**
```spl
index=netflow earliest=-1h
| where isnotnull(input_vlan) AND isnotnull(output_vlan) AND input_vlan!=output_vlan
| eval src_vlan=input_vlan, dest_vlan=output_vlan
| lookup authorized_vlans.csv src_vlan dest_vlan OUTPUT policy description
| where policy="deny" OR isnull(policy)
| stats sum(bytes) as bytes sum(packets) as pkts dc(src) as sources dc(dest) as destinations by src_vlan, dest_vlan, policy
| eval bytes_MB=round(bytes/1048576, 1)
| eval violation_type=if(isnull(policy), "Undefined (no policy)", "Explicit Deny")
| sort -bytes
```

#### Understanding this SPL: Compares every inter-VLAN flow against the authorized traffic matrix. Flows matching a "deny" policy or with no policy defined (undefined VLAN pair) are violations. This is essentially network segmentation validation using flow data. The `dc(src)` and `dc(dest)` show the scope — a single host crossing VLANs may be a misconfigured device, while many hosts crossing suggests an ACL or routing issue.

**VLAN hopping detection — double-tagged frames:**
```spl
index=netflow earliest=-1h
| where input_vlan!=output_vlan
| stats dc(input_vlan) as src_vlans dc(output_vlan) as dest_vlans sum(bytes) as bytes by src
| where src_vlans > 3
| lookup asset_inventory.csv ip as src OUTPUT hostname role
| eval src_label=if(isnotnull(hostname), hostname, src)
| sort -src_vlans
```

#### Understanding this SPL: A single host appearing on multiple VLANs is suspicious. Normal hosts are on one VLAN. A host spanning 3+ VLANs could be: (a) an attacker performing VLAN hopping, (b) a router/firewall (legitimate — filter these), (c) a VM host with interfaces in multiple VLANs. Cross-reference with the asset inventory to identify whether the multi-VLAN host is legitimate.

**Inter-VLAN traffic volume matrix (baseline):**
```spl
index=netflow earliest=-24h
| where input_vlan!=output_vlan
| stats sum(bytes) as bytes dc(src) as sources dc(dest) as dests by input_vlan, output_vlan
| eval bytes_GB=round(bytes/1073741824, 2)
| sort -bytes
```

### Step 3 — Validate
(a) Compare the VLAN traffic matrix to your firewall/ACL policy. Every "allow" pair in the matrix should have a corresponding permit rule. Every "deny" pair should have a deny rule. Gaps indicate policy drift.
(b) Test: from a host in VLAN 100, attempt to ping a host in a restricted VLAN (e.g., 300). The flow should appear in the violation results.
(c) Verify VLAN numbering: ensure the VLAN IDs in flow records match your switch VLAN database (`show vlan brief`).

### Step 4 — Operationalize
Dashboard ("Security — VLAN Traffic Policy"):
- Row 1 — Single-value tiles: "Active VLAN violations (1h)", "Denied VLAN pairs with traffic", "VLAN hopping suspects", "Inter-VLAN volume (GB/h)".
- Row 2 — Heat map: VLAN-to-VLAN traffic matrix (green=allowed, red=denied, gray=undefined).
- Row 3 — Violation table: src_vlan, dest_vlan, violation_type, bytes_MB, sources, destinations.
- Row 4 — Multi-VLAN hosts table with drilldown to flow details.

Alerting:
- Critical (traffic on explicitly denied VLAN pair > 10 MB): possible ACL misconfiguration or active exploitation — alert network security.
- High (single host on 4+ VLANs and not a known router): possible VLAN hopping — alert SOC.
- Warning (new undefined VLAN pair observed): alert network operations to review and classify.

Runbook:
1. **Traffic on denied VLAN pair**: Check the ACL/firewall rule for the relevant interface. If the deny rule exists, the traffic should have been blocked — investigate why it wasn't (rule ordering, bypass route). If no rule exists, add it.
2. **VLAN hopping suspect**: Check the physical port configuration of the source host. Ensure access ports are not misconfigured as trunk ports. Apply `switchport mode access` and `switchport nonegotiate` on all user-facing ports.
3. **New undefined VLAN pair**: Classify as allow or deny in the authorized_vlans.csv lookup and update ACLs accordingly.

### Step 5 — Troubleshooting

- **VLAN IDs all show as 0** — The exporter is not including VLAN fields in the flow record. This is common with NetFlow v5. Upgrade to NetFlow v9 or IPFIX with VLAN-aware flow records.

- **Subnet-to-VLAN mapping produces mismatches** — If your subnets don't map 1:1 to VLANs (e.g., multiple subnets in one VLAN), the derived VLAN will be wrong. Use native VLAN fields from flow records for accuracy.

- **Legitimate routers flagged as VLAN hoppers** — Routers and L3 switches legitimately appear on multiple VLANs. Add them to an exclusion list based on `role="network_device"` in the asset inventory.

- **High volume of undefined VLAN pairs** — Your authorized_vlans.csv is incomplete. Start by populating it with the highest-volume pairs from the baseline search and classifying each one.

## SPL

```spl
index=network sourcetype="netflow"
| lookup vlan_authorization_lookup src_vlan OUTPUT authorized
| where authorized!="yes" OR isnull(authorized)
| stats sum(bytes) as bytes, dc(src) as unique_hosts by src_vlan, input_interface
| sort -bytes
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out dc(All_Traffic.src) as unique_hosts
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

## Visualization

Table (VLAN, interface, hosts, volume), Alert panel, Status grid.

## Known False Positives

Span changes, trunks, and temporary moves can put traffic on unexpected VLANs during maintenance. Traffic spikes during backup jobs, large file transfers, or video streaming on those VLANs are usually operational, not policy violations.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
