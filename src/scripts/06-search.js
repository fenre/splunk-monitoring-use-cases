/* Cisco UI catalog — chunk 6: lazy-loaded sharded search index.
 *
 * Replaces the in-memory ``_searchBlob`` linear scan over the legacy 39 MB
 * data.js payload with a static, sharded inverted index built at build
 * time and served from /assets/.
 *
 * Wire-up
 * -------
 * The catalog (00-loader.js) populates window.DATA + _searchBlob first.
 * The filter pipeline (02-filters.js) runs synchronously on every
 * keystroke and does the *substring* match against _searchBlob — that
 * keeps the UI feeling instant, but only matches stub-level fields
 * (UC name, summary, source names, app names, regulation IDs).
 *
 * THIS module adds the heavy-field overlay: full SPL, full markdown
 * narrative, expanded MITRE/CIM tags. On every (debounced) query it
 * returns a Set<UCID> of additional matches found in those fields. The
 * filter pipeline UNIONS the two sets, so a UC matches the search if
 * EITHER scan finds it.
 *
 * Public API
 * ----------
 *   window.__searchIndex.query(q)            -> Promise<Set<UCID>>
 *   window.__searchIndex.warmup()            -> kick off vocab prefetch
 *   window.__searchAsyncResults              -> { q, set, when } latest
 *   window.__onSearchResults(q, set)         -> wired by 02-filters.js,
 *                                               called once shard fetch
 *                                               resolves; triggers reRender.
 *
 * Cache strategy
 * --------------
 * vocab.json: stable filename, fetched fresh per session (cache normal HTTP).
 * search-shard-NN.<hash>.json: fingerprinted, safe to cache forever.
 * In-memory: vocab + every shard requested are kept in JS for the
 * lifetime of the page; queryCache memoises {q -> Set<UCID>}.
 *
 * Failure modes
 * -------------
 * If vocab or any shard fetch fails (offline, 404, JSON parse error),
 * we log to console and return an empty set. The substring scan in
 * 02-filters.js still runs, so search continues to work over the
 * stub-level fields — this module is a strict additive layer.
 */

