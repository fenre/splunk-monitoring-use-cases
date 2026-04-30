<!-- AUTO-GENERATED from UC-3.1.25.json — DO NOT EDIT -->

---
id: "3.1.25"
title: "Docker Socket Exposure Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.1.25 · Docker Socket Exposure Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for little boxes that secretly carry the host’s master key through a shared socket hole, and we watch for the front door of the Docker service being left open on the network. When either happens without paperwork, we raise a loud alarm so strangers cannot drive the whole machine.*

---

## Description

This control correlates three independent evidence families that attackers routinely chain to break out of Docker namespaces: declarative bind mounts that place the Docker control socket inside a container namespace, host audit telemetry that reveals dockerd listening on wide-area TCP without modern TLS protections, and Falco runtime alerts that observe connect syscalls or policy hits against sensitive unix sockets. Once a workload holds docker.sock, it can schedule privileged siblings, bind the host root filesystem, harvest secrets from other containers, pivot toward Kubernetes API servers on adjacent RFC1918 segments, or exfiltrate images and volumes without touching SSH. Plaintext 2375 removes even the Unix permission model that guards the local socket. The Splunk pipeline keeps inspect truth, event-stream hints, audit configuration drift, and live syscall-grade alerts in one analyst view so a Fortune 500 SOC can decide within minutes whether a mount is an approved automation artifact or an active escape attempt.

## Value

Quantifying mean time to detect a docker.sock or plaintext daemon exposure in minutes instead of weeks directly reduces expected loss from cryptojacking, data ransom, and regulator notification triggers; industry incidents such as the 2018 Tesla cloud breach illustrated how an open Engine API becomes an unpaid compute farm within hours. Privileged-container incident response often exceeds six figures in forensics alone, while automated detection with immutable HEC evidence costs a rounding error in license bytes. Boards and customers increasingly ask for SOC2, ISO 27001, and PCI DSS proof that container escape surfaces are monitored; this UC produces timestamped rows tied to change tickets and allowlist governance, shrinking audit preparation cycles. The asymmetry is stark: one missed socket mount can equal an entire quarter of Splunk ingest spend in breach response, so instrumenting the control is rational even on conservative FinOps teams.

## Implementation

Deploy inspect and events feeds into index=containers, linux_secure or audit:json into index=os, and Falco JSON into index=containers with sourcetype falco:alert. Publish docker_socket_allowlist and container_owner lookups with lowercase host keys. Save container_uc_3_1_25_docker_socket_exposure on a five- or fifteen-minute cadence over earliest=-4h@h latest=@h, route critical socket and 2375 rows to platform secops jointly, archive weekly CSV snapshots with ticket ids, and keep the comment macro synchronized with index names your security office approves.

## Evidence

Saved search container_uc_3_1_25_docker_socket_exposure, docker_socket_allowlist KV or CSV with change ticket hashes, weekly exports to a restricted evidence index, dashboard drilldowns on docker:inspect Mounts and falco:alert payloads, and mapping worksheets aligned to CIS Docker Benchmark control 5.31 on not mounting the Docker socket into containers. Public breach literature includes the 2018 Tesla cloud incident where an exposed administrative Docker daemon was abused for cryptomining, illustrating why plaintext Engine APIs demand instant response. Threat research from Sysdig and Anchore routinely flags docker.sock as a top-tier breakout primitive, consistent with MITRE ATT&CK technique T1611 Escape to Host narratives.

## Control test

### Positive scenario

On a lab Linux host mount /var/run/docker.sock into a throwaway alpine container without an allowlist row, ingest docker:inspect and docker:events into index=containers, run container_uc_3_1_25_docker_socket_exposure, and expect critical_socket_mount_unapproved with allowlist_state unlisted and non-null recommended_response.

### Negative scenario

Add a matching docker_socket_allowlist entry with aligned expected_container_id and allowed_image_regex, redeploy only the approved Portainer image, verify inspect shows the socket mount, and confirm the saved search emits no qualifying row after the join because exit_vector_severity evaluates null for clean approvals.

## Detailed Implementation

### Step 1 — Prerequisites

Platform security and container infrastructure share accountability for this control. Before you ingest a single event, confirm who may legally touch docker.sock on collectors, who owns the Splunk heavy forwarder that runs scripted inspect, and who maintains the Falco policy bundle. The control assumes Linux dockerd hosts in production, not Windows containers, and not fully abstracted serverless runtimes where operators never see Engine APIs. You need a change-approved index route: hot data in index=containers for docker:inspect, docker:events, and falco:alert; host hardening telemetry in index=os for linux_secure or audit:json lines that capture process executions, file integrity on /etc/docker/daemon.json, and systemd unit drops for docker.service. Roles must separate SOC analysts who may read Falco details from developers who should not see production socket allowlists unless they are on-call.

