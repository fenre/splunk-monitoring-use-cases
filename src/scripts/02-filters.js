function isEquipmentModelId(compoundId) {
  var list = EQUIPMENT || [];
  for (var i = 0; i < list.length; i++) {
    var eq = list[i];
    if (!eq.models) continue;
    for (var j = 0; j < eq.models.length; j++) {
      if (compoundId === eq.id + '_' + eq.models[j].id) return true;
    }
  }
  return false;
}

function getCatById(id) {
  if (id == null) return null;
  return DATA.find(function(c) { return c.i === id; }) || null;
}

function getFilteredUCs() {
  var result = allUCs;
  if (inventorySelections.length > 0 && !selectedEquipmentId) {
    var invSet = new Set(inventorySelections);
    var invTopIds = new Set();
    inventorySelections.forEach(function(id) { invTopIds.add(id.split('_')[0]); });
    result = result.filter(function(e) {
      var eq = e.uc.e || [];
      var em = e.uc.em || [];
      return eq.some(function(id) { return invSet.has(id) || invTopIds.has(id); })
          || em.some(function(id) { return invSet.has(id); });
    });
  }
  if (selectedEquipmentId) {
    var byModel = isEquipmentModelId(selectedEquipmentId);
    result = result.filter(function(e) {
      if (byModel) return Array.isArray(e.uc.em) && e.uc.em.indexOf(selectedEquipmentId) !== -1;
      return Array.isArray(e.uc.e) && e.uc.e.indexOf(selectedEquipmentId) !== -1;
    });
  }
  if (currentPillarFilter !== 'all') {
    result = result.filter(function(e) {
      var p = e.uc.pillar || 'observability';
      if (currentPillarFilter === 'security') return p === 'security' || p === 'both';
      if (currentPillarFilter === 'observability') return p === 'observability' || p === 'both';
      return true;
    });
  }
  if (currentRegulationFilter !== 'all') {
    // Top-level regulation filter still honours the flat ``regs[]`` list
    // for backward compatibility with UCs that don't have a structured
    // ``cmp[]`` array yet (pre-Phase-1 sidecars). UCs that *do* have a
    // ``cmp[]`` array still match here because build.py mirrors every
    // ``cmp`` row's regulation id into the flat ``regs[]`` union.
    result = result.filter(function(e) {
      return Array.isArray(e.uc.regs) && e.uc.regs.indexOf(currentRegulationFilter) !== -1;
    });
    if (currentClauseFilter && currentClauseFilter !== 'all') {
      // Second-level clause filter: only applicable when the top-level
      // regulation was chosen AND a specific ``{version}#{clause}`` tuple
      // has been selected. We split on the first ``#`` because clause
      // strings such as ``§164.312(b)`` legitimately contain ``#``-free
      // characters but could in theory include other punctuation. The
      // match is exact on regulation + version + clause — a partial
      // match would silently over-count coverage, which is the precise
      // story problem Phase 3 is meant to fix.
      var hashAt = currentClauseFilter.indexOf('#');
      if (hashAt > 0) {
        var wantVer = currentClauseFilter.slice(0, hashAt);
        var wantClause = currentClauseFilter.slice(hashAt + 1);
        result = result.filter(function(e) {
          if (!Array.isArray(e.uc.cmp)) return false;
          return e.uc.cmp.some(function(row) {
            return row
              && row.r === currentRegulationFilter
              && row.v === wantVer
              && row.cl === wantClause;
          });
        });
      }
    }
  }
  if (currentFilter !== 'all') result = result.filter(function(e) { return e.uc.c === currentFilter; });
  if (currentDiffFilter !== 'all') result = result.filter(function(e) { return e.uc.f === currentDiffFilter; });
  if (currentStatusFilter !== 'all') {
    result = result.filter(function(e) { return (e.uc.status || 'community') === currentStatusFilter; });
  }
  if (currentFreshFilter !== 'all') {
    result = result.filter(function(e) { return freshnessBucket(e.uc.reviewed) === currentFreshFilter; });
  }
  if (currentMtypeFilter !== 'all') {
    result = result.filter(function(e) { return Array.isArray(e.uc.mtype) && e.uc.mtype.indexOf(currentMtypeFilter) !== -1; });
  }
  if (currentIndustryFilter !== 'all') result = result.filter(function(e) { return e.uc.ind === currentIndustryFilter; });
  if (currentEscuFilter !== 'all') {
    result = result.filter(function(e) { return currentEscuFilter === 'yes' ? !!e.uc.escu : !e.uc.escu; });
  }
  if (currentDtypeFilter !== 'all') {
    var dtypeMethodologies = ['TTP','Anomaly','Hunting','Baseline','Correlation','Operational metrics'];
    if (currentDtypeFilter === 'TTP') {
      result = result.filter(function(e) { var d = e.uc.dtype; return d && (d === 'TTP' || dtypeMethodologies.indexOf(d) === -1); });
    } else {
      result = result.filter(function(e) { return e.uc.dtype === currentDtypeFilter; });
    }
  }
  if (currentPremiumFilter !== 'all') {
    result = result.filter(function(e) { return (e.uc.premium || '') === currentPremiumFilter; });
  }
  if (currentCimFilter !== 'all') {
    result = result.filter(function(e) {
      return Array.isArray(e.uc.a) && e.uc.a.some(function(m) { return m.split('(')[0].trim() === currentCimFilter; });
    });
  }
  if (currentSappFilter !== 'all') {
    var sappId = parseInt(currentSappFilter, 10);
    result = result.filter(function(e) {
      return Array.isArray(e.uc.sapp) && e.uc.sapp.some(function(a) { return a.id === sappId; });
    });
  }
  if (currentMitreFilter) {
    var mq = currentMitreFilter;
    result = result.filter(function(e) { return Array.isArray(e.uc.mitre) && e.uc.mitre.indexOf(mq) !== -1; });
  }
  if (currentMitreTacticFilter && typeof FILTER_FACETS !== 'undefined' && FILTER_FACETS.mitre) {
    var tacticTechs = {};
    FILTER_FACETS.mitre.forEach(function(g) { tacticTechs[g.tactic] = g.techniques.map(function(t) { return t.id; }); });
    var ids = tacticTechs[currentMitreTacticFilter] || [];
    result = result.filter(function(e) { return Array.isArray(e.uc.mitre) && e.uc.mitre.some(function(t) { return ids.indexOf(t) !== -1; }); });
  }
  if (currentDsGroup && !currentDatasourceFilter) {
    var grp = FILTER_FACETS.datasource_groups && FILTER_FACETS.datasource_groups.find(function(g) { return g.name === currentDsGroup; });
    if (grp) {
      var srcNames = grp.sources.map(function(s) { return s.name.toLowerCase(); });
      result = result.filter(function(e) {
        var d = (e.uc.d || '').toLowerCase();
        return srcNames.some(function(sn) { return d.indexOf(sn) !== -1; });
      });
    }
  } else if (currentDatasourceFilter) {
    var dq = currentDatasourceFilter.toLowerCase();
    result = result.filter(function(e) { return (e.uc.d || '').toLowerCase().indexOf(dq) !== -1; });
  }
  if (currentTrendFilter) result = result.filter(function(e) { return /\btrend/i.test(e.uc.n); });
  if (currentCat != null) result = result.filter(function(e) { return e.cat.i === currentCat; });
  if (currentSearch) {
    // Two-tier search:
    //   1) Synchronous substring scan over the in-memory _searchBlob.
    //      Always runs, returns instantly. Matches stub-level fields
    //      only (UC name, summary, source names, app names, etc.).
    //   2) Asynchronous shard-based inverted index (06-search.js).
    //      Indexes the full SPL + markdown narrative + heavy fields the
    //      stub doesn't ship. Scheduled here, results flow in via
    //      window.__onSearchResults -> reRender(); the union of (1) and
    //      the latest (2) is what the user sees.
    var qNorm = currentSearch.toLowerCase().trim();
    var words = qNorm.split(/\s+/).filter(Boolean);
    var inMem = new Set();
    for (var _si = 0; _si < result.length; _si++) {
      var _e = result[_si];
      if (words.every(function(w) { return _e._searchBlob.indexOf(w) !== -1; })) {
        inMem.add(_e.uc.i);
      }
    }
    if (window.__searchIndex && typeof window.__searchIndex.query === 'function') {
      // Schedule the async query (debounced inside the index). When it
      // resolves it calls __onSearchResults which fires reRender, and on
      // the next pass through here window.__searchAsyncResults will be
      // fresh.
      window.__searchIndex.query(qNorm);
    }
    var asyncSet = null;
    var ar = window.__searchAsyncResults;
    if (ar && ar.q === qNorm && ar.set) asyncSet = ar.set;
    result = result.filter(function(e) {
      return inMem.has(e.uc.i) || (asyncSet && asyncSet.has(e.uc.i));
    });
  }
  return result;
}

