---
title: Collaboration & IoT/OT Monitoring Domain Guide
type: domain-guide
domains: [Collaboration, IoT, OT]
categories: [11, 14]
last_updated: 2026-04-30
---

# Collaboration & IoT/OT Monitoring Domain Guide

This guide connects human collaboration telemetry (mail, identity, unified communications, video) and operational technology (buildings, ICS, edge ingest, OT security) to Splunk-ready data contracts. It follows Cisco gold-standard patterns where the catalog emphasizes Cisco Webex, Cyber Vision, and Edge Intelligence, while remaining accurate for Microsoft 365, Google Workspace, and generic OT protocols documented in IEC 62443 and NIST SP 800-82.

Practitioners should read this guide alongside **Microsoft Learn** references for Graph permissions, **Cisco’s** Webex and Cyber Vision administration guides for sensor placement, and **Splunk Lantern** onboarding articles for OT sourcetype hygiene. Where exact REST paths evolve, defer to vendor release notes—the catalog’s Splunk searches remain contractually anchored to normalized fields rather than brittle URL patterns.

Telemetry programs succeed when leadership funds **both** SaaS audit subscriptions and OT span infrastructure; half-deployed Graph APIs or half-racked Cyber Vision sensors produce false confidence. Treat identity compromise as a race between **[Inbox Rule Monitoring](../../index.html#uc-11.1.8)** detectors and attacker dwell time; treat OT compromise as a physics problem first—loss of **[Process Variable Anomalies](../../index.html#uc-14.2.2)** visibility often means you only learn about failure from human phone calls after the flare stack already lit.

Browse the catalog pillars: [Browse Email & Collaboration](../../index.html#cat-11) · [Browse IoT & Operational Technology](../../index.html#cat-14).

---

## Category 11: Email & Collaboration (107 use cases)

Category 11 organizes collaboration risk and reliability into **[Microsoft 365 / Exchange](../../index.html#cat-11/11.1)** (12), **[Google Workspace](../../index.html#cat-11/11.2)** (18), **[Unified Communications](../../index.html#cat-11/11.3)** (57), **[Mail Transport](../../index.html#cat-11/11.4)** (8), and **[Video Conferencing](../../index.html#cat-11/11.5)** (12). Cisco gold-standard coverage concentrates Webex Meetings, Calling, device telemetry, and adjacent Cisco UC/security stacks—paired with SaaS audit planes so defenders see policy drift before mail rules forward data offshore.

Subcategory counts illustrate where practitioners spend discovery hours: Unified Communications dominates because PSTN modernization, hunt groups, Contact Center integrations, and hybrid Webex Calling estates multiply sourcetypes faster than mailbox-only deployments.

Subcategory mapping is indicative—adjust priorities after inventorying which SaaS connectors already carry OAuth tokens on your Heavy Forwarders.

### Microsoft 365 vendor guidance

Microsoft publishes separate planes for **audit** versus **mail-flow diagnostics**. Splunk practitioners should treat them as complementary—not interchangeable—telemetry streams.

**Management Activity API (audit plane)**

- **WHAT:** Unified Graph-backed audit records for administrative actions and user-driven changes across Exchange Online, SharePoint, Entra ID–integrated workloads, and PowerShell cmdlet execution captured where licensing permits unified auditing.
- **WHY:** Policy violations (mailbox forwarding, suspicious inbox rules, privilege escalations) rarely surface in SMTP logs alone; audit narratives anchor WHO changed WHAT before outcomes appear in abuse-mailbox complaints or DMARC aggregate failures.
- **HOW:** Route audit feeds through **`Splunk Add-on for Microsoft Cloud Services`** (`Splunk_TA_MS_O365`, Splunkbase 3110) into normalized sourcetypes such as `ms:o365:management`. Correlate `Operation`, `UserId`, target objects, and geo/IP enrichment where available; retain sufficient retention for insider-threat investigations aligned to organizational records-management policy.

**Message trace (delivery plane)**

- **WHAT:** Per-message tracking across connectors, routing hops, deferrals, and failures—distinct from mailbox audit trails.
- **WHY:** Delivery delays masquerade as “Outlook slowness” while root causes live in connector health, DNS/MX regressions, or transport-rule loops.
- **HOW:** Index **`ms:o365:messageTrace`** (per catalog UC implementations) with hourly aggregates split by failure taxonomy; threshold against trailing median rather than static counts so seasonal mail bursts do not flood paging.

**Inbox-rule monitoring for compromise detection**

- **WHAT:** Detection logic targeting auto-forward and deletion rules consistent with BEC tradecraft (silent data diversion).
- **WHY:** Attackers stabilize persistence post-phish by hiding malicious transport paths inside mailbox automation invisible to perimeter defenses.
- **HOW:** Operationalize **[Inbox Rule Monitoring](../../index.html#uc-11.1.8)**—critical tier—with SPL filtering external forwards not aligned to sanctioned domains and alerting within minutes of creation alongside **[Mail Flow Health Monitoring](../../index.html#uc-11.1.1)**.

**Google Workspace parity**

Workspace exposes login telemetry separately from admin audit APIs; **[Login Anomaly Detection](../../index.html#uc-11.2.4)** illustrates **`Splunk Add-on for Google Workspace`** ingestion (`gws:login`) with brute-force clustering suitable as a crawl-layer anchor before richer UEBA fusion.

### Extended Microsoft 365 operations (hybrid & assurance)

**Exchange Online Protection and policy logs**

- **WHAT:** Anti-spam/anti-malware verdicts, transport rules, DLP policy hits, and Safe Links detonations captured in message-trace adjacent exports and security dashboards.
- **WHY:** Users experience “mail delay” when policy engines quarantine bulk mail; without policy-specific fields, ops blames networking while compliance teams need proof of control activation.
- **HOW:** Split searches: one macro for pure transport failure (connector, DNS, resource forest) feeding **[Mail Flow Health Monitoring](../../index.html#uc-11.1.1)**, another for `Policy` dimensions so SecOps correlates spikes in `JunkEmail` or `Phish` verdicts with user training cohorts—never collapse them into one undifferentiated “bad mail” KPI.

**Defender / Entra signals (conceptual alignment)**

Where Microsoft Defender for Office 365 surfaces phish campaigns, ensure alert IDs and investigation GUIDs flow into Splunk (Graph security API or SIEM forwarding) so **[Inbox Rule Monitoring](../../index.html#uc-11.1.8)** alerts can be suppressed when the same tenant is already under active IR with expected admin activity.

**Records for legal & HR holds**

- **WHAT:** Immutable audit trails for mailbox litigation holds, eDiscovery jobs, and privileged mailbox access.
- **WHY:** SEC/FTC-style investigations ask for timeline integrity, not just “we have Splunk.”
- **HOW:** Mirror hold-status change events into a restricted index; document chain-of-custody in saved-search descriptions tied to UC governance text.

---

### Cisco Webex (Unified Communications & Video Conferencing)

Webex publishes OAuth 2.0–authenticated REST endpoints under `https://webexapis.com/v1/` for meetings administration, participants, recordings, devices, xAPI adjacent resources, and Calling/Contact Center analytics depending on entitlement. Cisco’s documentation emphasizes least-privilege integrations, rotating client credentials or authorization-code flows tied to scoped admin consent, and separating “read analytics” integrations from privileged device-control scopes.

**Meeting quality & engagement**

- **WHAT:** Meeting-level metrics—latencies, loss, bitrate, participant join/leave cadence—exposed via analytics and summary reporting patterns (implementation varies by tenant feature set).
- **WHY:** Executive video is a revenue-critical channel; degradations correlate with ISP path issues, VPN hairpins, or oversubscribed VPN concentrators—not only Webex cloud faults.
- **HOW:** Combine Webex Meetings add-on sourcetypes with network path telemetry (ThousandEyes, SD-WAN, campus Wi-Fi) to triage “audio only” incidents; anchor operational views to catalog UCs such as **[Meeting Room No-Show and Early Release Trending](../../index.html#uc-11.5.9)** where room IoT occupancy disambiguates wasted video minutes from codec problems.

**CDR via Webex Calling API**

Call Detail Records underpin toll-fraud analytics, hunt-group efficiency, and PSTN spend governance. **[Webex Calling Queue Performance and SLA](../../index.html#uc-11.3.16)** demonstrates queue-level abandon rates and wait-time SLAs sourced from Calling analytics patterns—pair with **[Webex License Utilization and Adoption Tracking](../../index.html#uc-11.3.20)** so finance sees paid entitlements mapped to behavioral reality.

**Contact Center integration (SplunkBridge pattern)**

Enterprise Webex Contact Center frequently lands as JSON/HEC pipelines or middleware “bridge” forwards. **WHAT/WHY/HOW:** Treat bridge events as first-class sourcetypes with schema tests; failures in the bridge appear as silent data loss unless you alert on ingestion gap detectors against expected message rates per skill group.

**Security & admin audit**

Admin change events (device moves, calling policies, integration scopes) complement meetings telemetry when proving SOC 2–style change control over UC infrastructure—tie forwarders into restricted indexes where contractual obligations mandate segregation.

**Splunk technical attachments (Splunkbase references per catalog)**

| App / TA | Approx. Splunkbase ID | Role |
|---------|------------------------|------|
| Cisco Webex Meetings Add-on | 4991 | Meetings history & participant narratives |
| Cisco Webex App | 4992 | Operational dashboards packaged by Cisco |
| Cisco Webex REST Add-on | 5781 | REST modular inputs / token-managed collectors |

Representative normalized sourcetypes called out across UC authoring include **`cisco:webex:meetings:history`**, **`cisco:webex:meetings:attendee`**, **`cisco:webex:calling:cdr`**, **`cisco:webex:audit`**—normalize timestamps to UTC before SLA math spanning daylight-saving transitions.

**API cadence, throttling, and secret rotation**

- **WHAT:** REST pagination, `429` backoff policies, and separate rate pools for heavy admin exports vs high-cardinality device telemetry.
- **WHY:** Under-provisioned poll intervals create holes that SecOps misreads as “user went dark” when the integration simply tripped Cisco API guardrails.
- **HOW:** Exponential backoff in modular inputs, shard collections per region or Webex org, and rotate OAuth refresh tokens on a documented calendar with break-glass procedures—store secrets in Splunk credential stores or external vaults referenced via REST credential stanzas rather than plaintext `inputs.conf`.

**Meeting quality scores & participant engagement**

Cisco-collateral discussions often cite MOS-like constructs for audio/video channels plus engagement proxies (screenshare duration, dominant speaker switches, reconnect counts). **WHAT:** Structured KPIs emitted per meeting or per participant slice. **WHY:** Helps isolate last-mile Wi-Fi congestion vs backbone loss—critical when **[Meeting Room No-Show and Early Release Trending](../../index.html#uc-11.5.9)** proves rooms were booked yet codec logs show zero packet loss (hinting scheduling discipline issues rather than AV faults). **HOW:** Align meeting IDs across Webex APIs and calendar integrations; deduplicate recurring series before trending weekly averages.

**Cross-domain troubleshooting narrative**

Run tabletop exercises that chain **[Mail Flow Health Monitoring](../../index.html#uc-11.1.1)** → transport connectors → **[SMTP Service Availability](../../index.html#uc-11.4.1)** → perimeter spam verdict when phishing simulations spike—then pivot to **[Webex Calling Queue Performance and SLA](../../index.html#uc-11.3.16)** if PSTN carriers throttle concurrent invites during the same incident window.

---

**[Webex Room System Uptime](../../index.html#uc-11.5.5)** tracks device connectivity regressions (`webex:device`) suitable for bridge-before-war-room workflows alongside **[SMTP Service Availability](../../index.html#uc-11.4.1)** when hybrid mail-flow troubleshooting spans Cisco **ESA** gateways.

---

### Cisco Unified Communications Manager (UCM)

UCM emits **CDR** (billing-grade call records) and **CMR** (quality diagnostics merged into analytics pipelines). **WHAT:** Per-call QoS vectors and endpoint identity. **WHY:** Voice teams still justify capacity; security teams hunt priv-dial fraud. **HOW:** Ingest via **`Cisco UCM`** technology add-ons per deployment guide, align device/line fields to Identity lookup tables, and monitor anomalous international patterns in parallel with Webex Calling CDR when hybrid PSTN exits exist.

---

### Cisco Email Security Appliance (ESA) — Mail transport

ESA enforces SMTP policy, anti-abuse pipelines, DKIM/DMARC alignment checks, and suspected phish workflows. **WHAT:** Mail policy decisions and verdicts at the MTA boundary. **WHY:** Cloud mail alone cannot prove loop resolution when hybrid transport includes on-prem relays. **HOW:** Syslog or AMP/async feeds into Splunk with sender/recipient hashing where GDPR minimization applies—coordinate with **[Mail Flow Health Monitoring](../../index.html#uc-11.1.1)** when transport bifurcates across O365 connectors and ESA hops.

When investigators reconstruct timelines after credential phishing, combine ESA verdict fields with **[Inbox Rule Monitoring](../../index.html#uc-11.1.8)** outcomes so narrative clarity survives corporate counsel review—Splunk retains immutable `_time` ordering while mail admins rotate quarantine policies; documenting correlation macros prevents analysts from retyping seventeen SPL fragments mid-war-room.

---

### Collaboration adoption checklist (WHAT / WHY / HOW)

| Practice | WHAT | WHY | HOW |
|---------|------|-----|-----|
| Separate audit vs delivery telemetry | Distinct schemas (`management` vs `messageTrace`) | BEC investigations die when analysts mix unrelated signals | Dedicated macros per plane |
| Anchor identity narratives | Forward rule alerts tied to **[Inbox Rule Monitoring](../../index.html#uc-11.1.8)** | Prevent irreversible data theft during dwell time | Lookup sanctioned domains + SOC workflow |
| UC spend governance | License versus behavioral adoption | CFO scrutiny on collaboration Opex | **[Webex License Utilization and Adoption Tracking](../../index.html#uc-11.3.20)** |
| Room intelligence | Occupancy vs booking waste | Facilities cost recovery | **[Meeting Room No-Show and Early Release Trending](../../index.html#uc-11.5.9)** |

---

## Category 14: IoT & Operational Technology (230 use cases)

**[Browse IoT & Operational Technology](../../index.html#cat-14)** spans Building Management Systems (47), ICS/SCADA (28), **Splunk Edge Hub** (56), IoT platforms (19), MQTT/OPC-UA (22), Zeek ICS (20), Litmus Edge (9), trending/novel patterns (4), and **Cisco Cyber Vision / Nozomi** (25). Cisco gold-standard narratives emphasize Cyber Vision’s passive discovery and Splunk-bound OT flows alongside Edge Intelligence pipelines shipping industrial workloads into HTTP Event Collector endpoints.

---

### Cisco Cyber Vision (subcategory 14.9)

Cyber Vision sensors perform deep-packet visibility across OT VLANs while central managers correlate asset identities, vulnerabilities, and behavioral anomalies—consistent with Cisco-validated architectures through approximately **release 5.3.x** lines referenced in Cisco administration collateral.

**Administrative pillars (WHAT / WHY / HOW)**

| Guidance theme | WHAT | WHY | HOW |
|----------------|------|-----|-----|
| Preset categories | Starter asset classes (“OT devices”, controller families, CSMS tooling) | Accelerates analyst intuition during rollout | Clone presets into customer-named groups before production segmentation maps freeze |
| Baselines | Separate weekday/weekend profiles | OT loads swing between continuous chemical batches vs planned outage windows | Train anomaly windows per asset group with exclusion calendars |
| Subnetwork posture | Tag ranges internal vs external | Risk scoring algorithms weigh exposure differently per perimeter assumption | Import IP plans from PCM exports; reconcile quarterly |
| IDS overlays | Snort/Suricata-class rules where sensors permit | Detect exploit sequences invisible to pure allow/deny telemetry | Tune suppression lists after vendor PLC upgrades spike benign signatures |

**Splunk-facing telemetry**

Expose REST-exported inventories plus syslog **CEF** streams where syslog-ng/sc4s pipelines normalize severity. Canonical sourcetypes appearing across UC implementations include **`cisco:cybervision:components`**, **`cisco:cybervision:flows`**, **`cisco:cybervision:events`**, **`cisco:cybervision:vulnerabilities`**—each answering different investigative pivots (inventory drift vs lateral movement vs vuln SLA).

**Representative Cyber Vision catalog anchors**

- **[OT Asset Discovery and Inventory Tracking](../../index.html#uc-14.9.1)** — authoritative OT CMDB enrichment feeding IEC 62443 evidence packs.
- **[New Communication Flow Detection](../../index.html#uc-14.9.12)** — east-west surprises after segmentation projects.
- **[Protocol Exception Monitoring](../../index.html#uc-14.9.13)** — deterministic PLC chatter disrupted by scanners or ransomware staging.
- **[Snort IDS Threat Detection on OT Networks](../../index.html#uc-14.9.6)** — sensor-backed IDS overlays correlated with firewall denies.

Splunk linkage honors MITRE ICS tactics only when ICS-protocol parsers preserve temporal causality—avoid naive union with IT IDS noise without VLAN attribution.

**Risk scoring prerequisites**

Cyber Vision assigns exposure scores influenced by patch cycles, segmentation posture, and observed lateral vectors— Splunk dashboards should annotate whether scores assumed internal-only OT subnets versus internet-adjacent segments per Cisco guidance on subnetwork tagging. When **[New Communication Flow Detection](../../index.html#uc-14.9.12)** fires during maintenance windows, temporarily suppress correlated vulnerability SLA breaches so vulnerability-management teams chase genuine zero-day exposures—not contractor laptops running legitimate PLC uploads.

---

### Cisco Edge Intelligence

Edge Intelligence executes on industrial routers (**IR1101**, **IR829**), **IC3000** compute gateways, and select **Catalyst IE** switches—close to sensors where OPC-UA subscriptions would choke WAN links.

**Pipeline WHAT/WHY/HOW**

| Stage | WHAT | WHY | HOW |
|-------|------|-----|-----|
| Source | PLC tags, MQTT topics, serial payloads | Keeps deterministic loops local | Configure redundancy when pulling Modbus holding registers |
| Transform | Data Rules / Data Logic (JavaScript) | Normalize vendor quirks before Splunk taxes indexers | Unit-test transforms against captured PCAP extracts |
| Destination | Splunk HEC batch vs single-event modes | Balance latency vs indexer ACK overhead | Tune batch KB thresholds per uplink |

**Edge filtering discipline—**send on change**, **deadband analog swings**, aggregate high-frequency vibration FFT buckets—mirrors Splunk OT economics guidance and **[Temperature Anomaly Detection](../../index.html#uc-14.3.1)** Edge Hub modeling references.

Document JavaScript transforms under Git revision control—OT engineers deserve diff reviews identical to PLC ladder edits because faulty Data Logic accidentally multiplying torque readings contaminates Splunk ML models downstream.

---

### Splunk Edge Hub (subcategory 14.3)

Edge Hub bundles compute near harsh environments with onboard sensors (temperature/humidity/vibration depending on SKU) plus protocol adapters (**MQTT**, **OPC-UA**, **Modbus**, **SNMP**, **BACnet**). Pair **[Temperature Anomaly Detection](../../index.html#uc-14.3.1)** with building-mechanical historians when merging OT/facilities narratives.

**Commissioning checklist**

- **WHAT:** Sensor calibration proofs, MQTT broker ACL matrices, OPC-UA endpoint certificates, Modbus register maps frozen under change control.
- **WHY:** Edge deployments fail when OT ships registers documented only inside vendor PDFs rather than Splunk lookups—analytics teams tune thresholds against meaningless integers.
- **HOW:** Maintain CSV lookups (`plc_register_meaning.csv`) versioned beside Splunk apps; rehearse failover where Edge Hub loses uplink yet buffers locally—dashboard ingest lag detectors accordingly.

---

### IoT platforms, Litmus Edge, and emerging collectors

Enterprise IoT platforms (asset trackers, cold-chain logistics, OEM-managed MQTT namespaces) frequently arrive ahead of standardized Splunk TAs.

**WHAT:** Vendor-specific JSON schemas emitted via HTTPS webhooks or Kafka-compatible feeds.

**WHY:** Supply-chain sensors warn before refrigeration breaches spoil payloads—finance cares because insurance riders demand proof-of-temperature telemetry.

**HOW:** Normalize early via Heavy Forwarder transforms (`props.conf` `SEDCMD`, `EVAL-*`) before indexing—avoid indexing raw nested JSON blobs without extraction plans; correlate vendor asset IDs with ERP shipment IDs via lookups.

Litmus Edge deployments often mirror Edge Intelligence topology—prioritize deterministic tagging (`customer`, `site`, `line`) before Splunk-side **[PLC/RTU Health Monitoring](../../index.html#uc-14.2.1)** joins succeed across acquisitions.

---

### ICS / SCADA & industrial protocols

**WHAT:** **[PLC/RTU Health Monitoring](../../index.html#uc-14.2.1)** proves CPU/memory/comm wedges before HMIs freeze.

**WHY:** OT downtime compounds faster than IT latency SLO breaches—lost batches vs slower Outlook sync.

**HOW:** OPC-UA metrics sourcetypes (`opcua:metrics`) + Modbus TA polls aligned to PLC vendor scan budgets—never oversample deterministic racks without OT engineering approval.

Process stewardship anchors:

- **[Process Variable Anomalies](../../index.html#uc-14.2.2)** — analog breaches predicting mechanical faults.
- **[Safety System Activation](../../index.html#uc-14.2.3)** — interlocks proving IEC 61511 narratives post-trip.

Facility overlays critical for regulated estates:

- **[SNMP Trap Storm Detection](../../index.html#uc-14.1.10)** — protects collectors when firmware storms after power blips.
- **[Water Leak Detection and Flood Alerts (Meraki MT)](../../index.html#uc-14.1.18)** — physical loss prevention in IDF closets.
- **[Domestic Hot Water Temperature Compliance (Legionella Prevention)](../../index.html#uc-14.1.40)** — public-health compliance telemetry from **`bms:water`** pipelines.

---

### Industrial frameworks — IEC 62443 & NIST SP 800-82

**Network segmentation (Purdue levels 0–5)**

- **WHAT:** Explicit zoning—field devices through DMZ historians into enterprise Splunk indexers.
- **WHY:** Lateral ransomware propagation historically exploited flat OT VLANs—segmentation raises attacker cost.
- **HOW:** Document conduit rules (who may initiate flows) and mirror enforcement logs into Splunk correlation searches referencing **`edge_hub`** + firewall denies.

**Asset inventory foundation**

Without authoritative OT inventory, vulnerability dashboards lie—Cyber Vision **[OT Asset Discovery and Inventory Tracking](../../index.html#uc-14.9.1)** feeds IEC zones/conduits mappings demanded during IEC 62443 assessments.

**Baseline-driven anomaly detection**

Mirrors Cisco baseline guidance—pair **[Temperature Anomaly Detection](../../index.html#uc-14.3.1)** outputs with seasonal overlays before declaring latent refrigeration faults.

**NIST SP 800-82 Rev.3 emphasis — control-system resilience**

The NIST Guide to ICS Security stresses inventory, monitoring, segmentation, least privilege, and contingency planning—not merely antivirus refresh cadences.

- **WHAT:** Continuous visibility into controller firmware versions, backup restoration drills, remote-access gateways, and vendor remote-maintenance sessions.
- **WHY:** Regulators (NERC CIP adjacent sectors, EPA water directives, FDA manufacturing) increasingly ask for proof that OT cyber programs mirror operational reality—not checkbox PDFs disconnected from Splunk indexes.
- **HOW:** Align **[Admin Connection Detection to ICS Assets](../../index.html#uc-14.9.15)** style narratives with actual VPN logs and Cyber Vision flows so evidence bundles enumerate every engineering laptop crossing into Purdue Level 2 during turbine outage weekends.

---

### Cisco Cyber Vision alongside Nozomi-style ecosystems

Dual-sensor estates appear when enterprises adopt Cisco Cyber Vision for segmentation-aware visibility yet retain specialized ICS DPI platforms for legacy workflows.

**WHAT:** Parallel inventories risk divergent CMDB rows.

**WHY:** Duplicate asset counts undermine **[OT Asset Discovery and Inventory Tracking](../../index.html#uc-14.9.1)** evidence unless reconciliation jobs deduplicate MAC/OUI plus hostname facets.

**HOW:** Establish Splunk lookups keyed on immutable OT identifiers (serial numbers from passive banners where stable) and weekly reconciliation dashboards showing drift percentages above tolerances—route discrepancies to OT engineering before auditors cite control gaps.

---

### Priority UC lattice (critical excerpts)

| Risk theme | Representative UC |
|------------|-------------------|
| Collaboration SLA | **[Mail Flow Health Monitoring](../../index.html#uc-11.1.1)** |
| BEC persistence | **[Inbox Rule Monitoring](../../index.html#uc-11.1.8)** |
| SaaS identity drift | **[Login Anomaly Detection](../../index.html#uc-11.2.4)** |
| Trap amplification | **[SNMP Trap Storm Detection](../../index.html#uc-14.1.10)** |
| Facility safety | **[Water Leak Detection and Flood Alerts (Meraki MT)](../../index.html#uc-14.1.18)** |
| Public-health HVAC water | **[Domestic Hot Water Temperature Compliance (Legionella Prevention)](../../index.html#uc-14.1.40)** |
| ICS reliability | **[PLC/RTU Health Monitoring](../../index.html#uc-14.2.1)** · **[Process Variable Anomalies](../../index.html#uc-14.2.2)** · **[Safety System Activation](../../index.html#uc-14.2.3)** |
| OT monitoring posture | **[OT Event Severity Distribution and Security Posture Dashboard](../../index.html#uc-14.9.23)** |

---

### Building Management Systems (BMS) — bridges between facilities and OT

Building telemetry often rides **BACnet/IP**, **Modbus**, or proprietary gateways merging HVAC, access control, and life-safety endpoints. **WHAT:** Temperature, airflow, compressor status, valve positions, leak ropes. **WHY:** Facilities outages precede compute outages—humidity excursions ruin tape libraries before CRAC alarms reach NOC dashboards. **HOW:** Normalize BACnet object IDs into stable keys (`building`, `floor`, `ahu`, `vav`) before Splunk dashboards; pair mechanical narratives with **[Water Leak Detection and Flood Alerts (Meraki MT)](../../index.html#uc-14.1.18)** when IoT sensors augment traditional BMS leak probes.

Operational hygiene demands separating **comfort optimization** datasets from **compliance-critical** feeds—Legionella governance belongs with **[Domestic Hot Water Temperature Compliance (Legionella Prevention)](../../index.html#uc-14.1.40)** retention policies, not with generic occupancy analytics indexes lacking audit-grade timestamps.

---

### MQTT, OPC-UA, and fieldbus orchestration

**MQTT broker hygiene**

- **WHAT:** Topic namespaces (`plant1/line3/press/vibration`) with QoS selection (0/1/2) and retained-message policies.
- **WHY:** Misconfigured wildcard subscriptions replicate millions of redundant readings into Splunk, collapsing indexer queues during commissioning weekends.
- **HOW:** Edge Intelligence or Edge Hub pipelines filter at publish-time—subscribe narrowly, aggregate windows locally, ship anomaly vectors upstream only.

**OPC-UA security modes**

Microsoft OPC Foundations guidance distinguishes None/Basic128Rsa15/Basic256Sha256 suites—production deployments should abandon anonymous endpoints. **WHAT:** Signed/encrypted sessions with certificate pinning. **WHY:** Credential theft across PLCs historically exploited plaintext OPC tunnels from HMIs to historians. **HOW:** Align Splunk ingestion hosts inside Purdue Level 3 DMZ zones with mutual TLS wherever UA clients expose browsing beyond loopback.

---

### Zeek ICS & passive packet analytics

Zeek (formerly Bro) ICS scripts fingerprint Modbus function bursts, BACnet Who-Is storms, and DNP3 anomalies without injecting master polls—critical where active scanning violates vendor warranties.

**WHAT/WHY/HOW triad**

| Dimension | Detail |
|-----------|--------|
| WHAT | Zeek `.log` streams (`conn`, `modbus`, specialized ICS scripts) forwarded via syslog or raw file tails |
| WHY | Passive analytics catch ARP/election storms that SNMP polling misses |
| HOW | Dedicated Heavy Forwarders on SPAN taps; never co-locate with enterprise DNS resolvers that reorder packets |

Combine Zeek-derived session tables with **[Protocol Exception Monitoring](../../index.html#uc-14.9.13)** outputs so analysts distinguish vendor bugs from malicious scanning.

---

### Protocol inventory, decode health, and resilience

Catalog UCs emphasize meta-monitoring—knowing when telemetry lies:

- **[OT Protocol Usage Analysis and Inventory](../../index.html#uc-14.9.24)** — answers “which ICS dialects dominate each VLAN?” before firewall policy changes silently drop needed UDP ports.
- **[Decode Failure and Malformed Packet Detection](../../index.html#uc-14.9.25)** — surfaces parser mismatches after firmware bumps so Cyber Vision or Zeek stops silently under-counting flows.
- **[Network Redundancy and HA Failover Events](../../index.html#uc-14.9.19)** — ties ring/PRP redundancy flaps to historian gaps when OT networks reconverge.

These three practices share a discipline: **instrument the instrumentation**. **WHAT:** Health metrics on collectors, parsers, and span-feed availability. **WHY:** OT IR teams burn hours chasing ghosts when half the packets never reached Splunk. **HOW:** Synthetic poll checks, file-age monitors on Zeek queues, and HEC ACK ratio dashboards per Edge Intelligence destination.

---

### Splunk OT Intelligence & data-model alignment

Where deployments adopt **Operational Telemetry** or **CIM** extensions, enforce field aliasing (`metric_name`, `metric_value`, `asset_id`) per Splunk OT documentation so facility teams and plant engineers share dashboards without rebuilding extractions—especially when **[Temperature Anomaly Detection](../../index.html#uc-14.3.1)** outputs must join Cyber Vision asset families.

---

### Runbooks tying collaboration outages to OT dependencies

Enterprise reality: executive Webex bridges depend on HVAC keeping IDF closets within spec—correlate **[Webex Room System Uptime](../../index.html#uc-11.5.5)** with **[SNMP Trap Storm Detection](../../index.html#uc-14.1.10)** when PDUs spam traps after cooling loss. **WHAT:** Cross-domain correlation models. **WHY:** Siloed NOC vs facilities vs AV teams prolong MTTR when symptoms appear as “bad video.” **HOW:** Host-level macros linking `device_id` in Webex to Meraki switch ports and BMS points via CMDB lookups.

---

### KPIs and review cadences

Sustaining these domains requires recurring reviews that treat telemetry completeness as a first-class control.

**Collaboration KPI basket**

- **WHAT:** Weekly trending for **[Mail Flow Health Monitoring](../../index.html#uc-11.1.1)** defer/fail percentages, **[Inbox Rule Monitoring](../../index.html#uc-11.1.8)** alert aging, **[Webex Calling Queue Performance and SLA](../../index.html#uc-11.3.16)** abandon-rate deltas, **[Login Anomaly Detection](../../index.html#uc-11.2.4)** cluster counts by geography.
- **WHY:** Dashboards abandoned after launch decay—leadership forgets integrations expire silently when OAuth certificates lapse.
- **HOW:** Quarterly tabletop tying SOC escalations to UC ops owners with RACI overlays; automate JIRA or ServiceNow tickets when OAuth renewal windows approach (`inputs.conf` certificate fingerprints monitored via scripted alerts).

**OT KPI basket**

- **WHAT:** Trap-rate stability (**[SNMP Trap Storm Detection](../../index.html#uc-14.1.10)** baselines), historian ingest latency vs **[PLC/RTU Health Monitoring](../../index.html#uc-14.2.1)** poll cycles, Cyber Vision backlog queues vs **[Decode Failure and Malformed Packet Detection](../../index.html#uc-14.9.25)** spikes.
- **WHY:** OT availability SLAs frequently cite “five nines” aggregate uptime yet hide brittle collectors—the KPI stack above exposes ingestion fragility before turbines interpret phantom faults.
- **HOW:** Monthly OT governance forums pairing ICS engineers with Splunk admins; escalate firewall ACL edits needed after **[New Communication Flow Detection](../../index.html#uc-14.9.12)** positives validate legitimate contractor laptops rather than malware sweeps.

**Unified narrative for CIO/BISO forums**

Storylines blend **[Mail Flow Health Monitoring](../../index.html#uc-11.1.1)** reliability alongside **[Snort IDS Threat Detection on OT Networks](../../index.html#uc-14.9.6)** alert fidelity—proving coordinated resilience investments rather than isolated tool budgets.

---

### Getting started checklist

1. **Microsoft 365 audit plane first** — Management Activity API via `Splunk_TA_MS_O365`. Without audit trails, inbox rule compromises go undetected ([Inbox Rule Monitoring](../../index.html#uc-11.1.8)).
2. **Mail flow health second** — message trace ingestion for delivery diagnostics separate from audit ([Mail Flow Health Monitoring](../../index.html#uc-11.1.1)).
3. **Cisco Webex CDR and meetings third** — Webex REST APIs for calling analytics and meeting quality. Pair with ThousandEyes path data when available ([Webex Calling Queue Performance and SLA](../../index.html#uc-11.3.16)).
4. **OT asset inventory fourth** — Cisco Cyber Vision passive discovery before deploying IDS rules. You cannot protect what you cannot enumerate ([OT Asset Discovery and Inventory Tracking](../../index.html#uc-14.9.1)).
5. **Edge Hub / Edge Intelligence commissioning fifth** — validate register maps, MQTT topic ACLs, and OPC-UA certificates under change control before trusting sensor readings ([Temperature Anomaly Detection](../../index.html#uc-14.3.1)).
6. **ICS protocol baselines sixth** — train weekday/weekend anomaly windows before enabling alerting on Cyber Vision or Zeek ICS outputs ([Protocol Exception Monitoring](../../index.html#uc-14.9.13)).
7. **Cross-domain correlation last** — link Webex device health to facility BMS telemetry via CMDB lookups for war-room readiness ([Webex Room System Uptime](../../index.html#uc-11.5.5)).

---

### Closing stance

Treat collaboration telemetry as identity-centric continuity insurance—pair **[Mail Flow Health Monitoring](../../index.html#uc-11.1.1)** with **[Webex Calling Queue Performance and SLA](../../index.html#uc-11.3.16)** when hybrid PSTN paths blur accountability. Treat OT telemetry as physics-backed assurance—Cyber Vision inventories (**[OT Asset Discovery and Inventory Tracking](../../index.html#uc-14.9.1)**) supply the denominator for **[Snort IDS Threat Detection on OT Networks](../../index.html#uc-14.9.6)** numerators so SOC tiers spend cognitive budget on causal chains—not arguing whether assets exist.