Build two governance lookups under the same app that hosts the saved search. docker_socket_allowlist stores one row per approved socket consumer with columns host_id (lowercase hostname as Universal Forwarders emit it), container_name (exact docker name including Compose prefixes if that is how events name the task), approved_reason (free text ticket pointer), expected_container_id (optional twelve plus character id for drift detection), and allowed_image_regex (a Splunk-compatible PCRE substring match against image_ref). container_owner.csv mirrors UC-3.1.x patterns with host, container_name, owner_team; the SPL renames host to host_id inside joins. If you store allowlist in KV Store collections, expose it through transforms.conf as docker_socket_allowlist so inputlookup still works in Cloud.

Falco must ship JSON alerts to Splunk via HEC or a lightweight forwarder with sourcetype falco:alert. Confirm your Falco version still maps Container with sensitive mount and Detect docker socket access from container into stable rule strings; when vendors rename macros, update the Falco arm filter in a comment macro rather than silently dropping detections. Optional Splunk Add-on for Sysmon for Linux enriches linux_secure with process lineage when dockerd is relaunched with dangerous flags; treat it as additive, not a replacement for auditd rules that watch daemon.json.

Risk context you should brief executives once: mounting the Docker socket into a workload is functionally equivalent to handing that workload an unconstrained root capability on the host because the Engine API can create privileged containers with host bind mounts and host networking. TCP listeners on 2375 remove Unix permission gates entirely. This is why the severity ladder reserves critical for plaintext 2375 and unapproved mounts.

Differentiation: UC-3.1.1 through UC-3.1.13 track reliability signals such as crash cadence, cgroup OOM, and restart back-off. This UC is pure escape-surface monitoring aligned to MITRE ATT&CK T1611 style outcomes. Do not merge reliability thresholds here.

Licensing: inspect snapshots are larger than events-only feeds; schedule them five to fifteen minutes apart on busy CI hosts and hourly on static production nodes unless your SO mandates faster drift detection.

### Step 2 — Configure data collection

Bind-mount telemetry begins with a privileged scripted input or systemd timer on each docker host that runs docker inspect for every running container id and posts one JSON event per container to HEC with sourcetype docker:inspect. Normalize host_id to the same short name your forwarders use. Include Mounts arrays verbatim so Splunk spath can expand Source paths. Where scripted inputs are politically difficult, complement with docker:events streams from Splunk Connect for Docker or an equivalent modular input reading unix:///var/run/docker.sock; tune filters so create and mount-related lines remain visible when the daemon logs volume mounts in the event payload.

For docker:events, enable the Docker Events modular input with the same socket security model you expect in production. Validate that action attributes survive for container create and exec patterns that mention mount destinations. When events omit explicit paths but you still need coverage, increase inspect frequency rather than muting the UC.

Daemon TCP exposure telemetry relies on host audit pipelines. With auditd, add rules that log execve of dockerd, edits to /etc/docker/daemon.json, and writes under /etc/systemd/system/docker.service.d. Ingest those lines as linux_secure or audit:json depending on your Splunk Add-on for Unix and Linux configuration. Where file integrity monitoring already lands unix_filemonitor events for daemon.json, add that sourcetype as a fifth multisearch arm in a follow-on macro if your search head capacity allows; the baseline SPL focuses on linux_secure and audit:json because they usually carry dockerd argv.

Falco runtime alerts should include container_id, container_image_repository, k8s_pod_name when Kubernetes wraps Docker, output_fields for file descriptors, and proc_cmdline for the process that touched the socket. Point Falco at the same cgroup and container metadata your CRI provides; mixed containerd-only nodes may need a distinct UC.

Security hygiene for collectors: the account that reads docker.sock to emit inspect or events must not be the same interactive user developers use on laptops. Store secrets in vault, rotate HEC tokens quarterly, and document Mirantis Container Runtime versus Docker CE field deltas in props.conf so coalesce lists stay short.

Expected validation queries before saving the alert: index=containers sourcetype=docker:inspect earliest=-15m with spath Mounts, index=containers sourcetype=falco:alert rule=*socket*, index=os sourcetype=linux_secure dockerd earliest=-24h. Expect sub-minute skew between host clock and Splunk _time; larger skew breaks streamstats ordering.

