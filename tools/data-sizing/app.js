/* ═══════════════════════════════════════════════════════════
   OT Data Sizing Assessment — Application Logic
   ═══════════════════════════════════════════════════════════ */

(function () {
  "use strict";

  // ── State ──
  // Array of instance objects. Each instance has a unique instanceId.
  // Endpoint sources: { instanceId, source, endpoints, epsProfile, customEps, customBytes }
  // Protocol sources: { instanceId, source, tags, pollSec, customBytes }
  let instances = [];
  let nextInstanceId = 1;

  const CATEGORY_DOT_CLASS = {
    "Security Sources":       "cat-dot-security",
    "IT Systems & Hardware":  "cat-dot-it",
    "OT System Sources":      "cat-dot-ot-systems",
    "Network Sources":        "cat-dot-network",
    "OT Hardware & Sensors":  "cat-dot-ot-hw",
    "Protocols":              "cat-dot-protocols",
    "Business & Compliance":  "cat-dot-business",
    "Cisco Products":         "cat-dot-cisco",
    "OT Vendor Systems":      "cat-dot-ot-vendor"
  };

  const SECONDS_PER_DAY = 86400;
  const BYTES_PER_GB    = 1e9;

  // ── v2 engine pipeline (spec §7) ──────────────────────────────────────
  // The catalogue file (`ot-data-sources.js`) became pure data after the
  // Task 2 migration. Every helper that v1 used to expose from there
  // (`getCategories`, `getSourcesByCategory`, `SPLUNK_LICENSE_TIERS`,
  // `recommendLicenseTier`) is owned by app.js from v2 onward.
  //
  // Task 8: the global profile is now user-changeable. It lives in
  // `PROFILE_REF.value` and is read via the `PROFILE()` getter so the
  // engine + renderers stay agnostic of who mutated it. The Profile
  // dropdown in the Sizing Assumptions panel writes it.
  const PROFILE_REF = { value: "typical" };
  function PROFILE() { return PROFILE_REF.value; }

  const CLUSTER = {
    rf: 2, sf: 2, smartstore: false, indexerCount: 3,
    burst: 1.5, headroom: 1.25, retentionDays: 30
  };

  const SPLUNK_LICENSE_TIERS = [
    { gb_per_day: 0.5,  label: "0.5 GB/day", tier: "Entry",       typical_use: "Pilot, lab, or single small service" },
    { gb_per_day: 1,    label: "1 GB/day",   tier: "Entry",       typical_use: "Single-site pilot or proof-of-concept" },
    { gb_per_day: 2,    label: "2 GB/day",   tier: "Entry",       typical_use: "Small team / single department" },
    { gb_per_day: 5,    label: "5 GB/day",   tier: "Small",       typical_use: "Single site, limited sources" },
    { gb_per_day: 10,   label: "10 GB/day",  tier: "Small",       typical_use: "Single site with moderate visibility" },
    { gb_per_day: 25,   label: "25 GB/day",  tier: "Medium",      typical_use: "Multi-site or full single-site deployment" },
    { gb_per_day: 50,   label: "50 GB/day",  tier: "Medium",      typical_use: "Multi-site with full security + ops telemetry" },
    { gb_per_day: 100,  label: "100 GB/day", tier: "Large",       typical_use: "Enterprise with firewalls + flow data" },
    { gb_per_day: 200,  label: "200 GB/day", tier: "Large",       typical_use: "Enterprise multi-site with full IT/OT/security" },
    { gb_per_day: 500,  label: "500 GB/day", tier: "Enterprise",  typical_use: "Large enterprise with full telemetry" },
    { gb_per_day: 1000, label: "1 TB/day",   tier: "Enterprise+", typical_use: "Major enterprise with NetFlow + full logging" },
    { gb_per_day: 2000, label: "2 TB/day",   tier: "Enterprise+", typical_use: "Global enterprise, maximum visibility" }
  ];

  function recommendLicenseTier(totalGBPerDay) {
    for (var i = 0; i < SPLUNK_LICENSE_TIERS.length; i++) {
      if (totalGBPerDay <= SPLUNK_LICENSE_TIERS[i].gb_per_day) return SPLUNK_LICENSE_TIERS[i];
    }
    return SPLUNK_LICENSE_TIERS[SPLUNK_LICENSE_TIERS.length - 1];
  }

  function getCategories() {
    var sources = window.OT_DATA_SOURCES || [];
    var seen = {};
    var out = [];
    for (var i = 0; i < sources.length; i++) {
      var c = sources[i].category;
      if (!seen[c]) { seen[c] = true; out.push(c); }
    }
    return out;
  }

  function getSourcesByCategory(category) {
    var sources = window.OT_DATA_SOURCES || [];
    return sources.filter(function (s) { return s.category === category; });
  }

  function runComputeForInstance(entry, profile) {
    profile = profile || PROFILE();
    var src = entry.source;
    var fn = (window.COMPUTE_FUNCTIONS || {})[src.compute];
    if (typeof fn !== "function") {
      console.error("Unknown compute function: " + src.compute + " on source " + src.id);
      return { eps: 0, bytesPerEvent: 0 };
    }
    // Merge driver defaults <- profile presets <- user overrides.
    var driverValues = {};
    (src.drivers || []).forEach(function (d) {
      var presets = d.profilePresets || {};
      var override = entry.driverValues && entry.driverValues[d.id];
      var v;
      if (override !== undefined) {
        v = override;
      } else if (presets[profile] !== undefined) {
        v = presets[profile];
      } else {
        v = d.default;
      }
      driverValues[d.id] = v;
    });
    var out = fn(driverValues, profile);
    var u = (src.uncertainty || {})[profile] || 1.0;
    return { eps: out.eps * u, bytesPerEvent: out.bytesPerEvent };
  }

  // ── DOM refs ──
  // v2: the per-source `<table>` is gone — `#cardList` (a flex column
  // of `.config-card` divs) replaces it. `$cardList` itself is bound
  // later, after the renderer is defined, so the event-handler block
  // can sit alongside the listeners it owns.
  const $catalog       = document.getElementById("catalogAccordion");
  const $configWrap    = document.getElementById("configTableWrap");
  const $emptyState    = document.getElementById("emptyState");
  const $selectedCount = document.getElementById("selectedCount");
  const $searchInput   = document.getElementById("catalogSearch");

  // Task 9: the v1 KPI cards + "Breakdown by Category" /
  // "Ingest Method Summary" sections have been deleted from the DOM
  // and replaced by `#resultsBlock` populated from `renderResultsBlock`.

  // Task 8: sizing-assumptions panel controls.
  const $globalProfile = document.getElementById("globalProfile");
  const $burstFactor   = document.getElementById("burstFactor");
  const $headroom      = document.getElementById("headroomFactor");
  const $retentionDays = document.getElementById("retentionDays");
  const $rf            = document.getElementById("rfFactor");
  const $sf            = document.getElementById("sfFactor");
  const $smartStore    = document.getElementById("smartStore");
  const $indexerCount  = document.getElementById("indexerCount");
  const $resultsBlock  = document.getElementById("resultsBlock");

  const $modalOverlay = document.getElementById("sourceModal");
  const $modalTitle   = document.getElementById("modalTitle");
  const $modalBody    = document.getElementById("modalBody");

  // ── Helpers ──
  function isProtocol(src) { return src.source_type === "protocol"; }
  function findInstance(iid) { return instances.find(i => i.instanceId === iid); }

  function hasEndpointInstance(sourceId) {
    return instances.some(i => i.source.id === sourceId && !isProtocol(i.source));
  }

  // ═══════════════════════════════════════════════════════════
  //  BUILD CATALOG ACCORDION
  // ═══════════════════════════════════════════════════════════

  // Task 9: catalogue browser now respects a calibration filter and
  // shows a coverage stat. Stored at module scope so the change handler
  // can mutate it without leaving the IIFE.
  var CATALOGUE_FILTER = { calibrated: true, pending: true };

  function renderCatalogueHeader() {
    var all = window.OT_DATA_SOURCES || [];
    var cal = all.filter(function (s) { return s.calibration === "calibrated"; }).length;
    var pct = all.length ? Math.round(cal / all.length * 100) : 0;
    var $h = document.querySelector(".catalog-header");
    if (!$h) return;
    var $stat = document.getElementById("calStat");
    if (!$stat) {
      $stat = document.createElement("div");
      $stat.id = "calStat";
      $stat.className = "cal-stat";
      $h.appendChild($stat);
    }
    $stat.innerHTML =
      '<div class="cal-stat-bar">Calibration ' + cal + ' / ' + all.length + ' (' + pct + '%)</div>' +
      '<div class="cal-filter">' +
        '<label><input type="checkbox" id="filtCal" ' + (CATALOGUE_FILTER.calibrated ? 'checked' : '') + '> Calibrated</label>' +
        '<label><input type="checkbox" id="filtPend" ' + (CATALOGUE_FILTER.pending ? 'checked' : '') + '> Pending</label>' +
      '</div>';
    document.getElementById("filtCal").addEventListener("change", function (e) {
      CATALOGUE_FILTER.calibrated = e.target.checked;
      buildCatalog($searchInput.value);
    });
    document.getElementById("filtPend").addEventListener("change", function (e) {
      CATALOGUE_FILTER.pending = e.target.checked;
      buildCatalog($searchInput.value);
    });
  }

  function buildCatalog(filter) {
    $catalog.innerHTML = "";
    const categories = getCategories();
    const lowerFilter = (filter || "").toLowerCase();

    categories.forEach(cat => {
      let sources = getSourcesByCategory(cat);
      if (lowerFilter) {
        sources = sources.filter(s =>
          s.name.toLowerCase().includes(lowerFilter) ||
          s.description.toLowerCase().includes(lowerFilter) ||
          (s.vendor_examples || "").toLowerCase().includes(lowerFilter) ||
          s.protocol.toLowerCase().includes(lowerFilter) ||
          s.subcategory.toLowerCase().includes(lowerFilter)
        );
      }
      // Calibration filter applies after the text filter so the search
      // box still finds calibration-filtered sources by name; if the
      // user hides everything we just render an empty list.
      sources = sources.filter(function (s) {
        if (s.calibration === "calibrated" && !CATALOGUE_FILTER.calibrated) return false;
        if (s.calibration === "pending"    && !CATALOGUE_FILTER.pending)    return false;
        return true;
      });
      if (sources.length === 0) return;

      const dotClass = CATEGORY_DOT_CLASS[cat] || "";
      const group = document.createElement("div");
      group.className = "cat-group" + (lowerFilter ? " open" : "");

      group.innerHTML = `
        <div class="cat-group-header">
          <span><span class="cat-dot ${dotClass}"></span>${cat} (${sources.length})</span>
          <span class="chevron">▶</span>
        </div>
        <div class="cat-group-body"></div>
      `;

      const body = group.querySelector(".cat-group-body");
      sources.forEach(src => {
        const proto = isProtocol(src);
        const isAdded = !proto && hasEndpointInstance(src.id);
        const instanceCount = instances.filter(i => i.source.id === src.id).length;

        const card = document.createElement("div");
        card.className = "source-card" + (isAdded ? " added" : "");
        card.dataset.id = src.id;

        const addLabel = proto
          ? `+ Add${instanceCount > 0 ? " (" + instanceCount + ")" : ""}`
          : (isAdded ? "✓ Added" : "+ Add");

        const commBadge = proto && src.comm_model
          ? `<span class="tag tag-protocol">${src.comm_model}</span>` : "";

        // Per-source calibration badge — single-letter form to fit
        // beside the source name without overflowing the catalog tile.
        const calBadgeLabel = src.calibration === "calibrated" ? "Calib" : "Pend";
        const calBadgeCls   = src.calibration === "calibrated" ? "cal-ok" : "cal-pending";

        card.innerHTML = `
          <div class="source-info">
            <div class="source-name">${src.name}<span class="cal-badge cal-mini ${calBadgeCls}">${calBadgeLabel}</span>${proto ? '<span class="proto-label">Protocol</span>' : ""}</div>
            <div class="source-sub">${src.subcategory} — ${src.description.length > 80 ? src.description.substring(0, 80) + '\u2026' : src.description}</div>
            <div class="source-meta">
              <span class="tag tag-protocol">${src.protocol}</span>
              <span class="tag tag-ingest">${src.ingest_method.split(",")[0].trim()}</span>
              ${commBadge}
            </div>
          </div>
          <div class="source-actions">
            <button class="btn btn-add btn-add-toggle" data-id="${src.id}">${addLabel}</button>
            <button class="btn btn-info btn-detail" data-id="${src.id}" title="View details">ⓘ</button>
          </div>
        `;
        body.appendChild(card);
      });

      group.querySelector(".cat-group-header").addEventListener("click", () => {
        group.classList.toggle("open");
      });

      $catalog.appendChild(group);
    });

    renderCatalogueHeader();
  }

  $searchInput.addEventListener("input", () => buildCatalog($searchInput.value));

  // ═══════════════════════════════════════════════════════════
  //  ADD / REMOVE INSTANCE
  // ═══════════════════════════════════════════════════════════

  function addSource(id) {
    var src = (window.OT_DATA_SOURCES || []).find(function (s) { return s.id === id; });
    if (!src) return;
    // v2: every entry carries a driverValues bag. Empty = use the
    // driver's `profilePresets[PROFILE]` (or `default` as a last
    // resort). Task 7's per-source card writes into this bag.
    instances.push({
      instanceId: nextInstanceId++,
      source: src,
      driverValues: {}
    });
    refreshAll();
  }

  function removeInstance(iid) {
    instances = instances.filter(i => i.instanceId !== iid);
    refreshAll();
  }

  // ═══════════════════════════════════════════════════════════
  //  INSTANCE CALCULATIONS
  // ═══════════════════════════════════════════════════════════

  // v2: raw EPS (after uncertainty, before filterable_fraction).
  function getInstanceEps(entry)   { return runComputeForInstance(entry).eps; }
  function getInstanceBytes(entry) { return runComputeForInstance(entry).bytesPerEvent; }

  // v2: effective EPS = raw × (1 - filterable_fraction). This is what
  // matters for license sizing (filtered events never hit indexers).
  function getInstanceEffectiveEps(entry) {
    var r = runComputeForInstance(entry);
    var f = (entry.source.realism || {}).filterable_fraction_typical || 0;
    return r.eps * (1 - f);
  }

  function getInstanceGBDay(entry) {
    var eps = getInstanceEffectiveEps(entry);
    var bpe = getInstanceBytes(entry);
    return (eps * SECONDS_PER_DAY * bpe) / BYTES_PER_GB;
  }

  // ═══════════════════════════════════════════════════════════
  //  RENDER CONFIG TABLE
  // ═══════════════════════════════════════════════════════════

  // v2: per-source cards. One card per instance; driver inputs come
  // straight from `source.drivers` so adding a calibrated source with
  // new drivers (e.g. `tls_fraction`) auto-renders without UI work.
  function renderCardList() {
    var count = instances.length;
    $selectedCount.textContent = count + " source" + (count !== 1 ? "s" : "");
    $emptyState.style.display = count === 0 ? "" : "none";
    $configWrap.style.display = count === 0 ? "none" : "";

    var cards = document.getElementById("cardList");
    cards.innerHTML = "";

    instances.forEach(function (entry) {
      var s = entry.source;
      var r = runComputeForInstance(entry, PROFILE());
      var filt = (s.realism || {}).filterable_fraction_typical || 0;
      var effEps = r.eps * (1 - filt);
      var gbDay = (effEps * SECONDS_PER_DAY * r.bytesPerEvent) / BYTES_PER_GB;
      var iid = entry.instanceId;
      var dotClass = CATEGORY_DOT_CLASS[s.category] || "";
      var calBadge = (s.calibration === "calibrated")
          ? '<span class="cal-badge cal-ok">Calibrated \u00B7 ' + (s.citations || []).length + ' src</span>'
          : '<span class="cal-badge cal-pending">\u26A0 Calibration pending</span>';

      var card = document.createElement("div");
      // NB: `config-card` not `source-card` — the catalog browser already
      // owns `.source-card` for its picker tiles and the two stylings
      // collide.
      card.className = "config-card";
      card.dataset.iid = iid;
      card.innerHTML =
        '<div class="card-header">' +
          '<div class="card-title">' +
            '<span class="cat-dot ' + dotClass + '"></span>' + s.name + ' ' + calBadge +
            '<button class="btn-card-remove" data-iid="' + iid + '" title="Remove">&times;</button>' +
          '</div>' +
          '<div class="card-sub">' + s.category + ' \u203A ' + s.subcategory + '</div>' +
        '</div>' +
        '<div class="card-drivers">' + renderDriverInputs(entry) + '</div>' +
        '<div class="card-estimate">' +
          '\u2192 Estimate: ' +
          '<span class="est-num">' + formatNumber(effEps, 0) + '</span> EPS \u00B7 ' +
          '<span class="est-num">' + formatBytes(r.bytesPerEvent) + '</span>/event \u00B7 ' +
          '<span class="est-num">' + gbDay.toFixed(2) + '</span> GB/day' +
        '</div>' +
        '<details class="card-disclosure">' +
          '<summary>\u25B8 Why these numbers? <span class="ds-meta">' +
            (s.calibration === "calibrated"
              ? (s.citations || []).length + ' citations \u00B7 formula \u00B7 realism'
              : 'no citations yet \u00B7 formula \u00B7 realism') +
          '</span></summary>' +
          '<div class="ds-body">' + renderDisclosure(entry) + '</div>' +
        '</details>';
      cards.appendChild(card);
    });
  }

  function renderDriverInputs(entry) {
    return (entry.source.drivers || []).map(function (d) {
      var presets = d.profilePresets || {};
      var override = entry.driverValues && entry.driverValues[d.id];
      var cur = (override !== undefined) ? override
              : (presets[PROFILE()] !== undefined ? presets[PROFILE()] : d.default);
      var labelExtra = d.unit ? ' <span class="driver-unit">' + d.unit + '</span>' : '';
      var help = d.help
                  ? ' <span class="driver-help" title="' + String(d.help).replace(/"/g, "&quot;") + '">\u24D8</span>'
                  : '';

      if (d.type === "number") {
        var minAttr = d.min !== undefined ? ' min="' + d.min + '"' : '';
        var maxAttr = d.max !== undefined ? ' max="' + d.max + '"' : '';
        var preset = presets[PROFILE()];
        var hint = preset !== undefined
                    ? '<span class="driver-hint">(typical: ' + preset + ')</span>'
                    : '<span class="driver-hint"></span>';
        return '<label class="driver-row">' +
                 '<span class="driver-label">' + d.label + labelExtra + help + '</span>' +
                 '<input type="number"' + minAttr + maxAttr + ' step="any" value="' + cur + '"' +
                       ' data-iid="' + entry.instanceId + '" data-field="' + d.id + '">' +
                 hint +
               '</label>';
      }
      // enum
      var opts = (d.options || []).map(function (o) {
        var sel = String(o.value) === String(cur) ? ' selected' : '';
        return '<option value="' + o.value + '"' + sel + '>' + o.label + '</option>';
      }).join('');
      return '<label class="driver-row">' +
               '<span class="driver-label">' + d.label + labelExtra + help + '</span>' +
               '<select data-iid="' + entry.instanceId + '" data-field="' + d.id + '">' + opts + '</select>' +
               '<span class="driver-hint"></span>' +
             '</label>';
    }).join('');
  }

  function renderDisclosure(entry) {
    var s = entry.source;
    var html = '<div class="ds-formula">Formula (<code>' + s.compute + '</code>): see <code>compute-functions.js</code></div>';
    if (s.calibration === "calibrated" && (s.citations || []).length > 0) {
      html += '<div class="ds-section-title">Citations</div><ol class="ds-citations">';
      s.citations.forEach(function (c) {
        var note = c.note ? '<div class="ds-note">' + c.note + '</div>' : '';
        html += '<li><strong>' + c.type + '</strong> \u2014 ' +
                '<a href="' + c.url + '" target="_blank" rel="noopener">' + c.url + '</a> ' +
                '<span class="ds-accessed">(accessed ' + c.accessed + ')</span>' + note + '</li>';
      });
      html += '</ol>';
    } else {
      html += '<div class="ds-warning">\u26A0 Calibration pending \u2014 these numbers are a best-effort port from the v1 catalogue. No vendor citations have been gathered yet.</div>';
    }
    var r = s.realism || {};
    var rc = Math.round((r.rawdata_compression_typical || 0) * 100);
    var ts = Math.round((r.tsidx_overhead_typical || 0) * 100);
    var ff = Math.round((r.filterable_fraction_typical || 0) * 100);
    html += '<div class="ds-section-title">Realism factors</div>' +
            '<div>Compression on-disk: rawdata ' + rc + '% + tsidx ' + ts + '% = ' + (rc + ts) + '% of raw</div>' +
            '<div>Filtering at ingest: ~' + ff + '% of events droppable at SC4S / Edge Processor</div>';
    return html;
  }

  // ═══════════════════════════════════════════════════════════
  //  TOTALS + SUMMARY
  // ═══════════════════════════════════════════════════════════

  // v2 cluster math (spec §7.3). Returns both v2 totals (totalRawEps,
  // totalEffectiveEps, totalDailyRawGB, totalClusterRawGB, …) and v1-named
  // aliases (totalEps, totalGBDay) so the legacy export path and any
  // not-yet-rewritten callers still get a number while Tasks 7–10 land.
  function computeTotals() {
    var totalRawEps = 0;
    var totalEffectiveEps = 0;
    var totalDailyRawGB = 0;
    var totalClusterRawGB = 0;
    var totalClusterTsidxGB = 0;
    var byCat = {}, byIngest = {};

    instances.forEach(function (entry) {
      var s = entry.source;
      var r = runComputeForInstance(entry);
      var filt = (s.realism || {}).filterable_fraction_typical || 0;
      var effEps = r.eps * (1 - filt);
      var gbDay = (effEps * SECONDS_PER_DAY * r.bytesPerEvent) / BYTES_PER_GB;

      var rawdataC = (s.realism || {}).rawdata_compression_typical || 0.15;
      var tsidxC   = (s.realism || {}).tsidx_overhead_typical      || 0.35;
      var rfMul = CLUSTER.smartstore ? 1 : CLUSTER.rf;
      var clusterRaw   = gbDay * rawdataC * rfMul;
      var clusterTsidx = gbDay * tsidxC   * CLUSTER.sf;

      totalRawEps         += r.eps;
      totalEffectiveEps   += effEps;
      totalDailyRawGB     += gbDay;
      totalClusterRawGB   += clusterRaw;
      totalClusterTsidxGB += clusterTsidx;

      byCat[s.category] = (byCat[s.category] || 0) + gbDay;
      var method = ((s.ingest_method || "Unknown").split(",")[0].split("/")[0]).trim();
      byIngest[method] = (byIngest[method] || 0) + gbDay;
    });

    var diurnalPeakEps  = totalEffectiveEps * CLUSTER.burst;
    var headroomPeakEps = diurnalPeakEps    * CLUSTER.headroom;
    var totalClusterGB  = totalClusterRawGB + totalClusterTsidxGB;
    var perIndexerGB    = totalClusterGB / Math.max(1, CLUSTER.indexerCount);

    return {
      // v2 surface (spec §7.3)
      totalRawEps: totalRawEps,
      totalEffectiveEps: totalEffectiveEps,
      totalDailyRawGB: totalDailyRawGB,
      diurnalPeakEps: diurnalPeakEps,
      headroomPeakEps: headroomPeakEps,
      totalClusterRawGB: totalClusterRawGB,
      totalClusterTsidxGB: totalClusterTsidxGB,
      totalClusterGB: totalClusterGB,
      perIndexerGB: perIndexerGB,
      byCat: byCat,
      byIngest: byIngest,
      // v1 aliases (kept so the not-yet-rewritten exportReport still runs)
      totalEps: totalEffectiveEps,
      totalGBDay: totalDailyRawGB
    };
  }

  // Task 9: renderSummary is now a thin alias for renderResultsBlock so
  // existing call sites (addSource / removeInstance / refreshAll /
  // assumptions-panel listeners) keep working without churn.
  function renderSummary() { renderResultsBlock(); }

  // Weighted-by-GB-day rawdata-compression average across the selected
  // instances. Used in the Results block's "Compressed raw" line so the
  // summary reflects whatever the user has in front of them rather
  // than a global default. Falls back to 0.15 when nothing is selected.
  function averageRawdata() {
    if (instances.length === 0) return 0.15;
    var tot = 0, w = 0;
    instances.forEach(function (e) {
      var gb = getInstanceGBDay(e);
      tot += gb * ((e.source.realism || {}).rawdata_compression_typical || 0.15);
      w   += gb;
    });
    return w > 0 ? tot / w : 0.15;
  }

  // Render the Results block in the Sizing Summary panel.
  // Reads totals from `computeTotals()` (spec §7.3) and renders five
  // sub-sections: Ingest, License, Storage (cluster-wide), Breakdown by
  // Category, and Ingest Method Summary.
  function renderResultsBlock() {
    if (!$resultsBlock) return;

    if (instances.length === 0) {
      $resultsBlock.innerHTML = '<div class="rb-empty">Add one or more sources from the catalog to see ingest, license, and storage estimates.</div>';
      return;
    }

    var t = computeTotals();
    var lic = recommendLicenseTier(t.totalDailyRawGB);
    var licIdx = SPLUNK_LICENSE_TIERS.indexOf(lic);
    var nextTier = licIdx >= 0 ? SPLUNK_LICENSE_TIERS[licIdx + 1] : null;
    var utilPct = lic.gb_per_day > 0 ? Math.round(t.totalDailyRawGB / lic.gb_per_day * 100) : 0;
    var headroomToNext = nextTier ? (nextTier.gb_per_day - t.totalDailyRawGB).toFixed(1) : "\u2014";

    var eff = formatCompact(t.totalEffectiveEps);
    var raw = formatCompact(t.totalRawEps);
    var dailyEv = formatCompact(t.totalEffectiveEps * SECONDS_PER_DAY);

    var peak = t.totalEffectiveEps * CLUSTER.burst;
    var peakHr = peak * CLUSTER.headroom;

    var tsidxDay = t.totalClusterTsidxGB.toFixed(1);
    var totDay = t.totalClusterGB.toFixed(1);
    var totRet = (t.totalClusterGB * CLUSTER.retentionDays).toFixed(0);
    var perIdxDay = t.perIndexerGB.toFixed(1);
    var perIdxRet = (t.perIndexerGB * CLUSTER.retentionDays).toFixed(0);
    // averageRawdata() returns the user-weighted compression; included as a
    // tooltip on the Compressed-raw row so callers can audit the implied %.
    var avgRaw = Math.round(averageRawdata() * 100);

    var catRows = Object.entries(t.byCat).sort(function (a, b) { return b[1] - a[1]; })
      .map(function (entry) {
        var cat = entry[0], gb = entry[1];
        var dot = CATEGORY_DOT_CLASS[cat] || "";
        var pct = t.totalDailyRawGB > 0 ? (gb / t.totalDailyRawGB * 100).toFixed(1) : "0";
        return '<div class="rb-row"><span><span class="cat-dot ' + dot + '"></span>' + cat + '</span>' +
               '<span>' + gb.toFixed(2) + ' GB (' + pct + '%)</span></div>';
      }).join("");

    var ingestRows = Object.entries(t.byIngest).sort(function (a, b) { return b[1] - a[1]; })
      .map(function (entry) {
        var m = entry[0], gb = entry[1];
        var pct = t.totalDailyRawGB > 0 ? (gb / t.totalDailyRawGB * 100).toFixed(1) : "0";
        return '<div class="rb-row"><span>' + m + '</span>' +
               '<span>' + gb.toFixed(2) + ' GB (' + pct + '%)</span></div>';
      }).join("");

    $resultsBlock.innerHTML =
      '<div class="rb-section">' +
        '<div class="rb-title">Ingest</div>' +
        '<div class="rb-row"><span>Sources selected</span><span>' + instances.length + '</span></div>' +
        '<div class="rb-row"><span>Effective EPS (post-filter)</span><span>' + eff + ' <em>raw pre-filter ' + raw + '</em></span></div>' +
        '<div class="rb-row"><span>Daily events</span><span>' + dailyEv + '</span></div>' +
        '<div class="rb-row"><span>Daily raw ingest</span><span>' + t.totalDailyRawGB.toFixed(2) + ' GB/day</span></div>' +
        '<div class="rb-row"><span>Diurnal peak EPS</span><span>' + formatCompact(peak) + ' <em>(burst \u00D7' + CLUSTER.burst + ')</em></span></div>' +
        '<div class="rb-row"><span>Peak EPS w/ headroom</span><span>' + formatCompact(peakHr) + ' <em>(\u00D7' + CLUSTER.headroom + ')</em></span></div>' +
      '</div>' +
      '<div class="rb-section">' +
        '<div class="rb-title">License</div>' +
        '<div class="rb-row"><span>Recommended tier</span><span>' + lic.label + ' <em>(' + lic.tier + ')</em></span></div>' +
        '<div class="rb-row"><span>Utilization</span><span>' + utilPct + '% of recommended tier</span></div>' +
        '<div class="rb-row"><span>Headroom to next tier</span><span>' + (headroomToNext === "\u2014" ? "\u2014" : headroomToNext + ' GB/day') + '</span></div>' +
      '</div>' +
      '<div class="rb-section">' +
        '<div class="rb-title">Storage (cluster-wide \u00B7 RF=' + CLUSTER.rf + ' \u00B7 SF=' + CLUSTER.sf + (CLUSTER.smartstore ? ' \u00B7 SmartStore' : '') + ')</div>' +
        '<div class="rb-row" title="' + avgRaw + '% weighted-average rawdata compression"><span>Compressed raw</span>' +
          '<span>' + t.totalClusterRawGB.toFixed(1) + ' GB/day \u2192 ' + (t.totalClusterRawGB * CLUSTER.retentionDays).toFixed(0) + ' GB / ' + CLUSTER.retentionDays + ' d</span></div>' +
        '<div class="rb-row"><span>TSIDX</span>' +
          '<span>' + tsidxDay + ' GB/day \u2192 ' + (t.totalClusterTsidxGB * CLUSTER.retentionDays).toFixed(0) + ' GB / ' + CLUSTER.retentionDays + ' d</span></div>' +
        '<div class="rb-row rb-total"><span>Total cluster-wide</span>' +
          '<span>' + totDay + ' GB/day \u2192 ' + totRet + ' GB / ' + CLUSTER.retentionDays + ' d</span></div>' +
        '<div class="rb-row"><span>Per indexer (' + CLUSTER.indexerCount + ' idx)</span>' +
          '<span>' + perIdxDay + ' GB/day \u2192 ' + perIdxRet + ' GB / ' + CLUSTER.retentionDays + ' d</span></div>' +
      '</div>' +
      (catRows ? '<div class="rb-section"><div class="rb-title">Breakdown by Category</div>' + catRows + '</div>' : '') +
      (ingestRows ? '<div class="rb-section"><div class="rb-title">Ingest Method Summary</div>' + ingestRows + '</div>' : '');
  }

  // ═══════════════════════════════════════════════════════════
  //  REFRESH
  // ═══════════════════════════════════════════════════════════

  function refreshAll() {
    renderCardList();
    renderSummary();
    buildCatalog($searchInput.value);
  }

  // ═══════════════════════════════════════════════════════════
  //  SOURCE DETAIL MODAL
  // ═══════════════════════════════════════════════════════════

  function showSourceDetail(id) {
    const s = OT_DATA_SOURCES.find(src => src.id === id);
    if (!s) return;
    const proto = isProtocol(s);
    $modalTitle.textContent = s.name;

    let html = `
      <div class="detail-row"><span class="detail-label">Category</span><span class="detail-value">${s.category} › ${s.subcategory}</span></div>
      <div class="detail-row"><span class="detail-label">Description</span><span class="detail-value">${s.description}</span></div>
      <div class="detail-row"><span class="detail-label">Vendor Examples</span><span class="detail-value">${s.vendor_examples || "—"}</span></div>
      <div class="detail-row"><span class="detail-label">Protocol</span><span class="detail-value">${s.protocol}</span></div>
      <div class="detail-row"><span class="detail-label">Ingest Method</span><span class="detail-value">${s.ingest_method}</span></div>
      <div class="detail-row"><span class="detail-label">Splunk Sourcetype</span><span class="detail-value"><code>${s.splunk_sourcetype}</code></span></div>
    `;

    if (proto) {
      html += `
        <div class="detail-row"><span class="detail-label">Comm Model</span><span class="detail-value">${s.comm_model}</span></div>
        <h3 style="margin-top:20px; font-size:13px; font-weight:700; color:var(--text-secondary);">Bytes per Tag/Topic (JSON event)</h3>
        <div class="detail-range">
          <div class="range-box"><div class="rl">Low</div><div class="rv">${formatBytes(s.bytes_per_tag.low)}</div></div>
          <div class="range-box" style="border-color:var(--cisco-blue);"><div class="rl">Typical</div><div class="rv">${formatBytes(s.bytes_per_tag.typical)}</div></div>
          <div class="range-box"><div class="rl">High</div><div class="rv">${formatBytes(s.bytes_per_tag.high)}</div></div>
        </div>
        <div class="detail-row" style="margin-top:16px;"><span class="detail-label">Default Tags</span><span class="detail-value">${s.default_tags}</span></div>
        <div class="detail-row"><span class="detail-label">Default Poll Interval</span><span class="detail-value">${s.default_poll_sec}s</span></div>
        <div class="detail-row"><span class="detail-label">Sizing Formula</span><span class="detail-value"><code>EPS = tags ÷ poll_interval_sec</code><br><code>GB/day = EPS × 86400 × bytes/tag ÷ 1e9</code></span></div>
      `;
    } else {
      html += `
        <h3 style="margin-top:20px; font-size:13px; font-weight:700; color:var(--text-secondary);">Bytes per Event</h3>
        <div class="detail-range">
          <div class="range-box"><div class="rl">Low</div><div class="rv">${formatBytes(s.bytes_per_event.low)}</div></div>
          <div class="range-box" style="border-color:var(--cisco-blue);"><div class="rl">Typical</div><div class="rv">${formatBytes(s.bytes_per_event.typical)}</div></div>
          <div class="range-box"><div class="rl">High</div><div class="rv">${formatBytes(s.bytes_per_event.high)}</div></div>
        </div>
        <h3 style="margin-top:20px; font-size:13px; font-weight:700; color:var(--text-secondary);">Events/sec per Endpoint</h3>
        <div class="detail-range">
          <div class="range-box"><div class="rl">Low</div><div class="rv">${s.eps_per_endpoint.low}</div></div>
          <div class="range-box" style="border-color:var(--cisco-blue);"><div class="rl">Typical</div><div class="rv">${s.eps_per_endpoint.typical}</div></div>
          <div class="range-box"><div class="rl">High</div><div class="rv">${s.eps_per_endpoint.high}</div></div>
        </div>
        <div class="detail-row" style="margin-top:16px;"><span class="detail-label">Default Endpoints</span><span class="detail-value">${s.default_endpoints}</span></div>
      `;
    }

    if (s.notes) html += `<div class="notes-box"><strong>Sizing Notes:</strong> ${s.notes}</div>`;

    if (s.related_uc_ids && s.related_uc_ids.length > 0) {
      html += `<div class="notes-box" style="margin-top:12px; border-color:var(--cisco-blue);">`;
      html += `<strong>Related Use Cases:</strong> `;
      html += s.related_uc_ids.map(id =>
        `<a href="../../#uc-${id}" target="_blank" rel="noopener" style="color:var(--cisco-blue); text-decoration:none; margin-right:8px;" title="Open UC-${id} in Use Case Catalog">UC-${id}</a>`
      ).join('');
      html += `</div>`;
    }

    $modalBody.innerHTML = html;
    $modalOverlay.style.display = "";
  }

  // ═══════════════════════════════════════════════════════════
  //  EXPORT REPORT
  // ═══════════════════════════════════════════════════════════

  function csvCell(val) {
    var s = String(val);
    if (s.indexOf('"') !== -1 || s.indexOf(',') !== -1 || s.indexOf('\n') !== -1 || s.indexOf('\r') !== -1) {
      return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
  }
  function csvRow(fields) { return fields.map(csvCell).join(',') + '\r\n'; }

  function exportReport() {
    if (instances.length === 0) { alert("No sources selected."); return; }

    const { totalEps, totalGBDay, byCat, byIngest } = computeTotals();
    const retDays = parseInt($retentionDays.value);
    const burst   = parseFloat($burstFactor.value);
    const peakGB  = totalGBDay * burst;
    const rawGB   = totalGBDay * retDays;
    const diskGB  = rawGB * 0.5;
    const license = recommendLicenseTier(peakGB);
    const now     = new Date().toISOString().replace("T", " ").substring(0, 19);

    let csv = '';

    csv += csvRow(['Sizing Summary','Value']);
    csv += csvRow(['Report Generated', now]);
    csv += csvRow(['Total Daily Ingest (GB/day)', totalGBDay.toFixed(2)]);
    csv += csvRow(['Total Events/sec', totalEps.toFixed(1)]);
    csv += csvRow(['Total Events/day', Math.round(totalEps * SECONDS_PER_DAY)]);
    csv += csvRow(['Peak Daily Ingest (' + burst + 'x burst)', peakGB.toFixed(2) + ' GB/day']);
    csv += csvRow(['Recommended License', license.label + ' (' + license.tier + ')']);
    csv += csvRow(['Retention Period', retDays + ' days']);
    csv += csvRow(['Raw Storage', rawGB.toFixed(1) + ' GB']);
    csv += csvRow(['Estimated Disk (50% compression)', diskGB.toFixed(1) + ' GB']);
    csv += '\r\n';

    csv += csvRow(['Category','GB/Day','Percentage']);
    Object.entries(byCat).sort((a, b) => b[1] - a[1]).forEach(([cat, gb]) => {
      const pct = totalGBDay > 0 ? (gb / totalGBDay * 100).toFixed(1) + '%' : '0%';
      csv += csvRow([cat, gb.toFixed(2), pct]);
    });
    csv += '\r\n';

    csv += csvRow(['Ingest Method','GB/Day','Percentage']);
    Object.entries(byIngest).sort((a, b) => b[1] - a[1]).forEach(([m, gb]) => {
      const pct = totalGBDay > 0 ? (gb / totalGBDay * 100).toFixed(1) + '%' : '0%';
      csv += csvRow([m, gb.toFixed(2), pct]);
    });
    csv += '\r\n';

    // v2 per-source rows. `Drivers (k=v)` enumerates every driver with
    // its effective value (override → profile preset → default), so the
    // CSV is self-describing for review without the catalogue in hand.
    csv += csvRow(['Source','Category','Subcategory','Calibration','Compute','Drivers (k=v)','Raw EPS','Effective EPS','Bytes/Event','GB/Day','Sourcetype']);
    var profile = PROFILE();
    instances.forEach(function (entry) {
      var s = entry.source;
      var out = runComputeForInstance(entry, profile);
      var filt = (s.realism || {}).filterable_fraction_typical || 0;
      var effEps = out.eps * (1 - filt);
      var gbDay  = (effEps * SECONDS_PER_DAY * out.bytesPerEvent) / BYTES_PER_GB;
      var kv = (s.drivers || []).map(function (d) {
        var v;
        if (entry.driverValues && entry.driverValues[d.id] !== undefined) {
          v = entry.driverValues[d.id];
        } else if (d.profilePresets && d.profilePresets[profile] !== undefined) {
          v = d.profilePresets[profile];
        } else {
          v = d.default;
        }
        return d.id + "=" + v;
      }).join("; ");
      csv += csvRow([
        s.name,
        s.category,
        s.subcategory,
        s.calibration || "pending",
        s.compute || "",
        kv,
        out.eps.toFixed(1),
        effEps.toFixed(1),
        out.bytesPerEvent,
        gbDay.toFixed(2),
        s.splunk_sourcetype || ""
      ]);
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `OT_Data_Sizing_Report_${new Date().toISOString().substring(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ═══════════════════════════════════════════════════════════
  //  FORMATTERS
  // ═══════════════════════════════════════════════════════════

  function formatNumber(n, decimals) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
    return n.toFixed(decimals !== undefined ? decimals : 0);
  }

  function formatCompact(n) {
    if (n >= 1e12) return (n / 1e12).toFixed(1) + " T";
    if (n >= 1e9)  return (n / 1e9).toFixed(1) + " B";
    if (n >= 1e6)  return (n / 1e6).toFixed(1) + " M";
    if (n >= 1e3)  return (n / 1e3).toFixed(1) + " K";
    return n.toFixed(1);
  }

  function formatBytes(b) {
    if (b >= 1024) return (b / 1024).toFixed(1) + " KB";
    return b + " B";
  }

  // ═══════════════════════════════════════════════════════════
  //  EVENT HANDLERS
  // ═══════════════════════════════════════════════════════════

  $catalog.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-add-toggle");
    if (btn) {
      const id = btn.dataset.id;
      const src = OT_DATA_SOURCES.find(s => s.id === id);
      if (src && !isProtocol(src) && hasEndpointInstance(id)) {
        removeInstance(instances.find(i => i.source.id === id).instanceId);
      } else {
        addSource(id);
      }
      return;
    }
    const infoBtn = e.target.closest(".btn-detail");
    if (infoBtn) showSourceDetail(infoBtn.dataset.id);
  });

  // v2: writes the coerced value into entry.driverValues[fieldName].
  // The field name comes straight from the driver `id` in the catalogue,
  // so Task 7's renderer only has to emit `data-field="<driver.id>"` on
  // each input. Coercion + min/max clamping happens here so the engine
  // can stay pure.
  function applyFieldToState(el) {
    var iid = parseInt(el.dataset.iid, 10);
    var field = el.dataset.field;
    if (!iid || !field) return null;
    var entry = findInstance(iid);
    if (!entry) return null;
    var driver = (entry.source.drivers || []).find(function (d) { return d.id === field; });
    if (!driver) return null;
    var raw = el.value;
    var v;
    if (driver.type === "number") {
      v = parseFloat(raw);
      if (Number.isNaN(v)) v = driver.default;
      if (driver.min !== undefined && v < driver.min) v = driver.min;
      if (driver.max !== undefined && v > driver.max) v = driver.max;
    } else {
      // enum — coerce to number if the option value parses cleanly so
      // numeric option values (e.g. poll_interval_sec 1/5/10/60) stay
      // numeric for the compute function.
      v = (raw !== "" && !isNaN(Number(raw))) ? Number(raw) : raw;
    }
    if (!entry.driverValues) entry.driverValues = {};
    entry.driverValues[field] = v;
    return entry;
  }

  // v2: re-render only the `.card-estimate` line of one card. Keeps
  // typing in number inputs snappy without disturbing focus / cursor.
  function rerenderOneCardEstimate(entry) {
    var card = $cardList.querySelector('.config-card[data-iid="' + entry.instanceId + '"]');
    if (!card) return;
    var est = card.querySelector(".card-estimate");
    if (!est) return;
    var r = runComputeForInstance(entry, PROFILE());
    var filt = (entry.source.realism || {}).filterable_fraction_typical || 0;
    var effEps = r.eps * (1 - filt);
    var gbDay = (effEps * SECONDS_PER_DAY * r.bytesPerEvent) / BYTES_PER_GB;
    est.innerHTML =
      '\u2192 Estimate: ' +
      '<span class="est-num">' + formatNumber(effEps, 0) + '</span> EPS \u00B7 ' +
      '<span class="est-num">' + formatBytes(r.bytesPerEvent) + '</span>/event \u00B7 ' +
      '<span class="est-num">' + gbDay.toFixed(2) + '</span> GB/day';
  }

  var $cardList = document.getElementById("cardList");

  $cardList.addEventListener("input", function (e) {
    var el = e.target;
    if (el.tagName === "SELECT") return;       // change fires on select
    if (!el.dataset || !el.dataset.field) return;
    var entry = applyFieldToState(el);
    if (entry) {
      rerenderOneCardEstimate(entry);
      renderSummary();
    }
  });

  $cardList.addEventListener("change", function (e) {
    var el = e.target;
    if (!el.dataset || !el.dataset.field) return;
    var entry = applyFieldToState(el);
    if (!entry) return;
    if (el.tagName === "SELECT") {
      // enum changes can flip downstream presets (e.g. cipher_strength
      // → bytes_per_event), so a full re-render is safest.
      renderCardList();
      renderSummary();
    } else {
      rerenderOneCardEstimate(entry);
      renderSummary();
    }
  });

  $cardList.addEventListener("click", function (e) {
    var btn = e.target.closest(".btn-card-remove");
    if (btn) removeInstance(parseInt(btn.dataset.iid, 10));
  });

  function closeModal() { $modalOverlay.style.display = "none"; }
  document.getElementById("modalClose").addEventListener("click", closeModal);
  $modalOverlay.addEventListener("click", (e) => {
    if (e.target === $modalOverlay) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && $modalOverlay.style.display !== "none") closeModal();
  });

  // ═══════════════════════════════════════════════════════════
  //  SIZING-ASSUMPTIONS PANEL — Cluster + Profile + Burst/Headroom
  // ═══════════════════════════════════════════════════════════

  // Pull every assumption value out of the DOM and mutate CLUSTER in
  // place. Called on every dropdown / checkbox / numeric change so the
  // engine sees the new values on the next render.
  function syncClusterFromUI() {
    if ($rf)            CLUSTER.rf            = parseInt($rf.value, 10) || 2;
    // SF must never exceed RF — Splunk core requirement. Clamp here so
    // even an out-of-range value loaded from a share URL stays sane.
    if ($sf)            CLUSTER.sf            = Math.min(CLUSTER.rf, parseInt($sf.value, 10) || 2);
    if ($smartStore)    CLUSTER.smartstore    = !!$smartStore.checked;
    if ($indexerCount)  CLUSTER.indexerCount  = Math.max(1, parseInt($indexerCount.value, 10) || 1);
    if ($burstFactor)   CLUSTER.burst         = parseFloat($burstFactor.value) || 1.0;
    if ($headroom)      CLUSTER.headroom      = parseFloat($headroom.value)    || 1.0;
    if ($retentionDays) CLUSTER.retentionDays = parseInt($retentionDays.value, 10) || 30;
  }

  // Disable SF options > RF and snap the current SF back to RF if needed.
  function clampSFOptionsToRF() {
    if (!$rf || !$sf) return;
    var rf = parseInt($rf.value, 10) || 2;
    Array.prototype.forEach.call($sf.options, function (o) {
      o.disabled = parseInt(o.value, 10) > rf;
    });
    if ((parseInt($sf.value, 10) || 2) > rf) $sf.value = String(rf);
  }

  [$burstFactor, $headroom, $retentionDays, $rf, $sf, $smartStore, $indexerCount].forEach(function (el) {
    if (!el) return;
    el.addEventListener("change", function () {
      syncClusterFromUI();
      refreshAll();
    });
  });

  if ($rf) {
    $rf.addEventListener("change", function () {
      clampSFOptionsToRF();
      syncClusterFromUI();
      refreshAll();
    });
  }

  if ($globalProfile) {
    $globalProfile.addEventListener("change", function () {
      PROFILE_REF.value = $globalProfile.value;
      refreshAll();
    });
  }

  // Establish the initial UI state on page load.
  clampSFOptionsToRF();
  syncClusterFromUI();

  document.getElementById("btnClearAll").addEventListener("click", () => {
    instances = [];
    refreshAll();
  });

  document.getElementById("btnExport").addEventListener("click", exportReport);

  // v2: encode current selection as `?sources=ID:k=v,k=v|ID2:…`.
  // Only emit driver overrides that actually differ from the active
  // profile preset / default; otherwise the URL stays short and
  // self-describing.
  var btnShare = document.getElementById("btnShare");
  if (btnShare) {
    btnShare.addEventListener("click", function () {
      if (instances.length === 0) {
        alert("No sources selected. Add at least one source to share a link.");
        return;
      }
      var profile = PROFILE();
      var encoded = instances.map(function (entry) {
        var pairs = [];
        (entry.source.drivers || []).forEach(function (d) {
          if (!entry.driverValues || entry.driverValues[d.id] === undefined) return;
          var current = entry.driverValues[d.id];
          var preset = (d.profilePresets && d.profilePresets[profile] !== undefined)
                         ? d.profilePresets[profile]
                         : d.default;
          if (current !== preset) pairs.push(d.id + "=" + current);
        });
        return entry.source.id + (pairs.length ? ":" + pairs.join(",") : "");
      }).join("|");
      var url = window.location.origin + window.location.pathname
              + "?sources=" + encodeURIComponent(encoded);
      var done = function (ok) {
        if (ok) alert("Share link copied to clipboard.");
        else window.prompt("Copy this link:", url);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(
          function () { done(true); },
          function () { done(false); }
        );
      } else {
        done(false);
      }
    });
  }

  // ═══════════════════════════════════════════════════════════
  //  THEME TOGGLE (shared key with main catalog)
  // ═══════════════════════════════════════════════════════════

  function applyTheme() {
    var d = document.documentElement.classList.contains('dark');
    var lbl = document.getElementById('dsa-theme-label');
    var ico = document.getElementById('dsa-theme-ico');
    if (lbl) lbl.textContent = d ? 'Light' : 'Dark';
    if (ico) ico.textContent = d ? '☀' : '☾';
  }

  function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    var d = document.documentElement.classList.contains('dark');
    try { localStorage.setItem('cisco-ui-theme', d ? 'dark' : 'light'); } catch (e) {}
    applyTheme();
  }

  var themeBtn = document.getElementById('dsa-theme-btn');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  applyTheme();

  // ═══════════════════════════════════════════════════════════
  //  INIT
  // ═══════════════════════════════════════════════════════════

  buildCatalog();
  renderSummary();

  var params = new URLSearchParams(window.location.search);
  var equipParam = params.get('equipment');
  if (equipParam) {
    var eqLabels = equipParam.split(',').filter(Boolean).map(function(id) {
      if (typeof EQUIPMENT !== 'undefined' && Array.isArray(EQUIPMENT)) {
        var obj = EQUIPMENT.find(function(e) { return e.id === id.trim(); });
        if (obj) return obj.label;
      }
      return id.trim().replace(/_/g, ' ');
    });
    if (eqLabels.length) {
      var banner = document.createElement('div');
      banner.className = 'equipment-context';
      banner.textContent = 'Equipment context: ' + eqLabels.join(', ');
      var summaryH2 = document.querySelector('.summary-panel h2');
      if (summaryH2) summaryH2.parentNode.insertBefore(banner, summaryH2.nextSibling);
    }
  }
  // v2 share-URL format. Instances are separated by '|' (was ',' in v1).
  // Per instance, optional ':k1=v1,k2=v2' overrides driver defaults.
  // Numeric drivers are coerced; unknown driver IDs are silently dropped
  // so a future catalogue can rename drivers without breaking old URLs.
  var sourcesParam = params.get('sources');
  if (sourcesParam) {
    sourcesParam.split('|').filter(Boolean).forEach(function (entry) {
      var parts = entry.split(':');
      var sid = parts[0].trim();
      addSource(sid);
      if (parts[1]) {
        var added = instances[instances.length - 1];
        if (added) {
          parts[1].split(',').forEach(function (kv) {
            var eq = kv.indexOf('=');
            if (eq <= 0) return;
            var k = kv.slice(0, eq).trim();
            var v = kv.slice(eq + 1).trim();
            var driver = (added.source.drivers || []).find(function (d) { return d.id === k; });
            if (!driver) return;
            var coerced = (driver.type === "number") ? parseFloat(v) : v;
            if (!added.driverValues) added.driverValues = {};
            added.driverValues[k] = coerced;
          });
        }
      }
    });
    refreshAll();
  }

})();
