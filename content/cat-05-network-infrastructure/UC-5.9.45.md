<!-- AUTO-GENERATED from UC-5.9.45.json — DO NOT EDIT -->

---
id: "5.9.45"
title: "FTP Server Availability and Throughput"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.45 · FTP Server Availability and Throughput

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We test our file transfer servers to make sure they're working and fast enough, because many important business processes depend on files being sent and received on time.*

---

## Description

Monitors FTP/SFTP/FTPS server availability, response time, and file transfer throughput. Supports GET, PUT, and LS operations. Critical for organizations that depend on file transfer for B2B integrations, batch data processing, or content publishing.

## Value

FTP-based workflows are often invisible to modern monitoring stacks focused on HTTP/REST APIs. Yet many organizations depend on FTP for critical business processes: EDI transactions with partners, batch file processing, content staging, and backup transfers. When an FTP server goes down or slows down, the impact may not be visible for hours until a batch job fails or a partner complains about missing files. Proactive FTP monitoring detects these issues before downstream processes are affected.

## Implementation

FTP Server tests are configured in ThousandEyes to target FTP endpoints with specific operations (upload, download, directory listing).

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **FTP Server tests configured in ThousandEyes.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Network → FTP Server**. Each test specifies:
  - **Target server:** The FTP server hostname or IP.
  - **Port:** Default 21 for FTP, 22 for SFTP, 990 for FTPS (implicit).
  - **Protocol:** FTP, SFTP, or FTPS. Most production environments use SFTP or FTPS — plain FTP transmits credentials in cleartext.
  - **Credentials:** Username and password for authentication. ThousandEyes stores these encrypted. Use a dedicated read-only test account, NOT a production account with write permissions.
  - **Operation:** GET (download a specific file), PUT (upload a test file), or LS (list directory). Each operation tests different aspects:
    - GET: measures download throughput and file accessibility.
    - PUT: measures upload throughput and write permissions.
    - LS: measures directory listing speed (fastest test, lowest overhead).
  - **File path:** For GET, specify a test file on the server (e.g., `/test/healthcheck.dat`). Use a file of known size (1 MB recommended) for consistent throughput measurement.
  - **Agents:** Enterprise Agents in networks that normally access the FTP server.
  - **Interval:** 5 minutes for production FTP servers.
