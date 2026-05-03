<!-- AUTO-GENERATED from UC-5.8.27.json — DO NOT EDIT -->

---
id: "5.8.27"
title: "Infoblox DNS Firewall and RPZ Threat Block Events"
status: "draft"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.8.27 · Infoblox DNS Firewall and RPZ Threat Block Events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Status:** Draft

*We help you see when Infoblox blocks bad DNS in real time, so you can act while the event is still fresh.*

---

## Description

Infoblox Threat Protection and response policy zones block queries to known malicious or policy-violating names. Aggregating blocks by client, threat category, and domain validates policy coverage and reveals infected or compromised endpoints.

## Value

Security operations teams leverage Infoblox DNS Firewall and RPZ block events to identify infected or compromised endpoints, validate threat feed coverage, and provide actionable SOC visibility without waiting for proxy or endpoint telemetry.

## Implementation

Forward Infoblox DNS Firewall and Threat Protection logs to Splunk via syslog. Install `Splunk_TA_infoblox` for CIM-compatible extractions under `infoblox:threatprotect`. Enrich `src_ip` with DHCP or AD identity where available. Tune out noisy NAT gateways using internal subnet lookups.

## Detailed Implementation

### Prerequisites
- Splunk Add-on for Infoblox (Splunk_TA_infoblox, Splunkbase 2934) installed for CIM-compatible field extractions. Infoblox NIOS configured to forward Threat Protection / DNS Firewall syslog to Splunk via syslog (UDP/TCP 514 or TLS 6514).
- Data in `index=dns` (or `index=infoblox`) with `sourcetype=infoblox:threatprotect`. Key fields: `src_ip` (client querying the blocked domain), `threat_type` (malware, phishing, botnet, adware, etc.), `threat_rule` (RPZ rule name or threat feed name), `domain` (blocked domain name), `action` (NXDOMAIN, NODATA, PASSTHRU, DROP), `severity`, `feed_name` (e.g., "infoblox-base-rpz", "custom-block-list").
- Infoblox DNS Firewall uses Response Policy Zones (RPZ) to block queries to malicious domains. RPZ feeds include: (1) Infoblox Threat Intelligence (commercial feed), (2) Custom RPZ zones (organization-specific block lists), (3) Third-party feeds (abuse.ch, etc.). When a query matches an RPZ entry, Infoblox returns a modified response (typically NXDOMAIN) instead of the actual DNS answer.
- Build `infoblox_threat_severity.csv` lookup: `threat_type,severity_override,response_action` (e.g., `malware,critical,investigate`, `adware,low,monitor`).

### Step 1 — Configure data collection
Verify Threat Protection data:
```spl
index=dns sourcetype="infoblox:threatprotect" earliest=-24h
| stats count by threat_type, action
| sort -count
```
Healthy output: blocks distributed across threat types (malware, phishing, botnet). If empty: verify Infoblox Threat Protection is enabled (Data Management > DNS > Threat Protection), syslog forwarding is configured, and the TA is installed.

### Step 2 — Create the search and alert

**Primary search — Top threat sources with enrichment:**
```spl
index=dns sourcetype="infoblox:threatprotect" earliest=-24h
| stats count as blocks dc(domain) as unique_domains values(threat_type) as threat_types latest(_time) as last_seen by src_ip
| lookup infoblox_threat_severity.csv threat_type as threat_types OUTPUT severity_override response_action
| eval severity=coalesce(severity_override, case(blocks > 100, "critical", blocks > 20, "high", blocks > 5, "medium", 1==1, "low"))
| lookup dhcp_leases.csv ip as src_ip OUTPUT mac hostname username
| eval client_label=case(isnotnull(username), username." (".hostname.")", isnotnull(hostname), hostname, 1==1, src_ip)
| sort -blocks
| head 40
```

#### Understanding this SPL: A client with many DNS Firewall blocks is either: (1) infected with malware (calling home to C2 domains), (2) compromised and exfiltrating data via DNS, (3) a user visiting many phishing/ad domains (less urgent), or (4) a NAT gateway aggregating multiple users (check unique_domains to distinguish). The DHCP lease lookup enriches the IP with the actual user identity — critical for incident response.

**Threat type distribution:**
```spl
index=dns sourcetype="infoblox:threatprotect" earliest=-7d
| bin _time span=1d
| stats count by _time, threat_type
| timechart span=1d sum(count) by threat_type
```

**Newly blocked domains (first seen in 24h):**
```spl
index=dns sourcetype="infoblox:threatprotect" earliest=-24h
| stats count min(_time) as first_block by domain, threat_type
| where first_block > relative_time(now(), "-24h@h")
| sort -count
| head 20
```

**RPZ feed effectiveness:**
```spl
index=dns sourcetype="infoblox:threatprotect" earliest=-7d
| stats count as blocks dc(domain) as unique_domains dc(src_ip) as clients_protected by feed_name
| sort -blocks
```

### Step 3 — Validate
(a) In Infoblox Grid Manager: Reporting > DNS Threat Protection. Compare block counts by threat type with Splunk results.
(b) Attempt to resolve a known-blocked domain from a test client and verify the block event appears in Splunk within seconds.
(c) Verify RPZ feed status: Data Management > DNS > Response Policy Zones — all feeds should be active and recently updated.

### Step 4 — Operationalize
Dashboard ("Infoblox DNS Firewall"):
- Row 1 — Single-value tiles: "Blocks (24h)", "Unique malicious domains", "Clients with blocks", "Feed coverage (active feeds)".
- Row 2 — Top blocked clients table with identity enrichment: client, blocks, unique domains, threat types, severity.
- Row 3 — Threat type trending (7 days).
- Row 4 — RPZ feed effectiveness: feed name, blocks, domains covered, clients protected.

Alerting:
- Critical (client with > 100 blocks to malware/botnet domains in 1 hour): possible active infection — isolate and investigate.
- High (new domain blocked > 10 times in 1 hour): emerging threat — verify RPZ feed coverage.
- Warning (RPZ feed not updated in > 24 hours): threat intelligence may be stale.

### Step 5 — Troubleshooting

- **No threatprotect events** — Verify: (1) DNS Firewall is licensed and enabled on the Infoblox grid, (2) RPZ feeds are configured and active, (3) syslog logging level includes threat protection events (typically "info" or higher), (4) the TA is parsing syslog into the correct sourcetype.

- **High false positive rate** — Some RPZ feeds are aggressive (blocking ad domains, trackers). Review the `feed_name` field to identify which feed is generating the most blocks. Custom feeds can be tuned; commercial feeds may need category exclusions.

- **src_ip is always the same (NAT gateway)** — All clients behind a NAT appear as the same source IP. Enable DNS query logging with client subnet (EDNS Client Subnet) or correlate with DHCP lease data to identify individual clients.

## SPL

```spl
index=dns sourcetype="infoblox:threatprotect" earliest=-24h
| stats count by src_ip, threat_type, threat_rule, domain
| sort -count
| head 40
```

## Visualization

Table (top blocked clients), Bar chart (threat_type), Timeline (block volume).

## Known False Positives

RPZ and firewall hits spike during false-positive list updates; tune lists and see Infoblox threat analytics before major incident call.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
