<!-- AUTO-GENERATED from UC-5.20.93.json — DO NOT EDIT -->

---
id: "5.20.93"
title: "GDPR IPv6 Address Privacy Compliance — Personal Data Protection"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.93 · GDPR IPv6 Address Privacy Compliance — Personal Data Protection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*In Europe, your new postal address (IPv6) is considered personal information — like your name or phone number. Some addresses even contain your house ID number (MAC address from EUI-64). The privacy law (GDPR) says we can't keep personal addresses in our records forever and must handle them carefully.*

---

## Description

Audits IPv6 address handling practices for GDPR compliance. Following the EU Court of Justice *Breyer* ruling, IPv6 addresses are personal data under GDPR when they can be linked to an individual. This use case detects EUI-64 addresses (which embed hardware MAC addresses), monitors log retention periods for IPv6-containing data, and identifies logs that may need anonymisation, pseudonymisation, or deletion to comply with GDPR data minimisation and retention requirements.

## Value

GDPR non-compliance fines can reach 4% of global annual turnover or €20 million. IPv6 addresses are a frequently overlooked source of personal data in network logs. EUI-64 addresses are particularly concerning because they contain persistent hardware identifiers that can track individuals across networks and time. This audit ensures IPv6 address data is handled with appropriate privacy controls — anonymisation for long-term analytics, pseudonymisation for security monitoring, and deletion schedules for compliance.

## Implementation

Scan all log sources for IPv6 addresses. Identify EUI-64 addresses. Audit retention periods. Recommend anonymisation or pseudonymisation for long-term retention. Verify deletion capability for right-to-erasure requests.

## Detailed Implementation

### Prerequisites
- Data Protection Impact Assessment (DPIA) for IPv6 address processing.
- Defined data retention policies per log category.
- Understanding of GDPR legitimate interest basis for security monitoring.

### Step 1 — Configure data collection

**IPv6 address data inventory:**
```spl
index=* earliest=-1d
| eval contains_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){3,7}"), 1, 0)
| where contains_ipv6=1
| stats count as events by index, sourcetype
| eval data_category=case(
    match(sourcetype, "firewall|traffic|paloalto"), "Security logs",
    match(sourcetype, "netflow|ipfix"), "Flow data",
    match(sourcetype, "syslog|cisco"), "Infrastructure logs",
    match(sourcetype, "web|access"), "Web access logs",
    1=1, "Other")
| table index, sourcetype, data_category, events
| sort -events
```
This creates an inventory of all indexes and sourcetypes that contain IPv6 address data.

**EUI-64 detection across all logs:**
```spl
index=* earliest=-7d
| rex field=_raw "(?<ipv6_addr>[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){7})"
| eval iid=mvindex(split(ipv6_addr, ":"), 5)
| eval is_eui64=if(match(iid, "(?i)[0-9a-fA-F]{2}[Ff][Ff]"), 1, 0)
| where is_eui64=1
| stats count as occurrences dc(ipv6_addr) as unique_addresses by index, sourcetype
| eval gdpr_action="EUI-64 addresses contain hardware MAC — consider anonymisation or elimination"
```

**Verification:**
```spl
index=network sourcetype="netflow" earliest=-24h | eval has_ipv6=if(isnotnull(sourceIPv6Address), 1, 0) | stats count(eval(has_ipv6=1)) as ipv6_records
```

### Step 2 — Create privacy compliance dashboard

**Retention period audit:**
```spl
| rest /services/data/indexes
| eval retention_days=frozenTimePeriodInSecs / 86400
| table title, frozenTimePeriodInSecs, retention_days
| join type=left title [| search index=* earliest=-1d | eval has_ipv6=if(match(_raw, ":"), 1, 0) | where has_ipv6=1 | stats count as ipv6_events by index | rename index as title]
| where isnotnull(ipv6_events)
| eval gdpr_status=case(
    retention_days > 365, "REVIEW — IPv6 data retained >1 year. Verify GDPR justification.",
    retention_days > 90, "ACCEPTABLE — verify anonymisation for long-term analytics",
    1=1, "OK")
| table title, retention_days, ipv6_events, gdpr_status
```

**Anonymisation readiness:**
```spl
| makeresults
| eval capability=mvappend(
    "IPv6 address truncation to /48 before analytics",
    "EUI-64 elimination (RFC 7217 deployment)",
    "Log pseudonymisation (hash IPv6 with rotating salt)",
    "Right-to-erasure capability (delete specific IPv6 entries)",
    "Data retention automation (auto-delete after policy period)")
| mvexpand capability
| lookup gdpr_readiness.csv capability OUTPUT status
| table capability, status
```

