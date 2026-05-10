<!-- AUTO-GENERATED from UC-3.1.9.json — DO NOT EDIT -->

---
id: "3.1.9"
title: "Docker Daemon Health and Version Drift"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.1.9 · Docker Daemon Health and Version Drift

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We check that every machine running our container engine reports the same approved software generation you expect, like making sure every truck in a delivery fleet passed the same safety inspection on schedule. When too many different versions appear in one region, or a known safety recall still shows up in the field, we raise a hand before anything catches fire.*

---

## Description

Monitors Docker Engine binary-version compliance and patch-channel governance for large mixed fleets spanning data-center bare metal, edge gateways, and cloud VMs by ingesting periodic docker version and docker info JSON into index=oti_containers, joining an authoritative docker_engine_versions.csv allowlist that carries supported_until_date, channel, and known_cves metadata, and scoring docker info Warnings that reveal kernel or cgroup misconfiguration affecting security and resource accounting. The analytic measures distinct_engine_versions_per_segment with eventstats so operational segments that exceed three concurrent Engine minors flag high_engine_version_sprawl_segment_above_3, uses streamstats to detect recent Server.Version transitions per host_id for upgrade auditing, and classifies severity into CVE-bearing builds still in production, calendar EOL breaches, security-relevant warnings such as missing memory limit support, sprawl breaches, residual minor drift, and stale build timestamps. Three telemetry feeds matter: sourcetype=docker:version for Server.Version and API metadata, sourcetype=docker:info for ServerVersion, ContainerdVersion, RuncVersion, KernelVersion, and Warnings arrays, and optionally sourcetype=docker:journald when you need narrative correlation with UC-3.1.8 without merging scopes. This is intentionally not UC-3.1.8, which tracks dockerd journald error-class reliability narratives and Prometheus engine API saturation, and not UC-3.1.11, which tracks dockerd file descriptor, thread, and pull-queue ceilings from /proc and metrics scrapes.

## Value

Quantified outcomes include shrinking mean time to patch for Engine CVEs such as BuildKit race class issues by naming exact hosts and versions still on vulnerable builds, preventing sudden image pull or run failures when API or image-format defaults shift across semver boundaries, and producing auditor-friendly evidence for SOC 2 CC8.1 change-management reviews plus mapping hooks to NIST Cybersecurity Framework PR.IP-12 and PCI DSS 6.2 secure systems maintenance narratives when weekly CSV exports tie Splunk rows to CAB tickets. Finance and reliability leaders gain a single pane showing how many hosts remain outside the golden matrix, which supports capacity conversations about repaving versus in-place upgrades, while security operations receives prioritized rows when known_cves intersects CISA KEV catalog entries. Developer productivity improves when CI base images and worker AMIs target the same narrow Engine set, reducing impossible-to-reproduce bugs caused by one team on 24.0.x and another on 26.x. Risk registers stay honest because docker info Warnings surface silent cgroup gaps that vulnerability scanners never see, and because patch latency metrics become trendable quarter over quarter instead of anecdotal.

## Implementation

Deploy Splunk Add-on for Unix and Linux scripted inputs emitting sourcetype=docker:version and sourcetype=docker:info into index=oti_containers on five-minute cadences, publish lookups/docker_engine_versions.csv with engine_version, supported_until_date, channel, and known_cves, schedule container_uc_3_1_9_engine_version_drift with earliest=-24h@h, route critical severities to Head of Platform and archive weekly exports to your evidence index.

## Evidence

Saved search container_uc_3_1_9_engine_version_drift against index=oti_containers, lookups/docker_engine_versions.csv with weekly git commits, dashboard Docker Engine Version Governance exporting CSV snapshots to the evidence index, and cited references from Docker Engine release notes, Docker security bulletins, CIS Docker Benchmark guidance, Splunk Lantern vulnerability-descriptor articles, Aqua Security Leaky Vessels remediation blogging, and CISA KEV listings.

## Control test

### Positive scenario

On a lab Linux host with docker:version and docker:info ingesting into oti_containers, set docker_engine_versions.csv to list the host Engine build with a known_cves value containing CVE-2024-23651 and a future supported_until_date, run the saved search, and expect a critical_engine_known_cve_unpatched row with populated recommended_response and twelve-column table projection.

### Negative scenario

Normalize the host onto an allowlisted Engine build whose docker_engine_versions.csv row carries empty known_cves and a future supported_until_date, ensure docker info Warnings is an empty array, align segment peers to a single server_version, and confirm the saved search returns zero rows for that host when no other drift signals exist.

## Detailed Implementation

### Step 1 — Prerequisites and governance contracts

