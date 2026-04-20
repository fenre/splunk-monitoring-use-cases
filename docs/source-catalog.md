# Use Case Source Catalog

Comprehensive reference of all sources used (and not yet used) to develop use cases in this repository. Check these periodically for new content, updated TAs, and emerging integrations.

**Legend:**
- ✅ **USED** — Source actively used; UCs already in catalog
- 🟡 **PLANNED** — Source researched; UCs in expansion plan but not yet written
- 🔵 **UNTAPPED** — Promising source with real Splunk backing; not yet used
- ⬜ **LOW PRIORITY** — Source exists but adds marginal value given current coverage

Last reviewed: 2026-04-20 (catalogue v7.1)

> **What changed since the v3.20 review (2026-03-20):** the catalogue
> grew from 4,625 UCs / 22 categories / 122 subcategories to
> **6,447 UCs / 23 categories / 189 subcategories**. The regulatory
> corpus was rebuilt on top of `data/regulations.json` (66 frameworks
> across three tiers), every tier-1 regulation is now covered by a
> deep `commonClauses[]` matrix with `obligationText`, and the
> catalogue ships clause-level machine APIs under `api/v1/compliance/`
> (story, clause-navigator, and per-regulation payloads). The MCP
> server (`mcp/`) now exposes ten tools covering the whole corpus. See
> `CHANGELOG.md` v3.21 &rarr; v7.1 and
> `docs/v6.0-release-report.md` for the detailed timeline.

---

## 1. Splunk Official Documentation & Portals

### Splunk Lantern (lantern.splunk.com)

Primary use case library. Check quarterly for new content.

| Section | URL | Status | Notes |
|---|---|---|---|
| Security Use Cases | lantern.splunk.com/Security_Use_Cases | ✅ USED | Threat Investigation, Security Monitoring, Compliance, Threat Hunting |
| Security — Compliance | lantern.splunk.com/Security_Use_Cases/Compliance | ✅ USED | PCI DSS, HIPAA, GDPR PII detection, NERC CIP, MiFID II, KYC |
| Security — Threat Hunting | lantern.splunk.com/Security_Use_Cases/Threat_Hunting | ✅ USED | Cisco SNA + ES + RBA integration |
| Security — Use Case Explorer | lantern.splunk.com/Security/UCE | ✅ USED | Foundational Visibility, Security Monitoring, Advanced Threat Detection |
| Observability Use Cases | lantern.splunk.com/Observability_Use_Cases | ✅ USED | Optimize Performance, Troubleshoot, Monitor Business, User Journey |
| Observability — Infrastructure Monitoring | lantern.splunk.com/Observability/Product_Tips/Infrastructure_Monitoring | ✅ USED | VMware, AWS RDS, K8s, PostgreSQL, HPA |
| Observability — APM | lantern.splunk.com/Observability/Getting_Started/Implementing_features_and_use_cases_in_Splunk_APM | 🔵 UNTAPPED | OpenAI/GPT monitoring, Lambda, third-party API calls, span tag indexing |
| Industry — Financial Services | lantern.splunk.com/Industry_Use_Cases/Financial_Services_and_Insurance | ✅ USED | Fraud Analytics, Behavioral Profiling, Data Compliance Pipelines SA |
| Industry — Manufacturing | lantern.splunk.com/Industry_Use_Cases/Manufacturing | 🟡 PLANNED | Predictive maintenance, inventory optimization, OT perimeter |
| Industry — Communications & Media | lantern.splunk.com/Industry_Use_Cases/Communications_and_Media | 🟡 PLANNED | Telecom operations |
| Industry — Public Sector | lantern.splunk.com/Industry_Use_Cases/Public_Sector | ✅ USED | FedRAMP, CMMC, FISMA, CJIS |
| Industry — Retail | lantern.splunk.com/Industry_Use_Cases/Retail | 🟡 PLANNED | In-store analytics, POS, inventory visibility |
| Splunk & Cisco Use Cases | lantern.splunk.com/Splunk_and_Cisco_Use_Cases | ✅ USED | Identity Intelligence, SNA, switches/routers/WLAN, gRPC, global ops |
| Data Descriptors | lantern.splunk.com/Data_Descriptors | ✅ USED | Data source best practices and TA links |
| Data Descriptors — Cisco | lantern.splunk.com/Data_Descriptors/Cisco | ✅ USED | IOS, ASA, Meraki, ISE, etc. |
| Data Descriptors — Google | lantern.splunk.com/Data_Descriptors/Google | ✅ USED | GCP, Google Workspace |
| AI Use Cases | lantern.splunk.com — AI section | ✅ USED | AI/LLM observability, Splunk AI implementations |
| Platform Data Management | lantern.splunk.com — Platform section | ✅ USED | Edge Processor, data pipelines |
| DORA Cross-Region DR | lantern.splunk.com/Security_Use_Cases/Compliance/Using_Cross-Region_Disaster_Recovery_for_OCC_and_DORA_compliance | 🟡 PLANNED | EU DORA + OCC compliance |

