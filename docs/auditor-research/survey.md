# Anonymous evidence-pack preference survey

> **Status:** Phase 0.1 draft, produced 2026-04-16.
> **Purpose:** a short anonymous survey that captures evidence-pack
> preferences at scale, alongside the 1:1 interviews in
> `interview-guide.md`. Responses populate quantitative sections of
> `findings.md` and set priorities for Phase 1 evidence-pack generation.
> **Runtime:** target 6–8 minutes, 22 questions, single-page.
> **Platform note:** hostable as a Google Form / Microsoft Forms /
> Typeform / OSS equivalent — all questions are portable to a `.csv`
> for synthesis.

---

## Section A — About you (5 questions; no PII)

A1. Which of these best describes your role? (single choice)
  - Internal auditor (first / second line)
  - External auditor (Big 4 / national firm)
  - QSA (PCI-DSS)
  - DPO / privacy officer
  - SOC 2 practitioner (ISAE 3000 / SSAE 18)
  - ISMS / ISO 27001 lead auditor
  - Supervisory authority / regulator staff
  - SOX / PCAOB external auditor
  - GRC consultant / advisor
  - Other (please specify — free text, optional)

A2. Which frameworks do you currently work with? (multi-select)
  - SOC 2 (TSC 2017)
  - ISO/IEC 27001:2022
  - PCI-DSS v4.x
  - HIPAA Security Rule
  - HITRUST CSF
  - GDPR / UK-GDPR
  - SOX (PCAOB AS 2201) / ITGC
  - NIS2
  - DORA
  - NIST SP 800-53 Rev 5
  - NIST CSF 2.0
  - ISA/IEC 62443 (OT)
  - FedRAMP
  - CIS Controls v8
  - Other / national
  - None of the above

A3. Roughly how many assessments have you led or signed in the last
12 months? (single choice)
  - 0 – 2
  - 3 – 10
  - 11 – 30
  - 30+

A4. Do you work predominantly with… (single choice)
  - On-premise estates
  - Cloud-native (AWS / Azure / GCP)
  - Hybrid
  - OT / industrial

A5. Do you use any SIEM / log-management platform as a primary evidence
source? (single choice)
  - Yes — Splunk
  - Yes — other (please specify — free text, optional)
  - No

---

## Section B — Evidence-pack structure (6 questions)

B1. For a single control, what's the *minimum* set of artefacts you expect
an organisation to produce as evidence? (multi-select)
  - Natural-language description of the control
  - Reference to the policy / standard it implements
  - Reference to the regulatory clause(s) it maps to
  - Technical detection / SPL / rule definition
  - A screenshot or export of the dashboard
  - Raw log sample
  - Fixture / test data proving the detection fires
  - Audit trail of every time the control ran
  - Attestation / signature from a named control owner
  - Change history of the control itself (versioning)
  - None — any of the above is optional

B2. If you had to pick the *single* most important artefact from B1 for an
audit to go well, which would it be? (single choice — same list)

B3. Rank these evidence-pack formats from most to least useful:
(drag-to-rank, 5 items)
  - A single signed PDF containing screenshots and narrative
  - A ZIP with `*.json` metadata + `*.csv` data + screenshots
  - A link to a live dashboard + a time-stamped export
  - An OSCAL Component Definition + linked saved-search config
  - A Splunk `.spl` app bundle with README

B4. Which timestamp formats are acceptable to you as authoritative in
evidence? (multi-select)
  - ISO 8601 UTC with "Z" (2026-04-16T10:00:00Z)
  - ISO 8601 with offset (2026-04-16T10:00:00+02:00)
  - Local time with zone name (2026-04-16 10:00:00 CEST)
  - Epoch seconds
  - None of the above — I demand a specific format (please describe —
    free text, optional)

B5. How do you feel about evidence that is produced by a scheduled
SIEM / SOAR search rather than manually assembled? (single choice)
  - Preferred — it's more reliable
  - Acceptable with additional provenance
  - Acceptable only if the search definition itself is version-controlled
  - Unacceptable — evidence must be human-assembled

B6. How important is it that each piece of evidence is cryptographically
signed or otherwise tamper-evident? (1 = not at all; 5 = mandatory)

---

## Section C — Control mapping language (4 questions)

C1. "This control SATISFIES clause 10.2.1 of PCI-DSS."
Does that statement convey what you need? (1 = completely useless;
5 = exactly right)

C2. "This control DETECTS VIOLATIONS OF clause 10.2.1 of PCI-DSS."
How does this compare with "SATISFIES" in usefulness? (1 = much less
useful; 5 = much more useful)

C3. If a control provides *partial* coverage of a clause, which word
would you prefer to see? (single choice)
  - "partial"
  - "contributing"
  - "supports"
  - "helps to satisfy"
  - "compensating"
  - Other (free text)

C4. When a control maps to multiple regulatory clauses, how should
that be displayed? (single choice)
  - A flat list, one mapping per row
  - Grouped by regulation with an explicit assurance label per clause
  - A matrix view (controls × clauses)
  - Don't care — as long as the data is in the export

---

## Section D — Catalogue-specific questions (5 questions)

D1. Have you seen the Splunk Monitoring Use Cases catalogue before?
(yes / no / unsure)

D2. If yes, how did you use it? (free text, optional)

D3. Imagine a catalogue that produces, per use case, a downloadable
evidence pack containing the saved-search definition, dashboard
screenshot, fixture data, and an OSCAL Component Definition. How likely
would you be to accept that as primary evidence? (1 = definitely would
not; 5 = definitely would)

D4. Which of these would most increase your trust in the catalogue?
(multi-select, max 3)
  - Version control and diffs for every use case
  - Provenance stamp showing when the use case last ran in a real
    Splunk environment
  - Signature from a named reviewer (e.g. QSA / ISMS lead)
  - Alignment with NIST OLIR crosswalks for NIST 800-53 ↔ CSF
  - Mapping to MITRE ATT&CK techniques
  - Open-source under a permissive licence
  - Third-party audit of the catalogue itself

D5. What would you *not* want to see in such a catalogue? (free text,
optional)

---

## Section E — Free text & follow-up (2 questions)

E1. Is there anything you wish evidence packs routinely contained that
no product currently gives you? (free text, optional)

E2. Would you like to be contacted (anonymously) for a 45-minute
follow-up interview? (yes/no)
  - If yes, paste a throwaway contact (email alias, Matrix ID, etc.) —
    free text, optional, deleted after contact.

---

## Privacy, retention & aggregation

* Responses are stored **without IP addresses** by the survey host;
  where the host logs IPs, we immediately discard them on download.
* Free-text answers are scanned for accidental PII and redacted before
  publication.
* Aggregated findings will be published in
  `docs/auditor-research/findings.md` with **no individual response
  traceable**.
* Raw CSVs are retained for 12 months in an access-controlled location
  and then deleted.
* Respondents may ask for their response to be withdrawn at any time by
  citing the timestamp of submission (no contact info required).

---

## Synthesis checklist (run by maintainer after close)

- [ ] Export CSV, discard IP column, anonymise free text.
- [ ] Compute per-question distributions.
- [ ] Cross-tabulate Section B/C answers by persona (Section A1).
- [ ] Publish aggregated results to
      `docs/auditor-research/findings.md` under heading "Survey results".
- [ ] Delete raw CSV per retention policy (12 months from close).
