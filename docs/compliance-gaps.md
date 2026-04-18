# Compliance clause-level gap analysis

_Generated: 1970-01-01T00:00:00Z_ by `scripts/audit_compliance_gaps.py`. Do not hand-edit.

This report inverts the compliance coverage audit: for every regulation-version listed in `data/regulations.json` it walks every `commonClauses[]` entry and records whether at least one non-draft UC sidecar tags that clause. Gaps are ranked by the clause's `priorityWeight` so authoring effort can focus on the highest-impact worklist items.

## Tier rollups

| Tier | Clauses | Covered | Coverage % | Priority weight | Priority covered | Priority % |
|------|--------:|--------:|-----------:|----------------:|------------------:|-----------:|
| tier-1 | 199 | 199 | 100.00 | 186.1000 | 186.1000 | 100.00 |
| tier-2 | 99 | 66 | 66.67 | 97.2000 | 64.8000 | 66.67 |
| tier-3 | 0 | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |

## Tier 1 frameworks

### CMMC — `cmmc`

_Cybersecurity Maturity Model Certification_

#### CMMC@2.0

- Common clauses: **9**
- Covered: **9** (100.00%)
- Priority-weighted coverage: **100.00%** (9.0000 / 9.0000)
- Authoritative source: https://dodcio.defense.gov/CMMC/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `AC.L2-3.1.1` | Authorized access to systems | 1.00 | ✔ 1 | partial | 22.20.1 |
| `AC.L2-3.1.5` | Least privilege | 1.00 | ✔ 1 | partial | 22.20.2 |
| `AU.L2-3.3.1` | Create audit records | 1.00 | ✔ 1 | partial | 22.20.3 |
| `AU.L2-3.3.2` | Ensure unique user traceability | 1.00 | ✔ 1 | partial | 22.20.4 |
| `AU.L2-3.3.5` | Audit reporting and correlation | 1.00 | ✔ 1 | partial | 22.20.5 |
| `CM.L2-3.4.1` | Baseline configurations | 1.00 | ✔ 1 | partial | 22.20.6 |
| `IR.L2-3.6.1` | Incident handling capability | 1.00 | ✔ 1 | partial | 22.20.7 |
| `SC.L2-3.13.8` | Cryptographic mechanisms for CUI in transit | 1.00 | ✔ 1 | partial | 22.20.8 |
| `SI.L2-3.14.6` | Monitor for attacks | 1.00 | ✔ 1 | partial | 22.20.9 |

### DORA — `dora`

_EU Digital Operational Resilience Act_

#### DORA@Regulation (EU) 2022/2554

- Common clauses: **14**
- Covered: **14** (100.00%)
- Priority-weighted coverage: **100.00%** (13.4000 / 13.4000)
- Authoritative source: https://eur-lex.europa.eu/eli/reg/2022/2554/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.5` | ICT risk-management governance | 1.00 | ✔ 1 | contributing | 22.3.19 |
| `Art.6` | ICT risk-management framework | 1.00 | ✔ 3 | full | 22.11.106, 22.3.41, 22.6.46 |
| `Art.7` | ICT systems, protocols and tools | 1.00 | ✔ 2 | full | 22.3.42, 22.8.32 |
| `Art.8` | Identification | 1.00 | ✔ 2 | full | 22.11.103, 22.3.43 |
| `Art.9` | Protection and prevention | 1.00 | ✔ 2 | partial | 22.11.97, 22.41.3 |
| `Art.10` | Detection | 1.00 | ✔ 2 | partial | 22.3.7, 22.8.33 |
| `Art.11` | Response and recovery | 1.00 | ✔ 1 | contributing | 22.3.8 |
| `Art.12` | Backup policies and recovery methods | 1.00 | ✔ 4 | full | 22.3.9, 22.35.3, 22.45.1, 22.45.3 |
| `Art.17` | ICT-related incident management process | 1.00 | ✔ 5 | full | 22.3.44, 22.6.51, 22.6.52, 22.8.34, 22.8.35 |
| `Art.18` | Classification of ICT-related incidents | 1.00 | ✔ 1 | contributing | 22.3.11 |
| `Art.19` | Reporting of major ICT-related incidents | 1.00 | ✔ 2 | full | 22.3.12, 22.39.1 |
| `Art.24` | Digital operational-resilience testing | 0.70 | ✔ 2 | full | 22.11.105, 22.3.45 |
| `Art.26` | Threat-led penetration testing | 0.70 | ✔ 1 | contributing | 22.3.17 |
| `Art.28` | ICT third-party risk | 1.00 | ✔ 5 | full | 22.38.3, 22.44.1, 22.44.2, 22.44.3, 22.8.37 |

### GDPR — `gdpr`

_General Data Protection Regulation_

#### GDPR@2016/679

- Common clauses: **20**
- Covered: **20** (100.00%)
- Priority-weighted coverage: **100.00%** (17.3000 / 17.3000)
- Authoritative source: https://eur-lex.europa.eu/eli/reg/2016/679/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.5` | Principles of processing | 1.00 | ✔ 2 | full | 22.49.1, 22.49.2 |
| `Art.6` | Lawful basis | 1.00 | ✔ 1 | partial | 22.37.1 |
| `Art.7` | Conditions for consent | 0.70 | ✔ 5 | full | 22.1.46, 22.1.5, 22.37.1, 22.37.2, 22.8.39 |
| `Art.15` | Right of access | 1.00 | ✔ 1 | full | 22.36.1 |
| `Art.16` | Right to rectification | 0.70 | ✔ 1 | partial | 22.1.2 |
| `Art.17` | Right to erasure | 1.00 | ✔ 2 | full | 22.1.11, 22.36.2 |
| `Art.18` | Right to restrict processing | 0.70 | ✔ 1 | partial | 22.1.16 |
| `Art.20` | Right to data portability | 0.70 | ✔ 1 | full | 22.36.3 |
| `Art.21` | Right to object | 0.70 | ✔ 1 | partial | 22.1.46 |
| `Art.22` | Automated decision making | 0.70 | ✔ 1 | contributing | 22.1.18 |
| `Art.25` | Data protection by design and by default | 1.00 | ✔ 1 | contributing | 22.1.9 |
| `Art.28` | Processor obligations | 1.00 | ✔ 2 | full | 22.1.15, 22.44.2 |
| `Art.30` | Records of processing | 1.00 | ✔ 2 | contributing | 22.1.43, 22.1.8 |
| `Art.32` | Security of processing | 1.00 | ✔ 6 | partial | 22.1.10, 22.1.41, 22.1.7, 22.35.2, 22.35.3, 22.41.1 |
| `Art.33` | Breach notification to supervisory authority | 1.00 | ✔ 5 | full | 22.1.29, 22.1.3, 22.39.1, 22.39.2, 22.9.4 |
| `Art.34` | Breach communication to data subjects | 1.00 | ✔ 2 | full | 22.1.13, 22.39.3 |
| `Art.35` | DPIA | 0.70 | ✔ 1 | contributing | 22.1.14 |
| `Art.44` | International transfers — general principle | 1.00 | ✔ 2 | full | 22.38.1, 22.38.3 |
| `Art.45` | Transfers via adequacy decision | 0.70 | ✔ 2 | partial | 22.1.39, 22.38.2 |
| `Art.46` | Transfers subject to safeguards | 0.70 | ✔ 2 | full | 22.38.1, 22.38.2 |

