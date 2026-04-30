---
title: Infrastructure Monitoring Domain Guide
type: domain-guide
domains: [Infrastructure]
categories: [1, 2, 5, 6, 15, 18, 19]
last_updated: 2026-04-30
---

# Infrastructure Monitoring Domain Guide

This guide situates the **Infrastructure** pillar of the Splunk monitoring use-case catalog: operating-system telemetry, virtualization signals, campus-to-data-center networking, storage lifecycles, physical facility risks, programmable fabrics, and converged compute platforms. It connects vendor-native instrumentation—what each stack emits—to Splunk normalization patterns (Apps/TAs, sourcetypes, common alert semantics) so practitioners can prioritize crawl/walk/run adoption against measurable outage classes and audit obligations.

Browse the domain categories directly: [Browse Server & Compute](index.html#cat-1), [Browse Virtualization](index.html#cat-2), [Browse Network Infrastructure](index.html#cat-5), [Browse Storage & Backup](index.html#cat-6), [Browse Data Center Physical Infrastructure](index.html#cat-15), [Browse Data Center Fabric & SDN](index.html#cat-18), [Browse Compute Infrastructure](index.html#cat-19).

---

## Category 1: Server & Compute (275 use cases)

Server & Compute spans [Linux Servers](index.html#cat-1/1.1) (131), [Windows Servers](index.html#cat-1/1.2) (127), [macOS Endpoints](index.html#cat-1/1.3) (6), [Bare-Metal / Hardware](index.html#cat-1/1.4) (11), and blends performance telemetry with security-relevant OS narrative.

### Operating-system metrics and monitoring stance

**CPU, memory, disk, and processes** remain the canonical foundation because they translate directly into saturation, latency, and queueing—the three leverage points of capacity management.

- **Linux — WHAT/WHY/HOW:** Collect utilization from `/proc`-derived scripted metrics (`cpu`, `vmstat`, `df`, `ps`, `top`-equivalent scripts) via **Splunk Add-on for Unix and Linux (`Splunk_TA_nix`, Splunkbase 833)**. *Why:* Without normalized CPU steal / iowait / runnable-queue context, Linux hosts hide disk-backed slowdowns that masquerade as “CPU problems.” *How:* Deploy Universal Forwarders with TA inputs enabled at sensible intervals (typically 60–300s depending on cardinality); route `index=os` sourcetypes (`cpu`, `vmstat`, `df`) into accelerated Performance-model searches where alert latency demands sub-minute freshness.

- **Windows — WHAT/WHY/HOW:** Pair **Windows Event Log** security channels with **Performance Monitor** counters (PerfMon) and WMI-backed scripted queries via **`Splunk_TA_windows`** (Splunkbase 742). *Why:* Windows separates interactive saturation (processor queue, privileged time) from storage stalls (logical disk latency, avg. disk queue length). *How:* Enable WinHostMon / PerfMon inputs for `% Processor Time`, `Available MBytes`, paging file `% Usage`, logical disk `% Free Space`; ingest Security.evtx alongside for privileged-use auditing.

- **macOS — WHAT/WHY/HOW:** Endpoint fleets rarely justify bare-metal KPI parity with servers; prioritize integrity-relevant signals (auth events, privilege escalation paths, MDM posture) plus lightweight CPU/mem/disk snapshots where operational analytics justify UF footprint.

### Security events and compliance

Linux **`auditd`** trails (`audit.log`) anchor privileged-command accountability when forwarded via syslog or UF file tails; Windows **Advanced Audit Policy** selections align Security.evtx categories (logon, account management, privilege use) to SOC/SOX sampling expectations.

Compliance framing typically blends:

1. **Preventive controls** — patch cadence proxies via OS versioning fields pulled into lookups.
2. **Detective controls** — authentication anomalies and sudo / RunAs spikes correlated with change tickets.
3. **Corrective controls** — orchestration callbacks triggered by Splunk alerts (limited here by organizational maturity).

### Bare-metal reliability signals

Hardware-adjacent failures escape OS counters until workloads crash silently; prioritize EDAC/IPMI/BMC narratives:

| Critical UC | Risk addressed |
|-------------|----------------|
| [EDAC Memory Error Tracking](index.html#uc-1.1.102) | Row/column ECC faults preceding DIMM replacement |
| [IPMI Sensor Threshold Violations](index.html#uc-1.1.103) | Power/temp/current excursions visible only out-of-band |
| [Thermal Throttling Detection](index.html#uc-1.1.104) | Firmware slowing CPUs before thermal shutdown |
| [Fan Speed Anomalies](index.html#uc-1.1.105) | Cooling subsystem degradation vs HVAC faults |
| [Power Supply State Changes](index.html#uc-1.1.106) | Redundancy loss preceding cascading faults |

**WHAT/WHY/HOW for BMC ingestion:** Ship SEL/IPMI syslog streams or periodic sensor polls into Splunk via syslog receivers or scripted pulls (Heavy Forwarder). *Why:* Operating systems frequently lack sensors when BMC asserts predictive failures. *How:* Normalize vendor-specific severity tokens into Splunk lookups (`bmc_vendor`,`regex_extract`,`severity_map`) so correlated dashboards combine Linux OS KPIs with BMC thermal/power timelines without double-counting transient spikes during chassis firmware flashes.

### Linux syslog, `rsyslog`, and audit pipeline hardening

**WHAT:** Forward **syslog** (`/var/log/messages`, application logs, authentication trails) alongside **`auditd`** binary-format audit trails (`/var/log/audit/audit.log`) using Splunk UF `monitor://` inputs or **`imjournal`**/`imfile` hops through a Heavy Forwarder when checksum guarantees matter.

**WHY:** Performance metrics (`cpu`,`vmstat`) alone miss credential-theft timelines—Splunk correlation chains rely on temporal alignment between syscall-level audit records (`execve`,`chmod`,`mount`) and network-facing syslog authentication failures.

**HOW:** Apply Splunk **`props.conf`** `LINE_BREAKER`/`TIME_PREFIX` tuned per distro; tag `host`,`source`,`sourcetype` consistently (`linux_secure`,`auditd`). Map audit keys (`type=SYSCALL`,`type=USER_LOGIN`) into CIM **Authentication** where feasible; throttle noisy daemons via `whitelist`/`blacklist` transforms while preserving tamper-evident chains for Tier-1 hosts.

Representative catalog threads tying OS observability to incident response hygiene:

| Linked UC | Focus |
|-----------|-------|
| [OOM Killer Events](index.html#uc-1.1.7) | Memory-pressure kill signatures preceding instability |
| [SSH Brute-Force Detection](index.html#uc-1.1.8) | Credential-stuffing narratives |
| [Unauthorized Sudo Usage](index.html#uc-1.1.9) | Privilege escalation forensic pivot |
| [Cron Job Failure Monitoring](index.html#uc-1.1.10) | Scheduled-task automation drift |

### Windows Event Log depth and PerfMon pairing

**WHAT:** Harvest **Microsoft-Windows-Security**, **System**, **Application**, and workload-specific channels (SQL Server, IIS, Hyper-V) with unified timestamp normalization and channel-aware rendering (`renderXml=false` where KV extraction suffices).

**WHY:** Critical-path outages often surface first as **Event ID 7031/7034** service termination cascades before PerfMon saturation charts move—dual-plane ingestion avoids blind spots.

**HOW:** Splunk **`Splunk_TA_windows`** `WinEventLog://` stanzas reference explicit channels; combine with **`perfmon://`** checkpointed counters (`\Processor(_Total)\% Processor Time`, `\LogicalDisk(*)\Avg. Disk sec/Read`) sampled at ≤60s for operational dashboards vs ≤15s for tier-0 golden signals.

---

## Category 2: Virtualization (124 use cases)

Virtualization aggregates hypervisors ([VMware vSphere](index.html#cat-2/2.1)), Microsoft Hyper-V, KVM / Proxmox / oVirt families, cross-platform abstractions, VDI estates, and Citrix delivery tiers—each exporting scheduler/memory semantics invisible to guest-only agents.

### Splunk integration baseline

Use **`Splunk Add-on for VMware`** (Splunkbase package historically paired with VMware credential vault integrations) for inventory-aware KPI extraction across clusters, hosts, and VMs—avoid flattening raw hypervisor telemetry without CMDB linkage.

Anchor operational resilience:

| Critical UC | Signal |
|-------------|--------|
| [ESXi Host Unexpected Reboot](index.html#uc-2.1.21) | Host isolation / PSOD-class outages |
| [vCenter Service Health](index.html#uc-2.1.22) | Control-plane dependency failures |
| [VM Unexpected Power State Changes](index.html#uc-2.1.23) | HA/restart storms vs automation drift |
| [Datastore Capacity Trending](index.html#uc-2.1.3) | Thin-provision exhaustion cascades |

### VMware vendor-aligned hypervisor KPI practices (gold reference)

These practices derive from VMware capacity-planning doctrine (`esxtop`/vSphere Performance charts); Splunk surfaces them through TA-backed extracts or REST KPI pulls—**WHAT/WHY/HOW** triplets apply throughout.

**CPU Ready time (%RDY):**

- **WHAT:** Track CPU Ready (`%RDY`) per vCPU cohort—not raw CPU utilization—to quantify scheduler wait attributable to contention.
- **WHY:** Guests may report low CPU usage while latent-ready queues indicate undersized reservations during bursts; utilization-only dashboards green-light overloaded clusters.
- **HOW:** Capture `%RDY` from Performance Manager counters (`cpu.ready.summation` normalized by interval × vCPU), baseline weekly rolling medians/p95 per cluster/datastore cohort, alert when sustained Ready exceeds cohort percentile thresholds **derived from historical steady-state windows** (avoid static magic numbers).

**Balloon driver (`vmmemctl`):**

- **WHAT:** Monitor balloon target/active balloon KB (`mem.vmmemctl`), correlated with active memory (`mem.active`).
- **WHY:** Ballooning is VMware Tools-mediated reclaim signaling memory pressure earlier than swapping; sustained balloon growth precedes guest paging storms.
- **HOW:** Trend balloon slopes alongside reservation/overcommit ratios; suppress benign bursts tied to scheduled desktop pools using CMDB-backed scheduled suppression tokens.

**Swap activity (`swapinRate`/`swapoutRate`):**

- **WHAT:** Split VMkernel swap metrics from datastore latency spikes.
- **WHY:** Swap indicates worst-tier reclaim—latency-sensitive workloads crater before datastore KPI fires if clusters oversubscribe RAM aggressively.
- **HOW:** Combine swap counters with datastore queues (`disk.queueLatency`) for causality narratives in Splunk dashboards; elevate alerts when swap persists beyond rolling baseline envelopes absent correlated backup windows.

**Snapshot growth & orphaned snapshots:**

- **WHAT:** Track snapshot chain depth, aggregate snapshot GB per VM, delta-VMDK churn vs backup SLA snapshots.
- **WHY:** Snapshots inflate datastore utilization silently and degrade SCSI latency—classic latent outage vector during patching cycles.
- **HOW:** Scheduled searches comparing snapshot inventories daily; correlate Splunk alerts with backup orchestrator APIs where snapshot retention exceeds policy baselines.

**Baseline-driven thresholds:**

- **WHAT:** Replace global static thresholds with workload-tier baselines (percentile envelopes over aligned windows).
- **WHY:** Production OLTP behaves unlike dev burst workloads; uniform thresholds yield chronic alert fatigue across tiers.
- **HOW:** Store baseline stats via summary indexing (`summary index = vmware_baselines`) keyed by `(cluster,tier,business_service)`; alerts evaluate deviation multiples vs baseline—not absolute KPI alone.

**Service mapping & operational hygiene:**

- **WHAT:** Map VMs/clusters to business services with CMDB IDs reflected as Splunk indexed fields (`business_service`,`tier`).
- **WHY:** Incident bridges prioritize blast radius when datastore contention threatens tier-1 ERP clusters vs sandbox tiers.
- **HOW:** Automated KV lookups nightly from ITSM exports; dashboards split KPI tiles by service criticality.

**Alert grouping & maintenance suppression:**

- **WHAT:** Aggregate correlated host/cluster alarms within configurable suppression windows coinciding with VMware Maintenance Mode entries or CI/CD resize bursts.
- **WHY:** Rolling storms duplicate pager noise during intentional migrations (Storage vMotion waves).
- **HOW:** Splunk alert throttle keyed on `(cluster,domain)` plus Splunk lookups referencing approved maintenance calendars.

### Hyper-V, KVM / Proxmox / oVirt, VDI, and Citrix overlays

VMware dominates enterprise hypervisor mindshare, yet Splunk estates routinely aggregate heterogeneous stacks—each exposes distinct choke points:

**Hyper-V — WHAT/WHY/HOW:** Ingest **Hyper-V Worker** Event Log clusters (`Microsoft-Windows-Hyper-V-Worker/Admin`), **VMMS** service health, synthetic CSV exports from **`Get-VM`** scheduled scripts, and SCVMM Orchestration logs where System Center persists automation intent. *Why:* Hyper-V clusters signal localized CSV disconnections (`Event ID 5120/5121`) independent of VMware datastore narratives. *How:* Splunk UF on cluster nodes plus centralized Hyper-V host grouping macros (`hyperv_cluster`,`csv_volume_guid`) correlate CSV reconnect storms with upstream SAN latency searches from Category 6.

**KVM / Proxmox / oVirt — WHAT/WHY/HOW:** Normalize **`libvirt`**/`qemu` logs, Proxmox **`pvestatd`** JSON exports via scripted inputs, and oVirt REST VM statistics where burst-heavy workloads demand kernel-side KVM scheduling visibility (`vcpu` steal analogs via `/proc/stat` deltas per guest cgroup). *Why:* Open ecosystems lack VMware’s unified Performance Manager—Splunk becomes the aggregator of truth for scheduler fairness signals. *How:* Heavy Forwarder pulls bridge API credentials into KV stores; dashboards overlay storage pools (`thin_lv_full`) with guest CPU steal proxies.

**VDI — WHAT/WHY/HOW:** Horizon/Citrix landscapes prioritize **session latency**, **protocol degradation**, **launch failures**, and **brokering queue depth** ahead of generic CPU charts. *Why:* User-perceived outages stem from protocol-tier contention even when ESXi Ready % looks acceptable. *How:* Splunk indexes Citrix Delivery Controller events (`Citrix Broker/Licensing`), VMware Horizon Connection Server logs (`ldap`,`certificate`,`blast`) merged with VMware KPIs above—baseline **logon duration percentiles** weekly.

**Citrix — WHAT/WHY/HOW:** Pull Citrix ADC (**NetScaler**) syslog (`EVENT_MSG`/`SSLVPN`) alongside Citrix Virtual Apps session reliability metrics (`WFICA`, `Citrix Workspace App`). *Why:* Gateway saturation presents as ICA RTT spikes invisible inside guest OS monitors alone. *How:* Splunk transforms map Citrix ADC expressions (`citrix_adc_syslog`) into multi-field extractions correlating VIP (`vserver`) with ThousandEyes SaaS HTTP tests where hybrid workers traverse competing paths.

---

## Category 5: Network Infrastructure (490 use cases) — Cisco gold standard

Network Infrastructure is the catalog’s largest vertical ([Browse Network Infrastructure](index.html#cat-5)): routers/switches, firewalls, load balancers, wireless, SD-WAN, DNS/DHCP, flow telemetry, management-plane APIs, Digital Experience Monitoring (ThousandEyes), carrier signaling, model-driven telemetry (gNMI/gRPC), telecom-style CDR feeds, Cisco Catalyst Center assurance/automation posture, Infoblox IPAM narratives, plus adjacent ecosystem integrations.

Non-Cisco ecosystems remain essential for heterogeneous estates:

| Focus | Typical Splunk angle |
|-------|---------------------|
| Juniper Junos syslog | **`Splunk_TA_juniper`** — structured facility parsing |
| Arista EOS streaming | Syslog via **Splunk Connect for Syslog (SC4S)** with EOS-specific parsers |
| Aruba Central / WLAN controllers | REST exports + syslog hybrids |
| F5 BIG-IP | AFM/LTM logs + iHealth snapshots via scripted pulls |
| BlueCat / Infoblox DDI | Audit syslog + Grid replication events |
| NetFlow/IPFIX + Zeek | Flow codecs (`stream:*`) beside IDS narratives |

### Firewalls, ADCs, wireless, DNS/DHCP, flow telemetry, and streaming models

Before consolidating on Cisco-specific controllers, align Splunk ingestion with **horizontal control-plane roles**—each subcategory maps to measurable blast-radius classes:

#### Firewalls ([Browse Firewalls](index.html#cat-5/5.2))

**WHAT:** Normalize vendor syslog (Palo Alto `traffic`/`threat`, Cisco Secure Firewall **eStreamer**/syslog, Fortinet FGTVOM, Check Point OPSEC LEA, Meraki MX unified threat narratives) into Splunk ES-compatible schemas where licensing permits.

**WHY:** Stateful inspection devices emit **session lifecycle** semantics—Splunk timelines differentiate benign bulk transfers from **C2 beaconing** faster than pure NetFlow absent application labels.

**HOW:** Deploy Heavy Forwarders at syslog aggregation tiers with **`props/transforms`** enforcing consistent `_time` extraction across fragmented syslog lines; leverage **`Firewall`**/**`IDS`** CIM templates for cross-vendor analytics. Anchor operational resilience via catalog threads such as [Firewall HA Failover Events](index.html#uc-5.2.14) (fail-open detection) and [Session Table Exhaustion](index.html#uc-5.2.13) (state-store pressure preceding silent drops).

#### Load balancers ([Browse Load Balancers & ADCs](index.html#cat-5/5.3))

**WHAT:** Capture F5 BIG-IP **LTM**/AFM logs (`/var/log/ltm`), pool member health transitions (`POOL_MEMBER_DOWN`), SSL handshake failures, Citrix ADC rewrite policies, plus A10/Kemp syslog dialects where applicable.

**WHY:** ADCs terminate TLS—Splunk joins certificate expiry narratives with Catalyst Center wireless onboarding failures when captive portals share PKI chains.

**HOW:** Scripted pulls of **iHealth**/**qkview** summaries complement streaming logs—schedule nightly modular inputs storing serialized diagnostics alongside syslog streams for RCA archives.

#### Wireless infrastructure ([Browse Wireless Infrastructure](index.html#cat-5/5.4))

**WHAT:** Blend Cisco Catalyst/WLC syslog (`CLIENT_OR_DEBUG`), Aruba Central REST exports, Mist JWT-based webhooks, and Meraki MR RF telemetry (`meraki:networks`/`meraki:wireless`) already unified via **`Splunk_TA_cisco_meraki`**.

**WHY:** RF metrics (`SNR`,`retry rate`,`channel utilization`) contextualize Catalyst Center Assurance scores—Splunk overlays bridge controller-less vs controller-led architectures.

**HOW:** Normalize BSSID/AP MAC joins across datasets via lookups keyed by `serial`/`networkId`; correlate roaming events with DHCP scope pressure captured next.

#### DNS & DHCP ([Browse DNS & DHCP](index.html#cat-5/5.6))

**WHAT:** Infoblox **Grid** syslog (`audit`,`dns`,`dhcp`), BlueCat Address Manager audit feeds, Microsoft DNS analytical logs (`Microsoft-Windows-DNS-Server/Analytical`), ISC BIND structured syslog.

**WHY:** Application outages masquerade as “network down” when **NXDOMAIN** storms or **DHCP exhaustion** starve clients—Catalyst Center client health cannot diagnose authoritative DNS failures alone.

**HOW:** Splunk Add-on for **Infoblox** supplies field extractions; pair [DHCP Scope Exhaustion](index.html#uc-5.6.5) baselines with Meraki MX DHCP narratives (`meraki:events`) for branch-office contrast. DNSSEC validation threads ([DNSSEC Validation Failures](index.html#uc-5.6.10)) demand Splunk correlation against resolver forwarding hops.

#### Network flow data ([Browse Network Flow Data](index.html#cat-5/5.7))

**WHAT:** Ingest **NetFlow v5/v9/IPFIX** (`stream:cisco_hsl_netflow`, Splunk Stream, Cisco IOS Flexible NetFlow exports), **sFlow**, and **Zeek** `conn.log`/`dns.log` for unsampled east-west forensics.

**WHY:** Flow telemetry reveals volumetric DDoS and lateral movement paths absent from SNMP interface counters—security analytics complements SD-WAN **TCP/UDP syslog** security dashboards mandated by Cisco reference designs.

**HOW:** Splunk **CIM Network Traffic** acceleration over flow-derived fields (`src_ip`,`dest_ip`,`bytes_in`) powers [East-West Traffic Monitoring](index.html#uc-5.7.4) and [Long-Duration Flow Detection](index.html#uc-5.7.10) pivots; tune retention/class masks to control license burn—sample heavy CDN flows via Splunk **filter transforms**.

#### gNMI / gRPC streaming telemetry ([Browse gNMI / gRPC](index.html#cat-5/5.11))

**WHAT:** Subscribe to **OpenConfig**/`ietf-interfaces` YANG paths via **gNMI ON_CHANGE** dial-out/dial-in collectors feeding Splunk HTTP Event Collector endpoints—NX-OS/Arista EOS expose line-rate counters (`interfaces/interface/state/counters`) suitable for microburst analytics.

**WHY:** Poll-based SNMP misses sub-second microbursts causing silent drops—streaming telemetry aligns with Cisco **model-driven telemetry** guidance for modern fabrics.

**HOW:** Operationalize UC threads such as [Interface Utilization via gNMI Streaming Counters](index.html#uc-5.11.1) and [BGP Peer State Change Detection via ON_CHANGE](index.html#uc-5.11.3)—Splunk dashboards stitch dial-out telemetry with Catalyst Center Assurance fault timelines using shared `deviceId` lookups.

#### Carrier signaling & telecom CDR ([Browse Carrier](index.html#cat-5/5.10), [Browse Telecom & CDR](index.html#cat-5/5.12))

**WHAT:** Capture SS7/Diameter adjunct logs (where permissible), SIP ladder diagrams normalized to syslog, CDR batches via SFTP ingestion into Splunk indexes partitioned by tenant.

**WHY:** Service-provider interconnect faults surface as signaling anomalies invisible to enterprise LAN tooling—Splunk correlation joins SIP **5xx** bursts with ThousandEyes Voice Test metrics for UCaaS bridges.

**HOW:** Heavy Forwarder **`batch`** inputs monitor landing zones; **`INDEXED_EXTRACTIONS = CSV`** with strict **TZ** offsets prevents multi-region daylight drift during regulatory investigations.

### Cisco Catalyst Center (78 use cases — subcategory [Cisco Catalyst Center](index.html#cat-5/5.13))

Cisco Catalyst Center (formerly DNA Center) exemplifies controller-led assurance across campus fabrics. Cisco IT publicly cites transformational outcomes—**97% reduction in critical/high software vulnerabilities** through disciplined lifecycle governance and **59% faster software upgrades** via standardized automation pipelines—underscoring why Splunk correlation across Catalyst Center telemetry yields measurable operational ROI versus fragmented CLI scraping.

#### Assurance vs Intent APIs — WHAT/WHY/HOW

**Assurance API (experience-centric KPIs):**

- **WHAT:** Consume endpoints exposing network/client/device **health scores** (WLAN RF, onboarding latency, QoE aggregates).
- **WHY:** Assurance stitches passive telemetry already correlated inside Catalyst Center—Splunk amplifies breadth across IT domains without rebuilding ML pipelines manually.
- **HOW:** Configure **`TA_cisco_catalyst` account inputs** hitting Catalyst Center HTTPS endpoints (`/dna/intent/api/v1/**` families—health/issue/device/client namespaces vary by release); normalize responses into Splunk sourcetypes **`cisco:dnac:issue`**, **`cisco:dnac:device`**, **`cisco:dnac:client`**. Store bearer-token refreshes via TA credential vault patterns.

**Intent API (structured automation-facing datasets):**

- **WHAT:** Poll Intent endpoints for inventory (`network-device`), topology overlays (`topology`), fabrics (`site`,`fabric-site`), wireless assurance summaries.
- **WHY:** Intent responses include MoRef-style handles you can pivot on in Splunk lookups (serial → site mapping) for downstream service modeling.
- **HOW:** Scripted inputs stagger API calls with rate-limit awareness; summary-index high-cardinality enumerations nightly to flatten day-time search cost.

| Sourcetype (TA output) | Example `GET` path | Health / issue semantics |
|------------------------|---------------------|---------------------------|
| `cisco:dnac:networkhealth` | `/dna/intent/api/v1/network-health` | Aggregate network score & good/bad counts |
| `cisco:dnac:devicehealth` | `/dna/intent/api/v1/device-health` | Per-device `overallHealth`, reachability |
| `cisco:dnac:clienthealth` | `/dna/intent/api/v1/client-health` | Wired/wireless client score rollups |
| `cisco:dnac:issue` | `/dna/intent/api/v1/issues` | Assurance issue objects (`issueId`,`priority`,`status`) |
| `cisco:dnac:device` | `/dna/intent/api/v1/network-device` | Inventory / `softwareVersion` / `managementIpAddress` |
| `cisco:dnac:client` | `/dna/intent/api/v1/client-detail` | Per-client MAC, host type, connection type, health JSON |
| `cisco:dnac:swim` | `/dna/intent/api/v1/image/importation` | Image compliance vs golden target (input cadence varies) |
| `cisco:dnac:securityadvisory` | `/dna/intent/api/v1/security-advisory/advisory` | PSIRT/CVE device coverage |

**Note:** Exact query parameters (`deviceId`,`siteId`,`macAddress`) vary by Catalyst Center release—validate against the TA’s shipped Python/REST helpers before crafting ad-hoc `curl` probes in production change windows.

#### SWIM & PnP — operational pairing

**SWIM (Software Image Management):**

- **WHAT:** Track image compliance matrices, pending upgrade batches, golden-image adherence.
- **WHY:** Catalyst Center reduces MTTR for CVE responses when Splunk overlays image drift with vulnerability ticketing.
- **HOW:** Splunk ingest includes `cisco:dnac:swim` class events (when enabled) with join keys `deviceId`,`siteName` correlated to `cisco:dnac:securityadvisory` PSIRT summaries (per TA feature set).

**PnP (Plug and Play):**

- **WHAT:** Log zero-touch provisioning lifecycle with RMA replacement tracking.
- **WHY:** Mis-provisioned templates mimic outages—PnP failures correlate with DHCP/DNS Splunk feeds cross-domain.
- **HOW:** Splunk dashboards overlay `cisco:dnac:event:notification` webhook streams when administrators configure Catalyst Center notifications toward Splunk HTTP Event Collector (HEC).

#### ITSM integration (ServiceNow)

**WHAT/WHY/HOW:** Catalyst Center automation hooks commonly synchronize incidents with ServiceNow CMDB CI granularity. Splunk correlates Catalyst Center issue fingerprints (`issueId`,`priority`,`deviceManagementIp`) with SNOW change/incident IDs ingested via TA-ServiceNow connectors—closing loops between assurance anomalies and workflow execution audits captured as **`cisco:dnac:audit`** (`audit` lineage covers administrator actions affecting templates/PnP/SWIM).

#### Splunk packaging

| Artifact | Splunkbase ID | Role |
|----------|---------------|------|
| Cisco Catalyst Add-on for Splunk | **7538** | Credential-backed scripted/API inputs |
| Cisco Enterprise Networking App for Splunk | **7539** | Dashboards/macros bridging Catalyst Center + IOS-XE/NX-OS contexts |

Canonical sourcetypes emphasized for Splunk analysts:

- **`cisco:dnac:issue`** — prioritized anomaly narratives with remediation hints.
- **`cisco:dnac:device`** — inventory posture attributes (`softwareVersion`,`role`,`reachability`).
- **`cisco:dnac:client`** — onboarding/session diagnostics where Assurance licensing applies.
- **`cisco:dnac:audit`** — privileged-change lineage.

Representative correlated UC journeys pair Assurance anomalies with upstream/downstream telemetry—for example bridging Catalyst Center wireless onboarding degradation with DHCP/DNS Splunk feeds captured elsewhere in Category 5.

### Cisco ThousandEyes (54 use cases — subcategory [Network Experience Monitoring](index.html#cat-5/5.9))

ThousandEyes treats Internet/SaaS paths as first-class observables—distinct from SNMP/syslog device-only narratives.

#### Path Visualization — WHAT/WHY/HOW

**WHAT:** Hop-by-hop Path Visualization overlays latency/packet-loss attribution across autonomous systems.

**WHY:** Traditional ICMP-only pings collapse multi-provider faults into ambiguous endpoint failures—path graphs localize ISP brownouts versus DNS hijacks versus SaaS ingress saturation.

**HOW:** ThousandEyes tests emit normalized metrics Splunk indexes via **`ThousandEyesOTel`** OpenTelemetry streams hitting Splunk **HEC** (recommended ingestion architecture per ThousandEyes streaming guides). Splunk dashboards replicate storytelling layering:

1. Executive KPI strip — SLA adherence vs synthetic availability budget.
2. Middle tier — geographic variance tiles (`GeoLatency`).
3. Detail hop table — ASN-level deltas with correlated internal change markers.

Illustrative catalog links:

| UC | ThousandEyes tie-in |
|----|---------------------|
| [Path Hop Count Analysis](index.html#uc-5.9.5) | Path length regression |
| [Network Path Change Detection](index.html#uc-5.9.6) | Route flaps vs DC moves |
| [HTTP Server Availability Monitoring (ThousandEyes)](index.html#uc-5.9.34) | Test targets tied to SaaS SLAs |

#### SYN vs SACK probing optimization — WHAT/WHY/HOW

**WHAT:** ThousandEyes supports SYN-style probes alongside TCP-mode analyses leveraging selective acknowledgment semantics where permitted.

**WHY:** Oversimplified ICMP-only tooling risks **false packet-loss** indications when intermediate routers treat ICMP lower priority—SYN vs TCP semantics differentiate congestion-induced discard versus benign ICMP shaping.

**HOW:** Splunk alerts comparing probe-method strata (`testType`,`protocol`) stored as indexed fields—suppress noisy ICMP-only dashboards where TCP-mode corroborates healthy SaaS availability.

#### SaaS monitoring packs — WHAT/WHY/HOW

**WHAT:** Instantiate ThousandEyes Cloud Agent suites targeting Microsoft 365, Teams, Salesforce, Webex, Zoom front doors plus regional CDN edges.

**WHY:** SaaS outages bypass campus SNMP entirely—digital employee experience KPIs belong beside Catalyst Center WLAN Assurance scores.

**HOW:** Splunk correlation joins ThousandEyes HTTP transaction KPIs (`ThousandEyesOTel.*`) with **`cisco:thousandeyes:test`** normalized dimensions (`testId`,`agentId`,`interval`), augmenting **`cisco:thousandeyes:alert`** streams for paging workflows.

#### Splunk TA footprint

**App:** Cisco ThousandEyes (Splunkbase **7719**)

**Sourcetypes:**

- **`ThousandEyesOTel`** — OTLP metrics/logs streaming via HEC (preferred operational pipeline).
- **`cisco:thousandeyes:test`** — poll-based test telemetry.
- **`cisco:thousandeyes:alert`** — incident-class events for Splunk alerting.

#### Dashboard storytelling best practices — WHAT/WHY/HOW

**WHAT:** Arrange layers: (1) synthetic availability SLO badge, (2) loss/latency trend with maintenance markers, (3) hop-level forensics panel, (4) internal change overlay from ITSM webhook index.

**WHY:** Bridge teams distrust charts lacking operational context—storytelling prevents duplicate Sev1 bridges during dual-domain ambiguity.

**HOW:** Splunk Dashboard Studio tokens referencing `_time`-bounded `$maintenance$` lookups mute ThousandEyes spikes coinciding with authorized carrier maintenance windows.

### Cisco Meraki (wireless / IoT sensors)

Meraki blends wireless telemetry with MT environmental sensors—Splunk dashboards unify WLAN KPIs with sensor anomaly timelines.

#### Dashboard primitives — WHAT/WHY/HOW

**WHAT:** MT sensor dashboards expose alert cards (threshold crossings), overview cards (aggregate humidity/temperature distributions), alert logs for forensic timelines.

**WHY:** Facilities anomalies historically lived outside NetOps tooling—Splunk correlation merges HVAC excursions with WLAN RF degradation narratives.

**HOW:** **`Splunk_TA_cisco_meraki` (`Splunkbase 5580`, release notes highlight multi-org aggregation improvements including **3.3.0**)** merges organizations via consolidated API credential scopes—Splunk admins configure parallel modular inputs per org while dashboards federate cross-org KPI tiles via lookup normalization.

#### Integration architecture — WHAT/WHY/HOW

**WHAT:** Combine REST polling (`/organizations/*/devices`, sensor histories), Meraki webhooks (alert streams), MQTT telemetry where IoT gateways participate.

**WHY:** REST yields completeness while webhooks/MQTT minimize latency for transient spikes—Splunk ingestion tiers merge batch + streaming semantics.

**HOW:** Splunk Heavy Forwarder modular inputs populate **`meraki:devices`**, **`meraki:sensorreadingshistory`**, **`meraki:webhook`** sourcetypes—normalize JSON payloads via props/transforms into accelerated summaries (`sensor_serial`,`sensor_metric`,`networkId`).

### Cisco SD-WAN (20 use cases — subcategory [SD-WAN](index.html#cat-5/5.5))

Cisco Catalyst SD-WAN overlays application-aware steering with security service edge adjacencies—Splunk delivers single-pane operational/security fusion.

#### Enhanced Monitor Overview — WHAT/WHY/HOW

**WHAT:** Cisco SD-WAN Manager dashboards (`Enhanced Monitor Overview`, Release **20.7.1+**) emphasize customizable dashlets with global topology overlays summarizing overlay vs underlay health.

**WHY:** Operators distinguish intentional WAN brownouts remediated via SLA steering versus latent controller-plane regressions faster than CLI hopping edge routers.

**HOW:** Splunk mirrors dashlet KPI families via syslog (`cisco:sdwan:syslog`), IPS signatures (`cisco:sdwan:ips`), NetFlow (`stream:cisco_hsl_netflow`) parsing aligned with **Splunk Add-on for Cisco Catalyst SD-WAN** (Splunkbase **6656**) and **Cisco Catalyst SD-WAN App** (Splunkbase **6657**).

#### Security analytics pairing — WHAT/WHY/HOW

**WHAT:** Cisco’s validated Splunk integration patterns emphasize forwarding **TCP/UDP syslog** streams from SD-WAN appliances (control connections, UTunnel events, AMP correlatives where licensed) alongside **NetFlow/IPFIX** exports (`stream:cisco_hsl_netflow`) capturing flow-aware threat hunts—mirroring dashboards packaged with **`Splunk Add-on for Cisco Catalyst SD-WAN (6656)`** / **`App (6657)`**.

**WHY:** Overlay-centric troubleshooting isolates SLA steering gaps while security analytics exposes east-west malware egress disguised as benign SaaS TLS—dual-plane ingestion avoids tunnel-vision ops dashboards.

**HOW:** Splunk Heavy Forwarders terminate syslog TLS optionally; NetFlow receivers sit on dedicated collector tiers with **`source`=`cisco_sdwan_netflow`** naming consistency for CIM joins—alerts throttle on `(vdevice_id,threat_signature)` tuples to match Cisco’s recommended deduplication semantics.

#### IOS-XE baseline requirement — WHAT/WHY/HOW

**WHAT:** IOS-XE **17.10+** compatibility gates Splunk app expectations around telemetry richness.

**WHY:** Older IOS-XE trains omit consistent model-driven telemetry exports—Splunk parsers fall back ambiguously without field contracts.

**HOW:** Compliance searches index `softwareVersion` fields alongside Splunk lookups verifying minimal IOS-XE trains before onboarding routers into dashboards.

### IOS / IOS-XE routers & switches ([Routers & Switches](index.html#cat-5/5.1))

Classic Cisco forwarding-plane instrumentation feeds Splunk via syslog (facility-oriented severity tokens), SNMP traps for hardware redundancy transitions, and streaming telemetry adjuncts.

**TA:** **`TA-cisco_ios` (`Splunkbase 1352`)** supplies Cisco IOS syslog transforms accelerating interface/protocol narratives.

#### Critical IOS-aligned UC anchors

| UC | Operational interpretation |
|----|----------------------------|
| [Interface Up/Down](index.html#uc-5.1.1) | Link-loss segmentation vs bounce churn |
| [Power Supply/Fan Failures](index.html#uc-5.1.11) | Hardware redundancy breaches |
| [Route Table Flapping](index.html#uc-5.1.16) | Control-plane instability |
| [EIGRP Neighbor Flapping](index.html#uc-5.1.20) | IGP reconvergence storms |
| [HSRP/VRRP State Changes](index.html#uc-5.1.23) | Default-gateway failover narratives |

**WHAT/WHY/HOW aggregate:** Normalize syslog `%LINK`/`%BGP`/`%OSPF`/`%EIGRP`/`%HSRP` patterns via TA transforms—Splunk alerts differentiate singular fiber cuts (`single-interface`) vs systemic PSU faults (`multi-interface concurrent`). Correlate Catalyst Center Assurance overlays where IOS-XE switches integrate controller-managed telemetry alongside standalone syslog ingestion.

---

## Category 6: Storage & Backup (81 use cases)

Storage spans SAN/NAS arrays ([SAN/NAS](index.html#cat-6/6.1)), object endpoints ([Object Storage](index.html#cat-6/6.2)), backup suites ([Backup & Recovery](index.html#cat-6/6.3)), and shared file services ([File Services](index.html#cat-6/6.4)).

### Capacity, latency, IOPS — unified lens

**WHAT:** Track utilization growth rates, thin-provisioning headroom, controller queue depth, front-end Fibre Channel / NVMe-oF latency percentiles.

**WHY:** Storage failures often present as latency tail events before absolute space exhaustion—IOPS saturation matters for bursty DB workloads even when capacity KPIs remain green.

**HOW:** Splunk ingestion from array APIs (`ONTAP`, `PowerStore`, `Pure1`, `Isilon REST`) harmonized via TAs or custom modular inputs—summary index daily growth projections (`predict` command windows) feeding capacity burn-down dashboards.

### Vendor-specific array telemetry — NetApp, Dell EMC, Pure, Dell **Isilon**/PowerScale

**NetApp ONTAP — WHAT/WHY/HOW:** Subscribe to **EMS** event catalogs (`wafl.cp.toolong`,`disk.hardware.error`) alongside REST **`/api/storage/aggregates`** capacity payloads and Unified Manager performance polls. *Why:* WAFL checkpoint latency precedes NFS timeouts observable only indirectly at hosts. *How:* Splunk modular inputs stagger `/api/cluster` contexts per SVM—dashboards correlate EMS severity with NFSv4 **`v4_x_err`** syslog tails forwarded from NAS gateways.

**Dell EMC PowerStore / Unity — WHAT/WHY/HOW:** Pull REST **`instance`**/`metric` families for node CPU/memory headroom plus replication session states (`ReplicationSession`). *Why:* Active/active Metro fabrics shift failure domains—Splunk must pair replication lag seconds with VMware datastore latency from Category 2. *How:* OAuth-stored credentials inside Splunk credential locker with rotating refresh tokens scripted nightly.

**Pure Storage FlashArray — WHAT/WHY/HOW:** Pure1 REST exposes **`array`,`volume`,`host`** latency histograms (`usec_per_op`)—trend drive rebuild states (`hardware.components`) alongside predictive failure counters per Pure Operations Guide thresholds. *Why:* All-flash arrays mask wear until parallel rebuild windows coincide with peak OLTP bursts. *How:* Scheduled searches persist `capacity` and `thin_provisioning` snapshot fields into summary indexes powering [Pure Storage Array Health](index.html#uc-6.1.19).

**Dell PowerScale (Isilon) — WHAT/WHY/HOW:** OneFS **`isi_audit_categories`** syslog plus REST **`/platform/*/cluster/status`** quorum narratives feed Splunk alongside SMB/NFS latency proxies. *Why:* Scale-out NAS outages cluster as **`JOB_ENGINE`** backlog spikes—capacity alone stays green while metadata storms persist. *How:* Correlate [Isilon Cluster Health](index.html#uc-6.1.11) dashboards with SMB **`tcp`** connection resets captured at adjacent Catalyst Center client metrics.

**Ceph — WHAT/WHY/HOW:** **`ceph -w`**/`ceph.log`, RADOSGW access logs, Prometheus **`ceph_exporter`** scrape endpoints via Splunk HTTP Event Collector OTEL bridging. *Why:* Placement-group `degraded` / `peering` states precede client IO stalls—Splunk overlays OSD maps with host disk SMART narratives from Category 1. *How:* Implementation narrative captured in [Ceph Cluster Health](index.html#uc-6.1.14).

### Backup job monitoring — WHAT/WHY/HOW

**WHAT:** Capture job status, transferred bytes, dedupe ratios, synthetic full durations, immutable copy compliance.

**WHY:** Silent backup failures undermine DR/BCP attestations faster than primary array faults when ransomware events demand immutable restore points.

**HOW:** Splunk alerts on consecutive `Failed`/`Warning` statuses with deduplicated parent/child job IDs (`parentJobId`) to avoid pager storms on per-VM granularity.

### Veeam & Commvault operational analytics

**Veeam — WHAT/WHY/HOW:** Pull **Backup Enterprise Manager** SQL views or REST **`BackupSessions`**/`ReplicaSessions` endpoints via scripted inputs—fields include **`Result`,`Duration`,`TransferredSize`,`DedupRatio`,`IsIncremental`**. *Why:* Veeam dedupe anomalies precede repository fullness faster than datastore KPIs alone when synthetic fulls balloon unexpectedly. *How:* Splunk lookups translate **`JobName`** tokens into CMDB **`business_service`** fields—failed backups escalate only when SLA tiers intersect immutable retention gaps.

**Commvault — WHAT/WHY/HOW:** Forward **CommServe** Event Viewer streams (`EvMgrs_*`), **`Jobs`** XML exports, **`CVPerfMgr`** counters via ODBC pulls—normalize **`jobOptions`**/`failureReason` enumerations vendor publishes per maintenance packs. *Why:* Multi-tenant MSP overlays demand Splunk RBAC slicing **`clientGroup`**/`organizationId`. *How:* Heavy Forwarder modular ODBC inputs checkpoint **`completedJobId`** watermarks hourly—dashboards emphasize **`storagePolicyCopy`** lag minutes for air-gapped vaults.

### Vendor anchors (summary)

| Vendor | Observability hooks |
|--------|---------------------|
| NetApp ONTAP | EMS events, REST counters, Unified Manager exports |
| Dell EMC PowerStore / Unity | REST + syslog |
| Pure Storage | Pure1 REST telemetry |
| Veeam | Backup Enterprise Manager SQL/API bridges |
| Commvault | Event/Message streams |

Catalog-critical UC anchors:

| UC | Tier focus |
|----|------------|
| [Volume Capacity Trending](index.html#uc-6.1.1) | Capacity forecasting |
| [Isilon Cluster Health](index.html#uc-6.1.11) | Scale-out NAS resilience |
| [Ceph Cluster Health](index.html#uc-6.1.14) | Open-source SDS quorum narratives |
| [Pure Storage Array Health](index.html#uc-6.1.19) | All-flash endurance |

### Object storage & shared file services

**Object storage — WHAT/WHY/HOW:** Index S3-compatible access logs (`GET/PUT` latency, `503` bursts), Erasure-coded repair metrics (`repairDuration`), and lifecycle transition failures from **NetApp StorageGRID**, **Dell ECS**, **Scality RING**, or cloud-adjacent stacks when Splunk aggregates hybrid bursting patterns. *Why:* Erasure-coded rebuild windows interact with WAN replication—Splunk ties object consistency lag to VMware datastore snapshots from Category 2 when VADP-style backup targets sit on object endpoints. *How:* Heavy Forwarder batches ORC/Parquet inventory reports from lifecycle scanners; optional **Splunk Observability Cloud** OTLP bridges for modern SRE teams.

**File services — WHAT/WHY/HOW:** SMB (`Microsoft-Windows-SMBClient/Operational`) alongside NFS `rpc` timeout counters on Linux file clients provide end-host perspective on array/controller issues flagged in [Volume Capacity Trending](index.html#uc-6.1.1). *Why:* Array controllers may assert healthy yet client-side `STATUS_NETWORK_NAME_DELETED` storms indicate split-brain DFS or stale DNS pointers. *How:* Splunk correlation rules join DFS namespace events with [DNS Record Change Audit](index.html#uc-5.6.7) timelines from Category 5.

---

## Category 15: Data Center Physical Infrastructure (81 use cases)

Physical-layer resilience splits across [Power / UPS](index.html#cat-15/15.1), [Cooling / Environmental](index.html#cat-15/15.2), and [Physical Security](index.html#cat-15/15.3)—Splunk narratives converge telemetry historically siloed in BMS/BEPMS tooling.

### UPS / generators / transfer switches — WHAT/WHY/HOW

**WHAT:** Battery health metrics (`batteryReplaceIndicator`, impedance trends), estimated runtime under load, generator fuel/reserve autonomy, ATS source transfers.

**WHY:** Facilities failures produce IT incidents that appear “mysteriously random” unless Splunk overlays UPS SNMP traps with HVAC narratives—thermal excursions correlate with UPS fan faults preceding shutdown.

**HOW:** Normalize SNMP OID walks via Splunk Modular Inputs / Edge hubs—alert when runtime projections drop below contractual SLA envelopes correlated with concurrent rack PDU redundancy losses.

Critical UC anchors:

| UC | Scenario |
|----|----------|
| [UPS Battery Health](index.html#uc-15.1.1) | Cell degradation forecasting |
| [UPS Battery Runtime](index.html#uc-15.1.10) | Load-adjusted autonomy breaches |
| [Generator Fuel Level](index.html#uc-15.1.12) | Extended outage preparedness |
| [Transfer Switch Events](index.html#uc-15.1.13) | Utility/generator source transitions |

### Cooling & physical access

**WHAT:** CRAC humidity/temperature deltas, leak detection probes, rack door/badge access systems.

**WHY:** Cooling degradations silently throttle CPU turbo bins (looping back to Category 1 CPU thermals).

**HOW:** Splunk correlation rules join Meraki MT sensors (`meraki:sensorreadingshistory`) with Catalyst Center WLAN Assurance thermal overlays where dense racks threaten RF absorption anomalies—closing facilities/network causality loops.

### Physical security & access control ([Physical Security](index.html#cat-15/15.3))

**WHAT:** Integrate badge reader syslog (`ACCESS_GRANTED/DENIED`), biometric failures, elevator interlocks, video metadata markers (where privacy policies permit aggregated counts only), and intrusion-detection perimeter feeds—Splunk indexes operational summaries rather than raw PII wherever feasible.

**WHY:** Physical breaches correlate with logical pivots—Splunk timelines reconcile unauthorized badge retries with privileged VPN authentications across Category 5 firewall narratives.

**HOW:** Lookup tables anonymize **`badge_id`**/`employee_hash`; Splunk alerts threshold **`DENIED`** streaks before pairing with Catalyst Center **`client`** onboarding anomalies (`failedDot1xAttempts`) where wireless campuses intersect secured cages.


---

## Category 18: Data Center Fabric & SDN (76 use cases)

Fabric automation merges controller-led overlays ([Cisco ACI](index.html#cat-18/18.1)), VMware NSX micro-segmentation ([VMware NSX](index.html#cat-18/18.2)), generalized EVPN/VXLAN transports ([Other SDN](index.html#cat-18/18.3)), and Nexus Dashboard/NX-OS telemetry ([Nexus Dashboard](index.html#cat-18/18.4)).

### Cisco ACI (23 use cases — subcategory [Cisco ACI](index.html#cat-18/18.1))

APIC exposes hierarchical managed-object graphs—Splunk correlates faults/events across tenants transparently.

#### Health scoring — WHAT/WHY/HOW

**WHAT:** APIC assigns **health scores 0–100** with severity-weighted fault penalties propagated through MO parent/child hierarchies (`fvTenant`,`l3extOut`,`bd`,`epg`).

**WHY:** Flat syslog severity misses blast-radius prioritization—score deltas localize remediation paths faster than CLI traversal.

**HOW:** **`Splunk Add-on for Cisco ACI (`Splunkbase 4022`)** streams **`cisco:aci:faults`**, **`cisco:aci:events`**, **`cisco:aci:audit`**—Splunk dashboards bubble prioritized faults via lookups translating distinguished-name paths into human-readable tenant/EPG labels.

#### Top-down troubleshooting workflow — WHAT/WHY/HOW

**WHAT:** Traverse faults → correlated events → MO-level health deltas → drill into embedded tooling (`iPing`,`iTraceroute`, SPAN orchestrations exposed via GUI workflows mirrored by Splunk hyperlinks).

**WHY:** Operators shorten MTTR following layered causality rather than reactive SSH loops.

**HOW:** Splunk drilldown searches pivot `faultId` → `dn` → correlated `event` narratives; optional HEC ingestion of packet-capture metadata when automation exports pcap summaries.

#### Administrative visibility — WHAT/WHY/HOW

**WHAT:** Role-based visibility isolates faults per administrative domain—Splunk mirrors RBAC slices via indexed fields filtered per SOC/NOC squad macros.

**WHY:** Shared-services fabrics collapse noisy dashboards unless Splunk RBAC aligns APIC tenancy scopes.

**How:** Saved searches parameterized by `tenantRegex` macros referencing Splunk roles.

#### Critical UC anchors

| UC | Fabric narrative |
|----|------------------|
| [ACI Fabric Health Score Monitoring](index.html#uc-18.1.1) | Global spine/leaf posture |
| [Multi-Site Health](index.html#uc-18.1.17) | Inter-site contracts stretched fabrics |
| [Contract Violation and Implicit Deny Bursts](index.html#uc-18.1.20) | Policy-drop forensic timelines |
| [APIC Resource Exhaustion](index.html#uc-18.1.23) | Control-plane saturation |

#### REST endpoints and Splunk mapping — WHAT/WHY/HOW

**WHAT:** Poll APIC northbound REST namespaces—examples include **`/api/mo/uni/fvTenant`** (tenant inventory), **`/api/class/faultInst`** (active faults), **`/api/class/aaaModLR`** (audit commits). Cisco publishes fault severity taxonomy alongside MO distinguished names (`dn`) Splunk extractions mirror verbatim.

**WHY:** Splunk dashboards join REST-derived fault counts with syslog-adjacent **`cisco:aci:audit`** trails—operators prove whether automation (`apic:${source}-commit`) preceded implicit deny bursts versus silent policy drift.

**HOW:** Scripted inputs stagger intervals (`poll_interval_sec`) respecting APIC CPU guidance—bulk export **`subscribe?query-target-filter`** batches nightly while minute-level fault pulls feed alerting paths; token refresh uses APIC **`aaaLogin`** cookie lifecycle cached in Splunk credential stores.

### Cisco Nexus Dashboard & NX-OS (13 use cases — subcategory [Nexus Dashboard Fabric Controller](index.html#cat-18/18.4))

**WHAT:** Nexus Dashboard Fabric Controller (**NDFC**) aggregates NX-OS telemetry, NetFlow/IPFIX exports, overlay/underlay operational state for VXLAN/EVPN fabrics.

**WHY:** Campus Catalyst Center Assurance does not replace data-center fabrics—Splunk overlays NDFC REST + streaming telemetry alongside ACI feeds for brownfield coexistence.

**HOW:** **`Cisco DC Networking App for Splunk (`Splunkbase 7777`)** centralizes NX-OS/NDFC KPIs (`cisco:dcnetworking:*` families per packaging) with complementary `cisco:aci:*` joins on `serial`/`podId` bridging where crosswalks exist.

### VMware NSX (18 use cases)

**WHAT:** Distributed firewall hit logs, IDS/IPS service chain events, Tier-0/Tier-1 gateway HA failover semantics, GENEVE transport health.

**WHY:** Micro-segmentation shifts enforcement closer to workloads—routing anomalies manifest as firewall permit/deny bursts versus classical ICMP gaps.

**HOW:** Splunk ingestion via syslog forwarders from NSX Manager plus aggregated firewall logs normalized into Splunk Common Information Model (`Network_Traffic`,`Intrusion_Detection`) where feasible.

Critical failover UC:

| UC | Interpretation |
|----|----------------|
| [NSX Tier-0/Tier-1 Gateway HA Failover](index.html#uc-18.2.12) | Control-plane redundancy regressions |

---

## Category 19: Compute Infrastructure (72 use cases)

Compute Infrastructure merges Cisco UCS (`cat-19.1`), HyperFlex-driven HCI clusters (`cat-19.2`), and Azure Stack HCI footprints (`cat-19.3`).

### Cisco UCS (33 use cases — subcategory [Cisco UCS](index.html#cat-19/19.1))

UCS Manager exposes hierarchical faults spanning chassis/blades/FIs/service profiles—Splunk operationalizes XML API streams alongside syslog semantics.

#### Fault severity taxonomy — WHAT/WHY/HOW

**WHAT:** UCS faults categorize **critical / major / minor / warning** severities across compute/rack/blade/storage subsystems.

**WHY:** Severity classes map to escalation cadence (IMT vs proactive RMA)—mis-labeled suppressed faults erode SLA compliance.

**HOW:** Splunk lookups convert `severity` + `cause` tuples into ticket priority classes; dashboards color by canonical vendor codes.

#### FSM behavioral nuance — WHAT/WHY/HOW

**WHAT:** Prioritize monitoring for **non-FSM faults**—Finite State Machine transient faults auto-resolve during normal provisioning while hardware-level faults persist.

**WHY:** Alerting on benign FSM churn misleads pager duty; Splunk suppresses ephemeral FSM contexts when correlating success events.

**HOW:** SPL `transaction` spanning `fault` + `fsmFsm` transitions with `closed` semantics (per Cisco UCS fault reference).

#### Transport channels — WHAT/WHY/HOW

**WHAT:** Combine **XML API** pulls, **SNMP** traps, **`Fault`/`Event`/`Audit` syslogs**.

**WHY:** API streams provide structured fields (`dn`,`descr`,`severity`); syslog offers real-time propagation for link/rack sensor events before API poll windows elapse.

**HOW:** **`Splunk Add-on for Cisco UCS`** (see TA documentation for release-specific input types) configures scheduled XML API scripted inputs plus optional syslog receivers; **Splunk TA supports up to 15 UCS Managers** on approximately **8-core / 8GB** search-tier resources per sizing guidance—scale horizontally for larger fabrics.

#### CIMC memory monitoring — WHAT/WHY/HOW

**WHAT:** Track rack server CIMC memory utilization (`memory available` vs thresholds) alongside host OS memory to catch out-of-band management regressions preceding host boot failures.

**WHY:** Blade/rack BMC memory pressure can block remote remediation when host OS agents fail to start.

**How:** Dedicated modular input or SNMP OIDs mirrored into Splunk Performance index with host=`CIMC-*` naming.

#### Critical UCS UC anchors

| UC | Operational focus |
|----|-------------------|
| [Blade/Rack Server Health](index.html#uc-19.1.1) | Overall compute availability |
| [Service Profile Association Failures](index.html#uc-19.1.11) | Stateless automation breaks |
| [FI Port-Channel Errors](index.html#uc-19.1.13) | Fabric interconnect resilience |
| [Chassis PSU Redundancy Loss](index.html#uc-19.1.15) | Power-domain risk |
| [Intersight Server Alarm Monitoring](index.html#uc-19.1.19) | Cloud-managed alarm correlation |

### Cisco HyperFlex (HCI — subcategory [Hyper-Converged Infrastructure](index.html#cat-19/19.2))

**WHAT:** HX Connect / HXDP REST APIs expose cluster quorum health, replication backlog depth, storage IO latency distributions across SCSI/NFS fronts.

**WHY:** HCI collapses compute/storage networking—silent replication divergence threatens workload consistency beyond naive CPU KPI charts.

**HOW:** Splunk modular inputs authenticate REST tokens scoped per HX cluster—normalize JSON counters (`clusterHealth`,`resyncPercent`,`dedupeRatio`) into operational dashboards correlated with VMware datastore KPIs from Category 2.

### Azure Stack HCI (7 use cases)

**WHAT:** Hyper-V guarded fabric telemetry, Storage Spaces Direct health, Azure Arc linkage signals.

**WHY:** Hybrid edge footprints inherit dual observability mandates—on-prem HCI resilience plus Azure control-plane attestations.

**How:** Splunk Universal Forwarders on HCI nodes ingest Windows perfmon + cluster logs alongside Arc heartbeat streams documented under hybrid-cloud ingestion patterns.

---

## Adopting this guide in practice

Treat this document as a **domain map**, not a substitute for per-UC SPL: start with browse anchors to [Browse Network Infrastructure](index.html#cat-5) when cross-domain causality dominates (Catalyst Center Assurance + ThousandEyes SaaS KPIs + IOS-XE syslog), tighten to [Browse Server & Compute](index.html#cat-1) when host-level saturation or hardware sensor patterns lead, and escalate to [Browse Data Center Fabric & SDN](index.html#cat-18) / [Browse Compute Infrastructure](index.html#cat-19) when controller-led fabrics or blade chassis narratives explain outages unreachable via SNMP alone.

Minimum viable Splunk pairing checklist:

1. Deploy vendor TA packages aligned with onboarded sourcetypes (`Splunk_TA_nix`,`Splunk_TA_windows`,`TA_cisco_catalyst`,`Splunk_Add-on_for_VMware`,`Splunk_Add-on_for_Cisco_ACI`).
2. Normalize identification (`serial`,`deviceId`,`tenant`,`business_service`) via nightly lookups bridging CMDB exports.
3. Route critical UCS anchors ([Blade/Rack Server Health](index.html#uc-19.1.1)), resilient IOS narratives ([HSRP/VRRP State Changes](index.html#uc-5.1.23)), virtualization datastore runway ([Datastore Capacity Trending](index.html#uc-2.1.3)), and ThousandEyes SaaS probes ([HTTP Server Availability Monitoring (ThousandEyes)](index.html#uc-5.9.34)) into rehearsed incident bridges—Splunk becomes the forensic ledger tying assurance APIs to packet-path realities without swapping consoles mid-severity event.
