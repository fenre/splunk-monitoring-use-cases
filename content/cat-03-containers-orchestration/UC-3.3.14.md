<!-- AUTO-GENERATED from UC-3.3.14.json — DO NOT EDIT -->

---
id: "3.3.14"
title: "OpenShift OAuth Server Authentication Flow Failures, IdP Backend Errors, and Token-Lifecycle Anomalies"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.14 · OpenShift OAuth Server Authentication Flow Failures, IdP Backend Errors, and Token-Lifecycle Anomalies

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the cluster sign-in doorway and its connections to your corporate login systems. When sign-in starts failing in waves, when the cluster cannot talk to your login provider, or when account records change too fast, we raise a clear signal so teams fix it before people are locked out.*

---

## Description

Detects OpenShift integrated OAuth server login flow failures and identity provider backend errors across LDAP, OpenID Connect, GitHub, GitLab, Google, RequestHeader, htpasswd, BasicAuth, and Keystone configurations by correlating oauth server and apiserver audit streams, authentication-related Kubernetes events, oauth-openshift edge telemetry, Prometheus counters such as oauth_authentication_request_total and oauth_apiserver_request_total, optional apiserver_request_total grouped to oauth.openshift.io, token issuance velocity anomalies via streamstats, User and Identity API churn in user.openshift.io audit, and optional authentication ClusterOperator degradation strictly as a corroborating hint rather than the primary signal.

## Value

Identity and platform leaders shorten mean time to restore console and oc login when external IdP incidents, OAuth configuration drift, or token issuance anomalies would otherwise scatter evidence across control-plane nodes, metrics silos, and help-desk tickets. Security governance gains continuous narrative that interactive authentication stayed observable across provider rotations, certificate reloads, and workforce changes without conflating the story with SCC admission denials, generic RBAC permission drift, admission webhook failures, or cluster-admin binding escalation timelines covered by sibling use cases.

## Implementation

Land ocp_oauth_server_audit, ocp_oauth_apiserver_audit, ocp_audit, ocp_events, and ocp_oauth into governed indexes with cluster and idp labels; federate oauth_authentication_request_total, oauth_apiserver_request_total, and apiserver_request_total with group oauth.openshift.io into ocp_metrics; normalize user.openshift.io audit fields in props; save openshift_uc_3_3_14_oauth_server_flow_health on fifteen minute cadence over earliest=-6h@h; route page and warn to identity platform on-call via Splunk OpenShift App alerts; archive weekly CSV exports for access governance.

## Evidence

Saved search openshift_uc_3_3_14_oauth_server_flow_health with fifteen minute schedule; Splunk OpenShift App dashboard drilldowns on ocp_oauth_server_audit, ocp_oauth_apiserver_audit, ocp_audit, ocp_events, ocp_oauth, and ocp_metrics lanes; weekly CSV exports to a restricted evidence index with change_ticket_id correlation.

## Control test

### Positive scenario

In a lab OpenShift cluster, misconfigure a test LDAP identity provider to an unreachable host or supply invalid bind credentials, attempt oc login until AuthenticationFailed or IdentityProviderConfigError events appear in ocp_events with matching oauth audit or oauth-openshift log extracts, ingest prometheus error samples on oauth_authentication_request_total, and confirm openshift_uc_3_3_14_oauth_server_flow_health returns warn or page with non-null recommended_action within the scheduled window.

### Negative scenario

After restoring a working identity provider configuration with clean interactive login, stable oauth_authentication_request_total error rates near zero, and Identity churn at baseline, confirm severities return to info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift identity and access management engineering lead, the corporate directory services team that operates upstream LDAP or OpenID Connect endpoints, and the observability engineers who steward Splunk HTTP Event Collector tokens plus OpenTelemetry Collector agents that forward control-plane logs and federated Prometheus from OpenShift Monitoring. This use case isolates the OpenShift integrated OAuth server data plane: the oauth-openshift Deployment in namespace openshift-authentication that terminates browser and oc login flows at routes such as https://oauth-openshift.apps.<cluster>/oauth/authorize and related /oauth paths, the authentication.config.openshift.io cluster OAuth configuration surface exposed by oc get oauth cluster -o yaml, IdentityProvider stanzas under spec.identityProviders that declare LDAP, OpenID, GitHub, GitLab, Google, RequestHeader, htpasswd, BasicAuth, and Keystone integration shapes, and the aggregated oauth.openshift.io API group that serves user.openshift.io resources including User and Identity objects reconciled from successful logins. UC-3.3.6 remains ClusterOperator-level reconciliation for the authentication operator: Available, Progressing, Degraded, and Upgradeable semantics on the clusteroperator.authentication row are a corroborating lane here, not the primary analytic axis. UC-3.3.4 remains Security Context Constraint admission outcomes and openshift.io/scc annotation truth on Pods. UC-3.2.12 remains Kubernetes RBAC permission anomalies on Roles and ClusterRoles such as escalate, bind, or wildcard resource rules. UC-3.2.40 remains admission webhook failure modes at the admission review layer. UC-3.2.23 remains ClusterRoleBinding grants of cluster-admin and other cluster-scoped binding tampering narratives. This UC does not replace vanilla kube-apiserver authentication latency analytics that ignore OAuth-specific flow stages, generic workload OAuth clients for first-party applications outside the cluster ingress auth stack, or CIS benchmark host-level sshd hardening reviews.

Operational scope emphasizes per-provider login flow telemetry: flow stages labeled start, code, token, userinfo, and groups for correlation across browser redirects, authorization code exchange, access token issuance, user info retrieval, and group synchronization where the IdP integration supports it. Identity provider connection failures include LDAP bind errors against corporate directory partitions, OpenID Connect discovery document retrieval returning HTTP 5xx, GitHub.com or GitHub Enterprise rate-limit responses surfaced to oauth-openshift, missing or freshly rotated htpasswd-backed Secrets referenced from the OAuth CR, RequestHeader misalignment between the edge authenticating proxy and oauth-openshift trust configuration, and Keystone integration failures in environments that wire OpenStack identity. Token lifecycle anomalies include sudden drops or surges in oauth-apiserver token grant counters relative to a rolling baseline, elevated oauth_authentication_request_total series with result="error" broken out by reason labels, and elevated oauth_apiserver_request_total error fractions grouped by verb and HTTP code for aggregated user.openshift.io APIs. User and Identity custom resource churn spikes may indicate misconfigured identity mappings spraying duplicate Identity rows after IdP attribute remaps. ServiceAccount token usage as a break-glass path when interactive OAuth is impaired is inferred cautiously from audit verbs executed by human principals using system:serviceaccount tokens outside normal automation baselines, joined only as a secondary hint so legitimate CI is not misclassified.

