/* ───────────────────────────────────────────────────────────────────────────
 *  guide-reader.js — Shared markdown rendering + reading-mode helpers
 *
 *  Exposes:  window.GuideReader = {
 *    escapeHtml(s)         → safe HTML
 *    slugify(s)            → kebab-case anchor id
 *    render(markdown, ctx) → rendered HTML string
 *    decorateAnchors(root) → adds clickable ¶ anchors to h2/h3
 *    buildTOC(root, list)  → fills <ul> with TOC items, returns items[]
 *    wireTOCSearch(input, list)
 *    wireTOCHighlight(items, opts)
 *    wireProgress({fill, topBtn, article})
 *    autoLinkUCs(html)     → links UC-X.Y.Z references to the catalogue
 *  }
 *
 *  Used by:
 *    docs.html         → renders any markdown doc inline in the detail pane
 *    guide-reader.html → redirects to docs.html#doc=<src> (uses helpers
 *                        only as fallback when JS routing is disabled)
 *
 *  Notes
 *  -----
 *  • Pure browser JS, no dependencies. Stays in sync with the original
 *    renderer that previously lived inside guide-reader.html.
 *  • `render()` accepts an optional `ctx` argument: { srcPath } — used so
 *    Mermaid diagram fallbacks can still link to the GitHub source view.
 *  • `autoLinkUCs()` rewrites `UC-X.Y.Z` mentions inside text to anchor
 *    tags pointing at index.html#uc-X.Y.Z so the catalogue picks them up.
 * ──────────────────────────────────────────────────────────────────────── */

