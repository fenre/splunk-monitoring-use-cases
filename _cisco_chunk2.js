function setSort(val) {
  currentSort = val;
  try { localStorage.setItem('uc-sort-pref', val); } catch (e) {}
  reRender();
}

function setPillarFilter(val) { currentPillarFilter = val; reRender(); }
function setFilter(f) { currentFilter = f; reRender(); }
function setDiffFilter(f) { currentDiffFilter = f; reRender(); }
function setRegFilter(f) { currentRegulationFilter = f; reRender(); }
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
  html += '<option value="all">All</option>';
  if (FILTER_FACETS.dtype) FILTER_FACETS.dtype.forEach(function(v) {
    html += '<option value="' + esc(v) + '"' + (currentDtypeFilter === v ? ' selected' : '') + '>' + esc(v) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">Premium</label><select class="c-select full" onchange="setAdvFilter(\'premium\',this.value)">';
  html += '<option value="all">All</option>';
  if (FILTER_FACETS.premium) FILTER_FACETS.premium.forEach(function(v) {
    html += '<option value="' + esc(v) + '"' + (currentPremiumFilter === v ? ' selected' : '') + '>' + esc(v.substring(0, 80)) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">CIM</label><select class="c-select full" onchange="setAdvFilter(\'cim\',this.value)">';
  html += '<option value="all">All</option>';
  if (FILTER_FACETS.cim) FILTER_FACETS.cim.forEach(function(v) {
    html += '<option value="' + esc(v) + '"' + (currentCimFilter === v ? ' selected' : '') + '>' + esc(v) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">App / TA</label><select class="c-select full" onchange="setAdvFilter(\'sapp\',this.value)">';
  html += '<option value="all">All</option>';
  if (FILTER_FACETS.sapp) FILTER_FACETS.sapp.forEach(function(v) {
    html += '<option value="' + v.id + '"' + (currentSappFilter === String(v.id) ? ' selected' : '') + '>' + esc(v.name) + '</option>';
  });
  html += '</select></div>';
  html += '<div class="adv-group"><label class="adv-label">Industry</label><select class="c-select full" onchange="setAdvFilter(\'industry\',this.value)">';
  html += '<option value="all">All</option>';
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

function filterStrip() {
  var html = '<div class="filter-strip">';
  [['all','All'],['security','Security'],['observability','Observability']].forEach(function(p) {
    html += '<button type="button" class="c-chip' + (currentPillarFilter === p[0] ? ' active' : '') + '" onclick="setPillarFilter(\'' + p[0] + '\')">' + p[1] + '</button>';
  });
  html += '<select class="c-select" onchange="setFilter(this.value)"><option value="all">All Criticality</option>';
  ['critical','high','medium','low'].forEach(function(c) {
    html += '<option value="' + c + '"' + (currentFilter === c ? ' selected' : '') + '>' + c.charAt(0).toUpperCase() + c.slice(1) + '</option>';
  });
  html += '</select><select class="c-select" onchange="setDiffFilter(this.value)"><option value="all">All Difficulty</option>';
  ['beginner','intermediate','advanced','expert'].forEach(function(d) {
    html += '<option value="' + d + '"' + (currentDiffFilter === d ? ' selected' : '') + '>' + d.charAt(0).toUpperCase() + d.slice(1) + '</option>';
  });
  html += '</select>';
  var regSet = {};
  allUCs.forEach(function(e) { if (Array.isArray(e.uc.regs)) e.uc.regs.forEach(function(r) { regSet[r] = (regSet[r] || 0) + 1; }); });
  var regKeys = Object.keys(regSet).sort();
  if (regKeys.length) {
    html += '<select class="c-select" onchange="setRegFilter(this.value)"><option value="all">All Regulations</option>';
    regKeys.forEach(function(r) { html += '<option value="' + esc(r) + '"' + (currentRegulationFilter === r ? ' selected' : '') + '>' + esc(r) + '</option>'; });
    html += '</select>';
  }
  var mtypes = new Set();
  allUCs.forEach(function(e) { if (Array.isArray(e.uc.mtype)) e.uc.mtype.forEach(function(t) { mtypes.add(t); }); });
  if (mtypes.size) {
    var mtOrder = ['Availability','Performance','Security','Configuration','Capacity','Fault','Anomaly','Compliance'];
    var sortedMt = Array.from(mtypes).sort(function(a, b) {
      var ia = mtOrder.indexOf(a), ib = mtOrder.indexOf(b);
      if (ia >= 0 && ib >= 0) return ia - ib;
      if (ia >= 0) return -1;
      if (ib >= 0) return 1;
      return a.localeCompare(b);
    });
    html += '<select class="c-select" onchange="setMtypeFilter(this.value)"><option value="all">All monitoring types</option>';
    sortedMt.forEach(function(t) { html += '<option value="' + esc(t) + '"' + (currentMtypeFilter === t ? ' selected' : '') + '>' + esc(t) + '</option>'; });
    html += '</select>';
  }
  html += '<button type="button" class="c-chip trend' + (currentTrendFilter ? ' active' : '') + '" onclick="setTrendFilter()">📈 Trend</button>';
  html += '<span class="filter-count"><strong id="filter-count-num">0</strong> use cases</span></div>';
  var anyAdv = currentEscuFilter !== 'all' || currentDtypeFilter !== 'all' || currentPremiumFilter !== 'all' || currentCimFilter !== 'all' || currentSappFilter !== 'all' || currentIndustryFilter !== 'all' || currentMitreFilter || currentMitreTacticFilter || currentDsGroup || currentDatasourceFilter;
  html += '<div class="adv-toggle-row"><button type="button" class="adv-toggle-btn' + (advFiltersOpen ? ' open' : '') + '" onclick="toggleAdvFilters()">Advanced filters ' + (anyAdv ? '•' : '') + ' ' + (advFiltersOpen ? '▲' : '▼') + '</button></div>';
  if (advFiltersOpen) html += advancedFilterPanel();
  return html;
}

function activeFilterTags() {
  var tags = [];
  if (currentPillarFilter !== 'all') tags.push({ label: currentPillarFilter === 'security' ? 'Security' : 'Observability', fn: "setPillarFilter('all')" });
  if (currentFilter !== 'all') tags.push({ label: currentFilter, fn: "setFilter('all')" });
  if (currentDiffFilter !== 'all') tags.push({ label: currentDiffFilter, fn: "setDiffFilter('all')" });
  if (currentRegulationFilter !== 'all') tags.push({ label: currentRegulationFilter, fn: "setRegFilter('all')" });
  if (currentMtypeFilter !== 'all') tags.push({ label: currentMtypeFilter, fn: "setMtypeFilter('all')" });
  if (currentIndustryFilter !== 'all') tags.push({ label: 'Industry: ' + currentIndustryFilter, fn: "setAdvFilter('industry','all')" });
  if (currentEscuFilter !== 'all') tags.push({ label: 'ES: ' + currentEscuFilter, fn: "setAdvFilter('escu','all')" });
  if (currentDtypeFilter !== 'all') tags.push({ label: 'Detection: ' + currentDtypeFilter, fn: "setAdvFilter('dtype','all')" });
  if (currentPremiumFilter !== 'all') tags.push({ label: 'Premium…', fn: "setAdvFilter('premium','all')" });
  if (currentCimFilter !== 'all') tags.push({ label: 'CIM: ' + currentCimFilter, fn: "setAdvFilter('cim','all')" });
  if (currentSappFilter !== 'all') {
    var sl = currentSappFilter;
    if (FILTER_FACETS.sapp) { var sf = FILTER_FACETS.sapp.find(function(s) { return String(s.id) === currentSappFilter; }); if (sf) sl = sf.name; }
    tags.push({ label: 'App: ' + sl, fn: "setAdvFilter('sapp','all')" });
  }
  if (currentMitreFilter) tags.push({ label: 'MITRE: ' + currentMitreFilter, fn: "setAdvFilter('mitre','')" });
  if (currentMitreTacticFilter) tags.push({ label: 'Tactic', fn: "setAdvFilter('mitre_tactic','')" });
  if (currentDsGroup || currentDatasourceFilter) tags.push({ label: 'Data source', fn: "clearAdvSearch('datasource')" });
  if (currentTrendFilter) tags.push({ label: 'Trend', fn: "clearTrendFilter()" });
  if (selectedEquipmentId) tags.push({ label: 'Equipment', fn: "clearEquipmentFilter()" });
  if (inventorySelections.length) tags.push({ label: 'Inventory (' + inventorySelections.length + ')', fn: "clearInventoryFilter()" });
  if (ovHeroGroupFilter) tags.push({ label: 'Domain filter', fn: "filterByHeroGroup('" + ovHeroGroupFilter + "')" });
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
  currentFilter = 'all'; currentDiffFilter = 'all'; currentIndustryFilter = 'all'; currentMtypeFilter = 'all';
  currentPillarFilter = 'all'; currentRegulationFilter = 'all'; currentEscuFilter = 'all'; currentDtypeFilter = 'all';
  currentPremiumFilter = 'all'; currentCimFilter = 'all'; currentSappFilter = 'all'; currentMitreFilter = '';
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

function renderUCCard(uc) {
  var tags = '';
  if (Array.isArray(uc.mtype)) uc.mtype.slice(0, 2).forEach(function(m) { tags += '<span class="uc-card-tag">' + esc(m) + '</span>'; });
  return '<div class="uc-card" onclick="openUCById(\'' + esc(uc.i) + '\')"><div class="uc-card-top"><span class="uc-crit-dot c-' + esc(uc.c || 'low') + '"></span><span class="uc-card-title">' + esc(uc.n) + '</span></div><div class="uc-card-meta">' + diffBadge(uc.f) + '</div><p class="uc-card-val">' + esc(stripMd((uc.v || '').substring(0, 160))) + (uc.v && uc.v.length > 160 ? '…' : '') + '</p><div class="uc-card-tags">' + tags + '</div></div>';
}

function renderUCBatch(container, startIdx) {
  var end = Math.min(startIdx + ucRenderBatch, ucAllCardsHtml.length);
  if (ucGridTargets.length) {
    var byGrid = {};
    for (var i = startIdx; i < end; i++) {
      var gid = ucGridTargets[i];
      if (!byGrid[gid]) byGrid[gid] = [];
      byGrid[gid].push(ucAllCardsHtml[i]);
    }
    Object.keys(byGrid).forEach(function(gid) {
      var grid = document.getElementById(gid);
      if (!grid) return;
      var frag = document.createDocumentFragment();
      byGrid[gid].forEach(function(html) {
        var d = document.createElement('div');
        d.innerHTML = html;
        while (d.firstChild) frag.appendChild(d.firstChild);
      });
      grid.appendChild(frag);
    });
  }
  ucRenderedCount = end;
}

function setupUCScrollObserver(container) {
  if (ucScrollObserver) { ucScrollObserver.disconnect(); ucScrollObserver = null; }
  if (ucRenderedCount >= ucAllCardsHtml.length) return;
  var sentinel = document.createElement('div');
  sentinel.className = 'uc-scroll-sentinel';
  sentinel.style.height = '1px';
  container.appendChild(sentinel);
  ucScrollObserver = new IntersectionObserver(function(entries) {
    if (entries[0].isIntersecting && ucRenderedCount < ucAllCardsHtml.length) {
      sentinel.remove();
      renderUCBatch(container, ucRenderedCount);
      if (ucRenderedCount < ucAllCardsHtml.length) container.appendChild(sentinel);
      else ucScrollObserver.disconnect();
    }
  }, { rootMargin: '400px' });
  ucScrollObserver.observe(sentinel);
}

function filterOvGroup(group) {
  ovGroupFilter = group;
  renderOverview();
  updateHash(false);
}

function filterByHeroGroup(group) {
  var des = ovHeroGroupFilter === group;
  ovHeroGroupFilter = des ? null : group;
  sidebarManualToggle = false;
  if (!des) { expandedSidebarGroups.clear(); expandedSidebarGroups.add(group); sidebarManualToggle = true; }
  renderOverview();
  buildSidebar();
}

function toggleOvSection(el) {
  var body = el.nextElementSibling;
  var arrow = el.querySelector('.ov-collapse-arrow');
  var open = body.style.display === 'none';
  body.style.display = open ? '' : 'none';
  if (arrow) arrow.classList.toggle('open', open);
  el.setAttribute('aria-expanded', open ? 'true' : 'false');
}

function toggleSidebarGroup(g) {
  sidebarManualToggle = true;
  if (expandedSidebarGroups.has(g)) expandedSidebarGroups.delete(g);
  else expandedSidebarGroups.add(g);
  buildSidebar();
}

function scrollToSubcat(scId) {
  currentSubcat = scId;
  buildSidebar();
  updateHash(true);
  var el = document.getElementById('sc-' + String(scId).replace(/\./g, '_'));
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function goToSubcat(catId, scId) {
  selectCat(catId);
  setTimeout(function() { scrollToSubcat(scId); }, 50);
}
