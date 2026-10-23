// "Start here" wizard + paste-sourcetypes matcher (guided onboarding).
// Uses the pure planner in 07-starter-plan.js. Data comes from
// api/v1/starter-packs/index.json and (lazily, for UC counts and unknown
// sourcetypes) api/v1/recommender/sourcetype-index.json. Never loads
// catalog.json and never sends pasted data anywhere.

var START_HELPER_SPL = '| tstats count where (index=* OR index=_*) by index, sourcetype';
var START_QUICK_EQUIPMENT = [
  { id: 'splunk', label: 'Splunk platform itself' },
  { id: 'windows', label: 'Windows servers' },
  { id: 'linux', label: 'Linux servers' },
  { id: 'cisco_catalyst_center', label: 'Cisco Catalyst Center (DNA Center)' },
  { id: 'cisco_thousandeyes', label: 'Cisco ThousandEyes' },
  { id: 'cisco_meraki', label: 'Cisco Meraki' },
  { id: 'cisco_ise', label: 'Cisco ISE' },
  { id: 'paloalto_pan_firewall', label: 'Palo Alto Networks firewalls' }
];
var START_LEVELS = [
  { id: 'beginner', label: 'New to Splunk', hint: 'I have not built searches or alerts yet.' },
  { id: 'intermediate', label: 'Some experience', hint: 'I can edit SPL and schedule alerts.' },
  { id: 'advanced', label: 'Experienced', hint: 'I tune searches and manage add-ons.' }
];
var START_MAX_LINK_SOURCETYPES = 200;

// No initialisers: initApp() (05-app.js) may run before this file's
// top-level statements and open the wizard from a #start deep link.
var startState;
var _spIndex;
var _spIndexPromise;
var _spStIndex;
var _spStIndexPromise;

function _startDefaults() {
  return {
    step: 1, goal: '', level: 'beginner', cloud: false,
    equipment: [], sourcetypes: [], indexes: [], preview: false, pasteText: ''
  };
}

function _spApiURL(rel) {
  var base = (typeof window.__SITE_BASE_PATH === 'string' && window.__SITE_BASE_PATH)
    ? window.__SITE_BASE_PATH.replace(/\/+$/, '')
    : '';
  return (base ? base + '/' : '/') + rel.replace(/^\/+/, '');
}

function _spEnsureIndex() {
  if (_spIndex) return Promise.resolve(_spIndex);
  if (_spIndexPromise) return _spIndexPromise;
  _spIndexPromise = fetch(_spApiURL('api/v1/starter-packs/index.json'), { credentials: 'same-origin' })
    .then(function(res) { if (!res.ok) throw new Error('starter-packs HTTP ' + res.status); return res.json(); })
    .then(function(data) { _spIndex = data && Array.isArray(data.packs) ? data : { packs: [], sourcetypeAliases: [] }; return _spIndex; })
    .catch(function(err) {
      console.warn('[start] starter-packs fetch failed:', err);
      _spIndex = { packs: [], sourcetypeAliases: [], _error: true };
      return _spIndex;
    });
  return _spIndexPromise;
}

function _spEnsureSourcetypeIndex() {
  if (_spStIndex) return Promise.resolve(_spStIndex);
  if (_spStIndexPromise) return _spStIndexPromise;
  _spStIndexPromise = fetch(_spApiURL('api/v1/recommender/sourcetype-index.json'), { credentials: 'same-origin' })
    .then(function(res) { if (!res.ok) throw new Error('sourcetype-index HTTP ' + res.status); return res.json(); })
    .then(function(data) { _spStIndex = (data && data.sourcetypes) || {}; return _spStIndex; })
    .catch(function(err) { console.warn('[start] sourcetype-index fetch failed:', err); _spStIndex = {}; return _spStIndex; });
  return _spStIndexPromise;
}

function _spPackById(id) {
  var packs = (_spIndex && _spIndex.packs) || [];
  for (var i = 0; i < packs.length; i++) if (packs[i].id === id) return packs[i];
  return null;
}

// --- hash ------------------------------------------------------------------

