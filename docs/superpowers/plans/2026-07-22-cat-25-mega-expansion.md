# cat-25 "Personal & Hobbyist Monitoring" — Mega-Expansion Plan

**Goal:** Grow the fun category (`cat-25`) from its launch state of 117 use cases
across 13 subcategories into the largest, broadest, most gleefully over-engineered
category in the catalogue — a target of **1,000+ use cases across ~40 subcategories**
(with a stretch vision of ~2,000 across ~60). Every entry proves the same thesis:
the exact SPL, dashboards, alerting, and anomaly detection used on a corporate data
centre work just as well pointed at your own life.

**Guiding principle:** Almost every consumer gadget, hobby service, or DIY sensor
exposes a REST API, webhook, MQTT topic, ESP32/ESPHome feed, SDR stream, CSV export,
or computer-vision model you can pipe into Splunk HEC. Ingest it all into
`index=personal` and your life gets the same observability production does.

**Reality check:** This is not hypothetical. The overwhelming majority of the ideas
below map to real, published community projects (Grafana<sup class="ref">[<a href="#ref-2">2</a>]</sup>/Home Assistant/GitHub) —
sourdough-rise ESP32 monitors, beehive weight+CV bee-counting, DIY seismographs
(GeoShake), Geiger counters (MultiGeiger), ADS-B trackers (aerodrome/flightjar),
live caffeine dashboards, relationship chat-analytics, swear jars, and more. Each
maps cleanly to a `sourcetype` under `index=personal`.

---

## Authoring contract (unchanged from launch)

Every UC must:

- Validate against [`schemas/uc.schema.json`](../../../schemas/uc.schema.json) with all
  13 required fields plus the optional depth fields the launch set uses.
- Use only well-known SPL commands / eval functions (no hallucinated syntax) and
  avoid the high-severity anti-patterns (`join`, `makeresults`, `random()`,
  `search` after `stats`, `earliest=0`, unbounded `transaction`).
- Carry a jargon-free `grandmaExplanation` with a **unique opener within its
  subcategory** (enforced by `audit-content-quality`).
- Keep `value` distinct from `description`.
- Register every new `sourcetype` in
  [`src/splunk_uc/audits/_spl_well_known.py`](../../../src/splunk_uc/audits/_spl_well_known.py).
- Add a matching block to `apps/web/src/data/non-technical-view.data.ts` for every
  new subcategory, then `emit:legacy` to regenerate `non-technical-view.js`.

Subcategory IDs are **gap-free and sequential** (`25.14`, `25.15`, …). The thematic
map below is the intended ordering; actual authoring assigns the next free integer.

Generator: `tools/build/` is untouched; UCs are authored via a standalone
generator script (the launch set used one) that emits sidecars following the
template above. `_category.json` `useCaseCount` fields and the top-level total are
updated to match after each batch.

---

## Subcategory map

### Launched (deepen to ~16–18 each in later waves)

| # | Subcategory |
|---|---|
| 25.1 | Fitness & Activity Tracking |
| 25.2 | Health, Sleep & Wearables |
| 25.3 | Connected Cars & EVs |
| 25.4 | Smart Home Platforms & Automation |
| 25.5 | Smart Home Devices & Sensors |
| 25.6 | Home Energy & Solar |
| 25.7 | Media, Gaming & Entertainment |
| 25.8 | Home Lab & Self-Hosting |
| 25.9 | Home Network & Connectivity |
| 25.10 | Weather, Environment & Garden |
| 25.11 | Pets & Home Life |
| 25.12 | Personal Finance & Crypto |
| 25.13 | Digital Life & Productivity |

### Wave 1 — crowd-pleasers & the physical world (`25.14`–`25.19`)

| # | Subcategory | Representative sourcetypes |
|---|---|---|
| 25.14 | Travel, Commute & Flight-Spotting | `adsb:aircraft`, `flight:log`, `commute:trip`, `transit:arrival`, `geofence:event`, `travel:document`, `airprice:quote` |
| 25.15 | Kitchen, Cooking & Fermentation | `sourdough:reading`, `bbq:probe`, `kitchen:appliance`, `espresso:shot`, `pantry:item`, `kombucha:reading` |
| 25.16 | Homebrewing, Beer & Wine | `brew:fermentation`, `kegerator:pour`, `winecellar:reading` |
| 25.17 | Making, 3D Printing & Workshop | `octoprint:job`, `printer:telemetry`, `filament:spool`, `cnc:job`, `workshop:air`, `tool:battery` |
| 25.18 | Home Security & Surveillance | `frigate:event`, `camera:health`, `alarm:event`, `lock:access`, `plate:detection`, `doorbell:event` |
| 25.19 | Water, Plumbing & Utilities | `watermeter:flow`, `sumppump:event`, `wellpump:event`, `pool:chemistry`, `watersoftener:status`, `irrigation:zone` |

