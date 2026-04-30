var detailOpen = false;
var detailEntry = null;
var _detailScrollPos = 0;

function fillDetailPane(e) {
  var uc = e.uc;
  var pane = document.getElementById('detail-pane');
  if (!pane) return;

  var html = '<div class="dp-header">';
  html += '<div class="dp-id">UC-' + esc(uc.i) + ' · ' + esc(e.cat.n) + ' · ' + esc(e.sc.n) + '</div>';
  html += '<div class="dp-title">' + esc(uc.n) + '</div>';
  html += '<div class="dp-badges">';
  html += critBadge(uc.c) + ' ' + diffBadge(uc.f);
  if (uc.wv && WAVE_LABELS[uc.wv]) html += ' ' + waveBadge(uc.wv);
  if (uc._qt) {
    var tierLabel = uc._qt === 'gold' ? 'Deep' : uc._qt === 'silver' ? 'Solid' : uc._qt === 'bronze' ? 'Basic' : 'Stub';
    html += ' <span class="uc-card-depth depth-' + esc(uc._qt) + '">' + esc(tierLabel) + '</span>';
  }
  if (uc.status) html += ' <span class="uc-card-status ' + esc(uc.status) + '">' + esc(uc.status) + '</span>';
  var dpProvCode = (window.PROVENANCE && window.PROVENANCE[uc.i]) || null;
  if (dpProvCode) {
    var dpProvLabel = (window.PROVENANCE_LABELS && window.PROVENANCE_LABELS[dpProvCode]) || 'Source';
    html += ' <span class="uc-card-prov prov-' + esc(dpProvCode) + '">' + esc(dpProvLabel) + '</span>';
  }
  html += '</div>';
  var metaParts = [];
  if (uc.mtype && uc.mtype.length) metaParts.push(esc(uc.mtype.join(', ')));
  if (uc.pillar) metaParts.push(esc(uc.pillar));
  if (uc.sver) metaParts.push(esc(uc.sver));
  if (uc.reviewed) metaParts.push(esc(uc.reviewed) + ' ' + freshChipHtml(uc.reviewed));
  if (uc.rby) metaParts.push('by ' + esc(uc.rby));
  if (uc.ind) metaParts.push(esc(uc.ind));
  if (uc.sdomain) metaParts.push(esc(uc.sdomain));
  if (uc.dtype) metaParts.push(esc(uc.dtype));
  if (uc._qt && uc._qs) metaParts.push(uc._qs + '/100');
  if (metaParts.length) html += '<div class="dp-meta-line">' + metaParts.join(' · ') + '</div>';
  html += '<a class="dp-link" href="uc/UC-' + esc(uc.i) + '/" target="_blank" rel="noopener">' + si('external') + ' Open full page</a>';
  html += '</div>';

  if (uc.ge) {
    html += '<div class="dp-ge"><div class="dp-ge-label">In plain language</div><div class="dp-ge-body">' + renderMd(uc.ge) + '</div></div>';
  }

  var isThin = !uc._qt || uc._qt === 'none' || uc._qt === 'bronze';
  if (isThin && !uc.md && !uc.q) {
    html += '<div class="dp-thin"><div class="dp-thin-title">This use case needs more detail</div><p>Help improve it — <a href="' + esc(githubIssueUrlForEntry(e)) + '" target="_blank" rel="noopener">suggest edits on GitHub</a>.</p></div>';
  }

  if (uc._qg && uc._qg.length) {
    html += '<div class="c-panel-section quality-callout"><div class="c-panel-section-title">Quality gaps</div><div class="c-panel-section-body"><ul>';
    uc._qg.forEach(function(g) { html += '<li>' + esc(g) + '</li>'; });
    html += '</ul></div></div>';
  }

  html += renderImplementationOrdering(uc);

  if (uc.v) html += '<div class="dp-section"><div class="dp-section-title">Value</div><div class="dp-section-body">' + renderMd(uc.v) + '</div></div>';

  if (uc.mitre && uc.mitre.length) {
    html += '<div class="dp-section"><div class="dp-section-title">MITRE ATT&CK</div><div class="dp-section-body">';
    uc.mitre.forEach(function(tid) {
      html += '<button type="button" class="linkish" onclick="filterByMitreId(\'' + esc(tid) + '\')">' + esc(tid) + '</button> ';
    });
    html += '</div></div>';
  }

  if (uc.regs && uc.regs.length) {
    html += '<div class="dp-section"><div class="dp-section-title">Regulations</div><div class="dp-section-body">';
    uc.regs.forEach(function(r) {
      html += '<button type="button" class="linkish" onclick="filterByRegEnc(\'' + encodeURIComponent(r).replace(/'/g, '%27') + '\')">' + esc(r) + '</button> ';
    });
    html += '</div></div>';
  }

  if (Array.isArray(uc.cmp) && uc.cmp.length) {
    html += '<div class="dp-section"><div class="dp-section-title">Compliance clauses</div><div class="dp-section-body">';
    html += '<div class="uc-compliance-table-wrap"><table class="uc-compliance-table">';
    html += '<thead><tr><th>Regulation</th><th>Clause</th><th>Mode</th><th>Assurance</th><th>Control objective</th><th>Evidence artefact</th></tr></thead><tbody>';
    uc.cmp.forEach(function(row) {
      if (!row) return;
      var canonical = (row.v || '') + '#' + (row.cl || '');
      var regEnc = encodeURIComponent(row.r || '').replace(/'/g, '%27');
      var clauseEnc = encodeURIComponent(canonical).replace(/'/g, '%27');
      var clauseCell = esc(row.cl || '');
      if (row.u) clauseCell = '<a href="' + esc(row.u) + '" target="_blank" rel="noopener noreferrer">' + clauseCell + '</a>';
      if (row.v) clauseCell += ' <span class="uc-compliance-ver">(' + esc(row.v) + ')</span>';
      html += '<tr>';
      html += '<td><button type="button" class="linkish" onclick="filterByRegEnc(\'' + regEnc + '\')">' + esc(row.r || '') + '</button></td>';
      html += '<td>' + clauseCell + ' <button type="button" class="linkish uc-compliance-filter-clause" onclick="filterByClauseEnc(\'' + regEnc + '\',\'' + clauseEnc + '\')">filter</button></td>';
      html += '<td>' + (row.m ? '<span class="uc-compliance-mode mode-' + esc(row.m) + '">' + esc(row.m) + '</span>' : '') + '</td>';
      html += '<td>' + (row.a ? '<span class="uc-compliance-assurance assurance-' + esc(row.a) + '">' + esc(row.a) + '</span>' : '') + '</td>';
      html += '<td>' + (row.co ? esc(row.co) : '<span class="uc-compliance-missing">—</span>') + '</td>';
      html += '<td>' + (row.ea ? esc(row.ea) : '<span class="uc-compliance-missing">—</span>') + '</td>';
      html += '</tr>';
    });
    html += '</tbody></table></div></div></div>';
  }

  if (uc.a && uc.a.length) {
    html += '<div class="dp-section"><div class="dp-section-title">CIM models</div><div class="dp-section-body">';
    uc.a.forEach(function(m) { html += '<a href="' + esc(cimDocUrl(m)) + '" target="_blank" rel="noopener">' + esc(m) + '</a> '; });
    html += '</div></div>';
  }

  html += '<div class="dp-section"><div class="dp-section-title">App / TA</div><div class="dp-section-body">';
  var taText = uc.t ? stripMd(uc.t) : '';
  if (uc.ta_link && uc.ta_link.url) {
    html += '<a href="' + esc(uc.ta_link.url) + '" target="_blank" rel="noopener" class="splunk-app-link ta-card">';
    html += '<span class="splunk-ta-icon">' + si('data') + '</span>';
    html += '<span class="splunk-ta-info"><span class="splunk-ta-label">Technology Add-on</span>';
    html += '<strong>' + esc(uc.ta_link.name || taText) + '</strong>';
    if (taText && uc.ta_link.name) html += '<span class="splunk-app-desc">' + esc(taText) + '</span>';
    html += '</span><span class="splunk-app-arrow">' + si('external') + '</span></a>';
  } else if (taText) {
    html += '<div class="splunk-ta-card"><span class="splunk-ta-icon">' + si('data') + '</span>';
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
        html += ' (archived on Splunkbase).</div>';
      }
    });
  }
  html += '</div></div>';

  if (uc.d) html += '<div class="dp-section"><div class="dp-section-title">Data sources</div><div class="dp-section-body"><code>' + esc(stripMd(uc.d)) + '</code></div></div>';
  if (uc.e && uc.e.length) {
    html += '<div class="dp-section"><div class="dp-section-title">Equipment</div><div class="dp-section-body">';
    uc.e.forEach(function(eid) { var eq = _eqById[eid]; html += esc(eq ? eq.label : eid) + '<br>'; });
    html += '</div></div>';
  }
  if (uc.em && uc.em.length) {
    html += '<div class="dp-section"><div class="dp-section-title">Equipment models</div><div class="dp-section-body">';
    uc.em.forEach(function(mid) { html += esc(mid) + '<br>'; });
    html += '</div></div>';
  }
  if (uc.premium) html += '<div class="dp-section"><div class="dp-section-title">Premium Apps</div><div class="dp-section-body">' + esc(uc.premium) + '</div></div>';
  if (uc.reqf) html += '<div class="dp-section"><div class="dp-section-title">Required fields</div><div class="dp-section-body"><code>' + esc(uc.reqf) + '</code></div></div>';
  if (uc.schema) html += '<div class="dp-section"><div class="dp-section-title">Schema</div><div class="dp-section-body"><code>' + esc(uc.schema) + '</code></div></div>';

  function copyBlock(label, text, id) {
    if (!text) return '';
    return '<div class="dp-section"><div class="dp-section-title">' + label + '</div><div class="code-wrap"><pre class="c-spl-block" id="' + id + '">' + esc(text) + '</pre><button type="button" class="copy-btn" onclick="copyCode(this)">Copy</button></div></div>';
  }
  html += copyBlock('SPL query', uc.q, 'copy-q');
  html += copyBlock('tstats query', uc.qs, 'copy-qs');
  html += copyBlock('Script example', uc.script, 'copy-script');

  if (uc.m) html += '<div class="dp-section"><div class="dp-section-title">Implementation</div><div class="dp-section-body">' + renderMd(uc.m) + '</div></div>';
  if (uc.md) html += '<div class="dp-section"><div class="dp-section-title">Detailed implementation</div><div class="dp-section-body">' + renderMd(uc.md) + '</div></div>';
  if (uc.kfp) html += '<div class="dp-section"><div class="dp-section-title">Known false positives</div><div class="dp-section-body">' + renderMd(uc.kfp) + '</div></div>';
  if (uc.refs) html += '<div class="dp-section"><div class="dp-section-title">References</div><div class="dp-section-body">' + renderMd(uc.refs) + '</div></div>';
  if (uc.dma) html += '<div class="dp-section"><div class="dp-section-title">Data model acceleration</div><div class="dp-section-body">' + renderMd(uc.dma) + '</div></div>';

  if (uc.z) {
    html += '<div class="dp-section"><div class="dp-section-title">Visualization</div><div class="dp-section-body">' + renderMd(uc.z) + '</div>';
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
        html += '<div class="app-screenshots-section"><div class="app-screenshots-title">App Dashboard Examples</div><div class="app-screenshots-grid">';
        allScreenshots.forEach(function(s) {
          html += '<a href="' + esc(s.url) + '" target="_blank" rel="noopener" class="app-screenshot-card" title="' + esc(s.app) + '">';
          html += '<img src="' + esc(s.src) + '" alt="' + esc(s.app) + ' dashboard" loading="lazy">';
          html += '<span class="app-screenshot-label">' + esc(s.app) + '</span></a>';
        });
        html += '</div></div>';
      }
    }
    if (!hasScreenshots && typeof ntVizMockups === 'function') {
      html += '<div class="app-screenshots-section"><div class="app-screenshots-title">Example Dashboard Layout</div>' + ntVizMockups(uc.z) + '</div>';
    }
    html += '</div>';
  }
  if (uc.tuc) html += '<div class="dp-section"><div class="dp-section-title">Telco use case</div><div class="dp-section-body">' + renderMd(uc.tuc) + '</div></div>';

  var ucDocs = typeof UC_DOC_MAP !== 'undefined' && UC_DOC_MAP[uc.i];
  if (ucDocs && ucDocs.length) {
    html += '<div class="dp-section"><div class="dp-section-title">Related Documentation</div><div style="display:flex;flex-wrap:wrap;gap:6px">';
    ucDocs.forEach(function(d) { html += '<a class="c-doc-chip" href="guide-reader.html?src=' + esc(d.path) + '">' + esc(d.title) + '</a>'; });
    html += '</div></div>';
  }

  html += '<div class="c-panel-gh"><a class="c-btn c-btn-secondary" href="' + esc(githubIssueUrlForEntry(e)) + '" target="_blank" rel="noopener">Report issue on GitHub</a></div>';
  pane.innerHTML = html;
  pane.scrollTop = 0;
}

