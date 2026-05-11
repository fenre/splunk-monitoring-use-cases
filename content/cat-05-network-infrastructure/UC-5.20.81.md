<!-- AUTO-GENERATED from UC-5.20.81.json — DO NOT EDIT -->

---
id: "5.20.81"
title: "RFC 9099 Operational Security Checklist — Automated Status Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.81 · RFC 9099 Operational Security Checklist — Automated Status Tracking

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*The international standards body (IETF) published a comprehensive guide book (RFC 9099) for safely running the new postal system (IPv6). We created a master checklist from the guide book and automatically check each item. It's like having a safety inspector who checks every chapter of the safety manual and gives us a score.*

---

## Description

Provides a unified compliance tracking dashboard for RFC 9099 (BCP 256) — the IETF's authoritative guide for operational security of IPv6 networks. Maps each RFC 9099 section to one or more monitoring use cases in this catalog, aggregates their results, and produces a composite compliance score. RFC 9099 is the single most important reference document for IPv6 operational security.

## Value

RFC 9099 represents the collective operational experience of the IPv6 security community, distilled into actionable guidance. By mapping each section to automated monitoring, this dashboard transforms a 50-page reference document into a living compliance tracker. Security teams can see at a glance which RFC 9099 recommendations are being actively monitored, which have identified gaps, and which are not yet covered. This is the master dashboard that ties all IPv6 monitoring use cases together.

## Implementation

Create a lookup table mapping each RFC 9099 section to relevant use cases. Populate status automatically from use case results. Display as a composite compliance dashboard with drill-down to individual use cases.

## Detailed Implementation

### Prerequisites
- Familiarity with RFC 9099 sections and requirements.
- Multiple IPv6 use cases deployed and producing results.
- Lookup table mapping RFC 9099 sections to use case IDs.

### Step 1 — Configure data collection

**Create RFC 9099 section-to-UC mapping lookup:**
```csv
section,requirement,linked_uc,status,last_checked,evidence
§2.1.1 Address planning,"Document IPv6 address plan","5.20.8",pass,2026-05-01,"IPAM plan verified"
§2.1.2 SLAAC management,"Monitor SLAAC behaviour and flag anomalies","5.20.9;5.20.17",pass,2026-05-01,"SLAAC monitoring active"
§2.1.3 Privacy extensions,"Track privacy extension address churn","5.20.12",pass,2026-05-01,"Churn monitoring active"
§2.1.4 EUI-64 deprecation,"Detect and eliminate EUI-64 address usage","5.20.13;5.20.80",partial,2026-05-01,"12 devices still using EUI-64"
§2.2.1 BGP IPv6 security,"Monitor MP-BGP IPv6 sessions and RPKI ROV","5.20.44;5.20.49",pass,2026-05-01,"BGP IPv6 and RPKI active"
§2.2.2 OSPF/IS-IS IPv6,"Monitor OSPFv3 and IS-IS multi-topology","5.20.43;5.20.46",pass,2026-05-01,"Routing protocol monitoring active"
§2.2.3 Ingress filtering,"Verify BCP 38 uRPF for IPv6","5.20.50",fail,2026-05-01,"uRPF not verified on 8 edge routers"
§2.3.1 RA Guard,"RA Guard on all access ports","5.20.29",pass,2026-05-01,"100% coverage verified"
§2.3.2 SISF/FHS,"SISF binding table monitoring","5.20.31;5.20.32",pass,2026-05-01,"SISF monitoring active"
§2.3.3 NDP monitoring,"NDP cache trending and anomaly detection","5.20.19;5.20.20",pass,2026-05-01,"NDP monitoring active"
§2.4.1 ICMPv6 policy,"RFC 4890 compliant firewall rules","5.20.37;5.20.64",pass,2026-05-01,"ICMPv6 policy verified"
§2.4.2 Bogon filtering,"IPv6 bogon and martian filtering at perimeter","5.20.63",pass,2026-05-01,"Bogon filtering active"
§2.5 Extension headers,"Extension header filtering and abuse detection","5.20.41;5.20.42",pass,2026-05-01,"Extension header monitoring active"
§2.6.1 Flow monitoring,"IPv6 flow data collection and analysis","5.20.66;5.20.67",partial,2026-05-01,"3 exporters on v5 only"
§2.6.2 NDP cache logging,"Historical NDP cache logging for forensics","5.20.16",pass,2026-05-01,"NDP polling active every 30s"
§2.6.3 Address correlation,"IPv6-to-user attribution chain","5.20.15",partial,2026-05-01,"DUID-MAC gap on wireless"
§2.7.1 Tunnel detection,"Detect unauthorised 6to4/Teredo/ISATAP","5.20.57",pass,2026-05-01,"Tunnel detection active"
§2.7.2 Dual-stack parity,"IPv4/IPv6 service reachability parity","5.20.58",pass,2026-05-01,"Parity monitoring active"
§3 Management plane,"IPv6 management transport readiness","TBD",fail,2026-05-01,"Not yet assessed"
```
Upload as `rfc9099_status.csv`. Update linked UC results on a scheduled basis.

