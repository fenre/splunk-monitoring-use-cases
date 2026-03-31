# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Section headings (e.g. `### New Use Cases`) are rendered as-is in the release
notes popup. `build.py` auto-generates the HTML from this file — do not edit
the release notes block in `index.html` by hand.

---

## [5.5] - 2026-03-26

### UI — Subcategory Navigation & Source Catalog Updates

- **Subcategory landing page** &mdash; Clicking a category on the front page now shows an intermediate view of its subcategories as cards (with description, UC count, and criticality breakdown) instead of jumping straight to all use cases. A "Show all N use cases" button restores the previous full-list behaviour.
- **Hash routing** &mdash; `#cat-N` now opens the subcategory view; `#cat-N/X.Y` opens the full list scrolled to a specific subcategory.
- **Source catalog expanded** &mdash; Added OpenConfig gNMI specification, Telegraf gNMI plugin, Cisco Nexus gNMI white paper, Nokia gNMIc, Nozomi Networks Guardian docs, and Nozomi Universal Add-on (6905) + CCX Extensions (6796) to the Sources popup.

---

## [5.4] - 2026-03-26

### gNMI / gRPC Streaming Telemetry — New Section 5.11

- **11 new use cases** (UC-5.11.1 through UC-5.11.11) for model-driven streaming telemetry via gNMI/gRPC.
- **Multi-vendor** &mdash; Cisco IOS XR/NX-OS/IOS XE, Arista EOS, Juniper Junos, Nokia SR Linux all supported with OpenConfig YANG paths.
- **Telegraf → Splunk HEC pipeline** &mdash; All UCs use the documented Telegraf `inputs.gnmi` plugin with `splunkmetric` output to Splunk metrics indexes. SPL uses `mstats` and `rate_avg()`.
- **Use cases cover**: interface utilization at sub-minute granularity (5.11.1), interface error/discard streaming (5.11.2), BGP peer state ON_CHANGE detection (5.11.3), system CPU/memory (5.11.4), optical transceiver health with predictive failure alerting (5.11.5), QoS queue depth and microburst detection (5.11.6), LLDP topology change detection (5.11.7), BGP prefix churn and route leak detection (5.11.8), hardware environment monitoring (5.11.9), Telegraf collector pipeline health (5.11.10), and ACL hit counter analysis (5.11.11).

---

## [5.3] - 2026-03-26

### Nozomi Networks — Multi-Vendor OT Security

- **25 existing Cisco Cyber Vision UCs merged** to support both Cisco Cyber Vision and Nozomi Networks Guardian/Vantage as alternative data sources.
- **Section 14.9 renamed** from "Cisco Cyber Vision (OT Security)" to "OT Network Security Monitoring (Cisco Cyber Vision / Nozomi Networks)".
- **Dual SPL examples** &mdash; every UC now has both a Cisco Cyber Vision SPL block and a Nozomi Networks alternative SPL block with correct sourcetypes (`nozomi:nn_asset`, `nozomi:alert`, `nozomi:variable`, `nozomi:link`, `nozomi:session`, `nozomi:health`).
- **New Splunk apps registered** &mdash; Nozomi Networks Universal Add-on (Splunkbase 6905), CCX Extensions for Nozomi Networks (Splunkbase 6796), with archived Nozomi Networks Sensor Add-on (5316) as predecessor.
- **Value descriptions neutralized** &mdash; vendor-specific language replaced with vendor-agnostic descriptions throughout all 25 UCs.

---

## [4.3] - 2026-03-26

### My Environment Inventory

- **Customer inventory tool** &mdash; New "My Inventory" button in the footer opens a full-screen modal where users can check off all equipment and software in their environment. On apply, the catalog filters to show only use cases relevant to the selected items (OR logic across all checked equipment).
- **Organized checklist** &mdash; 80+ equipment items grouped into 15 logical categories (Servers & OS, Virtualization, Cloud & Containers, Networking, Databases, Security Tools, DevOps, Splunk Products, OT/IoT, and more) with collapsible sections, select-all per group, and a search filter.
- **Persistent selections** &mdash; Inventory choices are automatically saved to localStorage and restored on page load.
- **Export / Import** &mdash; Save your inventory as a JSON file for portability, or load a previously saved file to restore selections across browsers or machines.
- **Filter integration** &mdash; Active inventory appears as a clearable filter tag alongside existing filters. Composes with all other filters (criticality, difficulty, pillar, regulation, etc.) via AND logic.

---

## [5.0] - 2026-03-26

### Business Analytics & Executive Intelligence — New Category 23

Major release: **New category 23** with 38 use cases across 9 subcategories, bringing non-technical, business-aligned use cases into the catalog for the first time.

- **23.1 Customer Experience & Digital Analytics** (6 UCs) — Conversion funnels, cart abandonment, page load revenue impact, NPS tracking, cross-channel attribution, mobile app crash rates.
- **23.2 Revenue & Sales Operations** (5 UCs) — Pipeline velocity, revenue booking trends, churn prediction, renewal pipeline, pricing/discount effectiveness.
- **23.3 Marketing Performance & Attribution** (4 UCs) — Campaign ROI by channel, lead-to-revenue funnel, email engagement, SEO/traffic source analysis.
- **23.4 HR & People Analytics** (4 UCs) — Attrition analysis and flight risk, time-to-hire, diversity metrics, training compliance.
- **23.5 Supply Chain & Operations** (4 UCs) — Order-to-cash cycle time, inventory stockout risk, supplier OTIF, delivery SLA compliance.
- **23.6 Financial Operations & Procurement** (4 UCs) — AR aging/DSO, expense anomaly detection, budget vs actual variance, payment processing success.
- **23.7 Customer Support & Service Excellence** (3 UCs) — Ticket volume/SLA, first-contact resolution, customer effort scoring.
- **23.8 Executive Dashboards & Business KPIs** (3 UCs) — CEO/CFO scorecard, operational efficiency metrics, business risk heatmap.
- **23.9 ESG & Sustainability Reporting** (5 UCs) — Carbon footprint, energy efficiency, waste diversion, water conservation, ESG disclosure readiness.

