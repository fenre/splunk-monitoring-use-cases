## 12. DevOps & CI/CD

### 12.1 Source Control

**Primary App/TA:** GitHub TA, GitLab webhook inputs, custom API inputs (Bitbucket, Azure DevOps).

---

### UC-12.1.1 · Commit Activity Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Commit velocity indicates team productivity and project health. Drops may signal blockers; spikes may precede release issues.
- **App/TA:** GitHub webhook, custom API input
- **Data Sources:** Git webhook events (push), GitHub/GitLab API
- **SPL:**
```spl
index=devops sourcetype="github:webhook" event="push"
| timechart span=1d count as commits by repository
```
- **Implementation:** Configure GitHub/GitLab webhooks to send push events to Splunk HEC. Parse repository, author, branch, and commit count. Track trends per team and repository. Report on developer activity metrics.
- **Visualization:** Line chart (commits over time), Bar chart (commits by repo), Stacked area (commits by team).
- **CIM Models:** N/A

---

### UC-12.1.2 · Branch Protection Bypasses
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Direct pushes to protected branches bypass code review, introducing unreviewed code to production. Detection ensures process compliance.
- **App/TA:** GitHub audit log, GitLab API
- **Data Sources:** GitHub/GitLab audit log, push events to protected branches
- **SPL:**
```spl
index=devops sourcetype="github:audit" action="protected_branch.policy_override"
| table _time, actor, repo, branch, action
```
- **Implementation:** Ingest GitHub/GitLab audit logs. Alert on any push to protected branches (main, release) without PR merge. Alert on branch protection rule changes. Correlate with deployment events.
- **Visualization:** Table (bypass events), Timeline (protection violations), Single value (bypasses this month — target: 0).
- **CIM Models:** N/A

---

### UC-12.1.3 · Pull Request Metrics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** PR cycle time affects development velocity. Long review times indicate bottlenecks; abandoned PRs indicate scope or alignment issues.
- **App/TA:** GitHub API input
- **Data Sources:** PR events (opened, reviewed, merged, closed)
- **SPL:**
```spl
index=devops sourcetype="github:pull_request" action="closed" merged="true"
| eval cycle_hours=round((merged_at_epoch-created_at_epoch)/3600,1)
| stats avg(cycle_hours) as avg_cycle, median(cycle_hours) as median_cycle by repository
| sort -avg_cycle
```
- **Implementation:** Ingest PR lifecycle events. Calculate open-to-merge time, review cycles, and abandonment rates. Track per repository and team. Report on engineering efficiency metrics. Identify bottleneck reviewers.
- **Visualization:** Bar chart (avg cycle time by repo), Line chart (PR metrics trend), Table (PR summary), Histogram (cycle time distribution).
- **CIM Models:** N/A

---

### UC-12.1.4 · Secret Exposure Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Secrets committed to source control are immediately compromised. Detection within minutes enables rapid rotation before exploitation.
- **App/TA:** GitGuardian webhook, GitHub secret scanning
- **Data Sources:** Pre-commit hook results, GitGuardian/GitHub secret scanning alerts
- **SPL:**
```spl
index=devops sourcetype="github:secret_scanning" OR sourcetype="gitguardian:alert"
| table _time, repository, secret_type, file_path, author, status
| sort -_time
```
- **Implementation:** Enable GitHub secret scanning or deploy GitGuardian. Forward alerts to Splunk. Alert at critical priority on any secret detection. Track remediation time (rotation). Report on secret types and recurrence.
- **Visualization:** Table (exposed secrets), Single value (unresolved secrets — target: 0), Bar chart (secrets by type), Timeline (detection events).
- **CIM Models:** N/A

---

