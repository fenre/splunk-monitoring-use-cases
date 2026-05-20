# Compliance coverage report

_Generated: 2026-05-20T10:48:22Z_ by `python -m splunk_uc audit-compliance-mappings`. Do not hand-edit.

Status: **passed**

## Summary

* UC files checked: **7929**
* UC files valid:   **7929**
* Compliance entries: **2790**
* Findings: **0** (errors: **0**, baselined: **0**)
* Baseline (`tests/golden/audit-baseline.json`): total **0**, tolerated this run **0**, new errors **0**, unused fingerprints **0** (see `docs/coverage-methodology.md` § 12)

## Global coverage (all tiers)

* Clause coverage %: **92.9878**
* Priority-weighted %: **93.187**
* Assurance-adjusted %: **71.0244**

## Per tier

| Tier | Clause % | Priority-weighted % | Assurance-adjusted % |
|------|----------|----------------------|-----------------------|
| tier-1 | 90.8889 | 90.8982 | 74.9462 |
| tier-2 | 97.549 | 98.0483 | 62.7761 |
| tier-3 | 100.0 | 100.0 | 50.0 |

## Per family (derivesFrom roots)

| Family root | Clause % | Priority-weighted % | Assurance-adjusted % |
|-------------|----------|----------------------|-----------------------|
| api-rp-1164 | 100.0 | 100.0 | 50.0 |
| apra-cps-234 | 100.0 | 100.0 | 50.0 |
| asd-e8 | 100.0 | 100.0 | 60.0 |
| au-privacy-act | 100.0 | 100.0 | 50.0 |
| awia | 96.4286 | 97.2 | 97.2 |
| bait-kait | 100.0 | 100.0 | 50.0 |
| basel-iii | 100.0 | 100.0 | 50.0 |
| bsi-kritisv | 100.0 | 100.0 | 50.0 |
| cert-in | 90.0 | 94.1176 | 88.2353 |
| circia | 100.0 | 100.0 | 95.8498 |
| cjis | 100.0 | 100.0 | 50.0 |
| clc-ts-50701 | 82.1429 | 85.3282 | 85.3282 |
| cmmc | 100.0 | 100.0 | 83.3333 |
| cn-csl | 93.3333 | 93.3333 | 90.0 |
| cobit | 100.0 | 100.0 | 50.0 |
| coppa | 100.0 | 100.0 | 50.0 |
| coso | 100.0 | 100.0 | 50.0 |
| do-326a | 100.0 | 100.0 | 83.3333 |
| dora | 100.0 | 100.0 | 79.291 |
| eidas | 100.0 | 100.0 | 50.0 |
| eu-ai-act | 100.0 | 100.0 | 50.0 |
| eu-aml | 100.0 | 100.0 | 50.0 |
| eu-cra | 100.0 | 100.0 | 75.0 |
| fca-smcr | 100.0 | 100.0 | 50.0 |
| fca-ss1-21 | 100.0 | 100.0 | 50.0 |
| fda-part-11 | 100.0 | 100.0 | 66.6667 |
| fedramp | 100.0 | 100.0 | 66.6667 |
| ferc-cip | 100.0 | 100.0 | 50.0 |
| ferpa | 100.0 | 100.0 | 50.0 |
| fisma | 100.0 | 100.0 | 50.0 |
| fr-lpm | 87.5 | 87.5 | 75.0 |
| gdpr | 100.0 | 100.0 | 68.6111 |
| glba | 100.0 | 100.0 | 50.0 |
| hipaa-privacy | 100.0 | 100.0 | 44.8529 |
| hipaa-security | 100.0 | 100.0 | 64.8551 |
| hitrust | 100.0 | 100.0 | 75.0 |
| hkma-tm-g-2 | 100.0 | 100.0 | 50.0 |
| iec-61511 | 83.3333 | 81.8182 | 75.0 |
| iec-62443 | 100.0 | 100.0 | 63.5135 |
| imo-msc-428-98 | 94.4444 | 94.4444 | 88.8889 |
| iso-27001 | 100.0 | 100.0 | 85.7422 |
| it-grundschutz | 100.0 | 100.0 | 75.0 |
| it-sig-2 | 100.0 | 100.0 | 50.0 |
| mas-trm | 100.0 | 100.0 | 50.0 |
| meta-multi | 0.0 | 0.0 | 0.0 |
| mifid-ii | 100.0 | 100.0 | 50.0 |
| nca-otcc | 100.0 | 100.0 | 89.6947 |
| nerc-cip | 100.0 | 100.0 | 70.0 |
| nesa-uae-ias | 100.0 | 100.0 | 50.0 |
| nis2 | 100.0 | 100.0 | 49.4444 |
| nist-800-53 | 100.0 | 100.0 | 73.8095 |
| nist-csf | 100.0 | 100.0 | 67.5393 |
| no-kbf-nve | 100.0 | 100.0 | 50.0 |
| no-personopplysningsloven | 100.0 | 100.0 | 50.0 |
| no-petroleumsforskriften | 100.0 | 100.0 | 50.0 |
| no-sikkerhetsloven | 100.0 | 100.0 | 50.0 |
| nzism | 100.0 | 100.0 | 50.0 |
| pci-dss | 100.0 | 100.0 | 94.7183 |
| pipl | 100.0 | 100.0 | 50.0 |
| pra-ss2-21 | 100.0 | 100.0 | 50.0 |
| psd2 | 100.0 | 100.0 | 50.0 |
| qcb-cyber | 100.0 | 100.0 | 50.0 |
| rbi-cyber | 100.0 | 100.0 | 50.0 |
| sa-pdpl | 100.0 | 100.0 | 50.0 |
| sama-csf | 100.0 | 100.0 | 50.0 |
| sg-cyber-act | 40.0 | 40.0 | 36.6667 |
| sg-pdpa | 100.0 | 100.0 | 50.0 |
| soc-2 | 100.0 | 100.0 | 87.5899 |
| soci | 75.0 | 77.7328 | 71.6599 |
| sox-itgc | 100.0 | 100.0 | 92.3423 |
| swift-csp | 100.0 | 100.0 | 50.0 |
| tsa-sd | 100.0 | 100.0 | 50.0 |
| tsa-surface | 35.7143 | 36.4964 | 36.4964 |
| uk-cyber-essentials | 100.0 | 100.0 | 50.0 |
| uk-nis | 100.0 | 100.0 | 50.0 |
| unece-r155 | 100.0 | 100.0 | 50.0 |
| unece-r156 | 100.0 | 100.0 | 50.0 |

