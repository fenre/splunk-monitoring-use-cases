<!-- AUTO-GENERATED from UC-1.1.1.json — DO NOT EDIT -->

---
id: "1.1.1"
title: "CPU Utilization Trending (Linux)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.1 · CPU Utilization Trending (Linux)

## Description

Detects Linux hosts whose CPU has been pinned above 90% on average for an hour, indicating sustained overload that will cause request queuing and SLA breaches before users notice.

## Value

Sustained CPU saturation almost always surfaces as user-visible latency, queued connections, or batch overruns. Catching it on the host first means you rebalance, scale, or kill a runaway process before it becomes an incident — and the trend line tells you whether to add capacity now or schedule a hardware refresh next quarter.

## Implementation

Deploy `Splunk_TA_nix` to Linux Universal Forwarders via Forwarder Management. Enable the `cpu` scripted input (`[script://./bin/cpu.sh] interval=60 index=os`). Schedule the search every 15 minutes over the last 1 hour, throttle by `host` for 4 hours.

## Detailed Implementation

Prerequisites
• Splunk Add-on for Unix and Linux (`Splunk_TA_nix`, Splunkbase 833) ≥8.0 installed on Search Heads, Indexers (for parsing), and every Universal Forwarder. Required on Search Heads even if you only use the CIM variant — that's where the eventtype/tag mapping lives.
• Universal Forwarder ≥9.0 on each target host, deployed via Deployment Server / Forwarder Management with a serverclass mapping all Linux hosts to a `nix_uf` app bundle that contains `Splunk_TA_nix` plus a local override.
• Network: outbound from each UF to your indexer tier on `9997/tcp` (splunktcp) or `9998/tcp` (splunktcp-ssl, recommended).
• Splunk role: users running this search need `srchIndexesAllowed = os`. Add to a custom role (`linux_observer`) rather than granting `admin`.
• License: the `cpu` sourcetype generates ~1.5 KB/event/host/minute ≈ 2.2 GB/host/month at the default 60s interval. Plan license headroom for `fleet_size × 2.2 GB`. For metric-store deployments see Step 1 — switching to the `cpu_metric` sourcetype lowers ingest ~5×.
• Baseline knowledge: expected normal `cpu_used` per host class (web ≈ 30%, db ≈ 50%, batch ≈ 70–90% during job windows). Used in Step 3 validation and Step 5 troubleshooting.

Step 1 — Configure data collection
On the Deployment Server (or via Forwarder Management UI), edit `etc/deployment-apps/Splunk_TA_nix/local/inputs.conf` to enable the `cpu` scripted input. Override the default-disabled stanza:

```ini
[script://./bin/cpu.sh]
disabled = 0
interval = 60
sourcetype = cpu
source = cpu
index = os
```

Reload the deployment server (`splunk reload deploy-server`) and verify in Forwarder Management that all `nix_uf` clients pulled the bundle.

Verification: on one UF, `splunk btool inputs list --debug | grep cpu.sh` should show your local stanza winning over the default. Tail `$SPLUNK_HOME/var/log/splunk/splunkd.log` for `ExecProcessor` entries naming `cpu.sh` with `rc=0`.

Expected event volume: 1 event per host per `interval` per CPU plus a summary row (`CPU=all`). A 16-core box at interval=60 produces 17 events/min ≈ 24,500 events/day.

The `cpu.sh` script (`$SPLUNK_HOME/etc/apps/Splunk_TA_nix/bin/cpu.sh`) wraps `top -bn1` on most distros (RHEL, Ubuntu, SUSE) and `vmstat 1 1` on AIX-derivatives. The TA's `props.conf` extracts: `CPU` (digit or `all`), `pctUser`, `pctNice`, `pctSystem`, `pctIowait`, `pctIdle`, `pctSteal`. The CIM mapping (`eventtype = nix_cpu_metric`, tags `cpu` + `performance`) computes `cpu_load_percent = pctUser + pctSystem + pctIowait`.

For metric-store deployments: change `sourcetype = cpu` to `sourcetype = cpu_metric` and route the input to a metric index. Ingest drops ~5× and the CIM variant in Step 2 still works because `Performance.CPU` is metric-aware in CIM 5.x+.

Step 2 — Create the search and alert
Raw-event SPL:

```spl
index=os sourcetype=cpu host=* CPU="all"
| eval cpu_used = 100 - pctIdle
| timechart span=1h avg(cpu_used) as avg_cpu by host
| where avg_cpu > 90
```

