function fillPanelBody(e) {
  var uc = e.uc;
  var html = '<div class="c-panel-meta">';
  html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Criticality</div>' + critBadge(uc.c) + '</div>';
  html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Difficulty</div>' + diffBadge(uc.f) + '</div>';
  if (uc.mtype && uc.mtype.length) html += '<div class="c-panel-meta-item full"><div class="c-panel-meta-label">Monitoring type</div><div>' + esc(uc.mtype.join(', ')) + '</div></div>';
  if (uc.pillar) html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Pillar</div><div>' + esc(uc.pillar) + '</div></div>';
  if (uc.status) html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Status</div><div><span class="uc-card-status ' + esc(uc.status) + '">' + esc(uc.status) + '</span></div></div>';
  var panelProvCode = (window.PROVENANCE && window.PROVENANCE[uc.i]) || null;
  if (panelProvCode) {
    var panelProvLabel = (window.PROVENANCE_LABELS && window.PROVENANCE_LABELS[panelProvCode]) || 'Source';
    html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Source</div><div><span class="uc-card-prov prov-' + esc(panelProvCode) + '" title="Source classification">' + esc(panelProvLabel) + '</span></div></div>';
  }
  if (uc.reviewed) html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Last reviewed</div><div>' + esc(uc.reviewed) + ' ' + freshChipHtml(uc.reviewed) + '</div></div>';
  if (uc.sver) html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Splunk versions</div><div>' + esc(uc.sver) + '</div></div>';
  if (uc.rby) html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Reviewer</div><div>' + esc(uc.rby) + '</div></div>';
  if (uc.ind) html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Industry</div><div>' + esc(uc.ind) + '</div></div>';
  if (uc.sdomain) html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Security domain</div><div>' + esc(uc.sdomain) + '</div></div>';
  if (uc.dtype) html += '<div class="c-panel-meta-item"><div class="c-panel-meta-label">Detection type</div><div>' + esc(uc.dtype) + '</div></div>';
  html += '</div>';

  if (uc.mitre && uc.mitre.length) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">MITRE ATT&CK</div><div class="c-panel-section-body">';
    uc.mitre.forEach(function(tid) {
      html += '<button type="button" class="linkish" onclick="filterByMitreId(\'' + esc(tid) + '\')">' + esc(tid) + '</button> ';
    });
    html += '</div></div>';
  }
  if (uc.regs && uc.regs.length) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">Regulations</div><div class="c-panel-section-body">';
    uc.regs.forEach(function(r) {
      html += '<button type="button" class="linkish" onclick="filterByRegEnc(\'' + encodeURIComponent(r).replace(/'/g, '%27') + '\')">' + esc(r) + '</button> ';
    });
    html += '</div></div>';
  }
  // Phase 3a — clause-level compliance table. Renders the structured
  // ``uc.cmp[]`` projection when the UC sidecar has one (v1.6.0 schema,
  // ~1,395 UCs at the time of writing). Columns reflect the three
  // audiences the redesign targets:
  //   * Clause  — what the regulator asks for (auditor/buyer anchor)
  //   * Mode    — satisfies / detects-violation-of / assists-with
  //   * Assurance — full / partial / contributing
  //   * Control objective — implementer-facing "what this UC actually does"
  //   * Evidence artefact — auditor-facing "what you can hand to the audit"
  // UCs with a flat ``regs[]`` but no ``cmp[]`` continue to show only
  // the flat chip list above, so no regression for pre-Phase-1 UCs.
  if (Array.isArray(uc.cmp) && uc.cmp.length) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">Compliance clauses</div><div class="c-panel-section-body">';
    html += '<div class="uc-compliance-table-wrap"><table class="uc-compliance-table">';
    html += '<thead><tr>';
    html += '<th scope="col">Regulation</th>';
    html += '<th scope="col">Clause</th>';
    html += '<th scope="col">Mode</th>';
    html += '<th scope="col">Assurance</th>';
    html += '<th scope="col">Control objective</th>';
    html += '<th scope="col">Evidence artefact</th>';
    html += '</tr></thead><tbody>';
    uc.cmp.forEach(function(row) {
      if (!row) return;
      var canonical = (row.v || '') + '#' + (row.cl || '');
      var regEnc = encodeURIComponent(row.r || '').replace(/'/g, '%27');
      var clauseEnc = encodeURIComponent(canonical).replace(/'/g, '%27');
      var clauseCell = esc(row.cl || '');
      if (row.u) {
        // Deep-link to the regulator's own clause page when the sidecar
        // provided one. External links always open in a new tab with
        // noopener/noreferrer per OWASP link guidance — the catalogue
        // is hosted on GitHub Pages and must not leak referrer data.
        clauseCell = '<a href="' + esc(row.u) + '" target="_blank" rel="noopener noreferrer" title="Open in new tab">' + clauseCell + '</a>';
      }
      if (row.v) clauseCell += ' <span class="uc-compliance-ver">(' + esc(row.v) + ')</span>';
      html += '<tr>';
      html += '<td><button type="button" class="linkish" onclick="filterByRegEnc(\'' + regEnc + '\')">' + esc(row.r || '') + '</button></td>';
      html += '<td>' + clauseCell + ' <button type="button" class="linkish uc-compliance-filter-clause" title="Filter catalogue by this clause" onclick="filterByClauseEnc(\'' + regEnc + '\',\'' + clauseEnc + '\')">filter</button></td>';
      html += '<td>' + (row.m ? '<span class="uc-compliance-mode mode-' + esc(row.m) + '">' + esc(row.m) + '</span>' : '') + '</td>';
      html += '<td>' + (row.a ? '<span class="uc-compliance-assurance assurance-' + esc(row.a) + '">' + esc(row.a) + '</span>' : '') + '</td>';
      html += '<td>' + (row.co ? esc(row.co) : '<span class="uc-compliance-missing">—</span>') + '</td>';
      html += '<td>' + (row.ea ? esc(row.ea) : '<span class="uc-compliance-missing">—</span>') + '</td>';
      html += '</tr>';
    });
    html += '</tbody></table></div>';
    html += '<div class="uc-compliance-footnote">Clauses without a control objective or evidence artefact are flagged for SME review (Phase 4 migration).</div>';
    html += '</div></div>';
  }
  if (uc.a && uc.a.length) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">CIM models</div><div class="c-panel-section-body">';
    uc.a.forEach(function(m) {
      var u = cimDocUrl(m);
      html += '<a href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(m) + '</a> ';
    });
    html += '</div></div>';
  }
  if (uc.v) html += '<div class="c-panel-section"><div class="c-panel-section-title">Value</div><div class="c-panel-section-body">' + esc(stripMd(uc.v)) + '</div></div>';

  html += '<div class="c-panel-section"><div class="c-panel-section-title">App / TA</div><div class="c-panel-section-body">';
  var taText = uc.t ? stripMd(uc.t) : '';
  if (uc.ta_link && uc.ta_link.url) {
    html += '<a href="' + esc(uc.ta_link.url) + '" target="_blank" rel="noopener" class="splunk-app-link ta-card">';
    html += '<span class="splunk-ta-icon">' + si('data') + '</span>';
    html += '<span class="splunk-ta-info"><span class="splunk-ta-label">Technology Add-on</span>';
    html += '<strong>' + esc(uc.ta_link.name || taText) + '</strong>';
    if (taText && uc.ta_link.name) html += '<span class="splunk-app-desc">' + esc(taText) + '</span>';
    html += '</span><span class="splunk-app-arrow">' + si('external') + '</span></a>';
  } else if (taText) {
    html += '<div class="splunk-ta-card">';
    html += '<span class="splunk-ta-icon">' + si('data') + '</span>';
    html += '<span class="splunk-ta-info"><span class="splunk-ta-label">Data Input / Add-on</span>';
    html += '<strong>' + esc(taText) + '</strong></span></div>';
  }
  if (uc.sapp && uc.sapp.length) {
    uc.sapp.forEach(function(app) {
      var id = typeof app === 'object' && app != null ? app.id : app;
      var name = typeof app === 'object' && app && app.name ? app.name : ('Splunkbase #' + id);
      var u = typeof app === 'object' && app && app.url ? app.url : ('https://splunkbase.splunk.com/app/' + id);
      var desc = typeof app === 'object' && app && app.desc ? app.desc : '';
      html += '<a href="' + esc(u) + '" target="_blank" rel="noopener" class="splunk-app-link app-card">';
      html += '<span class="splunk-app-icon">' + si('monitorChart') + '</span>';
      html += '<span class="splunk-app-info"><span class="splunk-app-label">Splunkbase App</span>';
      html += '<strong>' + esc(name) + '</strong>';
      if (desc) html += '<span class="splunk-app-desc">' + esc(desc) + '</span>';
      html += '</span><span class="splunk-app-arrow">' + si('external') + '</span></a>';
      if (typeof app === 'object' && Array.isArray(app.predecessor) && app.predecessor.length) {
        html += '<div class="predecessor-note-box">Replaces ';
        app.predecessor.forEach(function(p, pi) {
          if (pi > 0) html += ', ';
          var pUrl = typeof p === 'object' && p.url ? p.url : '#';
          var pName = typeof p === 'object' && p.name ? p.name : String(p);
          html += '<a href="' + esc(pUrl) + '" target="_blank" rel="noopener">' + esc(pName) + '</a>';
        });
        html += ' (archived on Splunkbase). The underlying TA/Add-on still works for data collection.</div>';
      }
    });
  }
  html += '</div></div>';

  if (uc.d) html += '<div class="c-panel-section"><div class="c-panel-section-title">Data sources</div><div class="c-panel-section-body"><code>' + esc(stripMd(uc.d)) + '</code></div></div>';
  if (uc.e && uc.e.length) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">Equipment</div><div class="c-panel-section-body">';
    uc.e.forEach(function(eid) { var eq = _eqById[eid]; html += esc(eq ? eq.label : eid) + '<br>'; });
    html += '</div></div>';
  }
  if (uc.em && uc.em.length) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">Equipment models</div><div class="c-panel-section-body">';
    uc.em.forEach(function(mid) { html += esc(mid) + '<br>'; });
    html += '</div></div>';
  }
  if (uc.premium) html += '<div class="c-panel-section"><div class="c-panel-section-title">Premium Apps</div><div class="c-panel-section-body">' + esc(uc.premium) + '</div></div>';
  if (uc.reqf) html += '<div class="c-panel-section"><div class="c-panel-section-title">Required fields</div><div class="c-panel-section-body"><code>' + esc(uc.reqf) + '</code></div></div>';
  if (uc.schema) html += '<div class="c-panel-section"><div class="c-panel-section-title">Schema</div><div class="c-panel-section-body"><code>' + esc(uc.schema) + '</code></div></div>';

  function copyBlock(label, text, id) {
    if (!text) return '';
    return '<div class="c-panel-section"><div class="c-panel-section-title">' + label + '</div><div class="code-wrap"><pre class="c-spl-block" id="' + id + '">' + esc(text) + '</pre><button type="button" class="copy-btn" onclick="copyCode(this)">Copy</button></div></div>';
  }
  html += copyBlock('SPL query', uc.q, 'copy-q');
  html += copyBlock('tstats query', uc.qs, 'copy-qs');
  html += copyBlock('Script example', uc.script, 'copy-script');

  if (uc.m) html += '<div class="c-panel-section"><div class="c-panel-section-title">Implementation</div><div class="c-panel-section-body">' + esc(stripMd(uc.m)) + '</div></div>';
  if (uc.md) html += '<details class="c-panel-details"><summary>Detailed implementation</summary><div class="c-panel-section-body">' + renderDetailBody(uc.md) + '</div></details>';
  if (uc.kfp) html += '<div class="c-panel-section"><div class="c-panel-section-title">Known false positives</div><div class="c-panel-section-body">' + esc(stripMd(uc.kfp)) + '</div></div>';
  if (uc.refs) html += '<div class="c-panel-section"><div class="c-panel-section-title">References</div><div class="c-panel-section-body">' + esc(stripMd(uc.refs)) + '</div></div>';
  if (uc.dma) html += '<div class="c-panel-section"><div class="c-panel-section-title">Data model acceleration</div><div class="c-panel-section-body">' + esc(stripMd(uc.dma)) + '</div></div>';
  if (uc.z) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">Visualization</div><div class="c-panel-section-body">' + esc(stripMd(uc.z)) + '</div>';
    var hasScreenshots = false;
    if (Array.isArray(uc.sapp) && uc.sapp.length) {
      var allScreenshots = [];
      uc.sapp.forEach(function(app) {
        if (typeof app === 'object' && Array.isArray(app.screenshots) && app.screenshots.length) {
          app.screenshots.forEach(function(s) { allScreenshots.push({src: s, app: app.name || '', url: app.url || '#'}); });
        }
      });
      if (allScreenshots.length) {
        hasScreenshots = true;
        html += '<div class="app-screenshots-section">';
        html += '<div class="app-screenshots-title">App Dashboard Examples</div>';
        html += '<div class="app-screenshots-grid">';
        allScreenshots.forEach(function(s) {
          html += '<a href="' + esc(s.url) + '" target="_blank" rel="noopener" class="app-screenshot-card" title="' + esc(s.app) + ' — View on Splunkbase">';
          html += '<img src="' + esc(s.src) + '" alt="' + esc(s.app) + ' dashboard screenshot" loading="lazy">';
          html += '<span class="app-screenshot-label">' + esc(s.app) + '</span></a>';
        });
        html += '</div></div>';
      }
    }
    if (!hasScreenshots && typeof ntVizMockups === 'function') {
      html += '<div class="app-screenshots-section">';
      html += '<div class="app-screenshots-title">Example Dashboard Layout</div>';
      html += ntVizMockups(uc.z);
      html += '</div>';
    }
    html += '</div>';
  }
  if (uc.tuc) html += '<div class="c-panel-section"><div class="c-panel-section-title">Telco use case</div><div class="c-panel-section-body">' + esc(stripMd(uc.tuc)) + '</div></div>';

  html += '<div class="c-panel-gh"><a class="c-btn c-btn-secondary" href="' + esc(githubIssueUrlForEntry(e)) + '" target="_blank" rel="noopener">Report issue on GitHub</a></div>';
  document.getElementById('panel-body').innerHTML = html;
}