Index and permission design land before field extraction. Designate index=ocp_oauth for dedicated oauth-openshift pod logs, optional oauth server access logs, and structured extracts from oc adm node-logs --role=master --path=oauth-server/audit.log when your log pipeline can ship control-plane host paths with tamper-evident chain-of-custody. Designate index=ocp_audit for Kubernetes API audit JSON including user.openshift.io and oauth.openshift.io groups, plus openshift-config or openshift-authentication Secret touch audit when policy permits Metadata-level visibility only. Designate index=ocp_events for Kubernetes events with reasons AuthenticationFailed, IdentityProviderConfigError, OAuthServerError, TokenIssuedFailed, or free-text messages that cite oauth-openshift, openshift-authentication, or identity provider connectivity. Designate index=ocp_metrics for Prometheus exposition including oauth_authentication_request_total, oauth_apiserver_request_total, oauth_apiserver_request_count when your OpenShift minor still exposes legacy counter names, and apiserver_request_total filtered by group="oauth.openshift.io" when kube-apiserver metrics federation preserves that label cardinality. Issue distinct HEC tokens per environment with least privilege: platform identity engineers may search all lanes; application teams receive filtered views that redact requestObject bodies and suppress htpasswd hash material. Retention should cover at least thirty days hot for quarterly access reviews, ninety days when regulated customers require identity forensic replay, and align cold storage with enterprise logging policy. Legal review should confirm corporate usernames, email attributes, and internal IdP hostnames are acceptable in Splunk.

RBAC and safety: collectors that read openshift-config Secrets or run oc logs -n openshift-authentication deploy/oauth-openshift must use dedicated break-glass ServiceAccounts with namespace-scoped read plus cluster read on authentication.config.openshift.io, not long-lived kubeadmin kubeconfig files on employee laptops. Forwarders that tail control-plane oauth-server audit.log must run on hardened control-plane hosts or consume cloud-provider equivalents with read-only roles. When you federate Prometheus, bind scrapers to metrics readers rather than cluster administrators.

Field normalization expectations: flatten identity provider type into idp_provider with lowercase tokens ldap, openid, github, gitlab, google, requestheader, htpasswd, basicauth, keystone, or unknown when parsers cannot infer the stanza name. Map flow stage hints from structured oauth server audit lines or message substrings into flow_stage using start, code, token, userinfo, groups, or unknown. Preserve cluster identity on every event as cluster, openshift_cluster, or cluster_name drawn from management-cluster context or external_labels on Prometheus scrapes. For audit rows touching users or identities, extract objectRef.name, objectRef.resource, verb, user.username, responseStatus.code, and responseStatus.reason. If JSON paths arrive dotted versus bracketed, coalesce() ladders in SPL still resolve when props.conf FIELDALIAS maps are maintained.

Risk briefing: bursts of AuthenticationFailed events may follow password rotation campaigns, certificate reloads on corporate load balancers, or intentional multi-factor enforcement rollouts rather than attack. OAuth 5xx spikes may coincide with single IdP shard maintenance windows approved on the change calendar. Token issuance surges may track marketing-driven registration floods or end-of-quarter hiring waves. Elevated Identity create rates may be benign during oc adm groups sync testing in lab clusters. Alerts must combine dwell, multi-lane corroboration, and optional lookup-driven suppressions tied to change_ticket_id metadata on HTTP Event Collector payloads rather than paging on every denied login attempt.

Differentiation recap: OpenShift integrated OAuth server flows, identity provider integration health, oauth.openshift.io aggregated API error and latency behavior, and User or Identity lifecycle anomalies tied to authentication, not vanilla ClusterOperator-only storytelling, not SCC admission, not generic RBAC graph analytics, not admission webhook timeouts, not cluster-admin binding escalation analytics alone.

Operational posture: align telemetry with your change board by stamping change_ticket_id onto HEC events when platform teams rotate OAuth serving certificates, patch authentication.config.openshift.io identityProviders, or reload corporate reverse proxies in front of RequestHeader integrations. When Splunk shows Identity churn but corporate IdP logs show clean authentications, suspect attribute mapping changes in the OAuth CR rather than external directory failure.

### Step 2 — Configure data collection

Stand up six complementary lanes Splunk multisearch can fuse: structured oauth server and oauth-apiserver audit streams, Kubernetes events citing authentication failures, optional oauth-openshift container logs, Prometheus metrics for oauth_authentication_request_total and oauth_apiserver_request_total families, apiserver_request_total grouped to oauth.openshift.io when cardinality policies allow, and periodic ClusterOperator authentication snapshots used only as a degraded corroboration bit rather than the primary signal.

OAuth server audit lane: where supported, enable collection from control-plane node paths oauth-server/audit.log using oc adm node-logs --role=master --path=oauth-server/audit.log during investigations, and for continuous telemetry ship the same files with sourcetype=ocp_oauth_server_audit into index=ocp_oauth or index=ocp_audit depending on classification. Preserve timestamps, HTTP paths under /oauth/, upstream status codes returned to browsers, correlation identifiers when present, and provider labels when the oauth server logs include them. When structured JSON is unavailable, rely on regex extracts in props.conf for stage and provider hints.

OAuth apiserver audit lane: ship audit lines for requests against apiservices/v1.user.openshift.io and other oauth.openshift.io aggregated endpoints with sourcetype=ocp_oauth_apiserver_audit when you split streams; many teams keep sourcetype=ocp_audit and filter objectRef.apiGroup in SPL. Ensure verbs on users, identities, and useridentitymappings are visible at Metadata or RequestResponse levels consistent with volume budgets.

