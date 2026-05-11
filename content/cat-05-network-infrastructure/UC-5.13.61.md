<!-- AUTO-GENERATED from UC-5.13.61.json — DO NOT EDIT -->

---
id: "5.13.61"
title: "Rogue AP and aWIPS Alert Monitoring"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.61 · Rogue AP and aWIPS Alert Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for unauthorised wireless access points plugged into your network — devices that someone brought in without permission that could be used to steal data or sneak into the system. When one is detected, your security team gets an immediate alert so they can find and disconnect it before any damage is done.*

---

## Description

Detects rogue access points and wireless intrusion prevention (aWIPS) alerts from Catalyst Center's Assurance engine, identifying unauthorised wireless infrastructure that may be used for eavesdropping, man-in-the-middle attacks, or data exfiltration — a critical security control for NIST AC-18 (Wireless Access) and PCI DSS 11.2.1 (Rogue Wireless Detection).

## Value

A rogue AP plugged into your wired network creates an uncontrolled wireless entry point that bypasses all your security controls — firewalls, NAC, IDS. An attacker-operated rogue AP can intercept credentials, inject traffic, or provide persistent backdoor access. Catalyst Center's built-in rogue detection uses the managed AP infrastructure as distributed sensors — every legitimate AP scans for unauthorised wireless signals. This UC centralises those detections in Splunk for cross-domain correlation (with ISE, firewall, physical access logs) and provides the continuous rogue monitoring evidence that PCI DSS assessors require as an alternative to quarterly wireless scans.

## Implementation

Same `issue` input as UC-5.13.21. Filter to Security category with rogue/aWIPS keywords. For real-time detection, enable HEC webhooks for Catalyst Center security event notifications (UC-5.13.64). Schedule as alert: `*/15 * * * *`, trigger on any rogue detection.

## Detailed Implementation

### Prerequisites
- UC-5.13.21 (Issue Summary) must be operational — same `issue` data feed.
- Catalyst Center must have rogue AP detection enabled: **Assurance > Rogue Management > Settings**. Verify detection mode (Monitor, Containment, or Auto-containment).
- For PCI DSS 11.2.1, document this UC as the continuous rogue monitoring control. QSAs may accept continuous WIDS monitoring as an alternative to quarterly wireless scans.
- For real-time detection (sub-15-minute latency), enable HEC webhooks for Security event notifications from Catalyst Center (UC-5.13.64–66).

### Step 1 — Configure data collection
Same `issue` input as UC-5.13.21. Rogue AP detections appear as Assurance issues in the Security category with names containing `rogue`, `aWIPS`, or `unauthorized`.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Security" earliest=-30d
| stats dc(issueId) as security_issues values(name) as issue_names
```
If rogue detections are present, you'll see issue names containing `rogue` or `aWIPS`.

For real-time webhook detection:
```spl
index=catalyst sourcetype="cisco:dnac:event:notification" eventType="*ROGUE*" OR description="*rogue*" earliest=-7d
| stats count
```

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Security" (name="*rogue*" OR name="*aWIPS*" OR name="*unauthorized*")
| stats dc(issueId) as alert_count values(name) as alert_types values(deviceName) as detecting_aps by siteId
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site=coalesce(siteName, siteId)
| sort -alert_count
```

Why filter by category and keyword: Catalyst Center's Security category includes multiple issue types. The keyword filter isolates wireless-specific security events (rogue, aWIPS) from other security issues.

Why `values(deviceName) as detecting_aps`: shows which managed APs detected the rogue. This narrows the physical search area — if AP-Floor3-IDF-A detected the rogue, the unauthorised AP is near that location.

Why `by siteId`: groups detections by location. A single rogue detected by 3 APs at the same site is one incident, not three.

Schedule as Alert: `*/15 * * * *`, time range `-30m`, trigger on any results. Route to security operations with high urgency. Throttle by `siteId` for 4 hours (same rogue at the same site).

For SOAR integration (UC-5.13.76 — Rogue AP Containment playbook):
```spl
<base search>
| eval action_required=if(alert_count > 0, "INVESTIGATE — potential rogue AP", "no action")
```

### Step 3 — Validate
(a) In a lab, create a rogue AP (personal hotspot near a managed AP). Catalyst Center should detect it within 15 minutes. The issue should appear in the Splunk search.
(b) Cross-reference with **Catalyst Center > Assurance > Rogue Management** — the rogue AP list should match.
(c) For PCI environments: verify the detection covers all CDE locations by checking that managed APs exist at every CDE site.
(d) Vendor UI parity: compare the rogue count with **Catalyst Center > Assurance > Rogue Management > Summary**.