function openPanel(idx) {
  panelIdx = idx;
  var e = panelUCList[idx];
  if (!e) return;
  panelOpen = true;
  document.getElementById('panel-id').textContent = 'UC-' + e.uc.i + ' · ' + e.cat.n + ' · ' + e.sc.n;
  document.getElementById('panel-title').textContent = e.uc.n;

  // Render whatever stub data we have immediately so the panel feels
  // responsive, then lazy-fetch the per-category JSON to merge in heavy
  // fields (full SPL, narrative, references, screenshots) and re-render.
  fillPanelBody(e);
  var pos = document.getElementById('panel-pos');
  if (pos) pos.textContent = (idx + 1) + ' / ' + panelUCList.length;
  document.getElementById('panel-backdrop').classList.add('open');
  document.body.classList.add('panel-open');
  buildSidebar();
  history.replaceState(null, '', '#uc-' + e.uc.i);

  if (typeof window.__ensureFullUC === 'function') {
    var ucIdAtOpen = e.uc.i;
    window.__ensureFullUC(e.uc.i).then(function() {
      // Bail if the user navigated away before the fetch resolved.
      if (!panelOpen || panelIdx !== idx) return;
      var current = panelUCList[panelIdx];
      if (!current || current.uc.i !== ucIdAtOpen) return;
      fillPanelBody(current);
    }).catch(function() { /* loader already logged */ });
  }
}