API audit lane for User and Identity churn: include rules for user.openshift.io resources at RequestResponse or Metadata levels. Successful creates on Identity objects during steady state should be rare outside provisioning projects; bursts warrant retention of actor user.username and source IP enrichment when audit policy captures it.

Events lane: forward Kubernetes events into index=ocp_events with sourcetype=ocp_events. Retain reason, message, involvedObject.kind, involvedObject.name, involvedObject.namespace, type, count, and lastTimestamp. Explicitly route events where reason matches AuthenticationFailed, IdentityProviderConfigError, OAuthServerError, or TokenIssuedFailed into the same indexes this UC searches.

Metrics lane: federate in-cluster Prometheus targets that expose oauth_authentication_request_total with result and reason labels, oauth_apiserver_request_total with verb and code labels, and apiserver_request_total with group and resource labels. Land lines in index=ocp_metrics with sourcetype=prometheus:metrics. Create recording rules or utilization dashboards in OpenShift Monitoring that pre-aggregate high-cardinality series before Splunk if cost requires, but preserve error and 5xx fractions per cluster.

ClusterOperator corroboration lane: optional lightweight snapshots from oc get clusteroperator authentication -o json into sourcetype=ocp_clusteroperator with Degraded and Progressing flags copied into fields auth_op_deg and auth_op_prog for join hints. This UC treats authentication operator Degraded as a secondary amplifier, not a duplicate of UC-3.3.6 paging logic.

Example oc verification operators run during design reviews:

```bash
oc get clusteroperator authentication -o wide
oc get oauth cluster -o yaml
oc -n openshift-authentication logs deploy/oauth-openshift --tail=200
oc adm node-logs --role=master --path=oauth-server/audit.log
oc get users.user.openshift.io -A
oc get identity.user.openshift.io -A
```

Example audit-policy fragment illustrating user.openshift.io focus (tune omitStages and users per estate):

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - "RequestReceived"
rules:
  - level: Metadata
    verbs: ["create", "update", "patch", "delete"]
    resources:
      - group: "user.openshift.io"
        resources: ["users", "identities", "useridentitymappings"]
    namespaces: []