**Automated status update search (run weekly):**
```spl
| inputlookup rfc9099_status.csv
| lookup uc_health_status.csv linked_uc OUTPUT uc_status
| eval status=case(
    uc_status="green", "pass",
    uc_status="amber", "partial",
    uc_status="red", "fail",
    isnull(uc_status), "not_monitored")
| eval last_checked=strftime(now(), "%Y-%m-%d")
| outputlookup rfc9099_status.csv
```

### Step 2 — Create the dashboard

**Overall compliance score:**
```spl
| inputlookup rfc9099_status.csv
| stats count(eval(status="pass")) as passed count(eval(status="partial")) as partial count(eval(status="fail")) as failed count(eval(status="not_monitored")) as unmonitored
| eval total=passed + partial + failed + unmonitored
| eval score=round((passed + partial * 0.5) / total * 100, 0)
```

**Section detail with drill-down:**
```spl
| inputlookup rfc9099_status.csv
| eval status_icon=case(status="pass", "✓", status="partial", "◐", status="fail", "✗", 1=1, "?")
| table section, status_icon, requirement, linked_uc, last_checked, evidence
```

### Step 3 — Validate
(a) **Cross-reference.** For each 'pass' status, click through to the linked use case dashboard and verify the use case is actually running and producing healthy results.

(b) **Gap identification.** Any 'not_monitored' section should have a remediation plan with a target date for deploying the linked use case.

(c) **Expert review.** Have an IPv6 specialist review the mapping to ensure each RFC 9099 section is mapped to the correct use case(s).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RFC 9099 Compliance"):
- Row 1 — Single-value: overall compliance score. Gauge visualization.
- Row 2 — Section-by-section status table with status icons and drill-down links.
- Row 3 — Bar chart: pass/partial/fail/unmonitored distribution.
- Row 4 — Trend: compliance score over 12 months.

**Scheduling:** Automated status update weekly. Manual review quarterly. Executive summary monthly.

**Runbook:**
1. 'fail' sections: Review linked UCs. If UC exists but shows failures, remediate the underlying issue. If UC doesn't exist yet, prioritise deployment.
2. 'partial' sections: Identify specific sub-requirements that are failing. Create targeted remediation plans.
3. 'not_monitored' sections: Deploy the linked UC(s) and update the mapping.

### Step 5 — Troubleshooting

- **Mapping granularity.** RFC 9099 sections contain many sub-requirements. The mapping may need to be more granular for large organisations. Consider breaking sections into individual requirement rows.

- **Multi-vendor environments.** RFC 9099 compliance may vary by vendor. A requirement that's easily verified on Cisco may be harder to verify on Juniper. Document vendor-specific verification procedures.

- **Evolving document.** RFC 9099 may be updated or supplemented by new RFCs. Monitor the IETF v6ops working group for updates.

## SPL

```spl
| makeresults
| eval section=mvappend(
    "§2.1 Addressing — address plan and SLAAC/DHCPv6 management",
    "§2.2 Routing — BGP/OSPF/IS-IS IPv6 security and BCP 38",
    "§2.3 NDP and First-Hop Security — RA Guard, SISF, NDP monitoring",
    "§2.4 Filtering — ICMPv6 policy, bogon filtering, extension headers",
    "§2.5 Extension Headers — proper processing and filtering",
    "§2.6 Monitoring — flow data, NDP cache, address correlation, parity",
    "§2.7 Transition — tunnel detection, dual-stack parity, NAT64/DNS64",
    "§3 Management — management plane IPv6 transport")
| mvexpand section
| lookup rfc9099_status.csv section OUTPUT status last_checked evidence linked_uc
| eval compliant=if(status="pass", 1, 0)
| eventstats sum(compliant) as passed count as total
| eval overall_score=round(passed / total * 100, 0) . "%"
| table section, status, last_checked, evidence, linked_uc, overall_score
```

## Visualization

(1) Single-value: overall RFC 9099 compliance score (target: 100%). (2) Table: section-by-section status with evidence links. (3) Status indicator per section (pass/fail/partial). (4) Trend: compliance improvement over time.

## Known False Positives

**Sections not applicable.** Some RFC 9099 sections may not apply to all environments. For example, §2.7 (Transition Mechanisms) is irrelevant for native IPv6-only networks. Mark these as 'N/A' rather than 'fail'.

**Partial compliance.** Many sections have multiple sub-requirements. A section scored as 'partial' may have 80% of requirements met but one critical gap. Use the linked use case results for granular assessment.

**Monitoring vs enforcement.** RFC 9099 compliance requires both monitoring (detection) and enforcement (prevention). This dashboard tracks monitoring coverage. Enforcement verification requires separate configuration audits (see UC-5.20.79).

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (BCP 256)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 9099 Authors' Presentation — IETF 112 (operational context and deployment experience)](https://datatracker.ietf.org/meeting/)
