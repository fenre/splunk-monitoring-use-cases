<!-- AUTO-GENERATED from UC-5.2.52.json — DO NOT EDIT -->

---
id: "5.2.52"
title: "Check Point Anti-Spoofing Violations (Check Point)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.52 · Check Point Anti-Spoofing Violations (Check Point)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We count anti-spoofing hits so bad addressing, late routing change, and miswired segments surface before they turn into silent drops.*

---

## Description

Anti-spoofing validates that packets arriving on an interface have source IPs consistent with the interface's defined topology. Violations indicate either network misconfiguration (asymmetric routing, missing routes) or actual IP spoofing attacks. High violation rates from specific sources warrant immediate investigation as they may mask data exfiltration or DDoS reflection.

## Value

Security teams monitor Check Point anti-spoofing violations by interface and source to detect IP address spoofing attacks and identify topology misconfigurations causing false positive drops.

## Implementation

Forward firewall drop logs including anti-spoofing events. Map `inzone` and `outzone` to topology to distinguish misconfiguration from attacks. Alert on new source IPs triggering anti-spoofing. Correlate with routing changes. Tune anti-spoofing topology definitions after legitimate asymmetric routing is identified.

## Detailed Implementation

### Prerequisites
* Check Point anti-spoofing violation logs. Data in `index=checkpoint` with `sourcetype=cp_log`. Key fields: `action` (Drop/Reject), `src`, `dst`, `ifname`, `rule_name`, `product`, `description`.
* Anti-spoofing: validates that packets arriving on an interface have source IPs consistent with the interface's defined topology (network behind the interface). Configured per-interface in Gateway Properties > Topology. When a packet's source IP doesn't match the expected network for the ingress interface, it's dropped as a spoofing attempt. Also prevents internal IP addresses from appearing on external interfaces.

### Step 1 — - Configure data collection
```
# SmartConsole -- enable anti-spoofing
# Gateway Properties > Network Management > Topology
# For each interface:
#   Define topology (Internal/External)
#   Set anti-spoofing to "Prevent" or "Detect"
#   Define the network behind the interface
# Enable logging for anti-spoofing drops

# Ensure "Spoofed packets" logging is enabled:
# Global Properties > Log and Alert > Anti Spoofing
```
Verify:
```spl
index=checkpoint sourcetype="cp_log" earliest=-7d
| where match(_raw, "(?i)spoof|anti.?spoof") OR match(action, "(?i)drop") AND match(description, "(?i)spoof")
| stats count by ifname, src
| sort -count | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- Anti-spoofing violation monitoring:**
```spl
index=checkpoint sourcetype="cp_log" earliest=-24h
| where match(_raw, "(?i)spoof|anti.?spoof") OR (match(action, "(?i)drop") AND match(description, "(?i)spoof"))
| eval src=coalesce(src, source_address, src_ip)
| eval dst=coalesce(dst, destination_address, dest_ip)
| eval iface=coalesce(ifname, interface, inzone)
| eval device=coalesce(origin, host)
| iplocation src prefix=src_
| stats count as violations dc(src) as unique_sources dc(dst) as unique_targets values(src) as source_ips by device, iface
| eval severity=case(
    violations > 1000, "CRITICAL -- massive spoofing attempt (".violations." violations)",
    unique_sources > 20, "WARNING -- distributed spoofing from ".unique_sources." sources",
    violations > 100, "WARNING -- sustained spoofing activity",
    1==1, "INFO")
| where severity != "INFO"
| sort severity, -violations
```

### Step 3 — - Validate
(a) SmartConsole: Gateway > Topology -- verify anti-spoofing is "Prevent" on all interfaces.
(b) SmartConsole: Logs & Monitor -- filter for anti-spoofing events.
(c) CLI: `fw ctl zdebug + drop` -- check for anti-spoofing drops in real time.

### Step 4 — - Operationalize
Dashboard ("Check Point -- Anti-Spoofing"):
* Row 1 -- Single-value: "Spoofing violations (24h)", "Unique sources", "Interfaces affected".
* Row 2 -- Anti-spoofing violation timeline.
* Row 3 -- Top spoofed source IPs with geolocation.

Alert: Critical (>1000 violations in 1 hour): active spoofing attack or misconfiguration.

### Step 5 — - Troubleshooting

* **False positives from asymmetric routing** -- Anti-spoofing drops legitimate traffic when return path uses a different interface. Solution: adjust topology definition to include the additional network, or use `do not check packets from` exception.

* **False positives after network changes** -- Adding new subnets behind an interface requires updating the topology definition. Failing to update causes anti-spoofing drops for the new subnet. Run: `fetch topology` in SmartConsole.

* **Anti-spoofing not preventing** -- Verify mode is "Prevent" not "Detect" for production interfaces. Check: Gateway Properties > Topology > anti-spoofing setting per interface.

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(action),"(?i)drop") AND match(lower(logdesc),"(?i)anti.?spoof|spoofing")
| stats count by src, inzone, outzone, rule_name, orig
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

## Visualization

Table (spoofing violations by source), Bar chart (violations by interface/zone), Line chart (violation trend), Map (source geo if available).

## Known False Positives

Asymmetric routing, late updates, and lab VLANs can trigger spoofing detections you still need to verify.

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
