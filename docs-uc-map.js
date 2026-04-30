/* ───────────────────────────────────────────────────────────────────────────
 *  docs-uc-map.js — Bidirectional mapping between documentation and use cases
 *
 *  Consumed by:
 *    docs.html  → DOC_UC_MAP  (UC chips below each doc entry)
 *    index.html → UC_DOC_MAP  (Related Documentation in UC detail panel)
 *
 *  Single source of truth: curate DOC_UC_MAP only; the reverse index is
 *  computed automatically.  Not every doc needs UC associations — architecture,
 *  governance, and process docs are listed without `ucs`.
 *
 *  Validation:  make build  (runs validate_docs_uc_map)
 *  Quick check: node -e "eval(require('fs').readFileSync('docs-uc-map.js','utf8')); \
 *    console.log(Object.keys(DOC_UC_MAP).length+' docs, '+Object.keys(UC_DOC_MAP).length+' UCs OK');"
 * ──────────────────────────────────────────────────────────────────────────── */

/* eslint-disable no-var */
/* global DOC_UC_MAP:writable, UC_DOC_MAP:writable */

var DOC_UC_MAP = {

  /* ── Getting Started ─────────────────────────────────────────────────── */
  "docs/implementation-guide.md": {
    title: "Implementation Guide",
    ucs: ["1.1.1", "1.2.1", "5.1.1", "7.1.1", "13.1.1"]
  },
  "docs/github-pages-setup.md": {
    title: "GitHub Pages Setup"
  },

  /* ── Product Design ──────────────────────────────────────────────────── */
  "docs/DESIGN.md": {
    title: "Product Design"
  },
  "docs/architecture.md": {
    title: "Architecture"
  },
  "docs/adr/0001-markdown-as-source-of-truth.md": {
    title: "ADR-0001: Markdown as Source of Truth"
  },
  "docs/adr/0002-static-single-page-app.md": {
    title: "ADR-0002: Static Single-Page App"
  },
  "docs/adr/0003-single-catalog-json-plus-per-category-api.md": {
    title: "ADR-0003: Single catalog.json + Per-Category API"
  },
  "docs/adr/0004-python-stdlib-only.md": {
    title: "ADR-0004: Python stdlib Only"
  },
  "docs/adr/0005-uc-id-x-y-z-scheme.md": {
    title: "ADR-0005: UC-ID X.Y.Z Scheme"
  },
  "docs/adr/0006-single-file-design-doc.md": {
    title: "ADR-0006: Single-File Design Doc"
  },
  "docs/adr/README.md": {
    title: "ADR Index"
  },

  /* ── Use Case Authoring ──────────────────────────────────────────────── */
  "docs/use-case-fields.md": {
    title: "Use Case Field Reference",
    ucs: ["1.1.1", "10.1.1", "22.1.1"]
  },
  "docs/gold-standard-template.md": {
    title: "Gold Standard Template",
    ucs: ["1.1.1"]
  },
  "docs/category-files-and-names.md": {
    title: "Category Files & Names"
  },
  "docs/grandma-explanations.md": {
    title: "Plain-Language Explanations"
  },
  "docs/implementation-ordering.md": {
    title: "Implementation Ordering (Crawl/Walk/Run)",
    ucs: ["1.1.1", "1.1.2", "5.1.1", "13.1.1"]
  },
  "docs/content-gap-analysis.md": {
    title: "Content Gap Analysis"
  },

  /* ── Catalog & API ───────────────────────────────────────────────────── */
  "docs/catalog-schema.md": {
    title: "Catalog Schema Reference"
  },
  "docs/api-versioning.md": {
    title: "API Versioning"
  },
  "docs/schema-versioning.md": {
    title: "Schema Versioning"
  },
  "docs/url-scheme.md": {
    title: "URL Scheme"
  },
  "docs/source-catalog.md": {
    title: "Source Catalog"
  },

  /* ── CIM & Data Models ───────────────────────────────────────────────── */
  "docs/cim-and-data-models.md": {
    title: "CIM & Data Models",
    ucs: ["1.1.1", "1.1.2", "5.1.1", "9.1.1", "10.1.1"]
  },

  /* ── Compliance & Regulatory ─────────────────────────────────────────── */
  "docs/regulatory-primer.md": {
    title: "Regulatory Primer",
    ucs: ["22.1.1", "22.2.1", "22.3.1", "22.4.1", "22.5.1"]
  },
  "docs/coverage-methodology.md": {
    title: "Coverage Methodology",
    ucs: ["22.1.1"]
  },
  "docs/compliance-coverage.md": {
    title: "Compliance Coverage Map",
    ucs: ["22.1.1", "22.4.1", "22.5.1"]
  },
  "docs/compliance-gaps.md": {
    title: "Compliance Gaps Analysis",
    ucs: ["22.1.1", "22.4.1"]
  },
  "docs/regulatory-change-watch.md": {
    title: "Regulatory Change Watch"
  },
  "docs/legal-review-guide.md": {
    title: "Legal Review Guide"
  },
  "docs/nis2-monitoring-methodology.md": {
    title: "NIS2 Monitoring Methodology",
    ucs: ["22.2.1", "22.2.2", "22.2.3"]
  },
  "docs/nis2-external-review-pack.md": {
    title: "NIS2 External Review Pack",
    ucs: ["22.2.1", "22.2.2", "22.2.3"]
  },
  "docs/nis2-maturity-benchmark.md": {
    title: "NIS2 Maturity Benchmark",
    ucs: ["22.2.1", "22.2.2", "22.2.3"]
  },
  "docs/nis2-self-validation.md": {
    title: "NIS2 Self-Validation Record",
    ucs: ["22.2.1", "22.2.2", "22.2.3"]
  },
  "docs/research/nis2-source-map.md": {
    title: "NIS2 Source Map",
    ucs: ["22.2.1", "22.2.2", "22.2.3"]
  },

  /* ── Evidence Packs ──────────────────────────────────────────────────── */
  "docs/evidence-packs/README.md": {
    title: "Evidence Packs Overview",
    ucs: ["22.1.1"]
  },
  "docs/evidence-packs/gdpr.md": {
    title: "Evidence Pack \u2014 GDPR",
    ucs: ["22.1.1", "22.1.2", "22.1.3", "22.1.4", "22.1.5"]
  },
  "docs/evidence-packs/uk-gdpr.md": {
    title: "Evidence Pack \u2014 UK GDPR",
    ucs: ["22.7.1", "22.7.2", "22.7.3"]
  },
  "docs/evidence-packs/pci-dss.md": {
    title: "Evidence Pack \u2014 PCI DSS",
    ucs: ["22.4.1", "22.4.2", "22.4.3", "22.4.4", "22.4.5"]
  },
  "docs/evidence-packs/hipaa-security.md": {
    title: "Evidence Pack \u2014 HIPAA",
    ucs: ["22.5.1", "22.5.2", "22.5.3"]
  },
  "docs/evidence-packs/sox-itgc.md": {
    title: "Evidence Pack \u2014 SOX / ITGC",
    ucs: ["22.6.1", "22.6.2", "22.6.3"]
  },
  "docs/evidence-packs/soc-2.md": {
    title: "Evidence Pack \u2014 SOC 2",
    ucs: ["22.8.1", "22.8.2", "22.8.3"]
  },
  "docs/evidence-packs/iso-27001.md": {
    title: "Evidence Pack \u2014 ISO 27001",
    ucs: ["22.9.1", "22.9.2", "22.9.3"]
  },
  "docs/evidence-packs/nist-csf.md": {
    title: "Evidence Pack \u2014 NIST CSF",
    ucs: ["22.10.1", "22.10.2", "22.10.3"]
  },
  "docs/evidence-packs/nist-800-53.md": {
    title: "Evidence Pack \u2014 NIST 800-53",
    ucs: ["22.11.1", "22.11.2", "22.11.3"]
  },
  "docs/evidence-packs/nis2.md": {
    title: "Evidence Pack \u2014 NIS2",
    ucs: ["22.2.1", "22.2.2", "22.2.3"]
  },
  "docs/evidence-packs/dora.md": {
    title: "Evidence Pack \u2014 DORA",
    ucs: ["22.3.1", "22.3.2", "22.3.3"]
  },
  "docs/evidence-packs/cmmc.md": {
    title: "Evidence Pack \u2014 CMMC",
    ucs: ["22.12.1", "22.12.2", "22.12.3"]
  },

  /* ── Splunk Content Packs ────────────────────────────────────────────── */
  "docs/enterprise-deployment.md": {
    title: "Enterprise Deployment Guide",
    ucs: ["13.1.1", "13.1.2", "13.1.3"]
  },
  "docs/recommender-app.md": {
    title: "Recommender App"
  },
  "docs/splunk-apps-use-cases-comparison.md": {
    title: "Splunk Apps vs Use Cases Comparison"
  },
  "docs/splunk-cloud-compat.md": {
    title: "Splunk Cloud Compatibility"
  },

  /* ── Integration Guides ──────────────────────────────────────────────── */
  "docs/guides/catalyst-center.md": {
    title: "Catalyst Center Integration Guide",
    ucs: ["5.8.1", "5.4.40"]
  },
  "docs/guides/security-monitoring.md": {
    title: "Security Monitoring Domain Guide",
    ucs: [
      "9.1.1", "9.1.11", "9.1.15", "9.1.16", "9.1.17", "9.3.1", "9.5.2", "9.5.7", "9.5.8", "9.5.9", "9.6.1", "9.7.2",
      "10.1.1", "10.1.2", "10.1.3", "10.1.4", "10.2.1", "10.3.2", "10.6.1", "10.7.1", "10.7.2", "10.7.4", "10.8.1",
      "10.11.1", "10.11.2", "10.12.1", "10.13.1", "10.14.1", "10.15.2", "10.16.7",
      "17.1.2", "17.1.3", "17.1.8", "17.1.12", "17.2.2", "17.2.3", "17.2.8", "17.2.14", "17.3.1", "17.3.3", "17.3.8"
    ]
  },
  "docs/guides/cloud-monitoring.md": {
    title: "Cloud & Containers Monitoring Domain Guide",
    ucs: [
      "3.1.1", "3.1.2", "3.1.13", "3.1.25", "3.2.1", "3.2.7", "3.2.8", "3.3.1", "3.4.1", "3.5.1",
      "4.1.2", "4.1.4", "4.1.7", "4.1.8", "4.1.9", "4.1.22", "4.1.30", "4.1.51",
      "4.2.4", "4.2.7", "4.2.9", "4.3.2", "4.3.30", "4.5.2",
      "20.1.1", "20.1.2", "20.1.4", "20.1.5", "20.1.13", "20.2.1", "20.2.2", "20.2.24"
    ]
  },
  "docs/guides/application-monitoring.md": {
    title: "Application & Service Monitoring Domain Guide",
    ucs: [
      "7.1.1", "7.1.2", "7.1.3", "7.1.5", "7.1.12", "7.1.15", "7.1.17", "7.1.19", "7.2.1",
      "8.1.1", "8.1.5", "8.1.14", "8.1.15", "8.1.32", "8.2.1", "8.3.1", "8.3.3",
      "12.1.1", "12.1.2", "12.1.4", "12.1.10", "12.2.5", "12.2.8", "12.3.2",
      "13.1.1", "13.1.3", "13.1.10", "13.1.11", "13.2.1", "13.2.6",
      "16.1.1", "16.1.2", "16.1.3", "16.1.4", "16.1.9", "16.1.14", "16.2.1"
    ]
  },
  "docs/guides/collaboration-iot-monitoring.md": {
    title: "Collaboration & IoT/OT Monitoring Domain Guide",
    ucs: [
      "11.1.1", "11.1.8", "11.2.4", "11.3.16", "11.3.20", "11.4.1", "11.5.5", "11.5.9",
      "14.1.10", "14.1.18", "14.1.40", "14.2.1", "14.2.2", "14.2.3", "14.3.1",
      "14.9.1", "14.9.6", "14.9.12", "14.9.13", "14.9.15", "14.9.19", "14.9.23", "14.9.24", "14.9.25"
    ]
  },
  "docs/guides/industry-verticals.md": {
    title: "Industry Verticals Monitoring Domain Guide",
    ucs: [
      "21.1.1", "21.1.2", "21.1.7", "21.1.13",
      "21.2.3", "21.2.5", "21.2.8", "21.2.12", "21.2.14",
      "21.3.1", "21.3.14", "21.3.15", "21.3.19",
      "21.4.2", "21.4.3", "21.4.11",
      "21.5.6", "21.5.7", "21.5.10",
      "21.6.2",
      "21.7.6", "21.7.7",
      "21.8.2", "21.8.3",
      "21.9.6", "21.9.7",
      "21.10.1", "21.10.2", "21.10.3", "21.10.5", "21.10.6", "21.10.8"
    ]
  },
  "docs/guides/compliance-business.md": {
    title: "Compliance & Business Analytics Domain Guide",
    ucs: [
      "22.1.1", "22.2.1", "22.3.1", "22.4.1", "22.6.1", "22.7.1", "22.8.1",
      "22.10.1", "22.11.1", "22.12.1", "22.13.11", "22.14.1", "22.15.1", "22.16.1", "22.20.1", "22.21.4",
      "23.1.1", "23.2.1", "23.2.2", "23.2.3", "23.3.1", "23.4.1", "23.5.1", "23.6.1", "23.7.1", "23.8.1", "23.9.1"
    ]
  },
  "docs/guides/datagen-top10-use-cases.md": {
    title: "Data Generator \u2014 Top 10 Use Cases",
    ucs: ["1.1.1", "1.1.2", "5.1.1", "10.1.1"]
  },
  "docs/guides/infrastructure-monitoring.md": {
    title: "Infrastructure Monitoring Domain Guide",
    ucs: [
      "1.1.7",
      "1.1.102",
      "2.1.3",
      "2.1.21",
      "5.1.1",
      "5.2.13",
      "5.6.5",
      "5.9.5",
      "5.9.34",
      "6.1.1",
      "15.1.1",
      "18.1.1",
      "18.2.12",
      "19.1.1"
    ]
  },

  /* ── Equipment & Data Sources ────────────────────────────────────────── */
  "docs/equipment-table.md": {
    title: "Equipment Table Reference",
    ucs: ["5.1.1", "14.1.1", "14.2.1"]
  },
  "docs/samples-coverage.md": {
    title: "Sample Data Coverage"
  },

  /* ── AI & Automation ─────────────────────────────────────────────────── */
  "AGENTS.md": {
    title: "AI Agent Entrypoint"
  },
  "docs/mcp-server.md": {
    title: "MCP Server Reference"
  },

  /* ── Quality & Governance ────────────────────────────────────────────── */
  "docs/scorecard.md": {
    title: "Quality Scorecard"
  },
  "docs/provenance-coverage.md": {
    title: "Provenance Coverage"
  },
  "docs/signed-provenance.md": {
    title: "Signed Provenance"
  },
  "docs/peer-review-guide.md": {
    title: "Peer Review Guide"
  },
  "docs/sme-review-guide.md": {
    title: "SME Review Guide"
  },
  "docs/gold-standard-authoring-playbook.md": {
    title: "Gold Standard Authoring Playbook"
  },
  "docs/uc-quality-mandate.md": {
    title: "Use Case Quality Mandate"
  },

  /* ── Replication ─────────────────────────────────────────────────────── */
  "docs/replication-guide.md": {
    title: "Replication Guide"
  },

  /* ── Auditor Research ────────────────────────────────────────────────── */
  "docs/auditor-research/survey.md": {
    title: "Auditor Survey"
  },
  "docs/auditor-research/interview-guide.md": {
    title: "Auditor Interview Guide"
  },
  "docs/auditor-research/recruitment.md": {
    title: "Auditor Recruitment"
  },
  "docs/auditor-research/findings-template.md": {
    title: "Auditor Findings Template"
  },

  /* ── Product Overview ───────────────────────────────────────────────── */
  "docs/PITCH.md": {
    title: "Product Pitch"
  },
  "docs/implementation-brief-v7.1.md": {
    title: "Implementation Brief v7.1"
  },

  /* ── Migration & Release Reports ─────────────────────────────────────── */
  "docs/migration-build-parity.md": {
    title: "Migration Build Parity"
  },
  "docs/uc-migration-report.md": {
    title: "UC Migration Report"
  },
  "docs/v6.0-release-report.md": {
    title: "v6.0 Release Report"
  },
  "docs/v7.1-release-report.md": {
    title: "v7.1 Release Report"
  },
  "docs/checkpoint-phase0.md": {
    title: "Phase 0 Checkpoint"
  },
  "docs/feasibility-spike-results.md": {
    title: "Feasibility Spike Results"
  }
};

/* ── Reverse index: UC-ID → [{path, title}] ─────────────────────────────
 *  Computed automatically — do NOT edit manually.                         */
var UC_DOC_MAP = {};
Object.keys(DOC_UC_MAP).forEach(function(path) {
  var entry = DOC_UC_MAP[path];
  (entry.ucs || []).forEach(function(ucId) {
    if (!UC_DOC_MAP[ucId]) UC_DOC_MAP[ucId] = [];
    UC_DOC_MAP[ucId].push({ path: path, title: entry.title });
  });
});
