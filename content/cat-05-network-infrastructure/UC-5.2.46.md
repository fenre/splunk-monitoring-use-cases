<!-- AUTO-GENERATED from UC-5.2.46.json — DO NOT EDIT -->

---
id: "5.2.46"
title: "FortiGate Web Filter and Application Control Events (Fortinet)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.46 · FortiGate Web Filter and Application Control Events (Fortinet)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We add up web filter and app control events on FortiGate so overblocking, shadow apps, and policy drift are easier to see in one place.*

---

## Description

FortiGate UTM combines web filtering (FortiGuard URL categories), DNS filtering, and application control in one policy pass. Reviewing blocked categories, high-risk apps, and allow/deny ratios shows policy drift, shadow IT, and risky user behavior without full packet capture. It also helps justify license spend and tune noisy categories that generate help-desk load.

## Value

Security teams analyze FortiGate web filter and application control events by risk level, detecting malware access, policy violations, and evasion attempts through proxy/anonymizer usage.

## Implementation

Enable UTM logging on policies using web filter and application control; send UTM logs to a dedicated index if volume is high. Use the Fortinet TA for parsing. Build dashboards for top blocked categories and applications; alert on blocks for sensitive groups (executives, servers) or sudden spikes in `proxy`/`vpn` application blocks. Periodically review `act=blocked` outliers to refine explicit allow rules and DNS filter lists.

## Detailed Implementation

### Prerequisites
* FortiGate UTM web filter and application control logs. Data in `index=fortinet` or `index=firewall` with `sourcetype=fgt_utm` or `sourcetype=fgt_log`. Key fields: `catdesc` (URL category), `hostname`, `url`, `action` (blocked/allowed/monitored), `appcat` (application category), `app` (application name), `profile`, `policyid`.
* FortiGate UTM: combines web filtering (FortiGuard URL categories, custom categories, DNS filtering), application control (deep packet inspection), and SSL inspection in a single policy. Categories defined in `config webfilter profile` and `config application list`.

### Step 1 — - Configure data collection
```
# FortiGate CLI -- enable UTM logging
config webfilter profile
    edit "default"
        config ftgd-wf
            config filters
                edit 1
                    set category 2    # Adult
                    set action block
                next
                edit 2
                    set category 7    # Malware
                    set action block
                next
            end
        end
        set log-all-url enable
    next
end

config application list
    edit "default"
        set other-application-action pass
        set other-application-log enable
        config entries
            edit 1
                set category 5    # P2P
                set action block
            next
        end
    next
end
```
Verify:
```spl
index=fortinet sourcetype="fgt_utm" earliest=-4h
| stats count by catdesc, action, app
| sort -count | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- Web filter and application control events:**
```spl
index=fortinet sourcetype="fgt_utm" earliest=-4h
| eval url_category=coalesce(catdesc, cat, category)
| eval application=coalesce(app, appcat, application)
| eval act=lower(coalesce(action, utmaction))
| eval hostname=coalesce(hostname, dstname)
| eval user=coalesce(user, srcuser, unauthuser)
| eval src=coalesce(srcip, src_ip, src)
| eval risk_level=case(
    match(url_category, "(?i)malware|phishing|botnet|command.and.control"), "CRITICAL -- threat category",
    match(url_category, "(?i)proxy|vpn|anonymizer"), "HIGH -- evasion attempt",
    match(act, "(?i)block") AND match(url_category, "(?i)adult|gambling|weapons"), "MEDIUM -- policy violation",
    match(application, "(?i)tor|bitTorrent|p2p"), "HIGH -- high-risk application",
    match(act, "(?i)block"), "INFO -- blocked",
    1==1, "LOW")
| where risk_level != "LOW"
| stats count as events dc(src) as unique_users values(user) as users values(hostname) as sites by risk_level, url_category, application, act
| sort risk_level, -events
```

### Step 3 — - Validate
(a) CLI: `diagnose wad stats` -- check web filter processing statistics.
(b) CLI: `diagnose application list` -- verify application signatures are current.
(c) Test: attempt to access a blocked category and verify block page appears.

### Step 4 — - Operationalize
Dashboard ("FortiGate -- UTM Web Filter & App Control"):
* Row 1 -- Single-value: "Threat blocks", "Policy violations", "Evasion attempts".
* Row 2 -- Category block distribution.
* Row 3 -- Top blocked users and sites.

Alert: Critical (malware/phishing/C2 category access): SOC investigation.
High (anonymizer/proxy/Tor usage): potential policy evasion.

### Step 5 — - Troubleshooting

* **Web filter not blocking HTTPS** -- SSL deep inspection must be enabled. Verify: `config firewall ssl-ssh-profile`. Without inspection, only SNI-based filtering works (category detection is limited).

* **Application misidentified** -- FortiGuard application DB may need update: `exec update-now`. Custom application signatures can override default classification.

* **User not identified in logs** -- Enable FSSO (Fortinet Single Sign-On) or explicit proxy authentication. Without user identification, logs show only source IP.

## SPL

```spl
index=firewall sourcetype IN ("fgt_utm","fortinet_fortios_utm")
| eval cat=coalesce(catdesc, category, urlfilter_cat, web_cat)
| eval app_name=coalesce(app, appname, applist, app_cat)
| eval act=lower(coalesce(action, utm_action))
| eval device=coalesce(devname, dvc, host)
| stats count by device act cat app_name hostname src
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Bar chart (top categories), Table (user/src, app, action), Pie chart (block vs allow ratio).

## Known False Positives

Overblocking categories, new SaaS, and end-user workarounds can make web or app control logs noisy by design.

## References

- [Splunkbase app 2846](https://splunkbase.splunk.com/app/2846)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