function renderCondensedList() {
  var list = document.getElementById('detail-list');
  if (!list) return;

  var catName = detailEntry ? detailEntry.cat.n : '';
  var scName = detailEntry ? detailEntry.sc.n : '';
  var html = '<div class="dl-heading">';
  html += '<div class="dl-heading-cat">' + esc(catName) + '</div>';
  if (scName) html += '<div class="dl-heading-sc">' + esc(scName) + '</div>';
  html += '</div>';

  var lastSc = '';
  panelUCList.forEach(function(e, idx) {
    if (e.sc.n !== lastSc) {
      lastSc = e.sc.n;
      html += '<div class="dl-sc-divider">' + esc(e.sc.n) + '</div>';
    }
    var cls = 'dl-item' + (detailEntry && detailEntry.uc.i === e.uc.i ? ' active' : '');
    html += '<div class="' + cls + '" data-idx="' + idx + '" onclick="openDetailByIdx(' + idx + ')">';
    html += '<span class="uc-crit-dot c-' + esc(e.uc.c || 'low') + '"></span>';
    html += '<span class="dl-item-name">' + esc(e.uc.n) + '</span>';
    html += '</div>';
  });

  list.innerHTML = html;
  var active = list.querySelector('.dl-item.active');
  if (active) active.scrollIntoView({ block: 'nearest' });
}

