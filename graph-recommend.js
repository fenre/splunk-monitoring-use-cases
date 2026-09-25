/**
 * graph-recommend.js — ranking engine for the inventory-first use-case graph.
 *
 * Loaded as a plain script by graph-mvp.html (exposes window.UCRecommend) and
 * imported directly by the Node tests in tests/recommender/. Keep it free of
 * DOM and network access so both consumers, and eventually VISTA, can share it.
 *
 * Ranking combines two independent signals:
 *
 *   value      — how good the use case is in the abstract (quality tier,
 *                implementation wave, criticality, difficulty, quality score).
 *   relevance  — how specifically it is about the product you selected.
 *
 * Relevance matters because equipment tagging is uneven. `security_essentials`
 * tags 2142 use cases and `cisco` tags 1074, so matching on those slugs says
 * almost nothing, while the median use case carries a single tag. A use case
 * written for your product must outrank one that sprays across seventeen.
 *
 * Presentation applies two caps borrowed from the Splunk recommender app
 * (splunk-apps/splunk-uc-recommender), which hit the same failure modes:
 * round-robin across selected products so none is omitted, and a per-category
 * cap so one dense category cannot sweep the list.
 */
(function (factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (typeof window !== "undefined") window.UCRecommend = api;
})(function () {
  "use strict";

  var VALUE_QUALITY = { gold: 40, silver: 30, bronze: 18, none: 5 };
  var VALUE_WAVE = { crawl: 25, walk: 15, run: 7 };
  var VALUE_IMPACT = { critical: 20, high: 14, medium: 8, low: 3 };
  var VALUE_EASE = { beginner: 12, intermediate: 8, advanced: 4, expert: 1 };
  var CLASS_LABEL = {
    start_now: "Start now",
    high_value_blocked: "High value, unblock first",
    foundation: "Foundation",
    later: "Later"
  };
  var profileBySlug = Object.create(null);

  // The published quality score is a 0-100 integer and is the finest-grained
  // signal available. Without it the coarse buckets above tie constantly: a
  // three-product stack previously returned eight results all scoring 99.
  var QUALITY_SCORE_WEIGHT = 0.15;
  var RELEVANCE_WEIGHT = 100;

  // Share of one page of results any single category may occupy.
  var CATEGORY_SHARE = 0.34;

  // Slugs whose labels do not survive naive title-casing.
  var LABEL_OVERRIDES = {
    "splunk-es": "Splunk Enterprise Security",
    splunk_es: "Splunk Enterprise Security",
    "splunk-soar": "Splunk SOAR",
    "splunk-stream": "Splunk Stream",
    m365: "Microsoft 365",
    aws: "AWS",
    gcp: "Google Cloud",
    hec: "Splunk HEC",
    kvstore: "Splunk KV Store",
    itsi: "Splunk ITSI",
    snmp: "SNMP",
    f5: "F5",
    vmware: "VMware",
    paloalto: "Palo Alto Networks",
    paloaltonetworks: "Palo Alto Networks",
    cisco_ise: "Cisco ISE",
    security_essentials: "Splunk Security Essentials",
    db_connect: "Splunk DB Connect",
    openshift_container_platform: "OpenShift Container Platform"
  };

  function labelFor(slug) {
    if (LABEL_OVERRIDES[slug]) return LABEL_OVERRIDES[slug];
    return String(slug)
      .replace(/[-_]+/g, " ")
      .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  /**
   * How much a match on this slug tells us. A slug attached to thousands of
   * use cases is a bucket rather than a product, so it is worth less.
   */
  function specificityOf(count) {
    return 1 / Math.log(10 + (count || 0));
  }

  /**
   * How focused a use case is. One tagged with a single product is about that
   * product; one tagged with seventeen is about none of them in particular.
   */
  function focusOf(uc) {
    var spread = (uc.e || []).length || 1;
    return 1 / (1 + 0.25 * (spread - 1));
  }

  function valueOf(uc) {
    var status = uc.status === "verified" ? 6 : (uc.status === "draft" ? -5 : 0);
    return (VALUE_QUALITY[uc._qt] || 5)
      + (VALUE_WAVE[uc.wv] || 3)
      + (VALUE_IMPACT[uc.c] || 5)
      + (VALUE_EASE[uc.f] || 3)
      + status
      + (uc._qs || 0) * QUALITY_SCORE_WEIGHT;
  }

  function categoryOf(uc) {
    var id = String(uc.i || "");
    var dot = id.indexOf(".");
    return dot > 0 ? id.slice(0, dot) : id;
  }

  /**
   * Flatten the catalogue and index it by equipment slug.
   *
   * Products are derived from the slugs the use cases actually reference, not
   * from the curated EQUIPMENT registry. The registry lists 106 products while
   * the catalogue references 331, so a registry-only picker cannot reach
   * Juniper, Arista or Splunk ES at all. Registry entries still supply the
   * better labels, vendors and aliases where they exist.
   */
  function buildIndex(catalog) {
    var entries = [];
    (catalog.DATA || []).forEach(function (cat) {
      (cat.s || []).forEach(function (sub) {
        (sub.u || []).forEach(function (uc) {
          entries.push({ uc: uc, category: cat.n || "", subcategory: sub.n || "" });
        });
      });
    });

    var bySlug = Object.create(null);
    entries.forEach(function (entry) {
      (entry.uc.e || []).forEach(function (slug) {
        (bySlug[slug] || (bySlug[slug] = [])).push(entry);
      });
    });

    var registry = Object.create(null);
    (catalog.EQUIPMENT || []).forEach(function (item) {
      var id = String(item.id || item.i || "");
      if (id) registry[id] = item;
    });

    var products = Object.create(null);
    Object.keys(bySlug).forEach(function (slug) {
      var meta = registry[slug] || {};
      var count = bySlug[slug].length;
      products[slug] = {
        id: slug,
        label: meta.label || meta.n || meta.name || labelFor(slug),
        vendor: meta.vendor || meta.v || "",
        aliases: meta.aliases || meta.a || [],
        count: count,
        specificity: specificityOf(count),
        inRegistry: Boolean(registry[slug])
      };
    });

    var byId = Object.create(null);
    entries.forEach(function (entry) {
      byId[String(entry.uc.i)] = entry;
    });

    var productList = Object.keys(products).map(function (slug) { return products[slug]; });
    productList.sort(function (a, b) {
      return b.count - a.count || a.label.localeCompare(b.label);
    });

    return { entries: entries, bySlug: bySlug, products: products, productList: productList, byId: byId };
  }

  function attachProfiles(payload) {
    profileBySlug = Object.create(null);
    var profiles = (payload && payload.profiles) || {};
    Object.keys(profiles).forEach(function (slug) {
      profileBySlug[slug] = profiles[slug];
    });
  }

  function bindProfiles(index) {
    Object.keys(profileBySlug).forEach(function (slug) {
      if (!index.products[slug]) {
        index.products[slug] = {
          id: slug,
          label: profileBySlug[slug].label || labelFor(slug),
          vendor: "",
          aliases: [],
          count: (profileBySlug[slug].core || []).length,
          specificity: 1,
          inRegistry: true
        };
        index.productList.push(index.products[slug]);
      }
    });
    index.productList.sort(function (a, b) {
      return b.count - a.count || a.label.localeCompare(b.label);
    });
    return index;
  }

  function isReady(ucId, context) {
    context = context || {};
    if (context.inventoryReady && Object.prototype.hasOwnProperty.call(context.inventoryReady, ucId)) {
      return Boolean(context.inventoryReady[ucId]);
    }
    return true;
  }

  function hasGuidedContext(context) {
    if (!context) return false;
    return Boolean(
      (context.roles && context.roles.length) ||
      (context.outcomes && context.outcomes.length) ||
      (context.suites && context.suites.length) ||
      context.maturity
    );
  }

  /**
   * Map VISTA wizard formData (or a similar questionnaire) onto the context
   * object rankForProduct / startHere consume.
   */
  function contextFromWizard(form) {
    form = form || {};
    var suites = form.premiumSuites || form.suites || [];
    var mapped = [];
    (Array.isArray(suites) ? suites : []).forEach(function (s) {
      var v = String(s).toLowerCase();
      if (v.indexOf("itsi") >= 0) mapped.push("itsi");
      else if (v.indexOf("enterprise") >= 0 || v === "es") mapped.push("es");
      else if (v.indexOf("observ") >= 0 || v === "o11y") mapped.push("o11y");
      else mapped.push(v);
    });
    var wave = form.implementationWave || form.maturity || "";
    var maturity = "";
    if (/crawl|walk|run/i.test(String(wave))) {
      maturity = String(wave).toLowerCase().match(/crawl|walk|run/)[0];
    }
    return {
      roles: form.roles || form.audience || [],
      outcomes: form.desiredOutcomes || form.outcomes || [],
      suites: mapped,
      maturity: maturity,
      vertical: form.industryVertical || form.vertical || "",
      inventoryReady: form.inventoryReady || null
    };
  }

  function classify(classHint, ucId, context) {
    var hint = classHint || "start_now";
    var ready = isReady(ucId, context);
    if (!ready && hint !== "later" && hint !== "foundation") return "high_value_blocked";
    if (hint === "foundation") return "foundation";
    if (hint === "later") return "later";
    return ready ? "start_now" : "high_value_blocked";
  }

  function scoreEntry(index, entry, slug) {
    var product = index.products[slug];
    var specificity = product ? product.specificity : specificityOf(0);
    var relevance = specificity * focusOf(entry.uc) * RELEVANCE_WEIGHT;
    return valueOf(entry.uc) + relevance;
  }

  /**
   * Plain-language justification. Leads with product specificity because that
   * is the part a non-expert cannot infer from the badges.
   */
  function reasonFor(entry, slug, index) {
    var uc = entry.uc;
    var reasons = [];
    var spread = (uc.e || []).length;
    var product = index.products[slug];
    var name = product ? product.label : labelFor(slug);
    if (spread === 1) reasons.push("written specifically for " + name);
    else if (spread <= 3) reasons.push("closely targeted at " + name);
    if (uc._qt === "gold") reasons.push("gold-standard documentation");
    else if (uc._qt === "silver") reasons.push("well documented");
    if (uc.wv === "crawl") reasons.push("a foundation to build on");
    if (uc.c === "critical" || uc.c === "high") reasons.push("high operational impact");
    if (uc.f === "beginner" || uc.f === "intermediate") reasons.push("practical to start");
    if (!reasons.length) reasons.push("relevant to " + name);
    return reasons.join(", ");
  }

  function decorate(index, entry, slug, extras) {
    extras = extras || {};
    var base = extras.score != null ? extras.score : scoreEntry(index, entry, slug);
    return {
      uc: entry.uc,
      slug: slug,
      category: entry.category,
      subcategory: entry.subcategory,
      score: base,
      reason: extras.reason || reasonFor(entry, slug, index),
      why: extras.why || "",
      whyNow: extras.whyNow || "",
      metric: extras.metric || "",
      dataNeeded: extras.dataNeeded || [],
      sources: extras.sources || [],
      classHint: extras.classHint || "",
      confidence: extras.confidence || entry.uc._qt || "",
      presentationClass: extras.presentationClass || "later"
    };
  }

  function rankCatalogOnly(index, slug, limit) {
    var matches = index.bySlug[slug] || [];
    var ranked = matches.map(function (entry) {
      var item = decorate(index, entry, slug);
      item.presentationClass = "start_now";
      return item;
    });
    ranked.sort(function (a, b) {
      return b.score - a.score
        || String(a.uc.i).localeCompare(String(b.uc.i), undefined, { numeric: true });
    });
    return typeof limit === "number" ? ranked.slice(0, limit) : ranked;
  }

  /** Best use cases for a single product, highest value and relevance first. */
  function rankForProduct(index, slug, limit, context) {
    context = context || {};
    var profile = profileBySlug[slug];
    if (!profile) return rankCatalogOnly(index, slug, limit);
    var ranked = [];
    var seen = Object.create(null);
    (profile.core || []).forEach(function (core) {
      var entry = index.byId[core.i];
      if (!entry) {
        entry = { uc: { i: core.i, n: "UC-" + core.i, e: [slug] }, category: "", subcategory: "" };
      }
      var reason = hasGuidedContext(context)
        ? (core.why + " " + core.now)
        : ("Best-practice starting point. " + core.why);
      var item = decorate(index, entry, slug, {
        score: (11 - (core.r || 10)) * 1000,
        reason: reason,
        why: core.why,
        whyNow: core.now,
        metric: core.m,
        dataNeeded: core.d,
        sources: core.src,
        classHint: core.c,
        confidence: profile.confidence,
        presentationClass: classify(core.c, core.i, context)
      });
      ranked.push(item);
      seen[core.i] = true;
    });
    (index.bySlug[slug] || []).forEach(function (entry) {
      var id = String(entry.uc.i);
      if (seen[id]) return;
      var extra = decorate(index, entry, slug);
      extra.presentationClass = "later";
      extra.score = extra.score / 10;
      ranked.push(extra);
    });
    ranked.sort(function (a, b) {
      return b.score - a.score
        || String(a.uc.i).localeCompare(String(b.uc.i), undefined, { numeric: true });
    });
    return typeof limit === "number" ? ranked.slice(0, limit) : ranked;
  }

  /** One shortlist per selected product, so nothing you selected is omitted. */
  function perProduct(index, slugs, perProductLimit, context) {
    var limit = perProductLimit || 5;
    return (slugs || []).filter(function (slug) {
      return (index.bySlug[slug] || []).length > 0 || profileBySlug[slug];
    }).map(function (slug) {
      var product = index.products[slug];
      var profile = profileBySlug[slug];
      return {
        slug: slug,
        label: (profile && profile.label) || (product ? product.label : labelFor(slug)),
        total: (index.bySlug[slug] || []).length,
        items: rankForProduct(index, slug, limit, context)
      };
    });
  }

  /**
   * Merged shortlist across the whole stack.
   *
   * Round-robins across products so every selected product surfaces before any
   * product gets a second slot, and caps each category so a dense category
   * cannot sweep the page. A use case matching several selected products is
   * credited to the one it scores highest for, and never repeats.
   */
  function startHere(index, slugs, limit, context) {
    var want = limit || 8;
    var active = (slugs || []).filter(function (slug) {
      return (index.bySlug[slug] || []).length > 0 || profileBySlug[slug];
    });
    if (!active.length) return [];

    var queues = active.map(function (slug) { return rankForProduct(index, slug, undefined, context); });
    var cursors = active.map(function () { return 0; });
    var categoryCap = active.length === 1
      ? want
      : Math.max(1, Math.ceil(want * CATEGORY_SHARE));

    var picked = [];
    var seen = Object.create(null);
    var perCategory = Object.create(null);
    var deferred = [];

    var exhausted = false;
    while (picked.length < want && !exhausted) {
      exhausted = true;
      for (var q = 0; q < queues.length && picked.length < want; q += 1) {
        var queue = queues[q];
        var taken = false;
        while (cursors[q] < queue.length && !taken) {
          var candidate = queue[cursors[q]];
          cursors[q] += 1;
          exhausted = false;
          var id = String(candidate.uc.i);
          if (seen[id]) continue;
          var cat = categoryOf(candidate.uc);
          if ((perCategory[cat] || 0) >= categoryCap) {
            deferred.push(candidate);
            continue;
          }
          seen[id] = true;
          perCategory[cat] = (perCategory[cat] || 0) + 1;
          picked.push(candidate);
          taken = true;
        }
      }
    }

    // Sparse stacks may not fill the page once category caps are applied; top
    // up with the best deferred candidates rather than returning a short list.
    for (var d = 0; d < deferred.length && picked.length < want; d += 1) {
      var extra = deferred[d];
      var extraId = String(extra.uc.i);
      if (seen[extraId]) continue;
      seen[extraId] = true;
      picked.push(extra);
    }
    return picked;
  }

  /**
   * Every use case touching the stack, de-duplicated and credited to its
   * best-scoring product. Backs the Expert table and the coverage counters.
   */
  function allMatches(index, slugs) {
    var best = Object.create(null);
    (slugs || []).forEach(function (slug) {
      (index.bySlug[slug] || []).forEach(function (entry) {
        var id = String(entry.uc.i);
        var scored = decorate(index, entry, slug);
        if (!best[id] || scored.score > best[id].score) best[id] = scored;
      });
    });
    var out = Object.keys(best).map(function (id) { return best[id]; });
    out.sort(function (a, b) {
      return b.score - a.score
        || String(a.uc.i).localeCompare(String(b.uc.i), undefined, { numeric: true });
    });
    return out;
  }

  return {
    buildIndex: buildIndex,
    attachProfiles: attachProfiles,
    bindProfiles: bindProfiles,
    rankForProduct: rankForProduct,
    perProduct: perProduct,
    startHere: startHere,
    allMatches: allMatches,
    valueOf: valueOf,
    labelFor: labelFor,
    classify: classify,
    contextFromWizard: contextFromWizard,
    CLASS_LABEL: CLASS_LABEL
  };
});
