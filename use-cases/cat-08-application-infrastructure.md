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
