---
id: "2.3.5"
title: "Libvirt Network Filter and Firewall Rule Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.3.5 · Libvirt Network Filter and Firewall Rule Audit

## Description

VM-level firewall and filter rules can be changed accidentally or maliciously. Auditing ensures network isolation and compliance.

## Value

VM-level firewall and filter rules can be changed accidentally or maliciously. Auditing ensures network isolation and compliance.

## Implementation

Periodically dump VM network filter config and compute hash. Compare to baseline lookup. Alert on change. Run after change windows or daily.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`virsh nwfilter-list`, `virsh dumpxml`).
• Ensure the following data sources are available: Libvirt XML dump, nwfilter definitions.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Periodically dump VM network filter config and compute hash. Compare to baseline lookup. Alert on change. Run after change windows or daily.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype=libvirt_nwfilter host=*
| stats latest(rule_hash) as current by host, vm_name, filter_name
| inputlookup expected_nwfilter append=t
| eval drift=if(current!=expected_hash, "Yes", "No")
| where drift="Yes"
| table host vm_name filter_name
```

Understanding this SPL

**Libvirt Network Filter and Firewall Rule Audit** — VM-level firewall and filter rules can be changed accidentally or maliciously. Auditing ensures network isolation and compliance.

Documented **Data sources**: Libvirt XML dump, nwfilter definitions. **App/TA** (typical add-on context): Custom scripted input (`virsh nwfilter-list`, `virsh dumpxml`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: libvirt_nwfilter. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype=libvirt_nwfilter. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, vm_name, filter_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting.
• `eval` defines or adjusts **drift** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where drift="Yes"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Libvirt Network Filter and Firewall Rule Audit**): table host vm_name filter_name


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, VM, filter, drift), Compliance count.

## SPL

```spl
index=virtualization sourcetype=libvirt_nwfilter host=*
| stats latest(rule_hash) as current by host, vm_name, filter_name
| inputlookup expected_nwfilter append=t
| eval drift=if(current!=expected_hash, "Yes", "No")
| where drift="Yes"
| table host vm_name filter_name
```

## Visualization

Table (host, VM, filter, drift), Compliance count.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