Why `CPU="all"`: `cpu.sh` emits one event per logical core PLUS a summary row tagged `CPU=all`. Without the filter you double-count and your average gets skewed by per-core IRQ spikes (a kworker softirq pinned to CPU0 will look like a fleet-wide problem).

Why `avg` not `max`: alerting on `max(cpu_used)` fires constantly because every Linux host briefly hits 100% during context switches and IRQ handling. `avg` over 1h is the correct "sustained overload" signal. If you need a tighter SLO trigger, narrow to `span=5m` and `where avg_cpu > 85`.

Schedule as Alert: cron `*/15 * * * *`, time range `-1h@h to @h`, trigger on "Number of results > 0", throttle suppression `host` field for `4h` so the same overloaded host doesn't re-page during the same incident.

CIM / accelerated variant (preferred when the Performance datamodel is accelerated — typically 10–50× faster than raw):

```spl
| tstats summariesonly=true
    avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance
  where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
| rename Performance.host as host
```

The CIM variant uses `Performance.cpu_load_percent`, which is `pctUser + pctSystem + pctIowait` (i.e. "non-idle, non-nice, non-steal" — slightly different from the raw `100 - pctIdle` because it excludes nice and steal). On most workloads the two agree to within 1–2%; on heavily-niced hosts (build farms) or virtualised hosts with steal time, the CIM number is the better SLO signal.

Step 3 — Validate
On a known-good Linux host whose forwarder is sending events:

(a) SSH to the host. `top -bn1 | head -5` and read the `%Cpu(s):` line. Note `id` (idle).

(b) In Splunk: `index=os sourcetype=cpu host=<that-host> CPU="all" | head 1 | table _time pctIdle pctUser pctSystem pctIowait`. The newest event's `pctIdle` should match the `id` value from `top` to within ~1% (forwarder pipeline lag aside).

(c) Confirm field extraction: `index=os sourcetype=cpu host=<that-host> earliest=-5m | stats count by CPU` should return one row per logical core plus an `all` row. If only `all` is present, your `props.conf` extraction is broken (typically because a corporate hardening script re-formatted `cpu.sh` stdout).

(d) Confirm CIM tagging: `index=os sourcetype=cpu host=<that-host> earliest=-5m | head 1 | eval _ok=if(searchmatch("eventtype=nix_cpu_metric"), "tagged", "MISSING — check Splunk_TA_nix is on the Search Head")`.

(e) Run the CIM variant of Step 2 with `span=5m` and `where Performance.host="<that-host>"`. If it returns no rows but raw works, the Performance datamodel isn't accelerated for that time range — Settings → Data Models → Performance → Edit Acceleration.

(f) Confirm role permissions: `| rest splunk_server=local /servicesNS/-/-/authorization/roles | search title=<your-role> | table title srchIndexesAllowed`. The list must include `os`.

Step 4 — Operationalize
Dashboard (recommended layout, named "Linux Compute — Sustained Overload"):
• Row 1 — Single value tiles: "Hosts >90% sustained 1h in last 4h" (red threshold ≥1), "Hours of overload in last 24h fleet-wide".
• Row 2 — Timechart line, top-10 hosts by current avg %CPU, time-picker default "Last 4 hours".
• Row 3 — Sortable table: host | peak %CPU last hour | hours over 90% in last 24h | owning service (joined from `server_inventory` lookup on `host`) | last_change (joined from `index=changes`). Drilldown opens host detail dashboard.
• Time-picker presets: "Last 4 hours" (incident view) and "Last 30 days" (capacity-review view).

Alerting:
• PagerDuty integration: low-urgency on first violation per host, high-urgency if the same host re-fires within 4h. Annotate the alert with the last-1h timechart PNG (Splunk → Alert Action → Webhook to PagerDuty Events API v2).
• Slack/Teams secondary notification to `#sre-linux` for visibility, no paging.

Runbook (owner: Linux SRE on-call):
1. Open the host's panel in the dashboard. If `pctIowait` is the dominant contributor, this is an I/O issue not a CPU issue — pivot to UC-1.1.6 (Disk I/O Saturation).
2. SSH to the host. `top -o %CPU` or `htop`. Identify the dominant process by `%CPU`.
3. If process is `kworker/*` or `softirqd/*`, suspect kernel-side IRQ storm — escalate to Linux platform team.
4. Check planned maintenance: `index=changes earliest=-2h host=<host>` and your `maintenance_windows` lookup.
5. Check batch scheduler (cron, systemd-timer, Airflow, Control-M) for overlapping jobs scheduled on this host.
6. If unowned process or runaway: `nice -n 19` to deprioritise; coordinate kill with workload owner.