```

props.conf guidance: TRUNCATE sufficiently large for JSON audit bodies, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER for newline-delimited JSON, and SEDCMD or transforms that strip password-like patterns if misconfigured clients ever leak credentials into logs.

Pre-save validation: index=ocp_oauth sourcetype=ocp_oauth_server_audit earliest=-1h must return events after enabling forwarding; ocp_oauth_apiserver_audit or filtered ocp_audit must show user.openshift.io traffic during test oc login; ocp_events must surface AuthenticationFailed during intentional bad-password tests in lab; prometheus:metrics must include oauth_authentication_request_total after scrape start; optional ocp_clusteroperator snapshots must move when authentication operator toggles during controlled upgrades.

Dashboards: the Splunk OpenShift App should host a severity-colored table keyed on cluster and idp_provider with drilldowns to raw oauth audit lines, ocp_events text, prometheus metric samples, and identity object audit JSON. Splunk Enterprise Security deployments may treat high-severity rows as risk notables with cluster as an asset and idp_provider as a vector.

Supplemental mstats guidance: when metrics land in metrics indexes with prestats instead of raw prometheus lines, mirror the oauth_authentication_request_total and oauth_apiserver_request_total selectors using mstats avg() or sum() over span=5m with the same cluster label conventions, then join results to audit arms on cluster and _time buckets. Keep span aligned to the saved search schedule so token velocity math stays comparable to streamstats baselines on raw series.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_14_oauth_server_flow_health with a fifteen minute schedule during steady-state production, dispatch earliest=-6h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster, idp_provider, signal_lane rows for thirty minutes unless severity escalates from warn to page. Include recommended_action, flow_stage, and oauth_http_max fields in pager descriptions so incident commanders open identity provider runbooks without rerunning ad hoc searches.

Pipeline narrative for reviewers: multisearch fans per-IdP flow-failure and event arms, oauth-openshift HTTP 5xx style extracts, oauth-apiserver Prometheus error and latency hints, token issuance anomaly arms using streamstats on counter deltas, Identity and User churn arms using audit verbs, and optional authentication ClusterOperator degraded corroboration so a silent single sourcetype outage does not hide genuine auth outages. coalesce() absorbs field naming drift across exporters. streamstats computes short-window velocity and z-score style deviations on token grant deltas per cluster. eventstats adds fleet context such as count of distinct failing providers per cluster. case() maps multi-lane corroborated failures, sustained error reasons, churn spikes, and operator degradation amplifiers into page versus warn versus info tiers. recommended_action encodes oc describe identity, oc get oauth cluster, oc logs oauth-openshift, and corporate IdP escalation paths without pretending Splunk replaces kubectl.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.14 OpenShift OAuth server flow — ocp_oauth_server_audit ocp_oauth_apiserver_audit ocp_audit ocp_events ocp_oauth + prometheus oauth_* + optional clusteroperator auth. Tunables: err_warn=0.05 err_page=0.15 z_page=3.5 churn_warn=25 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_oauth) earliest=-6h@h latest=now
        (sourcetype=ocp_oauth_server_audit OR sourcetype=ocp_oauth_apiserver_audit OR sourcetype=ocp_audit OR sourcetype=ocp_events)
        ((reason=AuthenticationFailed OR reason=IdentityProviderConfigError OR reason=OAuthServerError OR reason=TokenIssuedFailed) OR match(lower(_raw),"authenticationfailed|identityproviderconfigerror|oauthservererror|tokenissuedfailed|oauth\/authorize|oauth\/token|\/oauth\/") OR match(lower(coalesce(message, Message, "")),"identity provider|oauth|ldap bind|openid|htpasswd|requestheader|keystone"))
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval idp_provider=lower(trim(toString(coalesce(identity_provider, idp_type, provider, providerName, idp, "unknown"))))
      | eval idp_provider=if(match(idp_provider,"^$|^unknown$"), case(
            match(lower(_raw),"ldap|389"), "ldap",
            match(lower(_raw),"openid|oidc|well-known"), "openid",
            match(lower(_raw),"github"), "github",
            match(lower(_raw),"gitlab"), "gitlab",
            match(lower(_raw),"google"), "google",
            match(lower(_raw),"requestheader|remote_user"), "requestheader",
            match(lower(_raw),"htpasswd"), "htpasswd",
            match(lower(_raw),"basicauth|basic auth"), "basicauth",
            match(lower(_raw),"keystone"), "keystone",
            true(), "unknown"), idp_provider)
      | eval flow_stage=lower(trim(toString(coalesce(oauth_stage, stage, flow, ""))))
      | eval flow_stage=if(len(flow_stage)<2, case(
            match(lower(_raw),"\/oauth\/authorize|login|start"), "start",
            match(lower(_raw),"code|callback|grant"), "code",
            match(lower(_raw),"\/oauth\/token|token endpoint"), "token",
            match(lower(_raw),"userinfo"), "userinfo",
            match(lower(_raw),"group|sync"), "groups",
            true(), "unknown"), flow_stage)
      | eval oauth_http_code_hint=tonumber(tostring(coalesce(status, http_status, response_code, "0")),10)
      | eval lane_detail=substr(trim(toString(coalesce(message, Message, reason, ""))),1,220)
      | eval signal_lane="idp_flow_evt"
      | stats count AS lane_events max(oauth_http_code_hint) AS oauth_http_max latest(_time) AS last_evt_t values(reason) AS evt_reasons BY cluster idp_provider flow_stage signal_lane ]
    [ search (index=ocp_oauth OR index=ocp_audit) earliest=-6h@h latest=now
        (sourcetype=ocp_oauth_server_audit OR sourcetype=ocp_audit)
        | where match(lower(_raw),"oauth-openshift|openshift-authentication|oauth\/|tokenissuedfailed| 5[0-9][0-9]")
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval idp_provider=lower(trim(toString(coalesce(provider, idp_provider, "aggregate"))))
      | eval flow_stage="http_edge"
      | rex field=_raw "(?i)(?P<rex_http>5\\d{2})"
      | eval oauth_http_max=tonumber(rex_http,10)
      | eval signal_lane="oauth_httpserver_5xx"
      | stats count AS lane_events max(oauth_http_max) AS oauth_http_max latest(_time) AS last_evt_t BY cluster idp_provider flow_stage signal_lane ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype="prometheus:ocp") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"oauth_authentication_request_total|oauth_apiserver_request_total")
      | eval result_l=lower(trim(toString(coalesce(result, ""))))
      | eval code_l=lower(trim(toString(coalesce(code, status_code, http_code, ""))))
      | eval reason_l=lower(trim(toString(coalesce(reason, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval idp_provider=lower(trim(toString(coalesce(provider, client_id, "aggregate"))))
      | eval flow_stage="metrics"
      | eval is_err=if((result_l=="error") OR match(code_l,"^5..$") OR (match(mn,"oauth_apiserver_request_total") AND match(code_l,"5..")),1,0)
      | eval signal_lane="oauth_prom_errs"
      | stats sum(mv) AS metric_sum sum(eval(if(is_err==1,mv,0))) AS err_sum latest(_time) AS last_evt_t values(mn) AS metric_names values(reason_l) AS prom_reasons values(verb_l) AS prom_verbs BY cluster idp_provider flow_stage signal_lane ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype="prometheus:ocp") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"oauth_apiserver_request_total|oauth_apiserver_request_count")
      | eval idp_provider="aggregate"
      | eval flow_stage="token_grant"
      | eval signal_lane="token_issuance"
      | sort 0 + cluster - _time
      | streamstats window=12 current=t global=f last(mv) AS prev_mv BY cluster
      | eval delta=mv-coalesce(prev_mv,0)
      | eventstats avg(delta) AS tok_avg stdev(delta) AS tok_stdev BY cluster
      | eval token_delta_z=if(tok_stdev>0, round((delta - tok_avg) / tok_stdev, 3), 0)
      | stats latest(_time) AS last_evt_t max(abs(token_delta_z)) AS token_z_peak latest(mv) AS grant_latest BY cluster idp_provider flow_stage signal_lane ]
    [ search index=ocp_audit sourcetype=ocp_audit earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, apigroup, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, ""))))
      | where match(apig,"user.openshift.io") AND match(res,"identities|users|useridentitymappings") AND match(verb,"create|update|patch|delete")
      | eval idp_provider="identity_api"
      | eval flow_stage="identity_churn"
      | eval signal_lane="user_identity_churn"
      | stats count AS lane_events latest(_time) AS last_evt_t BY cluster idp_provider flow_stage signal_lane ]
    [ search index=ocp_metrics sourcetype=ocp_clusteroperator earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval op=lower(trim(toString(coalesce(name, operator, metadata_name, ""))))
      | where match(op,"^authentication$")
      | eval dg=lower(trim(toString(coalesce(degraded, conditions_degraded, degraded_status, ""))))
      | eval auth_op_deg_hint=if(match(dg,"true|1"),1,0)
      | eval idp_provider="clusteroperator"
      | eval flow_stage="operator"
      | eval signal_lane="auth_operator_hint"
      | stats latest(_time) AS last_evt_t max(auth_op_deg_hint) AS auth_op_deg_hint BY cluster idp_provider flow_stage signal_lane ]
    [ | mstats prestats=t sum(_value) AS mv WHERE index=ocp_metrics (metric_name="oauth_authentication_request_total" OR metric_name="oauth_apiserver_request_total") span=5m BY cluster metric_name
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval idp_provider=lower(trim(toString(coalesce(metric_name, "mstats_metric"))))
      | eval flow_stage="mstats"
      | eval signal_lane="mstats_supplement"
      | eval metric_sum=mv
      | eval err_sum=0
      | stats sum(metric_sum) AS metric_sum sum(err_sum) AS err_sum latest(_time) AS last_evt_t BY cluster idp_provider flow_stage signal_lane ]
| eval cluster=coalesce(nullif(cluster,""), "unknown_cluster")
| stats sum(lane_events) AS lane_events max(last_evt_t) AS last_seen max(oauth_http_max) AS oauth_http_max values(signal_lane) AS signal_lanes values(evt_reasons) AS evt_reasons values(metric_names) AS metric_names max(err_sum) AS err_sum max(metric_sum) AS metric_sum max(token_z_peak) AS token_z_peak max(auth_op_deg_hint) AS auth_op_deg_hint values(prom_reasons) AS prom_reasons values(prom_verbs) AS prom_verbs max(grant_latest) AS grant_latest BY cluster idp_provider flow_stage
| eval oauth_err_rate=if(isnotnull(metric_sum) AND metric_sum>0, round(coalesce(err_sum,0)/metric_sum,4), null())
| eventstats perc70(oauth_err_rate) AS fleet_oauth_err_p70 sum(eval(if(coalesce(oauth_err_rate,0)>0.05,1,0))) AS cluster_hot_providers BY cluster
| streamstats window=6 current=t global=f sum(lane_events) AS flow_burst BY cluster idp_provider
| eval token_delta_z=coalesce(token_z_peak,0)
| eval identity_chg_rate=coalesce(lane_events,0)
| eval evidence_snip=substr(trim(toString(mvindex(mvdedup(evt_reasons),0))),1,160)
| eval severity=case(
    coalesce(auth_op_deg_hint,0)==1 AND (coalesce(oauth_err_rate,0)>=0.15 OR flow_burst>=40 OR token_delta_z>=3.5), "page",
    coalesce(auth_op_deg_hint,0)==1 AND (coalesce(oauth_err_rate,0)>=0.05 OR flow_burst>=15), "warn",
    coalesce(oauth_err_rate,0)>=0.15 AND cluster_hot_providers>=2, "page",
    coalesce(oauth_err_rate,0)>=0.05, "warn",
    token_delta_z>=3.5, "page",
    token_delta_z>=2.0, "warn",
    flow_burst>=60, "page",
    flow_burst>=25, "warn",
    match(flow_stage,"identity_churn") AND identity_chg_rate>=40, "warn",
    coalesce(oauth_http_max,0)>=500, "warn",
    true(), "info")
| eval recommended_action=case(
    severity=="page" AND match(idp_provider,"ldap"), "verify_ldap_urls_tls_and_bind_secret_then_oc_get_oauth_cluster",
    severity=="page" AND match(idp_provider,"openid|github|gitlab|google"), "validate_oidc_well_known_and_client_secrets_corporate_idp_health",
    severity=="page" AND match(idp_provider,"htpasswd"), "restore_htpasswd_secret_and_roll_oauth_openshift_pods_under_change_control",
    severity=="page" AND match(idp_provider,"requestheader"), "validate_edge_proxy_headers_and_requestheader_oauth_stanza",
    flow_burst>=25, "tail_oauth_openshift_logs_and_collect_oauth_server_audit_from_control_plane_nodes",
    token_delta_z>=2.0, "compare_oauth_token_metrics_to_login_baselines_and_review_audit_denials",
    match(flow_stage,"identity_churn"), "review_identity_mapping_changes_and_oc_get_identity_for_duplicates",
    coalesce(auth_op_deg_hint,0)==1, "oc_describe_clusteroperator_authentication_and_correlate_uc_3_3_6_context",
    true(), "oc_get_oauth_cluster_yaml_and_open_support_troubleshooting_authentication_runbook")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster idp_provider flow_stage signal_lanes lane_events oauth_http_max oauth_err_rate token_delta_z identity_chg_rate auth_op_deg_hint flow_burst cluster_hot_providers severity recommended_action last_seen evidence_snip metric_names prom_verbs grant_latest cluster_tier owner_team environment
```