function _scopeListToCategory(entry) {
  var cat = getCatById(entry.cat.i);
  if (!cat) return;
  var entries = [];
  var newIdx = 0;
  cat.s.forEach(function(sc) {
    sc.u.forEach(function(uc) {
      if (uc.i === entry.uc.i) newIdx = entries.length;
      entries.push({ uc: uc, cat: cat, sc: sc });
    });
  });
  panelUCList = entries;
  currentDisplayedList = entries;
  panelIdx = newIdx;
}

function openDetail(entry) {
  if (window.innerWidth < 768) {
    window.location.href = 'uc/UC-' + entry.uc.i + '/';
    return;
  }
  _detailScrollPos = window.scrollY;
  detailEntry = entry;
  detailOpen = true;
  panelOpen = true;
  currentCat = entry.cat.i;
  currentSubcat = null;
  _scopeListToCategory(entry);
  document.body.classList.add('detail-open');
  fillDetailPane(entry);
  renderCondensedList();
  buildSidebar();
  history.pushState({ uc: entry.uc.i }, '', '#uc-' + entry.uc.i);
  if (typeof window.__ensureFullUC === 'function') {
    var ucIdAtOpen = entry.uc.i;
    window.__ensureFullUC(entry.uc.i).then(function() {
      if (!detailOpen || !detailEntry || detailEntry.uc.i !== ucIdAtOpen) return;
      fillDetailPane(detailEntry);
    }).catch(function() {});
  }
}

