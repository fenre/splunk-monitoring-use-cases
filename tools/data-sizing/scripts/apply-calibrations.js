#!/usr/bin/env node
/**
 * One-shot calibration applier for plan-2026-05-27 Tasks 12–35.
 *
 * Loads ot-data-sources.js in a vm-context, swaps in the 24 calibrated
 * entries (drivers + compute reference + realism + citations +
 * uncertainty band), preserves descriptive metadata (name, category,
 * subcategory, description, vendor_examples, protocol, ingest_method,
 * splunk_sourcetype, related_uc_ids), then re-emits the file with the
 * same `window.OT_DATA_SOURCES = [...]` wrapper.
 *
 * Idempotent: re-running it produces a byte-identical file because the
 * calibration payloads are deterministic. Once Tasks 12–35 are merged
 * this script can be deleted (Task 40 in the plan).
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const FILE = path.join(__dirname, "..", "ot-data-sources.js");
const TODAY = "2026-05-27";

const ctx = { console, module: { exports: {} } };
ctx.window = {};
ctx.global = ctx;  // catalogue footer references `global.OT_DATA_SOURCES`
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(FILE, "utf8"), ctx);
const sources = ctx.window.OT_DATA_SOURCES;
if (!Array.isArray(sources)) throw new Error("Failed to load catalogue.");

function cite(type, url, note) {
  return { type: type, url: url, accessed: TODAY, note: note };
}

const CALIBRATIONS = {
  sec_ngfw_fortinet: {
    drivers: [
      {
        id: "throughput_gbps", label: "Sustained throughput", unit: "Gbps",
        type: "number", default: 1.0, min: 0.01, max: 100,
        profilePresets: { low: 0.3, typical: 1.0, high: 4.0 },
        help: "Sustained inspected throughput across all VDOMs. Drives base EPS via FortiAnalyzer sizing table."
      },
      {
        id: "utm_features", label: "UTM inspection bundle enabled",
        type: "enum", default: "+ips",
        options: [
          { value: "base",                "label": "Base (traffic only)" },
          { value: "+ips",                "label": "+ IPS" },
          { value: "+ips+webfilter",      "label": "+ IPS + Web Filter" },
          { value: "+ips+webfilter+av",   "label": "+ IPS + Web Filter + AV" }
        ],
        help: "Each additional inspection module adds a distinct event stream and grows bytes/event."
      }
    ],
    compute: "sec_ngfw_fortinet_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.20 },
    citations: [
      cite("vendor-sizing", "https://docs.fortinet.com/document/fortianalyzer/latest/administration-guide/",
        "Fortinet FortiAnalyzer sizing guide (logs per Gbps tables)"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/2846",
        "Splunk Add-on for Fortinet FortiGate default CEF parser rates")
    ]
  },

  sec_fw_cisco: {
    drivers: [
      {
        id: "throughput_gbps", label: "Sustained throughput", unit: "Gbps",
        type: "number", default: 1.0, min: 0.01, max: 100,
        profilePresets: { low: 0.3, typical: 1.0, high: 4.0 }
      },
      {
        id: "mode", label: "Logging mode", type: "enum", default: "ftd-syslog",
        options: [
          { value: "asa-syslog",     "label": "ASA classic syslog (compact CSV)" },
          { value: "ftd-syslog",     "label": "FTD security syslog" },
          { value: "ftd-estreamer",  "label": "FTD eStreamer (full detail)" }
        ],
        help: "ASA syslog is famously compact (~200 B); FTD security events are 1.2–2.5 KB depending on transport."
      }
    ],
    compute: "sec_fw_cisco_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.20 },
    citations: [
      cite("vendor-sizing", "https://www.cisco.com/c/en/us/td/docs/security/firepower/quick_start/sizing/firewall-sizing.html",
        "Cisco Secure Firewall logging best practices and sizing"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/1620",
        "Splunk Add-on for Cisco ASA — default sourcetype rates"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/3450",
        "Splunk_TA_cisco_firepower — eStreamer parser defaults")
    ]
  },

  sec_edr: {
    drivers: [
      {
        id: "endpoints", label: "Number of endpoints", unit: "endpoints",
        type: "number", default: 100, min: 1, max: 1e6,
        profilePresets: { low: 25, typical: 100, high: 1000 }
      },
      {
        id: "telemetry_profile", label: "Telemetry depth",
        type: "enum", default: "behavioural",
        options: [
          { value: "summary",       "label": "Summary (detections only)" },
          { value: "behavioural",   "label": "Behavioural events" },
          { value: "full-process",  "label": "Full process telemetry (raw)" }
        ],
        help: "Cross-vendor average (CrowdStrike Falcon, SentinelOne, Microsoft Defender for Endpoint, Carbon Black). Per-endpoint volume varies 100x across profiles."
      }
    ],
    compute: "sec_edr_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.18, tsidx_overhead_typical: 0.40, filterable_fraction_typical: 0.30 },
    citations: [
      cite("vendor-sizing", "https://www.crowdstrike.com/falcon-platform/data-protection/",
        "CrowdStrike Falcon raw telemetry sizing — full-process mode"),
      cite("vendor-sizing", "https://www.sentinelone.com/platform/singularity-data-lake/",
        "SentinelOne Singularity data-lake sizing reference"),
      cite("vendor-sizing", "https://learn.microsoft.com/en-us/defender-endpoint/api/advanced-hunting-overview",
        "Microsoft Defender for Endpoint advanced-hunting telemetry sizes (E5 audit volumes)")
    ]
  },

  sec_ids_cybervision: {
    drivers: [
      {
        id: "monitored_devices", label: "Monitored OT devices", unit: "devices",
        type: "number", default: 100, min: 1, max: 100000,
        profilePresets: { low: 25, typical: 100, high: 1000 }
      },
      {
        id: "dpi_mode", label: "DPI depth", type: "enum", default: "summary",
        options: [
          { value: "summary", "label": "Summary (components + state changes)" },
          { value: "full",    "label": "Full (per-flow telemetry)" }
        ]
      }
    ],
    compute: "sec_ids_cybervision_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.18, tsidx_overhead_typical: 0.40, filterable_fraction_typical: 0.15 },
    citations: [
      cite("vendor-sizing", "https://www.cisco.com/c/en/us/products/security/cyber-vision/index.html",
        "Cisco Cyber Vision sensor performance and event-density guide"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/5979",
        "Cisco Cyber Vision Add-on for Splunk — default component + flow emission rates")
    ]
  },

  sec_ise: {
    drivers: [
      {
        id: "authentications_per_hour", label: "Authentications per hour", unit: "auths/h",
        type: "number", default: 5000, min: 0, max: 1e7,
        profilePresets: { low: 500, typical: 5000, high: 50000 }
      },
      {
        id: "accounting_enabled", label: "RADIUS accounting enabled",
        type: "enum", default: "yes",
        options: [
          { value: "yes", "label": "Yes (interim updates ~4x event volume)" },
          { value: "no",  "label": "No (auth-only events)" }
        ]
      }
    ],
    compute: "sec_ise_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.10 },
    citations: [
      cite("vendor-sizing", "https://www.cisco.com/c/en/us/td/docs/security/ise/performance_and_scalability/b_ise_perf_and_scale.html",
        "Cisco ISE Performance & Scalability Guide (authentications and accounting volume)"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/1915",
        "Cisco ISE Add-on for Splunk default parser rates"),
      cite("lantern", "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Authentication_and_Access_Management",
        "Splunk Lantern auth/IAM sizing patterns")
    ]
  },

  dsa_sec_waf: {
    drivers: [
      {
        id: "requests_per_sec", label: "HTTP requests per second", unit: "rps",
        type: "number", default: 100, min: 0, max: 1e6,
        profilePresets: { low: 10, typical: 100, high: 10000 }
      },
      {
        id: "log_mode", label: "Logging mode",
        type: "enum", default: "denied-only",
        options: [
          { value: "denied-only",             "label": "Denied / blocked only (~1%)" },
          { value: "denied+sampled-allowed",  "label": "Denied + sampled allowed (~10%)" },
          { value: "full",                    "label": "Full (every request)" }
        ],
        help: "Cross-vendor average (F5 ASM, ModSecurity, AWS WAF, Cloudflare). Logged fraction is the dominant volume driver."
      }
    ],
    compute: "dsa_sec_waf_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.12, tsidx_overhead_typical: 0.30, filterable_fraction_typical: 0.20 },
    citations: [
      cite("vendor-sizing", "https://my.f5.com/manage/s/article/K000131653",
        "F5 ASM / Advanced WAF logging best-practices"),
      cite("vendor-blog", "https://github.com/owasp-modsecurity/ModSecurity/wiki/Reference-Manual-(v3.x)#SecAuditEngine",
        "ModSecurity SecAuditEngine defaults and logged-event sizing"),
      cite("vendor-sizing", "https://developers.cloudflare.com/logs/logpush/logpush-job/datasets/zone/http_requests/",
        "Cloudflare HTTP request logs (logpush dataset size)")
    ]
  },

  dsa_sec_ips_ids: {
    drivers: [
      {
        id: "inspected_throughput_gbps", label: "Inspected throughput", unit: "Gbps",
        type: "number", default: 1.0, min: 0.01, max: 100,
        profilePresets: { low: 0.3, typical: 1.0, high: 4.0 }
      },
      {
        id: "ruleset", label: "Ruleset profile", type: "enum", default: "balanced",
        options: [
          { value: "connectivity", "label": "Connectivity (~50 alerts/Gbps/h)" },
          { value: "balanced",     "label": "Balanced (~200 alerts/Gbps/h)" },
          { value: "security",     "label": "Security (~800 alerts/Gbps/h)" }
        ]
      }
    ],
    compute: "dsa_sec_ips_ids_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.10 },
    citations: [
      cite("vendor-blog", "https://docs.suricata.io/en/latest/performance/tuning-considerations.html",
        "Suricata performance / tuning guide (alert density per Gbps)"),
      cite("vendor-blog", "https://www.snort.org/documents/snort-3-user-manual",
        "Snort 3 manual — rule profile densities"),
      cite("vendor-sizing", "https://www.cisco.com/c/en/us/td/docs/security/firepower/quick_start/sizing/firewall-sizing.html",
        "Cisco FTD IPS sizing — Talos-tuned rule sets")
    ]
  },

  dsa_it_cloud_iaas: {
    drivers: [
      {
        id: "monthly_api_calls", label: "Monthly API calls", unit: "calls",
        type: "number", default: 1e6, min: 0, max: 1e12,
        profilePresets: { low: 1e5, typical: 1e6, high: 1e9 }
      },
      {
        id: "data_event_pct", label: "Data-plane events", unit: "%",
        type: "number", default: 5, min: 0, max: 100,
        profilePresets: { low: 0, typical: 5, high: 30 },
        help: "Percentage of total events that are S3/Storage/BigQuery data-plane (~4x larger than management events)."
      }
    ],
    compute: "dsa_it_cloud_iaas_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.10, tsidx_overhead_typical: 0.25, filterable_fraction_typical: 0.20 },
    citations: [
      cite("vendor-sizing", "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-pricing.html",
        "AWS CloudTrail pricing & sizing — management + data event ratios"),
      cite("vendor-sizing", "https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log",
        "Azure Monitor Activity log volumes"),
      cite("vendor-sizing", "https://cloud.google.com/logging/docs/audit",
        "GCP Cloud Audit logs — admin/data/system event sizing")
    ]
  },

  dsa_it_office365: {
    drivers: [
      {
        id: "seats", label: "Licensed seats", unit: "users",
        type: "number", default: 100, min: 0, max: 1e7,
        profilePresets: { low: 25, typical: 100, high: 10000 }
      },
      {
        id: "tier", label: "M365 license tier", type: "enum", default: "e3",
        options: [
          { value: "e3", "label": "E3 (Unified Audit Log base)" },
          { value: "e5", "label": "E5 (+ Defender XDR + ATP audit)" }
        ]
      }
    ],
    compute: "dsa_it_office365_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.15 },
    citations: [
      cite("vendor-sizing", "https://learn.microsoft.com/en-us/purview/audit-log-activities",
        "Microsoft Purview Unified Audit Log activities reference (seat × tier volumes)"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/4055",
        "Splunk Add-on for Microsoft Office 365 — Unified Audit Log defaults")
    ]
  },

  dsa_it_sso: {
    drivers: [
      {
        id: "daily_active_users", label: "Daily active users", unit: "users",
        type: "number", default: 1000, min: 0, max: 1e7,
        profilePresets: { low: 100, typical: 1000, high: 100000 }
      },
      {
        id: "mfa_enabled", label: "MFA enabled", type: "enum", default: "yes",
        options: [
          { value: "yes", "label": "Yes (~12 events/user/day)" },
          { value: "no",  "label": "No (~6 events/user/day)" }
        ]
      }
    ],
    compute: "dsa_it_sso_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.10 },
    citations: [
      cite("vendor-sizing", "https://developer.okta.com/docs/reference/api/system-log/",
        "Okta System Log API — per-user event volumes"),
      cite("vendor-sizing", "https://docs.pingidentity.com/r/en-us/pingfederate-121/help_pingfederate-administrators-reference-guide",
        "PingFederate audit log reference"),
      cite("vendor-sizing", "https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-sign-ins",
        "Microsoft Entra ID sign-in log sizing (interactive + non-interactive)")
    ]
  },

  it_windows: {
    drivers: [
      {
        id: "endpoints", label: "Windows endpoints", unit: "hosts",
        type: "number", default: 100, min: 1, max: 1e6,
        profilePresets: { low: 25, typical: 100, high: 1000 }
      },
      {
        id: "audit_policy", label: "Audit policy", type: "enum", default: "default",
        options: [
          { value: "default",                  "label": "Default (Security + System)" },
          { value: "advanced",                 "label": "Advanced audit policy" },
          { value: "advanced+ps-transcript",   "label": "Advanced + PowerShell transcript (10–40x volume)" }
        ]
      }
    ],
    compute: "it_windows_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.15 },
    citations: [
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/742",
        "Splunk Add-on for Microsoft Windows — default WinEventLog inputs"),
      cite("lantern", "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Windows_Logging",
        "Splunk Lantern Windows logging sizing patterns")
    ]
  },

  it_windows_dc: {
    drivers: [
      {
        id: "users_authenticated_per_hour", label: "Users authenticated per hour", unit: "auths/h",
        type: "number", default: 5000, min: 0, max: 1e7,
        profilePresets: { low: 500, typical: 5000, high: 50000 }
      },
      {
        id: "audit_logon_level", label: "Audit Logon level", type: "enum", default: "success+failure",
        options: [
          { value: "success-only",      "label": "Success only" },
          { value: "success+failure",   "label": "Success + Failure (+50% events)" }
        ]
      }
    ],
    compute: "it_windows_dc_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.10 },
    citations: [
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/742",
        "Splunk Add-on for Microsoft Windows — 4624/4625/4768/4769 inputs"),
      cite("lantern", "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Active_Directory_Monitoring",
        "Splunk Lantern Active Directory monitoring sizing")
    ]
  },

  it_linux: {
    drivers: [
      {
        id: "endpoints", label: "Linux endpoints", unit: "hosts",
        type: "number", default: 100, min: 1, max: 1e6,
        profilePresets: { low: 25, typical: 100, high: 1000 }
      },
      {
        id: "auditd_enabled", label: "auditd enabled", type: "enum", default: "no",
        options: [
          { value: "yes", "label": "Yes" },
          { value: "no",  "label": "No (syslog only)" }
        ]
      },
      {
        id: "auditd_ruleset_size", label: "auditd ruleset", type: "enum", default: "cis",
        options: [
          { value: "minimal", "label": "Minimal (~0.5 EPS/host)" },
          { value: "cis",     "label": "CIS hardened (~2 EPS/host)" },
          { value: "full",    "label": "Full (~8 EPS/host)" }
        ],
        help: "Only applies when auditd is enabled."
      }
    ],
    compute: "it_linux_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.15 },
    citations: [
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/833",
        "Splunk Add-on for Unix and Linux — default sourcetypes"),
      cite("lantern", "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Linux_Endpoint_Monitoring",
        "Splunk Lantern Linux endpoint monitoring sizing"),
      cite("vendor-blog", "https://github.com/splunk/splunk-connect-for-syslog",
        "SC4S reference configurations for Linux syslog ingestion")
    ]
  },

  dsa_it_database: {
    drivers: [
      {
        id: "transactions_per_sec", label: "Database transactions per second", unit: "tps",
        type: "number", default: 100, min: 0, max: 1e6,
        profilePresets: { low: 10, typical: 100, high: 10000 }
      },
      {
        id: "audit_level", label: "Audit level", type: "enum", default: "dml-only",
        options: [
          { value: "dml-only",     "label": "DML only (~1% logged)" },
          { value: "dml+ddl",      "label": "DML + DDL (~5% logged)" },
          { value: "full+select",  "label": "Full + SELECT (every txn)" }
        ]
      }
    ],
    compute: "dsa_it_database_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.10 },
    citations: [
      cite("vendor-sizing", "https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/auditing-overview.html",
        "Oracle Unified Audit volume reference"),
      cite("vendor-sizing", "https://learn.microsoft.com/en-us/sql/relational-databases/extended-events/extended-events",
        "Microsoft SQL Server Extended Events sizing"),
      cite("vendor-blog", "https://github.com/pgaudit/pgaudit",
        "PostgreSQL pgAudit reference and event density")
    ]
  },

  dsa_it_webserver: {
    drivers: [
      {
        id: "requests_per_sec", label: "HTTP requests per second", unit: "rps",
        type: "number", default: 100, min: 0, max: 1e6,
        profilePresets: { low: 10, typical: 100, high: 10000 }
      },
      {
        id: "log_format", label: "Access-log format", type: "enum", default: "combined",
        options: [
          { value: "combined",        "label": "Apache combined / nginx default (~350 B)" },
          { value: "combined+vhost",  "label": "Combined + vhost (~450 B)" },
          { value: "json-rich",       "label": "JSON rich (~1100 B)" }
        ]
      }
    ],
    compute: "dsa_it_webserver_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.10, tsidx_overhead_typical: 0.30, filterable_fraction_typical: 0.10 },
    citations: [
      cite("rfc", "https://httpd.apache.org/docs/2.4/logs.html",
        "Apache mod_log_config combined log format reference"),
      cite("vendor-blog", "https://nginx.org/en/docs/http/ngx_http_log_module.html",
        "nginx ngx_http_log_module default access log format"),
      cite("vendor-blog", "https://learn.microsoft.com/en-us/iis/configuration/system.applicationhost/sites/site/logfile/",
        "IIS W3C extended log format reference")
    ]
  },

  net_netflow: {
    drivers: [
      {
        id: "aggregated_flows_per_sec", label: "Aggregated flows per second", unit: "fps",
        type: "number", default: 1000, min: 0, max: 1e7,
        profilePresets: { low: 100, typical: 1000, high: 50000 },
        help: "Flow rate emitted toward the collector AFTER aggregation (typical 10:1 dedup at exporter)."
      },
      {
        id: "format", label: "Flow format", type: "enum", default: "netflow-v9",
        options: [
          { value: "netflow-v5", "label": "NetFlow v5 (~100 B)" },
          { value: "netflow-v9", "label": "NetFlow v9 (~150 B)" },
          { value: "ipfix",      "label": "IPFIX (~180 B)" },
          { value: "sflow",      "label": "sFlow (~200 B)" }
        ]
      }
    ],
    compute: "net_netflow_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.10, tsidx_overhead_typical: 0.15, filterable_fraction_typical: 0.15 },
    citations: [
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/489",
        "Splunk_TA_netflow / NetFlow Logic Splunk Add-on — collector defaults"),
      cite("vendor-sizing", "https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/fnetflow/configuration/15-mt/fnf-15-mt-book/cfg-fnflow-data-expts.html",
        "Cisco Flexible NetFlow data exporter sizing")
    ]
  },

  net_meraki: {
    drivers: [
      {
        id: "devices", label: "Meraki devices (MX/MR/MS/MV)", unit: "devices",
        type: "number", default: 50, min: 0, max: 100000,
        profilePresets: { low: 10, typical: 50, high: 1000 }
      },
      {
        id: "syslog_features", label: "Enabled syslog features",
        type: "enum", default: "events+flows",
        options: [
          { value: "events-only",         "label": "Events only" },
          { value: "events+flows",        "label": "Events + flows" },
          { value: "events+flows+url",    "label": "Events + flows + URL/content filter" }
        ]
      }
    ],
    compute: "net_meraki_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.12, tsidx_overhead_typical: 0.30, filterable_fraction_typical: 0.15 },
    citations: [
      cite("vendor-sizing", "https://documentation.meraki.com/General_Administration/Other_Topics/Syslog_Server_Overview_and_Configuration",
        "Meraki syslog server configuration and per-feature event mix"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/3018",
        "Splunk Add-on for Cisco Meraki — Dashboard API + syslog parsers")
    ]
  },

  dsa_net_loadbalancer: {
    drivers: [
      {
        id: "requests_per_sec", label: "Requests per second", unit: "rps",
        type: "number", default: 100, min: 0, max: 1e6,
        profilePresets: { low: 10, typical: 100, high: 10000 }
      },
      {
        id: "log_level", label: "Log verbosity", type: "enum", default: "summary",
        options: [
          { value: "denied-only",  "label": "Denied only (~0.5%)" },
          { value: "summary",      "label": "Summary (~10%)" },
          { value: "full-detail",  "label": "Full detail (every request)" }
        ]
      }
    ],
    compute: "dsa_net_loadbalancer_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.12, tsidx_overhead_typical: 0.30, filterable_fraction_typical: 0.20 },
    citations: [
      cite("vendor-blog", "https://my.f5.com/manage/s/article/K12131",
        "F5 BIG-IP logging best practices"),
      cite("vendor-blog", "https://docs.netscaler.com/en-us/citrix-adc/current-release/system/audit-logging.html",
        "Citrix NetScaler ADC audit logging configuration"),
      cite("vendor-blog", "https://avinetworks.com/docs/latest/log-settings/",
        "VMware NSX Advanced LB (AVI) logging settings")
    ]
  },

  dsa_net_vpn: {
    drivers: [
      {
        id: "concurrent_sessions", label: "Concurrent VPN sessions", unit: "sessions",
        type: "number", default: 100, min: 0, max: 1e6,
        profilePresets: { low: 10, typical: 100, high: 10000 }
      },
      {
        id: "disconnect_alerts_enabled", label: "Disconnect / heartbeat alerts",
        type: "enum", default: "yes",
        options: [
          { value: "yes", "label": "Yes (+heartbeat / tear-down events)" },
          { value: "no",  "label": "No (connect / disconnect only)" }
        ]
      }
    ],
    compute: "dsa_net_vpn_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
    realism: { rawdata_compression_typical: 0.15, tsidx_overhead_typical: 0.35, filterable_fraction_typical: 0.05 },
    citations: [
      cite("vendor-sizing", "https://www.cisco.com/c/en/us/td/docs/security/vpn_client/anyconnect/anyconnect49/administration/guide/b_AnyConnect_Administrator_Guide_4-9.html",
        "Cisco AnyConnect VPN logging reference"),
      cite("vendor-blog", "https://community.openvpn.net/openvpn/wiki/HOWTO#Logging",
        "OpenVPN logging defaults"),
      cite("vendor-sizing", "https://help.ivanti.com/ps/help/en_US/PCS/9.1R12/AG/troubleshooting/logging.htm",
        "Ivanti/Pulse Connect Secure logging guide")
    ]
  },

  proto_opcua: {
    drivers: [
      {
        id: "tag_count", label: "Subscribed tags", unit: "tags",
        type: "number", default: 500, min: 1, max: 100000,
        profilePresets: { low: 100, typical: 500, high: 5000 }
      },
      {
        id: "publish_interval_ms", label: "Publish interval", unit: "ms",
        type: "enum", default: 1000,
        options: [
          { value: 100,  "label": "100 ms (control-loop)" },
          { value: 500,  "label": "500 ms (fast metrics)" },
          { value: 1000, "label": "1 s (typical historian)" },
          { value: 5000, "label": "5 s (slow trending)" }
        ]
      },
      {
        id: "deadband_ratio", label: "Server-side deadband",
        unit: "fraction", type: "number",
        default: 0.60, min: 0.0, max: 0.95,
        profilePresets: { low: 0.20, typical: 0.60, high: 0.85 },
        help: "Fraction of publish slots filtered at the server (no change)."
      }
    ],
    compute: "proto_opcua_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.5 },
    realism: { rawdata_compression_typical: 0.10, tsidx_overhead_typical: 0.20, filterable_fraction_typical: 0.10 },
    citations: [
      cite("rfc", "https://reference.opcfoundation.org/Core/Part4/v105/docs/",
        "OPC UA Part 4 services reference (subscription, deadband)"),
      cite("vendor-blog", "https://documentation.unified-automation.com/uaserversdk/1.9.0/html/index.html",
        "Unified Automation OPC UA Server SDK performance notes"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/6049",
        "Splunk Edge Hub Connect for OPC UA — default subscription event shape")
    ]
  },

  proto_modbus: {
    drivers: [
      {
        id: "tag_count", label: "Registers polled", unit: "tags",
        type: "number", default: 500, min: 1, max: 100000,
        profilePresets: { low: 100, typical: 500, high: 5000 }
      },
      {
        id: "poll_interval_sec", label: "Polling interval", unit: "seconds",
        type: "enum", default: 30,
        options: [
          { value: 1,   "label": "1 s (control-loop)" },
          { value: 5,   "label": "5 s (fast metrics)" },
          { value: 10,  "label": "10 s" },
          { value: 30,  "label": "30 s (typical historian)" },
          { value: 60,  "label": "60 s (slow trending)" },
          { value: 300, "label": "5 min (batch reporting)" }
        ]
      },
      {
        id: "deadband_ratio", label: "Gateway value-change filter",
        unit: "fraction", type: "number",
        default: 0.40, min: 0.0, max: 0.95,
        profilePresets: { low: 0.10, typical: 0.40, high: 0.80 },
        help: "Fraction of polls dropped when the register value hasn't changed."
      }
    ],
    compute: "proto_modbus_v1",
    uncertainty: { low: 0.7, typical: 1.0, high: 1.6 },
    realism: { rawdata_compression_typical: 0.10, tsidx_overhead_typical: 0.20, filterable_fraction_typical: 0.10 },
    citations: [
      cite("rfc", "https://modbus.org/specs.php",
        "Modbus.org — Modbus TCP frame size and register data format"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/6048",
        "Splunk Edge Hub Connect for Modbus — default emission shape")
    ]
  },

  proto_mqtt: {
    drivers: [
      {
        id: "topic_count", label: "Subscribed topics", unit: "topics",
        type: "number", default: 100, min: 1, max: 1e6,
        profilePresets: { low: 10, typical: 100, high: 10000 }
      },
      {
        id: "messages_per_topic_per_sec", label: "Messages per topic per second", unit: "msgs/s",
        type: "number", default: 1, min: 0, max: 1000,
        profilePresets: { low: 0.1, typical: 1, high: 10 }
      },
      {
        id: "qos", label: "QoS level", type: "enum", default: 0,
        options: [
          { value: 0, "label": "QoS 0 (fire-and-forget, ~250 B)" },
          { value: 1, "label": "QoS 1 (at-least-once, ~280 B)" },
          { value: 2, "label": "QoS 2 (exactly-once, ~310 B)" }
        ]
      }
    ],
    compute: "proto_mqtt_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.12, tsidx_overhead_typical: 0.25, filterable_fraction_typical: 0.10 },
    citations: [
      cite("rfc", "https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html",
        "OASIS MQTT v5.0 spec — packet sizes and QoS semantics"),
      cite("vendor-blog", "https://www.hivemq.com/docs/hivemq/4.30/user-guide/configuration.html",
        "HiveMQ broker default configuration and event sizes"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/6051",
        "Splunk Edge Hub Connect for MQTT")
    ]
  },

  proto_bacnet: {
    drivers: [
      {
        id: "device_count", label: "BACnet devices", unit: "devices",
        type: "number", default: 50, min: 1, max: 10000,
        profilePresets: { low: 10, typical: 50, high: 500 }
      },
      {
        id: "polled_objects_per_device", label: "Polled objects per device", unit: "objects",
        type: "number", default: 20, min: 1, max: 1000,
        profilePresets: { low: 5, typical: 20, high: 100 }
      },
      {
        id: "poll_interval_sec", label: "Polling interval", unit: "seconds",
        type: "enum", default: 60,
        options: [
          { value: 10,  "label": "10 s (fast HVAC loop)" },
          { value: 30,  "label": "30 s" },
          { value: 60,  "label": "60 s (typical building)" },
          { value: 300, "label": "5 min (trend report)" }
        ]
      },
      {
        id: "deadband_ratio", label: "Gateway value-change filter",
        unit: "fraction", type: "number",
        default: 0.60, min: 0.0, max: 0.95,
        profilePresets: { low: 0.20, typical: 0.60, high: 0.85 }
      }
    ],
    compute: "proto_bacnet_v1",
    uncertainty: { low: 0.5, typical: 1.0, high: 2.5 },
    realism: { rawdata_compression_typical: 0.12, tsidx_overhead_typical: 0.25, filterable_fraction_typical: 0.10 },
    citations: [
      cite("rfc", "https://www.ashrae.org/technical-resources/standards-and-guidelines/standards-addenda/standard-135-2020-addenda",
        "ASHRAE 135 (BACnet) standard — object types and property data sizes"),
      cite("vendor-blog", "http://www.bacnet.org/Bibliography/index.html",
        "BACnet/IP object-property reference (BTL implementation guide)"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/6050",
        "Splunk Edge Hub Connect for BACnet — default emission shape")
    ]
  },

  proto_snmp: {
    drivers: [
      {
        id: "oid_count", label: "Polled OIDs", unit: "OIDs",
        type: "number", default: 100, min: 1, max: 100000,
        profilePresets: { low: 25, typical: 100, high: 5000 }
      },
      {
        id: "poll_interval_sec", label: "Polling interval", unit: "seconds",
        type: "enum", default: 60,
        options: [
          { value: 30,  "label": "30 s (fast metrics)" },
          { value: 60,  "label": "60 s (typical)" },
          { value: 300, "label": "5 min (trend)" }
        ]
      },
      {
        id: "version", label: "SNMP version", type: "enum", default: "v2c",
        options: [
          { value: "v2c", "label": "SNMPv2c (compact varbinds, ~120 B)" },
          { value: "v3",  "label": "SNMPv3 (+ auth/priv headers, ~180 B)" }
        ]
      }
    ],
    compute: "proto_snmp_v1",
    uncertainty: { low: 0.6, typical: 1.0, high: 2.0 },
    realism: { rawdata_compression_typical: 0.10, tsidx_overhead_typical: 0.20, filterable_fraction_typical: 0.10 },
    citations: [
      cite("rfc", "https://datatracker.ietf.org/doc/html/rfc3411",
        "IETF RFC 3411 — SNMPv3 architecture (varbind framing)"),
      cite("splunkbase-ta", "https://splunkbase.splunk.com/app/5347",
        "Splunk Connect for SNMP — default poller emission rates")
    ]
  }
};

// Apply each calibration in-place. Preserves descriptive metadata.
let applied = 0;
const ids = Object.keys(CALIBRATIONS);
for (const id of ids) {
  const idx = sources.findIndex(s => s.id === id);
  if (idx === -1) {
    console.error("MISSING source:", id);
    continue;
  }
  const orig = sources[idx];
  const cal = CALIBRATIONS[id];
  sources[idx] = {
    id: orig.id,
    name: orig.name,
    category: orig.category,
    subcategory: orig.subcategory,
    description: orig.description,
    vendor_examples: orig.vendor_examples,
    protocol: orig.protocol,
    ingest_method: orig.ingest_method,
    splunk_sourcetype: orig.splunk_sourcetype,
    calibration: "calibrated",
    drivers: cal.drivers,
    compute: cal.compute,
    uncertainty: cal.uncertainty,
    realism: cal.realism,
    citations: cal.citations,
    related_uc_ids: orig.related_uc_ids || []
  };
  applied++;
}

console.log("Applied", applied, "of", ids.length, "calibrations.");
if (applied !== ids.length) process.exit(1);

// Re-emit the file. Preserve the wrapper exactly so diff stays focused.
const header = `/**
 * Data-Sizing v2 catalogue. See tools/data-sizing/schemas/data-source.schema.json.
 *
 * Calibration tiers:
 *   - "calibrated": vendor-cited drivers + dedicated compute function in
 *     compute-functions.js. Citations array must be non-empty (CI gate).
 *   - "pending":    mechanically ported from v1; numbers approximate.
 *                   Uses endpoint_legacy_v1 or protocol_legacy_v1 driving
 *                   ordinary numeric drivers with profilePresets, so the
 *                   v1 lookup tables flow through the standard driver
 *                   pipeline (no carve-out fields).
 */
window.OT_DATA_SOURCES = `;
const footer = `;

if (typeof module !== "undefined" && module.exports) {
  module.exports = global.OT_DATA_SOURCES || window.OT_DATA_SOURCES;
}
`;

fs.writeFileSync(FILE, header + JSON.stringify(sources, null, 2) + footer);
console.log("Wrote", FILE);
