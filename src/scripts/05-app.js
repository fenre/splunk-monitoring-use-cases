var _srcBuilt = false;
function buildSourceCatalog() {
  if (_srcBuilt) return;
  _srcBuilt = true;
  var b = document.getElementById('src-body');
  var h = '';

  function badge(s) { return '<span class="src-badge ' + s + '">' + s.charAt(0).toUpperCase() + s.slice(1) + '</span>'; }
  function link(url, label) { return '<a href="https://' + url + '" target="_blank" rel="noopener noreferrer">' + (label || url) + '</a>'; }

  h += '<div class="src-section"><div class="src-section-head">Splunk Official Documentation &amp; Portals</div>';

  h += '<div class="src-group"><div class="src-group-title">Splunk Lantern</div>';
  h += '<table class="src-table"><tr><th>Section</th><th>Status</th><th>Notes</th></tr>';
  [['lantern.splunk.com/Security_Use_Cases','Security Use Cases','used','Threat Investigation, Security Monitoring, Compliance, Threat Hunting'],
   ['lantern.splunk.com/Security_Use_Cases/Compliance','Security &mdash; Compliance','used','PCI DSS, HIPAA, GDPR, NERC CIP, MiFID II'],
   ['lantern.splunk.com/Security_Use_Cases/Threat_Hunting','Security &mdash; Threat Hunting','used','Cisco SNA + ES + RBA integration'],
   ['lantern.splunk.com/Security/UCE','Security &mdash; Use Case Explorer','used','Foundational Visibility, Security Monitoring, Advanced Threat Detection'],
   ['lantern.splunk.com/Observability_Use_Cases','Observability Use Cases','used','Optimize Performance, Troubleshoot, Monitor Business'],
   ['lantern.splunk.com/Observability/Product_Tips/Infrastructure_Monitoring','Observability &mdash; Infrastructure Monitoring','used','VMware, AWS RDS, K8s, PostgreSQL, HPA'],
   ['lantern.splunk.com/Industry_Use_Cases/Financial_Services_and_Insurance','Industry &mdash; Financial Services','used','Fraud Analytics, Behavioral Profiling, Data Compliance'],
   ['lantern.splunk.com/Industry_Use_Cases/Public_Sector','Industry &mdash; Public Sector','used','FedRAMP, CMMC, FISMA, CJIS'],
   ['lantern.splunk.com/Splunk_and_Cisco_Use_Cases','Splunk &amp; Cisco Use Cases','used','Identity Intelligence, switches/routers/WLAN, gRPC'],
   ['lantern.splunk.com/Data_Descriptors','Data Descriptors','used','Data source best practices and TA links'],
  ].forEach(function(r) {
    h += '<tr><td>' + link(r[0], r[1]) + '</td><td>' + badge(r[2]) + '</td><td>' + r[3] + '</td></tr>';
  });
  h += '</table></div>';

  h += '<div class="src-group"><div class="src-group-title">Splunk Security Content (ESCU)</div>';
  h += '<table class="src-table"><tr><th>Source</th><th>Status</th><th>Notes</th></tr>';
  [['research.splunk.com/stories','Analytic Stories','used','2,000+ detections across 300+ stories'],
   ['research.splunk.com/stories/tactics','Stories by MITRE Tactic','used','ATT&CK-mapped detections'],
   ['research.splunk.com/stories/source','Stories by Data Source','used','Mapped to TAs and sourcetypes'],
   ['github.com/splunk/security_content','GitHub: security_content','used','Raw YAML detections, contentctl tool'],
  ].forEach(function(r) {
    h += '<tr><td>' + link(r[0], r[1]) + '</td><td>' + badge(r[2]) + '</td><td>' + r[3] + '</td></tr>';
  });
  h += '</table></div>';

  h += '<div class="src-group"><div class="src-group-title">Splunk Documentation &amp; Blogs</div>';
  h += '<table class="src-table"><tr><th>Source</th><th>Status</th><th>Notes</th></tr>';
  [['docs.splunk.com/Documentation/CIM/latest','CIM Manual','used','CIM data model reference'],
   ['docs.splunk.com/Documentation/ITSI/latest','ITSI Docs','used','Service modeling, KPIs, Glass Tables'],
   ['docs.splunk.com/Documentation/ES/latest','Enterprise Security Docs','used','Notable events, correlation searches'],
   ['docs.splunk.com/Documentation/EdgeHub','Edge Hub Docs','used','MQTT, OPC-UA, Modbus via Edge Hub'],
   ['splunk.com/en_us/blog/security','Security Blog','used','ESCU updates, threat research, detection stories'],
   ['splunk.com/en_us/blog/observability','Observability Blog','used','DORA operational resilience, APM'],
   ['community.splunk.com','Splunk Community (Answers)','used','User-contributed SPL, troubleshooting'],
  ].forEach(function(r) {
    h += '<tr><td>' + link(r[0], r[1]) + '</td><td>' + badge(r[2]) + '</td><td>' + r[3] + '</td></tr>';
  });
  h += '</table></div>';
  h += '</div>';

  h += '<div class="src-section"><div class="src-section-head">Splunkbase Apps &amp; Technology Add-ons</div>';

  h += '<div class="src-group"><div class="src-group-title">Core Platform TAs</div>';
  h += '<table class="src-table"><tr><th>TA / App</th><th>Approx. UCs</th><th>Categories</th></tr>';
  [['Splunk Security Essentials (SSE) &amp; ES Content Update (ESCU)','~2,074','10.2&ndash;10.9'],
   ['Splunk Add-on for Microsoft Windows','~210','1, 2, 6, 8, 9'],
   ['Splunk Add-on for Unix and Linux','~141','1'],
   ['Splunk Add-on for Amazon Web Services (AWS)','~230','4, 6, 7, 10, 20'],
   ['Splunk Add-on for Microsoft Cloud Services','~121','4, 7, 9, 10, 11'],
   ['Splunk Add-on for Google Cloud Platform','~51','4, 7'],
   ['Splunk Add-on for VMware','~89','2, 10, 18, 19'],
   ['Splunk Add-on for ServiceNow','~33','5, 16, 20, 22, 23'],
   ['Splunk Add-on for Palo Alto Networks','~80','5, 10, 17'],
   ['Fortinet FortiGate Add-On for Splunk','~66','5, 10, 17'],
   ['Splunk Add-on for Okta Identity Cloud','~48','9, 10'],
   ['Splunk Add-on for Google Workspace','~25','10, 11'],
   ['Splunk Add-on for Cisco Identity Services (ISE)','~45','5, 10, 11, 17'],
  ].forEach(function(r) {
    h += '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td><td>' + r[2] + '</td></tr>';
  });
  h += '</table></div>';

  h += '<div class="src-group"><div class="src-group-title">Cisco TAs</div>';
  h += '<table class="src-table"><tr><th>TA / App</th><th>Splunkbase</th><th>Categories</th></tr>';
  [['Cisco Meraki Add-on for Splunk','5580','5.1, 5.2, 5.4, 5.8, 14.1, 15.3'],
   ['Cisco ThousandEyes App for Splunk','7719','5.9, 11.3'],
   ['Cisco Security Cloud','7404','5.2, 9.5, 10.1, 10.7, 17.2'],
   ['Cisco Catalyst Add-on for Splunk','7538','5.5, 15.3'],
  ].forEach(function(r) {
    h += '<tr><td>' + r[0] + '</td><td>' + link('splunkbase.splunk.com/app/' + r[1], '#' + r[1]) + '</td><td>' + r[2] + '</td></tr>';
  });
  h += '</table></div>';

  h += '<div class="src-group"><div class="src-group-title">Security Vendor TAs</div>';
  h += '<table class="src-table"><tr><th>Vendor</th><th>Approx. UCs</th><th>Categories</th></tr>';
  [['Palo Alto Networks','~84','5.2, 10.1, 10.6, 10.11, 17.2, 17.3'],
   ['Fortinet (FortiGate/FortiManager)','~66','5.2, 10.1, 10.11, 17.2, 17.3'],
   ['Check Point','~56','5.2, 10.11, 13.3, 17.3'],
   ['CrowdStrike','~484','10.2, 10.3, 10.6, 10.7, 10.11'],
   ['Carbon Black','~24','10.3, 10.7, 10.11'],
   ['Tanium','~13','10.11, 10.16'],
   ['Tenable','~17','10.6, 10.11, 22.2'],
   ['Zscaler','~35','10.5, 10.11, 17.3'],
  ].forEach(function(r) {
    h += '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td><td>' + r[2] + '</td></tr>';
  });
  h += '</table></div>';
  h += '</div>';

  h += '<div class="src-section"><div class="src-section-head">Frameworks &amp; Standards</div>';
  h += '<table class="src-table"><tr><th>Framework</th><th>Status</th><th>Usage</th></tr>';
  [['attack.mitre.org','MITRE ATT&CK Enterprise','used','Mapped in 10.2&ndash;10.7 via ESCU'],
   ['attack.mitre.org/techniques/ics','MITRE ATT&CK for ICS','used','OT Security detections in 10.14'],
   ['pcisecuritystandards.org','PCI DSS v4.0','used','10.12.7, 10.12.15'],
   ['hhs.gov/hipaa','HIPAA Security Rule','used','10.12.16&ndash;30'],
   ['csrc.nist.gov/publications/detail/sp/800-53/rev-5/final','NIST 800-53 Rev 5','used','10.12.41'],
   ['nerc.com/pa/Stand/Pages/CIPStandards.aspx','NERC CIP Standards','used','14.2.11 + planned expansion'],
   ['gdpr-info.eu','GDPR Full Text','used','22.1'],
   ['eur-lex.europa.eu','NIS2 Directive','used','22.2'],
   ['eur-lex.europa.eu','DORA Regulation','used','22.3'],
  ].forEach(function(r) {
    h += '<tr><td>' + link(r[0], r[1]) + '</td><td>' + badge(r[2]) + '</td><td>' + r[3] + '</td></tr>';
  });
  h += '</table></div>';

  h += '<div class="src-section"><div class="src-section-head">External &amp; Vendor Documentation</div>';
  h += '<table class="src-table"><tr><th>Source</th><th>Status</th><th>Notes</th></tr>';
  [   ['docs.thousandeyes.com','Cisco ThousandEyes Docs','used','OTel Data Model v2 metrics, Splunk integration'],
   ['elastic.co/guide/en/elasticsearch/reference/current/monitor-elasticsearch-cluster.html','Elasticsearch Cluster Monitoring','used','Cluster health, node stats, shard allocation, ILM, CCR'],
   ['learn.microsoft.com/en-us/azure/azure-monitor/','Azure Monitor Docs','used','Activity Log, metrics, diagnostics for 15+ Azure services'],
   ['docs.docker.com/engine/daemon/prometheus','Docker Monitoring Docs','used','Daemon metrics, health checks, events API, system df'],
   ['opcfoundation.org','OPC Foundation','used','OPC-UA in 14.5'],
   ['modbus.org','Modbus.org','used','Modbus protocol in 14.2'],
   ['docs.zeek.org','Zeek ICS Protocol Analyzers','used','Protocol-specific ICS detections'],
   ['github.com/cisagov/ICSNPP','CISA ICSNPP Parsers','used','Zeek ICS protocol parsers'],
  ].forEach(function(r) {
    h += '<tr><td>' + link(r[0], r[1]) + '</td><td>' + badge(r[2]) + '</td><td>' + r[3] + '</td></tr>';
  });
  h += '</table></div>';

  h += '<div class="src-section"><div class="src-section-head">Splunk Solutions &amp; Industry Pages</div>';
  h += '<table class="src-table"><tr><th>Page</th><th>Status</th><th>Notes</th></tr>';
  [['splunk.com/en_us/solutions/compliance.html','Compliance','used','GDPR, PCI, HIPAA, compliance automation'],
   ['splunk.com/solutions/industries/financial-services','Financial Services','used','Fraud, AML, operational resilience'],
   ['splunk.com/solutions/industries/public-sector','Public Sector','used','FedRAMP, CMMC'],
   ['splunk.com/solutions/industries/energy-and-utilities','Energy &amp; Utilities','used','OT monitoring, grid security'],
   ['splunk.com/solutions/industries/healthcare','Healthcare','used','EHR monitoring, HIPAA'],
   ['splunk.com/solutions/industries/manufacturing','Manufacturing','used','OT visibility, predictive maintenance'],
  ].forEach(function(r) {
    h += '<tr><td>' + link(r[0], r[1]) + '</td><td>' + badge(r[2]) + '</td><td>' + r[3] + '</td></tr>';
  });
  h += '</table></div>';

  b.innerHTML = h;
}