### Splunk Security Content (research.splunk.com)

ESCU detections and analytic stories. Check monthly for new releases.

| Section | URL | Status | Notes |
|---|---|---|---|
| Analytic Stories | research.splunk.com/stories | ✅ USED | 80 stories in 10.9; 1,900+ detections drove 10.3, 10.4, 10.7 |
| Stories by Tactic | research.splunk.com/stories/tactics/ | ✅ USED | MITRE ATT&CK mapped detections |
| Stories by Data Source | research.splunk.com/stories/source/ | ✅ USED | Mapped to TAs and sourcetypes |
| GitHub: splunk/security_content | github.com/splunk/security_content | ✅ USED | Raw YAML detections, `contentctl` tool |
| Monthly Updates Blog | splunk.com/en_us/blog/security/latest-splunk-security-content.html | 🔵 UNTAPPED | Check monthly for new analytic stories not yet in 10.9 |

### Splunk Docs (docs.splunk.com)

| Section | URL | Status | Notes |
|---|---|---|---|
| Pretrained Source Types | docs.splunk.com/Documentation/Splunk/latest/Data/Listofpretrainedsourcetypes | 🔵 UNTAPPED | Complete list of all built-in sourcetypes — useful for gap analysis |
| CIM Manual | docs.splunk.com/Documentation/CIM/latest/ | ✅ USED | CIM data model reference |
| ITSI Docs | docs.splunk.com/Documentation/ITSI/latest/ | ✅ USED | Service modeling, KPIs, Glass Tables |
| ES Docs | docs.splunk.com/Documentation/ES/latest/ | ✅ USED | Notable events, correlation searches |
| Edge Hub Docs | docs.splunk.com/Documentation/EdgeHub/ | ✅ USED | MQTT, OPC-UA, Modbus via Edge Hub |

### Splunk Blogs (splunk.com/blog)

| Topic | URL Pattern | Status | Notes |
|---|---|---|---|
| Security Blog | splunk.com/en_us/blog/security/ | ✅ USED | ESCU updates, threat research, detection stories |
| Observability Blog | splunk.com/en_us/blog/observability/ | ✅ USED | DORA operational resilience, APM, IM |
| Industries Blog | splunk.com/en_us/blog/industries/ | 🟡 PLANNED | DORA for financial services, energy solutions |
| Learn Blog | splunk.com/en_us/blog/learn/ | ✅ USED | NIS2 directive explainer |
| Customers Blog | splunk.com/en_us/blog/customers/ | ✅ USED | Lantern annual refresh, customer stories |
| .conf Recaps | splunk.com/en_us/blog/conf-splunklive/ | 🔵 UNTAPPED | .conf25 session recordings and new feature announcements |

### Splunk Solutions Pages

| Page | URL | Status | Notes |
|---|---|---|---|
| Compliance | splunk.com/en_us/solutions/compliance.html | ✅ USED | GDPR, PCI, HIPAA, compliance automation |
| Energy & Utilities | splunk.com/solutions/industries/energy-and-utilities | 🟡 PLANNED | Argos, Bosch Rexroth customer stories |
| Financial Services | splunk.com/solutions/industries/financial-services | ✅ USED | Fraud, AML, operational resilience |
| Healthcare | splunk.com/solutions/industries/healthcare | 🟡 PLANNED | EHR monitoring, HIPAA |
| Manufacturing | splunk.com/solutions/industries/manufacturing | 🟡 PLANNED | OT visibility, predictive maintenance |
| Retail | splunk.com/solutions/industries/retail | 🟡 PLANNED | POS, omnichannel, inventory |
| Public Sector | splunk.com/solutions/industries/public-sector | ✅ USED | FedRAMP, CMMC |

---

## 2. Splunkbase Apps & Technology Add-ons

### Core Platform TAs (✅ USED — all heavily utilized)

| TA | Splunkbase ID | UCs | Categories |
|---|---|---|---|
| Splunk Security Essentials / ESCU | — | ~2,068 | 10.2-10.9 |
| Splunk_TA_windows | — | ~172 | 1.2, 10.3, 10.7 |
| Splunk_TA_nix | — | ~131 | 1.1 |
| Splunk_TA_aws | — | ~94 | 4.1, 10.7 |
| Splunk_TA_microsoft-cloudservices | — | ~63 | 4.2, 10.4, 10.7 |
| Splunk_TA_google-cloudplatform | — | ~44 | 4.3 |
| Splunk_TA_vmware | — | ~38 | 2.1 |
| Splunk_TA_snow (ServiceNow) | — | ~34 | 16.1-16.4 |
| Splunk_TA_paloalto | — | ~30 | 10.1, 10.11 |
| Splunk_TA_fortinet | — | ~20 | 10.1, 10.11 |
| Splunk_TA_okta | — | ~21 | 9.5 |
| Splunk_TA_GoogleWorkspace | — | ~18 | 11.2 |
| Splunk_TA_cisco-ise | — | ~18 | 5.8, 17.1 |

