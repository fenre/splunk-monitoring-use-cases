/**
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
window.OT_DATA_SOURCES = [
  {
    "id": "sec_ngfw_paloalto",
    "name": "Palo Alto NGFW",
    "category": "Security Sources",
    "subcategory": "Firewalls",
    "description": "Next-Gen Firewall traffic, threat, URL, DNS-Security, WildFire logs",
    "vendor_examples": "PA-220, PA-440, PA-3200, PA-5400, PA-7000, PA-VM",
    "protocol": "Syslog / Splunk_TA_paloalto API",
    "ingest_method": "Splunk_TA_paloalto",
    "splunk_sourcetype": "pan:traffic, pan:threat, pan:url, pan:system, pan:config",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "throughput_gbps",
        "label": "Sustained throughput",
        "unit": "Gbps",
        "type": "number",
        "default": 1,
        "min": 0.01,
        "max": 100,
        "profilePresets": {
          "low": 0.3,
          "typical": 1,
          "high": 4
        },
        "help": "Sustained inspected throughput across all virtual systems. Drives base EPS via PAN-OS log-storage table."
      },
      {
        "id": "log_profile",
        "label": "Log subscriptions enabled",
        "type": "enum",
        "default": "traffic+threat",
        "options": [
          {
            "value": "traffic-only",
            "label": "Traffic only"
          },
          {
            "value": "traffic+threat",
            "label": "Traffic + Threat"
          },
          {
            "value": "traffic+threat+url",
            "label": "Traffic + Threat + URL"
          },
          {
            "value": "traffic+threat+url+dns+wildfire",
            "label": "Traffic + Threat + URL + DNS-Security + WildFire"
          }
        ],
        "help": "Enabled log streams. Each additional subscription adds a distinct sourcetype and grows EPS + bytes/event."
      }
    ],
    "compute": "fw_palo_alto_ngfw_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.18,
      "tsidx_overhead_typical": 0.4,
      "filterable_fraction_typical": 0.2
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-admin/monitoring/log-storage-sizing",
        "accessed": "2026-05-27",
        "note": "PAN-OS 11 log-storage sizing tables"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/491",
        "accessed": "2026-05-27",
        "note": "Splunk_TA_paloalto default props.conf per-sourcetype rates"
      },
      {
        "type": "lantern",
        "url": "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Architectures/Splunk_Validated_Architectures",
        "accessed": "2026-05-27",
        "note": "Splunk Validated Architectures firewall sizing guidance"
      }
    ],
    "related_uc_ids": [
      "5.2.1",
      "5.2.2",
      "5.2.3",
      "17.2.9",
      "17.3.23"
    ]
  },
  {
    "id": "sec_ngfw_fortinet",
    "name": "Fortinet FortiGate",
    "category": "Security Sources",
    "subcategory": "Firewalls",
    "description": "UTM firewall traffic, IPS, web filter, and application control logs",
    "vendor_examples": "FortiGate 40F, 60F, 100F, 200F, 600E, 3000F",
    "protocol": "Syslog / CEF",
    "ingest_method": "SC4S → HEC",
    "splunk_sourcetype": "fgt_traffic, fgt_utm, fgt_event",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "throughput_gbps",
        "label": "Sustained throughput",
        "unit": "Gbps",
        "type": "number",
        "default": 1,
        "min": 0.01,
        "max": 100,
        "profilePresets": {
          "low": 0.3,
          "typical": 1,
          "high": 4
        },
        "help": "Sustained inspected throughput across all VDOMs. Drives base EPS via FortiAnalyzer sizing table."
      },
      {
        "id": "utm_features",
        "label": "UTM inspection bundle enabled",
        "type": "enum",
        "default": "+ips",
        "options": [
          {
            "value": "base",
            "label": "Base (traffic only)"
          },
          {
            "value": "+ips",
            "label": "+ IPS"
          },
          {
            "value": "+ips+webfilter",
            "label": "+ IPS + Web Filter"
          },
          {
            "value": "+ips+webfilter+av",
            "label": "+ IPS + Web Filter + AV"
          }
        ],
        "help": "Each additional inspection module adds a distinct event stream and grows bytes/event."
      }
    ],
    "compute": "sec_ngfw_fortinet_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.2
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://docs.fortinet.com/document/fortianalyzer/latest/administration-guide/",
        "accessed": "2026-05-27",
        "note": "Fortinet FortiAnalyzer sizing guide (logs per Gbps tables)"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/2846",
        "accessed": "2026-05-27",
        "note": "Splunk Add-on for Fortinet FortiGate default CEF parser rates"
      }
    ],
    "related_uc_ids": [
      "5.2.44",
      "5.2.45",
      "5.2.46",
      "17.3.39",
      "17.3.42"
    ]
  },
  {
    "id": "sec_fw_cisco",
    "name": "Cisco Secure Firewall (FTD / ASA)",
    "category": "Security Sources",
    "subcategory": "Firewalls",
    "description": "Firepower Threat Defense and ASA firewall events, connection logs, and IPS alerts",
    "vendor_examples": "Firepower 1010, 2100, 4100, 9300; ASA 5500-X",
    "protocol": "Syslog / eStreamer",
    "ingest_method": "SC4S (syslog) or eStreamer TA (HF)",
    "splunk_sourcetype": "cisco:asa, cisco:firepower:syslog",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "throughput_gbps",
        "label": "Sustained throughput",
        "unit": "Gbps",
        "type": "number",
        "default": 1,
        "min": 0.01,
        "max": 100,
        "profilePresets": {
          "low": 0.3,
          "typical": 1,
          "high": 4
        }
      },
      {
        "id": "mode",
        "label": "Logging mode",
        "type": "enum",
        "default": "ftd-syslog",
        "options": [
          {
            "value": "asa-syslog",
            "label": "ASA classic syslog (compact CSV)"
          },
          {
            "value": "ftd-syslog",
            "label": "FTD security syslog"
          },
          {
            "value": "ftd-estreamer",
            "label": "FTD eStreamer (full detail)"
          }
        ],
        "help": "ASA syslog is famously compact (~200 B); FTD security events are 1.2–2.5 KB depending on transport."
      }
    ],
    "compute": "sec_fw_cisco_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.2
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://www.cisco.com/c/en/us/td/docs/security/firepower/quick_start/sizing/firewall-sizing.html",
        "accessed": "2026-05-27",
        "note": "Cisco Secure Firewall logging best practices and sizing"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/1620",
        "accessed": "2026-05-27",
        "note": "Splunk Add-on for Cisco ASA — default sourcetype rates"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/3450",
        "accessed": "2026-05-27",
        "note": "Splunk_TA_cisco_firepower — eStreamer parser defaults"
      }
    ],
    "related_uc_ids": [
      "5.2.1",
      "5.2.3",
      "10.1.46",
      "10.1.58",
      "10.1.62"
    ]
  },
  {
    "id": "sec_ids_claroty",
    "name": "Claroty (OT IDS/IPS)",
    "category": "Security Sources",
    "subcategory": "OT IDS / IPS",
    "description": "OT network monitoring — asset discovery, vulnerability detection, and anomaly alerts",
    "vendor_examples": "Claroty CTD, xDome",
    "protocol": "Syslog / CEF / REST API",
    "ingest_method": "HEC or SC4S + TA API",
    "splunk_sourcetype": "claroty:alert, claroty:asset",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 5,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 2000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 2000,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.5",
      "14.9.20",
      "14.9.21"
    ]
  },
  {
    "id": "sec_ids_nozomi",
    "name": "Nozomi Networks (OT IDS)",
    "category": "Security Sources",
    "subcategory": "OT IDS / IPS",
    "description": "OT/IoT network visibility — threat detection, asset tracking, vulnerability assessment",
    "vendor_examples": "Nozomi Guardian, Vantage",
    "protocol": "Syslog / CEF / REST API",
    "ingest_method": "SC4S or TA API → HEC",
    "splunk_sourcetype": "nozomi:alert, nozomi:asset",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 5,
          "high": 25
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 2000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 2000,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.5",
      "14.9.8",
      "14.9.20"
    ]
  },
  {
    "id": "sec_ids_dragos",
    "name": "Dragos Platform (OT IDS)",
    "category": "Security Sources",
    "subcategory": "OT IDS / IPS",
    "description": "Industrial cybersecurity platform — threat intelligence, asset visibility, vulnerability management",
    "vendor_examples": "Dragos Platform, Neighborhood Keeper",
    "protocol": "Syslog / REST API",
    "ingest_method": "SC4S or TA API → HEC",
    "splunk_sourcetype": "dragos:alert, dragos:asset",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 5,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 2500,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 2500,
          "high": 6000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.5",
      "14.9.20",
      "14.9.22"
    ]
  },
  {
    "id": "sec_ids_cybervision",
    "name": "Cisco Cyber Vision",
    "category": "Security Sources",
    "subcategory": "OT IDS / IPS",
    "description": "Industrial network visibility — OT asset discovery, flow analysis, vulnerability detection",
    "vendor_examples": "Cyber Vision Center, Sensor (embedded in IE switches)",
    "protocol": "Syslog / REST API",
    "ingest_method": "Splunk TA (API) + SC4S",
    "splunk_sourcetype": "cisco:cybervision:event",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "monitored_devices",
        "label": "Monitored OT devices",
        "unit": "devices",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 25,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "dpi_mode",
        "label": "DPI depth",
        "type": "enum",
        "default": "summary",
        "options": [
          {
            "value": "summary",
            "label": "Summary (components + state changes)"
          },
          {
            "value": "full",
            "label": "Full (per-flow telemetry)"
          }
        ]
      }
    ],
    "compute": "sec_ids_cybervision_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.18,
      "tsidx_overhead_typical": 0.4,
      "filterable_fraction_typical": 0.15
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://www.cisco.com/c/en/us/products/security/cyber-vision/index.html",
        "accessed": "2026-05-27",
        "note": "Cisco Cyber Vision sensor performance and event-density guide"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/5979",
        "accessed": "2026-05-27",
        "note": "Cisco Cyber Vision Add-on for Splunk — default component + flow emission rates"
      }
    ],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.5",
      "14.9.20",
      "14.9.21"
    ]
  },
  {
    "id": "sec_edr",
    "name": "Endpoint Detection & Response (EDR)",
    "category": "Security Sources",
    "subcategory": "Endpoint Security",
    "description": "Endpoint telemetry — process creation, file access, network connections, threat alerts",
    "vendor_examples": "CrowdStrike Falcon, Microsoft Defender, Carbon Black, SentinelOne",
    "protocol": "REST API / Streaming API",
    "ingest_method": "Splunk TA (API) → HEC",
    "splunk_sourcetype": "crowdstrike:events, msdefender:events",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "endpoints",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 25,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "telemetry_profile",
        "label": "Telemetry depth",
        "type": "enum",
        "default": "behavioural",
        "options": [
          {
            "value": "summary",
            "label": "Summary (detections only)"
          },
          {
            "value": "behavioural",
            "label": "Behavioural events"
          },
          {
            "value": "full-process",
            "label": "Full process telemetry (raw)"
          }
        ],
        "help": "Cross-vendor average (CrowdStrike Falcon, SentinelOne, Microsoft Defender for Endpoint, Carbon Black). Per-endpoint volume varies 100x across profiles."
      }
    ],
    "compute": "sec_edr_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.18,
      "tsidx_overhead_typical": 0.4,
      "filterable_fraction_typical": 0.3
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://www.crowdstrike.com/falcon-platform/data-protection/",
        "accessed": "2026-05-27",
        "note": "CrowdStrike Falcon raw telemetry sizing — full-process mode"
      },
      {
        "type": "vendor-sizing",
        "url": "https://www.sentinelone.com/platform/singularity-data-lake/",
        "accessed": "2026-05-27",
        "note": "SentinelOne Singularity data-lake sizing reference"
      },
      {
        "type": "vendor-sizing",
        "url": "https://learn.microsoft.com/en-us/defender-endpoint/api/advanced-hunting-overview",
        "accessed": "2026-05-27",
        "note": "Microsoft Defender for Endpoint advanced-hunting telemetry sizes (E5 audit volumes)"
      }
    ],
    "related_uc_ids": [
      "10.7.277",
      "10.11.41",
      "10.11.42",
      "10.11.45",
      "10.11.46"
    ]
  },
  {
    "id": "sec_ise",
    "name": "Cisco ISE",
    "category": "Security Sources",
    "subcategory": "Identity & Access",
    "description": "Network access control — authentication, authorization, accounting (AAA), posture, profiling",
    "vendor_examples": "Cisco ISE 3.x",
    "protocol": "Syslog / pxGrid",
    "ingest_method": "SC4S (syslog) + pxGrid TA",
    "splunk_sourcetype": "cisco:ise:syslog",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "authentications_per_hour",
        "label": "Authentications per hour",
        "unit": "auths/h",
        "type": "number",
        "default": 5000,
        "min": 0,
        "max": 10000000,
        "profilePresets": {
          "low": 500,
          "typical": 5000,
          "high": 50000
        }
      },
      {
        "id": "accounting_enabled",
        "label": "RADIUS accounting enabled",
        "type": "enum",
        "default": "yes",
        "options": [
          {
            "value": "yes",
            "label": "Yes (interim updates ~4x event volume)"
          },
          {
            "value": "no",
            "label": "No (auth-only events)"
          }
        ]
      }
    ],
    "compute": "sec_ise_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://www.cisco.com/c/en/us/td/docs/security/ise/performance_and_scalability/b_ise_perf_and_scale.html",
        "accessed": "2026-05-27",
        "note": "Cisco ISE Performance & Scalability Guide (authentications and accounting volume)"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/1915",
        "accessed": "2026-05-27",
        "note": "Cisco ISE Add-on for Splunk default parser rates"
      },
      {
        "type": "lantern",
        "url": "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Authentication_and_Access_Management",
        "accessed": "2026-05-27",
        "note": "Splunk Lantern auth/IAM sizing patterns"
      }
    ],
    "related_uc_ids": [
      "17.1.1",
      "17.1.3",
      "17.1.7",
      "17.1.13",
      "17.1.21"
    ]
  },
  {
    "id": "dsa_sec_vuln_mgmt",
    "name": "Vulnerability Management (VM)",
    "category": "Security Sources",
    "subcategory": "Vulnerability Scanning",
    "description": "Scan results and vulnerability findings from enterprise VM platforms",
    "vendor_examples": "Qualys, Nessus, Tenable, Rapid7 InsightVM, Tripwire IP360",
    "protocol": "REST API / Syslog",
    "ingest_method": "TA (API poll) or HEC",
    "splunk_sourcetype": "qualys:hostDetection, nessus:scan",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.3,
          "typical": 1,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 2000,
        "min": 0,
        "profilePresets": {
          "low": 1000,
          "typical": 2000,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.6.1",
      "10.6.2",
      "10.6.3",
      "10.6.4",
      "10.6.5"
    ]
  },
  {
    "id": "dsa_sec_ips_ids",
    "name": "IPS/IDS (Network)",
    "category": "Security Sources",
    "subcategory": "Intrusion Detection",
    "description": "Network intrusion detection/prevention alerts and logs",
    "vendor_examples": "Snort, Suricata, Cisco Firepower IPS, TippingPoint, McAfee NSP",
    "protocol": "Syslog / CEF / LEEF",
    "ingest_method": "SC4S or Syslog → HEC",
    "splunk_sourcetype": "snort, suricata, cisco:firepower:syslog",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "inspected_throughput_gbps",
        "label": "Inspected throughput",
        "unit": "Gbps",
        "type": "number",
        "default": 1,
        "min": 0.01,
        "max": 100,
        "profilePresets": {
          "low": 0.3,
          "typical": 1,
          "high": 4
        }
      },
      {
        "id": "ruleset",
        "label": "Ruleset profile",
        "type": "enum",
        "default": "balanced",
        "options": [
          {
            "value": "connectivity",
            "label": "Connectivity (~50 alerts/Gbps/h)"
          },
          {
            "value": "balanced",
            "label": "Balanced (~200 alerts/Gbps/h)"
          },
          {
            "value": "security",
            "label": "Security (~800 alerts/Gbps/h)"
          }
        ]
      }
    ],
    "compute": "dsa_sec_ips_ids_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "vendor-blog",
        "url": "https://docs.suricata.io/en/latest/performance/tuning-considerations.html",
        "accessed": "2026-05-27",
        "note": "Suricata performance / tuning guide (alert density per Gbps)"
      },
      {
        "type": "vendor-blog",
        "url": "https://www.snort.org/documents/snort-3-user-manual",
        "accessed": "2026-05-27",
        "note": "Snort 3 manual — rule profile densities"
      },
      {
        "type": "vendor-sizing",
        "url": "https://www.cisco.com/c/en/us/td/docs/security/firepower/quick_start/sizing/firewall-sizing.html",
        "accessed": "2026-05-27",
        "note": "Cisco FTD IPS sizing — Talos-tuned rule sets"
      }
    ],
    "related_uc_ids": [
      "10.2.1",
      "10.2.2",
      "10.2.3",
      "10.2.4",
      "10.2.5"
    ]
  },
  {
    "id": "dsa_sec_threat_intel",
    "name": "Threat Intelligence Feeds",
    "category": "Security Sources",
    "subcategory": "Threat Intelligence",
    "description": "Indicator of Compromise (IoC) feeds, blocklists, and threat intel lookups",
    "vendor_examples": "Anomali, CrowdStrike Intel, FireEye iSIGHT, MISP, AlienVault OTX",
    "protocol": "REST API / STIX-TAXII",
    "ingest_method": "TA (API poll) or HEC",
    "splunk_sourcetype": "threat_intel, stix:indicator",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 2,
          "typical": 3,
          "high": 30
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.6,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.6,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1000,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.7.45",
      "10.7.46",
      "10.7.47",
      "10.7.48",
      "10.7.49"
    ]
  },
  {
    "id": "dsa_sec_malware_sandbox",
    "name": "Automated Malware Analysis (Sandbox)",
    "category": "Security Sources",
    "subcategory": "Malware Analysis",
    "description": "Sandbox detonation results, file analysis verdicts, behavioral reports",
    "vendor_examples": "Cisco AMP, FireEye, Check Point SandBlast, Cuckoo, Lastline",
    "protocol": "REST API / Syslog",
    "ingest_method": "TA (API poll) or SC4S",
    "splunk_sourcetype": "cisco:amp:event, fireeye_nx",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.6,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.6,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 3000,
        "min": 0,
        "profilePresets": {
          "low": 1500,
          "typical": 3000,
          "high": 8000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.7.277",
      "10.3.1",
      "10.3.2",
      "10.3.3",
      "10.3.4"
    ]
  },
  {
    "id": "dsa_sec_waf",
    "name": "WAF (Web Application Firewall)",
    "category": "Security Sources",
    "subcategory": "Web Security",
    "description": "Web application firewall logs — HTTP requests, blocks, rule violations",
    "vendor_examples": "Imperva, F5 ASM, Barracuda, Radware, Citrix ADC, AWS WAF, Cloudflare",
    "protocol": "Syslog / CEF / REST API",
    "ingest_method": "SC4S or TA (API poll)",
    "splunk_sourcetype": "imperva:waf, f5:bigip:asm",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "requests_per_sec",
        "label": "HTTP requests per second",
        "unit": "rps",
        "type": "number",
        "default": 100,
        "min": 0,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 100,
          "high": 10000
        }
      },
      {
        "id": "log_mode",
        "label": "Logging mode",
        "type": "enum",
        "default": "denied-only",
        "options": [
          {
            "value": "denied-only",
            "label": "Denied / blocked only (~1%)"
          },
          {
            "value": "denied+sampled-allowed",
            "label": "Denied + sampled allowed (~10%)"
          },
          {
            "value": "full",
            "label": "Full (every request)"
          }
        ],
        "help": "Cross-vendor average (F5 ASM, ModSecurity, AWS WAF, Cloudflare). Logged fraction is the dominant volume driver."
      }
    ],
    "compute": "dsa_sec_waf_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.12,
      "tsidx_overhead_typical": 0.3,
      "filterable_fraction_typical": 0.2
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://my.f5.com/manage/s/article/K000131653",
        "accessed": "2026-05-27",
        "note": "F5 ASM / Advanced WAF logging best-practices"
      },
      {
        "type": "vendor-blog",
        "url": "https://github.com/owasp-modsecurity/ModSecurity/wiki/Reference-Manual-(v3.x)#SecAuditEngine",
        "accessed": "2026-05-27",
        "note": "ModSecurity SecAuditEngine defaults and logged-event sizing"
      },
      {
        "type": "vendor-sizing",
        "url": "https://developers.cloudflare.com/logs/logpush/logpush-job/datasets/zone/http_requests/",
        "accessed": "2026-05-27",
        "note": "Cloudflare HTTP request logs (logpush dataset size)"
      }
    ],
    "related_uc_ids": [
      "10.5.1",
      "10.5.2",
      "10.5.3",
      "10.5.4",
      "10.5.5"
    ]
  },
  {
    "id": "dsa_sec_dlp",
    "name": "Data Loss Prevention (DLP)",
    "category": "Security Sources",
    "subcategory": "Data Protection",
    "description": "DLP policy violations, content inspection events, data exfiltration alerts",
    "vendor_examples": "Microsoft Purview, Symantec DLP, Digital Guardian, McAfee DLP, Forcepoint",
    "protocol": "Syslog / REST API",
    "ingest_method": "TA (API poll) or SC4S",
    "splunk_sourcetype": "symantec:dlp:incident, mcafee:dlp",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.6,
        "min": 0,
        "profilePresets": {
          "low": 0.2,
          "typical": 0.6,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1000,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.7.1",
      "10.7.2",
      "10.7.3",
      "10.12.1",
      "10.12.2"
    ]
  },
  {
    "id": "dsa_sec_ndr",
    "name": "NDR (Network Detection & Response)",
    "category": "Security Sources",
    "subcategory": "Network Detection",
    "description": "Network anomaly detection, behavioral analysis, encrypted traffic analytics",
    "vendor_examples": "Darktrace, Vectra AI, ExtraHop Reveal(x), Lastline, Corelight",
    "protocol": "Syslog / CEF / REST API",
    "ingest_method": "SC4S or TA (API poll)",
    "splunk_sourcetype": "darktrace:modelbreaches, vectra:detections",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1500,
        "min": 0,
        "profilePresets": {
          "low": 800,
          "typical": 1500,
          "high": 4000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.2.1",
      "10.2.2",
      "10.2.3",
      "5.7.1",
      "5.7.2"
    ]
  },
  {
    "id": "dsa_sec_uba",
    "name": "UBA / UEBA (User Behavior Analytics)",
    "category": "Security Sources",
    "subcategory": "Behavior Analytics",
    "description": "User behavior anomaly detection, insider threat analytics, risk scoring",
    "vendor_examples": "Splunk UBA, Exabeam, Securonix, Gurucul",
    "protocol": "REST API / Syslog",
    "ingest_method": "TA (API poll) or HEC",
    "splunk_sourcetype": "ueba:anomaly, ueba:risk",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.2,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1500,
        "min": 0,
        "profilePresets": {
          "low": 800,
          "typical": 1500,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.15.1",
      "10.15.2",
      "10.15.3",
      "10.15.4",
      "10.15.5"
    ]
  },
  {
    "id": "dsa_sec_pen_test",
    "name": "Penetration Testing Systems",
    "category": "Security Sources",
    "subcategory": "Security Testing",
    "description": "Pen test scan results, exploitation attempt logs, assessment findings",
    "vendor_examples": "Metasploit, Cobalt Strike, Burp Suite, Nmap, HackerOne",
    "protocol": "REST API / File",
    "ingest_method": "HEC or UF (file monitor)",
    "splunk_sourcetype": "pentest:results, nmap:scan",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1500,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1500,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.6.1",
      "10.6.2",
      "10.10.1",
      "10.10.2",
      "10.10.3"
    ]
  },
  {
    "id": "dsa_sec_soar",
    "name": "Block-, Allow-, Watch-Lists & SOAR",
    "category": "Security Sources",
    "subcategory": "Threat Lists & Automation",
    "description": "Curated lists of prohibited/allowed items, SOAR playbook execution logs",
    "vendor_examples": "Splunk SOAR, Palo Alto XSOAR, Swimlane, custom CSV lists",
    "protocol": "REST API / CSV / Lookup",
    "ingest_method": "HEC or lookup file",
    "splunk_sourcetype": "soar:playbook, threat_list",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.05,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.05,
          "high": 0.5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.7.1",
      "10.7.2",
      "10.7.3",
      "10.7.4",
      "10.7.5"
    ]
  },
  {
    "id": "dsa_sec_asset_identity",
    "name": "Asset & Identity Lists (CMDB / GRC)",
    "category": "Security Sources",
    "subcategory": "Asset Management",
    "description": "CMDB exports, asset inventories, identity directories for ES correlation",
    "vendor_examples": "ServiceNow CMDB, Active Directory, IT-GRC, Axonius, Lansweeper",
    "protocol": "REST API / CSV / LDAP",
    "ingest_method": "TA (API poll) or scheduled CSV import",
    "splunk_sourcetype": "asset_inventory, identity_manager",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.3,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.3,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.13.1",
      "10.13.2",
      "10.13.3",
      "10.13.4",
      "10.13.5"
    ]
  },
  {
    "id": "sec_physical",
    "name": "Physical Security (Access Control / Cameras)",
    "category": "Security Sources",
    "subcategory": "Physical Security",
    "description": "Badge access events, door controllers, video analytics alerts, perimeter sensors",
    "vendor_examples": "Lenel, HID, Genetec, Axis, Hikvision",
    "protocol": "Syslog / MQTT / CSV export",
    "ingest_method": "HEC or UF (file monitors)",
    "splunk_sourcetype": "acs:badge, camera:analytics",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.1,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.1,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "15.3.30",
      "15.3.34",
      "15.3.38",
      "15.3.39",
      "15.3.40"
    ]
  },
  {
    "id": "it_windows",
    "name": "Windows Server (Security / System logs)",
    "category": "IT Systems & Hardware",
    "subcategory": "Operating Systems",
    "description": "Windows Security, System, and Application event logs including logon, process, and policy events",
    "vendor_examples": "Windows Server 2019/2022",
    "protocol": "Windows Event Log (WEL)",
    "ingest_method": "Universal Forwarder",
    "splunk_sourcetype": "WinEventLog:Security, WinEventLog:System",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Windows endpoints",
        "unit": "hosts",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 25,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "audit_policy",
        "label": "Audit policy",
        "type": "enum",
        "default": "default",
        "options": [
          {
            "value": "default",
            "label": "Default (Security + System)"
          },
          {
            "value": "advanced",
            "label": "Advanced audit policy"
          },
          {
            "value": "advanced+ps-transcript",
            "label": "Advanced + PowerShell transcript (10–40x volume)"
          }
        ]
      }
    ],
    "compute": "it_windows_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/742",
        "accessed": "2026-05-27",
        "note": "Splunk Add-on for Microsoft Windows — default WinEventLog inputs"
      },
      {
        "type": "lantern",
        "url": "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Windows_Logging",
        "accessed": "2026-05-27",
        "note": "Splunk Lantern Windows logging sizing patterns"
      }
    ],
    "related_uc_ids": [
      "1.2.1",
      "1.2.4",
      "1.2.6",
      "1.2.8",
      "1.2.9"
    ]
  },
  {
    "id": "it_windows_dc",
    "name": "Windows Domain Controller",
    "category": "IT Systems & Hardware",
    "subcategory": "Operating Systems",
    "description": "Active Directory domain controller — authentication, replication, group policy, DNS logs",
    "vendor_examples": "Windows Server 2019/2022 (DC role)",
    "protocol": "Windows Event Log (WEL)",
    "ingest_method": "Universal Forwarder",
    "splunk_sourcetype": "WinEventLog:Security, WinEventLog:Directory Service",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "users_authenticated_per_hour",
        "label": "Users authenticated per hour",
        "unit": "auths/h",
        "type": "number",
        "default": 5000,
        "min": 0,
        "max": 10000000,
        "profilePresets": {
          "low": 500,
          "typical": 5000,
          "high": 50000
        }
      },
      {
        "id": "audit_logon_level",
        "label": "Audit Logon level",
        "type": "enum",
        "default": "success+failure",
        "options": [
          {
            "value": "success-only",
            "label": "Success only"
          },
          {
            "value": "success+failure",
            "label": "Success + Failure (+50% events)"
          }
        ]
      }
    ],
    "compute": "it_windows_dc_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/742",
        "accessed": "2026-05-27",
        "note": "Splunk Add-on for Microsoft Windows — 4624/4625/4768/4769 inputs"
      },
      {
        "type": "lantern",
        "url": "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Active_Directory_Monitoring",
        "accessed": "2026-05-27",
        "note": "Splunk Lantern Active Directory monitoring sizing"
      }
    ],
    "related_uc_ids": [
      "1.2.1",
      "1.2.4",
      "1.2.6",
      "9.1.1",
      "9.1.2"
    ]
  },
  {
    "id": "it_linux",
    "name": "Linux Server (syslog / auth)",
    "category": "IT Systems & Hardware",
    "subcategory": "Operating Systems",
    "description": "Linux system logs — auth, kern, daemon, cron, and application logs",
    "vendor_examples": "RHEL, Ubuntu, CentOS, SLES",
    "protocol": "Syslog / journald",
    "ingest_method": "Universal Forwarder or SC4S",
    "splunk_sourcetype": "linux_secure, syslog",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Linux endpoints",
        "unit": "hosts",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 25,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "auditd_enabled",
        "label": "auditd enabled",
        "type": "enum",
        "default": "no",
        "options": [
          {
            "value": "yes",
            "label": "Yes"
          },
          {
            "value": "no",
            "label": "No (syslog only)"
          }
        ]
      },
      {
        "id": "auditd_ruleset_size",
        "label": "auditd ruleset",
        "type": "enum",
        "default": "cis",
        "options": [
          {
            "value": "minimal",
            "label": "Minimal (~0.5 EPS/host)"
          },
          {
            "value": "cis",
            "label": "CIS hardened (~2 EPS/host)"
          },
          {
            "value": "full",
            "label": "Full (~8 EPS/host)"
          }
        ],
        "help": "Only applies when auditd is enabled."
      }
    ],
    "compute": "it_linux_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/833",
        "accessed": "2026-05-27",
        "note": "Splunk Add-on for Unix and Linux — default sourcetypes"
      },
      {
        "type": "lantern",
        "url": "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Linux_Endpoint_Monitoring",
        "accessed": "2026-05-27",
        "note": "Splunk Lantern Linux endpoint monitoring sizing"
      },
      {
        "type": "vendor-blog",
        "url": "https://github.com/splunk/splunk-connect-for-syslog",
        "accessed": "2026-05-27",
        "note": "SC4S reference configurations for Linux syslog ingestion"
      }
    ],
    "related_uc_ids": [
      "1.1.1",
      "1.1.2",
      "1.1.12",
      "1.1.18",
      "1.1.20"
    ]
  },
  {
    "id": "it_dns",
    "name": "DNS Server (Query Logs)",
    "category": "IT Systems & Hardware",
    "subcategory": "Network Services",
    "description": "DNS query and response logs for internal resolution and security analytics",
    "vendor_examples": "Windows DNS, BIND, Infoblox, Cisco Umbrella",
    "protocol": "File / Syslog / API",
    "ingest_method": "Universal Forwarder or SC4S",
    "splunk_sourcetype": "dns, MSAD:NT6:DNS",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 200,
        "min": 0,
        "profilePresets": {
          "low": 10,
          "typical": 200,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 250,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 250,
          "high": 500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.6.1",
      "5.6.2",
      "5.6.4",
      "5.6.8",
      "1.2.15"
    ]
  },
  {
    "id": "it_dhcp",
    "name": "DHCP Server",
    "category": "IT Systems & Hardware",
    "subcategory": "Network Services",
    "description": "IP address lease events — discover, offer, request, acknowledge, release",
    "vendor_examples": "Windows DHCP, ISC DHCP, Infoblox",
    "protocol": "File / Syslog",
    "ingest_method": "Universal Forwarder or SC4S",
    "splunk_sourcetype": "DhcpSrvLog, dhcpd",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 20,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 20,
          "high": 200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.6.1",
      "5.6.2",
      "5.6.4",
      "1.2.15"
    ]
  },
  {
    "id": "it_vmware",
    "name": "VMware vSphere / ESXi",
    "category": "IT Systems & Hardware",
    "subcategory": "Virtualization",
    "description": "Hypervisor task and event logs — VM operations, performance metrics, alarms",
    "vendor_examples": "vCenter 7.x/8.x, ESXi",
    "protocol": "REST API / Syslog",
    "ingest_method": "Splunk Add-on for VMware (API)",
    "splunk_sourcetype": "vmware:vclog, vmware:inv:vm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 15,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 15,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "2.1.1",
      "2.1.2",
      "2.1.11",
      "2.1.14",
      "2.1.21"
    ]
  },
  {
    "id": "it_backup",
    "name": "Backup Systems",
    "category": "IT Systems & Hardware",
    "subcategory": "Data Protection",
    "description": "Backup job status, success/failure, storage utilization, and compliance reports",
    "vendor_examples": "Veeam, Commvault, Veritas NetBackup, Cohesity",
    "protocol": "File / REST API",
    "ingest_method": "UF (file monitors) or TA (API)",
    "splunk_sourcetype": "veeam:backup, commvault:job",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.1,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.1,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 3000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 3000,
          "high": 10000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "6.3.1",
      "6.3.2",
      "6.3.3",
      "6.3.4",
      "6.3.5"
    ]
  },
  {
    "id": "it_proxy",
    "name": "Web Proxy / Secure Web Gateway",
    "category": "IT Systems & Hardware",
    "subcategory": "Network Services",
    "description": "HTTP/HTTPS request logs — URL, user, action, content type, threat category",
    "vendor_examples": "Zscaler, Cisco WSA, Symantec ProxySG, McAfee Web Gateway",
    "protocol": "Syslog / API / File",
    "ingest_method": "SC4S or UF",
    "splunk_sourcetype": "zscalernss-web, bluecoat:proxysg:access:syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 200,
        "min": 0,
        "profilePresets": {
          "low": 10,
          "typical": 200,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1500,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 1500,
          "high": 3500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.5.1",
      "10.5.2",
      "10.5.3",
      "8.1.1",
      "8.1.2"
    ]
  },
  {
    "id": "it_email",
    "name": "Email Security Gateway",
    "category": "IT Systems & Hardware",
    "subcategory": "Network Services",
    "description": "Email metadata — sender, recipient, subject, action, spam/malware verdict",
    "vendor_examples": "Proofpoint, Mimecast, Microsoft Exchange/O365, Cisco Email Security",
    "protocol": "REST API / Syslog",
    "ingest_method": "Splunk TA (API) or SC4S",
    "splunk_sourcetype": "proofpoint:pps:messagelog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 10,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 2000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 2000,
          "high": 20000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.4.1",
      "10.4.2",
      "10.4.3",
      "11.1.1",
      "11.1.2"
    ]
  },
  {
    "id": "dsa_it_cloud_iaas",
    "name": "Cloud IaaS (AWS / Azure / GCP)",
    "category": "IT Systems & Hardware",
    "subcategory": "Cloud Infrastructure",
    "description": "Infrastructure-as-a-Service logs — CloudTrail, Activity Log, VPC Flow, Audit Logs",
    "vendor_examples": "AWS, Microsoft Azure, Google Cloud Platform, Oracle Cloud",
    "protocol": "REST API / S3 / Event Hub",
    "ingest_method": "TA (Splunk Add-on for AWS/Azure/GCP)",
    "splunk_sourcetype": "aws:cloudtrail, azure:aad:signin, google:gcp:pubsub:message",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "monthly_api_calls",
        "label": "Monthly API calls",
        "unit": "calls",
        "type": "number",
        "default": 1000000,
        "min": 0,
        "max": 1000000000000,
        "profilePresets": {
          "low": 100000,
          "typical": 1000000,
          "high": 1000000000
        }
      },
      {
        "id": "data_event_pct",
        "label": "Data-plane events",
        "unit": "%",
        "type": "number",
        "default": 5,
        "min": 0,
        "max": 100,
        "profilePresets": {
          "low": 0,
          "typical": 5,
          "high": 30
        },
        "help": "Percentage of total events that are S3/Storage/BigQuery data-plane (~4x larger than management events)."
      }
    ],
    "compute": "dsa_it_cloud_iaas_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.1,
      "tsidx_overhead_typical": 0.25,
      "filterable_fraction_typical": 0.2
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-pricing.html",
        "accessed": "2026-05-27",
        "note": "AWS CloudTrail pricing & sizing — management + data event ratios"
      },
      {
        "type": "vendor-sizing",
        "url": "https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log",
        "accessed": "2026-05-27",
        "note": "Azure Monitor Activity log volumes"
      },
      {
        "type": "vendor-sizing",
        "url": "https://cloud.google.com/logging/docs/audit",
        "accessed": "2026-05-27",
        "note": "GCP Cloud Audit logs — admin/data/system event sizing"
      }
    ],
    "related_uc_ids": [
      "4.1.1",
      "4.1.2",
      "4.2.1",
      "4.2.2",
      "4.3.1"
    ]
  },
  {
    "id": "dsa_it_cloud_paas",
    "name": "Cloud PaaS (Serverless / Containers)",
    "category": "IT Systems & Hardware",
    "subcategory": "Cloud Infrastructure",
    "description": "Platform-as-a-Service logs — Lambda, Azure Functions, Cloud Run, Container logs",
    "vendor_examples": "AWS Lambda, Azure Functions, Google Cloud Run, Heroku, Kubernetes",
    "protocol": "REST API / CloudWatch / Log Analytics",
    "ingest_method": "TA (API poll) or HEC",
    "splunk_sourcetype": "aws:cloudwatch:logs, azure:monitor:logs",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "4.1.1",
      "4.2.1",
      "4.3.1",
      "4.5.1",
      "4.5.2"
    ]
  },
  {
    "id": "dsa_it_cloud_saas",
    "name": "Cloud SaaS (General)",
    "category": "IT Systems & Hardware",
    "subcategory": "Cloud SaaS",
    "description": "SaaS application audit and activity logs — user actions, admin changes, data access",
    "vendor_examples": "Salesforce, ServiceNow, Workday, Box, Dropbox, Slack, Zoom",
    "protocol": "REST API / Webhook",
    "ingest_method": "TA (API poll) or HEC (webhook)",
    "splunk_sourcetype": "salesforce:loginHistory, servicenow:incident",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 700,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 700,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "4.4.1",
      "4.4.2",
      "4.4.3",
      "11.1.1",
      "11.2.1"
    ]
  },
  {
    "id": "dsa_it_office365",
    "name": "Office 365 / Microsoft 365",
    "category": "IT Systems & Hardware",
    "subcategory": "Cloud SaaS",
    "description": "M365 audit logs — Exchange, SharePoint, OneDrive, Teams activity, Azure AD sign-ins",
    "vendor_examples": "Microsoft 365, G-Suite",
    "protocol": "REST API (Management Activity API)",
    "ingest_method": "Splunk Add-on for Microsoft 365",
    "splunk_sourcetype": "o365:management:activity, ms:aad:signin",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "seats",
        "label": "Licensed seats",
        "unit": "users",
        "type": "number",
        "default": 100,
        "min": 0,
        "max": 10000000,
        "profilePresets": {
          "low": 25,
          "typical": 100,
          "high": 10000
        }
      },
      {
        "id": "tier",
        "label": "M365 license tier",
        "type": "enum",
        "default": "e3",
        "options": [
          {
            "value": "e3",
            "label": "E3 (Unified Audit Log base)"
          },
          {
            "value": "e5",
            "label": "E5 (+ Defender XDR + ATP audit)"
          }
        ]
      }
    ],
    "compute": "dsa_it_office365_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://learn.microsoft.com/en-us/purview/audit-log-activities",
        "accessed": "2026-05-27",
        "note": "Microsoft Purview Unified Audit Log activities reference (seat × tier volumes)"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/4055",
        "accessed": "2026-05-27",
        "note": "Splunk Add-on for Microsoft Office 365 — Unified Audit Log defaults"
      }
    ],
    "related_uc_ids": [
      "11.1.1",
      "11.1.2",
      "11.1.3",
      "11.1.4",
      "11.1.5"
    ]
  },
  {
    "id": "dsa_it_crm",
    "name": "CRM (Salesforce / Dynamics)",
    "category": "IT Systems & Hardware",
    "subcategory": "Cloud SaaS",
    "description": "CRM platform audit logs — login activity, record changes, API calls",
    "vendor_examples": "Salesforce, Microsoft Dynamics 365, HubSpot",
    "protocol": "REST API",
    "ingest_method": "Splunk Add-on for Salesforce",
    "splunk_sourcetype": "sfdc:logfile, sfdc:loginHistory",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 50,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.06,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.06,
          "high": 0.2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.1.3",
      "23.1.4"
    ]
  },
  {
    "id": "dsa_it_sso",
    "name": "SSO / IAM (Okta / Ping / Azure AD)",
    "category": "IT Systems & Hardware",
    "subcategory": "Identity & Access",
    "description": "Single sign-on authentication, MFA events, provisioning, directory sync logs",
    "vendor_examples": "Okta, Ping Identity, Azure AD, OneLogin, Auth0",
    "protocol": "REST API / Webhook",
    "ingest_method": "Splunk Add-on for Okta / TA",
    "splunk_sourcetype": "OktaIM2:log, ping:audit",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "daily_active_users",
        "label": "Daily active users",
        "unit": "users",
        "type": "number",
        "default": 1000,
        "min": 0,
        "max": 10000000,
        "profilePresets": {
          "low": 100,
          "typical": 1000,
          "high": 100000
        }
      },
      {
        "id": "mfa_enabled",
        "label": "MFA enabled",
        "type": "enum",
        "default": "yes",
        "options": [
          {
            "value": "yes",
            "label": "Yes (~12 events/user/day)"
          },
          {
            "value": "no",
            "label": "No (~6 events/user/day)"
          }
        ]
      }
    ],
    "compute": "dsa_it_sso_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://developer.okta.com/docs/reference/api/system-log/",
        "accessed": "2026-05-27",
        "note": "Okta System Log API — per-user event volumes"
      },
      {
        "type": "vendor-sizing",
        "url": "https://docs.pingidentity.com/r/en-us/pingfederate-121/help_pingfederate-administrators-reference-guide",
        "accessed": "2026-05-27",
        "note": "PingFederate audit log reference"
      },
      {
        "type": "vendor-sizing",
        "url": "https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-sign-ins",
        "accessed": "2026-05-27",
        "note": "Microsoft Entra ID sign-in log sizing (interactive + non-interactive)"
      }
    ],
    "related_uc_ids": [
      "9.3.1",
      "9.3.2",
      "9.3.3",
      "9.3.4",
      "9.3.5"
    ]
  },
  {
    "id": "dsa_it_storage",
    "name": "Storage Arrays (SAN / NAS)",
    "category": "IT Systems & Hardware",
    "subcategory": "Storage",
    "description": "Enterprise storage performance logs, access audits, IOPS metrics, health alerts",
    "vendor_examples": "EMC VNX/Unity, NetApp ONTAP, Pure Storage, HPE 3PAR, Dell PowerStore",
    "protocol": "Syslog / REST API / SNMP",
    "ingest_method": "TA (API poll) or SC4S",
    "splunk_sourcetype": "emc:vnx, netapp:ontap:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 3,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "6.1.1",
      "6.1.2",
      "6.1.3",
      "6.2.1",
      "6.2.2"
    ]
  },
  {
    "id": "dsa_it_desktop",
    "name": "Desktops / Workstations",
    "category": "IT Systems & Hardware",
    "subcategory": "Endpoints",
    "description": "Endpoint OS event logs, antivirus, patch status, application logs",
    "vendor_examples": "Windows 10/11, macOS, Linux desktops",
    "protocol": "WinEventLog / Syslog",
    "ingest_method": "Universal Forwarder (UF)",
    "splunk_sourcetype": "WinEventLog:Security, syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 50,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.12,
        "min": 0,
        "profilePresets": {
          "low": 0.02,
          "typical": 0.12,
          "high": 0.5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "1.3.1",
      "1.3.2",
      "1.3.3",
      "2.5.1",
      "2.5.2"
    ]
  },
  {
    "id": "dsa_it_database",
    "name": "Database Instances",
    "category": "IT Systems & Hardware",
    "subcategory": "Databases",
    "description": "Database audit logs, performance metrics, query logs, error logs",
    "vendor_examples": "Oracle, SQL Server, MySQL, PostgreSQL, MongoDB, MariaDB",
    "protocol": "DB Connect / Syslog / File",
    "ingest_method": "Splunk DB Connect or UF (file monitor)",
    "splunk_sourcetype": "oracle:audit, mssql:audit, mysql:error",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "transactions_per_sec",
        "label": "Database transactions per second",
        "unit": "tps",
        "type": "number",
        "default": 100,
        "min": 0,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 100,
          "high": 10000
        }
      },
      {
        "id": "audit_level",
        "label": "Audit level",
        "type": "enum",
        "default": "dml-only",
        "options": [
          {
            "value": "dml-only",
            "label": "DML only (~1% logged)"
          },
          {
            "value": "dml+ddl",
            "label": "DML + DDL (~5% logged)"
          },
          {
            "value": "full+select",
            "label": "Full + SELECT (every txn)"
          }
        ]
      }
    ],
    "compute": "dsa_it_database_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/auditing-overview.html",
        "accessed": "2026-05-27",
        "note": "Oracle Unified Audit volume reference"
      },
      {
        "type": "vendor-sizing",
        "url": "https://learn.microsoft.com/en-us/sql/relational-databases/extended-events/extended-events",
        "accessed": "2026-05-27",
        "note": "Microsoft SQL Server Extended Events sizing"
      },
      {
        "type": "vendor-blog",
        "url": "https://github.com/pgaudit/pgaudit",
        "accessed": "2026-05-27",
        "note": "PostgreSQL pgAudit reference and event density"
      }
    ],
    "related_uc_ids": [
      "7.1.1",
      "7.1.2",
      "7.1.3",
      "7.2.1",
      "7.2.2"
    ]
  },
  {
    "id": "dsa_it_webserver",
    "name": "Web Servers",
    "category": "IT Systems & Hardware",
    "subcategory": "Application Infrastructure",
    "description": "HTTP access logs, error logs, SSL handshake logs from web servers",
    "vendor_examples": "Apache, Nginx, IIS, Caddy, LiteSpeed",
    "protocol": "File / Syslog",
    "ingest_method": "Universal Forwarder (UF)",
    "splunk_sourcetype": "access_combined, iis, nginx:access",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "requests_per_sec",
        "label": "HTTP requests per second",
        "unit": "rps",
        "type": "number",
        "default": 100,
        "min": 0,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 100,
          "high": 10000
        }
      },
      {
        "id": "log_format",
        "label": "Access-log format",
        "type": "enum",
        "default": "combined",
        "options": [
          {
            "value": "combined",
            "label": "Apache combined / nginx default (~350 B)"
          },
          {
            "value": "combined+vhost",
            "label": "Combined + vhost (~450 B)"
          },
          {
            "value": "json-rich",
            "label": "JSON rich (~1100 B)"
          }
        ]
      }
    ],
    "compute": "dsa_it_webserver_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.1,
      "tsidx_overhead_typical": 0.3,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "rfc",
        "url": "https://httpd.apache.org/docs/2.4/logs.html",
        "accessed": "2026-05-27",
        "note": "Apache mod_log_config combined log format reference"
      },
      {
        "type": "vendor-blog",
        "url": "https://nginx.org/en/docs/http/ngx_http_log_module.html",
        "accessed": "2026-05-27",
        "note": "nginx ngx_http_log_module default access log format"
      },
      {
        "type": "vendor-blog",
        "url": "https://learn.microsoft.com/en-us/iis/configuration/system.applicationhost/sites/site/logfile/",
        "accessed": "2026-05-27",
        "note": "IIS W3C extended log format reference"
      }
    ],
    "related_uc_ids": [
      "8.1.1",
      "8.1.2",
      "8.1.3",
      "8.1.4",
      "8.1.5"
    ]
  },
  {
    "id": "dsa_it_appserver",
    "name": "Application Servers",
    "category": "IT Systems & Hardware",
    "subcategory": "Application Infrastructure",
    "description": "Application runtime logs — JVM metrics, deployment events, thread dumps, error stacks",
    "vendor_examples": "Tomcat, WebSphere, WebLogic, JBoss/WildFly, .NET IIS, Node.js",
    "protocol": "File / JMX / Syslog",
    "ingest_method": "Universal Forwarder (UF) or HEC",
    "splunk_sourcetype": "tomcat:access, websphere:activity",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 2,
          "typical": 3,
          "high": 30
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 3,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1000,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "8.2.1",
      "8.2.2",
      "8.2.3",
      "8.2.4",
      "8.2.5"
    ]
  },
  {
    "id": "dsa_it_middleware",
    "name": "Middleware / Integration Services",
    "category": "IT Systems & Hardware",
    "subcategory": "Application Infrastructure",
    "description": "Message queue logs, ESB transactions, API gateway logs, integration events",
    "vendor_examples": "MuleSoft, TIBCO, IBM MQ, RabbitMQ, Kafka, Software AG webMethods",
    "protocol": "File / JMS / REST API",
    "ingest_method": "UF or HEC",
    "splunk_sourcetype": "mq:queue, kafka:broker, esb:transaction",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 3,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 1000,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "8.3.1",
      "8.3.2",
      "8.3.3",
      "8.4.1",
      "8.4.2"
    ]
  },
  {
    "id": "dsa_it_splunk_internal",
    "name": "Splunk Internal Logs (_internal)",
    "category": "IT Systems & Hardware",
    "subcategory": "Splunk Platform",
    "description": "Splunk platform operational logs — metrics, audit, scheduler, search performance",
    "vendor_examples": "Splunk Indexers, Search Heads, Cluster Masters, Universal Forwarders",
    "protocol": "Internal",
    "ingest_method": "Splunk internal monitoring console",
    "splunk_sourcetype": "splunkd, splunk_resource_usage, scheduler",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.5,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "13.1.1",
      "13.1.2",
      "13.1.3",
      "13.2.1",
      "13.2.2"
    ]
  },
  {
    "id": "dsa_it_apm",
    "name": "APM (Application Performance Monitoring)",
    "category": "IT Systems & Hardware",
    "subcategory": "Observability",
    "description": "Application traces, distributed tracing spans, service metrics, error analytics",
    "vendor_examples": "Splunk APM, Dynatrace, New Relic, AppDynamics, Datadog APM",
    "protocol": "REST API / OTLP",
    "ingest_method": "TA (API poll) or HEC / OTEL Collector",
    "splunk_sourcetype": "apm:span, newrelic:apm, dynatrace:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.5,
          "high": 8
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.1.3",
      "8.7.1",
      "8.7.2"
    ]
  },
  {
    "id": "dsa_it_sap",
    "name": "SAP / ERP (Enterprise Systems)",
    "category": "IT Systems & Hardware",
    "subcategory": "Enterprise Applications",
    "description": "SAP application logs, security audit log, change documents, batch job logs",
    "vendor_examples": "SAP NetWeaver, SAP S/4HANA, SAP Business One",
    "protocol": "RFC / REST API / File",
    "ingest_method": "Splunk Add-on for SAP",
    "splunk_sourcetype": "sap:security_audit, sap:change_document",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 3,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1000,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.2.1",
      "23.2.2"
    ]
  },
  {
    "id": "dsa_it_pam",
    "name": "PAM / Privileged Access Management",
    "category": "IT Systems & Hardware",
    "subcategory": "Identity & Access",
    "description": "Privileged session recordings, credential checkout, access request and approval logs",
    "vendor_examples": "CyberArk, BeyondTrust, Thycotic, Delinea, HashiCorp Vault",
    "protocol": "Syslog / REST API",
    "ingest_method": "TA (API poll) or SC4S",
    "splunk_sourcetype": "cyberark:epv:cef, beyondtrust:session",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "9.4.1",
      "9.4.2",
      "9.4.3",
      "9.4.4",
      "9.4.5"
    ]
  },
  {
    "id": "dsa_it_telephone",
    "name": "Telephone / PBX Systems",
    "category": "IT Systems & Hardware",
    "subcategory": "Unified Communications",
    "description": "PBX call detail records, call routing, trunk utilization, voicemail logs",
    "vendor_examples": "Cisco UCM, Avaya, Mitel, Genesys, Shoretel, Twilio",
    "protocol": "Syslog / CDR file / REST API",
    "ingest_method": "UF (file monitor) or SC4S",
    "splunk_sourcetype": "cisco:ucm:cdr, avaya:cdr",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 3,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "11.3.1",
      "11.3.2",
      "11.3.3",
      "11.3.4",
      "11.3.5"
    ]
  },
  {
    "id": "dsa_it_voip",
    "name": "VoIP / SIP Systems",
    "category": "IT Systems & Hardware",
    "subcategory": "Unified Communications",
    "description": "SIP signaling logs, RTP quality metrics, VoIP call records",
    "vendor_examples": "Asterisk, FreeSWITCH, Cisco CUBE, Twilio, RingCentral",
    "protocol": "Syslog / CDR file",
    "ingest_method": "UF (file monitor) or SC4S",
    "splunk_sourcetype": "asterisk:cdr, sip:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2.5,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "11.3.1",
      "11.3.2",
      "5.12.1",
      "5.12.2",
      "5.12.3"
    ]
  },
  {
    "id": "dsa_it_uxm",
    "name": "User Experience Monitoring (DEM)",
    "category": "IT Systems & Hardware",
    "subcategory": "Observability",
    "description": "Digital experience monitoring — synthetic tests, real user monitoring, endpoint performance",
    "vendor_examples": "Splunk RUM, ThousandEyes, Nexthink, Aternity, Lakeside",
    "protocol": "REST API / Agent",
    "ingest_method": "TA (API poll) or HEC",
    "splunk_sourcetype": "thousandeyes:test, nexthink:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2.5,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.9.1",
      "5.9.2",
      "5.9.6",
      "23.1.1",
      "23.1.2"
    ]
  },
  {
    "id": "dsa_it_cicd",
    "name": "CI/CD & Build Systems",
    "category": "IT Systems & Hardware",
    "subcategory": "DevOps",
    "description": "Build logs, pipeline status, deployment events, test results, code scanning",
    "vendor_examples": "Jenkins, GitHub Actions, GitLab CI, Bamboo, TeamCity, Travis CI",
    "protocol": "REST API / Webhook / File",
    "ingest_method": "HEC (webhook) or UF",
    "splunk_sourcetype": "jenkins:build, github:webhook",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1500,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1500,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "12.1.1",
      "12.1.2",
      "12.1.3",
      "12.2.1",
      "12.2.2"
    ]
  },
  {
    "id": "dsa_it_config_mgmt",
    "name": "Configuration & Deployment Tools",
    "category": "IT Systems & Hardware",
    "subcategory": "DevOps",
    "description": "Infrastructure automation — config runs, compliance reports, deployment status",
    "vendor_examples": "Ansible, Puppet, Chef, Salt, Terraform, Docker",
    "protocol": "REST API / Syslog / File",
    "ingest_method": "UF or HEC",
    "splunk_sourcetype": "puppet:report, ansible:event, terraform:plan",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.2,
          "typical": 1,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 4000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "12.3.1",
      "12.3.2",
      "12.3.3",
      "12.3.4"
    ]
  },
  {
    "id": "dsa_it_qa_test",
    "name": "QA & Test Automation Systems",
    "category": "IT Systems & Hardware",
    "subcategory": "DevOps",
    "description": "Test execution results, code quality analysis, automated test suite output",
    "vendor_examples": "SonarQube, Selenium, PyTest, JUnit, Cucumber, Robot Framework",
    "protocol": "REST API / File / Webhook",
    "ingest_method": "HEC or UF (file monitor)",
    "splunk_sourcetype": "sonarqube:project, junit:results",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1500,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1500,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "12.1.1",
      "12.2.1",
      "12.2.2",
      "12.3.1"
    ]
  },
  {
    "id": "dsa_it_print",
    "name": "Print Servers",
    "category": "IT Systems & Hardware",
    "subcategory": "Shared Services",
    "description": "Print job logs, queue status, user print activity, printer health",
    "vendor_examples": "Windows Print Server, CUPS, PaperCut, PrinterLogic",
    "protocol": "WinEventLog / Syslog / File",
    "ingest_method": "Universal Forwarder (UF)",
    "splunk_sourcetype": "WinEventLog:PrintService, cups:access",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.2,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "1.2.1",
      "1.2.4",
      "1.1.1"
    ]
  },
  {
    "id": "dsa_it_mobile",
    "name": "Mobile Devices / MDM",
    "category": "IT Systems & Hardware",
    "subcategory": "Endpoints",
    "description": "Mobile device management events, app crash logs, compliance checks, policy violations",
    "vendor_examples": "Microsoft Intune, VMware Workspace ONE, Jamf, MobileIron, SOTI",
    "protocol": "REST API",
    "ingest_method": "TA (API poll)",
    "splunk_sourcetype": "intune:device, jamf:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 50,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.06,
        "min": 0,
        "profilePresets": {
          "low": 0.005,
          "typical": 0.06,
          "high": 0.2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "9.6.1",
      "9.6.2",
      "9.6.3",
      "9.6.4",
      "9.6.5"
    ]
  },
  {
    "id": "dsa_it_emr",
    "name": "Electronic Medical Record (EMR/EHR)",
    "category": "IT Systems & Hardware",
    "subcategory": "Healthcare",
    "description": "Clinical system audit logs, patient record access, order entry, HL7/FHIR messages",
    "vendor_examples": "Epic, Cerner, MEDITECH, Allscripts, athenahealth",
    "protocol": "Syslog / HL7 / FHIR / REST API",
    "ingest_method": "TA (API poll) or HEC",
    "splunk_sourcetype": "epic:audit, hl7:message",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.5,
          "high": 8
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.2.1",
      "23.2.2",
      "23.2.3",
      "23.2.4"
    ]
  },
  {
    "id": "ot_scada",
    "name": "SCADA System (Alarms & Events)",
    "category": "OT System Sources",
    "subcategory": "SCADA / HMI",
    "description": "SCADA alarm journal, operator actions, setpoint changes, and system events",
    "vendor_examples": "Ignition (Inductive Automation), Wonderware InTouch, GE iFIX, Siemens WinCC",
    "protocol": "ODBC / File export / Syslog / OPC-UA",
    "ingest_method": "DB Connect, UF (file monitors), or HEC",
    "splunk_sourcetype": "scada:alarm, scada:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 5,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "ot_historian",
    "name": "Process Historian (Aggregated Exports)",
    "category": "OT System Sources",
    "subcategory": "Historians",
    "description": "Time-series process data — temperature, pressure, flow, level, setpoints (aggregated/sampled)",
    "vendor_examples": "OSIsoft PI, Honeywell PHD, Wonderware Historian, GE Proficy, AVEVA",
    "protocol": "PI Web API / ODBC / CSV export",
    "ingest_method": "DB Connect, scheduled scripts → HEC",
    "splunk_sourcetype": "historian:metric, pi:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 50,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 50,
          "high": 500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 50,
          "typical": 300,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.2.16",
      "14.2.25",
      "14.2.26"
    ]
  },
  {
    "id": "ot_dcs",
    "name": "DCS (Distributed Control System)",
    "category": "OT System Sources",
    "subcategory": "Control Systems",
    "description": "DCS alarms, operator actions, sequence events, controller diagnostics",
    "vendor_examples": "Honeywell Experion, ABB 800xA, Emerson DeltaV, Yokogawa CENTUM",
    "protocol": "Syslog / Proprietary export / OPC-UA",
    "ingest_method": "UF (file monitors), HEC, or DB Connect",
    "splunk_sourcetype": "dcs:alarm, dcs:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 10,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 1200,
          "high": 4000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.2.25",
      "14.2.26"
    ]
  },
  {
    "id": "ot_mes",
    "name": "MES / Manufacturing Execution System",
    "category": "OT System Sources",
    "subcategory": "Production Systems",
    "description": "Production orders, batch records, quality checks, OEE calculations, material tracking",
    "vendor_examples": "Siemens Opcenter, Rockwell FactoryTalk, SAP MES, AVEVA MES",
    "protocol": "REST API / ODBC / File export",
    "ingest_method": "DB Connect, TA (API), or UF",
    "splunk_sourcetype": "mes:production, mes:quality",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.5,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 3000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 3000,
          "high": 10000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.2.16",
      "14.2.25",
      "14.2.26",
      "14.5.1"
    ]
  },
  {
    "id": "ot_erp",
    "name": "ERP System (Production / Maintenance)",
    "category": "OT System Sources",
    "subcategory": "Production Systems",
    "description": "Work orders, maintenance requests, inventory transactions, production planning events",
    "vendor_examples": "SAP S/4HANA, Oracle EBS, Microsoft Dynamics, Infor",
    "protocol": "REST API / ODBC / RFC/BAPI",
    "ingest_method": "DB Connect or TA (API) → HEC",
    "splunk_sourcetype": "erp:workorder, erp:maintenance",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.2,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.2,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 2500,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 2500,
          "high": 8000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.5.1",
      "14.5.2",
      "14.5.3",
      "23.2.1",
      "23.2.2"
    ]
  },
  {
    "id": "ot_hmi",
    "name": "HMI Stations",
    "category": "OT System Sources",
    "subcategory": "SCADA / HMI",
    "description": "Operator workstation logs — login/logout, screen navigation, alarm acknowledgments",
    "vendor_examples": "Ignition Vision, Wonderware InTouch, Siemens WinCC, GE CIMPLICITY",
    "protocol": "Syslog / File export",
    "ingest_method": "UF (file monitors) or SC4S",
    "splunk_sourcetype": "hmi:audit, hmi:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.5,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "dsa_ot_firewall",
    "name": "OT-Specific Firewall (Industrial)",
    "category": "OT System Sources",
    "subcategory": "OT Network Security",
    "description": "Industrial firewall/DPI logs — Purdue level segmentation, protocol-aware filtering",
    "vendor_examples": "Tofino, Fortinet OT, Palo Alto IoT Security, Cisco Industrial Network Director",
    "protocol": "Syslog / CEF",
    "ingest_method": "SC4S or HEC",
    "splunk_sourcetype": "tofino:firewall, pan:ot_security",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.20",
      "5.2.1",
      "10.14.1"
    ]
  },
  {
    "id": "dsa_ot_historian_access",
    "name": "Historian Access / Audit Logs",
    "category": "OT System Sources",
    "subcategory": "Historians",
    "description": "User access logs for process historian systems — login, query, data export activity",
    "vendor_examples": "OSIsoft PI (AVEVA), Wonderware Historian, GE Proficy, Honeywell PHD",
    "protocol": "Syslog / SQL / File",
    "ingest_method": "UF or DB Connect",
    "splunk_sourcetype": "pi:audit, wonderware:access",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 3,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.2.16",
      "14.2.25",
      "14.2.26"
    ]
  },
  {
    "id": "dsa_ot_asset_mgmt",
    "name": "OT Asset Management (CMMS)",
    "category": "OT System Sources",
    "subcategory": "Asset Management",
    "description": "Computerized maintenance management — work orders, preventive maintenance, asset lifecycle",
    "vendor_examples": "IBM Maximo, Infor EAM, SAP PM, Oracle EAM, eMaint, Fiix",
    "protocol": "REST API / DB Connect / File",
    "ingest_method": "TA (API poll) or DB Connect",
    "splunk_sourcetype": "maximo:workorder, sap:pm_notification",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.6,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.6,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1000,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.1",
      "14.1.8",
      "14.1.9",
      "14.1.10",
      "14.1.11"
    ]
  },
  {
    "id": "dsa_ot_server_mgmt",
    "name": "Server Management (BMC / IPMI)",
    "category": "OT System Sources",
    "subcategory": "Infrastructure Management",
    "description": "Out-of-band server management — hardware health, thermal, power, remote console events",
    "vendor_examples": "HP iLO, Dell iDRAC, Lenovo XClarity, Supermicro IPMI",
    "protocol": "SNMP / REST API / Syslog",
    "ingest_method": "SC4S or TA (API poll)",
    "splunk_sourcetype": "ilo:health, idrac:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.25,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.25,
          "high": 1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.1",
      "14.1.10",
      "14.1.14",
      "1.1.1",
      "1.2.1"
    ]
  },
  {
    "id": "dsa_ot_remote_access",
    "name": "Secure Remote Access / Screen Sharing",
    "category": "OT System Sources",
    "subcategory": "Remote Access",
    "description": "Remote desktop session logs — connection events, session recordings metadata, user actions",
    "vendor_examples": "VNC, Dameware, TeamViewer, Bomgar/BeyondTrust, Cisco Secure Equipment Access",
    "protocol": "Syslog / File / REST API",
    "ingest_method": "UF or HEC",
    "splunk_sourcetype": "vnc:connection, teamviewer:session",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.3,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.3,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.5",
      "14.9.20",
      "9.4.1"
    ]
  },
  {
    "id": "dsa_ot_file_transfer",
    "name": "Secure File Transfer (OT)",
    "category": "OT System Sources",
    "subcategory": "Data Transfer",
    "description": "Managed file transfer logs between IT/OT zones — firmware updates, recipe transfers, batch data",
    "vendor_examples": "Honeywell Nexus, SFTP, Globalscape EFT, GoAnywhere, Axway",
    "protocol": "Syslog / File",
    "ingest_method": "UF (file monitor)",
    "splunk_sourcetype": "sftp:audit, mft:transfer",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 2,
          "typical": 3,
          "high": 30
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.05,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.05,
          "high": 0.5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.20",
      "6.4.1"
    ]
  },
  {
    "id": "dsa_ot_scada_security",
    "name": "SCADA Security Solutions",
    "category": "OT System Sources",
    "subcategory": "OT Network Security",
    "description": "Dedicated SCADA/ICS security platforms — anomaly detection, protocol validation, change tracking",
    "vendor_examples": "Industrial Defender, Honeywell Forge, Schneider StruxureWare, Fortinet OT",
    "protocol": "Syslog / REST API / CEF",
    "ingest_method": "SC4S or TA (API poll)",
    "splunk_sourcetype": "industrial_defender:event, struxureware:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.5,
          "high": 8
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 1000,
          "high": 2500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.5",
      "14.9.20",
      "10.14.1"
    ]
  },
  {
    "id": "net_switch",
    "name": "Managed Switch (OT/IT)",
    "category": "Network Sources",
    "subcategory": "Switching",
    "description": "Switch syslog — port up/down, spanning tree, MAC learning, security violations",
    "vendor_examples": "Cisco IE3x00, Cisco Catalyst, Stratix, Hirschmann, Moxa",
    "protocol": "Syslog",
    "ingest_method": "SC4S → HEC",
    "splunk_sourcetype": "cisco:ios, syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 20,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 10,
          "typical": 20,
          "high": 200
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.5,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 600
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.1.1",
      "5.1.6",
      "5.1.13",
      "5.1.22",
      "5.1.36"
    ]
  },
  {
    "id": "net_router",
    "name": "Router",
    "category": "Network Sources",
    "subcategory": "Routing",
    "description": "Router syslog — routing protocol events, interface status, ACL violations, NAT logs",
    "vendor_examples": "Cisco ISR, Cisco IR1101, Cisco ASR, Juniper MX/SRX",
    "protocol": "Syslog",
    "ingest_method": "SC4S → HEC",
    "splunk_sourcetype": "cisco:ios, syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 350,
        "min": 0,
        "profilePresets": {
          "low": 120,
          "typical": 350,
          "high": 700
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.1.4",
      "5.1.5",
      "5.1.16",
      "5.1.35"
    ]
  },
  {
    "id": "net_wireless",
    "name": "Wireless LAN Controller / Access Points",
    "category": "Network Sources",
    "subcategory": "Wireless",
    "description": "Wi-Fi events — client association, roaming, authentication, rogue AP detection",
    "vendor_examples": "Cisco WLC, Cisco Catalyst 9800, Aruba, Meraki",
    "protocol": "Syslog / API",
    "ingest_method": "SC4S or TA (API)",
    "splunk_sourcetype": "cisco:wlc, meraki:events",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 20,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 20,
          "high": 200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.4.2",
      "5.4.7",
      "5.4.10",
      "5.4.12",
      "5.4.20"
    ]
  },
  {
    "id": "net_sdwan",
    "name": "SD-WAN",
    "category": "Network Sources",
    "subcategory": "WAN",
    "description": "SD-WAN overlay events — tunnel status, SLA metrics, policy changes, application routing",
    "vendor_examples": "Cisco Catalyst SD-WAN (Viptela), Fortinet SD-WAN, VMware VeloCloud",
    "protocol": "Syslog / REST API",
    "ingest_method": "SC4S or TA (API) → HEC",
    "splunk_sourcetype": "cisco:sdwan:syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.5.1",
      "5.5.4",
      "5.5.18",
      "5.9.29"
    ]
  },
  {
    "id": "net_netflow",
    "name": "NetFlow / IPFIX / sFlow",
    "category": "Network Sources",
    "subcategory": "Flow Data",
    "description": "Network flow records — source/dest IP, ports, bytes, packets, protocol, duration",
    "vendor_examples": "Cisco NetFlow v9, IPFIX, sFlow (HP/Arista/Juniper)",
    "protocol": "UDP (flow export)",
    "ingest_method": "Flow collector → UF/HEC, or Splunk Stream",
    "splunk_sourcetype": "netflow, sflow",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "aggregated_flows_per_sec",
        "label": "Aggregated flows per second",
        "unit": "fps",
        "type": "number",
        "default": 1000,
        "min": 0,
        "max": 10000000,
        "profilePresets": {
          "low": 100,
          "typical": 1000,
          "high": 50000
        },
        "help": "Flow rate emitted toward the collector AFTER aggregation (typical 10:1 dedup at exporter)."
      },
      {
        "id": "format",
        "label": "Flow format",
        "type": "enum",
        "default": "netflow-v9",
        "options": [
          {
            "value": "netflow-v5",
            "label": "NetFlow v5 (~100 B)"
          },
          {
            "value": "netflow-v9",
            "label": "NetFlow v9 (~150 B)"
          },
          {
            "value": "ipfix",
            "label": "IPFIX (~180 B)"
          },
          {
            "value": "sflow",
            "label": "sFlow (~200 B)"
          }
        ]
      }
    ],
    "compute": "net_netflow_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.1,
      "tsidx_overhead_typical": 0.15,
      "filterable_fraction_typical": 0.15
    },
    "citations": [
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/489",
        "accessed": "2026-05-27",
        "note": "Splunk_TA_netflow / NetFlow Logic Splunk Add-on — collector defaults"
      },
      {
        "type": "vendor-sizing",
        "url": "https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/fnetflow/configuration/15-mt/fnf-15-mt-book/cfg-fnflow-data-expts.html",
        "accessed": "2026-05-27",
        "note": "Cisco Flexible NetFlow data exporter sizing"
      }
    ],
    "related_uc_ids": [
      "5.7.1",
      "5.7.2",
      "5.7.7",
      "5.7.8",
      "5.7.10"
    ]
  },
  {
    "id": "net_meraki",
    "name": "Cisco Meraki (Cloud Networking)",
    "category": "Network Sources",
    "subcategory": "Cloud-Managed Networking",
    "description": "Meraki syslog and API events — network events, security events, air marshal, location analytics",
    "vendor_examples": "Meraki MX, MS, MR, MV, MT",
    "protocol": "Syslog / REST API / Webhooks",
    "ingest_method": "SC4S (syslog) or TA (API) → HEC",
    "splunk_sourcetype": "meraki:events, meraki:api",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "devices",
        "label": "Meraki devices (MX/MR/MS/MV)",
        "unit": "devices",
        "type": "number",
        "default": 50,
        "min": 0,
        "max": 100000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 1000
        }
      },
      {
        "id": "syslog_features",
        "label": "Enabled syslog features",
        "type": "enum",
        "default": "events+flows",
        "options": [
          {
            "value": "events-only",
            "label": "Events only"
          },
          {
            "value": "events+flows",
            "label": "Events + flows"
          },
          {
            "value": "events+flows+url",
            "label": "Events + flows + URL/content filter"
          }
        ]
      }
    ],
    "compute": "net_meraki_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.12,
      "tsidx_overhead_typical": 0.3,
      "filterable_fraction_typical": 0.15
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://documentation.meraki.com/General_Administration/Other_Topics/Syslog_Server_Overview_and_Configuration",
        "accessed": "2026-05-27",
        "note": "Meraki syslog server configuration and per-feature event mix"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/3018",
        "accessed": "2026-05-27",
        "note": "Splunk Add-on for Cisco Meraki — Dashboard API + syslog parsers"
      }
    ],
    "related_uc_ids": [
      "5.1.36",
      "5.2.19",
      "5.4.12",
      "5.8.2",
      "14.1.15"
    ]
  },
  {
    "id": "dsa_net_vpn",
    "name": "VPN Concentrators / Remote Access",
    "category": "Network Sources",
    "subcategory": "Remote Access",
    "description": "VPN tunnel logs — connections, disconnections, authentication, tunnel stats",
    "vendor_examples": "Cisco AnyConnect, Palo Alto GlobalProtect, Fortinet SSL-VPN, Citrix NetScaler",
    "protocol": "Syslog / RADIUS",
    "ingest_method": "SC4S or TA",
    "splunk_sourcetype": "cisco:asa, pan:globalprotect",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "concurrent_sessions",
        "label": "Concurrent VPN sessions",
        "unit": "sessions",
        "type": "number",
        "default": 100,
        "min": 0,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 100,
          "high": 10000
        }
      },
      {
        "id": "disconnect_alerts_enabled",
        "label": "Disconnect / heartbeat alerts",
        "type": "enum",
        "default": "yes",
        "options": [
          {
            "value": "yes",
            "label": "Yes (+heartbeat / tear-down events)"
          },
          {
            "value": "no",
            "label": "No (connect / disconnect only)"
          }
        ]
      }
    ],
    "compute": "dsa_net_vpn_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 1.8
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.05
    },
    "citations": [
      {
        "type": "vendor-sizing",
        "url": "https://www.cisco.com/c/en/us/td/docs/security/vpn_client/anyconnect/anyconnect49/administration/guide/b_AnyConnect_Administrator_Guide_4-9.html",
        "accessed": "2026-05-27",
        "note": "Cisco AnyConnect VPN logging reference"
      },
      {
        "type": "vendor-blog",
        "url": "https://community.openvpn.net/openvpn/wiki/HOWTO#Logging",
        "accessed": "2026-05-27",
        "note": "OpenVPN logging defaults"
      },
      {
        "type": "vendor-sizing",
        "url": "https://help.ivanti.com/ps/help/en_US/PCS/9.1R12/AG/troubleshooting/logging.htm",
        "accessed": "2026-05-27",
        "note": "Ivanti/Pulse Connect Secure logging guide"
      }
    ],
    "related_uc_ids": [
      "5.2.1",
      "5.2.3",
      "9.4.1",
      "17.2.9",
      "17.3.23"
    ]
  },
  {
    "id": "dsa_net_loadbalancer",
    "name": "Load Balancers / ADC",
    "category": "Network Sources",
    "subcategory": "Application Delivery",
    "description": "Load balancer traffic logs, health checks, SSL offload, connection pool metrics",
    "vendor_examples": "F5 BIG-IP, Citrix NetScaler/ADC, HAProxy, Nginx Plus, AWS ALB/NLB",
    "protocol": "Syslog / REST API / iRules",
    "ingest_method": "SC4S or TA (iControl REST)",
    "splunk_sourcetype": "f5:bigip:syslog, citrix:netscaler:syslog",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "requests_per_sec",
        "label": "Requests per second",
        "unit": "rps",
        "type": "number",
        "default": 100,
        "min": 0,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 100,
          "high": 10000
        }
      },
      {
        "id": "log_level",
        "label": "Log verbosity",
        "type": "enum",
        "default": "summary",
        "options": [
          {
            "value": "denied-only",
            "label": "Denied only (~0.5%)"
          },
          {
            "value": "summary",
            "label": "Summary (~10%)"
          },
          {
            "value": "full-detail",
            "label": "Full detail (every request)"
          }
        ]
      }
    ],
    "compute": "dsa_net_loadbalancer_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.12,
      "tsidx_overhead_typical": 0.3,
      "filterable_fraction_typical": 0.2
    },
    "citations": [
      {
        "type": "vendor-blog",
        "url": "https://my.f5.com/manage/s/article/K12131",
        "accessed": "2026-05-27",
        "note": "F5 BIG-IP logging best practices"
      },
      {
        "type": "vendor-blog",
        "url": "https://docs.netscaler.com/en-us/citrix-adc/current-release/system/audit-logging.html",
        "accessed": "2026-05-27",
        "note": "Citrix NetScaler ADC audit logging configuration"
      },
      {
        "type": "vendor-blog",
        "url": "https://avinetworks.com/docs/latest/log-settings/",
        "accessed": "2026-05-27",
        "note": "VMware NSX Advanced LB (AVI) logging settings"
      }
    ],
    "related_uc_ids": [
      "5.3.1",
      "5.3.2",
      "5.3.3",
      "5.3.4",
      "5.3.5"
    ]
  },
  {
    "id": "dsa_net_ddos",
    "name": "DDoS Protection",
    "category": "Network Sources",
    "subcategory": "DDoS Mitigation",
    "description": "DDoS mitigation logs — attack detection, scrubbing center events, traffic analysis",
    "vendor_examples": "Akamai, Cloudflare, Arbor/Netscout, A10 Networks, Corero, Radware",
    "protocol": "REST API / Syslog / CEF",
    "ingest_method": "TA (API poll) or SC4S",
    "splunk_sourcetype": "akamai:siem, cloudflare:firewall",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.2.1",
      "5.2.3",
      "10.2.1",
      "10.2.2"
    ]
  },
  {
    "id": "dsa_net_nac",
    "name": "Network Access Control (NAC)",
    "category": "Network Sources",
    "subcategory": "Access Control",
    "description": "802.1X authentication, posture assessment, guest access, BYOD onboarding events",
    "vendor_examples": "Aruba ClearPass, Cisco ISE, Forescout, Portnox, Extreme NAC",
    "protocol": "Syslog / RADIUS / REST API",
    "ingest_method": "SC4S or TA",
    "splunk_sourcetype": "clearpass:event, forescout:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 3,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 1000,
          "high": 2500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "17.1.1",
      "17.1.3",
      "17.1.7",
      "17.1.13"
    ]
  },
  {
    "id": "dsa_net_ldap",
    "name": "LDAP Directory Services",
    "category": "Network Sources",
    "subcategory": "Directory Services",
    "description": "LDAP query logs, directory modifications, bind attempts, schema changes",
    "vendor_examples": "OpenLDAP, Microsoft AD LDS, 389 Directory, Oracle Directory Server",
    "protocol": "Syslog / File",
    "ingest_method": "UF (file monitor)",
    "splunk_sourcetype": "openldap:access, ldap:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "9.2.1",
      "9.2.2",
      "9.2.3",
      "9.2.4",
      "9.2.5"
    ]
  },
  {
    "id": "dsa_net_ftp",
    "name": "FTP / SFTP Servers",
    "category": "Network Sources",
    "subcategory": "File Transfer",
    "description": "File transfer protocol logs — connections, transfers, authentication, directory operations",
    "vendor_examples": "vsftpd, ProFTPD, OpenSSH SFTP, FileZilla Server, WS_FTP",
    "protocol": "Syslog / File",
    "ingest_method": "UF (file monitor)",
    "splunk_sourcetype": "vsftpd, proftpd, sshd",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 3,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "6.4.1",
      "6.4.2",
      "6.4.3",
      "6.4.4"
    ]
  },
  {
    "id": "dsa_net_dpi",
    "name": "Deep Packet Inspection / Network Forensics",
    "category": "Network Sources",
    "subcategory": "Network Visibility",
    "description": "Full packet capture metadata, protocol analysis, application identification",
    "vendor_examples": "Zeek (Bro), Splunk Stream, Corelight, Moloch/Arkime, PCAP",
    "protocol": "Syslog / JSON / File",
    "ingest_method": "UF or HEC",
    "splunk_sourcetype": "bro:conn:json, stream:http",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.7.1",
      "5.7.2",
      "5.7.7",
      "5.7.8"
    ]
  },
  {
    "id": "dsa_net_snmp_mgmt",
    "name": "SNMP Management Systems",
    "category": "Network Sources",
    "subcategory": "Network Management",
    "description": "SNMP trap receivers, NMS polling results, network performance monitoring alerts",
    "vendor_examples": "LogicMonitor, SolarWinds, ManageEngine, PRTG, Nagios, LibreNMS",
    "protocol": "SNMP traps / Syslog / REST API",
    "ingest_method": "SC4S or TA",
    "splunk_sourcetype": "snmp:trap, solarwinds:alert",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.5,
          "high": 8
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.8.1",
      "5.8.2",
      "5.8.3",
      "14.1.10",
      "14.1.11"
    ]
  },
  {
    "id": "ot_plc_modbus",
    "name": "PLC via Modbus TCP",
    "category": "OT Hardware & Sensors",
    "subcategory": "PLCs",
    "description": "Register/coil data polled from PLCs — analog measurements, digital status, setpoints",
    "vendor_examples": "Siemens S7, Allen-Bradley ControlLogix/CompactLogix, Schneider Modicon",
    "protocol": "Modbus TCP",
    "ingest_method": "Edge Hub / Cisco EI → HEC",
    "splunk_sourcetype": "modbus:register, edge_hub:modbus",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 200,
        "min": 0,
        "profilePresets": {
          "low": 80,
          "typical": 200,
          "high": 500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.3.34"
    ]
  },
  {
    "id": "ot_plc_opcua",
    "name": "PLC / Controller via OPC-UA",
    "category": "OT Hardware & Sensors",
    "subcategory": "PLCs",
    "description": "OPC-UA subscription data — process variables, alarms, events from OPC-UA servers",
    "vendor_examples": "Siemens S7-1500 (built-in), Kepware, Ignition OPC-UA, Matrikon, Unified Automation",
    "protocol": "OPC-UA",
    "ingest_method": "Edge Hub / Cisco EI → HEC",
    "splunk_sourcetype": "opcua:metric, edge_hub:opcua",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 2,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.9",
      "14.2.8",
      "14.3.31",
      "14.3.35"
    ]
  },
  {
    "id": "ot_rtu",
    "name": "RTU (Remote Terminal Unit)",
    "category": "OT Hardware & Sensors",
    "subcategory": "Remote Telemetry",
    "description": "Remote telemetry — field measurements, status, alarms from remote/unmanned sites",
    "vendor_examples": "Schneider Easergy, ABB RTU500, Siemens SICAM, Emerson ROC",
    "protocol": "DNP3 / Modbus / Serial-to-IP",
    "ingest_method": "Edge Gateway → HEC",
    "splunk_sourcetype": "rtu:telemetry",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.1,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.1,
          "high": 1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 350,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 350,
          "high": 700
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.1.10"
    ]
  },
  {
    "id": "ot_iot_sensor",
    "name": "IoT Sensors / Gateways",
    "category": "OT Hardware & Sensors",
    "subcategory": "IoT / Edge",
    "description": "Environmental and process sensors — temperature, humidity, vibration, energy, pressure via gateways",
    "vendor_examples": "Cisco Meraki MT, LoRaWAN gateways, Monnit, Banner Engineering, IFM",
    "protocol": "MQTT / HTTP / LoRaWAN / Zigbee",
    "ingest_method": "Edge Hub or MQTT TA → HEC",
    "splunk_sourcetype": "iot:sensor, mqtt:message",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 25,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.05,
        "min": 0,
        "profilePresets": {
          "low": 0.001,
          "typical": 0.05,
          "high": 1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 250,
        "min": 0,
        "profilePresets": {
          "low": 80,
          "typical": 250,
          "high": 600
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.7",
      "14.3.24",
      "14.3.42"
    ]
  },
  {
    "id": "ot_mqtt",
    "name": "MQTT Broker (Topic Aggregation)",
    "category": "OT Hardware & Sensors",
    "subcategory": "Messaging",
    "description": "MQTT message broker — aggregated topic data from multiple publishers (sensors, PLCs, edge devices)",
    "vendor_examples": "HiveMQ, Mosquitto, EMQX, AWS IoT Core, Azure IoT Hub",
    "protocol": "MQTT",
    "ingest_method": "MQTT TA or Edge Hub → HEC",
    "splunk_sourcetype": "mqtt:message",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 50,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 50,
          "high": 500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 500,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.5",
      "14.3.24",
      "14.3.33",
      "14.3.42"
    ]
  },
  {
    "id": "ot_bacnet",
    "name": "BACnet Devices (Building Automation)",
    "category": "OT Hardware & Sensors",
    "subcategory": "Building Automation",
    "description": "BACnet/IP change-of-value (COV) and polled data — HVAC, lighting, energy meters, fire/life safety",
    "vendor_examples": "Johnson Controls, Honeywell, Schneider EcoStruxure, Tridium Niagara",
    "protocol": "BACnet/IP",
    "ingest_method": "Edge Hub → HEC",
    "splunk_sourcetype": "bacnet:point, edge_hub:bacnet",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 20,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 10,
          "typical": 20,
          "high": 200
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.2,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.2,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 350,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 350,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.1",
      "14.1.45",
      "14.1.46",
      "14.3.24"
    ]
  },
  {
    "id": "ot_edge_hub",
    "name": "Splunk Edge Hub",
    "category": "OT Hardware & Sensors",
    "subcategory": "Edge Computing",
    "description": "Splunk Edge Hub — multi-protocol edge collector for Modbus, OPC-UA, MQTT, BACnet, SNMP",
    "vendor_examples": "Splunk Edge Hub (OTI platform)",
    "protocol": "Multiple (Modbus/OPC-UA/MQTT/BACnet/SNMP)",
    "ingest_method": "Native → HEC (via OTI Datastreamer)",
    "splunk_sourcetype": "edge_hub:modbus, edge_hub:opcua, edge_hub:mqtt",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 20,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 20,
          "high": 200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.7",
      "14.3.34",
      "14.3.42"
    ]
  },
  {
    "id": "ot_cisco_ei",
    "name": "Cisco Edge Intelligence",
    "category": "OT Hardware & Sensors",
    "subcategory": "Edge Computing",
    "description": "Cisco EI — industrial data orchestration from OT protocols to Splunk via Data Rules",
    "vendor_examples": "Cisco IR1101, IR829, IC3000, Catalyst IE3x00",
    "protocol": "Modbus / OPC-UA / MQTT / Serial / NTCIP",
    "ingest_method": "HTTPS/MQTT → HEC",
    "splunk_sourcetype": "cisco:ei:telemetry",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 2,
          "typical": 3,
          "high": 30
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 5,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.7",
      "14.3.34",
      "14.3.42"
    ]
  },
  {
    "id": "ot_env_sensor",
    "name": "Environmental Monitoring Sensors",
    "category": "OT Hardware & Sensors",
    "subcategory": "Environmental",
    "description": "Facility environment — temperature, humidity, air quality, water leak, power quality, vibration",
    "vendor_examples": "APC NetBotz, Meraki MT, Monnit, Sensaphone, Fluke",
    "protocol": "SNMP / MQTT / HTTP",
    "ingest_method": "Edge Hub or SNMP TA → HEC",
    "splunk_sourcetype": "env:sensor, snmp:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 20,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 10,
          "typical": 20,
          "high": 200
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.03,
        "min": 0,
        "profilePresets": {
          "low": 0.003,
          "typical": 0.03,
          "high": 0.5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 200,
        "min": 0,
        "profilePresets": {
          "low": 80,
          "typical": 200,
          "high": 500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.24",
      "14.1.45",
      "14.1.46"
    ]
  },
  {
    "id": "ot_energy_meter",
    "name": "Power / Energy Meters",
    "category": "OT Hardware & Sensors",
    "subcategory": "Energy Management",
    "description": "Electrical metering — voltage, current, power factor, energy consumption, harmonics",
    "vendor_examples": "Schneider PM8000, Siemens PAC, Eaton, Dent, Carlo Gavazzi",
    "protocol": "Modbus TCP / BACnet / SNMP",
    "ingest_method": "Edge Hub → HEC",
    "splunk_sourcetype": "energy:meter, modbus:register",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.2,
        "min": 0,
        "profilePresets": {
          "low": 0.03,
          "typical": 0.2,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.24",
      "14.5.1",
      "14.5.2"
    ]
  },
  {
    "id": "ot_safety_system",
    "name": "Safety Instrumented System (SIS)",
    "category": "OT Hardware & Sensors",
    "subcategory": "Safety Systems",
    "description": "SIS diagnostic and trip events — proof tests, demand events, override status, bypass logs",
    "vendor_examples": "Honeywell SIS (Safety Manager), Schneider Triconex, Siemens S7-F, Yokogawa ProSafe-RS",
    "protocol": "Syslog / Proprietary / OPC-UA",
    "ingest_method": "UF (file monitors) or HEC",
    "splunk_sourcetype": "sis:event, sis:diagnostic",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.05,
        "min": 0,
        "profilePresets": {
          "low": 0.001,
          "typical": 0.05,
          "high": 1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 800,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.15",
      "14.2.25",
      "14.9.1"
    ]
  },
  {
    "id": "ot_vibration",
    "name": "Vibration / Condition Monitoring",
    "category": "OT Hardware & Sensors",
    "subcategory": "Predictive Maintenance",
    "description": "Machine health — vibration spectra, bearing analysis, temperature trends for rotating equipment",
    "vendor_examples": "SKF, Emerson AMS, Bently Nevada, Fluke 3563, Banner QM42VT",
    "protocol": "MQTT / HTTP / Modbus",
    "ingest_method": "Edge Hub or MQTT TA → HEC",
    "splunk_sourcetype": "vibration:metric, condition:monitor",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.1,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.1,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 400,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.4.1",
      "14.4.2",
      "14.4.3",
      "14.4.4",
      "14.4.5"
    ]
  },
  {
    "id": "proto_modbus",
    "name": "Modbus TCP / RTU",
    "category": "Protocols",
    "subcategory": "Industrial Polling",
    "description": "Register/coil polling from PLCs, VFDs, meters, RTUs — the most widespread OT protocol",
    "vendor_examples": "Siemens, Allen-Bradley, Schneider, ABB, Wago, Beckhoff",
    "protocol": "Modbus TCP / Modbus RTU",
    "ingest_method": "Edge Hub / Cisco EI → HEC",
    "splunk_sourcetype": "modbus:register, edge_hub:modbus",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Registers polled",
        "unit": "tags",
        "type": "number",
        "default": 500,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 100,
          "typical": 500,
          "high": 5000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling interval",
        "unit": "seconds",
        "type": "enum",
        "default": 30,
        "options": [
          {
            "value": 1,
            "label": "1 s (control-loop)"
          },
          {
            "value": 5,
            "label": "5 s (fast metrics)"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s (typical historian)"
          },
          {
            "value": 60,
            "label": "60 s (slow trending)"
          },
          {
            "value": 300,
            "label": "5 min (batch reporting)"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Gateway value-change filter",
        "unit": "fraction",
        "type": "number",
        "default": 0.4,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.4,
          "high": 0.8
        },
        "help": "Fraction of polls dropped when the register value hasn't changed."
      }
    ],
    "compute": "proto_modbus_v1",
    "uncertainty": {
      "low": 0.7,
      "typical": 1,
      "high": 1.6
    },
    "realism": {
      "rawdata_compression_typical": 0.1,
      "tsidx_overhead_typical": 0.2,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "rfc",
        "url": "https://modbus.org/specs.php",
        "accessed": "2026-05-27",
        "note": "Modbus.org — Modbus TCP frame size and register data format"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/6048",
        "accessed": "2026-05-27",
        "note": "Splunk Edge Hub Connect for Modbus — default emission shape"
      }
    ],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32"
    ]
  },
  {
    "id": "proto_opcua",
    "name": "OPC UA",
    "category": "Protocols",
    "subcategory": "Industrial Interoperability",
    "description": "Secure subscription-based protocol for PLC/SCADA interoperability — modern replacement for OPC DA",
    "vendor_examples": "Siemens S7-1500, Kepware, Ignition, Matrikon, Unified Automation, Prosys",
    "protocol": "OPC UA (TCP binary / HTTPS)",
    "ingest_method": "Edge Hub / Cisco EI → HEC",
    "splunk_sourcetype": "opcua:metric, edge_hub:opcua",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Subscribed tags",
        "unit": "tags",
        "type": "number",
        "default": 500,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 100,
          "typical": 500,
          "high": 5000
        }
      },
      {
        "id": "publish_interval_ms",
        "label": "Publish interval",
        "unit": "ms",
        "type": "enum",
        "default": 1000,
        "options": [
          {
            "value": 100,
            "label": "100 ms (control-loop)"
          },
          {
            "value": 500,
            "label": "500 ms (fast metrics)"
          },
          {
            "value": 1000,
            "label": "1 s (typical historian)"
          },
          {
            "value": 5000,
            "label": "5 s (slow trending)"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Server-side deadband",
        "unit": "fraction",
        "type": "number",
        "default": 0.6,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0.2,
          "typical": 0.6,
          "high": 0.85
        },
        "help": "Fraction of publish slots filtered at the server (no change)."
      }
    ],
    "compute": "proto_opcua_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2.5
    },
    "realism": {
      "rawdata_compression_typical": 0.1,
      "tsidx_overhead_typical": 0.2,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "rfc",
        "url": "https://reference.opcfoundation.org/Core/Part4/v105/docs/",
        "accessed": "2026-05-27",
        "note": "OPC UA Part 4 services reference (subscription, deadband)"
      },
      {
        "type": "vendor-blog",
        "url": "https://documentation.unified-automation.com/uaserversdk/1.9.0/html/index.html",
        "accessed": "2026-05-27",
        "note": "Unified Automation OPC UA Server SDK performance notes"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/6049",
        "accessed": "2026-05-27",
        "note": "Splunk Edge Hub Connect for OPC UA — default subscription event shape"
      }
    ],
    "related_uc_ids": [
      "14.1.9",
      "14.2.8",
      "14.3.31",
      "14.3.35"
    ]
  },
  {
    "id": "proto_mqtt",
    "name": "MQTT",
    "category": "Protocols",
    "subcategory": "Pub/Sub Messaging",
    "description": "Lightweight pub/sub messaging for IoT telemetry, edge gateways, and cloud integration",
    "vendor_examples": "HiveMQ, Mosquitto, EMQX, AWS IoT Core, Azure IoT Hub",
    "protocol": "MQTT 3.1.1 / 5.0 (TCP/TLS)",
    "ingest_method": "MQTT TA / Edge Hub → HEC",
    "splunk_sourcetype": "mqtt:message",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "topic_count",
        "label": "Subscribed topics",
        "unit": "topics",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 100,
          "high": 10000
        }
      },
      {
        "id": "messages_per_topic_per_sec",
        "label": "Messages per topic per second",
        "unit": "msgs/s",
        "type": "number",
        "default": 1,
        "min": 0,
        "max": 1000,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "qos",
        "label": "QoS level",
        "type": "enum",
        "default": 0,
        "options": [
          {
            "value": 0,
            "label": "QoS 0 (fire-and-forget, ~250 B)"
          },
          {
            "value": 1,
            "label": "QoS 1 (at-least-once, ~280 B)"
          },
          {
            "value": 2,
            "label": "QoS 2 (exactly-once, ~310 B)"
          }
        ]
      }
    ],
    "compute": "proto_mqtt_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.12,
      "tsidx_overhead_typical": 0.25,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "rfc",
        "url": "https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html",
        "accessed": "2026-05-27",
        "note": "OASIS MQTT v5.0 spec — packet sizes and QoS semantics"
      },
      {
        "type": "vendor-blog",
        "url": "https://www.hivemq.com/docs/hivemq/4.30/user-guide/configuration.html",
        "accessed": "2026-05-27",
        "note": "HiveMQ broker default configuration and event sizes"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/6051",
        "accessed": "2026-05-27",
        "note": "Splunk Edge Hub Connect for MQTT"
      }
    ],
    "related_uc_ids": [
      "14.3.5",
      "14.3.24",
      "14.3.33"
    ]
  },
  {
    "id": "proto_snmp",
    "name": "SNMP (v2c / v3)",
    "category": "Protocols",
    "subcategory": "Network Management",
    "description": "OID-based device monitoring — UPS, switches, PDUs, RTUs, environmental sensors",
    "vendor_examples": "Cisco, APC, Eaton, Emerson, Net-SNMP, SNMP Informant",
    "protocol": "SNMP v2c / v3 (UDP)",
    "ingest_method": "Edge Hub / SNMP TA → HEC",
    "splunk_sourcetype": "snmp:metric, edge_hub:snmp",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "oid_count",
        "label": "Polled OIDs",
        "unit": "OIDs",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 25,
          "typical": 100,
          "high": 5000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling interval",
        "unit": "seconds",
        "type": "enum",
        "default": 60,
        "options": [
          {
            "value": 30,
            "label": "30 s (fast metrics)"
          },
          {
            "value": 60,
            "label": "60 s (typical)"
          },
          {
            "value": 300,
            "label": "5 min (trend)"
          }
        ]
      },
      {
        "id": "version",
        "label": "SNMP version",
        "type": "enum",
        "default": "v2c",
        "options": [
          {
            "value": "v2c",
            "label": "SNMPv2c (compact varbinds, ~120 B)"
          },
          {
            "value": "v3",
            "label": "SNMPv3 (+ auth/priv headers, ~180 B)"
          }
        ]
      }
    ],
    "compute": "proto_snmp_v1",
    "uncertainty": {
      "low": 0.6,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.1,
      "tsidx_overhead_typical": 0.2,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "rfc",
        "url": "https://datatracker.ietf.org/doc/html/rfc3411",
        "accessed": "2026-05-27",
        "note": "IETF RFC 3411 — SNMPv3 architecture (varbind framing)"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/5347",
        "accessed": "2026-05-27",
        "note": "Splunk Connect for SNMP — default poller emission rates"
      }
    ],
    "related_uc_ids": [
      "14.1.10",
      "14.1.11",
      "14.1.14",
      "5.8.3",
      "5.1.14"
    ]
  },
  {
    "id": "proto_bacnet",
    "name": "BACnet/IP",
    "category": "Protocols",
    "subcategory": "Building Automation",
    "description": "Building automation — HVAC, lighting, energy, fire/life safety, access control points",
    "vendor_examples": "Johnson Controls, Honeywell, Schneider EcoStruxure, Tridium Niagara, Distech",
    "protocol": "BACnet/IP (UDP)",
    "ingest_method": "Edge Hub → HEC",
    "splunk_sourcetype": "bacnet:point, edge_hub:bacnet",
    "calibration": "calibrated",
    "drivers": [
      {
        "id": "device_count",
        "label": "BACnet devices",
        "unit": "devices",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 10000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "polled_objects_per_device",
        "label": "Polled objects per device",
        "unit": "objects",
        "type": "number",
        "default": 20,
        "min": 1,
        "max": 1000,
        "profilePresets": {
          "low": 5,
          "typical": 20,
          "high": 100
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling interval",
        "unit": "seconds",
        "type": "enum",
        "default": 60,
        "options": [
          {
            "value": 10,
            "label": "10 s (fast HVAC loop)"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "60 s (typical building)"
          },
          {
            "value": 300,
            "label": "5 min (trend report)"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Gateway value-change filter",
        "unit": "fraction",
        "type": "number",
        "default": 0.6,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0.2,
          "typical": 0.6,
          "high": 0.85
        }
      }
    ],
    "compute": "proto_bacnet_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2.5
    },
    "realism": {
      "rawdata_compression_typical": 0.12,
      "tsidx_overhead_typical": 0.25,
      "filterable_fraction_typical": 0.1
    },
    "citations": [
      {
        "type": "rfc",
        "url": "https://www.ashrae.org/technical-resources/standards-and-guidelines/standards-addenda/standard-135-2020-addenda",
        "accessed": "2026-05-27",
        "note": "ASHRAE 135 (BACnet) standard — object types and property data sizes"
      },
      {
        "type": "vendor-blog",
        "url": "http://www.bacnet.org/Bibliography/index.html",
        "accessed": "2026-05-27",
        "note": "BACnet/IP object-property reference (BTL implementation guide)"
      },
      {
        "type": "splunkbase-ta",
        "url": "https://splunkbase.splunk.com/app/6050",
        "accessed": "2026-05-27",
        "note": "Splunk Edge Hub Connect for BACnet — default emission shape"
      }
    ],
    "related_uc_ids": [
      "14.1.1",
      "14.1.45",
      "14.1.46",
      "14.3.24"
    ]
  },
  {
    "id": "proto_ethernetip",
    "name": "EtherNet/IP (CIP)",
    "category": "Protocols",
    "subcategory": "Industrial Fieldbus",
    "description": "Rockwell/Allen-Bradley ecosystem — tag-based reads from ControlLogix and CompactLogix PLCs",
    "vendor_examples": "Rockwell Automation, Allen-Bradley, Molex, Phoenix Contact",
    "protocol": "EtherNet/IP (TCP/UDP)",
    "ingest_method": "OPC UA gateway → Edge Hub / HEC",
    "splunk_sourcetype": "cip:tag, opcua:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.1,
            "label": "0.1 s"
          },
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 350,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 350,
          "high": 680
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.9.1"
    ]
  },
  {
    "id": "proto_profinet",
    "name": "PROFINET",
    "category": "Protocols",
    "subcategory": "Industrial Fieldbus",
    "description": "Siemens-centric real-time industrial Ethernet — cyclic IO, alarms, diagnostics",
    "vendor_examples": "Siemens, Phoenix Contact, Weidmüller, Beckhoff, Festo",
    "protocol": "PROFINET (Ethernet, cyclic)",
    "ingest_method": "OPC UA gateway → Edge Hub / HEC",
    "splunk_sourcetype": "profinet:metric, opcua:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 360,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 360,
          "high": 700
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.9.1"
    ]
  },
  {
    "id": "proto_dnp3",
    "name": "DNP3",
    "category": "Protocols",
    "subcategory": "Utility / SCADA",
    "description": "Utility-grade SCADA protocol — classed events, time sync, secure auth (IEEE 1815)",
    "vendor_examples": "SEL, ABB, GE, Schneider, Siemens, Honeywell",
    "protocol": "DNP3 (TCP/Serial)",
    "ingest_method": "SCADA historian / OPC gateway → HEC",
    "splunk_sourcetype": "dnp3:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 200,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 40,
          "typical": 200,
          "high": 2000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 15,
        "options": [
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 15,
            "label": "15 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 120,
            "label": "2 min"
          },
          {
            "value": 300,
            "label": "5 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 320,
        "min": 0,
        "profilePresets": {
          "low": 140,
          "typical": 320,
          "high": 620
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.9.1"
    ]
  },
  {
    "id": "proto_iec61850",
    "name": "IEC 61850",
    "category": "Protocols",
    "subcategory": "Utility / Substation",
    "description": "Power substation automation — GOOSE fast exchange, MMS for reports/config, Sampled Values",
    "vendor_examples": "ABB, Siemens, GE, SEL, Schneider, Hitachi Energy",
    "protocol": "IEC 61850 MMS / GOOSE / SV",
    "ingest_method": "SCADA historian / OPC gateway → HEC",
    "splunk_sourcetype": "iec61850:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 10,
        "options": [
          {
            "value": 0.1,
            "label": "0.1 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 170,
          "typical": 400,
          "high": 850
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.9.1"
    ]
  },
  {
    "id": "proto_iec104",
    "name": "IEC 60870-5-104",
    "category": "Protocols",
    "subcategory": "Utility / SCADA",
    "description": "TCP-based telecontrol for power grids and water systems — ASDUs, timestamps, quality flags",
    "vendor_examples": "ABB, Siemens, GE, Schneider, Hitachi Energy",
    "protocol": "IEC 104 (TCP)",
    "ingest_method": "SCADA front-end / gateway → HEC",
    "splunk_sourcetype": "iec104:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 200,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 40,
          "typical": 200,
          "high": 2000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 30,
        "options": [
          {
            "value": 3,
            "label": "3 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 15,
            "label": "15 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 300,
            "label": "5 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 310,
        "min": 0,
        "profilePresets": {
          "low": 130,
          "typical": 310,
          "high": 600
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.9.1"
    ]
  },
  {
    "id": "proto_s7comm",
    "name": "S7comm / S7comm+",
    "category": "Protocols",
    "subcategory": "Industrial Fieldbus",
    "description": "Siemens S7 PLC protocol — variable access, DB reads, block operations, diagnostics",
    "vendor_examples": "Siemens S7-300, S7-400, S7-1200, S7-1500",
    "protocol": "S7comm (TCP/102)",
    "ingest_method": "OPC UA on PLC / gateway → HEC",
    "splunk_sourcetype": "s7:metric, opcua:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.2,
            "label": "0.2 s"
          },
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 330,
        "min": 0,
        "profilePresets": {
          "low": 140,
          "typical": 330,
          "high": 650
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.9.1"
    ]
  },
  {
    "id": "proto_hartip",
    "name": "HART-IP",
    "category": "Protocols",
    "subcategory": "Process Instrumentation",
    "description": "Smart instrument protocol — device variables, diagnostics, calibration from HART field instruments",
    "vendor_examples": "Emerson, Endress+Hauser, Honeywell, Yokogawa, VEGA",
    "protocol": "HART-IP (TCP/UDP)",
    "ingest_method": "OPC gateway / SCADA historian → HEC",
    "splunk_sourcetype": "hart:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 30,
        "options": [
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 300,
            "label": "5 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 340,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 340,
          "high": 680
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32",
      "14.4.1"
    ]
  },
  {
    "id": "proto_sparkplug",
    "name": "Sparkplug B (on MQTT)",
    "category": "Protocols",
    "subcategory": "Pub/Sub Messaging",
    "description": "MQTT-based OT convention with birth/death certificates, metric model, and state management",
    "vendor_examples": "Cirrus Link, Ignition, HiveMQ, EMQX, Chariot",
    "protocol": "Sparkplug B (MQTT)",
    "ingest_method": "MQTT TA / Edge Hub → HEC",
    "splunk_sourcetype": "sparkplug:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 420,
        "min": 0,
        "profilePresets": {
          "low": 180,
          "typical": 420,
          "high": 950
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.5",
      "14.3.24",
      "14.3.33",
      "14.3.42"
    ]
  },
  {
    "id": "proto_amqp",
    "name": "AMQP 1.0",
    "category": "Protocols",
    "subcategory": "Enterprise Messaging",
    "description": "Enterprise messaging protocol — Azure Event Hubs, RabbitMQ, IoT platform backplanes",
    "vendor_examples": "Azure Event Hubs, RabbitMQ, Apache Qpid, ActiveMQ",
    "protocol": "AMQP 1.0 (TCP/TLS)",
    "ingest_method": "Connector / scripted input → HEC",
    "splunk_sourcetype": "amqp:message",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 10,
        "options": [
          {
            "value": 0.1,
            "label": "0.1 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 380,
        "min": 0,
        "profilePresets": {
          "low": 160,
          "typical": 380,
          "high": 900
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "8.3.1",
      "8.3.2",
      "8.3.3",
      "14.3.33"
    ]
  },
  {
    "id": "proto_coap",
    "name": "CoAP",
    "category": "Protocols",
    "subcategory": "IoT Lightweight",
    "description": "UDP-based REST-like protocol for constrained IoT devices — observe/subscribe pattern",
    "vendor_examples": "Eclipse Californium, libcoap, Zephyr RTOS, Nordic Semi",
    "protocol": "CoAP (UDP)",
    "ingest_method": "Border router → MQTT/HTTP → HEC",
    "splunk_sourcetype": "coap:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 20,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 4,
          "typical": 20,
          "high": 200
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 60,
        "options": [
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 300,
            "label": "5 min"
          },
          {
            "value": 900,
            "label": "15 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 280,
        "min": 0,
        "profilePresets": {
          "low": 120,
          "typical": 280,
          "high": 550
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.24",
      "14.3.42"
    ]
  },
  {
    "id": "proto_mtconnect",
    "name": "MTConnect",
    "category": "Protocols",
    "subcategory": "Machine Tools / CNC",
    "description": "XML/HTTP streaming standard for machine tools — equipment metadata, samples, events, conditions",
    "vendor_examples": "Mazak, DMG Mori, Haas, Okuma, Fanuc, Mitsubishi",
    "protocol": "MTConnect (HTTP/XML)",
    "ingest_method": "Scripted input / gateway → HEC",
    "splunk_sourcetype": "mtconnect:sample",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.1,
            "label": "0.1 s"
          },
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 450,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 450,
          "high": 1100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.7",
      "14.2.12",
      "14.5.1",
      "14.5.2"
    ]
  },
  {
    "id": "proto_opcda",
    "name": "OPC DA (Classic)",
    "category": "Protocols",
    "subcategory": "Industrial Interoperability",
    "description": "Legacy Windows DCOM OPC — synchronous/async reads and subscriptions for SCADA/HMI",
    "vendor_examples": "Kepware, Matrikon, Honeywell, Wonderware, GE",
    "protocol": "OPC DA (DCOM)",
    "ingest_method": "DA→UA wrapper / OPC gateway → HEC",
    "splunk_sourcetype": "opcda:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 200,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 40,
          "typical": 200,
          "high": 2000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.1,
            "label": "0.1 s"
          },
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 340,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 340,
          "high": 700
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.9",
      "14.2.8",
      "14.3.31",
      "14.3.35"
    ]
  },
  {
    "id": "proto_ethercat",
    "name": "EtherCAT",
    "category": "Protocols",
    "subcategory": "Motion / Fieldbus",
    "description": "High-speed fieldbus for motion control — processing-on-the-fly Ethernet frames",
    "vendor_examples": "Beckhoff, Omron, Yaskawa, Mitsubishi, Bosch Rexroth",
    "protocol": "EtherCAT (Ethernet L2)",
    "ingest_method": "TwinCAT ADS / OPC UA → HEC",
    "splunk_sourcetype": "ethercat:metric, opcua:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 10,
        "options": [
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 360,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 360,
          "high": 720
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32"
    ]
  },
  {
    "id": "proto_lorawan",
    "name": "LoRa / LoRaWAN",
    "category": "Protocols",
    "subcategory": "LPWAN / IoT",
    "description": "Low-power wide-area network for remote assets — small uplink frames, long range",
    "vendor_examples": "Semtech, The Things Network, Chirpstack, Kerlink, MultiTech",
    "protocol": "LoRaWAN (RF/IP)",
    "ingest_method": "Network server → MQTT/HTTP webhook → HEC",
    "splunk_sourcetype": "lorawan:uplink",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 20,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 4,
          "typical": 20,
          "high": 200
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 300,
        "options": [
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 120,
            "label": "2 min"
          },
          {
            "value": 300,
            "label": "5 min"
          },
          {
            "value": 600,
            "label": "10 min"
          },
          {
            "value": 900,
            "label": "15 min"
          },
          {
            "value": 1800,
            "label": "30 min"
          },
          {
            "value": 3600,
            "label": "60 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 320,
        "min": 0,
        "profilePresets": {
          "low": 130,
          "typical": 320,
          "high": 600
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.24",
      "14.3.42"
    ]
  },
  {
    "id": "proto_knx",
    "name": "KNX / EIB",
    "category": "Protocols",
    "subcategory": "Building Automation",
    "description": "European building automation bus — group addresses for lighting, HVAC, shading, metering",
    "vendor_examples": "ABB, Schneider, Siemens, Hager, Gira, Jung",
    "protocol": "KNX/IP (Multicast/Tunnel)",
    "ingest_method": "KNX→IP gateway → MQTT/OPC → HEC",
    "splunk_sourcetype": "knx:telegram",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 60,
        "options": [
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 120,
            "label": "2 min"
          },
          {
            "value": 300,
            "label": "5 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 130,
          "typical": 300,
          "high": 560
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.1",
      "14.1.45",
      "14.1.46",
      "14.3.24"
    ]
  },
  {
    "id": "proto_profibus",
    "name": "PROFIBUS DP/PA",
    "category": "Protocols",
    "subcategory": "Legacy Fieldbus",
    "description": "Legacy fieldbus widely installed in process plants — master/slave cyclic IO, diagnostics",
    "vendor_examples": "Siemens, Endress+Hauser, Phoenix Contact, Pepperl+Fuchs",
    "protocol": "PROFIBUS DP/PA (RS-485)",
    "ingest_method": "OPC gateway / historian → HEC",
    "splunk_sourcetype": "profibus:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 10,
        "options": [
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 320,
        "min": 0,
        "profilePresets": {
          "low": 140,
          "typical": 320,
          "high": 600
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32"
    ]
  },
  {
    "id": "proto_cclink",
    "name": "CC-Link IE",
    "category": "Protocols",
    "subcategory": "Industrial Fieldbus",
    "description": "Mitsubishi-centric field network — deterministic cyclic IO, station diagnostics",
    "vendor_examples": "Mitsubishi, Cognex, Keyence, Yaskawa",
    "protocol": "CC-Link IE (Ethernet)",
    "ingest_method": "MC Protocol / OPC gateway → HEC",
    "splunk_sourcetype": "cclink:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 350,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 350,
          "high": 680
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32"
    ]
  },
  {
    "id": "proto_fins",
    "name": "FINS (Omron)",
    "category": "Protocols",
    "subcategory": "Industrial Fieldbus",
    "description": "Omron PLC protocol over Ethernet/serial — memory area reads, commands, diagnostics",
    "vendor_examples": "Omron CJ2, NJ/NX, CP1, CS1",
    "protocol": "FINS (UDP/TCP)",
    "ingest_method": "OPC gateway / Kepware → HEC",
    "splunk_sourcetype": "fins:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.2,
            "label": "0.2 s"
          },
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 310,
        "min": 0,
        "profilePresets": {
          "low": 130,
          "typical": 310,
          "high": 580
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32"
    ]
  },
  {
    "id": "proto_melsec",
    "name": "MELSEC (MC Protocol)",
    "category": "Protocols",
    "subcategory": "Industrial Fieldbus",
    "description": "Mitsubishi PLC access protocol — binary read/write of device registers (SLMP compatible)",
    "vendor_examples": "Mitsubishi MELSEC iQ-R, iQ-F, Q, L series",
    "protocol": "MELSEC MC / SLMP (TCP/UDP)",
    "ingest_method": "OPC gateway / SCADA historian → HEC",
    "splunk_sourcetype": "melsec:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 20,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.2,
            "label": "0.2 s"
          },
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 320,
        "min": 0,
        "profilePresets": {
          "low": 130,
          "typical": 320,
          "high": 600
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.2.7",
      "14.3.32"
    ]
  },
  {
    "id": "proto_iolink",
    "name": "IO-Link",
    "category": "Protocols",
    "subcategory": "Smart Sensors",
    "description": "Point-to-point smart sensor/actuator protocol — ISDU parameters, process data, events",
    "vendor_examples": "IFM, Balluff, Sick, Turck, Banner, Pepperl+Fuchs",
    "protocol": "IO-Link (3-wire, via master)",
    "ingest_method": "IO-Link master → OPC/MQTT → HEC",
    "splunk_sourcetype": "iolink:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 30,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 6,
          "typical": 30,
          "high": 300
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 5,
        "options": [
          {
            "value": 0.1,
            "label": "0.1 s"
          },
          {
            "value": 0.5,
            "label": "0.5 s"
          },
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 330,
        "min": 0,
        "profilePresets": {
          "low": 140,
          "typical": 330,
          "high": 700
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.4.1",
      "14.4.2",
      "14.3.24"
    ]
  },
  {
    "id": "proto_wirelesshart",
    "name": "WirelessHART",
    "category": "Protocols",
    "subcategory": "Wireless Industrial",
    "description": "IEC 62591 wireless mesh for process instruments — time-synchronized TDMA",
    "vendor_examples": "Emerson, Honeywell, ABB, Endress+Hauser, Yokogawa",
    "protocol": "WirelessHART (IEEE 802.15.4)",
    "ingest_method": "DCS/gateway → OPC → HEC",
    "splunk_sourcetype": "wirelesshart:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 30,
        "options": [
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 300,
            "label": "5 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 340,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 340,
          "high": 680
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.8",
      "14.4.1",
      "14.3.24"
    ]
  },
  {
    "id": "proto_zigbee",
    "name": "Zigbee / Thread",
    "category": "Protocols",
    "subcategory": "IoT Lightweight",
    "description": "Low-power mesh for building and consumer IoT — clusters/attributes model (802.15.4)",
    "vendor_examples": "Silicon Labs, NXP, Texas Instruments, SmartThings, Philips Hue",
    "protocol": "Zigbee 3.0 / Thread (802.15.4)",
    "ingest_method": "Hub/gateway → MQTT/HTTP → HEC",
    "splunk_sourcetype": "zigbee:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 60,
        "options": [
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 120,
            "label": "2 min"
          },
          {
            "value": 300,
            "label": "5 min"
          },
          {
            "value": 600,
            "label": "10 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 130,
          "typical": 300,
          "high": 580
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.24"
    ]
  },
  {
    "id": "proto_restjson",
    "name": "HTTP/REST + JSON (Modern PLCs)",
    "category": "Protocols",
    "subcategory": "Web / API",
    "description": "REST API endpoints on modern PLCs, gateways, and edge devices — cloud-native pattern",
    "vendor_examples": "Siemens S7-1500 WebAPI, Wago PFC, Codesys, Node-RED, custom edge apps",
    "protocol": "HTTP/HTTPS (REST/JSON)",
    "ingest_method": "Scripted input / webhook → HEC",
    "splunk_sourcetype": "rest:metric",
    "calibration": "pending",
    "drivers": [
      {
        "id": "tag_count",
        "label": "Number of tags / topics / OIDs",
        "unit": "tags",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 1000000,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "poll_interval_sec",
        "label": "Polling / publish interval",
        "unit": "seconds",
        "type": "enum",
        "default": 10,
        "options": [
          {
            "value": 1,
            "label": "1 s"
          },
          {
            "value": 2,
            "label": "2 s"
          },
          {
            "value": 5,
            "label": "5 s"
          },
          {
            "value": 10,
            "label": "10 s"
          },
          {
            "value": 30,
            "label": "30 s"
          },
          {
            "value": 60,
            "label": "1 min"
          },
          {
            "value": 300,
            "label": "5 min"
          }
        ]
      },
      {
        "id": "deadband_ratio",
        "label": "Value-change filter (deadband)",
        "unit": "fraction",
        "type": "number",
        "default": 0,
        "min": 0,
        "max": 0.95,
        "profilePresets": {
          "low": 0,
          "typical": 0,
          "high": 0
        },
        "help": "Fraction of polls deduplicated at the gateway when register value didn’t change. Default 0 for pending sources; calibrated sources tune per protocol."
      },
      {
        "id": "bytes_per_tag",
        "label": "Bytes per tag (per poll cycle)",
        "unit": "bytes",
        "type": "number",
        "default": 380,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 380,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "protocol_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "8.4.1",
      "8.4.2",
      "14.3.42",
      "23.1.1"
    ]
  },
  {
    "id": "dsa_biz_transaction",
    "name": "Business Transaction Logs",
    "category": "Business & Compliance",
    "subcategory": "Transaction Processing",
    "description": "Business service transaction logs — order processing, payment status, batch uploads",
    "vendor_examples": "Oracle Apps, SAP, Salesforce, ServiceNow, custom ERP systems",
    "protocol": "REST API / DB Connect / File",
    "ingest_method": "DB Connect or TA (API poll)",
    "splunk_sourcetype": "oracle:apps, sap:transaction",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.5,
          "high": 8
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.1.3",
      "23.1.4",
      "23.1.5"
    ]
  },
  {
    "id": "dsa_biz_ecommerce",
    "name": "E-Commerce / High-Volume Transactions",
    "category": "Business & Compliance",
    "subcategory": "Transaction Processing",
    "description": "High-volume e-commerce transaction logs — web orders, cart events, payment processing",
    "vendor_examples": "Shopify, Magento, WooCommerce, Salesforce Commerce, custom platforms",
    "protocol": "REST API / Webhook / File",
    "ingest_method": "HEC (webhook) or TA",
    "splunk_sourcetype": "ecommerce:transaction, payment:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.1.3",
      "23.2.1"
    ]
  },
  {
    "id": "dsa_biz_pos",
    "name": "Point of Sale (POS) Systems",
    "category": "Business & Compliance",
    "subcategory": "Retail Operations",
    "description": "POS transaction records, card processing, inventory changes, employee actions",
    "vendor_examples": "NCR, Square, LightSpeed, Revel, Toshiba, Clover",
    "protocol": "REST API / File / DB Connect",
    "ingest_method": "TA (API poll) or DB Connect",
    "splunk_sourcetype": "pos:transaction, pos:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.3,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.3,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.2.1",
      "23.2.2"
    ]
  },
  {
    "id": "dsa_biz_batch",
    "name": "Batch Processing / ETL Logs",
    "category": "Business & Compliance",
    "subcategory": "Data Processing",
    "description": "Batch job execution logs — ETL pipelines, data warehouse loads, scheduled report runs",
    "vendor_examples": "Informatica, Talend, SSIS, Apache Airflow, Control-M, Autosys",
    "protocol": "File / REST API / Syslog",
    "ingest_method": "UF (file monitor) or HEC",
    "splunk_sourcetype": "batch:status, etl:job",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 2,
          "typical": 3,
          "high": 30
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.3,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.3,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.2.1"
    ]
  },
  {
    "id": "dsa_biz_apm",
    "name": "Business Service APM",
    "category": "Business & Compliance",
    "subcategory": "Service Monitoring",
    "description": "Application performance monitoring focused on business service health and SLAs",
    "vendor_examples": "Dynatrace, New Relic, AppDynamics, Pulseway, Idera",
    "protocol": "REST API / OTLP",
    "ingest_method": "TA (API poll) or HEC",
    "splunk_sourcetype": "dynatrace:problem, appdynamics:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1.5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 1.5,
          "high": 8
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.1.3",
      "8.7.1",
      "8.7.2"
    ]
  },
  {
    "id": "dsa_biz_fraud",
    "name": "Fraud Detection / Customer Fraud Logs",
    "category": "Business & Compliance",
    "subcategory": "Fraud Analytics",
    "description": "Customer fraud detection events, risk scoring, chargeback alerts, account takeover signals",
    "vendor_examples": "FICO Falcon, SAS Fraud, Actimize, Featurespace, Kount",
    "protocol": "REST API / File / DB Connect",
    "ingest_method": "DB Connect or HEC",
    "splunk_sourcetype": "fraud:alert, fraud:transaction",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 6,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 6,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.12.1",
      "10.12.2",
      "10.12.3",
      "23.1.1"
    ]
  },
  {
    "id": "dsa_biz_social",
    "name": "Social Media Feeds",
    "category": "Business & Compliance",
    "subcategory": "Digital Channels",
    "description": "Social media monitoring — mentions, sentiment, brand monitoring, campaign analytics",
    "vendor_examples": "Twitter/X, LinkedIn, Facebook, custom social listening platforms",
    "protocol": "REST API / Streaming API",
    "ingest_method": "TA (API poll) or HEC",
    "splunk_sourcetype": "twitter:tweet, social:mention",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1000,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.2.1",
      "23.2.2",
      "23.2.3"
    ]
  },
  {
    "id": "cisco_spaces",
    "name": "Cisco Spaces (Indoor Location Services)",
    "category": "Cisco Products",
    "subcategory": "Networking & Location",
    "description": "Indoor location analytics — visitor foot traffic, dwell time, asset tracking, occupancy, environmental IoT via existing Cisco wireless infrastructure",
    "vendor_examples": "Cisco Spaces (formerly DNA Spaces / CMX)",
    "protocol": "Firehose API / REST API / Webhook",
    "ingest_method": "HEC (Firehose streaming or API poll)",
    "splunk_sourcetype": "cisco:spaces:location, cisco:spaces:entry, cisco:spaces:exit, cisco:spaces:iot",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "15.3.30",
      "15.3.34",
      "15.3.38",
      "15.3.39",
      "15.3.40"
    ]
  },
  {
    "id": "cisco_thousandeyes",
    "name": "Cisco ThousandEyes (Digital Experience Monitoring)",
    "category": "Cisco Products",
    "subcategory": "Observability",
    "description": "Network path analysis, application performance, DNS monitoring, VoIP quality, BGP monitoring across owned and unowned networks",
    "vendor_examples": "Cisco ThousandEyes",
    "protocol": "OpenTelemetry / REST API / Webhook",
    "ingest_method": "OTEL → HEC (native Splunk connector) or TA (API poll)",
    "splunk_sourcetype": "ThousandEyesOTel, cisco:thousandeyes:test, cisco:thousandeyes:alert",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.9.1",
      "5.9.2",
      "5.9.6",
      "5.9.18",
      "5.9.46"
    ]
  },
  {
    "id": "cisco_catalyst_center",
    "name": "Cisco Catalyst Center (DNA Center)",
    "category": "Cisco Products",
    "subcategory": "Networking & Assurance",
    "description": "Network controller — device health scores, client health, AI-driven issue detection, software compliance, configuration audit, wireless RF health",
    "vendor_examples": "Cisco Catalyst Center (formerly DNA Center)",
    "protocol": "REST API (Intent API) / Webhook / Syslog",
    "ingest_method": "Cisco Catalyst Add-on (API poll) or Webhook → HEC",
    "splunk_sourcetype": "cisco:dnac:issue, cisco:dnac:device, cisco:dnac:client, cisco:dnac:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.2,
          "typical": 1,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.8.1"
    ]
  },
  {
    "id": "cisco_sdwan",
    "name": "Cisco Catalyst SD-WAN (vManage)",
    "category": "Cisco Products",
    "subcategory": "Networking & Security",
    "description": "SD-WAN security events — IPS, malware, URL filtering, firewall policy; VPN tunnel health; NetFlow traffic analytics; device telemetry",
    "vendor_examples": "Cisco Catalyst SD-WAN (formerly Viptela)",
    "protocol": "Syslog / NetFlow v9 / REST API",
    "ingest_method": "Cisco Catalyst SD-WAN Add-on (SC4S + NetFlow)",
    "splunk_sourcetype": "cisco:sdwan:syslog, cisco:sdwan:ips, cisco:sdwan:firewall, stream:cisco_hsl_netflow",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 30,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 30,
          "high": 200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.5.1",
      "5.5.4",
      "5.5.18",
      "5.9.29"
    ]
  },
  {
    "id": "cisco_meraki_network",
    "name": "Cisco Meraki (Cloud-Managed Networking)",
    "category": "Cisco Products",
    "subcategory": "Cloud-Managed Networking",
    "description": "Cloud-managed AP, switch, and MX security appliance — device health, wireless analytics, security events, firmware tracking via REST API and webhooks",
    "vendor_examples": "Cisco Meraki MR, MS, MX, MG",
    "protocol": "REST API / Webhook / Syslog",
    "ingest_method": "Cisco Meraki Add-on (API poll) + Webhook → HEC",
    "splunk_sourcetype": "meraki:devices, meraki:webhook, meraki:apirequestshistory",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 2,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.1.36",
      "5.2.19",
      "5.4.12",
      "5.8.2",
      "14.1.15"
    ]
  },
  {
    "id": "cisco_meraki_sensors",
    "name": "Cisco Meraki MT Sensors (Environmental)",
    "category": "Cisco Products",
    "subcategory": "IoT Sensors",
    "description": "Environmental monitoring — temperature, humidity, door open/close, water leak, air quality (PM2.5, TVOC) from Meraki MT sensor line via MQTT or API",
    "vendor_examples": "Cisco Meraki MT10, MT12, MT14, MT15, MT20, MT30, MT40",
    "protocol": "MQTT / REST API",
    "ingest_method": "MQTT → Edge Hub → HEC, or API poll via TA",
    "splunk_sourcetype": "meraki:sensorreadingshistory, meraki_mt_json",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 20,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 10,
          "typical": 20,
          "high": 200
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.1,
        "min": 0,
        "profilePresets": {
          "low": 0.02,
          "typical": 0.1,
          "high": 1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 350,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 350,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.15",
      "14.3.1",
      "14.3.6",
      "14.3.24"
    ]
  },
  {
    "id": "cisco_meraki_cameras",
    "name": "Cisco Meraki MV Cameras (Video Analytics)",
    "category": "Cisco Products",
    "subcategory": "IoT Sensors",
    "description": "Smart camera analytics — people counting, motion detection, zone occupancy via MV Sense MQTT API (metadata only, no video stream)",
    "vendor_examples": "Cisco Meraki MV2, MV12, MV22, MV32, MV52, MV72",
    "protocol": "MQTT (MV Sense API)",
    "ingest_method": "MQTT → Edge Hub → HEC",
    "splunk_sourcetype": "meraki_mv_json",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 5,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "15.3.30",
      "15.3.34",
      "15.3.38",
      "14.1.15"
    ]
  },
  {
    "id": "cisco_secure_firewall",
    "name": "Cisco Secure Firewall (FTD / ASA / FMC)",
    "category": "Cisco Products",
    "subcategory": "Network Security",
    "description": "NGFW — intrusion prevention (IPS), malware defense (AMP), connection logging, URL filtering, application visibility via eStreamer or syslog",
    "vendor_examples": "Cisco FTD, Cisco ASA, Firepower Management Center (FMC)",
    "protocol": "eStreamer / Syslog / REST API",
    "ingest_method": "eStreamer eNcore Add-on or SC4S (syslog)",
    "splunk_sourcetype": "cisco:firepower:estreamer, cisco:ftd:syslog, cisco:asa:syslog, cisco:firepower:connection",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 100,
        "min": 0,
        "profilePresets": {
          "low": 10,
          "typical": 100,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.2.1",
      "5.2.3",
      "10.1.46",
      "10.1.58",
      "10.1.62"
    ]
  },
  {
    "id": "cisco_ise",
    "name": "Cisco ISE (Identity Services Engine)",
    "category": "Cisco Products",
    "subcategory": "Identity & Access",
    "description": "NAC platform — RADIUS authentication, posture assessment, device profiling, TrustSec SGT, guest access, pxGrid context sharing",
    "vendor_examples": "Cisco Identity Services Engine (ISE)",
    "protocol": "Syslog / pxGrid / Data Connect (JDBC)",
    "ingest_method": "Splunk Add-on for Cisco ISE (SC4S syslog)",
    "splunk_sourcetype": "cisco:ise:syslog, cisco:ise:audit, cisco:ise:radius",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 50,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 50,
          "high": 500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 1200,
          "high": 2500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "17.1.1",
      "17.1.3",
      "17.1.7",
      "17.1.13",
      "17.1.21"
    ]
  },
  {
    "id": "cisco_cyber_vision",
    "name": "Cisco Cyber Vision (OT/ICS Security)",
    "category": "Cisco Products",
    "subcategory": "OT Security",
    "description": "OT/ICS network visibility — industrial asset discovery, vulnerability tracking (CVE), anomaly detection, protocol analysis, IEC 62443 zone compliance",
    "vendor_examples": "Cisco Cyber Vision Center + Sensors",
    "protocol": "REST API / Syslog (CEF) / Webhook",
    "ingest_method": "Cisco Catalyst Add-on (API poll) or SC4S",
    "splunk_sourcetype": "cisco:cybervision:components, cisco:cybervision:flows, cisco:cybervision:events, cisco:cybervision:vulnerabilities",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.9.1",
      "14.9.3",
      "14.9.5",
      "14.9.20",
      "14.9.21"
    ]
  },
  {
    "id": "cisco_secure_endpoint",
    "name": "Cisco Secure Endpoint (AMP for Endpoints)",
    "category": "Cisco Products",
    "subcategory": "Endpoint Security",
    "description": "Cloud-delivered endpoint protection — file conviction, malware detection, threat hunting, device trajectory, exploit prevention, Orbital queries",
    "vendor_examples": "Cisco Secure Endpoint (formerly AMP for Endpoints)",
    "protocol": "REST API / Syslog",
    "ingest_method": "Cisco AMP TA (API poll) or SC4S",
    "splunk_sourcetype": "cisco:amp:event, cisco:amp:computer",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 500,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 250,
          "typical": 500,
          "high": 5000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.05,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.05,
          "high": 0.5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.3.1",
      "10.3.2",
      "10.3.3",
      "10.11.41",
      "10.11.42"
    ]
  },
  {
    "id": "cisco_umbrella",
    "name": "Cisco Umbrella (DNS Security / SIG)",
    "category": "Cisco Products",
    "subcategory": "Cloud Security",
    "description": "Cloud-delivered DNS security — DNS query logs, proxy logs, firewall logs, DLP, CASB, malware blocking, Secure Internet Gateway (SIG) events",
    "vendor_examples": "Cisco Umbrella",
    "protocol": "REST API / S3 log export / Syslog",
    "ingest_method": "Cisco Umbrella TA (S3 log download or API poll)",
    "splunk_sourcetype": "cisco:umbrella:dns, cisco:umbrella:proxy, cisco:umbrella:cloudfirewall",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 100,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 50,
          "typical": 100,
          "high": 1000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.5.1",
      "10.5.2",
      "10.5.3",
      "5.6.1",
      "5.6.2"
    ]
  },
  {
    "id": "cisco_duo",
    "name": "Cisco Duo (MFA / Zero Trust Access)",
    "category": "Cisco Products",
    "subcategory": "Identity & Access",
    "description": "Multi-factor authentication — auth logs, admin actions, telephony events, device trust, adaptive access policy events",
    "vendor_examples": "Cisco Duo Security",
    "protocol": "REST API (Admin API)",
    "ingest_method": "Cisco Duo TA (API poll)",
    "splunk_sourcetype": "duo:authentication, duo:admin, duo:telephony",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 500,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 250,
          "typical": 500,
          "high": 5000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.03,
        "min": 0,
        "profilePresets": {
          "low": 0.005,
          "typical": 0.03,
          "high": 0.1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1000,
          "high": 2500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "9.5.1",
      "9.5.2",
      "9.5.3",
      "9.5.4",
      "9.5.5"
    ]
  },
  {
    "id": "cisco_secure_network_analytics",
    "name": "Cisco Secure Network Analytics (Stealthwatch)",
    "category": "Cisco Products",
    "subcategory": "Network Security",
    "description": "Network traffic analytics — flow-based anomaly detection, encrypted traffic analytics (ETA), insider threat, data exfiltration, lateral movement detection",
    "vendor_examples": "Cisco Secure Network Analytics (formerly Stealthwatch)",
    "protocol": "Syslog / REST API",
    "ingest_method": "SC4S (syslog) or TA (API poll)",
    "splunk_sourcetype": "cisco:stealthwatch:alert, cisco:stealthwatch:flow",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 1000,
          "high": 2500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.7.1",
      "5.7.2",
      "5.7.7",
      "10.2.1",
      "10.2.2"
    ]
  },
  {
    "id": "cisco_email_security",
    "name": "Cisco Secure Email (ESA / CES)",
    "category": "Cisco Products",
    "subcategory": "Email Security",
    "description": "Email gateway — anti-spam, anti-malware, DLP, URL defenses, encrypted email, message tracking, content filtering, AMP for email",
    "vendor_examples": "Cisco Secure Email (formerly Email Security Appliance / Cloud Email Security)",
    "protocol": "Syslog",
    "ingest_method": "SC4S or UF (file monitor)",
    "splunk_sourcetype": "cisco:esa:syslog, cisco:esa:textmail",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 20,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 20,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.4.1",
      "10.4.2",
      "10.4.3",
      "10.4.4",
      "10.4.5"
    ]
  },
  {
    "id": "cisco_web_security",
    "name": "Cisco Secure Web Appliance (WSA / SWG)",
    "category": "Cisco Products",
    "subcategory": "Web Security",
    "description": "Web proxy / SWG — URL filtering, malware scanning, HTTPS inspection, application visibility, DLP, bandwidth management, user activity logging",
    "vendor_examples": "Cisco Secure Web Appliance (formerly WSA / Web Security Appliance)",
    "protocol": "Syslog / W3C access log",
    "ingest_method": "SC4S or UF (file monitor)",
    "splunk_sourcetype": "cisco:wsa:squid, cisco:wsa:w3c",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 50,
        "min": 0,
        "profilePresets": {
          "low": 10,
          "typical": 50,
          "high": 500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 700,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 700,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.5.1",
      "10.5.2",
      "10.5.3",
      "10.5.4",
      "10.5.5"
    ]
  },
  {
    "id": "cisco_webex_meetings",
    "name": "Cisco Webex Meetings",
    "category": "Cisco Products",
    "subcategory": "Collaboration",
    "description": "Video conferencing analytics — meeting sessions, participant details, audio/video quality scores, recording metadata, host activity",
    "vendor_examples": "Cisco Webex Meetings",
    "protocol": "REST API / XML API / Webhook",
    "ingest_method": "Cisco Webex Add-on (API poll) or Webhook → HEC",
    "splunk_sourcetype": "cisco:webex:meetings:history, cisco:webex:meetings:attendee, cisco:webex:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 500,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 250,
          "typical": 500,
          "high": 5000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.03,
        "min": 0,
        "profilePresets": {
          "low": 0.005,
          "typical": 0.03,
          "high": 0.1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "11.5.1",
      "11.5.2",
      "11.5.3",
      "11.3.1",
      "11.3.2"
    ]
  },
  {
    "id": "cisco_webex_calling",
    "name": "Cisco Webex Calling (CDR)",
    "category": "Cisco Products",
    "subcategory": "Collaboration",
    "description": "Cloud calling platform — call detail records, call quality metrics, user adoption, device registration, trunk utilization",
    "vendor_examples": "Cisco Webex Calling",
    "protocol": "REST API",
    "ingest_method": "Cisco Webex Add-on (API poll)",
    "splunk_sourcetype": "cisco:webex:calling:cdr",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 500,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 250,
          "typical": 500,
          "high": 5000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.02,
        "min": 0,
        "profilePresets": {
          "low": 0.005,
          "typical": 0.02,
          "high": 0.1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 700,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 700,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "11.3.1",
      "11.3.2",
      "11.3.3",
      "5.12.1",
      "5.12.2"
    ]
  },
  {
    "id": "cisco_webex_contact_center",
    "name": "Cisco Webex Contact Center (WxCC)",
    "category": "Cisco Products",
    "subcategory": "Collaboration",
    "description": "Cloud contact center — agent state changes, interaction records, queue metrics, IVR flow events, customer journey analytics, CSAT scores",
    "vendor_examples": "Cisco Webex Contact Center (WxCC)",
    "protocol": "REST API / Webhook",
    "ingest_method": "HEC (SplunkBridge or API poll)",
    "splunk_sourcetype": "cisco:wxcc:interaction, cisco:wxcc:agent",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 50,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 25,
          "typical": 50,
          "high": 500
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.5,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "11.3.1",
      "11.3.2",
      "23.1.1",
      "23.1.2"
    ]
  },
  {
    "id": "cisco_ucm",
    "name": "Cisco Unified Communications Manager (UCM)",
    "category": "Cisco Products",
    "subcategory": "Collaboration",
    "description": "On-premises IP telephony — call detail records, call management records, syslog events, phone registration, trunk utilization",
    "vendor_examples": "Cisco UCM (CallManager), Cisco Unity Connection",
    "protocol": "Syslog / CDR flat file / JTAPI",
    "ingest_method": "UF (CDR file monitor) or SC4S (syslog)",
    "splunk_sourcetype": "cisco:ucm:cdr, cisco:ucm:cmr, cisco:ucm:syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 25
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "11.3.1",
      "11.3.2",
      "11.3.3",
      "11.3.4",
      "11.3.5"
    ]
  },
  {
    "id": "cisco_intersight",
    "name": "Cisco Intersight (Infrastructure Management)",
    "category": "Cisco Products",
    "subcategory": "Infrastructure",
    "description": "Cloud operations platform — UCS server health, HyperFlex storage, firmware compliance, advisory alerts, workload optimization",
    "vendor_examples": "Cisco Intersight, Cisco UCS, Cisco HyperFlex",
    "protocol": "REST API / Webhook",
    "ingest_method": "TA (API poll) or Webhook → HEC",
    "splunk_sourcetype": "cisco:intersight:alarm, cisco:intersight:server, cisco:intersight:advisory",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.5,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "19.1.1",
      "19.1.2",
      "19.1.3",
      "1.4.1",
      "1.4.2"
    ]
  },
  {
    "id": "cisco_appdynamics",
    "name": "Cisco AppDynamics (APM)",
    "category": "Cisco Products",
    "subcategory": "Observability",
    "description": "Application performance monitoring — business transaction health, tier/node metrics, error analytics, database visibility, infrastructure monitoring",
    "vendor_examples": "Cisco AppDynamics (Cloud Native / On-Premises)",
    "protocol": "REST API / Webhook",
    "ingest_method": "TA (API poll) or Webhook → HEC",
    "splunk_sourcetype": "appdynamics:event, appdynamics:metric, appdynamics:health_rule",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "23.1.1",
      "23.1.2",
      "23.1.3",
      "8.7.1",
      "8.7.2"
    ]
  },
  {
    "id": "cisco_secure_access",
    "name": "Cisco Secure Access (SSE / ZTNA)",
    "category": "Cisco Products",
    "subcategory": "Cloud Security",
    "description": "Security Service Edge — Zero Trust Network Access, secure web gateway, CASB, DLP, FWaaS, DNS security — unified cloud security logs",
    "vendor_examples": "Cisco Secure Access (SSE platform)",
    "protocol": "REST API / S3 log export",
    "ingest_method": "TA (S3 or API poll)",
    "splunk_sourcetype": "cisco:sse:access, cisco:sse:web, cisco:sse:dlp",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 500,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 250,
          "typical": 500,
          "high": 5000
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.3,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.3,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 700,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 700,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "17.2.9",
      "17.3.23",
      "10.5.1",
      "9.3.1"
    ]
  },
  {
    "id": "cisco_xdr",
    "name": "Cisco XDR (Extended Detection & Response)",
    "category": "Cisco Products",
    "subcategory": "Security Operations",
    "description": "Cross-product security orchestration — correlated incidents from Firewall, Endpoint, Email, Umbrella; automated response playbooks; threat intelligence",
    "vendor_examples": "Cisco XDR (formerly SecureX)",
    "protocol": "REST API / Webhook",
    "ingest_method": "TA (API poll) or Webhook → HEC",
    "splunk_sourcetype": "cisco:xdr:incident, cisco:xdr:sighting, cisco:xdr:casebook",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.5,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 2000,
        "min": 0,
        "profilePresets": {
          "low": 800,
          "typical": 2000,
          "high": 5000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "10.7.1",
      "10.7.2",
      "10.7.3",
      "10.7.4",
      "10.7.5"
    ]
  },
  {
    "id": "cisco_ind",
    "name": "Cisco Industrial Network Director (IND)",
    "category": "Cisco Products",
    "subcategory": "OT Networking",
    "description": "OT network management — industrial switch/router monitoring, PROFINET/CIP device discovery, alarm management, firmware compliance, topology visualization",
    "vendor_examples": "Cisco Industrial Network Director",
    "protocol": "REST API / Syslog / SNMP",
    "ingest_method": "SC4S or TA (API poll)",
    "splunk_sourcetype": "cisco:ind:alarm, cisco:ind:device, cisco:ind:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.5,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.1",
      "14.1.8",
      "14.1.10",
      "14.1.14",
      "5.8.3"
    ]
  },
  {
    "id": "cisco_catalyst_switches",
    "name": "Cisco Catalyst Switches (Enterprise / Industrial)",
    "category": "Cisco Products",
    "subcategory": "Networking Hardware",
    "description": "Enterprise and industrial Ethernet switches — syslog, SNMP traps, NetFlow, ERSPAN, EEM events, PoE status, environmental sensors",
    "vendor_examples": "Cisco Catalyst 9000, 3000, IE3x00, IE4000, IE5000 series",
    "protocol": "Syslog / SNMP / NetFlow",
    "ingest_method": "SC4S (syslog) or UF",
    "splunk_sourcetype": "cisco:ios, cisco:ios:syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 20,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 10,
          "typical": 20,
          "high": 200
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.1.1",
      "5.1.6",
      "5.1.13",
      "5.1.22",
      "5.1.36"
    ]
  },
  {
    "id": "cisco_routers",
    "name": "Cisco Routers (Enterprise / Industrial)",
    "category": "Cisco Products",
    "subcategory": "Networking Hardware",
    "description": "Enterprise and industrial routers — syslog, NetFlow, SNMP, BGP events, interface stats, IOx application logs, EEM events",
    "vendor_examples": "Cisco ISR 1000/4000, ASR 1000, IR1101, IR829, IR8340",
    "protocol": "Syslog / NetFlow / SNMP",
    "ingest_method": "SC4S (syslog) or UF",
    "splunk_sourcetype": "cisco:ios, cisco:iosxe:syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.1.4",
      "5.1.5",
      "5.1.16",
      "5.1.35"
    ]
  },
  {
    "id": "cisco_wlc",
    "name": "Cisco Wireless LAN Controller (WLC / C9800)",
    "category": "Cisco Products",
    "subcategory": "Networking Hardware",
    "description": "Wireless controller — client association/disassociation, rogue AP detection, RF interference, RADIUS auth, mobility events, AP join/disjoin",
    "vendor_examples": "Cisco Catalyst 9800 WLC, Cisco 5520/8540 WLC",
    "protocol": "Syslog / SNMP / NMSP",
    "ingest_method": "SC4S (syslog)",
    "splunk_sourcetype": "cisco:wlc:syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 2,
          "typical": 10,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "5.4.2",
      "5.4.7",
      "5.4.10",
      "5.4.12",
      "5.4.20"
    ]
  },
  {
    "id": "cisco_edge_intelligence",
    "name": "Cisco Edge Intelligence (IoT Data Orchestration)",
    "category": "Cisco Products",
    "subcategory": "IoT / Industrial",
    "description": "Edge data orchestration — OPC-UA, Modbus, MQTT, EIP/CIP data collection; JavaScript edge transforms; native Splunk HEC destination; runs on IR1101/IR829/IC3000",
    "vendor_examples": "Cisco Edge Intelligence on IR1101, IR829, IC3000, Catalyst IE",
    "protocol": "OPC-UA / Modbus / MQTT / EIP/CIP → HEC",
    "ingest_method": "Native Splunk HEC destination (built-in)",
    "splunk_sourcetype": "cisco:ei:telemetry, cisco:ei:opcua, cisco:ei:modbus, cisco:ei:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 2,
          "typical": 3,
          "high": 30
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.7",
      "14.3.34",
      "14.3.42"
    ]
  },
  {
    "id": "siemens_mindsphere",
    "name": "Siemens MindSphere / Insights Hub",
    "category": "OT Vendor Systems",
    "subcategory": "Siemens",
    "description": "Industrial IoT cloud — asset telemetry, condition monitoring, alarms, KPI analytics, fleet management, predictive maintenance signals",
    "vendor_examples": "Siemens MindSphere, Siemens Insights Hub",
    "protocol": "REST API / MQTT",
    "ingest_method": "TA (API poll) or MQTT → HEC",
    "splunk_sourcetype": "siemens:mindsphere:telemetry, siemens:mindsphere:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.4.1",
      "14.5.1"
    ]
  },
  {
    "id": "siemens_wincc",
    "name": "Siemens WinCC / WinCC OA (SCADA)",
    "category": "OT Vendor Systems",
    "subcategory": "Siemens",
    "description": "SCADA/HMI — process alarms, operator actions, audit trail, tag historian exports; WinCC OA adds redundancy and large-scale distribution",
    "vendor_examples": "Siemens WinCC Professional, WinCC OA (Open Architecture)",
    "protocol": "OPC UA / SQL / File logs",
    "ingest_method": "OPC UA → Edge Hub, or DB Connect (SQL), or UF (file logs)",
    "splunk_sourcetype": "siemens:wincc:alarm, siemens:wincc:audit, siemens:wincc:tag",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "siemens_tia_portal",
    "name": "Siemens TIA Portal (Engineering)",
    "category": "OT Vendor Systems",
    "subcategory": "Siemens",
    "description": "Engineering workstation logs — project compile events, PLC download records, connection logs, user activity audit trail",
    "vendor_examples": "Siemens TIA Portal V17/V18/V19",
    "protocol": "Windows Event Log / File logs",
    "ingest_method": "UF (WinEventLog + file monitor)",
    "splunk_sourcetype": "WinEventLog:Application, siemens:tia:log",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 2,
          "typical": 3,
          "high": 30
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.1,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.1,
          "high": 1
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.9.1"
    ]
  },
  {
    "id": "siemens_sinema",
    "name": "Siemens SINEMA (Network Management)",
    "category": "OT Vendor Systems",
    "subcategory": "Siemens",
    "description": "OT network management — SINEMA Server network topology, SINEMA Remote Connect VPN sessions, device status, fault diagnostics",
    "vendor_examples": "Siemens SINEMA Server, SINEMA Remote Connect",
    "protocol": "Syslog / SNMP / REST API",
    "ingest_method": "SC4S (syslog) or TA (API poll)",
    "splunk_sourcetype": "siemens:sinema:syslog, siemens:sinema:vpn",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.1",
      "14.1.10",
      "14.1.14",
      "5.8.3"
    ]
  },
  {
    "id": "siemens_scalance",
    "name": "Siemens SCALANCE Switches / Routers",
    "category": "OT Vendor Systems",
    "subcategory": "Siemens",
    "description": "Industrial networking hardware — syslog, SNMP traps, port security events, PROFINET diagnostics, redundancy switchover events",
    "vendor_examples": "Siemens SCALANCE XC, XR, XM, XB, SC series, RUGGEDCOM",
    "protocol": "Syslog / SNMP",
    "ingest_method": "SC4S (syslog)",
    "splunk_sourcetype": "syslog, siemens:scalance:syslog",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.1",
      "14.1.10",
      "5.1.1",
      "5.1.6"
    ]
  },
  {
    "id": "siemens_industrial_edge",
    "name": "Siemens Industrial Edge",
    "category": "OT Vendor Systems",
    "subcategory": "Siemens",
    "description": "Edge computing platform — app telemetry, device metrics, edge analytics results, container health; runs on IPCs near PLCs",
    "vendor_examples": "Siemens Industrial Edge (IPC-based)",
    "protocol": "MQTT / REST API / OPC UA",
    "ingest_method": "MQTT → HEC or TA (API poll)",
    "splunk_sourcetype": "siemens:edge:telemetry, siemens:edge:app",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 2,
          "typical": 3,
          "high": 30
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.3.7",
      "14.3.42"
    ]
  },
  {
    "id": "siemens_opcenter",
    "name": "Siemens Opcenter (MES)",
    "category": "OT Vendor Systems",
    "subcategory": "Siemens",
    "description": "Manufacturing execution — production orders, quality inspections, batch records, genealogy/traceability, OEE, scheduling events",
    "vendor_examples": "Siemens Opcenter Execution, Opcenter Quality, Opcenter Intelligence",
    "protocol": "REST API / SQL / OPC UA",
    "ingest_method": "DB Connect (SQL) or TA (API poll)",
    "splunk_sourcetype": "siemens:opcenter:production, siemens:opcenter:quality",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.5.1",
      "14.5.2",
      "14.5.3"
    ]
  },
  {
    "id": "rockwell_factorytalk",
    "name": "Rockwell FactoryTalk View / Optix (SCADA)",
    "category": "OT Vendor Systems",
    "subcategory": "Rockwell Automation",
    "description": "SCADA/HMI — alarm journal, operator audit trail, diagnostic events, FactoryTalk Diagnostics logs, runtime events",
    "vendor_examples": "FactoryTalk View SE, FactoryTalk Optix, FactoryTalk Linx",
    "protocol": "OPC DA/UA / SQL / Windows logs",
    "ingest_method": "OPC UA → Edge Hub, or DB Connect, or UF (FT Diagnostics logs)",
    "splunk_sourcetype": "rockwell:ft:alarm, rockwell:ft:audit, rockwell:ft:diag",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "rockwell_ft_historian",
    "name": "Rockwell FactoryTalk Historian",
    "category": "OT Vendor Systems",
    "subcategory": "Rockwell Automation",
    "description": "Process historian — compressed time-series tag data, alarm history, batch context; SQL access for aggregated exports to Splunk",
    "vendor_examples": "FactoryTalk Historian SE (OSIsoft PI-based), FactoryTalk Historian ME",
    "protocol": "SQL / OPC / PI Web API",
    "ingest_method": "DB Connect (SQL views) or PI Web API → HEC",
    "splunk_sourcetype": "rockwell:historian:tag, rockwell:historian:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.2.16",
      "14.2.25",
      "14.2.26"
    ]
  },
  {
    "id": "rockwell_plantpax",
    "name": "Rockwell PlantPAx (DCS)",
    "category": "OT Vendor Systems",
    "subcategory": "Rockwell Automation",
    "description": "Modern DCS — process alarms, batch events, loop diagnostics, SOE (sequence of events), safety (GuardLogix) events, module faults",
    "vendor_examples": "Rockwell PlantPAx 5.0, PlantPAx Process Library",
    "protocol": "OPC UA / FactoryTalk Historian / SQL",
    "ingest_method": "OPC UA → Edge Hub, or DB Connect (historian SQL)",
    "splunk_sourcetype": "rockwell:plantpax:alarm, rockwell:plantpax:batch, rockwell:plantpax:soe",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 30,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 30,
          "high": 300
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "rockwell_plex",
    "name": "Rockwell Plex (Cloud MES)",
    "category": "OT Vendor Systems",
    "subcategory": "Rockwell Automation",
    "description": "Cloud MES — production tracking, quality management, traceability, shipping/receiving, machine monitoring, supplier management",
    "vendor_examples": "Plex Smart Manufacturing Platform",
    "protocol": "REST API / SQL",
    "ingest_method": "TA (API poll) or DB Connect",
    "splunk_sourcetype": "rockwell:plex:production, rockwell:plex:quality",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.5.1",
      "14.5.2",
      "14.5.3"
    ]
  },
  {
    "id": "rockwell_fiix",
    "name": "Rockwell Fiix (CMMS)",
    "category": "OT Vendor Systems",
    "subcategory": "Rockwell Automation",
    "description": "Cloud CMMS — work orders, preventive maintenance schedules, asset history, parts inventory, failure codes, meter readings",
    "vendor_examples": "Fiix CMMS (Rockwell Automation)",
    "protocol": "REST API",
    "ingest_method": "TA (API poll)",
    "splunk_sourcetype": "rockwell:fiix:workorder, rockwell:fiix:asset",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.05,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.05,
          "high": 0.3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 1000,
          "high": 2500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.4.1",
      "14.4.2",
      "14.4.3",
      "14.4.4"
    ]
  },
  {
    "id": "rockwell_thinmanager",
    "name": "Rockwell ThinManager",
    "category": "OT Vendor Systems",
    "subcategory": "Rockwell Automation",
    "description": "Thin client / terminal management — session logs, user authentication, terminal status, configuration changes, display assignments",
    "vendor_examples": "Rockwell ThinManager",
    "protocol": "Windows Event Log / SQL",
    "ingest_method": "UF (WinEventLog) or DB Connect",
    "splunk_sourcetype": "rockwell:thinmgr:session, rockwell:thinmgr:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.5,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "2.5.1",
      "2.5.2"
    ]
  },
  {
    "id": "schneider_ecostruxure_plant",
    "name": "Schneider EcoStruxure Plant (SCADA / DCS)",
    "category": "OT Vendor Systems",
    "subcategory": "Schneider Electric",
    "description": "Plant operations — Wonderware/AVEVA System Platform alarms, InTouch HMI events, historian data, batch records, Modicon PLC diagnostics",
    "vendor_examples": "EcoStruxure Plant, Wonderware System Platform, InTouch, Citect SCADA",
    "protocol": "OPC UA / SQL / Historian API",
    "ingest_method": "DB Connect (historian SQL) or OPC UA → Edge Hub",
    "splunk_sourcetype": "schneider:ecostruxure:alarm, schneider:ecostruxure:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 15,
        "min": 0,
        "profilePresets": {
          "low": 2,
          "typical": 15,
          "high": 150
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.3.1",
      "14.5.1"
    ]
  },
  {
    "id": "schneider_ecostruxure_building",
    "name": "Schneider EcoStruxure Building (BMS)",
    "category": "OT Vendor Systems",
    "subcategory": "Schneider Electric",
    "description": "Building management — HVAC alarms, occupancy trends, energy consumption, equipment schedules, BACnet point values, fire/access integration",
    "vendor_examples": "EcoStruxure Building Operation (EBO), SmartStruxure, TAC Vista",
    "protocol": "BACnet/IP / REST API / SQL",
    "ingest_method": "BACnet gateway → HEC, or DB Connect, or API poll",
    "splunk_sourcetype": "schneider:building:alarm, schneider:building:trend, schneider:building:energy",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.45",
      "14.1.46",
      "14.3.24",
      "14.3.1"
    ]
  },
  {
    "id": "schneider_ecostruxure_power",
    "name": "Schneider EcoStruxure Power (EMS)",
    "category": "OT Vendor Systems",
    "subcategory": "Schneider Electric",
    "description": "Electrical distribution monitoring — power quality, demand management, breaker status, transformer health, ION meter readings, power factor",
    "vendor_examples": "EcoStruxure Power Monitoring Expert (PME), EcoStruxure Power Operation",
    "protocol": "Modbus / SQL / REST API",
    "ingest_method": "DB Connect (SQL) or Modbus gateway → HEC",
    "splunk_sourcetype": "schneider:power:meter, schneider:power:alarm, schneider:power:quality",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.5.1",
      "14.5.2"
    ]
  },
  {
    "id": "schneider_triconex",
    "name": "Schneider Triconex (Safety System / SIS)",
    "category": "OT Vendor Systems",
    "subcategory": "Schneider Electric",
    "description": "Triple-modular-redundant SIS — safety trip records, SOE logs, voted logic events, diagnostic faults, bypass status, proof test records",
    "vendor_examples": "Schneider Triconex Tricon, Trident, Tri-GP",
    "protocol": "SOE export / Proprietary / OPC",
    "ingest_method": "UF (SOE file export) or OPC → middleware",
    "splunk_sourcetype": "schneider:triconex:soe, schneider:triconex:trip, schneider:triconex:diag",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.1,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.1,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.15",
      "14.2.25",
      "14.9.1"
    ]
  },
  {
    "id": "schneider_powerlogic",
    "name": "Schneider PowerLogic Meters",
    "category": "OT Vendor Systems",
    "subcategory": "Schneider Electric",
    "description": "Power metering — voltage, current, power factor, harmonic distortion, demand, energy accumulation from PM/ION series digital meters",
    "vendor_examples": "Schneider PowerLogic PM5000/PM8000, ION7400/9000 series",
    "protocol": "Modbus TCP / BACnet / Gateway software",
    "ingest_method": "Modbus gateway → HEC, or DB Connect (EcoStruxure PME SQL)",
    "splunk_sourcetype": "schneider:powerlogic:meter, schneider:powerlogic:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.5,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 0.5,
          "high": 3
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.5.1",
      "14.5.2"
    ]
  },
  {
    "id": "abb_ability",
    "name": "ABB Ability Platform (IoT / APM)",
    "category": "OT Vendor Systems",
    "subcategory": "ABB",
    "description": "Industrial IoT cloud — condition monitoring KPIs, predictive maintenance alerts, fleet analytics, remote diagnostics for motors/drives/robots",
    "vendor_examples": "ABB Ability, ABB Ability Genix",
    "protocol": "REST API / MQTT",
    "ingest_method": "TA (API poll) or MQTT → HEC",
    "splunk_sourcetype": "abb:ability:telemetry, abb:ability:alert",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.4.1",
      "14.5.1"
    ]
  },
  {
    "id": "abb_800xa",
    "name": "ABB 800xA (DCS)",
    "category": "OT Vendor Systems",
    "subcategory": "ABB",
    "description": "Distributed control system — process alarms, batch events, SOE, operator actions, device diagnostics, AC800M controller logs, system audit",
    "vendor_examples": "ABB Ability Symphony Plus, ABB 800xA",
    "protocol": "OPC / SQL / Proprietary (800xA Information Mgmt)",
    "ingest_method": "OPC → Edge Hub, or DB Connect (historian SQL)",
    "splunk_sourcetype": "abb:800xa:alarm, abb:800xa:event, abb:800xa:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 30,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 30,
          "high": 300
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "abb_robotics",
    "name": "ABB Robotics (IRC5 / OmniCore)",
    "category": "OT Vendor Systems",
    "subcategory": "ABB",
    "description": "Industrial robot controllers — cycle logs, error/fault events, production counters, axis diagnostics, safety events, program changes",
    "vendor_examples": "ABB IRC5, ABB OmniCore, ABB RobotStudio",
    "protocol": "OPC UA / File logs / Robot Web Services API",
    "ingest_method": "OPC UA → Edge Hub, or UF on cell gateway",
    "splunk_sourcetype": "abb:robot:event, abb:robot:cycle, abb:robot:fault",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.4.1",
      "14.5.1",
      "14.5.2"
    ]
  },
  {
    "id": "honeywell_experion",
    "name": "Honeywell Experion PKS (DCS)",
    "category": "OT Vendor Systems",
    "subcategory": "Honeywell",
    "description": "Distributed control system — process alarms, SOE, batch events, operator actions, C300 controller diagnostics, safety (SIL) events, audit trail",
    "vendor_examples": "Honeywell Experion PKS (Process Knowledge System)",
    "protocol": "OPC / SQL / Honeywell Uniformance",
    "ingest_method": "OPC → Edge Hub, or DB Connect (PHD/Uniformance SQL)",
    "splunk_sourcetype": "honeywell:experion:alarm, honeywell:experion:soe, honeywell:experion:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 30,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 30,
          "high": 300
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "honeywell_phd",
    "name": "Honeywell Uniformance / PHD (Historian)",
    "category": "OT Vendor Systems",
    "subcategory": "Honeywell",
    "description": "Process historian — compressed time-series, calculated tags, alarm history, batch context; SQL/ODBC access for aggregated exports",
    "vendor_examples": "Honeywell Uniformance Suite, PHD (Process History Database)",
    "protocol": "SQL (ODBC) / OPC / REST API",
    "ingest_method": "DB Connect (SQL views for KPIs/aggregates)",
    "splunk_sourcetype": "honeywell:phd:tag, honeywell:phd:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.2.16",
      "14.2.25",
      "14.2.26"
    ]
  },
  {
    "id": "honeywell_bms",
    "name": "Honeywell Building Management (EBI / WEBs)",
    "category": "OT Vendor Systems",
    "subcategory": "Honeywell",
    "description": "Building automation — HVAC alarms, setpoint changes, energy metering, occupancy, fire panel integration, access control events",
    "vendor_examples": "Honeywell EBI (Enterprise Buildings Integrator), Honeywell WEBs, Tridium-based",
    "protocol": "BACnet/IP / SQL / REST API",
    "ingest_method": "BACnet gateway → HEC, or DB Connect",
    "splunk_sourcetype": "honeywell:bms:alarm, honeywell:bms:trend, honeywell:bms:energy",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.45",
      "14.1.46",
      "14.3.24",
      "14.3.1"
    ]
  },
  {
    "id": "emerson_deltav",
    "name": "Emerson DeltaV (DCS)",
    "category": "OT Vendor Systems",
    "subcategory": "Emerson",
    "description": "Distributed control system — process alarms, batch (ISA-88), SOE, operator actions, module diagnostics, DeltaV SIS safety events, audit trail",
    "vendor_examples": "Emerson DeltaV (v14/v15), DeltaV SIS, DeltaV Batch",
    "protocol": "OPC / SQL (DeltaV Chronicle) / DeltaV APIs",
    "ingest_method": "OPC → Edge Hub, or DB Connect (Chronicle/Continuous Historian SQL)",
    "splunk_sourcetype": "emerson:deltav:alarm, emerson:deltav:batch, emerson:deltav:soe, emerson:deltav:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 30,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 30,
          "high": 300
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "emerson_ovation",
    "name": "Emerson Ovation (DCS - Power Generation)",
    "category": "OT Vendor Systems",
    "subcategory": "Emerson",
    "description": "Power generation DCS — turbine/boiler alarms, SOE, unit trip records, combustion diagnostics, NERC CIP audit logs",
    "vendor_examples": "Emerson Ovation (power plant DCS)",
    "protocol": "OPC / SQL / File exports",
    "ingest_method": "OPC → Edge Hub, or DB Connect, or UF (SOE files)",
    "splunk_sourcetype": "emerson:ovation:alarm, emerson:ovation:soe, emerson:ovation:trip",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 20,
        "min": 0,
        "profilePresets": {
          "low": 3,
          "typical": 20,
          "high": 200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "emerson_plantweb",
    "name": "Emerson Plantweb / AMS Device Manager",
    "category": "OT Vendor Systems",
    "subcategory": "Emerson",
    "description": "Asset performance management — smart device diagnostics (HART/FF), calibration records, device alerts, predictive health scores",
    "vendor_examples": "Emerson Plantweb Optics, AMS Device Manager, AMS Machinery Manager",
    "protocol": "SQL / REST API",
    "ingest_method": "DB Connect (SQL) or TA (API poll)",
    "splunk_sourcetype": "emerson:ams:device, emerson:ams:alert, emerson:ams:calibration",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.3,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.3,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1000,
        "min": 0,
        "profilePresets": {
          "low": 400,
          "typical": 1000,
          "high": 2500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.1",
      "14.3.6",
      "14.4.1",
      "14.5.1"
    ]
  },
  {
    "id": "ge_proficy_historian",
    "name": "GE Proficy Historian",
    "category": "OT Vendor Systems",
    "subcategory": "GE Vernova",
    "description": "Industrial historian — compressed time-series tags, calculated points, alarm history, batch context; SQL/OPC/Web API access for exports",
    "vendor_examples": "GE Proficy Historian (formerly Intellution iHistorian)",
    "protocol": "SQL / OPC / REST (Web API) / CSV",
    "ingest_method": "DB Connect (SQL) or TA (Web API poll)",
    "splunk_sourcetype": "ge:proficy:tag, ge:proficy:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.2.16",
      "14.2.25",
      "14.2.26"
    ]
  },
  {
    "id": "ge_ifix",
    "name": "GE iFIX / CIMPLICITY (SCADA)",
    "category": "OT Vendor Systems",
    "subcategory": "GE Vernova",
    "description": "SCADA/HMI — alarm history, operator audit, trend data, recipe management, VBA script events; part of Proficy suite",
    "vendor_examples": "GE iFIX, GE CIMPLICITY, GE Proficy Plant Applications",
    "protocol": "OPC / SQL / File logs",
    "ingest_method": "OPC → Edge Hub, or DB Connect, or UF (log files)",
    "splunk_sourcetype": "ge:ifix:alarm, ge:ifix:audit, ge:cimplicity:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "ge_mark_vie",
    "name": "GE Mark VIe (Turbine Control)",
    "category": "OT Vendor Systems",
    "subcategory": "GE Vernova",
    "description": "Gas/steam turbine control — trip logs, SOE, diagnostic alarms, vibration snapshots, combustion tuning events, protective relay actions",
    "vendor_examples": "GE Mark VIe, Mark VIeS (safety), EX2100e (excitation)",
    "protocol": "Proprietary / OPC / SOE file export",
    "ingest_method": "UF (SOE/trip file export) or OPC → middleware",
    "splunk_sourcetype": "ge:markvie:trip, ge:markvie:soe, ge:markvie:diag",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "yokogawa_centum",
    "name": "Yokogawa CENTUM VP (DCS)",
    "category": "OT Vendor Systems",
    "subcategory": "Yokogawa",
    "description": "Distributed control system — process alarms, SOE, batch (ISA-88), operator actions, FCS controller diagnostics, system audit, Exaopc data",
    "vendor_examples": "Yokogawa CENTUM VP, CENTUM CS 3000 (legacy)",
    "protocol": "OPC (Exaopc) / SQL / File exports",
    "ingest_method": "OPC → Edge Hub, or DB Connect (historian SQL)",
    "splunk_sourcetype": "yokogawa:centum:alarm, yokogawa:centum:soe, yokogawa:centum:batch",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 25,
        "min": 0,
        "profilePresets": {
          "low": 5,
          "typical": 25,
          "high": 250
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 800,
        "min": 0,
        "profilePresets": {
          "low": 300,
          "typical": 800,
          "high": 2000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "yokogawa_prosafe",
    "name": "Yokogawa ProSafe-RS (SIS)",
    "category": "OT Vendor Systems",
    "subcategory": "Yokogawa",
    "description": "Safety instrumented system — safety trip records, SOE, voted logic events, diagnostic faults, proof test results, bypass status",
    "vendor_examples": "Yokogawa ProSafe-RS (IEC 61508 SIL3)",
    "protocol": "SOE export / OPC / Vnet/IP integration",
    "ingest_method": "UF (SOE file export) or OPC → Edge Hub",
    "splunk_sourcetype": "yokogawa:prosafe:soe, yokogawa:prosafe:trip, yokogawa:prosafe:diag",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.1,
        "min": 0,
        "profilePresets": {
          "low": 0.01,
          "typical": 0.1,
          "high": 50
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.15",
      "14.2.25",
      "14.9.1"
    ]
  },
  {
    "id": "aveva_pi_system",
    "name": "AVEVA PI System (Data Archive)",
    "category": "OT Vendor Systems",
    "subcategory": "AVEVA / OSIsoft",
    "description": "Enterprise historian — PI points (time-series), AF (Asset Framework) metadata, event frames, notifications, PI audit trail; PI Web API for Splunk export",
    "vendor_examples": "AVEVA PI Data Archive, PI AF, PI Vision, PI Integrator for Business Analytics",
    "protocol": "PI Web API / PI Integrator / SQL (OLEDB) / CSV",
    "ingest_method": "PI Web API → HEC, or PI Integrator, or DB Connect",
    "splunk_sourcetype": "aveva:pi:tag, aveva:pi:event, aveva:pi:notification, aveva:pi:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 20,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 20,
          "high": 200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.2.16",
      "14.2.25",
      "14.2.26"
    ]
  },
  {
    "id": "aveva_system_platform",
    "name": "AVEVA System Platform / InTouch (SCADA)",
    "category": "OT Vendor Systems",
    "subcategory": "AVEVA / OSIsoft",
    "description": "Enterprise SCADA — alarm journal, operator audit, InTouch HMI events, Galaxy namespace changes, redundancy switchover, script events",
    "vendor_examples": "AVEVA System Platform (formerly Wonderware), InTouch HMI, OMI",
    "protocol": "SQL / OPC / Historian API",
    "ingest_method": "DB Connect (alarm/event SQL) or OPC → Edge Hub",
    "splunk_sourcetype": "aveva:scada:alarm, aveva:scada:audit, aveva:intouch:event",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "aveva_historian",
    "name": "AVEVA Historian (Wonderware)",
    "category": "OT Vendor Systems",
    "subcategory": "AVEVA / OSIsoft",
    "description": "Plant historian — time-series tag storage, summary data, alarm history; SQL Server-based with IDAS interfaces to PLCs and SCADA",
    "vendor_examples": "AVEVA Historian (formerly Wonderware Historian), InSQL",
    "protocol": "SQL (IDAS) / OPC / REST",
    "ingest_method": "DB Connect (SQL views for KPIs/aggregates)",
    "splunk_sourcetype": "aveva:historian:tag, aveva:historian:alarm",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 100
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.2.16",
      "14.2.25",
      "14.2.26"
    ]
  },
  {
    "id": "jci_metasys",
    "name": "Johnson Controls Metasys (BMS)",
    "category": "OT Vendor Systems",
    "subcategory": "Johnson Controls",
    "description": "Building automation — HVAC alarms, trend data, schedule events, setpoint changes, equipment status, energy optimization, BACnet integration",
    "vendor_examples": "Johnson Controls Metasys (ADS/ADX server), NAE/NIE controllers",
    "protocol": "BACnet/IP / SQL (ADS) / REST API (Metasys 12+)",
    "ingest_method": "BACnet gateway → HEC, or DB Connect (ADS SQL)",
    "splunk_sourcetype": "jci:metasys:alarm, jci:metasys:trend, jci:metasys:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.45",
      "14.1.46",
      "14.3.24",
      "14.3.1"
    ]
  },
  {
    "id": "tridium_niagara",
    "name": "Tridium Niagara Framework (BMS / IoT)",
    "category": "OT Vendor Systems",
    "subcategory": "Tridium",
    "description": "Multi-protocol BMS framework — alarm records, audit trail, point history, BACnet/Modbus/LonWorks integration, JACE controllers, Niagara Supervisor",
    "vendor_examples": "Tridium Niagara 4, JACE 8000, Niagara Supervisor (Honeywell-owned)",
    "protocol": "BACnet / Modbus / REST (Fox protocol) / MQTT modules",
    "ingest_method": "Custom module → HEC, or DB Connect (history DB)",
    "splunk_sourcetype": "tridium:niagara:alarm, tridium:niagara:history, tridium:niagara:audit",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 2,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 2,
          "high": 20
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 5,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 5,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.1.45",
      "14.1.46",
      "14.3.24",
      "14.3.1"
    ]
  },
  {
    "id": "ignition_scada",
    "name": "Inductive Automation Ignition (SCADA / MES)",
    "category": "OT Vendor Systems",
    "subcategory": "Inductive Automation",
    "description": "Unified SCADA/MES — alarm journal, tag historian, audit trail, transaction groups, Perspective/Vision HMI events, MES module (production/track-and-trace)",
    "vendor_examples": "Ignition by Inductive Automation (Gateway + modules)",
    "protocol": "SQL (MySQL/PostgreSQL/MSSQL) / MQTT (Sparkplug B) / OPC UA / REST",
    "ingest_method": "DB Connect (alarm/tag historian SQL), or MQTT → HEC, or Kafka module",
    "splunk_sourcetype": "ignition:alarm, ignition:audit, ignition:tag, ignition:transaction",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 15,
        "min": 0,
        "profilePresets": {
          "low": 2,
          "typical": 15,
          "high": 200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25",
      "14.3.1"
    ]
  },
  {
    "id": "copadata_zenon",
    "name": "COPA-DATA zenon (SCADA / EMS)",
    "category": "OT Vendor Systems",
    "subcategory": "COPA-DATA",
    "description": "SCADA/HMI + energy management — alarms, trends, batch (ISA-88), energy reporting, IEC 61850 substation automation, FDA 21 CFR Part 11 audit",
    "vendor_examples": "COPA-DATA zenon",
    "protocol": "SQL / OPC UA / REST API / File exports",
    "ingest_method": "DB Connect (SQL) or OPC UA → Edge Hub",
    "splunk_sourcetype": "zenon:alarm, zenon:event, zenon:energy",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 10,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 10,
          "high": 80
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 600,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 600,
          "high": 1500
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "vtscada",
    "name": "VTScada (Utilities SCADA)",
    "category": "OT Vendor Systems",
    "subcategory": "VTScada",
    "description": "All-in-one SCADA for water/wastewater/utilities — alarms, historian, operator events, communication diagnostics, built-in redundancy, thin client access logs",
    "vendor_examples": "VTScada by Trihedral Engineering",
    "protocol": "SQL / OPC / REST API / File logs",
    "ingest_method": "DB Connect (historian SQL) or UF (log files)",
    "splunk_sourcetype": "vtscada:alarm, vtscada:event, vtscada:history",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 8,
        "min": 0,
        "profilePresets": {
          "low": 1,
          "typical": 8,
          "high": 60
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.3.38",
      "14.2.1",
      "14.2.15",
      "14.2.25"
    ]
  },
  {
    "id": "beckhoff_twincat",
    "name": "Beckhoff TwinCAT (PLC / Motion)",
    "category": "OT Vendor Systems",
    "subcategory": "Beckhoff",
    "description": "Software PLC on IPC — ADS logs, scope data, TwinCAT Analytics, controller diagnostics, motion axis events, IoT connectivity via MQTT/OPC UA",
    "vendor_examples": "Beckhoff TwinCAT 3 (XAE/XAR), TwinCAT IoT, TwinCAT Analytics",
    "protocol": "OPC UA / MQTT / ADS (proprietary) / TwinCAT Analytics",
    "ingest_method": "OPC UA → Edge Hub, or MQTT → HEC",
    "splunk_sourcetype": "beckhoff:twincat:event, beckhoff:twincat:diag",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 30
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.3.32",
      "14.9.1"
    ]
  },
  {
    "id": "phoenix_plcnext",
    "name": "Phoenix Contact PLCnext (Edge PLC)",
    "category": "OT Vendor Systems",
    "subcategory": "Phoenix Contact",
    "description": "Linux-based edge PLC — app logs, diagnostics, OPC UA server, MQTT publisher, container workload metrics, PROFINET/Modbus device data",
    "vendor_examples": "Phoenix Contact PLCnext Control (AXC F 2152/3152), PLCnext Engineer",
    "protocol": "OPC UA / MQTT / REST / Syslog (Linux)",
    "ingest_method": "MQTT → HEC, or OPC UA → Edge Hub, or SC4S (syslog)",
    "splunk_sourcetype": "phoenix:plcnext:event, phoenix:plcnext:diag",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 3,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 3,
          "high": 20
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 400,
        "min": 0,
        "profilePresets": {
          "low": 150,
          "typical": 400,
          "high": 1000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.3.32",
      "14.3.42"
    ]
  },
  {
    "id": "wago_pfc",
    "name": "WAGO PFC Controllers (PLC / Edge)",
    "category": "OT Vendor Systems",
    "subcategory": "WAGO",
    "description": "Compact Linux-based PLC — CODESYS runtime diagnostics, MQTT publish, OPC UA server, Node-RED flows, BACnet, KNX for building automation",
    "vendor_examples": "WAGO PFC100, PFC200, Compact Controller 100, Touch Panel 600",
    "protocol": "MQTT / OPC UA / Modbus / BACnet",
    "ingest_method": "MQTT → HEC, or OPC UA → Edge Hub",
    "splunk_sourcetype": "wago:pfc:event, wago:pfc:telemetry",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 5,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 3,
          "typical": 5,
          "high": 50
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 15
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 300,
        "min": 0,
        "profilePresets": {
          "low": 100,
          "typical": 300,
          "high": 800
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.1",
      "14.2.7",
      "14.3.32",
      "14.3.1"
    ]
  },
  {
    "id": "fanuc_cnc",
    "name": "Fanuc CNC Controllers",
    "category": "OT Vendor Systems",
    "subcategory": "Fanuc",
    "description": "CNC machine tool controllers — alarm history, parameter changes, production counters, spindle load, MTConnect data, FOCAS diagnostics",
    "vendor_examples": "Fanuc 30i/31i/32i, 0i-Plus, Series 35i",
    "protocol": "MTConnect / FOCAS (Ethernet) / OPC UA adapter",
    "ingest_method": "MTConnect agent → HEC, or FOCAS middleware → HEC",
    "splunk_sourcetype": "fanuc:cnc:alarm, fanuc:cnc:production, fanuc:cnc:mtconnect",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 2,
        "min": 0,
        "profilePresets": {
          "low": 0.5,
          "typical": 2,
          "high": 10
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.5.1",
      "14.5.2",
      "14.4.1"
    ]
  },
  {
    "id": "fanuc_robotics",
    "name": "Fanuc Robotics (R-30iB / R-50iA)",
    "category": "OT Vendor Systems",
    "subcategory": "Fanuc",
    "description": "Industrial robot controllers — cycle logs, fault/error events, production counters, axis torque, program changes, collision detection events",
    "vendor_examples": "Fanuc R-30iB Plus, R-50iA, CRX collaborative robots",
    "protocol": "FOCAS / OPC UA adapter / File logs",
    "ingest_method": "FOCAS middleware → HEC, or UF on cell gateway",
    "splunk_sourcetype": "fanuc:robot:event, fanuc:robot:fault, fanuc:robot:cycle",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.4.1",
      "14.5.1",
      "14.5.2"
    ]
  },
  {
    "id": "kuka_robotics",
    "name": "KUKA Robotics (KRC5 / KRC4)",
    "category": "OT Vendor Systems",
    "subcategory": "KUKA",
    "description": "Industrial robot controllers — XML event logs, error/warning events, cycle diagnostics, safety events, program changes, motion metrics",
    "vendor_examples": "KUKA KRC5, KRC4, LBR iiwa (collaborative), KMR (mobile)",
    "protocol": "OPC UA / XML logs / EthernetKRL / RSI",
    "ingest_method": "OPC UA → Edge Hub, or UF on cell gateway (XML logs)",
    "splunk_sourcetype": "kuka:robot:event, kuka:robot:fault, kuka:robot:cycle",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 5,
          "typical": 10,
          "high": 100
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 1,
        "min": 0,
        "profilePresets": {
          "low": 0.1,
          "typical": 1,
          "high": 5
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 500,
        "min": 0,
        "profilePresets": {
          "low": 200,
          "typical": 500,
          "high": 1200
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.2.12",
      "14.4.1",
      "14.5.1",
      "14.5.2"
    ]
  },
  {
    "id": "ibm_maximo",
    "name": "IBM Maximo (CMMS / EAM)",
    "category": "OT Vendor Systems",
    "subcategory": "IBM",
    "description": "Enterprise asset management — work orders, preventive maintenance, asset registry, failure codes, inventory, inspection records, IoT integrations",
    "vendor_examples": "IBM Maximo Application Suite (MAS), Maximo Manage, Maximo Health",
    "protocol": "REST API (OSLC/JSON) / SQL / Kafka",
    "ingest_method": "TA (API poll) or DB Connect (SQL)",
    "splunk_sourcetype": "ibm:maximo:workorder, ibm:maximo:asset, ibm:maximo:meter",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.3,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.3,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.4.1",
      "14.4.2",
      "14.4.3",
      "14.4.4"
    ]
  },
  {
    "id": "sap_pm",
    "name": "SAP Plant Maintenance (PM / EAM)",
    "category": "OT Vendor Systems",
    "subcategory": "SAP",
    "description": "Enterprise maintenance management — maintenance notifications, work orders, equipment master, functional locations, measuring points, warranty tracking",
    "vendor_examples": "SAP PM, SAP S/4HANA Asset Management, SAP Intelligent Asset Management",
    "protocol": "REST (OData) / RFC / SQL (HANA)",
    "ingest_method": "TA (OData API poll) or DB Connect",
    "splunk_sourcetype": "sap:pm:notification, sap:pm:workorder, sap:pm:equipment",
    "calibration": "pending",
    "drivers": [
      {
        "id": "endpoints",
        "label": "Number of endpoints",
        "unit": "devices",
        "type": "number",
        "default": 1,
        "min": 1,
        "max": 100000,
        "profilePresets": {
          "low": 1,
          "typical": 1,
          "high": 10
        }
      },
      {
        "id": "eps_per_endpoint",
        "label": "EPS per endpoint",
        "unit": "eps",
        "type": "number",
        "default": 0.3,
        "min": 0,
        "profilePresets": {
          "low": 0.05,
          "typical": 0.3,
          "high": 2
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      },
      {
        "id": "bytes_per_event",
        "label": "Bytes per event",
        "unit": "bytes",
        "type": "number",
        "default": 1200,
        "min": 0,
        "profilePresets": {
          "low": 500,
          "typical": 1200,
          "high": 3000
        },
        "help": "Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs."
      }
    ],
    "compute": "endpoint_legacy_v1",
    "uncertainty": {
      "low": 0.5,
      "typical": 1,
      "high": 2
    },
    "realism": {
      "rawdata_compression_typical": 0.15,
      "tsidx_overhead_typical": 0.35,
      "filterable_fraction_typical": 0.15
    },
    "citations": [],
    "related_uc_ids": [
      "14.4.1",
      "14.4.2",
      "14.5.1",
      "23.2.1"
    ]
  }
];

if (typeof module !== "undefined" && module.exports) {
  module.exports = global.OT_DATA_SOURCES || window.OT_DATA_SOURCES;
}
