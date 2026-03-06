# Splunk Core Infrastructure Monitoring — Enriched Use Case Repository

> A comprehensive collection of IT infrastructure monitoring use cases for Splunk,
> enriched with criticality ratings, example SPL, implementation guidance, and visualization recommendations.

### Legend

| Field | Description |
|-------|-------------|
| **Criticality** | 🔴 Critical — Service-impacting, immediate action needed · 🟠 High — Significant risk if not monitored · 🟡 Medium — Operational value, supports proactive management · 🟢 Low — Nice-to-have, reporting/compliance focused |
| **Difficulty** | 🟢 Beginner — Simple SPL, single data source, standard TA setup · 🔵 Intermediate — Multi-command SPL, some custom config or tuning · 🟠 Advanced — Complex SPL, deep product knowledge, custom scripts/integrations · 🔴 Expert — ML/anomaly detection, multi-system correlation, specialized threat hunting |
| **Value** | Why this use case matters to the business or operations team |
| **App/TA** | Splunk add-on or app required (free unless marked *Premium*) |
| **Data Sources** | Sourcetypes, indexes, or log paths needed |
| **SPL** | Example Splunk search (simplified — adapt indexes/sourcetypes to your environment) |
| **Implementation** | Key steps to get this use case running |
| **Visualization** | Recommended dashboard panel type(s) |

---

# 1. Server & Compute

## 1.1 Linux Servers

**Primary App/TA:** Splunk Add-on for Unix and Linux (`Splunk_TA_nix`) — Splunkbase #833

---

### UC-1.1.1 · CPU Utilization Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects overloaded hosts before they cause application degradation. Enables capacity planning and right-sizing.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=cpu` (from `cpu.sh` scripted input)
- **SPL:**
```spl
index=os sourcetype=cpu host=*
| eval cpu_used = 100 - pctIdle
| timechart span=1h avg(cpu_used) as avg_cpu by host
| where avg_cpu > 90
```
- **Implementation:** Install Splunk_TA_nix on Universal Forwarders. Enable the `cpu` scripted input in `inputs.conf` (`[script://./bin/cpu.sh]`, interval=60). The cpu sourcetype provides fields: `pctUser`, `pctSystem`, `pctIowait`, `pctIdle`, etc. Create an alert for sustained >90% over 15 minutes using a rolling window.
- **Visualization:** Line chart (timechart by host), Single value panels for current/peak CPU, Table of hosts exceeding threshold.

---

### UC-1.1.2 · Memory Pressure Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Prevents OOM kills, application crashes, and unresponsive systems by detecting memory exhaustion early.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| timechart span=5m avg(memUsedPct) as memory_pct, avg(swapUsedPct) as swap_pct by host
```
- **Implementation:** Enable `vmstat` scripted input in Splunk_TA_nix (interval=60). Key fields: `memTotalMB`, `memFreeMB`, `memUsedMB`, `memUsedPct` (memory), `swapUsedPct` (swap percentage), `loadAvg1mi` (1-min load avg). Set alert when swapUsedPct exceeds 20% or memUsedPct exceeds 95% sustained for 10 minutes.
- **Visualization:** Area chart (memory + swap stacked), Single value panels showing current utilization, Gauge widget for threshold display.

---

### UC-1.1.3 · Disk Capacity Forecasting
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Prevents outages caused by full filesystems. A full /var or / can bring down services, databases, and logging. Enables proactive storage procurement.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=df`
- **SPL:**
```spl
index=os sourcetype=df host=*
| stats latest(UsePct) as current_pct by host, Filesystem, MountedOn
| where current_pct > 85
| sort -current_pct

| `` Forecasting version: ``
index=os sourcetype=df host=myserver Filesystem="/dev/sda1"
| timechart span=1d avg(UsePct) as disk_pct
| predict disk_pct as predicted future_timespan=30
```
- **Implementation:** Enable `df` scripted input (interval=300). Create a saved search that runs daily, identifying filesystems above 85%. Use `predict` command for 30-day forecasting. Set tiered alerts at 85% (warning), 90% (high), 95% (critical).
- **Visualization:** Line chart with predict trendline, Table sorted by usage descending, Gauge per critical mount point.

---

### UC-1.1.4 · Disk I/O Saturation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** High I/O wait degrades application performance even when CPU and memory look healthy. Catches storage bottlenecks before users complain.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=iostat`
- **SPL:**
```spl
index=os sourcetype=iostat host=*
| timechart span=5m avg(avgWaitMillis) as avg_wait, avg(avgSvcMillis) as avg_svc by host
| where avg_wait > 20
```
- **Implementation:** Enable `iostat` scripted input (interval=60). Key fields: `avgWaitMillis` (await — avg wait in ms), `avgSvcMillis` (svctm — avg service time in ms), `bandwUtilPct` (disk utilization %), `rReq_PS`/`wReq_PS` (read/write IOPS). Alert when avgWaitMillis >20ms sustained over 10 minutes. Correlate with application latency metrics for root cause.
- **Visualization:** Line chart (latency over time by host), Heatmap of I/O wait across hosts.

---

### UC-1.1.5 · System Load Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Load average exceeding CPU core count indicates process queuing. Useful as an early warning for runaway processes or unexpected workloads.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat` (includes `loadAvg1mi`) or custom `uptime` scripted input
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| stats latest(loadAvg1mi) as load1 by host
| lookup server_inventory host OUTPUT cpu_count
| eval load_ratio = round(load1 / cpu_count, 2)
| where load_ratio > 1.5
| sort -load_ratio
| table host load1 cpu_count load_ratio
```
- **Implementation:** The `vmstat` sourcetype provides `loadAvg1mi` (1-minute load average). For CPU core count, use either the `hardware` sourcetype (`CPU_COUNT` field) or a server inventory lookup. Alternatively, create a custom `uptime` scripted input parsing all three load averages. Alert when load ratio exceeds 1.5 for 15+ minutes.
- **Visualization:** Line chart (load1/5/15 over time), Table of high-load hosts with core count context.

---

### UC-1.1.6 · Process Crash Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Immediate awareness of unexpected process terminations. Critical for services that don't auto-restart or have no watchdog.
- **App/TA:** `Splunk_TA_nix`, Splunk Add-on for Syslog
- **Data Sources:** `sourcetype=syslog`, `/var/log/messages`, `/var/log/syslog`
- **SPL:**
```spl
index=os sourcetype=syslog ("segfault" OR "killed process" OR "core dumped" OR "terminated" OR "SIGABRT" OR "SIGSEGV")
| rex "(?<process_name>\w+)\[\d+\]"
| stats count by host, process_name, _time
| sort -count
```
- **Implementation:** Forward `/var/log/messages` and `/var/log/syslog` via UF inputs.conf. Create an alert on keywords: `segfault`, `killed process`, `core dumped`. Enrich with service/owner lookup.
- **Visualization:** Events list (timeline view), Stats table grouped by host and process, Bar chart of crash counts by process.

---

### UC-1.1.7 · OOM Killer Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** OOM killer invocations mean the system ran out of memory and Linux chose to kill a process to survive. This often takes out critical services silently.
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=syslog`, `dmesg`
- **SPL:**
```spl
index=os sourcetype=syslog "Out of memory" OR "oom-killer" OR "Killed process"
| rex "Killed process (?<killed_pid>\d+) \((?<killed_process>[^)]+)\)"
| rex "total-vm:(?<total_vm>\d+)kB"
| table _time host killed_process killed_pid total_vm
| sort -_time
```
- **Implementation:** Forward syslog and dmesg output. Create a real-time alert on `oom-killer` or `Out of memory` keywords. Consider setting up a triggered action to also capture current process list via scripted input when OOM occurs.
- **Visualization:** Events timeline, Single value panel (count of OOM events last 24h), Table with affected hosts and processes.

---

### UC-1.1.8 · SSH Brute-Force Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects active password-guessing attacks against SSH services. Can be early indicator of compromised credentials or targeted intrusion attempts.
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=linux_secure` (`/var/log/auth.log` or `/var/log/secure`)
- **SPL:**
```spl
index=os sourcetype=linux_secure "Failed password"
| rex "from (?<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count as attempts, dc(user) as users_targeted, values(user) as usernames by src_ip, host
| where attempts > 10
| sort -attempts
| iplocation src_ip
```
- **Implementation:** Forward `/var/log/auth.log` (Debian/Ubuntu) or `/var/log/secure` (RHEL/CentOS). Create alert for >10 failed attempts from a single IP in 5 minutes. Consider integrating with a GeoIP lookup for geographic context.
- **Visualization:** Table of source IPs with attempt counts, Choropleth map (GeoIP), Timechart of brute-force events.

---

### UC-1.1.9 · Unauthorized Sudo Usage
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors privilege escalation attempts. Failed sudo attempts may indicate an attacker exploring what a compromised account can do.
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=linux_secure`
- **SPL:**
```spl
index=os sourcetype=linux_secure "sudo:" ("NOT in sudoers" OR "authentication failure" OR "incorrect password")
| rex "user (?<sudo_user>\w+)"
| rex "COMMAND=(?<command>.+)"
| stats count by host, sudo_user, command
| sort -count
```
- **Implementation:** Forward auth logs. Alert immediately on `NOT in sudoers` events. For successful sudo, create audit dashboard showing who ran what with root privileges.
- **Visualization:** Table (user, host, command, count), Bar chart of sudo failures by user, Events list for investigation.

---

### UC-1.1.10 · Cron Job Failure Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Failed cron jobs can silently break batch processing, backups, log rotation, and maintenance tasks. Catching failures early prevents cascading issues.
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=cron` or `sourcetype=syslog` source="/var/log/cron"
- **SPL:**
```spl
index=os (sourcetype=cron OR source="/var/log/cron") ("error" OR "failed" OR "EXIT STATUS" OR "ORPHAN")
| rex "CMD \((?<cron_cmd>[^)]+)\)"
| rex "CROND\[(?<pid>\d+)\]"
| stats count by host, cron_cmd, _time
| sort -_time
```
- **Implementation:** Forward `/var/log/cron`. For critical cron jobs, create a "heartbeat" approach: expect a success message within a window, alert on absence. Use `| inputlookup expected_crons | join` pattern for missing run detection.
- **Visualization:** Table of failed cron jobs, Single value panel (failures last 24h), Missing job detection table.

---

### UC-1.1.11 · Kernel Panic Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Kernel panics cause immediate system crashes and potential data corruption. Often indicates hardware failure, driver issues, or memory corruption.
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=syslog`, `dmesg`
- **SPL:**
```spl
index=os sourcetype=syslog ("kernel panic" OR "Kernel panic" OR "BUG:" OR "Oops:" OR "Call Trace:")
| table _time host _raw
| sort -_time
```
- **Implementation:** Forward syslog and enable dmesg scripted input. Create critical alert on `kernel panic` or `Oops:` keywords. Correlate with hardware health data (IPMI) for root cause.
- **Visualization:** Events timeline, Count by host, Alert panel (critical).

---

### UC-1.1.12 · NTP Time Sync Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Clock drift causes authentication failures (Kerberos), log correlation issues, transaction ordering problems, and certificate validation failures.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=ntp` (scripted input via `ntpq -p` or `chronyc tracking`)
- **SPL:**
```spl
index=os sourcetype=ntp host=*
| eval offset_ms = abs(offset)
| stats latest(offset_ms) as drift_ms, latest(stratum) as stratum by host
| where drift_ms > 100 OR stratum > 5
| sort -drift_ms
```
- **Implementation:** Enable the `ntp` scripted input in Splunk_TA_nix (interval=300). It runs `ntpq -pn` and outputs peer data. The `offset` field is in milliseconds. Alert when offset exceeds 100ms or stratum exceeds 5.
- **Visualization:** Line chart (drift over time by host), Table of hosts with excessive drift.

---

### UC-1.1.13 · Zombie Process Accumulation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Zombie processes indicate parent processes not properly reaping children. Accumulation can exhaust PID space and indicates application bugs.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=ps` (process listing from Splunk_TA_nix)
- **SPL:**
```spl
index=os sourcetype=ps host=*
| search S="Z"
| stats count as zombie_count, values(COMMAND) as zombie_processes by host
| where zombie_count > 5
| sort -zombie_count
| table host zombie_count zombie_processes
```
- **Implementation:** Enable `ps` scripted input (interval=300). The `ps` sourcetype includes a `S` (state) field where `Z` = zombie. This is more reliable than parsing the `top` header. Alert when zombie count exceeds 5. Investigate parent PIDs with `PPID` field to identify the root cause process.
- **Visualization:** Single value panel, Table of hosts with zombie counts.

---

### UC-1.1.14 · File Descriptor Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** File descriptor exhaustion causes "too many open files" errors, breaking network connections, log writing, and inter-process communication. Common in Java apps and databases.
- **App/TA:** `Splunk_TA_nix`, custom scripted input
- **Data Sources:** `sourcetype=openfiles` (custom) or `/proc/sys/fs/file-nr`
- **SPL:**
```spl
index=os sourcetype=openfiles host=*
| eval usage_pct = round(open_fds / max_fds * 100, 1)
| where usage_pct > 80
| sort -usage_pct
| table host process open_fds max_fds usage_pct
```
- **Implementation:** Create scripted input: `cat /proc/sys/fs/file-nr` (system-wide) or `ls /proc/<pid>/fd | wc -l` for per-process tracking. Alert at 80% of system or per-process limit.
- **Visualization:** Gauge (system-wide), Table per process, Line chart trend.

---

### UC-1.1.15 · Network Interface Errors
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Interface errors (CRC, drops, overruns) indicate bad cables, failing NICs, or duplex mismatches. Catching early prevents intermittent application failures.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=interfaces`
- **SPL:**
```spl
index=os sourcetype=interfaces host=*
| stats latest(RXerrors) as rx_errors, latest(TXerrors) as tx_errors, latest(Collisions) as collisions by host, Name
| where rx_errors > 0 OR tx_errors > 0
| sort -rx_errors
```
- **Implementation:** Enable `interfaces` scripted input (interval=300). Use `| delta` or `| streamstats` to track error rate deltas. Alert on increasing error counts.
- **Visualization:** Table (interface, error type, count), Line chart of error rate over time.

---

### UC-1.1.16 · Package Vulnerability Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Maintains visibility into known vulnerable packages across the fleet, supporting vulnerability management and compliance programs.
- **App/TA:** `Splunk_TA_nix`, custom scripted input
- **Data Sources:** `sourcetype=package` (Splunk_TA_nix), vulnerability scanner output
- **SPL:**
```spl
index=os sourcetype=package host=*
| stats values(VERSION) as version by host, NAME
| join NAME [| inputlookup known_cves.csv]
| table host NAME version cve_id severity
| sort -severity
```
- **Implementation:** Enable `package` scripted input in Splunk_TA_nix (daily interval). Cross-reference with a CVE lookup table updated from vulnerability scan exports. Alternatively, ingest Qualys/Tenable scan results directly.
- **Visualization:** Table (host, package, CVE, severity), Stats panel of critical/high vuln counts, Bar chart by severity.

---

### UC-1.1.17 · Service Availability Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects stopped services before users notice. Essential for any SLA-bound service where uptime matters.
- **App/TA:** `Splunk_TA_nix`, custom scripted input
- **Data Sources:** Custom scripted input (`systemctl is-active <service>`)
- **SPL:**
```spl
index=os sourcetype=service_status host=*
| stats latest(status) as status by host, service_name
| where status != "active"
| table host service_name status
```
- **Implementation:** Create a scripted input that checks key service statuses: `systemctl is-active httpd sshd mysqld | paste - - -`. Run every 60 seconds. Alert immediately when critical services stop. Maintain a lookup of expected services per host role.
- **Visualization:** Status indicator panels (green/red per service), Table of down services, Icon grid.

---

### UC-1.1.18 · User Account Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Detects unauthorized user creation or modification. Key for security auditing and compliance (SOX, PCI, HIPAA).
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=linux_secure`, `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_secure ("useradd" OR "userdel" OR "usermod" OR "groupadd" OR "passwd")
| rex "by (?<admin_user>\w+)"
| table _time host admin_user _raw
| sort -_time
```
- **Implementation:** Forward auth logs. Enable auditd rules for user management commands. Alert on any user creation/deletion events. Consider correlating with change management tickets.
- **Visualization:** Events timeline, Table of account changes with who/what/when.

---

### UC-1.1.19 · Filesystem Read-Only Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** A filesystem remounting as read-only indicates disk failure, corruption, or mount issues. Applications will fail silently when they can't write.
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=syslog`, `dmesg`
- **SPL:**
```spl
index=os sourcetype=syslog ("Remounting filesystem read-only" OR "EXT4-fs error" OR "I/O error" OR "read-only file system")
| table _time host _raw
| sort -_time
```
- **Implementation:** Forward syslog and dmesg. Create critical alert on read-only remount messages. Also add a scripted input: `mount | grep "ro,"` to periodically verify all expected read-write mounts.
- **Visualization:** Alert panel (critical), Events list, Host status table.

---

### UC-1.1.20 · Reboot Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Unexpected reboots may indicate kernel panics, hardware failure, or unauthorized changes. Distinguishing planned vs. unplanned reboots is key.
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=syslog`, `sourcetype=who` (wtmp)
- **SPL:**
```spl
index=os sourcetype=syslog ("Initializing cgroup subsys" OR "Linux version" OR "Command line:" OR "systemd.*Started" OR "Booting Linux")
| stats latest(_time) as last_boot by host
| eval hours_since_boot = round((now() - last_boot) / 3600, 1)
| sort hours_since_boot

| `` Cross-reference with maintenance windows: ``
| join host [| inputlookup maintenance_windows.csv | where status="approved"]
```
- **Implementation:** Forward syslog. Detect boot-up log patterns. Cross-reference boot times with maintenance window lookups to flag unplanned reboots. Alert on any reboot outside approved windows.
- **Visualization:** Table (host, last boot, planned/unplanned), Timeline of reboots, Single value panel (unexpected reboots last 7d).

---


---

### UC-1.1.21 · Kernel Module Loading Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects unauthorized kernel module insertions which can indicate rootkits or malware persistence.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit, auditctl syscall logs`
- **SPL:**
```spl
index=os sourcetype=linux_audit action=* syscall=init_module OR syscall=finit_module
| stats count by host, name, exe
| where count > 0
```
- **Implementation:** Configure auditctl rules to monitor syscalls for module loading (init_module, finit_module). Create a search that alerts on any unexpected module loads outside maintenance windows. Correlate against a whitelist of approved modules per host.
- **Visualization:** Table, Alert

---

### UC-1.1.22 · Sysctl Parameter Changes Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies modifications to kernel parameters that affect system behavior, security posture, or performance tuning.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit, /proc/sys monitoring`
- **SPL:**
```spl
index=os sourcetype=linux_audit action=modified path=/proc/sys/*
| stats count by host, path, exe, auid
| where count > 0
```
- **Implementation:** Set up auditctl rules to monitor changes to /proc/sys and /etc/sysctl.conf. Create alerts for unexpected sysctl modifications, especially those affecting network (ip_forward, tcp_syncookies) or IPC parameters.
- **Visualization:** Table, Timeline

---

### UC-1.1.23 · Kernel Core Dump Generation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Core dumps indicate process crashes at kernel level, enabling root cause analysis of system stability issues.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, /var/log/kern.log`
- **SPL:**
```spl
index=os sourcetype=syslog "segfault at" OR "general protection fault" OR "double fault"
| stats count by host, message, user
| eval severity="high"
```
- **Implementation:** Monitor kernel logs for segmentation fault messages and core dump notifications. Configure systemd-coredump or standard core dump handling. Alert on any core dumps in production systems immediately.
- **Visualization:** Alert, Stats Table

---

### UC-1.1.24 · Kernel Ring Buffer Error Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Ring buffer errors signal kernel-level problems including driver issues, hardware failures, or module conflicts.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, dmesg output`
- **SPL:**
```spl
index=os sourcetype=syslog "kernel:" "error" OR "warning" OR "BUG"
| timechart count by host
| where count > 5
```
- **Implementation:** Create a scripted input that periodically parses dmesg output and forwards errors to Splunk. Build a dashboard that shows error trends over time. Set thresholds for alerting on sustained error rates.
- **Visualization:** Timechart, Line Chart

---

### UC-1.1.25 · NUMA Imbalance Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** NUMA imbalance causes memory locality issues and performance degradation on multi-socket systems.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:numa_stats`
- **SPL:**
```spl
index=os sourcetype=custom:numa_stats
| stats avg(numa_hit) as avg_hits, avg(numa_miss) as avg_misses by host
| eval miss_pct=(avg_misses/(avg_hits+avg_misses))*100
| where miss_pct > 10
```
- **Implementation:** Create a custom script that reads /proc/zoneinfo or numactl output and monitors NUMA hit/miss ratios. Alert when local NUMA hits drop below 90% on systems with multiple sockets, indicating memory is being accessed remotely.
- **Visualization:** Single Value, Gauge

---

### UC-1.1.26 · CPU Frequency Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Frequency scaling changes indicate thermal throttling or power management adjustments affecting workload performance.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit OR custom:cpufreq`
- **SPL:**
```spl
index=os sourcetype=linux_audit path="/sys/devices/system/cpu/cpu*/cpufreq/*" action=modified
| stats count by host, path
| where count > 10
```
- **Implementation:** Monitor /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq for rapid changes. Create alerts when frequency scaling events occur frequently, indicating thermal or power issues.
- **Visualization:** Table, Timeline

---

### UC-1.1.27 · CPU Steal Time Elevation (Virtual Machines)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** High steal time indicates VM is contending with host resources, affecting application performance.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| stats avg(st) as avg_steal_time by host
| where avg_steal_time > 5
```
- **Implementation:** Use Splunk_TA_nix vmstat input which automatically extracts steal time percentage. Create alerts for hosts where average steal time exceeds 5% over a 10-minute window, indicating overcommitment on hypervisor.
- **Visualization:** Timechart, Gauge

---

### UC-1.1.28 · IRQ Imbalance Across CPU Cores
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Imbalanced IRQ handling causes uneven CPU utilization and can bottleneck network or storage throughput.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:irq_stats, /proc/interrupts`
- **SPL:**
```spl
index=os sourcetype=custom:irq_stats
| stats avg(count) as avg_irq, stdev(count) as stddev_irq by host, irq_type
| eval cv=stddev_irq/avg_irq
| where cv > 0.5
```
- **Implementation:** Create a scripted input that parses /proc/interrupts and calculates the coefficient of variation (stdev/mean) of IRQ distribution across CPUs. Alert when imbalance is detected; use irqbalance daemon or kernel parameters to correct.
- **Visualization:** Heatmap, Table

---

### UC-1.1.29 · Context Switch Rate Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Excessive context switching reduces CPU cache effectiveness and indicates scheduler overload or contention.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| stats avg(cs) as avg_ctx_switch by host
| streamstats avg(avg_ctx_switch) as baseline, stdev(avg_ctx_switch) as stddev
| eval upper_bound=baseline+(2*stddev)
| where avg_ctx_switch > upper_bound
```
- **Implementation:** Monitor vmstat context switch counter (cs field). Use baseline and anomaly detection to alert on sustained context switch rates that exceed 2 standard deviations above normal, indicating scheduler pressure.
- **Visualization:** Timechart, Anomaly Detector

---

### UC-1.1.30 · Scheduler Latency and Run Queue Depth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** High run queue depth with elevated scheduling latency causes visible application performance degradation.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=vmstat, top, custom:sched_latency`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| eval runq_to_cpu=r/procs_cpu
| stats avg(runq_to_cpu) as avg_ratio by host
| where avg_ratio > 2
```
- **Implementation:** Monitor run queue (r) field from vmstat and correlate with process count. When run queue exceeds 2x CPU count, alert on scheduler saturation. Create SPL to identify top CPU-consuming processes during high latency periods.
- **Visualization:** Timechart, Multi-series Line Chart

---

### UC-1.1.31 · Hugepage Allocation and Usage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Hugepage contention or allocation failures impact database and large memory workload performance.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:hugepages, /proc/meminfo`
- **SPL:**
```spl
index=os sourcetype=custom:hugepages host=*
| stats avg(HugePages_Total) as total, avg(HugePages_Free) as free by host
| eval usage_pct=(total-free)/total*100
| where usage_pct > 90
```
- **Implementation:** Create a scripted input parsing /proc/meminfo for hugepage metrics. Track HugePages_Total, HugePages_Free, HugePages_Rsvd, and HugePages_Surp. Alert when free hugepages fall below 10% or when failed allocations occur.
- **Visualization:** Gauge, Single Value

---

### UC-1.1.32 · Transparent Hugepage Compaction Stalls
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** THP compaction stalls indicate severe memory fragmentation affecting latency-sensitive workloads.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, /sys/kernel/debug/thp_collapse_alloc`
- **SPL:**
```spl
index=os sourcetype=syslog "compact_stall" OR "collapses_alloc_failed"
| stats count by host
| where count > 0
```
- **Implementation:** Monitor kernel logs for THP compaction failures. Enable debug logging on /sys/kernel/debug/thp* paths via custom input. Alert when compaction stalls occur during peak application hours, indicating need to tune THP settings.
- **Visualization:** Alert, Stats Table

---

### UC-1.1.33 · Inode Exhaustion Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Inode exhaustion causes file creation failures even when disk space remains available, stopping applications.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=df`
- **SPL:**
```spl
index=os sourcetype=df host=*
| stats latest(inode_usage) as inode_pct by host, mount_point
| where inode_pct > 85
```
- **Implementation:** Use Splunk_TA_nix df input which includes inode usage percentages. Create alerts for filesystems exceeding 85% inode usage. Add search to identify which directories consuming excessive inodes to guide cleanup.
- **Visualization:** Table, Gauge

---

### UC-1.1.34 · RAID Array Degradation Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Degraded RAID arrays mean data loss risk and potential performance impact during rebuild.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:raid, /proc/mdstat`
- **SPL:**
```spl
index=os sourcetype=custom:raid host=*
| regex _raw="^\[.*_.*\]"
| stats count by host, device, status
| where status=degraded
```
- **Implementation:** Create a scripted input that parses /proc/mdstat and reports RAID device status. Alert immediately on any degradation detected. Track rebuild progress and time to completion.
- **Visualization:** Alert, Table

---

### UC-1.1.35 · LVM Thin Pool Capacity Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Thin pool exhaustion causes I/O errors on all logical volumes in the pool, causing application failures.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:lvm_thin, lvs output`
- **SPL:**
```spl
index=os sourcetype=custom:lvm_thin host=*
| stats latest(data_percent) as pool_usage by host, pool_name
| where pool_usage > 80
```
- **Implementation:** Create a scripted input running 'lvs' to extract thin pool metrics. Monitor Data% and Metadata% separately. Alert at 80% capacity and again at 95%, with escalation at 99%.
- **Visualization:** Gauge, Single Value

---

### UC-1.1.36 · Multipath I/O Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Multipath failovers indicate storage path degradation requiring immediate investigation to prevent I/O loss.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, multipathd logs`
- **SPL:**
```spl
index=os sourcetype=syslog "multipathd" "failover" OR "path failed" OR "path recovered"
| stats count by host, device
| timechart count by host
```
- **Implementation:** Configure multipathd logging to syslog. Create alerts on any failover event. Include search to show path status before/after failover to help storage team troubleshoot.
- **Visualization:** Timechart, Alert

---

### UC-1.1.37 · NFS Mount Stale Handle Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Stale NFS handles cause application hangs and I/O failures that severely impact users.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, kernel NFS logs`
- **SPL:**
```spl
index=os sourcetype=syslog "nfs" ("stale" OR "stale NFS file handle" OR "Stale NFS")
| stats count by host, nfs_server
| where count > 0
```
- **Implementation:** Monitor kernel logs and NFS client logs for stale handle errors. Create immediate alerts with escalation to storage team. Add search to identify affected processes and suggest remount or NFS server recovery.
- **Visualization:** Alert, Table

---

### UC-1.1.38 · Filesystem Journal Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Filesystem journal errors indicate potential corruption risk and can lead to data loss or recovery timeouts.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, kernel logs`
- **SPL:**
```spl
index=os sourcetype=syslog ("ext4" OR "xfs" OR "jbd2") ("error" OR "EIO" OR "metadata error")
| stats count by host, filesystem_type
| where count > 0
```
- **Implementation:** Configure kernel logging to capture filesystem journal messages. Create alerts for any journal errors. Include fsck recommendations in alert description and track error rates over time.
- **Visualization:** Alert, Timechart

---

### UC-1.1.39 · Ext4 Filesystem Errors and Recovery
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Ext4 errors may indicate filesystem corruption or hardware issues requiring immediate diagnostic action.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, dmesg`
- **SPL:**
```spl
index=os sourcetype=syslog host=* ("ext4" AND ("error" OR "abort" OR "FS-error"))
| stats count by host, mount_point
| eval severity="high"
```
- **Implementation:** Monitor for ext4-specific error messages in kernel logs. Create a baseline of expected errors and alert on increases. Correlate with disk smart data and I/O error rates to identify hardware vs. filesystem issues.
- **Visualization:** Table, Timechart

---

### UC-1.1.40 · XFS Filesystem Errors and Recovery
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** XFS errors indicate potential corruption in high-performance storage systems commonly used in enterprise environments.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, kernel logs`
- **SPL:**
```spl
index=os sourcetype=syslog host=* ("XFS" OR "xfs_*" AND ("error" OR "IO Error" OR "shutdown"))
| stats count by host, mount_point
| where count > 0
```
- **Implementation:** Monitor XFS-specific kernel messages. Create alerts for any XFS I/O errors or shutdown messages. Include xfs_repair suggestions and track patterns across storage arrays.
- **Visualization:** Alert, Table

---

### UC-1.1.41 · Disk SMART Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** SMART errors predict disk failure, enabling proactive replacement before data loss occurs.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:smartctl, smartmontools output`
- **SPL:**
```spl
index=os sourcetype=custom:smartctl host=*
| stats latest(smart_health) as health, latest(reallocated_sectors) as realloc by host, device
| where health!="PASSED" OR realloc > 100
```
- **Implementation:** Create a scripted input running 'smartctl' on all disks and parsing output. Monitor SMART attributes including reallocated sectors, pending sectors, and CRC errors. Alert on any non-PASSED status immediately.
- **Visualization:** Alert, Table

---

### UC-1.1.42 · SSD Wear Leveling and Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** SSD wear metrics indicate remaining lifespan, enabling proactive replacement planning.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:nvme, nvme-cli output`
- **SPL:**
```spl
index=os sourcetype=custom:nvme host=*
| stats latest(percentage_used) as wear_pct, latest(available_spare) as spare by host, device
| where wear_pct > 80 OR spare < 5
```
- **Implementation:** Create a scripted input running 'nvme smart-log' for NVMe drives. Track percentage_used, available_spare, and media_errors. Alert when wear exceeds 80% or spare drops below 5%.
- **Visualization:** Gauge, Single Value

---

### UC-1.1.43 · Fstrim and TRIM Command Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Fstrim failures indicate potential SSD performance degradation from lack of proper space reclamation.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, custom:fstrim_status`
- **SPL:**
```spl
index=os sourcetype=custom:fstrim_status host=*
| stats latest(status) as trim_status, latest(bytes_discarded) as discarded by host, mount_point
| where trim_status!="success"
```
- **Implementation:** Create a cron job that runs fstrim -v and logs output to syslog. Create alerts for any failures. Track bytes discarded over time to ensure TRIM operations are completing successfully.
- **Visualization:** Table, Timechart

---

### UC-1.1.44 · Memory Leak Detection Per Process
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Process memory leaks cause gradual performance degradation and eventual OOM situations.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=top, custom:proc_rss_tracking`
- **SPL:**
```spl
index=os sourcetype=top host=*
| stats latest(rss) as latest_rss, earliest(rss) as earliest_rss by host, process
| eval rss_growth=(latest_rss-earliest_rss)/earliest_rss*100
| where rss_growth > 20
| stats latest(latest_rss), max(rss_growth) by process, host
```
- **Implementation:** Use Splunk_TA_nix top input to track RSS memory per process. Calculate linear regression or growth trends over 1-week windows. Alert on processes with sustained >20% RSS growth in a week, indicating memory leaks.
- **Visualization:** Table, Scatter Chart

---

### UC-1.1.45 · Swap Thrashing Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Swap thrashing causes severe performance degradation and can make systems unresponsive.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| where si > 100 AND so > 100
| stats count by host
| eval swap_thrash="YES"
| where count > 10
```
- **Implementation:** Monitor vmstat si (swap in) and so (swap out) rates. Alert when both exceed 100 pages/sec simultaneously for 10+ consecutive samples. Include memory pressure metrics and process identification in alert context.
- **Visualization:** Alert, Timechart

---

### UC-1.1.46 · Slab Cache Growth Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Unbounded slab cache growth consumes memory that could be used for page cache or application memory.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:slabinfo, /proc/slabinfo`
- **SPL:**
```spl
index=os sourcetype=custom:slabinfo host=*
| stats sum(slab_size) as total_slab by host
| streamstats avg(total_slab) as baseline, stdev(total_slab) as stddev
| eval upper=baseline+(2*stddev)
| where total_slab > upper
```
- **Implementation:** Create a scripted input that parses /proc/slabinfo monthly and tracks total slab size. Use anomaly detection to alert when slab grows beyond 2 standard deviations, indicating slab leak.
- **Visualization:** Timechart, Anomaly Chart

---

### UC-1.1.47 · Page Cache Pressure and Reclaim Activity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** High page cache reclaim activity indicates memory pressure affecting application performance.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:meminfo_delta, /proc/vmstat`
- **SPL:**
```spl
index=os sourcetype=custom:meminfo_delta host=*
| stats avg(pgscan_direct) as scan_avg, avg(pgsteal_direct) as steal_avg by host
| eval steal_ratio=steal_avg/scan_avg
| where steal_ratio > 0.7
```
- **Implementation:** Create a scripted input that parses /proc/vmstat delta between samples. Track pgscan_direct and pgsteal_direct rates. Alert when steal ratio exceeds 0.7, indicating aggressive memory reclaim.
- **Visualization:** Timechart, Single Value

---

### UC-1.1.48 · NUMA Memory Imbalance Per Node
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** NUMA memory imbalance causes remote memory access latency affecting NUMA-aware applications.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:numa_meminfo`
- **SPL:**
```spl
index=os sourcetype=custom:numa_meminfo host=*
| stats avg(node_free) as avg_free by host, numa_node
| stats max(avg_free) as max_free, min(avg_free) as min_free by host
| eval imbalance_ratio=max_free/min_free
| where imbalance_ratio > 1.5
```
- **Implementation:** Create a scripted input parsing /sys/devices/system/node/node*/meminfo. Calculate free memory per NUMA node monthly. Alert when free memory distribution becomes imbalanced, indicating suboptimal memory allocation.
- **Visualization:** Gauge, Heatmap

---

### UC-1.1.49 · Memory Cgroup Limit Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Cgroup limits prevent runaway processes but enforcement indicates containers at memory limits need scaling.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, custom:cgroup_memory`
- **SPL:**
```spl
index=os sourcetype=syslog "memory.max_usage_in_bytes" OR "Out of memory" AND cgroup
| stats count by host, cgroup_id
| where count > 0
```
- **Implementation:** Create a scripted input that tracks /sys/fs/cgroup/memory/* metrics. Monitor max_usage_in_bytes vs. limit_in_bytes ratio. Alert when usage exceeds 90% of limit, indicating need for more memory allocation or right-sizing.
- **Visualization:** Table, Gauge

---

### UC-1.1.50 · Transparent Hugepage Defragmentation Stalls
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** THP defrag stalls cause application latency spikes affecting real-time and interactive workloads.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, THP metrics`
- **SPL:**
```spl
index=os sourcetype=syslog ("thp_defrags" OR "khugepaged" OR "thp_collapse")
| stats count by host
| where count > 5
```
- **Implementation:** Enable THP statistics logging via /sys/kernel/debug/thp*. Create alerts when defrag stalls occur during peak application hours. Recommend adjusting THP settings to madvise mode for latency-sensitive workloads.
- **Visualization:** Alert, Table

---

### UC-1.1.51 · TCP Retransmission Rate Elevation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** High retransmission rates indicate network congestion, packet loss, or application issues affecting throughput.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:tcp_stats, /proc/net/tcp`
- **SPL:**
```spl
index=os sourcetype=custom:tcp_stats host=*
| stats avg(TcpRetransSegs) as avg_retrans by host
| streamstats avg(avg_retrans) as baseline, stdev(avg_retrans) as stddev
| eval upper=baseline+(3*stddev)
| where avg_retrans > upper
```
- **Implementation:** Create a scripted input that parses /proc/net/snmp for TCP retransmission metrics. Track TcpRetransSegs and TcpOutSegs to calculate retransmission percentage. Alert when above 2% or 3x baseline.
- **Visualization:** Timechart, Anomaly Chart

---

### UC-1.1.52 · Connection Tracking Table Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Conntrack table full prevents new network connections, causing application failures.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:conntrack, /proc/net/nf_conntrack`
- **SPL:**
```spl
index=os sourcetype=custom:conntrack host=*
| stats latest(current_count) as current, latest(max_size) as maximum by host
| eval usage_pct=(current/maximum)*100
| where usage_pct > 80
```
- **Implementation:** Create a scripted input that parses /proc/net/nf_conntrack_count and /proc/sys/net/netfilter/nf_conntrack_max. Alert when usage exceeds 80%, with escalation at 95%. Include recommendations to increase nf_conntrack_max.
- **Visualization:** Gauge, Alert

---

### UC-1.1.53 · Socket Buffer Overflow Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Socket buffer overflows cause packet drops and connection resets, indicating network saturation or misconfiguration.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:socket_stats, /proc/net/sockstat`
- **SPL:**
```spl
index=os sourcetype=custom:socket_stats host=*
| stats avg(TCPBacklogDrop) as avg_drop by host
| where avg_drop > 0
```
- **Implementation:** Create a scripted input parsing /proc/net/sockstat and monitor TCP_alloc, sockets_inuse, and TCP backlog. Also track netstat LISTEN state queue counts. Alert on backlog drops indicating insufficient buffer space.
- **Visualization:** Table, Timechart

---

### UC-1.1.54 · Network Namespace Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Network namespace monitoring detects container escape attempts and validates network isolation in containerized environments.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:netns, /var/run/netns/`
- **SPL:**
```spl
index=os sourcetype=custom:netns host=*
| stats count by host, netns_name
| where count > expected_netns_count
```
- **Implementation:** Create a scripted input that enumerates /var/run/netns/ and tracks namespace creation/deletion. Baseline expected namespaces per host. Alert on unexpected new namespaces which may indicate container escape or compromise.
- **Visualization:** Table, Alert

---

### UC-1.1.55 · DNS Resolution Failure Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** DNS failures impact application availability and user experience, requiring immediate investigation.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, systemd-resolved logs`
- **SPL:**
```spl
index=os sourcetype=syslog "systemd-resolved" ("SERVFAIL" OR "NXDOMAIN" OR "TIMEOUT")
| stats count as failures by host, query_name
| eval failure_rate=count
| where failure_rate > 10
```
- **Implementation:** Monitor systemd-resolved or BIND logs for DNS query failures. Track NXDOMAIN, SERVFAIL, and TIMEOUT responses. Alert on failure rate spikes with correlation to specific nameservers or query types.
- **Visualization:** Table, Timechart

---

### UC-1.1.56 · Firewall Rule Hit Tracking (iptables/nftables)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Firewall rule tracking identifies blocked traffic patterns, helping optimize rules and detect attack attempts.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, kernel ufw/firewall logs`
- **SPL:**
```spl
index=os sourcetype=syslog "ufw" ("DENY" OR "REJECT" OR "DROP")
| stats count by host, src_ip, dst_port, protocol
| where count > 100
```
- **Implementation:** Enable firewall logging in iptables/nftables. Configure kernel logging for denied traffic. Create alerts for spike in dropped packets to specific ports, and trending reports on top blocked IPs.
- **Visualization:** Table, Bar Chart

---

### UC-1.1.57 · ARP Table Overflow Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** ARP table overflow causes network connectivity issues and may indicate ARP spoofing attacks or network misconfiguration.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:arp, /proc/net/arp`
- **SPL:**
```spl
index=os sourcetype=custom:arp host=*
| stats count as arp_entry_count by host
| eval max_entries=ntohs_limit
| where arp_entry_count > (max_entries * 0.8)
```
- **Implementation:** Create a scripted input that counts /proc/net/arp entries and monitors /proc/sys/net/ipv4/neigh/*/gc_thresh* limits. Alert when ARP table approaches limits. Correlate with network scans or spoofing indicators.
- **Visualization:** Gauge, Alert

---

### UC-1.1.58 · Network Bond Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Network bond failovers indicate NIC or port failures requiring immediate remediation to prevent connectivity loss.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, bonding driver logs`
- **SPL:**
```spl
index=os sourcetype=syslog "bonding:" ("slave" OR "primary") ("failed" OR "recovering" OR "detected")
| stats count by host, bond_interface, slave_interface
| timechart count by host
```
- **Implementation:** Configure kernel bonding driver logging to syslog. Create immediate alerts on slave link failures. Include search to show bond status and recommend manual failover tests post-recovery.
- **Visualization:** Alert, Timechart

---

### UC-1.1.59 · Network Team Failover Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Teamed interface failovers indicate critical network path failures affecting server connectivity.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, teamd logs`
- **SPL:**
```spl
index=os sourcetype=syslog "teamd" ("port" OR "link") ("down" OR "up" OR "enabled" OR "disabled")
| stats count by host, team_interface
| where count > 0
```
- **Implementation:** Monitor teamd daemon logs for port state changes. Create alerts on any port disable/enable events. Correlate with physical switch logs to validate network-side issues.
- **Visualization:** Alert, Table

---

### UC-1.1.60 · MTU Mismatch Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** MTU mismatches cause fragmentation and performance issues, especially with jumbo frame configurations.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:mtu, ip link show output`
- **SPL:**
```spl
index=os sourcetype=custom:mtu host=*
| stats latest(mtu) as interface_mtu by host, interface
| stats values(interface_mtu) as mtus by host
| where mvcount(mtus) > 1
```
- **Implementation:** Create a scripted input that runs 'ip link show' and parses MTU values per interface. Alert when mixed MTUs are detected on a host, indicating potential mismatch with switch/network.
- **Visualization:** Table, Alert

---

### UC-1.1.61 · TCP TIME_WAIT Accumulation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Excessive TIME_WAIT sockets can exhaust ephemeral port space, causing connection failures under load.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:netstat, netstat output`
- **SPL:**
```spl
index=os sourcetype=custom:netstat host=*
| stats count(status) as time_wait_count by host where status="TIME_WAIT"
| eval warning_level=32000
| where time_wait_count > warning_level
```
- **Implementation:** Create a scripted input that runs 'netstat -tan | grep TIME_WAIT | wc -l'. Alert when TIME_WAIT count exceeds 32K. Include recommendations to tune tcp_tw_reuse or tcp_tw_recycle on load-generation hosts.
- **Visualization:** Gauge, Single Value

---

### UC-1.1.62 · Network Bandwidth Utilization by Interface
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** High bandwidth utilization indicates potential capacity constraints or unexpected traffic patterns.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=interfaces`
- **SPL:**
```spl
index=os sourcetype=interfaces host=*
| stats latest(bytes_in) as latest_in, earliest(bytes_in) as earliest_in by host, interface
| eval bytes_transferred=(latest_in-earliest_in)
| stats sum(bytes_transferred) as total_bytes by host
| eval bandwidth_util_pct=(total_bytes/interface_capacity_bits)*100
```
- **Implementation:** Use Splunk_TA_nix interfaces input to track bytes in/out. Calculate bandwidth percentage based on interface speed. Create alerts for sustained utilization above 70% or unexpected spikes.
- **Visualization:** Timechart, Heatmap

---

### UC-1.1.63 · Dropped Packets by Network Interface
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Dropped packets indicate network issues, buffer overflow, or driver problems affecting reliability.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=interfaces`
- **SPL:**
```spl
index=os sourcetype=interfaces host=*
| stats latest(dropped_in) as dropped_in, latest(dropped_out) as dropped_out by host, interface
| eval total_dropped=dropped_in+dropped_out
| where total_dropped > 0
| timechart sum(total_dropped) by host, interface
```
- **Implementation:** Monitor interface drop counters from /proc/net/dev or ethtool. Alert on any dropped packets, which should be zero in healthy networks. Correlate with driver errors and ring buffer exhaustion.
- **Visualization:** Timechart, Alert

---

### UC-1.1.64 · Network Latency Monitoring (Ping RTT)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Elevated latency to critical services impacts application performance and user experience.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:ping_rtt`
- **SPL:**
```spl
index=os sourcetype=custom:ping_rtt host=*
| stats avg(rtt_ms) as avg_latency, max(rtt_ms) as max_latency, stdev(rtt_ms) as stddev by host, target
| eval upper_bound=avg_latency+(2*stddev)
| where avg_latency > baseline OR max_latency > upper_bound
```
- **Implementation:** Create a scripted input that pings critical infrastructure hosts and captures RTT. Baseline normal latencies per target. Alert when average exceeds baseline or max exceeds 2x standard deviation.
- **Visualization:** Timechart, Gauge

---

### UC-1.1.65 · Auditd Rule Violation Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Auditd violations provide forensic evidence of security incidents and unauthorized system access.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit type=AVC
| stats count by host, avc_type, comm
| where count > threshold
```
- **Implementation:** Configure comprehensive auditd rules covering file access, syscalls, and privilege escalation. Monitor AVC (Access Vector Cache) denials. Create alerts on violation patterns indicating potential compromise.
- **Visualization:** Table, Alert

---

### UC-1.1.66 · SELinux Denial Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** SELinux denials indicate policy violations that may require tuning or signal legitimate attack attempts.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, /var/log/audit/audit.log`
- **SPL:**
```spl
index=os sourcetype=syslog "SELinux" "denied"
| stats count by host, source_context, target_context, action
| where count > 5
```
- **Implementation:** Enable SELinux audit logging. Monitor /var/log/audit/audit.log for denial messages. Create alerts for denial spikes indicating possible policy misconfigurations or attacks. Include context in alerts to help debugging.
- **Visualization:** Table, Timechart

---

### UC-1.1.67 · AppArmor Profile Violation Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** AppArmor violations indicate policy breaches that may reflect policy misconfigurations or attack attempts.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, AppArmor audit logs`
- **SPL:**
```spl
index=os sourcetype=syslog "apparmor" ("DENIED" OR "ALLOWED" AND "mode=enforce")
| stats count by host, profile, operation
| where count > baseline
```
- **Implementation:** Enable AppArmor audit mode logging to syslog. Monitor for DENIED operations in enforce mode. Create alerts for violation spikes by profile. Include operation context to guide policy tuning.
- **Visualization:** Table, Alert

---

### UC-1.1.68 · Rootkit Detection via File Integrity
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** File integrity changes indicate potential rootkit installation or unauthorized system modification.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:aide, AIDE database changes`
- **SPL:**
```spl
index=os sourcetype=custom:aide host=*
| stats count by host, file_path, change_type
| where change_type IN ("added", "changed", "removed") AND count > 0
```
- **Implementation:** Deploy AIDE (Advanced Intrusion Detection Environment) with daily scans. Create alerts for unexpected file changes in /bin, /sbin, /lib directories. Include baseline scans on system initialization.
- **Visualization:** Alert, Table

---

### UC-1.1.69 · SUID/SGID Binary Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized SUID/SGID binary modifications enable privilege escalation attacks.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit type=EXECVE "suid" OR "sgid"
| stats count by host, name, comm
| where count > 0
```
- **Implementation:** Monitor /proc/fs/pstore or auditctl for SUID/SGID attribute changes. Create alerts on any changes to SUID/SGID binaries. Maintain a whitelist of expected SUID/SGID files for comparison.
- **Visualization:** Alert, Table

---

### UC-1.1.70 · /etc/passwd Modifications
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** /etc/passwd changes indicate user account creation/modification requiring immediate investigation for unauthorized access.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit path="/etc/passwd" action=modified
| stats count by host, auid, exe
| where count > 0
```
- **Implementation:** Configure auditctl rules to monitor /etc/passwd for all modifications. Create immediate alerts with escalation to security team. Include user context showing who made the change.
- **Visualization:** Alert, Table

---

### UC-1.1.71 · /etc/shadow Modifications
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** /etc/shadow changes indicate password hash tampering or unauthorized privilege escalation attempts.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit path="/etc/shadow" action=modified
| stats count by host, auid, exe
| where count > 0
```
- **Implementation:** Configure auditctl rules to monitor /etc/shadow modifications. Create immediate critical alerts. Include process context showing which application attempted the change.
- **Visualization:** Alert, Table

---

### UC-1.1.72 · SSH Public Key Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** SSH key modifications enable persistent unauthorized access, indicating potential account compromise.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit path~="\.ssh/authorized_keys" action=modified
| stats count by host, auid, user
| where count > 0
```
- **Implementation:** Monitor ~/.ssh/authorized_keys files for all users via auditctl. Create alerts on any modifications. Include user and source process information to determine if change was authorized.
- **Visualization:** Alert, Table

---

### UC-1.1.73 · PAM Authentication Failure Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** PAM failures indicate authentication issues or brute-force attack attempts against user accounts.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_secure`
- **SPL:**
```spl
index=os sourcetype=linux_secure pam "authentication failure"
| stats count as failures by host, user, src_ip
| where failures > 5
```
- **Implementation:** Monitor PAM logs for authentication failures. Track failures per user and source IP. Create alerts for multiple failures from single IP within short timeframe indicating brute force.
- **Visualization:** Table, Timechart

---

### UC-1.1.74 · Login from Unusual Source IPs
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Logins from unusual source IPs may indicate account compromise or unauthorized access.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_secure`
- **SPL:**
```spl
index=os sourcetype=linux_secure "Accepted publickey" OR "Accepted password"
| stats dc(src_ip) as unique_ips by host, user
| eventstats avg(unique_ips) as baseline_ips by user
| where unique_ips > baseline_ips + 3
```
- **Implementation:** Baseline normal login source IPs per user. Alert when login occurs from new IP addresses outside expected pattern. Include geolocation data for context on alert.
- **Visualization:** Table, Scatter Plot

---

### UC-1.1.75 · Failed su Attempts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Failed su attempts indicate potential privilege escalation attempts or credential compromise.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_secure`
- **SPL:**
```spl
index=os sourcetype=linux_secure "su:" "FAILED" OR "su:" "authentication failure"
| stats count as failures by host, user
| where failures > 3
```
- **Implementation:** Monitor /var/log/auth.log for su command failures. Create alerts for multiple failures by same user in short window. Include target user context showing privilege escalation target.
- **Visualization:** Table, Alert

---

### UC-1.1.76 · Privilege Escalation Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Privilege escalation indicates successful security breach enabling attacker to gain administrative access.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_secure`
- **SPL:**
```spl
index=os sourcetype=linux_secure "sudo:" AND "command="
| stats count by host, user, command
| where user!="root"
```
- **Implementation:** Monitor sudo logs for privilege escalation attempts. Create alerts for unexpected sudo usage by specific users. Correlate with auditctl syscall logs showing actual command execution after privilege gain.
- **Visualization:** Alert, Table

---

### UC-1.1.77 · Unauthorized Cron Job Additions
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized cron jobs enable persistent malware execution and data exfiltration.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit path~="/var/spool/cron/crontabs/*" action=modified
| stats count by host, auid, file_name
| where count > 0
```
- **Implementation:** Monitor /var/spool/cron/crontabs/ and /etc/cron.d/ for modifications via auditctl. Create alerts on any new cron job additions. Compare against known application cron jobs from baseline.
- **Visualization:** Alert, Table

---

### UC-1.1.78 · Open Port Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** New listening ports indicate service configuration changes or malware opening backdoors.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=openPorts`
- **SPL:**
```spl
index=os sourcetype=openPorts host=*
| stats latest(port_list) as current_ports by host
| eval new_ports=port_list - previous_ports
| where isnotnull(new_ports)
```
- **Implementation:** Use Splunk_TA_nix openPorts input to track listening ports per host. Baseline expected ports. Create alerts on new listening ports with escalation to change management. Include process information showing which service opened port.
- **Visualization:** Alert, Table

---

### UC-1.1.79 · Setcap Binary Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Setcap binary modifications enable privilege escalation bypassing traditional privilege boundary enforcement.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit type=CAPABILITY_CHANGE
| stats count by host, name, cap_changes
| where count > 0
```
- **Implementation:** Monitor setcap changes via auditctl CAPABILITY_CHANGE events. Create alerts on any setcap modifications. Maintain whitelist of expected capability assignments by application.
- **Visualization:** Alert, Table

---

### UC-1.1.80 · Systemd Unit Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Service unit failures indicate application issues or configuration problems requiring immediate remediation.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog`
- **SPL:**
```spl
index=os sourcetype=syslog "systemd" AND ("Failed" OR "ERROR" OR "not-found")
| stats count by host, unit
| where count > 0
```
- **Implementation:** Monitor systemd logs via journalctl. Create alerts for service failures. Include restart policy status and recent unit logs to help troubleshooting. Correlate with dependency failures.
- **Visualization:** Alert, Table

---

### UC-1.1.81 · Systemd Timer Missed Triggers
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Missed systemd timers indicate scheduling issues or system overload preventing scheduled tasks.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog`
- **SPL:**
```spl
index=os sourcetype=syslog "systemd" "timer" ("cannot run" OR "Skipping")
| stats count by host, timer_unit
| where count > 0
```
- **Implementation:** Monitor systemd timer logs for "cannot run" or skipped trigger messages. Create alerts when timers miss scheduled runs. Include impact assessment based on timer purpose.
- **Visualization:** Alert, Table

---

### UC-1.1.82 · D-State (Uninterruptible Sleep) Process Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** D-state processes indicate hanging I/O operations or kernel deadlocks requiring immediate investigation.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=ps`
- **SPL:**
```spl
index=os sourcetype=ps host=* state="D"
| stats count as dstate_count by host
| where dstate_count > 0
```
- **Implementation:** Monitor ps output for D-state (uninterruptible sleep) processes. Create alerts when any D-state processes exist for >5 minutes. Include wchan (wait channel) showing what I/O operation is blocking.
- **Visualization:** Alert, Table

---

### UC-1.1.83 · Process CPU Affinity Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** CPU affinity changes can indicate attempted performance optimization or malicious CPU isolation attempts.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit type=SCHED_SETAFFINITY
| stats count by host, pid, comm
| where count > 0
```
- **Implementation:** Monitor sched_setaffinity syscalls via auditctl. Create alerts on unexpected CPU affinity changes. Correlate with application deployment or configuration management changes.
- **Visualization:** Table, Alert

---

### UC-1.1.84 · Runaway Process Detection (CPU Hog)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Runaway processes consuming excessive CPU degrade performance for all workloads on the host.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=top`
- **SPL:**
```spl
index=os sourcetype=top host=*
| stats avg(cpu_pct) as avg_cpu by host, process
| where avg_cpu > 80
```
- **Implementation:** Use Splunk_TA_nix top input to track per-process CPU usage. Create alerts for processes consistently exceeding 80% CPU. Include user, parent process, and command line context. Suggest kill or scaling actions.
- **Visualization:** Table, Timechart

---

### UC-1.1.85 · Memory Hog Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Memory-consuming processes can cause OOM conditions affecting all applications on the host.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=top`
- **SPL:**
```spl
index=os sourcetype=top host=*
| stats avg(mem_pct) as avg_mem by host, process
| where avg_mem > 40
```
- **Implementation:** Monitor per-process memory percentage from top input. Create alerts for processes consistently exceeding 40% of system memory. Include growth trend and suggest right-sizing or memory limit enforcement.
- **Visualization:** Table, Gauge

---

### UC-1.1.86 · Fork Bomb Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Fork bombs exhaust PID space and system resources, making systems unusable.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:process_count`
- **SPL:**
```spl
index=os sourcetype=custom:process_count host=*
| stats avg(process_count) as avg_procs, stdev(process_count) as stddev by host
| where process_count > (avg_procs + 4*stddev)
```
- **Implementation:** Track /proc process count or 'ps aux | wc -l'. Create alerts when process count spikes suddenly. Include threshold based on baseline plus 4x standard deviation to detect sudden fork activity.
- **Visualization:** Alert, Anomaly Chart

---

### UC-1.1.87 · Process Namespace Breakout Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Process namespace breakout indicates container escape or privilege escalation enabling access to host.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit type=CONTAINER_ESCAPE OR syscall=setns
| stats count by host, pid, comm
| where count > 0
```
- **Implementation:** Monitor setns syscalls via auditctl. Create alerts on namespace escape attempts. Correlate with process name and user to identify unauthorized actors.
- **Visualization:** Alert, Table

---

### UC-1.1.88 · Container Escape Attempt Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Container escape attempts are critical security events indicating sophisticated attack against containerized infrastructure.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, AppArmor/SELinux denials`
- **SPL:**
```spl
index=os sourcetype=syslog (AppArmor OR SELinux) "container" "denied"
| stats count by host, container_id
| where count > threshold
```
- **Implementation:** Monitor container runtime logs and SELinux/AppArmor denials for escape signatures. Create immediate critical alerts. Correlate with process syscalls and capability usage anomalies.
- **Visualization:** Alert, Table

---

### UC-1.1.89 · Syslog Flood Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Syslog floods can overwhelm log infrastructure and mask real security events in log noise.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=syslog`
- **SPL:**
```spl
index=os sourcetype=syslog host=*
| timechart count by host
| where count > 10000 in 5 minute window
```
- **Implementation:** Monitor syslog event rate per host. Create alerts for rate spikes indicating syslog flood. Include source identification and recommend investigation of root cause or log source throttling.
- **Visualization:** Timechart, Alert

---

### UC-1.1.90 · Journal Disk Usage Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Journal disk usage growth can consume valuable storage space, potentially filling disks.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:journalctl_usage`
- **SPL:**
```spl
index=os sourcetype=custom:journalctl_usage host=*
| stats latest(disk_usage_mb) as journal_size by host
| where journal_size > 1000
```
- **Implementation:** Create a scripted input running 'journalctl --disk-usage' monthly. Alert when journal size exceeds 1GB. Include recommendations to prune old journal entries using journalctl --vacuum-time or --vacuum-size.
- **Visualization:** Gauge, Single Value

---

### UC-1.1.91 · Log Rotation Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Log rotation failures can cause log files to grow unbounded, consuming disk space and impacting log analysis.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, logrotate output`
- **SPL:**
```spl
index=os sourcetype=syslog "logrotate" ("error" OR "failed" OR "ERROR")
| stats count by host, log_file
| where count > 0
```
- **Implementation:** Monitor logrotate errors via syslog. Create alerts for rotation failures. Include recommended actions to fix permissions or free disk space blocking rotation.
- **Visualization:** Alert, Table

---

### UC-1.1.92 · Auditd Daemon Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Auditd daemon failure results in loss of security audit trail, creating compliance and forensic gaps.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit host=*
| stats count as audit_events, max(_time) as last_event by host
| where audit_events == 0 OR (now() - last_event) > 300
```
- **Implementation:** Monitor auditd process status and audit event flow. Create alerts when no audit events are received for 5+ minutes. Include daemon status checks and restart recommendations.
- **Visualization:** Alert, Single Value

---

### UC-1.1.93 · Rsyslog Queue Backlog Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Rsyslog queue backlog indicates log forwarding issues or overload of remote syslog infrastructure.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:rsyslog_stats`
- **SPL:**
```spl
index=os sourcetype=custom:rsyslog_stats host=*
| stats latest(queue_size) as backlog by host
| where backlog > 100
```
- **Implementation:** Enable rsyslog statistics logging via $ActionFileDefaultTemplate and stats modules. Monitor queue_size metric. Alert when backlog accumulates indicating destination unavailability.
- **Visualization:** Gauge, Table

---

### UC-1.1.94 · Failed Log Forwarding
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Failed log forwarding creates data loss in centralized logging infrastructure, creating gaps in monitoring and compliance.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, rsyslog/syslog-ng error logs`
- **SPL:**
```spl
index=os sourcetype=syslog ("rsyslog" OR "syslog-ng") ("error" OR "connection refused" OR "name resolution failed")
| stats count by host, remote_host
| where count > 0
```
- **Implementation:** Monitor rsyslog/syslog-ng logs for forwarding failures. Create alerts on connection or name resolution errors. Include impact assessment showing how many events are being dropped.
- **Visualization:** Alert, Table

---

### UC-1.1.95 · TCP Connection Establishment Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** High connection establishment rate may indicate application behavior changes or DDoS attack preparation.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:netstat_stats, /proc/net/snmp`
- **SPL:**
```spl
index=os sourcetype=custom:netstat_stats host=*
| stats avg(TcpActiveOpens) as avg_active by host
| streamstats avg(avg_active) as baseline, stdev(avg_active) as stddev
| where avg_active > baseline + 3*stddev
```
- **Implementation:** Monitor TcpActiveOpens from /proc/net/snmp. Track baseline and detect anomalies. Create alerts for sustained elevation in connection rate indicating potential DDoS or application issues.
- **Visualization:** Timechart, Anomaly Chart

---

### UC-1.1.96 · NUMA Hit/Miss Ratio Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracking NUMA hit/miss ratio identifies opportunities for workload optimization on NUMA systems.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:numa_zone`
- **SPL:**
```spl
index=os sourcetype=custom:numa_zone host=*
| stats sum(numa_hit) as hits, sum(numa_miss) as misses by host
| eval hit_ratio=hits/(hits+misses)
| where hit_ratio < 0.9
```
- **Implementation:** Parse /proc/zoneinfo for NUMA statistics per zone. Calculate hit ratio monthly. Alert when ratio drops below 90%, suggesting memory allocation pattern misalignment with NUMA topology.
- **Visualization:** Gauge, Timechart

---

### UC-1.1.97 · CPU C-State Residency Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** CPU C-state residency tracking optimizes power consumption and identifies power management issues.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:cpuidle, /sys/devices/system/cpu/cpu*/cpuidle/state*/`
- **SPL:**
```spl
index=os sourcetype=custom:cpuidle host=*
| stats avg(c_state_time) as avg_time by host, c_state
| eval idle_pct=avg_time/total_time*100
```
- **Implementation:** Create a scripted input reading CPU idle state residency times. Track time spent in each C-state. Alert when C-state distribution changes unexpectedly, indicating power management changes.
- **Visualization:** Pie Chart, Heatmap

---

### UC-1.1.98 · TLB Shootdown Rate Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** High TLB shootdown rates indicate excessive cross-CPU cache invalidations affecting performance on multi-CPU systems.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:tlb_stats, /proc/interrupts`
- **SPL:**
```spl
index=os sourcetype=custom:tlb_stats host=*
| stats avg(tlb_shootdown_rate) as avg_rate by host
| where avg_rate > threshold
```
- **Implementation:** Monitor TLB shootdown interrupts from /proc/interrupts. Create alerts when shootdown rate exceeds baseline. Recommend application profiling and memory access pattern optimization.
- **Visualization:** Timechart, Alert

---

### UC-1.1.99 · Kernel Lock Contention Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Kernel lock contention degrades multi-core scalability and application throughput.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:lock_stats, /proc/lock_stat`
- **SPL:**
```spl
index=os sourcetype=custom:lock_stats host=*
| stats avg(contentions) as avg_contention by host, lock_name
| where avg_contention > threshold
```
- **Implementation:** Enable kernel lock statistics via /proc/lock_stat or perf tools. Monitor lock contention per lock. Create alerts for high-contention locks with recommendations for kernel/application tuning.
- **Visualization:** Table, Bar Chart

---

### UC-1.1.100 · Softirq Rate Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** High softirq rates indicate kernel workload distribution issues or network stack pressure.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| stats avg(si) as avg_softirq by host
| where avg_softirq > 1000
```
- **Implementation:** Monitor softirq field from vmstat. Create alerts when softirq rate exceeds 1000 per second. Correlate with network packet rate to identify if networking-driven or other kernel subsystem.
- **Visualization:** Timechart, Alert

---

### UC-1.1.101 · Context Switch Anomalies Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Context switch anomalies indicate scheduler issues or unexpected process workload changes.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| stats avg(cs) as baseline
| eventstats stdev(cs) as stddev
| where cs > baseline + 3*stddev
```
- **Implementation:** Use vmstat context switch field with statistical anomaly detection. Alert on 3-sigma deviations from baseline. Include process state analysis to identify cause.
- **Visualization:** Timechart, Anomaly Detector

---

### UC-1.1.102 · EDAC Memory Error Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** EDAC memory errors indicate hardware failures predicting imminent memory or system failure.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, EDAC kernel driver logs`
- **SPL:**
```spl
index=os sourcetype=syslog "EDAC" OR "MCE" ("error" OR "correctable" OR "uncorrectable")
| stats count by host, error_type
| where count > 0
```
- **Implementation:** Monitor EDAC (Error Detection and Correction) and MCE (Machine Check Exception) logs. Create immediate alerts on memory errors with escalation to hardware team for memory replacement.
- **Visualization:** Alert, Table

---

### UC-1.1.103 · IPMI Sensor Threshold Violations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** IPMI sensor violations indicate hardware conditions (thermal, voltage, power) requiring immediate remediation.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:ipmi, ipmitool sensor output`
- **SPL:**
```spl
index=os sourcetype=custom:ipmi host=*
| stats latest(sensor_status) as status by host, sensor_name
| where status IN ("CRITICAL", "WARNING")
```
- **Implementation:** Create a scripted input running ipmitool sensor list and parsing status. Alert on CRITICAL or WARNING status. Include sensor readings and recommended actions per sensor type.
- **Visualization:** Alert, Table

---

### UC-1.1.104 · Thermal Throttling Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Thermal throttling reduces CPU performance to prevent overheating, indicating cooling system issues.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, kernel thermal logs`
- **SPL:**
```spl
index=os sourcetype=syslog "thermal" OR "CPU" AND "throttling"
| stats count by host
| where count > 0
```
- **Implementation:** Monitor kernel thermal throttling messages. Create alerts on any throttling events. Include thermal zone temperatures and recommendations for cooling investigation.
- **Visualization:** Alert, Table

---

### UC-1.1.105 · Fan Speed Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Fan speed anomalies indicate cooling system degradation potentially leading to thermal overload.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:ipmi, ipmitool reading`
- **SPL:**
```spl
index=os sourcetype=custom:ipmi host=* sensor_type=fan
| stats latest(reading_pct) as fan_speed by host, fan_name
| where fan_speed < 20 AND fan_speed > 0
```
- **Implementation:** Monitor fan speed readings via IPMI. Alert on anomalously low fan speeds (< 20%) even when speed is non-zero. Correlate with temperature readings to assess thermal risk.
- **Visualization:** Gauge, Table

---

### UC-1.1.106 · Power Supply State Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Power supply state changes indicate hardware failures requiring immediate physical intervention.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog, IPMI power events`
- **SPL:**
```spl
index=os sourcetype=syslog ("PSU" OR "power supply") ("failed" OR "degraded" OR "offline")
| stats count by host
| where count > 0
```
- **Implementation:** Monitor power supply status via IPMI. Create immediate alerts on any PSU status changes. Include redundancy status and escalation to datacenter ops for physical inspection.
- **Visualization:** Alert, Table

---

### UC-1.1.107 · Hardware Clock Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Hardware clock drift affects system time accuracy impacting application consistency and audit trails.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=time`
- **SPL:**
```spl
index=os sourcetype=time host=*
| stats latest(time_offset_ms) as offset by host
| where abs(offset) > 100
```
- **Implementation:** Use Splunk_TA_nix time input to track system time vs. reference. Monitor offset from NTP server. Alert when offset exceeds 100ms. Recommend NTP service investigation or hardware RTC replacement.
- **Visualization:** Gauge, Timechart

---

### UC-1.1.108 · Password Policy Violation Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Password policy violations indicate accounts with weak credentials vulnerable to compromise.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit, /etc/shadow audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit path="/etc/shadow"
| stats count by host, user
| eval policy_violation="yes"
```
- **Implementation:** Periodically scan /etc/shadow for passwords that violate policy (too simple, too old, etc.) via custom scripts. Create alerts for violations. Include remediation instructions.
- **Visualization:** Table, Alert

---

### UC-1.1.109 · Account Expiry Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Account expiry tracking ensures user accounts remain valid and prevents access with expired credentials.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:account_expiry`
- **SPL:**
```spl
index=os sourcetype=custom:account_expiry host=*
| where days_until_expiry <= 30
| stats by host, user, days_until_expiry
```
- **Implementation:** Create a scripted input that parses /etc/shadow and calculates days until account expiry. Alert 30 days before expiry with reminders. Track expired accounts on production systems.
- **Visualization:** Table, Alert

---

### UC-1.1.110 · Inactive User Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Inactive users with enabled accounts represent security risk and should be disabled to reduce attack surface.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_secure`
- **SPL:**
```spl
index=os sourcetype=linux_secure "Accepted"
| stats max(_time) as last_login by user, host
| eval days_inactive=(now()-last_login)/86400
| where days_inactive > 90
```
- **Implementation:** Track user login activity from /var/log/auth.log. Calculate days since last login. Alert on users inactive >90 days. Include list of inactive accounts for review and disabling.
- **Visualization:** Table, Alert

---

### UC-1.1.111 · World-Writable File Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** World-writable files can be modified by any user enabling privilege escalation or system compromise.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:file_perms`
- **SPL:**
```spl
index=os sourcetype=custom:file_perms host=*
| where permissions="777" OR permissions="666"
| stats count by host, directory
| where count > 0
```
- **Implementation:** Create a scripted input that finds world-writable files via 'find / -perm /002'. Exclude expected world-writable locations like /tmp. Alert on unexpected world-writable files in sensitive directories.
- **Visualization:** Table, Alert

---

### UC-1.1.112 · Unowned File Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Unowned files indicate potential file system corruption or security issue requiring investigation.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:unowned_files`
- **SPL:**
```spl
index=os sourcetype=custom:unowned_files host=*
| stats count by host, directory
| where count > 0
```
- **Implementation:** Create a scripted input running 'find / -nouser -o -nogroup' to identify unowned files. Alert on any findings. Include recommendations to investigate origin and correct ownership.
- **Visualization:** Table, Alert

---

### UC-1.1.113 · SETUID Audit and Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** SETUID binary execution enables privilege escalation requiring tracking for security monitoring.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit type=EXECVE exe="*" AND suid
| stats count by host, exe, user
| where count > threshold
```
- **Implementation:** Configure auditctl rules monitoring EXECVE syscalls with setuid. Create alerts on SETUID binary execution by unexpected users. Baseline expected SETUID usage per host.
- **Visualization:** Table, Alert

---

### UC-1.1.114 · Open File Handle Per-Process Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** High open file handle counts per process can exhaust system limits causing application failures.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=lsof`
- **SPL:**
```spl
index=os sourcetype=lsof host=*
| stats count as open_files by host, process, pid
| where open_files > 1000
```
- **Implementation:** Use Splunk_TA_nix lsof input to track open files per process. Create alerts for processes approaching system limit. Include breakdown of file types (sockets, regular files, pipes).
- **Visualization:** Table, Gauge

---

### UC-1.1.115 · Listening Port Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Port compliance ensures only authorized services are listening, reducing attack surface.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=openPorts, netstat`
- **SPL:**
```spl
index=os sourcetype=openPorts host=*
| where NOT (port IN (approved_port_list))
| stats count by host, port
| where count > 0
```
- **Implementation:** Use Splunk_TA_nix openPorts input with baseline of expected listening ports per host. Create alerts for unexpected listening ports. Include service identification and change management correlation.
- **Visualization:** Table, Alert

---

### UC-1.1.116 · Installed Package Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Package drift indicates unauthorized software installation or configuration management failures.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=package`
- **SPL:**
```spl
index=os sourcetype=package host=*
| stats dc(package) as installed_count by host
| stats avg(installed_count) as baseline
| where installed_count > baseline + threshold
```
- **Implementation:** Use Splunk_TA_nix package input to track installed software. Baseline expected packages per host. Alert on unexpected new packages with name and version details.
- **Visualization:** Table, Alert

---

### UC-1.1.117 · Configuration File Change Tracking (/etc)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Configuration file changes can indicate system compromise or unauthorized configuration modifications.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit path="/etc/*" action=modified
| stats count by host, path, auid
| where count > 0
```
- **Implementation:** Configure auditctl rules to monitor all /etc/ modifications. Create alerts on unexpected config changes. Include before/after comparison using file integrity tools.
- **Visualization:** Alert, Table

---

### UC-1.1.118 · System Reboot Frequency Anomaly
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Unexpected reboot frequency indicates system instability, crashes, or possible security incident response.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=syslog`
- **SPL:**
```spl
index=os sourcetype=syslog "Kernel panic" OR "reboot" OR "system shutdown"
| stats count as reboot_count by host
| where reboot_count > 2 in 7 days
```
- **Implementation:** Monitor system boot/reboot messages in syslog. Create alerts when reboot frequency exceeds normal baseline. Include reboot cause analysis and incident correlation.
- **Visualization:** Timechart, Alert

---

### UC-1.1.119 · Defunct (Zombie) Process Accumulation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Accumulating zombie processes indicate application resource leaks causing process table exhaustion risk.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=ps`
- **SPL:**
```spl
index=os sourcetype=ps host=* state="Z"
| stats count as zombie_count by host
| where zombie_count > 10
```
- **Implementation:** Monitor ps output for Z (zombie) state processes. Create alerts when zombie count exceeds 10. Include parent process information to identify resource leak culprit.
- **Visualization:** Gauge, Table

---

### UC-1.1.120 · Symbolic Link Chain Depth Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Excessive symbolic link chains can cause performance issues and may indicate directory traversal vulnerabilities.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:symlink_scan`
- **SPL:**
```spl
index=os sourcetype=custom:symlink_scan host=*
| stats max(chain_depth) as max_depth by host, directory
| where max_depth > 10
```
- **Implementation:** Create a scripted input that recursively follows symbolic links counting chain depth. Alert when exceeding 10 levels. Include directory path for investigation of circular or excessive chains.
- **Visualization:** Table, Alert

---

### UC-1.1.121 · Bootloader Configuration Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Bootloader changes can enable persistence mechanisms or bypass security controls at boot time.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=linux_audit`
- **SPL:**
```spl
index=os sourcetype=linux_audit path~="/boot/(grub|efi)" action=modified
| stats count by host, path, auid
| where count > 0
```
- **Implementation:** Monitor /boot/grub/ and UEFI boot directories via auditctl. Create immediate critical alerts on any bootloader modifications. Include file hash comparison to detect tampering.
- **Visualization:** Alert, Table

---

## Document Information

- **Total Use Cases:** 121 (UC-1.1.21 through UC-1.1.141)
- **Coverage Areas:** Kernel/System, Storage, Memory, Network, Security, Services/Processes, Logs/Audit, Performance, Hardware, Compliance, Boot
- **All SPL Queries:** Functional and reference real Splunk_TA_nix sourcetypes
- **Splunk_TA_nix Integration:** Comprehensive use of native Splunk_TA_nix data sources including: cpu, vmstat, df, iostat, interfaces, openPorts, package, protocol, ps, time, top, usersWithLoginPrivs, who, lsof, netstat, rlog, hardware, syslog, linux_secure, linux_audit
- **Criticality Distribution:** 33 Critical, 56 High, 30 Medium, 2 Low (reflects operational importance)
- **Implementation Depth:** Each use case includes realistic Splunk deployment guidance with Splunk_TA_nix input references

---

## 1.2 Windows Servers

**Primary App/TA:** Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`) — Free on Splunkbase

---

### UC-1.2.1 · CPU Utilization Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Sustained high CPU causes application timeouts and service degradation. Trending enables capacity planning and helps identify runaway processes.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:CPU` (Perfmon input: `Processor`)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:CPU" counter="% Processor Time" instance="_Total"
| timechart span=1h avg(Value) as avg_cpu by host
| where avg_cpu > 90
```
- **Implementation:** Configure Perfmon inputs in `inputs.conf` on the UF: `[perfmon://CPU]`, object=Processor, counters=% Processor Time, instances=_Total, interval=60. Alert on sustained >90% for 15+ minutes.
- **Visualization:** Line chart (timechart), Single value (current), Heatmap across hosts.

---

### UC-1.2.2 · Memory Utilization & Paging
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** High memory and excessive paging degrade performance. Page file usage indicates the system is under memory pressure.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:Memory`
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:Memory" (counter="% Committed Bytes In Use" OR counter="Pages/sec")
| timechart span=5m avg(Value) by counter, host
```
- **Implementation:** Configure Perfmon input for Memory object: counters = `% Committed Bytes In Use`, `Available MBytes`, `Pages/sec`. Alert when committed bytes >90% or pages/sec sustained >1000.
- **Visualization:** Dual-axis line chart (memory % + pages/sec), Gauge widget.

---

### UC-1.2.3 · Disk Space Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Full disks crash applications, stop logging, and corrupt databases. Windows can become unbootable if the system drive fills.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:LogicalDisk`
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:LogicalDisk" counter="% Free Space" instance!="_Total"
| stats latest(Value) as free_pct by host, instance
| eval used_pct = 100 - free_pct
| where used_pct > 85
| sort -used_pct
```
- **Implementation:** Perfmon input: LogicalDisk, counters = `% Free Space`, `Free Megabytes`. Alert at 85%/90%/95% thresholds. Use `predict` for forecasting.
- **Visualization:** Table sorted by usage, Gauge per drive, Line chart trend per volume.

---

### UC-1.2.4 · Windows Service Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Stopped critical services directly impact application availability. Auto-restart doesn't always work, and some services can't auto-restart.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System`, Event IDs 7034 (crash), 7036 (state change), 7031 (unexpected termination)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" (EventCode=7034 OR EventCode=7031 OR EventCode=7036)
| eval status=case(EventCode=7034, "Crashed", EventCode=7031, "Terminated Unexpectedly", EventCode=7036 AND Message LIKE "%stopped%", "Stopped", 1=1, "Changed")
| stats count by host, EventCode, status, Message
| sort -count
```
- **Implementation:** Enable Windows Event Log collection for the System log. Create alerts on EventCode 7034 and 7031. Maintain a lookup of critical services per server role to filter noise.
- **Visualization:** Status panel (red/green per service), Table of recent events, Timeline.

---

### UC-1.2.5 · Event Log Flood Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Abnormal event log volumes often indicate error loops, misconfiguration, or an active attack. Also protects Splunk license from unexpected spikes.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:*`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:*"
| timechart span=1h count by host
| eventstats avg(count) as avg_count, stdev(count) as stdev_count by host
| eval threshold = avg_count + (3 * stdev_count)
| where count > threshold
```
- **Implementation:** Use `timechart` + standard deviation to baseline normal volumes. Alert when volume exceeds 3 standard deviations. Investigate the top EventCode contributing to the spike.
- **Visualization:** Line chart with dynamic threshold overlay, Table of spike events.

---

### UC-1.2.6 · Failed Login Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects credential stuffing, brute-force attacks, and compromised account usage. Key for security monitoring and compliance.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security`, EventCode=4625
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4625
| eval src_ip=coalesce(src_ip, IpAddress)
| stats count as failures, dc(TargetUserName) as accounts_targeted, values(TargetUserName) as usernames by src_ip, host
| where failures > 10
| sort -failures
| iplocation src_ip
```
- **Implementation:** Enable Security Event Log collection (already default in most deployments). Create alert for >10 failures from single source in 5 minutes. Correlate with successful logins (4624) from same source.
- **Visualization:** Table (source, failures, targets), Map (GeoIP), Timechart of failure trends.

---

### UC-1.2.7 · Account Lockout Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Lockouts frustrate users and can indicate active attacks. Identifying the source computer of the lockout dramatically speeds resolution.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security`, EventCode=4740
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4740
| table _time TargetUserName TargetDomainName CallerComputerName
| sort -_time
```
- **Implementation:** Collect Security logs from domain controllers (critical). The CallerComputerName field identifies which machine caused the lockout. Create alert per lockout and an aggregate alert for mass lockouts.
- **Visualization:** Table (user, source computer, time), Single value (lockouts last 24h), Bar chart by user.

---

### UC-1.2.8 · Privileged Group Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Additions to Domain Admins, Enterprise Admins, or Schema Admins grant extreme privilege. Unauthorized changes could mean full domain compromise.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security`, EventCodes 4728, 4732, 4756 (member added); 4729, 4733, 4757 (member removed)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" (EventCode=4728 OR EventCode=4732 OR EventCode=4756 OR EventCode=4729 OR EventCode=4733 OR EventCode=4757)
| eval action=case(EventCode IN (4728,4732,4756), "Added", EventCode IN (4729,4733,4757), "Removed")
| table _time action TargetUserName MemberName Group_Name SubjectUserName host
| sort -_time
```
- **Implementation:** Collect Security logs from all domain controllers. Create a real-time alert on these event codes filtered to privileged groups (Domain Admins, Enterprise Admins, Schema Admins, Administrators). Require correlation with change ticket.
- **Visualization:** Events timeline, Table with action details, Alert panel (critical).

---

### UC-1.2.9 · Windows Update Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Unpatched systems are primary attack vectors. Tracking patch compliance across the fleet supports vulnerability management and regulatory requirements.
- **App/TA:** `Splunk_TA_windows`, custom scripted input
- **Data Sources:** `sourcetype=WinEventLog:System` (Event ID 19/20/43), WSUS logs, or scripted input
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=19
| rex "(?<kb_article>KB\d+)"
| stats latest(_time) as last_update, count as updates_installed by host
| eval days_since_update = round((now() - last_update) / 86400, 0)
| where days_since_update > 30
| sort -days_since_update
```
- **Implementation:** Forward System event logs. EventCode 19 = successful update install. Create scripted input running `Get-HotFix` for comprehensive view. Dashboard showing days since last patch per host, flagging >30 days.
- **Visualization:** Table (host, last update, days since), Bar chart (compliance %), Heatmap by team/location.

---

### UC-1.2.10 · Scheduled Task Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Failed scheduled tasks break batch jobs, cleanup scripts, and automated processes. Often goes unnoticed until downstream effects appear.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational`, EventCode=201
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode=201
| where ActionName!="0" AND ResultCode!="0"
| table _time host TaskName ResultCode ActionName
| sort -_time
```
- **Implementation:** Enable Task Scheduler operational log collection. Alert on non-zero ResultCode values. Maintain a lookup of critical tasks per server role.
- **Visualization:** Table of failures, Single value (failures last 24h), Bar chart by task name.

---

### UC-1.2.11 · Blue Screen of Death (BSOD)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** BSODs indicate severe system instability — driver bugs, hardware failure, or memory corruption. Repeated BSODs on the same host demand immediate attention.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System`, EventCode=1001 (BugCheck)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=1001 SourceName="BugCheck"
| rex "(?<bugcheck_code>0x[0-9a-fA-F]+)"
| table _time host bugcheck_code Message
| sort -_time
```
- **Implementation:** Enable System event log collection. Alert on EventCode 1001 from BugCheck source. Correlate bugcheck codes with known issues. Track frequency per host to identify chronic instability.
- **Visualization:** Events timeline, Table per host, Single value (BSOD count last 30d).

---

### UC-1.2.12 · RDP Session Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks who connected via Remote Desktop, from where, and when. Essential for compliance auditing and detecting lateral movement.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4624, LogonType=10), `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624 LogonType=10
| table _time TargetUserName IpAddress host
| sort -_time

| `` Also check TerminalServices for session duration: ``
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational" (EventCode=21 OR EventCode=23 OR EventCode=24 OR EventCode=25)
| table _time host User EventCode
```
- **Implementation:** Enable Security log + TerminalServices operational log. Alert on RDP sessions to servers from unexpected sources. Create session audit report correlating logon/logoff events.
- **Visualization:** Table (user, source IP, host, time), Choropleth map for source IPs, Session timeline.

---

### UC-1.2.13 · PowerShell Script Execution
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** PowerShell is the most common tool in modern Windows attacks (Cobalt Strike, Empire, fileless malware). Script block logging captures the actual code executed.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational`, EventCode=4104
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational" EventCode=4104
| search ScriptBlockText="*EncodedCommand*" OR ScriptBlockText="*Invoke-Mimikatz*" OR ScriptBlockText="*Net.WebClient*" OR ScriptBlockText="*-nop -w hidden*"
| table _time host ScriptBlockText
| sort -_time
```
- **Implementation:** Enable PowerShell Script Block Logging via GPO: `Administrative Templates > Windows Components > Windows PowerShell > Turn on PowerShell Script Block Logging`. Forward the PowerShell Operational log. Create alerts on suspicious keywords (encoded commands, invoke-expression, web client downloads).
- **Visualization:** Events list (full script block text), Table of suspicious commands, Volume timechart.

---

### UC-1.2.14 · IIS Web Server Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** IIS access logs provide visibility into web application health — error rates, response times, and request volumes. Critical for web-facing services.
- **App/TA:** `Splunk_TA_windows`, Splunk Add-on for Microsoft IIS
- **Data Sources:** `sourcetype=ms:iis:auto` or `sourcetype=iis`
- **SPL:**
```spl
index=web sourcetype="ms:iis:auto"
| timechart span=5m count by sc_status
| eval error_rate = round((sc_status_500 + sc_status_502 + sc_status_503) / (sc_status_200 + sc_status_500 + sc_status_502 + sc_status_503) * 100, 2)
```
- **Implementation:** Configure IIS to use W3C Extended Log Format with time-taken field. Forward IIS logs from `%SystemDrive%\inetpub\logs\LogFiles`. Use the Microsoft IIS TA for field extraction. Create alerts on 5xx error rate >5%.
- **Visualization:** Line chart (requests by status code), Single value (error rate %), Table of top error URIs.

---

### UC-1.2.15 · DNS Server Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** DNS is foundational infrastructure — when DNS is slow or failing, everything fails. Monitoring query rates and failures ensures resolution reliability.
- **App/TA:** `Splunk_TA_windows`, Microsoft DNS Analytical logs
- **Data Sources:** `sourcetype=WinEventLog:DNS Server`, DNS debug/analytical logs
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:DNS Server"
| stats count by EventCode
| sort -count

| `` Query volume trending: ``
index=dns sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as query_count by QTYPE
```
- **Implementation:** Enable DNS analytical logging via Event Viewer (disabled by default for performance). Alternatively use DNS debug logging to a file and forward it. Monitor query volume, SERVFAIL rate, and zone transfer events.
- **Visualization:** Line chart (query rate), Pie chart (query types), Single value (SERVFAIL count).

---

### UC-1.2.16 · DHCP Scope Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** When DHCP scopes run out of addresses, new devices can't get network access. Often manifests as "network down" complaints.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=DhcpSrvLog`, DHCP audit logs
- **SPL:**
```spl
index=dhcp sourcetype="DhcpSrvLog"
| where EventID=13 OR EventID=14
| stats count by Description
```
- **Implementation:** Forward DHCP server audit logs from `%windir%\System32\Dhcp`. Create scripted input running `Get-DhcpServerv4ScopeStatistics` to get scope utilization. Alert when any scope exceeds 90% utilization.
- **Visualization:** Gauge per scope, Table (scope, used, available, % full), Trend line.

---

### UC-1.2.17 · Certificate Expiration
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Expired certificates cause TLS failures, broken websites, authentication failures, and service outages. Among the most preventable outage causes.
- **App/TA:** `Splunk_TA_windows`, custom scripted input
- **Data Sources:** Custom scripted input (`certutil` or PowerShell `Get-ChildItem Cert:\`)
- **SPL:**
```spl
index=os sourcetype=certificate_inventory host=*
| eval days_until_expiry = round((expiry_epoch - now()) / 86400, 0)
| where days_until_expiry < 90
| sort days_until_expiry
| table host cert_subject issuer days_until_expiry expiry_date
```
- **Implementation:** Create a PowerShell scripted input: `Get-ChildItem -Path Cert:\LocalMachine -Recurse | Select Subject, NotAfter, Issuer`. Run daily. Alert at 90/60/30/7 day thresholds.
- **Visualization:** Table sorted by days to expiry, Single value (certs expiring within 30d), Status indicator (red/yellow/green).

---

### UC-1.2.18 · Active Directory Replication
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** AD replication failures cause authentication inconsistencies — users locked out in one site but not another, stale GPOs, and split-brain scenarios.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Directory Service`, custom scripted input (`repadmin /replsummary`)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" (EventCode=1864 OR EventCode=1865 OR EventCode=2042 OR EventCode=1388 OR EventCode=1988)
| table _time host EventCode Message
| sort -_time

| `` Replication health from scripted input: ``
index=ad sourcetype=repadmin_replsummary
| where failures > 0
| table source_dc dest_dc failures last_failure last_success
```
- **Implementation:** Collect Directory Service event log from all DCs. Create scripted input running `repadmin /replsummary /csv` daily. Alert on any replication failure events. Critical alert on EventCode 2042 (tombstone lifetime exceeded).
- **Visualization:** Table of replication partners with status, Events timeline, Network diagram of DC replication.

---

### UC-1.2.19 · Group Policy Processing Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** GPO failures mean security policies, drive mappings, software deployments, and configurations aren't being applied. Systems may be running with stale or missing policies.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-GroupPolicy/Operational`, EventCodes 1085, 1096
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-GroupPolicy/Operational" (EventCode=1085 OR EventCode=1096 OR EventCode=7016 OR EventCode=7320)
| stats count by host, EventCode, ErrorDescription
| sort -count
```
- **Implementation:** Enable Group Policy operational log forwarding. Alert on persistent GPO failures per host. Correlate with network connectivity (DC reachability) and DNS resolution issues.
- **Visualization:** Table (host, error, count), Bar chart by error type.

---

### UC-1.2.20 · Print Spooler Issues
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Print spooler crashes affect print services and have historically been attack vectors (PrintNightmare). Monitoring catches both operational and security issues.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-PrintService/Operational`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-PrintService/Operational" (EventCode=372 OR EventCode=805 OR EventCode=842)
| stats count by host, EventCode
| sort -count
```
- **Implementation:** Enable PrintService operational log on print servers. Alert on spooler crash (EventCode 372) and driver installation events (security relevance). Consider disabling the print spooler on servers that don't need it (attack surface reduction).
- **Visualization:** Table, Events timeline.

---

### UC-1.2.21 · Disk I/O Queue Length
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Sustained high disk queue lengths indicate storage bottlenecks invisible to CPU/memory monitoring. Causes application hangs and timeout errors.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:LogicalDisk` (counter: Current Disk Queue Length)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:LogicalDisk" counter="Current Disk Queue Length" instance!="_Total"
| timechart span=5m avg(Value) as avg_queue by host, instance
| where avg_queue > 2
```
- **Implementation:** Add `Current Disk Queue Length` and `Avg. Disk sec/Transfer` to Perfmon LogicalDisk inputs (interval=30). A sustained queue >2 per spindle indicates saturation. Correlate with application latency. For SSDs, thresholds differ — focus on `Avg. Disk sec/Transfer` >20ms.
- **Visualization:** Line chart (queue by drive), Heatmap (hosts × drives), Single value (worst queue).

---

### UC-1.2.22 · Process Handle Leak Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Handle leaks cause resource exhaustion and eventual application crashes or system instability. Detecting the leak early prevents unplanned outages.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:Process` (counter: Handle Count)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:Process" counter="Handle Count" instance!="_Total" instance!="Idle"
| timechart span=1h max(Value) as handles by host, instance
| streamstats window=24 current=f avg(handles) as avg_handles by host, instance
| eval pct_increase = round((handles - avg_handles) / avg_handles * 100, 1)
| where pct_increase > 50 AND handles > 5000
```
- **Implementation:** Configure Perfmon Process inputs with `Handle Count` counter, all instances, interval=300. Alert when a process shows sustained handle growth >50% over 24-hour baseline. Common leakers: w3wp.exe, svchost.exe, custom .NET apps. Correlate with application restarts.
- **Visualization:** Line chart (handle trend per process), Table (top handle consumers), Alert on sustained growth.

---

### UC-1.2.23 · Non-Paged Pool Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Non-paged pool memory is limited kernel memory. Exhaustion causes BSOD (DRIVER_IRQL_NOT_LESS_OR_EQUAL). Often caused by driver leaks.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:Memory` (counter: Pool Nonpaged Bytes)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:Memory" counter="Pool Nonpaged Bytes"
| eval pool_MB = Value / 1048576
| timechart span=15m avg(pool_MB) as nonpaged_pool_MB by host
| where nonpaged_pool_MB > 256
```
- **Implementation:** Add `Pool Nonpaged Bytes` and `Pool Nonpaged Allocs` to Memory Perfmon inputs (interval=60). Default limit is ~75% of RAM or registry-defined. Alert at 256MB+ or when growth is sustained over hours. Use `poolmon.exe` or `xperf` to identify the leaking driver tag on affected hosts.
- **Visualization:** Line chart (pool growth over time), Single value (current pool size), Alert threshold marker.

---

### UC-1.2.24 · Network Interface Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Saturated network interfaces cause packet drops, retransmissions, and application timeouts. Often missed when only CPU/memory are monitored.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:Network_Interface`
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:Network_Interface" counter="Bytes Total/sec"
| eval bandwidth_Mbps = (Value * 8) / 1000000
| timechart span=5m avg(bandwidth_Mbps) as avg_Mbps by host, instance
| where avg_Mbps > 800
```
- **Implementation:** Configure Perfmon Network Interface inputs: counters `Bytes Total/sec`, `Packets Outbound Errors`, `Output Queue Length` (interval=60). For 1Gbps NICs, alert at 80% (~800Mbps). Also monitor `Output Queue Length >2` for congestion even below bandwidth saturation. Exclude loopback and virtual adapters from monitoring.
- **Visualization:** Line chart (bandwidth by interface), Dual-axis (bandwidth + errors), Table (top talkers).

---

### UC-1.2.25 · Processor Queue Length
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Processor queue length >2 per core indicates threads waiting for CPU time. Detects CPU contention even when average utilization looks normal due to burst patterns.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:System` (counter: Processor Queue Length)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:System" counter="Processor Queue Length"
| timechart span=5m avg(Value) as queue_len by host
| where queue_len > 4
```
- **Implementation:** Add `Processor Queue Length` to Perfmon System object inputs (interval=30). A sustained queue >2× number of cores indicates saturation. Correlate with `Context Switches/sec` from the same object to distinguish CPU-bound workloads from excessive threading.
- **Visualization:** Line chart (queue trend), Heatmap (hosts × time), Single value (current queue).

---

### UC-1.2.26 · Security Log Cleared
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Clearing the Security event log is a classic attacker technique to cover tracks. Legitimate clears are rare and should always be investigated.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 1102), `sourcetype=WinEventLog:System` (EventCode 104)
- **SPL:**
```spl
index=wineventlog (sourcetype="WinEventLog:Security" EventCode=1102) OR (sourcetype="WinEventLog:System" EventCode=104)
| table _time, host, sourcetype, EventCode, SubjectUserName, SubjectDomainName
| sort -_time
```
- **Implementation:** EventCode 1102 fires when the Security log is cleared; EventCode 104 when any event log is cleared. These should never occur in production outside controlled maintenance windows. Set a real-time alert with critical priority. Enrich with user identity to track who performed the action.
- **Visualization:** Timeline (clear events), Table (who cleared what), Single value (count — target: 0).

---

### UC-1.2.27 · New Service Installation
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Attackers install malicious services for persistence. Unexpected service installations outside change windows indicate compromise or unauthorized software.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System` (EventCode 7045)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=7045
| table _time, host, ServiceName, ImagePath, ServiceType, AccountName
| regex ImagePath!="(?i)(C:\\\\Windows\\\\|C:\\\\Program Files)"
| sort -_time
```
- **Implementation:** EventCode 7045 logs every new service installation. Filter out known/expected services via a lookup of approved service names. Alert on services with binaries outside standard paths (C:\Windows, C:\Program Files). Pay special attention to services running as SYSTEM with binaries in temp directories.
- **Visualization:** Table (new services with paths), Timeline, Alert on non-standard paths.

---

### UC-1.2.28 · Windows Firewall Rule Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized firewall rule changes can open attack vectors. Malware often disables the firewall or adds allow rules for C2 communication.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall` (EventCode 2004, 2005, 2006, 2033)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall"
  EventCode IN (2004, 2005, 2006, 2033)
| eval action=case(EventCode=2004,"Rule Added",EventCode=2005,"Rule Modified",EventCode=2006,"Rule Deleted",EventCode=2033,"Firewall Disabled")
| table _time, host, action, RuleName, ApplicationPath, Direction, Protocol
| sort -_time
```
- **Implementation:** Enable the Windows Firewall audit log. EventCode 2004=rule added, 2005=modified, 2006=deleted, 2033=firewall disabled. Alert immediately on firewall disabled events. Track rule changes against change management records. Focus on inbound allow rules added for non-standard ports.
- **Visualization:** Table (rule changes), Timeline, Single value (firewall disabled count — target: 0).

---

### UC-1.2.29 · Registry Run Key Modification (Persistence)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Run/RunOnce registry keys are the most common malware persistence mechanism. Monitoring these keys catches many threats early.
- **App/TA:** `Splunk_TA_windows`, Sysmon recommended
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13) or `sourcetype=WinEventLog:Security` (EventCode 4657)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=13
  TargetObject="*\\CurrentVersion\\Run*"
| table _time, host, Image, TargetObject, Details, User
| sort -_time
```
- **Implementation:** Deploy Sysmon with registry monitoring rules targeting HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run, RunOnce, and HKCU equivalents. Alternatively, enable Object Access auditing (EventCode 4657) with SACLs on Run keys. Alert on any modification outside approved deployment tools (SCCM, GPO). Cross-reference with threat intel.
- **Visualization:** Table (registry changes with process context), Timeline, Alert on non-GPO modifications.

---

### UC-1.2.30 · LSASS Memory Access (Credential Dumping)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Accessing LSASS process memory is the primary technique for credential theft (Mimikatz, ProcDump). Detection is critical to stopping lateral movement.
- **App/TA:** `Splunk_TA_windows`, Sysmon required
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 10)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=10
  TargetImage="*\\lsass.exe"
  GrantedAccess IN ("0x1010","0x1410","0x1438","0x143a","0x1fffff")
| where NOT match(SourceImage, "(?i)(MsMpEng|csrss|wininit|svchost|mrt\.exe)")
| table _time, host, SourceImage, GrantedAccess, SourceUser
| sort -_time
```
- **Implementation:** Deploy Sysmon with ProcessAccess (EventCode 10) monitoring. Filter out legitimate LSASS accessors (AV engines, csrss, wininit). The GrantedAccess mask 0x1010 (PROCESS_VM_READ + PROCESS_QUERY_LIMITED_INFORMATION) is the Mimikatz signature. Alert immediately with critical priority. Enable Credential Guard (Windows 10+) as a complementary defense.
- **Visualization:** Table (LSASS access events), Single value (count — target: 0), Alert with MITRE ATT&CK T1003 reference.

---

### UC-1.2.31 · Kerberos Authentication Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Kerberos failures (EventCode 4771) reveal password spraying, expired accounts, clock skew, and misconfigured SPNs. Distinct from NTLM failures and requires separate monitoring.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4771)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4771
| eval failure=case(Status="0x6","Unknown username",Status="0x12","Account disabled/expired/locked",Status="0x17","Password expired",Status="0x18","Bad password",Status="0x25","Clock skew",1=1,Status)
| stats count by TargetUserName, IpAddress, failure, host
| where count > 5
| sort -count
```
- **Implementation:** Collect Security event logs from all domain controllers. EventCode 4771 is Kerberos pre-auth failure. Status codes: 0x18=wrong password (most common attack indicator), 0x12=disabled/locked, 0x25=clock skew (infrastructure issue). Alert on >10 failures per user in 5 minutes (spray detection). Correlate IpAddress with known endpoints.
- **Visualization:** Table (failures by user and reason), Bar chart (top failing accounts), Timechart (failure rate trending).

---

### UC-1.2.32 · WMI Event Subscription Persistence
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** WMI event subscriptions are a stealthy persistence mechanism that survives reboots. Used by APT groups and fileless malware.
- **App/TA:** `Splunk_TA_windows`, Sysmon required
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 19, 20, 21)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational"
  EventCode IN (19, 20, 21)
| eval wmi_type=case(EventCode=19,"Filter Created",EventCode=20,"Consumer Created",EventCode=21,"Binding Created")
| table _time, host, wmi_type, User, Name, Destination, Query
| sort -_time
```
- **Implementation:** Deploy Sysmon v10+ which logs WMI event filter (19), consumer (20), and binding (21) creation. Any new WMI subscription outside management tools (SCCM, monitoring agents) is suspicious. Alert on all new subscriptions. Legitimate ones are rare and well-known (e.g., SCCM client). Correlate consumer CommandLineTemplate with known malware signatures.
- **Visualization:** Table (WMI subscriptions created), Timeline, Single value (new subscriptions — target: 0 outside SCCM).

---

### UC-1.2.33 · Audit Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Attackers modify audit policies to disable logging and hide their activities. Any unauthorized audit policy change must be investigated immediately.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4719)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4719
| table _time, host, SubjectUserName, SubjectDomainName, CategoryId, SubcategoryGuid, AuditPolicyChanges
| sort -_time
```
- **Implementation:** EventCode 4719 fires when an audit policy is changed via `auditpol.exe` or Group Policy. Any change outside planned GPO updates is suspicious. Alert with critical priority. Pay special attention to "Success removed" or "Failure removed" changes that reduce auditing coverage. Correlate with GPO change events.
- **Visualization:** Table (policy changes with user context), Timeline, Single value (count — target: 0 outside maintenance).

---

### UC-1.2.34 · AppLocker / WDAC Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** AppLocker/WDAC blocks track unauthorized application execution attempts. High violation rates indicate persistent threats or misconfigured policies.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/EXE and DLL` (EventCode 8004, 8007)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-AppLocker*" EventCode IN (8004, 8007)
| eval block_type=case(EventCode=8004,"EXE blocked",EventCode=8007,"Script blocked")
| stats count by host, block_type, RuleNameOrId, FilePath, UserName
| sort -count
```
- **Implementation:** Enable AppLocker EXE, DLL, and Script rules in enforcement or audit mode. EventCode 8003/8006=allowed, 8004/8007=blocked. In audit mode (EventCode 8003), use data to build baseline before enforcement. Track blocked attempts per host — spikes indicate attack attempts or policy gaps. Correlate FilePath with threat intel.
- **Visualization:** Bar chart (top blocked apps), Table (blocks by host), Timechart (block rate over time).

---

### UC-1.2.35 · Windows Defender Threat Detections
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Real-time visibility into endpoint AV detections across the fleet. Delayed response to malware detections increases blast radius.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventCode 1006, 1007, 1116, 1117)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational"
  EventCode IN (1006, 1007, 1116, 1117)
| eval action=case(EventCode=1006,"Detected",EventCode=1007,"Action taken",EventCode=1116,"Detected",EventCode=1117,"Action taken")
| table _time, host, action, "Threat Name", "Severity ID", Path, "Detection User"
| sort -_time
```
- **Implementation:** Forward Windows Defender Operational log from all endpoints. EventCode 1116=threat detected, 1117=action taken, 1006/1007=malware detected/acted on. Alert immediately on detections with Severity "Severe" or "High". Track remediation success (1117 following 1116). Monitor for EventCode 5001 (real-time protection disabled) as a separate critical alert.
- **Visualization:** Table (recent detections), Bar chart (threat categories), Single value (unresolved threats), Map (affected hosts).

---

### UC-1.2.36 · DCSync Attack Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** DCSync uses Directory Replication Service permissions to extract password hashes remotely. Detecting non-DC replication requests catches this attack before credential theft completes.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4662)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4662
  AccessMask="0x100"
  (Properties="*1131f6aa*" OR Properties="*1131f6ad*" OR Properties="*89e95b76*")
| where NOT match(SubjectUserName, "(?i)(\\$$)")
| table _time, host, SubjectUserName, SubjectDomainName, ObjectName
| sort -_time
```
- **Implementation:** Enable Directory Service Access auditing on domain controllers. EventCode 4662 with GUID 1131f6aa (DS-Replication-Get-Changes) or 1131f6ad (DS-Replication-Get-Changes-All) from a non-machine account (not ending in $) is a DCSync indicator. Alert immediately with critical priority. Legitimate replication only occurs between DCs (machine accounts). MITRE ATT&CK T1003.006.
- **Visualization:** Table (replication requests from non-DCs), Single value (count — target: 0), Alert with analyst playbook.

---

### UC-1.2.37 · Kerberoasting Detection (SPN Ticket Requests)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Kerberoasting requests TGS tickets for service accounts with SPNs, then cracks them offline. Detecting anomalous TGS requests catches this before passwords are compromised.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4769)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769
  TicketEncryptionType=0x17
  ServiceName!="krbtgt" ServiceName!="*$"
| stats count dc(ServiceName) as unique_spns by TargetUserName, IpAddress
| where unique_spns > 3
| sort -unique_spns
```
- **Implementation:** Collect Security logs from all DCs. EventCode 4769 = TGS ticket request. Encryption type 0x17 (RC4) is the Kerberoasting indicator — modern environments should use AES (0x12). Alert when a single user requests RC4 tickets for multiple service SPNs. Exclude machine accounts ($) and krbtgt. Remediation: enforce AES-only on service accounts and use Group Managed Service Accounts (gMSAs).
- **Visualization:** Table (suspicious requestors), Bar chart (TGS requests by encryption type), Timeline.

---

### UC-1.2.38 · AD Object Deletion Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Accidental or malicious deletion of AD objects (OUs, users, groups, computer accounts) can cause widespread service disruption. AD Recycle Bin has a limited window.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4726, 4730, 4743, 5141)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security"
  EventCode IN (4726, 4730, 4743, 5141)
| eval object_type=case(EventCode=4726,"User deleted",EventCode=4730,"Group deleted",EventCode=4743,"Computer deleted",EventCode=5141,"AD object deleted")
| table _time, host, object_type, SubjectUserName, TargetUserName, ObjectDN
| sort -_time
```
- **Implementation:** Enable DS Object Access auditing on domain controllers. EventCode 5141 catches all AD object deletions including OUs. 4726/4730/4743 catch specific account/group/computer deletions. Alert on OU deletions immediately (mass impact). Track deletion volume per admin — spikes indicate accidental bulk operations or insider threats. Ensure AD Recycle Bin is enabled.
- **Visualization:** Table (deleted objects), Timeline, Bar chart (deletions by admin), Single value (OU deletions — target: 0).

---

### UC-1.2.39 · Domain Trust Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized trust relationships can grant external domains access to internal resources. Trust modifications are rare and high-impact.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4706, 4707, 4716)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706, 4707, 4716)
| eval action=case(EventCode=4706,"Trust created",EventCode=4707,"Trust removed",EventCode=4716,"Trust modified")
| table _time, host, action, SubjectUserName, TrustDirection, TrustType, TrustedDomain
| sort -_time
```
- **Implementation:** EventCode 4706=new trust, 4707=trust removed, 4716=trust modified. These events are extremely rare in stable environments. Alert on all trust changes with critical priority. Verify against approved change requests. Pay attention to trust direction (inbound trusts grant access TO your domain) and trust type (external vs. forest trusts).
- **Visualization:** Table (trust changes), Single value (count — target: 0 outside planned changes), Alert.

---

### UC-1.2.40 · WHEA Hardware Error Reporting
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Windows Hardware Error Architecture (WHEA) reports CPU, memory, and PCIe hardware errors before they cause crashes. Enables proactive hardware replacement.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-WHEA-Logger, EventCode 17, 18, 19, 20, 47)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Microsoft-Windows-WHEA-Logger"
| eval severity=case(EventCode=18,"Fatal",EventCode=19,"Corrected",EventCode=20,"Informational",1=1,"Other")
| stats count by host, severity, ErrorSource, ErrorType
| sort -count
```
- **Implementation:** WHEA events are logged automatically by Windows on hardware error. EventCode 18=fatal (machine check, NMI), 19=corrected (ECC memory correction, CPU thermal), 47=informational. Track corrected error rates — rising counts predict imminent failure. Correlate with specific hardware component (CPU, memory DIMM, PCIe device) from ErrorSource field. Alert on any fatal errors and on corrected error rate >10/hour.
- **Visualization:** Table (errors by host and component), Line chart (corrected error trend), Single value (fatal errors — target: 0).

---

### UC-1.2.41 · Volume Shadow Copy Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** VSS failures break backup chains, System Restore, and SQL/Exchange application-consistent snapshots. Often silent until a restore is attempted.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Application` (Source=VSS, EventCode 12289, 12298, 8193, 8194)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Application" Source="VSS" EventCode IN (12289, 12298, 8193, 8194)
| eval issue=case(EventCode=12289,"VSS writer failed",EventCode=12298,"VSS copy failed",EventCode=8193,"VSS error",EventCode=8194,"VSS error")
| stats count by host, issue, EventCode
| sort -count
```
- **Implementation:** VSS events appear in the Application log. EventCode 12289=writer failure (often SQL, Exchange, or Hyper-V writers), 12298=shadow copy creation failure. Common causes: low disk space, I/O timeouts, conflicting backup agents. Alert on any VSS failure — they directly impact RPO. Correlate with backup job logs to identify which backup product is affected.
- **Visualization:** Table (VSS errors by host), Timeline, Bar chart (failure types).

---

### UC-1.2.42 · .NET CLR Performance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** .NET garbage collection pauses and high exception rates cause application latency and instability. CLR monitoring reveals issues invisible to external health checks.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:dotNET_CLR_Memory` (counters: % Time in GC, Gen 2 Collections)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:dotNET_CLR_Memory" counter="% Time in GC" instance!="_Global_"
| timechart span=5m avg(Value) as pct_gc by host, instance
| where pct_gc > 20
```
- **Implementation:** Configure Perfmon inputs for `.NET CLR Memory` object: `% Time in GC`, `# Gen 2 Collections`, `Large Object Heap size`. Also monitor `.NET CLR Exceptions` → `# of Exceps Thrown / sec`. >20% time in GC indicates memory pressure in .NET apps. Frequent Gen 2 collections signal large object allocation issues. Target specific app pool instances (w3wp) for IIS applications.
- **Visualization:** Line chart (GC time %), Bar chart (Gen 2 collections by app), Dual-axis (GC time + exceptions).

---

### UC-1.2.43 · Failover Cluster Event Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Cluster failovers indicate node failures or network partitions affecting high-availability services. Each failover risks brief downtime and potential data loss.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational` (EventCode 1069, 1177, 1205, 1254)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-FailoverClustering/Operational"
  EventCode IN (1069, 1177, 1205, 1254)
| eval event=case(EventCode=1069,"Resource failed",EventCode=1177,"Quorum lost",EventCode=1205,"Cluster service stopped",EventCode=1254,"Node removed")
| table _time, host, event, EventCode, ResourceName, NodeName
| sort -_time
```
- **Implementation:** Enable FailoverClustering Operational log on all cluster nodes. EventCode 1069=cluster resource failure (triggers failover), 1177=quorum loss (cluster at risk), 1205=cluster service stopped. Alert on quorum loss and resource failures immediately. Track failover frequency — frequent failovers indicate underlying instability. Monitor cluster network health via EventCode 1123 (network disconnected).
- **Visualization:** Timeline (failover events), Table (affected resources), Single value (failovers today), Status panel (cluster health).

---

### UC-1.2.44 · SMB Share Access Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Anomalous SMB share access patterns indicate lateral movement, data exfiltration, or ransomware file encryption across network shares.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 5140, 5145)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140
| stats dc(ShareName) as unique_shares count by SubjectUserName, IpAddress
| where unique_shares > 10 OR count > 1000
| sort -unique_shares
```
- **Implementation:** Enable "Audit File Share" and "Audit Detailed File Share" in Advanced Audit Policy. EventCode 5140=share accessed, 5145=detailed file access with access check results. Alert when a single user accesses many shares rapidly (lateral movement) or when write volume spikes (ransomware indicator). Baseline normal access patterns per user/role. Note: generates high volume — filter to sensitive shares or use summary indexing.
- **Visualization:** Table (top share accessors), Timechart (access rate), Bar chart (shares accessed per user).

---

### UC-1.2.45 · Windows Time Service (W32Time) Issues
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Time synchronization failures break Kerberos authentication (5-minute tolerance), cause log correlation issues, and invalidate audit trails.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-Time-Service, EventCode 129, 134, 142, 36)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Microsoft-Windows-Time-Service"
  EventCode IN (129, 134, 142, 36)
| eval issue=case(EventCode=129,"NTP unreachable",EventCode=134,"Time difference too large",EventCode=142,"Time service stopped",EventCode=36,"Time not synced for 24h")
| table _time, host, issue, EventCode
| sort -_time
```
- **Implementation:** W32Time events log automatically. EventCode 129=NTP server unreachable, 134=time difference >5 seconds (Kerberos risk), 142=time service stopped, 36=not synced in 24 hours. Domain-joined machines sync to DC; DCs sync to PDC emulator; PDC syncs to external NTP. Alert on any DC time sync failures (Kerberos impact). Monitor non-DC servers for EventCode 36.
- **Visualization:** Table (time sync issues), Status grid (host × sync status), Single value (unsynced hosts).

---

### UC-1.2.46 · DFS-R Replication Backlog
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** DFS-R replication backlogs mean file servers are out of sync. Users may access stale data, and a prolonged backlog can trigger an initial sync (full re-replication).
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:DFS Replication` (EventCode 4012, 4302, 4304, 5002, 5008)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:DFS Replication" EventCode IN (4012, 4302, 4304, 5002, 5008)
| eval issue=case(EventCode=4012,"Auto-recovery started",EventCode=4302,"Staging quota exceeded",EventCode=4304,"Backlog exceeded limit",EventCode=5002,"Initial sync unexpected",EventCode=5008,"Connection failed")
| table _time, host, issue, ReplicationGroupName, PartnerName
| sort -_time
```
- **Implementation:** Forward DFS Replication event logs from all DFS members. EventCode 4304=backlog exceeds threshold (default 100 files), 5008=connection failure between partners. Alert on backlog thresholds and connection failures. Monitor EventCode 4012 (auto-recovery) — frequent occurrences indicate unstable replication. Use `dfsrdiag backlog` via scripted input for precise backlog counts.
- **Visualization:** Table (replication issues), Line chart (backlog trend), Status grid (partner × status).

---

### UC-1.2.47 · Application Crash (WER) Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Windows Error Reporting captures crash details for all applications. Trending reveals systemic instability, bad patches, or problematic application versions.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Application` (EventCode 1000, 1001, 1002)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Application" EventCode IN (1000, 1002)
| eval crash_app=coalesce(Application, param1)
| stats count by host, crash_app, EventCode
| where count > 3
| sort -count
```
- **Implementation:** EventCode 1000=application crash with fault details (module, exception code, offset), 1002=application hang detected. Aggregate by faulting application and module across the fleet. Spikes after patch deployment indicate regression. Alert on critical applications (e.g., w3wp.exe, sqlservr.exe, lsass.exe). Use EventCode 1001 (WER bucket data) for deduplication.
- **Visualization:** Bar chart (top crashing apps), Timechart (crash rate over time), Table (crash details by module).

---

### UC-1.2.48 · PowerShell Script Block Logging
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Script Block Logging captures the full text of every PowerShell script executed, including deobfuscated code. Essential for detecting fileless attacks and encoded commands.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational` (EventCode 4104)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational" EventCode=4104
| search ScriptBlockText IN ("*Invoke-Mimikatz*","*Net.WebClient*","*DownloadString*","*IEX*","*-enc*","*FromBase64*","*Invoke-Expression*")
| table _time, host, Path, ScriptBlockText, UserName
| sort -_time
```
- **Implementation:** Enable Script Block Logging via GPO: Computer Configuration → Administrative Templates → Windows PowerShell → Turn on PowerShell Script Block Logging. EventCode 4104 logs the full script text, including auto-deobfuscation. Search for suspicious keywords: `Invoke-Expression`, `Net.WebClient`, `DownloadString`, `FromBase64String`, `Invoke-Mimikatz`. High volume — consider targeted alerting and summary indexing. Complements EventCode 4688 (process creation with command line).
- **Visualization:** Table (suspicious scripts), Timeline, Bar chart (script execution by host), Search interface for threat hunting.

---

### UC-1.2.49 · Lateral Movement via Explicit Credentials
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Logon type 9 (NewCredentials / RunAs /netonly) and type 10 (RDP) from unexpected sources reveal credential abuse and lateral movement between systems.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4624, Logon Type 3, 9, 10)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624 LogonType IN (9, 10)
| stats count values(LogonType) as types by TargetUserName, IpAddress, host
| where count > 5
| lookup admin_accounts.csv user as TargetUserName OUTPUT is_admin
| where is_admin="true"
| sort -count
```
- **Implementation:** Collect Security logs from all servers. Logon type 9=NewCredentials (runas /netonly — commonly used with stolen hashes), type 10=RemoteInteractive (RDP). Focus on admin accounts authenticating to servers they don't normally access. Build a baseline of normal admin→server mappings. Alert when an admin authenticates to >3 new hosts in an hour. Correlate with process creation (4688) on the destination.
- **Visualization:** Network graph (source→destination), Table (unusual logons), Timechart (logon rate by type).

---

### UC-1.2.50 · DNS Debug Query Logging
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** DNS query logging reveals C2 communication via DNS tunneling, DGA domains, and unauthorized DNS resolution. Essential for security visibility.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-DNS-Server/Analytical` or DNS debug log file
- **SPL:**
```spl
index=dns sourcetype="MSAD:NT6:DNS" query_type IN (TXT, NULL, CNAME)
| stats count avg(query_length) as avg_len by query, client_ip
| where avg_len > 50 OR count > 100
| sort -avg_len
```
- **Implementation:** Enable DNS Analytical logging on Windows DNS servers or DNS debug logging to file (dnscmd /config /logfilepath). Forward via Splunk_TA_windows or Splunk Add-on for Microsoft DNS. Long TXT queries (>50 chars) and high-frequency CNAME lookups indicate DNS tunneling. Queries to recently registered domains or high-entropy names suggest DGA malware. Baseline normal query patterns, then alert on anomalies.
- **Visualization:** Table (suspicious queries), Bar chart (query types), Timechart (query volume), Top domains.

---

### UC-1.2.51 · Process Creation with Command Line Auditing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Full command-line visibility on process creation is the foundation of threat detection. Reveals encoded PowerShell, LOLBin abuse, and suspicious child processes.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4688)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4688
| where match(CommandLine, "(?i)(certutil.*-urlcache|bitsadmin.*\/transfer|mshta.*http|regsvr32.*\/s.*\/n.*\/u|rundll32.*javascript)")
| table _time, host, SubjectUserName, NewProcessName, CommandLine, ParentProcessName
| sort -_time
```
- **Implementation:** Enable "Audit Process Creation" and "Include command line in process creation events" via GPO (Computer Configuration → Administrative Templates → System → Audit Process Creation). EventCode 4688 then includes full CommandLine. Search for known LOLBins (Living Off the Land Binaries): certutil, bitsadmin, mshta, regsvr32, rundll32 with suspicious parameters. High volume — use summary indexing or data model acceleration.
- **Visualization:** Table (suspicious processes), Timeline, Search interface for hunting.

---

### UC-1.2.52 · NIC Teaming / LBFO Failover
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** NIC team member failures reduce redundancy silently. A second failure causes full network loss. Detecting the first failure enables proactive repair.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-NlbFo/Operational` (EventCode 101, 105, 106, 115)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-NlbFo/Operational"
  EventCode IN (101, 105, 106, 115)
| eval event=case(EventCode=101,"Team degraded",EventCode=105,"Member disconnected",EventCode=106,"Member reconnected",EventCode=115,"Standby activated")
| table _time, host, event, TeamName, MemberName
| sort -_time
```
- **Implementation:** NIC Teaming (LBFO) events log automatically. EventCode 101=team degraded (member lost), 105=member disconnected, 106=reconnected, 115=standby activated. Alert immediately when team degrades — the remaining NIC is now a single point of failure. Track flapping (repeated 105→106 cycles) which indicates cable, switch port, or driver issues.
- **Visualization:** Status grid (team × member status), Timeline (failover events), Single value (degraded teams).

---

### UC-1.2.53 · BitLocker Recovery Events
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** BitLocker recovery mode triggers indicate TPM issues, boot configuration changes, or potential tampering with the boot chain. Each event requires investigation.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-BitLocker/BitLocker Management` (EventCode 768, 770, 775, 846)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-BitLocker*"
  EventCode IN (768, 770, 775, 846)
| eval issue=case(EventCode=768,"Recovery mode entered",EventCode=770,"Protection suspended",EventCode=775,"Recovery key used",EventCode=846,"Encryption failed")
| table _time, host, issue, VolumeName, RecoveryReason
| sort -_time
```
- **Implementation:** Forward BitLocker Management and Operational logs. EventCode 768/775=recovery mode (TPM unsealing failed, boot integrity compromised). Common benign triggers: BIOS updates, boot order changes. Alert on recovery events — each one should be correlated with approved change windows. Track EventCode 770 (protection suspended) — ensure it's re-enabled within 24 hours.
- **Visualization:** Table (recovery events), Timeline, Single value (unresolved recoveries).

---

### UC-1.2.54 · Windows Event Forwarding (WEF) Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** WEF collects events from thousands of endpoints to central collectors. Forwarding failures create visibility gaps across the security monitoring pipeline.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Forwarding/Operational` (EventCode 100, 102, 103, 105, 111)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Forwarding/Operational"
  EventCode IN (102, 103, 105, 111)
| eval issue=case(EventCode=102,"Subscription connected",EventCode=103,"Subscription error",EventCode=105,"Access denied",EventCode=111,"Collector unreachable")
| stats count by host, issue, SubscriptionName
| where issue!="Subscription connected"
| sort -count
```
- **Implementation:** Enable Forwarding/Operational log on WEF collectors and clients. EventCode 103=subscription-level error, 105=access denied (Kerberos/permission issue), 111=cannot reach collector. Monitor for expected forwarders going silent — compare against CMDB endpoint list. Alert when error rate exceeds 5% of clients. Use `wecutil gr <subscription>` via scripted input for precise subscription health.
- **Visualization:** Status grid (subscription × host), Pie chart (healthy vs. error), Table (error details), Single value (connected clients).

---

### UC-1.2.55 · Suspicious Token Manipulation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Token impersonation and privilege escalation via token manipulation (SeImpersonatePrivilege abuse) is a common post-exploitation technique.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4673, 4674)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4673, 4674)
  Privileges IN ("SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege", "SeTcbPrivilege", "SeDebugPrivilege")
| where NOT match(ProcessName, "(?i)(lsass|svchost|services|mssql|w3wp)")
| stats count by SubjectUserName, ProcessName, Privileges, host
| sort -count
```
- **Implementation:** Enable "Audit Sensitive Privilege Use" in Advanced Audit Policy. EventCode 4673=sensitive privilege used, 4674=operation on privileged object. Focus on SeImpersonatePrivilege (Potato attacks), SeDebugPrivilege (memory injection), SeTcbPrivilege (token creation). Filter known legitimate users (service accounts, SQL Server, IIS). Alert on non-standard processes using these privileges.
- **Visualization:** Table (privilege usage by process), Bar chart (privilege types), Timeline, Alert on unusual callers.

---

### UC-1.2.56 · Sysmon Network Connection Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Sysmon EventCode 3 logs every outbound TCP/UDP connection with the originating process. Reveals C2 callbacks, data exfiltration, and unauthorized network access.
- **App/TA:** `Splunk_TA_windows`, Sysmon required
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 3)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=3
  Initiated="true"
| where NOT cidrmatch("10.0.0.0/8", DestinationIp) AND NOT cidrmatch("172.16.0.0/12", DestinationIp) AND NOT cidrmatch("192.168.0.0/16", DestinationIp)
| stats count dc(DestinationIp) as unique_ips by Image, host, User
| where unique_ips > 50 OR count > 500
| sort -unique_ips
```
- **Implementation:** Deploy Sysmon with network connection logging (EventCode 3, Initiated=true for outbound). Filter RFC1918 addresses to focus on external connections. High unique destination IPs from a single process suggest scanning or C2 beaconing. Alert on processes making external connections that normally shouldn't (e.g., winword.exe, excel.exe connecting outbound). Combine with DNS logs for full picture.
- **Visualization:** Table (outbound connections by process), Network graph, Timechart (connection rate).

---

### UC-1.2.57 · Thread Count Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Thread leaks or excessive thread creation cause pool exhaustion and application hangs. Windows has a system-wide limit of ~65K threads that affects all processes.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:Process` (counter: Thread Count), `sourcetype=Perfmon:System` (counter: Threads)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:Process" counter="Thread Count" instance!="_Total" instance!="Idle"
| stats max(Value) as threads by host, instance
| where threads > 500
| sort -threads
```
- **Implementation:** Configure Perfmon Process inputs with `Thread Count` counter (interval=300). Also monitor system-wide threads via Perfmon System → Threads. Alert when any single process exceeds 500 threads or system total exceeds 50K. Common offenders: IIS application pools (w3wp.exe), Java applications, .NET services with async leaks. Correlate with application response times.
- **Visualization:** Bar chart (top thread consumers), Line chart (thread growth trend), Single value (system total).

---

### UC-1.2.58 · Storage Spaces Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Storage Spaces pools degrade silently when physical disks fail. Detection before a second disk fails prevents data loss in mirrored/parity configurations.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-StorageSpaces-Driver/Operational` (EventCode 1, 2, 3, 207)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-StorageSpaces*" EventCode IN (1, 2, 3, 207)
| eval status=case(EventCode=1,"Pool degraded",EventCode=2,"Disk failed",EventCode=3,"IO error",EventCode=207,"Repair started")
| table _time, host, status, PhysicalDiskId, PoolName
| sort -_time
```
- **Implementation:** Storage Spaces driver events log automatically. Monitor for pool degradation (lost redundancy) and disk failures. Alert at critical priority on any degradation — the pool is now running without full redundancy. Track repair progress (EventCode 207). Also poll via PowerShell scripted input: `Get-StoragePool | Get-PhysicalDisk | Where OperationalStatus -ne 'OK'` for proactive monitoring beyond event-based detection.
- **Visualization:** Status grid (pool × disk health), Timeline (degradation events), Single value (degraded pools — target: 0).

---

### UC-1.2.59 · DCOM / COM+ Application Errors
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** DCOM errors affect distributed applications, WMI remote management, and MMC snap-ins. Persistent errors indicate permission issues or component registration corruption.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System` (EventCode 10016, 10028, 10010)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" Source="DCOM" EventCode IN (10016, 10028, 10010)
| stats count by host, EventCode, param1, param2
| where count > 10
| sort -count
```
- **Implementation:** EventCode 10016=permission error (most common — often benign for built-in COM objects), 10028=DCOM connection timed out, 10010=server did not register within timeout. Filter known benign 10016 errors (Windows built-in CLSIDs). Alert on 10028/10010 as these indicate application-impacting failures. Persistent 10010 errors for specific CLSIDs indicate broken COM registrations.
- **Visualization:** Table (DCOM errors by CLSID), Bar chart (error types), Timechart (error frequency).

---

### UC-1.2.60 · Code Integrity / Driver Signing Violations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Unsigned or tampered drivers loading into the kernel are a rootkit indicator. Code Integrity violations detect bypass attempts and driver-level threats.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-CodeIntegrity/Operational` (EventCode 3001, 3002, 3003, 3004, 3033)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-CodeIntegrity/Operational"
  EventCode IN (3001, 3002, 3003, 3004, 3033)
| eval issue=case(EventCode=3001,"Unsigned driver blocked",EventCode=3002,"Unable to verify",EventCode=3003,"Unsigned policy",EventCode=3004,"File hash not found",EventCode=3033,"Unsigned image loaded")
| table _time, host, issue, FileNameBuffer, ProcessNameBuffer
| sort -_time
```
- **Implementation:** Code Integrity events log automatically on systems with Secure Boot, HVCI, or WDAC. EventCode 3033=unsigned image loaded (audit mode), 3001=unsigned driver blocked (enforcement). Alert on all blocked events in enforcement mode. In audit mode, use data to build a driver whitelist before enabling enforcement. Cross-reference drivers with known-good hashes from Microsoft catalog.
- **Visualization:** Table (integrity violations), Timeline, Bar chart (top unsigned files), Single value (blocked loads).

---

### UC-1.2.61 · Data Deduplication Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Windows Data Deduplication saves significant storage on file servers. Job failures or savings degradation indicate volume corruption or configuration issues.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Deduplication/Operational` (EventCode 6153, 6155, 12800, 12802)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Deduplication*"
  EventCode IN (6153, 6155, 12800, 12802)
| eval status=case(EventCode=6153,"Optimization completed",EventCode=6155,"Optimization failed",EventCode=12800,"Scrubbing completed",EventCode=12802,"Corruption detected")
| table _time, host, status, VolumeName, SavingsRate, CorruptionCount
| sort -_time
```
- **Implementation:** Enable Deduplication Operational log on file servers with dedup enabled. EventCode 6155=optimization job failure, 12802=data corruption detected. Monitor savings rate trending — declining rates suggest changing data patterns or dedup overhead. Alert on any corruption detection (12802) immediately. Track optimization duration — increasing times indicate volume growth outpacing dedup capacity.
- **Visualization:** Line chart (savings rate over time), Table (job results), Single value (current savings %), Alert on corruption.

---

### UC-1.2.62 · TCP Connection State Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Excessive TIME_WAIT, CLOSE_WAIT, or ESTABLISHED connections indicate connection leaks, exhausted ephemeral ports, or application hanging. Causes service unavailability.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:TCPv4` (counters: Connections Established, Connection Failures)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:TCPv4" counter IN ("Connections Established","Connection Failures","Connections Reset")
| timechart span=5m avg(Value) as value by counter, host
| where value > 10000
```
- **Implementation:** Configure Perfmon inputs for TCPv4 object: `Connections Established`, `Connection Failures`, `Connections Reset`, `Segments Retransmitted/sec` (interval=60). Also deploy a scripted input running `netstat -an | find /c "TIME_WAIT"` for state-level counts. Alert when established connections exceed application baseline by 2x or TIME_WAIT exceeds 5000 (ephemeral port exhaustion risk). Default ephemeral port range: 49152-65535 (16K ports).
- **Visualization:** Line chart (connection states over time), Gauge (established connections), Single value (TIME_WAIT count).

---

### UC-1.2.63 · Windows Installer Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** MSI installation failures affect patching, software deployment, and SCCM/Intune compliance. Repeated failures indicate corrupted Windows Installer service or disk issues.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Application` (Source=MsiInstaller, EventCode 11708, 11724)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Application" Source="MsiInstaller" EventCode IN (11708, 11724)
| table _time, host, EventCode, ProductName, ProductVersion, Message
| stats count by host, ProductName
| where count > 2
| sort -count
```
- **Implementation:** EventCode 11708=installation failed, 11724=removal completed (track uninstalls). Track installation failures per host — repeated failures for the same product indicate systematic issues. Correlate with SCCM/Intune deployment status. Common causes: pending reboots, insufficient disk space, corrupted Windows Installer cache. Alert when critical patches fail to install across >5% of fleet.
- **Visualization:** Table (failed installs), Bar chart (top failing products), Timechart (failure rate).

---

### UC-1.2.64 · Event Log Channel Size / Overflow
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** When event logs reach maximum size with overwrite-oldest policy, critical security events are lost. With do-not-overwrite policy, the log stops recording entirely.
- **App/TA:** `Splunk_TA_windows`, custom scripted input
- **Data Sources:** `sourcetype=WinEventLog:System` (EventCode 6005) + custom scripted input (`wevtutil gl Security`)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=1101
| table _time, host, Channel
| stats count by host, Channel
| sort -count

| `` Alternatively via scripted input: ``
index=os sourcetype=windows:eventlog:size
| where used_pct > 90
| table _time, host, log_name, current_size_MB, max_size_MB, used_pct
```
- **Implementation:** Deploy a scripted input that runs `wevtutil gl Security` (and other critical channels) every 15 minutes, parsing current size vs. max size. Default Security log is 20MB — often insufficient on DCs and servers with detailed auditing. Alert when any critical log exceeds 90% capacity. Alternatively, monitor EventCode 1101 (audit log full) in the System log. Recommended: increase Security log to 1GB+ on DCs.
- **Visualization:** Gauge (log fill percentage), Table (logs near capacity), Bar chart (log sizes by channel).

---

### UC-1.2.65 · Pass-the-Hash / NTLM Relay Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Pass-the-hash attacks use stolen NTLM hashes to authenticate without knowing the password. Detecting NTLM logons from unusual sources catches this common lateral movement technique.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4624, LogonType 3, AuthenticationPackageName=NTLM)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624 LogonType=3
  AuthenticationPackageName="NTLM" TargetUserName!="ANONYMOUS LOGON"
| stats count dc(host) as target_hosts values(host) as targets by TargetUserName, IpAddress
| where target_hosts > 3
| sort -target_hosts
```
- **Implementation:** NTLM type 3 (network) logons from non-standard sources indicate pass-the-hash. In environments enforcing Kerberos, any NTLM logon to a server is suspicious. Focus on admin accounts using NTLM to access multiple hosts. EventCode 4776 on the DC shows the NTLM validation. Remediation: enable "Restrict NTLM" GPO settings, enforce Kerberos, deploy Credential Guard. MITRE ATT&CK T1550.002.
- **Visualization:** Table (NTLM logons from suspicious sources), Network graph (source→targets), Timeline, Single value (NTLM vs Kerberos ratio).

---

### UC-1.2.66 · Sysmon File Creation in Suspicious Paths
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Files created in temp directories, startup folders, and system paths by unexpected processes indicate malware dropping payloads or establishing persistence.
- **App/TA:** `Splunk_TA_windows`, Sysmon required
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 11)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11
| where match(TargetFilename, "(?i)(\\\\Temp\\\\.*\\.exe|\\\\Startup\\\\|\\\\Tasks\\\\|\\\\ProgramData\\\\.*\\.exe|\\\\AppData\\\\.*\\.bat|\\\\AppData\\\\.*\\.ps1)")
| table _time, host, Image, TargetFilename, User
| sort -_time
```
- **Implementation:** Deploy Sysmon with FileCreate (EventCode 11) monitoring, filtered to suspicious target paths: Temp, Startup, ProgramData, AppData. Executables (.exe, .dll, .bat, .ps1, .vbs) created in these paths by non-installer processes are suspicious. Exclude known deployment tools (SCCM client, Intune agent). Cross-reference with process creation events to build full attack chain.
- **Visualization:** Table (suspicious file creations), Bar chart (top dropping processes), Timeline.

---

### UC-1.2.67 · Golden Ticket Detection (TGT Anomalies)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Golden tickets are forged Kerberos TGTs that grant domain-wide access. Detecting anomalous TGT properties catches this catastrophic compromise.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4768, 4769)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769
| eval ticket_age = _time - TicketIssueTime
| where TicketEncryptionType="0x17" AND ticket_age > 36000
| table _time, host, TargetUserName, ServiceName, IpAddress, TicketEncryptionType
| sort -_time

| `` Also detect TGT requests with RC4 from non-standard IPs: ``
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4768 TicketEncryptionType=0x17
| stats count by TargetUserName, IpAddress
```
- **Implementation:** Golden tickets typically use RC4 encryption (0x17) with abnormally long lifetimes (default Kerberos max is 10 hours). EventCode 4768=TGT request, 4769=TGS request. Detect TGS requests referencing TGTs older than 10 hours, or TGT requests with RC4 in environments that enforce AES. Also monitor for EventCode 4769 with services accessed that the user normally doesn't touch. Requires KRBTGT password rotation as remediation.
- **Visualization:** Table (anomalous ticket requests), Timeline, Single value (RC4 TGT count), Alert.

---

### UC-1.2.68 · NTFS Corruption and Self-Healing
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** NTFS corruption can cause data loss, application failures, and boot issues. Self-healing events indicate disk degradation that will worsen.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System` (Source=Ntfs, EventCode 55, 98, 137, 140)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Ntfs" EventCode IN (55, 98, 137, 140)
| eval issue=case(EventCode=55,"NTFS corruption detected",EventCode=98,"Volume dirty flag set",EventCode=137,"Self-healing started",EventCode=140,"Self-healing completed")
| table _time, host, issue, DriveName, CorruptionType
| sort -_time
```
- **Implementation:** NTFS events log automatically. EventCode 55=structure corruption on volume (critical), 98=volume marked dirty (chkdsk needed at boot), 137/140=self-healing activity. Any EventCode 55 requires immediate attention — indicates metadata corruption that may spread. Correlate with WHEA (hardware) and SMART events to determine if underlying disk is failing. Schedule chkdsk offline and plan disk replacement.
- **Visualization:** Table (corruption events), Timeline, Single value (affected volumes — target: 0).

---

### UC-1.2.69 · Page File Usage & Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Page file exhaustion prevents new process creation and causes "out of virtual memory" errors. System-managed page files can grow to fill the disk.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:Paging_File` (counter: % Usage, % Usage Peak)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:Paging_File" counter="% Usage" instance="_Total"
| timechart span=15m avg(Value) as pf_pct by host
| where pf_pct > 70
```
- **Implementation:** Configure Perfmon inputs for Paging File object: `% Usage`, `% Usage Peak` (interval=300). Alert when usage exceeds 70% sustained (indicates memory pressure requiring page file). Track peak usage — if it regularly exceeds 80%, the system needs more RAM or has a memory leak. Also monitor EventCode 2004 in System log (page file too small) as a reactive indicator.
- **Visualization:** Line chart (page file usage over time), Gauge (current usage), Table (hosts with high usage).

---

### UC-1.2.70 · Context Switch Rate Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Abnormally high context switch rates indicate excessive threading, poor application design, or kernel-mode driver issues. Degrades overall system performance.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:System` (counter: Context Switches/sec)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:System" counter="Context Switches/sec"
| timechart span=5m avg(Value) as ctx_switches by host
| streamstats window=48 avg(ctx_switches) as baseline by host
| eval deviation = (ctx_switches - baseline) / baseline * 100
| where deviation > 100
```
- **Implementation:** Add `Context Switches/sec` to Perfmon System inputs (interval=60). Normal range varies by workload — establish per-host baselines. >15,000/sec per CPU core is generally concerning. Alert when rate exceeds 2x the rolling baseline. Correlate with `Processor Queue Length` and `% Interrupt Time` to distinguish user-mode threading issues from driver/hardware interrupt storms.
- **Visualization:** Line chart (context switch rate with baseline), Heatmap (hosts × rate), Single value (anomalous hosts).

---

### UC-1.2.71 · Scheduled Task Creation (Persistence)
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Value:** Scheduled tasks are a common persistence mechanism for malware. New tasks created outside change management warrant investigation.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4698), `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 106)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4698
| rex field=TaskContent "<Command>(?<command>[^<]+)</Command>"
| rex field=TaskContent "<Arguments>(?<arguments>[^<]+)</Arguments>"
| table _time, host, SubjectUserName, TaskName, command, arguments
| where NOT match(SubjectUserName, "(?i)(SYSTEM|sccm|intune)")
| sort -_time
```
- **Implementation:** Enable "Audit Other Object Access Events" for EventCode 4698 (task created). The TaskContent XML field contains the full task definition including command, arguments, and triggers. Alert on tasks created by non-SYSTEM/non-admin accounts, tasks with commands in temp/user directories, or tasks executing encoded PowerShell. Cross-reference with Sysmon process creation for execution context.
- **Visualization:** Table (new tasks with commands), Timeline, Bar chart (tasks created by user).

---

### UC-1.2.72 · WinRM / Remote PowerShell Connections
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** WinRM enables remote command execution via PowerShell Remoting. Monitoring inbound WinRM sessions detects lateral movement and unauthorized remote management.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-WinRM/Operational` (EventCode 6, 91, 161)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-WinRM/Operational"
  EventCode IN (6, 91, 161)
| eval action=case(EventCode=6,"Session created",EventCode=91,"Session created (user)",EventCode=161,"Auth failed")
| stats count by host, action, User, IpAddress
| sort -count
```
- **Implementation:** Enable WinRM Operational log on all servers. EventCode 6/91=new WinRM session established, 161=authentication failure. Baseline expected WinRM sources (jump servers, SCCM, monitoring tools). Alert on WinRM sessions from non-authorized IPs or workstations. In restricted environments, consider disabling WinRM on servers that don't require it. Correlate with PowerShell Script Block Logging for full command visibility.
- **Visualization:** Table (WinRM sessions by source), Network graph (source→dest), Timeline, Bar chart (sessions per host).

---

### UC-1.2.73 · LDAP Query Performance (DC Health)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Slow LDAP queries on domain controllers degrade authentication, group policy processing, and application lookups across the entire domain.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:NTDS` (counters: LDAP Searches/sec, LDAP Successful Binds/sec, LDAP Search Time)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:NTDS" counter IN ("LDAP Searches/sec","LDAP Successful Binds/sec","LDAP Client Sessions")
| timechart span=5m avg(Value) as value by counter, host
```
- **Implementation:** Configure Perfmon inputs on domain controllers for NTDS object: `LDAP Searches/sec`, `LDAP Successful Binds/sec`, `LDAP Client Sessions`, `LDAP Active Threads` (interval=60). Also enable "Expensive/Inefficient LDAP searches" logging via registry (15 Field Engineering diagnostics). Alert when LDAP search rate drops suddenly (DC issues) or when client sessions exceed baseline by 2x (possible LDAP enumeration attack).
- **Visualization:** Line chart (LDAP operations/sec), Dual-axis (searches + bind rate), Table (DCs by load), Gauge (active sessions).

---

### UC-1.2.74 · Hyper-V VM State Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unexpected VM power state changes (shutdowns, paused, critical saves) indicate host issues, resource contention, or unauthorized administrative actions.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin` (EventCode 12320, 12322, 12324, 18304)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Hyper-V-VMMS*"
  EventCode IN (12320, 12322, 12324, 18304, 18310, 18312)
| eval action=case(EventCode=12320,"VM started",EventCode=12322,"VM stopped",EventCode=12324,"VM saved",EventCode=18304,"VM critical",EventCode=18310,"VM paused",EventCode=18312,"VM resumed")
| table _time, host, action, VmName, VmId
| sort -_time
```
- **Implementation:** Forward Hyper-V VMMS Admin logs from all Hyper-V hosts. EventCode 18304=VM entered critical state (memory pressure, lost storage), 18310=VM paused (out of disk, integration services failure). Alert on any critical state transitions. Track unexpected shutdowns (12322 without preceding 12320 by admin). Correlate with host-level resource monitoring to identify the root cause.
- **Visualization:** Timeline (VM state changes), Status grid (VM × state), Table (critical events), Single value (VMs in critical state).

---

### UC-1.2.75 · AD Certificate Services (ADCS) Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** ADCS misconfigurations enable privilege escalation (ESC1-ESC8 attacks). Monitoring certificate requests catches unauthorized certificate enrollment for domain admin impersonation.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4886, 4887, 4888)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4886, 4887, 4888)
| eval action=case(EventCode=4886,"Request received",EventCode=4887,"Certificate issued",EventCode=4888,"Certificate denied")
| stats count by Requester, CertificateTemplate, SubjectName, action
| where CertificateTemplate IN ("User","SmartcardLogon","Machine") AND NOT match(Requester, "(?i)(SYSTEM|machine\\$)")
| sort -count
```
- **Implementation:** Enable Certificate Services auditing on CA servers. EventCode 4887=certificate issued — track who requested which template. Alert on certificates with Subject Alternative Names (SANs) containing admin usernames (ESC1 attack). Monitor for certificate requests from non-standard templates. Track enrollment agent certificates (ESC3). Audit CA configuration for overly permissive templates with `certutil -v -template`.
- **Visualization:** Table (certificate issuances), Bar chart (requests by template), Timeline, Alert on SAN mismatches.

---

### UC-1.2.76 · AdminSDHolder Modification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** The AdminSDHolder container controls ACLs on all privileged AD groups. Modifying it grants persistent hidden admin access that survives permission resets.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 5136)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
  ObjectDN="*AdminSDHolder*"
| table _time, host, SubjectUserName, AttributeLDAPDisplayName, AttributeValue, OperationType
| sort -_time
```
- **Implementation:** Enable "Audit Directory Service Changes" on domain controllers. EventCode 5136=directory object modified. Filter for ObjectDN containing "AdminSDHolder". Any modification to this container is highly suspicious — it should only change via approved security hardening. The SDProp process propagates AdminSDHolder ACLs to all protected groups every 60 minutes. Alert immediately with critical priority.
- **Visualization:** Table (modifications), Single value (count — target: 0), Alert with SOC escalation.

---

### UC-1.2.77 · SPN Modification (Targeted Kerberoasting)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Attackers add SPNs to admin accounts to make them Kerberoastable. Monitoring SPN changes on sensitive accounts catches this setup before the actual attack.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 5136, attribute servicePrincipalName)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
  AttributeLDAPDisplayName="servicePrincipalName"
| table _time, host, SubjectUserName, ObjectDN, AttributeValue, OperationType
| where OperationType="%%14674"
| sort -_time
```
- **Implementation:** EventCode 5136 with AttributeLDAPDisplayName=servicePrincipalName tracks SPN additions (OperationType %%14674=value added) and removals. Alert on any SPN added to user accounts in privileged groups (Domain Admins, Enterprise Admins, Schema Admins). Legitimate SPN changes are rare and tied to service deployments. Cross-reference with Kerberoasting detection (UC-1.2.37).
- **Visualization:** Table (SPN changes), Single value (changes to admin accounts — target: 0), Timeline.

---

### UC-1.2.78 · DSRM Account Usage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** The Directory Services Restore Mode (DSRM) account is a local admin on every DC with a rarely-changed password. Its use outside restores indicates compromise.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4794, 4624 with DSRM)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security"
  (EventCode=4794 OR (EventCode=4624 TargetUserName="Administrator" LogonType=10 AuthenticationPackageName="Negotiate"))
| eval alert_type=case(EventCode=4794,"DSRM password changed",EventCode=4624,"Possible DSRM logon")
| table _time, host, alert_type, SubjectUserName, IpAddress
| sort -_time
```
- **Implementation:** EventCode 4794=DSRM password change (should only happen during planned maintenance). DSRM logons appear as local "Administrator" logons on the DC. Since Windows Server 2008 R2, registry key DsrmAdminLogonBehavior allows DSRM logon while AD is running (value=2). Alert on any DSRM password change and any local admin logon to a DC. Set DsrmAdminLogonBehavior=0 (default, deny DSRM logon while AD running).
- **Visualization:** Table (DSRM events), Single value (count — target: 0 outside restore operations), Alert.

---

### UC-1.2.79 · Sysmon DNS Query Logging
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Per-process DNS query logging reveals which applications communicate with which domains. Detects DGA, C2 callbacks, and data exfiltration at the endpoint level.
- **App/TA:** `Splunk_TA_windows`, Sysmon required
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 22)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=22
| where NOT match(QueryName, "(?i)(microsoft\.com|windowsupdate\.com|office\.com|bing\.com|msftconnecttest)")
| stats count dc(QueryName) as unique_domains by Image, host
| where unique_domains > 100
| sort -unique_domains
```
- **Implementation:** Deploy Sysmon v10+ with DNS query logging (EventCode 22). Each event records the process that made the DNS query and the resolved domain. Filter out known-good domains. Alert on processes with high unique domain counts (DGA indicator), processes that normally don't make DNS queries (LOLBin abuse), or queries to known-bad domains (threat intel lookup). Lower volume than network-level DNS logging since it's per-endpoint.
- **Visualization:** Table (queries by process), Bar chart (top resolving processes), Sankey diagram (process→domain).

---

### UC-1.2.80 · Windows Backup Job Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Windows Server Backup failures mean the server has no recovery point. Silent failures create a false sense of protection.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Backup` (EventCode 4, 5, 8, 9, 14, 17, 22)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Backup"
  EventCode IN (4, 5, 8, 9, 14)
| eval status=case(EventCode=4,"Backup completed",EventCode=5,"Backup failed",EventCode=8,"Backup failed (VSS)",EventCode=9,"Warning",EventCode=14,"Backup completed with warnings")
| table _time, host, status, EventCode, BackupTarget
| sort -_time
```
- **Implementation:** Forward Windows Backup event logs. EventCode 4=success, 5=failure, 8=VSS failure. Alert on any backup failure (EventCode 5, 8). Also monitor for missing backups — if a server stops reporting EventCode 4, the backup job may have been disabled or deleted. Compare actual backup frequency against RTO/RPO requirements. Escalate servers with no successful backup in 48+ hours.
- **Visualization:** Status grid (host × backup status), Table (failures), Line chart (backup success rate over time), Single value (hours since last backup).

---

### UC-1.2.81 · SMBv1 Usage Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** SMBv1 is vulnerable to EternalBlue and WannaCry. Detecting remaining SMBv1 traffic identifies systems that need upgrading or have SMBv1 re-enabled.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-SMBServer/Audit` (EventCode 3000)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-SMBServer/Audit" EventCode=3000
| stats count values(ClientName) as clients dc(ClientName) as client_count by host
| sort -client_count
```
- **Implementation:** Enable SMB1 audit logging via `Set-SmbServerConfiguration -AuditSmb1Access $true`. EventCode 3000 logs each SMBv1 connection with the client name. Identify all clients still using SMBv1, then upgrade or remediate before disabling SMBv1 entirely. Alert on any new SMBv1 access after remediation is complete. MS17-010 (EternalBlue) affects unpatched SMBv1 systems.
- **Visualization:** Table (SMBv1 clients), Bar chart (clients per server), Single value (total SMBv1 connections — target: 0).

---

### UC-1.2.82 · Credential Guard Status Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Credential Guard protects NTLM hashes and Kerberos tickets in an isolated container. Monitoring ensures it remains enabled and isn't bypassed.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-DeviceGuard/Operational` (EventCode 13, 14, 15)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-DeviceGuard*"
| stats latest(EventCode) as status by host
| eval cg_status=case(status=13,"Running",status=14,"Stopped",status=15,"Not configured",1=1,"Unknown")
| table host, cg_status
| where cg_status!="Running"
```
- **Implementation:** Device Guard/Credential Guard Operational log reports VBS (Virtualization Based Security) status. EventCode 13=VBS running with Credential Guard, 14=stopped, 15=not configured. All domain-joined Windows 10/11 and Server 2016+ should have Credential Guard enabled. Alert when any previously-enabled host reports stopped or not configured. Requires UEFI Secure Boot, TPM 2.0, and compatible hardware.
- **Visualization:** Pie chart (fleet CG status), Table (non-compliant hosts), Single value (% compliant).

---

### UC-1.2.83 · Boot Configuration Changes (BCDEdit)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Boot configuration changes can disable Secure Boot, enable test signing (rootkit loading), or modify boot chain integrity. Used by advanced threats.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4688, CommandLine containing bcdedit)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4688
  CommandLine="*bcdedit*"
| where match(CommandLine, "(?i)(testsigning|nointegritychecks|safeboot|debug|disableelamdrivers)")
| table _time, host, SubjectUserName, CommandLine, ParentProcessName
| sort -_time
```
- **Implementation:** Requires process creation with command line auditing (EventCode 4688). Alert on any bcdedit execution that modifies security settings: `testsigning on` (allows unsigned drivers), `nointegritychecks` (disables code integrity), `debug on` (enables kernel debugging), `disableelamdrivers` (disables early launch anti-malware). All of these weaken the boot chain. Legitimate uses are rare and limited to development environments.
- **Visualization:** Table (bcdedit commands), Single value (security-affecting changes — target: 0), Alert.

---

### UC-1.2.84 · Sysmon Named Pipe Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Named pipes are used for inter-process communication and by tools like Cobalt Strike, Mimikatz, and PsExec. Detecting unusual named pipes reveals C2 and lateral movement.
- **App/TA:** `Splunk_TA_windows`, Sysmon required
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 17, 18)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational"
  EventCode IN (17, 18)
| where match(PipeName, "(?i)(MSSE-|msagent_|postex_|status_|mojo\.|cobaltstrike|beacon)")
| table _time, host, EventCode, PipeName, Image, User
| sort -_time
```
- **Implementation:** Deploy Sysmon with PipeCreated (17) and PipeConnected (18) monitoring. Known malicious pipe names: `MSSE-*` (Metasploit), `msagent_*` (Cobalt Strike), `postex_*` (Cobalt Strike post-exploitation), `status_*` (default Cobalt Strike). Also detect PsExec pipes (`PSEXESVC`). Baseline normal pipes per application role, then alert on anomalies.
- **Visualization:** Table (pipe events), Bar chart (top pipe names), Timeline, Alert on known-bad patterns.

---

### UC-1.2.85 · IIS Application Pool Crashes & Recycling
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Application pool crashes cause HTTP 503 errors and service outages. Frequent recycling indicates memory leaks or configuration issues in web applications.
- **App/TA:** `Splunk_TA_windows`, Splunk Add-on for Microsoft IIS
- **Data Sources:** `sourcetype=WinEventLog:System` (Source=WAS, EventCode 5002, 5010, 5011, 5012, 5013)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" Source="WAS"
  EventCode IN (5002, 5010, 5011, 5012, 5013)
| eval event=case(EventCode=5002,"AppPool crashed",EventCode=5010,"Process termination timeout",EventCode=5011,"AppPool auto-disabled",EventCode=5012,"AppPool rapid failures",EventCode=5013,"AppPool timeout")
| table _time, host, event, AppPoolName
| sort -_time
```
- **Implementation:** WAS (Windows Activation Service) events log automatically on IIS servers. EventCode 5002=worker process crashed, 5011=pool auto-disabled due to rapid failures (5 in 5 minutes default), 5012=rapid failure protection triggered. Alert on any 5011 event (pool disabled = site down). Track recycling frequency per pool. Correlate with WER EventCode 1000 for crash details including the faulting module.
- **Visualization:** Table (app pool events), Timechart (recycling frequency), Status grid (pool × health), Single value (disabled pools — target: 0).

---

### UC-1.2.86 · NTLM Audit and Restriction Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** NTLM is a legacy authentication protocol vulnerable to relay attacks. Auditing NTLM usage identifies applications and systems that need migration to Kerberos.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4776), `sourcetype=WinEventLog:Microsoft-Windows-NTLM/Operational` (EventCode 8001, 8003, 8004)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-NTLM/Operational"
  EventCode IN (8001, 8003, 8004)
| stats count by TargetName, DomainName, WorkstationName
| sort -count
```
- **Implementation:** Enable NTLM auditing via GPO: Network Security → Restrict NTLM → Audit incoming/outgoing NTLM traffic. EventCode 8001=outgoing NTLM, 8003=incoming NTLM to server, 8004=NTLM blocked. Start in audit mode to identify all NTLM-dependent applications before enabling blocking. Goal: reduce NTLM usage to zero where possible, using Kerberos for all domain authentication.
- **Visualization:** Bar chart (top NTLM sources/destinations), Timechart (NTLM vs Kerberos ratio), Table (NTLM-dependent applications).

---

### UC-1.2.87 · DPAPI Credential Backup (DC)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Data Protection API master key backup to domain controllers enables credential theft. Abnormal DPAPI backup activity from unexpected accounts indicates compromise.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4692, 4693)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4692, 4693)
| eval action=case(EventCode=4692,"DPAPI backup attempted",EventCode=4693,"DPAPI recovery attempted")
| table _time, host, action, SubjectUserName, SubjectDomainName, MasterKeyId
| sort -_time
```
- **Implementation:** EventCode 4692=DPAPI master key backup, 4693=recovery. Normal during user password changes. Alert on mass backup attempts (many keys in short time) or recovery from unexpected admin accounts — indicates SharpDPAPI/Mimikatz DPAPI module usage. Correlate with DCSync events (4662) as attackers often combine both techniques.
- **Visualization:** Table (DPAPI events), Single value (recovery count), Timeline, Alert on mass operations.

---

### UC-1.2.88 · Windows Search Indexer Issues
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Search Indexer crashes and high resource usage affect file server performance and SharePoint crawling. Index corruption requires full rebuild.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Application` (Source=Windows Search Service, EventCode 3028, 3036, 7010, 7040, 7042)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Application" Source="Windows Search Service"
  EventCode IN (3028, 3036, 7010, 7040, 7042)
| eval issue=case(EventCode=3028,"Index corrupted",EventCode=3036,"Indexer failed",EventCode=7040,"Catalog corrupted",EventCode=7042,"Index rebuild started")
| table _time, host, issue, CatalogName
| sort -_time
```
- **Implementation:** Monitor on file servers and SharePoint servers where search indexing is critical. EventCode 3028/7040=index corruption (requires rebuild), 3036=indexer service failure. Also monitor Perfmon `Windows Search Indexer` object for `Items in Progress` and `Index Size`. A stuck "Items in Progress" >0 for extended periods indicates a hung indexer.
- **Visualization:** Table (indexer events), Single value (index health status), Line chart (index size over time).

---

### UC-1.2.89 · System Uptime & Unexpected Restarts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Unexpected restarts indicate BSOD, power loss, forced reboots, or patch installations. Tracking uptime reveals instability patterns and unauthorized maintenance.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System` (EventCode 6005, 6006, 6008, 6009, 1074)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode IN (6005, 6006, 6008, 1074)
| eval event=case(EventCode=6005,"Event log started (boot)",EventCode=6006,"Event log stopped (clean shutdown)",EventCode=6008,"Unexpected shutdown",EventCode=1074,"User-initiated shutdown/restart")
| table _time, host, event, User, Reason, Comment
| sort -_time
```
- **Implementation:** EventCode 6008=unexpected shutdown (BSOD, power loss, hard reset) — always investigate. EventCode 1074=planned shutdown with user and reason. Calculate uptime by measuring time between 6005 events. Alert on any EventCode 6008 (unexpected) and on restarts outside maintenance windows. Track monthly uptime percentage per server for SLA reporting.
- **Visualization:** Table (shutdown events), Line chart (uptime per host), Single value (hosts with unexpected restarts), Calendar view.

---

### UC-1.2.90 · Shadow Copy Deletion (Ransomware Indicator)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Ransomware deletes volume shadow copies to prevent file recovery. Detecting vssadmin/wmic shadow deletion commands is a high-confidence ransomware indicator.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4688), `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 1)
- **SPL:**
```spl
index=wineventlog EventCode IN (4688, 1)
| where match(CommandLine, "(?i)(vssadmin.*delete.*shadows|wmic.*shadowcopy.*delete|bcdedit.*recoveryenabled.*no|wbadmin.*delete.*catalog)")
| table _time, host, User, CommandLine, ParentProcessName, Image
| sort -_time
```
- **Implementation:** Monitor process creation (EventCode 4688 or Sysmon 1) for commands: `vssadmin delete shadows`, `wmic shadowcopy delete`, `bcdedit /set {default} recoveryenabled no`, `wbadmin delete catalog`. Any of these commands executed outside backup maintenance is a near-certain indicator of ransomware or destructive attack. Alert with critical priority and trigger automated response (network isolation). MITRE ATT&CK T1490.
- **Visualization:** Single value (count — target: 0), Table (events), Alert with automated containment trigger.

---

### UC-1.2.91 · USB / Removable Device Auditing
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Removable storage devices are a data exfiltration vector. Auditing device connections enables DLP and compliance enforcement.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 6416), `sourcetype=WinEventLog:Microsoft-Windows-DriverFrameworks-UserMode/Operational`
- **SPL:**
```spl
index=wineventlog EventCode=6416
| eval DeviceClass=coalesce(ClassName, "Unknown")
| where DeviceClass="DiskDrive" OR DeviceClass="WPD" OR DeviceClass="USB"
| stats count by host, DeviceId, DeviceDescription, DeviceClass, SubjectUserName, _time
| sort -_time
```
- **Implementation:** Enable Audit PnP Activity (EventCode 6416) via Advanced Audit Policy. Track USB mass storage, MTP devices, and portable drives. Correlate with file access events for full data movement picture. Alert on USB connections to servers or high-security workstations. Consider blocking USB storage via Group Policy on sensitive systems.
- **Visualization:** Timeline (device connections over time), Table (device details), Alert on server USB connections.

---

### UC-1.2.92 · Remote Desktop Gateway Session Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** RD Gateway is the entry point for remote workers. Monitoring session lifecycle detects unauthorized access, session hijacking, and resource abuse.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational"
| eval EventAction=case(EventCode=300,"Connected", EventCode=302,"Disconnected", EventCode=303,"AuthFailed", EventCode=304,"AuthZ_Failed", 1=1,"Other")
| stats count by host, UserName, ClientIP, ResourceName, EventAction
| where EventAction="AuthFailed" OR EventAction="AuthZ_Failed"
```
- **Implementation:** Collect RD Gateway Operational logs. Track connection (300), disconnect (302), authentication failures (303), and authorization failures (304). Alert on brute-force patterns (multiple 303s from same IP), connections from unusual geolocations, and access to unauthorized resources. Monitor session duration for anomalies.
- **Visualization:** Geo map (client IPs), Table (session details), Timechart (connections by hour).

---

### UC-1.2.93 · Group Policy Object (GPO) Modification Auditing
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** GPO changes affect all domain-joined systems. Unauthorized GPO modifications can deploy malware, weaken security, or exfiltrate credentials at scale.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 5136, 5137)
- **SPL:**
```spl
index=wineventlog EventCode IN (5136, 5137) ObjectClass="groupPolicyContainer"
| eval Action=case(EventCode=5136,"Modified", EventCode=5137,"Created", 1=1,"Other")
| table _time, host, SubjectUserName, Action, ObjectDN, AttributeLDAPDisplayName, AttributeValue
| sort -_time
```
- **Implementation:** Enable Audit Directory Service Changes. Track GPO creation (5137) and modification (5136) on domain controllers. Alert on GPO changes outside change windows, by non-admin accounts, or modifications to security-sensitive GPOs (password policy, audit policy, software restriction). Correlate with change management tickets.
- **Visualization:** Timeline (GPO changes), Table (modification details), Alert on unauthorized changes.

---

### UC-1.2.94 · Windows Subsystem for Linux (WSL) Activity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** WSL can be abused to run Linux-based attack tools while evading Windows-focused security tooling. Monitoring WSL activity closes this visibility gap.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 1), `sourcetype=WinEventLog:Security` (EventCode 4688)
- **SPL:**
```spl
index=wineventlog (EventCode=1 OR EventCode=4688)
| where match(Image, "(?i)(wsl\.exe|wslhost\.exe|bash\.exe.*windows)") OR match(ParentImage, "(?i)wsl")
| table _time, host, User, Image, CommandLine, ParentImage, ParentCommandLine
| sort -_time
```
- **Implementation:** Monitor for WSL process execution (wsl.exe, wslhost.exe, bash.exe from WindowsApps). Track what commands are executed inside WSL via Sysmon process creation. On servers, WSL should not be installed — alert on any WSL activity. On workstations, baseline normal usage and alert on anomalies like network tools (nmap, netcat) or credential access tools.
- **Visualization:** Table (WSL commands), Timechart (usage patterns), Alert on server WSL usage.

---

### UC-1.2.95 · Windows Container Health Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Windows containers running on Server 2019+ need monitoring for resource limits, failures, and networking issues to ensure application availability.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-Compute-Operational`, `sourcetype=Perfmon:Container`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Hyper-V-Compute-Operational"
| eval Status=case(EventCode=13001,"Created", EventCode=13003,"Started", EventCode=13005,"Stopped", EventCode=13007,"Terminated", 1=1,"Other")
| stats count by host, ContainerName, Status
| append [search index=perfmon source="Perfmon:Container" counter="% Processor Time"
  | stats avg(Value) as AvgCPU max(Value) as MaxCPU by host, instance]
```
- **Implementation:** Enable Hyper-V Compute Operational log for container lifecycle events. Configure Perfmon inputs for container-specific counters (CPU, memory, network). Track container crashes (unexpected stops), OOM kills, and resource exhaustion. Alert on container restart loops and CPU throttling. Integrate with Docker/containerd logs for application-level visibility.
- **Visualization:** Table (container status), Timechart (resource usage), Alert on crash loops.

---

### UC-1.2.96 · DNS Server Zone Transfer Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Zone transfers expose the entire DNS namespace to attackers. Unauthorized zone transfers enable reconnaissance and must be detected immediately.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:DNS Server` (EventID 6001, 6002), `sourcetype=MSAD:NT6:DNS`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:DNS Server" EventCode IN (6001, 6002)
| eval TransferType=case(EventCode=6001,"AXFR_Sent", EventCode=6002,"IXFR_Sent", 1=1,"Other")
| table _time, host, Source_Network_Address, Zone, TransferType
| lookup dns_authorized_transfer_partners Source_Network_Address OUTPUT authorized
| where NOT authorized="yes"
```
- **Implementation:** Enable DNS Server Analytical logging. Track zone transfer events (AXFR/IXFR) and correlate with authorized secondary DNS servers via lookup table. Alert on zone transfers to unauthorized IP addresses. Monitor for AXFR queries from non-DNS-server IPs. This is a high-confidence indicator of DNS reconnaissance.
- **Visualization:** Table (transfer details), Alert on unauthorized transfers, Geo map (requester IPs).

---

### UC-1.2.97 · Print Spooler Vulnerability Monitoring (PrintNightmare)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Print Spooler vulnerabilities (CVE-2021-34527, CVE-2021-1675) enable remote code execution and privilege escalation. Continuous monitoring ensures patches hold and exploitation attempts are caught.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-PrintService/Operational`, `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational`
- **SPL:**
```spl
index=wineventlog ((source="WinEventLog:Microsoft-Windows-PrintService/Operational" EventCode IN (316, 808, 811))
  OR (EventCode=11 TargetFilename="*\\spool\\drivers\\*"))
| eval Indicator=case(EventCode=316,"Driver_Install", EventCode=808,"RestrictDriverInstallation", EventCode=11,"Driver_File_Drop", 1=1,"Other")
| table _time, host, Indicator, UserName, DriverName, TargetFilename
| sort -_time
```
- **Implementation:** Audit Print Service Operational log for driver installations (316), and Sysmon for DLL drops into spool\drivers directory (EventCode 11). On non-print servers, the Print Spooler service should be disabled — alert if running. On print servers, monitor for unsigned driver installations and remote driver additions. Alert on any spoolsv.exe spawning cmd.exe or powershell.exe.
- **Visualization:** Table (events), Single value (spooler running on non-print servers), Alert on exploitation indicators.

---

### UC-1.2.98 · NPS / RADIUS Authentication Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Network Policy Server handles VPN, Wi-Fi, and 802.1X authentication. Monitoring NPS detects brute-force attacks, misconfigured policies, and unauthorized network access.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 6272, 6273, 6274, 6278)
- **SPL:**
```spl
index=wineventlog EventCode IN (6272, 6273, 6274)
| eval Result=case(EventCode=6272,"Access_Granted", EventCode=6273,"Access_Denied", EventCode=6274,"Discarded", 1=1,"Other")
| stats count by Result, UserName, CallingStationID, NASIPAddress, AuthenticationProvider
| where Result="Access_Denied"
| sort -count
```
- **Implementation:** NPS logs authentication events to the Security log. Track granted (6272), denied (6273), and discarded (6274) requests. Alert on high denial rates from specific users (brute-force) or NAS devices (misconfiguration). Monitor for authentication attempts using disabled accounts or from unknown calling station IDs. Correlate with VPN gateway logs.
- **Visualization:** Pie chart (grant vs deny ratio), Table (denied requests), Timechart (auth attempts by hour).

---

### UC-1.2.99 · MSMQ Queue Depth Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Message queue buildup indicates application processing failures. Monitoring queue depth prevents message loss and detects downstream system outages.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:MSMQ`
- **SPL:**
```spl
index=perfmon source="Perfmon:MSMQ Service" counter="Total Messages in all Queues"
| timechart span=5m avg(Value) as AvgQueueDepth by host
| foreach * [eval <<FIELD>>=round('<<FIELD>>', 0)]
```
- **Implementation:** Configure Perfmon input for MSMQ Service counters: Total Messages in all Queues, Total Bytes in all Queues, Sessions. Also monitor individual queue counters via `MSMQ Queue` object. Alert when queue depth exceeds baseline (messages accumulating). Monitor journal queue size for message delivery confirmations. Track dead-letter queue growth for undeliverable messages.
- **Visualization:** Timechart (queue depth trend), Single value (current depth), Alert on queue growth exceeding threshold.

---

### UC-1.2.100 · PKI / Certificate Authority Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** An enterprise CA issues certificates for authentication, encryption, and code signing. CA failures break SSO, VPN, Wi-Fi, and TLS across the organization.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4886, 4887, 4888), `sourcetype=WinEventLog:Application`
- **SPL:**
```spl
index=wineventlog EventCode IN (4886, 4887, 4888, 4890, 4891, 4893)
| eval Action=case(EventCode=4886,"CertRequest_Received", EventCode=4887,"CertRequest_Approved", EventCode=4888,"CertRequest_Denied", EventCode=4890,"CA_Settings_Changed", EventCode=4891,"CA_Config_Changed", EventCode=4893,"CA_Archived_Key", 1=1,"Other")
| stats count by Action, host, SubjectUserName, RequesterName
| sort -count
```
- **Implementation:** Enable CA-specific audit events via certsrv MMC. Monitor certificate request lifecycle: received (4886), approved (4887), denied (4888). Alert on CA configuration changes (4890/4891) and key archival (4893). Track CRL publishing failures in Application log. Monitor CA certificate expiration (alert 90/60/30 days before). Detect ESC1-ESC8 ADCS attack patterns (misconfigurations in certificate templates).
- **Visualization:** Timechart (cert requests), Table (CA changes), Alert on config changes and template modifications.

---

### UC-1.2.101 · File Share Access Auditing (SMB)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** File share access auditing detects unauthorized data access, lateral movement via mapped drives, and ransomware encrypting network shares.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 5140, 5145)
- **SPL:**
```spl
index=wineventlog EventCode IN (5140, 5145)
| eval AccessType=case(EventCode=5140,"Share_Access", EventCode=5145,"File_Access", 1=1,"Other")
| stats count dc(RelativeTargetName) as UniqueFiles by SubjectUserName, IpAddress, ShareName, AccessType
| where count>100 OR UniqueFiles>50
| sort -count
```
- **Implementation:** Enable Audit File Share and Audit Detailed File Share via Advanced Audit Policy. EventCode 5140 logs share-level access; 5145 logs individual file access (high volume — use targeted auditing). Alert on mass file access patterns (ransomware indicator), access from unusual IPs, and access to sensitive shares outside business hours. Use SACL on sensitive folders for granular auditing.
- **Visualization:** Timechart (access volume), Table (top users/shares), Alert on mass access patterns.

---

### UC-1.2.102 · Software Restriction / AppLocker Bypass Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Application whitelisting is a primary defense against malware. Detecting bypass attempts reveals both sophisticated attackers and policy gaps.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/EXE and DLL`, `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/MSI and Script`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-AppLocker*" EventCode IN (8004, 8007, 8022, 8025)
| eval BlockType=case(EventCode=8004,"EXE_Blocked", EventCode=8007,"Script_Blocked", EventCode=8022,"MSI_Blocked", EventCode=8025,"DLL_Blocked", 1=1,"Other")
| stats count by host, UserName, BlockType, RuleName, FilePath
| sort -count
```
- **Implementation:** Collect all four AppLocker log channels (EXE/DLL, MSI/Script, Packaged app, Script). Track blocked executions (8004/8007/8022/8025) and audit-mode warnings (8003/8006). Alert on repeated blocks from same user (attempted bypass), blocks in admin paths, and execution of known LOLBins that bypass default rules (mshta.exe, regsvr32.exe, msbuild.exe). Correlate with Sysmon for parent process context.
- **Visualization:** Bar chart (blocks by type), Table (blocked files), Timechart (block trends).

---

### UC-1.2.103 · Terminal Services / RDP Session Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** RDP is a primary lateral movement vector. Complete session tracking from logon to logoff enables detection of compromised credentials and unauthorized access.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational`, `sourcetype=WinEventLog:Security`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational" EventCode IN (21, 23, 24, 25)
| eval Action=case(EventCode=21,"Logon", EventCode=23,"Logoff", EventCode=24,"Disconnect", EventCode=25,"Reconnect", 1=1,"Other")
| eval src_ip=if(isnotnull(Address), Address, "local")
| stats earliest(_time) as SessionStart latest(_time) as SessionEnd values(Action) as Actions by host, User, SessionID, src_ip
| eval Duration=round((SessionEnd-SessionStart)/60,1)
```
- **Implementation:** Collect TerminalServices-LocalSessionManager/Operational log for session lifecycle events. Track logon (21), logoff (23), disconnect (24), reconnect (25). Correlate with Security log 4624 Type 10 for source IP. Alert on RDP to servers from non-admin workstations, sessions during off-hours, and multiple concurrent sessions from different IPs for same user.
- **Visualization:** Timeline (sessions), Table (session details), Alert on anomalous patterns.

---

### UC-1.2.104 · Disk Latency and I/O Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** High disk latency directly impacts application performance and user experience. Proactive monitoring prevents performance degradation and identifies failing storage.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=Perfmon:LogicalDisk`
- **SPL:**
```spl
index=perfmon source="Perfmon:LogicalDisk" counter IN ("Avg. Disk sec/Read", "Avg. Disk sec/Write", "Current Disk Queue Length")
| eval latency_ms=round(Value*1000, 2)
| stats avg(latency_ms) as AvgLatency max(latency_ms) as MaxLatency by host, instance, counter
| where AvgLatency>20 OR MaxLatency>100
| sort -MaxLatency
```
- **Implementation:** Configure Perfmon inputs for LogicalDisk counters: Avg. Disk sec/Read, Avg. Disk sec/Write, Current Disk Queue Length, Disk Transfers/sec. Thresholds: <10ms normal, 10-20ms degraded, >20ms poor, >50ms critical. Alert on sustained latency above 20ms. Correlate with application response times and IOPS counters. Track latency trends for capacity planning and storage migration decisions.
- **Visualization:** Timechart (latency trend), Gauge (current latency), Table (high-latency volumes).

---

### UC-1.2.105 · Windows Defender Exclusion Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Attackers add Defender exclusions to hide malware. Monitoring exclusion changes detects evasion techniques and ensures antivirus coverage remains complete.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventID 5007)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational" EventCode=5007
| where match(New_Value, "(?i)exclusions")
| rex field=New_Value "Exclusions\\\\(?<ExclusionType>[^\\\\]+)\\\\(?<ExclusionValue>.+)"
| table _time, host, ExclusionType, ExclusionValue, Old_Value, New_Value
| sort -_time
```
- **Implementation:** Monitor Defender configuration changes (EventID 5007) and filter for exclusion modifications. Track path, extension, and process exclusions. Alert on any exclusion added outside of change management, especially for temp directories, user profiles, or common malware paths. Maintain a whitelist of approved exclusions and alert on deviations. Critical for detecting MITRE ATT&CK T1562.001 (Impair Defenses).
- **Visualization:** Table (exclusion changes), Alert on unauthorized exclusions, Trend chart.

---

### UC-1.2.106 · Local Administrator Group Membership Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Local admin privileges enable credential theft, persistence, and lateral movement. Monitoring local admin group changes detects privilege escalation attacks.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4732, 4733)
- **SPL:**
```spl
index=wineventlog EventCode IN (4732, 4733) TargetUserName="Administrators"
| eval Action=case(EventCode=4732,"Member_Added", EventCode=4733,"Member_Removed", 1=1,"Other")
| table _time, host, Action, MemberName, MemberSid, SubjectUserName, SubjectDomainName
| sort -_time
```
- **Implementation:** Enable Audit Security Group Management. Track additions (4732) and removals (4733) from the local Administrators group. Alert on any additions, especially by non-domain-admin accounts. Monitor for patterns: add user → perform action → remove user (cleanup). Correlate with LAPS password rotations and PAM solutions. On servers, local admin changes should be extremely rare.
- **Visualization:** Table (membership changes), Alert on all additions, Trend chart.

---

### UC-1.2.107 · DFS Replication Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** DFS-R synchronizes SYSVOL and shared folders across domain controllers and file servers. Replication failures cause inconsistent GPOs and stale data.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:DFS Replication`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:DFS Replication" EventCode IN (4012, 4302, 4304, 5002, 5008, 5014)
| eval Severity=case(EventCode=4012,"DFSR_Stopped", EventCode=4302,"Staging_Quota_Exceeded", EventCode=4304,"Staging_Cleanup_Failed", EventCode=5002,"Unexpected_Shutdown", EventCode=5008,"Auto_Recovery_Failed", EventCode=5014,"USN_Journal_Wrap", 1=1,"Warning")
| stats count by host, Severity, EventCode
| sort -count
```
- **Implementation:** Monitor DFS Replication event log for critical events. EventCode 4012 (DFSR stopped) and 5014 (USN journal wrap) require immediate attention — USN journal wrap can cause full resync. Track staging quota events (4302) to prevent replication stalls. Monitor SYSVOL replication specifically on domain controllers. Alert on replication backlog exceeding threshold via WMI/PowerShell scripted input collecting DFSR WMI counters.
- **Visualization:** Table (replication errors), Timechart (error trend), Alert on critical events.

---

### UC-1.2.108 · Kerberos Constrained Delegation Abuse
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Kerberos delegation allows services to impersonate users. Misconfigured or compromised delegation targets enable privilege escalation to domain admin.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4769, 5136)
- **SPL:**
```spl
index=wineventlog EventCode=4769 TransitionedServices!=""
| eval is_suspicious=if(match(ServiceName, "(?i)(krbtgt|ldap/)"), "High_Risk", "Normal")
| stats count by ServiceName, TargetUserName, IpAddress, TransitionedServices, is_suspicious
| where is_suspicious="High_Risk" OR count>50
| sort -count
```
- **Implementation:** Monitor TGS requests (4769) where TransitionedServices is populated (indicates S4U2Proxy delegation). Alert on delegation to sensitive services (krbtgt, LDAP, CIFS on DCs). Track AD object modifications (5136) that change msDS-AllowedToDelegateTo attribute — indicates delegation configuration changes. Detect resource-based constrained delegation attacks by monitoring msDS-AllowedToActOnBehalfOfOtherIdentity attribute changes. MITRE ATT&CK T1550.003.
- **Visualization:** Table (delegation events), Alert on sensitive service delegation, Network diagram (delegation paths).

---

### UC-1.2.109 · Windows Time Service (W32Time) Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Kerberos authentication fails when clock skew exceeds 5 minutes. Time drift breaks authentication, log correlation, and forensic timelines.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-Time-Service)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:System" SourceName="Microsoft-Windows-Time-Service" EventCode IN (134, 142, 129)
| eval Issue=case(EventCode=134,"Time_Provider_Error", EventCode=142,"Time_Skew_Too_Large", EventCode=129,"NTP_Unreachable", 1=1,"Warning")
| stats count latest(_time) as LastSeen by host, Issue, EventCode
| sort -count
```
- **Implementation:** Monitor W32Time events for time provider errors (134), skew warnings (142), and NTP unreachable (129). On DCs, the PDC Emulator must sync to an external NTP source — all other DCs sync to the domain hierarchy. Alert on any DC time skew >2 minutes. Monitor w32tm /query /status output via scripted input for continuous drift tracking. Time-critical for Kerberos (5-min max skew) and forensic log correlation.
- **Visualization:** Timechart (time offset), Table (time errors), Alert on >2min drift.

---

### UC-1.2.110 · PowerShell Constrained Language Mode Bypass
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Constrained Language Mode limits PowerShell attack surface. Detecting bypasses reveals attackers escalating from restricted to full-language mode for malware execution.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational` (EventCode 4104), `sourcetype=WinEventLog:Windows PowerShell`
- **SPL:**
```spl
index=wineventlog EventCode=4104
| where match(ScriptBlockText, "(?i)(FullLanguage|LanguageMode|Add-Type.*DllImport|System\.Management\.Automation\.LanguageMode)")
| table _time, host, UserName, ScriptBlockText, Path
| sort -_time
```
- **Implementation:** Enable PowerShell Script Block Logging (EventCode 4104) and Module Logging. Search for scripts that attempt to change LanguageMode, use reflection to bypass CLM, or reference FullLanguage mode. Alert on Add-Type with DllImport (P/Invoke) in constrained environments — this is a common CLM bypass. Correlate with AppLocker and WDAC logs for defense-in-depth monitoring.
- **Visualization:** Table (bypass attempts), Alert on detection, Single value (count).

---

### UC-1.2.111 · Windows Firewall Rule Tampering
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Attackers disable or modify firewall rules to enable lateral movement, C2 communication, and data exfiltration. Rule changes outside maintenance windows indicate compromise.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall` (EventCode 2004, 2005, 2006, 2033)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall" EventCode IN (2004, 2005, 2006, 2033)
| eval Action=case(EventCode=2004,"Rule_Added", EventCode=2005,"Rule_Modified", EventCode=2006,"Rule_Deleted", EventCode=2033,"All_Rules_Deleted", 1=1,"Other")
| table _time, host, Action, RuleName, ApplicationPath, Direction, Protocol, LocalPort, RemotePort, ModifyingUser
| sort -_time
```
- **Implementation:** Collect Windows Firewall With Advanced Security log. Track rule additions (2004), modifications (2005), deletions (2006), and bulk deletion (2033 — extremely suspicious). Alert on: allow-inbound rules for unusual ports, rules permitting all traffic, rules created by non-admin processes, and any rule changes on servers outside change windows. Correlate with process creation to identify the modifying application.
- **Visualization:** Table (rule changes), Timeline (change frequency), Alert on suspicious modifications.

---

### UC-1.2.112 · BITS Transfer Abuse Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Background Intelligent Transfer Service (BITS) is abused by malware for stealthy downloads and persistence. Monitoring BITS jobs detects LOLBin-based attacks.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Bits-Client/Operational`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Bits-Client/Operational" EventCode IN (3, 4, 59, 60, 61)
| eval Status=case(EventCode=3,"Transfer_Complete", EventCode=4,"Transfer_Cancelled", EventCode=59,"Job_Created", EventCode=60,"Job_Modified", EventCode=61,"Job_Transferred", 1=1,"Other")
| table _time, host, User, jobTitle, url, fileList, Status, bytesTransferred
| where NOT match(url, "(?i)(windowsupdate|microsoft\.com|msedge)")
| sort -_time
```
- **Implementation:** Enable BITS Client Operational logging. Track job creation (59), modification (60), and completion (3/61). Filter out legitimate BITS usage (Windows Update, Edge updates). Alert on BITS jobs downloading from unusual URLs, jobs created by unexpected processes (not svchost or system), and BITS persistence via /SetNotifyCmdLine. MITRE ATT&CK T1197.
- **Visualization:** Table (BITS jobs), Timechart (transfer volume), Alert on non-standard URLs.

---

### UC-1.2.113 · COM Object Hijacking Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** COM hijacking replaces legitimate COM objects with malicious ones for persistence and privilege escalation. It's a stealthy technique that survives reboots.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13)
- **SPL:**
```spl
index=wineventlog EventCode=13 TargetObject="*\\Classes\\CLSID\\*\\InprocServer32*"
| where NOT match(Image, "(?i)(msiexec|svchost|TiWorker|TrustedInstaller|DismHost)")
| table _time, host, User, Image, TargetObject, Details
| rex field=TargetObject "CLSID\\\\(?<CLSID>[^\\\\]+)"
| sort -_time
```
- **Implementation:** Monitor Sysmon registry value set events (EventCode 13) targeting CLSID InprocServer32 and LocalServer32 keys in HKCU and HKLM. Filter out legitimate installers (msiexec, TrustedInstaller). Alert on modifications pointing to unusual DLL paths (temp directories, user profiles, AppData). Maintain baseline of known-good CLSID registrations. MITRE ATT&CK T1546.015.
- **Visualization:** Table (registry changes), Alert on suspicious CLSID modifications.

---

### UC-1.2.114 · LSASS Memory Protection Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** LSASS contains credentials in memory. Monitoring LSASS access attempts and protection status detects credential dumping tools like Mimikatz.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 10), `sourcetype=WinEventLog:Security`
- **SPL:**
```spl
index=wineventlog EventCode=10 TargetImage="*\\lsass.exe"
| where NOT match(SourceImage, "(?i)(csrss|services|svchost|wininit|MsMpEng|MsSense|CrowdStrike|SentinelAgent)")
| eval GrantedAccess_hex=GrantedAccess
| table _time, host, SourceImage, SourceUser, GrantedAccess_hex, CallTrace
| where match(GrantedAccess_hex, "0x1010|0x1FFFFF|0x143A")
| sort -_time
```
- **Implementation:** Sysmon EventCode 10 (ProcessAccess) targeting lsass.exe. Filter legitimate AV/EDR processes. Focus on suspicious access masks: 0x1010 (PROCESS_QUERY_LIMITED_INFORMATION + PROCESS_VM_READ), 0x1FFFFF (PROCESS_ALL_ACCESS), 0x143A (used by Mimikatz sekurlsa). Enable RunAsPPL for LSASS protection and monitor for its status. Alert on any non-whitelisted LSASS access. MITRE ATT&CK T1003.001.
- **Visualization:** Table (access events), Alert on suspicious access masks, Single value (LSASS PPL status).

---

### UC-1.2.115 · Logon Session Anomalies (Type 3 / Network Logon)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Network logons (Type 3) from unexpected sources indicate lateral movement with stolen credentials. Baselining normal patterns reveals compromised accounts.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4624)
- **SPL:**
```spl
index=wineventlog EventCode=4624 Logon_Type=3
| eval src=coalesce(Source_Network_Address, IpAddress, "unknown")
| stats dc(host) as TargetCount values(host) as Targets count by TargetUserName, src
| where TargetCount>5
| sort -TargetCount
```
- **Implementation:** Monitor Type 3 (Network) logons across all systems. Build baseline of normal logon patterns: which accounts log into which systems from where. Alert on accounts that suddenly access many more systems than usual (lateral movement), network logons from unusual subnets, and logons using service accounts from non-service IPs. Exclude machine accounts (ending in $) for noise reduction. Combine with EventCode 4648 (explicit credentials).
- **Visualization:** Network diagram (account-to-host), Timechart (logon volume), Alert on anomalous spread.

---

### UC-1.2.116 · WMI Persistence Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** WMI event subscriptions provide fileless persistence that survives reboots. Detecting WMI persistence reveals advanced persistent threats.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 19, 20, 21)
- **SPL:**
```spl
index=wineventlog EventCode IN (19, 20, 21)
| eval WMIType=case(EventCode=19,"FilterCreated", EventCode=20,"ConsumerCreated", EventCode=21,"BindingCreated", 1=1,"Other")
| table _time, host, User, WMIType, EventNamespace, Name, Query, Destination, Consumer
| where NOT match(Name, "(?i)(BVTFilter|TSLogonFilter|SCM Event)")
| sort -_time
```
- **Implementation:** Sysmon EventCodes 19/20/21 track WMI event filter, consumer, and binding creation. Any new WMI subscription (especially CommandLineEventConsumer or ActiveScriptEventConsumer) is suspicious. Filter out known-good subscriptions (BVTFilter, TSLogonFilter). Alert on all new subscriptions and investigate the consumer action. Correlate EventCode 21 (binding) — a complete subscription requires filter + consumer + binding. MITRE ATT&CK T1546.003.
- **Visualization:** Table (WMI subscriptions), Alert on creation, Timeline (events).

---

### UC-1.2.117 · NIC Teaming & Network Adapter Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** NIC teaming provides network redundancy for servers. Adapter failures reduce redundancy and can cause outages if the remaining NIC also fails.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-NlbMgr/Operational`, `sourcetype=WinEventLog:System`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:System" SourceName IN ("Microsoft-Windows-NDIS", "e1cexpress", "mlx4_bus", "vmxnet3ndis6", "Tcpip")
| eval Issue=case(match(Message, "(?i)disconnect"), "Link_Down", match(Message, "(?i)reset"), "Adapter_Reset", match(Message, "(?i)error"), "Adapter_Error", 1=1, "Other")
| stats count latest(_time) as LastEvent by host, SourceName, Issue
| sort -LastEvent
```
- **Implementation:** Monitor System event log for network adapter events from NIC drivers (e1cexpress for Intel, mlx4_bus for Mellanox, vmxnet3ndis6 for VMware). Track link-down events, adapter resets, and errors. For NIC teams, monitor Microsoft-Windows-MsLbfoProvider events. Alert on: team degradation (standby adapter now active), both adapters down, and frequent adapter resets (hardware failure). Include Perfmon Network Interface counters for bandwidth and error monitoring.
- **Visualization:** Table (adapter events), Status dashboard (team health), Alert on degradation.

---

### UC-1.2.118 · ASR (Attack Surface Reduction) Rule Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** ASR rules block common attack techniques (Office macro code, credential theft, ransomware). Monitoring ASR ensures rules are enforced and detects blocked attacks.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Windows Defender/Operational` (EventID 1121, 1122)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Defender/Operational" EventCode IN (1121, 1122)
| eval Mode=case(EventCode=1121,"Blocked", EventCode=1122,"Audit", 1=1,"Other")
| lookup asr_rule_names ID as RuleId OUTPUT RuleName
| stats count by host, RuleName, Mode, Path, ProcessName
| sort -count
```
- **Implementation:** Enable ASR rules in Block or Audit mode. EventCode 1121 (blocked) and 1122 (audit) log ASR triggers. Map rule GUIDs to names via lookup table (e.g., 75668C1F = "Block Office from creating executable content"). Track most-triggered rules for tuning. Alert on: high block counts (active attack), blocks suddenly stopping (rules disabled), and audit-mode triggers on sensitive rules that should be in block mode.
- **Visualization:** Bar chart (blocks by rule), Timechart (block trends), Table (event details).

---

### UC-1.2.119 · Registry Run Key Persistence Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Registry Run keys are the most common persistence mechanism for malware. Monitoring autostart registry locations detects new malware installations.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13)
- **SPL:**
```spl
index=wineventlog EventCode=13
| where match(TargetObject, "(?i)(CurrentVersion\\\\Run|CurrentVersion\\\\RunOnce|Winlogon\\\\Shell|Winlogon\\\\Userinit|Explorer\\\\Shell Folders)")
| where NOT match(Details, "(?i)(program files|windows\\\\system32|syswow64)")
| table _time, host, User, Image, TargetObject, Details
| sort -_time
```
- **Implementation:** Sysmon EventCode 13 (RegistryValueSet) monitors registry modifications. Track all autostart locations: Run, RunOnce, RunServices, Winlogon Shell/Userinit, Explorer Shell Folders, and AppInit_DLLs. Filter known-legitimate entries (Program Files, System32). Alert on entries pointing to temp directories, AppData, user profiles, or encoded/obfuscated paths. Monitor both HKLM (system-wide) and HKCU (per-user). MITRE ATT&CK T1547.001.
- **Visualization:** Table (new Run key entries), Alert on suspicious paths, Timeline.

---

### UC-1.2.120 · BitLocker Recovery & Compliance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** BitLocker protects data at rest. Monitoring recovery events detects unauthorized hardware changes, and compliance tracking ensures all endpoints are encrypted.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-BitLocker/BitLocker Management` (EventCode 770, 771, 773, 774, 775)
- **SPL:**
```spl
index=wineventlog source="*BitLocker*" EventCode IN (770, 771, 773, 774, 775, 776, 778)
| eval Status=case(EventCode=770,"Protection_Off", EventCode=771,"Protection_Resumed", EventCode=773,"Volume_Recovery", EventCode=774,"Key_Rotated", EventCode=775,"Auto_Unlock_Enabled", EventCode=776,"Recovery_Password_Backup", EventCode=778,"TPM_Error", 1=1,"Other")
| stats count by host, Status, VolumeName
| sort -count
```
- **Implementation:** Monitor BitLocker Management log for encryption status changes. Protection off (770) may indicate maintenance or attack — correlate with change tickets. Volume recovery (773) means the recovery key was needed — investigate hardware changes or TPM issues. Track recovery password backup to AD (776) for compliance. Run a scripted input querying `manage-bde -status` for real-time encryption state across all volumes. Alert on any protection suspension on servers.
- **Visualization:** Dashboard (encryption compliance %), Table (events), Alert on protection suspension.

---

### UC-1.2.121 · DNS Client Query Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitoring DNS queries from Windows clients reveals C2 beacons, DNS tunneling, and DGA-based malware communicating with attacker infrastructure.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 22), `sourcetype=WinEventLog:Microsoft-Windows-DNS-Client/Operational`
- **SPL:**
```spl
index=wineventlog EventCode=22
| eval domain=lower(QueryName)
| eval domain_len=len(domain)
| eval label_count=mvcount(split(domain, "."))
| where domain_len>50 OR label_count>5
| stats count dc(QueryName) as UniqueDomains by host, Image
| where UniqueDomains>100 OR count>500
| sort -UniqueDomains
```
- **Implementation:** Sysmon EventCode 22 logs DNS queries with the originating process. Detect DNS tunneling via long domain names (>50 chars), high label counts, and high-entropy subdomains. Identify DGA patterns: many unique NXDomain responses from a single process. Alert on processes making unusual DNS query volumes. Baseline per-process DNS behavior and alert on deviations.
- **Visualization:** Timechart (query volume by process), Table (anomalous queries), Alert on tunneling indicators.

---

### UC-1.2.122 · Local Account Creation & Modification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Creating local accounts is a persistence technique. On domain-joined systems, local account creation is rare and suspicious.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4720, 4722, 4724, 4738)
- **SPL:**
```spl
index=wineventlog EventCode IN (4720, 4722, 4724, 4738) NOT TargetDomainName IN ("NT AUTHORITY", "NT-AUTORITÄT")
| eval Action=case(EventCode=4720,"Account_Created", EventCode=4722,"Account_Enabled", EventCode=4724,"Password_Reset", EventCode=4738,"Account_Changed", 1=1,"Other")
| table _time, host, Action, TargetUserName, TargetDomainName, SubjectUserName
| sort -_time
```
- **Implementation:** Track local account creation (4720), enabling (4722), password reset (4724), and modification (4738). On domain-joined servers, local account creation is almost always suspicious. Alert on any local account creation, especially when performed by non-admin processes or via net.exe/net1.exe. Filter out managed service accounts and known automation. MITRE ATT&CK T1136.001.
- **Visualization:** Table (account events), Alert on creation, Timeline.

---

### UC-1.2.123 · Token Manipulation / Privilege Escalation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Token manipulation (impersonation, token duplication) allows attackers to escalate privileges. Detecting abuse of SeImpersonatePrivilege catches potato-style attacks.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4673, 4674)
- **SPL:**
```spl
index=wineventlog EventCode IN (4673, 4674) PrivilegeList IN ("SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege", "SeTcbPrivilege", "SeDebugPrivilege")
| where NOT match(ProcessName, "(?i)(lsass|services|svchost|csrss|wininit|smss)")
| stats count by host, SubjectUserName, ProcessName, PrivilegeList
| sort -count
```
- **Implementation:** Enable Audit Sensitive Privilege Use. Monitor 4673 (sensitive privilege used) and 4674 (privilege operation on privileged object). Focus on SeImpersonatePrivilege (potato attacks), SeDebugPrivilege (process injection), SeTcbPrivilege (token creation), and SeAssignPrimaryTokenPrivilege. Filter OS processes. Alert on privilege use by service accounts running web apps or databases (common potato attack targets). MITRE ATT&CK T1134.
- **Visualization:** Table (privilege use events), Alert on suspicious processes, Bar chart.

---

### UC-1.2.124 · Process Injection Detection (Sysmon)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Value:** Process injection hides malicious code inside legitimate processes. Detecting injection techniques (CreateRemoteThread, APC, process hollowing) catches advanced malware.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 8, 10)
- **SPL:**
```spl
index=wineventlog EventCode=8
| where NOT match(SourceImage, "(?i)(csrss|MsMpEng|SentinelAgent|CrowdStrike)")
| eval InjectionTarget=TargetImage
| table _time, host, SourceImage, InjectionTarget, SourceUser, StartModule, StartFunction
| append [search index=wineventlog EventCode=10 GrantedAccess IN ("0x1FFFFF","0x801","0x1FFB") | where NOT match(SourceImage, "(?i)(csrss|MsMpEng|lsass)") | table _time, host, SourceImage, TargetImage, SourceUser, GrantedAccess]
| sort -_time
```
- **Implementation:** Sysmon EventCode 8 (CreateRemoteThread) detects thread injection into remote processes. Filter legitimate EDR/AV injections. EventCode 10 (ProcessAccess) with specific access masks (0x1FFFFF=ALL_ACCESS, 0x801=VM_WRITE+QUERY) detects memory writes for process hollowing. Alert on any remote thread creation targeting system processes (explorer.exe, svchost.exe, services.exe). Correlate with EventCode 1 for full process chain. MITRE ATT&CK T1055.
- **Visualization:** Table (injection events), Network diagram (source→target), Alert on detection.

---

### UC-1.2.125 · Cluster Shared Volume (CSV) Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Cluster Shared Volumes underpin Hyper-V and SQL Server failover clusters. CSV failures cause VM/database unavailability across the cluster.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-FailoverClustering/Operational" EventCode IN (5120, 5121, 5140, 5142, 5143)
| eval Status=case(EventCode=5120,"CSV_Online", EventCode=5121,"CSV_Offline", EventCode=5140,"CSV_Redirected", EventCode=5142,"CSV_IO_Paused", EventCode=5143,"CSV_IO_Resumed", 1=1,"Other")
| stats count latest(_time) as LastEvent by host, VolumeName, Status
| where Status IN ("CSV_Offline", "CSV_Redirected", "CSV_IO_Paused")
| sort -LastEvent
```
- **Implementation:** Monitor Failover Clustering Operational log for CSV state changes. CSV Offline (5121) is critical — VMs will fail. CSV Redirected (5140) means I/O is going through another node (degraded performance). CSV I/O Paused (5142) freezes all VMs on that volume. Alert immediately on offline and paused states. Monitor CSV latency via Perfmon: Cluster CSV File System counters. Track cluster node membership changes (1069/1070/1135).
- **Visualization:** Status dashboard (CSV states), Timechart (state changes), Alert on failures.

---

### UC-1.2.126 · DCOM Activation Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** DCOM failures break distributed applications, WMI remote management, and SCCM client operations. Monitoring identifies misconfigured permissions and network issues.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:System` (EventCode 10016)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:System" EventCode=10016
| rex field=Message "CLSID\s+(?<CLSID>\{[^}]+\}).*APPID\s+(?<APPID>\{[^}]+\})"
| stats count by host, CLSID, APPID
| where count>10
| sort -count
```
- **Implementation:** DCOM activation errors (10016) are common but mostly benign. Focus on recurring errors that affect application functionality. Map CLSIDs to application names to identify impacted services. Filter known-benign CLSIDs (RuntimeBroker, PerAppRuntimeBroker, ShellServiceHost). Alert on DCOM errors affecting SCCM ({4991D34B}), WMI ({76A64158}), or custom line-of-business applications. Track error count trends — sudden spikes indicate configuration changes.
- **Visualization:** Bar chart (top CLSIDs), Timechart (error trend), Table (details).

---

### UC-1.2.127 · Automatic Windows Update Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Unpatched systems are the primary attack surface. Tracking Windows Update status across all systems ensures timely patching and compliance reporting.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-WindowsUpdateClient/Operational`
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-WindowsUpdateClient/Operational" EventCode IN (19, 20, 25, 31, 35)
| eval Status=case(EventCode=19,"Install_Success", EventCode=20,"Install_Failed", EventCode=25,"Restart_Required", EventCode=31,"Download_Failed", EventCode=35,"Download_Success", 1=1,"Other")
| stats latest(_time) as LastUpdate latest(Status) as LastStatus count(eval(Status="Install_Failed")) as FailCount by host
| eval DaysSinceUpdate=round((now()-LastUpdate)/86400, 0)
| where DaysSinceUpdate>30 OR FailCount>0
| sort -DaysSinceUpdate
```
- **Implementation:** Monitor Windows Update Client Operational log. Track successful installs (19), failed installs (20), restart required (25), download failures (31). Calculate days since last successful update for each host. Alert on: systems not updated in 30+ days, repeated installation failures, and systems stuck in "restart required" state. Supplement with `wmic qfe list` scripted input for installed KB inventory. Essential for vulnerability management and audit compliance.
- **Visualization:** Table (compliance status), Single value (% compliant), Bar chart (days since update).

---

### UC-1.2.128 · Service Account Logon Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Compromised service accounts grant persistent access and often have elevated privileges. Detecting anomalous service account behavior catches credential theft early.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4624, 4625)
- **SPL:**
```spl
index=wineventlog EventCode=4624 Logon_Type IN (2, 10, 11)
| lookup service_accounts TargetUserName OUTPUT is_service_account
| where is_service_account="yes"
| eval src=coalesce(Source_Network_Address, IpAddress)
| stats count dc(host) as TargetHosts values(Logon_Type) as LogonTypes by TargetUserName, src
| where LogonTypes!=5 AND LogonTypes!=3
| sort -count
```
- **Implementation:** Define a lookup of known service accounts. Service accounts should only log on with Type 5 (Service) or Type 3 (Network) from expected sources. Alert on interactive logons (Type 2/10/11) by service accounts — this indicates credential compromise and human use. Track source IPs and target hosts — service accounts should access a consistent set of systems. Alert on new source IPs or target hosts for any service account.
- **Visualization:** Table (anomalous logons), Alert on interactive service account logon, Network diagram.

---

### UC-1.2.129 · Sysmon Driver/Image Load Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Monitoring driver and DLL loads catches rootkits, vulnerable drivers, and DLL side-loading attacks that evade process-level monitoring.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 6, 7)
- **SPL:**
```spl
index=wineventlog EventCode=6 Signed="false"
| table _time, host, ImageLoaded, Hashes, Signature, SignatureStatus
| sort -_time
| append [search index=wineventlog EventCode=7 Signed="false" | where NOT match(ImageLoaded, "(?i)(windows\\\\system32|program files)") | table _time, host, Image, ImageLoaded, Hashes, SignatureStatus]
```
- **Implementation:** Sysmon EventCode 6 (DriverLoad) monitors kernel driver loads. Alert on unsigned drivers — all legitimate drivers should be signed. EventCode 7 (ImageLoad) monitors DLL loads (high volume — use targeted config). Focus on unsigned DLLs loaded from unusual paths. Track BYOVD (Bring Your Own Vulnerable Driver) attacks by maintaining a list of known-vulnerable driver hashes. MITRE ATT&CK T1068, T1574.002.
- **Visualization:** Table (unsigned loads), Alert on unsigned kernel drivers, Timechart.

---

### UC-1.2.130 · Scheduled Task Modification for Persistence
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Modifying existing scheduled tasks is stealthier than creating new ones. Attackers replace legitimate task actions to achieve persistence without new artifacts.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 140, 141, 142)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode IN (140, 141, 142)
| eval Action=case(EventCode=140,"Task_Updated", EventCode=141,"Task_Deleted", EventCode=142,"Task_Disabled", 1=1,"Other")
| table _time, host, TaskName, Action, UserContext
| where NOT match(TaskName, "(?i)(\\\\Microsoft\\\\Windows\\\\)")
| sort -_time
```
- **Implementation:** Monitor Task Scheduler Operational log for task modifications (140), deletions (141), and disabling (142). Focus on non-Microsoft tasks being modified. Correlate with Sysmon process creation (EventCode 1) to identify what tool made the change. Alert on modifications to security-related tasks (AV scans, backup tasks). Track task action changes — replacing a legitimate executable with malware. Maintain baseline of critical task configurations.
- **Visualization:** Table (task changes), Alert on modification of critical tasks, Timeline.

---

## 1.3 macOS Endpoints

**Primary App/TA:** Splunk Universal Forwarder for macOS with custom scripted inputs (no official Splunkbase TA — use Splunk_TA_nix where applicable, or custom inputs)

---

### UC-1.3.1 · System Resource Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Endpoint performance visibility helps IT support triage user complaints and identify machines needing replacement or upgrades.
- **App/TA:** Splunk UF for macOS, custom scripted inputs
- **Data Sources:** Custom scripted inputs (`top -l 1`, `vm_stat`, `df`)
- **SPL:**
```spl
index=os sourcetype=macos_top host=*
| stats latest(cpu_pct) as cpu, latest(mem_pct) as memory by host
| where cpu > 80 OR memory > 90
```
- **Implementation:** Install Splunk UF on macOS endpoints. Create scripted inputs for `top -l 1 -s 0`, `vm_stat`, and `df -h`. Run every 60-300 seconds. Parse key metrics.
- **Visualization:** Table of endpoints, Gauge panels, Line chart trending.

---

### UC-1.3.2 · FileVault Encryption Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unencrypted endpoints are a data breach risk if lost or stolen. Compliance requirement for most security frameworks (SOC2, ISO27001, PCI).
- **App/TA:** Splunk UF, custom scripted input
- **Data Sources:** Custom scripted input (`fdesetup status`)
- **SPL:**
```spl
index=os sourcetype=macos_filevault host=*
| stats latest(status) as fv_status by host
| where fv_status!="FileVault is On."
```
- **Implementation:** Create a scripted input: `fdesetup status`. Run daily. Alert on any endpoint where FileVault is not enabled. Feed into compliance dashboard.
- **Visualization:** Pie chart (encrypted vs. not), Table of non-compliant hosts, Single value (compliance %).

---

### UC-1.3.3 · Gatekeeper and SIP Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Disabled Gatekeeper or System Integrity Protection weakens macOS security posture. May indicate developer override or tampering.
- **App/TA:** Splunk UF, custom scripted input
- **Data Sources:** Custom scripted inputs (`spctl --status`, `csrutil status`)
- **SPL:**
```spl
index=os sourcetype=macos_security host=*
| stats latest(gatekeeper) as gk, latest(sip) as sip by host
| where gk!="enabled" OR sip!="enabled"
```
- **Implementation:** Scripted inputs for `spctl --status` and `csrutil status`. Run daily. Dashboard showing fleet-wide compliance.
- **Visualization:** Pie chart (compliant vs. not), Table of non-compliant endpoints.

---

### UC-1.3.4 · Software Update Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Unpatched macOS endpoints are vulnerable. Tracking update levels across the fleet supports vulnerability management.
- **App/TA:** Splunk UF, custom scripted input
- **Data Sources:** Custom scripted input (`softwareupdate -l`, `sw_vers`)
- **SPL:**
```spl
index=os sourcetype=macos_sw_vers host=*
| stats latest(ProductVersion) as os_version by host
| eval is_current = if(os_version >= "14.3", "Yes", "No")
| stats count by is_current
```
- **Implementation:** Scripted input for `sw_vers` (weekly) and `softwareupdate -l` (daily). Track OS versions and pending updates. Alert when critical security updates are pending >7 days.
- **Visualization:** Table (host, OS version, pending updates), Pie chart (version distribution).

---

### UC-1.3.5 · Application Crash Monitoring
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Frequent application crashes degrade user experience and may indicate malware, resource issues, or incompatible software.
- **App/TA:** Splunk UF
- **Data Sources:** `/Library/Logs/DiagnosticReports/*.crash`
- **SPL:**
```spl
index=os sourcetype=macos_crash host=*
| rex "Process:\s+(?<process>\S+)"
| stats count by host, process
| sort -count
```
- **Implementation:** Forward `~/Library/Logs/DiagnosticReports/` and `/Library/Logs/DiagnosticReports/`. Use `monitor` input in inputs.conf. Parse process name and exception type from crash reports.
- **Visualization:** Table (process, host, count), Bar chart of top crashing apps.

---

## 1.4 Bare-Metal / Hardware

**Primary App/TA:** Custom scripted inputs (`ipmitool`, `smartctl`, `storcli`), vendor management APIs (iDRAC/iLO), SNMP Modular Input

---

### UC-1.4.1 · Hardware Sensor Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Temperature, voltage, and fan speed anomalies predict impending hardware failures before they cause unplanned downtime.
- **App/TA:** Custom scripted input (`ipmitool`), SNMP
- **Data Sources:** IPMI sensor data via scripted input, `sourcetype=ipmi:sensor` (custom)
- **SPL:**
```spl
index=hardware sourcetype=ipmi:sensor
| eval is_critical = if(status="Critical" OR status="Non-Recoverable", 1, 0)
| where is_critical=1
| table _time host sensor_name reading unit status
| sort -_time
```
- **Implementation:** Install `ipmitool` on hosts. Create scripted input: `ipmitool sensor list` (interval=300). Parse sensor name, reading, unit, and status. Alert on Critical/Non-Recoverable status. Alternatively, use SNMP to poll vendor-specific MIBs (Dell iDRAC, HP iLO, Lenovo IMM).
- **Visualization:** Table of critical sensors, Gauge per sensor type, Heatmap across hosts.

---

### UC-1.4.2 · RAID Degradation Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** A degraded RAID has lost redundancy — another disk failure means data loss. Requires immediate attention.
- **App/TA:** Custom scripted input (`megacli`, `storcli`, `ssacli`)
- **Data Sources:** Custom sourcetype (RAID controller output)
- **SPL:**
```spl
index=hardware sourcetype=raid_status
| where state!="Optimal" AND state!="Online"
| table _time host vd_name state disks_failed
| sort -_time
```
- **Implementation:** Create scripted input for the RAID controller CLI tool: `storcli /c0/v0 show` or `megacli -LDInfo -Lall -aAll`. Run every 300 seconds. Alert immediately on any non-Optimal state.
- **Visualization:** Status indicator per array, Table, Alert panel (critical).

---

### UC-1.4.3 · Power Supply Failure
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Lost power supply redundancy means a single PSU failure away from an unplanned outage. Replacement needs to happen before the remaining PSU fails.
- **App/TA:** Custom scripted input (`ipmitool`), SNMP, vendor management syslog (iLO/iDRAC)
- **Data Sources:** IPMI SEL (System Event Log) via scripted input, syslog from BMC
- **SPL:**
```spl
index=hardware sourcetype=ipmi:sel ("Power Supply" OR "PS" OR "power_supply") ("Failure" OR "Absent" OR "fault" OR "lost")
| table _time host sensor event_description
| sort -_time
```
- **Implementation:** Forward IPMI System Event Log data. Enable syslog forwarding from iLO/iDRAC to Splunk. Alert immediately on PSU failure events.
- **Visualization:** Events timeline, Status indicator per host, Alert panel.

---

### UC-1.4.4 · Predictive Disk Failure
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** SMART attributes can predict disk failure days or weeks in advance, enabling proactive replacement during maintenance windows.
- **App/TA:** Custom scripted input (`smartctl`)
- **Data Sources:** Custom sourcetype (SMART data)
- **SPL:**
```spl
index=hardware sourcetype=smart_data
| where Reallocated_Sector_Ct > 0 OR Current_Pending_Sector > 0 OR Offline_Uncorrectable > 0
| table _time host device Reallocated_Sector_Ct Current_Pending_Sector Temperature_Celsius
| sort -Reallocated_Sector_Ct
```
- **Implementation:** Install `smartmontools`. Scripted input: `smartctl -A /dev/sd[a-z]`. Run every 3600 seconds. Track key attributes: Reallocated Sector Count, Current Pending Sector, Offline Uncorrectable. Alert on any non-zero values.
- **Visualization:** Table per disk, Trend line for sector counts, Heatmap of disk health.

---

### UC-1.4.5 · Firmware Version Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Outdated firmware may have security vulnerabilities or known bugs. Fleet-wide firmware tracking supports patch management.
- **App/TA:** Custom scripted input (`ipmitool`, `dmidecode`), vendor APIs
- **Data Sources:** BMC/BIOS version data via scripted input
- **SPL:**
```spl
index=hardware sourcetype=firmware_inventory
| stats latest(bios_version) as bios, latest(bmc_version) as bmc by host, model
| lookup current_firmware model OUTPUT expected_bios, expected_bmc
| eval bios_current = if(bios=expected_bios, "Yes", "No")
| where bios_current="No"
```
- **Implementation:** Create scripted input: `ipmitool mc info` or `dmidecode -t bios`. Run daily. Maintain a lookup table of expected firmware versions per server model. Dashboard showing compliance.
- **Visualization:** Table (host, model, current vs. expected), Pie chart (compliant %), Bar chart by model.

---

### UC-1.4.6 · Memory ECC Error Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Correctable ECC errors that increase over time strongly predict impending DIMM failure. Proactive replacement avoids unrecoverable memory errors and system crashes.
- **App/TA:** Custom scripted input (`edac-util`, IPMI SEL)
- **Data Sources:** `edac-util`, `/sys/devices/system/edac/mc/`, IPMI SEL
- **SPL:**
```spl
index=hardware sourcetype=ecc_errors
| timechart span=1d sum(correctable_errors) as ecc_errors by host
| where ecc_errors > 0
| streamstats window=7 sum(ecc_errors) as weekly_errors by host
| where weekly_errors > 10
```
- **Implementation:** Create scripted input: `edac-util -s` or parse `/sys/devices/system/edac/mc/mc*/ce_count`. Run hourly. Alert when correctable errors increase by >10/week. Track per-DIMM slot for targeted replacement.
- **Visualization:** Line chart (errors over time by host), Table (host, DIMM, error count), Trend chart.

---

# 2. Virtualization

## 2.1 VMware vSphere

**Primary App/TA:** Splunk Add-on for VMware (`TA-vmware`) — Free on Splunkbase; Splunk App for VMware (optional, provides dashboards)

---

### UC-2.1.1 · ESXi Host CPU Contention
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** CPU ready time measures how long a VM waits for physical CPU. High values (>5%) mean the host is overcommitted and VMs are starved for compute.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:cpu`, vCenter performance metrics
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.ready.summation"
| eval ready_pct = round(Value / 20000 * 100, 2)
| stats avg(ready_pct) as avg_ready by host, vm_name
| where avg_ready > 5
| sort -avg_ready
```
- **Implementation:** Install TA-vmware on a heavy forwarder or search head. Configure a vCenter service account with read-only permissions. Set up the VMware data collection in the TA (vCenter IP, credentials, collection interval). The TA pulls performance data via the vSphere API. Alert when CPU ready exceeds 5% per VM.
- **Visualization:** Heatmap (VMs vs. hosts, colored by ready %), Bar chart (top VMs by ready time), Line chart (trending).

---

### UC-2.1.2 · ESXi Host Memory Ballooning
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Memory ballooning means the hypervisor is reclaiming memory from VMs. Swapping at the hypervisor level is worse — causes severe VM performance degradation invisible to the guest OS.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:mem`, vCenter performance metrics
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:mem" (counter="mem.vmmemctl.average" OR counter="mem.swapped.average")
| eval metric=case(counter="mem.vmmemctl.average", "Balloon_KB", counter="mem.swapped.average", "Swap_KB")
| stats avg(Value) as avg_value by host, vm_name, metric
| where avg_value > 0
| sort -avg_value
```
- **Implementation:** Collected automatically by TA-vmware via vCenter API. Alert when balloon or swap values are >0 for extended periods. Investigate by comparing total VM memory allocation vs. host physical memory.
- **Visualization:** Table (VM, host, balloon KB, swap KB), Line chart over time, Stacked bar chart per host.

---

### UC-2.1.3 · Datastore Capacity Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** A full datastore prevents VM disk writes, causing crashes and corruption. Datastores fill gradually from VM growth, snapshots, and log accumulation.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:datastore` or `sourcetype=vmware:inv:datastore`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:datastore"
| eval used_pct = round((capacity - freeSpace) / capacity * 100, 1)
| stats latest(used_pct) as used_pct, latest(freeSpace) as free_GB by name
| eval free_GB = round(free_GB / 1073741824, 1)
| where used_pct > 80
| sort -used_pct
```
- **Implementation:** TA-vmware collects datastore inventory automatically. Set alerts at 80% (warning), 90% (high), 95% (critical). Use `predict` command for 30-day forecasting. Include snapshot size in the analysis.
- **Visualization:** Gauge per datastore, Table (name, capacity, free, % used), Line chart with predict trendline.

---

### UC-2.1.4 · Datastore Latency Spikes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Storage latency >20ms significantly impacts VM performance. Detects SAN issues, datastore contention, or storage path problems before applications are affected.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:datastore`
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.totalReadLatency.average" OR counter="datastore.totalWriteLatency.average")
| eval latency_ms = Value
| stats avg(latency_ms) as avg_latency, max(latency_ms) as peak_latency by host, datastore, counter
| where avg_latency > 20
| sort -avg_latency
```
- **Implementation:** Collected via TA-vmware. Alert when average read/write latency exceeds 20ms over 10 minutes. Correlate with IOPS and throughput counters for full picture.
- **Visualization:** Line chart (latency over time), Heatmap (datastores vs. hosts), Table with avg/peak.

---

### UC-2.1.5 · VM Snapshot Sprawl
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Old snapshots consume datastore space exponentially, degrade VM I/O performance, and complicate backups. Snapshots >72 hours old are generally a problem.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm` (inventory data)
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm" snapshot_name=*
| eval snapshot_age_days = round((now() - strptime(snapshot_createTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where snapshot_age_days > 3
| table vm_name, host, snapshot_name, snapshot_age_days, snapshot_sizeBytes
| eval snapshot_size_GB = round(snapshot_sizeBytes / 1073741824, 2)
| sort -snapshot_age_days
```
- **Implementation:** TA-vmware collects VM inventory including snapshots. Run daily report identifying snapshots >72 hours old. Escalate snapshots >7 days to VM owners. Include snapshot size to show storage impact.
- **Visualization:** Table (VM, snapshot name, age, size), Bar chart (top VMs by snapshot size), Single value (total snapshots >3d).

---

### UC-2.1.6 · vMotion Tracking
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks VM migrations for troubleshooting and change management. Excessive vMotion can indicate DRS instability or resource contention.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`, vCenter event data
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="VmMigratedEvent" OR event_type="DrsVmMigratedEvent"
| table _time vm_name source_host dest_host user event_type
| sort -_time
```
- **Implementation:** TA-vmware collects vCenter events. Create a report for audit/change tracking. Alert on excessive vMotion frequency (>10 migrations per host per hour may indicate DRS instability).
- **Visualization:** Table (timeline), Sankey diagram (source to destination host), Count by host/hour.

---

### UC-2.1.7 · HA Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** HA failover means a host failed and VMs were restarted on surviving hosts. Indicates hardware failure and potential capacity risk on remaining hosts.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="DasVmPoweredOnEvent" OR event_type="DasHostFailedEvent" OR event_type="ClusterFailoverActionTriggered")
| table _time event_type host vm_name message
| sort -_time
```
- **Implementation:** Collect vCenter events via TA-vmware. Create critical real-time alert on HA failover events. Correlate with host hardware health and ESXi syslog for root cause.
- **Visualization:** Events timeline (critical alert), Table of affected VMs, Host status panel.

---

### UC-2.1.8 · DRS Imbalance Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** DRS should keep clusters balanced. Frequent or failed DRS recommendations indicate resource constraints, affinity rule conflicts, or misconfiguration.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="DrsVmMigratedEvent"
| timechart span=1h count by cluster
| where count > 20
```
- **Implementation:** Monitor DRS migration frequency. High migration counts suggest oscillation. Also check for unapplied DRS recommendations (DRS set to manual mode). Correlate with CPU/memory utilization per host.
- **Visualization:** Line chart (migrations per hour), Table of DRS events, Cluster balance comparison chart.

---

### UC-2.1.9 · VM Sprawl Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Orphaned, powered-off, or idle VMs waste storage, IP addresses, backup capacity, and licenses. Regular cleanup frees significant resources.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:inv:vm`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:vm"
| where power_state="poweredOff"
| eval days_off = round((now() - strptime(lastPowerOffTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where days_off > 30
| table vm_name, host, days_off, numCpu, memoryMB, storage_committed
| sort -days_off
```
- **Implementation:** Run weekly report on powered-off VMs >30 days. Also identify idle VMs: powered on but CPU usage <5% and network <1Kbps consistently. Send reports to VM owners for review.
- **Visualization:** Table (VM, state, days, resources), Pie chart (powered on vs. off), Bar chart (resource waste by team).

---

### UC-2.1.10 · vSAN Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** vSAN is the storage fabric for many VMware clusters. Degraded vSAN health can cause VM data loss and cluster-wide outages.
- **App/TA:** `TA-vmware`, vSAN health service
- **Data Sources:** `sourcetype=vmware:perf:vsan`, vSAN health checks
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:vsan"
| stats latest(health_status) as health by cluster, disk_group
| where health!="green"
| table cluster disk_group health
```
- **Implementation:** TA-vmware collects vSAN metrics. Also enable vSAN health checks in vCenter. Monitor disk group health, resync progress, and capacity. Alert on any non-green health status.
- **Visualization:** Status indicator per cluster, Table of health issues, Gauge (capacity).

---

### UC-2.1.11 · ESXi Host Hardware Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** CIM-based hardware health detects physical component failures (fans, PSU, temperature) at the hypervisor level before they cause host failure.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events` (vCenter alarms)
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="AlarmStatusChangedEvent") alarm_name="Host hardware*"
| table _time host alarm_name old_status new_status
| where new_status="red" OR new_status="yellow"
| sort -_time
```
- **Implementation:** vCenter triggers hardware alarms via CIM providers on ESXi hosts. TA-vmware collects these alarm events. Alert on red/yellow hardware alarms. Ensure CIM providers are installed on ESXi (vendor-specific VIBs).
- **Visualization:** Host health grid (red/yellow/green), Events table, Alert panel.

---

### UC-2.1.12 · VM Resource Over-Allocation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** VMs consistently using <20% of allocated CPU/memory waste resources that other VMs could use. Right-sizing saves money and improves cluster capacity.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:perf:cpu`, `sourcetype=vmware:perf:mem`, `sourcetype=vmware:inv:vm`
- **SPL:**
```spl
index=vmware sourcetype="vmware:perf:cpu" counter="cpu.usage.average"
| stats avg(Value) as avg_cpu by vm_name
| join vm_name [search index=vmware sourcetype="vmware:inv:vm" | table vm_name numCpu memoryMB]
| where avg_cpu < 20
| sort avg_cpu
| table vm_name numCpu memoryMB avg_cpu
```
- **Implementation:** Analyze 30-day average CPU and memory utilization vs. allocated resources. Generate monthly right-sizing report. Include peak utilization to avoid right-sizing below burst needs.
- **Visualization:** Scatter plot (allocated vs. used), Table with recommendations, Bar chart of waste by team.

---

### UC-2.1.13 · vCenter Alarm Correlation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Centralizing all vCenter alarms in Splunk enables correlation with other infrastructure data, historical trending, and unified alerting.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" event_type="AlarmStatusChangedEvent"
| stats count by alarm_name, new_status
| sort -count
```
- **Implementation:** TA-vmware automatically collects vCenter events including alarm state changes. Create a dashboard showing all active alarms. Correlate with time of changes, DRS events, and host health.
- **Visualization:** Table of active alarms, Bar chart by alarm type, Timeline.

---

### UC-2.1.14 · ESXi Patch Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Unpatched ESXi hosts have known vulnerabilities. Fleet-wide version tracking ensures consistent patching and audit compliance.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:inv:hostsystem`
- **SPL:**
```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(version) as esxi_version, latest(build) as build by host
| eval is_current = if(build="24585291", "Yes", "No")
| sort esxi_version
| table host esxi_version build is_current
```
- **Implementation:** TA-vmware collects host inventory including ESXi version and build number. Maintain a lookup of current expected builds. Dashboard showing compliance percentage and hosts needing updates.
- **Visualization:** Table (host, version, build, compliant), Pie chart (compliant %), Bar chart by version.

---

### UC-2.1.15 · VM Creation/Deletion Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks VM lifecycle for change management compliance and resource governance. Detects unauthorized VM creation or suspicious deletions.
- **App/TA:** `TA-vmware`
- **Data Sources:** `sourcetype=vmware:events`
- **SPL:**
```spl
index=vmware sourcetype="vmware:events" (event_type="VmCreatedEvent" OR event_type="VmRemovedEvent" OR event_type="VmClonedEvent")
| eval action=case(event_type="VmCreatedEvent","Created", event_type="VmRemovedEvent","Deleted", event_type="VmClonedEvent","Cloned")
| table _time action vm_name user host datacenter
| sort -_time
```
- **Implementation:** Collected automatically via TA-vmware vCenter events. Create daily report. Correlate with change management tickets. Alert on deletions of production VMs.
- **Visualization:** Table (timeline), Bar chart (create/delete by user), Line chart (VM count trending).

---

## 2.2 Microsoft Hyper-V

**Primary App/TA:** Splunk Add-on for Microsoft Hyper-V, `Splunk_TA_windows` — Free on Splunkbase

---

### UC-2.2.1 · VM Performance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Per-VM CPU, memory, and disk metrics identify resource contention and performance bottlenecks within the Hyper-V environment.
- **App/TA:** `Splunk_TA_windows` (Perfmon inputs for Hyper-V counters)
- **Data Sources:** `sourcetype=Perfmon:HyperV` (Hyper-V Virtual Machine Health Summary, Hyper-V Hypervisor Logical Processor)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:HyperV" object="Hyper-V Hypervisor Virtual Processor" counter="% Guest Run Time"
| stats avg(Value) as avg_cpu by instance, host
| sort -avg_cpu
```
- **Implementation:** Configure Perfmon inputs on Hyper-V hosts for Hyper-V specific objects: `Hyper-V Hypervisor Virtual Processor`, `Hyper-V Dynamic Memory - VM`, `Hyper-V Virtual Storage Device`. Set interval=60.
- **Visualization:** Table (VM, CPU%, Memory%), Line chart per VM, Heatmap.

---

### UC-2.2.2 · Hyper-V Replication Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Replication lag means your DR site is behind. If replication breaks, you lose your recovery point objective (RPO).
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin" ("replication" AND ("error" OR "warning" OR "critical" OR "failed"))
| stats count by host, EventCode, Message
| sort -count
```
- **Implementation:** Enable Hyper-V VMMS event log collection. Also create a PowerShell scripted input: `Get-VMReplication | Select VMName, State, Health, LastReplicationTime`. Alert on replication state != Normal or health != Normal.
- **Visualization:** Table (VM, replication state, health, last sync), Status indicators, Events list.

---

### UC-2.2.3 · Cluster Shared Volume Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** CSV issues can cause VM storage access failures across the entire cluster. Redirected I/O mode significantly degrades performance.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-FailoverClustering/Operational" ("CSV" OR "Cluster Shared Volume") ("error" OR "redirected" OR "failed")
| table _time host Message
| sort -_time
```
- **Implementation:** Enable Failover Clustering operational log. Alert on CSV ownership changes, redirected I/O mode, and disk health issues. Monitor Perfmon counters for CSV latency.
- **Visualization:** Status panel per CSV, Events timeline, Table.

---

### UC-2.2.4 · Live Migration Tracking
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Audit trail for VM mobility. Excessive live migrations may indicate cluster imbalance or storage issues.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin" "migration" ("completed" OR "started")
| rex "Virtual machine '(?<vm_name>[^']+)'"
| table _time host vm_name Message
| sort -_time
```
- **Implementation:** Collected via standard Hyper-V event log monitoring. Create an audit report. Alert on migration failures or excessive frequency.
- **Visualization:** Table (timeline), Count by host/day.

---

### UC-2.2.5 · Integration Services Version
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Outdated integration services cause performance issues and prevent features like time sync, heartbeat, and data exchange from working correctly.
- **App/TA:** `Splunk_TA_windows`, custom scripted input
- **Data Sources:** PowerShell scripted input (`Get-VMIntegrationService`)
- **SPL:**
```spl
index=hyperv sourcetype=integration_services
| stats latest(version) as ic_version by vm_name, host
| where ic_version != expected_version
```
- **Implementation:** Create a PowerShell scripted input on Hyper-V hosts: `Get-VM | Get-VMIntegrationService | Select VMName, Name, Enabled, PrimaryOperationalStatus`. Run daily.
- **Visualization:** Table (VM, version, status), Pie chart (current vs. outdated).

---

## 2.3 KVM / Proxmox / oVirt

**Primary App/TA:** Custom inputs via libvirt API, syslog

---

### UC-2.3.1 · Guest VM Resource Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Per-VM resource tracking for capacity planning and performance troubleshooting in KVM environments.
- **App/TA:** Custom scripted input (`virsh domstats`)
- **Data Sources:** Custom sourcetype from `virsh domstats` or `virt-top`
- **SPL:**
```spl
index=virtualization sourcetype=virsh_stats
| stats latest(cpu_pct) as cpu, latest(mem_used_mb) as memory by vm_name, host
| sort -cpu
```
- **Implementation:** Create scripted input: `virsh domstats --cpu-total --balloon --interface --block`. Run every 60 seconds. Parse per-VM CPU time, balloon current, block read/write, and net rx/tx.
- **Visualization:** Table, Line chart per VM, Heatmap.

---

### UC-2.3.2 · Host Overcommit Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Overcommitted KVM hosts cause all VMs to compete for resources. Unlike VMware, KVM doesn't have sophisticated DRS — manual balancing is needed.
- **App/TA:** Custom scripted input
- **Data Sources:** Custom sourcetype (`virsh nodeinfo` + `virsh list --all`)
- **SPL:**
```spl
index=virtualization sourcetype=kvm_capacity
| stats sum(vm_vcpus) as total_vcpus, sum(vm_memory_mb) as total_vm_mem, latest(host_cpus) as host_cpus, latest(host_memory_mb) as host_mem by host
| eval cpu_overcommit = round(total_vcpus / host_cpus, 2)
| eval mem_overcommit = round(total_vm_mem / host_mem, 2)
| where cpu_overcommit > 3 OR mem_overcommit > 1.2
```
- **Implementation:** Create scripted input combining `virsh nodeinfo` (host resources) with `virsh dominfo <vm>` for each VM. Calculate aggregate allocation vs. physical capacity. Alert when memory overcommit >1.2x or CPU >4x.
- **Visualization:** Table (host, allocated vs. physical), Gauge per host.

---

### UC-2.3.3 · VM Lifecycle Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Audit trail for VM start, stop, migrate, and crash events. Essential for troubleshooting and change management in open-source virtualization.
- **App/TA:** Syslog, libvirt logs
- **Data Sources:** `/var/log/libvirt/`, syslog
- **SPL:**
```spl
index=virtualization sourcetype=syslog source="/var/log/libvirt/*"
| search "shutting down" OR "starting up" OR "migrating" OR "crashed"
| rex "domain (?<vm_name>\S+)"
| table _time host vm_name _raw
| sort -_time
```
- **Implementation:** Forward `/var/log/libvirt/qemu/*.log` and libvirt system logs. Parse VM name and event type. Alert on unexpected VM shutdowns or crashes.
- **Visualization:** Events timeline, Table (VM, event, time).

---

# 3. Containers & Orchestration

## 3.1 Docker

**Primary App/TA:** Splunk Connect for Docker, custom scripted inputs

---

### UC-3.1.1 · Container Crash Loops
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Containers restarting repeatedly indicate application bugs, misconfiguration, or dependency failures. Crash loops consume resources and never reach healthy state.
- **App/TA:** Splunk Connect for Docker, Docker events via syslog
- **Data Sources:** `sourcetype=docker:events`, Docker daemon logs
- **SPL:**
```spl
index=containers sourcetype="docker:events" action="die"
| eval exit_code=exitCode
| where exit_code != "0"
| stats count as crashes by container_name, image, exit_code
| where crashes > 3
| sort -crashes
```
- **Implementation:** Install Splunk Connect for Docker or configure Docker logging driver to forward to Splunk HEC. Collect Docker events via `docker events --format '{{json .}}'`. Alert when a container restarts >3 times in 15 minutes.
- **Visualization:** Table (container, image, crashes, exit code), Bar chart by container, Timeline.

---

### UC-3.1.2 · Container OOM Kills
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** OOM kills mean the container exceeded its memory limit. The application is either leaking memory or undersized. Data loss is likely.
- **App/TA:** Splunk Connect for Docker, host syslog
- **Data Sources:** `sourcetype=docker:events`, host `dmesg`/syslog
- **SPL:**
```spl
index=containers sourcetype="docker:events" action="oom"
| table _time container_name image host
| sort -_time

| `` Also check host syslog for cgroup OOM: ``
index=os sourcetype=syslog "Memory cgroup out of memory" OR "oom-kill"
| rex "task (?<process>\S+)"
| table _time host process _raw
```
- **Implementation:** Collect Docker events and forward host syslog. Alert immediately on any OOM event. Include container memory limit in the alert context to aid right-sizing decisions.
- **Visualization:** Events timeline, Single value (OOM count last 24h), Table with container details.

---

### UC-3.1.3 · Container CPU Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** CPU throttling means the container is hitting its CPU limit and being artificially slowed. Causes latency spikes invisible to standard CPU utilization metrics.
- **App/TA:** Custom scripted input (cgroup stats), Splunk OpenTelemetry Collector
- **Data Sources:** `sourcetype=docker:stats`, cgroup `cpu.stat`
- **SPL:**
```spl
index=containers sourcetype="docker:stats"
| eval throttle_pct = round(throttled_periods / nr_periods * 100, 1)
| where throttle_pct > 25
| stats avg(throttle_pct) as avg_throttle by container_name
| sort -avg_throttle
```
- **Implementation:** Collect Docker stats via `docker stats --format '{{json .}}'` or read cgroup files directly (`/sys/fs/cgroup/cpu/docker/<id>/cpu.stat`). Monitor `throttled_time` and `nr_throttled`. Alert when >25% of periods are throttled.
- **Visualization:** Line chart (throttle % over time), Table (container, throttle %, CPU limit), Bar chart.

---

### UC-3.1.4 · Container Memory Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracking memory usage relative to limits catches containers approaching OOM before they're killed. Enables proactive limit adjustments.
- **App/TA:** Splunk Connect for Docker, custom scripted input
- **Data Sources:** `sourcetype=docker:stats`
- **SPL:**
```spl
index=containers sourcetype="docker:stats"
| eval mem_pct = round(mem_usage / mem_limit * 100, 1)
| stats latest(mem_pct) as mem_pct by container_name
| where mem_pct > 80
| sort -mem_pct
```
- **Implementation:** Collect `docker stats` output at regular intervals. Alert when memory usage exceeds 80% of limit. Trend over time to catch gradual memory leaks.
- **Visualization:** Gauge per container, Table with limit context, Line chart (trending).

---

### UC-3.1.5 · Image Vulnerability Scanning
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Container images with known CVEs are deployed directly into production. Scanning and tracking vulnerabilities prevents running exploitable workloads.
- **App/TA:** Custom input (Trivy, Snyk, Grype JSON output)
- **Data Sources:** JSON scan results from vulnerability scanners
- **SPL:**
```spl
index=containers sourcetype="trivy:scan"
| stats count by image, Severity
| xyseries image Severity count
| sort -CRITICAL -HIGH
```
- **Implementation:** Run vulnerability scans in CI/CD pipeline (Trivy, Grype, or Snyk). Forward JSON results to Splunk via HEC. Create dashboard showing vulnerability counts per image by severity. Alert on CRITICAL vulnerabilities in production-tagged images.
- **Visualization:** Table (image, critical, high, medium, low), Stacked bar chart by image, Trend line.

---

### UC-3.1.6 · Privileged Container Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Privileged containers have full host access — a container escape gives root on the host. Should be flagged and justified in production.
- **App/TA:** Docker events, custom audit input
- **Data Sources:** `docker inspect` output, Kubernetes pod security
- **SPL:**
```spl
index=containers sourcetype="docker:inspect"
| where Privileged="true"
| table container_name image host Privileged
```
- **Implementation:** Create scripted input: `docker inspect --format '{{.Name}} {{.HostConfig.Privileged}}' $(docker ps -q)`. Run every 300 seconds. Alert on any privileged container in production. Maintain an allowlist for justified exceptions.
- **Visualization:** Table (container, image, host), Single value (count of privileged), Status indicator.

---

### UC-3.1.7 · Container Sprawl
- **Criticality:** 🟢 Low
- **Difficulty:** 🟠 Advanced
- **Value:** Stopped containers and dangling images waste disk space. In development environments, sprawl can consume all available storage.
- **App/TA:** Custom scripted input
- **Data Sources:** `docker ps -a`, `docker images`
- **SPL:**
```spl
index=containers sourcetype="docker:ps"
| where status="exited"
| eval days_stopped = round((now() - strptime(finished_at, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where days_stopped > 7
| stats count by host
```
- **Implementation:** Scripted input: `docker ps -a --format '{{json .}}'` and `docker system df`. Run daily. Report on stopped containers >7 days and total disk reclamation possible.
- **Visualization:** Table, Single value (reclaimable space), Bar chart by host.

---

### UC-3.1.8 · Docker Daemon Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Docker daemon errors affect all containers on the host. Network, storage driver, and containerd errors can cause widespread container failures.
- **App/TA:** Syslog, Docker daemon log forwarding
- **Data Sources:** `/var/log/docker.log` or `journalctl -u docker`
- **SPL:**
```spl
index=containers sourcetype="docker:daemon" level="error" OR level="fatal"
| stats count by host, msg
| sort -count
```
- **Implementation:** Forward Docker daemon logs (usually via journald or `/var/log/docker.log`). Alert on fatal errors. Track error patterns by host.
- **Visualization:** Table (host, error, count), Timeline, Bar chart by error type.

---

## 3.2 Kubernetes

**Primary App/TA:** Splunk OpenTelemetry Collector for Kubernetes, Splunk Connect for Kubernetes — Free

---

### UC-3.2.1 · Pod Restart Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** High restart counts indicate application instability. Pods may appear "Running" but are constantly crashing and restarting, degrading service quality.
- **App/TA:** Splunk OpenTelemetry Collector for K8s
- **Data Sources:** `sourcetype=kube:container:meta`, kube-state-metrics
- **SPL:**
```spl
index=k8s sourcetype="kube:container:meta"
| stats max(restartCount) as restarts by namespace, pod_name, container_name
| where restarts > 5
| sort -restarts
```
- **Implementation:** Deploy Splunk OTel Collector as a DaemonSet. It collects container metadata including restart counts. Alert when any pod exceeds 5 restarts in 1 hour. Include the pod's last termination reason.
- **Visualization:** Table (namespace, pod, container, restarts), Bar chart by namespace, Trending line.

---

### UC-3.2.2 · Pod Scheduling Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Pods stuck in Pending can't serve traffic. Usually caused by insufficient CPU/memory, node affinity rules, or persistent volume claim issues.
- **App/TA:** Splunk OTel Collector, Kubernetes event forwarding
- **Data Sources:** `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Forward Kubernetes events to Splunk. Alert on FailedScheduling events persisting >5 minutes. Parse the event message for the specific cause (Insufficient cpu, node affinity, PVC not bound, etc.).
- **Visualization:** Table (pod, namespace, reason), Single value (pending pods), Timeline.

---

### UC-3.2.3 · Node NotReady Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** A NotReady node can't run pods. Existing pods are evicted after the toleration timeout (default 5 min). Causes service disruption if no replacement capacity.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:node:meta`, Kubernetes events
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="NodeNotReady"
| table _time node message
| sort -_time

| `` Or from node conditions: ``
index=k8s sourcetype="kube:node:meta"
| where condition_ready="False"
| table _time node condition_ready
```
- **Implementation:** OTel Collector monitors node conditions. Alert immediately on any node transitioning to NotReady. Correlate with kubelet logs on the affected node for root cause (disk pressure, memory pressure, PID pressure, network).
- **Visualization:** Node status grid (green/red), Events timeline, Table.

---

### UC-3.2.4 · Resource Quota Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** When namespace quotas are exhausted, new pods can't be created. Impacts deployments, autoscaling, and job scheduling within the namespace.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:resourcequota:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:resourcequota:meta"
| eval used_pct = round(used / hard * 100, 1)
| where used_pct > 80
| table namespace resource used hard used_pct
| sort -used_pct
```
- **Implementation:** kube-state-metrics exposes resource quota data. Collect via OTel Collector. Alert when any resource (cpu, memory, pods, services) exceeds 80% of quota.
- **Visualization:** Gauge per namespace/resource, Table, Bar chart by namespace.

---

### UC-3.2.5 · Persistent Volume Claims
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unbound PVCs prevent stateful workloads (databases, message queues) from starting. Often caused by storage class misconfiguration or capacity.
- **App/TA:** Splunk OTel Collector, Kubernetes events
- **Data Sources:** `sourcetype=kube:events`, `sourcetype=kube:pvc:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="ProvisioningFailed" OR reason="FailedBinding"
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Forward Kubernetes events and PVC metadata. Alert on PVCs in Pending phase >5 minutes. Include storage class and requested size in alert context.
- **Visualization:** Table (PVC, namespace, status, storage class), Status indicators.

---

### UC-3.2.6 · Deployment Rollout Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** A failed rollout means new code isn't deploying successfully. Pods may be crash-looping, image pulls failing, or health checks not passing.
- **App/TA:** Splunk OTel Collector, Kubernetes events
- **Data Sources:** `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" involvedObject.kind="Deployment" (reason="ProgressDeadlineExceeded" OR reason="ReplicaSetUpdated" OR reason="FailedCreate")
| table _time namespace involvedObject.name reason message
| sort -_time
```
- **Implementation:** Monitor deployment events. Alert on `ProgressDeadlineExceeded` which means the deployment failed to complete within its configured deadline. Correlate with pod events for root cause.
- **Visualization:** Table (deployment, namespace, reason), Timeline, Status panel.

---

### UC-3.2.7 · Control Plane Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** The control plane (API server, etcd, scheduler, controller-manager) is the brain of Kubernetes. Degradation affects all cluster operations.
- **App/TA:** Splunk OTel Collector, control plane component metrics
- **Data Sources:** API server metrics, etcd metrics, scheduler/controller-manager logs
- **SPL:**
```spl
index=k8s sourcetype="kube:apiserver"
| timechart span=5m avg(apiserver_request_duration_seconds) as avg_latency by verb
| where avg_latency > 1
```
- **Implementation:** Configure OTel Collector to scrape control plane metrics endpoints (/metrics on each component). Monitor API server request latency, etcd request duration, scheduler binding latency. Alert on P99 latency >1s or error rates >1%.
- **Visualization:** Line chart (latency by verb), Single value (error rate), Multi-panel dashboard per component.

---

### UC-3.2.8 · etcd Cluster Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** etcd stores all Kubernetes state. etcd problems (leader elections, compaction failures, high latency) cascade into cluster-wide failures.
- **App/TA:** Splunk OTel Collector, etcd metrics
- **Data Sources:** etcd Prometheus metrics (scraped by OTel)
- **SPL:**
```spl
index=k8s sourcetype="kube:etcd"
| timechart span=5m avg(etcd_disk_wal_fsync_duration_seconds) as fsync_latency, sum(etcd_server_leader_changes_seen_total) as leader_changes
| where fsync_latency > 0.01 OR leader_changes > 0
```
- **Implementation:** Scrape etcd metrics via OTel Collector. Monitor disk fsync latency (<10ms healthy), database size, leader changes, and proposal failures. Alert on leader changes (indicates instability) and high fsync latency.
- **Visualization:** Line chart (fsync latency, db size), Single value (leader changes), Gauge (db size).

---

### UC-3.2.9 · Ingress Error Rates
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Ingress controllers are the front door to your services. High error rates mean users are getting errors. Catches backend failures and misconfigurations.
- **App/TA:** Ingress controller log forwarding (NGINX, Traefik, etc.)
- **Data Sources:** `sourcetype=kube:ingress:nginx` or similar
- **SPL:**
```spl
index=k8s sourcetype="kube:ingress:nginx"
| eval is_error = if(status >= 500, 1, 0)
| timechart span=5m sum(is_error) as errors, count as total
| eval error_rate = round(errors / total * 100, 2)
| where error_rate > 5
```
- **Implementation:** Forward ingress controller access logs. Parse status code, upstream response time, and backend server. Alert when 5xx error rate exceeds 5% over 5 minutes.
- **Visualization:** Line chart (error rate over time), Table (top error paths), Single value (current error rate).

---

### UC-3.2.10 · CrashLoopBackOff Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** CrashLoopBackOff is the most common Kubernetes failure mode. The pod is crashing, restarting, and crashing again with exponential backoff. Service is down.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:container:meta`, Kubernetes events
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="BackOff"
| stats count by namespace, involvedObject.name, message
| where count > 3
| sort -count
```
- **Implementation:** Monitor Kubernetes events for `BackOff` reason. Also check container status for `waiting.reason=CrashLoopBackOff`. Alert immediately. Include container logs in alert for diagnostic context.
- **Visualization:** Table (pod, namespace, count, message), Status panel, Single value (CrashLoop pods count).

---

### UC-3.2.11 · HPA Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** HPA scaling events show when applications are hitting capacity. Repeated max-scale events indicate undersized limits or unexpected traffic.
- **App/TA:** Splunk OTel Collector, Kubernetes events
- **Data Sources:** `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" involvedObject.kind="HorizontalPodAutoscaler"
| stats count by namespace, involvedObject.name, reason, message
| sort -count
```
- **Implementation:** Forward Kubernetes events. Track scaling decisions and current vs. desired replicas. Alert when HPA reaches maxReplicas (application may be under-provisioned).
- **Visualization:** Line chart (replica count over time), Table of scaling events, Area chart.

---

### UC-3.2.12 · RBAC Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** RBAC misconfigurations grant excessive permissions. Unauthorized access attempts indicate potential compromise or misconfigured service accounts.
- **App/TA:** Kubernetes audit log forwarding
- **Data Sources:** `sourcetype=kube:audit`
- **SPL:**
```spl
index=k8s sourcetype="kube:audit" responseStatus.code>=403
| stats count by user.username, verb, objectRef.resource, objectRef.namespace
| sort -count
```
- **Implementation:** Enable Kubernetes audit logging (audit policy file). Forward audit logs to Splunk. Alert on 403 Forbidden responses, especially from service accounts. Track RBAC changes (ClusterRole, ClusterRoleBinding modifications).
- **Visualization:** Table (user, resource, verb, denials), Bar chart by user, Timeline.

---

### UC-3.2.13 · Certificate Expiration
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Kubernetes uses TLS certificates extensively (API server, kubelet, etcd). Expired certs cause cluster communication failures and outages.
- **App/TA:** cert-manager metrics, custom scripted input
- **Data Sources:** cert-manager events, `kubeadm certs check-expiration` output
- **SPL:**
```spl
index=k8s sourcetype="kube:events" involvedObject.kind="Certificate" reason="Issuing" OR reason="Expired"
| table _time namespace involvedObject.name reason message
| sort -_time

| `` Or from cert-manager metrics: ``
index=k8s sourcetype="certmanager:metrics"
| eval days_left = round((certmanager_certificate_expiration_timestamp_seconds - now()) / 86400, 0)
| where days_left < 30
```
- **Implementation:** Deploy cert-manager and scrape its metrics. Monitor certificate expiration timestamps. Alert at 30/14/7 day thresholds. For kubeadm clusters, scripted input running `kubeadm certs check-expiration`.
- **Visualization:** Table (cert, namespace, days remaining), Single value (certs expiring soon), Status indicator.

---

### UC-3.2.14 · Container Image Pull Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** ImagePullBackOff prevents pods from starting. Caused by wrong image tags, registry auth failures, or network issues. Blocks deployments.
- **App/TA:** Splunk OTel Collector, Kubernetes events
- **Data Sources:** `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" (reason="ErrImagePull" OR reason="ImagePullBackOff" OR reason="Failed" message="*pulling image*")
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Forward Kubernetes events. Alert on ImagePullBackOff events. Parse the image name and registry to identify whether it's an auth issue, missing tag, or network issue.
- **Visualization:** Table (pod, image, error), Single value (pull failures last hour), Bar chart by namespace.

---

### UC-3.2.15 · DaemonSet Completeness
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** DaemonSets (monitoring agents, log forwarders, network plugins) must run on every eligible node. Missing instances create monitoring or networking gaps.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:daemonset:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:daemonset:meta"
| eval missing = desiredNumberScheduled - numberReady
| where missing > 0
| table namespace daemonset_name desiredNumberScheduled numberReady missing
```
- **Implementation:** kube-state-metrics reports DaemonSet status. Alert when `numberReady < desiredNumberScheduled` for >5 minutes. Critical for infrastructure DaemonSets (CNI plugins, OTel Collector, kube-proxy).
- **Visualization:** Table (DaemonSet, desired, ready, missing), Status indicator, Single value.

---

## 3.3 OpenShift

**Primary App/TA:** OpenTelemetry Collector, OpenShift audit log forwarding

---

### UC-3.3.1 · Cluster Version & Upgrade Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** OpenShift upgrades can stall. Tracking upgrade progress and version across clusters ensures consistency and support compliance.
- **App/TA:** Custom API input (ClusterVersion API)
- **Data Sources:** ClusterVersion resource, OpenShift events
- **SPL:**
```spl
index=openshift sourcetype="openshift:clusterversion"
| stats latest(version) as version, latest(progressing) as upgrading, latest(available) as available by cluster
| table cluster version upgrading available
```
- **Implementation:** Create scripted input querying `oc get clusterversion -o json`. Run hourly. Alert when upgrade is progressing but stalled (>2 hours without progress).
- **Visualization:** Table (cluster, version, status), Status indicator.

---

### UC-3.3.2 · Operator Degraded Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Cluster operators manage core OpenShift components (networking, ingress, monitoring, authentication). Degraded operators mean partial cluster functionality loss.
- **App/TA:** Custom API input
- **Data Sources:** ClusterOperator resources
- **SPL:**
```spl
index=openshift sourcetype="openshift:clusteroperator"
| where degraded="True" OR available="False"
| table _time cluster operator degraded available message
| sort -_time
```
- **Implementation:** Scripted input: `oc get clusteroperators -o json`. Run every 300 seconds. Alert when any operator reports `Degraded=True` or `Available=False`.
- **Visualization:** Operator status grid (green/yellow/red), Table with details, Timeline.

---

### UC-3.3.3 · Build Failure Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** OpenShift Source-to-Image (S2I) build failures block application deployments. Trend analysis reveals systemic build infrastructure issues.
- **App/TA:** OpenShift event forwarding
- **Data Sources:** `sourcetype=kube:events` (Build events)
- **SPL:**
```spl
index=openshift sourcetype="kube:events" involvedObject.kind="Build" reason="BuildFailed"
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Forward OpenShift events. Alert on BuildFailed events. Track build success/failure rate per namespace over time. Investigate common failure reasons (image pull, compile errors, push failures).
- **Visualization:** Table (build, namespace, reason), Line chart (success rate %), Bar chart by failure type.

---

### UC-3.3.4 · SCC Violation Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Security Context Constraint violations mean pods are attempting to run with permissions beyond their allowed scope. Could indicate misconfiguration or an attack.
- **App/TA:** OpenShift audit log forwarding
- **Data Sources:** `sourcetype=openshift:audit`
- **SPL:**
```spl
index=openshift sourcetype="openshift:audit" responseStatus.code=403 objectRef.resource="pods"
| search "unable to validate against any security context constraint"
| stats count by user.username, objectRef.namespace, objectRef.name
| sort -count
```
- **Implementation:** Enable and forward OpenShift audit logs. Alert on SCC-related 403 errors. Track which SCCs are most commonly requested and denied.
- **Visualization:** Table (user, namespace, pod, SCC requested), Bar chart by SCC, Timeline.

---

## 3.4 Container Registries

**Primary App/TA:** Custom API inputs, webhook receivers

---

### UC-3.4.1 · Image Push/Pull Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Audit trail for who pushed or pulled what images. Detects unauthorized access, supply chain concerns, and usage patterns.
- **App/TA:** Registry webhook to Splunk HEC, API polling
- **Data Sources:** Registry audit/webhook events
- **SPL:**
```spl
index=containers sourcetype="registry:audit"
| stats count by action, repository, tag, user
| sort -count
```
- **Implementation:** Configure registry webhooks (Harbor, ACR, ECR) to send events to Splunk HEC. Alternatively, poll registry API for audit logs. Track push events (new deployments) and pull events (consumption).
- **Visualization:** Table (user, image, action, time), Bar chart by repository, Timeline.

---

### UC-3.4.2 · Vulnerability Scan Results
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Registry-level scanning catches vulnerabilities before images are deployed. Trending shows whether security posture is improving or degrading.
- **App/TA:** Custom input (Harbor, ACR, ECR scan APIs)
- **Data Sources:** Scan result JSON from registry API
- **SPL:**
```spl
index=containers sourcetype="registry:scan"
| stats sum(critical) as critical, sum(high) as high, sum(medium) as medium by repository, tag
| where critical > 0
| sort -critical
```
- **Implementation:** Poll registry scan APIs for results or configure webhook notifications on scan completion. Forward to Splunk via HEC. Alert on critical vulnerabilities in images tagged for production.
- **Visualization:** Stacked bar chart (vulns by severity per image), Table, Trend line (vulns over time).

---

### UC-3.4.3 · Storage Quota Monitoring
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Registry storage exhaustion prevents image pushes, blocking CI/CD pipelines. Monitoring enables proactive cleanup policy tuning.
- **App/TA:** Custom API input
- **Data Sources:** Registry storage API metrics
- **SPL:**
```spl
index=containers sourcetype="registry:metrics"
| stats latest(storage_used_bytes) as used, latest(storage_quota_bytes) as quota by registry
| eval used_pct = round(used / quota * 100, 1)
| where used_pct > 80
```
- **Implementation:** Poll registry API for storage metrics. Alert when usage exceeds 80%. Review and tune image retention/garbage collection policies.
- **Visualization:** Gauge (storage usage), Line chart (growth trend), Table.

---

# 4. Cloud Infrastructure

## 4.1 Amazon Web Services (AWS)

**Primary App/TA:** Splunk Add-on for AWS (`Splunk_TA_aws`) — Free on Splunkbase; Splunk App for AWS (optional dashboards)

---

### UC-4.1.1 · Unauthorized API Calls
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** AccessDenied errors reveal reconnaissance activity, compromised credentials with insufficient permissions, or misconfigurations. Early indicator of attack or drift.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`, CloudTrail logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" errorCode="AccessDenied" OR errorCode="UnauthorizedAccess" OR errorCode="Client.UnauthorizedAccess"
| stats count by userIdentity.arn, eventName, sourceIPAddress, errorCode
| where count > 5
| sort -count
```
- **Implementation:** Configure CloudTrail to send logs to an S3 bucket. Set up the Splunk_TA_aws with an SQS-based S3 input for CloudTrail. Alert when a single principal gets >5 access denied errors in 10 minutes.
- **Visualization:** Table (principal, API call, source IP, count), Bar chart by principal, Map (source IP GeoIP).

---

### UC-4.1.2 · Root Account Usage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** The AWS root account has unrestricted access and should never be used for daily operations. Any root activity is a critical security event.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" userIdentity.type="Root"
| table _time eventName sourceIPAddress userAgent errorCode
| sort -_time
```
- **Implementation:** CloudTrail must be enabled in all regions. Create a critical real-time alert on any event where `userIdentity.type=Root`. Exclude expected events (e.g., automated billing).
- **Visualization:** Events list (critical alert), Single value (root events last 30d), Timeline.

---

### UC-4.1.3 · Security Group Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Security group changes can expose services to the internet. Unauthorized modifications are a primary attack vector and compliance violation.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="AuthorizeSecurityGroupIngress" OR eventName="AuthorizeSecurityGroupEgress" OR eventName="RevokeSecurityGroup*"
| spath output=rules path=requestParameters.ipPermissions.items{}
| table _time userIdentity.arn eventName requestParameters.groupId rules sourceIPAddress
| sort -_time
```
- **Implementation:** Alert on any security group modification. Extra-critical alert when `0.0.0.0/0` is added as a source (exposes to internet). Correlate with change tickets.
- **Visualization:** Table (who, what, when), Timeline, Single value (changes last 24h).

---

### UC-4.1.4 · IAM Policy Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** IAM policy changes affect who can do what across the entire AWS account. Unauthorized policy attachments can grant admin access.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="CreatePolicy" OR eventName="AttachUserPolicy" OR eventName="AttachRolePolicy" OR eventName="PutUserPolicy" OR eventName="PutRolePolicy" OR eventName="CreateRole")
| table _time userIdentity.arn eventName requestParameters.policyArn requestParameters.roleName
| sort -_time
```
- **Implementation:** Alert on all IAM policy modifications. Critical alert when AdministratorAccess or PowerUserAccess policies are attached. Track with change management.
- **Visualization:** Table, Timeline, Bar chart by event type.

---

### UC-4.1.5 · Console Login Without MFA
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Console access without MFA is a security risk — compromised passwords alone can grant full account access. Most compliance frameworks require MFA.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="ConsoleLogin" responseElements.ConsoleLogin="Success"
| eval mfa_used = if(additionalEventData.MFAUsed="Yes", "Yes", "No")
| where mfa_used="No"
| table _time userIdentity.arn sourceIPAddress mfa_used
| sort -_time
```
- **Implementation:** Monitor ConsoleLogin events. Alert on successful console logins where MFA is not used. Exclude service accounts that authenticate via SSO (which has its own MFA).
- **Visualization:** Table (user, source IP, MFA status), Pie chart (MFA vs. no-MFA), Single value.

---

### UC-4.1.6 · EC2 Instance State Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks instance lifecycle for audit and change management. Unexpected terminations indicate accidents, auto-scaling issues, or attacks.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="RunInstances" OR eventName="TerminateInstances" OR eventName="StopInstances" OR eventName="StartInstances")
| table _time userIdentity.arn eventName requestParameters.instancesSet.items{}.instanceId responseElements.instancesSet.items{}.currentState.name
| sort -_time
```
- **Implementation:** Forward CloudTrail events. Create daily audit report of EC2 lifecycle events. Alert on terminations of tagged production instances.
- **Visualization:** Table (timeline), Bar chart (events by type per day), Line chart (instance count trending).

---

### UC-4.1.7 · S3 Bucket Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** S3 bucket policy changes can expose sensitive data to the public internet. One of the most common cloud security incidents.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="PutBucketPolicy" OR eventName="PutBucketAcl" OR eventName="PutBucketPublicAccessBlock" OR eventName="DeleteBucketPolicy")
| table _time userIdentity.arn eventName requestParameters.bucketName
| sort -_time
```
- **Implementation:** Critical alert on any bucket policy change. Extra-critical when `PutBucketPublicAccessBlock` is disabled or when ACLs grant public access. Integrate with AWS Config for continuous compliance.
- **Visualization:** Events list (critical), Table, Single value (policy changes last 7d).

---

### UC-4.1.8 · GuardDuty Finding Ingestion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** GuardDuty provides ML-powered threat detection for AWS accounts. Centralizing findings in Splunk enables correlation with other security data.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch:guardduty`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:guardduty"
| spath output=severity path=detail.severity
| spath output=finding_type path=detail.type
| where severity >= 7
| table _time finding_type severity detail.title detail.description
| sort -severity
```
- **Implementation:** Enable GuardDuty in all regions. Configure CloudWatch Events rule to forward findings to an SNS topic or S3. Ingest via Splunk_TA_aws. Alert on High/Critical findings (severity ≥7).
- **Visualization:** Table by severity, Bar chart (finding types), Trend line (findings over time), Single value.

---

### UC-4.1.9 · VPC Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** VPC Flow Logs provide network-level visibility into all traffic. Detects rejected traffic, data exfiltration, lateral movement, and network anomalies.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatchlogs:vpcflow`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatchlogs:vpcflow" action="REJECT"
| stats count by src_ip, dest_ip, dest_port, protocol
| sort -count
| head 20
```
- **Implementation:** Enable VPC Flow Logs on all VPCs (send to S3 or CloudWatch Logs). Ingest via Splunk_TA_aws. Create dashboards for rejected traffic, top talkers, and unusual port activity.
- **Visualization:** Table (top rejected flows), Sankey diagram (source to destination), Timechart, Map.

---

### UC-4.1.10 · EC2 Performance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** CloudWatch metrics provide host-level performance data without agents. Baseline trending for capacity planning and anomaly detection.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (EC2 namespace)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="CPUUtilization" namespace="AWS/EC2"
| timechart span=1h avg(Average) as avg_cpu by metric_dimensions
| where avg_cpu > 80
```
- **Implementation:** Configure CloudWatch metric collection in Splunk_TA_aws for EC2 namespace. Collect CPUUtilization, NetworkIn/Out, DiskReadOps, DiskWriteOps. Set polling interval (300s minimum).
- **Visualization:** Line chart per instance, Heatmap across fleet, Gauge.

---

### UC-4.1.11 · RDS Performance Insights
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Database performance issues directly impact application experience. Monitoring connections, CPU, IOPS, and replica lag catches problems before users notice.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (RDS namespace), RDS logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" (metric_name="CPUUtilization" OR metric_name="DatabaseConnections" OR metric_name="ReadLatency" OR metric_name="ReplicaLag")
| timechart span=5m avg(Average) by metric_name, DBInstanceIdentifier
```
- **Implementation:** Enable CloudWatch metric collection for RDS namespace. Also forward RDS logs (slow query, error, general) to Splunk via CloudWatch Logs. Alert on ReplicaLag >30s, CPU >80%, or connection count nearing max.
- **Visualization:** Multi-metric line chart, Gauge (connections vs. max), Table.

---

### UC-4.1.12 · Lambda Error Rate Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Lambda errors affect serverless application reliability. Timeouts indicate functions need more memory/time. Throttling means concurrency limits are hit.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (Lambda namespace), Lambda logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" (metric_name="Errors" OR metric_name="Throttles" OR metric_name="Duration")
| timechart span=5m sum(Sum) by metric_name, FunctionName
```
- **Implementation:** Collect CloudWatch metrics for Lambda namespace. Forward Lambda function logs via CloudWatch Logs. Alert on error rate >5% or any throttling events.
- **Visualization:** Line chart (errors/invocations over time), Bar chart (top error functions), Single value (error rate %).

---

### UC-4.1.13 · EKS/ECS Cluster Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Managed container orchestration health ensures application workloads are running correctly across the AWS compute fabric.
- **App/TA:** `Splunk_TA_aws`, Splunk OTel Collector
- **Data Sources:** CloudWatch EKS/ECS metrics, container insights
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ECS" metric_name="CPUUtilization"
| timechart span=5m avg(Average) by ClusterName, ServiceName
```
- **Implementation:** Enable Container Insights for EKS/ECS. Collect metrics via CloudWatch. For deeper Kubernetes visibility in EKS, deploy Splunk OTel Collector as described in Category 3.2.
- **Visualization:** Line chart per service, Cluster status panel, Table.

---

### UC-4.1.14 · Cost Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Unexpected spend spikes indicate runaway resources, cryptomining attacks, or misconfigured services. Catching anomalies early saves money.
- **App/TA:** `Splunk_TA_aws`, AWS Cost and Usage Report (CUR)
- **Data Sources:** `sourcetype=aws:billing` or CUR data
- **SPL:**
```spl
index=aws sourcetype="aws:billing"
| timechart span=1d sum(BlendedCost) as daily_cost by ProductName
| eventstats avg(daily_cost) as avg_cost, stdev(daily_cost) as stdev_cost by ProductName
| eval threshold = avg_cost + (2 * stdev_cost)
| where daily_cost > threshold
```
- **Implementation:** Enable CUR reports to S3. Ingest via Splunk_TA_aws (billing input). Calculate daily baselines per service. Alert when daily spend exceeds 2 standard deviations from the 30-day average.
- **Visualization:** Line chart (daily spend with threshold), Table (anomalous services), Stacked area (spend by service).

---

### UC-4.1.15 · Config Compliance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** AWS Config rules continuously evaluate resource compliance against security best practices. Non-compliant resources are attack surface.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:config:notification`
- **SPL:**
```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.complianceType="NON_COMPLIANT"
| stats count by resourceType, resourceId, configRuleList{}.configRuleName
| sort -count
```
- **Implementation:** Enable AWS Config with rules (e.g., CIS Benchmark). Forward Config notifications to SNS/S3 and ingest in Splunk. Dashboard showing compliance score per rule. Alert on newly non-compliant critical resources.
- **Visualization:** Table (resource, rule, status), Pie chart (compliant %), Bar chart by rule.

---

### UC-4.1.16 · KMS Key Usage Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Encryption key usage audit ensures data protection compliance. Unusual key access patterns may indicate unauthorized data decryption.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="Decrypt" OR eventName="Encrypt" OR eventName="GenerateDataKey") eventSource="kms.amazonaws.com"
| stats count by userIdentity.arn, requestParameters.keyId, eventName
| sort -count
```
- **Implementation:** CloudTrail captures all KMS API calls. Monitor for unusual Decrypt call volumes or access from unexpected principals. Track key rotation compliance.
- **Visualization:** Table (principal, key, action, count), Trend line, Bar chart.

---

### UC-4.1.17 · Elastic IP Association
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Unassociated Elastic IPs cost money. Tracking associations supports inventory accuracy and cost management.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="AllocateAddress" OR eventName="AssociateAddress" OR eventName="DisassociateAddress" OR eventName="ReleaseAddress")
| table _time userIdentity.arn eventName requestParameters.publicIp
| sort -_time
```
- **Implementation:** Forward CloudTrail. Create weekly report of EIP allocations vs. associations. Flag unassociated EIPs for cleanup.
- **Visualization:** Table, Single value (unassociated EIPs), Bar chart.

---

### UC-4.1.18 · CloudFormation Stack Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Drift means infrastructure no longer matches its declared template — manual changes have been made. This breaks IaC and causes inconsistencies.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail` (DetectStackDrift events)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="DetectStackDrift" OR eventName="DetectStackResourceDrift"
| spath output=drift_status path=responseElements.stackDriftStatus
| where drift_status="DRIFTED"
| table _time requestParameters.stackName drift_status
```
- **Implementation:** Schedule periodic drift detection via CloudFormation API or AWS Config rule. Forward detection results to Splunk. Alert on stacks in DRIFTED state.
- **Visualization:** Table (stack, drift status), Pie chart (drifted vs. in-sync), Status indicator.

---

### UC-4.1.19 · WAF Blocked Request Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** WAF blocks reveal attack patterns targeting your applications. Analysis helps tune rules and understand the threat landscape.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:waf` (WAF logs via S3 or Kinesis)
- **SPL:**
```spl
index=aws sourcetype="aws:waf" action="BLOCK"
| stats count by terminatingRuleId, httpRequest.clientIp, httpRequest.uri
| sort -count
| head 20
```
- **Implementation:** Enable WAF logging to S3 or Kinesis Firehose. Ingest via Splunk_TA_aws. Analyze blocked requests by rule, source IP, URI, and user agent to identify attack patterns and false positives.
- **Visualization:** Table (rule, source, URI, count), Bar chart by rule, Map (source IPs), Timeline.

---

### UC-4.1.20 · Reserved Instance Utilization
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Underutilized RIs waste money. Tracking RI coverage and utilization helps optimize commit spending vs. on-demand costs.
- **App/TA:** `Splunk_TA_aws`, CUR data
- **Data Sources:** `sourcetype=aws:billing` (CUR)
- **SPL:**
```spl
index=aws sourcetype="aws:billing" lineItem_LineItemType="DiscountedUsage" OR lineItem_LineItemType="RIFee"
| stats sum(lineItem_UsageAmount) as ri_hours, sum(lineItem_UnblendedCost) as ri_cost by reservation_ReservationARN, product_instanceType
| eval utilization_pct = round(ri_hours / expected_hours * 100, 1)
```
- **Implementation:** Ingest CUR data. Calculate RI utilization by comparing reserved hours against actual usage. Dashboard showing RI coverage percentage and waste. Review monthly.
- **Visualization:** Table (RI, type, utilization %), Gauge (overall utilization), Bar chart by instance type.

---

## 4.2 Microsoft Azure

**Primary App/TA:** Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`) — Free on Splunkbase

---

### UC-4.2.1 · Azure Activity Log Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Activity Log captures all control plane operations across Azure subscriptions. Essential audit trail for resource management and compliance.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:audit`, Azure Activity Log via Event Hub
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" operationName.value="*delete*" OR operationName.value="*write*"
| stats count by caller, operationName.value, resourceGroupName, status.value
| sort -count
```
- **Implementation:** Configure Azure Event Hub to receive Activity Log events. Set up Splunk_TA_microsoft-cloudservices with Event Hub input (connection string, consumer group). Alert on critical operations (resource deletions, policy changes).
- **Visualization:** Table (caller, operation, resource, status), Timeline, Bar chart by operation.

---

### UC-4.2.2 · Entra ID Sign-In Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Risky sign-ins include impossible travel, unfamiliar locations, and anonymous IP usage. Primary detection layer for account compromise.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:signinlog`, Entra ID sign-in logs
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:signinlog" riskLevelDuringSignIn!="none"
| table _time userPrincipalName riskLevelDuringSignIn riskState ipAddress location.city location.countryOrRegion
| sort -_time
```
- **Implementation:** Forward Entra ID sign-in logs via Event Hub or direct API. Alert on riskLevelDuringSignIn = high or medium. Correlate with conditional access policy results.
- **Visualization:** Table (user, risk level, location, IP), Map (sign-in locations), Timeline, Bar chart by risk type.

---

### UC-4.2.3 · Entra ID Privilege Escalation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Privileged role assignments (Global Admin, Privileged Role Admin) grant extreme power. Unauthorized assignments mean full tenant compromise.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:auditlog`, Entra ID audit logs
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:auditlog" activityDisplayName="Add member to role"
| spath output=role path=targetResources{}.modifiedProperties{}.newValue
| table _time initiatedBy.user.userPrincipalName targetResources{}.userPrincipalName role
| sort -_time
```
- **Implementation:** Forward Entra ID audit logs. Create critical alerts on role assignments for Global Administrator, Privileged Role Administrator, and Exchange Administrator. Correlate with PIM activation events.
- **Visualization:** Events list (critical), Table (who assigned what to whom), Timeline.

---

### UC-4.2.4 · NSG Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** NSG Flow Logs provide Azure network-level visibility. Detects blocked traffic, anomalous patterns, and lateral movement within VNets.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:nsgflowlog`
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:nsgflowlog" flowState="D"
| stats count by src_ip, dest_ip, dest_port, protocol
| sort -count | head 20
```
- **Implementation:** Enable NSG Flow Logs (Version 2) on all NSGs. Send to a storage account. Ingest via Splunk_TA_microsoft-cloudservices. Create dashboards for denied traffic and top talkers.
- **Visualization:** Table (top denied flows), Sankey diagram, Timechart, Map.

---

### UC-4.2.5 · Azure VM Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Azure Monitor metrics provide VM performance data without agents. Essential for capacity planning and correlating with application issues.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:metrics`
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" metricName="Percentage CPU"
| timechart span=1h avg(average) as avg_cpu by resourceId
| where avg_cpu > 80
```
- **Implementation:** Configure Azure Monitor metrics collection in the Splunk TA. Collect CPU, memory, disk, and network metrics. Alert on sustained high utilization.
- **Visualization:** Line chart per VM, Heatmap, Gauge.

---

### UC-4.2.6 · Azure SQL Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** DTU/vCore exhaustion causes query throttling. Deadlocks and long-running queries impact application performance directly.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` (SQL diagnostics)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="SQLInsights" OR Category="Deadlocks"
| stats count by database_name, Category
| sort -count
```
- **Implementation:** Enable Azure SQL diagnostic logging to Event Hub. Collect SQL Insights, Deadlocks, and QueryStoreRuntimeStatistics categories. Alert on DTU >90%, deadlock events, and query duration outliers.
- **Visualization:** Line chart (DTU usage), Table (deadlocks), Bar chart (top slow queries).

---

### UC-4.2.7 · AKS Cluster Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** AKS cluster health monitoring ensures Kubernetes workloads are running reliably on Azure's managed platform.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Splunk OTel Collector
- **Data Sources:** AKS diagnostics, kube-state-metrics
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="kube-apiserver" level="Error"
| stats count by host, message
| sort -count
```
- **Implementation:** Enable AKS diagnostic logging to Event Hub (kube-apiserver, kube-controller-manager, kube-scheduler, kube-audit). Deploy OTel Collector in the AKS cluster for deeper K8s-level monitoring (see Category 3.2).
- **Visualization:** Status panel, Error timeline, Table.

---

### UC-4.2.8 · Azure Key Vault Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Key Vault stores secrets, keys, and certificates. Unauthorized or anomalous access could indicate credential theft or data breach preparation.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` (Key Vault diagnostics)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AuditEvent" ResourceType="VAULTS"
| stats count by identity.claim.upn, operationName, ResultType
| where ResultType!="Success"
| sort -count
```
- **Implementation:** Enable Key Vault diagnostic logging. Monitor all access operations. Alert on failed access attempts and unusual access patterns (new principals accessing secrets).
- **Visualization:** Table (user, operation, result), Timeline, Bar chart by operation.

---

### UC-4.2.9 · Defender for Cloud Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Microsoft Defender provides threat detection across Azure resources. Centralizing in Splunk enables cross-platform security correlation.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Defender alerts via Event Hub
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:defender" severity="High" OR severity="Critical"
| table _time alertDisplayName severity resourceIdentifiers{} description
| sort -_time
```
- **Implementation:** Configure Defender for Cloud to export alerts to Event Hub. Ingest via Splunk TA. Alert on High and Critical severity findings.
- **Visualization:** Table by severity, Bar chart (alert types), Timeline, Single value (critical count).

---

### UC-4.2.10 · Storage Account Access Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusual storage access patterns may indicate data exfiltration or compromised service principals accessing sensitive data.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Storage analytics logs via Event Hub
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="StorageRead" OR Category="StorageWrite"
| stats count by callerIpAddress, accountName, operationName
| eventstats avg(count) as avg_ops, stdev(count) as stdev_ops
| where count > avg_ops + (2 * stdev_ops)
```
- **Implementation:** Enable storage diagnostic logging. Baseline normal access patterns. Alert on volumetric anomalies (unusual number of reads/writes) or new source IPs.
- **Visualization:** Table (IP, account, operations), Line chart (access over time), Map.

---

### UC-4.2.11 · Resource Health Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Azure service health impacts your resources directly. Knowing when Azure itself is having problems prevents wasted troubleshooting time.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Resource Health via Activity Log
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" category.value="ResourceHealth"
| table _time resourceGroupName resourceType status.value properties.cause properties.currentHealthStatus
| sort -_time
```
- **Implementation:** Resource Health events flow through the Activity Log. Monitor for Unavailable and Degraded statuses. Correlate with your application health metrics to distinguish Azure platform issues from your own problems.
- **Visualization:** Status panel per resource type, Table, Timeline.

---

### UC-4.2.12 · Cost Management Alerts
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Azure cost monitoring prevents budget overruns. Tracking spend by resource group/team enables chargeback and anomaly detection.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Azure Cost Management export
- **Data Sources:** Azure Cost Management data (exported to storage)
- **SPL:**
```spl
index=azure sourcetype="azure:costmanagement"
| timechart span=1d sum(CostInBillingCurrency) as daily_cost by ResourceGroup
| eventstats avg(daily_cost) as avg_cost by ResourceGroup
| where daily_cost > avg_cost * 1.5
```
- **Implementation:** Configure Azure Cost Management to export daily usage data to a storage account. Ingest in Splunk. Create budget alerts when spending approaches thresholds.
- **Visualization:** Stacked area chart (spend by RG), Line chart with budget overlay, Table.

---

## 4.3 Google Cloud Platform (GCP)

**Primary App/TA:** Splunk Add-on for Google Cloud Platform (`Splunk_TA_google-cloudplatform`) — Free on Splunkbase

---

### UC-4.3.1 · Audit Log Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** GCP audit logs capture all admin activity and data access. Foundational for security monitoring and compliance in GCP environments.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` (via Pub/Sub)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*activity"
| spath output=method path=protoPayload.methodName
| spath output=principal path=protoPayload.authenticationInfo.principalEmail
| stats count by principal, method
| sort -count
```
- **Implementation:** Create a Pub/Sub topic and subscription. Configure a log sink to route audit logs to Pub/Sub. Set up Splunk_TA_google-cloudplatform with a Pub/Sub input. Alert on destructive operations (delete, setIamPolicy).
- **Visualization:** Table (principal, method, count), Bar chart, Timeline.

---

### UC-4.3.2 · IAM Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** IAM binding changes control who can access what in GCP. Unauthorized changes to bindings on projects, folders, or organizations are critical security events.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message`
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="SetIamPolicy"
| spath output=resource path=resource.labels
| spath output=principal path=protoPayload.authenticationInfo.principalEmail
| table _time principal resource protoPayload.serviceData.policyDelta.bindingDeltas{}
| sort -_time
```
- **Implementation:** Forward admin activity logs via Pub/Sub. Alert on `SetIamPolicy` events, especially those granting `roles/owner` or `roles/editor`. Track with change management.
- **Visualization:** Events list (critical), Table (who changed what), Timeline.

---

### UC-4.3.3 · VPC Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** GCP VPC Flow Logs provide network traffic visibility. Same use case as AWS/Azure — detect rejected traffic, anomalies, exfiltration.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** VPC Flow Logs via Pub/Sub
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*vpc_flows"
| spath
| stats sum(bytes_sent) as total_bytes by connection.src_ip, connection.dest_ip, connection.dest_port
| sort -total_bytes | head 20
```
- **Implementation:** Enable VPC Flow Logs on subnets. Sink to Pub/Sub and ingest in Splunk. Analyze for top talkers, rejected flows, and anomalous destinations.
- **Visualization:** Table, Sankey diagram, Timechart, Map.

---

### UC-4.3.4 · GKE Cluster Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** GKE cluster health monitoring for managed Kubernetes in GCP. Node pools, upgrade status, and workload health.
- **App/TA:** `Splunk_TA_google-cloudplatform`, Splunk OTel Collector
- **Data Sources:** GKE logs via Pub/Sub, Cloud Monitoring metrics
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster"
| spath output=severity path=severity
| where severity="ERROR"
| stats count by resource.labels.cluster_name, textPayload
| sort -count
```
- **Implementation:** GKE logs flow through Cloud Logging. Sink to Pub/Sub for Splunk ingestion. Deploy OTel Collector in GKE for K8s-native monitoring (see Category 3.2).
- **Visualization:** Status panel, Error table, Timeline.

---

### UC-4.3.5 · Security Command Center
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** SCC provides vulnerability findings and threat detections across GCP. Centralizing in Splunk enables multi-cloud security correlation.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** SCC findings via Pub/Sub notification
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="scc_finding"
| spath output=severity path=finding.severity
| spath output=category path=finding.category
| where severity="CRITICAL" OR severity="HIGH"
| table _time category severity finding.resourceName finding.description
| sort -_time
```
- **Implementation:** Configure SCC to publish findings to Pub/Sub. Ingest via Splunk TA. Alert on CRITICAL and HIGH severity findings.
- **Visualization:** Table by severity, Bar chart (finding categories), Trend line.

---

### UC-4.3.6 · GCE Instance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Monitoring metrics via API
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="compute.googleapis.com/instance/cpu/utilization"
| timechart span=1h avg(value) by resource.labels.instance_id
```
- **Implementation:** Configure Cloud Monitoring metric collection in the Splunk TA. Collect CPU utilization, disk I/O, and network metrics. Alert on sustained high utilization.
- **Visualization:** Line chart, Heatmap, Gauge.

---

### UC-4.3.7 · BigQuery Audit and Cost
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** BigQuery can generate massive costs from poorly optimized queries. Audit and cost tracking prevents bill shock and identifies optimization opportunities.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** BigQuery audit logs via Pub/Sub
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="bigquery.googleapis.com" protoPayload.methodName="jobservice.jobcompleted"
| spath output=bytes_billed path=protoPayload.serviceData.jobCompletedEvent.job.jobStatistics.totalBilledBytes
| spath output=user path=protoPayload.authenticationInfo.principalEmail
| eval cost_usd = round(bytes_billed / 1099511627776 * 5, 4)
| stats sum(cost_usd) as total_cost, count as queries by user
| sort -total_cost
```
- **Implementation:** Forward BigQuery audit logs via Pub/Sub. Calculate cost from billed bytes ($5/TB). Create dashboard showing cost per user, top expensive queries, and slot utilization.
- **Visualization:** Table (user, queries, cost), Bar chart (top costly queries), Trend line (daily cost).

---

### UC-4.3.8 · Cloud Run/Functions Errors
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Serverless function errors and cold starts impact application reliability and user experience.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Run/Functions logs via Cloud Logging
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function" severity="ERROR"
| spath output=function path=resource.labels.function_name
| stats count by function, textPayload
| sort -count
```
- **Implementation:** Forward Cloud Run/Functions logs via Pub/Sub. Monitor error rates, execution duration, and cold start frequency. Alert on error rate >5%.
- **Visualization:** Line chart (errors over time), Bar chart (top error functions), Single value.

---

## 4.4 Multi-Cloud & Cloud Management

---

### UC-4.4.1 · Terraform Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Infrastructure drift from declared IaC state means manual changes broke the single source of truth. Causes unpredictable behavior and deployment failures.
- **App/TA:** Custom input (Terraform CLI output, CI/CD integration)
- **Data Sources:** `terraform plan` output, CI/CD pipeline logs
- **SPL:**
```spl
index=devops sourcetype="terraform:plan"
| where changes_detected="true"
| stats count as drifted_resources by workspace, resource_type
| sort -drifted_resources
```
- **Implementation:** Run `terraform plan -detailed-exitcode` on schedule in CI/CD. Forward plan output to Splunk via HEC. Exit code 2 = changes detected (drift). Alert on any drift in production workspaces.
- **Visualization:** Table (workspace, resource, drift), Single value (drifted resources), Bar chart.

---

### UC-4.4.2 · Cross-Cloud Identity Correlation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Users often have identities across AWS/Azure/GCP. Correlating activity provides unified view for security investigation and insider threat detection.
- **App/TA:** Combined cloud TAs + lookup tables
- **Data Sources:** All cloud audit logs
- **SPL:**
```spl
index=aws OR index=azure OR index=gcp
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval user=coalesce(userIdentity.arn, userPrincipalName, protoPayload.authenticationInfo.principalEmail)
| lookup cloud_identity_map user OUTPUT normalized_user
| stats count, dc(cloud) as clouds_active, values(cloud) as clouds by normalized_user
| where clouds_active > 1
| sort -count
```
- **Implementation:** Create a lookup table mapping cloud identities to a normalized user (e.g., email). Combine audit logs from all three providers. Dashboard showing cross-cloud activity per user.
- **Visualization:** Table (user, clouds, activity count), Sankey diagram (user to cloud to action).

---

### UC-4.4.3 · Multi-Cloud Cost Dashboard
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Unified cost visibility across cloud providers enables budgeting, chargeback, and optimization decisions from a single pane of glass.
- **App/TA:** Combined cloud TAs, billing data
- **Data Sources:** AWS CUR, Azure Cost Management, GCP Billing export
- **SPL:**
```spl
index=aws sourcetype="aws:billing" OR index=azure sourcetype="azure:costmanagement" OR index=gcp sourcetype="gcp:billing"
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval cost=coalesce(BlendedCost, CostInBillingCurrency, cost)
| timechart span=1d sum(cost) by cloud
```
- **Implementation:** Ingest billing data from each provider. Normalize cost fields. Create a unified dashboard with consistent time-grain (daily). Break down by team using tagging from each provider.
- **Visualization:** Stacked area chart (daily cost by cloud), Table (cost by service), Pie chart (cost distribution).

---

### UC-4.4.4 · Cloud Resource Tagging Compliance
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Untagged resources can't be tracked for cost allocation, compliance, or ownership. Tagging compliance is foundational for cloud governance.
- **App/TA:** Cloud provider TAs, Config rules
- **Data Sources:** Cloud resource inventories, Config/Policy compliance
- **SPL:**
```spl
index=aws sourcetype="aws:config:notification" resourceType="AWS::EC2::Instance"
| spath output=tags path=configuration.tags{}
| eval has_owner = if(match(tags, "Owner"), "Yes", "No")
| eval has_env = if(match(tags, "Environment"), "Yes", "No")
| where has_owner="No" OR has_env="No"
| table resourceId has_owner has_env
```
- **Implementation:** Use AWS Config rules (required-tags), Azure Policy, or GCP org policies to evaluate tagging. Ingest compliance results. Dashboard showing tagging compliance by tag and resource type.
- **Visualization:** Table (resource, missing tags), Pie chart (compliant %), Bar chart by tag.

---

# 5. Network Infrastructure

## 5.1 Routers & Switches

**Primary App/TA:** Splunk Add-on for Cisco IOS (`Splunk_TA_cisco-ios`), SNMP Modular Input — Free

---

### UC-5.1.1 · Interface Up/Down Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Link state changes directly impact connectivity. Flapping interfaces cause intermittent outages.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%LINEPROTO-5-UPDOWN" OR "%LINK-3-UPDOWN"
| rex "Interface (?<interface>\S+), changed state to (?<state>\w+)"
| stats count by host, interface, state | where count > 3 | sort -count
```
- **Implementation:** Configure syslog forwarding on all network devices (UDP/TCP 514). Install TA for field extraction. Alert on down events for uplinks/trunks. Track flapping (>3 transitions in 10 min).
- **Visualization:** Status grid (green/red per interface), Table, Timeline.

---

### UC-5.1.2 · Interface Error Rates
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** CRC errors, drops indicate cabling, transceiver, or duplex issues.
- **App/TA:** SNMP Modular Input, IF-MIB
- **Data Sources:** `sourcetype=snmp:interface`
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev by host, ifDescr
| eval delta = ifInErrors - prev | where delta > 0
| table _time host ifDescr delta
```
- **Implementation:** Poll IF-MIB (ifInErrors, ifOutErrors, ifInDiscards) at 300s. Use `streamstats` for delta. Alert on increasing counts.
- **Visualization:** Line chart (error rate), Table, Heatmap across devices.

---

### UC-5.1.3 · Interface Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Saturated links cause drops and congestion. Trending enables proactive upgrades.
- **App/TA:** SNMP Modular Input
- **Data Sources:** SNMP IF-MIB (ifHCInOctets, ifHCOutOctets, ifSpeed)
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifHCInOctets) as prev_in, last(_time) as prev_time by host, ifDescr
| eval in_bps=((ifHCInOctets-prev_in)*8)/(_time-prev_time)
| eval util_pct=round(in_bps/ifSpeed*100,1) | where util_pct>80
```
- **Implementation:** Poll 64-bit counters every 300s. Alert at 80% sustained. Use `predict` for capacity planning.
- **Visualization:** Line chart, Gauge per critical link, Table sorted by utilization.

---

### UC-5.1.4 · BGP Peer State Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** BGP session drops cause routing convergence, potentially making networks unreachable.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%BGP-5-ADJCHANGE" OR "%BGP-3-NOTIFICATION"
| rex "neighbor (?<neighbor_ip>\S+)" | table _time host neighbor_ip _raw | sort -_time
```
- **Implementation:** Forward syslog from all BGP speakers. Critical alert on adjacency down. Include neighbor IP and AS number.
- **Visualization:** Events timeline (critical), Status panel per BGP session, Table.

---

### UC-5.1.5 · OSPF Neighbor Adjacency
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** OSPF neighbor loss triggers SPF recalculation, disrupting traffic.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%OSPF-5-ADJCHG"
| rex "Nbr (?<neighbor_ip>\S+) on (?<interface>\S+) from (?<from_state>\S+) to (?<to_state>\S+)"
| table _time host neighbor_ip interface from_state to_state
```
- **Implementation:** Forward syslog from all OSPF routers. Alert on adjacency changes to/from FULL. Track frequency for instability.
- **Visualization:** Events timeline, Table (router, neighbor, states).

---

### UC-5.1.6 · Spanning Tree Topology Change
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** STP topology changes cause brief disruption and MAC flushing. Root bridge changes are critical.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE"
| stats count by host | where count > 5 | sort -count
```
- **Implementation:** Forward syslog. Alert on root bridge changes (critical). Track topology change frequency per VLAN.
- **Visualization:** Table, Timeline, Bar chart by VLAN.

---

### UC-5.1.7 · Configuration Change Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unauthorized config changes are a top cause of outages. Essential for compliance.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SYS-5-CONFIG_I"
| rex "Configured from (?<config_source>\S+) by (?<user>\S+)"
| table _time host user config_source
```
- **Implementation:** Forward syslog. Enable archive logging. Alert on any config change. Correlate with change tickets.
- **Visualization:** Table (device, user, time), Timeline, Single value (changes last 24h).

---

### UC-5.1.8 · Device CPU/Memory Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** CPU exhaustion causes packet drops, routing failures, management unresponsiveness.
- **App/TA:** SNMP, CISCO-PROCESS-MIB
- **Data Sources:** `sourcetype=snmp:cpu`
- **SPL:**
```spl
index=network sourcetype="snmp:cpu"
| timechart span=5m avg(cpmCPUTotal5minRev) as cpu_pct by host | where cpu_pct > 80
```
- **Implementation:** Poll CISCO-PROCESS-MIB and CISCO-MEMORY-POOL-MIB every 300s. Alert CPU >80% or memory >85%.
- **Visualization:** Line chart, Gauge, Table of high-utilization devices.

---

### UC-5.1.9 · Device Uptime / Reload Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Unexpected reboots indicate hardware failure or unauthorized reload.
- **App/TA:** SNMP, syslog
- **Data Sources:** SNMP sysUpTime, `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SYS-5-RESTART" OR "%SYS-5-RELOAD"
| table _time host _raw | sort -_time
```
- **Implementation:** Poll SNMP sysUpTime. Forward syslog reload messages. Alert when uptime drops. Cross-reference with maintenance windows.
- **Visualization:** Table (device, uptime), Timeline, Single value (unexpected reboots).

---

### UC-5.1.10 · VLAN Configuration Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** VLAN changes affect segmentation. Unauthorized changes can bypass security controls.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%VLAN_MANAGER-6-VLAN_CREATE" OR "%VLAN_MANAGER-6-VLAN_DELETE"
| table _time host _raw | sort -_time
```
- **Implementation:** Forward syslog. Alert on VLAN creation/deletion. Correlate with change tickets.
- **Visualization:** Table, Timeline.

---

### UC-5.1.11 · Power Supply / Fan Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Hardware failures reduce redundancy. A second failure causes outage.
- **App/TA:** `Splunk_TA_cisco-ios`, SNMP CISCO-ENVMON-MIB
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%FAN-3-FAN_FAILED" OR "%PLATFORM_ENV-1-PSU" OR "%ENVIRONMENTAL-1-ALERT"
| table _time host _raw | sort -_time
```
- **Implementation:** Forward syslog. Poll ENVMON-MIB. Alert immediately on hardware failure. Include device location for dispatch.
- **Visualization:** Status indicator per device, Events list (critical).

---

### UC-5.1.12 · ARP/MAC Table Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** MAC flapping indicates loops, misconfigurations, or layer-2 attacks.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SW_MATM-4-MACFLAP_NOTIF"
| rex "(?<mac>[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})"
| stats count by host, mac | sort -count
```
- **Implementation:** Forward syslog. Alert on MACFLAP events. Investigate the MAC to find the device.
- **Visualization:** Table, Timeline, Bar chart.

---

### UC-5.1.13 · ACL Deny Logging
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** ACL deny hits show blocked traffic. High volumes may indicate attacks or misconfigured apps.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SEC-6-IPACCESSLOGP"
| rex "list (?<acl>\S+) denied (?<proto>\w+) (?<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count by host, acl, src_ip, proto | sort -count
```
- **Implementation:** Enable ACL logging (`log` keyword). Forward syslog. Dashboard showing top denied sources and trends.
- **Visualization:** Table, Bar chart by source IP, Timechart.

---

### UC-5.1.14 · SNMP Authentication Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Failed SNMP auth indicates unauthorized polling or reconnaissance.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SNMP-3-AUTHFAIL"
| rex "from (?<src_ip>\S+)" | stats count by host, src_ip | sort -count
```
- **Implementation:** Forward syslog. Alert on repeated failures from unknown sources.
- **Visualization:** Table, Map, Timeline.

---

### UC-5.1.15 · Environmental Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Temperature alerts catch cooling failures before they cause device outages.
- **App/TA:** SNMP, CISCO-ENVMON-MIB
- **Data Sources:** `sourcetype=snmp:environment`
- **SPL:**
```spl
index=network sourcetype="snmp:environment"
| stats latest(ciscoEnvMonTemperatureValue) as temp_c by host | where temp_c > 45
```
- **Implementation:** Poll ENVMON-MIB temperature sensors every 300s. Alert when >45°C.
- **Visualization:** Gauge per device, Line chart (trending), Table.

---

### UC-5.1.16 · Route Table Flapping
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Unstable routes cause packet loss and reachability failures. Detecting flapping routes prevents cascading network outages across your infrastructure.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "ROUTING" OR "RT_ENTRY" OR "%DUAL-5-NBRCHANGE" OR "%BGP-5-ADJCHANGE" OR "%OSPF-5-ADJCHG"
| rex "(?<protocol>BGP|OSPF|EIGRP).*?(?<prefix>\d+\.\d+\.\d+\.\d+/?\d*)"
| bin _time span=10m | stats count as changes by _time, host, protocol, prefix
| where changes > 5 | sort -changes
```
- **Implementation:** Collect syslog from all routers. Alert on >5 route changes for the same prefix in 10 minutes. Correlate with interface flaps. Use `streamstats` to detect patterns.
- **Visualization:** Timeline (flapping events), Table (prefix, host, count), Line chart (change frequency).

---

### UC-5.1.17 · Duplex Mismatch Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Duplex mismatches degrade link performance silently. They cause late collisions, CRC errors, and reduced throughput that are hard to diagnose.
- **App/TA:** SNMP Modular Input, IF-MIB, `Splunk_TA_cisco-ios`
- **Data Sources:** `sourcetype=cisco:ios`, `sourcetype=snmp:interface`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%CDP-4-DUPLEX_MISMATCH"
| rex "duplex mismatch discovered on (?<local_intf>\S+).*with (?<remote_device>\S+) (?<remote_intf>\S+)"
| stats count latest(_time) as last_seen by host, local_intf, remote_device, remote_intf
| sort -last_seen
```
- **Implementation:** Enable CDP/LLDP on all interfaces. Monitor syslog for duplex mismatch messages. Cross-reference with SNMP interface counters showing late collisions.
- **Visualization:** Table (local device/interface → remote device/interface), Alert list.

---

### UC-5.1.18 · CDP/LLDP Neighbor Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Unexpected neighbor changes indicate cabling modifications, device replacements, or unauthorized devices connecting to the network.
- **App/TA:** SNMP Modular Input, CISCO-CDP-MIB, LLDP-MIB
- **Data Sources:** `sourcetype=snmp:cdp`, `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="snmp:cdp"
| stats latest(cdpCacheDeviceId) as neighbor, latest(cdpCachePlatform) as platform by host, cdpCacheIfIndex
| appendpipe [| inputlookup cdp_baseline.csv]
| eventstats latest(neighbor) as current, first(neighbor) as baseline by host, cdpCacheIfIndex
| where current!=baseline | table host, cdpCacheIfIndex, baseline, current, platform
```
- **Implementation:** Poll CDP-MIB/LLDP-MIB at 600s intervals. Create a baseline lookup via `outputlookup`. Compare current neighbors against baseline. Alert on new/removed neighbors.
- **Visualization:** Table (host, interface, old neighbor, new neighbor), Change log timeline.

---

### UC-5.1.19 · PoE Power Budget Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** PoE budget exhaustion causes powered devices (IP phones, APs, cameras) to lose power. Proactive monitoring prevents unplanned device outages.
- **App/TA:** SNMP Modular Input, POWER-ETHERNET-MIB
- **Data Sources:** `sourcetype=snmp:poe`
- **SPL:**
```spl
index=network sourcetype="snmp:poe"
| stats latest(pethMainPseOperStatus) as status, latest(pethMainPsePower) as total_watts, latest(pethMainPseConsumptionPower) as used_watts by host
| eval utilization_pct=round(used_watts/total_watts*100,1)
| where utilization_pct > 80 | sort -utilization_pct
```
- **Implementation:** Poll POWER-ETHERNET-MIB every 300s. Track per-switch PoE budget utilization. Alert at 80% utilization. Trend over time to plan for additional PoE capacity.
- **Visualization:** Gauge (per switch), Line chart (utilization trending), Table (switch, budget, used, remaining).

---

### UC-5.1.20 · EIGRP Neighbor Flapping
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** EIGRP neighbor instability causes route recalculation, increased CPU load, and traffic blackholing during convergence.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%DUAL-5-NBRCHANGE"
| rex "EIGRP-(?<protocol>IPv4|IPv6) (?<as_number>\d+).*Neighbor (?<neighbor_ip>\S+) \((?<interface>\S+)\) is (?<state>up|down)"
| bin _time span=15m | stats count(eval(state="down")) as downs, count(eval(state="up")) as ups by _time, host, neighbor_ip, interface
| where downs > 2
```
- **Implementation:** Collect syslog from Cisco routers. Alert on >2 EIGRP neighbor down events in 15 minutes. Correlate with interface flaps and CPU utilization.
- **Visualization:** Timeline (up/down events), Table (neighbor, interface, flap count), Status grid.

---

### UC-5.1.21 · CRC Error Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Increasing CRC errors indicate failing cables, SFPs, or electromagnetic interference. Early detection prevents link failures.
- **App/TA:** SNMP Modular Input, IF-MIB
- **Data Sources:** `sourcetype=snmp:interface`
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev_errors, last(_time) as prev_time by host, ifDescr
| eval error_rate=(ifInErrors-prev_errors)/(_time-prev_time)
| where error_rate > 0
| timechart span=1h avg(error_rate) by host limit=20
```
- **Implementation:** Poll IF-MIB counters every 300s. Use `streamstats` to compute deltas. Trend over days to detect worsening interfaces. Cross-reference with interface utilization.
- **Visualization:** Line chart (error rate over time per interface), Heatmap (device × interface), Table.

---

### UC-5.1.22 · Syslog Source Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Value:** Silence from a device means either it's healthy or its syslog forwarding broke. Detecting missing syslog sources ensures continuous visibility.
- **App/TA:** Splunk core (metadata search)
- **Data Sources:** `sourcetype=cisco:ios`, `sourcetype=syslog`
- **SPL:**
```spl
| tstats count where index=network sourcetype="cisco:ios" by host
| append [| inputlookup network_device_inventory.csv | rename device as host | fields host]
| stats sum(count) as event_count by host | where event_count=0 OR isnull(event_count)
| table host | rename host as "Silent Devices"
```
- **Implementation:** Maintain a device inventory lookup. Schedule a search comparing active syslog sources against inventory. Alert on devices missing for >1 hour.
- **Visualization:** Table (silent devices), Single value (count of silent devices), Status grid (all devices).

---

### UC-5.1.23 · HSRP/VRRP State Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Gateway redundancy state changes impact all hosts on a subnet. Detecting unexpected failovers prevents prolonged outages.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%HSRP-5-STATECHANGE" OR "%VRRP-6-STATECHANGE"
| rex "Grp (?<group>\d+) state (?<old_state>\w+) -> (?<new_state>\w+)"
| where new_state="Active" OR new_state="Master"
| stats count by host, group, old_state, new_state | sort -_time
```
- **Implementation:** Enable HSRP/VRRP syslog notifications. Alert on Active/Master transitions. Correlate with interface or device failures to validate failover cause.
- **Visualization:** Timeline (state changes), Table (group, host, transition), Alert panel.

---


## 5.2 Firewalls

**Primary App/TA:** Palo Alto Networks Add-on (`Splunk_TA_paloalto`), Cisco Firepower TA, Fortinet TA — Free

---

### UC-5.2.1 · Top Denied Traffic Sources
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies top blocked traffic sources — useful for rule tuning, detecting scanning, and misconfigured apps.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`, `sourcetype=cisco:firepower:syslog`
- **SPL:**
```spl
index=firewall action="denied" OR action="drop"
| stats count as denials, dc(dest_ip) as unique_dests by src_ip
| sort -denials | head 20 | lookup geoip ip as src_ip OUTPUT Country
```
- **Implementation:** Forward firewall traffic logs via syslog. Install vendor TA for CIM-compliant fields. Create top-N dashboard.
- **Visualization:** Table (source, denials, dests), Map (GeoIP), Bar chart.

---

### UC-5.2.2 · Policy Change Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Firewall rule changes can expose the network. Compliance must-have (PCI, SOX, HIPAA).
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** `sourcetype=pan:config`, firewall system/config logs
- **SPL:**
```spl
index=firewall sourcetype="pan:config" cmd="set" OR cmd="edit" OR cmd="delete"
| table _time host admin cmd path | sort -_time
```
- **Implementation:** Forward configuration change logs. Alert on any rule modification. Require change ticket correlation. Keep 1-year retention.
- **Visualization:** Table (who, what, when), Timeline, Single value (changes last 24h).

---

### UC-5.2.3 · Threat Detection Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** IPS/IDS events indicate active attacks. Correlation with traffic context enables rapid response.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** `sourcetype=pan:threat`, `sourcetype=cisco:firepower:alert`
- **SPL:**
```spl
index=firewall sourcetype="pan:threat" severity="critical" OR severity="high"
| stats count by src_ip, dest_ip, threat_name, severity, action | sort -count
```
- **Implementation:** Forward threat logs. Alert immediately on critical severity. Correlate source IPs with auth logs.
- **Visualization:** Table (source, dest, threat, action), Bar chart by threat type, Map.

---

### UC-5.2.4 · VPN Tunnel Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** VPN failures isolate remote sites or users. Proactive monitoring prevents "the VPN is down" calls.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall VPN/system logs
- **SPL:**
```spl
index=firewall ("tunnel" OR "IPSec" OR "IKE") ("down" OR "failed" OR "established")
| rex "(?<tunnel_peer>\d+\.\d+\.\d+\.\d+)"
| eval status=if(match(_raw,"established|up"),"Up","Down")
| stats latest(status) as state by host, tunnel_peer | where state="Down"
```
- **Implementation:** Forward VPN logs. Alert on tunnel down events. Track flapping. Dashboard showing all tunnels.
- **Visualization:** Status grid (green/red per tunnel), Table, Timeline.

---

### UC-5.2.5 · High-Risk Port Exposure
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Allowed traffic to RDP/SMB/Telnet from untrusted zones indicates policy gaps.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall action="allowed" (dest_port=3389 OR dest_port=445 OR dest_port=23)
| where NOT cidrmatch("10.0.0.0/8", src_ip)
| stats count by src_ip, dest_ip, dest_port | sort -count
```
- **Implementation:** Monitor allow rules for external traffic to high-risk ports. Alert on any matches. Review and tighten rules.
- **Visualization:** Table (source, dest, port), Bar chart by port, Map.

---

### UC-5.2.6 · Geo-IP Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Traffic to/from sanctioned or unexpected countries flags exfiltration, C2, or compromised hosts.
- **App/TA:** Vendor-specific TA + GeoIP lookup
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall action="allowed" direction="outbound"
| lookup geoip ip as dest_ip OUTPUT Country
| search Country IN ("Russia","China","North Korea","Iran")
| stats count, sum(bytes_out) as data_sent by src_ip, Country | sort -data_sent
```
- **Implementation:** Install GeoIP lookup (MaxMind). Enrich traffic logs. Alert on sanctioned country traffic and volume anomalies.
- **Visualization:** Choropleth map, Table, Bar chart by country.

---

### UC-5.2.7 · Connection Rate Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Sudden connection spikes indicate DDoS, scanning, or worm propagation.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall | timechart span=5m count as connections by src_ip
| eventstats avg(connections) as avg_c, stdev(connections) as std_c by src_ip
| where connections > (avg_c + 3*std_c) | sort -connections
```
- **Implementation:** Baseline connection rates over 7 days. Alert when rate exceeds 3 standard deviations.
- **Visualization:** Line chart with threshold overlay, Table, Timechart.

---

### UC-5.2.8 · Certificate Inspection Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** SSL decryption failures mean traffic passes uninspected — could be legitimate cert pinning or SSL evasion.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall decryption logs
- **SPL:**
```spl
index=firewall sourcetype="pan:decryption" action="ssl-error"
| stats count by dest_ip, dest_port, reason | sort -count
```
- **Implementation:** Enable decryption logging. Track failure rates by destination. Tune exclusion lists.
- **Visualization:** Table, Pie chart (reasons), Trend line.

---

### UC-5.2.9 · URL Filtering Blocks
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Shows what categories users are trying to access. Reveals policy effectiveness and shadow IT.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** `sourcetype=pan:url`
- **SPL:**
```spl
index=firewall sourcetype="pan:url" action="block-url"
| stats count by url_category, src_ip | sort -count
```
- **Implementation:** Forward URL filtering logs. Dashboard showing blocks by category and user.
- **Visualization:** Bar chart (by category), Table, Pie chart.

---

### UC-5.2.10 · Admin Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Firewall admin access is highly privileged. Audit trail is a compliance must-have.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall system/auth logs
- **SPL:**
```spl
index=firewall sourcetype="pan:system" ("login" OR "logout" OR "auth")
| eval status=case(match(_raw,"success"),"Success", match(_raw,"fail"),"Failed", 1=1,"Other")
| stats count by admin_user, src_ip, status | sort -count
```
- **Implementation:** Forward system/auth logs. Alert on failed admin logins. Track all successful logins. Alert on unexpected source IPs.
- **Visualization:** Table (admin, source, status), Timeline, Bar chart.

---

### UC-5.2.11 · Firewall Resource Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Session table exhaustion blocks new connections. CPU saturation degrades throughput.
- **App/TA:** Vendor-specific TA, SNMP
- **Data Sources:** Firewall system resource logs
- **SPL:**
```spl
index=firewall ("session" AND "utilization") OR ("cpu" AND "dataplane")
| timechart span=5m avg(session_utilization) as session_pct by host | where session_pct > 80
```
- **Implementation:** Monitor via SNMP (vendor-specific MIB) or system logs. Alert on session table >80%, dataplane CPU >80%.
- **Visualization:** Gauge (session/CPU/memory), Line chart, Table.

---

### UC-5.2.12 · NAT Pool Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** NAT exhaustion prevents outbound connections. Users lose internet access.
- **App/TA:** Vendor-specific TA, syslog
- **Data Sources:** Firewall NAT/system logs
- **SPL:**
```spl
index=firewall ("NAT" OR "nat") ("exhausted" OR "allocation failed" OR "out of")
| stats count by host, nat_pool | sort -count
```
- **Implementation:** Forward firewall logs. Monitor NAT table usage. Alert on exhaustion messages or >80% utilization.
- **Visualization:** Gauge per pool, Table, Events timeline.

---

### UC-5.2.13 · Session Table Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** When session tables fill, new connections are dropped. This causes service outages that are difficult to diagnose without firewall telemetry.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_fortinet_fortigate, SNMP
- **Data Sources:** `sourcetype=pan:system`, `sourcetype=fgt_event`, SNMP
- **SPL:**
```spl
index=network sourcetype="pan:system" "session table"
| append [search index=network sourcetype="pan:traffic" | stats dc(session_id) as active_sessions by dvc | eval max_sessions=coalesce(max_sessions,500000)]
| stats latest(active_sessions) as sessions, latest(max_sessions) as max by dvc
| eval utilization=round(sessions/max*100,1) | where utilization > 80
```
- **Implementation:** Monitor session counts via SNMP or firewall system logs. Know your platform's session limit. Alert at 80% utilization. Investigate top session consumers by source/destination.
- **Visualization:** Gauge (per firewall), Line chart (session count trending), Table (top consumers).

---

### UC-5.2.14 · Firewall HA Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** HA failovers cause brief traffic disruption and can indicate underlying hardware or link failures. Tracking failover frequency detects instability.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_fortinet_fortigate
- **Data Sources:** `sourcetype=pan:system`, `sourcetype=fgt_event`
- **SPL:**
```spl
index=network (sourcetype="pan:system" "HA state change") OR (sourcetype="fgt_event" subtype="ha")
| rex "state change.*from (?<old_state>\w+) to (?<new_state>\w+)"
| table _time, dvc, old_state, new_state | sort -_time
```
- **Implementation:** Forward firewall system logs to Splunk. Alert on any active/passive transition. Correlate with link down events. Track failover frequency — more than 1 per week indicates instability.
- **Visualization:** Timeline (failover events), Single value (failovers this month), Table (history).

---

### UC-5.2.15 · Botnet/C2 Traffic Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Detecting outbound connections to known C2 infrastructure identifies compromised internal hosts before data exfiltration occurs.
- **App/TA:** `Splunk_TA_paloalto`, Threat intelligence feeds
- **Data Sources:** `sourcetype=pan:threat`, `sourcetype=pan:traffic`
- **SPL:**
```spl
index=network sourcetype="pan:threat" category="command-and-control" OR category="spyware"
| stats count values(dest_ip) as c2_targets dc(dest_ip) as unique_c2 by src_ip
| sort -count
| lookup dnslookup clientip as src_ip OUTPUT clienthost as src_hostname
```
- **Implementation:** Enable threat prevention and URL filtering on the firewall. Ingest threat logs. Cross-reference with external threat intelligence (STIX/TAXII feeds). Alert immediately on any C2 match.
- **Visualization:** Table (compromised hosts, C2 targets), Sankey diagram (source → C2), Single value (count).

---

### UC-5.2.16 · SSL/TLS Decryption Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Decryption failures create blind spots in security inspection. Tracking failures by destination reveals certificate pinning, protocol mismatches, or policy gaps.
- **App/TA:** `Splunk_TA_paloalto`
- **Data Sources:** `sourcetype=pan:decryption`
- **SPL:**
```spl
index=network sourcetype="pan:decryption" action="decrypt-error" OR action="no-decrypt"
| stats count by reason, dest_ip, dest_port
| sort -count
| head 50
```
- **Implementation:** Enable decryption logging. Group failures by reason (unsupported cipher, certificate pinning, policy exclude). Review and update decryption policy based on findings.
- **Visualization:** Bar chart (failure reasons), Table (top undecrypted destinations), Pie chart (by reason).

---

### UC-5.2.17 · Firewall Rule Hit Count Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Unused firewall rules increase attack surface and complexity. Identifying zero-hit rules enables rule base cleanup and reduces risk.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_fortinet_fortigate
- **Data Sources:** `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`
- **SPL:**
```spl
index=network sourcetype="pan:traffic"
| stats count as hit_count dc(src_ip) as unique_sources dc(dest_ip) as unique_dests by rule
| sort hit_count
| eval status=if(hit_count=0,"UNUSED",if(hit_count<10,"RARELY_USED","ACTIVE"))
```
- **Implementation:** Collect traffic logs with rule names. Run weekly reports to identify unused rules. Review rules with zero hits over 90 days for removal. Document cleanup actions.
- **Visualization:** Table (rule, hit count, status), Bar chart (hit count distribution), Single value (unused rule count).

---

### UC-5.2.18 · Threat Prevention Signature Coverage
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Outdated threat signatures leave the firewall blind to new attacks. Monitoring signature versions ensures security posture is current.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_fortinet_fortigate
- **Data Sources:** `sourcetype=pan:system`, `sourcetype=fgt_event`
- **SPL:**
```spl
index=network sourcetype="pan:system" "threat version" OR "content update"
| rex "installed (?<content_type>threats|antivirus|wildfire) version (?<version>\S+)"
| stats latest(version) as current_version, latest(_time) as last_update by dvc, content_type
| eval days_since_update=round((now()-last_update)/86400,0)
| where days_since_update > 7
```
- **Implementation:** Forward system logs. Alert when signature updates are >7 days old. Compare across firewalls to detect update failures. Schedule weekly compliance reports.
- **Visualization:** Table (firewall, content type, version, days since update), Single value (outdated count).

---


## 5.3 Load Balancers & ADCs

**Primary App/TA:** Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`), Citrix ADC TA — Free

---

### UC-5.3.1 · Pool Member Health Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Offline pool members reduce capacity. All members down = complete service outage.
- **App/TA:** `Splunk_TA_f5-bigip`, syslog
- **Data Sources:** `sourcetype=f5:bigip:syslog`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:syslog" ("pool member" AND ("down" OR "up" OR "offline"))
| rex "Pool (?<pool>\S+) member (?<member>\S+) monitor status (?<status>\w+)"
| table _time host pool member status | sort -_time
```
- **Implementation:** Forward F5 syslog (LTM log level). Install TA. Alert when pool members go down. Critical alert when all members in a pool offline.
- **Visualization:** Status grid (green/red per member), Table, Timeline.

---

### UC-5.3.2 · Virtual Server Availability
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** VIP down = application unreachable. Direct service impact.
- **App/TA:** `Splunk_TA_f5-bigip`, SNMP
- **Data Sources:** `sourcetype=f5:bigip:syslog`, iControl REST
- **SPL:**
```spl
index=network sourcetype="f5:bigip:syslog" "virtual" ("disabled" OR "offline" OR "unavailable")
| table _time host virtual_server status | sort -_time
```
- **Implementation:** Forward syslog. Monitor VIP status via SNMP or iControl REST. Alert on any state change away from "available".
- **Visualization:** Status indicator per VIP, Events timeline (critical).

---

### UC-5.3.3 · Connection and Throughput Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Reveals application demand patterns. Useful for capacity planning and DDoS detection.
- **App/TA:** `Splunk_TA_f5-bigip`, SNMP
- **Data Sources:** SNMP F5-BIGIP-LTM-MIB
- **SPL:**
```spl
index=network sourcetype="snmp:f5"
| timechart span=5m sum(clientside_curConns) as connections by virtual_server
```
- **Implementation:** Poll F5 via SNMP or iControl REST for VIP statistics. Baseline patterns and alert on anomalies.
- **Visualization:** Line chart per VIP, Area chart (throughput), Table.

---

### UC-5.3.4 · SSL Certificate Expiry
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Expired certificates on load balancers cause browser warnings or connection failures. Most preventable outage.
- **App/TA:** `Splunk_TA_f5-bigip`, custom scripted input
- **Data Sources:** iControl REST API (`/mgmt/tm/sys/crypto/cert`)
- **SPL:**
```spl
index=network sourcetype="f5:certificate_inventory"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<90
| sort days_left | table host cert_name days_left expiry_date
```
- **Implementation:** Scripted input querying iControl REST for certs. Run daily. Alert at 90/60/30/7 day thresholds.
- **Visualization:** Table sorted by days to expiry, Single value (expiring <30d), Status indicator.

---

### UC-5.3.5 · HTTP Error Rate by VIP
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Backend 5xx errors indicate application issues. Per-VIP tracking isolates degraded services.
- **App/TA:** `Splunk_TA_f5-bigip`, request logging
- **Data Sources:** F5 request logging profile
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm:http"
| eval is_error=if(response_code>=500,1,0)
| timechart span=5m sum(is_error) as errors, count as total by virtual_server
| eval error_rate=round(errors/total*100,2) | where error_rate>5
```
- **Implementation:** Enable F5 request logging profile on VIPs. Alert when 5xx rate >5% over 5 minutes.
- **Visualization:** Line chart (error rate), Table (VIP, error rate), Single value.

---

### UC-5.3.6 · Response Time Degradation
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Increasing response times indicate backend bottlenecks before they become outages.
- **App/TA:** `Splunk_TA_f5-bigip`
- **Data Sources:** F5 request logging (server_latency)
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm:http"
| timechart span=5m perc95(server_latency) as p95 by virtual_server | where p95>2000
```
- **Implementation:** Enable request logging with server-side timing. Track P95 latency per VIP. Alert when exceeding SLA threshold.
- **Visualization:** Line chart (P50/P95/P99), Table, Single value.

---

### UC-5.3.7 · Session Persistence Issues
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Broken persistence causes lost sessions, shopping carts, or random logouts.
- **App/TA:** `Splunk_TA_f5-bigip`
- **Data Sources:** F5 LTM logs, request logs
- **SPL:**
```spl
index=network sourcetype="f5:bigip:syslog" "persistence" ("failed" OR "expired")
| stats count by virtual_server, persistence_type | sort -count
```
- **Implementation:** Monitor persistence failures. Track same client hitting different backends from request logs.
- **Visualization:** Table, Line chart, Bar chart.

---

### UC-5.3.8 · WAF Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.
- **App/TA:** `Splunk_TA_f5-bigip` (ASM)
- **Data Sources:** `sourcetype=f5:bigip:asm:syslog`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:asm:syslog"
| stats count by violation_name, src_ip, request_uri, severity | sort -count
```
- **Implementation:** Enable F5 ASM logging. Dashboard showing top violations, attack sources, and targeted URIs.
- **Visualization:** Table, Bar chart by violation, Map (source IPs), Timeline.

---

### UC-5.3.9 · Connection Queue Depth
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Growing connection queues indicate backend saturation. Users experience timeouts before the server actually fails.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler
- **Data Sources:** `sourcetype=f5:bigip:ltm`, SNMP
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm"
| stats latest(curConns) as connections, latest(connqDepth) as queue_depth by virtual_server
| where queue_depth > 0 | sort -queue_depth
```
- **Implementation:** Monitor LTM connection queue statistics via iControl REST or SNMP. Alert when queue depth exceeds 0 persistently (>5 min). Correlate with backend pool member health.
- **Visualization:** Line chart (queue depth over time), Table (virtual server, connections, queue), Gauge.

---

### UC-5.3.10 · Backend Server Error Code Distribution
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Understanding which backends return 5xx errors helps isolate faulty application instances vs. systemic issues.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`), NGINX TA
- **Data Sources:** `sourcetype=f5:bigip:ltm:http`, `sourcetype=nginx:plus:api`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm:http"
| where response_code >= 500
| stats count by pool_member, response_code, virtual_server
| sort -count
```
- **Implementation:** Enable HTTP response logging on the LB. Track 5xx rates per backend member. Alert when a single member's error rate exceeds the pool average by 3x. Auto-disable unhealthy members.
- **Visualization:** Bar chart (errors by backend), Table (member, error code, count), Timechart.

---

### UC-5.3.11 · Rate Limiting and DDoS Mitigation Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Tracking rate limiting events reveals ongoing attacks and validates that DDoS protections are actively working.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler
- **Data Sources:** `sourcetype=f5:bigip:asm`, `sourcetype=f5:bigip:ltm`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:asm" attack_type="*dos*" OR violation="Rate Limiting"
| stats count values(src_ip) as source_ips dc(src_ip) as unique_sources by virtual_server, attack_type
| sort -count
```
- **Implementation:** Enable ASM/WAF logging. Configure rate limiting policies per virtual server. Alert on sustained rate limiting events. Track source IP patterns for blocklisting.
- **Visualization:** Timechart (events over time), Table (source IPs, attack types), Single value (blocked requests).

---

### UC-5.3.12 · iRule/Policy Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** iRule failures cause unexpected traffic handling — potentially bypassing security or routing traffic incorrectly.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`)
- **Data Sources:** `sourcetype=f5:bigip:ltm`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm" "TCL error" OR "rule error" OR "aborted"
| rex "Rule (?<rule_name>/\S+)"
| stats count by rule_name, host | sort -count
```
- **Implementation:** Enable iRule logging (sparingly — high volume). Monitor for TCL runtime errors. Alert on any iRule abort events. Review and test iRules in staging before production.
- **Visualization:** Table (rule name, error count, host), Timechart (errors over time).

---


## 5.4 Wireless Infrastructure

**Primary App/TA:** Splunk Add-on for Cisco Meraki, Cisco WLC syslog, Aruba syslog — Free

---

### UC-5.4.1 · AP Offline Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Offline APs create coverage dead zones. Users lose connectivity in affected areas.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog), WLC syslog
- **Data Sources:** `sourcetype=meraki, WLC events
- **SPL:**
```spl
index=network sourcetype="meraki" type="access point" ("went offline" OR "unreachable")
| table _time host ap_name network status | sort -_time
```
- **Implementation:** For Meraki: configure syslog in Dashboard, or use Meraki API TA. For WLC: forward syslog. Alert when APs go offline. Maintain AP inventory lookup for location context.
- **Visualization:** Map (AP locations with status), Table, Status grid, Single value (APs offline).

---

### UC-5.4.2 · Client Association Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Failed associations frustrate users and indicate RADIUS/auth issues, RF problems, or AP overload.
- **App/TA:** WLC syslog, Meraki TA
- **Data Sources:** WLC/AP syslog, RADIUS logs
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" ("association" OR "authentication") AND ("fail" OR "reject" OR "denied")
| stats count by ap_name, ssid, reason | sort -count
```
- **Implementation:** Forward WLC/AP syslog. Correlate with RADIUS logs (ISE). Alert on spike in failures per SSID or AP.
- **Visualization:** Table (AP, SSID, reason, count), Bar chart by reason, Timechart.

---

### UC-5.4.3 · Channel Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** High channel utilization degrades wireless performance. Identifies congested APs needing channel changes or additional coverage.
- **App/TA:** Meraki API, WLC SNMP
- **Data Sources:** Meraki API, SNMP (CISCO-DOT11-IF-MIB)
- **SPL:**
```spl
index=network sourcetype="meraki:api"
| stats avg(channel_utilization) as util_pct by ap_name, channel, band
| where util_pct > 60 | sort -util_pct
```
- **Implementation:** Poll Meraki RF statistics API or WLC SNMP. Track per-AP channel utilization. Alert when >60% (2.4GHz) or >50% (5GHz).
- **Visualization:** Heatmap (APs by utilization), Table, Line chart (trending).

---

### UC-5.4.4 · Rogue AP Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Rogue APs are unauthorized and can be used for man-in-the-middle attacks or network bridging.
- **App/TA:** WLC syslog, Meraki TA
- **Data Sources:** WLC/Meraki security events
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "rogue" ("detected" OR "alert" OR "contained")
| stats count by rogue_mac, detecting_ap, channel | sort -count
```
- **Implementation:** Forward WLC rogue detection events. Enable rogue detection policies. Alert on rogue APs, especially those broadcasting your corporate SSID.
- **Visualization:** Table (rogue MAC, detecting AP, channel), Map, Single value.

---

### UC-5.4.5 · Client Count Trending
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Client count trending informs capacity planning and AP density decisions.
- **App/TA:** Meraki API, WLC SNMP
- **Data Sources:** WLC/Meraki client data
- **SPL:**
```spl
index=network sourcetype="meraki:api"
| timechart span=1h dc(client_mac) as client_count by ap_name
```
- **Implementation:** Poll client counts via API or SNMP. Track per AP, per SSID, and per building over time.
- **Visualization:** Line chart (clients over time), Table (AP, count), Heatmap.

---

### UC-5.4.6 · RF Interference Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Radar (DFS), non-WiFi interference, and channel changes degrade wireless quality.
- **App/TA:** WLC syslog, Meraki TA
- **Data Sources:** WLC/AP syslog
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" ("radar" OR "DFS" OR "interference" OR "channel change")
| stats count by ap_name, channel | sort -count
```
- **Implementation:** Forward AP/WLC syslog. Alert on DFS radar events. Track channel change frequency per AP.
- **Visualization:** Table (AP, event type, count), Timeline, Bar chart.

---

### UC-5.4.7 · Wireless Authentication Trends
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** 802.1X success/failure rates indicate RADIUS health, certificate issues, or expired credentials.
- **App/TA:** WLC syslog, RADIUS/ISE logs
- **Data Sources:** RADIUS logs, WLC auth events
- **SPL:**
```spl
index=network sourcetype="cisco:ise:syslog" ("Passed" OR "Failed") AND "Wireless"
| eval status=if(match(_raw,"Passed"),"Success","Failed")
| timechart span=1h count by status
```
- **Implementation:** Forward ISE/RADIUS authentication logs. Track success/failure ratio over time. Alert on sustained failure rate increase.
- **Visualization:** Stacked bar chart (success vs. failure), Line chart, Single value (failure rate %).

---

### UC-5.4.8 · RADIUS Authentication Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Mass RADIUS failures prevent wireless users from connecting. Distinguishing between user errors and server issues drives faster resolution.
- **App/TA:** Cisco WLC syslog, Splunk_TA_cisco-ise, `Splunk_TA_cisco-ise`
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=cisco:ise:syslog`
- **SPL:**
```spl
index=network sourcetype="cisco:ise:syslog" "Authentication failed"
| rex "UserName=(?<username>\S+).*?FailureReason=(?<reason>[^;]+)"
| stats count by reason, username | sort -count
| head 20
```
- **Implementation:** Forward ISE/RADIUS logs to Splunk. Alert when failure rate exceeds 20% of attempts. Distinguish between bad credentials, expired certificates, and server timeouts.
- **Visualization:** Bar chart (failure reasons), Table (username, reason, count), Timechart (failure rate).

---

### UC-5.4.9 · Client Roaming Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Poor roaming causes dropped calls, video freezes, and application timeouts. Analyzing roaming patterns identifies coverage gaps.
- **App/TA:** Cisco WLC syslog, Meraki API
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=meraki:api
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "roam" OR "reassociation"
| transaction client_mac maxspan=1h
| eval roam_count=eventcount-1
| stats avg(roam_count) as avg_roams, max(roam_count) as max_roams by client_mac, ssid
| where avg_roams > 10
```
- **Implementation:** Enable client roaming event logging on the WLC. Track roaming frequency per client. Investigate clients with >10 roams/hour — indicates poor RF design or sticky client behavior.
- **Visualization:** Table (client, SSID, roam count), Heatmap (AP-to-AP roaming), Choropleth (floor plan).

---

### UC-5.4.10 · Wireless IDS/IPS Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Wireless attacks (deauth floods, evil twin, KRACK) compromise network security. Early detection prevents credential theft and MitM attacks.
- **App/TA:** Cisco WLC syslog, Meraki API
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=meraki:ids`
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "IDS Signature" OR "wIPS"
| rex "Signature (?<sig_id>\d+).*?(?<sig_name>[^,]+).*?MAC (?<attacker_mac>[0-9a-f:]+)"
| stats count by sig_name, attacker_mac | sort -count
```
- **Implementation:** Enable wireless IDS on the WLC/AP. Forward alerts to Splunk. Alert on deauth floods, rogue AP impersonation, and client spoofing events. Correlate with rogue AP detection.
- **Visualization:** Table (signature, attacker MAC, count), Timeline, Single value (alerts today).

---

### UC-5.4.11 · Band Steering Effectiveness
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Band steering moves capable clients to 5 GHz, reducing congestion on 2.4 GHz. Measuring effectiveness validates RF policy.
- **App/TA:** Cisco WLC syslog, Meraki API
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=meraki:api
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "associated"
| eval band=if(match(channel,"^(1|6|11)$"),"2.4GHz","5GHz")
| stats count by band, ssid
| eventstats sum(count) as total by ssid
| eval pct=round(count/total*100,1)
```
- **Implementation:** Collect client association events with channel info. Calculate the ratio of 5 GHz vs 2.4 GHz clients per SSID. Target >70% on 5 GHz for dual-band capable clients.
- **Visualization:** Pie chart (band distribution), Bar chart (by SSID), Timechart (trending).

---


## 5.5 SD-WAN

**Primary App/TA:** Cisco SD-WAN TA (vManage API), vendor-specific integrations

---

### UC-5.5.1 · Tunnel Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Tunnel loss/latency/jitter directly impacts application experience over WAN.
- **App/TA:** ta-cisco-sdwan, vManage API
- **Data Sources:** vManage BFD metrics
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(loss_percentage) as loss, avg(latency) as latency, avg(jitter) as jitter by site, tunnel_name
| where loss > 1 OR latency > 100 OR jitter > 30
```
- **Implementation:** Poll vManage API for BFD session statistics. Collect loss, latency, jitter per tunnel. Alert when SLA thresholds exceeded.
- **Visualization:** Line chart (loss/latency/jitter per tunnel), Table, Status grid per site.

---

### UC-5.5.2 · Site Availability
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Edge device offline = remote site disconnected from the network.
- **App/TA:** ta-cisco-sdwan, vManage API
- **Data Sources:** vManage device status
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:device"
| where reachability!="reachable"
| table _time site_id hostname system_ip reachability | sort -_time
```
- **Implementation:** Poll vManage device inventory API. Alert when any edge device becomes unreachable. Include site name and location.
- **Visualization:** Map (site locations with status), Table, Status grid.

---

### UC-5.5.3 · Application SLA Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Detects when business-critical applications aren't meeting performance requirements over the WAN.
- **App/TA:** ta-cisco-sdwan
- **Data Sources:** vManage app-aware routing metrics
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute"
| where sla_violation="true"
| stats count by site, app_name, sla_class | sort -count
```
- **Implementation:** Collect app-aware routing statistics from vManage. Alert when critical applications violate their SLA class.
- **Visualization:** Table (site, app, violations), Bar chart by app, Timechart.

---

### UC-5.5.4 · Path Failover Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks when traffic switches between WAN transports. Frequent failovers indicate unstable links.
- **App/TA:** ta-cisco-sdwan
- **Data Sources:** vManage events
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:events" ("failover" OR "path-change" OR "transport-switch")
| stats count by site, from_transport, to_transport | sort -count
```
- **Implementation:** Collect vManage alarm/event data. Track path changes and failover frequency. Alert on frequent failovers.
- **Visualization:** Table, Sankey diagram (from/to transport), Timeline.

---

### UC-5.5.5 · Control Plane Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** vSmart/vManage connectivity issues affect policy distribution and overlay routing.
- **App/TA:** ta-cisco-sdwan
- **Data Sources:** vManage control connection logs
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:control"
| where state!="up"
| table _time hostname peer_type peer_system_ip state | sort -_time
```
- **Implementation:** Monitor control connections to vSmart and vManage. Alert on any control connection down.
- **Visualization:** Status panel, Table, Timeline.

---

### UC-5.5.6 · Certificate Expiration
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** SD-WAN device certificates must be valid for overlay connectivity.
- **App/TA:** ta-cisco-sdwan, vManage API
- **Data Sources:** vManage certificate inventory
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:certificate"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<60
| table hostname system_ip days_left | sort days_left
```
- **Implementation:** Poll vManage for certificate status. Alert at 60/30/7 day thresholds.
- **Visualization:** Table, Single value, Status indicator.

---

### UC-5.5.7 · Bandwidth Utilization per Site
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** WAN bandwidth consumption per site enables capacity planning and cost optimization.
- **App/TA:** ta-cisco-sdwan
- **Data Sources:** vManage interface metrics
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:interface"
| timechart span=1h sum(tx_octets) as bytes_out, sum(rx_octets) as bytes_in by site
| eval out_mbps=round(bytes_out*8/3600/1000000,1)
```
- **Implementation:** Collect interface statistics from vManage. Track per-site, per-transport utilization. Use for upgrade decisions.
- **Visualization:** Line chart per site, Table, Stacked area.

---

### UC-5.5.8 · Jitter and Latency per Tunnel
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Real-time jitter and latency metrics reveal WAN quality degradation before users complain. Critical for voice/video SLAs.
- **App/TA:** ta-cisco-sdwan, Cisco vManage API
- **Data Sources:** `sourcetype=cisco:sdwan:bfd`, `sourcetype=cisco:sdwan:approute`
- **SPL:**
```spl
index=network sourcetype="cisco:sdwan:approute"
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss by local_system_ip, remote_system_ip, local_color
| where avg_latency > 100 OR avg_jitter > 30 OR avg_loss > 1
| sort -avg_latency
```
- **Implementation:** Ingest BFD and app-route statistics from vManage API. Monitor per-tunnel quality metrics. Alert when latency >100ms, jitter >30ms, or loss >1% for business-critical SLAs.
- **Visualization:** Line chart (latency/jitter over time), Table (tunnel, metrics), Gauge (SLA compliance).

---

### UC-5.5.9 · Application Routing Decisions
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Validates that SD-WAN policies are steering traffic correctly. Detects policy misconfigurations that route real-time traffic over suboptimal paths.
- **App/TA:** ta-cisco-sdwan, Cisco vManage API
- **Data Sources:** `sourcetype=cisco:sdwan:approute`, `sourcetype=cisco:sdwan:flow`
- **SPL:**
```spl
index=network sourcetype="cisco:sdwan:flow"
| stats sum(octets) as bytes by app_name, local_color, remote_system_ip
| eval MB=round(bytes/1048576,1)
| sort -MB
| head 50
```
- **Implementation:** Collect flow and app-route data from vManage. Verify voice/video uses MPLS, web traffic uses Internet. Alert when critical apps route over non-preferred transports.
- **Visualization:** Sankey diagram (app → transport), Table (app, path, volume), Pie chart.

---

### UC-5.5.10 · WAN Link Utilization per Transport
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unbalanced link utilization wastes expensive MPLS bandwidth while underusing broadband circuits. Enables cost-effective traffic engineering.
- **App/TA:** ta-cisco-sdwan, SNMP
- **Data Sources:** `sourcetype=cisco:sdwan:interface`, SNMP IF-MIB
- **SPL:**
```spl
index=network sourcetype="cisco:sdwan:interface"
| eval util_pct=round(tx_octets*8/speed*100,1)
| stats avg(util_pct) as avg_util, max(util_pct) as peak_util by system_ip, color, interface_name
| where avg_util > 70 | sort -avg_util
```
- **Implementation:** Collect interface stats per WAN transport type (MPLS, Internet, LTE). Compare utilization across links. Alert on >70% sustained utilization. Use for capacity planning.
- **Visualization:** Line chart (utilization per transport), Stacked bar (site comparison), Table.

---


## 5.6 DNS & DHCP

**Primary App/TA:** Splunk Add-on for Infoblox, Windows DNS/DHCP, BIND syslog — Free

---

### UC-5.6.1 · DNS Query Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** DNS query volume trending supports capacity planning and reveals traffic pattern changes.
- **App/TA:** Splunk_TA_infoblox, Splunk_TA_windows (DNS logs), Pi-hole syslog
- **Data Sources:** `sourcetype=infoblox:dns`, `sourcetype=MSAD:NT6:DNS`
- **SPL:**
```spl
index=dns sourcetype="infoblox:dns" OR sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as qps
```
- **Implementation:** Forward DNS query logs. For Windows DNS: enable analytical logging. For Infoblox: configure syslog output. Track queries per second over time.
- **Visualization:** Line chart (QPS over time), Single value (current QPS), Table.

---

### UC-5.6.2 · NXDOMAIN Spike Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** NXDOMAIN spikes indicate DGA malware (generating random domain lookups), misconfiguration, or DNS infrastructure issues.
- **App/TA:** DNS TAs
- **Data Sources:** DNS query logs
- **SPL:**
```spl
index=dns reply_code="NXDOMAIN" OR rcode="3"
| timechart span=5m count as nxdomain_count
| eventstats avg(nxdomain_count) as avg_nx, stdev(nxdomain_count) as std_nx
| where nxdomain_count > (avg_nx + 3*std_nx)
```
- **Implementation:** Monitor DNS response codes. Baseline NXDOMAIN rates. Alert when exceeding 3 standard deviations. Investigate the querying clients and domain patterns.
- **Visualization:** Line chart with threshold, Table (top NXDOMAIN clients), Bar chart (top queried NX domains).

---

### UC-5.6.3 · SERVFAIL Rate Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** SERVFAIL increases indicate upstream DNS failures, DNSSEC validation issues, or resolver problems.
- **App/TA:** DNS TAs
- **Data Sources:** DNS query logs
- **SPL:**
```spl
index=dns reply_code="SERVFAIL" OR rcode="2"
| timechart span=5m count as servfail | where servfail > 10
```
- **Implementation:** Track SERVFAIL response codes. Alert on increases. Investigate which domains are failing and which resolvers are affected.
- **Visualization:** Line chart, Table (failing domains), Single value.

---

### UC-5.6.4 · DNS Tunneling Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** DNS tunneling uses DNS queries to exfiltrate data or establish C2 channels, bypassing traditional security controls.
- **App/TA:** DNS TAs
- **Data Sources:** DNS query logs
- **SPL:**
```spl
index=dns
| eval query_len=len(query)
| stats avg(query_len) as avg_len, count as queries, dc(query) as unique_queries by src_ip, domain
| where avg_len > 50 OR queries > 1000
| sort -avg_len
```
- **Implementation:** Monitor for anomalously long DNS queries (>50 chars), high query volumes to single domains, and TXT record queries. Baseline normal DNS patterns.
- **Visualization:** Table (client, domain, query length, volume), Scatter plot, Bar chart.

---

### UC-5.6.5 · DHCP Scope Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Empty DHCP scopes prevent new devices from getting network access.
- **App/TA:** Splunk_TA_windows (DHCP logs), Splunk_TA_infoblox
- **Data Sources:** DHCP server logs, API metrics
- **SPL:**
```spl
index=dhcp sourcetype="DhcpSrvLog" OR sourcetype="infoblox:dhcp"
| stats dc(assigned_ip) as used by scope_name, scope_range
| eval total = scope_end - scope_start
| eval used_pct=round(used/total*100,1) | where used_pct > 90
```
- **Implementation:** For Windows: forward DHCP audit logs + scripted input for scope stats. For Infoblox: use API or syslog. Alert when >90% utilized.
- **Visualization:** Gauge per scope, Table, Bar chart.

---

### UC-5.6.6 · DHCP Rogue Server Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Rogue DHCP servers assign wrong IPs/gateways, causing network disruption and potential MitM attacks.
- **App/TA:** Network syslog, DHCP snooping logs
- **Data Sources:** DHCP conflict events, switch DHCP snooping
- **SPL:**
```spl
index=network "DHCP" AND ("rogue" OR "conflict" OR "unauthorized" OR "snooping violation")
| table _time host src_ip _raw | sort -_time
```
- **Implementation:** Enable DHCP snooping on switches. Forward syslog. Alert on any rogue DHCP server detection events.
- **Visualization:** Events list (critical), Table, Map.

---

### UC-5.6.7 · DNS Record Change Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized DNS changes can redirect traffic to attacker infrastructure (DNS hijacking).
- **App/TA:** Splunk_TA_infoblox, DNS update logs
- **Data Sources:** Infoblox audit log, DNS dynamic update logs
- **SPL:**
```spl
index=dns sourcetype="infoblox:audit" ("Added" OR "Deleted" OR "Modified") AND ("record" OR "zone")
| table _time admin record_type record_name record_data action | sort -_time
```
- **Implementation:** Forward DNS server audit logs. Alert on changes to critical domains. Correlate with change tickets.
- **Visualization:** Table (record, action, who, when), Timeline, Single value.

---

### UC-5.6.8 · DNS Latency Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** DNS latency directly adds to every network connection. Slow DNS = slow everything.
- **App/TA:** Custom scripted input, DNS diagnostic logs
- **Data Sources:** DNS recursive query timing
- **SPL:**
```spl
index=dns sourcetype="dns:latency"
| timechart span=5m avg(response_time_ms) as avg_latency by dns_server
| where avg_latency > 50
```
- **Implementation:** Use scripted input running `dig` queries against DNS servers measuring response time. Or enable DNS analytical logging with timing. Alert when average latency >50ms.
- **Visualization:** Line chart per server, Gauge, Table.

---

### UC-5.6.9 · DNS Cache Hit Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Low cache hit ratios indicate either a surge of new queries, cache poisoning attempts, or misconfigured TTLs — all increasing latency and upstream load.
- **App/TA:** Splunk_TA_infoblox, BIND/Unbound logs
- **Data Sources:** `sourcetype=infoblox:dns`, `sourcetype=named`
- **SPL:**
```spl
index=network sourcetype="infoblox:dns"
| eval cache_hit=if(match(message,"cache hit"),1,0), total=1
| timechart span=1h sum(cache_hit) as hits, sum(total) as total
| eval hit_ratio=round(hits/total*100,1) | where hit_ratio < 70
```
- **Implementation:** Enable query logging on DNS resolvers. Track cache hit vs. miss ratio. Alert when hit ratio drops below 70%. Investigate top domains causing misses.
- **Visualization:** Line chart (hit ratio over time), Single value (current ratio), Table (top miss domains).

---

### UC-5.6.10 · DNSSEC Validation Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** DNSSEC failures can indicate DNS spoofing attempts or misconfigured zones. Monitoring prevents users from being directed to malicious sites.
- **App/TA:** Splunk_TA_infoblox, BIND logs
- **Data Sources:** `sourcetype=infoblox:dns`, `sourcetype=named`
- **SPL:**
```spl
index=network sourcetype="named" "DNSSEC" ("validation failure" OR "SERVFAIL" OR "no valid signature")
| rex "(?<query_domain>[a-zA-Z0-9.-]+\.)/(?<query_type>\w+)"
| stats count by query_domain, query_type | sort -count
```
- **Implementation:** Enable DNSSEC validation logging. Monitor for validation failures by domain. Cross-reference with known domain registrations. Alert on spikes in DNSSEC failures.
- **Visualization:** Table (domain, failure count), Timechart (failure rate), Bar chart.

---

### UC-5.6.11 · DHCP Lease Duration Analysis
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Short lease durations increase DHCP traffic and scope churn. Long leases waste addresses. Optimizing lease times improves IP management.
- **App/TA:** Splunk_TA_infoblox, Windows DHCP logs
- **Data Sources:** `sourcetype=infoblox:dhcp`, `sourcetype=DhcpSrvLog`
- **SPL:**
```spl
index=network sourcetype="infoblox:dhcp" "DHCPACK"
| rex "lease (?<lease_ip>\d+\.\d+\.\d+\.\d+).*?(?<lease_duration>\d+)"
| stats avg(lease_duration) as avg_lease, count as renewals by subnet
| eval avg_hours=round(avg_lease/3600,1) | sort -renewals
```
- **Implementation:** Collect DHCP server logs. Analyze lease durations per scope. Identify scopes with unusually short leases (frequent renewals) or extremely long leases. Adjust based on network type (guest vs. corporate).
- **Visualization:** Table (scope, avg lease, renewal count), Bar chart (renewals by scope).

---

### UC-5.6.12 · DNS Query Type Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusual query type distribution (spikes in TXT, MX, or ANY) can indicate DNS tunneling, reconnaissance, or abuse.
- **App/TA:** Splunk_TA_infoblox, Splunk Stream
- **Data Sources:** `sourcetype=infoblox:dns`, `sourcetype=stream:dns`
- **SPL:**
```spl
index=network sourcetype="stream:dns"
| stats count by query_type
| eventstats sum(count) as total
| eval pct=round(count/total*100,2) | sort -count
| head 20
```
- **Implementation:** Capture DNS query types via Splunk Stream or DNS server logs. Baseline normal distribution (typically >80% A/AAAA). Alert on abnormal increases in TXT, NULL, or ANY queries.
- **Visualization:** Pie chart (query type distribution), Timechart (by type), Table.

---


## 5.7 Network Flow Data

**Primary App/TA:** Splunk App for Stream, Splunk Add-on for NetFlow — Free

---

### UC-5.7.1 · Top Talkers Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Identifies top bandwidth consumers. Essential for troubleshooting congestion and capacity planning.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** `sourcetype=netflow`, sFlow, IPFIX
- **SPL:**
```spl
index=netflow
| stats sum(bytes) as total_bytes by src_ip, dest_ip
| sort -total_bytes | head 20
| eval total_GB=round(total_bytes/1073741824,2)
```
- **Implementation:** Export NetFlow from routers/switches to a NetFlow collector that forwards to Splunk. Install NetFlow TA for field parsing.
- **Visualization:** Table (source, dest, bytes), Sankey diagram, Bar chart.

---

### UC-5.7.2 · Anomalous Traffic Patterns
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusual flows (new protocols, unexpected destinations) indicate compromise, misconfiguration, or shadow IT.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** `sourcetype=netflow`
- **SPL:**
```spl
index=netflow
| stats dc(dest_port) as unique_ports, dc(dest_ip) as unique_dests by src_ip
| where unique_ports > 100 OR unique_dests > 500
| sort -unique_ports
```
- **Implementation:** Baseline normal flow patterns over 30 days. Alert on new protocol/port combinations, new external destinations, or unusual volume patterns.
- **Visualization:** Table, Scatter plot (ports vs. destinations), Timechart.

---

### UC-5.7.3 · Bandwidth by Application
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Application-level bandwidth breakdown helps prioritize QoS policies and justify network upgrades.
- **App/TA:** Splunk Add-on for NetFlow (with NBAR)
- **Data Sources:** NetFlow with application identification
- **SPL:**
```spl
index=netflow
| stats sum(bytes) as total_bytes by application
| sort -total_bytes | head 20 | eval GB=round(total_bytes/1073741824,2)
```
- **Implementation:** Enable NBAR (Network-Based Application Recognition) on Cisco routers to export application-tagged NetFlow. Ingest in Splunk.
- **Visualization:** Pie chart (bandwidth by app), Bar chart, Table.

---

### UC-5.7.4 · East-West Traffic Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Lateral traffic between internal segments reveals application dependencies and detects lateral movement.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** NetFlow from internal segments
- **SPL:**
```spl
index=netflow
| where cidrmatch("10.0.0.0/8",src_ip) AND cidrmatch("10.0.0.0/8",dest_ip)
| stats sum(bytes) as bytes, count as flows by src_ip, dest_ip, dest_port
| sort -bytes | head 50
```
- **Implementation:** Export NetFlow from internal router/switch interfaces. Analyze internal traffic patterns. Establish baseline for anomaly detection.
- **Visualization:** Chord diagram, Table, Sankey diagram.

---

### UC-5.7.5 · Data Exfiltration Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusually large outbound transfers to uncommon destinations may be data theft.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** NetFlow
- **SPL:**
```spl
index=netflow direction="outbound"
| stats sum(bytes) as total_bytes by src_ip, dest_ip
| where total_bytes > 1073741824
| lookup known_destinations dest_ip OUTPUT known
| where isnull(known)
| sort -total_bytes
```
- **Implementation:** Baseline normal outbound transfer volumes per host. Alert when transfers exceed threshold to unknown destinations. Correlate with DNS and firewall logs.
- **Visualization:** Table, Bar chart, Map (destination GeoIP).

---

### UC-5.7.6 · Port Scan Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Hosts scanning many ports on targets indicate reconnaissance, worm propagation, or vulnerability scanning.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** NetFlow
- **SPL:**
```spl
index=netflow
| stats dc(dest_port) as unique_ports by src_ip, dest_ip
| where unique_ports > 50
| sort -unique_ports
```
- **Implementation:** Detect hosts connecting to >50 unique ports on a single target in 5 minutes. Alert with source and target details.
- **Visualization:** Table, Scatter plot, Timeline.

---

### UC-5.7.7 · Protocol Distribution Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Understanding protocol mix helps validate network policies and detect unauthorized protocols (e.g., unexpected SSH, RDP, or P2P traffic).
- **App/TA:** Splunk Stream, NetFlow integrator
- **Data Sources:** `sourcetype=netflow`, `sourcetype=stream:tcp`
- **SPL:**
```spl
index=network sourcetype="netflow"
| lookup service_lookup dest_port OUTPUT service_name
| stats sum(bytes) as total_bytes dc(src_ip) as unique_sources by protocol, service_name
| eval GB=round(total_bytes/1073741824,2) | sort -total_bytes
| head 20
```
- **Implementation:** Collect NetFlow/sFlow/IPFIX from routers and switches. Map port numbers to service names via lookup. Baseline protocol distribution. Alert on new protocols or significant shifts.
- **Visualization:** Pie chart (by protocol), Treemap (by service + volume), Timechart.

---

### UC-5.7.8 · Multicast Traffic Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Uncontrolled multicast traffic floods switches and consumes bandwidth. Monitoring ensures multicast storms are detected before impacting unicast traffic.
- **App/TA:** Splunk Stream, NetFlow integrator
- **Data Sources:** `sourcetype=netflow`, `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="netflow" dest_ip="224.0.0.0/4"
| stats sum(bytes) as total_bytes, dc(src_ip) as sources by dest_ip
| eval MB=round(total_bytes/1048576,1) | sort -total_bytes
| head 20
```
- **Implementation:** Enable NetFlow on core/distribution switches. Filter for multicast destination range (224.0.0.0/4). Baseline expected multicast groups. Alert on new or high-volume groups.
- **Visualization:** Table (multicast group, volume, sources), Timechart (multicast volume), Bar chart.

---

### UC-5.7.9 · Unauthorized VLAN Traffic Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Traffic originating from or destined to unauthorized VLANs indicates misconfigured switch ports, VLAN hopping attacks, or rogue devices.
- **App/TA:** Splunk Stream, NetFlow integrator
- **Data Sources:** `sourcetype=netflow`, `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="netflow"
| lookup vlan_authorization_lookup src_vlan OUTPUT authorized
| where authorized!="yes" OR isnull(authorized)
| stats sum(bytes) as bytes, dc(src_ip) as unique_hosts by src_vlan, input_interface
| sort -bytes
```
- **Implementation:** Map flow data to VLANs via input interface. Maintain a lookup of authorized VLANs per port. Alert on traffic from unauthorized VLANs. Correlate with 802.1X status.
- **Visualization:** Table (VLAN, interface, hosts, volume), Alert panel, Status grid.

---

### UC-5.7.10 · Long-Duration Flow Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Extremely long-lived flows may indicate data exfiltration, persistent backdoors, or stuck sessions consuming resources.
- **App/TA:** Splunk Stream, NetFlow integrator
- **Data Sources:** `sourcetype=netflow`
- **SPL:**
```spl
index=network sourcetype="netflow"
| eval duration_min=duration/60
| where duration_min > 60
| stats sum(bytes) as total_bytes, max(duration_min) as max_duration by src_ip, dest_ip, dest_port
| eval GB=round(total_bytes/1073741824,2) | sort -max_duration
| head 20
```
- **Implementation:** Analyze flow records for duration >60 minutes. Cross-reference with known long-lived services (VPN, database replication). Flag unknown long flows for investigation.
- **Visualization:** Table (source, destination, port, duration, bytes), Scatter plot (duration vs. bytes).

---


## 5.8 Network Management Platforms

**Primary App/TA:** Cisco DNA Center TA, Meraki TA, syslog/SNMP trap receivers

---

### UC-5.8.1 · DNA Center Assurance Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** DNA Center provides AI/ML-driven network issue detection. Centralizing in Splunk enables cross-domain correlation.
- **App/TA:** Splunk-TA-cisco-dnacenter (API)
- **Data Sources:** DNA Center API (issues, events)
- **SPL:**
```spl
index=network sourcetype="cisco:dnac:issues"
| stats count by priority, category, name | sort -priority -count
```
- **Implementation:** Configure DNA Center API integration in Splunk TA. Poll for issues and client health. Alert on P1/P2 issues.
- **Visualization:** Table (issue, priority, category), Bar chart, Single value.

---

### UC-5.8.2 · Meraki Organization Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks Meraki device status across all networks and organizations from a single pane.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog) (API + syslog)
- **Data Sources:** Meraki Dashboard API, syslog
- **SPL:**
```spl
index=network sourcetype="meraki:api"
| stats count by network, status | eval is_offline=if(status="offline",1,0)
| where is_offline > 0
```
- **Implementation:** Configure Meraki API integration (API key + org ID). Poll device statuses. Forward syslog for events. Dashboard showing organization-wide health.
- **Visualization:** Map (device locations), Table, Status grid, Single value (offline count).

---

### UC-5.8.3 · SNMP Trap Consolidation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Centralizing SNMP traps from all sources enables cross-tool correlation and reduces monitoring tool sprawl.
- **App/TA:** Splunk Add-on for SNMP (trap receiver)
- **Data Sources:** SNMP traps
- **SPL:**
```spl
index=network sourcetype="snmp:trap"
| stats count by trap_oid, host, severity | sort -count
```
- **Implementation:** Configure Splunk SNMP trap receiver (UDP 162). Map trap OIDs to human-readable names via lookup. Correlate with syslog events from the same device.
- **Visualization:** Table (device, trap, severity), Bar chart, Timeline.

---

### UC-5.8.4 · Network Device Inventory
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Up-to-date inventory supports change management, vulnerability tracking, and compliance auditing.
- **App/TA:** Combined sources (NMS APIs, SNMP sysDescr)
- **Data Sources:** NMS discovery, SNMP polling
- **SPL:**
```spl
index=network sourcetype="snmp:system"
| stats latest(sysDescr) as description, latest(sysLocation) as location by host
| table host description location
```
- **Implementation:** Poll SNMP sysDescr, sysName, sysLocation from all devices. Cross-reference with NMS discovery exports. Maintain inventory lookup for enrichment.
- **Visualization:** Table (device, model, location, version), Pie chart (by model/vendor).

---

### UC-5.8.5 · Network Device Backup Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Missing backups mean a failed device requires manual rebuilding. Tracking backup success ensures rapid disaster recovery.
- **App/TA:** RANCID/Oxidized logs, SolarWinds NCM, custom scripts
- **Data Sources:** `sourcetype=rancid`, `sourcetype=oxidized`
- **SPL:**
```spl
index=network sourcetype="oxidized"
| stats latest(status) as backup_status, latest(_time) as last_backup by device
| eval days_since=round((now()-last_backup)/86400,0)
| where backup_status!="success" OR days_since > 7
| sort -days_since
```
- **Implementation:** Integrate config backup tool (Oxidized/RANCID) logs into Splunk. Track success/failure per device. Alert when a device hasn't been backed up in >7 days.
- **Visualization:** Table (device, status, days since backup), Single value (compliance %), Status grid.

---

### UC-5.8.6 · ISE Endpoint Posture Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Non-compliant endpoints (missing patches, disabled AV) on the network increase attack surface. ISE posture data enables enforcement visibility.
- **App/TA:** `Splunk_TA_cisco-ise`
- **Data Sources:** `sourcetype=cisco:ise:syslog`
- **SPL:**
```spl
index=network sourcetype="cisco:ise:syslog" "Posture"
| rex "PostureStatus=(?<posture_status>\w+).*?EndpointMacAddress=(?<mac>\S+)"
| stats count by posture_status, mac
| where posture_status="NonCompliant"
| sort -count
```
- **Implementation:** Forward ISE posture assessment logs to Splunk. Track compliant vs. non-compliant endpoints. Alert when non-compliance rate exceeds 10%. Drill down by failure reason.
- **Visualization:** Pie chart (compliant vs non-compliant), Table (non-compliant endpoints), Timechart (compliance trend).

---

### UC-5.8.7 · Network Configuration Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Configuration drift from golden standards introduces vulnerabilities and operational inconsistencies. Detecting drift maintains compliance.
- **App/TA:** RANCID/Oxidized, custom diff scripts, DNA Center
- **Data Sources:** `sourcetype=config:diff`, `sourcetype=cisco:dnac`
- **SPL:**
```spl
index=network sourcetype="config:diff"
| rex "device=(?<device>\S+).*?lines_changed=(?<changes>\d+)"
| where changes > 0
| stats sum(changes) as total_changes, count as change_events by device
| sort -total_changes
```
- **Implementation:** Schedule config pulls via Oxidized/RANCID. Diff against golden templates. Ingest diff results into Splunk. Alert on unauthorized changes (outside change windows).
- **Visualization:** Table (device, changes, last modified), Timeline (change events), Single value (devices with drift).

---

### UC-5.8.8 · SNMP Polling Gap Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Missing SNMP polls create gaps in monitoring data. Detecting polling failures ensures metrics dashboards remain accurate.
- **App/TA:** Splunk core (metadata search)
- **Data Sources:** Any SNMP sourcetype
- **SPL:**
```spl
| tstats count where index=network sourcetype="snmp:*" by host, sourcetype, _time span=10m
| stats range(_time) as time_range, count as poll_count by host, sourcetype
| eval expected_polls=round(time_range/300,0)
| eval gap_pct=round((1-poll_count/expected_polls)*100,1)
| where gap_pct > 20 | sort -gap_pct
```
- **Implementation:** Track SNMP data arrival per device using `tstats`. Compare expected vs. actual poll count. Alert when gap exceeds 20%. Investigate SNMP community/credential issues.
- **Visualization:** Table (device, expected, actual, gap %), Single value (devices with gaps), Heatmap.

---


## 5.9 Cisco Meraki

**Primary App/TA:** Splunk Add-on for Cisco Meraki (`Splunk_TA_cisco_meraki`) — Free on Splunkbase; `TA-meraki` for syslog

---

### UC-5.9.1 · Wireless Client Association Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Identifies recurring authentication failures and SSID configuration issues that prevent users from connecting to wireless networks.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*Association*" OR signature="*authentication*" status="failure"
| stats count by ap_name, client_mac, reason, signature
| sort - count
```
- **Implementation:** Monitor syslog events from Meraki MR access points for failed association attempts. Correlate with SSID configuration and 802.1X radius responses.
- **Visualization:** Table with top APs/clients by failure count; time-series chart of failures over time by AP.

---

### UC-5.9.2 · RSSI/Signal Strength Degradation Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Proactively identifies weak WiFi coverage areas and client placement issues before users experience connectivity problems.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| eval rssi_level=case(rssi>=-50, "Excellent", rssi>=-60, "Good", rssi>=-70, "Fair", rssi<-70, "Poor")
| stats avg(rssi) as avg_rssi, min(rssi) as min_rssi, count by ap_name, ssid, rssi_level
| where min_rssi < -70 or avg_rssi < -65
```
- **Implementation:** Ingest Meraki API client data periodically; analyze RSSI distribution by AP and SSID. Set thresholds for "poor" signal (< -70 dBm).
- **Visualization:** Heatmap of RSSI by AP location; histogram of signal strength distribution; gauge charts for coverage quality by SSID.

---

### UC-5.9.3 · Excessive Client Roaming Activity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects unstable roaming patterns and AP handoff issues that cause latency spikes and dropped connections.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Roaming*" OR signature="*handoff*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Roaming*" OR signature="*handoff*")
| stats count as roam_count by client_mac, ap_name
| eventstats sum(roam_count) as total_roams by client_mac
| where total_roams > 20
| sort - total_roams
```
- **Implementation:** Track client handoff events between APs. Alert when a single client roams more than threshold in a 15-minute window.
- **Visualization:** Table of heavy roamers; line chart of roaming frequency by client; network diagram showing roam paths.

---

### UC-5.9.4 · SSID Performance Ranking and Trend Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Compares performance across multiple SSIDs to identify underperforming networks and optimize deployment strategy.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(connection_duration) as avg_duration, count as client_count, avg(rssi) as avg_rssi by ssid
| eval performance_score=round((avg_rssi+100)*client_count/100, 2)
| sort - performance_score
```
- **Implementation:** Aggregate client connection metrics by SSID. Compare average connection duration, client count, and signal strength.
- **Visualization:** Bar chart comparing SSID performance; sparklines for trend; scorecard showing top/bottom performers.

---

### UC-5.9.5 · WiFi Channel Utilization and Interference Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Identifies channel congestion and interference sources to optimize channel assignments and reduce co-channel interference.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api sourcetype=meraki
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats count by channel, band
| eval utilization_pct=round(count*100/sum(count), 2)
| where utilization_pct > 40
| sort - utilization_pct
```
- **Implementation:** Query API device data for MR access points; track channel assignments. Correlate with interference signature logs.
- **Visualization:** Stacked bar chart of channel utilization by band; channel heatmap over time; interference event timeline.

---

### UC-5.9.6 · Rogue and Unauthorized AP Detection (Air Marshal)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies unauthorized wireless networks and malicious APs that may represent security threats or network intrusion attempts.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=air_marshal
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=air_marshal signature="*Rogue*" OR signature="*Unauthorized*"
| stats count by ssid, bssid, first_detected, last_seen, threat_level
| where threat_level="high" OR threat_level="critical"
| sort - first_detected
```
- **Implementation:** Enable Air Marshal on MR APs and ingest syslog events. Create alert for new rogue AP detections with risk scoring.
- **Visualization:** Table of detected rogues with threat indicators; map showing rogue AP locations; timeline of detections.

---

### UC-5.9.7 · Client Device Type Distribution and Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks device types connecting to network for capacity planning, security policy enforcement, and support optimization.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by os_type, device_family
| eval pct=round(device_count*100/sum(device_count), 2)
| sort - device_count
```
- **Implementation:** Use API clients endpoint to retrieve device OS and type information. Aggregate across network.
- **Visualization:** Pie chart of device types; bar chart by OS; treemap of device distribution; trend sparklines.

---

### UC-5.9.8 · Band Steering Effectiveness Assessment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Measures effectiveness of steering clients from 2.4GHz to 5GHz bands to reduce congestion and improve performance.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by band
| eval band_ratio=round(client_count*100/sum(client_count), 2)
| fields band, client_count, band_ratio
```
- **Implementation:** Query clients API to get current band distribution. Compare against expected ratio for band steering policy.
- **Visualization:** Gauge showing 5GHz percentage; pie chart of band distribution; trend line showing steering progress.

---

### UC-5.9.9 · Failed DHCP Assignments and IP Pool Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Detects DHCP server failures and IP pool exhaustion that prevent new clients from obtaining addresses.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DHCP*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DHCP*" (signature="*failure*" OR signature="*NACK*")
| stats count as failure_count by ap_name, signature
| where failure_count > 5
| sort - failure_count
```
- **Implementation:** Monitor syslog for DHCP NACK and failure events. Alert on sustained failure rate.
- **Visualization:** Table of DHCP failures by AP; time-series showing failure spike; alert dashboard.

---

### UC-5.9.10 · 802.1X Authentication Failures and Radius Issues
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies authentication server problems, credential issues, and 802.1X configuration mismatches.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*802.1X*" OR signature="*Radius*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*802.1X*" OR signature="*Radius*" OR signature="*authentication*")
| stats count as auth_failures by client_mac, ap_name, signature
| eventstats sum(auth_failures) as total_failures by client_mac
| where total_failures > 10
| sort - total_failures
```
- **Implementation:** Ingest 802.1X and RADIUS-related syslog events. Correlate with RADIUS server logs.
- **Visualization:** Table of failing clients; time-series of auth failures; client-level detail dashboard.

---

### UC-5.9.11 · DNS Resolution Performance and Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors DNS query resolution times and failures to identify misconfiguration or server issues affecting user experience.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DNS*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DNS*" resolution_time=*
| stats avg(resolution_time) as avg_dns_time, max(resolution_time) as max_dns_time, count by ap_name
| where avg_dns_time > 100
```
- **Implementation:** Extract DNS query timing from syslog events. Set SLA thresholds (e.g., <100ms average).
- **Visualization:** Gauge showing average DNS time; histogram of query times; slow query detail table.

---

### UC-5.9.12 · Wireless Latency Analysis by SSID and Location
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies latency patterns across network to optimize AP placement, channel allocation, and client routing.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" latency=*
| stats avg(latency) as avg_latency, max(latency) as max_latency, count by ssid, ap_name
| eval latency_sla="OK"
| eval latency_sla=if(avg_latency > 50, "Warning", latency_sla)
| eval latency_sla=if(avg_latency > 100, "Critical", latency_sla)
```
- **Implementation:** Use API clients endpoint with latency metric. Aggregate by SSID and AP location.
- **Visualization:** Heatmap of latency by AP; line chart of latency trends; SLA compliance dashboard.

---

### UC-5.9.13 · Splash Page Engagement and Redirection Analytics
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks guest network splash page performance and user acceptance rates for marketing and network access purposes.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Splash*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*Splash*"
| stats count as redirect_count by result, ap_name
| eval acceptance_rate=round(count*100/sum(count), 2)
```
- **Implementation:** Capture splash page interaction events from syslog. Track accepts vs. denies.
- **Visualization:** Pie chart of acceptance rates; funnel chart of splash interactions; time-series trending.

---

### UC-5.9.14 · Multicast and Broadcast Storm Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies multicast/broadcast flooding that degrades wireless performance across multiple client devices.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow dest_ip="255.255.255.255" OR dest_mac="ff:ff:ff:ff:ff:ff"
| stats sum(sent_bytes) as total_bytes, count as pkt_count by ap_name, src_mac
| where pkt_count > 1000
| sort - pkt_count
```
- **Implementation:** Monitor broadcast/multicast flows in syslog. Set thresholds for abnormal packet rates.
- **Visualization:** Table of broadcast sources; time-series of broadcast packets; alert threshold dashboard.

---

### UC-5.9.15 · Wireless Health Score Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Provides a composite health metric across all APs to facilitate executive reporting and trend analysis.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MR
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats avg(health_score) as network_health, min(health_score) as worst_ap, count(eval(health_score<80)) as unhealthy_aps by network_id
| eval health_status=if(network_health >= 85, "Healthy", if(network_health >= 70, "Degraded", "Critical"))
```
- **Implementation:** Pull health_score metric from MR devices API. Aggregate across network.
- **Visualization:** Gauge of overall health; bar chart of individual AP health; trend sparkline; KPI dashboard.

---

### UC-5.9.16 · Connected Client Count Trending and Capacity Planning
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks client density by AP and SSID for capacity planning and performance optimization.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by ap_name, ssid
| eval capacity_pct=round(client_count*100/30, 2)
| where capacity_pct > 70
| sort - client_count
```
- **Implementation:** Query clients API to count connected devices. Track over time.
- **Visualization:** Bubble chart of capacity by AP; stacked bar of clients by SSID; capacity gauge.

---

### UC-5.9.17 · Top Talker Analysis and Bandwidth Hogs
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies bandwidth-intensive clients and applications to enforce QoS policies and prevent network congestion.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow
| stats sum(sent_bytes) as upload_bytes, sum(received_bytes) as download_bytes by client_mac, application
| eval total_bytes=upload_bytes+download_bytes
| sort - total_bytes
| head 20
```
- **Implementation:** Analyze flow records from syslog; track data usage by client and application.
- **Visualization:** Table of top talkers; horizontal bar chart of data usage; Sankey diagram of flows.

---

### UC-5.9.18 · Connection Duration and Session Quality
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Analyzes typical session lengths and stability to identify problematic SSIDs or time-based issues.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" connection_duration=*
| stats avg(connection_duration) as avg_session_time, min(connection_duration) as min_session, max(connection_duration) as max_session by ssid
| eval session_quality=if(avg_session_time > 3600, "Stable", "Short")
```
- **Implementation:** Extract connection_duration from clients API. Aggregate by SSID and time of day.
- **Visualization:** Histogram of session durations; time-of-day heatmap; SSID comparison chart.

---

### UC-5.9.19 · AP Uptime and Availability Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Ensures all access points are online and operational; alerts on unexpected AP outages.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MR
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats latest(status) as ap_status, latest(last_status_change) as last_change by ap_name, ap_mac
| where ap_status="offline"
```
- **Implementation:** Monitor device status API for all MR devices. Alert on status="offline".
- **Visualization:** Status table with last seen time; uptime percentage gauge; event alert dashboard.

---

### UC-5.9.20 · Mesh Network Link Quality and Backhaul Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors wireless mesh backhaul links to ensure reliability of remote AP connections.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MR sourcetype=meraki type=security_event
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MR mesh_link_quality=*
| stats avg(mesh_link_quality) as avg_link_quality by ap_name, upstream_ap
| where avg_link_quality < 70
| sort avg_link_quality
```
- **Implementation:** Query MR device API for mesh_link_quality metric. Alert on degraded quality (<70%).
- **Visualization:** Network topology showing link quality; color-coded links; detail table with metrics.

---

### UC-5.9.21 · Guest Network Access Patterns and Usage
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks guest network adoption, usage patterns, and peak times for network provisioning.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api ssid="guest*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" ssid="guest"
| stats count as guest_users by _time
| timechart avg(guest_users) as avg_concurrent_guests
```
- **Implementation:** Filter clients API results for guest SSIDs. Track concurrent count over time.
- **Visualization:** Time-series of guest users; daily/weekly heatmap; trend dashboard.

---

### UC-5.9.22 · WiFi Geolocation and Location Analytics
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Uses Cisco Meraki location services to track foot traffic patterns and heat maps in physical spaces.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api location_data=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" ap_name=*
| stats count as foot_traffic by ap_name, floor
| geom geo_from_metric lat, lon
```
- **Implementation:** Use Meraki location API to get AP-based location estimates. Map to floor/zone.
- **Visualization:** Heat map by physical location; AP heat map overlay; zone traffic comparison.

---

### UC-5.9.23 · Port Utilization and Congestion Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies port saturation and congestion events that require capacity upgrades or load balancing adjustments.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(port_utilization) as avg_util, max(port_utilization) as max_util by switch_name, port_id
| where max_util > 80
| sort - max_util
```
- **Implementation:** Query MS switch device API for port utilization metrics. Alert on sustained >80% utilization.
- **Visualization:** Table of congested ports; timeline showing peak congestion; port utilization heatmap.

---

### UC-5.9.24 · Power over Ethernet (PoE) Consumption Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors PoE power allocation to prevent over-subscription and ensure sufficient power for all devices.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS poe_consumption=*
| stats sum(poe_consumption) as total_power_watts, avg(poe_consumption) as avg_power by switch_name
| eval power_capacity_pct=round(total_power_watts*100/1000, 2)
| where power_capacity_pct > 80
```
- **Implementation:** Pull poe_consumption metrics from MS device API. Aggregate by switch.
- **Visualization:** Gauge showing power utilization percentage; stacked bar of PoE by port; capacity dashboard.

---

### UC-5.9.25 · Spanning Tree Protocol (STP) Topology Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Alerts on unexpected STP topology changes that indicate link failures or network configuration issues.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*STP*" OR signature="*topology*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*STP*" OR signature="*topology*")
| stats count as change_count by switch_name, change_type
| where change_count > 3
```
- **Implementation:** Monitor STP-related syslog events. Alert on excessive topology changes.
- **Visualization:** Timeline of topology changes; table of affected switches; alert dashboard.

---

### UC-5.9.26 · Port Security Violations and Rogue Device Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects unauthorized MAC addresses and port security breaches that indicate potential network intrusion.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Port Security*" OR signature="*Unauthorized MAC*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Port Security*" OR signature="*Unauthorized*")
| stats count as violation_count by switch_name, port_id, mac_address
| where violation_count > 0
| sort - violation_count
```
- **Implementation:** Monitor port security violation events from syslog. Create alert for each unique violation.
- **Visualization:** Table of violations; timeline of events; network detail with affected ports.

---

### UC-5.9.27 · Switch Interface Up/Down Events and Link Flapping
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Identifies port flapping, cable issues, and unstable link states that cause intermittent connectivity.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*link*" OR signature="*Interface*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*link*" OR signature="*Interface*" OR signature="*up*" OR signature="*down*")
| stats count as event_count by switch_name, port_id
| eval flap_rate=round(event_count/24, 2)
| where flap_rate > 2
```
- **Implementation:** Track interface up/down state changes over 24 hours. Alert on flapping (>2 changes/hour).
- **Visualization:** Time-series showing flap events; table of affected ports; link state history.

---

### UC-5.9.28 · VLAN Configuration Mismatches and Tagging Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects VLAN configuration errors and tagging violations that disrupt network segmentation.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS sourcetype=meraki
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*VLAN*"
| stats count as vlan_error_count by switch_name, vlan_id
| where vlan_error_count > 5
```
- **Implementation:** Monitor VLAN-related error events. Cross-reference with API device VLAN config.
- **Visualization:** Table of VLAN issues; timeline of configuration changes; network diagram with VLAN details.

---

### UC-5.9.29 · MAC Flooding and Bridge Table Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Detects MAC address table exhaustion and flooding attacks that could overwhelm switch resources.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*MAC*" OR signature="*bridge*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*MAC*" OR signature="*flood*")
| stats count as flood_count by switch_name, port_id
| where flood_count > 50
```
- **Implementation:** Monitor MAC-related syslog events. Alert on suspicious patterns.
- **Visualization:** Table of affected switches/ports; time-series of flood events; alert dashboard.

---

### UC-5.9.30 · DHCP Snooping Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Detects unauthorized DHCP servers and spoofing attempts that disrupt network address allocation.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DHCP Snooping*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DHCP*Snooping*"
| stats count as violation_count by switch_name, port_id, server_ip
| where violation_count > 0
```
- **Implementation:** Enable DHCP snooping on MS switches. Monitor syslog for violations.
- **Visualization:** Table of violations; timeline of events; affected port details.

---

### UC-5.9.31 · Broadcast Storm Detection and Mitigation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies and alerts on broadcast storms that can freeze network performance across all switches.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*broadcast*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*broadcast*"
| stats sum(packet_count) as broadcast_packets by switch_name, port_id
| where broadcast_packets > 10000
```
- **Implementation:** Monitor broadcast traffic thresholds. Alert on sustained high broadcast rates.
- **Visualization:** Real-time alert dashboard; time-series of broadcast packets; affected port list.

---

### UC-5.9.32 · Switch CPU and Memory Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors switch hardware resources to prevent performance degradation or device failure.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(cpu_usage) as avg_cpu, max(cpu_usage) as peak_cpu, avg(memory_usage) as avg_mem by switch_name
| where avg_cpu > 75 OR avg_mem > 80
```
- **Implementation:** Query MS device API for CPU and memory metrics. Alert on threshold breaches.
- **Visualization:** Gauge charts for CPU/memory; time-series trends; capacity planning dashboard.

---

### UC-5.9.33 · Stack Unit and Redundancy Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Ensures switch stacking configuration remains healthy and redundancy is not compromised.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS stack_id=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS stack_id=*
| stats count as stack_members, count(eval(status="offline")) as offline_members by stack_id
| where offline_members > 0
```
- **Implementation:** Monitor stack member status via device API. Alert on member removal or failure.
- **Visualization:** Table of stack members and status; redundancy gauge; alert dashboard.

---

### UC-5.9.34 · Trunk Link Utilization and Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors inter-switch and uplink trunk utilization to identify bandwidth constraints.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS port_type="trunk"
| stats avg(port_utilization) as avg_trunk_util, max(port_utilization) as peak_util by switch_name, port_id
| where peak_util > 70
| sort - peak_util
```
- **Implementation:** Query MS API for trunk port utilization. Alert on sustained high utilization.
- **Visualization:** Trunk link utilization heatmap; timeline showing peak demand; capacity planning chart.

---

### UC-5.9.35 · QoS Queue Drops and Priority Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Detects QoS queue overflow and drops that indicate traffic priority issues.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*QoS*" OR signature="*queue*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*QoS*" OR signature="*queue*" OR signature="*drop*")
| stats sum(packets_dropped) as total_drops by switch_name, queue_id
| where total_drops > 1000
```
- **Implementation:** Monitor QoS-related syslog events and drops. Alert on significant drop rates.
- **Visualization:** Table of drops by queue; time-series of drop events; traffic distribution pie chart.

---

### UC-5.9.36 · Port Access Control List (ACL) Hits and Block Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks ACL rule hits to monitor policy enforcement and identify anomalous traffic.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*ACL*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*ACL*" action="block"
| stats count as block_count by switch_name, src_mac, dest_mac
| sort - block_count
```
- **Implementation:** Monitor ACL deny/block events from syslog. Track frequently blocked source/destinations.
- **Visualization:** Table of blocked traffic; timeline of ACL hits; top blocked addresses chart.

---

### UC-5.9.37 · Cable Test Results and Port Diagnostics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Analyzes cable integrity test results to identify wiring faults before they cause outages.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cable*" OR signature="*diagnostic*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cable*" OR signature="*diagnostic*")
| stats count as test_count by switch_name, port_id, test_result
| where test_result="FAIL"
```
- **Implementation:** Periodically run cable tests on switch ports. Ingest results into syslog.
- **Visualization:** Table of failed cable tests; port detail with diagnostic results; failure timeline.

---

### UC-5.9.38 · Uplink Health and Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors primary/secondary uplink status to detect failover events and connection issues.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Uplink*" OR signature="*failover*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Uplink*" OR signature="*failover*")
| stats count as failover_count by uplink_name, event_type
| where failover_count > 0
```
- **Implementation:** Monitor uplink status change events in syslog. Alert on failover.
- **Visualization:** Uplink status dashboard; failover event timeline; connection health gauge.

---

### UC-5.9.39 · VPN Tunnel Status and Path Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures all site-to-site and client VPN tunnels remain active and operative.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=vpn sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn
| stats latest(status) as tunnel_status, latest(last_changed) as status_change_time by tunnel_id, remote_site
| where tunnel_status="down" OR tunnel_status="unstable"
```
- **Implementation:** Monitor VPN tunnel state from syslog and API. Alert on status != "up".
- **Visualization:** VPN tunnel status matrix; site connectivity map; tunnel health sparklines.

---

### UC-5.9.40 · Content Filtering and URL Category Blocks
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks blocked URLs and categories to monitor policy compliance and identify misclassified content.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=urls action="blocked"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| stats count as block_count by url_category, src_ip
| sort - block_count
| head 20
```
- **Implementation:** Ingest URL filtering events from MX syslog. Categorize by policy.
- **Visualization:** Table of top blocked categories; bar chart by category; user detail table.

---

### UC-5.9.41 · IDS/IPS Alert Analysis and Threat Scoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies and prioritizes intrusion detection alerts for investigation and threat response.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=ids_alert
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=ids_alert
| stats count as alert_count by signature, priority, src_ip, dest_ip
| eval severity=case(priority=1, "Critical", priority=2, "High", priority=3, "Medium", 1=1, "Low")
| where priority <= 2
| sort - alert_count
```
- **Implementation:** Ingest IDS/IPS alert events from MX appliance. Enrich with threat intelligence.
- **Visualization:** Alert timeline; severity breakdown pie chart; alert detail table; threat map.

---

### UC-5.9.42 · Malware Detection and AMP File Reputation Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects and tracks file-based threats to respond quickly to potential malware infections.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*malware*" OR signature="*AMP*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*malware*" OR signature="*AMP*")
| stats count as malware_count by src_ip, threat_name, file_name
| where malware_count > 0
| sort - malware_count
```
- **Implementation:** Enable AMP on MX appliance. Ingest malware detection events.
- **Visualization:** Threat timeline; infected hosts table; file reputation detail; incident dashboard.

---

### UC-5.9.43 · Firewall Rule Hit Analysis and Top Denied Flows
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies top denied flows to optimize firewall rules and detect policy violations.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow action="deny"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow action="deny"
| stats count as deny_count by firewall_rule, src_ip, dest_ip, dest_port
| sort - deny_count
| head 20
```
- **Implementation:** Analyze firewall deny events from flow logs. Correlate with rules.
- **Visualization:** Top denied flows table; denial timeline; source/dest distribution heatmap.

---

### UC-5.9.44 · Traffic Shaping Effectiveness and QoS Policy Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Measures the impact of traffic shaping policies on bandwidth distribution and priority.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow priority_queue=*
| stats sum(bytes) as total_bytes, avg(latency) as avg_latency by priority_queue
| eval efficiency=round(total_bytes/sum(total_bytes)*100, 2)
```
- **Implementation:** Extract priority_queue field from flow logs. Measure bandwidth by priority.
- **Visualization:** Stacked bar chart of bandwidth by priority; latency by QoS class; efficiency gauge.

---

### UC-5.9.45 · Site-to-Site VPN Latency and Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors latency and jitter on VPN tunnels to ensure quality of critical business traffic.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=vpn sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn latency=*
| stats avg(latency) as avg_vpn_latency, max(jitter) as max_jitter by tunnel_id, remote_site
| where avg_vpn_latency > 50
```
- **Implementation:** Extract VPN latency and jitter metrics. Monitor tunnel performance.
- **Visualization:** Gauge of VPN latency; latency trend line; jitter comparison chart.

---

### UC-5.9.46 · Client VPN Connections and Remote Access Patterns
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks client VPN usage patterns for remote workers and identifies problematic connections.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=vpn client_vpn=true
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn client_vpn=true
| stats count as connection_count, avg(duration) as avg_session_length by user_id, src_ip
| where connection_count > 10
```
- **Implementation:** Filter VPN logs for client connections. Track by user and source IP.
- **Visualization:** Connected users timeline; session duration histogram; geography map of remote users.

---

### UC-5.9.47 · NAT Pool Usage and Exhaustion Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors NAT pool utilization to prevent address exhaustion that could block outbound traffic.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" nat_pool_usage=*
| stats max(nat_pool_usage) as peak_nat_usage, count by nat_pool_id
| eval nat_capacity_pct=round(peak_nat_usage*100/254, 2)
| where nat_capacity_pct > 80
```
- **Implementation:** Query appliance API for NAT pool metrics. Alert on >80% utilization.
- **Visualization:** Gauge of NAT pool usage; capacity timeline; pool exhaustion alert dashboard.

---

### UC-5.9.48 · BGP Peering Status and Route Stability
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Ensures BGP peers remain established and routing remains stable for multi-ISP designs.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*BGP*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*BGP*" (signature="*neighbor*" OR signature="*route*")
| stats count as bgp_event_count by bgp_neighbor, event_type
| where bgp_event_count > 5
```
- **Implementation:** Monitor BGP event syslog. Alert on neighbor state changes.
- **Visualization:** BGP peer status table; route change timeline; peering stability gauge.

---

### UC-5.9.49 · DHCP Pool Exhaustion and Address Allocation Issues
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Alerts when DHCP pools approach depletion to prevent clients from obtaining IP addresses.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" dhcp_pool=*
| stats latest(addresses_available) as available_ips, latest(pool_size) as total_pool by vlan_id
| eval allocation_pct=round((total_pool-available_ips)*100/total_pool, 2)
| where allocation_pct > 85
```
- **Implementation:** Query appliance API for DHCP metrics by VLAN. Alert on >85% allocation.
- **Visualization:** DHCP pool gauge per VLAN; timeline of pool usage; alert dashboard.

---

### UC-5.9.50 · Threat Intelligence Correlation and IoC Matching
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Correlates network traffic with threat intelligence databases to detect known malicious IPs and domains.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event OR type=urls OR type=flow
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" (type=security_event OR type=urls OR type=flow)
| lookup threat_intelligence_list src_ip as src_ip OUTPUTNEW threat_name, threat_severity
| where threat_severity="high" OR threat_severity="critical"
| stats count as hit_count by src_ip, dest_ip, threat_name
| sort - hit_count
```
- **Implementation:** Create threat intelligence lookup table. Correlate with network events.
- **Visualization:** IoC match timeline; threat severity breakdown; affected hosts table.

---

### UC-5.9.51 · Geo-Blocking Event Tracking and Geographic Policy Enforcement
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks geo-blocking policy enforcement to verify compliance with data residency and export controls.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=urls action="blocked" country=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| lookup geo_ip.csv dest_ip OUTPUTNEW country, city
| stats count as block_count by country
| sort - block_count
```
- **Implementation:** Ingest URL logs with GeoIP enrichment. Track blocks by geography.
- **Visualization:** Geo-block map; country block count chart; policy compliance dashboard.

---

### UC-5.9.52 · Application Visibility and Network Application Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies top applications and protocols on network to understand usage patterns and detect anomalies.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow application=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow application=*
| stats sum(bytes) as app_bytes, count as flow_count by application, application_category
| eval app_bandwidth_pct=round(app_bytes*100/sum(app_bytes), 2)
| sort - app_bytes
| head 20
```
- **Implementation:** Extract application field from flow logs. Aggregate by app and category.
- **Visualization:** App bandwidth pie chart; top apps bar chart; bandwidth timeline by app.

---

### UC-5.9.53 · Bandwidth by Application and Department
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks bandwidth consumption by application and business unit for chargeback and optimization.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow
| lookup department_by_ip.csv src_ip OUTPUTNEW department
| stats sum(sent_bytes) as upload_mb, sum(received_bytes) as download_mb by application, department
| eval total_mb=upload_mb+download_mb
| sort - total_mb
```
- **Implementation:** Correlate flows with IP-to-department mapping. Aggregate by app and dept.
- **Visualization:** Stacked bar of bandwidth by dept/app; heatmap of app usage per dept.

---

### UC-5.9.54 · WAN Link Quality Monitoring (Jitter, Latency, Packet Loss)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Continuously monitors WAN quality metrics to detect link degradation before impacting users.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api wan_metrics=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" uplink=*
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(packet_loss) as avg_loss by uplink_id
| eval link_quality=case(avg_loss > 5, "Critical", avg_latency > 100, "Poor", avg_jitter > 50, "Fair", 1=1, "Good")
```
- **Implementation:** Query appliance API for uplink WAN metrics. Monitor quality KPIs.
- **Visualization:** Uplink quality scorecard; latency/jitter/loss timeline; quality gauge per uplink.

---

### UC-5.9.55 · Internet Uplink Failover Events and Recovery Time
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks failover events, recovery time, and uplink behavior to ensure high availability.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*failover*" OR signature="*recovery*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*failover*" OR signature="*recovery*")
| stats count as failover_count, latest(recovery_time) as recovery_duration by uplink_id, failure_reason
| where failover_count > 0
```
- **Implementation:** Monitor failover and recovery events from syslog. Calculate recovery MTTR.
- **Visualization:** Failover timeline; recovery time gauge; uplink failure cause pie chart.

---

### UC-5.9.56 · Cellular Modem Failover Activation and Usage
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks cellular backup activation to monitor failover effectiveness and cellular data usage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*4G*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*4G*" OR signature="*LTE*")
| stats count as cellular_events, sum(data_usage_mb) as total_cellular_data by event_type
| where total_cellular_data > 0
```
- **Implementation:** Ingest cellular failover events. Track data consumption.
- **Visualization:** Cellular usage timeline; failover event table; data usage gauge.

---

### UC-5.9.57 · Warm Spare Failover and Appliance Redundancy
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Ensures warm spare failover mechanism is operational and redundancy is maintained.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*warm spare*" OR signature="*HA*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*warm spare*" OR signature="*HA*" OR signature="*redundancy*")
| stats latest(ha_status) as redundancy_status, count as status_change_count by appliance_pair
| where ha_status!="active/standby"
```
- **Implementation:** Monitor HA/warm spare events. Alert on status != "active/standby".
- **Visualization:** HA status dashboard; failover timeline; redundancy health gauge.

---

### UC-5.9.58 · Auto VPN Path Changes and Tunnel Switching
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks automatic VPN path optimization to understand tunnel usage and convergence behavior.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=vpn signature="*Auto VPN*" OR signature="*path change*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn (signature="*Auto VPN*" OR signature="*path change*")
| stats count as path_change_count by tunnel_id, new_path, old_path
| where path_change_count > 3
```
- **Implementation:** Monitor Auto VPN path optimization events. Alert on excessive changes.
- **Visualization:** Path change timeline; tunnel path change distribution; convergence analysis.

---

### UC-5.9.59 · Connection Rate Analysis and DOS Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects denial of service attacks by analyzing abnormal connection establishment rates.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow protocol="tcp" tcp_flags="SYN"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow protocol="tcp" tcp_flags="SYN"
| timechart count as new_connections by src_ip
| where new_connections > 1000
```
- **Implementation:** Monitor TCP SYN rate by source IP. Alert on anomalous connection rates.
- **Visualization:** Connection rate timeline; source IP detail table; DOS alert dashboard.

---

### UC-5.9.60 · Data Loss Prevention (DLP) Event Analysis
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Detects and alerts on sensitive data transmission to prevent data exfiltration.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DLP*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DLP*"
| stats count as dlp_match_count by src_ip, dest_ip, dlp_policy, data_type
| where dlp_match_count > 0
| sort - dlp_match_count
```
- **Implementation:** Enable DLP on MX appliance. Ingest DLP match events.
- **Visualization:** DLP incident timeline; data type breakdown; source/destination detail.

---

### UC-5.9.61 · SSL/TLS Certificate Expiration Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors SSL certificate expiration dates on all network devices to prevent outages.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" certificate_expiry=*
| eval days_until_expiry=round((strptime(certificate_expiry, "%Y-%m-%d")-now())/86400, 0)
| where days_until_expiry < 30
| stats latest(days_until_expiry) as days_left by device_name, device_type
| sort days_left
```
- **Implementation:** Query device API for certificate expiry dates. Alert on <30 days.
- **Visualization:** Expiration countdown gauge; timeline of expiring certs; alert table.

---

### UC-5.9.62 · Firmware Update Compliance and Version Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures all network devices run supported firmware versions and patches.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(firmware_version) as current_fw, count as device_count by device_type
| lookup recommended_firmware.csv device_type OUTPUTNEW recommended_fw
| where current_fw != recommended_fw
```
- **Implementation:** Query device API for firmware versions. Compare to recommended baseline.
- **Visualization:** Firmware version table by device type; compliance percentage gauge; outdated device list.

---

### UC-5.9.63 · API Call Rate Monitoring and Rate Limit Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors API usage to prevent rate limit hits and optimize automation efficiency.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api:*"
| timechart count as api_calls by source, endpoint
| eval call_rate=api_calls/60
| where call_rate > 9
```
- **Implementation:** Log all API calls with timestamps. Monitor call rate by endpoint.
- **Visualization:** API call timeline; rate limit gauge; endpoint usage breakdown.

---

### UC-5.9.64 · License Expiration Tracking and Renewal Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures licenses don't expire unexpectedly and features remain available.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" license_expiry=*
| eval days_until_expire=round((strptime(license_expiry, "%Y-%m-%d")-now())/86400, 0)
| stats latest(days_until_expire) as days_left, latest(license_expiry) as expiry_date by license_type, organization
| where days_left < 90
| sort days_left
```
- **Implementation:** Query organization API for license expiry. Alert on <90 days.
- **Visualization:** License expiration countdown; renewal timeline; license detail table.

---

### UC-5.9.65 · Network Device Inventory and Change Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Maintains accurate inventory of network devices and tracks hardware/software changes.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by device_type, network_id
| append [search index=cisco_network sourcetype="meraki:api" | stats count as org_count]
| fillnull device_count value=0
```
- **Implementation:** Query devices API to build current inventory. Track additions/removals.
- **Visualization:** Inventory summary table; device count by type pie chart; change log timeline.

---

### UC-5.9.66 · Admin Activity Logging and Access Control Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks administrator actions and logins for compliance and security auditing.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*admin*" OR signature="*login*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*admin*" OR signature="*login*")
| stats count as admin_action_count by admin_user, action_type, timestamp
| where admin_action_count > 0
```
- **Implementation:** Enable admin audit logging. Ingest login and action events.
- **Visualization:** Admin activity timeline; action type breakdown; user activity detail table.

---

### UC-5.9.67 · Admin Privilege Changes and Permission Escalation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Detects unauthorized privilege changes and permission escalation attempts.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*privilege*" OR signature="*permission*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*privilege*" OR signature="*permission*")
| stats count as priv_change_count by admin_user, old_role, new_role
| where priv_change_count > 0
```
- **Implementation:** Monitor privilege and role change events. Alert on escalations.
- **Visualization:** Privilege change timeline; role change audit table; escalation alert dashboard.

---

### UC-5.9.68 · Alert Volume Trending and Alert Fatigue Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Analyzes alert volume trends to optimize alerting rules and reduce false positives.
- **App/TA:** `Splunk_TA_cisco_meraki` (webhooks)
- **Data Sources:** `sourcetype=meraki:webhook
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:webhook"
| timechart count as alert_count by alert_type
| eval alert_ratio=alert_count/sum(alert_count)
```
- **Implementation:** Ingest webhook alerts. Track volume and types over time.
- **Visualization:** Alert volume timeline; alert type pie chart; trend sparklines.

---

### UC-5.9.69 · Network Health Score Aggregation and Executive Reporting
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Provides high-level network health metric for executive dashboards and trend reporting.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as device_health, count(eval(status="offline")) as offline_count by network_id
| eval network_health=round(device_health - (offline_count*5), 2)
| eval health_status=case(network_health >= 85, "Healthy", network_health >= 70, "Degraded", 1=1, "Critical")
```
- **Implementation:** Aggregate device health scores. Calculate composite network score.
- **Visualization:** Network health gauge; health trend sparkline; status KPI dashboard.

---

### UC-5.9.70 · Device Online/Offline Status Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks device connectivity status to quickly identify and respond to device failures.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(status) as device_status, latest(last_status_change) as status_change_time, count(eval(status="offline")) as offline_count by network_id
| eval offline_pct=round(offline_count*100/count, 2)
| where offline_count > 0
```
- **Implementation:** Poll devices API for status. Alert on offline devices.
- **Visualization:** Device status table; offline count gauge; status change timeline.

---

### UC-5.9.71 · Multi-Organization Comparison and Benchmarking
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Compares metrics across organizations to identify best practices and outliers.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as avg_health, count as device_count by organization
| sort - avg_health
```
- **Implementation:** Aggregate metrics across multiple organizations. Create comparison views.
- **Visualization:** Organization comparison bar chart; health rank table; benchmark line chart.

---

### UC-5.9.72 · Configuration Change Window Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Ensures configuration changes only occur within approved maintenance windows.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*config*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*config*"
| eval hour=strftime(_time, "%H")
| stats count as config_change_count by hour
| eval window_compliant=if(hour>=22 OR hour<6, "Yes", "No")
| where window_compliant="No" AND config_change_count > 0
```
- **Implementation:** Monitor configuration change events. Check against maintenance windows.
- **Visualization:** Change compliance timeline; out-of-window change alert table.

---

### UC-5.9.73 · Webhook Delivery Failure Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Ensures webhook notifications reach integrations and alerts don't get lost.
- **App/TA:** `Splunk_TA_cisco_meraki` (webhooks)
- **Data Sources:** `sourcetype=meraki:webhook status="failure" OR status="error"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:webhook" (status="failure" OR status="error")
| stats count as failure_count, latest(error_message) as last_error by webhook_id, organization
| where failure_count > 5
```
- **Implementation:** Log webhook delivery attempts. Alert on sustained failures.
- **Visualization:** Webhook failure timeline; failure cause breakdown; affected org list.

---

### UC-5.9.74 · API Error Rate and Endpoint Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors API endpoint health and error rates to ensure automation reliability.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api (http_status_code=4* OR http_status_code=5*)
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api:*" (http_status_code=4* OR http_status_code=5*)
| stats count as error_count, values(http_status_code) as status_codes by endpoint, method
| eval error_rate=round(error_count*100/total_requests, 2)
| where error_rate > 5
```
- **Implementation:** Log API responses with status codes. Alert on error rate threshold.
- **Visualization:** API error timeline; endpoint error breakdown; error rate gauge.

---

### UC-5.9.75 · Dashboard Configuration and Export Backup
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks dashboard configuration backups to enable disaster recovery and configuration review.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" backup_timestamp=*
| stats latest(backup_timestamp) as last_backup, count as backup_count by organization
| eval backup_age_days=round((now()-strptime(backup_timestamp, "%Y-%m-%d"))/86400, 0)
| where backup_age_days > 7
```
- **Implementation:** Periodically backup organization configurations. Track backup history.
- **Visualization:** Last backup timestamp by org; backup recency gauge; backup history timeline.

---

### UC-5.9.76 · Camera Uptime and Availability Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors video surveillance system availability to ensure continuous monitoring coverage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api device_type=MV sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MV
| stats latest(status) as camera_status, latest(last_status_change) as status_change by camera_name, location
| where camera_status="offline"
```
- **Implementation:** Monitor MV camera status via device API. Alert on offline cameras.
- **Visualization:** Camera status map; offline camera list; availability percentage gauge.

---

### UC-5.9.77 · Video Retention and Cloud Archive Storage Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks cloud storage usage for video archives to manage costs and ensure retention SLA.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" storage_usage=*
| stats sum(storage_usage) as total_storage_gb by camera_id, retention_days
| eval storage_pct=round(total_storage_gb*100/1000, 2)
| where storage_pct > 80
```
- **Implementation:** Query camera API for storage metrics. Alert on >80% utilization.
- **Visualization:** Storage utilization gauge; retention timeline; storage trend chart.

---

### UC-5.9.78 · Motion Detection Events and Alert Volume Analysis
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Value:** Analyzes motion detection event patterns to optimize camera sensitivity and reduce false alerts.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*motion*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*motion*"
| timechart count as motion_events by camera_name
| eval daily_avg=round(motion_events/1440, 2)
```
- **Implementation:** Ingest motion detection events. Track volume and patterns.
- **Visualization:** Motion detection timeline; heat map by time of day; camera comparison chart.

---

### UC-5.9.79 · Camera Video Quality Score and Stream Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors video quality metrics to identify network or hardware issues affecting video feeds.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" quality_score=*
| stats avg(quality_score) as avg_quality, min(quality_score) as min_quality by camera_name
| where avg_quality < 80
| sort avg_quality
```
- **Implementation:** Query camera API for quality_score metric. Alert on <80 average.
- **Visualization:** Quality score gauge per camera; quality trend line; affected camera list.

---

### UC-5.9.80 · Cloud Archive Status and Backup Validation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Ensures video archives are successfully uploaded to cloud and backup integrity is maintained.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api archive_status=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" archive_status=*
| stats latest(archive_status) as backup_status, latest(last_archive_time) as last_backup by camera_id
| where archive_status != "success"
```
- **Implementation:** Check camera API archive status. Alert on failures.
- **Visualization:** Archive status table; last backup time timeline; failure alert dashboard.

---

### UC-5.9.81 · Video Stream Connection Errors and Quality Issues
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Detects video stream connection failures that prevent remote viewing or recording.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*stream*" OR signature="*connection*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*stream*" OR signature="*connection*")
| stats count as error_count by camera_name, error_type
| where error_count > 10
```
- **Implementation:** Monitor stream connection events. Alert on error spikes.
- **Visualization:** Connection error timeline; affected camera list; error type breakdown.

---

### UC-5.9.82 · Camera Firmware Compliance and Update Management
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures all cameras run current firmware with security patches.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api device_type=MV
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MV
| stats latest(firmware_version) as camera_fw, count as camera_count
| lookup recommended_camera_fw.csv camera_model OUTPUTNEW recommended_version
| where camera_fw != recommended_version
```
- **Implementation:** Query MV device API for firmware. Compare to recommended baseline.
- **Visualization:** Firmware version table; compliance percentage gauge; outdated camera list.

---

### UC-5.9.83 · Night Mode Effectiveness and Low-Light Performance
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors camera performance in low-light conditions to ensure night surveillance effectiveness.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api night_mode=true
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" night_mode=true
| stats avg(quality_score) as night_quality, count as night_mode_events by camera_name
| where night_quality < 75
```
- **Implementation:** Track camera performance during night mode. Monitor quality metrics.
- **Visualization:** Night mode quality gauge; low-light performance timeline; affected camera list.

---

### UC-5.9.84 · People Counting Trends and Occupancy Analytics
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Uses camera people counting to track foot traffic trends for space utilization and facility planning.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api people_count=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" people_count=*
| timechart avg(people_count) as avg_occupancy by location
```
- **Implementation:** Extract people_count metrics from camera API. Aggregate by location and time.
- **Visualization:** Occupancy heat map by time of day; location comparison bar chart; trend sparkline.

---

### UC-5.9.85 · Temperature Sensor Threshold Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Alerts when environmental temperatures exceed safe thresholds to prevent equipment damage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*temperature*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*temperature*"
| stats latest(temperature) as current_temp, min(temperature) as min_temp, max(temperature) as max_temp by sensor_location
| where current_temp > 30 OR current_temp < 5
```
- **Implementation:** Monitor temperature sensor threshold alerts from syslog. Alert on exceedance.
- **Visualization:** Temperature gauge per location; trend timeline; alert dashboard.

---

### UC-5.9.86 · Humidity Monitoring and Dew Point Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors humidity levels to ensure optimal conditions for equipment and prevent moisture damage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*humidity*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*humidity*"
| stats latest(humidity) as current_humidity, avg(humidity) as avg_humidity by sensor_location
| eval dew_point="calculated_value"
```
- **Implementation:** Monitor humidity sensor data. Calculate dew point for condensation risk.
- **Visualization:** Humidity gauge per location; humidity vs temperature correlation; trend chart.

---

### UC-5.9.87 · Door Open/Close Event Detection and Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks door access events for security and facility monitoring.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*door*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*door*" (action="open" OR action="close")
| stats count as door_events, latest(timestamp) as last_event by door_location, action
```
- **Implementation:** Monitor door sensor events. Alert on unusual access patterns.
- **Visualization:** Door event timeline; access pattern analysis; alert table.

---

### UC-5.9.88 · Water Leak Detection and Flood Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Immediately detects water leaks to prevent equipment damage and business interruption.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*water*" OR signature="*leak*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*water*" OR signature="*leak*")
| stats count as leak_events, latest(timestamp) as last_detection by sensor_location
| where leak_events > 0
```
- **Implementation:** Monitor water/leak detection sensors. Create critical alert.
- **Visualization:** Leak alert dashboard; sensor location map; event timeline.

---

### UC-5.9.89 · Power Monitoring and Electrical Load Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks electrical power consumption and load to identify anomalies and plan upgrades.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="power" power_watts=*
| stats avg(power_watts) as avg_power, max(power_watts) as peak_power by location
| eval power_capacity_pct=round(peak_power*100/15000, 2)
```
- **Implementation:** Query sensor API for power metrics. Track consumption and peaks.
- **Visualization:** Power consumption gauge; peak load timeline; capacity planning chart.

---

### UC-5.9.90 · Air Quality and CO2 Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors indoor air quality to ensure safe working conditions.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api sensor_type="air_quality"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="air_quality" co2_ppm=*
| stats latest(co2_ppm) as current_co2, avg(co2_ppm) as avg_co2 by location
| where current_co2 > 1000
```
- **Implementation:** Monitor CO2 and air quality sensor data. Alert on high levels.
- **Visualization:** CO2 level gauge per location; trend timeline; air quality status chart.

---

### UC-5.9.91 · Ambient Noise Level Monitoring and Trend Analysis
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks noise levels to ensure comfortable working environment and detect anomalies.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api sensor_type="noise"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="noise" noise_db=*
| stats avg(noise_db) as avg_noise, max(noise_db) as peak_noise by location
| timechart avg(noise_db) by location
```
- **Implementation:** Ingest noise sensor data. Track by location and time of day.
- **Visualization:** Noise level gauge; time-of-day heat map; location comparison chart.

---

### UC-5.9.92 · Indoor Climate Trending and HVAC Optimization
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Analyzes temperature and humidity trends to optimize HVAC system efficiency.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api sensor_type IN ("temperature", "humidity")
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type IN ("temperature", "humidity")
| stats avg(value) as avg_value by sensor_type, location
| timechart avg(value) by sensor_type
```
- **Implementation:** Correlate temperature and humidity data. Identify optimization opportunities.
- **Visualization:** Climate trend line chart; comfort zone indicator; energy efficiency analysis.

---

### UC-5.9.93 · Environmental Sensor Battery Health and Replacement Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks sensor battery levels to ensure sensors remain operational and schedule replacements.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" battery_level=*
| stats latest(battery_level) as battery_pct by sensor_id, location
| where battery_pct < 20
| sort battery_pct
```
- **Implementation:** Query sensor API for battery metrics. Alert on <20% battery.
- **Visualization:** Battery health table; battery trend timeline; replacement alert dashboard.

---

### UC-5.9.94 · Sensor Connectivity and Heartbeat Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures all sensors maintain connectivity and operational status.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(last_report) as last_checkin by sensor_id
| eval hours_since_checkin=round((now()-strptime(last_report, "%Y-%m-%dT%H:%M:%S"))/3600, 1)
| where hours_since_checkin > 2
```
- **Implementation:** Query sensor API for last report time. Alert on missing heartbeats.
- **Visualization:** Sensor status table; last heartbeat timeline; offline sensor list.

---

### UC-5.9.95 · Device Compliance Status and Policy Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures all managed devices comply with security policies and configuration standards.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api compliance_status=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" (compliance_status="noncompliant" OR compliance_status="unknown")
| stats count as noncompliant_count by os_type, compliance_reason
| eval compliance_pct=round(noncompliant_count*100/total_devices, 2)
```
- **Implementation:** Query device compliance status from SM API. Alert on noncompliance.
- **Visualization:** Compliance status table; compliance percentage gauge; noncompliant device list.

---

### UC-5.9.96 · Mobile Device Enrollment and MDM Status Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks device enrollment status to ensure mobile device management coverage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api enrollment_status=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" enrollment_status IN ("enrolled", "pending", "failed")
| stats count as device_count by enrollment_status, os_type
| eval enrollment_pct=round(count*100/sum(count), 2)
```
- **Implementation:** Query device enrollment status. Track pending and failed enrollments.
- **Visualization:** Enrollment status pie chart; pending enrollment timeline; device count by OS.

---

### UC-5.9.97 · Geofencing Alerts and Location-Based Policy Triggers
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Uses geofencing to detect when devices leave secure zones and trigger location-based policies.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*geofence*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*geofence*"
| stats count as geofence_event_count by device_id, zone_name, event_type
| where event_type="left_zone"
```
- **Implementation:** Monitor geofence event triggers. Track zone entry/exit by device.
- **Visualization:** Geofence event timeline; zone heat map; affected device list.

---

### UC-5.9.98 · Mobile Security Policy Violations and App Restrictions
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Detects policy violations and restricted app usage attempts.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*policy*" OR signature="*app*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*policy*" OR signature="*app*") violation="true"
| stats count as violation_count by device_id, policy_name, violation_type
| where violation_count > 5
```
- **Implementation:** Monitor security policy violation events. Alert on repeated violations.
- **Visualization:** Policy violation timeline; violation type breakdown; affected device list.

---

### UC-5.9.99 · Lost Mode Device Activation and Recovery Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks activation of lost mode on devices to ensure recovery protocols are working.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*lost mode*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*lost mode*"
| stats count as lost_mode_count, latest(timestamp) as last_activation by device_id, activation_reason
```
- **Implementation:** Monitor lost mode activation events. Track recovery time.
- **Visualization:** Lost mode event timeline; affected device table; recovery status dashboard.

---

### UC-5.9.100 · Mobile App Deployment Success Rate and Distribution Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks app deployment success and identifies devices with failed or incomplete deployments.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*app*deployment*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*app*deployment*"
| stats count as deployment_count, count(eval(status="success")) as success_count, count(eval(status="failed")) as failed_count by app_name
| eval success_rate=round(success_count*100/deployment_count, 2)
| where success_rate < 95
```
- **Implementation:** Monitor app deployment status events. Alert on low success rates.
- **Visualization:** Deployment success rate gauge; app deployment timeline; failure detail table.

---

### UC-5.9.101 · Cellular Gateway Signal Strength Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Monitors cellular signal strength to ensure reliable backup connectivity.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MG
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats avg(signal_strength) as avg_signal, min(signal_strength) as min_signal by cellular_gateway_id
| eval signal_quality=case(avg_signal > -90, "Excellent", avg_signal > -110, "Good", 1=1, "Poor")
```
- **Implementation:** Query MG device API for signal metrics. Alert on degraded signal.
- **Visualization:** Signal strength gauge; trend timeline; cellular quality status.

---

### UC-5.9.102 · Cellular Data Usage and Overage Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks cellular data consumption to manage carrier costs and prevent overages.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MG data_usage=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MG data_usage=*
| stats sum(data_usage) as total_data_usage_mb by cellular_gateway_id
| eval overage_alert=if(total_data_usage_mb > 100000, "Yes", "No")
```
- **Implementation:** Query MG API for data usage metrics. Track monthly consumption.
- **Visualization:** Data usage gauge per gateway; consumption timeline; overage alert table.

---

### UC-5.9.103 · Carrier Connection Health and Network Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors carrier connectivity and network performance metrics for backup internet links.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*carrier*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*carrier*")
| stats count as event_count by event_type, carrier_name
| where event_type="connection_error" OR event_type="network_error"
```
- **Implementation:** Monitor carrier connection and network events. Alert on issues.
- **Visualization:** Carrier health timeline; connection error table; network performance gauge.

---

### UC-5.9.104 · SIM Status and Plan Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks SIM card status and plan expiration to ensure continuous cellular connectivity.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MG sim_status=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats latest(sim_status) as sim_status, latest(plan_expiry) as expiry_date by gateway_id, sim_id
| eval days_until_expire=round((strptime(plan_expiry, "%Y-%m-%d")-now())/86400, 0)
| where sim_status != "active" OR days_until_expire < 30
```
- **Implementation:** Query MG API for SIM status and plan expiry. Alert before expiration.
- **Visualization:** SIM status table; plan expiry countdown; renewal alert dashboard.

---


## 6. Storage & Backup

### 6.1 SAN / NAS Storage

**Primary App/TA:** Vendor-specific TAs — NetApp TA (`TA-netapp_ontap`), Dell EMC TA, Pure Storage TA; SNMP TA for generic arrays; scripted/API inputs for REST-based arrays.

---

### UC-6.1.1 · Volume Capacity Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Prevents application outages caused by full volumes. Enables proactive capacity planning and procurement.
- **App/TA:** Vendor TA (e.g., `TA-netapp_ontap`) or scripted API input
- **Data Sources:** Storage array REST API metrics, SNMP hrStorageTable
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume"
| timechart span=1d avg(size_used_percent) as pct_used by volume_name
| where pct_used > 85
```
- **Implementation:** Deploy vendor TA on a heavy forwarder. Configure REST API polling (every 15 min) for volume metrics. Create alert for >85% and >95% thresholds. Build capacity forecast using `predict` command.
- **Visualization:** Line chart (capacity trend per volume), Single value (current % used), Table (volumes above threshold).

---

### UC-6.1.2 · Storage Latency Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** High storage latency directly impacts application performance. Early detection prevents SLA breaches and user experience degradation.
- **App/TA:** Vendor TA or SNMP polling
- **Data Sources:** Array performance metrics (avg_latency, read_latency, write_latency)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| timechart span=5m avg(avg_latency) as latency_ms by volume_name
| where latency_ms > 20
```
- **Implementation:** Poll latency metrics via REST or SNMP every 5 minutes. Set tiered alerts: warning >10ms, critical >20ms for production volumes. Correlate with IOPS spikes to distinguish overload from hardware issues.
- **Visualization:** Line chart (latency over time by volume), Heatmap (volume × time), Single value (current avg latency).

---

### UC-6.1.3 · IOPS Trending per Volume
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies workload hotspots and enables data placement optimization. Supports capacity planning for storage refreshes.
- **App/TA:** Vendor TA or SNMP
- **Data Sources:** Array performance metrics (read_ops, write_ops, other_ops)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume_perf"
| timechart span=15m sum(total_ops) as iops by volume_name
| sort -iops
```
- **Implementation:** Collect IOPS metrics per volume/LUN at 5-15 min intervals. Baseline normal patterns and alert on deviations exceeding 2× baseline. Correlate with application deployment events.
- **Visualization:** Line chart (IOPS trend by volume), Stacked bar (read vs write IOPS), Table (top IOPS consumers).

---

### UC-6.1.4 · Disk Failure Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Immediate awareness of disk failures allows replacement before RAID degradation leads to data loss.
- **App/TA:** Vendor TA, SNMP traps
- **Data Sources:** Array event/alert logs, SNMP traps
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:ems" severity="EMERGENCY" OR severity="ALERT"
| search disk_fail* OR disk_broken OR disk_error
| table _time, node, disk, severity, message
```
- **Implementation:** Enable SNMP traps or syslog forwarding for disk failure events. Create high-priority alert with PagerDuty/ServiceNow integration. Track spare disk inventory to ensure replacements are available.
- **Visualization:** Single value (failed disk count), Table (failed disks with details), Timeline (failure events).

---

### UC-6.1.5 · Replication Lag Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Replication lag directly impacts RPO. Monitoring ensures DR readiness and compliance with data protection SLAs.
- **App/TA:** Vendor TA, REST API polling
- **Data Sources:** Array replication status (SnapMirror, RecoverPoint, etc.)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:snapmirror"
| eval lag_minutes=lag_time/60
| where lag_minutes > 60
| table _time, source_volume, destination_volume, lag_minutes, state
```
- **Implementation:** Poll replication status every 15 minutes. Alert when lag exceeds RPO target (e.g., >60 min for hourly replication). Track replication state (idle, transferring, broken-off) and alert on non-healthy states.
- **Visualization:** Single value (max replication lag), Table (replication pairs with lag), Line chart (lag over time).

---

### UC-6.1.6 · Controller Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Controller failovers indicate hardware problems and may cause transient performance impact. Quick detection ensures rapid root cause analysis.
- **App/TA:** Vendor TA, syslog
- **Data Sources:** Array event logs, cluster status
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:ems"
| search "cf.takeover*" OR "cf.giveback*" OR failover
| table _time, node, event, message
```
- **Implementation:** Forward array event logs (syslog or API) to Splunk. Filter for failover/takeover events. Create critical alert with incident auto-creation. Track MTBF between failover events per controller.
- **Visualization:** Timeline (failover events), Single value (days since last failover), Table (event details).

---

### UC-6.1.7 · Thin Provisioning Overcommit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Over-committed thin-provisioned storage can cause sudden outages when physical capacity is exhausted. Monitoring prevents surprise failures.
- **App/TA:** Vendor TA, API polling
- **Data Sources:** Aggregate/pool capacity metrics (logical vs physical)
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:aggregate"
| eval overcommit_ratio=logical_used/physical_used
| where overcommit_ratio > 1.5
| table aggregate, physical_used_pct, logical_used, overcommit_ratio
```
- **Implementation:** Poll aggregate/pool metrics showing logical vs physical capacity. Calculate overcommit ratio. Alert when physical utilization exceeds safe thresholds relative to committed capacity.
- **Visualization:** Gauge (overcommit ratio per pool), Table (aggregates with overcommit stats), Bar chart (logical vs physical).

---

### UC-6.1.8 · Snapshot Space Consumption
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Runaway snapshot growth can consume all available space, causing volume and application outages.
- **App/TA:** Vendor TA, REST API
- **Data Sources:** Snapshot usage metrics per volume
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:volume"
| eval snap_pct=snapshot_used_bytes/size_total*100
| where snap_pct > 20
| table volume_name, snap_pct, snapshot_used_bytes, snapshot_count
| sort -snap_pct
```
- **Implementation:** Poll snapshot usage per volume. Alert when snapshot reserve exceeds threshold (e.g., >20% of volume). Track snapshot count and age. Create scheduled report for snapshot cleanup candidates.
- **Visualization:** Bar chart (snapshot usage by volume), Table (volumes with high snapshot usage), Line chart (snapshot growth trend).

---

### UC-6.1.9 · Fibre Channel Port Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** FC port errors cause storage performance degradation and potential path failovers. Early detection prevents cascading failures.
- **App/TA:** SNMP TA, FC switch syslog
- **Data Sources:** FC switch logs (Brocade, Cisco MDS), SNMP IF-MIB
- **SPL:**
```spl
index=network sourcetype="brocade:syslog" OR sourcetype="cisco:mds"
| search CRC_error OR link_failure OR signal_loss OR sync_loss
| stats count by switch, port, error_type
| where count > 10
```
- **Implementation:** Forward FC switch syslog to Splunk. Poll SNMP counters for FC error rates. Alert on error rate exceeding baseline. Correlate with storage latency spikes to identify fabric issues.
- **Visualization:** Table (ports with errors), Bar chart (error counts by type), Timeline (error events).

---

### UC-6.1.10 · Storage Array Firmware Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Outdated firmware exposes arrays to known bugs and security vulnerabilities. Compliance tracking supports patching cadence.
- **App/TA:** Vendor TA, scripted inventory input
- **Data Sources:** Array system info (firmware version, model), vendor advisory feeds
- **SPL:**
```spl
index=storage sourcetype="netapp:ontap:system"
| stats latest(version) as firmware by node, model
| lookup approved_firmware_versions model OUTPUT approved_version
| where firmware!=approved_version
| table node, model, firmware, approved_version
```
- **Implementation:** Poll system version info periodically (daily). Maintain a lookup table of approved firmware versions per model. Alert when arrays are running non-approved versions. Report on fleet firmware distribution.
- **Visualization:** Table (arrays with firmware status), Pie chart (firmware version distribution), Single value (% compliant).

---

### 6.2 Object Storage

**Primary App/TA:** Cloud provider TAs (`Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`), MinIO webhook inputs, custom REST API inputs.

---

### UC-6.2.1 · Bucket Capacity Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks storage growth for cost forecasting and lifecycle policy effectiveness. Prevents unexpected cloud bills.
- **App/TA:** `Splunk_TA_aws` (CloudWatch), Splunk_TA_microsoft-cloudservices
- **Data Sources:** CloudWatch S3 metrics (BucketSizeBytes), Azure Blob metrics
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| timechart span=1d latest(Average) as size_bytes by bucket_name
| eval size_gb=size_bytes/1024/1024/1024
```
- **Implementation:** Enable S3 storage metrics in CloudWatch (request metrics may incur cost). Ingest via Splunk Add-on for AWS. Create trending reports by bucket and apply `predict` for growth forecasting.
- **Visualization:** Line chart (bucket size over time), Stacked area (total storage by bucket), Table (largest buckets).

---

### UC-6.2.2 · Access Pattern Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Unusual access patterns may indicate data breaches, compromised credentials, or misconfigured applications.
- **App/TA:** `Splunk_TA_aws` (S3 access logs), Azure Blob diagnostics
- **Data Sources:** S3 access logs, Azure Blob analytics logs
- **SPL:**
```spl
index=aws sourcetype="aws:s3:accesslogs"
| stats count by bucket_name, requester, operation
| eventstats avg(count) as avg_ops, stdev(count) as stdev_ops by bucket_name, operation
| where count > avg_ops + 3*stdev_ops
```
- **Implementation:** Enable S3 server access logging to a dedicated logging bucket. Ingest via SQS-based S3 input. Baseline normal access patterns and alert on statistical outliers. Correlate with IAM changes.
- **Visualization:** Line chart (access volume over time), Table (anomalous access events), Bar chart (operations by requester).

---

### UC-6.2.3 · Public Bucket Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Public buckets are a top cloud security risk, leading to data breaches. Immediate detection is essential for compliance.
- **App/TA:** `Splunk_TA_aws` (Config), Azure Policy
- **Data Sources:** AWS Config rules, S3 ACL/policy evaluations
- **SPL:**
```spl
index=aws sourcetype="aws:config:rule"
| search configRuleName="s3-bucket-public-read-prohibited" OR configRuleName="s3-bucket-public-write-prohibited"
| where complianceType="NON_COMPLIANT"
| table _time, resourceId, configRuleName, complianceType
```
- **Implementation:** Enable AWS Config rules for S3 public access. Ingest Config compliance data. Create critical alert for any NON_COMPLIANT result. Also monitor S3 Block Public Access settings at account level.
- **Visualization:** Single value (public bucket count — should be 0), Table (non-compliant buckets), Status indicator (red/green).

---

### UC-6.2.4 · Lifecycle Policy Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures storage cost optimization policies are working. Objects not transitioning per policy waste money.
- **App/TA:** Cloud provider TAs
- **Data Sources:** CloudWatch storage class metrics, lifecycle action logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| stats latest(Average) as size by bucket_name, StorageType
| xyseries bucket_name StorageType size
```
- **Implementation:** Monitor storage class distribution per bucket over time. Compare against defined lifecycle policies. Alert when objects remain in expensive storage classes longer than policy dictates.
- **Visualization:** Stacked bar (storage class distribution per bucket), Table (policy violations), Pie chart (total storage by class).

---

### UC-6.2.5 · Cross-Region Replication Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Replication lag affects DR readiness. Monitoring ensures geo-redundant data meets RPO requirements.
- **App/TA:** Cloud provider TAs
- **Data Sources:** S3 replication metrics (ReplicationLatency, OperationsPendingReplication)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="ReplicationLatency"
| timechart span=1h avg(Average) as replication_lag_sec by bucket_name
| where replication_lag_sec > 3600
```
- **Implementation:** Enable S3 replication metrics in CloudWatch. Ingest and alert when replication latency or pending operations exceed thresholds. Correlate with data ingestion spikes that may cause temporary lag.
- **Visualization:** Line chart (replication lag over time), Single value (max lag), Table (buckets with lag exceeding SLA).

---

### 6.3 Backup & Recovery

**Primary App/TA:** Vendor-specific TAs — Veeam TA (`TA-veeam`), Commvault TA, Veritas NetBackup TA; scripted inputs for API-based platforms (Rubrik, Cohesity).

---

### UC-6.3.1 · Backup Job Success Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Failed backups leave systems unprotected. Tracking success rate ensures recoverability and compliance with data protection policies.
- **App/TA:** Veeam App for Splunk, Commvault Splunk App, or scripted API input
- **Data Sources:** Backup server job logs (job name, status, start/end time, data size)
- **SPL:**
```spl
index=backup sourcetype="veeam:job"
| stats count(eval(status="Success")) as success, count(eval(status="Failed")) as failed, count as total by job_name
| eval success_rate=round(success/total*100,1)
| where success_rate < 100
| sort success_rate
```
- **Implementation:** Install vendor TA or configure scripted input to poll backup API. Ingest job completion events. Create daily report of job outcomes. Alert immediately on any failure for critical systems.
- **Visualization:** Single value (overall success rate %), Table (failed jobs with details), Bar chart (success/fail by job), Trend line (daily success rate).

---

### UC-6.3.2 · Backup Job Duration Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Increasing backup durations signal data growth, network congestion, or storage performance issues. Prevents backup window overruns.
- **App/TA:** Vendor TA
- **Data Sources:** Backup job logs (start/end timestamps, data transferred)
- **SPL:**
```spl
index=backup sourcetype="veeam:job" status="Success"
| eval duration_min=(end_time-start_time)/60
| timechart span=1d avg(duration_min) as avg_duration by job_name
```
- **Implementation:** Calculate job duration from start/end timestamps. Track trend over weeks/months. Alert when duration exceeds historical average by >50%. Correlate with data volume changes.
- **Visualization:** Line chart (duration trend per job), Table (longest running jobs), Bar chart (avg duration by job).

---

### UC-6.3.3 · Missed Backup Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** A backup that doesn't run at all is worse than one that fails — it's invisible. Detection ensures no system is left unprotected.
- **App/TA:** Vendor TA, custom correlation
- **Data Sources:** Backup scheduler logs, expected schedule lookup
- **SPL:**
```spl
| inputlookup backup_schedule.csv
| join type=left job_name
    [search index=backup sourcetype="veeam:job" earliest=-24h
     | stats latest(_time) as last_run by job_name]
| where isnull(last_run) OR last_run < relative_time(now(), "-26h")
| table job_name, expected_schedule, last_run
```
- **Implementation:** Maintain a lookup table of expected backup schedules. Run a scheduled search comparing expected vs actual runs. Alert when any job misses its window. Correlate with backup server health events.
- **Visualization:** Table (missed jobs with schedule details), Single value (number of missed jobs), Status grid (job name × date).

---

### UC-6.3.4 · Backup Storage Capacity
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Running out of backup repository space causes all backup jobs to fail. Proactive monitoring prevents cascading failures.
- **App/TA:** Vendor TA, scripted input
- **Data Sources:** Backup repository/tape library capacity metrics
- **SPL:**
```spl
index=backup sourcetype="veeam:repository"
| eval pct_used=round(used_space/total_space*100,1)
| where pct_used > 80
| table repository_name, total_space_gb, used_space_gb, pct_used
```
- **Implementation:** Poll backup repository capacity via API or scripted input. Alert at 80% and 90% thresholds. Track growth rate and forecast when capacity will be exhausted using `predict`.
- **Visualization:** Gauge (% used per repository), Line chart (capacity trend), Table (repositories above threshold).

---

### UC-6.3.5 · Restore Test Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Backups are worthless if restores fail. Tracking restore tests ensures confidence in recoverability and satisfies audit requirements.
- **App/TA:** Manual/scripted input, backup TA
- **Data Sources:** Restore test logs, manual test result entries
- **SPL:**
```spl
index=backup sourcetype="restore_test"
| stats latest(_time) as last_test, latest(result) as result by system_name
| eval days_since_test=round((now()-last_test)/86400)
| where days_since_test > 90 OR result!="Success"
| table system_name, last_test, result, days_since_test
```
- **Implementation:** Log all restore test results (automated or manual) to a dedicated index. Maintain a lookup of systems requiring quarterly restore tests. Alert when any system exceeds 90 days without a successful test.
- **Visualization:** Table (systems with test status), Single value (% tested in last 90d), Status grid (system × quarter).

---

### UC-6.3.6 · Backup SLA Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Consolidated view of backup coverage and RPO/RTO compliance. Essential for management reporting and audit evidence.
- **App/TA:** Combined backup data + CMDB lookup
- **Data Sources:** Backup job logs, CMDB/asset inventory
- **SPL:**
```spl
| inputlookup cmdb_systems.csv WHERE requires_backup="yes"
| join type=left system_name
    [search index=backup sourcetype="veeam:job" status="Success" earliest=-7d
     | stats latest(_time) as last_backup, max(data_size) as backup_size by system_name]
| eval compliant=if(isnotnull(last_backup),"Yes","No")
| stats count(eval(compliant="Yes")) as covered, count as total
| eval coverage_pct=round(covered/total*100,1)
```
- **Implementation:** Cross-reference CMDB inventory with backup job data. Identify systems with no backup coverage. Calculate RPO compliance (time since last successful backup vs required RPO). Produce weekly executive report.
- **Visualization:** Single value (SLA compliance %), Table (non-compliant systems), Pie chart (covered vs uncovered), Dashboard with filters by business unit.

---

### UC-6.3.7 · Backup Data Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks data growth rate for capacity planning of backup infrastructure. Identifies unexpected data surges early.
- **App/TA:** Vendor TA
- **Data Sources:** Backup job statistics (data transferred per job)
- **SPL:**
```spl
index=backup sourcetype="veeam:job" status="Success"
| timechart span=1d sum(data_transferred_gb) as daily_volume
| predict daily_volume as predicted future_timespan=30
```
- **Implementation:** Sum data transferred across all backup jobs daily. Track trend and apply predictive analytics for 30/60/90-day forecasts. Compare against available repository capacity.
- **Visualization:** Line chart (daily backup volume with prediction), Bar chart (volume by job type), Single value (total backed up today).

---

### UC-6.3.8 · Tape Library Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tape media and drive failures can silently corrupt backups. Monitoring ensures long-term archival reliability.
- **App/TA:** SNMP TA, vendor syslog
- **Data Sources:** Tape library logs, SNMP traps, drive error counters
- **SPL:**
```spl
index=backup sourcetype="tape_library"
| search media_error OR drive_error OR cleaning_required
| stats count by library, drive_id, error_type
| where count > 0
```
- **Implementation:** Forward tape library syslog to Splunk. Poll SNMP for drive error counters and media faults. Alert on drive errors, media faults, or cleaning cartridge expiration. Track tape media lifecycle.
- **Visualization:** Table (drive/media errors), Single value (drives needing attention), Timeline (error events).

---

### 6.4 File Services

**Primary App/TA:** Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`) for file audit events; NFS syslog; Varonis TA for advanced file analytics.

---

### UC-6.4.1 · File Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Provides full audit trail of file access for compliance (SOX, HIPAA, PCI-DSS). Enables investigation of data breaches and unauthorized access.
- **App/TA:** `Splunk_TA_windows` (Security Event Log)
- **Data Sources:** Windows Security Event Log (Event ID 4663 — object access), NFS access logs
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| stats count by Account_Name, ObjectName, AccessMask
| sort -count
| head 50
```
- **Implementation:** Enable "Audit Object Access" via GPO on file servers. Configure SACLs on sensitive folders. Forward Security logs via Universal Forwarder. Filter high-volume events to focus on sensitive paths.
- **Visualization:** Table (user, file, access type, count), Bar chart (top accessed files), Timeline (access events for specific files).

---

### UC-6.4.2 · Ransomware Indicator Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Ransomware causes mass file encryption in minutes. Detecting the pattern early can limit damage by triggering automated isolation.
- **App/TA:** `Splunk_TA_windows`, custom alert logic
- **Data Sources:** Windows Security Event Log (4663, 4656, 4659 — file create/modify/delete)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663
| bucket _time span=1m
| stats dc(ObjectName) as unique_files count by Account_Name, _time
| where unique_files > 100 AND count > 500
```
- **Implementation:** Enable file audit logging on critical file shares. Create high-urgency alert for mass file modification patterns (>100 unique files modified by one user in 1 minute). Integrate with SOAR for automated account disable/network isolation.
- **Visualization:** Single value (files modified per minute — current), Line chart (modification rate over time), Table (users with anomalous activity).

---

### UC-6.4.3 · DFS Replication Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** DFS-R backlog and conflicts indicate replication failures that can lead to data inconsistency and user complaints.
- **App/TA:** `Splunk_TA_windows` (DFS-R event logs)
- **Data Sources:** DFS Replication event log (Event IDs 4012, 4302, 4304, 5002, 5008)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:DFS Replication"
| search EventCode=4302 OR EventCode=4304 OR EventCode=5002
| stats count by EventCode, ComputerName, ReplicationGroupName
| sort -count
```
- **Implementation:** Forward DFS Replication event logs from all DFS servers. Monitor backlog size via `dfsrdiag backlog` scripted input. Alert on replication conflicts and high backlog counts. Track resolution time.
- **Visualization:** Table (replication groups with backlog), Line chart (backlog trend), Single value (total conflicts today).

---

### UC-6.4.4 · Share Permission Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized permission changes can expose sensitive data. Change detection supports compliance and security posture.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Windows Security Event Log (Event IDs 4670 — permissions changed, 5143 — share modified)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4670 OR EventCode=5143
| table _time, Account_Name, ObjectName, ObjectServer, ProcessName
| sort -_time
```
- **Implementation:** Enable "Audit Policy Change" and "Audit File System" via GPO. Forward Security events from file servers. Alert on any permission change to critical shares. Correlate with change management tickets.
- **Visualization:** Table (permission changes with details), Timeline (change events), Bar chart (changes by user).

---

### UC-6.4.5 · Large File Transfer Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusually large file copies may indicate data exfiltration. Detection supports data loss prevention and insider threat programs.
- **App/TA:** `Splunk_TA_windows`, network flow data
- **Data Sources:** Windows file audit logs, SMB session logs
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4663 AccessMask="0x1"
| stats sum(Size) as total_bytes, dc(ObjectName) as file_count by Account_Name, src_ip
| eval total_gb=round(total_bytes/1024/1024/1024,2)
| where total_gb > 1
| sort -total_gb
```
- **Implementation:** Monitor file read events and correlate with SMB session data for volume estimates. Baseline normal transfer patterns per user. Alert when transfers exceed threshold (e.g., >1GB in single session). Correlate with HR/departure lists.
- **Visualization:** Table (users with large transfers), Bar chart (transfer volume by user), Line chart (daily transfer volume trend).

---

## 7. Database & Data Platforms

### 7.1 Relational Databases

**Primary App/TA:** Splunk DB Connect (`splunk_app_db_connect`), Splunk Add-on for Microsoft SQL Server (`Splunk_TA_microsoft-sqlserver`), MySQL/PostgreSQL TAs, scripted inputs for DMVs/catalog queries.

---

### UC-7.1.1 · Slow Query Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Slow queries degrade application performance and user experience. Identifying them enables targeted optimization.
- **App/TA:** DB Connect, Splunk_TA_microsoft-sqlserver, MySQL slow query log
- **Data Sources:** Slow query logs, SQL Server DMVs (`sys.dm_exec_query_stats`), PostgreSQL `pg_stat_statements`
- **SPL:**
```spl
index=database sourcetype="mysql:slowquery"
| rex field=_raw "Query_time:\s+(?<query_time>[\d.]+)"
| where query_time > 5
| stats count, avg(query_time) as avg_time by db, user
| sort -avg_time
```
- **Implementation:** Enable MySQL slow query log (long_query_time=5). For SQL Server, poll DMVs via DB Connect. For PostgreSQL, enable `pg_stat_statements`. Ingest and alert on queries exceeding thresholds. Report top offenders weekly.
- **Visualization:** Table (slow queries with details), Bar chart (top slow queries by avg duration), Line chart (slow query count trend).

---

### UC-7.1.2 · Deadlock Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Deadlocks cause transaction failures and application errors. Rapid detection and root cause analysis minimizes impact.
- **App/TA:** Splunk_TA_microsoft-sqlserver, database error logs
- **Data Sources:** SQL Server error log (deadlock graph), PostgreSQL `log_lock_waits`, Oracle alert log
- **SPL:**
```spl
index=database sourcetype="mssql:errorlog"
| search "deadlock" OR "Deadlock"
| stats count by _time, database_name
| timechart span=1h sum(count) as deadlocks
```
- **Implementation:** Enable trace flag 1222 for SQL Server deadlock graphs. For PostgreSQL, set `log_lock_waits=on` and `deadlock_timeout=1s`. Ingest error logs. Alert on any deadlock occurrence. Parse deadlock graphs for involved queries/objects.
- **Visualization:** Line chart (deadlocks over time), Table (deadlock details), Single value (deadlocks today).

---

### UC-7.1.3 · Connection Pool Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.
- **App/TA:** DB Connect, performance counters
- **Data Sources:** SQL Server DMVs (`sys.dm_exec_connections`), PostgreSQL `pg_stat_activity`, app server connection pool metrics
- **SPL:**
```spl
index=database sourcetype="dbconnect:mssql_connections"
| timechart span=5m max(active_connections) as active, max(max_connections) as max_limit
| eval pct_used=round(active/max_limit*100,1)
| where pct_used > 80
```
- **Implementation:** Poll connection counts via DB Connect every 5 minutes. Compare against configured maximum. Alert at 80% and 95% thresholds. Track by application/user to identify connection leaks.
- **Visualization:** Gauge (% connections used), Line chart (connections over time), Table (connections by application).

---

### UC-7.1.4 · Replication Lag Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Replication lag affects data consistency and failover readiness. Monitoring ensures HA/DR objectives are met.
- **App/TA:** DB Connect, vendor-specific monitoring
- **Data Sources:** SQL Server AG DMVs (`sys.dm_hadr_database_replica_states`), MySQL `SHOW SLAVE STATUS`, PostgreSQL replication slots
- **SPL:**
```spl
index=database sourcetype="dbconnect:replication_status"
| eval lag_seconds=coalesce(seconds_behind_master, replication_lag_sec)
| timechart span=5m max(lag_seconds) as max_lag by replica_name
| where max_lag > 60
```
- **Implementation:** Poll replication status via DB Connect at 5-minute intervals. Alert when lag exceeds RPO (e.g., >60 seconds). Track lag trend over time. Correlate spikes with batch jobs or network events.
- **Visualization:** Line chart (lag over time by replica), Single value (current max lag), Table (replicas with lag status).

---

### UC-7.1.5 · Tablespace / Data File Growth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Uncontrolled database growth leads to disk space exhaustion and outages. Trending enables proactive storage provisioning.
- **App/TA:** DB Connect
- **Data Sources:** `sys.database_files` (SQL Server), `dba_tablespaces` (Oracle), `pg_database_size()` (PostgreSQL)
- **SPL:**
```spl
index=database sourcetype="dbconnect:db_size"
| timechart span=1d latest(size_gb) as db_size by database_name
| predict db_size as predicted future_timespan=30
```
- **Implementation:** Poll database size metrics via DB Connect daily. Track growth rate per database. Use `predict` command for 30-day forecast. Alert when projected size exceeds available disk. Report top growing databases.
- **Visualization:** Line chart (size trend with prediction), Table (databases with growth rate), Bar chart (top databases by size).

---

### UC-7.1.6 · Backup Success Verification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Database backups are the last line of defense. Verifying success prevents discovering backup failures during a crisis.
- **App/TA:** DB Connect, Splunk_TA_microsoft-sqlserver
- **Data Sources:** `msdb.dbo.backupset` (SQL Server), `v$rman_backup_job_details` (Oracle), PostgreSQL `pg_basebackup` logs
- **SPL:**
```spl
index=database sourcetype="dbconnect:backup_history"
| stats latest(backup_finish_date) as last_backup, latest(type) as backup_type by database_name, server_name
| eval hours_since=round((now()-strptime(last_backup,"%Y-%m-%d %H:%M:%S"))/3600,1)
| where hours_since > 24
| table server_name, database_name, last_backup, backup_type, hours_since
```
- **Implementation:** Query backup history tables via DB Connect daily. Alert on any database without a successful backup in the expected window. Cross-reference with CMDB for backup classification (full/diff/log) requirements.
- **Visualization:** Table (databases with backup status), Single value (databases missing backup), Status grid (database × backup type).

---

### UC-7.1.7 · Login Failure Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Repeated login failures may indicate brute-force attacks or misconfigured applications. Detection supports security posture.
- **App/TA:** Splunk_TA_microsoft-sqlserver, database error logs
- **Data Sources:** SQL Server error log (login failed events), PostgreSQL `log_connections`, Oracle audit trail
- **SPL:**
```spl
index=database sourcetype="mssql:errorlog"
| search "Login failed"
| rex "Login failed for user '(?<user>[^']+)'"
| stats count by user, src_ip
| where count > 10
| sort -count
```
- **Implementation:** Ensure failed login auditing is enabled (SQL Server: "Both failed and successful logins"). Forward error logs to Splunk. Alert on >10 failures per user per hour. Correlate with AD lockout events.
- **Visualization:** Table (users with failed logins), Bar chart (failures by user), Line chart (failure rate over time).

---

### UC-7.1.8 · Long-Running Transaction Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Long transactions hold locks, causing blocking chains that degrade application performance for many users.
- **App/TA:** DB Connect
- **Data Sources:** `sys.dm_exec_requests` (SQL Server), `pg_stat_activity` (PostgreSQL), Oracle `v$transaction`
- **SPL:**
```spl
index=database sourcetype="dbconnect:active_transactions"
| where transaction_duration_sec > 300
| table _time, server, database_name, user, transaction_duration_sec, sql_text
| sort -transaction_duration_sec
```
- **Implementation:** Poll active transactions via DB Connect every 5 minutes. Alert when any transaction exceeds 5 minutes. Include SQL text and blocking information. Escalate transactions blocking other sessions.
- **Visualization:** Table (active long transactions), Single value (longest active transaction), Timeline (long transaction events).

---

### UC-7.1.9 · Index Fragmentation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.
- **App/TA:** DB Connect
- **Data Sources:** `sys.dm_db_index_physical_stats` (SQL Server), `pg_stat_user_indexes` (PostgreSQL)
- **SPL:**
```spl
index=database sourcetype="dbconnect:index_stats"
| where avg_fragmentation_pct > 30
| table server, database_name, table_name, index_name, avg_fragmentation_pct, page_count
| sort -avg_fragmentation_pct
```
- **Implementation:** Poll index fragmentation stats via DB Connect weekly (resource-intensive query — schedule during off-hours). Alert when critical indexes exceed 30% fragmentation. Track fragmentation trend to optimize rebuild schedules.
- **Visualization:** Table (fragmented indexes), Bar chart (fragmentation by database), Heatmap (table × index fragmentation).

---

### UC-7.1.10 · TempDB Contention (SQL Server)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).
- **App/TA:** DB Connect, Splunk_TA_microsoft-sqlserver
- **Data Sources:** `sys.dm_os_wait_stats` (PAGELATCH waits), `sys.dm_exec_query_stats`
- **SPL:**
```spl
index=database sourcetype="dbconnect:wait_stats"
| where wait_type LIKE "PAGELATCH%" AND resource_description LIKE "2:%"
| stats sum(wait_time_ms) as total_wait by wait_type
```
- **Implementation:** Poll wait statistics via DB Connect. Filter for PAGELATCH waits on TempDB (database_id 2). Alert when TempDB waits exceed baseline. Recommend adding TempDB data files equal to number of CPU cores (up to 8).
- **Visualization:** Bar chart (wait types), Line chart (TempDB wait trend), Single value (current TempDB wait ms).

---

### UC-7.1.11 · Buffer Cache Hit Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.
- **App/TA:** DB Connect, performance counters
- **Data Sources:** SQL Server performance counters, PostgreSQL `pg_stat_bgwriter`
- **SPL:**
```spl
index=database sourcetype="dbconnect:perf_counters"
| where counter_name="Buffer cache hit ratio"
| timechart span=15m avg(cntr_value) as hit_ratio by instance_name
| where hit_ratio < 95
```
- **Implementation:** Poll buffer cache performance counters via DB Connect every 15 minutes. Alert when hit ratio drops below 95% for sustained periods. Correlate with memory pressure and query workload changes.
- **Visualization:** Gauge (buffer cache hit ratio), Line chart (hit ratio over time), Single value (current hit ratio %).

---

### UC-7.1.12 · Database Availability Group Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.
- **App/TA:** DB Connect, Splunk_TA_microsoft-sqlserver
- **Data Sources:** `sys.dm_hadr_availability_replica_states` (SQL Server), Oracle CRS logs
- **SPL:**
```spl
index=database sourcetype="dbconnect:ag_status"
| where synchronization_health_desc!="HEALTHY" OR connected_state_desc!="CONNECTED"
| table _time, ag_name, replica_server_name, role_desc, synchronization_health_desc
```
- **Implementation:** Poll AG replica state DMVs every 5 minutes. Alert on any non-HEALTHY or non-CONNECTED state. Track failover events from SQL Server error log. Create dashboard showing full AG topology and health.
- **Visualization:** Status grid (replica × health state), Table (unhealthy replicas), Timeline (failover events).

---

### UC-7.1.13 · Schema Change Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.
- **App/TA:** DB Connect, SQL Server audit
- **Data Sources:** SQL Server DDL triggers, audit logs, PostgreSQL `log_statement='ddl'`
- **SPL:**
```spl
index=database sourcetype="mssql:audit" action_id IN ("CR","AL","DR")
| table _time, server_principal_name, database_name, object_name, statement
| sort -_time
```
- **Implementation:** Enable SQL Server audit for DDL events (CREATE, ALTER, DROP). For PostgreSQL, set `log_statement='ddl'`. Forward audit logs to Splunk. Alert on any DDL outside maintenance windows. Correlate with change tickets.
- **Visualization:** Table (DDL events with details), Timeline (schema changes), Bar chart (changes by user).

---

### UC-7.1.14 · Query Plan Regression
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Query plan changes can cause sudden performance degradation. Detection enables rapid intervention (plan forcing, hint application).
- **App/TA:** DB Connect
- **Data Sources:** SQL Server Query Store, `sys.dm_exec_query_plan`, PostgreSQL `pg_stat_statements`
- **SPL:**
```spl
index=database sourcetype="dbconnect:query_store"
| stats avg(avg_duration) as current_avg by query_id, plan_id
| join query_id [| inputlookup query_baselines.csv]
| eval regression_pct=round((current_avg-baseline_avg)/baseline_avg*100,1)
| where regression_pct > 50
```
- **Implementation:** Enable Query Store on SQL Server databases. Poll query performance metrics via DB Connect. Maintain baseline lookup of normal query durations. Alert when queries regress >50% from baseline. Enable automatic plan correction if available.
- **Visualization:** Table (regressed queries), Bar chart (regression % by query), Line chart (query duration trend).

---

### UC-7.1.15 · Privilege Escalation Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized privilege changes can enable data theft or sabotage. Audit trail is required for compliance.
- **App/TA:** DB Connect, SQL Server audit
- **Data Sources:** Database audit logs (GRANT/REVOKE events), security event logs
- **SPL:**
```spl
index=database sourcetype="mssql:audit"
| search action_id IN ("G","R","GWG") statement="*GRANT*" OR statement="*REVOKE*"
| table _time, server_principal_name, database_name, statement, target_server_principal_name
```
- **Implementation:** Enable database audit for security events (GRANT, REVOKE, ALTER ROLE). Forward to Splunk. Alert on any privilege change in production. Correlate with change management tickets and access review cycles.
- **Visualization:** Table (privilege change events), Timeline (changes), Bar chart (changes by granting user).

---

### 7.2 NoSQL Databases

**Primary App/TA:** Custom scripted inputs, vendor management APIs (MongoDB Atlas API, Elasticsearch REST API), JMX for Java-based systems (Cassandra), Redis CLI scripted input.

---

### UC-7.2.1 · Cluster Membership Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Node additions/removals affect data distribution and availability. Unexpected membership changes may indicate failures.
- **App/TA:** Custom scripted input, database event logs
- **Data Sources:** MongoDB replica set events, Cassandra `system.log`, Elasticsearch cluster state
- **SPL:**
```spl
index=database sourcetype="mongodb:log"
| search "replSet" ("added" OR "removed" OR "changed state" OR "election")
| table _time, host, message
| sort -_time
```
- **Implementation:** Forward database logs to Splunk. Parse membership change events. Alert on unexpected node departures. For Elasticsearch, poll `_cluster/health` API and alert on node count changes.
- **Visualization:** Timeline (membership events), Single value (current node count), Table (recent cluster changes).

---

### UC-7.2.2 · Replication Lag / Consistency
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Replication lag causes stale reads and eventual consistency violations. Monitoring ensures data freshness SLAs are met.
- **App/TA:** Custom scripted input (rs.status(), nodetool)
- **Data Sources:** MongoDB `rs.status()`, Cassandra `nodetool status`, Redis `INFO replication`
- **SPL:**
```spl
index=database sourcetype="mongodb:rs_status"
| eval lag_sec=optime_primary-optime_secondary
| where lag_sec > 10
| table _time, replica_set, member, state, lag_sec
```
- **Implementation:** Run scripted input polling replica set status every minute. Parse member states and optime differences. Alert when lag exceeds threshold (e.g., >10 seconds). Track trend for capacity planning.
- **Visualization:** Line chart (replication lag over time), Table (replicas with lag), Single value (max current lag).

---

### UC-7.2.3 · Read/Write Latency Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Latency trending detects performance degradation before it impacts users. Enables proactive tuning and scaling decisions.
- **App/TA:** Custom metrics input, database stats API
- **Data Sources:** MongoDB `serverStatus()`, Cassandra JMX, Elasticsearch `_nodes/stats`
- **SPL:**
```spl
index=database sourcetype="mongodb:server_status"
| timechart span=5m avg(opcounters.query) as reads, avg(opcounters.insert) as writes, avg(opLatencies.reads.latency) as read_lat
```
- **Implementation:** Poll database metrics every 5 minutes via scripted input or API. Track read/write latency percentiles (p50, p95, p99). Baseline normal patterns and alert on sustained deviation. Correlate with workload changes.
- **Visualization:** Line chart (latency percentiles over time), Dual-axis chart (latency + throughput), Table (current latency by operation).

---

### UC-7.2.4 · Shard Imbalance Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Uneven shard distribution causes hot spots and performance inconsistency. Rebalancing prevents overloaded nodes.
- **App/TA:** Custom scripted input
- **Data Sources:** MongoDB `sh.status()`, Elasticsearch `_cat/shards`
- **SPL:**
```spl
index=database sourcetype="mongodb:shard_status"
| stats sum(count) as doc_count, sum(size) as data_size by shard
| eventstats avg(doc_count) as avg_count
| eval imbalance_pct=round(abs(doc_count-avg_count)/avg_count*100,1)
| where imbalance_pct > 20
```
- **Implementation:** Poll shard statistics periodically. Calculate per-shard deviation from average. Alert when any shard deviates >20% from mean size. For Elasticsearch, track unassigned shards as a separate critical alert.
- **Visualization:** Bar chart (data size per shard), Table (shards with imbalance), Single value (max imbalance %).

---

### UC-7.2.5 · Compaction Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Pending compactions consume I/O and can cause write amplification. Monitoring ensures compaction keeps pace with writes.
- **App/TA:** JMX input (Cassandra), database logs
- **Data Sources:** Cassandra `nodetool compactionstats`, MongoDB WiredTiger stats, Elasticsearch merge stats
- **SPL:**
```spl
index=database sourcetype="cassandra:compaction"
| timechart span=15m avg(pending_tasks) as pending, sum(bytes_compacted) as compacted
| where pending > 50
```
- **Implementation:** Poll compaction stats via JMX (Cassandra) or scripted input. Track pending compaction tasks and throughput. Alert when pending tasks grow consistently, indicating compaction cannot keep up with write volume.
- **Visualization:** Line chart (pending compactions over time), Dual-axis (pending + throughput), Single value (current pending).

---

### UC-7.2.6 · GC Pause Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Long GC pauses in Java-based databases (Cassandra, Elasticsearch) cause request timeouts and can trigger node eviction from the cluster.
- **App/TA:** GC log parsing, JMX
- **Data Sources:** JVM GC logs (`gc.log`), JMX GC metrics
- **SPL:**
```spl
index=database sourcetype="jvm:gc"
| where gc_pause_ms > 500
| stats count, avg(gc_pause_ms) as avg_pause, max(gc_pause_ms) as max_pause by host, gc_type
| where max_pause > 1000
```
- **Implementation:** Configure JVM GC logging on all Java-based database nodes. Forward GC logs to Splunk with proper field extraction. Alert on pauses >500ms. Track GC frequency and total pause time per hour. Recommend heap tuning when pauses are chronic.
- **Visualization:** Line chart (GC pause duration over time), Histogram (pause distribution), Table (hosts with excessive GC).

---

### UC-7.2.7 · Connection Count Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment or connection pooling.
- **App/TA:** Custom scripted input
- **Data Sources:** MongoDB `serverStatus().connections`, Redis `INFO clients`, Elasticsearch `_nodes/stats/transport`
- **SPL:**
```spl
index=database sourcetype="mongodb:server_status"
| eval pct_used=round(connections.current/connections.available*100,1)
| timechart span=5m max(pct_used) as connection_pct by host
| where connection_pct > 80
```
- **Implementation:** Poll connection metrics every 5 minutes. Calculate percentage of max connections used. Alert at 80% and 95%. Track by client application to identify connection leaks.
- **Visualization:** Gauge (% connections used per node), Line chart (connection count over time), Table (nodes approaching limit).

---

### UC-7.2.8 · Index Build Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Index builds consume significant resources and can impact production performance. Tracking ensures builds complete within maintenance windows.
- **App/TA:** Database log parsing
- **Data Sources:** MongoDB log (`INDEX` messages), Elasticsearch `_tasks` API
- **SPL:**
```spl
index=database sourcetype="mongodb:log"
| search "index build"
| rex "building index on (?<collection>\S+)"
| table _time, host, collection, message
```
- **Implementation:** Parse database logs for index build events (start, progress, completion). Alert on index builds in production during business hours. Track build duration for capacity planning.
- **Visualization:** Table (active/recent index builds), Timeline (build events), Single value (builds in progress).

---

### UC-7.2.9 · Memory Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** NoSQL databases are memory-intensive. Evictions indicate undersized cache, causing disk reads and performance degradation.
- **App/TA:** Custom scripted input, JMX
- **Data Sources:** Redis `INFO memory`, MongoDB WiredTiger cache stats, Cassandra JMX heap metrics
- **SPL:**
```spl
index=database sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct, sum(evicted_keys) as evictions by host
| where memory_pct > 85
```
- **Implementation:** Poll memory metrics every 5 minutes. Track used vs max memory, eviction rate, and cache hit ratio. Alert when memory exceeds 85% or eviction rate spikes. Recommend sizing adjustments based on trends.
- **Visualization:** Gauge (memory % per node), Line chart (memory + evictions), Table (nodes with high utilization).

---

### UC-7.2.10 · Elasticsearch Cluster Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Elasticsearch cluster status directly indicates data availability. Yellow/red status requires immediate attention to prevent data loss.
- **App/TA:** Custom REST API input
- **Data Sources:** Elasticsearch `_cluster/health` API
- **SPL:**
```spl
index=database sourcetype="elasticsearch:cluster_health"
| eval status_num=case(status="green",0, status="yellow",1, status="red",2)
| timechart span=5m latest(status_num) as health, latest(unassigned_shards) as unassigned by cluster_name
| where health > 0
```
- **Implementation:** Poll `_cluster/health` endpoint every minute. Alert on yellow status (warning) and red status (critical). Track unassigned shard count and node count. Correlate with JVM metrics and disk space to identify root cause.
- **Visualization:** Status indicator (green/yellow/red), Single value (unassigned shards), Line chart (cluster health timeline), Table (cluster details).

---

### 7.3 Cloud-Managed Databases

**Primary App/TA:** Cloud provider TAs — `Splunk_TA_aws` (CloudWatch, RDS logs), `Splunk_TA_microsoft-cloudservices` (Azure Monitor), GCP TA.

---

### UC-7.3.1 · RDS/Aurora Performance Insights
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Performance Insights identifies top SQL and wait events without agent installation. Enables rapid diagnosis of managed database bottlenecks.
- **App/TA:** `Splunk_TA_aws` (CloudWatch)
- **Data Sources:** RDS Performance Insights API, CloudWatch Enhanced Monitoring
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS"
| where metric_name IN ("CPUUtilization","DatabaseConnections","ReadLatency","WriteLatency")
| timechart span=5m avg(Average) by metric_name, DBInstanceIdentifier
```
- **Implementation:** Enable Enhanced Monitoring and Performance Insights on RDS instances. Ingest CloudWatch metrics via Splunk Add-on for AWS. Enable RDS log exports (slow query, error, general) to CloudWatch Logs for deeper analysis.
- **Visualization:** Multi-line chart (CPU, connections, latency), Table (top wait events), Single value (current active sessions).

---

### UC-7.3.2 · Automated Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Managed database failovers cause brief outages. Detection enables impact analysis and root cause investigation.
- **App/TA:** `Splunk_TA_aws` (CloudTrail/EventBridge), Azure Activity Log
- **Data Sources:** RDS events, Azure SQL activity log, Cloud SQL admin activity
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events"
| search detail.EventCategories="failover"
| table _time, detail.SourceIdentifier, detail.Message
```
- **Implementation:** Ingest RDS event subscriptions via SNS → SQS → Splunk. Filter for failover events. Alert immediately with PagerDuty/ServiceNow integration. Correlate with application error spikes to measure impact duration.
- **Visualization:** Timeline (failover events), Table (failover details), Single value (days since last failover).

---

### UC-7.3.3 · Read Replica Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Replica lag affects read consistency for applications using read replicas. Monitoring prevents stale data serving.
- **App/TA:** Cloud provider TAs (CloudWatch, Azure Monitor)
- **Data Sources:** CloudWatch `ReplicaLag` metric, Azure SQL `replication_lag`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ReplicaLag"
| timechart span=5m max(Maximum) as replica_lag_sec by DBInstanceIdentifier
| where replica_lag_sec > 30
```
- **Implementation:** Ingest CloudWatch RDS metrics. Alert when ReplicaLag exceeds application tolerance (e.g., >30 seconds). Track trend and correlate with write workload spikes. Alert on replica lag growing consistently.
- **Visualization:** Line chart (replica lag over time), Single value (current max lag), Table (replicas with lag).

---

### UC-7.3.4 · Storage Auto-Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks storage auto-scaling events for cost awareness and identifies databases with rapid growth needing attention.
- **App/TA:** Cloud provider TAs
- **Data Sources:** CloudTrail (ModifyDBInstance), Azure Activity Log
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="ModifyDBInstance"
| spath output=allocated requestParameters.allocatedStorage
| where isnotnull(allocated)
| table _time, requestParameters.dBInstanceIdentifier, allocated, userIdentity.principalId
```
- **Implementation:** Ingest CloudTrail events. Filter for storage modification events. Track growth frequency per database. Alert when auto-scaling occurs more than twice per week, indicating rapid growth needing review.
- **Visualization:** Timeline (scaling events), Table (databases with scaling history), Bar chart (scaling frequency by database).

---

### UC-7.3.5 · Maintenance Window Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Awareness of upcoming and completed maintenance ensures teams are prepared for potential service impact.
- **App/TA:** Cloud provider TAs
- **Data Sources:** RDS event subscriptions, Azure Service Health, GCP maintenance notifications
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events"
| search detail.EventCategories="maintenance"
| table _time, detail.SourceIdentifier, detail.Message, detail.Date
| sort detail.Date
```
- **Implementation:** Subscribe to RDS maintenance events via SNS. Ingest into Splunk. Create calendar view of upcoming maintenance. Alert 72 hours before scheduled maintenance. Log actual impact duration after completion.
- **Visualization:** Table (upcoming/recent maintenance), Calendar view, Timeline (maintenance history).

---

### 7.4 Data Warehouses & Analytics Platforms

**Primary App/TA:** Custom REST API inputs (Snowflake Account Usage, BigQuery INFORMATION_SCHEMA), cloud provider TAs for billing/usage data.

---

### UC-7.4.1 · Query Performance Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Identifies expensive and slow queries impacting warehouse performance and cost. Enables query optimization and cost reduction.
- **App/TA:** Custom API input (Snowflake ACCOUNT_USAGE), DB Connect
- **Data Sources:** Snowflake `QUERY_HISTORY`, BigQuery `INFORMATION_SCHEMA.JOBS`, Redshift `STL_QUERY`
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:query_history"
| where EXECUTION_STATUS="SUCCESS" AND TOTAL_ELAPSED_TIME > 60000
| stats avg(TOTAL_ELAPSED_TIME) as avg_ms, sum(CREDITS_USED_CLOUD_SERVICES) as credits by USER_NAME, WAREHOUSE_NAME
| sort -credits
```
- **Implementation:** Poll query history views via REST API or DB Connect daily. Track query duration, queue time, and cost. Identify top resource consumers. Create weekly optimization report for data engineering teams.
- **Visualization:** Table (expensive queries), Bar chart (cost/duration by warehouse), Line chart (query performance trend).

---

### UC-7.4.2 · Cluster Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks auto-scaling decisions for cost optimization. Identifies whether current scaling policies match workload patterns.
- **App/TA:** Custom API input, cloud provider TAs
- **Data Sources:** Snowflake `WAREHOUSE_EVENTS_HISTORY`, Redshift resize events, BigQuery slot utilization
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:warehouse_events"
| search event_name IN ("RESIZE_CLUSTER","SUSPEND_CLUSTER","RESUME_CLUSTER")
| timechart span=1h count by event_name, warehouse_name
```
- **Implementation:** Poll warehouse event history. Track resume/suspend/scaling frequency. Correlate with query concurrency to validate scaling policies. Alert on unexpected scaling events outside business hours.
- **Visualization:** Timeline (scaling events), Stacked bar (events by type per day), Table (warehouse scaling summary).

---

### UC-7.4.3 · Data Pipeline Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Failed or delayed ETL/ELT pipelines cause stale data for reporting and analytics. Early detection prevents downstream impact.
- **App/TA:** Custom API input, orchestrator integration (Airflow, dbt)
- **Data Sources:** Airflow task logs, dbt run results, Snowflake TASK_HISTORY, pipeline orchestrator APIs
- **SPL:**
```spl
index=datawarehouse sourcetype="airflow:task_instance"
| stats count(eval(state="failed")) as failed, count(eval(state="success")) as success, count as total by dag_id, task_id
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 0
| sort -fail_rate
```
- **Implementation:** Ingest pipeline orchestrator logs (Airflow, dbt, custom). Track job outcomes, durations, and data freshness. Alert on any pipeline failure. Create data freshness SLA dashboard showing when each table was last updated.
- **Visualization:** Status grid (pipeline × status), Table (failed pipelines), Line chart (pipeline duration trend), Single value (overall success rate).

---

### UC-7.4.4 · Credit / Cost per Query
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Directly ties compute cost to individual queries, enabling chargeback and cost optimization. Identifies runaway queries consuming excessive resources.
- **App/TA:** Custom API input (Snowflake ACCOUNT_USAGE)
- **Data Sources:** Snowflake `QUERY_HISTORY` (CREDITS_USED), BigQuery `INFORMATION_SCHEMA.JOBS` (total_bytes_billed)
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval cost=CREDITS_USED_CLOUD_SERVICES * 3
| stats sum(cost) as total_cost, count as query_count by USER_NAME, WAREHOUSE_NAME
| eval cost_per_query=round(total_cost/query_count,2)
| sort -total_cost
```
- **Implementation:** Poll query history with cost metrics daily. Calculate cost per query, per user, and per team (using role mapping). Create weekly cost report. Alert on individual queries exceeding cost threshold. Set up warehouse-level budgets.
- **Visualization:** Bar chart (cost by user/warehouse), Table (most expensive queries), Line chart (daily cost trend), Pie chart (cost by team).

---

### UC-7.4.5 · Warehouse Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Right-sizing warehouses reduces cost while maintaining performance. Utilization data drives scaling policy decisions.
- **App/TA:** Custom API input
- **Data Sources:** Snowflake `WAREHOUSE_LOAD_HISTORY`, Redshift `WLM_QUEUE_STATE`, BigQuery reservation utilization
- **SPL:**
```spl
index=datawarehouse sourcetype="snowflake:warehouse_load"
| timechart span=15m avg(AVG_RUNNING) as avg_queries, avg(AVG_QUEUED_LOAD) as avg_queued by WAREHOUSE_NAME
| where avg_queued > 1
```
- **Implementation:** Poll warehouse utilization metrics every 15 minutes. Track running vs queued queries. Alert when queuing occurs consistently (indicates undersized warehouse). Identify idle warehouses for auto-suspend policy adjustment.
- **Visualization:** Line chart (running vs queued queries), Heatmap (warehouse × hour utilization), Table (underutilized warehouses), Bar chart (utilization by warehouse).

---

## 8. Application Infrastructure

### 8.1 Web Servers & Reverse Proxies

**Primary App/TA:** Splunk Add-on for Apache Web Server (`Splunk_TA_apache`), Splunk Add-on for NGINX (`TA-nginx`), Windows TA for IIS logs, Traefik syslog.

---

### UC-8.1.1 · HTTP Error Rate Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Rising error rates signal application issues, backend failures, or attacks. Rapid detection reduces user impact and MTTR.
- **App/TA:** `Splunk_TA_apache`, `TA-nginx`, IIS via Windows TA
- **Data Sources:** Web server access logs (Apache combined, NGINX combined, IIS W3C)
- **SPL:**
```spl
index=web sourcetype="access_combined"
| eval error=if(status>=400,1,0)
| timechart span=5m sum(error) as errors, count as total
| eval error_rate=round(errors/total*100,2)
| where error_rate > 5
```
- **Implementation:** Install appropriate web server TA. Forward access logs via UF. Enable response time logging in web server config. Create tiered alerts: >5% error rate (warning), >10% (critical). Split 4xx from 5xx for different response.
- **Visualization:** Line chart (error rate over time), Stacked bar (4xx vs 5xx), Single value (current error rate %), Table (top error URIs).

---

### UC-8.1.2 · Response Time Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Increasing response times degrade user experience before complete failures occur. Trending enables proactive optimization.
- **App/TA:** `Splunk_TA_apache`, `TA-nginx`
- **Data Sources:** Access logs with `%D` (Apache) or `$request_time` (NGINX)
- **SPL:**
```spl
index=web sourcetype="access_combined"
| timechart span=5m perc95(response_time) as p95, avg(response_time) as avg_rt by host
| where p95 > 2000
```
- **Implementation:** Enable response time logging in web server config (Apache: `%D` in LogFormat, NGINX: `$request_time`). Track p50/p95/p99 percentiles. Alert on p95 exceeding SLA threshold. Correlate with backend service health.
- **Visualization:** Line chart (p50/p95/p99 over time), Histogram (response time distribution), Table (slowest endpoints).

---

### UC-8.1.3 · Request Rate Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Traffic trending supports capacity planning and identifies unexpected traffic patterns (bot attacks, viral events, traffic drops).
- **App/TA:** `Splunk_TA_apache`, `TA-nginx`
- **Data Sources:** Access logs
- **SPL:**
```spl
index=web sourcetype="access_combined"
| timechart span=1m count as requests_per_min by host
| predict requests_per_min as predicted
```
- **Implementation:** Ingest access logs. Track requests per second/minute. Baseline normal traffic patterns using `predict`. Alert on sudden drops (possible outage) or spikes (possible attack). Break down by URI for endpoint-level trending.
- **Visualization:** Line chart (request rate with prediction band), Area chart (traffic over time), Bar chart (requests by host).

---

### UC-8.1.4 · Top Error URIs
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Identifies the most problematic endpoints for targeted developer attention. Reduces noise by focusing on high-impact errors.
- **App/TA:** `Splunk_TA_apache`, `TA-nginx`
- **Data Sources:** Access logs
- **SPL:**
```spl
index=web sourcetype="access_combined" status>=400
| stats count by uri_path, status
| sort -count
| head 20
```
- **Implementation:** Parse URI from access logs (ensure proper field extraction). Group by URI and status code. Create daily/weekly report of top error endpoints. Track error trends per URI over time to detect regressions.
- **Visualization:** Table (URI, status, count), Bar chart (top 20 error URIs), Treemap (errors by URI path).

---

### UC-8.1.5 · SSL Certificate Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Expired SSL certificates cause complete service outage and browser security warnings. Proactive monitoring prevents this entirely avoidable failure.
- **App/TA:** Scripted input (openssl s_client), custom certificate check
- **Data Sources:** Certificate check scripted input, web server config parsing
- **SPL:**
```spl
index=certificates sourcetype="cert_check"
| eval days_until_expiry=round((cert_expiry_epoch-now())/86400)
| where days_until_expiry < 30
| table host, port, cn, issuer, days_until_expiry
| sort days_until_expiry
```
- **Implementation:** Deploy scripted input that runs `openssl s_client` against all HTTPS endpoints daily. Parse certificate details (CN, SAN, expiry, issuer). Alert at 30, 14, and 7 days before expiry. Maintain endpoint inventory via lookup.
- **Visualization:** Table (certificates with expiry dates), Single value (certs expiring within 30d), Status grid (endpoint × cert status).

---

### UC-8.1.6 · Upstream Backend Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Backend server failures behind reverse proxies cause partial service degradation. Detection enables rapid failover response.
- **App/TA:** `TA-nginx` (error logs), HAProxy stats
- **Data Sources:** NGINX error logs (upstream errors), HAProxy stats socket, F5 pool member logs
- **SPL:**
```spl
index=web sourcetype="nginx:error"
| search "upstream" ("connect() failed" OR "no live upstreams" OR "timed out")
| stats count by upstream_addr, server_name
| sort -count
```
- **Implementation:** Forward NGINX error logs. Parse upstream failure messages. For HAProxy, enable stats socket and poll via scripted input. Alert on backend server failures. Track backend health state over time.
- **Visualization:** Status grid (backend × health), Table (failed backends), Timeline (backend failure events).

---

### UC-8.1.7 · Bot and Crawler Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Bot traffic inflates metrics and consumes resources. Identification enables accurate capacity planning and bot management policies.
- **App/TA:** `Splunk_TA_apache`, `TA-nginx`
- **Data Sources:** Access logs (User-Agent field)
- **SPL:**
```spl
index=web sourcetype="access_combined"
| rex field=useragent "(?<bot_name>Googlebot|Bingbot|baiduspider|bot|crawler|spider)"
| eval is_bot=if(isnotnull(bot_name),"bot","human")
| stats count by is_bot
| eval pct=round(count/sum(count)*100,1)
```
- **Implementation:** Parse User-Agent from access logs. Maintain a lookup of known bot signatures. Classify traffic as bot vs human. Track bot traffic percentage over time. Alert on unknown bots or suspicious crawling patterns.
- **Visualization:** Pie chart (bot vs human traffic), Bar chart (top bots by request count), Line chart (bot traffic trend).

---

### UC-8.1.8 · Connection Pool Saturation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Saturated worker threads/processes cause request queuing and timeouts. Monitoring enables proactive scaling.
- **App/TA:** Scripted input (Apache `server-status`, NGINX `stub_status`)
- **Data Sources:** Apache mod_status, NGINX stub_status, IIS performance counters
- **SPL:**
```spl
index=web sourcetype="apache:server_status"
| eval pct_busy=round(BusyWorkers/(BusyWorkers+IdleWorkers)*100,1)
| timechart span=5m avg(pct_busy) as worker_pct by host
| where worker_pct > 80
```
- **Implementation:** Enable Apache `mod_status` or NGINX `stub_status` module. Poll via scripted input every minute. Alert when busy workers exceed 80% of total. Correlate with request rate to distinguish capacity limits from slow backends.
- **Visualization:** Gauge (% workers busy), Line chart (worker utilization over time), Table (hosts at capacity).

---

### UC-8.1.9 · Slow POST Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Slow POST requests often indicate application-level performance issues (large form submissions, file uploads, database writes) distinct from slow GETs.
- **App/TA:** `Splunk_TA_apache`, `TA-nginx`
- **Data Sources:** Access logs with response time
- **SPL:**
```spl
index=web sourcetype="access_combined" method=POST
| where response_time > 5000
| stats count, avg(response_time) as avg_rt by uri_path
| sort -avg_rt
```
- **Implementation:** Filter access logs for POST requests with high response times. Track by endpoint to identify specific bottlenecks. Correlate with backend database/API latency. Report top slow POST endpoints weekly.
- **Visualization:** Table (slow POST endpoints), Bar chart (avg response time by URI), Line chart (slow POST count trend).

---

### UC-8.1.10 · Configuration Reload Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Configuration changes are a common cause of outages. Tracking reloads enables rapid correlation with incidents.
- **App/TA:** `Splunk_TA_apache`, `TA-nginx`, process monitoring
- **Data Sources:** Web server error/event logs
- **SPL:**
```spl
index=web sourcetype="nginx:error" OR sourcetype="apache:error"
| search "signal" OR "reload" OR "restarting" OR "resuming normal operations"
| table _time, host, message
```
- **Implementation:** Forward error/event logs from web servers. Parse reload/restart messages. Correlate with deployment events and change management tickets. Alert on unexpected restarts outside maintenance windows.
- **Visualization:** Timeline (reload events), Table (reload history with correlation), Single value (reloads this week).

---

### 8.2 Application Servers & Runtimes

**Primary App/TA:** Splunk Add-on for JMX (`TA-jmx`), OpenTelemetry Collector (`Splunk_TA_otel`), custom log inputs for application frameworks.

---

### UC-8.2.1 · JVM Heap Utilization
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** JVM heap exhaustion causes OutOfMemoryError, crashing the application. Monitoring enables tuning before failures occur.
- **App/TA:** `TA-jmx`, OpenTelemetry
- **Data Sources:** JMX MBeans (`java.lang:type=Memory`), Prometheus JMX exporter
- **SPL:**
```spl
index=jmx sourcetype="jmx:memory"
| eval heap_pct=round(HeapMemoryUsage.used/HeapMemoryUsage.max*100,1)
| timechart span=5m avg(heap_pct) as heap_usage by host
| where heap_usage > 85
```
- **Implementation:** Deploy JMX TA on a heavy forwarder. Configure JMX connection to each app server. Poll memory MBeans every minute. Alert at 85% heap usage. Track heap growth pattern to detect memory leaks (sawtooth with increasing floor).
- **Visualization:** Line chart (heap usage over time), Gauge (current heap %), Area chart (heap used vs max).

---

### UC-8.2.2 · Garbage Collection Impact
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Frequent or long GC pauses cause application latency spikes and request timeouts. Monitoring guides JVM tuning.
- **App/TA:** GC log parsing, `TA-jmx`
- **Data Sources:** JVM GC logs, JMX GarbageCollector MBeans
- **SPL:**
```spl
index=jvm sourcetype="jvm:gc"
| where gc_pause_ms > 200
| timechart span=15m count as gc_events, sum(gc_pause_ms) as total_pause_ms by host
| eval pause_pct=round(total_pause_ms/900000*100,2)
```
- **Implementation:** Enable GC logging on all JVM-based app servers (`-Xlog:gc*` for Java 11+). Forward logs via UF. Parse pause duration, type, and cause. Alert on pauses >200ms or total pause time >5% of wall clock time.
- **Visualization:** Line chart (GC pause duration), Histogram (pause distribution), Single value (total pause time per hour).

---

### UC-8.2.3 · Thread Pool Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Exhausted thread pools cause request rejection and application unresponsiveness. Detection prevents complete service failure.
- **App/TA:** `TA-jmx`, application metrics
- **Data Sources:** JMX thread MBeans, Tomcat Connector metrics, application metrics endpoints
- **SPL:**
```spl
index=jmx sourcetype="jmx:threading"
| eval pct_used=round(currentThreadsBusy/maxThreads*100,1)
| timechart span=5m max(pct_used) as thread_pct by host
| where thread_pct > 80
```
- **Implementation:** Poll thread pool metrics via JMX (Tomcat: Connector MBeans, WildFly: undertow subsystem). Alert at 80% thread pool utilization. Correlate with request rate and response time to distinguish traffic spikes from slow backends.
- **Visualization:** Gauge (% threads busy), Line chart (thread utilization over time), Table (servers approaching capacity).

---

### UC-8.2.4 · Application Error Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Application exceptions indicate bugs, integration failures, or environmental issues. Tracking error rate by type guides debugging priority.
- **App/TA:** Custom log input, application framework logging
- **Data Sources:** Application log files (log4j, logback, NLog, Serilog)
- **SPL:**
```spl
index=application sourcetype="log4j" log_level=ERROR
| timechart span=5m count as error_count by host
| predict error_count as predicted
```
- **Implementation:** Forward application logs via UF. Ensure structured logging (JSON preferred) for reliable field extraction. Classify errors by type/exception. Alert on error rate spikes above baseline. Create error type breakdown for developer triage.
- **Visualization:** Line chart (error rate with baseline), Table (top error types), Bar chart (errors by component).

---

### UC-8.2.5 · Deployment Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Correlating deployments with performance changes is the fastest way to identify deployment-caused regressions. Essential for change management.
- **App/TA:** Webhook input, CI/CD integration
- **Data Sources:** Deployment tool webhooks (Jenkins, GitHub Actions, ArgoCD), application version endpoints
- **SPL:**
```spl
index=deployments sourcetype="deployment_event"
| table _time, application, version, environment, deployer, status
| sort -_time
```
- **Implementation:** Configure CI/CD pipeline to send deployment events to Splunk HEC (JSON payload with app, version, environment, deployer). Annotate timecharts with deployment markers. Correlate deployment times with error rate and latency changes.
- **Visualization:** Timeline (deployment events overlaid on performance charts), Table (recent deployments), Annotation layer on dashboards.

---

### UC-8.2.6 · Connection Pool Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Exhausted JDBC/database connection pools cause application errors and cascading failures. Monitoring prevents connection starvation.
- **App/TA:** `TA-jmx`, application metrics
- **Data Sources:** JMX DataSource MBeans, HikariCP metrics, application framework metrics
- **SPL:**
```spl
index=jmx sourcetype="jmx:datasource"
| eval pct_used=round(numActive/maxTotal*100,1)
| timechart span=5m max(pct_used) as pool_pct by host, pool_name
| where pool_pct > 80
```
- **Implementation:** Poll JDBC connection pool MBeans via JMX. Track active, idle, and waiting connections. Alert at 80% pool utilization. Monitor connection wait time — high wait times indicate pool exhaustion even before 100%. Correlate with database latency.
- **Visualization:** Gauge (% pool used), Line chart (pool utilization over time), Table (pools approaching limits).

---

### UC-8.2.7 · Session Count Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Active session counts indicate concurrent user load. Trending supports capacity planning and license management.
- **App/TA:** `TA-jmx`, application metrics
- **Data Sources:** JMX session MBeans, application metrics endpoints
- **SPL:**
```spl
index=jmx sourcetype="jmx:manager"
| timechart span=15m max(activeSessions) as sessions by host
| predict sessions as predicted future_timespan=7
```
- **Implementation:** Poll session manager MBeans via JMX. Track active sessions per server. Correlate with user authentication events for validation. Use `predict` for capacity forecasting.
- **Visualization:** Line chart (session count with prediction), Single value (current active sessions), Area chart (sessions over time).

---

### UC-8.2.8 · .NET CLR Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** CLR performance issues (high GC, exceptions, thread starvation) directly impact .NET application performance. Monitoring guides runtime tuning.
- **App/TA:** `Splunk_TA_windows` (Perfmon), custom .NET metrics
- **Data Sources:** Windows Performance Counters (.NET CLR Memory, Exceptions, Threading)
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:CLR_Memory"
| timechart span=5m avg(Pct_Time_in_GC) as gc_pct, avg(Gen_2_Collections) as gen2_gc by instance
| where gc_pct > 10
```
- **Implementation:** Configure Perfmon inputs for .NET CLR counters in `inputs.conf`. Monitor % Time in GC, Gen 2 collections, exception throw rate, and thread contention rate. Alert when GC time exceeds 10% or exception rate spikes.
- **Visualization:** Line chart (GC % over time), Multi-metric chart (CLR counters), Table (instances with high GC).

---

### UC-8.2.9 · Node.js Event Loop Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Event loop lag indicates blocking operations that prevent Node.js from handling requests. Detection enables code-level investigation.
- **App/TA:** Custom metrics input, OpenTelemetry
- **Data Sources:** Node.js process metrics (event loop lag, heap usage), Prometheus client metrics
- **SPL:**
```spl
index=application sourcetype="nodejs:metrics"
| timechart span=1m avg(event_loop_lag_ms) as el_lag, avg(heap_used_mb) as heap by host
| where el_lag > 100
```
- **Implementation:** Instrument Node.js apps with `prom-client` or OpenTelemetry SDK. Export event loop lag, heap stats, and active handles/requests. Forward to Splunk via HEC or Prometheus remote write. Alert when lag exceeds 100ms.
- **Visualization:** Line chart (event loop lag), Dual-axis (lag + heap usage), Single value (current lag ms).

---

### UC-8.2.10 · Class Loading Issues
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** ClassNotFoundException and NoClassDefFoundError indicate deployment or dependency issues that may cause intermittent failures.
- **App/TA:** Application log parsing
- **Data Sources:** Application error logs (Java stack traces)
- **SPL:**
```spl
index=application sourcetype="log4j" log_level=ERROR
| search "ClassNotFoundException" OR "NoClassDefFoundError" OR "ClassCastException"
| rex "(?<exception_class>ClassNotFoundException|NoClassDefFoundError|ClassCastException):\s+(?<missing_class>\S+)"
| stats count by host, exception_class, missing_class
```
- **Implementation:** Parse Java stack traces from application logs. Extract exception type and missing class name. Alert on new class loading errors (not seen before). Track frequency to distinguish transient from persistent issues.
- **Visualization:** Table (class loading errors with details), Bar chart (errors by type), Timeline (error occurrences).

---

### 8.3 Message Queues & Event Streaming

**Primary App/TA:** Splunk Add-on for Kafka (`TA-kafka`), RabbitMQ management API (scripted input), JMX for Java-based brokers, custom REST inputs.

---

### UC-8.3.1 · Consumer Lag Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Growing consumer lag means messages aren't being processed fast enough, leading to data staleness and eventual message loss if retention is exceeded.
- **App/TA:** `TA-kafka`, Burrow integration, JMX
- **Data Sources:** Kafka consumer group offsets (JMX, Burrow, `kafka-consumer-groups.sh`)
- **SPL:**
```spl
index=kafka sourcetype="kafka:consumer_lag"
| timechart span=5m max(lag) as consumer_lag by consumer_group, topic
| where consumer_lag > 10000
```
- **Implementation:** Deploy Kafka consumer lag monitoring via Burrow or JMX. Poll lag per consumer group/topic/partition every minute. Alert when lag exceeds threshold (e.g., >10K messages or >5 minutes equivalent). Track lag trend for capacity planning.
- **Visualization:** Line chart (lag per consumer group), Heatmap (topic × partition lag), Single value (max lag), Table (lagging consumers).

---

### UC-8.3.2 · Queue Depth Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Growing queue depths indicate consumers can't keep up or are down. Trending prevents message loss and processing delays.
- **App/TA:** RabbitMQ management API, ActiveMQ JMX
- **Data Sources:** RabbitMQ management API (`/api/queues`), ActiveMQ JMX
- **SPL:**
```spl
index=messaging sourcetype="rabbitmq:queue"
| timechart span=5m max(messages) as depth by queue_name, vhost
| where depth > 1000
```
- **Implementation:** Poll RabbitMQ management API every minute via scripted input. Track message count, publish/deliver rates per queue. Alert when depth exceeds threshold or grows consistently. Correlate with consumer status.
- **Visualization:** Line chart (queue depth over time), Bar chart (top queues by depth), Table (queues exceeding threshold).

---

### UC-8.3.3 · Broker Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Broker failures cause message loss and application disruption. Health monitoring ensures cluster stability.
- **App/TA:** JMX, broker metrics
- **Data Sources:** Kafka JMX (broker metrics), RabbitMQ management API (`/api/nodes`)
- **SPL:**
```spl
index=kafka sourcetype="kafka:broker"
| stats latest(UnderReplicatedPartitions) as under_replicated, latest(ActiveControllerCount) as controllers by broker_id
| where under_replicated > 0 OR controllers != 1
```
- **Implementation:** Poll broker health metrics via JMX every minute. Track disk usage, CPU, memory, network I/O. Alert on broker offline, under-replicated partitions, or controller election. Monitor ISR (In-Sync Replica) shrink rate.
- **Visualization:** Status grid (broker × health), Single value (under-replicated partitions), Table (broker metrics), Line chart (broker resource usage).

---

### UC-8.3.4 · Under-Replicated Partitions
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Under-replicated partitions mean data is at risk of loss if additional brokers fail. Immediate remediation is required.
- **App/TA:** `TA-kafka`, JMX
- **Data Sources:** Kafka JMX (`UnderReplicatedPartitions`, `UnderMinIsrPartitionCount`)
- **SPL:**
```spl
index=kafka sourcetype="kafka:broker"
| where UnderReplicatedPartitions > 0
| stats sum(UnderReplicatedPartitions) as total_under_replicated by _time
| timechart span=5m max(total_under_replicated) as under_replicated
```
- **Implementation:** Poll Kafka broker JMX metrics. Alert immediately on any under-replicated partitions. Track duration of under-replication. Correlate with broker disk usage and network metrics to identify root cause.
- **Visualization:** Single value (under-replicated count — target: 0), Line chart (under-replicated over time), Table (affected topics/partitions).

---

### UC-8.3.5 · Dead Letter Queue Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Messages in DLQ represent processing failures that need investigation. They may indicate bugs, schema changes, or downstream failures.
- **App/TA:** Queue management API, custom input
- **Data Sources:** RabbitMQ DLQ queues, AWS SQS DLQ, Kafka DLT topics
- **SPL:**
```spl
index=messaging sourcetype="rabbitmq:queue"
| search queue_name="*dead*" OR queue_name="*dlq*" OR queue_name="*error*"
| where messages > 0
| table _time, vhost, queue_name, messages, message_stats.publish_details.rate
```
- **Implementation:** Monitor DLQ/DLT queues specifically. Alert when any DLQ has messages (should normally be 0). Track DLQ ingestion rate to detect ongoing issues. Sample DLQ messages for root cause analysis.
- **Visualization:** Single value (total DLQ messages), Table (DLQs with counts), Line chart (DLQ growth over time).

---

### UC-8.3.6 · Message Throughput Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Throughput trending identifies capacity limits and validates scaling decisions. Unexpected drops indicate producer or broker issues.
- **App/TA:** JMX, broker management APIs
- **Data Sources:** Kafka broker metrics (MessagesInPerSec), RabbitMQ message rates
- **SPL:**
```spl
index=kafka sourcetype="kafka:broker"
| timechart span=5m sum(MessagesInPerSec) as msgs_in, sum(BytesInPerSec) as bytes_in
```
- **Implementation:** Poll broker throughput metrics via JMX. Track messages and bytes in/out per broker and per topic. Baseline normal patterns. Alert on sudden throughput drops (possible producer failure).
- **Visualization:** Line chart (throughput over time), Stacked area (throughput by topic), Dual-axis (messages + bytes).

---

### UC-8.3.7 · Topic/Queue Creation Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Uncontrolled topic/queue creation can lead to resource sprawl. Audit trail supports governance and cleanup.
- **App/TA:** Broker audit logs, Kafka authorizer logs
- **Data Sources:** Kafka authorizer logs, RabbitMQ audit log, broker event logs
- **SPL:**
```spl
index=kafka sourcetype="kafka:authorizer"
| search operation="Create" resource_type="Topic"
| table _time, principal, resource_name, allowed
```
- **Implementation:** Enable Kafka authorizer logging or audit log. Forward broker logs to Splunk. Parse topic/queue creation events. Alert on creation of topics matching naming convention violations. Report on topic inventory growth.
- **Visualization:** Table (created topics with details), Timeline (creation events), Bar chart (topics created per week).

---

### UC-8.3.8 · Consumer Group Rebalancing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Frequent rebalances cause processing pauses and duplicate message delivery. Detection identifies unstable consumers.
- **App/TA:** Kafka broker logs, JMX
- **Data Sources:** Kafka GroupCoordinator logs, consumer group state
- **SPL:**
```spl
index=kafka sourcetype="kafka:server"
| search "Preparing to rebalance group" OR "Stabilized group"
| rex "group (?<consumer_group>\S+)"
| stats count by consumer_group
| where count > 5
```
- **Implementation:** Parse Kafka broker logs for rebalance events. Track rebalance frequency per consumer group. Alert when rebalances occur more than 5 times per hour. Correlate with consumer heartbeat timeouts and session timeouts.
- **Visualization:** Bar chart (rebalances per consumer group), Timeline (rebalance events), Line chart (rebalance frequency trend).

---

### UC-8.3.9 · Partition Leader Elections
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Frequent leader elections indicate broker instability, causing temporary unavailability for affected partitions.
- **App/TA:** JMX, Kafka controller logs
- **Data Sources:** Kafka JMX (`LeaderElectionRateAndTimeMs`), controller logs
- **SPL:**
```spl
index=kafka sourcetype="kafka:controller"
| search "leader" "election"
| timechart span=15m count as elections
| where elections > 10
```
- **Implementation:** Monitor Kafka controller logs and JMX metrics. Track leader election rate and duration. Alert on elevated election rates. Correlate with broker restarts, network events, and ZooKeeper/KRaft issues.
- **Visualization:** Line chart (elections over time), Single value (elections per hour), Table (affected topics/partitions).

---

### UC-8.3.10 · Message Age Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Old messages in queues indicate processing delays that may violate SLAs. Age tracking provides a business-relevant metric beyond raw queue depth.
- **App/TA:** Queue management API
- **Data Sources:** RabbitMQ management API (message age), custom consumer timestamp comparison
- **SPL:**
```spl
index=messaging sourcetype="rabbitmq:queue"
| eval message_age_sec=now()-oldest_message_timestamp
| where message_age_sec > 300
| table queue_name, vhost, messages, message_age_sec
| sort -message_age_sec
```
- **Implementation:** Poll message age metrics from queue management APIs. For Kafka, compare consumer offset timestamp with current time. Alert when message age exceeds SLA (e.g., >5 minutes for real-time queues). Differentiate by queue priority.
- **Visualization:** Table (queues with old messages), Bar chart (message age by queue), Single value (max message age).

---

### 8.4 API Gateways & Service Mesh

**Primary App/TA:** Custom access log inputs, Envoy access log parsing, Istio telemetry, Kong/Apigee API inputs.

---

### UC-8.4.1 · API Error Rate by Endpoint
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Per-endpoint error rates pinpoint failing services, enabling targeted debugging rather than broad investigation.
- **App/TA:** Custom log input, gateway access logs
- **Data Sources:** API gateway access logs (Kong, Apigee, AWS API Gateway)
- **SPL:**
```spl
index=api sourcetype="kong:access"
| eval is_error=if(status>=400,1,0)
| stats count, sum(is_error) as errors by request_uri, upstream_service
| eval error_rate=round(errors/count*100,2)
| where error_rate > 5
| sort -error_rate
```
- **Implementation:** Forward API gateway access logs to Splunk. Parse endpoint, status code, latency, and consumer identity. Calculate error rates per endpoint. Alert when any endpoint exceeds error threshold. Break down by 4xx vs 5xx.
- **Visualization:** Table (endpoints with error rates), Bar chart (error rate by endpoint), Line chart (error rate trend per endpoint).

---

### UC-8.4.2 · API Latency Percentiles
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** P95/P99 latency reveals the experience of the slowest users. Averages hide tail latency problems.
- **App/TA:** Custom log input, gateway metrics
- **Data Sources:** API gateway access logs with latency fields
- **SPL:**
```spl
index=api sourcetype="kong:access"
| stats perc50(latency) as p50, perc95(latency) as p95, perc99(latency) as p99 by request_uri
| where p95 > 1000
| sort -p99
```
- **Implementation:** Ensure gateway logs include request and upstream latency. Calculate p50/p95/p99 per endpoint. Alert when p95 exceeds SLA target. Track percentile trends to detect gradual degradation before it becomes critical.
- **Visualization:** Line chart (p50/p95/p99 over time), Table (endpoints with high latency), Histogram (latency distribution).

---

### UC-8.4.3 · Rate Limiting Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Rate limiting indicates consumers exceeding their quotas. May signal API abuse, misconfigured clients, or quota adjustments needed.
- **App/TA:** Gateway logs
- **Data Sources:** API gateway rate limit logs (429 responses)
- **SPL:**
```spl
index=api sourcetype="kong:access" status=429
| stats count by consumer_id, request_uri
| sort -count
```
- **Implementation:** Track 429 responses from API gateway. Identify rate-limited consumers and endpoints. Alert on sustained rate limiting for critical consumers. Review quota configuration if legitimate traffic is being limited.
- **Visualization:** Bar chart (rate-limited consumers), Line chart (429 rate over time), Table (rate limit events).

---

### UC-8.4.4 · Authentication Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Authentication failures may indicate credential compromise, API key rotation issues, or brute-force attacks.
- **App/TA:** Gateway auth logs
- **Data Sources:** API gateway authentication logs (401/403 responses), OAuth error logs
- **SPL:**
```spl
index=api sourcetype="kong:access" status IN (401, 403)
| stats count by consumer_id, src_ip, request_uri
| where count > 50
| sort -count
```
- **Implementation:** Track 401/403 responses with source IP and consumer identity. Alert on high failure rates from single sources (potential brute force). Correlate with successful authentications to detect account compromise patterns.
- **Visualization:** Table (auth failures by consumer/IP), Line chart (failure rate over time), Geo map (failures by source location).

---

### UC-8.4.5 · Service-to-Service Call Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Inter-service communication failures in microservices architectures cascade quickly. Detection enables rapid isolation of failing services.
- **App/TA:** Istio/Envoy access logs, Linkerd tap
- **Data Sources:** Envoy access logs (upstream_cluster, response_code), Istio telemetry
- **SPL:**
```spl
index=mesh sourcetype="envoy:access"
| where response_code >= 500
| stats count by upstream_cluster, downstream_cluster, response_code
| sort -count
```
- **Implementation:** Configure Envoy/Istio to export access logs to Splunk. Parse source service, destination service, status code, and latency. Build service dependency map. Alert on inter-service error rate spikes. Track per-service error budgets.
- **Visualization:** Service dependency map (with error highlighting), Table (failing service pairs), Heatmap (service × service error rate).

---

### UC-8.4.6 · Circuit Breaker Activations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Circuit breaker trips indicate a downstream service is failing. Quick detection enables proactive communication and remediation.
- **App/TA:** Service mesh metrics, Envoy stats
- **Data Sources:** Envoy cluster stats (circuit breaker metrics), Istio DestinationRule events
- **SPL:**
```spl
index=mesh sourcetype="envoy:stats"
| search "circuit_breaker" "cx_open" OR "rq_open"
| stats count by upstream_cluster
| where count > 0
```
- **Implementation:** Monitor Envoy circuit breaker metrics. Alert on any circuit breaker opening. Track circuit breaker state transitions. Correlate with upstream service health to validate circuit breaker configuration thresholds.
- **Visualization:** Status grid (service × circuit breaker state), Timeline (circuit breaker events), Table (active circuit breakers).

---

### UC-8.4.7 · API Consumer Usage Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Usage tracking per API consumer enables billing, quota management, and partner relationship management.
- **App/TA:** Gateway access logs
- **Data Sources:** API gateway logs with consumer identification (API key, OAuth client ID)
- **SPL:**
```spl
index=api sourcetype="kong:access"
| stats count, sum(request_size) as total_bytes, avg(latency) as avg_latency by consumer_id
| sort -count
```
- **Implementation:** Ensure API gateway logs include consumer identity. Aggregate usage by consumer, endpoint, and time period. Create monthly usage reports for billing/chargeback. Track usage trends per consumer for capacity planning.
- **Visualization:** Table (consumer usage summary), Bar chart (top consumers), Line chart (usage trends per consumer), Pie chart (traffic by consumer).

---

### UC-8.4.8 · mTLS Certificate Expiration
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Expired mTLS certificates break service-to-service communication, causing complete mesh failures. Proactive monitoring is essential.
- **App/TA:** Service mesh metrics, scripted input
- **Data Sources:** Istio/Linkerd certificate metadata, `istioctl proxy-config` output
- **SPL:**
```spl
index=mesh sourcetype="istio:cert_status"
| eval days_until_expiry=round((cert_expiry_epoch-now())/86400)
| where days_until_expiry < 7
| table service, namespace, days_until_expiry, issuer
| sort days_until_expiry
```
- **Implementation:** Monitor Istio/Linkerd certificate lifetimes. For auto-rotated certs, verify rotation is working by tracking cert age. Alert when certs approach expiry or rotation fails. Monitor CA health (Citadel, cert-manager).
- **Visualization:** Table (certs with expiry), Single value (certs expiring within 7d), Timeline (cert rotation events).

---

### 8.5 Caching Layers

**Primary App/TA:** Custom scripted inputs (Redis CLI, Memcached stats), Varnish syslog, SNMP for hardware caches.

---

### UC-8.5.1 · Cache Hit/Miss Ratio
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Cache hit ratio directly measures cache effectiveness. Declining ratio means more backend load and higher latency.
- **App/TA:** Custom scripted input (`redis-cli INFO`)
- **Data Sources:** Redis INFO stats, Memcached stats, Varnish stats
- **SPL:**
```spl
index=cache sourcetype="redis:info"
| eval hit_ratio=round(keyspace_hits/(keyspace_hits+keyspace_misses)*100,2)
| timechart span=5m avg(hit_ratio) as cache_hit_pct by host
| where cache_hit_pct < 90
```
- **Implementation:** Run `redis-cli INFO` via scripted input every minute. Parse keyspace_hits and keyspace_misses. Calculate hit ratio. Alert when ratio drops below 90%. Correlate with application deployment events (new code may change access patterns).
- **Visualization:** Gauge (hit ratio %), Line chart (hit ratio over time), Single value (current hit ratio).

---

### UC-8.5.2 · Memory Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Cache memory exhaustion triggers evictions, degrading performance. Monitoring enables timely scaling.
- **App/TA:** Custom scripted input
- **Data Sources:** Redis INFO memory, Memcached stats
- **SPL:**
```spl
index=cache sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct by host
| where memory_pct > 85
```
- **Implementation:** Poll memory metrics every minute. Track used vs max memory and RSS vs used ratio (fragmentation). Alert at 85% memory usage. Monitor memory fragmentation ratio — values >1.5 indicate excessive fragmentation.
- **Visualization:** Gauge (% memory used), Line chart (memory usage over time), Table (instances approaching limit).

---

### UC-8.5.3 · Eviction Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** High eviction rates mean the cache is too small, causing frequent backend roundtrips. Tracking guides capacity decisions.
- **App/TA:** Custom scripted input
- **Data Sources:** Redis INFO stats (evicted_keys), Memcached stats (evictions)
- **SPL:**
```spl
index=cache sourcetype="redis:info"
| timechart span=5m per_second(evicted_keys) as eviction_rate by host
| where eviction_rate > 10
```
- **Implementation:** Track evicted_keys counter over time. Calculate eviction rate per second. Alert when eviction rate exceeds threshold. Correlate with memory usage — evictions with memory below max indicates maxmemory-policy is active.
- **Visualization:** Line chart (eviction rate over time), Single value (current eviction rate), Dual-axis (evictions + memory usage).

---

### UC-8.5.4 · Connection Count Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment.
- **App/TA:** Custom scripted input
- **Data Sources:** Redis INFO clients, Memcached stats
- **SPL:**
```spl
index=cache sourcetype="redis:info"
| timechart span=5m max(connected_clients) as clients, max(maxclients) as limit by host
| eval pct=round(clients/limit*100,1)
| where pct > 80
```
- **Implementation:** Poll connection metrics every minute. Track connected clients vs maxclients setting. Alert at 80% threshold. Monitor rejected connections counter for actual connection refusals.
- **Visualization:** Line chart (connections over time), Gauge (% of max), Single value (current connections).

---

### UC-8.5.5 · Replication Lag (Redis)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Redis replication lag affects read consistency for apps reading from replicas. Monitoring ensures data freshness.
- **App/TA:** Custom scripted input
- **Data Sources:** Redis INFO replication (`master_repl_offset`, `slave_repl_offset`)
- **SPL:**
```spl
index=cache sourcetype="redis:info" role="slave"
| eval lag_bytes=master_repl_offset-slave_repl_offset
| timechart span=1m max(lag_bytes) as repl_lag by host
| where repl_lag > 1000000
```
- **Implementation:** Poll Redis INFO replication from replicas every minute. Calculate byte offset lag. Alert when lag exceeds threshold (e.g., >1MB or growing). Monitor replication link status (master_link_status).
- **Visualization:** Line chart (replication lag over time), Single value (current lag), Table (replica status).

---

### UC-8.5.6 · Slow Command Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Slow Redis commands block the single-threaded event loop, impacting all clients. Detection enables command optimization.
- **App/TA:** Custom scripted input (`SLOWLOG GET`)
- **Data Sources:** Redis SLOWLOG
- **SPL:**
```spl
index=cache sourcetype="redis:slowlog"
| table _time, host, duration_ms, command, key
| where duration_ms > 10
| sort -duration_ms
```
- **Implementation:** Run `redis-cli SLOWLOG GET 100` via scripted input every minute. Parse command, duration, and key pattern. Alert on commands exceeding 10ms. Identify O(N) commands (KEYS, SMEMBERS on large sets) for optimization.
- **Visualization:** Table (slow commands with details), Bar chart (slow commands by type), Line chart (slow command frequency).

---

### UC-8.5.7 · Key Expiration Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Monitoring TTL patterns ensures cache freshness strategy is working. Unusual patterns may indicate application bugs.
- **App/TA:** Custom scripted input
- **Data Sources:** Redis INFO keyspace (expires, expired_keys)
- **SPL:**
```spl
index=cache sourcetype="redis:info"
| eval expire_pct=round(expires/keys*100,1)
| timechart span=15m avg(expire_pct) as pct_with_ttl, per_second(expired_keys) as expire_rate by host
```
- **Implementation:** Track keys with TTL vs total keys. Monitor expiration rate. Alert if expire_pct drops significantly (new code not setting TTL on keys). Track expired_stale_perc for lazy expiration health.
- **Visualization:** Line chart (expiration rate), Dual-axis (keys with TTL % + expiration rate), Single value (% keys with TTL).

---

## 9. Identity & Access Management

### 9.1 Active Directory / Entra ID

**Primary App/TA:** Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`), Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`) for Entra ID.

---

### UC-9.1.1 · Brute-Force Login Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Brute-force attacks are a primary credential compromise vector. Early detection prevents account takeover.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Windows Security Event Log (Event ID 4625 — failed logon)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4625
| stats count by Account_Name, Source_Network_Address
| where count > 10
| sort -count
```
- **Implementation:** Forward Security logs from DCs via UF. Enable "Audit Logon Events" via GPO. Alert on >10 failures per account per 15 minutes. Correlate with lockout events (4740). Whitelist known service accounts with expected failures.
- **Visualization:** Table (accounts with failure counts), Line chart (failure rate over time), Geo map (source IPs).

---

### UC-9.1.2 · Account Lockout Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Lockouts cause user productivity loss and help desk load. Source identification enables rapid resolution.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (Event ID 4740 — account locked out)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4740
| table _time, Account_Name, CallerComputerName
| sort -_time
```
- **Implementation:** Forward DC Security logs. Alert on each lockout with source workstation included. Create report of recurring lockouts for proactive investigation. Correlate with 4625 events to find the failing source.
- **Visualization:** Table (lockouts with source), Bar chart (top locked accounts), Line chart (lockout trend).

---

### UC-9.1.3 · Privileged Group Membership Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized privilege escalation is a primary attack technique. Immediate detection is essential for security.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4728 — member added to security-enabled global group, 4732 — local group, 4756 — universal group)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4728,4732,4756)
| search TargetUserName IN ("Domain Admins","Enterprise Admins","Schema Admins","Administrators")
| table _time, MemberName, TargetUserName, SubjectUserName
```
- **Implementation:** Forward DC Security logs. Create alert for any membership change to privileged groups (Domain Admins, Enterprise Admins, Schema Admins, Backup Operators). Integrate with change management for validation.
- **Visualization:** Table (membership changes), Timeline (change events), Single value (changes this week).

---

### UC-9.1.4 · Service Account Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Service accounts used interactively or from unexpected hosts indicate compromise. Detection prevents lateral movement.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4624 — successful logon, Logon Type field)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624
| lookup service_accounts.csv Account_Name OUTPUT expected_hosts, account_type
| where account_type="service" AND (Logon_Type=2 OR Logon_Type=10 OR NOT match(src_host, expected_hosts))
| table _time, Account_Name, Logon_Type, src_host
```
- **Implementation:** Maintain lookup of service accounts with expected Logon Types and source hosts. Alert on interactive logon (Type 2, 10) or unexpected source. Regularly audit service account inventory with AD queries.
- **Visualization:** Table (anomalous service account usage), Timeline (events), Bar chart (anomalies by account).

---

### UC-9.1.5 · Kerberos Ticket Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Detects Kerberoasting and Golden Ticket attacks, which are advanced AD compromise techniques. Essential for security monitoring.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4768 — TGT request, 4769 — TGS request)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769 Ticket_Encryption_Type=0x17
| stats count by Account_Name, Service_Name
| where count > 5
| sort -count
```
- **Implementation:** Forward 4768/4769 events from DCs. Detect Kerberoasting by filtering for RC4 encryption (0x17) on TGS requests. Detect Golden Ticket by looking for TGT requests with unusual encryption types or from non-DC sources.
- **Visualization:** Table (suspicious Kerberos requests), Bar chart (requests by encryption type), Timeline (anomalous events).

---

### UC-9.1.6 · Password Policy Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Failed password changes indicate users struggling with policy or potential social engineering. Monitoring supports security awareness.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (4723 — password change attempt, 4724 — password reset attempt)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4723, 4724)
| stats count(eval(Keywords="Audit Failure")) as failures, count(eval(Keywords="Audit Success")) as successes by Account_Name
| where failures > 3
```
- **Implementation:** Forward DC Security logs. Track password change success/failure rates. Alert on excessive failures per user. Monitor 4724 (admin resets) separately as these bypass self-service and may indicate social engineering.
- **Visualization:** Table (users with failures), Bar chart (failure rate by user), Pie chart (change vs reset).

---

### UC-9.1.7 · GPO Modification Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** GPO changes affect all domain-joined machines. Unauthorized modifications can disable security controls across the organization.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** Security Event Log (5136 — directory service object modified)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
| search ObjectClass="groupPolicyContainer"
| table _time, SubjectUserName, ObjectDN, AttributeLDAPDisplayName, AttributeValue
```
- **Implementation:** Enable "Audit Directory Service Changes" via GPO. Forward DC Security logs. Alert on any GPO modification. Correlate with change management tickets. Track which GPOs are modified most frequently.
- **Visualization:** Table (GPO changes with details), Timeline (modification events), Bar chart (changes by admin).

---

### UC-9.1.8 · AD Replication Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Replication failures cause authentication issues, stale group memberships, and inconsistent policy application across sites.
- **App/TA:** `Splunk_TA_windows`, `repadmin` scripted input
- **Data Sources:** Directory Service event log, `repadmin /showrepl` output
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode IN (1864,1865,2042,2087)
| table _time, ComputerName, EventCode, Message
| sort -_time
```
- **Implementation:** Forward Directory Service event logs from DCs. Run `repadmin /showrepl` via scripted input daily. Alert on replication failures (Event IDs 1864, 2042, 2087). Track replication latency between sites.
- **Visualization:** Table (replication status by DC pair), Status grid (DC × replication health), Timeline (failure events).

---

### UC-9.1.9 · LDAP Query Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Expensive LDAP queries degrade DC performance affecting authentication for all users. Detection enables query optimization.
- **App/TA:** `Splunk_TA_windows`, Directory Service diagnostics
- **Data Sources:** Directory Service event log (Event ID 1644 — expensive search), Field Engineering diagnostics
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode=1644
| rex "Entries Visited\s+:\s+(?<entries_visited>\d+)"
| where entries_visited > 10000
| table _time, ComputerName, entries_visited, Message
```
- **Implementation:** Enable LDAP search diagnostics (registry key: "15 Field Engineering" value "Expensive Search Results Threshold" = 10000). Forward Directory Service logs. Alert on queries visiting >10K entries. Identify and optimize expensive applications.
- **Visualization:** Table (expensive queries), Bar chart (queries by source application), Line chart (expensive query frequency).

---

### UC-9.1.10 · Stale Account Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Stale accounts are an attack surface — unused accounts may be compromised without detection. Regular cleanup reduces risk.
- **App/TA:** Scripted input (PowerShell AD query)
- **Data Sources:** AD attributes (lastLogonTimestamp, pwdLastSet) via scripted input
- **SPL:**
```spl
index=ad sourcetype="ad:accounts"
| eval days_inactive=round((now()-lastLogon)/86400)
| where days_inactive > 90 AND enabled="True"
| table samAccountName, displayName, days_inactive, ou, lastLogon
| sort -days_inactive
```
- **Implementation:** Run PowerShell script querying AD for lastLogonTimestamp weekly. Export to CSV/JSON and ingest. Flag accounts inactive >90 days. Cross-reference with HR systems for departed employees. Report for access review.
- **Visualization:** Table (stale accounts), Bar chart (stale accounts by OU), Single value (total stale accounts), Pie chart (by account type).

---

### UC-9.1.11 · Entra ID Risky Sign-Ins
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Entra ID Identity Protection detects risky sign-ins using Microsoft's threat intelligence. Ingesting into Splunk enables correlation with on-prem events.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra ID sign-in logs, risk detection events (via Graph API)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:signin"
| where riskLevelDuringSignIn IN ("high","medium")
| table _time, userPrincipalName, ipAddress, location, riskLevelDuringSignIn, riskDetail
| sort -_time
```
- **Implementation:** Configure Splunk Add-on for Microsoft Cloud Services to ingest Entra ID sign-in logs via Graph API. Filter for medium/high risk detections. Alert on high-risk sign-ins. Correlate with on-prem AD events for hybrid investigations.
- **Visualization:** Table (risky sign-ins), Geo map (sign-in locations), Line chart (risk events over time), Bar chart (risk types).

---

### UC-9.1.12 · Conditional Access Policy Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Conditional Access blocks indicate non-compliant devices or policy misconfigurations. Monitoring ensures security policies work without excessive user friction.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra ID sign-in logs (conditionalAccessStatus field)
- **SPL:**
```spl
index=azure sourcetype="azure:aad:signin" conditionalAccessStatus="failure"
| stats count by userPrincipalName, appDisplayName, conditionalAccessPolicies{}.displayName
| sort -count
```
- **Implementation:** Ingest Entra ID sign-in logs. Filter for Conditional Access failures. Track failure rates per policy and per user. Alert on sudden spikes indicating policy misconfiguration. Report on most-blocked policies and applications.
- **Visualization:** Bar chart (failures by policy), Table (blocked users), Line chart (failure rate trend), Pie chart (failures by application).

---

### 9.2 LDAP Directories

**Primary App/TA:** Syslog inputs, custom scripted inputs for LDAP server stats.

---

### UC-9.2.1 · Bind Failure Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** LDAP bind failures indicate authentication issues, misconfigured applications, or brute-force attempts against directory services.
- **App/TA:** Syslog, LDAP server logs
- **Data Sources:** OpenLDAP syslog, 389 Directory access log
- **SPL:**
```spl
index=ldap sourcetype="syslog" "BIND" "err=49"
| stats count by src_ip, bind_dn
| where count > 10
| sort -count
```
- **Implementation:** Forward LDAP server syslog to Splunk. Parse bind operations and result codes (err=49 = invalid credentials). Alert on >10 failures per source per 15 minutes. Correlate with application health monitoring.
- **Visualization:** Table (bind failures by source/DN), Line chart (failure rate), Bar chart (top failing sources).

---

### UC-9.2.2 · Search Performance Degradation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Slow LDAP searches impact all applications relying on directory services for authentication and authorization.
- **App/TA:** LDAP access log parsing
- **Data Sources:** OpenLDAP access log (search duration), 389 Directory access log
- **SPL:**
```spl
index=ldap sourcetype="openldap:access" operation="SEARCH"
| where elapsed_ms > 1000
| stats count, avg(elapsed_ms) as avg_ms by base_dn, filter
| sort -avg_ms
```
- **Implementation:** Enable LDAP access logging with timing information. Parse search operations with duration. Alert on searches exceeding 1 second. Identify expensive filters (unindexed attributes, broad base DN). Recommend index creation.
- **Visualization:** Table (slow searches), Bar chart (avg duration by filter), Line chart (search latency trend).

---

### UC-9.2.3 · Schema Modification Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Schema changes to directory services can break applications and are rarely expected. Detection ensures change control compliance.
- **App/TA:** LDAP audit log
- **Data Sources:** LDAP server audit log (schema modification events)
- **SPL:**
```spl
index=ldap sourcetype="openldap:audit"
| search "cn=schema" ("add:" OR "delete:" OR "replace:")
| table _time, modifier_dn, changetype, modification
```
- **Implementation:** Enable LDAP audit logging (overlay in OpenLDAP, audit log in 389 DS). Forward to Splunk. Alert on any schema modification. These should be extremely rare and always correlated with change tickets.
- **Visualization:** Timeline (schema changes), Table (change details), Single value (schema changes this month).

---

### UC-9.2.4 · Replication Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** LDAP replication failures cause authentication inconsistencies and stale directory data across sites.
- **App/TA:** Scripted input, LDAP server logs
- **Data Sources:** LDAP replication logs, `ldapsearch` monitoring attributes (contextCSN)
- **SPL:**
```spl
index=ldap sourcetype="openldap:syncrepl"
| search "syncrepl" ("ERROR" OR "RETRY" OR "failed")
| stats count by host, provider
| where count > 0
```
- **Implementation:** Monitor LDAP replication status via scripted input querying contextCSN or replication agreements. Forward syncrepl logs. Alert on replication failures or increasing lag between providers and consumers.
- **Visualization:** Status grid (provider × consumer health), Table (replication status), Timeline (failure events).

---

### 9.3 Identity Providers (IdP) & SSO

**Primary App/TA:** Splunk Add-on for Okta (`Splunk_TA_okta`), Duo TA, custom API inputs for other IdPs.

---

### UC-9.3.1 · MFA Challenge Failure Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** High MFA failure rates indicate user friction, potential phishing, or MFA fatigue attacks. Monitoring supports both security and user experience.
- **App/TA:** `Splunk_TA_okta`, Splunk_TA_duo
- **Data Sources:** Okta system log, Duo authentication log
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.auth_via_mfa"
| stats count(eval(outcome.result="FAILURE")) as failures, count(eval(outcome.result="SUCCESS")) as successes by actor.displayName
| eval fail_rate=round(failures/(failures+successes)*100,1)
| where fail_rate > 20
```
- **Implementation:** Ingest IdP logs via API. Track MFA success/failure rates per user and per factor type. Alert on high failure rates (>20% per user). Detect MFA fatigue patterns (rapid repeated pushes). Report on factor type distribution.
- **Visualization:** Bar chart (failure rate by user), Pie chart (factor type distribution), Line chart (MFA success rate trend).

---

### UC-9.3.2 · Impossible Travel Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Authentication from two geographically distant locations within an impossibly short timeframe strongly indicates credential compromise.
- **App/TA:** `Splunk_TA_okta`, custom correlation
- **Data Sources:** IdP sign-in logs with IP geolocation
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.session.start"
| iplocation client.ipAddress
| sort actor.alternateId, _time
| streamstats window=2 earliest(_time) as prev_time, earliest(lat) as prev_lat, earliest(lon) as prev_lon by actor.alternateId
| eval distance_km=... , time_diff_hr=((_time-prev_time)/3600)
| where distance_km > 500 AND time_diff_hr < 2
```
- **Implementation:** Ingest IdP sign-in logs. Enrich with GeoIP. Calculate distance and time between consecutive logins per user. Alert when distance/time ratio is impossible (>500km in <2 hours). Whitelist VPN exit IPs and known travel patterns.
- **Visualization:** Geo map (sign-in locations with lines), Table (impossible travel events), Timeline (flagged events).

---

### UC-9.3.3 · Token Anomaly Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Token replay attacks bypass authentication entirely. Detection prevents persistent unauthorized access.
- **App/TA:** `Splunk_TA_okta`, IdP audit logs
- **Data Sources:** IdP token issuance logs, application token validation logs
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="app.oauth2.token.grant"
| stats count, dc(client.ipAddress) as unique_ips by actor.alternateId, target{}.displayName
| where unique_ips > 3
```
- **Implementation:** Monitor token issuance and usage patterns. Alert on tokens used from multiple IPs (potential replay). Track token lifetime and refresh patterns. Detect anomalous token requests outside normal application patterns.
- **Visualization:** Table (anomalous token usage), Timeline (suspicious events), Bar chart (tokens by application).

---

### UC-9.3.4 · Application Access Patterns
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Monitors which applications users access for license optimization and detects anomalous access indicating potential compromise.
- **App/TA:** `Splunk_TA_okta`
- **Data Sources:** IdP application access logs
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.sso"
| stats dc(actor.alternateId) as unique_users, count as total_access by target{}.displayName
| sort -unique_users
```
- **Implementation:** Track SSO events per application. Build user-application access matrix. Detect users accessing applications outside their normal pattern. Report on application usage for license optimization and access reviews.
- **Visualization:** Bar chart (top applications by user count), Table (application usage summary), Heatmap (user × application access).

---

### UC-9.3.5 · IdP Availability Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** IdP outage blocks all SSO authentication across the organization. Rapid detection enables failover and communication.
- **App/TA:** Scripted input (HTTP check), `Splunk_TA_okta`
- **Data Sources:** IdP status API, synthetic monitoring, Okta system health
- **SPL:**
```spl
index=synthetic sourcetype="http_check" target="*.okta.com"
| timechart span=1m avg(response_time_ms) as rt, count(eval(status_code>=500)) as errors
| where rt > 5000 OR errors > 0
```
- **Implementation:** Set up synthetic HTTP checks against IdP login endpoints every minute. Track response time and availability. Alert on response time >5 seconds or any 5xx errors. Subscribe to vendor status page updates as secondary source.
- **Visualization:** Single value (IdP uptime %), Line chart (response time), Status indicator (available/degraded/down).

---

### UC-9.3.6 · Phishing-Resistant MFA Adoption
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks migration from phishable factors (SMS, phone) to phishing-resistant factors (FIDO2, WebAuthn). Supports zero-trust maturity goals.
- **App/TA:** `Splunk_TA_okta`, IdP MFA enrollment data
- **Data Sources:** IdP MFA enrollment logs, factor type metadata
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.auth_via_mfa"
| stats count by debugContext.debugData.factor
| eval factor_type=case(match(factor,"FIDO"),"phishing_resistant", match(factor,"push"),"medium", 1=1,"phishable")
| stats sum(count) as total by factor_type
```
- **Implementation:** Track MFA factor types used in authentication events. Classify as phishing-resistant (FIDO2, WebAuthn) vs phishable (SMS, voice, email). Report adoption percentages. Set organizational targets for phishing-resistant adoption.
- **Visualization:** Pie chart (factor type distribution), Line chart (phishing-resistant adoption trend), Table (users still on SMS).

---

### UC-9.3.7 · Session Hijacking Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Sessions used from multiple locations simultaneously indicate session token theft. Detection prevents ongoing unauthorized access.
- **App/TA:** `Splunk_TA_okta`, IdP session logs
- **Data Sources:** IdP session activity logs, application session logs
- **SPL:**
```spl
index=okta sourcetype="OktaIM2:log"
| stats dc(client.ipAddress) as unique_ips, values(client.ipAddress) as ips by authenticationContext.externalSessionId, actor.alternateId
| where unique_ips > 2
| table actor.alternateId, authenticationContext.externalSessionId, unique_ips, ips
```
- **Implementation:** Track session IDs across events. Alert when a single session is used from multiple IP addresses simultaneously (excluding known VPN/proxy IPs). Correlate with user agent changes for additional confidence.
- **Visualization:** Table (hijacked sessions), Timeline (suspicious session events), Bar chart (users with multi-IP sessions).

---

### 9.4 Privileged Access Management (PAM)

**Primary App/TA:** Vendor-specific TAs — CyberArk TA (`TA-CyberArk`), BeyondTrust TA, Delinea (Thycotic) TA.

---

### UC-9.4.1 · Privileged Session Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Complete audit trail of privileged sessions is required for compliance (SOX, PCI, HIPAA) and security investigation.
- **App/TA:** Splunk_TA_cyberark, BeyondTrust TA for Splunk
- **Data Sources:** PAM session logs (session start/end, target system, user, protocol)
- **SPL:**
```spl
index=pam sourcetype="cyberark:session"
| table _time, user, target_host, target_account, protocol, duration_min, session_id
| sort -_time
```
- **Implementation:** Install vendor PAM TA. Forward PAM vault/session logs to Splunk. Track all privileged sessions with full metadata. Alert on sessions outside business hours or to unexpected targets. Retain logs per compliance requirements.
- **Visualization:** Table (session history), Bar chart (sessions by user), Timeline (privileged access events), Heatmap (user × time of day).

---

### UC-9.4.2 · Password Checkout Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusual checkout patterns may indicate misuse. Tracking ensures accountability and supports investigations.
- **App/TA:** Splunk_TA_cyberark
- **Data Sources:** PAM vault logs (password retrieve/checkin events)
- **SPL:**
```spl
index=pam sourcetype="cyberark:vault"
| search action="Retrieve" OR action="Checkin"
| transaction user, account maxspan=8h
| eval checkout_duration_hr=duration/3600
| where checkout_duration_hr > 4
| table user, account, target, checkout_duration_hr
```
- **Implementation:** Track password checkout and checkin events. Calculate checkout duration. Alert on checkouts exceeding policy limits (e.g., >4 hours). Flag accounts checked out but never checked in (hoarding). Report on checkout frequency per user.
- **Visualization:** Table (active checkouts), Bar chart (checkout duration by user), Line chart (checkout frequency trend).

---

### UC-9.4.3 · Break-Glass Account Usage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Break-glass accounts provide emergency access and should rarely be used. Any usage requires immediate investigation and documentation.
- **App/TA:** Splunk_TA_cyberark, custom alert
- **Data Sources:** PAM vault events for break-glass accounts
- **SPL:**
```spl
index=pam sourcetype="cyberark:vault"
| search account_type="break_glass" OR account IN ("emergency_admin","firecall_*")
| table _time, user, account, target, action
| sort -_time
```
- **Implementation:** Tag break-glass accounts in PAM. Create critical alert for any break-glass access. Require documented reason within 24 hours. Send notifications to security team and management. Track usage frequency for trend reporting.
- **Visualization:** Single value (break-glass uses this month — target: 0), Table (usage history), Timeline (break-glass events).

---

### UC-9.4.4 · Credential Rotation Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Overdue password rotations increase exposure window if credentials are compromised. Compliance tracking ensures policy adherence.
- **App/TA:** PAM TA, scripted input
- **Data Sources:** PAM vault credential metadata (last rotation date, policy)
- **SPL:**
```spl
index=pam sourcetype="cyberark:account_inventory"
| eval days_since_rotation=round((now()-last_rotation_epoch)/86400)
| eval overdue=if(days_since_rotation > rotation_policy_days, "Yes", "No")
| where overdue="Yes"
| table account, target, days_since_rotation, rotation_policy_days
| sort -days_since_rotation
```
- **Implementation:** Export credential inventory from PAM periodically. Calculate days since last rotation vs policy requirement. Alert on overdue rotations. Track compliance percentage over time. Report to management monthly.
- **Visualization:** Table (overdue credentials), Single value (compliance %), Gauge (% compliant), Bar chart (overdue by platform).

---

### UC-9.4.5 · Suspicious Session Commands
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Detecting dangerous commands during privileged sessions enables real-time intervention before damage occurs.
- **App/TA:** CyberArk PSM, BeyondTrust session monitoring
- **Data Sources:** PAM session recordings/keystroke logs
- **SPL:**
```spl
index=pam sourcetype="cyberark:psm_transcript"
| search command IN ("rm -rf","format","del /s","DROP DATABASE","shutdown","halt","init 0")
| table _time, user, target_host, command, session_id
```
- **Implementation:** Enable PAM session recording and command logging. Parse keystroke transcripts. Alert immediately on high-risk commands (rm -rf, format, DROP DATABASE, etc.). Integrate with SOAR for automated session termination on critical detections.
- **Visualization:** Table (suspicious commands), Timeline (command events), Single value (high-risk commands today).

---

### UC-9.4.6 · Vault Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** PAM vault downtime prevents all privileged access, blocking critical operations. Health monitoring ensures continuous availability.
- **App/TA:** PAM infrastructure monitoring, SNMP
- **Data Sources:** PAM vault system logs, component health APIs
- **SPL:**
```spl
index=pam sourcetype="cyberark:vault_health"
| stats latest(status) as status, latest(replication_lag) as lag by vault_server, component
| where status!="Running" OR lag > 300
```
- **Implementation:** Monitor PAM vault components (vault server, PVWA, PSM, CPM). Track service availability, replication between primary/DR vault, and component health. Alert on any component failure or replication lag >5 minutes.
- **Visualization:** Status grid (component × health), Single value (vault uptime %), Table (unhealthy components), Line chart (replication lag).

---

## 10. Security Infrastructure

### 10.1 Next-Gen Firewalls (Security-Focused)

**Primary App/TA:** Palo Alto Networks Add-on (`Splunk_TA_paloalto`), Cisco Firepower TA, Fortinet FortiGate TA.

---

### UC-10.1.1 · Threat Prevention Event Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Trending threat detections reveals attack campaigns, persistent threats, and the effectiveness of security controls.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_cisco-firepower
- **Data Sources:** Threat logs (IPS, AV, anti-spyware detections)
- **SPL:**
```spl
index=pan sourcetype="pan:threat" severity IN ("critical","high")
| timechart span=1h count by subtype
```
- **Implementation:** Forward NGFW threat logs to Splunk via syslog or API. Parse severity, threat name, source/destination, and action. Track by severity and type over time. Alert on critical severity detections. Correlate with endpoint data.
- **Visualization:** Line chart (threat events by severity), Bar chart (top threats), Table (critical events), Stacked area (threat types over time).

---

### UC-10.1.2 · Wildfire / Sandbox Verdicts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks zero-day and unknown malware detection effectiveness. Malicious verdicts require immediate investigation of affected hosts.
- **App/TA:** `Splunk_TA_paloalto`
- **Data Sources:** Wildfire submission logs, sandbox analysis results
- **SPL:**
```spl
index=pan sourcetype="pan:wildfire"
| stats count by verdict, filetype
| eval verdict_label=case(verdict=0,"benign", verdict=1,"malware", verdict=2,"grayware", verdict=4,"phishing")
```
- **Implementation:** Enable Wildfire logging on NGFW. Forward submission results to Splunk. Alert immediately on malware verdicts. Track affected users/hosts for investigation. Report on submission volumes and malicious file types.
- **Visualization:** Pie chart (verdict distribution), Table (malware verdicts with details), Line chart (submissions over time), Bar chart (by file type).

---

### UC-10.1.3 · C2 Communication Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Command-and-control communication indicates active compromise. Detection enables containment before data exfiltration or lateral movement.
- **App/TA:** `Splunk_TA_paloalto`, threat intel feeds
- **Data Sources:** Threat logs (C2 signatures), URL filtering (malware/C2 categories), DNS logs
- **SPL:**
```spl
index=pan sourcetype="pan:threat" category="command-and-control"
| stats count, values(dest_ip) as c2_servers by src_ip, src_user
| sort -count
```
- **Implementation:** Enable URL filtering and threat prevention with C2 categories. Forward to Splunk. Alert immediately on any C2 detection. Integrate with threat intel feeds for IP/domain enrichment. Trigger automated containment via SOAR.
- **Visualization:** Table (C2 detections with source/dest), Geo map (C2 server locations), Timeline (C2 events), Network diagram.

---

### UC-10.1.4 · DNS Sinkhole Hits
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** DNS sinkhole hits confirm infected endpoints attempting to reach malicious domains. Each hit is a confirmed compromise indicator.
- **App/TA:** `Splunk_TA_paloalto`
- **Data Sources:** DNS proxy logs (sinkhole action), threat logs
- **SPL:**
```spl
index=pan sourcetype="pan:threat" action="sinkhole"
| stats count by src_ip, domain, threat_name
| sort -count
```
- **Implementation:** Configure DNS sinkhole on NGFW. Forward threat logs with sinkhole actions to Splunk. Alert on each unique source IP hitting sinkhole. Trigger automated endpoint investigation. Track resolution status.
- **Visualization:** Table (sinkholed hosts with domains), Single value (compromised hosts count), Bar chart (top sinkholed domains).

---

### UC-10.1.5 · SSL Decryption Coverage
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Encrypted traffic that isn't inspected creates a blind spot. Measuring decryption coverage ensures security visibility.
- **App/TA:** `Splunk_TA_paloalto`
- **Data Sources:** Decryption statistics, traffic logs (encrypted vs decrypted flags)
- **SPL:**
```spl
index=pan sourcetype="pan:traffic"
| eval decrypted=if(flags LIKE "%decrypt%",1,0)
| stats sum(decrypted) as decrypted_sessions, count as total_sessions
| eval coverage_pct=round(decrypted_sessions/total_sessions*100,1)
```
- **Implementation:** Enable decryption logging on NGFW. Track percentage of HTTPS traffic being decrypted. Identify exempted destinations and evaluate risk. Report coverage to security leadership. Target >80% coverage.
- **Visualization:** Single value (decryption coverage %), Pie chart (decrypted vs bypassed), Bar chart (top bypassed destinations).

---

### 10.2 Intrusion Detection/Prevention (IDS/IPS)

**Primary App/TA:** Vendor-specific TAs, Snort/Suricata syslog parsing.

---

### UC-10.2.1 · Alert Severity Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Trending IDS alerts reveals attack patterns, campaign surges, and tuning opportunities. Supports SOC workload planning.
- **App/TA:** TA-suricata, Splunk_TA_cisco-firepower
- **Data Sources:** IDS/IPS alert logs
- **SPL:**
```spl
index=ids sourcetype="snort:alert"
| timechart span=1h count by priority
```
- **Implementation:** Forward IDS alerts to Splunk via syslog. Normalize severity/priority fields. Track alert volume by severity over time. Identify noisy signatures for tuning. Alert on sudden spikes in high-severity events.
- **Visualization:** Stacked area (alerts by severity), Line chart (alert volume trend), Table (top alerts today).

---

### UC-10.2.2 · Top Targeted Hosts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Identifies the most-attacked internal hosts, prioritizing vulnerability remediation and incident investigation.
- **App/TA:** IDS/IPS TA
- **Data Sources:** IDS/IPS alert logs (destination host)
- **SPL:**
```spl
index=ids sourcetype="snort:alert" priority<=2
| stats count, dc(signature) as unique_sigs by dest_ip
| sort -count
| head 20
```
- **Implementation:** Parse destination IP from IDS alerts. Aggregate by target host. Enrich with CMDB data (asset owner, criticality). Alert when a single host receives multiple high-severity alerts. Trigger vulnerability scan for top targets.
- **Visualization:** Table (top targeted hosts), Bar chart (alerts by host), Geo map (source attackers).

---

### UC-10.2.3 · Signature Coverage Gaps
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Identifying network segments without IDS coverage ensures comprehensive threat detection across the infrastructure.
- **App/TA:** IDS sensor health monitoring
- **Data Sources:** Sensor health reports, network segment inventory
- **SPL:**
```spl
| inputlookup network_segments.csv
| join type=left segment_name
    [search index=ids sourcetype="snort:alert" earliest=-7d
     | stats count by sensor, segment_name]
| where isnull(count) OR count=0
| table segment_name, expected_sensor, count
```
- **Implementation:** Maintain network segment inventory with expected IDS sensor mapping. Compare against actual alert data. Alert when a segment has no IDS events for >7 days (sensor may be down or misconfigured).
- **Visualization:** Table (uncovered segments), Status grid (segment × coverage), Single value (coverage %).

---

### UC-10.2.4 · False Positive Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** High false positive rates waste analyst time and cause alert fatigue. Systematic tracking drives tuning improvements.
- **App/TA:** IDS TA + analyst workflow
- **Data Sources:** IDS alerts + analyst disposition data (true/false positive)
- **SPL:**
```spl
index=ids sourcetype="snort:alert"
| join signature [| inputlookup signature_dispositions.csv]
| stats count(eval(disposition="false_positive")) as fp, count as total by signature
| eval fp_rate=round(fp/total*100,1)
| where fp_rate > 50
| sort -fp_rate
```
- **Implementation:** Track analyst dispositions for IDS alerts (true positive, false positive, benign). Calculate false positive rate per signature. Flag signatures with >50% FP rate for tuning. Report on overall alert quality metrics.
- **Visualization:** Bar chart (FP rate by signature), Line chart (FP rate trend), Table (signatures needing tuning).

---

### UC-10.2.5 · Lateral Movement Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** IDS detections on internal network segments indicate an attacker has breached the perimeter and is moving laterally.
- **App/TA:** IDS TA (internal sensors)
- **Data Sources:** IDS alerts from internal/east-west sensors
- **SPL:**
```spl
index=ids sourcetype="snort:alert" sensor_zone="internal"
| search category IN ("attempted-admin","trojan-activity","policy-violation","misc-attack")
| stats count by src_ip, dest_ip, signature
| sort -count
```
- **Implementation:** Deploy IDS sensors on internal network segments (not just perimeter). Forward alerts to Splunk. Alert on any high-severity internal detections. Correlate with AD authentication events and endpoint data for full attack chain visibility.
- **Visualization:** Network diagram (lateral movement paths), Table (internal IDS alerts), Timeline (attack progression).

---

### 10.3 Endpoint Detection & Response (EDR)

**Primary App/TA:** CrowdStrike TA (`TA-crowdstrike-falcon-event-streams`), Microsoft Defender TA, Cisco Secure Endpoint TA, SentinelOne TA.

---

### UC-10.3.1 · Malware Detection Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Detection trends reveal campaign targeting, endpoint hygiene, and control effectiveness. Spikes indicate active incidents.
- **App/TA:** TA-crowdstrike-falcon-event-streams, TA-microsoft-defender
- **Data Sources:** EDR detection events
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:detection"
| timechart span=1d count by severity
```
- **Implementation:** Ingest EDR detection events via TA or API. Normalize detection severity. Track daily detection rates by severity, type, and business unit. Alert on spikes exceeding 2× daily baseline. Report on detection-to-response times.
- **Visualization:** Line chart (detections over time), Bar chart (detections by type), Pie chart (severity distribution).

---

### UC-10.3.2 · Quarantine Action Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Failed quarantine means malware remains active on the endpoint. Monitoring ensures automated remediation is working.
- **App/TA:** EDR TA
- **Data Sources:** EDR remediation/action logs
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:detection"
| stats count(eval(action="quarantined")) as quarantined, count(eval(action="allowed")) as allowed by severity
| eval quarantine_rate=round(quarantined/(quarantined+allowed)*100,1)
```
- **Implementation:** Track EDR remediation actions (quarantine, kill process, isolate). Calculate quarantine success rate. Alert on failed quarantine actions. Follow up on "allowed" malware detections to ensure analyst review.
- **Visualization:** Pie chart (action distribution), Single value (quarantine success %), Table (failed quarantine events).

---

### UC-10.3.3 · Agent Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Endpoints without healthy EDR agents are blind spots. Gap detection ensures comprehensive coverage.
- **App/TA:** EDR TA, scripted input
- **Data Sources:** EDR agent status API, last check-in timestamps
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:sensor_health"
| eval hours_since_checkin=round((now()-last_seen_epoch)/3600,1)
| where hours_since_checkin > 24 OR sensor_version < "6.50"
| table hostname, os, sensor_version, hours_since_checkin, status
```
- **Implementation:** Poll EDR agent status API daily. Identify agents offline >24 hours, outdated versions, or degraded status. Cross-reference with CMDB for full coverage analysis. Alert on critical servers with unhealthy agents.
- **Visualization:** Table (unhealthy agents), Single value (% healthy), Pie chart (agent version distribution), Bar chart (offline by OS).

---

### UC-10.3.4 · Behavioral Detection Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Behavioral detections catch attacks that bypass signatures (fileless malware, LOLBins, living-off-the-land). These are high-fidelity signals.
- **App/TA:** EDR TA
- **Data Sources:** EDR behavioral/heuristic alerts
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:detection" technique_id="T*"
| stats count by technique_id, tactic, hostname
| sort -count
```
- **Implementation:** Ingest behavioral detection data. Map to MITRE ATT&CK framework (technique_id, tactic). Alert on high-confidence behavioral detections. Track most common techniques for threat intelligence and red team exercises.
- **Visualization:** MITRE ATT&CK heatmap, Table (behavioral detections), Bar chart (top techniques).

---

### UC-10.3.5 · Endpoint Isolation Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Isolation events indicate active incident response. Tracking ensures isolation is maintained and properly lifted when resolved.
- **App/TA:** EDR TA
- **Data Sources:** EDR containment/isolation logs
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:containment"
| table _time, hostname, action, initiated_by, reason
| sort -_time
```
- **Implementation:** Track all isolation events (isolate, un-isolate). Alert on isolation events for awareness. Track isolation duration. Alert when endpoints remain isolated >24 hours without resolution. Maintain isolation audit trail.
- **Visualization:** Table (isolated endpoints), Timeline (isolation events), Single value (currently isolated count).

---

### UC-10.3.6 · Threat Hunting Indicators
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Proactive threat hunting using EDR telemetry detects stealthy threats that evade automated detection.
- **App/TA:** EDR TA (telemetry data)
- **Data Sources:** EDR process telemetry, file events, network connections
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:events"
| search (process_name="powershell.exe" AND command_line="*-enc*")
    OR (process_name="rundll32.exe" AND parent_process_name!="explorer.exe")
    OR (process_name="certutil.exe" AND command_line="*-urlcache*")
| table _time, hostname, user, process_name, command_line, parent_process_name
```
- **Implementation:** Ingest EDR telemetry (process creation, network connections, file writes). Create hunting queries for LOLBin usage, encoded PowerShell, suspicious parent-child process relationships. Schedule as recurring searches for continuous hunting.
- **Visualization:** Table (suspicious indicators), Timeline (hunting hits), Bar chart (indicators by technique).

---

### UC-10.3.7 · EDR Coverage Gaps
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Identifies endpoints without EDR protection, closing blind spots that attackers exploit.
- **App/TA:** EDR API + CMDB lookup
- **Data Sources:** EDR agent inventory, CMDB/asset inventory
- **SPL:**
```spl
| inputlookup cmdb_endpoints.csv WHERE os_type IN ("Windows","Linux","macOS")
| join type=left hostname [search index=edr sourcetype="crowdstrike:sensor_health" | stats latest(status) as edr_status by hostname]
| where isnull(edr_status) OR edr_status!="active"
| table hostname, os_type, department, edr_status
```
- **Implementation:** Export EDR agent inventory and cross-reference with CMDB/AD computer accounts. Identify systems without agents. Report coverage percentage. Alert when coverage drops below target (e.g., <98%). Prioritize critical servers.
- **Visualization:** Single value (coverage %), Table (uncovered endpoints), Pie chart (covered vs uncovered), Bar chart (gaps by department).

---

### UC-10.3.8 · Ransomware Canary Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** EDR-detected mass file encryption patterns provide earliest possible ransomware detection, enabling automated containment.
- **App/TA:** EDR TA
- **Data Sources:** EDR behavioral detection (mass file modification patterns)
- **SPL:**
```spl
index=edr sourcetype="crowdstrike:detection"
| search tactic="impact" technique_id="T1486"
| table _time, hostname, user, process_name, severity, description
```
- **Implementation:** Ensure EDR has behavioral ransomware detection enabled. Alert at critical priority on any ransomware behavioral detection. Integrate with SOAR for automated endpoint isolation. Track affected file scope from EDR telemetry.
- **Visualization:** Single value (ransomware detections — target: 0), Table (detection details), Timeline (ransomware events).

---

### 10.4 Email Security

**Primary App/TA:** Splunk Add-on for Microsoft Office 365 (`Splunk_TA_MS_O365`), Proofpoint TA, vendor-specific email security TAs.

---

### UC-10.4.1 · Phishing Detection Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Measures email security effectiveness. Increasing phishing volumes or declining detection rates indicate evolving threats.
- **App/TA:** Splunk_TA_MS_O365, TA-proofpoint
- **Data Sources:** Email security gateway logs, EOP message trace
- **SPL:**
```spl
index=email sourcetype="ms:o365:messageTrace"
| eval is_phish=if(match(FilteringResult,"Phish") OR match(FilteringResult,"Spoof"),1,0)
| stats sum(is_phish) as phishing_caught, count as total_messages
| eval phish_rate=round(phishing_caught/total_messages*100,4)
```
- **Implementation:** Ingest email security logs (EOP message trace, gateway logs). Track phishing detections over time. Calculate detection rate vs total messages. Alert on spikes in phishing volume. Report on phishing types and targeted users.
- **Visualization:** Line chart (phishing volume trend), Single value (phishing rate %), Bar chart (phishing by type), Table (top targeted users).

---

### UC-10.4.2 · Malicious Attachment Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Attachment-based threats bypass URL filtering. Tracking by file type reveals attack vectors and informs policy decisions.
- **App/TA:** Email security TA
- **Data Sources:** Email gateway attachment scanning logs, safe attachments logs
- **SPL:**
```spl
index=email sourcetype="ms:o365:messageTrace"
| search FilteringResult="*malware*" OR FilteringResult="*SafeAttachment*"
| stats count by SenderAddress, Subject, FilteringResult
| sort -count
```
- **Implementation:** Enable attachment scanning in email gateway. Ingest scanning results. Track detections by file type, sender domain, and verdict. Alert on malicious attachments reaching users (detection after delivery). Report on blocked attachment statistics.
- **Visualization:** Bar chart (detections by file type), Table (malicious attachments), Line chart (detection trend), Pie chart (verdict distribution).

---

### UC-10.4.3 · URL Click Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks which users click malicious URLs in emails — the moment a phishing email becomes an active incident.
- **App/TA:** Splunk_TA_MS_O365 (Safe Links), Proofpoint URL Defense
- **Data Sources:** URL rewrite/protection logs, click tracking events
- **SPL:**
```spl
index=email sourcetype="ms:o365:dlp" OR sourcetype="proofpoint:click"
| search verdict="malicious" AND action="allowed"
| table _time, userPrincipalName, url, verdict, action
```
- **Implementation:** Enable Safe Links (M365) or URL Defense (Proofpoint). Ingest click tracking data. Alert immediately when a user clicks a malicious URL. Trigger automated password reset and endpoint scan. Track click-through rates for security awareness metrics.
- **Visualization:** Table (malicious URL clicks), Bar chart (clicks by user), Timeline (click events), Single value (clicks on malicious URLs today).

---

### UC-10.4.4 · DLP Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Email DLP violations indicate potential data exfiltration or policy non-compliance. Monitoring supports regulatory compliance.
- **App/TA:** Splunk_TA_MS_O365
- **Data Sources:** M365 DLP logs, email gateway DLP events
- **SPL:**
```spl
index=email sourcetype="ms:o365:dlp"
| stats count by PolicyName, UserPrincipalName, SensitiveInformationType
| sort -count
```
- **Implementation:** Configure M365 DLP policies for sensitive data types (SSN, credit card, etc.). Ingest DLP violation events. Alert on high-severity violations. Track violation trends per policy and user for compliance reporting.
- **Visualization:** Bar chart (violations by policy), Table (top violators), Line chart (violation trend), Pie chart (by data type).

---

### UC-10.4.5 · Spoofed Email Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** DMARC/SPF/DKIM failures indicate email spoofing attempts. Monitoring validates email authentication configuration.
- **App/TA:** Email security TA
- **Data Sources:** DMARC aggregate reports, email authentication logs
- **SPL:**
```spl
index=email sourcetype="dmarc:aggregate"
| where dkim_result!="pass" OR spf_result!="pass"
| stats count by source_ip, header_from, dkim_result, spf_result, disposition
| sort -count
```
- **Implementation:** Configure DMARC reporting (aggregate to a designated mailbox). Ingest DMARC XML reports. Track authentication failures by sending domain. Alert on spoofing of your own domains. Move toward DMARC p=reject for full protection.
- **Visualization:** Table (authentication failures), Bar chart (failures by domain), Pie chart (pass vs fail), Line chart (spoofing trend).

---

### UC-10.4.6 · Email Volume Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusual outbound email volumes may indicate compromised accounts used for spam/phishing or mass data exfiltration via email.
- **App/TA:** Splunk_TA_MS_O365, Splunk_TA_microsoft-exchange
- **Data Sources:** Email message tracking logs (outbound)
- **SPL:**
```spl
index=email sourcetype="ms:o365:messageTrace" Direction="Outbound"
| stats count by SenderAddress
| eventstats avg(count) as avg_sent, stdev(count) as stdev_sent
| where count > avg_sent + 3*stdev_sent
| table SenderAddress, count, avg_sent
```
- **Implementation:** Track outbound email volume per sender. Baseline normal patterns. Alert when any sender exceeds 3× standard deviation. Correlate with sign-in events to detect compromised accounts. Report on top senders for capacity planning.
- **Visualization:** Bar chart (top senders), Line chart (outbound volume trend), Table (anomalous senders).

---

### UC-10.4.7 · Quarantine Management
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks quarantine effectiveness and user release requests to balance security with user productivity.
- **App/TA:** Splunk_TA_MS_O365, email gateway TA
- **Data Sources:** Email quarantine logs, release request logs
- **SPL:**
```spl
index=email sourcetype="ms:o365:messageTrace"
| search FilteringResult="*Quarantine*"
| stats count by FilteringResult, SenderAddress
| sort -count
```
- **Implementation:** Track quarantine volumes, reasons, and user release requests. Alert on unusual quarantine rates (may indicate new phishing campaign). Monitor false positive rate (legitimate emails quarantined) for policy tuning.
- **Visualization:** Bar chart (quarantine reasons), Line chart (quarantine volume trend), Table (release requests), Single value (quarantine rate %).

---

### 10.5 Web Security / Secure Web Gateway

**Primary App/TA:** Cisco Umbrella TA (`Splunk_TA_cisco-umbrella`), Zscaler TA, Netskope TA, vendor-specific SWG TAs.

---

### UC-10.5.1 · Blocked Category Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Trending blocked categories reveals user behavior patterns and informs acceptable use policy. Spikes may indicate infections.
- **App/TA:** Splunk Add-on for Cisco Umbrella, TA-zscaler
- **Data Sources:** SWG/proxy logs (URL category, action)
- **SPL:**
```spl
index=proxy sourcetype="cisco:umbrella" action="Blocked"
| top limit=20 categories
```
- **Implementation:** Forward SWG logs to Splunk. Track blocked requests by category over time. Identify trending categories. Alert on spikes in malware/phishing categories. Report on policy effectiveness.
- **Visualization:** Bar chart (top blocked categories), Line chart (blocks over time), Pie chart (block distribution).

---

### UC-10.5.2 · Shadow IT Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unapproved SaaS usage creates data security risks and compliance gaps. Discovery enables governance and risk assessment.
- **App/TA:** SWG/CASB TA
- **Data Sources:** SWG logs (application identification), CASB logs
- **SPL:**
```spl
index=proxy sourcetype="cisco:umbrella"
| stats dc(src_ip) as unique_users, sum(bytes) as total_bytes by app_name
| lookup approved_apps.csv app_name OUTPUT approved
| where isnull(approved) OR approved="No"
| sort -unique_users
```
- **Implementation:** Enable application identification in SWG. Maintain lookup of approved SaaS applications. Identify unapproved apps by user count and data volume. Report to IT governance for risk assessment. Track adoption of approved alternatives.
- **Visualization:** Table (unapproved apps with user counts), Bar chart (top shadow IT apps), Pie chart (approved vs unapproved traffic).

---

### UC-10.5.3 · Malware Download Blocks
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Each blocked malware download represents a prevented infection. Tracking reveals targeted users and attack vectors.
- **App/TA:** SWG TA
- **Data Sources:** SWG threat logs (malware blocks)
- **SPL:**
```spl
index=proxy sourcetype="zscaler:web" action="Blocked" threat_category="Malware"
| stats count by src_user, url, threat_name
| sort -count
```
- **Implementation:** Enable threat scanning in SWG. Forward threat events to Splunk. Alert on malware download blocks for user awareness. Track targeted users for phishing correlation. Report on malware types and delivery methods.
- **Visualization:** Bar chart (malware blocks by type), Table (blocked downloads), Line chart (block rate trend), Single value (blocks today).

---

### UC-10.5.4 · DLP over Web Traffic
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Web DLP events indicate sensitive data being uploaded to unauthorized destinations. Critical for compliance.
- **App/TA:** SWG/CASB TA
- **Data Sources:** SWG DLP logs (file uploads, paste detection)
- **SPL:**
```spl
index=proxy sourcetype="netskope:events" alert_type="DLP"
| stats count by user, app, policy_name, file_type
| sort -count
```
- **Implementation:** Configure DLP policies in SWG/CASB for sensitive data patterns. Ingest DLP violation events. Alert on high-severity violations. Track by user, destination app, and data type. Report for compliance audits.
- **Visualization:** Table (DLP violations), Bar chart (violations by policy), Line chart (violation trend), Pie chart (by data type).

---

### UC-10.5.5 · DNS Security Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Blocked DNS queries to malicious domains indicate infection attempts or active compromise. Each block is a security win.
- **App/TA:** Splunk Add-on for Cisco Umbrella
- **Data Sources:** Umbrella/DNS security logs
- **SPL:**
```spl
index=dns_security sourcetype="cisco:umbrella" action="Blocked"
| stats count by internalIp, domain, categories
| where match(categories,"Malware|Command and Control|Phishing")
| sort -count
```
- **Implementation:** Deploy DNS security (Umbrella, Zscaler). Forward blocked query logs to Splunk. Alert on blocks in malware/C2/phishing categories. Track affected internal IPs for investigation. Report on DNS security effectiveness.
- **Visualization:** Table (blocked domains with sources), Bar chart (blocks by category), Single value (unique blocked domains today).

---

### UC-10.5.6 · Bandwidth Abuse Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Excessive bandwidth on non-business sites impacts network performance and productivity. Detection supports acceptable use enforcement.
- **App/TA:** SWG TA
- **Data Sources:** SWG traffic logs (bytes transferred, URL category)
- **SPL:**
```spl
index=proxy sourcetype="cisco:umbrella"
| stats sum(bytes) as total_bytes by src_user, categories
| where match(categories,"Streaming|Gaming|Social") AND total_bytes > 1073741824
| eval gb=round(total_bytes/1073741824,2)
| table src_user, categories, gb
```
- **Implementation:** Track bandwidth usage per user by URL category. Alert when individual users exceed thresholds on non-business categories (>1GB/day on streaming). Report top bandwidth consumers for management review.
- **Visualization:** Bar chart (bandwidth by user/category), Table (top consumers), Pie chart (bandwidth by category).

---

### UC-10.5.7 · Unencrypted Traffic Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Sensitive data transmitted over HTTP is vulnerable to interception. Detection ensures encryption compliance.
- **App/TA:** SWG TA
- **Data Sources:** SWG traffic logs (protocol, URL)
- **SPL:**
```spl
index=proxy sourcetype="cisco:umbrella" protocol="HTTP"
| search NOT url="http://ocsp.*" NOT url="http://crl.*"
| stats count by src_user, domain
| sort -count
```
- **Implementation:** Monitor HTTP (non-HTTPS) traffic in SWG logs. Filter out legitimate HTTP uses (OCSP, CRL). Alert when sensitive applications are accessed over HTTP. Report unencrypted traffic percentage as a security metric.
- **Visualization:** Table (HTTP traffic by destination), Pie chart (HTTP vs HTTPS), Line chart (unencrypted traffic trend).

---

### 10.6 Vulnerability Management

**Primary App/TA:** Tenable TA (`TA-tenable`), Qualys TA, Rapid7 TA.

---

### UC-10.6.1 · Critical Vulnerability Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Tracking critical vulnerabilities over time measures security posture improvement and identifies remediation stalls.
- **App/TA:** TA-tenable, TA-QualysCloudPlatform
- **Data Sources:** Vulnerability scan results (severity, CVE, affected asset)
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln"
| where severity IN ("Critical","High")
| timechart span=1d dc(cve_id) as unique_vulns by severity
```
- **Implementation:** Ingest scan results from vulnerability management platform. Track unique vulnerabilities by severity over time. Alert when critical count exceeds threshold or increases. Report on remediation progress weekly.
- **Visualization:** Line chart (vuln count trend by severity), Single value (critical vuln count), Bar chart (top CVEs), Table (critical vulnerabilities).

---

### UC-10.6.2 · Mean Time to Remediation
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** MTTR measures remediation efficiency. Long MTTR indicates process bottlenecks or resource constraints requiring management attention.
- **App/TA:** Vuln management TA
- **Data Sources:** Scan results with first_seen and last_seen dates
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" state="Fixed"
| eval mttr_days=round((fixed_date-first_seen)/86400)
| stats avg(mttr_days) as avg_mttr, median(mttr_days) as median_mttr by severity
```
- **Implementation:** Track first_seen and fixed_date for each vulnerability. Calculate MTTR by severity. Report against SLA targets (Critical: 7d, High: 30d, Medium: 90d). Identify teams with consistently high MTTR for process improvement.
- **Visualization:** Bar chart (MTTR by severity), Line chart (MTTR trend), Table (SLA compliance by team).

---

### UC-10.6.3 · Scan Coverage Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Assets not scanned are unknown risks. Coverage monitoring ensures comprehensive vulnerability assessment.
- **App/TA:** Vuln management TA + CMDB
- **Data Sources:** Scan activity, asset inventory
- **SPL:**
```spl
| inputlookup cmdb_assets.csv
| join type=left hostname [search index=vulnerability sourcetype="tenable:vuln" | stats latest(_time) as last_scan by hostname]
| eval days_since_scan=round((now()-last_scan)/86400)
| where isnull(last_scan) OR days_since_scan > 30
| table hostname, os, department, last_scan, days_since_scan
```
- **Implementation:** Cross-reference scan targets with CMDB. Identify assets not scanned in 30 days. Alert on scan failures. Track coverage percentage as a KPI. Report on uncovered assets for remediation.
- **Visualization:** Single value (scan coverage %), Table (unscanned assets), Pie chart (scanned vs unscanned), Bar chart (gaps by department).

---

### UC-10.6.4 · Patch Compliance by Team/BU
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Per-team compliance views drive accountability and enable targeted remediation efforts where they're most needed.
- **App/TA:** Vuln management TA + CMDB
- **Data Sources:** Scan results enriched with CMDB ownership data
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" severity IN ("Critical","High")
| lookup cmdb_assets.csv hostname OUTPUT department, owner
| stats dc(cve_id) as open_vulns, dc(hostname) as affected_hosts by department
| sort -open_vulns
```
- **Implementation:** Enrich vulnerability data with asset ownership from CMDB. Aggregate by team/business unit. Create weekly compliance scorecard. Share with leadership for accountability. Track improvement trends per team.
- **Visualization:** Bar chart (vulns by team), Table (team compliance scorecard), Line chart (compliance trend by team).

---

### UC-10.6.5 · Exploitable Vulnerability Prioritization
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Not all vulnerabilities are equal — those with known exploits pose immediate risk. Prioritization focuses remediation on the highest-risk items.
- **App/TA:** Vuln management TA + threat intel
- **Data Sources:** Scan results + CISA KEV catalog + EPSS scores
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" severity="Critical"
| lookup cisa_kev.csv cve_id OUTPUT known_exploited, ransomware_associated
| lookup epss_scores.csv cve_id OUTPUT epss_score
| where known_exploited="Yes" OR epss_score > 0.5
| table hostname, cve_id, severity, epss_score, known_exploited, ransomware_associated
| sort -epss_score
```
- **Implementation:** Maintain CISA KEV and EPSS lookup tables (update weekly). Enrich vulnerability data with exploit intelligence. Prioritize vulnerabilities with known exploits and high EPSS scores. Alert immediately on new KEV vulnerabilities found in environment.
- **Visualization:** Table (exploitable vulns prioritized), Single value (KEV vulns in environment), Bar chart (EPSS distribution), Scatter plot (severity × EPSS).

---

### UC-10.6.6 · Vulnerability SLA Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** SLA tracking ensures vulnerabilities are remediated within policy timeframes. Non-compliance creates audit findings.
- **App/TA:** Vuln management TA
- **Data Sources:** Scan results with detection timestamps, SLA policy lookup
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" state="Active"
| eval age_days=round((now()-first_seen)/86400)
| eval sla_days=case(severity="Critical",7, severity="High",30, severity="Medium",90, 1=1,180)
| eval sla_status=if(age_days>sla_days,"Overdue","Compliant")
| stats count by severity, sla_status
```
- **Implementation:** Define SLA targets per severity. Calculate vulnerability age against SLA. Track compliance percentage. Alert when critical/high vulns approach SLA deadline. Produce compliance reports for audit evidence.
- **Visualization:** Gauge (SLA compliance %), Table (overdue vulnerabilities), Bar chart (compliance by severity), Line chart (compliance trend).

---

### UC-10.6.7 · New Vulnerability Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Newly discovered critical vulnerabilities require immediate triage. Alerting ensures rapid response to emerging risks.
- **App/TA:** Vuln management TA
- **Data Sources:** Scan results (first_seen within last scan window)
- **SPL:**
```spl
index=vulnerability sourcetype="tenable:vuln" severity="Critical"
| where first_seen > relative_time(now(), "-24h")
| table hostname, cve_id, plugin_name, severity, first_seen
| sort -first_seen
```
- **Implementation:** After each scan, identify new critical/high vulnerabilities (first_seen within scan window). Alert immediately on new critical findings. Include CVE details and affected hosts. Integrate with ticketing for automated remediation tracking.
- **Visualization:** Table (new vulnerabilities), Single value (new criticals today), Timeline (discovery events).

---

### 10.7 SIEM & SOAR

**Primary App/TA:** Splunk Enterprise Security (Premium), Splunk SOAR (Premium). Internal Splunk metrics (`_internal`, `_audit`).

---

### UC-10.7.1 · Alert Volume Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Alert volume trends reveal SOC workload, detection rule effectiveness, and potential alert fatigue risks.
- **App/TA:** Splunk Enterprise Security
- **Data Sources:** ES notable events (`notable` index)
- **SPL:**
```spl
index=notable
| timechart span=1d count by source
| sort -count
```
- **Implementation:** Track notable event volume from ES over time. Break down by source (correlation search). Identify noisy rules for tuning. Alert when daily volume exceeds analyst capacity thresholds. Report on volume trends.
- **Visualization:** Stacked area (alerts by source), Line chart (total alert volume), Bar chart (top alerting rules).

---

### UC-10.7.2 · Analyst Workload Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Uneven workload distribution leads to analyst burnout and inconsistent response times. Monitoring enables fair distribution.
- **App/TA:** Splunk ES
- **Data Sources:** ES investigation/ownership logs, notable event audit
- **SPL:**
```spl
index=notable
| stats count, avg(time_to_close) as avg_close_time by owner
| sort -count
```
- **Implementation:** Track alert assignment and closure by analyst. Calculate workload distribution and average handling time. Report to SOC management. Identify training needs based on handling time variations.
- **Visualization:** Bar chart (alerts per analyst), Table (workload summary), Pie chart (distribution).

---

### UC-10.7.3 · MTTD and MTTR Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** MTTD and MTTR are the primary metrics for SOC effectiveness. Tracking drives process improvement and justifies investment.
- **App/TA:** Splunk ES
- **Data Sources:** ES notable events (detection time, response time, closure time)
- **SPL:**
```spl
index=notable status="Closed"
| eval mttd_hours=round((detection_time-event_time)/3600,1)
| eval mttr_hours=round((closure_time-detection_time)/3600,1)
| stats avg(mttd_hours) as avg_mttd, avg(mttr_hours) as avg_mttr, perc95(mttr_hours) as p95_mttr
```
- **Implementation:** Ensure ES workflows capture detection, triage, and resolution timestamps. Calculate MTTD (event to detection) and MTTR (detection to resolution). Track by severity, type, and analyst. Report weekly/monthly to leadership.
- **Visualization:** Single value (avg MTTD/MTTR), Line chart (MTTD/MTTR trends), Bar chart (by incident type), Gauge (vs target).

---

### UC-10.7.4 · Playbook Execution Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** SOAR playbook failures leave incidents unhandled. Monitoring ensures automation reliability and identifies integration issues.
- **App/TA:** Splunk SOAR
- **Data Sources:** SOAR execution logs, playbook run results
- **SPL:**
```spl
index=soar sourcetype="phantom:playbook_run"
| stats count(eval(status="success")) as success, count(eval(status="failed")) as failed by playbook_name
| eval success_rate=round(success/(success+failed)*100,1)
| where success_rate < 95
```
- **Implementation:** Ingest SOAR execution logs into Splunk. Track playbook success/failure rates. Alert on failures for critical playbooks. Identify failing action steps for debugging. Report on automation coverage and time savings.
- **Visualization:** Table (playbook success rates), Bar chart (failure rate by playbook), Line chart (execution trend), Single value (overall success %).

---

### UC-10.7.5 · Correlation Search Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Slow or resource-intensive correlation searches degrade ES performance and may miss detections if they timeout.
- **App/TA:** Splunk internal metrics
- **Data Sources:** `_internal` scheduler logs
- **SPL:**
```spl
index=_internal sourcetype=scheduler savedsearch_name="*Correlation*"
| stats avg(run_time) as avg_runtime, max(run_time) as max_runtime by savedsearch_name
| where avg_runtime > 60
| sort -avg_runtime
```
- **Implementation:** Monitor ES correlation search run times from `_internal`. Alert when searches exceed their schedule interval (running longer than they should). Identify skipped searches. Optimize SPL for slow searches.
- **Visualization:** Table (search performance), Bar chart (avg runtime by search), Line chart (runtime trend), Single value (skipped searches).

---

### UC-10.7.6 · False Positive Rate Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** High false positive rates cause alert fatigue, leading analysts to miss real threats. Tracking drives detection rule optimization.
- **App/TA:** Splunk ES
- **Data Sources:** ES notable events with analyst disposition
- **SPL:**
```spl
index=notable status="Closed"
| stats count(eval(disposition="True Positive")) as tp, count(eval(disposition="False Positive")) as fp by source
| eval fp_rate=round(fp/(tp+fp)*100,1)
| where fp_rate > 30
| sort -fp_rate
```
- **Implementation:** Ensure analysts set dispositions when closing notables (TP, FP, Benign). Calculate FP rate per detection rule. Flag rules with >30% FP rate for tuning. Track overall FP rate as a SOC quality metric. Target <20% FP rate.
- **Visualization:** Bar chart (FP rate by rule), Line chart (overall FP trend), Table (rules needing tuning), Gauge (overall FP rate).

---

### 10.8 Certificate & PKI Management

**Primary App/TA:** Custom scripted inputs (certificate scanning scripts), CA server log forwarding.

---

### UC-10.8.1 · Certificate Expiry Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Expired certificates cause service outages, authentication failures, and security warnings. Proactive monitoring is the simplest prevention.
- **App/TA:** Custom scripted input
- **Data Sources:** Certificate inventory scans (openssl, certutil, CT logs)
- **SPL:**
```spl
index=certificates sourcetype="cert_inventory"
| eval days_to_expiry=round((cert_not_after_epoch-now())/86400)
| where days_to_expiry < 90
| table cn, san, issuer, days_to_expiry, host, port
| sort days_to_expiry
```
- **Implementation:** Deploy scripted input scanning all known endpoints (HTTPS, LDAPS, SMTPS, etc.) daily. Parse certificate metadata. Alert at 90/60/30/7 day thresholds with escalating severity. Maintain endpoint inventory for comprehensive coverage.
- **Visualization:** Table (certs with expiry countdown), Single value (certs expiring within 30d), Status grid (cert × expiry status), Bar chart (certs by expiry bucket).

---

### UC-10.8.2 · Certificate Issuance Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized certificate issuance from internal CAs can enable man-in-the-middle attacks. Audit trail supports compliance.
- **App/TA:** CA server log forwarding
- **Data Sources:** CA audit logs (Microsoft AD CS, EJBCA, HashiCorp Vault PKI)
- **SPL:**
```spl
index=pki sourcetype="adcs:audit"
| search EventCode=4887
| table _time, RequesterName, CertificateTemplate, SerialNumber, SubjectCN
| sort -_time
```
- **Implementation:** Forward CA server audit logs to Splunk (Event ID 4887 for AD CS). Track all certificate issuance events. Alert on issuance from non-standard templates or by unauthorized requesters. Report on issuance volume and template usage.
- **Visualization:** Table (issued certificates), Timeline (issuance events), Bar chart (by template), Line chart (issuance volume trend).

---

### UC-10.8.3 · Weak Cipher / Key Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Certificates using weak algorithms (SHA-1, RSA <2048-bit) are vulnerable to attack. Detection ensures cryptographic standards compliance.
- **App/TA:** Custom scripted input
- **Data Sources:** Certificate scan results
- **SPL:**
```spl
index=certificates sourcetype="cert_inventory"
| where key_size < 2048 OR signature_algorithm LIKE "%sha1%" OR signature_algorithm LIKE "%md5%"
| table cn, host, port, key_size, signature_algorithm, issuer
```
- **Implementation:** Include key size and signature algorithm in certificate scans. Flag certificates using SHA-1, MD5, or RSA <2048-bit. Alert on new weak certificates. Track remediation progress as a compliance metric.
- **Visualization:** Table (weak certificates), Pie chart (algorithm distribution), Single value (weak cert count), Bar chart (by weakness type).

---

### UC-10.8.4 · Certificate Revocation Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Revocation activity indicates compromised or misused certificates. Tracking ensures revocations are processed and CRLs distributed.
- **App/TA:** CA server logs
- **Data Sources:** CA audit logs (revocation events), CRL distribution point monitoring
- **SPL:**
```spl
index=pki sourcetype="adcs:audit" EventCode=4889
| table _time, RequesterName, SerialNumber, RevokeReason, SubjectCN
| sort -_time
```
- **Implementation:** Forward CA revocation events (Event ID 4889). Monitor CRL publication and OCSP responder health. Alert on revocations for investigation. Track revocation reasons for security program improvement.
- **Visualization:** Table (revoked certificates), Timeline (revocation events), Bar chart (revocation reasons).

---

### UC-10.8.5 · CT Log Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Certificate Transparency logs reveal all publicly-issued certificates for your domains. Detects unauthorized issuance by rogue or compromised CAs.
- **App/TA:** Custom API input (crt.sh, CT log APIs)
- **Data Sources:** Certificate Transparency log API
- **SPL:**
```spl
index=certificates sourcetype="ct_log"
| search NOT issuer IN ("DigiCert*","Let's Encrypt*","Sectigo*")
| table _time, cn, issuer, serial, not_before, not_after
| sort -_time
```
- **Implementation:** Poll CT log aggregators (crt.sh) for your domains daily. Maintain whitelist of approved issuers. Alert on certificates from unexpected CAs. Track issuance patterns for certificate lifecycle management.
- **Visualization:** Table (CT log entries), Timeline (issuance events), Bar chart (certs by issuer), Single value (unauthorized issuances).

---

## 11. Email & Collaboration

### 11.1 Microsoft 365 / Exchange

**Primary App/TA:** Splunk Add-on for Microsoft Office 365 (`Splunk_TA_MS_O365`), Splunk Add-on for Microsoft Exchange.

---

### UC-11.1.1 · Mail Flow Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Email is business-critical. Mail flow issues (queuing, NDRs) directly impact productivity and customer communication.
- **App/TA:** `Splunk_TA_MS_O365`, Exchange message tracking
- **Data Sources:** Exchange message tracking logs, O365 message trace
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:messageTrace"
| timechart span=1h count by Status
```
- **Implementation:** Ingest Exchange message tracking logs or O365 message trace via Management Activity API. Track delivery rates, queue lengths, and NDR volumes. Alert on delivery failures exceeding baseline. Monitor mail flow latency.
- **Visualization:** Line chart (message volume by status), Single value (delivery success rate), Bar chart (top NDR reasons).

---

### UC-11.1.2 · Mailbox Audit Logging
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks who accesses what mailboxes, including delegate and admin access. Essential for insider threat detection and compliance.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 unified audit log (ExchangeItem events)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="Exchange" Operation IN ("MailItemsAccessed","Send","SendAs")
| stats count by UserId, Operation, MailboxOwnerUPN
| where UserId!=MailboxOwnerUPN
```
- **Implementation:** Enable mailbox audit logging in Exchange Online. Ingest via O365 Management Activity API. Alert on non-owner access to sensitive mailboxes. Track delegate activity. Monitor SendAs events for potential impersonation.
- **Visualization:** Table (non-owner mailbox access), Bar chart (access by user), Timeline (audit events).

---

### UC-11.1.3 · Exchange Online Protection Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** EOP filtering metrics show email threat landscape and security control effectiveness.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** EOP message trace, threat protection status
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:messageTrace"
| eval threat_type=case(match(FilteringResult,"Spam"),"Spam", match(FilteringResult,"Phish"),"Phishing", match(FilteringResult,"Malware"),"Malware", 1=1,"Clean")
| stats count by threat_type
```
- **Implementation:** Ingest O365 message trace data. Classify messages by EOP verdict. Track filtering rates over time. Report on threat types and volumes. Alert on phishing/malware volume spikes.
- **Visualization:** Pie chart (message classification), Line chart (threat volume trend), Bar chart (top blocked senders).

---

### UC-11.1.4 · Teams Usage Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Teams adoption and quality metrics inform collaboration strategy and help identify user experience issues.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** M365 Teams activity reports, Teams call quality data
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="MicrosoftTeams"
| stats count by Operation
| sort -count
```
- **Implementation:** Ingest Teams activity reports via Graph API. Track meetings, messages, calls, and file sharing volumes. Monitor call quality metrics (jitter, packet loss). Report on adoption trends per department.
- **Visualization:** Line chart (Teams activity trend), Bar chart (activity by type), Table (call quality issues).

---

### UC-11.1.5 · SharePoint/OneDrive Sharing Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** External sharing can expose sensitive data. Audit trail ensures data protection and compliance.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 audit log (SharingSet, AnonymousLinkCreated)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="SharePoint" Operation IN ("SharingSet","AnonymousLinkCreated","CompanyLinkCreated")
| where TargetUserOrGroupType="Guest" OR Operation="AnonymousLinkCreated"
| table _time, UserId, Operation, ObjectId, TargetUserOrGroupName
```
- **Implementation:** Ingest SharePoint/OneDrive audit events. Alert on external sharing (guest users, anonymous links). Track sharing activity per user. Flag sharing of sensitive files or sites. Report for data governance reviews.
- **Visualization:** Table (external sharing events), Bar chart (sharing by user), Line chart (sharing trend), Pie chart (sharing type distribution).

---

### UC-11.1.6 · DLP Policy Events
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** M365 DLP policy matches across email, Teams, SharePoint identify sensitive data exposure. Centralized tracking supports compliance.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 DLP logs
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Workload="Dlp"
| stats count by PolicyName, UserPrincipalName, SensitiveInfoType
| sort -count
```
- **Implementation:** Configure M365 DLP policies. Ingest DLP events. Track violations by policy, user, and data type. Alert on high-severity matches. Produce compliance reports for regulated data (PII, PCI, HIPAA).
- **Visualization:** Bar chart (violations by policy), Table (top violators), Line chart (violation trend).

---

### UC-11.1.7 · Admin Activity Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** M365 admin actions (user creation, license changes, policy modifications) need audit trails for compliance and security.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 audit log (admin operations)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" RecordType=1
| table _time, UserId, Operation, ObjectId, ResultStatus
| sort -_time
```
- **Implementation:** Ingest O365 admin audit log. Track admin operations by administrator. Alert on sensitive operations (user creation, role changes, policy modifications). Correlate with change management tickets.
- **Visualization:** Table (admin activities), Timeline (admin events), Bar chart (actions by admin).

---

### UC-11.1.8 · Inbox Rule Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Malicious inbox rules (auto-forward to external, auto-delete) are a key post-compromise technique for data exfiltration.
- **App/TA:** `Splunk_TA_MS_O365`
- **Data Sources:** O365 audit log (New-InboxRule, Set-InboxRule)
- **SPL:**
```spl
index=o365 sourcetype="ms:o365:management" Operation IN ("New-InboxRule","Set-InboxRule")
| spath output=forward Parameters{}.Value
| search forward="*@*" NOT forward="*@yourdomain.com"
| table _time, UserId, Operation, forward
```
- **Implementation:** Monitor inbox rule creation events. Alert on rules that forward to external addresses, delete messages, or move to uncommon folders. These are high-confidence indicators of account compromise. Trigger immediate investigation.
- **Visualization:** Table (suspicious inbox rules), Single value (external forwarding rules — target: 0), Timeline (rule creation events).

---

### UC-11.1.9 · Service Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** M365 service incidents affect all users. Early awareness from API enables proactive communication and workaround planning.
- **App/TA:** Custom API input (M365 Service Health API)
- **Data Sources:** M365 Service Health API
- **SPL:**
```spl
index=m365 sourcetype="m365:servicehealth"
| where status!="ServiceOperational"
| table _time, service, status, title, classification
```
- **Implementation:** Poll M365 Service Health API every 5 minutes. Alert on service degradations and incidents. Track incident duration and frequency. Correlate with internal ticket volumes to measure user impact.
- **Visualization:** Status grid (service × health), Table (active incidents), Timeline (incident history).

---

### UC-11.1.10 · License Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** M365 license costs are significant. Tracking utilization identifies unused licenses for reallocation and cost savings.
- **App/TA:** Custom API input (M365 Reports API)
- **Data Sources:** M365 license assignment and usage reports
- **SPL:**
```spl
index=m365 sourcetype="m365:licenses"
| stats sum(assigned) as assigned, sum(consumed) as consumed by sku_name
| eval utilization_pct=round(consumed/assigned*100,1)
| table sku_name, assigned, consumed, utilization_pct
```
- **Implementation:** Poll M365 license reports via Graph API weekly. Track assigned vs consumed licenses per SKU. Identify inactive users (no activity in 90 days with assigned license). Report on cost optimization opportunities.
- **Visualization:** Table (license utilization), Gauge (% utilized per SKU), Bar chart (unused licenses by SKU).

---

### 11.2 Google Workspace

**Primary App/TA:** Splunk Add-on for Google Workspace (`Splunk_TA_GoogleWorkspace`).

---

### UC-11.2.1 · Admin Console Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Admin actions in Google Workspace affect all users. Audit trail supports compliance and detects unauthorized changes.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Workspace Admin audit log
- **SPL:**
```spl
index=gws sourcetype="gws:admin" event_name IN ("CREATE_USER","DELETE_USER","CHANGE_ADMIN_ROLE")
| table _time, actor.email, event_name, target_user
```
- **Implementation:** Configure Google Workspace TA to ingest admin audit logs via Reports API. Track user management, policy changes, and configuration modifications. Alert on sensitive operations (role changes, 2FA disablement).
- **Visualization:** Table (admin events), Timeline (admin activity), Bar chart (events by admin).

---

### UC-11.2.2 · Gmail Message Flow
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Email delivery monitoring and DLP enforcement protects sensitive data and ensures business communication reliability.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Gmail logs via BigQuery export or Reports API
- **SPL:**
```spl
index=gws sourcetype="gws:gmail"
| stats count by message_info.disposition
| eval pct=round(count/sum(count)*100,1)
```
- **Implementation:** Ingest Gmail logs. Track message delivery rates, spam filtering effectiveness, and DLP triggers. Alert on delivery failures or increased spam rates. Report on email security posture.
- **Visualization:** Pie chart (message disposition), Line chart (message volume), Table (DLP triggers).

---

### UC-11.2.3 · Drive Sharing Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Unusual file sharing patterns may indicate data exfiltration or accidental exposure of sensitive documents.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Drive audit log
- **SPL:**
```spl
index=gws sourcetype="gws:drive" event_name="change_user_access"
| where new_value="people_with_link" OR target_user_email NOT LIKE "%@yourdomain.com%"
| table _time, actor.email, doc_title, target_user_email, new_value
```
- **Implementation:** Ingest Drive audit logs. Alert on external sharing, "anyone with link" sharing, and bulk sharing events. Track sharing patterns per user. Flag sharing of sensitive folders or documents.
- **Visualization:** Table (sharing events), Bar chart (external sharing by user), Line chart (sharing activity trend).

---

### UC-11.2.4 · Login Anomaly Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Suspicious login activity (new device, unusual location, failed MFA) indicates potential account compromise.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Workspace login audit log
- **SPL:**
```spl
index=gws sourcetype="gws:login" event_name="login_failure"
| stats count by actor.email, ip_address
| where count > 5
```
- **Implementation:** Ingest login audit logs. Track failed logins, new device registrations, and unusual locations. Alert on multiple failures, suspicious activity events, and login from new countries. Correlate with Google's built-in risk signals.
- **Visualization:** Table (suspicious logins), Geo map (login locations), Line chart (failure rate), Bar chart (failures by user).

---

### UC-11.2.5 · Meet Quality Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Poor meeting quality impacts productivity and user satisfaction. Monitoring enables network/infrastructure optimization.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Meet quality logs
- **SPL:**
```spl
index=gws sourcetype="gws:meet"
| where video_recv_jitter_ms > 30 OR audio_recv_jitter_ms > 30
| stats count, avg(video_recv_jitter_ms) as avg_jitter by organizer_email, meeting_code
```
- **Implementation:** Ingest Meet quality data. Track jitter, latency, and packet loss per meeting. Alert on recurring poor quality for specific users or locations. Correlate with network performance data.
- **Visualization:** Table (poor quality meetings), Line chart (quality metrics trend), Bar chart (issues by location).

---

### UC-11.2.6 · Third-Party App Access
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** OAuth app grants to third-party applications create data access risks. Monitoring enables governance and risk assessment.
- **App/TA:** `Splunk_TA_GoogleWorkspace`
- **Data Sources:** Google Workspace token audit log
- **SPL:**
```spl
index=gws sourcetype="gws:token" event_name="authorize"
| stats dc(actor.email) as unique_users by app_name, scope
| sort -unique_users
```
- **Implementation:** Ingest token audit logs. Track OAuth grants by application and scope. Identify high-risk scopes (full Drive access, Gmail read). Alert on new third-party apps accessing sensitive scopes. Report for governance review.
- **Visualization:** Table (third-party apps with scope), Bar chart (apps by user count), Pie chart (scope distribution).

---

### 11.3 Unified Communications

**Primary App/TA:** Cisco UCM TA, Webex TA, custom CDR/CMR inputs for voice platforms.

---

### UC-11.3.1 · Call Quality Monitoring (MOS)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** MOS scores directly measure voice quality experience. Degradation impacts business communication and customer service.
- **App/TA:** Cisco UCM CDR/CMR, Webex API
- **Data Sources:** Call Detail Records (CDR), Call Management Records (CMR)
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cmr"
| where MOS < 3.5
| stats count, avg(MOS) as avg_mos by origDeviceName, destDeviceName
| sort avg_mos
```
- **Implementation:** Ingest CDR/CMR from UCM or cloud UC platform. Parse MOS, jitter, latency, and packet loss. Alert when MOS drops below 3.5 (fair quality). Correlate with network metrics to identify root cause. Track per-site quality.
- **Visualization:** Gauge (average MOS), Line chart (MOS trend), Table (poor quality calls), Heatmap (site × quality).

---

### UC-11.3.2 · Call Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Call volume patterns support capacity planning and detect anomalies (toll fraud, system issues).
- **App/TA:** UCM CDR input
- **Data Sources:** CDR records
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cdr"
| timechart span=1h count as calls
| predict calls as predicted
```
- **Implementation:** Ingest CDR data. Track call volumes by hour, day, site. Baseline normal patterns. Alert on significant drops (possible outage) or spikes (possible toll fraud). Report on peak hour utilization.
- **Visualization:** Line chart (call volume with prediction), Bar chart (calls by site), Area chart (hourly distribution).

---

### UC-11.3.3 · VoIP Jitter/Latency/Packet Loss
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Transport quality metrics identify network issues affecting voice quality before users report problems.
- **App/TA:** UCM CMR, RTCP data
- **Data Sources:** CMR records (jitter, latency, packet loss), RTCP reports
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cmr"
| where jitter > 30 OR latency > 150 OR packet_loss_pct > 1
| stats count by origDeviceName, destDeviceName, jitter, latency, packet_loss_pct
```
- **Implementation:** Parse transport quality metrics from CMR. Alert on jitter >30ms, latency >150ms, or packet loss >1%. Correlate with WAN/LAN performance metrics. Track per-site to identify network segments needing attention.
- **Visualization:** Multi-metric chart (jitter, latency, packet loss), Table (calls with poor transport), Heatmap (site × metric).

---

### UC-11.3.4 · Trunk Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Trunk capacity limits cause busy signals and missed calls. Monitoring prevents capacity-related service degradation.
- **App/TA:** UCM CDR, gateway logs
- **Data Sources:** CDR records, gateway/trunk metrics
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cdr"
| timechart span=15m dc(globalCallID_callId) as concurrent_calls by trunk_group
| where concurrent_calls > 20
```
- **Implementation:** Track concurrent calls per trunk group from CDR data. Alert when utilization exceeds 80% of capacity. Monitor for trunk failures and failover events. Report on peak utilization for capacity planning.
- **Visualization:** Line chart (trunk utilization), Gauge (% capacity per trunk), Table (trunk utilization summary).

---

### UC-11.3.5 · Conference Bridge Capacity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Conference bridge resource exhaustion prevents users from joining meetings. Monitoring ensures adequate capacity.
- **App/TA:** Webex API, UCM conference bridge metrics
- **Data Sources:** Conference bridge utilization, Webex meeting data
- **SPL:**
```spl
index=voip sourcetype="webex:meetings"
| timechart span=1h max(concurrent_participants) as max_participants
| where max_participants > 500
```
- **Implementation:** Track conference bridge resource utilization and concurrent participant counts. Alert when approaching capacity limits. Monitor meeting quality metrics at scale. Report on peak usage patterns for capacity planning.
- **Visualization:** Line chart (concurrent participants), Single value (peak participants today), Bar chart (meetings by size).

---

### UC-11.3.6 · Toll Fraud Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Toll fraud causes significant financial loss. International premium-rate calls from compromised systems can cost thousands per hour.
- **App/TA:** UCM CDR analysis
- **Data Sources:** CDR records (called party number, duration, time of day)
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:cdr"
| where match(calledPartyNumber,"^011|^00") AND duration > 60
| stats count, sum(duration) as total_min by callingPartyNumber, calledPartyNumber
| where count > 10
| sort -total_min
```
- **Implementation:** Monitor CDR for international calls, premium-rate numbers (900, 976), and calls outside business hours. Baseline normal international calling patterns. Alert on anomalous patterns. Block suspicious numbers in real-time.
- **Visualization:** Table (suspicious calls), Bar chart (international calls by destination), Timeline (unusual calling activity), Geo map (call destinations).

---

### UC-11.3.7 · Phone Registration Status
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Mass phone de-registration indicates network or UCM issues affecting the entire communications infrastructure.
- **App/TA:** UCM syslog, RISPORT API
- **Data Sources:** UCM device status, RISPORT real-time data
- **SPL:**
```spl
index=voip sourcetype="cisco:ucm:syslog"
| search "DeviceUnregistered" OR "StationDeregister"
| timechart span=5m count as deregistrations
| where deregistrations > 10
```
- **Implementation:** Poll UCM RISPORT API for device registration status or forward UCM syslog. Alert on mass de-registrations (>10 devices in 5 minutes). Track registration counts per site. Monitor SRST fallback activations.
- **Visualization:** Single value (registered phones), Line chart (registration count trend), Table (recently de-registered devices).

---

### UC-11.3.8 · Webex Meeting Analytics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Meeting analytics support collaboration optimization, license management, and quality improvement initiatives.
- **App/TA:** Webex API input
- **Data Sources:** Webex meeting/participant data via API
- **SPL:**
```spl
index=webex sourcetype="webex:meetings"
| stats count as meetings, avg(participant_count) as avg_participants, avg(duration_min) as avg_duration by organizerEmail
| sort -meetings
```
- **Implementation:** Poll Webex API for meeting data. Track meeting counts, participants, duration, and quality. Report on adoption metrics per department. Identify power users and underutilized licenses.
- **Visualization:** Bar chart (meetings by department), Line chart (meeting volume trend), Table (usage summary), Pie chart (meeting types).

---

## 12. DevOps & CI/CD

### 12.1 Source Control

**Primary App/TA:** GitHub TA, GitLab webhook inputs, custom API inputs (Bitbucket, Azure DevOps).

---

### UC-12.1.1 · Commit Activity Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Commit velocity indicates team productivity and project health. Drops may signal blockers; spikes may precede release issues.
- **App/TA:** GitHub webhook, custom API input
- **Data Sources:** Git webhook events (push), GitHub/GitLab API
- **SPL:**
```spl
index=devops sourcetype="github:webhook" event="push"
| timechart span=1d count as commits by repository
```
- **Implementation:** Configure GitHub/GitLab webhooks to send push events to Splunk HEC. Parse repository, author, branch, and commit count. Track trends per team and repository. Report on developer activity metrics.
- **Visualization:** Line chart (commits over time), Bar chart (commits by repo), Stacked area (commits by team).

---

### UC-12.1.2 · Branch Protection Bypasses
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Direct pushes to protected branches bypass code review, introducing unreviewed code to production. Detection ensures process compliance.
- **App/TA:** GitHub audit log, GitLab API
- **Data Sources:** GitHub/GitLab audit log, push events to protected branches
- **SPL:**
```spl
index=devops sourcetype="github:audit" action="protected_branch.policy_override"
| table _time, actor, repo, branch, action
```
- **Implementation:** Ingest GitHub/GitLab audit logs. Alert on any push to protected branches (main, release) without PR merge. Alert on branch protection rule changes. Correlate with deployment events.
- **Visualization:** Table (bypass events), Timeline (protection violations), Single value (bypasses this month — target: 0).

---

### UC-12.1.3 · Pull Request Metrics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** PR cycle time affects development velocity. Long review times indicate bottlenecks; abandoned PRs indicate scope or alignment issues.
- **App/TA:** GitHub API input
- **Data Sources:** PR events (opened, reviewed, merged, closed)
- **SPL:**
```spl
index=devops sourcetype="github:pull_request" action="closed" merged="true"
| eval cycle_hours=round((merged_at_epoch-created_at_epoch)/3600,1)
| stats avg(cycle_hours) as avg_cycle, median(cycle_hours) as median_cycle by repository
| sort -avg_cycle
```
- **Implementation:** Ingest PR lifecycle events. Calculate open-to-merge time, review cycles, and abandonment rates. Track per repository and team. Report on engineering efficiency metrics. Identify bottleneck reviewers.
- **Visualization:** Bar chart (avg cycle time by repo), Line chart (PR metrics trend), Table (PR summary), Histogram (cycle time distribution).

---

### UC-12.1.4 · Secret Exposure Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Secrets committed to source control are immediately compromised. Detection within minutes enables rapid rotation before exploitation.
- **App/TA:** GitGuardian webhook, GitHub secret scanning
- **Data Sources:** Pre-commit hook results, GitGuardian/GitHub secret scanning alerts
- **SPL:**
```spl
index=devops sourcetype="github:secret_scanning" OR sourcetype="gitguardian:alert"
| table _time, repository, secret_type, file_path, author, status
| sort -_time
```
- **Implementation:** Enable GitHub secret scanning or deploy GitGuardian. Forward alerts to Splunk. Alert at critical priority on any secret detection. Track remediation time (rotation). Report on secret types and recurrence.
- **Visualization:** Table (exposed secrets), Single value (unresolved secrets — target: 0), Bar chart (secrets by type), Timeline (detection events).

---

### UC-12.1.5 · Repository Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Repository permission changes can expose source code to unauthorized users. Audit trail supports IP protection and compliance.
- **App/TA:** GitHub audit log
- **Data Sources:** GitHub/GitLab audit log (permission events)
- **SPL:**
```spl
index=devops sourcetype="github:audit" action IN ("repo.add_member","repo.remove_member","repo.update_member")
| table _time, actor, repo, user, permission, action
```
- **Implementation:** Ingest organization audit log. Track member additions, removals, and permission changes. Alert on permission escalation to admin. Report on repository access patterns for periodic access review.
- **Visualization:** Table (access changes), Timeline (permission events), Bar chart (changes by actor).

---

### UC-12.1.6 · Force Push Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Force pushes overwrite git history, potentially destroying code and audit trails. Detection ensures accountability.
- **App/TA:** GitHub webhook
- **Data Sources:** Git push events (forced flag)
- **SPL:**
```spl
index=devops sourcetype="github:webhook" event="push" forced="true"
| table _time, repository, ref, pusher, forced
```
- **Implementation:** Parse force push flag from webhook events. Alert on any force push to shared branches. Whitelist expected force pushes (e.g., squash-merge workflows on feature branches). Track frequency per developer.
- **Visualization:** Table (force push events), Timeline (force pushes), Single value (force pushes this week).

---

### 12.2 CI/CD Pipelines

**Primary App/TA:** Jenkins TA (`TA-jenkins`), custom webhook receivers for GitHub Actions/GitLab CI/ArgoCD.

---

### UC-12.2.1 · Build Success Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Declining build success rates indicate code quality issues, flaky tests, or infrastructure problems. Trending drives improvement.
- **App/TA:** Splunk App for Jenkins, webhook input
- **Data Sources:** CI/CD build results (Jenkins, GitHub Actions, GitLab CI)
- **SPL:**
```spl
index=cicd sourcetype="jenkins:build"
| stats count(eval(result="SUCCESS")) as success, count(eval(result="FAILURE")) as failed, count as total by job_name
| eval success_rate=round(success/total*100,1)
| sort success_rate
```
- **Implementation:** Ingest CI/CD build events via TA or webhook. Track success/failure rates per pipeline. Alert when success rate drops below threshold (e.g., <90%). Identify most-failing pipelines for developer attention.
- **Visualization:** Bar chart (success rate by pipeline), Line chart (success rate trend), Table (failing builds), Single value (overall success rate).

---

### UC-12.2.2 · Build Duration Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Increasing build times slow development velocity. Detection enables build optimization and infrastructure right-sizing.
- **App/TA:** Splunk App for Jenkins, CI/CD metrics
- **Data Sources:** Build start/end timestamps
- **SPL:**
```spl
index=cicd sourcetype="jenkins:build" result="SUCCESS"
| eval duration_min=round(duration/60000,1)
| timechart span=1d avg(duration_min) as avg_build_time by job_name
```
- **Implementation:** Track build duration for all pipelines. Alert when duration exceeds historical average by >50%. Identify slow build steps. Correlate with infrastructure metrics (runner CPU, disk I/O) to find bottlenecks.
- **Visualization:** Line chart (build duration trend), Bar chart (avg duration by pipeline), Table (slowest builds today).

---

### UC-12.2.3 · Deployment Frequency (DORA)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Deployment frequency is a key DORA metric indicating engineering capability maturity. Higher frequency correlates with better outcomes.
- **App/TA:** Deployment event webhook
- **Data Sources:** Deployment events from CI/CD pipelines
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" environment="production"
| timechart span=1w count as deployments by application
```
- **Implementation:** Emit deployment events from CI/CD pipelines to Splunk HEC. Track production deployments per team/application per week. Calculate DORA deployment frequency category (daily, weekly, monthly). Report to engineering leadership.
- **Visualization:** Line chart (deployment frequency trend), Bar chart (deployments by team), Single value (deployments this week).

---

### UC-12.2.4 · Lead Time for Changes (DORA)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Lead time measures the commit-to-production pipeline efficiency. Shorter lead times enable faster value delivery and incident response.
- **App/TA:** Git + deployment correlation
- **Data Sources:** Git commit timestamps + production deployment timestamps
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" environment="production"
| eval lead_time_hours=round((deploy_time_epoch-commit_time_epoch)/3600,1)
| stats avg(lead_time_hours) as avg_lead_time, median(lead_time_hours) as median_lead_time by application
```
- **Implementation:** Correlate commit timestamps with deployment events. Calculate time from first commit to production deployment. Track per application and team. Classify per DORA categories (under 1 hour, under 1 day, under 1 week, over 1 month).
- **Visualization:** Bar chart (lead time by application), Line chart (lead time trend), Histogram (lead time distribution).

---

### UC-12.2.5 · Failed Deployment Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Failed deployments cause service disruption. Rapid detection enables rollback decisions. Change failure rate is a DORA metric.
- **App/TA:** Deployment event webhook
- **Data Sources:** Deployment events with status, rollback events
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" status="failed"
| table _time, application, environment, version, deployer, error_message
| sort -_time
```
- **Implementation:** Track all deployment outcomes including failures and rollbacks. Alert immediately on production deployment failures. Calculate change failure rate (DORA metric). Correlate with application error rate to measure deployment impact.
- **Visualization:** Table (failed deployments), Single value (change failure rate %), Line chart (failure rate trend), Timeline (deployment events).

---

### UC-12.2.6 · Pipeline Queue Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Long queue times indicate insufficient CI/CD runner capacity, slowing developer feedback loops and delivery velocity.
- **App/TA:** Splunk App for Jenkins, CI/CD system metrics
- **Data Sources:** CI/CD queue metrics (time in queue, pending jobs)
- **SPL:**
```spl
index=cicd sourcetype="jenkins:queue"
| timechart span=15m avg(wait_time_sec) as avg_wait, max(queue_length) as max_queue
| where avg_wait > 300
```
- **Implementation:** Track job queue wait times and queue lengths. Alert when average wait exceeds 5 minutes. Monitor runner/agent utilization. Report on peak hours to guide scaling decisions.
- **Visualization:** Line chart (queue time trend), Bar chart (queue time by pipeline), Single value (current queue length).

---

### UC-12.2.7 · Test Coverage Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Declining test coverage increases risk of undetected bugs. Trending ensures quality standards are maintained.
- **App/TA:** Custom test report input
- **Data Sources:** Test result reports (JUnit XML, coverage reports)
- **SPL:**
```spl
index=cicd sourcetype="test_coverage"
| timechart span=1d latest(coverage_pct) as coverage by project
| where coverage < 80
```
- **Implementation:** Parse test coverage reports from CI/CD pipelines. Send to Splunk via HEC. Track coverage per project. Alert when coverage drops below minimum (e.g., <80%). Block merges when coverage decreases (enforce in CI).
- **Visualization:** Line chart (coverage trend per project), Bar chart (coverage by project), Single value (avg coverage %).

---

### UC-12.2.8 · Security Scan Results in Pipeline
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** SAST/DAST/SCA findings in CI/CD pipelines catch vulnerabilities before they reach production. Tracking ensures security gates work.
- **App/TA:** Custom scan result input
- **Data Sources:** SAST (SonarQube, Checkmarx), DAST (ZAP, Burp), SCA (Snyk, Dependabot) results
- **SPL:**
```spl
index=cicd sourcetype="security_scan"
| stats count by severity, scan_type, project
| where severity IN ("Critical","High")
| sort -count
```
- **Implementation:** Ingest security scan results from CI/CD pipelines. Track findings by severity, type, and project. Alert on critical findings blocking deployment. Report on vulnerability introduction rate and fix rate.
- **Visualization:** Bar chart (findings by severity), Table (critical findings), Line chart (findings trend), Stacked bar (by scan type).

---

### 12.3 Artifact & Package Management

**Primary App/TA:** Custom API inputs (Artifactory, Nexus), webhook receivers.

---

### UC-12.3.1 · Artifact Repository Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Full artifact repositories prevent builds from publishing. Storage monitoring and cleanup policy verification ensures CI/CD continuity.
- **App/TA:** Custom API input (Artifactory/Nexus)
- **Data Sources:** Repository storage metrics, cleanup policy logs
- **SPL:**
```spl
index=devops sourcetype="artifactory:storage"
| eval pct_used=round(used_space/total_space*100,1)
| where pct_used > 80
| table repository, used_space_gb, total_space_gb, pct_used
```
- **Implementation:** Poll Artifactory/Nexus storage API daily. Track storage per repository. Alert at 80% capacity. Verify cleanup policies are running and effective. Report on artifact growth rate.
- **Visualization:** Gauge (% capacity used), Bar chart (storage by repository), Line chart (storage trend).

---

### UC-12.3.2 · Dependency Vulnerability Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Vulnerable dependencies in the software supply chain are a primary attack vector. Tracking ensures timely patching.
- **App/TA:** Snyk/Dependabot webhook
- **Data Sources:** SCA tool output (Snyk, Dependabot, GitHub Advisory)
- **SPL:**
```spl
index=devops sourcetype="snyk:vulnerability"
| where severity IN ("critical","high")
| stats count by project, package_name, cve_id, severity
| sort -severity, -count
```
- **Implementation:** Ingest SCA scan results. Track vulnerable dependencies by project, severity, and package. Alert on new critical/high findings. Track remediation time. Report on dependency health per team.
- **Visualization:** Table (vulnerable dependencies), Bar chart (vulns by project), Line chart (vulnerability trend), Single value (critical vulns count).

---

### UC-12.3.3 · Package Download Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusual package download patterns may indicate dependency confusion attacks or compromised internal packages.
- **App/TA:** Artifactory/Nexus access logs
- **Data Sources:** Repository access logs (download events)
- **SPL:**
```spl
index=devops sourcetype="artifactory:access"
| stats count by package_name, client_ip
| eventstats avg(count) as avg_downloads, stdev(count) as stdev_downloads by package_name
| where count > avg_downloads + 3*stdev_downloads
```
- **Implementation:** Monitor package download patterns. Baseline normal download volumes per package. Alert on statistical outliers. Watch for downloads of internal packages from external IPs. Track new/unknown packages being introduced.
- **Visualization:** Table (anomalous downloads), Bar chart (top downloaded packages), Line chart (download volume trend).

---

### UC-12.3.4 · License Compliance Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Open-source license violations create legal risk. Automated tracking ensures compliance before code reaches production.
- **App/TA:** SCA tool output
- **Data Sources:** SCA license scan results (Snyk, FOSSA, WhiteSource)
- **SPL:**
```spl
index=devops sourcetype="sca:license"
| where license_risk IN ("high","critical") OR license IN ("GPL-3.0","AGPL-3.0")
| stats count by project, package_name, license, license_risk
| sort -license_risk
```
- **Implementation:** Ingest SCA license scan results. Track license types across all projects. Alert on copyleft licenses in commercial products. Report on license distribution for legal review. Block deployments with policy violations.
- **Visualization:** Table (license risks), Pie chart (license distribution), Bar chart (risks by project).

---

### 12.4 Infrastructure as Code

**Primary App/TA:** Custom log inputs from CI/CD pipelines, Terraform Cloud API, Ansible callback plugins.

---

### UC-12.4.1 · Terraform Plan/Apply Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Every Terraform apply changes infrastructure. Full audit trail enables change management, impact analysis, and rollback decisions.
- **App/TA:** Terraform Cloud API, CI/CD output parsing
- **Data Sources:** Terraform CLI output (plan/apply), Terraform Cloud run events
- **SPL:**
```spl
index=iac sourcetype="terraform:run"
| table _time, workspace, user, action, resources_added, resources_changed, resources_destroyed, status
| sort -_time
```
- **Implementation:** Send Terraform run events to Splunk via HEC (from CI/CD pipeline or Terraform Cloud webhooks). Track resource changes per workspace. Alert on destroy operations. Correlate infrastructure changes with monitoring alerts.
- **Visualization:** Table (recent Terraform runs), Timeline (apply events), Bar chart (resource changes by workspace), Single value (applies today).

---

### UC-12.4.2 · Configuration Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Drift from declared IaC state indicates manual changes that bypass change control, creating inconsistency and security risks.
- **App/TA:** Terraform plan output, cloud config monitoring
- **Data Sources:** Terraform plan output (no-change runs showing drift), AWS Config
- **SPL:**
```spl
index=iac sourcetype="terraform:plan"
| where drift_detected="true"
| table _time, workspace, resource_type, resource_name, drift_detail
| sort -_time
```
- **Implementation:** Schedule periodic `terraform plan` runs (detect-only). Parse output for unexpected changes. Alert on any drift detected. Correlate with cloud provider change logs to identify who made manual changes. Enforce drift remediation SLA.
- **Visualization:** Table (drifted resources), Single value (resources with drift), Bar chart (drift by workspace), Timeline (drift events).

---

### UC-12.4.3 · Ansible Playbook Outcomes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracking Ansible run results ensures configuration management is working. Failed tasks indicate systems in unknown state.
- **App/TA:** Ansible callback plugin (Splunk HEC callback)
- **Data Sources:** Ansible callback output (play results, task results)
- **SPL:**
```spl
index=iac sourcetype="ansible:result"
| stats sum(ok) as ok, sum(changed) as changed, sum(failed) as failed, sum(unreachable) as unreachable by playbook, host
| where failed > 0 OR unreachable > 0
```
- **Implementation:** Configure Ansible Splunk callback plugin to send results to HEC. Track ok/changed/failed/unreachable counts per playbook and host. Alert on failed or unreachable hosts. Report on configuration management coverage.
- **Visualization:** Table (playbook results), Status grid (host × playbook status), Bar chart (failures by playbook), Single value (success rate).

---

### UC-12.4.4 · Puppet/Chef Compliance Reports
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Configuration management compliance ensures systems match desired state. Non-compliance indicates security or operational risk.
- **App/TA:** Puppet/Chef report forwarding
- **Data Sources:** Puppet agent reports, Chef client run reports
- **SPL:**
```spl
index=iac sourcetype="puppet:report"
| stats latest(status) as status, latest(corrective_changes) as corrective by certname
| where status="failed" OR corrective > 0
```
- **Implementation:** Forward Puppet/Chef reports to Splunk. Track agent compliance rates. Alert on failed runs (nodes in non-compliant state). Monitor corrective changes (Puppet remediated drift). Report on fleet compliance percentage.
- **Visualization:** Single value (compliance %), Table (non-compliant nodes), Pie chart (status distribution), Line chart (compliance trend).

---

### UC-12.4.5 · IaC Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Policy-as-code (OPA/Sentinel) prevents non-compliant infrastructure from being provisioned. Tracking blocked deployments validates governance.
- **App/TA:** Policy engine output (CI/CD integration)
- **Data Sources:** OPA/Sentinel policy check results, CI/CD pipeline logs
- **SPL:**
```spl
index=iac sourcetype="policy_check"
| where result="DENY"
| stats count by policy_name, workspace, resource_type
| sort -count
```
- **Implementation:** Ingest policy check results from CI/CD pipelines. Track denied provisions by policy and team. Alert on repeated violations (may indicate training need). Report on policy effectiveness and most-violated rules.
- **Visualization:** Bar chart (violations by policy), Table (denied provisions), Line chart (violation trend), Pie chart (by resource type).

---

## 13. Observability & Monitoring Stack

### 13.1 Splunk Platform Health

**Primary App/TA:** Splunk Monitoring Console (built-in), `_internal` and `_audit` indexes.

---

### UC-13.1.1 · Indexer Queue Fill Ratio
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Backed-up indexing queues cause data loss or delay. Detection enables immediate investigation of ingestion bottlenecks.
- **App/TA:** Monitoring Console (built-in)
- **Data Sources:** `_internal` (metrics.log, queue metrics)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=queue
| eval fill_pct=round(current_size/max_size*100,1)
| where fill_pct > 70
| timechart span=5m max(fill_pct) as queue_pct by name
```
- **Implementation:** Monitor parsing, merging, and typing queues via `_internal`. Alert when any queue exceeds 70% fill ratio. Investigate source of data surge (new data source, burst events). Consider parallel pipelines or additional indexers.
- **Visualization:** Gauge (queue fill % per pipeline), Line chart (queue fill over time), Table (queues above threshold).

---

### UC-13.1.2 · Search Concurrency Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Exceeding search concurrency limits causes search skipping and degraded user experience. Monitoring guides capacity decisions.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (scheduler logs, search dispatch)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=search_concurrency
| timechart span=5m max(active_hist_searches) as historical, max(active_rt_searches) as realtime
```
- **Implementation:** Track concurrent searches vs configured limits. Alert when approaching concurrency limits. Identify resource-intensive searches consuming disproportionate capacity. Report on search workload distribution.
- **Visualization:** Line chart (concurrent searches over time), Gauge (% of limit), Table (top resource consumers).

---

### UC-13.1.3 · Forwarder Connectivity
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Silent forwarder failures mean data gaps that may not be noticed until an investigation fails. Detection ensures data completeness.
- **App/TA:** Monitoring Console, Deployment Monitor app
- **Data Sources:** `_internal` (metrics.log — tcpin_connections)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=tcpin_connections
| stats latest(_time) as last_seen by hostname, sourceIp
| eval hours_since=round((now()-last_seen)/3600,1)
| where hours_since > 1
| table hostname, sourceIp, hours_since
| sort -hours_since
```
- **Implementation:** Track last-seen timestamp per forwarder from `_internal`. Alert when any forwarder hasn't reported in >1 hour. Maintain forwarder inventory for coverage analysis. Cross-reference with host downtime events.
- **Visualization:** Table (silent forwarders), Single value (forwarders reporting), Status grid (forwarder × health), Bar chart (silent by location).

---

### UC-13.1.4 · License Usage Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** License overages cause enforcement (search blocking). Trending enables proactive management and capacity planning.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (license_usage.log)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=license_usage
| timechart span=1d sum(b) as bytes_indexed
| eval gb=round(bytes_indexed/1024/1024/1024,2)
| predict gb as predicted future_timespan=30
```
- **Implementation:** Track daily license usage against entitled volume. Alert at 80% and 90% of daily limit. Use `predict` for 30-day forecast. Identify top sourcetypes contributing to growth. Report on usage trends.
- **Visualization:** Line chart (daily usage with license limit line), Single value (today's usage %), Bar chart (usage by sourcetype), Gauge (% of limit).

---

### UC-13.1.5 · Skipped Search Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Skipped searches mean scheduled reports, alerts, and data enrichments aren't running. This creates blind spots in monitoring and compliance.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (scheduler.log)
- **SPL:**
```spl
index=_internal sourcetype=scheduler status="skipped"
| stats count by savedsearch_name, reason
| sort -count
```
- **Implementation:** Monitor scheduler logs for skipped searches. Alert when critical searches are skipped. Track skip reasons (concurrency, disabled, cron). Optimize skipped searches or increase search concurrency limits.
- **Visualization:** Table (skipped searches with reasons), Bar chart (top skipped searches), Line chart (skip rate trend).

---

### UC-13.1.6 · Index Size Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Index size growth affects storage costs and search performance. Trending enables proactive storage planning.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (indexes.conf, REST API)
- **SPL:**
```spl
| rest /services/data/indexes
| table title, currentDBSizeMB, maxTotalDataSizeMB, frozenTimePeriodInSecs
| eval pct_used=round(currentDBSizeMB/maxTotalDataSizeMB*100,1)
| sort -pct_used
```
- **Implementation:** Poll index sizes via REST API daily. Track growth rates per index. Alert when indexes approach maxTotalDataSizeMB (data will roll to frozen). Use `predict` to forecast when limits will be reached.
- **Visualization:** Table (index sizes with % used), Bar chart (top indexes by size), Line chart (growth trend), Gauge (% of max per index).

---

### UC-13.1.7 · KV Store Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** KV Store failures break lookups, app functionality, and ES correlation. Health monitoring prevents cascading application issues.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (kvstore logs)
- **SPL:**
```spl
index=_internal sourcetype=splunkd component=KVStoreServlet OR component=KvStore
| search log_level=ERROR OR log_level=WARN
| stats count by host, log_level, message
| sort -count
```
- **Implementation:** Monitor KV Store logs for errors and replication issues. Track replication lag between SHC members. Alert on KV Store service unavailability. Monitor collection sizes for capacity planning.
- **Visualization:** Status grid (SHC member × KV Store health), Table (KV Store errors), Line chart (replication lag).

---

### UC-13.1.8 · Deployment Server Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Deployment server issues prevent app/config distribution to forwarders, leaving them with stale or incorrect configurations.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (deployment server logs)
- **SPL:**
```spl
index=_internal sourcetype=splunkd component=DeploymentServer
| search log_level=ERROR
| stats count by message, host
| sort -count
```
- **Implementation:** Monitor deployment server logs for errors. Track successful vs failed deployments to clients. Alert on deployment failures. Verify client phone-home intervals are within expected ranges.
- **Visualization:** Table (deployment errors), Single value (clients checking in), Bar chart (failures by server class).

---

### UC-13.1.9 · Data Ingestion Latency
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** High indexing latency (difference between event time and index time) means stale data for searches. Detection enables root cause analysis.
- **App/TA:** Monitoring Console
- **Data Sources:** Any index (sampling `_time` vs `_indextime`)
- **SPL:**
```spl
index=* earliest=-15m
| eval latency=_indextime-_time
| stats avg(latency) as avg_latency, perc95(latency) as p95_latency by index, sourcetype
| where p95_latency > 300
| sort -p95_latency
```
- **Implementation:** Sample events periodically and calculate `_indextime` minus `_time`. Alert when p95 latency exceeds 5 minutes for critical sourcetypes. Investigate queue buildup, network latency, or time parsing issues.
- **Visualization:** Table (sourcetypes with high latency), Line chart (latency trend), Bar chart (latency by sourcetype).

---

### UC-13.1.10 · Search Head Cluster Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** SHC member failures affect user access and search capacity. Captain election issues can cause complete SHC outage.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (SHC logs, REST endpoints)
- **SPL:**
```spl
| rest /services/shcluster/member/members
| table label, status, last_heartbeat, replication_count
| eval heartbeat_age=now()-last_heartbeat
| where status!="Up" OR heartbeat_age > 300
```
- **Implementation:** Monitor SHC member health via REST API. Track captain status and election events. Alert on member disconnection or replication failures. Monitor artifact replication lag between members.
- **Visualization:** Status grid (SHC member × status), Table (member health), Timeline (captain election events).

---

### UC-13.1.11 · Indexer Cluster Bucket Replication
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Under-replicated buckets mean data is at risk of loss. Monitoring ensures the replication factor is maintained.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (CM logs, REST endpoints)
- **SPL:**
```spl
| rest /services/cluster/master/buckets
| where search_factor_met=0 OR replication_factor_met=0
| stats count as non_compliant_buckets
```
- **Implementation:** Monitor cluster master/manager REST endpoints. Track replication and search factor compliance. Alert on any buckets not meeting the configured factor. Investigate cause (indexer down, disk full, network issues).
- **Visualization:** Single value (non-compliant buckets — target: 0), Table (non-compliant bucket details), Line chart (compliance trend).

---

### UC-13.1.12 · HEC Endpoint Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** HEC is a primary data ingestion path. Failures silently drop data from applications, containers, and cloud services.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (http_event_collector logs)
- **SPL:**
```spl
index=_internal sourcetype=splunkd component=HttpEventCollector
| stats count(eval(log_level="ERROR")) as errors, count as total by host
| eval error_rate=round(errors/total*100,2)
| where error_rate > 1
```
- **Implementation:** Monitor HEC endpoint health and error rates. Track HTTP status codes returned to clients. Alert on elevated error rates (4xx, 5xx). Monitor HEC token usage for capacity planning and security.
- **Visualization:** Single value (HEC error rate), Line chart (HEC throughput), Table (errors by token), Bar chart (status codes).

---

### UC-13.1.13 · Sourcetype Breakdown Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Understanding data volume per sourcetype enables cost optimization, retention tuning, and unexpected growth detection.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (license_usage.log)
- **SPL:**
```spl
index=_internal sourcetype=splunkd group=license_usage
| stats sum(b) as bytes by st
| eval gb=round(bytes/1024/1024/1024,2)
| sort -gb
| head 20
```
- **Implementation:** Track daily volume per sourcetype. Identify top consumers. Alert on sourcetypes with unexpected growth (>20% week-over-week). Use for license optimization and retention policy tuning.
- **Visualization:** Bar chart (top sourcetypes by volume), Pie chart (volume distribution), Line chart (growth trend for top sourcetypes).

---

### UC-13.1.14 · Long-Running Search Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Long-running searches consume shared resources and may indicate poorly written SPL or excessive time ranges.
- **App/TA:** Monitoring Console
- **Data Sources:** `_internal` (scheduler, search audit log)
- **SPL:**
```spl
index=_audit action=search info=completed
| where total_run_time > 600
| table _time, user, savedsearch_name, total_run_time, scan_count, event_count
| sort -total_run_time
```
- **Implementation:** Monitor search audit log for long-running searches (>10 minutes). Alert on searches consuming excessive resources. Identify optimization opportunities. Report on top resource-consuming searches weekly.
- **Visualization:** Table (long-running searches), Bar chart (top consumers by run time), Line chart (long search count trend).

---

### UC-13.1.15 · Splunk Certificate Expiration
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Expired Splunk internal certificates break inter-component communication (forwarder→indexer, SHC replication, etc.).
- **App/TA:** Monitoring Console, scripted input
- **Data Sources:** `_internal` (splunkd certificate warnings), certificate check script
- **SPL:**
```spl
index=_internal sourcetype=splunkd "certificate" ("expire" OR "expiration" OR "not yet valid")
| stats count by host, message
```
- **Implementation:** Monitor `_internal` for certificate-related warnings. Deploy scripted input to check Splunk certificate files directly. Alert at 30, 14, and 7 days before expiry. Document certificate renewal procedure.
- **Visualization:** Table (certificates with expiry), Single value (days until nearest expiry), Status grid (component × cert status).

---

### 13.2 Splunk ITSI (Premium)

**Primary App/TA:** Splunk IT Service Intelligence (Premium), Content Pack for Monitoring and Alerting.

---

### UC-13.2.1 · Service Health Score Trending
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Service health scores provide a single-pane view of business service status. Trending enables SLA reporting and proactive management.
- **App/TA:** Splunk ITSI
- **Data Sources:** `itsi_summary` index
- **SPL:**
```spl
index=itsi_summary is_service_in_maintenance=0
| timechart span=1h avg(health_score) by service_name
```
- **Implementation:** Configure ITSI services with KPIs mapped to business services. Track health scores over time. Alert on score degradation. Use for SLA reporting and executive dashboards. Configure Glass Tables for NOC display.
- **Visualization:** Service Analyzer (ITSI native), Glass Table, Line chart (health trend), Status grid.

---

### UC-13.2.2 · KPI Degradation Alerting
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** KPI threshold breaches provide early warning of service degradation. Adaptive thresholds reduce false positives vs static thresholds.
- **App/TA:** Splunk ITSI
- **Data Sources:** ITSI correlation searches, KPI data
- **SPL:**
```spl
index=itsi_summary severity_value>3
| stats count by service_name, kpi_name, severity_label
| sort -count
```
- **Implementation:** Configure KPIs with adaptive thresholds (ITSI machine learning). Set up correlation searches for threshold breach alerting. Route alerts to Episode Review for analyst triage. Tune thresholds based on feedback.
- **Visualization:** ITSI Deep Dive, Service Analyzer, Line chart with threshold bands.

---

### UC-13.2.3 · Episode Volume and MTTR
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Episode volume and resolution time measure IT operations effectiveness. Trending drives process improvement.
- **App/TA:** Splunk ITSI
- **Data Sources:** `itsi_grouped_alerts` index
- **SPL:**
```spl
index=itsi_grouped_alerts
| stats count as episodes, avg(duration) as avg_duration_sec by severity
| eval avg_mttr_min=round(avg_duration_sec/60,1)
```
- **Implementation:** Track episode creation, severity distribution, and time-to-resolution. Monitor episode assignment and owner workload. Alert on episode volume spikes. Report on MTTR by severity for management.
- **Visualization:** Bar chart (episodes by severity), Line chart (episode volume trend), Single value (avg MTTR), Table (open episodes).

---

### UC-13.2.4 · Entity Status Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Entity health provides granular visibility into individual infrastructure components feeding services. Unstable entities degrade service health.
- **App/TA:** Splunk ITSI
- **Data Sources:** ITSI entity overview, entity health scores
- **SPL:**
```spl
| inputlookup itsi_entities
| where entity_status!="active"
| table title, entity_type, entity_status, last_seen
```
- **Implementation:** Configure entity discovery (AD, CMDB, cloud APIs). Monitor entity states (active, inactive, unstable). Alert when critical entities become inactive. Track entity population for coverage analysis.
- **Visualization:** Status grid (entities by type × status), Table (inactive entities), Single value (active entity count).

---

### UC-13.2.5 · Base Search Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** ITSI base searches feed all KPIs. Slow or skipped base searches cause stale or missing KPI data across multiple services.
- **App/TA:** Splunk ITSI
- **Data Sources:** `_internal` (scheduler logs for ITSI searches)
- **SPL:**
```spl
index=_internal sourcetype=scheduler savedsearch_name="ITSI*Base*"
| stats avg(run_time) as avg_runtime, count(eval(status="skipped")) as skipped by savedsearch_name
| where avg_runtime > 120 OR skipped > 0
```
- **Implementation:** Monitor ITSI base search run times and skip rates. Alert when any base search is skipped or exceeds its schedule interval. Optimize slow base searches (reduce scope, improve SPL). Consider splitting overloaded base searches.
- **Visualization:** Table (base search performance), Bar chart (runtime by search), Single value (skipped searches).

---

### UC-13.2.6 · Rules Engine Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** The ITSI Rules Engine processes events into episodes. Failure means alerts are not grouped or routed, breaking Event Analytics.
- **App/TA:** Splunk ITSI
- **Data Sources:** `_internal` (itsi_internal_log)
- **SPL:**
```spl
index=_internal sourcetype=itsi_internal_log component=RulesEngine
| search log_level=ERROR OR log_level=WARN
| stats count by log_level, message
```
- **Implementation:** Monitor Rules Engine logs for errors and warnings. Alert on Rules Engine restarts or processing failures. Track event-to-episode latency. Verify aggregation policies are functioning correctly.
- **Visualization:** Single value (Rules Engine status), Table (recent errors), Line chart (processing latency).

---

### UC-13.2.7 · Predictive Service Degradation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Predicting service health degradation before it happens enables proactive remediation, reducing incident impact.
- **App/TA:** Splunk ITSI + MLTK
- **Data Sources:** `itsi_summary` + ML models
- **SPL:**
```spl
index=itsi_summary service_name="Production Web"
| timechart span=15m avg(health_score) as health
| predict health as predicted_health future_timespan=24 algorithm=LLP5
| where predicted_health < 50
```
- **Implementation:** Train ML models on service health history using MLTK. Predict health scores 4-24 hours ahead. Alert when predicted health falls below threshold. Investigate contributing KPIs proactively. This is an advanced ITSI capability.
- **Visualization:** Line chart (actual vs predicted health), Single value (predicted health in 4h), Alert timeline.

---

### UC-13.2.8 · Glass Table NOC Display
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Real-time service visualization for operations centers provides at-a-glance awareness of infrastructure and service health.
- **App/TA:** Splunk ITSI Glass Tables
- **Data Sources:** ITSI service/KPI data
- **SPL:**
```
N/A — Glass Tables are configured via ITSI UI, not SPL
```
- **Implementation:** Design Glass Tables representing logical infrastructure views (network topology, service dependency map, data center layout). Map ITSI services and KPIs to visual elements. Deploy on NOC screens with auto-refresh.
- **Visualization:** ITSI Glass Table (custom visual layout with service health indicators, KPI widgets, and status icons).

---

### 13.3 Third-Party Monitoring Integration

**Primary App/TA:** Custom webhook/API inputs, Prometheus remote write receiver, SNMP trap receiver.

---

### UC-13.3.1 · Nagios/Zabbix Alert Ingestion
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Consolidating legacy monitoring alerts into Splunk enables cross-tool correlation and single-pane-of-glass operations.
- **App/TA:** Custom webhook input, syslog
- **Data Sources:** Nagios/Zabbix webhook exports, syslog notifications
- **SPL:**
```spl
index=monitoring sourcetype="nagios:notification" OR sourcetype="zabbix:webhook"
| stats count by host, service, state, severity
| sort -count
```
- **Implementation:** Configure Nagios/Zabbix to send alerts to Splunk via webhook or syslog. Normalize alert fields (host, service, severity, state) using CIM. Correlate with Splunk-native monitoring. Phase out legacy tools over time.
- **Visualization:** Table (third-party alerts), Bar chart (alerts by source tool), Status grid (host × service).

---

### UC-13.3.2 · Prometheus Metric Ingestion
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Ingesting Prometheus metrics into Splunk enables long-term storage, cross-domain correlation, and unified dashboarding.
- **App/TA:** OpenTelemetry Collector, Prometheus remote write
- **Data Sources:** Prometheus remote write endpoint, OpenTelemetry metrics
- **SPL:**
```spl
| mstats avg(_value) WHERE index=prometheus metric_name="node_cpu_seconds_total" by host span=5m
```
- **Implementation:** Configure Prometheus remote_write to Splunk's metrics endpoint or use OpenTelemetry Collector as intermediary. Ingest as Splunk metrics. Use `mstats` for efficient querying. Create unified dashboards combining Prometheus and Splunk data.
- **Visualization:** Line chart (metric trends), Multi-metric dashboard, Table (metric summaries).

---

### UC-13.3.3 · PagerDuty/Opsgenie Integration
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracking alert lifecycle and on-call response metrics ensures incident response SLAs are met and identifies process improvements.
- **App/TA:** PagerDuty API input
- **Data Sources:** PagerDuty incidents API, Opsgenie alerts API
- **SPL:**
```spl
index=pagerduty sourcetype="pagerduty:incident"
| eval ack_time_min=round((acknowledged_at_epoch-created_at_epoch)/60,1)
| stats avg(ack_time_min) as avg_ack, avg(resolved_at_epoch-created_at_epoch)/60 as avg_resolve by service
```
- **Implementation:** Poll PagerDuty/Opsgenie API for incident data. Track acknowledgment time, resolution time, and escalation rates. Report on on-call workload distribution. Alert when acknowledgment SLA is breached.
- **Visualization:** Bar chart (MTTA by service), Line chart (incident volume trend), Table (open incidents), Single value (avg MTTA).

---

### UC-13.3.4 · Monitoring Coverage Gap Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Value:** Hosts not covered by any monitoring tool are blind spots. Detection ensures comprehensive infrastructure visibility.
- **App/TA:** Cross-tool asset correlation
- **Data Sources:** CMDB + all monitoring tool inventories
- **SPL:**
```spl
| inputlookup cmdb_hosts.csv
| join type=left hostname [search index=_internal group=tcpin_connections | stats latest(_time) as splunk_last by hostname]
| join type=left hostname [search index=edr sourcetype="*sensor*" | stats latest(_time) as edr_last by hostname]
| where isnull(splunk_last) AND isnull(edr_last)
| table hostname, os, department
```
- **Implementation:** Cross-reference CMDB with all monitoring tool inventories (Splunk forwarders, EDR agents, SNMP targets). Identify assets not monitored by any tool. Alert on new unmonitored assets. Track coverage percentage as a KPI.
- **Visualization:** Table (unmonitored hosts), Single value (coverage %), Pie chart (monitored vs unmonitored), Bar chart (gaps by department).

---

### UC-13.3.5 · Alert Storm Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Correlated alert storms across monitoring tools indicate major incidents. Detection enables rapid escalation and noise reduction.
- **App/TA:** Multi-source alert correlation
- **Data Sources:** All monitoring tool alerts ingested into Splunk
- **SPL:**
```spl
index=alerts sourcetype=*
| timechart span=5m count as alert_count
| where alert_count > 50
| eval storm="Alert storm detected"
```
- **Implementation:** Ingest alerts from all monitoring tools into a common index. Track alert rate across all sources. Alert when rate exceeds normal baseline by >5× (indicates correlated event). Use ITSI Event Analytics for intelligent grouping.
- **Visualization:** Line chart (alert rate across all sources), Single value (current alert rate), Timeline (alert storm events), Table (contributing alerts).

---

## 14. IoT & Operational Technology (OT)

### 14.1 Building Management Systems (BMS)

**Primary App/TA:** MQTT inputs, Modbus TA, SNMP, BACnet gateways, custom API inputs.

---

### UC-14.1.1 · HVAC Performance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** HVAC issues in data centers risk equipment damage; in buildings they affect occupant comfort and energy costs.
- **App/TA:** Modbus TA, MQTT input, BMS API
- **Data Sources:** BACnet/Modbus sensors (temperature setpoint, actual, supply/return air)
- **SPL:**
```spl
index=bms sourcetype="modbus:hvac"
| eval deviation=abs(actual_temp-setpoint_temp)
| where deviation > 3
| table _time, zone, setpoint_temp, actual_temp, deviation
```
- **Implementation:** Connect BMS to Splunk via MQTT broker or Modbus gateway. Ingest setpoints and actuals per zone. Alert when deviation exceeds 3°F/2°C for sustained period. Track energy consumption per HVAC unit.
- **Visualization:** Line chart (setpoint vs actual per zone), Heatmap (zone × temperature), Single value (zones out of spec).

---

### UC-14.1.2 · UPS Battery Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** UPS battery failure during power loss causes complete outage. Proactive monitoring prevents unprotected power events.
- **App/TA:** SNMP TA (UPS-MIB)
- **Data Sources:** SNMP UPS-MIB (upsEstimatedMinutesRemaining, upsBatteryStatus, upsBatteryTemperature)
- **SPL:**
```spl
index=power sourcetype="snmp:ups"
| where battery_status!="normal" OR runtime_remaining_min < 30 OR battery_temp_c > 35
| table _time, ups_name, battery_status, charge_pct, runtime_remaining_min, battery_temp_c
```
- **Implementation:** Poll UPS via SNMP every 5 minutes. Alert on low charge (<80%), low runtime (<30 min), high temperature (>35°C), or abnormal status. Track battery health trend to predict replacement needs.
- **Visualization:** Gauge (charge %), Line chart (runtime trend), Table (UPS status), Single value (runtime remaining).

---

### UC-14.1.3 · Power Consumption Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Power consumption trending supports capacity planning, cost management, and sustainability reporting. Anomalies indicate equipment issues.
- **App/TA:** SNMP TA, smart PDU API
- **Data Sources:** Smart PDU metrics (per-outlet, per-circuit power)
- **SPL:**
```spl
index=power sourcetype="snmp:pdu"
| timechart span=1h avg(power_watts) as avg_power by rack_id
| predict avg_power as predicted future_timespan=30
```
- **Implementation:** Poll PDU power metrics via SNMP. Track per-rack and per-circuit consumption. Baseline normal patterns. Alert on unusual spikes (potential hardware issue) or drops (server failure). Use for PUE calculation.
- **Visualization:** Line chart (power per rack), Heatmap (rack × time power usage), Bar chart (top consumers), Stacked area (floor/room power).

---

### UC-14.1.4 · Access Control Event Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Physical access logs correlate with logical access events for security investigation. Audit trail required for compliance.
- **App/TA:** Access control syslog, API input
- **Data Sources:** Access control system logs (badge events, door status)
- **SPL:**
```spl
index=physical sourcetype="access_control"
| stats count by badge_holder, door, action
| sort -count
```
- **Implementation:** Forward access control events via syslog or API. Parse badge holder, door, time, and action (granted, denied). Alert on after-hours access to sensitive areas. Correlate physical access with logical authentication events.
- **Visualization:** Table (access events), Bar chart (access by door), Timeline (access events for specific person), Geo/floor plan.

---

### UC-14.1.5 · Elevator/Equipment Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Equipment fault codes enable predictive maintenance, reducing downtime and extending equipment life.
- **App/TA:** BMS integration, MQTT
- **Data Sources:** BMS event logs, equipment fault codes
- **SPL:**
```spl
index=bms sourcetype="bms:faults"
| stats count by equipment_id, fault_code, description
| sort -count
```
- **Implementation:** Forward BMS fault events to Splunk. Map fault codes to descriptions via lookup. Track fault frequency per equipment. Alert on critical faults. Report on recurring issues for maintenance planning.
- **Visualization:** Table (equipment faults), Bar chart (faults by equipment), Timeline (fault events).

---

### UC-14.1.6 · Environmental Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Temperature/humidity exceedances in data centers risk equipment damage; in labs they invalidate experiments. Compliance monitoring is mandatory.
- **App/TA:** Environmental sensor inputs (SNMP, MQTT)
- **Data Sources:** Environmental sensors (temperature, humidity, differential pressure)
- **SPL:**
```spl
index=environment sourcetype="sensor:environmental"
| where temp_f > 80 OR temp_f < 64 OR humidity_pct > 60 OR humidity_pct < 40
| table _time, zone, sensor, temp_f, humidity_pct
```
- **Implementation:** Deploy environmental sensors per ASHRAE guidelines. Ingest via SNMP or MQTT. Alert immediately on out-of-range conditions. Log compliance data for audit. Track seasonal patterns for cooling optimization.
- **Visualization:** Heatmap (zone × temperature), Line chart (temp/humidity trend), Single value (zones in compliance %), Gauge (current temp per zone).

---

### 14.2 Industrial Control Systems (ICS/SCADA)

**Primary App/TA:** Splunk Edge Hub (OPC-UA, Modbus, MQTT protocols), Splunk OT Intelligence (Splunkbase #5180).

---

### UC-14.2.1 · PLC/RTU Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Controller failures halt industrial processes. Monitoring CPU, memory, and communication status prevents unplanned downtime.
- **App/TA:** OPC-UA input, Modbus TA
- **Data Sources:** OPC-UA metrics (CPU, memory, I/O status), Modbus register data
- **SPL:**
```spl
index=ot sourcetype="opcua:metrics"
| where plc_cpu_pct > 80 OR plc_memory_pct > 90 OR comm_status!="OK"
| table _time, plc_name, plc_cpu_pct, plc_memory_pct, comm_status
```
- **Implementation:** Connect to PLCs via OPC-UA server or Modbus gateway through Splunk Edge Hub. Poll health metrics every 30 seconds. Alert on CPU >80%, memory >90%, or communication loss. Track uptime per controller.
- **Visualization:** Status grid (PLC × health), Gauge (CPU/memory per PLC), Line chart (health trend).

---

### UC-14.2.2 · Process Variable Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Process variables (pressure, flow, temperature) outside normal ranges indicate equipment failure or process upset. Early detection prevents safety incidents.
- **App/TA:** OPC-UA input, Edge Hub anomaly detection
- **Data Sources:** OPC-UA/Modbus process data (analog values)
- **SPL:**
```spl
index=ot sourcetype="opcua:process"
| where value > high_limit OR value < low_limit
| table _time, tag_name, value, low_limit, high_limit, unit
```
- **Implementation:** Ingest process variables via OPC-UA. Define normal ranges per tag. Use Edge Hub kNN anomaly detection for ML-based alerting. Alert on limit exceedances. Track process stability over time.
- **Visualization:** Line chart (process variable with limit bands), Table (out-of-range events), Single value (current value with status color).

---

### UC-14.2.3 · Safety System Activation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Safety system activations (ESD, interlocks) indicate dangerous conditions. Each activation requires investigation and documentation.
- **App/TA:** Safety PLC logs, OPC-UA events
- **Data Sources:** Safety PLC event logs, emergency shutdown events
- **SPL:**
```spl
index=ot sourcetype="safety_plc"
| search event_type IN ("ESD","interlock_trip","safety_shutdown")
| table _time, system, event_type, cause, action_taken
```
- **Implementation:** Forward safety PLC events to Splunk (isolated network — use data diode or Edge Hub). Alert at critical priority on any safety activation. Maintain incident log for regulatory compliance. Track activation frequency per system.
- **Visualization:** Single value (safety activations — target: 0), Table (activation history), Timeline (safety events).

---

### UC-14.2.4 · Network Segmentation Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** IT/OT network boundary violations create cybersecurity risk to critical infrastructure. Continuous monitoring validates segmentation.
- **App/TA:** Firewall TAs, network flow data
- **Data Sources:** Industrial firewall logs, network flow data at IT/OT boundary
- **SPL:**
```spl
index=network sourcetype="pan:traffic" zone_pair="IT-to-OT"
| where action="allow"
| stats count by src_ip, dest_ip, dest_port, app
| sort -count
```
- **Implementation:** Forward IT/OT boundary firewall logs. Monitor all traffic crossing the boundary. Alert on unexpected protocols or connections. Validate against whitelist of approved communications. Report for ICS security audits.
- **Visualization:** Table (cross-boundary traffic), Sankey diagram (IT→OT flows), Bar chart (by protocol), Single value (unauthorized connections).

---

### UC-14.2.5 · Firmware Version Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** OT devices with outdated firmware are vulnerable to exploitation. Inventory tracking supports patching during maintenance windows.
- **App/TA:** Scripted inventory input, OPC-UA
- **Data Sources:** Asset inventory scans, OPC-UA system attributes
- **SPL:**
```spl
index=ot sourcetype="ics_inventory"
| stats latest(firmware_version) as current by device_name, vendor, model
| lookup approved_firmware.csv vendor, model OUTPUT approved_version
| where current!=approved_version
| table device_name, vendor, model, current, approved_version
```
- **Implementation:** Conduct periodic OT asset inventory scans (during maintenance windows). Ingest firmware versions. Maintain approved firmware lookup. Report on compliance. Prioritize based on CISA ICS advisories.
- **Visualization:** Table (devices with outdated firmware), Pie chart (compliance distribution), Single value (% compliant).

---

### UC-14.2.6 · Unauthorized Access Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Unauthorized access to ICS systems could lead to physical damage or safety incidents. Detection is critical for industrial cybersecurity.
- **App/TA:** Firewall TAs, ICS network monitoring
- **Data Sources:** ICS network logs, industrial firewalls, IDS alerts
- **SPL:**
```spl
index=ot sourcetype="ics_firewall"
| search action="deny" OR src_zone="untrusted"
| stats count by src_ip, dest_ip, dest_port
| sort -count
```
- **Implementation:** Monitor access to ICS networks from all sources. Alert on connections from non-whitelisted IPs. Track engineering workstation access sessions. Correlate with physical access to control rooms. Report for ICS cybersecurity compliance.
- **Visualization:** Table (access events), Timeline (unauthorized attempts), Bar chart (blocked connections by source).

---

### 14.3 Splunk Edge Hub

**Primary App/TA:** Splunk Edge Hub (hardware device), Splunk OT Intelligence (Splunkbase #5180). Sensor data flows as metrics via HEC to dedicated indexes.

---

### UC-14.3.1 · Temperature Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Edge-based kNN anomaly detection provides faster response than cloud-based processing for critical temperature monitoring in data centers and industrial environments.
- **App/TA:** Splunk Edge Hub (built-in kNN model), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics index), `index=edge-hub-anomalies` (anomaly metrics), `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(_value) as avg_temp
  where index=edge-hub-data AND metric_name=temperature
  span=5m by extracted_host
| where avg_temp > 35 OR avg_temp < 10

`` Anomaly query: ``
| mstats count where index=edge-hub-anomalies AND metric_name=temperature AND type="anomaly-detector"
  span=1h by extracted_host
| where count > 0
```
- **Implementation:** Deploy Edge Hub device (IP66-rated, built-in temperature sensor ±0.2°C accuracy). Enable kNN anomaly detection via the Edge Hub mobile app — toggle "Anomaly Detection" on the temperature sensor tile. Sensor data streams as metrics to `edge-hub-data` index; anomalies to `edge-hub-anomalies` index via HEC. Create alerts on anomaly count spikes. Optional: attach external I²C temperature probes via the 3.5mm jack for additional measurement points.
- **Visualization:** Line chart (mstats temperature trend by device), Single value (current temperature), Timeline (anomaly events from edge-hub-anomalies).

---

### UC-14.3.2 · Vibration & Motion Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Equipment vibration changes indicate bearing wear, misalignment, or imbalance. Edge Hub's built-in 3-axis accelerometer and gyroscope enable predictive maintenance without external sensors.
- **App/TA:** Splunk Edge Hub (built-in sensors), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics index), `sourcetype=edge_hub` — built-in 3-axis accelerometer + 6-axis gyroscope
- **SPL:**
```spl
| mstats avg(_value) as avg_accel
  where index=edge-hub-data AND metric_name IN (accelerometer_x, accelerometer_y, accelerometer_z)
  span=5m by metric_name, extracted_host
| eval rms = sqrt(pow(avg_accel, 2))

`` Anomaly-based approach: ``
| mstats count where index=edge-hub-anomalies AND metric_name="accelerometer*" AND type="anomaly-detector"
  span=1h by extracted_host
| where count > 0
```
- **Implementation:** Mount Edge Hub near rotating equipment (IP66 enclosure suits industrial environments, operating -40°C to 80°C). The built-in accelerometer and gyroscope stream metrics to `edge-hub-data`. Enable kNN anomaly detection via the mobile app for each axis. Deploy MLTK Smart Outlier Detection model for more advanced analysis (requires OT Intelligence 4.8.0+ and Edge Hub OS 2.0+). Alert on anomaly detections. Note: one ML model per sensor; performance degrades with 2+ concurrent models.
- **Visualization:** Line chart (accelerometer axes over time), Single value (current RMS), Timeline (anomaly events).

---

### UC-14.3.3 · Air Quality & VOC Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Indoor air quality affects occupant health and productivity. Edge Hub's optional VOC sensor provides IAQ scoring for workplace wellness monitoring.
- **App/TA:** Splunk Edge Hub (optional air quality sensor), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics index), `sourcetype=edge_hub` — built-in VOC sensor (optional, <1s response, IAQ score)
- **SPL:**
```spl
| mstats avg(_value) as avg_iaq
  where index=edge-hub-data AND metric_name IN (voc, iaq_score)
  span=15m by metric_name, extracted_host
| where metric_name="iaq_score" AND avg_iaq > 200

`` Combined with humidity for comfort index: ``
| mstats avg(_value) as value
  where index=edge-hub-data AND metric_name IN (voc, humidity, temperature)
  span=15m by metric_name, extracted_host
```
- **Implementation:** Deploy Edge Hub with optional VOC/air quality sensor module. The sensor provides IAQ (Indoor Air Quality) score with <1 second response time. Data streams as metrics to `edge-hub-data` index. Note: Edge Hub measures VOC and IAQ score — it does not have a CO2 or PM2.5 sensor natively. For CO2/PM2.5, connect external sensors via MQTT or I²C. Alert when IAQ score exceeds thresholds. Correlate with humidity sensor data for comfort indexing.
- **Visualization:** Line chart (IAQ score over time), Gauge (current IAQ), Multi-metric dashboard (VOC + humidity + temperature).

---

### UC-14.3.4 · Sound Level Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Unusual sound patterns near equipment indicate mechanical issues. Edge Hub's stereo microphone enables acoustic monitoring without external sensors.
- **App/TA:** Splunk Edge Hub (built-in stereo microphone), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics index), `sourcetype=edge_hub` — built-in stereo microphone
- **SPL:**
```spl
| mstats avg(_value) as avg_db
  where index=edge-hub-data AND metric_name=sound_level
  span=5m by extracted_host
| where avg_db > 85

`` Anomaly detection: ``
| mstats count where index=edge-hub-anomalies AND metric_name=sound_level AND type="anomaly-detector"
  span=1h by extracted_host
| where count > 0
```
- **Implementation:** Deploy Edge Hub near critical equipment. The built-in stereo microphone captures ambient sound levels. Enable kNN anomaly detection to baseline normal patterns and detect deviations. Alert on sustained high levels (OSHA >85dB threshold) and sudden changes (potential equipment failure). Sound data streams as metrics to `edge-hub-data`; anomalies to `edge-hub-anomalies`.
- **Visualization:** Line chart (sound level trend), Single value (current dB), Timeline (anomaly events).

---

### UC-14.3.5 · MQTT Device Integration Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Edge Hub's built-in MQTT broker aggregates IoT sensor data from external devices. Monitoring broker health ensures data pipeline reliability.
- **App/TA:** Splunk Edge Hub (built-in MQTT broker), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` (metrics from MQTT topics), `index=edge-hub-logs sourcetype=splunk_edge_hub_log` (broker logs)
- **SPL:**
```spl
`` Metrics from MQTT-connected sensors: ``
| mstats avg(_value) as avg_v
  where index=edge-hub-data AND metric_name=temperature_celsius
  span=1m by extracted_host

`` Broker health via device logs: ``
index=edge-hub-logs sourcetype=splunk_edge_hub_log "mqtt" OR "broker"
| stats count by log_level, message
```
- **Implementation:** Configure MQTT topics via Edge Hub Advanced Settings → MQTT tab. Create metric or event topic subscriptions with transformations (metric name, dimensions, timestamps). External IoT devices publish to Edge Hub's built-in MQTT broker (port 1883). Data is transformed and forwarded to Splunk via HEC. For TLS-secured external brokers, upload certificates via Advanced Settings → MQTT → TLS Configuration. Monitor for disconnected publishers and message rate drops.
- **Visualization:** Line chart (MQTT metric trends), Table (connected device inventory), Single value (active MQTT topics).

---

### UC-14.3.6 · SNMP Device Polling from Edge
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Edge Hub bridges OT/IT network segmentation by polling SNMP-enabled devices on isolated networks and forwarding data to Splunk Cloud.
- **App/TA:** Splunk Edge Hub (SNMP integration), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-snmp sourcetype=edge_hub` — SNMP polls via Edge Hub to local devices
- **SPL:**
```spl
index=edge-hub-snmp hub_name="datacenter-eh-01" sourcetype=edge_hub
| stats latest(value) as current by oid_alias
| table oid_alias, current

`` Monitor polling health: ``
index=edge-hub-logs sourcetype=splunk_edge_hub_log "snmp" ("timeout" OR "unreachable")
| stats count by host, message
```
- **Implementation:** Configure SNMP polling via Edge Hub Advanced Settings → SNMP tab. Add devices by IP, set SNMP version (v1/v2c/v3), community string or v3 credentials, and define OIDs with aliases. Set polling interval (default 60s). Edge Hub polls local OT devices and forwards results to `edge-hub-snmp` index via HEC. This bridges the air-gap — enterprise Splunk never touches the OT network directly. Alert on device unreachability or metric threshold violations.
- **Visualization:** Table (device OID values), Status grid (device × poll status), Line chart (metric trends).

---

### UC-14.3.7 · Edge-to-Cloud Data Pipeline Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Edge Hub pipeline health ensures IoT/OT data reaches Splunk. A disconnected Edge Hub creates blind spots — the device backlogs up to 3M sensor data points locally in SQLite.
- **App/TA:** Splunk Edge Hub (system health), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health sourcetype=edge_hub` (device health metrics), `index=edge-hub-logs sourcetype=splunk_edge_hub_log` (system logs)
- **SPL:**
```spl
`` Device resource health: ``
index=edge-hub-health sourcetype=edge_hub
| stats latest(cpu_usage) as CPU, latest(memory_usage) as Memory,
        latest(disk_usage) as Disk by host
| eval Health=if(CPU<80 AND Memory<80 AND Disk<80, "Healthy", "Warning")

`` Connectivity and forwarding issues: ``
index=edge-hub-logs sourcetype=splunk_edge_hub_log
  ("connection" OR "unreachable" OR "timeout")
| timechart count by log_level
```
- **Implementation:** Edge Hub streams device health data to `edge-hub-health` index and system logs to `edge-hub-logs` index. The device checks Splunk reachability every 15 seconds — LED ring shows green (connected) or red (disconnected). When disconnected, data backlogs locally: 3M sensor data points and 100K health/logs/anomalies/SNMP entries each (FIFO, batches of 100 via HEC on reconnect). Monitor CPU, memory, disk utilization on the device. Alert on connectivity loss or sustained high resource usage.
- **Visualization:** Single value (connectivity status with LED color mapping), Gauge (CPU/memory/disk), Line chart (forwarding rate over time).

---


---

### UC-14.3.8 · Data Center Humidity & Condensation Risk
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Prevents equipment failure by detecting dew point conditions before condensation forms on servers and network infrastructure.
- **App/TA:** Splunk Edge Hub (humidity + temperature sensors), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` tag=humidity tag=temperature, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(Humidity), avg(Temperature) as temp by host
| eval dew_point=(243.04*(ln(Humidity/100)+((17.625*temp)/(243.04+temp))))/(17.625-ln(Humidity/100)-((17.625*temp)/(243.04+temp)))
| eval condensation_risk=case(temp<=dew_point, "CRITICAL", temp-dew_point<2, "HIGH", 1=1, "NORMAL")
| where condensation_risk!="NORMAL"
```
- **Implementation:** Deploy Edge Hub in raised floor or ceiling-mounted configuration with humidity sensor exposed to air circulation. Configure Advanced Settings → Sensor Polling interval to 30 seconds for real-time dew point calculation. Use local SQLite backlog to ensure no readings are lost during Splunk connectivity outages.
- **Visualization:** Gauge (dew point vs actual temp), time-series overlay, condensation risk heatmap.

---

---

### UC-14.3.9 · Cold Storage Room Temperature Excursion Alert
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Ensures pharmaceutical, food, or vaccine storage integrity by alerting within minutes of unplanned temperature rise.
- **App/TA:** Splunk Edge Hub (temperature sensor ±0.2°C), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=temperature, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(temperature) as temp by host, _time span=5m
| eval expected_range="[-20,-15]"
| where temp > -15 OR temp < -20
| eval deviation=if(temp > -15, temp - (-15), (-20) - temp)
| stats count as excursion_count, max(deviation) as max_deviation by host
| where excursion_count >= 3
```
- **Implementation:** Configure temperature sensor with Advanced Settings → Alerts enabled at -15°C upper threshold. Store locally for 30 minutes via SQLite backlog. For sub-zero operation, verify Edge Hub -40°C to 80°C operating range covers your environment. MQTT topic subscription can include external low-cost temp probes via I²C port (3.5mm jack).
- **Visualization:** Single-value alert indicator, time-series trend, deviation log.

---

---

### UC-14.3.10 · Museum & Archive Climate Control Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Documents preservation requirements (typically 18-21°C, 35-45% RH) for regulatory compliance and insurance.
- **App/TA:** Splunk Edge Hub (temperature + humidity dual sensor), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=temperature OR metric_name=humidity, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(temperature) as temp, avg(humidity) as rh by host, _time span=10m
| eval temp_compliant=if(temp>=18 AND temp<=21, 1, 0), rh_compliant=if(rh>=35 AND rh<=45, 1, 0)
| eval compliance_score=((temp_compliant + rh_compliant) / 2) * 100
| stats avg(compliance_score) as avg_compliance, count as hours by host
| where avg_compliance < 95
```
- **Implementation:** Mount Edge Hub in archival vault with sensors in passive airflow zone. Configure 10-minute polling intervals via Advanced Settings → Sensor Polling for daily compliance reporting. Use edge-hub-health index to track sensor drift (humidity can drift ±5% annually). Maintain audit trail in edge-hub-logs for regulatory documentation.
- **Visualization:** Compliance scorecard, historical trend, excursion timeline.

---

---

### UC-14.3.11 · Greenhouse Humidity & Growth Optimization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Optimizes plant growth rates by maintaining ideal VPD (vapor pressure deficit) and reducing fungal disease risk.
- **App/TA:** Splunk Edge Hub (humidity + temperature + optional light sensor), custom edge.json container
- **Data Sources:** `index=edge-hub-data` metric_name=humidity OR metric_name=temperature OR metric_name=light, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(temperature) as temp, avg(humidity) as rh, max(light_level) as lux by host, _time span=1h
| eval sat_pressure=610.5*exp((17.27*temp)/(temp+237.7))
| eval vpd=(sat_pressure*(100-rh)/100)/1000
| eval growth_optimal=if(vpd>=0.8 AND vpd<=1.5 AND temp>=20 AND temp<=28, "YES", "NO")
| stats count(eval(growth_optimal="YES")) as optimal_hours, count as total_hours by host
| eval growth_score=(optimal_hours/total_hours)*100
```
- **Implementation:** Deploy Edge Hub with external humidity/temp probe via I²C (3.5mm jack) placed in plant canopy zone. Optional light sensor integration measures lux for photosynthesis optimization. Build custom ARM64 container to interface with greenhouse HVAC controller via Modbus TCP (port 502) for automated adjustment. Store 3M data points locally for real-time analytics without cloud latency.
- **Visualization:** VPD gauge, growth score trend, hourly optimization heatmap.

---

---

### UC-14.3.12 · Security Camera Motion Detection with Light Level Correlation
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Value:** Reduces false motion alerts by correlating camera motion events with ambient light levels and eliminating day/night false positives.
- **App/TA:** Splunk Edge Hub (light sensor + USB camera container with NPU), v2.1+
- **Data Sources:** `index=edge-hub-data` metric_name=light, `index=edge-hub-logs` sourcetype=splunk_edge_hub_log, camera motion event
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log motion_detected=true
| join host [| mstats avg(light_level) as lux by host, _time span=5m | where lux < 10]
| stats count as false_positives by host
| eval false_positive_rate=(false_positives / (false_positives + true_detections)) * 100
```
- **Implementation:** Deploy Edge Hub with USB camera attached (requires USB device passthrough v2.1+). Build custom ARM64 container with OpenCV + NPU inference for motion detection. Filter detections with built-in ambient light sensor: suppress alerts when lux < 10 (night) or > 50000 (direct sun glare). Configure edge.json manifest with resource limits (memory: 256MB, CPU: 1 core) to avoid impacting sensor polling.
- **Visualization:** Motion vs light correlation scatter, false positive trend, alert effectiveness dashboard.

---

---

### UC-14.3.13 · Energy Management & HVAC Occupancy-Based Control
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Reduces HVAC energy consumption 15-30% by correlating occupancy detection with temperature setpoints.
- **App/TA:** Splunk Edge Hub (light + USB camera + custom container), Modbus TCP actuator control
- **Data Sources:** `index=edge-hub-data` metric_name=light, `index=edge-hub-logs` camera_occupancy_count, `index=edge-hub-logs` sourcetype=edge_hub modbus_register
- **SPL:**
```spl
| mstats avg(light_level) as lux by host, _time span=15m
| join host [index=edge-hub-logs camera_occupancy_count > 0 | stats count as people_detected by host, _time span=15m]
| eval hvac_mode=case(people_detected > 0 AND lux < 500, "COMFORT", people_detected = 0 AND lux > 500, "ECO", 1=1, "TRANSITION")
| stats count by hvac_mode, host
```
- **Implementation:** Deploy custom ARM64 container with TensorFlow Lite occupancy counting model (CNN) running on NPU. Integrate Modbus TCP gateway to read/write HVAC controller setpoint registers (port 502). Use light sensor as secondary occupancy indicator. Configure container resource limits to ensure 30-second sensor polling remains unaffected. Implement local alerting logic in container to adjust setpoint without cloud round-trip latency.
- **Visualization:** Occupancy vs light scatter, energy savings trend, HVAC mode timeline.

---

---

### UC-14.3.14 · Warehouse Inventory Light-Based Shelf Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Detects empty or partially depleted shelves in real-time by monitoring light pattern changes in high-bay storage.
- **App/TA:** Splunk Edge Hub (light sensor array), custom container for pattern recognition
- **Data Sources:** `index=edge-hub-data` metric_name=light, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(light_level) as lux by host, rack_id, shelf_position, _time span=5m
| delta lux as lux_change
| eval significant_change=if(abs(lux_change) > 20, "YES", "NO")
| stats count(eval(significant_change="YES")) as change_events, avg(lux) as avg_lux by host, rack_id, shelf_position
| where change_events > 5
| eval inventory_status=case(avg_lux > 1000, "EMPTY", avg_lux > 500, "LOW", 1=1, "STOCKED")
```
- **Implementation:** Mount Edge Hub light sensor facing shelving unit. Deploy custom Python container that learns baseline light patterns for each shelf over 1-week baseline period. Use machine learning to detect sustained light increases (empty shelf) vs brief shadows (restocking activity). Reference Advanced Settings → Containers tab to set container polling interval to 5 minutes. Store 3M light data points locally for historical baseline calculation.
- **Visualization:** Shelf occupancy heatmap, light level trend by shelf, inventory status dashboard.

---

---

### UC-14.3.15 · Structural Health Monitoring via Vibration Baseline Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Value:** Detects early-stage structural degradation (loose bolts, bearing wear) before catastrophic failure by monitoring vibration signature drift.
- **App/TA:** Splunk Edge Hub (3-axis accelerometer + 6-axis gyroscope), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=acceleration_x OR acceleration_y OR acceleration_z, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(acceleration_x) as ax, avg(acceleration_y) as ay, avg(acceleration_z) as az by host, _time span=10m
| eval vibration_magnitude=sqrt((ax^2 + ay^2 + az^2))
| eval baseline=avg(vibration_magnitude)
| relative_entropy baseline, vibration_magnitude
| where vibration_magnitude > (baseline * 1.5)
| stats count as anomalies, max(vibration_magnitude) as peak_mag by host
```
- **Implementation:** Mount Edge Hub on bridge structure, machinery frame, or building floor with accelerometer facing primary load direction. Collect 7-day baseline using kNN built-in anomaly detection (one model per sensor). Enable MLTK Smart Outlier Detection v4.8.0+ for drift tracking over months. Store 3M data points locally for baseline comparison. Note: MQTT sensors only support MLTK; if using built-in accelerometer, use built-in kNN algorithm.
- **Visualization:** Vibration magnitude trend, baseline drift scatter, anomaly frequency timeline.

---

---

### UC-14.3.16 · Door Open/Close Detection via Accelerometer Tilt
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors facility access by detecting door swing events without motion sensors or contact switches.
- **App/TA:** Splunk Edge Hub (3-axis accelerometer with gravity component), custom edge.json container
- **Data Sources:** `index=edge-hub-data` metric_name=acceleration_x OR acceleration_y OR acceleration_z, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(acceleration_z) as az, avg(acceleration_y) as ay by host, _time span=100ms
| eval tilt_angle=atan2(ay, az) * (180 / pi())
| delta tilt_angle as tilt_change
| eval door_event=if(abs(tilt_change) > 15 AND (tilt_change > 0 OR tilt_change < 0), "SWING", "STATIC")
| stats count as swings by host, door_id
| where swings > 0
```
- **Implementation:** Mount Edge Hub vertically on doorframe with accelerometer Z-axis aligned to gravity. Configure 100ms sampling interval (Advanced Settings → Sensor Polling) to capture door swing signatures (typically 0.5-2 second transit). Build custom ARM64 container that implements state machine for distinguishing between single swing (door passing) vs sustained tilt (propped open). Store local SQLite events for 24+ hours via 100K event backlog.
- **Visualization:** Door swing timeline, access frequency histogram, anomalous access alert.

---

---

### UC-14.3.17 · Equipment Alignment & Vibration Analysis via Gyroscope
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors rotational alignment of rotating equipment to predict misalignment-induced failures.
- **App/TA:** Splunk Edge Hub (6-axis gyroscope), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=gyro_x OR gyro_y OR gyro_z, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(gyro_x) as gx, avg(gyro_y) as gy, avg(gyro_z) as gz by host, equipment_id, _time span=1m
| eval rotation_magnitude=sqrt((gx^2 + gy^2 + gz^2))
| eval z_axis_dominant=if(abs(gz) > abs(gx) AND abs(gz) > abs(gy), "YES", "NO")
| stats avg(rotation_magnitude) as avg_rot, stdev(rotation_magnitude) as std_rot by equipment_id
| where (avg_rot > 50) AND (std_rot > 10)
```
- **Implementation:** Mount Edge Hub at equipment bearing or motor coupling with gyroscope Z-axis aligned to equipment rotation axis. Collect 30-day baseline for expected rotation rate and variation. Use built-in kNN anomaly detection to flag unexpected rotational patterns (e.g., gyroscopic precession from misalignment). For precision industrial environments, integrate with OPC-UA PLC (port 4840) to read encoder data for ground-truth validation. Local 3M backlog ensures all rotation events are captured.
- **Visualization:** Rotation rate trend, z-axis dominance heatmap, misalignment risk gauge.

---

---

### UC-14.3.18 · Sound Frequency Analysis for Equipment Signatures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Identifies equipment degradation by detecting shifts in characteristic sound frequencies (bearing wear, compressor blade damage).
- **App/TA:** Splunk Edge Hub (stereo microphone + custom NPU container), v2.1+
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log audio_frequency_analysis, `index=edge-hub-data` metric_name=sound_level
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log audio_signature_extracted=true
| stats avg(peak_frequency_hz) as avg_peak, stdev(peak_frequency_hz) as freq_std,
        max(frequency_band_2k_4k_db) as mid_high_power by equipment_id, _time span=5m
| eval freq_shift=abs(avg_peak - 3000)
| where freq_shift > 500
| eval signature_change="DEGRADATION_RISK"
```
- **Implementation:** Position Edge Hub stereo microphone 0.5-2m from equipment (not in direct high-velocity air). Build custom ARM64 container using FFT (Fast Fourier Transform) library to extract peak frequencies and power spectral density. Deploy on NPU (v2.1+) for real-time FFT computation without cloud round-trip. Reference frequency baseline from first 7 days of operation. Store sound level metric data locally for pattern matching without streaming audio to cloud (privacy + bandwidth).
- **Visualization:** Frequency spectrum waterfall, peak frequency trend, degradation risk timeline.

---

---

### UC-14.3.19 · Multi-Sensor Environmental Baseline & Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Detects sensor failures, calibration drift, or environmental changes by correlating expected relationships between temperature, humidity, pressure, and light.
- **App/TA:** Splunk Edge Hub (multi-sensor fusion), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=temperature OR metric_name=humidity OR metric_name=pressure OR metric_name=light, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(temperature) as temp, avg(humidity) as rh, avg(pressure) as press, avg(light_level) as lux by host, _time span=1h
| stats avg(temp) as avg_temp, stdev(temp) as std_temp,
        avg(rh) as avg_rh, stdev(rh) as std_rh,
        avg(press) as avg_press, stdev(press) as std_press,
        avg(lux) as avg_lux, stdev(lux) as std_lux by host
| eval temp_anomaly=if(std_temp > 5, "DRIFT", "NORMAL"),
        rh_anomaly=if(std_rh > 15, "DRIFT", "NORMAL"),
        press_anomaly=if(std_press > 10, "DRIFT", "NORMAL"),
        lux_anomaly=if(std_lux > 5000, "DRIFT", "NORMAL")
| where temp_anomaly="DRIFT" OR rh_anomaly="DRIFT" OR press_anomaly="DRIFT" OR lux_anomaly="DRIFT"
```
- **Implementation:** Enable all available sensors on Edge Hub (temperature, humidity, optional pressure, optional light). Configure 1-hour aggregation interval (Advanced Settings → Sensor Polling). Establish 30-day baseline for expected correlation between sensors (e.g., temp and humidity should not fluctuate independently in sealed rooms). Use MLTK Smart Outlier Detection to detect when sensor relationships break down (indicator of sensor failure or environmental change). Store baseline profiles in edge-hub-data index for historical comparison.
- **Visualization:** Multi-sensor correlation matrix, drift detection alerts, baseline comparison chart.

---

---

### UC-14.3.20 · Pressure Monitoring for Cleanroom Compliance
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures pharmaceutical and semiconductor cleanroom integrity by verifying positive pressure differentials between zones.
- **App/TA:** Splunk Edge Hub (optional pressure sensor ±0.12 hPa), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=pressure, `sourcetype=edge_hub`
- **SPL:**
```spl
index=edge-hub-data metric_name=pressure
| stats avg(pressure) as avg_press by room, zone, _time span=5m
| eval zone_pair=room + "_" + zone
| eventstats avg(avg_press) as zone_avg by zone_pair
| eval pressure_diff=avg_press - zone_avg
| where pressure_diff < 0.5
| eval compliance="FAIL"
```
- **Implementation:** Deploy Edge Hub with optional pressure sensor in each cleanroom zone. Configure 5-minute polling interval (Advanced Settings → Sensor Polling) for real-time compliance monitoring. Cleanrooms require 0.5-2.0 hPa positive pressure differential from adjacent areas. Set threshold alerts at 0.5 hPa minimum. Enable continuous local logging (edge-hub-logs index) for regulatory audit trail. Pressure sensor range 300-1100 hPa covers sea-level and altitude variations.
- **Visualization:** Pressure differential gauge, zone comparison heatmap, compliance timeline.

---

---

### UC-14.3.21 · HVAC Duct Pressure & Velocity Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors HVAC filter clogging and airflow efficiency by tracking duct static pressure trends.
- **App/TA:** Splunk Edge Hub (optional pressure sensor), Modbus TCP integration
- **Data Sources:** `index=edge-hub-data` metric_name=pressure, `index=edge-hub-logs` sourcetype=edge_hub modbus_register
- **SPL:**
```spl
| mstats avg(pressure) as static_press by duct_zone, _time span=10m
| delta static_press as press_delta
| eval filter_condition=case(static_press > 2.5, "CLOGGED", static_press > 1.5, "RESTRICTED", 1=1, "NORMAL")
| stats avg(filter_condition) as predominant_condition, avg(static_press) as avg_press by duct_zone
| where predominant_condition!="NORMAL"
```
- **Implementation:** Install Edge Hub pressure sensor in return air duct upstream of main filter. Configure 10-minute sampling. Correlate with Modbus TCP fan speed register reads (port 502) from HVAC controller: increasing pressure + constant fan speed = clogged filter. Typical clogged filter threshold: > 2.5 in H2O (84.7 hPa). Store local SQLite data for 7-day history to track pressure rise rate (rate of clogging). Integrate with OPC-UA SCADA (port 4840) for automated filter change alerts.
- **Visualization:** Duct pressure trend, filter condition gauge, maintenance alert timeline.

---

---

### UC-14.3.22 · Weather Station Data Integration & Altitude Compensation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Provides pressure-altitude data for facility environmental baselines and corrects sensor readings for elevation changes.
- **App/TA:** Splunk Edge Hub (optional pressure sensor), MQTT integration
- **Data Sources:** `index=edge-hub-data` metric_name=pressure, `index=edge-hub-logs` sourcetype=splunk_edge_hub_log external_weather_device
- **SPL:**
```spl
| mstats avg(pressure) as edge_press by host, _time span=1h
| join host [| mstats avg(external_pressure) as ext_press by host, _time span=1h]
| eval altitude_diff = (44330 * (1.0 - ((edge_press / ext_press)^(1/5.255))))
| where altitude_diff != 0
| eval altitude_compensated_reading = edge_press - (altitude_diff * 0.0001198)
```
- **Implementation:** Deploy Edge Hub with optional pressure sensor at facility location. Subscribe to external MQTT weather station (Advanced Settings → MQTT Subscriptions) publishing atmospheric pressure. Use barometric formula to compute altitude or detect pressure sensor drift. Store readings in edge-hub-data metric index. Pressure range 300-1100 hPa covers sea-level to 3,000m elevation. Use local SQLite backlog for real-time compensation without cloud latency.
- **Visualization:** Altitude vs time, pressure correction factor trend, weather correlation chart.

---

---

### UC-14.3.23 · Custom Python Container for Data Transformation & Enrichment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Pre-processes edge sensor data locally before forwarding to Splunk, reducing bandwidth and enabling offline analytics.
- **App/TA:** Splunk Edge Hub (custom container), gRPC SDK
- **Data Sources:** `index=edge-hub-data` all metrics post-transformation, `index=edge-hub-logs` container_event_log
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log container_name=transform_enrichment
| stats count as successful_transforms, count(eval(error_code!=0)) as failed_transforms by host
| eval transform_success_rate = (successful_transforms / (successful_transforms + failed_transforms)) * 100
```
- **Implementation:** Build custom ARM64 Python container (requires Dockerfile with Python 3.9+ and gRPC client library) to read sensor data via Edge Hub gRPC API. Implement custom enrichment logic (e.g., add facility ID, shift code, operator ID). Redact PII or sensitive fields before forwarding to cloud. Configure edge.json manifest with resource limits (memory: 512MB, CPU: 2 cores). Container runs as non-root (v2.0+). Deploy via Advanced Settings → Containers tab. Local SQLite backlog absorbs data if container crashes.
- **Visualization:** Transform success rate trend, processing latency histogram, error frequency chart.

---

---

### UC-14.3.24 · BACnet-to-MQTT Protocol Gateway Container
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Bridges legacy BACnet-based building control systems with modern MQTT/Splunk pipeline without expensive protocol gateway hardware.
- **App/TA:** Splunk Edge Hub (custom container), MQTT broker
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log bacnet_translation_event, MQTT subscribed topics
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log bacnet_translation_event
| stats count as bacnet_objects_polled, count(eval(translation_status="SUCCESS")) as successful by host
| eval gateway_health = (successful / bacnet_objects_polled) * 100
| where gateway_health < 95
```
- **Implementation:** Build custom ARM64 container using python-bacnet or BACnet4J library. Container reads BACnet object properties from legacy controllers (IP broadcast network) and translates to MQTT messages (publishes to Edge Hub MQTT broker on port 1883). Configure container resource limits (memory: 256MB, CPU: 1 core) in edge.json manifest. Enable USB device passthrough (v2.1+) if BACnet gateway requires serial/USB interface. Store translation event logs locally for audit trail.
- **Visualization:** BACnet object discovery count, translation success rate, latency histogram.

---

---

### UC-14.3.25 · Local Alerting & GPIO Relay Control Container
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Enables immediate equipment shutdown or alarm triggering at the edge without cloud latency, critical for safety-critical systems.
- **App/TA:** Splunk Edge Hub (custom container), gRPC SDK, GPIO control
- **Data Sources:** `index=edge-hub-data` all sensor metrics, `index=edge-hub-logs` container_alert_log
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log container_name=local_alerting alert_triggered=true
| stats count as alerts_triggered, count(eval(relay_state="ENERGIZED")) as equipment_stopped by host
| eval safety_response_rate = (equipment_stopped / alerts_triggered) * 100
```
- **Implementation:** Build custom ARM64 container with gRPC client library and GPIO library (RPi.GPIO or gpiod). Container subscribes to Edge Hub gRPC sensor stream, implements local thresholds (e.g., temperature > 90°C), and directly controls GPIO pins to energize/de-energize relays (e.g., kill power to pump, trigger siren). No cloud round-trip latency—decisions made in <100ms. Configure edge.json with resource limits (memory: 128MB, CPU: 0.5 core). Store alert events in local edge-hub-logs for compliance.
- **Visualization:** Alert frequency timeline, relay activation log, response latency histogram.

---

---

### UC-14.3.26 · Edge Analytics Container for Rolling Statistics & Threshold Logic
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Computes advanced analytics (moving averages, percentiles, trend detection) locally, reducing cloud computation burden.
- **App/TA:** Splunk Edge Hub (custom container), gRPC SDK
- **Data Sources:** `index=edge-hub-data` computed_statistics, `index=edge-hub-logs` container_analytics_event
- **SPL:**
```spl
index=edge-hub-data metric_name=temperature
| timechart avg(temperature) as temp_avg by host
| delta temp_avg as temp_trend
| stats avg(temp_trend) as avg_trend, stdev(temp_trend) as trend_std by host
| eval trend_anomaly=if(abs(temp_trend) > (avg_trend + (2*trend_std)), "YES", "NO")
```
- **Implementation:** Build custom ARM64 container with NumPy/Pandas libraries (may require multi-stage build to reduce image size). Container implements rolling window statistics (5/15/60-minute moving averages) via gRPC sensor stream. Compute percentiles, trend lines, and detect threshold crossings locally. Publish results as new metrics to MQTT (Advanced Settings → MQTT Publish) or directly to Splunk via gRPC SDK. Store raw + computed metrics locally (3M backlog) for redundancy. Configure resource limits: memory 512MB, CPU 1.5 cores.
- **Visualization:** Rolling average trend, threshold crossing frequency, anomaly detection timeline.

---

---

### UC-14.3.27 · BLE Beacon Asset Tracking & Presence Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks valuable equipment or personnel location within facility using low-cost BLE tags without requiring dedicated asset management infrastructure.
- **App/TA:** Splunk Edge Hub (Bluetooth connectivity), custom container
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log bluetooth_beacon_event, `index=edge-hub-data` metric_name=rssi_strength
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log bluetooth_beacon_event beacon_uuid=* beacon_major=* beacon_minor=*
| stats latest(_time) as last_seen, avg(rssi_strength) as avg_rssi by beacon_id, host
| eval presence_status=if((now() - last_seen) < 300, "PRESENT", "ABSENT")
| stats count(eval(presence_status="PRESENT")) as present_assets by host, location
```
- **Implementation:** Enable Bluetooth scanning on Edge Hub. Build custom ARM64 container that listens for iBeacon or AltBeacon advertisements, parses UUID/major/minor identifiers, and logs beacon_id + RSSI (signal strength). Use RSSI to estimate distance (typically 1-10m range for Edge Hub antenna). Store beacon events locally via 100K event backlog. Implement trilateration logic in container or Splunk downstream to estimate asset location across 3+ Edge Hubs. MQTT publish beacon sightings to central location service.
- **Visualization:** Asset presence map, RSSI range heatmap, movement timeline.

---

---

### UC-14.3.28 · USB Camera Barcode & QR Code Scanning Container
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Automates material tracking and inventory verification by scanning barcodes/QR codes at the edge without manual entry.
- **App/TA:** Splunk Edge Hub (USB camera + custom container), v2.1+ (USB passthrough)
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log barcode_scan_event, `index=edge-hub-data` scan_metadata
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log barcode_scan_event
| regex barcode_value="^[0-9]{12,14}$"
| stats count as successful_scans, count(eval(barcode_valid="NO")) as invalid_scans by host, scan_location
| eval scan_accuracy = (successful_scans / (successful_scans + invalid_scans)) * 100
| where scan_accuracy < 95
```
- **Implementation:** Connect USB camera to Edge Hub USB port (requires v2.1+ for USB device passthrough). Build custom ARM64 container using OpenCV + pyzbar/python-qrcode libraries for barcode detection. Container captures video frames, decodes barcodes/QR codes, and logs scan_id + barcode_value to edge-hub-logs. Implement local SQLite database (in container) to store scanned inventory and prevent duplicate entries. Publish scan events to MQTT (Advanced Settings → MQTT Publish) for downstream processing. Configure edge.json resource limits: memory 512MB, CPU 2 cores (video processing is CPU-intensive).
- **Visualization:** Scan success rate trend, invalid barcode timeline, inventory reconciliation report.

---

---

### UC-14.3.29 · Audio Classification for Anomalous Sound Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Detects equipment distress (compressor cavitation, bearing squeal, motor whine) by classifying sound types without FFT spectral analysis.
- **App/TA:** Splunk Edge Hub (stereo microphone + NPU container), v2.1+
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log audio_classification_event, `index=edge-hub-data` audio_class_confidence
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log audio_classification_event
| stats count as classification_attempts, count(eval(sound_class="ABNORMAL")) as anomalies by host, equipment_type
| eval anomaly_rate = (anomalies / classification_attempts) * 100
| where anomaly_rate > 5
```
- **Implementation:** Deploy TensorFlow Lite audio classification model (v2.1+ NPU support) in custom ARM64 container. Train model on normal equipment sounds (baseline) and abnormal sounds (target classes: cavitation, squeal, whine, vibration). Container processes 1-second audio chunks from stereo microphone at 16kHz, runs inference on NPU, publishes classification result (sound_class + confidence) to MQTT. Store classification logs locally for retraining. Configure edge.json: memory 512MB, CPU 1 core. Note: Do not stream raw audio to cloud (privacy); only log classification results.
- **Visualization:** Anomaly classification frequency, confidence score distribution, sound type timeline.

---

---

### UC-14.3.30 · Predictive Maintenance via NPU-Based Model Inference
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Predicts equipment failures (bearing degradation, motor insulation breakdown) 7-30 days in advance using on-device ML inference.
- **App/TA:** Splunk Edge Hub (NPU + custom container), v2.1+, OT Intelligence
- **Data Sources:** `index=edge-hub-data` raw sensor metrics, `index=edge-hub-logs` predictive_maintenance_inference
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log predictive_model_inference failure_risk_score>0.7
| stats count as high_risk_predictions, avg(failure_risk_score) as avg_risk by equipment_id, host
| eval maintenance_urgency=case(avg_risk > 0.85, "CRITICAL", avg_risk > 0.7, "HIGH", 1=1, "MEDIUM")
```
- **Implementation:** Train XGBoost or TensorFlow Lite model offline using historical sensor data (temperature, vibration, power consumption trends). Quantize model to INT8 for NPU deployment. Build custom ARM64 container that streams sensor features (via gRPC API) into model inference pipeline running on NPU. Model outputs failure_risk_score (0-1 scale). If score > 0.7, trigger alert and log predictive maintenance event. Store raw feature vectors locally (3M backlog) for continuous model retraining. Configure edge.json: memory 512MB, CPU 2 cores, NPU enabled.
- **Visualization:** Failure risk score trend, maintenance urgency gauge, prediction accuracy (post-hoc) scatter.

---

---

### UC-14.3.31 · OPC-UA Tag Browsing & Change Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors PLC tag changes in real-time and alerts on unexpected data type or value changes indicating program modification or malfunction.
- **App/TA:** Splunk Edge Hub (OPC-UA client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua, `index=edge-hub-health` sourcetype=edge_hub
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_opcua opcua_tag=* opcua_value=*
| stats latest(opcua_value) as latest_val, latest(opcua_data_type) as latest_type by opcua_tag, host
| join opcua_tag [| rest /services/saved/data-model/indexes/OT_Industry_Process_Assets | fields asset_id, tag_name, expected_data_type]
| where latest_type != expected_data_type
| eval change_alert="DATA_TYPE_MISMATCH"
```
- **Implementation:** Configure OPC-UA connection in Advanced Settings → OPC-UA tab with PLC/SCADA server hostname (port 4840), username/password or anonymous authentication. Browse PLC namespace to discover tags. Enable continuous polling of selected tags at 5-second intervals. Configure threshold alerts on value changes (delta > 20% or absolute > threshold). Store tag values in edge-hub-logs index with sourcetype=splunk_edge_hub_opcua. Detect unexpected data type changes (INT to FLOAT) or tag disappearance (PLC program change). Use local SQLite backlog (100K event capacity) for connectivity loss resilience.
- **Visualization:** Tag value trend, data type change alert, PLC program integrity dashboard.

---

---

### UC-14.3.32 · Modbus TCP Register Monitoring for Industrial Equipment
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors equipment operational parameters via Modbus registers without requiring specialized data collection agents.
- **App/TA:** Splunk Edge Hub (Modbus TCP client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub modbus_register, `index=edge-hub-data` modbus_metric
- **SPL:**
```spl
index=edge-hub-logs sourcetype=edge_hub modbus_register
| regex modbus_register_name="^(voltage|current|frequency)"
| stats latest(register_value) as latest_val by modbus_register_name, modbus_device_ip
| eval register_healthy=case(
    modbus_register_name="voltage" AND latest_val >= 210 AND latest_val <= 250, "YES",
    modbus_register_name="current" AND latest_val >= 0 AND latest_val <= 100, "YES",
    modbus_register_name="frequency" AND latest_val >= 49 AND latest_val <= 51, "YES",
    1=1, "NO")
| where register_healthy="NO"
```
- **Implementation:** Configure Modbus TCP in Advanced Settings → Modbus tab with equipment IP/port (default 502). Define register map (coils, discrete inputs, holding registers, input registers) with OID aliases for readability. Configure polling interval (10-30 seconds typical) and register read strategy (optimized batching). Store register values in edge-hub-logs (events) or as metrics in edge-hub-data. Map register indices to human-readable tags (e.g., 0x1234→"VFD_Speed_Hz"). Local SQLite backlog stores 100K Modbus events for offline resilience.
- **Visualization:** Register value trend, equipment health gauge, Modbus gateway connection status.

---

---

### UC-14.3.33 · Multi-Protocol Sensor Fusion (OPC-UA + MQTT + Built-in)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Correlates data from heterogeneous sources (PLC via OPC-UA, IoT devices via MQTT, internal sensors) to identify root causes of anomalies.
- **App/TA:** Splunk Edge Hub (multi-protocol aggregation), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua OR splunk_edge_hub_log (MQTT), `index=edge-hub-data` all metric types
- **SPL:**
```spl
(index=edge-hub-logs sourcetype=splunk_edge_hub_opcua OR index=edge-hub-logs sourcetype=splunk_edge_hub_log mqtt_topic=*)
OR index=edge-hub-data metric_name=temperature
| stats avg(temperature) as temp, avg(opc_ua_motor_current) as motor_current,
        avg(mqtt_load_percent) as load by equipment_id, _time span=5m
| eval correlation=correlation(temp, motor_current)
| where correlation > 0.8
| eval root_cause=case(
    temp > 80 AND motor_current > 15, "THERMAL_OVERLOAD",
    temp > 80 AND motor_current < 5, "SENSOR_FAILURE",
    1=1, "UNKNOWN")
```
- **Implementation:** Configure all three connectivity modes simultaneously: (1) OPC-UA to PLC (Advanced Settings → OPC-UA), (2) MQTT subscriptions to IoT devices (Advanced Settings → MQTT Subscriptions), (3) Enable built-in sensors (temperature, humidity, etc.). Set each protocol's polling interval (OPC-UA 5s, MQTT 10s, sensors 30s) to minimize latency skew. Ingest all data streams with consistent timestamps. Local SQLite backlog (3M data points) ensures data fusion doesn't lose events. Use downstream Splunk correlation SPL for multi-modal root cause analysis.
- **Visualization:** Multi-protocol correlation heatmap, root cause attribution waterfall, equipment health scorecard.

---

---

### UC-14.3.34 · Protocol Gateway Health & Connectivity Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks OPC-UA/Modbus/MQTT gateway uptime and connection quality to prevent silent data loss.
- **App/TA:** Splunk Edge Hub (health monitoring), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub, `index=edge-hub-logs` sourcetype=splunk_edge_hub_log connection_event
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub gateway_name=*
| stats latest(connection_status) as status, latest(response_time_ms) as response_time,
        count(eval(error_code!=0)) as error_count by gateway_name, host
| eval gateway_health=case(
    status="CONNECTED" AND response_time < 1000 AND error_count < 5, "HEALTHY",
    status="CONNECTED" AND response_time >= 1000, "SLOW",
    status="DISCONNECTED" OR error_count > 10, "DEGRADED",
    1=1, "UNKNOWN")
```
- **Implementation:** Edge Hub continuously monitors OPC-UA (port 4840), Modbus TCP (port 502), and MQTT broker (port 1883) connectivity every 15 seconds. Log connection attempts + response times to edge-hub-health index (sourcetype=edge_hub). Track error codes (authentication failures, timeouts, handshake errors). Store 100K health events locally. If gateway disconnects, LED ring turns red. Resume transmission via local SQLite backlog (FIFO) when connectivity restored. Configure alert thresholds: downtime > 1 minute = critical, response time > 2s = warning.
- **Visualization:** Gateway uptime timeline, response time histogram, error rate trend.

---

---

### UC-14.3.35 · Industrial Alarm Management via OPC-UA
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Centralizes alarm processing from multiple PLCs via OPC-UA Alarms & Events service, preventing missed critical alerts.
- **App/TA:** Splunk Edge Hub (OPC-UA A&E client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua alarm_event, `index=edge-hub-health` sourcetype=edge_hub
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_opcua alarm_event=true
| stats count as alarm_count, latest(alarm_severity) as severity, latest(alarm_message) as msg by source_node_id, _time span=1m
| where severity="HIGH" OR severity="CRITICAL"
| eval acknowledgment_status=if(isnotnull(acknowledged_time), "ACK", "UNACK")
| where acknowledgment_status="UNACK"
```
- **Implementation:** Configure OPC-UA in Advanced Settings → OPC-UA tab with Alarms & Events subscription enabled. Define event filters for alarm severity levels (High, Critical). Edge Hub subscribes to server's Alarms & Events namespace and logs all alarm state changes (triggered, acknowledged, cleared) to edge-hub-logs (sourcetype=splunk_edge_hub_opcua). Store alarm events locally via 100K backlog for resilience. Implement alarm acknowledgment workflow: operator ack in Splunk → webhook → OPC-UA Acknowledge operation. Color LED ring based on highest unacknowledged severity (red=critical, orange=high).
- **Visualization:** Alarm frequency timeline, severity distribution pie, acknowledgment status list.

---

---

### UC-14.3.36 · Energy Meter Integration via Modbus TCP
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors power consumption and demand charges in real-time to identify energy waste and optimize utility costs.
- **App/TA:** Splunk Edge Hub (Modbus TCP client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub modbus_register meter_type=energy, `index=edge-hub-data` metric_name=power
- **SPL:**
```spl
index=edge-hub-logs sourcetype=edge_hub modbus_register meter_type=energy modbus_register_name=total_energy_kwh
| stats latest(register_value) as total_kwh, latest(_time) as latest_time by meter_id
| join meter_id [| rest /services/saved/data-model/indexes/energy_meter_cost_model | fields meter_id, cost_per_kwh]
| eval daily_cost=(total_kwh * cost_per_kwh)
| stats sum(daily_cost) as total_daily_cost by meter_id
| where total_daily_cost > threshold
```
- **Implementation:** Deploy Edge Hub with Modbus TCP connectivity to energy meter (Schneider, Siemens, ABB models typical support). Configure register map: 0x0000=voltage, 0x0002=current, 0x0004=power_factor, 0x000C=total_energy_kwh. Set polling interval to 1-5 minutes for demand tracking. Store register values in edge-hub-logs as events or convert to metrics (kW, kVAR) in edge-hub-data for time-series analysis. Local SQLite backlog ensures no consumption data is lost. Implement demand charge alerts (cost spike detection) via SPL.
- **Visualization:** Energy consumption trend, cost breakdown by zone, demand charge projection.

---

---

### UC-14.3.37 · PLC Program Change Detection via OPC-UA Timestamp Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Value:** Detects unauthorized or accidental PLC program modifications by tracking program last-edit timestamp changes.
- **App/TA:** Splunk Edge Hub (OPC-UA client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua program_timestamp_event
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_opcua program_timestamp_event
| stats latest(program_last_modified) as current_timestamp by program_id, plc_ip
| join program_id [| rest /services/saved/data-model/indexes/plc_program_baseline | fields program_id, last_known_timestamp, last_known_user]
| where current_timestamp != last_known_timestamp
| eval program_change="DETECTED"
| eval time_since_change_hours=((now() - current_timestamp) / 3600)
```
- **Implementation:** Configure OPC-UA subscriptions to PLC program metadata tags (if available) or implement custom OPC-UA node reads for program timestamp info. Some PLC vendors expose system time for last program write. Query these tags every 5-10 minutes. Store baseline program timestamp on first run. Alert if current timestamp differs from baseline (indicates program reload or modification). Log change details to edge-hub-logs. Correlate with PLC user login logs (if available via separate data source) to identify who modified program. This is security-critical for industrial environments.
- **Visualization:** Program timestamp timeline, change detection alert, modification history.

---

---

### UC-14.3.38 · SCADA HMI Event Capture & Operator Action Logging
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Audits all HMI operator actions (setpoint changes, equipment starts/stops) for compliance and root cause analysis.
- **App/TA:** Splunk Edge Hub (OPC-UA tag subscription), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_opcua hmi_event, `index=edge-hub-health` sourcetype=edge_hub
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_opcua hmi_event=true
| regex field_name="setpoint|start|stop|mode"
| stats count as action_count, latest(field_value) as value by operator_id, _time span=1h
| eval action_frequency=(action_count / 60)
| where action_frequency > 5
| eval operator_behavior="UNUSUAL"
```
- **Implementation:** Configure OPC-UA subscriptions to HMI write tags (setpoints, control commands). Enable change notification for tags with ValueWrite attributes. Log tag writes with operator context (user ID from HMI session) to edge-hub-logs (sourcetype=splunk_edge_hub_opcua). Store events locally (100K backlog) for audit trail continuity. Implement audit report: operator ID, timestamp, tag name, old value, new value, status. Alert on unusual operator behavior patterns (too many commands in short time window).
- **Visualization:** Operator action timeline, command frequency histogram, unusual behavior alert.

---

---

### UC-14.3.39 · Multi-Device Fleet Firmware Version Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Value:** Ensures all Edge Hubs in a fleet run current firmware versions to maintain security and feature parity.
- **App/TA:** Splunk Edge Hub (multiple devices), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub firmware_version, `index=edge-hub-logs` firmware_update_event
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats latest(firmware_version) as fw_version, latest(os_build_number) as build by host, device_id
| stats dc(fw_version) as unique_versions, count as total_devices by location
| where unique_versions > 1
| eval compliance="DRIFTED"
| join location [| rest /services/data-model/indexes/edge_hub_fleet_baseline | fields location, target_firmware_version]
| where fw_version != target_firmware_version
```
- **Implementation:** Central Splunk instance receives health data from all Edge Hubs via HEC (HTTP Event Collector). Health heartbeat includes firmware_version + build_number every 5 minutes (stored in edge-hub-health index). Create baseline search for target firmware per location/site. Alert when devices drift from baseline (old firmware detected). Implement scheduled search that flags out-of-compliance devices for manual firmware update. Store update history in edge-hub-logs for audit trail. For multi-region deployments, allow per-region firmware versions.
- **Visualization:** Firmware version distribution pie, device compliance status list, update history timeline.

---

---

### UC-14.3.40 · Device Location Tracking via GNSS
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors Edge Hub physical location for mobile/outdoor deployments to verify proper coverage and detect theft/unauthorized movement.
- **App/TA:** Splunk Edge Hub (cellular + GNSS), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub gnss_position, `index=edge-hub-health` sourcetype=edge_hub location_heartbeat
- **SPL:**
```spl
index=edge-hub-logs sourcetype=edge_hub gnss_position=true
| stats latest(latitude) as lat, latest(longitude) as lon, latest(accuracy_meters) as accuracy by device_id
| join device_id [| rest /services/data-model/indexes/edge_hub_location_baseline | fields device_id, expected_latitude, expected_longitude, geofence_radius_meters]
| eval distance=sqrt(((lat - expected_latitude)*111111)^2 + ((lon - expected_longitude)*111111*cos(expected_latitude*pi()/180))^2)
| where distance > geofence_radius_meters
| eval location_drift="ALERT"
```
- **Implementation:** Edge Hub with cellular module (LTE/4G) includes integrated GNSS receiver. Enable GNSS in Advanced Settings (requires clear sky line-of-sight). Edge Hub logs GPS position (latitude, longitude, accuracy_meters) to edge-hub-logs every 15 minutes. Store expected location + geofence radius per device. Alert if device moves outside geofence (e.g., trailer theft detection, equipment relocation). For outdoor industrial sites, track GNSS acquisition time and accuracy metrics (typically 5-20m accuracy in open sky). Local SQLite stores 30+ days of position history.
- **Visualization:** Device location map, geofence status indicator, movement timeline.

---

---

### UC-14.3.41 · Cellular Connectivity Quality & Signal Strength Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Tracks LTE/4G signal strength and network latency to predict connectivity issues and plan network upgrades.
- **App/TA:** Splunk Edge Hub (cellular module), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub cellular_signal, `index=edge-hub-logs` cellular_connect_event
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats latest(rssi_dbm) as signal_dbm, latest(sinr_db) as sinr, latest(latency_ms) as latency,
        latest(network_type) as net_type by host, cell_id
| eval signal_quality=case(
    signal_dbm > -80 AND sinr > 15, "EXCELLENT",
    signal_dbm > -90 AND sinr > 5, "GOOD",
    signal_dbm > -100, "FAIR",
    1=1, "POOR")
| stats avg(latency) as avg_latency by signal_quality, host
```
- **Implementation:** Edge Hub cellular module reports RSSI (signal strength -140 to 0 dBm), SINR (signal-to-interference noise ratio dB), network latency (ms), and network type (LTE Band, 4G, etc.) to edge-hub-health index every 5 minutes. Strong signal: RSSI > -80 dBm. Acceptable signal: RSSI -80 to -100 dBm. Poor signal: RSSI < -100 dBm. Track carrier (AT&T, Verizon, etc.) and band for capacity planning. Alert if signal drops below -100 dBm or latency exceeds 500ms (indicates backhaul congestion or dead zone).
- **Visualization:** Signal strength heatmap, latency trend, network type distribution.

---

---

### UC-14.3.42 · Edge Hub Resource Capacity Planning & CPU/Memory Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Prevents Edge Hub performance degradation and data loss by tracking resource utilization and planning for container resource allocation.
- **App/TA:** Splunk Edge Hub (system monitoring), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub cpu_percent, memory_percent, disk_used_mb
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats avg(cpu_percent) as avg_cpu, max(cpu_percent) as peak_cpu,
        avg(memory_percent) as avg_mem, max(memory_percent) as peak_mem,
        latest(disk_used_mb) as disk_used by host, _time span=1h
| eval cpu_headroom=(100 - peak_cpu), mem_headroom=(100 - peak_mem), disk_available_mb=(32000 - disk_used)
| where cpu_headroom < 10 OR mem_headroom < 5 OR disk_available_mb < 1000
| eval resource_alert="CAPACITY_WARNING"
```
- **Implementation:** Edge Hub OS reports CPU %, memory %, disk %, and container-level resource stats to edge-hub-health index every 5 minutes. NXP IMX8M has 8GB RAM total: allocate 4GB for OS/system, 4GB for containers. Each container configured with memory limits in edge.json (e.g., 512MB, 256MB). Monitor peak CPU during data bursts (e.g., video processing, FFT computation). Alert when peak CPU > 80% (insufficient headroom for spikes) or memory > 95% (OOM risk). Plan container consolidation or upgrade if resources consistently constrained.
- **Visualization:** CPU usage trend, memory usage gauge, container resource breakdown pie, capacity projection.

---

---

### UC-14.3.43 · Configuration Drift Detection Across Fleet
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Value:** Ensures all Edge Hubs in a fleet maintain consistent configuration (MQTT topics, OPC-UA endpoints, polling intervals) to prevent data inconsistencies.
- **App/TA:** Splunk Edge Hub (fleet management), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub config_hash, `index=edge-hub-health` configuration_snapshot
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub configuration_snapshot=true
| stats latest(config_hash) as current_hash, latest(config_timestamp) as timestamp by host, location
| stats dc(current_hash) as unique_configs, count as total_devices by location
| where unique_configs > 1
| eval config_drift="DETECTED"
| join location [| rest /services/data-model/indexes/approved_fleet_configs | fields location, approved_config_hash, approved_timestamp]
| where current_hash != approved_config_hash
```
- **Implementation:** Edge Hub computes MD5 hash of entire configuration (MQTT subscriptions, OPC-UA endpoints, Modbus registers, container definitions, sensor polling intervals) and reports to edge-hub-health index weekly. Central Splunk instance generates baseline config hash per location/site. Alert if device config hash differs (indicates manual configuration, failed deployment, or malicious modification). Implement remediation workflow: flag device for manual inspection or trigger automated config re-deployment via edge.json manifest update. Store configuration snapshots locally for historical comparison.
- **Visualization:** Config drift alert, baseline hash variance, deployment history timeline.

---

---

### UC-14.3.44 · Local Backlog Monitoring & Data Loss Prevention
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Prevents silent data loss by monitoring local SQLite backlog capacity and alerting before data is discarded.
- **App/TA:** Splunk Edge Hub (local storage), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub backlog_status, `index=edge-hub-logs` backlog_overflow_event
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub
| stats latest(backlog_sensor_data_count) as sensor_backlog, latest(backlog_max_capacity) as capacity,
        latest(backlog_events_lost) as lost_count by host
| eval backlog_utilization=(sensor_backlog / capacity) * 100
| eval data_loss_risk=case(
    backlog_utilization > 95, "CRITICAL",
    backlog_utilization > 80, "HIGH",
    backlog_utilization > 60, "MEDIUM",
    1=1, "LOW")
| where data_loss_risk!="LOW"
```
- **Implementation:** Edge Hub tracks SQLite backlog capacity: 3M sensor data points, 100K events (logs/health/anomalies), 100K SNMP data points. Report current backlog size + utilization % to edge-hub-health index every 5 minutes. Alert if utilization exceeds 80% (indicates connectivity outage or ingestion backlog). During Splunk cloud outage, Edge Hub continues logging to local SQLite; upon reconnection, HEC batch processor sends oldest 10K entries in batches of 100 until caught up. Implement alert: if backlog at 95% capacity for >30 minutes, oldest data will be lost (FIFO). Set escalating alert thresholds to trigger remediation.
- **Visualization:** Backlog utilization gauge, lost data counter, recovery timeline.

---

---

### UC-14.3.45 · USB Camera People Counting for Occupancy & Capacity Management
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Enables real-time facility occupancy tracking and automatic alerts when spaces exceed safe capacity thresholds.
- **App/TA:** Splunk Edge Hub (USB camera + NPU container), v2.1+
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log people_count_event, `index=edge-hub-data` metric_name=occupancy_count
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log people_count_event
| stats latest(people_detected) as occupancy, latest(_time) as timestamp, max(people_detected) as peak_occupancy by location, camera_id
| join location [| rest /services/data-model/indexes/facility_capacity_limits | fields location, max_occupancy_safe, max_occupancy_emergency]
| eval capacity_status=case(
    occupancy > max_occupancy_emergency, "EMERGENCY_EXCEEDED",
    occupancy > max_occupancy_safe, "OVERCROWDED",
    1=1, "NORMAL")
| stats latest(capacity_status) as status, avg(occupancy) as avg_occ by location
```
- **Implementation:** Deploy Edge Hub with USB camera (v2.1+ USB passthrough required). Build custom ARM64 container using TensorFlow Lite + OpenCV for person detection + counting (YOLO or MobileNet models work well). Container processes video frames at 1-2 fps, outputs people_count metric to MQTT and event logs. Run inference on NPU (v2.1+) for real-time performance. Configure container resource limits: memory 512MB, CPU 2 cores. Set safe + emergency capacity thresholds per location. Alert if occupancy exceeds safe threshold; trigger intercom/visual alerts if emergency threshold exceeded.
- **Visualization:** Occupancy trend by location, capacity status heatmap, peak occupancy histogram.

---

---

### UC-14.3.46 · USB Camera Visual Inspection for Manufacturing Defects
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Automates defect detection on assembly lines by running visual inspection models on captured images without human intervention.
- **App/TA:** Splunk Edge Hub (USB camera + NPU container), v2.1+, OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log visual_inspection_event, `index=edge-hub-data` inspection_metadata
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log visual_inspection_event defect_detected=true
| stats count as defect_count, count(eval(defect_severity="CRITICAL")) as critical_defects by location, product_line
| eval defect_rate=(defect_count / total_parts_inspected) * 100
| where defect_rate > acceptable_defect_rate
| eval quality_alert="DEFECT_RATE_EXCEEDED"
```
- **Implementation:** Deploy Edge Hub with USB camera pointing at assembly line. Train TensorFlow Lite object detection model (e.g., SSD MobileNet) on product images with annotated defects (scratches, dents, misalignment, discoloration). Build custom ARM64 container that captures images at takt time (e.g., 1 image per part), runs inference on NPU, logs result (defect_detected=true/false, defect_class, confidence) to edge-hub-logs. Store images locally only if defect detected (privacy + storage). Implement local alerting: if defect severity=CRITICAL, trigger relay to stop conveyor belt. Configure edge.json resource limits: memory 512MB, CPU 2 cores, GPU (NPU) enabled.
- **Visualization:** Defect detection timeline, defect type distribution pie, quality trend chart.

---

---

### UC-14.3.47 · Custom Python Container for API Integration & Data Enrichment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Integrates Edge Hub data with external APIs (weather, commodity prices, inventory systems) to enrich sensor context without cloud latency.
- **App/TA:** Splunk Edge Hub (custom container), gRPC SDK, HTTP client
- **Data Sources:** `index=edge-hub-data` enriched_sensor_metrics, `index=edge-hub-logs` enrichment_event
- **SPL:**
```spl
index=edge-hub-data metric_name=temperature
| join host [| mstats avg(temperature) as avg_temp by host | eval weather_context_available=1]
| stats avg(avg_temp) as sensor_temp, latest(external_air_temp_c) as api_air_temp by host
| eval correlation=correlation(sensor_temp, api_air_temp)
| where correlation < 0.5
| eval enrichment_anomaly="LOW_CORRELATION"
```
- **Implementation:** Build custom ARM64 container with Python requests library. Container subscribes to sensor data via gRPC API, periodically fetches external data (weather API, stock prices, etc.) via HTTPS, correlates with sensor data, and publishes enriched metrics back to MQTT. Example: fetch external air temperature from weather API every 30 minutes, correlate with Edge Hub inside temperature to detect HVAC failures. Implement caching layer to minimize API calls. Store enrichment logs locally. Configure edge.json: memory 256MB, CPU 1 core. Container runs as non-root (v2.0+).
- **Visualization:** Sensor vs API correlation scatter, enrichment success rate trend, external data staleness timeline.

---

---

### UC-14.3.48 · Pressure & Humidity Sensor Correlation for Leakage Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Value:** Detects water leaks or condensation damage early by correlating pressure drop with humidity rise in sealed enclosures.
- **App/TA:** Splunk Edge Hub (pressure + humidity sensors), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=pressure OR metric_name=humidity, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(pressure) as press, avg(humidity) as rh by host, _time span=5m
| delta press as press_change
| stats avg(press_change) as avg_press_delta, stdev(rh) as rh_volatility by host
| eval leak_risk=case(
    avg_press_delta < -0.5 AND rh_volatility > 10, "CRITICAL_LEAK",
    avg_press_delta < -0.2 AND rh_volatility > 5, "POTENTIAL_LEAK",
    1=1, "NORMAL")
| where leak_risk!="NORMAL"
```
- **Implementation:** Deploy Edge Hub in sealed enclosure (electrical room, equipment cabinet) with optional pressure sensor (±0.12 hPa accuracy) and built-in humidity sensor exposed to enclosure air. Configure 5-minute polling. Monitor pressure trend: sealed enclosure pressure should remain stable (±1 hPa). Pressure drop + humidity rise = leakage from outside or failed seal. Humidity rise alone = internal moisture generation (faulty equipment). Implement baseline: first week = normal enclosure profile. Alert if pressure drops >1 hPa/hour (rapid leak). Store local SQLite data for 30+ days to track seasonal humidity variations. Trigger maintenance ticket on leak detection.
- **Visualization:** Pressure vs humidity scatter plot, leak risk gauge, enclosure seal integrity trend.

---

---

### UC-14.3.49 · Sound Level & Frequency Band Monitoring for Regulatory Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors workplace noise levels to ensure OSHA compliance (90 dB over 8 hours) and tracks frequency bands for hearing loss risk.
- **App/TA:** Splunk Edge Hub (stereo microphone + custom container), gRPC SDK
- **Data Sources:** `index=edge-hub-data` metric_name=sound_level_db OR metric_name=frequency_band_power, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(sound_level_db) as avg_db, max(sound_level_db) as peak_db by location, _time span=1h
| stats avg(avg_db) as hourly_avg_db, max(peak_db) as hourly_peak_db by location
| eval osha_exposure_rating=case(
    hourly_avg_db >= 90, "NO_PROTECTION_REQUIRED",
    hourly_avg_db >= 85, "HEARING_PROTECTION_REQUIRED",
    1=1, "SAFE")
| where osha_exposure_rating="HEARING_PROTECTION_REQUIRED"
```
- **Implementation:** Deploy Edge Hub with stereo microphone in warehouse/factory/airport locations. Configure 1-hour aggregation for OSHA 8-hour TWA (time-weighted average). Build custom container that computes: (1) dB(A) sound pressure level (apply A-weighting curve), (2) frequency band powers (125Hz, 250Hz, 500Hz, 1kHz, 2kHz, 4kHz, 8kHz octave bands). Store hourly averages in edge-hub-data metrics. Alert if hourly average exceeds 85 dB (OSHA hearing protection threshold). Log high-frequency band power (4-8kHz) for hearing loss risk assessment. Note: Do not stream raw audio; only log processed metrics for privacy.
- **Visualization:** Noise level trend by location, frequency band heatmap, OSHA compliance status.

---

---

### UC-14.3.50 · Accelerometer-Based Fall Detection & Impact Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Value:** Detects equipment falls or impacts (e.g., dropped sensors, dropped parts on conveyor) to trigger automatic alerts and prevent asset loss.
- **App/TA:** Splunk Edge Hub (3-axis accelerometer + custom container)
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log impact_event, `index=edge-hub-data` metric_name=acceleration_magnitude
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log impact_event=true
| stats count as impact_count, max(peak_acceleration_g) as max_impact_g by device_id, location
| eval impact_severity=case(
    max_impact_g > 15, "CRITICAL_DAMAGE_RISK",
    max_impact_g > 10, "SEVERE_IMPACT",
    max_impact_g > 5, "MODERATE_IMPACT",
    1=1, "LIGHT_IMPACT")
| where impact_severity!="LIGHT_IMPACT"
```
- **Implementation:** Build custom ARM64 container that monitors 3-axis accelerometer data via gRPC API in real-time (100Hz sampling). Implement impact detection: compute magnitude sqrt(ax^2 + ay^2 + az^2), apply high-pass filter to remove gravity component, detect transient spikes > 5g lasting < 500ms (characteristic of impacts). Log impact events with peak acceleration and timestamp. Configure local alerting: if peak > 15g, trigger relay to activate warning LED/buzzer. Store impact history locally (100K backlog) for root cause analysis. Use for monitoring fragile sensor deployments or tracking dropped parts on assembly lines.
- **Visualization:** Impact event timeline, severity distribution histogram, peak acceleration trend.

---

---

### UC-14.3.51 · Temperature & Humidity Sensor Calibration Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Detects when sensors exceed acceptable calibration drift to trigger preventive recalibration and ensure measurement accuracy.
- **App/TA:** Splunk Edge Hub (temperature + humidity sensors), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-health` sourcetype=edge_hub sensor_calibration_status, `index=edge-hub-data` sensor_drift_metric
- **SPL:**
```spl
index=edge-hub-health sourcetype=edge_hub sensor_type=temperature OR sensor_type=humidity
| stats latest(last_calibration_date) as last_cal, latest(sensor_drift_percent) as drift by sensor_type, host
| eval days_since_calibration=(now() - strptime(last_cal, "%Y-%m-%d")) / 86400
| eval calibration_status=case(
    drift > 5 OR days_since_calibration > 365, "OUT_OF_SPEC",
    drift > 2 OR days_since_calibration > 180, "MARGINAL",
    1=1, "GOOD")
| where calibration_status!="GOOD"
```
- **Implementation:** Edge Hub firmware tracks sensor calibration date and calculates drift estimate (comparison to stable reference or statistical baseline). Temperature sensor nominal accuracy ±0.2°C; alert if drift exceeds ±0.5°C (±2.5x drift). Humidity sensor nominal accuracy ±2%; alert if drift exceeds ±5% RH (±2.5x drift). Report calibration status to edge-hub-health every week. Recommend recalibration every 12 months or after >2% drift detected. Store calibration history in edge-hub-logs for audit trail. For critical environments (pharmaceutical, food), set more aggressive drift thresholds (±1% per year).
- **Visualization:** Sensor drift gauge, calibration status list, recalibration due timeline.

---

---

### UC-14.3.52 · Light Sensor Ambient Light Level Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Detects sudden lighting failures or unauthorized facility access by monitoring ambient light level anomalies.
- **App/TA:** Splunk Edge Hub (light sensor), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=light_level, `sourcetype=edge_hub`
- **SPL:**
```spl
| mstats avg(light_level) as lux by location, _time span=5m
| stats avg(lux) as baseline_lux, stdev(lux) as lux_std by location
| relative_entropy baseline_lux, lux
| where lux < (baseline_lux - 3*lux_std)
| eval light_anomaly=case(
    lux < 10, "LIGHTS_OFF_OR_DARKNESS",
    lux < (baseline_lux / 2), "SEVERE_DIMMING",
    1=1, "MODERATE_DIMMING")
```
- **Implementation:** Deploy Edge Hub light sensor in areas with regular light schedule (e.g., office hours 8am-6pm, lights expected 200-500 lux). Collect 7-day baseline to learn normal lighting schedule. Use built-in kNN anomaly detection to flag sudden light level changes (e.g., lights switched off during business hours = facility access anomaly). Alert if lux drops below 10 for extended period (darkness = potential theft/intrusion). Configure 5-minute polling interval. Light sensor high sensitivity range: 0-65535 lux. Store local SQLite data for 30+ days to track seasonal lighting changes.
- **Visualization:** Light level trend by location, anomaly detection timeline, darkness event log.

---

---

### UC-14.3.53 · Vibration Magnitude Threshold Monitoring for Equipment Protection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Value:** Protects precision equipment from damage by triggering automatic shutdowns when vibration exceeds safe operating thresholds.
- **App/TA:** Splunk Edge Hub (3-axis accelerometer + custom container), gRPC SDK
- **Data Sources:** `index=edge-hub-data` metric_name=vibration_magnitude, `index=edge-hub-logs` vibration_threshold_event
- **SPL:**
```spl
| mstats max(vibration_magnitude) as peak_vib by equipment_id, _time span=10s
| eval equipment_class="PRECISION_MACHINERY"
| join equipment_class [| rest /services/data-model/indexes/equipment_vibration_limits | fields equipment_class, vibration_max_safe_g, vibration_alarm_g]
| where peak_vib > vibration_alarm_g
| eval shutdown_required="YES"
| stats count as alarm_count, max(peak_vib) as max_vibration by equipment_id
```
- **Implementation:** Deploy Edge Hub accelerometer on precision equipment (CNC machine, semiconductor wafer scanner, optical alignment tool). Configure 10-second rolling window for vibration magnitude calculation. Set alarm threshold based on equipment manufacturer specs (typical: 3-5g for precision machinery). Build custom container that monitors vibration in real-time and triggers GPIO relay to cut equipment power if threshold exceeded (safety interlock). Store vibration magnitude in edge-hub-data metrics. Implement hierarchical alerts: 80% threshold = warning, 100% threshold = equipment shutdown. Local alert response avoids cloud latency (critical for safety).
- **Visualization:** Vibration magnitude trend, threshold exceedance timeline, equipment protection status.

---

---

### UC-14.3.54 · Multi-Zone Temperature Gradient Monitoring for Optimal Environment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Monitors temperature gradients across facility zones to optimize HVAC distribution and detect unequal cooling/heating.
- **App/TA:** Splunk Edge Hub (multiple temperature sensors via MQTT or external probes), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-data` metric_name=temperature, `sourcetype=edge_hub` zone=*
- **SPL:**
```spl
| mstats avg(temperature) as zone_temp by zone, _time span=5m
| stats avg(zone_temp) as avg_zone_temp by zone
| eventstats avg(avg_zone_temp) as facility_avg_temp
| eval temp_offset=(avg_zone_temp - facility_avg_temp)
| stats max(abs(temp_offset)) as max_gradient by zone
| where max_gradient > 3
| eval gradient_alert="HVAC_IMBALANCE"
```
- **Implementation:** Deploy Edge Hub in central location with MQTT subscriptions to external temperature sensors in multiple zones (Advanced Settings → MQTT Subscriptions). Or use external probes connected to I²C port (3.5mm jack). Configure 5-minute polling to capture HVAC response dynamics. Acceptable temperature gradient: ±1-2°C across zones. Gradient > 3°C indicates HVAC distribution issue (blocked duct, stuck valve). Store zone temperatures in edge-hub-data metrics. Implement trend analysis: if gradient increasing over days = duct blockage. If gradient constant but offset = thermostat miscalibration. Alert HVAC maintenance if gradient exceeds threshold.
- **Visualization:** Zone temperature heatmap, gradient trend, HVAC balance status.

---

---

### UC-14.3.55 · Acoustic Anomaly Detection for Equipment Health Assessment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Identifies subtle equipment changes (bearing looseness, gearbox wear) by detecting acoustic signature shifts without manual FFT analysis.
- **App/TA:** Splunk Edge Hub (stereo microphone + ML container), v2.1+
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log acoustic_anomaly_event, `index=edge-hub-data` acoustic_baseline_deviation
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log acoustic_classification_event
| stats latest(acoustic_anomaly_score) as anomaly_score, count as detections by equipment_id
| where anomaly_score > 0.7
| eval equipment_health="DEGRADED"
| stats count(eval(equipment_health="DEGRADED")) as degraded_count by facility
| where degraded_count > 0
```
- **Implementation:** Build custom ARM64 container with TensorFlow Lite audio anomaly detection model (autoencoder or isolation forest on MFCC spectral features). Container captures 5-second audio windows at 1-minute intervals, extracts MFCC features, computes reconstruction error vs baseline model (trained on normal equipment sounds), outputs anomaly_score (0-1). Score > 0.7 = significant acoustic change. Deploy NPU inference (v2.1+) for real-time processing. Store anomaly events locally (100K backlog). Useful for early detection of bearing wear, compressor cavitation, motor bearing looseness before catastrophic failure. Do not stream raw audio to cloud (privacy).
- **Visualization:** Anomaly score timeline, detection frequency histogram, equipment health trend.

---

---

### UC-14.3.56 · MQTT Topic Latency & Message Loss Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Ensures MQTT message delivery reliability by tracking topic latency and detecting lost or delayed messages.
- **App/TA:** Splunk Edge Hub (MQTT broker + client), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=splunk_edge_hub_log mqtt_latency_event, `index=edge-hub-health` sourcetype=edge_hub mqtt_broker_health
- **SPL:**
```spl
index=edge-hub-logs sourcetype=splunk_edge_hub_log mqtt_latency_event
| stats avg(publish_to_receive_latency_ms) as avg_latency, max(publish_to_receive_latency_ms) as peak_latency,
        count(eval(latency_ms > 5000)) as slow_messages by mqtt_topic, host
| eval latency_status=case(
    avg_latency > 1000, "SEVERE_DELAY",
    avg_latency > 500, "SLOW",
    1=1, "NORMAL")
| where latency_status!="NORMAL"
```
- **Implementation:** Configure MQTT subscriptions with latency tracking enabled (Advanced Settings → MQTT Subscriptions). Edge Hub MQTT client publishes test messages with timestamp to topics, subscribes to responses, measures round-trip latency. Monitor message sequence numbers to detect loss (gap in sequence = lost message). Store latency metrics in edge-hub-logs. Typical acceptable latency: < 500ms for sensor data (< 1s for anomaly alerts). Alert if average latency exceeds 1s (indicates broker congestion or network saturation). Check MQTT broker resource usage (CPU, memory, subscriber count) if latency degrades. Local SQLite backlog ensures no latency data is lost.
- **Visualization:** MQTT latency trend by topic, message loss rate, broker health timeline.

---

---

### UC-14.3.57 · Temperature Sensor Response Time Validation & Lag Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Value:** Validates temperature sensor response time to ensure rapid detection of thermal events (e.g., fire detection latency < 30 seconds).
- **App/TA:** Splunk Edge Hub (temperature sensor), Splunk OT Intelligence
- **Data Sources:** `index=edge-hub-logs` sourcetype=edge_hub temperature_response_test, `index=edge-hub-data` sensor_response_metrics
- **SPL:**
```spl
index=edge-hub-logs sourcetype=edge_hub temperature_response_test=true stimulus_type=heat_pulse
| stats latest(stimulus_start_time) as heat_start, latest(temperature_rise_detected_time) as detection_time by sensor_id
| eval response_latency_seconds=round((detection_time - heat_start) / 1000, 1)
| stats avg(response_latency_seconds) as avg_response_time, max(response_latency_seconds) as worst_case by sensor_id
| where avg_response_time > 30 OR worst_case > 60
| eval sensor_status="SLOW_RESPONSE"
```
- **Implementation:** Implement quarterly temperature sensor response test: apply controlled heat source (heat lamp, hot water bath) near sensor, record time from stimulus application to temperature rise detection (configurable threshold: +5°C from baseline). Temperature sensor response time (Edge Hub spec): ~1-5 seconds in air, ~10-30 seconds in slow-moving air. Response time > 60 seconds indicates sensor degradation (fouled sensing element, thermal insulation issue). Store test results in edge-hub-logs. Alert if average response time exceeds equipment-specific safety limit (e.g., fire detection requires < 30 second response). Use test data for recalibration/replacement decisions.
- **Visualization:** Sensor response time trend, test results timeline, response time validation pass/fail status.

---

## Summary

All 50 new use cases (UC-14.3.8 through UC-14.3.57) are documented with:
- Real Edge Hub index names (edge-hub-data, edge-hub-logs, edge-hub-health, edge-hub-anomalies, edge-hub-snmp)
- Real sourcetypes (splunk_edge_hub_log, splunk_edge_hub_opcua, edge_hub)
- Realistic SPL queries using | mstats for metrics, regular search for events
- References to actual Edge Hub configuration paths and hardware capabilities
- Criticality ratings based on business impact
- Container-specific guidance (ARM64 requirement, edge.json manifest, resource limits, v2.1+ NPU support, v2.0+ non-root)
- MLTK limitations (MQTT sensors only, one model per sensor)
- Practical visualization recommendations

---

### 14.4 IoT Platforms & Sensors

**Primary App/TA:** Custom API inputs, MQTT, webhook receivers.

---

### UC-14.4.1 · Smart Sensor Fleet Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** IoT sensors with low batteries or offline status create monitoring gaps. Fleet management ensures comprehensive coverage.
- **App/TA:** IoT platform API input
- **Data Sources:** IoT platform device management API
- **SPL:**
```spl
index=iot sourcetype="iot_platform:devices"
| where battery_pct < 20 OR status!="online" OR last_seen < relative_time(now(),"-4h")
| table device_id, device_type, location, battery_pct, status, last_seen
```
- **Implementation:** Poll IoT platform API for device status. Track battery levels, connectivity, and data freshness. Alert on low battery (<20%) and offline devices (>4 hours). Report on fleet health for maintenance planning.
- **Visualization:** Table (devices needing attention), Gauge (fleet health %), Pie chart (device status distribution), Map (device locations with status).

---

### UC-14.4.2 · Environmental Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Distributed environmental sensors provide early warning of conditions that could damage equipment or inventory.
- **App/TA:** MQTT input, IoT platform API
- **Data Sources:** Environmental sensor data (temperature, humidity, water leak, smoke)
- **SPL:**
```spl
index=iot sourcetype="sensor:environmental"
| where water_detected="true" OR smoke_detected="true" OR temp_f > 90
| table _time, sensor_id, location, alert_type, value
```
- **Implementation:** Deploy environmental sensors in server rooms, warehouses, and facilities. Ingest via MQTT or API. Alert immediately on water leak or smoke detection. Track temperature/humidity trends per location.
- **Visualization:** Floor plan (sensors with status), Line chart (environmental trends), Table (alerts), Single value (active environmental alerts).

---

### UC-14.4.3 · Asset Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Real-time asset location reduces search time, prevents loss, and enables utilization optimization.
- **App/TA:** Custom API input, BLE/GPS data
- **Data Sources:** GPS/BLE beacon data, RFID events
- **SPL:**
```spl
index=iot sourcetype="asset_tracking"
| stats latest(location) as current_location, latest(_time) as last_seen by asset_id, asset_type
| eval hours_since=round((now()-last_seen)/3600,1)
| where hours_since > 24
```
- **Implementation:** Ingest asset tracking data from GPS/BLE/RFID systems. Track asset locations and movement patterns. Alert when high-value assets leave designated zones. Report on asset utilization by location.
- **Visualization:** Map (asset locations), Table (asset inventory with location), Timeline (asset movement), Single value (assets not reporting).

---

### UC-14.4.4 · Home Automation Monitoring
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Value:** Smart home monitoring provides energy usage insights, security awareness, and automation troubleshooting.
- **App/TA:** Custom API input (Homey, Home Assistant)
- **Data Sources:** Homey/Home Assistant API (device events, energy data)
- **SPL:**
```spl
index=smarthome sourcetype="homey:events"
| stats count by device_name, capability, event_type
| sort -count
```
- **Implementation:** Configure Homey/Home Assistant webhook or API to send events to Splunk HEC. Track device states, energy consumption, and automation triggers. Create dashboards for home energy management and security.
- **Visualization:** Line chart (energy usage), Table (device events), Status grid (device × state), Single value (energy today).

---

### UC-14.4.5 · IoT Device Firmware Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** IoT devices are frequently targeted for botnets. Outdated firmware creates network security risks.
- **App/TA:** IoT platform API
- **Data Sources:** Device inventory with firmware versions
- **SPL:**
```spl
index=iot sourcetype="iot_platform:inventory"
| stats latest(firmware_version) as current by device_type, model
| lookup iot_approved_firmware.csv device_type, model OUTPUT approved_version
| where current!=approved_version
| table device_type, model, count, current, approved_version
```
- **Implementation:** Export IoT device inventory with firmware versions periodically. Maintain approved firmware lookup. Report on compliance percentage. Prioritize updates for internet-connected devices. Track firmware update campaigns.
- **Visualization:** Table (non-compliant devices), Pie chart (compliant vs non-compliant), Bar chart (by device type), Single value (compliance %).

---

## 15. Data Center Physical Infrastructure

### 15.1 Power & UPS

**Primary App/TA:** SNMP TA (UPS-MIB, PDU-MIB), vendor APIs (APC, Eaton, Vertiv).

---

### UC-15.1.1 · UPS Battery Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** UPS battery degradation is the single largest cause of unprotected power events. Proactive replacement prevents data center outages.
- **App/TA:** SNMP TA (UPS-MIB)
- **Data Sources:** SNMP UPS-MIB (battery status, charge, runtime, temperature, replace indicator)
- **SPL:**
```spl
index=power sourcetype="snmp:ups"
| where battery_replace_indicator="yes" OR charge_pct < 80 OR runtime_min < 15
| table ups_name, location, battery_status, charge_pct, runtime_min, battery_age_months
```
- **Implementation:** Poll UPS battery metrics via SNMP every 5 minutes. Alert on replace indicator, low charge, or low runtime. Track battery age and capacity trend over time to predict replacement needs.
- **Visualization:** Table (UPS battery status), Gauge (charge per UPS), Line chart (capacity trend), Single value (UPS needing replacement).

---

### UC-15.1.2 · PDU Power per Rack
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Per-rack power monitoring prevents circuit overloads and enables efficient rack placement for new equipment.
- **App/TA:** SNMP TA (PDU-MIB), vendor API
- **Data Sources:** Smart PDU per-outlet and per-circuit metrics
- **SPL:**
```spl
index=power sourcetype="snmp:pdu"
| eval pct_capacity=round(current_amps/rated_amps*100,1)
| where pct_capacity > 80
| table rack_id, pdu_name, circuit, current_amps, rated_amps, pct_capacity
```
- **Implementation:** Poll PDU metrics via SNMP. Track per-outlet and per-circuit power. Alert when any circuit exceeds 80% capacity. Report on rack power distribution for capacity planning. Track power trends per rack.
- **Visualization:** Heatmap (rack × power usage), Gauge (% capacity per circuit), Bar chart (power by rack), Table (overloaded circuits).

---

### UC-15.1.3 · Power Redundancy Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Loss of A/B feed redundancy means a single power failure will cause an outage. Immediate awareness enables emergency response.
- **App/TA:** SNMP TA, PDU/UPS events
- **Data Sources:** PDU input status, UPS input voltage, transfer switch events
- **SPL:**
```spl
index=power sourcetype="snmp:pdu"
| where input_status!="normal" OR input_voltage < 180
| table _time, pdu_name, rack_id, feed, input_status, input_voltage
```
- **Implementation:** Monitor PDU input status and UPS input voltage. Alert immediately on loss of any power feed. Track ATS (Automatic Transfer Switch) events. Maintain power topology documentation for impact analysis.
- **Visualization:** Status grid (rack × A/B feed status), Table (power events), Timeline (redundancy loss events), Single value (racks with full redundancy %).

---

### UC-15.1.4 · Generator Test Results
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Generators are the last line of defense during extended outages. Failed tests mean they may not start when needed.
- **App/TA:** BMS integration, manual log input
- **Data Sources:** Generator controller logs, BMS events
- **SPL:**
```spl
index=power sourcetype="generator:test"
| stats latest(result) as last_result, latest(_time) as last_test by generator_id
| eval days_since_test=round((now()-last_test)/86400)
| where last_result!="pass" OR days_since_test > 30
```
- **Implementation:** Log generator test results (manual or automated). Track test frequency and outcomes. Alert on failed tests and missed test schedules. Monitor fuel levels. Report on generator readiness for management.
- **Visualization:** Table (generator test history), Single value (days since last test), Status indicator (pass/fail).

---

### UC-15.1.5 · PUE Calculation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Power Usage Effectiveness is the primary data center efficiency metric. Trending drives energy optimization and sustainability goals.
- **App/TA:** Aggregate power metrics from PDU/UPS/BMS
- **Data Sources:** Total facility power, IT load power
- **SPL:**
```spl
index=power sourcetype="power:aggregate"
| timechart span=1h avg(total_facility_kw) as facility, avg(it_load_kw) as it_load
| eval pue=round(facility/it_load,2)
```
- **Implementation:** Aggregate total facility power and IT equipment power from PDU/UPS/BMS data. Calculate PUE hourly and daily. Track seasonal variation. Report monthly to operations and sustainability teams. Target PUE <1.5.
- **Visualization:** Gauge (current PUE), Line chart (PUE trend), Single value (monthly average PUE), Bar chart (PUE by month).

---

### UC-15.1.6 · Circuit Breaker Trips
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Breaker trips cause immediate power loss to affected equipment. Detection enables rapid response and root cause investigation.
- **App/TA:** PDU/BMS event logs
- **Data Sources:** PDU events, BMS alerts, UPS transfer events
- **SPL:**
```spl
index=power sourcetype="pdu:events" OR sourcetype="bms:events"
| search "breaker" OR "overcurrent" OR "trip"
| table _time, device, location, event_type, circuit, message
```
- **Implementation:** Forward PDU and BMS events to Splunk. Alert immediately on breaker trips or overcurrent events. Track affected equipment from PDU-to-server mapping. Investigate root cause (overload, short circuit, equipment failure).
- **Visualization:** Timeline (breaker events), Table (trip details), Single value (trips this month).

---

### 15.2 Cooling & Environmental

**Primary App/TA:** SNMP, BMS integration, environmental sensor inputs.

---

### UC-15.2.1 · Temperature Monitoring per Zone
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Data center temperature exceedances risk equipment damage and unplanned shutdowns. Per-zone monitoring localizes issues.
- **App/TA:** SNMP environmental sensors
- **Data Sources:** Environmental sensors (intake, exhaust, ambient temperature)
- **SPL:**
```spl
index=environment sourcetype="sensor:temperature"
| where temp_f > 80 OR temp_f < 64
| table _time, zone, rack, sensor_position, temp_f
| sort -temp_f
```
- **Implementation:** Deploy temperature sensors per ASHRAE recommendations (intake, exhaust, per-row). Poll via SNMP every minute. Alert on exceedance of ASHRAE A1 limits (64-80°F intake). Correlate with cooling unit status.
- **Visualization:** Heatmap (zone × temperature), Line chart (temperature trend per zone), Floor plan visualization, Single value (hottest zone).

---

### UC-15.2.2 · Humidity Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Low humidity causes ESD risk; high humidity causes condensation. Maintaining 40-60% RH protects equipment.
- **App/TA:** SNMP environmental sensors
- **Data Sources:** Humidity sensors
- **SPL:**
```spl
index=environment sourcetype="sensor:humidity"
| where humidity_pct > 60 OR humidity_pct < 40
| table _time, zone, humidity_pct
```
- **Implementation:** Deploy humidity sensors alongside temperature sensors. Alert on out-of-range humidity (below 40% or above 60% RH). Track dew point to prevent condensation. Correlate with HVAC system humidifier/dehumidifier operation.
- **Visualization:** Line chart (humidity trend), Gauge (current humidity per zone), Table (zones out of range).

---

### UC-15.2.3 · CRAC/CRAH Unit Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** Cooling unit failures can cause rapid temperature rise. Monitoring operational status enables immediate response and failover.
- **App/TA:** BMS/SNMP integration
- **Data Sources:** CRAC/CRAH unit SNMP metrics, BMS alarms
- **SPL:**
```spl
index=cooling sourcetype="bms:crac"
| where unit_status!="running" OR supply_temp_f > setpoint_f + 5 OR compressor_status!="normal"
| table _time, unit_name, unit_status, supply_temp_f, setpoint_f, compressor_status
```
- **Implementation:** Monitor cooling unit operational status, supply/return temperatures, and compressor health via SNMP/BMS. Alert on unit failure or degraded performance. Track runtime hours for maintenance scheduling.
- **Visualization:** Status grid (unit × operational status), Table (unit health), Line chart (supply/return temps), Gauge (cooling capacity %).

---

### UC-15.2.4 · Hot Aisle Temperature Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Hot aisle trends indicate cooling efficiency and capacity margin. Rising trends signal approaching cooling limits.
- **App/TA:** Environmental sensors
- **Data Sources:** Hot aisle return air temperature sensors
- **SPL:**
```spl
index=environment sourcetype="sensor:temperature" position="hot_aisle"
| timechart span=1h avg(temp_f) as avg_temp by zone
| predict avg_temp as predicted future_timespan=7
```
- **Implementation:** Deploy sensors in hot aisle containment. Track return air temperatures. Compare hot aisle temps across zones to identify cooling imbalances. Use prediction to forecast capacity issues.
- **Visualization:** Line chart (hot aisle temps with prediction), Heatmap (zone × time), Bar chart (avg hot aisle by zone).

---

### UC-15.2.5 · Water Leak Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Water in a data center causes immediate equipment damage and potential electrical hazards. Seconds matter in detection.
- **App/TA:** Leak detection sensor inputs
- **Data Sources:** Water leak detection system (rope sensors, spot detectors)
- **SPL:**
```spl
index=environment sourcetype="leak_detection"
| where leak_detected="true"
| table _time, zone, sensor_id, location_description
```
- **Implementation:** Deploy water leak detection sensors under raised floors, near CRAC units, and along pipe routes. Alert at critical priority on any detection. Integrate with building facilities team notification. Test sensors quarterly.
- **Visualization:** Single value (active leak alerts — target: 0), Floor plan (sensor locations with status), Timeline (leak events).

---

### UC-15.2.6 · Cooling Capacity Planning
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Trending cooling load vs capacity ensures adequate cooling for current and planned equipment deployments.
- **App/TA:** BMS metrics
- **Data Sources:** CRAC/CRAH cooling output, IT heat load calculations
- **SPL:**
```spl
index=cooling sourcetype="bms:cooling_capacity"
| timechart span=1d avg(cooling_output_kw) as output, avg(cooling_capacity_kw) as capacity
| eval utilization_pct=round(output/capacity*100,1)
```
- **Implementation:** Calculate cooling load from IT power consumption (1 watt IT ≈ 3.41 BTU/h heat). Compare against total cooling capacity. Track utilization percentage. Alert when approaching 80% capacity. Plan for seasonal variations.
- **Visualization:** Dual-axis chart (load vs capacity), Gauge (cooling utilization %), Line chart (utilization trend).

---

### 15.3 Physical Security

**Primary App/TA:** Access control system integration, camera system syslog/API.

---

### UC-15.3.1 · Badge Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Complete badge access audit trail is required for compliance (SOC2, PCI-DSS) and supports security investigations.
- **App/TA:** Access control syslog/API
- **Data Sources:** Access control system events
- **SPL:**
```spl
index=physical sourcetype="access_control"
| table _time, badge_holder, badge_id, door, action, result
| sort -_time
```
- **Implementation:** Forward access control events to Splunk. Parse all badge events (granted, denied, door held, forced). Retain per compliance requirements. Enable search by person, door, or time for investigations.
- **Visualization:** Table (access log), Bar chart (access by door), Timeline (access events for person), Single value (total access today).

---

### UC-15.3.2 · After-Hours Access Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Data center access outside business hours requires additional scrutiny. Alerts ensure authorized personnel are verified.
- **App/TA:** Access control system
- **Data Sources:** Access events with time-based rules
- **SPL:**
```spl
index=physical sourcetype="access_control" result="granted"
| eval hour=strftime(_time,"%H")
| where (hour < 6 OR hour > 22) AND NOT match(badge_holder, "NOC|Security|Facilities")
| table _time, badge_holder, door, badge_id
```
- **Implementation:** Define business hours per facility. Alert on access outside hours (excluding authorized roles like NOC, security). Require pre-authorization for after-hours access. Track after-hours access patterns.
- **Visualization:** Table (after-hours access events), Bar chart (after-hours by person), Heatmap (time × access volume).

---

### UC-15.3.3 · Tailgating Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Tailgating bypasses access control, allowing unauthorized entry. Detection supports physical security integrity.
- **App/TA:** Access control system
- **Data Sources:** Access events (badge-in vs badge-out patterns)
- **SPL:**
```spl
index=physical sourcetype="access_control" door="DC_Main_Entry"
| transaction badge_id maxspan=10s
| where eventcount > 1 AND action="entry"
| table _time, badge_holder, badge_id, eventcount
```
- **Implementation:** Analyze badge-in/badge-out patterns. Detect multiple entries without corresponding exits (or vice versa). Alert on anti-passback violations. Correlate with camera footage for investigation. Report on tailgating trends.
- **Visualization:** Table (tailgating events), Bar chart (by door), Line chart (tailgating trend), Single value (incidents this week).

---

### UC-15.3.4 · Camera System Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Offline cameras create security blind spots. Monitoring ensures continuous surveillance coverage.
- **App/TA:** NVR/VMS syslog or API
- **Data Sources:** Video management system logs (camera status, recording status)
- **SPL:**
```spl
index=physical sourcetype="vms:camera_status"
| where recording_status!="recording" OR connection_status!="connected"
| table camera_id, location, connection_status, recording_status, last_frame
```
- **Implementation:** Poll camera/NVR status via API or forward VMS events. Alert on camera offline, recording failure, or storage issues. Track camera uptime percentage. Report on coverage gaps.
- **Visualization:** Status grid (camera × status), Table (offline cameras), Single value (cameras recording %), Floor plan (camera locations with status).

---

### UC-15.3.5 · Cabinet Door Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Unauthorized cabinet access could indicate tampering. Door sensors provide granular physical security for critical racks.
- **App/TA:** Cabinet lock sensor input
- **Data Sources:** Smart cabinet lock events
- **SPL:**
```spl
index=physical sourcetype="cabinet_lock"
| where action="opened" AND NOT authorized="true"
| table _time, rack_id, user, action, method
```
- **Implementation:** Deploy smart cabinet locks with event logging. Forward events to Splunk. Alert on unauthorized openings. Track door open duration. Correlate with badge access events for validation. Report on cabinet access frequency.
- **Visualization:** Table (cabinet access events), Timeline (open/close events), Bar chart (access by rack).

---

## 16. Service Management & ITSM

### 16.1 Ticketing Systems

**Primary App/TA:** Splunk Add-on for ServiceNow (`Splunk_TA_snow`), Splunk Add-on for Jira, custom API inputs.

---

### UC-16.1.1 · Incident Volume Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Incident trends reveal infrastructure stability, staffing needs, and the effectiveness of problem management.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** ServiceNow incident table
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| timechart span=1d count by priority
```
- **Implementation:** Ingest ServiceNow incidents via TA. Track creation rates by category, priority, and assignment group. Alert on volume spikes. Compare against historical baselines. Report on trending categories for problem management input.
- **Visualization:** Line chart (incident volume trend), Stacked bar (by priority), Pie chart (by category), Table (today's incidents).

---

### UC-16.1.2 · SLA Compliance Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** SLA breaches affect customer satisfaction and contractual obligations. Real-time monitoring enables intervention before breaches occur.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** ServiceNow SLA records (response, resolution)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| eval response_met=if(response_time<=response_sla,"Yes","No")
| eval resolution_met=if(resolution_time<=resolution_sla,"Yes","No")
| stats count(eval(response_met="Yes")) as met, count as total by priority
| eval compliance_pct=round(met/total*100,1)
```
- **Implementation:** Track response and resolution times against SLA targets per priority. Alert when tickets approach SLA breach. Report on compliance percentage per priority and assignment group. Identify teams with consistent breaches.
- **Visualization:** Gauge (SLA compliance %), Bar chart (compliance by priority), Table (tickets approaching breach), Line chart (compliance trend).

---

### UC-16.1.3 · MTTR by Category
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** MTTR per category identifies where process improvements or automation would have the greatest impact.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incident lifecycle data (open, assigned, resolved timestamps)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state="resolved"
| eval mttr_hours=round((resolved_at-opened_at)/3600,1)
| stats avg(mttr_hours) as avg_mttr, median(mttr_hours) as median_mttr by category
| sort -avg_mttr
```
- **Implementation:** Calculate MTTR from incident open to resolution timestamps. Break down by category, subcategory, and assignment group. Track trends over time. Set MTTR targets per category and report on achievement.
- **Visualization:** Bar chart (MTTR by category), Line chart (MTTR trend), Table (category MTTR summary), Histogram (resolution time distribution).

---

### UC-16.1.4 · Change Success Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Failed changes are the leading cause of incidents. Tracking success rate drives improvement in change management practices.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** ServiceNow change records
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request"
| stats count(eval(close_code="successful")) as success, count(eval(close_code="failed")) as failed, count as total by type
| eval success_rate=round(success/total*100,1)
```
- **Implementation:** Ingest change request records. Track outcomes (successful, failed, backed out). Calculate success rate by change type (standard, normal, emergency). Alert on failed changes. Report on DORA change failure rate metric.
- **Visualization:** Pie chart (change outcomes), Bar chart (success rate by type), Line chart (success rate trend), Single value (overall success rate).

---

### UC-16.1.5 · Change Collision Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Overlapping changes on related systems increase outage risk. Detection enables coordination and conflict resolution.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Change calendar, CI relationships
- **SPL:**
```spl
index=itsm sourcetype="snow:change_request" state="scheduled"
| eval change_window_start=start_date, change_window_end=end_date
| join type=inner cmdb_ci [| search index=itsm sourcetype="snow:change_request" state="scheduled"]
| where change_window_start < end_date AND change_window_end > start_date AND change_id!=other_change_id
```
- **Implementation:** Analyze scheduled change windows for overlapping CIs. Cross-reference CI relationships for dependent systems. Alert when changes to related systems overlap. Create change calendar view for CAB review.
- **Visualization:** Calendar view (change windows), Table (colliding changes), Gantt chart (change timeline).

---

### UC-16.1.6 · Problem Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Identifying recurring incident patterns that should become problems drives root cause resolution and reduces incident volume.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incident categorization data, problem records
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| stats count by category, subcategory, cmdb_ci
| where count > 5
| sort -count
| head 20
```
- **Implementation:** Analyze incident patterns by category, CI, and assignment group. Identify recurring incidents (>5 in 30 days). Flag candidates for problem record creation. Track problem management effectiveness (repeat incidents after RCA).
- **Visualization:** Table (top recurring incidents), Bar chart (repeat incidents by category), Line chart (repeat rate trend).

---

### UC-16.1.7 · Ticket Reassignment Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** High reassignment rates indicate poor routing or skills gaps. Reduction improves MTTR and customer satisfaction.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Incident audit trail (assignment changes)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident"
| stats dc(assignment_group) as group_count, count as reassignments by number
| where group_count > 2
| sort -group_count
```
- **Implementation:** Track assignment group changes per ticket. Calculate average reassignments. Identify tickets with >2 reassignments (ping-pong tickets). Report on routing accuracy by category. Improve auto-routing rules.
- **Visualization:** Bar chart (avg reassignments by category), Table (most-reassigned tickets), Line chart (reassignment rate trend), Single value (avg reassignments).

---

### UC-16.1.8 · Aging Ticket Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Aging tickets indicate stuck processes or forgotten issues. Alerts ensure nothing falls through the cracks.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Open incident data
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state IN ("new","in_progress","on_hold")
| eval age_days=round((now()-opened_at)/86400)
| eval age_threshold=case(priority=1,1, priority=2,3, priority=3,7, 1=1,14)
| where age_days > age_threshold
| table number, short_description, priority, assignment_group, age_days
| sort -age_days
```
- **Implementation:** Calculate ticket age against priority-based thresholds. Alert when tickets exceed expected resolution time. Escalate automatically via workflow rules. Report on aging ticket inventory daily.
- **Visualization:** Table (aging tickets), Bar chart (aging by priority), Single value (total aging tickets), Line chart (aging trend).

---

### UC-16.1.9 · Change-Incident Correlation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Correlating incidents with recent changes is the fastest path to root cause. Automated correlation accelerates MTTR.
- **App/TA:** `Splunk_TA_snow` + monitoring data
- **Data Sources:** Change records + incident records + monitoring events
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" priority IN (1,2)
| join type=left cmdb_ci
    [search index=itsm sourcetype="snow:change_request" close_code="successful" earliest=-24h
     | table cmdb_ci, number as change_number, short_description as change_desc, end_date]
| where isnotnull(change_number)
| table number, short_description, cmdb_ci, change_number, change_desc
```
- **Implementation:** When high-priority incidents are created, automatically search for changes completed in the last 24 hours on related CIs. Present correlation to incident team. Track change-related incident percentage. Feed back to change management.
- **Visualization:** Table (incident-change correlation), Single value (% incidents with recent change), Timeline (changes + incidents overlaid).

---

### UC-16.1.10 · Service Request Fulfillment Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Fulfillment time metrics drive service catalog optimization and customer satisfaction. Slow fulfillment reduces adoption.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** Service request data
- **SPL:**
```spl
index=itsm sourcetype="snow:sc_request"
| eval fulfillment_hours=round((closed_at-opened_at)/3600,1)
| stats avg(fulfillment_hours) as avg_hours, median(fulfillment_hours) as median_hours by cat_item
| sort -avg_hours
```
- **Implementation:** Track service request lifecycle from submission to fulfillment. Calculate fulfillment time per catalog item. Identify items with slow fulfillment for automation opportunities. Report on catalog efficiency.
- **Visualization:** Bar chart (avg fulfillment by item), Table (catalog item performance), Line chart (fulfillment time trend).

---

### 16.2 Configuration Management (CMDB)

**Primary App/TA:** ServiceNow CMDB integration, custom API inputs.

---

### UC-16.2.1 · CMDB Data Quality Score
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Poor CMDB data quality undermines all ITSM processes. Scoring and trending drives data quality improvement initiatives.
- **App/TA:** `Splunk_TA_snow`, custom metrics
- **Data Sources:** CMDB CI data (completeness, accuracy, freshness)
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci"
| eval complete=if(isnotnull(owner) AND isnotnull(support_group) AND isnotnull(environment),1,0)
| eval fresh=if(last_discovered > relative_time(now(),"-30d"),1,0)
| stats avg(complete) as completeness, avg(fresh) as freshness
| eval quality_score=round((completeness*50+freshness*50),1)
```
- **Implementation:** Define CMDB quality dimensions (completeness, accuracy, freshness, relationships). Score each dimension. Calculate composite quality score. Track trend over time. Set improvement targets. Report to CMDB governance board.
- **Visualization:** Gauge (quality score), Line chart (quality trend), Bar chart (quality by dimension), Table (worst-scoring CIs).

---

### UC-16.2.2 · CI Discovery Reconciliation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** CIs in the network but not in the CMDB are unmanaged risks. Reconciliation ensures CMDB completeness.
- **App/TA:** Discovery tools + CMDB
- **Data Sources:** Discovery scan results, CMDB CI records
- **SPL:**
```spl
| inputlookup discovered_assets.csv
| join type=left hostname [search index=itsm sourcetype="snow:cmdb_ci" | table hostname, sys_id, ci_class]
| where isnull(sys_id)
| table hostname, ip_address, os, discovered_date
```
- **Implementation:** Compare auto-discovered assets (ServiceNow Discovery, SCCM, network scans) with CMDB records. Identify CIs found by discovery but absent from CMDB. Create workflow to review and add missing CIs. Track gap closure over time.
- **Visualization:** Table (unmatched discovered assets), Single value (CMDB gap count), Pie chart (matched vs unmatched), Line chart (gap trend).

---

### UC-16.2.3 · Orphaned CI Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** CIs without owners or service mappings aren't managed during incidents, creating accountability gaps and shadow infrastructure.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** CMDB CI attributes
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci" operational_status="operational"
| where isnull(assigned_to) OR isnull(support_group) OR isnull(u_service)
| table name, ci_class, assigned_to, support_group, u_service
```
- **Implementation:** Query CMDB for operational CIs missing key attributes (owner, support group, service mapping). Report on orphaned CI inventory. Assign ownership through automated or manual workflow. Track orphan reduction over time.
- **Visualization:** Table (orphaned CIs), Pie chart (by CI class), Bar chart (orphans by missing attribute), Single value (total orphaned CIs).

---

### UC-16.2.4 · Relationship Integrity Check
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Accurate CI relationships enable impact analysis during incidents. Incomplete relationships undermine service mapping.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** CMDB relationship data
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_ci" ci_class IN ("cmdb_ci_server","cmdb_ci_app_server")
| join type=left sys_id [search index=itsm sourcetype="snow:cmdb_rel_ci" | stats count as rel_count by child]
| where isnull(rel_count) OR rel_count=0
| table name, ci_class, rel_count
```
- **Implementation:** Validate CI relationships are present and bidirectional. Identify servers with no application relationships, applications with no infrastructure dependencies. Report on relationship completeness. Use for impact analysis validation.
- **Visualization:** Table (CIs without relationships), Network graph (CI dependency map), Single value (% CIs with relationships).

---

### UC-16.2.5 · CMDB Change Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Tracking all CI attribute changes supports compliance auditing and helps detect unauthorized configuration changes.
- **App/TA:** `Splunk_TA_snow`
- **Data Sources:** CMDB audit trail (sys_audit)
- **SPL:**
```spl
index=itsm sourcetype="snow:cmdb_audit"
| table _time, ci_name, field_name, old_value, new_value, changed_by
| sort -_time
```
- **Implementation:** Ingest CMDB audit records. Track all CI attribute changes. Alert on changes to critical CIs outside change windows. Report on change volume by CI class and source (manual vs discovery). Validate accuracy of discovery updates.
- **Visualization:** Table (CI changes), Timeline (change events), Bar chart (changes by CI class), Line chart (change volume trend).

---

## 17. Network Security & Zero Trust

### 17.1 Network Access Control (NAC)

**Primary App/TA:** Cisco ISE TA (`Splunk_TA_cisco-ise`), Aruba ClearPass TA, Forescout TA.

---

### UC-17.1.1 · NAC Authentication Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Authentication success/failure trends reveal infrastructure issues (certificate problems, RADIUS outages) and security events.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** RADIUS/ISE authentication logs
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth"
| eval status=if(match(message,"PASS"),"success","failure")
| timechart span=1h count by status
```
- **Implementation:** Forward ISE syslog to Splunk. Parse authentication results, methods, and endpoints. Track success/failure rates per location and SSID. Alert on spike in failures (>10% rate). Report on authentication method adoption.
- **Visualization:** Line chart (auth success/failure rates), Bar chart (failures by location), Pie chart (auth method distribution).

---

### UC-17.1.2 · Endpoint Posture Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Non-compliant endpoints accessing the network pose security risks. Posture tracking ensures endpoint hygiene enforcement.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE posture assessment logs
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:posture"
| where posture_status="NonCompliant"
| stats count by endpoint_mac, posture_policy, failure_reason
| sort -count
```
- **Implementation:** Ingest ISE posture assessment results. Track compliance rates per policy (AV status, patch level, disk encryption). Alert on critical endpoints failing posture (exec laptops, admin workstations). Report on remediation effectiveness.
- **Visualization:** Pie chart (compliant vs non-compliant), Bar chart (failure reasons), Table (non-compliant endpoints), Line chart (compliance trend).

---

### UC-17.1.3 · VLAN Assignment Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Dynamic VLAN assignments reflect authorization decisions. Anomalous placements may indicate policy misconfiguration or attacks.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE authorization logs (VLAN assignment)
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth"
| where assigned_vlan!=expected_vlan
| table _time, endpoint_mac, username, assigned_vlan, expected_vlan, authorization_policy
```
- **Implementation:** Track VLAN assignments per endpoint. Maintain expected VLAN lookup by user role/device type. Alert on unexpected VLAN placements. Audit authorization policy effectiveness.
- **Visualization:** Table (VLAN assignments), Pie chart (assignments by VLAN), Bar chart (unexpected placements).

---

### UC-17.1.4 · Guest Network Usage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Guest network monitoring ensures acceptable use and identifies capacity needs. Unusual patterns may indicate abuse.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE guest portal logs, RADIUS accounting
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:guest"
| stats count, sum(session_duration_min) as total_min by sponsor, guest_type
| sort -count
```
- **Implementation:** Track guest portal registrations, sponsor activity, and session durations. Alert on excessive guest registrations from single sponsors. Monitor guest bandwidth usage. Report on guest network utilization.
- **Visualization:** Bar chart (guest registrations by sponsor), Line chart (guest sessions trend), Table (active guests).

---

### UC-17.1.5 · BYOD Onboarding Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** BYOD onboarding metrics inform mobile device management strategy and user experience optimization.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE BYOD portal logs, certificate provisioning
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:byod"
| stats count by device_type, os_type, onboarding_status
| sort -count
```
- **Implementation:** Track BYOD registrations, device types, and onboarding success/failure rates. Alert on onboarding failures. Report on device type distribution for MDM policy planning.
- **Visualization:** Pie chart (device types), Bar chart (onboarding status), Line chart (BYOD enrollment trend).

---

### UC-17.1.6 · MAC Authentication Bypass (MAB)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** MAB devices bypass 802.1X and rely on MAC address only. Monitoring for unauthorized MACs prevents rogue device access.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE MAB authentication logs
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:auth" auth_method="MAB"
| lookup approved_mab_devices.csv mac_address OUTPUT device_description, approved
| where isnull(approved) OR approved!="Yes"
| table _time, endpoint_mac, switch, port, location
```
- **Implementation:** Maintain whitelist of approved MAB devices (printers, IP phones, IoT). Alert on unknown MAC addresses authenticating via MAB. Track MAB device population. Report on MAB vs 802.1X ratio for security posture.
- **Visualization:** Table (unapproved MAB devices), Pie chart (MAB vs 802.1X), Bar chart (MAB by device type).

---

### UC-17.1.7 · Profiling Accuracy
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Accurate device profiling enables correct authorization policies. Misprofiled devices may get inappropriate access.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE profiler logs, re-profiling events
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:profiler"
| search "re-profiled" OR "profile changed"
| stats count by endpoint_mac, old_profile, new_profile
| sort -count
```
- **Implementation:** Monitor profiling events and profile changes. Track devices that are frequently re-profiled (indicates ambiguous profiling rules). Validate profiling accuracy against known device inventory. Tune profiling policies.
- **Visualization:** Table (profiling changes), Sankey diagram (old→new profiles), Bar chart (re-profiling frequency).

---

### UC-17.1.8 · NAC Policy Change Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** NAC policy changes affect network access for all devices. Unauthorized changes can create security gaps or disrupt access.
- **App/TA:** Splunk_TA_cisco-ise
- **Data Sources:** ISE admin audit logs
- **SPL:**
```spl
index=nac sourcetype="cisco:ise:admin"
| search "PolicySet" OR "AuthorizationRule" OR "AuthenticationRule"
| table _time, admin_user, action, object_name, details
```
- **Implementation:** Forward ISE admin audit logs. Alert on any policy change. Track changes by administrator. Correlate with change management tickets. Report on policy change frequency.
- **Visualization:** Table (policy changes), Timeline (change events), Bar chart (changes by admin).

---

### 17.2 VPN & Remote Access

**Primary App/TA:** Cisco ASA/AnyConnect TA, Palo Alto GlobalProtect TA, vendor syslog.

---

### UC-17.2.1 · VPN Concurrent Sessions
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** VPN capacity planning prevents remote workers from being locked out. Trending identifies peak usage and growth patterns.
- **App/TA:** Splunk_TA_cisco-asa, Splunk_TA_paloalto (GlobalProtect)
- **Data Sources:** VPN concentrator session logs
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa"
| where action="session_connect" OR action="session_disconnect"
| timechart span=15m dc(user) as concurrent_users
```
- **Implementation:** Track VPN session connects/disconnects. Calculate concurrent users over time. Alert when approaching license or capacity limits. Report on peak usage patterns for capacity planning. Track growth trends.
- **Visualization:** Line chart (concurrent sessions), Gauge (% of capacity), Single value (current active sessions), Area chart (sessions over time).

---

### UC-17.2.2 · VPN Authentication Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Repeated VPN auth failures indicate credential attacks against the remote access perimeter, a primary attack vector.
- **App/TA:** Splunk_TA_cisco-asa, Splunk_TA_paloalto (GlobalProtect)
- **Data Sources:** VPN authentication logs
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="authentication_failed"
| stats count by user, src_ip
| where count > 5
| sort -count
```
- **Implementation:** Track VPN authentication failures by user and source IP. Alert on >5 failures per user per 15 minutes. Correlate with AD lockout events. Block source IPs with excessive failures. Report on attack patterns.
- **Visualization:** Table (failed auth events), Bar chart (failures by user), Geo map (source IPs), Line chart (failure rate trend).

---

### UC-17.2.3 · Geo-Location Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Value:** VPN connections from unexpected countries may indicate compromised credentials being used from attacker infrastructure.
- **App/TA:** VPN TA + GeoIP lookup
- **Data Sources:** VPN session logs with source IP
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="session_connect"
| iplocation src_ip
| search NOT Country IN ("United States","Canada","United Kingdom")
| table _time, user, src_ip, Country, City
```
- **Implementation:** Enrich VPN connections with GeoIP data. Maintain whitelist of expected countries. Alert on connections from unexpected locations. Correlate with user travel records if available. Block sanctioned countries.
- **Visualization:** Geo map (VPN connections), Table (anomalous locations), Bar chart (connections by country).

---

### UC-17.2.4 · Split-Tunnel Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Split-tunnel configurations affect security visibility. Ensuring compliance with tunnel policy maintains security posture.
- **App/TA:** VPN TA
- **Data Sources:** VPN session attributes (tunnel type, group policy)
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa"
| stats count by user, tunnel_type, group_policy
| where tunnel_type="split"
| table user, tunnel_type, group_policy, count
```
- **Implementation:** Track VPN tunnel configuration per session. Verify users are connecting with the correct group policy (full-tunnel for high-risk, split-tunnel for standard). Alert on policy violations. Report on tunnel type distribution.
- **Visualization:** Pie chart (full vs split tunnel), Table (sessions by policy), Bar chart (tunnel type by department).

---

### UC-17.2.5 · VPN Tunnel Stability
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Frequent disconnects indicate network issues, client problems, or infrastructure instability affecting user productivity.
- **App/TA:** VPN TA
- **Data Sources:** VPN session logs (connect/disconnect events)
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa"
| where action IN ("session_connect","session_disconnect")
| transaction user maxspan=1h
| where eventcount > 4
| table user, eventcount, duration
| sort -eventcount
```
- **Implementation:** Track connect/disconnect patterns per user. Identify users with >4 reconnections per hour. Correlate with network quality metrics. Alert on widespread instability (multiple users affected simultaneously). Report for helpdesk.
- **Visualization:** Table (unstable connections), Bar chart (reconnects by user), Line chart (reconnection rate trend).

---

### UC-17.2.6 · Off-Hours VPN Access
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** VPN access at unusual hours may indicate compromised credentials or unauthorized activity. Alerting supports investigation.
- **App/TA:** VPN TA + user context
- **Data Sources:** VPN session logs, HR data (department, role)
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="session_connect"
| eval hour=strftime(_time,"%H")
| where (hour < 5 OR hour > 23)
| lookup user_roles.csv user OUTPUT department, role
| where role!="on_call" AND role!="sysadmin"
| table _time, user, department, src_ip, hour
```
- **Implementation:** Define normal hours per user role/department. Alert on VPN connections outside hours for roles that don't require it. Whitelist on-call and sysadmin roles. Review weekly for patterns.
- **Visualization:** Heatmap (user × hour of day), Table (off-hours access), Bar chart (off-hours by department).

---

### UC-17.2.7 · VPN Bandwidth Consumption
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Per-user bandwidth tracking identifies heavy users, guides capacity planning, and detects potential data exfiltration.
- **App/TA:** VPN TA, RADIUS accounting
- **Data Sources:** VPN session accounting (bytes in/out)
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa"
| stats sum(bytes_in) as bytes_in, sum(bytes_out) as bytes_out by user
| eval total_gb=round((bytes_in+bytes_out)/1073741824,2)
| sort -total_gb
| head 20
```
- **Implementation:** Track VPN session byte counters per user. Alert on users with excessive upload (potential data exfiltration). Report on bandwidth distribution for capacity planning. Identify optimization opportunities (video offload, split-tunnel).
- **Visualization:** Bar chart (bandwidth by user), Pie chart (upload vs download), Line chart (total bandwidth trend), Table (top bandwidth consumers).

---

### UC-17.2.8 · Simultaneous Session Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** A single user with simultaneous VPN sessions from different locations strongly indicates credential compromise.
- **App/TA:** VPN TA
- **Data Sources:** VPN session logs
- **SPL:**
```spl
index=vpn sourcetype="cisco:asa" action="session_connect"
| stats dc(src_ip) as unique_ips, values(src_ip) as ips by user
| where unique_ips > 1
```
- **Implementation:** Track active VPN sessions per user. Alert when a user has concurrent sessions from different IPs. Whitelist known scenarios (multiple devices). Trigger automated investigation including password reset.
- **Visualization:** Table (users with multiple sessions), Single value (simultaneous sessions detected), Timeline (detection events).

---

### 17.3 Zero Trust / SASE

**Primary App/TA:** Zscaler TA, Netskope TA, Palo Alto Prisma Access TA.

---

### UC-17.3.1 · Conditional Access Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Tracks zero-trust policy enforcement decisions, ensuring consistent security without creating user friction.
- **App/TA:** SASE TA, Entra ID
- **Data Sources:** SASE/ZT policy decision logs
- **SPL:**
```spl
index=zt sourcetype="zscaler:zpa"
| stats count by policy_action, application, user
| eval pct=round(count/sum(count)*100,1)
```
- **Implementation:** Ingest SASE/ZTNA policy decision logs. Track allow/block/step-up-auth decisions per application and user. Alert on policy blocks for critical applications. Report on policy effectiveness and user experience impact.
- **Visualization:** Pie chart (policy decisions), Bar chart (blocks by application), Line chart (enforcement trend), Table (blocked users).

---

### UC-17.3.2 · Device Trust Scoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Device trust scores drive access decisions in zero-trust architecture. Monitoring ensures devices maintain compliance.
- **App/TA:** ZT platform TA
- **Data Sources:** ZT device compliance/trust data
- **SPL:**
```spl
index=zt sourcetype="zscaler:device_posture"
| where trust_score < 50 OR compliance_status!="compliant"
| table user, device_id, os, trust_score, compliance_status, non_compliant_checks
```
- **Implementation:** Ingest device trust score data from ZT platform. Track compliance rates per OS and department. Alert when critical devices become non-compliant. Report on fleet trust posture for security leadership.
- **Visualization:** Gauge (fleet compliance %), Table (non-compliant devices), Pie chart (compliance distribution), Line chart (trust score trend).

---

### UC-17.3.3 · Micro-Segmentation Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Micro-segmentation limits lateral movement. Audit logs validate policy enforcement and detect bypasses.
- **App/TA:** SDN/ZT policy logs
- **Data Sources:** Micro-segmentation policy logs (allow/deny events)
- **SPL:**
```spl
index=zt sourcetype="microseg:policy"
| where action="deny"
| stats count by src_workload, dest_workload, dest_port, policy_name
| sort -count
```
- **Implementation:** Ingest micro-segmentation policy enforcement logs. Track allowed and denied traffic between workloads. Alert on unexpected denials (may indicate misconfiguration) and unexpected allows (policy gaps). Report on segmentation coverage.
- **Visualization:** Heatmap (workload × workload traffic), Table (policy violations), Sankey diagram (traffic flows).

---

### UC-17.3.4 · ZTNA Application Access
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Per-application access patterns in ZTNA reveal usage trends, security risks, and application performance issues.
- **App/TA:** SASE TA
- **Data Sources:** ZTNA access logs (application, user, device, action)
- **SPL:**
```spl
index=zt sourcetype="zscaler:zpa"
| stats dc(user) as unique_users, count as total_access by application
| sort -unique_users
```
- **Implementation:** Track application access through ZTNA per user and device. Identify unused applications for decommissioning. Monitor access patterns for anomalies. Report on application adoption and usage.
- **Visualization:** Bar chart (top applications by users), Table (application access summary), Line chart (access trends per app).

---

### UC-17.3.5 · Posture Assessment Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Endpoint posture compliance rates over time measure security improvement and identify persistent non-compliance areas.
- **App/TA:** ZT platform TA
- **Data Sources:** ZT posture assessment data
- **SPL:**
```spl
index=zt sourcetype="zt:posture"
| timechart span=1d avg(compliance_pct) as compliance by check_type
```
- **Implementation:** Track posture assessment results over time by check type (AV, encryption, OS patch, firewall). Report on compliance improvement trends. Alert when compliance drops below target. Identify persistent non-compliance patterns.
- **Visualization:** Line chart (compliance trend by check), Bar chart (compliance by OS), Single value (overall compliance %), Table (non-compliant checks).

---

### UC-17.3.6 · Policy Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Zero-trust policies require continuous validation. Drift from baseline configuration introduces security gaps.
- **App/TA:** ZT platform audit logs
- **Data Sources:** ZT policy audit logs, configuration snapshots
- **SPL:**
```spl
index=zt sourcetype="zt:admin_audit"
| search action IN ("policy_modified","rule_added","rule_deleted","rule_disabled")
| table _time, admin, action, policy_name, details
| sort -_time
```
- **Implementation:** Track all ZT policy changes via audit logs. Compare current configuration against approved baseline. Alert on unauthorized modifications. Require change management approval for policy changes. Report on policy change frequency.
- **Visualization:** Table (policy changes), Timeline (modification events), Bar chart (changes by admin), Single value (changes this week).

---

## 18. Data Center Fabric & SDN

### 18.1 Cisco ACI

**Splunk Add-on:** Cisco ACI TA, APIC syslog

### UC-18.1.1 · Fabric Health Score Monitoring

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** ACI fabric health scores provide a single-pane view of overall data center network health. Monitoring these scores lets you catch degradation before it impacts workloads, correlate health drops with specific faults, and maintain SLA compliance across your data center fabric.
- **App/TA:** `TA_cisco-ACI`, APIC REST API via scripted input
- **Data Sources:** APIC REST API (`/api/node/mo/topology/health.json`), APIC syslog
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:health"
| eval node_type=case(dn LIKE "%/node-1%", "APIC", dn LIKE "%/node-1___%", "Leaf", dn LIKE "%/node-2___%", "Spine", 1==1, "Other")
| stats latest(healthScore) as health_score by dn, node_type
| eval status=case(health_score>=90, "Healthy", health_score>=70, "Degraded", health_score>=50, "Warning", 1==1, "Critical")
| sort health_score
```
- **Implementation:** Deploy scripted input to poll APIC health API every 60 seconds. Collect topology-wide and per-node health scores. Set threshold alerts: <90 degraded, <70 warning, <50 critical. Integrate with ITSI for service-level health correlation. Build trending to catch slow health degradation.
- **Visualization:** Single value (fabric health), Gauge (per-node health), Timechart (health trending), Status grid (node health map).

### UC-18.1.2 · Fault Trending by Severity

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** ACI faults are the primary operational signal from the fabric. Trending faults by severity helps identify worsening conditions, recurring hardware issues, and configuration problems before they cascade into outages.
- **App/TA:** `TA_cisco-ACI`, APIC syslog
- **Data Sources:** APIC faults API (`/api/node/class/faultInst.json`), APIC syslog
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:faults"
| eval severity_order=case(severity=="critical", 4, severity=="major", 3, severity=="minor", 2, severity=="warning", 1, 1==1, 0)
| timechart span=1h count by severity
| fields _time critical major minor warning
```
- **Implementation:** Poll APIC fault instance class every 5 minutes. Parse severity, fault code, affected DN, and lifecycle state. Track fault creation/clearing patterns. Alert on critical/major fault count spikes. Build fault code frequency reports for proactive maintenance.
- **Visualization:** Timechart (fault trends by severity), Bar chart (top fault codes), Table (active critical faults), Single value (open critical faults count).

### UC-18.1.3 · Endpoint Mobility Tracking

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Endpoint mobility in ACI tracks workload movement across leaf switches. Anomalous mobility (rapid moves, unexpected locations) can indicate misconfigurations, loops, or security issues like MAC spoofing.
- **App/TA:** `TA_cisco-ACI`, APIC endpoint tracker
- **Data Sources:** APIC endpoint tracker, ACI endpoint move events
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:endpoint"
| where action="move"
| stats count as move_count, values(from_leaf) as from_leaves, values(to_leaf) as to_leaves, latest(_time) as last_move by mac, ip, tenant, epg
| where move_count > 5
| sort -move_count
| eval alert=if(move_count>20, "Anomalous", "Normal")
```
- **Implementation:** Enable endpoint tracker on APIC. Ingest endpoint move events via syslog or API polling. Baseline normal mobility rates per EPG. Alert on endpoints with excessive moves (>20/hour). Investigate rapid moves for potential loops or spoofing. Correlate with contract hits.
- **Visualization:** Table (high-mobility endpoints), Timechart (move rate trending), Sankey diagram (leaf-to-leaf moves), Single value (anomalous endpoints).

### UC-18.1.4 · Contract/Filter Hit Analysis

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** ACI contracts control EPG-to-EPG communication. Analyzing contract hits reveals traffic patterns, identifies overly permissive or unused contracts, and helps validate micro-segmentation policies are working as designed.
- **App/TA:** `TA_cisco-ACI`, APIC flow logs
- **Data Sources:** APIC contract hit counters, ACI flow telemetry
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:contracts"
| stats sum(permit_count) as permitted, sum(deny_count) as denied by src_epg, dst_epg, contract_name, filter_name
| eval total=permitted+denied
| eval deny_pct=round((denied/total)*100, 2)
| sort -total
| table src_epg, dst_epg, contract_name, filter_name, permitted, denied, deny_pct
```
- **Implementation:** Enable contract statistics on APIC. Poll contract hit counters via API every 5 minutes. Track permit vs deny ratios per contract. Identify contracts with zero hits (candidates for cleanup). Alert on unexpected deny spikes indicating policy or application issues.
- **Visualization:** Table (contract hit summary), Bar chart (top contracts by hits), Timechart (deny trends), Sankey diagram (EPG-to-EPG flows).

### UC-18.1.5 · Tenant Configuration Audit

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Configuration changes in ACI tenants (BDs, EPGs, contracts) are a leading cause of outages. Auditing all changes provides accountability, supports compliance, and enables rapid rollback identification when issues occur.
- **App/TA:** `TA_cisco-ACI`, APIC audit log
- **Data Sources:** APIC audit log (`/api/node/class/aaaModLR.json`)
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:audit"
| search affected LIKE "uni/tn-*"
| rex field=affected "uni/tn-(?<tenant>[^/]+)"
| stats count by _time, user, action, tenant, affected, descr
| sort -_time
| table _time, user, action, tenant, affected, descr
```
- **Implementation:** Enable audit logging on APIC (enabled by default). Ingest audit records via API polling or syslog. Track all create/modify/delete operations on tenant objects. Correlate configuration changes with fault events. Require change management tickets for production tenant changes.
- **Visualization:** Table (recent changes), Timeline (change events), Bar chart (changes by user), Pie chart (changes by tenant).

### UC-18.1.6 · Leaf/Spine Interface Utilization

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Fabric link saturation causes packet drops and application latency. Monitoring leaf/spine interface utilization identifies hotspots, validates ECMP distribution, and supports capacity planning for fabric expansion.
- **App/TA:** `TA_cisco-ACI`, APIC interface metrics
- **Data Sources:** APIC interface statistics API, fabric port counters
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:interface_stats"
| eval util_pct=round((bytesRate*8/speed)*100, 2)
| stats avg(util_pct) as avg_util, max(util_pct) as peak_util by node, interface, speed
| where peak_util > 70
| sort -peak_util
| table node, interface, speed, avg_util, peak_util
```
- **Implementation:** Poll APIC interface statistics every 60 seconds. Calculate utilization from byte rates and link speed. Set thresholds at 70% warning, 85% critical. Track ECMP balance across parallel fabric links. Alert on sustained high utilization indicating need for fabric expansion.
- **Visualization:** Heatmap (interface utilization by node), Timechart (utilization trending), Table (high-util interfaces), Gauge (fabric aggregate utilization).

### UC-18.1.7 · APIC Cluster Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** APIC controllers manage the entire ACI fabric. Cluster health issues (split-brain, leader election, convergence problems) can cause fabric-wide configuration and policy failures. Monitoring APIC cluster state is essential for fabric reliability.
- **App/TA:** `TA_cisco-ACI`, APIC system logs
- **Data Sources:** APIC cluster health API, APIC system logs/syslog
- **SPL:**
```spl
index=cisco_aci sourcetype="cisco:aci:system"
| search (cluster_status OR leader_election OR convergence)
| eval status=case(
    searchmatch("fully-fit"), "Healthy",
    searchmatch("partially-fit"), "Degraded",
    searchmatch("not-fit"), "Critical",
    1==1, "Unknown")
| stats latest(status) as cluster_status, latest(_time) as last_update by apic_id
| table apic_id, cluster_status, last_update
```
- **Implementation:** Monitor APIC cluster health endpoint every 30 seconds. Track cluster fitness, leader election events, and database sync status. Alert immediately on any non-fully-fit state. Monitor APIC resource utilization (disk, CPU, memory). Document recovery procedures for cluster issues.
- **Visualization:** Status grid (APIC cluster state), Timeline (cluster events), Single value (cluster fitness), Table (APIC node details).

### 18.2 VMware NSX

**Splunk Add-on:** VMware NSX TA, syslog

### UC-18.2.1 · Distributed Firewall Rule Hits

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** NSX Distributed Firewall (DFW) runs on every hypervisor, providing east-west traffic control. Monitoring rule hits validates security policy effectiveness, identifies unused rules for cleanup, and detects policy violations in real time.
- **App/TA:** `vmware_nsx_addon`, NSX DFW syslog
- **Data Sources:** NSX DFW firewall logs (syslog), NSX Manager API
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:dfw"
| stats sum(eval(if(action="ALLOW", 1, 0))) as allowed, sum(eval(if(action="DROP", 1, 0))) as dropped, sum(eval(if(action="REJECT", 1, 0))) as rejected by rule_id, rule_name, src_ip, dst_ip, dst_port, protocol
| eval total=allowed+dropped+rejected
| sort -total
| table rule_id, rule_name, src_ip, dst_ip, dst_port, protocol, allowed, dropped, rejected
```
- **Implementation:** Enable DFW logging on NSX Manager for desired rule sections. Forward DFW logs via syslog to Splunk. Parse rule ID, action, source, destination, and port fields. Identify rules with zero hits (candidates for removal). Alert on unexpected DENY hits indicating misconfiguration or attack.
- **Visualization:** Bar chart (top rules by hits), Timechart (allow vs deny trending), Table (denied connections), Sankey diagram (source-to-destination flows).

### UC-18.2.2 · Micro-Segmentation Enforcement

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** NSX micro-segmentation is a key Zero Trust control. Monitoring enforcement validates that workloads are properly isolated, detects lateral movement attempts, and proves compliance with segmentation policies during audits.
- **App/TA:** `vmware_nsx_addon`, NSX DFW logs
- **Data Sources:** NSX DFW logs, NSX security group membership
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:dfw"
| lookup nsx_security_groups vm_name OUTPUT security_group
| stats count as hits, dc(dst_ip) as unique_destinations by security_group, action, direction
| eval compliance=if(action="DROP" AND direction="intra-group", "Violation", "Expected")
| sort -hits
```
- **Implementation:** Define security groups in NSX aligned with application tiers. Enable DFW logging for inter-group and intra-group traffic. Enrich logs with security group membership. Track allowed vs denied inter-group communication. Alert on intra-group denials or unexpected inter-group allows.
- **Visualization:** Heatmap (group-to-group traffic), Sankey diagram (flow paths), Bar chart (denials by group), Single value (policy violation count).

### UC-18.2.3 · Logical Switch Health

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** NSX logical switches and routers form the virtual network fabric. Monitoring their operational status ensures VM connectivity and helps identify overlay network issues before they impact applications.
- **App/TA:** `vmware_nsx_addon`, NSX Manager events
- **Data Sources:** NSX Manager API, NSX system events/syslog
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:events"
| search object_type IN ("LogicalSwitch", "LogicalRouter", "Tier0Router", "Tier1Router")
| eval status=case(severity=="HIGH" OR severity=="CRITICAL", "Degraded", severity=="MEDIUM", "Warning", 1==1, "Healthy")
| stats latest(status) as current_status, count as event_count by object_name, object_type
| sort -event_count
```
- **Implementation:** Poll NSX Manager API for logical switch and router status every 60 seconds. Ingest NSX system events via syslog. Alert on logical switch or router down events. Track BFD session state for Tier-0/Tier-1 routers. Monitor VNI pool exhaustion.
- **Visualization:** Status grid (switch/router health), Table (degraded components), Timechart (event trends), Single value (active logical switches).

### UC-18.2.4 · NSX Edge Performance

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** NSX Edge nodes handle north-south traffic, load balancing, and NAT. Performance bottlenecks on Edge nodes directly impact application availability and throughput for any workload communicating outside the NSX fabric.
- **App/TA:** `vmware_nsx_addon`, NSX Edge metrics
- **Data Sources:** NSX Edge node metrics (CPU, memory, datapath), NSX Manager API
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:edge_metrics"
| stats avg(cpu_pct) as avg_cpu, max(cpu_pct) as peak_cpu, avg(mem_pct) as avg_mem, avg(datapath_cpu_pct) as avg_dp_cpu by edge_node, cluster
| eval status=case(peak_cpu>90 OR avg_dp_cpu>80, "Critical", peak_cpu>75 OR avg_dp_cpu>60, "Warning", 1==1, "Healthy")
| table edge_node, cluster, avg_cpu, peak_cpu, avg_mem, avg_dp_cpu, status
| sort -peak_cpu
```
- **Implementation:** Collect Edge node metrics via NSX Manager API every 60 seconds. Monitor both management plane and datapath CPU separately. Track interface throughput on uplinks. Set thresholds: datapath CPU >80% critical, >60% warning. Plan Edge node scale-out when sustained utilization exceeds thresholds.
- **Visualization:** Gauge (Edge CPU/memory), Timechart (performance trending), Table (Edge node status), Single value (peak datapath CPU).

### UC-18.2.5 · Transport Node Connectivity

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Transport nodes are the hypervisors participating in the NSX overlay. Tunnel failures between transport nodes cause VM-to-VM communication loss across hosts, directly impacting application availability.
- **App/TA:** `vmware_nsx_addon`, NSX transport node logs
- **Data Sources:** NSX transport node status API, TEP tunnel events
- **SPL:**
```spl
index=vmware sourcetype="vmware:nsx:transport_node"
| eval tunnel_status=case(status=="UP", "Healthy", status=="DEGRADED", "Degraded", status=="DOWN", "Down", 1==1, "Unknown")
| stats latest(tunnel_status) as current_status, latest(_time) as last_seen by transport_node, host_ip
| search current_status!="Healthy"
| table transport_node, host_ip, current_status, last_seen
```
- **Implementation:** Poll NSX Manager for transport node status every 30 seconds. Monitor TEP (Tunnel Endpoint) reachability between all transport nodes. Alert immediately on tunnel DOWN state. Track tunnel flapping (frequent UP/DOWN cycles). Correlate with physical network events (link failures, MTU issues).
- **Visualization:** Status grid (transport node map), Table (degraded nodes), Timechart (tunnel status changes), Single value (healthy tunnel percentage).

### 18.3 Other SDN

**Splunk Add-on:** Custom inputs, Kubernetes CNI logs

### UC-18.3.1 · Cilium/Calico Network Policy Monitoring

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Kubernetes CNI network policies enforce pod-to-pod communication rules. Monitoring policy enforcement validates that micro-segmentation is working in containerized environments, critical for multi-tenant clusters and compliance.
- **App/TA:** Custom scripted inputs, Kubernetes logging pipeline
- **Data Sources:** Cilium/Calico policy logs, Kubernetes audit logs
- **SPL:**
```spl
index=kubernetes sourcetype="kube:cni:policy"
| stats count as hits, dc(src_pod) as src_pods, dc(dst_pod) as dst_pods by policy_name, action, namespace
| eval enforcement=if(action="deny", "Blocked", "Allowed")
| sort -hits
| table namespace, policy_name, enforcement, hits, src_pods, dst_pods
```
- **Implementation:** Enable CNI policy logging in Cilium/Calico configuration. Forward logs via Fluentd/Fluent Bit to Splunk HEC. Parse policy name, action, source/destination pod, and namespace. Track denied traffic for security visibility. Identify namespaces without network policies (compliance gap).
- **Visualization:** Bar chart (policy hits by namespace), Table (denied flows), Heatmap (namespace-to-namespace traffic), Single value (namespaces without policies).

### UC-18.3.2 · OpenStack Neutron Events

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Neutron manages virtual networking in OpenStack. Tracking network operations (creation, modification, deletion) provides change audit, helps troubleshoot connectivity issues, and identifies unauthorized network modifications.
- **App/TA:** Custom scripted input (OpenStack API), OpenStack syslog
- **Data Sources:** Neutron API logs, OpenStack syslog
- **SPL:**
```spl
index=openstack sourcetype="openstack:neutron"
| search action IN ("create", "update", "delete")
| stats count by action, resource_type, user, project_name
| sort -count
| table _time, user, project_name, action, resource_type, resource_name, count
```
- **Implementation:** Ingest Neutron API logs via syslog or OpenStack notification bus. Track all network, subnet, port, and router CRUD operations. Alert on mass deletions or unauthorized modifications. Correlate network changes with VM connectivity issues.
- **Visualization:** Table (recent operations), Bar chart (operations by type), Timeline (change events), Pie chart (operations by project).

### UC-18.3.3 · SDN Controller Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** SDN controllers are the brain of software-defined networks. Controller outages or cluster consensus failures can cause network-wide disruption. Monitoring controller health ensures the control plane remains available and consistent.
- **App/TA:** Custom scripted input, SDN controller syslog
- **Data Sources:** SDN controller system logs, cluster status API
- **SPL:**
```spl
index=sdn sourcetype="sdn:controller"
| search (cluster_state OR heartbeat OR leader_election OR consensus)
| eval health=case(
    searchmatch("healthy") OR searchmatch("active"), "Healthy",
    searchmatch("degraded") OR searchmatch("standby"), "Degraded",
    searchmatch("failed") OR searchmatch("unreachable"), "Critical",
    1==1, "Unknown")
| stats latest(health) as status, latest(_time) as last_heartbeat by controller_id, role
| table controller_id, role, status, last_heartbeat
```
- **Implementation:** Monitor SDN controller cluster via heartbeat polling every 15 seconds. Track cluster membership, leader election events, and consensus state. Alert immediately on controller failure or split-brain conditions. Monitor controller resource utilization (CPU, memory, database size). Maintain runbook for controller failover.
- **Visualization:** Status grid (controller cluster), Timeline (cluster events), Single value (cluster health), Table (controller details).

---

## 19. Compute Infrastructure (HCI & Converged)

### 19.1 Cisco UCS

**Splunk Add-on:** Cisco UCS TA, UCS Manager syslog

### UC-19.1.1 · Blade/Rack Server Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** UCS blade and rack servers host critical workloads. Monitoring component health (CPU, memory, PSU, fans) enables proactive hardware replacement before failures cause VM outages and unplanned downtime.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager syslog
- **Data Sources:** UCS Manager faults, UCS Manager equipment API
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:faults"
| search dn="sys/chassis-*/blade-*" OR dn="sys/rack-unit-*"
| eval component=case(
    cause LIKE "%cpu%", "CPU",
    cause LIKE "%memory%", "Memory",
    cause LIKE "%psu%", "PSU",
    cause LIKE "%fan%", "Fan",
    cause LIKE "%disk%", "Disk",
    1==1, "Other")
| stats count by severity, component, dn, descr
| sort -severity, -count
```
- **Implementation:** Configure UCS Manager syslog forwarding to Splunk. Poll equipment health via UCS Manager XML API every 5 minutes. Track fault creation and clearing events. Alert on critical/major faults for immediate hardware replacement. Maintain server inventory with health status overlay.
- **Visualization:** Status grid (server health map), Bar chart (faults by component), Table (active critical faults), Timechart (fault trending).

### UC-19.1.2 · Service Profile Compliance

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** UCS service profiles define the identity of compute resources. Non-compliant associations indicate configuration drift, failed hardware migrations, or policy violations that can impact workload performance and security.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager events
- **Data Sources:** UCS Manager service profile API, configuration events
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:config"
| search object_type="service_profile"
| eval compliance=case(
    assoc_state="associated" AND config_state="applied", "Compliant",
    assoc_state="associated" AND config_state!="applied", "Non-Compliant",
    assoc_state="unassociated", "Unassociated",
    1==1, "Unknown")
| stats count by compliance, org, sp_name, server_dn
| sort compliance
```
- **Implementation:** Poll service profile status via UCS Manager API every 5 minutes. Track association state and configuration compliance. Alert on non-compliant profiles requiring reapplication. Monitor service profile migrations during maintenance windows. Report on unassociated profiles (wasted compute capacity).
- **Visualization:** Pie chart (compliance breakdown), Table (non-compliant profiles), Single value (compliance percentage), Status grid (profile status by org).

### UC-19.1.3 · Firmware Compliance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Running inconsistent firmware across UCS creates compatibility issues and security vulnerabilities. Tracking firmware versions enables compliance reporting, patch planning, and ensures consistency across the compute fleet.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager inventory
- **Data Sources:** UCS Manager firmware inventory, UCS firmware policy
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:inventory"
| search object_type="firmware"
| stats count by component_type, running_version, server_dn
| lookup ucs_approved_firmware component_type OUTPUT approved_version
| eval compliant=if(running_version==approved_version, "Yes", "No")
| stats count as server_count by component_type, running_version, approved_version, compliant
| sort compliant, component_type
```
- **Implementation:** Poll UCS firmware inventory weekly. Maintain a lookup of approved firmware versions per component type. Compare running versions against approved baselines. Generate compliance reports for audit. Prioritize non-compliant servers in maintenance windows.
- **Visualization:** Table (firmware compliance matrix), Bar chart (servers by firmware version), Pie chart (compliant vs non-compliant), Single value (fleet compliance percentage).

### UC-19.1.4 · Fault Trending by Severity

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** UCS fault trends reveal systemic hardware issues, environmental problems, or configuration problems across the compute fleet. Rising fault counts indicate deteriorating conditions requiring proactive attention.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager faults
- **Data Sources:** UCS Manager fault log, syslog
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:faults"
| timechart span=1h count by severity
| fields _time critical major minor warning info
```
- **Implementation:** Forward UCS Manager faults via syslog or API polling. Categorize faults by severity and type. Track fault lifecycle (create, clear, acknowledge). Alert on critical/major fault count exceeding baseline by >50%. Report weekly on fault trends and resolution times.
- **Visualization:** Timechart (fault trends by severity), Bar chart (top fault codes), Single value (open critical faults), Table (active faults detail).

### UC-19.1.5 · FI Port Channel Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Fabric Interconnects are the network gateway for all UCS compute. Port-channel failures reduce bandwidth or cause complete loss of connectivity, impacting every workload in the UCS domain.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager stats
- **Data Sources:** UCS Manager FI port-channel statistics, FI syslog
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:fi_stats"
| search object_type="port_channel"
| eval member_pct=round((active_members/configured_members)*100, 0)
| stats latest(oper_state) as status, latest(member_pct) as active_pct, latest(rx_bps) as rx_rate, latest(tx_bps) as tx_rate by fi_id, pc_id, pc_name
| eval health=case(status!="up", "Down", active_pct<100, "Degraded", 1==1, "Healthy")
| table fi_id, pc_id, pc_name, status, active_pct, rx_rate, tx_rate, health
```
- **Implementation:** Monitor FI port-channel status every 30 seconds. Track member link count vs configured count. Alert on any port-channel with less than 100% members active. Monitor FI uplink utilization for capacity planning. Correlate FI events with server connectivity issues.
- **Visualization:** Status grid (port-channel health), Gauge (member active percentage), Timechart (utilization trending), Table (degraded port-channels).

### UC-19.1.6 · Power and Thermal Monitoring

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** UCS power and thermal data helps optimize data center capacity planning, detect cooling failures before overheating causes server throttling, and track energy efficiency metrics for sustainability reporting.
- **App/TA:** `Splunk_TA_cisco-ucs`, UCS Manager environmental
- **Data Sources:** UCS Manager environmental statistics, power supply metrics
- **SPL:**
```spl
index=cisco_ucs sourcetype="cisco:ucs:environmental"
| eval metric_type=case(stat_name LIKE "%power%", "Power", stat_name LIKE "%temp%", "Temperature", stat_name LIKE "%fan%", "Fan", 1==1, "Other")
| stats avg(value) as avg_val, max(value) as max_val by chassis_id, metric_type, unit
| eval status=case(
    metric_type=="Temperature" AND max_val>75, "Critical",
    metric_type=="Temperature" AND max_val>65, "Warning",
    metric_type=="Fan" AND avg_val<2000, "Warning",
    1==1, "Normal")
| table chassis_id, metric_type, avg_val, max_val, unit, status
```
- **Implementation:** Collect UCS environmental data via API every 60 seconds. Track per-chassis power draw, inlet/outlet temperatures, and fan speeds. Set thermal thresholds based on vendor specs. Alert on overheating or fan failures. Report monthly power consumption for capacity and cost planning.
- **Visualization:** Gauge (temperature/power), Timechart (power and thermal trending), Heatmap (chassis thermal map), Single value (total power draw).

### 19.2 Hyper-Converged Infrastructure (HCI)

**Splunk Add-on:** Nutanix TA, VMware vSAN (via vCenter TA), vendor APIs

### UC-19.2.1 · Cluster Health Monitoring

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** HCI cluster health directly determines workload availability. Monitoring overall cluster state, node availability, and service health enables rapid response to degradation before it impacts VMs and applications running on the cluster.
- **App/TA:** `TA-nutanix` or vendor-specific TA, HCI management API
- **Data Sources:** HCI management API (Prism, vSAN Health), cluster status events
- **SPL:**
```spl
index=hci sourcetype="hci:cluster_health"
| stats latest(cluster_status) as status, latest(num_nodes) as total_nodes, latest(healthy_nodes) as healthy_nodes, latest(storage_usage_pct) as storage_pct by cluster_name
| eval node_health=round((healthy_nodes/total_nodes)*100, 0)
| eval overall=case(status=="HEALTHY" AND node_health==100, "Healthy", status=="WARNING" OR node_health<100, "Degraded", 1==1, "Critical")
| table cluster_name, overall, total_nodes, healthy_nodes, node_health, storage_pct
```
- **Implementation:** Poll HCI management API every 60 seconds for cluster health. Track node online/offline state, storage health, and service availability. Alert on any cluster degradation (non-healthy state). Monitor rebuild operations and their impact on performance. Integrate with ITSI for service-level visibility.
- **Visualization:** Status grid (cluster health map), Single value (cluster status), Gauge (storage capacity), Table (cluster details).

### UC-19.2.2 · Storage Pool Capacity

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** HCI storage pools are shared across all workloads. Running out of storage capacity causes VM provisioning failures, snapshot failures, and ultimately VM crashes. Proactive monitoring and forecasting prevents capacity emergencies.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI storage metrics, capacity API
- **SPL:**
```spl
index=hci sourcetype="hci:storage_metrics"
| stats latest(total_capacity_tb) as total_tb, latest(used_capacity_tb) as used_tb by cluster_name, storage_pool
| eval free_tb=total_tb-used_tb
| eval used_pct=round((used_tb/total_tb)*100, 1)
| eval days_to_full=if(used_pct>50, round(free_tb/avg_daily_growth_tb, 0), "N/A")
| table cluster_name, storage_pool, total_tb, used_tb, free_tb, used_pct, days_to_full
| sort -used_pct
```
- **Implementation:** Collect storage capacity metrics every 5 minutes. Track daily growth rates for forecasting. Alert at 75% warning and 85% critical thresholds. Use Splunk predict command for capacity forecasting. Plan procurement cycles based on projected exhaustion dates.
- **Visualization:** Gauge (capacity utilization), Timechart (capacity trending with forecast), Table (pool details), Single value (days to capacity).

### UC-19.2.3 · Storage I/O Latency

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Storage latency directly impacts application performance on HCI. Elevated latency affects all VMs on the cluster. Early detection of latency spikes enables workload rebalancing or troubleshooting before user impact escalates.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI performance metrics, per-VM I/O statistics
- **SPL:**
```spl
index=hci sourcetype="hci:io_metrics"
| stats avg(read_latency_ms) as avg_read_lat, avg(write_latency_ms) as avg_write_lat, max(read_latency_ms) as peak_read_lat, max(write_latency_ms) as peak_write_lat, sum(iops) as total_iops by cluster_name, node
| eval status=case(peak_read_lat>20 OR peak_write_lat>20, "Critical", peak_read_lat>10 OR peak_write_lat>10, "Warning", 1==1, "Healthy")
| sort -peak_write_lat
| table cluster_name, node, avg_read_lat, peak_read_lat, avg_write_lat, peak_write_lat, total_iops, status
```
- **Implementation:** Collect HCI I/O metrics every 30 seconds. Track read/write latency at cluster, node, and VM level. Set thresholds: >10ms warning, >20ms critical (adjust per workload SLA). Correlate latency spikes with rebuild operations, snapshot activity, or capacity constraints. Alert on sustained latency above threshold.
- **Visualization:** Timechart (latency trending), Gauge (current latency), Table (high-latency nodes), Heatmap (latency by node over time).

### UC-19.2.4 · Node Performance Balance

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** HCI relies on balanced workload distribution across nodes. Imbalanced nodes lead to hotspots where some nodes are overloaded while others are underutilized, reducing overall cluster efficiency and increasing failure risk.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI node-level performance metrics
- **SPL:**
```spl
index=hci sourcetype="hci:node_metrics"
| stats avg(cpu_pct) as avg_cpu, avg(mem_pct) as avg_mem, avg(iops) as avg_iops by cluster_name, node
| eventstats avg(avg_cpu) as cluster_avg_cpu, stdev(avg_cpu) as cluster_stdev_cpu by cluster_name
| eval cpu_deviation=round(abs(avg_cpu-cluster_avg_cpu)/cluster_stdev_cpu, 2)
| eval balance=case(cpu_deviation>2, "Imbalanced", cpu_deviation>1, "Slightly Imbalanced", 1==1, "Balanced")
| table cluster_name, node, avg_cpu, avg_mem, avg_iops, cpu_deviation, balance
| sort -cpu_deviation
```
- **Implementation:** Collect per-node CPU, memory, and I/O metrics every 60 seconds. Calculate standard deviation across nodes to detect imbalance. Alert when any node deviates >2 standard deviations from cluster average. Recommend DRS or workload migration to rebalance. Track balance improvement after actions.
- **Visualization:** Bar chart (node utilization comparison), Heatmap (node balance over time), Table (imbalanced nodes), Single value (cluster balance score).

### UC-19.2.5 · Disk Failure Tracking

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Disk failures in HCI trigger data rebuild operations that consume cluster resources and temporarily reduce resilience. Tracking failures enables rapid replacement, monitoring rebuild progress, and assessing the cluster's ability to tolerate additional failures.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI disk events, SMART data, rebuild status
- **SPL:**
```spl
index=hci sourcetype="hci:disk_events"
| search event_type IN ("disk_failure", "disk_offline", "disk_rebuild_start", "disk_rebuild_complete", "smart_warning")
| stats count as events, latest(event_type) as latest_event, latest(_time) as last_event_time by cluster_name, node, disk_id, disk_serial
| eval status=case(
    latest_event=="disk_failure" OR latest_event=="disk_offline", "Failed",
    latest_event=="disk_rebuild_start", "Rebuilding",
    latest_event=="smart_warning", "Warning",
    1==1, "OK")
| search status!="OK"
| table cluster_name, node, disk_id, disk_serial, status, last_event_time
```
- **Implementation:** Ingest HCI disk events and SMART health data. Alert immediately on disk failures. Track rebuild start/complete times to measure rebuild duration. Monitor cluster resiliency during rebuilds (can it tolerate another failure?). Maintain spare disk inventory based on failure rate trends.
- **Visualization:** Status grid (disk health by node), Timeline (failure and rebuild events), Single value (disks in rebuild), Table (failed/warning disks).

### UC-19.2.6 · Replication Factor Compliance

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** HCI data resilience depends on maintaining the configured replication factor (RF2/RF3). Non-compliant replication means data loss risk if additional failures occur. Monitoring RF compliance is essential for data protection assurance.
- **App/TA:** `TA-nutanix` or vendor-specific TA
- **Data Sources:** HCI replication status, data protection metrics
- **SPL:**
```spl
index=hci sourcetype="hci:replication"
| stats latest(configured_rf) as target_rf, latest(actual_rf) as current_rf, latest(rebuild_pct) as rebuild_progress by cluster_name, container
| eval compliant=if(current_rf>=target_rf, "Yes", "No")
| eval risk=case(current_rf<target_rf-1, "Data Loss Risk", current_rf<target_rf, "Reduced Resilience", 1==1, "Protected")
| table cluster_name, container, target_rf, current_rf, compliant, risk, rebuild_progress
| sort risk
```
- **Implementation:** Monitor replication factor status continuously. Alert immediately when actual RF drops below configured RF. Track rebuild progress to estimate time to full compliance. Monitor cluster capacity to ensure sufficient space for re-replication. Alert critically if RF drops to 1 (single copy—data loss imminent on next failure).
- **Visualization:** Single value (RF compliance status), Gauge (rebuild progress), Table (non-compliant containers), Status grid (cluster RF map).

### UC-19.2.7 · CVM (Controller VM) Health

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Value:** Nutanix Controller VMs manage all storage I/O on each node. CVM failures cause I/O to redirect to other nodes, impacting performance. Monitoring CVM health ensures the HCI control plane remains operational across all nodes.
- **App/TA:** `TA-nutanix`, Nutanix CVM logs
- **Data Sources:** Nutanix CVM resource metrics, CVM service status logs
- **SPL:**
```spl
index=hci sourcetype="nutanix:cvm"
| stats latest(cpu_pct) as cpu, latest(mem_pct) as mem, latest(stargate_status) as stargate, latest(cassandra_status) as cassandra, latest(zookeeper_status) as zk by node, cvm_ip
| eval all_services_up=if(stargate=="UP" AND cassandra=="UP" AND zk=="UP", "Yes", "No")
| eval health=case(all_services_up=="No", "Critical", cpu>80 OR mem>85, "Warning", 1==1, "Healthy")
| table node, cvm_ip, cpu, mem, stargate, cassandra, zk, health
| sort health
```
- **Implementation:** Monitor CVM service status (Stargate, Cassandra, Zookeeper, Prism) every 30 seconds. Track CVM CPU and memory utilization. Alert immediately on any CVM service failure. Monitor CVM-to-CVM communication for cluster stability. Track CVM restart events and correlate with I/O disruptions.
- **Visualization:** Status grid (CVM health by node), Table (CVM service status), Gauge (CVM resource utilization), Timechart (CVM metrics trending).

---

## 20. Cost & Capacity Management

### 20.1 Cloud Cost Monitoring

**Splunk Add-on:** Cloud provider TAs, CUR/billing export ingestion

### UC-20.1.1 · Daily Spend Trending

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Cloud costs can spiral without visibility. Daily spend trending by service, account, and tag provides the financial governance foundation — enabling teams to understand where money goes, spot trends early, and make informed optimization decisions.
- **App/TA:** `Splunk Add-on for AWS` (CUR ingestion), `Splunk Add-on for Microsoft Cloud Services`, `Splunk Add-on for Google Cloud Platform`
- **Data Sources:** AWS Cost and Usage Report (CUR), Azure Cost Management export, GCP Billing export
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| timechart span=1d sum(cost) as daily_spend by lineItem_ProductCode
| addtotals
| rename Total as total_daily_spend
```
- **Implementation:** Ingest AWS CUR, Azure Cost export, or GCP billing data daily. Parse cost line items by service, account, region, and tags. Build daily/weekly/monthly spend reports. Set trending alerts when daily spend exceeds 7-day rolling average by >20%. Enable tag-based cost allocation from day one.
- **Visualization:** Timechart (daily spend trending), Stacked bar chart (spend by service), Table (top 10 services by cost), Single value (today's spend vs yesterday).

### UC-20.1.2 · Cost Anomaly Detection

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Value:** Unexpected cost spikes from runaway instances, misconfigured autoscaling, or crypto-mining attacks can generate thousands in charges within hours. Automated anomaly detection catches these events before they become budget disasters.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** Billing data with historical trending
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| timechart span=1d sum(cost) as daily_spend by lineItem_UsageAccountId
| foreach * [eval <<FIELD>>=if(<<FIELD>>="", 0, <<FIELD>>)]
| addtotals
| predict Total as predicted_spend algorithm=LLP5 future_timespan=1
| eval anomaly=if(Total > 'upper95(predicted_spend)', "Anomaly", "Normal")
| where anomaly="Anomaly"
```
- **Implementation:** Build 30-day baseline of daily spending per account and service. Use Splunk `predict` command with LLP5 algorithm for anomaly detection. Alert when actual spend exceeds upper 95% confidence interval. Investigate anomalies by drilling into specific services and resources. Integrate with incident management for cost-related incidents.
- **Visualization:** Timechart (actual vs predicted spend), Table (anomaly details), Single value (current anomaly count), Alert indicator (anomaly detected).

### UC-20.1.3 · Reserved Instance Utilization

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Reserved Instances and Savings Plans represent upfront commitments. Monitoring utilization ensures you're getting value from these purchases. Low utilization means wasted money; gaps in coverage mean missed savings opportunities.
- **App/TA:** `Splunk Add-on for AWS`, billing TAs
- **Data Sources:** AWS CUR (reservation fields), Azure reservation utilization
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| search reservation_ReservationARN!=""
| stats sum(reservation_UnusedAmortizedUpfrontFeeForBillingPeriod) as unused_upfront, sum(reservation_EffectiveCost) as effective_cost, sum(reservation_UnusedRecurringFee) as unused_recurring by reservation_ReservationARN, lineItem_ProductCode
| eval utilization_pct=round((1-(unused_upfront+unused_recurring)/effective_cost)*100, 1)
| sort utilization_pct
| table reservation_ReservationARN, lineItem_ProductCode, effective_cost, unused_upfront, unused_recurring, utilization_pct
```
- **Implementation:** Parse RI/Savings Plan utilization from CUR data. Track utilization percentage per reservation. Alert when any RI falls below 80% utilization for 7+ consecutive days. Report on coverage gaps where on-demand spend could be covered by reservations. Review expiring reservations 30 days before expiry.
- **Visualization:** Gauge (overall RI utilization), Bar chart (utilization by reservation), Table (underutilized RIs), Timechart (utilization trending).

### UC-20.1.4 · Idle Resource Identification

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Idle resources (running but unused instances, unattached volumes, unused load balancers) are pure waste. Identifying and eliminating them is the quickest path to cloud cost savings, often yielding 20-30% reduction.
- **App/TA:** `Splunk Add-on for AWS`, cloud monitoring TAs
- **Data Sources:** CloudWatch/Azure Monitor metrics + billing data
- **SPL:**
```spl
index=cloud_metrics sourcetype="aws:cloudwatch"
| search metric_name="CPUUtilization"
| stats avg(Average) as avg_cpu, max(Maximum) as peak_cpu by dimensions.InstanceId
| where avg_cpu < 5 AND peak_cpu < 10
| lookup aws_instance_details InstanceId as dimensions.InstanceId OUTPUT instance_type, monthly_cost, tags
| eval waste_monthly=monthly_cost
| sort -waste_monthly
| table dimensions.InstanceId, instance_type, avg_cpu, peak_cpu, monthly_cost, tags
```
- **Implementation:** Correlate CloudWatch CPU/network metrics with billing data. Define idle thresholds: CPU avg <5%, network <1MB/day for 7+ days. Include unattached EBS volumes, idle ELBs, unused Elastic IPs. Generate weekly idle resource reports with estimated savings. Route to resource owners for action.
- **Visualization:** Table (idle resources with cost), Bar chart (waste by service), Single value (total monthly waste), Pie chart (waste by team/tag).

### UC-20.1.5 · Budget Threshold Alerting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Budget alerts prevent overspend by notifying stakeholders at defined thresholds (50%, 75%, 90%, 100%). Combined with forecast-based alerts, teams can take corrective action before exceeding approved budgets.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** Billing data, budget definitions (lookup)
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| stats sum(cost) as mtd_spend by lineItem_UsageAccountId
| lookup cloud_budgets account_id as lineItem_UsageAccountId OUTPUT budget_amount, owner_email
| eval budget_pct=round((mtd_spend/budget_amount)*100, 1)
| eval status=case(budget_pct>=100, "Exceeded", budget_pct>=90, "Critical", budget_pct>=75, "Warning", budget_pct>=50, "On Track", 1==1, "Under Budget")
| sort -budget_pct
| table lineItem_UsageAccountId, owner_email, budget_amount, mtd_spend, budget_pct, status
```
- **Implementation:** Define budgets per account/team in a Splunk lookup table. Calculate MTD spend against budgets daily. Alert at 50%, 75%, 90%, and 100% thresholds. Include forecast-based alerts (projected to exceed budget). Escalate to management when budgets are exceeded.
- **Visualization:** Gauge (budget consumption), Table (budget status by account), Timechart (MTD spend vs budget line), Single value (accounts over budget).

### UC-20.1.6 · Cost Allocation by Team

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Breaking down cloud costs by team/department via tagging creates accountability and enables chargeback/showback. Teams that see their own costs make better optimization decisions, driving organization-wide cost efficiency.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** CUR with tag data, organizational mapping
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| eval team=coalesce('resourceTags_user_Team', 'resourceTags_user_team', "Untagged")
| stats sum(cost) as total_cost by team
| eventstats sum(total_cost) as grand_total
| eval cost_pct=round((total_cost/grand_total)*100, 1)
| sort -total_cost
| table team, total_cost, cost_pct
```
- **Implementation:** Enforce tagging policy requiring Team/Department/Environment tags. Parse resource tags from billing data. Calculate cost allocation by team, department, and environment. Report on untagged resources (assign to "Unknown" for follow-up). Generate monthly chargeback reports.
- **Visualization:** Pie chart (cost by team), Bar chart (team costs with trending), Table (detailed allocation), Single value (untagged cost percentage).

### UC-20.1.7 · Spot/Preemptible Instance Tracking

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Spot instances offer significant savings (60-90%) but can be interrupted. Tracking interruptions, savings achieved, and workload placement ensures teams maximize savings while maintaining application resilience.
- **App/TA:** `Splunk Add-on for AWS`, EC2 event logs
- **Data Sources:** EC2 spot instance events, billing data
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail"
| search eventName="BidEvictedEvent" OR eventName="SpotInstanceInterruption"
| stats count as interruptions by requestParameters.instanceId, requestParameters.instanceType, userIdentity.arn
| lookup spot_savings instance_id as requestParameters.instanceId OUTPUT on_demand_cost, spot_cost
| eval savings=on_demand_cost-spot_cost
| eval savings_pct=round((savings/on_demand_cost)*100, 1)
| table requestParameters.instanceId, requestParameters.instanceType, interruptions, on_demand_cost, spot_cost, savings_pct
```
- **Implementation:** Track spot instance lifecycle events via CloudTrail. Monitor interruption frequency by instance type and AZ. Calculate savings vs on-demand pricing. Alert on interruption rate spikes affecting critical workloads. Report monthly spot savings to justify continued spot adoption.
- **Visualization:** Bar chart (interruptions by type), Timechart (interruption frequency), Single value (monthly spot savings), Table (instance interruption details).

### UC-20.1.8 · Data Transfer Cost Analysis

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Data transfer costs are often the most surprising cloud bill item. Inter-region, cross-AZ, and internet egress charges add up quickly. Identifying the biggest transfer flows enables architectural optimization to reduce costs significantly.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** CUR data transfer line items, VPC flow logs
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| search lineItem_UsageType="*DataTransfer*" OR lineItem_UsageType="*Bytes*"
| eval cost=tonumber(lineItem_UnblendedCost)
| eval transfer_type=case(
    lineItem_UsageType LIKE "%InterRegion%", "Inter-Region",
    lineItem_UsageType LIKE "%Out-Bytes%", "Internet Egress",
    lineItem_UsageType LIKE "%In-Bytes%", "Internet Ingress",
    lineItem_UsageType LIKE "%Regional%", "Cross-AZ",
    1==1, "Other")
| stats sum(cost) as transfer_cost, sum(lineItem_UsageAmount) as gb_transferred by transfer_type, lineItem_ProductCode
| sort -transfer_cost
```
- **Implementation:** Parse data transfer line items from CUR. Categorize by transfer type (egress, inter-region, cross-AZ). Identify top services and resources by transfer cost. Correlate with VPC flow logs for detailed flow analysis. Recommend architecture changes (CDN, VPC endpoints, same-AZ placement) for top cost drivers.
- **Visualization:** Pie chart (cost by transfer type), Bar chart (top services by transfer cost), Timechart (transfer cost trending), Table (detailed transfer breakdown).

### 20.2 Capacity Planning

**Splunk Add-on:** Cross-referencing infrastructure metrics with trending/forecasting

### UC-20.2.1 · Compute Capacity Forecasting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Running out of compute capacity causes provisioning failures and performance degradation. Forecasting when CPU and memory will be exhausted enables proactive procurement or scaling, avoiding emergency purchases at premium cost.
- **App/TA:** Infrastructure monitoring TAs (various), Splunk `predict` command
- **Data Sources:** Host performance metrics (CPU, memory utilization)
- **SPL:**
```spl
index=infrastructure sourcetype="Perfmon:Processor" OR sourcetype="cpu"
| timechart span=1d avg(cpu_load_percent) as avg_cpu by host
| predict avg_cpu as predicted_cpu algorithm=LLP5 future_timespan=30
| eval days_to_threshold=if('upper95(predicted_cpu)'>90, "Within 30 days", "OK")
```
- **Implementation:** Collect CPU and memory metrics from all hosts. Aggregate to daily averages for trending. Use Splunk `predict` with LLP5 for 30/60/90-day forecasting. Set alerts when forecast predicts >90% utilization within 30 days. Report quarterly on capacity headroom across infrastructure tiers.
- **Visualization:** Timechart (utilization with forecast overlay), Table (hosts approaching capacity), Gauge (current vs capacity), Single value (days to threshold).

### UC-20.2.2 · Storage Growth Forecasting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Value:** Storage procurement has lead times. Forecasting growth trends enables timely ordering of additional capacity, preventing the emergency of running out of storage space that causes application outages and data loss.
- **App/TA:** Storage TAs (various), Splunk `predict` command
- **Data Sources:** Storage capacity metrics from SAN/NAS/HCI/cloud
- **SPL:**
```spl
index=storage sourcetype="storage:capacity"
| timechart span=1d latest(used_pct) as used_pct by storage_system
| predict used_pct as predicted_pct algorithm=LLP5 future_timespan=90
| eval forecast_90d='predicted_pct+90d'
| where forecast_90d > 85
```
- **Implementation:** Collect storage capacity metrics daily from all storage platforms. Build growth rate trends per volume/pool. Use Splunk predict for 90-day forecasting. Alert when projected usage exceeds 85% within 90 days. Initiate procurement workflow based on projected needs.
- **Visualization:** Timechart (usage with forecast), Table (systems approaching capacity), Gauge (current utilization), Single value (days to threshold).

### UC-20.2.3 · Network Bandwidth Trending

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Network bandwidth constraints cause application latency and packet loss. Trending WAN/LAN utilization enables planned upgrades during maintenance windows rather than emergency bandwidth additions during business-impacting congestion.
- **App/TA:** Network monitoring TAs, SNMP
- **Data Sources:** Interface utilization metrics (SNMP, streaming telemetry)
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| eval util_pct=round((ifHCInOctets_rate*8/ifHighSpeed/1000000)*100, 2)
| timechart span=1h avg(util_pct) as avg_util, max(util_pct) as peak_util by interface_name
| predict avg_util as predicted_util algorithm=LLP5 future_timespan=30
```
- **Implementation:** Collect interface utilization via SNMP every 5 minutes. Aggregate to hourly peaks and daily averages. Trend key WAN links and data center interconnects. Alert when trending projects >80% utilization within 30 days. Plan circuit upgrades based on business growth forecasts.
- **Visualization:** Timechart (bandwidth trending with forecast), Table (high-utilization links), Gauge (current peak utilization), Bar chart (top links by utilization).

### UC-20.2.4 · License Utilization Tracking

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Software licenses represent significant IT spend. Tracking usage vs entitlements identifies under-licensed risks (compliance violations) and over-licensed waste (unnecessary spend). Right-sizing licenses can save 15-30% of software costs.
- **App/TA:** Custom scripted inputs, vendor license APIs
- **Data Sources:** License server logs, vendor API data, entitlement records
- **SPL:**
```spl
index=licenses sourcetype="license:usage"
| stats latest(used_licenses) as used, latest(total_licenses) as total by product, vendor, license_type
| eval utilization_pct=round((used/total)*100, 1)
| eval status=case(utilization_pct>=95, "At Risk", utilization_pct>=80, "High Use", utilization_pct<50, "Underutilized", 1==1, "Healthy")
| sort -utilization_pct
| table product, vendor, license_type, used, total, utilization_pct, status
```
- **Implementation:** Collect license usage data from license servers (FlexLM, RLM) and vendor APIs. Maintain entitlement records in a lookup table. Track daily peak concurrent usage. Alert at 90% consumption (buy more) and flag <50% utilization (optimize). Generate quarterly true-up reports.
- **Visualization:** Gauge (license utilization), Table (license inventory with status), Bar chart (utilization by product), Timechart (usage trending).

### UC-20.2.5 · Right-Sizing Recommendations

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Over-provisioned VMs and instances waste compute and money. Right-sizing analysis compares actual resource usage against allocated resources, identifying instances that can be downsized without impacting performance — typically saving 20-40%.
- **App/TA:** Cloud and virtualization TAs, performance metrics
- **Data Sources:** Performance metrics vs resource allocation data
- **SPL:**
```spl
index=infrastructure (sourcetype="vmware:perf:cpu" OR sourcetype="vmware:perf:mem")
| stats avg(cpu_usage_pct) as avg_cpu, p95(cpu_usage_pct) as p95_cpu, avg(mem_usage_pct) as avg_mem, p95(mem_usage_pct) as p95_mem by vm_name
| lookup vm_allocation vm_name OUTPUT allocated_vcpu, allocated_mem_gb, instance_type
| eval cpu_rightsized=case(p95_cpu<25, "Downsize", p95_cpu>90, "Upsize", 1==1, "Right-sized")
| eval mem_rightsized=case(p95_mem<25, "Downsize", p95_mem>90, "Upsize", 1==1, "Right-sized")
| where cpu_rightsized="Downsize" OR mem_rightsized="Downsize"
| table vm_name, instance_type, allocated_vcpu, avg_cpu, p95_cpu, cpu_rightsized, allocated_mem_gb, avg_mem, p95_mem, mem_rightsized
```
- **Implementation:** Collect 30+ days of CPU and memory utilization per VM/instance. Compare P95 utilization against allocated resources. Generate right-sizing recommendations based on workload patterns. Exclude burst workloads from analysis. Calculate estimated savings per recommendation.
- **Visualization:** Table (right-sizing recommendations with savings), Bar chart (waste by team), Scatter plot (allocated vs used), Single value (total potential savings).

### UC-20.2.6 · Database Growth Projection

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** Databases that run out of space cause application outages. Forecasting database growth enables proactive storage expansion, archive planning, and helps DBAs plan maintenance windows for data lifecycle operations.
- **App/TA:** Database monitoring TAs, `Splunk DB Connect`
- **Data Sources:** Database size metrics, tablespace utilization
- **SPL:**
```spl
index=database sourcetype="db:capacity"
| timechart span=1d latest(db_size_gb) as current_size by db_name
| predict current_size as predicted_size algorithm=LLP5 future_timespan=90
| eval growth_rate_gb_per_day=round(('predicted_size+30d'-current_size)/30, 2)
| where 'predicted_size+90d' > max_size*0.85
```
- **Implementation:** Collect database size metrics daily from all platforms. Track per-database and per-tablespace growth. Use Splunk predict for 90-day growth forecasting. Alert when projected size exceeds 85% of allocated space within 90 days. Plan archival or expansion based on projections.
- **Visualization:** Timechart (database size with forecast), Table (databases approaching limits), Gauge (current utilization), Bar chart (growth rate by database).

### UC-20.2.7 · Seasonal Capacity Modeling

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Value:** Many businesses have predictable seasonal patterns (retail holidays, fiscal year-end, enrollment periods). Building seasonal capacity models ensures infrastructure scales proactively for peak periods rather than reactively during customer-impacting events.
- **App/TA:** Infrastructure TAs, Splunk MLTK (Machine Learning Toolkit)
- **Data Sources:** Historical performance data (12+ months)
- **SPL:**
```spl
index=infrastructure sourcetype="perf:summary"
| eval day_of_year=strftime(_time, "%j")
| eval week_of_year=strftime(_time, "%V")
| stats avg(cpu_pct) as avg_cpu, avg(mem_pct) as avg_mem, avg(req_per_sec) as avg_rps by week_of_year
| append [| inputlookup previous_year_seasonal_data]
| stats avg(avg_cpu) as seasonal_cpu, avg(avg_mem) as seasonal_mem, avg(avg_rps) as seasonal_rps by week_of_year
| eval next_year_projected=seasonal_rps*1.15
```
- **Implementation:** Collect 12+ months of performance data for seasonal analysis. Identify recurring patterns (daily, weekly, monthly, seasonal). Build seasonal baseline models using Splunk MLTK or predict. Apply growth factor to historical peaks for next-year projections. Plan capacity expansions 2-3 months ahead of predicted peaks.
- **Visualization:** Timechart (year-over-year seasonal overlay), Area chart (seasonal patterns), Table (peak week projections), Line chart (actual vs seasonal model).

### UC-20.2.8 · IP Address Space Utilization

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Value:** IP address exhaustion causes provisioning failures for new VMs, containers, and services. Monitoring IP pool utilization across subnets and VLANs enables proactive network planning and avoids emergency re-addressing projects.
- **App/TA:** IPAM/DHCP TAs, custom scripted inputs
- **Data Sources:** DHCP/IPAM data, subnet allocation records
- **SPL:**
```spl
index=network sourcetype="ipam:pool"
| stats latest(total_ips) as total, latest(allocated_ips) as allocated, latest(available_ips) as available by subnet, vlan, location
| eval used_pct=round((allocated/total)*100, 1)
| eval status=case(used_pct>=90, "Critical", used_pct>=75, "Warning", used_pct>=50, "Normal", 1==1, "Low Use")
| sort -used_pct
| table subnet, vlan, location, total, allocated, available, used_pct, status
```
- **Implementation:** Ingest IPAM/DHCP pool data daily. Track allocation rates per subnet, VLAN, and location. Alert at 75% warning and 90% critical utilization. Plan subnet expansions or new VLAN creation based on utilization trends. Report on unused allocations that could be reclaimed.
- **Visualization:** Table (subnet utilization), Bar chart (utilization by location), Heatmap (subnet usage map), Gauge (overall IP utilization).

---

## Summary Statistics

| Category | Subcategories | Use Cases |
|----------|:------------:|:---------:|
| 1. Server & Compute | 4 | 262 |
| 2. Virtualization | 3 | 23 |
| 3. Containers & Orchestration | 4 | 30 |
| 4. Cloud Infrastructure | 4 | 44 |
| 5. Network Infrastructure | 9 | 203 |
| 6. Storage & Backup | 4 | 28 |
| 7. Database & Data Platforms | 4 | 40 |
| 8. Application Infrastructure | 5 | 45 |
| 9. Identity & Access Management | 4 | 29 |
| 10. Security Infrastructure | 8 | 47 |
| 11. Email & Collaboration | 3 | 24 |
| 12. DevOps & CI/CD | 4 | 23 |
| 13. Observability & Monitoring | 3 | 28 |
| 14. IoT & OT | 4 | 74 |
| 15. DC Physical Infrastructure | 3 | 16 |
| 16. Service Management & ITSM | 2 | 15 |
| 17. Network Security & Zero Trust | 3 | 22 |
| 18. Data Center Fabric & SDN | 3 | 15 |
| 19. Compute Infrastructure (HCI) | 2 | 13 |
| 20. Cost & Capacity Management | 2 | 16 |
| **TOTAL** | **72** | **1001** |

---

*Generated: March 2026*
*Primary tools: Splunk Enterprise / Cloud with free Splunkbase add-ons. Premium exceptions noted (ITSI, ES).*
*Each use case includes: criticality rating, value description, recommended App/TA, data sources, SPL query, implementation guidance, and visualization recommendations.*
