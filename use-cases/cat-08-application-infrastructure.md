## 8. Application Infrastructure

### 8.1 Web Servers & Reverse Proxies

**Primary App/TA:** Splunk Add-on for Apache Web Server (`Splunk_TA_apache`), Splunk Add-on for NGINX (`TA-nginx`), Windows TA for IIS logs, Traefik syslog.

---

### UC-8.1.1 · HTTP Error Rate Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=400
  by Web.src Web.uri_path Web.status span=5m
| sort -count
```
- **References:** [Splunk Add-on for Apache](https://splunkbase.splunk.com/app/830), [Splunk Add-on for NGINX](https://splunkbase.splunk.com/app/3178), [Web CIM](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- **Known false positives:** Client errors (4xx) from bots or invalid requests; consider separate thresholds for 4xx vs 5xx.

---

### UC-8.1.2 · Response Time Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count as request_count
  from datamodel=Web.Web
  by Web.uri_path Web.status span=5m
| sort -request_count
```

---

### UC-8.1.3 · Request Rate Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

---

### UC-8.1.4 · Top Error URIs
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=400
  by Web.src Web.uri_path Web.status span=5m
| sort -count
```

---

### UC-8.1.5 · SSL Certificate Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

---

### UC-8.1.6 · Upstream Backend Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

---

### UC-8.1.7 · Bot and Crawler Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

---

### UC-8.1.8 · Connection Pool Saturation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

---

### UC-8.1.9 · Slow POST Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Web.bytes) as avg_bytes count
  from datamodel=Web.Web
  by Web.uri_path Web.status span=5m
| sort -avg_bytes
```

---

### UC-8.1.10 · Configuration Reload Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

---

### UC-8.1.11 · NGINX Upstream Response Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Counts upstream HTTP 5xx and connect/timeout errors from NGINX access/error logs. Isolates reverse-proxy vs origin issues faster than aggregate 5xx alone.
- **App/TA:** `TA-nginx`
- **Data Sources:** `access_combined` with `upstream_status`, `nginx:error` upstream messages
- **SPL:**
```spl
index=web sourcetype="nginx:access" OR sourcetype="access_combined"
| eval up_err=if(upstream_status>=500 OR status=502 OR status=504,1,0)
| stats sum(up_err) as upstream_errors, count as total by host, upstream_addr
| eval err_rate=round(upstream_errors/total*100,2)
| where err_rate > 2
```
- **Implementation:** Enable `upstream_status` and `upstream_addr` in log_format. Alert on upstream error rate >2% for 5m. Correlate with backend pool health.
- **Visualization:** Line chart (upstream error rate), Table (upstream_addr, errors), Bar chart (5xx by upstream).
- **CIM Models:** Web

---

### UC-8.1.12 · Apache mod_security WAF Blocks
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Tracks ModSecurity rule IDs and scores for blocked requests. Supports tuning false positives and detecting attack campaigns.
- **App/TA:** `Splunk_TA_apache`, modsec audit log
- **Data Sources:** `modsec_audit.log`, `SecRule` action deny entries
- **SPL:**
```spl
index=web sourcetype="apache:modsec"
| search action="denied" OR intercept_phase="phase:2"
| stats count by rule_id, uri_path, src_ip
| sort -count
| head 30
```
- **Implementation:** Ingest JSON or native ModSecurity audit format. Extract `rule_id`, `msg`. Alert on spike in unique IPs or new rule_id firing at high volume.
- **Visualization:** Table (rule, URI, count), Bar chart (blocks by rule), Map (src_ip).
- **CIM Models:** Web

---

### UC-8.1.13 · IIS Worker Process Recycling
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Frequent `w3wp` recycles cause session loss and latency spikes. Event Log IDs 5074, 5002, 1011 indicate config, memory, or crash-driven recycles.
- **App/TA:** `Splunk_TA_windows`
- **Data Sources:** System/Application Event Log (WAS, W3SVC)
- **SPL:**
```spl
index=wineventlog sourcetype="WinEventLog:System" SourceName=WAS EventCode=5074
| bucket _time span=5m
| stats count as recycles by ComputerName, AppPoolName, _time
| where recycles > 3
```
- **Implementation:** Enable WAS/W3SVC auditing. Alert when recycles per app pool exceed baseline. Correlate with private bytes and GC from perfmon.
- **Visualization:** Timeline (recycle events), Table (app pool, recycle count), Line chart (recycles per hour).
- **CIM Models:** Web

---

### UC-8.1.14 · SSL Certificate Expiry Countdown
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Days-to-expiry dashboard for all TLS endpoints monitored by cert checks. Complements UC-8.1.5 with trend and earliest-expiry focus.
- **App/TA:** Scripted cert check, `openssl` input
- **Data Sources:** `cert_check` with `cert_expiry_epoch`, `cn`
- **SPL:**
```spl
index=certificates sourcetype="cert_check"
| eval days_left=round((cert_expiry_epoch-now())/86400,0)
| stats min(days_left) as soonest by host, port
| where soonest < 45
| sort soonest
```
- **Implementation:** Daily collection. Alert tiers at 45/30/14/7 days. Include chain validation failures as severity 1.
- **Visualization:** Table (host, port, days_left), Single value (minimum days_left fleet-wide), Column chart (certs by expiry bucket).
- **CIM Models:** Web

---

### UC-8.1.15 · HAProxy Backend Health State
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** CSV stats `status` (UP/DOWN/MAINT) per server line with weight. Distinct from UC-8.1.6 NGINX-only upstream errors for HAProxy-native shops.
- **App/TA:** HAProxy stats socket scripted input
- **Data Sources:** `haproxy:stats` `svname`, `status`, `chkfail`
- **SPL:**
```spl
index=haproxy sourcetype="haproxy:stats" type=server
| where status!="UP" OR chkfail > 0
| stats latest(status) as status, sum(chkfail) as fails by pxname, svname
| sort fails
```
- **Implementation:** Poll stats every 30s. Alert on any backend DOWN not in maintenance window. Track flapping (status changes >3 in 10m).
- **Visualization:** Status grid (backend × UP/DOWN), Table (DOWN servers), Timeline (state changes).
- **CIM Models:** Web

---

### UC-8.1.16 · Web Server Thread Pool Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** IIS `QueueFull`, NGINX worker saturation, or Apache `BusyWorkers` at limit causes queueing. Unified thresholding across stacks.
- **App/TA:** `TA-nginx` stub_status, `Splunk_TA_windows` perfmon, Apache mod_status
- **Data Sources:** `nginx:stub_status`, `Perfmon:W3SVC_W3WP`, `apache:server_status`
- **SPL:**
```spl
index=web (sourcetype="nginx:stub_status" OR sourcetype="apache:server_status" OR sourcetype="Perfmon:W3SVC_W3WP")
| eval util_pct=coalesce(worker_util_pct, pct_busy, thread_pool_queue_length/max_threads*100)
| where util_pct > 85 OR queue_current > 50
| timechart span=5m max(util_pct) as util by host, sourcetype
```
- **Implementation:** Normalize field names at ingest. Alert when util >85% for 10m or IIS request queue length sustained high. Correlate with CPU and backend latency.
- **Visualization:** Gauge (util %), Line chart (util and queue), Table (hosts over threshold).
- **CIM Models:** Web

---

### 8.2 Application Servers & Runtimes

**Primary App/TA:** Splunk Add-on for JMX (`TA-jmx`), OpenTelemetry Collector (`Splunk_TA_otel`), custom log inputs for application frameworks.

---

### UC-8.2.1 · JVM Heap Utilization
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.2.2 · Garbage Collection Impact
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.2.3 · Thread Pool Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-8.2.4 · Application Error Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.2.5 · Deployment Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
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
- **CIM Models:** N/A

---

### UC-8.2.6 · Connection Pool Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-8.2.7 · Session Count Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-8.2.8 · .NET CLR Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.2.9 · Node.js Event Loop Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.2.10 · Class Loading Issues
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-8.2.11 · PHP-FPM Pool Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Value:** Active/idle process counts, listen queue depth, and slow request detection indicate PHP-FPM capacity and backend saturation. Exhausted pools cause 502 errors and request timeouts.
- **App/TA:** Custom scripted input (PHP-FPM status page)
- **Data Sources:** PHP-FPM status page (JSON output, `/status?json`)
- **SPL:**
```spl
index=php sourcetype="phpfpm:status"
| eval pool_util=round(active_processes/(active_processes+idle_processes)*100,1)
| where pool_util > 80 OR listen_queue > 5
| timechart span=5m max(pool_util) as util_pct, max(listen_queue) as queue_depth by host, pool
```
- **Implementation:** Enable PHP-FPM status via `pm.status_path = /status` and `pm.status_listen` in pool config. Add `fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name`; protect with auth. Poll `/status?json` via scripted input every minute. Parse active_processes, idle_processes, listen_queue, max_listen_queue, slow_requests. Forward to Splunk via HEC. Alert when pool_util >80% or listen_queue >5. Track slow_requests for endpoints needing optimization.
- **Visualization:** Gauge (% pool used), Line chart (pool utilization and queue depth), Table (pools with high utilization), Single value (slow requests).
- **CIM Models:** N/A

---

### UC-8.2.12 · Tomcat JMX Thread Pool Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Connector thread pool busy percentage and rejected connections indicate Tomcat capacity limits. Exhausted pools cause 503 errors and connection timeouts.
- **App/TA:** Custom JMX input (Jolokia, JMX modular input)
- **Data Sources:** JMX MBeans (`Catalina:type=ThreadPool,name="http-nio-8080"`)
- **SPL:**
```spl
index=jmx sourcetype="jmx:tomcat:threadpool"
| eval pool_pct=round(currentThreadsBusy/maxThreads*100,1)
| where pool_pct > 80 OR connectionCount > 0
| timechart span=5m max(pool_pct) as busy_pct, sum(connectionCount) as rejected by host, connector_name
```
- **Implementation:** Deploy Jolokia agent or Splunk JMX modular input on Tomcat. Configure polling for `Catalina:type=ThreadPool,name="http-nio-8080"` (adjust connector name per instance). Extract currentThreadsBusy, maxThreads, connectionCount (rejected). Poll every 5 minutes. Alert when pool_pct >80% or any rejected connections. Correlate with request rate and response time to distinguish traffic spikes from slow backends.
- **Visualization:** Gauge (% threads busy), Line chart (thread utilization over time), Table (connectors with rejections), Single value (rejected connections).
- **CIM Models:** N/A

