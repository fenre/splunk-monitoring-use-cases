<!-- AUTO-GENERATED from UC-2.2.9.json — DO NOT EDIT -->

---
id: "2.2.9"
title: "Virtual Switch Dropped Packets and Network Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.2.9 · Virtual Switch Dropped Packets and Network Errors

## Description

Virtual switch dropped packets indicate congestion, misconfigured VLAN tagging, or bandwidth management policy throttling. Hyper-V Extensible Switch drops are invisible from within the VM, making hypervisor-level monitoring the only way to detect them.

## Value

Virtual switch dropped packets indicate congestion, misconfigured VLAN tagging, or bandwidth management policy throttling. Hyper-V Extensible Switch drops are invisible from within the VM, making hypervisor-level monitoring the only way to detect them.

## Implementation

Configure Perfmon inputs for `Hyper-V Virtual Network Adapter` (Dropped Packets Incoming/Outgoing, Packets Received/Sent Errors) and `Hyper-V Virtual Switch` (Dropped Packets/sec). Alert when any adapter shows >0 dropped packets sustained over 5 minutes. Correlate with bandwidth usage to distinguish congestion from misconfiguration.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V Perfmon inputs).
• Ensure the following data sources are available: `sourcetype=Perfmon:HyperV` (Hyper-V Virtual Switch, Hyper-V Virtual Network Adapter).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs for `Hyper-V Virtual Network Adapter` (Dropped Packets Incoming/Outgoing, Packets Received/Sent Errors) and `Hyper-V Virtual Switch` (Dropped Packets/sec). Alert when any adapter shows >0 dropped packets sustained over 5 minutes. Correlate with bandwidth usage to distinguish congestion from misconfiguration.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Virtual Network Adapter" (counter="Dropped Packets Incoming" OR counter="Dropped Packets Outgoing")
| stats sum(Value) as total_drops by instance, host, counter
| where total_drops > 0
| sort -total_drops
| table instance, host, counter, total_drops
```

Understanding this SPL

**Virtual Switch Dropped Packets and Network Errors** — Virtual switch dropped packets indicate congestion, misconfigured VLAN tagging, or bandwidth management policy throttling. Hyper-V Extensible Switch drops are invisible from within the VM, making hypervisor-level monitoring the only way to detect them.

Documented **Data sources**: `sourcetype=Perfmon:HyperV` (Hyper-V Virtual Switch, Hyper-V Virtual Network Adapter). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V Perfmon inputs). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:HyperV. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:HyperV". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by instance, host, counter** so each row reflects one combination of those dimensions.
• Filters the current rows with `where total_drops > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Virtual Switch Dropped Packets and Network Errors**): table instance, host, counter, total_drops

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (adapter, host, drops), Line chart (drops over time), Bar chart (top adapters by drops).

## SPL

```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Virtual Network Adapter" (counter="Dropped Packets Incoming" OR counter="Dropped Packets Outgoing")
| stats sum(Value) as total_drops by instance, host, counter
| where total_drops > 0
| sort -total_drops
| table instance, host, counter, total_drops
```

## Visualization

Table (adapter, host, drops), Line chart (drops over time), Bar chart (top adapters by drops).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