### Step 4 — Operationalize
- Alert: page security operations on any rogue AP detection. Include site, detecting APs, and alert type.
- SOAR: trigger the Rogue AP Containment playbook (UC-5.13.76) for automated investigation.
- PCI evidence: maintain a monthly rogue detection report. Zero detections is ideal; each detection should have an investigation outcome (legitimate neighbour, contained rogue, remediated).

Runbook (owner: Security Operations):
1. Receive rogue AP alert. Note the `site` and `detecting_aps`.
2. Physical investigation: go to the area near the detecting APs. Look for unauthorised hardware (small APs plugged into Ethernet jacks, bridge devices, personal hotspots).
3. If a physical rogue is found: disconnect it immediately. Photograph it. File a security incident report.
4. If no physical rogue found: check if the detection is from a neighbour's AP (multi-tenant building). Add to the `rogue_exceptions` lookup if confirmed as a neighbour.
5. For aWIPS alerts (wireless intrusion): investigate the attack vector. Check for deauthentication floods, evil twin SSIDs, or other wireless attacks. Escalate to the security incident response team.
6. Document the investigation outcome for PCI DSS 11.2.1 evidence.

### Step 5 — Troubleshooting

- **No rogue detections ever** — either rogue detection is disabled in Catalyst Center, or no rogues exist (ideal). Verify in **Catalyst Center > Assurance > Rogue Management > Settings** that detection is enabled.

- **Too many rogue detections** — multi-tenant building with many neighbours. Classify neighbour APs as 'known' in Catalyst Center Rogue Management and suppress them.

- **Rogue detected but can't be physically located** — the detecting AP identifies the general area, not the exact location. Use a wireless analyser (Ekahau) to triangulate the rogue's physical position.

- **aWIPS alerts during wireless site surveys** — expected. Coordinate survey schedules and suppress during survey windows.

- **Rogue appears and disappears repeatedly** — intermittent rogue (e.g., someone bringing a personal AP to work occasionally). Set up a persistent tracking case.

- **PCI QSA doesn't accept continuous WIDS as alternative to quarterly scans** — provide: (1) this UC's detection capability documentation, (2) managed AP coverage map showing all CDE locations have detection capability, (3) 90-day detection history with investigation outcomes.

- **Rogue MAC address not in the issue data** — the `issue` feed may not include the rogue's MAC. Check the `event:notification` webhook data which often has more detail.

- **Want to auto-contain rogues** — Catalyst Center supports auto-containment (sends deauth frames). Enable cautiously — false containment of a neighbour's AP can cause legal issues. Use the SOAR playbook (UC-5.13.76) for human-in-the-loop containment.

Additional operational context for Rogue AP and aWIPS Alert Monitoring:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Security" (name="*rogue*" OR name="*aWIPS*" OR name="*unauthorized*")
| stats dc(issueId) as alert_count values(name) as alert_types values(deviceName) as detecting_aps by siteId
| lookup catalyst_site_lookup siteId OUTPUT siteName
| eval site=coalesce(siteName, siteId)
| sort -alert_count
```

## Visualization

(1) Table: site, alert_count, alert_types, detecting_aps — showing where rogue APs were detected and by which managed APs. (2) Single value: active rogue detections (red ≥ 1). (3) Map: plot rogue detections by site if geo data is available. (4) Timeline: rogue detection events over 30 days for pattern analysis.

## Known False Positives

**Neighbouring business's legitimate APs detected as rogue.** In multi-tenant buildings, neighbouring organisations' APs appear in rogue scans. Distinguish by checking the MAC address OUI — known vendor prefixes (Cisco, Aruba, Meraki) from adjacent tenants are 'contained' but not malicious. Suppress by adding known-neighbour MAC prefixes to a `rogue_exceptions` lookup.

**Personal hotspots (mobile phones) triggering rogue detection.** Employees' personal hotspots on their phones can trigger rogue AP alerts. Distinguish by checking whether the SSID matches common hotspot names (iPhone, AndroidAP). Suppress by classifying mobile hotspots as low-risk in the rogue policy and filtering them from the security alert.

**Misconfigured corporate AP appearing as rogue.** A legitimate AP that was physically moved or reconfigured outside Catalyst Center may be classified as rogue because Catalyst Center doesn't recognise its new parameters. Distinguish by checking the MAC address against the Catalyst Center inventory. Fix by rediscovering the AP in Catalyst Center.

**aWIPS false positive from legitimate wireless tools.** Network engineers running wireless survey tools (Ekahau, AirMagnet) may trigger aWIPS alerts due to active probing. Distinguish by correlating with planned site survey schedules. Suppress by scheduling survey windows and excluding them from alerting.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Rogue AP Detection — Cisco Docs](https://www.cisco.com/c/en/us/)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [PCI DSS v4.0 — Requirement 11.2.1 Wireless Detection](https://www.pcisecuritystandards.org/document_library/)