Platform engineering must treat Docker Engine as part of the regulated software bill of materials, not as an invisible dependency beneath application containers. Before enabling this control, confirm Splunk Add-on for Unix and Linux (Splunkbase 833) or an equivalent customer-maintained scripted input tier can execute docker version --format json and docker info --format json as a least-privileged service account that is a member of the linux group owning /var/run/docker.sock, or use a documented TCP or SSH relay that preserves identical JSON field shapes. RBAC on the Splunk side must allow index=oti_containers for operators running the saved search, plus lookup editor for the team that curates lookups/docker_engine_versions.csv with columns engine_version, supported_until_date, channel, and known_cves; version control that CSV in git and promote it through the same change advisory board process as kernel rollouts because stale rows create false assurance. Network path from universal forwarders to indexers must tolerate five-minute poll bursts without dropping HEC batches when five thousand hosts report simultaneously after daylight-saving clock jumps. Document the distinction between this UC and UC-3.1.8: journald level=error streams describe runtime failure narratives, while this UC reads declarative inventory JSON from the Engine API. Document the distinction versus UC-3.1.11: file descriptor and thread ceilings describe process pressure, not semver compliance. CMDB or cloud tag ingestion must populate host_segment or equivalent so eventstats can compute distinct_engine_versions_per_segment per data-center, edge, or cloud-VM lane; without segmentation every host lands in unsegmented and sprawl math becomes meaningless. Kernel uniformity matters because docker info Warnings frequently reference cgroup and netfilter capabilities; maintain a kernel allowlist cross-reference so warnings that are benign on one kernel remain explainable. Licensing: this UC uses core Splunk indexing without premium apps, though optional Splunk ITSI can mirror severity tiers as entity-level KPIs if your operations model already models docker hosts as entities. Evidence retention should meet your patch-management policy, commonly ninety to one hundred eighty days of raw docker:version and docker:info events plus seven years of weekly CSV snapshots exported to an evidence index if finance audits ask for historical proof of Engine standardization. Finally, assign Head of Platform as accountable owner because Engine semver discipline spans infrastructure, security, and developer productivity. Executive stakeholders care because image-format compatibility and API negotiation drift silently break CI/CD contracts long before journald logs a panic, and because regulators increasingly ask for proof that container runtimes were patched within vendor-published windows, not merely that applications were redeployed.

### Step 2 — Configure docker version and docker info scripted inputs

Create two scripted inputs or one consolidated script that prints newline-delimited JSON with distinct sourcetype overrides. Recommended interval is three hundred seconds for docker:info because Warnings change with sysctl edits, and six hundred seconds for docker:version unless you are inside an active upgrade wave where five-minute sampling is justified. Set sourcetype=docker:version for events produced by docker version --format '{{json .}}' after elevating to the docker-capable user inside the script; preserve the full Client and Server objects so coalesce ladders can read Server.Version, Server.ApiVersion, Server.GoVersion, Server.Os, Server.Arch, Server.KernelVersion, and Server.BuildTime without lossy transforms. Set sourcetype=docker:info for docker info --format '{{json .}}' output, ensuring Warnings arrives as a multivalue or JSON array Splunk can parse; if your TA flattens arrays into _raw only, add KV_MODE=json and ARRAY_INDEXING=true in props.conf for that sourcetype. Route both streams to index=oti_containers and stamp host_segment from a static file or from cloud instance tags read at collection time so downstream searches do not rely on brittle Splunk search-time lookups for segmentation. Harden the script: timeout docker calls after thirty seconds, log stderr locally when docker returns permission denied, and never print registry credentials. Volume expectations: roughly two events per host per poll cycle across both sourcetypes, which is negligible compared to container logs but still requires indexer acknowledgment during fleet-wide upgrades when every host changes semver simultaneously. Optional docker:journald sourcetype remains on the host for UC-3.1.8; do not merge those raw lines into docker:version because it breaks JSON parsing. After deployment, run a twenty-four hour timechart count by sourcetype to prove continuous arrival and detect silent gaps longer than two intervals, which usually indicate socket permission drift or disk-full on the forwarder. Document forwarder upgrade interactions: when Splunk_TA_nix updates shuffle field extractions, replay props on a canary indexer before fleet rollout so Server.Version does not temporarily disappear from search. For Mirantis Container Runtime or enterprise Moby forks, capture vendor-specific JSON quirks in a sidecar README so the coalesce list in the SPL remains the single source of truth rather than forked searches per distribution.

### Step 3 — Create the search and alert