function openSourceCatalog() {
  buildSourceCatalog();
  document.getElementById('src-overlay').classList.add('open');
  document.body.classList.add('overlay-open');
}
function closeSourceCatalog() {
  document.getElementById('src-overlay').classList.remove('open');
  _maybeClearOverlayClass();
}
function openReleaseNotes() {
  document.getElementById('rn-overlay').classList.add('open');
  document.body.classList.add('overlay-open');
}
function closeReleaseNotes() {
  document.getElementById('rn-overlay').classList.remove('open');
  _maybeClearOverlayClass();
}
function _maybeClearOverlayClass() {
  if (!document.getElementById('src-overlay').classList.contains('open') && !document.getElementById('rn-overlay').classList.contains('open')
    && !document.getElementById('inv-overlay').classList.contains('open') && !document.getElementById('mitre-map-overlay').classList.contains('open')
    && !document.getElementById('help-overlay').classList.contains('open') && !panelOpen)
    document.body.classList.remove('overlay-open');
}

var HELP_BANNER_KEY = 'umc.helpBannerDismissed';
var HELP_TABS = ['web', 'api', 'ai', 'packs', 'tools'];

function renderHelpBanner() {
  try { if (localStorage.getItem(HELP_BANNER_KEY) === '1') return ''; } catch (e) {}
  return '<div class="c-help-banner" role="region" aria-label="Getting started" id="help-banner">' +
    '<div class="c-help-banner-ico" aria-hidden="true">?</div>' +
    '<div class="c-help-banner-text"><strong>New here?</strong>' +
    'Learn how to find use cases fast, pull them via the JSON API, and ground AI agents in the catalog.</div>' +
    '<button type="button" class="c-help-banner-cta" onclick="openHelpGuide()">Show me how &rarr;</button>' +
    '<button type="button" class="c-help-banner-close" onclick="dismissHelpBanner()" aria-label="Dismiss">&times;</button>' +
    '</div>';
}