### Step 3 — Create search and alert

Save the SPL as container_uc_3_1_25_docker_socket_exposure with schedule */15 * * * * or */5 * * * * during incident response, using earliest=-4h@h latest=@h so allowlist joins see recent container churn without scanning a full day every run. Throttle duplicate critical rows per host_id and exit_vector_severity for forty-five minutes except when signal_burst_count jumps by more than three in an hour, which often indicates automated exploitation scans.

Understanding the pipeline in operator terms: the opening comment macro is the contract for index names, lookup paths, and time windows. multisearch fans four arms so a silent failure in one vendor path does not blank the others. The inspect arm expands Mounts and keeps only sources that end with docker.sock semantics. The events arm catches raw strings your inspect poller might miss when short-lived CI tasks die between samples. The audit arm surfaces daemon-level misconfiguration that no container introspection will ever see. The Falco arm proves runtime connect syscalls or policy violations even when attackers tamper with inspect scripts.

After the fan-in, the first join pulls docker_socket_allowlist without using the standalone lookup command, satisfying governance reviewers who ban unscoped lookups. allowlist_hit gates whether a mount is expected. streamstats counts per_lane_seq per host and signal_type to show bursty replay attacks; eventstats lifts signal_burst_count for the closing table. The exit_vector_severity case encodes the five mandated classes; rows that represent approved, non-drift mounts return null and drop out. recommended_response is explicit text for paging bridges so analysts do not improvise under stress. The second join adds owner_team from container_owner for routing; daemon rows map to a synthetic container name so you can add a static owner_team row for infrastructure if desired.

Alert actions: critical severities should open a Sev-1 or equivalent, attach the recommended_response string, and link to this UC’s dashboard. medium Falco rows should create a task queue item for tier-one validation before paging.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.25 Docker Socket Exposure Detection. Tunables: indexes index=containers index=os; KV lookup docker_socket_allowlist via join (CSV or collections); allowed_image_regex is a Splunk PCRE; expected_container_id optional drift guard; earliest=-4h@h latest=@h.")`
| multisearch
    [ search index=containers sourcetype="docker:inspect" earliest=-4h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, Id, id, containerId, "")))
      | eval container_name=trim(toString(coalesce(Name, name, container_name, containerName, "")))
      | eval image_ref=trim(toString(coalesce(Config__Image, image, Image, "")))
      | spath output=mounts path=Mounts{}
      | mvexpand mounts
      | spath input=mounts output=mount_source path=Source
      | eval ms=lower(trim(toString(mount_source)))
      | where match(ms, "docker\\.sock")
      | eval signal_type="docker_inspect_mount"
      | eval evidence_detail=toString(mount_source)
      | eval daemon_listen_detail=""
      | eval falco_rule_name="" ]
    [ search index=containers sourcetype="docker:events" earliest=-4h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, "")))
      | eval lr=lower(_raw)
      | where match(lr, "docker\\.sock") OR match(lr, "mount=.*docker") OR match(lr, "/var/run/docker\\.sock|/run/docker\\.sock|/var/lib/docker\\.sock")
      | eval container_id=trim(toString(coalesce(container_id, id, Id, actor_id, "")))
      | eval container_name=trim(toString(coalesce(containerName, container_name, name, Actor__Attributes__name, "")))
      | eval image_ref=trim(toString(coalesce(Image, image, from, "")))
      | eval signal_type="docker_events_mount_signal"
      | eval evidence_detail=substr(_raw,1,900)
      | eval daemon_listen_detail=""
      | eval falco_rule_name="" ]
    [ search index=os (sourcetype="linux_secure" OR sourcetype="audit:json") earliest=-4h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval lr=lower(_raw)
      | where (match(lr, "dockerd") OR match(lr, "daemon\\.json") OR match(lr, "docker\\.service")) AND (match(lr, "2375|2376") OR match(lr, "tcp://0\\.0\\.0\\.0") OR match(lr, "\\\"hosts\\\"") OR match(lr, "-h tcp://"))
      | eval signal_type="daemon_exposure_audit"
      | eval container_id=""
      | eval container_name="DOCKER_DAEMON_HOST_CONFIG"
      | eval image_ref=""
      | eval evidence_detail=if(match(lr,"2375"), "audit_hint_tcp_2375_plaintext_expected", if(match(lr,"2376"), "audit_hint_tcp_2376_tls_review", "audit_hint_daemon_json_or_unit_change"))
      | eval daemon_listen_detail=substr(_raw,1,900)
      | eval falco_rule_name="" ]
    [ search index=containers sourcetype="falco:alert" earliest=-4h@h latest=@h
      | eval host_id=lower(toString(coalesce(hostname, host, k8s_node_name, nodeName, "")))
      | eval rule=toString(coalesce(rule, Rule, ruleName, ""))
      | eval rlow=lower(rule)
      | where (match(rlow, "docker") AND match(rlow, "socket")) OR match(rlow, "sensitive mount") OR match(rlow, "container with sensitive mount") OR match(rlow, "unix.*docker")
      | eval container_id=trim(toString(coalesce(container_id, containerID, k8s_pod_uid, "")))
      | eval container_name=trim(toString(coalesce(container_name, k8s_pod_name, containerName, "")))
      | eval image_ref=trim(toString(coalesce(container_image_repository, container_image_tag, image, "")))
      | eval signal_type="falco_runtime_alert"
      | eval evidence_detail=toString(coalesce(output, proc_cmdline, procCmdline, evt_arg, ""))
      | eval daemon_listen_detail=""
      | eval falco_rule_name=rule ]