### HIPAA Security — `hipaa-security`

_HIPAA Security Rule_

#### HIPAA Security@2013-final

- Common clauses: **15**
- Covered: **15** (100.00%)
- Priority-weighted coverage: **100.00%** (13.8000 / 13.8000)
- Authoritative source: https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§164.308(a)(1)` | Security management process | 1.00 | ✔ 4 | contributing | 22.10.1, 22.10.2, 22.10.22, 22.10.55 |
| `§164.308(a)(3)` | Workforce security | 1.00 | ✔ 1 | contributing | 22.10.4 |
| `§164.308(a)(4)` | Information access management | 1.00 | ✔ 1 | full | 22.10.21 |
| `§164.308(a)(5)` | Security awareness and training | 0.70 | ✔ 3 | full | 22.10.6, 22.46.1, 22.6.53 |
| `§164.308(a)(6)` | Security incident procedures | 1.00 | ✔ 2 | partial | 22.10.7, 22.39.1 |
| `§164.308(a)(7)` | Contingency plan | 1.00 | ✔ 2 | full | 22.10.8, 22.45.2 |
| `§164.308(a)(8)` | Evaluation | 0.70 | ✔ 1 | contributing | 22.10.9 |
| `§164.310(a)(1)` | Facility access controls | 1.00 | ✔ 1 | contributing | 22.10.31 |
| `§164.310(d)(1)` | Device and media controls | 0.70 | ✔ 3 | full | 22.10.29, 22.49.1, 22.49.2 |
| `§164.312(a)(1)` | Access control | 1.00 | ✔ 3 | contributing | 22.10.21, 22.10.24, 22.10.25 |
| `§164.312(a)(2)(iv)` | Encryption and decryption | 0.70 | ✔ 2 | full | 22.10.16, 22.41.1 |
| `§164.312(b)` | Audit controls | 1.00 | ✔ 2 | contributing | 22.10.17, 22.10.36 |
| `§164.312(c)(1)` | Integrity | 1.00 | ✔ 3 | full | 22.10.18, 22.10.27, 22.35.2 |
| `§164.312(d)` | Person or entity authentication | 1.00 | ✔ 3 | contributing | 22.10.19, 22.10.23, 22.10.42 |
| `§164.312(e)(1)` | Transmission security | 1.00 | ✔ 6 | full | 22.10.20, 22.10.22, 22.10.26, 22.41.2, 22.8.31, 22.8.38 |

### ISO 27001 — `iso-27001`

_ISO/IEC 27001 — ISMS_

#### ISO 27001@2013

- Common clauses: **5**
- Covered: **5** (100.00%)
- Priority-weighted coverage: **100.00%** (4.7000 / 4.7000)
- Authoritative source: https://www.iso.org/standard/54534.html

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `A.9.2.5` | Review of user access rights (2013) | 1.00 | ✔ 1 | full | 22.6.3 |
| `A.12.4.1` | Event logging (2013) | 1.00 | ✔ 1 | full | 22.6.2 |
| `A.12.4.2` | Protection of log information (2013) | 1.00 | ✔ 1 | partial | 22.6.38 |
| `A.12.4.3` | Administrator and operator logs (2013) | 0.70 | ✔ 1 | full | 22.6.26 |
| `A.16.1.2` | Reporting information security events (2013) | 1.00 | ✔ 1 | partial | 22.6.39 |

#### ISO 27001@2022

- Common clauses: **23**
- Covered: **23** (100.00%)
- Priority-weighted coverage: **100.00%** (20.9000 / 20.9000)
- Authoritative source: https://www.iso.org/standard/27001

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `6.1` | Risk assessment | 1.00 | ✔ 2 | full | 22.6.46, 22.6.48 |
| `6.2` | Information-security objectives | 1.00 | ✔ 1 | full | 22.6.47 |
| `7.2` | Competence | 0.70 | ✔ 1 | full | 22.6.53 |
| `7.5` | Documented information | 0.70 | ✔ 1 | full | 22.6.54 |
| `8.1` | Operational planning | 0.70 | ✔ 2 | full | 22.6.55, 22.8.33 |
| `8.2` | Information-security risk assessment | 1.00 | ✔ 2 | full | 22.11.106, 22.6.48 |
| `9.1` | Monitoring, measurement, analysis, evaluation | 1.00 | ✔ 2 | full | 22.6.47, 22.6.49 |
| `9.2` | Internal audit | 1.00 | ✔ 1 | full | 22.6.50 |
| `A.5.7` | Threat intelligence (2022 new) | 0.70 | ✔ 1 | contributing | 22.6.11 |
| `A.5.15` | Access control | 1.00 | ✔ 1 | full | 22.40.2 |
| `A.5.18` | Access rights review | 1.00 | ✔ 3 | full | 22.12.36, 22.12.37, 22.40.3 |
| `A.5.23` | Information security in cloud services (2022 new) | 1.00 | ✔ 1 | contributing | 22.6.13 |
| `A.5.24` | Incident management planning | 1.00 | ✔ 3 | full | 22.11.105, 22.3.44, 22.6.51 |
| `A.5.25` | Assessment and decision on events | 1.00 | ✔ 2 | full | 22.6.52, 22.8.34 |
| `A.8.2` | Privileged access rights | 1.00 | ✔ 1 | contributing | 22.6.26 |
| `A.8.9` | Configuration management (2022 new) | 1.00 | ✔ 2 | full | 22.11.92, 22.6.32 |
| `A.8.12` | Data leakage prevention | 1.00 | ✔ 3 | full | 22.11.93, 22.6.35, 22.8.38 |
| `A.8.15` | Logging | 1.00 | ✔ 2 | full | 22.11.99, 22.6.38 |
| `A.8.16` | Monitoring activities | 1.00 | ✔ 2 | full | 22.11.104, 22.6.39 |
| `A.8.17` | Clock synchronisation | 0.70 | ✔ 2 | full | 22.11.100, 22.6.40 |
| `A.8.23` | Web filtering (2022 new) | 0.70 | ✔ 2 | partial | 22.6.42, 22.8.32 |
| `A.8.25` | Secure development life cycle | 1.00 | ✔ 2 | full | 22.11.95, 22.6.45 |
| `A.8.28` | Secure coding (2022 new) | 0.70 | ✔ 1 | contributing | 22.6.45 |

### NIS2 — `nis2`

_EU NIS2 Directive_

#### NIS2@Directive (EU) 2022/2555

- Common clauses: **12**
- Covered: **12** (100.00%)
- Priority-weighted coverage: **100.00%** (11.4000 / 11.4000)
- Authoritative source: https://eur-lex.europa.eu/eli/dir/2022/2555/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.20` | Governance | 1.00 | ✔ 3 | contributing | 22.2.20, 22.2.41, 22.2.42 |
| `Art.21(2)(a)` | Risk analysis and information-system security policies | 1.00 | ✔ 5 | contributing | 22.2.18, 22.2.26, 22.2.36, 22.2.37, 22.2.6 |
| `Art.21(2)(b)` | Incident handling | 1.00 | ✔ 1 | contributing | 22.2.23 |
| `Art.21(2)(c)` | Business continuity and crisis management | 1.00 | ✔ 4 | contributing | 22.2.17, 22.2.24, 22.2.4, 22.2.40 |
| `Art.21(2)(d)` | Supply-chain security | 1.00 | ✔ 5 | full | 22.2.16, 22.2.2, 22.2.25, 22.3.42, 22.44.1 |
| `Art.21(2)(e)` | Security in acquisition, development and maintenance | 1.00 | ✔ 5 | partial | 22.2.15, 22.2.27, 22.2.3, 22.2.38, 22.43.1 |
| `Art.21(2)(f)` | Policies and procedures effectiveness | 0.70 | ✔ 3 | contributing | 22.2.39, 22.2.43, 22.2.9 |
| `Art.21(2)(g)` | Cyber-hygiene and training | 0.70 | ✔ 4 | full | 22.2.10, 22.2.28, 22.46.1, 22.46.2 |
| `Art.21(2)(h)` | Cryptography and encryption | 1.00 | ✔ 3 | full | 22.2.11, 22.2.29, 22.41.2 |
| `Art.21(2)(i)` | Human resources and access control | 1.00 | ✔ 4 | contributing | 22.2.13, 22.2.14, 22.2.30, 22.2.5 |
| `Art.21(2)(j)` | MFA and secure communications | 1.00 | ✔ 1 | contributing | 22.2.12 |
| `Art.23` | Reporting obligations | 1.00 | ✔ 7 | full | 22.2.1, 22.2.33, 22.2.45, 22.3.44, 22.39.1, 22.39.2, 22.9.4 |