### Cisco TAs (✅ USED)

| TA | Splunkbase ID | UCs | Categories |
|---|---|---|---|
| Cisco Meraki Add-on | 5580 | ~110 | 5.9 |
| Cisco ThousandEyes App | 7719 | ~60 | 5.10, 8.7 |
| Cisco Security Cloud | 7404 | — | 10.1 (via Firewall syslog) |
| Cisco Catalyst Add-on | 7538 | — | 5.1 (via syslog/Netflow) |

### Security Vendor TAs (✅ USED)

| TA | Splunkbase ID | UCs | Category |
|---|---|---|---|
| Palo Alto Networks App | Various | ~30 | 10.1, 10.11 |
| Fortinet (FortiGate/FortiManager) | Various | ~20 | 10.1, 10.11 |
| Check Point | Various | ~15 | 10.11 |
| CrowdStrike | Various | ~15 | 10.7, 10.11 |
| Carbon Black (VMware) | Various | ~12 | 10.11 |
| Tanium | Various | ~12 | 10.11 |
| Tenable | Various | ~11 | 10.6, 10.11 |
| Qualys | Various | — | 10.6 |
| Zscaler | Various | ~9 | 10.5, 10.11 |
| Netskope | Various | — | 10.5 |
| Proofpoint | Various | — | 10.4 |
| Wiz | Various | — | 10.6 |
| Snyk | Various | — | 12.3 |

### 🔵 UNTAPPED Security Vendor TAs (missing from catalog entirely)

These vendors have Splunkbase TAs but zero UCs in the catalog. Adding them would further increase Cat 10 (already 53.5% of catalog).

| Vendor | Splunkbase App | Potential Category | Est. UCs | Priority |
|---|---|---|---|---|
| SentinelOne | Splunkbase 5765 | 10.11 Vendor Security | ~8 | Medium — major EDR competitor |
| Sophos | Splunkbase 4646 | 10.11 Vendor Security | ~6 | Medium — endpoint + firewall |
| Trend Micro | Splunkbase 3965 | 10.11 Vendor Security | ~6 | Medium — Deep Security, Apex One |
| Mimecast | Splunkbase 3200 | 10.4 Email Security | ~5 | Medium — major email security |
| Barracuda | Splunkbase 2913 | 10.4/10.5 | ~4 | Low — overlaps with existing email UCs |
| Symantec/Broadcom | Splunkbase 2772 | 10.11 | ~5 | Low — declining market share |
| McAfee/Trellix | Splunkbase 2740 | 10.11 | ~4 | Low — declining market share |

### 🔵 UNTAPPED Non-Security TAs

These fill gaps in observability/infrastructure categories (higher priority since Cat 10 is already heavy).

| Vendor | Splunkbase App | Potential Category | Est. UCs | Priority |
|---|---|---|---|---|
| Aruba (HPE) | Splunkbase 5579 | 5.4 Wireless | ~5 | **High** — major wireless vendor, fills gap |
| Rubrik | Splunkbase 4834 | 6.3 Backup | ~4 | **High** — major backup platform, fills gap |
| Veritas NetBackup | Splunkbase various | 6.3 Backup | ~3 | Medium — enterprise backup |
| Confluence (Atlassian) | Splunkbase 4616 | 11 or 12 | ~3 | Low — collaboration niche |
| Datadog | Integration via HEC | 13.3 Third-Party Monitoring | ~3 | Low — competitor product |
| Nagios | Splunkbase 2695 | 13.3 Third-Party Monitoring | ~2 | Low — legacy monitoring |

### OT / IoT TAs (🟡 PLANNED — in expansion plan)

| TA | Splunkbase ID | Status | Plan Phase |
|---|---|---|---|
| OT Security Add-on | 5151 | 🟡 PLANNED | Phase 2 — 10.14 OT Security |
| OT Intelligence | 5180 | ✅ USED | Cat 14 existing |
| TA for Zeek | 5466 | 🟡 PLANNED | Phase 1a — 14.6 Zeek ICS |
| Corelight App | 3884 | 🟡 PLANNED | Phase 1a — 14.6 Zeek ICS |
| MQTT Modular Input | 1890 | 🟡 PLANNED | Phase 1c — 14.5 HiveMQ |

### 🔵 UNTAPPED: Recently Released Apps (2025-2026)

These are new Splunkbase apps that could generate timely, relevant UCs.

| App | Splunkbase ID | Released | Potential Category | Est. UCs | Priority |
|---|---|---|---|---|---|
| GenAI Observability for Splunk | 8308 | Dec 2025 | 13.4 AI & LLM Observability | ~5 | **High** — tokens, latency, costs, errors for OpenAI/Anthropic/Langchain |
| MITRE ATLAS AI Threat Detection | 8527 | Mar 2026 | 10.9 or 10.3 | ~3 | **High** — prompt injection, jailbreak, data exfil detection |
| LLM Command Scoring | 7932 | Jul 2025 | 10.3 EDR / 13.4 AI | ~2 | Medium — LLM-scored command lines for SOC |
| Dropzone AI App | 8323 | Dec 2025 | 10.7 SIEM & SOAR | ~2 | Low — AI automation platform health |
| Spex M365 Automation Add-on | 7809 | Apr 2025 | 11.1 Microsoft 365 | ~2 | Low — Power Platform/Logic Apps |
| Illumio TA | 3657 | Dec 2025 | 17.3 Zero Trust | ~3 | Medium — micro-segmentation visibility |