### UC-12.1.5 · Repository Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Repository permission changes can expose source code to unauthorized users. Audit trail supports IP protection and compliance.
- **App/TA:** GitHub audit log
- **Data Sources:** GitHub/GitLab audit log (permission events)
- **SPL:**
```spl
index=devops sourcetype="github:audit" action IN ("repo.add_member","repo.remove_member","repo.update_member")
| table _time, actor, repo, user, permission, action
```
- **Implementation:** Ingest organization audit log. Track member additions, removals, and permission changes. Alert on permission escalation to admin. Report on repository access patterns for periodic access review.
- **Visualization:** Table (access changes), Timeline (permission events), Bar chart (changes by actor).
- **CIM Models:** N/A

---

### UC-12.1.6 · Force Push Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Force pushes overwrite git history, potentially destroying code and audit trails. Detection ensures accountability.
- **App/TA:** GitHub webhook
- **Data Sources:** Git push events (forced flag)
- **SPL:**
```spl
index=devops sourcetype="github:webhook" event="push" forced="true"
| table _time, repository, ref, pusher, forced
```
- **Implementation:** Parse force push flag from webhook events. Alert on any force push to shared branches. Whitelist expected force pushes (e.g., squash-merge workflows on feature branches). Track frequency per developer.
- **Visualization:** Table (force push events), Timeline (force pushes), Single value (force pushes this week).
- **CIM Models:** N/A

---

### 12.2 CI/CD Pipelines

**Primary App/TA:** Jenkins TA (`TA-jenkins`), custom webhook receivers for GitHub Actions/GitLab CI/ArgoCD.

---

### UC-12.2.1 · Build Success Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Declining build success rates indicate code quality issues, flaky tests, or infrastructure problems. Trending drives improvement.
- **App/TA:** Splunk App for Jenkins, webhook input
- **Data Sources:** CI/CD build results (Jenkins, GitHub Actions, GitLab CI)
- **SPL:**
```spl
index=cicd sourcetype="jenkins:build"
| stats count(eval(result="SUCCESS")) as success, count(eval(result="FAILURE")) as failed, count as total by job_name
| eval success_rate=round(success/total*100,1)
| sort success_rate
```
- **Implementation:** Ingest CI/CD build events via TA or webhook. Track success/failure rates per pipeline. Alert when success rate drops below threshold (e.g., <90%). Identify most-failing pipelines for developer attention.
- **Visualization:** Bar chart (success rate by pipeline), Line chart (success rate trend), Table (failing builds), Single value (overall success rate).
- **CIM Models:** N/A

---

### UC-12.2.2 · Build Duration Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Increasing build times slow development velocity. Detection enables build optimization and infrastructure right-sizing.
- **App/TA:** Splunk App for Jenkins, CI/CD metrics
- **Data Sources:** Build start/end timestamps
- **SPL:**
```spl
index=cicd sourcetype="jenkins:build" result="SUCCESS"
| eval duration_min=round(duration/60000,1)
| timechart span=1d avg(duration_min) as avg_build_time by job_name
```
- **Implementation:** Track build duration for all pipelines. Alert when duration exceeds historical average by >50%. Identify slow build steps. Correlate with infrastructure metrics (runner CPU, disk I/O) to find bottlenecks.
- **Visualization:** Line chart (build duration trend), Bar chart (avg duration by pipeline), Table (slowest builds today).
- **CIM Models:** N/A

---

### UC-12.2.3 · Deployment Frequency (DORA)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Deployment frequency is a key DORA metric indicating engineering capability maturity. Higher frequency correlates with better outcomes.
- **App/TA:** Deployment event webhook
- **Data Sources:** Deployment events from CI/CD pipelines
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" environment="production"
| timechart span=1w count as deployments by application
```
- **Implementation:** Emit deployment events from CI/CD pipelines to Splunk HEC. Track production deployments per team/application per week. Calculate DORA deployment frequency category (daily, weekly, monthly). Report to engineering leadership.
- **Visualization:** Line chart (deployment frequency trend), Bar chart (deployments by team), Single value (deployments this week).
- **CIM Models:** N/A

---

### UC-12.2.4 · Lead Time for Changes (DORA)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Lead time measures the commit-to-production pipeline efficiency. Shorter lead times enable faster value delivery and incident response.
- **App/TA:** Git + deployment correlation
- **Data Sources:** Git commit timestamps + production deployment timestamps
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" environment="production"
| eval lead_time_hours=round((deploy_time_epoch-commit_time_epoch)/3600,1)
| stats avg(lead_time_hours) as avg_lead_time, median(lead_time_hours) as median_lead_time by application
```
- **Implementation:** Correlate commit timestamps with deployment events. Calculate time from first commit to production deployment. Track per application and team. Classify per DORA categories (under 1 hour, under 1 day, under 1 week, over 1 month).
- **Visualization:** Bar chart (lead time by application), Line chart (lead time trend), Histogram (lead time distribution).
- **CIM Models:** N/A

