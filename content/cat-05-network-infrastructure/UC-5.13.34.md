<!-- AUTO-GENERATED from UC-5.13.34.json — DO NOT EDIT -->

---
id: "5.13.34"
title: "Security Advisory (PSIRT) Overview"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.34 · Security Advisory (PSIRT) Overview

## Description

Provides an overview of all Cisco Product Security Incident Response Team (PSIRT) advisories affecting devices managed by Catalyst Center.

## Value

Security advisories represent known vulnerabilities in your network infrastructure. This overview ensures none are missed and all are tracked to remediation.

## Implementation

Enable the `securityadvisory` input in the Cisco Catalyst TA. The TA calls `GET /dna/intent/api/v1/security-advisory/advisory` on a **3600s** default interval. Key fields: `advisoryId`, `severity` (CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL), `cveId`, `deviceCount`, `advisoryTitle`, and `fixedVersions` where present.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (Splunkbase 7538); **securityadvisory** into `index=catalyst`, sourcetype `cisco:dnac:securityadvisory`.
• Catalyst Center release with **PSIRT** / **Security Advisory** integration enabled; API user with read access to the advisory endpoints your **TA** documents.
• Joint process with **vulnerability management** (ServiceNow, Qualys, etc.) for **remediation** tracking—this feed is **advisory and inventory context**, not a replacement for **active scanning**.
• `docs/implementation-guide.md` for TA credentials, proxy, and index sizing (typically **low** volume, **retain** long enough for **audit** lookbacks).

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/security-advisory/advisory`.
• **TA input name:** **securityadvisory**; sourcetype `cisco:dnac:securityadvisory`.
• **Default interval:** **3600 seconds (1 hour)**—PSIRT data changes on **vendor** cadence, not per-second; avoid **sub-hour** polling without a strong reason (API and rate limits).
• **Key fields:** `advisoryId`, `severity` (**CRITICAL**, **HIGH**, **MEDIUM**, **LOW**, **INFORMATIONAL**), `cveId`, `deviceCount`, **`advisoryTitle`**, and commonly **`fixedVersions`** / affected versions in the payload (confirm in one **raw** event).

Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats count as advisory_count dc(advisoryId) as unique_advisories by severity | sort -severity
```

Understanding this SPL
• **`by severity`** gives a **portfolio view**; add **`| stats values(advisoryId) values(advisoryTitle)`** in a **drilldown** or **separate** table for **exec** vs **engineer** views.
• **`dc(advisoryId)`** approximates **breadth of distinct advisories**; raw **`count`** can be high if the TA **re-emits** the same advisory per **device**—interpret **KPIs** in context of your **ingest** pattern.

**Pipeline walkthrough**
• Scopes the **PSIRT** feed; **aggregates** by **severity** and **sorts** so **CRITICAL** surfaces first for **SOC** and **network** triage.

Step 3 — Validate (PSIRT-specific)
• **Open Catalyst Center** (or the **Cisco** advisory tool linked from the product) and **compare the list of `advisoryId` / `cveId` and affected device counts** to what Splunk shows for the same **sweep** (allow **one** poll difference).
• Spot-check a **HIGH** or **CRITICAL** row: confirm **`advisoryTitle`** and **`deviceCount`** look plausible versus **Catalyst** inventory (empty **deviceCount** may mean “not yet evaluated” for that advisory—verify in the UI, not in Splunk alone).
• **`| timechart count`** to verify **regular** ingest (a **flatline** of several days is a **TA** or **API** problem).

Step 4 — Operationalize
• **Dashboard:** **bar** by **severity**, **drilldown** to **`advisoryId`**, and a **table** of **`advisoryTitle` + `deviceCount` + `cveId`** for **remediation** owners.
• **Alerting (optional):** new **`CRITICAL`** advisories with **`deviceCount` > 0** in **your** **managed** set—tune to avoid **noise** on **informational** advisories with **zero** in-scope impact.
• **GRC:** export **monthly** snapshot for **RA-5** / **SI-2** evidence; link to **change tickets** for **fixed** versions.

Step 5 — Troubleshooting (PSIRT)
• **Empty or stale feed:** re-enable **securityadvisory** input, re-check **token** and **Catalyst** **cloud/on-prem** **URL**; review **`splunkd.log`** for **REST** errors.
• **Mismatch vs Cisco Security Portal:** your **Catalyst** build may **lag** the **public** portal by a **release**—**TAC** or **field notice** is the **authoritative** path for **exploitability** in **your** design.
• **Inflated `count`:** **dedup** on **`advisoryId`** + **`_time` bucket** if the TA **duplicates** rows per **poll**.
• **No `deviceCount`:** some advisories are **informational** until **Catalyst** maps **affected** platforms—**do not** assume **zero** risk without **Catalyst** confirmation.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats count as advisory_count dc(advisoryId) as unique_advisories by severity | sort -severity
```

## Visualization

Bar chart (advisory_count by severity), table of unique advisories, drilldowns to advisoryId.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