| eval container_name=if(signal_type="daemon_exposure_audit", "DOCKER_DAEMON_HOST_CONFIG", container_name)
| join type=left max=0 host_id, container_name
    [| inputlookup docker_socket_allowlist
     | eval host_id=lower(trim(toString(host_id)))
     | eval container_name=trim(toString(container_name))
     | eval approved_reason=toString(coalesce(approved_reason, business_justification, ""))
     | eval expected_container_id=trim(toString(coalesce(expected_container_id, approved_container_id, "")))
     | eval allowed_image_regex=toString(coalesce(allowed_image_regex, image_allow_regex, ""))
     | fields host_id container_name approved_reason expected_container_id allowed_image_regex ]
| eval allowlist_hit=if(isnotnull(approved_reason) AND len(trim(approved_reason))>0, 1, 0)
| eval id_drift=if((allowlist_hit=1) AND (len(expected_container_id)>0) AND (len(container_id)>0) AND (container_id!=expected_container_id), 1, 0)
| eval image_drift=if((allowlist_hit=1) AND (len(allowed_image_regex)>0) AND (len(image_ref)>0) AND (NOT match(lower(image_ref), lower(allowed_image_regex))), 1, 0)
| eval allowlist_state=case(allowlist_hit=0, "unlisted", (id_drift=1 OR image_drift=1), "listed_drift", true(), "listed_ok")
| sort 0 + host_id, signal_type, _time
| streamstats window=120 current=t global=f count AS per_lane_seq BY host_id, signal_type
| eventstats count AS signal_burst_count BY host_id
| eval lr_daemon=lower(daemon_listen_detail)
| eval exit_vector_severity=case(
    signal_type="daemon_exposure_audit" AND match(lr_daemon, "2375"), "critical_2375_unencrypted_daemon",
    signal_type="daemon_exposure_audit" AND match(lr_daemon, "2376") AND (match(lr_daemon, "insecure|tlsverify=false|verify=false|noverify|--tlsverify=false") OR match(lower(evidence_detail), "insecure|tlsverify=false|verify=false")), "high_2376_no_tls_verify",
    signal_type="daemon_exposure_audit" AND match(lr_daemon, "2376"), "high_2376_no_tls_verify",
    (signal_type="docker_inspect_mount" OR signal_type="docker_events_mount_signal") AND allowlist_hit=0, "critical_socket_mount_unapproved",
    (signal_type="docker_inspect_mount" OR signal_type="docker_events_mount_signal") AND allowlist_hit=1 AND (id_drift=1 OR image_drift=1), "high_socket_mount_approved_drift",
    signal_type="falco_runtime_alert", "medium_falco_runtime_alert",
    true(), null())
| where isnotnull(exit_vector_severity)
| eval recommended_response=case(
    exit_vector_severity="critical_2375_unencrypted_daemon", "Treat as active breach surface: firewall block 2375, restart docker with TLS or local socket only, capture unit files and /etc/docker/daemon.json, rotate host admin creds, scan east-west from that host.",
    exit_vector_severity="critical_socket_mount_unapproved", "Immediately stop the task, remove /var/run/docker.sock bind propagation, rebuild from signed digest, open IR ticket with image provenance and deploy pipeline audit.",
    exit_vector_severity="high_socket_mount_approved_drift", "Reconcile KV allowlist row with live container_id and image digest; revoke stale approvals; force recreate under locked CI template.",
    exit_vector_severity="high_2376_no_tls_verify", "Require mutual TLS with verified client certs or SSH tunnel; remove insecure flags; validate systemd drop-ins for dockerd.",
    exit_vector_severity="medium_falco_runtime_alert", "Preserve Falco json output_fields, pivot to docker:inspect on same host, confirm mount graph, tune automation exceptions only after owner sign-off.",
    true(), "Correlate inspect, audit, and Falco arms before closure; escalate if any privileged container pull coincides.")