function startHashString() {
  var s = startState || _startDefaults();
  var parts = [];
  if (s.goal) parts.push('goal=' + s.goal);
  if (s.level && s.level !== 'beginner') parts.push('level=' + s.level);
  if (s.cloud) parts.push('cloud=1');
  if (s.equipment.length) parts.push('eq=' + s.equipment.map(encodeURIComponent).join(','));
  if (s.sourcetypes.length) parts.push('st=' + s.sourcetypes.slice(0, START_MAX_LINK_SOURCETYPES).map(encodeURIComponent).join(','));
  if (s.indexes.length) parts.push('ix=' + s.indexes.map(encodeURIComponent).join(','));
  if (s.preview) parts.push('preview=1');
  if (s.step > 1) parts.push('step=' + s.step);
  return '#start' + (parts.length ? '?' + parts.join('&') : '');
}

function parseStartHash(h) {
  var s = _startDefaults();
  var m = String(h || '').match(/^start(?:\?(.*))?$/);
  if (!m || !m[1]) return s;
  m[1].split('&').forEach(function(kv) {
    var i = kv.indexOf('=');
    if (i < 1) return;
    var k = kv.slice(0, i);
    var v = kv.slice(i + 1);
    function list() {
      return v.split(',').map(function(x) { try { return decodeURIComponent(x).trim().toLowerCase(); } catch (_) { return ''; } })
        .filter(function(x) { return x; });
    }
    if (k === 'goal' && (v === 'security' || v === 'operations')) s.goal = v;
    else if (k === 'level' && /^(beginner|intermediate|advanced|expert)$/.test(v)) s.level = v;
    else if (k === 'cloud') s.cloud = v === '1';
    else if (k === 'eq') s.equipment = list();
    else if (k === 'st') s.sourcetypes = list();
    else if (k === 'ix') s.indexes = list();
    else if (k === 'preview') s.preview = v === '1';
    else if (k === 'step') s.step = Math.min(4, Math.max(1, parseInt(v, 10) || 1));
  });
  if (!s.goal && s.step > 1) s.step = 1;
  return s;
}

function _startSyncHash() {
  if (!startState) return;
  history.replaceState(null, '', startHashString());
}

// --- open / close ------------------------------------------------------------

function openStartWizard(initial) {
  var fromHash = initial && typeof initial === 'object';
  startState = fromHash ? initial : _startDefaults();
  if (!startState.equipment.length && typeof inventorySelections !== 'undefined' && inventorySelections.length) {
    startState.equipment = inventorySelections.slice();
  }
  var ov = document.getElementById('start-overlay');
  if (!ov) return;
  ov.classList.add('open');
  document.body.classList.add('overlay-open');
  if (fromHash) history.replaceState(null, '', startHashString());
  else history.pushState(null, '', startHashString());
  _startRender();
  _spEnsureIndex().then(_startRender);
  if (startState.sourcetypes.length || startState.indexes.length) _spEnsureSourcetypeIndex().then(_startRender);
}

function closeStartWizard(fromRouter) {
  var ov = document.getElementById('start-overlay');
  if (!ov || !ov.classList.contains('open')) return;
  ov.classList.remove('open');
  startState = null;
  if (typeof _maybeClearOverlayClass === 'function') _maybeClearOverlayClass();
  if (!fromRouter && typeof updateHash === 'function') updateHash(false);
}

function isStartWizardOpen() {
  var ov = document.getElementById('start-overlay');
  return !!(ov && ov.classList.contains('open'));
}

// --- step handlers -------------------------------------------------------------

