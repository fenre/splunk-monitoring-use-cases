<!-- AUTO-GENERATED from UC-3.3.23.json — DO NOT EDIT -->

---
id: "3.3.23"
title: "OpenShift Console and API Access Forensics: Impersonation Detection, Privileged Action Velocity, Console Plugin Audit, and Bearer-Token Reuse Anomalies"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.23 · OpenShift Console and API Access Forensics: Impersonation Detection, Privileged Action Velocity, Console Plugin Audit, and Bearer-Token Reuse Anomalies

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We follow who touched the cluster control panel and the behind-the-scenes application programming surface, how fast they changed sensitive settings, whether someone is pretending to be someone else, and whether the same login token appears from two places at once.*

---

## Description

Correlates kube-apiserver and openshift-apiserver audit lanes with console-specific signals to surface impersonation chains, bursts of destructive verbs on sensitive resources, browser-driven console sessions and plugin lifecycle changes, bearer-token reuse proxies via distinct source addresses, legacy token markers, baseline authorization surprises, and administrative CIDR alignment for OpenShift 4.

## Value

OpenShift Console and API Access Forensics

## Implementation

Land ocp_audit and k8s_audit with kube apiserver audit JSON at sufficient depth for impersonation headers, subresources, and annotations; forward optional ocp_oauth_audit; publish audit_baseline.csv and approved_admin_cidrs.csv; save openshift_uc_3_3_23_console_api_access_forensics on fifteen minute cadence; route critical and high rows to platform security; archive weekly evidence exports with lookup commit hashes.

## Evidence

Saved search openshift_uc_3_3_23_console_api_access_forensics with fifteen minute schedule; versioned audit_baseline.csv and approved_admin_cidrs.csv in git; weekly CSV exports to a restricted evidence index; dashboard drilldowns on ocp_audit lanes.

## Control test

### Positive scenario

In a lab OpenShift cluster under change control, run an authorized oc impersonate exercise, perform a short burst of secret or binding mutations with a dedicated service account, install a test console plugin, and generate two source IP paths for the same principal through split proxies; ingest audit with annotations preserved and confirm openshift_uc_3_3_23_console_api_access_forensics returns critical or high rows with non-null recommended_action within the scheduled window.

### Negative scenario

After revoking test tokens, removing the test plugin, and restoring baselines with lookups updated, confirm severities return to low or informational and the alert wrapper emits zero rows when filtering to critical and high only per policy.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the OpenShift platform security lead, the identity engineers who operate the corporate identity provider integrated through OAuth, the Kubernetes authorization maintainers who interpret impersonation headers and selfsubjectrulesreview semantics, and the observability engineers who steward Splunk HTTP Event Collector tokens plus audit log forwarders from kube-apiserver, openshift-apiserver, and oauth-apiserver. This use case isolates the forensic signal plane around the OpenShift web console and the aggregated API audit streams: who exercised which verbs against which sensitive resources, from which client fingerprints and addresses, and how abruptly those patterns diverge from each identity baseline. UC-3.3.21 remains ClusterRole and ClusterRoleBinding drift governance with bundled role integrity and OAuth subject hygiene joins to periodic RBAC inventory. UC-3.3.22 remains Pod Security Admission enforcement outcomes, SCC interaction signatures, and namespace PSA label drift relative to approved_psa_baseline.csv. UC-3.2.23 remains vanilla Kubernetes cluster-admin ClusterRoleBinding escalation with k8s_cluster_admin_sa_allowlist.csv as the primary cluster-admin tier narrative. UC-3.3.14 remains OAuth server flow failures and identity provider backend errors rather than generalized privileged API velocity. Splunk becomes the tamper-resistant ledger that fuses impersonation headers and impersonatedUser bodies, five-minute velocity windows on destructive verbs against secrets, configmaps, bindings, token subresources, exec and port-forward paths, routes, OAuth clients, and clusteroperators, console.openshift.io console plugin install and update audit rows, browser user-agent correlated console route reads and interactive pod subresource use, bearer-token reuse proxies using distinct sourceIPs inside short windows, service account home-namespace mismatches on objectRef namespaces, legacy service account token annotations, authorization decisions that contradict governance baselines loaded from audit_baseline.csv, and coarse source IP alignment to approved_admin_cidrs.csv supernets per cluster.

Index and permission design land before field extraction. Designate index=ocp_audit for Kubernetes API audit v1 JSON forwarded from management clusters with sourcetype=ocp_audit or sourcetype=k8s_audit depending on whether you segregate OpenShift from vanilla Kubernetes estates. Forward openshift-apiserver audit into the same index when your collectors split streams; normalize cluster labels so openshift_cluster, cluster_name, and cluster keys coalesce predictably in SPL. Forward oauth-apiserver audit when your threat model includes OAuthClient mutations and OAuth token families correlated to apiserver principals. Issue distinct HEC tokens per environment with least privilege: platform security may search all sourcetypes; application teams receive filtered views that omit requestObject bodies when counsel requires minimization. Retention should cover at least thirty days hot for incident replay, ninety days when regulated customers require quarterly access attestations, and align cold storage with enterprise logging policy. Legal review should confirm corporate usernames, group names, partial userAgent strings, and source IP addresses are acceptable in Splunk.

RBAC and safety: collectors that tail kube-apiserver audit.log must run on control-plane hosts or consume cloud-provider audit exports with read-only service roles. Dedicated management-cluster collectors should use short-lived kubeconfig files rather than long-lived kubeadmin credentials on employee laptops. Analysts who replay oc adm must-gather bundles should import them into isolated lab indexes so production alerting cardinality is unaffected.

