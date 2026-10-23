# Starter packs — guided onboarding

Starter packs answer one question for people who are new to Splunk:
*which use cases should I turn on first, in what order, for the data I
already have and the goal I care about?*

A pack is a short, ordered list of **existing** use cases for one data
source and one goal. Packs never carry their own SPL; the UC sidecar is
always the source of truth.

## Files

| File | Role |
| --- | --- |
| `data/starter-packs/<id>.json` | One curated pack (hand-authored) |
| `schemas/starter-pack.schema.json` | JSON Schema 2020-12 contract (`x-stability: preview`) |
| `schemas/changelogs/starter-pack.md` | Schema lifecycle log |
| `data/sourcetype-aliases.json` | Documented sourcetype renames (for example `WinEventLog` ↔ `XmlWinEventLog`) |
| `src/splunk_uc/audits/starter_packs.py` | `audit-starter-packs` |
| `src/splunk_uc/generators/starter_packs.py` | `generate-starter-packs` → `api/v1/starter-packs/` |

## Pack shape

| Field | Meaning |
| --- | --- |
| `id` | Stable kebab-case id; must match the file name. Permanent once published. |
| `goal` | `security` or `operations`. The wizard and `plan_rollout` only show packs whose goal matches the user's goal. |
| `status` | `draft` (hidden from end users) or `published`. |
| `pairId` | Sibling pack with the opposite goal for the same source, or `null`. |
| `equipment[]` | Inventory slugs (`windows`, `linux`, `splunk`) or model ids (`cisco_catalyst_center`, `cisco_thousandeyes`, `cisco_meraki`, `cisco_ise`, `paloalto_pan_firewall`). The wizard prefers packs whose equipment matches the user's inventory. |
| `requiredData` | Primary Splunkbase<sup class="ref">[<a href="#ref-4">4</a>]</sup> add-ons, the sourcetypes the steps search, internal indexes (`_internal`, `_audit`, …), and a `notes` string for licences, roles, or input settings that are not Splunk apps. |
| `industrySources[]` | `{url, control}` — the external list the steps were picked from. |
| `steps[]` | `{ucId, order}` only. At most 10. |
| `nextPacks[]` | Suggestions only. Mutual suggestions (A → B, B → A) are fine. |
| `curationNotes[]` | Optional reviewer notes about known gaps in packed UCs. |

## How steps are picked

1. Start from an industry list (vendor default alerts, Microsoft
   Appendix L, CIS, ThousandEyes<sup class="ref">[<a href="#ref-1">1</a>]</sup> default alert rules, …), recorded in
   `industrySources[]`.
2. Map each item to the nearest catalogue UC that runs on the default
   add-on or Splunk's own internal data.
3. Use catalogue `criticality` only as a tie-break.
4. Drop UCs that need products most users of that source do not have
   (MLTK, Sysmon, AIDE, ES-only content, custom collectors, extra vendor
   licences).
5. Cap at eight steps and order by blast radius.

Authored `difficulty` is shown on each step as a warning. It is never a
filter, and there is no computed difficulty.

### Pair rule

Every pack has a `goal`. A source gets a security pack **and** an
operations pack only when industry practice has a distinct list for each
goal and the catalogue has at least five packable UCs for each. Firewalls
and IDS are usually security-only. Do not create empty packs to complete
a pair. A UC may not appear in both packs of a pair.

## Audit

```bash
PYTHONPATH=src python3 -m splunk_uc audit-starter-packs --check
```

**Errors** (always fail CI): schema violations; `id` ≠ file name; unknown
`ucId`; duplicate steps or `order` not 1..n; unknown / non-reciprocal /
same-goal `pairId`; the same UC in both packs of a pair; a step placed
before one of its in-pack prerequisites; a step whose sourcetypes,
internal indexes, equipment, or required Splunkbase apps are not covered
by the pack `requiredData`; unknown or self-referencing `nextPacks`;
unknown equipment or Splunkbase apps; deprecated apps; a published pack
with a cat-25 UC; a published pack with any warning.

**Warnings** (only block `status: published`): step UC not
`status: verified`; below Silver depth; compliance rows tagged
`requires_sme_review`; a prerequisite that is in neither the pack nor its
pair.

Step data coverage is checked with the same sourcetype extractor that
builds `/api/v1/recommender/sourcetype-index.json`, plus literal
sourcetype mentions and `index=_internal`-style mentions for declared
internal indexes. Sourcetype comparisons are lowercase and use
`data/sourcetype-aliases.json`.

## API

```bash
PYTHONPATH=src python3 -m splunk_uc generate-starter-packs
PYTHONPATH=src python3 -m splunk_uc generate-starter-packs --check
```

| URL | Content |
| --- | --- |
| `/api/v1/starter-packs/index.json` | All packs (draft and published) with resolved steps, audit readiness, and the alias groups |
| `/api/v1/starter-packs/{id}.json` | One pack |

