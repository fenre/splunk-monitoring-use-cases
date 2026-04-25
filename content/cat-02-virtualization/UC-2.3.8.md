<!-- AUTO-GENERATED from UC-2.3.8.json — DO NOT EDIT -->

---
id: "2.3.8"
title: "Virtio Driver and Balloon Status in Guests"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.3.8 · Virtio Driver and Balloon Status in Guests

## Description

Virtio drivers and balloon driver improve I/O and allow memory reclamation. Missing or inactive drivers cause poor performance and overcommit issues.

## Value

Virtio drivers and balloon driver improve I/O and allow memory reclamation. Missing or inactive drivers cause poor performance and overcommit issues.

## Implementation

Use `virsh dommemstat` to get balloon current and maximum. High ratio indicates host is reclaiming memory from the VM. Alert when ratio >50% for critical VMs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (guest agent or in-guest script).
• Ensure the following data sources are available: QEMU guest agent, `virsh dommemstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use `virsh dommemstat` to get balloon current and maximum. High ratio indicates host is reclaiming memory from the VM. Alert when ratio >50% for critical VMs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype=kvm_balloon host=*
| stats latest(balloon_current_kb) as balloon_kb, latest(balloon_max_kb) as max_kb by host, vm_name
| eval balloon_ratio=round(balloon_kb/max_kb*100, 1)
| where balloon_ratio > 50
| table host vm_name balloon_kb max_kb balloon_ratio
```

Understanding this SPL

**Virtio Driver and Balloon Status in Guests** — Virtio drivers and balloon driver improve I/O and allow memory reclamation. Missing or inactive drivers cause poor performance and overcommit issues.

Documented **Data sources**: QEMU guest agent, `virsh dommemstat`. **App/TA** (typical add-on context): Custom scripted input (guest agent or in-guest script). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: kvm_balloon. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype=kvm_balloon. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, vm_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **balloon_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where balloon_ratio > 50` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Virtio Driver and Balloon Status in Guests**): table host vm_name balloon_kb max_kb balloon_ratio

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, balloon KB, ratio), Line chart (balloon over time).

## SPL

```spl
index=virtualization sourcetype=kvm_balloon host=*
| stats latest(balloon_current_kb) as balloon_kb, latest(balloon_max_kb) as max_kb by host, vm_name
| eval balloon_ratio=round(balloon_kb/max_kb*100, 1)
| where balloon_ratio > 50
| table host vm_name balloon_kb max_kb balloon_ratio
```

## Visualization

Table (VM, balloon KB, ratio), Line chart (balloon over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