---

### UC-8.2.13 · WildFly / JBoss Datasource Pool Usage
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Availability
- **Value:** JMX datasource pool active/idle/wait connections indicate database connectivity health. Exhausted pools cause application errors and slow transactions.
- **App/TA:** Custom JMX input (Jolokia)
- **Data Sources:** JMX MBeans (`jboss.as:subsystem=datasources,data-source=*`)
- **SPL:**
```spl
index=jmx sourcetype="jmx:wildfly:datasource"
| eval pool_pct=round(AvailableCount/(AvailableCount+InUseCount)*100,1), wait_pct=round(WaitingCount/(AvailableCount+InUseCount+WaitingCount)*100,1)
| where pool_pct < 20 OR WaitingCount > 0
| timechart span=5m max(pool_pct) as avail_pct, avg(WaitingCount) as waiting by host, data_source
```
- **Implementation:** Deploy Jolokia on WildFly/JBoss. Poll `jboss.as:subsystem=datasources,data-source=*` for AvailableCount, InUseCount, WaitingCount, MaxUsedCount. Poll every 5 minutes. Alert when pool availability drops below 20% or WaitingCount >0 (indicating connection starvation). Track MaxUsedCount for capacity planning.
- **Visualization:** Gauge (% pool available), Line chart (active vs idle over time), Table (datasources with waiting connections), Single value (total waiting).
- **CIM Models:** N/A

---

### UC-8.2.14 · JVM Garbage Collection Pause Time (STW)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Stop-the-world pause duration percentiles from unified GC logs (G1, ZGC) drive SLA breaches before heap % alerts fire.
- **App/TA:** GC log parsing, `jvm:gc` sourcetype
- **Data Sources:** `-Xlog:gc*` (Java 11+), `gc_pause_ms`, `gc_type`
- **SPL:**
```spl
index=jvm sourcetype="jvm:gc"
| where gc_pause_ms > 500
| timechart span=5m perc95(gc_pause_ms) as p95_pause, max(gc_pause_ms) as max_pause by host
| where p95_pause > 200
```
- **Implementation:** Parse pause events only (not concurrent phases). Alert on p95 >200ms or any pause >2s. Split by pool (G1 Old Gen vs Young).
- **Visualization:** Line chart (p95/max pause), Histogram (pause distribution), Table (worst hosts).
- **CIM Models:** N/A

---

### UC-8.2.15 · .NET CLR Memory Pressure
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** `# Bytes in all Heaps`, `LOH` size, and `% Time in GC` together indicate memory pressure vs high allocation rate. Refines UC-8.2.8.
- **App/TA:** `Splunk_TA_windows` Perfmon
- **Data Sources:** `.NET CLR Memory`, `.NET Memory Cache`
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:CLR_Memory"
| timechart span=5m avg(Gen_2_heap_size) as gen2_bytes, avg(Pct_Time_in_GC) as gc_pct by instance
| where gc_pct > 15
```
- **Implementation:** Collect every 1m for critical apps. Alert when GC time >15% and Gen 2 heap grows week-over-week. Trigger dump analysis workflow.
- **Visualization:** Dual-axis (heap vs GC %), Line chart (Gen 2 size), Table (instances over threshold).
- **CIM Models:** N/A

---

### UC-8.2.16 · Node.js Event Loop Lag (High Resolution)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** `eventLoopUtilization` and `delay` histogram from `perf_hooks` or Prometheus `nodejs_eventloop_lag_seconds` for sub-millisecond vs millisecond precision.
- **App/TA:** OpenTelemetry, `prom-client`
- **Data Sources:** `nodejs:metrics` `event_loop_lag_p99_ms`
- **SPL:**
```spl
index=application sourcetype="nodejs:metrics"
| timechart span=1m perc99(event_loop_lag_ms) as p99_lag by host
| where p99_lag > 50
```
- **Implementation:** Export p50/p99 lag. Alert on p99 >50ms for 5m. Correlate with blocking `fs` or `dns` calls from traces.
- **Visualization:** Line chart (p99 event loop lag), Table (hosts breaching SLO), Single value (current p99).
- **CIM Models:** N/A

---

### UC-8.2.17 · Python WSGI Worker Pool Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Gunicorn/uWSGI `active workers`, `listening queue`, and `timeout` worker kills indicate saturation or slow upstream (DB).
- **App/TA:** Structured app logs, stats endpoint
- **Data Sources:** `gunicorn:json` `workers`, `req`, `timeout`
- **SPL:**
```spl
index=application sourcetype="gunicorn:json"
| where worker_timeout > 0 OR active_workers >= max_workers OR backlog > 10
| stats sum(worker_timeout) as timeouts, max(backlog) as max_backlog by host, app_name
| where timeouts > 0 OR max_backlog > 10
```
- **Implementation:** Enable `--statsd` or JSON access/error with worker fields. Alert on backlog growth or worker timeouts. Scale workers or fix slow queries.
- **Visualization:** Line chart (backlog and active workers), Table (apps with timeouts), Single value (total worker timeouts 1h).
- **CIM Models:** N/A

---

### UC-8.2.18 · Tomcat Active Session Count
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Session explosion may indicate bot traffic, session fixation abuse, or missing session TTL. Per-context session counts from JMX.
- **App/TA:** `TA-jmx`
- **Data Sources:** `Catalina:type=Manager` `activeSessions`, `sessionMaxAliveTime`
- **SPL:**
```spl
index=jmx sourcetype="jmx:tomcat:manager"
| timechart span=15m max(activeSessions) as sessions by host, context_path
| eventstats avg(sessions) as baseline by context_path
| where sessions > baseline * 3 AND sessions > 5000
```
- **Implementation:** Baseline sessions per context. Alert on 3× baseline or absolute cap. Correlate with marketing events or attacks.
- **Visualization:** Line chart (sessions over time), Table (context, sessions), Single value (peak sessions).
- **CIM Models:** N/A

---

### UC-8.2.19 · WebLogic Stuck Threads
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Stuck thread count >0 blocks request processing and triggers health check failures. Server log `BEA-000337` patterns.
- **App/TA:** WebLogic Server logs, JMX
- **Data Sources:** `weblogic:server` log, `StuckThreadCount` MBean
- **SPL:**
```spl
index=application sourcetype="weblogic:server"
| search "BEA-000337" OR "STUCK" OR stuck_thread_count>0
| stats count by domain, server_name, thread_name
| where count > 0
```
- **Implementation:** Forward stdout/stderr and domain logs. Alert on first stuck thread. Thread dump automation on critical domains.
- **Visualization:** Table (domain, server, stuck count), Timeline (stuck events), Single value (stuck threads now).
- **CIM Models:** N/A

---

### UC-8.2.20 · JBoss / WildFly Deployment Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Failed deployments leave apps stopped or partial. Log markers `WFLYSRV0026`, `Deployment FAILED` require immediate attention.
- **App/TA:** JBoss server.log ingestion
- **Data Sources:** `jboss:server.log`, `server.log` deployment phase
- **SPL:**
```spl
index=application sourcetype="jboss:server"
| search "Deployment FAILED" OR "WFLYSRV0059" OR "Services with missing/unavailable dependencies"
| table _time, host, deployment, message
| sort -_time
```
- **Implementation:** Parse deployment name from log line. Alert on any FAILURE during CI/CD window or outside window (rogue deploy). Correlate with Git commit from pipeline ID if present.
- **Visualization:** Timeline (deployment outcomes), Table (failed deployment, error), Single value (failures 24h).
- **CIM Models:** N/A

---

### UC-8.2.21 · Spring Boot Actuator Health Down
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** `/actuator/health` JSON with `status:DOWN` from liveness/readiness probes. Aggregates component failures (diskSpace, db, redis).
- **App/TA:** HEC from K8s probe sidecar, access log
- **Data Sources:** `spring:actuator` JSON lines, probe stderr
- **SPL:**
```spl
index=application sourcetype="spring:actuator" OR path="/actuator/health"
| spath output=status status
| spath output=components components
| where status!="UP"
| table _time, host, app_name, status, components
```
- **Implementation:** Ship health check responses (avoid PII). Alert on non-UP. Break down `components.*.status` for root cause.
- **Visualization:** Status grid (app × component), Table (DOWN components), Timeline (health flaps).
- **CIM Models:** N/A

---

### UC-8.2.22 · .NET Exception Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** `# of Exceps Thrown / sec` and first-chance exception logs show error storms after deploys. Complements log-based UC-8.2.4 with runtime counters.
- **App/TA:** `Splunk_TA_windows` Perfmon, Serilog/NLog
- **Data Sources:** `.NET CLR Exceptions` `# of Exceps Thrown / sec`
- **SPL:**
```spl
index=perfmon sourcetype="Perfmon:CLR_Exceptions"
| timechart span=5m sum(Exceps_Thrown_per_sec) as ex_rate by process_name
| eventstats avg(ex_rate) as baseline by process_name
| where ex_rate > baseline * 5 AND ex_rate > 1
```
- **Implementation:** Baseline per process. Alert on 5× baseline. Join with deployment markers from UC-8.2.5.
- **Visualization:** Line chart (exception rate), Table (process, spike factor), Single value (total exceptions/sec).
- **CIM Models:** N/A

---

### 8.3 Message Queues & Event Streaming