savedsearches.conf sketch:

```ini
[openshift_uc_3_3_14_oauth_server_flow_health_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -6h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-identity@example.com
action.email.subject = OCP OAuth flow $result.severity$ $result.cluster$ $result.idp_provider$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_14_oauth_server_flow_health | where severity IN ("page","warn")
```

Performance: if Job Inspector shows multisearch queue time above internal SLA, materialize prometheus counters and identity churn arms hourly into summary indexes keyed on cluster and idp_provider, widen alert windows to earliest=-2h@h on summaries, and retain this full search for investigations.

### Step 4 — Validate

Ground truth always starts on-cluster. During a controlled lab login failure, compare Splunk flow_stage and idp_provider fields to oauth-openshift pod logs gathered with oc logs -n openshift-authentication deploy/oauth-openshift and to any oauth-server audit lines pulled using oc adm node-logs --role=master --path=oauth-server/audit.log. When Splunk omits provider labels present live, tighten FIELDALIAS maps or ship structured JSON instead of raw plain text.

Identity provider configuration review: run oc get oauth cluster -o yaml and verify spec.identityProviders names match Splunk idp_provider tokens after lowercase normalization. Compare GitHub or GitLab enterprise URLs in the OAuth CR to corporate IdP health dashboards during suspected rate-limit windows.

Prometheus cross-check: in the OpenShift console monitoring stack, validate oauth_authentication_request_total error fractions and oauth_apiserver_request_total 5xx rates for the same cluster labels Splunk indexes. When metrics disagree with audit-derived failure counts, suspect scrape gaps, label collisions between regions, or recording rules that drop reason labels.

Synthetic failure tests: under change control, misconfigure a lab LDAP provider to point at an unroutable host, attempt oc login, confirm AuthenticationFailed or IdentityProviderConfigError style events land in ocp_events, and confirm openshift_uc_3_3_14_oauth_server_flow_health returns warn or page within the scheduled window. Revert the change, confirm recovery, and confirm severity returns to info.

Negative test: after recovery with clean interactive login for multiple providers, steady oauth_authentication_request_total error rates near zero, and Identity churn at baseline, confirm the alert wrapper returns zero rows when filtering to page and warn only.

Correlation discipline: when authentication ClusterOperator reports Degraded per oc get clusteroperator authentication, pair with this UC lanes before blaming kube-apiserver alone. Escalate to UC-3.3.6 owners if the defect is purely operator reconciliation without user-facing login impact.

User and Identity object validation: run oc get identity.user.openshift.io and compare create rates to Splunk identity_churn rows. Sudden duplicate providerUserName keys across multiple Identity resources often indicate mapping changes rather than brute-force attacks.

OAuth CR and Secret validation: compare oc get oauth cluster -o yaml to version control commits. Secret generation metadata for htpasswd should move only during approved rotations; unexpected drift without tickets is high severity in governance reviews independent of this alert.

