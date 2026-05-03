<!-- AUTO-GENERATED from UC-5.2.9.json — DO NOT EDIT -->

---
id: "5.2.9"
title: "URL Filtering Blocks"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.9 · URL Filtering Blocks

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We see which web categories and pages get stopped most so policy stays fair, current, and aligned with what the business really needs.*

---

## Description

Shows what categories users are trying to access. Reveals policy effectiveness and shadow IT.

## Value

Security teams analyze URL filtering blocks by risk category, prioritizing malware/phishing/C2 blocks that indicate compromised users over routine policy violations.

## Implementation

Forward URL filtering logs. Dashboard showing blocks by category and user.

## Detailed Implementation

### Prerequisites
* Firewall URL filtering logs. Palo Alto: `sourcetype=pan:url`, Fortinet: `sourcetype=fgt_utm` with type=webfilter, Cisco FTD: URL filtering events. Key fields: `url`, `url_category`, `action` (block/alert/allow), `user`, `src_ip`.
* URL filtering engines classify URLs into categories (malware, phishing, adult, social-media, gambling, etc.) and enforce policy (block/alert/allow per category).

### Step 1 — - Configure data collection
**Palo Alto:**
```
# Objects > Security Profiles > URL Filtering > set categories to block/alert
# Attach URL Filtering profile to security policies
# Device > Log Settings > URL > forward via syslog
```
Verify:
```spl
index=firewall (sourcetype="pan:url" OR (sourcetype="fgt_utm" type="webfilter")) earliest=-4h
| where action="blocked" OR action="block" OR action="deny"
| stats count by url_category
| sort -count
```

### Step 2 — - Create the search and alert

**Primary search -- URL filtering block analysis:**
```spl
index=firewall (sourcetype="pan:url" OR (sourcetype="fgt_utm" type="webfilter") OR sourcetype="cisco:firepower:syslog") earliest=-4h
| where match(action, "(?i)block|deny|drop")
| eval category=coalesce(url_category, category, web_category)
| eval usr=coalesce(user, src_user, srcuser)
| eval src=coalesce(src_ip, src, srcaddr)
| eval risk_category=case(match(category, "(?i)malware|phishing|command-and-control|c2|malicious"), "HIGH_RISK", match(category, "(?i)hacking|proxy-avoidance|questionable|suspicious"), "MEDIUM_RISK", match(category, "(?i)adult|gambling|drugs"), "POLICY_VIOLATION", 1==1, "LOW_RISK")
| stats count as blocks dc(url) as unique_urls dc(src) as unique_users values(category) as categories by risk_category
| eval severity=case(risk_category="HIGH_RISK" AND blocks > 10, "CRITICAL -- malware/phishing/C2 blocks", risk_category="MEDIUM_RISK" AND blocks > 50, "WARNING -- evasion attempts", 1==1, "INFO")
| sort severity, -blocks
```

**Users with high-risk URL blocks:**
```spl
index=firewall (sourcetype="pan:url" OR sourcetype="fgt_utm") action="blocked" earliest=-4h
| eval category=coalesce(url_category, category)
| where match(category, "(?i)malware|phishing|command-and-control")
| eval usr=coalesce(user, src_user, srcuser)
| eval src=coalesce(src_ip, src)
| stats count as malicious_blocks dc(url) as unique_malicious_urls values(category) as categories by usr, src
| sort -malicious_blocks
```

### Step 3 — - Validate
(a) Test with a known blocked category URL and verify the block event appears.
(b) Palo Alto: Monitor > Logs > URL Filtering -- compare with Splunk.
(c) Verify category accuracy by checking a sample of blocked URLs against the vendor's URL lookup.

### Step 4 — - Operationalize
Dashboard ("Firewall -- URL Filtering"):
* Row 1 -- Single-value: "Malware/phishing blocks", "Policy violations", "Total blocks", "Unique blocked URLs".
* Row 2 -- Block distribution by risk category.
* Row 3 -- Users with malware/phishing blocks.

Alerting:
* Critical (malware/phishing/C2 blocks for specific user): potential compromise.
* Warning (proxy avoidance blocks): user attempting to bypass security controls.

### Step 5 — - Troubleshooting

* **Legitimate site blocked** -- URL may be miscategorized. Submit recategorization request to vendor (Palo Alto PAN-DB, Fortinet FortiGuard). Add temporary URL exception if business-critical.

* **High malware blocks from single user** -- User may have visited a compromised site or have malware. Investigate: (1) endpoint AV/EDR status, (2) recent downloads, (3) check if blocks were for the same domain or diverse.

* **URL filtering not blocking** -- Check: (1) URL Filtering profile is attached to the correct policy, (2) policy matches the traffic (zone, source, destination), (3) HTTPS decryption is enabled (without it, only the domain is visible, not the full URL).

## SPL

```spl
index=firewall sourcetype="pan:url" action="block-url"
| stats count by url_category, src | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Bar chart (by category), Table, Pie chart.

## Known False Positives

New sites, rewrites, and overly broad category blocks can create noisy URL blocks for benign traffic.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