function closePanel() {
  document.getElementById('panel-backdrop').classList.remove('open');
  document.body.classList.remove('panel-open');
  panelOpen = false;
  updateHash(true);
}

function navPanel(dir) {
  var n = panelIdx + dir;
  if (n >= 0 && n < panelUCList.length) openPanel(n);
}

function copyCode(btn) {
  var wrap = btn.parentElement;
  var pre = wrap.querySelector('pre');
  var t = pre ? pre.textContent : '';
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(t).then(function() {
      btn.textContent = 'Copied!'; setTimeout(function() { btn.textContent = 'Copy'; }, 1500);
    }).catch(function() { _fallbackCopy(t, btn); });
  } else { _fallbackCopy(t, btn); }
}
function _fallbackCopy(text, btn) {
  var ta = document.createElement('textarea');
  ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy'); btn.textContent = 'Copied!'; } catch (e) { btn.textContent = 'Failed'; }
  document.body.removeChild(ta);
  setTimeout(function() { btn.textContent = 'Copy'; }, 1500);
}

function filterByMitreId(id) {
  closePanel();
  currentMitreFilter = id;
  currentMitreTacticFilter = '';
  currentCat = null;
  currentSearch = '';
  document.getElementById('search-input').value = '';
  reRender();
  updateHash(false);
}

