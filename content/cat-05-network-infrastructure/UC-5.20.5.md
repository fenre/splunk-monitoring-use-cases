<!-- AUTO-GENERATED from UC-5.20.5.json — DO NOT EDIT -->

---
id: "5.20.5"
title: "IPv6 Address Canonical Format Compliance"
status: "verified"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.20.5 · IPv6 Address Canonical Format Compliance

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We check that all systems write internet addresses the same way, because if one system writes '2001:DB8::1' and another writes '2001:0db8:0000:0000:0000:0000:0000:0001', our security tools won't realise they're the same address — like two people spelling a name differently on different forms.*

---

## Description

Audits IPv6 addresses across all log sources for compliance with RFC 5952, which defines the canonical text representation of IPv6 addresses: lowercase hexadecimal, leading zeros suppressed, longest run of all-zero groups compressed to '::', and no unnecessary '::' expansion. Non-canonical representations are a silent operational hazard — the same device appears as different addresses in different logs, breaking SIEM correlation, lookup table joins, threat intelligence matching, and incident investigation. RFC 9099 §2.6.1.1 explicitly warns that non-canonical IPv6 addresses are a significant operational security problem.

## Value

If your firewall logs `2001:0DB8::1`, your DHCP server logs `2001:db8:0:0:0:0:0:1`, and your RADIUS server logs `2001:DB8::1`, a search for any one form will miss the other two — and the attacker's address will only appear in one log. This is not a theoretical problem: RFC 9099 documents it as a known operational failure mode. This UC quantifies the problem per sourcetype, identifying which data sources need normalisation, and tracks compliance improvement over time. For organisations with IPv6 threat intelligence feeds, non-canonical addresses also cause feed lookups to miss matches.

## Implementation

Run the search across all indexes containing IPv6 data. The search extracts raw IPv6 addresses from event text, then checks for three common non-canonical patterns: leading zeros in groups (e.g., `0db8` instead of `db8`), uppercase hex digits (e.g., `DB8` instead of `db8`), and full expansion without '::' compression. The compliance percentage per sourcetype tells you which data sources need attention. Fix at the source (device configuration) or at ingest (Splunk Edge Processor or props.conf SEDCMD).

## Detailed Implementation

### Prerequisites
- IPv6 data must already be indexed in Splunk from any source (syslog, flow data, firewall logs, DNS logs). This UC does not require new data collection — it audits the format of addresses already in your events.
- Understanding of RFC 5952 canonical form:
  - All hex digits MUST be lowercase: `2001:db8::1` (not `2001:DB8::1`)
  - Leading zeros MUST be suppressed: `2001:db8::1` (not `2001:0db8::0001`)
  - The longest run of consecutive all-zero 16-bit groups MUST be compressed to `::`, and only once per address
  - The first sequence of zero bits gets the `::` compression if there are ties in length
- RFC 9099 §2.6.1.1 warns: "The lack of a standard representation for IPv6 addresses in logs can lead to correlation failures. All logging systems SHOULD normalize IPv6 addresses to the canonical form defined in RFC 5952."

### Step 1 — Configure data collection
No new data collection is needed. This UC audits existing data.

To identify which indexes contain IPv6 data:
```spl
| tstats count where index=* by index sourcetype
| search count > 0
| map maxsearches=20 search="search index=$index$ sourcetype=$sourcetype$ earliest=-1h | head 100 | where match(_raw, \"[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}\") | stats count as ipv6_events | eval index=\"$index$\", sourcetype=\"$sourcetype$\""
```
Or more simply:
```spl
index=* earliest=-1h
| where match(_raw, "[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}")
| stats count by index, sourcetype
| sort -count
```

### Step 2 — Create the search and alert

**Primary search — canonical compliance per sourcetype:**
```spl
index=network OR index=netflow OR index=firewall OR index=dns earliest=-24h
| rex field=_raw "(?<raw_ipv6>[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,7})"
| where isnotnull(raw_ipv6)
| eval has_leading_zeros=if(match(raw_ipv6, ":0[0-9a-fA-F]"), 1, 0)
| eval has_uppercase=if(match(raw_ipv6, "[A-F]"), 1, 0)
| eval is_fully_expanded=if(len(raw_ipv6) > 25, 1, 0)
| eval non_canonical=if(has_leading_zeros=1 OR has_uppercase=1 OR is_fully_expanded=1, 1, 0)
| stats count as total_addresses sum(non_canonical) as non_canonical_count by sourcetype
| eval compliance_pct=round((1 - non_canonical_count/total_addresses) * 100, 1)
| sort compliance_pct
```

**Understanding this SPL:**
- The regex `[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,7}` extracts strings that look like IPv6 addresses — 3 to 8 colon-separated hex groups. It won't capture addresses using `::` compression (which is fine — those are already partially canonical).
- Three non-canonical patterns checked:
  1. `has_leading_zeros`: `:0[0-9a-fA-F]` — a colon followed by a zero and another hex digit means a leading zero wasn't suppressed (e.g., `:0db8` should be `:db8`).
  2. `has_uppercase`: `[A-F]` — any uppercase hex letter violates RFC 5952.
  3. `is_fully_expanded`: length > 25 characters means the address is not using `::` compression (a fully-expanded address like `2001:0db8:0000:0000:0000:0000:0000:0001` is 39 characters).
- The compliance percentage per sourcetype immediately tells you which data sources are the worst offenders and where to focus normalisation effort.

