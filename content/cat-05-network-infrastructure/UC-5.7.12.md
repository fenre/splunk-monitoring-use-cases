<!-- AUTO-GENERATED from UC-5.7.12.json — DO NOT EDIT -->

---
id: "5.7.12"
title: "IPFIX Application-ID Mapping (Cisco NBAR / App-ID)"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.7.12 · IPFIX Application-ID Mapping (Cisco NBAR / App-ID)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Security, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We read the network equipment’s own labels for what each conversation is for. That helps us rank heavy uses fairly and spot mystery labels that need a human name before we trust the picture.*

---

## Description

Summarizes bytes and endpoints keyed on exporter-reported application identifiers so teams can verify classification coverage, spot unnamed or stale numeric identifiers, and reconcile policy labels with observed flows.

## Value

Application owners and network operators prioritize troubleshooting and capacity decisions using vendor-native application labels instead of port guesses, catch misclassification after routing changes, and give security teams consistent names for allowlists and investigations.

## Implementation

Export NBAR App-ID in IPFIX templates; ingest with NetFlow TA; maintain a supplemental lookup for vendor IDs; build top-application panels and alerts for unknown IDs.

## Detailed Implementation

### Prerequisites
- Cisco platforms with NBAR2 enabled and Flexible NetFlow monitors referencing application-performance or optimized-application-monitors where supported.
- Splunk Add-on for NetFlow receiving IPFIX with information elements for `applicationId` mapped into `application_id` and textual names into `application_name` fields.
- Optional spreadsheet maintained by the application governance team listing business-critical labels and risk tiers.

### Step 1 — Configure data collection
On the exporter, confirm `show flow exporter template` includes application fields. Increase template refresh modestly during rollout so Splunk learns new IEs quickly. Document timezone alignment between flow timestamps and change windows.

### Step 2 — Create the search
Schedule the primary SPL hourly. Add `| where match(last_app_name, "^app_id_")` as an alert for unresolved numeric IDs. Enrich with `| lookup nbar_appid_to_category.csv application_id OUTPUT category risk` for SOC views.

### Step 3 — Validate
Compare Splunk’s top five apps for a site against Cisco DNA Center or Catalyst Center QoS reports for the same hour; variances above twenty percent warrant template checks.

### Step 4 — Operationalize
Embed results in a Dashboard Studio tab beside traditional port-based charts; route unknown-ID alerts to the networking queue with attached interface and exporter metadata.

### Step 5 — Troubleshooting
If `application_name` disappears after an IOS upgrade, reload the NBAR protocol pack and verify Flexible NetFlow records still reference NBAR attributes. Encrypted traffic may fall back to generic web labels—pair with metadata from dedicated encrypted-traffic analytics feeds when needed.

## SPL

```spl
index=netflow (sourcetype="stream:ipfix" OR sourcetype="netflow")
| eval app_key=coalesce(application_name, "app_id_".application_id)
| stats sum(bytes) as total_bytes sum(packets) as total_packets dc(src) as sources dc(dest) as destinations last(application_name) as last_app_name
  by application_id app_key
| eval gb=round(total_bytes/1073741824, 3)
| sort -total_bytes
| head 50
```

## Visualization

Bar chart of gb by app_key; drilldown table with sources, destinations, application_id; treemap when category lookup exists.

## Known False Positives

Midnight software updates rotate protocol packs and temporarily skew counts. Split tunnels and Secure Web Gateway hairpins can duplicate flows. Some records show aggregate "web" labels that hide fine-grained SaaS usage.

## References

- [Cisco IOS XE — Flexible NetFlow Configuration Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/fnetflow/configuration/xe-16/fnf-xe-16-book.pdf)
- [IANA IPFIX Information Elements](https://www.iana.org/assignments/ipfix/ipfix.xhtml)
