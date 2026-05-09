<!-- AUTO-GENERATED from UC-5.1.74.json — DO NOT EDIT -->

---
id: "5.1.74"
title: "VLAN Configuration Change and VTP Audit"
status: "community"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.74 · VLAN Configuration Change and VTP Audit

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Configuration, Compliance &middot; **Wave:** Crawl &middot; **Status:** Community

*We watch every change to the network's virtual segments — the imaginary boundaries that separate the finance network from the guest network from the printer network. A bad change can knock everyone off the network instantly. We alert on every change so the team can confirm it was approved before any damage spreads.*

---

## Description

Captures VLAN create / delete events and VTP revision-number changes from switch syslog. Each event represents a Layer-2 topology mutation that propagates across every trunk port in the VTP domain — and a misconfigured one is one of the few changes that can cause a network-wide outage in seconds.

## Value

VLAN configuration is the most consequential Layer-2 change a network engineer can make. A bad VTP revision number from a single switch can wipe the entire VLAN database across the VTP domain — the famous 'VTP bomb' that took down everyone's network at least once before VTP version 3 added explicit primary-server control. Outside the VTP horror story, every VLAN change is a change-management item: did the change-window match the change-ticket? Did it happen on the approved switch? Did it match what the design said? This UC turns the audit trail from 'check the running-config diff next quarter' into 'see every change as it happens, with the user that made it'.

## Implementation

Forward switch syslog to Splunk at severity 6 or lower. Monitor VLAN create / delete events and VTP revision-number changes. Alert on any VLAN modification outside an approved change window. For VTP-mode `transparent` environments — and any modern config-as-code shop — monitor configuration-file checksum changes instead of (or alongside) the legacy syslog mnemonics.

## SPL

```spl
index=network sourcetype="cisco:ios"
  "%VLAN_MGR-6-VLAN_CREATE" OR "%VLAN_MGR-6-VLAN_DELETE" OR "%VTP-6-VTP_REV_CHANGE"
| stats count by host, _raw
| sort - count
```

## Visualization

Table (VLAN changes by device with raw event line), Timeline (change history over the past 24h / 7d), Single-value (VLAN modifications in the last 24h, the headline tile of the change-management dashboard).

## Known False Positives

**VLAN adds during scheduled provisioning.** New service installations frequently add VLANs across the access tier. Suppress alerts during announced provisioning windows or filter on VLAN-ID ranges reserved for new service creation.

**Test / lab VLANs in approved test ranges.** Lab VLANs (e.g. 4000–4094) are intentionally created and destroyed during testing. Filter alerts on production VLAN-ID ranges only.

**Failover VLAN database resync after VTP role change.** When VTP roles shift (primary → secondary on the new chassis), the VLAN database resyncs and emits create-style events for every existing VLAN. Tolerate a 30-minute warm-up window after a chassis-replacement event.

## References

- [Cisco VTP Version 3 — preventing the VTP bomb](https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst3850/software/release/16-1/configuration_guide/lyr2/b_161_lyr2_3850_cg/b_161_lyr2_3850_cg_chapter_010001.html)
- [Cisco VLAN Configuration Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/lanswitch/configuration/15-mt/lnsw-15-mt-book.html)
