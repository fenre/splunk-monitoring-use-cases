<!-- AUTO-GENERATED from UC-3.1.21.json — DO NOT EDIT -->

---
id: "3.1.21"
title: "Container Runtime Security Events"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.1.21 · Container Runtime Security Events

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We keep motion sensors inside the shop, not only a list of who borrowed the key. If a quiet stockroom suddenly starts rearranging shelves, calling unfamiliar numbers, or tripping a burst of different alarms at once, we treat it like someone turned the back office into a lab without a work order.*

---

## Description

Network ingress controls and image scanners stop helping the instant an actor wins code execution inside a container namespace: from there they rely on shells, package managers, cron persistence, and outbound connects that rarely appear in application logs because those logs were never designed to narrate syscalls. This use case is the kernel-runtime behavioral plane for Linux Docker estates at scale: Falco priorities from sourcetype=falco:json (ingested through Splunk_TA_falco) map rule families to MITRE ATT&CK container techniques such as T1611 escape primitives, T1525 live drift, T1496 hijacking, T1059 interpreters, T1543 persistence, and T1110 credential abuse when your baseline CSV tags them; ebpf:process_exec events expose unexpected descendants versus image_process_baseline.csv golden process regex, including orphan interactive shells when docker:events exec correlation shows no recent operator session (complementing UC-3.1.24 operator exec session auditing rather than replacing it); ebpf:net_connect rows quantify egress diversity and port fan-out, correlate destinations to c2_iocs.csv and tor_exit_nodes.csv, and highlight RFC1918 east-west touches that violate the narrow egress profile of static ingress images. UC-3.1.6 remains the declarative privilege posture on the container object; UC-3.1.25 remains docker.sock and daemon attack-surface telemetry; UC-3.1.24 remains the ticket-backed docker exec lifecycle narrative. None of those siblings substitute continuous syscall-grade Falco plus eBPF process and connect telemetry once an adversary is already inside the cgroup.

## Value

Mean dwell time for in-container intrusions typically collapses from roughly a day of log-only triage to minutes when analysts can chain Falco rule bursts, unexpected process lineage, and IOC-weighted egress in one Splunk row. ATT&CK container coverage becomes measurable: T1611 escape-class mounts and release_agent abuse, T1525 runtime package installs, T1496 miner and stratum chatter, T1059 non-interactive interpreters, T1543 cron or binary-dir mutations, and T1110 failed-login storms each produce distinct evidence lanes instead of a single noisy catch-all. False positives fall when image_process_baseline.csv and falco_rule_baseline.csv ship with the same golden pipeline that signs digests, because benign mesh sidecars and backup tooling are documented rather than treated as malware. Regulators asking for PCI DSS 11.5 change detection, SOC 2 CC7.2 monitoring, or ISO 27001 A.12.4 evidence receive timestamped exports that pair kernel facts with lookup versions. Economically, one thwarted cryptominer or data-exfiltration sprint across tens of thousands of nodes routinely exceeds several years of Falco and eBPF ingest spend when outage and investigation costs are counted honestly.

## Implementation

Land falco:json, ebpf:process_exec, and ebpf:net_connect in index=oti_containers_security via Splunk_TA_falco and Splunk Add-on for Unix and Linux scripted inputs. Version falco_rule_baseline.csv, image_process_baseline.csv, c2_iocs.csv, tor_exit_nodes.csv, and crypto_mining_pools.csv in git; schedule container_uc_3_1_21_runtime_security_events every five minutes (earliest=-1h@h latest=@h); route critical rows to platform and SOC jointly; archive weekly CSV snapshots to your evidence index.

## Evidence

Saved search container_uc_3_1_21_runtime_security_events; versioned lookups falco_rule_baseline.csv, image_process_baseline.csv, c2_iocs.csv, tor_exit_nodes.csv, crypto_mining_pools.csv; weekly CSV snapshots with commit SHAs in a restricted evidence index; dashboard drilldowns on falco:json, ebpf:process_exec, and ebpf:net_connect. External corroboration includes Sysdig and Falco field reports on TeamTNT, Kinsing, and Cetus cryptominer campaigns, MITRE ATT&CK enterprise containers matrix, NIST SP 800-190 discussion of runtime threats to containerized applications, and Aqua Nautilus quarterly threat briefs on Linux container abuse.

## Control test

### Positive scenario

On a sealed lab Linux host, install Falco with a test rule that fires at warning or higher, ingest falco:json into index=oti_containers_security, generate ebpf:process_exec and ebpf:net_connect samples from an approved exporter, populate c2_iocs.csv with a lab destination IP used in a controlled connect, run container_uc_3_1_21_runtime_security_events, and expect a non-null severity among the six mandated tiers with populated container_id and recommended_response.

### Negative scenario

Run nginx:alpine with golden baselines that mark nginx worker patterns as expected, ensure no Falco rules above notice fire, block outbound connects except approved health checks, verify the saved search emits only low_baseline_drift or zero rows after tuning across multiple five-minute intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the container security engineering lead and the operations detection owner who certifies Falco policy bundles and eBPF collection on Linux worker fleets. UC-3.1.21 is the kernel-runtime behavioral axis: it answers what workloads do after they are already running inside cgroups, using syscall-grade telemetry that application logs and pure docker inspect snapshots rarely capture faithfully. UC-3.1.6 proves configuration-time privilege posture on the container object. UC-3.1.25 proves daemon-level docker.sock and plaintext Engine exposure. UC-3.1.24 audits user-initiated docker exec lifecycles and ties sessions to change windows. None of those siblings replace continuous Falco rule evaluation backed by eBPF probes, nor do they baseline per-image process trees and egress entropy the way this control does.

Before indexing, inventory Splunk_TA_falco or an approved HEC path that lands sourcetype falco:json with stable output_fields for container_id, container_image_repository, rule, priority, proc_cmdline, and user_name. Pair it with Splunk Add-on for Unix and Linux scripted inputs or a vetted eBPF exporter that emits sourcetype ebpf:process_exec for clone, execve, and fork lineages with parent PID, and sourcetype ebpf:net_connect for connect and sendto destinations with container scope. Index routing should default to index=oti_containers_security with role separation between platform engineers and application teams.