Audit policy depth: capture Metadata at minimum for high-volume read traffic on routes and console resources; capture RequestResponse or Request on create, update, patch, and delete for secrets, configmaps, rolebindings, clusterrolebindings, serviceaccounts token subresources, pods exec and attach and port-forward subresources, oauthclients, consoleplugins.console.openshift.io, operators.coreos.com subscriptions when your console YAML workflows touch them, config.openshift.io OAuth and KubeAPIServer and ClusterVersion objects, and clusteroperator rows when console-driven reconciliation is in scope. Include stage-level timestamps so RequestReceived without a timely ResponseComplete surfaces apiserver stalls. Preserve auditAnnotations.authentication.k8s.io/legacy-token when your Kubernetes minor emits it. Preserve annotations.authorization.k8s.io/decision when authorization webhooks and default RBAC combine.

Field normalization: flatten objectRef.apiGroup, objectRef.resource, objectRef.subresource, objectRef.namespace, objectRef.name, user.username, userAgent, verb, impersonatedUser.username, requestReceivedTimestamp, stageTimestamp, responseStatus.code, sourceIPs arrays, and nested annotations. If JSON paths arrive dotted versus flattened, coalesce() ladders in SPL still resolve when props.conf FIELDALIAS maps are maintained. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name.

Governance lookups: publish audit_baseline.csv in git with columns cluster, resource_expect or resource, verb_expect or verb, expect_deny or expect_deny_flag, and note or policy_note so joins flag allow decisions that violate written policy baselines. Publish approved_admin_cidrs.csv with cluster and allowed_cidr carrying a summarized management supernet or tightly scoped administrative CIDR used for cidrmatch() enrichment against mvindex(sourceIPs{},0). When geography is required for OAuth token reuse across autonomous systems, land MaxMind or Splunk iplocation output in a summary index keyed on cluster, identity, and five-minute buckets rather than expanding every raw audit row on every search.

Risk briefing: legitimate OpenShift upgrades and Operator Lifecycle Manager reconciliations create bursts of cluster-scoped writes that resemble attacks until you join ClusterVersion history and change_ticket_id metadata on HTTP Event Collector payloads. GitOps controllers reconciling secrets and configmaps can elevate priv_ct without malice. Penetration tests that impersonate users under authorization should be paired with pentest windows in lookup suppressions. Break-glass administrators using the console to patch OAuth or ClusterVersion should expect medium severity until tickets arrive.

Differentiation recap: console and API access forensics with impersonation chains, privileged-action velocity, console plugin and route session correlation, bearer-token reuse proxies, legacy token annotations, baseline decision surprises, and administrative CIDR alignment, not UC-3.3.21 RBAC drift inventory storytelling, not UC-3.3.22 PSA enforcement plane analytics, not UC-3.2.23 cluster-admin binding exclusivity.

Operational posture: align telemetry with change tickets by stamping change_ticket_id on HEC events when platform teams rotate OAuth serving certificates, reconcile console plugins, or execute privileged YAML edits against ClusterVersion or Subscription objects. When Splunk shows console bursts but corporate identity logs show no matching interactive logins, suspect stolen refresh tokens or shared break-glass credentials and escalate using the token_ip_reuse arm.

Fleet narrative: platform security leaders often need evidence that privileged console paths are monitored continuously, not only during annual access reviews. This saved search produces exportable rows suitable for audit packs when paired with lookup commit hashes and change tickets.

Selfsubjectrulesreview narrative: audits of selfsubjectrulesreview and selfsubjectaccessreviews should remain visible at Metadata or Request depth when your volume budget allows because they document what a principal believed it could do before attempting impersonation or mass edits. Pair those verbs with subsequent impersonation or binding mutations to tell a complete story.

OAuth and console correlation narrative: openshift-console sessions frequently mint OAuth access tokens that later appear as user.username values distinct from service account principals. Keep oauth-apiserver lanes available when you must prove whether two IP addresses in five minutes map to the same device posture or to impossible travel.

Long-lived token narrative: when service account secrets exceed organization rotation windows but still authenticate, combine legacy-token annotations with secret GET patterns to prioritize rotation debt without conflating the signal with short-lived projected tokens.

Plugin ContentSecurityPolicy narrative: console operators may surface ContentSecurityPolicy violations through separate ingress logs; route those violations into index=ocp_logs with shared cluster labels so analysts can pivot from consoleplugins mutations to edge telemetry.

Impossible travel narrative: exact-match impossible travel requires trusted geolocation fields; implement per-identity sliding windows in a summary index that stores previous city or country and compares velocity against great-circle distance divided by elapsed seconds, then join summaries back to this primary search on cluster and identity.

RequestReceived stall narrative: build a companion scheduled search that pairs RequestReceived stages to ResponseComplete by auditID and flags gaps longer than thirty seconds when your audit policy retains both stages; wire results into the same dashboard as this use case without duplicating the multisearch cost on every interactive query.

Console YAML edits narrative: successful patch or update verbs against subscriptions.operators.coreos.com, config.openshift.io OAuth or KubeAPIServer or ClusterVersion cluster-scoped objects, and similar console-editable surfaces should inherit higher scrutiny when userAgent matches browsers even if the actor is a cluster administrator, because browsers imply interactive humans rather than GitOps robots.

Reconcile-cluster-role-bindings narrative: oc adm policy reconcile-cluster-role-bindings style mutations appear as binding patches; when userAgent is not a known CI robot, elevate within priv_write_velocity using a lookup of automation_user_agent.csv you maintain beside audit_baseline.csv.

### Step 2 — Configure data collection

Stand up four complementary lanes Splunk multisearch can fuse: kube-apiserver and openshift-apiserver audit for impersonation headers and impersonatedUser bodies, the same audit streams filtered to destructive verbs on sensitive resources for five-minute velocity and seven-day z-score baselines per identity, console.openshift.io console plugin and browser-correlated console route and pod exec or port-forward traffic, and short-window distinct source IP counts per authenticated principal for token reuse proxies.

Audit lane primary: ship kube-apiserver audit.log and openshift-apiserver audit streams into index=ocp_audit with sourcetype=ocp_audit using Splunk Connect for Kubernetes filelog patterns, Splunk OpenTelemetry Collector filelog receiver, or cloud-audit exports that preserve Kubernetes audit v1 JSON. Ensure requestReceivedTimestamp maps to _time within thirty seconds of true apiserver time. Enable TLS to Splunk, rotate HEC tokens quarterly, and document which management cluster forwards lab versus production to prevent cluster label collisions.

