<!-- AUTO-GENERATED from UC-8.4.38.json — DO NOT EDIT -->

---
id: "8.4.38"
title: "PHP-FPM Memory per Worker Trend from Status and Host Metrics"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.38 · PHP-FPM Memory per Worker Trend from Status and Host Metrics

## Description

Detects PHP-FPM worker pools whose average resident-set memory grows materially week-over-week, the canonical signature of an opcache, ORM-container, PSR-7-stream, or APCu leak that will eventually let `pm.max_children` × per-worker RSS exceed the host or container memory ceiling and OOM-kill a worker mid-request.

## Value

PHP-FPM leaks are silent until they aren't. Each request adds a few KB to a worker; thousands of requests later, the pool's footprint quietly doubles, the cgroup's `memory.max` is hit, and the kernel OOM-kills a worker holding an in-flight HTTPS request — the user sees a 502, the front proxy logs it as upstream reset, and the on-call has to correlate three log streams to find that the root cause was a code change three deploys ago. Catching the trend a week before the cliff lets the team raise `pm.max_requests`, ship the leak fix, or scale the host on a planning cadence instead of a paging cadence.

## Implementation

Deploy `Splunk_TA_nix` with the `ps` scripted input enabled to every Linux host running PHP-FPM. Add a small `fpm_status.sh` scripted input that scrapes `http://127.0.0.1/status?json` every 60s. Schedule the leak-detection alert weekly (Monday 09:00 local) over a 7-day comparison window, throttle by `host` + `pool` for 24h.

## Detailed Implementation

Prerequisites
• Splunk Add-on for Unix and Linux (`Splunk_TA_nix`, Splunkbase 833) ≥8.0 installed on Search Heads (extractions for `ps` are server-side) and on every Universal Forwarder running on a Linux host that hosts PHP-FPM. Required on Search Heads even if you only ever look at the search results — that's where the `props.conf` field extractions live.
• Universal Forwarder ≥9.0 deployed via Deployment Server, with a serverclass mapping all PHP-FPM hosts to a `phpfpm_uf` app bundle that contains `Splunk_TA_nix` plus a small local app for the FPM status scraper (Step 1).
• PHP-FPM ≥7.4 configured with `pm.status_path = /status` in the pool config (typically `/etc/php/8.2/fpm/pool.d/www.conf` on Debian/Ubuntu, `/etc/php-fpm.d/www.conf` on RHEL). The status endpoint is disabled by default — until you uncomment that directive there is nothing to scrape.
• A web-server location block (nginx or Apache) that proxies `/status` to the FPM socket and restricts it to `127.0.0.1` / `::1` so the endpoint is not internet-exposed. Example nginx stanza:

```nginx
location ~ ^/(status|ping)$ {
    access_log off;
    allow 127.0.0.1;
    allow ::1;
    deny all;
    fastcgi_pass unix:/run/php/php8.2-fpm.sock;
    fastcgi_param SCRIPT_FILENAME $fastcgi_script_name;
    include fastcgi_params;
}
```

• Network: outbound from each UF to your indexer tier on `9997/tcp` (splunktcp) or `9998/tcp` (splunktcp-ssl, recommended).
• Splunk role: users running this search need `srchIndexesAllowed` covering both `os` (for `ps`) and `web` (for `phpfpm:status`). Add to a custom role (`web_observer`) rather than granting `admin`.
• License envelope: at the default 60s ps cadence, a host running 50 PHP-FPM workers emits ~50 events/minute × 350 bytes = 17 KB/minute = ~720 MB/host/month from `ps` alone. The status JSON is a single ~600-byte event per pool per minute = ~26 MB/host/month/pool. Plan for `fleet_size × (~750 MB/month + pools × 26 MB/month)`.
• Baseline knowledge: typical steady-state `mb_per_worker` by stack — vanilla PHP scripts ≈ 20–30 MB; WordPress with caching ≈ 35–55 MB; Symfony 6 in `prod` env with compiled container ≈ 60–100 MB; Laravel with Octane disabled ≈ 50–80 MB; Magento 2 ≈ 150–250 MB. Used in Step 3 validation and the leak-vs-baseline alert variant in Step 2.

Step 1 — Configure data collection

Three streams to enable. Streams (a) and (b) are required; stream (c) is optional and recommended for containerised FPM.

(a) Splunk_TA_nix ps scripted input. On the Deployment Server, edit `etc/deployment-apps/phpfpm_uf/local/inputs.conf`:

```ini
[script://./bin/ps.sh]
disabled = 0
interval = 60
sourcetype = ps
source = ps
index = os
```

