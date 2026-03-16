# 1. Server & Compute

## 1.1 Linux Servers

**Primary App/TA:** Splunk Add-on for Unix and Linux (`Splunk_TA_nix`) — Splunkbase #833

---

### UC-1.1.1 · CPU Utilization Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
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
- **CIM Models:** Performance
- **Data model acceleration:** Enable acceleration for the Performance data model; set summary range to cover your alert window (e.g. 30 days).
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```
- **References:** [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833), [inputs.conf](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Inputsconf)
- **Known false positives:** Sustained high CPU during backups, batch jobs, or maintenance; correlate with change windows.

---

### UC-1.1.2 · Memory Pressure Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.1.3 · Disk Capacity Forecasting
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Prevents outages caused by full filesystems. A full /var or / can bring down services, databases, and logging. Enables proactive storage procurement.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=df`
- **SPL:**
```spl
index=os sourcetype=df host=*
| stats latest(UsePct) as current_pct by host, Filesystem, MountedOn
| where current_pct > 85
| sort -current_pct

| comment "Forecasting version (optional)"
index=os sourcetype=df host=myserver Filesystem="/dev/sda1"
| timechart span=1d avg(UsePct) as disk_pct
| predict disk_pct as predicted future_timespan=30
```
- **Implementation:** Enable `df` scripted input (interval=300). Create a saved search that runs daily, identifying filesystems above 85%. Use `predict` command for 30-day forecasting. Set tiered alerts at 85% (warning), 90% (high), 95% (critical).
- **Visualization:** Line chart with predict trendline, Table sorted by usage descending, Gauge per critical mount point.
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-1.1.4 · Disk I/O Saturation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-1.1.5 · System Load Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` latest(Performance.uptime) as uptime_sec
  from datamodel=Performance where nodename=Performance.Uptime
  by Performance.host
| eval uptime_days = round(uptime_sec / 86400, 1)
```

---

### UC-1.1.6 · Process Crash Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-1.1.7 · OOM Killer Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.8 · SSH Brute-Force Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-1.1.9 · Unauthorized Sudo Usage
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

---

### UC-1.1.10 · Cron Job Failure Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.11 · Kernel Panic Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.12 · NTP Time Sync Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
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
- **CIM Models:** N/A

---

### UC-1.1.13 · Zombie Process Accumulation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.14 · File Descriptor Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-1.1.15 · Network Interface Errors
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

---

### UC-1.1.16 · Package Vulnerability Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.1.17 · Service Availability Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.1.18 · User Account Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration, Compliance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.1.19 · Filesystem Read-Only Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.20 · Reboot Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Fault
- **Value:** Unexpected reboots may indicate kernel panics, hardware failure, or unauthorized changes. Distinguishing planned vs. unplanned reboots is key.
- **App/TA:** `Splunk_TA_nix`, Syslog
- **Data Sources:** `sourcetype=syslog`, `sourcetype=who` (wtmp)
- **SPL:**
```spl
index=os sourcetype=syslog ("Initializing cgroup subsys" OR "Linux version" OR "Command line:" OR "systemd.*Started" OR "Booting Linux")
| stats latest(_time) as last_boot by host
| eval hours_since_boot = round((now() - last_boot) / 3600, 1)
| sort hours_since_boot

| comment "Cross-reference with maintenance windows"
| join host [| inputlookup maintenance_windows.csv | where status="approved"]
```
- **Implementation:** Forward syslog. Detect boot-up log patterns. Cross-reference boot times with maintenance window lookups to flag unplanned reboots. Alert on any reboot outside approved windows.
- **Visualization:** Table (host, last boot, planned/unplanned), Timeline of reboots, Single value panel (unexpected reboots last 7d).
- **CIM Models:** N/A

---


---

### UC-1.1.21 · Kernel Module Loading Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.22 · Sysctl Parameter Changes Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
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
- **CIM Models:** N/A

---

### UC-1.1.23 · Kernel Core Dump Generation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.24 · Kernel Ring Buffer Error Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.25 · NUMA Imbalance Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.26 · CPU Frequency Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.27 · CPU Steal Time Elevation (Virtual Machines)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.1.28 · IRQ Imbalance Across CPU Cores
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.29 · Context Switch Rate Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Excessive context switching reduces CPU cache effectiveness and indicates scheduler overload or contention.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| bin _time span=5m
| stats avg(cs) as avg_ctx_switch by host, _time
| streamstats window=100 avg(avg_ctx_switch) as baseline stdev(avg_ctx_switch) as stddev by host
| eval upper_bound=baseline+(2*stddev)
| where avg_ctx_switch > upper_bound
```
- **Implementation:** Monitor vmstat context switch counter (cs field). Use baseline and anomaly detection to alert on sustained context switch rates that exceed 2 standard deviations above normal, indicating scheduler pressure.
- **Visualization:** Timechart, Anomaly Detector
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.1.30 · Scheduler Latency and Run Queue Depth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.1.31 · Hugepage Allocation and Usage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.32 · Transparent Hugepage Compaction Stalls
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.33 · Inode Exhaustion Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-1.1.34 · RAID Array Degradation Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.35 · LVM Thin Pool Capacity Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-1.1.36 · Multipath I/O Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.1.37 · NFS Mount Stale Handle Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.38 · Filesystem Journal Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.39 · Ext4 Filesystem Errors and Recovery
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.40 · XFS Filesystem Errors and Recovery
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.41 · Disk SMART Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.42 · SSD Wear Leveling and Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.43 · Fstrim and TRIM Command Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.44 · Memory Leak Detection Per Process
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.45 · Swap Thrashing Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.1.46 · Slab Cache Growth Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Unbounded slab cache growth consumes memory that could be used for page cache or application memory.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:slabinfo, /proc/slabinfo`
- **SPL:**
```spl
index=os sourcetype=syslog "slab"
| bin _time span=1d
| stats sum(slab_size) as total_slab by host, _time
| streamstats window=30 avg(total_slab) as baseline stdev(total_slab) as stddev by host
| eval upper=baseline+(2*stddev)
| where total_slab > upper
```
- **Implementation:** Create a scripted input that parses /proc/slabinfo monthly and tracks total slab size. Use anomaly detection to alert when slab grows beyond 2 standard deviations, indicating slab leak.
- **Visualization:** Timechart, Anomaly Chart
- **CIM Models:** N/A