// Wired by 06-search.js once the async shard fetch resolves. The handler
// just kicks reRender(); getFilteredUCs() will then read the freshly
// published window.__searchAsyncResults on its next pass.
if (typeof window !== 'undefined') {
  window.__onSearchResults = function(q, set) {
    if (typeof currentSearch === 'undefined') return;
    if ((currentSearch || '').toLowerCase().trim() !== q) return;
    if (typeof reRender === 'function') {
      try { reRender(); } catch (e) { /* swallow */ }
    }
  };
}

function sortUCs(list, sortKey) {
  var s = sortKey || currentSort;
  return list.slice().sort(function(a, b) {
    if (s === 'criticality') return (CRIT_ORDER[a.uc.c] || 9) - (CRIT_ORDER[b.uc.c] || 9) || (DIFF_ORDER[a.uc.f] || 9) - (DIFF_ORDER[b.uc.f] || 9);
    if (s === 'difficulty') return (DIFF_ORDER[a.uc.f] || 9) - (DIFF_ORDER[b.uc.f] || 9) || (CRIT_ORDER[a.uc.c] || 9) - (CRIT_ORDER[b.uc.c] || 9);
    if (s === 'difficulty-desc') return (DIFF_ORDER[b.uc.f] || 9) - (DIFF_ORDER[a.uc.f] || 9) || (CRIT_ORDER[a.uc.c] || 9) - (CRIT_ORDER[b.uc.c] || 9);
    if (s === 'name-az') return a.uc.n.localeCompare(b.uc.n);
    if (s === 'name-za') return b.uc.n.localeCompare(a.uc.n);
    if (s === 'category') return (a.cat.i - b.cat.i) || (CRIT_ORDER[a.uc.c] || 9) - (CRIT_ORDER[b.uc.c] || 9);
    return 0;
  });
}