(function (global) {
  'use strict';

  var GITHUB_BASE = 'https://github.com/fenre/splunk-monitoring-use-cases/blob/main/';

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function slugify(text) {
    return String(text).toLowerCase()
      .replace(/\u00a0/g, ' ')
      .replace(/[^\w\s-]/g, '')
      .replace(/\s/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function renderInline(raw) {
    var tokens = [];
    function stash(html) {
      var i = tokens.length;
      tokens.push(html);
      return '\u0000T' + i + '\u0000';
    }

    var text = String(raw).replace(/`([^`\n]+?)`/g, function (_, inner) {
      return stash('<code>' + escapeHtml(inner) + '</code>');
    });

    // Inline HTML whitelist (produced by scripts/generate_doc_references.py
    // and a handful of hand-authored docs).  Same-origin markdown only, so
    // we can pass these through without XSS risk — but we keep the whitelist
    // tight and rebuild each tag from validated capture groups.
    text = text.replace(
      /<sup class=["']ref["']>\[<a href=["']#ref-([\w.-]+)["']>([\w.-]+)<\/a>\]<\/sup>/g,
      function (_, refId, label) {
        return stash(
          '<sup class="ref">[<a href="#ref-' + escapeHtml(refId) + '">' +
          escapeHtml(label) + '</a>]</sup>'
        );
      }
    );
    text = text.replace(/<a id=["']([\w.:-]+)["']><\/a>/g, function (_, id) {
      return stash('<a id="' + escapeHtml(id) + '"></a>');
    });
    text = text.replace(/<sup>([^<\n]+)<\/sup>/g, function (_, inner) {
      return stash('<sup>' + escapeHtml(inner) + '</sup>');
    });
    text = text.replace(/<kbd>([^<\n]+)<\/kbd>/g, function (_, inner) {
      return stash('<kbd>' + escapeHtml(inner) + '</kbd>');
    });
    text = text.replace(/<br\s*\/?>/g, function () {
      return stash('<br>');
    });

    text = escapeHtml(text);
    text = text.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g, function (m, label, url) {
      if (!/^(https?:|mailto:|#|\.?\.?\/)/i.test(url)) return m;
      var external = /^https?:\/\//i.test(url);
      var attrs = external ? ' target="_blank" rel="noopener noreferrer"' : '';
      var anchor = '<a href="' + escapeHtml(url) + '"' + attrs + '>' + label + '</a>';
      return stash(anchor);
    });

    // Auto-link bare URLs (e.g. plain `https://example.com/` in the
    // bibliographic footer).  We do this after explicit markdown links have
    // been stashed, so we never double-wrap an already-linked URL.  Lead
    // must be start-of-string, whitespace, or a few safe punctuation chars
    // — never `=` or `"`, which would mean we're inside an attribute.
    text = text.replace(
      /(^|[\s(\[<>])(https?:\/\/[^\s<>"'`)\]]+)/g,
      function (_, lead, url) {
        var trail = '';
        while (/[.,;:!?\)\]]$/.test(url)) {
          trail = url.slice(-1) + trail;
          url = url.slice(0, -1);
        }
        if (!url) return lead + trail;
        return lead + stash(
          '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' +
          url + '</a>'
        ) + trail;
      }
    );

    text = text.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, '$1<em>$2</em>');
    text = text.replace(/---/g, '&mdash;').replace(/--/g, '&ndash;');
    text = text.replace(/\u0000T(\d+)\u0000/g, function (_, i) { return tokens[+i]; });
    return text;
  }

  function splitTableRow(line) {
    var cells = [], cur = '';
    for (var i = 0; i < line.length; i++) {
      var c = line[i];
      if (c === '\\' && line[i + 1] === '|') { cur += '|'; i++; }
      else if (c === '|') { cells.push(cur); cur = ''; }
      else { cur += c; }
    }
    cells.push(cur);
    if (cells.length > 1) {
      if (cells[0].trim() === '') cells.shift();
      if (cells.length && cells[cells.length - 1].trim() === '') cells.pop();
    }
    return cells.map(function (x) { return x.trim(); });
  }

  function isTableSeparator(s) {
    return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(s.trim());
  }

  function render(md, ctx) {
    ctx = ctx || {};
    var srcPath = ctx.srcPath || '';

    md = String(md).replace(/^---\n[\s\S]*?\n---\n/, '');

    var lines = md.replace(/\r\n/g, '\n').split('\n');
    var out = [];
    var i = 0;

    function flushParagraph(buf) {
      if (!buf.length) return;
      var para = buf.join(' ').trim();
      if (para) out.push('<p>' + renderInline(para) + '</p>');
      buf.length = 0;
    }

    while (i < lines.length) {
      var line = lines[i];
      var stripped = line.replace(/\s+$/, '');

      if (!stripped.trim()) { i++; continue; }
      if (/^---\s*$/.test(stripped) || /^\*{3,}\s*$/.test(stripped)) { out.push('<hr>'); i++; continue; }

      var fenceMatch = stripped.match(/^(`{3,})([\w-]*)\s*$/);
      if (fenceMatch) {
        var fence = fenceMatch[1];
        var lang = fenceMatch[2] || '';
        var codeLines = [];
        i++;
        while (i < lines.length) {
          var trimmed = lines[i].replace(/\s+$/, '');
          if (trimmed === fence || (trimmed.indexOf(fence) === 0 && trimmed.length === fence.length)) {
            i++;
            break;
          }
          codeLines.push(lines[i]);
          i++;
        }
        var codeContent = escapeHtml(codeLines.join('\n'));
        if (lang === 'mermaid') {
          var ghLink = srcPath
            ? '<a href="' + escapeHtml(GITHUB_BASE + srcPath) + '" target="_blank" rel="noopener">GitHub</a>'
            : 'the source repository';
          out.push('<div class="gr-mermaid">[Mermaid diagram &mdash; view on ' + ghLink + ' for the rendered version]</div>');
        } else {
          var langLabel = lang ? '<span class="gr-lang-label">' + escapeHtml(lang) + '</span>' : '';
          out.push('<pre>' + langLabel + '<code>' + codeContent + '</code></pre>');
        }
        continue;
      }

      var hm = stripped.match(/^(#{1,6})\s+(.*?)\s*#*\s*$/);
      if (hm) {
        var level = hm[1].length;
        var htext = hm[2];
        var id = slugify(htext);
        out.push('<h' + level + ' id="' + escapeHtml(id) + '">' + renderInline(htext) + '</h' + level + '>');
        i++; continue;
      }

      // Block-level HTML whitelist for the auto-generated references footer
      // emitted by scripts/generate_doc_references.py.  Pass <details>,
      // <summary>...</summary>, </details> through verbatim so the content
      // *inside* a <details> still renders as normal markdown.
      if (/^<details>\s*$/.test(stripped)) {
        out.push('<details>'); i++; continue;
      }
      if (/^<\/details>\s*$/.test(stripped)) {
        out.push('</details>'); i++; continue;
      }
      var sm = stripped.match(/^<summary>(.*)<\/summary>\s*$/);
      if (sm) {
        out.push('<summary>' + renderInline(sm[1]) + '</summary>');
        i++; continue;
      }

      if (/^>\s?/.test(stripped)) {
        var bqBuf = [];
        while (i < lines.length && /^>\s?/.test(lines[i])) { bqBuf.push(lines[i].replace(/^>\s?/, '')); i++; }
        var parts = bqBuf.join('\n').split(/\n\s*\n/);
        out.push('<blockquote>' + parts.map(function (p) {
          return '<p>' + renderInline(p.replace(/\n/g, ' ').trim()) + '</p>';
        }).join('') + '</blockquote>');
        continue;
      }

      if (/\|/.test(stripped) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
        var header = splitTableRow(stripped);
        var sep = splitTableRow(lines[i + 1]);
        var aligns = sep.map(function (s) {
          var t = s.trim();
          if (/^:-+:$/.test(t)) return 'center';
          if (/^:-+$/.test(t)) return 'left';
          if (/^-+:$/.test(t)) return 'right';
          return '';
        });
        i += 2;
        var rows = [];
        while (i < lines.length && /\|/.test(lines[i]) && lines[i].trim()) { rows.push(splitTableRow(lines[i])); i++; }
        var thtml = '<div class="gr-tablewrap"><table><thead><tr>';
        header.forEach(function (h, idx) {
          var sty = aligns[idx] ? ' style="text-align:' + aligns[idx] + '"' : '';
          thtml += '<th' + sty + '>' + renderInline(h) + '</th>';
        });
        thtml += '</tr></thead><tbody>';
        rows.forEach(function (r) {
          thtml += '<tr>';
          for (var c = 0; c < header.length; c++) {
            var cell = r[c] != null ? r[c] : '';
            var sty2 = aligns[c] ? ' style="text-align:' + aligns[c] + '"' : '';
            thtml += '<td' + sty2 + '>' + renderInline(cell) + '</td>';
          }
          thtml += '</tr>';
        });
        thtml += '</tbody></table></div>';
        out.push(thtml);
        continue;
      }

      if (/^(\s*)([-*+])\s+/.test(stripped)) {
        var ulItems = [];
        while (i < lines.length) {
          var raw = lines[i];
          var mm = raw.match(/^(\s*)([-*+])\s+(.*)$/);
          if (mm) { ulItems.push(mm[3]); i++; }
          else if (/^\s{2,}\S/.test(raw) && ulItems.length) { ulItems[ulItems.length - 1] += ' ' + raw.trim(); i++; }
          else if (!raw.trim()) {
            if (i + 1 < lines.length && /^(\s*)([-*+])\s+/.test(lines[i + 1])) { i++; continue; }
            break;
          } else { break; }
        }
        out.push('<ul>' + ulItems.map(function (it) { return '<li>' + renderInline(it) + '</li>'; }).join('') + '</ul>');
        continue;
      }

      if (/^(\s*)\d+\.\s+/.test(stripped)) {
        var olItems = [];
        while (i < lines.length) {
          var raw2 = lines[i];
          var om = raw2.match(/^(\s*)\d+\.\s+(.*)$/);
          if (om) { olItems.push(om[2]); i++; }
          else if (/^\s{2,}\S/.test(raw2) && olItems.length) { olItems[olItems.length - 1] += ' ' + raw2.trim(); i++; }
          else if (!raw2.trim()) {
            if (i + 1 < lines.length && /^(\s*)\d+\.\s+/.test(lines[i + 1])) { i++; continue; }
            break;
          } else { break; }
        }
        out.push('<ol>' + olItems.map(function (it) { return '<li>' + renderInline(it) + '</li>'; }).join('') + '</ol>');
        continue;
      }

      var pBuf = [stripped];
      i++;
      while (i < lines.length) {
        var nxt = lines[i];
        if (!nxt.trim()) break;
        if (/^#{1,6}\s+/.test(nxt)) break;
        if (/^---\s*$/.test(nxt) || /^\*{3,}\s*$/.test(nxt)) break;
        if (/^>\s?/.test(nxt)) break;
        if (/^(\s*)([-*+])\s+/.test(nxt)) break;
        if (/^(\s*)\d+\.\s+/.test(nxt)) break;
        if (/^`{3,}/.test(nxt)) break;
        if (/\|/.test(nxt) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) break;
        if (/^<\/?details>\s*$/.test(nxt.trim())) break;
        if (/^<summary>.*<\/summary>\s*$/.test(nxt.trim())) break;
        pBuf.push(nxt);
        i++;
      }
      flushParagraph(pBuf);
    }
    return out.join('\n');
  }

  function autoLinkUCs(html) {
    return html.replace(/(>)([^<]*?)\bUC-(\d+\.\d+\.\d+)\b/g, function (m, gt, pre, id) {
      return gt + pre + '<a href="index.html#uc-' + id + '" title="View UC-' + id + ' in the catalogue">UC-' + id + '</a>';
    });
  }

  function decorateAnchors(article, opts) {
    opts = opts || {};
    var urlFor = typeof opts.urlFor === 'function'
      ? opts.urlFor
      : function (h) { return window.location.href.split('#')[0] + '#' + h.id; };
    var onAnchorClick = typeof opts.onAnchorClick === 'function' ? opts.onAnchorClick : null;
    var hs = article.querySelectorAll('h2[id], h3[id]');
    hs.forEach(function (h) {
      if (h.querySelector('.gr-anchor')) return;
      var a = document.createElement('a');
      a.className = 'gr-anchor';
      a.href = '#' + h.id;
      a.setAttribute('aria-label', 'Copy link to ' + (h.textContent || '').trim());
      a.title = 'Copy link to this section';
      a.textContent = '\u00b6';
      a.addEventListener('click', function (ev) {
        if (ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
        ev.preventDefault();
        try {
          if (navigator.clipboard) {
            navigator.clipboard.writeText(urlFor(h));
          }
        } catch (_) { /* clipboard not available */ }
        if (onAnchorClick) onAnchorClick(h);
      });
      h.insertBefore(a, h.firstChild);
    });
  }

  function buildTOC(article, listEl) {
    if (!listEl) return [];
    listEl.innerHTML = '';
    var hs = article.querySelectorAll('h2[id], h3[id], h4[id]');
    var items = [];
    hs.forEach(function (h) {
      var level = parseInt(h.tagName.substring(1), 10);
      var li = document.createElement('li');
      li.className = 'gr-toc-l' + level;
      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = (h.textContent || '').replace(/^\s*\u00b6\s*/, '').trim();
      a.setAttribute('data-target', h.id);
      a.addEventListener('click', function (ev) {
        ev.preventDefault();
        h.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      li.appendChild(a);
      listEl.appendChild(li);
      items.push({ el: h, link: a });
    });
    return items;
  }

  function wireTOCSearch(input, list) {
    if (!input || !list) return;
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      list.querySelectorAll('li').forEach(function (li) {
        var t = (li.textContent || '').toLowerCase();
        if (!q || t.indexOf(q) !== -1) li.classList.remove('gr-hidden');
        else li.classList.add('gr-hidden');
      });
    });
  }

  function wireTOCHighlight(items, opts) {
    if (!items || !items.length || !('IntersectionObserver' in window)) return null;
    opts = opts || {};
    var rootEl = opts.scrollRoot || null;
    var rootMargin = opts.rootMargin || '-64px 0px -70% 0px';
    var activeLink = null;

    function setActive(link) {
      if (activeLink === link) return;
      if (activeLink) activeLink.classList.remove('gr-active');
      if (link) link.classList.add('gr-active');
      activeLink = link;
    }

    var linkById = {};
    items.forEach(function (it) { linkById[it.el.id] = it.link; });
    var visible = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { visible[e.target.id] = e.isIntersecting; });
      var topMost = null, topY = Infinity;
      items.forEach(function (it) {
        if (!visible[it.el.id]) return;
        var y = it.el.getBoundingClientRect().top;
        if (y < topY && y >= -20) { topY = y; topMost = it.el.id; }
      });
      if (topMost && linkById[topMost]) setActive(linkById[topMost]);
    }, { root: rootEl, rootMargin: rootMargin, threshold: [0, 1] });
    items.forEach(function (it) { io.observe(it.el); });
    return io;
  }

  function wireProgress(opts) {
    opts = opts || {};
    var fill = opts.fill;
    var topBtn = opts.topBtn;
    var article = opts.article;
    var scrollEl = opts.scrollEl || window;
    if (!article) return;
    function update() {
      var rect = article.getBoundingClientRect();
      var viewH = (scrollEl === window) ? window.innerHeight : scrollEl.clientHeight;
      var total = rect.height - viewH;
      var scrolled = -rect.top;
      var pct = total > 0 ? Math.max(0, Math.min(1, scrolled / total)) : 0;
      if (fill) fill.style.width = (pct * 100).toFixed(2) + '%';
      if (topBtn) {
        if (scrolled > 280) topBtn.classList.add('gr-visible');
        else topBtn.classList.remove('gr-visible');
      }
    }
    update();
    if (scrollEl === window) {
      window.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update);
    } else {
      scrollEl.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update);
    }
    if (topBtn) {
      topBtn.addEventListener('click', function () {
        if (scrollEl === window) window.scrollTo({ top: 0, behavior: 'smooth' });
        else scrollEl.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
    return update;
  }

  global.GuideReader = {
    escapeHtml: escapeHtml,
    slugify: slugify,
    render: render,
    autoLinkUCs: autoLinkUCs,
    decorateAnchors: decorateAnchors,
    buildTOC: buildTOC,
    wireTOCSearch: wireTOCSearch,
    wireTOCHighlight: wireTOCHighlight,
    wireProgress: wireProgress,
    GITHUB_BASE: GITHUB_BASE
  };
})(typeof window !== 'undefined' ? window : this);
