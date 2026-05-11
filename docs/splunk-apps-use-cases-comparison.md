# Splunk Apps Use Cases — Comparison with This Repo

This document lists use cases from **Splunk IT Essentials Learn**, **IT Essentials Work**, **Content Packs for ITSI/ITE Work**, and related/legacy apps, then compares them to what is already in this repository.

---

## 1. Splunk IT Essentials Learn (ITE Learn)

- **Splunkbase<sup class="ref">[<a href="#ref-1">1</a>]</sup>:** [IT Essentials Learn](https://splunkbase.splunk.com/app/5390/) (app 5390)
- **Docs:** [Investigate procedures](https://docs.splunk.com/Documentation/ITELearn/1.1.8/User/Use), [Overview](https://docs.splunk.com/Documentation/ITELearn/1.1.8/ReleaseNotes/Overview)
- **Content:** Free app with **60+ procedures** (pre-built SPL searches). Each procedure has demo + live data, SPL explanations, and implementation guidance. Procedures are grouped by **use case** and **IT Maturity Journey** stage (Descriptive, Diagnostic, Predictive, Prescriptive).

### Use case categories in ITE Learn (from docs)

| Category | Subcategories / Data sources |
|----------|------------------------------|
| **Application** | Web Servers, Application |
| **Cloud Infrastructure** | VMware, GCP, Azure, AWS |
| **Database** | Database Wire Data |
| **Network** | Routers and Switches, Firewall |
| **Server and OS** | Windows, Unix and Linux |
| **Storage** | Isilon |

**Note:** The **exact procedure names** (e.g. “Track successful logins to a server”) are **not** published in the docs; they exist only inside the app UI. To get a full list you would need to install the app and export or scrape the Investigate tab (e.g. from the app’s default config or REST).

---

## 2. Splunk IT Essentials Work (ITE Work)

- **Splunkbase:** [IT Essentials Work](https://splunkbase.splunk.com/app/5403/) (app 5403)
- **Docs:** [Overview of entity types](https://help.splunk.com/en/splunk-it-service-intelligence/splunk-it-essentials-work/discover-and-integrate-it-components/4.21/entity-types/overview-of-entity-types-in-ite-work)

ITE Work is **entity-centric**: it provides **entity types**, **vital metrics**, **analysis data filters**, and **navigations** (dashboards). Each entity type effectively represents a “use case” for monitoring that kind of asset.

### Entity types and vital metrics (from docs)

| Entity type | Analysis data filters (examples) | Vital metrics (examples) | Navigation / dashboard |
|-------------|----------------------------------|---------------------------|------------------------|
| ***nix** | *nix logs, System metrics | Avg Network Traffic, Avg Available Disk, Avg Free Memory, **Avg CPU Usage** | *nix Overview Dashboard |
| **Unix/Linux Add-on** | *nix-TA logs, System metrics | Same as *nix | Unix and Linux Add-on Overview Dashboard |
| **Windows** | Windows logs, System metrics | Avg Network Traffic, Avg Available Disk, Avg Free Memory, **Avg CPU Usage** | Windows Overview Dashboard |
| **Kubernetes Node** | K8s Node metadata/logs/metrics | Avg Network Traffic, Avg Available Disk, Avg Free Memory, **Avg CPU Usage** | N/A |
| **Kubernetes Pod** | K8s Pod metadata/logs/metrics | Avg Network Traffic, Avg Free Memory, **Avg CPU Usage** | N/A |
| **VMware Cluster** | VMware Cluster Events/Inventory logs, Cluster metrics | Triggered Alarms, Hosts Down, Avg Effective Memory, **Avg CPU Usage** | VMware Cluster Overview Dashboard |
| **VMware Datastore** | VMware Datastore Events/logs, VM/ESXi Datastore metrics | Avg Datastore Write/Read Latency, Datastore Overprovisioned, **Avg Datastore Usage** | VMware Datastore Overview Dashboard |
| **VMware ESXi Host** | VMware ESXi/Events/Tasks/Inventory logs, ESXi metrics | Avg Network Traffic, Avg Datastore Latency, Avg Memory Usage, **Avg CPU Usage** | VMware ESXi Overview Dashboard |
| **VMware vCenter** | vCenter/Tasks/Events/Inventory logs, vCenter metrics | VCSA Failures, Avg Virtual/Physical Memory Usage, **Avg CPU Usage** | VMware vCenter Overview Dashboard |
| **VMware VM** | VMware Tasks/Inventory logs, VM metrics | Avg Network Usage, Avg Datastore Latency, Avg Memory Usage, **Avg CPU Usage** | VMware VM Overview Dashboard |

Docs also mention **AWS** and **Microsoft Azure** entity types with overview dashboards; the default config file is `itsi_entity_type.conf` in `SA-ITOA`.

---

## 3. Content Packs for ITSI and IT Essentials Work

From [Available content packs](https://help.splunk.com/en/splunk-it-service-intelligence/content-packs/1.9/overview/available-content-packs) (App for Content Packs 1.9):

| Content pack | Description | Supported apps |
|---------------|--------------|----------------|
| Content Pack for **Amazon Web Services** Dashboards and Reports | Monitor health/availability of AWS | ITSI, ITE Work |
| Content Pack for **Example Glass Tables** | Example glass table use cases | ITSI |
| Content Pack for **ITE Work Alert Routing** | External actions (e.g. email) on ITE Work alerts | ITE Work |
| Content Pack for **ITSI Monitoring and Alerting** | Enterprise-wide alerting blueprint | ITSI |
| Content Pack for **Microsoft 365** | Monitor M365 health/availability | ITSI, ITE Work |
| Content Pack for **Microsoft Exchange** | Monitor Exchange health/availability | ITSI, ITE Work |
| Content Pack for **Monitoring Citrix** | Monitor Citrix virtual apps/desktop | ITSI |
| Content Pack for **Monitoring Microsoft Windows** | OS-level Windows server health | ITSI |
| Content Pack for **Monitoring Pivotal Cloud Foundry** | Monitor PCF deployment | ITSI |
| Content Pack for **Monitoring Splunk as a Service** | OS and app-level Splunk monitoring | ITSI |
| Content Pack for **Monitoring Unix and Linux** | OS-level Linux/Unix health | ITSI |
| Content Pack for **NetApp Data ONTAP** Dashboards and Reports | Monitor NetApp health/availability | ITSI, ITE Work |
| Content Pack for **ServiceNow** | Monitor ServiceNow instances | ITSI, ITE Work |
| Content Pack for **Shared IT Infrastructure Components** | Map service dependencies in ITSI | ITSI |
| Content Pack for **SOAR System Logs** | Monitor SOAR server health | ITSI |
| Content Pack for **Splunk Observability Cloud** | Bridge ITSI with Synthetic/IM/APM | ITSI, ITE Work |
| Content Pack for **Splunk Synthetic Monitoring** | Synthetic monitoring use cases | ITSI, ITE Work |
| Content Pack for **Third-Party APM** | AppDynamics, DynaTrace, New Relic | ITSI, ITE Work |
| Content Pack for **Unix** Dashboards and Reports | Reports, alerts, dashboards for Linux/Unix | ITSI, ITE Work |
| Content Pack for **VMware** Dashboards and Reports | Virtual environment health/availability | ITSI, ITE Work |
| Content Pack for **VMware Monitoring** | vSphere main components performance | ITSI |
| Content Pack for **Windows** Dashboards and Reports | Windows Server & Active Directory visibility | ITSI, ITE Work |

**Content Pack for Windows** includes many dashboards, for example: Windows Overview, Event Monitoring, Performance Monitoring, Application Crashes, Application Installs, Windows Update, Hosts Overview, Host Inventory, Disk Information, Processes, Services, Network Activity, Printers, Domain Health/Replication/Directory Performance, DC/DNS Status, User/Computer/Group/Group Policy Audit, etc. (See [Dashboard reference](https://docs.splunk.com/Documentation/CPWindowsDash/latest/CP/DashboardReference).)

---

## 4. Other / legacy Splunk apps with use cases

- **Splunk Security Essentials (SSE)** — Already imported into this repo (cat-10); 1,991 ESCU detections redistributed into 10.1–10.8.
- **Splunk App for Unix and Linux** (EOL) / **Splunk Add-on for Unix and Linux** — Dashboards and reports; covered conceptually by cat-01 (Server & Compute) and Content Pack for Unix.
- **Splunk App for Windows Infrastructure** (EOL) — Replaced by Content Pack for Windows Dashboards and Reports; covered by cat-01 and cat-09 (Identity).
- **Splunk App for VMware** (EOL) / **Splunk Add-on for VMware** — Covered by cat-02 (Virtualization) and VMware Content Packs.
- **Splunk App for AWS** (EOL) — Replaced by Content Pack for AWS; covered by cat-04 (Cloud).
- **Splunk App for Infrastructure** (EOL) — Generic infra; covered by cat-01, 02, 04, etc.
- **Use Case Explorer** (archived) — Folded into Insight Suite; investigative use cases.
- **Utilization Monitor for Splunk (SUM)** (archived) — License/utilization; related to cat-20 / cat-13.

---

## 5. Comparison with this repository

### 5.1 Repo structure (summary)

This repo has **23 categories** (cat-01 … cat-23) with **6,400+ use cases** after build (including ESCU in cat-10). Non-ESCU use cases live in cat-01–09, 11–23; ESCU is in cat-10.

| Repo category | Covers (examples) |
|---------------|--------------------|
| 1 Server & Compute | Linux, Windows, OS metrics, security events |
| 2 Virtualization | VMware, Hyper-V, KVM |
| 3 Containers & Orchestration | Docker, Kubernetes |
| 4 Cloud Infrastructure | AWS, Azure, GCP |
| 5 Network Infrastructure | Routers, switches, firewalls, load balancers |
| 6 Storage & Backup | SAN/NAS, object storage, backup |
| 7 Database & Data Platforms | SQL, NoSQL, replication |
| 8 Application Infrastructure | Web servers, app servers, message queues |
| 9 Identity & Access Management | AD, LDAP, MFA, PAM |
| 10 Security Infrastructure | NGFW, IDS/IPS, EDR, email security, ESCU |
| 11 Email & Collaboration | M365, Exchange, Teams |
| 12 DevOps & CI/CD | Source control, pipelines, artifacts |
| 13 Observability & Monitoring Stack | Splunk health, ITSI |
| 14 IoT & OT | OT, industrial |
| 15 Data Center Physical Infrastructure | Power, cooling, physical security |
| 16 Service Management & ITSM | ServiceNow, incident/change management |
| 17 Network Security & Zero Trust | NAC, VPN, device posture |
| 18 Data Center Fabric & SDN | Cisco ACI, VMware NSX |
| 19 Compute Infrastructure (HCI & Converged) | Nutanix, UCS, blade chassis |
| 20 Cost & Capacity Management | Cloud cost, rightsizing, forecasting |
| 21 Industry Verticals | Energy, manufacturing, healthcare, telecom |
| 22 Regulatory & Compliance Frameworks | GDPR<sup class="ref">[<a href="#ref-3">3</a>]</sup>, NIS2<sup class="ref">[<a href="#ref-2">2</a>]</sup>, DORA<sup class="ref">[<a href="#ref-4">4</a>]</sup>, ISO 27001, NIST CSF |
| 23 Business Analytics & Executive Intelligence | Executive dashboards, KPI tracking, data quality |

### 5.2 IT Essentials Learn vs repo

- **Application (Web Servers, Application):** Repo has cat-08 (Web Servers & Reverse Proxies, Application Servers, Message Queues). **Largely covered**; ITE Learn may add more procedure-level variety (e.g. Apache vs IIS vs generic).
- **Cloud (VMware, GCP, Azure, AWS):** Repo has cat-02 (VMware, Hyper-V), cat-04 (AWS, Azure, GCP). **Covered** at category level; ITE Learn’s 60+ procedures are a subset of possible SPL patterns.
- **Database (Database Wire Data):** Repo has cat-07 (Database & Data Platforms). “Database Wire Data” may imply wire-capture or DB audit; if so, consider adding a **database wire/audit** subcategory or use case under cat-07 if you want explicit parity.
- **Network (Routers and Switches, Firewall):** Repo has cat-05 (Routers & Switches, Firewalls, etc.). **Covered.**
- **Server and OS (Windows, Unix and Linux):** Repo has cat-01 (Server & Compute). **Covered.**
- **Storage (Isilon):** Repo has cat-06 (SAN/NAS, object, backup) but **no Isilon-specific** use case. **Gap:** add an **Isilon** use case (or subcategory) under Storage if you want parity with ITE Learn.

### 5.3 IT Essentials Work vs repo

- Entity types (*nix, Windows, Kubernetes Node/Pod, VMware Cluster/Datastore/ESXi/vCenter/VM) map to **cat-01** (Server), **cat-03** (Kubernetes), **cat-02** (VMware). Vital metrics (CPU, memory, disk, network, datastore usage, etc.) are already reflected in existing server/virtualization/container use cases. **No structural gap**; ITE Work is a different packaging (entity + dashboard) of similar monitoring ideas.

### 5.4 Content Packs vs repo

- **AWS, Windows, Unix/Linux, VMware, Exchange, NetApp:** Covered by cat-04, cat-01, cat-02, cat-11, cat-06.
- **Microsoft 365:** Cat-11 (Email & Collaboration).
- **Citrix:** Not a dedicated category; could add **Citrix** under cat-08 (Application) or cat-02 (virtual apps) if you want explicit coverage.
- **Pivotal Cloud Foundry (PCF):** Not present; **gap** if you care about PCF (add under cat-04 or a “PaaS” area).
- **Monitoring Splunk as a Service, SOAR System Logs:** Cat-13 (Observability), cat-10 (SOAR).
- **ServiceNow, ITSI Monitoring and Alerting, Synthetic, Observability Cloud, Third-Party APM:** Partially or fully covered by cat-13, cat-16 (ITSM), cat-08/13 (synthetic/APM). Optional: explicit **Synthetic monitoring** and **third-party APM** use cases under cat-13.
- **ITE Work Alert Routing:** Operational/config, not a “use case” in the same sense; no gap.

### 5.5 Gaps and recommendations

| Source | What’s missing in repo | Recommendation |
|--------|------------------------|----------------|
| **ITE Learn** | **Isilon** storage procedures | Add one or more **Isilon** use cases under cat-06 (Storage), e.g. “Isilon cluster/node health”, “Isilon capacity/performance”. |
| **ITE Learn** | Exact 60+ procedure titles | Install ITE Learn app and export procedure list from the UI or app config to do a name-level comparison. |
| **Content Packs** | **Citrix** (virtual apps/desktop) | Optionally add subcategory or use cases for **Citrix** under cat-08 or cat-02. |
| **Content Packs** | **Pivotal Cloud Foundry (PCF)** | If relevant, add a small **PCF** section under cat-04 (Cloud) or a “PaaS” subsection. |
| **Content Packs** | **Synthetic monitoring** | Optionally add explicit “Synthetic monitoring” use cases under cat-13. |
| **Content Packs** | **Third-party APM** (AppDynamics, DynaTrace, New Relic) | Optionally add “Third-party APM health” under cat-13. |

---

## 6. How to get a full procedure list from IT Essentials Learn

The public docs do **not** list the 60+ procedure names. To compare **by name** with this repo:

1. **Install the app** from [Splunkbase (app 5390)](https://splunkbase.splunk.com/app/5390/).
2. **Export or scrape** the procedure list, for example:
   - Use the **Investigate** tab in the app and capture procedure titles (and optionally use case + data source).
   - If the app stores procedures in config/lookups (e.g. `default/*.conf` or CSV/JSON in the app), extract procedure IDs and titles from there.
   - Optionally use the **My Progress** or **IT Maturity Journey** views to get a structured list.

Once you have a list (e.g. CSV: procedure_id, title, use_case, data_source), you can diff it against your repo’s use case titles (e.g. from `data.js` or from `grep '^### UC-' use-cases/cat-*.md`) to find exact matches and missing items.

A helper script was previously available at `use-cases/list_ite_learn_procedures.py` for scanning an unpacked IT Essentials Learn app directory; it has since been removed.

---

## 7. Companion app: Splunk UC Recommender

This repository ships a unified
**[Splunk UC Recommender](recommender-app.md)** app
(`splunk-uc-recommender`) that subsumes what used to be a family of
regulation-scoped compliance apps (CMMC, DORA, GDPR, HIPAA<sup class="ref">[<a href="#ref-14">14</a>]</sup>, ISO 27001,
NIS2, NIST 800-53, NIST CSF, PCI DSS, SOC 2, SOX<sup class="ref">[<a href="#ref-12">12</a>]</sup> ITGC).

Where IT Essentials / ITSI content packs / ESCU deliver a fixed
library of saved searches bound to a specific data source or
regulation, the recommender app solves the inverse problem: **"given
the data I already have in Splunk, which of the 7,364 use cases in
this catalogue are worth turning on?"** — *and* it still ships all
tier-1 compliance content for auditors in the same app.

Key differences vs. the other apps discussed above:

- It is **preview-only** for its recommender flow — it never writes
  new saved searches when you explore recommendations. It scans your
  inventory and shows a card grid with **Copy SPL** and **Open in
  Search app** for every match.
- It **bundles every tier-1 compliance UC** (GDPR, HIPAA, PCI-DSS,
  NIS2, ISO 27001, NIST CSF, NIST 800-53, DORA, CMMC, SOC 2, SOX
  ITGC) as **disabled, unscheduled** saved searches with a filterable
  Compliance view so a single install covers both "what could we
  monitor?" and "what do we need for audit evidence?".
- It covers the **full catalogue** (all 23 categories, 7,364 UCs)
  for recommendations, not just the compliance-tagged subset.
- It is **Splunk Cloud safe** — no custom commands, REST endpoints,
  scripted inputs, or web.conf exposures; all catalogue fetches
  happen in the browser against an allow-listed origin.

See the [full guide](recommender-app.md) for install, architecture,
scan cadence, the remote API contract, the bundled compliance
content, and the security model.

---

## 8. Summary

- **IT Essentials Learn:** 60+ procedures in 6 use case areas (Application, Cloud, Database, Network, Server/OS, Storage). Repo covers all areas except **Isilon**; procedure-level comparison needs the app’s procedure list.
- **IT Essentials Work:** 10+ entity types with dashboards and vital metrics; concepts are covered by cat-01, 02, 03.
- **Content Packs:** 20+ packs; most map to existing categories. Optional additions: **Isilon**, **Citrix**, **PCF**, **Synthetic monitoring**, **Third-party APM** if you want explicit parity.
- **Legacy apps:** Superseded by Content Packs and existing categories; no new use case gaps.

To close the main documented gap: add **Isilon** storage use case(s) under **cat-06 (Storage & Backup)**. For fine-grained alignment with ITE Learn, export the app’s procedure list and run a name-based diff against your repo.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Primary sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

### Supporting sources

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-5"></a>**[5]** Payment Card Industry Security Standards Council. (2018). *Payment Card Industry Data Security Standard v3.2.1* (v3.2.1). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-6"></a>**[6]** Payment Card Industry Security Standards Council. (2022). *Payment Card Industry Data Security Standard v4.0* (v4.0). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk AppInspect documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/

<a id="ref-8"></a>**[8]** Splunk Inc. (2026). *Splunk Cloud Platform App Vetting requirements*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud/latest/Service/SplunkCloudservice

<a id="ref-9"></a>**[9]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

<a id="ref-10"></a>**[10]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-11"></a>**[11]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-12"></a>**[12]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-13"></a>**[13]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-14"></a>**[14]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<details>
<summary>Additional online sources cited in the document body (7)</summary>

<a id="ref-15"></a>**[15]** splunkbase.splunk.com. *IT Essentials Learn*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/5390/

<a id="ref-16"></a>**[16]** docs.splunk.com. *Investigate procedures*. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITELearn/1.1.8/User/Use

<a id="ref-17"></a>**[17]** docs.splunk.com. *Overview*. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITELearn/1.1.8/ReleaseNotes/Overview

<a id="ref-18"></a>**[18]** splunkbase.splunk.com. *IT Essentials Work*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/5403/

<a id="ref-19"></a>**[19]** help.splunk.com. *Overview of entity types*. Retrieved May 11, 2026, from https://help.splunk.com/en/splunk-it-service-intelligence/splunk-it-essentials-work/discover-and-integrate-it-components/4.21/entity-types/overview-of-entity-types-in-ite-work

<a id="ref-20"></a>**[20]** help.splunk.com. *Available content packs*. Retrieved May 11, 2026, from https://help.splunk.com/en/splunk-it-service-intelligence/content-packs/1.9/overview/available-content-packs

<a id="ref-21"></a>**[21]** docs.splunk.com. *Dashboard reference*. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CPWindowsDash/latest/CP/DashboardReference

</details>

### Related repository documents

- [`docs/recommender-app.md`](recommender-app.md)

### Cited by

- [`README.md`](../README.md)

<!-- END-AUTOGENERATED-SOURCES -->
