# Roadmap

> The plan below is indicative, not contractual. Dates can slip; priorities
> can change based on user feedback and contributor bandwidth. The **source of
> truth** for *what has shipped* is [`CHANGELOG.md`](CHANGELOG.md).

## Current release

**v8.6.4 — Phase 4 primer back-fill — three new tier-1 deep dives close the OT-regulation primer gap (TSA Surface §4.18, SG Cyber Act 2018 §4.19, France LPM §4.20)** *(shipped 2026-05-15)*

Theme: **plan-gap closure for the six-phase OT regulation deep-dive
arc shipped through v8.5.0 → v8.6.3.** The Phase 4 batch (TSA Surface
+ SG Cyber Act + France LPM) had registered each framework in
`data/regulations.json`, populated subcategories 22.56 / 22.57 / 22.58,
authored 51 gold-tier UCs and three evidence packs, and added three
areas to `non-technical-view.js` — but the corresponding deep-dive
primer sections in `docs/regulatory-primer.md` had been skipped, so
the `non-technical-view.js` entries pointed at `#tsa-surface`,
`#sg-cyber-act`, and `#fr-lpm` anchors that did not yet exist. v8.6.4
lands those three primer sections, renumbers the subsequent §4.x
deep-dives by three positions to keep numerical and subcategory order
aligned, fixes a one-line introductory count-drift in §1 of the
primer, and back-fills the `evidencePack` field on three
`non-technical-view.js` areas. No new UCs, no new regulations, no
schema changes — strictly a documentation patch.

Three new tier-1 primer deep dives:

1. **§4.18 TSA Surface Cybersecurity Security Directives** (US
   Pipeline + Freight Rail + Passenger Rail + Aviation) — the TSA SD
   family issued under expedited authority at 49 U.S.C. §
   114(l)(2)(A) after the May 2021 Colonial Pipeline incident.
   Covers the four CIP control families, the 24-hour CISA-reporting
   clock with PHMSA / FRA / FAA dual-clock parallel notification,
   the Cybersecurity Coordinator role, the CIRP annual exercise,
   the Cybersecurity Assessment Programme (CAP), and the *Enhancing
   Surface Cyber Risk Management* NPRM as the pending durable Final
   Rule. Cross-refs NERC CIP<sup class="ref">[<a href="#ref-5">5</a>]</sup> / AWIA / CIRCIA.
2. **§4.19 SG Cybersecurity Act 2018 + CCoP 2.0 + CSA CII
   Regulations** (Singapore) — the *Cybersecurity Act 2018* (Act 9
   of 2018, amended 2024) and its implementing instruments
   (CCoP 2.0, CII Regulations 2018). Covers the CSA designation
   process, **the 2-hour prescribed-incident reporting clock — the
   tightest statutory clock in this catalogue**, annual audit and
   biennial risk assessment, the CSA-directed exercise programme,
   and the 2024 amendment scope expansion to FDI / STCC / SCI.
3. **§4.20 France LPM OIV Regime + Décret 2015-351 + ANSSI
   Implementing Decrees** (France) — the *Loi de Programmation
   Militaire* (LPM 2014–2019 / 2018 / 2024) and the *Code de la
   Défense* L1332-6-1 et seq., operationalised through Décret
   2015-351 and the **twenty ANSSI cybersecurity rules** bound to
   designated SIIVs operated by ~240 OIVs across 12 SAIV sectors.
   Covers OIV / SIIV designation, the Cybersecurity Officer (RSSI)
   role, SIIV asset inventory, identity + access control + MFA,
   ANSSI-mandated detection capability with mandatory **PDIS
   qualification** for any third-party detection provider, and
   CERT-FR incident reporting.

Section renumbering (anchors preserved):

| Anchor | v8.6.3 number | v8.6.4 number | Subcategory |
|---|---|---|---|
| `#imo-msc-428-98` | §4.18 | §4.21 | §22.59 |
| `#do-326a` | §4.19 | §4.22 | §22.60 |
| `#cn-csl` | §4.20 | §4.23 | §22.61 |
| `#cert-in` | §4.21 | §4.24 | §22.62 |
| `#iec-61511` | §4.22 | §4.25 | §22.63 |

### Shipped outcomes

- **22 tier-1 frameworks now all covered to gold-tier primer depth.**
  Before v8.6.4, only 19 of the 22 tier-1 frameworks had deep-dive
  primer sections; TSA Surface / SG Cyber Act / France LPM had every
  other artefact (data, UCs, evidence packs, non-technical areas) but
  no primer §4.x. v8.6.4 closes that gap.
- **Primer §1 count drift fixed** from "18 tier-1 frameworks covered
  deeply" to "22 tier-1 frameworks covered deeply" — matching the
  actual tier-1 count in `data/regulations.json`.
- **`non-technical-view.js` `evidencePack` back-filled** on three
  tier-1 cat-22 areas. Evidence packs themselves have existed on
  disk since v8.6.0; v8.6.4 surfaces them through the non-technical
  mode per `non-technical-sync.mdc`.
- **Catalogue counts unchanged.** 23 categories · 265 subcategories
  · 7,929 UCs · 82 regulations (22 tier-1, 58 tier-2, 2 tier-3).
- **All 14 CI gates pass.** No new UCs, no new regulations, no
  schema changes; this is strictly a documentation patch.

See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.6.4 release
notes.

---

## Previous releases

**v8.6.3 — OT Regulation Deep-Dive (Phase 6: China CSL / DSL / PIPL<sup class="ref">[<a href="#ref-8">8</a>]</sup> / CII + CERT-In Directions 2022 / DPDP Act 2023 + IEC 61511 / 61508 functional-safety cybersecurity overlay) — closes the six-phase OT regulation deep-dive arc** *(shipped 2026-05-14)*

Theme: **Phase 6 of the multi-phase OT-regulation programme — final
phase that closes the six-phase, 247-UC arc that opened with v8.5.0
(Phase 3: NCA OTCC + SOCI + AWIA), continued through v8.6.0 (Phase 4:
TSA Surface + Singapore Cyber Act + France LPM), v8.6.1 (Phase 5a:
IMO MSC.428(98)), and v8.6.2 (Phase 5b: RTCA DO-326A / EUROCAE
ED-202A).** v8.6.3 lands three tier-1 frameworks in a single release:

1. **China CSL / DSL / PIPL / CII Regulations / MLPS 2.0** — the four
   primary PRC statutes (CSL 2017, DSL 2021, PIPL 2021, CIIO
   Regulations 2021) with the Cybersecurity Review Measures (2022),
   CAC Cross-Border Security Assessment + Standard Contract +
   Certification mechanisms (2022/2023), and MLPS 2.0 implementation
   standard (GB/T 22239-2019). 12 hand-written gold-tier UCs.
2. **CERT-In Directions 2022 + DPDP Act 2023** — CERT-In Directions
   of 28 April 2022 (No. 20(3)/2022-CERT-In) under IT Act Section
   70B(6), binding from 27 June 2022, with the Digital Personal Data
   Protection Act 2023 (passed 11 August 2023) and IT Act Section 43A
   SPDI Rules 2011. Carries the **6-hour incident-reporting clock —
   the shortest such clock in any major jurisdiction**. 8 hand-
   written gold-tier UCs.
