<!-- AUTO-GENERATED from UC-5.13.35.json — DO NOT EDIT -->

---
id: "5.13.35"
title: "Critical/High PSIRT Alerting"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.35 · Critical/High PSIRT Alerting

## Description

Alerts on critical and high severity PSIRTs affecting managed devices, with the count of affected devices and associated CVEs.

## Value

Critical and high PSIRTs require immediate remediation. Alerting with affected device counts helps prioritize patching based on blast radius.

## Implementation

Enable the `securityadvisory` input. Use as a scheduled alert with low latency for CRITICAL, and include advisoryTitle and cves in the payload for analysts.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with **securityadvisory** input → `cisco:dnac:securityadvisory` in `index=catalyst`.
• `GET /dna/intent/api/v1/security-advisory/advisory` (Catalyst/TA default ~**3600s** poll); confirm **Catalyst** and **Cisco** PSIRT are enabled for your account.
• Run `fieldsummary` on `deviceId` vs `deviceName`—this SPL uses `deviceId`; if your build only has names, change the `dc()` field accordingly.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Configure data collection
• **Security Advisory** data is **Catalyst**-scoped to **managed** inventory; it does not replace org-wide **Qualys/Defender** coverage.
• **Default interval:** one hour is typical; sub-hour often adds API load for little gain unless you have an emergency bridge.

Step 2 — Create the search and **alert** (high priority)
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH") | stats dc(deviceId) as affected_devices values(cveId) as cves latest(advisoryId) as advisory by severity, advisoryTitle | sort severity -affected_devices
```

Understanding this SPL (blast radius, not a CVSS calculator)
**Critical/High PSIRT** — Triage list for **VulnMgmt**; combine with your **CAB** and **EOL** data before mandatory reboots in change freeze.
• `sort severity -affected_devices` is a **heuristic**; **Cisco** may sort **severity** lexicographically in some UIs—verify **CRITICAL** > **HIGH** in your `sort` if you need strict ordering (sometimes use **eval** of numeric rank).

**Pipeline walkthrough**
• High/Critical only → per **`severity, advisoryTitle`** → **dc(deviceId)** and **values(cveId)** for ticket body.

Step 3 — Validate
• Open **Catalyst** (or the linked **Cisco** advisory) for one row: **`deviceCount` / affected list** and **CVEs** should align within one **poll**.
• In Splunk, check whether multiple rows per `advisoryId` exist; if so, the **count** of raw events is **not** the same as **`dc(deviceId)`**—this is expected.

Step 4 — Operationalize (alerting)
• **Schedule** every **hour** (or 15m during active PSIRT) with time range **Last 2h** to survive clock skew. **Throttle** to **1 ticket per `advisoryId` per 24h** with **separate** zero-results **recovery** in ITSM (optional).
• **Enrich** with a **CMDB** lookup: filter `deviceId` to **prod**; send **P1** if **>0** **prod** and **0** test.

Step 5 — Troubleshooting
• **Fires on empty inventory:** `deviceId` may be null for some **informational** advisories—tighten `| where isnotnull(deviceId) AND affected_devices>0` if needed.
• **Stuck old advisories:** `latest(advisoryId)` in this SPL is a **per-group** field—pair with a **Catalyst** **fixed** version field in a **v2** panel for **true** closure status.
• **401/403 on collection:** re-check the **Catalyst** **API** **role** and **token**; review **Add-on** **logs** on the inputs host.
• **Catalyst lags cisco.com:** treat **Cisco TAC/PSIRT** as final on **exploit** status when the portal and **Catalyst** differ.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH") | stats dc(deviceId) as affected_devices values(cveId) as cves latest(advisoryId) as advisory by severity, advisoryTitle | sort severity -affected_devices
```

## Visualization

Table (affected_devices, cves, advisory by severity and title), top-N list for P1 remediation.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
