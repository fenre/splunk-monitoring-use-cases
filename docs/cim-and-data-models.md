# CIM, Data Model Acceleration, and OCSF

Use cases in this repo often reference **Splunk Common Information Model (CIM)** and **Data Model Acceleration (DMA)**. Some newer content may also align with **OCSF** (Open Cybersecurity Schema Framework). This page explains what they are and how they fit the use cases.

---

## Splunk CIM (Common Information Model)

The [Splunk CIM](https://docs.splunk.com/Documentation/CIM/latest/User/Overview) is a shared data model that normalizes field names and event types across different data sources. Use cases that list **CIM Models** (e.g. `Performance`, `Network_Traffic`, `Change`, `Authentication`) expect data to be normalized into those models so that:

- **tstats** and **datamodel** searches can run against a consistent schema.
- Dashboards and alerts work across multiple TAs and sourcetypes.
- You can swap data sources without rewriting searches.

**Where it’s used in use cases**

- **CIM Models:** Comma-separated list of data model names (e.g. `Performance`, `Web`, `Intrusion_Detection`). These are the CIM data models the use case’s SPL or tstats query relies on.
- **CIM SPL:** The `tstats` or `from datamodel=...` query that runs on the accelerated data model. It only works if the corresponding data model is populated and, for good performance, **accelerated**.

**Useful links**

- [CIM Overview](https://docs.splunk.com/Documentation/CIM/latest/User/Overview)
- [CIM Data Models list](https://docs.splunk.com/Documentation/CIM/latest/User/ListOfDataModels) (Performance, Web, Change, Authentication, etc.)
- [Configure TAs for CIM](https://docs.splunk.com/Documentation/CIM/latest/User/ConfigureTAs) so your data is mapped into the right models.

---

## Data Model Acceleration (DMA)

**Data Model Acceleration** pre-indexes data model datasets so that **tstats** and **datamodel** searches run quickly over large time ranges instead of scanning raw events.

- Use cases that include **CIM SPL** (tstats / `from datamodel=...`) assume the listed **CIM models** are **accelerated** in your environment.
- If acceleration is not enabled for a model, the tstats query may be slow or may not return data until the model is built and accelerated.

**What to do**

1. In Splunk Web: **Settings → Data models**, open the data model (e.g. Performance, Network_Traffic).
2. Enable **Acceleration** and set the **Summary Range** (e.g. 30 days) and, if needed, **Acceleration Summary Range**.
3. Ensure the underlying data is CIM-compliant (correct TA and tag/stanza mappings).

**Useful links**

- [Accelerate data models](https://docs.splunk.com/Documentation/Splunk/latest/Knowledge/Acceleratedatamodels)
- [Data model acceleration and summary range](https://docs.splunk.com/Documentation/Splunk/latest/Knowledge/Aboutdatamodelacceleration)

When a use case lists **CIM Models** and has **CIM SPL**, treat “enable Data Model Acceleration for the listed model(s)” as part of the implementation.

---

## OCSF (Open Cybersecurity Schema Framework)

[OCSF](https://schema.ocsf.io/) is an open schema for security and telemetry events. Vendors and platforms are increasingly aligning to OCSF; Splunk can ingest and search OCSF-shaped data.

- Use cases that support or prefer **OCSF** may list an **OCSF category/class** (e.g. `Authentication`, `Network Activity`) in addition to or instead of CIM.
- **Schema** in a use case can be set to **CIM**, **OCSF**, or both (e.g. “CIM (Performance); OCSF: process”). This helps you see whether the use case is written for the classic CIM/tstats path, an OCSF path, or both.

For OCSF-only or OCSF-first use cases, implementation will rely on OCSF-normalized data and possibly different field names than CIM; the use case description and SPL should reflect that.

---

## Summary

| Concept | Role in use cases |
|--------|---------------------|
| **CIM Models** | Data model names the use case depends on (e.g. Performance, Change). |
| **CIM SPL** | tstats/datamodel query; requires CIM-compliant data and, for performance, **DMA** on those models. |
| **Data model acceleration** | Enable for each CIM model used by tstats so the use case runs efficiently. |
| **Schema / OCSF** | Optional; indicates CIM, OCSF, or both when the use case aligns with OCSF. |

When implementing a use case that has **CIM Models** and **CIM SPL**, enable Data Model Acceleration for the listed model(s) and ensure data is mapped into those models via the appropriate Splunk TAs or CIM configuration.

---

## Preferred CIM-style field names (raw / index searches)

For **index-time SPL** examples (outside `tstats` / `from datamodel`), this catalog prefers names that align with **CIM-normalized** fields so searches port more easily to data models and ES:

| Prefer (CIM-aligned) | Often seen in vendor raw logs | Notes |
|---------------------|-------------------------------|--------|
| `src` | `src_ip`, `source_ip`, some `client_ip` | Source address (host or IP). |
| `dest` | `dest_ip`, `dst_ip`, some `server_ip` | Destination address. |
| `user` | `user_name`, `username` | Use `eval user=coalesce(user, user_name)` when both may appear. |
| `dest_port`, `src_port` | `remote_port`, etc. | Rename or coalesce when mapping vendor fields. |

Vendor-specific paths (e.g. `connection.src_ip` in JSON) are often **`eval`/`rename`d** to `src`/`dest` in the SPL block. **Data model** paths in `tstats` use dataset prefixes, e.g. `All_Traffic.src`, `All_Traffic.dest` (not `*_ip`).

The helper script `scripts/normalize_cim_fields.py` can re-apply bulk `src_ip`/`dest_ip` → `src`/`dest` renames on `use-cases/cat-*.md` when needed; always review **BY** clauses for duplicate `All_Traffic.dest` lines after replacing `dest_ip`.
