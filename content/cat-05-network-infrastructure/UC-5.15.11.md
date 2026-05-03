<!-- AUTO-GENERATED from UC-5.15.11.json — DO NOT EDIT -->

---
id: "5.15.11"
title: "Infoblox Administrative Audit Trail for DNS Zone and Grid Changes (Infoblox)"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.15.11 · Infoblox Administrative Audit Trail for DNS Zone and Grid Changes (Infoblox)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Platform &middot; **Type:** Audit, Compliance, Governance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep a readable diary of who changed important internet phonebook settings inside Infoblox so nobody can quietly break critical names without leaving fingerprints.*

---

## Description

Curated audit discovery surfaces privileged Infoblox UI/API changes impacting authoritative zones, RPZ policies, or Grid-wide settings with actor attribution derived from syslog tokens.

## Value

Change governance teams prove who altered DNS or DHCP objects during audits, accelerate rollback after unauthorized edits, and satisfy regulators needing authoritative evidence beyond Splunk operator logs alone.

## Implementation

Forward audit severity informational+, normalize actor regex per locale, schedule saved searches segregating destructive verbs (`delete`, `remove`), ship summaries to SIEM retention index with immutability controls.

## Detailed Implementation

### Prerequisites
- Role-based access mapping Splunk analysts vs DNS admins to enforce least privilege viewing.
- Time synchronization per UC‑5.15.3 guidance.
- Runbook linking Splunk events to Infoblox revision history screenshots.

### Step 1 — Configure data collection
Enable auditing categories for admin actions on Grid Master; optionally aggregate passive replicas—avoid duplicates using `dedup _raw` heuristics.

### Step 2 — Create the search and alert
Primary SPL enumerates actors; add alerting subsearch for destructive combinations (`delete` AND `zone`). Throttle known automation service accounts via lookup `infoblox_svc_accounts.csv`.

### Step 3 — Validate
Perform benign TXT record change under controlled account; confirm Splunk captures actor and object tokens matching GUI audit export CSV.

### Step 4 — Operationalize
Weekly digest email to CAB, Splunk Dashboard Studio with textual timeline, integration with ticketing via webhook alert action.

### Step 5 — Troubleshooting
**Null actor:** falls back to syslog `user` field—extend props.conf extraction.**High noise:** filter routine heartbeat audits.**Multiline messages:** adjust LINE_BREAKER on HF if Infoblox splits entries.

## SPL

```spl
index=netops sourcetype="infoblox:audit" earliest=-24h
| search (admin OR administrator OR user OR login OR modify OR delete OR add OR zone OR record OR grid OR rpz OR permission)
| rex field=_raw "(?i)(?:user|admin|login)[\\s:=]+(?<admin_actor>[^\\s,;]+)"
| rex field=_raw "(?i)(?:object|zone|fqdn|name)[\\s:=]+(?<object_name>[^\\s,;]+)"
| stats count latest(_time) as last_action values(object_name) as objects by admin_actor host
| sort - count
| head 200
```

## CIM SPL

```spl
| tstats count where index=netops sourcetype=infoblox:audit by host span=1h
```

## Visualization

Timeline of actions by admin_actor, stacked counts by verb category (add/modify/delete), detail table with object_name.

## Known False Positives

**Automation accounts:** Nightly sync jobs resemble suspicious bursts—allowlist with lookup.**Benign mass imports:** Large CSV imports spike counts legitimately during migrations.**Keyword bleed:** Words like "zone" in unrelated messages—tighten token proximity rules.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
