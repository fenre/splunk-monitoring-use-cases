---
id: "5.13.40"
title: "Client Inventory and Connection Summary"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.40 · Client Inventory and Connection Summary

## Description

Provides a complete inventory of all clients detected by Catalyst Center, summarized by host type and connection method.

## Value

Understanding your client population (count, types, connection methods) is foundational for capacity planning and security policy design.

## Implementation

Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA calls `GET /dna/intent/api/v1/client-detail` on a **3600s** (1 hour) default interval. Key fields: `macAddress`, `hostType`, `connectionType`, `ssid`, `vlanId`, `healthScore` (and `location` when present).

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (Splunkbase 7538); **client** feed into `index=catalyst`, sourcetype `cisco:dnac:client`.
• Catalyst **Assurance** / client visibility licensed where your organization relies on **Client 360**-style data; **API** user with read access to **client detail** in your **Intent** **RBAC** model.
• **PII** / **data-classification** review: **MAC addresses** and **hostnames** may be sensitive—restrict **index** **ACLs** and **dashboard** audiences per policy.
• `docs/implementation-guide.md` for modular input **interval**, **scope** (global vs site), and **proxy** settings.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/client-detail` (client inventory and health detail as implemented in your **Catalyst** and **TA** version).
• **TA input name:** **client**; sourcetype `cisco:dnac:client`.
• **Default interval:** **3600 seconds (1 hour)**—larger sites may need **tuning**; shorter intervals **increase** **API** load; align with how often **NOC** expects **roaming** updates.
• **Key fields:** **`macAddress`**, **`hostType`**, **`connectionType`**, **`ssid`**, **`vlanId`**, **`healthScore`** (plus **`location`** or site fields if your **TA** enriches them).

Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:client" | stats dc(macAddress) as unique_clients count as total_records latest(connectionType) as connection_type by hostType | sort -unique_clients
```

Understanding this SPL
• **`dc(macAddress)`** counts **distinct** clients by **`hostType`**—if one **MAC** appears as **multiple** **record types** per poll, validate **dedup** rules with a **`values(macAddress)`** sample.
• **`latest(connectionType)`** is a **simplification** for a **summary** table; for **per-SSID** cut, pivot with **`by ssid`** in a **separate** panel (see **UC-5.13.12** for health-by-segment context).

**Pipeline walkthrough**
• Scopes the **client** feed; **aggregates** by **host** category for **capacity** and **security** “what is on my network” views.

Step 3 — Validate
• Compare **rough order-of-magnitude** **unique** **Wi-Fi** vs **wired** clients to **Catalyst > Clients** for the same **time** (not byte-for-byte—**Catalyst** may **de-duplicate** differently than this **1h** **Splunk** **window**).
• **Spot-check** a few **MACs** in **Catalyst** **Client 360** and confirm **`hostType`**, **`ssid`**, **`vlanId`** look consistent with **one** **raw** **Splunk** event.

Step 4 — Operationalize
• **Dashboard:** **table** of **hostType** with **unique_clients**; **single value** for **sum(unique_clients)** in a **subsearch** or **post-process**; optional **export** to **CMDB** **sync** (batch only—do not **reverse**-sync **PII** without **governance**).
• **Not** a real-time **location** system—**Assurance** **and** **Splunk** **latency** apply; use for **trends**, not **sub-minute** **tracking**.

Step 5 — Troubleshooting
• **Zero events:** **client** **input** disabled, **wrong** **index**, or **API** **403**—check **TA** **logs** and **Catalyst** **roles**.
• **Counts** **too** **high** vs **UI**:** **duplicates** per **poll**—add a `dedup macAddress` (or equivalent) before `stats` if your **TA** emits multiple rows per **MAC** per poll.
• **Missing** **SSID**/**VLAN**:** some **Wired** clients will **naturally** **lack** them—**filter** `connectionType` in **SPL** for **wireless**-only **panels**.
• **PII** **escalation:** if **hostnames** appear in **raw** **JSON** but **should not** be **searched** broadly, **mask** in **ingest** or use **field-level** **restrictions** in **roles**.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" | stats dc(macAddress) as unique_clients count as total_records latest(connectionType) as connection_type by hostType | sort -unique_clients
```

## Visualization

Table (host type, count, connection type), Pie chart (client types), Single value (total clients).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