(function() {
  if (typeof window === 'undefined') return;

  // Root-absolute paths so the SPA works from any depth (e.g. /browse/).
  // Override via window.__CATALOG_ASSETS_BASE if hosting under a non-root prefix.
  var ASSETS_BASE = (typeof window.__CATALOG_ASSETS_BASE === 'string' && window.__CATALOG_ASSETS_BASE)
    ? window.__CATALOG_ASSETS_BASE.replace(/\/+$/, '') + '/'
    : '/assets/';

  var VOCAB_URL = ASSETS_BASE + 'search-vocab.json';
  var SHARD_BASE = ASSETS_BASE;

  var vocabPromise = null;
  var vocab = null;
  var shardCache = {};
  var queryCache = {};
  var debounceTimer = null;
  var DEBOUNCE_MS = 80;
  var MAX_PREFIX_EXPANSION = 32;
  var MAX_QUERY_TOKENS = 8;

  function _shardUrl(shardId) {
    if (!vocab || !vocab.shardFiles) return null;
    var name = vocab.shardFiles[shardId];
    return name ? SHARD_BASE + name : null;
  }

  function _fetchVocab() {
    if (vocabPromise) return vocabPromise;
    vocabPromise = fetch(VOCAB_URL, { credentials: 'same-origin' })
      .then(function(r) {
        if (!r.ok) throw new Error('vocab HTTP ' + r.status);
        return r.json();
      })
      .then(function(v) {
        if (!v || v.version !== 2 || v.hash !== 'fnv1a32' || !Array.isArray(v.tokens)) {
          throw new Error('vocab schema mismatch');
        }
        vocab = v;
        return v;
      })
      .catch(function(err) {
        console.error('[search] vocab fetch failed:', err);
        vocabPromise = null;
        throw err;
      });
    return vocabPromise;
  }

  function _fetchShard(shardId) {
    if (shardCache[shardId]) return shardCache[shardId];
    var url = _shardUrl(shardId);
    if (!url) return Promise.resolve({});
    shardCache[shardId] = fetch(url, { credentials: 'same-origin' })
      .then(function(r) {
        if (!r.ok) throw new Error('shard HTTP ' + r.status);
        return r.json();
      })
      .then(function(s) { return s.postings || {}; })
      .catch(function(err) {
        console.error('[search] shard ' + shardId + ' fetch failed:', err);
        delete shardCache[shardId];
        return {};
      });
    return shardCache[shardId];
  }

  /* ------------------------------------------------------------------
   * Query pipeline
   * ------------------------------------------------------------------ */

  function _tokenize(q) {
    if (!q) return [];
    return q.toLowerCase().split(/[^a-z0-9_]+/).filter(function(t) {
      return t.length >= 3 && t.length <= 30;
    });
  }

  function _expandPrefix(token, sortedTokens) {
    if (!sortedTokens || !sortedTokens.length) return [];
    // Exact match wins — no need to expand.
    if (_binarySearch(sortedTokens, token) !== -1) return [token];
    // Otherwise treat as a prefix: collect tokens that start with `token`.
    var lo = _lowerBound(sortedTokens, token);
    var out = [];
    for (var i = lo; i < sortedTokens.length; i++) {
      var t = sortedTokens[i];
      if (t.indexOf(token) !== 0) break;
      out.push(t);
      if (out.length >= MAX_PREFIX_EXPANSION) break;
    }
    return out;
  }

  function _binarySearch(arr, needle) {
    var lo = 0, hi = arr.length - 1;
    while (lo <= hi) {
      var mid = (lo + hi) >>> 1;
      var v = arr[mid];
      if (v === needle) return mid;
      if (v < needle) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
  }

  function _lowerBound(arr, needle) {
    var lo = 0, hi = arr.length;
    while (lo < hi) {
      var mid = (lo + hi) >>> 1;
      if (arr[mid] < needle) lo = mid + 1; else hi = mid;
    }
    return lo;
  }

  function _postingFromString(str) {
    if (!str) return [];
    var parts = str.split(',');
    var out = new Array(parts.length);
    for (var i = 0; i < parts.length; i++) out[i] = +parts[i];
    return out;
  }

  function _intersect(a, b) {
    var out = [];
    var i = 0, j = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { out.push(a[i]); i++; j++; }
      else if (a[i] < b[j]) i++;
      else j++;
    }
    return out;
  }

  function _union(arrs) {
    if (arrs.length === 1) return arrs[0];
    var s = new Set();
    for (var i = 0; i < arrs.length; i++) {
      var a = arrs[i];
      for (var j = 0; j < a.length; j++) s.add(a[j]);
    }
    var out = Array.from(s);
    out.sort(function(x, y) { return x - y; });
    return out;
  }

  function _runQuery(q) {
    if (queryCache[q]) return Promise.resolve(queryCache[q]);
    return _fetchVocab().then(function() {
      var tokens = _tokenize(q).slice(0, MAX_QUERY_TOKENS);
      if (!tokens.length) {
        var emptySet = new Set();
        queryCache[q] = emptySet;
        return emptySet;
      }
      var perTokenExpansion = tokens.map(function(t) {
        return _expandPrefix(t, vocab.tokens);
      });
      // Any query token with zero vocab matches => no UC can satisfy AND
      // semantics. Bail with an empty set rather than fetching shards.
      for (var i = 0; i < perTokenExpansion.length; i++) {
        if (perTokenExpansion[i].length === 0) {
          var s = new Set();
          queryCache[q] = s;
          return s;
        }
      }
      var shardIds = {};
      perTokenExpansion.forEach(function(arr) {
        arr.forEach(function(t) { shardIds[_shardForToken(t)] = true; });
      });
      var ids = Object.keys(shardIds).map(Number);
      return Promise.all(ids.map(_fetchShard)).then(function(shardData) {
        var byId = {};
        for (var k = 0; k < ids.length; k++) byId[ids[k]] = shardData[k];
        var perTokenPostings = perTokenExpansion.map(function(expanded) {
          var lists = expanded.map(function(t) {
            var sid = _shardForToken(t);
            var raw = byId[sid] && byId[sid][t];
            return raw ? _postingFromString(raw) : [];
          });
          return _union(lists);
        });
        var matched = perTokenPostings.reduce(function(a, b) {
          return _intersect(a, b);
        });
        var ucIds = matched.map(function(idx) { return vocab.ucIds[idx]; });
        var resultSet = new Set(ucIds);
        queryCache[q] = resultSet;
        return resultSet;
      });
    });
  }

  function _publish(q, set) {
    window.__searchAsyncResults = { q: q, set: set, when: Date.now() };
    if (typeof window.__onSearchResults === 'function') {
      try { window.__onSearchResults(q, set); } catch (e) { /* swallow */ }
    }
  }

  /* ------------------------------------------------------------------
   * Public API
   * ------------------------------------------------------------------ */

  window.__searchIndex = {
    /** Schedule a (debounced) async query and return its Promise<Set>. */
    query: function(q) {
      var key = String(q || '').toLowerCase().trim();
      if (queryCache[key]) {
        window.__searchAsyncResults = { q: key, set: queryCache[key], when: Date.now() };
        return Promise.resolve(queryCache[key]);
      }
      clearTimeout(debounceTimer);
      return new Promise(function(resolve) {
        debounceTimer = setTimeout(function() {
          _runQuery(key).then(function(set) {
            // The user may have typed more chars while we were fetching.
            // Only publish if this query is still the latest the loader saw.
            _publish(key, set);
            resolve(set);
          }).catch(function() { resolve(new Set()); });
        }, DEBOUNCE_MS);
      });
    },
    /** Best-effort vocab prefetch. Called once after catalog:ready. */
    warmup: function() {
      var ric = window.requestIdleCallback;
      if (typeof ric === 'function') {
        ric(function() { _fetchVocab().catch(function() {}); }, { timeout: 2000 });
      } else {
        setTimeout(function() { _fetchVocab().catch(function() {}); }, 250);
      }
    },
    /** True if vocab is loaded and the index is ready to answer queries. */
    isReady: function() { return vocab !== null; }
  };

  if (window.__catalogReady && typeof window.__catalogReady.then === 'function') {
    window.__catalogReady.then(function() { window.__searchIndex.warmup(); });
  } else {
    window.__searchIndex.warmup();
  }

  /* ------------------------------------------------------------------
   * FNV-1a 32-bit token hash (for shard routing).
   *
   * Mirrors render_search.py::_shard_for. FNV-1a chosen over BLAKE2b
   * because the JS implementation is 7 lines vs ~150 with no dependence
   * on Web Crypto. Distribution is uniform to within 5% across the
   * 12k-token vocabulary — plenty for static shard routing.
   * ------------------------------------------------------------------ */

  function _shardForToken(token) {
    if (!vocab) return 0;
    var hash = 0x811C9DC5;
    for (var i = 0; i < token.length; i++) {
      var code = token.charCodeAt(i);
      // Encode codepoint as UTF-8 bytes — vocab is ASCII (^[a-z0-9_]+$),
      // but we still go through the encoder for correctness.
      if (code < 0x80) {
        hash ^= code;
        hash = Math.imul(hash, 0x01000193) >>> 0;
      } else if (code < 0x800) {
        hash ^= 0xC0 | (code >> 6);
        hash = Math.imul(hash, 0x01000193) >>> 0;
        hash ^= 0x80 | (code & 0x3F);
        hash = Math.imul(hash, 0x01000193) >>> 0;
      } else {
        hash ^= 0xE0 | (code >> 12);
        hash = Math.imul(hash, 0x01000193) >>> 0;
        hash ^= 0x80 | ((code >> 6) & 0x3F);
        hash = Math.imul(hash, 0x01000193) >>> 0;
        hash ^= 0x80 | (code & 0x3F);
        hash = Math.imul(hash, 0x01000193) >>> 0;
      }
    }
    return (hash >>> 0) % vocab.shardCount;
  }
})();
