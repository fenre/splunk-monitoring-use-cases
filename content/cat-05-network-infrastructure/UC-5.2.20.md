<!-- AUTO-GENERATED from UC-5.2.20.json — DO NOT EDIT -->

---
id: "5.2.20"
title: "Content Filtering and URL Category Blocks (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.20 · Content Filtering and URL Category Blocks (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We show which web categories and pages get stopped at the network edge so policy stays in step with what people really need to do their jobs.*

---

## Description

Tracks blocked URLs and categories to monitor policy compliance and identify misclassified content.

## Value

Security teams analyze Meraki MX content filtering blocks by risk category, prioritizing malware/phishing blocks and proxy evasion attempts over routine policy enforcement.

## Implementation

Ingest URL filtering events from MX syslog. Categorize by policy.

## Detailed Implementation

### Prerequisites
* Meraki MX content filtering logs via syslog or API. Data in `index=meraki` with `sourcetype=meraki:events` (syslog) or `sourcetype=meraki:api:contentfiltering`. Key fields: `url`, `category`, `action` (block/allow), `client_mac`, `client_ip`.
* Meraki content filtering: MX appliances categorize web traffic and enforce per-category allow/block policies. Categories include: adult content, social networking, streaming media, gambling, etc. URL categories are provided by Meraki's cloud-based classification service.

### Step 1 — - Configure data collection
Syslog configuration:
```
# Dashboard > Network-wide > General > Syslog servers
# Roles: URLs
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)content_filter|url.*block|category.*block|web.*filter")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Content filtering and URL category blocks:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:contentfiltering") earliest=-4h
| where match(_raw, "(?i)content.filter.*block|url.*block|category.*deny|web.*filter.*block")
| eval category=coalesce(category, url_category)
| eval url=coalesce(url, request_url, dest_url)
| eval client=coalesce(client_ip, src_ip, src)
| eval risk=case(match(category, "(?i)malware|phishing|botnet|command"), "HIGH_RISK", match(category, "(?i)proxy|anonymizer|vpn|tor"), "EVASION", match(category, "(?i)adult|gambling|drugs"), "POLICY", 1==1, "STANDARD")
| stats count as blocks dc(url) as unique_urls dc(client) as affected_clients by category, risk
| eval severity=case(risk="HIGH_RISK", "CRITICAL -- security threat category blocked", risk="EVASION", "HIGH -- proxy/anonymizer evasion attempt", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -blocks
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Content filtering -- check blocked categories and rules.
(b) Visit a known blocked category URL through the MX and verify the block event appears.
(c) Compare block counts with Dashboard content filtering reports.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Content Filtering"):
* Row 1 -- Single-value: "Malware/phishing blocks", "Evasion blocks", "Policy blocks".
* Row 2 -- Blocks by category.
* Row 3 -- Top blocked clients.

Alerting:
* Critical (malware/phishing blocks from specific client): investigate for compromise.
* High (proxy/anonymizer evasion from client): policy violation attempt.

### Step 5 — - Troubleshooting

* **Legitimate site blocked** -- Submit URL recategorization via Meraki Dashboard or Webroot BrightCloud lookup. Add temporary URL whitelist if business-critical.

* **Content filtering not blocking** -- Check: (1) content filtering policy is applied to the network, (2) HTTPS inspection is enabled (SSL/TLS decryption in MX), (3) client is routing through MX.

* **High blocks from single client** -- May indicate: malware on the device, unauthorized browsing, or misconfigured application. Investigate the client device.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| stats count as block_count by url_category, src
| sort - block_count
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Table of top blocked categories; bar chart by category; user detail table.

## Known False Positives

Overly strict categories, new SaaS, and one-off page visits can make URL blocks look worse than a policy problem.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