function dismissHelpBanner() {
  try { localStorage.setItem(HELP_BANNER_KEY, '1'); } catch (e) {}
  var el = document.getElementById('help-banner');
  if (el && el.parentNode) el.parentNode.removeChild(el);
}

function openHelpGuide(tab) {
  var id = (tab && HELP_TABS.indexOf(tab) !== -1) ? tab : 'web';
  switchHelpTab(id);
  document.getElementById('help-overlay').classList.add('open');
  document.body.classList.add('overlay-open');
  setTimeout(function() {
    var btn = document.querySelector('#help-overlay .help-tab-btn.active');
    if (btn) btn.focus();
  }, 0);
}

function closeHelpGuide() {
  document.getElementById('help-overlay').classList.remove('open');
  _maybeClearOverlayClass();
  if ((location.hash || '').replace(/^#/, '').indexOf('help') === 0) {
    history.replaceState(null, '', '#overview');
  }
}

function switchHelpTab(id) {
  if (HELP_TABS.indexOf(id) === -1) id = 'web';
  var root = document.getElementById('help-overlay');
  if (!root) return;
  root.querySelectorAll('.help-tab-btn').forEach(function(b) {
    var active = b.getAttribute('data-tab') === id;
    b.classList.toggle('active', active);
    b.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  root.querySelectorAll('.help-tab-panel').forEach(function(p) {
    p.classList.toggle('active', p.id === 'help-panel-' + id);
  });
  var bd = root.querySelector('.c-modal-bd');
  if (bd) bd.scrollTop = 0;
}

var _invUCCounts = {};
function _invComputeUCCounts() {
  _invUCCounts = {};
  allUCs.forEach(function(e) {
    (e.uc.e || []).forEach(function(eid) { _invUCCounts[eid] = (_invUCCounts[eid] || 0) + 1; });
    (e.uc.em || []).forEach(function(mid) { _invUCCounts[mid] = (_invUCCounts[mid] || 0) + 1; });
  });
}
function _invDsaCount(id) {
  var m = window.DSA_EQUIPMENT_MAP;
  return (m && m[id]) ? m[id].filter(function(s) { return s; }).length : 0;
}
function _invBuildBody(filterText) {
  var ft = (filterText || '').toLowerCase().trim();
  if (!Object.keys(_invUCCounts).length) _invComputeUCCounts();
  var html = '';
  var totalGroups = 0;
  EQUIPMENT_GROUPS.forEach(function(grp, gi) {
    var items = [];
    grp.ids.forEach(function(eid) {
      var eq = _eqById[eid];
      if (!eq) return;
      var matchesFilter = !ft || eq.label.toLowerCase().indexOf(ft) !== -1 || eq.id.toLowerCase().indexOf(ft) !== -1;
      var modelMatches = [];
      if (eq.models) eq.models.forEach(function(m) {
        var mid = eq.id + '_' + m.id;
        if (!ft || m.label.toLowerCase().indexOf(ft) !== -1 || mid.toLowerCase().indexOf(ft) !== -1 || matchesFilter) modelMatches.push(m);
      });
      if (matchesFilter || modelMatches.length) items.push({ eq: eq, modelMatches: modelMatches.length && !matchesFilter ? modelMatches : eq.models, matchesFilter: matchesFilter });
    });
    if (!items.length) return;
    totalGroups++;
    var grpSelectedCount = 0;
    items.forEach(function(it) {
      if (_invTempSelections.has(it.eq.id)) grpSelectedCount++;
      if (it.eq.models) it.eq.models.forEach(function(m) { if (_invTempSelections.has(it.eq.id + '_' + m.id)) grpSelectedCount++; });
    });
    var grpCountBadge = grpSelectedCount > 0 ? '<span class="inv-group-count">' + grpSelectedCount + '</span>' : '';
    html += '<div class="inv-group' + (ft ? ' open' : '') + '" data-grp="' + gi + '">'
      + '<div class="inv-group-header" onclick="invToggleGroup(this)">'
      + '<span class="inv-chevron">&#9654;</span>'
      + '<span style="flex:1">' + esc(grp.name) + '</span>'
      + grpCountBadge
      + '<button type="button" class="inv-selall" onclick="event.stopPropagation();invToggleGroupAll(' + gi + ')">Select all</button>'
      + '</div>'
      + '<div class="inv-items" data-grp-items="' + gi + '">';
    items.forEach(function(it) {
      var checked = _invTempSelections.has(it.eq.id);
      var dsaCnt = _invDsaCount(it.eq.id);
      var ucCnt = _invUCCounts[it.eq.id] || 0;
      var modelCnt = it.eq.models ? it.eq.models.length : 0;
      html += '<div class="inv-card' + (checked ? ' selected' : '') + '" onclick="invCardClick(event,\'' + it.eq.id + '\')">'
        + '<div class="inv-card-cb"><input type="checkbox" data-inv-id="' + it.eq.id + '"' + (checked ? ' checked' : '') + ' onchange="invItemChg(this)" onclick="event.stopPropagation()"></div>'
        + '<div class="inv-card-info">'
        + '<div class="inv-card-name">' + esc(it.eq.label) + '</div>'
        + '<div class="inv-card-meta">';
      if (ucCnt > 0) html += '<span class="inv-card-tag ucs">' + ucCnt + ' use case' + (ucCnt !== 1 ? 's' : '') + '</span>';
      if (dsaCnt > 0) html += '<span class="inv-card-tag dsa">' + dsaCnt + ' data source' + (dsaCnt !== 1 ? 's' : '') + '</span>';
      if (modelCnt > 0) html += '<span class="inv-card-tag models">' + modelCnt + ' model' + (modelCnt !== 1 ? 's' : '') + '</span>';
      html += '</div></div></div>';
      if (it.eq.models && it.modelMatches && it.modelMatches.length) {
        html += '<div class="inv-models-drawer">';
        it.modelMatches.forEach(function(m) {
          var mid = it.eq.id + '_' + m.id;
          var mc = _invTempSelections.has(mid);
          var mDsa = _invDsaCount(mid);
          var mUc = _invUCCounts[mid] || 0;
          html += '<div class="inv-model-row"><label>'
            + '<input type="checkbox" data-inv-id="' + mid + '"' + (mc ? ' checked' : '') + ' onchange="invItemChg(this)">'
            + esc(m.label)
            + '</label>';
          if (mUc > 0) html += '<span class="inv-card-tag ucs">' + mUc + ' UCs</span>';
          if (mDsa > 0) html += '<span class="inv-card-tag dsa">' + mDsa + ' src</span>';
          html += '</div>';
        });
        html += '</div>';
      }
    });
    html += '</div></div>';
  });
  if (!totalGroups) {
    return '<div style="text-align:center;padding:40px 20px;color:var(--text-tertiary);">'
      + '<div style="font-size:32px;margin-bottom:12px;">🔍</div>'
      + '<div style="font-size:14px;font-weight:600;">No equipment matches &ldquo;' + esc(ft) + '&rdquo;</div>'
      + '<div style="font-size:12px;margin-top:4px;">Try a different search term</div></div>';
  }
  return html;
}

function _invUpdateFooter() {
  var n = _invTempSelections.size;
  document.getElementById('inv-footer-count').textContent = n + ' selected';
  var dsaTotal = 0;
  _invTempSelections.forEach(function(id) { dsaTotal += _invDsaCount(id); });
  var dsaEl = document.getElementById('inv-footer-dsa');
  if (dsaEl) dsaEl.textContent = dsaTotal > 0 ? '(' + dsaTotal + ' data source' + (dsaTotal !== 1 ? 's' : '') + ' for sizing)' : '';
  var btn = document.getElementById('inv-estimate-btn');
  if (btn) btn.disabled = dsaTotal === 0;
}
function openInventoryModal() {
  _invTempSelections = new Set(inventorySelections);
  document.getElementById('inv-body').innerHTML = _invBuildBody('');
  document.getElementById('inv-search').value = '';
  _invUpdateFooter();
  document.getElementById('inv-overlay').classList.add('open');
  document.body.classList.add('overlay-open');
}
function closeInventoryModal() {
  document.getElementById('inv-overlay').classList.remove('open');
  _maybeClearOverlayClass();
}
function invToggleGroup(headerEl) {
  var group = headerEl.closest('.inv-group');
  if (group) group.classList.toggle('open');
}
function invToggleGroupAll(gi) {
  var grp = EQUIPMENT_GROUPS[gi];
  if (!grp) return;
  var allIds = [];
  grp.ids.forEach(function(eid) {
    var eq = _eqById[eid];
    if (!eq) return;
    allIds.push(eq.id);
    if (eq.models) eq.models.forEach(function(m) { allIds.push(eq.id + '_' + m.id); });
  });
  var allOn = allIds.every(function(id) { return _invTempSelections.has(id); });
  allIds.forEach(function(id) { if (allOn) _invTempSelections.delete(id); else _invTempSelections.add(id); });
  document.getElementById('inv-body').innerHTML = _invBuildBody(document.getElementById('inv-search').value.trim());
  _invUpdateFooter();
}
function invCardClick(ev, id) {
  if (ev.target.tagName === 'INPUT' || ev.target.tagName === 'BUTTON') return;
  var cb = ev.currentTarget.querySelector('input[type="checkbox"]');
  if (cb) { cb.checked = !cb.checked; invItemChg(cb); }
}
function invItemChg(cb) {
  var id = cb.getAttribute('data-inv-id');
  if (cb.checked) _invTempSelections.add(id); else _invTempSelections.delete(id);
  var card = cb.closest('.inv-card');
  if (card) { if (cb.checked) card.classList.add('selected'); else card.classList.remove('selected'); }
  _invUpdateFooter();
}
function applyInventory() {
  inventorySelections = Array.from(_invTempSelections);
  _saveInventory();
  _updateInventoryBadge();
  selectedEquipmentId = '';
  var es = document.getElementById('equipment-select');
  var ms = document.getElementById('equipment-model-select');
  var mw = document.getElementById('equipment-model-wrap');
  if (es) es.value = '';
  if (ms) ms.innerHTML = '<option value="">All models</option>';
  if (mw) mw.style.display = 'none';
  closeInventoryModal();
  _updateSizingTray();
  if (inventorySelections.length) ovGroupFilter = 'alluc';
  reRender();
}
function clearInventory() {
  _invTempSelections.clear();
  document.getElementById('inv-body').innerHTML = _invBuildBody(document.getElementById('inv-search').value.trim());
  _invUpdateFooter();
}
function exportInventory() {
  var data = { equipment: Array.from(_invTempSelections), updated: new Date().toISOString().slice(0, 10) };
  var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = 'splunk-inventory-' + data.updated + '.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
function importInventory() { document.getElementById('inv-file-input').click(); }

function exportFiltered(fmt) {
  var list = currentDisplayedList || getFilteredUCs();
  if (!list.length) { showToast('No use cases match the current filters.'); return; }
  var date = new Date().toISOString().slice(0, 10);
  if (fmt === 'json') {
    var rows = list.map(function(e) {
      return {
        id: e.uc.i, title: e.uc.n, category: e.cat.n, subcategory: e.sc.n,
        criticality: e.uc.c, difficulty: e.uc.f,
        monitoring_type: Array.isArray(e.uc.mtype) ? e.uc.mtype.join(', ') : '',
        app_ta: e.uc.t, value: e.uc.v
      };
    });
    var blob = new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' });
    _downloadBlob(blob, 'splunk-use-cases-' + date + '.json');
  } else {
    var header = ['ID','Title','Category','Subcategory','Criticality','Difficulty','Monitoring Type','App/TA','Value'];
    var lines = [header.join(',')];
    list.forEach(function(e) {
      var row = [
        e.uc.i, _csvQ(e.uc.n), _csvQ(e.cat.n), _csvQ(e.sc.n),
        e.uc.c, e.uc.f,
        _csvQ(Array.isArray(e.uc.mtype) ? e.uc.mtype.join('; ') : ''),
        _csvQ(e.uc.t), _csvQ(e.uc.v)
      ];
      lines.push(row.join(','));
    });
    var blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    _downloadBlob(blob, 'splunk-use-cases-' + date + '.csv');
  }
}
function _csvQ(s) {
  if (!s) return '""';
  return '"' + String(s).replace(/"/g, '""') + '"';
}
function showToast(msg) {
  var el = document.getElementById('toast');
  if (!el) { el = document.createElement('div'); el.id = 'toast'; el.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--text-primary,#1a1a1a);color:#fff;padding:10px 20px;border-radius:8px;font-size:13px;z-index:9999;opacity:0;transition:opacity .3s;pointer-events:none;'; document.body.appendChild(el); }
  el.textContent = msg; el.style.opacity = '1';
  clearTimeout(el._t); el._t = setTimeout(function() { el.style.opacity = '0'; }, 3000);
}
function _downloadBlob(blob, name) {
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function _dataSizingURL(query) {
  var base = window.__SITE_BASE_PATH || '';
  var path = base + '/tools/data-sizing/index.html';
  return query ? path + '?' + query : path;
}

function launchDSAFromInventory() {
  var dsaSet = new Set();
  var eqMap = window.DSA_EQUIPMENT_MAP || {};
  _invTempSelections.forEach(function(eqId) {
    var sources = eqMap[eqId];
    if (sources) sources.forEach(function(s) { if (s) dsaSet.add(s); });
  });
  if (dsaSet.size === 0) return;
  var params = ['sources=' + Array.from(dsaSet).join(',')];
  var eqIds = Array.from(_invTempSelections);
  if (eqIds.length) params.push('equipment=' + eqIds.join(','));
  window.open(_dataSizingURL(params.join('&')), '_blank');
}

function updateHash(replace) {
  var hash = '#overview';
  if (document.getElementById('panel-backdrop').classList.contains('open')) return;
  if (currentSearch) hash = '#search=' + encodeURIComponent(currentSearch);
  else if (currentCat != null) {
    hash = '#cat-' + currentCat;
    if (currentSubcat) hash += '/' + currentSubcat;
  } else if (ovGroupFilter !== 'all') hash = '#' + ovGroupFilter;
  if (replace) history.replaceState(null, '', hash);
  else history.pushState(null, '', hash);
}

function restoreFromHash() {
  var h = (location.hash || '').replace(/^#/, '');
  var hm = h.match(/^help(?:=([a-z]+))?$/);
  if (hm) {
    currentCat = null; currentSubcat = null; currentSearch = ''; ovGroupFilter = 'all'; ovHeroGroupFilter = null;
    document.getElementById('search-input').value = '';
    reRender();
    openHelpGuide(hm[1] || 'web');
    return;
  }
  if (!h || h === 'overview') {
    currentCat = null; currentSubcat = null; currentSearch = ''; ovGroupFilter = 'all'; ovHeroGroupFilter = null;
    document.getElementById('search-input').value = '';
    reRender();
    return;
  }
  var sm = h.match(/^search=(.+)/);
  if (sm) {
    currentSearch = decodeURIComponent(sm[1]);
    currentCat = null;
    document.getElementById('search-input').value = currentSearch;
    reRender();
    return;
  }
  if (['alluc','subcats','quickwins','recent'].indexOf(h) !== -1) {
    currentCat = null; currentSearch = ''; ovGroupFilter = h;
    document.getElementById('search-input').value = '';
    reRender();
    return;
  }
  var cm = h.match(/^cat-(\d+)(?:\/(.+))?$/);
  if (cm) {
    var catId = parseInt(cm[1], 10);
    if (cm[2]) {
      currentCat = catId;
      currentSubcat = cm[2];
      catShowAllUCs = true;
      currentSearch = '';
      document.getElementById('search-input').value = '';
      reRender();
      setTimeout(function() { scrollToSubcat(cm[2]); }, 80);
    } else {
      selectCat(catId, true);
    }
    return;
  }
  var um = h.match(/^uc-([\d.]+)/);
  if (um) {
    openUCById(um[1]);
    buildSidebar();
  }
}

function goHome() {
  currentCat = null; currentSubcat = null; catShowAllUCs = false; currentSearch = '';
  ovHeroGroupFilter = null; ovGroupFilter = 'all';
  document.getElementById('search-input').value = '';
  currentFilter = 'all'; currentDiffFilter = 'all'; currentIndustryFilter = 'all'; currentMtypeFilter = 'all';
  currentPillarFilter = 'all'; currentRegulationFilter = 'all'; currentEscuFilter = 'all'; currentDtypeFilter = 'all';
  currentPremiumFilter = 'all'; currentCimFilter = 'all'; currentSappFilter = 'all'; currentMitreFilter = '';
  currentStatusFilter = 'all'; currentFreshFilter = 'all';
  currentMitreTacticFilter = ''; currentDsGroup = ''; currentDatasourceFilter = ''; currentTrendFilter = false;
  selectedEquipmentId = '';
  var es = document.getElementById('equipment-select');
  var ms = document.getElementById('equipment-model-select');
  var mw = document.getElementById('equipment-model-wrap');
  if (es) es.value = '';
  if (ms) ms.innerHTML = '<option value="">All models</option>';
  if (mw) mw.style.display = 'none';
  inventorySelections = [];
  try { localStorage.removeItem(INVENTORY_STORAGE_KEY); } catch (e) {}
  _updateInventoryBadge();
  advFiltersOpen = false;
  reRender();
  updateHash(false);
}

function selectCat(id, skipHash) {
  sidebarManualToggle = false;
  currentCat = id;
  currentSubcat = null;
  catShowAllUCs = false;
  currentSearch = '';
  document.getElementById('search-input').value = '';
  reRender();
  if (!skipHash) updateHash(false);
  closeMobileSidebar();
}

function setNonTechnicalView(on) {
  nonTechnicalView = on;
  try { localStorage.setItem('cisco-ui-nontech', on ? '1' : '0'); } catch (e) {}
  document.body.classList.toggle('non-technical-view', on);
  var bT = document.getElementById('view-tech');
  var bN = document.getElementById('view-nontech');
  if (bT) { bT.classList.toggle('active', !on); bT.setAttribute('aria-pressed', String(!on)); }
  if (bN) { bN.classList.toggle('active', on); bN.setAttribute('aria-pressed', String(on)); }
  document.querySelectorAll('.technical-only').forEach(function(el) { el.style.display = on ? 'none' : ''; });
  reRender();
}

function renderNonTechnicalOverview() {
  window.scrollTo(0, 0);
  var nt = window.NON_TECHNICAL || {};
  var main = document.getElementById('main');
  var totalUCs = allUCs.length;
  var totalSubs = DATA.reduce(function(a, c) { return a + c.s.length; }, 0);
  var html = '<div class="nt-hero"><h2>Monitoring outcomes</h2><p>Plain-language view of what we watch across your environment.</p>';
  html += '<div class="nt-stats"><div><strong>' + DATA.length + '</strong><span>Areas</span></div><div><strong>' + totalSubs + '</strong><span>Focus topics</span></div><div><strong>' + totalUCs.toLocaleString() + '</strong><span>Checks</span></div></div>';
  html += '<div style="margin-top:12px"><input type="text" id="nt-search" placeholder="Search outcomes\u2026" oninput="filterNTCards(this.value)" style="width:100%;max-width:400px;padding:8px 12px;border-radius:8px;border:1px solid var(--border-subtle);font-size:14px;background:var(--bg-card);color:var(--text-primary)"></div>';
  html += '</div>';
  html += '<div class="c-cat-grid" id="nt-grid">';
  DATA.forEach(function(cat) {
    var block = nt[String(cat.i)];
    if (!block) return;
    var text = (block.outcomes || []).join(' ') + ' ' + (block.areas || []).map(function(a) {
      return a.name + ' ' + (a.description || '') + ' ' + (a.whatItIs || '') + ' ' + (a.whoItAffects || '') + ' ' + (a.splunkValue || '') + ' ' + (a.ucs || []).map(function(u) { return u.why; }).join(' ');
    }).join(' ');
    html += '<div class="c-cat-card nt-card" data-nt-text="' + esc(text.toLowerCase()) + '" onclick="selectCat(' + cat.i + ')"><h3>' + esc(cat.n) + '</h3>';
    (block.outcomes || []).forEach(function(o) { html += '<p class="nt-out">' + esc(o) + '</p>'; });
    html += '</div>';
  });
  html += '</div>';
  main.innerHTML = html;
  document.getElementById('back-btn').style.display = 'none';
}

function filterNTCards(q) {
  q = q.toLowerCase().trim();
  var cards = document.querySelectorAll('#nt-grid .nt-card');
  cards.forEach(function(c) { c.style.display = (!q || (c.getAttribute('data-nt-text') || '').indexOf(q) !== -1) ? '' : 'none'; });
}
var NTV_REPO_BASE = 'https://github.com/fenre/splunk-monitoring-use-cases/blob/main/';
function ntResolveLink(relativePath) {
  if (!relativePath) return '';
  var s = String(relativePath);
  if (/^https?:\/\//i.test(s)) return s;
  s = s.replace(/^\/+/, '');
  // Route regulatory primer paths to the dashboard-styled reader so the
  // plain-language content renders in a design-system-matching view with
  // navigation, search, dark mode, and print support instead of GitHub's
  // raw markdown view. Anchors are preserved so per-section links still work.
  var primerMatch = s.match(/^docs\/regulatory-primer\.md(#.*)?$/);
  if (primerMatch) {
    return 'regulatory-primer.html' + (primerMatch[1] || '');
  }
  return NTV_REPO_BASE + s;
}
function renderNonTechnicalCategory(catId) {
  window.scrollTo(0, 0);
  var cat = getCatById(catId);
  var block = (window.NON_TECHNICAL || {})[String(catId)];
  var main = document.getElementById('main');
  if (!cat || !block) { renderNonTechnicalOverview(); return; }
  var html = '<div class="c-section-header"><div class="c-section-title">' + esc(cat.n) + '</div></div><div class="nt-areas">';
  (block.areas || []).forEach(function(ar) {
    html += '<div class="nt-area"><h4>' + esc(ar.name) + '</h4><p>' + esc(ar.description || '') + '</p>';
    var hasMeta = ar.whatItIs || ar.whoItAffects || ar.splunkValue;
    if (hasMeta) {
      html += '<dl class="nt-area-meta">';
      if (ar.whatItIs)      html += '<div><dt>What it is</dt><dd>' + esc(ar.whatItIs) + '</dd></div>';
      if (ar.whoItAffects)  html += '<div><dt>Who it affects</dt><dd>' + esc(ar.whoItAffects) + '</dd></div>';
      if (ar.splunkValue)   html += '<div><dt>How Splunk helps</dt><dd>' + esc(ar.splunkValue) + '</dd></div>';
      html += '</dl>';
    }
    var hasLinks = ar.primer || ar.evidencePack;
    if (hasLinks) {
      html += '<div class="nt-area-links">';
      if (ar.primer)        html += '<a href="' + esc(ntResolveLink(ar.primer)) + '" title="Open this section of the regulatory primer">Regulatory primer &rarr;</a>';
      if (ar.evidencePack)  html += '<a href="' + esc(ntResolveLink(ar.evidencePack)) + '" target="_blank" rel="noopener noreferrer" title="Open the auditor evidence pack in a new tab">Evidence pack &rarr;</a>';
      html += '</div>';
    }
    html += '<ul>';
    (ar.ucs || []).forEach(function(u) {
      html += '<li><strong>' + esc(u.id) + '</strong> — ' + esc(u.why || '') + '</li>';
    });
    html += '</ul></div>';
  });
  html += '</div>';
  main.innerHTML = html;
  document.getElementById('back-btn').style.display = 'flex';
}

function reRender() {
  buildSidebar();
  if (nonTechnicalView) {
    if (currentCat == null) renderNonTechnicalOverview();
    else renderNonTechnicalCategory(currentCat);
    return;
  }
  if (currentSearch) renderSearchResults();
  else if (currentCat != null) {
    if (catShowAllUCs) renderCategory();
    else renderSubcategoryView();
  }
  else renderOverview();
}

function populateEquipmentSelect() {
  var sel = document.getElementById('equipment-select');
  if (!sel) return;
  var html = '<option value="">All equipment</option>';
  (EQUIPMENT || []).slice().sort(function(a, b) { return a.label.localeCompare(b.label); }).forEach(function(eq) {
    html += '<option value="' + esc(eq.id) + '">' + esc(eq.label) + '</option>';
  });
  sel.innerHTML = html;
}

function onEquipmentChange() {
  var val = (document.getElementById('equipment-select').value || '').trim();
  var eq = val ? _eqById[val] : null;
  var mw = document.getElementById('equipment-model-wrap');
  var ms = document.getElementById('equipment-model-select');
  if (eq && eq.models && eq.models.length) {
    mw.style.display = 'flex';
    ms.innerHTML = '<option value="">All models</option>';
    eq.models.forEach(function(m) { ms.innerHTML += '<option value="' + esc(m.id) + '">' + esc(m.label) + '</option>'; });
    selectedEquipmentId = val;
  } else {
    mw.style.display = 'none';
    ms.innerHTML = '<option value="">All models</option>';
    selectedEquipmentId = val;
  }
  if (inventorySelections.length) { inventorySelections = []; _saveInventory(); _updateInventoryBadge(); }
  reRender();
}

function onModelChange() {
  var eqVal = (document.getElementById('equipment-select').value || '').trim();
  var modelVal = (document.getElementById('equipment-model-select').value || '').trim();
  selectedEquipmentId = eqVal + (modelVal ? '_' + modelVal : '');
  if (inventorySelections.length) { inventorySelections = []; _saveInventory(); _updateInventoryBadge(); }
  reRender();
}

/* Text size: 5 steps -2..+2 */
var TEXT_KEY = 'uc-text-size-step';
var TEXT_STEPS = [-2, -1, 0, 1, 2];
function applyTextSizeStep(step) {
  var s = Math.max(-2, Math.min(2, parseInt(step, 10) || 0));
  document.documentElement.style.fontSize = (15 + s) + 'px';
  try { localStorage.setItem(TEXT_KEY, String(s)); } catch (e) {}
}
function textSizeDelta(d) {
  var cur = 0;
  try { cur = parseInt(localStorage.getItem(TEXT_KEY) || '0', 10) || 0; } catch (e2) {}
  applyTextSizeStep(cur + d);
}

function toggleColorblind() {
  var on = document.getElementById('cb-toggle').checked;
  document.documentElement.classList.toggle('cb-friendly', on);
  try { localStorage.setItem('uc-colorblind-friendly', on ? '1' : '0'); } catch (e) {}
}

function toggleTheme() {
  document.documentElement.classList.toggle('dark');
  var d = document.documentElement.classList.contains('dark');
  try { localStorage.setItem('cisco-ui-theme', d ? 'dark' : 'light'); } catch (e) {}
  document.getElementById('theme-label').textContent = d ? 'Light' : 'Dark';
  var ico = document.getElementById('theme-ico');
  if (ico) ico.textContent = d ? '☀' : '☾';
}

document.addEventListener('click', function(ev) {
  var w = document.getElementById('mitre-dd-wrap');
  if (w && !w.contains(ev.target)) {
    var dd = document.getElementById('mitre-dd');
    if (dd) { dd.classList.remove('open'); var b = dd.previousElementSibling; if (b) b.classList.remove('open'); }
  }
});

function isInputFocused() {
  var el = document.activeElement;
  return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT');
}

/* ─── UC Selection & DSA Integration ─── */
function _saveUCSelections() {
  try {
    if (selectedUCIds.size > 0) {
      localStorage.setItem(UC_SELECTION_STORAGE_KEY, JSON.stringify(Array.from(selectedUCIds)));
    } else {
      localStorage.removeItem(UC_SELECTION_STORAGE_KEY);
    }
  } catch (e) {}
}

function _restoreUCSelections() {
  try {
    var raw = localStorage.getItem(UC_SELECTION_STORAGE_KEY);
    if (raw) {
      var arr = JSON.parse(raw);
      if (Array.isArray(arr)) selectedUCIds = new Set(arr);
    }
  } catch (e) {}
}

function toggleUCSelection(ucId) {
  if (selectedUCIds.has(ucId)) {
    selectedUCIds.delete(ucId);
  } else {
    selectedUCIds.add(ucId);
  }
  _saveUCSelections();
  _updateSizingTray();
  var cb = document.querySelector('.uc-card input[onchange*="' + ucId + '"]');
  if (cb) cb.checked = selectedUCIds.has(ucId);
}

function clearUCSelections() {
  selectedUCIds.clear();
  _saveUCSelections();
  inventorySelections = [];
  _saveInventory();
  _updateInventoryBadge();
  selectedEquipmentId = '';
  var es = document.getElementById('equipment-select');
  var ms = document.getElementById('equipment-model-select');
  var mw = document.getElementById('equipment-model-wrap');
  if (es) es.value = '';
  if (ms) ms.innerHTML = '<option value="">All models</option>';
  if (mw) mw.style.display = 'none';
  _updateSizingTray();
  document.querySelectorAll('.uc-select-cb input[type="checkbox"], .uc-tbl-cb input[type="checkbox"]').forEach(function(cb) { cb.checked = false; });
  reRender();
}

function _updateSizingTray() {
  var tray = document.getElementById('uc-sizing-tray');
  if (!tray) return;
  var count = selectedUCIds.size;
  var invCount = inventorySelections.length;
  var hasSelection = count > 0 || invCount > 0;
  tray.classList.toggle('has-selection', hasSelection);
  var countEl = tray.querySelector('.uc-sizing-tray-count');
  var estimateBtn = tray.querySelector('.uc-sizing-tray-btn.primary');
  var clearBtn = tray.querySelector('.uc-sizing-tray-btn.ghost');
  if (countEl) {
    if (hasSelection) {
      var parts = [];
      if (count > 0) parts.push(count + ' use case' + (count !== 1 ? 's' : ''));
      if (invCount > 0) parts.push(invCount + ' equipment');
      var dsaSources = buildDSASources();
      var hasDsaSources = dsaSources.size > 0;
      var ucsMapped = 0, ucsUnmapped = 0;
      var ucMap = window.DSA_UC_MAP || {};
      selectedUCIds.forEach(function(ucId) {
        if (ucMap[ucId] && ucMap[ucId].length) ucsMapped++; else ucsUnmapped++;
      });
      var summary = parts.join(' + ') + ' selected';
      if (hasDsaSources) {
        summary += ' \u2014 ' + dsaSources.size + ' data source' + (dsaSources.size !== 1 ? 's' : '') + ' for sizing';
      }
      countEl.innerHTML = summary;
      if (!hasDsaSources && count > 0 && invCount === 0) {
        countEl.innerHTML += '<br><span style="font-size:11px;color:var(--text-tertiary);font-weight:400">'
          + 'These use cases don\u2019t have data sources mapped yet. Add equipment via '
          + '<a href="#" onclick="event.preventDefault();openInventoryModal()" style="color:var(--cisco-blue);text-decoration:underline">My Equipment</a>'
          + ' to include data sources, or open the <a href="' + _dataSizingURL('') + '" target="_blank" style="color:var(--cisco-blue);text-decoration:underline">Data Sizing Tool</a>'
          + ' to select industrial data sources directly.</span>';
      } else if (ucsUnmapped > 0 && hasDsaSources) {
        countEl.innerHTML += '<br><span style="font-size:11px;color:var(--text-tertiary);font-weight:400">'
          + ucsUnmapped + ' of ' + count + ' selected use case' + (count !== 1 ? 's' : '') + ' don\u2019t have data sources mapped. '
          + 'Their data volume can be estimated by adding relevant equipment in '
          + '<a href="#" onclick="event.preventDefault();openInventoryModal()" style="color:var(--cisco-blue);text-decoration:underline">My Equipment</a>'
          + '.</span>';
      }
    } else {
      countEl.textContent = 'Select use cases or inventory to estimate data sizing';
    }
  }
  if (estimateBtn) {
    var dsaCheck = buildDSASources();
    estimateBtn.disabled = dsaCheck.size === 0;
    estimateBtn.title = dsaCheck.size === 0
      ? 'No data sources mapped to your selections. Add equipment via My Equipment to enable sizing.'
      : 'Open Data Sizing Assessment with ' + dsaCheck.size + ' data sources';
  }
  if (clearBtn) clearBtn.style.display = hasSelection ? '' : 'none';
}

function buildDSASources() {
  var dsaSet = new Set();
  var eqMap = window.DSA_EQUIPMENT_MAP || {};
  var ucMap = window.DSA_UC_MAP || {};
  inventorySelections.forEach(function(eqId) {
    var sources = eqMap[eqId];
    if (sources) sources.forEach(function(s) { dsaSet.add(s); });
  });
  selectedUCIds.forEach(function(ucId) {
    var sources = ucMap[ucId];
    if (sources) sources.forEach(function(s) { dsaSet.add(s); });
  });
  return dsaSet;
}

function launchDSAEstimate() {
  var dsaSources = buildDSASources();
  var params = [];
  if (dsaSources.size > 0) {
    params.push('sources=' + Array.from(dsaSources).join(','));
  }
  if (inventorySelections.length > 0) {
    params.push('equipment=' + inventorySelections.join(','));
  }
  if (dsaSources.size === 0) {
    var msg = 'No data sources could be mapped from your current selections.\n\n';
    if (selectedUCIds.size > 0 && inventorySelections.length === 0) {
      msg += 'The selected use cases don\u2019t have specific data sources linked. '
        + 'To get a data volume estimate:\n\n'
        + '1. Click "My Equipment" and select the equipment in your environment\n'
        + '2. Or open the Data Sizing Tool directly to browse all ' + '206+ data sources';
    } else {
      msg += 'Add equipment via "My Equipment" or select use cases that have data sources mapped.';
    }
    alert(msg);
    return;
  }
  window.open(_dataSizingURL(params.join('&')), '_blank');
}

function initApp() {
  _loadInventory();
  _updateInventoryBadge();
  _restoreUCSelections();
  populateEquipmentSelect();
  try {
    if (localStorage.getItem('cisco-ui-theme') === 'dark') {
      document.documentElement.classList.add('dark');
      document.getElementById('theme-label').textContent = 'Light';
      var ic = document.getElementById('theme-ico');
      if (ic) ic.textContent = '☀';
    }
  } catch (e) {}
  try {
    var ts = localStorage.getItem(TEXT_KEY);
    if (ts != null) applyTextSizeStep(ts);
  } catch (e2) {}
  try {
    if (localStorage.getItem('uc-colorblind-friendly') === '1') {
      document.getElementById('cb-toggle').checked = true;
      document.documentElement.classList.add('cb-friendly');
    }
  } catch (e3) {}
  try {
    if (localStorage.getItem('cisco-ui-nontech') === '1') setNonTechnicalView(true);
  } catch (e4) {}
  document.getElementById('footer-author').textContent = SITE.siteAuthor ? 'Author: ' + SITE.siteAuthor : '';
  var fl = document.getElementById('footer-feedback');
  if (fl && SITE.siteRepoUrl) fl.href = SITE.siteRepoUrl;

  var headerLogo = document.getElementById('header-logo');
  headerLogo.addEventListener('click', goHome);
  headerLogo.addEventListener('keydown', function(e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); goHome(); } });
  document.getElementById('theme-btn').addEventListener('click', toggleTheme);
  document.getElementById('hamburger').addEventListener('click', function() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebar-backdrop').classList.toggle('open');
  });
  document.getElementById('sidebar-backdrop').addEventListener('click', closeMobileSidebar);
  (function() {
    var mBtn = document.getElementById('mobile-search-btn');
    var mBar = document.getElementById('mobile-search-bar');
    var mInput = document.getElementById('mobile-search-input');
    var deskInput = document.getElementById('search-input');
    mBtn.addEventListener('click', function() {
      var open = mBar.classList.toggle('open');
      if (open) mInput.focus();
    });
    var mst;
    mInput.addEventListener('input', function(ev) {
      clearTimeout(mst);
      mst = setTimeout(function() {
        currentSearch = ev.target.value.trim();
        searchShowAll = false;
        deskInput.value = currentSearch;
        if (currentSearch) { currentCat = null; }
        reRender();
        updateHash(false);
      }, 200);
    });
  })();
  document.getElementById('equipment-select').addEventListener('change', onEquipmentChange);
  document.getElementById('equipment-model-select').addEventListener('change', onModelChange);
  document.getElementById('inv-search').addEventListener('input', function(ev) {
    document.getElementById('inv-body').innerHTML = _invBuildBody(ev.target.value);
  });
  document.getElementById('inv-file-input').addEventListener('change', function(ev) {
    var f = ev.target.files[0];
    if (!f) return;
    var r = new FileReader();
    r.onload = function() {
      try {
        var d = JSON.parse(r.result);
        if (d && Array.isArray(d.equipment)) {
          _invTempSelections = new Set(d.equipment);
          document.getElementById('inv-body').innerHTML = _invBuildBody('');
          document.getElementById('inv-footer-count').textContent = _invTempSelections.size + ' selected';
        }
      } catch (e) {}
    };
    r.readAsText(f);
    ev.target.value = '';
  });

  var siEl = document.getElementById('search-input');
  var st;
  siEl.addEventListener('input', function(ev) {
    clearTimeout(st);
    st = setTimeout(function() {
      currentSearch = ev.target.value.trim();
      searchShowAll = false;
      if (currentSearch) { currentCat = null; }
      reRender();
      if (currentSearch) updateHash(false);
      else updateHash(false);
    }, 250);
  });

  document.addEventListener('keydown', function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); if (!nonTechnicalView) siEl.focus(); return; }
    if (e.key === '/' && !isInputFocused() && !nonTechnicalView) { e.preventDefault(); siEl.focus(); return; }
    if (e.key === 'Escape') {
      if (document.getElementById('help-overlay').classList.contains('open')) { closeHelpGuide(); return; }
      if (document.getElementById('inv-overlay').classList.contains('open')) { closeInventoryModal(); return; }
      if (document.getElementById('src-overlay').classList.contains('open')) { closeSourceCatalog(); return; }
      if (document.getElementById('rn-overlay').classList.contains('open')) { closeReleaseNotes(); return; }
      if (document.activeElement === siEl && siEl.value) { siEl.value = ''; siEl.blur(); currentSearch = ''; selectCat(null); return; }
      if (document.getElementById('panel-backdrop').classList.contains('open')) { closePanel(); return; }
      if (document.getElementById('mitre-map-overlay').classList.contains('open')) { closeMitreMap(); return; }
      closeMobileSidebar();
      return;
    }
    if (document.getElementById('panel-backdrop').classList.contains('open')) {
      if (e.key === 'ArrowLeft') navPanel(-1);
      if (e.key === 'ArrowRight') navPanel(1);
    }
  });

  document.getElementById('panel-backdrop').addEventListener('click', function(ev) { if (ev.target === this) closePanel(); });
  document.getElementById('panel').addEventListener('click', function(ev) { ev.stopPropagation(); });

  window.addEventListener('popstate', function() { restoreFromHash(); });

  _updateSizingTray();
  restoreFromHash();
}

function closeMobileSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-backdrop').classList.remove('open');
}

// initApp depends on window.DATA / window.EQUIPMENT / window.CAT_META
// being populated, which the loader handles asynchronously in production
// (lazy mode) and synchronously in legacy mode (when data.js was loaded
// as a separate <script> tag). Wait for the catalog:ready handshake.
if (window.__catalogReady && typeof window.__catalogReady.then === 'function') {
  window.__catalogReady.then(function() {
    try { initApp(); } catch (err) { console.error('[app] initApp failed:', err); }
  });
} else {
  // Defensive fallback for direct-from-disk file:// loads where the
  // loader IIFE may not have evaluated yet (or window features differ).
  initApp();
}