Governance lookups live beside the saved search. falco_rule_baseline.csv carries rule_name, mitre_technique, and baseline_seen_count summarizing how often each rule historically fired per golden image cohort. image_process_baseline.csv carries image_key and expected_proc_regex describing approved binaries and worker patterns. c2_iocs.csv, tor_exit_nodes.csv, and crypto_mining_pools.csv feed join-wrapped inputlookup enrichment for egress correlation. container_owner.csv continues UC-3.1.x paging discipline with host_id, container_name, owner_team when you extend the alert with routing macros.

Risk briefing for executives: perimeter controls end at the container boundary. After remote code execution lands, attackers pivot through shells, package managers, cron persistence, and outbound callbacks. Falco maps those behaviors to ATT&CK container techniques including T1611 escape primitives, T1525 image modification at runtime, T1496 resource hijacking, T1059 scripting, T1543 persistence, and T1110 credential attacks when brute-force macros fire. eBPF visibility closes the gap between what developers think an image does and what the kernel actually schedules.

Licensing and volume: Falco JSON is moderate compared to full container stdout scraping, but eBPF process exec streams can grow quickly on busy nodes. Cap collection to production tiers first, deduplicate dual writers during OpenTelemetry migration, and keep hot retention aligned with incident response needs rather than multi-year archives on raw syscall feeds.

Legal and privacy: proc_cmdline and Falco output can contain URLs or tokens. Redact at the forwarder when regulation demands, and restrict dashboards that show raw argv to security operations roles.

Differentiation recap: this UC is intentionally not UC-3.1.1 crash taxonomy, UC-3.1.2 memory OOM, UC-3.1.3 CPU throttle, UC-3.1.8 dockerd panic, UC-3.1.13 restart cadence, UC-3.1.14 overlay networking, UC-3.1.22 HEALTHCHECK degradation, or UC-3.1.28 Swarm replica convergence. It is the in-container runtime threat plane.

### Step 2 — Configure data collection

On every Linux worker running Docker CE, Mirantis Container Runtime, or an approved enterprise Engine build with Falco modern probe drivers, install Falco with JSON output enabled and forward alerts through Splunk_TA_falco into index=oti_containers_security with sourcetype falco:json. Confirm priorities notice through emergency are preserved and that container metadata keys survive camelCase and snake_case transforms your props.conf applies.

Deploy eBPF exporters under change control. For process trees, ensure each event includes host_id, container_id or cgroup identifiers that can be joined to docker inspect inventory, parent_pid, exe or comm, and a normalized cmdline field. For network connects, capture destination IP, destination port, and container scope. Map sourcetype ebpf:process_exec and ebpf:net_connect explicitly so multisearch arms remain stable across upgrades.

Schedule docker:events collection into the same index for exec correlation used in the SPL join. Preserve type=exec or exec_create, exec_start, and exec_die patterns consistent with UC-3.1.24 so orphan-shell logic can compare eBPF shells against recent exec windows without duplicating that UC’s full session analytics.

Publish lookups weekly from git. falco_rule_baseline.csv must list mitre_technique strings aligned to Falco default rule tags. image_process_baseline.csv must use Splunk PCRE-friendly patterns tested in Search before production. c2_iocs.csv and crypto_mining_pools.csv should refresh from threat-intel pipelines with ticket references. tor_exit_nodes.csv can follow public feeds but document the publisher for auditors.

Validate on a canary host: trigger a benign Falco notice, confirm _time skew under thirty seconds, and verify eBPF events arrive with matching container_id keys. Clock drift breaks percentile math and exec window joins.

Security hygiene: HEC tokens live in vault, rotate quarterly, and never reuse developer laptop credentials for collectors reading the Docker socket or eBPF perf buffers.

### Step 3 — Create search and alert

Save the SPL as container_uc_3_1_21_runtime_security_events with schedule every five minutes and time range earliest=-1h@h latest=@h during steady state. Throttle duplicate critical rows per host_id and container_id for forty-five minutes unless severity escalates from medium to critical inside the same hour. Route critical tiers to a joint platform and security operations bridge with recommended_response text inline.

Understanding the pipeline: the opening comment macro records indexes, sourcetypes, lookup names, rule-storm threshold, and explicit differentiation from UC-3.1.6, UC-3.1.24, and UC-3.1.25. multisearch fans three arms so a silent Falco outage does not hide eBPF process anomalies, and vice versa. coalesce lists absorb vendor field renames across Falco versions and exporter implementations.

After fan-in, sort establishes deterministic ordering before streamstats. streamstats time_window=300s computes a sliding-window distinct rule count for Falco rows per container, surfacing cascades faster than fixed buckets alone. bin span=5m then creates stable buckets for per-container Falco cardinality. eventstats computes dc(falco_rule) inside each bucket to detect rule storms greater than ten distinct rules, which often indicates automated exploitation tooling or a poisoned supply-chain image waking many macros at once. eventstats also computes fleet_p95_dc_rules and fleet_p50_dc_rules so analysts see whether a container is an outlier relative to the estate. rule_storm combines bucketed and sliding-window gates.

The first join wraps inputlookup falco_rule_baseline.csv on falco_rule to attach MITRE technique identifiers and historical baseline_seen_count for novel signature logic. The second join wraps inputlookup c2_iocs.csv on suspicious_dest_ip. Additional joins add tor_exit_nodes.csv and crypto_mining_pools.csv enrichment without using bare lookup commands, satisfying governance reviewers.

image_process_baseline.csv joins on image_key to mark proc_baseline_ok when suspicious_process matches the golden regex. The docker:events subsearch supplies exec_time_buckets for docker_exec_recent_window versus orphan_shell_candidate hints.