OAuth audit lane: forward oauth-apiserver audit into index=ocp_audit with sourcetype=ocp_oauth_audit when you split streams; otherwise filter objectRef.apiGroup for oauth.openshift.io in SPL when OAuth client mutations matter for console authentication chains.

Console observability lane: where platform policy permits, ship openshift-console pod access logs and ingress edge logs for /api/console paths into index=ocp_logs with sourcetype=ocp_console_access so ContentSecurityPolicy violation reports and plugin backend health checks can corroborate audit rows. Redact secrets at collection.

Governance lookup lane: maintain audit_baseline.csv and approved_admin_cidrs.csv in the same repository as exception tickets so auditors can trace commit ancestry. Refresh summaries used for seven-day z-score baselines on a schedule that matches your risk appetite; the priv_write_velocity arm uses earliest=-7d@d to approximate the seven-day identity baseline inside the same saved search.

Example oc verification operators run during design reviews:

```bash
oc get console.operator.openshift.io cluster -o yaml | sed -n '1,160p'
oc get consoleplugin.console.openshift.io -A
oc get route -n openshift-console console -o yaml | sed -n '1,120p'
oc adm policy who-can impersonate users
```

props.conf guidance: TRUNCATE sufficiently large for RequestResponse bodies, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER for newline-delimited JSON audit files, and SEDCMD or transforms that strip tls.key-like patterns if misconfigured clients ever leak secrets.

Pre-save validation: index=ocp_audit earliest=-15m must return non-zero counts; intentional oc impersonate tests in lab should populate impersonatedUser or request headers in raw JSON; console plugin installs should emit console.openshift.io audit rows; approved_admin_cidrs.csv must parse with cluster keys matching audit cluster labels.

Dashboards: host a severity-colored table keyed on cluster and signal_lane with drilldowns to raw audit JSON, optional ocp_console_access rows, and lookup matches. Splunk Enterprise Security users may treat recommended_action as an adaptive response hint field without auto-remediation.

Volume controls: if RequestResponse audit is too heavy, keep RequestResponse for secret, binding, token, exec, port-forward, console plugin, and OAuth client resources only and use Metadata elsewhere, following OpenShift audit profile documentation.

Label consistency: enforce cluster naming conventions on HTTP Event Collector metadata so ocp_audit and ocp_logs share identical cluster keys for joins.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_23_console_api_access_forensics with a fifteen minute schedule during steady-state production, dispatch earliest=-24h@h for arms that must stay near-real-time, allow the priv_write_velocity arm to use earliest=-7d@d inside multisearch for baseline math, dispatch latest=now, and alert when severity is critical or high. Throttle duplicate cluster, signal_lane, identity rows for forty-five minutes unless severity escalates. Include recommended_action, lane_detail, and src_ip fields in pager descriptions so incident commanders open console and identity runbooks without rerunning ad hoc searches.