### NIST 800-53 — `nist-800-53`

_NIST SP 800-53 Rev. 5_

#### NIST 800-53@Rev. 5

- Common clauses: **24**
- Covered: **24** (100.00%)
- Priority-weighted coverage: **100.00%** (23.1000 / 23.1000)
- Authoritative source: https://csrc.nist.gov/pubs/sp/800/53/r5/final

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `AC-2` | Account management | 1.00 | ✔ 2 | full | 22.14.16, 22.40.3 |
| `AC-3` | Access enforcement | 1.00 | ✔ 1 | contributing | 22.14.17 |
| `AC-6` | Least privilege | 1.00 | ✔ 3 | full | 22.14.19, 22.40.1, 22.40.2 |
| `AU-2` | Event logging | 1.00 | ✔ 1 | contributing | 22.14.1 |
| `AU-3` | Content of audit records | 1.00 | ✔ 1 | contributing | 22.14.2 |
| `AU-6` | Audit review, analysis, and reporting | 1.00 | ✔ 1 | contributing | 22.14.5 |
| `AU-8` | Time stamps | 1.00 | ✔ 2 | full | 22.11.100, 22.14.7 |
| `AU-9` | Protection of audit information | 1.00 | ✔ 2 | full | 22.14.8, 22.35.3 |
| `AU-12` | Audit record generation | 1.00 | ✔ 1 | contributing | 22.14.11 |
| `CM-2` | Baseline configuration | 1.00 | ✔ 2 | full | 22.14.52, 22.42.2 |
| `CM-6` | Configuration settings | 1.00 | ✔ 3 | full | 22.11.92, 22.14.56, 22.42.2 |
| `CP-9` | System backup | 1.00 | ✔ 4 | full | 22.14.79, 22.45.1, 22.45.2, 22.45.3 |
| `IA-2` | Identification and authentication (users) | 1.00 | ✔ 3 | full | 22.11.96, 22.11.98, 22.14.26 |
| `IA-5` | Authenticator management | 1.00 | ✔ 1 | contributing | 22.14.29 |
| `IR-4` | Incident handling | 1.00 | ✔ 3 | contributing | 22.14.45, 22.6.51, 22.6.52 |
| `PM-1` | Information security program plan | 0.70 | ✔ 1 | partial | 22.47.1 |
| `PS-4` | Personnel termination | 1.00 | ✔ 1 | full | 22.10.5 |
| `RA-5` | Vulnerability scanning | 1.00 | ✔ 5 | full | 22.11.103, 22.14.75, 22.3.43, 22.43.1, 22.43.2 |
| `SC-7` | Boundary protection | 1.00 | ✔ 1 | contributing | 22.14.67 |
| `SC-8` | Transmission confidentiality and integrity | 1.00 | ✔ 2 | full | 22.14.68, 22.41.2 |
| `SC-13` | Cryptographic protection | 1.00 | ✔ 3 | full | 22.14.71, 22.41.1, 22.41.3 |
| `SI-4` | System monitoring | 1.00 | ✔ 2 | partial | 22.14.36, 22.8.33 |
| `SR-3` | Supply chain controls and processes | 0.70 | ✔ 1 | partial | 22.44.1 |
| `PT-3` | Personally identifiable information processing purposes | 0.70 | ✔ 1 | partial | 22.1.48 |

### NIST CSF — `nist-csf`

_NIST Cybersecurity Framework_

#### NIST CSF@1.1

- Common clauses: **3**
- Covered: **3** (100.00%)
- Priority-weighted coverage: **100.00%** (3.0000 / 3.0000)
- Authoritative source: https://www.nist.gov/cyberframework/framework

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `ID.AM-1` | Physical devices inventory | 1.00 | ✔ 1 | full | 22.7.3 |
| `PR.AC-1` | Identities and credentials managed | 1.00 | ✔ 1 | full | 22.7.4 |
| `DE.AE-3` | Event data collection and correlation | 1.00 | ✔ 1 | full | 22.7.2 |

#### NIST CSF@2.0

- Common clauses: **17**
- Covered: **17** (100.00%)
- Priority-weighted coverage: **100.00%** (16.1000 / 16.1000)
- Authoritative source: https://www.nist.gov/cyberframework

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `GV.OC-01` | Organisational context | 0.70 | ✔ 1 | contributing | 22.7.8 |
| `GV.RM-01` | Risk management strategy | 1.00 | ✔ 1 | contributing | 22.7.10 |
| `GV.RR-01` | Organisational leadership | 0.70 | ✔ 1 | contributing | 22.7.11 |
| `ID.AM-01` | Asset inventory | 1.00 | ✔ 1 | contributing | 22.7.16 |
| `ID.RA-01` | Risk assessment | 1.00 | ✔ 1 | contributing | 22.7.19 |
| `PR.AA-01` | Authentication | 1.00 | ✔ 1 | contributing | 22.7.23 |
| `PR.AA-05` | Access permissions | 1.00 | ✔ 1 | full | 22.7.4 |
| `PR.DS-01` | Data-at-rest protection | 1.00 | ✔ 1 | contributing | 22.7.26 |
| `PR.DS-02` | Data-in-transit protection | 1.00 | ✔ 1 | contributing | 22.7.27 |
| `PR.PS-04` | Log generation | 1.00 | ✔ 1 | partial | 22.7.32 |
| `DE.AE-02` | Anomalies and events analysis | 1.00 | ✔ 1 | contributing | 22.7.37 |
| `DE.CM-01` | Network monitoring | 1.00 | ✔ 1 | contributing | 22.7.31 |
| `DE.CM-03` | Personnel activity monitoring | 1.00 | ✔ 1 | contributing | 22.7.33 |
| `DE.CM-09` | Environment monitoring | 0.70 | ✔ 1 | partial | 22.7.5 |
| `RS.MA-01` | Incident management | 1.00 | ✔ 1 | contributing | 22.7.39 |
| `RS.AN-03` | Incident analysis | 1.00 | ✔ 1 | full | 22.7.6 |
| `RC.RP-01` | Recovery plan execution | 1.00 | ✔ 1 | contributing | 22.7.46 |

