// Starter-pack planner (guided onboarding). Pure functions only: no DOM,
// no fetch, no globals beyond the ones defined here. The same algorithm is
// mirrored in mcp/src/splunk_uc_mcp/starter_plan.py; the shared fixture in
// tests/fixtures/starter-plan-parity.json must produce identical output in
// both. Change both files together.

var SP_LEVELS = { beginner: 0, intermediate: 1, advanced: 2, expert: 3 };
var SP_UNLOCK_RANK = { full: 0, partial: 1, none: 2 };
var SP_MAX_STEPS = 10;
var SP_NEXT_SOURCES = 3;

function spAliasMap(groups) {
  var out = {};
  (groups || []).forEach(function(group) {
    if (!group || !group.length) return;
    var canonical = String(group[0]).trim().toLowerCase();
    group.forEach(function(name) { out[String(name).trim().toLowerCase()] = canonical; });
  });
  return out;
}

function spNormalise(name, aliases) {
  var key = String(name == null ? '' : name).trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(aliases, key) ? aliases[key] : key;
}

function spSortedUnique(values) {
  var seen = {};
  var out = [];
  values.forEach(function(v) { if (v && !seen[v]) { seen[v] = true; out.push(v); } });
  return out.sort();
}

// Parse `| tstats count where (index=* OR index=_*) by index, sourcetype`
// output pasted from Splunk Web (tab / multi-space separated), a CSV export,
// or a plain list of sourcetypes. Returns lowercase, de-duplicated lists.
function spParsePaste(text) {
  var sourcetypes = [];
  var indexes = [];
  var lines = String(text || '').split(/\r?\n/);
  var stCol = -1;
  var idxCol = -1;
  function split(line) {
    var t = line.trim();
    if (t.indexOf('\t') !== -1) return t.split('\t');
    if (t.indexOf(',') !== -1) return t.split(',');
    return t.split(/\s+/);
  }
  function clean(cell) { return String(cell || '').trim().replace(/^"|"$/g, '').trim().toLowerCase(); }
  function isNumber(cell) { return /^[\d,.]+$/.test(clean(cell)); }
  lines.forEach(function(line) {
    if (!line.trim() || /^\s*\|/.test(line)) return;
    var cells = split(line).map(clean).filter(function(c) { return c !== ''; });
    if (!cells.length) return;
    var hdrSt = cells.indexOf('sourcetype');
    if (hdrSt !== -1) { stCol = hdrSt; idxCol = cells.indexOf('index'); return; }
    if (stCol !== -1) {
      if (cells[stCol]) sourcetypes.push(cells[stCol]);
      if (idxCol !== -1 && cells[idxCol]) indexes.push(cells[idxCol]);
      return;
    }
    if (cells.length === 3 && isNumber(cells[2])) { indexes.push(cells[0]); sourcetypes.push(cells[1]); return; }
    if (cells.length === 2 && isNumber(cells[1])) { sourcetypes.push(cells[0]); return; }
    cells.forEach(function(c) {
      if (isNumber(c)) return;
      if (c.charAt(0) === '_' && c.indexOf(':') === -1) indexes.push(c);
      else sourcetypes.push(c);
    });
  });
  return {
    sourcetypes: spSortedUnique(sourcetypes.filter(function(s) { return !/^[\d,.]+$/.test(s); })),
    indexes: spSortedUnique(indexes.filter(function(s) { return !/^[\d,.]+$/.test(s); }))
  };
}

function spEquipmentMatch(packEquipment, userEquipment) {
  return (packEquipment || []).some(function(e) {
    return userEquipment.some(function(u) { return u === e || u.indexOf(e + '_') === 0; });
  });
}

