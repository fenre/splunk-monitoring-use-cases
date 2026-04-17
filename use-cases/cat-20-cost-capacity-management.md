## 20. Cost & Capacity Management

### 20.1 Cloud Cost Monitoring

**Primary App/TA:** Cloud provider TAs, CUR/billing export ingestion

### UC-20.1.1 · Daily Spend Trending

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Cloud costs can spiral without visibility. Daily spend trending by service, account, and tag provides the financial governance foundation — enabling teams to understand where money goes, spot trends early, and make informed optimization decisions.
- **App/TA:** `Splunk Add-on for AWS` (CUR ingestion), `Splunk Add-on for Microsoft Cloud Services`, `Splunk Add-on for Google Cloud Platform`
- **Data Sources:** AWS Cost and Usage Report (CUR), Azure Cost Management export, GCP Billing export
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| timechart span=1d sum(cost) as daily_spend by lineItem_ProductCode
| addtotals
| rename Total as total_daily_spend
```
- **Implementation:** Ingest AWS CUR, Azure Cost export, or GCP billing data daily. Parse cost line items by service, account, region, and tags. Build daily/weekly/monthly spend reports. Set trending alerts when daily spend exceeds 7-day rolling average by >20%. Enable tag-based cost allocation from day one.
- **Visualization:** Timechart (daily spend trending), Stacked bar chart (spend by service), Table (top 10 services by cost), Single value (today's spend vs yesterday).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876), [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110), [Splunk Add-on for Google Cloud Platform](https://splunkbase.splunk.com/app/3088)
### UC-20.1.2 · Cost Anomaly Detection

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Unexpected cost spikes from runaway instances, misconfigured autoscaling, or crypto-mining attacks can generate thousands in charges within hours. Automated anomaly detection catches these events before they become budget disasters.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** Billing data with historical trending
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| timechart span=1d sum(cost) as daily_spend by lineItem_UsageAccountId
| foreach * [eval <<FIELD>>=if(<<FIELD>>="", 0, <<FIELD>>)]
| addtotals
| predict Total as predicted_spend algorithm=LLP5 future_timespan=1
| eval anomaly=if(Total > 'upper95(predicted_spend)', "Anomaly", "Normal")
| where anomaly="Anomaly"
```
- **Implementation:** Build 30-day baseline of daily spending per account and service. Use Splunk `predict` command with LLP5 algorithm for anomaly detection. Alert when actual spend exceeds upper 95% confidence interval. Investigate anomalies by drilling into specific services and resources. Integrate with incident management for cost-related incidents.
- **Visualization:** Timechart (actual vs predicted spend), Table (anomaly details), Single value (current anomaly count), Alert indicator (anomaly detected).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.3 · Reserved Instance Utilization

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Reserved Instances and Savings Plans represent upfront commitments. Monitoring utilization ensures you're getting value from these purchases. Low utilization means wasted money; gaps in coverage mean missed savings opportunities.
- **App/TA:** `Splunk Add-on for AWS`, billing TAs
- **Data Sources:** AWS CUR (reservation fields), Azure reservation utilization
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| search reservation_ReservationARN!=""
| stats sum(reservation_UnusedAmortizedUpfrontFeeForBillingPeriod) as unused_upfront, sum(reservation_EffectiveCost) as effective_cost, sum(reservation_UnusedRecurringFee) as unused_recurring by reservation_ReservationARN, lineItem_ProductCode
| eval utilization_pct=round((1-(unused_upfront+unused_recurring)/effective_cost)*100, 1)
| sort utilization_pct
| table reservation_ReservationARN, lineItem_ProductCode, effective_cost, unused_upfront, unused_recurring, utilization_pct
```
- **Implementation:** Parse RI/Savings Plan utilization from CUR data. Track utilization percentage per reservation. Alert when any RI falls below 80% utilization for 7+ consecutive days. Report on coverage gaps where on-demand spend could be covered by reservations. Review expiring reservations 30 days before expiry.
- **Visualization:** Gauge (overall RI utilization), Bar chart (utilization by reservation), Table (underutilized RIs), Timechart (utilization trending).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.4 · Idle Resource Identification

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Idle resources (running but unused instances, unattached volumes, unused load balancers) are pure waste. Identifying and eliminating them is the quickest path to cloud cost savings, often yielding 20-30% reduction.
- **App/TA:** `Splunk Add-on for AWS`, cloud monitoring TAs
- **Data Sources:** CloudWatch/Azure Monitor metrics + billing data
- **SPL:**
```spl
index=cloud_metrics sourcetype="aws:cloudwatch"
| search metric_name="CPUUtilization"
| stats avg(Average) as avg_cpu, max(Maximum) as peak_cpu by dimensions.InstanceId
| where avg_cpu < 5 AND peak_cpu < 10
| lookup aws_instance_details InstanceId as dimensions.InstanceId OUTPUT instance_type, monthly_cost, tags
| eval waste_monthly=monthly_cost
| sort -waste_monthly
| table dimensions.InstanceId, instance_type, avg_cpu, peak_cpu, monthly_cost, tags
```
- **Implementation:** Correlate CloudWatch CPU/network metrics with billing data. Define idle thresholds: CPU avg <5%, network <1MB/day for 7+ days. Include unattached EBS volumes, idle ELBs, unused Elastic IPs. Generate weekly idle resource reports with estimated savings. Route to resource owners for action.
- **Visualization:** Table (idle resources with cost), Bar chart (waste by service), Single value (total monthly waste), Pie chart (waste by team/tag).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.5 · Budget Threshold Alerting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Budget alerts prevent overspend by notifying stakeholders at defined thresholds (50%, 75%, 90%, 100%). Combined with forecast-based alerts, teams can take corrective action before exceeding approved budgets.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** Billing data, budget definitions (lookup)
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| stats sum(cost) as mtd_spend by lineItem_UsageAccountId
| lookup cloud_budgets account_id as lineItem_UsageAccountId OUTPUT budget_amount, owner_email
| eval budget_pct=round((mtd_spend/budget_amount)*100, 1)
| eval status=case(budget_pct>=100, "Exceeded", budget_pct>=90, "Critical", budget_pct>=75, "Warning", budget_pct>=50, "On Track", 1==1, "Under Budget")
| sort -budget_pct
| table lineItem_UsageAccountId, owner_email, budget_amount, mtd_spend, budget_pct, status
```
- **Implementation:** Define budgets per account/team in a Splunk lookup table. Calculate MTD spend against budgets daily. Alert at 50%, 75%, 90%, and 100% thresholds. Include forecast-based alerts (projected to exceed budget). Escalate to management when budgets are exceeded.
- **Visualization:** Gauge (budget consumption), Table (budget status by account), Timechart (MTD spend vs budget line), Single value (accounts over budget).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.6 · Cost Allocation by Team

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Breaking down cloud costs by team/department via tagging creates accountability and enables chargeback/showback. Teams that see their own costs make better optimization decisions, driving organization-wide cost efficiency.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** CUR with tag data, organizational mapping
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| eval team=coalesce('resourceTags_user_Team', 'resourceTags_user_team', "Untagged")
| stats sum(cost) as total_cost by team
| eventstats sum(total_cost) as grand_total
| eval cost_pct=round((total_cost/grand_total)*100, 1)
| sort -total_cost
| table team, total_cost, cost_pct
```
- **Implementation:** Enforce tagging policy requiring Team/Department/Environment tags. Parse resource tags from billing data. Calculate cost allocation by team, department, and environment. Report on untagged resources (assign to "Unknown" for follow-up). Generate monthly chargeback reports.
- **Visualization:** Pie chart (cost by team), Bar chart (team costs with trending), Table (detailed allocation), Single value (untagged cost percentage).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.7 · Spot/Preemptible Instance Tracking

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Spot instances offer significant savings (60-90%) but can be interrupted. Tracking interruptions, savings achieved, and workload placement ensures teams maximize savings while maintaining application resilience.
- **App/TA:** `Splunk Add-on for AWS`, EC2 event logs
- **Data Sources:** EC2 spot instance events, billing data
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail"
| search eventName="BidEvictedEvent" OR eventName="SpotInstanceInterruption"
| stats count as interruptions by requestParameters.instanceId, requestParameters.instanceType, userIdentity.arn
| lookup spot_savings instance_id as requestParameters.instanceId OUTPUT on_demand_cost, spot_cost
| eval savings=on_demand_cost-spot_cost
| eval savings_pct=round((savings/on_demand_cost)*100, 1)
| table requestParameters.instanceId, requestParameters.instanceType, interruptions, on_demand_cost, spot_cost, savings_pct
```
- **Implementation:** Track spot instance lifecycle events via CloudTrail. Monitor interruption frequency by instance type and AZ. Calculate savings vs on-demand pricing. Alert on interruption rate spikes affecting critical workloads. Report monthly spot savings to justify continued spot adoption.
- **Visualization:** Bar chart (interruptions by type), Timechart (interruption frequency), Single value (monthly spot savings), Table (instance interruption details).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.8 · Data Transfer Cost Analysis

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Data transfer costs are often the most surprising cloud bill item. Inter-region, cross-AZ, and internet egress charges add up quickly. Identifying the biggest transfer flows enables architectural optimization to reduce costs significantly.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** CUR data transfer line items, VPC flow logs
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| search lineItem_UsageType="*DataTransfer*" OR lineItem_UsageType="*Bytes*"
| eval cost=tonumber(lineItem_UnblendedCost)
| eval transfer_type=case(
    lineItem_UsageType LIKE "%InterRegion%", "Inter-Region",
    lineItem_UsageType LIKE "%Out-Bytes%", "Internet Egress",
    lineItem_UsageType LIKE "%In-Bytes%", "Internet Ingress",
    lineItem_UsageType LIKE "%Regional%", "Cross-AZ",
    1==1, "Other")
| stats sum(cost) as transfer_cost, sum(lineItem_UsageAmount) as gb_transferred by transfer_type, lineItem_ProductCode
| sort -transfer_cost
```
- **Implementation:** Parse data transfer line items from CUR. Categorize by transfer type (egress, inter-region, cross-AZ). Identify top services and resources by transfer cost. Correlate with VPC flow logs for detailed flow analysis. Recommend architecture changes (CDN, VPC endpoints, same-AZ placement) for top cost drivers.
- **Visualization:** Pie chart (cost by transfer type), Bar chart (top services by transfer cost), Timechart (transfer cost trending), Table (detailed transfer breakdown).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.9 · Predictive Disk / Volume Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Time-to-full forecast using linear regression on disk usage data enables proactive capacity planning. Running out of disk space causes application outages, failed backups, and data loss. Predicting exhaustion dates allows teams to provision storage or archive data before hitting critical thresholds.
- **App/TA:** `Splunk_TA_nix`, `Splunk_TA_windows`, SNMP-based storage inputs
- **Data Sources:** df/disk usage data (any sourcetype with UsePct and filesystem), Windows Perfmon logical disk, SNMP storage MIBs
- **SPL:**
```spl
index=infrastructure (sourcetype="df" OR sourcetype="disk" OR sourcetype="Perfmon:LogicalDisk")
| eval UsePct=coalesce(UsePct, pctUsed, 'Percent_Used')
| eval filesystem=coalesce(filesystem, mount, instance)
| where isnotnull(UsePct) AND isnotnull(filesystem)
| bin _time span=1d
| stats latest(UsePct) as used_pct by filesystem, host, _time
| timechart span=1d latest(used_pct) as used_pct by filesystem, host
| predict used_pct as predicted_pct algorithm=LLP5 future_timespan=90
| eval risk_30d=if('predicted_pct+30d'>85, "At Risk", "OK")
| eval risk_90d=if('predicted_pct+90d'>95, "Critical", "OK")
| where risk_30d="At Risk" OR risk_90d="Critical"
| table _time, filesystem, host, used_pct, 'predicted_pct+30d', 'predicted_pct+90d', risk_30d, risk_90d
```
- **Implementation:** Collect disk usage metrics daily from all hosts (df, Perfmon, SNMP). Ensure UsePct and filesystem/mount are extracted. Use Splunk `predict` with LLP5 for 30/60/90-day forecasting. Alert when projected usage exceeds 85% within 30 days or 95% within 90 days. Exclude ephemeral or tmpfs mounts from alerts. Build a dashboard with forecast overlay and drilldown to host/filesystem.
- **Visualization:** Timechart (usage with forecast overlay), Table (volumes approaching exhaustion with risk status), Gauge (current utilization), Single value (volumes at risk).
- **CIM Models:** N/A

- **References:** [Splunk_TA_nix](https://splunkbase.splunk.com/app/833), [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
### UC-20.1.10 · Reserved Instance Coverage Gaps

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Highlights on-demand spend in families/regions that could be covered by additional RIs/Savings Plans — complements utilization of existing commitments (UC-20.1.3).
- **App/TA:** `Splunk Add-on for AWS`, billing TAs
- **Data Sources:** CUR with `lineItem_LineItemType`, usage type, instance family
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur" earliest=-30d
| eval cost=tonumber(lineItem_UnblendedCost)
| eval on_demand=if(isnull(reservation_ReservationARN) AND match(lineItem_UsageType,"BoxUsage"),cost,0)
| stats sum(on_demand) as od_spend by lineItem_ProductCode, lineItem_UsageType, lineItem_AvailabilityZone
| sort -od_spend
| head 30
```
- **Implementation:** Top on-demand spend by family/AZ drives RI buying decisions. Join with coverage reports from Cost Explorer export if available.
- **Visualization:** Table (coverage gap candidates), Bar chart (on-demand by family), Single value (total addressable OD spend).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.11 · Spot Instance Interruption Rate

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Cost, Performance
- **Value:** Interruptions per 1,000 instance-hours by pool and AZ — extends raw event counts (UC-20.1.7) with a **rate** for SLO tracking.
- **App/TA:** `Splunk Add-on for AWS`, CloudTrail
- **Data Sources:** `aws:cloudtrail` Spot events, instance-hours from CUR
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" earliest=-30d
| search eventName="SpotInstanceInterruption"
| stats count as intr
| append [ search index=cloud_billing sourcetype="aws:billing:cur" earliest=-30d
  | search lineItem_UsageType="*SpotUsage*"
  | stats sum(lineItem_NormalizedUsageAmount) as instance_hours ]
