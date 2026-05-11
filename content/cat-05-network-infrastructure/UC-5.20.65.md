<!-- AUTO-GENERATED from UC-5.20.65.json — DO NOT EDIT -->

---
id: "5.20.65"
title: "IPv6 Firewall Deny Log Analysis — Blocked Traffic Characterisation"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.65 · IPv6 Firewall Deny Log Analysis — Blocked Traffic Characterisation

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*Every time the security guard turns someone away at the door, they write it in a logbook. We read through this logbook to find patterns. Sometimes we discover the guard is accidentally blocking people who should be allowed in (like the postman who delivers important letters). Other times we find records of suspicious people who tried to sneak in.*

---

## Description

Analyses IPv6 firewall deny logs to characterise blocked traffic into actionable categories: misconfiguration indicators (blocked NDP, PMTUD, SLAAC), security threats (scanning, spoofing, tunnel leakage), and operational gaps (applications lacking IPv6 firewall rules). The deny log is one of the most valuable data sources for IPv6 troubleshooting — patterns in denied traffic reveal both attacks and self-inflicted wounds.

## Value

IPv6 deny logs contain the answers to two critical questions: (1) 'Is the firewall blocking something it should not be blocking?' — revealed by denied NDP, ICMPv6 essential types, or legitimate application traffic, and (2) 'Is someone probing my IPv6 space?' — revealed by scanning patterns, bogon sources, or tunnel probes. Without structured analysis, deny logs are noise. With categorisation, they become the primary diagnostic tool for both IPv6 security and connectivity issues.

## Implementation

Collect firewall deny/drop logs. Filter to IPv6 traffic. Categorise each denied flow into actionable categories (misconfiguration, scanning, application gap, etc.). Alert on misconfiguration indicators. Track scanning activity.

## Detailed Implementation

### Prerequisites
- Firewall deny/drop logging enabled and forwarded to Splunk.
- Sufficient log volume to identify patterns (at least 24 hours).
- Firewall role lookup (perimeter vs internal) to contextualise findings.

### Step 1 — Configure data collection

**Palo Alto — deny logs:**
Palo Alto logs denied traffic automatically when the default deny rule is hit. Ensure the default deny rule has logging enabled:
```
set rulebase security rules "Default Deny" log-end yes
```
For interzone traffic, configure the interzone-default rule to log:
```
set rulebase security rules "interzone-default" log-end yes
```

**Cisco ASA — deny logs:**
```
logging enable
logging trap 6
logging class flow level 4
```
Deny events appear as syslog messages: `%ASA-4-106100: access-list acl_name denied ...`

**Verification:**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:asa") (action="denied" OR action="drop" OR "denied" OR "Deny") earliest=-1h
| eval is_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}"), 1, 0)
| stats count(eval(is_ipv6=1)) as ipv6_denies count(eval(is_ipv6=0)) as ipv4_denies by host
```

### Step 2 — Create the search and alert

**Misconfiguration alert (blocked essential ICMPv6):**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:asa") (action="denied" OR "denied") earliest=-1h
| eval is_critical_block=case(
    match(_raw, "(?i)icmpv6.*packet.too.big|icmpv6.*type.?2"), "PMTUD broken",
    match(_raw, "(?i)icmpv6.*router.solicit|icmpv6.*type.?133"), "SLAAC broken",
    match(_raw, "(?i)icmpv6.*router.advert|icmpv6.*type.?134"), "SLAAC broken",
    match(_raw, "(?i)icmpv6.*neighbor.solicit|icmpv6.*type.?135"), "NDP broken",
    match(_raw, "(?i)ff02::1:ff"), "Solicited-node multicast blocked",
    1=1, null())
| where isnotnull(is_critical_block)
| stats count as events values(is_critical_block) as impact by host
| eval alert="CRITICAL — firewall " . host . " is blocking essential IPv6 traffic: " . mvjoin(impact, ", ")
```
Trigger: any event. These deny categories should never appear — their presence definitively indicates a firewall misconfiguration.