### PCI DSS — `pci-dss`

_Payment Card Industry Data Security Standard_

#### PCI DSS@v3.2.1

- Common clauses: **7**
- Covered: **7** (100.00%)
- Priority-weighted coverage: **100.00%** (6.7000 / 6.7000)
- Authoritative source: https://www.pcisecuritystandards.org/document_library/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `3.4` | PAN rendering unreadable | 1.00 | ✔ 1 | full | 22.11.18 |
| `8.2.3` | Strong password parameters | 1.00 | ✔ 1 | full | 22.11.48 |
| `10.1` | Audit trail linking access to user | 1.00 | ✔ 1 | full | 22.11.67 |
| `10.2` | Audit events required to be logged | 1.00 | ✔ 1 | full | 22.11.61 |
| `10.5` | Log integrity | 1.00 | ✔ 1 | full | 22.11.65 |
| `10.6` | Log review | 1.00 | ✔ 1 | full | 22.11.63 |
| `11.4` | Intrusion detection | 0.70 | ✔ 1 | full | 22.11.77 |

#### PCI DSS@v4.0

- Common clauses: **22**
- Covered: **22** (100.00%)
- Priority-weighted coverage: **100.00%** (21.7000 / 21.7000)
- Authoritative source: https://www.pcisecuritystandards.org/document_library/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `1.2` | Network security controls configuration | 1.00 | ✔ 1 | partial | 22.42.2 |
| `1.3` | CDE network boundary | 1.00 | ✔ 1 | full | 22.11.91 |
| `2.2` | Secure system component configuration | 1.00 | ✔ 1 | full | 22.11.92 |
| `3.3` | Sensitive authentication data not stored | 1.00 | ✔ 1 | full | 22.11.93 |
| `3.5` | PAN protection | 1.00 | ✔ 1 | full | 22.41.1 |
| `4.2` | Strong cryptography for CHD in transit | 1.00 | ✔ 1 | full | 22.41.2 |
| `5.2` | Anti-malware mechanisms | 1.00 | ✔ 1 | full | 22.11.94 |
| `6.2` | Bespoke software developed securely | 1.00 | ✔ 1 | full | 22.11.95 |
| `6.3` | Vulnerabilities identified and addressed | 1.00 | ✔ 2 | full | 22.43.1, 22.43.2 |
| `7.2` | Access granted on least privilege | 1.00 | ✔ 1 | partial | 22.48.1 |
| `8.3` | Strong authentication | 1.00 | ✔ 1 | full | 22.11.96 |
| `8.4` | MFA | 1.00 | ✔ 1 | full | 22.11.97 |
| `8.6` | Application and system accounts | 1.00 | ✔ 1 | full | 22.11.98 |
| `10.2` | Audit logs captured for all system components | 1.00 | ✔ 1 | partial | 22.40.1 |
| `10.3` | Audit logs protected from modification | 1.00 | ✔ 1 | full | 22.11.99 |
| `10.4` | Time synchronised | 1.00 | ✔ 1 | full | 22.11.100 |
| `10.6` | Logs reviewed | 1.00 | ✔ 1 | full | 22.11.101 |
| `10.7` | Log retention | 1.00 | ✔ 1 | full | 22.11.102 |
| `11.3` | External and internal vulnerabilities identified | 1.00 | ✔ 1 | full | 22.11.103 |
| `11.4` | Intrusion detection / prevention | 1.00 | ✔ 1 | full | 22.11.104 |
| `12.3` | Targeted risk analysis | 0.70 | ✔ 1 | full | 22.11.106 |
| `12.10` | Security incident response | 1.00 | ✔ 1 | full | 22.11.105 |

### SOC 2 — `soc-2`

_SOC 2 Trust Services Criteria_

#### SOC 2@2017 TSC

- Common clauses: **16**
- Covered: **16** (100.00%)
- Priority-weighted coverage: **100.00%** (13.9000 / 13.9000)
- Authoritative source: https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `CC1.1` | Integrity and ethical values | 0.70 | ✔ 1 | full | 22.8.36 |
| `CC2.1` | Internal communication | 0.70 | ✔ 1 | contributing | 22.8.4 |
| `CC3.1` | Risk assessment | 1.00 | ✔ 1 | partial | 22.47.2 |
| `CC5.1` | Control activities | 1.00 | ✔ 1 | full | 22.47.1 |
| `CC6.1` | Logical access controls | 1.00 | ✔ 2 | full | 22.11.96, 22.40.1 |
| `CC6.6` | Encryption in transit | 1.00 | ✔ 2 | full | 22.11.91, 22.8.31 |
| `CC6.7` | System boundaries and data transmission | 1.00 | ✔ 1 | full | 22.8.32 |
| `CC7.1` | System operations monitoring | 1.00 | ✔ 5 | full | 22.11.101, 22.11.104, 22.12.40, 22.6.49, 22.8.33 |
| `CC7.2` | System monitoring for anomalies | 1.00 | ✔ 2 | partial | 22.11.99, 22.35.2 |
| `CC7.3` | Evaluated events and incidents | 1.00 | ✔ 2 | full | 22.6.52, 22.8.34 |
| `CC7.4` | Incident response | 1.00 | ✔ 2 | full | 22.11.105, 22.8.35 |
| `CC8.1` | Change management | 1.00 | ✔ 6 | full | 22.11.92, 22.11.95, 22.12.38, 22.12.39, 22.42.1, 22.6.55 |
| `CC9.1` | Risk mitigation activities | 0.70 | ✔ 1 | full | 22.8.37 |
| `A1.2` | Availability commitments | 0.70 | ✔ 2 | full | 22.35.3, 22.45.1 |
| `C1.1` | Confidentiality | 0.70 | ✔ 2 | full | 22.11.93, 22.8.38 |
| `P1.1` | Privacy notice | 0.40 | ✔ 1 | full | 22.8.39 |

### SOX ITGC — `sox-itgc`

_SOX — PCAOB AS 2201 ITGCs_

#### SOX ITGC@PCAOB AS 2201

- Common clauses: **12**
- Covered: **12** (100.00%)
- Priority-weighted coverage: **100.00%** (11.1000 / 11.1000)
- Authoritative source: https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `ITGC.AccessMgmt.Provisioning` | User provisioning | 1.00 | ✔ 2 | full | 22.12.36, 9.5.15 |
| `ITGC.AccessMgmt.Termination` | Timely deprovisioning | 1.00 | ✔ 1 | full | 22.12.37 |
| `ITGC.AccessMgmt.Privileged` | Privileged access | 1.00 | ✔ 3 | full | 22.40.1, 22.40.2, 7.1.21 |
| `ITGC.AccessMgmt.SOD` | Segregation of duties | 1.00 | ✔ 2 | full | 22.48.1, 22.48.2 |
| `ITGC.AccessMgmt.Review` | Periodic access review | 0.70 | ✔ 1 | full | 22.40.3 |
| `ITGC.ChangeMgmt.Authorization` | Change authorised | 1.00 | ✔ 3 | full | 16.4.1, 22.42.1, 7.1.13 |
| `ITGC.ChangeMgmt.Testing` | Change tested | 1.00 | ✔ 2 | full | 22.11.95, 22.12.38 |
| `ITGC.ChangeMgmt.Approval` | Change approved | 1.00 | ✔ 3 | full | 12.2.17, 22.12.39, 22.6.55 |
| `ITGC.Operations.JobSchedule` | Batch scheduling and monitoring | 0.70 | ✔ 1 | full | 22.12.40 |
| `ITGC.Operations.Backup` | Backup and restore | 1.00 | ✔ 1 | full | 22.45.3 |
| `ITGC.Logging.Continuity` | Audit trail completeness | 1.00 | ✔ 2 | partial | 22.35.2, 7.1.40 |
| `ITGC.Logging.Review` | Log review | 0.70 | ✔ 2 | partial | 22.47.2, 22.49.3 |

