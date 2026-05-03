<!-- AUTO-GENERATED from UC-5.6.7.json — DO NOT EDIT -->

---
id: "5.6.7"
title: "DNS Record Change Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.6.7 · DNS Record Change Audit

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Configuration, Compliance

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

Unauthorized DNS changes can redirect traffic to attacker infrastructure (DNS hijacking).

## Value

DNS and security teams maintain a complete audit trail of DNS record changes, detecting unauthorized modifications to critical records, after-hours changes, and bulk modifications that may indicate DNS hijacking or misconfiguration.

## Implementation

Forward DNS server audit logs. Alert on changes to critical domains. Correlate with change tickets.

## Detailed Implementation

### Prerequisites
- DNS zone change/audit logs in `index=dns` or `index=audit`. Sources: Infoblox NIOS audit logs (`sourcetype=infoblox:audit` — tracks all NIOS API/GUI changes including zone modifications), Windows DNS Server audit events (Event IDs 540-582 for zone changes), or BIND `named` with `update-security-log` enabled.
- DNS record changes (A, AAAA, CNAME, MX, NS, TXT modifications) are high-impact events: a hijacked A record redirects traffic to an attacker, a modified MX record intercepts email, a changed NS record delegates a zone to a malicious server.
- Build a `dns_critical_records.csv` lookup: `fqdn,record_type,expected_value,owner` listing your most important DNS records (corporate website, email MX, API endpoints, identity providers).
- For dynamic DNS (DDNS) environments: legitimate record changes are frequent. Focus alerting on static zones (manually managed records) where changes are rare and should go through change management.

### Step 1 — Configure data collection
Verify audit log availability:
```spl
index=dns OR index=audit (sourcetype="infoblox:audit" OR sourcetype="MSAD:NT6:DNS") earliest=-24h
| search "record" OR "zone" OR "add" OR "modify" OR "delete" OR "update"
| stats count by sourcetype, host
```

### Step 2 — Create the search and alert

**Primary search — DNS record change audit:**
```spl
index=dns OR index=audit (sourcetype="infoblox:audit" OR sourcetype="MSAD:NT6:DNS") earliest=-24h
| search "record" OR "zone" OR "add" OR "modify" OR "delete" OR "update"
| rex field=_raw "(?i)(?:action|operation)[\s:=]+(?<change_action>\w+)"
| rex field=_raw "(?i)(?:name|record|fqdn)[\s:=]+(?<record_name>[\w.-]+)"
| rex field=_raw "(?i)(?:type)[\s:=]+(?<record_type>\w+)"
| rex field=_raw "(?i)(?:user|admin|by)[\s:=]+(?<changed_by>[\w@.-]+)"
| rex field=_raw "(?i)(?:value|data|address|rdata)[\s:=]+(?<new_value>[^\s,;]+)"
| where isnotnull(change_action) AND isnotnull(record_name)
| lookup dns_critical_records.csv fqdn as record_name OUTPUT owner expected_value
| eval is_critical=if(isnotnull(owner), "CRITICAL RECORD", "Standard")
| table _time, host, changed_by, change_action, record_name, record_type, new_value, is_critical, owner
| sort -_time
```

#### Understanding this SPL: Extracts the who/what/when/how of every DNS record change. The `dns_critical_records.csv` lookup flags changes to business-critical records. A change to `www.company.com` by an unauthorized user is a critical security event (DNS hijacking). Regex patterns cover common audit log formats across Infoblox, Windows, and BIND.

**Unauthorized change detection (outside change window):**
```spl
index=dns OR index=audit (sourcetype="infoblox:audit") earliest=-24h
| search "record" "add" OR "modify" OR "delete"
| rex field=_raw "(?i)(?:user|admin)[\s:=]+(?<changed_by>[\w@.-]+)"
| rex field=_raw "(?i)(?:name|fqdn)[\s:=]+(?<record_name>[\w.-]+)"
| eval hour=strftime(_time, "%H")
| eval is_business_hours=if(hour >= 8 AND hour < 18, "yes", "no")
| eval day_of_week=strftime(_time, "%w")
| eval is_weekend=if(day_of_week==0 OR day_of_week==6, "yes", "no")
| where is_business_hours="no" OR is_weekend="yes"
| table _time, host, changed_by, record_name, is_weekend
| sort -_time
```

**Bulk change detection (mass modification):**
```spl
index=dns OR index=audit (sourcetype="infoblox:audit") earliest=-1h
| search "record"
| rex field=_raw "(?i)(?:user|admin)[\s:=]+(?<changed_by>[\w@.-]+)"
| stats count dc(eval(if(match(_raw, "(?i)add"), _raw, null()))) as adds dc(eval(if(match(_raw, "(?i)delete"), _raw, null()))) as deletes by changed_by
| where count > 20
| eval alert="Bulk DNS change: ".changed_by." made ".count." changes in 1 hour"
| sort -count
```

### Step 3 — Validate
(a) Make a test DNS record change (add a TXT record) and verify it appears in the audit search within minutes.
(b) Verify the `changed_by` field accurately identifies the administrator. For Infoblox, this comes from NIOS audit logs. For Windows, from the Security event log.
(c) Cross-reference with change management: recent DNS changes should have corresponding change tickets.

### Step 4 — Operationalize
Dashboard ("DNS — Record Change Audit"):
- Row 1 — Single-value tiles: "Changes (24h)", "Critical record changes", "After-hours changes", "Bulk changes".
- Row 2 — Change audit table: time, admin, action, record, type, value, criticality.
- Row 3 — Timeline: changes over 7 days by action type (add/modify/delete).

Alerting:
- Critical (change to any record in `dns_critical_records.csv`): alert security and DNS owner immediately.
- High (any change outside business hours or on weekends): alert for review.
- Warning (bulk changes > 20 in 1 hour by single admin): verify against change management.

Runbook:
1. **Unauthorized critical record change**: Immediately verify the record's current value (`dig <record>`). If hijacked, revert to the expected value. Investigate the admin account that made the change — possible compromised credentials.
2. **After-hours change**: Contact the administrator and verify the change was planned. If not, treat as potential compromise.

### Step 5 — Troubleshooting

- **Infoblox audit logs don't capture all changes** — Ensure audit logging is enabled at the Grid level: Grid > Grid Manager > Audit Log. Set to capture "All" or at minimum "Configuration changes".

- **Windows DNS changes not logged** — Enable DNS Server audit logging via Group Policy: `Computer Configuration > Policies > Windows Settings > Security Settings > Advanced Audit Policy > Object Access > Audit Other Object Access Events`.

- **Dynamic DNS updates flooding the audit** — DDNS updates from DHCP (automatic A/PTR record creation) generate high volumes. Filter: `| where changed_by!="DHCP"` or exclude PTR record changes for DDNS zones.

## SPL

```spl
index=dns sourcetype="infoblox:audit" ("Added" OR "Deleted" OR "Modified") AND ("record" OR "zone")
| table _time admin record_type record_name record_data action | sort -_time
```

## Visualization

Table (record, action, who, when), Timeline, Single value.

## Known False Positives

Planned cutovers, DDI automation, and bulk import jobs can produce bursts of add/delete events that are authorized but look noisy; align to change records.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