function filterByReg(r) {
  closePanel();
  currentRegulationFilter = r;
  currentClauseFilter = 'all';
  currentCat = null;
  currentSearch = '';
  document.getElementById('search-input').value = '';
  reRender();
  updateHash(false);
}

function filterByRegEnc(enc) {
  try { filterByReg(decodeURIComponent(enc)); } catch (e) {}
}

function filterByClause(reg, clauseCanonical) {
  // Jumps straight into the catalogue filtered by one specific
  // (regulation, version, clause) tuple. Used by the clause-filter
  // button on the UC detail panel's compliance table so an auditor
  // reading "UC-X covers GDPR Art.5" can click through and see
  // every other UC that also covers GDPR Art.5 without manually
  // re-selecting both dropdowns. The regulation dropdown's
  // ``onchange`` normally clears the clause filter, so we set
  // regulation first and clause second.
  closePanel();
  currentRegulationFilter = reg;
  currentClauseFilter = clauseCanonical || 'all';
  currentCat = null;
  currentSearch = '';
  var siEl = document.getElementById('search-input');
  if (siEl) siEl.value = '';
  reRender();
  updateHash(false);
}

function filterByClauseEnc(regEnc, clauseEnc) {
  try { filterByClause(decodeURIComponent(regEnc), decodeURIComponent(clauseEnc)); } catch (e) {}
}