## Tier 2 frameworks

### API RP 1164 — `api-rp-1164`

_API Recommended Practice 1164 — Pipeline Control Systems Cybersecurity_

#### API RP 1164@3rd edition

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://www.api.org/products-and-services/standards/important-standards-announcements/standard-1164

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `5.3` | Access control | 1.00 | ✔ 5 | partial | 14.2.14, 14.9.14, 15.3.1, 15.3.37, 5.1.14 |
| `6.2.1` | Logging and monitoring | 1.00 | ✔ 3 | partial | 14.2.4, 14.2.9, 14.6.6 |

### APPI — `appi`

_Japan Act on the Protection of Personal Information_

#### APPI@2022 amendments

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://www.ppc.go.jp/en/legal/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.23` | Security control action | 1.00 | ✔ 3 | contributing | 22.35.2, 22.35.3, 22.41.1 |
| `Art.26` | Leakage reporting | 1.00 | ✔ 3 | partial | 22.39.1, 22.39.2, 22.39.3 |

### APRA CPS 234 — `apra-cps-234`

_APRA CPS 234 Information Security_

#### APRA CPS 234@current

- Common clauses: **3**
- Covered: **3** (100.00%)
- Priority-weighted coverage: **100.00%** (2.7000 / 2.7000)
- Authoritative source: https://www.apra.gov.au/information-security

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `15` | Policy framework | 0.70 | ✔ 2 | contributing | 1.2.9, 1.3.4 |
| `23` | Incident management | 1.00 | ✔ 4 | partial | 16.1.20, 16.3.6, 6.3.1, 6.3.23 |
| `36` | Notification of incidents | 1.00 | ✔ 2 | partial | 16.1.20, 16.3.6 |

### ASD E8 — `asd-e8`

_ASD Essential Eight Maturity Model_

#### ASD E8@Nov 2023

- Common clauses: **5**
- Covered: **4** (80.00%)
- Priority-weighted coverage: **80.00%** (4.0000 / 5.0000)
- Authoritative source: https://www.cyber.gov.au/resources-business-and-government/essential-cyber-security/essential-eight/essential-eight-maturity-model

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `E8.01` | Application control | 1.00 | ✔ 2 | partial | 1.2.91, 12.3.10 |
| `E8.03` | Configure MS Office macro settings | 1.00 | ✖ 0 | — | — |
| `E8.05` | Restrict administrative privileges | 1.00 | ✔ 3 | partial | 1.1.76, 9.1.3, 9.4.1 |
| `E8.06` | Patch operating systems | 1.00 | ✔ 4 | partial | 1.2.9, 1.3.4, 12.3.2, 3.1.5 |
| `E8.08` | Regular backups | 1.00 | ✔ 4 | full | 5.1.24, 6.3.1, 6.3.13, 6.3.23 |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `E8.03` | Configure MS Office macro settings |

</details>

### AU Privacy Act — `au-privacy-act`

_Australian Privacy Act 1988 and Notifiable Data Breaches scheme_

#### AU Privacy Act@current

- Common clauses: **3**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 3.0000)
- Authoritative source: https://www.legislation.gov.au/C2004A03712/latest/text

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `APP 1` | Open and transparent management of personal info | 1.00 | ✖ 0 | — | — |
| `APP 11` | Security of personal information | 1.00 | ✖ 0 | — | — |
| `§26WK` | NDB — notifiable data breach | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `APP 1` | Open and transparent management of personal info |
| 1.00 | `APP 11` | Security of personal information |
| 1.00 | `§26WK` | NDB — notifiable data breach |

</details>

### BAIT/KAIT — `bait-kait`

_BaFin Banking/Insurance Supervisory Requirements for IT (BAIT/KAIT)_

#### BAIT/KAIT@Aug 2021

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://www.bafin.de/SharedDocs/Veroeffentlichungen/EN/Rundschreiben/2021/rs_1021_BAIT_en.html

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§5` | Identity & access management | 1.00 | ✔ 5 | partial | 13.1.39, 4.1.4, 9.1.3, 9.4.1, 9.5.15 |
| `§9` | ICT operations management | 1.00 | ✔ 3 | partial | 12.2.17, 16.4.1, 5.1.24 |

### BSI-KritisV — `bsi-kritisv`

_BSI KRITIS-Verordnung_

#### BSI-KritisV@2021 (as amended)

- Common clauses: **1**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 1.0000)
- Authoritative source: https://www.gesetze-im-internet.de/bsi-kritisv/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§8a` | Security in IT systems | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§8a` | Security in IT systems |

</details>

### CCPA/CPRA — `ccpa`

_California Consumer Privacy Act / CPRA_

#### CCPA/CPRA@CPRA (as amended)

- Common clauses: **3**
- Covered: **3** (100.00%)
- Priority-weighted coverage: **100.00%** (2.7000 / 2.7000)
- Authoritative source: https://cppa.ca.gov/regulations/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§1798.100` | Consumer right to know | 1.00 | ✔ 3 | full | 22.36.1, 22.37.2, 22.49.1 |
| `§1798.105` | Consumer right to delete | 1.00 | ✔ 1 | full | 22.36.2 |
| `§1798.150` | Private right of action for data breaches | 0.70 | ✔ 1 | partial | 22.39.3 |

### CJIS — `cjis`

_FBI CJIS Security Policy_

#### CJIS@v5.9.4

- Common clauses: **2**
- Covered: **1** (50.00%)
- Priority-weighted coverage: **50.00%** (1.0000 / 2.0000)
- Authoritative source: https://le.fbi.gov/cjis-division/cjis-security-policy-resource-center

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `5.5.1` | Access control - identification | 1.00 | ✔ 5 | partial | 1.1.108, 4.1.4, 5.1.14, 7.1.21, 9.1.1 |
| `5.13.3` | Incident response | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `5.13.3` | Incident response |

</details>

### eIDAS — `eidas`

_EU eIDAS Regulation_

#### eIDAS@Regulation (EU) 2024/1183

- Common clauses: **1**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 1.0000)
- Authoritative source: https://eur-lex.europa.eu/eli/reg/2024/1183/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.24` | Requirements for qualified trust service providers | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `Art.24` | Requirements for qualified trust service providers |

</details>

### EU AI Act — `eu-ai-act`

_EU AI Act_

#### EU AI Act@Regulation (EU) 2024/1689

