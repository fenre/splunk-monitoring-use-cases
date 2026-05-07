---
title: Cisco Identity Services Engine (ISE) Integration Guide
type: integration-guide
product: Cisco Identity Services Engine
product_aliases: [ISE, Cisco ISE, Identity Services Engine, NAC]
splunkbase_id: 1915
ta_name: Splunk Add-on for Cisco Identity Services
index: nac
sourcetypes:
  - cisco:ise:syslog
  - cisco:ise:radius
  - cisco:ise:tacacs
  - cisco:ise:profiler
  - cisco:ise:guestaccess
  - cisco:ise:posture
  - cisco:ise:admin-audit
  - cisco:ise:system-statistics
  - cisco:ise:pxgrid
  - cisco:ise:ers
ise_versions: "3.1+, 3.2, 3.3, 3.4"
ta_versions: "4.x+"
cross_products: [Catalyst Center, Catalyst Switch, Wireless LAN Controller, ASA/FTD, Splunk SOAR, Splunk ES]
compliance_frameworks: [NIS2, DORA, PCI-DSS, HIPAA, NIST-800-53, ISO-27001, SOC-2, SOX-ITGC, NERC-CIP, CMMC]
use_case_subcategory: "17.1"
use_case_count: 82
maturity_tiers: {crawl: 16, walk: 28, run: 38}
last_updated: 2026-05-06
---

# Cisco Identity Services Engine (ISE) Integration Guide