function critBadge(c) {
  return '<span class="c-badge c-badge-' + esc(c || 'low') + '">' + esc((c || '').charAt(0).toUpperCase() + (c || '').slice(1)) + '</span>';
}
function diffBadge(d) {
  return '<span class="c-badge c-badge-diff">' + esc((d || '').charAt(0).toUpperCase() + (d || '').slice(1)) + '</span>';
}
// Wave is the per-UC implementation tier inside the crawl/walk/run rollout
// model. Surfaces only when the curator has assigned one (uc.wv set); UCs
// without a wave never render a badge.
var WAVE_LABELS = { crawl: 'Crawl', walk: 'Walk', run: 'Run' };
var WAVE_TOOLTIPS = {
  crawl: 'Foundation wave — install the TA, turn on a base data feed, ship one panel or alert. Implement first.',
  walk: 'Intermediate wave — refines or correlates a crawl signal (anomaly detection, SLA math, cross-host roll-ups).',
  run: 'Advanced wave — depends on multiple crawls/walks, often cross-category. Implement after walk UCs are stable.'
};
function waveBadge(w) {
  var key = (w || '').toLowerCase();
  if (!WAVE_LABELS[key]) return '';
  return '<span class="c-badge c-badge-wave-' + esc(key) + '" title="' + esc(WAVE_TOOLTIPS[key]) + '">' + esc(WAVE_LABELS[key]) + '</span>';
}
// Reverse-prereq index: { 'UC-X.Y.Z': ['UC-A.B.C', ...] } where the listed
// UCs declare the key as a prerequisite. Built lazily on first use so the
// initial DATA scan in buildIndex() stays untouched, then memoised.
var _reversePrereqIndex = null;
function getReversePrereqIndex() {
  if (_reversePrereqIndex) return _reversePrereqIndex;
  _reversePrereqIndex = {};
  if (typeof DATA === 'undefined' || !Array.isArray(DATA)) return _reversePrereqIndex;
  DATA.forEach(function(cat) {
    (cat.s || []).forEach(function(sc) {
      (sc.u || []).forEach(function(uc) {
        if (!Array.isArray(uc.pre) || !uc.pre.length) return;
        var src = 'UC-' + uc.i;
        uc.pre.forEach(function(dep) {
          if (typeof dep !== 'string') return;
          (_reversePrereqIndex[dep] = _reversePrereqIndex[dep] || []).push(src);
        });
      });
    });
  });
  Object.keys(_reversePrereqIndex).forEach(function(k) {
    _reversePrereqIndex[k] = _reversePrereqIndex[k].sort();
  });
  return _reversePrereqIndex;
}
// Render an inline UC chip that opens the target UC in the side panel when
// clicked. Falls back to a plain id when the referenced UC is missing from
// the catalogue (defensive — validate_prerequisites() should already have
// failed the build, but the SPA must not crash on stale cached data.js).
function renderUCChip(ucFullId) {
  if (typeof ucFullId !== 'string' || !ucFullId.indexOf) return '';
  var bareId = ucFullId.replace(/^UC-/, '');
  var entry = (typeof ucIndex === 'object' && ucIndex) ? ucIndex[bareId] : null;
  if (!entry) {
    return '<li><span class="uc-chip" title="Unknown or removed UC">' + esc(ucFullId) + '</span></li>';
  }
  var title = entry.uc.n || '';
  var waveHtml = '';
  if (entry.uc.wv && WAVE_LABELS[entry.uc.wv]) {
    waveHtml = ' <span class="chip-wave c-badge c-badge-wave-' + esc(entry.uc.wv) + '" title="' + esc(WAVE_TOOLTIPS[entry.uc.wv]) + '">' + esc(WAVE_LABELS[entry.uc.wv]) + '</span>';
  }
  return '<li><button type="button" class="uc-chip" title="' + esc(title) + '" onclick="openUCById(\'' + esc(bareId) + '\')">' + esc(ucFullId) + waveHtml + '</button></li>';
}
function renderImplementationOrdering(uc) {
  var html = '';
  var pre = Array.isArray(uc.pre) ? uc.pre : [];
  var enables = getReversePrereqIndex()['UC-' + uc.i] || [];
  if (!pre.length && !enables.length) return '';
  if (pre.length) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">Implement first (prerequisites)</div><div class="c-panel-section-body"><ul class="uc-chip-list">';
    pre.forEach(function(p) { html += renderUCChip(p); });
    html += '</ul></div></div>';
  }
  if (enables.length) {
    html += '<div class="c-panel-section"><div class="c-panel-section-title">Enables</div><div class="c-panel-section-body"><ul class="uc-chip-list">';
    enables.forEach(function(p) { html += renderUCChip(p); });
    html += '</ul></div></div>';
  }
  return html;
}
// Per-category 'Crawl → Walk → Run' rollout rendered above the UC list.
// Reads from the precomputed ROADMAP global emitted by build.py
// (one bucket per wave, one bucket per category id). Returns '' when the
// category has no waves assigned at all so categories curators have not
// yet touched render unchanged.
function renderCategoryRoadmap(catId) {
  if (typeof ROADMAP === 'undefined' || !ROADMAP) return '';
  var buckets = ROADMAP[String(catId)];
  if (!buckets) return '';
  var crawl = Array.isArray(buckets.crawl) ? buckets.crawl : [];
  var walk = Array.isArray(buckets.walk) ? buckets.walk : [];
  var run = Array.isArray(buckets.run) ? buckets.run : [];
  var unassigned = Array.isArray(buckets.unassigned) ? buckets.unassigned : [];
  if (!crawl.length && !walk.length && !run.length) return '';
  var MAX_VISIBLE = 5;
  function chips(list) {
    if (!list.length) return '<span class="c-roadmap-empty">No UCs assigned</span>';
    var visible = list.slice(0, MAX_VISIBLE).map(renderUCChip).join('');
    var more = list.length > MAX_VISIBLE
      ? '<span class="c-roadmap-more" title="' + (list.length - MAX_VISIBLE) + ' more in this wave">+' + (list.length - MAX_VISIBLE) + '</span>'
      : '';
    return '<ul class="uc-chip-list">' + visible + '</ul>' + more;
  }
  function col(label, list, tip, withArrow) {
    return '<div class="c-roadmap-col">'
      + '<div class="c-roadmap-col-title" title="' + esc(tip) + '">'
      + esc(label) + ' <span class="c-roadmap-count">(' + list.length + ')</span>'
      + (withArrow ? ' <span class="c-roadmap-col-arrow" aria-hidden="true">→</span>' : '')
      + '</div>'
      + '<div class="c-roadmap-col-body">' + chips(list) + '</div>'
      + '</div>';
  }
  var html = '<div class="c-roadmap-band" role="group" aria-label="Implementation roadmap for this category">';
  html += col('Crawl', crawl, WAVE_TOOLTIPS.crawl, true);
  html += col('Walk', walk, WAVE_TOOLTIPS.walk, true);
  html += col('Run', run, WAVE_TOOLTIPS.run, false);
  if (unassigned.length) {
    html += '<div class="c-roadmap-unassigned">'
      + unassigned.length + ' UC(s) in this category have no wave assigned yet.'
      + '</div>';
  }
  html += '</div>';
  return html;
}