**Variant — show specific non-canonical examples for remediation:**
```spl
index=network OR index=firewall earliest=-24h
| rex field=_raw "(?<raw_ipv6>[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,7})"
| where isnotnull(raw_ipv6) AND (match(raw_ipv6, ":0[0-9a-fA-F]") OR match(raw_ipv6, "[A-F]") OR len(raw_ipv6) > 25)
| stats count as occurrences by raw_ipv6, sourcetype, host
| sort -occurrences
| head 20
```
This shows the 20 most frequently occurring non-canonical addresses with their source device, making it easy to identify which devices need configuration changes.

**Remediation at ingest time (props.conf):**
```
[cisco:ios]
SEDCMD-lowercase_ipv6 = s/([0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{1,4}/\L&/g
```
Note: SEDCMD can handle lowercase conversion but not zero suppression or `::` compression. For full canonicalisation, use Splunk Edge Processor or a custom scripted input wrapper.

### Step 3 — Validate
(a) **Manual comparison:** Pick a non-canonical address from the results (e.g., `2001:0DB8:0000:0001:0000:0000:0000:0001`). Manually apply RFC 5952 rules: lowercase (`2001:0db8:0000:0001:0000:0000:0000:0001`), suppress leading zeros (`2001:db8:0:1:0:0:0:1`), compress longest zero run (`2001:db8:0:1::1`). Verify this canonical form is what you'd want in your correlation searches.

(b) **Cross-source correlation test:** Find an IPv6 address that appears in both syslog and flow data. Check if the representations match. If they don't, a `| join` or lookup between these sources will fail for that address.

(c) **TI feed test:** If you have an IPv6 threat intelligence feed, check if the feed uses canonical form. If so, non-canonical addresses in your logs will miss TI matches.

### Step 4 — Operationalize

**Dashboard** (panel on the "IPv6 Address Hygiene" dashboard from UC-5.20.3):
- Add a panel: "Canonical Format Compliance" — bar chart by sourcetype, compliance percentage.
- Drilldown: click a sourcetype to see the top 20 non-canonical addresses from that source.

**Scheduling:** Monthly compliance report. This is a hygiene metric, not an operational alert.

**Runbook** (owner: Logging / SIEM Engineering):
1. For each sourcetype with < 90% compliance, determine the root cause:
   - Device configuration: some platforms default to uppercase or fully-expanded format. Reconfigure where possible.
   - TA field extraction: some TAs extract IPv6 addresses without normalisation. File a feature request or apply props.conf SEDCMD.
   - Edge Processor: if using Splunk Edge Processor, add an IPv6 canonicalisation pipeline rule.
2. Target: 95%+ canonical compliance across all sourcetypes within 6 months.

### Step 5 — Troubleshooting

- **Compliance is 100% but correlation still fails** — The search only checks three common non-canonical patterns. Other issues can break correlation: different levels of `::` compression (both are valid but produce different strings), trailing spaces, or embedded IPv4 notation (`::ffff:192.0.2.1`). For reliable correlation, normalise addresses at ingest time or use a lookup macro that applies canonicalisation.

- **Very low compliance (< 50%) for a specific sourcetype** — The device or application generating those logs likely uses fully-expanded format by default. Common offenders: Windows event logs (expand all addresses), some Java/Python logging frameworks, and older Cisco NX-OS versions.

- **False matches on non-IPv6 hex strings** — If the regex matches strings that aren't IPv6 addresses, add additional context filtering: `| where match(_raw, "ipv6|IPv6|inet6|::")` to limit to events that are likely IPv6-related.

## SPL

```spl
index=network OR index=netflow OR index=firewall earliest=-24h
| rex field=_raw "(?<raw_ipv6>[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,7})"
| where isnotnull(raw_ipv6)
| eval has_leading_zeros=if(match(raw_ipv6, ":0[0-9a-fA-F]"), 1, 0)
| eval has_uppercase=if(match(raw_ipv6, "[A-F]"), 1, 0)
| eval is_fully_expanded=if(len(raw_ipv6) > 25, 1, 0)
| eval non_canonical=if(has_leading_zeros=1 OR has_uppercase=1 OR is_fully_expanded=1, 1, 0)
| stats count as total_addresses sum(non_canonical) as non_canonical_count by sourcetype
| eval compliance_pct=round((1 - non_canonical_count/total_addresses) * 100, 1)
| sort compliance_pct
```

## Visualization

(1) Table: sourcetype, total addresses, non-canonical count, compliance percentage — sorted worst-first. (2) Single-value tile: overall canonical compliance percentage across all sources. (3) Bar chart: compliance percentage by sourcetype for quick identification of the worst offenders. (4) Examples panel: sample non-canonical addresses with suggested canonical form for remediation.

## Known False Positives

**Intentionally expanded addresses in configuration contexts.** Some device configurations (ACLs, static routes) use fully-expanded IPv6 addresses for clarity or template consistency. These appear in syslog when configurations are logged, but represent intentional formatting, not a correlation problem — the log event itself is a config snippet, not a traffic record.

**Hex values in non-IPv6 contexts.** The regex may match hex strings that look like IPv6 address fragments but are actually MAC addresses, certificate hashes, or session IDs. The filter `(:[0-9a-fA-F]{1,4}){2,7}` requires at least 3 colon-separated groups, which reduces false matches, but some non-IPv6 strings may still match. Validate by spot-checking flagged entries.

**Mixed-notation IPv4-mapped addresses.** Addresses like `::ffff:192.0.2.1` use mixed IPv4/IPv6 notation, which RFC 5952 permits. These may appear non-canonical by the uppercase/expansion checks but are correctly formatted.

## References

- [RFC 5952 — A Recommendation for IPv6 Address Text Representation](https://www.rfc-editor.org/rfc/rfc5952)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.1 — Logging format)](https://www.rfc-editor.org/rfc/rfc9099)