> The definitive guide to integrating Cisco ISE with Splunk for network access
> control, identity-aware monitoring, posture compliance, TrustSec
> microsegmentation, pxGrid context sharing, ANC adaptive response, and
> auditable regulatory evidence. 82 use cases across crawl/walk/run maturity
> tiers, plus 24 cross-cutting compliance wrappers in cat-22.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Data Sources Reference](#data-sources)
- [Sample Events](#sample-events)
- [TA Configuration](#ta-configuration)
- [Syslog Pipeline](#syslog-pipeline)
- [pxGrid Subscriber](#pxgrid)
- [ERS / OpenAPI Polling](#ers-openapi)
- [Data Connect (Direct DB)](#data-connect)
- [CIM Mapping](#cim-mapping)
- [Compliance Mapping](#compliance-mapping)
- [Crawl / Walk / Run Roadmap](#roadmap)
- [Cross-Product Correlation](#cross-product)
- [SOAR Closed-Loop Patterns](#soar)
- [ITSI Service Modeling](#itsi)
- [Splunk ES Risk-Based Alerting (RBA)](#rba)
- [Capacity Planning and Sizing](#sizing)
- [Validation Checklist](#validation-checklist)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [FAQ](#faq)
- [Glossary](#glossary)
- [References](#references)

---

<a id="quick-start"></a>
## Quick Start — 10 Minutes to First Data

1. **Install the TA** — Download [Splunk Add-on for Cisco Identity Services (Splunkbase 1915)](https://splunkbase.splunk.com/app/1915) and install it on your search head and heavy forwarder (or single-instance Splunk).

2. **Create the index** — In Splunk, Settings → Indexes → New Index. Name: `nac`, Data type: Events. Set retention per the highest-tier compliance framework you operate under (HIPAA: 6y; SOX/NERC CIP: 7y; PCI: 1y).

3. **Configure ISE syslog forwarding** — In ISE, Administration → System → Logging → Remote Logging Targets. Add the heavy forwarder hostname/IP, port `514` UDP (or port `6514` over TLS), and assign all relevant logging categories (Failed-Attempts, Passed-Authentications, Authorization, Admin-Operations, System-Diagnostics, Posture, etc.).

4. **Verify data** — Within 5 minutes, run:
   ```spl
   index=nac sourcetype=cisco:ise:syslog | stats count by MessageCode | sort -count
   ```

5. **Deploy core UCs** — Start with the Crawl-tier set (see [Roadmap](#roadmap)).

---

<a id="overview"></a>
## Overview — What Good Looks Like

Cisco ISE is a **policy decision point** for network access control (NAC), supporting:

- **Authentication**: 802.1X (EAP-TLS, EAP-TEAP, PEAP, EAP-FAST), MAB, iPSK, PSK; RADIUS for network-edge enforcement; TACACS+ for device administration.
- **Authorization**: Policy stack producing per-session results — VLAN, dACL, SGT, ACL push, URL redirect.
- **Posture**: Endpoint compliance attestation via Cisco Secure Client.
- **Profiling**: Endpoint identification via DHCP, RADIUS, NMAP, NetFlow, SNMP, HTTP, AD, AI Endpoint Analytics.
- **TrustSec / Group-Based Policy (GBP)**: SGT-based microsegmentation. SXP for IP-to-SGT propagation.
- **pxGrid**: Real-time context sharing with security/IT ecosystems.
- **ANC (Adaptive Network Control)**: Programmatic enforcement (quarantine, port-bounce, port-shutdown).
- **Guest / BYOD**: Sponsor portals, self-registration, MDM/UEM integration.

What good Splunk integration looks like:

- All 10 sourcetypes ingested with end-to-end timestamp accuracy (clock-skew <2s).
- Authentication & Change CIM compliance covering RADIUS+TACACS+ events.
- Posture, profiling, and TrustSec context exposed via the Splunk Add-on for Cisco Identity Services field model.
- Cross-product correlation with WLC, Catalyst, ASA/FTD, ThousandEyes, and Catalyst Center.
- ANC closed-loop integration with Splunk SOAR (Splunkbase 4250) for MTTC <60s.
- Audit-grade evidence pipelines into `audit_evidence` tagged with regulatory clauses.

---

<a id="architecture"></a>
## Architecture and Data Flow

```
[ISE Cluster]                   [Splunk Tier]
+---------+--+--------+         +--------+--+--------+
| PAN     |  | MnT    |         | HF     |  | Index  |
| (Admin) |  | (Logs) |  Syslog | (Recv) |  | nac    |
+---------+  +---+----+ ------>  +--------+  +--------+
| PSN(s)  |      |                     |
+---------+      |  pxGrid              v
                 |  TLS+cert      +-----------+
                 +---->-----+---> | Splunk    |
                            |     | ES / SOAR |
                            |     +-----------+
            [ISE OpenAPI]   |
                +-----------+
                | ERS poll  |
                +-----------+
```

**Data acquisition options (recommended layering):**

1. **Syslog (primary)** — Logging categories targeted to a Splunk heavy forwarder; UDP/514, TCP/6514 (TLS), or via SC4S.
2. **pxGrid (real-time context)** — Subscriber model for streaming session context, profiling, ANC events. Requires pxGrid certificate trust.
3. **ERS / OpenAPI (poll-based)** — Read-only inventory for SGT matrix, certificates, license, MnT operational data.
4. **Data Connect (advanced)** — Direct database access for high-volume historical reporting (audit-controlled).

---

<a id="prerequisites"></a>
## Prerequisites

| Layer | Requirement |
|---|---|
| ISE | 3.1+ (3.2+ for full pxGrid Cloud); current minor patch level |
| Splunk Enterprise | 9.2+ or Splunk Cloud current |
| Splunk Add-on for Cisco Identity Services | 4.x or later |
| Heavy forwarder | At least one, sized for ISE syslog volume (see [Sizing](#sizing)) |
| TLS | TLS 1.2+ for syslog (port 6514); TLS 1.2+ for pxGrid (mandatory) |
| Trusted CA | For pxGrid mutual auth |
| Cisco SOAR app | Optional — Splunkbase 4250 for closed-loop ANC |
| ES | Optional but recommended — ES 7.x+ for RBA / Notable / IDM integration |
| Indexes | `nac` (primary), `audit_evidence` (compliance), `risk` (ES RBA) |
| Lookups | `ise_psn_capacity.csv`, `ise_sgt_matrix.csv` (and baseline), `pci_cde_*`, `bes_cyber_asset_inventory.csv` (NERC) |

---

<a id="data-sources"></a>
## Data Sources Reference

The Splunk Add-on for Cisco Identity Services (1915) supports 10 sourcetypes:

| Sourcetype | Source | Volume (typical) |
|---|---|---|
| `cisco:ise:syslog` | All ISE logging categories | 80% of ISE volume |
| `cisco:ise:radius` | RADIUS Accounting | High in WLC-heavy estates |
| `cisco:ise:tacacs` | TACACS+ accounting | Medium |
| `cisco:ise:profiler` | Profiler events | Medium |
| `cisco:ise:guestaccess` | Sponsor / guest portal | Low-medium |
| `cisco:ise:posture` | Posture events (some via syslog) | Medium |
| `cisco:ise:admin-audit` | Administrative ops audit | Low (high importance) |
| `cisco:ise:system-statistics` | Performance stats | Low |
| `cisco:ise:pxgrid` | pxGrid subscriber events | Variable |
| `cisco:ise:ers` | OpenAPI poll outputs | Low (snapshot data) |

**Key MessageCode ranges (within `cisco:ise:syslog`):**

| Range | Category |
|---|---|
| 5000–5999 | Authentication / Authorization |
| 11000–11999 | TACACS+ Device Administration |
| 35000–36999 | Certificate Management |
| 37000–37999 | Replication |
| 60000–60999 | Administrative Operations Audit |
| 80000–80999 | Posture / AI Endpoint Analytics |
| 86000–86099 | ANC (Adaptive Network Control) |
| 87000–87999 | TrustSec / SXP |

---

<a id="sample-events"></a>
## Sample Events

**Successful authentication (5200):**
```
<134>Apr 25 15:23:01 ise-psn-01 CISE_Passed_Authentications 0001234567 1 0 2026-04-25 15:23:01.123 +00:00 ... CategoryName=Passed-Authentications, MessageCode=5200, NetworkDeviceName=core-switch-bldg5, EapAuthentication=EAP-TLS, AuthenticationMethod=dot1x, ...
```

**ANC quarantine applied (86001):**
```
<134>Apr 25 15:24:02 ise-psn-01 CISE_AdaptiveNetworkControl 0001234568 1 0 ... MessageCode=86001, anc_action=quarantine, mac=00:11:22:33:44:55, anc_policy=DEFAULT_QUARANTINE, initiator=SOAR ...
```

**Admin role grant (60100):**
```
<134>Apr 25 15:25:03 ise-pan-01 CISE_AdministrativeOperationsAudit 0001234569 1 0 ... MessageCode=60100, admin_user=jdoe, admin_role=SUPERADMIN, admin_action=role_assigned, source_ip=10.0.0.5 ...
```

---

<a id="ta-configuration"></a>
## TA Configuration

Configure under `Splunk Add-on for Cisco Identity Services` → Configuration:

```ini
[cisco_ise://prod-cluster]
host = ise-pan-01.example.com
duration = 900
index = nac
account = ise-prod
disabled = 0
```

For pxGrid:

```ini
[cisco_ise_pxgrid://prod-cluster]
host = ise-pan-01.example.com
pxgrid_port = 8910
client_cert = $SPLUNK_HOME/etc/apps/Splunk_TA_cisco_ise/local/certs/pxgrid-client.pem
ca_cert = $SPLUNK_HOME/etc/apps/Splunk_TA_cisco_ise/local/certs/ca.pem
topics = com.cisco.ise.session,com.cisco.ise.config.profiler,com.cisco.ise.anc
index = nac
```

---

<a id="syslog-pipeline"></a>
## Syslog Pipeline

**Recommended:** Splunk Connect for Syslog (SC4S) or syslog-ng routing into the heavy forwarder. SC4S provides:
- Built-in ISE message parsing
- Per-PSN routing
- TLS termination
- Index/sourcetype assignment

**props.conf (heavy forwarder):**
```ini
[cisco:ise:syslog]
TIME_PREFIX = ^<\d+>\w+ \d+ \d+:\d+:\d+ \S+ CISE_
TIME_FORMAT = %b %d %H:%M:%S
TZ = UTC
SHOULD_LINEMERGE = false
LINE_BREAKER = ([\r\n]+)<\d+>
KV_MODE = none
EXTRACT-ise_kv = (?<key>\w+)=(?<value>[^,]+)(?:, |$)
```

---

<a id="pxgrid"></a>
## pxGrid Subscriber

Recommended topics for security operations:

| Topic | Purpose |
|---|---|
| `com.cisco.ise.session` | Session context — user-to-IP mapping with full identity context |
| `com.cisco.ise.config.profiler` | Profiler attribute updates |
| `com.cisco.ise.anc` | ANC (quarantine) events from peers |
| `com.cisco.ise.config.identity` | Identity-store updates |
| `com.cisco.ise.config.endpoint.assetlookup` | TC-NAC threat list updates |
| `com.cisco.ise.mdm` | MDM compliance state |

**Operational concerns** (see UC-17.1.33, UC-17.1.34, UC-17.1.35): subscriber WebSocket health, throughput anomaly, cloud-relay TLS health.

---

<a id="ers-openapi"></a>
## ERS / OpenAPI Polling

ERS (External RESTful Services) and OpenAPI are read-mostly REST endpoints for inventory and configuration:

- `/ers/config/sgt` — SGT inventory
- `/ers/config/sgmatrix` — Effective SGT matrix
- `/ers/config/networkdevice` — NAD inventory
- `/api/v1/admin-permissions` — Admin role inventory

**Risk awareness:** UC-17.1.57 detects brute force / abuse; UC-17.1.58 audits Data Connect direct DB.

---

<a id="data-connect"></a>
## Data Connect (Direct Database Access)

ISE Data Connect (3.2+) exposes the MnT operational DB read-only over TLS. Useful for high-volume retrospective reports. **Audit-controlled**: every connection logged via `cisco:ise:syslog` 40400/40401 events. Wrapped by UC-17.1.58 + UC-22.12.43.

---

<a id="cim-mapping"></a>
## CIM Mapping

| ISE Field | CIM Model | CIM Field |
|---|---|---|
| `user`, `username` | Authentication | `user` |
| `nas_ip`, `device_ip` | Authentication | `dest`, `dvc` |
| `calling_station_id` (MAC) | Authentication | `src_mac` |
| `framed_ip_address` | Authentication | `src_ip` |
| `Acct-Status-Type` | Authentication | `action` |
| `MessageCode` | Authentication | `signature_id` |
| `MatchedPolicyName` | Authentication | `authentication_method` |
| `EapAuthentication` | Authentication | `signature` |
| `admin_user`, `admin_role`, `admin_action` | Change | `user`, `object`, `action` |
| `anc_action`, `endpoint_mac` | Alerts | `signature`, `dest_mac` |
| `anomaly_type`, `anomaly_score` | Alerts | `signature`, `severity_id` |

Required tags: `authentication`, `tacacs`, `radius` (for relevant events).

---

<a id="compliance-mapping"></a>
## Compliance Mapping

This guide's UC catalog is mapped to the following frameworks via the structured `compliance[]` array on each UC:

| Framework | Primary cat-22 wrappers |
|---|---|
| **PCI DSS v4.0** | UC-22.11.107 (4.2.1 wireless), UC-22.11.108 (1.4.5 segmentation), UC-22.11.109 (8.3.10 revocation), UC-22.11.110 (1.4.5 dACL push) |
| **HIPAA** | UC-22.10.57 (164.308(a)(4)(ii)(B) admin), UC-22.10.58 (164.312(b) posture) |
| **NIS2** | UC-22.2.58 (Art.21(2)(b) ANC), UC-22.2.59 (Art.21(2)(b) MTTC) |
| **DORA** | UC-22.3.46 (Art.7 capacity), UC-22.3.47 (Art.10 multi-site) |
| **NIST 800-53 Rev.5** | UC-22.14.81 (IA-2(1) TEAP) |
| **ISO/IEC 27001:2022** | UC-22.6.56 (A.8.24 PKI), UC-22.6.57 (A.8.2 admin), UC-22.6.58 (A.8.20 segregation) |
| **SOC 2** | UC-22.8.40 (CC7.4 ANC) |
| **SOX / ITGC** | UC-22.12.41 (admin), UC-22.12.42 (TACACS+), UC-22.12.43 (Data Connect) |
| **CMMC 2.0** | UC-22.20.21 (AC.L2-3.1.1 strong auth) |
| **NERC CIP** | UC-22.13.71 (CIP-007-6 R5 BES) |
| **Cross-cutting** | UC-22.40.6/7 (privileged access), UC-22.41.6/7 (encryption/key management) |

Each cat-17 ISE UC also carries its own `compliance[]` array for direct framework attribution. Together they provide bidirectional linking from ISE technical evidence to regulatory clauses.

---

<a id="roadmap"></a>
## Crawl / Walk / Run Roadmap

**Crawl** (foundation, weeks 0-4):
- UC-17.1.1 to UC-17.1.10 (existing legacy detections)
- UC-17.1.28 (replication health)
- UC-17.1.29 (node resource saturation)
- UC-17.1.31 (cert expiry)
- UC-17.1.71 (admin role audit)
- UC-17.1.43 (TACACS+ privileged commands)

**Walk** (operational excellence, weeks 4-12):
- UC-17.1.30 (process crashes)
- UC-17.1.32 (license/MnT retention)
- UC-17.1.33-35 (pxGrid)
- UC-17.1.38-40 (advanced authentication)
- UC-17.1.44-46 (identity stores, PassiveID, CII)
- UC-17.1.47-49 (backup/restore/upgrade)
- UC-17.1.55 (profiler probe quality)
- UC-17.1.56 (CoA failure)
- UC-17.1.74 (SSID auth-mode purity)
- UC-17.1.75 (dACL push integrity)
- UC-17.1.78 (PSN distribution imbalance)

**Run** (advanced patterns, weeks 12+):
- UC-17.1.36-37 (TrustSec/SGT matrix)
- UC-17.1.41-42 (TC-NAC, ANC)
- UC-17.1.50-54 (MDM, sponsor, posture funnel, agent)
- UC-17.1.57-65 (ERS, Data Connect, Edge Processor, cloud, hybrid, stealth, CPP, CoCM)
- UC-17.1.66-68 (IoT/AI Endpoint, AEB)
- UC-17.1.69-72 (TEAP, OCSP/CRL, lockouts, anomalies)
- UC-17.1.73 (wireless funnel)
- UC-17.1.76 (GBP matrix drift)
- UC-17.1.77, UC-17.1.79 (PSN SLO, policy funnel)
- UC-17.1.80-82 (closed-loop ANC, RBA, SOAR MTTC)

---

<a id="cross-product"></a>
## Cross-Product Correlation

| Combine ISE with | Use Case |
|---|---|
| Cisco WLC | UC-17.1.73 wireless onboarding funnel |
| Cisco Catalyst Center | UC-5.13.68 cross-correlation of failed auths to NAD health |
| Cisco ASA / FTD | Identity-aware firewall policy (pxGrid IDM) |
| Cisco ThousandEyes | Network path correlation for ISE PSN reachability |
| Splunk SOAR | UC-17.1.82 closed-loop ANC playbook MTTC |
| Splunk ES | UC-17.1.81 Risk-Based Alerting integration |
| Cisco Cyber Vision | OT-asset profile feeding ISE TC-NAC |
| AWS / Azure / GCP | UC-17.1.60 cloud-hosted PSN cost & resource tracking |

---

<a id="soar"></a>
## SOAR Closed-Loop Patterns

The Splunk SOAR Cisco ISE app (Splunkbase 4250) provides actions:

- `block_endpoint` — Apply ANC quarantine
- `unblock_endpoint` — Release ANC quarantine
- `endpoint_session_info` — Get current session context
- `terminate_session` — RADIUS CoA disconnect

**Pattern: SOC investigation → ANC quarantine** (audited by UC-17.1.82 + UC-22.2.59):

1. ES Notable fires (UEBA / RBA threshold reached).
2. SOAR playbook invokes `block_endpoint` with the suspect MAC.
3. ISE applies ANC; emits 86001.
4. Switch enforces (CoA disconnect + redirect ACL).
5. Splunk measures end-to-end MTTC (NIS2/DORA evidence).

---

<a id="itsi"></a>
## ITSI Service Modeling

**Service: ISE NAC Platform**

Tier-1 KPIs:
- Authentication success rate (UC-17.1.40 latency SLO)
- PSN headroom (UC-17.1.77)
- Replication lag (UC-17.1.28, UC-17.1.61)

Tier-2 KPIs:
- pxGrid subscriber connection count (UC-17.1.33)
- Posture compliance rate (UC-17.1.21, UC-17.1.53)
- Backup job success (UC-17.1.47)

Sub-services: PSN tier; PAN tier; MnT tier; pxGrid; Identity Stores (UC-17.1.44).

---

<a id="rba"></a>
## Splunk ES Risk-Based Alerting (RBA)

ISE risk modifiers applied to identity / endpoint risk objects:

| Source signature | Risk score | Description |
|---|---|---|
| 5400 (auth fail × N) | 5 each | Failed authentication |
| 80002 (posture fail) | 15 | Endpoint posture non-compliance |
| 86040 (TC-NAC threat) | 60 | Threat-list match |
| 86200 (MDM noncompliance) | 30 | MDM-detected risk |
| 86001 (CII risk score >70) | 40 | CII-driven risk elevation |

Wrapped by UC-17.1.81. Configure via ES → Risk → Risk Factors and Risk Modifiers.

---

<a id="sizing"></a>
## Capacity Planning and Sizing

| ISE deployment scale | Daily syslog volume | Splunk indexer count |
|---|---|---|
| Small (1 PAN+MnT, 1-2 PSN, <5,000 endpoints) | 5–20 GB | 1 |
| Medium (Distributed, 4 PSN, 20,000 endpoints) | 50–150 GB | 2-3 |
| Large (Distributed-Multisite, 10+ PSN, 100,000 endpoints) | 300 GB-1 TB | 4-8 |
| Very large (Hyperscale-Multisite, 50,000+ endpoints/site) | 1-3 TB | 8+ |

PSN platform TPS reference (Cisco SNS-3700 series): SNS-3715 = 5,000 TPS; SNS-3725 = 10,000 TPS; SNS-3755 = 20,000 TPS; SNS-3795 = 50,000 TPS. Used by UC-17.1.77.

---

<a id="validation-checklist"></a>
## Validation Checklist

- [ ] All 10 sourcetypes producing events.
- [ ] Heavy-forwarder syslog endpoint reachable from PSNs (UDP/514 or TCP/6514).
- [ ] Clock skew between ISE and Splunk indexers <2 seconds.
- [ ] CIM Authentication tag present for `cisco:ise:syslog` MessageCode 5200/5400.
- [ ] pxGrid subscriber connected (UC-17.1.33 healthy).
- [ ] Acceleration enabled on Authentication and Change DMs.
- [ ] `ise_psn_capacity.csv` populated.
- [ ] `audit_evidence` index has 1y+ retention; PCI/HIPAA/SOX/NERC retention enforced per applicable framework.
- [ ] Crawl-tier UCs deployed and steady-state validated.

---

<a id="troubleshooting"></a>
## Troubleshooting

**Symptom: No `cisco:ise:syslog` events**
- Check ISE Logging → Remote Logging Targets — is the destination valid?
- Check heavy forwarder firewall — UDP/514 or TCP/6514 allowed?
- Run `nc -ul 514 | head -5` on the heavy forwarder to confirm reception.
- Check `index=_internal source=*splunkd.log component=TcpInputProc` for connection accept errors.

**Symptom: `MessageCode` field missing**
- Verify Splunk Add-on for Cisco Identity Services 4.x+ deployed on indexers and search head.
- Check `props.conf` extractions are pushed to indexers.

**Symptom: pxGrid subscriber stuck "PendingApproval"**
- Approve via ISE Administration → pxGrid Services → Web Clients → Approve.
- See UC-17.1.33 known false positives.

**Symptom: Event volume drops at the same time daily**
- Often due to ISE log purge / bucket roll. UC-17.1.32 detects MnT retention falling below target.

---

<a id="known-limitations"></a>
## Known Limitations

- Pre-3.2 ISE does not support pxGrid Cloud (UC-17.1.35 will not fire on legacy).
- AI Endpoint Analytics (UC-17.1.66, UC-17.1.67) requires Catalyst Center 2.3.5+ AND ISE 3.x integration. Not available standalone.
- Data Connect (UC-17.1.58) requires ISE 3.2+ Premium licensing.
- MDM/UEM integration (UC-17.1.50) requires connector configuration per MDM vendor; not all messages arrive in real time.
- TEAP (UC-17.1.69) requires Windows 11 22H2+ or Cisco Secure Client native supplicant; not all clients support it.

---

<a id="faq"></a>
## FAQ

**Q: We use TACACS+ but not RADIUS — does this guide apply?**
A: Most UCs apply; UC-17.1.43 is fully TACACS+ focused. Wireless-specific UCs (UC-17.1.73, 74) won't apply.

**Q: Can we run this guide with ISE 2.x?**
A: Most syslog-based UCs work with ISE 2.7+. pxGrid Cloud, AI Endpoint Analytics, TEAP, and Data Connect UCs require 3.x.

**Q: How do we handle ISE high-cardinality fields like `endpoint_mac`?**
A: Use summary indexing for daily aggregates. The `audit_evidence` index already accommodates this pattern.

**Q: Do we need ES?**
A: Strongly recommended. UC-17.1.81 (RBA) and UC-22.* compliance wrappers leverage ES Risk and Notable frameworks.

---

<a id="glossary"></a>
## Glossary

- **ANC**: Adaptive Network Control — programmatic policy enforcement
- **CoA**: Change of Authorization — RADIUS message to update a session
- **CII**: Cisco Identity Intelligence — risk-scoring service
- **CoCM**: Continuous Compliance Monitoring — posture grace tracking
- **CPP**: Custom Posture Provisioning
- **GBP**: Group-Based Policy
- **MnT**: Monitoring node — ISE node that aggregates operational data
- **NAD**: Network Access Device — switch, AP, controller
- **PAN**: Policy Administration Node — ISE control plane
- **PSN**: Policy Services Node — ISE data plane
- **pxGrid**: Cisco's context-sharing fabric
- **SGT**: Security Group Tag — TrustSec tag
- **SXP**: SGT Exchange Protocol
- **TC-NAC**: Threat-Centric NAC — STIX/TAXII feed integration
- **TEAP**: Tunnel EAP — joint user+machine authentication

---

<a id="references"></a>
## References

- [Cisco ISE 3.4 Admin Guide](https://www.cisco.com/c/en/us/td/docs/security/ise/3-4/admin_guide/b_ise_admin_3_4.html)
- [Splunk Add-on for Cisco Identity Services (Splunkbase 1915)](https://splunkbase.splunk.com/app/1915)
- [Splunk SOAR Cisco ISE App (Splunkbase 4250)](https://splunkbase.splunk.com/app/4250)
- [RFC 7170 — TEAP](https://www.rfc-editor.org/rfc/rfc7170)
- [Cisco SNS-3700 Series Datasheet](https://www.cisco.com/c/en/us/products/collateral/security/secure-network-server/datasheet-c78-744213.html)
- [Cisco TrustSec Configuration Guide](https://www.cisco.com/c/en/us/support/security/identity-services-engine/products-installation-and-configuration-guides-list.html)
- [Cisco AI Endpoint Analytics](https://www.cisco.com/c/en/us/products/cloud-systems-management/dna-spaces/ai-endpoint-analytics.html)

---

## Contribution and Feedback

Contributions welcome via PR. UC IDs follow the cat-17.1.X convention; compliance wrappers in cat-22 follow the existing subcategory numbering. See [`AGENTS.md`](../../AGENTS.md) and [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
