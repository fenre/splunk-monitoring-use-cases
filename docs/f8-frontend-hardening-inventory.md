# F8 frontend hardening inventory

> Single-page inventory of the `index.html` front-end sites flagged by **F8** in
> [docs/health-check-2026-progress.md](health-check-2026-progress.md). The goal
> of this doc is to turn the abstract `H` severity rating into a bounded,
> review-friendly migration plan: every `innerHTML` sink, what it actually
> writes, whether it touches untrusted input, and how to migrate it without
> breaking the build.
>
> Companion to [docs/ci-architecture.md](ci-architecture.md) and
> [docs/workflow-audit.md](workflow-audit.md) — same single-page format,
> same auditability contract: every claim has a line number, every line
> number resolves at HEAD.
>
> **Authored:** 2026-05-13 at HEAD `b3f0da75a` (post-PR #21 squash).
> The five raw numbers below were captured by `grep` / `wc -l` against the
> committed `index.html` at that head.

## TL;DR (the five F8 numbers, fresh)

| Metric | Plan baseline (2026-Q1) | HEAD (2026-05-13, `b3f0da75a`) | Delta |
|---|---|---|---|
| `index.html` raw size | 621 KB | **645 KB** (645,766 bytes) | +24 KB |
| `index.html` gzipped | 162 KB | **173 KB** (173,030 bytes) | +11 KB |
| `.innerHTML =` sinks | "33" | **29** | −4 |
| `'unsafe-inline'` in CSP | 1 | **1** (the meta tag — one comma-separated string lists `'unsafe-inline'` for *both* `script-src` and `style-src`; see §4) | unchanged |
| `eval` / `new Function(` / `document.write(` | unknown | **0** | clean |

> The plan said "33 `innerHTML`" but a fresh `rg '\.innerHTML\s*=' index.html | wc -l`
> against HEAD reports 29. The drop is from the four `innerHTML` sites in the
> long-dead overview-roadmap block that were inlined into the build pipeline
> during the v7.0→v8.0 migration. The remaining 29 are real and inventoried below.

## The 29 `.innerHTML = …` sites (one row each)

Columns: **L#** (line in `index.html` at HEAD `b3f0da75a`), **Target element**,
**RHS shape**, **Untrusted input?**, **Category** (see §3), **Migration cost**.

| L# | Target | RHS shape | Untrusted? | Cat | Migration cost |
|---:|---|---|---|---|---|
| 4306 | `mitre-dd-list` | `buildMitreDdList('')` | No (closed enum of MITRE techniques, escaped via `esc()`) | C | M (helper builds DOM nodes) |
| 4314 | `mitre-dd-list` | `buildMitreDdList(val)` | `val` is user search input but only used as a *filter predicate*; never injected into HTML | C | M (same as above) |
| 4594 | `equipment-model-select` | `'<option value="">All models</option>'` (static literal) | No | **A** | S (one-line helper) |
| 4620 | `equipment-model-select` | `'<option value="">All models</option>'` | No | **A** | S |
| 4698 | scratch `<div>` (then `firstChild` migrated into `frag`) | UC-card HTML string built by `buildUCCard` | No (catalog data, escaped via `esc()`) | E | H (intentional HTML-to-DOM bridge) |
| 4859 | `sidebar` (`sb`) | category/subcategory tree HTML built via `esc(sc.n)` | No | C | M (DOM-building helper) |
| 5082 | `main` | overview/category cards built via `esc()` per cell | No | C | H (large; whole-page render) |
| 5117 | `main` | category-deep-dive HTML | No | C | H |
| 5141 | `main` | subcategory deep-dive HTML | No | C | H |
| 5244 | `main` | UC-by-tag deep-dive HTML | No | C | H |
| 5313 | `main` | all-UCs grid HTML | No | C | H |
| 5584 | `detail-pane` (`pane`) | UC detail-pane HTML (incl. `esc(d.path)`, `esc(d.title)`, `esc(githubIssueUrlForEntry(e))`) | No | C | H |
| 5612 | `detail-list` | UC condensed list HTML | No | C | M |
| 5847 | `mitre-map-body` (`body`) | MITRE matrix HTML (`esc(t.id)`, `esc(t.name)`, etc.) | No | C | M |
| 6026 | `src-body` (`b`) | source-catalogue HTML table | No (literal strings) | C | M |
| 6209 | `inv-body` | `_invBuildBody('')` | No | C | M |
| 6235 | `inv-body` | `_invBuildBody(searchInput.value.trim())` | `filterText` is user search; only used as filter predicate (line 6121–6134) and as `esc(ft)` for the no-match echo on line 6191 | C | M |
| 6259 | `equipment-model-select` | `'<option value="">All models</option>'` | No | **A** | S |
| 6268 | `inv-body` | `_invBuildBody(...)` | same as 6235 | C | M |
| 6477 | `equipment-model-select` | `'<option value="">All models</option>'` | No | **A** | S |
| 6542 | `main` | recommend-view HTML | No | C | H |
| 6602 | `main` | scan-view HTML | No | C | H |
| 6628 | `equipment-select` | `<option value="">All equipment</option>` + `esc(eq.id)`/`esc(eq.label)` per equipment | No | C | S–M |
| 6638 | `equipment-model-select` | `'<option value="">All models</option>'` (then re-populated via `+=` on 6639) | No | **A**+**D** | M (also the `+= '<option>'` loop pattern) |
| 6643 | `equipment-model-select` | `'<option value="">All models</option>'` | No | **A** | S |
| 6748 | `equipment-model-select` | `'<option value="">All models</option>'` | No | **A** | S |
| 6781 | `inv-count` (`countEl`) | `summary` (string built from numeric counts only) | No | **D** | S |
| 6921 | `inv-body` | `_invBuildBody(ev.target.value)` | same as 6235 | C | M |
| 6932 | `inv-body` | `_invBuildBody('')` | No | C | M |

Additionally, two `countEl.innerHTML += …` *append* sites appear at lines
**6783** and **6789** — they extend the prior `summary` with a `<br><span>` block.
They are not in the 29 because they re-use an existing element's content via `+=`
not `=`, but they share the Category D smell and are listed in §3 for completeness.

## Categories

- **A — Static literal HTML, no dynamic data.** 7 sites:
  4594, 4620, 6259, 6477, 6638, 6643, 6748. All identical:
  `ms.innerHTML = '<option value="">All models</option>'`. Reset the
  "all models" sentinel option on the equipment-model `<select>`.
  Safe today (no untrusted input touches the literal). Easiest to migrate
  to `ms.replaceChildren(…)` and the single highest-quality "win" for
  a follow-on PR because seven call sites collapse into one helper.

- **B — `innerHTML = ''` pure clearing.** 0 sites at HEAD.
  (`replaceChildren()` would be the modern equivalent, but no sites
  actually need it today — every clearing site in `index.html` also
  re-populates the element in the same statement.)

- **C — Dynamic HTML built by a helper that uses `esc()`.** 18 sites.
  These compose HTML strings from catalog data (`EQUIPMENT_GROUPS`,
  `FILTER_FACETS.mitre`, `UC_DOC_MAP`, etc.) and run every string through
  `esc()` (the canonical 5-char HTML escaper defined at line 3582). No
  user-controlled text reaches the HTML output; user filter text is used
  only in predicate comparisons (`.toLowerCase().indexOf(ft) !== -1`) and
  echoed back only via `esc(ft)` on the no-match block (line 6191).
  Safe today but the HTML-string-concatenation pattern is the largest
  surface area in the file and is brittle to future authoring mistakes.

- **D — `+=` append (innerHTML extension) on an already-populated element.**
  3 sites: 6638-6639 (model-select build loop), 6781 + 6783 + 6789
  (`countEl.innerHTML +=` block). These are the *only* places where
  innerHTML is read implicitly (the browser re-serializes the previous
  content to read it back) — a known performance trap and a defense-in-
  depth weakness if any earlier write smuggles unescaped data.

- **E — Scratch `<div>` used as HTML-string → DOM-node bridge.** 1 site:
  4698, inside the `appendVirtualizedUCRows` virtual-scroll renderer.
  This is the *intentional* pattern: build a string via `buildUCCard`,
  parse it into nodes via `d.innerHTML = html; while (d.firstChild)
  frag.appendChild(d.firstChild)`. Replacing it requires a real
  HTML→DOM helper (e.g., `<template>` cloning) and is more invasive.
  Last priority, but the highest-impact win once done because the
  virtual-scroll renderer is the hot path for the "All UCs" view.

## Helper function audit

The four functions that drive the Category C sites are all escape-safe
today. Reviewers should re-audit them on every change because they're
the load-bearing layer.

### `esc(s)` — `index.html` 3582–3585

Canonical 5-char HTML escaper:

```javascript
function esc(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#39;');
}
```

Coverage of OWASP §4 ("HTML Entity Encoding") rules 1–3: complete. Does
not handle JavaScript context, URL context, or CSS context — but those
contexts are not exercised by Category C sites (no `<script>` or `style`
attribute injection from catalog data).

### `buildMitreDdList(query)` — `index.html` 4273–4295

Every dynamic value passes through `esc()`:

- `esc(group.tactic || '')` at line 4287 (inside `onclick` attribute)
- `esc(group.label)` at line 4287 (inside text)
- `esc(t.id)` at line 4290 (twice: inside `onclick` and inside text)
- `esc(t.name || '')` at line 4290

No raw concatenation of dynamic values. The query parameter is used
only as a case-insensitive filter on `.toLowerCase().indexOf(q)` — it
never enters the output HTML.

### `_invBuildBody(filterText)` — `index.html` 6120–6194

Every dynamic value passes through `esc()`:

- `esc(grp.name)` at line 6149
- `esc(it.eq.label)` at line 6162
- `esc(m.label)` at line 6177
- `esc(ft)` at line 6191 (the no-match echo of user filter text)

Raw values appear inside HTML attributes but only for catalog-controlled
IDs (`it.eq.id` at line 6159, `it.eq.id` and `m.id` at 6176): these are
the same kebab-case slugs that flow through `audit-uc-structure` and are
guaranteed not to contain quote characters. Still a smell — see §6.

### `_dataSizingURL(s)` — only consumed as `href="' + _dataSizingURL('') + '"'`

Returns a fixed `https://…` URL with no dynamic parameters. Safe today
because the function takes no untrusted input.

## CSP accounting (`'unsafe-inline'` on both `script-src` and `style-src`)

`index.html` ships exactly **one** CSP directive on line 5:

```
default-src 'self';
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
font-src 'self' https://fonts.gstatic.com;
img-src 'self' data: https:;
connect-src 'self' https:
```

This is the **load-bearing F8 weakness**. `'unsafe-inline'` on `script-src`
means the `script-src 'self'` defense-in-depth that would normally backstop
a Category C HTML-injection bug is **not** in effect: if any `esc()`
call site ever fails, an attacker who controls the catalog data could
inject a `<script>` tag and the browser would run it. The Category C audit
in §4 establishes that no such failure exists at HEAD — but the safety
net is missing.

Why `'unsafe-inline'` is still on `script-src`:

- **2 inline `<script>…</script>` blocks** in `index.html` (bare `<script>`
  open tag count = 2 at HEAD).
- **104 inline event-handler attributes** (`onclick=`, `onkeydown=`,
  `onchange=`, `onsubmit=`, `onload=`) — every one of these requires
  `'unsafe-inline'` (or a per-handler `nonce`, which the browser only
  supports for `<script>` and `<style>` elements, not for inline event
  handlers — those need `'unsafe-hashes'` plus per-handler hashing).
- The 5 external scripts (`<script src=`) under `script-src 'self'`
  would work without `'unsafe-inline'`; the inline blocks and the 104
  inline handlers are what's holding it up.

Why `'unsafe-inline'` is still on `style-src`:

- **1 inline `<style>…</style>` block** in `<head>`.
- **42 inline `style="…"` attributes** in the body of `index.html`
  (e.g., `<span style="font-size:11px;color:var(--text-tertiary)">`
  at line 6783).
- `style-src` also allows `https://fonts.googleapis.com` because the
  Google Fonts CSS file is served from that origin.

Removing `'unsafe-inline'` from either directive is a multi-PR refactor
(extract the 2 inline scripts and 104 inline handlers + the 1 inline
style and 42 inline style attributes into external files, then either
re-add via build pipeline or use `nonce`/`hash` allow-lists). **Tracked
as a known-cost follow-up**, not the F8 close criterion. The F8 close
criterion is PR-A + PR-B landed and Category C re-audited; CSP tightening
folds into phase **P10** (Performance + a11y hardening — see the P10 row
in [docs/health-check-2026-progress.md](health-check-2026-progress.md)),
which the plan already names F8 as a prerequisite for.

## Recommended migration plan

Three PRs, ordered by risk-adjusted value. PR-A + PR-B land the F8
close; PR-C is the explicit known-cost follow-up. CSP tightening
folds into phase **P10** (see §5) and is *not* in F8 scope.

### PR-A (zero-risk, ≤15 LOC): collapse the 7 Category A sites

Replace the seven copies of `ms.innerHTML = '<option value="">All models</option>'`
with one helper:

```javascript
function _resetEquipmentModelSelect(ms) {
  if (!ms) return;
  var opt = document.createElement('option');
  opt.value = '';
  opt.textContent = 'All models';
  ms.replaceChildren(opt);
}
```

Then call `_resetEquipmentModelSelect(ms)` at lines 4594, 4620, 6259,
6477, 6638, 6643, 6748. Net: ~6 LOC added, ~7 LOC removed, behaviour
identical, no XSS surface reduction but the file gets one less
"raw HTML string" pattern to grep for. Bonus: makes the equipment-
model-select reset semantics introspectable from a single source.

### PR-B (low-risk, ~50 LOC): fix the two Category D `+=` sites

Rewrite the `countEl.innerHTML += '<br><span …>…</span>'` blocks at
lines 6783 and 6789 to build the auxiliary `<span>` via `document.
createElement` and append it to `countEl`. The `summary` string written
to `innerHTML` on line 6781 already only contains numeric strings and
spaces — but folding it into the DOM-build path removes the implicit
re-parse that `+=` triggers.

Same for the `eq.models.forEach(function(m) { ms.innerHTML += '<option …>'; })`
loop at line 6639: rewrite as `ms.append(document.createElement('option'))`
inside the loop. This is the only loop in the file that issues a fresh
`innerHTML` write per iteration; the perf win is small but real.

### PR-C (medium-risk, ~500 LOC): replace HTML-string concatenation with `<template>` cloning in the virtual-scroll renderer

Rewrite the `buildUCCard(entry)` → `d.innerHTML = html; while (d.firstChild)
frag.appendChild(d.firstChild)` bridge at line 4698 into a `<template>`-
cloned + field-populated pattern. This is the hot path for the "All UCs"
view and is the largest single source of innerHTML churn in the file
(every UC card on the all-UCs grid goes through this path).

Out of scope for autonomous mode: this requires a render-fidelity test
plan (perf-a11y will catch the layout half but not the click handlers).
Tracked here as a known-cost item, not a near-term action.

## What's deliberately not on this list

- **Removing `'unsafe-inline'` from `style-src`.** Multi-PR effort to
  migrate every inline style. Not a small task.
- **Removing `innerHTML = "<option …>"` from `populateEquipmentSelect`
  (line 6624–6628).** This is a single-call-site builder that runs once
  on app boot; the cost/benefit ratio of rewriting it is the same as
  PR-A but it doesn't collapse multiple call sites, so it's lower
  priority. Will fold into PR-A only if it's trivial.
- **Adopting Trusted Types.** Requires `Content-Security-Policy:
  require-trusted-types-for 'script'` and a sink-by-sink rewrite. Listed
  in `docs/health-check-2026-progress.md` recommended action #2 as a
  future phase; not in F8 scope.

## How to keep this doc honest

Re-run on every PR that edits `index.html`:

```bash
grep -nE '\.innerHTML\s*=' index.html | wc -l   # should drop only after PR-A, PR-B, PR-C
grep -nE '"unsafe-inline"' index.html           # should stay at 1 until the style-src removal
grep -nE '\beval\s*\(|new Function\s*\(|document\.write\s*\(' index.html  # must stay 0
```

If any of these three numbers drift unexpectedly:

1. Update the table in §2 (one row per added/removed site).
2. Update the TL;DR table in §1.
3. Update [docs/health-check-2026-progress.md](health-check-2026-progress.md)
   F8 row with the new counts.
4. Mention the doc-refresh in the PR description so a reviewer can
   confirm the inventory is current.

A future audit verb (`audit-frontend-inventory` against this doc) is
filed under F8 follow-on actions in `docs/health-check-2026-progress.md`
but is **not** a blocker for closing F8 — the F8 close criteria are
PR-A + PR-B landed, with PR-C tracked as an explicit known-cost
follow-up.

## See also

- [docs/health-check-2026-progress.md](health-check-2026-progress.md) — F8 row
- [docs/ci-architecture.md](ci-architecture.md) — surrounding CI guardrails
- [docs/workflow-audit.md](workflow-audit.md) — sibling single-page inventory
- OWASP XSS Prevention Cheat Sheet, §4–§5 (HTML & JavaScript context encoding)
- `index.html` lines 3582 (`esc`), 4273 (`buildMitreDdList`), 6120 (`_invBuildBody`)

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** OWASP Foundation. (2026). *OWASP Cheat Sheet Series*. OWASP Foundation, Inc. Retrieved May 11, 2026, from https://cheatsheetseries.owasp.org/

### Related repository documents

- [`docs/ci-architecture.md`](ci-architecture.md)
- [`docs/health-check-2026-progress.md`](health-check-2026-progress.md)
- [`docs/workflow-audit.md`](workflow-audit.md)

### Cited by

- [`docs/health-check-2026-progress.md`](health-check-2026-progress.md)

<!-- END-AUTOGENERATED-SOURCES -->