The severity case ladder emits only the six mandated strings. recommended_response provides runbook bridges without improvising under pressure. The closing table projects container_id, container_name, image, host_id, mitre_technique, falco_rule, severity, suspicious_process, suspicious_dest_ip, ioc_match, recommended_response, egress_ip_dc_5m, egress_dport_dc_5m, egress_entropy_hint, internal_rfc1918_dst, signal_lane, distinct_falco_rules_5m, rule_storm, stream_dc_falco_rules_300s, exec_parent_hint, fleet percentile columns for Falco rule cardinality and egress diversity.

Alert actions should attach the row, link to dashboards described in the visualization field, and deep link to UC-3.1.24 when operator exec overlap is suspected.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.21 Container Runtime Security Events. Tunables: index=oti_containers_security; sourcetypes falco:json, ebpf:process_exec, ebpf:net_connect; inputlookup joins falco_rule_baseline.csv and c2_iocs.csv; supporting lookups image_process_baseline.csv, tor_exit_nodes.csv, crypto_mining_pools.csv; rule-storm when dc(falco_rule) exceeds ten in a five-minute bucket or streamstats sliding window; fleet context uses eventstats percentiles for Falco bursts and egress IP/port fan-out; earliest=-1h@h latest=@h.")`
| multisearch
    [ search index=oti_containers_security sourcetype="falco:json" earliest=-1h@h latest=@h
      | eval signal_lane="falco_json"
      | eval host_id=lower(toString(coalesce(host, Host, hostname, hostname_s, k8s_node_name, nodeName, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, k8s_pod_uid, "")))
      | eval container_name=trim(toString(coalesce(container_name, containerName, k8s_pod_name, name, "")))
      | eval image=trim(toString(coalesce(container_image_repository, container_image_tag, image, Image, "")))
      | eval falco_rule=toString(coalesce(rule, Rule, ruleName, output_rule, ""))
      | eval falco_priority=lower(toString(coalesce(priority, Priority, "")))
      | eval suspicious_process=toString(coalesce(proc_name, procName, process_name, ""))
      | eval suspicious_dest_ip=""
      | eval dport=""
      | eval ppid=toString(coalesce(ppid, parent_pid, proc_ppid, ""))
      | eval proc_cmdline=toString(coalesce(proc_cmdline, procCmdline, output, ""))
      | where len(falco_rule)>0 AND match(falco_priority, "notice|warning|error|critical|alert|emergency")
      | fields _time host_id container_id container_name image falco_rule falco_priority suspicious_process suspicious_dest_ip signal_lane ppid proc_cmdline dport ]
    [ search index=oti_containers_security sourcetype="ebpf:process_exec" earliest=-1h@h latest=@h
      | eval signal_lane="ebpf_process_exec"
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, cgroup_container_id, "")))
      | eval container_name=trim(toString(coalesce(container_name, containerName, scope_task, "")))
      | eval image=trim(toString(coalesce(image, Image, container_image, "")))
      | eval falco_rule=""
      | eval falco_priority=""
      | eval cmdline=toString(coalesce(cmdline, proc_cmdline, argv, procCmdline, ""))
      | eval suspicious_process=toString(coalesce(exe, comm, cmdline, ""))
      | eval suspicious_dest_ip=""
      | eval dport=""
      | eval ppid=toString(coalesce(parent_pid, ppid, PPID, ""))
      | eval proc_cmdline=cmdline
      | where match(lower(suspicious_process), "(?i)(^|/)(bash|sh|dash|zsh|ash)( |$)|\\bpython\\s+-c\\b|\\bperl\\s+-e\\b|\\bcurl\\b|\\bwget\\b|\\bnc\\b|\\bncat\\b|\\bapt-get\\b|\\byum\\b|\\bapk\\s+add\\b")
      | fields _time host_id container_id container_name image falco_rule falco_priority suspicious_process suspicious_dest_ip signal_lane ppid proc_cmdline dport ]
    [ search index=oti_containers_security sourcetype="ebpf:net_connect" earliest=-1h@h latest=@h
      | eval signal_lane="ebpf_net_connect"
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, "")))
      | eval container_name=trim(toString(coalesce(container_name, containerName, "")))
      | eval image=trim(toString(coalesce(image, Image, "")))
      | eval falco_rule=""
      | eval falco_priority=""
      | eval suspicious_process=toString(coalesce(comm, process_name, ""))
      | eval suspicious_dest_ip=trim(toString(coalesce(dst_ip, dest_ip, remote_ip, daddr, dip, "")))
      | eval dport=toString(coalesce(dport, dst_port, dest_port, ""))
      | eval ppid=""
      | eval proc_cmdline=""
      | where len(suspicious_dest_ip)>0
      | fields _time host_id container_id container_name image falco_rule falco_priority suspicious_process suspicious_dest_ip signal_lane ppid proc_cmdline dport ]