function startSetGoal(goal) { startState.goal = goal; startState.step = 2; _startSyncHash(); _startRender(); }
function startSetLevel(level) { startState.level = level; _startSyncHash(); _startRender(); }
function startSetCloud(on) { startState.cloud = !!on; _startSyncHash(); _startRender(); }
function startTogglePreview(on) { startState.preview = !!on; _startSyncHash(); _startRender(); }
function startGo(step) {
  if (step > 1 && !startState.goal) step = 1;
  if (startState.step === 3) _startCapturePaste();
  startState.step = step;
  _startSyncHash();
  _startRender();
  if (step === 4) _spEnsureSourcetypeIndex().then(_startRender);
}
function startToggleEquipment(id, on) {
  var set = startState.equipment.filter(function(e) { return e !== id; });
  if (on) set.push(id);
  startState.equipment = set.sort();
  _startSyncHash();
}
function _startCapturePaste() {
  var ta = document.getElementById('start-paste');
  if (!ta) return;
  startState.pasteText = ta.value;
  if (ta.value.trim()) {
    var parsed = spParsePaste(ta.value);
    startState.sourcetypes = parsed.sourcetypes;
    startState.indexes = parsed.indexes;
  }
}
function startAnalyzePaste() { _startCapturePaste(); startGo(4); }
function startClearData() {
  startState.sourcetypes = []; startState.indexes = []; startState.pasteText = '';
  _startSyncHash(); _startRender();
}
function startCopyHelper() {
  _startCopy(START_HELPER_SPL, 'Search copied. Run it in Splunk over the last 7 days, then paste the results here.');
}

function _startCopy(text, okMsg) {
  function fallback() {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); showToast(okMsg); } catch (_) { showToast('Copy failed. Select the text and copy it manually.'); }
    document.body.removeChild(ta);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function() { showToast(okMsg); }, fallback);
  } else fallback();
}

// --- plan --------------------------------------------------------------------

function startComputePlan() {
  var s = startState;
  return spPlanRollout(_spIndex || { packs: [] }, {
    goal: s.goal, level: s.level, sourcetypes: s.sourcetypes, indexes: s.indexes,
    equipment: s.equipment, includeDrafts: s.preview
  });
}

function _startDataSummary() {
  var s = startState;
  var aliases = spAliasMap((_spIndex && _spIndex.sourcetypeAliases) || []);
  var packKeys = {};
  ((_spIndex && _spIndex.packs) || []).forEach(function(p) {
    (p.steps || []).forEach(function(st) { (st.sourcetypes || []).forEach(function(x) { packKeys[spNormalise(x, aliases)] = true; }); });
  });
  var ucs = {};
  var unknown = [];
  var reverse = {};
  Object.keys(aliases).forEach(function(k) { (reverse[aliases[k]] = reverse[aliases[k]] || []).push(k); });
  s.sourcetypes.forEach(function(raw) {
    var canon = spNormalise(raw, aliases);
    var variants = [raw, canon].concat(reverse[canon] || []);
    var known = !!packKeys[canon];
    variants.forEach(function(v) {
      var ids = _spStIndex && _spStIndex[v];
      if (ids && ids.length) { known = true; ids.forEach(function(id) { ucs[id] = true; }); }
    });
    if (!known && _spStIndex) unknown.push(raw);
  });
  return { ucCount: Object.keys(ucs).length, unknown: unknown, indexLoaded: !!_spStIndex };
}

function _startPublishedCount(goal) {
  return ((_spIndex && _spIndex.packs) || []).filter(function(p) { return p.goal === goal && p.status === 'published'; }).length;
}

// --- exports -----------------------------------------------------------------

function _startShareURL() {
  return location.href.split('#')[0] + startHashString();
}

function _startPlanMarkdown(plan) {
  var s = startState;
  var lines = ['# Splunk starter plan', '',
    '- Goal: ' + s.goal, '- Experience: ' + s.level, '- Platform: ' + (s.cloud ? 'Splunk Cloud' : 'Splunk Enterprise'),
    '- Equipment: ' + (s.equipment.join(', ') || 'none selected'),
    '- Sourcetypes: ' + (s.sourcetypes.length ? s.sourcetypes.length + ' detected' : 'none pasted'), ''];
  if (plan.steps.length) {
    lines.push('## Use cases, in order', '');
    plan.steps.forEach(function(st) {
      lines.push(st.position + '. **' + st.ucId + '** ' + st.title + ' (pack: ' + st.packId + ', difficulty: ' + (st.difficulty || 'n/a')
        + (st.difficultyWarning ? ', above your level' : '') + (st.ready ? '' : ', needs data') + ')');
    });
    lines.push('');
  } else {
    lines.push(plan.emptyReason === 'no-input'
      ? 'No plan yet: paste your sourcetypes or pick your equipment.'
      : 'None of the ' + s.goal + ' packs match your data yet. Onboard one of the data sources below first.', '');
  }
  if (plan.nextSources.length) {
    lines.push('## Next data sources to onboard', '');
    plan.nextSources.forEach(function(n) {
      lines.push('- ' + (n.kind === 'index' ? 'index ' : 'sourcetype ') + '`' + n.name + '` unlocks ' + n.unlocks + ' step(s) in ' + n.packs.join(', '));
    });
    lines.push('');
  }
  lines.push('Link: ' + _startShareURL());
  return lines.join('\n') + '\n';
}