The TA's default `props.conf` extracts `USER`, `PID`, `PCPU`, `PMEM`, `VSZ` (KB), `RSS` (KB) → field aliased to `mem_used`, `TT`, `STAT`, `STARTED`, `TIME`, `COMMAND` → field aliased to `args`, plus a 16-char-truncated `comm`. PHP-FPM's master and workers all share the truncated `comm = "php-fpm:"`; the discriminator is in `args`: `php-fpm: master process (...)` vs `php-fpm: pool www`. Filter on `args` in Step 2.

(b) FPM status scraper. Create a small scripted input under your local TA. File `phpfpm_uf/local/bin/fpm_status.sh`:

```bash
#!/usr/bin/env bash
# fpm_status.sh — emit one JSON event per FPM pool per run.
# Reads the host's status endpoint(s); add one line per vhost/pool you expose.
set -euo pipefail
for URL in \
    "http://127.0.0.1/status?json" \
    ; do
  # The trailing pool tag lets us split events when multiple pools are
  # exposed on different vhosts on the same host.
  RESP=$(curl -fsS --max-time 5 "$URL" || true)
  [ -z "$RESP" ] && continue
  # Splunk timestamp prefix ensures the event-time matches the scrape time,
  # not the indexing time, so leak trends are not skewed by pipeline lag.
  printf '%s scrape_url="%s" %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" "$URL" "$RESP"
done
```

```ini
[script://./bin/fpm_status.sh]
disabled = 0
interval = 60
sourcetype = phpfpm:status
source = fpm_status
index = web
```

Field aliases (so you can use clean names in SPL — keys in the FPM JSON contain spaces). Edit `phpfpm_uf/local/props.conf`:

```ini
[phpfpm:status]
KV_MODE = json
TIME_PREFIX = ^
TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%3NZ
MAX_TIMESTAMP_LOOKAHEAD = 30
FIELDALIAS-fpm = process\ manager AS process_manager start\ since AS start_since accepted\ conn AS accepted_conn listen\ queue AS listen_queue idle\ processes AS idle_processes active\ processes AS active_processes total\ processes AS total_processes max\ active\ processes AS max_active_processes max\ children\ reached AS max_children_reached slow\ requests AS slow_requests
```

Push via `splunk reload deploy-server`. Verify on a UF: `splunk btool inputs list --debug | grep fpm_status.sh` shows `disabled = 0` from your local app.