---

### UC-12.2.5 · Failed Deployment Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Failed deployments cause service disruption. Rapid detection enables rollback decisions. Change failure rate is a DORA metric.
- **App/TA:** Deployment event webhook
- **Data Sources:** Deployment events with status, rollback events
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" status="failed"
| table _time, application, environment, version, deployer, error_message
| sort -_time
```
- **Implementation:** Track all deployment outcomes including failures and rollbacks. Alert immediately on production deployment failures. Calculate change failure rate (DORA metric). Correlate with application error rate to measure deployment impact.
- **Visualization:** Table (failed deployments), Single value (change failure rate %), Line chart (failure rate trend), Timeline (deployment events).
- **CIM Models:** N/A

---

### UC-12.2.6 · Pipeline Queue Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Long queue times indicate insufficient CI/CD runner capacity, slowing developer feedback loops and delivery velocity.
- **App/TA:** Splunk App for Jenkins, CI/CD system metrics
- **Data Sources:** CI/CD queue metrics (time in queue, pending jobs)
- **SPL:**
```spl
index=cicd sourcetype="jenkins:queue"
| timechart span=15m avg(wait_time_sec) as avg_wait, max(queue_length) as max_queue
| where avg_wait > 300
```
- **Implementation:** Track job queue wait times and queue lengths. Alert when average wait exceeds 5 minutes. Monitor runner/agent utilization. Report on peak hours to guide scaling decisions.
- **Visualization:** Line chart (queue time trend), Bar chart (queue time by pipeline), Single value (current queue length).
- **CIM Models:** N/A

---

### UC-12.2.7 · Test Coverage Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Declining test coverage increases risk of undetected bugs. Trending ensures quality standards are maintained.
- **App/TA:** Custom test report input
- **Data Sources:** Test result reports (JUnit XML, coverage reports)
- **SPL:**
```spl
index=cicd sourcetype="test_coverage"
| timechart span=1d latest(coverage_pct) as coverage by project
| where coverage < 80
```
- **Implementation:** Parse test coverage reports from CI/CD pipelines. Send to Splunk via HEC. Track coverage per project. Alert when coverage drops below minimum (e.g., <80%). Block merges when coverage decreases (enforce in CI).
- **Visualization:** Line chart (coverage trend per project), Bar chart (coverage by project), Single value (avg coverage %).
- **CIM Models:** N/A

---

### UC-12.2.8 · Security Scan Results in Pipeline
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** SAST/DAST/SCA findings in CI/CD pipelines catch vulnerabilities before they reach production. Tracking ensures security gates work.
- **App/TA:** Custom scan result input
- **Data Sources:** SAST (SonarQube, Checkmarx), DAST (ZAP, Burp), SCA (Snyk, Dependabot) results
- **SPL:**
```spl
index=cicd sourcetype="security_scan"
| stats count by severity, scan_type, project
| where severity IN ("Critical","High")
| sort -count
```
- **Implementation:** Ingest security scan results from CI/CD pipelines. Track findings by severity, type, and project. Alert on critical findings blocking deployment. Report on vulnerability introduction rate and fix rate.
- **Visualization:** Bar chart (findings by severity), Table (critical findings), Line chart (findings trend), Stacked bar (by scan type).
- **CIM Models:** N/A

---

### 12.3 Artifact & Package Management

**Primary App/TA:** Custom API inputs (Artifactory, Nexus), webhook receivers.

---

### UC-12.3.1 · Artifact Repository Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Full artifact repositories prevent builds from publishing. Storage monitoring and cleanup policy verification ensures CI/CD continuity.
- **App/TA:** Custom API input (Artifactory/Nexus)
- **Data Sources:** Repository storage metrics, cleanup policy logs
- **SPL:**
```spl
index=devops sourcetype="artifactory:storage"
| eval pct_used=round(used_space/total_space*100,1)
| where pct_used > 80
| table repository, used_space_gb, total_space_gb, pct_used
```
- **Implementation:** Poll Artifactory/Nexus storage API daily. Track storage per repository. Alert at 80% capacity. Verify cleanup policies are running and effective. Report on artifact growth rate.
- **Visualization:** Gauge (% capacity used), Bar chart (storage by repository), Line chart (storage trend).
- **CIM Models:** N/A

---

### UC-12.3.2 · Dependency Vulnerability Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Vulnerable dependencies in the software supply chain are a primary attack vector. Tracking ensures timely patching.
- **App/TA:** Snyk/Dependabot webhook
- **Data Sources:** SCA tool output (Snyk, Dependabot, GitHub Advisory)
- **SPL:**
```spl
index=devops sourcetype="snyk:vulnerability"
| where severity IN ("critical","high")
| stats count by project, package_name, cve_id, severity
| sort -severity, -count
```
- **Implementation:** Ingest SCA scan results. Track vulnerable dependencies by project, severity, and package. Alert on new critical/high findings. Track remediation time. Report on dependency health per team.
- **Visualization:** Table (vulnerable dependencies), Bar chart (vulns by project), Line chart (vulnerability trend), Single value (critical vulns count).
- **CIM Models:** N/A

---

### UC-12.3.3 · Package Download Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unusual package download patterns may indicate dependency confusion attacks or compromised internal packages.
- **App/TA:** Artifactory/Nexus access logs
- **Data Sources:** Repository access logs (download events)
- **SPL:**
```spl
index=devops sourcetype="artifactory:access"
| stats count by package_name, client_ip
| eventstats avg(count) as avg_downloads, stdev(count) as stdev_downloads by package_name
| where count > avg_downloads + 3*stdev_downloads
```
- **Implementation:** Monitor package download patterns. Baseline normal download volumes per package. Alert on statistical outliers. Watch for downloads of internal packages from external IPs. Track new/unknown packages being introduced.
- **Visualization:** Table (anomalous downloads), Bar chart (top downloaded packages), Line chart (download volume trend).
- **CIM Models:** N/A

---

### UC-12.3.4 · License Compliance Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Open-source license violations create legal risk. Automated tracking ensures compliance before code reaches production.
- **App/TA:** SCA tool output
- **Data Sources:** SCA license scan results (Snyk, FOSSA, WhiteSource)
- **SPL:**
```spl
index=devops sourcetype="sca:license"
| where license_risk IN ("high","critical") OR license IN ("GPL-3.0","AGPL-3.0")
| stats count by project, package_name, license, license_risk
| sort -license_risk
```
- **Implementation:** Ingest SCA license scan results. Track license types across all projects. Alert on copyleft licenses in commercial products. Report on license distribution for legal review. Block deployments with policy violations.
- **Visualization:** Table (license risks), Pie chart (license distribution), Bar chart (risks by project).
- **CIM Models:** N/A

---

### 12.4 Infrastructure as Code

**Primary App/TA:** Custom log inputs from CI/CD pipelines, Terraform Cloud API, Ansible callback plugins.

---

### UC-12.4.1 · Terraform Plan/Apply Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Every Terraform apply changes infrastructure. Full audit trail enables change management, impact analysis, and rollback decisions.
- **App/TA:** Terraform Cloud API, CI/CD output parsing
- **Data Sources:** Terraform CLI output (plan/apply), Terraform Cloud run events
- **SPL:**
```spl
index=iac sourcetype="terraform:run"
| table _time, workspace, user, action, resources_added, resources_changed, resources_destroyed, status
| sort -_time
```
- **Implementation:** Send Terraform run events to Splunk via HEC (from CI/CD pipeline or Terraform Cloud webhooks). Track resource changes per workspace. Alert on destroy operations. Correlate infrastructure changes with monitoring alerts.
- **Visualization:** Table (recent Terraform runs), Timeline (apply events), Bar chart (resource changes by workspace), Single value (applies today).
- **CIM Models:** N/A

---

### UC-12.4.2 · Configuration Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Drift from declared IaC state indicates manual changes that bypass change control, creating inconsistency and security risks.
- **App/TA:** Terraform plan output, cloud config monitoring
- **Data Sources:** Terraform plan output (no-change runs showing drift), AWS Config
- **SPL:**
```spl
index=iac sourcetype="terraform:plan"
| where drift_detected="true"
| table _time, workspace, resource_type, resource_name, drift_detail
| sort -_time
```
- **Implementation:** Schedule periodic `terraform plan` runs (detect-only). Parse output for unexpected changes. Alert on any drift detected. Correlate with cloud provider change logs to identify who made manual changes. Enforce drift remediation SLA.
- **Visualization:** Table (drifted resources), Single value (resources with drift), Bar chart (drift by workspace), Timeline (drift events).
- **CIM Models:** N/A

---

### UC-12.4.3 · Ansible Playbook Outcomes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Tracking Ansible run results ensures configuration management is working. Failed tasks indicate systems in unknown state.
- **App/TA:** Ansible callback plugin (Splunk HEC callback)
- **Data Sources:** Ansible callback output (play results, task results)
- **SPL:**
```spl
index=iac sourcetype="ansible:result"
| stats sum(ok) as ok, sum(changed) as changed, sum(failed) as failed, sum(unreachable) as unreachable by playbook, host
| where failed > 0 OR unreachable > 0
```
- **Implementation:** Configure Ansible Splunk callback plugin to send results to HEC. Track ok/changed/failed/unreachable counts per playbook and host. Alert on failed or unreachable hosts. Report on configuration management coverage.
- **Visualization:** Table (playbook results), Status grid (host × playbook status), Bar chart (failures by playbook), Single value (success rate).
- **CIM Models:** N/A

---

### UC-12.4.4 · Puppet/Chef Compliance Reports
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Configuration management compliance ensures systems match desired state. Non-compliance indicates security or operational risk.
- **App/TA:** Puppet/Chef report forwarding
- **Data Sources:** Puppet agent reports, Chef client run reports
- **SPL:**
```spl
index=iac sourcetype="puppet:report"
| stats latest(status) as status, latest(corrective_changes) as corrective by certname
| where status="failed" OR corrective > 0
```
- **Implementation:** Forward Puppet/Chef reports to Splunk. Track agent compliance rates. Alert on failed runs (nodes in non-compliant state). Monitor corrective changes (Puppet remediated drift). Report on fleet compliance percentage.
- **Visualization:** Single value (compliance %), Table (non-compliant nodes), Pie chart (status distribution), Line chart (compliance trend).
- **CIM Models:** N/A

---

### UC-12.4.5 · IaC Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Policy-as-code (OPA/Sentinel) prevents non-compliant infrastructure from being provisioned. Tracking blocked deployments validates governance.
- **App/TA:** Policy engine output (CI/CD integration)
- **Data Sources:** OPA/Sentinel policy check results, CI/CD pipeline logs
- **SPL:**
```spl
index=iac sourcetype="policy_check"
| where result="DENY"
| stats count by policy_name, workspace, resource_type
| sort -count
```
- **Implementation:** Ingest policy check results from CI/CD pipelines. Track denied provisions by policy and team. Alert on repeated violations (may indicate training need). Report on policy effectiveness and most-violated rules.
- **Visualization:** Bar chart (violations by policy), Table (denied provisions), Line chart (violation trend), Pie chart (by resource type).
- **CIM Models:** N/A

---