**Primary App/TA:** Splunk Connect for Kafka (Splunkbase 3862), JMX, RabbitMQ management API (scripted input), custom REST inputs.

---

### UC-8.3.1 · Consumer Lag Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Growing consumer lag means messages aren't being processed fast enough, leading to data staleness and eventual message loss if retention is exceeded.
- **App/TA:** `Splunk Connect for Kafka` (Splunkbase 3862), Burrow integration, JMX
- **Data Sources:** Kafka consumer group offsets (JMX, Burrow, `kafka-consumer-groups.sh`)
- **SPL:**
```spl
index=kafka sourcetype="kafka:consumer_lag"
| timechart span=5m max(lag) as consumer_lag by consumer_group, topic
| where consumer_lag > 10000
```
- **Implementation:** Deploy Kafka consumer lag monitoring via Burrow or JMX. Poll lag per consumer group/topic/partition every minute. Alert when lag exceeds threshold (e.g., >10K messages or >5 minutes equivalent). Track lag trend for capacity planning.
- **Visualization:** Line chart (lag per consumer group), Heatmap (topic × partition lag), Single value (max lag), Table (lagging consumers).
- **CIM Models:** N/A

---

### UC-8.3.2 · Queue Depth Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-8.3.3 · Broker Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-8.3.4 · Under-Replicated Partitions
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Under-replicated partitions mean data is at risk of loss if additional brokers fail. Immediate remediation is required.
- **App/TA:** `Splunk Connect for Kafka` (Splunkbase 3862), JMX
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
- **CIM Models:** N/A

---

### UC-8.3.5 · Dead Letter Queue Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-8.3.6 · Message Throughput Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.3.7 · Topic/Queue Creation Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
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
- **CIM Models:** N/A

---

### UC-8.3.8 · Consumer Group Rebalancing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.3.9 · Partition Leader Elections
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-8.3.10 · Message Age Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.3.11 · RabbitMQ Queue Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Queue depth, consumer count, message rate, and unacknowledged messages indicate message processing health. Growing depth or unacked messages signal consumer lag or failures.
- **App/TA:** Custom (RabbitMQ Management API)
- **Data Sources:** RabbitMQ Management API (`/api/queues`)
- **SPL:**
```spl
index=messaging sourcetype="rabbitmq:queue"
| eval unacked_pct=if(messages>0, round(messages_unacknowledged/messages*100,1), 0)
| where messages > 1000 OR messages_unacknowledged > 100 OR consumer_count==0
| timechart span=5m max(messages) as queue_depth, avg(messages_unacknowledged) as unacked by vhost, name
```
- **Implementation:** Enable RabbitMQ Management Plugin. Poll `/api/queues` via scripted input (curl with auth) every minute. Parse name, vhost, messages, messages_unacknowledged, messages_ready, consumers, message_stats.publish_details.rate, message_stats.deliver_get_details.rate. Forward to Splunk via HEC. Alert when queue depth exceeds threshold, unacked messages grow, or consumer_count drops to 0 for critical queues. Track publish vs deliver rate delta for backlog detection.
- **Visualization:** Line chart (queue depth and unacked over time), Table (queues with high depth), Single value (queues with no consumers), Bar chart (message rate by queue).
- **CIM Models:** N/A

---

### UC-8.3.12 · ZooKeeper Ensemble Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Leader election state, outstanding requests, and watch count indicate ZooKeeper stability. Frequent leader changes or growing outstanding requests signal ensemble instability affecting Kafka, HBase, and other dependents.
- **App/TA:** Custom scripted input (ZooKeeper 4-letter commands or AdminServer)
- **Data Sources:** mntr command output, ZooKeeper AdminServer `/commands/monitor`
- **SPL:**
```spl
index=zookeeper sourcetype="zookeeper:mntr"
| where outstanding_requests > 100 OR (mode!="standalone" AND num_alive_connections < 2)
| timechart span=5m max(outstanding_requests) as outstanding by host
```
- **Implementation:** Enable ZooKeeper AdminServer or use 4-letter commands (`echo mntr | nc localhost 2181`). Poll mntr output every minute via scripted input. Parse mode (leader/follower/standalone), outstanding_requests, num_alive_connections, watch_count, zk_approximate_data_size. Forward to Splunk via HEC. Alert when outstanding_requests exceeds 100 or num_alive_connections drops (ensemble partition). Track leader changes via mode transitions.
- **Visualization:** Status grid (node × mode), Line chart (outstanding requests over time), Single value (leader node), Table (ensemble health summary).
- **CIM Models:** N/A

---

### UC-8.3.13 · Kafka Consumer Lag Monitoring (Consumer Group)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Lag in messages and approximate time lag per partition for each `group.id`. Tightens UC-8.3.1 with `kafka-consumer-groups` export fields.
- **App/TA:** Burrow, Kafka Connect, `kafka:consumer_lag` scripted input
- **Data Sources:** `LAG`, `CONSUMER-ID`, `TOPIC`, `PARTITION`
- **SPL:**
```spl
index=kafka sourcetype="kafka:consumer_lag"
| eval lag_sec=coalesce(lag_seconds, estimated_lag_sec)
| where lag > 100000 OR lag_sec > 300
| timechart span=5m max(lag) as max_lag by consumer_group, topic
```
- **Implementation:** Poll `kafka-consumer-groups.sh --describe` every minute. Alert on lag > SLA messages or estimated seconds. Exclude bursty batch groups via lookup.
- **Visualization:** Line chart (lag by group/topic), Heatmap (partition lag), Single value (worst consumer group).
- **CIM Models:** N/A

---

### UC-8.3.14 · RabbitMQ Queue Depth Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Per-queue `messages_ready` thresholds with business priority tags. Alert routing by `queue` name pattern (`critical.*`).
- **App/TA:** RabbitMQ management API
- **Data Sources:** `rabbitmq:queue` `messages`, `messages_ready`, `consumers`
- **SPL:**
```spl
index=messaging sourcetype="rabbitmq:queue"
| lookup rabbitmq_queue_sla queue_name OUTPUT max_depth
| where messages_ready > max_depth OR consumers=0 OR consumers IS NULL
| table vhost name messages_ready consumers max_depth
```
- **Implementation:** Maintain SLA lookup per queue. Page on critical queue depth. Auto-scale consumers from orchestrator if integrated.
- **Visualization:** Line chart (depth vs threshold), Table (breached queues), Single value (queues in alert).
- **CIM Models:** N/A

---

### UC-8.3.15 · Azure Service Bus Dead Letter Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** DLQ message count per topic/subscription and dead-letter reasons (`DeliveryCount`, `ExceptionDescription`) for cloud-native messaging.
- **App/TA:** Azure Monitor Diagnostic Settings → Splunk
- **Data Sources:** `DeadletteredMessages` metric, operational logs
- **SPL:**
```spl
index=azure sourcetype="azure:servicebus:metrics"
| where metric_name="DeadletteredMessages" OR EntityName="*DeadLetter*"
| timechart span=5m sum(Total) as dlq_count by EntityName, SubscriptionName
| where dlq_count > 0
```
- **Implementation:** Enable metrics on topics/subscriptions. Alert on any DLQ growth for tier-1 entities. Sample DLQ messages via separate secure pipeline (not full body in Splunk if PII).
- **Visualization:** Line chart (DLQ count), Table (entity, subscription, count), Single value (total DLQ messages).
- **CIM Models:** N/A

---

### UC-8.3.16 · Kafka Connect Task Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Connector `FAILED` state, task failures, and `offset_commit` errors stop data pipelines. Distinct from broker-only monitoring.
- **App/TA:** Connect worker logs, Connect REST `/status`
- **Data Sources:** `kafka_connect:connector_status`, worker log
- **SPL:**
```spl
index=kafka sourcetype="kafka_connect:status"
| where connector_state="FAILED" OR task_state="FAILED"
| stats latest(trace) as err by connector, task_id
| table connector task_id connector_state task_state err
```
- **Implementation:** Poll `/connectors/*/status` every 2m. Alert on any FAILED. Include stack trace first line only for indexing size.
- **Visualization:** Table (failed connectors/tasks), Timeline (state changes), Single value (open failures).
- **CIM Models:** N/A

---

### UC-8.3.17 · Kafka Topic Partition Skew
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Byte size and message count skew across partitions causes hot brokers and uneven consumer lag. Uses `kafka-log-dirs` or broker metrics.
- **App/TA:** JMX, broker metrics export
- **Data Sources:** `Size` per partition, `LogEndOffset` per partition
- **SPL:**
```spl
index=kafka sourcetype="kafka:partition_skew"
| eventstats avg(partition_size_bytes) as avg_sz by topic
| eval skew_pct=round(abs(partition_size_bytes-avg_sz)/avg_sz*100,1)
| where skew_pct > 25
| table topic partition partition_size_bytes skew_pct
```
- **Implementation:** Nightly job from log size per partition. Alert when skew >25%. Recommend partition key review or reassign.
- **Visualization:** Bar chart (skew % by partition), Table (top skewed topics), Heatmap (broker × partition size).
- **CIM Models:** N/A

---

### UC-8.3.18 · RabbitMQ Memory Alarm
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** `mem_alarm` blocks publishers when `vm_memory_high_watermark` is hit. Early warning from `memory` and `allocated` fields.
- **App/TA:** RabbitMQ management API `/api/nodes`
- **Data Sources:** `mem_used`, `mem_limit`, `mem_alarm`
- **SPL:**
```spl
index=messaging sourcetype="rabbitmq:node"
| where mem_alarm==true OR mem_used/mem_limit > 0.75
| table _time, name, mem_used, mem_limit, mem_alarm
```
- **Implementation:** Poll nodes every minute. Alert at 75% memory or alarm true. Flow control from alarm requires immediate consumer scale-up or queue purge policy.
- **Visualization:** Gauge (memory % per node), Line chart (mem_used trend), Table (nodes in alarm).
- **CIM Models:** N/A

---

