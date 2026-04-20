# Plain-language explanations (`grandmaExplanation`)

> **Status:** shipped v7.1 (2026-04-20) · **Schema:** `uc.schema.json` v1.5.0 · **Writer:** [`scripts/generate_grandma_explanations.py`](../scripts/generate_grandma_explanations.py) · **CI guard:** `generate_grandma_explanations.py --check`

Every use case in the catalogue carries a short, jargon-free "explain it
to my grandma" sentence in the sidecar field `grandmaExplanation`
(short key `ge` in `catalog.json` / `data.js`). This is the **primary
text rendered throughout the non-technical view** — UC cards, search
results, subcategory lists, recently-added, and the very top of the UC
detail panel.

If you are only reading use cases, you can stop here: the non-technical
toggle is in the header and does the rest.

---

## Why this field exists

Before v7.1, the non-technical view leaned on:

1. The technical `description` / `value` copy (which mentions *tstats*,
   *CIM*, *MITRE T1078*, *add-on*, *index*, …).
2. A curated `why` line in `non-technical-view.js` that covered only
   ~621 of 6,472 UCs (~10 %).

Users who flipped to non-technical mode still saw Splunk acronyms on
90 % of UCs the moment they clicked into one. v7.1 fixes that by giving
every UC a first-class plain-language summary that's generated once from
the existing curated copy and then curator-polishable.

---

## Authoring contract

| Property       | Rule                                                                                                                                                                    |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Length**     | 20–400 characters (schema-enforced; hard-fails the build if violated).                                                                                                  |
| **Sentences**  | 1–3 short sentences. Read-aloud test: can a non-technical reader say it in one breath?                                                                                  |
| **Voice**      | First-person plural (`we watch…`, `we catch…`, `we help you know when…`). Never "this use case" / "this detection".                                                     |
| **Forbidden**  | Splunk / SPL / CIM / MITRE / ATT&CK / TA / add-on / index / sourcetype / tstats / datamodel / regulation clause numbers (e.g. "Art. 32", "NIS2 Art. 21(2)(d)").         |
| **Allowed**    | Everyday technology nouns users already know: *server*, *laptop*, *login*, *email*, *password*, *backup*, *switch*, *camera*, *factory floor*.                          |
| **Tone**       | Warm, plain, helpful. Avoid fear-mongering; explain *what we watch* and *why anyone should care*, not *what attackers do*.                                              |
| **Specificity**| Keep it concrete. "We watch your Linux servers and tell you when one is running out of disk." beats "We watch systems and detect problems."                             |

### Good examples

> We watch every Windows laptop and server for sudden bursts of failed
> sign-ins — the kind an attacker would try when guessing passwords —
> and tell you in time to lock things down before anyone gets in.

> We keep an eye on the factory floor controllers and flag the moment
> one stops talking, so the line doesn't sit idle while nobody notices.

> We tell you when a new admin account appears out of hours or from an
> unusual place, so you can confirm it was really you who created it.

### Not-great examples

> ❌ "This UC uses tstats over the Authentication datamodel to detect
>    anomalous logon volume per host."  (acronyms, passive voice)
>
> ❌ "Covers DORA Art. 9(4)(b) ICT risk management."  (clause number)
>
> ❌ "Monitors systems."  (too short, no specificity)

---

## Where it lives

1. **UC sidecar** — the source of truth:

   ```jsonc
   // content/cat-01-server-compute/UC-1.1.1.json
   {
     "id": "UC-1.1.1",
     "title": "Disk full on Linux server",
     "grandmaExplanation": "We watch every Linux server's disks and warn you before one fills up, so the server doesn't stop working in the middle of the night."
   }
   ```

2. **`catalog.json` / `data.js`** — emitted under the short key `ge`
   by `build.py`. Markdown-only UCs (no sidecar yet) receive a
   runtime fallback composed from `title` / `value` / `description` so
   the UI never shows an empty non-technical card.

