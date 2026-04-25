<!-- AUTO-GENERATED from UC-5.3.25.json — DO NOT EDIT -->

---
id: "5.3.25"
title: "Citrix ADC Bot Management Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.25 · Citrix ADC Bot Management Detection

## Description

Citrix ADC Bot Management classifies clients (good automation, bad bots, unknown) and can enforce CAPTCHA, allow, or deny. Tracking category mix and enforcement rates surfaces credential stuffing, scraping, and misclassified good bots. A rising bad or unknown share, or high CAPTCHA rates, can indicate attack campaigns or policy tuning needs before user experience or origin load suffers.

## Value

Citrix ADC Bot Management classifies clients (good automation, bad bots, unknown) and can enforce CAPTCHA, allow, or deny. Tracking category mix and enforcement rates surfaces credential stuffing, scraping, and misclassified good bots. A rising bad or unknown share, or high CAPTCHA rates, can indicate attack campaigns or policy tuning needs before user experience or origin load suffers.

## Implementation

Enable bot signatures and logging to appflow and/or syslog. Ensure HTTP headers or log fields that carry bot decision and action are extracted. Index to `index=netscaler`. Build baselines for allow versus challenge versus block per major application. Alert on bad-bot surges, spikes in unknown classification, or CAPTCHA rate jumps that exceed normal human traffic patterns.

## Detailed Implementation

Prerequisites
• Bot Management licensed and configured; logging enabled.
• Data in `index=netscaler` with `citrix:netscaler:appflow` and/or syslog lines containing decisions.
• Optional: geo and ASN enrichment via separate lookup.

Step 1 — Configure data collection
Send AppFlow and security-related syslog to Splunk. Map vendor fields to `bot_class` and `action` where the add-on provides CIM-style fields; otherwise refine the `eval` in SPL after sampling `_raw`.

Step 2 — Create the search and alert
Run the search; alert on thresholds tuned per site (for example, bad bot count > N per 15 minutes, or unknown share doubling week over week). Add allowlists for monitoring services.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Intrusion_Detection data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Intrusion_Detection model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Pair alerts with your web fraud or identity team. Document how to add exceptions for partner automation without turning off protection.

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

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
- [Citrix ADC — Bot management](https://docs.citrix.com/en-us/citrix-adc/current-release/bot-management.html)