### UC-8.3.19 · ActiveMQ Broker Store Usage
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Persistent store percent used (KahaDB) or JDBC store growth causes broker pause and producer blocking. JMX `StoreLimit` usage.
- **App/TA:** ActiveMQ JMX, `activemq` log
- **Data Sources:** `org.apache.activemq:type=Broker` `StoreLimit`, `TempLimit`
- **SPL:**
```spl
index=messaging sourcetype="activemq:broker"
| eval store_pct=round(store_used/store_limit*100,1)
| where store_pct > 80
| timechart span=5m max(store_pct) as pct by broker_name
```
- **Implementation:** Poll JMX every 5m. Alert at 80% store. Schedule garbage collection or archive old messages per policy.
- **Visualization:** Gauge (store %), Line chart (store usage), Table (brokers over threshold).
- **CIM Models:** N/A

---

### UC-8.3.20 · NATS JetStream Consumer Ack Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** `NumAckPending`, `NumRedelivered`, and consumer lag for JetStream streams indicate slow consumers or poison messages.
- **App/TA:** NATS Prometheus exporter, `nats` server varz/jsz
- **Data Sources:** `jetstream_consumer_lag`, `ack_pending`
- **SPL:**
```spl
index=messaging sourcetype="nats:jetstream"
| where num_ack_pending > 1000 OR num_redelivered > 100
| stats max(num_ack_pending) as lag by stream_name, consumer_name
| sort -lag
```
- **Implementation:** Scrape `/jsz` or Prometheus metrics. Alert on rising ack_pending. Correlate with consumer pod restarts.
- **Visualization:** Line chart (ack pending), Table (stream, consumer, lag), Single value (max redelivered).
- **CIM Models:** N/A

---

### 8.4 API Gateways & Service Mesh

**Primary App/TA:** Custom access log inputs, Envoy access log parsing, Istio telemetry, Kong/Apigee API inputs.

---

### UC-8.4.1 · API Error Rate by Endpoint
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=400
  by Web.src Web.uri_path Web.status span=5m
| sort -count
```

---

### UC-8.4.2 · API Latency Percentiles
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Web.bytes) as avg_bytes count
  from datamodel=Web.Web
  by Web.uri_path Web.status span=5m
| sort -avg_bytes
```

---

### UC-8.4.3 · Rate Limiting Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.4.4 · Authentication Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
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
- **CIM Models:** N/A

---

### UC-8.4.5 · Service-to-Service Call Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.4.6 · Circuit Breaker Activations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
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
- **CIM Models:** N/A

---

### UC-8.4.7 · API Consumer Usage Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.4.8 · mTLS Certificate Expiration
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-8.4.9 · HAProxy Backend and Frontend Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Backend server state, connection queue depth, and HTTP response distribution indicate load balancer effectiveness and backend capacity. Detection of DOWN backends or saturated queues enables rapid failover and scaling decisions.
- **App/TA:** Custom (HAProxy stats socket/CSV, syslog)
- **Data Sources:** HAProxy stats CSV (`/haproxy?stats;csv`), syslog
- **SPL:**
```spl
index=haproxy sourcetype="haproxy:stats"
| eval backend_status=case(status=="UP",1, status=="DOWN",0, 1=1,null())
| stats latest(backend_status) as up, latest(qcur) as queue_depth, latest(scur) as sessions by pxname, svname, type
| where type=="backend" AND (up==0 OR queue_depth>10)
| table pxname, svname, up, queue_depth, sessions
```
- **Implementation:** Enable HAProxy stats via `stats uri /haproxy?stats` and `stats enable` in the frontend. Poll stats CSV via scripted input (curl or socket) every 30–60 seconds. Parse backend/frontend rows; extract status (UP/DOWN), qcur (current queued requests), scur (current sessions), and response code distribution. Forward to Splunk via HEC. Alert when any backend is DOWN or queue_depth exceeds 10. Correlate with syslog for connection errors and backend health transitions.
- **Visualization:** Status grid (backend × health), Table (backends with queue depth), Line chart (queue depth over time), Single value (DOWN backends count).
- **CIM Models:** N/A

---

### UC-8.4.10 · Kong Rate Limit Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Security
- **Value:** Kong `rate_limiting` plugin log lines and `429` with `RateLimit-*` headers. Identifies abusive consumers vs tight quotas.
- **App/TA:** Kong admin/access logs
- **Data Sources:** `kong:access` `status=429`, `rate_limiting` plugin log
- **SPL:**
```spl
index=api sourcetype="kong:access" status=429
| stats count by consumer_id, request_uri, rate_limit_plugin
| sort -count
| head 50
```
- **Implementation:** Enable plugin logging. Baseline 429s per consumer. Alert on spike vs baseline or new consumer_id hitting limit.
- **Visualization:** Bar chart (429 by consumer), Line chart (429 rate), Table (top limited routes).
- **CIM Models:** Web

---