Pipeline narrative for reviewers: multisearch fans impersonation rows, privileged write velocity rows with streamstats time_window=5m and eventstats mean and standard deviation per identity, console UI plane rows, and token IP reuse rows. coalesce() absorbs flattened versus dotted JSON field naming drift across exporters. join wraps audit_baseline.csv on cluster, resource, and verb to compute policy_surprise when decisions allow actions your baseline marks as expect_deny. join wraps approved_admin_cidrs.csv to compute cidrmatch() alignment for management supernets. case() maps impersonation chains, token reuse, baseline surprises, velocity and z-score tiers, legacy token annotations, console plugin mutations, and administrative CIDR mismatches into severity tiers. recommended_action encodes kubectl and oc review steps, OAuth rotation guidance, and console plugin validation without pretending Splunk replaces platform tooling.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.23 OpenShift console and API access forensics — impersonation chains, privileged write velocity with five-minute windows, console or plugin plane touches, token and IP reuse. Join audit_baseline.csv and approved_admin_cidrs.csv. Tunables: vel_crit=40 z_crit=4 earliest=-24h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval lr=lower(_raw)
      | eval imp_user=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval tgt_user=trim(toString(coalesce('impersonatedUser.username', impersonatedUser_username, impersonatedUser.username, "")))
      | eval has_imp_hdr=if(match(lr,"impersonate-user|impersonate-group|impersonate-extra"),1,0)
      | eval has_imp_obj=if(len(tgt_user)>1 OR match(lr,"impersonateduser"),1,0)
      | where has_imp_hdr=1 OR has_imp_obj=1
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval user_agent=trim(toString(coalesce('userAgent', userAgent, user_agent, "")))
      | eval src_ip=trim(toString(coalesce(mvindex('sourceIPs{}',0), mvindex(sourceIPs,0), "")))
      | eval identity=coalesce(nullif(tgt_user,""), imp_user)
      | eval signal_lane="impersonation_forensics"
      | eval lane_detail=strcat("actor=",imp_user," target=",coalesce(tgt_user,"self")," apig=",apig)
      | eval priv_ct=0
      | eval dc_res_ns=0
      | eval ipdc_5m=0
      | eval token_lane=0
      | eval priv_z=0
      | eval legacy_tok=if(match(lr,"legacy-token\\\":\\\"true\\\"|authentication.k8s.io/legacy-token"),1,0)
      | eval req_decision=lower(trim(toString(coalesce('annotations."authorization.k8s.io/decision"', annotations_authorization_k8s_io_decision, ""))))
      | fields _time cluster signal_lane identity imp_user tgt_user verb res apig namespace obj user_agent src_ip lane_detail priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok req_decision ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval subres=lower(trim(toString(coalesce('objectRef.subresource', objectRef.subresource, objectRef_subresource, ""))))
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval identity=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval user_agent=trim(toString(coalesce('userAgent', userAgent, user_agent, "")))
      | eval src_ip=trim(toString(coalesce(mvindex('sourceIPs{}',0), mvindex(sourceIPs,0), "")))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | where match(verb,"create|update|patch|delete") AND (match(res,"secrets|configmaps|clusterrolebindings|rolebindings|serviceaccounts|routes|oauthclients|clusteroperators") OR (match(res,"^pods$") AND match(subres,"exec|attach|portforward")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | rex field=identity "^system:serviceaccount:(?<sa_ns>[^:]+):(?<sa_name>.+)$"
      | eval cross_ns_sa=if(len(sa_ns)>0 AND len(namespace)>0 AND sa_ns!=namespace,1,0)
      | sort 0 + cluster identity - _time
      | streamstats time_window=5m count AS priv_ct dc(verb) AS dc_v dc(res) AS dc_r dc(namespace) AS dc_ns BY cluster identity
      | eventstats avg(priv_ct) AS id_priv_avg stdev(priv_ct) AS id_priv_std BY identity
      | eval priv_z=if(isnotnull(id_priv_std) AND id_priv_std>0, round((priv_ct-id_priv_avg)/id_priv_std,3), 0)
      | eval signal_lane="priv_write_velocity"
      | eval lane_detail=strcat("dc_verb=",dc_v," dc_res=",dc_r," dc_ns=",dc_ns," z=",priv_z)
      | eval imp_user=identity
      | eval tgt_user=""
      | eval legacy_tok=0
      | eval req_decision=""
      | eval token_lane=cross_ns_sa
      | eval ipdc_5m=0
      | eval dc_res_ns=dc_ns
      | fields _time cluster signal_lane identity imp_user tgt_user verb res apig namespace obj user_agent src_ip lane_detail priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok req_decision ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval lr=lower(_raw)
      | eval ual=lower(trim(toString(coalesce('userAgent', userAgent, user_agent, ""))))
      | eval is_browser=if(match(ual,"mozilla|chrome|safari|edg"),1,0)
      | eval console_plugin=if(match(apig,"console.openshift.io") AND match(res,"consoleplugins"),1,0)
      | eval console_route=if(match(res,"^routes$") AND match(lr,"console") AND verb="get",1,0)
      | eval pod_exec_pf=if(match(res,"^pods$") AND match(verb,"create|get") AND match(lr,"/exec|/portforward|attach"),1,0)
      | where console_plugin=1 OR (console_route=1 AND is_browser=1) OR (pod_exec_pf=1 AND is_browser=1)
      | eval identity=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval src_ip=trim(toString(coalesce(mvindex('sourceIPs{}',0), mvindex(sourceIPs,0), "")))
      | eval user_agent=trim(toString(coalesce('userAgent', userAgent, user_agent, "")))
      | eval signal_lane="console_ui_plane"
      | eval lane_detail=case(console_plugin=1,"console_plugin_change", console_route=1,"console_route_session", true(),"console_pod_exec_or_portforward")
      | eval imp_user=identity
      | eval tgt_user=""
      | eval priv_ct=0
      | eval priv_z=0
      | eval dc_res_ns=0
      | eval ipdc_5m=0
      | eval token_lane=0
      | eval legacy_tok=0
      | eval req_decision=""
      | fields _time cluster signal_lane identity imp_user tgt_user verb res apig namespace obj user_agent src_ip lane_detail priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok req_decision ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval identity=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval src_ip=trim(toString(coalesce(mvindex('sourceIPs{}',0), mvindex(sourceIPs,0), "")))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval user_agent=trim(toString(coalesce('userAgent', userAgent, user_agent, "")))
      | where len(src_ip)>6 AND len(identity)>2
      | sort 0 + cluster identity - _time
      | streamstats time_window=5m dc(src_ip) AS ipdc_5m values(src_ip) AS ips_seen BY cluster identity
      | where ipdc_5m>=2
      | eval signal_lane="token_ip_reuse"
      | eval lane_detail=strcat("distinct_ips=",ipdc_5m," values=",ips_seen)
      | eval imp_user=identity
      | eval tgt_user=""
      | eval priv_ct=0
      | eval priv_z=0
      | eval dc_res_ns=0
      | eval token_lane=1
      | eval legacy_tok=0
      | eval req_decision=""
      | fields _time cluster signal_lane identity imp_user tgt_user verb res apig namespace obj user_agent src_ip lane_detail priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok req_decision ]
| eval cluster=coalesce(nullif(cluster,""),"unknown_cluster")
| fillnull value="" res verb req_decision baseline_note allowed_cidr
| fillnull value=0 priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok
| eval src_ip=trim(toString(coalesce(src_ip,"")))
| join type=left max=0 cluster res verb
    [| inputlookup audit_baseline.csv
     | eval cluster=lower(trim(toString(cluster)))
     | eval res=lower(trim(toString(coalesce(resource_expect, resource, res_expect, ""))))
     | eval verb=lower(trim(toString(coalesce(verb_expect, verb, ""))))
     | eval expect_deny=tonumber(trim(toString(coalesce(expect_deny, expect_deny_flag, "0"))),10)
     | eval baseline_note=trim(toString(coalesce(note, policy_note, "")))
     | fields cluster res verb expect_deny baseline_note ]
| join type=left max=1 cluster
    [| inputlookup approved_admin_cidrs.csv
     | eval cluster=lower(trim(toString(cluster)))
     | fields cluster allowed_cidr ]
| fillnull value=0 expect_deny
| fillnull value="" baseline_note allowed_cidr
| eval decision_allow=if(len(req_decision)<1 OR match(req_decision,"allow"),1,0)
| eval policy_surprise=if(decision_allow=1 AND expect_deny=1,1,0)
| eval cidr_ok=if(len(allowed_cidr)<3 OR len(src_ip)<7, -1, if(cidrmatch(allowed_cidr, src_ip), 1, 0))
| eval severity=case(
    signal_lane=="impersonation_forensics" AND match(imp_user,"system:serviceaccount") AND len(tgt_user)>1, "critical",
    signal_lane=="token_ip_reuse" AND token_lane=1, "critical",
    policy_surprise=1, "critical",
    signal_lane=="priv_write_velocity" AND priv_ct>=40 AND priv_z>=4, "high",
    signal_lane=="priv_write_velocity" AND priv_ct>=25, "high",
    legacy_tok=1, "high",
    signal_lane=="console_ui_plane" AND match(lane_detail,"console_plugin"), "high",
    len(allowed_cidr)>3 AND cidr_ok=0 AND match(identity,"admin"), "high",
    signal_lane=="impersonation_forensics", "medium",
    signal_lane=="console_ui_plane", "medium",
    true(), "low")
| eval recommended_action=case(
    severity=="critical" AND signal_lane=="token_ip_reuse", "revoke_sessions_rotate_tokens_correlate_idp_and_network_firewall",
    severity=="critical" AND policy_surprise=1, "review_authorization_webhook_order_and_audit_policy_expectations",
    signal_lane=="impersonation_forensics", "capture_impersonation_headers_review_rbac_impersonate_rights",
    signal_lane=="priv_write_velocity", "timeline_cluster_mutations_restore_from_backup_if_unauthorized",
    signal_lane=="console_ui_plane", "validate_console_plugins_and_routes_review_csp_reports",
    true(), "correlate_to_change_ticket_and_identity_provider_signin_logs")
| table _time cluster signal_lane severity identity imp_user tgt_user src_ip user_agent verb res namespace obj lane_detail priv_ct priv_z dc_res_ns ipdc_5m legacy_tok cidr_ok expect_deny policy_surprise recommended_action baseline_note
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_23_console_api_access_forensics_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform-security@example.com
action.email.subject = OCP console and API forensics $result.severity$ $result.cluster$ $result.signal_lane$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_23_console_api_access_forensics | where severity IN ("critical","high")
```

Performance: if Job Inspector shows multisearch queue time above internal service level objectives, materialize the priv_write_velocity arm hourly into a summary index keyed on cluster and identity, widen alert searches to earliest=-6h@h on summaries, and retain this full search for investigations. For Splunk Enterprise Security, use the closing table as a correlation search feeding a notable template with cluster and identity as assets.

SPL tuning: expand admin identity match lists when your directory naming standards differ; keep audit_baseline.csv authoritative rather than embedding hundreds of resources in case(). Expand approved_admin_cidrs.csv to multiple rows per cluster when you must list several supernets, knowing max=1 join keeps only the first row unless you pre-stats the lookup into one summarized field outside this template.

### Step 4 — Validate

Ground truth always starts on-cluster. For impersonation rows surfaced in Splunk, compare user.username, impersonatedUser.username, and request headers captured in audit storage to oc adm policy who-can impersonate users and subjectaccessreview outcomes for the impersonator. When headers disagree with Splunk extracts, verify FIELDALIAS maps and duplicate forwarders before blaming analysts.

Privileged velocity validation: pick a high priv_ct window, run oc get secrets or oc get clusterrolebinding against the same second using change tickets, and confirm automation actors explain the burst. When z-score spikes appear, verify the seven-day window is not polluted by upgrade maintenance that skipped lookup annotations.

Console plane validation: confirm console plugin installs in audit match oc get consoleplugin and that browser user-agent correlated exec rows align with console network policies and egress proxies.

Token reuse validation: compare distinct sourceIPs in Splunk to corporate reverse proxy logs and identity provider sign-in logs for the same principal. When geography enrichment is enabled, validate impossible travel math against VPN concentrator addresses before paging executives.

Baseline surprise validation: when policy_surprise fires, confirm audit_baseline.csv expect_deny rows still reflect counsel-approved policy and that webhook ordering explains allows rather than silent RBAC expansion.

CIDR validation: confirm approved_admin_cidrs.csv supernets still cover jump hosts and bastions after network architecture changes.

Negative test: after revoking test tokens and restoring baselines, confirm severities return to low or informational and the alert wrapper emits zero rows when filtering to critical and high only per policy.

Clock skew test: indexer time within thirty seconds of apiserver; otherwise streamstats time windows mis-order events.

Parser drift test: after OpenShift minor upgrades, validate nested annotation field names for authorization decisions and legacy token markers.

RBAC test: readers without ocp_audit role must see zero rows.

Privacy test: requestObject bodies should not land in developer-shared indexes when they disclose secrets; redact at collection.

Correlation test: pair timelines with UC-3.3.14 only when OAuth server outages coincide with console bursts; this use case should still emit console rows without requiring OAuth metrics.

Synthetic impersonation: in lab under change control, run kubectl or oc impersonate against a dedicated test user and confirm impersonation_forensics classification within one scheduled window.

Synthetic token reuse: in lab, authenticate the same principal through two distinct egress IPs within five minutes using approved split-horizon tests and confirm token_ip_reuse rows, then document proxy metadata to avoid production false positives.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Service account impersonating an interactive user: Trigger: impersonation_forensics rows where imp_user matches system:serviceaccount and tgt_user matches a corporate principal without a recorded break-glass ticket. Investigate: pull raw audit JSON for Impersonate-User headers, chain to selfsubjectrulesreview or subjectaccessreview audit if present, and compare to RBAC impersonate rights. Who to involve: platform security, identity operations, and the service owner for the calling namespace. Remediate: remove unnecessary impersonate grants, rotate service account tokens implicated in the chain, and isolate workloads that require human delegation until architecture review completes. Validate: oc who-can impersonate users shows tightened rights, Splunk clears critical severity for two windows, and identity provider sign-in logs show no unexplained parallel sessions.

Case 2 — Chained impersonation across two hops: Trigger: lane_detail shows nested impersonation context or paired auditIDs where the first hop is a controller account and the second hop presents a human username. Investigate: map auditID sequences, request URIs, and userAgent stability across hops. Who to involve: incident commander, Kubernetes authorization engineers, and Splunk observability owners if timestamps skew. Remediate: break the chain at the weakest impersonate binding, revoke tokens, and patch automation that stacks impersonation without guardrails. Validate: replay tests in lab no longer produce chained impersonatedUser bodies without explicit approval metadata.

Case 3 — Privileged-action velocity storm on secrets and bindings: Trigger: priv_write_velocity with priv_ct above threshold and elevated priv_z. Investigate: sort mutations by _time, join GitOps commits, and compare actor service accounts to known controllers. Who to involve: platform on-call, application teams when actors are tenant service accounts, and information security if actors are unfamiliar. Remediate: freeze automation credentials if malicious, restore objects from trusted backups if integrity fails, and tighten GitOps deploy roles if benign but noisy. Validate: velocity decays to baseline, z-score returns toward zero, and change records explain the burst.

Case 4 — Console plugin install without change record: Trigger: console_ui_plane with console_plugin_change and no matching change_ticket_id on HEC metadata. Investigate: oc get consoleplugin, review plugin manifests for external script sources, and scan ingress logs for ContentSecurityPolicy violations. Who to involve: platform security and console operator maintainers. Remediate: remove unapproved plugins, restore known-good console operator configuration, and document exceptions with expiry. Validate: console operator reports healthy state, Splunk shows no new plugin mutations without tickets, and users confirm expected console features.

Case 5 — Browser pod exec versus oc CLI exec: Trigger: console_pod_exec_or_portforward with browser user-agent patterns. Investigate: correlate to Route and OAuth session establishment, review namespace RBAC for pods exec, and confirm business justification for interactive shells. Who to involve: application owner and platform security. Remediate: replace interactive shells with debug tooling that preserves attestations, or narrow RoleBindings when abuse is suspected. Validate: repeat searches show only expected break-glass windows with tickets.

Case 6 — Token IP reuse inside five minutes: Trigger: token_ip_reuse with ipdc_5m greater than or equal to two. Investigate: compare ips_seen to corporate geo and ASN feeds, check for split-horizon proxies, and hunt for parallel OAuth grants. Who to involve: identity operations and network security. Remediate: revoke refresh tokens, force step-up authentication, and block suspicious egress if internal tooling confirms theft. Validate: distinct IP counts fall to one for steady sessions, and identity provider risk scores normalize.

Case 7 — Service account token used outside home namespace: Trigger: token_lane or cross-namespace signals in priv_write_velocity arm for system:serviceaccount principals. Investigate: confirm objectRef.namespace differs from parsed sa_ns using oc describe and audit bodies. Who to involve: application platform engineering and security operations. Remediate: replace cluster-scoped automation misuse with namespaced RoleBindings, rotate tokens, and enforce namespace-scoped secrets access. Validate: repeated API calls show aligned namespaces or documented cluster-scoped exceptions.

Case 8 — Legacy service account token still present: Trigger: legacy_tok equals one on audit annotations. Investigate: identify controllers and users still mounting long-lived secrets, map rotation deadlines, and compare to Kubernetes bound service account token guidance. Who to involve: platform lifecycle engineers and workload owners. Remediate: migrate workloads to time-bounded tokens, remove legacy secret mounts, and restart offenders after rotation. Validate: legacy annotation rate trends to zero, and kubelet secret volume metrics align.

Case 9 — Baseline surprise allow on governed resources: Trigger: policy_surprise equals one after audit_baseline.csv join. Investigate: validate webhook ordering, confirm whether deny was expected due to organizational policy, and compare to live ValidatingWebhookConfiguration. Who to involve: policy engineering and GRC counsel when interpretations differ. Remediate: fix webhook failures, tighten RBAC, or update baseline CSV under formal change when policy changes. Validate: replay shows deny or updated baseline commits with hashes recorded in evidence.

Case 10 — Administrative source IP outside approved supernet: Trigger: high severity with cidr_ok equals zero and allowed_cidr populated. Investigate: confirm whether the session crossed a new bastion, compare to approved_admin_cidrs.csv version, and gather VPN logs. Who to involve: network operations and privileged access management. Remediate: update CIDR inventory after architecture changes or block addresses that are truly foreign. Validate: cidrmatch returns one for authorized paths and Splunk noise drops.

Case 11 — Audit stage stall longer than thirty seconds: Trigger: companion hunt shows RequestReceived without ResponseComplete for identical auditID beyond internal latency budgets. Investigate: correlate to apiserver load, etcd latency, and control-plane node health. Who to involve: platform SRE and vendor support when stalls cluster. Remediate: scale apiservers, fix etcd, or patch known defects per release notes. Validate: stage pairing returns to normal latency and hunt searches go quiet.

Closing checklist: five em-dash step headers are present; Step 3 fenced SPL matches the spl field exactly; multisearch lists impersonation, privileged velocity, console UI, and token IP reuse arms; join wraps audit_baseline.csv and approved_admin_cidrs.csv; coalesce, streamstats, eventstats, and case appear; closing table includes _time, cluster, signal_lane, severity, identity, imp_user, tgt_user, src_ip, user_agent, verb, res, namespace, obj, lane_detail, priv_ct, priv_z, dc_res_ns, ipdc_5m, legacy_tok, cidr_ok, expect_deny, policy_surprise, recommended_action, and baseline_note for analyst review.


## SPL

```spl
`comment("UC-3.3.23 OpenShift console and API access forensics — impersonation chains, privileged write velocity with five-minute windows, console or plugin plane touches, token and IP reuse. Join audit_baseline.csv and approved_admin_cidrs.csv. Tunables: vel_crit=40 z_crit=4 earliest=-24h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval lr=lower(_raw)
      | eval imp_user=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval tgt_user=trim(toString(coalesce('impersonatedUser.username', impersonatedUser_username, impersonatedUser.username, "")))
      | eval has_imp_hdr=if(match(lr,"impersonate-user|impersonate-group|impersonate-extra"),1,0)
      | eval has_imp_obj=if(len(tgt_user)>1 OR match(lr,"impersonateduser"),1,0)
      | where has_imp_hdr=1 OR has_imp_obj=1
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval user_agent=trim(toString(coalesce('userAgent', userAgent, user_agent, "")))
      | eval src_ip=trim(toString(coalesce(mvindex('sourceIPs{}',0), mvindex(sourceIPs,0), "")))
      | eval identity=coalesce(nullif(tgt_user,""), imp_user)
      | eval signal_lane="impersonation_forensics"
      | eval lane_detail="actor=".imp_user." target=".coalesce(tgt_user,"self")." apig=".apig
      | eval priv_ct=0
      | eval dc_res_ns=0
      | eval ipdc_5m=0
      | eval token_lane=0
      | eval priv_z=0
      | eval legacy_tok=if(match(lr,"legacy-token\\\":\\\"true\\\"|authentication.k8s.io/legacy-token"),1,0)
      | eval req_decision=lower(trim(toString(coalesce('annotations."authorization.k8s.io/decision"', annotations_authorization_k8s_io_decision, ""))))
      | fields _time cluster signal_lane identity imp_user tgt_user verb res apig namespace obj user_agent src_ip lane_detail priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok req_decision ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval subres=lower(trim(toString(coalesce('objectRef.subresource', objectRef.subresource, objectRef_subresource, ""))))
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval identity=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval user_agent=trim(toString(coalesce('userAgent', userAgent, user_agent, "")))
      | eval src_ip=trim(toString(coalesce(mvindex('sourceIPs{}',0), mvindex(sourceIPs,0), "")))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | where match(verb,"create|update|patch|delete") AND (match(res,"secrets|configmaps|clusterrolebindings|rolebindings|serviceaccounts|routes|oauthclients|clusteroperators") OR (match(res,"^pods$") AND match(subres,"exec|attach|portforward")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | rex field=identity "^system:serviceaccount:(?<sa_ns>[^:]+):(?<sa_name>.+)$"
      | eval cross_ns_sa=if(len(sa_ns)>0 AND len(namespace)>0 AND sa_ns!=namespace,1,0)
      | sort 0 + cluster identity - _time
      | streamstats time_window=5m count AS priv_ct dc(verb) AS dc_v dc(res) AS dc_r dc(namespace) AS dc_ns BY cluster identity
      | eventstats avg(priv_ct) AS id_priv_avg stdev(priv_ct) AS id_priv_std BY identity
      | eval priv_z=if(isnotnull(id_priv_std) AND id_priv_std>0, round((priv_ct-id_priv_avg)/id_priv_std,3), 0)
      | eval signal_lane="priv_write_velocity"
      | eval lane_detail="dc_verb=".dc_v." dc_res=".dc_r." dc_ns=".dc_ns." z=".priv_z
      | eval imp_user=identity
      | eval tgt_user=""
      | eval legacy_tok=0
      | eval req_decision=""
      | eval token_lane=cross_ns_sa
      | eval ipdc_5m=0
      | eval dc_res_ns=dc_ns
      | fields _time cluster signal_lane identity imp_user tgt_user verb res apig namespace obj user_agent src_ip lane_detail priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok req_decision ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval lr=lower(_raw)
      | eval ual=lower(trim(toString(coalesce('userAgent', userAgent, user_agent, ""))))
      | eval is_browser=if(match(ual,"mozilla|chrome|safari|edg"),1,0)
      | eval console_plugin=if(match(apig,"console.openshift.io") AND match(res,"consoleplugins"),1,0)
      | eval console_route=if(match(res,"^routes$") AND match(lr,"console") AND verb="get",1,0)
      | eval pod_exec_pf=if(match(res,"^pods$") AND match(verb,"create|get") AND match(lr,"/exec|/portforward|attach"),1,0)
      | where console_plugin=1 OR (console_route=1 AND is_browser=1) OR (pod_exec_pf=1 AND is_browser=1)
      | eval identity=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval src_ip=trim(toString(coalesce(mvindex('sourceIPs{}',0), mvindex(sourceIPs,0), "")))
      | eval user_agent=trim(toString(coalesce('userAgent', userAgent, user_agent, "")))
      | eval signal_lane="console_ui_plane"
      | eval lane_detail=case(console_plugin=1,"console_plugin_change", console_route=1,"console_route_session", true(),"console_pod_exec_or_portforward")
      | eval imp_user=identity
      | eval tgt_user=""
      | eval priv_ct=0
      | eval priv_z=0
      | eval dc_res_ns=0
      | eval ipdc_5m=0
      | eval token_lane=0
      | eval legacy_tok=0
      | eval req_decision=""
      | fields _time cluster signal_lane identity imp_user tgt_user verb res apig namespace obj user_agent src_ip lane_detail priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok req_decision ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval identity=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval src_ip=trim(toString(coalesce(mvindex('sourceIPs{}',0), mvindex(sourceIPs,0), "")))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval user_agent=trim(toString(coalesce('userAgent', userAgent, user_agent, "")))
      | where len(src_ip)>6 AND len(identity)>2
      | sort 0 + cluster identity - _time
      | streamstats time_window=5m dc(src_ip) AS ipdc_5m values(src_ip) AS ips_seen BY cluster identity
      | where ipdc_5m>=2
      | eval signal_lane="token_ip_reuse"
      | eval lane_detail="distinct_ips=".ipdc_5m." values=".ips_seen
      | eval imp_user=identity
      | eval tgt_user=""
      | eval priv_ct=0
      | eval priv_z=0
      | eval dc_res_ns=0
      | eval token_lane=1
      | eval legacy_tok=0
      | eval req_decision=""
      | fields _time cluster signal_lane identity imp_user tgt_user verb res apig namespace obj user_agent src_ip lane_detail priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok req_decision ]
| eval cluster=coalesce(nullif(cluster,""),"unknown_cluster")
| fillnull value="" res verb req_decision baseline_note allowed_cidr
| fillnull value=0 priv_ct priv_z dc_res_ns ipdc_5m token_lane legacy_tok
| eval src_ip=trim(toString(coalesce(src_ip,"")))
| join type=left max=0 cluster res verb
    [| inputlookup audit_baseline.csv
     | eval cluster=lower(trim(toString(cluster)))
     | eval res=lower(trim(toString(coalesce(resource_expect, resource, res_expect, ""))))
     | eval verb=lower(trim(toString(coalesce(verb_expect, verb, ""))))
     | eval expect_deny=tonumber(trim(toString(coalesce(expect_deny, expect_deny_flag, "0"))),10)
     | eval baseline_note=trim(toString(coalesce(note, policy_note, "")))
     | fields cluster res verb expect_deny baseline_note ]
| join type=left max=1 cluster
    [| inputlookup approved_admin_cidrs.csv
     | eval cluster=lower(trim(toString(cluster)))
     | fields cluster allowed_cidr ]
| fillnull value=0 expect_deny
| fillnull value="" baseline_note allowed_cidr
| eval decision_allow=if(len(req_decision)<1 OR match(req_decision,"allow"),1,0)
| eval policy_surprise=if(decision_allow=1 AND expect_deny=1,1,0)
| eval cidr_ok=if(len(allowed_cidr)<3 OR len(src_ip)<7, -1, if(cidrmatch(allowed_cidr, src_ip), 1, 0))
| eval severity=case(
    signal_lane=="impersonation_forensics" AND match(imp_user,"system:serviceaccount") AND len(tgt_user)>1, "critical",
    signal_lane=="token_ip_reuse" AND token_lane=1, "critical",
    policy_surprise=1, "critical",
    signal_lane=="priv_write_velocity" AND priv_ct>=40 AND priv_z>=4, "high",
    signal_lane=="priv_write_velocity" AND priv_ct>=25, "high",
    legacy_tok=1, "high",
    signal_lane=="console_ui_plane" AND match(lane_detail,"console_plugin"), "high",
    len(allowed_cidr)>3 AND cidr_ok=0 AND match(identity,"admin"), "high",
    signal_lane=="impersonation_forensics", "medium",
    signal_lane=="console_ui_plane", "medium",
    true(), "low")
| eval recommended_action=case(
    severity=="critical" AND signal_lane=="token_ip_reuse", "revoke_sessions_rotate_tokens_correlate_idp_and_network_firewall",
    severity=="critical" AND policy_surprise=1, "review_authorization_webhook_order_and_audit_policy_expectations",
    signal_lane=="impersonation_forensics", "capture_impersonation_headers_review_rbac_impersonate_rights",
    signal_lane=="priv_write_velocity", "timeline_cluster_mutations_restore_from_backup_if_unauthorized",
    signal_lane=="console_ui_plane", "validate_console_plugins_and_routes_review_csp_reports",
    true(), "correlate_to_change_ticket_and_identity_provider_signin_logs")
| table _time cluster signal_lane severity identity imp_user tgt_user src_ip user_agent verb res namespace obj lane_detail priv_ct priv_z dc_res_ns ipdc_5m legacy_tok cidr_ok expect_deny policy_surprise recommended_action baseline_note

```

## CIM SPL

```spl
| tstats summariesonly=t latest(Authentication.user) AS auth_user latest(Authentication.src) AS auth_src FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=now BY Authentication.dest
| rename Authentication.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=t latest(Change.action) AS chg_action latest(Change.object) AS chg_object latest(Change.user) AS chg_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
     | rename Change.dest AS cim_dest ]
| where like(lower(chg_object), "%secret%") OR like(lower(chg_object), "%clusterrolebinding%") OR match(lower(auth_user), "system:serviceaccount")
| table cim_dest auth_user auth_src chg_action chg_object chg_user
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timeline of priv_ct and priv_z by identity; map of src_ip rarity; drilldown from signal_lane to raw audit JSON; console plugin inventory panel keyed on cluster.

## Known False Positives

OpenShift upgrades and operator reconciliations emit bursts of cluster-scoped writes that resemble attacks until joined to ClusterVersion history and change windows. GitOps controllers and backup operators mutate secrets and configmaps rapidly with benign intent; tune priv_ct thresholds using automation_actor metadata. Corporate reverse proxies and split-horizon DNS can make token_ip_reuse fire when a single user crosses two edge addresses; confirm proxy topology before paging identity teams. Browser user-agent matches are heuristic; headless Chromium in CI may resemble consoles unless you join pipeline identities. cidrmatch against a single management supernet per cluster will flag legitimate travel through new bastions after network moves until approved_admin_cidrs.csv refreshes. audit_baseline.csv surprises may reflect intentional policy changes not yet committed to git; avoid critical routing until GRC confirms drift. Seven-day z-scores inside multisearch still inherit maintenance spikes; pair with upgrade freeze lookups. Duplicate HEC shipments double counts; dedupe on auditID when present. Penetration tests and red-team impersonation exercises should carry pentest lookup windows. Some managed offerings redact portions of audit bodies; expect partial nulls in impersonation extracts and validate with vendor guidance.

## References

- [OpenShift Documentation — Viewing audit logs](https://docs.openshift.com/container-platform/latest/security/audit-log-view.html)
- [OpenShift Documentation — Configuring the audit log policy](https://docs.openshift.com/container-platform/latest/security/audit-log-policy-config.html)
- [Kubernetes Documentation — Auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [Kubernetes Documentation — Authenticating — User impersonation](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#user-impersonation)
- [Red Hat Documentation — OpenShift Container Platform](https://docs.redhat.com/en/documentation/openshift_container_platform/)
- [OpenShift Console repository](https://github.com/openshift/console)
- [OpenShift API — console v1 console plugin types](https://github.com/openshift/api/blob/master/console/v1/types_console_plugin.go)
- [Red Hat Blog — Pod Security Admission in OpenShift 4.11](https://www.redhat.com/en/blog/pod-security-admission-in-openshift-4.11)