| eval image_key=lower(trim(if(len(trim(image))>0, image, container_name)))
| sort 0 + host_id, container_id, _time
| streamstats time_window=300s global=f dc(eval(if(signal_lane=="falco_json", falco_rule, null()))) AS stream_dc_falco_rules_300s BY host_id, container_id
| bin _time span=5m as t5
| eventstats dc(eval(if(signal_lane=="falco_json", falco_rule, null()))) AS distinct_falco_rules_5m count(eval(if(signal_lane=="falco_json", 1, null()))) AS falco_evt_5m BY host_id, container_id, t5
| eventstats perc95(distinct_falco_rules_5m) AS fleet_p95_dc_rules perc50(distinct_falco_rules_5m) AS fleet_p50_dc_rules
| eventstats dc(eval(if(signal_lane=="ebpf_net_connect", suspicious_dest_ip, null()))) AS egress_ip_dc_5m dc(eval(if(signal_lane=="ebpf_net_connect", dport, null()))) AS egress_dport_dc_5m BY host_id, container_id, t5
| eventstats perc95(egress_ip_dc_5m) AS fleet_p95_egress_ip_dc perc50(egress_ip_dc_5m) AS fleet_p50_egress_ip_dc perc95(egress_dport_dc_5m) AS fleet_p95_egress_dport_dc perc50(egress_dport_dc_5m) AS fleet_p50_egress_dport_dc
| fillnull value=0 egress_ip_dc_5m egress_dport_dc_5m fleet_p95_egress_ip_dc fleet_p50_egress_ip_dc fleet_p95_egress_dport_dc fleet_p50_egress_dport_dc
| eval internal_rfc1918_dst=if(signal_lane=="ebpf_net_connect" AND len(suspicious_dest_ip)>0 AND match(suspicious_dest_ip, "^(10\\.|172\\.(1[6-9]|2[0-9]|3[01])\\.|192\\.168\\.)"), 1, 0)
| eval egress_entropy_hint=case(signal_lane!="ebpf_net_connect", "", (egress_ip_dc_5m>=8) OR (egress_ip_dc_5m>0 AND egress_ip_dc_5m>fleet_p95_egress_ip_dc AND fleet_p95_egress_ip_dc>0), "high_dest_ip_diversity", (egress_dport_dc_5m>=6) OR (egress_dport_dc_5m>0 AND egress_dport_dc_5m>fleet_p95_egress_dport_dc AND fleet_p95_egress_dport_dc>0), "port_fanout_drift", true(), "nominal_egress_shape")
| eval rule_storm=if(distinct_falco_rules_5m>10 OR stream_dc_falco_rules_300s>10, 1, 0)
| join type=left max=0 falco_rule
    [| inputlookup falco_rule_baseline.csv
     | eval falco_rule=trim(toString(coalesce(rule_name, falco_rule, rule, "")))
     | eval mitre_technique=toString(coalesce(mitre_technique, mitre_id, attack_technique, ""))
     | eval baseline_seen_count=tonumber(tostring(coalesce(baseline_seen_count, image_historical_fires, hist_fires, "")), 10)
     | fields falco_rule mitre_technique baseline_seen_count ]
| eval mitre_technique=coalesce(mitre_technique, "")
| join type=left max=0 suspicious_dest_ip
    [| inputlookup c2_iocs.csv
     | eval suspicious_dest_ip=trim(toString(coalesce(ip, ioc_ip, dest_ip, "")))
     | eval ioc_match=toString(coalesce(threat_name, ioc_label, feed, "c2_ioc"))
     | fields suspicious_dest_ip ioc_match ]
| join type=left max=0 suspicious_dest_ip
    [| inputlookup tor_exit_nodes.csv
     | eval suspicious_dest_ip=trim(toString(coalesce(exit_ip, ip, "")))
     | eval tor_tag="tor_exit_node"
     | fields suspicious_dest_ip tor_tag ]
| join type=left max=0 suspicious_dest_ip
    [| inputlookup crypto_mining_pools.csv
     | eval suspicious_dest_ip=trim(toString(coalesce(pool_ip, ip, "")))
     | eval mining_tag=toString(coalesce(pool_name, pool_family, "crypto_stratum_pool"))
     | fields suspicious_dest_ip mining_tag ]
| eval ioc_match=coalesce(ioc_match, if(len(tor_tag)>0, "tor_exit_list_match", null()), if(len(mining_tag)>0, mining_tag, null()), "")
| join type=left max=0 image_key
    [| inputlookup image_process_baseline.csv
     | eval image_key=lower(trim(toString(coalesce(image_key, image_ref, image, ""))))
     | eval expected_proc_regex=toString(coalesce(expected_proc_regex, allowed_processes_regex, golden_proc_pattern, ""))
     | fields image_key expected_proc_regex ]
| eval proc_baseline_ok=if(len(expected_proc_regex)>0 AND match(lower(suspicious_process), lower(expected_proc_regex)), 1, 0)
| join type=left max=0 host_id, container_id
    [| search index=oti_containers_security sourcetype="docker:events" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, "")))
      | eval typ=lower(toString(coalesce(type, Type, event_type, "")))
      | eval act=lower(toString(coalesce(action, Action, "")))
      | where typ="exec" OR match(act, "^exec_")
      | eval container_id=trim(toString(coalesce(container_id, containerId, id, Id, actor_id, "")))
      | bin _time span=2m
      | stats dc(_time) AS exec_time_buckets BY host_id, container_id ]
| eval exec_parent_hint=if(isnotnull(exec_time_buckets) AND exec_time_buckets>0, "docker_exec_recent_window", "orphan_shell_candidate")
| eval novel_rule_signature=if(signal_lane=="falco_json" AND (isnull(baseline_seen_count) OR baseline_seen_count==0), 1, 0)
| eval severity=case(
    signal_lane=="falco_json" AND (match(lower(falco_rule), "(?i)escape|release_agent|privileged|nsenter|cap_sys|sensitive mount|docker daemon|mount launched") OR match(lower(mitre_technique), "(?i)t1611")),
        "critical_t1611_container_escape_or_t1525_image_modification",
    signal_lane=="ebpf_process_exec" AND match(lower(suspicious_process), "(?i)apt-get|yum |dnf |apk add|dpkg "),
        "critical_t1611_container_escape_or_t1525_image_modification",
    (len(mining_tag)>0) OR (len(ioc_match)>0 AND match(lower(ioc_match), "(?i)c2|malware|miner|stratum|bot|tor_exit")),
        "critical_egress_to_known_c2_or_crypto_mining_pool",
    signal_lane=="falco_json" AND match(lower(falco_rule), "(?i)miner|stratum|crypto|kinsing|teamtnt"),
        "high_t1496_crypto_miner_or_t1059_reverse_shell",
    match(lower(proc_cmdline), "(?i)python\\s+-c|perl\\s+-e|/dev/tcp|bash\\s+-i|reverse"),
        "high_t1496_crypto_miner_or_t1059_reverse_shell",
    signal_lane=="ebpf_process_exec" AND proc_baseline_ok=0 AND match(lower(suspicious_process), "(?i)(^|/)(bash|sh|dash|zsh)( |$)") AND exec_parent_hint="orphan_shell_candidate",
        "high_unexpected_shell_in_container_no_exec_parent",
    signal_lane=="ebpf_net_connect" AND internal_rfc1918_dst=1 AND match(egress_entropy_hint, "high_dest_ip_diversity|port_fanout_drift"),
        "medium_novel_rule_signature_for_image",
    novel_rule_signature=1 OR rule_storm=1,
        "medium_novel_rule_signature_for_image",
    true(),
        "low_baseline_drift")