Capacity review (cadence: monthly, owner: Capacity Planning):
• Query: `<base SPL> | timechart span=1d count(eval(avg_cpu>90)) as overloaded_hours by host | stats sum(overloaded_hours) as total by host | where total > 24`.
• Action thresholds: 24–72 hours/month → flag for workload tuning; >72 hours/month → flag for vertical scaling or workload migration.

Step 5 — Troubleshooting

• **No events at all** — TA not deployed to the host, or scripted input still default-disabled. On the UF: `splunk btool inputs list --debug | grep cpu.sh` should show `disabled = 0` from your local app, not `disabled = 1` from `Splunk_TA_nix/default/`. Check `$SPLUNK_HOME/var/log/splunk/splunkd.log` for `ExecProcessor: ... cpu.sh ... rc=0` lines.

• **Events arriving but `pctIdle` is null** — `props.conf` extraction is broken, typically because a corporate hardening script wrapped or re-formatted `cpu.sh` stdout. Compare the host's output against vanilla: `/opt/splunkforwarder/etc/apps/Splunk_TA_nix/bin/cpu.sh | head -5`. The first line should be a header like `CPU pctUser pctNice pctSystem pctIowait pctIdle ...`.

• **`avg_cpu` always 100 across all hosts** — you forgot the `CPU="all"` filter and are double-counting per-core summary rows. Add `CPU="all"` to the base search.

• **CIM variant returns no rows but raw SPL works** — Performance datamodel isn't accelerated, OR the Splunk_TA_nix tags didn't propagate to the Search Head. Settings → Data Models → Performance → check acceleration. Then `index=os sourcetype=cpu | head 1 | eval _checktag=if(searchmatch("eventtype=nix_cpu_metric"), "tagged", "missing — TA not on SH")`.

• **Alert fires every night at 03:00** — `dnf-automatic` / `apt-daily` weekly upgrade is the culprit. Either accept it (scheduled work), shift the upgrade window, or filter the search: `| where NOT (date_hour>=3 AND date_hour<=4 AND date_wday="sunday")`. Better: maintain a `maintenance_windows` lookup keyed on `host` and filter via `lookup maintenance_windows host OUTPUT in_window | where in_window!="yes"`.

• **Single host shows >100% sustained** — forwarder clock skew is producing duplicate events with the same `_time` being summed. `ntpq -p` or `chronyc sources` on the host. Also check `_indextime - _time` distribution: `index=os sourcetype=cpu host=<host> | eval lag=_indextime-_time | stats avg(lag) p95(lag) max(lag)`.

• **Alert never fires even when you can see >90% in the dashboard** — alert time range likely doesn't match the search. Verify the alert is scheduled `*/15 * * * *` with time range `-1h@h to @h`, not `-15m to now` (which would only see one event per host and never average above an hourly threshold).

• **CIM variant materially disagrees with raw** — virtualised host with high steal time, OR a build farm with heavy `nice`-d workloads. The CIM `cpu_load_percent` excludes both `pctSteal` and `pctNice`. For VMs, the CIM number is closer to "what the guest is actually getting" — keep it. For build farms, switch back to `100 - pctIdle`.

## SPL

```spl
index=os sourcetype=cpu host=* CPU="all"
| eval cpu_used = 100 - pctIdle
| timechart span=1h avg(cpu_used) as avg_cpu by host
| where avg_cpu > 90
```

## CIM SPL

```spl
| tstats summariesonly=true
    avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance
  where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
| rename Performance.host as host
```

## Visualization

(1) Timechart line panel split by host showing the top-10 noisiest series, last 24h. (2) Single value: count of hosts currently >90% sustained 1h in the last 4h. (3) Sortable table of (host, peak %CPU last hour, hours over 90% in last 24h, owning service via `server_inventory` lookup). (4) Optional heatmap of `pctUser` vs `pctIowait` to distinguish CPU-bound from I/O-bound workloads.

## References

- [Splunk Add-on for Unix and Linux (Splunkbase 833)](https://splunkbase.splunk.com/app/833)
- [Splunk_TA_nix scripted inputs reference (cpu, vmstat, iostat)](https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/Sourcetypes)
- [Splunk CIM: Performance data model](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
- [inputs.conf reference (script:// stanza)](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Inputsconf)