### Step 3 — Validate
(a) **EUI-64 verification.** Identify a sample EUI-64 address from logs. Verify the extracted MAC matches a known device. This demonstrates the personal data risk.

(b) **Retention test.** Check the oldest IPv6-containing event in each index. Verify it falls within the defined retention period.

(c) **Anonymisation test.** Apply IPv6 address truncation to a sample dataset. Verify the truncated addresses cannot be linked to individuals.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — GDPR Privacy Compliance"):
- Row 1 — Single-value: EUI-64 addresses in logs (target: 0). Log sources with IPv6 data.
- Row 2 — Table: data inventory — indexes/sourcetypes containing IPv6 addresses with retention periods.
- Row 3 — Anonymisation readiness checklist.
- Row 4 — Trend: EUI-64 address count over time (should decrease as RFC 7217 is deployed).

**Scheduling:** Monthly compliance review. Quarterly DPO reporting.

**Runbook:**
1. EUI-64 detected: Deploy RFC 7217 stable identifiers on the source device (UC-5.20.80). This eliminates the privacy issue at source.
2. Excessive retention: Implement index lifecycle management with anonymisation before archival.
3. Right-to-erasure request: Use `| delete` (requires admin role) or index-level event deletion to remove specific IPv6 address records.

### Step 5 — Troubleshooting

- **Anonymisation sufficiency.** Truncating IPv6 addresses to /48 removes the interface identifier but retains the network prefix. In small organisations, the /48 prefix alone may still identify the user's location. Consider truncating to /32 (RIR allocation level) for stronger anonymisation.

- **Pseudonymisation with HMAC.** Replace IPv6 addresses with HMAC(address, rotating_key) for security analytics. This preserves correlation capability within a rotation period while preventing long-term tracking.

- **Cross-dataset correlation.** Even anonymised IPv6 addresses may be re-identifiable through correlation with other datasets (timestamps, user agents, session IDs). Assess re-identification risk as part of the DPIA.

## SPL

```spl
index=network earliest=-30d
| eval contains_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,7}"), 1, 0)
| where contains_ipv6=1
| eval has_eui64=if(match(_raw, "[0-9a-fA-F]{1,4}:[Ff][Ff][Ff][Ee]:[0-9a-fA-F]{1,4}"), 1, 0)
| eval retention_days=round((now() - _time) / 86400, 0)
| eval gdpr_concern=case(
    has_eui64=1 AND retention_days > 90, "HIGH — EUI-64 address (contains MAC) retained >90 days",
    has_eui64=1, "MEDIUM — EUI-64 address (contains hardware identifier) in logs",
    retention_days > 365, "MEDIUM — IPv6 address retained >1 year without anonymisation",
    1=1, null())
| where isnotnull(gdpr_concern)
| stats count as events dc(host) as sources max(retention_days) as max_retention by gdpr_concern
| sort -events
```

## Visualization

(1) Single-value: EUI-64 addresses in logs (privacy risk indicator). (2) Table: log sources with IPv6 data and retention periods. (3) Heatmap: retention period by log source. (4) Trend: EUI-64 elimination progress.

## Known False Positives

**Non-EU data subjects.** GDPR applies to EU data subjects regardless of where the data is processed. However, logs from networks that serve only non-EU users may not be subject to GDPR IPv6 requirements.

**Anonymised data.** If IPv6 addresses are truncated to /48 or /32 prefixes before long-term storage, the data may no longer be personal data (depends on whether the prefix alone can identify an individual). Verify anonymisation is sufficient.

**Security incident retention.** GDPR allows extended retention for legitimate security purposes (Article 6(1)(f)). Security incident logs containing IPv6 addresses may be retained longer than general logs if justified.

## References

- [CJEU *Breyer v. Germany* (C-582/14) — Dynamic IP addresses as personal data](https://curia.europa.eu/juris/document/document.jsf?docid=184668)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.1 — privacy considerations)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 7721 — Security and Privacy Considerations for IPv6 Address Generation Mechanisms](https://www.rfc-editor.org/rfc/rfc7721)
- [GDPR Article 5(1)(e) — Storage Limitation Principle](https://gdpr-info.eu/art-5-gdpr/)