function githubIssueUrlForEntry(entry) {
  var uc = entry.uc, cat = entry.cat, sc = entry.sc;
  var repo = (SITE.siteRepoUrl || 'https://github.com/fenre/splunk-monitoring-use-cases').replace(/\/$/, '').replace(/\.git$/, '');
  var mm = repo.match(/github\.com\/([^/]+)\/([^/?#]+)/);
  var base = mm ? 'https://github.com/' + mm[1] + '/' + mm[2] : 'https://github.com/fenre/splunk-monitoring-use-cases';
  var issueTitle = '[UC Feedback] UC-' + uc.i + ' — ' + String(uc.n).replace(/[\r\n]+/g, ' ').substring(0, 100);
  var mdLink = cat.src ? (repo + '/blob/main/use-cases/' + cat.src) : (repo + '/tree/main/use-cases');
  var pageLink = '';
  try { pageLink = location.origin + location.pathname + location.search + '#uc-' + (uc.i || ''); } catch (e2) { pageLink = repo; }
  // Pre-fill the YAML issue form fields declared in
  // .github/ISSUE_TEMPLATE/use-case-feedback.yml:
  //   - uc-id      (input)
  //   - details    (textarea)
  //   - fix        (textarea)  -- left blank for the reporter
  var details = 'Category: ' + cat.i + '. ' + cat.n +
                ' / Subcategory: ' + sc.i + ' ' + sc.n + '\n\n' +
                'Source file: ' + (cat.src ? mdLink : '(unknown)') + '\n' +
                'Dashboard link: ' + pageLink + '\n\n' +
                'What is wrong?\n\n';
  var qs = [
    'template=use-case-feedback.yml',
    'title=' + encodeURIComponent(issueTitle),
    'uc-id=' + encodeURIComponent('UC-' + uc.i),
    'details=' + encodeURIComponent(details)
  ].join('&');
  return base + '/issues/new?' + qs;
}

function cimDocUrl(model) {
  var base = model.split('(')[0].trim().replace(/\s+/g, '_');
  return 'https://docs.splunk.com/Documentation/CIM/latest/User/' + encodeURIComponent(base);
}

function renderDetailBody(md) {
  if (!md) return '';
  var fence = /^```(\w*)$/;
  var lines = md.split('\n');
  var out = [];
  var inCode = false;
  var codeLang = '';
  var codeLines = [];
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    var m = line.match(fence);
    if (m) {
      if (!inCode) { inCode = true; codeLang = (m[1] || 'text').toLowerCase(); codeLines = []; }
      else {
        inCode = false;
        out.push('<pre class="c-spl-block">' + esc(codeLines.join('\n')) + '</pre>');
      }
      continue;
    }
    if (inCode) codeLines.push(line);
    else out.push(linkify(line) + '<br>');
  }
  if (inCode && codeLines.length) out.push('<pre class="c-spl-block">' + esc(codeLines.join('\n')) + '</pre>');
  return out.join('');
}
function setSort(val) {
  currentSort = val;
  try { localStorage.setItem('uc-sort-pref', val); } catch (e) {}
  reRender();
}

function setPillarFilter(val) { currentPillarFilter = val; reRender(); }
function setFilter(f) { currentFilter = f; reRender(); }
function setDiffFilter(f) { currentDiffFilter = f; reRender(); }
function setStatusFilter(f) { currentStatusFilter = f; reRender(); }
function setFreshFilter(f) { currentFreshFilter = f; reRender(); }
function freshnessBucket(iso) {
  if (!iso) return 'unknown';
  var t = Date.parse(iso);
  if (isNaN(t)) return 'unknown';
  var days = (Date.now() - t) / 86400000;
  if (days <= 183) return 'fresh';
  if (days <= 366) return 'stale';
  return 'outdated';
}
function freshChipHtml(iso) {
  if (!iso) return '';
  var t = Date.parse(iso);
  if (isNaN(t)) return '';
  var days = Math.floor((Date.now() - t) / 86400000);
  var cls = 'fresh-green', label;
  if (days < 31) label = days + 'd ago';
  else if (days < 366) label = Math.round(days / 30) + 'mo ago';
  else label = Math.max(1, Math.round(days / 365)) + 'y ago';
  if (days > 183) cls = 'fresh-amber';
  if (days > 366) cls = 'fresh-red';
  return '<span class="uc-card-fresh ' + cls + '" title="Last reviewed ' + esc(iso) + '">✓ ' + esc(label) + '</span>';
}
function setRegFilter(f) {
  // Changing the regulation always resets the clause selection: a
  // clause id is only meaningful inside a single framework, and keeping
  // a stale clause when the user switches from (say) GDPR to PCI DSS
  // would silently produce zero-result pages with no obvious cause.
  currentRegulationFilter = f;
  currentClauseFilter = 'all';
  reRender();
}
function setClauseFilter(f) {
  // Clause-level filter is only meaningful when a specific regulation
  // is already selected; the regulation dropdown's ``onchange`` clears
  // this automatically. Values are the canonical ``{version}#{clause}``
  // form stored in ``_cachedClausesByReg``.
  currentClauseFilter = f || 'all';
  reRender();
}
function setMtypeFilter(f) { currentMtypeFilter = f; reRender(); }
function setTrendFilter() { currentTrendFilter = !currentTrendFilter; reRender(); }

function setAdvFilter(key, val) {
  if (key === 'escu') currentEscuFilter = val;
  else if (key === 'dtype') currentDtypeFilter = val;
  else if (key === 'premium') currentPremiumFilter = val;
  else if (key === 'cim') currentCimFilter = val;
  else if (key === 'sapp') currentSappFilter = val;
  else if (key === 'industry') currentIndustryFilter = val;
  else if (key === 'mitre') { currentMitreFilter = val; currentMitreTacticFilter = ''; }
  else if (key === 'mitre_tactic') { currentMitreTacticFilter = val; currentMitreFilter = ''; }
  reRender();
}

var _advDebounceTimer = null;
function debounceAdvSearch(key, val) {
  clearTimeout(_advDebounceTimer);
  _advDebounceTimer = setTimeout(function() {
    if (key === 'datasource') currentDatasourceFilter = val;
    reRender();
  }, 300);
}

function handleDsGroupSelect(val) {
  if (val === 'all') { currentDsGroup = ''; currentDatasourceFilter = ''; }
  else if (val === '__custom__') { currentDsGroup = ''; currentDatasourceFilter = ''; }
  else { currentDsGroup = val; currentDatasourceFilter = ''; }
  reRender();
}
function handleDsSourceSelect(val) { currentDatasourceFilter = val; reRender(); }

function toggleAdvFilters() { advFiltersOpen = !advFiltersOpen; reRender(); }

function buildMitreDdList(query) {
  if (typeof FILTER_FACETS === 'undefined' || !FILTER_FACETS.mitre) return '';
  var q = (query || '').toLowerCase().trim();
  var html = '<div class="adv-mitre-clear" onclick="selectMitreTech(\'\')">← All tactics & techniques</div>';
  var any = false;
  FILTER_FACETS.mitre.forEach(function(group) {
    var tacticMatch = !q || group.label.toLowerCase().indexOf(q) !== -1 || (group.tactic && group.tactic.toLowerCase().indexOf(q) !== -1);
    var matched = group.techniques.filter(function(t) {
      if (!q || tacticMatch) return true;
      return t.id.toLowerCase().indexOf(q) !== -1 || (t.name && t.name.toLowerCase().indexOf(q) !== -1);
    });
    if (matched.length === 0 && !tacticMatch) return;
    any = true;
    var tacSel = currentMitreTacticFilter === group.tactic ? ' selected' : '';
    html += '<div class="adv-mitre-tactic clickable' + tacSel + '" onclick="selectMitreDdTactic(\'' + esc(group.tactic || '') + '\')">' + esc(group.label) + '</div>';
    matched.forEach(function(t) {
      var sel = currentMitreFilter === t.id ? ' selected' : '';
      html += '<div class="adv-mitre-opt' + sel + '" onclick="selectMitreTech(\'' + esc(t.id) + '\')"><span class="mitre-tid">' + esc(t.id) + '</span> ' + esc(t.name || '') + '</div>';
    });
  });
  if (!any) html += '<div class="adv-mitre-none">No matches</div>';
  return html;
}

function toggleMitreDd() {
  var dd = document.getElementById('mitre-dd');
  var btn = dd && dd.previousElementSibling;
  if (!dd) return;
  var show = !dd.classList.contains('show');
  dd.classList.toggle('show', show);
  if (btn) btn.classList.toggle('open', show);
  if (show) {
    var list = document.getElementById('mitre-dd-list');
    if (list) list.innerHTML = buildMitreDdList('');
    var inp = dd.querySelector('.adv-mitre-search');
    if (inp) { inp.value = ''; inp.focus(); }
  }
}

function filterMitreDd(val) {
  var list = document.getElementById('mitre-dd-list');
  if (list) list.innerHTML = buildMitreDdList(val);
}

function selectMitreTech(id) {
  currentMitreFilter = id;
  currentMitreTacticFilter = '';
  var dd = document.getElementById('mitre-dd');
  if (dd) { dd.classList.remove('show'); var b = dd.previousElementSibling; if (b) b.classList.remove('open'); }
  reRender();
}

function selectMitreDdTactic(tactic) {
  currentMitreTacticFilter = tactic;
  currentMitreFilter = '';
  var dd = document.getElementById('mitre-dd');
  if (dd) { dd.classList.remove('show'); var b = dd.previousElementSibling; if (b) b.classList.remove('open'); }
  reRender();
}

function advancedFilterPanel() {
  var html = '<div class="adv-filter-panel"><div class="adv-row">';
  html += '<div class="adv-group"><label class="adv-label">ES Detection</label><div class="adv-chips">';
  [['all','All'],['yes','Yes'],['no','No']].forEach(function(o) {
    html += '<button type="button" class="c-chip sm' + (currentEscuFilter === o[0] ? ' active' : '') + '" onclick="setAdvFilter(\'escu\',\'' + o[0] + '\')">' + o[1] + '</button>';
  });
  html += '</div></div>';
  html += '<div class="adv-group"><label class="adv-label">Detection type</label><select class="c-select full" onchange="setAdvFilter(\'dtype\',this.value)">';
  html += '<option value="all">All types</option>';
  if (FILTER_FACETS.dtype) FILTER_FACETS.dtype.forEach(function(v) {
    html += '<option value="' + esc(v) + '"' + (currentDtypeFilter === v ? ' selected' : '') + '>' + esc(v) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">Premium Apps</label><select class="c-select full" onchange="setAdvFilter(\'premium\',this.value)">';
  html += '<option value="all">All</option>';
  if (FILTER_FACETS.premium) FILTER_FACETS.premium.forEach(function(v) {
    html += '<option value="' + esc(v) + '"' + (currentPremiumFilter === v ? ' selected' : '') + '>' + esc(v.substring(0, 80)) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">CIM Data Model</label><select class="c-select full" onchange="setAdvFilter(\'cim\',this.value)">';
  html += '<option value="all">All models</option>';
  if (FILTER_FACETS.cim) FILTER_FACETS.cim.forEach(function(v) {
    html += '<option value="' + esc(v) + '"' + (currentCimFilter === v ? ' selected' : '') + '>' + esc(v) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">App / TA</label><select class="c-select full" onchange="setAdvFilter(\'sapp\',this.value)">';
  html += '<option value="all">All apps</option>';
  if (FILTER_FACETS.sapp) FILTER_FACETS.sapp.forEach(function(v) {
    html += '<option value="' + v.id + '"' + (currentSappFilter === String(v.id) ? ' selected' : '') + '>' + esc(v.name) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">Industry</label><select class="c-select full" onchange="setAdvFilter(\'industry\',this.value)">';
  html += '<option value="all">All industries</option>';
  if (FILTER_FACETS.industry) FILTER_FACETS.industry.forEach(function(v) {
    html += '<option value="' + esc(v) + '"' + (currentIndustryFilter === v ? ' selected' : '') + '>' + esc(v) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">Data source</label>';
  html += '<select class="c-select full" onchange="handleDsGroupSelect(this.value)">';
  html += '<option value="all"' + (!currentDsGroup && !currentDatasourceFilter ? ' selected' : '') + '>All sources</option>';
  if (FILTER_FACETS.datasource_groups) FILTER_FACETS.datasource_groups.forEach(function(g) {
    if (g.name === 'Other') return;
    html += '<option value="' + esc(g.name) + '"' + (currentDsGroup === g.name ? ' selected' : '') + '>' + esc(g.name) + ' (' + g.total + ')</option>';
  });
  html += '<option value="__custom__"' + (!currentDsGroup && currentDatasourceFilter ? ' selected' : '') + '>Other…</option></select>';
  if (currentDsGroup) {
    var grp = FILTER_FACETS.datasource_groups && FILTER_FACETS.datasource_groups.find(function(g) { return g.name === currentDsGroup; });
    if (grp && grp.sources.length) {
      html += '<select class="c-select full mt" onchange="handleDsSourceSelect(this.value)">';
      html += '<option value="">Any in group</option>';
      grp.sources.forEach(function(s) {
        html += '<option value="' + esc(s.name) + '"' + (currentDatasourceFilter === s.name ? ' selected' : '') + '>' + esc(s.name) + '</option>';
      });
      html += '</select>';
    }
  }
  if (!currentDsGroup && currentDatasourceFilter) {
    html += '<input type="text" class="c-input full mt" placeholder="Type data source…" value="' + esc(currentDatasourceFilter) + '" oninput="debounceAdvSearch(\'datasource\',this.value)">';
  }
  html += '</div></div>';
  var mitreLabel = 'All tactics & techniques';
  var mitreHas = false;
  if (currentMitreFilter && FILTER_FACETS.mitre) {
    mitreHas = true;
    FILTER_FACETS.mitre.some(function(g) {
      var f = g.techniques.find(function(t) { return t.id === currentMitreFilter; });
      if (f) { mitreLabel = f.id + ' — ' + f.name; return true; }
    });
  } else if (currentMitreTacticFilter && FILTER_FACETS.mitre) {
    mitreHas = true;
    var tg = FILTER_FACETS.mitre.find(function(g) { return g.tactic === currentMitreTacticFilter; });
    mitreLabel = tg ? 'Tactic: ' + tg.label : currentMitreTacticFilter;
  }
  html += '<div class="adv-row single"><div class="adv-group grow">';
  html += '<label class="adv-label">MITRE ATT&CK</label><div class="adv-mitre-row">';
  html += '<div class="adv-mitre-wrap" id="mitre-dd-wrap"><button type="button" class="adv-mitre-btn' + (mitreHas ? ' has-value' : '') + '" onclick="toggleMitreDd()">' + esc(mitreLabel) + '</button>';
  html += '<div class="adv-mitre-dd" id="mitre-dd"><input type="text" class="adv-mitre-search" placeholder="Search…" oninput="filterMitreDd(this.value)"><div id="mitre-dd-list"></div></div></div>';
  html += '<button type="button" class="c-btn c-btn-secondary mitre-map-trigger" onclick="openMitreMap()">' + si('shield') + ' Coverage Map</button>';
  html += '</div></div></div></div>';
  return html;
}

function breadcrumb(catObj, scObj) {
  var h = '<nav class="c-breadcrumb"><button onclick="goHome()">Overview</button>';
  if (catObj) {
    h += '<span class="c-bc-sep">/</span>';
    if (scObj) {
      h += '<button onclick="selectCat(' + catObj.i + ')">' + esc(catObj.n) + '</button>';
      h += '<span class="c-bc-sep">/</span><span class="c-bc-current">' + esc(scObj.n) + '</span>';
    } else {
      h += '<span class="c-bc-current">' + esc(catObj.n) + '</span>';
    }
  }
  return h + '</nav>';
}
function emptyState(msg) {
  return '<div class="c-empty-state">' +
    '<div class="c-empty-icon">' + si('search') + '</div>' +
    '<div class="c-empty-title">' + esc(msg || 'No use cases match your filters') + '</div>' +
    '<div class="c-empty-desc">Try removing some filters or broadening your search.</div>' +
    '<div class="c-empty-actions">' +
    '<button class="primary" onclick="clearAllFilters()">Clear all filters</button>' +
    '<button onclick="goHome()">Back to overview</button>' +
    '</div></div>';
}
function filterStrip() {
  var html = '<div class="filter-strip">';
  [['all','All'],['security','Security'],['observability','Observability']].forEach(function(p) {
    html += '<button type="button" class="c-chip' + (currentPillarFilter === p[0] ? ' active' : '') + '" onclick="setPillarFilter(\'' + p[0] + '\')">' + p[1] + '</button>';
  });
  html += '<select class="c-select" onchange="setFilter(this.value)"><option value="all">All criticality</option>';
  ['critical','high','medium','low'].forEach(function(c) {
    html += '<option value="' + c + '"' + (currentFilter === c ? ' selected' : '') + '>' + c.charAt(0).toUpperCase() + c.slice(1) + '</option>';
  });
  html += '</select><select class="c-select" onchange="setDiffFilter(this.value)"><option value="all">All Difficulty</option>';
  ['beginner','intermediate','advanced','expert'].forEach(function(d) {
    html += '<option value="' + d + '"' + (currentDiffFilter === d ? ' selected' : '') + '>' + d.charAt(0).toUpperCase() + d.slice(1) + '</option>';
  });
  html += '</select>';
  html += '<select class="c-select" onchange="setStatusFilter(this.value)" title="Quality status">';
  html += '<option value="all">All Status</option>';
  ['verified','community','draft'].forEach(function(s) {
    html += '<option value="' + s + '"' + (currentStatusFilter === s ? ' selected' : '') + '>' + s.charAt(0).toUpperCase() + s.slice(1) + '</option>';
  });
  html += '</select>';
  html += '<select class="c-select" onchange="setFreshFilter(this.value)" title="Last reviewed">';
  html += '<option value="all">All Freshness</option>';
  [['fresh','≤ 6 mo'],['stale','6–12 mo'],['outdated','> 12 mo'],['unknown','Never reviewed']].forEach(function(fp) {
    html += '<option value="' + fp[0] + '"' + (currentFreshFilter === fp[0] ? ' selected' : '') + '>' + fp[1] + '</option>';
  });
  html += '</select>';
  if (_cachedRegKeys.length) {
    html += '<select class="c-select" onchange="setRegFilter(this.value)" title="Regulation framework">';
    html += '<option value="all">All Regulations</option>';
    _cachedRegKeys.forEach(function(r) {
      html += '<option value="' + esc(r) + '"' + (currentRegulationFilter === r ? ' selected' : '') + '>' + esc(r) + '</option>';
    });
    html += '</select>';
    // Phase 3a — clause-level dropdown. Only renders when the user
    // picked a specific regulation AND that regulation has at least
    // one structured ``cmp[]`` row in the catalogue. Frameworks whose
    // UCs still use the flat ``regs[]`` form (pre-Phase-1 sidecars)
    // simply don't show the second dropdown, so the UX degrades to
    // "regulation only" instead of breaking.
    if (currentRegulationFilter !== 'all') {
      var clauses = _cachedClausesByReg[currentRegulationFilter] || [];
      if (clauses.length) {
        html += '<select class="c-select" onchange="setClauseFilter(this.value)" title="Specific clause or article">';
        html += '<option value="all">All Clauses (' + clauses.length + ')</option>';
        clauses.forEach(function(canonical) {
          // canonical form: ``{version}#{clause}``. Split on the first
          // ``#`` so the option label can show the clause prominently
          // with the version in parentheses — clauses are how auditors
          // think ("show me GDPR Art.5 coverage") and versions are
          // disambiguators, not the primary key.
          var hashAt = canonical.indexOf('#');
          var ver = hashAt > 0 ? canonical.slice(0, hashAt) : '';
          var clause = hashAt > 0 ? canonical.slice(hashAt + 1) : canonical;
          var label = clause + (ver ? '  (' + ver + ')' : '');
          html += '<option value="' + esc(canonical) + '"' + (currentClauseFilter === canonical ? ' selected' : '') + '>' + esc(label) + '</option>';
        });
        html += '</select>';
      }
    }
  }
  if (_cachedMtypes.length) {
    html += '<select class="c-select" onchange="setMtypeFilter(this.value)"><option value="all">All Types</option>';
    _cachedMtypes.forEach(function(t) { html += '<option value="' + esc(t) + '"' + (currentMtypeFilter === t ? ' selected' : '') + '>' + esc(t) + '</option>'; });
    html += '</select>';
  }
  html += '<button type="button" class="c-chip trend' + (currentTrendFilter ? ' active' : '') + '" onclick="setTrendFilter()">📈 Trend</button>';
  html += '<span class="filter-count"><strong id="filter-count-num">0</strong> use cases</span></div>';
  var anyAdv = currentEscuFilter !== 'all' || currentDtypeFilter !== 'all' || currentPremiumFilter !== 'all' || currentCimFilter !== 'all' || currentSappFilter !== 'all' || currentIndustryFilter !== 'all' || currentMitreFilter || currentMitreTacticFilter || currentDsGroup || currentDatasourceFilter;
  html += '<div class="adv-toggle-row"><button type="button" class="adv-toggle-btn' + (advFiltersOpen ? ' open' : '') + '" onclick="toggleAdvFilters()">Advanced Filters ' + (anyAdv ? '•' : '') + ' ' + (advFiltersOpen ? '▲' : '▼') + '</button></div>';
  if (advFiltersOpen) html += advancedFilterPanel();
  return html;
}

function activeFilterTags() {
  var tags = [];
  if (currentPillarFilter !== 'all') tags.push({ label: currentPillarFilter === 'security' ? 'Security' : 'Observability', fn: "setPillarFilter('all')" });
  if (currentFilter !== 'all') tags.push({ label: currentFilter.charAt(0).toUpperCase() + currentFilter.slice(1), fn: "setFilter('all')" });
  if (currentDiffFilter !== 'all') tags.push({ label: currentDiffFilter.charAt(0).toUpperCase() + currentDiffFilter.slice(1), fn: "setDiffFilter('all')" });
  if (currentStatusFilter !== 'all') tags.push({ label: 'Status: ' + currentStatusFilter.charAt(0).toUpperCase() + currentStatusFilter.slice(1), fn: "setStatusFilter('all')" });
  if (currentFreshFilter !== 'all') {
    var freshMap = { fresh: '≤ 6 mo', stale: '6–12 mo', outdated: '> 12 mo', unknown: 'Never reviewed' };
    tags.push({ label: 'Reviewed: ' + (freshMap[currentFreshFilter] || currentFreshFilter), fn: "setFreshFilter('all')" });
  }
  if (currentRegulationFilter !== 'all') tags.push({ label: currentRegulationFilter, fn: "setRegFilter('all')" });
  if (currentClauseFilter && currentClauseFilter !== 'all') {
    // Render the clause as "<clause> (<version>)" so the chip reads like
    // an auditor would say it out loud ("GDPR Art.5 (2016/679)") rather
    // than the raw canonical ``{version}#{clause}`` which looks like an
    // internal id. The backing filter value stays canonical for exact
    // match in ``getFilteredUCs()``.
    var hashAt2 = currentClauseFilter.indexOf('#');
    var clauseLabel = hashAt2 > 0 ? (currentClauseFilter.slice(hashAt2 + 1) + '  (' + currentClauseFilter.slice(0, hashAt2) + ')') : currentClauseFilter;
    tags.push({ label: 'Clause: ' + clauseLabel, fn: "setClauseFilter('all')" });
  }
  if (currentMtypeFilter !== 'all') tags.push({ label: currentMtypeFilter, fn: "setMtypeFilter('all')" });
  if (currentIndustryFilter !== 'all') tags.push({ label: 'Industry: ' + currentIndustryFilter, fn: "setAdvFilter('industry','all')" });
  if (currentEscuFilter !== 'all') tags.push({ label: 'ES Detection: ' + (currentEscuFilter === 'yes' ? 'Yes' : 'No'), fn: "setAdvFilter('escu','all')" });
  if (currentDtypeFilter !== 'all') tags.push({ label: 'Detection: ' + currentDtypeFilter, fn: "setAdvFilter('dtype','all')" });
  if (currentPremiumFilter !== 'all') tags.push({ label: 'Premium: ' + currentPremiumFilter, fn: "setAdvFilter('premium','all')" });
  if (currentCimFilter !== 'all') tags.push({ label: 'CIM: ' + currentCimFilter, fn: "setAdvFilter('cim','all')" });
  if (currentSappFilter !== 'all') {
    var sl = currentSappFilter;
    if (FILTER_FACETS.sapp) { var sf = FILTER_FACETS.sapp.find(function(s) { return String(s.id) === currentSappFilter; }); if (sf) sl = sf.name; }
    tags.push({ label: 'App: ' + sl, fn: "setAdvFilter('sapp','all')" });
  }
  if (currentMitreFilter) {
    var mitreLabel = currentMitreFilter;
    if (FILTER_FACETS.mitre) { var mf2 = null; FILTER_FACETS.mitre.some(function(g) { mf2 = g.techniques.find(function(t) { return t.id === currentMitreFilter; }); return !!mf2; }); if (mf2 && mf2.name) mitreLabel = mf2.id + ' ' + mf2.name; }
    tags.push({ label: 'MITRE: ' + mitreLabel, fn: "setAdvFilter('mitre','')" });
  }
  if (currentMitreTacticFilter) {
    var tacLabel = currentMitreTacticFilter;
    if (FILTER_FACETS.mitre) { var tg = FILTER_FACETS.mitre.find(function(g) { return g.tactic === currentMitreTacticFilter; }); if (tg) tacLabel = tg.label; }
    tags.push({ label: 'Tactic: ' + tacLabel, fn: "setAdvFilter('mitre_tactic','')" });
  }
  if (currentDsGroup && currentDatasourceFilter) {
    tags.push({ label: currentDsGroup + ': ' + currentDatasourceFilter, fn: "clearAdvSearch('datasource')" });
  } else if (currentDsGroup) {
    tags.push({ label: 'Data source: ' + currentDsGroup, fn: "clearAdvSearch('datasource')" });
  } else if (currentDatasourceFilter) {
    tags.push({ label: 'Data source: ' + currentDatasourceFilter, fn: "clearAdvSearch('datasource')" });
  }
  if (currentTrendFilter) tags.push({ label: 'Trend', fn: "clearTrendFilter()" });
  if (selectedEquipmentId) {
    var _eqLabel = selectedEquipmentId;
    var _eqObj = (EQUIPMENT||[]).find(function(x){return x.id===selectedEquipmentId;});
    if (_eqObj) _eqLabel = _eqObj.label;
    tags.push({ label: 'Equipment: ' + _eqLabel, fn: "clearEquipmentFilter()" });
  }
  if (inventorySelections.length) tags.push({ label: 'Inventory (' + inventorySelections.length + ' items)', fn: "clearInventoryFilter()" });
  if (ovHeroGroupFilter) tags.push({ label: 'Domain: ' + ovHeroGroupFilter, fn: 'clearHeroFilter()' });
  if (currentSearch) tags.push({ label: 'Search: ' + currentSearch, fn: "clearSearch()" });
  if (!tags.length) return '';
  var h = '<div class="c-active-tags">';
  tags.forEach(function(t) { h += '<button type="button" class="c-active-tag" onclick="' + t.fn + '">' + esc(t.label) + ' <span class="x">×</span></button>'; });
  h += '<button type="button" class="c-clear-all" onclick="clearAllFilters()">Clear all</button></div>';
  return h;
}

function clearTrendFilter() { currentTrendFilter = false; reRender(); }
function clearAdvSearch(key) {
  if (key === 'datasource') { currentDsGroup = ''; currentDatasourceFilter = ''; }
  reRender();
}
function clearEquipmentFilter() {
  selectedEquipmentId = '';
  var es = document.getElementById('equipment-select');
  var ms = document.getElementById('equipment-model-select');
  var mw = document.getElementById('equipment-model-wrap');
  if (es) es.value = '';
  if (ms) ms.innerHTML = '<option value="">All models</option>';
  if (mw) mw.style.display = 'none';
  if (typeof reRender === 'function') reRender();
}
function clearInventoryFilter() {
  inventorySelections = [];
  try { localStorage.removeItem(INVENTORY_STORAGE_KEY); } catch (e) {}
  _updateInventoryBadge();
  reRender();
}

function clearAllFilters() {
  currentSearch = '';
  var siEl = document.getElementById('search-input');
  if (siEl) siEl.value = '';
  currentFilter = 'all'; currentDiffFilter = 'all'; currentIndustryFilter = 'all'; currentMtypeFilter = 'all';
  currentPillarFilter = 'all'; currentRegulationFilter = 'all'; currentClauseFilter = 'all'; currentEscuFilter = 'all'; currentDtypeFilter = 'all';
  currentPremiumFilter = 'all'; currentCimFilter = 'all'; currentSappFilter = 'all'; currentMitreFilter = '';
  currentStatusFilter = 'all'; currentFreshFilter = 'all';
  currentMitreTacticFilter = ''; currentDsGroup = ''; currentDatasourceFilter = ''; currentTrendFilter = false;
  ovHeroGroupFilter = null; ovGroupFilter = 'all';
  selectedEquipmentId = '';
  var es = document.getElementById('equipment-select');
  var ms = document.getElementById('equipment-model-select');
  var mw = document.getElementById('equipment-model-wrap');
  if (es) es.value = '';
  if (ms) ms.innerHTML = '<option value="">All models</option>';
  if (mw) mw.style.display = 'none';
  if (inventorySelections.length) { inventorySelections = []; try { localStorage.removeItem(INVENTORY_STORAGE_KEY); } catch (e2) {} }
  _updateInventoryBadge();
  reRender();
}
