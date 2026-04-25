<!-- AUTO-GENERATED from UC-2.6.69.json — DO NOT EDIT -->

---
id: "2.6.69"
title: "Citrix Endpoint Management Server Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.69 · Citrix Endpoint Management Server Health

## Description

The Citrix Endpoint Management application tier sits on a JVM, a relational database, and background schedulers that push policy and app commands. Thread starvation, pool exhaustion, or a stuck job queue can surface as flapping device check-ins and mass policy drift before a simple `ping` fails. Server-side health metrics plus SSL and database utilization give a root-cause-friendly picture that complements per-device UCs. Certificate expiry on the CEM public endpoint is a classic near-miss that full-stack monitoring should never leave to an annual calendar reminder alone.

## Value

The Citrix Endpoint Management application tier sits on a JVM, a relational database, and background schedulers that push policy and app commands. Thread starvation, pool exhaustion, or a stuck job queue can surface as flapping device check-ins and mass policy drift before a simple `ping` fails. Server-side health metrics plus SSL and database utilization give a root-cause-friendly picture that complements per-device UCs. Certificate expiry on the CEM public endpoint is a classic near-miss that full-stack monitoring should never leave to an annual calendar reminder alone.

## Implementation

Instrument each CEM node: JVM thread dumps on alert, JDBC pool via JMX, scheduler backlog from application logs, and a synthetic login or API every five minutes. Forward Windows or Linux system logs. Alert in stages: queue backlog over a static threshold, DB pool over 90 percent for ten minutes, blocked threads over 50 for two samples, and SSL cert under 30 days. Pair with database server KPIs. Document rolling patch windows and scale-out when a single node saturates. Keep an HA pair or cluster view so you alert on the worst node and the cluster average.

## Detailed Implementation

Prerequisites
• Admin access to JMX (secured); DB performance counters; a clear mapping from hostname to CEM site role; TLS inventory for all listener endpoints.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use least-privilege JMX. Omit connection strings in logs. Baseline a normal business week before thresholds.

Step 2 — Create the search and alert
Tie to maintenance windows. Page on SLO burn for the synthetic probe plus internal saturation signals together to reduce false positives.

Step 3 — Validate
In test, cap the DB connection pool in a throwaway node, assert pool and error logs align. For SSL, use a test cert with a near `notAfter` if your CA allows it.

Step 4 — Operationalize
Add to the EUC and database shared on-call line for saturation alerts; run a tabletop twice a year for total CEM outage.

## SPL

```spl
index=app (sourcetype="citrix:endpoint:server:health" OR sourcetype="citrix:cep:jmx")
| eval blocked=tonumber(coalesce(jvm_thread_blocked, blocked_threads, 0))
| eval db_use=tonumber(coalesce(db_pool_in_use, db_active, 0))
| eval db_max=tonumber(coalesce(db_pool_max, db_total, 1))
| eval back=tonumber(coalesce(scheduler_backlog, job_queue, async_queue, 0))
| eval cert_days=if(isnotnull(ssl_cert_expiry_date), round((strptime(ssl_cert_expiry_date,"%Y-%m-%d")-now())/86400,0), null())
| eval db_pct=if(db_max>0, round(100*db_use/db_max,1), 0)
| where blocked>50 OR back>1000 OR db_pct>90 OR (isnotnull(cert_days) AND cert_days<=30)
| stats latest(blocked) as blocked, latest(db_pct) as db_pool_util_pct, latest(back) as queue_backlog, latest(cert_days) as ssl_cert_days_left by host, role
| sort - db_pool_util_pct
```

## Visualization

Node grid: pool percent, queue depth, blocked threads; line chart: backlog with deploy markers; cert countdown single value for public VIP.

## References

- [Citrix Endpoint Management — supported topologies and sizing context](https://docs.citrix.com/en-us/citrix-endpoint-management/citrix-endpoint-mdm-mam.html)