### Industry-Specific Apps (🟡 PLANNED / ✅ USED)

| App | Splunkbase ID | Status | Plan Phase |
|---|---|---|---|
| Splunk App for Fraud Analytics | Various | 🟡 PLANNED | Phase 3a/3j |
| Behavioral Profiling App | Various | 🟡 PLANNED | Phase 3a/3j |
| Airport Ground Operations App | 7793 | 🟡 PLANNED | Phase 3g — 21.7 Aviation |
| Airport CIM | GitHub | 🟡 PLANNED | Phase 3g — 21.7 Aviation |
| Tesla App for Splunk | 4660 | 🟡 PLANNED | Phase 3d — 21.4 Transport |
| Splunk App for PCI Compliance | Various | ✅ USED | 10.12.7, 10.12.15 |

---

## 3. External Open-Source & Community Sources

### CISA & MITRE

| Source | URL | Status | Notes |
|---|---|---|---|
| MITRE ATT&CK Enterprise | attack.mitre.org | ✅ USED | Mapped in 10.2-10.7 via ESCU |
| MITRE ATT&CK for ICS | attack.mitre.org/techniques/ics/ | 🟡 PLANNED | Phase 2 — 10.14 OT Security |
| MITRE ATLAS (AI threats) | atlas.mitre.org | 🔵 UNTAPPED | AI/ML attack framework; MITRE ATLAS TA exists |
| CISA ICSNPP Parsers | github.com/cisagov/ICSNPP | 🟡 PLANNED | Phase 1a — Zeek ICS protocol parsers |
| CISA Advisories | cisa.gov/advisories | 🔵 UNTAPPED | Check quarterly for new ICS/OT advisories |

### OT / IoT Vendor Documentation

| Source | URL | Status | Notes |
|---|---|---|---|
| Litmus Edge Splunk Integration | litmus.io/integrations/splunk | 🟡 PLANNED | Phase 1b — 14.7 Litmus Edge |
| HiveMQ Splunk Extension | hivemq.com/extensions | 🟡 PLANNED | Phase 1c — HiveMQ MQTT |
| HiveMQ Documentation | docs.hivemq.com | 🟡 PLANNED | Cluster health, shared subscriptions |
| Zeek ICS Protocol Analyzers | docs.zeek.org/en/master/script-reference/proto-analyzers.html | 🟡 PLANNED | Phase 1a — protocol-specific UCs |
| OPC Foundation | opcfoundation.org | ✅ USED | OPC-UA in 14.5 |
| Modbus.org | modbus.org | ✅ USED | Modbus protocol in 14.2 |

### Regulatory Framework Documentation

The regulatory corpus has been formalised into `data/regulations.json`
since v6.0 &mdash; every framework below now carries an authoritative
`commonClauses[]` list with `obligationText`, a `clauseGrammar` regex
for clause-string validation, and generated machine-readable endpoints
under `/api/v1/compliance/regulations/{id}.json`. Coverage is
auditable via `scripts/audit_compliance_mappings.py` (baseline lives
in `tests/golden/audit-baseline.json`). Full tier-1 + tier-2 coverage
reached **1,395 UCs / 1,964 compliance entries / 946 clauses** in v7.1.

