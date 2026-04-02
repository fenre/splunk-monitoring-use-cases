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

  // ── DOM refs ──
  const $catalog       = document.getElementById("catalogAccordion");
  const $configBody    = document.getElementById("configBody");
  const $configWrap    = document.getElementById("configTableWrap");
  const $emptyState    = document.getElementById("emptyState");
  const $selectedCount = document.getElementById("selectedCount");
  const $searchInput   = document.getElementById("catalogSearch");

  const $kpiTotalGB       = document.getElementById("kpiTotalGB");
  const $kpiTotalEPS      = document.getElementById("kpiTotalEPS");
  const $kpiTotalEventsDay= document.getElementById("kpiTotalEventsDay");
  const $kpiLicense       = document.getElementById("kpiLicense");
  const $kpiLicenseTier   = document.getElementById("kpiLicenseTier");
  const $kpiRawStorage    = document.getElementById("kpiRawStorage");
  const $kpiDiskStorage   = document.getElementById("kpiDiskStorage");
  const $kpiPeakGB        = document.getElementById("kpiPeakGB");
  const $catBreakdown     = document.getElementById("categoryBreakdown");
  const $ingestBreakdown  = document.getElementById("ingestBreakdown");
  const $retentionDays    = document.getElementById("retentionDays");
  const $burstFactor      = document.getElementById("burstFactor");

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

        card.innerHTML = `
          <div class="source-info">
            <div class="source-name">${src.name}${proto ? '<span class="proto-label">Protocol</span>' : ""}</div>
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
  }

  $searchInput.addEventListener("input", () => buildCatalog($searchInput.value));

  // ═══════════════════════════════════════════════════════════
  //  ADD / REMOVE INSTANCE
  // ═══════════════════════════════════════════════════════════

  function addSource(id) {
    const src = OT_DATA_SOURCES.find(s => s.id === id);
    if (!src) return;

    if (isProtocol(src)) {
      instances.push({
        instanceId: nextInstanceId++,
        source: src,
        tags: src.default_tags,
        pollSec: src.default_poll_sec,
        customBytes: src.bytes_per_tag.typical
      });
    } else {
      if (hasEndpointInstance(id)) return;
      instances.push({
        instanceId: nextInstanceId++,
        source: src,
        endpoints: src.default_endpoints,
        epsProfile: "typical",
        customEps: src.eps_per_endpoint.typical,
        customBytes: src.bytes_per_event.typical
      });
    }
    refreshAll();
  }

  function removeInstance(iid) {
    instances = instances.filter(i => i.instanceId !== iid);
    refreshAll();
  }

  // ═══════════════════════════════════════════════════════════
  //  INSTANCE CALCULATIONS
  // ═══════════════════════════════════════════════════════════

  function getInstanceEps(entry) {
    if (isProtocol(entry.source)) {
      return entry.tags / Math.max(entry.pollSec, 0.001);
    }
    if (entry.epsProfile === "custom") return entry.customEps * entry.endpoints;
    const epsPerEp = entry.source.eps_per_endpoint[entry.epsProfile] || entry.source.eps_per_endpoint.typical;
    return epsPerEp * entry.endpoints;
  }

  function getInstanceBytes(entry) {
    if (isProtocol(entry.source)) return entry.customBytes;
    if (entry.epsProfile === "custom") return entry.customBytes;
    return entry.source.bytes_per_event[entry.epsProfile] || entry.source.bytes_per_event.typical;
  }

  function getInstanceGBDay(entry) {
    return (getInstanceEps(entry) * SECONDS_PER_DAY * getInstanceBytes(entry)) / BYTES_PER_GB;
  }

  // ═══════════════════════════════════════════════════════════
  //  RENDER CONFIG TABLE
  // ═══════════════════════════════════════════════════════════

  function renderConfigTable() {
    const count = instances.length;
    $selectedCount.textContent = count + " source" + (count !== 1 ? "s" : "");
    $emptyState.style.display = count === 0 ? "" : "none";
    $configWrap.style.display = count === 0 ? "none" : "";

    $configBody.innerHTML = "";
    instances.forEach(entry => {
      const s = entry.source;
      const proto = isProtocol(s);
      const totalEps = getInstanceEps(entry);
      const bpe = getInstanceBytes(entry);
      const gbDay = getInstanceGBDay(entry);
      const dotClass = CATEGORY_DOT_CLASS[s.category] || "";
      const iid = entry.instanceId;

      const tr = document.createElement("tr");
      if (proto) tr.className = "proto-row";

      if (proto) {
        const pollOptions = (s.poll_presets || [1, 5, 10, 30, 60]).map(v => {
          const label = v >= 60 ? (v / 60) + "m" : v + "s";
          return `<option value="${v}" ${entry.pollSec === v ? "selected" : ""}>${label}</option>`;
        }).join("");

        tr.innerHTML = `
          <td class="source-name-cell">${s.name}<span class="proto-label">Protocol</span></td>
          <td><span class="cat-dot ${dotClass}"></span><span class="cat-label">${s.subcategory}</span></td>
          <td class="num"><input type="number" min="1" max="1000000" value="${entry.tags}" data-iid="${iid}" data-field="tags" title="Number of tags / topics / OIDs"></td>
          <td class="num">
            <select data-iid="${iid}" data-field="pollSec">${pollOptions}</select>
            <span class="poll-unit">interval</span>
          </td>
          <td>—</td>
          <td class="num"><input type="number" min="10" max="100000" step="10" value="${bpe}" data-iid="${iid}" data-field="bytes"></td>
          <td class="num eps-value num-cell">${formatNumber(totalEps, 1)}</td>
          <td class="num gb-value num-cell">${gbDay.toFixed(2)}</td>
          <td><button class="btn btn-remove" data-iid="${iid}" title="Remove">&times;</button></td>
        `;
      } else {
        const eps = entry.epsProfile === "custom"
          ? entry.customEps
          : (s.eps_per_endpoint[entry.epsProfile] || s.eps_per_endpoint.typical);

        tr.innerHTML = `
          <td class="source-name-cell">${s.name}</td>
          <td><span class="cat-dot ${dotClass}"></span><span class="cat-label">${s.subcategory}</span></td>
          <td class="num"><input type="number" min="1" max="100000" value="${entry.endpoints}" data-iid="${iid}" data-field="endpoints"></td>
          <td class="num"><input type="number" min="0.001" max="100000" step="0.1" value="${eps}" data-iid="${iid}" data-field="eps"></td>
          <td>
            <select data-iid="${iid}" data-field="epsProfile">
              <option value="low" ${entry.epsProfile === "low" ? "selected" : ""}>Low</option>
              <option value="typical" ${entry.epsProfile === "typical" ? "selected" : ""}>Typical</option>
              <option value="high" ${entry.epsProfile === "high" ? "selected" : ""}>High</option>
              <option value="custom" ${entry.epsProfile === "custom" ? "selected" : ""}>Custom</option>
            </select>
          </td>
          <td class="num"><input type="number" min="10" max="100000" step="10" value="${bpe}" data-iid="${iid}" data-field="bytes"></td>
          <td class="num eps-value num-cell">${formatNumber(totalEps, 1)}</td>
          <td class="num gb-value num-cell">${gbDay.toFixed(2)}</td>
          <td><button class="btn btn-remove" data-iid="${iid}" title="Remove">&times;</button></td>
        `;
      }
      $configBody.appendChild(tr);
    });
  }

  // ═══════════════════════════════════════════════════════════
  //  TOTALS + SUMMARY
  // ═══════════════════════════════════════════════════════════

  function computeTotals() {
    let totalEps = 0, totalGBDay = 0;
    const byCat = {}, byIngest = {};

    instances.forEach(entry => {
      const s = entry.source;
      const eps = getInstanceEps(entry);
      const gbDay = getInstanceGBDay(entry);

      totalEps += eps;
      totalGBDay += gbDay;
      byCat[s.category] = (byCat[s.category] || 0) + gbDay;

      const method = s.ingest_method.split(",")[0].split("/")[0].trim();
      byIngest[method] = (byIngest[method] || 0) + gbDay;
    });
    return { totalEps, totalGBDay, byCat, byIngest };
  }

  function renderSummary() {
    const { totalEps, totalGBDay, byCat, byIngest } = computeTotals();
    const retDays = parseInt($retentionDays.value);
    const burst   = parseFloat($burstFactor.value);
    const peakGB  = totalGBDay * burst;
    const rawGB   = totalGBDay * retDays;
    const diskGB  = rawGB * 0.5;
    const license = recommendLicenseTier(peakGB);
    const eventsDay = totalEps * SECONDS_PER_DAY;

    $kpiTotalGB.textContent        = totalGBDay.toFixed(2);
    $kpiTotalEPS.textContent       = formatNumber(totalEps, 1);
    $kpiTotalEventsDay.textContent = formatCompact(eventsDay);
    $kpiLicense.textContent        = license.label;
    $kpiLicenseTier.textContent    = license.tier + " — " + license.typical_use;
    $kpiRawStorage.textContent     = formatCompact(rawGB);
    $kpiDiskStorage.textContent    = formatCompact(diskGB);
    $kpiPeakGB.textContent         = peakGB.toFixed(2);

    $catBreakdown.innerHTML = "";
    Object.entries(byCat).sort((a, b) => b[1] - a[1]).forEach(([cat, gb]) => {
      const dotClass = CATEGORY_DOT_CLASS[cat] || "";
      const pct = totalGBDay > 0 ? (gb / totalGBDay * 100).toFixed(1) : 0;
      $catBreakdown.innerHTML += `
        <div class="breakdown-item">
          <span class="bd-label"><span class="cat-dot ${dotClass}"></span>${cat}</span>
          <span class="bd-value">${gb.toFixed(2)} GB (${pct}%)</span>
        </div>`;
    });

    $ingestBreakdown.innerHTML = "";
    Object.entries(byIngest).sort((a, b) => b[1] - a[1]).forEach(([method, gb]) => {
      const pct = totalGBDay > 0 ? (gb / totalGBDay * 100).toFixed(1) : 0;
      $ingestBreakdown.innerHTML += `
        <div class="breakdown-item">
          <span class="bd-label">${method}</span>
          <span class="bd-value">${gb.toFixed(2)} GB (${pct}%)</span>
        </div>`;
    });
  }

  // ═══════════════════════════════════════════════════════════
  //  REFRESH
  // ═══════════════════════════════════════════════════════════

  function refreshAll() {
    renderConfigTable();
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

    csv += csvRow(['Source','Category','Subcategory','Type','Protocol','Ingest Method','Endpoints/Tags','EPS or Poll Interval','Bytes/Event','Total EPS','GB/Day','Sourcetype']);
    instances.forEach(entry => {
      const s = entry.source;
      const proto = isProtocol(s);
      const totalSrcEps = getInstanceEps(entry);
      const bpe = getInstanceBytes(entry);
      const gbDay = getInstanceGBDay(entry);

      if (proto) {
        csv += csvRow([s.name, s.category, s.subcategory, 'protocol', s.protocol, s.ingest_method, entry.tags + ' tags', entry.pollSec + 's interval', bpe, totalSrcEps.toFixed(1), gbDay.toFixed(2), s.splunk_sourcetype]);
      } else {
        const epsPerEp = entry.epsProfile === "custom" ? entry.customEps : (s.eps_per_endpoint[entry.epsProfile] || s.eps_per_endpoint.typical);
        csv += csvRow([s.name, s.category, s.subcategory, 'endpoint', s.protocol, s.ingest_method, entry.endpoints + ' endpoints', epsPerEp + ' EPS/ep', bpe, totalSrcEps.toFixed(1), gbDay.toFixed(2), s.splunk_sourcetype]);
      }
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

  function applyFieldToState(el) {
    const iid = parseInt(el.dataset.iid);
    const field = el.dataset.field;
    if (!iid || !field) return null;

    const entry = findInstance(iid);
    if (!entry) return null;

    if (field === "endpoints") {
      entry.endpoints = Math.max(1, parseInt(el.value) || 1);
    } else if (field === "tags") {
      entry.tags = Math.max(1, parseInt(el.value) || 1);
    } else if (field === "eps") {
      entry.customEps = Math.max(0.001, parseFloat(el.value) || 0.001);
      entry.epsProfile = "custom";
    } else if (field === "bytes") {
      entry.customBytes = Math.max(10, parseInt(el.value) || 10);
      if (!isProtocol(entry.source)) entry.epsProfile = "custom";
    } else if (field === "pollSec") {
      entry.pollSec = parseFloat(el.value);
    } else if (field === "epsProfile") {
      entry.epsProfile = el.value;
      if (el.value !== "custom") {
        entry.customEps = entry.source.eps_per_endpoint[el.value];
        entry.customBytes = entry.source.bytes_per_event[el.value];
      }
    } else {
      return null;
    }
    return entry;
  }

  function updateRowCells(entry) {
    const row = $configBody.querySelector(`button[data-iid="${entry.instanceId}"]`);
    if (!row) return;
    const tr = row.closest("tr");
    if (!tr) return;
    const epsCell = tr.querySelector(".eps-value");
    const gbCell  = tr.querySelector(".gb-value");
    if (epsCell) epsCell.textContent = formatNumber(getInstanceEps(entry), 1);
    if (gbCell)  gbCell.textContent  = getInstanceGBDay(entry).toFixed(2);
  }

  $configBody.addEventListener("input", (e) => {
    const el = e.target;
    if (el.tagName === "SELECT") return;
    const entry = applyFieldToState(el);
    if (entry) {
      updateRowCells(entry);
      renderSummary();
    }
  });

  $configBody.addEventListener("change", (e) => {
    const el = e.target;
    const entry = applyFieldToState(el);
    if (!entry) return;
    if (el.tagName === "SELECT") {
      refreshAll();
    } else {
      updateRowCells(entry);
      renderSummary();
    }
  });

  $configBody.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-remove");
    if (btn) removeInstance(parseInt(btn.dataset.iid));
  });

  function closeModal() { $modalOverlay.style.display = "none"; }
  document.getElementById("modalClose").addEventListener("click", closeModal);
  $modalOverlay.addEventListener("click", (e) => {
    if (e.target === $modalOverlay) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && $modalOverlay.style.display !== "none") closeModal();
  });

  $retentionDays.addEventListener("change", renderSummary);
  $burstFactor.addEventListener("change", renderSummary);

  document.getElementById("btnClearAll").addEventListener("click", () => {
    instances = [];
    refreshAll();
  });

  document.getElementById("btnExport").addEventListener("click", exportReport);

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

  try {
    if (localStorage.getItem('cisco-ui-theme') === 'dark') {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {}
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
  var sourcesParam = params.get('sources');
  if (sourcesParam) {
    sourcesParam.split(',').filter(Boolean).forEach(function(id) { addSource(id.trim()); });
    refreshAll();
  }

})();