#### Understanding this SPL without repeating the mechanical definition of every command: the comment macro is the operator contract for indexes, sourcetypes, lookup names, and governance thresholds. The search pulls two scripted-input families that must land in the same index so one host_id timeline can merge docker version JSON and docker info JSON without implying a single vendor owns both schemas. Coalesce ladders tolerate Moby builds that flatten Server.Version versus distributions that only populate ServerVersion on the info side, plus TA variants that renamed kernel and API fields during upgrades. streamstats keeps a per-host previous Server.Version sample so upgrade regressions surface as version_changed_recent before stats collapses the timeline; eventstats then measures distinct_engine_versions_per_segment so a retail edge tier cannot hide twelve different Engine minors behind one dashboard tile. The inputlookup join is intentionally left outer: a missing allowlist row is itself a governance finding (lookup_miss) distinct from a populated row that documents known_cves text drawn from Docker security bulletins. Warnings logic keys off docker:info only because docker version does not emit the Warnings array; sec_warn elevates memory and netfilter classes while deprecation-only paths fall through to medium_minor_version_drift so SOC evidence stays honest about kernel-impact versus cosmetic notices. Severity ordering applies critical tiers to documented CVE rows and calendar EOL before sprawl, because patch latency and legal attestation beat capacity aesthetics in audits. Recommended_response text is sized for paging bridges so on-call engineers paste runbook verbs directly into change systems. Optional docker:journald correlation belongs in a secondary panel paired with UC-3.1.8 rather than inside this pipeline, keeping the monitoring axis binary-clean for version compliance. Pipeline walkthrough: scope index and sourcetypes; normalize host_id and segment; derive sv_line and parallel component versions; classify warnings; sort for streamstats; aggregate per host; normalize engine_key for join; enrich allowlist; compute sprawl with eventstats; case severity; filter to actionable rows; project the twelve-column compliance table.