| join type=left max=0 host_id, container_name
    [| inputlookup container_owner.csv
     | eval host_id=lower(toString(host))
     | eval container_name=toString(container_name)
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | fields host_id container_name owner_team ]
| table _time host_id container_id container_name image_ref signal_type evidence_detail falco_rule_name exit_vector_severity allowlist_state per_lane_seq signal_burst_count owner_team recommended_response
```

### Step 4 — Validate

Positive test A — unapproved socket mount: on a disposable Linux host run docker run -v /var/run/docker.sock:/var/run/docker.sock --rm alpine sleep 300 without an allowlist row. Wait for inspect ingestion and confirm docker_inspect_mount fires critical_socket_mount_unapproved with allowlist_state unlisted. Tear down immediately.

Positive test B — Falco runtime: enable the default rules that flag docker socket access, exec a container that touches the socket with a noninteractive probe allowed by your lab policy, and confirm falco:alert produces medium_falco_runtime_alert while inspect may lag by one interval.

Positive test C — daemon TCP hint: in a sealed lab VM only, configure a unit snippet that includes -H tcp://0.0.0.0:2375 long enough to generate an audit line, then revert. Expect critical_2375_unencrypted_daemon. Do not leave this configuration running on any routable network.

Negative test — approved Portainer-style consumer: add a docker_socket_allowlist row matching host_id and container_name, set allowed_image_regex to match your lab image, run the approved container with the socket mount, and confirm the search returns zero rows when id and image align with expected_container_id.

Correlation test: introduce allowlist drift by changing the image tag without updating allowed_image_regex; expect high_socket_mount_approved_drift. Reset the lookup before leaving the lab.

RBAC test: a role without index=os must fail to see daemon_exposure_audit rows, proving split visibility.

Performance test: run Job Inspector on a busy Monday window; if scan cost exceeds budget, push docker:inspect into a summary index that only retains Mounts hashes.

### Step 5 — Operationalize & Troubleshoot

Case A — Daemon TCP 2375 detected: treat as emergency network exposure. Block the port at the nearest firewall, snapshot docker.service unit and daemon.json, restart dockerd without TCP listeners, and initiate credential rotation for anyone who could reach the host. Review cloud security groups because automation often mirrors bad templates across fleets.

Case B — Socket mount on production host without allowlist entry: isolate the workload, capture docker inspect and image digest, and trace the deploy pipeline commit that injected the volume. Assume compromise until proven otherwise if the image is not yours.

Case C — Falco alert without daemon-side detection: Falco may fire on benign language runtimes probing the socket path; pull docker:inspect for the same minute. If inspect shows no mount but Falco persists, investigate PID namespace cloning and rule specificity before muting.

Case D — Allowlist drift for Portainer or Traefik: update expected_container_id after controlled redeploys, tie changes to CAB tickets, and reject permanent wildcards in allowed_image_regex.

Case E — docker:events noise from CI: ephemeral runners may spam mount strings; route CI hosts to a lower schedule or maintain parallel allowlists keyed by host class macros.

Case F — Audit arm floods after patch Tuesday: systemd restarts can resemble flag changes; diff daemon.json from backups before paging.

Case G — Join misses on container_owner: normalize Compose project prefixes between CSV publishers and event field extractions; add alias rows rather than loosening the join.

Case H — streamstats per_lane_seq resets unexpectedly: clock skew or batch replay can reorder _time; enforce NTP on forwarders and consider _indextime tie-breakers in a diagnostic clone.

Case I — Duplicate hits across inspect and events: keep both signals during investigations; dedup in presentation layer using stats latest by host_id and container_id if alerts duplicate.

Case J — Splunk Universal Forwarder host monitoring container with an approved socket: document it explicitly in docker_socket_allowlist with ticket id in approved_reason so tier-one analysts recognize the pattern.

Dashboard layout: publish a severity-tiered table trellised by exit_vector_severity with drilldowns to raw docker:inspect Mounts, the triggering audit line, and Falco json. Add a Sankey or flow diagram panel from container_id to mount_source to host_id for leadership briefings. Maintain a single-value tile counting critical_2375_unencrypted_daemon in the trailing twenty-four hours and another for critical_socket_mount_unapproved.

Evidence retention: weekly CSV exports of the closing table to a restricted index with lookup commit hashes satisfies most SOC2 and ISO 27001 control testers when paired with change tickets. Map findings to PCI DSS expectation of monitoring unauthorized access paths for in-scope hosts.

Governance: quarterly, replay one historical incident through the SPL after Docker or Falco upgrades. Update the comment macro when indexes move.

Closing checklist: five plain-text step headers present; multisearch lists four arms; coalesce appears in every arm; streamstats and eventstats both appear; two join type=left max=0 blocks wrap inputlookup only; exit_vector_severity uses the five mandated strings; table lists thirteen columns including recommended_response; narrative JSON fields avoid asterisk emphasis; knownFalsePositives stay security-themed; references include Docker docs, Falco guidance, CIS Docker Benchmark landing page, MITRE T1611, NIST SP 800-190, and a specific Splunk Lantern article.

Supplemental engineering notes for long-term owners: when migrating to rootless Docker, socket paths and permissions change but risk remains if users delegate poorly; revisit allowlist paths when docker context switches to remote daemons. When using Podman with docker.sock compatibility, field names may differ; extend coalesce lists carefully. When EKS or GKE node groups swap to containerd-only without Docker, retire this UC on those classes rather than forcing noisy suppressions. When integrating Splunk Enterprise Security, map exit_vector_severity to risk scores with higher weight on critical_2375_unencrypted_daemon. When auditors ask for CIS Docker Benchmark control 5.31 coverage, attach a screenshot of this saved search description and a redacted alert row. When finance questions ingest cost, show that inspect compression and five-minute schedules beat breach cost asymmetry by orders of magnitude. When legal requests preservation, include docker:inspect json and Falco output_fields in the hold scope. When red-teaming, pair this UC with UC-3.1.24 docker exec auditing for lateral movement stories. When OT gateways accidentally ship Docker for edge services, duplicate the governance lookups with OT owner_team routing. When service meshes inject sidecars that touch abstract sockets, validate Falco macros so service mesh noise does not drown real docker.sock connects. When vulnerability management finds CVEs in dockerd, cross-launch this dashboard to prove you were not simultaneously exposing TCP APIs. When board decks need a single sentence, use the grandma-friendly storyline about master keys and open front doors, not crash-loop jargon.



## SPL

```spl
`comment("UC-3.1.25 Docker Socket Exposure Detection. Tunables: indexes index=containers index=os; KV lookup docker_socket_allowlist via join (CSV or collections); allowed_image_regex is a Splunk PCRE; expected_container_id optional drift guard; earliest=-4h@h latest=@h.")`
| multisearch
    [ search index=containers sourcetype="docker:inspect" earliest=-4h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, Id, id, containerId, "")))
      | eval container_name=trim(toString(coalesce(Name, name, container_name, containerName, "")))
      | eval image_ref=trim(toString(coalesce(Config__Image, image, Image, "")))
      | spath output=mounts path=Mounts{}
      | mvexpand mounts
      | spath input=mounts output=mount_source path=Source
      | eval ms=lower(trim(toString(mount_source)))
      | where match(ms, "docker\\.sock")
      | eval signal_type="docker_inspect_mount"
      | eval evidence_detail=toString(mount_source)
      | eval daemon_listen_detail=""
      | eval falco_rule_name="" ]
    [ search index=containers sourcetype="docker:events" earliest=-4h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, "")))
      | eval lr=lower(_raw)
      | where match(lr, "docker\\.sock") OR match(lr, "mount=.*docker") OR match(lr, "/var/run/docker\\.sock|/run/docker\\.sock|/var/lib/docker\\.sock")
      | eval container_id=trim(toString(coalesce(container_id, id, Id, actor_id, "")))
      | eval container_name=trim(toString(coalesce(containerName, container_name, name, Actor__Attributes__name, "")))
      | eval image_ref=trim(toString(coalesce(Image, image, from, "")))
      | eval signal_type="docker_events_mount_signal"
      | eval evidence_detail=substr(_raw,1,900)
      | eval daemon_listen_detail=""
      | eval falco_rule_name="" ]
    [ search index=os (sourcetype="linux_secure" OR sourcetype="audit:json") earliest=-4h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval lr=lower(_raw)
      | where (match(lr, "dockerd") OR match(lr, "daemon\\.json") OR match(lr, "docker\\.service")) AND (match(lr, "2375|2376") OR match(lr, "tcp://0\\.0\\.0\\.0") OR match(lr, "\\\"hosts\\\"") OR match(lr, "-h tcp://"))
      | eval signal_type="daemon_exposure_audit"
      | eval container_id=""
      | eval container_name="DOCKER_DAEMON_HOST_CONFIG"
      | eval image_ref=""
      | eval evidence_detail=if(match(lr,"2375"), "audit_hint_tcp_2375_plaintext_expected", if(match(lr,"2376"), "audit_hint_tcp_2376_tls_review", "audit_hint_daemon_json_or_unit_change"))
      | eval daemon_listen_detail=substr(_raw,1,900)
      | eval falco_rule_name="" ]
    [ search index=containers sourcetype="falco:alert" earliest=-4h@h latest=@h
      | eval host_id=lower(toString(coalesce(hostname, host, k8s_node_name, nodeName, "")))
      | eval rule=toString(coalesce(rule, Rule, ruleName, ""))
      | eval rlow=lower(rule)
      | where (match(rlow, "docker") AND match(rlow, "socket")) OR match(rlow, "sensitive mount") OR match(rlow, "container with sensitive mount") OR match(rlow, "unix.*docker")
      | eval container_id=trim(toString(coalesce(container_id, containerID, k8s_pod_uid, "")))
      | eval container_name=trim(toString(coalesce(container_name, k8s_pod_name, containerName, "")))
      | eval image_ref=trim(toString(coalesce(container_image_repository, container_image_tag, image, "")))
      | eval signal_type="falco_runtime_alert"
      | eval evidence_detail=toString(coalesce(output, proc_cmdline, procCmdline, evt_arg, ""))
      | eval daemon_listen_detail=""
      | eval falco_rule_name=rule ]