function _startPlanCSV(plan) {
  var rows = [['Position', 'UC ID', 'Title', 'Pack', 'Difficulty', 'Above level', 'Wave', 'Criticality', 'Ready'].join(',')];
  plan.steps.forEach(function(st) {
    rows.push([st.position, st.ucId, _csvQ(st.title), st.packId, st.difficulty, st.difficultyWarning ? 'yes' : 'no',
      st.wave, st.criticality, st.ready ? 'yes' : 'no'].join(','));
  });
  return rows.join('\n') + '\n';
}

function _startAIPrompt(plan) {
  var s = startState;
  var out = [
    'I am ' + (s.level === 'beginner' ? 'new to Splunk' : 'a ' + s.level + ' Splunk user') + ' running '
      + (s.cloud ? 'Splunk Cloud' : 'Splunk Enterprise') + '. My goal is ' + s.goal + ' monitoring.',
    'My data (sourcetypes): ' + (s.sourcetypes.slice(0, 60).join(', ') || 'not provided')
      + (s.indexes.length ? '. Internal indexes I can read: ' + s.indexes.filter(function(i) { return i.charAt(0) === '_'; }).join(', ') : '') + '.',
    'My equipment: ' + (s.equipment.join(', ') || 'not provided') + '.',
    '',
    'The Splunk Monitoring Use Cases catalogue suggests this order:'
  ];
  plan.steps.forEach(function(st) {
    out.push(st.position + '. ' + st.ucId + ' — ' + st.title + ' (' + (st.difficulty || 'n/a') + (st.ready ? '' : ', needs data') + ')');
  });
  if (!plan.steps.length) out.push('(no use cases match yet)');
  if (plan.nextSources.length) {
    out.push('', 'Data sources that would unlock more: ' + plan.nextSources.map(function(n) { return n.name; }).join(', ') + '.');
  }
  out.push('',
    'For each use case, fetch its details from ' + location.origin + _spApiURL('uc/') + '<UC-ID>/uc.md and walk me through:',
    '1. what it detects and why it matters, 2. the data I must confirm is arriving, 3. how to paste and schedule the SPL as an alert,',
    '4. how to tune false positives. Go one use case at a time and wait for me to confirm before moving on.');
  return out.join('\n') + '\n';
}

function startExport(kind) {
  var plan = startComputePlan();
  var date = new Date().toISOString().slice(0, 10);
  if (kind === 'link') _startCopy(_startShareURL(), 'Link copied.');
  else if (kind === 'md') _downloadBlob(new Blob([_startPlanMarkdown(plan)], { type: 'text/markdown;charset=utf-8' }), 'splunk-starter-plan-' + date + '.md');
  else if (kind === 'csv') _downloadBlob(new Blob([_startPlanCSV(plan)], { type: 'text/csv;charset=utf-8' }), 'splunk-starter-plan-' + date + '.csv');
  else if (kind === 'ai') _startCopy(_startAIPrompt(plan), 'AI prompt copied. Paste it into your assistant.');
}

function startOpenUC(ucId) {
  closeStartWizard(true);
  openUCById(String(ucId).replace(/^UC-/, ''));
  buildSidebar();
}

// --- render ------------------------------------------------------------------

function _startProgress() {
  var labels = ['Goal', 'Experience', 'Your data', 'Your plan'];
  return '<ol class="start-progress" aria-label="Wizard progress">' + labels.map(function(l, i) {
    var n = i + 1;
    var cls = n === startState.step ? ' current' : (n < startState.step ? ' done' : '');
    var reachable = n === 1 || !!startState.goal;
    return '<li class="start-progress-item' + cls + '">' + (reachable
      ? '<button type="button" onclick="startGo(' + n + ')"' + (n === startState.step ? ' aria-current="step"' : '') + '>' + n + '. ' + esc(l) + '</button>'
      : '<span>' + n + '. ' + esc(l) + '</span>') + '</li>';
  }).join('') + '</ol>';
}

