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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.2 · Branch Protection Bypasses
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.4 · Secret Exposure Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.7 · GitHub Actions Workflow Run Time Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Workflow duration growth over time indicates growing tech debt, resource constraints, or inefficient pipeline design. Early detection enables optimization before velocity degrades.
- **App/TA:** Custom (GitHub API)
- **Data Sources:** GitHub /repos/:owner/:repo/actions/runs
- **SPL:**
```spl
index=devops sourcetype="github:actions_run"
| eval duration_min=round((updated_at_epoch-run_started_at_epoch)/60,1)
| timechart span=1d avg(duration_min) as avg_duration, median(duration_min) as median_duration by workflow_name
| where avg_duration > 0
```
- **Implementation:** Poll GitHub Actions API for workflow runs. Ingest run metadata (workflow_name, status, run_started_at, updated_at) to Splunk HEC. Calculate duration per run. Track 7-day and 30-day rolling averages. Alert when avg duration increases >20% week-over-week. Correlate with runner capacity and job concurrency.
- **Visualization:** Line chart (workflow duration trend by workflow), Bar chart (avg duration by workflow), Table (slowest workflows this week), Single value (p95 duration).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.8 · GitHub Actions Billing Usage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Cost
- **Value:** Approaching included minutes quota risks unexpected overages or workflow throttling. Proactive monitoring prevents billing surprises and supports capacity planning.
- **App/TA:** Custom (GitHub API)
- **Data Sources:** GitHub /orgs/:org/settings/billing/actions
- **SPL:**
```spl
index=devops sourcetype="github:actions_billing"
| eval pct_used=round(total_minutes_used/total_minutes_included*100,1)
| where pct_used > 70
| table _time, org, total_minutes_used, total_minutes_included, pct_used, total_paid_minutes_used
```
- **Implementation:** Poll GitHub billing API (requires org admin scope). Ingest minutes used vs. included per billing cycle. Alert at 70%, 85%, and 95% of included minutes. Track paid minutes consumption. Report on usage by repository and workflow for optimization.
- **Visualization:** Gauge (% of included minutes used), Single value (minutes remaining), Line chart (usage trend over billing cycle), Table (top consuming repos).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.9 · Branch Protection Bypass Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Complements UC-12.1.2 by correlating audit `protected_branch.policy_override` with push events for investigation packs.
- **App/TA:** GitHub audit log, webhook HEC
- **Data Sources:** `github:audit` policy_override, `github:webhook` push
- **SPL:**
```spl
index=devops sourcetype="github:audit" action="protected_branch.policy_override"
| join type=left max=1 repo [search index=devops sourcetype="github:webhook" event="push" | fields repository, ref, pusher, _time]
| table _time, actor, repo, branch, action, pusher
```
- **Implementation:** Require GitHub Advanced Security audit stream. Alert on any override; require VP approval ticket in lookup. Weekly report of overrides vs zero target.
- **Visualization:** Table (overrides), Timeline, Single value (count — target 0).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.10 · Force Push to Protected Branches
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Narrows UC-12.1.6 to default/release branches where history rewrite has highest impact.
- **App/TA:** GitHub/GitLab webhooks
- **Data Sources:** Push events with `forced=true` and `ref` matching protected branch patterns
- **SPL:**
```spl
index=devops sourcetype="github:webhook" event="push" forced="true"
| where match(ref,"refs/heads/(main|master|release/.*|production)")
| table _time, repository, ref, pusher, forced
| sort -_time
```
- **Implementation:** Maintain lookup of protected ref regex per org. Page on-call for production branch force pushes. Exclude documented release bot service accounts.
- **Visualization:** Table (force pushes), Timeline, Bar chart (by branch).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.11 · Sensitive File Commit Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Paths such as `.env`, `id_rsa`, `kubeconfig`, and `*.pem` in commits indicate credential sprawl even before secret scanning fires.
- **App/TA:** GitHub `push` webhook payload (commits[].modified/added)
- **Data Sources:** Push webhook with file path arrays, or GitHub compare API
- **SPL:**
```spl
index=devops sourcetype="github:webhook" event="push"
| mvexpand commits{}.modified limit=500
| where match(commits{}.modified,"(\.env|id_rsa|kubeconfig|\.pem|credentials\.xml)$")
| table _time, repository, commits{}.author.username, commits{}.modified
```
- **Implementation:** Expand commit file lists in ingestion. Alert on first match; auto-open rotation ticket. Pair with secret scanning (UC-12.1.4).
- **Visualization:** Table (sensitive paths), Bar chart (repos), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.12 · Repository Permission Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Team `maintain`/`admin` grants and visibility changes to `public` are higher risk than member adds (UC-12.1.5).
- **App/TA:** GitHub audit log
- **Data Sources:** `repo.update`, `team.add_repository`, `org.update_member`
- **SPL:**
```spl
index=devops sourcetype="github:audit" action IN ("repo.update","team.add_repository","repo.access")
| where visibility="public" OR permission IN ("admin","maintain")
| table _time, actor, repo, action, permission, visibility
```
- **Implementation:** Alert on public visibility toggles and admin grants. Quarterly access review export.
- **Visualization:** Table (high-risk changes), Timeline, Single value (public repos).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.13 · PR Review Bypass Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Merges with zero approvals or with only self-approval violate four-eyes policies.
- **App/TA:** GitHub GraphQL / pull_request webhook
- **Data Sources:** `pull_request` `closed` merged=true with `review_count`, `merge_method`
- **SPL:**
```spl
index=devops sourcetype="github:pull_request" action="closed" merged="true"
| where review_count=0 OR (review_count=1 AND merger=author)
| search base_ref IN ("main","master","production")
| table _time, repository, author, merger, review_count, base_ref
```
- **Implementation:** Ingest PR merged payload with review tally from API enrichment. Exclude bots via label. Alert in Splunk as backstop to branch protection.
- **Visualization:** Table (bypass merges), Bar chart (by author), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.14 · Fork Network Suspicious Activity
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Sudden stars/forks from new accounts or geo clusters can precede supply-chain attacks or leaked-token cloning.
- **App/TA:** GitHub audit + Events API
- **Data Sources:** `fork`, `create` events; `WatchEvent` bursts
- **SPL:**
```spl
index=devops sourcetype="github:meta" event_type IN ("ForkEvent","WatchEvent")
| bin _time span=1h
| stats dc(actor_id) as unique_actors, count by repo_name, _time
| where unique_actors > 50 OR count > 200
| sort -count
```
- **Implementation:** Ingest public repo events for crown-jewel repositories. Correlate with token scope changes. Feed threat intel on abusive ASNs.
- **Visualization:** Line chart (fork/star rate), Table (spikes), Geo map (actor country).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.15 · CODEOWNERS File Modification Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** Attackers may weaken review requirements by editing `CODEOWNERS` or `.github/CODEOWNERS`.
- **App/TA:** GitHub pull_request webhook
- **Data Sources:** PR `files[]` paths
- **SPL:**
```spl
index=devops sourcetype="github:pull_request" action IN ("opened","synchronize")
| where mvjoin(commit_files{},",") LIKE "%CODEOWNERS%"
| table _time, repository, author, title, commit_files
```
- **Implementation:** Parse file lists from PR payloads. Require CODEOWNER approval for CODEOWNERS changes via branch rules; alert on any edit pending rule rollout.
- **Visualization:** Table (PRs touching CODEOWNERS), Timeline, Single value (changes per quarter).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.16 · Large File Commit Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Security
- **Value:** Large blobs bloat repos, bypass review in diff viewers, and may hide embedded data.
- **App/TA:** GitHub `push` hook with size, Git LFS audit
- **Data Sources:** Commit statistics (`size`, `distinct_size`), LFS upload events
- **SPL:**
```spl
index=devops sourcetype="github:webhook" event="push"
| where commits{}.size > 5242880 OR commits{}.distinct_size > 5242880
| table _time, repository, commits{}.id, commits{}.size, pusher
```
- **Implementation:** Threshold 5MB default; tune per repo. Require LFS for binaries. Alert on repeated violations.
- **Visualization:** Table (large commits), Bar chart (by repo), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.17 · Signed Commit Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** Unsigned commits on protected branches weaken non-repudiation; verify GPG/SSH sig status.
- **App/TA:** GitHub commit signature API, push webhook enrichment
- **Data Sources:** Commit `verification.status` != `verified`
- **SPL:**
```spl
index=devops sourcetype="github:commit_status"
| where verification_status!="verified" AND branch IN ("main","master","production")
| stats count by repository, author, verification_status
| sort -count
```
- **Implementation:** Enrich push SHAs via API in pipeline. Alert on unverified commits after enforcement date. Whitelist bots with documented keys.
- **Visualization:** Table (unsigned commits), Line chart (compliance %), Pie chart (verified vs not).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.18 · Stale Branch Cleanup Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Security
- **Value:** Long-lived branches accumulate merge debt and stale code; tracking supports automated deletion policies.
- **App/TA:** GitHub GraphQL / repos API
- **Data Sources:** Branch `updated_at`, open PR linkage
- **SPL:**
```spl
index=devops sourcetype="github:branch_inventory"
| eval age_days=round((now()-strptime(updated_at,"%Y-%m-%dT%H:%M:%SZ"))/86400,1)
| where age_days > 180 AND protected="false"
| stats max(age_days) as max_age by repository, ref
| sort -max_age
```
- **Implementation:** Nightly job lists branches. Join with Jira for linked tickets. Auto-PR stale branch report to teams channel.
- **Visualization:** Table (stale branches), Bar chart (count by repo), Single value (branches >180d).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.19 · Repository Webhook Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Failed webhook deliveries break CI, security scanning, and Splunk ingestion—monitor delivery logs and HTTP status.
- **App/TA:** GitHub Webhook deliveries API, Splunk HEC receiver logs
- **Data Sources:** `delivery` records with `status_code`, `error_message`
- **SPL:**
```spl
index=devops sourcetype="github:webhook_delivery"
| where status_code>=400 OR delivered="false"
| stats count by repository, hook_id, status_code
| where count > 5
| sort -count
```
- **Implementation:** Poll recent deliveries or ingest GitHub Enterprise audit. Alert on sustained 4xx/5xx to Splunk HEC. Verify TLS cert on endpoint.
- **Visualization:** Table (failing hooks), Line chart (failure rate), Single value (open incidents).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.1.20 · Code Scanning Alert Trends
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** GitHub Advanced Security CodeQL/code scanning alert open/close rates show remediation velocity and new debt.
- **App/TA:** GitHub `code_scanning_alert` webhooks, API
- **Data Sources:** `alert` created, fixed, reopened events
- **SPL:**
```spl
index=devops sourcetype="github:code_scanning"
| timechart span=1w sum(eval(action="created")) as opened, sum(eval(action="fixed")) as fixed by rule_severity
| eval net_debt=opened-fixed
```
- **Implementation:** Ingest SARIF-related alert events. Track MTTR for Critical. Executive dashboard: net debt per language.
- **Visualization:** Line chart (opened vs fixed), Bar chart (by severity), Single value (open Critical alerts).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.5 · Failed Deployment Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.8 · Security Scan Results in Pipeline
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.9 · Jenkins Executor Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Busy executors as % of total and queue wait time indicate CI capacity. High utilization with long queue times signals need for additional agents or executor scaling.
- **App/TA:** Custom (Jenkins API, Prometheus metrics endpoint)
- **Data Sources:** Jenkins /metrics, /api/json?tree=computer[displayName,busyExecutors,totalExecutors]
- **SPL:**
```spl
index=cicd sourcetype="jenkins:metrics"
| eval utilization_pct=round(busy_executors/total_executors*100,1)
| timechart span=15m avg(utilization_pct) as avg_util, avg(queue_wait_sec) as avg_wait by computer
| where avg_util > 80 OR avg_wait > 300
```
- **Implementation:** Poll Jenkins /metrics (Prometheus format) or /computer/api/json for executor counts. Ingest busyExecutors, totalExecutors, and queue wait time. Calculate utilization per node. Alert when utilization >85% sustained for 15 min or queue wait >5 min. Correlate with build duration to right-size capacity.
- **Visualization:** Gauge (current utilization %), Line chart (utilization and queue wait trend), Bar chart (utilization by node), Single value (avg queue wait sec).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.10 · Jenkins Node Offline Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Build agents going offline impacts CI capacity and causes job failures. Rapid detection enables agent recovery or failover before queue backlog grows.
- **App/TA:** Custom (Jenkins API)
- **Data Sources:** Jenkins /computer/api/json
- **SPL:**
```spl
index=cicd sourcetype="jenkins:computer"
| where offline="true" OR offline=true
| table _time, displayName, offline, temporarilyOffline, numExecutors, idleExecutors
| sort -_time
```
- **Implementation:** Poll Jenkins /computer/api/json periodically (e.g., every 5 min). Ingest offline, temporarilyOffline, displayName per node. Alert immediately when any node goes offline. Exclude master if desired. Track offline duration and recurrence for capacity planning.
- **Visualization:** Table (offline nodes), Single value (offline node count — target: 0), Status grid (node × online/offline), Timeline (offline events).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.11 · GitLab CI Runner Availability
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Runner registration status and job queue time affect CI throughput. Offline or paused runners cause jobs to wait or fail; monitoring ensures runner fleet health.
- **App/TA:** Custom (GitLab API)
- **Data Sources:** GitLab /api/v4/runners, runner logs
- **SPL:**
```spl
index=cicd sourcetype="gitlab:runners"
| where active="false" OR paused="true" OR (status!="online" AND status!="idle")
| table _time, runner_id, description, active, paused, status, contacted_at
| sort -_time
```
- **Implementation:** Poll GitLab /api/v4/runners for runner list and status. Ingest active, paused, contacted_at. Optionally parse runner logs for connectivity errors. Alert when runner goes inactive or paused. Track job queue time from pipeline events. Report on runner utilization and availability SLA.
- **Visualization:** Table (inactive/paused runners), Single value (available runners), Status grid (runner × status), Line chart (job queue time trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.12 · GitLab Pipeline Duration Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Pipeline getting slower over time indicates growing tech debt or resource constraints. Trending enables proactive optimization before developer velocity degrades.
- **App/TA:** Custom (GitLab API)
- **Data Sources:** GitLab /api/v4/projects/:id/pipelines
- **SPL:**
```spl
index=cicd sourcetype="gitlab:pipeline"
| eval duration_sec=coalesce(duration, 0)
| timechart span=1d avg(duration_sec) as avg_duration, percentile(duration_sec, 95) as p95_duration by ref
| where avg_duration > 0
```
- **Implementation:** Poll GitLab pipelines API per project. Ingest id, ref, status, duration, created_at. Calculate duration for completed pipelines. Track 7-day rolling average. Alert when avg duration increases >25% week-over-week. Correlate with runner capacity and stage-level timings.
- **Visualization:** Line chart (pipeline duration trend by branch), Bar chart (avg duration by project), Table (slowest pipelines this week), Single value (p95 duration).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.14 · Jenkins Agent Offline Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Operational paging when executors disappear—complements UC-12.2.10 with severity tiers and agent labels (prod vs dev).
- **App/TA:** Splunk App for Jenkins, Jenkins API
- **Data Sources:** `/computer/api/json` `offline=true`, agent heartbeat
- **SPL:**
```spl
index=cicd sourcetype="jenkins:computer" (offline="true" OR offline=true)
| lookup jenkins_agent_tier displayName OUTPUT tier
| where tier="production"
| table _time, displayName, offline, labels, numExecutors
| sort -_time
```
- **Implementation:** Tag agents in lookup. Page immediately for production-labeled offline agents. Auto-create incident if >30% of pool offline.
- **Visualization:** Table (offline prod agents), Single value (count), Status grid (agent × tier).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.15 · Pipeline Stage Duration Regression
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Stage-level regression (e.g., `test` stage) surfaces before overall job duration crosses SLA (UC-12.2.2).
- **App/TA:** Jenkins Blue Ocean / GitLab job trace, GitHub Actions job logs
- **Data Sources:** Stage start/end timestamps per pipeline run
- **SPL:**
```spl
index=cicd sourcetype="cicd:stage"
| eval stage_duration_sec=duration_ms/1000
| eventstats median(stage_duration_sec) as med by stage_name, pipeline
| where stage_duration_sec > med*1.5 AND stage_duration_sec > 60
| table _time, pipeline, stage_name, stage_duration_sec, med
```
- **Implementation:** Emit structured stage events from CI. Baseline weekly medians. Alert on regression >50% vs median.
- **Visualization:** Line chart (stage duration trend), Table (regressions), Heatmap (stage × pipeline).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.16 · Build Artifact Integrity Verification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Compares published artifact checksums/Sigstore signatures against CI-recorded values to detect tampering at rest.
- **App/TA:** Cosign, Jenkins archive, S3/GCS object metadata
- **Data Sources:** Build record with `sha256`, registry manifest digest
- **SPL:**
```spl
index=cicd sourcetype="artifact:integrity"
| where expected_sha256!=actual_sha256 OR signature_valid="false"
| table _time, artifact_name, pipeline, expected_sha256, actual_sha256
```
- **Implementation:** CI stores expected hash in Splunk; registry poll compares. Alert on any mismatch before prod promotion.
- **Visualization:** Table (mismatches — target empty), Timeline, Single value (failed verifications).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.17 · Deploy Approval Bypass Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Production deploys without change ticket or approval group in CD system (Spinnaker, Argo Rollouts, Harness).
- **App/TA:** CD platform audit logs
- **Data Sources:** Deployment events with `approval_id`, `change_ticket`
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" environment="production"
| where isnull(approval_id) OR isnull(change_ticket)
| search user!="svc_cd_bot"
| table _time, application, user, version, environment
```
- **Implementation:** Enforce required fields in CD templates. Alert on nulls. Correlate with Entra/Okta for human actors.
- **Visualization:** Table (unapproved deploys), Timeline, Single value (violations 30d).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.18 · Parallel Build Resource Contention
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Runner saturation lengthens CI pipelines and causes flaky tests that block releases. Correlating saturation metrics with P95 job duration justifies autoscaling investment and prevents false 'code regression' blame when infrastructure is the root cause.
- **App/TA:** Jenkins metrics, Kubernetes node metrics
- **Data Sources:** Active executor count, node CPU utilization, overlapping job IDs
- **SPL:**
```spl
index=cicd sourcetype="jenkins:metrics"
| eval utilization_pct=round(busy_executors/total_executors*100,1)
| join type=left max=1 _time [search index=infra sourcetype="kube:node" | stats avg(cpu_usage) as node_cpu by _time]
| where utilization_pct>90 AND node_cpu>85
| table _time, computer, utilization_pct, node_cpu
```
- **Implementation:** Align timestamps between CI and Kubernetes. Alert when high utilization coincides with p95 build time spike. Scale runner pool.
- **Visualization:** Line chart (utilization vs build time), Table (contention windows), Bar chart (by node pool).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.19 · Flaky Test Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Tests that pass/fail without code changes waste time and hide real failures; quarantine candidates identified by pass rate variance.
- **App/TA:** JUnit XML ingest, Buildkite/GitHub Actions annotations
- **Data Sources:** Test case name, suite, result per run
- **SPL:**
```spl
index=cicd sourcetype="junit:result"
| stats count(eval(result="SUCCESS")) as pass, count(eval(result="FAILURE")) as fail, count as runs by test_case, class_name
| eval flake_rate=round(fail/runs*100,1)
| where runs>10 AND flake_rate>10 AND flake_rate<90
| sort -flake_rate
```
- **Implementation:** Minimum 10 runs for statistics. File Jira for quarantine when flake_rate >25%. Track fix SLA.
- **Visualization:** Table (flaky tests), Bar chart (flake rate), Line chart (trend after fix).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.20 · Deployment Frequency Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** DORA dashboard slice—deployments per service per day with team and application tags (extends UC-12.2.3).
- **App/TA:** `deployment_event` HEC
- **Data Sources:** Normalized deploy events with `service`, `team`
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" environment="production"
| bin _time span=1d
| stats count as deploys by _time, team, service
| sort -deploys
```
- **Implementation:** Tag all deploy pipelines. Weekly report to leadership. Compare to DORA elite thresholds (on-demand per day).
- **Visualization:** Line chart (deploys per day by team), Bar chart (by service), Single value (deploys 7d).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.21 · Lead Time for Changes (Percentile)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** p95 lead time exposes tail latency hiding in averages (UC-12.2.4).
- **App/TA:** Git + deployment correlation
- **Data Sources:** First commit SHA timestamp → prod deploy time
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" environment="production"
| eval lead_hours=(deploy_time_epoch-commit_time_epoch)/3600
| stats avg(lead_hours) as avg_lt, p95(lead_hours) as p95_lt by application
| where p95_lt > 168
| sort -p95_lt
```
- **Implementation:** Require deploy events to carry commit SHA. Alert when p95 exceeds one week. Segment by monorepo vs microservice.
- **Visualization:** Histogram (lead time), Table (p95 by app), Line chart (p95 trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.22 · Mean Time to Recovery (MTTR)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Time from incident detection or deploy failure to successful restore—core DORA metric.
- **App/TA:** PagerDuty/Opsgenie, deployment events
- **Data Sources:** Incident `created_at`, `resolved_at`; rollback `deploy_time`
- **SPL:**
```spl
index=itsm sourcetype="pagerduty:incident"
| eval mttr_min=(resolved_epoch-ack_epoch)/60
| stats avg(mttr_min) as avg_mttr, p95(mttr_min) as p95_mttr by service
| where avg_mttr > 60
| sort -avg_mttr
```
- **Implementation:** Correlate PD incidents with service. For deploy failures, measure time to healthy deploy. Executive review monthly.
- **Visualization:** Table (MTTR by service), Line chart (avg MTTR trend), Gauge (vs SLA).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.23 · Change Failure Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Ratio of failed deployments or hotfix-required releases to total deployments—DORA metric.
- **App/TA:** Deployment + incident linkage
- **Data Sources:** `deployment_event` outcome, post-deploy incident within 1h
- **SPL:**
```spl
index=cicd sourcetype="deployment_event" environment="production"
| eval failed=if(status="failed" OR incident_within_1h="true",1,0)
| stats sum(failed) as fails, count as total by application
| eval cfr=round(fails/total*100,2)
| where cfr > 15
| sort -cfr
```
- **Implementation:** Flag incidents linked to version within 1h window. Target CFR <15% for mature teams. Review outliers in postmortems.
- **Visualization:** Bar chart (CFR by app), Line chart (CFR trend), Single value (org CFR).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.24 · Pipeline Secret Rotation Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** CI/CD credentials (vault tokens, cloud API keys) approaching expiry without rotation break builds and create risk.
- **App/TA:** Vault audit, cloud IAM credential reports
- **Data Sources:** Secret `expires_at`, `last_rotated`
- **SPL:**
```spl
index=secrets sourcetype="vault:audit" OR sourcetype="ci:credential_inventory"
| eval days_left=(expiry_epoch-now())/86400
| where days_left < 14 AND days_left > 0
| table secret_name, pipeline, days_left, owner
| sort days_left
```
- **Implementation:** Export CI secret inventory from Vault or sealed secrets metadata. Alert at 14/7/1 days. Block pipeline if expired.
- **Visualization:** Table (expiring secrets), Gauge (compliance %), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.25 · Build Queue Wait Time SLA
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** SLA-focused view of queue delay—% of jobs waiting >5 min (extends UC-12.2.6).
- **App/TA:** Jenkins queue API, GitLab pending jobs
- **Data Sources:** `queue_wait_ms`, `queued_at`, `started_at`
- **SPL:**
```spl
index=cicd sourcetype="jenkins:build"
| eval wait_min=queue_wait_ms/60000
| stats count(eval(wait_min>5)) as slow_queued, count as total
| eval pct_slow=round(slow_queued/total*100,2)
| where pct_slow > 10
```
- **Implementation:** Emit wait time per build. Alert if >10% of builds exceed 5 min queue in 1h window. Scale agents.
- **Visualization:** Line chart (p95 wait time), Histogram (wait distribution), Single value (% >5min).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.26 · Test Coverage Regression
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** PRs that reduce line coverage vs main branch—visibility for governance (pair with CI gates).
- **App/TA:** Cobertura/JaCoCo XML to HEC
- **Data Sources:** `coverage_pct` per branch, PR number
- **SPL:**
```spl
index=cicd sourcetype="test_coverage" branch=main
| eventstats latest(coverage_pct) as main_cov by project
| join max=1 project [search index=cicd sourcetype="test_coverage" branch!=main | fields project, coverage_pct, pr]
| eval delta=coverage_pct-main_cov
| where delta < -1
| table project, pr, coverage_pct, main_cov, delta
```
- **Implementation:** Compare PR coverage to main on each build. Alert on >1% drop. Block merge in CI when integrated.
- **Visualization:** Table (regressions), Bar chart (delta by project), Line chart (main coverage trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.2.27 · Pipeline Resource Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** CPU/memory per runner job—right-sizing and spot vs on-demand mix.
- **App/TA:** Kubernetes metrics, Jenkins Prometheus plugin
- **Data Sources:** `container_cpu_usage_seconds`, `job_duration`, resource requests
- **SPL:**
```spl
index=infra sourcetype="kube:pod_metrics" label_app="ci-runner"
| bin _time span=5m
| stats avg(cpu_cores) as avg_cpu by pod_name
| join max=1 pod_name [search index=cicd sourcetype="jenkins:build" | stats avg(duration) as job_dur by executor_pod]
| table pod_name, avg_cpu, job_dur
```
- **Implementation:** Correlate runner pods with jobs. Identify over-provisioned runners. Recommend requests/limits tuning.
- **Visualization:** Table (utilization by runner), Bar chart (avg CPU per job type), Line chart (efficiency trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.2 · Dependency Vulnerability Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Wave:** 🐢 crawl
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.5 · Terraform State Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration, Compliance
- **Value:** Planned vs. applied resource count and drift between declared and actual infrastructure indicate manual changes or state corruption. Detection ensures IaC remains source of truth and supports compliance audits.
- **App/TA:** Custom (terraform plan output)
- **Data Sources:** terraform plan JSON output (-json flag)
- **SPL:**
```spl
index=iac sourcetype="terraform:plan_json"
| eval add_count=coalesce(resource_changes_add, 0), change_count=coalesce(resource_changes_change, 0), destroy_count=coalesce(resource_changes_destroy, 0)
| where add_count > 0 OR change_count > 0 OR destroy_count > 0
| table _time, workspace, plan_mode, add_count, change_count, destroy_count, resource_changes
| sort -_time
```
- **Implementation:** Run `terraform plan -json` in CI or on schedule. Parse JSON output for resource_changes (add, change, destroy). Ingest to Splunk via HEC. Alert on any unexpected changes (drift) in detect-only runs. Track planned vs. applied resource counts per workspace. Correlate drift events with cloud provider change logs. Enforce drift remediation SLA and report on compliance.
- **Visualization:** Table (drift events with resource details), Single value (workspaces with drift), Bar chart (add/change/destroy by workspace), Timeline (drift detection events).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.6 · Container Image Vulnerability Scan Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** CI gate failures when Trivy/Grype/ECR scanning cannot pull image or scanner errors—distinct from found CVEs (UC-12.3.2).
- **App/TA:** Trivy JSON output, Harbor webhook
- **Data Sources:** Scan exit code, `Status: ERROR` in SARIF
- **SPL:**
```spl
index=devops sourcetype="container:scan"
| where scan_status!="SUCCESS" OR match(_raw,"(?i)(timeout|failed to pull|manifest unknown)")
| stats count by image_ref, scanner, error_message
| sort -count
```
- **Implementation:** Alert on scanner infrastructure failures separately from policy violations. Retry with backoff; page platform team on registry outages.
- **Visualization:** Table (failed scans), Line chart (failure rate), Single value (open scan errors).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.7 · Package Dependency Audit Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** New AGPL/GPL or typosquat package names in lockfiles—policy engine output beyond CVE severity.
- **App/TA:** FOSSA, `npm audit` JSON, OSV
- **Data Sources:** Policy violation events `license_policy`, `dependency_policy`
- **SPL:**
```spl
index=devops sourcetype="sca:policy"
| where policy_result="violation" OR risk="blocked"
| stats count by project, package_name, policy_name
| sort -count
```
- **Implementation:** Map policies to Splunk alerts. Weekly license review for new copyleft in commercial products.
- **Visualization:** Table (violations), Bar chart (by policy), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.8 · Artifact Retention Policy Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Capacity
- **Value:** Verifies cleanup jobs deleted snapshots per policy; stale artifacts past retention indicate failed garbage collection.
- **App/TA:** Artifactory/Nexus repository metadata API
- **Data Sources:** Artifact `last_downloaded`, `created`, retention rule ID
- **SPL:**
```spl
index=devops sourcetype="artifactory:artifact_age"
| eval age_days=(now()-created_epoch)/86400
| where age_days > retention_days + 7
| stats count by repository, path
| sort -count
```
- **Implementation:** Compare artifact age to configured retention. Alert on drift >7 days past policy. Audit quarterly for legal hold exceptions.
- **Visualization:** Table (over-retained artifacts), Bar chart (by repo), Single value (non-compliant count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.9 · SBOM Generation Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** CycloneDX/SPDX missing for release builds breaks supply-chain attestation requirements (EO 14028).
- **App/TA:** Syft, build pipeline attestations
- **Data Sources:** `sbom_generated=true`, artifact `sbom_path`
- **SPL:**
```spl
index=cicd sourcetype="release:build"
| where sbom_present="false" AND environment="release"
| table _time, application, version, build_id
| sort -_time
```
- **Implementation:** Fail release stage if SBOM not uploaded to blob store. Track SBOM format version (CycloneDX 1.5).
- **Visualization:** Table (missing SBOM), Single value (compliance %), Line chart (trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.10 · Artifact Signing Verification
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Cosign/Notary verification results at deploy time—signature missing or wrong key.
- **App/TA:** Cosign, Sigstore Rekor
- **Data Sources:** Verify command JSON `verified`, `issuer`; lookup `trusted_signing_issuers.csv` maintained by the platform team with `issuer` → `trusted` (true/false)
- **SPL:**
```spl
index=cicd sourcetype="cosign:verify"
| lookup trusted_signing_issuers.csv issuer OUTPUT trusted
| where verified="false" OR trusted!="true"
| table _time, image, issuer, reason
```
- **Implementation:** Ingest verification from CD pipeline. Block deploy on false. Rotate keys per runbook.
- **Visualization:** Table (failed verifications), Timeline, Single value (failed count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.11 · Package Provenance Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** SLSA provenance predicate links artifact digest to git source SHA and builder ID—detects builds not from trusted pipelines.
- **App/TA:** SLSA provenance JSON, GitHub attestations
- **Data Sources:** `predicate.buildDefinition`, `subject.digest`
- **SPL:**
```spl
index=cicd sourcetype="slsa:provenance"
| where builder_id!="https://github.com/org/trusted-workflow" OR commit_ref!=expected_git_sha
| table _time, artifact_digest, builder_id, commit_ref, expected_git_sha
```
- **Implementation:** Store expected builder allowlist. Alert on provenance mismatch for prod images.
- **Visualization:** Table (mismatches), Bar chart (by builder), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.3.12 · Registry Storage Growth
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Daily growth rate of container/NPM registry—forecast disk exhaustion (extends UC-12.3.1).
- **App/TA:** Harbor/ECR/Artifactory storage API
- **Data Sources:** Total bytes, per-repo breakdown
- **SPL:**
```spl
index=devops sourcetype="registry:storage"
| timechart span=1d sum(size_bytes) as total by registry_name
| predict total as forecast
```
- **Implementation:** Alert when weekly growth >20% or forecast crosses 85% capacity in <90 days. Recommend GC tuning.
- **Visualization:** Line chart (storage growth), Area chart (by project), Single value (days to full).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.6 · Pipeline Failure Root Cause Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Recurring failure causes (e.g., flaky tests, env issues) slow delivery. Trending root causes supports targeted remediation and stability.
- **App/TA:** Jenkins/GitHub Actions/Azure DevOps TAs
- **Data Sources:** Pipeline run logs, failure reasons, stage outcomes
- **SPL:**
```spl
index=cicd sourcetype="jenkins:build"
| where result="FAILURE"
| rex field=message "(?<cause>Timeout|OOM|Connection refused|AssertionError|dependency)"
| stats count by cause, job_name
| sort -count
```
- **Implementation:** Parse failure messages and stack traces from CI logs. Classify by cause (test, env, dependency, timeout). Alert on spike in a specific cause. Report on top failure reasons by job and week.
- **Visualization:** Bar chart (failures by cause), Table (job × cause), Line chart (failure rate trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.7 · Container Image Build and Push Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Unauthorized or untagged image pushes can introduce risk. Auditing build and push events supports supply chain security and compliance.
- **App/TA:** Registry and CI logs (ECR, ACR, Harbor, Docker)
- **Data Sources:** Image push events, build logs, registry audit
- **SPL:**
```spl
index=registry sourcetype="registry:audit"
| search action=push
| stats latest(_time) as last_push, count by image_name, actor, tag
| table image_name, tag, actor, last_push, count
```
- **Implementation:** Ingest registry audit and CI build events. Alert on push from unexpected identity or to production repo without tag policy. Report on image provenance and push frequency.
- **Visualization:** Table (push events), Timeline (pushes by image), Bar chart (pushes by actor).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.8 · Release Gate and Approval Lag
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Long approval or gate wait times delay releases. Monitoring gate duration and approval latency supports process improvement.
- **App/TA:** Release management / pipeline TAs
- **Data Sources:** Gate and approval timestamps from release pipelines
- **SPL:**
```spl
index=cicd sourcetype="release:gate"
| eval wait_sec=approved_time - submitted_time
| stats avg(wait_sec) as avg_wait, max(wait_sec) as max_wait by stage_name, environment
| where avg_wait > 3600
```
- **Implementation:** Ingest gate and approval events from Azure DevOps, Spinnaker, or similar. Compute wait time per stage. Alert when average wait exceeds threshold. Report on approval latency by stage and approver.
- **Visualization:** Bar chart (wait time by stage), Table (slow gates), Line chart (approval latency trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.9 · Feature Flag and Experiment Rollout Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Feature flags and experiments affect user experience. Monitoring rollout percentage and error rate per flag supports safe rollouts and rollback.
- **App/TA:** Feature flag provider logs, app telemetry
- **Data Sources:** Flag evaluation logs, rollout events, error rates by flag
- **SPL:**
```spl
index=app sourcetype="feature_flag:eval"
| bin _time span=1h
| stats count, sum(eval(if(error="true",1,0))) as errors by flag_name, variant, _time
| eval error_rate=round((errors/count)*100, 2)
| where error_rate > 5
```
- **Implementation:** Ingest flag evaluation and error data. Track rollout % and error rate per flag/variant. Alert on error rate spike after rollout. Report on flag adoption and performance by variant.
- **Visualization:** Line chart (error rate by flag), Table (flags with high errors), Bar chart (rollout % by variant).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.10 · Deployment Rollback and Canary Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failed canaries or automatic rollbacks indicate bad releases. Tracking rollback rate and canary metrics ensures safe deployments.
- **App/TA:** Kubernetes/Argo/Spinnaker TAs, app metrics
- **Data Sources:** Deployment events, canary success/failure, rollback triggers
- **SPL:**
```spl
index=k8s sourcetype="kube:deployment"
| search (reason="Rollback" OR reason="CanaryFailed" OR type="Rollback")
| stats count by namespace, deployment, reason
| sort -count
```
- **Implementation:** Ingest deployment and canary outcome events. Alert on any rollback or canary failure. Correlate with change and error metrics. Report on rollback rate by service and time.
- **Visualization:** Table (rollback events), Single value (rollbacks this week), Line chart (canary success rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.11 · ArgoCD Application Sync Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration, Fault
- **Value:** Out-of-sync or degraded applications in ArgoCD indicate GitOps drift or deployment failures. Detection ensures desired state matches cluster state and enables rapid remediation.
- **App/TA:** Custom (ArgoCD API)
- **Data Sources:** ArgoCD /api/v1/applications
- **SPL:**
```spl
index=devops sourcetype="argocd:application"
| where sync_status!="Synced" OR health_status!="Healthy" OR health_status="Degraded"
| table _time, name, namespace, sync_status, health_status, revision, message
| sort -_time
```
- **Implementation:** Poll ArgoCD API /api/v1/applications for application list. Ingest sync.status, health.status, revision, message. Alert when sync_status is OutOfSync or health_status is Degraded/Progressing for >5 min. Track sync and health history. Correlate with Git commits and cluster events. Report on application sync health and remediation time.
- **Visualization:** Table (out-of-sync/degraded apps), Single value (synced apps %), Status grid (app × sync/health), Timeline (sync status changes).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.12 · Terraform Plan Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Scheduled CI `terraform plan` runs that show changes when no pipeline apply occurred—focused operational view vs UC-12.4.2.
- **App/TA:** Terraform CLI in CI, Terraform Cloud
- **Data Sources:** Plan JSON `resource_changes`, `plan_mode=scheduled`
- **SPL:**
```spl
index=iac sourcetype="terraform:plan_ci"
| where plan_mode="scheduled" AND (changes_add>0 OR changes_change>0 OR changes_destroy>0)
| table _time, workspace, changes_add, changes_change, changes_destroy, run_url
| sort -_time
```
- **Implementation:** Nightly plan-only workflow for prod workspaces. Alert on any change. Auto-create drift remediation ticket.
- **Visualization:** Table (drift plans), Timeline, Bar chart (by workspace).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.13 · CloudFormation Stack Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration, Compliance
- **Value:** AWS `DetectStackDrift` results show live resources diverging from template—essential for CloudFormation-centric teams.
- **App/TA:** AWS CloudFormation API, CloudTrail
- **Data Sources:** `StackDriftStatus`, `StackResourceDriftStatus`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudformation:drift"
| where StackDriftStatus="DRIFTED" OR DetectionStatus="DETECTION_FAILED"
| stats latest(_time) as last_check, values(LogicalResourceId) as drifted_resources by StackName, region
| sort -last_check
```
- **Implementation:** Schedule drift detection after stack updates. Alert on DRIFTED. Optionally ingest full drift detail JSON.
- **Visualization:** Table (drifted stacks), Bar chart (by account), Timeline.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

- **References:** [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-12.4.14 · Ansible Playbook Failure Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Failure rate per playbook and run—trending layer on top of UC-12.4.3 outcomes.
- **App/TA:** Ansible Splunk callback, ARA
- **Data Sources:** Per-play `failed`, `unreachable`, `playbook`
- **SPL:**
```spl
index=iac sourcetype="ansible:result"
| stats sum(failed) as fails, sum(unreachable) as unreach, count as runs by playbook
| eval fail_rate=round((fails+unreach)/runs*100,2)
| where fail_rate > 5
| sort -fail_rate
```
- **Implementation:** Alert when fail_rate >5% over 24h. Page for security baseline playbooks. Host-level drilldown from same data.
- **Visualization:** Line chart (fail rate trend), Table (worst playbooks), Bar chart (by team).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.15 · Policy-as-Code Violation Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** OPA, Sentinel, or Conftest denials over time—spikes after new policy rollout (extends UC-12.4.5).
- **App/TA:** OPA decision logs, Terraform Cloud policy sets
- **Data Sources:** `result="fail"`, `policy_path`, `namespace`
- **SPL:**
```spl
index=iac sourcetype="opa:decision"
| where result="fail"
| timechart span=1d count by policy_name
```
- **Implementation:** Baseline failures per policy. Alert on 3× week-over-week spike. Run education before switching to hard-fail.
- **Visualization:** Line chart (violations over time), Bar chart (by policy), Table (top namespaces).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.4.16 · IaC Module Version Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Terraform module sources below approved minimum semver—reduces stale or vulnerable module usage.
- **App/TA:** `terraform-config-inspect`, CI parse of resolved modules
- **Data Sources:** Module `name`, `version` from `terraform init -json`
- **SPL:**
```spl
index=iac sourcetype="terraform:modules"
| lookup terraform_module_allowed module_name OUTPUT min_version
| where semver_compare(module_version, min_version) < 0
| table workspace, module_name, module_version, min_version
```
- **Implementation:** Weekly compliance report. Enforce minimum via Sentinel/OPA in pipeline. Pair with private registry pinning.
- **Visualization:** Table (non-compliant modules), Bar chart (version lag), Line chart (compliance %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 12.5 GitOps & Deployment Automation

**Primary App/TA:** Splunk Add-on for Argo CD, Splunk Add-on for Kubernetes, GitHub Actions log forwarder, GitLab CI integration, Splunk Connect for Helm/Flux metrics, custom HEC for GitOps APIs.

---

### UC-12.5.1 · ArgoCD Sync Status Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Configuration
- **Value:** Failed or stuck sync operations leave clusters diverging from Git and block releases; surfacing them quickly limits blast radius and restores desired state.
- **App/TA:** Splunk Add-on for Argo CD, custom ArgoCD API/audit input
- **Data Sources:** `sourcetype=argocd:application`, `sourcetype=argocd:audit`
- **SPL:**
```spl
index=devops (sourcetype="argocd:application" OR sourcetype="argocd:audit")
| search sync_status IN ("OutOfSync","Unknown") OR operation_state="Error" OR phase="Failed"
| stats latest(_time) as last_seen, values(message) as messages by name, namespace, project
| sort -last_seen
```
- **Implementation:** Ingest Argo CD application CR status and controller/audit logs via add-on or HEC. Normalize `sync_status`, `operation_state`, and error messages. Alert when sync fails or remains in Error/Failed beyond a short window. Correlate with Git commits and cluster events.
- **Visualization:** Table (failed apps), Single value (apps in failed sync), Timeline (sync operations), Status grid by project.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.2 · ArgoCD Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration, Compliance
- **Value:** Live cluster drift from Git-defined manifests risks untracked changes and audit gaps; detecting drift prioritizes reconciliation before incidents or compliance findings.
- **App/TA:** Splunk Add-on for Argo CD
- **Data Sources:** `sourcetype=argocd:application`
- **SPL:**
```spl
index=devops sourcetype="argocd:application"
| where sync_status="OutOfSync" OR health_status="Degraded"
| eval drift_indicator=if(sync_status="OutOfSync","manifest_drift","health_degraded")
| stats count by name, namespace, sync_status, health_status, drift_indicator
| sort -count
```
- **Implementation:** Poll or stream Argo CD application objects so `sync_status` and `health_status` are current. Treat sustained `OutOfSync` as drift unless an approved sync window applies. Alert with application, revision, and diff summary fields when available.
- **Visualization:** Table (drifted apps), Bar chart (drift by cluster/namespace), Line chart (drift count over time).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.3 · Flux Reconciliation Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Availability
- **Value:** Unhealthy Flux `Kustomization`/`HelmRelease` resources stop automated delivery; monitoring reconciliation ensures continuous GitOps and catches controller or source errors early.
- **App/TA:** Custom (Flux logs/metrics), Splunk OTel Collector for Kubernetes
- **Data Sources:** `sourcetype=fluxcd:controller`, `sourcetype=kube:container_flux`
- **SPL:**
```spl
index=devops (sourcetype="fluxcd:controller" OR sourcetype="kube:container_flux")
| search (status="False" AND type="Ready") OR level="error" OR msg="*reconciliation*failed*"
| stats count by namespace, name, kind, message
| sort -count
```
- **Implementation:** Forward Flux source-controller, kustomize-controller, and helm-controller logs (or scrape status conditions from CRDs) into Splunk. Parse Ready=False conditions and error strings. Alert on reconciliation failures or backlog growth. Group by cluster and tenant.
- **Visualization:** Table (failed resources), Single value (failed reconciliations), Timeline (controller errors), Bar chart (failures by kind).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.4 · GitHub Actions Workflow Failure Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Fault
- **Value:** A rising workflow failure rate signals flaky pipelines, bad merges, or infra issues that slow delivery and can block production paths.
- **App/TA:** GitHub Audit Log / webhook forwarder, Splunk HTTP Event Collector
- **Data Sources:** `sourcetype=github:workflow_run`, `sourcetype=github:webhook`
- **SPL:**
```spl
index=devops sourcetype="github:workflow_run"
| eval failed=if(conclusion IN ("failure","cancelled","timed_out"),1,0)
| timechart span=1h sum(failed) as failures, count as runs
| eval failure_rate=round(100*failures/runs,2)
| fields _time, failure_rate, failures, runs
```
- **Implementation:** Ingest workflow_run events with conclusion, workflow, branch, and repository. Compute failure rate over sliding windows per repo or default branch. Alert when failure_rate exceeds baseline or a fixed threshold. Exclude expected flaky jobs via labels when possible.
- **Visualization:** Line chart (failure rate), Stacked bar (conclusions), Single value (last 24h failure %), Table (top failing workflows).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.5 · GitHub Actions Runner Queue Depth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Deep job queues delay CI feedback and releases; tracking queue depth distinguishes runner capacity problems from workflow volume spikes.
- **App/TA:** GitHub Enterprise Server / self-hosted runner scripts, custom metrics via Actions API
- **Data Sources:** `sourcetype=github:runner_metrics`, `sourcetype=github:workflow_job`
- **SPL:**
```spl
index=devops (sourcetype="github:workflow_job" OR sourcetype="github:runner_metrics")
| eval queued=if(status="queued",1,0)
| bin _time span=5m
| stats sum(queued) as queued_jobs, dc(runner_name) as active_runners by _time, organization
| sort _time
```
- **Implementation:** Emit periodic queue depth from self-hosted runner APIs or poll workflow jobs in `queued` state. For hosted runners, approximate backlog using queued job counts and wait times. Alert when queued_jobs or wait time p95 exceeds SLO. Plan runner pool scaling from trends.
- **Visualization:** Area chart (queued jobs), Line chart (queue wait p95), Single value (current queue depth), Table (repos with longest waits).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.6 · GitLab CI Pipeline Duration Regression
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Sudden pipeline duration increases waste compute budgets and slow merges; regression detection isolates stages, runners, or dependencies that changed.
- **App/TA:** GitLab webhook / API integration, Splunk Add-on for GitLab (custom)
- **Data Sources:** `sourcetype=gitlab:pipeline`
- **SPL:**
```spl
index=devops sourcetype="gitlab:pipeline" status="success"
| eval duration_min=round(duration_sec/60,2)
| eventstats median(duration_min) as baseline_med by project_id, ref
| eval regression=if(duration_min > baseline_med * 1.5, 1, 0)
| where regression=1
| table _time, project, ref, duration_min, baseline_med, pipeline_id
| sort -_time
```
- **Implementation:** Ingest pipeline completion events with duration, project, ref, and stage timings if available. Establish rolling median baseline per project/branch. Alert when duration exceeds threshold multiplier or absolute cap. Drill into job-level logs for the slow stage.
- **Visualization:** Line chart (median duration trend), Table (regression events), Box plot (duration distribution by pipeline).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.7 · Deployment Rollback Frequency Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Change
- **Value:** Frequent rollbacks indicate release quality or progressive-delivery issues; tracking frequency supports blameless review and release process tuning.
- **App/TA:** Argo Rollouts, Flagger, Kubernetes audit, CI/CD webhook
- **Data Sources:** `sourcetype=kube:events`, `sourcetype=argocd:application`
- **SPL:**
```spl
index=devops (sourcetype="kube:events" OR sourcetype="argocd:application")
| search rollback="true" OR reason="Rollback" OR message="*rollback*"
| timechart span=1d count by namespace
```
- **Implementation:** Tag rollback events from Argo Rollouts/Flagger, deployment controllers, or GitOps sync history. Deduplicate by deployment and revision. Report rollbacks per service and environment. Correlate with failed health checks or error spikes.
- **Visualization:** Line chart (rollbacks per day), Bar chart (rollbacks by service), Table (recent rollbacks with revision).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.8 · Helm Release Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Configuration
- **Value:** Failed or pending Helm releases leave workloads partially updated or broken; monitoring release status prevents silent partial deploys.
- **App/TA:** Helm CLI / Flux helm-controller logs, `splunk-otel-collector` for cluster metrics
- **Data Sources:** `sourcetype=helm:release`, `sourcetype=fluxcd:controller`
- **SPL:**
```spl
index=devops (sourcetype="helm:release" OR (sourcetype="fluxcd:controller" AND kind="HelmRelease"))
| where status IN ("failed","pending-upgrade","pending-rollback") OR info_status!="deployed"
| stats latest(_time) as last_event, values(message) as notes by release, namespace, chart, status
| sort -last_event
```
- **Implementation:** Ingest Helm release status from `helm list -o json` jobs, Flux HelmRelease conditions, or controller logs. Map statuses to deployed/failed/pending. Alert on non-deployed steady states. Include chart version and values hash for change correlation.
- **Visualization:** Table (unhealthy releases), Single value (non-deployed count), Timeline (release operations).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.9 · Kustomize Build Error Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Configuration
- **Value:** Kustomize build failures block manifests from applying; early detection shortens fix time for overlay, patch, or base reference mistakes.
- **App/TA:** CI pipeline logs, Flux kustomize-controller
- **Data Sources:** `sourcetype=gitlab:job`, `sourcetype=github:workflow_job`, `sourcetype=fluxcd:controller`
- **SPL:**
```spl
index=devops (sourcetype="fluxcd:controller" OR sourcetype="gitlab:job" OR sourcetype="github:workflow_job")
| search kustomize_build OR "kustomize build" OR "error building kustomize"
| rex field=_raw "(?<err_msg>kustomize:.*|error:.*)"
| stats count by project, pipeline_id, err_msg
| sort -count
```
- **Implementation:** Capture stderr from CI jobs and Flux kustomize-controller when `kustomize build` runs. Extract file paths and duplicate key errors. Alert on any build failure on protected branches or for production overlays. Feed counts back to repo owners.
- **Visualization:** Table (build errors), Bar chart (errors by repo), Timeline (failure events).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.5.10 · GitOps Deployment Lead Time
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Measuring Git commit-to-production lead time exposes bottlenecks in review, CI, and sync so teams can optimize end-to-end delivery speed.
- **App/TA:** Git + ArgoCD/Flux correlation (custom), DORA metrics scripts
- **Data Sources:** `sourcetype=github:webhook`, `sourcetype=argocd:application`
- **SPL:**
```spl
index=devops (sourcetype="github:webhook" OR sourcetype="argocd:application")
| eval commit_ts=if(sourcetype="github:webhook", strptime(commit_time,"%Y-%m-%dT%H:%M:%SZ"), null())
| eval sync_ts=if(sourcetype="argocd:application", _time, null())
| stats earliest(commit_ts) as first_commit, latest(sync_ts) as last_sync by repository, revision
| eval lead_time_sec=last_sync-first_commit
| where isnotnull(lead_time_sec) AND lead_time_sec > 0
| eval lead_time_min=round(lead_time_sec/60,1)
| table repository, revision, lead_time_min
| sort -lead_time_min
```
- **Implementation:** Correlate Git merge or push timestamps with Argo CD successful sync or Flux `LastAppliedRevision` time for the same revision. Use lookup or transaction across indexes if needed. Report p50/p95 lead time by team and service. Exclude hotfix channels with tags if required.
- **Visualization:** Histogram (lead time distribution), Line chart (p95 lead time trend), Bar chart (lead time by service).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 12.6 DevOps Trending

**Primary App/TA:** GitHub Add-on / webhooks, GitLab integrations, Jenkins log/metrics forwarders, Splunk CI/CD content for DORA-style KPIs.

**Data Sources:** `index=devops` with `sourcetype=github:*`, `sourcetype=jenkins:*`, `sourcetype=gitlab:*`. Normalize repository, pipeline, environment, and conclusion fields across tools before building executive DORA panels.

---

### UC-12.6.1 · DORA Metrics Trending Dashboard
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Deployment frequency, lead time, change failure rate, and restore time summarize delivery health; month-over-month trends show whether engineering investments actually improved flow or reliability.
- **App/TA:** GitHub/GitLab/Jenkins integrations, optional Splunk DORA or custom summary searches
- **Data Sources:** `index=devops` `sourcetype IN ("github:workflow_run","gitlab:pipeline","jenkins:build")`; production deploy tags on `environment` or `branch`
- **SPL:**
```spl
index=devops sourcetype="github:workflow_run" earliest=-180d@d (environment="production" OR ref="refs/heads/main")
| eval deploy=if(conclusion="success",1,0)
| timechart span=1mon sum(deploy) as deployment_frequency
```
```spl
index=devops sourcetype="gitlab:pipeline" earliest=-180d@d environment=production status="success"
| eval lead_hr=round(duration_sec/3600,2)
| timechart span=1mon median(lead_hr) as lead_time_hours_median
| trendline sma3(lead_time_hours_median) as lead_trend
```
```spl
index=devops (sourcetype="github:workflow_run" OR sourcetype="jenkins:build") earliest=-180d@d
| eval failed=if(conclusion IN ("failure","cancelled") OR result="FAILURE",1,0)
| eval prod=if(match(lower(coalesce(environment,labels)),"(?i)prod|production"),1,0)
| where prod=1
| timechart span=1mon sum(failed) as failed_deploys count as deploys
| eval change_failure_rate_pct=round(100*failed_deploys/nullif(deploys,0),2)
| trendline sma3(change_failure_rate_pct) as cfr_trend
| eventstats median(change_failure_rate_pct) as cfr_med
```
```spl
index=devops sourcetype="github:issues" earliest=-180d@d (label="incident" OR priority="P1")
| eval created_ts=strptime(created_at,"%Y-%m-%dT%H:%M:%SZ")
| eval closed_ts=strptime(closed_at,"%Y-%m-%dT%H:%M:%SZ")
| eval restore_hr=round((closed_ts-created_ts)/3600,2)
| where restore_hr>=0
| eval _time=closed_ts
| timechart span=1mon median(restore_hr) as mttr_restore_hours
| trendline sma3(mttr_restore_hours) as mttr_trend
```
- **Implementation:** Rarely one query fits all four DORA metrics—implement four saved searches (or a data model) that align on calendar months and team tags. Map GitHub Actions, GitLab pipelines, and Jenkins jobs to “production deploy” using branch/environment rules. For change failure rate, count failed production workflows over successful attempts to prod in the same window. Restore time often comes from incident tooling (`index=itsm`) if not in GitHub issues—join on service name. Validate timestamps are UTC-consistent.
- **Visualization:** Four-panel executive dashboard (line charts per metric), Optional radar chart for normalized month scores, Table (monthly KPI table export).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.6.2 · Security Scan Finding Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Seeing new, open, and closed findings per sprint proves whether shift-left scanning and remediation keep pace with development; spikes in new findings after dependency upgrades are expected—flat open counts are not.
- **App/TA:** GitHub Advanced Security (Dependabot, code scanning), GitLab SAST/DAST, Jenkins security stage plugins
- **Data Sources:** `index=devops` `sourcetype IN ("github:dependabot_alert","github:code_scanning","gitlab:vulnerability","jenkins:security_scan")`
- **SPL:**
```spl
index=devops sourcetype IN ("github:dependabot_alert","gitlab:vulnerability") earliest=-90d@d
| eval is_open=if(lower(coalesce(state,status,"open"))="open",1,0)
| timechart span=7d sum(is_open) as open_findings count as total_alerts
| eval open_pct=round(100*open_findings/nullif(total_alerts,0),1)
| trendline sma2(open_pct) as open_trend
| eventstats avg(open_pct) as baseline_open
```
- **Implementation:** Ingest Dependabot and SARIF or code-scanning webhooks with stable `alert_id`. For GitLab, map `state` transitions over time or snapshot daily open counts via API. Tag by `repository` and `severity`. Exclude informational severities if policy dictates. Review sprints where `open_findings` rises while merges are flat—often a supply-chain or license scan change.
- **Visualization:** Stacked bar (new versus closed per sprint), Line chart (open backlog trend), Treemap (findings by repo).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.6.3 · Build Queue Wait Time Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Queue wait reflects runner capacity and pipeline fan-in; rising waits delay feedback and release trains even when job success rates look fine.
- **App/TA:** Jenkins metrics (`metrics` plugin), GitLab Runner metrics, GitHub Actions (job queue via API-derived events)
- **Data Sources:** `index=devops` `sourcetype="jenkins:queue"` or `sourcetype="jenkins:build"` with `queue_wait_ms`; `sourcetype="gitlab:job"` with `queued_duration`
- **SPL:**
```spl
index=devops (sourcetype="jenkins:build" OR sourcetype="gitlab:job") earliest=-30d@d
| eval wait_sec=coalesce(queue_wait_ms/1000, queued_duration, queue_time_sec)
| where isnotnull(wait_sec)
| timechart span=1d avg(wait_sec) as avg_wait_sec p95(wait_sec) as p95_wait_sec
| eval avg_wait_min=round(avg_wait_sec/60,2)
| trendline sma7(avg_wait_min) as wait_trend
| eventstats median(avg_wait_min) as med_wait
| eval backlog_pressure=if(avg_wait_min > med_wait*1.5,1,0)
```
- **Implementation:** Ensure `wait_sec` excludes container provisioning if that is tracked separately. For GitHub-only shops, ingest workflow_job events with `queued_at` and `started_at` to derive wait. Split by `label` or `runner_group` to see constrained pools. Alert when p95 wait exceeds SLA for two consecutive days.
- **Visualization:** Line chart (average and p95 wait in minutes), Area chart (wait distribution bands), Single value (current p95 wait).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-12.6.4 · Container Image Build Time Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Longer image builds slow every downstream deploy; sprint-level trends catch Dockerfile regressions, bloated layers, or registry latency before they dominate CI budgets.
- **App/TA:** GitLab CI, GitHub Actions, Jenkins Pipelines with Kaniko/buildkit logging
- **Data Sources:** `index=devops` `sourcetype IN ("gitlab:job","github:workflow_job","jenkins:build")` filtered to `image`/`container`/`docker` job or stage names
- **SPL:**
```spl
index=devops sourcetype IN ("gitlab:job","github:workflow_job") earliest=-90d@d
| eval job_lower=lower(coalesce(name,job_name,workflow_name))
| where match(job_lower,"(?i)image|container|docker|build.*push|kaniko|buildkit")
| eval dur_min=round(coalesce(duration_sec,duration)/60,2)
| eval sprint=strftime(_time,"%Y-W%V")
| stats avg(dur_min) as avg_build_min median(dur_min) as med_build_min by sprint, project
| eventstats median(avg_build_min) as fleet_med by sprint
| eval regression=if(avg_build_min > fleet_med*1.35,1,0)
| sort sprint project
```
- **Implementation:** Standardize job naming so filters stay reliable; alternatively maintain a lookup of pipeline IDs that produce images. Strip cache-hit jobs if duration is near-zero noise. Compare medians per repo against its own 8-sprint baseline to reduce cross-team skew. Pair with container registry pull latency dashboards when build times spike only in certain regions.
- **Visualization:** Line chart (average image build minutes by sprint), Bar chart (top regressing projects), Table (sprint, project, avg, median).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

