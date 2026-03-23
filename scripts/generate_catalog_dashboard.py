#!/usr/bin/env python3
"""
Regenerate dashboards/catalog-quick-start-top2.json: exactly **one** Dashboard Studio
visualization object per Quick-Start use case (44 total). UC id + title are set as each
panel's **title** and **description** (not separate markdown blocks). Page header only.
Edit UC lists to match use-cases/INDEX.md Quick Start.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboards" / "catalog-quick-start-top2.json"

def _bg_data_uri(canvas_h: int) -> str:
    """Dark grid background sized to dashboard height."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="{canvas_h}">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="#0c1828"/><stop offset="100%" stop-color="#050a12"/>'
        "</linearGradient>"
        '<pattern id="p" width="32" height="32" patternUnits="userSpaceOnUse">'
        '<path d="M32 0H0v32" fill="none" stroke="#1e3a5f" stroke-width="0.35" opacity="0.2"/>'
        "</pattern></defs>"
        f'<rect width="1440" height="{canvas_h}" fill="url(#g)"/>'
        f'<rect width="1440" height="{canvas_h}" fill="url(#p)" opacity="0.35"/>'
        "</svg>"
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

UC_IDS = (
    "UC-1.1.23,UC-1.1.36,UC-2.1.7,UC-2.2.3,UC-3.2.7,UC-3.2.8,UC-4.1.2,UC-4.1.7,UC-5.1.1,UC-5.1.4,"
    "UC-6.1.2,UC-6.1.4,UC-7.1.2,UC-7.1.3,UC-8.1.1,UC-8.2.1,UC-9.1.3,UC-9.1.5,UC-10.1.2,UC-10.1.4,"
    "UC-11.1.8,UC-11.1.1,UC-12.1.4,UC-12.2.5,UC-13.1.1,UC-13.2.1,UC-14.1.2,UC-14.1.6,UC-15.1.1,UC-15.1.6,"
    "UC-16.1.2,UC-16.1.9,UC-17.2.3,UC-17.2.8,UC-18.2.5,UC-18.2.1,UC-19.1.1,UC-19.1.5,UC-20.1.1,UC-20.1.4,"
    "UC-21.1.1,UC-21.2.1,UC-22.1.1,UC-22.2.1"
)

