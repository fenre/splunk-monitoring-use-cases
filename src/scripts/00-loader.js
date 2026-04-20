/* Cisco UI catalog — chunk 0: lazy-bootstrap loader.
 *
 * Runs FIRST in the concatenated bundle. Two modes:
 *
 *   1) Legacy mode — `data.js` was loaded as a separate <script> tag, so
 *      window.DATA, window.EQUIPMENT, window.CAT_META, window.CAT_GROUPS,
 *      window.FILTER_FACETS, window.RECENTLY_ADDED already exist.
 *      The loader resolves immediately, calls __bootstrapCatalogState(),
 *      and dispatches the "catalog:ready" event synchronously.
 *
 *   2) Lazy mode (production) — data.js is NOT loaded. window.DATA is
 *      empty. The loader fetches /api/catalog-index.json (~5 MB JSON,
 *      ~750 KB gzipped), reconstructs the legacy globals from the
 *      lightweight UC stubs, then runs the bootstrap.
 *
 * Heavy per-UC fields (full SPL, narrative, references, screenshots)
 * are NOT in the index. The detail panel lazy-fetches them from
 * /api/cat-{cat}.json on first open via __ensureFullUC().
 *
 * Public surface:
 *   window.__catalogReady   — Promise<void>; resolves when DATA + globals
 *                             are populated and __bootstrapCatalogState()
 *                             has run. initApp() must `await` this.
 *   window.__catalogIndex   — the parsed catalog-index.json (lazy mode only).
 *   window.__ensureFullUC(uc_id) — returns Promise<void> that resolves when
 *                             the UC's heavy fields are merged into DATA.
 *                             Cheap if already loaded.
 *   window.dispatchEvent(new Event("catalog:ready"))  — fired exactly once.
 */

