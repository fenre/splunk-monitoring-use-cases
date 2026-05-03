<!-- AUTO-GENERATED from UC-5.3.24.json — DO NOT EDIT -->

---
id: "5.3.24"
title: "Citrix ADC Web Application Firewall (WAF) Violations"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.3.24 · Citrix ADC Web Application Firewall (WAF) Violations

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security

*We count web application firewall style blocks on the same path so a noisy rule, a test, and a real attack are easier to separate.*

---

## Description

Citrix ADC Web Application Firewall inspects HTTP traffic for common attacks (SQL injection, cross-site scripting, JSON/XML threats) and policy violations. Spikes in violations, or critical signatures firing in enforcement mode, indicate active attacks or misconfigured applications. Distinguishing learning mode noise from enforcement blocks, and monitoring geographic blocks, keeps incident response focused and reduces false positives.

## Value

Security teams analyze Citrix ADC Application Firewall violations by attack category (SQLi, XSS, buffer overflow, data leak), identifying unblocked critical violations and targeted attacks.

## Implementation

Send WAF log profile output to syslog and index as `citrix:netscaler:syslog`. Parse violation type, action (block, learn, log), and policy. Build correlation searches for attack categories (SQL, XSS, JSON injection) and for geo-IP block actions if logged. Tune thresholds by application: public APIs may legitimately spike; internal apps should not. Use lookups for known scanner IPs and pen-test windows.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC Application Firewall (AppFW/WAF) logs in `index=netscaler` with `sourcetype=citrix:netscaler:syslog` or `sourcetype=citrix:netscaler:appfw`. Key fields: `appfw_violation`, `severity`, `source_ip`, `url`, `action` (block/log/transform), `signature_id`, `violation_category`.
* Citrix ADC AppFW protections: SQL injection, XSS, buffer overflow, cookie tampering, form field consistency, credit card/SSN protection, XML DoS, JSON DoS, signature-based detection.

### Step 1 — - Configure data collection
Enable AppFW logging:
```
set appfw settings -logEveryPolicyHit ON
add audit syslogAction appfw_log <splunk_ip> -logLevel ALL
set appfw profile <profile> -logEveryPolicyHit ON
```
Verify:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:appfw") ("APPFW" OR "AppFirewall" OR "violation") earliest=-4h
| stats count by appfw_violation, action
```

### Step 2 — - Create the search and alert

**Primary search -- WAF violation analysis:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:appfw") ("APPFW" OR "AppFirewall" OR "violation" OR "appfw_") earliest=-4h
| eval violation=coalesce(appfw_violation, violation_type, violation_category)
| eval act=coalesce(action, enforcement_action)
| eval src=coalesce(source_ip, client_ip)
| eval attack_class=case(match(violation, "(?i)sql"), "SQL_INJECTION", match(violation, "(?i)xss|cross.site"), "XSS", match(violation, "(?i)buffer|overflow"), "BUFFER_OVERFLOW", match(violation, "(?i)cookie"), "COOKIE_TAMPERING", match(violation, "(?i)field|form"), "FORM_MANIPULATION", match(violation, "(?i)credit.card|ssn"), "DATA_LEAK", match(violation, "(?i)signature"), "SIGNATURE_MATCH", 1==1, "OTHER")
| stats count as violations dc(src) as unique_sources values(url) as target_urls by attack_class, act, severity
| eval risk=case(act!="block" AND severity="CRITICAL", "HIGH RISK -- critical violation NOT blocked", act="block" AND violations > 100, "ACTIVE DEFENSE -- blocking attack", violations > 50, "ELEVATED -- high violation volume", 1==1, "INFO")
| sort risk, -violations
```

### Step 3 — - Validate
(a) Send a test SQLi payload and verify the violation appears (e.g., `curl "https://app/?id=1 OR 1=1"`).
(b) On ADC CLI: `stat appfw profile <profile>` -- compare violation counts.
(c) Verify blocking vs logging mode: `show appfw profile <profile>` for each protection.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- WAF"):
* Row 1 -- Single-value: "Total violations", "Blocked", "Logged only", "Critical unblocked".
* Row 2 -- Attack classification with action and risk.
* Row 3 -- Top attacking IPs.

Alerting:
* Critical (critical violation NOT blocked): WAF in learn/log mode -- review.
* High (> 100 violations from single IP in 15 min): targeted attack.

### Step 5 — - Troubleshooting

* **False positives** -- AppFW may flag legitimate requests. Check the learning engine: `show appfw learningdata <profile>`. Accept legitimate patterns to reduce false positives.

* **Violations logged but not blocked** -- Profile is in "log" mode. To block: `set appfw profile <profile> -SQLInjectionAction block log stats`.

* **Signature-based violations** -- Update signatures: `update appfw signatures`. Signatures are separate from the AppFW profile.

## SPL

```spl
index=netscaler sourcetype="citrix:netscaler:syslog" (WAF OR "Application Firewall" OR APPFW)
| rex field=_raw "(?i)(?<violation>SQL|XSS|JSON|XML|CSRF|OWASP)"
| eval is_learning=if(match(_raw, "(?i)learning"), 1, 0)
| where NOT (is_learning=1 AND match(_raw, "(?i)info"))
| bin _time span=15m
| stats count as hits, values(violation) as violation_types, dc(url) as unique_urls, latest(host) as adc by policy_name, _time
| where hits > 0
| sort - hits
| table _time, adc, policy_name, violation_types, unique_urls, hits
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

Stacked column chart of violations by type over time, treemap of policies, drilldown to sample URLs (sanitized).

## Known False Positives

Tuning, pen tests, and browser oddities can make web firewall logs noisy; partner with the app team on false rules.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
- [Citrix ADC — Web App Firewall](https://docs.citrix.com/en-us/citrix-adc/current-release/application-firewall.html)
