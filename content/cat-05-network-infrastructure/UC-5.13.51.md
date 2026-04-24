---
id: "5.13.51"
title: "Site Hierarchy Inventory"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.51 · Site Hierarchy Inventory

## Description

Provides a complete inventory of the Catalyst Center site hierarchy (areas, buildings, floors) for infrastructure documentation and capacity planning.

## Value

Understanding the site hierarchy is foundational for location-based analytics. This inventory ensures Splunk has a complete map of the physical infrastructure.

## Implementation

Enable the `site_topology` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA calls `GET /dna/intent/api/v1/topology/site-topology` on a **3600s** (1 hour) default interval. Key fields: `siteId`, `siteType`, `siteName`, `parentSiteName`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (Splunkbase 7538); **site topology** in `index=catalyst`, sourcetype `cisco:dnac:site:topology`.
• **Catalyst** **Design** / **NOC** owner who **maintains** the **hierarchy** in **Catalyst**—Splunk is a **read-only** **mirror**; **mismatches** are fixed in **Catalyst** first.
• **Process:** when you **onboard** new **buildings** or **renovations**, **refresh** the **topology** in **Catalyst** and **re-validate** this **search** the **same** **week**.
• `docs/implementation-guide.md` for **TA** **config** and **index** **routing**.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/topology/site-topology` (site **hierarchy**; **Catalyst** **version** may **namespace** the path—verify **in** the **API** **browser** of **your** **release**).
• **TA input name:** **site_topology**; sourcetype `cisco:dnac:site:topology`.
• **Default interval:** **3600 seconds (1 hour)**—**structure** **changes** are **rare**; do **not** over-poll **without** **reason**.
• **Key fields:** `siteId`, `siteType` (for example **area** / **building** / **floor**—values **depend** on **your** **design**), `siteName`, `parentSiteName`.

Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(siteId) as total_sites values(siteType) as types by parentSiteName | sort parentSiteName
```

Understanding this SPL
• **`parentSiteName` as the by-clause** gives a **parent** **rollup**; if **Catalyst** **nests** **multiple** **levels** **under** a **regional** **root**, you may need a **separate** **panel** **by** **`siteName`** for **leaves** only.
• **`values(siteType)`** is **for** **sanity** **checking**—it is **not** a **compliance** **count**; **one** **parent** can **host** many **child** **types**.

**Pipeline walkthrough**
• Scopes the **site** **feed**; **dedupes** **IDs** per **parent**; **orders** for **NOC** **naming** **comfort** with **Catalyst** **UI** **navigation**.

Step 3 — Validate
• **Open** **Catalyst** **>** **Network** **>** **Sites** and **compare** the **set** of **`siteName`** and **`parentSiteName`** to **rows** in **Splunk** for the **last** **poll**—allow **relabel** **lag** of **up** to **one** **hour**.
• If **`total_sites` == 0** for a **parent** you **expect**, **re-run** a **broad** **search** **`| stats count by siteName`** to **see** if **Catalyst** **moved** **sites** **under** a **new** **regional** **parent**.

Step 4 — Operationalize
• **Dashboard:** **indented** **table** of **rollups**; **export** a **CSV** to **Confluence** or the **CMDB** for **on-call** **runbooks** that **name** **sites** the **same** way as **Catalyst**.
• **Join** with **other** **UCs** (for example **device** or **AP** by **siteId** **when** **available**) using a **lookup** table **keyed** by **`siteId`**—**rebuild** the **lookup** on a **nightly** **schedule** when **topology** **changes** are **frequent**.

Step 5 — Troubleshooting
• **Empty** **index:** **site_topology** **input** **disabled** or **wrong** **Catalyst** **URL**—**check** **TA** **logs**.
• **Duplicate** **`siteId`:** **TA** or **Catalyst** **re-emitted** a **reparent**; **use** `| dedup siteId` before **stats** if **necessary**.
• **Extra** **parents** in **Splunk** not in **Catalyst**:** **old** **cache**; **bump** **TA** **or** **clear** the **input** **checkpoint** per **Cisco** **doc** (careful in **prod**—coordinate).
• **Orphaned** **sites** after **mergers:** a **Catalyst** **admin** must **reassign** **parents**; **Splunk** will **not** “fix” **governance** **errors** in **Catalyst** itself.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(siteId) as total_sites values(siteType) as types by parentSiteName | sort parentSiteName
```

## Visualization

Hierarchical or indented table (parentSiteName, total_sites, types), tree or Sankey if exported to a viz app, single value of global site count in a subsearch if needed.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
