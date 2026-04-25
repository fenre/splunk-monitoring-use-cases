<!-- AUTO-GENERATED from UC-5.13.37.json — DO NOT EDIT -->

---
id: "5.13.37"
title: "Devices Affected by Active Advisories"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.37 · Devices Affected by Active Advisories

## Description

Maps security advisories to specific devices, showing which devices have the most advisories and which have critical-severity vulnerabilities.

## Value

Knowing which devices are most exposed enables risk-based patching prioritization — fix the devices with the most critical advisories first.

## Implementation

Enable the `securityadvisory` input. If `searchmatch` is noisy on multivalue `severities`, consider `mvfind` or `where mvfilter` patterns instead after validating the field format.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with `cisco:dnac:securityadvisory` in `index=catalyst`; confirm in raw events that `deviceId`, `deviceName`, `advisoryId`, and `severity` (or their equivalents) are extracted as you expect.
• Where possible, scope Catalyst to production intent domains so test or lab devices do not dominate “top at-risk” lists.
• `docs/implementation-guide.md`.

Step 1 — Configure data collection
• Default security-advisory poll is often hourly. Spares and lab gear that remain in Catalyst inventory still show advisories; decide whether to filter them in SPL or in Catalyst scope.

Step 2 — Per-device exposure roll-up
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats count as advisory_count values(advisoryId) as advisories values(severity) as severities by deviceId, deviceName, platformId | eval has_critical=if(searchmatch("*CRITICAL*"),1,0) | sort -has_critical -advisory_count
```

Understanding this SPL (noise vs risk)
**Devices Affected by Active Advisories** — Ranks which managed devices have the heaviest advisory **traffic** in the index, not a CVSS score per device. `count` can reflect multiple events per `advisoryId` per poll; add `dc(advisoryId)` in the same or a companion panel to show breadth. Replace `searchmatch` with an `mvfind` on `severities` if your multivalue field is well-behaved, to avoid substring false positives in free text.

**Pipeline walkthrough**
• `stats` per `deviceId` with lists of advisories and severities, `has_critical` as a quick sort key, then sort by critical presence and then row volume.

Step 3 — Validate
• Compare the top device to the Catalyst security advisory or PSIRT view for that hostname or serial. Allow one poll of skew.
• If you add site or owner fields via a second join to `cisco:dnac:device`, re-run counts to ensure joins do not duplicate rows.

Step 4 — Operationalize
• Use as a priority list for patching or SWIM campaigns; export top N with advisory IDs and CVE list for the CAB packet.

Step 5 — Troubleshooting
• Multiple controllers or tenants in one index: add a `where` on controller host or a tag the TA provides so clusters do not mix.
• `searchmatch` overmatches: tighten the `eval` to explicit multivalue checks when field structure allows.
• Flat “everything is bad” after a platform bug: verify Catalyst API and TA health, not just Splunk—compare total device inventory to advisory rows.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats count as advisory_count values(advisoryId) as advisories values(severity) as severities by deviceId, deviceName, platformId | eval has_critical=if(searchmatch("*CRITICAL*"),1,0) | sort -has_critical -advisory_count
```

## Visualization

Table (advisory_count, severities, advisories by device), bar chart of top at-risk deviceId.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