function openDetailByIdx(idx) {
  var e = panelUCList[idx];
  if (!e) return;
  panelIdx = idx;
  detailEntry = e;
  fillDetailPane(e);
  renderCondensedList();
  history.pushState({ uc: e.uc.i }, '', '#uc-' + e.uc.i);
  var pane = document.getElementById('detail-pane');
  if (pane) pane.scrollTop = 0;
  if (typeof window.__ensureFullUC === 'function') {
    var ucIdAtOpen = e.uc.i;
    window.__ensureFullUC(e.uc.i).then(function() {
      if (!detailOpen || !detailEntry || detailEntry.uc.i !== ucIdAtOpen) return;
      fillDetailPane(detailEntry);
    }).catch(function() {});
  }
}

function closeDetail() {
  detailOpen = false;
  panelOpen = false;
  detailEntry = null;
  document.body.classList.remove('detail-open');
  window.scrollTo(0, _detailScrollPos);
  updateHash(true);
}

function openPanel(idx) {
  panelIdx = idx;
  var e = panelUCList[idx];
  if (!e) return;
  openDetail(e);
}

function navPanel(dir) {
  var n = panelIdx + dir;
  if (n >= 0 && n < panelUCList.length) {
    panelIdx = n;
    openDetailByIdx(n);
  }
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
  closeDetail();
  currentMitreFilter = id;
  currentMitreTacticFilter = '';
  currentCat = null;
  currentSearch = '';
  document.getElementById('search-input').value = '';
  reRender();
  updateHash(false);
}

