<!-- AUTO-GENERATED from UC-5.2.46.json — DO NOT EDIT -->

---
id: "5.2.46"
title: "FortiGate Web Filter and Application Control Events (Fortinet)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.46 · FortiGate Web Filter and Application Control Events (Fortinet)

## Description

FortiGate UTM combines web filtering (FortiGuard URL categories), DNS filtering, and application control in one policy pass. Reviewing blocked categories, high-risk apps, and allow/deny ratios shows policy drift, shadow IT, and risky user behavior without full packet capture. It also helps justify license spend and tune noisy categories that generate help-desk load.

## Value

FortiGate UTM combines web filtering (FortiGuard URL categories), DNS filtering, and application control in one policy pass. Reviewing blocked categories, high-risk apps, and allow/deny ratios shows policy drift, shadow IT, and risky user behavior without full packet capture. It also helps justify license spend and tune noisy categories that generate help-desk load.

## Implementation

Enable UTM logging on policies using web filter and application control; send UTM logs to a dedicated index if volume is high. Use the Fortinet TA for parsing. Build dashboards for top blocked categories and applications; alert on blocks for sensitive groups (executives, servers) or sudden spikes in `proxy`/`vpn` application blocks. Periodically review `act=blocked` outliers to refine explicit allow rules and DNS filter lists.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-fortinet_fortigate` (Splunkbase 2846).
• Ensure the following data sources are available: `sourcetype=fgt_utm`, `sourcetype=fortinet_fortios_utm`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable UTM logging on policies using web filter and application control; send UTM logs to a dedicated index if volume is high. Use the Fortinet TA for parsing. Build dashboards for top blocked categories and applications; alert on blocks for sensitive groups (executives, servers) or sudden spikes in `proxy`/`vpn` application blocks. Periodically review `act=blocked` outliers to refine explicit allow rules and DNS filter lists.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype IN ("fgt_utm","fortinet_fortios_utm")
| eval cat=coalesce(catdesc, category, urlfilter_cat, web_cat)
| eval app_name=coalesce(app, appname, applist, app_cat)
| eval act=lower(coalesce(action, utm_action))
| eval device=coalesce(devname, dvc, host)
| stats count by device act cat app_name hostname src
| sort -count
```

Understanding this SPL

**FortiGate Web Filter and Application Control Events (Fortinet)** — FortiGate UTM combines web filtering (FortiGuard URL categories), DNS filtering, and application control in one policy pass. Reviewing blocked categories, high-risk apps, and allow/deny ratios shows policy drift, shadow IT, and risky user behavior without full packet capture. It also helps justify license spend and tune noisy categories that generate help-desk load.

Documented **Data sources**: `sourcetype=fgt_utm`, `sourcetype=fortinet_fortios_utm`. **App/TA** (typical add-on context): `TA-fortinet_fortigate` (Splunkbase 2846). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cat** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **app_name** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **act** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **device** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by device act cat app_name hostname src** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Web data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Web model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Reconcile a sample of results with the FortiGate GUI or FortiManager for the same policies, objects, and time range.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top categories), Table (user/src, app, action), Pie chart (block vs allow ratio).

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

## References

- [Splunkbase app 2846](https://splunkbase.splunk.com/app/2846)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