### Step 5 — Operationalize & Troubleshoot

Case 1 — LDAP bind failures after directory certificate rotation: validate trust bundles referenced by the OAuth CR, compare ldap url tls settings, restart oauth-openshift only under vendor guidance after fixing trust, and coordinate with directory teams on bind DN password expiry separate from user passwords.

Case 2 — OpenID Connect discovery 5xx from corporate IdP: check well-known endpoint health, load balancer pools, and WAF rules blocking oauth-openshift egress; temporarily widen maintenance suppressions when change_ticket_id matches an approved IdP window.

Case 3 — GitHub or GitLab rate limiting during CI-driven login storms: move automation to ServiceAccount tokens or OAuth applications with higher quotas, stagger GitOps controller logins, and correlate Splunk bursts with Git provider status pages before paging cluster leadership.

Case 4 — htpasswd Secret missing or rotated without console reload: confirm oc get secret -n openshift-config references match the OAuth CR fileData keys, restore Secret objects from sealed-secrets or vault pipelines under change control, and communicate password resets to affected teams.

Case 5 — RequestHeader trust misconfiguration after ingress controller upgrade: validate clientCommonNames, headers, and allowed names on the authenticating proxy, compare HAProxy or cloud load balancer client certificate policies, and capture oauth-openshift warnings about header mismatches in pod logs.

Case 6 — Keystone provider errors in hybrid OpenStack estates: verify endpoint catalog TLS, clock skew between clouds, and project membership mappings; treat elevated Identity churn as secondary evidence until OpenStack identity engineers confirm clean token issuance.

Case 7 — Token issuance anomaly with benign cause: end-of-quarter hiring spikes or training classes may elevate grants; compare streamstats velocity to HR calendars and suppress when workforce_events lookup authorizes the window.

Case 8 — Identity object spray after attribute remap: when corporate IdP starts emitting a new preferredUsername claim, OpenShift may create duplicate Identity rows; coordinate oc adm cleanup or documented pruning procedures with identity governance before automated deletion.

Case 9 — ServiceAccount token usage hint during OAuth outage: investigate whether human actors run oc --token against emergency scripts; distinguish break-glass from stolen tokens using source IP baselines and UC-3.2.23 binding context without conflating authentication with authorization escalation alone.

Case 10 — oauth-apiserver latency with healthy oauth-openshift: check etcd, openshift-apiserver, and aggregated apiservers; gather pprof only under support guidance; compare apiserver_request_total group oauth.openshift.io latency histograms to kube-apiserver overall health.

Case 11 — Cluster-wide MFA enforcement rollout: expect AuthenticationFailed spikes on legacy clients; communicate client upgrades, tune alert thresholds for the rollout window, and document the change ticket on HEC events.

Case 12 — Transient LDAP referral chase loops on hub-and-spoke directories: identity teams may enable referral following that increases latency; Splunk may show grouped failures without sustained 5xx at oauth-openshift; treat as warn unless customer-facing SLAs breach.

Closing checklist: multisearch lists flow or event arms, HTTP error arms, prometheus arms, token anomaly arms, identity churn arms, and optional operator corroboration; coalesce, streamstats, eventstats, and case appear; closing table includes cluster, idp_provider, flow_stage, signal_lanes, lane_events, oauth_http_max, oauth_err_rate, token_delta_z, identity_chg_rate, auth_op_deg_hint, flow_burst, cluster_hot_providers, severity, recommended_action, last_seen, evidence_snip, metric_names, prom_verbs, and grant_latest for eighteen analyst-visible columns.

## SPL

