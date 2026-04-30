---
title: Security Monitoring Domain Guide
type: domain-guide
domains: [Security]
categories: [9, 10, 17]
last_updated: 2026-04-30
---

# Security Monitoring Domain Guide

Splunk’s value in security operations comes from correlating identity signals, control-plane telemetry from security infrastructure, and network-enforcement context into coherent detection narratives—not from collecting “more syslog” without priority. This guide orients architects and SOC engineers to three catalogue pillars—[Browse Category](../../index.html#cat-9) (**Identity & Access Management**), [Browse Category](../../index.html#cat-10) (**Security Infrastructure**), and [Browse Category](../../index.html#cat-17) (**Network Security & Zero Trust**)—with vendor-grounded ingestion advice, Cisco gold-standard paths where the catalogue marks them, and explicit links into the use-case library so you can jump from concept to executable content in one click.

### Who should read this

**Security architects** use the guide to sequence data onboarding—starting with authoritative identity stores before east-west IDS floods obscure correlation budgets. **SOC engineers** leverage Cisco-specific Splunkbase identifiers, sourcetypes, and syslog semantics (MnT aggregation, FMC threat prioritization, ASA VPN classes) to avoid repeating deployment mistakes documented across Cisco validated designs. **GRC partners** trace catalogue coverage back to measurable controls—pair [NAC Policy Change Audit](../../index.html#uc-17.1.8) evidence with firewall rule drift analytics when auditors ask how network admission policies tie to change tickets.

### Principles repeated throughout

1. **Prioritize high-fidelity security slices** (IPS verdicts, sandbox outcomes, posture failures) ahead of volumetric connection archives unless hunts explicitly demand flow telemetry.
2. **Normalize into CIM** wherever vendor TAs support it—downstream Enterprise Security, ESCU, and MLTK content assumes normalized fields (`user`, `src`, `dest`, `signature`).
3. **Preserve forensic timestamps** end-to-end: NTP-synchronized syslog receivers must honor consistent stratum, Splunk `TIME_PREFIX`/`MAX_TIMESTAMP_LOOKAHEAD` overrides belong in TA `props.conf` validated against `_indextime` skew dashboards.

---

## Category 9: Identity & Access Management — 104 use cases

[Browse Category](../../index.html#cat-9) spans modern directory services, federation, privileged access, Cisco Duo, and endpoint administration. Treat this category as the *who* and *whether the session should exist* layer: every downstream alert in firewall, NAC, or EDR tiers is stronger when Splunk can answer “which human or service principal, through which factor, against which policy version.”

### Subcategory map and priorities

| Focus | Subcategory link | Typical data |
|-------|------------------|---------------|
| AD & cloud directory | [Active Directory / Entra ID](../../index.html#cat-9/9.1) | Windows Security, Entra ID Graph |
| LDAP | [LDAP](../../index.html#cat-9/9.2) | OpenLDAP / AD LDAP access logs |
| IdP & SSO | [IdP & SSO](../../index.html#cat-9/9.3) | Okta, SAML, OIDC vendor logs |
| PAM | [PAM](../../index.html#cat-9/9.4) | CyberArk, BeyondTrust, Delinea |
| Okta & Duo | [Okta & Duo](../../index.html#cat-9/9.5) | `Okta:*`, `duo:*` |
| Endpoint / MDM | [Endpoint / MDM](../../index.html#cat-9/9.6) | Meraki Systems Manager, Intune |

> **Fragment note:** The catalogue uses `#cat-<N>/<X.Y>` (for example `#cat-9/9.1`) for subcategory deep links in `index.html`.

### Active Directory / Entra ID — Microsoft-grounded monitoring

**What:** Instrument account lifecycle, Kerberos authentication, Group Policy tampering, and hybrid cloud identity risk in a single searchable timeline.

**Why:** AD remains the authoritative account store for most enterprises; Entra ID extends that trust into SaaS and conditional access. Without Event ID discipline, you cannot prove *lateral movement* versus *help-desk noise* to auditors or incident responders.

**How:**

1. **Domain controllers — security channel (Event IDs).** Forward the Security log (or XML-rendered equivalents) with minimum retention aligned to investigations. Priority IDs include:
   - **4720** — user account creation (persistence after phish).
   - **4732** — security-enabled group membership changes (privilege escalation).
   - **4768 / 4769** — Kerberos TGT / service ticket issuance (golden/silver ticket hunting, Kerberoasting precursors).
   - **4625** — failed logon (password spray, brute force; pair with lockout telemetry).
   These IDs are documented in Microsoft’s *Windows security audit events* references; map them into the Splunk Common Information Model (CIM) **Authentication** data model using the Splunk-supported Windows TA so `user`, `src`, `action`, and `signature` align with multivendor correlation.

2. **GPO modifications — change integrity.** Monitor **5136 / 5137 / 5138 / 5139** (directory service object changes) and **4904 / 4905** (audit list changes) on systems that hold GPO DACL edits. **What:** capture the *object DN*, *subject*, and *attribute* values. **Why:** attackers with domain credentials often weaken GPO-based hardening instead of dropping malware immediately. **How:** route DC *System* and targeted *Security* events to a parsing tier that preserves XML detail; use accelerated saved searches keyed on `EventCode` with throttles per GPO DN.

3. **DC replication health — availability and integrity.** Track **Replication failures** via Directory Service event patterns and performance objects. **Why:** replication lag delays lockout propagation and can hide malicious object changes on a subset of DCs. **How:** combine Windows perf host metrics (`ldap` / `drs` related) with Splunk ITSI or simple threshold alerts; link to [Brute-Force Login Detection](../../index.html#uc-9.1.1) when auth anomalies cluster on one site.

4. **Entra ID cloud plane.** Pull sign-in and audit data through **Microsoft Graph**—for example `GET https://graph.microsoft.com/v1.0/auditLogs/signIns` and risk APIs under `/identityProtection/` (versions may include `beta` for specific risk detail). The Splunk Add-on for Microsoft Cloud Services normalizes these streams. Centre critical cloud UCs:

   - [Entra ID Risky Sign-Ins](../../index.html#uc-9.1.11) — Identity Protection risk levels in one place for hybrid correlation.
   - [Entra Conditional Access Policy Changes](../../index.html#uc-9.1.17) — policy tampering is insider and nation-state prep.
   - [Kerberoasting Detection](../../index.html#uc-9.1.15) and [Golden Ticket Indicators](../../index.html#uc-9.1.16) — on-prem Kerberos abuse remains a red-team staple; keep on-prem ticket analytics even as sessions move to cloud.

### Cisco Duo — gold standard for MFA telemetry (subcategory [Okta & Duo](../../index.html#cat-9/9.5))

**What:** Duo provides step-up authentication, device trust, and adaptive policies. Splunk must show authentication *result*, *factor*, *device posture*, and *administrative enrollment* changes.

**Why:** MFA is only as strong as enrollment integrity and bypass resistance; device trust closes the gap between “user knows password” and “device is managed.”

**How:**

1. **Ingest `duo:*` sourcetypes** from the Cisco Duo TA (authentication, admin, telephony) into a dedicated index (commonly `duo` or a team standard). **Splunk Connect for Cisco Security Cloud** (see Category 10) can unify Cisco security telemetry when you standardize on Cisco’s cloud connectors.

2. **Operational detections aligned to catalogue UCs:**
   - [Duo Authentication Denials](../../index.html#uc-9.5.7) — policy and attack surface visibility.
   - [Duo Device Trust Posture](../../index.html#uc-9.5.8) — unmanaged or downgraded trust is a precursor to credential stuffing success.
   - [Duo Enrollment Anomalies](../../index.html#uc-9.5.9) — enrollment spikes precede insider data theft and service-desk abuse.

3. **Best-practice pairing — Okta & Entra:** When Okta fronts applications but Duo protects VPN, correlate [Okta MFA Bypass Attempts](../../index.html#uc-9.5.2) with Duo results to see whether failures are synchronized attacks or fragmented policies.

4. **Cross-domain MFA adoption:** [MFA Adoption Rate Trending](../../index.html#uc-9.7.2) intentionally blends Okta, Duo, and Entra fields—use it as an executive control metric, not only SOC.

### Splunk Connect for Cisco Security Cloud — unifying Duo with Cisco security portfolios

**What:** Splunk Connect for Cisco Security Cloud (implemented through the Cisco Security Cloud Splunk integrations on Splunkbase **7404**) centralizes ingestion for multiple Cisco-controlled telemetry streams—reducing bespoke HEC endpoints for each product silo.

**Why:** Enterprises often deploy Duo beside Secure Firewall, Umbrella, and XDR-class exports; Splunk forwards proliferate without governance. Consolidating connectors lowers firewall pinholes and aligns credential vaulting.

**How:** Design a **dedicated Heavy Forwarder** (or Splunk Cloud universal forwarder tier approved for cloud credential storage) hosting the Cisco Security Cloud app; scope service accounts per product family, rotate API secrets through your existing PAM programme, and route normalized events into Cisco-approved indexes before CIM transformations. Test with a shadow index so Duo `duo:authentication` events continue populating legacy dashboards while parallel sourcetype mappings from the Security Cloud pipeline validate field parity.

### Cisco Meraki Systems Manager — endpoint posture ([Endpoint / MDM](../../index.html#cat-9/9.6))

**What:** Systems Manager pushes MDM profiles, inventory, and compliance posture for endpoints across offices and remote workers.

**Why:** Identity without device integrity is incomplete for zero trust; MDM tells you whether encryption, OS patch levels, and jailbreak/root flags match policy.

**How:** Deploy **Cisco Meraki Add-on for Splunk** (Splunkbase **5580**) on Heavy Forwarders or authorized collection hosts with outbound HTTPS access to **Dashboard APIs** (`api.meraki.com`—confirm regional endpoints per Cisco Meraki documentation). Typical sourcetypes include organization inventory patterns such as `meraki:organization:networkdevices`; newer TA trains may expose Systems Manager endpoints under companion sourcetypes—always reconcile names under **Settings → Data inputs → Meraki** before writing detections. Operational dashboards should align with [Device Compliance Status and Policy Enforcement](../../index.html#uc-9.6.1).

**WHAT/WHY/HOW — MDM policy drift:** Systems Manager profiles encode encryption, PIN complexity, OS patch floors, and jailbreak/root posture. **What:** baseline compliant-device ratios per network tag (`network_name`) weekly. **Why:** attackers exploit unmanaged cohorts excluded from conditional access policies. **How:** join MDM posture summaries with Entra device filters or Duo trust signals—when Meraki marks non-compliant yet Entra still surfaces healthy posture, investigate stale connector credentials before blaming users.

### LDAP governance — binds and queries ([LDAP](../../index.html#cat-9/9.2))

**What:** LDAP access logs expose anonymous binds, privileged DN enumeration, excessive `(memberOf=*)` searches, and timed brute-force attempts against directory replicas.

**Why:** Attackers harvest group memberships before Kerberos abuse; legacy apps often permit anonymous LDAP slices that bypass MFA entirely on the backend.

**How:** Ship **OpenLDAP** `slapd` accesslog overlays or **Active Directory** Directory Service diagnostics to Splunk with client IP, binding DN, search base, and filter text. Normalize `src`, `ldap_bind_dn`, `ldap_search_base`, and `action` into CIM **Authentication** where possible. Pair abnormal search volume with [Brute-Force Login Detection](../../index.html#uc-9.1.1) when the same client IP rotates DNs across distributed domain controllers.

### IdP & SSO hygiene ([IdP & SSO](../../index.html#cat-9/9.3))

**What:** Modern IdPs (Okta, Entra ID, Ping, Auth0) emit system logs for MFA challenges, token grants, SAML/OIDC assertions, device compliance gating, and admin API changes.

**Why:** SSO is the choke point for SaaS lateral movement—one IdP compromise becomes hundreds of downstream apps.

**How:** Prefer API collection (Okta **System Log** `v1/logs`, Entra Graph **signIn** and **auditLogs/directoryAudits**) over email digests; map `eventType`, `outcome.result`, `actor.alternateId`, and `securityContext.asNumber` fields to CIM fields. Operational teams should operationalize MFA fatigue analytics and step-up prompts through catalogues that aggregate cross-vendor MFA health such as [MFA Challenge Failure Rate](../../index.html#uc-9.3.1) — a control that becomes more powerful when Duo and Okta streams land in shared summaries.

### Privileged Access Management — CyberArk, BeyondTrust, Delinea ([PAM](../../index.html#cat-9/9.4))

**What:** Session recording metadata, credential checkout, JIT elevation, and vault administrative actions.

**Why:** Tier-zero assets are attacked through shared vaults and break-glass accounts; session fidelity proves *who typed what* post-incident.

**How:**

1. **Session recordings:** ingest indexing metadata (session ID, source IP, target asset, recording URI) rather than raw video into Splunk—reserve binaries for native vault archives.

2. **Checkout anomalies:** statistical rarity on `(account, src, hour)` triples; spikes correlate with ransomware preparation.

3. **JIT bridges:** tie CyberArk Privilege Cloud or Self-Hosted REST callbacks (`https://<PVWA>/PasswordVault/WebServices/PIMServices.svc`) style integrations to Splunk HTTP Event Collector where vendors publish audit streams.

Pair catalogue searches with LDAP governance UCs under [LDAP](../../index.html#cat-9/9.2) when shared service accounts blur attribution.

### Trending & programme reporting ([Identity & Access Trending](../../index.html#cat-9/9.7))

[Browse Subcategory](../../index.html#cat-9/9.7) entries track adoption velocity—MFA rollout, privileged account hygiene, and IdP migration milestones. Programme leaders should not treat these as Sev-1 paging sources; instead schedule them beside risk register reviews so underperforming departments receive funding before auditors do.

---

## Category 10: Security Infrastructure — 2,402 use cases

[Browse Category](../../index.html#cat-10) is the largest bucket: NGFW, IDS/IPS, EDR, email and web gateways, vulnerability management, SIEM/SOAR, PKI, ESCU-style analytics, OT, and behavioural analytics. Success depends on **prioritizing threat-quality signals**, standardizing on CIM for correlation, and measuring detection efficacy—not merely uptime charts.

### Cisco Secure Firewall & FMC — NGFW gold standard ([NGFW](../../index.html#cat-10/10.1))

**CRITICAL prioritization — threat before connection:**

| Principle | WHAT | WHY | HOW |
|-----------|------|-----|-----|
| Threat-first indexing | Ship IPS/threat/File/Malware/FTP stacks ahead of bulk connection logs | Threat events carry vendor disposition (priority impact), CVE linkage, and sandbox verdicts—far fewer bytes than connection flows for equal investigative gain | On FMC **10.x**, use **Platform Settings → Syslog → Splunk** wizard templates where available; otherwise structured syslog templates filtering event categories |
| Volume economics | Budget ~5 GB/day per large HA pair baseline | Connection logs dominate disk; threat slices identify malicious subsets | Rate-limit export interfaces; split indexes (`fw_threat`, `fw_conn`) so acceleration differs |
| Transport selection | Prefer syslog over legacy estreamer-only builds for greenfield | Syslog scales horizontally with UDP/TCP syslog-ng architectures and avoids proprietary backlog coupling where architectures demand simplicity | Deploy Heavy Forwarders with persistent queues receiving syslog (`9514/tcp`) |
| Historical parity | Maintain eStreamer where deep FMC correlation fields remain mandatory | eStreamer carries richer relational metadata for certain forensic timelines | Install **Splunk Add-on for eStreamer eNcore** (Splunkbase **3662**) on collecting tier |

**Event families (eStreamer nomenclature retained for Cisco-native teams):**

- **Intrusion** — IPS signatures and correlated CVE tags.
- **Connection** — allow/deny/session tuples—essential for hunt breadth but noisy for alerting.
- **File / Malware** — AMP/disposition chains across SMB and HTTP.
- **Discovery** — host/port/application visibility.

**Splunk packaging:**

| Package | Splunkbase ID | Role |
|---------|-----------------|------|
| Cisco Security Cloud | **7404** | Unified Cisco telemetry normalization |
| eStreamer eNcore Add-on | **3662** | Binary protocol receivers translating to Splunk-friendly JSON/XML |

**Representative sourcetypes you should recognize in searches:**

`cisco:firepower:estreamer`, `cisco:ftd:syslog`, `cisco:asa:syslog`, `cisco:firepower:intrusion`, `cisco:firepower:connection`, `cisco:firepower:malware`

Validate extraction versions against your TA release notes—field surfaces evolve between FTD maintenance releases.

**Catalogue-critical NGFW use cases:**

- [Threat Prevention Event Trending](../../index.html#uc-10.1.1)
- [Wildfire / Sandbox Verdicts](../../index.html#uc-10.1.2)
- [C2 Communication Detection](../../index.html#uc-10.1.3)
- [DNS Sinkhole Hits](../../index.html#uc-10.1.4)

Operational cadence: weekly trending on **10.1.1**, monthly ROC review tying sandbox verdict deltas (**10.1.2**) to SOC tuning backlog items.

**FMC 7.4+ / 10.x Splunk-forwarding wizards — WHAT/WHY/HOW:** Cisco documents wizard-driven integrations that export curated event subsets toward syslog receivers—**what** you configure is not “enable all categories blindly” but explicitly tick IPS/threat/file categories tied to Splunk index routing. **Why** this matters: greenfield teams underestimate parser CPU on both FMC *and* Splunk when connection logs dwarf threat volumes; wizards encode Cisco-tested bundles that align with Splunk TA expectations. **How:** In FMC UI navigate **Devices → Platform Settings → Logging / Syslog Servers**, define Splunk Heavy Forwarder destinations with TLS where supported, attach templates per logical device cluster (inside vs DMZ FTD pairs), then validate message headers on UF using `tcpdump` before enabling production routing rules.

**Cross-check against catalogue ROI:** Keep [Threat Prevention Event Trending](../../index.html#uc-10.1.1) dashboards filtered on threat-disposition keywords (`Intrusion`, `Malware`) before layering connections-only hunts—otherwise KPI decks mirror throughput spikes unrelated to attacker progression.

### Other NGFW ecosystems

**What:** Palo Alto Networks PAN-OS threat & traffic (`pan:threat`, `pan:traffic`), Fortinet FortiGate IPS (`fortigate_*` sourcetypes per TA), Check Point (`cp_*` patterns).

**Why:** Defence diversity matters—Splunk becomes neutral ground for ATT&CK-aligned hunts across vendors.

**How:** Install vendor TAs (**PAN**: Splunkbase **2757** typical footprint), normalize into **Intrusion_Detection** and **Network_Traffic** models, deduplicate perimeter scanners via lookups.

Representative correlated UC: [FortiGate IPS Event Trending](../../index.html#uc-10.11.2). Firewall policy posture sits adjacent to IPS trending—pair IPS feeds with [FortiGate Firewall Policy Violations](../../index.html#uc-10.11.1) when investigating intentional bypass attempts versus signature tuning gaps.

### IDS / IPS fabrics ([IDS/IPS](../../index.html#cat-10/10.2))

**What:** Dedicated IDS/IPS tiers—Snort/Suricata sensors, appliance IDS blades feeding syslog, Kubernetes sidecars exporting DROP verdict metadata—sit beside NGFW east-west segments where lateral scanning dominates.

**Why:** NGFW logs emphasize perimeter verdicts; IDS fabrics spotlight legacy plaintext protocols and VLAN-spanning exploits missed when TLS blind spots remain.

**How:** Preserve raw rule SID (`gid:sid:rev`), packet capture pointers (`pkt_src`), and VLAN tags—Splunk lookups align Snort sid-msg maps through nightly CSV imports. Severity trending belongs in [Alert Severity Trending](../../index.html#uc-10.2.1); escalate only after vendor-suppressed duplicates collapse via `transaction` or `stats` on `(signature_id,src_ip,dest_ip,dest_port)` tuples.

Operational pairing: correlate IDS spikes with NGFW threat trending (**10.1.1**)—parallel jumps imply worm propagation; IDS-only spikes imply passive monitoring gaps on perimeter sensors.

### Endpoint Detection & Response ([EDR](../../index.html#cat-10/10.3))

CrowdStrike Falcon, Microsoft Defender for Endpoint, SentinelOne, VMware Carbon Black—the catalogue assumes CIM-friendly extractions for process, filehash, device, parent chain.

**What:** Process ancestry, behavioural prevention blocks, credential theft tooling.

**Why:** Network logs rarely carry TLS-inspected payloads anymore; endpoint telemetry proves execution.

**How:** Prefer vendor APIs where syslog truncation loses JSON fidelity; route MITRE technique tags (`technique_id`) into Splunk ES risk frameworks.

Representative UC: [Quarantine Action Monitoring](../../index.html#uc-10.3.2).

### Email & web security ([Email Security](../../index.html#cat-10/10.4), [Web Security](../../index.html#cat-10/10.5))

**What:** Gateway verdicts (`virus_detected`, `url_rewrite`), sandbox callbacks (`sandbox_status`), user attribution (`recipient`, `sender`), and DMARC aggregate alignment.

**Why:** BEC and QR phishing bypass perimeter IDS—mailbox telemetry isolates patient-zero clicks feeding downstream NGFW IOC hunts.

**How:** Deploy Proofpoint TAP/Mimecast/Microsoft Defender for Office 365 TAs—normalize **Authentication**, **Email**, and **Intrusion_Detection** subsets where malicious attachments mimic exploit payloads.

Prioritize catalogue narratives tying suspicious attachments with sandbox verdict UC **10.1.2** and DNS sinkholes **10.1.4** for kill-chain sequencing.

### Vulnerability management correlation ([Vulnerability Management](../../index.html#cat-10/10.6))

**What:** Scanner exports—Qualys host detections (`QID`), Tenable plugin outputs, Rapid7 Nexpose exposures—with severity, CVSS vector strings, proof-of-concept references.

**Why:** SOC relevance emerges only when exposures intersect reachable attack paths—Splunk overlays vuln feeds onto CMDB-enriched ownership plus NGFW exposure zones.

**How:** Accelerate **CIM:Vulnerabilities** (`cve`, `severity`, `signature`) nightly; tie trending dashboards such as [Critical Vulnerability Trending](../../index.html#uc-10.6.1) to patch SLAs—not raw scanner uptime.

### Certificate & PKI observability ([Certificate & PKI Management](../../index.html#cat-10/10.8))

**What:** ACME renewal failures, CT log watchers (`crt.sh` APIs), internal enterprise CA issuance queues, SCEP enrollment spikes.

**Why:** TLS outages masquerade as “application incidents,” yet expired appliance certs frequently coincide with lateral tunnels failing closed—Splunk bridges PKI ops with SecOps narratives.

**How:** Scripted inputs hitting REST monitors (`GET https://crt.sh/?q=%.example.com&output=json`) feed lookups augmenting CA backlog summaries; anchor operational hygiene with [Certificate Expiry Monitoring](../../index.html#uc-10.8.1).

### Vendor-specific packaged detections ([Vendor-Specific Security Detections](../../index.html#cat-10/10.11))

**What:** Splunk-tested SPL macros referencing proprietary vendor fields (`fw_rule_uid`, `panorama_device_group`) packaged into reusable analytic narratives.

**Why:** SOC analysts waste cycles rewriting identical PAN versus Fortinet translations—catalogue vendor lanes accelerate onboarding without diluting vendor nuance.

**How:** Maintain TA compatibility matrices quarterly; promote macros surviving TA upgrades via CI pipelines referencing Splunk AppInspect outputs.

### Industry compliance overlays ([Industry-Specific Compliance & Fraud Detection](../../index.html#cat-10/10.12))

**What:** Vertical telemetry—HIPAA PHI access auditing hooks, PCI DSS segmentation gap monitors, SWIFT CSP correlators, PCI PIN debit overlays—often referencing Splunk Enterprise Security control mappings.

**Why:** Regulatory examinations demand traceability between detective controls and retained logs spanning hybrid estates.

**How:** Align catalogue UC backlog with regulator-ready narratives—example anchor patterns exist where Lantern-derived fraud monitors intersect telemetry-only datasets ([ATM Fraud Pattern Detection](../../index.html#uc-10.12.1) illustrates staged behavioural clustering despite Splunk-native datasets differing per issuing bank).

### Cisco Umbrella (DNS-layer enforcement)

**What:** Umbrella logs DNS security events, Secure Internet Gateway proxy flows, and policy hits.

**Why:** Blocks malware beacon resolution earlier than NGFW in roaming scenarios.

**How:** Deploy Cisco Umbrella inputs (Splunk TA for Umbrella patterns—confirm Splunkbase ID in your tenant’s connector docs), map DNS queries into **DNS** subset of Network Resolution models; correlate Umbrella identity (`internal networks`) with [DNS Sinkhole Hits](../../index.html#uc-10.1.4).

### SIEM, SOAR, and orchestration ([SIEM & SOAR](../../index.html#cat-10/10.7))

**Splunk Enterprise Security** layers assets & identities, notable events, risk scoring, and adaptive response.

Representative catalogue stitches:

- [Alert Volume Trending](../../index.html#uc-10.7.1)
- [Playbook Execution Monitoring](../../index.html#uc-10.7.4)
- [Risk Score Distribution Trending](../../index.html#uc-10.16.7)

Pair alert-volume KPIs with analyst staffing models—when queue depth climbs without playbook throughput gains, escalate orchestration backlog reviews ahead of paging saturation.

Splunk SOAR (Phantom) exposes REST endpoints such as **`https://<phantom-host>/rest/playbook_run`** and **`/rest/container`** for run history—poll with modular inputs using API tokens scoped to read-only automation metadata, not case evidence containing PII binaries. Capture HTTP status distributions weekly; sustained `5xx` spikes warrant failover drills before paging storms coincide with insider threat hunts.

**What:** Track automation success/failure counts and SLA adherence.

**Why:** SOAR bypass equals analyst burnout; silent playbook failure erodes trust faster than noisy alerts.

**How:** Emit Phantom/SOAR REST audit pulls (`/rest/container`, `/rest/playbook_run`) via HTTPS modular inputs or HTTP Event Collector JSON posts—normalize playbook names via lookups.

### MITRE ATT&CK mapping

**What:** Technique IDs enrich dashboards (`technique_id`, `technique_name`) straight from vendor feeds or ESCU lookups.

**Why:** Reporting by tactic exposes coverage gaps versus registration spam counts.

**How:** Maintain a KV store `mitre_technique_map` keyed by vendor signature IDs; nightly backfill from Splunk ATT&CK Analyzer (where licensed) or community transforms.

### ESCU & security content lifecycle (subcategory touchpoint [ESCU](../../index.html#cat-10/10.9))

Enterprise Security Content Updates ship detection *stories*—bundled SPL with narratives referencing MITRE tactics and observability prerequisites.

**WHAT:** Import ESCU analytic stories relevant to your telemetry maturity (`ESCU`, Security Essentials pipelines).

**WHY:** Raw SPL dumps age poorly—story packaging ensures analysts learn detection intent (why MITRE technique T1558 ties to credential harvesting prerequisites).

**HOW:** Run Splunk-supported importer tooling (`import_sse_detections.py` referenced from catalogue `_category.json` quick tips), redistribute narratives into catalogue-aligned subfolders (`redistribute_sse_ucs.py`), tag macros pointing at accelerated data models (`cim_mod_changes`), schedule staged dry runs across representative indexes before flipping alerting adapters.

Treat **2025–2026** ESCU vintages as iterative baselines—not immutable doctrine—because adversary tradecraft shifts faster than quarterly Splunk releases; integrate ESCU merges alongside Cisco NGFW (**10.1.x**) and Duo (**9.5.x**) upgrades so prerequisite macros referencing `signature`, `vendor_product`, or `user` remain populated after TA field renames.

Representative analytic posture UC tie-in: align ESCU phishing narratives with email controls under [Email Security](../../index.html#cat-10/10.4)—schedule tabletop drills referencing ESCU narrative steps beside malicious attachment UC clusters **10.4.x**.

### CIM patterns ([CIM Patterns](../../index.html#cat-10/10.13))

Authentication (`Authentication`), IDS (`Intrusion_Detection`), Network Traffic (`Network_Traffic`), Malware (`Malware`), Changes (`Change`)—each powers `tstats` acceleration without raw scans.

Representative UC: [Failed Authentication Ratio Trending](../../index.html#uc-10.13.1).

### Detection efficacy & behavioural analytics ([Detection Efficacy](../../index.html#cat-10/10.10), [ML / Behavioural](../../index.html#cat-10/10.15))

**What:** Track suppression reasons, analyst disposition (`true_positive`, `benign_true_positive`), model drift.

**Why:** Boards ask “are detections improving?”—only efficacy metrics answer.

**How:** Splunk ES correlation search metadata + SOC ticketing lookups.

Representative advanced UC: [Lateral Movement via Rare Destination Hosts (MLTK)](../../index.html#uc-10.15.2).

### OT security bridge ([OT Security](../../index.html#cat-10/10.14))

Where IT SOC overlaps OT DMZ monitoring: deploy **OT Security Add-on for Splunk** (Splunkbase **5151**, ES prerequisite per catalogue metadata) so ICS-focused correlation searches remain healthy—[OT Security Add-on Health and Configuration Status](../../index.html#uc-10.14.1) validates parsers before ICS hunts proceed.

Map ICS narratives using MITRE ATT&CK for ICS tactics alongside enterprise ATT&CK overlays—dual overlays clarify when PLC-facing telemetry differs from enterprise lateral movement signatures embedded in Category **17** VPN telemetry.

### YARA monitoring

**What:** Vendor YARA hit telemetry from email gateways, sandbox exports, or endpoint scanners.

**Why:** Signature staleness silently misses commodity loaders rewritten weekly.

**How:** Weekly digest `stats dc(rule_name)` vs malware intel drops; escalate drift beyond threshold.

### Licence economics & retention envelopes

**What:** Partition indexes (`idx_sec_threat`, `idx_sec_conn`, `idx_idm`) with distinct retention—threat-centric indexes justify longer hot retention because daily volumes stay constrained once filtered.

**Why:** SOC investigations stall when cold buckets lack IPS metadata yet retain petabytes of VPN flows unrelated to incident timelines.

**How:** Align Splunk licence forecasts with Cisco guidance—when a firewall pair approaches **~5 GB/day** blended ingest, model growth using threat-vs-connection ratios championed earlier; escalate architecture reviews before universal TSIDX acceleration doubles licence draw.

### Security operations trending ([Security Operations Trending](../../index.html#cat-10/10.16))

Beyond reactive alerting, Category **10.16** aggregates SOC maturity telemetry—Mean Time to Acknowledge, backlog ageing, hunter-hours versus automation-hours.

**WHAT:** Stitch Splunk ES notable metadata (`notable_*`), SOC ticketing exports (`ticket_priority`, `assignment_group`), and orchestrator throughput **10.7.4**.

**WHY:** Boards judge SOC uplift via operational metrics, not raw detection counts alone.

**HOW:** Normalize weekly scorecards referencing [Risk Score Distribution Trending](../../index.html#uc-10.16.7); cross-check with [Analyst Workload Distribution](../../index.html#uc-10.7.2) when triage fairness across squads falters.

---

## Category 17: Network Security & Zero Trust — 105 use cases

[Browse Category](../../index.html#cat-17) binds identity signals to enforcement on the wire—NAC, remote access VPN, and vendor Zero Trust / SASE overlays.

### Cisco ISE — NAC gold standard ([NAC](../../index.html#cat-17/17.1))

**MnT syslog aggregation — WHAT/WHY/HOW:**

| Topic | Detail |
|-------|--------|
| WHAT | Send syslog from **Monitoring & Troubleshooting (MnT)** nodes, not individually from each Policy Service Node (PSN). |
| WHY | MnT aggregates operational alarms and forwarded PSN diagnostics—centralizes sequencing while avoiding syslog storms & dedupe ambiguity when scaling PSN clusters. |
| HOW | Design syslog VIP pointing at MnT cluster members per Cisco’s *Cisco ISE Administrator Guide* syslog chapter; verify time sync (NTP) before deduping authentication chains. |

**UDP frame size:**

- **WHAT:** Increase maximum UDP message length to **8192 bytes** for ISE syslog exports.
- **WHY:** Default 1024-byte truncations silently cut RADIUS attributes & pxGrid correlation tokens from search.
- **HOW:** On receiving syslog-ng/rsyslog, set `log-msg-size` / `$MaxMessageSize` appropriately; confirm on Splunk `_raw` length histograms.

**Logging categories (production-safe baseline):**

Enable **AAA Audit**, **Failed Attempts**, **Passed Authentication**, **RADIUS Accounting**, **Posture Audit**, **Administrative Audit**, **Guest**, **System Diagnostics**.

**WHAT:** Each maps to discrete troubleshooting planes—failure analytics versus operational overhead.

**WHY:** Missing posture audit hides non-compliant endpoints remediated only via Splunk retrospectively.

**HOW:** On ISE GUI **Administration → System → Logging → Logging Categories**, subscribe MnT collectors; verify Splunk extraction macros (`cisco:ise:*`) populate `calling_station_id`, `nas_ip_address`, `audit_session_id`.

**AVOID Debug-class floods:**

**WHAT:** Debug categories multiply EPS by an order of magnitude.

**WHY:** license exhaustion & indexer latency—not investigative clarity.

**HOW:** Permit debug only during Sev1 bridges with TTL automation.

**Posture timer coordination:**

**WHAT:** Maintain **≥7200 seconds** policy timers for posture reauthentication where Cisco recommends cooldown consistency.

**WHY:** Aggressive timers churn DHCP churn & Splunk correlation noise.

**HOW:** Harmonize with endpoint compliance dashboards ([Endpoint Posture Failures](../../index.html#uc-17.1.2)).

**Load balancer persistence:**

**WHAT:** Sticky sessions for posture redirects must land users on original PSNs handling CoA.

**WHY:** Stateless LB breaks Change-of-Authorization sequencing—Splunk sees succeeded auth followed by mysterious disconnects.

**How:** LB docs + ISE deployment guides prescribe algorithms (`source IP hash` cautiously vs cookie inserts).

**Feature anchors:** 802.1X & RADIUS, **pxGrid** context streaming (`session:{topic}` style subscriptions—consult Cisco pxGrid integration guides), **TrustSec SGP/SGT**, **ISE Data Connect** (3.2+) SQL-backed analytics exports.

**Splunk artifacts:**

| Artifact | Value |
|----------|-------|
| Splunk Add-on for Cisco ISE | Splunkbase **1915** |
| Cisco Catalyst Add-on | Splunkbase **7538** (contextual campus telemetry) |

**Sourcetypes:** `cisco:ise:syslog`, `cisco:ise:audit`, `cisco:ise:radius`, `cisco:ise:eps`

**Critical catalogue ties:**

- [Rogue Device Detection](../../index.html#uc-17.1.12)
- [Endpoint Posture Failures](../../index.html#uc-17.1.2)
- [NAC Policy Change Audit](../../index.html#uc-17.1.8)

Combine rogue profiling with [VLAN Assignment Audit](../../index.html#uc-17.1.3) when lateral segmentation discrepancies arise—unexpected VLAN hops paired with posture failures frequently expose mislabeled IoT cohorts bridged into user VLANs.

**pxGrid subscriber hygiene:** pxGrid exposes REST/WebSocket fabrics (`https://<ise>/pxgrid/` endpoints—consult Cisco pxGrid integration guides per release). **WHAT:** subscribe only to topics justified by SOC correlation (`com.cisco.ise.session`, `com.cisco.ise.endpoint`). **WHY:** oversubscribed pxGrid consumers inflate JVM heaps on ISE Policy Administration nodes. **HOW:** authenticate with client certificates, throttle pull intervals, mirror critical session fields into KV cache for Splunk lookups instead of replaying entire session tables hourly.

### Cisco ASA & AnyConnect — VPN observability ([VPN & Remote Access](../../index.html#cat-17/17.2))

**What:** VPN concentration telemetry—successful tunnels, AAA failures, simultaneous sessions per identity, geographic attribution.

**Why:** Credential stuffing culminates at VPN concentrators before lateral movement; geo velocity signals stolen passwords.

**How:** Deploy **Splunk Add-on for Cisco ASA** (`Splunk_TA_cisco-asa`), normalize `cisco:asa` syslog into Authentication / Network Sessions models where parsers provide `session_id`.

**Syslog tuning — WHAT/WHY/HOW:** ASA/FTD syslog classes must include **VPN/SSL events** (`%ASA-4-722051`, `%ASA-5-713049` families per Cisco ASA syslog message guides) so Splunk retains `Username`, `Group_Policy`, `Public_IP`, `Assigned_IP`. **Why:** Missing message classes produce “user X connected” dashboards with empty usernames—irreversible if archive retention expired. **How:** On ASA `logging list`, attach VPN-focused lists to Splunk-bound sink servers; verify `logging device-id` contexts for multi-context ASAs.

Anchor use cases:

- [Geo-Impossible VPN Connections](../../index.html#uc-17.2.14)
- [Geo-Location Anomalies](../../index.html#uc-17.2.3)
- [Simultaneous Session Detection](../../index.html#uc-17.2.8)
- [VPN Authentication Failures](../../index.html#uc-17.2.2)

Operational pairing: correlate ASA AAA failures with Duo/Okta MFA failures within ±60 seconds for credential stuffing narratives.

### Zero Trust / SASE overlays ([Zero Trust / SASE](../../index.html#cat-17/17.3))

**What:** Continuous verification brokers—Zscaler Internet Access / Private Access, Netskope, Palo Alto Prisma Access—evaluate identity, device posture, and destination risk each transaction.

**Why:** Traditional perimeter ACLs lack application-aware context; SASE telemetry proves policy enforcement away from corp HQ while accommodating acquisitions that cannot backhaul traffic through legacy DMZ chokepoints.

**How:** Use vendor Splunk TAs (Netskope Add-on Splunkbase **3808**, Zscaler NSS feeds to HEC, Palo Alto Prisma Access leveraging **`Splunk_TA_paloalto`** Splunkbase **2757**, Check Point Splunkbase **4293**, Cloudflare Splunkbase **4501**, Fortinet **`TA-fortinet_fortigate`** Splunkbase **2846** for converged FortiSASE telemetry—confirm dual-use licensing per vendor contracts).

Representative catalogue hooks:

- [Conditional Access Enforcement](../../index.html#uc-17.3.1)
- [Micro-Segmentation Audit](../../index.html#uc-17.3.3)
- [Zero Trust Access Denial Trending](../../index.html#uc-17.3.8)

Continuous verification KPIs belong on executive dashboards beside MFA adoption (**9.7.2**)—culture + telemetry alignment. Document data residency expectations whenever EU sovereign cloud tenants forbid North American SaaS aggregation so Splunk routing stays compliant alongside Zscaler/Netskope tenancy boundaries. Tag `data_residency` and `tenant_region` fields at ingest so executive scorecards remain auditable without ad-hoc spreadsheet reconciliations.

---

## Cross-cutting checklist — turning catalogue breadth into SOC outcomes

1. **Prioritize indexes:** Threat slices (`*_threat`) vs volumetric connection archives (`*_conn`).
2. **Normalize:** Install vendor TAs + CIM—avoid orphan proprietary fields when ESCU macros expect DM-normal names.
3. **Anchor identities:** Populate Splunk ES Assets & Identities from HR + CMDB nightly—every geo velocity UC depends on accuracy.
4. **Measure efficacy:** Monthly dashboards combining ESCU coverage %, playbook SLA ([Playbook Execution Monitoring](../../index.html#uc-10.7.4)), disposition stats, and analyst equity reviews ([Analyst Workload Distribution](../../index.html#uc-10.7.2)).
5. **Reuse catalogue links:** Bookmark critical detection entries ([Brute-Force Login Detection](../../index.html#uc-9.1.1), [Threat Prevention Event Trending](../../index.html#uc-10.1.1), [Rogue Device Detection](../../index.html#uc-17.1.12)) as onboarding curricula.
6. **Coordinate change windows:** Firewall, ISE, and IdP upgrades share Splunk parsing dependencies—schedule TA regression tests whenever Cisco FMC/ISE builds introduce new syslog tokens referenced by saved searches tied to [Threat Prevention Event Trending](../../index.html#uc-10.1.1) or [NAC Policy Change Audit](../../index.html#uc-17.1.8).
7. **Practice hybrid investigations:** Combine Entra risky sign-ins ([Entra ID Risky Sign-Ins](../../index.html#uc-9.1.11)) with VPN geo anomalies ([Geo-Location Anomalies](../../index.html#uc-17.2.3)) monthly—tabletop exercises decay without live rehearsed SPL.

### Threat intelligence feedback loops

**WHAT:** Feed Splunk Enterprise Security notable suppression lists from Tanium, Recorded Future, or MISP exports — whichever intel programme your CSIRT trusts.

**WHY:** Without feeding disposition outcomes back into Splunk lookups, YARA and IDS signatures remain static even when SOC proves benign contexts weekly.

**HOW:** Nightly KV updates consumed by correlation searches referenced across Categories **9**, **10**, **17**; ensure duplicate suppression IDs sync between ES adaptive responses and SOAR playbooks monitored via [Playbook Execution Monitoring](../../index.html#uc-10.7.4).

---

## References — authoritative vendor documentation

- Cisco DUO Splunk integration — https://duo.com/docs  
- Cisco Secure Firewall Management Center syslog export guides — Cisco Secure Firewall documentation portal (`Syslog` integration chapters per FMC OS release).  
- Cisco ISE Administrator Guide — Logging, MnT sizing, syslog categories (matches Cisco Learning / DocWiki releases).  
- Cisco pxGrid Integration Guides — REST/WebSocket subscriber sizing, certificate rotation, topic catalogues (`com.cisco.ise.session`).  
- Cisco ASA syslog messages reference — VPN and cryptographic subsystem classes required before Splunk dashboards populate `Username`/`Group_Policy`.  
- Microsoft Learn — Entra ID reporting APIs (`graph.microsoft.com` audit & sign-in logs).  
- Microsoft Learn — Windows Security auditing baseline (Event ID tables).  
- Splunk Lantern & ES product documentation — CIM primer, ESCU operationalization, Enterprise Security Risk Analysis workflows.  
- Splunk Docs — Splunk Common Information Model (`datamodel.conf` acceleration), Splunk ML Toolkit operational guidelines for behavioural detections paired with [Lateral Movement via Rare Destination Hosts (MLTK)](../../index.html#uc-10.15.2).

### Getting started checklist

New teams onboarding security telemetry should sequence data sources in this order:

1. **Identity stores first** — AD Security channel + Entra audit/sign-in APIs ([Active Directory / Entra ID](../../index.html#cat-9/9.1)). Without identity context, downstream correlation searches produce ambiguous `src_ip`-only alerts.
2. **MFA telemetry second** — Duo and/or Okta logs ([Okta & Duo](../../index.html#cat-9/9.5)). MFA gaps explain bypass paths that firewall logs alone cannot surface.
3. **Firewall threat slices third** — Cisco Secure Firewall IPS/threat/file categories before bulk connection logs ([NGFW](../../index.html#cat-10/10.1)). Threat-first indexing controls license burn while delivering high-fidelity detections.
4. **NAC and VPN fourth** — ISE syslog via MnT + ASA/AnyConnect VPN tunnels ([NAC](../../index.html#cat-17/17.1), [VPN & Remote Access](../../index.html#cat-17/17.2)). Geo-velocity and simultaneous session analytics require identity-enriched sessions.
5. **EDR and email gateways fifth** — process ancestry and phish campaigns ([EDR](../../index.html#cat-10/10.3), [Email Security](../../index.html#cat-10/10.4)). Endpoint evidence proves execution; email evidence proves delivery vector.
6. **Vulnerability and posture last** — scanner exports and compliance overlays ([Vulnerability Management](../../index.html#cat-10/10.6)). Vuln data contextualizes alerts but produces little standalone alerting value without the identity and network layers already in place.

This sequence mirrors the cross-cutting checklist above and optimizes for correlation quality over raw ingest volume.

---

*This guide is descriptive, not exhaustive; always confirm Splunkbase IDs, sourcetype strings, and API route versions against your installed add-on revision, Cisco DUO and Cisco Security Cloud release notes, and vendor documentation before production rollout.*