// opts: { goal, level, sourcetypes[], indexes[], equipment[], includeDrafts, maxSteps }
function spPlanRollout(index, opts) {
  opts = opts || {};
  var aliases = spAliasMap(index && index.sourcetypeAliases);
  var goal = opts.goal === 'security' ? 'security' : 'operations';
  var level = Object.prototype.hasOwnProperty.call(SP_LEVELS, opts.level) ? opts.level : 'beginner';
  var maxSteps = opts.maxSteps > 0 ? opts.maxSteps : SP_MAX_STEPS;
  var userSt = {};
  (opts.sourcetypes || []).forEach(function(s) { var n = spNormalise(s, aliases); if (n) userSt[n] = true; });
  var userIdx = {};
  (opts.indexes || []).forEach(function(s) { var n = String(s).trim().toLowerCase(); if (n) userIdx[n] = true; });
  var userEq = spSortedUnique((opts.equipment || []).map(function(e) { return String(e).trim().toLowerCase(); }));
  var hasData = Object.keys(userSt).length > 0 || Object.keys(userIdx).length > 0;

  var candidates = ((index && index.packs) || []).filter(function(p) {
    return p.goal === goal && (p.status === 'published' || opts.includeDrafts === true);
  });

  function stepKeys(step) {
    var keys = (step.sourcetypes || []).map(function(s) { return spNormalise(s, aliases); });
    (step.indexes || []).forEach(function(i) { keys.push('index:' + String(i).toLowerCase()); });
    return keys;
  }
  function stepReady(step) {
    return stepKeys(step).some(function(k) {
      return k.indexOf('index:') === 0 ? userIdx[k.slice(6)] === true : userSt[k] === true;
    });
  }

  var evaluated = candidates.map(function(p) {
    var steps = (p.steps || []).slice().sort(function(a, b) { return a.order - b.order; });
    var ready = steps.map(stepReady);
    var readyCount = ready.filter(Boolean).length;
    var unlock = readyCount === 0 ? 'none' : (readyCount === steps.length ? 'full' : 'partial');
    var missing = [];
    steps.forEach(function(s, i) { if (!ready[i]) missing = missing.concat(stepKeys(s)); });
    return {
      pack: p, steps: steps, ready: ready, readyCount: readyCount, unlock: unlock,
      equipmentMatch: spEquipmentMatch(p.equipment, userEq),
      missingData: spSortedUnique(missing)
    };
  });

  var included = evaluated.filter(function(e) { return e.readyCount > 0 || e.equipmentMatch; });
  included.sort(function(a, b) {
    var ka = [a.readyCount > 0 ? 0 : 1, a.equipmentMatch ? 0 : 1, SP_UNLOCK_RANK[a.unlock], -a.readyCount];
    var kb = [b.readyCount > 0 ? 0 : 1, b.equipmentMatch ? 0 : 1, SP_UNLOCK_RANK[b.unlock], -b.readyCount];
    for (var i = 0; i < ka.length; i++) { if (ka[i] !== kb[i]) return ka[i] - kb[i]; }
    return a.pack.id < b.pack.id ? -1 : (a.pack.id > b.pack.id ? 1 : 0);
  });

  var planSteps = [];
  var seen = {};
  included.forEach(function(e) {
    var noneReady = e.readyCount === 0;
    e.steps.forEach(function(s, i) {
      if (planSteps.length >= maxSteps || seen[s.ucId]) return;
      if (!e.ready[i] && !noneReady) return;
      seen[s.ucId] = true;
      var diff = String(s.difficulty || '');
      planSteps.push({
        position: planSteps.length + 1,
        ucId: s.ucId,
        title: s.title || '',
        packId: e.pack.id,
        order: s.order,
        criticality: s.criticality || '',
        difficulty: diff,
        wave: s.wave || '',
        ready: e.ready[i],
        difficultyWarning: Object.prototype.hasOwnProperty.call(SP_LEVELS, diff) && SP_LEVELS[diff] > SP_LEVELS[level]
      });
    });
  });

  var unsatisfied = {};
  var ucPacks = {};
  evaluated.forEach(function(e) {
    e.steps.forEach(function(s, i) {
      if (e.ready[i]) return;
      if (!unsatisfied[s.ucId]) unsatisfied[s.ucId] = stepKeys(s);
      (ucPacks[s.ucId] = ucPacks[s.ucId] || {})[e.pack.id] = true;
    });
  });
  var nextSources = [];
  for (var round = 0; round < SP_NEXT_SOURCES; round++) {
    var gain = {};
    Object.keys(unsatisfied).forEach(function(uc) {
      spSortedUnique(unsatisfied[uc]).forEach(function(k) { (gain[k] = gain[k] || []).push(uc); });
    });
    var best = null;
    Object.keys(gain).sort().forEach(function(k) {
      if (best === null || gain[k].length > gain[best].length) best = k;
    });
    if (best === null) break;
    var packs = {};
    gain[best].forEach(function(uc) {
      Object.keys(ucPacks[uc]).forEach(function(pid) { packs[pid] = true; });
      delete unsatisfied[uc];
    });
    var isIndex = best.indexOf('index:') === 0;
    nextSources.push({
      kind: isIndex ? 'index' : 'sourcetype',
      name: isIndex ? best.slice(6) : best,
      unlocks: gain[best].length,
      packs: Object.keys(packs).sort()
    });
  }

  var emptyReason = null;
  if (!planSteps.length) emptyReason = (!hasData && !userEq.length) ? 'no-input' : 'no-match';

  return {
    goal: goal,
    level: level,
    packs: included.map(function(e) {
      return {
        id: e.pack.id,
        title: e.pack.title || '',
        status: e.pack.status,
        unlock: e.unlock,
        readySteps: e.readyCount,
        totalSteps: e.steps.length,
        equipmentMatch: e.equipmentMatch,
        missingData: e.missingData
      };
    }),
    steps: planSteps,
    nextSources: nextSources,
    emptyReason: emptyReason
  };
}