These use cases are written for non-technical stakeholders (CFOs, CMOs, CHROs, COOs) and focus on business outcomes rather than technical mechanisms. All are implementable with Splunk using DB Connect, HEC, web access logs, and standard integrations.

Catalog now at 5,054 use cases across 23 categories.

---

## [5.2] - 2026-03-26

### Citrix — uberAgent & Expanded Data Center Coverage

- **uberAgent UXM integration (11 new UCs)** &mdash; UC-2.6.17 through UC-2.6.27: Experience Score monitoring, application unresponsiveness detection, application startup duration, browser performance per website, machine boot/shutdown analysis, per-application CPU/memory, crash reporting, Citrix Site delivery group capacity, NetScaler via uberAgent, per-application network performance, and endpoint security analytics (ESA) threat detection.
- **Existing UCs updated** &mdash; UC-2.6.1 (logon) and UC-2.6.2 (ICA RTT) now recommend uberAgent as the preferred data source alongside the existing XenDesktop 7 template and OData API.
- **New apps registered** &mdash; uberAgent UXM (Splunkbase 1448), Splunk Add-on for Citrix NetScaler (Splunkbase 2770). Citrix vendor expanded with CVAD, uberAgent, and NetScaler sub-models.

---

## [5.1] - 2026-03-26

### Cisco Data Center — Expanded Coverage

- **Cisco Intersight (7 new UCs)** &mdash; UC-19.1.19 through UC-19.1.25: server alarm monitoring, firmware compliance, HCL compliance, power/thermal telemetry, audit logs, contract/warranty tracking, and UCS X-Series IFM health. Leverages the Cisco Intersight Add-on for Splunk (Splunkbase 7828).
- **Cisco MDS SAN Fabric (6 new UCs)** &mdash; UC-6.1.27 through UC-6.1.32: ISL utilisation monitoring, slow drain detection, zone configuration compliance, FLOGI database monitoring, VSAN health/isolation events, and fabric oversubscription ratio. Expands MDS coverage from 1 UC to 7.
- **Nexus Dashboard & NX-OS Fabric (8 new UCs)** &mdash; New section 18.4 with UC-18.4.1 through UC-18.4.8: Nexus Dashboard Insights anomaly monitoring, NDFC fabric compliance/drift, advisory and field notice alerts, NX-OS streaming telemetry health, VXLAN EVPN underlay BGP, CoPP drops, NDO cross-fabric consistency, and NDFC switch lifecycle tracking.
- **New Splunk apps registered** &mdash; Cisco DC Networking Application (Splunkbase 7777) and Cisco Intersight Add-on (Splunkbase 7828) added to the app catalog. New Cisco sub-vendors: Intersight, Nexus/NDFC/MDS.

---

## [4.6] - 2026-03-26

### DORA — Full Digital Operational Resilience Coverage

- **15 new DORA use cases** (UC-22.3.6 through UC-22.3.20), expanding coverage from 5 to 20 dedicated UCs.
- **Art. 9 — Protection & Prevention**: ICT change management and patch compliance (Art. 9(4)(e)), access control and authentication monitoring (Art. 9(4)(c)).
- **Art. 10 — Detection**: ICT anomaly detection capability monitoring — proving detection infrastructure covers all critical functions.
- **Art. 11 — Response & Recovery**: MTTD/MTTR/RTO tracking for DORA-regulated services against defined targets.
- **Art. 12 — Backup**: backup completeness, restoration testing, and segregation validation for critical function systems.
- **Art. 13 — Learning & Evolving**: post-incident review completion, root cause tracking, and improvement action implementation.
- **Art. 14 — Communication**: crisis communication readiness — plan freshness, contact list currency, drill completion.
- **Art. 18 — 7-Criteria Classification**: automated major ICT incident classification against all DORA criteria (clients affected, geographic spread, duration, data loss).
- **Art. 19 — Three-Report Timeline**: tracking initial (4h), intermediate (72h), and final (1 month) report submission for major incidents.
- **Art. 25 — Testing Program**: vulnerability assessment and penetration test tracking with finding remediation SLAs.
- **Art. 26 — TLPT**: Threat-Led Penetration Testing lifecycle tracking including the three-year cycle requirement.
- **Art. 28(3) — Register of Information**: validation of ICT provider register completeness against actual network traffic.
- **Art. 28(8) — Exit Strategy**: exit plan readiness scoring for all critical/important function providers.
- **Art. 30 — SLA Monitoring**: actual ICT provider performance vs contractual availability and response time targets.
- **Art. 5 — Management Body Governance**: board ICT risk briefing, framework approval, training, and risk appetite evidence.
- DORA now has the most comprehensive coverage of any regulation in the catalog with 20 dedicated UCs.

---

## [4.5] - 2026-03-26

### GDPR — Comprehensive Article Coverage Expansion

- **14 new GDPR use cases** (UC-22.1.7 through UC-22.1.20), expanding coverage from 6 to 20 dedicated UCs.
- **Art. 32 — Security of Processing**: encryption and pseudonymisation coverage monitoring for personal data systems.
- **Art. 30 — Records of Processing Activities**: ROPA completeness validation against observed data flows.
- **Art. 25 — Data Protection by Design**: data minimisation validation detecting over-collection of PII.
- **Art. 5(1)(f) / Art. 32 — Integrity and Confidentiality**: privileged access monitoring for personal data stores (databases, file systems).
- **Art. 17 — Right to Erasure Verification**: post-deletion scanning to catch incomplete "right to be forgotten" execution.
- **Art. 33(3) — Breach Scope Quantification**: automated estimation of affected data subjects for 72h notification.
- **Art. 34 — Communication to Data Subjects**: tracking of high-risk breach individual notification workflows.
- **Art. 35 — DPIA Coverage**: monitoring that Data Protection Impact Assessments exist for high-risk processing.
- **Art. 28 — Processor Compliance**: continuous monitoring of data flows to third-party processors.
- **Art. 7(3) — Consent Withdrawal Enforcement**: verification that processing stops after consent is withdrawn.
- **Art. 5(2) — Audit Log Integrity**: tamper detection for the evidence trail used to prove GDPR compliance.
- **Art. 22 — Automated Decision-Making Transparency**: monitoring decision volumes, override rates, and appeal handling.
- **Art. 12 — Data Subject Rights SLA Dashboard**: executive view across all rights with SLA tracking.
- **Art. 6(1)(f) — Legitimate Interest Balancing**: LIA coverage and objection monitoring — the highest-fine enforcement area in 2025-2026.
- Catalog crosses **5,000 use cases** milestone with this release.