## Per regulation-version

| Regulation@Version | Tier | Clause % | Priority-weighted % | Assurance-adjusted % |
|---------------------|------|----------|----------------------|-----------------------|
| API RP 1164@3rd edition | 2 | 100.0 | 100.0 | 50.0 |
| APPI@2022 amendments | 2 | 100.0 | 100.0 | 50.0 |
| APRA CPS 234@current | 2 | 100.0 | 100.0 | 50.0 |
| ASD E8@Nov 2023 | 2 | 100.0 | 100.0 | 60.0 |
| AU Privacy Act@current | 2 | 100.0 | 100.0 | 50.0 |
| AWIA@2018-amended-SDWA-1433 | 1 | 96.4286 | 97.2 | 97.2 |
| BAIT/KAIT@Aug 2021 | 2 | 100.0 | 100.0 | 50.0 |
| BSI-KritisV@2021 (as amended) | 2 | 100.0 | 100.0 | 50.0 |
| Basel III@BCBS 2021 | 2 | 100.0 | 100.0 | 50.0 |
| CCPA/CPRA@CPRA (as amended) | 2 | 100.0 | 100.0 | 87.037 |
| CERT-In Directions 2022@2022-04-28-cert-in-directions-with-2023-dpdp | 1 | 90.0 | 94.1176 | 88.2353 |
| CIRCIA@2022-act-with-2024-nprm | 1 | 100.0 | 100.0 | 95.8498 |
| CJIS@v5.9.4 | 2 | 100.0 | 100.0 | 50.0 |
| CLC/TS 50701@2021-with-iec63452-alignment | 2 | 82.1429 | 85.3282 | 85.3282 |
| CMMC@2.0 | 1 | 100.0 | 100.0 | 83.3333 |
| CN CSL / DSL / PIPL@2017-csl-with-2021-dsl-pipl-and-2022-ciio-cross-border | 1 | 93.3333 | 93.3333 | 90.0 |
| COBIT@2019 | 2 | 100.0 | 100.0 | 50.0 |
| COPPA@16 CFR 312 | 2 | 100.0 | 100.0 | 50.0 |
| COSO@2013 ICFR | 2 | 100.0 | 100.0 | 50.0 |
| Cyber Essentials@Montpellier (2025) | 2 | 100.0 | 100.0 | 50.0 |
| DO-326A / ED-202A@2014-do-326a-with-2020-do-355a-and-2026-easa-part-is | 1 | 100.0 | 100.0 | 83.3333 |
| DORA@Regulation (EU) 2022/2554 | 1 | 100.0 | 100.0 | 79.291 |
| EU AI Act@Regulation (EU) 2024/1689 | 2 | 100.0 | 100.0 | 50.0 |
| EU AML@6AMLD / AMLR 2024 | 2 | 100.0 | 100.0 | 50.0 |
| EU CRA@Regulation (EU) 2024/2847 | 2 | 100.0 | 100.0 | 75.0 |
| FCA SM&CR@current | 2 | 100.0 | 100.0 | 50.0 |
| FCA SS1/21@2021 | 2 | 100.0 | 100.0 | 50.0 |
| FDA Part 11@current | 2 | 100.0 | 100.0 | 66.6667 |
| FERC CIP@current | 3 | 100.0 | 100.0 | 50.0 |
| FERPA@20 USC §1232g | 2 | 100.0 | 100.0 | 50.0 |
| FISMA@2014 | 2 | 100.0 | 100.0 | 50.0 |
| FedRAMP@Rev.5 Baselines | 2 | 100.0 | 100.0 | 66.6667 |
| France LPM (OIV)@2013-2018-with-anssi-2024-decrees | 1 | 87.5 | 87.5 | 75.0 |
| GDPR@2016/679 | 1 | 100.0 | 100.0 | 73.2659 |
| GLBA@16 CFR 314 (2023 amendments) | 2 | 100.0 | 100.0 | 50.0 |
| HIPAA Privacy@current | 2 | 100.0 | 100.0 | 44.8529 |
| HIPAA Security@2013-final | 1 | 100.0 | 100.0 | 64.8551 |
| HITRUST@v11 | 2 | 100.0 | 100.0 | 75.0 |
| HKMA TM-G-2@current | 2 | 100.0 | 100.0 | 50.0 |
| IEC 61511 + ISA TR84.00.09@2016-iec-61511-ed-2-with-isa-tr84-00-09 | 1 | 83.3333 | 81.8182 | 75.0 |
| IEC 62443@2013-ongoing | 2 | 100.0 | 100.0 | 63.5135 |
| IMO MSC.428(98)@2017-msc-428-98-with-2022-circ-3-rev-2-and-2024-iacs-e26-e27 | 1 | 94.4444 | 94.4444 | 88.8889 |
| ISO 27001@2013 | 1 | 100.0 | 100.0 | 78.7234 |
| ISO 27001@2022 | 1 | 100.0 | 100.0 | 87.3206 |
| IT-Grundschutz@2023 Edition | 2 | 100.0 | 100.0 | 75.0 |
| IT-SiG 2.0@2021 | 2 | 100.0 | 100.0 | 50.0 |
| LGPD@Lei nº 13.709/2018 | 2 | 100.0 | 100.0 | 50.0 |
| MAS TRM@2021 | 2 | 100.0 | 100.0 | 50.0 |
| MiFID II@Directive 2014/65/EU | 2 | 100.0 | 100.0 | 50.0 |
| Multiple@n/a | 3 | 0.0 | 0.0 | 0.0 |
| NCA OTCC@1:2022 | 2 | 100.0 | 100.0 | 89.6947 |
| NERC CIP@current | 2 | 100.0 | 100.0 | 70.0 |
| NESA IAS@v2 (2020) | 2 | 100.0 | 100.0 | 50.0 |
| NIS2@Directive (EU) 2022/2555 | 1 | 100.0 | 100.0 | 49.4444 |
| NIST 800-53@Rev. 5 | 1 | 100.0 | 100.0 | 73.8095 |
| NIST CSF@1.1 | 1 | 100.0 | 100.0 | 100.0 |
| NIST CSF@2.0 | 1 | 100.0 | 100.0 | 61.4907 |
| NO KBF@2012 as amended | 2 | 100.0 | 100.0 | 50.0 |
| NO Personopplysningsloven@2018 | 2 | 100.0 | 100.0 | 50.0 |
| NO Petroleumsforskriften@1997 as amended | 2 | 100.0 | 100.0 | 50.0 |
| NO Sikkerhetsloven@2018 | 2 | 100.0 | 100.0 | 50.0 |
| NZISM@3.7 | 2 | 100.0 | 100.0 | 50.0 |
| PCI DSS@v3.2.1 | 1 | 100.0 | 100.0 | 100.0 |
| PCI DSS@v4.0 | 1 | 100.0 | 100.0 | 93.0876 |
| PIPL@2021 | 2 | 100.0 | 100.0 | 50.0 |
| PRA SS2/21@2021 | 2 | 100.0 | 100.0 | 50.0 |
| PSD2@Directive (EU) 2015/2366 | 2 | 100.0 | 100.0 | 50.0 |
| QCB Cyber@2018 | 2 | 100.0 | 100.0 | 50.0 |
| RBI Cyber@2016 (as amended) | 2 | 100.0 | 100.0 | 50.0 |
| SA PDPL@current | 2 | 100.0 | 100.0 | 50.0 |
| SAMA CSF@v1.0 (2017) | 2 | 100.0 | 100.0 | 50.0 |
| SG Cyber Act@2018-amended-2024 | 1 | 40.0 | 40.0 | 36.6667 |
| SG PDPA@2020 amended | 2 | 100.0 | 100.0 | 50.0 |
| SOC 2@2017 TSC | 1 | 100.0 | 100.0 | 87.5899 |
| SOCI Act@2022-SLACIP+CIRMP-2023 | 1 | 75.0 | 77.7328 | 71.6599 |
| SOX ITGC@PCAOB AS 2201 | 1 | 100.0 | 100.0 | 92.3423 |
| SWIFT CSP@CSCF v2025 | 2 | 100.0 | 100.0 | 50.0 |
| Swiss nFADP@2020 revision | 2 | 100.0 | 100.0 | 50.0 |
| TSA SD@SD02C | 2 | 100.0 | 100.0 | 50.0 |
| TSA Surface SDs@2024-consolidated-pipeline-rail | 1 | 35.7143 | 36.4964 | 36.4964 |
| UK GDPR@post-Brexit | 2 | 100.0 | 100.0 | 50.0 |
| UK NIS@2018 | 2 | 100.0 | 100.0 | 50.0 |
| UN R155@2021 | 2 | 100.0 | 100.0 | 50.0 |
| UN R156@2021 | 2 | 100.0 | 100.0 | 50.0 |
| eIDAS@Regulation (EU) 2024/1183 | 2 | 100.0 | 100.0 | 50.0 |

## Golden tuples

* Total: **52**  |  Passed: **52**  |  Failed: **0**

---

_This file is generated by `python -m splunk_uc audit-compliance-mappings` (or `make audit-compliance-mappings`). See `docs/coverage-methodology.md` for the formal definitions._