3. **IEC 61508 / 61511 + ISA-TR84.00.09 + IEC 62443<sup class="ref">[<a href="#ref-3">3</a>]</sup>-3-2 / 62443-3-3**
   — the universally-recognised Good Engineering Practice (RAGAGEP)
   for Safety Instrumented Systems in the process industries,
   incorporated by reference into OSHA PSM (29 CFR 1910.119), EPA
   RMP, HSE COMAH 2015, Seveso III, MSIHC Rules 1989 (India), KOSHA
   PSM (Korea), and most major process-safety legal regimes
   worldwide. IEC 61511 Edition 2 Clause 8.2.4 mandates a SIS
   Cybersecurity Risk Assessment via ISA-TR84.00.09 — the bridge
   between functional safety and OT cybersecurity. 7 hand-written
   gold-tier UCs.

All three regulations land with auditor-grade evidence packs and the
catalogue tier-1 count rises to **22 frameworks** (was 19). Total
regulatory inventory rises to **82 frameworks** (was 79).

- **China CSL / DSL / PIPL / CII Regulations / MLPS 2.0 registered**
  in `data/regulations.json` with 15 monitored clauses: CSL Art.21
  (network-security graded protection + ≥6-month log retention),
  Art.25 (incident-response plans + reporting), Art.31 (CIIO regime),
  Art.34 (CIIO security measures), Art.37 (CIIO data localisation),
  Art.38 (annual CII inspection); DSL Art.21 (Important Data
  Catalogue), Art.27 (data-security-management + log retention),
  Art.29 (8-hour Significant / 24-hour Ordinary incident reporting),
  Art.36 (data-blocking statute); PIPL Art.24 (ADM transparency),
  Art.38 (cross-border PI transfer), Art.41 (foreign data-request
  blocking), Art.51 / 52 / 55 / 56 (SPIH governance); CIIO Reg
  Art.14 + CRM 2022 (pre-procurement cybersecurity review); MLPS 2.0
  GB/T 22239-2019 (Level 2+ MPS filing, Level 3+ annual independent
  assessment).
- **12 hand-written gold-tier UCs** under subcategory `22.61` (China
  CSL/DSL/PIPL/CII): MLPS 2.0 grading register (UC-22.61.1), CIIO
  designation + annual inspection archive (UC-22.61.2), the layered
  CSL Art.25 + DSL Art.29 tiered (1h / 8h / 24h) incident-reporting
  clock (UC-22.61.3), CSL Art.37 + CIIO data-localisation egress
  detection (UC-22.61.4), DSL Art.21 Important Data Catalogue
  freshness (UC-22.61.5), DSL Art.36 + PIPL Art.41 foreign data-
  request blocking with competent-authority approval workflow
  (UC-22.61.6), PIPL Art.38 cross-border PI transfer register
  (UC-22.61.7), Significant PIH governance + PIPL Art.51 / 52 / 55 /
  56 internal management + DPO + PIPIA freshness (UC-22.61.8), PIPL
  Art.24 automated decision-making transparency + opt-out audit
  (UC-22.61.9), CIIO Reg Art.14 + CRM 2022 pre-procurement
  cybersecurity review (UC-22.61.10), MLPS L3+ annual independent
  assessment cadence (UC-22.61.11), and CSL Art.21 + DSL Art.27 +
  GB/T 22239 ≥6-month log retention with integrity protection
  (UC-22.61.12).
- **CERT-In Directions 2022 + DPDP Act 2023 registered** in
  `data/regulations.json` with 10 monitored clauses: CERT-In
  Direction (ii) 6-hour cybersecurity incident reporting clock for
  20 enumerated incident categories, Direction (iii) Indian NTP
  synchronisation (NIC `samay1.nic.in` / NPL `time.npl.res.in` with
  ±100 ms drift), Direction (iv) 180-day rolling ICT log retention
  within Indian jurisdiction, Direction (v) VPN/VPS/cloud subscriber
  KYC (5-year post-cancellation retention), Direction (vi)
  designated POC register with 24×7 contactability test, Direction
  (vii) Virtual Asset Service Provider KYC + 5-year transaction
  retention, DPDP Section 8(6) 72-hour breach notification to the
  Data Protection Board of India + parallel Data Principal
  notification, DPDP Section 10 Significant Data Fiduciary
  designation + India-resident DPO + annual independent audit, IT
  Act Section 43A SPDI Rules 2011 reasonable-security-practices
  obligation.
- **8 hand-written gold-tier UCs** under subcategory `22.62` (CERT-
  In Directions + DPDP): the 6-hour reporting clock (UC-22.62.1),
  Indian NTP drift monitoring (UC-22.62.2), POC register +
  contactability test (UC-22.62.3), 180-day log retention
  (UC-22.62.4), VPN/VPS/cloud subscriber-KYC (UC-22.62.5), VASP
  customer KYC + transaction retention (UC-22.62.6), DPDP §10
  Significant Data Fiduciary register (UC-22.62.7), and the DPDP
  Section 8(6) 72-hour breach-notification clock (UC-22.62.8).
- **IEC 61508 / 61511 + ISA-TR84.00.09 + IEC 62443-3-2 / 62443-3-3
  registered** in `data/regulations.json` with 12 monitored clauses:
  IEC 61511 Clause 5 (16-phase safety lifecycle), Cl.8.2.4 (SIS
  Cybersecurity Risk Assessment per ISA-TR84.00.09), Cl.10 (SIS
  Safety Requirements Specification + SIL allocation), Cl.11.7.6
  (SIS-BPCS separation + SIF override governance), Cl.14 (SIS
  operation + maintenance), Cl.16.3 (proof-test interval + demand-
  rate verification), Cl.17.2 (SIS Management-of-Change discipline);
  IEC 62443-3-2:2020 (zone-and-conduit partitioning + SL-T target),
  IEC 62443-3-3:2013 FR1–FR7 (Foundational Requirements +
  capabilities); ISA-TR84.00.09 §4 + §5 (integrated cybersecurity
  programme + 5-min ack / 8-h CRA finding / 24-h PHA-refresh
  decision).
- **7 hand-written gold-tier UCs** under subcategory `22.63` (IEC
  61511 + cybersecurity overlay): the 16-phase safety-lifecycle
  compliance register (UC-22.63.1), SIS Cybersecurity Risk
  Assessment freshness with IEC 62443-3-2 zone-and-conduit
  partitioning (UC-22.63.2), Cl.11.7.6 SIS-BPCS separation with
  authorised + annunciated + time-bounded SIF overrides
  (UC-22.63.3), Cl.16.3 proof-test interval + demand-rate +
  spurious-trip-rate trending against PFD/PFH SIL allocation
  (UC-22.63.4), Cl.17.2 SIS Management-of-Change discipline
  (UC-22.63.5), ISA-TR84.00.09 integrated cybersecurity programme
  (UC-22.63.6), and IEC 62443-3-2 + IEC 61511 Cl.8.2.4 zone-and-
  conduit SL-T / SL-C / SL-A measurement across all seven IEC
  62443-3-3 Foundational Requirements (UC-22.63.7). Every UC carries
  the full gold-tier payload (`controlTest` + parameterised SPL +
  `controlObjective` + `evidenceArtifact` + `obligationRef` +
  `knownFalsePositives` with suppression + `detailedImplementation`
  with KV-store schema + cron + runbook + process-safety-specific
  notes + `grandmaExplanation`).