- **FTP server test file prepared.** Create a dedicated test file on the FTP server (e.g., `/test/healthcheck.dat`, 1 MB). A file of known, consistent size enables accurate throughput measurement. For PUT tests, create a writable test directory.
- **Firewall rules.** FTP uses port 21 (control) + ephemeral ports (data) for active FTP, or port 21 + high ports for passive FTP. SFTP uses port 22 only. Ensure the agent can reach the server on the required ports. Passive FTP is common behind firewalls.
- **FTP server types in scope.** Common FTP use cases requiring monitoring:
  - Partner file exchange (B2B EDI, supply chain data).
  - Batch processing input (nightly data feeds, report generation).
  - Backup and archive (offsite backup destinations).
  - Legacy application integration (mainframe/AS400 file transfers).
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
FTP Server test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify FTP test data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="ftp-server" earliest=-1h
| stats count avg(ftp.server.request.availability) as avg_avail by thousandeyes.test.name, server.address
| eval avg_avail_pct=round(avg_avail,2)
| sort thousandeyes.test.name
```
Each FTP test should show data. If `avg_avail=0`, the test is consistently failing.

**FTP-specific metrics in the OTel v2 data model:**
- `ftp.server.request.availability` — percentage (0–100). Whether the FTP operation completed successfully. 100% means every test round succeeded.
- `ftp.client.request.duration` — total time for the FTP operation in SECONDS. Includes: DNS resolution + TCP connect + authentication + data transfer. For a GET operation, this is the time to download the file. For LS, it's the time to list the directory.
- `ftp.server.throughput` — data transfer rate in BYTES/SECOND. Only meaningful for GET and PUT operations. Convert to Mbps: `throughput * 8 / 1000000`. For LS operations, throughput is near-zero (just directory listing text).
- `ftp.response.status_code` — FTP reply code (e.g., 226 = Transfer complete, 530 = Login failed, 550 = File not found).
- `ftp.request.command` — the FTP command used: GET, PUT, or LIST.
- `error.type` — error category if the test failed (e.g., authentication_failure, connection_refused, timeout).

### Step 2 — Create the search and alert
**FTP server health overview:**
```spl
`stream_index` thousandeyes.test.type="ftp-server"
| stats avg(ftp.server.request.availability) as avg_avail avg(ftp.client.request.duration) as avg_duration avg(ftp.server.throughput) as avg_throughput by thousandeyes.test.name, server.address
| eval avg_avail_pct=round(avg_avail,2), avg_duration_s=round(avg_duration,2), avg_throughput_mbps=round(avg_throughput*8/1000000,2)
| sort avg_avail_pct, -avg_duration_s
```

**Understanding this SPL**

`avg(ftp.server.request.availability)` — averaged over the search window. For FTP servers, 100% is the target. Any drop indicates test failures (authentication, connectivity, or file access issues).

`avg(ftp.client.request.duration)` — average time for the complete FTP operation. For a 1 MB file download over a 100 Mbps link, expect ~0.1 seconds. For a slow WAN link (10 Mbps), expect ~1 second.

`avg(ftp.server.throughput)` — bytes per second. Multiply by 8 and divide by 1,000,000 for Mbps. Low throughput with a known file size indicates network congestion, server I/O bottleneck, or connection limits.

**FTP failure analysis (what's going wrong):**
```spl
`stream_index` thousandeyes.test.type="ftp-server" ftp.server.request.availability<100 earliest=-24h
| stats count by thousandeyes.test.name, server.address, error.type, ftp.response.status_code
| sort -count
```
Common FTP failure codes:
- 530 = Login incorrect (wrong credentials or account locked).
- 550 = File not found or permission denied.
- 421 = Service not available (server overloaded or shutting down).
- 425 = Can't open data connection (passive mode firewall issue).
- Timeout = Server unreachable or too slow to respond.

**FTP throughput trending (detect performance degradation):**
```spl
`stream_index` thousandeyes.test.type="ftp-server" earliest=-7d
| timechart span=4h avg(ftp.server.throughput) as avg_throughput_bps avg(ftp.client.request.duration) as avg_duration_s by thousandeyes.test.name
```
Look for declining throughput trends which may indicate disk degradation, network congestion, or increasing server load.

**Per-agent FTP performance comparison:**
```spl
`stream_index` thousandeyes.test.type="ftp-server" thousandeyes.test.name="<specific-test>" earliest=-24h
| stats avg(ftp.client.request.duration) as avg_duration avg(ftp.server.throughput) as avg_throughput avg(ftp.server.request.availability) as avg_avail by thousandeyes.source.agent.name
| eval avg_duration_s=round(avg_duration,2), avg_mbps=round(avg_throughput*8/1000000,2), avg_avail_pct=round(avg_avail,2)
| sort -avg_duration_s
```
If one agent shows significantly slower throughput, the issue is in that agent's network path, not the FTP server.

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`. Alert on `ftp.server.request.availability < 100`. Throttle by `thousandeyes.test.name` for 1 hour.

### Step 3 — Validate
(a) **Manual FTP connection.** Connect to the FTP server using a command-line client and perform the same operation:
```
# SFTP example
sftp user@ftp.example.com
sftp> get /test/healthcheck.dat
sftp> ls -la /data/
```
Compare transfer time and file size with ThousandEyes-reported duration and throughput.

(b) **Throughput calculation.** If the test file is 1 MB (1,048,576 bytes) and `ftp.client.request.duration` is 0.5 seconds, expected throughput = 1,048,576 / 0.5 = 2,097,152 bytes/sec ≈ 16.8 Mbps. Verify this matches `ftp.server.throughput`.

(c) **Credential verification.** If availability is 0% and `ftp.response.status_code` is 530, the test credentials are wrong. Verify the account is active and has permissions for the test operation.

(d) **Passive mode vs active mode.** If the agent is behind a firewall, FTP requires passive mode (PASV). Active mode requires the server to initiate a data connection back to the agent, which firewalls block. ThousandEyes uses passive mode by default.

(e) **Test file exists.** For GET tests, verify the test file exists at the specified path. A missing file causes 550 errors with 0% availability.

