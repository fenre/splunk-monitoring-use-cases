## 20. Cost & Capacity Management

### 20.1 Cloud Cost Monitoring

**Splunk Add-on:** Cloud provider TAs, CUR/billing export ingestion

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
| join type=left budget_name [ search index=cloud_cost sourcetype="cost:daily" earliest=-7d | stats sum(cost) as daily_cost by account_id, _time span=1d ]
| table _time, budget_name, threshold_type, daily_cost
```
- **Implementation:** Ingest budget notifications via HEC or Lambda. Drill down to service cost change same day. Link to change tickets.
- **Visualization:** Timeline (budget alerts overlaid with spend), Table (alert + cost delta), Sankey (alert → service).
- **CIM Models:** N/A

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

### 20.2 Capacity Planning

**Splunk Add-on:** Cross-referencing infrastructure metrics with trending/forecasting

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

### UC-20.2.21 · CPU and Memory Right-Sizing (Host and VM)

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Host-level overcommit risk and VM-level downsize candidates — pairs with VM view (UC-20.2.5).
- **App/TA:** VMware perf, Hyper-V
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
| 20. Cost & Capacity Management | 3 | 27 |
| **TOTAL** | **76** | **1042** |

---

*Generated: March 2026*
*Primary tools: Splunk Enterprise / Cloud with free Splunkbase add-ons. Premium exceptions noted (ITSI, ES).*
*Each use case includes: criticality rating, value description, recommended App/TA, data sources, SPL query, implementation guidance, and visualization recommendations.*