**IPv6 scanning detection:**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:asa") (action="denied" OR "denied") earliest=-1h
| eval is_ipv6_dest=if(match(dest, ":"), 1, 0)
| where is_ipv6_dest=1
| rex field=dest "(?<dest_prefix>[0-9a-fA-F:]+:)[0-9a-fA-F]+$"
| stats dc(dest) as unique_targets count as attempts by src, dest_prefix
| where unique_targets > 20
| eval alert="IPv6 scan detected: " . src . " probed " . unique_targets . " addresses in " . dest_prefix . "/64"
```

**Application IPv6 gap analysis:**
```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:asa") (action="denied" OR "denied") earliest=-7d
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| rex field=_raw "(?:rule|acl)\s*=?\s*(?<denied_by>\S+)"
| stats count as denies dc(src) as unique_sources by dest, dest_port, denied_by
| where denies > 100 AND unique_sources > 5
| eval recommendation="Consider adding IPv6 firewall rule for " . dest . ":" . dest_port . " — denied " . denies . " times from " . unique_sources . " sources"
| sort -denies
```
This identifies IPv6 traffic that is consistently denied from multiple sources — likely legitimate traffic that lacks a permit rule.

### Step 3 — Validate
(a) **Blocked ICMPv6 PTB.** Temporarily deny ICMPv6 Type 2 on a test firewall. Verify the misconfiguration alert fires.

(b) **Scanning detection.** Use a test tool to probe multiple addresses in a /64. Verify the scanning detection search identifies the pattern.

(c) **Application gap.** Identify a known application that communicates over IPv6 but has been denied. Verify the gap analysis search identifies it.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Firewall Deny Analysis"):
- Row 1 — Alert panel: misconfiguration indicators (CRITICAL — blocked essential ICMPv6).
- Row 2 — Pie chart: deny category distribution.
- Row 3 — Timechart: deny volume by category over 7 days.
- Row 4 — Table: application gap candidates (high-volume denied destinations).
- Row 5 — Table: scanning activity summary.

**Scheduling:** Misconfiguration alert every 5 minutes. Scanning detection every 15 minutes. Application gap analysis weekly.

**Runbook:**
1. Blocked essential ICMPv6: URGENT — fix the firewall rule immediately (UC-5.20.64). Test PMTUD and NDP after the fix.
2. IPv6 scanning: expected at perimeter. Investigate if from internal sources. Block persistent external scanners at upstream provider if necessary.
3. Application gap: work with application team to verify IPv6 is intended. If yes, add firewall rule. If no, fix the application to not attempt IPv6.

### Step 5 — Troubleshooting

- **Log volume** — IPv6 deny logs can be very high-volume at the internet perimeter due to background scanning. Consider summary indexing to aggregate deny events by source-prefix rather than individual source address.

- **False negatives** — Some firewalls log denies as 'silent drops' without generating a log entry. Verify the firewall is configured to log denied traffic (not just permitted traffic).

- **IPv4-mapped addresses** — Some firewalls log IPv4 traffic with IPv4-mapped IPv6 addresses (::ffff:a.b.c.d). Filter these out of IPv6 deny analysis to avoid mixing IPv4 and IPv6 deny events.

## SPL

```spl
index=network (sourcetype="pan:traffic" OR sourcetype="cisco:asa" OR sourcetype="cisco:ios") action="denied" earliest=-24h
| eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0)
| where is_ipv6=1
| eval deny_category=case(
    match(dest, "^[Ff][Ff]02::1:[Ff][Ff]"), "NDP solicited-node multicast BLOCKED — firewall misconfiguration",
    match(_raw, "(?i)packet.too.big|icmpv6.*type.?2"), "ICMPv6 PTB BLOCKED — PMTUD broken",
    match(_raw, "(?i)router.solicit|router.advert|icmpv6.*type.?13[34]"), "RA/RS BLOCKED — SLAAC broken",
    match(_raw, "(?i)neighbor.solicit|neighbor.advert|icmpv6.*type.?13[56]"), "NDP NS/NA BLOCKED — resolution broken",
    match(src, "^[Ff][Ee][89AaBb]"), "Link-local source denied (may be legitimate)",
    match(src, "^2001:[Dd][Bb]8:"), "Documentation address source (test config leak)",
    match(dest_port, "^(22|3389|445|1433|3306|5432)$"), "Admin/DB service probe BLOCKED (expected)",
    1=1, "General deny")
| stats count as events first(_time) as first_seen last(_time) as last_seen by deny_category, src, dest
| sort -events
```

## Visualization

(1) Pie chart: deny category distribution. (2) Timechart: deny volume by category over 7 days. (3) Table: top denied sources and destinations. (4) Alert panel: misconfiguration indicators (blocked NDP, PMTUD).

## Known False Positives

**Internet background radiation.** IPv6 scanning from the internet produces a constant stream of deny events. This is expected at the perimeter and should not trigger alerts unless the volume or pattern changes significantly.

**Happy Eyeballs fallback.** When a client attempts IPv6 first and the firewall denies the IPv6 connection, the client falls back to IPv4 silently. This is working-as-designed for the client, but the denied IPv6 connection should be investigated — it may indicate a missing firewall rule rather than a deliberate block.

**Expired session re-establishment.** After a firewall session table entry expires, the next packet in the flow is denied. This is normal for long-lived but idle connections (e.g., SSH sessions that timed out).

## References

- [RFC 4890 — Recommendations for Filtering ICMPv6 Messages in Firewalls](https://www.rfc-editor.org/rfc/rfc4890)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks](https://www.rfc-editor.org/rfc/rfc9099)