```spl
`comment("UC-3.3.14 OpenShift OAuth server flow — ocp_oauth_server_audit ocp_oauth_apiserver_audit ocp_audit ocp_events ocp_oauth + prometheus oauth_* + optional clusteroperator auth. Tunables: err_warn=0.05 err_page=0.15 z_page=3.5 churn_warn=25 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_oauth) earliest=-6h@h latest=now
        (sourcetype=ocp_oauth_server_audit OR sourcetype=ocp_oauth_apiserver_audit OR sourcetype=ocp_audit OR sourcetype=ocp_events)
        ((reason=AuthenticationFailed OR reason=IdentityProviderConfigError OR reason=OAuthServerError OR reason=TokenIssuedFailed) OR match(lower(_raw),"authenticationfailed|identityproviderconfigerror|oauthservererror|tokenissuedfailed|oauth\/authorize|oauth\/token|\/oauth\/") OR match(lower(coalesce(message, Message, "")),"identity provider|oauth|ldap bind|openid|htpasswd|requestheader|keystone"))
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval idp_provider=lower(trim(toString(coalesce(identity_provider, idp_type, provider, providerName, idp, "unknown"))))
      | eval idp_provider=if(match(idp_provider,"^$|^unknown$"), case(
            match(lower(_raw),"ldap|389"), "ldap",
            match(lower(_raw),"openid|oidc|well-known"), "openid",
            match(lower(_raw),"github"), "github",
            match(lower(_raw),"gitlab"), "gitlab",
            match(lower(_raw),"google"), "google",
            match(lower(_raw),"requestheader|remote_user"), "requestheader",
            match(lower(_raw),"htpasswd"), "htpasswd",
            match(lower(_raw),"basicauth|basic auth"), "basicauth",
            match(lower(_raw),"keystone"), "keystone",
            true(), "unknown"), idp_provider)
      | eval flow_stage=lower(trim(toString(coalesce(oauth_stage, stage, flow, ""))))
      | eval flow_stage=if(len(flow_stage)<2, case(
            match(lower(_raw),"\/oauth\/authorize|login|start"), "start",
            match(lower(_raw),"code|callback|grant"), "code",
            match(lower(_raw),"\/oauth\/token|token endpoint"), "token",
            match(lower(_raw),"userinfo"), "userinfo",
            match(lower(_raw),"group|sync"), "groups",
            true(), "unknown"), flow_stage)
      | eval oauth_http_code_hint=tonumber(tostring(coalesce(status, http_status, response_code, "0")),10)
      | eval lane_detail=substr(trim(toString(coalesce(message, Message, reason, ""))),1,220)
      | eval signal_lane="idp_flow_evt"
      | stats count AS lane_events max(oauth_http_code_hint) AS oauth_http_max latest(_time) AS last_evt_t values(reason) AS evt_reasons BY cluster idp_provider flow_stage signal_lane ]
    [ search (index=ocp_oauth OR index=ocp_audit) earliest=-6h@h latest=now
        (sourcetype=ocp_oauth_server_audit OR sourcetype=ocp_audit)
        | where match(lower(_raw),"oauth-openshift|openshift-authentication|oauth\/|tokenissuedfailed| 5[0-9][0-9]")
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval idp_provider=lower(trim(toString(coalesce(provider, idp_provider, "aggregate"))))
      | eval flow_stage="http_edge"
      | rex field=_raw "(?i)(?P<rex_http>5\\d{2})"
      | eval oauth_http_max=tonumber(rex_http,10)
      | eval signal_lane="oauth_httpserver_5xx"
      | stats count AS lane_events max(oauth_http_max) AS oauth_http_max latest(_time) AS last_evt_t BY cluster idp_provider flow_stage signal_lane ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype="prometheus:ocp") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"oauth_authentication_request_total|oauth_apiserver_request_total")
      | eval result_l=lower(trim(toString(coalesce(result, ""))))
      | eval code_l=lower(trim(toString(coalesce(code, status_code, http_code, ""))))
      | eval reason_l=lower(trim(toString(coalesce(reason, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval idp_provider=lower(trim(toString(coalesce(provider, client_id, "aggregate"))))
      | eval flow_stage="metrics"
      | eval is_err=if((result_l=="error") OR match(code_l,"^5..$") OR (match(mn,"oauth_apiserver_request_total") AND match(code_l,"5..")),1,0)
      | eval signal_lane="oauth_prom_errs"
      | stats sum(mv) AS metric_sum sum(eval(if(is_err==1,mv,0))) AS err_sum latest(_time) AS last_evt_t values(mn) AS metric_names values(reason_l) AS prom_reasons values(verb_l) AS prom_verbs BY cluster idp_provider flow_stage signal_lane ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype="prometheus:ocp") earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"oauth_apiserver_request_total|oauth_apiserver_request_count")
      | eval idp_provider="aggregate"
      | eval flow_stage="token_grant"
      | eval signal_lane="token_issuance"
      | sort 0 + cluster - _time
      | streamstats window=12 current=t global=f last(mv) AS prev_mv BY cluster
      | eval delta=mv-coalesce(prev_mv,0)
      | eventstats avg(delta) AS tok_avg stdev(delta) AS tok_stdev BY cluster
      | eval token_delta_z=if(tok_stdev>0, round((delta - tok_avg) / tok_stdev, 3), 0)
      | stats latest(_time) AS last_evt_t max(abs(token_delta_z)) AS token_z_peak latest(mv) AS grant_latest BY cluster idp_provider flow_stage signal_lane ]
    [ search index=ocp_audit sourcetype=ocp_audit earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, apigroup, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, ""))))
      | where match(apig,"user.openshift.io") AND match(res,"identities|users|useridentitymappings") AND match(verb,"create|update|patch|delete")
      | eval idp_provider="identity_api"
      | eval flow_stage="identity_churn"
      | eval signal_lane="user_identity_churn"
      | stats count AS lane_events latest(_time) AS last_evt_t BY cluster idp_provider flow_stage signal_lane ]
    [ search index=ocp_metrics sourcetype=ocp_clusteroperator earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval op=lower(trim(toString(coalesce(name, operator, metadata_name, ""))))
      | where match(op,"^authentication$")
      | eval dg=lower(trim(toString(coalesce(degraded, conditions_degraded, degraded_status, ""))))
      | eval auth_op_deg_hint=if(match(dg,"true|1"),1,0)
      | eval idp_provider="clusteroperator"
      | eval flow_stage="operator"
      | eval signal_lane="auth_operator_hint"
      | stats latest(_time) AS last_evt_t max(auth_op_deg_hint) AS auth_op_deg_hint BY cluster idp_provider flow_stage signal_lane ]
    [ | mstats prestats=t sum(_value) AS mv WHERE index=ocp_metrics (metric_name="oauth_authentication_request_total" OR metric_name="oauth_apiserver_request_total") span=5m BY cluster metric_name
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval idp_provider=lower(trim(toString(coalesce(metric_name, "mstats_metric"))))
      | eval flow_stage="mstats"
      | eval signal_lane="mstats_supplement"
      | eval metric_sum=mv
      | eval err_sum=0
      | stats sum(metric_sum) AS metric_sum sum(err_sum) AS err_sum latest(_time) AS last_evt_t BY cluster idp_provider flow_stage signal_lane ]
| eval cluster=coalesce(nullif(cluster,""), "unknown_cluster")
| stats sum(lane_events) AS lane_events max(last_evt_t) AS last_seen max(oauth_http_max) AS oauth_http_max values(signal_lane) AS signal_lanes values(evt_reasons) AS evt_reasons values(metric_names) AS metric_names max(err_sum) AS err_sum max(metric_sum) AS metric_sum max(token_z_peak) AS token_z_peak max(auth_op_deg_hint) AS auth_op_deg_hint values(prom_reasons) AS prom_reasons values(prom_verbs) AS prom_verbs max(grant_latest) AS grant_latest BY cluster idp_provider flow_stage
| eval oauth_err_rate=if(isnotnull(metric_sum) AND metric_sum>0, round(coalesce(err_sum,0)/metric_sum,4), null())
| eventstats perc70(oauth_err_rate) AS fleet_oauth_err_p70 sum(eval(if(coalesce(oauth_err_rate,0)>0.05,1,0))) AS cluster_hot_providers BY cluster
| streamstats window=6 current=t global=f sum(lane_events) AS flow_burst BY cluster idp_provider
| eval token_delta_z=coalesce(token_z_peak,0)
| eval identity_chg_rate=coalesce(lane_events,0)
| eval evidence_snip=substr(trim(toString(mvindex(mvdedup(evt_reasons),0))),1,160)
| eval severity=case(
    coalesce(auth_op_deg_hint,0)==1 AND (coalesce(oauth_err_rate,0)>=0.15 OR flow_burst>=40 OR token_delta_z>=3.5), "page",
    coalesce(auth_op_deg_hint,0)==1 AND (coalesce(oauth_err_rate,0)>=0.05 OR flow_burst>=15), "warn",
    coalesce(oauth_err_rate,0)>=0.15 AND cluster_hot_providers>=2, "page",
    coalesce(oauth_err_rate,0)>=0.05, "warn",
    token_delta_z>=3.5, "page",
    token_delta_z>=2.0, "warn",
    flow_burst>=60, "page",
    flow_burst>=25, "warn",
    match(flow_stage,"identity_churn") AND identity_chg_rate>=40, "warn",
    coalesce(oauth_http_max,0)>=500, "warn",
    true(), "info")