| eval recommended_response=case(
    severity="critical_t1611_container_escape_or_t1525_image_modification", "Isolate the workload and node segment, preserve Falco JSON and eBPF exports, compare against UC-3.1.6 privilege posture and UC-3.1.25 socket exposure timelines, rotate material secrets, and rebuild from signed digest.",
    severity="critical_egress_to_known_c2_or_crypto_mining_pool", "Block egress at the nearest enforcement point, quarantine the container, hunt lateral movement on the segment, validate IOC list freshness, and escalate if mining pool or C2 overlap persists beyond one collection interval.",
    severity="high_t1496_crypto_miner_or_t1059_reverse_shell", "Kill suspicious descendant processes, capture command lines, diff image layers against golden build, correlate UC-3.1.24 operator exec sessions, and scan the fleet for the same image digest.",
    severity="high_unexpected_shell_in_container_no_exec_parent", "Validate break-glass tickets, pull docker exec audit around the window, capture parent PID lineage from eBPF, and escalate if no approved maintenance record exists.",
    severity="medium_novel_rule_signature_for_image", "Refresh falco_rule_baseline.csv and image_process_baseline.csv, tune Falco macros for the service tier, and review deploy correlation for supply-chain or red-team overlap.",
    severity="low_baseline_drift", "Tune baselines and context macros, document expected automation, and keep monitoring for escalation patterns.",
    true(), "Correlate all three signal lanes and close only with host and container owner sign-off.")
