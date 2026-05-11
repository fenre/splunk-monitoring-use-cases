# Recruitment messaging & channel plan

> **Status:** Phase 0.1 draft, produced 2026-04-16.
> **Purpose:** the words we use and the channels we use to reach auditors,
> QSAs, DPOs, ISMS leads, SOC-2 practitioners and ITGC/SOX<sup class="ref">[<a href="#ref-6">6</a>]</sup> auditors for the
> interview and survey described in
> `docs/auditor-research/interview-guide.md` and
> `docs/auditor-research/survey.md`.
> **Ethical bar:** no cold LinkedIn spam, no dark patterns, no incentives
> that bias results. All outreach discloses that the catalogue is open-source
> and that responses are aggregated and anonymised before publication.

---

## 1. Target personas and recruitment channels

| Persona | Primary channel | Secondary channel | Target count |
|---|---|---|---|
| Internal SIEM / compliance engineer | Splunk Trust Slack/forum post | SplunkBase app reviewers | 10 |
| QSA (PCI-DSS) | PCI SSC QSA list + personal network of QSAs who have published blogs | A2LA-listed QSA firms | 5 |
| DPO / privacy officer | IAPP community board + national DPO associations (e.g. German BVD, UK DPN) | LinkedIn Privacy Engineering groups | 5 |
| SOC-2 practitioner (CPA) | AICPA SOC-2 community + r/soc2 subreddit | Linkedin #SOC2 audience | 5 |
| ISMS lead auditor | ISO TC-272, BSI / DNV / SGS / TÜV practitioner LinkedIn | UKAS / DakkS certified bodies | 5 |
| SOX ITGC external auditor | PCAOB-registered firm alumni networks | LinkedIn #ITGC and #SOX audiences | 4 |
| NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup> / DORA<sup class="ref">[<a href="#ref-3">3</a>]</sup> supervisor or consultant | ENISA working-group contacts (public channels only) | LinkedIn DORA / NIS2 groups | 3 |

Target total: 25–35 interviews, 80–120 survey responses.

---

## 2. Core messaging (all channels)

Every outreach uses the same four beats in this order:

1. **What the catalogue is.** "Open-source catalogue of Splunk monitoring
   use cases, under a permissive licence, not a vendor product."
2. **What we need.** "30-60 minutes of your honest feedback on whether
   our regulatory mappings are useful to *you*, not whether they're good."
3. **What's in it for you.** "Early access to the draft gold-standard
   schema + your influence on what the catalogue maps to first."
4. **How we protect you.** "No names, firms, or client data in anything we
   publish. Aggregated findings only. Drafts sent to you before release."

**Hard rules** (apply everywhere):

* No paid incentives. Even gift cards bias research.
* No name-dropping other respondents.
* No "I noticed you worked at X and…" personalisation — that's creepy.
* No "limited time" framing.
* Always include the open-source link.
* Always include opt-out language (single sentence).

---

## 3. Per-channel templates

### 3.1 Splunk Trust / SplunkBase forum post

**Title:** Looking for honest feedback on a public catalogue of Splunk
monitoring use cases (open-source, no vendor)

**Body:**

> Hi all — I maintain an open-source catalogue of Splunk monitoring use
> cases at https://github.com/fenre/splunk-monitoring-use-cases (MIT
> licensed, no vendor affiliation).
>
> I'm working on making the regulatory-compliance section genuinely useful
> for auditors and the engineers who work with them — precise clause-level
> mappings to GDPR<sup class="ref">[<a href="#ref-2">2</a>]</sup>, HIPAA<sup class="ref">[<a href="#ref-8">8</a>]</sup>, PCI-DSS, SOC-2, ISO 27001<sup class="ref">[<a href="#ref-4">4</a>]</sup>, SOX-ITGC, NIS2, DORA,
> etc., published as machine-readable OSCAL plus human-readable dashboards.
>
> If you've built, received or reviewed SIEM-based evidence packs for any
> of those, I'd love 30–60 minutes of your candid feedback. No pitch, no
> prep work, no incentive — just whether the mappings land or not.
>
> Book a slot: [short Cal/Calendly link — created in Phase 0.1].
> Or fill the 6-minute anonymous survey:
> [Google Form / MS Forms link — created in Phase 0.1].
>
> All answers are aggregated and anonymised before anything is published,
> and you'll get to review the draft before it goes out. Opt out any time.

### 3.2 LinkedIn post (personal feed)

> Short, one-paragraph version of 3.1. Must fit above the "see more" fold
> (~200 chars before the form link).
>
> Draft:
>
> "Open-source Splunk monitoring catalogue maintainer here. I'm making
> the regulatory-compliance section auditor-grade (clause-level OSCAL
> mappings). Looking for 30-60 min with auditors / DPOs / QSAs /
> ISMS leads / SOC-2 practitioners. No pitch, no incentive. Anonymous
> aggregated results only. Sign up: [link]. 6-min survey: [link]."

### 3.3 LinkedIn direct message (inbound only)

Only sent to people who liked / commented on 3.2 or reached out first.

