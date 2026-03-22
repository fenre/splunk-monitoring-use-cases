#!/usr/bin/env python3
"""
Regenerate dashboards/catalog-quick-start-top2.json after changing Quick Start
lists in use-cases/INDEX.md (top two bullets per category).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboards" / "catalog-quick-start-top2.json"

BG = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNDQwIiBoZWlnaHQ9IjIxMDAiPjxkZWZzPjxsaW5lYXJHcmFkaWVudCBpZD0iZyIgeDE9IjAiIHkxPSIwIiB4Mj0iMSIgeTI9IjEiPjxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiMwYzE4MjgiLz48c3RvcCBvZmZzZXQ9IjUwJSIgc3RvcC1jb2xvcj0iIzBhMTQyMCIvPjxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iIzA1MGExMiIvPjwvbGluZWFyR3JhZGllbnQ+PHBhdHRlcm4gaWQ9InAiIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTTMyIDBIMHYzMiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMWUzYTVmIiBzdHJva2Utd2lkdGg9IjAuMzUiIG9wYWNpdHk9IjAuMjUiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxNDQwIiBoZWlnaHQ9IjIxMDAiIGZpbGw9InVybCgjZykiLz48cmVjdCB3aWR0aD0iMTQ0MCIgaGVpZ2h0PSIyMTAwIiBmaWxsPSJ1cmwoI3ApIiBvcGFjaXR5PSIwLjQiLz48L3N2Zz4="
)

UC_IDS = (
    "UC-1.1.23,UC-1.1.36,UC-2.1.7,UC-2.2.3,UC-3.2.7,UC-3.2.8,UC-4.1.2,UC-4.1.7,UC-5.1.1,UC-5.1.4,"
    "UC-6.1.2,UC-6.1.4,UC-7.1.2,UC-7.1.3,UC-8.1.1,UC-8.2.1,UC-9.1.3,UC-9.1.5,UC-10.1.2,UC-10.1.4,"
    "UC-11.1.8,UC-11.1.1,UC-12.1.4,UC-12.2.5,UC-13.1.1,UC-13.2.1,UC-14.1.2,UC-14.1.6,UC-15.1.1,UC-15.1.6,"
    "UC-16.1.2,UC-16.1.9,UC-17.2.3,UC-17.2.8,UC-18.2.5,UC-18.2.1,UC-19.1.1,UC-19.1.5,UC-20.1.1,UC-20.1.4,"
    "UC-21.1.1,UC-21.2.1,UC-22.1.1,UC-22.2.1"
)

TITLES = "###".join(
    [
        "Kernel Core Dump Generation",
        "Multipath I/O Failover Events",
        "HA Failover Events",
        "Cluster Shared Volume Health",
        "Control Plane Health",
        "etcd Cluster Health",
        "Root Account Usage",
        "S3 Bucket Policy Changes",
        "Interface Up/Down Events",
        "BGP Peer State Changes",
        "Storage Latency Monitoring",
        "Disk Failure Alerts",
        "Deadlock Monitoring",
        "Connection Pool Exhaustion",
        "HTTP Error Rate Monitoring",
        "JVM Heap Utilization",
        "Privileged Group Membership Changes",
        "Kerberos Ticket Anomalies",
        "Wildfire / Sandbox Verdicts",
        "DNS Sinkhole Hits",
        "Inbox Rule Monitoring",
        "Mail Flow Health Monitoring",
        "Secret Exposure Detection",
        "Failed Deployment Tracking",
        "Indexer Queue Fill Ratio",
        "Service Health Score Trending",
        "UPS Battery Monitoring",
        "Environmental Compliance",
        "UPS Battery Health",
        "Circuit Breaker Trips",
        "SLA Compliance Monitoring",
        "Change-Incident Correlation",
        "Geo-Location Anomalies",
        "Simultaneous Session Detection",
        "Transport Node Connectivity",
        "Distributed Firewall Rule Hits",
        "Blade/Rack Server Health",
        "FI Port Channel Health",
        "Daily Spend Trending",
        "Idle Resource Identification",
        "SCADA RTU Communication Health",
        "PLC Program Change Detection",
        "GDPR PII Detection in Application Log Data",
        "NIS2 Incident Detection and 24-Hour Early Warning Reporting",
    ]
)

CATS = "###".join(
    [
        "Server & Compute",
        "Server & Compute",
        "Virtualization",
        "Virtualization",
        "Containers & Orchestration",
        "Containers & Orchestration",
        "Cloud Infrastructure",
        "Cloud Infrastructure",
        "Network Infrastructure",
        "Network Infrastructure",
        "Storage & Backup",
        "Storage & Backup",
        "Database & Data Platforms",
        "Database & Data Platforms",
        "Application Infrastructure",
        "Application Infrastructure",
        "Identity & Access Management",
        "Identity & Access Management",
        "Security Infrastructure",
        "Security Infrastructure",
        "Email & Collaboration",
        "Email & Collaboration",
        "DevOps & CI/CD",
        "DevOps & CI/CD",
        "Observability & Monitoring Stack",
        "Observability & Monitoring Stack",
        "IoT & Operational Technology (OT)",
        "IoT & Operational Technology (OT)",
        "Data Center Physical Infrastructure",
        "Data Center Physical Infrastructure",
        "Service Management & ITSM",
        "Service Management & ITSM",
        "Network Security & Zero Trust",
        "Network Security & Zero Trust",
        "Data Center Fabric & SDN",
        "Data Center Fabric & SDN",
        "Compute Infrastructure (HCI & Converged)",
        "Compute Infrastructure (HCI & Converged)",
        "Cost & Capacity Management",
        "Cost & Capacity Management",
        "Industry Verticals",
        "Industry Verticals",
        "Regulatory and Compliance Frameworks",
        "Regulatory and Compliance Frameworks",
    ]
)

SHORT = (
    "Srv,Virt,K8s,Cloud,Net,Stor,DB,App,IAM,Sec,Collab,DevOps,Obs,IoT,DCphys,ITSM,ZT,SDN,HCI,Cost,Ind,Gov"
)


def spl_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_base() -> str:
    return (
        "| makeresults count=44 "
        "| streamstats count as i "
        "| eval category_id=ceil(i/2) "
        f'| eval uc_id=mvindex(split("{UC_IDS}",","),i-1) '
        f'| eval title=mvindex(split("{spl_escape(TITLES)}","###"),i-1) '
        f'| eval category=mvindex(split("{spl_escape(CATS)}","###"),i-1) '
        f'| eval cat_short=mvindex(split("{SHORT}",","),category_id-1) '
        "| eval events_24h=4200+((i*133)%8700)+category_id*211 "
        "| eval health_score=72+((i*17)%26) "
        "| eval coverage_pct=68+((i*11)%32) "
        '| eval status=case(health_score>=88,"Healthy",health_score>=75,"Watch",1=1,"Critical") '
        "| eval trend_pct=round(((i*3)%8)-2,1) "
    )


def main() -> None:
    base = build_base()
    ds_table = (
        base
        + '| table category_id cat_short category uc_id title events_24h health_score coverage_pct status trend_pct '
        + '| rename category_id as "Cat" cat_short as "Cat code" category as "Category" uc_id as "UC ID" '
        'title as "Use case" events_24h as "Events (24h)" health_score as "Health" coverage_pct as "Coverage %" '
        'status as "Status" trend_pct as "Trend" '
    )
    ds_cat = base + "| stats sum(events_24h) as events by cat_short | sort cat_short "
    ds_kpi_sum = base + "| stats sum(events_24h) as total_events | fields total_events"
    ds_kpi_health = base + "| stats avg(health_score) as avg_health | eval avg_health=round(avg_health,1) | fields avg_health"
    ds_kpi_risk = (
        base
        + '| stats sum(eval(if(status!="Healthy",1,0))) as at_risk | fields at_risk'
    )
    ds_kpi_mon = "| makeresults | eval monitored=44 | fields monitored"
    ds_trend = (
        "| makeresults count=48 | streamstats count as i "
        '| eval _time=relative_time(now(), "-24h")+(i-1)*1800 '
        "| eval portfolio_signals=980000+(i%9)*12400+((i*37)%82000) "
        "| fields _time portfolio_signals "
    )

    dashboard = {
        "visualizations": {
            "bg_canvas": {"type": "splunk.image", "options": {"src": BG}},
            "lbl_title": {
                "type": "splunk.markdown",
                "options": {
                    "markdown": "## MONITORING CATALOG — QUICK START PORTFOLIO",
                    "fontColor": "#fafafa",
                },
            },
            "lbl_sub": {
                "type": "splunk.markdown",
                "options": {
                    "markdown": "Top 2 use cases per category (INDEX.md Quick Start) — **synthetic demo data** for executive review",
                    "fontColor": "#909090",
                },
            },
            "lbl_live": {"type": "splunk.markdown", "options": {"markdown": "\u25cf  DEMO", "fontColor": "#04A4B0"}},
            "k_lbl_0": {
                "type": "splunk.markdown",
                "options": {"markdown": "**TOTAL EVENTS (24H)**", "fontColor": "#909090"},
            },
            "k_viz_0": {
                "type": "splunk.singlevalue",
                "options": {
                    "backgroundColor": "transparent",
                    "sparklineDisplay": "off",
                    "trendDisplay": "off",
                    "unit": "",
                    "unitPosition": "after",
                    "numberPrecision": 0,
                    "shouldUseThousandSeparators": True,
                    "majorColor": "#3993ff",
                },
                "dataSources": {"primary": "ds_kpi_sum"},
            },
            "k_lbl_1": {
                "type": "splunk.markdown",
                "options": {"markdown": "**AVG HEALTH SCORE**", "fontColor": "#909090"},
            },
            "k_viz_1": {
                "type": "splunk.singlevalue",
                "options": {
                    "backgroundColor": "transparent",
                    "sparklineDisplay": "off",
                    "trendDisplay": "off",
                    "unit": "",
                    "unitPosition": "after",
                    "numberPrecision": 1,
                    "shouldUseThousandSeparators": True,
                    "majorColor": "> majorValue | rangeValue(majorColorEditorConfig)",
                },
                "dataSources": {"primary": "ds_kpi_health"},
                "context": {
                    "majorColorEditorConfig": [
                        {"value": "#FA5762", "to": 75},
                        {"value": "#F26722", "from": 75, "to": 85},
                        {"value": "#04A4B0", "from": 85},
                    ]
                },
            },
            "k_lbl_2": {
                "type": "splunk.markdown",
                "options": {"markdown": "**WATCH / CRITICAL**", "fontColor": "#909090"},
            },
            "k_viz_2": {
                "type": "splunk.singlevalue",
                "options": {
                    "backgroundColor": "transparent",
                    "sparklineDisplay": "off",
                    "trendDisplay": "off",
                    "unit": " UCs",
                    "unitPosition": "after",
                    "numberPrecision": 0,
                    "shouldUseThousandSeparators": True,
                    "majorColor": "> majorValue | rangeValue(majorColorEditorConfig)",
                },
                "dataSources": {"primary": "ds_kpi_risk"},
                "context": {
                    "majorColorEditorConfig": [
                        {"value": "#04A4B0", "to": 5},
                        {"value": "#F26722", "from": 5, "to": 12},
                        {"value": "#FA5762", "from": 12},
                    ]
                },
            },
            "k_lbl_3": {
                "type": "splunk.markdown",
                "options": {"markdown": "**MONITORED USE CASES**", "fontColor": "#909090"},
            },
            "k_viz_3": {
                "type": "splunk.singlevalue",
                "options": {
                    "backgroundColor": "transparent",
                    "sparklineDisplay": "off",
                    "trendDisplay": "off",
                    "unit": "",
                    "numberPrecision": 0,
                    "shouldUseThousandSeparators": True,
                    "majorColor": "#A974F7",
                },
                "dataSources": {"primary": "ds_kpi_mon"},
            },
            "s1_lbl": {
                "type": "splunk.markdown",
                "options": {"markdown": "**EVENTS BY CATEGORY**", "fontColor": "#A974F7"},
            },
            "cat_viz": {
                "type": "splunk.column",
                "dataSources": {"primary": "ds_cat"},
                "options": {
                    "backgroundColor": "transparent",
                    "seriesColors": ["#3993ff"],
                    "legendDisplay": "off",
                    "xAxisTitleVisibility": "hide",
                    "yAxisTitleVisibility": "hide",
                    "dataValuesDisplay": "off",
                },
            },
            "s2_lbl": {
                "type": "splunk.markdown",
                "options": {
                    "markdown": "**PORTFOLIO SIGNAL VOLUME**",
                    "fontColor": "#A974F7",
                },
            },
            "trend_viz": {
                "type": "splunk.area",
                "dataSources": {"primary": "ds_trend"},
                "options": {
                    "backgroundColor": "transparent",
                    "seriesColors": ["#04A4B0"],
                    "areaOpacity": 0.2,
                    "legendDisplay": "off",
                    "yAxisTitleVisibility": "hide",
                    "xAxisTitleVisibility": "hide",
                },
            },
            "s3_lbl": {
                "type": "splunk.markdown",
                "options": {"markdown": "**USE CASE DETAIL**", "fontColor": "#A974F7"},
            },
            "tbl_viz": {
                "type": "splunk.table",
                "dataSources": {"primary": "ds_table"},
                "options": {"backgroundColor": "transparent", "count": 50},
            },
        },
        "dataSources": {
            "ds_table": {
                "type": "ds.search",
                "options": {"query": ds_table, "queryParameters": {"earliest": "-24h@h", "latest": "now"}},
                "name": "ds_table",
            },
            "ds_cat": {
                "type": "ds.search",
                "options": {"query": ds_cat, "queryParameters": {"earliest": "-24h@h", "latest": "now"}},
                "name": "ds_cat",
            },
            "ds_kpi_sum": {
                "type": "ds.search",
                "options": {"query": ds_kpi_sum, "queryParameters": {"earliest": "-24h@h", "latest": "now"}},
                "name": "ds_kpi_sum",
            },
            "ds_kpi_health": {
                "type": "ds.search",
                "options": {"query": ds_kpi_health, "queryParameters": {"earliest": "-24h@h", "latest": "now"}},
                "name": "ds_kpi_health",
            },
            "ds_kpi_risk": {
                "type": "ds.search",
                "options": {"query": ds_kpi_risk, "queryParameters": {"earliest": "-24h@h", "latest": "now"}},
                "name": "ds_kpi_risk",
            },
            "ds_kpi_mon": {
                "type": "ds.search",
                "options": {"query": ds_kpi_mon, "queryParameters": {"earliest": "-24h@h", "latest": "now"}},
                "name": "ds_kpi_mon",
            },
            "ds_trend": {
                "type": "ds.search",
                "options": {"query": ds_trend, "queryParameters": {"earliest": "-24h@h", "latest": "now"}},
                "name": "ds_trend",
            },
        },
        "defaults": {
            "dataSources": {
                "ds.search": {
                    "options": {"queryParameters": {"earliest": "$global_time.earliest$", "latest": "$global_time.latest$"}}
                }
            }
        },
        "inputs": {
            "input_tr": {
                "type": "input.timerange",
                "options": {"token": "global_time", "defaultValue": "-24h,now"},
                "title": "Time Range",
            }
        },
        "layout": {
            "type": "absolute",
            "options": {"width": 1440, "height": 1980, "display": "auto-scale"},
            "structure": [],
            "globalInputs": ["input_tr"],
        },
        "title": "Catalog Quick-Start Portfolio (Top 2 / Category)",
        "description": "Dashboard Studio demo: 44 Quick-Start use cases with synthetic KPIs, category load, trend, and detail table. Import into Splunk Enterprise/Cloud.",
    }

    struct = [
        {"item": "bg_canvas", "type": "block", "position": {"x": 0, "y": 0, "w": 1440, "h": 1980}},
        {"item": "lbl_title", "type": "block", "position": {"x": 30, "y": 14, "w": 900, "h": 40}},
        {"item": "lbl_sub", "type": "block", "position": {"x": 30, "y": 52, "w": 900, "h": 36}},
        {"item": "input_tr", "type": "input", "position": {"x": 1020, "y": 24, "w": 260, "h": 40}},
        {"item": "lbl_live", "type": "block", "position": {"x": 1310, "y": 34, "w": 80, "h": 22}},
    ]
    for j in range(4):
        x = 30 + j * 348
        struct.append({"item": f"k_lbl_{j}", "type": "block", "position": {"x": x, "y": 100, "w": 300, "h": 22}})
        struct.append({"item": f"k_viz_{j}", "type": "block", "position": {"x": x, "y": 126, "w": 300, "h": 96}})
    struct += [
        {"item": "s1_lbl", "type": "block", "position": {"x": 30, "y": 248, "w": 400, "h": 22}},
        {"item": "cat_viz", "type": "block", "position": {"x": 30, "y": 276, "w": 860, "h": 320}},
        {"item": "s2_lbl", "type": "block", "position": {"x": 910, "y": 248, "w": 400, "h": 22}},
        {"item": "trend_viz", "type": "block", "position": {"x": 910, "y": 276, "w": 500, "h": 320}},
        {"item": "s3_lbl", "type": "block", "position": {"x": 30, "y": 618, "w": 400, "h": 22}},
        {"item": "tbl_viz", "type": "block", "position": {"x": 30, "y": 648, "w": 1380, "h": 1300}},
    ]
    dashboard["layout"]["structure"] = struct

    OUT.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