Each resolved step carries the UC title, criticality, authored difficulty,
wave, status, prerequisites, and the pack sourcetypes / internal indexes
the step searches. `readiness.publishable` is `true` only when the audit
reports no warnings or errors for the pack.

The `api/` tree is gitignored. `starter-packs` is listed in
`api_surface._EXTERNAL_SUBTREES`, so `generate-api-surface` leaves it
alone; `pages.yml` runs `generate-starter-packs` after
`generate-api-surface`. Inputs are only the pack files, UC sidecars, the
alias map, and `VERSION`, so `--check` is hermetic.

**Consumers must show only `status: published` packs by default.**

## Publishing a pack

1. Clear every audit warning for the pack (lift or verify the packed UCs,
   resolve SME review, fix out-of-pack prerequisites).
2. Set `"status": "published"`.
3. Run `audit-starter-packs --check` and `generate-starter-packs`.
4. Add a CHANGELOG entry. Published pack ids are permanent.

## First-wave packs

| Pack | Goal | Steps | Default data |
| --- | --- | --- | --- |
| `splunk-platform-ops` | operations | 8 | `_internal`, `_introspection` |
| `splunk-platform-security` | security | 5 | `_audit` |
| `windows-ops` | operations | 8 | Splunkbase 742 (Perfmon, System, Application) |
| `windows-security-basics` | security | 8 | Splunkbase 742 (Security log) |
| `linux-ops-basics` | operations | 8 | Splunkbase 833 (`cpu`, `vmstat`, `df`, syslog) |
| `linux-security-basics` | security | 8 | Splunkbase 833 (`linux_secure`, `rlog.sh`) |
| `catalyst-center-ops` | operations | 8 | Splunkbase 7538 (Assurance health + issues) |
| `catalyst-center-security` | security | 7 | Splunkbase 7538 (advisories, compliance, audit logs) |
| `thousandeyes-ops` | operations | 8 | Splunkbase 7719 (Tests Stream metrics, events) |
| `thousandeyes-security` | security | 5 | Splunkbase 7719 (BGP, DNSSEC, activity log) |

## Later-category packs

The pair rule was applied to each remaining source. "Packable" means the
UC searches a sourcetype the default add-on actually emits.

| Pack | Goal | Steps | Default data |
| --- | --- | --- | --- |
| `meraki-ops` | operations | 5 | Splunkbase 5580 (Dashboard API: availability, SD-WAN, uplink loss/latency, assurance alerts, licences) |
| `meraki-security` | security | 5 | Splunkbase 5580 (Dashboard API: audit, Air Marshal, devices) |
| `ise-ops` | operations | 5 | Splunkbase 1915 (`cisco:ise:syslog`, ISE system alarms) |
| `ise-security` | security | 5 | Splunkbase 1915 (`cisco:ise:syslog`, authentication and admin audit) |
| `paloalto-firewall-security` | security | 6 | Splunkbase 7523 (`pan:config`, `pan:system`, `pan:threat`) |

| Source | Decision | Why |
| --- | --- | --- |
| Meraki | Pair | Dashboard alerts split cleanly into device/uplink/licence health and admin/rogue-AP events; at least five UCs per goal on `meraki:*` API sourcetypes. UCs on the plain `meraki` syslog sourcetype are excluded. |
| Cisco ISE | Pair | The ISE alarm catalogue has distinct system-health alarms (Process Down, High Load Average, Replication Failed, CoA Failed) and security alarms (Excessive Failed Attempts, admin lockout, TACACS+ failures). |
| Palo Alto firewall | Security only | No distinct beginner ops list on the default add-on. `pan:url` and `pan:wildfire` UCs are excluded because the add-on files those events under `pan:threat`. |
| Cisco SD-WAN | No pack | Catalogue SD-WAN UCs search `cisco:sdwan:bfd`, `:device`, `:approute`, …; the Cisco Catalyst add-on emits `cisco:sdwan:sitehealth`, `:tunnelhealth`, `:linkhealth`, `:syslog`. Zero packable UCs, so no pack until the UCs are moved to those sourcetypes. |

All fifteen packs ship as `draft`. Each pack's `curationNotes[]` and the
audit warnings list what must be fixed before it can be published.
`ise-ops` already has no audit warnings and only needs curator sign-off.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Cisco ThousandEyes. (2026). *Cisco ThousandEyes Documentation*. Cisco Systems, Inc. Retrieved May 11, 2026, from https://docs.thousandeyes.com/

<a id="ref-2"></a>**[2]** Gerhards, R. (2009, March). *The Syslog Protocol*. Internet Engineering Task Force. RFC 5424. https://www.rfc-editor.org/rfc/rfc5424

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

<!-- END-AUTOGENERATED-SOURCES -->