| Source | URL | Status | Notes |
|---|---|---|---|
| GDPR Full Text | gdpr-info.eu | ✅ USED | Tier-1; Cat 22.1; 100% common-clause coverage; `obligationText` on Art.5 / Art.32 / Art.33 |
| NIS2 Directive | eur-lex.europa.eu (Directive 2022/2555) | ✅ USED | Tier-1; Cat 22.2; evidence pack + story payload shipped |
| DORA Regulation | eur-lex.europa.eu (Regulation 2022/2554) | ✅ USED | Tier-1; Cat 22.3; RTS references in NIS2 + DORA cross-walks |
| CCPA/CPRA Text | oag.ca.gov/privacy/ccpa | ✅ USED | Tier-2; Cat 22.4; contributing coverage on &sect;1798.100 + &sect;1798.150 |
| MiFID II | esma.europa.eu | ✅ USED | Tier-2; Cat 22.5; MiFID II operational controls UCs |
| ISO 27001:2022 | iso.org/standard/27001 | ✅ USED | Tier-1; Cat 22.6; Annex A controls mapped to UCs; full `obligationText` backfill in v7.1 |
| NIST CSF 2.0 | nist.gov/cyberframework | ✅ USED | Tier-1; Cat 22.7; Identify / Protect / Detect / Respond / Recover / Govern covered |
| SOC 2 Trust Services Criteria | aicpa.org | ✅ USED | Tier-2; Cat 22.8; CC1&ndash;CC9 common criteria |
| NERC CIP Standards | nerc.com/pa/Stand/Pages/CIPStandards.aspx | ✅ USED | Tier-1; CIP-002 &ndash; CIP-014 covered; OT/ICS cross-walks to Cat 14 |
| PCI DSS v4.0 | pcisecuritystandards.org | ✅ USED | Tier-1; requirement 1&ndash;12 common clauses; evidence pack + Splunk app shipped |
| HIPAA Security Rule | hhs.gov/hipaa | ✅ USED | Tier-1; &sect;164.308 / &sect;164.310 / &sect;164.312 mapped; HIPAA + HITECH evidence packs |
| NIST 800-53 Rev 5 | csrc.nist.gov/publications/detail/sp/800-53/rev-5/final | ✅ USED | Tier-1; AC / AU / CM / IA / SC / SI control families |
| FedRAMP Moderate Baseline | fedramp.gov/documents-templates/ | ✅ USED | Tier-2; derives from 800-53 Rev 5 |
| SOX 404 IT General Controls | sarbanes-oxley-101.com | ✅ USED | Tier-1; PCAOB AS-5 control mappings |
| CMMC Level 2 | dodcio.defense.gov/CMMC/ | ✅ USED | Tier-2; 14 domains cross-walked to 800-171 |
| FISMA | nist.gov/itl/smallbusinesscyber/cybersecurity-basics/fisma | ✅ USED | Tier-2; 800-53 moderate baseline |
| CJIS Security Policy | fbi.gov/services/cjis/ | ✅ USED | Tier-2; criminal-justice information handling |
| LGPD (Brazil) | planalto.gov.br/ccivil_03/\_ato2015-2018/2018/lei/l13709.htm | ✅ USED | Tier-2; GDPR-mapped mode |
| PDPA (Singapore) | pdpc.gov.sg | ✅ USED | Tier-2 |
| PIPEDA (Canada) | priv.gc.ca | ✅ USED | Tier-2 |
| Australian Privacy Principles | oaic.gov.au/privacy/australian-privacy-principles | ✅ USED | Tier-2 |
| COPPA | ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa | ✅ USED | Tier-2; story payload ships with `uncovered` clauses flagged |
| IEC 62443 | iec.ch | ✅ USED | Tier-1; OT/ICS security; cross-walked to NIS2 Annex I |
| HKMA Supervisory Policy Manual | hkma.gov.hk/eng/regulatory-resources/ | ✅ USED | Tier-2; Hong Kong banking resilience |
| UK GDPR + Data Protection Act 2018 | ico.org.uk | ✅ USED | Tier-2; GDPR-derived |
| PSD2 / SCA (EU) | eba.europa.eu | ✅ USED | Tier-2; financial services strong-customer-auth |
| KYC / AML Directives | eba.europa.eu | ✅ USED | Tier-2; money-laundering directives |
| Full tier inventory | `data/regulations.json` &mdash; **66 frameworks** total | ✅ USED | 11 tier-1, 54 tier-2, 1 tier-3 (browse via `regulatory-primer.html` + `api/v1/compliance/regulations/index.json`) |

### Community & Partner Resources

| Source | URL | Status | Notes |
|---|---|---|---|
| Splunk Community (Splunk Answers) | community.splunk.com | ✅ USED | User-contributed SPL, troubleshooting |
| Splunk .conf Session Catalog | conf.splunk.com/sessions.html | 🔵 UNTAPPED | .conf25 had 250+ sessions; check recordings for new UC ideas |
| Cisco Blogs (IoT/OT) | blogs.cisco.com/industrial-iot | 🟡 PLANNED | NIS2 compliance, OT/IT convergence |
| Cisco Solution Briefs | cisco.com/c/en/us/products/collateral/security/ | 🟡 PLANNED | NIS2 + Cisco framework |

---

## 4. Story-Layer APIs & Tooling (new since v3.20)

The v6.0 &rarr; v7.1 releases added a full machine-readable story layer
for the regulatory corpus. These endpoints and tools are themselves
content sources &mdash; review them quarterly alongside the upstream
regulator documentation to catch drift between the catalogue and the
published obligation texts.

### Compliance API endpoints (`api/v1/compliance/`)

