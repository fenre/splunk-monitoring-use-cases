# Gemini Prompt — Recreate the Splunk Core Infrastructure Monitoring Use Case Dashboard

> Use this prompt to instruct Google Gemini (or any capable LLM) to rebuild this project from scratch. Paste the full contents of this file as your prompt, then attach the source data files listed in Step 1.

---

## Context

This project is a **single-file, self-contained HTML dashboard** for Splunk solutions engineers and customers. It presents a searchable, filterable repository of ~600 IT infrastructure monitoring use cases — each with criticality ratings, example SPL queries, implementation guidance, and recommended visualizations. It requires no backend, no build step, no dependencies. Everything is embedded in one HTML file and can be hosted on GitHub Pages or served from any static host.

---

## Step 1 — Source Files to Attach

Attach the following files to your session before generating:

| File | Purpose |
|------|---------|
| `use-cases-enriched.md` | Primary source of truth — all use cases with full detail |
| `infrastructure-categories.md` | Category and subcategory taxonomy |

> ⚠️ **Do NOT recreate:** `getting-started.html` and `use_case_repository.spl` are deprecated and should not exist in the rebuilt project.

---

## Step 2 — Output

Generate a **single file** named `use-case-dashboard.html`. All CSS, JavaScript, and data must be inline. No external dependencies except Google Fonts (loaded via `@import`).

---

## Step 3 — Data Model

The use case data must be compiled into a JavaScript constant named `DATA` embedded in a `<script>` tag. Use the following structure:

```javascript
const DATA = [
  {
    i: 1,                         // category ID (integer)
    n: "Server & Compute",        // category name
    s: [                          // subcategories array
      {
        i: "1.1",                 // subcat ID (string like "1.1")
        n: "Linux Servers",       // subcat name
        u: [                      // use cases array
          {
            i: "1.1.1",           // UC ID (string like "1.1.1")
            n: "CPU Utilization Trending",   // title
            c: "high",            // criticality: "critical"|"high"|"medium"|"low"
            f: "intermediate",    // difficulty: "beginner"|"intermediate"|"advanced"|"expert"
            v: "...",             // value proposition (1–2 sentences)
            t: "Splunk_TA_nix",   // App/TA name (backtick-formatted ok)
            d: "sourcetype=cpu",  // data sources
            q: "index=os ...",    // SPL query (raw text, may be multi-line)
            m: "...",             // implementation notes
            z: "..."              // visualization recommendations
          }
        ]
      }
    ]
  }
];
```

Also define this category grouping constant immediately after `DATA`:

```javascript
const CAT_GROUPS = {
  infra:    [1, 2, 5, 6, 15, 18, 19],
  security: [9, 10, 17],
  cloud:    [3, 4, 20],
  app:      [7, 8, 11, 12, 13, 14, 16]
};
```

Parse every use case from `use-cases-enriched.md` into this structure. All fields must be populated where available in the source. The `q` field (SPL) is the most important — do not omit it.

---

## Step 4 — Visual Design

### Design Language
Dark glassmorphism. Professional, data-dense, and clean. Inspired by enterprise monitoring tools. No gradients on primary surfaces — keep the background flat dark. Glass cards have subtle blur, border, and shadow effects.

### CSS Custom Properties (copy exactly)
```css
:root {
  --glass-bg:        rgba(255,255,255,0.05);
  --glass-border:    rgba(255,255,255,0.10);
  --glass-highlight: rgba(255,255,255,0.15);
  --glass-shadow:    rgba(0,0,0,0.4);
  --accent:          #65A637;   /* Splunk green */
  --accent2:         #4EC9B0;   /* teal */
  --accent3:         #ED7872;   /* coral */
  --bg-start:        #111215;
  --bg-mid:          #171D21;
  --bg-end:          #0D0F11;
  --text:            #DCE1E6;
  --text-dim:        #D0D6DC;
  --text-bright:     #FAFBFC;
  --crit-critical:   #D94F57;
  --crit-high:       #EC9960;
  --crit-medium:    #F8C869;
  --crit-low:        #65A637;
}
```