```spl
`comment("UC-3.1.9 Docker Daemon Health and Version Drift. Engine binary compliance, CVE allowlist governance, docker info Warnings. Distinct from UC-3.1.8 journald level=error reliability and UC-3.1.11 dockerd FD/thread ceilings. Tunables: index=oti_containers; sourcetypes docker:version docker:info; optional docker:journald for ServerError correlation; lookup docker_engine_versions.csv fields engine_version supported_until_date channel known_cves; sprawl_distinct_threshold=3; earliest=-24h@h latest=@h")`
| search index=oti_containers (sourcetype="docker:version" OR sourcetype="docker:info") earliest=-24h@h latest=@h
| eval host_id=lower(trim(toString(coalesce(host, Host, hostname, _HOSTNAME, host_id, dest, ""))))
| eval segment=trim(toString(coalesce(host_segment, segment, fleet_segment, datacenter_tier, availability_zone, pool, "unsegmented")))
| eval server_from_ver=trim(toString(coalesce(server_version, Server_Version, ServerVersion, "")))
| eval server_from_info=trim(toString(coalesce(ServerVersion, server_version, "")))
| eval sv_line=trim(toString(coalesce(server_from_ver, server_from_info, "")))
| eval api_line=trim(toString(coalesce(api_version, ApiVersion, APIVersion, Client_APIVersion, "")))
| eval cd_line=trim(toString(coalesce(containerd_version, ContainerdVersion, containerdVersion, "")))
| eval rc_line=trim(toString(coalesce(runc_version, RuncVersion, runcVersion, "")))
| eval kv_line=trim(toString(coalesce(kernel_version, KernelVersion, Server_KernelVersion, "")))
| eval bt_line=trim(toString(coalesce(Server_BuildTime, BuildTime, server_buildtime, "")))
| eval warn_blob=toString(coalesce(Warnings, warnings, ""))
| eval warn_lower=lower(warn_blob)
| eval warnings_count=if(sourcetype!="docker:info", null(), if(match(warn_blob,"^\s*\[\s*\]\s*$") OR len(trim(warn_blob))==0 OR warn_blob="null", 0, if(isnotnull(Warnings), mvcount(Warnings), if(match(warn_blob,"(?i)warning"), 1, 0))))
| eval warnings_summary=if(sourcetype!="docker:info", "", case(
    warnings_count==0 OR isnull(warnings_count), "none",
    match(warn_lower, "(?i)no memory limit|memory limit support|cgroup.*memory"), "memory_limit_support",
    match(warn_lower, "(?i)bridge-nf-call-iptables|iptables.*disabled|forbidden inter-container"), "netfilter_bridge",
    match(warn_lower, "(?i)deprecated"), "deprecation",
    true(), "other"))
| sort 0 + host_id, _time
| streamstats window=1 current=f last(sv_line) AS prev_sv BY host_id
| eval version_changed_recent=if(sourcetype=="docker:version" AND isnotnull(prev_sv) AND len(prev_sv)>0 AND len(sv_line)>0 AND sv_line!=prev_sv, 1, 0)
| stats 
    latest(sv_line) AS server_version
    latest(api_line) AS api_version
    latest(cd_line) AS containerd_version
    latest(rc_line) AS runc_version
    latest(kv_line) AS kernel_version
    latest(bt_line) AS server_buildtime
    latest(warnings_count) AS warnings_count
    latest(warnings_summary) AS warnings_summary
    latest(warn_lower) AS warn_lower_agg
    max(version_changed_recent) AS had_version_change_window
    latest(segment) AS segment
  BY host_id
| eval engine_key=trim(replace(replace(server_version, "\s*\(.*$", ""), "\s+ce\s*$", ""))
| join type=left max=0 engine_key
    [| inputlookup docker_engine_versions.csv
     | eval engine_key=trim(toString(engine_version))
     | eval supported_until_epoch=coalesce(
         strptime(trim(toString(supported_until_date)), "%Y-%m-%d"),
         strptime(trim(toString(supported_until_date)), "%m/%d/%Y"))
     | eval supported_until=strftime(supported_until_epoch, "%Y-%m-%d")
     | eval known_cves=toString(coalesce(known_cves, cve_list, ""))
     | eval patch_channel=toString(coalesce(channel, patch_channel, ""))
     | fields engine_key supported_until_epoch supported_until known_cves patch_channel ]
| fillnull value="" known_cves
| eval eol_in_prod=if(isnotnull(supported_until_epoch) AND supported_until_epoch>0 AND supported_until_epoch < relative_time(now(), "@d"), 1, 0)
| eval has_known_cve=if(match(lower(known_cves), "cve-20"), 1, 0)
| eval lookup_miss=if(len(trim(server_version))>0 AND (isnull(supported_until_epoch) OR supported_until_epoch==0), 1, 0)
| eval build_epoch=if(len(trim(server_buildtime))>0, coalesce(
    strptime(substr(trim(server_buildtime),1,19), "%Y-%m-%dT%H:%M:%S"),
    strptime(trim(server_buildtime), "%Y-%m-%d")), null())
| eval build_stale=if(isnotnull(build_epoch) AND build_epoch < relative_time(now(), "-400d@d"), 1, 0)
| eventstats dc(server_version) AS distinct_engine_versions_per_segment BY segment
| eval sprawl_flag=if(distinct_engine_versions_per_segment>3, 1, 0)
| eval sec_warn=if(warnings_count>=1 AND (match(warn_lower_agg, "(?i)no memory limit|memory limit support|cgroup") OR match(warn_lower_agg, "(?i)bridge-nf-call-iptables|iptables")), 1, 0)
| eval deprec_only=if(warnings_count>=1 AND sec_warn==0 AND match(warn_lower_agg, "(?i)deprecated"), 1, 0)
| eval severity=case(
    has_known_cve==1 AND lookup_miss==0, "critical_engine_known_cve_unpatched",
    eol_in_prod==1, "critical_engine_eol_in_production",
    sec_warn==1, "high_warnings_security_relevant",
    sprawl_flag==1, "high_engine_version_sprawl_segment_above_3",
    deprec_only==1 OR lookup_miss==1 OR (distinct_engine_versions_per_segment>=2 AND distinct_engine_versions_per_segment<=3), "medium_minor_version_drift",
    build_stale==1, "low_engine_buildtime_stale",
    warnings_count>=1, "high_warnings_security_relevant",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity=="critical_engine_known_cve_unpatched", "Freeze image promotion on the host class, attach Docker security bulletin and CISA KEV references to the change ticket, schedule emergency Engine patch to an approved build on the docker_engine_versions allowlist, validate containerd and runc pins in the same maintenance wave, and rerun docker version after reboot to close the audit finding.",
    severity=="critical_engine_eol_in_production", "Treat as compliance debt: pull the host segment into the next CAB-approved Engine upgrade train, document exception expiry, and block net-new production scheduling on the segment until Server.Version matches a supported_until_date row in docker_engine_versions.csv.",
    severity=="high_warnings_security_relevant", "Remediate kernel and cgroup configuration behind docker info Warnings: enable memory controller accounting or cgroup v2 delegation as required, restore bridge-nf-call-iptables where security policy expects firewall enforcement on container bridges, reboot only under change control, and resample docker:info to prove warnings_count returns to zero.",
    severity=="high_engine_version_sprawl_segment_above_3", "Collapse patch-channel sprawl: freeze ad-hoc package installs, repave hosts onto the golden Engine matrix (for example three approved minors), reconcile vendor mirrors so apt/yum pins cannot drift, and attach fleet-wide distinct_engine_versions_per_segment metrics to the quarterly governance review.",
    severity=="medium_minor_version_drift", "Schedule coordinated patch: align Server.Version to the nearest approved allowlist row, refresh docker_engine_versions.csv with vendor LTS rationale if the version is intentional, and separate deprecation-only warnings from security-relevant kernel gaps before downgrading severity.",
    severity=="low_engine_buildtime_stale", "Rebuild or restage the Engine package from a trusted artifact registry so Server.BuildTime is current, verify supply-chain attestation on the binary, and dismiss only after build_epoch matches a release built within policy window.",
    true(), "Review docker:version and docker:info side by side with optional docker:journald ServerError correlation; route to Head of Platform.")
| table host_id segment server_version api_version containerd_version runc_version kernel_version supported_until known_cves warnings_count warnings_summary severity recommended_response
```