function openUCById(id) {
  panelUCList = currentDisplayedList.length ? currentDisplayedList : getFilteredUCs();
  var idx = panelUCList.findIndex(function(e) { return String(e.uc.i) === String(id); });
  if (idx < 0) {
    var entry = ucIndex[id];
    if (!entry) return;
    panelUCList = allUCs;
    idx = entry.flatIdx;
  }
  openPanel(idx);
}

function openMitreMap() {
  var body = document.getElementById('mitre-map-body');
  if (!body || !FILTER_FACETS.mitre) return;
  var filtered = getFilteredUCs();
  var isFiltered = filtered.length < allUCs.length;
  var techCounts = {};
  filtered.forEach(function(e) {
    if (Array.isArray(e.uc.mitre)) e.uc.mitre.forEach(function(t) { techCounts[t] = (techCounts[t] || 0) + 1; });
  });
  var html = '';
  if (isFiltered) html += '<div class="mitre-filtered-note">Showing counts for ' + filtered.length + ' filtered use cases</div>';
  html += '<div class="mitre-map-grid">';
  FILTER_FACETS.mitre.forEach(function(group) {
    var techSet = {};
    group.techniques.forEach(function(t) { techSet[t.id] = true; });
    var tacticCount = 0;
    filtered.forEach(function(e) {
      if (Array.isArray(e.uc.mitre) && e.uc.mitre.some(function(t) { return techSet[t]; })) tacticCount++;
    });
    html += '<div class="mitre-map-col"><div class="mitre-map-tactic" onclick="mapSelectTactic(\'' + esc(group.tactic) + '\')"><span class="mm-count">' + tacticCount + '</span>' + esc(group.label) + '</div>';
    group.techniques.forEach(function(t) {
      var c = techCounts[t.id] || 0;
      html += '<div class="mitre-map-tech' + (c === 0 ? ' zero' : '') + '" onclick="mapSelectTech(\'' + esc(t.id) + '\')"><span class="mm-tc">' + c + '</span> ' + esc(t.id) + ' ' + esc(t.name || '') + '</div>';
    });
    html += '</div>';
  });
  html += '</div>';
  body.innerHTML = html;
  document.getElementById('mitre-map-overlay').classList.add('open');
  document.body.classList.add('overlay-open');
}

function closeMitreMap() {
  document.getElementById('mitre-map-overlay').classList.remove('open');
  _maybeClearOverlayClass();
}

function mapSelectTactic(tactic) {
  closeMitreMap();
  currentMitreTacticFilter = tactic;
  currentMitreFilter = '';
  reRender();
  updateHash(false);
}

function mapSelectTech(id) {
  closeMitreMap();
  currentMitreFilter = id;
  currentMitreTacticFilter = '';
  reRender();
  updateHash(false);
}