---

## [4.4] - 2026-03-26

### NIS2 Directive — Full Article 21 & Article 23 Coverage

- **15 new NIS2 use cases** (UC-22.2.6 through UC-22.2.20), expanding coverage from 5 to 20 dedicated UCs.
- Now covers **all 10 Article 21(2) measures**: (a) risk analysis & security policies, (b) incident handling, (c) business continuity & backup/DR, (d) supply chain security, (e) secure development lifecycle, (f) effectiveness assessment, (g) cyber hygiene & training, (h) cryptography & encryption, (i) access control, asset management & HR security, (j) MFA & secure communications.
- **Article 23 three-stage reporting** fully covered: 24h early warning (existing), 72h notification (new), one-month final report (new), cross-border impact assessment (new).
- **Article 20 management accountability**: governance evidence dashboard for board-level training, policy approval, and risk acceptance tracking.
- New use cases include: NIS2 effectiveness KPI dashboard, training compliance tracking, TLS/certificate health monitoring, JML process enforcement, CI/CD security gate coverage, supplier risk continuous monitoring, and backup/restore verification.
- Updated 22.2 Primary App/TA to include Okta, Stream, CyberArk, Qualys, Veeam, GitHub, and Jira add-ons.

---

## [4.3] - 2026-03-26

### Check Point Quantum Firewall & Security Expansion

- **8 new Check Point firewall UCs in cat-05** (UC-5.2.47 through UC-5.2.54): ClusterXL failover, policy install/publish tracking, SecureXL acceleration status, CoreXL CPU distribution, log rate and capacity, anti-spoofing violations, HTTPS inspection status and bypass, gateway connection table utilization.
- **10 new Check Point security UCs in cat-10** (UC-10.11.121 through UC-10.11.130): Zero Phishing detection, ThreatCloud IOC match rate, Quantum IoT Protect device discovery, Maestro Orchestrator health, CloudGuard Network security events, Threat Prevention policy layer effectiveness, admin session and login audit, DDoS Protector integration events, Infinity managed service events, HTTPS inspection certificate errors.
- Check Point coverage now totals **33 dedicated UCs** across cat-05, cat-10, and cat-17 — on par with Palo Alto and Fortinet.

---

## [4.2] - 2026-03-26

### Zero Trust / SASE Vendor Expansion

- **31 new zero-trust / SASE use cases** (UC-17.3.32 through UC-17.3.62) covering vendors missing from the catalog:
  - **Netskope** (7 UCs): Cloud app risk (CCI scoring), DLP violations, threat protection, SWG category blocking, Private Access (NPA) health, CASB inline enforcement, admin audit trail.
  - **Fortinet FortiSASE** (5 UCs): SWG policy violations, ZTNA tag-based access, threat detection (IPS/AV), thin edge tunnel health, admin configuration audit.
  - **Check Point Harmony SASE** (5 UCs): ThreatCloud prevention, Internet Access policy, Private Access (ZTNA) health, admin audit, DLP events.
  - **Akamai Guardicore** (4 UCs): Segmentation policy violations, Reveal map anomalies, agent health, incident investigation with deception triggers.
  - **Broadcom / Symantec SSE** (3 UCs): Cloud SWG policy analysis, CASB shadow IT detection, SWG threat events.
  - **Cloudflare Zero Trust** (3 UCs): Access (ZTNA) policy enforcement, Gateway DNS/HTTP filtering, Tunnel health.
  - **Forcepoint ONE** (2 UCs): SSE web security events, ZTNA private access health.
  - **SonicWall** (1 UC): Cloud SWG and SMA access events.
  - **Versa Networks** (1 UC): Unified SASE security and access events.
- **Existing vendor-neutral UCs updated:** 13 generic UCs (17.3.1–17.3.20) now list all relevant vendor TAs (Zscaler, Netskope, Prisma Access, FortiSASE, Check Point, Cloudflare, Akamai Guardicore, Broadcom Symantec, Forcepoint) where the use case concept applies across platforms.
- **New Splunkbase app integrations:** Added Netskope App (6042), Check Point App (4293), Cloudflare App (4501), Akamai Guardicore Add-on (7426), Forcepoint Insights SIEM App (8053), Netskope Add-on (3808), Symantec WSS Add-on (3856), SonicWall SMA 1000 TA (6670) to build.py for automatic Splunkbase linking.

---

## [4.1] - 2026-03-26

### Multi-Vendor TA Coverage & Archived App Display