### Step 4 — Validate inventory fidelity and allowlist joins

Validation begins on a lab host with a known Engine build: run docker version and docker info locally, then compare each field to the latest indexed event for that host_id within index=oti_containers. Confirm Server.Version matches, ApiVersion aligns with the documented API negotiation level for that Engine, and KernelVersion matches uname -r within the formatting differences Moby reports. For Warnings, temporarily disable bridge-nf-call-iptables on a disposable VM and confirm warnings_count increments within one collection interval, then restore sysctl and confirm return to zero. Test the join by loading a temporary docker_engine_versions.csv row with a fake engine_version matching the lab host and a supported_until_date in the past; the saved search should raise critical_engine_eol_in_production until you restore a future date. Test CVE classification by populating known_cves with a sample CVE-2024-23651 style string; expect critical_engine_known_cve_unpatched when lookup_miss is zero. Validate sprawl math by indexing three hosts in the same segment with three different Engine minors; distinct_engine_versions_per_segment should read three without firing high sprawl, then add a fourth distinct minor and confirm high_engine_version_sprawl_segment_above_3 on that segment. Cross-check streamstats version flips by installing an older Engine package on a throwaway host, letting it index, upgrading, and verifying had_version_change_window flags the transition in the underlying pre-stats data if you temporarily remove the stats command during debugging. Compare counts to your configuration management database: the distinct count of server_version in Splunk should match the distinct count of package versions CMDB believes are installed, modulo delayed forwarder connectivity. RBAC testing ensures readers without oti_containers access see zero rows, proving separation of duties between platform and application teams. Extend validation to multi-arch fleets: ARM64 hosts sometimes omit Client sections when collectors run server-only scripts; confirm coalesce still yields api_version from whichever branch populated. For edge gateways on intermittent LTE, widen the acceptance window for staleness but keep version compliance separate from UC-3.1.8 connectivity alerts so operators do not conflate missed polls with semver drift. Perform quarterly red-team style checks where a volunteer downgrades Engine in lab and confirms the saved search fires within two collection intervals, attaching results to SOC 2 evidence binders. When Splunk Cloud export jobs archive weekly CSV snapshots, verify signatures or checksums on those exports so auditors trust the chain of custody.

### Step 5 — Operationalize dashboards and troubleshoot drift signals

Operationalize by scheduling saved search container_uc_3_1_9_engine_version_drift every fifteen minutes on earliest=-24h@h latest=@h for steady state, tightening to five minutes during enterprise patch waves. Route critical_engine_known_cve_unpatched and critical_engine_eol_in_production to the Head of Platform paging bridge jointly with information security when CISA KEV references appear in known_cves. Build four dashboard panels: a pie chart of server_version distribution colored by patch_channel from the lookup, a table of hosts with non-empty known_cves, a histogram of warnings_count bucketed zero versus one versus many, and a timechart of distinct_engine_versions_per_segment with a reference line at three. Archive weekly CSV exports of the closing table to your evidence index with git commit hashes for docker_engine_versions.csv attached in the ticket description. Integrate maintenance windows by adding maintenance=true rows to a host_suppressions.csv lookup rather than disabling the search globally. Train analysts that low_engine_buildtime_stale is a supply-chain hygiene signal, not a runtime incident, unless paired with compromise indicators. Keep optional docker:journald panels adjacent but authored under UC-3.1.8 to avoid conflating log errors with semver governance. During major acquisitions, run a one-time backfill across newly merged networks before enabling alerts so inherited stray versions do not page until mapped into segments. Pair executive summaries with dollars: quantify hours saved by avoiding image-format rollback incidents and attach NIST CSF PR.IP-12 mapping slides for risk committees.
Case 1 — Empty Server.Version on otherwise healthy hosts: freshly imaged Linux nodes sometimes emit docker:info before docker:version during first boot; confirm both sourcetypes share the same poll interval, verify the scripted input user can reach /var/run/docker.sock, and compare against sudo docker version on the host before muting.