function _startChoice(selected, onclick, title, hint) {
  return '<button type="button" class="start-choice' + (selected ? ' selected' : '') + '" aria-pressed="' + (selected ? 'true' : 'false') + '" onclick="' + onclick + '">'
    + '<span class="start-choice-title">' + esc(title) + '</span>'
    + (hint ? '<span class="start-choice-hint">' + esc(hint) + '</span>' : '') + '</button>';
}

function _startStepGoal() {
  var g = startState.goal;
  return '<h3 class="start-q">What do you want Splunk to do for you first?</h3>'
    + '<div class="start-choices">'
    + _startChoice(g === 'security', "startSetGoal('security')", 'Catch attackers', 'Security: suspicious logins, privilege changes, tampering.')
    + _startChoice(g === 'operations', "startSetGoal('operations')", 'Keep things running', 'Operations: outages, full disks, failed services, slow networks.')
    + '</div>';
}

function _startStepLevel() {
  var s = startState;
  var html = '<h3 class="start-q">How much Splunk experience do you have?</h3><div class="start-choices">';
  START_LEVELS.forEach(function(l) { html += _startChoice(s.level === l.id, "startSetLevel('" + l.id + "')", l.label, l.hint); });
  html += '</div><p class="start-note">This only adds a warning to harder use cases. Nothing is hidden.</p>';
  html += '<h3 class="start-q">Where does your Splunk run?</h3><div class="start-choices">'
    + _startChoice(!s.cloud, 'startSetCloud(false)', 'Splunk Enterprise', 'I run Splunk on my own servers.')
    + _startChoice(s.cloud, 'startSetCloud(true)', 'Splunk Cloud', 'Splunk hosts it for me.')
    + '</div>';
  return html;
}

function _startStepData() {
  var s = startState;
  var html = '<h3 class="start-q">What do you have? Pick your equipment.</h3><div class="start-eq">';
  var quickIds = {};
  START_QUICK_EQUIPMENT.forEach(function(q) {
    quickIds[q.id] = true;
    var on = s.equipment.indexOf(q.id) !== -1;
    html += '<label class="start-eq-item"><input type="checkbox"' + (on ? ' checked' : '') + ' onchange="startToggleEquipment(\'' + q.id + '\', this.checked)"> ' + esc(q.label) + '</label>';
  });
  html += '</div>';
  var others = s.equipment.filter(function(e) { return !quickIds[e]; });
  if (others.length) {
    html += '<p class="start-note">Also from My Equipment: ' + others.map(function(e) { return '<code>' + esc(e) + '</code>'; }).join(' ') + '</p>';
  }
  html += '<h3 class="start-q">Optional: paste what is already in your Splunk</h3>'
    + '<ol class="start-howto"><li>Run this search in Splunk (last 7 days is enough): '
    + '<code class="start-spl">' + esc(START_HELPER_SPL) + '</code> '
    + '<button type="button" class="inv-btn" onclick="startCopyHelper()">Copy search</button></li>'
    + '<li>Copy the results table and paste it below. A plain list of sourcetypes also works.</li></ol>'
    + '<textarea id="start-paste" class="start-paste" rows="7" spellcheck="false" aria-label="Paste sourcetypes" placeholder="index&#9;sourcetype&#9;count&#10;_internal&#9;splunkd&#9;120394&#10;wineventlog&#9;XmlWinEventLog&#9;88410">'
    + esc(s.pasteText) + '</textarea>'
    + '<p class="start-note">Parsed in your browser only. Nothing is uploaded.</p>';
  if (s.sourcetypes.length || s.indexes.length) {
    html += '<p class="start-note">Currently using ' + s.sourcetypes.length + ' sourcetype(s) and ' + s.indexes.length
      + ' index(es). <button type="button" class="start-link" onclick="startClearData()">Clear</button></p>';
  }
  return html;
}