TITLES = [
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

# First Quick-Start row per category (22 names, same order as INDEX.md categories 1–22)
CAT_NAMES = [
    "Server & Compute",
    "Virtualization",
    "Containers & Orchestration",
    "Cloud Infrastructure",
    "Network Infrastructure",
    "Storage & Backup",
    "Database & Data Platforms",
    "Application Infrastructure",
    "Identity & Access Management",
    "Security Infrastructure",
    "Email & Collaboration",
    "DevOps & CI/CD",
    "Observability & Monitoring Stack",
    "IoT & Operational Technology (OT)",
    "Data Center Physical Infrastructure",
    "Service Management & ITSM",
    "Network Security & Zero Trust",
    "Data Center Fabric & SDN",
    "Compute Infrastructure (HCI & Converged)",
    "Cost & Capacity Management",
    "Industry Verticals",
    "Regulatory and Compliance Frameworks",
]

VIZ_TYPES = ("singlevalue", "line", "area", "column")

PALETTE = {
    "line": "#04A4B0",
    "area": "#A974F7",
    "column": "#3993ff",
    "singlevalue": "#65A637",
}


def ds_for_panel(i: int, kind: str) -> str:
    """Synthetic SPL matched loosely to chart type (demo only)."""
    seed = 800 + i * 97
    if kind == "singlevalue":
        # Multi-row for sparkline (last row = headline value in Studio)
        return (
            f"| makeresults count=18 | streamstats count as pt | "
            f'eval _time=relative_time(now(), "-18h")+(pt-1)*3600 | '
            f"eval signal_24h={12 + (i * 37) % 400}+pt*(3+pt%4) | fields _time signal_24h"
        )
    if kind == "line":
        return (
            f"| makeresults count=24 | streamstats count as pt | "
            f'eval _time=relative_time(now(), "-24h")+(pt-1)*3600 | '
            f"eval metric={35 + (i % 11)} + pt * 1.4 + (pt % 4) | fields _time metric"
        )
    if kind == "area":
        return (
            f"| makeresults count=24 | streamstats count as pt | "
            f'eval _time=relative_time(now(), "-24h")+(pt-1)*3600 | '
            f"eval load={seed}+(pt * 83) % 4200 | fields _time load"
        )
    # column
    base = 18 + (i % 22)
    return (
        f"| makeresults count=6 | streamstats count as b | "
        f'eval segment=case(b=1,"East",b=2,"West",b=3,"North",b=4,"South",b=5,"Central",1=1,"APAC") | '
        f"eval score={base} + b * 9 | fields segment score"
    )


def viz_options(kind: str, i: int) -> dict:
    color = PALETTE[kind]
    base = {
        "backgroundColor": "transparent",
        "legendDisplay": "off",
        "xAxisTitleVisibility": "hide",
        "yAxisTitleVisibility": "hide",
    }
    if kind == "singlevalue":
        units = [" events", " hits", " %", " ms"]
        return {
            "backgroundColor": "transparent",
            "sparklineDisplay": "line",
            "trendDisplay": "off",
            "unit": units[i % len(units)],
            "unitPosition": "after",
            "numberPrecision": 0 if i % 4 != 3 else 1,
            "shouldUseThousandSeparators": True,
            "majorColor": color,
        }
    if kind == "line":
        return {**base, "seriesColors": [color], "dataValuesDisplay": "off"}
    if kind == "area":
        return {
            **base,
            "seriesColors": [color],
            "areaOpacity": 0.22,
            "dataValuesDisplay": "off",
        }
    return {**base, "seriesColors": [color], "dataValuesDisplay": "off"}


def panel_titles(uc_id: str, title: str, cat_name: str, cat_num: int) -> tuple[str, str]:
    """Studio panel title + description (one visualization object per use case)."""
    t = f"{uc_id} — {title}"
    if len(t) > 118:
        t = t[:115] + "…"
    desc = f"Category {cat_num} · {cat_name} · synthetic demo data"
    return t, desc


def main() -> None:
    uc_ids = UC_IDS.split(",")
    assert len(uc_ids) == len(TITLES) == 44, "Expected 44 Quick-Start use cases"

    COL_W = 684
    GAP = 16
    X0 = 24
    X1 = X0 + COL_W + GAP
    # One layout block per use case (title/description are on the viz itself, not separate markdown).
    PANEL_H = 278
    TOP = 118

    canvas_h = TOP + 22 * PANEL_H + 100

    visualizations: dict = {
        "bg_canvas": {"type": "splunk.image", "options": {"src": _bg_data_uri(canvas_h)}},
        "lbl_title": {
            "type": "splunk.markdown",
            "options": {
                "markdown": "## CATALOG QUICK START — TOP 2 USE CASES PER CATEGORY",
                "fontColor": "#fafafa",
            },
        },
        "lbl_sub": {
            "type": "splunk.markdown",
            "options": {
                "markdown": "**44 separate charts** · one Dashboard Studio visualization per use case (title + description on each panel) · INDEX.md Quick Start · synthetic `makeresults` data",
                "fontColor": "#909090",
            },
        },
        "lbl_live": {
            "type": "splunk.markdown",
            "options": {"markdown": "\u25cf  DEMO", "fontColor": "#04A4B0"},
        },
    }

    data_sources: dict = {}

    structure: list = [
        {"item": "bg_canvas", "type": "block", "position": {"x": 0, "y": 0, "w": 1440, "h": canvas_h}},
        {"item": "lbl_title", "type": "block", "position": {"x": 30, "y": 14, "w": 950, "h": 38}},
        {"item": "lbl_sub", "type": "block", "position": {"x": 30, "y": 48, "w": 1000, "h": 52}},
        {"item": "input_tr", "type": "input", "position": {"x": 1020, "y": 24, "w": 260, "h": 40}},
        {"item": "lbl_live", "type": "block", "position": {"x": 1310, "y": 34, "w": 80, "h": 22}},
    ]

    for row in range(22):
        cat_num = row + 1
        cat_name = CAT_NAMES[row]
        y_panel = TOP + row * PANEL_H

        for col in range(2):
            i = row * 2 + col
            kind = VIZ_TYPES[i % 4]
            uc_id = uc_ids[i]
            title = TITLES[i]
            viz_id = f"viz_uc_{i}"
            ds_name = f"ds_uc_{i}"

            ptitle, pdesc = panel_titles(uc_id, title, cat_name, cat_num)

            viz_def: dict = {
                "type": f"splunk.{kind}",
                "title": ptitle,
                "description": pdesc,
                "containerOptions": {
                    "title": {"color": "#e8eef7"},
                    "description": {"color": "#8b95a8"},
                },
                "dataSources": {"primary": ds_name},
                "options": viz_options(kind, i),
            }
            visualizations[viz_id] = viz_def

            data_sources[ds_name] = {
                "type": "ds.search",
                "options": {
                    "query": ds_for_panel(i, kind),
                    "queryParameters": {"earliest": "-24h@h", "latest": "now"},
                },
                "name": ds_name,
            }

            x = X0 if col == 0 else X1
            structure.append(
                {
                    "item": viz_id,
                    "type": "block",
                    "position": {"x": x, "y": y_panel, "w": COL_W, "h": PANEL_H},
                }
            )
    dashboard = {
        "visualizations": visualizations,
        "dataSources": data_sources,
        "defaults": {
            "dataSources": {
                "ds.search": {
                    "options": {
                        "queryParameters": {
                            "earliest": "$global_time.earliest$",
                            "latest": "$global_time.latest$",
                        }
                    }
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
            "options": {"width": 1440, "height": canvas_h, "display": "auto-scale"},
            "structure": structure,
            "globalInputs": ["input_tr"],
        },
        "title": "Catalog Quick-Start — 44 use case panels",
        "description": "Dashboard Studio: one labeled chart per Quick-Start use case (top 2 × 22 categories). Synthetic demo data.",
    }

    OUT.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n_chart = len([k for k, v in visualizations.items() if str(v.get("type", "")).startswith("splunk.") and v["type"] not in ("splunk.image", "splunk.markdown")])
    print(f"Wrote {OUT} ({n_chart} chart visualizations only; titles on-panel)")


if __name__ == "__main__":
    main()