Case 2 — engine_key join misses while docker reports a trailing distro suffix: Ubuntu packages append plus signs or distro tags; extend docker_engine_versions.csv with alias rows or strip tokens in a calculated field so 24.0.7~ubuntu matches the canonical 24.0.7 allowlist entry.

Case 3 — distinct_engine_versions_per_segment spikes during a canary lane: one segment intentionally runs a newer Engine build; document the lane in host_segment metadata and add a lookup column exempt_sprawl=1 for that segment rather than raising the global sprawl threshold.

Case 4 — warnings_count stuck at zero but operators see warnings in docker info: JSON may nest Warnings under a different path; add FIELDALIAS or spath extraction in props.conf for the TA, then replay a five-minute window to validate mvcount(Warnings).

Case 5 — known_cves fires critical on a version you already mitigated with AppArmor profiles: governance requires updating docker_engine_versions.csv to record compensating controls or clearing the CVE text after vendor confirmation; do not silence the alert without a CSV commit hash referenced in the ticket.

Case 6 — build_stale rows after golden image rebuilds: registry mirrors can serve an Engine RPM with an old embedded BuildTime while CI stamped a new layer; compare package NEVRA from rpm -q docker-ce against Server.BuildTime before trusting low_engine_buildtime_stale alone.

Case 7 — eventstats sprawl counts skewed by missing segment field: hosts default to unsegmented bucket; fix CMDB ingestion so fleet_tag populates before quarterly reviews, otherwise hundreds of unrelated hosts inflate one synthetic segment.

Case 8 — join explosion after duplicate engine_version rows in CSV: dedupe docker_engine_versions.csv on engine_key during the weekly publish job; Splunk join type=left max=0 still expects one authoritative row per key for predictable known_cves text.

Case 9 — Patch wave produces benign medium_minor_version_drift noise: when every host is mid-flight between two approved versions, temporarily widen the time window or join against a planned_versions.csv that encodes acceptable transition pairs so CAB-approved motion does not page as drift.

Case 10 — Air-gapped field teams import docker_engine_versions.csv quarterly while CVEs publish weekly: expect transient critical rows until the CSV refresh lands; route to vulnerability management with an explicit SLA instead of muting the Splunk alert, because the monitoring axis is working as designed.


## SPL