### UC-8.4.11 · AWS API Gateway 4xx/5xx Trends
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** CloudWatch `4XXError`, `5XXError`, `Latency` per API stage. Single pane for serverless API frontends.
- **App/TA:** `Splunk_TA_aws` CloudWatch
- **Data Sources:** `AWS/ApiGateway` metrics, execution logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApiGateway" metric_name IN ("4XXError","5XXError")
| timechart span=5m sum(Sum) as err by ApiName, Stage, metric_name
| where err > 0
```
- **Implementation:** Enable detailed metrics per stage. Alert on 5XX >0 sustained or 4XX spike vs baseline. Join with Lambda logs for root cause.
- **Visualization:** Stacked area (4xx vs 5xx), Line chart (error rate), Table (API, stage, errors).
- **CIM Models:** Web

---

### UC-8.4.12 · Apigee Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Apigee analytics API or syslog with `fault` policy name (SOAPThreat, JSONThreat, Quota, SpikeArrest) for blocked requests.
- **App/TA:** Apigee export (BigQuery/Splunk), `apigee:analytics`
- **Data Sources:** `fault` policy, `developer_app`, `response_status_code`
- **SPL:**
```spl
index=api sourcetype="apigee:analytics"
| where isnotnull(fault_policy) OR response_status_code="429"
| stats count by fault_policy, proxy_name, developer_app
| sort -count
```
- **Implementation:** Ingest nightly or hourly analytics. Alert on new fault_policy or high `SpikeArrest` counts. Tune policies vs false positives.
- **Visualization:** Bar chart (faults by policy), Table (proxy, policy, count), Line chart (policy violations over time).
- **CIM Models:** Web

---

### UC-8.4.13 · API Response Time SLA Breaches
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** p95/p99 latency from gateway access logs vs documented SLA per route (`/api/v1/orders`). Complements UC-8.4.2 with SLA lookup join.
- **App/TA:** Kong, Envoy, AWS API GW access logs
- **Data Sources:** `latency`, `request_uri`, `route_id`
- **SPL:**
```spl
index=api sourcetype="kong:access"
| lookup api_route_sla route_uri OUTPUT p95_ms_sla
| stats perc95(latency) as p95 by route_uri
| where p95 > p95_ms_sla
| table route_uri p95 p95_ms_sla
```
- **Implementation:** Maintain SLA lookup per route. Run every 15m. Alert on breach for 3 consecutive windows. Exclude OPTIONS from stats.
- **Visualization:** Line chart (p95 vs SLA), Table (breached routes), Heatmap (route × hour).
- **CIM Models:** Web

---

### UC-8.4.14 · API Key Abuse Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Unusual volume of requests per API key or key used from many distinct IPs/countries in short window.
- **App/TA:** Gateway logs with `consumer_id` or `api_key` hash
- **Data Sources:** `kong:access` `credential_id`, `src_ip`
- **SPL:**
```spl
index=api sourcetype="kong:access"
| stats count, dc(src_ip) as ips by credential_id, _time span=1h
| where count > 10000 OR ips > 50
| table credential_id count ips
```
- **Implementation:** Never log raw API keys. Use hashed id. Baseline per credential. Alert on volume or IP diversity anomaly. Integrate with IP reputation.
- **Visualization:** Table (credential, count, ips), Map (src_ip), Timeline (abuse spikes).
- **CIM Models:** Web

---

### UC-8.4.15 · GraphQL Query Depth Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Depth/complexity limit errors from Apollo/GraphQL server logs prevent DoS via deep queries.
- **App/TA:** Application logs, GraphQL gateway
- **Data Sources:** `graphql:request` `depth`, `errors`, `operationName`
- **SPL:**
```spl
index=application sourcetype="graphql:server"
| search "depth limit" OR "complexity" OR "Query is too deep"
| stats count by operationName, client_name, depth
| where count > 10
```
- **Implementation:** Log structured rejection reason. Alert on high rejection rate from single client or operation. Tune limits for legitimate mobile apps.
- **Visualization:** Table (operation, depth, count), Bar chart (rejections by client), Line chart (depth violations over time).
- **CIM Models:** Web

---

### UC-8.4.16 · API Version Deprecation Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Traffic to `/v1/` deprecated routes vs `/v2/` for migration planning. Header `Sunset` or path-based routing logs.
- **App/TA:** API gateway access logs
- **Data Sources:** `request_uri` path version segment, `X-API-Version`
- **SPL:**
```spl
index=api sourcetype="kong:access"
| rex field=request_uri "^/api/v(?<api_version>\d+)/"
| stats count by api_version, request_uri
| lookup api_version_deprecation api_version OUTPUT sunset_epoch
| eval days_to_sunset=round((sunset_epoch-now())/86400)
| where days_to_sunset < 90 AND api_version="1"
```
- **Implementation:** Maintain deprecation calendar lookup. Weekly report of traffic still on old versions. Alert on any `/v1/*` usage after sunset date.
- **Visualization:** Pie chart (traffic by version), Line chart (v1 traffic trend), Table (routes still on deprecated version).
- **CIM Models:** Web

---

### 8.5 Caching Layers

**Primary App/TA:** Custom scripted inputs (Redis CLI, Memcached stats), Varnish syslog, SNMP for hardware caches.

---

### UC-8.5.1 · Cache Hit/Miss Ratio
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.5.2 · Memory Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.5.3 · Eviction Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-8.5.4 · Connection Count Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.5.5 · Replication Lag (Redis)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
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
- **CIM Models:** N/A

---

### UC-8.5.6 · Slow Command Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
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
- **CIM Models:** N/A

---

### UC-8.5.7 · Key Expiration Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
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
- **CIM Models:** N/A

---

### UC-8.5.8 · Memcached Hit Ratio and Eviction Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cache hit ratio and eviction rate measure cache effectiveness and capacity pressure. Declining hit ratio or rising evictions indicate undersized cache or changing access patterns.
- **App/TA:** Custom scripted input (memcached stats)
- **Data Sources:** memcached stats command (get_hits, get_misses, evictions)
- **SPL:**
```spl
index=cache sourcetype="memcached:stats"
| eval hit_ratio=round(get_hits/(get_hits+get_misses)*100,2)
| timechart span=5m avg(hit_ratio) as hit_pct, per_second(evictions) as eviction_rate by host
| where hit_pct < 85 OR eviction_rate > 5
```
- **Implementation:** Run `echo stats | nc localhost 11211` (or memcached stats protocol) via scripted input every minute. Parse get_hits, get_misses, evictions, bytes, bytes_read, bytes_written. Forward to Splunk via HEC. Calculate hit ratio; alert when below 85%. Track eviction rate; alert when evictions per second exceed 5. Correlate with memory usage (limit_maxbytes).
- **Visualization:** Gauge (hit ratio %), Line chart (hit ratio and eviction rate over time), Single value (current eviction rate), Table (instances with low hit ratio).
- **CIM Models:** N/A

---

### UC-8.5.9 · Squid Proxy Cache Hit Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cache HIT/MISS/DENY rates on forward/reverse proxy indicate cache effectiveness and upstream load. Declining ratio increases origin latency and bandwidth.
- **App/TA:** Custom (Squid access log, SNMP)
- **Data Sources:** Squid access.log (cache result codes), SNMP
- **SPL:**
```spl
index=proxy sourcetype="squid:access"
| rex "TCP_(?<cache_result>HIT|MISS|DENIED|REFRESH)"
| stats count by cache_result
| eventstats sum(count) as total
| eval pct=round(count/total*100,2)
| where cache_result=="MISS" AND pct > 30
```
- **Implementation:** Configure Squid to log cache result codes (TCP_HIT, TCP_MISS, TCP_DENIED, TCP_REFRESH) in access.log. Forward via Universal Forwarder. Parse cache_result field. Alternatively poll Squid SNMP cacheHitRatio if available. Calculate hit ratio per 5-minute window. Alert when MISS rate exceeds 30%. Correlate with request rate for capacity planning.
- **Visualization:** Pie chart (HIT vs MISS vs DENY), Line chart (hit ratio over time), Table (cache result distribution), Single value (hit ratio %).
- **CIM Models:** Web

---

### UC-8.5.10 · Varnish Cache Hit Rate and Backend Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Value:** Cache efficiency and backend connection failures indicate Varnish health. Backend failures cause cache misses and user-facing errors.
- **App/TA:** Custom scripted input (varnishstat, varnishlog)
- **Data Sources:** varnishstat JSON output
- **SPL:**
```spl
index=cache sourcetype="varnish:stats"
| eval hit_ratio=round(cache_hit/(cache_hit+cache_miss)*100,2)
| where hit_ratio < 80 OR backend_fail > 0 OR backend_busy > 0
| timechart span=5m avg(hit_ratio) as hit_pct, sum(backend_fail) as backend_failures by host
```
- **Implementation:** Run `varnishstat -j` via scripted input every minute. Parse MAIN.cache_hit, MAIN.cache_miss, MAIN.backend_fail, MAIN.backend_busy, MAIN.backend_unhealthy. Forward to Splunk via HEC. Alert when hit ratio drops below 80% or backend failures occur. Correlate backend_fail with backend health probes.
- **Visualization:** Gauge (hit ratio %), Line chart (hit ratio and backend failures), Table (backend health status), Single value (backend failures).
- **CIM Models:** N/A

---

### UC-8.5.11 · Synthetic Transaction Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Performance
- **Value:** Simulated multi-step user journeys with timing per step validate end-to-end availability and detect degradation before users report issues. Step-level timing enables pinpointing of slow components.
- **App/TA:** Splunk Synthetic Monitoring, custom scripted input (Selenium, Playwright)
- **Data Sources:** Synthetic test runner output with step-level timings
- **SPL:**
```spl
index=synthetic sourcetype="synthetic:test"
| eval step_duration=step_end_time-step_start_time
| where overall_status=="FAIL" OR step_duration > 5000
| stats count, avg(step_duration) as avg_step_ms by test_name, step_name
| sort -avg_step_ms
```
- **Implementation:** Run synthetic tests via Splunk Synthetic Monitoring, Selenium, or Playwright. Configure tests to log JSON with test_name, step_name, step_start_time, step_end_time, overall_status, error_message. Forward to Splunk via HEC. Alert when any test fails or step duration exceeds SLA (e.g., 5s). Track step-level trends to identify regressions. Use transaction for multi-step journey correlation.
- **Visualization:** Timeline (test runs with pass/fail), Table (slow steps by test), Line chart (step duration trend), Single value (failed tests).
- **CIM Models:** N/A

---

### UC-8.5.12 · Website Page Load Time Breakdown
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** DNS, connect, TLS, TTFB, and download timing per page element enable root cause analysis of slow page loads. Breakdown identifies whether slowness is network, backend, or resource-related.
- **App/TA:** Splunk RUM or custom scripted input (curl timing)
- **Data Sources:** Navigation Timing API, curl -w format, RUM beacon data
- **SPL:**
```spl
index=rum sourcetype="rum:timing"
| eval dns_ms=domain_dns_end-domain_dns_start, connect_ms=connect_end-connect_start, ttfb_ms=response_start-request_start
| timechart span=5m perc95(ttfb_ms) as p95_ttfb, perc95(dns_ms) as p95_dns by page_url
| where p95_ttfb > 1000
```
- **Implementation:** Instrument frontend with RUM (Splunk RUM, Boomerang, or custom beacon) to capture Navigation Timing API fields. Alternatively run curl with `-w` format for key endpoints. Parse domainLookupEnd-domainLookupStart (DNS), connectEnd-connectStart (connect), responseStart-requestStart (TTFB). Forward to Splunk via HEC. Alert when p95 TTFB exceeds 1s. Correlate with backend latency and CDN metrics.
- **Visualization:** Waterfall (timing breakdown by resource), Line chart (p95 TTFB/DNS/connect over time), Table (slowest pages), Single value (p95 page load).
- **CIM Models:** Web

---

### 8.6 Network Service Availability

Covers Nagios-style active connectivity checks (check_ssh, check_ftp, check_smtp, check_pop, check_imap) reproduced in Splunk using log-based presence/absence detection and scripted synthetic inputs.

---

### UC-8.6.1 · SSH Service Availability Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** SSH is the primary remote administration channel for Linux and Unix servers. An unresponsive SSH daemon locks out operators and often signals broader system distress (OOM, hung kernel, storage full). Nagios `check_ssh` is one of the most universally deployed checks; Splunk replicates it through absence-of-event detection and syslog-based availability trending.
- **App/TA:** `Splunk_TA_nix`, `Splunk_TA_syslog`
- **Data Sources:** `sourcetype=syslog` (sshd messages), scripted input or Stream for TCP/22 probe
- **SPL:**
```spl
| inputlookup monitored_linux_hosts.csv
| fields host
| join type=left host [search index=os sourcetype=syslog process=sshd earliest=-15m | stats count as ssh_events by host]
| where isnull(ssh_events) OR ssh_events=0
| eval status="SSH_DOWN"
| table host, status
```
- **Implementation:** Ingest sshd syslog messages (Linux) via Universal Forwarder. Maintain a lookup (`monitored_linux_hosts.csv`) of expected hosts. Use `tstats` or a scheduled search every 5 minutes to detect hosts with no sshd events in the last 10 minutes. Optionally deploy a scripted input that performs a TCP connect to port 22 and logs result (0=up, 1=down) for direct availability data. Alert on SSH_DOWN status for more than 2 consecutive intervals to reduce false positives during restart.
- **Visualization:** Single value (hosts with SSH down), Table (host, last seen, duration down), Timeline (SSH availability per host), Heatmap (host × time availability).
- **CIM Models:** N/A

---

### UC-8.6.2 · FTP / SFTP Service Availability Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** FTP and SFTP services support automated file transfer workflows between systems, partners, and legacy integrations. Silent service failures cause missed file deliveries that may not surface until business processes fail downstream. Nagios `check_ftp` provides port-level verification; Splunk replicates this through daemon log monitoring and scripted probes.
- **App/TA:** `Splunk_TA_syslog`, custom scripted input
- **Data Sources:** `vsftpd`, `proftpd`, or `openssh-sftp-server` logs; scripted TCP port probe output
- **SPL:**
```spl
| inputlookup ftp_hosts.csv
| fields host, service_name
| join type=left host [search index=os (sourcetype=vsftpd OR sourcetype=syslog process=sftp-server) earliest=-15m | stats count as ftp_events by host]
| where isnull(ftp_events) OR ftp_events=0
| eval status="FTP_DOWN"
| table host, service_name, status
```
- **Implementation:** Monitor vsftpd, proftpd, or OpenSSH SFTP subsystem logs via Universal Forwarder. For SFTP (port 22 subsystem), filter syslog for `sftp-server` process events. Alert when no daemon activity is seen for more than 15 minutes on a host expected to serve FTP/SFTP. Supplement with a scripted input using `nc -z -w5 host 21` (FTP) or `nc -z -w5 host 22` (SFTP) logged as synthetic check results. Correlate FTP availability with file-transfer success/failure logs.
- **Visualization:** Table (host, port, status, last event), Single value (unavailable FTP hosts), Line chart (event rate over time per host), Alert timeline.
- **CIM Models:** N/A

---

### UC-8.6.3 · SMTP Service Availability
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Distinct from mail queue depth monitoring — this checks whether the SMTP daemon is accepting TCP connections and responding to EHLO. A crashed postfix or sendmail process stops inbound/outbound mail entirely without generating queue entries. Nagios `check_smtp` verifies this at the connection layer; Splunk replicates it via daemon-level log monitoring.
- **App/TA:** `Splunk_TA_syslog`, `Splunk_TA_postfix` (community)
- **Data Sources:** `sourcetype=syslog` (postfix, sendmail, exim logs), `sourcetype=postfix:syslog`
- **SPL:**
```spl
index=mail (sourcetype=syslog process=postfix* OR sourcetype="postfix:syslog")
| bucket _time span=5m
| stats count as smtp_events by host, _time
| streamstats window=3 min(smtp_events) as min_events by host
| where min_events=0
| eval status="SMTP_DOWN"
| table _time, host, status
```
- **Implementation:** Ingest Postfix/Sendmail syslog output via Universal Forwarder. Under normal operation, an active MTA generates constant log activity (queue manager, cleanup, smtp/smtpd). Absence of events for 5–10 minutes on an expected mail host indicates SMTP process death or service failure. Alert after 2 consecutive empty windows. Complement with a scripted input: `echo QUIT | nc -w5 host 25` — log exit code as synthetic probe result. Monitor separately for TLS handshake failures (port 587/465) as distinct service checks.
- **Visualization:** Single value (SMTP hosts down), Timeline (downtime events), Line chart (event rate per mail host), Table (host, MTA type, last event timestamp).
- **CIM Models:** N/A

---

### UC-8.6.4 · POP3 / IMAP Mail Retrieval Service Availability
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** POP3 and IMAP services allow mail clients to retrieve messages. Even when delivery works correctly, a crashed Dovecot or Cyrus daemon prevents users from reading email, appearing as a total mail outage. Nagios `check_pop` and `check_imap` monitor these ports directly; Splunk replicates availability detection through daemon log analysis.
- **App/TA:** `Splunk_TA_syslog`
- **Data Sources:** `sourcetype=syslog` (dovecot, cyrus-imapd logs), Dovecot authentication log
- **SPL:**
```spl
index=mail sourcetype=syslog (process=dovecot OR process=imap OR process=pop3)
| bucket _time span=5m
| stats count as imap_events by host, _time
| where isnull(imap_events) OR imap_events=0
| eval status="IMAP_POP3_DOWN"
| table _time, host, status
```
- **Implementation:** Forward Dovecot or Cyrus IMAP logs via Universal Forwarder. Dovecot logs login events, failed auth, and daemon lifecycle events continuously during normal operation. Zero events for >10 minutes on a mail host indicates a process crash or service failure. Alert after 2 consecutive empty windows. Cross-correlate with auth failures (could indicate process restart loops). For comprehensive coverage, deploy a scripted TCP probe on ports 143 (IMAP), 993 (IMAPS), 110 (POP3), 995 (POP3S).
- **Visualization:** Table (host, protocol, port, status), Timeline (downtime events), Single value (services down count), Line chart (login event rate as proxy for service health).
- **CIM Models:** N/A

---

### UC-8.6.5 · Mail Queue Depth and Deferred Message Backlog
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Growing mail queue (deferred, hold) indicates delivery failures, recipient issues, or abuse. Detecting backlog early prevents bounce storms and blacklisting.
- **App/TA:** `Splunk_TA_syslog`, custom scripted input (mailq, postqueue)
- **Data Sources:** Postfix `mailq`, Sendmail queue, Exchange queue length
- **SPL:**
```spl
index=mail sourcetype=mail_queue host=*
| stats latest(queue_depth) as depth, latest(deferred_count) as deferred, latest(_time) as last_seen by host
| where depth > 100 OR deferred > 50
| table host depth deferred last_seen
```
- **Implementation:** Run `mailq` or equivalent every 5 minutes. Parse queue depth and deferred count. Alert when queue exceeds 100 or deferred exceeds 50. Correlate with rejection logs and recipient domains.
- **Visualization:** Line chart (queue depth over time), Table (host, queue, deferred), Single value (max queue).
- **CIM Models:** N/A

---

### UC-8.6.6 · SMTP Authentication and Relay Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Failed SMTP auth or unauthorized relay attempts may indicate credential stuffing or abuse. Monitoring supports security and ensures relay policy is enforced.
- **App/TA:** `Splunk_TA_syslog`, mail server logs
- **Data Sources:** Postfix maillog, Sendmail logs, Exchange SMTP receive connector logs
- **SPL:**
```spl
index=mail sourcetype=syslog (process=postfix OR process=sendmail) ("authentication failed" OR "relay denied" OR "reject")
| rex "user=(?<sasl_user>\S+)"
| stats count by src_ip, sasl_user, action
| where count > 10
| sort -count
```
- **Implementation:** Forward mail server logs. Extract auth and relay outcomes. Alert on high volume of auth failures from single IP or relay denied for internal IPs (possible misconfiguration).
- **Visualization:** Table (IP, user, action, count), Timechart of failures, Map (GeoIP).
- **CIM Models:** Authentication

---

### UC-8.6.7 · Mail Delivery Rate and Bounce Rate by Domain
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Sudden drop in delivery rate or spike in bounces for a domain indicates reputation or configuration issues. Trending supports deliverability and capacity planning.
- **App/TA:** Mail server logs, bounce logs
- **Data Sources:** Postfix/Sendmail delivery status, bounce messages, Exchange tracking logs
- **SPL:**
```spl
index=mail sourcetype=mail_delivery
| stats count(eval(status="delivered")) as delivered, count(eval(status="bounce")) as bounces by domain, _time span=1h
| eval bounce_rate=round(bounces/(delivered+bounces)*100, 2)
| where bounce_rate > 5 OR delivered < 10
| table domain delivered bounces bounce_rate
```
- **Implementation:** Parse delivery and bounce events by recipient domain. Compute hourly delivery and bounce rate. Alert when bounce rate exceeds 5% or delivery volume drops significantly for critical domains.
- **Visualization:** Line chart (delivery and bounce rate by domain), Table (domain, delivered, bounces, %), Bar chart (bounce rate by domain).
- **CIM Models:** N/A

---

### UC-8.6.8 · Outbound Mail Volume and Recipient Anomaly
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unusual outbound volume or new bulk recipients may indicate compromised account or phishing campaign. Baseline and anomaly detection support incident response.
- **App/TA:** Mail server logs
- **Data Sources:** Postfix/Sendmail/Exchange outbound logs
- **SPL:**
```spl
index=mail sourcetype=mail_send
| stats dc(recipient) as recipients, count as msg_count by sender, _time span=1h
| eventstats avg(msg_count) as avg_count, stdev(msg_count) as std_count by sender
| eval z_score=if(std_count>0, (msg_count-avg_count)/std_count, 0)
| where z_score > 3 OR recipients > 100
| table _time sender msg_count recipients z_score
```
- **Implementation:** Ingest outbound send events. Baseline message count and unique recipients per sender (hourly). Alert when volume or recipient count exceeds 3 standard deviations or recipient count >100 in one hour.
- **Visualization:** Table (sender, count, recipients, z-score), Line chart (volume by sender), Bar chart (top senders).
- **CIM Models:** N/A

---

### UC-8.6.9 · Mail Server TLS and Certificate Expiration
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Security
- **Value:** Expired or expiring TLS certificates on SMTP/IMAP/POP break encryption and can cause delivery failures. Proactive monitoring prevents outages.
- **App/TA:** Custom scripted input (openssl s_client)
- **Data Sources:** TLS handshake to mail server ports (25, 465, 587, 993, 995)
- **SPL:**
```spl
index=mail sourcetype=mail_tls host=*
| eval days_left=round((expiry_epoch-now())/86400, 0)
| where days_left < 30
| table host port days_left subject
| sort days_left
```
- **Implementation:** Script that connects to mail server ports and extracts certificate expiry (e.g. `openssl s_client -connect host:25 -starttls smtp`). Ingest daily. Alert when expiry is within 30 days.
- **Visualization:** Table (host, port, days left), Single value (soonest expiry), Gauge (days remaining).
- **CIM Models:** N/A

---

### UC-8.6.10 · Envoy Proxy Upstream Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Upstream cluster health, retry rate, and circuit breaker trips indicate Envoy proxy and backend service health. Detection enables rapid isolation of failing upstreams.
- **App/TA:** Custom (Envoy admin /stats, Prometheus metrics)
- **Data Sources:** Envoy /stats endpoint (envoy_cluster_upstream_cx_active, envoy_cluster_upstream_rq_retry)
- **SPL:**
```spl
index=mesh sourcetype="envoy:stats"
| search "envoy_cluster_upstream" ("cx_active" OR "rq_retry" OR "circuit_breakers")
| rex "envoy_cluster\.(?<cluster>[^.]+)\.(?<metric>\w+)=(?<value>\d+)"
| stats latest(value) as val by cluster, metric
| where metric=="rq_retry" AND val > 0 OR metric=="circuit_breakers_default_rq_open" AND val > 0
```
- **Implementation:** Enable Envoy admin interface (`/stats`). Poll via scripted input or Prometheus scrape every 30 seconds. Parse envoy_cluster_upstream_cx_active, envoy_cluster_upstream_rq_retry, envoy_cluster_upstream_rq_retry_overflow, circuit_breakers.*.rq_open. Forward to Splunk via HEC. Alert when retry rate spikes or circuit breaker opens. Correlate with upstream service health checks.
- **Visualization:** Status grid (cluster × health), Line chart (retry rate over time), Table (clusters with circuit breaker trips), Single value (active circuit breakers).
- **CIM Models:** N/A

---

### UC-8.6.11 · HashiCorp Vault Seal Status and Token Count
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Availability
- **Value:** Vault health, auto-unseal events, and token creation rate indicate secrets management availability. Sealed Vault blocks all secret access; token anomalies may indicate abuse.
- **App/TA:** Custom (Vault API, audit log)
- **Data Sources:** Vault `/v1/sys/health`, `/v1/sys/audit`, audit log
- **SPL:**
```spl
index=vault sourcetype="vault:health"
| where sealed==true
| table _time, host, sealed, standby, version
```
- **Implementation:** Poll Vault `/v1/sys/health` via scripted input every minute. Parse sealed, standby, version, replication_performance_mode. Forward to Splunk via HEC. Enable Vault audit log; forward audit events for token creation and auth attempts. Alert immediately when sealed==true. Track token creation rate; alert on anomalies. Correlate unseal events with operator actions.
- **Visualization:** Single value (sealed status — target: false), Table (Vault cluster health), Line chart (token creation rate), Timeline (unseal events).
- **CIM Models:** N/A

---

### UC-8.6.12 · HashiCorp Consul Service Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Service registration, deregistration, and health check failures indicate Consul service discovery health. Critical checks mean services are unavailable for discovery and routing.
- **App/TA:** Custom (Consul HTTP API)
- **Data Sources:** Consul `/v1/health/state/critical`, `/v1/catalog/services`
- **SPL:**
```spl
index=consul sourcetype="consul:health"
| where status=="critical"
| stats count, latest(Output) as Output by Node, ServiceID, CheckID
| table Node, ServiceID, CheckID, count, Output
```
- **Implementation:** Poll Consul `/v1/health/state/critical` and `/v1/catalog/services` via scripted input every minute. Parse Node, ServiceID, CheckID, Status, Output. Forward to Splunk via HEC. Alert when any service has critical health. Track service registration/deregistration events from catalog changes. Correlate with deployment events.
- **Visualization:** Status grid (service × health), Table (critical services), Single value (critical check count), Timeline (health transitions).
- **CIM Models:** N/A

---

### UC-8.6.13 · HashiCorp Nomad Job and Allocation Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failed allocations and job deployment health indicate Nomad scheduler and workload availability. Failed allocations mean tasks are not running; deployment failures block rollouts.
- **App/TA:** Custom (Nomad HTTP API)
- **Data Sources:** Nomad `/v1/jobs`, `/v1/allocations`
- **SPL:**
```spl
index=nomad sourcetype="nomad:allocations"
| where ClientStatus=="failed" OR (DesiredStatus=="run" AND ClientStatus!="running")
| stats count by JobID, TaskGroup, ClientStatus
| sort -count
```
- **Implementation:** Poll Nomad `/v1/jobs` and `/v1/allocations` via scripted input every 5 minutes. Parse JobID, TaskGroup, ClientStatus, DesiredStatus, CreateIndex. Forward to Splunk via HEC. Alert when ClientStatus==failed or allocations are pending/running when desired is stop. Track deployment status (job version, allocation placement). Correlate with node availability.
- **Visualization:** Table (failed allocations by job), Single value (failed allocation count), Status grid (job × allocation status), Timeline (allocation events).
- **CIM Models:** N/A

---

### UC-8.6.14 · Asterisk / FreePBX Call Quality and Trunk Status
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Performance
- **Value:** Call volume, ASR (Answer Seizure Ratio), ACD (Average Call Duration), and trunk registration indicate VoIP/PBX health. Trunk failures block inbound/outbound calls; quality metrics affect user experience.
- **App/TA:** Custom (Asterisk AMI, CDR logs)
- **Data Sources:** Asterisk CDR logs, AMI events, SIP trunk status
- **SPL:**
```spl
index=asterisk sourcetype="asterisk:cdr"
| eval duration_sec=tonumber(duration)
| stats count as calls, avg(duration_sec) as acd, count(eval(disposition=="ANSWERED")) as answered by _time span=1h
| eval asr=round(answered/calls*100,2)
| where asr < 80 OR acd < 60
```
- **Implementation:** Forward Asterisk CDR (Call Detail Record) logs via Universal Forwarder. Parse caller, callee, duration, disposition, channel. For trunk status, use AMI (Asterisk Manager Interface) or `asterisk -rx "pjsip show endpoints"` via scripted input. Poll trunk registration status every 5 minutes. Calculate ASR (answered/total*100) and ACD per hour. Alert when ASR drops below 80% or trunk shows UNREACHABLE. Track call volume for capacity planning.
- **Visualization:** Line chart (ASR and ACD over time), Table (trunk status), Single value (calls per hour), Bar chart (call volume by trunk).
- **CIM Models:** N/A

---

### UC-8.6.15 · SMTP Relay Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Availability
- **Value:** Tracks messages relayed through internal SMTP gateways vs policy — unexpected relay volume or open relay abuse paths.
- **App/TA:** `Splunk_TA_syslog`, Postfix/Exchange logs
- **Data Sources:** `postfix:syslog` `relay=`, `status=sent`, `reject` relay attempts
- **SPL:**
```spl
index=mail sourcetype="postfix:syslog" OR sourcetype=syslog process=postfix
| search relay=* OR "relay access denied"
| stats count by relay_domain, action, src_ip
| where count > 500
```
- **Implementation:** Parse relay lines for authorized vs denied. Alert on high relay denied from single IP (scanning) or high accepted relay to external domains (misconfiguration).
- **Visualization:** Table (relay domain, count), Line chart (relay attempts), Single value (relay denied rate).
- **CIM Models:** N/A

---

### UC-8.6.16 · NTP Stratum Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Stratum jumps or large offset indicate bad upstream clock or local drift — affects Kerberos, TLS, and distributed logs.
- **App/TA:** `Splunk_TA_nix`, `ntpq`/`chronyc` scripted input
- **Data Sources:** `ntp:peer` `stratum`, `offset_ms`, `jitter_ms`
- **SPL:**
```spl
index=os sourcetype="ntp:peer"
| where stratum > 4 OR abs(offset_ms) > 100
| timechart span=5m max(stratum) as stratum, max(abs(offset_ms)) as abs_offset by host
```
- **Implementation:** Poll `chronyc tracking` or `ntpq -pn` every 5m. Alert when stratum >4 or |offset| >100ms sustained. Correlate with VM time sync settings.
- **Visualization:** Line chart (offset and stratum), Table (hosts with bad clock), Single value (max |offset|).
- **CIM Models:** N/A

---

### UC-8.6.17 · DNS Recursive Query Volume
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Security
- **Value:** Sudden spike in recursive queries on internal resolvers may indicate DDoS, malware, or misconfigured application loops.
- **App/TA:** BIND `named` logs, Infoblox DNS, CoreDNS logs
- **Data Sources:** `dns:query` recursive flag, `client` IP, `qname`
- **SPL:**
```spl
index=dns sourcetype="bind:query" OR sourcetype="dns:query"
| where recursive=1
| bucket _time span=1m
| stats count as qps by client_ip, _time
| eventstats avg(qps) as avg_q by client_ip
| where qps > avg_q*10 AND qps > 1000
```
- **Implementation:** Baseline QPS per client subnet. Alert on 10× baseline or absolute flood. Top `qname` for tunneling investigation.
- **Visualization:** Line chart (recursive QPS), Table (top clients), Bar chart (query types).
- **CIM Models:** N/A

---

### UC-8.6.18 · TFTP Unauthorized Access
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** TFTP should be rare in enterprise networks. Any RRQ/WRQ outside PXE scope may indicate data exfil or firmware abuse.
- **App/TA:** Firewall logs, `atftpd`/`tftpd` syslog
- **Data Sources:** `tftp:syslog` `filename`, `op`, `src_ip`
- **SPL:**
```spl
index=network sourcetype="tftp:log" OR sourcetype="syslog" process=tftpd
| search RRQ OR WRQ
| lookup tftp_allowed_subnets src_ip OUTPUT allowed
| where allowed!=1 OR isnull(allowed)
| table _time, src_ip, filename, op
```
- **Implementation:** Maintain allowlist for PXE subnets. Alert on any other TFTP read/write. Block TFTP at firewall unless required.
- **Visualization:** Timeline (TFTP events), Table (unauthorized attempts), Single value (blocked attempts).
- **CIM Models:** N/A

---

### UC-8.6.19 · SNMP Community String Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Detects use of default `public`/`private` or unauthorized SNMP GETs to network devices for SNMPv2c exposure auditing.
- **App/TA:** Device syslog, SNMP proxy audit
- **Data Sources:** `snmpd` auth failures, `community` in trap receiver logs
- **SPL:**
```spl
index=network sourcetype="snmp:audit" OR (sourcetype=syslog process=snmpd)
| search "Authentication failed" OR community="public" OR community="private"
| stats count by src_ip, device, community
| where count > 10
```
- **Implementation:** Forward snmpd auth failures. Alert on default community strings in use or brute-force patterns. Migrate devices to SNMPv3.
- **Visualization:** Table (src_ip, device, community), Bar chart (failures by device), Line chart (auth failure rate).
- **CIM Models:** N/A

---

### 8.7 Cisco ThousandEyes — Synthetic Web & Application Testing

**Primary App/TA:** Cisco ThousandEyes App for Splunk (Splunkbase 7719) — Cisco Supported

---

### UC-8.7.1 · HTTP Server Availability Monitoring (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors web server availability from multiple global vantage points using ThousandEyes Cloud and Enterprise Agents. Detects regional outages that internal monitoring misses because the problem is between the user and the server.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_availability by thousandeyes.test.name, server.address, thousandeyes.source.agent.name
| where avg_availability < 100
| sort avg_availability
```
- **Implementation:** Create HTTP Server tests in ThousandEyes targeting critical web applications and stream metrics to Splunk via the Tests Stream input. The OTel metric `http.server.request.availability` reports 100% when the HTTP request succeeds and 0% when any error occurs. The Splunk App Application dashboard includes an "HTTP Server Availability (%)" panel with permalink drilldown.
- **Visualization:** Line chart (availability % over time), Single value (current availability), Table (test, server, agent, availability).
- **CIM Models:** N/A

---

### UC-8.7.2 · HTTP Server Response Time Tracking (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks Time to First Byte (TTFB) from ThousandEyes agents to web servers. Rising response times indicate backend degradation, infrastructure bottlenecks, or increased load — often visible from external vantage points before internal monitoring catches it.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| timechart span=5m avg(http.client.request.duration) as avg_ttfb_s by thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1)
```
- **Implementation:** The OTel metric `http.client.request.duration` reports TTFB in seconds. The Splunk App Application dashboard includes an "HTTP Server Request Duration (s)" line chart. Alert when TTFB exceeds your SLA threshold (e.g., 2 seconds). Correlate with `http.response.status_code` to distinguish slow responses from errors.
- **Visualization:** Line chart (TTFB over time by test), Single value (avg TTFB), Table with drilldown to ThousandEyes.
- **CIM Models:** N/A

---

### UC-8.7.3 · HTTP Server Throughput Analysis (ThousandEyes)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Measures download throughput from ThousandEyes agents to web servers, revealing bandwidth constraints or content delivery issues from the user perspective.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.throughput) as avg_throughput by thousandeyes.test.name, thousandeyes.source.agent.name
| eval throughput_mbps=round(avg_throughput/1048576,2)
| sort -throughput_mbps
```
- **Implementation:** The OTel metric `http.server.throughput` reports bytes per second. The Splunk App Application dashboard includes an "HTTP Server Throughput (MB/s)" line chart. Low throughput combined with high latency typically indicates a network bottleneck; low throughput with low latency suggests a server-side rate limit.
- **Visualization:** Line chart (throughput MB/s over time), Table (test, agent, throughput), Column chart by agent.
- **CIM Models:** N/A

---

### UC-8.7.4 · Page Load Completion Rate (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Measures whether web pages fully load from the user's perspective. Incomplete page loads indicate broken resources, blocked CDN content, or JavaScript errors that prevent users from completing tasks.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Page Load tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.completion) as avg_completion by thousandeyes.test.name, server.address
| where avg_completion < 100
| sort avg_completion
```
- **Implementation:** Create Page Load tests in ThousandEyes targeting critical web applications. The OTel metric `web.page_load.completion` reports 100% when the page loads successfully and 0% on error. Page Load tests automatically include underlying Agent-to-Server network tests, providing correlated network and application data.
- **Visualization:** Single value (completion %), Line chart (completion over time), Table (test, server, completion).
- **CIM Models:** N/A

---

### UC-8.7.5 · Page Load Duration Trending (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks total page load time including all resources (HTML, CSS, JS, images). Trending reveals gradual degradation from growing page weight, slow third-party resources, or backend issues.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Page Load tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="page-load"
| timechart span=5m avg(web.page_load.duration) as avg_load_s by thousandeyes.test.name
```
- **Implementation:** The OTel metric `web.page_load.duration` reports total page load time in seconds. The Splunk App Application dashboard includes a "Page Load Duration (s)" line chart with permalink drilldown to ThousandEyes waterfall views. Alert when load duration exceeds your performance budget.
- **Visualization:** Line chart (load time over time), Single value (avg load time), Table with permalink drilldown.
- **CIM Models:** N/A

---

### UC-8.7.6 · API Endpoint Completion Rate (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors multi-step API test completion, ensuring that entire API workflows (authentication, data retrieval, processing) succeed end-to-end from external vantage points.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (API tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.completion) as avg_completion by thousandeyes.test.name
| where avg_completion < 100
| sort avg_completion
```
- **Implementation:** Create API tests in ThousandEyes with multi-step sequences testing your critical API workflows. The OTel metric `api.completion` reports overall completion percentage. Per-step metrics (`api.step.completion`, `api.step.duration`) are also available with the `thousandeyes.test.step` attribute. The Splunk App Application dashboard includes an "API Completion (%)" panel.
- **Visualization:** Single value (completion %), Line chart (completion over time), Table (test, completion).
- **CIM Models:** N/A

---

### UC-8.7.7 · API Response Time Monitoring (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks total API test execution duration including all steps, revealing when API performance degrades from the consumer's perspective.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (API tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="api"
| timechart span=5m avg(api.duration) as avg_api_duration_s by thousandeyes.test.name
```
- **Implementation:** The OTel metric `api.duration` reports total API test execution time in seconds. For per-step analysis, use `api.step.duration` filtered by `thousandeyes.test.step`. The Splunk App Application dashboard includes an "API Request Duration (s)" line chart with permalink drilldown.
- **Visualization:** Line chart (API duration over time), Table (test, duration), Column chart (duration by step).
- **CIM Models:** N/A

---

### UC-8.7.8 · Transaction Test Completion Rate (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Transaction tests execute scripted multi-step user workflows (login, navigate, submit form, verify result). Completion rate below 100% means users cannot complete critical business processes.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Transaction tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.completion) as avg_completion sum(web.transaction.errors.count) as total_errors by thousandeyes.test.name
| where avg_completion < 100 OR total_errors > 0
| sort avg_completion
```
- **Implementation:** Create Transaction tests in ThousandEyes using Selenium-based scripted workflows that simulate real user journeys. The OTel metric `web.transaction.completion` reports 100% on success and 0% on error. `web.transaction.errors.count` returns 1 when an error occurs and 0 otherwise. The Splunk App Application dashboard includes a "Transaction Completion (%)" panel.
- **Visualization:** Single value (completion %), Line chart (completion over time), Table (test, completion, errors).
- **CIM Models:** N/A

---

### UC-8.7.9 · Transaction Duration Analysis (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures end-to-end time for complex user workflows. Slow transactions directly impact user productivity and satisfaction. Trending reveals gradual degradation across the multi-step flow.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Transaction tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="web-transactions"
| timechart span=5m avg(web.transaction.duration) as avg_transaction_s by thousandeyes.test.name
```
- **Implementation:** The OTel metric `web.transaction.duration` reports total transaction execution time in seconds (only reported when the transaction completes without errors). The Splunk App Application dashboard includes a "Transaction Duration (s)" line chart with permalink drilldown to ThousandEyes. ThousandEyes also supports OpenTelemetry traces for transaction tests, providing detailed span-level timing.
- **Visualization:** Line chart (transaction duration over time), Table (test, agent, duration), Drilldown to ThousandEyes trace view.
- **CIM Models:** N/A

---

### UC-8.7.10 · SaaS Application Response Time Comparison (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Compares availability and response time across business-critical SaaS applications (Microsoft 365, Salesforce, ServiceNow, etc.) from multiple office locations, enabling data-driven SaaS vendor performance management.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server / Page Load tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server" OR thousandeyes.test.type="page-load"
| search thousandeyes.test.name="*M365*" OR thousandeyes.test.name="*Salesforce*" OR thousandeyes.test.name="*ServiceNow*"
| stats avg(http.server.request.availability) as avg_avail avg(http.client.request.duration) as avg_ttfb_s by thousandeyes.test.name, thousandeyes.source.agent.location
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1)
| sort thousandeyes.test.name, avg_ttfb_ms
```
- **Implementation:** Create HTTP Server or Page Load tests in ThousandEyes for each SaaS application, running from Enterprise Agents at each office and Cloud Agents in relevant regions. Name tests consistently (e.g., "M365 - Exchange Online", "Salesforce - Login Page"). ThousandEyes provides best-practice monitoring guides for Microsoft 365, Salesforce, and other major SaaS platforms.
- **Visualization:** Column chart (TTFB by SaaS app per location), Table (app, location, availability, TTFB), Comparison dashboard.
- **CIM Models:** N/A

---

### UC-8.7.11 · Multi-Region SaaS Availability (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors SaaS application reachability from multiple geographic regions using ThousandEyes Cloud Agents, identifying regional availability issues that affect specific user populations.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_availability by thousandeyes.test.name, thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.location
| where avg_availability < 100
| sort avg_availability
```
- **Implementation:** Deploy the same HTTP Server tests across ThousandEyes Cloud Agents in Americas, EMEA, and APAC regions. Use `thousandeyes.source.agent.geo.country.iso_code` and `thousandeyes.source.agent.location` attributes to group results by region. A service that is available from US agents but not from EU agents indicates a regional issue.
- **Visualization:** Map (availability by agent location), Table (region, app, availability), Column chart (availability by region).
- **CIM Models:** N/A

---

### UC-8.7.12 · FTP Server Availability and Throughput (ThousandEyes)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Performance
- **Value:** Monitors FTP/SFTP server availability and file transfer throughput from ThousandEyes agents, ensuring file transfer services are accessible and performing adequately for automated data exchange workflows.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (FTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="ftp-server"
| stats avg(ftp.server.request.availability) as avg_availability avg(ftp.client.request.duration) as avg_response_s avg(ftp.server.throughput) as avg_throughput by thousandeyes.test.name, server.address
| eval avg_response_ms=round(avg_response_s*1000,1), throughput_mbps=round(avg_throughput/1048576,2)
| sort avg_availability, -throughput_mbps
```
- **Implementation:** Create FTP Server tests in ThousandEyes for critical file transfer endpoints. The OTel metric `ftp.server.request.availability` reports availability, `ftp.client.request.duration` reports TTFB, and `ftp.server.throughput` reports bytes per second. The `ftp.request.command` attribute indicates the FTP command tested (GET, PUT, LS). The Splunk App Voice dashboard includes FTP panels.
- **Visualization:** Line chart (availability and throughput over time), Table (server, availability, throughput, response time), Single value.
- **CIM Models:** N/A

---