- **Three new auditor-facing evidence packs** at
  [`docs/evidence-packs/cn-csl.md`](docs/evidence-packs/cn-csl.md),
  [`docs/evidence-packs/cert-in.md`](docs/evidence-packs/cert-in.md),
  and
  [`docs/evidence-packs/iec-61511.md`](docs/evidence-packs/iec-61511.md)
  + structured metadata in
  [`data/evidence-pack-extras.json`](data/evidence-pack-extras.json)
  covering each regime's anatomy, the regulator-facing scope, the
  per-clause evidence patterns, retention rules, common audit
  deficiencies + remediation, roles matrix (CISO + DPO + Process
  Safety Manager + Process Engineering + Asset Owner), reporting
  cadence, and a list of typical auditor questions cross-mapped to
  the catalogue UCs that answer each one.
- **Documentation wire-up** — three new cat-22 area entries in
  `non-technical-view.js` (between `do-326a` and `eu-ai-act`) with
  `whatItIs` / `whoItAffects` / `splunkValue` / `primer` /
  `evidencePack` + three representative UCs per area; three new
  forward maps in `docs-uc-map.js` from each evidence pack to its
  representative UCs; three new full primer sections in
  `docs/regulatory-primer.md` — §4.23 (China CSL/DSL/PIPL/CII +
  MLPS 2.0), §4.24 (CERT-In Directions 2022 + DPDP Act 2023), §4.25
  (IEC 61511 / 61508 + ISA-TR84.00.09 + IEC 62443 cybersecurity
  overlay), each covering convergence with adjacent regimes (CSL
  vs DSL vs PIPL vs CIIO, CERT-In vs DPDP vs SPDI Rules vs Indian
  IT Act, IEC 61511 vs OSHA PSM vs EPA RMP vs HSE COMAH vs Seveso
  III) and the count-drift fix from "16 tier-1 frameworks / 78
  inventory / subcat range 22.1–22.34" to "22 tier-1 frameworks /
  82 inventory / subcat range 22.1–22.34 and 22.50–22.63".

### Shipped outcomes

- Catalogue now ships **82 mapped regulations** (was 79) and
  **7,929 UCs** (was 7,902). Cat-22 alone gains 27 gold UCs across
  three new subcategories (22.61, 22.62, 22.63).
- Tier-1 framework count rises to **22**; auditor evidence pack
  count reaches **22**. Three new tier-1 frameworks join the deep-
  dive list: China CSL/DSL/PIPL/CII (93.3 % clause coverage),
  CERT-In Directions + DPDP (90.0 %), IEC 61511 + cybersecurity
  overlay (83.3 %).
- Global tier-1 coverage settles at **90.89 %**, tier-2 stays at
  **97.55 %**, tier-3 stays at **100 %**.
- Compliance entries cross **2,678** (was 2,628). SPL
  hallucinations: **0**. Prerequisite-graph errors: **0**. Catalog-
  schema / UC-structure / monitoring-type / MITRE regressions:
  **0**. All **14** CI gates pass.
- **The six-phase, 247-UC OT-regulation deep-dive arc that opened
  with v8.5.0 (Phase 3: NCA OTCC + SOCI + AWIA) closes here.** Total
  arc delivery: Phase 3 (NCA OTCC + SOCI + AWIA, 70 UCs across 22.50
  / 22.51 / 22.52); Phase 4 (TSA Surface + Singapore Cyber Act +
  France LPM, 51 UCs across 22.53 / 22.54 / 22.55 / 22.56 / 22.57 /
  22.58); Phase 5a (IMO MSC.428(98), 17 UCs in 22.59); Phase 5b
  (DO-326A / ED-202A, 17 UCs in 22.60); Phase 6 (China CSL/DSL/
  PIPL/CII + CERT-In + IEC 61511, 27 UCs in 22.61 / 22.62 / 22.63)
  + 65 cross-cutting tier-1 ratchet UCs. Net **+247 gold-tier UCs**,
  **+14 tier-1 frameworks**, **+10 auditor evidence packs**.

See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.6.3 release
notes.

---

**v8.6.2 — OT Regulation Deep-Dive (Phase 5b: RTCA DO-326A / EUROCAE ED-202A airworthiness security)** *(shipped 2026-05-14)*

Theme: **Phase 5b of the multi-phase OT-regulation programme — second
half of Phase 5.** v8.6.2 lands the *RTCA DO-326A / EUROCAE ED-202A —
Airworthiness Security Process Specification* (FAA + EASA + Transport
Canada + ANAC + CAA UK, tier-1, GLOBAL aviation) with the operator
continuing-airworthiness obligations from *DO-355A / ED-204A*, the
risk-assessment methods from *DO-356A / ED-203A*, the framework
guidance from *DO-391 / ED-205*, the regulator acceptance hooks from
*FAA AC 20-186* and *EASA AMC 20-42*, the four-domain trust
architecture from *ARINC 811*, and the operational ISMS overlay from
*EASA Part-IS* (Implementing Regulations (EU) 2022/1645 design side
and 2023/203 operator side). The regulation lands with an auditor-grade
evidence pack and **DO-326A becomes the first tier-1 framework with
100% clause coverage** (21/21). The catalogue tier-1 count rises to
16 frameworks.

- **DO-326A / ED-202A framework registered in `data/regulations.json`**
  with the airworthiness clause grammar covering DO-326A §2.1
  (objectives), §2.2 (PSecAA), §3.1 (Cyber Security Items), §3.2 (Threat
  Conditions Identification), §3.3 (Security Risk Assessment), §4.1
  (Security Architecture), §4.2 (Security Effectiveness Demonstration),
  §5.1 (Continued Airworthiness Security Information handoff); DO-355A
  §2.1 + §2.3 + §3.1 (operator continuing-airworthiness security,
  LSAP signature integrity, cyber-incident detection / response /
  reporting); DO-356A §3.1 (risk-assessment methods); FAA AC 20-186 §5
  and EASA AMC 20-42 §4 (regulator acceptance); ARINC 811 §4.2 (ACD /
  AISD / PIESD / POD domain architecture); and EASA Part-IS IS.OR.200
  (ISMS scope), IS.OR.205 (risk assessment), IS.OR.220 (incident
  detection / response), IS.OR.230 (24h / 72h / 1-month reporting),
  IS.OR.235 (supply-chain ISMS flow-down), IS.OR.245 (5-year record
  retention) — 21 monitored clauses.