```spl
`comment("UC-3.1.9 Docker Daemon Health and Version Drift. Engine binary compliance, CVE allowlist governance, docker info Warnings. Distinct from UC-3.1.8 journald level=error reliability and UC-3.1.11 dockerd FD/thread ceilings. Tunables: index=oti_containers; sourcetypes docker:version docker:info; optional docker:journald for ServerError correlation; lookup docker_engine_versions.csv fields engine_version supported_until_date channel known_cves; sprawl_distinct_threshold=3; earliest=-24h@h latest=@h")`
| search index=oti_containers (sourcetype="docker:version" OR sourcetype="docker:info") earliest=-24h@h latest=@h
| eval host_id=lower(trim(toString(coalesce(host, Host, hostname, _HOSTNAME, host_id, dest, ""))))
| eval segment=trim(toString(coalesce(host_segment, segment, fleet_segment, datacenter_tier, availability_zone, pool, "unsegmented")))
| eval server_from_ver=trim(toString(coalesce(server_version, Server_Version, ServerVersion, "")))
| eval server_from_info=trim(toString(coalesce(ServerVersion, server_version, "")))
| eval sv_line=trim(toString(coalesce(server_from_ver, server_from_info, "")))
| eval api_line=trim(toString(coalesce(api_version, ApiVersion, APIVersion, Client_APIVersion, "")))
| eval cd_line=trim(toString(coalesce(containerd_version, ContainerdVersion, containerdVersion, "")))
| eval rc_line=trim(toString(coalesce(runc_version, RuncVersion, runcVersion, "")))
| eval kv_line=trim(toString(coalesce(kernel_version, KernelVersion, Server_KernelVersion, "")))
| eval bt_line=trim(toString(coalesce(Server_BuildTime, BuildTime, server_buildtime, "")))
| eval warn_blob=toString(coalesce(Warnings, warnings, ""))
| eval warn_lower=lower(warn_blob)
| eval warnings_count=if(sourcetype!="docker:info", null(), if(match(warn_blob,"^\s*\[\s*\]\s*$") OR len(trim(warn_blob))==0 OR warn_blob="null", 0, if(isnotnull(Warnings), mvcount(Warnings), if(match(warn_blob,"(?i)warning"), 1, 0))))
| eval warnings_summary=if(sourcetype!="docker:info", "", case(
    warnings_count==0 OR isnull(warnings_count), "none",
    match(warn_lower, "(?i)no memory limit|memory limit support|cgroup.*memory"), "memory_limit_support",
    match(warn_lower, "(?i)bridge-nf-call-iptables|iptables.*disabled|forbidden inter-container"), "netfilter_bridge",
    match(warn_lower, "(?i)deprecated"), "deprecation",
    true(), "other"))
| sort 0 + host_id, _time
| streamstats window=1 current=f last(sv_line) AS prev_sv BY host_id
| eval version_changed_recent=if(sourcetype=="docker:version" AND isnotnull(prev_sv) AND len(prev_sv)>0 AND len(sv_line)>0 AND sv_line!=prev_sv, 1, 0)
| stats 
    latest(sv_line) AS server_version
    latest(api_line) AS api_version
    latest(cd_line) AS containerd_version
    latest(rc_line) AS runc_version
    latest(kv_line) AS kernel_version
    latest(bt_line) AS server_buildtime
    latest(warnings_count) AS warnings_count
    latest(warnings_summary) AS warnings_summary
    latest(warn_lower) AS warn_lower_agg
    max(version_changed_recent) AS had_version_change_window
    latest(segment) AS segment
  BY host_id
| eval engine_key=trim(replace(replace(server_version, "\s*\(.*$", ""), "\s+ce\s*$", ""))
| join type=left max=0 engine_key
    [| inputlookup docker_engine_versions.csv
     | eval engine_key=trim(toString(engine_version))
     | eval supported_until_epoch=coalesce(
         strptime(trim(toString(supported_until_date)), "%Y-%m-%d"),
         strptime(trim(toString(supported_until_date)), "%m/%d/%Y"))
     | eval supported_until=strftime(supported_until_epoch, "%Y-%m-%d")
     | eval known_cves=toString(coalesce(known_cves, cve_list, ""))
     | eval patch_channel=toString(coalesce(channel, patch_channel, ""))
     | fields engine_key supported_until_epoch supported_until known_cves patch_channel ]
| fillnull value="" known_cves
| eval eol_in_prod=if(isnotnull(supported_until_epoch) AND supported_until_epoch>0 AND supported_until_epoch < relative_time(now(), "@d"), 1, 0)
| eval has_known_cve=if(match(lower(known_cves), "cve-20"), 1, 0)
| eval lookup_miss=if(len(trim(server_version))>0 AND (isnull(supported_until_epoch) OR supported_until_epoch==0), 1, 0)
| eval build_epoch=if(len(trim(server_buildtime))>0, coalesce(
    strptime(substr(trim(server_buildtime),1,19), "%Y-%m-%dT%H:%M:%S"),
    strptime(trim(server_buildtime), "%Y-%m-%d")), null())
| eval build_stale=if(isnotnull(build_epoch) AND build_epoch < relative_time(now(), "-400d@d"), 1, 0)
| eventstats dc(server_version) AS distinct_engine_versions_per_segment BY segment
| eval sprawl_flag=if(distinct_engine_versions_per_segment>3, 1, 0)
| eval sec_warn=if(warnings_count>=1 AND (match(warn_lower_agg, "(?i)no memory limit|memory limit support|cgroup") OR match(warn_lower_agg, "(?i)bridge-nf-call-iptables|iptables")), 1, 0)
| eval deprec_only=if(warnings_count>=1 AND sec_warn==0 AND match(warn_lower_agg, "(?i)deprecated"), 1, 0)
| eval severity=case(
    has_known_cve==1 AND lookup_miss==0, "critical_engine_known_cve_unpatched",
    eol_in_prod==1, "critical_engine_eol_in_production",
    sec_warn==1, "high_warnings_security_relevant",
    sprawl_flag==1, "high_engine_version_sprawl_segment_above_3",
    deprec_only==1 OR lookup_miss==1 OR (distinct_engine_versions_per_segment>=2 AND distinct_engine_versions_per_segment<=3), "medium_minor_version_drift",
    build_stale==1, "low_engine_buildtime_stale",
    warnings_count>=1, "high_warnings_security_relevant",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity=="critical_engine_known_cve_unpatched", "Freeze image promotion on the host class, attach Docker security bulletin and CISA KEV references to the change ticket, schedule emergency Engine patch to an approved build on the docker_engine_versions allowlist, validate containerd and runc pins in the same maintenance wave, and rerun docker version after reboot to close the audit finding.",
    severity=="critical_engine_eol_in_production", "Treat as compliance debt: pull the host segment into the next CAB-approved Engine upgrade train, document exception expiry, and block net-new production scheduling on the segment until Server.Version matches a supported_until_date row in docker_engine_versions.csv.",
    severity=="high_warnings_security_relevant", "Remediate kernel and cgroup configuration behind docker info Warnings: enable memory controller accounting or cgroup v2 delegation as required, restore bridge-nf-call-iptables where security policy expects firewall enforcement on container bridges, reboot only under change control, and resample docker:info to prove warnings_count returns to zero.",
    severity=="high_engine_version_sprawl_segment_above_3", "Collapse patch-channel sprawl: freeze ad-hoc package installs, repave hosts onto the golden Engine matrix (for example three approved minors), reconcile vendor mirrors so apt/yum pins cannot drift, and attach fleet-wide distinct_engine_versions_per_segment metrics to the quarterly governance review.",
    severity=="medium_minor_version_drift", "Schedule coordinated patch: align Server.Version to the nearest approved allowlist row, refresh docker_engine_versions.csv with vendor LTS rationale if the version is intentional, and separate deprecation-only warnings from security-relevant kernel gaps before downgrading severity.",
    severity=="low_engine_buildtime_stale", "Rebuild or restage the Engine package from a trusted artifact registry so Server.BuildTime is current, verify supply-chain attestation on the binary, and dismiss only after build_epoch matches a release built within policy window.",
    true(), "Review docker:version and docker:info side by side with optional docker:journald ServerError correlation; route to Head of Platform.")
| table host_id segment server_version api_version containerd_version runc_version kernel_version supported_until known_cves warnings_count warnings_summary severity recommended_response
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Inventory.os) AS inv_os FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=@h BY Inventory.dest
| rename Inventory.dest AS host_id
| join type=left max=0 host_id
    [| tstats summariesonly=t values(Vulnerabilities.cve) AS vuln_cves FROM datamodel=Vulnerabilities WHERE nodename=Vulnerabilities earliest=-24h@h latest=@h BY Vulnerabilities.dest
     | rename Vulnerabilities.dest AS host_id ]
| where len(host_id)>0
```