> "Thanks for reacting — really appreciate it. Here's the interview
> booking link: [link]. I'll send the consent form and a one-pager about
> the catalogue as soon as you pick a slot. All responses anonymised;
> opt out any time."

### 3.4 IAPP / AICPA / ISO-community channels

Exact phrasing depends on the community's rules; each community moderator
must approve before posting. Use the 3.1 body, drop SplunkBase-specific
language, and add:

> "I'm aware this community typically requires moderator pre-approval
> for research requests — happy to send the research plan, consent form
> and a sample of the aggregated output before posting."

### 3.5 Partner consultancy outreach (Splunk partner firms)

Sent as a single-paragraph email from the maintainer's GitHub-linked
address to a named practice lead only. No mass mailings.

**Subject:** Open-source Splunk-compliance catalogue — auditor
interviews (30-60 min, anonymised)

**Body:**

> Hi [First name],
>
> I maintain an open-source catalogue of Splunk monitoring use cases at
> https://github.com/fenre/splunk-monitoring-use-cases. I'm working on
> making the regulatory-compliance section useful as primary evidence
> in PCI-DSS / SOC-2 / ISO / GDPR / HIPAA / SOX audits.
>
> If your firm has 1–2 practitioners who would be willing to give
> 30–60 minutes of honest feedback (not a sales call), I'd be grateful.
> No incentive, results published anonymised and aggregated only.
>
> Interview booking: [link]. Anonymous 6-minute survey: [link].
>
> Happy to share the research plan, the consent form and a draft of
> what we'll publish. Opt out any time.
>
> Thanks,
> [Maintainer name]
> [GitHub profile link]

### 3.6 Reddit / r/soc2, r/AskNetsec, r/ISO27001

Heavier moderator approval expected. Post only after reading the
subreddit's self-promo rules. Use the 3.1 body with an explicit tag in
the title (e.g. `[Research]`) and disclose self-interest.

### 3.7 NIS2 / DORA public working-group lists

**Do not** solicit supervisory authority staff directly on public lists.
Route via ENISA working-group coordinators. If declined, drop this
persona.

---

## 4. Disclosure & opt-out language (appended to every message)

> "This request is part of public research for an open-source catalogue.
> You can opt out at any point and your response will not be used.
> Responses are aggregated and anonymised before publication; no names,
> firms or clients are ever named. The full research plan is at
> docs/auditor-research/interview-guide.md. Any questions, reply here."

---

## 5. Recruitment tracker (spreadsheet schema)

Maintain locally, do not publish. Columns:

| column | purpose | retention |
|---|---|---|
| `date_reached` | date of first outreach | until +12 months |
| `channel` | one of: splunk-trust, linkedin-post, linkedin-dm, iapp, aicpa, iso-community, partner-email, reddit, enisa | until +12 months |
| `persona` | QSA / SOC-2 / DPO / ISMS / SOX / NIS2-DORA / internal-engineer / other | until +12 months |
| `status` | contacted / responded / interviewed / surveyed / declined | until +12 months |
| `interview_date` | when held | until +12 months |
| `notes` | free text, **no PII** | until +12 months |

No names, no email addresses, no firm names are recorded in this tracker —
use opaque IDs (e.g. `QSA-03`).

---

## 6. Success criteria

Phase 0.1 is complete when:

* **≥ 6 interviews completed** across at least **3 distinct personas**
  (hard floor; more is better).
* **≥ 40 survey responses** across at least **3 distinct personas**.
* Raw CSVs anonymised and stored according to the survey retention policy.
* Aggregated findings written to `docs/auditor-research/findings.md`.

If after 6 weeks we cannot hit the floor, the findings document is
published anyway with a clearly labelled "low-N" warning and Phase 1
decisions proceed with the available signal. A later Phase 2 re-run is
scheduled to close the gap.

---

## 7. Ethics checklist (maintainer completes before first outreach)

- [ ] Consent form reviewed and matches `interview-guide.md` §1.1.
- [ ] Survey hosting platform confirmed not to retain IP addresses.
- [ ] One-pager about the catalogue prepared and shareable.
- [ ] Cal/Calendly link scoped so it does not expose other bookings.
- [ ] Opt-out language present in every template.
- [ ] No incentives offered.
- [ ] No personal data stored in the recruitment tracker.
- [ ] Draft `findings.md` template prepared so respondents know the shape
      of what will be published about them.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-4"></a>**[4]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-5"></a>**[5]** Public Company Accounting Oversight Board. (2007). *Auditing Standard 2201 — An Audit of Internal Control Over Financial Reporting*. PCAOB. PCAOB AS 2201. https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

<a id="ref-6"></a>**[6]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-7"></a>**[7]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-8"></a>**[8]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<details>
<summary>Additional online sources cited in the document body (1)</summary>

<a id="ref-9"></a>**[9]** github.com. *GitHub: fenre/splunk-monitoring-use-cases*. Retrieved May 11, 2026, from https://github.com/fenre/splunk-monitoring-use-cases

</details>

<!-- END-AUTOGENERATED-SOURCES -->