- **17 hand-written gold-tier UCs** under the new `22.60` (RTCA
  DO-326A / EUROCAE ED-202A) subcategory: PSecAA register
  (UC-22.60.1) and DO-326A SRA coverage (UC-22.60.2); ARINC 811
  four-domain segregation drift (UC-22.60.3) and IFE-to-avionics
  traversal (UC-22.60.12); LSAP digital-signature integrity gate
  (UC-22.60.4) and Airworthiness Directive + Service Bulletin
  security-related compliance tracker (UC-22.60.5); PMAT laptop
  governance (UC-22.60.6) and Electronic Flight Bag Class 2 / Class 3
  security posture (UC-22.60.7); ACARS / CPDLC / VDL Mode 2 datalink
  integrity (UC-22.60.8) and GNSS / GPS spoofing + jamming
  (UC-22.60.9) and ADS-B / Mode S squitter integrity (UC-22.60.10);
  engine OEM remote-monitoring channel governance (UC-22.60.11);
  EASA Part-IS 24h / 72h / 1-month reporting clock (UC-22.60.13)
  and ISMS audit-evidence register (UC-22.60.14); airborne software
  cyber-SBOM vulnerability monitor (UC-22.60.15); pilot +
  maintenance cyber-incident training cadence + tabletop drill
  register (UC-22.60.16); and aeronautical database integrity
  attestation across navigation / FMS / terrain / performance /
  synthetic vision / EGPWS / weather-radar databases (UC-22.60.17).
  Every UC carries the full gold-tier payload (`controlTest` +
  parameterised SPL + `controlObjective` + `evidenceArtifact` +
  `obligationRef` + `knownFalsePositives` with suppression +
  `detailedImplementation` with KV-store schema + cron + runbook +
  aviation-specific notes + `grandmaExplanation`).
- **Auditor-facing evidence pack** at
  [`docs/evidence-packs/do-326a.md`](docs/evidence-packs/do-326a.md)
  + structured metadata in
  [`data/evidence-pack-extras.json`](data/evidence-pack-extras.json)
  covering the regulatory anatomy, the four-layer enforcement chain
  (TC-holder Continued Airworthiness Security Information → operator
  continuing-airworthiness security → in-service detection →
  mandatory reporting under Part-IS IS.OR.230 / FAA reporting
  framework), aviation-specific evidence patterns (TC-holder CASI,
  ARINC 811 SAD, LSAP loader audit, ISMS register, datalink
  integrity logs, aeronautical-database digital signatures),
  Part-IS IS.OR.245 5-year retention, common audit deficiencies +
  remediation, roles matrix (Chief Engineer + CAMO Manager +
  Director of Flight Operations + Director of Maintenance + CISO),
  and 16 typical auditor questions cross-mapped to catalogue UCs.
- **Documentation wire-up** — cat-22 area entry in
  `non-technical-view.js` (between `imo-msc-428-98` and
  `eu-ai-act`) with `whatItIs` / `whoItAffects` / `splunkValue` /
  `primer` / `evidencePack` + 3 representative UCs (22.60.1,
  22.60.13, 22.60.17); forward map in `docs-uc-map.js` from the
  evidence pack to 10 anchor UCs (22.60.1, 22.60.2, 22.60.3,
  22.60.4, 22.60.5, 22.60.13, 22.60.14, 22.60.15, 22.60.16,
  22.60.17); full primer section `docs/regulatory-primer.md`
  §4.22 covering DO-326A + DO-355A + DO-356A + DO-391 + FAA
  AC 20-186 + EASA AMC 20-42 + EASA Part-IS, the four-layer
  enforcement model, and convergence with NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup> (transport
  sector) + DORA<sup class="ref">[<a href="#ref-2">2</a>]</sup> (financial-services aviation vendors) + TSA
  SD-1582-21 (US aviation) + ICAO Annex 17 (security of civil
  aviation).
- **100% clause closure** — DO-326A reaches the catalogue's
  first tier-1 100% clause coverage (21/21). The last three
  high-level airworthiness clauses (§2.1 objectives, §3.1 CSI
  identification, §4.2 Security Effectiveness Demonstration)
  are operationally closed by genuine mappings onto five
  existing UCs (segregation drift, IFE traversal, LSAP signature
  gate, cyber-SBOM, training cadence) — no metric-chasing UCs
  added.

### Shipped outcomes

- Catalogue now ships **79 mapped regulations** (was 78) and
  **7,902 UCs** (was 7,885). Cat-22 alone gains 17 gold UCs in
  one new subcategory (22.60).
- Tier-1 framework count rises to **16**; auditor evidence pack
  count reaches **19**. DO-326A becomes the first tier-1
  framework with **100% clause coverage** (21/21).
- Global tier-1 coverage rises to **91.04%** (+0.73 pp), tier-2
  stays at **97.55%**, tier-3 stays at **100%**.
- Phase 5 closed end-to-end; the next milestone is Phase 6
  (China CII + CERT-In + IEC 61508/61511, subcats 22.61–22.63,
  27 UCs) which closes the six-phase, 247-UC arc.

See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.6.2 release notes.

**v8.6.1 — OT Regulation Deep-Dive (Phase 5a: IMO MSC.428(98) maritime cyber risk management)** *(shipped 2026-05-14)*

Theme: **Phase 5a of the multi-phase OT-regulation programme — first
half of Phase 5.** v8.6.1 lands the *IMO Resolution MSC.428(98) —
Maritime Cyber Risk Management in Safety Management Systems* (IMO,
tier-1, GLOBAL maritime/shipping) with the operational guidance from
*MSC-FAL.1/Circ.3 Rev.2 — Guidelines on Maritime Cyber Risk
Management* (2022) and the new-build equipment-level requirements
from *IACS UR E26 — Cyber Resilience of Ships* (Rev.4 2024) and
*IACS UR E27 — Cyber Resilience of On-board Systems and Equipment*
(Rev.3 2024), reading alongside the *BIMCO Guidelines on Cyber
Security Onboard Ships* (v5, 2025). The regulation lands with an
auditor-grade evidence pack and the catalogue tier-1 count rises to
15 frameworks.

- **IMO MSC.428(98) framework registered in `data/regulations.json`**
  with the maritime clause grammar covering the Resolution preamble
  paragraphs, MSC-FAL.1/Circ.3 Rev.2 §2.1–§2.4 (Identify / Protect /
  Detect / Respond / Recover), ISM Code §1.4 + §8.2 emergency-
  preparedness anchors, the seven cyber-vulnerable system categories
  from MSC-FAL.1/Circ.3 Rev.2 §3.1 (bridge / propulsion / cargo /
  communications / passenger and crew / administrative / access
  control), and the IACS UR E26 ship-level and UR E27 equipment-
  level cyber-resilience attestation registers — 18 monitored
  clauses.
- **17 hand-written gold-tier UCs** under the new `22.59` (IMO
  Maritime Cyber Risk Management) subcategory: DoC cyber-SMS
  verification (UC-22.59.1, UC-22.59.2), the seven cyber-vulnerable
  system categories from §3.1 (UC-22.59.3 through UC-22.59.12 —
  IT/OT segregation, ECDIS chart-update signatures, AIS / GMDSS /
  GNSS integrity, IBS configuration baseline drift, propulsion /
  DP / PMS anomaly, cargo control integrity, USB media governance,
  satcom governance, crew + passenger Wi-Fi segregation), the
  §2.4 Respond function (UC-22.59.13 24-hour multi-authority
  reporting clock — flag State + Recognised Organisation + USCG
  NRC + port-State Control under the nine regional MoUs;
  UC-22.59.14 annual cyber-drill cadence), UR E26 + UR E27
  attestation (UC-22.59.15 ship-level register; UC-22.59.16
  equipment-level register), and one cross-cutting audit-evidence
  retrieval ledger (UC-22.59.17). Every UC carries the full gold-
  tier payload (controlTest + parameterised SPL + controlObjective
  + evidenceArtifact + obligationRef + knownFalsePositives with
  suppression + detailedImplementation with KV-store schema + cron
  + runbook + maritime-specific notes + grandmaExplanation).
