<!-- AUTO-GENERATED from UC-5.2.5.json — DO NOT EDIT -->

---
id: "5.2.5"
title: "High-Risk Port Exposure"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.5 · High-Risk Port Exposure

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We look for allowed traffic to risky services so we can find exposed remote desktop, sharing, and old protocols before attackers do.*

---

## Description

Allowed traffic to RDP/SMB/Telnet from untrusted zones indicates policy gaps.

## Value

Security teams identify firewall rules allowing traffic to high-risk ports (RDP, SMB, SSH, databases), flagging unapproved external exposure and insecure protocols like Telnet.

## Implementation

Monitor allow rules for external traffic to high-risk ports. Alert on any matches. Review and tighten rules.

## Detailed Implementation

### Prerequisites
* Firewall traffic logs in `index=firewall` with sourcetypes per vendor. Key fields: `dest_port`, `action=allowed`, `dest_ip`, `app`, `rule`. High-risk ports: 22 (SSH), 23 (Telnet), 445 (SMB), 3389 (RDP), 1433 (MSSQL), 3306 (MySQL), 5432 (PostgreSQL), 5900 (VNC), 8080 (HTTP-alt).
* Create `approved_services.csv` lookup: `dest_port`, `service_name`, `approved_sources`, `business_justification`, `expiry_date`.

### Step 1 — - Configure data collection
Verify allowed traffic to high-risk ports:
```spl
index=firewall (action=allowed OR action=allow OR action=pass) earliest=-4h
| eval dport=tonumber(coalesce(dest_port, dstport))
| where dport IN (22, 23, 445, 3389, 1433, 3306, 5432, 5900, 8080)
| stats count by dport, host
```

### Step 2 — - Create the search and alert

**Primary search -- High-risk port exposure analysis:**
```spl
index=firewall (action=allowed OR action=allow OR action=pass) earliest=-4h
| eval src=coalesce(src_ip, src, srcaddr)
| eval dst=coalesce(dest_ip, dest, dstaddr)
| eval dport=tonumber(coalesce(dest_port, dstport))
| eval service=case(dport=22, "SSH", dport=23, "TELNET", dport=445, "SMB", dport=3389, "RDP", dport=1433, "MSSQL", dport=3306, "MySQL", dport=5432, "PostgreSQL", dport=5900, "VNC", dport=8080, "HTTP-alt", 1==1, "Port-".dport)
| where dport IN (22, 23, 445, 3389, 1433, 3306, 5432, 5900, 8080)
| lookup approved_services.csv dest_port AS dport OUTPUT approved_sources, business_justification, expiry_date
| eval is_approved=if(isnotnull(approved_sources), "APPROVED", "UNAPPROVED")
| eval from_external=if(NOT match(src, "^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)"), 1, 0)
| stats count as connections dc(src) as unique_sources dc(dst) as unique_targets sum(from_external) as external_connections by service, dport, is_approved
| eval severity=case(service="TELNET", "CRITICAL -- Telnet should never be allowed", is_approved="UNAPPROVED" AND external_connections > 0, "CRITICAL -- unapproved external access to ".service, is_approved="UNAPPROVED" AND connections > 100, "HIGH -- unapproved high-risk port exposure", 1==1, "WARNING")
| sort severity, -connections
```

### Step 3 — - Validate
(a) Cross-reference with firewall rule audit: identify rules allowing high-risk ports.
(b) Verify `approved_services.csv` is current and expired approvals are flagged.
(c) Run external port scan (nmap) against perimeter to confirm exposed services match firewall view.

### Step 4 — - Operationalize
Dashboard ("Firewall -- High-Risk Port Exposure"):
* Row 1 -- Single-value: "Unapproved services", "External connections to high-risk ports", "Telnet connections".
* Row 2 -- High-risk port exposure table.

Alerting:
* Critical (Telnet allowed anywhere): insecure protocol.
* Critical (unapproved external access to DB/RDP/SSH): potential attack vector.

### Step 5 — - Troubleshooting

* **Legitimate service flagged as unapproved** -- Update `approved_services.csv` with business justification and expiry date. Require periodic re-approval.

* **High-risk port allowed from external** -- Firewall rule may be overly permissive. Review: (1) source restriction (specific IPs vs any), (2) time-based access, (3) consider VPN requirement for remote access.

* **SMB (445) allowed between zones** -- Unless specifically required for file sharing, SMB should be blocked between security zones. Known vector for lateral movement (WannaCry, NotPetya).

## SPL

```spl
index=firewall action="allowed" (dest_port=3389 OR dest_port=445 OR dest_port=23)
| where NOT cidrmatch("10.0.0.0/8", src)
| stats count by src, dest, dest_port | sort -count
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

Table (source, dest, port), Bar chart by port, Map.

## Known False Positives

Jump boxes, admin jump hosts, and legacy apps may legitimately use high-risk ports; match to asset inventory before reacting.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