| Endpoint | Generator | Status | Notes |
|---|---|---|---|
| `compliance/index.json` | `scripts/generate_api_surface.py` | ✅ USED | Catalogue-wide rollup: regulations covered, tier counts, average assurance |
| `compliance/coverage.json` | `scripts/generate_api_surface.py` | ✅ USED | Per-regulation coverage-matrix summary |
| `compliance/gaps.json` | `scripts/generate_api_surface.py` | ✅ USED | Every `uncovered` common-clause, sorted by priority weight |
| `compliance/regulations/{id}.json` | `scripts/augment_regulation_api.py` | ✅ USED | Per-framework detail + `clauseCoverageMatrix[]` per version (v7.1) |
| `compliance/regulations/{id}@{version}.json` | `scripts/generate_api_surface.py` | ✅ USED | Per-version pointer with jurisdiction / tags |
| `compliance/clauses/index.json` | `scripts/generate_clause_index.py` | ✅ USED | Flat registry of 946 clauses (coverage state, covering UCs, `obligationText`, priority weight) |
| `compliance/clauses/{clauseId}.json` | `scripts/generate_clause_index.py` | ✅ USED | Per-clause reverse index &mdash; every UC that covers this clause with `controlObjective` + `evidenceArtifact` |
| `compliance/story/{regulationId}.json` | `scripts/generate_story_payload.py` | ✅ USED | Unified buyer/auditor/implementer narrative; 67 payloads shipped |
| `compliance/story/index.json` | `scripts/generate_story_payload.py` | ✅ USED | Story-landing rollup |
| `compliance/ucs/index.json` | `scripts/generate_api_surface.py` | ✅ USED | Compact list of compliance-tagged UCs |
| `compliance/ucs/{ucId}.json` | `scripts/generate_api_surface.py` | ✅ USED | Full UC sidecar (canonical form) &mdash; 6,447 per-UC files under `api/v1/` |
| `oscal/` catalogues + components | `scripts/generate_api_surface.py` | ✅ USED | OSCAL-flavoured exports for GRC tooling ingestion |

### Audience surfaces (HTML pages served next to `index.html`)

| Page | Audience | Status | Notes |
|---|---|---|---|
| `clause-navigator.html` | Auditor | ✅ USED | Clause-first table; deep-linkable as `#clause={clauseId}` or `#reg={regId}`; reads `compliance/clauses/index.json` |
| `compliance-story.html?reg={id}` | Buyer | ✅ USED | Per-regulation narrative (coverage headline / top-five highlights / top-three gaps); reads `compliance/story/{id}.json` |
| `regulatory-primer.html` | Legal / privacy / risk | ✅ USED | Reader view over `docs/regulatory-primer.md`; autolinks inline `<code>` clause references into the clause navigator (v7.1) |
| `scorecard.html` | Programme manager | ✅ USED | Tier-1 regulation scorecard; reads `compliance/regulations/{id}.json` |
| `index.html` (main catalogue) | Implementer | ✅ USED | Two-level regulation/clause filter; clause-level table on the UC detail panel (v7.1); new header audience-switch nav |

### Evidence packs (`docs/evidence-packs/*.md`)

Auditor-facing markdown packs. **12 packs** ship in v7.1, one per
tier-1 regulation plus the major tier-2 frameworks. Each pack now
ships a &ldquo;Live views&rdquo; block linking the reader to the
buyer narrative, the auditor clause navigator, and the JSON twin.
Generator: `scripts/generate_evidence_packs.py`.

| Pack | Regulation | Status |
|---|---|---|
| `docs/evidence-packs/gdpr.md` | GDPR | ✅ USED |
| `docs/evidence-packs/hipaa-security.md` | HIPAA Security Rule | ✅ USED |
| `docs/evidence-packs/pci-dss.md` | PCI DSS v4.0 | ✅ USED |
| `docs/evidence-packs/iso-27001.md` | ISO 27001:2022 | ✅ USED |
| `docs/evidence-packs/nist-csf.md` | NIST CSF 2.0 | ✅ USED |
| `docs/evidence-packs/nist-800-53.md` | NIST 800-53 Rev 5 | ✅ USED |
| `docs/evidence-packs/nis2.md` | NIS2 | ✅ USED |
| `docs/evidence-packs/dora.md` | DORA | ✅ USED |
| `docs/evidence-packs/sox.md` | SOX 404 ITGC | ✅ USED |
| `docs/evidence-packs/nerc-cip.md` | NERC CIP | ✅ USED |
| `docs/evidence-packs/iec-62443.md` | IEC 62443 | ✅ USED |
| `docs/evidence-packs/soc-2.md` | SOC 2 | ✅ USED |

### MCP server (`mcp/`, v1.6.x) &mdash; ten tools

The Model Context Protocol server exposes the catalogue to LLM clients
(Claude, GPT, Gemini, Mistral) via JSON-RPC with stable output
schemas. Install with `pip install -e mcp/[test]`. Drift-guarded by
`scripts/audit_mcp_tool_schemas.py` in CI.