- **Auditor-facing evidence pack** at
  [`docs/evidence-packs/imo-msc-428-98.md`](docs/evidence-packs/imo-msc-428-98.md)
  + structured metadata in
  [`data/evidence-pack-extras.json`](data/evidence-pack-extras.json)
  covering the regulatory anatomy, the three-layer enforcement
  chain (flag State + RO + PSC under Paris / Tokyo / Vina del Mar /
  Caribbean / Mediterranean / Indian Ocean / Riyadh / Black Sea /
  Abuja MoUs), maritime-specific evidence patterns (IMO number
  canonical identifier, UTC vs ship-time canonicalisation, the
  24-hour multi-authority clock, IACS UR E26/E27 attestation), DoC-
  cycle 5-year retention + 2-year post-renewal, common audit
  deficiencies, enforcement + penalties (PSC detention, DoC
  suspension, class-society survey hold, P&I knock-on), and 18
  typical auditor questions cross-mapped to catalogue UCs.
- **Documentation wire-up** — cat-22 area entry in
  `non-technical-view.js` (between `fr-lpm` and `eu-ai-act`) with
  `whatItIs` / `whoItAffects` / `splunkValue` / `primer` /
  `evidencePack` + 3 representative UCs (22.59.3, 22.59.13,
  22.59.17); forward map in `docs-uc-map.js` from the evidence
  pack to nine representative UCs; full primer section
  `docs/regulatory-primer.md` §4.21 covering ISM + ISPS + SOLAS
  chain, port-State Control under the nine MoUs, IACS UR E26 /
  UR E27 new-build contract-date hooks, BIMCO v5 alignment, and
  convergence with adjacent regimes (NIS2 EU-flagged vessels,
  USCG MTSA / 33 CFR Part 105, Paris MoU 2023 CIC).
- **SPL parameter fix** — three cat-22 UCs (UC-22.59.4, UC-22.59.12,
  UC-22.53.13) had `summariesonly=true/false` rather than the
  Splunk-canonical `t/f`. `audit-spl-hallucinations` now reports
  **0 findings** across all 7,885 sidecars.

### Shipped outcomes

- Catalogue now ships **78 mapped regulations** (was 77) and
  **7,885 UCs** (was 7,868). Cat-22 alone gains 17 gold UCs in
  one new subcategory (22.59).
- Tier-1 framework count rises to **15**; auditor evidence pack
  count reaches **18**.
- IMO tier-1 coverage: **17/18 clauses (94.4%)** with 15 `full` +
  2 `partial` assurance. Only uncovered clause is
  `IMO-MSC-FAL-Circ-3-s3-2 Stakeholder and supply-chain
  considerations` — a procurement / GRC policy obligation
  explicitly outside the Splunk monitoring envelope.
- Global tier-1 coverage rises to **90.56%**, tier-2 to **97.55%**,
  tier-3 stays at **100%**.
- Phase 5a half-closed; the final 8.7.0 minor bump waits for
  Phase 5b (DO-326A / ED-202A — aviation airworthiness security,
  subcat 22.60, 17 UCs), then Phase 6 (China CII + CERT-In +
  IEC 61508/61511, subcats 22.61–22.63, 27 UCs) closes the
  6-phase, 247-UC arc.

See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.6.1 release
notes.

**v8.6.0 — OT Regulation Deep-Dive (Phase 4: TSA Surface + SG Cyber Act + France LPM)** *(shipped 2026-05-13)*

Theme: **Phase 4 of the multi-phase OT-regulation programme.**
v8.6.0 lands the *TSA Surface Cybersecurity Security Directives*
family — SD-Pipeline-2021-01/02 with all amendments A–G, SD-1580/82-2022-01
for freight and passenger rail, SD-1580-21-01 and SD-1582-21-01 for
passenger rail, and SD-1582-2022-01 for aviation — (US, tier-1,
pipeline/rail/aviation), the *Singapore Cybersecurity Act 2018* as
amended by Act 13 of 2024 (Singapore, tier-1, 11 CII sectors), and the
*France LPM (Loi de Programmation Militaire) OIV regime* across
LPM 2014-2019 + LPM 2019-2025 + Décret 2015-351 + Décret 2024-405
(France, tier-1, 12 critical sectors). All three regulations land
with auditor-grade evidence packs and the catalogue tier-1 count
rises to 14 frameworks.

- **TSA Surface framework registered in `data/regulations.json`** with
  the TSA Surface clause grammar covering the SD-Pipeline-2021-01
  (network security and reporting), SD-Pipeline-2021-02 (cybersecurity
  measures, CAP, CIP, governance) including amendments A–G, the
  SD-1580/82-2022-01 unified rail directive, the SD-1580-21-01 +
  SD-1582-21-01 passenger-rail directives, and the SD-1582-2022-01
  aviation directive — 46 monitored clauses across all four
  surface-transportation modes.