- Common clauses: **6**
- Covered: **2** (33.33%)
- Priority-weighted coverage: **35.09%** (2.0000 / 5.7000)
- Authoritative source: https://eur-lex.europa.eu/eli/reg/2024/1689/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.12` | Record-keeping (logging) | 1.00 | ✔ 1 | partial | 1.1.65 |
| `Art.13` | Transparency and information | 0.70 | ✖ 0 | — | — |
| `Art.14` | Human oversight | 1.00 | ✖ 0 | — | — |
| `Art.15` | Accuracy, robustness, cybersecurity | 1.00 | ✖ 0 | — | — |
| `Art.19` | Automatically generated logs | 1.00 | ✔ 1 | contributing | 1.2.51 |
| `Art.26` | High-risk AI obligations for deployers | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `Art.14` | Human oversight |
| 1.00 | `Art.15` | Accuracy, robustness, cybersecurity |
| 1.00 | `Art.26` | High-risk AI obligations for deployers |
| 0.70 | `Art.13` | Transparency and information |

</details>

### EU AML — `eu-aml`

_EU Anti-Money-Laundering Framework_

#### EU AML@6AMLD / AMLR 2024

- Common clauses: **2**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 2.0000)
- Authoritative source: https://eur-lex.europa.eu/eli/reg/2024/1624/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.9` | Internal policies and controls | 1.00 | ✖ 0 | — | — |
| `Art.18` | Customer due diligence | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `Art.18` | Customer due diligence |
| 1.00 | `Art.9` | Internal policies and controls |

</details>

### EU CRA — `eu-cra`

_EU Cyber Resilience Act_

#### EU CRA@Regulation (EU) 2024/2847

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://eur-lex.europa.eu/eli/reg/2024/2847/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.13` | Obligations of manufacturers | 1.00 | ✔ 4 | partial | 12.1.4, 12.3.10, 12.3.2, 3.1.5 |
| `Art.14` | Reporting of actively exploited vulnerabilities | 1.00 | ✔ 2 | full | 12.3.2, 3.1.5 |

### FCA SM&CR — `fca-smcr`

_FCA Senior Managers and Certification Regime_

#### FCA SM&CR@current

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)
- Authoritative source: https://www.fca.org.uk/firms/senior-managers-certification-regime

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

### FCA SS1/21 — `fca-ss1-21`

_FCA SS1/21 Operational Resilience_

#### FCA SS1/21@2021

- Common clauses: **3**
- Covered: **2** (66.67%)
- Priority-weighted coverage: **66.67%** (2.0000 / 3.0000)
- Authoritative source: https://www.fca.org.uk/publication/policy/ps21-3.pdf

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§1.1` | Identify important business services | 1.00 | ✖ 0 | — | — |
| `§2.1` | Set impact tolerances | 1.00 | ✔ 1 | partial | 6.3.13 |
| `§3.1` | Scenario testing | 1.00 | ✔ 1 | partial | 6.3.13 |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§1.1` | Identify important business services |

</details>

### FDA Part 11 — `fda-part-11`

_FDA 21 CFR Part 11_

#### FDA Part 11@current

- Common clauses: **3**
- Covered: **2** (66.67%)
- Priority-weighted coverage: **66.67%** (2.0000 / 3.0000)
- Authoritative source: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§11.10(e)` | Audit trails | 1.00 | ✔ 5 | full | 1.1.65, 1.2.33, 1.2.51, 7.1.13, 7.1.40 |
| `§11.10(d)` | System access limited to authorized individuals | 1.00 | ✔ 1 | partial | 7.1.21 |
| `§11.200` | Electronic signatures | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§11.200` | Electronic signatures |

</details>

### FedRAMP — `fedramp`

_Federal Risk and Authorization Management Program_

#### FedRAMP@Rev.5 Baselines

- Common clauses: **3**
- Covered: **3** (100.00%)
- Priority-weighted coverage: **100.00%** (3.0000 / 3.0000)
- Authoritative source: https://www.fedramp.gov/baselines/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `AC-2` | Account management | 1.00 | ✔ 8 | full | 13.1.39, 17.1.8, 4.1.4, 5.2.2, 7.1.21, 9.1.3, 9.4.1, 9.5.15 |
| `AU-6` | Audit review, analysis, reporting | 1.00 | ✔ 3 | partial | 13.1.35, 13.1.37, 4.1.1 |
| `SI-4` | System monitoring | 1.00 | ✔ 4 | partial | 1.1.65, 1.1.76, 1.2.51, 4.1.1 |

### FISMA — `fisma`

_Federal Information Security Modernization Act_

#### FISMA@2014

- Common clauses: **2**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 2.0000)
- Authoritative source: https://www.congress.gov/bill/113th-congress/senate-bill/2521

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§3554(b)(1)` | Information security program | 1.00 | ✖ 0 | — | — |
| `§3554(b)(5)` | Security controls and monitoring | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§3554(b)(1)` | Information security program |
| 1.00 | `§3554(b)(5)` | Security controls and monitoring |

</details>

### HIPAA Privacy — `hipaa-privacy`

_HIPAA Privacy Rule_

#### HIPAA Privacy@current

- Common clauses: **4**
- Covered: **2** (50.00%)
- Priority-weighted coverage: **50.00%** (1.7000 / 3.4000)
- Authoritative source: https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§164.502(a)` | Uses and disclosures of PHI — general rules | 1.00 | ✔ 4 | partial | 11.1.5, 11.1.6, 15.3.37, 7.1.21 |
| `§164.504(e)` | Business Associate contracts | 1.00 | ✖ 0 | — | — |
| `§164.514(a)` | De-identification of PHI | 0.70 | ✔ 1 | contributing | 11.1.5 |
| `§164.528` | Accounting of disclosures | 0.70 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§164.504(e)` | Business Associate contracts |
| 0.70 | `§164.528` | Accounting of disclosures |

</details>

### HITRUST — `hitrust`

_HITRUST CSF_

#### HITRUST@v11

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://hitrustalliance.net/csf-overview/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `09.aa` | Audit logging | 1.00 | ✔ 8 | partial | 1.1.65, 1.2.33, 1.2.51, 12.1.4, 13.1.35, 13.1.36, 13.1.37, 7.1.40 |
| `01.b` | User access management | 1.00 | ✔ 9 | full | 1.1.108, 13.1.39, 4.1.4, 7.1.21, 9.1.1, 9.1.3, 9.3.1, 9.4.1 |

### HKMA TM-G-2 — `hkma-tm-g-2`

_HKMA TM-G-2 General Principles for Technology Risk Management_

#### HKMA TM-G-2@current

- Common clauses: **1**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 1.0000)
- Authoritative source: https://www.hkma.gov.hk/eng/regulatory-resources/regulatory-guides/supervisory-policy-manual/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§3` | Governance of technology risk | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§3` | Governance of technology risk |

</details>

### IEC 62443 — `iec-62443`

_IEC 62443 Industrial Automation and Control Systems Security_

#### IEC 62443@2013-ongoing

- Common clauses: **4**
- Covered: **4** (100.00%)
- Priority-weighted coverage: **100.00%** (3.7000 / 3.7000)
- Authoritative source: https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `SR 1.1` | Human user identification and authentication | 1.00 | ✔ 1 | contributing | 22.15.11 |
| `SR 2.8` | Auditable events | 1.00 | ✔ 1 | contributing | 22.15.22 |
| `SR 2.9` | Audit storage capacity | 0.70 | ✔ 1 | contributing | 22.15.23 |
| `FR 6.2` | Continuous monitoring | 1.00 | ✔ 7 | full | 14.2.4, 14.2.9, 14.6.6, 14.9.14, 14.9.22, 17.1.8, 17.3.3 |