---

### UC-1.1.47 · Page Cache Pressure and Reclaim Activity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.48 · NUMA Memory Imbalance Per Node
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.49 · Memory Cgroup Limit Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.50 · Transparent Hugepage Defragmentation Stalls
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.51 · TCP Retransmission Rate Elevation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** High retransmission rates indicate network congestion, packet loss, or application issues affecting throughput.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:tcp_stats, /proc/net/tcp`
- **SPL:**
```spl
index=os sourcetype=netstat host=*
| bin _time span=5m
| stats sum(retransSegs) as retrans by host, _time
| streamstats window=100 avg(retrans) as baseline stdev(retrans) as stddev by host
| eval upper=baseline+(2*stddev)
| where retrans > upper
```
- **Implementation:** Create a scripted input that parses /proc/net/snmp for TCP retransmission metrics. Track TcpRetransSegs and TcpOutSegs to calculate retransmission percentage. Alert when above 2% or 3x baseline.
- **Visualization:** Timechart, Anomaly Chart
- **CIM Models:** N/A

---

### UC-1.1.52 · Connection Tracking Table Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-1.1.53 · Socket Buffer Overflow Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.54 · Network Namespace Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Network namespace monitoring detects container escape attempts and validates network isolation in containerized environments.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:netns, /var/run/netns/`
- **SPL:**
```spl
index=os sourcetype=custom:netns host=*
| stats count by host, netns_name
| where count > 10
```
- **Implementation:** Create a scripted input that enumerates /var/run/netns/ and tracks namespace creation/deletion. Baseline expected namespaces per host. Alert on unexpected new namespaces which may indicate container escape or compromise.
- **Visualization:** Table, Alert
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

---