### Wave 2 — the sublime & the ambitious (`25.20`–`25.28`)

Citizen science (seismograph, Geiger, lightning, radon, allsky, aurora, ISS),
radio & SDR (APRS/WSPR, meteor scatter, NOAA sat images), backyard observatory,
family/baby chaos, homestead (bees/chickens/livestock), advanced health &
biohacking (CGM/HRV/apnea/illness-early-warning), wildlife & biodiversity
(BirdNET, moth-trap CV, bat detector), aquariums/reptiles, and sports/skill
telemetry (VBT bar-path, gait IMU, climbing hangboard, shot-arc CV).

### Wave 3 — the long tail (`25.29`–`25.40`)

Games & tabletop, collections, mind/mood/journaling, relationships & household
pettiness, everyday habits & vices, money pettiness, bodily oddities (tasteful),
household supplies & logistics, building health & structural, personal cyber &
digital exhaust, seasonal & silly, and cross-stream ML / the personal digital twin.

### Stretch — the "Personal Enterprise" frontier (`25.41`–`25.60`)

Micro-mobility & action sports, real aviation & flight sim, boating & marine,
fishing/hunting/foraging, music-making & creator analytics, tabletop RPG
campaigns, reading & second brain, language learning, wardrobe/fashion/beauty,
sustainability & zero-waste, chronic-condition management, elder care &
accessibility, wedding/event planning, home renovation PM, genealogy, spiritual
practice, volunteering, life-logging & memories, personal "Life OS" & digital
twin, and prediction markets on yourself.

**Meta layer (cross-cutting):** the parody-the-enterprise framing — Personal NOC
(a house-health wall), Personal SOC (breach/entry/impossible-travel), Personal SRE
(SLOs and error budgets on your own habits), Personal FinOps, Personal Compliance
(did-you-floss evidence packs), Life Incident Response runbooks (sick-day,
power-outage, guests-in-1-hour), and a gamification layer (XP, achievements,
streak boss-battles, household leaderboards).

---

## Delivery waves

| Wave | Scope | Approx. new UCs | Running total |
|------|-------|-----------------|---------------|
| Launch | 13 subcategories | 117 | 117 |
| Wave 1 | `25.14`–`25.19` (6 new subcats) | ~70 | ~185 |
| Wave 2 | `25.20`–`25.28` + deepen launched | ~250 | ~435 |
| Wave 3 | `25.29`–`25.40` + deepen | ~350 | ~785 |
| Stretch | `25.41`–`25.60` + meta layer | ~500 | ~1,300+ |

Each wave ships as its own branch/PR with a version bump, reusing the launch
mechanics checklist. Because everything stays inside `cat-25`, there is **no
category-count churn** — waves only add subcategory blocks, new sourcetypes, NTV
coverage, and regenerated reports.

## Per-wave mechanics checklist

1. Author UCs (schema-valid, anti-pattern-free, unique grandma openers).
2. Add subcategory blocks to `_category.json`; update every `useCaseCount` + total;
   refresh `content/INDEX.md`.
3. Register new sourcetypes in `_spl_well_known.py`.
4. Add NTV blocks; `emit:legacy` → `non-technical-view.js`.
5. Version bump (`VERSION`, `CHANGELOG.md`, `index.html` release notes,
   `openapi.yaml`, `CITATION.cff`, `ROADMAP.md`); update `docs/PITCH.md` count.
6. Regenerate derived artefacts: `make build`, `make sync-generated`, metrics
   snapshot, `attack-simulation.json`, `perf-a11y.json` (against the final build),
   `splunk-cloud-compat.md`, `splunk-version-matrix`, compliance/prerequisites.
7. Gates: `make audit`, affected `pytest`, `apps/web` typecheck+test, then confirm
   all CI checks green before merge.

## Risks / notes

- **Retrieval-eval baseline** needs regenerating after each large corpus jump.
- **`dist/catalog.json` perf budget** grows every wave — regenerate `perf-a11y.json`
  last, against the final build, or the `frontend` CI job drifts.
- **Depth vs breadth:** waves optimise breadth; an optional depth-lift pass (the
  gold-standard lift-loop) can raise depth scores to rival `cat-24`'s polish.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (Eds.). (2016). *Site Reliability Engineering: How Google Runs Production Systems*. O'Reilly Media. ISBN 978-1491929124. https://sre.google/sre-book/table-of-contents/

<a id="ref-2"></a>**[2]** Grafana Labs. (2026). *Grafana Documentation*. Retrieved May 11, 2026, from https://grafana.com/docs/

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<!-- END-AUTOGENERATED-SOURCES -->