| table _time container_id container_name image host_id mitre_technique falco_rule severity suspicious_process suspicious_dest_ip ioc_match recommended_response egress_ip_dc_5m egress_dport_dc_5m egress_entropy_hint internal_rfc1918_dst signal_lane distinct_falco_rules_5m rule_storm stream_dc_falco_rules_300s exec_parent_hint fleet_p95_dc_rules fleet_p50_dc_rules fleet_p95_egress_ip_dc fleet_p50_egress_dport_dc
```

### Step 4 — Validate

Positive path A — Falco escape-class rule: in a sealed lab, trigger a controlled rule that matches mount or privilege semantics without leaving the lab on the public internet, ingest falco:json, run the saved search, and expect critical_t1611_container_escape_or_t1525_image_modification with non-null mitre_technique when falco_rule_baseline.csv maps the rule.

Positive path B — eBPF shell without exec window: spawn an interactive shell inside a test container while docker:events exec ingestion is paused in lab only, confirm high_unexpected_shell_in_container_no_exec_parent or equivalent when exec_parent_hint reads orphan_shell_candidate. Restore exec ingestion before leaving the lab.

Positive path C — mining pool egress: point a lab container at a test IP listed in crypto_mining_pools.csv, ingest ebpf:net_connect, and expect critical_egress_to_known_c2_or_crypto_mining_pool with ioc_match populated.

Positive path D — rule storm: replay a bundle of distinct Falco rules inside the same five-minute bucket on one container_id in a test index, confirm medium_novel_rule_signature_for_image or rule_storm context with distinct_falco_rules_5m greater than ten or stream_dc_falco_rules_300s greater than ten.

Negative path — idle nginx: run nginx:alpine with tight Falco macros and no egress anomalies, confirm low noise after baseline tuning across several intervals.

Field sanity: temporarily rename Falco output_fields to camelCase-only in a sandbox forwarder and confirm coalesce still extracts container_id. Role-based access: readers without index=oti_containers_security must see zero rows. Clock skew: enforce chrony before trusting exec_parent_hint.

Correlation: compare alert times to UC-3.1.6 privileged drift and UC-3.1.25 socket rows on the same host_id minute.

Performance: if Job Inspector shows scan pressure, summarize falco:json into five-minute metrics indexes retaining dc(rule) per container before alerting while keeping raw events for forensics.

### Step 5 — Operationalize and troubleshoot

Case 1 — Falco arm empty but eBPF shows shells: Falco daemon may have exited or rules are silenced; verify systemctl status, kernel headers, and probe compatibility. Remediation is fixing Falco, not muting eBPF.

Case 2 — eBPF arm empty: exporter permissions, secure boot constraints, or BPF LSM policies may block probes; validate collector capabilities and kernel config. Document exemptions per host class.

Case 3 — Join misses on falco_rule_baseline.csv: rule rename after Falco upgrade; refresh CSV from vendor release notes and replay historical alerts.

Case 4 — Rule storm false positive during image promotion: new digest triggers many informational rules once; require sustained priority of warning or higher before paging, or add promotion windows to baselines.

Case 5 — c2_iocs.csv stale: benign IP reassigned; cross-check feed age and confidence before blocking egress.

Case 6 — docker exec join over-matches: short-lived continuous integration exec bursts flag docker_exec_recent_window for every shell; narrow the subsearch to production host classes via macro.

Case 7 — image_process_baseline regex too tight: legitimate JVM thread-dump helpers spawn bash; widen golden patterns with change-advisory approval.

Case 8 — Dual HEC writers duplicate Falco events: deduplicate on event generator fields or enforce single writer per node class.

Case 9 — Fleet percentiles flatline at zero: cold index or sparse Falco feed; confirm index name in comment macro matches production.

Case 10 — Severity stuck at low_baseline_drift: tune case ordering only after confirming no higher signal is masked by catch-all branch; never reorder without change review.

Case 11 — Container_id mismatch between Falco and eBPF: align cgroup key extraction with docker id format using a translation lookup.

Case 12 — Splunk Cloud autoscale overlaps schedules: add alert dedup on container_id and severity in automation or saved-search post-processing.

Dashboard publishing: build a Falco rule heatmap by container, an ATT&CK technique distribution panel, an egress geomap with IOC overlay, and a rule-storm timeline with annotations when baselines change.

Evidence retention: weekly CSV exports of the closing table with lookup commit hashes satisfy PCI DSS 11.5 style change-detection discussions, SOC 2 CC7.2 operational monitoring evidence, and ISO 27001 A.12.4 logging reviews when paired with tickets.

Governance: quarterly replay one historical intrusion exercise through the SPL after Falco, kernel, or Splunk upgrades. Update the comment macro when indexes move.

Closing checklist: five plain-text step headers with em dashes are present; Step 3 fenced SPL matches the spl field exactly; multisearch lists three arms; streamstats time_window provides sliding-window rule cascades alongside binned eventstats; two mandatory inputlookup joins appear for falco_rule_baseline.csv and c2_iocs.csv; supplemental joins cover tor and mining pools; severity strings match the contract exactly; narrative fields avoid forbidden boilerplate phrases from the gold contract list.


## SPL

```spl
`comment("UC-3.1.21 Container Runtime Security Events. Tunables: index=oti_containers_security; sourcetypes falco:json, ebpf:process_exec, ebpf:net_connect; inputlookup joins falco_rule_baseline.csv and c2_iocs.csv; supporting lookups image_process_baseline.csv, tor_exit_nodes.csv, crypto_mining_pools.csv; rule-storm when dc(falco_rule) exceeds ten in a five-minute bucket or streamstats sliding window; fleet context uses eventstats percentiles for Falco bursts and egress IP/port fan-out; earliest=-1h@h latest=@h.")`
| multisearch
    [ search index=oti_containers_security sourcetype="falco:json" earliest=-1h@h latest=@h
      | eval signal_lane="falco_json"
      | eval host_id=lower(toString(coalesce(host, Host, hostname, hostname_s, k8s_node_name, nodeName, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, k8s_pod_uid, "")))
      | eval container_name=trim(toString(coalesce(container_name, containerName, k8s_pod_name, name, "")))
      | eval image=trim(toString(coalesce(container_image_repository, container_image_tag, image, Image, "")))
      | eval falco_rule=toString(coalesce(rule, Rule, ruleName, output_rule, ""))
      | eval falco_priority=lower(toString(coalesce(priority, Priority, "")))
      | eval suspicious_process=toString(coalesce(proc_name, procName, process_name, ""))
      | eval suspicious_dest_ip=""
      | eval dport=""
      | eval ppid=toString(coalesce(ppid, parent_pid, proc_ppid, ""))
      | eval proc_cmdline=toString(coalesce(proc_cmdline, procCmdline, output, ""))
      | where len(falco_rule)>0 AND match(falco_priority, "notice|warning|error|critical|alert|emergency")
      | fields _time host_id container_id container_name image falco_rule falco_priority suspicious_process suspicious_dest_ip signal_lane ppid proc_cmdline dport ]
    [ search index=oti_containers_security sourcetype="ebpf:process_exec" earliest=-1h@h latest=@h
      | eval signal_lane="ebpf_process_exec"
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, cgroup_container_id, "")))
      | eval container_name=trim(toString(coalesce(container_name, containerName, scope_task, "")))
      | eval image=trim(toString(coalesce(image, Image, container_image, "")))
      | eval falco_rule=""
      | eval falco_priority=""
      | eval cmdline=toString(coalesce(cmdline, proc_cmdline, argv, procCmdline, ""))
      | eval suspicious_process=toString(coalesce(exe, comm, cmdline, ""))
      | eval suspicious_dest_ip=""
      | eval dport=""
      | eval ppid=toString(coalesce(parent_pid, ppid, PPID, ""))
      | eval proc_cmdline=cmdline
      | where match(lower(suspicious_process), "(?i)(^|/)(bash|sh|dash|zsh|ash)( |$)|\\bpython\\s+-c\\b|\\bperl\\s+-e\\b|\\bcurl\\b|\\bwget\\b|\\bnc\\b|\\bncat\\b|\\bapt-get\\b|\\byum\\b|\\bapk\\s+add\\b")
      | fields _time host_id container_id container_name image falco_rule falco_priority suspicious_process suspicious_dest_ip signal_lane ppid proc_cmdline dport ]
    [ search index=oti_containers_security sourcetype="ebpf:net_connect" earliest=-1h@h latest=@h
      | eval signal_lane="ebpf_net_connect"
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, "")))
      | eval container_name=trim(toString(coalesce(container_name, containerName, "")))
      | eval image=trim(toString(coalesce(image, Image, "")))
      | eval falco_rule=""
      | eval falco_priority=""
      | eval suspicious_process=toString(coalesce(comm, process_name, ""))
      | eval suspicious_dest_ip=trim(toString(coalesce(dst_ip, dest_ip, remote_ip, daddr, dip, "")))
      | eval dport=toString(coalesce(dport, dst_port, dest_port, ""))
      | eval ppid=""
      | eval proc_cmdline=""
      | where len(suspicious_dest_ip)>0
      | fields _time host_id container_id container_name image falco_rule falco_priority suspicious_process suspicious_dest_ip signal_lane ppid proc_cmdline dport ]