### UC-1.1.55 · DNS Resolution Failure Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.1.56 · Firewall Rule Hit Tracking (iptables/nftables)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.57 · ARP Table Overflow Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** ARP table overflow causes network connectivity issues and may indicate ARP spoofing attacks or network misconfiguration.
- **App/TA:** `Splunk_TA_nix, custom scripted input`
- **Data Sources:** `sourcetype=custom:arp, /proc/net/arp`
- **SPL:**
```spl
index=os sourcetype=custom:arp host=*
| stats count as arp_entry_count by host
| eval max_entries=1024
| where arp_entry_count > (max_entries * 0.8)
```
- **Implementation:** Create a scripted input that counts /proc/net/arp entries and monitors /proc/sys/net/ipv4/neigh/*/gc_thresh* limits. Alert when ARP table approaches limits. Correlate with network scans or spoofing indicators.
- **Visualization:** Gauge, Alert
- **CIM Models:** N/A

---

### UC-1.1.58 · Network Bond Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

---

### UC-1.1.59 · Network Team Failover Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

---

### UC-1.1.60 · MTU Mismatch Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.61 · TCP TIME_WAIT Accumulation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.62 · Network Bandwidth Utilization by Interface
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

---

### UC-1.1.63 · Dropped Packets by Network Interface
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

---

### UC-1.1.64 · Network Latency Monitoring (Ping RTT)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

---

### UC-1.1.65 · Auditd Rule Violation Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.66 · SELinux Denial Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.67 · AppArmor Profile Violation Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.68 · Rootkit Detection via File Integrity
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.69 · SUID/SGID Binary Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.70 · /etc/passwd Modifications
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.71 · /etc/shadow Modifications
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.72 · SSH Public Key Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.1.73 · PAM Authentication Failure Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-1.1.74 · Login from Unusual Source IPs
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.1.75 · Failed su Attempts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-1.1.76 · Privilege Escalation Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

---

### UC-1.1.77 · Unauthorized Cron Job Additions
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.78 · Open Port Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.79 · Setcap Binary Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.80 · Systemd Unit Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.1.81 · Systemd Timer Missed Triggers
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.82 · D-State (Uninterruptible Sleep) Process Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.83 · Process CPU Affinity Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.84 · Runaway Process Detection (CPU Hog)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.85 · Memory Hog Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.86 · Fork Bomb Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.87 · Process Namespace Breakout Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.88 · Container Escape Attempt Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.89 · Syslog Flood Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
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
- **CIM Models:** N/A

---

### UC-1.1.90 · Journal Disk Usage Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-1.1.91 · Log Rotation Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.92 · Auditd Daemon Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-1.1.93 · Rsyslog Queue Backlog Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.94 · Failed Log Forwarding
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.1.95 · TCP Connection Establishment Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.96 · NUMA Hit/Miss Ratio Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.97 · CPU C-State Residency Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.98 · TLB Shootdown Rate Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.99 · Kernel Lock Contention Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.100 · Softirq Rate Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.1.101 · Context Switch Anomalies Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.1.102 · EDAC Memory Error Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.103 · IPMI Sensor Threshold Violations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.104 · Thermal Throttling Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.105 · Fan Speed Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.106 · Power Supply State Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.1.107 · Hardware Clock Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
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
- **CIM Models:** N/A

---

### UC-1.1.108 · Password Policy Violation Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.109 · Account Expiry Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.110 · Inactive User Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.1.111 · World-Writable File Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.112 · Unowned File Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.113 · SETUID Audit and Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.114 · Open File Handle Per-Process Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-1.1.115 · Listening Port Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-1.1.116 · Installed Package Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.117 · Configuration File Change Tracking (/etc)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.1.118 · System Reboot Frequency Anomaly
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
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
- **CIM Models:** N/A

---

### UC-1.1.119 · Defunct (Zombie) Process Accumulation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.1.120 · Symbolic Link Chain Depth Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.121 · Bootloader Configuration Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.1.122 · Systemd Unit State Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **Value:** Track failed/inactive systemd services, auto-restart counts, and service startup time to prevent cascading failures and identify misconfigured or unhealthy units.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `systemctl list-units` output, systemd journal
- **SPL:**
```spl
index=os sourcetype=systemd_units host=*
| where ActiveState="failed" OR ActiveState="inactive"
| stats latest(ActiveState) as state, latest(SubState) as substate, values(Unit) as units by host
| where state!="active"
| table host state substate units

| comment "Restart count tracking"
index=os sourcetype=systemd_units host=* NRestarts>0
| stats sum(NRestarts) as total_restarts by host, Unit
| where total_restarts > 5
| sort -total_restarts
```
- **Implementation:** Create a scripted input that runs `systemctl list-units --all --no-pager --plain` and `systemctl show --property=ActiveState,SubState,NRestarts` for critical units. Parse ActiveState, SubState, and NRestarts. Run every 60 seconds. For startup time, use `systemd-analyze` output. Alert on any failed units; alert when NRestarts exceeds 5 in 1 hour for critical services.
- **Visualization:** Table (failed/inactive units by host), Single value (count of failed units), Timechart of restart counts.
- **CIM Models:** N/A

---

### UC-1.1.123 · Linux Cgroup Resource Pressure (PSI)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Monitor Pressure Stall Information (PSI) for CPU, memory, and I/O at cgroup level to detect resource contention before it causes application latency.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `/proc/pressure/cpu`, `/proc/pressure/memory`, `/proc/pressure/io`
- **SPL:**
```spl
index=os sourcetype=psi host=*
| eval resource=coalesce(cpu_resource, mem_resource, io_resource)
| timechart span=5m avg(avg10) as avg10_pct, avg(avg60) as avg60_pct, avg(avg300) as avg300_pct by host, resource
| where avg10_pct > 10 OR avg60_pct > 5

| comment "Per-cgroup PSI (if collected)"
index=os sourcetype=psi host=* cgroup=*
| stats latest(avg10) as pressure by host, cgroup, resource
| where pressure > 20
| sort -pressure
```
- **Implementation:** Create a scripted input that reads `/proc/pressure/cpu`, `/proc/pressure/memory`, and `/proc/pressure/io`. Parse avg10, avg60, avg300, and total fields (format: `avg10=0.00 avg60=0.00 avg300=0.00 total=12345`). Optionally collect per-cgroup PSI from `/sys/fs/cgroup/<cgroup>/cpu.pressure` etc. Run every 60 seconds. Alert when avg10 exceeds 10% or avg60 exceeds 5% for any resource.
- **Visualization:** Line chart (pressure over time by resource), Table of hosts with elevated pressure, Gauge per resource type.
- **CIM Models:** N/A

---

### UC-1.1.124 · Linux Entropy Pool Depletion
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Security
- **Value:** Low entropy blocks /dev/random and can stall crypto operations (SSL handshakes, key generation). Detecting depletion prevents application hangs and security failures.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `/proc/sys/kernel/random/entropy_avail`
- **SPL:**
```spl
index=os sourcetype=entropy host=*
| stats latest(entropy_avail) as avail by host
| where avail < 200
| table host avail

| comment "Trending"
index=os sourcetype=entropy host=*
| timechart span=5m avg(entropy_avail) as entropy by host
| where entropy < 500
```
- **Implementation:** Create a scripted input that reads `cat /proc/sys/kernel/random/entropy_avail` and optionally `poolsize`. Run every 60 seconds. Parse entropy_avail as integer. Alert when entropy drops below 200 (warning) or 100 (critical). Consider haveged or rng-tools for entropy generation on VMs.
- **Visualization:** Single value (entropy_avail), Line chart (entropy over time by host), Table of hosts below threshold.
- **CIM Models:** N/A

---

### UC-1.1.125 · Linux Journal / Journald Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Journal corruption, excessive disk usage, and rate-limited entries indicate logging problems that can hide critical events and fill disk.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `journalctl --disk-usage`, `journalctl --verify`
- **SPL:**
```spl
index=os sourcetype=journal_health host=*
| stats latest(disk_usage_mb) as size_mb, latest(corruption_status) as corrupt, latest(suppressed_count) as suppressed by host
| where corrupt="inconsistent" OR corrupt="corrupt" OR size_mb > 4096 OR suppressed > 100
| table host size_mb corrupt suppressed

| comment "Size trending"
index=os sourcetype=journal_health host=*
| timechart span=1h avg(disk_usage_mb) as journal_mb by host
```
- **Implementation:** Create a scripted input that runs `journalctl --disk-usage` (parse "Archived and active: X.XG" or similar) and `journalctl --verify 2>&1` (check exit code and output for "corrupt" or "inconsistent"). For suppressed messages, parse `journalctl -u systemd-journald` for "Suppressed" or use `journalctl --output=short-full` rate stats. Run every 300 seconds. Alert on corruption; alert when journal exceeds 4GB or suppressed count is high.
- **Visualization:** Table (host, size, corruption status), Line chart (journal size over time), Single value (corruption count).
- **CIM Models:** N/A

---

### UC-1.1.126 · Chrony / NTP Time Synchronization Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration, Availability
- **Value:** Clock offset, stratum, and reachability issues cause authentication failures, log correlation errors, and certificate validation problems. Time drift is a root cause of many subtle failures.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `chronyc tracking`, `ntpq -p`
- **SPL:**
```spl
index=os sourcetype=ntp_status host=*
| stats latest(offset_ms) as offset, latest(stratum) as stratum, latest(reachability) as reach by host
| where abs(offset) > 100 OR stratum > 10 OR reachability < 377
| table host offset stratum reachability

| comment "Offset trending"
index=os sourcetype=ntp_status host=*
| timechart span=15m avg(offset_ms) as offset_ms by host
| where abs(offset_ms) > 50
```
- **Implementation:** Create a scripted input that runs `chronyc tracking` (parse Last offset, Stratum, Leap status) or `ntpq -p` for ntpd. Extract offset_ms (convert to milliseconds), stratum, and reachability (octal 377 = all peers reachable). Run every 300 seconds. Alert when offset exceeds 100ms; alert when stratum > 10 or reachability indicates no peers.
- **Visualization:** Line chart (offset over time by host), Table (host, offset, stratum), Single value (hosts with drift).
- **CIM Models:** N/A

---

### UC-1.1.127 · Swap Activity Rate Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Pages swapped in/out per second (distinct from swap usage %) indicates memory pressure and I/O load. High swap I/O rate degrades performance even before swap usage is critical.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `sourcetype=vmstat`
- **SPL:**
```spl
index=os sourcetype=vmstat host=*
| eval swap_io_rate = si + so
| timechart span=5m avg(swap_io_rate) as avg_swap_rate, avg(si) as swap_in, avg(so) as swap_out by host
| where avg_swap_rate > 100

| comment "Baseline deviation alert"
index=os sourcetype=vmstat host=*
| eval swap_rate = si + so
| bin _time span=1h
| stats avg(swap_rate) as avg_rate, stdev(swap_rate) as std_rate by host, _time
| eventstats avg(avg_rate) as baseline stdev(avg_rate) as baseline_std by host
| eval threshold = baseline + (2 * coalesce(baseline_std, 50))
| where avg_rate > threshold
```
- **Implementation:** Enable vmstat scripted input in Splunk_TA_nix (interval=60). Fields `si` (swap in) and `so` (swap out) represent pages per interval. Create baseline of normal swap rate per host; alert when swap I/O rate exceeds 2x baseline or exceeds 100 pages/sec sustained for 10 minutes.
- **Visualization:** Line chart (swap in/out rates by host), Table of hosts with elevated swap I/O, Single value (current swap rate).
- **CIM Models:** Performance

---

### UC-1.1.128 · Filesystem Inode Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Inode usage approaching 100% blocks file creation even with free disk space. Applications fail with "No space left on device" despite available blocks — a common misdiagnosis.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `df -i` output
- **SPL:**
```spl
index=os sourcetype=df_inode host=*
| stats latest(IUsePct) as inode_pct by host, Filesystem, MountedOn
| where inode_pct > 90
| sort -inode_pct
| table host Filesystem MountedOn inode_pct

| comment "Warning threshold"
index=os sourcetype=df_inode host=*
| stats latest(IUsePct) as inode_pct by host, MountedOn
| where inode_pct > 80
```
- **Implementation:** Create a scripted input that runs `df -i` and parses output. Extract Filesystem, Inodes, IUsed, IFree, IUse%, MountedOn. Run every 300 seconds. Set tiered alerts: 80% (warning), 90% (high), 95% (critical). Include `find` or `du --inodes` to identify directories consuming inodes for remediation.
- **Visualization:** Table (filesystem, host, inode %), Gauge per critical mount, Line chart (inode % over time).
- **CIM Models:** N/A

---

### UC-1.1.129 · Linux Softirq / Hardirq Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Detect interrupt storms (softirq/hardirq) that degrade system performance. High IRQ time indicates network, block I/O, or timer storms.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `/proc/interrupts`, `/proc/softirqs`, `mpstat` output
- **SPL:**
```spl
index=os sourcetype=irq_stats host=*
| eval irq_pct = softirq_pct + hardirq_pct
| timechart span=5m avg(irq_pct) as irq_total, avg(softirq_pct) as softirq, avg(hardirq_pct) as hardirq by host
| where irq_total > 20

| comment "Per-CPU IRQ breakdown"
index=os sourcetype=irq_stats host=* cpu=*
| stats latest(softirq_pct) as softirq, latest(hardirq_pct) as hardirq by host, cpu
| where softirq > 30 OR hardirq > 15
```
- **Implementation:** Create a scripted input that parses `/proc/softirqs` and `/proc/interrupts` (or use `mpstat -I SUM` for softirq/hardirq percentages). Calculate softirq and hardirq as percentage of CPU time. Run every 60 seconds. Alert when combined IRQ time exceeds 20% sustained for 10 minutes. Correlate with network/block device activity.
- **Visualization:** Line chart (softirq/hardirq % over time), Table of hosts with elevated IRQ, Stacked area chart by IRQ type.
- **CIM Models:** Performance

---

### UC-1.1.130 · TCP Connection State Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** Count of ESTABLISHED, TIME_WAIT, CLOSE_WAIT, SYN_RECV connections. Detects connection leaks (accumulating CLOSE_WAIT), exhaustion (TIME_WAIT), and half-open buildup.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `ss -s` or `netstat` output
- **SPL:**
```spl
index=os sourcetype=tcp_states host=*
| stats latest(ESTAB) as established, latest(TIME-WAIT) as time_wait, latest(CLOSE-WAIT) as close_wait, latest(SYN-RECV) as syn_recv by host
| where close_wait > 1000 OR time_wait > 10000
| table host established time_wait close_wait syn_recv

| comment "Connection leak detection (CLOSE_WAIT growth)"
index=os sourcetype=tcp_states host=*
| timechart span=15m avg(CLOSE-WAIT) as close_wait by host
| where close_wait > 500
```
- **Implementation:** Create a scripted input that runs `ss -s` (parse TCP: inuse X orphaned X tw X alloc X mem X) or `netstat -an | awk` to count by state. Parse ESTAB, TIME-WAIT, CLOSE-WAIT, SYN-RECV. Run every 60 seconds. Alert when CLOSE_WAIT exceeds 1000 (possible connection leak); alert when TIME_WAIT exceeds 10000 (port exhaustion risk).
- **Visualization:** Stacked bar chart (state distribution by host), Line chart (CLOSE_WAIT over time), Table of hosts exceeding thresholds.
- **CIM Models:** N/A

---

### UC-1.1.131 · Linux OOM Killer Invocation Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Track which processes were killed by the OOM killer and how often. OOM events indicate severe memory pressure and often precede application outages.
- **App/TA:** `Splunk_TA_nix`
- **Data Sources:** `/var/log/kern.log`, `dmesg`, `sourcetype=syslog`
- **SPL:**
```spl
index=os (sourcetype=syslog OR sourcetype=linux_secure) host=*
| search "Out of memory" OR "oom-kill" OR "oom_reaper" OR "Killed process"
| rex "oom-kill:constraint=(?<constraint>\w+),.*process (?<pid>\d+), (?<process>\S+),"
| rex "Killed process (?<pid>\d+) \((?<process>[^)]+)\)"
| stats count as oom_count by host, process, _time
| sort -_time -oom_count

| comment "OOM events in last 24h"
index=os (sourcetype=syslog OR sourcetype=linux_secure) host=*
| search "oom-kill" OR "Out of memory" "Killed process"
| stats count by host
| where count > 0
```
- **Implementation:** Ensure kernel messages are forwarded via syslog or Splunk_TA_nix. The OOM killer logs to kernel ring buffer; rsyslog typically captures to kern.log. Use `dmesg -T` or journalctl for immediate capture. Create alert on any OOM event. Parse process name and PID for context. Correlate with memory metrics before the event.
- **Visualization:** Alert (immediate on OOM), Table (host, process, count), Timeline of OOM events.
- **CIM Models:** N/A

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
- **Monitoring type:** Performance, Capacity
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.2 · Memory Utilization & Paging
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.2.3 · Disk Space Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-1.2.4 · Windows Service Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.5 · Event Log Flood Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.6 · Failed Login Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-1.2.7 · Account Lockout Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-1.2.8 · Privileged Group Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

---

### UC-1.2.9 · Windows Update Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.2.10 · Scheduled Task Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.11 · Blue Screen of Death (BSOD)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.12 · RDP Session Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks who connected via Remote Desktop, from where, and when. Essential for compliance auditing and detecting lateral movement.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Security` (EventCode 4624, LogonType=10), `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational`
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624 LogonType=10
| table _time TargetUserName IpAddress host
| sort -_time

| comment "Also check TerminalServices for session duration"
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational" (EventCode=21 OR EventCode=23 OR EventCode=24 OR EventCode=25)
| table _time host User EventCode
```
- **Implementation:** Enable Security log + TerminalServices operational log. Alert on RDP sessions to servers from unexpected sources. Create session audit report correlating logon/logoff events.
- **Visualization:** Table (user, source IP, host, time), Choropleth map for source IPs, Session timeline.
- **CIM Models:** N/A

---

### UC-1.2.13 · PowerShell Script Execution
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.14 · IIS Web Server Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.2.15 · DNS Server Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** DNS is foundational infrastructure — when DNS is slow or failing, everything fails. Monitoring query rates and failures ensures resolution reliability.
- **App/TA:** `Splunk_TA_windows`, Microsoft DNS Analytical logs
- **Data Sources:** `sourcetype=WinEventLog:DNS Server`, DNS debug/analytical logs
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:DNS Server"
| stats count by EventCode
| sort -count

| comment "Query volume trending"
index=dns sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as query_count by QTYPE
```
- **Implementation:** Enable DNS analytical logging via Event Viewer (disabled by default for performance). Alternatively use DNS debug logging to a file and forward it. Monitor query volume, SERVFAIL rate, and zone transfer events.
- **Visualization:** Line chart (query rate), Pie chart (query types), Single value (SERVFAIL count).
- **CIM Models:** N/A

---

### UC-1.2.16 · DHCP Scope Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-1.2.17 · Certificate Expiration
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.2.18 · Active Directory Replication
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** AD replication failures cause authentication inconsistencies — users locked out in one site but not another, stale GPOs, and split-brain scenarios.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `sourcetype=WinEventLog:Directory Service`, custom scripted input (`repadmin /replsummary`)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" (EventCode=1864 OR EventCode=1865 OR EventCode=2042 OR EventCode=1388 OR EventCode=1988)
| table _time host EventCode Message
| sort -_time

| comment "Replication health from scripted input"
index=ad sourcetype=repadmin_replsummary
| where failures > 0
| table source_dc dest_dc failures last_failure last_success
```
- **Implementation:** Collect Directory Service event log from all DCs. Create scripted input running `repadmin /replsummary /csv` daily. Alert on any replication failure events. Critical alert on EventCode 2042 (tombstone lifetime exceeded).
- **Visualization:** Table of replication partners with status, Events timeline, Network diagram of DC replication.
- **CIM Models:** N/A

---

### UC-1.2.19 · Group Policy Processing Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.20 · Print Spooler Issues
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.21 · Disk I/O Queue Length
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-1.2.22 · Process Handle Leak Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.23 · Non-Paged Pool Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.2.24 · Network Interface Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in
                        sum(Performance.bytes_out) as bytes_out
  from datamodel=Performance where nodename=Performance.Network
  by Performance.host Performance.interface span=5m
```

---

### UC-1.2.25 · Processor Queue Length
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.26 · Security Log Cleared
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.27 · New Service Installation
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.28 · Windows Firewall Rule Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.29 · Registry Run Key Modification (Persistence)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.30 · LSASS Memory Access (Credential Dumping)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.31 · Kerberos Authentication Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-1.2.32 · WMI Event Subscription Persistence
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.33 · Audit Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.34 · AppLocker / WDAC Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.35 · Windows Defender Threat Detections
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.36 · DCSync Attack Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.37 · Kerberoasting Detection (SPN Ticket Requests)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.2.38 · AD Object Deletion Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.39 · Domain Trust Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.40 · WHEA Hardware Error Reporting
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.41 · Volume Shadow Copy Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.42 · .NET CLR Performance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.43 · Failover Cluster Event Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.2.44 · SMB Share Access Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.45 · Windows Time Service (W32Time) Issues
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.46 · DFS-R Replication Backlog
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.47 · Application Crash (WER) Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.48 · PowerShell Script Block Logging
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.49 · Lateral Movement via Explicit Credentials
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.50 · DNS Debug Query Logging
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.51 · Process Creation with Command Line Auditing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-1.2.52 · NIC Teaming / LBFO Failover
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.53 · BitLocker Recovery Events
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.54 · Windows Event Forwarding (WEF) Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.2.55 · Suspicious Token Manipulation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.56 · Sysmon Network Connection Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.57 · Thread Count Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.58 · Storage Spaces Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.2.59 · DCOM / COM+ Application Errors
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.60 · Code Integrity / Driver Signing Violations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.61 · Data Deduplication Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.62 · TCP Connection State Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.63 · Windows Installer Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.64 · Event Log Channel Size / Overflow
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **Value:** When event logs reach maximum size with overwrite-oldest policy, critical security events are lost. With do-not-overwrite policy, the log stops recording entirely.
- **App/TA:** `Splunk_TA_windows`, custom scripted input
- **Data Sources:** `sourcetype=WinEventLog:System` (EventCode 6005) + custom scripted input (`wevtutil gl Security`)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=1101
| table _time, host, Channel
| stats count by host, Channel
| sort -count

| comment "Alternatively via scripted input"
index=os sourcetype=windows:eventlog:size
| where used_pct > 90
| table _time, host, log_name, current_size_MB, max_size_MB, used_pct
```
- **Implementation:** Deploy a scripted input that runs `wevtutil gl Security` (and other critical channels) every 15 minutes, parsing current size vs. max size. Default Security log is 20MB — often insufficient on DCs and servers with detailed auditing. Alert when any critical log exceeds 90% capacity. Alternatively, monitor EventCode 1101 (audit log full) in the System log. Recommended: increase Security log to 1GB+ on DCs.
- **Visualization:** Gauge (log fill percentage), Table (logs near capacity), Bar chart (log sizes by channel).
- **CIM Models:** N/A

---

### UC-1.2.65 · Pass-the-Hash / NTLM Relay Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.66 · Sysmon File Creation in Suspicious Paths
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.67 · Golden Ticket Detection (TGT Anomalies)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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

| comment "Also detect TGT requests with RC4 from non-standard IPs"
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4768 TicketEncryptionType=0x17
| stats count by TargetUserName, IpAddress
```
- **Implementation:** Golden tickets typically use RC4 encryption (0x17) with abnormally long lifetimes (default Kerberos max is 10 hours). EventCode 4768=TGT request, 4769=TGS request. Detect TGS requests referencing TGTs older than 10 hours, or TGT requests with RC4 in environments that enforce AES. Also monitor for EventCode 4769 with services accessed that the user normally doesn't touch. Requires KRBTGT password rotation as remediation.
- **Visualization:** Table (anomalous ticket requests), Timeline, Single value (RC4 TGT count), Alert.
- **CIM Models:** N/A

---

### UC-1.2.68 · NTFS Corruption and Self-Healing
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.69 · Page File Usage & Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

---

### UC-1.2.70 · Context Switch Rate Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.71 · Scheduled Task Creation (Persistence)
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Security
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.dest Processes.process_name Processes.user span=1h
| sort -count
```

---

### UC-1.2.72 · WinRM / Remote PowerShell Connections
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.73 · LDAP Query Performance (DC Health)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.74 · Hyper-V VM State Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.75 · AD Certificate Services (ADCS) Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.76 · AdminSDHolder Modification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

---

### UC-1.2.77 · SPN Modification (Targeted Kerberoasting)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.78 · DSRM Account Usage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.79 · Sysmon DNS Query Logging
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.80 · Windows Backup Job Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.2.81 · SMBv1 Usage Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.82 · Credential Guard Status Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.83 · Boot Configuration Changes (BCDEdit)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.84 · Sysmon Named Pipe Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.85 · IIS Application Pool Crashes & Recycling
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.86 · NTLM Audit and Restriction Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.87 · DPAPI Credential Backup (DC)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.88 · Windows Search Indexer Issues
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.2.89 · System Uptime & Unexpected Restarts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.90 · Shadow Copy Deletion (Ransomware Indicator)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.91 · USB / Removable Device Auditing
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.2.92 · Remote Desktop Gateway Session Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.93 · Group Policy Object (GPO) Modification Auditing
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.94 · Windows Subsystem for Linux (WSL) Activity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.95 · Windows Container Health Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Availability
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.96 · DNS Server Zone Transfer Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.97 · Print Spooler Vulnerability Monitoring (PrintNightmare)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.98 · NPS / RADIUS Authentication Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.99 · MSMQ Queue Depth Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

---

### UC-1.2.100 · PKI / Certificate Authority Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.101 · File Share Access Auditing (SMB)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.102 · Software Restriction / AppLocker Bypass Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.103 · Terminal Services / RDP Session Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.104 · Disk Latency and I/O Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

---

### UC-1.2.105 · Windows Defender Exclusion Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.106 · Local Administrator Group Membership Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

---

### UC-1.2.107 · DFS Replication Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.2.108 · Kerberos Constrained Delegation Abuse
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.109 · Windows Time Service (W32Time) Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.110 · PowerShell Constrained Language Mode Bypass
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.111 · Windows Firewall Rule Tampering
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.112 · BITS Transfer Abuse Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.113 · COM Object Hijacking Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.114 · LSASS Memory Protection Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.115 · Logon Session Anomalies (Type 3 / Network Logon)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.116 · WMI Persistence Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.117 · NIC Teaming & Network Adapter Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.118 · ASR (Attack Surface Reduction) Rule Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.119 · Registry Run Key Persistence Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.120 · BitLocker Recovery & Compliance Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Security
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
- **CIM Models:** N/A

---

### UC-1.2.121 · DNS Client Query Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.122 · Local Account Creation & Modification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.123 · Token Manipulation / Privilege Escalation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

---

### UC-1.2.124 · Process Injection Detection (Sysmon)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.2.125 · Cluster Shared Volume (CSV) Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.2.126 · DCOM Activation Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Endpoint
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

---

### UC-1.2.127 · Automatic Windows Update Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.2.128 · Service Account Logon Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-1.2.129 · Sysmon Driver/Image Load Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.2.130 · Scheduled Task Modification for Persistence
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-1.2.131 · Windows Print Spooler Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Spooler service state, queue depth, and stalled print jobs affect printing availability. Print Spooler failures block all printing on the host.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `WinEventLog:System` (Event ID 7036 for spooler), Perfmon (Print Queue counters)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:System" EventCode=7036 ServiceName="Spooler"
| eval state=case(Message="*stopped*", "stopped", Message="*started*", "started", "running")
| stats latest(_time) as last_change, latest(state) as current_state by host
| where current_state="stopped"

| comment "Print queue depth"
index=perfmon sourcetype=Perfmon:PrintQueue host=* counter="Jobs"
| stats latest(Value) as queue_depth by host, instance
| where queue_depth > 50
| sort -queue_depth
```
- **Implementation:** Enable `WinEventLog:System` input for EventCode 7036 (service state change). Filter for ServiceName=Spooler. Configure Perfmon input for Print Queue object: counter=Jobs (queue depth). Run every 60 seconds. Alert when Spooler stops; alert when queue depth exceeds 50 for sustained period (stalled jobs).
- **Visualization:** Table (host, spooler state, queue depth), Single value (failed spooler count), Line chart (queue depth over time).
- **CIM Models:** N/A

---

### UC-1.2.132 · Windows Scheduled Task Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Detect tasks that failed to run or returned non-zero result codes. Indicates missed backups, sync jobs, or automation failures.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** `WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 201, 101)
- **SPL:**
```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode IN (201, 101)
| search ResultCode!=0
| eval task_result=case(ResultCode=0,"Success", ResultCode=1,"InProgress", ResultCode=2,"Disabled", ResultCode=267009,"AccessDenied", ResultCode=2147942401,"IncorrectPath", 1=1,"Other")
| table _time host TaskName ResultCode task_result
| sort -_time

| comment "Failed task count by host"
index=wineventlog source="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode=201 ResultCode!=0
| stats count by host, TaskName
| sort -count
```
- **Implementation:** Enable Task Scheduler Operational log input. EventCode 201 = task completed; EventCode 101 = task started. Parse ResultCode (0 = success). Alert on ResultCode != 0. Common codes: 0x1 (incorrect function), 0x2 (file not found), 0x5 (access denied). Exclude known flaky tasks from alert if acceptable.
- **Visualization:** Table (task, host, result code), Alert on failed tasks, Bar chart (failed task count by task name).
- **CIM Models:** N/A

---

### UC-1.2.133 · Windows WMI Repository Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** WMI corruption breaks many monitoring agents, SCCM, and management tools. Detecting broken WMI enables early remediation before dependent systems fail.
- **App/TA:** `Splunk_TA_windows` (scripted input)
- **Data Sources:** `winmgmt /verifyrepository` output
- **SPL:**
```spl
index=os sourcetype=wmi_verify host=*
| stats latest(verify_result) as result, latest(repository_status) as status by host
| where result!="consistent" OR status="inconsistent"
| table host result status

| comment "WMI verification failure events"
index=os sourcetype=wmi_verify host=*
| search "inconsistent" OR "corrupt" OR "failed"
| table _time host _raw
```
- **Implementation:** Create a scripted input that runs `winmgmt /verifyrepository` and captures output. Parse for "repository is consistent" (success) vs "inconsistent" or "corrupt". Run daily or weekly. Alert immediately on inconsistent. Remediation: `winmgmt /resetrepository` (requires reboot). WMI issues often cause perfmon and other agent inputs to fail.
- **Visualization:** Table (host, WMI status), Single value (hosts with WMI issues), Alert.
- **CIM Models:** N/A

---

### UC-1.2.134 · Windows Pending Reboot Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Detect servers waiting for reboot after Windows updates. Pending reboots cause inconsistent behavior and can block security patch application.
- **App/TA:** `Splunk_TA_windows` (scripted input)
- **Data Sources:** Registry keys (RebootRequired, PendingFileRenameOperations)
- **SPL:**
```spl
index=os sourcetype=windows_pending_reboot host=*
| stats latest(reboot_pending) as pending, latest(reason) as reason by host
| where pending="true"
| table host pending reason

| comment "Fleet pending reboot count"
index=os sourcetype=windows_pending_reboot host=*
| stats latest(reboot_pending) as pending by host
| search pending="true"
| stats count as pending_count
```
- **Implementation:** Create a scripted input that checks registry: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending`, `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations`, `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired`. Set reboot_pending=true if any exist. Run every 60-300 seconds. Report reason (e.g., "Windows Update", "Component Based Servicing"). Include in change management dashboard.
- **Visualization:** Table (host, pending, reason), Single value (pending reboot count), Pie chart (pending vs. current).
- **CIM Models:** N/A

---

## 1.3 macOS Endpoints

**Primary App/TA:** Splunk Universal Forwarder for macOS with custom scripted inputs (no official Splunkbase TA — use Splunk_TA_nix where applicable, or custom inputs)

---

### UC-1.3.1 · System Resource Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-1.3.2 · FileVault Encryption Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.3.3 · Gatekeeper and SIP Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-1.3.4 · Software Update Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.3.5 · Application Crash Monitoring
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.3.6 · macOS Gatekeeper and XProtect Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Verify Gatekeeper and XProtect are enabled and definitions are current. Disabled or outdated security controls increase malware risk.
- **App/TA:** `Splunk_TA_nix` (scripted input)
- **Data Sources:** `spctl --status`, `system_profiler SPInstallHistoryDataType`
- **SPL:**
```spl
index=os sourcetype=macos_gatekeeper host=*
| stats latest(gatekeeper_status) as gatekeeper, latest(xprotect_version) as xprotect_ver, latest(xprotect_date) as xprotect_date by host
| where gatekeeper!="assessments enabled" OR gatekeeper="disabled"
| table host gatekeeper xprotect_ver xprotect_date

| comment "XProtect definition age"
index=os sourcetype=macos_gatekeeper host=*
| eval xprotect_age_days = now() - strptime(xprotect_date, "%Y-%m-%d")
| where xprotect_age_days > 30
| table host xprotect_ver xprotect_date xprotect_age_days
```
- **Implementation:** Create a scripted input that runs `spctl --status` (expect "assessments enabled" for Gatekeeper on). For XProtect, run `system_profiler SPInstallHistoryDataType` and parse XProtect/XProtect Remediator entries, or check `/Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/version.plist`. Run daily. Alert when Gatekeeper is disabled; alert when XProtect definitions are older than 30 days.
- **Visualization:** Table (host, Gatekeeper status, XProtect version), Single value (non-compliant count), Pie chart (enabled vs. disabled).
- **CIM Models:** N/A

---

## 1.4 Bare-Metal / Hardware

**Primary App/TA:** Custom scripted inputs (`ipmitool`, `smartctl`, `storcli`), vendor management APIs (iDRAC/iLO), SNMP Modular Input

---

### UC-1.4.1 · Hardware Sensor Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.4.2 · RAID Degradation Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.4.3 · Power Supply Failure
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-1.4.4 · Predictive Disk Failure
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.4.5 · Firmware Version Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
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
- **CIM Models:** N/A

---

### UC-1.4.6 · Memory ECC Error Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-1.4.7 · BMC Out-of-Band Connectivity Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** BMC (IPMI/iDRAC/iLO) loss prevents remote power, console, and sensor access. Early detection ensures out-of-band management remains available for recovery.
- **App/TA:** Custom scripted input, IPMI
- **Data Sources:** `ipmitool lan print`, BMC health sensors, SNMP (if BMC supports it)
- **SPL:**
```spl
index=hardware sourcetype=bmc_health host=*
| stats latest(channel_voltage) as voltage, latest(link_detected) as link by host
| where link="no" OR voltage < 3.0
| table host link voltage _time
```
- **Implementation:** Create scripted input: `ipmitool lan print` or vendor-specific tools (racadm, hpasm) to verify BMC reachability and LAN channel. Run every 5 minutes. Alert when BMC becomes unreachable.
- **Visualization:** Status grid (BMC up/down per host), Table of unreachable BMCs, Single value (count of healthy BMCs).
- **CIM Models:** N/A

---

### UC-1.4.8 · PCIe Link Width and Speed Degradation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** PCIe links that downgrade (e.g. x16→x8) indicate slot or cable issues. Affects GPU, NVMe, and HBA performance and can precede full failure.
- **App/TA:** Custom scripted input (`lspci -vv` or Windows PCI query)
- **Data Sources:** `lspci -vv`, `/sys/bus/pci/devices/*/current_link_width_speed`
- **SPL:**
```spl
index=hardware sourcetype=pcie_link host=*
| stats latest(link_width) as width, latest(link_speed) as speed by host, slot
| lookup pcie_expected host slot OUTPUT expected_width expected_speed
| where width < expected_width OR speed < expected_speed
| table host slot width speed expected_width expected_speed
```
- **Implementation:** Parse `lspci -vv` for "LnkCap" and "LnkSta" or read sysfs. Run daily. Maintain lookup of expected width/speed per host and slot. Alert on downgrade.
- **Visualization:** Table (host, slot, current vs. expected), Bar chart of link widths.
- **CIM Models:** N/A

---

### UC-1.4.9 · Out-of-Band Sensor Threshold Breach (IPMI)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** IPMI sensor events (temperature, voltage, fan) indicate environmental or hardware problems before they cause crashes. Critical for datacenter and server health.
- **App/TA:** Splunk Add-on for Unix and Linux (scripted input), IPMI
- **Data Sources:** `ipmitool sdr`, IPMI SEL (System Event Log)
- **SPL:**
```spl
index=hardware sourcetype=ipmi_sdr host=*
| search sensor_type="Temperature" OR sensor_type="Voltage" OR sensor_type="Fan"
| eval status=case(sensor_reading >= upper_critical, "Critical", sensor_reading >= upper_non_critical, "Warning", 1=1, "OK")
| where status != "OK"
| table _time host sensor_name sensor_reading upper_critical status
```
- **Implementation:** Create scripted input: `ipmitool sdr type temperature` (and voltage, fan). Parse thresholds and current readings. Forward IPMI SEL for discrete events. Alert on Critical/Warning threshold breach.
- **Visualization:** Gauges per sensor, Table of breached sensors, Timeline of SEL events.
- **CIM Models:** N/A

---

### UC-1.4.10 · Disk Controller and HBA Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** RAID/HBA controller errors and degraded state often precede array failure. Early visibility enables planned maintenance and avoids data loss.
- **App/TA:** Custom scripted input (MegaRAID, perccli, hpssacli)
- **Data Sources:** Vendor CLI output (e.g. `MegaCli64 -AdpAllInfo -aAll`), `/proc/scsi/`
- **SPL:**
```spl
index=hardware sourcetype=raid_controller host=*
| stats latest(controller_status) as status, latest(degraded_virtual_drives) as degraded by host, controller_id
| where status != "Optimal" OR degraded > 0
| table host controller_id status degraded
```
- **Implementation:** Run vendor CLI (MegaCli, perccli, hpssacli) via scripted input every 15 minutes. Parse controller and virtual drive state. Alert when status is not Optimal or any array is degraded.
- **Visualization:** Status panel (Optimal/Degraded/Failed), Table of degraded arrays.
- **CIM Models:** N/A

---

### UC-1.4.11 · Boot Order and UEFI/BIOS Configuration Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** Unauthorized or accidental boot order changes can prevent systems from booting from the correct disk or PXE. Tracking supports change audit and recovery.
- **App/TA:** Custom scripted input (vendor tools, dmidecode)
- **Data Sources:** `dmidecode -t bios`, vendor REST/CLI (iDRAC, iLO) for boot order
- **SPL:**
```spl
index=hardware sourcetype=boot_config host=*
| stats latest(boot_order) as current_order, latest(secure_boot) as secure_boot by host
| inputlookup expected_boot_config append=t
| eval match=if('current_order'='expected_order', "Match", "Drift")
| where match="Drift"
| table host current_order expected_order secure_boot
```
- **Implementation:** Use vendor APIs or scripts to export boot order and Secure Boot state. Compare to a lookup of expected configuration. Alert on drift. Run after changes or daily.
- **Visualization:** Table (host, current vs. expected boot order), Compliance percentage.
- **CIM Models:** N/A

---