(c) Optional — cgroups v2 memory for containers. If FPM runs in Docker / Kubernetes, the OOM ceiling is the container's `memory.max`, not the host's. Run the [Splunk OpenTelemetry Collector](https://github.com/signalfx/splunk-otel-collector) as a DaemonSet with the `kubeletstats` or `cgroup` receiver and forward `container.memory.usage` and `container.memory.limit` to HEC at `index=metrics sourcetype=cgroup_memory`. The leak is then visible as `container.memory.usage / container.memory.limit` rising toward 1.0.

Verification of all three streams: tail `$SPLUNK_HOME/var/log/splunk/splunkd.log` for `ExecProcessor` entries naming `ps.sh` and `fpm_status.sh` with `rc=0`. Expected event volume: ps emits 1 event per process per `interval`; fpm_status.sh emits 1 event per URL per `interval`.

Step 2 — Create the search and alert

Primary trend SPL (the headline panel of the dashboard):

```spl
index=os sourcetype=ps args="php-fpm: pool *"
| rex field=args "php-fpm: pool (?<pool>\S+)"
| eval host_pool = host."::".pool
| bin _time span=1m
| stats sum(mem_used) as fpm_kb, dc(pid) as workers by _time host_pool
| eval mb_per_worker = round(fpm_kb / 1024 / workers, 2)
| timechart span=15m avg(mb_per_worker) by host_pool
```

Why this construction:

• `args="php-fpm: pool *"` excludes the master process (`php-fpm: master process (...)`) which uses near-zero memory and would deflate the per-worker average. The wildcard match works because PHP-FPM masks every worker as `php-fpm: pool <pool-name>`.
• `bin _time span=1m` aligns ps snapshots that arrived within the same scrape window. Without it, two workers captured 2 seconds apart land in different time buckets and `dc(pid)` undercounts.
• `dc(pid)` (not `count`) protects against a worker being captured twice in the same minute by overlapping scrapes.
• `host_pool = host."::".pool` keeps the same pool name on different hosts on different lines — important for sharded/horizontally-scaled deployments where pool `www` runs on five servers.

Leak-detection alert variant (week-over-week growth ≥25%):

```spl
index=os sourcetype=ps args="php-fpm: pool *" earliest=-1h
| rex field=args "php-fpm: pool (?<pool>\S+)"
| stats sum(mem_used) as kb_now, dc(pid) as workers_now by host pool
| eval mb_now = round(kb_now / 1024 / workers_now, 2)
| join type=left host pool [
    search index=os sourcetype=ps args="php-fpm: pool *" earliest=-7d@d-1h latest=-7d@d
    | rex field=args "php-fpm: pool (?<pool>\S+)"
    | stats sum(mem_used) as kb_base, dc(pid) as workers_base by host pool
    | eval mb_base = round(kb_base / 1024 / workers_base, 2)
    | table host pool mb_base
  ]
| eval growth_pct = if(mb_base>0, round(100*(mb_now-mb_base)/mb_base, 1), null())
| where growth_pct > 25 AND mb_now > 50
| table host pool mb_base mb_now growth_pct
```

The `mb_now > 50` floor stops the alert firing on tiny pools where 22 MB → 30 MB looks like 36% growth but is just background noise. Schedule weekly: cron `0 9 * * 1` (Monday 09:00 local), throttle suppression `host` + `pool` for 24h.

Saturation companion alert (under-provisioned `pm.max_children` — the leak's eventual symptom):

```spl
index=web sourcetype=phpfpm:status earliest=-15m
| eval max_children_reached = tonumber(coalesce(max_children_reached, 'max children reached'))
| eval listen_queue = tonumber(coalesce(listen_queue, 'listen queue'))
| stats max(max_children_reached) as mcr_peak, max(listen_queue) as lq_peak by host pool
| where mcr_peak > 0 OR lq_peak > 0
```

Run every 5 minutes; this is the high-urgency page (workers are queueing requests right now), distinct from the weekly leak-trend alert.

Step 3 — Validate

On a known-busy PHP-FPM host whose forwarder is sending events:

(a) SSH to the host. `curl -s http://127.0.0.1/status?json | jq`. Note `total processes`, `idle processes`, `active processes`, `max children reached`, `slow requests`. Then `ps -eo pid,user,rss,cmd | grep "php-fpm: pool" | grep -v master`. Count rows; sum the `rss` column; divide. The result should match `mb_per_worker` from Splunk for the most recent minute to within ~3% (forwarder pipeline lag).

(b) In Splunk: `index=web sourcetype=phpfpm:status earliest=-5m | head 1 | table _time pool process_manager total_processes active_processes max_children_reached slow_requests`. The newest event's `total_processes` should equal the FPM JSON's `total processes` and the `ps` worker count from (a).

(c) Confirm the master is NOT being counted: `index=os sourcetype=ps args="php-fpm: master*" earliest=-5m | stats count`. Expected: small (1 per host per minute). Now confirm the SPL filter excludes it: same query but `args="php-fpm: pool *"` — should return only worker rows.

(d) Confirm field aliases: `index=web sourcetype=phpfpm:status earliest=-5m | head 1 | table max_children_reached "max children reached"`. Both columns should be present and equal. If `max_children_reached` is null but `max children reached` is populated, the FIELDALIAS in `props.conf` didn't make it onto the Search Head — push the local TA there.

(e) Confirm role permissions: `| rest splunk_server=local /servicesNS/-/-/authorization/roles | search title=<your-role> | table title srchIndexesAllowed`. The list must include both `os` and `web`.

(f) Sanity-check the leak alert against a known-good baseline week. Run the leak-detection variant with `earliest=-14d@d-1h latest=-14d@d` substituted into the outer query and `-21d@d-1h / -21d@d` in the join — comparing two known-stable weeks should produce growth_pct values clustered around 0 (±5%). If you see >25% in this benign comparison, your baseline window straddled a deploy and the floor `mb_now > 50` may need raising for noisy small pools.

Step 4 — Operationalize

Dashboard (recommended layout, named "PHP-FPM — Worker Memory Trends"):
• Row 1 — Single-value tiles: "Pools with `max_children_reached > 0` (last 1h)" red threshold ≥1; "Pools with growth >25% week-over-week" red threshold ≥1; "Sustained `listen_queue > 0` (last 15 min)" red threshold ≥1.
• Row 2 — Timechart line of `mb_per_worker` by `host_pool`, last 14 days, top-20 series. Annotation overlay from `index=changes type=deploy app=php-*` so reload events are visible as vertical lines.
• Row 3 — Sortable table: host | pool | `mb_per_worker` (current) | `mb_per_worker` (7d ago) | growth_pct | `pm.max_children` (lookup) | `php_admin_value[memory_limit]` (lookup) | projected RSS at full saturation = `pm.max_children × mb_per_worker` | cgroup `memory.max` (lookup) | RED if projected > 0.85 × cgroup limit.
• Row 4 — Sawtooth panel: timechart of `avg(mb_per_worker)` for a single drill-down `host_pool` at `span=1m` over last 24h. The `pm.max_requests = 500` recycle is the drop-back-to-baseline pattern; if your dashboard does NOT show sawtooth and `pm.max_requests = 0`, that's a config recommendation flag.
• Row 5 — `slow_requests` delta by pool, top-10 last 24h: `index=web sourcetype=phpfpm:status | streamstats current=f window=1 last(slow_requests) as prev by pool | eval delta = slow_requests - prev | where delta > 0 | timechart sum(delta) by pool`.
• Time-picker presets: "Last 14 days" (leak-hunt view) and "Last 4 hours" (incident view).

Alerting:
• Saturation alert (`max_children_reached > 0` OR sustained `listen_queue > 0`): PagerDuty high-urgency, route to web on-call. Pages immediately because the user impact is happening now.
• Leak alert (>25% week-over-week per pool): Slack to `#sre-web` low-urgency notification, no paging. The trend alert is a planning signal, not an outage signal.
• Annotate every alert with the last-1h timechart PNG (Splunk → Alert Action → Webhook to PagerDuty Events API v2).

Runbook (owner: Web SRE on-call):
1. Open the dashboard, drill into the offending `host_pool`. If `mb_per_worker` is rising AND `slow_requests` is rising, the leak is in a slow code path — check the `phpfpm:slowlog` index for the dominant script.
2. SSH to the host. Pick one worker PID: `pgrep -f "php-fpm: pool <pool>" | head -1`. `cat /proc/<pid>/status | grep -E '^(VmRSS|VmPeak|VmData)'` gives the kernel's view; `cat /proc/<pid>/smaps_rollup | grep ^Pss` gives the proportional set size (better for FPM because workers share opcache code segments).
3. Quick mitigation if pages are firing: lower `pm.max_requests` to 200 (or set it from 0 to 500) and `systemctl reload php-fpm`. Workers will recycle more frequently, capping the leak's blast radius. This buys 24–48h to ship the real fix.
4. Identify the leak: capture an opcache dump from one worker before recycle: `php -r 'print_r(opcache_get_status(false));' > /tmp/opcache_$(date +%s).txt`. Compare two snapshots an hour apart; growth in `memory_consumption` or `cached_scripts` count points to runtime `eval()` or `include` of dynamically-named files (a common Symfony container-not-cached symptom).
5. Check planned maintenance: `index=changes earliest=-2h host=<host>` and your `maintenance_windows` lookup before paging out.
6. Permanent fix paths: (a) ship the code fix; (b) audit `apcu_store()` calls for missing TTLs; (c) flip Symfony / Laravel to compiled-container mode (`APP_ENV=prod`, warm cache); (d) right-size the pool: `pm.max_children = floor(cgroup_memory.max × 0.8 / mb_per_worker_steady_state)`.

Capacity review (cadence: monthly, owner: Web Platform):
• Query: `<leak SPL> | stats count(eval(growth_pct>10)) as weeks_of_growth by host pool | where weeks_of_growth >= 4`.
• Action thresholds: 4–8 weeks of consecutive >10% growth → flag for code review and APM tracing; >8 weeks → block further deploys to this pool until the leak is identified.

Step 5 — Troubleshooting

• **No `phpfpm:status` events at all** — most common cause: `pm.status_path` is still commented out in the pool config. `grep -E '^\s*pm.status_path' /etc/php-fpm.d/*.conf /etc/php/*/fpm/pool.d/*.conf`. Second cause: nginx/Apache not exposing the location. Test from the host: `curl -v http://127.0.0.1/status?json` should return a JSON body, not a 404. Third cause: SELinux or AppArmor blocking the curl from the scripted input — `audit2allow -a` or check `journalctl -u apparmor`.

• **`ps` events arriving but `mb_per_worker` is 0 or null** — `args` field truncated. Some older `ps.sh` versions limit `COMMAND` width to 64 chars; if the pool name plus the master's argv is long, `args` gets cut to `php-fpm: pool` with no name. Verify on the host: `ps -eo args= | grep "php-fpm:" | head -3` should show full pool names. If truncated, edit the TA's `ps.sh` to use `ps -e -o user,pid,...,args=` with `-w -w` (double-wide) and re-deploy.

• **`mb_per_worker` shows a perfect sawtooth dropping to ~30 MB every N minutes** — that is `pm.max_requests` recycling working as designed, not a leak. Confirm: `grep -E '^\s*pm.max_requests' /etc/php-fpm.d/<pool>.conf`. The leak signal is the slow-rising envelope across multiple sawtooth peaks — alert on `avg(mb_per_worker)` over a 1h window, not on the instantaneous value.

• **Memory grows linearly forever, no recycle, code review finds no leak** — likely an `apcu_store()` call without a TTL, or a long-lived persistent PDO connection (`PDO::ATTR_PERSISTENT => true`) accumulating prepared-statement metadata. `php -r 'print_r(apcu_cache_info(true));'` shows the APCu footprint; if it's >100 MB and rising, the cache is the leak.

• **Workers OOM-killed (visible in `dmesg` as `Killed process <pid> (php-fpm: pool ...)`) but `mb_per_worker` looks fine** — host memory is fine, container `memory.max` is not. Check the cgroup: `cat /sys/fs/cgroup/<pod-cgroup>/memory.max` and `cat /sys/fs/cgroup/<pod-cgroup>/memory.events` (`oom`, `oom_kill` counters). Then compute the worst-case: `pm.max_children × php_admin_value[memory_limit]`. If that product exceeds 0.85 × `memory.max`, you can OOM under load even when steady-state is healthy. Either raise the container memory request/limit or lower `pm.max_children`.

• **`max_children_reached` increments but `total_processes` is well below `pm.max_children`** — that's a stale counter. The FPM master only resets `max children reached` on a `SIGUSR2` reload, not on `SIGHUP`. The metric is cumulative since last reload; what you want is the delta between scrapes. Use `streamstats current=f window=1 last(max_children_reached) as prev by host pool | eval delta = max_children_reached - prev | where delta > 0` to alert on new occurrences only.

• **Leak alert never fires on a pool that visibly leaks in the dashboard** — the join's `host pool` key is not matching across the two time ranges. Most common cause: a `host` rename (DNS migration) between the baseline and current windows. Check: `index=os sourcetype=ps args="php-fpm: pool *" earliest=-7d@d-1h latest=-7d@d | stats values(host) by pool`. If the host name list disagrees with the current week, fall back to joining only on `pool` and accept some cross-host noise.

• **Different sources of `pool` disagree** — `ps`-derived pool comes from `args` regex; status-endpoint `pool` comes from the FPM JSON `pool` key. They should match in 99% of deployments but a chroot'd FPM with `[pool global]` on top can produce edge-case mismatches. Cross-check: `index=web sourcetype=phpfpm:status earliest=-1h | stats values(pool) as status_pools by host | append [search index=os sourcetype=ps args="php-fpm: pool *" earliest=-1h | rex field=args "php-fpm: pool (?<pool>\S+)" | stats values(pool) as ps_pools by host] | stats values(*) by host`. Anything in one column and not the other is a config drift to investigate.

## SPL

```spl
index=os sourcetype=ps args="php-fpm: pool *"
| rex field=args "php-fpm: pool (?<pool>\S+)"
| eval host_pool = host."::".pool
| bin _time span=1m
| stats sum(mem_used) as fpm_kb, dc(pid) as workers by _time host_pool
| eval mb_per_worker = round(fpm_kb / 1024 / workers, 2)
| timechart span=15m avg(mb_per_worker) by host_pool
```

## Visualization

(1) Timechart line of `mb_per_worker` by `host_pool`, last 14 days, top 20 series by current value — the leak ramp is visible as a slow upward slope and the `pm.max_requests` recycle is visible as the regular sawtooth dropping back to baseline. (2) Single-value tile: count of pools with `max_children_reached > 0` in the last hour (red threshold ≥1) — this is the saturation companion. (3) Sortable table: `host` | `pool` | `mb_per_worker` (current) | `mb_per_worker_baseline` (7d ago) | `growth_pct` | `pm.max_children` | `php_admin_value[memory_limit]` | projected RSS at full saturation, with red rows where projected RSS exceeds the cgroup's `memory.max`. (4) Bar chart of `slow_requests` delta by pool over last 24h — slow requests often correlate with the leak path (heavy controller → big container → slow GC).

## References

- [Splunk Add-on for Unix and Linux (Splunkbase 833)](https://splunkbase.splunk.com/app/833)
- [PHP-FPM configuration directives (pm.*, request_terminate_timeout, slowlog)](https://www.php.net/manual/en/install.fpm.configuration.php)
- [PHP-FPM status page reference (status_path, ?json, ?full)](https://www.php.net/manual/en/install.fpm.status.php)
- [Linux cgroups v2 memory controller (memory.current, memory.max, memory.events)](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html#memory)
- [OpenTelemetry Collector — PHP-FPM receiver](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/phpfpmreceiver)
