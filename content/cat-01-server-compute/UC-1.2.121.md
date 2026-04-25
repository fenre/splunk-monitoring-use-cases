<!-- AUTO-GENERATED from UC-1.2.121.json — DO NOT EDIT -->

---
id: "1.2.121"
title: "DNS Client Query Anomalies"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.121 · DNS Client Query Anomalies

## Description

Monitoring DNS queries from Windows clients reveals C2 beacons, DNS tunneling, and DGA-based malware communicating with attacker infrastructure.

## Value

Client-side DNS oddities—one host asking for many random names—can be C2, tunnels, or noisy software. Per-client baselines turn a firehose into actionable outliers.

## Implementation

Sysmon EventCode 22 logs DNS queries with the originating process. Detect DNS tunneling via long domain names (>50 chars), high label counts, and high-entropy subdomains. Identify DGA patterns: many unique NXDomain responses from a single process. Alert on processes making unusual DNS query volumes. Baseline per-process DNS behavior and alert on deviations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 22), `sourcetype=WinEventLog:Microsoft-Windows-DNS-Client/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sysmon EventCode 22 logs DNS queries with the originating process. Detect DNS tunneling via long domain names (>50 chars), high label counts, and high-entropy subdomains. Identify DGA patterns: many unique NXDomain responses from a single process. Alert on processes making unusual DNS query volumes. Baseline per-process DNS behavior and alert on deviations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=22
| eval domain=lower(QueryName)
| eval domain_len=len(domain)
| eval label_count=mvcount(split(domain, "."))
| where domain_len>50 OR label_count>5
| stats count dc(QueryName) as UniqueDomains by host, Image
| where UniqueDomains>100 OR count>500
| sort -UniqueDomains
```

Understanding this SPL

**DNS Client Query Anomalies** — Monitoring DNS queries from Windows clients reveals C2 beacons, DNS tunneling, and DGA-based malware communicating with attacker infrastructure.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 22), `sourcetype=WinEventLog:Microsoft-Windows-DNS-Client/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **domain** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **domain_len** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **label_count** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where domain_len>50 OR label_count>5` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, Image** so each row reflects one combination of those dimensions.
• Filters the current rows with `where UniqueDomains>100 OR count>500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (query volume by process), Table (anomalous queries), Alert on tunneling indicators.

## SPL

```spl
index=wineventlog EventCode=22
| eval domain=lower(QueryName)
| eval domain_len=len(domain)
| eval label_count=mvcount(split(domain, "."))
| where domain_len>50 OR label_count>5
| stats count dc(QueryName) as UniqueDomains by host, Image
| where UniqueDomains>100 OR count>500
| sort -UniqueDomains
```

## CIM SPL

```spl
| tstats `summariesonly` dc(DNS.query) as n
  from datamodel=Network_Resolution where nodename=Network_Resolution.DNS
  by DNS.client_host span=1h
| where n > 200
```

## Visualization

Timechart (query volume by process), Table (anomalous queries), Alert on tunneling indicators.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
