# Use Case Source Catalog

Comprehensive reference of all sources used (and not yet used) to develop use cases in this repository. Check these periodically for new content, updated TAs, and emerging integrations.

**Legend:**
- ✅ **USED** — Source actively used; UCs already in catalog
- 🟡 **PLANNED** — Source researched; UCs in expansion plan but not yet written
- 🔵 **UNTAPPED** — Promising source with real Splunk backing; not yet used
- ⬜ **LOW PRIORITY** — Source exists but adds marginal value given current coverage

Last reviewed: 2026-05-01 (catalogue v7.3)

> **What changed since the v3.20 review (2026-03-20):** the catalogue
> grew from 4,625 UCs / 22 categories / 122 subcategories to
> **7,364 UCs / 23 categories / 212 subcategories**. The regulatory
> corpus was rebuilt on top of `data/regulations.json` (69 frameworks
> across three tiers), every tier-1 regulation is now covered by a
> deep `commonClauses[]` matrix with `obligationText`, and the
> catalogue ships clause-level machine APIs under `api/v1/compliance/`
> (story, clause-navigator, and per-regulation payloads). The MCP
> server (`mcp/`) now exposes ten tools covering the whole corpus.
>
> **v7.2 (2026-04-29):** 195 UCs rewritten to the true-gold standard
> across cat-01, cat-18, cat-19, and cat-23; cat-23 Business Analytics
> (63 UCs) and cat-19 Compute Infrastructure (93 UCs) reached 100%
> coverage.
>
> **v7.3 (2026-04-30):** 27 Gold-tier UCs via Lantern UCE enrichment,
> 89 UCs enriched; interactive knowledge graph (`graph.html`) added;
> 78 Cisco Catalyst Center UCs (5.13.1–5.13.78) fully handwritten to
> gold standard; 57 NIS2 UCs deeply uplifted; 14 OpenShift UCs added.
>
> See `CHANGELOG.md` v3.21 &rarr; v7.3 and
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
| Cisco Catalyst Add-on | 7538 | ~78 | 5.1, 5.13 (Catalyst Center Intent API + syslog/Netflow) |

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

### Regulatory & Standards Source Register

This section documents **where all regulatory and standards content
comes from**. Every obligation text, clause identifier, and coverage
mapping in this catalogue traces back to the authoritative sources
listed below.

#### How regulatory content is sourced

1. **Primary sources.** Obligation text is taken verbatim (or closely
   paraphrased) from official government gazettes, regulator websites,
   and standards body publications. The `authoritativeUrl` field in
   `data/regulations.json` links each framework to its canonical
   online publication.
2. **Clause-level citations.** Many frameworks carry per-clause deep
   links via `clauseUrlTemplate` or individual `obligationSource`
   URLs that resolve to the specific article, section, or requirement
   within the source document (e.g., Eur-Lex article anchors, eCFR
   section links, PCI DSS PDF page numbers).
3. **Crosswalks.** Derivative relationships (e.g., UK GDPR derives
   from EU GDPR; FedRAMP from NIST 800-53) are encoded in the
   `derivesFrom` graph within `data/regulations.json`, with explicit
   `clauseMapping` and `divergences` arrays.
4. **Provenance tracking.** Ingested crosswalk datasets (MITRE
   ATT&CK, NIST OLIR, CTID, D3FEND, Atomic Red Team) are
   SHA-256-hashed in `data/provenance/ingest-manifest.json`. Legal
   attribution is documented in `LEGAL.md`.
5. **Verification.** Coverage is auditable via
   `scripts/audit_compliance_mappings.py` (baseline in
   `tests/golden/audit-baseline.json`). Clause-string formats are
   validated by the `clauseGrammar` regex in each framework version.

Machine-readable endpoints at `api/v1/compliance/regulations/{id}.json`
expose the full per-framework detail including `clauseCoverageMatrix[]`.
Browse interactively at `regulatory-primer.html` or query via MCP
tool `get_regulation(regulation_id)`.

Full corpus: **69 frameworks**, **994 clauses**, **1,452 compliance-tagged UCs**,
**2,082 compliance entries**.

#### Tier 1 &mdash; primary frameworks (11)

Deep clause coverage, evidence packs, story payloads, and per-regulation
Splunk apps. These frameworks are the foundation of the compliance
programme.