- **Singapore Cybersecurity Act 2018 framework registered in
  `data/regulations.json`** with the SG-CA clause grammar covering
  the CSA statutory sections (§7 designation, §10 Code of Practice
  binding force, §11 Cybersecurity Officer, §14(1) 2-hour prescribed-
  incident reporting, §14(2) material-change notification, §15(1)
  annual audit, §15(2) annual risk assessment, §16 cybersecurity
  exercises, §19 Commissioner's investigation), the CII Regulations
  2018, the CSA Code of Practice 2.0 topics, the 2024 ESCI / FDI /
  CTSP regulatory extensions, and the CSA-PDPA reconciliation — 24
  monitored clauses.
- **France LPM framework registered in `data/regulations.json`** with
  the LPM clause grammar covering the LPM 2014-2019 Article 22, the
  LPM 2019-2025 update, the Décret 2015-351 (SIIV designation + 20
  ANSSI cybersecurity rules), and the Décret 2024-405 (LPM → NIS2
  transposition) — 9 monitored clauses including the ANSSI 24-hour
  incident-reporting clock, the PSSI-MCAS audit, the PASSI external
  audit cycle, the ANSSI-qualified product procurement requirement,
  and the AIE zone-boundary surveillance regime.
- **51 hand-written gold-tier UCs** across the new `22.56` (TSA
  Surface — 28 UCs), `22.57` (SG Cyber Act — 15 UCs), and `22.58`
  (France LPM — 8 UCs) subcategories. Every UC starts at Gold
  quality with curated `equipmentModels[]` for the US surface-
  transportation stack (ServiceNow CMDB, Microsoft AD, Cisco ISE for
  OT segmentation, Claroty / Dragos / Nozomi for pipeline and rail
  OT monitoring, OSIsoft PI for SCADA telemetry, Splunk SOAR<sup class="ref">[<a href="#ref-7">7</a>]</sup> for
  CISA submission, ServiceNow Records Management for the TSA 5-year
  retention regime, CyberArk PSM / BeyondTrust for vendor remote
  access, Tenable / Qualys for vulnerability scoring), the Singapore
  CSA CII stack, and the French OIV stack with PSSI-MCAS / PASSI /
  ANSSI-qualified-product alignment.
- **Three new auditor evidence packs** at
  [`docs/evidence-packs/tsa-surface.md`](docs/evidence-packs/tsa-surface.md),
  [`docs/evidence-packs/sg-cyber-act.md`](docs/evidence-packs/sg-cyber-act.md),
  and [`docs/evidence-packs/fr-lpm.md`](docs/evidence-packs/fr-lpm.md)
  with high clause coverage, in-jurisdiction reporting-workflow
  guidance (CISA Services Portal 24-hour clock with dual PHMSA pipeline
  reporting for TSA; CSA SingCERT 2-hour clock for Singapore;
  ANSSI 24-hour notification + national-CSIRT coordination for
  France), and the Cybersecurity Assessment Plan (CAP) +
  Cybersecurity Implementation Plan (CIP) lifecycle for TSA.
- **Catalogue-wide schema-compliance ratchet — 7,868 UC sidecars
  now strictly validate against `schemas/uc.schema.json` v1.7.0.**
  The `audit-compliance-mappings` audit was promoted from
  "tolerate baselined errors" to "zero blocking errors." Global
  clause-coverage rose from 68.6 % to 92.9 %, and priority-weighted
  coverage from 68.9 % to 93.1 %. The ratchet normalised
  `controlFamily`, `monitoringType[]`, `owner`,
  `splunkbaseApps[].role`, and `compliance[].mode` across 164
  Phase 1–4 OT regulation UCs, and normalised
  `compliance[].regulation` from human-readable aliases to canonical
  lowercase IDs across 1,488 UCs (closing a long-standing gap where
  regulations like SOCI showed 0 covering UCs in the API surface
  even though their UCs were correctly mapped via aliases).
- **New API endpoints** at
  `api/v1/compliance/regulations/tsa-surface.json`,
  `api/v1/compliance/regulations/sg-cyber-act.json`,
  `api/v1/compliance/regulations/fr-lpm.json` (plus versioned
  aliases), and the corresponding evidence-pack endpoints. The
  `generate-evidence-packs` generator's `PACK_TARGETS` allow-list
  now lists 17 frameworks.

See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.6.0 release notes.

### Shipped outcomes

- Catalogue now ships **77 mapped regulations** (was 74) and
  **7,868 UCs** (was 7,817). Cat-22 alone gains 51 gold UCs and
  three new subcategories (22.56 + 22.57 + 22.58).
- Tier-1 framework count rises to **14**; auditor evidence pack
  count reaches **17**.
- Phase 4 of the multi-phase OT-regulation roadmap closed;
  Phases 5–6 (IMO 2021 MSC.428(98) + DO-326A / ED-202A, China
  CII + CERT-In + IEC 61508/61511) follow on the same release
  cadence and close the 6-phase, 247-UC arc.

---

**v8.5.0 — OT Regulation Deep-Dive (Phase 3: CIRCIA + CLC/TS 50701)** *(shipped 2026-05-13)*

Theme: **Phase 3 of the multi-phase OT-regulation programme.**
v8.5.0 lands the *Cyber Incident Reporting for Critical
Infrastructure Act of 2022* codified at 6 U.S.C. § 681 et seq. with
the CISA April-2024 NPRM (US, tier-1, cross-sector) and
*CLC/TS 50701:2021 — Railway applications - Cybersecurity*
(EU/EEA/UK/CH, tier-1, rail). Both regulations landed with 100 %
clause coverage, 28 gold-tier UCs each, and auditor-grade evidence
packs. Subcategories `22.54` (CIRCIA) and `22.55` (CLC/TS 50701)
bring the cat-22 OT-regulation arc to five phases shipped of six
planned.
See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.5.0 release notes.

**v8.4.0 — OT Regulation Deep-Dive (Phase 2: SOCI Act + AWIA)** *(shipped 2026-05-13)*

Theme: **Phase 2 of the multi-phase OT-regulation programme.**
v8.4.0 lands the *Security of Critical Infrastructure Act 2018 (Cth)*
with the 2022 SLACIP amendments and the 2023 CIRMP Rules (Australia,
tier-1) and Section 2013 of *America's Water Infrastructure Act of
2018* with the EPA Top Actions and CISA Pathway for the water sector
(US, tier-2). Both regulations landed with 100 % clause coverage, 28
gold-tier UCs each, and auditor-grade evidence packs. Subcategories
`22.52` (SOCI) and `22.53` (AWIA) bring the cat-22 OT-regulation
arc to four phases shipped of six planned.
See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.4.0 release notes.

**v8.3.0 — OT Regulation Deep-Dive (Phase 1: NCA OTCC)** *(shipped 2026-05-13)*

Theme: **first instalment of the multi-phase OT-regulation programme.**
v8.3.0 lands Saudi Arabia's National Cybersecurity Authority
*Operational Technology Cybersecurity Controls* (NCA OTCC, version
1:2022) as the catalogue's 70th regulation and the first tier-2
deep-dive aimed squarely at industrial control system operators. The
new `22.51` subcategory carries 28 hand-written gold-tier UCs and a
new auditor evidence pack at
[`docs/evidence-packs/nca-otcc.md`](docs/evidence-packs/nca-otcc.md);
the primer deep-dive at `docs/regulatory-primer.md §4.13` walks the
Domain → Subdomain → Main Control → Sub-Control grammar.
See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.3.0 release notes.



**v8.2.0 — Scripts Taxonomy Closed** *(shipped 2026-05-11)*

Theme: **`scripts/` is no longer the canonical entry point.** v8.2.0
closes the Phase 6 "scripts taxonomy" rebuild — every recurring script
under `scripts/` previously had a sibling implementation under
`src/splunk_uc/` plus a thin compatibility shim. With the dispatcher
exercised continuously by CI, the shims are now retired and the
package is the single Python surface.

- **`python -m splunk_uc <verb>`** is the single dispatcher for 83
  audits / generators / ingestors / migrations / feasibility tools /
  utilities. The 85 sibling shims under `scripts/` were deleted in
  one pass.
- **`splunk-uc` console script** wired via `pyproject.toml`
  (`[project.scripts]`); `pip install -e .` exposes the CLI globally.
  Tier 4 packaging shape lives at
  `[tool.hatch.build.targets.wheel].packages = ["src/splunk_uc"]`.
- **128 callers rewired in one pass** — workflows, Makefile,
  pre-commit hook, MCP server, tests, docs, templates,
  `AGENTS.md` / `README.md` / `CONTRIBUTING.md`.
- **76 deliberate Python files** remain in `scripts/` — underscore-
  prefixed one-shots, content-burndown helpers, gitignored Splunk-
  deployment generators, doc generators. All catalogued in
  [`docs/scripts-taxonomy.md`](docs/scripts-taxonomy.md).
- **F1 / F2 / F3 / F4 / F6 / F7 / F9 / F11 / F15** from the
  [`Repo Health Check plan`](docs/health-check-2026-progress.md) all
  resolved at v8.2.0 (with F7 closed 2026-05-12).

See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.2.0 release notes
and the v8.0 → v8.2 line.

**v7.1 — Non-Technical Everywhere** *(shipped 2026-04-20)*

Theme: **"every use case is explainable without jargon, everywhere, in
one sentence."** v7.1 extends v7.0's per-UC content architecture with a
first-class plain-language summary on every UC and a wholesale rewrite
of the non-technical UI so that toggle hides *all* technical chrome
behind a single disclosure.

- New required-at-runtime `grandmaExplanation` field on every UC
  sidecar (schema v1.6.1, 20–400 chars, `we` voice, no Splunk/SPL/CIM/
  MITRE/TA acronyms) — populated deterministically by
  `python3 -m splunk_uc generate-grandma-explanations` from the
  existing title/description/value copy
- Non-technical view now renders `grandmaExplanation` as the primary
  UC text on UC cards, search results, subcategory lists, recently-added,
  and at the top of the UC detail panel; technical sections (SPL, CIM,
  MITRE, data sources, etc.) collapse behind a single *Show technical
  details* disclosure that follows the mode toggle
- CI guard: `python3 -m splunk_uc generate-grandma-explanations --check`
  runs on every PR and blocks merge if any UC sidecar is missing the
  field
- Authoring and maintenance guide at
  [`docs/grandma-explanations.md`](docs/grandma-explanations.md); full
  narrative in [`docs/v7.1-release-report.md`](docs/v7.1-release-report.md)

**v7.0 — Per-UC Content Architecture** *(shipped 2026-04-19)*

Theme: **"every use case is its own file, every build is reproducible,
every URL is permanent."**  v7.0 replaced the monolithic per-category
markdown sources with individually authored per-UC file pairs and
introduced the current Python stdlib-only build pipeline (`tools/build/build.py`, `make build`).

- 23 monolithic `cat-*.md` files exploded into 6,449 individual
  `content/cat-NN-slug/UC-X.Y.Z.md` prose files paired with 6,470
  `UC-X.Y.Z.json` structured-metadata sidecars
- New build pipeline (`tools/build/build.py`) — single Python 3.12
  entrypoint, no Node/npm, reproducible builds with Sigstore attestation
- Extracted source assets (`src/styles/`, `src/scripts/`) with content-hash
  fingerprinting and immutable cache headers
- Sharded full-text search (16 MiniSearch shards, ~100 KB each) replacing
  the legacy linear scan over a single giant `data.js` payload
- CI quality gates (`tools/audits/`) — asset drift, bundle budgets,
  schema-diff, schema-meta, URL-freeze
- New schemas (`schemas/v2/`) — `catalog-index` and `search-index`
- Architecture contract (`docs/architecture.md`), URL scheme
  (`docs/url-scheme.md`), schema versioning (`docs/schema-versioning.md`)
- The catalog counted **7,364** UCs across 23 categories at v7.0 ship *(see [`CHANGELOG.md`](CHANGELOG.md); current count at HEAD is 7,677 — see the v8.2.0 entry above)*

### v6.x — monolithic markdown pipeline *(historical)*

The v6 line used per-category markdown under `use-cases/` and the root `build.py` workflow. It is **retired** in favour of **`content/` + `tools/build/build.py`** above.

**v6.1 — Verifiable Compliance Coverage** *(shipped 2026-04-16)*

- Six-phase regulation-coverage gap closure; 100% clause coverage on
  tier-1 + tier-2 frameworks
- Phase 5.5 structured equipment tagging on every cat-22 UC
- Phase 6 MCP server (`splunk-uc-mcp`) with eight read-only tools
- Regulatory primer reader (`regulatory-primer.html`)
- Branding updated to "Community Reference"
- Catalogue grew 6,424 → 6,447 UCs

**v6.0 — Verifiable Quality** *(shipped 2026-04-16)*

Theme: **"trust but verify"** — every shipped SPL should be demonstrably
correct and every quality signal transparently measured.

- Sample-event fixtures ([`samples/`](samples/)) with JSON-Schema-validated
  manifests — 15 golden fixtures at launch, expanding throughout v6.x
- UC test harness ([`scripts/run_uc_tests.py`](scripts/run_uc_tests.py))
  ingests samples via HEC, runs each UC's SPL in an ephemeral Splunk 9.4
  container, asserts on results, emits JUnit XML
- End-to-end CI workflow ([`.github/workflows/uc-tests.yml`](.github/workflows/uc-tests.yml))
- Splunk Cloud compatibility audit — see
  [`docs/splunk-cloud-compat.md`](docs/splunk-cloud-compat.md) for the
  rolling report (0 pack-level findings, 5 SPL-level warnings)
- Provenance ledger — 9-way source classification on every UC, rendered as
  a colour-coded dashboard badge (see
  [`docs/provenance-coverage.md`](docs/provenance-coverage.md))
- Quality scorecard — per-category Gold/Silver/Bronze letter grades across
  six quality dimensions (see [`docs/scorecard.md`](docs/scorecard.md))
- Two new API endpoints: `GET /provenance.json`, `GET /scorecard.json`
- OpenAPI spec bumped to 6.0.0

**v5.2 — Enterprise Packaging** *(shipped 2026-04-16)*

- Three Splunkbase-ready content packs: TA, ITSI, ES
- OpenAPI 3.1 spec + Swagger UI (self-hosted)
- Automated release workflow (`.github/workflows/release.yml`)
- Enterprise deployment guide
- Cross-cutting governance scaffolding (this document, `GOVERNANCE.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CODEOWNERS`, PR/issue templates,
  `CITATION.cff`)

**v5.1 — Gold Standard Quality Pass** *(shipped 2026-04-16)*

- 100 % references coverage across 6,304 UCs
- 100 % KFP coverage on security categories
- MITRE ATT&CK<sup class="ref">[<a href="#ref-4">4</a>]</sup> coverage ≥80 % on security categories
- Weekly link-check workflow
- Per-UC quality metadata chips (Status, Last reviewed, Splunk versions)

See [`CHANGELOG.md`](CHANGELOG.md) for full release notes.

---

## Next up: v8.3 — Gold Standard content uplift continues *(in progress)*

> The Gold Standard infrastructure shipped progressively over v7.2 →
> v7.4.x → v8.0; the *content* uplift itself is a continuous program
> that runs in parallel with platform work. Current distribution as of
> 2026-05-12: 724 Gold (9.4%) / 38 Silver (0.5%) / 6,106 Bronze (79.5%)
> / 809 below profile (10.5%) across 7,677 UCs. The goal is to grow
> Gold and Silver year-over-year while keeping the non-blocking
> summary gate visible in CI (see `audit-gold-profile --summary` in
> `validate.yml`). The platform infrastructure side of v8.3 is the
> [Repo Health Check plan](docs/health-check-2026-progress.md) work,
> tracked separately; this section covers the content side.

With the v7.0 per-UC architecture and the v7.1 non-technical rewrite in
place, **this program elevates content quality across the entire catalog**
to match the standard set by the Catalyst Center subcategory (5.13). The guiding
principle: *quality is operational utility, not field-count compliance;
fewer excellent UCs beat many shallow ones.*

### Gold Standard initiative

The Gold Standard defines tiered quality profiles (Gold / Silver / Bronze)
based on **operational completeness** — can someone implement a UC end-to-end
from this page alone?

Infrastructure shipped:
- **Quality profile schema** (`schemas/uc-profile-gold.json`) — tiered
  requirements emphasizing depth and product-specific detail
- **Template guide** (`docs/gold-standard-template.md`) — the quality
  contract: 5-step structure, anti-patterns, exemplar UC-5.13.1
- **Cursor authoring rule** (`.cursor/rules/gold-standard-authoring.mdc`) —
  AI authoring contract guiding agents to product-specific depth, not
  template filling
- **Depth audit** (`python3 -m splunk_uc audit-gold-profile`) — quality gate measuring
  substance, detecting shallow boilerplate and consolidation candidates
- **Build-time quality scores** — per-UC depth score and tier with actionable
  gap descriptions injected by `parse_content.py`, aggregated per subcategory
- **UI quality indicators** — depth badges on UC cards, quality progress bars
  on subcategory cards, quality gaps in the detail panel, category quality
  summaries, and a dedicated Quality review tab
- **Scorecard integration** — content depth is now a 20% weighted dimension
  in `generate_scorecard.py`
- **Markdown generation** (`python3 -m splunk_uc generate-md-from-json`) — JSON is the
  single source of truth; companion `.md` under `content/`, when present, is optional

### Content uplift workflow

Each subcategory is uplifted via Cursor agent sessions, branch per
subcategory, human review via PR:

1. Agent reads subcategory context and assesses holistically
2. Agent consolidates redundant UCs and deepens remaining ones
3. `audit_gold_profile.py` validates depth and flags gaps
4. PR review ensures product knowledge accuracy

### Ongoing content-uplift targets

- **Top-200 sample-event coverage** — Expand the `samples/` tree from 15
  fixtures to 200, targeting the most-used UCs identified by dashboard
  analytics. Goal: every Quick-Start UC has an authoritative fixture.
- **Scorecard targets** — Push at least 5 categories into **Silver** and
  push the current 3 Silver categories into **Gold** by backfilling KFP,
  MITRE mappings, reviewed-dates and sample coverage.
- **Test-harness scale** — Parallelize `run_uc_tests.py` and cache
  Splunk Docker images to keep the full-suite CI run under 15 minutes
  as fixture count grows.
- **Provenance refinement** — Drive the 2.4 % "unclassified" bucket below
  1 % by extending the host-rule allow-list and adding a heuristic
  fallback that inspects URL path/title.
- **Phase E SME-uplift continuation** — Walk the remaining tier-1 +
  tier-2 clause coverage entries from `assurance: contributing` to
  `partial` / `full` via SME judgment.  Phase E v6.1 lifted global
  assurance-adjusted coverage to 59.89 %; the current target is
  ≥75 % tier-1 / ≥55 % tier-2 without artificial uplift.
- **`grandmaExplanation` hand-polish pass** — Deterministic generator
  text is "good enough to ship"; the curator review loop raises
  quality (voice, warmth, concreteness) on the 500 most-viewed UCs
  without regenerating the rest.

---

## v8.4+ backlog *(no fixed date)*

The following ideas are under consideration but not yet scheduled. Pull
requests or issues advocating for any of them are welcome.

### Content

- **Industry-specific bundles** — Standalone content packs for Finance, OT,
  Healthcare, Public Sector (subset of existing UCs plus industry-specific
  framework mappings).
- **Cloud-provider deep dives** — Expand cat-4 with dedicated subcategories
  per provider (AWS/Azure/GCP) at the same depth as cat-10.
- **AI / LLM observability** — Dedicated subcategory under cat-13 covering
  prompt injection, token-cost monitoring, RAG retrieval quality, drift
  detection.
- **OCSF parity** — Second set of normalised SPL that produces OCSF-format
  output alongside the existing CIM-format queries.

### Tooling

- **CLI** — `pip install splunk-monitoring-use-cases` giving a `suc` CLI to
  query the catalog locally, export UC subsets, generate custom TAs for a
  specific category.
- **Terraform provider** — Declarative UC management for customers that manage
  Splunk via IaC.
- **VS Code extension** — Autocomplete for UC IDs, hover for UC summaries,
  quick-insert of SPL snippets into `.spl` or SPL scratch files.
- **MCP server (`splunk-uc-mcp`) — follow-ups after Phase 6.** Publish
  `splunk-uc-mcp` to PyPI (currently installed from source via
  `pip install -e mcp/`), add HTTP streaming transport as an opt-in for
  remote single-tenant deployments (stdio stays the default and the
  recommended mode per CoSAI guidance), expose a `list_mitre_techniques`
  tool (currently only filterable, not enumerable), add a
  `subscribe_use_cases` streaming resource so long-running agent sessions
  can be notified of new catalogue commits, and wire structured prompts
  (MCP `prompts/`) for the two canonical personas (compliance officer,
  detection engineer).

### Community & process

- **Translations** — `custom-text.js` is designed to allow UI translation;
  pilot translation to one additional language (likely Norwegian or German).
- **Contribution gamification** — Recognize top contributors per quarter in
  release notes; badges on the dashboard.
- **Monthly community call** — Public 30-minute call to review the roadmap,
  discuss RFCs, and onboard new contributors.

---

## Deprecated / declined ideas

Some things we have *decided not* to build. Each entry is linked to the issue
or discussion where the decision was made (once those exist).

- **Hosted SaaS** — The project stays static-site-first. Anyone can fork and
  host; we won't run infrastructure.
- **Commercial edition** — No paid tier, no premium content pack. Everything
  in the project is MIT-licensed.
- **Generated SPL by LLM** — We accept AI-assisted *authoring* via pull
  requests that are reviewed by humans, but we will not auto-publish LLM
  output to the catalog.

---

## How to influence the roadmap

- **Vote** with 👍 on existing issues.
- **Propose** new items by opening an issue with the `enhancement` label.
- **Advocate** for a backlog item by picking it up — maintainers prioritize
  items with active contributors.

See [`GOVERNANCE.md`](GOVERNANCE.md) for the full decision-making process.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-3"></a>**[3]** International Electrotechnical Commission. (2018). *IEC 62443 — Industrial communication networks — Network and system security*. IEC. https://webstore.iec.ch/en/publication/7029

<a id="ref-4"></a>**[4]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-5"></a>**[5]** North American Electric Reliability Corporation. (2024). *NERC Critical Infrastructure Protection (CIP) Reliability Standards*. NERC. https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk SOAR (Cloud) Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SOARonprem

<a id="ref-8"></a>**[8]** Standing Committee of the National People's Congress (China). (2021). *Personal Information Protection Law of the People's Republic of China*. National People's Congress. http://en.npc.gov.cn.cdurl.cn/2021-12/29/c_694559.htm

### Related repository documents

- [`docs/health-check-2026-progress.md`](docs/health-check-2026-progress.md)

### Cited by

- [`docs/enterprise-deployment.md`](docs/enterprise-deployment.md)

<!-- END-AUTOGENERATED-SOURCES -->