## Visualization

Engine version distribution pie chart with patch_channel coloring from docker_engine_versions.csv, CVE-affected hosts table sorted by severity, warnings_count histogram split zero versus non-zero, and distinct_engine_versions_per_segment trend with reference line at three distinct minors.

## Known False Positives

Canary segments that deliberately run one newer Engine minor on a fraction of hosts will trip sprawl or drift logic until you annotate host_segment or add exempt_sprawl metadata; this is expected and should be documented rather than muted. Vendor-locked LTS channels sometimes trail docker.com release notes by weeks while still being supported; if your allowlist row is missing, you will see lookup_miss until vulnerability management refreshes docker_engine_versions.csv even though finance signed the vendor exception. Freshly bootstrapped hosts can emit transient empty Server.Version rows for a single poll when dockerd starts slower than the scripted input; require two consecutive misses before paging. Engineers testing bleeding-edge nightly builds on lab hosts will appear as critical or medium rows until those hosts are tagged out of production segments. Hosts promoted from lab to prod without CMDB updates inherit stale segment labels, which distorts distinct_engine_versions_per_segment math until the next CMDB sync. Registry-mirror rebuilds can make Server.BuildTime look ancient relative to the image layer timestamps CI recorded, triggering low_engine_buildtime_stale until you compare package NEVRA from the OS package manager. Planned blue-green upgrades temporarily inflate medium_minor_version_drift when half the segment is mid-flight between two approved versions; pair alerts with deployment orchestration timestamps. Distro-specific package suffixes such as tilde ubuntu break naive string equality until you normalize engine_key. Duplicate CSV rows for the same engine_version create ambiguous known_cves text; dedupe during publish. Finally, remember UC-3.1.8 may show healthy journal streams while this UC still fires on semver debt, and UC-3.1.11 may show healthy FD ceilings while CVE rows remain critical.

## References

- [Docker Docs — Engine release notes](https://docs.docker.com/engine/release-notes/)
- [Docker Docs — Security](https://docs.docker.com/security/)
- [CIS Benchmarks — Docker](https://www.cisecurity.org/cis-benchmarks)
- [Splunk Lantern — Vulnerability detection data overview](https://lantern.splunk.com/Data_Descriptors/Vulnerability_detection_data)
- [Aqua Security — Mitigating Leaky Vessels (Moby, BuildKit, runc) guidance](https://www.aquasec.com/blog/mitigating-leaky-vessels-vulnerabilities-in-runc-buildkit-and-moby-with-aqua/)
- [CISA — Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
