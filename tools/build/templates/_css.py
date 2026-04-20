"""tools.build.templates._css — shared inline stylesheet for SSG pages.

Inlined into every static page so it renders the moment the HTML
arrives — no CSS round-trip, no FOUC, no JS dependency. Target ~5 KB
raw / ~1.5 KB gzipped. The richer SPA bundle at
``/assets/styles.<hash>.css`` is loaded only by ``/browse/``.

Tokens use ``light-dark()`` so we don't need a JS theme switcher on
static pages — the browser's ``prefers-color-scheme`` is the source of
truth. ``prefers-reduced-motion`` is honoured for scroll behaviour and
hover transitions.

The class names mirror what ``templates/{uc,category,landing,regulation}.py``
emit; keep the two in sync when adding sections.
"""

from __future__ import annotations


PAGE_CSS = """
:root {
  color-scheme: light dark;
  --bg: light-dark(#fafaf9, #1a1817);
  --bg-soft: light-dark(#f3f1ef, #221f1d);
  --bg-card: light-dark(#ffffff, #2a2624);
  --fg: light-dark(#1a1817, #f0ece8);
  --fg-soft: light-dark(#5a544e, #b8b2ab);
  --fg-muted: light-dark(#7a746e, #918a82);
  --accent: light-dark(#a3360e, #ff7748);
  --accent-soft: light-dark(#fde9d8, #2e2018);
  --accent-fg: light-dark(#ffffff, #1a1817);
  --border: light-dark(#e6e2dd, #3a3531);
  --code-bg: light-dark(#f5f1ec, #1f1c1a);
  --crit-bg: light-dark(#fde2dc, #4a1e16);
  --high-bg: light-dark(#fde9d8, #4a3018);
  --med-bg:  light-dark(#fdf3d8, #4a4018);
  --low-bg:  light-dark(#dff5e6, #1a3a25);
  --max-w: 64rem;
  --radius: 8px;
}
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui,
               "Helvetica Neue", Arial, sans-serif;
  font-size: 16px; line-height: 1.55;
  color: var(--fg); background: var(--bg);
  text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration-thickness: 1px; text-underline-offset: 2px; }
a:hover, a:focus-visible { text-decoration-thickness: 2px; }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.muted { color: var(--fg-muted); font-size: 0.875rem; }
.prov { color: var(--fg-muted); font-size: 0.85rem; font-style: italic; }
.lede { font-size: 1.125rem; color: var(--fg-soft); max-width: 42rem;
  margin: 0.75rem 0 1rem; }
header.site, footer.site {
  background: var(--bg-soft); border-bottom: 1px solid var(--border);
  padding: 0.75rem 1rem;
}
footer.site { border-top: 1px solid var(--border); border-bottom: none; }
header.site nav, footer.site nav {
  max-width: var(--max-w); margin: 0 auto;
  display: flex; flex-wrap: wrap; gap: 0.75rem 1.25rem; align-items: center;
}
header.site .brand { font-weight: 700; color: var(--fg); text-decoration: none; }
header.site nav a, footer.site nav a {
  color: var(--fg-soft); text-decoration: none; font-size: 0.9rem;
}
header.site nav a:hover, footer.site nav a:hover { color: var(--accent); }
main { max-width: var(--max-w); margin: 0 auto; padding: 1.25rem 1rem 3rem; }
nav.breadcrumb { font-size: 0.875rem; color: var(--fg-muted); margin-bottom: 1rem; }
nav.breadcrumb ol { list-style: none; padding: 0; margin: 0;
  display: flex; flex-wrap: wrap; gap: 0.25rem 0.5rem; }
nav.breadcrumb li { display: inline; }
nav.breadcrumb li::after { content: "›"; margin-left: 0.5rem; color: var(--fg-muted); }
nav.breadcrumb li:last-child::after { content: ""; }
nav.breadcrumb a { color: var(--fg-soft); text-decoration: none; }
nav.breadcrumb a:hover { color: var(--accent); text-decoration: underline; }
article { background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.5rem; }
article > header h1 { font-size: 1.875rem; line-height: 1.2; margin: 0 0 0.5rem; }
.uc-id { font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
  color: var(--fg-muted); font-size: 0.875rem; }
article h2, .section-h { font-size: 1.375rem; margin: 2rem 0 0.75rem;
  padding-top: 0.5rem; border-top: 1px solid var(--border); }
article h2:first-of-type, .section-h:first-of-type { border-top: none; padding-top: 0; }
article h3 { font-size: 1.0625rem; margin: 1.25rem 0 0.5rem; }
article p { margin: 0.5rem 0 1rem; }
article ul, article ol { margin: 0.5rem 0 1rem; padding-left: 1.5rem; }
article li { margin: 0.25rem 0; }
article code { font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
  background: var(--code-bg); padding: 1px 4px; border-radius: 3px; font-size: 0.875em; }
article pre { background: var(--code-bg); border: 1px solid var(--border);
  border-radius: 6px; padding: 0.875rem 1rem; overflow-x: auto; line-height: 1.4;
  font-size: 0.875rem; margin: 0.75rem 0 1.25rem; }
article pre code { background: transparent; padding: 0; border-radius: 0; font-size: inherit; }
details { border: 1px solid var(--border); border-radius: 6px;
  padding: 0.5rem 0.875rem; margin: 0.75rem 0 1.25rem; background: var(--bg-soft); }
details summary { cursor: pointer; font-weight: 600; color: var(--fg-soft); }
details[open] summary { margin-bottom: 0.5rem; }
.badges { display: flex; flex-wrap: wrap; gap: 0.375rem; margin: 0.75rem 0 0; }
.badge { display: inline-flex; align-items: center; gap: 0.25rem;
  padding: 0.125rem 0.5rem; border-radius: 999px; font-size: 0.75rem;
  font-weight: 600; line-height: 1.4; border: 1px solid var(--border);
  background: var(--bg-soft); color: var(--fg-soft); text-decoration: none; }
a.badge:hover { border-color: var(--accent); color: var(--accent); }
.badge-crit { background: var(--crit-bg); color: light-dark(#7a1f12, #ffb3a0); border-color: transparent; }
.badge-high { background: var(--high-bg); color: light-dark(#7a4a18, #ffc890); border-color: transparent; }
.badge-med  { background: var(--med-bg);  color: light-dark(#6a5018, #ffe690); border-color: transparent; }
.badge-low  { background: var(--low-bg);  color: light-dark(#1a5a30, #90e6b0); border-color: transparent; }
.badge-wave-crawl { background: light-dark(#e4f0fa, #183040); color: light-dark(#174a6a, #a8d8f0); border-color: transparent; }
.badge-wave-walk  { background: light-dark(#efe4fa, #2a1e40); color: light-dark(#4a2a7a, #c8b0f0); border-color: transparent; }
.badge-wave-run   { background: light-dark(#fae4e4, #401a1e); color: light-dark(#7a1a1a, #f0a8a8); border-color: transparent; }
.uc-ordering ul.uc-chip-list { list-style: none; padding: 0; margin: 0.5rem 0 1.25rem;
  display: flex; flex-wrap: wrap; gap: 0.375rem 0.5rem; }
.uc-ordering ul.uc-chip-list li { margin: 0; }
a.uc-chip { display: inline-flex; align-items: center; gap: 0.375rem;
  padding: 0.25rem 0.625rem; border-radius: 999px; font-size: 0.8125rem;
  border: 1px solid var(--border); background: var(--bg-soft); color: var(--fg);
  text-decoration: none; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
a.uc-chip:hover, a.uc-chip:focus-visible { border-color: var(--accent); color: var(--accent); }
a.uc-chip .chip-id { font-weight: 600; letter-spacing: 0.01em; }
a.uc-chip .chip-wave { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  font-size: 0.6875rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
  padding: 0.0625rem 0.375rem; border-radius: 4px; line-height: 1.2; }
a.uc-chip .chip-wave-crawl { background: light-dark(#cce2f2, #1a3040); color: light-dark(#0f3a5a, #bce0f8); }
a.uc-chip .chip-wave-walk  { background: light-dark(#e0ccf2, #2a1a40); color: light-dark(#3f1a6a, #dcbcf8); }
a.uc-chip .chip-wave-run   { background: light-dark(#f2cccc, #401a1a); color: light-dark(#6a0f0f, #f8bcbc); }
dl.facts { display: grid; grid-template-columns: max-content 1fr;
  gap: 0.375rem 1rem; margin: 0.75rem 0 1.25rem; font-size: 0.9rem; }
dl.facts dt { color: var(--fg-muted); font-weight: 600; }
dl.facts dd { margin: 0; color: var(--fg); }
ul.uc-list { list-style: none; padding: 0; margin: 0.5rem 0 1.5rem; }
ul.uc-list .uc-row { display: grid;
  grid-template-columns: minmax(12rem, max-content) 1fr max-content;
  gap: 0.25rem 0.875rem; padding: 0.625rem 0.75rem;
  border-bottom: 1px solid var(--border); align-items: baseline; }
ul.uc-list .uc-row:hover { background: var(--bg-soft); }
ul.uc-list .uc-link { display: inline-flex; gap: 0.5rem; align-items: baseline;
  text-decoration: none; color: var(--fg); }
ul.uc-list .uc-link:hover .uc-title { color: var(--accent); text-decoration: underline; }
ul.uc-list .uc-id { font-size: 0.8rem; min-width: 6rem; }
ul.uc-list .uc-title { font-weight: 600; }
ul.uc-list .uc-value { color: var(--fg-soft); font-size: 0.875rem; }
ul.link-list { list-style: none; padding: 0; margin: 0.75rem 0 1rem;
  display: grid; grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: 0.375rem 1rem; }
ul.link-list a { color: var(--accent); text-decoration: none; }
ul.link-list a:hover { text-decoration: underline; }
.hero { padding: 1rem 0 1.5rem; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; }
.hero .kicker { color: var(--accent); font-weight: 700; letter-spacing: 0.06em;
  text-transform: uppercase; font-size: 0.8rem; margin: 0 0 0.5rem; }
.hero h1 { font-size: 2.125rem; line-height: 1.15; margin: 0 0 0.75rem; max-width: 40rem; }
.hero .lede { font-size: 1.0625rem; max-width: 38rem; }
.hero-cta { display: flex; flex-wrap: wrap; gap: 0.625rem; margin-top: 1rem; }
.cta { display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 0.875rem; border-radius: 6px; font-weight: 600;
  text-decoration: none; font-size: 0.9rem;
  border: 1px solid var(--accent); color: var(--accent); background: transparent; }
.cta:hover, .cta:focus-visible { filter: brightness(1.05); }
.cta.primary { background: var(--accent); color: var(--accent-fg); }
.domain { margin: 1.5rem 0 1.25rem; }
.domain h3 { font-size: 1.125rem; margin: 0 0 0.25rem; }
.domain .muted { margin: 0 0 0.875rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: 0.875rem; }
.card { background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 0.875rem 1rem; text-decoration: none;
  color: var(--fg); display: block; transition: border-color 0.12s; }
.card:hover, .card:focus-visible { border-color: var(--accent); }
.card-head { display: flex; justify-content: space-between; gap: 0.5rem;
  font-size: 0.75rem; color: var(--fg-muted); margin-bottom: 0.25rem; }
.card-head .cat-id { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.card-title { font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem; color: var(--fg); }
.card-blurb { margin: 0; color: var(--fg-soft); font-size: 0.85rem; line-height: 1.4; }
@media (prefers-reduced-motion: reduce) { .card { transition: none; } }
@media (max-width: 40rem) {
  article { padding: 1rem; }
  article > header h1 { font-size: 1.5rem; }
  .hero h1 { font-size: 1.625rem; }
  dl.facts { grid-template-columns: 1fr; gap: 0.125rem 0; }
  dl.facts dt { margin-top: 0.5rem; }
  ul.uc-list .uc-row { grid-template-columns: 1fr; gap: 0.125rem; padding: 0.625rem 0.5rem; }
  ul.uc-list .uc-id { min-width: 0; }
}
@media print {
  header.site, footer.site, .hero-cta, nav.breadcrumb, details { display: none; }
  details[open] { display: block; }
  article { border: none; padding: 0; }
  body { background: white; color: black; }
  a { color: black; text-decoration: underline; }
}
"""


def page_css() -> str:
    """Return the page stylesheet as a single string (already minified-ish)."""
    return PAGE_CSS.strip()