### IT-Grundschutz — `it-grundschutz`

_BSI IT-Grundschutz Compendium_

#### IT-Grundschutz@2023 Edition

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://www.bsi.bund.de/EN/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/it-grundschutz_node.html

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `OPS.1.1.2` | Ordered ICT operation | 1.00 | ✔ 6 | partial | 1.2.91, 12.2.17, 13.1.36, 16.4.1, 5.1.7, 6.3.1 |
| `ORP.4` | Identity & access | 1.00 | ✔ 2 | full | 9.1.3, 9.5.15 |

### IT-SiG 2.0 — `it-sig-2`

_German IT-Sicherheitsgesetz 2.0_

#### IT-SiG 2.0@2021

- Common clauses: **2**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 2.0000)
- Authoritative source: https://www.bgbl.de/xaver/bgbl/start.xav?startbk=Bundesanzeiger_BGBl&start=//*[@attr_id=%27bgbl121s1122.pdf%27]

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§8a` | Security measures for KRITIS operators | 1.00 | ✖ 0 | — | — |
| `§8b` | National IT situation centre notification | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§8a` | Security measures for KRITIS operators |
| 1.00 | `§8b` | National IT situation centre notification |

</details>

### LGPD — `lgpd`

_Lei Geral de Proteção de Dados Pessoais_

#### LGPD@Lei nº 13.709/2018

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.46` | Security measures | 1.00 | ✔ 3 | contributing | 22.35.2, 22.35.3, 22.41.1 |
| `Art.48` | Breach notification | 1.00 | ✔ 3 | partial | 22.39.1, 22.39.2, 22.39.3 |

### MAS TRM — `mas-trm`

_MAS Technology Risk Management Guidelines_

#### MAS TRM@2021

- Common clauses: **3**
- Covered: **2** (66.67%)
- Priority-weighted coverage: **66.67%** (2.0000 / 3.0000)
- Authoritative source: https://www.mas.gov.sg/-/media/mas/regulations-and-financial-stability/regulatory-and-supervisory-framework/risk-management/trm-guidelines-18-january-2021.pdf

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§4.1.1` | Technology risk governance | 1.00 | ✔ 3 | contributing | 12.2.17, 16.4.1, 5.1.7 |
| `§8.1.1` | IT operations — incident mgmt | 1.00 | ✔ 1 | partial | 16.1.20 |
| `§11.1.1` | System resilience | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§11.1.1` | System resilience |

</details>

### MiFID II — `mifid-ii`

_Markets in Financial Instruments Directive II_

#### MiFID II@Directive 2014/65/EU

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://eur-lex.europa.eu/eli/dir/2014/65/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.16(7)` | Record keeping of communications | 1.00 | ✔ 1 | contributing | 22.5.2 |
| `Art.17` | Algorithmic trading controls | 1.00 | ✔ 1 | contributing | 22.5.8 |

### NERC CIP — `nerc-cip`

_NERC Critical Infrastructure Protection_

#### NERC CIP@current

- Common clauses: **5**
- Covered: **4** (80.00%)
- Priority-weighted coverage: **80.00%** (4.0000 / 5.0000)
- Authoritative source: https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `CIP-002-5.1a R1` | BES cyber system identification | 1.00 | ✔ 1 | partial | 14.2.11 |
| `CIP-005-7 R1` | Electronic security perimeter | 1.00 | ✔ 5 | full | 14.2.14, 14.2.4, 14.9.22, 15.3.1, 17.3.3 |
| `CIP-007-6 R4` | Security event monitoring | 1.00 | ✔ 3 | partial | 14.2.11, 14.2.14, 14.9.14 |
| `CIP-008-6 R1` | Incident response | 1.00 | ✖ 0 | — | — |
| `CIP-010-4 R1` | Configuration change management | 1.00 | ✔ 8 | full | 1.2.9, 13.1.36, 14.2.9, 14.6.6, 16.4.1, 5.1.24, 5.1.7, 7.1.13 |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `CIP-008-6 R1` | Incident response |

</details>

### NESA IAS — `nesa-uae-ias`

_UAE NESA Information Assurance Standards_

#### NESA IAS@v2 (2020)

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)
- Authoritative source: https://www.nesa.gov.ae/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

### NO KBF — `no-kbf-nve`

_Norwegian Kraftberedskapsforskriften (NVE Power-sector emergency preparedness regulation)_

#### NO KBF@2012 as amended

- Common clauses: **1**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 1.0000)
- Authoritative source: https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§6-1` | Informasjonssikkerhet | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§6-1` | Informasjonssikkerhet |

</details>

### NO Personopplysningsloven — `no-personopplysningsloven`

_Norwegian Personopplysningsloven (Personal Data Act)_

#### NO Personopplysningsloven@2018

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)
- Authoritative source: https://lovdata.no/dokument/NL/lov/2018-06-15-38

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

### NO Petroleumsforskriften — `no-petroleumsforskriften`

_Norwegian Petroleumsforskriften (Petroleum Safety regulation)_

#### NO Petroleumsforskriften@1997 as amended

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)
- Authoritative source: https://lovdata.no/dokument/SF/forskrift/1997-06-27-653

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

### NO Sikkerhetsloven — `no-sikkerhetsloven`

_Norwegian Sikkerhetsloven (National Security Act)_

#### NO Sikkerhetsloven@2018

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)
- Authoritative source: https://lovdata.no/dokument/NL/lov/2018-06-01-24

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

### NZISM — `nzism`

_New Zealand Information Security Manual_

#### NZISM@3.7

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)
- Authoritative source: https://www.nzism.gcsb.govt.nz/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

### PIPL — `pipl`

_China Personal Information Protection Law_

#### PIPL@2021

- Common clauses: **2**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 2.0000)
- Authoritative source: http://www.npc.gov.cn/npc/c2/c30834/202108/t20210820_313088.html

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.38` | Cross-border transfer conditions | 1.00 | ✖ 0 | — | — |
| `Art.51` | Information security measures | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `Art.38` | Cross-border transfer conditions |
| 1.00 | `Art.51` | Information security measures |

</details>

### PRA SS2/21 — `pra-ss2-21`

_PRA SS2/21 Outsourcing and third-party risk management_

#### PRA SS2/21@2021

- Common clauses: **2**
- Covered: **1** (50.00%)
- Priority-weighted coverage: **50.00%** (1.0000 / 2.0000)
- Authoritative source: https://www.bankofengland.co.uk/prudential-regulation/publication/2021/march/outsourcing-and-third-party-risk-management-ss

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§3.2` | Proportionality | 1.00 | ✖ 0 | — | — |
| `§9` | Business continuity & exit plans | 1.00 | ✔ 2 | partial | 6.3.13, 6.3.23 |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `§3.2` | Proportionality |

</details>

### PSD2 — `psd2`

_Revised Payment Services Directive_

#### PSD2@Directive (EU) 2015/2366