### Fonts
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
```
- Body text: `Inter`
- SPL code blocks: `JetBrains Mono`

### Criticality Colors
| Value | Color |
|-------|-------|
| `critical` | `--crit-critical` (#D94F57) |
| `high` | `--crit-high` (#EC9960) |
| `medium` | `--crit-medium` (#F8C869) |
| `low` | `--crit-low` (#65A637) |

### Difficulty Badge Colors
| Value | Color |
|-------|-------|
| `beginner` | rgba(101,166,55,0.15) / #65A637 |
| `intermediate` | rgba(91,155,213,0.15) / #5B9BD5 |
| `advanced` | rgba(236,153,96,0.15) / #EC9960 |
| `expert` | rgba(217,79,87,0.15) / #D94F57 |

---

## Step 5 — Page Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Splunk Infrastructure Monitoring — Use Case Repository</title>
  <style>/* all CSS inline */</style>
</head>
<body>
  <div class="bg-gradient"></div>

  <header>
    <div class="header-inner">
      <!-- hamburger toggle (mobile only) -->
      <button class="sidebar-toggle" id="sidebar-toggle">&#9776;</button>
      <!-- logo -->
      <div class="logo">
        <div class="logo-icon">&gt;</div>
        <div>
          <h1>Infrastructure Monitoring</h1>
          <div class="subtitle">Use Case Repository</div>
        </div>
      </div>
      <!-- search -->
      <div class="search-wrap">
        <span class="search-icon">🔍</span>
        <input type="text" id="search" placeholder="Search use cases, SPL, TAs..." autocomplete="off">
      </div>
      <!-- count -->
      <div class="header-stat"><span class="num" id="total-count">0</span> use cases</div>
    </div>
  </header>

  <div class="app-layout">
    <aside class="sidebar glass" id="sidebar"></aside>
    <main class="main-content" id="main"></main>
  </div>

  <!-- Detail modal -->
  <div class="modal-overlay" id="modal-overlay">
    <div class="modal" id="modal"></div>
  </div>

  <script>
    const DATA = [ /* ... */ ];
    const CAT_GROUPS = { /* ... */ };
    /* all JS inline */
  </script>
</body>
</html>
```

---

## Step 6 — Layout

### Header (sticky, `z-index: 100`)
- Height ~62px, `padding: 14px 32px`
- Background: `rgba(17,18,21,0.92)` with `backdrop-filter: blur(30px)`
- Border-bottom: `1px solid var(--glass-border)`
- Contents: hamburger button (mobile only) | logo | search bar | use case count
- Max-width: 1600px centered

### App Layout (below header)
- `display: flex; gap: 24px; padding: 24px; max-width: 1600px`
- Left: `<aside>` sidebar (300px wide, sticky)
- Right: `<main>` content area (flex: 1)

### Sidebar (`class="sidebar glass"`)
- Width: 300px, `position: sticky; top: 100px`
- Max-height: `calc(100vh - 124px)`, `overflow-y: auto`
- Contains nav items: first item is always "Overview (★)", then one item per category
- Active item has green gradient background
- Each category item shows: numbered badge | category name | use case count | expand chevron
- Clicking a category shows its subcategories as indented sub-items
- Clicking a subcategory jumps to that section within the category view

### Main Content
Switches between two views:

**Overview view** (shown on load, when no category selected):
- Hero section with gradient background, headline ("Infrastructure Monitoring Intelligence"), stats (total UCs, categories, subcategories, quick wins count)
- Overview filters to switch between All / Infra / Security / Cloud / App group views
- Roadmap grid showing all 20 categories with use case counts (cards, `repeat(auto-fill, minmax(230px, 1fr))`)
- "Quick Wins" section — use cases that are Beginner or Intermediate difficulty AND Critical or High criticality, grouped by category with collapsible SPL preview

**Category view** (shown when a category is selected):
- Category header: name, subcategory count, UC count
- Filter bar: All | Critical | High | Medium | Low (criticality), then All | Beginner | Intermediate | Advanced | Expert (difficulty)
- Subcategory title sections, each with a use case card grid below it
- Cards grid: `repeat(auto-fill, minmax(340px, 1fr))`

---

## Step 7 — Use Case Cards

Each card (`class="glass uc-card [criticality]"`) contains:
- A 3px left border strip color-coded by criticality
- Card head: criticality dot | UC title | UC ID | difficulty badge
- Value field (2-line truncated with `-webkit-line-clamp: 2`)
- TA badge (if present)

Clicking a card opens the detail modal.

---

## Step 8 — Detail Modal

Triggered by clicking a card. Renders on top of the page, clicking the overlay or pressing Escape closes it.

Modal contains:
- Close button (×) top-right
- Modal head: criticality badge | difficulty badge | use case title | UC ID + breadcrumb (Category → Subcategory)
- Sections (in order, only rendered if field is populated):
  1. **Value** — `uc.v`
  2. **Metadata grid** (2 columns): App/TA (`uc.t`) | Data Sources (`uc.d`)
  3. **SPL Query** — `uc.q` in a monospace code block with a "Copy" button
  4. **Implementation** — `uc.m`
  5. **Visualization** — `uc.z`