| eval container_name=if(signal_type="daemon_exposure_audit", "DOCKER_DAEMON_HOST_CONFIG", container_name)
| join type=left max=0 host_id, container_name
    [| inputlookup docker_socket_allowlist
     | eval host_id=lower(trim(toString(host_id)))
     | eval container_name=trim(toString(container_name))
     | eval approved_reason=toString(coalesce(approved_reason, business_justification, ""))
     | eval expected_container_id=trim(toString(coalesce(expected_container_id, approved_container_id, "")))
     | eval allowed_image_regex=toString(coalesce(allowed_image_regex, image_allow_regex, ""))
     | fields host_id container_name approved_reason expected_container_id allowed_image_regex ]
| eval allowlist_hit=if(isnotnull(approved_reason) AND len(trim(approved_reason))>0, 1, 0)
| eval id_drift=if((allowlist_hit=1) AND (len(expected_container_id)>0) AND (len(container_id)>0) AND (container_id!=expected_container_id), 1, 0)
| eval image_drift=if((allowlist_hit=1) AND (len(allowed_image_regex)>0) AND (len(image_ref)>0) AND (NOT match(lower(image_ref), lower(allowed_image_regex))), 1, 0)
| eval allowlist_state=case(allowlist_hit=0, "unlisted", (id_drift=1 OR image_drift=1), "listed_drift", true(), "listed_ok")
| sort 0 + host_id, signal_type, _time
| streamstats window=120 current=t global=f count AS per_lane_seq BY host_id, signal_type
| eventstats count AS signal_burst_count BY host_id
| eval lr_daemon=lower(daemon_listen_detail)
| eval exit_vector_severity=case(
    signal_type="daemon_exposure_audit" AND match(lr_daemon, "2375"), "critical_2375_unencrypted_daemon",
    signal_type="daemon_exposure_audit" AND match(lr_daemon, "2376") AND (match(lr_daemon, "insecure|tlsverify=false|verify=false|noverify|--tlsverify=false") OR match(lower(evidence_detail), "insecure|tlsverify=false|verify=false")), "high_2376_no_tls_verify",
    signal_type="daemon_exposure_audit" AND match(lr_daemon, "2376"), "high_2376_no_tls_verify",
    (signal_type="docker_inspect_mount" OR signal_type="docker_events_mount_signal") AND allowlist_hit=0, "critical_socket_mount_unapproved",
    (signal_type="docker_inspect_mount" OR signal_type="docker_events_mount_signal") AND allowlist_hit=1 AND (id_drift=1 OR image_drift=1), "high_socket_mount_approved_drift",
    signal_type="falco_runtime_alert", "medium_falco_runtime_alert",
    true(), null())