3. **UI (non-technical mode)** — rendered:
   - at the top of every UC card (`.uc-card-ge`)
   - at the top of the UC detail panel (`.c-panel-ge`), above a
     collapsed *Show technical details* disclosure
   - inside search results, the "recently added" strip, and the
     subcategory area lists that replace technical category views
     when the toggle is on

4. **Technical mode** — hidden. Technical readers keep the full panel
   with SPL, CIM, MITRE, etc. open by default.

---

## How it's generated

`scripts/generate_grandma_explanations.py` is the **sole writer** of
this field. It is deterministic (byte-for-byte identical output on
re-runs at the same catalogue state) and curator-respecting (existing
non-empty values are never touched unless `--force` is passed).

### Common invocations

```bash
# Fill missing values for every UC (default)
python3 scripts/generate_grandma_explanations.py

# CI drift guard — exit 1 on any missing value, no writes
python3 scripts/generate_grandma_explanations.py --check

# Regenerate one UC (after editing its title/description/value)
python3 scripts/generate_grandma_explanations.py --only 1.1.1

# Regenerate a whole category
python3 scripts/generate_grandma_explanations.py --category 22

# Show what would change without writing
python3 scripts/generate_grandma_explanations.py --dry-run

# Overwrite curator edits (rare — only when tone rules change)
python3 scripts/generate_grandma_explanations.py --force

# Per-UC status report
python3 scripts/generate_grandma_explanations.py --report
```

### What the generator does, in one paragraph

It reads each UC sidecar, drops code fences / inline code / markdown
links / regulation clause numbers / Splunk and security acronyms from
the `description` and `value` copy, rewrites the remaining first
sentence into `we` voice, and — when there's room under the 400-char
cap — appends a short "because …" clause pulled from `value`. If the
composed text would violate the 20–400 char bounds, it falls back to a
short safe sentence built from the UC `title` and the parent category
name.

---

## Hand-polishing

The generator is "good enough to ship" but curators are encouraged to
improve any UC by hand:

1. Open `content/cat-NN-slug/UC-X.Y.Z.json`.
2. Edit the `grandmaExplanation` string, keeping inside 20–400 chars.
3. Commit. CI will not regenerate on top of your edit — the generator
   only touches empty/missing values unless you pass `--force`.

If you believe the generator rules themselves need a change (e.g. you
keep seeing an acronym slip through), open a PR against the drop-list
in `scripts/generate_grandma_explanations.py` rather than hand-fixing
hundreds of UCs.

---

## CI guard

`.github/workflows/validate.yml` runs:

```bash
python3 scripts/generate_grandma_explanations.py --check
```

on every PR that touches use-case content. It exits non-zero — and
blocks merge — if any UC sidecar is missing, empty, or out-of-bounds
for the `grandmaExplanation` field. Contributors who add a new UC or
meaningfully edit an existing UC's `title` / `description` / `value`
should run the generator locally before pushing.

---

## Schema reference

Defined in [`schemas/uc.schema.json`](../schemas/uc.schema.json) (v1.5.0):

```jsonc
"grandmaExplanation": {
  "type": "string",
  "minLength": 20,
  "maxLength": 400,
  "description": "Plain, jargon-free, 'explain it to my grandma' summary …"
}
```

See [`schemas/changelogs/uc.md`](../schemas/changelogs/uc.md) for the
schema bump note.

---

## Further reading

- [`docs/use-case-fields.md`](use-case-fields.md) — full UC field reference (markdown keys)
- [`docs/catalog-schema.md`](catalog-schema.md) — `catalog.json` / `data.js` short keys
- [`docs/v7.1-release-report.md`](v7.1-release-report.md) — full narrative release report
- [`.cursor/rules/non-technical-sync.mdc`](../.cursor/rules/non-technical-sync.mdc) — content synchronization contract for the non-technical view
