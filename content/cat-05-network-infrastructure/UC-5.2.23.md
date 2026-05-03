<!-- AUTO-GENERATED from UC-5.2.23.json — DO NOT EDIT -->

---
id: "5.2.23"
title: "Firewall Rule Hit Analysis and Top Denied Flows (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.23 · Firewall Rule Hit Analysis and Top Denied Flows (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We list top denied flows on the small office device so you can see scanning, bad apps, and policy gaps without digging through raw logs by hand.*

---

## Description

Identifies top denied flows to optimize firewall rules and detect policy violations.

## Value

Security teams analyze Meraki MX firewall rule hit patterns, identifying top denied flows and validating rule effectiveness against security policy.

## Implementation

Analyze firewall deny events from flow logs. Correlate with rules.

## Detailed Implementation

### Prerequisites
* Meraki MX firewall rule logs via syslog. Data in `index=meraki` with `sourcetype=meraki:events`. Key fields: `pattern` (allow/deny), `src`, `dst`, `sport`, `dport`, `protocol`, `policy` (rule that matched).
* Meraki MX firewall rules: Layer 3 and Layer 7 rules configured in Dashboard. Rules process top-down. Default rule at bottom is typically "Allow all" or "Deny all".

### Step 1 — - Configure data collection
```
# Dashboard > Security & SD-WAN > Firewall
# Configure L3 and L7 rules
# Syslog > Roles: Flows
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)flows|firewall|deny|allow|pattern")
| stats count by pattern
```

### Step 2 — - Create the search and alert

**Primary search -- Firewall rule hit analysis and top denied flows:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)flows|firewall")
| eval act=lower(coalesce(pattern, action))
| eval src=coalesce(src, src_ip)
| eval dst=coalesce(dst, dest, dest_ip)
| eval dport=coalesce(dport, dest_port)
| eval proto=coalesce(protocol, proto)
| where act="deny" OR act="blocked" OR act="drop"
| stats count as denials dc(src) as unique_sources dc(dst) as unique_targets dc(dport) as unique_ports by host
| eval severity=case(denials > 10000, "HIGH -- heavy denial volume", unique_sources > 100, "WARNING -- many denied sources", 1==1, "INFO")
| where severity != "INFO"
```

**Top denied flows:**
```spl
index=meraki sourcetype="meraki:events" pattern="deny" earliest=-4h
| eval src=coalesce(src, src_ip)
| eval dst=coalesce(dst, dest_ip)
| eval dport=coalesce(dport, dest_port)
| stats count as denials by src, dst, dport, protocol
| sort -denials | head 20
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Firewall -- check rule order and hit counts.
(b) Compare denial counts with Dashboard event log.
(c) Verify default rule action (allow or deny).

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Firewall Rules"):
* Row 1 -- Single-value: "Total denials", "Unique denied sources", "Unique denied targets".
* Row 2 -- Top denied flows table.

Alerting:
* High (denials > 10K/hr from single source): scanning or misconfigured device.

### Step 5 — - Troubleshooting

* **Legitimate traffic denied** -- Check rule order in Dashboard. Meraki processes rules top-down -- a broad deny rule above a specific allow rule will block traffic. Move allow rules higher.

* **Default deny rule getting all hits** -- Most traffic doesn't match any specific rule. Review if additional allow rules are needed for required services.

* **No deny events in syslog** -- Verify: syslog roles include "Flows" and syslog server is configured correctly.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow action="deny"
| stats count as deny_count by firewall_rule, src, dest, dest_port
| sort - deny_count
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action IN ("deny","denied","drop","dropped","blocked","block")
  by All_Traffic.src All_Traffic.dest span=1h
| sort -count
```

## Visualization

Top denied flows table; denial timeline; source/dest distribution heatmap.

## Known False Positives

Port scans, misconfigured clients, and noisy default-deny rules can flood deny counts without a targeted attack.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
