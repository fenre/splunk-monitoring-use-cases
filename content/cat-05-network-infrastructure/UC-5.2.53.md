<!-- AUTO-GENERATED from UC-5.2.53.json — DO NOT EDIT -->

---
id: "5.2.53"
title: "Check Point HTTPS Inspection Status and Bypass (Check Point)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.53 · Check Point HTTPS Inspection Status and Bypass (Check Point)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We look at who is inspected, bypassed, or failing HTTPS checks so you can keep encryption policy honest and still serve legacy apps fairly.*

---

## Description

HTTPS inspection (SSL/TLS decryption) enables deep packet inspection of encrypted traffic. Connections that bypass inspection — due to certificate pinning, bypass rules, or resource limits — create visibility gaps. Monitoring bypass rates ensures that security coverage remains effective and identifies applications or categories that need policy updates.

## Value

Security teams monitor Check Point HTTPS inspection coverage and bypass rates, identifying visibility gaps where encrypted traffic is not inspected and validating bypass policy exceptions.

## Implementation

Enable HTTPS inspection logging (log bypassed and inspected connections). Baseline bypass rate per category. Alert when bypass percentage increases (new cert-pinned apps, resource limits). Report on inspection coverage for compliance (PCI DSS, SOX). Correlate with gateway CPU — high CPU can trigger automatic inspection bypass.

## Detailed Implementation

### Prerequisites
* Check Point HTTPS inspection (SSL/TLS decryption) logs. Data in `index=checkpoint` with `sourcetype=cp_log`. Key fields: `product` (HTTPS Inspection), `action` (Inspect/Bypass), `src`, `dst`, `ssl_inspection_rule`, `bypass_reason`, `server_name`, `ssl_version`, `ssl_cipher`.
* HTTPS Inspection: enables deep packet inspection of encrypted traffic. Check Point terminates the TLS session, inspects content, and re-encrypts to the client with a subordinate CA certificate. Connections bypassing inspection (due to category exception, pinned certificate, or unsupported protocol) create visibility gaps. Configured in SmartConsole > HTTPS Inspection policy.

### Step 1 — - Configure data collection
```
# SmartConsole -- configure HTTPS Inspection
# Security Policies > HTTPS Inspection
# Ensure logging is enabled for both Inspect and Bypass actions
# Manage & Settings > Logs > enable HTTPS Inspection logging

# Install CA certificate on endpoints for inspection to work
```
Verify:
```spl
index=checkpoint sourcetype="cp_log" product="HTTPS Inspection" earliest=-4h
| stats count by action, bypass_reason
```

### Step 2 — - Create the search and alert

**Primary search -- HTTPS inspection status and bypass analysis:**
```spl
index=checkpoint sourcetype="cp_log" earliest=-4h
| where product="HTTPS Inspection" OR match(_raw, "(?i)https.*inspect|ssl.*inspect|tls.*inspect")
| eval act=coalesce(action, ssl_action)
| eval bypass=coalesce(bypass_reason, bypass_category, "N/A")
| eval server=coalesce(server_name, dst, destination_address)
| eval user=coalesce(src_user_name, user, "unknown")
| eval ssl_ver=coalesce(ssl_version, tls_version)
| eval inspected=if(match(act, "(?i)inspect|decrypt"), "INSPECTED", "BYPASSED")
| stats count as connections count(eval(inspected="INSPECTED")) as inspected_count count(eval(inspected="BYPASSED")) as bypassed_count dc(server) as unique_servers by host
| eval inspect_pct=round(100*inspected_count/(inspected_count+bypassed_count), 1)
| eval bypass_pct=round(100*bypassed_count/(inspected_count+bypassed_count), 1)
| eval severity=case(
    bypass_pct > 50, "WARNING -- majority of traffic bypassing inspection (".bypass_pct."%)",
    bypass_pct > 30, "INFO -- significant bypass rate (".bypass_pct."%)",
    1==1, "OK")
| table host, inspected_count, bypassed_count, inspect_pct, bypass_pct, unique_servers, severity
```

**Secondary search -- Bypass reason breakdown:**
```spl
index=checkpoint sourcetype="cp_log" earliest=-4h
| where (product="HTTPS Inspection" OR match(_raw, "(?i)https.*inspect")) AND match(action, "(?i)bypass")
| eval bypass=coalesce(bypass_reason, bypass_category, "Unknown")
| eval server=coalesce(server_name, dst)
| stats count as bypassed dc(server) as unique_servers values(server) as sample_servers by bypass
| sort -bypassed
| eval sample_servers=mvindex(sample_servers, 0, 4)
```

### Step 3 — - Validate
(a) SmartConsole: HTTPS Inspection policy -- verify rules and exceptions.
(b) SmartConsole: Logs & Monitor -- filter product="HTTPS Inspection".
(c) CLI: `fw ctl zdebug + drop` -- check for HTTPS inspection failures.

### Step 4 — - Operationalize
Dashboard ("Check Point -- HTTPS Inspection"):
* Row 1 -- Single-value: "Inspection ratio (%)", "Bypassed connections", "Unique bypass servers".
* Row 2 -- Inspection vs bypass trend.
* Row 3 -- Top bypass reasons.

Alert: Warning (bypass rate > 50%): investigate inspection policy gaps.

### Step 5 — - Troubleshooting

* **High bypass rate** -- Review bypass categories. Common bypasses: certificate-pinned applications (banking, Apple services), health/financial categories (regulatory), or applications that break with inspection (WebRTC, VPN apps). Validate these are intentional.

* **Inspection causing application failures** -- Some applications use certificate pinning and break when intercepted. Add to HTTPS bypass rule. Check: "Update Services" category bypass for OS/software updates.

* **Client certificate errors** -- CA certificate not trusted on endpoints. Deploy the inspection CA certificate via GPO, MDM, or manual installation. Check certificate chain validity.

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(product),"(?i)https.?inspection|ssl.?inspection") OR match(lower(logdesc),"(?i)bypass|inspect|decrypt")
| eval inspected=if(match(lower(logdesc),"(?i)inspect|decrypt") AND NOT match(lower(logdesc),"(?i)bypass|skip|fail"),1,0)
| stats count sum(inspected) as inspected_count by rule_name, category
| eval bypass_pct=round(100*(count-inspected_count)/count,1)
| where bypass_pct > 20
| sort -bypass_pct
```

## Visualization

Pie chart (inspected vs bypassed), Bar chart (bypass by category), Line chart (bypass rate trend), Table (top bypass rules).

## Known False Positives

Legacy clients, pinned apps, and certificate work can make inspection status messages look worse than the risk.

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