| stats sum(intr) as interruptions sum(instance_hours) as ih
| eval intr_per_1k=round(1000*interruptions/nullif(ih,0),2)
```
- **Implementation:** Align instance-hour denominator from CUR `NormalizedUsageAmount`. Alert when `intr_per_1k` exceeds baseline for stateful tiers.
- **Visualization:** Single value (interruptions per 1k hours), Line chart (rate trend), Table (by AZ).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
### UC-20.1.12 · FinOps Budget Alert Correlation

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Joins AWS Budgets / Azure budget notifications with resource change events and anomaly searches to explain **why** a threshold fired.
- **App/TA:** Cloud billing TAs, CloudTrail
- **Data Sources:** Budget alert SNS/email logs, `cost:daily`, CloudTrail
- **SPL:**
```spl
index=finops sourcetype="aws:budget:alert" earliest=-7d
| eval budget_name=coalesce(budget_name,BudgetName)
| join type=left max=1 budget_name [ search index=cloud_cost sourcetype="cost:daily" earliest=-7d | stats sum(cost) as daily_cost by account_id, _time span=1d ]
| table _time, budget_name, threshold_type, daily_cost
```
- **Implementation:** Ingest budget notifications via HEC or Lambda. Drill down to service cost change same day. Link to change tickets.
- **Visualization:** Timeline (budget alerts overlaid with spend), Table (alert + cost delta), Sankey (alert → service).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.1.13 · Cost Anomaly by Cloud Service

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** z-score or median-absolute-deviation of **daily cost per `lineItem_ProductCode`** — tighter scope than account-level UC-20.1.2.
- **App/TA:** Billing export TAs
- **Data Sources:** CUR, Azure cost export
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur" earliest=-60d
| eval cost=tonumber(lineItem_UnblendedCost)
| timechart span=1d sum(cost) as daily by lineItem_ProductCode
| untable _time lineItem_ProductCode daily
| eventstats median(daily) as med, stdev(daily) as sd by lineItem_ProductCode
| eval z=if(sd>0, (daily-med)/sd, 0)
| where abs(z)>3
| table _time, lineItem_ProductCode, daily, med, z
```
- **Implementation:** Requires 60d history. Exclude credits via `lineItem_LineItemType`. Page on |z|>3 for top services.
- **Visualization:** Table (service anomalies), Line chart (daily vs median), Single value (open anomalies).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.1.14 · Savings Plan Utilization and Hourly Burn

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Savings Plan utilization % and unused commitment hours — operational view for FinOps reviews (related to UC-20.2.9).
- **App/TA:** AWS Cost Explorer export, `aws:savings_plan` sourcetype
- **Data Sources:** Savings Plans utilization report
- **SPL:**
```spl
index=cloud_cost sourcetype="aws:savings_plan" earliest=-7d
| stats latest(utilization_pct) as util, latest(unused_commitment_hrs) as unused by savings_plan_arn
| where util < 90 OR unused>100
| table savings_plan_arn, util, unused
```
- **Implementation:** Schedule daily SP utilization CSV from S3. Alert when utilization <90% for 3+ days. Recommend exchange/modify.
- **Visualization:** Gauge (SP utilization), Table (underutilized plans), Line chart (util trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.1.15 · Data Transfer Cost Attribution by Tag

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Allocates data transfer line items to `resourceTags_user_*` for chargeback — extends aggregate transfer analysis (UC-20.1.8).
- **App/TA:** CUR with resource tags
- **Data Sources:** `aws:billing:cur`
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| search lineItem_ProductCode="AmazonEC2" (lineItem_UsageType="*DataTransfer*" OR lineItem_UsageType="*Bytes*")
| eval cost=tonumber(lineItem_UnblendedCost)
| eval app=coalesce(resourceTags_user_Application,"untagged")
| stats sum(cost) as xfer_cost by app, lineItem_UsageType
| sort -xfer_cost
```
- **Implementation:** Requires tags on resources generating egress; untagged flows appear as `untagged`. Reconcile with VPC Flow to owners.
- **Visualization:** Stacked bar (transfer $ by app), Table (top untagged), Pie chart (egress by tag).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.1.16 · Container Workload Right-Sizing Cost

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Correlates EKS/AKS/GKE namespace CPU/memory requests vs actuals with allocated node cost for rightsizing recommendations.
- **App/TA:** Kubernetes metrics, cloud billing
- **Data Sources:** Prometheus metrics, CUR container cost allocation (Kubecost-style)
- **SPL:**
```spl
index=kubernetes sourcetype="kube:metrics" earliest=-7d
| stats avg(container_cpu_usage_cores) as use, avg(container_cpu_request_cores) as req by namespace, cluster
| eval oversize=if(req>use*2,1,0)
| where oversize=1
| lookup kube_namespace_monthly_cost namespace cluster OUTPUT monthly_cost
| table namespace, cluster, use, req, monthly_cost
```
- **Implementation:** Ingest kube-state-metrics or vendor. Join cost from Kubecost export or tag-based CUR. Drive requests/limits changes.
- **Visualization:** Table (oversized namespaces), Bar chart (waste $), Scatter (request vs use).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.1.17 · Serverless Invocation Cost Trending

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Cost
- **Value:** Daily Lambda/Azure Functions/Google Cloud Functions cost and invocation count — detects runaway retries and bad deploys.
- **App/TA:** Cloud billing with serverless product codes
- **Data Sources:** CUR, Azure meter export
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur" earliest=-30d
| search lineItem_ProductCode IN ("AWSLambda","AmazonSNS") OR lineItem_UsageType="*Lambda*"
| eval cost=tonumber(lineItem_UnblendedCost)
| timechart span=1d sum(cost) as serverless_cost sum(lineItem_UsageAmount) as units
```
- **Implementation:** Map usage types to invocations vs GB-sec. Alert when daily cost > 2× 7d average.
- **Visualization:** Line chart (serverless $ and invocations), Table (top functions from resource tags), Single value (day-over-day %).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.1.18 · Orphaned Cloud Resource Detection

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Unattached volumes, unused elastic IPs, old snapshots without volume — **inventory-driven** waste beyond idle CPU (UC-20.1.4).
- **App/TA:** AWS Config snapshot, resource inventory
- **Data Sources:** `aws:config:inventory`, cost
- **SPL:**
```spl
index=cloud_inventory sourcetype="aws:config:inventory" earliest=-1d
| where status="available" AND resource_type="AWS::EC2::Volume" AND attachments=0
| lookup monthly_storage_rate region OUTPUT rate_gb_mo
| eval waste=size_gb*rate_gb_mo
| stats sum(waste) as monthly_waste by account_id, region
| sort -monthly_waste
```
- **Implementation:** Refresh Config aggregator daily. Include unattached EIP and old snapshots in companion searches. Route to owners via account tags.
- **Visualization:** Table (orphan waste $), Bar chart (by account), Single value (total orphan monthly $).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.1.19 · Cost Allocation Tag Compliance

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Percentage of monthly spend that is **untagged** or missing required keys (`Application`, `CostCenter`, `Environment`).
- **App/TA:** CUR
- **Data Sources:** `aws:billing:cur`
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur" earliest=-30d
| eval cost=tonumber(lineItem_UnblendedCost)
| eval has_app=isnotnull(resourceTags_user_Application) AND resourceTags_user_Application!=""
| eval has_cc=isnotnull(resourceTags_user_CostCenter) AND resourceTags_user_CostCenter!=""
| stats sum(eval(if(has_app AND has_cc,cost,0))) as tagged_cost sum(cost) as total_cost
| eval tag_compliance_pct=round(100*tagged_cost/total_cost,1)
```
- **Implementation:** Expand required keys per policy. Break down by OU/account. Drive tagging enforcement at CI/CD.
- **Visualization:** Single value (tag compliance %), Pie chart (tagged vs untagged $), Table (worst accounts).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.1.20 · Idle Resource Identification by Account

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Cost
- **Value:** Rolls up idle candidates (UC-20.1.4) to **account and owner** for FinOps accountability — same theme, executive view.
- **App/TA:** Cloud metrics, CUR, CMDB
- **Data Sources:** Idle detection output, `lineItem_UsageAccountId`
- **SPL:**
```spl
index=summary sourcetype="cloud:idle_candidates" earliest=-1d
| stats sum(estimated_monthly_savings) as idle_dollars by lineItem_UsageAccountId
| lookup aws_account_owner account_id AS lineItem_UsageAccountId OUTPUT owner_email
| sort -idle_dollars
| head 25
```
- **Implementation:** Populate `cloud:idle_candidates` from scheduled UC-20.1.4 logic. Monthly email to top account owners.
- **Visualization:** Bar chart (idle $ by account), Table (owner, idle $), Single value (fleet idle $).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.1.21 · Azure Cost Management Daily Spend by Meter Category

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Performance
- **Value:** Azure invoices spread spend across many meters (compute, storage, networking, PaaS). Rolling up daily cost by `MeterCategory` and subscription exposes the biggest budget drivers early so teams can tune SKUs, retire sandboxes, and negotiate reservations before month-end true-up.
- **App/TA:** `Splunk Add-on for Microsoft Cloud Services`, Azure Cost Management export (Blob/HEC)
- **Data Sources:** `index=cloud_billing` `sourcetype="azure:billing:usage"`
- **SPL:**
```spl
index=cloud_billing sourcetype="azure:billing:usage" earliest=-30d
| eval cost=tonumber(coalesce(CostUSD, cost, pretax_cost))
| eval sub=coalesce(SubscriptionId, subscription_id)
| eval cat=coalesce(MeterCategory, meter_category, "Unknown")
| bin _time span=1d
| stats sum(cost) as daily_spend by _time, sub, cat
| timechart span=1d sum(daily_spend) as spend by cat
```
- **Implementation:** (1) Export Cost Management actual + amortized cost daily to Splunk (Blob pull or Event Hub). (2) Normalize currency fields and subscription identifiers. (3) Alert when any `MeterCategory` exceeds its 14-day median by 40% for two consecutive days.
- **Visualization:** Stacked area chart (spend by meter category), Table (top categories by subscription), Single value (MTD vs prior MTD %).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)

---

### UC-20.1.22 · GCP Billing Export Cost by Project and Service

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Capacity
- **Value:** Google Cloud bills aggregate credits, sustained-use discounts, and cross-project shared VPC egress. Tracking `project.id` and `service.description` daily highlights runaway BigQuery scan jobs, idle Composer environments, and forgotten projects that quietly consume committed spend.
- **App/TA:** `Splunk Add-on for Google Cloud Platform`, BigQuery billing export (JSONL to GCS → HEC)
- **Data Sources:** `index=cloud_billing` `sourcetype="gcp:billing:export"`
- **SPL:**
```spl
index=cloud_billing sourcetype="gcp:billing:export" earliest=-30d
| eval cost=tonumber(coalesce(cost, cost_amount, usage.amount))
| eval project=coalesce('project.id', project_id)
| eval svc=coalesce('service.description', service_description, sku.description)
| bin _time span=1d
| stats sum(cost) as daily_cost by _time, project, svc
| stats sum(eval(if(_time>=relative_time(now(),"-7d@d"),daily_cost,0))) as last7d
         sum(eval(if(_time<relative_time(now(),"-7d@d") AND _time>=relative_time(now(),"-14d@d"),daily_cost,0))) as prev7d by project, svc
| eval wow_pct=round(100*(last7d-prev7d)/nullif(prev7d,0),1)
| where wow_pct>25 OR last7d>5000
| sort -last7d
```
- **Implementation:** (1) Enable detailed billing export with project hierarchy labels. (2) Ingest with stable `project`/`service` field aliases. (3) Route week-over-week spikes to FinOps with drilldown links to BigQuery job IDs when present.
- **Visualization:** Treemap (cost by project), Bar chart (top services), Table (WoW % and 7-day spend).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Google Cloud Platform](https://splunkbase.splunk.com/app/3088)

---

### UC-20.1.23 · Reserved Instance Purchase Amortization vs On-Demand Leakage

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Cost, Performance
- **Value:** Amortized RI fees should displace on-demand box usage in the same instance family. When amortized reservation cost rises but matching usage stays on-demand, coverage or scope mismatches waste committed dollars. This view quantifies leakage for purchasing corrections.
- **App/TA:** `Splunk Add-on for AWS` (CUR)
- **Data Sources:** `index=cloud_billing` `sourcetype="aws:billing:cur"`
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur" earliest=-30d
| eval cost=tonumber(lineItem_UnblendedCost)
| eval ri_fee=if(lineItem_LineItemType IN ("DiscountedUsage","RIFee"), cost, 0)
| eval od_compute=if(match(lineItem_UsageType,"BoxUsage") AND isnull(reservation_ReservationARN), cost, 0)
| eval family=replace(lineItem_UsageType,"BoxUsage:","")
| stats sum(ri_fee) as ri_spend sum(od_compute) as od_leak by lineItem_UsageAccountId, family
| eval leak_ratio=round(od_leak/nullif(ri_spend+od_leak,0)*100,1)
| where od_leak>100 AND leak_ratio>15
| sort -od_leak
```
- **Implementation:** (1) Confirm CUR includes amortized cost columns for your payer account. (2) Map `lineItem_UsageType` to instance family for EC2. (3) Review accounts with high `leak_ratio` against AWS Cost Explorer coverage reports.
- **Visualization:** Table (accounts and families with leakage), Bar chart (on-demand leak $), Heatmap (account × family).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-20.1.24 · Savings Plan Coverage of Eligible Compute Spend

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Capacity
- **Value:** Savings Plans discount compute only when usage is eligible and within the commitment’s scope. Low coverage means you are still paying list price for large portions of EC2, Fargate, or Lambda despite owning a plan—direct savings opportunity on the next purchase or exchange.
- **App/TA:** `Splunk Add-on for AWS`, CUR with `savingsPlan_*` fields
- **Data Sources:** `index=cloud_billing` `sourcetype="aws:billing:cur"`
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur" earliest=-30d
| eval cost=tonumber(lineItem_UnblendedCost)
| eval sp_covered=if(isnotnull(savingsPlan_SavingsPlanARN) AND savingsPlan_SavingsPlanARN!="", cost, 0)
| eval eligible=if(lineItem_ProductCode IN ("AmazonEC2","AmazonECS","AWSLambda") AND match(lineItem_UsageType,"(BoxUsage|SpotUsage|Fargate)"), cost, 0)
| stats sum(sp_covered) as sp_sum sum(eligible) as elig_sum by lineItem_UsageAccountId
| eval coverage_pct=round(100*sp_sum/nullif(elig_sum,0),1)
| where coverage_pct<60 AND elig_sum>500
| sort elig_sum
```
- **Implementation:** (1) Ensure CUR includes Savings Plan ARN fields. (2) Tune the `eligible` filter to your contract (exclude Marketplace line items). (3) Target accounts below 60% coverage for rightsizing plus incremental SP buys.
- **Visualization:** Gauge (fleet-wide coverage), Table (accounts under target), Bar chart (eligible on-demand still uncovered).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-20.1.25 · NAT Gateway and VPC Endpoint Egress Cost Concentration

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Performance
- **Value:** Managed NAT and interface endpoints bill per GB processed; a single chatty microservice behind NAT can dominate networking spend. Ranking usage types tied to NAT Gateway and PrivateLink highlights candidates for VPC endpoint redesign, caching, or regional consolidation.
- **App/TA:** `Splunk Add-on for AWS`, VPC Flow Logs (optional correlation)
- **Data Sources:** `index=cloud_billing` `sourcetype="aws:billing:cur"`
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur" earliest=-30d
| eval cost=tonumber(lineItem_UnblendedCost)
| search lineItem_ProductCode="AmazonEC2" (lineItem_UsageType="NatGateway*" OR lineItem_UsageType="VpcEndpoint*")
| eval resource=coalesce(lineItem_ResourceId, resourceId)
| stats sum(cost) as nat_vpc_cost sum(lineItem_UsageAmount) as usage_qty by lineItem_UsageAccountId, lineItem_UsageType, resource
| sort -nat_vpc_cost
| head 50
```
- **Implementation:** (1) Tag NAT gateways and endpoints with owning application. (2) Join top resources to flow log aggregates if available. (3) Prioritize architecture reviews for the top 10 resources by trailing 30-day cost.
- **Visualization:** Table (top NAT/VPC-endpoint resources), Bar chart (cost by usage type), Pie chart (share by account).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-20.1.26 · Spot Fleet Savings vs Interrupted Instance-Hours

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Performance
- **Value:** Spot savings only matter if interruptions stay within SLOs. Correlating amortized spot spend with interruption counts from CloudTrail yields a simple dollars-saved-per-interruption metric so teams balance price and reliability across pools.
- **App/TA:** `Splunk Add-on for AWS` (CUR + CloudTrail)
- **Data Sources:** `index=cloud_billing` `sourcetype="aws:billing:cur"`, `index=aws` `sourcetype="aws:cloudtrail"`
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur" earliest=-30d
| eval cost=tonumber(lineItem_UnblendedCost)
| search lineItem_UsageType="*SpotUsage*"
| stats sum(cost) as spot_spend by lineItem_UsageAccountId
| join type=left lineItem_UsageAccountId [
  search index=aws sourcetype="aws:cloudtrail" earliest=-30d eventName="SpotInstanceInterruption"
  | eval acct=coalesce(recipientAccountId, accountId)
  | stats count as interruptions by acct
  | rename acct as lineItem_UsageAccountId
]
| fillnull value=0 interruptions
| eval savings_per_intr=if(interruptions>0, round(spend/interruptions,2), null())
| sort -spot_spend
```
- **Implementation:** (1) Normalize account IDs across billing and CloudTrail. (2) Schedule weekly review for accounts with high interruption counts and rising spot spend. (3) Pair with capacity-optimized vs price-optimized fleet settings from ASG/Launch Template metadata if ingested.
- **Visualization:** Scatter plot (spot spend vs interruptions), Table (accounts with worst ratio), Single value (fleet spot savings MTD).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-20.1.27 · Cross-Cloud Consolidated FinOps Executive Rollup

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Cost, Capacity
- **Value:** Enterprises rarely have a single pane for AWS, Azure, and GCP together. Normalizing daily spend into `cloud_provider`, `business_unit`, and `currency` enables portfolio-level trending and board-ready variance explanations without manual spreadsheet merges.
- **App/TA:** Multi-cloud billing TAs, optional `lookup fx_rates`
- **Data Sources:** `index=finops` `sourcetype="cost:unified_daily"`
- **SPL:**
```spl
index=finops sourcetype="cost:unified_daily" earliest=-90d
| eval spend_local=tonumber(daily_cost)
| lookup fx_rates currency as billing_currency OUTPUT usd_per_unit
| eval spend_usd=round(spend_local*usd_per_unit,2)
| bin _time span=1mon
| stats sum(spend_usd) as month_spend by _time, cloud_provider, business_unit
| eventstats sum(month_spend) as portfolio_total by _time
| eval pct_of_portfolio=round(100*month_spend/nullif(portfolio_total,0),1)
| sort _time, -month_spend
```
- **Implementation:** (1) Build a daily scheduled search that writes `cost:unified_daily` from each cloud’s normalized sourcetype. (2) Maintain FX rates for non-USD billers. (3) Publish an executive dashboard with MoM variance annotations from budget lookup.
- **Visualization:** Column chart (monthly spend by cloud), Stacked bar (business unit mix), Table (MoM % change).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 20.2 Capacity Planning

**Primary App/TA:** Cross-referencing infrastructure metrics with trending/forecasting

### UC-20.2.1 · Compute Capacity Forecasting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Running out of compute capacity causes provisioning failures and performance degradation. Forecasting when CPU and memory will be exhausted enables proactive procurement or scaling, avoiding emergency purchases at premium cost.
- **App/TA:** Infrastructure monitoring TAs (various), Splunk `predict` command
- **Data Sources:** Host performance metrics (CPU, memory utilization)
- **SPL:**
```spl
index=infrastructure sourcetype="Perfmon:Processor" OR sourcetype="cpu"
| timechart span=1d avg(cpu_load_percent) as avg_cpu by host
| predict avg_cpu as predicted_cpu algorithm=LLP5 future_timespan=30
| eval days_to_threshold=if('upper95(predicted_cpu)'>90, "Within 30 days", "OK")
```
- **Implementation:** Collect CPU and memory metrics from all hosts. Aggregate to daily averages for trending. Use Splunk `predict` with LLP5 for 30/60/90-day forecasting. Set alerts when forecast predicts >90% utilization within 30 days. Report quarterly on capacity headroom across infrastructure tiers.
- **Visualization:** Timechart (utilization with forecast overlay), Table (hosts approaching capacity), Gauge (current vs capacity), Single value (days to threshold).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.2 · Storage Growth Forecasting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Storage procurement has lead times. Forecasting growth trends enables timely ordering of additional capacity, preventing the emergency of running out of storage space that causes application outages and data loss.
- **App/TA:** Storage TAs (various), Splunk `predict` command
- **Data Sources:** Storage capacity metrics from SAN/NAS/HCI/cloud
- **SPL:**
```spl
index=storage sourcetype="storage:capacity"
| timechart span=1d latest(used_pct) as used_pct by storage_system
| predict used_pct as predicted_pct algorithm=LLP5 future_timespan=90
| eval forecast_90d='predicted_pct+90d'
| where forecast_90d > 85
```
- **Implementation:** Collect storage capacity metrics daily from all storage platforms. Build growth rate trends per volume/pool. Use Splunk predict for 90-day forecasting. Alert when projected usage exceeds 85% within 90 days. Initiate procurement workflow based on projected needs.
- **Visualization:** Timechart (usage with forecast), Table (systems approaching capacity), Gauge (current utilization), Single value (days to threshold).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.3 · Network Bandwidth Trending

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Network bandwidth constraints cause application latency and packet loss. Trending WAN/LAN utilization enables planned upgrades during maintenance windows rather than emergency bandwidth additions during business-impacting congestion.
- **App/TA:** Network monitoring TAs, SNMP
- **Data Sources:** Interface utilization metrics (SNMP, streaming telemetry)
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| eval util_pct=round((ifHCInOctets_rate*8/ifHighSpeed/1000000)*100, 2)
| timechart span=1h avg(util_pct) as avg_util, max(util_pct) as peak_util by interface_name
| predict avg_util as predicted_util algorithm=LLP5 future_timespan=30
```
- **Implementation:** Collect interface utilization via SNMP every 5 minutes. Aggregate to hourly peaks and daily averages. Trend key WAN links and data center interconnects. Alert when trending projects >80% utilization within 30 days. Plan circuit upgrades based on business growth forecasts.
- **Visualization:** Timechart (bandwidth trending with forecast), Table (high-utilization links), Gauge (current peak utilization), Bar chart (top links by utilization).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.4 · License Utilization Tracking

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Software licenses represent significant IT spend. Tracking usage vs entitlements identifies under-licensed risks (compliance violations) and over-licensed waste (unnecessary spend). Right-sizing licenses can save 15-30% of software costs.
- **App/TA:** Custom scripted inputs, vendor license APIs
- **Data Sources:** License server logs, vendor API data, entitlement records
- **SPL:**
```spl
index=licenses sourcetype="license:usage"
| stats latest(used_licenses) as used, latest(total_licenses) as total by product, vendor, license_type
| eval utilization_pct=round((used/total)*100, 1)
| eval status=case(utilization_pct>=95, "At Risk", utilization_pct>=80, "High Use", utilization_pct<50, "Underutilized", 1==1, "Healthy")
| sort -utilization_pct
| table product, vendor, license_type, used, total, utilization_pct, status
```
- **Implementation:** Collect license usage data from license servers (FlexLM, RLM) and vendor APIs. Maintain entitlement records in a lookup table. Track daily peak concurrent usage. Alert at 90% consumption (buy more) and flag <50% utilization (optimize). Generate quarterly true-up reports.
- **Visualization:** Gauge (license utilization), Table (license inventory with status), Bar chart (utilization by product), Timechart (usage trending).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.5 · Right-Sizing Recommendations

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Over-provisioned VMs and instances waste compute and money. Right-sizing analysis compares actual resource usage against allocated resources, identifying instances that can be downsized without impacting performance — typically saving 20-40%.
- **App/TA:** Cloud and virtualization TAs, performance metrics
- **Data Sources:** Performance metrics vs resource allocation data
- **SPL:**
```spl
index=infrastructure (sourcetype="vmware:perf:cpu" OR sourcetype="vmware:perf:mem")
| stats avg(cpu_usage_pct) as avg_cpu, p95(cpu_usage_pct) as p95_cpu, avg(mem_usage_pct) as avg_mem, p95(mem_usage_pct) as p95_mem by vm_name
| lookup vm_allocation vm_name OUTPUT allocated_vcpu, allocated_mem_gb, instance_type
| eval cpu_rightsized=case(p95_cpu<25, "Downsize", p95_cpu>90, "Upsize", 1==1, "Right-sized")
| eval mem_rightsized=case(p95_mem<25, "Downsize", p95_mem>90, "Upsize", 1==1, "Right-sized")
| where cpu_rightsized="Downsize" OR mem_rightsized="Downsize"
| table vm_name, instance_type, allocated_vcpu, avg_cpu, p95_cpu, cpu_rightsized, allocated_mem_gb, avg_mem, p95_mem, mem_rightsized
```
- **Implementation:** Collect 30+ days of CPU and memory utilization per VM/instance. Compare P95 utilization against allocated resources. Generate right-sizing recommendations based on workload patterns. Exclude burst workloads from analysis. Calculate estimated savings per recommendation.
- **Visualization:** Table (right-sizing recommendations with savings), Bar chart (waste by team), Scatter plot (allocated vs used), Single value (total potential savings).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.6 · Database Growth Projection

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Databases that run out of space cause application outages. Forecasting database growth enables proactive storage expansion, archive planning, and helps DBAs plan maintenance windows for data lifecycle operations.
- **App/TA:** Database monitoring TAs, `Splunk DB Connect`
- **Data Sources:** Database size metrics, tablespace utilization
- **SPL:**
```spl
index=database sourcetype="db:capacity"
| timechart span=1d latest(db_size_gb) as current_size by db_name
| predict current_size as predicted_size algorithm=LLP5 future_timespan=90
| eval growth_rate_gb_per_day=round(('predicted_size+30d'-current_size)/30, 2)
| where 'predicted_size+90d' > max_size*0.85
```
- **Implementation:** Collect database size metrics daily from all platforms. Track per-database and per-tablespace growth. Use Splunk predict for 90-day growth forecasting. Alert when projected size exceeds 85% of allocated space within 90 days. Plan archival or expansion based on projections.
- **Visualization:** Timechart (database size with forecast), Table (databases approaching limits), Gauge (current utilization), Bar chart (growth rate by database).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
### UC-20.2.7 · Seasonal Capacity Modeling

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Capacity
- **Value:** Many businesses have predictable seasonal patterns (retail holidays, fiscal year-end, enrollment periods). Building seasonal capacity models ensures infrastructure scales proactively for peak periods rather than reactively during customer-impacting events.
- **App/TA:** Infrastructure TAs, Splunk MLTK (Machine Learning Toolkit)
- **Data Sources:** Historical performance data (12+ months)
- **SPL:**
```spl
index=infrastructure sourcetype="perf:summary"
| eval day_of_year=strftime(_time, "%j")
| eval week_of_year=strftime(_time, "%V")
| stats avg(cpu_pct) as avg_cpu, avg(mem_pct) as avg_mem, avg(req_per_sec) as avg_rps by week_of_year
| append [| inputlookup previous_year_seasonal_data]
| stats avg(avg_cpu) as seasonal_cpu, avg(avg_mem) as seasonal_mem, avg(avg_rps) as seasonal_rps by week_of_year
| eval next_year_projected=seasonal_rps*1.15
```
- **Implementation:** Collect 12+ months of performance data for seasonal analysis. Identify recurring patterns (daily, weekly, monthly, seasonal). Build seasonal baseline models using Splunk MLTK or predict. Apply growth factor to historical peaks for next-year projections. Plan capacity expansions 2-3 months ahead of predicted peaks.
- **Visualization:** Timechart (year-over-year seasonal overlay), Area chart (seasonal patterns), Table (peak week projections), Line chart (actual vs seasonal model).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.8 · IP Address Space Utilization

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** IP address exhaustion causes provisioning failures for new VMs, containers, and services. Monitoring IP pool utilization across subnets and VLANs enables proactive network planning and avoids emergency re-addressing projects.
- **App/TA:** IPAM/DHCP TAs, custom scripted inputs
- **Data Sources:** DHCP/IPAM data, subnet allocation records
- **SPL:**
```spl
index=network sourcetype="ipam:pool"
| stats latest(total_ips) as total, latest(allocated_ips) as allocated, latest(available_ips) as available by subnet, vlan, location
| eval used_pct=round((allocated/total)*100, 1)
| eval status=case(used_pct>=90, "Critical", used_pct>=75, "Warning", used_pct>=50, "Normal", 1==1, "Low Use")
| sort -used_pct
| table subnet, vlan, location, total, allocated, available, used_pct, status
```
- **Implementation:** Ingest IPAM/DHCP pool data daily. Track allocation rates per subnet, VLAN, and location. Alert at 75% warning and 90% critical utilization. Plan subnet expansions or new VLAN creation based on utilization trends. Report on unused allocations that could be reclaimed.
- **Visualization:** Table (subnet utilization), Bar chart (utilization by location), Heatmap (subnet usage map), Gauge (overall IP utilization).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.9 · Cloud Commitment and Savings Plan Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Underutilized commitments or savings plans leave money on the table. Monitoring utilization and coverage supports optimization and renewal decisions.
- **App/TA:** AWS Cost Explorer, Azure Cost Management, CUDRI/savings plan data
- **Data Sources:** Commitment usage, savings plan coverage, hourly coverage %
- **SPL:**
```spl
index=cloud_cost sourcetype="aws:savings_plan"
| stats latest(utilization_pct) as util_pct, latest(coverage_pct) as coverage by plan_id, commitment_type
| where util_pct < 80 OR coverage < 70
| table plan_id, commitment_type, util_pct, coverage
```
- **Implementation:** Ingest commitment and savings plan usage from cloud cost APIs. Alert when utilization or coverage drops below target. Report on commitment ROI and recommend size changes at renewal.
- **Visualization:** Gauge (utilization %), Table (plans below target), Line chart (coverage trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.10 · Anomalous Cost Spike by Service or Account
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Sudden cost spikes may indicate runaway resources, misconfiguration, or abuse. Early detection limits bill shock and supports incident response.
- **App/TA:** Cloud cost TAs, billing exports
- **Data Sources:** Daily cost by service, account, region
- **SPL:**
```spl
index=cloud_cost sourcetype="cost:daily"
| stats sum(cost) as daily_cost by service, account_id, _time span=1d
| eventstats avg(daily_cost) as avg_cost, stdev(daily_cost) as std_cost by service, account_id
| where daily_cost > (avg_cost + (3*std_cost))
| table service, account_id, daily_cost, avg_cost, std_cost
```
- **Implementation:** Ingest daily cost by dimensions. Compute baseline and standard deviation. Alert when cost exceeds 3× std dev. Report on top anomalies and trend. Correlate with resource and usage data.
- **Visualization:** Table (anomalous services/accounts), Line chart (cost vs baseline), Bar chart (spike magnitude).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.11 · Unused and Orphaned Resource Cost Attribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Unused disks, idle instances, and orphaned snapshots drive waste. Attributing cost to these resources supports cleanup and chargeback.
- **App/TA:** Cloud resource inventory, cost allocation tags
- **Data Sources:** Resource list with last used, cost, tags
- **SPL:**
```spl
index=cloud_cost sourcetype="resource:inventory"
| where (last_used_days > 30 OR state="stopped") AND cost > 0
| stats sum(cost) as waste_cost, count by resource_type, account_id
| sort -waste_cost
| table resource_type, account_id, count, waste_cost
```
- **Implementation:** Combine resource inventory (with last-used or state) and cost data. Flag idle or stopped resources older than threshold. Report on waste by type and account. Drive cleanup campaigns.
- **Visualization:** Table (waste by type and account), Bar chart (waste cost by resource type), Single value (total waste).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.12 · License and Subscription Consumption vs Entitlement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Over-consumption causes true-up or compliance issues; under-consumption wastes spend. Monitoring usage vs entitlement supports optimization and renewal.
- **App/TA:** License management, SaaS usage APIs
- **Data Sources:** Entitlement count, consumed count, by product and pool
- **SPL:**
```spl
index=licenses sourcetype="license:usage"
| stats latest(entitled) as entitled, latest(consumed) as consumed by product, pool
| eval usage_pct=round((consumed/entitled)*100, 1)
| where usage_pct > 100 OR usage_pct < 50
| table product, pool, entitled, consumed, usage_pct
```
- **Implementation:** Ingest entitlement and consumption from license or SaaS tools. Alert when consumption exceeds entitlement or falls below target. Report on utilization by product and pool. Use for right-sizing at renewal.
- **Visualization:** Table (over/under utilized), Gauge (usage %), Bar chart (consumed vs entitled).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.13 · Cost Forecast vs Budget and Variance Alert
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Forecast over budget risks overspend; large variance indicates model or usage change. Monitoring forecast vs budget supports proactive control and reforecasting.
- **App/TA:** Cost forecasting tool, budget data
- **Data Sources:** Monthly forecast, budget, actuals to date
- **SPL:**
```spl
index=cloud_cost sourcetype="cost:forecast"
| stats latest(forecast_total) as forecast, latest(budget) as budget, latest(actual_ytd) as actual by account_id, month
| eval variance_pct=round((forecast-budget)/budget*100, 1)
| where variance_pct > 10 OR variance_pct < -20
| table account_id, month, forecast, budget, actual, variance_pct
```
- **Implementation:** Ingest forecast and budget. Compute variance. Alert when forecast exceeds budget by threshold or variance is large. Report on forecast accuracy and budget burn rate. Integrate with finance.
- **Visualization:** Table (accounts over budget), Gauge (variance %), Line chart (forecast vs budget trend).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.14 · Software License Compliance Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Compliance
- **Value:** Software license consumption vs. purchased (VMware, Oracle, Microsoft, etc.) visibility prevents compliance violations and identifies over-licensed waste. Tracking concurrent usage against entitlements supports true-up planning and right-sizing at renewal.
- **App/TA:** Custom (license server API, CMDB integration)
- **Data Sources:** License server data (concurrent_in_use, total_licensed), CMDB software inventory
- **SPL:**
```spl
index=licenses (sourcetype="license:server" OR sourcetype="license:usage")
| eval concurrent_in_use=coalesce(concurrent_in_use, in_use, used_count)
| eval total_licensed=coalesce(total_licensed, total_entitled, license_count)
| stats latest(concurrent_in_use) as used, latest(total_licensed) as total by product, vendor, license_server, _time span=1d
| eval utilization_pct=round((used/total)*100, 1)
| eval status=case(utilization_pct>=95, "At Risk", utilization_pct>=80, "High", utilization_pct<40, "Over-licensed", 1==1, "Healthy")
| lookup cmdb_software_inventory product OUTPUT cost_per_seat, cost_center
| eval waste_monthly=if(utilization_pct<40, (total-used)*cost_per_seat, 0)
| sort -utilization_pct
| table product, vendor, used, total, utilization_pct, status, waste_monthly
```
- **Implementation:** Ingest license server data via API or log collection (FlexLM, RLM, VMware vCenter, Oracle LMS, Microsoft VLSC). Map CMDB software inventory for entitlement and cost. Track daily peak concurrent usage. Alert at 90% consumption (compliance risk) and flag <40% utilization (over-licensed). Generate quarterly true-up reports for VMware, Oracle, Microsoft, and other enterprise software.
- **Visualization:** Gauge (overall license utilization), Table (license inventory with status), Bar chart (utilization by product), Timechart (usage trending).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.15 · Power Consumption Cost Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** kWh to cost mapping for data center charge-back enables accurate cost allocation and energy efficiency tracking. Understanding power consumption trends supports capacity planning and identifies cost reduction opportunities.
- **App/TA:** Custom (PDU SNMP, BMS integration, utility billing)
- **Data Sources:** PDU power readings (kWh), utility rate lookup
- **SPL:**
```spl
index=infrastructure (sourcetype="snmp:pdu" OR sourcetype="pdu:power")
| eval kwh=coalesce(kwh, energy_kwh, power_kwh)
| where isnotnull(kwh)
| bin _time span=1d
| stats sum(kwh) as daily_kwh by pdu_id, rack, zone, _time
| lookup utility_rate_lookup zone OUTPUT rate_per_kwh
| eval daily_cost=round(daily_kwh*rate_per_kwh, 2)
| timechart span=1d sum(daily_kwh) as total_kwh, sum(daily_cost) as total_cost by zone
| eval cost_per_kwh=if(total_kwh>0, round(total_cost/total_kwh, 4), 0)
```
- **Implementation:** Collect PDU power readings via SNMP (e.g., OID 1.3.6.1.4.1.2.6.223.8.2.2.1.2 for energy) or BMS integration. Maintain utility rate lookup by zone/tier. Aggregate kWh daily per rack, zone, or cost center. Map kWh to cost for charge-back reports. Alert on anomalous power spikes. Build dashboards for energy cost trending and charge-back allocation.
- **Visualization:** Timechart (kWh and cost trending), Table (cost by rack/zone), Bar chart (top consumers by cost), Single value (monthly power cost).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.16 · Cloud Committed-Use Discount Coverage
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Cost
- **Value:** Reserved instance and savings plan coverage percentage monitoring ensures committed-use discounts are utilized. Unused commitments waste money; gaps in coverage mean paying on-demand rates. Optimizing coverage typically saves 30–50% vs on-demand.
- **App/TA:** `Splunk Add-on for AWS`, `Splunk Add-on for Microsoft Cloud Services`, `Splunk Add-on for Google Cloud Platform`
- **Data Sources:** AWS CUR (reservation utilization), Azure Advisor reservation recommendations, GCP commitment usage
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| eval is_reserved=if(isnotnull(reservation_ReservationARN) AND reservation_ReservationARN!="", 1, 0)
| eval is_on_demand=if(lineItem_UsageType LIKE "%BoxUsage%" AND is_reserved=0, 1, 0)
| bin _time span=1d
| stats sum(eval(if(is_reserved=1, cost, 0))) as ri_cost, sum(eval(if(is_on_demand=1, cost, 0))) as on_demand_cost, sum(cost) as total_cost by lineItem_UsageAccountId, _time
| eval coverage_pct=round((ri_cost/total_cost)*100, 1)
| eval uncovered_cost=on_demand_cost
| where total_cost > 0
| stats avg(coverage_pct) as avg_coverage, sum(uncovered_cost) as uncovered by lineItem_UsageAccountId
| eval status=case(avg_coverage<70, "Low Coverage", uncovered>1000, "High Uncovered Cost", 1==1, "OK")
| where status!="OK"
| sort -uncovered
| table lineItem_UsageAccountId, avg_coverage, uncovered, status
```
- **Implementation:** Ingest AWS CUR with reservation fields, Azure Cost Management reservation utilization, and GCP commitment usage. Calculate coverage as (RI/savings plan cost) / (total compute cost). Alert when coverage drops below 70% or uncovered on-demand spend exceeds threshold. Report on unused commitment hours and recommend size changes. Correlate with Azure Advisor and AWS Cost Explorer recommendations for optimization.
- **Visualization:** Gauge (coverage percentage), Timechart (coverage trend with forecast), Table (accounts with low coverage), Bar chart (uncovered cost by account).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876), [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110), [Splunk Add-on for Google Cloud Platform](https://splunkbase.splunk.com/app/3088)
### UC-20.2.17 · Storage Capacity Forecast by Tier

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Forecast days-to-full per storage tier (flash vs capacity) — extends pool forecasting (UC-20.2.2) with **tier** dimension for procurement.
- **App/TA:** Storage TA, SNMP
- **Data Sources:** `storage:capacity` with `tier`
- **SPL:**
```spl
index=storage sourcetype="storage:capacity" earliest=-90d
| timechart span=1d latest(used_pct) as used_pct by storage_system, tier
| predict used_pct algorithm=LLP5 future_timespan=60
```
- **Implementation:** Map array vendor tiers. Alert when 60d forecast crosses 90% for any tier.
- **Visualization:** Line chart (used % by tier), Table (at-risk systems), Gauge.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.18 · Compute Cluster Scaling Headroom

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Remaining vCPU and RAM in VMware/vSphere clusters and AWS ASG max — for **provisioning headroom** beyond host forecast (UC-20.2.1).
- **App/TA:** vCenter TA, AWS API
- **Data Sources:** `vmware:cluster`, `aws:compute:capacity`
- **SPL:**
```spl
index=virtualization sourcetype="vmware:cluster" earliest=-1h
| eval headroom_pct=round(100*(cpu_capacity_mhz-cpu_used_mhz)/cpu_capacity_mhz,1)
| where headroom_pct < 15
| table cluster_name, headroom_pct, cpu_used_mhz, cpu_capacity_mhz
```
- **Implementation:** Poll cluster aggregate capacity. Alert when headroom <15% or policy threshold. Trigger scale-out or new hardware.
- **Visualization:** Gauge (headroom %), Table (clusters at risk), Bar chart (by datacenter).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.19 · Network Bandwidth Utilization Trending (Site Interconnect)

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Site-to-site and DCI link utilization trend with 95th percentile — complements interface forecast (UC-20.2.3).
- **App/TA:** SNMP, NetFlow summary
- **Data Sources:** `snmp:interface`, `netflow:site`
- **SPL:**
```spl
index=network sourcetype="netflow:site" earliest=-30d
| timechart span=1d perc95(utilization_pct) as p95_util by link_name
| where p95_util > 75
| table link_name, p95_util
```
- **Implementation:** Aggregate flows per DCI link daily. Alert on sustained high p95. Plan circuit upgrades.
- **Visualization:** Line chart (p95 util by link), Table (saturated links), Heatmap.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.20 · Seasonal Capacity Planning Baseline

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** YoY same-week CPU/RPS comparison for retail/event peaks — extends UC-20.2.7 with **automated peak week** flagging.
- **App/TA:** `perf:summary`, MLTK optional
- **Data Sources:** Weekly rollups per app
- **SPL:**
```spl
index=infrastructure sourcetype="perf:summary" earliest=-400d
| eval week=strftime(_time,"%V")
| stats avg(cpu_pct) as cpu by app, week
| eventstats avg(cpu) as fleet_week_avg by week
| where cpu > fleet_week_avg*1.25
| table app, week, cpu, fleet_week_avg
```
- **Implementation:** Simplify with `timewrap` if available. Use for pre-peak scale plans.
- **Visualization:** Line chart (YoY overlay), Table (apps with growth), Calendar heatmap.
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.21 · CPU and Memory Right-Sizing (Host and VM)

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Host-level overcommit risk and VM-level downsize candidates — pairs with VM view (UC-20.2.5).
- **App/TA:** `Splunk_TA_vmware`, `Splunk_TA_windows` (Hyper-V Perfmon)
- **Data Sources:** `vmware:host:perf`
- **SPL:**
```spl
index=virtualization sourcetype="vmware:host:perf" earliest=-7d
| stats avg(cpu_used_pct) as cpu, avg(mem_used_pct) as mem by host
| eval overcommit_risk=if(cpu>85 OR mem>90,1,0)
| where overcommit_risk=1
| table host, cpu, mem
```
- **Implementation:** Combine with cluster headroom (UC-20.2.18). Alert on chronic host saturation.
- **Visualization:** Table (hot hosts), Heatmap (host × day), Gauge.
- **CIM Models:** N/A

- **References:** [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
### UC-20.2.22 · Disk IOPS Saturation Trending

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Time-series of `iops_utilization_pct` or latency vs IOP limit for SAN/NVMe — storage performance bottleneck before capacity full.
- **App/TA:** Storage TA
- **Data Sources:** `storage:performance`, array metrics
- **SPL:**
```spl
index=storage sourcetype="storage:performance" earliest=-7d
| timechart span=1h avg(iops_util_pct) as iops_util avg(read_latency_ms) as lat by volume_id
| where iops_util>80 OR lat>10
```
- **Implementation:** Map vendor IOPS cap. Alert on sustained >80% util or latency SLO breach. Scale pool or move workload.
- **Visualization:** Line chart (IOPS util and latency), Table (hot volumes), Single value (volumes in saturation).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)
### UC-20.2.23 · VM Sprawl Detection

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Count of powered-on VMs per app owner vs license and growth rate — finds unchecked provisioning.
- **App/TA:** vCenter inventory
- **Data Sources:** `vmware:inv:vm`
- **SPL:**
```spl
index=virtualization sourcetype="vmware:inv:vm" earliest=-1d
| where power_state="poweredOn"
| stats count as vm_count by folder, owner
| eventstats avg(vm_count) as fleet_avg
| where vm_count > fleet_avg*3 AND vm_count>50
| sort -vm_count
```
- **Implementation:** Map `owner` from folder or tags. Review quarterly for consolidation. Correlate with cost (UC-20.1).
- **Visualization:** Bar chart (VM count by owner), Table (sprawl candidates), Line chart (VM growth).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.24 · Cloud Cost Anomaly with Seasonal Decomposition (MLTK)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Cost
- **Value:** Cloud costs follow predictable weekly and monthly cycles — batch jobs on weekends, month-end reporting spikes, quarterly compliance scans. Static thresholds generate noise during normal peaks and miss slow-growth anomalies during quiet periods. By decomposing cost into seasonal, trend, and residual components with MLTK, this detection flags true anomalies against the expected cost shape for that specific day and hour.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK), Splunk Add-on for AWS / Azure / GCP
- **Data Sources:** `index=cloud sourcetype=aws:billing` or `sourcetype=azure:costmanagement` or `sourcetype=gcp:billing`
- **SPL:**
```spl
index=cloud sourcetype IN ("aws:billing","azure:costmanagement","gcp:billing")
| bin _time span=1d
| stats sum(cost) as daily_cost by _time, service_name, account_id
| eval dow=strftime(_time, "%A"), dom=strftime(_time, "%d")
| fit StateSpaceForecast daily_cost holdback=0 forecast_k=14 conf_interval=95 by service_name into cost_seasonal_model
| eval residual=daily_cost - 'predicted(daily_cost)'
| eval pct_deviation=round(100*residual/nullif('predicted(daily_cost)', 0), 1)
| where abs(pct_deviation) > 25 OR daily_cost > 'upper95(predicted(daily_cost))'
| table _time, service_name, account_id, daily_cost, "predicted(daily_cost)", pct_deviation
| sort -pct_deviation
```
- **Implementation:** Ingest cloud billing data daily from CUR (AWS), Cost Management exports (Azure), or BigQuery billing export (GCP). Train StateSpaceForecast models per service that capture weekly seasonality (weekend dips) and monthly patterns (month-end peaks). Forecast 14 days ahead with 95% confidence intervals. Alert FinOps teams when actual cost exceeds the upper confidence bound or deviates more than 25% from the seasonal prediction. Include account-level drill-down to identify the specific workload driving the anomaly. Retrain models monthly. Pair with UC-20.1.13 for budget variance context and UC-20.1.18 for orphaned resource identification when cost spikes correlate with new resources.
- **Visualization:** Area chart (actual vs forecast with confidence band), Table (anomalous services), Bar chart (top cost deviations by service).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-20.2.25 · Capacity Exhaustion Prediction with Confidence Intervals (MLTK)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Linear extrapolation of resource growth is dangerously simplistic — it misses seasonal acceleration, step changes from new workloads, and growth rate changes after migrations. Probabilistic forecasting with MLTK provides a range of exhaustion dates (best/expected/worst case) so capacity teams can plan procurement and migrations with appropriate urgency.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK)
- **Data Sources:** `index=infra sourcetype=vmware:perf:cpu` or `sourcetype=linux:cpu` or `index=k8s sourcetype=kube:metrics`
- **SPL:**
```spl
index=infra sourcetype IN ("vmware:perf:cpu","linux:cpu","nix:df")
| bin _time span=1d
| stats avg(pctUsed) as avg_utilization by _time, host, resource_type
| fit StateSpaceForecast avg_utilization holdback=0 forecast_k=90 conf_interval=95 by host into capacity_forecast_model
| where 'upper95(predicted(avg_utilization))' > 85
| eval days_to_85=round(('upper95(predicted(avg_utilization))' - avg_utilization) / (('predicted(avg_utilization)' - avg_utilization) / 90), 0)
| where days_to_85 > 0 AND days_to_85 < 90
| table host, resource_type, avg_utilization, "predicted(avg_utilization)", "upper95(predicted(avg_utilization))", days_to_85
| sort days_to_85
```
- **Implementation:** Collect daily average utilization metrics for CPU, memory, disk, and network across hosts, VMs, and containers. Train StateSpaceForecast models per host-resource combination that learn growth trends and seasonal patterns. Forecast 90 days ahead with 95% confidence intervals. Flag resources where the upper confidence bound crosses the saturation threshold (85%) within the forecast window. Provide three timeline estimates: optimistic (lower bound), expected (point forecast), and pessimistic (upper bound). Integrate with CMDB for asset lifecycle context. Alert capacity planning teams monthly with prioritized lists sorted by days-to-exhaustion.
- **Visualization:** Area chart (utilization forecast with confidence band), Table (resources approaching saturation), Gantt chart (exhaustion timelines by host).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.26 · Kubernetes Namespace Resource Quota Pressure

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Hard quotas stop deployments during peak traffic, causing revenue-impacting outages. Tracking requested versus hard limits for CPU, memory, and persistent volume claims per namespace lets platform teams expand quotas or reclaim unused requests before developers hit the wall.
- **App/TA:** Kubernetes metrics TA, Prometheus exporter, OpenTelemetry
- **Data Sources:** `index=kubernetes` `sourcetype="kube:quota"`
- **SPL:**
```spl
index=kubernetes sourcetype="kube:quota" earliest=-1h
| eval cpu_req=tonumber(coalesce(cpu_requests_cores, cpu_requests))
| eval cpu_lim=tonumber(coalesce(cpu_hard_quota_cores, cpu_hard_limit))
| eval mem_req=tonumber(coalesce(memory_requests_gib, mem_requests_gib))
| eval mem_lim=tonumber(coalesce(memory_hard_quota_gib, mem_hard_limit_gib))
| eval cpu_headroom_pct=round(100*(cpu_lim-cpu_req)/nullif(cpu_lim,0),1)
| eval mem_headroom_pct=round(100*(mem_lim-mem_req)/nullif(mem_lim,0),1)
| where cpu_headroom_pct<15 OR mem_headroom_pct<15
| stats latest(cpu_headroom_pct) as cpu_head latest(mem_headroom_pct) as mem_head by cluster, namespace
| sort cluster, cpu_head
```
- **Implementation:** (1) Ingest kube-state-metrics quota objects or a vendor CMDB export with limits and allocated requests. (2) Alert when headroom stays below 15% for six hours. (3) Pair with cost data (UC-20.1.16) before raising quotas on idle namespaces.
- **Visualization:** Heatmap (namespace × resource headroom), Table (clusters at risk), Gauge (worst namespace headroom).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.27 · Object Storage Bucket Growth Forecast

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Cost
- **Value:** Object storage growth from logs, images, and backups drives recurring invoices. Forecasting gigabytes by bucket supports lifecycle policies, intelligent tiering, and archive capacity before ingest jobs fail.
- **App/TA:** `Splunk Add-on for AWS`, Azure Storage metrics, GCP monitoring export
- **Data Sources:** `index=cloud_storage` `sourcetype="aws:s3:bucket_metrics"`
- **SPL:**
```spl
index=cloud_storage sourcetype="aws:s3:bucket_metrics" earliest=-90d
| eval gb=tonumber(coalesce(size_bytes, BucketSizeBytes))/1024/1024/1024
| bin _time span=1d
| stats latest(gb) as used_gb by _time, bucket_name, account_id
| timechart span=1d latest(used_gb) as used_gb by bucket_name
| predict used_gb as forecast_gb algorithm=LLP5 future_timespan=60
| where 'forecast_gb+60d' > used_gb*1.25
| table bucket_name, used_gb, 'forecast_gb+60d'
```
- **Implementation:** (1) Collect bucket size daily from CloudWatch `BucketSizeBytes`, Storage Lens, or vendor export. (2) Exclude buckets with heavy lifecycle churn unless using MLTK for seasonality. (3) Alert owners when the 60-day forecast exceeds 125% of current size.
- **Visualization:** Line chart (actual versus forecast per bucket), Table (fastest-growing buckets), Single value (total forecasted terabytes).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-20.2.28 · Database Datafile Size and Autogrow Trending

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** SQL Server and Oracle datafiles that autogrow frequently signal unexpected data loads or missing archival. Trending file size and growth events avoids emergency disk extensions during month-end loads.
- **App/TA:** `Splunk DB Connect`, database monitoring scripts
- **Data Sources:** `index=database` `sourcetype="db:filegrowth"`
- **SPL:**
```spl
index=database sourcetype="db:filegrowth" earliest=-60d
| eval size_gb=tonumber(coalesce(size_gb, current_size_gb))
| eval ev=lower(coalesce(event_type, message, ""))
| eval grew=if(match(ev, "(grow|extend|autogrow)"),1,0)
| bin _time span=1d
| stats latest(size_gb) as size_gb sum(grew) as grow_events by _time, db_name, logical_filename
| sort 0 db_name, logical_filename, _time
| streamstats global=f window=2 earliest(size_gb) as prev_gb by db_name, logical_filename
| eval daily_delta_gb=round(size_gb-prev_gb,2)
| where daily_delta_gb>5 OR grow_events>3
| table _time, db_name, logical_filename, size_gb, grow_events, daily_delta_gb
```
- **Implementation:** (1) Push file-level metrics and autogrow events from DB Connect or a DBA agent. (2) Map `logical_filename` to disk mount for infrastructure correlation. (3) Page when daily delta exceeds policy (example five GB) or grow_events exceeds three in one day.
- **Visualization:** Timechart (size by database), Table (large deltas and autogrow counts), Bar chart (top databases by growth rate).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-20.2.29 · Site-to-Site VPN Tunnel Bandwidth Headroom

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity, Performance
- **Value:** VPN tunnels to cloud and partners have fixed negotiated throughput. Sustained high utilization causes latency and drops during batch windows. Headroom reporting triggers circuit upgrades or traffic engineering before outages.
- **App/TA:** SNMP, `Splunk Add-on for AWS` (VPN metrics), SD-WAN TA
- **Data Sources:** `index=network` `sourcetype="vpn:tunnel"`
- **SPL:**
```spl
index=network sourcetype="vpn:tunnel" earliest=-7d
| eval bps=tonumber(coalesce(ingress_bps, in_bps))+tonumber(coalesce(egress_bps, out_bps))
| eval cap=tonumber(coalesce(negotiated_bandwidth_bps, tunnel_capacity_bps))
| eval util_pct=round(100*bps/nullif(cap,0),2)
| bin _time span=5m
| stats perc95(util_pct) as p95_util by tunnel_id, site_name
| eval headroom_pct=round(100-p95_util,1)
| where headroom_pct < 20
| sort headroom_pct
```
- **Implementation:** (1) Ingest per-tunnel throughput from SD-WAN or cloud VPN metrics. (2) Store negotiated capacity per tunnel in a lookup. (3) Alert when seven-day P95 utilization leaves less than twenty percent headroom.
- **Visualization:** Gauge (headroom percent), Line chart (utilization trend), Table (tunnels sorted by risk).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-20.2.30 · Search and Analytics Cluster Disk Watermark Risk

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** OpenSearch and Elasticsearch clusters stop indexing when disk watermarks are breached, breaking log and application pipelines. Tracking used shard store versus cluster capacity predicts when frozen tiers or data nodes must be added.
- **App/TA:** Elastic/OpenSearch monitoring API, HTTP Event Collector
- **Data Sources:** `index=observability` `sourcetype="elastic:cluster_stats"`
- **SPL:**
```spl
index=observability sourcetype="elastic:cluster_stats" earliest=-30d
| eval used=tonumber(coalesce(store_size_bytes, total_used_bytes))
| eval total=tonumber(coalesce(total_capacity_bytes, disk_total_bytes))
| eval used_pct=round(100*used/nullif(total,0),2)
| bin _time span=1d
| stats latest(used_pct) as used_pct by _time, cluster_name
| predict used_pct as forecast_pct algorithm=LLP5 future_timespan=30
| where 'forecast_pct+30d' > 75
| table cluster_name, used_pct, 'forecast_pct+30d'
```
- **Implementation:** (1) Poll `_cluster/stats` or Elastic Cloud metrics daily. (2) Align thresholds with `cluster.routing.allocation.disk.watermark` settings. (3) Integrate with storage forecasting (UC-20.2.2) when forecast crosses seventy-five percent within thirty days.
- **Visualization:** Area chart (used percent with forecast), Table (clusters breaching planning threshold), Single value (clusters over watermark risk).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.31 · Message Broker Disk and Retention Capacity

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Cost
- **Value:** Kafka retains messages on disk; retention growth from new microservices or poison-pill topics can fill brokers and halt producers. Monitoring log segment volume and free disk prevents cascading application failures.
- **App/TA:** JMX TA, Prometheus, Confluent metrics exporter
- **Data Sources:** `index=messaging` `sourcetype="kafka:broker:disk"`
- **SPL:**
```spl
index=messaging sourcetype="kafka:broker:disk" earliest=-14d
| eval used_gb=tonumber(coalesce(log_size_gb, kafka_log_size_gb))
| eval free_gb=tonumber(coalesce(disk_free_gb, volume_free_gb))
| eval total_gb=used_gb+free_gb
| eval used_pct=round(100*used_gb/nullif(total_gb,0),1)
| bin _time span=1h
| stats latest(used_pct) as used_pct latest(retention_hours) as ret_hrs by _time, broker_id, cluster
| where used_pct>70
| stats max(used_pct) as peak_used min(ret_hrs) as min_ret by cluster, broker_id
| sort -peak_used
```
- **Implementation:** (1) Export per-broker log volume and filesystem free space. (2) Alert when used_pct exceeds seventy percent for four hours or minimum retention hours drops unexpectedly. (3) Correlate with topic byte rate to find noisy producers.
- **Visualization:** Line chart (disk used percent by broker), Table (brokers over threshold), Heatmap (cluster by broker).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.32 · GPU Pool Utilization for ML Workload Capacity

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity, Performance
- **Value:** GPU nodes are expensive; low average utilization wastes capital while queue spikes delay training service levels. Tracking streaming-multiprocessor utilization and peak load by host informs autoscaler bounds and purchase versus spot decisions.
- **App/TA:** NVIDIA DCGM exporter, Kubernetes GPU metrics, cloud GPU monitoring
- **Data Sources:** `index=ml_infra` `sourcetype="dcgm:gpu"`
- **SPL:**
```spl
index=ml_infra sourcetype="dcgm:gpu" earliest=-7d
| eval util=tonumber(coalesce(gpu_sm_utilization, sm_util_pct))
| bin _time span=1h
| stats avg(util) as avg_sm perc95(util) as p95_sm by _time, host, gpu_index
| stats avg(avg_sm) as fleet_avg max(p95_sm) as fleet_p95 by host
| eval underused=if(fleet_avg<35 AND fleet_p95<70,1,0)
| where underused=1 OR fleet_p95>92
| table host, fleet_avg, fleet_p95
```
- **Implementation:** (1) Deploy DCGM on GPU nodes and normalize `gpu_index`. (2) Tag hosts with workload type such as training versus inference. (3) Right-size node pools when underused persists fourteen days; scale out when fleet_p95 exceeds ninety-two.
- **Visualization:** Box plot (utilization distribution), Table (underused hosts), Timechart (job queue depth if ingested).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.2.33 · Domain Controller Performance Under LDAP Load

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Authentication and directory search storms can saturate domain controllers before generic server CPU alerts explain the blast radius. Correlating directory operation rate with CPU utilization supports extra domain controllers, load balancing changes, and misbehaving application fixes.
- **App/TA:** `Splunk Add-on for Microsoft Windows`, scripted performance export
- **Data Sources:** `index=active_directory` `sourcetype="ad:dc:performance"`
- **SPL:**
```spl
index=active_directory sourcetype="ad:dc:performance" earliest=-24h
| eval ldap_ops=tonumber(coalesce(ldap_searches_sec, ldap_ops_per_sec))
| eval cpu_pct=tonumber(coalesce(cpu_utilization, cpu_load_percent))
| bin _time span=5m
| stats avg(ldap_ops) as ldap_avg avg(cpu_pct) as cpu_avg by _time, host
| eventstats median(ldap_avg) as med_ldap by host
| eval stress=if(ldap_avg>med_ldap*2.5 AND cpu_avg>80,1,0)
| where stress=1
| table _time, host, ldap_avg, cpu_avg, med_ldap
```
- **Implementation:** (1) Collect NTDS `LDAP Searches/sec` and total CPU via Performance Monitor or a lightweight forwarder script into `ad:dc:performance`. (2) Tune multipliers for your baseline. (3) Escalate repeated stress windows to the identity engineering team with top calling applications from firewall or load balancer logs.
- **Visualization:** Timeline (stress markers overlaid on CPU), Table (domain controllers with correlated spikes), Single value (stress hours per week).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Microsoft Windows](https://splunkbase.splunk.com/app/742)

---

### 20.3 License & Subscription Management

**Primary App/TA:** Microsoft 365 / Entra ID reporting add-ons, Salesforce Splunk Connector, Flexera / ServiceNow SAM exports, `license:usage` HEC, cloud marketplace billing (AWS/Azure/GCP subscription lines).

---

### UC-20.3.1 · SaaS License Utilization (Assigned vs Active)

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Compliance
- **Value:** Paying for assigned-but-unused seats wastes budget; comparing entitlements to real sign-in or activity highlights reclaim and right-size opportunities before renewals.

- **App/TA:** Microsoft Entra ID Add-on, Okta Splunk App, Salesforce TA
- **Data Sources:** `sourcetype=license:usage`, `sourcetype=o365:reporting`
- **SPL:**
```spl
index=saas sourcetype="license:usage"
| eval assigned=coalesce(licenses_assigned,0), active=coalesce(active_users_30d,0)
| eval utilization_pct=round(100*active/nullif(assigned,0),1)
| where utilization_pct < 70 OR active < assigned*0.5
| stats latest(assigned) as assigned latest(active) as active latest(utilization_pct) as util_pct by product, sku, cost_center
| sort util_pct
```
- **Implementation:** Ingest monthly license assignment exports and last-sign-in or 30-day active user counts from IdP or vendor admin APIs. Schedule weekly jobs; join on `sku`/`product`. Alert when utilization drops below policy thresholds. Feed reclamation workflows with user lists.
- **Visualization:** Bar chart (utilization % by product), Table (reclaim candidates), Single value (wasted seat estimate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.2 · Software Audit Readiness Reporting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Audit-ready evidence of installs, purchases, and usage reduces true-up penalties and speeds vendor true-up negotiations.

- **App/TA:** Flexera / Snow SAM export, ServiceNow SAM, Splunk Universal Forwarder inventory
- **Data Sources:** `sourcetype=license:usage`, `sourcetype=inventory:software`
- **SPL:**
```spl
index=software (sourcetype="license:usage" OR sourcetype="inventory:software")
| eval publisher=coalesce(publisher,vendor), edition=coalesce(edition,product_name)
| stats dc(host) as install_count sum(entitlement_count) as purchased by publisher, edition
| eval gap=install_count-purchased
| where gap>0 OR isnull(purchased)
| table publisher, edition, install_count, purchased, gap
```
- **Implementation:** Normalize discovery data from endpoints and purchase records from procurement. Refresh entitlements from contract system. Dashboard shows install vs entitlement gap by publisher. Export CSV for auditor quarterly.
- **Visualization:** Table (gap by title), Bar chart (over-deployed publishers), Single value (total gap count).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.3 · Subscription Renewal Forecasting

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Forecasting renewal cash-out dates and contract values avoids surprise budget hits and gives procurement time to negotiate or consolidate vendors.

- **App/TA:** Contract repository export (ServiceNow SPM, Ariba), marketplace billing
- **Data Sources:** `sourcetype=license:usage`, `sourcetype=aws:billing:cur`
- **SPL:**
```spl
(index=contracts sourcetype="license:usage") OR (index=cloud_billing sourcetype="aws:billing:cur")
| eval renewal_epoch=strptime(renewal_date,"%Y-%m-%d"), amount=tonumber(annual_cost_usd)
| where renewal_epoch > relative_time(now(),"+30d@d") AND renewal_epoch < relative_time(now(),"+365d@d")
| eval days_until=round((renewal_epoch-now())/86400,0)
| stats sum(amount) as renewal_spend by vendor, renewal_date, cost_center
| sort renewal_date
```
- **Implementation:** Load subscription end dates and annual amounts from CLM or reseller exports; for AWS/Azure/GCP, tag marketplace subscriptions. Alert 90/60/30 days before renewal. Combine with utilization metrics to decide downgrade options before signing.
- **Visualization:** Timeline (renewals by quarter), Table (upcoming renewals), Single value (12-month renewal liability).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.4 · License Compliance Gap Detection

- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Security
- **Value:** Unlicensed use of enterprise software creates legal and financial exposure; continuous gap detection supports proactive remediation.

- **App/TA:** SAM inventory, Adobe/Microsoft portal exports
- **Data Sources:** `sourcetype=inventory:software`, `sourcetype=license:usage`
- **SPL:**
```spl
index=software sourcetype="inventory:software"
| search is_licensed="false" OR compliance_status="unlicensed"
| stats count by host, software_name, version, last_seen
| lookup license_entitlements software_name OUTPUT entitlement_qty
| eval breach=if(count>entitlement_qty OR isnull(entitlement_qty),1,0)
| where breach=1
| sort -count
```
- **Implementation:** Flag installs without matching entitlement rows in a KV store refreshed from purchases. Reconcile named-user products with IdP group membership. Alert on new breaches weekly; assign owners by `cost_center`.
- **Visualization:** Table (compliance gaps), Single value (open violations), Bar chart (gaps by department).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.5 · Multi-Year Contract Consumption Trending

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity, Cost
- **Value:** Enterprise agreements with committed spend need burn-down tracking; falling behind consumption risks leaving value on the table, while overspending early risks true-up shocks.

- **App/TA:** AWS/GCP/Azure EA billing, custom commitment tracker
- **Data Sources:** `sourcetype=aws:billing:cur`, `sourcetype=license:usage`
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval spend=tonumber(lineItem_UnblendedCost)
| eval contract_id=coalesce(agreement_id,license_pool_id)
| bin _time span=1mon
| stats sum(spend) as monthly_spend by contract_id, _time
| sort contract_id, _time
| streamstats sum(monthly_spend) as ytd_spend by contract_id
| lookup contract_commitments contract_id OUTPUT commit_total_usd
| eval pct_consumed=round(100*ytd_spend/nullif(commit_total_usd,0),1)
| table contract_id, _time, ytd_spend, pct_consumed
```
- **Implementation:** Map invoices and usage lines to enterprise agreement IDs. Compare cumulative spend to committed totals and contract term. Project end-of-term position with linear or seasonal fit. Alert if consumption is off pace vs. expected curve.
- **Visualization:** Line chart (% consumed vs time), Gauge (YTD vs commit), Table (contract status).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.6 · License Pool Allocation Optimization

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Shifting unused pool capacity between departments or regions avoids buying new seats while one pool sits idle.

- **App/TA:** ServiceNow SAM, custom pool allocator
- **Data Sources:** `sourcetype=license:usage`
- **SPL:**
```spl
index=saas sourcetype="license:usage"
| stats sum(assigned) as assigned sum(consumed) as consumed by pool_id, org_unit
| eval slack=assigned-consumed
| eventstats sum(slack) as total_slack by pool_id
| where slack < 0 OR (slack > 50 AND total_slack > 0)
| sort pool_id, slack
```
- **Implementation:** Ingest per–cost-center assignments against shared enterprise pools. Identify negative slack (overallocation) and large positive slack (reclaimable). Recommend transfers using simple optimization rules in a lookup updated monthly.
- **Visualization:** Heatmap (org × pool utilization), Table (rebalance suggestions), Bar chart (slack by pool).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.7 · Auto-Renewal Risk Detection

- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Cost
- **Value:** Unwanted auto-renewals lock spend for another term; early visibility lets legal and procurement opt out or renegotiate within notice windows.

- **App/TA:** CLM webhook, calendar export, `license:usage` metadata
- **Data Sources:** `sourcetype=license:usage`, `sourcetype=contracts:events`
- **SPL:**
```spl
index=contracts (sourcetype="license:usage" OR sourcetype="contracts:events")
| eval opt_out_deadline=strptime(cancellation_deadline,"%Y-%m-%d")
| eval auto_renew=if(match(lower(renewal_terms),"auto"),1,0)
| where auto_renew=1 AND opt_out_deadline > now() AND opt_out_deadline < relative_time(now(),"+90d@d")
| eval days_to_opt_out=round((opt_out_deadline-now())/86400,0)
| table vendor, product, renewal_date, cancellation_deadline, days_to_opt_out, owner
| sort days_to_opt_out
```
- **Implementation:** Capture `auto_renew` flags and contractual opt-out dates from vendor metadata or CLM. Alert owners at 90/60/30 days before the cancellation window closes. Track completion of opt-out tickets in ITSM.
- **Visualization:** Table (upcoming opt-out deadlines), Single value (contracts at risk), Timeline (deadlines).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.8 · Microsoft 365 Inactive License Harvest Candidates

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Capacity
- **Value:** Seats assigned to users who have not signed in for months are pure renewal waste. Identifying inactive assignees before true-up converts soft savings into reclaimed licenses and lower E5 or add-on counts at contract signature.
- **App/TA:** Microsoft Entra ID Add-on, `o365:reporting` HEC export, Graph API scripted input
- **Data Sources:** `index=saas` `sourcetype="o365:license_assignment"`
- **SPL:**
```spl
index=saas sourcetype="o365:license_assignment" earliest=-1d
| eval last_signin=if(isnotnull(last_signin_epoch), last_signin_epoch, strptime(last_signin,"%Y-%m-%dT%H:%M:%SZ"))
| eval inactive_days=round((now()-last_signin)/86400,0)
| where isnotnull(assigned_license_sku) AND assigned_license_sku!="" AND (inactive_days>90 OR isnull(last_signin))
| stats dc(user_upn) as harvest_candidates sum(monthly_seat_cost_usd) as monthly_at_risk by assigned_license_sku, department
| sort -monthly_at_risk
```
- **Implementation:** (1) Ingest daily license assignment with last interactive sign-in from Graph `reports/getOffice365ActivationsUserDetail` or equivalent. (2) Join `monthly_seat_cost_usd` from a procurement lookup by SKU. (3) Open harvest tickets only after manager approval workflow in ITSM.
- **Visualization:** Table (SKU and department reclaim value), Bar chart (inactive seats by workload), Single value (total monthly at-risk dollars).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.9 · Salesforce Seat Activity vs Purchased Licenses

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Performance
- **Value:** Salesforce contracts charge per seat tier while many users only log in quarterly for reporting. Comparing thirty-day active logins to purchased seats highlights downgrade and permission-set consolidation opportunities before renewal ramps.
- **App/TA:** Salesforce Splunk Connector, EventLog from Salesforce Shield (optional)
- **Data Sources:** `index=saas` `sourcetype="salesforce:login"`
- **SPL:**
```spl
index=saas sourcetype="salesforce:login" earliest=-30d
| eval uid=coalesce(user_id, USER_ID)
| stats dc(uid) as active_users_30d by org_id
| join type=left org_id [
  search index=saas sourcetype="salesforce:license_snapshot" earliest=-1d
  | stats latest(purchased_seats) as purchased by org_id
]
| eval utilization_pct=round(100*active_users_30d/nullif(purchased,0),1)
| eval slack_seats=purchased-active_users_30d
| where slack_seats>20 OR utilization_pct<60
| table org_id, purchased, active_users_30d, utilization_pct, slack_seats
```
- **Implementation:** (1) Schedule daily license snapshot via Salesforce REST into `salesforce:license_snapshot`. (2) Deduplicate login events per user per day before `dc`. (3) Feed slack_seats into renewal negotiation talking points.
- **Visualization:** Gauge (utilization percent), Bar chart (slack seats by org), Table (orgs under sixty percent utilization).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.10 · ServiceNow Fulfiller versus Requester License Mix

- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Cost, Compliance
- **Value:** ITSM platforms often blend fulfiller, approver, and requester licenses; over-purchasing fulfiller seats while requester counts spike drives both waste and audit findings. Aligning provisioned roles to transaction patterns avoids shelfware and compliance gaps.
- **App/TA:** ServiceNow Splunk Integration, `snow:license` export
- **Data Sources:** `index=itsm` `sourcetype="snow:user_role"`
- **SPL:**
```spl
index=itsm sourcetype="snow:user_role" earliest=-1d
| eval fulfiller=if(match(lower(roles),"itil|fulfiller|agent"),1,0)
| stats dc(eval(if(fulfiller=1,user_id,null()))) as fulfiller_users
        dc(user_id) as total_users by instance_name
| join type=left instance_name [
  search index=itsm sourcetype="snow:transaction" earliest=-30d
  | stats dc(opened_by) as active_requesters by instance_name
]
| eval fulfiller_ratio=round(100*fulfiller_users/nullif(total_users,0),1)
| where fulfiller_users>active_requesters*1.5 OR fulfiller_ratio>35
| table instance_name, fulfiller_users, active_requesters, fulfiller_ratio
```
- **Implementation:** (1) Export user-to-role assignments nightly from ServiceNow `sys_user_has_role`. (2) Count distinct requesters from `incident` and `sc_request` over thirty days. (3) Work with process owners when fulfiller count greatly exceeds active requesters.
- **Visualization:** Scatter plot (fulfiller users versus active requesters), Table (instances over policy ratio), Single value (excess fulfiller seats estimate from lookup).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.11 · Oracle Database Option Usage versus Entitlements

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Cost
- **Value:** Options such as Partitioning, Advanced Compression, and Diagnostics Pack are metered separately from the processor license. Undetected feature use creates audit exposure and six-figure true-up risk; proactive comparison to LMS entitlements funds remediation projects instead of penalties.
- **App/TA:** `Splunk DB Connect` (DBA_FEATURE_USAGE_STATISTICS), Oracle audit exports
- **Data Sources:** `index=database` `sourcetype="oracle:option_usage"`
- **SPL:**
```spl
index=database sourcetype="oracle:option_usage" earliest=-1d
| eval detected=if(upper(currently_used)="TRUE" OR currently_used="1",1,0)
| stats values(product) as option_name max(detected) as in_use by db_name, host
| join type=left db_name host [
  search index=licenses sourcetype="oracle:entitlement" earliest=-1d
  | table db_name, host, product, entitled
]
| eval gap=if(in_use=1 AND (entitled=0 OR isnull(entitled)),1,0)
| where gap=1
| table db_name, host, option_name, entitled
```
- **Implementation:** (1) Ingest weekly DBA_FEATURE_USAGE_STATISTICS via DB Connect with stable `product` names. (2) Maintain `oracle:entitlement` from procurement. (3) Open high-priority changes to disable unused options or purchase entitlements before vendor review.
- **Visualization:** Table (unentitled options in use), Bar chart (gap count by data center), Single value (databases with violations).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-20.3.12 · Splunk Enterprise License Pool Usage and Stack Warnings

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Cost
- **Value:** Splunk indexing volume directly ties to dollar cost; pools that repeatedly approach quota force soft violations, search degradation, and unplanned license purchases. Watching daily ingestion by pool and stack supports data retirement and routing before finance sees an emergency PO.
- **App/TA:** Splunk internal telemetry (no TA), Monitoring Console (optional)
- **Data Sources:** `index=_internal` `source=*license_usage.log*` `type=Usage`
- **SPL:**
```spl
index=_internal source=*license_usage.log* type=Usage earliest=-30d
| eval gb=round(b/1024/1024/1024,4)
| bin _time span=1d
| stats sum(gb) as idx_gb by _time, pool, stack
| eventstats sum(idx_gb) as daily_total by _time
| lookup splunk_license_quota pool stack OUTPUT quota_gb_per_day
| eval util_pct=round(100*idx_gb/nullif(quota_gb_per_day,0),1)
| where util_pct>85
| sort -util_pct
```
- **Implementation:** (1) Build `splunk_license_quota` from your entitlement and stacking plan (GB per day per pool). (2) Alert at eighty-five percent for two consecutive days. (3) Pair with `data model` acceleration and sourcetype-level volume reports to find noisy sources.
- **Visualization:** Line chart (indexed GB versus quota by pool), Table (pools over threshold), Single value (total daily utilization percent).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.13 · SAP Named User License versus Concurrent Session Peaks

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance, Capacity
- **Value:** SAP named-user contracts are priced on authorized humans while technical users and peak dialog sessions can exceed design points. Comparing entitled named users to measured concurrent dialog peaks highlights indirect access risk and indirect-license optimization programs.
- **App/TA:** SAProuter or SAP Security Audit Log forwarder, SAP Solution Manager export
- **Data Sources:** `index=sap` `sourcetype="sap:sm20"`
- **SPL:**
```spl
index=sap sourcetype="sap:sm20" earliest=-30d
| eval user=coalesce(sap_user, user_name)
| bin _time span=1h
| stats dc(user) as named_dialog_users by _time, system_id
| eventstats max(named_dialog_users) as peak_concurrent by system_id
| join type=left system_id [
  search index=licenses sourcetype="sap:license_position" earliest=-1d
  | stats latest(named_users_entitled) as entitled by system_id
]
| eval peak_to_entitled_pct=round(100*peak_concurrent/nullif(entitled,0),1)
| where peak_to_entitled_pct>25 AND peak_concurrent>entitled*0.9
| table system_id, entitled, peak_concurrent, peak_to_entitled_pct
```
- **Implementation:** (1) Ingest SM20 or gateway session logs with one-hour granularity. (2) Refresh `named_users_entitled` from LAW or contract system weekly. (3) Engage SAP measurement team when peaks approach entitlement for sustained business days.
- **Visualization:** Line chart (concurrent users versus entitlement), Table (systems breaching policy), Single value (peak over entitlement hours per month).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.14 · Software License Harvesting Queue from SAM Reclamation

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost, Capacity
- **Value:** Reclamation workflows stall when approvals idle in queues. Tracking candidate seats from assignment to uninstall reduces carry-over into the next renewal cycle and improves realized savings from harvest playbooks.
- **App/TA:** Flexera IT Visibility, ServiceNow SAM, Snow Inventory
- **Data Sources:** `index=software` `sourcetype="sam:reclaim_ticket"`
- **SPL:**
```spl
index=software sourcetype="sam:reclaim_ticket" earliest=-90d
| eval opened=strptime(opened_at,"%Y-%m-%d %H:%M:%S")
| eval closed=strptime(closed_at,"%Y-%m-%d %H:%M:%S")
| eval age_days=if(isnotnull(closed), round((closed-opened)/86400,1), round((now()-opened)/86400,1))
| where status!="Closed" OR age_days>14
| stats count as tickets avg(age_days) as avg_age sum(potential_savings_usd) as pipeline_savings by owner_team, publisher
| where tickets>5
| sort -pipeline_savings
```
- **Implementation:** (1) Push reclamation ticket milestones from ITSM when integrated with SAM. (2) Escalate tickets open more than fourteen days. (3) Report pipeline_savings to FinOps monthly for credited harvest dollars.
- **Visualization:** Bar chart (open reclaim savings by team), Table (stale tickets), Single value (total pipeline savings dollars).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.15 · GitHub Enterprise Seat Utilization versus Active Contributors

- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Cost, Performance
- **Value:** GitHub Enterprise bills per occupied seat while many accounts represent bots, service users, or former contractors. Comparing billed seats to users with pushes or reviews in the last sixty days supports deprovisioning and org consolidation before annual renewal.
- **App/TA:** GitHub Audit Log streaming to Splunk, GitHub Enterprise Server TA (optional)
- **Data Sources:** `index=devops` `sourcetype="github:audit"`
- **SPL:**
```spl
index=devops sourcetype="github:audit" earliest=-60d
| search action=pull_request OR action=push OR action=issue_comment
| eval actor=coalesce(actor, user, login)
| stats dc(actor) as active_contributors_60d by enterprise_slug
| join type=left enterprise_slug [
  search index=devops sourcetype="github:license_snapshot" earliest=-1d
  | stats latest(billed_seats) as billed_seats by enterprise_slug
]
| eval seat_util_pct=round(100*active_contributors_60d/nullif(billed_seats,0),1)
| eval dormant_seats=billed_seats-active_contributors_60d
| where dormant_seats>10 OR seat_util_pct<70
| table enterprise_slug, billed_seats, active_contributors_60d, seat_util_pct, dormant_seats
```
- **Implementation:** (1) Enable audit log streaming with actor and action fields normalized. (2) Ingest nightly seat count from billing API into `github:license_snapshot`. (3) Coordinate dormant seat removal with org owners outside peak release windows.
- **Visualization:** Gauge (seat utilization percent), Table (enterprises with dormant seats), Bar chart (dormant seats by business unit tag).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.16 · Webex or Zoom Concurrent License Peak versus Subscription

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Cost
- **Value:** Meeting platforms often license peak concurrent ports or hosts; a single all-hands can force expensive burst add-ons if baseline is wrong. Tracking measured concurrent peaks against purchased ports prevents both overbuying idle capacity and embarrassing hard caps during executive broadcasts.
- **App/TA:** Webex Control Hub export, Zoom Operation logs, vendor SCIM usage
- **Data Sources:** `index=collab` `sourcetype="meetings:usage"`
- **SPL:**
```spl
index=collab sourcetype="meetings:usage" earliest=-30d
| eval concurrent=tonumber(coalesce(concurrent_participants, concurrent_ports, peak_attendees))
| bin _time span=5m
| stats max(concurrent) as peak_5m by _time, tenant_id
| stats max(peak_5m) as month_peak by tenant_id
| join type=left tenant_id [
  search index=collab sourcetype="meetings:entitlement" earliest=-1d
  | stats latest(purchased_concurrent) as purchased by tenant_id
]
| eval headroom_pct=round(100*(purchased-month_peak)/nullif(purchased,0),1)
| where month_peak > purchased*0.85 OR headroom_pct>60
| table tenant_id, purchased, month_peak, headroom_pct
```
- **Implementation:** (1) Ingest five-minute concurrent participant metrics from admin APIs. (2) Store purchased concurrent or port counts in `meetings:entitlement`. (3) Alert when month_peak exceeds eighty-five percent of purchased; review sustained high headroom for downgrade at renewal.
- **Visualization:** Line chart (five-minute peak trend), Gauge (headroom percent), Table (tenants at risk of cap).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-20.3.17 · Citrix Virtual Apps and Desktops Concurrent Session versus License Count

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Cost
- **Value:** CVAD licenses are tied to peak concurrent instances or user connections; sustained peaks above entitlement trigger true-up or session denial. Trending peaks against purchased counts informs additional packs, burst cloud burst packs, or rightsizing published apps before renewal.
- **App/TA:** Citrix Director / Monitor data export, `Splunk Add-on for Citrix`
- **Data Sources:** `index=virtualization` `sourcetype="citrix:session"`
- **SPL:**
```spl
index=virtualization sourcetype="citrix:session" earliest=-30d
| where session_state="Active" OR session_state="Connected"
| bin _time span=5m
| stats dc(session_key) as concurrent_sessions by _time, site_name
| stats max(concurrent_sessions) as license_peak_30d by site_name
| lookup citrix_license_entitlement site_name OUTPUT concurrent_license_count
| eval peak_util_pct=round(100*license_peak_30d/nullif(concurrent_license_count,0),1)
| where peak_util_pct>85 OR peak_util_pct<40
| table site_name, concurrent_license_count, license_peak_30d, peak_util_pct
```
- **Implementation:** (1) Forward Director OData or Broker session records with stable `session_key`. (2) Maintain `citrix_license_entitlement` from license server or reseller CSV. (3) Plan purchases when peak_util_pct exceeds eighty-five for more than three peak days per month; investigate downsizing when under forty percent.
- **Visualization:** Area chart (concurrent sessions with license line overlay), Table (sites over or under target), Single value (portfolio peak utilization percent).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

## Summary Statistics

| Category | Subcategories | Use Cases |
|----------|:------------:|:---------:|
| 1. Server & Compute | 4 | 262 |
| 2. Virtualization | 3 | 23 |
| 3. Containers & Orchestration | 4 | 30 |
| 4. Cloud Infrastructure | 4 | 44 |
| 5. Network Infrastructure | 9 | 203 |
| 6. Storage & Backup | 4 | 28 |
| 7. Database & Data Platforms | 4 | 40 |
| 8. Application Infrastructure | 5 | 45 |
| 9. Identity & Access Management | 4 | 29 |
| 10. Security Infrastructure | 8 | 47 |
| 11. Email & Collaboration | 3 | 24 |
| 12. DevOps & CI/CD | 5 | 33 |
| 13. Observability & Monitoring | 4 | 40 |
| 14. IoT & OT | 4 | 74 |
| 15. DC Physical Infrastructure | 3 | 16 |
| 16. Service Management & ITSM | 3 | 23 |
| 17. Network Security & Zero Trust | 3 | 22 |
| 18. Data Center Fabric & SDN | 3 | 15 |
| 19. Compute Infrastructure (HCI) | 2 | 13 |
| 20. Cost & Capacity Management | 3 | 77 |
| **TOTAL** | **76** | **1067** |

---

*Generated: March 2026*
*Primary tools: Splunk Enterprise / Cloud with free Splunkbase add-ons. Premium exceptions noted (ITSI, ES).*
*Each use case includes: criticality rating, value description, recommended App/TA, data sources, SPL query, implementation guidance, and visualization recommendations.*