- **Complete multi-vendor TA coverage:** Every use case that lists multiple equipment vendors in its Equipment Models field now includes all relevant Technology Add-ons in its App/TA field. Previously, many multi-vendor UCs only listed a single vendor's TA (e.g. only `TA-cisco_ios` despite listing Juniper, Arista, and HPE Aruba equipment). Updated 35+ router/switch UCs (5.1.x) to include `Splunk_TA_juniper`, `arista:eos` via SC4S, and HPE Aruba CX syslog alongside Cisco TAs. Updated 18 firewall UCs (5.2.x) to include `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, and `Splunk_TA_juniper` (SRX). Updated NAC UCs (17.1.x) to include HPE Aruba ClearPass and Forescout CounterACT TAs. Updated VPN UCs (17.2.x) to include all four vendor TAs.
- **Successor app display:** Use cases referencing archived Splunkbase apps (Splunk App for Unix and Linux, Splunk App for Windows Infrastructure, Palo Alto Networks App for Splunk) now showcase the recommended successor app (IT Essentials Work, Splunk App for Palo Alto Networks) as the primary display, with the archived app mentioned below as a predecessor.
- **Equipment Models corrections:** Fixed UC-11.3.9, UC-11.3.10, UC-11.3.11, UC-11.3.13 which incorrectly listed Cisco voice equipment for Microsoft 365/Exchange use cases. Corrected to show Microsoft Exchange Online and M365 equipment with proper `Splunk_TA_MS_O365` and `Splunk_TA_microsoft-cloudservices` TAs.
- **Additional TA additions:** Added `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) to Spaces/occupancy UCs (11.5.x, 15.3.x) that include Meraki MV cameras or MR access points in Equipment Models. Added vendor-specific TAs to multi-vendor UCs in cat-18 (Data Center Fabric), cat-20 (Cost & Capacity), and cat-22 (Regulatory Compliance).

---

## [4.0] - 2026-03-24

### Multi-Vendor Network Coverage Expansion

- **Juniper Networks:** Added 4 Junos switching/routing UCs (5.1.56-5.1.59: chassis alarms, commit audit, RE failover, Virtual Chassis) and 3 SRX firewall UCs (5.2.41-5.2.43: IDP/IPS, Screen counters, cluster failover). Updated 34 generic router/switch UCs with Juniper EX/QFX/MX/SRX equipment models.
- **Arista Networks:** Added 3 Arista-specific UCs (5.1.60-5.1.62: MLAG health, EOS agent monitoring, CloudVision telemetry alerts). Updated 34 generic UCs with Arista 7000-series equipment.
- **HPE Aruba:** Added 2 Aruba CX switching UCs (5.1.63-5.1.64: VSF stack, VSX redundancy) and 5 wireless UCs (5.4.33-5.4.37: AP health, ClearPass RADIUS, WIDS/WIPS, Dynamic Segmentation, client experience). Updated 34 generic switch UCs and 9 wireless UCs with Aruba equipment.
- **Fortinet expansion:** Added 3 FortiGate-specific UCs (5.2.44-5.2.46: Security Fabric health, SD-WAN SLA monitoring, Web Filter/App Control). Updated 18 firewall UCs with FortiGate/FortiManager equipment models.
- **Cato Networks SASE:** Added 7 cloud-native SASE UCs (17.3.25-17.3.31: security events, WAN link health, threat prevention, cloud firewall audit, SD-WAN tunnels, SDP client monitoring, DLP/CASB events).
- **Palo Alto Networks:** Updated 18 firewall UCs with full PA-series equipment models and Panorama.
- **Multi-vendor equipment lists:** Updated 61 existing generic UCs across switching, firewall, wireless, VPN, and NAC sections to list equipment from Cisco, Juniper, Arista, HPE Aruba, Palo Alto, and Fortinet.
- **NAC section:** Updated 9 NAC UCs (17.1.x) to include HPE Aruba ClearPass and Forescout CounterACT alongside Cisco ISE.
- **VPN section:** Updated 8 VPN UCs (17.2.x) to include Palo Alto GlobalProtect, Fortinet SSL-VPN, and Juniper Dynamic VPN alongside Cisco ASA/AnyConnect.

---

## [3.9] - 2026-03-26

### Cisco Cyber Vision OT Security

- **25 new Cisco Cyber Vision use cases (14.9.1–14.9.25)** — Comprehensive OT/ICS security monitoring using Cisco Cyber Vision's Splunk Add-On (Splunkbase 5748) and syslog/CEF integration. Covers OT asset discovery and inventory tracking, new device detection alerts, vulnerability/CVE tracking with CVSS scoring, risk score monitoring, baseline deviation detection, Snort IDS threat detection with Talos rules, PLC program download/upload detection, controller firmware activation, forced variable detection, control action monitoring, controller mode changes (online/offline/force/CPU start-stop), new communication flow detection, protocol exception monitoring, authentication failure detection, admin connection tracking, port scan detection, weak encryption identification, SMB protocol activity in OT networks, network redundancy failover events, sensor health and resource monitoring, administration audit trail, IEC 62443 zone and conduit compliance, security posture dashboard, OT protocol usage analysis, and decode failure/malformed packet detection.

---

## [3.8] - 2026-03-26

### Building Management & Smart Buildings

- **26 new building management use cases** — Comprehensive smart building monitoring covering HVAC deep monitoring (AHU supply air temperature, VAV damper stuck detection, chiller COP efficiency, cooling tower approach, economizer free cooling, setpoint override tracking), energy management (EUI benchmarking, sub-metering, after-hours waste detection, peak demand shaving), elevator analytics (trip counting, door fault prediction, wait time SLAs), fire and life safety (alarm panel monitoring, sprinkler valve tamper, fire pump status), water management (consumption anomalies, Legionella prevention, cooling tower chemistry), lighting schedule compliance, parking occupancy, EV charging utilization, indoor air quality index, BACnet controller health, BMS alarm flood detection, and carbon emissions tracking (Scope 1+2).

---

## [3.7] - 2026-03-25

### Citrix Virtual Apps & Desktops and Citrix ADC/NetScaler Monitoring

- **Citrix CVAD monitoring (16 new)** — Session logon duration breakdown, ICA/HDX session latency and quality, connection failure analysis, VDA machine registration health, Delivery Controller service health, machine power state management, HDX virtual channel bandwidth, PVS vDisk streaming health, Profile Management load time, StoreFront authentication and enumeration, License Server utilization and compliance, application usage analytics, FAS certificate health, WEM optimization effectiveness, session recording compliance, and Cloud Connector health. New subcategory 2.6 in Virtualization.
- **Citrix ADC/NetScaler monitoring (10 new)** — Virtual server health and state, service group member health, SSL certificate expiration, HA failover monitoring, GSLB site and service health, Gateway/VPN session monitoring, content switching policy hit rate, system resource utilization, responder/rewrite policy errors, and SSL offload performance. Added to category 5.3 Load Balancers & ADCs.

---

## [3.6] - 2026-03-25

### DIPS Arena & IGEL Endpoint Monitoring

- **DIPS Arena EHR monitoring (10 new)** — Application response time, FHIR API availability and latency, user authentication and SSO monitoring, database performance, Communicator message throughput and failures, integration engine error monitoring, concurrent session and license utilization, clinical document generation latency, scheduled job monitoring, and openEHR AQL query performance. Added to category 21.3 Healthcare and Life Sciences.
- **IGEL End-User Computing / VDI Endpoints (10 new)** — Device fleet online/offline status, firmware version compliance, UMS server health monitoring, device heartbeat loss detection, OS endpoint syslog error monitoring, UMS security audit log monitoring, device resource utilization, unscheduled reboot detection, Cloud Gateway connection health, and device configuration drift detection. New subcategory 2.5 in Virtualization.

---

## [3.5] - 2026-03-25

### OpenTelemetry & Observability Expansion

- **OTel Collector Pipeline Operations (5 new)** — Pipeline throughput and backpressure monitoring, memory/CPU utilization tracking, configuration drift detection across collector fleet, per-receiver per-signal health monitoring, and exporter retry/timeout analysis.
- **Distributed Tracing Deep Dive (6 new)** — Trace duration anomaly and slow transaction detection, error rate by service and operation, trace completeness and orphan span detection, cross-service dependency map auto-discovery, log-to-trace correlation coverage audit, and trace fanout/depth anomaly detection.
- **Splunk Observability Cloud / APM / RUM / Synthetics (6 new)** — APM service map RED metrics, database query performance from APM traces, RUM Core Web Vitals tracking, RUM JavaScript error rate by page, synthetic multi-step transaction SLA, and Observability Cloud detector health audit.
- **SRE Methodology Patterns (5 new)** — RED metrics dashboard template, USE method for infrastructure, Golden Signals composite health per service, SLO multi-window burn rate alerting, and error budget policy enforcement.
- **eBPF Observability (3 new)** — Cilium Hubble kernel-level network flow monitoring, Tetragon process-level security observability, and Beyla eBPF auto-instrumented service metrics.
- **Observability Pipeline Governance (4 new)** — Data volume and cost attribution by team, cardinality explosion detection, instrumentation coverage audit, and telemetry signal freshness/staleness monitoring.
- **Kubernetes Observability (2 new)** — K8s event correlation with application traces, and resource quota/LimitRange compliance trending.

### New Subcategory

- **13.5 OpenTelemetry, Observability Pipelines & SRE Patterns** — Dedicated subcategory for OTel tracing, APM/RUM/Synthetics, SRE frameworks (RED/USE/Golden Signals/SLOs), and observability pipeline governance.

### Trend Use Cases Expansion (55 new)

- **9.7 Identity & Access Trending (7 new)** — Authentication volume, MFA adoption rate, privileged account activity, service account usage, conditional access policy blocks, password reset volume, and identity provider availability — all trended over 30–90 days with moving averages and forecasts.
- **22.9 Compliance Trending (5 new)** — Compliance posture score, audit finding closure rate, control effectiveness, regulatory incident response time, and policy violation volume trending across frameworks and quarters.
- **3.6 Container & Kubernetes Trending (6 new)** — Pod restart rate, container image vulnerability counts, deployment velocity, resource request vs limit utilization, Kubernetes event error rate, and ingress traffic volume trending.
- **4.6 Cloud Infrastructure Trending (6 new)** — Cloud resource count, Lambda/function invocation volume, security finding new vs resolved, S3/blob storage growth, network traffic volume, and CloudTrail/activity log event volume trending.
- **10.16 Security Operations Trending (8 new)** — Attack surface change, SIEM alert-to-incident ratio, MTTD, MTTR, phishing attempt volume, firewall rule hit rate, risk score distribution, and endpoint protection coverage trending.
- **8.7 Application Trending (5 new)** — User session volume, API latency percentiles (p50/p95/p99), error budget burn rate, cache hit ratio, and message queue backlog trending.
- **7.6 Database Trending (5 new)** — Connection pool utilization, slow query volume, replication lag, backup size growth, and index fragmentation trending.
- **16.5 ITSM Trending (5 new)** — Ticket backlog aging by bucket, change success rate, knowledge article deflection rate, MTTR by priority, and escalation rate trending.
- **14.8 IoT & OT Trending (4 new)** — Device fleet online rate, sensor data quality, OEE (Overall Equipment Effectiveness), and predictive maintenance alert volume trending.
- **12.6 DevOps Trending (4 new)** — DORA metrics dashboard (all four metrics), security scan finding lifecycle, build queue wait time, and container image build time trending.

### Non-Technical View

- **New areas added** — Plain-language sections for OpenTelemetry and observability pipelines, distributed tracing and APM, real user and synthetic monitoring, SRE patterns and SLOs, eBPF kernel-level observability, and trending areas for identity and access, compliance, containers, cloud, security operations, applications, databases, ITSM, IoT/OT, and DevOps.

### Datagen & POC tooling

- **Cribl / Splunk datagen guide** — `docs/guides/datagen-top10-use-cases.md` for ten representative use cases; `eventgen_data/manifest-top10.json` and per-family samples under `eventgen_data/samples/`; `scripts/generate_manifest_samples.py` (HEC NDJSON from the manifest), `scripts/parse_uc_catalog.py` (full catalog → `manifest-all.json`), `config/uc_to_log_family.json`; GitHub Actions workflow `.github/workflows/uc-manifest.yml` validates generation on push/PR.

---

## [3.4] - 2026-03-25

### Collaboration & Unified Communications Expansion

- **CUCM Deep Monitoring (7 new)** — CDR call path analysis, CMR call quality heatmap by site-pair, phone firmware compliance, gateway/CUBE channel utilization, cluster database replication health, Call Admission Control (CAC) rejection trending, and hunt group/line group overflow analytics.
- **Contact Center (5 new)** — Webex Contact Center agent state and occupancy, IVR containment rate, customer wait time SLA by skill group, UCCX real-time queue monitoring, and abandon rate correlation with network quality.
- **Jabber & IM Presence (2 new)** — Jabber client version compliance and health, IM and Presence Service (IM&P) node availability and XMPP session monitoring.
- **Unity Connection Voicemail (2 new)** — Voicemail system health (port utilization, message store, MWI delivery) and mailbox usage with retention compliance tracking.
- **Meeting Room Analytics (4 new)** — No-show and early release trending, people count vs capacity optimization, AV equipment health monitoring, and digital signage/room scheduler device health.
- **Cisco Spaces Advanced (3 new)** — Wayfinding and path analytics for traffic flow optimization, proximity and engagement analytics for space utilization, and IoT sensor alert correlation with building management response.

### Non-Technical View

- **New areas added** — Plain-language sections for on-premises phone systems (CUCM), contact center, messaging and presence, meeting room analytics, and indoor location/building intelligence.

---

## [3.3] - 2026-03-24

### Machine Learning & Deep Learning Use Cases

- **Security ML/UEBA (8 new)** — User peer-group logon anomaly, lateral movement via rare destinations, C2 beaconing detection, credential stuffing burst detection, risk score calibration, phishing NLP classification (DSDL), notable event prioritization model, and anomalous process execution — all leveraging MLTK and DSDL for threats that static rules miss.
- **IT Ops ML (6 new)** — Log volume/error rate anomaly per sourcetype, license usage forecast with seasonality, internal queue depth multivariate anomaly, service latency seasonality detection, Kubernetes HPA replica count anomaly, and SLO burn-rate multivariate anomaly.
- **ITSI ML extensions (2 new)** — Entity-level multivariate anomaly detection combining multiple KPIs per entity, and causal KPI ranking that automatically identifies root-cause KPIs when service health degrades.
- **Cloud & Cost ML (3 new)** — Cloud cost anomaly with seasonal decomposition, capacity exhaustion prediction with confidence intervals, and cloud control plane API call volume anomaly detection.
- **Deep Learning (4 new)** — Seq2seq log anomaly detection via LSTM autoencoder reconstruction error, host-metric heatmap anomaly via CNN, centralized model retraining for industrial sensor ML, and MLTK/DSDL model drift monitoring.

### New Subcategory

- **10.15 Machine Learning & Behavioral Analytics** — Dedicated subcategory for ML-powered security detections using MLTK and DSDL, covering UEBA, beaconing, credential attacks, and AI-assisted threat detection.

### Non-Technical View

- **ML areas added** — New plain-language sections explaining machine learning monitoring for security, platform intelligence, ITSI extensions, and deep learning model health.

---

## [3.2] - 2026-03-23

### New Use Cases

- **Elasticsearch deep monitoring** — 9 new use cases covering thread pool rejections, search latency and slow logs, ILM policy failures, snapshot health, cross-cluster replication lag, pending cluster tasks, cache evictions, segment merge pressure, and ingest pipeline errors.
- **Azure service expansion** — 15 new use cases for Application Gateway & WAF, VPN Gateway, ExpressRoute, Redis Cache, Data Factory, API Management, Virtual Desktop, Traffic Manager, Bastion, Network Watcher, Storage Queue, Managed Disk performance, SQL Managed Instance, Synapse Analytics, and Log Analytics Workspace ingestion health.
- **Docker deep monitoring** — 8 new use cases for container health check failures, network I/O anomalies, exec session auditing, socket exposure detection, image pull failures, dangling image/volume cleanup, Swarm service replica health, and container filesystem write rate.

### Data Source Filter

- **Two-level cascading filter** — Data source filter redesigned with 23 named source areas (Windows Event Logs, Sysmon, AWS, Cisco, etc.). Selecting an area reveals a second dropdown with specific sources and counts. Garbage entries from SPL parsing cleaned up.

### Sources Reference

- **New vendor documentation** — Added Elasticsearch cluster monitoring docs, Azure Monitor docs, and Docker monitoring docs to the External & Vendor Documentation section. Updated Microsoft Cloud TA count and category references.

---

## [3.1] - 2026-03-23

### Archived Splunkbase Apps

- **Archived app visibility** — Use cases referencing archived Splunkbase apps now show an amber "Archived App" badge on cards and a prominent warning box in the modal with a link to the recommended successor app.
- **Palo Alto Networks App** — Newly identified as archived; successor is Splunk App for Palo Alto Networks (Splunkbase 7505). Unix and Windows app entries now also link to IT Essentials Work (Splunkbase 5403).

### Advanced Filters

- **8 new filters** — Collapsible "Advanced Filters" panel below the existing filter strip with: ES Detection toggle, Detection type, Premium Apps, CIM Data Model, App/TA, Industry, MITRE ATT&CK (searchable), and Data source (searchable).
- **Pre-extracted facets** — `FILTER_FACETS` in data.js provides pre-sorted unique values for each filter dimension, eliminating client-side scanning of 4,600+ use cases on every page load.
- **Active filter chips** — All advanced filters appear as removable chips in the active filter tags row and are included in sidebar count updates.

### Non-Technical View

- **Full rewrite** — All 22 categories rewritten with 120 monitoring areas and 360 representative use case references. Build-time validation ensures UC IDs stay in sync with technical content.

### Sources Reference

- **Sources popup** — New footer button opens a reference of all documentation, apps, frameworks, and community resources used to research and build the use case catalog — from Splunk Lantern and ESCU to MITRE ATT&CK, vendor docs, and regulatory frameworks.

### Content Expansion

- **SD-WAN use case expansion** — Subcategory 5.5 expanded from 10 to 20 dedicated SD-WAN use cases covering OMP route monitoring, BFD session tracking, edge device resource utilization, firmware compliance, DPI application visibility, Cloud OnRamp performance, UTD security policy violations, vManage cluster health, transport circuit SLA tracking, and overlay topology validation.
- **Meraki subcategory dissolved** — All 110 Cisco Meraki UCs redistributed into their functional subcategories: wireless to 5.4, switching to 5.1, firewall/security to 5.2, DNS/DHCP to 5.6, management to 5.8, cameras to 15.3, environmental sensors to 14.1, and MDM to new subcategory 9.6.

---

## [3.0] - 2026-03-22

### Enterprise Security Detections

- **ES Detection badges** — 2,070 ESCU detection rules now display a teal "ES Detection" badge on use case cards and modals, with "Risk-Based Alerting" variant for RBA-enabled detections. Searchable via "escu", "es detection", "rba".
- **ESCU-specific implementation guidance** — Tailored deployment instructions for each detection methodology (TTP, Hunting, Anomaly, Baseline, Correlation): ES Content Management workflow, risk score tuning, analyst response per security domain, and SPL walkthrough for Risk Investigation drilldowns.

### SPL & Content Quality

- **join max=1** — Added explicit `max=1` to 88 `| join` statements across all categories to prevent silent data truncation at the default limit of 1.
- **Text quality pass** — Revised Value, Implementation, and Visualization fields for 30 use cases across 17 categories with specific, actionable guidance.

### Splunk Dashboard Studio (export)

- **44 separate chart objects** — `dashboards/catalog-quick-start-top2.json`: exactly **one** Dashboard Studio visualization per Quick-Start use case (top 2 × 22 categories). UC id and name appear as each panel's **title**/**description**, not extra markdown blocks. Regenerate with `scripts/generate_catalog_dashboard.py`.

---

## [2.1.12] - 2026-03-21

### Splunk dashboards

- **REST deploy** — `scripts/deploy_dashboard_studio_rest.py` pushes Dashboard Studio JSON to your Splunk server via the `data/ui/views` API (token or basic auth). See `dashboards/README.md`.

---

## [2.1.11] - 2026-03-21

### Splunk dashboards

- **Catalog Quick-Start Portfolio** — Initial `dashboards/catalog-quick-start-top2.json` (later replaced in v3 by **44** per-UC chart panels). Demo data (`makeresults`). See `dashboards/README.md`.

---

## [2.1.10] - 2026-03-21

### Content

- **Industry verticals** — Category 21 implementation notes for **aviation**, **telecom**, **water/wastewater**, and **insurance** now add domain context (standards, compliance, operations) and Splunk-oriented tuning notes alongside the existing guidance.

---

## [2.1.9] - 2026-03-21

### Detailed implementation

- **Tailored SPL explanations** — Generated guides now open with context from the use case (title, value, data sources, App/TA), compare the base search to documented sourcetypes, then walk the pipeline with command-specific detail (`stats`/`timechart` `by` and `span`, `eval` targets, `where` text). CIM blocks get a matching CIM-specific intro.

---

## [2.1.8] - 2026-03-21

### Navigation

- **Industry verticals** — Category 21 (Industry Verticals) is its own **domain group** in the sidebar and on the overview hero chips (between Applications and Regulatory & Compliance), not buried under Applications.

---

## [2.1.7] - 2026-03-21

### CIM field naming

- **src / dest** — Use-case SPL now prefers CIM-aligned `src` and `dest` (and related renames) instead of `src_ip`/`dest_ip` where practical; data model searches use `All_Traffic.src`/`All_Traffic.dest`. See `docs/cim-and-data-models.md` and `scripts/normalize_cim_fields.py`.

---

## [2.1.6] - 2026-03-21

### SPL & documentation

- **Review follow-up** — Additional hardening from `spl-review-findings.md`: `mvexpand` limits on multivalue fields, explicit `max=` on joins, `sort <N> -count` for top-N tables, AWS IoT provisioning aligned to CloudTrail + `eventSource`, RD Gateway XmlWinEventLog note. See the remediation note in that file.

---

## [2.1.5] - 2026-03-21

### Feedback

- **Report issue on GitHub** — Every use case modal (technical and plain-language) has a button that opens a new GitHub issue with the UC id, category path, link to the source `use-cases/*.md` file, and the dashboard URL with `#uc-…`. Set `window.SITE_CUSTOM.siteRepoUrl` if you fork the repo.

---

## [2.1.4] - 2026-03-21

### Detailed implementation

- **Understanding this SPL** — Generated step-by-step guides now include automatic pipeline explanations: what each major stage does (base search, aggregations, `tstats`/datamodel, joins, lookups, etc.). When a use case has CIM SPL, the optional accelerated query is included with a matching walkthrough.

---

## [2.1.3] - 2026-03-21

### SPL & Documentation

- **SPL / CIM alignment pass** — Catalog examples updated for Splunk CIM and TA conventions: `WinEventLog:Security` casing; `All_Traffic.bytes_in`/`bytes_out` totals; LDAP `tstats` + `cidrmatch()` for RFC1918; `index=windows` in compliance samples; FortiGate inventory scoped to supported sourcetypes; SOX ERP vs. AD searches split; safer `mvexpand`, `transaction`, and `sort` patterns; ITSI `inputlookup` context notes; fixed Meraki Data Sources backtick (UC-5.4.9).
- **Follow-up hygiene** — Correct `cidrmatch()` argument order (IP, then CIDR); CIM internal/external ratio example uses `drop_dm_object_name` + plain `src`/`dest`; MITRE coverage join uses explicit `max=0` and `mvexpand … limit=500`; bulk-closed broken inline-code backticks across Meraki Data Sources in Category 5; normalized `sort -field` spacing in Meraki SPL.

---

## [2.1.2] - 2026-03-21

### SPL Accuracy

- **ES `` `notable` `` macro** — Replaced `index=notable` with the Splunk ES `` `notable` `` macro across 15 SPL queries in Category 10 (Security Infrastructure) and Category 22 (Regulatory & Compliance). The macro resolves human-readable status labels, owner fields, and other enrichment that raw index access does not provide.

---

## [2.1.1] - 2026-03-21

### AI & LLM Discoverability

- **Self-describing catalog.json** — Added `_schema_url` and `_readme` keys at the top level so LLMs and tools fetching the catalog cold can immediately discover the field schema without a second fetch.
- **Expanded sitemap.xml** — Now generated by `build.py` with 33 URLs (was 4) — includes all 22 category files, INDEX.md, documentation pages, and AI index files. Stays in sync automatically as categories are added.
- **Cross-referenced llms.txt / llms-full.txt** — Each file now points to the other with a one-line note explaining the difference (concise category index vs. full use case listing).

---

## [2.1.0] - 2026-03-21

### Navigation & Filters

- **Tab-based content navigation** — Categories, Subcategories, Use Cases, and Quick Wins are now tabs above the content area, with the sort control on the same line.
- **Streamlined filter strip** — Removed inline labels; filter chips are self-explanatory with criticality colors shown as inline dots.
- **Interactive hero domain chips** — Clicking Infrastructure, Security, Cloud, Applications, Industry, or Regulatory on the front page filters the category grid and opens the relevant sidebar group.
- **Hero domain icons** — Replaced colored dots on front-page domain chips with monochrome SVG icons (server, shield, cloud, gear, clipboard).
- **Category icons in sidebar** — Replaced colored dots with per-category icons to avoid confusion with criticality colors.
- **Smart sidebar folding** — Non-active category groups auto-fold; manual expand/collapse is preserved until navigation changes.
- **Unified sidebar** — Both technical and non-technical modes now share the same grouped sidebar with collapsible sections, counts, and subcategory drill-down.

### Non-Technical View Redesign

- **Animated hero** — Gradient accent bar, "Proactive IT Monitoring" badge, gradient title text, and stagger-animated stats.
- **Richer category cards** — Staggered fade-in animations, gradient left-border on hover, icon highlight, focus-area and check counts on each card.
- **Category detail polish** — Back-to-overview button, gradient header accent, numbered area indicators, indented UC lists, and staggered area card animations.
- **Refreshed modal** — Styled section cards with green uppercase headings, subcategory breadcrumb, and "View full technical details" button with icon.

### Quality & Accessibility

- **Accessibility audit** — Added ARIA roles, keyboard handlers, and focus management to logo, hero chips, roadmap toggle, and navigation elements.
- **Release notes popup** — Full project history accessible from the page footer, covering all major and minor releases.
- **Bug fixes** — Fixed missing `filterByRegulation` function, Previous/Next URL updates, hash routing edge cases, clipboard error handling, and removed dead code.

---

## [2.0.0] - 2026-03-20

### Major UI Redesign

- **Unified filter system** — Pillar, criticality, difficulty, regulation, industry, and monitoring type consolidated into a single horizontal filter strip with active filter tags.
- **Redesigned front page** — Glassmorphism hero with animated gradient orbs, domain chips, key stats, and an expandable roadmap section.
- **Grouped sidebar navigation** — 6 collapsible groups (Infrastructure, Security, Cloud, Applications, Industry Verticals, Regulatory & Compliance) with color-coded headers.
- **Modern header** — Gradient header bar with integrated search (Cmd/Ctrl+K), live stats, theme toggle, and technical/non-technical view switch.
- **Deep linking** — Hash-based URL routing with `pushState`/`popstate` support for shareable links to categories, use cases, and search results.
- **Virtual scrolling** — IntersectionObserver-based lazy rendering for smooth performance with 4,600+ use cases.
- **Sort controls** — Sort by criticality, difficulty, name, or category with localStorage persistence.
- **Print stylesheet** — Clean printed output with navigation and decorative elements hidden.
- **Mobile experience** — Off-canvas sidebar with backdrop, 44px touch targets, safe-area insets, and dynamic viewport units.
- **Light mode overhaul** — Stronger contrast, subtle gradients, card shadows, and WCAG AA compliant tag colors.

### Content Expansion

- **4,625 use cases** across 22 categories — up from 3,473 across 20.
- **Category 22 — Regulatory & Compliance** promoted to standalone category with 30 use cases covering GDPR, NIS2, DORA, CCPA, MiFID II, ISO 27001, NIST CSF, and SOC 2.
- **Category 21 — Industry Verticals** with 119 use cases for energy, manufacturing, healthcare, telecom, retail, financial services, transportation, government, education, and insurance.
- **AI-friendly metadata** — Open Graph, Twitter Card, JSON-LD, `sitemap.xml`, `llms.txt`, and `llms-full.txt`.

---

## [1.0.0] - 2026-03-16

### First Public Release

- **3,000+ use cases** across 20 IT infrastructure categories with criticality, difficulty, SPL queries, CIM mappings, implementation guidance, and visualization recommendations.
- **Interactive single-page dashboard** with search, category/equipment/criticality filtering, non-technical view, and expandable use case details.
- **Build pipeline** — `build.py` compiles markdown use cases into `data.js` and `catalog.json`.
- **Equipment filter** with 30+ technology vendors/platforms and model-level drill-down.
- **Non-technical view** with plain-language outcomes per category for stakeholder discussions.
- **Machine-readable catalog** (`catalog.json`) for scripting and external integrations.
- **GitHub Pages deployment** via included GitHub Actions workflow.
- **SSE-aligned fields** — MITRE ATT&CK, detection type, known false positives, and security domain for security use cases.

---

## [0.x] - 2026-03-04 – 2026-03-09

### Early Development

- **Project created** — Initial upload of use case dashboard with basic HTML interface.
- **Core categories established** — Network, server, storage, security, and application monitoring use cases defined with SPL queries.
- **CIM integration** — Added Common Information Model data model references and tstats queries to use cases.
- **Meraki use cases** — Dedicated Cisco Meraki monitoring use cases added.
- **Cloud use cases** — AWS, Azure, and GCP monitoring categories introduced.
- **Equipment filter** — First version of vendor/platform equipment-based filtering.
- **Virtualization category** — VMware, Hyper-V, and container monitoring use cases.
- **Non-technical mode** — "Sales people mode" added for stakeholder-friendly descriptions.
- **Security Essentials integration** — Splunk Security Essentials and other app references added.
- **ThousandEyes use cases** — Network and application performance monitoring from ThousandEyes.
- **Cisco color scheme** — UI updated to align with Cisco brand guidelines.
- **LLM support** — Initial `llms.txt` for AI-assisted discovery.
