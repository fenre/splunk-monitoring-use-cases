<!-- AUTO-GENERATED from UC-5.8.28.json — DO NOT EDIT -->

---
id: "5.8.28"
title: "Infoblox DNS Zone Transfer (AXFR/IXFR) Attempts"
status: "draft"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.8.28 · Infoblox DNS Zone Transfer (AXFR/IXFR) Attempts

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Audit &middot; **Status:** Draft

*We help you catch unexpected zone transfer attempts, which can be normal in some designs but a red flag in others.*

---

## Description

Unauthorised zone transfers expose the entire zone contents to an attacker. Legitimate transfers should originate only from known secondary nameservers. Monitoring AXFR and IXFR queries surfaces reconnaissance and misconfiguration quickly.

## Value

Security operations teams detect unauthorized DNS zone transfer attempts (AXFR/IXFR) that could expose the entire DNS namespace, while monitoring authorized secondary server transfer health for zone replication integrity.

## Implementation

Ensure Infoblox query logging includes type AXFR/IXFR. Install the Infoblox TA and confirm field aliases for query type and client IP. Maintain a lookup of approved secondary IPs; alert on transfers from unknown sources. Review monthly with DNS operations.

## Detailed Implementation

### Prerequisites
- Splunk Add-on for Infoblox (Splunk_TA_infoblox, Splunkbase 2934) installed. Infoblox NIOS DNS audit logs forwarded to Splunk via syslog. Data in `index=dns` (or `index=infoblox`) with `sourcetype=infoblox:dns` or `sourcetype=infoblox:audit`.
- Key fields for zone transfers: `query_type` (AXFR or IXFR), `src_ip` (requesting server), `domain` (zone being transferred), `action` (allowed/denied), `response_code` (NOERROR, REFUSED, NOTAUTH).
- Zone transfers (AXFR = full transfer, IXFR = incremental transfer) replicate DNS zone data between authoritative servers. Authorized zone transfers between primary and secondary DNS servers are normal. Unauthorized zone transfer attempts are a significant security concern: an attacker can enumerate all hostnames, IP addresses, and service records in a domain.
- Build `authorized_transfer_peers.csv` lookup: `domain,authorized_ip,server_role` (e.g., `corp.example.com,10.1.1.2,secondary`, `corp.example.com,10.1.1.3,secondary`).

### Step 1 — Configure data collection
Verify zone transfer events:
```spl
index=dns (sourcetype="infoblox:dns" OR sourcetype="infoblox:audit") earliest=-30d
| where query_type="AXFR" OR query_type="IXFR" OR match(_raw, "(?i)(axfr|ixfr|zone.transfer)")
| stats count by query_type, src_ip, domain, response_code
```

### Step 2 — Create the search and alert

**Primary search — Unauthorized zone transfer attempts:**
```spl
index=dns (sourcetype="infoblox:dns" OR sourcetype="infoblox:audit") earliest=-24h
| where query_type="AXFR" OR query_type="IXFR" OR match(_raw, "(?i)(axfr|ixfr)")
| lookup authorized_transfer_peers.csv domain, authorized_ip as src_ip OUTPUT server_role
| eval authorization=if(isnotnull(server_role), "AUTHORIZED", "UNAUTHORIZED")
| eval transfer_type=coalesce(query_type, "AXFR")
| stats count as attempts first(_time) as first_seen latest(_time) as last_seen by src_ip, domain, transfer_type, authorization, response_code
| where authorization="UNAUTHORIZED"
| eval severity=case(response_code="NOERROR", "CRITICAL_SUCCEEDED", attempts > 5, "HIGH", 1==1, "MEDIUM")
| sort severity, -attempts
```

#### Understanding this SPL: The most dangerous finding is `CRITICAL_SUCCEEDED` — an unauthorized IP successfully completed a zone transfer, meaning the attacker now has a complete list of all DNS records in that zone. Even failed attempts (`REFUSED`, `NOTAUTH`) are concerning because they indicate reconnaissance activity. Multiple failed attempts from the same source suggest active scanning.

**Authorized transfer health:**
```spl
index=dns (sourcetype="infoblox:dns" OR sourcetype="infoblox:audit") earliest=-7d
| where query_type="AXFR" OR query_type="IXFR"
| lookup authorized_transfer_peers.csv domain, authorized_ip as src_ip OUTPUT server_role
| where isnotnull(server_role)
| stats count as transfers latest(_time) as last_transfer by src_ip, domain, server_role
| eval hours_since=round((now() - last_transfer)/3600, 1)
| eval health=case(hours_since > 48, "STALE", hours_since > 24, "DELAYED", 1==1, "HEALTHY")
| sort health
```

**Zone transfer source analysis:**
```spl
index=dns (sourcetype="infoblox:dns" OR sourcetype="infoblox:audit") earliest=-30d
| where query_type="AXFR" OR query_type="IXFR"
| stats count as transfers dc(domain) as zones_requested by src_ip
| lookup authorized_transfer_peers.csv authorized_ip as src_ip OUTPUT server_role
| eval status=if(isnotnull(server_role), "Known secondary", "INVESTIGATE")
| sort status, -transfers
```

### Step 3 — Validate
(a) From an authorized secondary server, initiate a zone transfer (`dig @infoblox-primary AXFR corp.example.com`) and verify it appears as "AUTHORIZED" in Splunk.
(b) From an unauthorized IP, attempt a zone transfer and verify it appears as "UNAUTHORIZED" with status REFUSED.
(c) Verify the authorized peers lookup is complete: all secondary DNS servers should be listed.

### Step 4 — Operationalize
Dashboard ("DNS Zone Transfer Audit"):
- Row 1 — Single-value tiles: "Unauthorized attempts (24h)", "Successful unauthorized transfers (CRITICAL)", "Authorized transfers (7d)", "Stale secondaries".
- Row 2 — Unauthorized transfer attempts table: source IP, domain, type, attempts, response code, severity.
- Row 3 — Authorized transfer health: secondary servers, last transfer time, health status.

Alerting:
- Critical (unauthorized zone transfer succeeded — response NOERROR): full zone data exposed — immediate security incident.
- High (> 5 unauthorized zone transfer attempts from same IP): active reconnaissance.
- Warning (authorized secondary hasn't transferred in > 48 hours): zone data may be stale on secondary.

### Step 5 — Troubleshooting

- **No zone transfer events in Splunk** — Infoblox may not log zone transfer queries at the current logging level. Set DNS query logging to include AXFR/IXFR: Grid > DNS > Logging > enable query logging with zone transfer capture.

- **Authorized transfers failing (REFUSED)** — The Infoblox zone transfer ACL may have changed. Verify: Data Management > DNS > Zone > Zone Transfer settings. The secondary server's IP must be in the allow-transfer list.

- **False positive from internal scanning tools** — Vulnerability scanners often test for open zone transfers. Add known scanner IPs to a suppression lookup or the authorized peers list with role "scanner".

## SPL

```spl
index=dns sourcetype="infoblox:dns" earliest=-7d
| eval qtype=upper(coalesce(query_type, record_type, dns_request_record_type))
| where qtype IN ("AXFR","IXFR")
| stats count by src_ip, dns_request, view, host
| sort -count
```

## Visualization

Table (client, zone, count), Map (geo for external sources).

## Known False Positives

Legit secondary transfers and lab AXFR tests can count as attempts; allowlist secondaries and compare to change records.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
