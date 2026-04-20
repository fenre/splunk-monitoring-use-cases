---
id: "5.1.63"
title: "Aruba CX VSF Stack Health (HPE Aruba)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.63 · Aruba CX VSF Stack Health (HPE Aruba)

## Description

VSF stacks present one logical switch; member loss or conductor changes can isolate access VLANs or reduce east-west capacity without a full box failure. Early detection of member state changes and inter-switch link issues prevents prolonged segments of a floor or IDF running on a single surviving member. Splunk gives stack-level visibility where SNMP polling alone may lag during control-plane events.

## Value

VSF stacks present one logical switch; member loss or conductor changes can isolate access VLANs or reduce east-west capacity without a full box failure. Early detection of member state changes and inter-switch link issues prevents prolonged segments of a floor or IDF running on a single surviving member. Splunk gives stack-level visibility where SNMP polling alone may lag during control-plane events.

## Implementation

Send CX switch syslog to a dedicated VIP or SC4S; tag `host` or `orig_host` so searches can narrow to CX models. Filter false positives from non-CX syslog sharing the index. Alert on member down, split stack indicators, or repeated conductor re-election. Cross-check with `show vsf` if you ingest periodic CLI or API snapshots.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: HPE Aruba CX syslog.
• Ensure the following data sources are available: Aruba CX syslog (`sourcetype=syslog` or site-specific parser such as `hpe:aruba` if configured).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Send CX switch syslog to a dedicated VIP or SC4S; tag `host` or `orig_host` so searches can narrow to CX models. Filter false positives from non-CX syslog sharing the index. Alert on member down, split stack indicators, or repeated conductor re-election. Cross-check with `show vsf` if you ingest periodic CLI or API snapshots.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=syslog
| search "VSF" OR "Virtual Switching Framework" OR "stack" OR "conductor" OR "standby" OR "Member"
| search "Aruba" OR "6300" OR "6400" OR "8320" OR "8360" OR host="*cx*"
| rex field=_raw "(?i)member\s*(?<member_slot>\d+)"
| stats count as vsf_events, latest(_raw) as last_event by host, member_slot
| sort -vsf_events
```

Understanding this SPL

**Aruba CX VSF Stack Health (HPE Aruba)** — VSF stacks present one logical switch; member loss or conductor changes can isolate access VLANs or reduce east-west capacity without a full box failure. Early detection of member state changes and inter-switch link issues prevents prolonged segments of a floor or IDF running on a single surviving member. Splunk gives stack-level visibility where SNMP polling alone may lag during control-plane events.

Documented **Data sources**: Aruba CX syslog (`sourcetype=syslog` or site-specific parser such as `hpe:aruba` if configured). **App/TA** (typical add-on context): HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, member_slot** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stack topology-style table (member ID, role, last event); timeline of conductor changes; heatmap of stacks with events.

## SPL

```spl
index=network sourcetype=syslog
| search "VSF" OR "Virtual Switching Framework" OR "stack" OR "conductor" OR "standby" OR "Member"
| search "Aruba" OR "6300" OR "6400" OR "8320" OR "8360" OR host="*cx*"
| rex field=_raw "(?i)member\s*(?<member_slot>\d+)"
| stats count as vsf_events, latest(_raw) as last_event by host, member_slot
| sort -vsf_events
```

## Visualization

Stack topology-style table (member ID, role, last event); timeline of conductor changes; heatmap of stacks with events.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