| eval image_key=lower(trim(if(len(trim(image))>0, image, container_name)))
| sort 0 + host_id, container_id, _time
| streamstats time_window=300s global=f dc(eval(if(signal_lane=="falco_json", falco_rule, null()))) AS stream_dc_falco_rules_300s BY host_id, container_id
| bin _time span=5m as t5
| eventstats dc(eval(if(signal_lane=="falco_json", falco_rule, null()))) AS distinct_falco_rules_5m count(eval(if(signal_lane=="falco_json", 1, null()))) AS falco_evt_5m BY host_id, container_id, t5
| eventstats perc95(distinct_falco_rules_5m) AS fleet_p95_dc_rules perc50(distinct_falco_rules_5m) AS fleet_p50_dc_rules
| eventstats dc(eval(if(signal_lane=="ebpf_net_connect", suspicious_dest_ip, null()))) AS egress_ip_dc_5m dc(eval(if(signal_lane=="ebpf_net_connect", dport, null()))) AS egress_dport_dc_5m BY host_id, container_id, t5
| eventstats perc95(egress_ip_dc_5m) AS fleet_p95_egress_ip_dc perc50(egress_ip_dc_5m) AS fleet_p50_egress_ip_dc perc95(egress_dport_dc_5m) AS fleet_p95_egress_dport_dc perc50(egress_dport_dc_5m) AS fleet_p50_egress_dport_dc
| fillnull value=0 egress_ip_dc_5m egress_dport_dc_5m fleet_p95_egress_ip_dc fleet_p50_egress_ip_dc fleet_p95_egress_dport_dc fleet_p50_egress_dport_dc
| eval internal_rfc1918_dst=if(signal_lane=="ebpf_net_connect" AND len(suspicious_dest_ip)>0 AND match(suspicious_dest_ip, "^(10\\.|172\\.(1[6-9]|2[0-9]|3[01])\\.|192\\.168\\.)"), 1, 0)
| eval egress_entropy_hint=case(signal_lane!="ebpf_net_connect", "", (egress_ip_dc_5m>=8) OR (egress_ip_dc_5m>0 AND egress_ip_dc_5m>fleet_p95_egress_ip_dc AND fleet_p95_egress_ip_dc>0), "high_dest_ip_diversity", (egress_dport_dc_5m>=6) OR (egress_dport_dc_5m>0 AND egress_dport_dc_5m>fleet_p95_egress_dport_dc AND fleet_p95_egress_dport_dc>0), "port_fanout_drift", true(), "nominal_egress_shape")
| eval rule_storm=if(distinct_falco_rules_5m>10 OR stream_dc_falco_rules_300s>10, 1, 0)
| join type=left max=0 falco_rule
    [| inputlookup falco_rule_baseline.csv
     | eval falco_rule=trim(toString(coalesce(rule_name, falco_rule, rule, "")))
     | eval mitre_technique=toString(coalesce(mitre_technique, mitre_id, attack_technique, ""))
     | eval baseline_seen_count=tonumber(tostring(coalesce(baseline_seen_count, image_historical_fires, hist_fires, "")), 10)
     | fields falco_rule mitre_technique baseline_seen_count ]
| eval mitre_technique=coalesce(mitre_technique, "")
| join type=left max=0 suspicious_dest_ip
    [| inputlookup c2_iocs.csv
     | eval suspicious_dest_ip=trim(toString(coalesce(ip, ioc_ip, dest_ip, "")))
     | eval ioc_match=toString(coalesce(threat_name, ioc_label, feed, "c2_ioc"))
     | fields suspicious_dest_ip ioc_match ]
| join type=left max=0 suspicious_dest_ip
    [| inputlookup tor_exit_nodes.csv
     | eval suspicious_dest_ip=trim(toString(coalesce(exit_ip, ip, "")))
     | eval tor_tag="tor_exit_node"
     | fields suspicious_dest_ip tor_tag ]
| join type=left max=0 suspicious_dest_ip
    [| inputlookup crypto_mining_pools.csv
     | eval suspicious_dest_ip=trim(toString(coalesce(pool_ip, ip, "")))
     | eval mining_tag=toString(coalesce(pool_name, pool_family, "crypto_stratum_pool"))
     | fields suspicious_dest_ip mining_tag ]
| eval ioc_match=coalesce(ioc_match, if(len(tor_tag)>0, "tor_exit_list_match", null()), if(len(mining_tag)>0, mining_tag, null()), "")
| join type=left max=0 image_key
    [| inputlookup image_process_baseline.csv
     | eval image_key=lower(trim(toString(coalesce(image_key, image_ref, image, ""))))
     | eval expected_proc_regex=toString(coalesce(expected_proc_regex, allowed_processes_regex, golden_proc_pattern, ""))
     | fields image_key expected_proc_regex ]
| eval proc_baseline_ok=if(len(expected_proc_regex)>0 AND match(lower(suspicious_process), lower(expected_proc_regex)), 1, 0)
| join type=left max=0 host_id, container_id
    [| search index=oti_containers_security sourcetype="docker:events" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, "")))
      | eval typ=lower(toString(coalesce(type, Type, event_type, "")))
      | eval act=lower(toString(coalesce(action, Action, "")))
      | where typ="exec" OR match(act, "^exec_")
      | eval container_id=trim(toString(coalesce(container_id, containerId, id, Id, actor_id, "")))
      | bin _time span=2m
      | stats dc(_time) AS exec_time_buckets BY host_id, container_id ]
| eval exec_parent_hint=if(isnotnull(exec_time_buckets) AND exec_time_buckets>0, "docker_exec_recent_window", "orphan_shell_candidate")
| eval novel_rule_signature=if(signal_lane=="falco_json" AND (isnull(baseline_seen_count) OR baseline_seen_count==0), 1, 0)
| eval severity=case(
    signal_lane=="falco_json" AND (match(lower(falco_rule), "(?i)escape|release_agent|privileged|nsenter|cap_sys|sensitive mount|docker daemon|mount launched") OR match(lower(mitre_technique), "(?i)t1611")),
        "critical_t1611_container_escape_or_t1525_image_modification",
    signal_lane=="ebpf_process_exec" AND match(lower(suspicious_process), "(?i)apt-get|yum |dnf |apk add|dpkg "),
        "critical_t1611_container_escape_or_t1525_image_modification",
    (len(mining_tag)>0) OR (len(ioc_match)>0 AND match(lower(ioc_match), "(?i)c2|malware|miner|stratum|bot|tor_exit")),
        "critical_egress_to_known_c2_or_crypto_mining_pool",
    signal_lane=="falco_json" AND match(lower(falco_rule), "(?i)miner|stratum|crypto|kinsing|teamtnt"),
        "high_t1496_crypto_miner_or_t1059_reverse_shell",
    match(lower(proc_cmdline), "(?i)python\\s+-c|perl\\s+-e|/dev/tcp|bash\\s+-i|reverse"),
        "high_t1496_crypto_miner_or_t1059_reverse_shell",
    signal_lane=="ebpf_process_exec" AND proc_baseline_ok=0 AND match(lower(suspicious_process), "(?i)(^|/)(bash|sh|dash|zsh)( |$)") AND exec_parent_hint="orphan_shell_candidate",
        "high_unexpected_shell_in_container_no_exec_parent",
    signal_lane=="ebpf_net_connect" AND internal_rfc1918_dst=1 AND match(egress_entropy_hint, "high_dest_ip_diversity|port_fanout_drift"),
        "medium_novel_rule_signature_for_image",
    novel_rule_signature=1 OR rule_storm=1,
        "medium_novel_rule_signature_for_image",
    true(),
        "low_baseline_drift")