- Keyboard navigation: ← / → arrows to navigate to previous/next UC in the current filtered list

---

## Step 9 — Search

- Live search on `input` event with 200ms debounce
- Searches across: UC title (`n`), value (`v`), TA (`t`), data sources (`d`), SPL (`q`), implementation (`m`)
- Case-insensitive
- When search has input, sidebar switches to "Search Results" view showing matching cards from all categories
- Clear search restores prior state

---

## Step 10 — Mobile Responsiveness

### Breakpoints

**Tablet (max-width: 900px):**
- Layout stacks vertically (`flex-direction: column`)
- Sidebar becomes full-width horizontal scrolling nav at top
- Card grid drops to 1 column
- Modal meta grid drops to 1 column

**Phone (max-width: 600px):**
- Header: logo subtitle hidden, search bar drops to its own row (full-width), use case count hidden
- Hamburger button (☰) appears; tapping it toggles sidebar visibility
- Sidebar is hidden by default; toggling adds `.open` class to show it; selecting a category auto-closes sidebar
- App layout padding reduced to 12px
- Modal: `padding: 0` on overlay, `align-items: flex-end` — modal slides up from bottom like a native sheet, `border-radius: 20px 20px 0 0`, `max-height: 92vh`
- SPL blocks: `font-size: 11px`
- Touch targets: `min-height: 44px` on nav items

---

## Step 11 — JavaScript Architecture

All JS is vanilla, no frameworks. Key functions:

| Function | Purpose |
|----------|---------|
| `buildSidebar()` | Renders the sidebar nav from `DATA`; marks active category/subcat |
| `renderOverview()` | Renders the overview hero, roadmap grid, and quick wins |
| `renderCategory(id)` | Renders a single category's subcategories and UC cards |
| `selectCat(id)` | Sets `currentCat`, resets filters, calls `buildSidebar()` + render; on mobile calls `closeSidebarOnMobile()` |
| `renderUCCard(uc)` | Returns HTML string for a single UC card |
| `openUC(id)` | Looks up a UC by ID from `ucIndex`, renders modal, shows overlay |
| `closeModal()` | Hides modal overlay |
| `navUC(dir)` | Navigates -1/+1 in current filtered UC list while modal is open |
| `copySPL(btn)` | Copies SPL from parent element to clipboard, shows "Copied!" feedback |
| `escHtml(s)` | Escapes `<`, `>`, `&`, `"` for safe HTML insertion |
| `closeSidebarOnMobile()` | Removes `.open` from sidebar if `window.innerWidth <= 600` |

**State variables:**
```javascript
let currentCat = null;          // null = overview
let currentFilter = 'all';      // criticality filter
let currentDiffFilter = 'all';  // difficulty filter
let currentSubcat = null;       // active subcat ID
let currentSearch = '';         // search string
let allUCs = [];                // flat array of all {cat, sc, uc, flatIdx}
let ucIndex = {};               // uc.i -> {cat, sc, uc, flatIdx}
```

**Initialization (at end of script):**
```javascript
buildSidebar();
renderOverview();
```

---

## Step 12 — Remaining Project Files

In addition to the generated `use-case-dashboard.html`, the project folder should contain the following files unchanged:

| File | Notes |
|------|-------|
| `use-cases-enriched.md` | Source data, keep as-is |
| `use-cases-full.md` | Supplementary data, keep as-is |
| `infrastructure-categories.md` | Category taxonomy, keep as-is |
| `github-pages-setup.md` | Deployment guide, keep as-is |

---

## Step 13 — Deployment

The dashboard is designed to be deployed as a static page on GitHub Pages. Rename `use-case-dashboard.html` to `index.html` when pushing to the repository root. See `github-pages-setup.md` for full instructions.

---

## Quality Checklist

Before finalizing, verify:

- [ ] All ~600 use cases from `use-cases-enriched.md` are present in `DATA`
- [ ] Every UC has `i`, `n`, `c`, `f`, `v`, `t`, `d`, `q` populated (at minimum)
- [ ] `m` (implementation) and `z` (visualization) populated where available in source
- [ ] Search works across all fields
- [ ] Criticality and difficulty filters work
- [ ] Modal opens, shows correct data, and closes
- [ ] Keyboard arrow navigation works in modal
- [ ] Copy SPL button works
- [ ] Overview roadmap shows all categories
- [ ] Quick Wins section populates correctly
- [ ] Mobile: hamburger shows at ≤600px, modal slides up from bottom
- [ ] No external JS/CSS dependencies (only Google Fonts CDN is acceptable)
- [ ] File is self-contained — works offline once fonts are cached