| eval recommended_action=case(
    severity=="page" AND match(idp_provider,"ldap"), "verify_ldap_urls_tls_and_bind_secret_then_oc_get_oauth_cluster",
    severity=="page" AND match(idp_provider,"openid|github|gitlab|google"), "validate_oidc_well_known_and_client_secrets_corporate_idp_health",
    severity=="page" AND match(idp_provider,"htpasswd"), "restore_htpasswd_secret_and_roll_oauth_openshift_pods_under_change_control",
    severity=="page" AND match(idp_provider,"requestheader"), "validate_edge_proxy_headers_and_requestheader_oauth_stanza",
    flow_burst>=25, "tail_oauth_openshift_logs_and_collect_oauth_server_audit_from_control_plane_nodes",
    token_delta_z>=2.0, "compare_oauth_token_metrics_to_login_baselines_and_review_audit_denials",
    match(flow_stage,"identity_churn"), "review_identity_mapping_changes_and_oc_get_identity_for_duplicates",
    coalesce(auth_op_deg_hint,0)==1, "oc_describe_clusteroperator_authentication_and_correlate_uc_3_3_6_context",
    true(), "oc_get_oauth_cluster_yaml_and_open_support_troubleshooting_authentication_runbook")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster idp_provider flow_stage signal_lanes lane_events oauth_http_max oauth_err_rate token_delta_z identity_chg_rate auth_op_deg_hint flow_burst cluster_hot_providers severity recommended_action last_seen evidence_snip metric_names prom_verbs grant_latest cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Authentication.user) AS auth_user latest(Authentication.action) AS auth_action latest(Authentication.src) AS auth_src FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=now BY Authentication.dest
| rename Authentication.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=t latest(Change.action) AS chg_action latest(Change.object) AS chg_object latest(Change.user) AS chg_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
     | rename Change.dest AS cim_dest ]
| where like(lower(chg_object), "%user.openshift.io%") OR like(lower(chg_object), "%oauth.openshift.io%") OR match(lower(auth_action), "failure|error")
| table cim_dest auth_user auth_action auth_src chg_action chg_object chg_user
```

## Visualization

Severity-colored table by cluster and idp_provider with drilldowns to ocp_oauth_server_audit, ocp_oauth_apiserver_audit, ocp_audit, ocp_events, and prometheus metric lines; timeline of oauth_err_rate; overlay authentication operator degraded hints as a secondary lane; single-value tiles for token_delta_z peaks.

## Known False Positives

Planned identity provider certificate rotations, corporate IdP maintenance windows, and OAuth serving certificate reloads on openshift-authentication often produce short AuthenticationFailed bursts that clear within minutes; require multi-lane corroboration or dwell thresholds before executive escalation. Scheduled GitHub Enterprise outages or rate-limit windows can spike oauth-openshift errors without cluster defects; join provider status pages and change_ticket_id metadata on HTTP Event Collector payloads. htpasswd Secret batch rotations during enterprise password campaigns generate many failed attempts from cached browser sessions until users pick up new credentials; communicate campaigns before muting alerts entirely. Cluster administrators running oc adm groups sync or identity mapping tests in lab clusters can create Identity churn spikes that resemble misconfiguration; segregate lab indexes or lookup suppressions for non-production clusters. End-of-quarter hiring waves and training-class login surges elevate token issuance velocity benignly; compare streamstats baselines to HR-approved calendars. Intentional MFA enforcement rollouts increase AuthenticationFailed counts on legacy oc clients until upgrades finish; document client baselines and extend thresholds during the rollout window. Transient LDAP referral chase loops on consolidated directory hubs can raise latency and failure counts without sustained oauth-openshift 5xx; pair with directory engineer tcpdump or IdP trace only under policy. Penetration tests that deliberately hammer OAuth endpoints may trip flow_burst logic; ingest pentest_authorization lookup rows with start and end epochs. Duplicate log forwarders can double lane_events counts; dedupe on audit auditID or equivalent correlation identifiers when present. Some managed OpenShift offerings redact oauth-server audit paths from centralized logging; expect metric-heavy firing and validate ground truth with oc adm node-logs during incidents. ServiceAccount token clues can reflect legitimate automation switched on during OAuth outages; never treat automation alone as hostile without UC-3.2.23 binding and UC-3.2.12 RBAC context.

## References

- [OpenShift Documentation — Understanding authentication](https://docs.openshift.com/container-platform/latest/authentication/understanding-authentication.html)
- [OpenShift Documentation — Configuring the internal OAuth server](https://docs.openshift.com/container-platform/latest/authentication/configuring-internal-oauth.html)
- [OpenShift Documentation — Configuring an LDAP identity provider](https://docs.openshift.com/container-platform/latest/authentication/identity_providers/configuring-ldap-identity-provider.html)
- [OpenShift Documentation — Configuring an OpenID Connect identity provider](https://docs.openshift.com/container-platform/latest/authentication/identity_providers/configuring-oidc-identity-provider.html)
- [OpenShift Documentation — Configuring an htpasswd identity provider](https://docs.openshift.com/container-platform/latest/authentication/identity_providers/configuring-htpasswd-identity-provider.html)
- [OpenShift Documentation — Troubleshooting authentication issues](https://docs.openshift.com/container-platform/latest/support/troubleshooting/troubleshooting-authentication.html)
- [Red Hat Blog — Introducing Red Hat OpenShift 4](https://www.redhat.com/en/blog/introducing-red-hat-openshift-4)