### Step 4 — Operationalize
**Dashboard** ("FTP Server Monitoring" — designed for infrastructure / integration teams):
- Row 1 — FTP server scoreboard: one tile per FTP test showing availability % and duration. Green = available and fast, yellow = available but slow, red = failures.
- Row 2 — Failure analysis: table showing recent failures with error types and FTP status codes. Drilldown to specific test details.
- Row 3 — Throughput trending: 7-day timechart showing transfer throughput per FTP test. Declining trends indicate capacity or performance issues.
- Row 4 — Per-agent comparison: for each FTP test, show duration per agent. Identifies network path issues.

**Alerting (tiered):**
- `ftp.server.request.availability < 100` → low-urgency notification to `#infra-ops`. Include test name, server, error type.
- `ftp.server.request.availability = 0` for > 15 min → high-urgency notification. FTP server is down. Page on-call.
- Throughput < 50% of baseline → medium-urgency notification. Transfer performance degraded.

**Runbook** (owner: infrastructure / integration team):
1. **FTP server unavailable (availability = 0%).** (a) Check FTP server process (`systemctl status vsftpd` or equivalent). (b) Check disk space — full disks prevent writes and may crash the FTP daemon. (c) Check network connectivity — firewall changes may have blocked the agent. (d) Check `error.type`: authentication_failure → credentials expired; connection_refused → server process down; timeout → network issue.
2. **Low throughput.** (a) Check server disk I/O — `iostat` or `iotop` on the FTP server. A disk at 100% utilization throttles transfers. (b) Check network bandwidth — other traffic may be saturating the link. (c) Check file size — if the test file is very small (< 10 KB), throughput measurement is unreliable due to protocol overhead.
3. **Authentication failures (530).** (a) Verify test credentials are current — password may have expired or account may be locked. (b) Check FTP server's auth logs. (c) If using SFTP with key-based auth, the key may have been rotated.
4. **Intermittent failures.** (a) Check if the FTP server has connection limits (max concurrent connections) — the test may be getting rejected during peak usage. (b) Check if a load balancer in front of the FTP server is unhealthy. (c) Check passive mode port range — if the port range is too narrow, connections may fail under load.

### Step 5 — Troubleshooting

- **No FTP test data** — Verify FTP tests are configured in ThousandEyes and the target server is reachable from the agent's network. Check the agent's status in ThousandEyes UI.

- **Throughput shows 0 or near-zero** — The test may be using LS (directory listing), which transfers minimal data. Throughput is meaningful only for GET/PUT operations with actual file content. Switch to a GET test with a 1 MB test file.

- **Duration seems unreasonably long** — If `ftp.client.request.duration` is > 30 seconds for a small file, the server may be slow to respond to the auth handshake, or DNS resolution is slow. Check if the FTP server does reverse DNS lookups on connecting clients (common cause of slow FTP logins).

- **SFTP vs FTPS confusion** — SFTP (SSH File Transfer Protocol, port 22) is NOT the same as FTPS (FTP over TLS, port 990 or 21). Ensure the test uses the correct protocol and port for your server.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for general app troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.type="ftp-server"
| stats avg(ftp.server.request.availability) as avg_avail avg(ftp.client.request.duration) as avg_duration avg(ftp.server.throughput) as avg_throughput by thousandeyes.test.name, server.address, ftp.request.command
| eval avg_duration_ms=round(avg_duration*1000,1), avg_throughput_mbps=round(avg_throughput*8/1000000,2)
| sort avg_avail, -avg_duration_ms
```

## Visualization

(1) Scoreboard: FTP server availability. (2) Table: FTP servers with response time and throughput. (3) Timechart: throughput trending. (4) Bar chart: throughput by server.

## Known False Positives

**FTP session limits.** FTP servers often limit concurrent connections. If multiple test agents connect simultaneously and exceed the limit, some connections fail — a test artifact, not a server problem. Stagger test schedules across agents.

**Credential rotation.** FTP tests using username/password authentication fail when credentials are rotated. Update test credentials after rotation.

**Firewall/NAT issues.** Active-mode FTP requires the server to initiate data connections back to the client, which is often blocked by firewalls. Use passive mode (PASV) in test configuration.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — FTP metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
