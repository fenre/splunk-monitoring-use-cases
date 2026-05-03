<!-- AUTO-GENERATED from UC-5.3.25.json — DO NOT EDIT -->

---
id: "5.3.25"
title: "Citrix ADC Bot Management Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.25 · Citrix ADC Bot Management Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security

*We look at bot and automation detections in one place so good crawlers you forgot to list do not drown out new risky behavior.*

---

## Description

Citrix ADC Bot Management classifies clients (good automation, bad bots, unknown) and can enforce CAPTCHA, allow, or deny. Tracking category mix and enforcement rates surfaces credential stuffing, scraping, and misclassified good bots. A rising bad or unknown share, or high CAPTCHA rates, can indicate attack campaigns or policy tuning needs before user experience or origin load suffers.

## Value

Security teams monitor Citrix ADC bot detection classifying traffic as good/bad/unknown bots, identifying unblocked malicious bots and misconfigured policies blocking legitimate crawlers.

## Implementation

Enable bot signatures and logging to appflow and/or syslog. Ensure HTTP headers or log fields that carry bot decision and action are extracted. Index to `index=netscaler`. Build baselines for allow versus challenge versus block per major application. Alert on bad-bot surges, spikes in unknown classification, or CAPTCHA rate jumps that exceed normal human traffic patterns.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC Bot Management logs. Key fields: `bot_type` (good/bad/unknown), `bot_category`, `action` (allow/block/captcha/rate-limit), `source_ip`, `user_agent`, `url`, `tps`.
* Citrix ADC Bot Management detects: (1) known good bots (Google, Bing crawlers), (2) known bad bots (scrapers, vulnerability scanners), (3) unknown bots (behavioral analysis), (4) CAPTCHA challengers, (5) device fingerprinting.

### Step 1 — - Configure data collection
Verify bot management data:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:appfw") ("bot" OR "BOT" OR "captcha" OR "fingerprint" OR "rate.limit") earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Bot detection analysis:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:appfw") ("bot" OR "BOT" OR "captcha" OR "fingerprint") earliest=-4h
| eval bot_class=coalesce(bot_type, bot_category, if(match(_raw, "(?i)good.bot"), "GOOD", if(match(_raw, "(?i)bad.bot|malicious"), "BAD", "UNKNOWN")))
| eval act=coalesce(action, enforcement_action)
| eval src=coalesce(source_ip, client_ip)
| eval ua=coalesce(user_agent, http_user_agent)
| stats count as detections dc(src) as unique_sources values(url) as target_urls by bot_class, act
| eval concern=case(bot_class="BAD" AND act!="block", "RISK -- bad bot not blocked", bot_class="UNKNOWN" AND detections > 100, "INVESTIGATE -- high unknown bot activity", bot_class="GOOD" AND act="block", "CONFIG -- good bot being blocked", 1==1, "OK")
| where concern != "OK"
| sort concern
```

### Step 3 — - Validate
(a) Use curl with a known bot user-agent: `curl -H "User-Agent: Googlebot" https://app/` -- verify it's classified as "GOOD".
(b) Use a vulnerability scanner user-agent and verify it's classified as "BAD".
(c) On ADC CLI: `show bot profile <profile> -stat` -- compare detection counts.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Bot Management"):
* Row 1 -- Single-value: "Good bots", "Bad bots", "Unknown bots", "Blocked".
* Row 2 -- Bot classification with action and concerns.

Alerting:
* Warning (bad bots not being blocked): bot profile may be in detect-only mode.
* Info (high unknown bot activity): review and classify.

### Step 5 — - Troubleshooting

* **Good bot blocked** -- Check bot allow-list: `show bot profile <profile> -goodbot`. Add the bot's user-agent or IP range to the allow-list.

* **Bad bot not blocked** -- Profile may be in "detect" mode. Change to "mitigate": `set bot profile <profile> -trap ON -trapurl /bot_trap`.

* **High "unknown" bot count** -- These need classification. Check behavioral analysis settings and device fingerprinting configuration.

## SPL

```spl
index=netscaler (sourcetype="citrix:netscaler:appflow" OR sourcetype="citrix:netscaler:syslog") ("bot" OR "BOT" OR captcha OR "reputation")
| eval bot_class=if(match(_raw, "(?i)good"),"good", if(match(_raw, "(?i)bad|malici"),"bad", if(match(_raw, "(?i)unknown|unclass"),"unknown","other")))
| eval action=if(match(_raw, "(?i)deny|block"),"deny", if(match(_raw, "(?i)captcha"),"captcha", if(match(_raw, "(?i)allow|pass"),"allow","other")))
| bin _time span=15m
| stats count as reqs, sum(eval(action="captcha")) as captcha_hits, sum(eval(action="deny")) as deny_hits, sum(eval(action="allow")) as allow_hits by _time, host, bot_class
| eval bot_to_human_ratio=if(allow_hits+deny_hits>0, round((deny_hits+captcha_hits)/(allow_hits+deny_hits+captcha_hits+0.001)*100,1), 0)
| where bot_class IN ("bad","unknown") OR bot_to_human_ratio > 25
| table _time, host, bot_class, reqs, allow_hits, captcha_hits, deny_hits, bot_to_human_ratio
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

## Visualization

Area chart of requests by bot class, pie chart of enforcement actions, table of ratio of challenged or denied to total session starts.

## Known False Positives

Good crawlers, marketing tools, and headless health checks can read as bots until you label known partners.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
- [Citrix ADC — Bot management](https://docs.citrix.com/en-us/citrix-adc/current-release/bot-management.html)
