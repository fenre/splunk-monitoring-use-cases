---
id: "5.13.45"
title: "Audit Log Activity Overview"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.45 · Audit Log Activity Overview

## Description

Provides an overview of all administrative activity logged by Catalyst Center, categorized by action type and description.

## Value

Audit logs are the foundation of accountability and change management. This overview establishes a baseline of normal administrative activity.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA calls `GET /dna/intent/api/v1/audit/logs` on a **300s** (5 minute) default interval. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (Splunkbase 7538); **audit_logs** into `index=catalyst`, sourcetype `cisco:dnac:audit:logs`.
• **Security** / **GRC** alignment: this feed is **management-plane** **accountability**—pair with **change** **tickets** and **MFA** reviews for the **Catalyst** **admin** **accounts**.
• **Retention** and **immutability** (where required): forward to a **WORM** or **locked** **index** if your **regulator** demands **append-only** **audit** **stores**.
• `docs/implementation-guide.md` for **TA** **install**, **credentials**, and **index** **routing** for **sensitive** **platform** **logs**.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/audit/logs` (paginated; **TA** may **iterate**—confirm **in** the **add-on** **release** **notes**).
• **TA input name:** **audit_logs**; sourcetype `cisco:dnac:audit:logs`.
• **Default interval:** **300 seconds (5 minutes)**—a reasonable **NOC**-grade **lag** for **admin** **activity** without **overwhelming** the **API**.
• **Key fields:** `auditRequestType`, `auditDescription`, `auditUserName`, **`auditTimestamp`**, `auditIpAddress` (names may **vary** slightly by **Catalyst** **build**—**fieldsummary** after **onboarding**).

Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | stats count by auditRequestType, auditDescription | sort -count | head 20
```

Understanding this SPL
• **Top-20** **summary** is a **baseline** **panel**; for **UEBA**-style **anomalies**, add a **rare** **alert** on **`auditUserName`** or **`auditIpAddress`** **outside** **corporate** **ranges** (via **lookup**).

**Pipeline walkthrough**
• Scopes **audit** **events**; **groups** by **type** and **description**; **surfaces** **most** **common** **admin** **patterns** first.

Step 3 — Validate (security)
• **Verify audit log `auditTimestamp` (or the mapped `_time` source) lines up with the Catalyst Center system clock and your organization’s NTP**—if **Splunk** **`_time`** is **off** by **hours**, **triage** **correlation** with **IdP** / **SIEM** will **mislead** **investigators**. Compare one **raw** event’s **`auditTimestamp`** to **Catalyst** **UI** **timestamps** for the same **row** and to **`date`** on the **Catalyst** **VMs** or **appliances** (see **Cisco** **Hardening** **guides** for **NTP**).
• **Spot-check** **high**-**risk** **verbs** in **`auditRequestType`** (e.g. **user** or **API** **token** **changes**) against **CAB** **records** for the **day**.

Step 4 — Operationalize
• **Dashboard:** **table** of **top** **types**; **drilldown** to a **secondary** **search** **filtered** by `auditRequestType` (or **token** **pass-through**) for **full** **history**; **retain** **12+** **months** if **SOX** / **NIST** **AU**-**family** **requires** **year-end** **replay**.
• **Correlate** with **Catalyst** **backup** and **upgrade** **windows**; **spikes** in **`auditDescription`** may be **expected** after **Cisco** **maintenance** **scripts**.

Step 5 — Troubleshooting
• **Gaps in `_time` chart:** **input** **disabled**, **Catalyst** **API** **errors**, or **search** **head** on a **dev** **index**—**verify** `inputs.conf` **stanza** and **`splunkd.log`** **HTTP** **codes**.
• **Missing** **`auditIpAddress`:** **Operator** is **on** a **jumphost**—still **valuable**; enrich with **lookup** to **AD** if **needed** (privacy **permitting**).
• **Flood of events:** an **automation** **account** may be **looping**; **throttle** **alerts** and **identify** **service** **principal** in **Catalyst** **RBAC**.
• **Time skew:** if **Catalyst** **is** **wrong** but **Splunk** is **right**, **fix** **Catalyst** **NTP** first—**do** **not** “fix” in **SPL** **alone** for **legal** **evidence** **chains**.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | stats count by auditRequestType, auditDescription | sort -count | head 20
```

## Visualization

Table (auditRequestType, auditDescription, count), bar chart of top request types, single value of total events in the window.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