- Common clauses: **3**
- Covered: **3** (100.00%)
- Priority-weighted coverage: **100.00%** (3.0000 / 3.0000)
- Authoritative source: https://eur-lex.europa.eu/eli/dir/2015/2366/oj

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.95` | Management of operational and security risks | 1.00 | ✔ 1 | contributing | 12.3.2 |
| `Art.96` | Incident reporting | 1.00 | ✔ 1 | partial | 16.3.6 |
| `Art.97` | Strong customer authentication | 1.00 | ✔ 4 | partial | 17.2.2, 4.1.5, 9.1.1, 9.3.1 |

### QCB Cyber — `qcb-cyber`

_Qatar Central Bank Cybersecurity Framework_

#### QCB Cyber@2018

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)
- Authoritative source: https://www.qcb.gov.qa/

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

### RBI Cyber — `rbi-cyber`

_RBI Cyber Security Framework for Banks_

#### RBI Cyber@2016 (as amended)

- Common clauses: **2**
- Covered: **1** (50.00%)
- Priority-weighted coverage: **50.00%** (1.0000 / 2.0000)
- Authoritative source: https://rbi.org.in/Scripts/NotificationUser.aspx?Id=10435

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Annex-A` | Baseline cyber-security controls | 1.00 | ✔ 1 | partial | 1.1.76 |
| `Annex-B` | Cyber-crisis management plan | 1.00 | ✖ 0 | — | — |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `Annex-B` | Cyber-crisis management plan |

</details>

### SA PDPL — `sa-pdpl`

_Saudi Personal Data Protection Law_

#### SA PDPL@current

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)
- Authoritative source: https://sdaia.gov.sa/en/SDAIA/about/Files/PersonalDataEnglish.pdf

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

### SAMA CSF — `sama-csf`

_SAMA Cyber Security Framework_

#### SAMA CSF@v1.0 (2017)

- Common clauses: **2**
- Covered: **1** (50.00%)
- Priority-weighted coverage: **50.00%** (1.0000 / 2.0000)
- Authoritative source: https://www.sama.gov.sa/en-US/Laws/BankingRules/SAMA%20Cyber%20Security%20Framework.pdf

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `3.1.1` | Cyber security governance | 1.00 | ✖ 0 | — | — |
| `3.3.5` | Security monitoring | 1.00 | ✔ 5 | partial | 1.1.76, 12.1.4, 17.2.2, 4.1.1, 9.4.1 |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `3.1.1` | Cyber security governance |

</details>

### SG PDPA — `sg-pdpa`

_Singapore Personal Data Protection Act_

#### SG PDPA@2020 amended

- Common clauses: **3**
- Covered: **3** (100.00%)
- Priority-weighted coverage: **100.00%** (3.0000 / 3.0000)
- Authoritative source: https://sso.agc.gov.sg/Act/PDPA2012

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `§24` | Protection of personal data obligation | 1.00 | ✔ 2 | partial | 11.1.5, 11.1.6 |
| `§26A` | Data breach notification | 1.00 | ✔ 2 | partial | 11.1.6, 16.3.6 |
| `§26B` | Criteria for notifiability | 1.00 | ✔ 1 | partial | 11.1.6 |

### SWIFT CSP — `swift-csp`

_SWIFT Customer Security Programme_

#### SWIFT CSP@CSCF v2025

- Common clauses: **3**
- Covered: **2** (66.67%)
- Priority-weighted coverage: **66.67%** (2.0000 / 3.0000)
- Authoritative source: https://www.swift.com/myswift/customer-security-programme-csp/security-controls

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `1.1` | SWIFT environment protection | 1.00 | ✔ 2 | partial | 5.1.7, 5.2.2 |
| `6.1` | Malware protection | 1.00 | ✖ 0 | — | — |
| `6.4` | Logging and monitoring | 1.00 | ✔ 6 | partial | 1.1.65, 1.2.33, 13.1.35, 13.1.36, 15.3.2, 7.1.40 |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `6.1` | Malware protection |

</details>

### Swiss nFADP — `swiss-nfadp`

_Swiss Federal Act on Data Protection (nFADP)_

#### Swiss nFADP@2020 revision

- Common clauses: **2**
- Covered: **1** (50.00%)
- Priority-weighted coverage: **50.00%** (1.0000 / 2.0000)
- Authoritative source: https://www.fedlex.admin.ch/eli/cc/2022/491/en

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.7` | Privacy by design | 1.00 | ✖ 0 | — | — |
| `Art.24` | Data breach notification | 1.00 | ✔ 2 | partial | 22.39.1, 22.39.2 |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `Art.7` | Privacy by design |

</details>

### TSA SD — `tsa-sd`

_TSA Pipeline Security Directive_

#### TSA SD@SD02C

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://www.tsa.gov/sd02c

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `III.A` | Cybersecurity plan | 1.00 | ✔ 5 | partial | 14.2.11, 14.2.4, 15.3.1, 15.3.2, 15.3.37 |
| `III.D` | Cybersecurity assessment | 1.00 | ✔ 2 | partial | 14.2.11, 14.9.22 |

### Cyber Essentials — `uk-cyber-essentials`

_UK NCSC Cyber Essentials_

#### Cyber Essentials@Montpellier (2025)

- Common clauses: **2**
- Covered: **2** (100.00%)
- Priority-weighted coverage: **100.00%** (2.0000 / 2.0000)
- Authoritative source: https://www.ncsc.gov.uk/cyberessentials/overview

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `CE.BF.1` | Boundary firewalls | 1.00 | ✔ 3 | partial | 17.1.8, 17.3.3, 5.2.2 |
| `CE.SAU.1` | Secure authentication & access | 1.00 | ✔ 5 | partial | 1.1.108, 17.2.2, 4.1.5, 9.1.1, 9.3.1 |

### UK GDPR — `uk-gdpr`

_UK General Data Protection Regulation_

#### UK GDPR@post-Brexit

- Common clauses: **1**
- Covered: **1** (100.00%)
- Priority-weighted coverage: **100.00%** (1.0000 / 1.0000)
- Authoritative source: https://www.legislation.gov.uk/eur/2016/679/contents

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Art.32` | Security of processing | 1.00 | ✔ 3 | contributing | 22.35.2, 22.35.3, 22.41.1 |

### UK NIS — `uk-nis`

_UK Network and Information Systems Regulations 2018_

#### UK NIS@2018

- Common clauses: **2**
- Covered: **1** (50.00%)
- Priority-weighted coverage: **50.00%** (1.0000 / 2.0000)
- Authoritative source: https://www.legislation.gov.uk/uksi/2018/506/contents

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|
| `Reg.10` | OES security duties | 1.00 | ✖ 0 | — | — |
| `Reg.11` | Incident reporting | 1.00 | ✔ 2 | partial | 16.1.20, 16.3.6 |

<details><summary>Top gaps (ranked by priority weight)</summary>

| Priority | Clause | Topic |
|---------:|--------|-------|
| 1.00 | `Reg.10` | OES security duties |

</details>

## Tier 3 frameworks

### Multiple — `meta-multi`

_Placeholder: multi-regulation or jurisdiction-generic_

#### Multiple@n/a

- Common clauses: **0**
- Covered: **0** (0.00%)
- Priority-weighted coverage: **0.00%** (0.0000 / 0.0000)

| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |
|--------|-------|---------:|----:|---------------|------------|

---

_This file is generated by `scripts/audit_compliance_gaps.py`. See `docs/coverage-methodology.md` for clause / priority / assurance definitions._
