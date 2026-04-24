function renderUCCard(uc) {
  var cbChecked = selectedUCIds.has(uc.i) ? ' checked' : '';
  var cb = '<label class="uc-select-cb" onclick="event.stopPropagation()" title="Select for data sizing estimate"><input type="checkbox"' + cbChecked + ' onchange="toggleUCSelection(\'' + esc(uc.i) + '\')"></label>';
  var html = '<div class="uc-card" onclick="openUCById(\'' + esc(uc.i) + '\')">' + cb;
  html += '<div class="uc-card-top"><span class="uc-crit-dot c-' + esc(uc.c || 'low') + '"></span><div style="flex:1;min-width:0"><span class="uc-card-title">' + esc(uc.n) + '</span><div style="margin-top:3px"><span class="uc-card-id">UC-' + esc(uc.i) + '</span></div></div>';
  html += diffBadge(uc.f);
  html += '</div>';
  if (uc.v) html += '<p class="uc-card-val">' + esc(stripMd(uc.v)) + '</p>';
  var ta = (uc.t || '').replace(/`/g, '');
  var cimModels = Array.isArray(uc.a) ? uc.a : null;
  var mtypes = Array.isArray(uc.mtype) ? uc.mtype : null;
  var provCode = (window.PROVENANCE && window.PROVENANCE[uc.i]) || null;
  var showTagStrip = ta || cimModels || mtypes || uc.escu || (Array.isArray(uc.regs) && uc.regs.length) || uc.status || uc.reviewed || provCode;
  if (showTagStrip) {
    html += '<div class="uc-card-tags">';
    if (uc.status) html += '<span class="uc-card-status ' + esc(uc.status) + '" title="Quality status">' + esc(uc.status) + '</span>';
    if (provCode) {
      var provLabel = (window.PROVENANCE_LABELS && window.PROVENANCE_LABELS[provCode]) || 'Source';
      html += '<span class="uc-card-prov prov-' + esc(provCode) + '" title="Source: ' + esc(provLabel) + ' (see References for details)">' + esc(provLabel) + '</span>';
    }
    html += freshChipHtml(uc.reviewed);
    if (ta) html += '<span class="uc-card-equip">' + esc(ta.substring(0, 40)) + '</span>';
    if (cimModels) html += '<span class="uc-card-cim">' + esc(cimModels.join(', ')) + '</span>';
    if (mtypes) mtypes.forEach(function(t) { html += '<span class="uc-card-tag">' + esc(t) + '</span>'; });
    var pillar = uc.pillar || 'observability';
    if (pillar === 'security' || pillar === 'both') html += '<span class="uc-card-pillar security">Security</span>';
    if (pillar === 'observability' || pillar === 'both') html += '<span class="uc-card-pillar observability">Observability</span>';
    if (Array.isArray(uc.regs) && uc.regs.length) uc.regs.forEach(function(r) { html += '<span class="uc-card-reg">' + esc(r) + '</span>'; });
    if (uc.escu) html += '<span class="uc-card-es">ES Detection' + (uc.escu_rba ? ' (RBA)' : '') + '</span>';
    if (Array.isArray(uc.sapp) && uc.sapp.some(function(a) { return typeof a === 'object' && Array.isArray(a.predecessor) && a.predecessor.length; })) html += '<span class="uc-card-successor">Successor App</span>';
    html += '</div>';
  }
  html += '</div>';
  return html;
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

function clearHeroFilter() {
  ovHeroGroupFilter = null;
  reRender();
}
function clearSearch() {
  currentSearch = '';
  var si = document.getElementById('search-input');
  if (si) si.value = '';
  reRender();
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

function _updateInventoryBadge() {
  var b = document.getElementById('inv-badge');
  if (b) {
    var n = inventorySelections.length;
    b.textContent = n ? String(n) : '';
    b.style.display = n ? 'inline-flex' : 'none';
  }
}

function _saveInventory() {
  try { localStorage.setItem(INVENTORY_STORAGE_KEY, JSON.stringify(inventorySelections)); } catch (e) {}
}

function _loadInventory() {
  try {
    var raw = localStorage.getItem(INVENTORY_STORAGE_KEY);
    if (raw) inventorySelections = JSON.parse(raw) || [];
  } catch (e) { inventorySelections = []; }
}

function updateFilterCountNum() {
  var el = document.getElementById('filter-count-num');
  if (el) el.textContent = getFilteredUCs().length.toLocaleString();
}

function buildSidebar() {
  var sb = document.getElementById('sidebar');
  if (!sb) return;
  var filt = getFilteredUCs();
  var hasFilter = selectedEquipmentId || inventorySelections.length || currentPillarFilter !== 'all' || currentRegulationFilter !== 'all'
    || currentFilter !== 'all' || currentDiffFilter !== 'all' || currentMtypeFilter !== 'all' || currentIndustryFilter !== 'all'
    || currentStatusFilter !== 'all' || currentFreshFilter !== 'all'
    || currentEscuFilter !== 'all' || currentDtypeFilter !== 'all' || currentPremiumFilter !== 'all' || currentCimFilter !== 'all'
    || currentSappFilter !== 'all' || currentMitreFilter || currentMitreTacticFilter || currentDsGroup || currentDatasourceFilter
    || currentTrendFilter || currentSearch;
  var filtByCat = {};
  var filtBySubcat = {};
  if (hasFilter) {
    filt.forEach(function(e) {
      filtByCat[e.cat.i] = (filtByCat[e.cat.i] || 0) + 1;
      filtBySubcat[e.sc.i] = (filtBySubcat[e.sc.i] || 0) + 1;
    });
  }
  if (currentCat != null && !sidebarManualToggle) {
    var catToGroup = {};
    ['infra','security','cloud','app','industry','compliance','business'].forEach(function(g) {
      (CAT_GROUPS[g] || []).forEach(function(id) { catToGroup[id] = g; });
    });
    var ag = catToGroup[currentCat];
    if (ag) { expandedSidebarGroups.clear(); expandedSidebarGroups.add(ag); }
  }
  var html = '<div class="c-sidebar-item' + (!currentCat && !currentSearch ? ' active' : '') + '" onclick="goHome()">' + si('globe') + '<span>Overview</span><span class="c-sidebar-count">' + filt.length + '</span></div>';
  var groupOrder = ['infra','security','cloud','app','industry','compliance','business'];
  groupOrder.forEach(function(g) {
    var ids = CAT_GROUPS[g] || [];
    var groupCount = 0;
    ids.forEach(function(id) {
      if (hasFilter) groupCount += filtByCat[id] || 0;
      else {
        var c = DATA.find(function(d) { return d.i === id; });
        if (c) groupCount += c.s.reduce(function(a, s) { return a + s.u.length; }, 0);
      }
    });
    var isOpen = expandedSidebarGroups.has(g);
    html += '<div class="sb-group"><button type="button" class="sb-group-hd' + (isOpen ? ' open' : '') + '" onclick="toggleSidebarGroup(\'' + g + '\')">' + si('chevronRight') + '<span>' + esc(SIDEBAR_GROUP_LABELS[g] || g) + '</span><span class="c-sidebar-count">' + groupCount + '</span></button>';
    html += '<div class="sb-group-bd' + (isOpen ? ' open' : '') + '">';
    ids.forEach(function(catId) {
      var cat = DATA.find(function(d) { return d.i === catId; });
      if (!cat) return;
      var count = hasFilter ? (filtByCat[cat.i] || 0) : cat.s.reduce(function(a, s) { return a + s.u.length; }, 0);
      var meta = CAT_META[cat.i] || {};
      var active = currentCat === cat.i ? ' active' : '';
      html += '<div class="c-sidebar-item depth' + active + '" tabindex="0" role="button" onclick="selectCat(' + cat.i + ')" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();selectCat(' + cat.i + ')}">' + si(meta.icon || 'globe') + '<span>' + esc(cat.n) + '</span><span class="c-sidebar-count">' + count + '</span></div>';
      html += '<div class="sb-subcats' + (currentCat === cat.i ? ' open' : '') + '">';
      cat.s.forEach(function(sc) {
        var scn = hasFilter ? (filtBySubcat[sc.i] || 0) : sc.u.length;
        if (hasFilter && scn === 0) return;
        var sca = currentSubcat === sc.i ? ' active' : '';
        html += '<div class="sb-subcat' + sca + '" tabindex="0" role="button" onclick="event.stopPropagation();goToSubcat(' + cat.i + ',\'' + String(sc.i).replace(/'/g, "\\'") + '\')" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();event.stopPropagation();goToSubcat(' + cat.i + ',\'' + String(sc.i).replace(/'/g, "\\'") + '\')}">' + esc(sc.n) + '<span class="c-sidebar-count">' + scn + '</span></div>';
      });
      html += '</div>';
    });
    html += '</div></div>';
  });
  sb.innerHTML = html;
}

function roadmapBlock() {
  var h = '<div class="roadmap-hd" onclick="toggleOvSection(this)" role="button" tabindex="0" aria-expanded="false"><span class="ov-collapse-arrow">' + si('chevronRight') + '</span> ' + esc(SITE.roadmapTitle || '') + '</div>';
  h += '<div class="roadmap-body" style="display:none"><p class="roadmap-sub">' + esc(SITE.roadmapSub || '') + '</p><div class="roadmap-grid">';
  [[SITE.phase1Title, SITE.phase1Heading, SITE.phase1Desc], [SITE.phase2Title, SITE.phase2Heading, SITE.phase2Desc], [SITE.phase3Title, SITE.phase3Heading, SITE.phase3Desc], [SITE.phase4Title, SITE.phase4Heading, SITE.phase4Desc]].forEach(function(p) {
    h += '<div class="roadmap-phase"><div class="rp-num">' + esc(p[0] || '') + '</div><h4>' + esc(p[1] || '') + '</h4><p>' + esc(p[2] || '') + '</p></div>';
  });
  h += '</div></div>';
  return h;
}

function renderOverview() {
  window.scrollTo(0, 0);
  if (ucScrollObserver) { ucScrollObserver.disconnect(); ucScrollObserver = null; }
  var main = document.getElementById('main');
  var filteredBase = getFilteredUCs();
  var filtered = filteredBase;
  if (ovHeroGroupFilter && CAT_GROUPS[ovHeroGroupFilter]) {
    var hg = CAT_GROUPS[ovHeroGroupFilter];
    filtered = filtered.filter(function(e) { return hg.indexOf(e.cat.i) !== -1; });
  }
  currentDisplayedList = filtered;
  var totalSubs = DATA.reduce(function(a, c) { return a + c.s.length; }, 0);
  var quickWins = filtered.filter(function(e) { return e.uc.f === 'beginner' && (e.uc.c === 'critical' || e.uc.c === 'high'); }).length;
  var intro = (SITE.heroIntro || '').replace('{useCases}', filtered.length).replace('{categories}', DATA.length);

  var html = '<div class="c-kpi-strip">';
  html += '<div class="c-kpi-card"><div class="c-kpi-num">' + filtered.length.toLocaleString() + '</div><div class="c-kpi-label">' + esc(SITE.statUseCases) + '</div></div>';
  html += '<div class="c-kpi-card"><div class="c-kpi-num">' + DATA.length + '</div><div class="c-kpi-label">' + esc(SITE.statCategories) + '</div></div>';
  html += '<div class="c-kpi-card"><div class="c-kpi-num">' + totalSubs + '</div><div class="c-kpi-label">' + esc(SITE.statSubcategories) + '</div></div>';
  html += '<div class="c-kpi-card"><div class="c-kpi-num">' + quickWins.toLocaleString() + '</div><div class="c-kpi-label">' + esc(SITE.statQuickWins) + '</div></div></div>';

  html += renderHelpBanner();
  html += '<div class="ov-hero-inline"><div class="ov-hero-badge">' + esc(SITE.heroBadge || '') + '</div><h2 class="ov-hero-h2">' + esc(SITE.heroTitle || '') + ' <span>' + esc(SITE.heroTitleSpan || '') + '</span></h2><p>' + esc(intro) + '</p></div>';

  var heroOrder = ['infra','security','cloud','app','industry','compliance','business'];
  var heroLabels = { infra:'Infrastructure', security:'Security', cloud:'Cloud', app:'Applications', industry:'Industry', compliance:'Regulatory & Compliance', business:'Business & Executive' };
  var heroIcons = { infra:'servers', security:'shield', cloud:'cloudNodes', app:'cog', industry:'factory', compliance:'clipboard', business:'chart' };
  html += '<div class="hero-domains">';
  heroOrder.forEach(function(g) {
    var ids = CAT_GROUPS[g] || [];
    var cnt = 0;
    ids.forEach(function(id) {
      var c = DATA.find(function(d) { return d.i === id; });
      if (c) cnt += c.s.reduce(function(a, s) { return a + s.u.length; }, 0);
    });
    var cls = 'hero-chip' + (ovHeroGroupFilter === g ? ' active' : '');
    html += '<button type="button" class="' + cls + '" onclick="filterByHeroGroup(\'' + g + '\')">' + si(heroIcons[g] || 'list') + esc(heroLabels[g]) + '<span class="hd-count">' + cnt + '</span></button>';
  });
  html += '</div>';

  html += filterStrip();
  html += activeFilterTags();

  html += '<div class="ov-tab-bar">';
  [['all', SITE.filterAll || 'Categories'], ['subcats', SITE.statSubcategories || 'Subcategories'], ['alluc', SITE.statUseCases || 'Use Cases'], ['quickwins', SITE.statQuickWins || 'Quick Wins'], ['recent', 'Recently Added']].forEach(function(g) {
    html += '<button type="button" class="ov-tab' + (ovGroupFilter === g[0] ? ' active' : '') + '" onclick="filterOvGroup(\'' + g[0] + '\')">' + esc(g[1]) + '</button>';
  });
  html += '<select class="ov-sort" onchange="setSort(this.value)">';
  [['criticality', '\u2195 Criticality'], ['difficulty', '\u2195 Easiest first'], ['difficulty-desc', '\u2195 Hardest first'], ['name-az', '\u2195 A\u2013Z'], ['name-za', '\u2195 Z\u2013A'], ['category', '\u2195 Category']].forEach(function(s) {
    html += '<option value="' + s[0] + '"' + (currentSort === s[0] ? ' selected' : '') + '>' + s[1] + '</option>';
  });
  html += '</select>';
  html += '<div style="margin-left:auto;display:flex;gap:6px">';
  html += '<button type="button" class="ov-tab" onclick="exportFiltered(\'csv\')" title="Export filtered use cases as CSV">' + si('download') + 'CSV</button>';
  html += '<button type="button" class="ov-tab" onclick="exportFiltered(\'json\')" title="Export filtered use cases as JSON">' + si('download') + 'JSON</button>';
  html += '</div></div>';

  ucAllCardsHtml = [];
  ucGridTargets = [];

  if (ovGroupFilter === 'alluc') {
    var sorted = sortUCs(filtered);
    currentDisplayedList = sorted;
    var byCat = {};
    sorted.forEach(function(e) {
      var k = e.cat.i;
      if (!byCat[k]) byCat[k] = { cat: e.cat, entries: [] };
      byCat[k].entries.push(e);
    });
    var vcStructure = '';
    var vcGridIdx = 0;
    DATA.forEach(function(cat) {
      var g = byCat[cat.i];
      if (!g || !g.entries.length) return;
      var gid = 'uc-vgrid-' + vcGridIdx++;
      vcStructure += '<div class="ov-section"><div class="subcat-header">' + esc(cat.i + '. ' + cat.n) + '<span class="subcat-count">(' + g.entries.length + ')</span></div><div class="uc-grid" id="' + gid + '"></div></div>';
      g.entries.forEach(function(e) {
        ucAllCardsHtml.push(renderUCCard(e.uc));
        ucGridTargets.push(gid);
      });
    });
    html += '<div id="uc-virtual-container">' + vcStructure + '</div>';
  } else if (ovGroupFilter === 'subcats') {
    var filteredBySubcat = {};
    filtered.forEach(function(e) {
      var key = e.cat.i + '.' + (e.sc.i != null ? e.sc.i : '');
      filteredBySubcat[key] = (filteredBySubcat[key] || 0) + 1;
    });
    var hasAny = selectedEquipmentId || inventorySelections.length || currentFilter !== 'all' || currentDiffFilter !== 'all' || currentPillarFilter !== 'all'
      || currentRegulationFilter !== 'all' || currentMtypeFilter !== 'all' || currentIndustryFilter !== 'all' || currentEscuFilter !== 'all'
      || currentStatusFilter !== 'all' || currentFreshFilter !== 'all'
      || currentDtypeFilter !== 'all' || currentPremiumFilter !== 'all' || currentCimFilter !== 'all' || currentSappFilter !== 'all'
      || currentMitreFilter || currentMitreTacticFilter || currentDsGroup || currentDatasourceFilter || currentTrendFilter;
    var visibleSubs = hasAny ? Object.keys(filteredBySubcat).length : totalSubs;
    html += '<div class="ov-section"><h3 class="ov-h3">Subcategories — ' + visibleSubs + '</h3><div class="ov-subcat-list">';
    DATA.forEach(function(cat) {
      cat.s.forEach(function(sc) {
        var key = cat.i + '.' + (sc.i != null ? sc.i : '');
        var subCount = hasAny ? (filteredBySubcat[key] || 0) : sc.u.length;
        if (hasAny && subCount === 0) return;
        html += '<button type="button" class="ov-subcat-row" onclick="goToSubcat(' + cat.i + ',\'' + String(sc.i).replace(/'/g, "\\'") + '\')">';
        html += '<span class="ov-subcat-id">' + esc(sc.i) + '</span><span>' + esc(sc.n) + '</span><span class="ov-subcat-count">' + subCount + '</span></button>';
      });
    });
    html += '</div></div>';
  } else if (ovGroupFilter === 'recent') {
    var recentSet = (typeof RECENTLY_ADDED !== 'undefined') ? RECENTLY_ADDED : new Set();
    var rr = sortUCs(filtered.filter(function(e) { return recentSet.has(e.uc.i); }));
    currentDisplayedList = rr;
    var byCatR = {};
    rr.forEach(function(e) {
      var k = e.cat.i;
      if (!byCatR[k]) byCatR[k] = { cat: e.cat, entries: [] };
      byCatR[k].entries.push(e);
    });
    html += '<div class="ov-section"><h3 class="ov-h3">Recently Added (' + rr.length + ')</h3>';
    if (rr.length === 0) {
      html += '<p style="padding:1rem;opacity:.6">No new use cases since the last build. Run <code>build.py</code> after adding content to populate this tab.</p>';
    }
    Object.values(byCatR).forEach(function(g) {
      html += '<div class="ov-section"><div class="subcat-header">' + esc(g.cat.i + '. ' + g.cat.n) + '</div><div class="uc-grid">';
      g.entries.forEach(function(e) { html += renderUCCard(e.uc); });
      html += '</div></div>';
    });
    html += '</div>';
  } else if (ovGroupFilter === 'quickwins') {
    var qw = sortUCs(filtered.filter(function(e) { return e.uc.f === 'beginner' && (e.uc.c === 'critical' || e.uc.c === 'high'); }));
    currentDisplayedList = qw;
    var byCatQ = {};
    qw.forEach(function(e) {
      var k = e.cat.i;
      if (!byCatQ[k]) byCatQ[k] = { cat: e.cat, entries: [] };
      byCatQ[k].entries.push(e);
    });
    html += '<div class="ov-section"><h3 class="ov-h3">' + esc(SITE.starterListLabel || 'Quick wins') + ' (' + qw.length + ')</h3>';
    Object.values(byCatQ).forEach(function(g) {
      html += '<div class="ov-section"><div class="subcat-header">' + esc(g.cat.i + '. ' + g.cat.n) + '</div><div class="uc-grid">';
      g.entries.forEach(function(e) { html += renderUCCard(e.uc); });
      html += '</div></div>';
    });
    html += '</div>';
  } else {
    var heroCatIds = ovHeroGroupFilter ? CAT_GROUPS[ovHeroGroupFilter] : null;
    html += '<div class="c-cat-grid">';
    DATA.forEach(function(cat) {
      if (heroCatIds && heroCatIds.indexOf(cat.i) === -1) return;
      var count = filtered.filter(function(e) { return e.cat.i === cat.i; }).length;
      var totalCount = cat.s.reduce(function(a, s) { return a + s.u.length; }, 0);
      var disp = (hasAnyFilterActive() ? count : totalCount);
      if ((selectedEquipmentId || inventorySelections.length) && count === 0) return;
      var meta = CAT_META[cat.i] || {};
      html += '<div class="c-cat-card" onclick="selectCat(' + cat.i + ')"><div class="c-cat-card-head"><div class="c-cat-card-icon">' + si(meta.icon || 'globe') + '</div><div><div class="c-cat-card-title">' + esc(cat.n) + '</div>';
      html += '<div class="c-cat-card-num">' + disp + ' use cases · ' + cat.s.length + ' subcategories</div></div></div>';
      html += '<div class="c-cat-card-desc">' + esc(stripMd(meta.desc || '')) + '</div><div class="c-cat-card-footer">';
      cat.s.slice(0, 3).forEach(function(sc) { html += '<span class="c-cat-card-badge">' + esc(sc.n) + '</span>'; });
      if (cat.s.length > 3) html += '<span class="c-cat-card-badge">+' + (cat.s.length - 3) + '</span>';
      html += '</div></div>';
    });
    html += '</div>';
  }

  html += roadmapBlock();
  main.innerHTML = html;
  document.getElementById('back-btn').style.display = 'none';
  updateFilterCountNum();

  if (ovGroupFilter === 'alluc' && ucAllCardsHtml.length > 50) {
    var vc = document.getElementById('uc-virtual-container');
    if (vc) {
      ucRenderedCount = 0;
      renderUCBatch(vc, 0);
      setupUCScrollObserver(vc);
    }
  } else if (ovGroupFilter === 'alluc' && ucAllCardsHtml.length) {
    var vc2 = document.getElementById('uc-virtual-container');
    if (vc2) renderUCBatch(vc2, 0);
  }
}

function hasAnyFilterActive() {
  return selectedEquipmentId || inventorySelections.length || currentFilter !== 'all' || currentDiffFilter !== 'all' || currentPillarFilter !== 'all'
    || currentRegulationFilter !== 'all' || currentMtypeFilter !== 'all' || currentIndustryFilter !== 'all' || currentEscuFilter !== 'all'
    || currentStatusFilter !== 'all' || currentFreshFilter !== 'all'
    || currentDtypeFilter !== 'all' || currentPremiumFilter !== 'all' || currentCimFilter !== 'all' || currentSappFilter !== 'all'
    || currentMitreFilter || currentMitreTacticFilter || currentDsGroup || currentDatasourceFilter || currentTrendFilter || currentSearch;
}

function renderSearchResults() {
  window.scrollTo(0, 0);
  var main = document.getElementById('main');
  var results = getFilteredUCs();
  panelUCList = results;
  currentDisplayedList = results;
  var html = '<div class="c-search-heading">Results for <strong>' + esc(currentSearch) + '</strong> — ' + results.length + ' use cases</div>';
  html += filterStrip() + activeFilterTags();
  if (!results.length) {
    html += emptyState('No matches found');
    main.innerHTML = html;
    updateFilterCountNum();
    document.getElementById('back-btn').style.display = 'none';
    return;
  }
  var SEARCH_RENDER_CAP = 200;
  var capped = !searchShowAll && results.length > SEARCH_RENDER_CAP;
  var renderList = capped ? results.slice(0, SEARCH_RENDER_CAP) : results;
  var grouped = {};
  renderList.forEach(function(e) {
    var k = e.cat.i;
    if (!grouped[k]) grouped[k] = { cat: e.cat, rows: [] };
    grouped[k].rows.push(e);
  });
  Object.keys(grouped).sort(function(a, b) { return a - b; }).forEach(function(k) {
    var g = grouped[k];
    html += '<div class="search-cat-block"><h3 class="subcat-header">' + esc(g.cat.i + '. ' + g.cat.n) + ' <span class="subcat-count">(' + g.rows.length + ')</span></h3>';
    html += '<div class="uc-grid">';
    g.rows.forEach(function(e) { html += renderUCCard(e.uc); });
    html += '</div></div>';
  });
  if (capped) {
    html += '<div style="text-align:center;padding:20px"><button type="button" class="c-chip active" onclick="searchShowAll=true;renderSearchResults()">Show all ' + results.length + ' results</button></div>';
  }
  main.innerHTML = html;
  document.getElementById('back-btn').style.display = 'none';
  updateFilterCountNum();
}

function renderSubcategoryView() {
  window.scrollTo(0, 0);
  var cat = getCatById(currentCat);
  var main = document.getElementById('main');
  if (!cat) { goHome(); return; }
  var catFiltered = getFilteredUCs();
  panelUCList = catFiltered;
  currentDisplayedList = catFiltered;
  var totalCount = cat.s.reduce(function(a, s) { return a + s.u.length; }, 0);
  var meta = CAT_META[cat.i] || {};

  var bySubcat = {};
  catFiltered.forEach(function(e) {
    var key = e.sc.i;
    if (!bySubcat[key]) bySubcat[key] = 0;
    bySubcat[key]++;
  });

  var html = breadcrumb(cat) + filterStrip() + activeFilterTags();
  html += '<div class="c-section-header"><div class="c-section-title">' + esc(cat.n) + '</div>';
  html += '<div class="c-section-desc">' + esc(stripMd(meta.desc || '')) + '</div>';
  html += '<div style="margin-top:6px;font-size:12px;color:var(--text-tertiary)">' + cat.s.length + ' subcategories · ' + catFiltered.length + ' / ' + totalCount + ' use cases</div>';
  html += '</div>';

  html += '<div class="sc-view-grid">';
  cat.s.forEach(function(sc) {
    var scCount = bySubcat[sc.i] || 0;
    var scTotal = sc.u.length;
    var hasFilter = catFiltered.length !== totalCount;
    var displayCount = hasFilter ? scCount : scTotal;
    if (hasFilter && scCount === 0) return;

    var critCounts = { critical: 0, high: 0, medium: 0, low: 0 };
    var entries = catFiltered.filter(function(e) { return e.sc.i === sc.i; });
    entries.forEach(function(e) { if (critCounts[e.uc.c] !== undefined) critCounts[e.uc.c]++; });

    html += '<article class="sc-view-card" onclick="goToSubcat(' + cat.i + ',\'' + String(sc.i).replace(/'/g, "\\'") + '\')">';
    html += '<div class="sc-view-card-head">';
    html += '<span class="sc-view-card-id">' + esc(String(sc.i)) + '</span>';
    html += '<h3 class="sc-view-card-name">' + esc(sc.n) + '</h3>';
    html += '<span class="sc-view-card-count">' + displayCount + ' use cases</span>';
    if (sc.g) html += '<a class="sc-guide-link" href="' + esc(sc.g) + '" onclick="event.stopPropagation()" target="_blank" title="Integration Guide">' + si('external') + ' Guide</a>';
    html += '</div>';

    html += '<div class="sc-view-card-crit">';
    if (critCounts.critical) html += '<span class="sc-crit-dot critical">' + critCounts.critical + ' Critical</span>';
    if (critCounts.high) html += '<span class="sc-crit-dot high">' + critCounts.high + ' High</span>';
    if (critCounts.medium) html += '<span class="sc-crit-dot medium">' + critCounts.medium + ' Medium</span>';
    if (critCounts.low) html += '<span class="sc-crit-dot low">' + critCounts.low + ' Low</span>';
    html += '</div>';

    var topUCs = entries.slice(0, 3);
    if (topUCs.length) {
      html += '<div class="sc-view-card-ucs">';
      topUCs.forEach(function(e) {
        html += '<div class="sc-view-uc-peek" onclick="event.stopPropagation(); openUCById(\'' + esc(e.uc.i) + '\')">';
        html += '<span class="uc-crit-dot c-' + (e.uc.c || 'low') + '"></span>';
        html += '<span class="sc-view-uc-name">' + esc(e.uc.n) + '</span></div>';
      });
      if (entries.length > 3) html += '<div class="sc-view-more">+' + (entries.length - 3) + ' more</div>';
      html += '</div>';
    }
    html += '</article>';
  });
  html += '</div>';

  html += '<div class="sc-view-showall">';
  html += '<button type="button" class="sc-view-showall-btn" onclick="showAllCategoryUCs()">';
  html += si('list') + ' Show all ' + catFiltered.length + ' use cases</button></div>';

  main.innerHTML = html;
  document.getElementById('back-btn').style.display = 'flex';
  updateFilterCountNum();
}

function goToSubcat(catId, scId) {
  currentCat = catId;
  currentSubcat = scId;
  catShowAllUCs = true;
  currentSearch = '';
  document.getElementById('search-input').value = '';
  buildSidebar();
  renderCategory();
  updateHash(false);
  closeMobileSidebar();
  setTimeout(function() {
    var el = document.getElementById('sc-' + String(scId).replace(/\./g, '_'));
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 50);
}

function showAllCategoryUCs() {
  catShowAllUCs = true;
  buildSidebar();
  renderCategory();
  updateHash(false);
}

function renderCategory() {
  window.scrollTo(0, 0);
  var cat = getCatById(currentCat);
  var main = document.getElementById('main');
  if (!cat) { goHome(); return; }
  var filtered = getFilteredUCs();
  panelUCList = filtered;
  currentDisplayedList = filtered;
  var meta = CAT_META[cat.i] || {};
  var html = breadcrumb(cat) + filterStrip() + activeFilterTags();
  html += '<div class="c-section-header"><div class="c-section-title">' + esc(cat.n) + '</div><div class="c-section-desc">' + esc(stripMd(meta.desc || '')) + '</div></div>';
  if (currentSearch) {
    html += '<div class="c-search-heading">Filtered in category</div>';
    html += '<div class="uc-grid">';
    filtered.forEach(function(e) { html += renderUCCard(e.uc); });
    html += '</div>';
  } else {
    html += renderCategoryRoadmap(cat.i);
    cat.s.forEach(function(sc) {
      var scUCs = filtered.filter(function(e) { return e.sc.i === sc.i; });
      if (!scUCs.length) return;
      var sid = 'sc-' + String(sc.i).replace(/\./g, '_');
      var guideBtn = sc.g ? ' <a class="sc-guide-link" href="' + esc(sc.g) + '" target="_blank" title="Integration Guide">' + si('external') + ' Integration Guide</a>' : '';
      html += '<div class="c-subcat-group" id="' + sid + '"><div class="c-subcat-title">' + esc(sc.n) + ' (' + scUCs.length + ')' + guideBtn + '</div>';
      html += '<div class="uc-grid">';
      scUCs.forEach(function(e) { html += renderUCCard(e.uc); });
      html += '</div></div>';
    });
  }
  if (!filtered.length) html += emptyState('No use cases match your filters');
  main.innerHTML = html;
  document.getElementById('back-btn').style.display = 'flex';
  updateFilterCountNum();
}

function ntVizMockups(vizStr) {
  if (!vizStr) return '';
  var v = vizStr.toLowerCase();
  var panels = [];
  var cb = 'var(--cisco-blue)';
  var ct = 'var(--text-tertiary)';
  var cs = 'var(--text-secondary)';
  var cp = 'var(--text-primary)';
  var bd = 'var(--border-default)';
  var bg = 'var(--bg-page)';
  var be = 'var(--bg-elevated)';
  var cg = 'var(--cisco-green)';
  var cr = 'var(--cisco-red)';
  if (v.indexOf('line chart') !== -1 || v.indexOf('timechart') !== -1) {
    panels.push({ title: 'Trend over time', svg: '<svg viewBox="0 0 240 100" class="ntviz-svg"><rect x="0" y="0" width="240" height="100" rx="4" fill="' + bg + '"/><line x1="30" y1="10" x2="30" y2="85" stroke="' + bd + '" stroke-width="1"/><line x1="30" y1="85" x2="230" y2="85" stroke="' + bd + '" stroke-width="1"/><polyline points="35,70 65,55 95,60 125,35 155,45 185,25 215,30" fill="none" stroke="' + cb + '" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><polyline points="35,75 65,68 95,72 125,58 155,62 185,50 215,55" fill="none" stroke="' + ct + '" stroke-width="1.5" stroke-dasharray="4,3" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/><text x="30" y="96" fill="' + ct + '" font-size="7">Time</text></svg>' });
  }
  if (v.indexOf('area chart') !== -1) {
    panels.push({ title: 'Usage over time', svg: '<svg viewBox="0 0 240 100" class="ntviz-svg"><rect x="0" y="0" width="240" height="100" rx="4" fill="' + bg + '"/><line x1="30" y1="10" x2="30" y2="85" stroke="' + bd + '" stroke-width="1"/><line x1="30" y1="85" x2="230" y2="85" stroke="' + bd + '" stroke-width="1"/><path d="M35,70 L65,50 L95,55 L125,35 L155,40 L185,30 L215,35 L215,85 L35,85 Z" fill="rgba(4,159,217,0.2)" stroke="' + cb + '" stroke-width="2"/></svg>' });
  }
  if (v.indexOf('bar chart') !== -1 || v.indexOf('column chart') !== -1) {
    panels.push({ title: 'Comparison', svg: '<svg viewBox="0 0 240 100" class="ntviz-svg"><rect x="0" y="0" width="240" height="100" rx="4" fill="' + bg + '"/><line x1="30" y1="85" x2="230" y2="85" stroke="' + bd + '" stroke-width="1"/><rect x="45" y="30" width="22" height="55" rx="2" fill="' + cb + '" opacity="0.8"/><rect x="80" y="45" width="22" height="40" rx="2" fill="' + cb + '" opacity="0.65"/><rect x="115" y="20" width="22" height="65" rx="2" fill="' + cb + '" opacity="0.9"/><rect x="150" y="55" width="22" height="30" rx="2" fill="' + cb + '" opacity="0.5"/><rect x="185" y="40" width="22" height="45" rx="2" fill="' + cb + '" opacity="0.7"/></svg>' });
  }
  if (v.indexOf('single value') !== -1) {
    panels.push({ title: 'Current status', svg: '<svg viewBox="0 0 160 90" class="ntviz-svg ntviz-sv"><rect x="0" y="0" width="160" height="90" rx="4" fill="' + bg + '"/><text x="80" y="50" text-anchor="middle" fill="' + cb + '" font-size="28" font-weight="700">94.2%</text><text x="80" y="70" text-anchor="middle" fill="' + ct + '" font-size="9">Current value</text></svg>' });
  }
  if (v.indexOf('gauge') !== -1) {
    panels.push({ title: 'Threshold gauge', svg: '<svg viewBox="0 0 160 100" class="ntviz-svg ntviz-sv"><rect x="0" y="0" width="160" height="100" rx="4" fill="' + bg + '"/><path d="M30,75 A50,50 0 0,1 130,75" fill="none" stroke="' + bd + '" stroke-width="8" stroke-linecap="round"/><path d="M30,75 A50,50 0 0,1 110,38" fill="none" stroke="' + cb + '" stroke-width="8" stroke-linecap="round"/><text x="80" y="80" text-anchor="middle" fill="' + cp + '" font-size="14" font-weight="700">72%</text><text x="80" y="93" text-anchor="middle" fill="' + ct + '" font-size="8">of threshold</text></svg>' });
  }
  if (v.indexOf('table') !== -1) {
    panels.push({ title: 'Details table', svg: '<svg viewBox="0 0 240 100" class="ntviz-svg"><rect x="0" y="0" width="240" height="100" rx="4" fill="' + bg + '"/><rect x="10" y="10" width="220" height="14" rx="2" fill="' + cb + '" opacity="0.15"/><text x="18" y="20" fill="' + cb + '" font-size="7" font-weight="600">Host</text><text x="90" y="20" fill="' + cb + '" font-size="7" font-weight="600">Status</text><text x="160" y="20" fill="' + cb + '" font-size="7" font-weight="600">Value</text><line x1="10" y1="26" x2="230" y2="26" stroke="' + bd + '" stroke-width="0.5"/><text x="18" y="36" fill="' + cs + '" font-size="7">server-01</text><text x="90" y="36" fill="' + cg + '" font-size="7">OK</text><text x="160" y="36" fill="' + cs + '" font-size="7">23.4%</text><line x1="10" y1="40" x2="230" y2="40" stroke="' + bd + '" stroke-width="0.3"/><text x="18" y="50" fill="' + cs + '" font-size="7">server-02</text><text x="90" y="50" fill="' + cr + '" font-size="7">Warning</text><text x="160" y="50" fill="' + cs + '" font-size="7">87.1%</text><line x1="10" y1="54" x2="230" y2="54" stroke="' + bd + '" stroke-width="0.3"/><text x="18" y="64" fill="' + cs + '" font-size="7">server-03</text><text x="90" y="64" fill="' + cs + '" font-size="7">OK</text><text x="160" y="64" fill="' + cs + '" font-size="7">41.7%</text></svg>' });
  }
  if (v.indexOf('heatmap') !== -1) {
    var cells = '';
    var colors = ['rgba(4,159,217,0.15)','rgba(4,159,217,0.3)','rgba(4,159,217,0.5)','rgba(4,159,217,0.7)','rgba(4,159,217,0.9)','rgba(229,57,53,0.6)','rgba(229,57,53,0.3)'];
    for (var r = 0; r < 4; r++) { for (var c = 0; c < 8; c++) { cells += '<rect x="' + (30 + c * 25) + '" y="' + (15 + r * 18) + '" width="22" height="15" rx="2" fill="' + colors[(r * 8 + c + r * 3) % colors.length] + '"/>'; } }
    panels.push({ title: 'Heatmap', svg: '<svg viewBox="0 0 240 100" class="ntviz-svg"><rect x="0" y="0" width="240" height="100" rx="4" fill="' + bg + '"/>' + cells + '</svg>' });
  }
  if (v.indexOf('pie') !== -1 || v.indexOf('donut') !== -1) {
    panels.push({ title: 'Distribution', svg: '<svg viewBox="0 0 160 100" class="ntviz-svg ntviz-sv"><rect x="0" y="0" width="160" height="100" rx="4" fill="' + bg + '"/><circle cx="80" cy="50" r="35" fill="none" stroke="' + bd + '" stroke-width="12"/><circle cx="80" cy="50" r="35" fill="none" stroke="' + cb + '" stroke-width="12" stroke-dasharray="154 66" stroke-dashoffset="0" transform="rotate(-90 80 50)"/><circle cx="80" cy="50" r="35" fill="none" stroke="' + ct + '" stroke-width="12" stroke-dasharray="44 176" stroke-dashoffset="-154" transform="rotate(-90 80 50)" opacity="0.5"/><text x="80" y="54" text-anchor="middle" fill="' + cp + '" font-size="12" font-weight="700">70%</text></svg>' });
  }
  if (v.indexOf('status') !== -1 || v.indexOf('grid') !== -1) {
    var dots = ''; var dC = [cb,cb,cb,cr,cb,cb,cb,cb,cb,cb,cb,cb];
    for (var di = 0; di < 12; di++) { dots += '<circle cx="' + (30 + (di % 6) * 34) + '" cy="' + (30 + Math.floor(di / 6) * 34) + '" r="10" fill="' + dC[di] + '" opacity="0.8"/>'; }
    panels.push({ title: 'Status grid', svg: '<svg viewBox="0 0 240 100" class="ntviz-svg"><rect x="0" y="0" width="240" height="100" rx="4" fill="' + bg + '"/>' + dots + '</svg>' });
  }
  if (v.indexOf('timeline') !== -1) {
    panels.push({ title: 'Event timeline', svg: '<svg viewBox="0 0 240 80" class="ntviz-svg"><rect x="0" y="0" width="240" height="80" rx="4" fill="' + bg + '"/><line x1="20" y1="40" x2="220" y2="40" stroke="' + bd + '" stroke-width="1.5"/><circle cx="40" cy="40" r="5" fill="' + cb + '"/><circle cx="85" cy="40" r="5" fill="' + cb + '"/><circle cx="110" cy="40" r="5" fill="' + cr + '"/><circle cx="150" cy="40" r="5" fill="' + cb + '"/><circle cx="200" cy="40" r="5" fill="' + cb + '"/><text x="40" y="55" text-anchor="middle" fill="' + ct + '" font-size="6">09:00</text><text x="110" y="55" text-anchor="middle" fill="' + cr + '" font-size="6">11:42</text><text x="200" y="55" text-anchor="middle" fill="' + ct + '" font-size="6">16:30</text></svg>' });
  }
  if (panels.length === 0) {
    panels.push({ title: 'Dashboard overview', svg: '<svg viewBox="0 0 320 140" class="ntviz-svg"><rect x="0" y="0" width="320" height="140" rx="4" fill="' + bg + '"/><rect x="8" y="8" width="94" height="40" rx="3" fill="' + be + '" stroke="' + bd + '" stroke-width="0.5"/><text x="55" y="28" text-anchor="middle" fill="' + cb + '" font-size="14" font-weight="700">247</text><text x="55" y="40" text-anchor="middle" fill="' + ct + '" font-size="6">Events</text><rect x="110" y="8" width="94" height="40" rx="3" fill="' + be + '" stroke="' + bd + '" stroke-width="0.5"/><text x="157" y="28" text-anchor="middle" fill="' + cp + '" font-size="14" font-weight="700">99.4%</text><text x="157" y="40" text-anchor="middle" fill="' + ct + '" font-size="6">Availability</text><rect x="212" y="8" width="100" height="40" rx="3" fill="' + be + '" stroke="' + bd + '" stroke-width="0.5"/><text x="262" y="28" text-anchor="middle" fill="' + cr + '" font-size="14" font-weight="700">3</text><text x="262" y="40" text-anchor="middle" fill="' + ct + '" font-size="6">Alerts</text><rect x="8" y="56" width="200" height="76" rx="3" fill="' + be + '" stroke="' + bd + '" stroke-width="0.5"/><line x1="28" y1="70" x2="28" y2="120" stroke="' + bd + '" stroke-width="0.5"/><line x1="28" y1="120" x2="195" y2="120" stroke="' + bd + '" stroke-width="0.5"/><polyline points="35,110 60,100 85,105 110,88 135,92 160,80 185,84" fill="none" stroke="' + cb + '" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="108" y="68" text-anchor="middle" fill="' + ct + '" font-size="6">Trend over time</text><rect x="216" y="56" width="96" height="76" rx="3" fill="' + be + '" stroke="' + bd + '" stroke-width="0.5"/><text x="264" y="68" text-anchor="middle" fill="' + ct + '" font-size="6">By host</text><rect x="228" y="76" width="72" height="8" rx="1" fill="' + bd + '"/><rect x="228" y="76" width="58" height="8" rx="1" fill="' + cb + '" opacity="0.7"/><rect x="228" y="88" width="72" height="8" rx="1" fill="' + bd + '"/><rect x="228" y="88" width="44" height="8" rx="1" fill="' + cb + '" opacity="0.5"/><rect x="228" y="100" width="72" height="8" rx="1" fill="' + bd + '"/><rect x="228" y="100" width="30" height="8" rx="1" fill="' + cb + '" opacity="0.4"/><rect x="228" y="112" width="72" height="8" rx="1" fill="' + bd + '"/><rect x="228" y="112" width="18" height="8" rx="1" fill="' + cr + '" opacity="0.6"/></svg>' });
  }
  var html = '<div class="ntviz-panels">';
  panels.forEach(function(p) { html += '<div class="ntviz-panel"><div class="ntviz-panel-title">' + esc(p.title) + '</div>' + p.svg + '</div>'; });
  html += '</div>';
  return html;
}