| where isnotnull(exit_vector_severity)
| eval recommended_response=case(
    exit_vector_severity="critical_2375_unencrypted_daemon", "Treat as active breach surface: firewall block 2375, restart docker with TLS or local socket only, capture unit files and /etc/docker/daemon.json, rotate host admin creds, scan east-west from that host.",
    exit_vector_severity="critical_socket_mount_unapproved", "Immediately stop the task, remove /var/run/docker.sock bind propagation, rebuild from signed digest, open IR ticket with image provenance and deploy pipeline audit.",
    exit_vector_severity="high_socket_mount_approved_drift", "Reconcile KV allowlist row with live container_id and image digest; revoke stale approvals; force recreate under locked CI template.",
    exit_vector_severity="high_2376_no_tls_verify", "Require mutual TLS with verified client certs or SSH tunnel; remove insecure flags; validate systemd drop-ins for dockerd.",
    exit_vector_severity="medium_falco_runtime_alert", "Preserve Falco json output_fields, pivot to docker:inspect on same host, confirm mount graph, tune automation exceptions only after owner sign-off.",
    true(), "Correlate inspect, audit, and Falco arms before closure; escalate if any privileged container pull coincides.")
| join type=left max=0 host_id, container_name
    [| inputlookup container_owner.csv
     | eval host_id=lower(toString(host))
     | eval container_name=toString(container_name)
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | fields host_id container_name owner_team ]
| table _time host_id container_id container_name image_ref signal_type evidence_detail falco_rule_name exit_vector_severity allowlist_state per_lane_seq signal_burst_count owner_team recommended_response
```

## CIM SPL

```spl
| tstats summariesonly=true count FROM datamodel=Endpoint WHERE nodename=Endpoint.Processes (Processes.process="dockerd" OR Processes.process_path="*/dockerd") BY Processes.dest Processes.process earliest=-24h latest=now
| rename Processes.dest AS host | head 200
```

## Visualization

Primary panel is a severity-tier ranked table by host_id with cell coloring for exit_vector_severity and drilldowns into raw Mounts json, audit _raw, and Falco output_fields. Add an SPL-driven Sankey from container_id through mount_source to host_id for leadership briefings. Secondary single-value tiles track counts of critical_2375_unencrypted_daemon and critical_socket_mount_unapproved over twenty-four hours. Provide a parallel timeline chart of per_lane_seq by signal_type to show burst replay during red-team exercises.

## Known False Positives

Legitimate Portainer, Traefik, Caddy docker-proxy helpers, Watchtower, Diun, and vendor-specific registry mirrors sometimes require docker.sock by design; every such workload must carry an explicit docker_socket_allowlist row with ticket-backed approved_reason text or analysts will keep reopening the same incident. CI build agents that still use Docker-in-Docker with socket forwarding will fire unless you migrate them to rootless Kaniko, BuildKit remote builders, or Podman isolated builds; during transition, tag those hosts with a ci namespace macro rather than global suppression. Local KIND, k3d, minikube, or testcontainers labs on engineer laptops should never ship their feeds into production indexes; route lab forwarders to a dev index and exclude them at the saved-search layer. Splunk Universal Forwarder or Datadog-style host monitoring containers that mount the socket under change control should be pre-approved with expected_container_id pinned to the digest you deploy. Security tools such as Sysdig agents or Falco exporters may legitimately reference docker APIs; document them like any other allowlist consumer. Managed services teams that intentionally expose Engine APIs behind mutual TLS on 2376 can still trigger high severity if argv text lacks verify flags; tune high_2376_no_tls_verify only after engineers prove client certificate enforcement on the load balancer path. Registry pull-through caches that run as privileged sidecars near dockerd can create mount-like strings in docker:events without a true breakout; corroborate with inspect before paging leadership.

## References

- [Docker Docs — Docker Engine security (daemon attack surface)](https://docs.docker.com/engine/security/)
- [Falco Docs — Rules concepts (default and custom policies)](https://falco.org/docs/concepts/rules/)
- [CIS Docker Benchmarks (community landing)](https://www.cisecurity.org/benchmark/docker)
- [MITRE ATT&CK — T1611 Escape to Host](https://attack.mitre.org/techniques/T1611/)
- [Splunk Lantern — Docker data source guidance](https://lantern.splunk.com/Data_Sources/Docker)
- [NIST SP 800-190 — Application Container Security Guide](https://csrc.nist.gov/publications/detail/sp/800-190/final)