function _startUnlockLabel(p) {
  if (p.unlock === 'full') return '<span class="start-badge ok">Ready</span>';
  if (p.unlock === 'partial') return '<span class="start-badge part">Partly ready (' + p.readySteps + '/' + p.totalSteps + ')</span>';
  return '<span class="start-badge need">Needs data</span>';
}

function _startStepPlan() {
  var s = startState;
  if (!_spIndex) return '<p class="start-note">Loading starter packs…</p>';
  if (_spIndex._error) return '<p class="start-note">Starter packs could not be loaded. Try again later.</p>';
  var plan = startComputePlan();
  var summary = _startDataSummary();
  var html = '';

  var published = _startPublishedCount(s.goal);
  if (!published) {
    html += '<div class="start-callout">No ' + esc(s.goal) + ' starter packs are published yet; the first ones are still being reviewed. '
      + '<label class="start-preview"><input type="checkbox"' + (s.preview ? ' checked' : '') + ' onchange="startTogglePreview(this.checked)"> Preview draft packs</label></div>';
  } else {
    html += '<label class="start-preview small"><input type="checkbox"' + (s.preview ? ' checked' : '') + ' onchange="startTogglePreview(this.checked)"> Include draft packs</label>';
  }

  if (s.sourcetypes.length && summary.indexLoaded) {
    html += '<p class="start-summary">Your ' + s.sourcetypes.length + ' sourcetype(s) feed <strong>' + summary.ucCount
      + '</strong> use cases in the catalogue. Below is a short ordered list to start with.</p>';
  }

  if (plan.steps.length) {
    html += '<h3 class="start-q">Turn these on, in this order</h3><ol class="start-plan">';
    plan.steps.forEach(function(st) {
      var pack = _spPackById(st.packId);
      html += '<li class="start-step' + (st.ready ? '' : ' not-ready') + '">'
        + '<button type="button" class="start-step-title" onclick="startOpenUC(\'' + esc(st.ucId) + '\')">'
        + '<span class="start-step-id">' + esc(st.ucId) + '</span> ' + esc(st.title) + '</button>'
        + '<span class="start-step-meta">' + esc(pack ? pack.title : st.packId)
        + (st.difficulty ? ' · ' + esc(st.difficulty) : '')
        + (st.difficultyWarning ? ' <span class="start-badge warn" title="Harder than your stated experience. Still worth doing; take it slowly.">above your level</span>' : '')
        + (st.ready ? '' : ' <span class="start-badge need">needs data</span>') + '</span></li>';
    });
    html += '</ol>';
  } else {
    html += '<div class="start-empty">' + (plan.emptyReason === 'no-input'
      ? 'Pick your equipment or paste your sourcetypes on the previous step to get a plan.'
      : 'None of the ' + esc(s.goal) + ' packs match your data yet. Start by onboarding one of the data sources below; the Splunkbase add-on listed on each pack does most of the work.') + '</div>';
  }

  if (plan.nextSources.length) {
    html += '<h3 class="start-q">Data worth onboarding next</h3><ul class="start-next">';
    plan.nextSources.forEach(function(n) {
      html += '<li><code>' + esc(n.kind === 'index' ? 'index=' + n.name : n.name) + '</code> unlocks ' + n.unlocks + ' more step(s) in '
        + n.packs.map(function(pid) { var p = _spPackById(pid); return esc(p ? p.title : pid); }).join(', ') + '</li>';
    });
    html += '</ul>';
  }

  if (plan.packs.length) {
    html += '<h3 class="start-q">Packs behind this plan</h3><div class="start-packs">';
    var suggested = {};
    plan.packs.forEach(function(pp) {
      var p = _spPackById(pp.id) || {};
      var rd = p.requiredData || {};
      html += '<div class="start-pack"><div class="start-pack-hd"><strong>' + esc(pp.title) + '</strong> ' + _startUnlockLabel(pp)
        + (pp.status !== 'published' ? ' <span class="start-badge draft">Draft</span>' : '')
        + (pp.equipmentMatch ? ' <span class="start-badge eq">Matches your equipment</span>' : '') + '</div>'
        + '<p class="start-pack-desc">' + esc(p.description || '') + '</p>';
      if ((rd.splunkbaseApps || []).length) {
        html += '<p class="start-pack-apps">Install: ' + rd.splunkbaseApps.map(function(a) {
          return '<a href="https://splunkbase.splunk.com/app/' + encodeURIComponent(a.id) + '" target="_blank" rel="noopener noreferrer">' + esc(a.displayName) + '</a>';
        }).join(', ') + '</p>';
      }
      if (rd.notes) html += '<p class="start-pack-notes">' + esc(rd.notes) + '</p>';
      if (s.cloud && (p.equipment || []).indexOf('splunk') !== -1) {
        html += '<p class="start-pack-notes">On Splunk Cloud, use the Cloud Monitoring Console for indexer-side health; your role may not see every _internal metric.</p>';
      }
      if (pp.missingData.length && pp.unlock !== 'none') {
        html += '<p class="start-pack-notes">Missing for the remaining steps: ' + pp.missingData.map(function(k) { return '<code>' + esc(k.replace(/^index:/, 'index=')) + '</code>'; }).join(' ') + '</p>';
      }
      html += '</div>';
      (p.nextPacks || []).forEach(function(nid) { suggested[nid] = true; });
    });
    html += '</div>';
    var shown = {};
    plan.packs.forEach(function(pp) { shown[pp.id] = true; });
    var nextList = Object.keys(suggested).sort().filter(function(nid) {
      var np = _spPackById(nid);
      if (!np || shown[nid] || (np.status !== 'published' && !s.preview)) return false;
      return spEquipmentMatch(np.equipment, s.equipment);
    });
    if (nextList.length) {
      html += '<p class="start-note">After that, these packs match your equipment: ' + nextList.map(function(nid) {
        var np = _spPackById(nid);
        return esc(np.title) + ' (' + esc(np.goal) + ')';
      }).join(', ') + '.</p>';
    }
  }

  if (summary.unknown.length) {
    html += '<details class="start-unknown"><summary>' + summary.unknown.length + ' sourcetype(s) not referenced by any use case</summary><p>'
      + summary.unknown.slice(0, 100).map(function(u) { return '<code>' + esc(u) + '</code>'; }).join(' ')
      + '</p><p class="start-note">Custom or renamed sourcetypes are common. If one of these is a standard source under another name, map it with a sourcetype rename in props.conf.</p></details>';
  }

  html += '<div class="start-exports"><span class="start-exports-label">Take this with you</span>'
    + '<button type="button" class="inv-btn" onclick="startExport(\'link\')">Copy link</button>'
    + '<button type="button" class="inv-btn" onclick="startExport(\'md\')">Markdown</button>'
    + '<button type="button" class="inv-btn" onclick="startExport(\'csv\')">CSV</button>'
    + '<button type="button" class="inv-btn primary" onclick="startExport(\'ai\')">Copy as AI prompt</button></div>';
  return html;
}

function _startRender() {
  if (!startState) return;
  var body = document.getElementById('start-body');
  var foot = document.getElementById('start-footer');
  if (!body || !foot) return;
  var s = startState;
  var inner = s.step === 1 ? _startStepGoal() : s.step === 2 ? _startStepLevel() : s.step === 3 ? _startStepData() : _startStepPlan();
  body.innerHTML = _startProgress() + '<div class="start-step-body">' + inner + '</div>';
  var back = s.step > 1 ? '<button type="button" class="inv-btn" onclick="startGo(' + (s.step - 1) + ')">&larr; Back</button>' : '<span></span>';
  var next = '';
  if (s.step === 1) next = s.goal ? '<button type="button" class="inv-btn primary" onclick="startGo(2)">Next &rarr;</button>' : '';
  else if (s.step === 2) next = '<button type="button" class="inv-btn primary" onclick="startGo(3)">Next &rarr;</button>';
  else if (s.step === 3) next = '<button type="button" class="inv-btn primary" onclick="startAnalyzePaste()">Build my plan &rarr;</button>';
  else next = '<button type="button" class="inv-btn" onclick="closeStartWizard()">Done</button>';
  foot.innerHTML = back + next;
}