| Tool | Status | Notes |
|---|---|---|
| `search_use_cases(query, category, regulation, equipment, mitre, limit)` | ✅ USED | Keyword + facet search; returns slim UC records |
| `get_use_case(uc_id)` | ✅ USED | Full UC detail; `compliance[]` always present (empty for non-compliance UCs) |
| `list_categories()` | ✅ USED | 23 categories &times; 189 subcategories with UC counts |
| `list_regulations(tier?)` | ✅ USED | 66 frameworks with jurisdiction / tags / UC counts |
| `get_regulation(regulation_id, version?)` | ✅ USED | Per-framework detail with `clauseCoverageMatrix[]` |
| `list_equipment(min_use_case_count?, regulation_id?)` | ✅ USED | Equipment inventory rollup |
| `get_equipment(equipment_id)` | ✅ USED | Equipment detail (tag, UCs, regulations, categories) |
| `find_compliance_gap(regulations[], equipment_id?)` | ✅ USED | Uncovered clauses with optional equipment overlay |
| `get_clause_coverage(regulation_id, clause, version?)` | ✅ USED (v7.1) | Per-clause detail: `coverageState`, `coveringUcs`, deep link to the clause navigator |
| `list_uncovered_clauses(regulations[], tier?, include_common_only?, limit?)` | ✅ USED (v7.1) | Uncovered clauses sorted by priority weight |

### Per-regulation Splunk apps (`splunk-apps/`)

Phase 1.8+ POC &rarr; v7.x: one AppInspect-shaped Splunk app per
tier-1 regulation. Each app ships `metadata/default.meta`, a
regulation-specific README, a correlation-search alert action
(`action.uc_compliance.param.{clauses,versions,uc_id,regulation}`),
and a `savedsearches.conf` block driven by the compliance tuples from
`tests/golden/compliance-truth.json`. Packaged via `scripts/pack_apps.py`
and published under `dist/splunk-apps/`.

---

## 5. Customer Stories & Case Studies

These provide validation that real deployments exist for specific use cases.

| Customer / Story | Source | Status | Relevant Category |
|---|---|---|---|
| Dubai Airports | Splunkbase / Splunk blog | 🟡 PLANNED | 21.7 Aviation |
| Gatwick Airport | Splunk customer story | 🟡 PLANNED | 21.7 Aviation |
| Continental AG (automotive) | splunk.com case study | 🟡 PLANNED | 21.4 Transportation |
| Argos (energy) | splunk.com case study | 🟡 PLANNED | 21.1 Energy |
| Bosch Rexroth (manufacturing) | splunk.com case study | 🟡 PLANNED | 21.2 Manufacturing |
| Cisco Store (retail) | Splunk Lantern | 🟡 PLANNED | 21.6 Retail |
| Conducive SI (water districts) | Partner blog | 🟡 PLANNED | 21.9 Water |
| Somerford (water treatment) | Confluent+Splunk blog | 🟡 PLANNED | 21.9 Water |

---

## 6. Quick Win Opportunities

Sources that could yield new UCs with minimal effort — but should be weighed against catalog balance.

### High Priority (fills observability gaps, not in Cat 10)

| Source | Est. UCs | Target Category | Rationale |
|---|---|---|---|
| GenAI Observability App (Splunkbase 8308) | ~5 | 13.4 AI & LLM Observability | Timely; OpenAI/Anthropic/Langchain token/latency/cost monitoring |
| Aruba TA (Splunkbase 5579) | ~5 | 5.4 Wireless Infrastructure | Fills wireless vendor gap; Aruba is #2 enterprise wireless |
| Rubrik TA (Splunkbase 4834) | ~4 | 6.3 Backup & Recovery | Fills modern backup gap; Rubrik is major data protection vendor |
| Splunk Lantern APM use cases | ~3 | 8 or 13 | OpenAI API monitoring, Lambda, third-party API calls |
| MITRE ATLAS AI Threat Detection (Splunkbase 8527) | ~3 | 10.9 or 13.4 | Prompt injection, jailbreak, exfil — new threat category |

### Medium Priority (adds security vendor breadth)

| Source | Est. UCs | Target Category | Rationale |
|---|---|---|---|
| SentinelOne TA (Splunkbase 5765) | ~8 | 10.11 Vendor Security | Major EDR; rounds out vendor coverage alongside CrowdStrike/Carbon Black |
| Sophos TA (Splunkbase 4646) | ~6 | 10.11 Vendor Security | Endpoint + firewall; popular in mid-market |
| Trend Micro TA (Splunkbase 3965) | ~6 | 10.11 Vendor Security | Deep Security, Apex One, Cloud One |
| Mimecast TA (Splunkbase 3200) | ~5 | 10.4 Email Security | Rounds out email security alongside Proofpoint |
| Illumio TA (Splunkbase 3657) | ~3 | 17.3 Zero Trust | Micro-segmentation visibility |

### Low Priority (diminishing returns)

| Source | Est. UCs | Target Category | Rationale |
|---|---|---|---|
| Barracuda TA | ~4 | 10.4/10.5 | Overlaps with existing email/web security UCs |
| Symantec/Broadcom TA | ~5 | 10.11 | Declining market share |
| McAfee/Trellix TA | ~4 | 10.11 | Declining market share |
| Orca Security | ~3 | 10.6 | Cloud security posture — similar to Wiz (already covered) |
| Veritas NetBackup | ~3 | 6.3 | Legacy backup — Commvault/Veeam already covered |
| Datadog integration | ~3 | 13.3 | Competitor product — awkward to feature |
| Nagios integration | ~2 | 13.3 | Legacy monitoring — Prometheus already covered |
| Confluence TA | ~3 | 11/12 | Niche collaboration use cases |