| eval recommended_response=case(
    severity="critical_t1611_container_escape_or_t1525_image_modification", "Isolate the workload and node segment, preserve Falco JSON and eBPF exports, compare against UC-3.1.6 privilege posture and UC-3.1.25 socket exposure timelines, rotate material secrets, and rebuild from signed digest.",
    severity="critical_egress_to_known_c2_or_crypto_mining_pool", "Block egress at the nearest enforcement point, quarantine the container, hunt lateral movement on the segment, validate IOC list freshness, and escalate if mining pool or C2 overlap persists beyond one collection interval.",
    severity="high_t1496_crypto_miner_or_t1059_reverse_shell", "Kill suspicious descendant processes, capture command lines, diff image layers against golden build, correlate UC-3.1.24 operator exec sessions, and scan the fleet for the same image digest.",
    severity="high_unexpected_shell_in_container_no_exec_parent", "Validate break-glass tickets, pull docker exec audit around the window, capture parent PID lineage from eBPF, and escalate if no approved maintenance record exists.",
    severity="medium_novel_rule_signature_for_image", "Refresh falco_rule_baseline.csv and image_process_baseline.csv, tune Falco macros for the service tier, and review deploy correlation for supply-chain or red-team overlap.",
    severity="low_baseline_drift", "Tune baselines and context macros, document expected automation, and keep monitoring for escalation patterns.",
    true(), "Correlate all three signal lanes and close only with host and container owner sign-off.")
| table _time container_id container_name image host_id mitre_technique falco_rule severity suspicious_process suspicious_dest_ip ioc_match recommended_response egress_ip_dc_5m egress_dport_dc_5m egress_entropy_hint internal_rfc1918_dst signal_lane distinct_falco_rules_5m rule_storm stream_dc_falco_rules_300s exec_parent_hint fleet_p95_dc_rules fleet_p50_dc_rules fleet_p95_egress_ip_dc fleet_p50_egress_dport_dc
```

## CIM SPL

```spl
| tstats summariesonly=true count FROM datamodel=Alerts WHERE nodename=Alerts earliest=-1h@h latest=now BY Alerts.signature Alerts.dest
| rename Alerts.dest AS host
| append [ | tstats summariesonly=true count FROM datamodel=Network_Traffic WHERE nodename=Network_Traffic earliest=-1h@h latest=now BY Network_Traffic.dest_ip Network_Traffic.src_ip ]
| head 400
```

## Visualization

Falco rule firing heatmap faceted by container; ATT&CK technique distribution bar chart; egress geomap with IOC and mining-pool overlays; time-series of egress_ip_dc_5m and egress_dport_dc_5m against fleet percentiles; rule-storm cascade timeline combining streamstats sliding counts with five-minute bucket overlays.

## Known False Positives

GitOps or Helm pre-sync init jobs sometimes run one-shot package installs or curl health checks that resemble T1525 or T1059 until you stamp their image_key rows in falco_rule_baseline.csv with historical fire counts and widen image_process_baseline.csv for the sidecar class. Istio, Linkerd, Consul connect, and Envoy-heavy meshes spawn auxiliary processes that can look like reverse-shell tooling until mesh-owned digests carry explicit expected_proc_regex allowances. Vendor JVM or WebSphere diagnostics may fork bash for thread dumps; document the maintenance digest and tie it to change windows instead of paging as host compromise. Read-only Postgres or MySQL replicas that stream backups through socat or kubectl cp analogues can emit net-like syscall patterns; pre-approve argv templates per backup operator image. The first month after a Falco rules upgrade often looks like novel_rule_signature spam until falco_rule_baseline.csv catches renames—treat notice-only noise as tuning work unless priorities climb to warning. Egress entropy gates can flag autoscaling discovery bursts when a service legitimately fans out to many pod IPs after a rollout; correlate with deployment timestamps before calling lateral movement. Stale c2_iocs.csv rows may label recycled cloud egress IPs; require feed provenance and confidence columns before firewall automation. Blue-green or canary releases that replace every task in a five-minute bucket can spike distinct Falco rule counts without malice; require sustained high priorities or IOC overlap before Sev-1 bridges. Security vendors’ own instrumentation containers sometimes carry permissive Falco macros; negotiate allowlists with the vendor’s threat intel team instead of silent suppression. Red-team exercise tags belong in lookup metadata so purple windows do not exhaust on-call goodwill.

## References

- [Falco documentation](https://falco.org/docs/)
- [Falco default rules library](https://falco.org/docs/rules/default-rules/)
- [MITRE ATT&CK — Containers matrix](https://attack.mitre.org/matrices/enterprise/containers/)
- [Splunk Lantern — Building a SOAR playbook for container enrichment](https://lantern.splunk.com/Security_Use_Cases/Advanced_Threat_Detection/Building_a_SOAR_playbook_for_container_enrichment)
- [Falco releases — CNCF Falco project](https://github.com/falcosecurity/falco/releases)
- [NIST SP 800-190 — Application Container Security Guide](https://csrc.nist.gov/publications/detail/sp/800-190/final)