| Framework | Jurisdiction | Authoritative Source | Issuing Body |
|---|---|---|---|
| GDPR | EU, EEA | [Regulation 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj) | European Parliament & Council |
| NIS2 Directive | EU | [Directive 2022/2555](https://eur-lex.europa.eu/eli/dir/2022/2555/oj) | European Parliament & Council |
| DORA | EU | [Regulation 2022/2554](https://eur-lex.europa.eu/eli/reg/2022/2554/oj) | European Parliament & Council |
| PCI DSS v4.0 | Global | [PCI Document Library](https://www.pcisecuritystandards.org/document_library/) | PCI Security Standards Council |
| HIPAA Security Rule | US | [45 CFR 164 Subpart C](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C) | HHS Office for Civil Rights |
| NIST CSF 2.0 | US, Global | [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/framework) | NIST |
| NIST 800-53 Rev 5 | US | [SP 800-53 Rev 5](https://csrc.nist.gov/pubs/sp/800/53/r5/final) | NIST CSRC |
| ISO 27001:2022 | Global | [ISO/IEC 27001](https://www.iso.org/standard/27001) | ISO / IEC |
| SOC 2 | US, Global | [SOC Suite of Services](https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services) | AICPA-CIMA |
| SOX ITGC | US | [PCAOB AS 2201](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201) | PCAOB |
| CMMC Level 2 | US | [CMMC Programme](https://dodcio.defense.gov/CMMC/) | US DoD CIO |

#### Tier 2 &mdash; extended frameworks (56)

Contributing coverage via clause mappings, crosswalks, or GDPR-derived
modes. Listed by jurisdiction.

**European Union**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| EU AI Act | [Regulation 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) | European Parliament & Council |
| EU Cyber Resilience Act | [Regulation 2024/2847](https://eur-lex.europa.eu/eli/reg/2024/2847/oj) | European Parliament & Council |
| PSD2 | [Directive 2015/2366](https://eur-lex.europa.eu/eli/dir/2015/2366/oj) | European Parliament & Council |
| MiFID II | [Directive 2014/65](https://eur-lex.europa.eu/eli/dir/2014/65/oj) | European Parliament & Council |
| EU AML Regulation | [Regulation 2024/1624](https://eur-lex.europa.eu/eli/reg/2024/1624/oj) | European Parliament & Council |
| eIDAS 2.0 | [Regulation 2024/1183](https://eur-lex.europa.eu/eli/reg/2024/1183/oj) | European Parliament & Council |

**United States**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| FedRAMP | [FedRAMP Baselines](https://www.fedramp.gov/baselines/) | GSA / FedRAMP PMO |
| FISMA | [Senate Bill 2521](https://www.congress.gov/bill/113th-congress/senate-bill/2521) | US Congress |
| CJIS Security Policy | [CJIS Resource Center](https://le.fbi.gov/cjis-division/cjis-security-policy-resource-center) | FBI CJIS Division |
| HIPAA Privacy Rule | [45 CFR 164 Subpart E](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E) | HHS OCR |
| CCPA/CPRA | [CPPA Regulations](https://cppa.ca.gov/regulations/) | California Privacy Protection Agency |
| COPPA | [16 CFR 312](https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-312) | FTC |
| FERPA | [34 CFR 99](https://www.ecfr.gov/current/title-34/subtitle-A/part-99) | US Dept. of Education |
| GLBA Safeguards | [16 CFR 314](https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-314) | FTC |
| FDA 21 CFR Part 11 | [21 CFR Part 11](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11) | FDA |
| TSA Security Directives | [TSA SD-02C](https://www.tsa.gov/sd02c) | TSA |
| HITRUST CSF | [HITRUST CSF Overview](https://hitrustalliance.net/csf-overview/) | HITRUST Alliance |
| NERC CIP | [CIP Standards](https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx) | NERC |

**United Kingdom**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| UK GDPR | [Retained EU Regulation 2016/679](https://www.legislation.gov.uk/eur/2016/679/contents) | UK Parliament (retained EU law) |
| UK NIS Regulations | [SI 2018/506](https://www.legislation.gov.uk/uksi/2018/506/contents) | UK Parliament |
| FCA SM&CR | [SM&CR](https://www.fca.org.uk/firms/senior-managers-certification-regime) | Financial Conduct Authority |
| FCA SS1/21 | [PS21-3 (PDF)](https://www.fca.org.uk/publication/policy/ps21-3.pdf) | Financial Conduct Authority |
| PRA SS2/21 | [Outsourcing and Third-Party Risk](https://www.bankofengland.co.uk/prudential-regulation/publication/2021/march/outsourcing-and-third-party-risk-management-ss) | Bank of England / PRA |
| Cyber Essentials | [Cyber Essentials Overview](https://www.ncsc.gov.uk/cyberessentials/overview) | NCSC |

**Germany**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| BAIT/KAIT | [BAIT Circular (EN)](https://www.bafin.de/SharedDocs/Veroeffentlichungen/EN/Rundschreiben/2021/rs_1021_BAIT_en.html) | BaFin |
| BSI-KritisV | [BSI-KritisV](https://www.gesetze-im-internet.de/bsi-kritisv/) | BSI |
| IT-Grundschutz | [IT-Grundschutz](https://www.bsi.bund.de/EN/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/it-grundschutz_node.html) | BSI |
| IT-SiG 2.0 | [Bundesgesetzblatt](https://www.bgbl.de/xaver/bgbl/start.xav?startbk=Bundesanzeiger_BGBl&start=//*[@attr_id=%27bgbl121s1122.pdf%27]) | German Federal Parliament |

**Norway**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| Personopplysningsloven | [Lov 2018-06-15-38](https://lovdata.no/dokument/NL/lov/2018-06-15-38) | Stortinget |
| Kraftberedskapsforskriften | [Forskrift 2012-12-07-1157](https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157) | NVE / OED |
| Petroleumsforskriften | [Forskrift 1997-06-27-653](https://lovdata.no/dokument/SF/forskrift/1997-06-27-653) | Petroleumstilsynet |
| Sikkerhetsloven | [Lov 2018-06-01-24](https://lovdata.no/dokument/NL/lov/2018-06-01-24) | Stortinget |

**Asia-Pacific**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| SG PDPA | [PDPA 2012](https://sso.agc.gov.sg/Act/PDPA2012) | PDPC (Singapore) |
| MAS TRM Guidelines | [TRM Guidelines (PDF)](https://www.mas.gov.sg/-/media/mas/regulations-and-financial-stability/regulatory-and-supervisory-framework/risk-management/trm-guidelines-18-january-2021.pdf) | MAS (Singapore) |
| APPI | [APPI Legal Portal](https://www.ppc.go.jp/en/legal/) | PPC (Japan) |
| PIPL | [PIPL Full Text](http://www.npc.gov.cn/npc/c2/c30834/202108/t20210820_313088.html) | NPC Standing Committee (China) |
| HKMA TM-G-2 | [SPM Hub](https://www.hkma.gov.hk/eng/regulatory-resources/regulatory-guides/supervisory-policy-manual/) | HKMA (Hong Kong) |
| RBI Cyber Security | [RBI Notification](https://rbi.org.in/Scripts/NotificationUser.aspx?Id=10435) | Reserve Bank of India |
| AU Privacy Act | [Privacy Act 1988](https://www.legislation.gov.au/C2004A03712/latest/text) | OAIC (Australia) |
| APRA CPS 234 | [CPS 234](https://www.apra.gov.au/information-security) | APRA (Australia) |
| ASD Essential Eight | [Essential Eight Maturity Model](https://www.cyber.gov.au/resources-business-and-government/essential-cyber-security/essential-eight/essential-eight-maturity-model) | ASD (Australia) |
| NZISM | [NZ ISM](https://www.nzism.gcsb.govt.nz/) | GCSB (New Zealand) |

**Americas (non-US)**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| LGPD (Brazil) | [Lei 13709/2018](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) | Planalto (Brazil) |

**Switzerland**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| Swiss nFADP | [nFADP (Fedlex)](https://www.fedlex.admin.ch/eli/cc/2022/491/en) | Swiss Federal Council |

**Middle East**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| NESA IAS | [NESA Portal](https://www.nesa.gov.ae/) | NESA (UAE) |
| QCB Cyber | [QCB Portal](https://www.qcb.gov.qa/) | Qatar Central Bank |
| SAMA CSF | [SAMA CSF (PDF)](https://www.sama.gov.sa/en-US/Laws/BankingRules/SAMA%20Cyber%20Security%20Framework.pdf) | SAMA (Saudi Arabia) |
| SA PDPL | [PDPL (PDF)](https://sdaia.gov.sa/en/SDAIA/about/Files/PersonalDataEnglish.pdf) | SDAIA (Saudi Arabia) |

**Global / industry bodies**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| IEC 62443 | [ISA/IEC 62443 Series](https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards) | ISA / IEC |
| ISO 27001 | [ISO/IEC 27001](https://www.iso.org/standard/54534.html) | ISO / IEC |
| SWIFT CSP | [SWIFT CSP Controls](https://www.swift.com/myswift/customer-security-programme-csp/security-controls) | SWIFT |
| API RP 1164 | [API Standard 1164](https://www.api.org/products-and-services/standards/important-standards-announcements/standard-1164) | American Petroleum Institute |
| Basel III | [BIS BCBS d516](https://www.bis.org/bcbs/publ/d516.htm) | BIS / BCBS |
| COSO | [COSO IC Guidance](https://www.coso.org/guidance-on-ic) | COSO |
| COBIT | [COBIT Resources](https://www.isaca.org/resources/cobit) | ISACA |
| UN R155 (Vehicle Cyber) | [UN R155](https://unece.org/transport/documents/2021/03/standards/un-regulation-no-155-cyber-security-and-cyber-security) | UNECE |
| UN R156 (Software Update) | [UN R156](https://unece.org/transport/documents/2021/03/standards/un-regulation-no-156-software-update-and-software-update) | UNECE |

**Tier 3**

| Framework | Authoritative Source | Issuing Body |
|---|---|---|
| FERC CIP | [FERC CIP](https://www.ferc.gov/industries-data/electric/industry-activities/critical-infrastructure-protection) | FERC |

#### Provenance and verification artefacts

| Artefact | Path | Purpose |
|---|---|---|
| Regulations database | `data/regulations.json` | Single source of truth for all 69 frameworks, versions, clauses, and authoritative URLs |
| Crosswalks | `data/crosswalks/` | OLIR/OSCAL-normalised mappings between frameworks |
| Ingest manifest | `data/provenance/ingest-manifest.json` | SHA-256 hashes of all ingested upstream datasets (ATT&CK, CTID, D3FEND, Atomic Red Team) |
| Legal attribution | `LEGAL.md` | Per-source licensing and attribution requirements |
| Coverage methodology | `docs/coverage-methodology.md` | How coverage percentages, priority weights, and assurance levels are calculated |
| Regulatory primer | `docs/regulatory-primer.md` | Reader-facing overview with supervisory authority table and appendices |
| Audit baseline | `tests/golden/audit-baseline.json` | CI-enforced baseline for `scripts/audit_compliance_mappings.py` |

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
| `compliance/clauses/index.json` | `scripts/generate_clause_index.py` | ✅ USED | Flat registry of 994 clauses (coverage state, covering UCs, `obligationText`, priority weight) |
| `compliance/clauses/{clauseId}.json` | `scripts/generate_clause_index.py` | ✅ USED | Per-clause reverse index &mdash; every UC that covers this clause with `controlObjective` + `evidenceArtifact` |
| `compliance/story/{regulationId}.json` | `scripts/generate_story_payload.py` | ✅ USED | Unified buyer/auditor/implementer narrative; 70 payloads shipped |
| `compliance/story/index.json` | `scripts/generate_story_payload.py` | ✅ USED | Story-landing rollup |
| `compliance/ucs/index.json` | `scripts/generate_api_surface.py` | ✅ USED | Compact list of compliance-tagged UCs |
| `compliance/ucs/{ucId}.json` | `scripts/generate_api_surface.py` | ✅ USED | Full UC sidecar (canonical form) &mdash; **7,364** per-UC JSON exports under `api/v1/` |
| `oscal/` catalogues + components | `scripts/generate_api_surface.py` | ✅ USED | OSCAL-flavoured exports for GRC tooling ingestion |

### Audience surfaces (HTML pages served next to `index.html`)

| Page | Audience | Status | Notes |
|---|---|---|---|
| `clause-navigator.html` | Auditor | ✅ USED | Clause-first table; deep-linkable as `#clause={clauseId}` or `#reg={regId}`; reads `compliance/clauses/index.json` |
| `compliance-story.html?reg={id}` | Buyer | ✅ USED | Per-regulation narrative (coverage headline / top-five highlights / top-three gaps); reads `compliance/story/{id}.json` |
| `regulatory-primer.html` | Legal / privacy / risk | ✅ USED | Reader view over `docs/regulatory-primer.md`; autolinks inline `<code>` clause references into the clause navigator (v7.1) |
| `scorecard.html` | Programme manager | ✅ USED | Tier-1 regulation scorecard; reads `compliance/regulations/{id}.json` |
| `graph.html` | Explorer | ✅ USED | Interactive knowledge graph (Sigma.js): 23 categories, 80 equipment types, 37 CIM models, 4 pillars as nodes with 446 weighted edges; dark mode, search, layer toggles (v7.3) |
| `index.html` (main catalogue) | Implementer | ✅ USED | Two-level regulation/clause filter; clause-level table on the UC detail panel (v7.1); new header audience-switch nav |

### Evidence packs (`docs/evidence-packs/*.md`)

Auditor-facing markdown packs. **13 packs** ship in v7.3, one per
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
| `docs/evidence-packs/sox-itgc.md` | SOX 404 ITGC | ✅ USED |
| `docs/evidence-packs/uk-gdpr.md` | UK GDPR + Data Protection Act 2018 | ✅ USED |
| `docs/evidence-packs/cmmc.md` | CMMC Level 2 | ✅ USED |
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
| `list_categories()` | ✅ USED | 23 categories &times; 212 subcategories with UC counts |
| `list_regulations(tier?)` | ✅ USED | 69 frameworks with jurisdiction / tags / UC counts |
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

## 8. Coverage Statistics (as of 2026-05-01, catalogue v7.3)

| Metric | Value |
|---|---|
| Total UCs in catalogue | **7,364** (+2,739 since 2026-03-20 baseline of 4,625) |
| Categories | **23** (+1 since 2026-03-20: Cat 22 regulatory-compliance split into 70 subcategories) |
| Subcategories | **212** (+90 since 2026-03-20) |
| Unique equipment tags | **241** |
| Security pillar UCs | 4,651 (63.2%) |
| Observability pillar UCs | 2,483 (33.7%) |
| IT Operations pillar UCs | 83 (1.1%) |
| Platform pillar UCs | 147 (2.0%) |
| Cat 10 (Security Infrastructure) share | 2,455 (33.3%) |
| Cat 22 (Regulatory Compliance) share | 1,345 (18.3%) |
| Cat 14 (OT/IoT) share | 249 (3.4%) |
| Regulations tracked in `data/regulations.json` | **69** (schemaVersion 1.1.0) |
| UCs with at least one `compliance[]` entry | 1,452 (19.7% of catalogue) |
| Total compliance entries (UC &times; clause pairs) | 2,082 |
| Unique clauses in `api/v1/compliance/clauses/index.json` | 994 |
| Story payloads (`api/v1/compliance/story/*.json`) | 70 |
| Evidence packs (`docs/evidence-packs/*.md`) | 13 |
| MCP tools exposed to LLM clients | 10 |
| Audience surfaces (HTML pages) | 6 (index, clause-navigator, compliance-story, regulatory-primer, scorecard, graph) |
| Schema version &mdash; UC sidecars | 1.6.1 |
| Schema version &mdash; `data/regulations.json` | 1.1.0 |

### Source coverage at a glance

| Source family | USED | PLANNED | UNTAPPED | Notes |
|---|---|---|---|---|
| Lantern + ESCU + docs.splunk.com | 14 | 3 | 1 | 🔵 `docs.splunk.com/.../Listofpretrainedsourcetypes` still the best gap-analysis source |
| Splunk blogs | 4 | 1 | 1 | .conf25/.conf26 recaps still untapped |
| Core platform TAs | 13 | 0 | 0 | Covered |
| Cisco TAs | 4 | 0 | 0 | Covered; Catalyst Center now has 78 gold-standard UCs (v7.3) |
| Security vendor TAs (used) | 13 | 0 | 0 | Covered |
| Security vendor TAs (untapped) | 0 | 0 | 7 | SentinelOne / Sophos / Trend Micro highest value |
| OT / IoT TAs | 1 | 4 | 0 | Still in expansion plan (Phase 1a/1b/1c) |
| Industry-specific apps | 1 | 5 | 0 | Aviation, transport, retail pending |
| Regulatory frameworks | **27** | 0 | 0 | Tier-1 fully covered; 69 total in `data/regulations.json` |
| Compliance APIs | 12 | 0 | 0 | Story, clauses, regulations, ucs, oscal endpoints |
| Audience surfaces | 6 | 0 | 0 | index, clause-navigator, compliance-story, regulatory-primer, scorecard, graph (v7.3) |
| Evidence packs | 13 | 0 | 0 | All tier-1 + SOC 2 + DORA + NIS2 + CIP + IEC 62443 |
| MCP tools | 10 | 0 | 0 | All ten shipped and drift-guarded |
