<!-- AUTO-GENERATED from UC-5.2.39.json — DO NOT EDIT -->

---
id: "5.2.39"
title: "Data Loss Prevention (DLP) Event Analysis (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.39 · Data Loss Prevention (DLP) Event Analysis (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We count data loss style events on the same edge so risky uploads to personal storage and odd data paths get a second look in time.*

---

## Description

Detects and alerts on sensitive data transmission to prevent data exfiltration.

## Value

Security teams monitor Meraki MX content filtering blocks as DLP proxy indicators, detecting potential data exfiltration attempts to file sharing, cloud storage, and high-risk upload destinations.

## Implementation

Enable DLP on MX appliance. Ingest DLP match events.

## Detailed Implementation

### Prerequisites
* Meraki MX content filtering and DLP event data. Data in `index=meraki` with `sourcetype=meraki:events`. Key fields: `category`, `url`, `src`, `action` (block/allow), `content_type`.
* Meraki MX content filtering: Dashboard > Security & SD-WAN > Content filtering. Categories include file sharing, adult content, malware. URL filtering via blocked/allowed lists. AMP (Advanced Malware Protection) provides file reputation scanning.
* Note: Meraki MX does not have full enterprise DLP (like Symantec/Forcepoint). This UC focuses on content filtering events that serve as DLP proxy indicators -- blocking uploads to cloud storage, file sharing sites, and detecting sensitive document transfers.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Security & SD-WAN > Content filtering
# Block categories: File sharing, Peer-to-peer, Cloud storage (for DLP)
# URL filtering: block known data exfiltration endpoints
# AMP: enable for malware and file reputation
# Syslog: enable Events, URLs
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)content.*filter|url.*block|amp|file.*block|category.*block")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Content filtering and potential data exfiltration:**
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)block|deny|content.*filter|url.*filter|amp")
| eval src=coalesce(src, src_ip)
| eval url=coalesce(url, dest_url, requested_url)
| eval category=coalesce(category, url_category, content_category)
| eval action=coalesce(action, disposition)
| lookup meraki_networks.csv serial OUTPUT network_name
| eval dlp_risk=case(
    match(category, "(?i)file.?shar|cloud.?stor|p2p|torrent"), "HIGH -- file sharing/cloud storage",
    match(category, "(?i)webmail|personal.?email"), "MEDIUM -- personal email/webmail",
    match(url, "(?i)pastebin|dropbox|mega\.nz|wetransfer|sendspace"), "HIGH -- data exfiltration target",
    match(category, "(?i)malware|phishing|botnet"), "CRITICAL -- malware/C2",
    1==1, "LOW")
| where dlp_risk != "LOW"
| stats count as blocks dc(url) as unique_urls values(category) as categories by src, dlp_risk, network_name
| sort dlp_risk, -blocks
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Content filtering -- verify blocked categories.
(b) Test: attempt to access a blocked category site and verify block event appears.
(c) Cross-reference with AMP file disposition events.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Content Filtering & DLP"):
* Row 1 -- Single-value: "High-risk blocks (24h)", "Unique users blocked", "Categories triggered".
* Row 2 -- DLP risk event table by user and category.
* Row 3 -- Blocked URL category distribution.

Alert: Critical (user accessing multiple high-risk exfiltration targets): SOC investigation.

### Step 5 — - Troubleshooting

* **Legitimate cloud storage blocked** -- Whitelist approved cloud storage domains (e.g., corporate OneDrive, approved Google Workspace). Use URL allow-lists.

* **Content filtering not blocking** -- Verify HTTPS inspection is enabled. Without SSL decryption, Meraki can only filter based on SNI/domain, not full URL or content.

* **AMP not scanning files** -- Verify AMP is enabled in Dashboard. Check that file types are not excluded from scanning.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DLP*"
| stats count as dlp_match_count by src, dest, dlp_policy, data_type
| where dlp_match_count > 0
| sort - dlp_match_count
```

## Visualization

DLP incident timeline; data type breakdown; source/destination detail.

## Known False Positives

False positives, large legitimate uploads, and user mistakes can all trip data-loss rules you still need to review.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