---

## 7. Periodic Review Checklist

Sources to check on a regular cadence for updates:

### Monthly
- [ ] research.splunk.com/stories — new ESCU analytic stories
- [ ] Splunk Security Blog — new detection content, threat advisories
- [ ] Splunkbase "Recently Updated" — new/updated TAs

### Quarterly
- [ ] Splunk Lantern — new use cases, industry content, data descriptors
- [ ] CISA Advisories — new ICS/OT advisories
- [ ] MITRE ATT&CK — technique additions and sub-technique changes
- [ ] Splunkbase "New Apps" — emerging integrations
- [ ] Regulator source URLs — spot-check `obligationSource` links in `data/regulations.json` for dead/moved pages
- [ ] Compliance audit baseline — reconcile `tests/golden/audit-baseline.json`; new blocker errors should drop to zero before the next release

### Annually (or at .conf)
- [ ] .conf session catalog — new features, customer stories, emerging patterns
- [ ] Splunk product announcements — new products, deprecated features
- [ ] Regulatory updates — NIS2 transposition status, DORA RTS updates, PCI DSS version changes, new tier-2 frameworks (e.g. India DPDP Act rules, KSA PDPL executive regulations)
- [ ] Industry-specific Splunk solution pages — new customer stories and capabilities

### Ad-hoc (on major events)
- [ ] Major CVE / zero-day — check if ESCU has new detection content
- [ ] New EU/US regulation — assess Splunk monitoring angle, open a new `data/regulations.json` stub with `tier` and `clauseGrammar`
- [ ] Splunk acquisition / partnership — new integration opportunities
- [ ] Major Splunkbase app release — assess UC potential

---

## 8. Coverage Statistics (as of 2026-04-20, catalogue v7.1)

| Metric | Value |
|---|---|
| Total UCs in catalogue | **6,447** (+1,822 since 2026-03-20) |
| Categories | **23** (+1 since 2026-03-20: Cat 22 regulatory-compliance split into 49 subcategories) |
| Subcategories | **189** (+67 since 2026-03-20) |
| Unique TAs / Apps referenced | **~2,635** (+~935 since 2026-03-20) |
| Security pillar UCs | 4,451 (69.0%) |
| Observability pillar UCs | 1,981 (30.7%) |
| Cat 10 (Security Infrastructure) share | 2,402 (37.3%) &mdash; dominance reduced from 51% as Cat 22 grew |
| Cat 22 (Regulatory Compliance) share | 1,310 (20.3%) |
| Cat 14 (OT/IoT) share | 230 (3.6%) |
| ESCU-derived UCs | ~2,068 (unchanged) |
| Regulations tracked in `data/regulations.json` | **66** (11 tier-1, 54 tier-2, 1 tier-3) |
| UCs with at least one `compliance[]` entry | 1,395 (21.6% of catalogue) |
| Total compliance entries (UC &times; clause pairs) | 1,964 |
| Unique clauses in `api/v1/compliance/clauses/index.json` | 946 |
| Story payloads (`api/v1/compliance/story/*.json`) | 67 |
| Evidence packs (`docs/evidence-packs/*.md`) | 12 |
| MCP tools exposed to LLM clients | 10 |
| Schema version &mdash; UC sidecars | 1.6.1 |
| Schema version &mdash; `data/regulations.json` | 1.1.0 |

### Source coverage at a glance

| Source family | USED | PLANNED | UNTAPPED | Notes |
|---|---|---|---|---|
| Lantern + ESCU + docs.splunk.com | 14 | 3 | 1 | 🔵 `docs.splunk.com/.../Listofpretrainedsourcetypes` still the best gap-analysis source |
| Splunk blogs | 4 | 1 | 1 | .conf25/.conf26 recaps still untapped |
| Core platform TAs | 13 | 0 | 0 | Covered |
| Cisco TAs | 4 | 0 | 0 | Covered |
| Security vendor TAs (used) | 13 | 0 | 0 | Covered |
| Security vendor TAs (untapped) | 0 | 0 | 7 | SentinelOne / Sophos / Trend Micro highest value |
| OT / IoT TAs | 1 | 4 | 0 | Still in expansion plan (Phase 1a/1b/1c) |
| Industry-specific apps | 1 | 5 | 0 | Aviation, transport, retail pending |
| Regulatory frameworks | **27** | 0 | 0 | Tier-1 fully covered; tier-2 buffer in `data/regulations.json` (see regulation table for the long tail) |
| Compliance APIs (new) | 12 | 0 | 0 | Story, clauses, regulations, ucs, oscal endpoints |
| Audience surfaces (new) | 5 | 0 | 0 | index, clause-navigator, compliance-story, regulatory-primer, scorecard |
| Evidence packs (new) | 12 | 0 | 0 | All tier-1 + SOC 2 + DORA + NIS2 + CIP + IEC 62443 |
| MCP tools (new) | 10 | 0 | 0 | All ten shipped and drift-guarded |