function filterByReg(r) {
  closeDetail();
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
  closeDetail();
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

function _applyDetailList(entries) {
  if (!entries.length) return;
  panelUCList = entries;
  currentDisplayedList = entries;
  panelIdx = 0;
  detailEntry = entries[0];
  fillDetailPane(detailEntry);
  renderCondensedList();
  history.pushState({ uc: detailEntry.uc.i }, '', '#uc-' + detailEntry.uc.i);
  var pane = document.getElementById('detail-pane');
  if (pane) pane.scrollTop = 0;
  buildSidebar();
  if (typeof window.__ensureFullUC === 'function') {
    var ucIdAtOpen = detailEntry.uc.i;
    window.__ensureFullUC(detailEntry.uc.i).then(function() {
      if (!detailOpen || !detailEntry || detailEntry.uc.i !== ucIdAtOpen) return;
      fillDetailPane(detailEntry);
    }).catch(function() {});
  }
}

function switchDetailCategory(catId) {
  var cat = getCatById(catId);
  if (!cat) return;
  var entries = [];
  cat.s.forEach(function(sc) {
    sc.u.forEach(function(uc) { entries.push({ uc: uc, cat: cat, sc: sc }); });
  });
  _applyDetailList(entries);
}

function switchDetailSubcat(catId, scId) {
  var cat = getCatById(catId);
  if (!cat) return;
  var entries = [];
  cat.s.forEach(function(sc) {
    if (String(sc.i) !== String(scId)) return;
    sc.u.forEach(function(uc) { entries.push({ uc: uc, cat: cat, sc: sc }); });
  });
  if (!entries.length) { switchDetailCategory(catId); return; }
  _applyDetailList(entries);
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
  panelIdx = idx;
  openDetail(panelUCList[idx]);
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

function setBrowseMode(mode) {
  currentBrowseMode = mode;
  try { localStorage.setItem('uc-browse-mode', mode); } catch (e) {}
  reRender();
}