(function() {
  if (typeof window === "undefined") return;

  // Root-absolute so the SPA works from any depth (e.g. /browse/, /embed/...).
  // Override via window.__CATALOG_API_BASE if hosting under a non-root prefix.
  var API_BASE = (typeof window.__CATALOG_API_BASE === "string" && window.__CATALOG_API_BASE)
    ? window.__CATALOG_API_BASE.replace(/\/+$/, "")
    : "/api";

  var CATALOG_INDEX_URL = API_BASE + "/catalog-index.json";
  var CATEGORY_URL = function(catId) { return API_BASE + "/cat-" + catId + ".json"; };

  var legacyMode =
    Array.isArray(window.DATA) &&
    window.DATA.length > 0 &&
    window.DATA[0] &&
    Array.isArray(window.DATA[0].s);

  var dispatchedReady = false;
  var fullCatPromises = {};
  var fullUCPromises = {};

  window.__catalogReady = new Promise(function(resolve, reject) {
    if (legacyMode) {
      // Defer to a microtask so __bootstrapCatalogState (defined later in
      // the bundle) is available when we call it.
      Promise.resolve().then(function() {
        try {
          if (typeof __bootstrapCatalogState === "function") {
            __bootstrapCatalogState();
          }
          _dispatchReady();
          resolve();
        } catch (err) {
          console.error("[loader] legacy bootstrap failed:", err);
          reject(err);
        }
      });
      return;
    }

    fetch(CATALOG_INDEX_URL, { credentials: "same-origin" })
      .then(function(res) {
        if (!res.ok) {
          throw new Error("catalog-index HTTP " + res.status);
        }
        return res.json();
      })
      .then(function(idx) {
        window.__catalogIndex = idx;
        _populateGlobalsFromIndex(idx);
        if (typeof __bootstrapCatalogState === "function") {
          __bootstrapCatalogState();
        }
        _dispatchReady();
        resolve();
      })
      .catch(function(err) {
        console.error("[loader] catalog-index fetch failed:", err);
        // Surface a minimal empty state so the SPA still renders shell UI.
        window.DATA = window.DATA || [];
        if (typeof __bootstrapCatalogState === "function") {
          try { __bootstrapCatalogState(); } catch (e) {}
        }
        _dispatchReady();
        resolve();
      });
  });

  function _dispatchReady() {
    if (dispatchedReady) return;
    dispatchedReady = true;
    try {
      window.dispatchEvent(new Event("catalog:ready"));
    } catch (e) {
      // IE-style fallback (we don't ship to IE but be polite).
      var ev = document.createEvent("Event");
      ev.initEvent("catalog:ready", true, true);
      window.dispatchEvent(ev);
    }
  }

  function _populateGlobalsFromIndex(idx) {
    if (!idx || typeof idx !== "object") return;
    if (idx.site) window.SITE_CUSTOM = idx.site;
    if (Array.isArray(idx.equipment)) window.EQUIPMENT = idx.equipment;
    if (idx.catGroups && typeof idx.catGroups === "object") window.CAT_GROUPS = idx.catGroups;
    if (idx.catMeta && typeof idx.catMeta === "object") window.CAT_META = idx.catMeta;
    if (idx.filterFacets && typeof idx.filterFacets === "object") window.FILTER_FACETS = idx.filterFacets;
    if (Array.isArray(idx.recentlyAdded)) {
      try {
        window.RECENTLY_ADDED = new Set(idx.recentlyAdded);
      } catch (e) {
        window.RECENTLY_ADDED = idx.recentlyAdded;
      }
    }
    if (idx.regulations) window.REGULATIONS = idx.regulations;

    var cats = (idx.categories || []).map(function(c) {
      return { i: c.i, n: c.n, s: (c.subs || []).map(function(s) {
        return { i: s.i, n: s.n, u: [] };
      }) };
    });
    var catById = {};
    var subKey = function(cat, subId) { return cat + "|" + subId; };
    cats.forEach(function(c) { catById[c.i] = c; });

    var subIndex = {};
    cats.forEach(function(c) {
      c.s.forEach(function(s) {
        subIndex[subKey(c.i, s.i)] = s;
      });
    });

    (idx.ucs || []).forEach(function(stub) {
      var sub = subIndex[subKey(stub.cat, stub.sub)];
      if (!sub) return;
      // The stub *is* the UC for browse-time purposes; per-UC heavy fields
      // are merged in lazily by __ensureFullUC().
      sub.u.push(stub);
    });

    window.DATA = cats;
  }

  // --------------------------------------------------------------------
  // Detail-panel lazy hydration
  // --------------------------------------------------------------------

  /** Fetch /api/cat-{catId}.json once and merge heavy fields into the
   *  matching UC stubs in window.DATA. Returns a Promise<void>. */
  window.__ensureFullCategory = function(catId) {
    if (legacyMode) return Promise.resolve();
    var key = String(catId);
    if (fullCatPromises[key]) return fullCatPromises[key];

    fullCatPromises[key] = fetch(CATEGORY_URL(catId), { credentials: "same-origin" })
      .then(function(res) {
        if (!res.ok) throw new Error("cat-" + catId + " HTTP " + res.status);
        return res.json();
      })
      .then(function(catFull) {
        _mergeCategoryFull(catId, catFull);
      })
      .catch(function(err) {
        console.error("[loader] cat-" + catId + " fetch failed:", err);
        // Allow retry on next call.
        delete fullCatPromises[key];
        throw err;
      });
    return fullCatPromises[key];
  };

  /** Convenience: ensure a single UC's heavy fields are merged. */
  window.__ensureFullUC = function(ucId) {
    if (!ucId) return Promise.resolve();
    if (fullUCPromises[ucId]) return fullUCPromises[ucId];
    var catId = parseInt(String(ucId).split(".")[0], 10);
    if (!catId || isNaN(catId)) return Promise.resolve();
    fullUCPromises[ucId] = window.__ensureFullCategory(catId);
    return fullUCPromises[ucId];
  };

  function _mergeCategoryFull(catId, catFull) {
    if (!catFull || !Array.isArray(catFull.s)) return;
    var stubCat = (window.DATA || []).find(function(c) { return c.i === catId; });
    if (!stubCat) return;

    var stubSubMap = {};
    stubCat.s.forEach(function(sub) {
      stubSubMap[sub.i] = sub;
      sub._ucMap = {};
      sub.u.forEach(function(uc, idx) { sub._ucMap[uc.i] = idx; });
    });

    catFull.s.forEach(function(fullSub) {
      var stubSub = stubSubMap[fullSub.i];
      if (!stubSub) return;
      (fullSub.u || []).forEach(function(fullUC) {
        var stubIdx = stubSub._ucMap[fullUC.i];
        if (typeof stubIdx === "number") {
          // Merge heavy fields onto the existing stub *in place* so any
          // existing references (ucIndex[].uc) keep pointing at the same
          // object. Stub fields take precedence for shape consistency.
          var stub = stubSub.u[stubIdx];
          for (var key in fullUC) {
            if (!Object.prototype.hasOwnProperty.call(fullUC, key)) continue;
            if (key in stub) continue; // already in stub
            stub[key] = fullUC[key];
          }
        } else {
          // Stub didn't exist for this UC — append the full record.
          stubSub.u.push(fullUC);
          stubSub._ucMap[fullUC.i] = stubSub.u.length - 1;
        }
      });
      delete stubSub._ucMap;
    });
  }
})();
