<!-- AUTO-GENERATED from UC-4.2.41.json — DO NOT EDIT -->

---
id: "4.2.41"
title: "Private Link DNS Resolution"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.41 · Private Link DNS Resolution

## Description

Private Endpoint FQDNs resolve via private DNS zones; NXDOMAIN or public resolution leaks traffic or breaks apps.

## Value

Private Endpoint FQDNs resolve via private DNS zones; NXDOMAIN or public resolution leaks traffic or breaks apps.

## Implementation

Forward DNS resolver logs from VNet-linked zones or Azure Firewall DNS proxy. Alert on high NXDOMAIN for PE FQDNs. Validate zone links and auto-registration on new NICs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (DNS query logs), `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure DNS private zone query logs (if enabled), VM DNS client logs, `sourcetype=dns:query`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward DNS resolver logs from VNet-linked zones or Azure Firewall DNS proxy. Alert on high NXDOMAIN for PE FQDNs. Validate zone links and auto-registration on new NICs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="dns:query" zone_type="private"
| stats count(eval(rcode!="NOERROR")) as failures, count as total by fqdn, src
| eval fail_pct=round(100*failures/total,2)
| where fail_pct > 5 AND total > 20
```

Understanding this SPL

**Private Link DNS Resolution** — Private Endpoint FQDNs resolve via private DNS zones; NXDOMAIN or public resolution leaks traffic or breaks apps.

Documented **Data sources**: Azure DNS private zone query logs (if enabled), VM DNS client logs, `sourcetype=dns:query`. **App/TA** (typical add-on context): Custom (DNS query logs), `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: dns:query. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="dns:query". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by fqdn, src** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **fail_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where fail_pct > 5 AND total > 20` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (fqdn, fail %), Timeline (DNS errors), Map (source subnet).

## SPL

```spl
index=network sourcetype="dns:query" zone_type="private"
| stats count(eval(rcode!="NOERROR")) as failures, count as total by fqdn, src
| eval fail_pct=round(100*failures/total,2)
| where fail_pct > 5 AND total > 20
```

## Visualization

Table (fqdn, fail %), Timeline (DNS errors), Map (source subnet).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
